"""Original interruption-owner faults; these tests never launch ADB or an application."""
import importlib.util
import json
from pathlib import Path
import sys
import tempfile
import threading
from concurrent.futures import ThreadPoolExecutor
from types import SimpleNamespace
import unittest
from unittest.mock import patch

SCRIPTS = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(SCRIPTS))
SPEC = importlib.util.spec_from_file_location("archive_recovery", SCRIPTS / "archive_recovery.py")
proof = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = proof
SPEC.loader.exec_module(proof)


def record(run="fixed-run", phase="arm-preview", pid=1234, **change):
    value = dict(version=1, run=run, phase=phase, pid=pid, archive_sha256=proof.common.digest(b"synthetic"), status="ready")
    value.update(change)
    return value


def wire(code=None):
    def block(status):
        return ("INSTRUMENTATION_STATUS: class=" + proof.TEST_CLASS + "\n"
                "INSTRUMENTATION_STATUS: test=" + proof.TEST_METHOD + "\n"
                "INSTRUMENTATION_STATUS: numtests=1\nINSTRUMENTATION_STATUS_CODE: " + status + "\n")
    return (block("1") + (block(code) if code is not None else "") +
            ("OK (1 test)\nINSTRUMENTATION_CODE: -1\n" if code == "0" else "")).encode()


def process(clean=True, data=b"", status="completed"):
    return SimpleNamespace(cleanup_complete=clean, status=status, stdout=data, stderr_bytes=0, returncode=0)


class MarkerAndTerminal(unittest.TestCase):
    def test_marker_requires_exact_scope_types_and_no_duplicate_keys(self):
        base = record()
        self.assertEqual(base, proof.parse_record(json.dumps(base).encode(), "fixed-run", "arm-preview", "ready"))
        cases = [dict(base, pid=True), dict(base, pid=0), dict(base, version=True), dict(base, version=2),
                 dict(base, run="other"), dict(base, phase="arm-committed"), dict(base, status="verified"),
                 dict(base, archive_sha256="A" * 64), dict(base, extra="unexpected")]
        for value in cases:
            with self.subTest(value=value), self.assertRaises(proof.Failure):
                proof.parse_record(json.dumps(value).encode(), "fixed-run", "arm-preview", "ready")
        duplicate = json.dumps(base)[:-1] + ',"pid":1234}'
        with self.assertRaisesRegex(proof.Failure, "marker_duplicate_key"):
            proof.parse_record(duplicate.encode(), "fixed-run", "arm-preview", "ready")

    def test_interrupted_arm_is_not_a_passing_or_failed_test(self):
        interrupted = proof.parse_transcript(wire(), interrupted=True)
        self.assertEqual(0, interrupted["passed"])
        self.assertEqual(1, interrupted["intentional_interruptions"])
        self.assertFalse(interrupted["test_terminal_received"])
        for data in (wire("0"), wire("-2"), b"INSTRUMENTATION_CODE: -1\n", wire() + wire()):
            with self.subTest(data=data[-40:]), self.assertRaises(proof.Failure):
                proof.parse_transcript(data, interrupted=True)

    def test_relaunch_requires_matching_complete_success_not_runner_exit(self):
        self.assertEqual(1, proof.parse_transcript(wire("0"))["passed"])
        for data in (wire(), wire("-2"), wire("0").replace(b"processRecovery", b"unrelated"),
                     wire("0") + b"shortMsg=Process crashed\n", wire("0").replace(b"OK (1 test)", b"FAILURES!!!")):
            with self.subTest(data=data[-40:]), self.assertRaises(proof.Failure):
                proof.parse_transcript(data)

    def test_remote_control_cannot_address_traversal_or_baseline_files(self):
        for run, name in (("../other", "ready-v1.json"), ("-e x", "archive.json"),
                          ("fixed-run", "baseline.json"), ("fixed-run", "../owner-v1")):
            with self.subTest(run=run, name=name), self.assertRaises(proof.Failure):
                proof.remote_path(run, name)


