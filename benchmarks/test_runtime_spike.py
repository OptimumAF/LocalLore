"""Synthetic host-boundary tests; no runtime package, model, or phone is used."""
import ctypes
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import threading
import time
import unittest
from unittest.mock import patch

import runtime_spike as spike


CANARY = "SYNTHETIC-PRIVATE-REVIEW-731"


def response(**changes):
    value = dict(version=1, status="completed", text="synthetic proposal", error=None,
                 load_ms=1.0, generation_ms=2.0, input_tokens=16, output_tokens=2,
                 schema_enforced=True, thinking_disabled=True, template_applied=True)
    value.update(changes)
    return value


def process_result(value=None, status="completed"):
    return spike.ProcessResult(status, 1, json.dumps(value or response()).encode(), 0, 0, True)


def request(role):
    return dict(version=1, role=role, prompt="synthetic fixture", schema=None,
                max_tokens=350 if role == "director" else 220, context_tokens=4096, threads=4)


def fixture():
    return dict(version=1, case="gift", preflight_error=None, revision=0, director=request("director"))


class ResponseTests(unittest.TestCase):
    def test_valid_completed_and_both_runtime_error_vocabularies(self):
        self.assertEqual(spike.parse_worker(json.dumps(response()).encode()), response())
        self.assertTrue({"runtime_unavailable", "model_invalid", "model_load_failed",
                         "unsupported_template", "decode_failed", "unexpected_output"}
                        .issubset(spike.WORKER_ERRORS))
        for category in spike.WORKER_ERRORS:
            with self.subTest(category=category):
                value = response(status="error", text="", error=category)
                self.assertEqual(spike.parse_worker(json.dumps(value).encode()), value)

    def test_surrogate_deep_duplicate_nonfinite_and_nonobject_are_rejected(self):
        raw = json.dumps(response()).encode()
        invalid = [b"[" * 2000 + b"]" * 2000, b"[]", b"null", b"not json", b"\xff",
                   raw[:-1] + b',"version":1}',
                   json.dumps(response(text="\ud800")).encode(),
                   json.dumps(response(load_ms=float("nan"))).encode(),
                   json.dumps(response(generation_ms=float("inf"))).encode()]
        for value in invalid:
            with self.subTest(shape=value[:40]):
                self.assertIsNone(spike.parse_worker(value))

    def test_strict_types_errors_bounds_and_schema(self):
        invalid = [dict(version=True), dict(error=CANARY), dict(text=CANARY * 2000),
                   dict(status="error", text="", error=[]),
                   dict(status="error", text="", error={}),
                   dict(status="error", text="", error=CANARY),
                   dict(status="error", text="private", error="model_invalid"),
                   dict(schema_enforced=1), dict(thinking_disabled="true"),
                   dict(template_applied=None), dict(load_ms=-1), dict(load_ms=180001),
                   dict(input_tokens=4097), dict(input_tokens=0.5), dict(input_tokens=True),
                   dict(output_tokens=351), dict(output_tokens=-1)]
        for change in invalid:
            with self.subTest(change=change):
                self.assertIsNone(spike.parse_worker(json.dumps(response(**change)).encode()))
        value = response(); value["unknown"] = CANARY
        self.assertIsNone(spike.parse_worker(json.dumps(value).encode()))
        value = response(); del value["text"]
        self.assertIsNone(spike.parse_worker(json.dumps(value).encode()))


