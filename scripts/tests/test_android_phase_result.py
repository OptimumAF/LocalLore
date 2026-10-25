"""Original model/device-free strict phase-result regressions.

Copyright 2026 LocalLore contributors. SPDX-License-Identifier: Apache-2.0
"""
import copy
import json
from pathlib import Path
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "benchmarks"))
import android_phase_result as phase


def completed(**changes):
    value = dict(version=1, status="completed", error="none", model_execution=False,
                 journal_valid=True, checkpoint_count=2, last_phase="probe_kill", last_role="none",
                 fresh_reader_process=True, exit_history_available=True, exit_records_examined=1,
                 exit_instance_matches=1, exit_instance_matched=True, exit_reason=2, exit_status=9)
    value.update(changes)
    return value


def wire(value, ending=b"\n"):
    return (b"INSTRUMENTATION_RESULT: phase_result=" + json.dumps(value, separators=(",", ":")).encode()
            + ending + b"INSTRUMENTATION_CODE: -1" + ending)


class PhaseResultTest(unittest.TestCase):
    def test_exact_completed_lf_and_crlf_match(self):
        for ending in (b"\n", b"\r\n"):
            result = phase.parse_result(wire(completed(), ending))
            self.assertEqual(result, completed())
            self.assertTrue(phase.journal_verified(result))
            self.assertTrue(phase.control_passed(result))

    def test_unavailable_history_preserves_journal_without_instance_claim(self):
        result = phase.parse_result(wire(completed(exit_history_available=False, exit_records_examined=0,
            exit_instance_matches=0, exit_instance_matched=False, exit_reason=-1, exit_status=-1)))
        self.assertIsNotNone(result)
        self.assertTrue(phase.journal_verified(result))
        self.assertFalse(phase.control_passed(result))

    def test_empty_and_ambiguous_available_history_are_unknown(self):
        for examined, matches in ((0, 0), (16, 0), (2, 2), (16, 16)):
            result = phase.parse_result(wire(completed(exit_records_examined=examined,
                exit_instance_matches=matches, exit_instance_matched=False, exit_reason=-1, exit_status=-1)))
            self.assertIsNotNone(result)
            self.assertTrue(phase.journal_verified(result))
            self.assertFalse(phase.control_passed(result))

    def test_partial_checkpoint_or_not_fresh_is_observation_not_pass(self):
        for value in (completed(checkpoint_count=1, last_phase="probe_ready"),
                      completed(fresh_reader_process=False)):
            result = phase.parse_result(wire(value))
            self.assertEqual(result, value)
            self.assertFalse(phase.journal_verified(result))
            self.assertFalse(phase.control_passed(result))

    def test_exact_runtime_error_only(self):
        error = dict(version=1, status="error", error="phase_probe_failed", model_execution=False)
        result = phase.parse_result(wire(error))
        self.assertEqual(result, error)
        self.assertFalse(phase.journal_verified(result))
        self.assertFalse(phase.control_passed(result))
        for changes in (dict(error="private-error-canary"), dict(error=None), dict(journal_valid=True),
                        dict(model_execution=True), dict(version=True)):
            self.assertIsNone(phase.parse_result(wire(dict(error, **changes))))

    def test_unknown_missing_and_partial_error_fields_fail(self):
        for field in completed():
            value = completed()
            del value[field]
            self.assertIsNone(phase.parse_result(wire(value)), field)
        for field in ("pid", "uid", "session", "path", "description", "text", "extra"):
            self.assertIsNone(phase.parse_result(wire(completed(**{field: "private-content-canary"}))))
        self.assertIsNone(phase.parse_result(wire(completed(status="error", error="phase_probe_failed"))))

    def test_boolean_fields_never_accept_numbers(self):
        for field in ("model_execution", "journal_valid", "fresh_reader_process",
                      "exit_history_available", "exit_instance_matched"):
            for bad in (0, 1, "true", None, [], {}):
                self.assertIsNone(phase.parse_result(wire(completed(**{field: bad}))), (field, bad))

    def test_integer_fields_reject_float_boolean_and_oversized(self):
        for field in ("version", "checkpoint_count", "exit_records_examined", "exit_instance_matches",
                      "exit_reason", "exit_status"):
            for bad in (True, False, 1.0, "1", None, [], {}, 2 ** 63):
                self.assertIsNone(phase.parse_result(wire(completed(**{field: bad}))), (field, bad))

    def test_probe_count_phase_role_and_version_are_frozen(self):
        for changes in (dict(checkpoint_count=0), dict(checkpoint_count=3),
                        dict(checkpoint_count=1), dict(last_phase="probe_ready"),
                        dict(last_phase="before_model_initialize"), dict(last_phase="private-phase-canary"),
                        dict(last_role="director"), dict(journal_valid=False), dict(version=2),
                        dict(status="success"), dict(error=None), dict(model_execution=True)):
            self.assertIsNone(phase.parse_result(wire(completed(**changes))), changes)

    def test_exit_count_and_match_consistency(self):
        cases = (dict(exit_records_examined=17), dict(exit_instance_matches=17),
                 dict(exit_records_examined=-1), dict(exit_instance_matches=-1),
                 dict(exit_records_examined=0), dict(exit_history_available=False),
                 dict(exit_instance_matched=False), dict(exit_reason=-1), dict(exit_status=-1),
                 dict(exit_reason=-2), dict(exit_status=-2),
                 dict(exit_instance_matches=0), dict(exit_instance_matches=2, exit_records_examined=2))
        for changes in cases:
            self.assertIsNone(phase.parse_result(wire(completed(**changes))), changes)

    def test_unknown_exit_values_cannot_carry_numeric_observations(self):
        for changes in (dict(exit_reason=2), dict(exit_status=9), dict(exit_instance_matched=True)):
            unknown = completed(exit_records_examined=0, exit_instance_matches=0,
                                exit_instance_matched=False, exit_reason=-1, exit_status=-1)
            unknown.update(changes)
            self.assertIsNone(phase.parse_result(wire(unknown)))
        for value in (0, phase.MAX_INTEGER):
            self.assertIsNotNone(phase.parse_result(wire(completed(exit_reason=value, exit_status=value))))

    def test_duplicate_and_nonfinite_json_rejected(self):
        raw = wire(completed())
        for old, new in ((b'"version":1', b'"version":1,"version":1'),
                         (b'"exit_status":9', b'"exit_status":NaN'),
                         (b'"exit_status":9', b'"exit_status":Infinity'),
                         (b'"exit_status":9', b'"exit_status":-Infinity')):
            self.assertIsNone(phase.parse_result(raw.replace(old, new)))

    def test_wrapper_chatter_duplicates_wrong_order_and_failure_rejected(self):
        raw = wire(completed())
        rows = raw.splitlines(keepends=True)
        for malformed in (b"private-chatter-canary\n" + raw, raw + b"extra\n", b"\n" + raw,
                          raw + raw, rows[0] + rows[0] + rows[1], rows[1] + rows[0],
                          raw.replace(b"CODE: -1", b"CODE: 0"),
                          raw.replace(b"RESULT: phase_result=", b"RESULT: other="),
                          b"INSTRUMENTATION_RESULT: shortMsg=Process crashed.\nINSTRUMENTATION_CODE: 0\n"):
            self.assertIsNone(phase.parse_result(malformed))

    def test_mixed_crlf_control_bytes_wrong_types_and_bound_rejected(self):
        raw = wire(completed())
        for malformed in (raw.replace(b"\n", b"\r\n", 1), raw.replace(b"\n", b"\r\r\n"),
                          raw.replace(b'"none"', b'"\x00"', 1), raw.replace(b'"none"', b'"\xff"', 1),
                          b"x" * (phase.MAX_RAW + 1), raw.decode(), bytearray(raw), None, 1):
            self.assertIsNone(phase.parse_result(malformed))

    def test_bad_json_roots_and_nesting_do_not_escape(self):
        for body in (b"null", b"true", b"[]", b"42", b"{}", b"{", b"[" * 2000 + b"]" * 2000):
            self.assertIsNone(phase.parse_result(b"INSTRUMENTATION_RESULT: phase_result=" + body
                + b"\nINSTRUMENTATION_CODE: -1\n"))

    def test_predicates_revalidate_and_do_not_mutate_observations(self):
        value = completed()
        original = copy.deepcopy(value)
        self.assertTrue(phase.journal_verified(value))
        self.assertTrue(phase.control_passed(value))
        self.assertEqual(value, original)
        for bad in (None, [], "private-canary", dict(value, pid=1), dict(value, checkpoint_count=True)):
            self.assertFalse(phase.journal_verified(bad))
            self.assertFalse(phase.control_passed(bad))


if __name__ == "__main__":
    unittest.main()