class LiveInterruption(unittest.TestCase):
    def setUp(self):
        self.device = SimpleNamespace(shell=lambda *args: b"")
        self.future = SimpleNamespace(done=lambda: False)
        self.identities = {proof.PACKAGE: "a" * 64, proof.TEST_PACKAGE: "b" * 64}

    def test_arm_ended_before_ready_never_reads_or_restarts(self):
        self.future.done = lambda: True
        with patch.object(proof, "remote_optional") as read:
            with self.assertRaisesRegex(proof.Failure, "arm_ended_before_interruption"):
                proof.await_ready(self.device, self.future, "fixed-run", "arm-preview")
        read.assert_not_called()

    def test_source_drift_and_stale_pid_cannot_authorize_interruption(self):
        ready = json.dumps(record()).encode()
        for source, pid, category in ((b"different", 1234, "source_hash"), (b"synthetic", 99, "live_pid_mismatch")):
            with self.subTest(category=category), patch.object(proof, "remote_optional", side_effect=[ready, proof.MARKER, source]), \
                 patch.object(proof, "package_pid", return_value=pid):
                with self.assertRaisesRegex(proof.Failure, category):
                    proof.await_ready(self.device, self.future, "fixed-run", "arm-preview")

    def test_partial_json_is_observed_again_before_any_process_action(self):
        with patch.object(proof, "remote_optional", side_effect=[b'{"version":', json.dumps(record()).encode(), proof.MARKER, b"synthetic"]), \
             patch.object(proof, "package_pid", return_value=1234), patch.object(proof.time, "sleep"):
            value, _ = proof.await_ready(self.device, self.future, "fixed-run", "arm-preview")
        self.assertEqual(1234, value["pid"])

    def test_package_identity_and_pid_are_rechecked_before_targeted_stop(self):
        for hashes, pid, category in ((["wrong"], 1234, "owned_package_changed"),
                                      (list(self.identities.values()), 99, "live_pid_mismatch")):
            with self.subTest(category=category), patch.object(proof.common, "installed_hash", side_effect=hashes), \
                 patch.object(proof, "package_pid", return_value=pid), patch.object(self.device, "shell") as shell:
                with self.assertRaisesRegex(proof.Failure, category):
                    proof.interrupt_live_arm(self.device, self.future, record(), self.identities, lambda *a, **k: None)
            shell.assert_not_called()

    def test_ended_arm_after_identity_observation_is_not_stopped_or_restarted(self):
        self.future.done = unittest.mock.Mock(side_effect=[False, True])
        with patch.object(proof.common, "installed_hash", side_effect=self.identities.values()), \
             patch.object(proof, "package_pid", return_value=1234), patch.object(self.device, "shell") as shell:
            with self.assertRaisesRegex(proof.Failure, "arm_ended_before_interruption"):
                proof.interrupt_live_arm(self.device, self.future, record(), self.identities, lambda *a, **k: None)
        shell.assert_not_called()

    def test_stop_acknowledgement_does_not_prove_actual_process_death(self):
        with patch.object(proof.common, "installed_hash", side_effect=self.identities.values()), \
             patch.object(proof, "package_pid", return_value=1234), patch.object(self.device, "shell") as shell:
            with self.assertRaisesRegex(proof.Failure, "target_process_survived"):
                proof.interrupt_live_arm(self.device, self.future, record(), self.identities, lambda *a, **k: None)
        shell.assert_called_once_with("am", "force-stop", proof.PACKAGE)


