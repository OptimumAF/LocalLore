"""Passive stream diagnostics exercised with original tiny data; no device IO.

Copyright 2026 LocalLore contributors. SPDX-License-Identifier: Apache-2.0
"""
from contextlib import ExitStack, redirect_stdout
import io
import json
from pathlib import Path
import subprocess
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import patch

from scripts.tests.test_receipt_real_stream_guards import StreamFixture, r


class ReceiptStreamTraceIntegrationTests(unittest.TestCase):
    def capture_failure(self, state, expected):
        with redirect_stdout(io.StringIO()) as output:
            with self.assertRaises(type(expected)) as caught:
                r.stream_authorized(state.value, 10310, state.proposal, state.authorization, state.root)
        self.assertIs(caught.exception, expected)
        return r.source_trace.extract_source_stream_trace(output.getvalue().encode("ascii"))

    def test_timeout_cursor_is_host_only_and_original_exception_survives(self):
        for count in (0, 17, r.PROBE_BYTES):
            with self.subTest(count=count), tempfile.TemporaryDirectory() as directory, ExitStack() as stack:
                state = StreamFixture(Path(directory))
                original = subprocess.TimeoutExpired(["private-path-never-emitted"], 1, output=b"private")
                def child(*args, **kwargs):
                    kwargs["stdin"].read(count)
                    raise original
                run = state.mocks(stack, child=child)
                trace = self.capture_failure(state, original)
                self.assertEqual(trace["phase"], "CLIENT")
                self.assertEqual(trace["source_position"], count)
                self.assertTrue(trace["source_verified"])
                self.assertTrue(trace["client_timed_out"])
                self.assertIsNone(trace["client_returncode"])
                self.assertGreater(trace["client_timeout_ms"], 0)
                self.assertLessEqual(trace["client_timeout_ms"], 150000)
                self.assertEqual(run.call_count, 1)

    def test_nonzero_keeps_legacy_result_and_adds_only_bounded_trace(self):
        with tempfile.TemporaryDirectory() as directory, ExitStack() as stack:
            state = StreamFixture(Path(directory))
            state.mocks(stack, child=lambda *a, **k: SimpleNamespace(returncode=7))
            status, raw = state.invoke()
            self.assertEqual(status, 2)
            lines = raw.splitlines()
            self.assertEqual(len(lines), 2)
            self.assertEqual(json.loads(lines[0]), {"version": 1, "source_bytes": r.PROBE_BYTES,
                "source_verified": True, "client_returncode": 7,
                "remote_exit_status_known": False, "destination_verified": False})
            trace = r.source_trace.extract_source_stream_trace(raw.encode("ascii"))
            self.assertEqual(trace["phase"], "COMPLETE")
            self.assertEqual(trace["client_returncode"], 7)
            self.assertFalse(trace["client_timed_out"])

    def test_success_output_is_exact_original_six_key_object(self):
        with tempfile.TemporaryDirectory() as directory, ExitStack() as stack:
            state = StreamFixture(Path(directory)); state.mocks(stack)
            status, raw = state.invoke()
            self.assertEqual(status, 0)
            self.assertEqual(raw, json.dumps({"version": 1, "source_bytes": r.PROBE_BYTES,
                "source_verified": True, "client_returncode": 0,
                "remote_exit_status_known": False, "destination_verified": False}) + "\n")

    def test_depleted_existing_parent_reserve_refuses_before_client(self):
        with tempfile.TemporaryDirectory() as directory, ExitStack() as stack:
            state = StreamFixture(Path(directory))
            state.parent["deadline_epoch"] = 100.0; state.rewrite_parent()
            run = state.mocks(stack)
            stack.enter_context(patch.object(r.time, "time", side_effect=[90.0, 96.0]))
            with redirect_stdout(io.StringIO()) as output, self.assertRaises(AssertionError):
                r.stream_authorized(state.value, 10310, state.proposal, state.authorization, state.root)
            trace = r.source_trace.extract_source_stream_trace(output.getvalue().encode("ascii"))
            self.assertEqual(trace["phase"], "CLIENT")
            self.assertEqual(trace["client_timeout_ms"], 0)
            run.assert_not_called()

    def test_postlease_refusal_preserves_exception_and_no_success_record(self):
        with tempfile.TemporaryDirectory() as directory, ExitStack() as stack:
            state = StreamFixture(Path(directory)); state.mocks(stack)
            original = RuntimeError("private lease reason")
            state.lease.check = lambda: None
            stack.enter_context(patch.object(state.lease, "check", side_effect=[None, None, original]))
            trace = self.capture_failure(state, original)
            self.assertEqual(trace["phase"], "LEASE_POSTCHECK")
            self.assertEqual(trace["client_returncode"], 0)

    def test_diagnostic_constructor_method_clock_and_writer_failures_do_not_replace_failure(self):
        for mode in ("constructor", "method", "clock", "snapshot_clock", "json", "writer"):
            with self.subTest(mode=mode), tempfile.TemporaryDirectory() as directory, ExitStack() as stack:
                state = StreamFixture(Path(directory))
                original = subprocess.TimeoutExpired("never-public", 1)
                def child(*a, **k): raise original
                state.mocks(stack, child=child)
                if mode == "constructor":
                    stack.enter_context(patch.object(r.source_trace, "SourceStreamTrace", side_effect=KeyboardInterrupt()))
                elif mode == "method":
                    stack.enter_context(patch.object(r.source_trace.SourceStreamTrace, "phase", side_effect=KeyboardInterrupt()))
                elif mode == "clock":
                    stack.enter_context(patch.object(r.source_trace.SourceStreamTrace, "_clock", side_effect=KeyboardInterrupt()))
                elif mode == "snapshot_clock":
                    stack.enter_context(patch.object(r.source_trace.SourceStreamTrace, "_clock", side_effect=[0, KeyboardInterrupt()]))
                elif mode == "json":
                    stack.enter_context(patch.object(r.source_trace.SourceStreamTrace, "json", side_effect=KeyboardInterrupt()))
                else:
                    stack.enter_context(patch("builtins.print", side_effect=BrokenPipeError()))
                self.capture_failure(state, original)

    def test_bad_diagnostic_constructor_and_observer_cannot_change_success(self):
        for method in ("__init__", "source_verified", "client_start", "client_return", "position", "phase"):
            with self.subTest(method=method), tempfile.TemporaryDirectory() as directory, ExitStack() as stack:
                state = StreamFixture(Path(directory)); state.mocks(stack)
                stack.enter_context(patch.object(r.source_trace.SourceStreamTrace, method, side_effect=KeyboardInterrupt()))
                status, raw = state.invoke()
                self.assertEqual(status, 0)
                self.assertEqual(json.loads(raw)["client_returncode"], 0)
                self.assertEqual(len(raw.splitlines()), 1)


if __name__ == "__main__":
    unittest.main()
