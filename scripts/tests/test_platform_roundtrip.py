"""Original orchestration faults; no compiler, model, ADB or app is launched."""
import importlib.util
import json
from pathlib import Path
import sys
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import patch
import zipfile

SPEC = importlib.util.spec_from_file_location("platform_roundtrip", Path(__file__).resolve().parents[1] / "platform_roundtrip.py")
proof = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = proof
SPEC.loader.exec_module(proof)


def transcript(terminal="0", summary="OK (1 test)"):
    def block(code):
        return ("INSTRUMENTATION_STATUS: class=" + proof.TEST_CLASS + "\n"
                "INSTRUMENTATION_STATUS: test=platformRoundTrip\n"
                "INSTRUMENTATION_STATUS: numtests=1\n"
                "INSTRUMENTATION_STATUS_CODE: " + code + "\n")
    return (block("1") + block(terminal) + summary + "\nINSTRUMENTATION_CODE: -1\n").encode()


class TempCase(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)


class Fixtures(TempCase):
    def test_existing_directory_and_file_are_not_adopted_or_overwritten(self):
        output = self.root / "existing"
        output.mkdir()
        sentinel = output / "sentinel"
        sentinel.write_bytes(b"keep")
        with self.assertRaises(FileExistsError):
            proof.fresh_directory(output)
        with self.assertRaises(FileExistsError):
            proof.write_new(sentinel, b"replace")
        self.assertEqual(b"keep", sentinel.read_bytes())

    def test_reparse_target_is_refused_before_reading(self):
        with patch.object(Path, "lstat", return_value=SimpleNamespace(st_mode=0o100600, st_file_attributes=0x400)):
            with self.assertRaisesRegex(proof.Failure, "linked_path"):
                proof.read_small(self.root / "foreign")

    def test_actual_fixture_size_is_bounded(self):
        file = self.root / "fixture"
        file.write_bytes(b"x" * proof.MAX_FIXTURE_BYTES)
        self.assertEqual(proof.MAX_FIXTURE_BYTES, len(proof.read_small(file)))
        file.write_bytes(b"x" * (proof.MAX_FIXTURE_BYTES + 1))
        with self.assertRaisesRegex(proof.Failure, "fixture_size"):
            proof.read_small(file)

    def test_remote_path_rejects_traversal_options_and_unknown_file_names(self):
        for run in ("../outside", "x/y", "-e hello", "x;touch", "", "UPPER", "x" * 49):
            with self.subTest(run=run), self.assertRaises(proof.Failure):
                proof.remote_path(run, "owner-v1")
        with self.assertRaisesRegex(proof.Failure, "invalid_remote_file"):
            proof.remote_path("fixed-run", "../owner-v1")

    def test_apk_fixture_drift_is_refused(self):
        fixture = self.root / "fixtures"
        fixture.mkdir()
        apk = self.root / "test.apk"
        with zipfile.ZipFile(apk, "w") as archive:
            for name in proof.ASSETS:
                (fixture / name).write_bytes(b"original")
                archive.writestr("assets/platform-roundtrip-v1/" + name,
                                 b"changed" if name == "windows-origin.json" else b"original")
        with self.assertRaisesRegex(proof.Failure, "fixture_drift"):
            proof.verify_packaged_fixtures(apk, fixture)


class Terminals(unittest.TestCase):
    def test_complete_matching_terminal_is_required(self):
        self.assertEqual(1, proof.parse_instrumentation(transcript())["passed"])
        for data in (b"INSTRUMENTATION_CODE: -1\n", transcript().split(b"INSTRUMENTATION_STATUS_CODE: 0")[0],
                     transcript() + transcript(), transcript().replace(b"platformRoundTrip", b"other"),
                     transcript().replace(b"numtests=1", b"numtests=2"),
                     transcript().replace(b"INSTRUMENTATION_CODE: -1", b"INSTRUMENTATION_CODE: 0")):
            with self.subTest(data=data[-80:]), self.assertRaises(proof.Failure):
                proof.parse_instrumentation(data)

    def test_failure_skip_and_conflicting_summary_never_pass(self):
        for terminal in ("-1", "-2", "-3", "-4"):
            with self.subTest(terminal=terminal), self.assertRaises(proof.Failure):
                proof.parse_instrumentation(transcript(terminal))
        for data in (transcript(summary="FAILURES!!!"), transcript() + b"shortMsg=Process crashed\n"):
            with self.assertRaises(proof.Failure):
                proof.parse_instrumentation(data)

    def test_unknown_client_cleanup_prevents_any_later_command(self):
        result = SimpleNamespace(cleanup_complete=False, status="cleanup_failed", returncode=None, stdout=b"")
        journal = lambda *args, **kwargs: None
        device = proof.OwnedDevice("unused", "unused", journal)
        with patch.object(proof.android.Device, "raw", return_value=result) as raw:
            device.raw(["first"])
            with self.assertRaisesRegex(proof.Failure, "client_cleanup_unknown"):
                device.raw(["must-not-run"])
        self.assertEqual(1, raw.call_count)


