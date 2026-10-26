"""Explicit Windows CRT mechanism control; never contacts ADB or a device.

Copyright 2026 LocalLore contributors. SPDX-License-Identifier: Apache-2.0
"""
import argparse
import ctypes
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import stat
import sys
import tempfile

FIXTURE = bytes(range(256)) * 3
SOURCE_SHA256 = "f3a25aa93aa2fbba28d79260535bbd6a5eb0fc1c24a8b0f04e12b484c1dfe363"
MODES = ("TEXT", "BINARY")
DEADLINE_SECONDS = 10
MAX_OUTPUT = 4096
MAX_READ_CALLS = 4
O_BINARY, O_TEXT = 0x8000, 0x4000
WORKER_KEYS = {"version", "mode", "status", "source_verified", "observed_bytes",
               "observed_sha256", "eof", "read_calls", "descriptor_closed"}


class ProbeRefused(Exception):
    """Only closed reasons cross the worker boundary."""


def sha256(data):
    return hashlib.sha256(data).hexdigest()


def _strict_json(raw):
    def unique(pairs):
        result = {}
        for key, value in pairs:
            if key in result:
                raise ValueError("duplicate")
            result[key] = value
        return result
    return json.loads(raw, object_pairs_hook=unique,
                      parse_constant=lambda _: (_ for _ in ()).throw(ValueError("nonfinite")))


def _load_crt():
    if os.name != "nt":
        raise ProbeRefused("unsupported_host")
    # The CRT uses cdecl. System32 search excludes the fixture/current directory.
    crt = ctypes.CDLL("ucrtbase.dll", winmode=0x00000800)
    declarations = {
        "_wopen": ([ctypes.c_wchar_p, ctypes.c_int], ctypes.c_int),
        "_dup2": ([ctypes.c_int, ctypes.c_int], ctypes.c_int),
        "_close": ([ctypes.c_int], ctypes.c_int),
        "_setmode": ([ctypes.c_int, ctypes.c_int], ctypes.c_int),
        "_read": ([ctypes.c_int, ctypes.c_void_p, ctypes.c_uint], ctypes.c_int),
        "_lseeki64": ([ctypes.c_int, ctypes.c_int64, ctypes.c_int], ctypes.c_int64),
    }
    for name, (args, result) in declarations.items():
        function = getattr(crt, name)
        function.argtypes, function.restype = args, result
    return crt


def _read_to_eof(crt):
    result = bytearray()
    buffer = ctypes.create_string_buffer(1024)
    for calls in range(1, MAX_READ_CALLS + 1):
        count = crt._read(0, buffer, len(buffer))
        if type(count) is not int or count < 0 or count > len(buffer):
            raise ProbeRefused("crt_failed")
        if count == 0:
            return bytes(result), calls
        result.extend(buffer.raw[:count])
        if len(result) > len(FIXTURE):
            raise ProbeRefused("output_limit")
    raise ProbeRefused("output_limit")


def observe_crt(path, mode, *, loader=_load_crt):
    """Worker only: replace CRT fd0 after the owned-job stdin barrier is drained.

    Opening, dup2, mode changes, seek, reads and close all use the SAME CRT DLL.
    The original is verified in binary mode before the measured read. No native
    code executes at import time. This is not an ADB binary/runtime observation.
    """
    result = {"version": 1, "mode": mode, "status": "crt_failed", "source_verified": False,
              "observed_bytes": 0, "observed_sha256": None, "eof": False,
              "read_calls": 0, "descriptor_closed": False}
    crt = None
    opened = None
    stdin_owned = False
    try:
        if mode not in MODES or type(mode) is not str:
            raise ProbeRefused("invalid_request")
        path = Path(path)
        if not path.is_absolute() or path.name != "original-768.bin" or path.is_symlink():
            raise ProbeRefused("invalid_request")
        info = path.stat()
        if not stat.S_ISREG(info.st_mode) or info.st_size != len(FIXTURE):
            raise ProbeRefused("fixture_mismatch")
        crt = loader()
        opened = crt._wopen(str(path), O_BINARY)  # O_RDONLY == 0; never create/truncate.
        if type(opened) is not int or opened < 0:
            opened = None
            raise ProbeRefused("crt_failed")
        if crt._dup2(opened, 0) != 0:
            raise ProbeRefused("crt_failed")
        stdin_owned = True
        if opened != 0:
            if crt._close(opened) != 0:
                raise ProbeRefused("crt_failed")
            opened = None
        else:
            opened = None
        if crt._setmode(0, O_BINARY) < 0:
            raise ProbeRefused("crt_failed")
        original, _ = _read_to_eof(crt)
        if original != FIXTURE or sha256(original) != SOURCE_SHA256:
            raise ProbeRefused("fixture_mismatch")
        result["source_verified"] = True
        if crt._lseeki64(0, 0, 0) != 0 or crt._setmode(0, O_TEXT if mode == "TEXT" else O_BINARY) < 0:
            raise ProbeRefused("crt_failed")
        observed, calls = _read_to_eof(crt)
        result.update(status="completed", observed_bytes=len(observed), observed_sha256=sha256(observed),
                      eof=True, read_calls=calls)
    except ProbeRefused as error:
        result["status"] = str(error)
    except (OSError, ValueError, TypeError, AttributeError, OverflowError):
        result["status"] = "crt_failed"
    finally:
        closed = True
        if crt is not None:
            for descriptor in ([opened] if opened is not None else []) + ([0] if stdin_owned else []):
                try:
                    closed = (crt._close(descriptor) == 0) and closed
                except (OSError, ValueError, TypeError, AttributeError):
                    closed = False
        result["descriptor_closed"] = closed
        if not closed:
            result["status"] = "crt_failed"
    return result


