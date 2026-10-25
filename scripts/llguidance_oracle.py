"""Offline, isolated development oracle; never used by the Android application.

Copyright 2026 LocalLore contributors. SPDX-License-Identifier: Apache-2.0
"""
import argparse
from email.parser import BytesParser
import hashlib
import io
import json
import os
from pathlib import Path, PurePosixPath
import platform
import stat
import subprocess
import sys
import zipfile

ROOT = Path(__file__).resolve().parents[1]
WHEEL_NAME = "llguidance-1.3.0-cp39-abi3-win_amd64.whl"
WHEEL_BYTES = 2_789_946
WHEEL_SHA256 = "1d1cd1c8618d1a13605d3e057c978651e551c8c469b481ee4041f1d6c436002d"
DIST = "llguidance-1.3.0.dist-info"
BARRIER = b"locallore_llguidance_owned_worker_v1\n"
MAX_CORPUS = 262_144  # Owned process helper bounds stdout+stderr together.
SCOPE = "locallore_llguidance_oracle_v1"
CONTROLS = {key: True for key in ("basic_compile", "valid_complete", "illegal_rejected",
                                 "incomplete_rejected", "unsupported_refused")}


class OracleError(Exception):
    """Closed reason only; paths and arbitrary dependency messages stay private."""


class ClosedArguments(argparse.ArgumentParser):
    def error(self, message):
        raise OracleError("arguments")


def closed_pairs(pairs):
    value = {}
    for key, item in pairs:
        if key in value:
            raise ValueError("duplicate_key")
        value[key] = item
    return value


def digest(data):
    return hashlib.sha256(data).hexdigest()


def no_links(path):
    """Reject existing symlinks/reparse points, including ancestors."""
    for candidate in (path,) + tuple(path.parents):
        try:
            info = candidate.lstat()
        except FileNotFoundError:
            continue
        if stat.S_ISLNK(info.st_mode) or getattr(info, "st_file_attributes", 0) & 0x400:
            raise OracleError("linked_path")


def private_path(value):
    path = Path(value).absolute()
    no_links(path)
    path = path.resolve()
    if path == ROOT or ROOT in path.parents:
        raise OracleError("private_directory_required")
    return path


def platform_check():
    if (sys.implementation.name != "cpython" or sys.version_info < (3, 9)
            or sys.platform != "win32" or platform.machine().lower() not in ("amd64", "x86_64")
            or sys.maxsize <= 2**32):
        raise OracleError("unsupported_platform")


def wheel_files(path):
    """Hash before ZIP parsing. Never import unverified native code."""
    no_links(path)
    if not path.is_file() or path.stat().st_size != WHEEL_BYTES:
        raise OracleError("wheel_size")
    with path.open("rb") as stream:
        raw = stream.read(WHEEL_BYTES + 1)
    if digest(raw) != WHEEL_SHA256:
        raise OracleError("wheel_hash")
    files = {}
    with zipfile.ZipFile(io.BytesIO(raw)) as wheel:
        entries = wheel.infolist()
        if len(entries) > 128 or sum(e.file_size for e in entries) > 64 * 1024 * 1024:
            raise OracleError("wheel_bounds")
        for entry in entries:
            name = entry.filename
            parts = PurePosixPath(name).parts
            if (entry.orig_filename != name or not parts or name.startswith("/") or "\\" in name or ":" in name
                    or any(p in (".", "..") for p in parts)
                    or parts[0] not in ("llguidance", DIST) or name in files
                    or stat.S_ISLNK(entry.external_attr >> 16) or entry.is_dir()):
                raise OracleError("wheel_layout")
            files[name] = wheel.read(entry)
    metadata = BytesParser().parsebytes(files.get(DIST + "/METADATA", b""))
    wheel_metadata = BytesParser().parsebytes(files.get(DIST + "/WHEEL", b""))
    if (metadata.get("Name") != "llguidance" or metadata.get("Version") != "1.3.0"
            or metadata.get("Requires-Python") != ">=3.9" or metadata.get_all("Requires-Dist")
            or metadata.get("License-Expression") != "MIT"
            or wheel_metadata.get_all("Tag") != ["cp39-abi3-win_amd64"]
            or "llguidance/_lib.pyd" not in files
            or not files.get(DIST + "/licenses/LICENSE", b"").lstrip().startswith(b"MIT License")):
        raise OracleError("wheel_metadata")
    return files


def provision(wheel, runtime):
    platform_check()
    wheel = Path(wheel).absolute()
    if wheel.name != WHEEL_NAME:
        raise OracleError("wheel_filename")
    files = wheel_files(wheel)
    runtime = private_path(runtime)
    runtime.mkdir()  # Create-only, including failure remnants; never delete prior evidence.
    (runtime / WHEEL_NAME).write_bytes(wheel.read_bytes())
    library = runtime / "lib"
    library.mkdir()
    for name, raw in files.items():
        target = library.joinpath(*PurePosixPath(name).parts)
        target.parent.mkdir(parents=True, exist_ok=True)
        with target.open("xb") as stream:
            stream.write(raw)
    verify_runtime(runtime)
    return {"version": 1, "status": "provisioned", "wheel_sha256": WHEEL_SHA256,
            "files": len(files)}