class ClientOwnership(unittest.TestCase):
    def test_unknown_cleanup_is_published_before_fallible_logging(self):
        def failed_log(*args, **kwargs):
            raise OSError("synthetic disk failure")
        device = proof.OwnedDevice("unused", "unused", failed_log)
        with patch.object(proof.common.android.Device, "raw", return_value=process(clean=False)) as raw:
            with self.assertRaises(OSError):
                device.raw(["first"])
            self.assertFalse(device.clients_cleaned)
            with self.assertRaisesRegex(proof.Failure, "client_cleanup_unknown"):
                device.raw(["must-not-run"])
        self.assertEqual(1, raw.call_count)

    def test_late_success_cannot_erase_concurrent_unknown_cleanup(self):
        live = threading.Event()
        release = threading.Event()
        device = proof.OwnedDevice("unused", "unused", lambda *a, **k: None)
        def call(args, *unused, **kwargs):
            if args == ["live"]:
                live.set()
                self.assertTrue(release.wait(2))
                return process()
            return process(clean=False)
        with patch.object(proof.common.android.Device, "raw", side_effect=call):
            with ThreadPoolExecutor(max_workers=1) as pool:
                pending = pool.submit(device.raw, ["live"])
                self.assertTrue(live.wait(2))
                device.raw(["failed"])
                release.set()
                pending.result(timeout=2)
        self.assertFalse(device.clients_cleaned)


class Pipeline(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.app, self.test, self.adb = [self.root / n for n in ("app.apk", "test.apk", "adb")]
        for path in (self.app, self.test, self.adb):
            path.write_bytes(path.name.encode())
        self.args = SimpleNamespace(alias="A", serial="not-a-device", app_apk=self.app, test_apk=self.test,
                                    adb=self.adb, output_directory=self.root / "proof")
        self.ids = {proof.PACKAGE: proof.common.digest(self.app.read_bytes()),
                    proof.TEST_PACKAGE: proof.common.digest(self.test.read_bytes())}

    def tools(self, command, **kwargs):
        package = proof.PACKAGE if command[-1] == str(self.app) else proof.TEST_PACKAGE
        return process(data=("package: name='" + package + "' versionCode='1'\n").encode())

    def test_artifact_mismatch_never_stops_or_arms_an_app(self):
        device = SimpleNamespace(clients_cleaned=True, shell=lambda *a: b"1")
        with patch.object(proof.common.process_owner, "run_process", side_effect=self.tools), \
             patch.object(proof, "OwnedDevice", return_value=device), \
             patch.object(proof.common, "protected_packages", return_value={}), \
             patch.object(proof.common, "stop_owned") as stop, patch.object(proof, "exercise_case") as arm:
            result = proof.run(self.args)
        self.assertEqual("installed_artifact_mismatch", result["failure"])
        stop.assert_not_called()
        arm.assert_not_called()

    def test_unknown_arm_cleanup_fences_relaunch_second_case_and_final_device_calls(self):
        calls = []
        device = SimpleNamespace(clients_cleaned=True, shell=lambda *a: b"1")
        def failed(*args):
            device.clients_cleaned = False
            raise proof.Failure("arm_client_cleanup_unknown")
        with patch.object(proof.common.process_owner, "run_process", side_effect=self.tools), \
             patch.object(proof, "OwnedDevice", return_value=device), \
             patch.object(proof.common, "protected_packages", side_effect=lambda *a: calls.append("inventory") or self.ids), \
             patch.object(proof.common, "stop_owned") as stop, patch.object(proof, "exercise_case", side_effect=failed) as arm:
            result = proof.run(self.args)
        self.assertEqual("failed", result["status"])
        self.assertFalse(result["adb_clients_cleaned"])
        self.assertEqual(["inventory"], calls)
        self.assertEqual(1, arm.call_count)
        self.assertEqual(1, stop.call_count)  # Initial verified drain only.

    def test_changed_protected_package_cannot_publish_success(self):
        device = SimpleNamespace(clients_cleaned=True, shell=lambda *a: b"1")
        with patch.object(proof.common.process_owner, "run_process", side_effect=self.tools), \
             patch.object(proof, "OwnedDevice", return_value=device), \
             patch.object(proof.common, "protected_packages", side_effect=[self.ids, dict(self.ids, other="changed")]), \
             patch.object(proof.common, "stop_owned"), patch.object(proof, "exercise_case", return_value={"status": "passed"}):
            result = proof.run(self.args)
        self.assertEqual(2, len(result["cases"]))
        self.assertFalse(result["prior_packages_preserved"])
        self.assertEqual("failed", result["status"])


if __name__ == "__main__":
    unittest.main()
