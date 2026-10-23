"""Independent synthetic control regressions; no ADB, runtime or model execution."""
import base64
import json
import threading
import unittest
from types import SimpleNamespace
from unittest.mock import patch

import android_runtime_spike as spike


CANARY = "SYNTHETIC-PRIVATE-CONTROL-REVIEW-941"
SHA = "1" * 64


def envelope():
    response = dict(version=1, status="completed", text=CANARY, error=None,
                    load_ms=1.0, generation_ms=2.0, input_tokens=16, output_tokens=2,
                    schema_enforced=True, thinking_disabled=True, template_applied=True)
    metrics = dict(worker_off_main=True, owners_balanced=True, generated_text_logged=False,
                   engines_opened=1, engines_closed=1, conversations_opened=1,
                   conversations_closed=1, main_pulses=2)
    return (b"INSTRUMENTATION_RESULT: result_base64="
            + base64.b64encode(json.dumps(response).encode())
            + b"\nINSTRUMENTATION_RESULT: metrics=" + json.dumps(metrics).encode() + b"\n")


class Clock:
    def __init__(self):
        self.now = 0.0

    def monotonic(self):
        return self.now

    def sleep(self, seconds):
        self.now += seconds


class SdkDevice:
    def __init__(self, changed=False, survives=False):
        self.events = []
        self.changed = changed
        self.survives = survives

    def shell(self, *args):
        self.events.append(args)
        if args[:2] == ("pm", "path"):
            return b"package:/synthetic/base.apk\n"
        if args[0] == "sha256sum":
            # Simulate a package replacement after the first successful check.
            count = sum(item[0] == "sha256sum" for item in self.events)
            return (("2" * 64 if self.changed and count > 1 else SHA) + "  apk\n").encode()
        return b""

    def script(self, command):
        self.events.append(("script", command))
        if "printf absent" in command:
            return b"running" if self.survives else b"absent"
        return b"123\n" if self.survives else b""

    def private_write(self, data):
        self.events.append(("write",))

    def raw(self, *args, **kwargs):
        self.events.append(("launch",))
        return SimpleNamespace(status="completed", stdout=envelope(), returncode=0,
                               cleanup_complete=True)


class SetupDevice:
    def __init__(self, failing, command_cleaned=True, remove_fails=False):
        self.failing = failing
        self.command_cleaned = command_cleaned
        self.remove_fails = remove_fails
        self.events = []

    def fail(self):
        error = spike.Failure(CANARY)
        error.command_cleaned = self.command_cleaned
        raise error

    def shell(self, *args):
        self.events.append(args)
        if args[0] == self.failing:
            self.fail()
        if self.remove_fails and args[0] == "rm":
            self.fail()
        return b""

    def put_bytes(self, data, path):
        self.events.append(("write", path))
        if self.failing == "write":
            self.fail()