def verify_runtime(runtime):
    platform_check()
    runtime = private_path(runtime)
    files = wheel_files(runtime / WHEEL_NAME)
    library = runtime / "lib"
    no_links(library)
    actual = set()
    for index, target in enumerate(library.rglob("*")):
        if index > 256:
            raise OracleError("runtime_integrity")
        no_links(target)
        if target.is_file():
            name = target.relative_to(library).as_posix()
            actual.add(name)
            expected = files.get(name)
            if expected is None or target.stat().st_size != len(expected) or target.read_bytes() != expected:
                raise OracleError("runtime_integrity")
        elif not target.is_dir():
            raise OracleError("runtime_integrity")
    if actual != set(files) or {p.name for p in runtime.iterdir()} != {WHEEL_NAME, "lib"}:
        raise OracleError("runtime_integrity")
    return library


def validate_report(report, corpus_raw):
    """Credit only a complete closed result bound to the exact exported corpus."""
    try:
        corpus = json.loads(corpus_raw)
        if (type(report) is not dict or set(report) != {"version", "scope", "status", "native",
                "corpus_sha256", "controls", "cases", "sample_count", "refusals"}
                or type(report["version"]) is not int or report["version"] != 1
                or report["scope"] != SCOPE or report["native"] is not True
                or report["status"] not in ("passed", "mismatch")
                or report["corpus_sha256"] != digest(corpus_raw)
                or type(report["controls"]) is not dict or set(report["controls"]) != set(CONTROLS)
                or any(value is not True for value in report["controls"].values())
                or type(report["refusals"]) is not int or report["refusals"] != len(corpus["refusals"])
                or type(report["cases"]) is not list or len(report["cases"]) != len(corpus["cases"])):
            return False
        count = 0
        mismatch = False
        for case_index, (row, case) in enumerate(zip(report["cases"], corpus["cases"])):
            if (type(row) is not dict or set(row) != {"index", "schema_sha256", "positives", "negatives"}
                    or type(row["index"]) is not int or row["index"] != case_index
                    or row["schema_sha256"] != digest(case["schema_json"].encode("utf-8"))):
                return False
            for category in ("positives", "negatives"):
                if type(row[category]) is not list or len(row[category]) != len(case[category]):
                    return False
                for index, (sample, original) in enumerate(zip(row[category], case[category])):
                    data = original["json"].encode("utf-8")
                    if (type(sample) is not dict or set(sample) != {"index", "sha256", "bytes", "accepted", "outcome", "checked_bytes"}
                            or type(sample["index"]) is not int or sample["index"] != index
                            or sample["sha256"] != digest(data)
                            or type(sample["bytes"]) is not int or sample["bytes"] != len(data)
                            or type(sample["accepted"]) is not bool
                            or type(sample["checked_bytes"]) is not int
                            or not 0 <= sample["checked_bytes"] <= len(data)
                            or sample["outcome"] not in ("COMPLETE", "BYTE_MASK", "INCOMPLETE")
                            or sample["accepted"] != (sample["outcome"] == "COMPLETE")
                            or (sample["outcome"] == "BYTE_MASK" and sample["checked_bytes"] >= len(data))
                            or (sample["outcome"] != "BYTE_MASK" and sample["checked_bytes"] != len(data))):
                        return False
                    mismatch |= sample["accepted"] != (category == "positives")
                    count += 1
        return (type(report["sample_count"]) is int and report["sample_count"] == count
                and (report["status"] == "mismatch") == mismatch)
    except (ValueError, TypeError, KeyError, UnicodeError):
        return False


def worker(mode, output, runtime):
    # Parent assigns the whole process tree to its Windows job before releasing input.
    if sys.stdin.buffer.read(len(BARRIER) + 1) != BARRIER:
        return 2
    output = private_path(output)
    env = dict(os.environ)
    for key in list(env):
        if key.upper().startswith(("PYTHON", "RUSTFLAGS", "RUSTDOCFLAGS", "CARGO_ENCODED_RUSTFLAGS")):
            del env[key]
    env.update(CARGO_NET_OFFLINE="true", RUSTUP_TOOLCHAIN="1.93.1")
    if mode == "build":
        command = ["cargo", "+1.93.1", "build", "--frozen", "--offline", "-p", "locallore",
                   "--features", "host", "--example", "llguidance_cases", "--target-dir", str(output / "target")]
    elif mode in ("test", "clippy"):
        command = ["cargo", "+1.93.1", mode, "--frozen", "--offline", "-p", "locallore",
                   "--features", "host", "--all-targets", "--target-dir", str(output / "target")]
        if mode == "clippy":
            command.extend(["--", "-D", "warnings"])
    elif mode == "export":
        command = [str(output / "target/debug/examples/llguidance_cases.exe")]
    elif mode == "check":
        library = verify_runtime(runtime)
        command = [sys.executable, "-I", "-S", "-B", str(ROOT / "benchmarks/llguidance_oracle.py"),
                   "--corpus", str(output / "corpus.json"), "--module-root", str(library)]
    else:
        return 2
    return subprocess.call(command, cwd=str(ROOT), env=env)


