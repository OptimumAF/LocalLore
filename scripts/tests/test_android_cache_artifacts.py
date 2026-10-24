"""Artifact identity stays bound across an admitted controller lifecycle; no devices/models."""
import base64
import json
import shlex
import unittest
from unittest.mock import Mock, patch

from test_android_cache_control import FakeDevice, INSTALLED, UUID, decoded, model, response, sample
import android_cache_control as control


class CacheArtifactTests(unittest.TestCase):
    def invoke(self, selected, installed, identity=None, measurements=None):
        device = FakeDevice(override=lambda _d, event, _args:
            response((installed() + "  " + INSTALLED + "\n").encode()) if event == "package_hash" else None)
        measure = Mock(side_effect=measurements or [sample(), sample()])
        identity = identity or Mock(return_value=model())
        sink = Mock()
        with patch.object(control.cache_result, "parse_result", return_value=decoded()):
            result = control.run_control(device, selected, "gift", UUID, measure, identity, sink)
        return result, device, measure, identity, sink

    def test_legacy_and_guarded_lifecycles_use_their_own_hash_and_worker_provenance(self):
        for selected in (control.APK_SHA256, control.GUARDED_APK_SHA256):
            with self.subTest(selected=selected):
                result, device, measure, identity, sink = self.invoke(selected, lambda: selected)
                self.assertTrue(result["check_passed"])
                self.assertEqual((device.launches, device.stops), (1, 3))
                self.assertEqual((measure.call_count, identity.call_count, sink.call_count), (2, 1, 1))
                play = [shlex.split(args[1]) for args, _ in device.calls
                        if shlex.split(args[1])[:2] == ["am", "instrument"]]
                self.assertEqual(len(play), 1)
                payload = play[0][play[0].index("profile_base64") + 1]
                self.assertEqual(json.loads(base64.b64decode(payload)), control.play.make_profile(selected))

    def test_both_known_artifacts_are_rejected_when_installed_bytes_differ_from_selection(self):
        for selected, installed in ((control.APK_SHA256, control.GUARDED_APK_SHA256),
                                    (control.GUARDED_APK_SHA256, control.APK_SHA256)):
            with self.subTest(selected=selected):
                result, device, _, identity, sink = self.invoke(selected, lambda: installed)
                self.assertEqual(result["failure_stage"], "initial_package_hash")
                self.assertFalse(result["check_passed"])
                self.assertEqual((device.stops, device.launches), (0, 0))
                identity.assert_not_called(); sink.assert_not_called()

    def test_model_callback_cannot_switch_between_known_artifacts(self):
        for selected, replacement in ((control.APK_SHA256, control.GUARDED_APK_SHA256),
                                      (control.GUARDED_APK_SHA256, control.APK_SHA256)):
            with self.subTest(selected=selected):
                installed = [selected]
                def identify():
                    installed[0] = replacement
                    return model()
                result, device, measure, _, sink = self.invoke(selected, lambda: installed[0], identify)
                self.assertTrue(result["model_verified"])
                self.assertEqual(result["failure_stage"], "verified_model_package_hash")
                self.assertEqual(result["cleanup_failure_stage"], "final_package_hash")
                self.assertEqual((device.stops, device.launches, measure.call_count), (1, 0, 1))
                self.assertFalse(result["process_absent"])
                self.assertTrue(result["clients_cleaned"])
                self.assertEqual(result["post"]["reasons"], ["operation_ownership_unknown"])
                sink.assert_not_called()

    def test_unknown_identity_never_even_samples_and_known_pre_refusal_never_touches_package(self):
        for unknown in ("0" * 64, None, True, [], "private-artifact-canary"):
            result, device, measure, identity, _ = self.invoke(unknown, lambda: control.APK_SHA256)
            self.assertEqual(result["status"], "input_refused")
            self.assertEqual(device.calls, [])
            measure.assert_not_called(); identity.assert_not_called()
        blocked = sample(); blocked["cache_free_bytes"] = 0
        result, device, _, identity, _ = self.invoke(control.GUARDED_APK_SHA256,
            lambda: control.GUARDED_APK_SHA256, measurements=[blocked])
        self.assertEqual(result["status"], "admission_blocked")
        self.assertEqual(device.calls, [])
        identity.assert_not_called()

    def test_default_client_keeps_legacy_pin_and_selected_identity_has_no_public_setter(self):
        old = control._Client(FakeDevice())
        selected = control._Client(FakeDevice(), control.GUARDED_APK_SHA256)
        self.assertEqual(old.apk_sha, control.APK_SHA256)
        self.assertEqual(selected.apk_sha, control.GUARDED_APK_SHA256)
        with self.assertRaises(AttributeError):
            selected.apk_sha = control.APK_SHA256


if __name__ == "__main__":
    unittest.main()