class ControlBehaviorTests(unittest.TestCase):
    def test_sdk_stops_and_proves_absence_before_publishing_request(self):
        device = SdkDevice()
        result = spike.SdkWorker(device, SHA).run("unused", [], b"synthetic")
        self.assertEqual(result.status, "completed")
        write = device.events.index(("write",))
        stop = next(index for index, item in enumerate(device.events) if item[:2] == ("am", "force-stop"))
        absence = next(index for index, item in enumerate(device.events) if item[0] == "script")
        self.assertLess(stop, absence)
        self.assertLess(absence, write)

    def test_changed_apk_cannot_authorize_force_stop_or_request_publication(self):
        device = SdkDevice(changed=True)
        try:
            spike.SdkWorker(device, SHA).run("unused", [], b"synthetic")
        except spike.Failure:
            pass
        self.assertFalse(any(item[:2] == ("am", "force-stop") for item in device.events))
        self.assertNotIn(("write",), device.events)
        self.assertNotIn(("launch",), device.events)

    def test_surviving_sdk_process_prevents_publication_and_discards_text(self):
        device, clock = SdkDevice(survives=True), Clock()
        with patch.object(spike.time, "monotonic", clock.monotonic), patch.object(spike.time, "sleep", clock.sleep):
            result = spike.SdkWorker(device, SHA).run("unused", [], b"synthetic")
        self.assertEqual(result.status, "cleanup_failed")
        self.assertFalse(result.cleanup_complete)
        self.assertEqual(result.cleanup_failure_stage, "sdk_stop_absence")
        self.assertEqual(result.stdout, b"")
        self.assertEqual(result.metrics, {})
        self.assertNotIn(("write",), device.events)
        self.assertNotIn(("launch",), device.events)

    def test_native_partial_request_failure_removes_only_created_owned_files(self):
        device = SetupDevice("write")
        result = spike.NativeWorker(device, "/synthetic/owner").run("/synthetic/worker", [])
        self.assertEqual(result.status, "setup_failed")
        self.assertTrue(result.cleanup_complete)  # No process was launched.
        self.assertTrue(result.adb_cleanup_complete)
        self.assertTrue(result.directory_cleanup_complete)
        directory = next(item[3] for item in device.events if item[0] == "mkdir")
        removals = [item for item in device.events if item[0] == "rm"]
        self.assertEqual(len(removals), 1)
        self.assertTrue(all(path.startswith(directory + "/") for path in removals[0][3:]))
        self.assertIn(("rmdir", directory), device.events)
        self.assertFalse(any(item[0] in ("kill", "pkill") for item in device.events))
        self.assertNotIn(CANARY, repr(result))
        self.assertEqual(result.failure_stage, "native_write_request")

    def test_native_mkdir_failure_does_not_remove_unowned_directory(self):
        device = SetupDevice("mkdir")
        result = spike.NativeWorker(device, "/synthetic/owner").run("/synthetic/worker", [])
        self.assertEqual(result.status, "setup_failed")
        self.assertTrue(result.cleanup_complete)
        self.assertTrue(result.adb_cleanup_complete)
        self.assertFalse(any(item[0] in ("rm", "rmdir") for item in device.events))

    def test_native_unknown_partial_transfer_preserves_files_until_client_is_known_drained(self):
        device = SetupDevice("write", command_cleaned=False)
        result = spike.NativeWorker(device, "/synthetic/owner").run("/synthetic/worker", [])
        self.assertEqual(result.status, "setup_failed")
        self.assertTrue(result.cleanup_complete)  # No inference owner was launched.
        self.assertFalse(result.adb_cleanup_complete)
        self.assertFalse(result.directory_cleanup_complete)
        self.assertFalse(any(item[0] in ("rm", "rmdir") for item in device.events))

    def test_native_file_removal_failure_preserves_independent_process_proof(self):
        device = SetupDevice("write", remove_fails=True)
        result = spike.NativeWorker(device, "/synthetic/owner").run("/synthetic/worker", [])
        self.assertEqual(result.status, "setup_failed")
        self.assertTrue(result.cleanup_complete)
        self.assertTrue(result.adb_cleanup_complete)
        self.assertFalse(result.directory_cleanup_complete)
        self.assertNotIn(CANARY, repr(result))
        self.assertEqual(result.cleanup_failure_stage, "native_remove_run")

    def test_native_unknown_removal_client_revokes_previous_adb_cleanup_proof(self):
        device = SetupDevice("write")
        original = device.shell

        def unknown_remove(*args):
            if args[0] == "rm":
                error = spike.Failure(CANARY)
                error.command_cleaned = False
                raise error
            return original(*args)

        device.shell = unknown_remove
        result = spike.NativeWorker(device, "/synthetic/owner").run("/synthetic/worker", [])
        self.assertTrue(result.cleanup_complete)
        self.assertFalse(result.adb_cleanup_complete)
        self.assertFalse(result.directory_cleanup_complete)
        self.assertEqual(result.cleanup_failure_stage, "native_remove_run")

    def test_sdk_unknown_request_removal_client_cannot_accept_completed_generation(self):
        device = SdkDevice()
        original = device.shell

        def unknown_remove(*args):
            if args[:3] == ("run-as", spike.PACKAGE, "rm"):
                error = spike.Failure(CANARY)
                error.command_cleaned = False
                raise error
            return original(*args)

        device.shell = unknown_remove
        result = spike.SdkWorker(device, SHA).run("unused", [], b"synthetic")
        self.assertFalse(result.adb_cleanup_complete)
        self.assertFalse(result.directory_cleanup_complete)
        self.assertNotEqual(result.status, "completed")
        self.assertEqual(result.stdout, b"")
        self.assertEqual(result.metrics, {})

    def test_sdk_final_stop_failure_discards_previously_completed_generation(self):
        device, clock = SdkDevice(), Clock()
        original = device.script

        def fail_only_after_launch(command):
            device.survives = ("launch",) in device.events
            return original(command)

        device.script = fail_only_after_launch
        with patch.object(spike.time, "monotonic", clock.monotonic), patch.object(spike.time, "sleep", clock.sleep):
            result = spike.SdkWorker(device, SHA).run("unused", [], b"synthetic")
        self.assertEqual(result.status, "cleanup_failed")
        self.assertFalse(result.cleanup_complete)
        self.assertEqual(result.stdout, b"")
        self.assertEqual(result.metrics, {})

    def test_sdk_unknown_request_transfer_cannot_claim_adb_cleanup_or_remove_request(self):
        device = SdkDevice()

        def failed_write(data):
            device.events.append(("write",))
            error = spike.Failure(CANARY)
            error.command_cleaned = False
            raise error

        device.private_write = failed_write
        result = spike.SdkWorker(device, SHA).run("unused", [], b"synthetic")
        self.assertEqual(result.status, "setup_failed")
        self.assertFalse(result.adb_cleanup_complete)
        self.assertFalse(result.directory_cleanup_complete)
        self.assertNotIn(("launch",), device.events)
        self.assertFalse(any(item[:3] == ("run-as", spike.PACKAGE, "rm") for item in device.events))
        self.assertEqual(result.stdout, b"")
        self.assertNotIn(CANARY, repr(result))
        self.assertEqual(result.failure_stage, "sdk_write_request")

    def test_sdk_thread_start_failure_is_returned_without_private_exception(self):
        device = SdkDevice()
        with patch.object(spike.threading.Thread, "start", side_effect=RuntimeError(CANARY)):
            result = spike.SdkWorker(device, SHA).run("unused", [], b"synthetic")
        self.assertNotEqual(result.status, "completed")
        self.assertEqual(result.stdout, b"")
        self.assertNotIn(CANARY, repr(result))
        self.assertEqual(result.failure_stage, "sdk_launch_instrumentation")

    def test_sdk_launcher_exception_retains_primary_stage_and_unknown_client_cleanup(self):
        device = SdkDevice()

        def failed_raw(*args, **kwargs):
            raise OSError(CANARY)

        device.raw = failed_raw
        result = spike.SdkWorker(device, SHA).run("unused", [], b"synthetic")
        self.assertEqual(result.failure_stage, "sdk_launch_instrumentation")
        self.assertEqual(result.cleanup_failure_stage, "sdk_join_adb")
        self.assertFalse(result.adb_cleanup_complete)
        self.assertFalse(result.cleanup_complete)
        self.assertEqual(result.stdout, b"")
        self.assertEqual(result.metrics, {})
        self.assertNotIn(CANARY, json.dumps(spike.remote_metadata(result)))

    def test_native_thread_start_failure_cleans_known_unlaunched_run(self):
        device = SetupDevice(None)
        with patch.object(spike.threading.Thread, "start", side_effect=RuntimeError(CANARY)):
            result = spike.NativeWorker(device, "/synthetic/owner").run("/synthetic/worker", [])
        self.assertNotEqual(result.status, "completed")
        self.assertTrue(result.cleanup_complete)
        self.assertTrue(result.directory_cleanup_complete)
        self.assertNotIn(CANARY, repr(result))
        self.assertEqual(result.failure_stage, "native_launch_owner")

    def test_native_recovery_cancel_oserror_cannot_escape_or_claim_client_cleanup(self):
        device = SetupDevice(None)
        device.raw = lambda *args, **kwargs: SimpleNamespace(status="completed", stdout=b"", returncode=0,
                                                           cleanup_complete=True)
        device.read_optional = lambda path: b"malformed-owner\n"

        def failed_cancel(*args, **kwargs):
            raise OSError(CANARY)

        device.script = failed_cancel
        result = spike.NativeWorker(device, "/synthetic/owner").run("/synthetic/worker", [])
        self.assertEqual(result.status, "cleanup_failed")
        self.assertFalse(result.cleanup_complete)
        self.assertFalse(result.adb_cleanup_complete)
        self.assertFalse(result.directory_cleanup_complete)
        self.assertEqual(result.failure_stage, "native_read_owner")
        self.assertNotIn(CANARY, json.dumps(spike.remote_metadata(result)))

    def test_sdk_startup_failure_keeps_attempt_denominator_and_private_diagnostics_out(self):
        fixture = dict(version=1, case="gift", preflight_error=None, revision=0,
                       director=dict(version=1, role="director", prompt="synthetic",
                                     schema=None, max_tokens=350, context_tokens=4096, threads=4))
        worker = spike.SdkWorker(SdkDevice(), SHA)
        with patch.object(spike, "oracle", return_value=fixture), \
                patch.object(spike.threading.Thread, "start", side_effect=RuntimeError(CANARY)):
            report = spike.experiment(None, worker, "unused", "oracle", "model")
        self.assertEqual(report["attempted_roles"], 1)
        self.assertEqual(len(report["roles"]), 1)
        self.assertEqual(report["roles"][0]["failure_stage"], "sdk_launch_instrumentation")
        self.assertNotEqual(report["status"], "committed")
        self.assertNotIn(CANARY, json.dumps(report, allow_nan=False))

    def test_sdk_cancel_drains_late_launcher_before_final_stop_and_absence_check(self):
        device, clock = SdkDevice(), Clock()
        real_event = threading.Event

        class FastFinished:
            def __init__(self):
                self.event = real_event()

            def set(self):
                self.event.set()

            def is_set(self):
                return self.event.is_set()

            def wait(self, timeout=None):
                # Long control waits advance immediately; short waits yield to the fake launcher.
                return self.event.wait(.001) if timeout is not None and timeout < 1 else self.event.is_set()

        events = []

        def event_factory():
            event = FastFinished() if not events else real_event()
            events.append(event)
            return event

        def advancing_time():
            clock.now += .05
            return clock.now

        def late_raw(*args, **kwargs):
            # Deterministic launch delayed until cancellation reaches the host client.
            if not kwargs["cancel"].wait(1):
                raise AssertionError("host cancellation was never delivered")
            device.events.append(("late_launch",))
            return SimpleNamespace(status="cancelled", stdout=envelope(), returncode=0,
                                   cleanup_complete=True)

        device.raw = late_raw
        with patch.object(spike.time, "monotonic", advancing_time), \
                patch.object(spike.time, "sleep", clock.sleep), \
                patch.object(spike.threading, "Event", event_factory):
            result = spike.SdkWorker(device, SHA).run("unused", [], b"synthetic", deadline=2, cancel_after=.5)
        late = device.events.index(("late_launch",))
        last_stop = max(index for index, item in enumerate(device.events) if item[:2] == ("am", "force-stop"))
        last_absence = max(index for index, item in enumerate(device.events) if item[0] == "script")
        self.assertLess(late, last_stop)
        self.assertLess(last_stop, last_absence)
        self.assertEqual(result.status, "cancelled")
        self.assertTrue(result.cleanup_complete)
        self.assertTrue(result.adb_cleanup_complete)
        self.assertEqual(result.stdout, b"")