def _valid_worker(value, mode):
    if type(value) is not dict or set(value) != WORKER_KEYS:
        return False
    if type(value["version"]) is not int or value["version"] != 1 or value["mode"] != mode:
        return False
    if type(value["status"]) is not str or value["status"] not in {"completed", "crt_failed", "invalid_request", "fixture_mismatch",
                              "output_limit", "unsupported_host"}:
        return False
    if any(type(value[key]) is not bool for key in ("source_verified", "eof", "descriptor_closed")):
        return False
    if type(value["observed_bytes"]) is not int or not 0 <= value["observed_bytes"] <= len(FIXTURE):
        return False
    if type(value["read_calls"]) is not int or not 0 <= value["read_calls"] <= MAX_READ_CALLS:
        return False
    digest = value["observed_sha256"]
    if digest is not None and (type(digest) is not str or len(digest) != 64 or any(c not in "0123456789abcdef" for c in digest)):
        return False
    if value["status"] == "completed":
        return (value["source_verified"] and value["eof"] and value["descriptor_closed"] and
                value["read_calls"] > 0 and digest is not None)
    return True


def _case(process, mode):
    # Closed projection: no raw stdout, exception, source path, PID or environment.
    row = {"mode": mode, "status": "worker_failed", "client_status": "unknown",
           "client_returncode": None, "cleanup_complete": False, "elapsed_ms": 0,
           "stdout_bytes": 0, "stdout_sha256": sha256(b""), "stderr_bytes": 0,
           "observation": None, "expected_match": False}
    if process is None:
        return row
    if type(process.status) is str and process.status in {"completed", "timeout", "cancelled", "output_limit", "spawn_failed", "cleanup_failed"}:
        row["client_status"] = process.status
    if type(process.returncode) is int and -(1 << 31) <= process.returncode < (1 << 32):
        row["client_returncode"] = process.returncode
    row["cleanup_complete"] = process.cleanup_complete is True
    if type(process.elapsed_ms) is int and 0 <= process.elapsed_ms <= 30_000:
        row["elapsed_ms"] = process.elapsed_ms
    valid_metadata = (type(process.stderr_bytes) is int and 0 <= process.stderr_bytes <= MAX_OUTPUT and
                      type(process.elapsed_ms) is int and 0 <= process.elapsed_ms <= 30_000)
    if type(process.stderr_bytes) is int and 0 <= process.stderr_bytes <= MAX_OUTPUT:
        row["stderr_bytes"] = process.stderr_bytes
    if type(process.stdout) is not bytes or len(process.stdout) > MAX_OUTPUT:
        return row
    row.update(stdout_bytes=len(process.stdout), stdout_sha256=sha256(process.stdout))
    if (not valid_metadata or row["client_status"] != "completed" or row["client_returncode"] != 0 or
            not row["cleanup_complete"] or row["stderr_bytes"] != 0):
        return row
    try:
        value = _strict_json(process.stdout)
        if not _valid_worker(value, mode):
            return row
    except (ValueError, TypeError, RecursionError, UnicodeError):
        return row
    row["observation"] = value
    row["status"] = value["status"]
    expected = bytes(range(26)) if mode == "TEXT" else FIXTURE
    row["expected_match"] = (value["status"] == "completed" and value["observed_bytes"] == len(expected) and
                             value["observed_sha256"] == sha256(expected))
    return row


