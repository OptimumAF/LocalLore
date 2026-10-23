"""Independent model-free controller lifecycle cases; no ADB or inference is executed.

Copyright 2026 LocalLore contributors. SPDX-License-Identifier: Apache-2.0
"""
import copy
import importlib
import json
from pathlib import Path
import shlex
import sys
from types import ModuleType, SimpleNamespace
import unittest
from unittest.mock import Mock, patch

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "benchmarks"))
# The coordinator owns this required production dependency. A temporary TEST-ONLY
# module allows the independent controller packet to run before its integration.
try:
    control = importlib.import_module("android_cache_control")
except ModuleNotFoundError as error:
    if error.name != "android_cache_result":
        raise
    parser_stub = ModuleType("android_cache_result")
    parser_stub.parse_result = lambda *_: None
    with patch.dict(sys.modules, {"android_cache_result": parser_stub}):
        control = importlib.import_module("android_cache_control")

UUID = "ABCD-1234"
PRIVATE = "private-story-path-identity-canary"
INSTALLED = "/data/app/~~synthetic/cacheprobe/base.apk"


def sample(**changes):
    return dict(version=1, volume_uuid=UUID, userdata_device=10, cache_device=20,
        mounted=True, primary=False, emulated=False, writable=True, backing_verified=True,
        userdata_free_bytes=4 * control.admission.GIB, cache_free_bytes=8 * control.admission.GIB,
        cache_bytes=0, userdata_host_volume="system", cache_host_volume="secondary",
        evidence_host_volume="secondary", userdata_host_free_bytes=20 * control.admission.GIB,
        cache_host_free_bytes=30 * control.admission.GIB, evidence_free_bytes=30 * control.admission.GIB,
        **changes)


def model(**changes):
    return dict(verified=True, volume_uuid=UUID, sha256=control.MODEL_SHA256,
                bytes=control.MODEL_BYTES, diagnostic="verified", **changes)


def decoded(**changes):
    turn = dict(outcome="committed", owner_drained=True, reopen_equal=True, error=None,
                canon_unchanged=False, first_output_observed=False)
    return dict(result={"case": "gift", "turns": [turn], "gift_seeded": False},
        sdk={"engines_opened": 1, "engines_closed": 1, "conversations_opened": 2,
             "conversations_closed": 2}, status="completed", error=None, storage_samples_valid=True, **changes)


def response(raw=b"", code=0, cleaned=True, status="completed"):
    return SimpleNamespace(stdout=raw, returncode=code, cleanup_complete=cleaned, status=status)


class FakeDevice:
    def __init__(self, override=None):
        self.clients_cleaned = True
        self.running = True
        self.calls = []
        self.events = []
        self.override = override
        self.launches = 0
        self.stops = 0

    def raw(self, args, **kwargs):
        if not self.clients_cleaned:
            raise AssertionError("dependent transport after unknown ownership")
        self.calls.append((args, kwargs))
        words = shlex.split(args[1])
        if words[:2] == ["pm", "path"]:
            event = "package_path"
            result = response(("package:" + INSTALLED + "\n").encode())
        elif words[0] == "sha256sum":
            event = "package_hash"
            result = response((control.APK_SHA256 + "  " + INSTALLED + "\n").encode())
        elif words[0] == "pidof":
            event = "process_probe"
            result = response(b"1234\n") if self.running else response(code=1)
        elif words[0] == "cat" and words[1].endswith("/cmdline"):
            event = "cmdline"
            result = response(control.PACKAGE.encode() + b"\0")
        elif words[0] == "cat" and words[1].endswith("/stat"):
            event = "stat"
            result = response(("1234 (synthetic process) " + " ".join(["S"] + ["0"] * 18 + ["9876"]) + "\n").encode())
        elif words[:2] == ["am", "force-stop"]:
            event = "stop"
            self.stops += 1
            result = response()
        elif words[:2] == ["am", "instrument"]:
            event = "play"
            self.launches += 1
            result = response(b"synthetic bounded instrumentation protocol")
        else:
            raise AssertionError("unexpected transport operation")
        self.events.append(event)
        if self.override is not None:
            changed = self.override(self, event, words)
            if changed is not None:
                result = changed
        if event == "stop" and result.returncode == 0:
            self.running = False
        if event == "play":
            self.running = True
        self.clients_cleaned &= result.cleanup_complete is True
        return result