class DiagnosticPrivacyTests(unittest.TestCase):
    def test_untrusted_stage_status_and_numeric_fields_are_projected_without_private_text(self):
        for elapsed in (CANARY, True, float("nan"), float("inf"), 10 ** 1000):
            for stage in (CANARY, [CANARY], {CANARY: CANARY}, True):
                with self.subTest(elapsed_type=type(elapsed).__name__, stage_type=type(stage).__name__):
                    result = SimpleNamespace(status=CANARY, elapsed_ms=elapsed, cleanup_complete=CANARY,
                                             adb_cleanup_complete=1, directory_cleanup_complete=[],
                                             returncode=True, failure_stage=stage, cleanup_failure_stage=stage,
                                             stdout=CANARY.encode(), metrics={CANARY: CANARY})
                    metadata = spike.remote_metadata(result)
                    self.assertEqual(metadata["failure_stage"], "unknown")
                    self.assertEqual(metadata["cleanup_failure_stage"], "unknown")
                    self.assertEqual(metadata["process_status"], "owner_failed")
                    self.assertEqual(metadata["wall_ms"], 0)
                    self.assertIsNone(metadata["worker_exit_code"])
                    self.assertIs(metadata["cleanup_complete"], False)
                    self.assertIs(metadata["adb_cleanup_complete"], False)
                    self.assertIs(metadata["directory_cleanup_complete"], False)
                    self.assertNotIn(CANARY, json.dumps(metadata, allow_nan=False))

    def test_known_stages_preserve_independent_cleanup_diagnostics(self):
        result = spike.RemoteResult("setup_failed", 12, True, stdout=CANARY.encode(),
                                    adb_cleanup_complete=True, failure_stage="native_write_request",
                                    cleanup_failure_stage="native_remove_run")
        metadata = spike.remote_metadata(result)
        self.assertEqual(metadata["failure_stage"], "native_write_request")
        self.assertEqual(metadata["cleanup_failure_stage"], "native_remove_run")
        self.assertTrue(metadata["cleanup_complete"])
        self.assertFalse(metadata["directory_cleanup_complete"])
        self.assertNotIn(CANARY, repr(result))
        self.assertNotIn(CANARY, json.dumps(metadata))


if __name__ == "__main__":
    unittest.main()
