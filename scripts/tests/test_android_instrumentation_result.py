"""Synthetic protocol proofs. No ADB, private log, model, or network input."""
import json
from pathlib import Path
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from android_instrumentation_result import analyse_instrumentation, MAX_BYTES

CASES = ("org.locallore.app.CohortTest#a", "org.locallore.app.CohortTest#b",
         "org.locallore.app.CohortTest#c", "org.locallore.app.CohortTest#d")
CANARY = "PRIVATE_STORY_path_PID_token_9472"
SIGNATURE = "java.util.concurrent.TimeoutException: ReferenceQueueDaemon\nHardwareRenderer$DestroyContextRunnable"


def record(case, current=1, total=4, code="1", stack=None, **extras):
    cls, method = case.split("#")
    fields = {"class": cls, "test": method, "current": str(current), "numtests": str(total),
              "id": "AndroidJUnitRunner", "stream": ""}
    if stack is not None:
        fields["stack"] = stack
    fields.update(extras)
    return "\r\n\r\n".join("INSTRUMENTATION_STATUS: " + key + "=" + value for key, value in fields.items()) + "\r\n\r\nINSTRUMENTATION_STATUS_CODE: " + code + "\r\n\r\n"


def finish(total=4, code="-1"):
    return ("INSTRUMENTATION_RESULT: stream=\r\n\r\nTime: 1.234\r\n\r\nOK (" + str(total)
            + (" test" if total == 1 else " tests") + ")\r\n\r\nINSTRUMENTATION_CODE: " + code + "\r\n\r\n")


def run(cases=CASES, outcomes=None, ending=True):
    outcomes = outcomes or ["0"] * len(cases)
    data = ""
    for index, (case, code) in enumerate(zip(cases, outcomes), 1):
        data += record(case, index, len(cases)) + record(case, index, len(cases), code)
    if ending:
        data += finish(len(cases))
    return data.encode()


