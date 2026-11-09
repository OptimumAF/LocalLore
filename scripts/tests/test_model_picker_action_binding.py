"""Host-only coverage of the fixed picker setup artifacts and result selector.

Copyright 2026 LocalLore contributors. SPDX-License-Identifier: Apache-2.0
"""
import copy
import hashlib
import json
from pathlib import PureWindowsPath
import unittest
from unittest.mock import call, patch

from benchmarks import android_instrumentation_evidence as evidence
from benchmarks import model_picker_action_binding as binding
from benchmarks import owned_target_contract as core


APP = "org.locallore.app.modelpickerverify"
TEST = APP + ".test"
KIND = "picker_action_scope"
CLASS = "org.locallore.app.ModelPickerActionScopeTest"
METHOD = "retiredChooseAndCheckCannotActOnReplacementStatus"
SELECTOR = CLASS + "#" + METHOD
ROOT = PureWindowsPath("D:/Dev/Experiments/LocalLore/2026-11-09-model-picker-action-scope-v1")
ROLES = ("build", "product_apk", "test_apk")


def runner_pass():
    fields = (
        f"INSTRUMENTATION_STATUS: class={CLASS}\n"
        f"INSTRUMENTATION_STATUS: test={METHOD}\n"
        "INSTRUMENTATION_STATUS: id=AndroidJUnitRunner\n"
        "INSTRUMENTATION_STATUS: current=1\n"
        "INSTRUMENTATION_STATUS: numtests=1\n"
    )
    return (
        fields + "INSTRUMENTATION_STATUS_CODE: 1\n"
        + fields + "INSTRUMENTATION_STATUS_CODE: 0\n"
        + "INSTRUMENTATION_RESULT: stream=\n\nTime: 1.234\n\nOK (1 test)\n\n"
        + "INSTRUMENTATION_CODE: -1\n"
    ).encode("ascii")


def pair_receipt(pins):
    return {
        "status": "passed",
        "selector": SELECTOR,
        "defined_in": "classes3.dex",
        "present_in_app": False,
        "test_permissions": ["android.permission.REORDER_TASKS"],
        "test_provider": {
            "document_authority": TEST + ".modelpicker",
            "control_authority": TEST + ".modelpicker.control",
            "process": ":model_picker_provider",
        },
        "app": {key: pins["product_apk"][key] for key in ("bytes", "sha256")},
        "test": {key: pins["test_apk"][key] for key in ("bytes", "sha256")},
    }