class Pipeline(TempCase):
    def args(self):
        fixture = self.root / "fixtures"
        fixture.mkdir()
        app, test = self.root / "app.apk", self.root / "test.apk"
        app.write_bytes(b"synthetic APK placeholder")
        with zipfile.ZipFile(test, "w") as archive:
            for name in proof.ASSETS:
                (fixture / name).write_bytes(b"{}")
                archive.writestr("assets/platform-roundtrip-v1/" + name, b"{}")
        executable = self.root / "native"
        executable.write_bytes(b"synthetic executable placeholder")
        sdk = self.root / "sdk/platform-tools"
        sdk.mkdir(parents=True)
        adb = sdk / "adb.exe"
        adb.write_bytes(b"placeholder")
        return SimpleNamespace(alias="A", serial="not-a-device", adb=adb, app_apk=app, test_apk=test,
                               fixture_executable=executable, fixtures=fixture,
                               output_directory=self.root / "proof")

    def setup_pipeline(self, args, wire=transcript(), clean=True):
        identities = {proof.PACKAGE: proof.digest(args.app_apk.read_bytes()),
                      proof.TEST_PACKAGE: proof.digest(args.test_apk.read_bytes())}
        fake = SimpleNamespace(clients_cleaned=True)
        def shell(*words, **kwargs):
            self.assertTrue(fake.clients_cleaned, "No command after uncertain cleanup")
            self.assertEqual("getprop", words[0])
            return {"sys.boot_completed": b"1", "ro.build.version.sdk": b"35", "ro.product.cpu.abi": b"x86_64"}[words[1]]
        fake.shell = shell
        def raw(*words, **kwargs):
            fake.clients_cleaned = clean
            return SimpleNamespace(stdout=wire, cleanup_complete=clean,
                                   status="completed" if clean else "timeout", returncode=0 if clean else None)
        fake.raw = raw
        def badging(command, **kwargs):
            package = proof.PACKAGE if command[-1] == str(args.app_apk) else proof.TEST_PACKAGE
            return SimpleNamespace(stdout=("package: name='" + package + "' versionCode='1'\n").encode())
        for target, value in (("OwnedDevice", fake), ("protected_packages", identities)):
            handle = patch.object(proof, target, return_value=value)
            self.addCleanup(handle.stop)
            handle.start()
        handle = patch.object(proof.subprocess, "run", side_effect=badging)
        self.addCleanup(handle.stop)
        handle.start()
        return fake, identities

    def test_failed_test_is_retained_and_never_reaches_native_verification(self):
        args = self.args()
        self.setup_pipeline(args, transcript("-2", "FAILURES!!!"))
        with patch.object(proof, "stop_owned") as stop, patch.object(proof, "native_check") as native:
            result = proof.run(args)
        self.assertEqual("failed", result["status"])
        self.assertEqual("instrumentation_failed", result["failure"])
        self.assertEqual(transcript("-2", "FAILURES!!!"), (args.output_directory / "outbound.raw.txt").read_bytes())
        native.assert_not_called()
        self.assertEqual(3, stop.call_count)  # Initial, phase drain, final ownership check.

    def test_timeout_retains_partial_raw_and_stops_after_unknown_cleanup(self):
        args = self.args()
        self.setup_pipeline(args, b"partial synthetic transcript", clean=False)
        with patch.object(proof, "stop_owned") as stop, patch.object(proof, "native_check") as native:
            result = proof.run(args)
        self.assertEqual("failed", result["status"])
        self.assertFalse(result["adb_clients_cleaned"])
        self.assertEqual(b"partial synthetic transcript", (args.output_directory / "outbound.raw.txt").read_bytes())
        self.assertEqual(1, stop.call_count)
        native.assert_not_called()

    def test_installed_artifact_mismatch_never_stops_or_runs_test(self):
        args = self.args()
        fake, before = self.setup_pipeline(args)
        before[proof.TEST_PACKAGE] = "0" * 64
        with patch.object(proof, "stop_owned") as stop, patch.object(fake, "raw") as raw:
            result = proof.run(args)
        self.assertEqual("installed_artifact_mismatch", result["failure"])
        stop.assert_not_called()
        raw.assert_not_called()

    def test_native_cleanup_unknown_prevents_transfer_and_device_cleanup(self):
        args = self.args()
        self.setup_pipeline(args)
        def unknown(*arguments):
            arguments[-1]("native", cleanup=False)
            raise proof.Failure("process_failed")
        with patch.object(proof, "phase", return_value={"passed": 1}), \
             patch.object(proof, "remote_marker"), patch.object(proof, "remote_read", return_value=b"{}"), \
             patch.object(proof, "native_check", side_effect=unknown), \
             patch.object(proof, "put_return") as transfer, patch.object(proof, "stop_owned") as stop:
            result = proof.run(args)
        self.assertFalse(result["native_clients_cleaned"])
        self.assertEqual("failed", result["status"])
        self.assertEqual(1, stop.call_count)
        transfer.assert_not_called()

    def test_return_collision_has_no_overwrite_or_fallback(self):
        device = SimpleNamespace(shell=lambda *args, **kwargs: None)
        with patch.object(proof, "remote_marker"), \
             patch.object(device, "shell", side_effect=proof.Failure("device_command_failed")) as call, \
             patch.object(proof, "remote_read") as read:
            with self.assertRaises(proof.Failure):
                proof.put_return(device, "fixed-run", b"synthetic bytes")
        self.assertEqual(1, call.call_count)
        self.assertEqual(b"synthetic bytes", call.call_args.kwargs["request"])
        read.assert_not_called()

    def test_unknown_native_cleanup_survives_raw_persistence_failure(self):
        args = self.args()
        self.setup_pipeline(args)
        actual_write = proof.write_new
        def failed_raw(path, data):
            if Path(path).name == "verify.raw.txt":
                raise OSError("synthetic disk full")
            actual_write(path, data)
        unknown = SimpleNamespace(cleanup_complete=False, status="cleanup_failed", returncode=None,
                                  stdout=b"partial synthetic result")
        with patch.object(proof, "phase", return_value={"passed": 1}), \
             patch.object(proof, "remote_marker"), patch.object(proof, "remote_read", return_value=b"{}"), \
             patch.object(proof.process_owner, "run_process", return_value=unknown), \
             patch.object(proof, "write_new", side_effect=failed_raw), \
             patch.object(proof, "put_return") as transfer, patch.object(proof, "stop_owned") as stop:
            result = proof.run(args)
        self.assertFalse(result["native_clients_cleaned"])
        self.assertEqual("failed", result["status"])
        self.assertEqual(1, stop.call_count)
        transfer.assert_not_called()

    def test_changed_protected_package_cannot_be_reported_as_a_pass(self):
        args = self.args()
        self.setup_pipeline(args)
        original = {proof.PACKAGE: proof.digest(args.app_apk.read_bytes()),
                    proof.TEST_PACKAGE: proof.digest(args.test_apk.read_bytes())}
        changed = dict(original, **{"org.locallore.other": "0" * 64})
        def checked(executable, mode, output, inputs, fixtures, journal):
            output.mkdir()
            if mode == "verify":
                (output / "android-return.json").write_bytes(b"{}")
                (output / "expected-android-final.json").write_bytes(b"{}")
            return {"status": "passed"}
        with patch.object(proof, "protected_packages", side_effect=[original, changed]), \
             patch.object(proof, "phase", return_value={"passed": 1}), \
             patch.object(proof, "remote_marker"), patch.object(proof, "remote_read", return_value=b"{}"), \
             patch.object(proof, "native_check", side_effect=checked), \
             patch.object(proof, "put_return"), patch.object(proof, "stop_owned"):
            result = proof.run(args)
        self.assertEqual(4, len(result["phases"]))
        self.assertFalse(result["prior_packages_preserved"])
        self.assertEqual("failed", result["status"])


if __name__ == "__main__":
    unittest.main()
