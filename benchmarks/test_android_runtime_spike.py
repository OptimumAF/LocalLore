"""Synthetic SDK/process protocol checks. No device, native SDK or model required."""
import base64
import json
import unittest
from unittest.mock import patch
from types import SimpleNamespace

import android_runtime_spike as spike


def envelope(metrics=None, output=None):
    if metrics is None:
        metrics = dict(worker_off_main=True, owners_balanced=True, generated_text_logged=False,
                       engines_opened=1, engines_closed=1, conversations_opened=1,
                       conversations_closed=1, main_pulses=3)
    if output is None:
        output = dict(version=1, status="completed", text="Synthetic Lantern", error=None,
                      load_ms=1, generation_ms=1, output_tokens=2, input_tokens=8,
                      schema_enforced=False, thinking_disabled=True, template_applied=True)
    return (b"INSTRUMENTATION_RESULT: result_base64=" + base64.b64encode(json.dumps(output).encode())
            + b"\r\nINSTRUMENTATION_RESULT: metrics=" + json.dumps(metrics).encode() + b"\r\n")


class SdkEnvelopeTests(unittest.TestCase):
    def test_expired_cancellation_budget_does_not_release_the_native_barrier(self):
        from test_android_runtime_ownership_review import ImmediateDevice
        device = ImmediateDevice()
        scripts = []
        device.script = lambda command, **kwargs: scripts.append(command) or b""
        # Windows Python 3.9 monotonic ticks can be coarser than a microsecond.
        # Control the clock so this tests cancellation ordering, not scheduler timing.
        with patch.object(spike.time, "monotonic", side_effect=iter([0.0] + [1.0] * 32)):
            result = spike.NativeWorker(device, "/fixed/owner").run("/fixed/binary", [], cancel_after=.5)
        self.assertEqual(result.status, "cancelled")
        self.assertFalse(any(command.endswith("/release") for command in scripts))
        self.assertTrue(any(command.endswith("/cancel") for command in scripts))

    def test_valid_result_keeps_text_in_memory_and_only_numeric_metadata(self):
        output, metrics = spike.sdk_response(envelope())
        self.assertEqual(spike.host.parse_worker(output)["text"], "Synthetic Lantern")
        self.assertNotIn("Synthetic Lantern", json.dumps(metrics))

    def test_duplicate_result_records_or_invalid_base64_fail_closed(self):
        for raw in (envelope() + envelope(), envelope().replace(b"result_base64=", b"result_base64=***")):
            self.assertIsNone(spike.sdk_response(raw))

    def test_unbalanced_owners_and_main_work_are_not_cleanup_evidence(self):
        base = dict(worker_off_main=True, owners_balanced=True, generated_text_logged=False,
                    engines_opened=1, engines_closed=1, conversations_opened=1, conversations_closed=1, main_pulses=3)
        for key, value in (("worker_off_main", False), ("owners_balanced", False),
                           ("generated_text_logged", True), ("engines_closed", 0),
                           ("conversations_closed", 0), ("main_pulses", 0), ("engines_opened", True)):
            with self.subTest(key=key):
                self.assertIsNone(spike.sdk_response(envelope(dict(base, **{key: value}))))

    def test_unknown_private_metrics_never_reach_public_aggregates(self):
        raw = envelope().replace(b'"main_pulses": 3', b'"main_pulses": 3, "exception": "PRIVATE-731"')
        result = spike.sdk_response(raw)
        self.assertIsNotNone(result)
        self.assertNotIn("PRIVATE-731", json.dumps(result[1]))

    def test_duplicate_nonfinite_and_private_numeric_fields_are_rejected(self):
        for change in (b'"main_pulses": 3, "main_pulses": 5', b'"main_pulses": NaN',
                       b'"main_pulses": "PRIVATE-731"'):
            self.assertIsNone(spike.sdk_response(envelope().replace(b'"main_pulses": 3', change)))

    def test_apk_hash_mismatch_cannot_force_stop_an_unknown_package(self):
        calls = []
        def shell(*args, **kwargs):
            calls.append(args)
            return b"package:/data/app/base.apk\n" if args[0] == "pm" else b"0" * 64 + b"  /data/app/base.apk\n"
        worker = spike.SdkWorker(SimpleNamespace(shell=shell), "1" * 64)
        with self.assertRaises(spike.Failure):
            worker.stop()
        self.assertFalse(any(args[0] == "am" for args in calls))

    def test_native_markers_accept_observed_windows_adb_newlines(self):
        self.assertEqual(spike.parse_done(b"completed 0\r\n"), ("completed", 0))
        self.assertIsNone(spike.parse_done(b"completed 0\r\nPRIVATE"))


if __name__ == "__main__":
    unittest.main()
