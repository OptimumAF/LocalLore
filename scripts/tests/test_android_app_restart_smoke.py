"""Synthetic-only adversarial tests: importing this module never operates ADB."""
import hashlib
import json
import shlex
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import android_app_restart_smoke as probe
from runtime_spike import ProcessResult

CANARY = "private-story-PID-1234-path-token"


def junit(method=probe.METHODS[0], start="1", end="0", final="-1", count="1", extra=""):
    def record(status):
        return "\r\n\r\n".join([
            "INSTRUMENTATION_STATUS: class=" + probe.CLASS,
            "INSTRUMENTATION_STATUS: current=1",
            "INSTRUMENTATION_STATUS: id=AndroidJUnitRunner",
            "INSTRUMENTATION_STATUS: numtests=" + count,
            "INSTRUMENTATION_STATUS: stream=",
            "INSTRUMENTATION_STATUS: test=" + method,
            "INSTRUMENTATION_STATUS_CODE: " + status]) + "\r\n\r\n"
    return (record(start) + record(end) + extra +
            "INSTRUMENTATION_RESULT: stream=\r\n\r\nTime: 0.125\r\n\r\nOK (1 test)\r\n\r\n"
            "INSTRUMENTATION_CODE: " + final + "\r\n\r\n").encode()


class ScriptedProcess:
    def __init__(self, hashes):
        self.hashes = hashes
        self.calls = []
        self.intercept = None

    def __call__(self, command, **kwargs):
        self.calls.append((command, kwargs))
        args = command[3:]
        if self.intercept:
            value = self.intercept(args)
            if value is not None:
                return value
        if args[:3] == ["shell", "pm", "path"]:
            output = ("package:/data/app/~~scope/" + args[3] + "/base.apk\n").encode()
        elif args[0] == "shell" and args[1].startswith("sha256sum "):
            path = shlex.split(args[1])[1]
            package = path.split("/")[-2]
            output = (self.hashes[package] + "  " + path + "\n").encode()
        elif args[:3] == ["shell", "am", "instrument"]:
            output = junit(args[7].split("#", 1)[1])
        elif args[:3] == ["shell", "am", "force-stop"]:
            output = b""
        elif args[0] == "shell" and args[1].startswith("pidof "):
            output = b"absent"
        else:
            raise AssertionError("Unexpected command")
        return ProcessResult("completed", 1, output, 0, 0, True)


class ParserTests(unittest.TestCase):
    def test_one_actual_pass_crlf(self):
        self.assertTrue(probe.passed_instrumentation(junit(), probe.METHODS[0]))

    def test_no_record_is_not_success(self):
        self.assertFalse(probe.passed_instrumentation(b"OK (1 test)\n", probe.METHODS[0]))

    def test_duplicate_status_and_runs_rejected(self):
        for output in (junit() + junit(), junit().replace(
                b"INSTRUMENTATION_STATUS: current=1", b"INSTRUMENTATION_STATUS: current=1\nINSTRUMENTATION_STATUS: current=1", 1)):
            self.assertFalse(probe.passed_instrumentation(output, probe.METHODS[0]))

    def test_skips_failures_and_assumption_failures_rejected(self):
        for code in ("-1", "-2", "-3", "-4", "2", "true"):
            self.assertFalse(probe.passed_instrumentation(junit(end=code), probe.METHODS[0]))

    def test_wrong_test_class_and_count_rejected(self):
        for output in (junit(method="other"), junit(count="2"),
                       junit().replace(probe.CLASS.encode(), b"other.Test")):
            self.assertFalse(probe.passed_instrumentation(output, probe.METHODS[0]))

    def test_crash_missing_final_and_malformed_rejected(self):
        for output in (junit(final="0"), junit().replace(b"INSTRUMENTATION_CODE: -1", b""),
                       junit(extra="INSTRUMENTATION_FAILED: crashed\n"),
                       junit().replace(b"current=1", b"current"), b"\xff"):
            self.assertFalse(probe.passed_instrumentation(output, probe.METHODS[0]))

    def test_duplicate_result_and_false_ok_rejected(self):
        for output in (junit().replace(b"INSTRUMENTATION_CODE:", b"INSTRUMENTATION_RESULT: stream=OK (1 test)\nINSTRUMENTATION_CODE:"),
                       junit().replace(b"OK (1 test)", b"FAILURES!!! OK (1 test)")):
            self.assertFalse(probe.passed_instrumentation(output, probe.METHODS[0]))


class RunnerTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.apk, self.tests = [Path(self.tmp.name) / name for name in ("app.apk", "tests.apk")]
        self.apk.write_bytes(b"source-built-app")
        self.tests.write_bytes(b"source-built-tests")
        hashes = {probe.APP: probe.apk_digest(self.apk), probe.TEST_APP: probe.apk_digest(self.tests)}
        self.process = ScriptedProcess(hashes)
        self.transport = probe.Transport(Path("adb"), "emulator-test", self.process)

    def execute(self):
        return probe.execute(self.transport, self.apk, self.tests)

    def test_success_requires_ordered_two_phases_and_two_identity_guarded_stops(self):
        report = self.execute()
        self.assertEqual(report["status"], "passed")
        self.assertEqual([row["phase"] for row in report["attempts"]], ["checkpoint", "process_stop", "resume"])
        commands = [args[3:] for args, _ in self.process.calls]
        phases = [args for args in commands if args[:3] == ["shell", "am", "instrument"]]
        self.assertEqual([args[7] for args in phases], [probe.CLASS + "#" + method for method in probe.METHODS])
        self.assertEqual(phases[0][10], phases[1][10])
        self.assertRegex(phases[0][10], r"^[0-9a-f]{32}$")
        stops = [index for index, args in enumerate(commands) if args[:3] == ["shell", "am", "force-stop"]]
        self.assertEqual(len(stops), 2)
        for index in stops:
            self.assertTrue(commands[index - 1][1].startswith("sha256sum "))
            self.assertTrue(commands[index + 1][1].startswith("pidof " + probe.APP))
        self.assertTrue(report["adb_clients_cleaned"] and report["app_process_absent"])
        for _, kwargs in self.process.calls:
            self.assertLessEqual(kwargs["deadline"], 180)
            self.assertLessEqual(kwargs["max_output"], 131_072)

    def test_mismatched_app_hash_prevents_launch_or_stop(self):
        self.process.hashes[probe.APP] = "0" * 64
        report = self.execute()
        self.assertEqual(report["failure_stage"], "app_identity")
        self.assertEqual(report["final_cleanup_stage"], "final_identity")
        self.assertFalse(report["app_process_absent"])
        self.assertFalse(any(call[0][4:6] in (["am", "instrument"], ["am", "force-stop"]) for call in self.process.calls))

    def test_mismatched_test_apk_prevents_instrumentation(self):
        self.process.hashes[probe.TEST_APP] = "0" * 64
        report = self.execute()
        self.assertEqual(report["failure_stage"], "test_identity")
        self.assertFalse(any("instrument" in call[0] for call in self.process.calls))
        self.assertTrue(report["app_process_absent"])

    def test_split_or_malformed_package_path_fails_closed(self):
        self.process.intercept = lambda args: ProcessResult("completed", 1, b"package:/data/app/base.apk\npackage:/data/app/split.apk\n", 0, 0, True) if args[:3] == ["shell", "pm", "path"] else None
        self.assertEqual(self.execute()["failure_stage"], "app_identity")

    def test_failed_first_phase_retained_no_second_phase(self):
        self.process.intercept = lambda args: ProcessResult("completed", 1, junit(end="-2"), 0, 0, True) if "instrument" in args else None
        report = self.execute()
        self.assertEqual(report["attempts"], [{"phase": "checkpoint", "passed": False, "failure_stage": "checkpoint", "adb_clients_cleaned": True}])
        self.assertTrue(report["app_process_absent"])

    def test_unknown_launcher_cleanup_prevents_next_client_and_absence_claim(self):
        self.process.intercept = lambda args: ProcessResult("timeout", 180000, junit(), 0, 0, False) if "instrument" in args else None
        report = self.execute()
        self.assertFalse(report["adb_clients_cleaned"])
        self.assertFalse(report["app_process_absent"])
        self.assertEqual(report["failure_stage"], "checkpoint")
        self.assertEqual(report["final_cleanup_stage"], "final_identity")
        self.assertIn("instrument", self.process.calls[-1][0])

    def test_nonzero_boolean_returncode_does_not_count_as_completed(self):
        for code in (1, False, True, None):
            with self.subTest(code=code):
                process = ScriptedProcess(self.process.hashes)
                process.intercept = lambda args, code=code: ProcessResult("completed", 1, junit(), 0, code, True) if "instrument" in args else None
                report = probe.execute(probe.Transport("adb", "test", process), self.apk, self.tests)
                self.assertEqual(report["failure_stage"], "checkpoint")

    def test_stop_failure_prevents_resume_and_retains_failed_attempt(self):
        self.process.intercept = lambda args: ProcessResult("completed", 1, CANARY.encode(), 0, 1, True) if "force-stop" in args else None
        report = self.execute()
        self.assertEqual(report["failure_stage"], "stop_command")
        self.assertEqual([row["phase"] for row in report["attempts"]], ["checkpoint", "process_stop"])
        self.assertEqual(report["final_cleanup_stage"], "final_stop")
        self.assertNotIn(CANARY, json.dumps(report))

    def test_probe_error_running_and_unknown_never_mean_absence(self):
        for data, code in ((b"running", 0), (b"absent", 1), (b"", 0), (b"absent\n", 0), (CANARY.encode(), 0)):
            process = ScriptedProcess(self.process.hashes)
            process.intercept = lambda args, data=data, code=code: ProcessResult("completed", 1, data, 0, code, True) if args[1].startswith("pidof ") else None
            report = probe.execute(probe.Transport("adb", "test", process), self.apk, self.tests)
            self.assertEqual(report["failure_stage"], "stop_absence")
            self.assertFalse(report["app_process_absent"])
            self.assertNotIn(CANARY, json.dumps(report))

    def test_final_cleanup_failure_revokes_pass_but_preserves_successful_phases(self):
        probes = 0
        def intercept(args):
            nonlocal probes
            if args[1].startswith("pidof "):
                probes += 1
                if probes == 2:
                    return ProcessResult("completed", 1, b"running", 0, 0, True)
        self.process.intercept = intercept
        report = self.execute()
        self.assertEqual(report["status"], "failed")
        self.assertTrue(all(row["passed"] for row in report["attempts"]))
        self.assertEqual(report["final_cleanup_stage"], "final_absence")

    def test_exception_and_output_never_leak_token_pid_path_or_story(self):
        def intercept(args):
            if "instrument" in args:
                raise OSError(CANARY + " " + args[10])
        self.process.intercept = intercept
        report = self.execute()
        encoded = json.dumps(report)
        self.assertNotIn(CANARY, encoded)
        self.assertNotIn(str(self.apk), encoded)
        token = next(args[13] for args, _ in self.process.calls if "instrument" in args)
        self.assertNotIn(token, encoded)
        self.assertFalse(report["adb_clients_cleaned"])

    def test_local_replacement_after_checkpoint_blocks_stop_before_another_phase(self):
        def intercept(args):
            if "instrument" in args:
                self.apk.write_bytes(b"replacement")
        self.process.intercept = intercept
        report = self.execute()
        self.assertEqual(report["failure_stage"], "local_apk")
        self.assertEqual(report["final_cleanup_stage"], "final_identity")
        self.assertEqual(len(report["attempts"]), 2)

    def test_missing_local_apk_uses_no_transport(self):
        self.apk.unlink()
        report = self.execute()
        self.assertEqual(report["failure_stage"], "local_apk")
        self.assertEqual(self.process.calls, [])


if __name__ == "__main__":
    unittest.main()