class PickerActionBindingTests(unittest.TestCase):
    def setUp(self):
        self.pins = binding.artifact_bindings()

    def test_artifacts_are_the_reviewed_b161_pair_and_receipt(self):
        self.assertEqual(binding.ANDROID_SOURCE, "ef8d3a3be38a18750725a97d85378342e5c574a5")
        self.assertEqual(set(self.pins), set(ROLES))
        expected = {
            "build": ("audit-test-pair-ef8d3a3b-v1.log", 763,
                      "50dd9fc0743a6b940a8efac56c1a2abb120731b30b35dad78aa556c549919e05"),
            "product_apk": ("app-debug.apk", 78697092,
                            "ce1bba095a49ffa1f9c8be3c6ab4fd3b1ae5502fe07a7cf49e7005fa9c0d44ca"),
            "test_apk": ("app-debug-androidTest.apk", 2423912,
                         "44815baedc1ae9dccd39976820f4a8ff94b5a3e3b3659c6881975c938f11434e"),
        }
        for role, (name, size, digest) in expected.items():
            with self.subTest(role=role):
                self.assertEqual(self.pins[role], {
                    "path": str(ROOT / name), "bytes": size, "sha256": digest,
                })

    def test_caller_cannot_mutate_the_fixed_artifact_map(self):
        original = copy.deepcopy(self.pins)
        self.pins["product_apk"]["sha256"] = "0" * 64
        del self.pins["build"]
        self.assertEqual(binding.artifact_bindings(), original)

    def test_reads_exact_receipt_then_both_artifacts_under_their_fixed_caps(self):
        receipt = json.dumps(pair_receipt(self.pins)).encode("utf-8")
        with patch.object(binding.files, "_bound", side_effect=[receipt, b"app", b"test"]) as read:
            self.assertIsNone(binding.verify_artifacts(self.pins))
        self.assertEqual(read.call_args_list, [
            call(self.pins[role], cap=self.pins[role]["bytes"]) for role in ROLES
        ])

    def test_bad_artifact_map_refuses_before_any_artifact_read(self):
        class ForeignMapping(dict):
            pass

        invalid = [None, [], ForeignMapping(self.pins)]
        replacement = copy.deepcopy(self.pins)
        replacement["build"] = ForeignMapping(replacement["build"])
        invalid.append(replacement)
        invalid.append({**self.pins, "model": self.pins["product_apk"]})
        invalid.append({role: self.pins[role] for role in ("build", "product_apk")})
        invalid.append({**self.pins, "product_apk": self.pins["test_apk"], "test_apk": self.pins["product_apk"]})
        for key, value in (
            ("path", str(ROOT / "different.apk")),
            ("sha256", "0" * 64),
            ("bytes", self.pins["product_apk"]["bytes"] + 1),
            ("bytes", float(self.pins["product_apk"]["bytes"])),
        ):
            invalid.append({**self.pins, "product_apk": {**self.pins["product_apk"], key: value}})
        for pins in invalid:
            with self.subTest(pins=pins), patch.object(binding.files, "_bound") as read:
                with self.assertRaisesRegex(core.TargetRefused, "^binding$"):
                    binding.verify_artifacts(pins)
                read.assert_not_called()

    def test_bad_pair_receipt_refuses_before_reading_either_apk(self):
        valid = pair_receipt(self.pins)
        mismatches = [
            {**valid, "selector": CLASS + "#anotherMethod"},
            {**valid, "present_in_app": 0},
            {**valid, "test_permissions": ["android.permission.INTERNET"]},
            {**valid, "test_provider": {**valid["test_provider"], "process": ":different"}},
            {**valid, "app": valid["test"], "test": valid["app"]},
            {**valid, "unexpected": "extra field"},
        ]
        malformed = [b"\xff", b"{", b"[]", b'{"status":"passed","status":"passed"}']
        for raw in malformed + [json.dumps(value).encode() for value in mismatches]:
            with self.subTest(raw=raw), patch.object(binding.files, "_bound", return_value=raw) as read:
                with self.assertRaisesRegex(core.TargetRefused, "^binding$"):
                    binding.verify_artifacts(self.pins)
                read.assert_called_once_with(self.pins["build"], cap=self.pins["build"]["bytes"])

    def test_refuses_an_unreadable_or_changed_required_artifact(self):
        receipt = json.dumps(pair_receipt(self.pins)).encode("utf-8")
        for index in range(len(ROLES)):
            with self.subTest(role=ROLES[index]), patch.object(
                binding.files, "_bound",
                side_effect=[receipt] * index + [OSError("private-path-read-failure")],
            ) as read:
                with self.assertRaisesRegex(core.TargetRefused, "^binding$"):
                    binding.verify_artifacts(self.pins)
                self.assertEqual(read.call_count, index + 1)

    def test_exact_instrumentation_argument_vector_and_result(self):
        self.assertEqual((binding.APP, binding.TEST), (APP, TEST))
        self.assertEqual(binding.INSTRUMENTATIONS, ((KIND, CLASS, METHOD),))
        self.assertEqual(binding.instrumentation_argv(KIND), [
            "am", "instrument", "-w", "-r", "-e", "class", SELECTOR,
            TEST + "/androidx.test.runner.AndroidJUnitRunner",
        ])
        raw = runner_pass()
        self.assertEqual(binding.validate_result(KIND, raw), {
            "class": CLASS, "methods": [METHOD], "method_count": 1,
            "stdout_sha256": hashlib.sha256(raw).hexdigest(), "passed": True,
        })

    def test_refuses_nonallowlisted_kinds(self):
        class ForeignKind(str):
            pass

        for kind in (None, True, "", KIND + " ", "record_screen", SELECTOR, ForeignKind(KIND)):
            with self.subTest(kind=kind):
                with self.assertRaisesRegex(core.TargetRefused, "^capability$"):
                    binding.instrumentation_argv(kind)
                with self.assertRaisesRegex(core.TargetRefused, "^capability$"):
                    binding.validate_result(kind, runner_pass())

    def test_refuses_other_classes_methods_and_incomplete_or_failed_results(self):
        raw = runner_pass()
        for invalid in (
            raw.replace(CLASS.encode(), b"org.locallore.app.DifferentTest", 1),
            raw.replace(METHOD.encode(), b"differentMethod"),
            raw.replace(b"INSTRUMENTATION_STATUS_CODE: 0", b"INSTRUMENTATION_STATUS_CODE: -2"),
            raw.replace(b"numtests=1", b"numtests=2"),
            raw.split(b"INSTRUMENTATION_RESULT:", 1)[0],
        ):
            with self.subTest(invalid=invalid):
                with self.assertRaisesRegex(evidence.EvidenceRefused, "^instrumentation_refused$"):
                    binding.validate_result(KIND, invalid)