class InstrumentationParserTests(unittest.TestCase):
    def parse(self, data, expected=CASES, **kwargs):
        return analyse_instrumentation(data, expected, **kwargs)

    def test_exact_four_case_pass_and_fixed_public_shape(self):
        report = self.parse(run(), required_first=CASES[0], required_last=CASES[-1])
        self.assertEqual(set(report), {"status", "passed", "failed", "skipped", "completed",
            "started_unfinished", "graphics_watchdog_signature", "order_verified", "final_success"})
        self.assertEqual(report["status"], "passed")
        self.assertEqual(report["passed"], 4)
        self.assertEqual(report["completed"], [{"case": case, "outcome": "passed"} for case in CASES])
        self.assertTrue(report["order_verified"] and report["final_success"])

    def test_single_case_and_lf_supported(self):
        report = self.parse(run(CASES[:1]).replace(b"\r\n", b"\n"), CASES[:1])
        self.assertEqual(report["status"], "passed")

    def test_missing_terminal_keeps_started_case_and_previous_pass(self):
        data = record(CASES[0]) + record(CASES[0], code="0") + record(CASES[1], 2)
        report = self.parse(data.encode())
        self.assertEqual(report["status"], "incomplete")
        self.assertEqual((report["passed"], report["started_unfinished"]), (1, 1))
        self.assertFalse(report["final_success"])

    def test_explicit_crash_preserves_valid_partial_counts(self):
        data = record(CASES[0]) + record(CASES[0], code="0") + record(CASES[1], 2)
        data += "INSTRUMENTATION_RESULT: shortMsg=Process crashed: " + CANARY + "\nINSTRUMENTATION_CODE: 0\n"
        report = self.parse(data.encode())
        self.assertEqual(report["status"], "aborted")
        self.assertEqual((report["passed"], report["started_unfinished"]), (1, 1))
        self.assertNotIn(CANARY, json.dumps(report))

    def test_watchdog_only_validated_stack_classifies(self):
        data = record(CASES[0]) + record(CASES[0], code="-2", stack=SIGNATURE + "\n" + CANARY)
        data += "INSTRUMENTATION_RESULT: shortMsg=Process crashed.\nINSTRUMENTATION_CODE: 0\n"
        report = self.parse(data.encode())
        self.assertEqual(report["status"], "aborted")
        self.assertEqual(report["failed"], 1)
        self.assertTrue(report["graphics_watchdog_signature"])
        self.assertNotIn(CANARY, json.dumps(report))
        self.assertNotIn("TimeoutException", json.dumps(report))
        for fragment in (SIGNATURE, SIGNATURE.replace("TimeoutException", "other")):
            data = record(CASES[0], stream=fragment) + record(CASES[0], code="0")
            self.assertFalse(self.parse(data.encode())["graphics_watchdog_signature"])

    def test_watchdog_in_truncated_or_unknown_case_stack_does_not_classify(self):
        for data in (record("private.Unknown#case") + record("private.Unknown#case", code="-2", stack=SIGNATURE),
                     record(CASES[0]) + "INSTRUMENTATION_STATUS: stack=" + SIGNATURE):
            self.assertFalse(self.parse(data.encode())["graphics_watchdog_signature"])

    def test_missing_signature_component_does_not_classify(self):
        for fragment in ("ReferenceQueueDaemon", "TimeoutException", "HardwareRenderer$DestroyContextRunnable"):
            data = record(CASES[0]) + record(CASES[0], code="-2", stack=SIGNATURE.replace(fragment, "other"))
            self.assertFalse(self.parse(data.encode())["graphics_watchdog_signature"])

    def test_skips_assumptions_errors_and_failures_cannot_pass_forged_ok(self):
        for code, field in (("-1", "failed"), ("-2", "failed"), ("-3", "skipped"), ("-4", "skipped")):
            with self.subTest(code=code):
                report = self.parse(run(outcomes=["0", code, "0", "0"]))
                self.assertEqual(report["status"], "failed")
                self.assertEqual(report[field], 1)
                self.assertEqual(report["passed"], 3)
                self.assertFalse(report["final_success"])

    def test_ascending_current_required_for_each_pair(self):
        data = record(CASES[0], 2) + record(CASES[0], 2, code="0") + finish()
        self.assertEqual(self.parse(data.encode())["status"], "invalid")
        data = record(CASES[0]) + record(CASES[0], 2, code="0")
        self.assertEqual(self.parse(data.encode())["status"], "invalid")

    def test_class_identity_and_count_must_match_start_and_end(self):
        for terminal in (record(CASES[1], code="0"), record(CASES[0], total=5, code="0"),
                         record(CASES[0], code="0", id="other")):
            report = self.parse((record(CASES[0]) + terminal).encode())
            self.assertEqual(report["status"], "invalid")
            self.assertEqual(report["passed"], 0)
            self.assertEqual(report["started_unfinished"], 1)

    def test_duplicate_test_or_terminal_rejected_with_previous_count_retained(self):
        data = record(CASES[0]) + record(CASES[0], code="0")
        for extra in (record(CASES[0], 2) + record(CASES[0], 2, code="0"), record(CASES[0], code="0")):
            report = self.parse((data + extra).encode())
            self.assertEqual(report["status"], "invalid")
            self.assertEqual(report["passed"], 1)

    def test_unknown_test_is_never_copied(self):
        report = self.parse((record("private." + CANARY + "#unexpected") + finish()).encode())
        self.assertEqual(report["status"], "invalid")
        self.assertNotIn(CANARY, json.dumps(report))

    def test_required_endpoints_are_actual_observed_order(self):
        reordered = (CASES[1], CASES[0], CASES[2], CASES[3])
        self.assertEqual(self.parse(run(reordered))["status"], "passed")
        report = self.parse(run(reordered), required_first=CASES[0], required_last=CASES[-1])
        self.assertEqual(report["status"], "failed")
        self.assertFalse(report["order_verified"])
        report = self.parse(run(), required_last=CASES[0])
        self.assertEqual(report["status"], "failed")

    def test_forged_ok_without_all_case_pairs_cannot_pass(self):
        for data in (finish().encode(), run(CASES[:1]) + finish().encode(),
                     (record(CASES[0]) + finish()).encode()):
            report = self.parse(data)
            self.assertNotEqual(report["status"], "passed")
            self.assertFalse(report["final_success"])

    def test_final_code_required_and_duplicate_rejected(self):
        self.assertEqual(self.parse(run(ending=False))["status"], "incomplete")
        self.assertEqual(self.parse(run() + b"INSTRUMENTATION_CODE: -1\n")["status"], "invalid")
        self.assertEqual(self.parse(run().replace(b"INSTRUMENTATION_CODE: -1", b"INSTRUMENTATION_CODE: 0"))["status"], "aborted")

    def test_malformed_and_unknown_metadata_fail_closed(self):
        base = run()
        for data in (base.replace(b"current=1", b"current=01"),
                     base.replace(b"numtests=4", b"numtests=true"),
                     base.replace(b"class=", b"unexpected="),
                     base.replace(b"id=AndroidJUnitRunner", b"id=AndroidJUnitRunner\nid=duplicate", 1),
                     base.replace(b"INSTRUMENTATION_STATUS_CODE: 0", b"INSTRUMENTATION_STATUS_CODE: true", 1),
                     base.replace(b"INSTRUMENTATION_RESULT: stream=", b"INSTRUMENTATION_RESULT: privateKey="),
                     base + b"INSTRUMENTATION_UNKNOWN: " + CANARY.encode(), base + b"\x00"):
            report = self.parse(data)
            self.assertEqual(report["status"], "invalid")
            self.assertFalse(report["final_success"])
            self.assertNotIn(CANARY, json.dumps(report))

    def test_stacks_are_not_success_even_with_zero_terminal(self):
        data = record(CASES[0]) + record(CASES[0], code="0", stack=CANARY)
        self.assertEqual(self.parse(data.encode())["status"], "invalid")

    def test_two_starts_or_terminal_without_start_rejected(self):
        for data in (record(CASES[0]) + record(CASES[1]), record(CASES[0], code="0")):
            self.assertEqual(self.parse(data.encode())["status"], "invalid")

    def test_size_encoding_wrong_types_and_invalid_configuration(self):
        values = [b"x" * (MAX_BYTES + 1), b"\xff", "text", bytearray(run()), None, True]
        for data in values:
            self.assertEqual(self.parse(data)["status"], "invalid")
        for expected in ([], (), list(CASES), (True,), (CASES[0], CASES[0]), ("bad\n#id",)):
            self.assertEqual(self.parse(run(), expected)["status"], "invalid")
        for kwargs in ({"required_first": True}, {"required_last": "unknown#case"}):
            self.assertEqual(self.parse(run(), **kwargs)["status"], "invalid")

    def test_failure_stream_and_exception_canary_do_not_escape(self):
        data = record(CASES[0], stream=CANARY) + record(CASES[0], code="-2", stack=CANARY)
        data += "INSTRUMENTATION_RESULT: stream=" + CANARY + "\nINSTRUMENTATION_CODE: -1\n"
        report = self.parse(data.encode())
        self.assertEqual(report["status"], "failed")
        self.assertNotIn(CANARY, json.dumps(report))

    def test_result_stack_watchdog_aborts_without_copying(self):
        data = record(CASES[0]) + "INSTRUMENTATION_RESULT: stack=" + SIGNATURE + "\n" + CANARY + "\nINSTRUMENTATION_CODE: 0\n"
        report = self.parse(data.encode())
        self.assertEqual(report["status"], "aborted")
        self.assertTrue(report["graphics_watchdog_signature"])
        self.assertNotIn(CANARY, json.dumps(report))


if __name__ == "__main__":
    unittest.main()