def run_probe(*, runner=None):
    report = {"version": 1, "scope": "windows_crt_regular_stdin_control", "status": "unsupported_host",
              "crt": "ucrtbase", "source_bytes": len(FIXTURE), "source_sha256": SOURCE_SHA256,
              "deadline_ms": DEADLINE_SECONDS * 1000, "max_output_bytes": MAX_OUTPUT,
              "source_unchanged": False, "fixture_retained": False,
              "cases": [], "installed_adb_proven": False}
    if os.name != "nt":
        return report
    if runner is None:
        spec = importlib.util.spec_from_file_location("windows_stdin_owned_runner", Path(__file__).with_name("runtime_spike.py"))
        module = importlib.util.module_from_spec(spec)
        sys.modules[spec.name] = module
        spec.loader.exec_module(module)
        runner = module.run_process
    report["status"] = "refused"
    directory = Path(tempfile.mkdtemp(prefix="locallore-crt-"))
    path = directory / "original-768.bin"
    children_cleaned = True
    report["fixture_retained"] = True
    try:
        with path.open("x+b") as source:
            source.write(FIXTURE)
            source.flush()
            identity = os.fstat(source.fileno())
            for mode in MODES:
                request = json.dumps({"version": 1, "mode": mode, "path": str(path)}, separators=(",", ":")).encode()
                children_cleaned = False  # Unproved until the runner returns known closure.
                try:
                    process = runner([sys.executable, "-I", str(Path(__file__).resolve()), "_worker"],
                                     request, deadline=DEADLINE_SECONDS, max_output=MAX_OUTPUT)
                except (OSError, ValueError, RuntimeError):
                    process = None
                row = _case(process, mode)
                report["cases"].append(row)
                children_cleaned = row["cleanup_complete"] is True
                if not children_cleaned:
                    break
                if row["client_status"] != "completed" or row["client_returncode"] != 0 or row["status"] != "completed":
                    break
            if children_cleaned:
                source.seek(0)
                after = os.fstat(source.fileno())
                visible = path.stat()
                report["source_unchanged"] = (
                    source.read(len(FIXTURE) + 1) == FIXTURE and not path.is_symlink() and
                    (identity.st_dev, identity.st_ino, identity.st_size, identity.st_mtime_ns) ==
                    (after.st_dev, after.st_ino, after.st_size, after.st_mtime_ns) ==
                    (visible.st_dev, visible.st_ino, visible.st_size, visible.st_mtime_ns))
    except (OSError, ValueError):
        pass  # Closed refusal; no filesystem exception/path reaches the report.
    finally:
        # Parent fd closes on every path. Retain only the visible fixture when
        # child closure is unknown; never delete a potentially live child's input.
        if children_cleaned:
            try:
                path.unlink(missing_ok=True)
                directory.rmdir()  # Exact owned file/directory only; never recursive.
                report["fixture_retained"] = False
            except OSError:
                pass
    if (not report["fixture_retained"] and report["source_unchanged"] and len(report["cases"]) == len(MODES) and
            all(row["expected_match"] for row in report["cases"])):
        report["status"] = "observed"
    return report


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("operation", choices=("run", "_worker"))
    args = parser.parse_args(argv)
    if args.operation == "_worker":
        # Trusted worker waits here until run_process has assigned its Windows Job.
        raw = sys.stdin.buffer.read(4097)
        try:
            request = _strict_json(raw)
            if (len(raw) > 4096 or type(request) is not dict or set(request) != {"version", "mode", "path"} or
                    type(request["version"]) is not int or request["version"] != 1 or
                    type(request["path"]) is not str or len(request["path"]) > 2048 or
                    request["mode"] not in MODES):
                raise ValueError("invalid_request")
            value = observe_crt(request["path"], request["mode"])
        except (ValueError, TypeError, UnicodeError, RecursionError):
            return 2
        print(json.dumps(value, sort_keys=True, separators=(",", ":")), flush=True)
        return 0 if value["status"] == "completed" else 1
    value = run_probe()
    print(json.dumps(value, sort_keys=True, separators=(",", ":")), flush=True)
    return 0 if value["status"] == "observed" else 1


if __name__ == "__main__":
    raise SystemExit(main())