class CacheControllerTests(unittest.TestCase):
    def invoke(self, device=None, measurements=None, identity=None, parsed=None, sink=None, case="gift", expected=UUID):
        device = device or FakeDevice()
        measure = Mock(side_effect=measurements or [sample(), sample()])
        identity = identity or Mock(return_value=model())
        sink = sink if sink is not None else Mock()
        with patch.object(control.cache_result, "parse_result", return_value=parsed if parsed is not None else decoded()) as parser:
            result = control.run_control(device, control.APK_SHA256, case, expected, measure, identity, sink)
        return result, device, measure, identity, sink, parser

    def test_whole_lifecycle_is_admitted_one_launch_and_new_package_only(self):
        result, device, measure, identity, sink, parser = self.invoke()
        self.assertTrue(result["check_passed"])
        self.assertTrue(result["process_absent"])
        self.assertTrue(result["clients_cleaned"])
        self.assertTrue(result["storage_checks_passed"])
        self.assertEqual((device.launches, device.stops, measure.call_count, identity.call_count), (1, 3, 2, 1))
        parser.assert_called_once_with(b"synthetic bounded instrumentation protocol", "gift", UUID)
        sink.assert_called_once()
        for args, _ in device.calls:
            self.assertNotIn(control.spike.PACKAGE, shlex.split(args[1]))
            self.assertNotIn("rm", shlex.split(args[1]))
        self.assertTrue(result["artifacts_retained"])
        self.assertFalse(result["phone_qualified"])

    def test_pre_refusal_has_no_package_stop_model_or_instrumentation_calls(self):
        pre = sample(); pre["cache_free_bytes"] = 0
        result, device, measure, identity, _, parser = self.invoke(measurements=[pre])
        self.assertEqual(result["status"], "admission_blocked")
        self.assertEqual(device.calls, [])
        self.assertEqual(measure.call_count, 1)
        identity.assert_not_called(); parser.assert_not_called()

    def test_wrong_expected_volume_is_blocked_before_any_package_operation(self):
        result, device, _, identity, _, _ = self.invoke(expected="FFFF-FFFF")
        self.assertEqual(result["admission"]["reasons"], ["volume_mismatch"])
        self.assertFalse(result["check_passed"])
        self.assertEqual(device.calls, [])
        identity.assert_not_called()

    def test_wrong_frozen_apk_or_case_or_uuid_does_not_even_measure(self):
        for sha, case, expected in (("a" * 64, "gift", UUID), (True, "gift", UUID),
                                    (control.APK_SHA256, PRIVATE, UUID), (control.APK_SHA256, "gift", PRIVATE)):
            device = FakeDevice(); measure = Mock(); identity = Mock()
            result = control.run_control(device, sha, case, expected, measure, identity)
            self.assertEqual(result["status"], "input_refused")
            self.assertEqual(device.calls, [])
            measure.assert_not_called(); identity.assert_not_called()
            self.assertNotIn(PRIVATE, json.dumps(result))

    def test_instrumentation_request_keeps_original_profile_and_explicit_volume(self):
        _, device, *_ = self.invoke()
        args, kwargs = next(call for call in device.calls if shlex.split(call[0][1])[:2] == ["am", "instrument"])
        words = shlex.split(args[1]); extras = {}
        for index, word in enumerate(words):
            if word == "-e":
                extras[words[index + 1]] = words[index + 2]
        self.assertEqual(kwargs["deadline"], 110)
        self.assertEqual(extras["operation"], "play")
        self.assertEqual(extras["volume_uuid"], UUID)
        self.assertRegex(extras["session"], r"^[a-f0-9]{32}$")
        import base64
        profile = json.loads(base64.b64decode(extras["profile_base64"]))
        self.assertEqual((profile["deadline_ms"], profile["director_tokens"], profile["narrator_tokens"]), (60000, 350, 220))
        self.assertEqual(profile, control.play.make_profile(control.APK_SHA256))
        self.assertEqual(words[-1], control.PACKAGE + "/" + control.INSTRUMENTATION)

    def test_raw_retention_happens_before_parser(self):
        order = []
        with patch.object(control.cache_result, "parse_result", side_effect=lambda *_: order.append("parse") or decoded()):
            result = control.run_control(FakeDevice(), control.APK_SHA256, "gift", UUID,
                Mock(side_effect=[sample(), sample()]), lambda: model(), lambda _: order.append("retain"))
        self.assertEqual(order, ["retain", "parse"])
        self.assertTrue(result["check_passed"])

    def test_accepted_receipt_survives_sink_failure_and_keeps_primary_stage(self):
        sink = Mock(side_effect=OSError(PRIVATE))
        result, _, measure, *_ = self.invoke(sink=sink)
        self.assertEqual(result["result"], decoded()["result"])
        self.assertEqual(result["failure_stage"], "raw_retention")
        self.assertFalse(result["check_passed"])
        self.assertEqual(measure.call_count, 2)
        self.assertNotIn(PRIVATE, json.dumps(result))

    def test_sdk_post_sample_failure_preserves_accepted_receipt(self):
        value = decoded(); value.update(status="error", error="volume_changed", storage_samples_valid=False)
        result, *_ = self.invoke(parsed=value)
        self.assertEqual(result["result"], decoded()["result"])
        self.assertFalse(result["result"]["turns"][0]["canon_unchanged"])
        self.assertEqual(result["worker_error"], "volume_changed")
        self.assertEqual(result["failure_stage"], "sdk_report")
        self.assertFalse(result["check_passed"])

    def test_host_post_budget_or_measure_failure_never_erases_observed_receipt(self):
        post = sample(); post["cache_bytes"] = control.admission.CACHE_ALLOWANCE + 1
        for after in (post, OSError(PRIVATE)):
            result, *_ = self.invoke(measurements=[sample(), after])
            self.assertEqual(result["result"], decoded()["result"])
            self.assertFalse(result["check_passed"])
            self.assertFalse(result["storage_checks_passed"])
            self.assertNotIn(PRIVATE, json.dumps(result))

    def test_unknown_instrumentation_client_retains_protocol_result_but_dispatches_nothing_later(self):
        device = FakeDevice(lambda _, event, __: response(b"bounded terminal", cleaned=False) if event == "play" else None)
        result, device, measure, _, sink, _ = self.invoke(device=device)
        self.assertEqual(result["result"], decoded()["result"])
        self.assertFalse(result["transport_valid"])
        self.assertFalse(result["clients_cleaned"])
        self.assertFalse(result["process_absent"])
        self.assertFalse(result["check_passed"])
        self.assertEqual((device.stops, measure.call_count), (2, 1))
        self.assertEqual(device.events[-1], "play")
        sink.assert_called_once_with(b"bounded terminal")

    def test_timeout_with_clean_client_can_stop_but_cannot_pass_or_erase_valid_terminal(self):
        device = FakeDevice(lambda _, event, __: response(b"bounded terminal", status="timeout", code=-1) if event == "play" else None)
        result, device, measure, *_ = self.invoke(device=device)
        self.assertEqual(result["result"], decoded()["result"])
        self.assertFalse(result["check_passed"])
        self.assertTrue(result["process_absent"])
        self.assertEqual((device.launches, device.stops, measure.call_count), (1, 3, 2))

    def test_final_unknown_client_keeps_receipt_and_prevents_post_measure(self):
        device = FakeDevice(lambda dev, event, _: response(cleaned=False) if event == "stop" and dev.stops == 3 else None)
        result, device, measure, *_ = self.invoke(device=device)
        self.assertEqual(result["result"], decoded()["result"])
        self.assertEqual(result["cleanup_failure_stage"], "final_force_stop")
        self.assertFalse(result["clients_cleaned"])
        self.assertFalse(result["check_passed"])
        self.assertEqual(measure.call_count, 1)
        self.assertEqual(device.events[-1], "stop")

    def test_valid_pre_sample_cannot_hide_callback_client_uncertainty(self):
        device = FakeDevice()
        def measure():
            device.clients_cleaned = False
            return sample()
        identity = Mock()
        result = control.run_control(device, control.APK_SHA256, "gift", UUID, measure, identity)
        self.assertEqual(device.calls, [])
        identity.assert_not_called()
        self.assertFalse(result["clients_cleaned"])
        self.assertFalse(result["check_passed"])

    def test_model_callback_unknown_client_blocks_instrumentation_cleanup_and_post_measure(self):
        device = FakeDevice()
        def identity():
            device.clients_cleaned = False
            return model()
        result, device, measure, *_ = self.invoke(device=device, identity=identity)
        self.assertEqual((device.launches, device.stops, measure.call_count), (0, 1, 1))
        self.assertEqual(result["failure_stage"], "model_identity")
        self.assertFalse(result["clients_cleaned"])

    def test_model_identity_full_hash_size_uuid_and_diagnostic_are_required(self):
        values = []
        for key, value in (("sha256", "0" * 64), ("bytes", control.MODEL_BYTES - 1),
                           ("volume_uuid", "FFFF-FFFF"), ("bytes", True), ("diagnostic", PRIVATE)):
            item = model(); item[key] = value; values.append(item)
        missing = model(); missing.pop("bytes"); values.append(missing)
        for value in values:
            result, device, *_ = self.invoke(identity=Mock(return_value=value))
            self.assertFalse(result["model_verified"])
            self.assertEqual(device.launches, 0)
            self.assertFalse(result["check_passed"])
            self.assertNotIn(PRIVATE, json.dumps(result))

    def test_original_model_diagnostic_survives_cleanup_failure(self):
        value = model(); value.update(verified=False, diagnostic="absent", bytes=0, sha256="")
        device = FakeDevice(lambda dev, event, _: response(code=1) if event == "stop" and dev.stops == 2 else None)
        result, _, _, _, _, _ = self.invoke(device=device, identity=Mock(return_value=value))
        self.assertEqual(result["model_diagnostic"], "absent")
        self.assertEqual(result["failure_stage"], "model_identity")
        self.assertEqual(result["cleanup_failure_stage"], "final_force_stop")

    def test_installed_identity_mismatch_never_force_stops_or_launches(self):
        device = FakeDevice(lambda _, event, __: response(("0" * 64 + "  " + INSTALLED + "\n").encode()) if event == "package_hash" else None)
        result, device, _, identity, *_ = self.invoke(device=device)
        self.assertEqual((device.stops, device.launches), (0, 0))
        identity.assert_not_called()
        self.assertEqual(result["failure_stage"], "initial_package_hash")
        self.assertFalse(result["check_passed"])

    def test_split_package_paths_and_unknown_pidof_cannot_be_absence(self):
        for event, raw, code in (("package_path", ("package:" + INSTALLED + "\npackage:/split.apk\n").encode(), 0),
                                  ("process_probe", b"", 2), ("process_probe", b"", 0),
                                  ("process_probe", b"1234 5678\n", 0), ("process_probe", PRIVATE.encode(), 1)):
            device = FakeDevice(lambda _, observed, __: response(raw, code) if observed == event else None)
            result, device, *_ = self.invoke(device=device)
            self.assertEqual((device.stops, device.launches), (0, 0))
            self.assertFalse(result["process_absent"])
            self.assertFalse(result["check_passed"])
            self.assertNotIn(PRIVATE, json.dumps(result))

    def test_process_identity_cannot_be_a_foreign_command_or_malformed_starttime(self):
        for event, raw in (("cmdline", b"different.app\0"), ("stat", b"malformed " + PRIVATE.encode())):
            device = FakeDevice(lambda _, observed, __: response(raw) if observed == event else None)
            result, device, *_ = self.invoke(device=device)
            self.assertEqual((device.stops, device.launches), (0, 0))
            self.assertFalse(result["check_passed"])
            self.assertNotIn(PRIVATE, json.dumps(result))

    def test_unsafe_or_malformed_terminal_never_reaches_public_report(self):
        with patch.object(control.cache_result, "parse_result", return_value=None):
            result = control.run_control(FakeDevice(), control.APK_SHA256, "gift", UUID,
                Mock(side_effect=[sample(), sample()]), lambda: model(), lambda _: None)
        self.assertIsNone(result["result"])
        self.assertEqual(result["status"], "invalid_terminal")
        self.assertFalse(result["check_passed"])
        self.assertNotIn("synthetic bounded", json.dumps(result))

    def test_preexisting_unknown_client_does_not_measure_or_dispatch(self):
        device = FakeDevice(); device.clients_cleaned = False
        measure, identity = Mock(), Mock()
        result = control.run_control(device, control.APK_SHA256, "gift", UUID, measure, identity)
        measure.assert_not_called(); identity.assert_not_called()
        self.assertEqual(device.calls, [])
        self.assertEqual(result["status"], "ownership_unknown")

    def test_callback_exception_without_cleanup_proof_stops_dependent_work(self):
        result, device, measure, *_ = self.invoke(identity=Mock(side_effect=OSError(PRIVATE)))
        self.assertEqual((device.launches, device.stops, measure.call_count), (0, 1, 1))
        self.assertFalse(result["clients_cleaned"])
        self.assertEqual(result["model_diagnostic"], "read_failed")
        self.assertNotIn(PRIVATE, json.dumps(result))

    def test_model_callback_process_is_verified_and_stopped_before_sdk(self):
        device = FakeDevice()
        def identity():
            device.running = True  # A completed verify_model instrumentation process.
            return model()
        result, device, *_ = self.invoke(device=device, identity=identity)
        self.assertTrue(result["check_passed"])
        play_index = device.events.index("play")
        self.assertEqual(device.events[:play_index].count("stop"), 2)
        self.assertEqual(device.events[:play_index].count("cmdline"), 2)
        self.assertEqual(device.stops, 3)

    def test_callback_cannot_replace_apk_then_launch_sdk_with_stale_identity(self):
        device = FakeDevice()
        def identity():
            device.override = lambda _, event, __: response(("0" * 64 + "  " + INSTALLED + "\n").encode()) if event == "package_hash" else None
            return model()
        result, device, measure, *_ = self.invoke(device=device, identity=identity)
        self.assertEqual(device.launches, 0)
        self.assertEqual(device.stops, 1)
        self.assertEqual(result["failure_stage"], "verified_model_package_hash")
        self.assertFalse(result["check_passed"])
        self.assertEqual(measure.call_count, 1)

    def test_unknown_pre_sdk_stop_blocks_launch_and_all_dependent_calls(self):
        device = FakeDevice(lambda dev, event, _: response(cleaned=False) if event == "stop" and dev.stops == 2 else None)
        result, device, measure, *_ = self.invoke(device=device)
        self.assertEqual(device.launches, 0)
        self.assertEqual(device.events[-1], "stop")
        self.assertEqual(result["failure_stage"], "verified_model_force_stop")
        self.assertFalse(result["clients_cleaned"])
        self.assertEqual(measure.call_count, 1)


if __name__ == "__main__":
    unittest.main()
