"""Closed synthetic failure observations never replace the successful runner gate.

Copyright 2026 LocalLore contributors. SPDX-License-Identifier: Apache-2.0
"""
import json
from pathlib import Path
import shlex
import sys
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import patch
from scripts.tests import test_receipt_setup_qualification as fixture

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "benchmarks"))
import receipt_setup_qualification as q


def payload():
    return {"version": 1, "case": "ACCEPT", "expected": "READY", "actual": "FAILED", "error": "STORAGE",
            "events_total": 2, "events_saturated": False, "events": ["IMPORT_START", "IMPORT_FAILED"],
            "source": {"opened": 1, "closed": 1, "active": 0, "reads": 2, "bytes": 63,
                       "reads_saturated": False, "bytes_saturated": False}}


def raw(value):
    return json.dumps(value, separators=(",", ":")).encode("ascii")


def wire(value=None):
    return q.FAILURE_PREFIX.encode("ascii") + raw(payload() if value is None else value) + b"\n" + q.FAILURE_STATUS.encode("ascii") + b"\n"


class SetupFailureTests(unittest.TestCase):
    def reject(self, value):
        with self.assertRaises((AssertionError, ValueError, UnicodeError)):
            q.parse_failure_trace(raw(value))

    def test_exact_finite_observation_is_not_a_success_record(self):
        value = q.extract_failure_trace(wire())
        self.assertEqual(value, payload())
        with self.assertRaises(AssertionError):
            q.parse_instrumentation(wire(), q.INITIAL_CLASS, q.INITIAL_METHODS)

    def test_every_case_phase_error_and_event_is_closed(self):
        for key, options in (("case", ("ACCEPT", "CANCEL_BEFORE", "CANCEL_AFTER", "DRAIN")),
                             ("expected", q.FAILURE_PHASES), ("actual", q.FAILURE_PHASES), ("error", q.FAILURE_CODES)):
            for choice in options:
                value = payload(); value[key] = choice
                self.assertEqual(q.parse_failure_trace(raw(value))[key], choice)
            for choice in (True, 1, None, {}, [], "unknown", "secret/path", "READY\n"):
                value = payload(); value[key] = choice; self.reject(value)
        for event in q.FAILURE_EVENTS:
            value = payload(); value["events"] = [event]; q.parse_failure_trace(raw(value))
        for events in (None, {}, "IMPORT_START", [True], ["secret"], ["IMPORT_START"] * 17):
            value = payload(); value["events"] = events; self.reject(value)

    def test_extra_missing_nested_and_untrusted_text_fields_refuse(self):
        for key in payload():
            value = payload(); value.pop(key); self.reject(value)
        for key in ("message", "cause", "stack", "path", "uri", "story", "pid", "error_class"):
            value = payload(); value[key] = "private canary"; self.reject(value)
            value = payload(); value["source"][key] = "private canary"; self.reject(value)
        for key in payload()["source"]:
            value = payload(); value["source"].pop(key); self.reject(value)

    def test_counter_types_limits_and_explicit_saturation(self):
        for key in ("opened", "closed", "active", "reads", "bytes"):
            for count in (0, q.FAILURE_LIMIT):
                value = payload(); value["source"][key] = count; q.parse_failure_trace(raw(value))
            for count in (-1, q.FAILURE_LIMIT + 1, True, 1.0, None, "1"):
                value = payload(); value["source"][key] = count; self.reject(value)
        for flag, count in (("reads_saturated", "reads"), ("bytes_saturated", "bytes")):
            value = payload(); value["source"][flag] = True; self.reject(value)
            value["source"][count] = q.FAILURE_LIMIT; q.parse_failure_trace(raw(value))
            for invalid in (1, 0, None, "true"):
                value["source"][flag] = invalid; self.reject(value)
        for total in (-1, 1, q.FAILURE_LIMIT + 1, True, 2.0):
            value = payload(); value["events_total"] = total; self.reject(value)
        value = payload(); value["events_saturated"] = True; self.reject(value)
        value["events_total"] = q.FAILURE_LIMIT; q.parse_failure_trace(raw(value))
        for invalid in (1, 0, None, "false"):
            value["events_saturated"] = invalid; self.reject(value)

    def test_independent_progress_and_last_error_have_no_causal_authority(self):
        value = payload(); value["actual"] = "READY"; value["source"].update(opened=0, closed=1, active=1)
        self.assertEqual(q.parse_failure_trace(raw(value)), value)

    def test_ascii_wire_bound_duplicate_keys_and_integer_version(self):
        base = raw(payload())
        limit = 2048 - len(q.FAILURE_PREFIX.encode("ascii"))
        self.assertEqual(q.parse_failure_trace(base + b" " * (limit - len(base))), payload())
        for invalid in (base + b" " * (limit - len(base) + 1), base + b"\n", b"\xef\xbb\xbf" + base,
                        base.replace(b'"version":1', b'"version":1,"version":1'), b"[]", b"null"):
            with self.assertRaises((AssertionError, ValueError, UnicodeError)):
                q.parse_failure_trace(invalid)
        for version in (True, 1.0, 2, "1"):
            value = payload(); value["version"] = version; self.reject(value)

    def test_one_adjacent_status_pair_only_and_no_passing_marker(self):
        for invalid in (wire() + wire(), wire() + b"OK (3 tests)\n", wire() + b"OK (1 test)\n",
                        wire().replace(b"1337", b"1338"), wire().replace(b"\nINSTRUMENTATION_STATUS_CODE", b"\nnoise\nINSTRUMENTATION_STATUS_CODE"),
                        q.FAILURE_STATUS.encode("ascii") + b"\n", wire().splitlines()[0] + b"\n",
                        wire().replace(b"locallore_receipt_failure_v1", b"locallore_receipt_failure_v2")):
            with self.assertRaises((AssertionError, ValueError, UnicodeError)):
                q.extract_failure_trace(invalid)
        self.assertIsNone(q.extract_failure_trace(b"INSTRUMENTATION_CODE: -1\n"))

    def test_lf_and_crlf_transport_preserve_strict_existing_framing(self):
        for ending in (b"\n", b"\r\n"):
            self.assertEqual(q.extract_failure_trace(wire().replace(b"\n", ending)), payload())
        for invalid in (wire().replace(b"\n", b"\r\r\n"), wire().replace(b"\n", b"\r"),
                        wire().replace(b"\n", b"\r\n", 1)):
            with self.assertRaises(AssertionError):
                q.extract_failure_trace(invalid)

    def test_full_original_runner_context_refuses_failure_and_passing_markers(self):
        passing = fixture.transcript()
        self.assertEqual(q.parse_instrumentation(passing, q.INITIAL_CLASS, q.INITIAL_METHODS)["passed"], 3)
        failure = passing.replace(b"INSTRUMENTATION_STATUS_CODE: 1\n",
                                  b"INSTRUMENTATION_STATUS_CODE: 1\n" + wire(), 1)
        failure = failure.replace(b"INSTRUMENTATION_STATUS_CODE: 0", b"INSTRUMENTATION_STATUS_CODE: -2", 1)
        failure = failure.replace(b"OK (3 tests)", b"FAILURES!!!\nTests run: 3, Failures: 1")
        self.assertEqual(q.extract_failure_trace(failure), payload())
        with self.assertRaises(AssertionError):
            q.parse_instrumentation(failure, q.INITIAL_CLASS, q.INITIAL_METHODS)
        with self.assertRaises(AssertionError):
            q.extract_failure_trace(passing + wire())

    def test_actual_mock_owner_retains_raw_and_observation_but_never_binds_helper(self):
        with tempfile.TemporaryDirectory() as directory:
            proposal = fixture.proposal(Path(directory)); lease = fixture.Lease(proposal)
            owner = q.Owner(proposal, lease); transport = fixture.Transport(proposal, lease)
            observed = fixture.transcript().replace(b"INSTRUMENTATION_STATUS_CODE: 1\n",
                b"INSTRUMENTATION_STATUS_CODE: 1\n" + wire(), 1).replace(
                b"INSTRUMENTATION_STATUS_CODE: 0", b"INSTRUMENTATION_STATUS_CODE: -2", 1).replace(
                b"OK (3 tests)", b"FAILURES!!!\nTests run: 3, Failures: 1")
            def dispatch(command, **kwargs):
                result = transport(command, **kwargs)
                if command[3] == "shell" and tuple(shlex.split(command[4])) == q.INITIAL_INSTRUMENT:
                    result.stdout = observed
                return result
            with patch.object(q.host, "run_process", side_effect=dispatch), patch.object(
                    q.shutil, "disk_usage", return_value=SimpleNamespace(free=20 * 1024 ** 3)):
                with self.assertRaises(AssertionError):
                    q.run_cohort(owner)
            self.assertEqual(transport.instruments, 1)
            self.assertEqual((owner.commands / ("command-%04d.stdout.bin" % owner.count)).read_bytes(), observed)
            self.assertEqual(json.loads((owner.directory / "initial-failure-trace-v1.json").read_bytes()), payload())
            self.assertFalse((owner.directory / "after-initial-facts.json").exists())
            self.assertFalse((owner.directory / "restart-instrumentation-v1.json").exists())

    def test_observation_persists_before_unchanged_failed_runner_refusal(self):
        with tempfile.TemporaryDirectory() as directory:
            owner = SimpleNamespace(directory=Path(directory))
            q.observe_failure_trace(owner, wire(), "initial")
            self.assertEqual(json.loads((owner.directory / "initial-failure-trace-v1.json").read_bytes()), payload())
            with self.assertRaises(AssertionError):
                q.parse_instrumentation(wire(), q.INITIAL_CLASS, q.INITIAL_METHODS)
            with self.assertRaises(AssertionError):
                q.observe_failure_trace(owner, wire(), "final")


if __name__ == "__main__":
    unittest.main()
