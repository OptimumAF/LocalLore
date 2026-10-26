"""Adversarial host controls; no real CRT/API/process execution in this suite.

Copyright 2026 LocalLore contributors. SPDX-License-Identifier: Apache-2.0
"""
import ctypes
import importlib.util
import json
from pathlib import Path
import tempfile
import types
import unittest
from unittest.mock import patch

SPEC = importlib.util.spec_from_file_location("windows_stdin_probe_under_test",
    Path(__file__).resolve().parents[2] / "benchmarks/windows_stdin_probe.py")
p = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(p)
CANARY = "PRIVATE_ORIGINAL_STDIN_CANARY"


class Crt:
    def __init__(self, data=p.FIXTURE, failure=None, fd=7):
        self.data, self.failure, self.fd = data, failure, fd
        self.cursor, self.mode, self.eof = 0, p.O_BINARY, False
        self.closes, self.setmodes, self.opens = [], [], []

    def _wopen(self, path, flags):
        self.opens.append((path, flags))
        return self.fd

    def _dup2(self, old, new):
        return -1 if self.failure == "dup" else 0

    def _close(self, fd):
        self.closes.append(fd)
        return -1 if self.failure == "close" else 0

    def _setmode(self, fd, mode):
        self.setmodes.append((fd, mode))
        old, self.mode = self.mode, mode
        return -1 if self.failure == "setmode" else old

    def _lseeki64(self, fd, offset, origin):
        self.cursor, self.eof = 0, False
        return -1 if self.failure == "seek" else 0

    def _read(self, fd, buffer, length):
        if self.failure == "read":
            return -1
        if self.failure == "oversized":
            return length + 1
        if self.eof:
            return 0
        end = min(len(self.data), self.cursor + (1 if self.failure == "dribble" else length))
        if self.mode == p.O_TEXT:
            control_z = self.data.find(b"\x1a", self.cursor, end)
            if control_z >= 0:
                end, self.eof = control_z, True
        chunk = self.data[self.cursor:end]
        self.cursor = end
        ctypes.memmove(buffer, chunk, len(chunk))
        return len(chunk)


def observation(mode="TEXT", **changes):
    data = bytes(range(26)) if mode == "TEXT" else p.FIXTURE
    return {"version": 1, "mode": mode, "status": "completed", "source_verified": True,
            "observed_bytes": len(data), "observed_sha256": p.sha256(data), "eof": True,
            "read_calls": 2, "descriptor_closed": True} | changes


def process(value=None, **changes):
    return types.SimpleNamespace(**({"status": "completed", "returncode": 0, "cleanup_complete": True,
        "elapsed_ms": 12, "stderr_bytes": 0, "stdout": json.dumps(value or observation()).encode()} | changes))