def run(runtime, output, process_runner=None, reductions=False):
    verify_runtime(runtime)
    output = private_path(output)
    output.mkdir()
    if process_runner is None:
        sys.path.insert(0, str(ROOT / "benchmarks"))
        from runtime_spike import run_process
        process_runner = run_process
    stages = []
    report = {"version": 1, "status": "failed", "wheel_sha256": WHEEL_SHA256, "stages": stages,
              "corpus_source": "reduction_fixture" if reductions else "engine_export"}
    if reductions:
        raw = (ROOT / "fixtures/llguidance_escape_reductions.json").read_bytes()
        if not 0 < len(raw) <= MAX_CORPUS:
            raise OracleError("corpus_size")
        (output / "corpus.json").write_bytes(raw)
        report["corpus_sha256"] = digest(raw)
    for mode in (("check",) if reductions else ("build", "export", "check")):
        command = [sys.executable, "-I", "-S", "-B", str(Path(__file__).resolve()),
                   "_worker", mode, str(output), str(Path(runtime).absolute())]
        result = process_runner(command, request=BARRIER, deadline=180 if mode == "build" else 60,
                                max_output=MAX_CORPUS)
        stages.append({"stage": mode, "status": result.status, "elapsed_ms": result.elapsed_ms,
                       "returncode": result.returncode, "cleanup_complete": result.cleanup_complete,
                       "stdout_bytes": len(result.stdout), "stderr_bytes": result.stderr_bytes})
        if result.status != "completed" or not result.cleanup_complete:
            break
        if mode == "export" and result.returncode == 0:
            if not result.stdout or len(result.stdout) > MAX_CORPUS:
                break
            (output / "corpus.json").write_bytes(result.stdout)
            report["corpus_sha256"] = digest(result.stdout)
        if mode == "check":
            # The fixed checker emits only its closed report. Failure details are bounded enums.
            try:
                checked = json.loads(result.stdout, object_pairs_hook=closed_pairs)
            except (ValueError, UnicodeError):
                break
            if not validate_report(checked, (output / "corpus.json").read_bytes()):
                (output / "rejected-report.json").write_bytes(result.stdout)
                break
            (output / "oracle.json").write_bytes(result.stdout)
            report["oracle_sha256"] = digest(result.stdout)
            if result.returncode == 0 and checked.get("status") == "passed" and checked.get("native") is True:
                report["status"] = "passed"
            elif result.returncode == 1 and checked.get("status") == "mismatch":
                report["status"] = "mismatch"
        if result.returncode != 0:
            break
    report["source_sha256"] = {name: digest((ROOT / name).read_bytes()) for name in (
        "Cargo.lock", "crates/locallore/Cargo.toml", "crates/locallore/examples/llguidance_cases.rs",
        "benchmarks/llguidance_oracle.py", "scripts/llguidance_oracle.py",
        "fixtures/llguidance_escape_reductions.json")}
    (output / "run.json").write_text(json.dumps(report, sort_keys=True) + "\n", encoding="utf-8")
    return report


def main(argv=None):
    parser = ClosedArguments(description=__doc__, allow_abbrev=False)
    commands = parser.add_subparsers(dest="command", required=True)
    setup = commands.add_parser("provision", allow_abbrev=False)
    setup.add_argument("--wheel", required=True)
    setup.add_argument("--runtime", required=True)
    for name in ("run", "reduce"):
        check = commands.add_parser(name, allow_abbrev=False)
        check.add_argument("--runtime", required=True)
        check.add_argument("--output", required=True)
    internal = commands.add_parser("_worker", help=argparse.SUPPRESS, allow_abbrev=False)
    internal.add_argument("mode", choices=("build", "export", "check", "test", "clippy"))
    internal.add_argument("output")
    internal.add_argument("runtime")
    try:
        args = parser.parse_args(argv)
        if args.command == "_worker":
            return worker(args.mode, args.output, args.runtime)
        result = provision(args.wheel, args.runtime) if args.command == "provision" else run(
            args.runtime, args.output, reductions=args.command == "reduce")
        print(json.dumps(result, sort_keys=True))
        return 0 if result["status"] in ("provisioned", "passed") else 1
    except OracleError as error:
        print(json.dumps({"version": 1, "status": "failed", "reason": str(error)}))
    except (OSError, ValueError, KeyError, zipfile.BadZipFile):
        print(json.dumps({"version": 1, "status": "failed", "reason": "local_tool_failure"}))
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
