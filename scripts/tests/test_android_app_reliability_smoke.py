"""Synthetic runner policy checks. Never opens ADB or any installed APK."""
import contextlib
import io
import json
from pathlib import Path
import shlex
import sys
import tempfile
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import android_app_reliability_smoke as probe
from runtime_spike import ProcessResult

CANARY = "PRIVATE-story-token-path-PID-31415"


def junit(cases, failed=None, reverse=False):
    cases = list(cases)
    if reverse:
        cases.reverse()
    lines = []
    for index, case in enumerate(cases, 1):
        cls, method = case.split("#")
        for code in (1, -2 if case == failed else 0):
            lines += ["INSTRUMENTATION_STATUS: class=" + cls,
                      "INSTRUMENTATION_STATUS: test=" + method,
                      "INSTRUMENTATION_STATUS: current=" + str(index),
                      "INSTRUMENTATION_STATUS: numtests=" + str(len(cases)),
                      "INSTRUMENTATION_STATUS: id=AndroidJUnitRunner",
                      "INSTRUMENTATION_STATUS: stream="]
            if code == -2:
                lines += ["INSTRUMENTATION_STATUS: stack=java.util.concurrent.TimeoutException: ReferenceQueueDaemon timed out while targeting android.graphics.HardwareRenderer$DestroyContextRunnable@abc",
                          "\tat " + CANARY]
            lines.append("INSTRUMENTATION_STATUS_CODE: " + str(code))
    lines += ["INSTRUMENTATION_RESULT: stream=", "Time: 0.123",
              "FAILURES!!!" if failed else "OK (" + str(len(cases)) + " test" + ("s" if len(cases) != 1 else "") + ")",
              "INSTRUMENTATION_CODE: -1"]
    return ("\r\n\r\n".join(lines) + "\r\n").encode()


class Process:
    def __init__(self, hashes):
        self.hashes = hashes
        self.calls = []
        self.intercept = None

    def __call__(self, command, **budgets):
        self.calls.append((command, budgets))
        args = command[3:]
        if self.intercept:
            result = self.intercept(args)
            if result is not None:
                return result
        if args[:3] == ["shell", "pm", "path"]:
            output = ("package:/data/app/~~scope/" + args[3] + "/base.apk\n").encode()
        elif args[0] == "shell" and args[1].startswith("sha256sum "):
            path = shlex.split(args[1])[1]
            output = (self.hashes[path.split("/")[-2]] + "  " + path + "\n").encode()
        elif args[:3] == ["shell", "am", "instrument"]:
            cohort = next(value for value in probe.COHORTS.values() if value[0] == args[7])
            output = junit(cohort[1])
        elif args[:3] == ["shell", "am", "force-stop"]:
            output = b""
        elif args[0] == "shell" and args[1].startswith("pidof "):
            output = b"absent"
        else:
            raise AssertionError("Unexpected command")
        return ProcessResult("completed", 1, output, 0, 0, True)


class RunnerTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.app, self.test = [Path(self.tmp.name) / name for name in ("app.apk", "tests.apk")]
        self.app.write_bytes(b"source app")
        self.test.write_bytes(b"source tests")
        self.process = Process({probe.APP: probe.apk_digest(self.app), probe.TEST_APP: probe.apk_digest(self.test)})
        self.transport = probe.Transport("adb", "explicit-test-target", self.process)
        self.records = []

    def execute(self, repetitions=2, cohorts=None, emit=None):
        return probe.execute(self.transport, self.app, self.test, repetitions,
                             tuple(probe.COHORTS) if cohorts is None else cohorts,
                             self.records.append if emit is None else emit)

    def phases(self):
        return [args for args, _ in self.process.calls if "instrument" in args]

    def test_predetermined_matrix_retains_every_ordered_attempt_and_verifies_cleanup(self):
        result = self.execute()
        self.assertEqual(result["status"], "passed")
        self.assertEqual(result["attempts_finished"], 6)
        self.assertEqual(result["case_passes"], 18)
        self.assertEqual(result["cohorts_passed"], 6)
        self.assertFalse(result["cause_fixed"])
        self.assertEqual([row["event"] for row in self.records],
                         ["plan"] + [event for _ in range(6) for event in ("attempt_started", "attempt_finished")] + ["complete"])
        expected = list(probe.COHORTS) * 2
        self.assertEqual([row["cohort"] for row in self.records if row["event"] == "attempt_started"], expected)
        for row in self.records:
            if row["event"] == "attempt_finished":
                self.assertTrue(row["app_absent_before"] and row["app_absent_after"] and row["adb_clients_cleaned"])
                self.assertTrue(row["result"]["order_verified"])
        for command, budgets in self.process.calls:
            self.assertEqual(command[1:3], ["-s", "explicit-test-target"])
            self.assertLessEqual(budgets["deadline"], 180)
            self.assertLessEqual(budgets["max_output"], 131_072)
            self.assertNotIn("install", command)
            self.assertNotIn("clear", command)
        self.assertTrue(result["app_process_absent"] and result["adb_clients_cleaned"])

    def test_device_operations_cannot_precede_durable_start_record(self):
        def emit(row):
            if row["event"] == "attempt_started":
                self.assertEqual(self.process.calls, [])
            self.records.append(row)
        self.execute(repetitions=1, cohorts=("cancel_only",), emit=emit)

    def test_one_failed_run_is_retained_and_later_passes_do_not_rescue_summary(self):
        failed = False
        def intercept(args):
            nonlocal failed
            if "instrument" in args and not failed:
                failed = True
                cases = next(v[1] for v in probe.COHORTS.values() if v[0] == args[7])
                return ProcessResult("completed", 1, junit(cases, failed=probe.CANCEL), 0, 0, True)
        self.process.intercept = intercept
        result = self.execute()
        self.assertEqual(result["status"], "failed")
        self.assertEqual(result["attempts_finished"], 6)
        self.assertEqual(result["cohorts_passed"], 5)
        self.assertEqual(result["graphics_signature_attempts"], 1)
        self.assertNotIn(CANARY, json.dumps(self.records))

    def test_wrong_observed_order_is_a_failed_cohort_despite_all_individual_passes(self):
        self.process.intercept = lambda args: ProcessResult("completed", 1, junit(probe.COHORTS["framework_then_cancel"][1], reverse=True), 0, 0, True) if "instrument" in args else None
        result = self.execute(1, ("framework_then_cancel",))
        self.assertEqual(result["case_passes"], 4)
        self.assertEqual(result["cohorts_passed"], 0)
        self.assertEqual(result["status"], "failed")

    def test_unknown_client_ownership_stops_all_future_clients_and_absence_claim(self):
        self.process.intercept = lambda args: ProcessResult("timeout", 180000, junit((probe.CANCEL,)), 0, 0, False) if "instrument" in args else None
        result = self.execute()
        self.assertEqual(result["attempts_started"], 1)
        self.assertEqual(result["unexecuted"], 5)
        self.assertFalse(result["adb_clients_cleaned"] or result["app_process_absent"])
        self.assertIn("instrument", self.process.calls[-1][0])

    def test_cancelled_host_client_stops_predetermined_plan_after_guarded_cleanup(self):
        self.process.intercept = lambda args: ProcessResult("cancelled", 1, b"", 0, 1, True) if "instrument" in args else None
        result = self.execute()
        self.assertEqual(result["attempts_started"], 1)
        self.assertTrue(result["app_process_absent"])
        self.assertEqual(result["status"], "failed")

    def test_timeout_with_partial_records_is_retained_and_next_attempt_requires_absence(self):
        timed_out = False
        def intercept(args):
            nonlocal timed_out
            if "instrument" in args and not timed_out:
                timed_out = True
                return ProcessResult("timeout", 180000, junit((probe.CANCEL,)), 0, 1, True)
        self.process.intercept = intercept
        result = self.execute()
        self.assertEqual(result["attempts_finished"], 6)
        self.assertEqual(result["cohorts_passed"], 5)
        self.assertEqual(result["status"], "failed")

    def test_nonzero_boolean_and_missing_returncodes_never_count_as_transport_pass(self):
        for code in (1, False, True, None):
            with self.subTest(code=code):
                process = Process(self.process.hashes)
                process.intercept = lambda args, code=code: ProcessResult("completed", 1, junit((probe.CANCEL,)), 0, code, True) if "instrument" in args else None
                records = []
                result = probe.execute(probe.Transport("adb", "target", process), self.app, self.test, 1, ("cancel_only",), records.append)
                self.assertEqual(result["cohorts_passed"], 0)

    def test_identity_mismatch_prevents_instrumentation_and_other_attempts(self):
        self.process.hashes[probe.APP] = "0" * 64
        result = self.execute()
        self.assertEqual(self.phases(), [])
        self.assertEqual(result["attempts_started"], 1)
        self.assertFalse(result["app_process_absent"])

    def test_local_app_replacement_after_phase_prevents_stop_of_replacement(self):
        def intercept(args):
            if "instrument" in args:
                self.app.write_bytes(b"replacement")
        self.process.intercept = intercept
        result = self.execute()
        self.assertEqual(len(self.phases()), 1)
        self.assertFalse(result["app_process_absent"])
        stops = [command for command, _ in self.process.calls if "force-stop" in command]
        self.assertEqual(len(stops), 1)  # Initial stop only; changed local identity fails closed.

    def test_failed_final_stop_revokes_success_and_does_not_start_another_attempt(self):
        stops = 0
        def intercept(args):
            nonlocal stops
            if "force-stop" in args:
                stops += 1
                if stops == 2:
                    return ProcessResult("completed", 1, CANARY.encode(), 0, 1, True)
        self.process.intercept = intercept
        result = self.execute()
        self.assertEqual(result["status"], "failed")
        self.assertEqual(result["attempts_started"], 1)
        self.assertFalse(result["app_process_absent"])
        self.assertNotIn(CANARY, json.dumps(self.records))

    def test_missing_local_apk_never_operates_transport(self):
        self.test.unlink()
        result = self.execute()
        self.assertEqual(self.process.calls, [])
        self.assertEqual(result["failure_stage"], "local_apk")

    def test_invalid_programmatic_plans_never_operate_transport(self):
        for repetitions, cohorts in ((False, ("cancel_only",)), (0, ("cancel_only",)), (3, ("cancel_only",)),
                                     (1, ()), (1, ("private",)), (1, ("cancel_only", "cancel_only"))):
            with self.assertRaises(ValueError):
                self.execute(repetitions, cohorts)
        self.assertEqual(self.process.calls, [])

    def test_journal_failure_before_first_start_performs_no_device_action(self):
        def emit(row):
            if row["event"] == "attempt_started":
                raise OSError(CANARY)
        with self.assertRaises(OSError):
            self.execute(emit=emit)
        self.assertEqual(self.process.calls, [])

    def test_finish_journal_failure_stops_after_cleanup_with_start_retained(self):
        def emit(row):
            if row["event"] == "attempt_finished":
                raise OSError(CANARY)
            self.records.append(row)
        with self.assertRaises(OSError):
            self.execute(emit=emit)
        self.assertEqual(len(self.phases()), 1)
        self.assertEqual(self.records[-1]["event"], "attempt_started")
        self.assertTrue(self.process.calls[-1][0][-1].startswith("pidof "))

    def test_failed_spawn_ownership_prevents_further_device_calls_and_private_error_echo(self):
        def intercept(args):
            if "instrument" in args:
                raise OSError(CANARY)
        self.process.intercept = intercept
        result = self.execute()
        self.assertFalse(result["adb_clients_cleaned"])
        self.assertIn("instrument", self.process.calls[-1][0])
        self.assertNotIn(CANARY, json.dumps(self.records))

    def test_private_unframed_output_is_rejected_without_echo(self):
        self.process.intercept = lambda args: ProcessResult("completed", 1, CANARY.encode(), 0, 0, True) if "instrument" in args else None
        result = self.execute(1, ("cancel_only",))
        self.assertEqual(result["status"], "failed")
        encoded = json.dumps(self.records)
        for private in (CANARY, str(self.app), "explicit-test-target"):
            self.assertNotIn(private, encoded)

    def test_exclusive_durable_journal_refuses_overwriting_existing_evidence(self):
        output = Path(self.tmp.name) / "journal.jsonl"
        journal = probe.Journal(output)
        journal.append({"event": "attempt_started", "index": 1})
        journal.close()
        before = output.read_bytes()
        with self.assertRaises(FileExistsError):
            probe.Journal(output)
        self.assertEqual(before, output.read_bytes())
        self.assertEqual(json.loads(before), {"event": "attempt_started", "index": 1})

    def test_cli_existing_output_and_private_argument_error_do_not_construct_transport(self):
        output = Path(self.tmp.name) / "existing.jsonl"
        output.write_text("earlier evidence")
        args = ["--adb", "adb", "--serial", "target", "--apk", str(self.app), "--test-apk", str(self.test), "--output", str(output)]
        with patch.object(probe, "Transport") as transport, contextlib.redirect_stdout(io.StringIO()) as printed:
            self.assertEqual(probe.main(args), 2)
            transport.assert_not_called()
        self.assertEqual(output.read_text(), "earlier evidence")
        with patch.object(probe, "Transport") as transport, contextlib.redirect_stdout(io.StringIO()) as printed:
            self.assertEqual(probe.main(args + ["--cohort", CANARY]), 2)
            transport.assert_not_called()
        self.assertNotIn(CANARY, printed.getvalue())


if __name__ == "__main__":
    unittest.main()