class ModelAndAggregateTests(unittest.TestCase):
    def test_missing_size_hash_and_unreadable_models_never_launch_worker(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "synthetic.gguf"
            artifact = ("synthetic-test-only", 3, hashlib.sha256(b"abc").hexdigest())
            with patch.dict(spike.ARTIFACTS, {"llama": artifact}), patch.object(spike, "oracle", return_value=fixture()), patch.object(spike, "run_process") as run:
                for data, expected in [(None, "model_missing"), (b"a", "model_size_mismatch"), (b"abd", "model_hash_mismatch")]:
                    if data is not None:
                        path.write_bytes(data)
                    result = spike.experiment("llama", sys.executable, path, "oracle", "helper")
                    self.assertEqual(result["status"], expected)
                    self.assertEqual(result["attempted_roles"], 0)
                path.write_bytes(b"abc")
                self.assertIsNone(spike.verify_model("llama", path))
                run.assert_not_called()
            with patch.object(spike, "oracle", return_value=fixture()), patch.object(spike, "verify_model", side_effect=OSError(CANARY)), patch.object(spike, "run_process") as run:
                self.assertEqual(spike.experiment("litert", sys.executable, path, "oracle")["status"], "model_unreadable")
                run.assert_not_called()

    def test_aggregate_omits_text_paths_and_uses_isolated_narrator_request(self):
        proposed = CANARY + " proposal"
        narrated = CANARY + " narration"
        director = fixture(); director["director"]["prompt"] = CANARY
        accepted = dict(status="accepted", error=None, narrator=request("narrator"))
        committed = dict(status="committed", error=None, revision=1, events=1,
                         exact_retry_unchanged=True, recipient_observations=1, absent_observations=0)
        with patch.object(spike, "oracle", side_effect=[director, accepted, committed]) as oracle, patch.object(spike, "verify_model", return_value=None), patch.object(spike, "run_process", side_effect=[process_result(response(text=proposed)), process_result(response(text=narrated))]) as run:
            report = spike.experiment("litert", sys.executable, CANARY, "oracle")
        self.assertEqual(report["status"], "committed")
        self.assertEqual(report["attempted_roles"], 2)
        self.assertEqual(len(report["roles"]), 2)
        self.assertNotIn(CANARY, json.dumps(report))
        self.assertNotIn(CANARY, run.call_args_list[1].args[1].decode())
        self.assertEqual(oracle.call_args_list[1].args[3], proposed.encode())
        self.assertEqual(json.loads(oracle.call_args_list[2].args[3])["narration"], narrated)
        self.assertFalse(report["quality_assessed"])
        self.assertFalse(report["phone_qualified"])

    def test_every_failed_role_remains_in_attempted_denominator(self):
        for status in ("timeout", "cancelled", "output_limit", "cleanup_failed"):
            for fail_second in (False, True):
                with self.subTest(status=status, fail_second=fail_second):
                    values = [process_result(status=status)]
                    oracle_values = [fixture()]
                    if fail_second:
                        values.insert(0, process_result())
                        oracle_values.append(dict(status="accepted", error=None, narrator=request("narrator")))
                    with patch.object(spike, "oracle", side_effect=oracle_values), patch.object(spike, "verify_model", return_value=None), patch.object(spike, "run_process", side_effect=values):
                        report = spike.experiment("litert", sys.executable, "model", "oracle")
                    self.assertEqual(report["status"], status)
                    self.assertEqual(report["attempted_roles"], 2 if fail_second else 1)
                    self.assertEqual(len(report["roles"]), report["attempted_roles"])
                    self.assertEqual(report["roles"][-1]["process_status"], status)

    def test_arbitrary_worker_and_oracle_errors_cannot_enter_report(self):
        for worker in (response(status="error", text="", error=CANARY), response(text="\ud800")):
            with patch.object(spike, "oracle", return_value=fixture()), patch.object(spike, "verify_model", return_value=None), patch.object(spike, "run_process", return_value=process_result(worker)):
                report = spike.experiment("litert", sys.executable, CANARY, "oracle")
            self.assertEqual(report["status"], "invalid_worker_response")
            self.assertNotIn(CANARY, json.dumps(report))
        bad = fixture(); bad["preflight_error"] = CANARY
        with patch.object(spike, "oracle", return_value=bad), patch.object(spike, "verify_model") as verify:
            report = spike.experiment("litert", sys.executable, CANARY, "oracle")
        self.assertEqual(report["status"], "oracle_failed")
        self.assertNotIn(CANARY, json.dumps(report))
        verify.assert_not_called()

    def test_shared_deadline_and_cancellation_clock_span_both_roles(self):
        accepted = dict(status="accepted", error=None, narrator=request("narrator"))
        committed = dict(status="committed", error=None)
        with patch.object(spike, "oracle", side_effect=[fixture(), accepted, committed]), patch.object(spike, "verify_model", return_value=None), patch.object(spike.time, "monotonic", side_effect=[100, 101, 109]), patch.object(spike, "run_process", side_effect=[process_result(), process_result()]) as run:
            report = spike.experiment("litert", sys.executable, "model", "oracle", deadline=60, cancel_after=2)
        self.assertEqual(report["status"], "committed")
        self.assertEqual([call.args[2] for call in run.call_args_list], [59, 51])
        self.assertEqual([call.kwargs["cancel_at"] for call in run.call_args_list], [102, 102])

    def test_expired_shared_budget_records_unstarted_narrator_failure(self):
        accepted = dict(status="accepted", error=None, narrator=request("narrator"))
        with patch.object(spike, "oracle", side_effect=[fixture(), accepted]), patch.object(spike, "verify_model", return_value=None), patch.object(spike.time, "monotonic", side_effect=[100, 101, 161]), patch.object(spike, "run_process", return_value=process_result()) as run:
            report = spike.experiment("litert", sys.executable, "model", "oracle", deadline=60)
        self.assertEqual(report["status"], "timeout")
        self.assertEqual(report["attempted_roles"], 2)
        self.assertEqual(report["roles"][-1]["wall_ms"], 0)
        self.assertEqual(run.call_count, 1)


class ProcessOwnershipTests(unittest.TestCase):
    def command(self, source):
        return [sys.executable, "-B", "-c", source]

    def test_pre_cancelled_never_spawns_and_rejects_invalid_budgets(self):
        cancel = threading.Event(); cancel.set()
        with patch.object(spike.subprocess, "Popen") as spawn:
            result = spike.run_process(["does-not-exist"], cancel=cancel)
        self.assertEqual(result.status, "cancelled")
        self.assertTrue(result.cleanup_complete)
        spawn.assert_not_called()
        for budget in (0, -1, 181, float("nan")):
            with self.subTest(budget=budget), self.assertRaises(ValueError):
                spike.run_process([], deadline=budget)

    def test_success_drains_both_pipes_without_disclosing_stderr(self):
        source = "import sys;sys.stdin.buffer.read();sys.stdout.buffer.write(b'o'*12000);sys.stdout.flush();sys.stderr.buffer.write(b'e'*12000);sys.stderr.flush()"
        result = spike.run_process(self.command(source), b"input", deadline=3)
        self.assertEqual(result.status, "completed")
        self.assertEqual(result.stdout, b"o" * 12000)
        self.assertEqual(result.stderr_bytes, 12000)
        self.assertTrue(result.cleanup_complete)
        self.assertNotIn("eeee", repr(result))

    def test_combined_pipe_overflow_kills_owned_process(self):
        source = "import sys,threading;sys.stdin.buffer.read();t=threading.Thread(target=lambda:sys.stderr.buffer.write(b'e'*200000));t.start();sys.stdout.buffer.write(b'o'*200000);t.join()"
        result = spike.run_process(self.command(source), b"input", deadline=3, max_output=65536)
        self.assertEqual(result.status, "output_limit")
        self.assertLessEqual(len(result.stdout) + result.stderr_bytes, 65536)
        self.assertTrue(result.cleanup_complete)

    def test_non_reader_cannot_block_large_stdin_or_deadline(self):
        start = time.monotonic()
        result = spike.run_process(self.command("import time;time.sleep(30)"), b"x" * 100000, deadline=.3)
        self.assertEqual(result.status, "timeout")
        self.assertTrue(result.cleanup_complete)
        self.assertLess(time.monotonic() - start, 3)

    def test_inflight_cancellation_reaps_process(self):
        cancel = threading.Event()
        timer = threading.Timer(.2, cancel.set); timer.start()
        try:
            result = spike.run_process(self.command("import sys,time;sys.stdin.buffer.read();time.sleep(30)"), b"input", deadline=3, cancel=cancel)
        finally:
            timer.cancel()
        self.assertEqual(result.status, "cancelled")
        self.assertTrue(result.cleanup_complete)
        self.assertLess(result.elapsed_ms, 2500)

    @unittest.skipUnless(os.name == "nt", "Windows process/job ownership check")
    def test_exited_root_with_live_grandchild_pipes_is_reaped(self):
        source = "import sys,subprocess;sys.stdin.buffer.read();p=subprocess.Popen([sys.executable,'-c','import time;time.sleep(30)']);print(p.pid,flush=True)"
        result = spike.run_process(self.command(source), b"input", deadline=.5)
        self.assertEqual(result.status, "timeout")
        self.assertTrue(result.cleanup_complete)
        pid = int(result.stdout.strip())
        kernel = ctypes.WinDLL("kernel32", use_last_error=True)
        kernel.OpenProcess.argtypes = [ctypes.c_ulong, ctypes.c_int, ctypes.c_ulong]
        kernel.OpenProcess.restype = ctypes.c_void_p
        kernel.WaitForSingleObject.argtypes = [ctypes.c_void_p, ctypes.c_ulong]
        kernel.CloseHandle.argtypes = [ctypes.c_void_p]
        handle = kernel.OpenProcess(0x00100000, False, pid)
        if handle:
            try:
                # Job accounting can reach zero just before the process handle
                # becomes signaled. Require bounded termination, not that race.
                self.assertEqual(kernel.WaitForSingleObject(handle, 1000), 0)
            finally:
                kernel.CloseHandle(handle)
        else:
            self.assertEqual(ctypes.get_last_error(), 87)  # Process no longer exists.

    @unittest.skipUnless(os.name == "nt", "Windows failed-cleanup watchdog")
    def test_cleanup_failure_with_live_readers_returns_without_close_deadlock(self):
        # Deliberately withhold job cleanup, then release the real job in finally.
        # The outer watchdog kills the test process if a pipe-close lock regresses;
        # closing its real job handle then kills the owned sleeping descendant.
        source = r'''
import json,sys,time
from unittest.mock import patch
import runtime_spike as m
original=m.WindowsJob
owners=[]
class WithheldJob:
    def __init__(self,pid):
        self.owner=original(pid);owners.append(self.owner)
    def close(self):return False
try:
    with patch.object(m,'WindowsJob',WithheldJob):
        result=m.run_process([sys.executable,'-B','-c','import sys,time;sys.stdin.buffer.read();time.sleep(30)'],b'input',deadline=.1)
    print(json.dumps({'status':result.status,'clean':result.cleanup_complete,'elapsed':result.elapsed_ms}),flush=True)
finally:
    for owner in owners:owner.close()
'''
        completed = subprocess.run(self.command(source), cwd=Path(spike.__file__).parent,
                                   capture_output=True, timeout=15, check=True)
        value = json.loads(completed.stdout)
        self.assertEqual(value["status"], "cleanup_failed")
        self.assertFalse(value["clean"])
        self.assertLess(value["elapsed"], 14000)
        self.assertEqual(completed.stderr, b"")


if __name__ == "__main__":
    unittest.main()