class WindowsStdinProbeTests(unittest.TestCase):
    def fixture(self, root):
        path = Path(root) / "original-768.bin"
        path.write_bytes(p.FIXTURE)
        return path

    def test_original_size_and_exact_hashes_are_fixed(self):
        self.assertEqual(768, len(p.FIXTURE))
        self.assertEqual("f3a25aa93aa2fbba28d79260535bbd6a5eb0fc1c24a8b0f04e12b484c1dfe363", p.sha256(p.FIXTURE))
        self.assertEqual(p.SOURCE_SHA256, p.sha256(p.FIXTURE))
        self.assertEqual("b858da80d8a57dc546905fd147612ebddd3c9188620405d058f9ee5ab1e6bc52", p.sha256(bytes(range(26))))

    def test_same_crt_opens_binary_verifies_rewinds_changes_mode_and_closes_fd0(self):
        with tempfile.TemporaryDirectory() as root:
            path = self.fixture(root)
            for mode, expected in [("TEXT", bytes(range(26))), ("BINARY", p.FIXTURE)]:
                crt = Crt()
                value = p.observe_crt(path, mode, loader=lambda: crt)
                self.assertEqual(observation(mode), value)
                self.assertEqual([(str(path), p.O_BINARY)], crt.opens)
                self.assertEqual([7, 0], crt.closes)
                self.assertEqual([(0, p.O_BINARY), (0, p.O_TEXT if mode == "TEXT" else p.O_BINARY)], crt.setmodes)
                self.assertEqual(p.sha256(expected), value["observed_sha256"])

    def test_same_size_corrupt_source_never_becomes_a_positive(self):
        with tempfile.TemporaryDirectory() as root:
            value = p.observe_crt(self.fixture(root), "TEXT", loader=lambda: Crt(b"x" * 768))
            self.assertEqual("fixture_mismatch", value["status"])
            self.assertFalse(value["source_verified"])
            self.assertIsNone(value["observed_sha256"])
            self.assertTrue(value["descriptor_closed"])

    def test_crt_failures_never_report_completed_and_close_acquired_owners(self):
        with tempfile.TemporaryDirectory() as root:
            for failure in ["dup", "close", "setmode", "seek", "read", "oversized", "dribble"]:
                crt = Crt(failure=failure)
                value = p.observe_crt(self.fixture(root) if not (Path(root) / "original-768.bin").exists()
                                      else Path(root) / "original-768.bin", "TEXT", loader=lambda: crt)
                self.assertNotEqual("completed", value["status"], failure)
                self.assertIn(7, crt.closes)
                if failure != "dup":
                    self.assertIn(0, crt.closes)
                self.assertEqual(failure != "close", value["descriptor_closed"])

    def test_opened_fd0_is_closed_once(self):
        with tempfile.TemporaryDirectory() as root:
            crt = Crt(fd=0)
            self.assertEqual("completed", p.observe_crt(self.fixture(root), "TEXT", loader=lambda: crt)["status"])
            self.assertEqual([0], crt.closes)

    def test_private_exception_is_closed_and_no_path_is_reported(self):
        def denied():
            raise OSError(CANARY)
        with tempfile.TemporaryDirectory() as root:
            value = p.observe_crt(self.fixture(root), "TEXT", loader=denied)
            self.assertEqual("crt_failed", value["status"])
            self.assertNotIn(CANARY, json.dumps(value))
            self.assertNotIn(root, json.dumps(value))

    def test_invalid_mode_or_source_does_not_load_crt(self):
        with tempfile.TemporaryDirectory() as root:
            path = self.fixture(root)
            for name, mode in [(path, "OTHER"), (Path("relative/original-768.bin"), "TEXT"), (path.parent, "TEXT")]:
                with patch.object(p, "_load_crt") as loader:
                    value = p.observe_crt(name, mode, loader=loader)
                    loader.assert_not_called()
                    self.assertEqual("invalid_request", value["status"])

    def test_nonzero_unknown_cleanup_deadline_or_stderr_cannot_credit_valid_stdout(self):
        for changes in [{"returncode": 1}, {"cleanup_complete": False}, {"status": "timeout"},
                        {"status": "cancelled"}, {"stderr_bytes": 1}, {"stderr_bytes": True},
                        {"elapsed_ms": True}, {"returncode": False}]:
            row = p._case(process(**changes), "TEXT")
            self.assertFalse(row["expected_match"], changes)
            self.assertIsNone(row["observation"], changes)

    def test_malformed_duplicate_nonfinite_boolean_and_unclosed_outputs_are_refused(self):
        bad = [b'{"version":1,"version":1}', b'{"x":NaN}', b'"' + CANARY.encode() + b'"', b"[1]",
               json.dumps(observation(status=["completed"])).encode(),
               json.dumps(observation(observed_bytes=True)).encode(),
               json.dumps(observation(read_calls=0)).encode(),
               json.dumps(observation(eof=False)).encode(),
               json.dumps(observation(descriptor_closed=False)).encode(),
               json.dumps(observation(observed_sha256="A" * 64)).encode(), b"x" * (p.MAX_OUTPUT + 1)]
        for raw in bad:
            row = p._case(process(stdout=raw), "TEXT")
            self.assertFalse(row["expected_match"])
            self.assertIsNone(row["observation"])
            self.assertNotIn(CANARY, json.dumps(row))

    def test_eof_with_wrong_hash_or_short_binary_is_retained_as_mismatch(self):
        for value, mode in [(observation(observed_sha256="0" * 64), "TEXT"),
                            (observation(mode="BINARY", observed_bytes=26,
                             observed_sha256=p.sha256(bytes(range(26)))), "BINARY")]:
            row = p._case(process(value), mode)
            self.assertEqual("completed", row["status"])
            self.assertFalse(row["expected_match"])
            self.assertEqual(value, row["observation"])

    def test_run_keeps_both_original_cases_and_fixed_owned_runner_budgets(self):
        requests = []
        def runner(command, request, **limits):
            value = json.loads(request)
            requests.append((command, value, limits))
            self.assertEqual(p.FIXTURE, Path(value["path"]).read_bytes())
            return process(observation(value["mode"]))
        with patch.object(p.os, "name", "nt"):
            report = p.run_probe(runner=runner)
        self.assertEqual("observed", report["status"])
        self.assertTrue(report["source_unchanged"])
        self.assertFalse(report["installed_adb_proven"])
        self.assertEqual(list(p.MODES), [r[1]["mode"] for r in requests])
        for command, request, limits in requests:
            self.assertEqual(["-I", str(Path(p.__file__).resolve()), "_worker"], command[1:])
            self.assertEqual({"deadline": 10, "max_output": 4096}, limits)
        self.assertEqual({"TEXT", "BINARY"}, {x["mode"] for x in report["cases"]})

    def test_fixture_mutation_suppresses_overall_success(self):
        def runner(command, request, **limits):
            value = json.loads(request)
            Path(value["path"]).write_bytes(b"x" * 768)
            return process(observation(value["mode"]))
        with patch.object(p.os, "name", "nt"):
            report = p.run_probe(runner=runner)
        self.assertEqual("refused", report["status"])
        self.assertFalse(report["source_unchanged"])

    def test_unknown_cleanup_stops_new_dispatch_and_preserves_fixture(self):
        requests = []
        handles = []
        original_open = Path.open
        def capture(path, *args, **kwargs):
            handle = original_open(path, *args, **kwargs)
            if args == ("x+b",):
                handles.append(handle)
            return handle
        def runner(command, request, **limits):
            requests.append(json.loads(request))
            return process(cleanup_complete=False)
        with tempfile.TemporaryDirectory() as root:
            with (patch.object(p.os, "name", "nt"), patch.object(p.tempfile, "mkdtemp", return_value=root),
                  patch.object(Path, "open", capture)):
                report = p.run_probe(runner=runner)
            self.assertEqual(1, len(requests))
            self.assertEqual("refused", report["status"])
            self.assertEqual(1, len(report["cases"]))
            self.assertTrue(report["fixture_retained"])
            self.assertTrue((Path(root) / "original-768.bin").is_file())
            self.assertEqual(1, len(handles))
            self.assertTrue(handles[0].closed)
            self.assertNotIn(root, json.dumps(report))

    def test_noncompleted_or_unparsed_client_stops_second_dispatch(self):
        for changes in [{"status": "spawn_failed"}, {"status": "timeout"},
                        {"status": "output_limit"}, {"stdout": b"{"}]:
            requests = []
            def runner(command, request, **limits):
                requests.append(json.loads(request))
                return process(**changes)
            with patch.object(p.os, "name", "nt"):
                report = p.run_probe(runner=runner)
            self.assertEqual(1, len(requests), changes)
            self.assertEqual("refused", report["status"])

    def test_same_contents_with_changed_mtime_still_refuses(self):
        requests = []
        def runner(command, request, **limits):
            value = json.loads(request)
            requests.append(value)
            path = Path(value["path"])
            before = path.stat()
            p.os.utime(path, ns=(before.st_atime_ns, before.st_mtime_ns + 10_000_000))
            return process(observation(value["mode"]))
        with patch.object(p.os, "name", "nt"):
            report = p.run_probe(runner=runner)
        self.assertEqual(2, len(requests))
        self.assertEqual("refused", report["status"])
        self.assertFalse(report["source_unchanged"])

    def test_spawn_exception_retains_partial_refusal_without_private_text(self):
        for failure in (OSError, RuntimeError):
            def fail(*args, **kwargs):
                raise failure(CANARY)
            with tempfile.TemporaryDirectory() as root:
                with patch.object(p.os, "name", "nt"), patch.object(p.tempfile, "mkdtemp", return_value=root):
                    report = p.run_probe(runner=fail)
                self.assertTrue(report["fixture_retained"])
            self.assertEqual("refused", report["status"])
            self.assertEqual(1, len(report["cases"]))
            self.assertNotIn(CANARY, json.dumps(report))

    def test_nonwindows_is_explicit_unsupported_without_launch(self):
        with patch.object(p.os, "name", "posix"), patch.object(p, "tempfile") as temp:
            report = p.run_probe(runner=lambda *a, **kw: self.fail("launch"))
        self.assertEqual("unsupported_host", report["status"])
        self.assertEqual([], report["cases"])
        temp.TemporaryDirectory.assert_not_called()


if __name__ == "__main__":
    unittest.main()
