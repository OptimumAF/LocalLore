"""Test the frozen cross-owner deletion APK pair and one-method result binding."""

from contextlib import redirect_stdout
import copy
import hashlib
from io import StringIO
import json
from pathlib import PureWindowsPath
import unittest
from unittest.mock import patch
from zipfile import BadZipFile

from benchmarks import android_instrumentation_evidence as evidence
from benchmarks import cross_owner_deletion_ui_binding as binding
from benchmarks import owned_target_contract as core
from scripts.tests.test_android_instrumentation_evidence import bundle, ending


APP = "org.locallore.app.storydelete"
TEST = APP + ".test"
RUNNER = "androidx.test.runner.AndroidJUnitRunner"
KIND = "cross_owner_deletion_recovery"
CLASS = "org.locallore.app.CrossOwnerDeletionRecoveryMainActivityTest"
METHOD = "recoversRetainedStoryAfterAnotherOwnerDeletesSelection"
SELECTOR = CLASS + "#" + METHOD
HEAD = "fdb8f622cdff0a4b1ee4e4d1e93d356995440544"
ROOT = PureWindowsPath("D:/Dev/Experiments/LocalLore/2026-11-09-cross-owner-deletion-ui-v1")
BUILD_ROOT = PureWindowsPath(
    "D:/Worktrees/LocalLore-cross-owner-deletion-ui-v1/apps/android/app/build-story-deletion/outputs/apk"
)
APP_BYTES = b"synthetic app bytes"
TEST_BYTES = b"synthetic test bytes"


def pin(filename, size, sha256):
    return {"path": str(ROOT / filename), "bytes": size, "sha256": sha256}


PINS = {
    "build": pin("publish-summary.json", 348,
                 "3d90f805d50303785f2ad4148c4469085f6c403fdca9b5ec9c4856f589779881"),
    "product_apk": pin("app-storydelete.apk", 28161292,
                       "7eb84420693759dd3a1c0b547a46fcfebeb6c4fdcbb15fe4c4c2e51ee50018db"),
    "test_apk": pin("test-storydelete.apk", 2555606,
                    "e5148a0bce6f24ec28cbbfd925d4175a3a4ce673b963ce9154f917cabd4424fa"),
}
AUDIT_PIN = pin("apk-audit.json", 1185,
                "f1889a3b037b9ebb49137d1dac0a48b75808d729256d0bd4f49f3735326f9fa1")


def build_report():
    return {
        "head": HEAD, "exit_code": 0, "suites": 90, "tests": 720.0,
        "failures": 0.0, "errors": 0.0, "skipped": 0.0,
        "lint": [
            {"id": "GradleDependency", "severity": "Warning"},
            {"id": "AutoboxingStateCreation", "severity": "Hint"},
        ],
    }


def pair_report():
    return {
        "head": HEAD, "app_package": APP, "test_package": TEST, "target_package": APP, "runner": RUNNER,
        "signer_sha256": "17ed497138b20dc1657d54039802305cfe0e3b782c73feaad20359c954707564",
        "abis": ["arm64-v8a", "x86_64"], "zip_alignment_verified": True,
        "selector": SELECTOR, "selector_in_test_only": True,
        "app": {**PINS["product_apk"], "path": str(BUILD_ROOT / "debug/app-debug.apk")},
        "test": {**PINS["test_apk"], "path": str(BUILD_ROOT / "androidTest/debug/app-debug-androidTest.apk")},
    }


def fixture_files():
    return {
        PINS["build"]["path"]: json.dumps(build_report()).encode(),
        AUDIT_PIN["path"]: json.dumps(pair_report()).encode(),
        PINS["product_apk"]["path"]: APP_BYTES,
        PINS["test_apk"]["path"]: TEST_BYTES,
    }


def runner_bytes():
    return (bundle(METHOD, 1, 1, cls=CLASS, count=1)
            + bundle(METHOD, 1, 0, cls=CLASS, count=1)
            + ending(1)).encode()


class CrossOwnerDeletionUiBindingTests(unittest.TestCase):
    def test_exact_artifact_pins_are_detached(self):
        pins = binding.artifact_bindings()
        self.assertEqual(pins, PINS)
        pins["product_apk"]["path"] = "unexpected.apk"
        pins.pop("test_apk")
        self.assertEqual(binding.artifact_bindings(), PINS)

    def test_substituted_roles_and_pins_refuse_before_any_read(self):
        swapped = {**PINS, "product_apk": PINS["test_apk"], "test_apk": PINS["product_apk"]}
        extra = {**PINS, "audit": AUDIT_PIN}
        changed = copy.deepcopy(PINS)
        changed["build"]["sha256"] = "0" * 64
        float_size = copy.deepcopy(PINS)
        float_size["test_apk"]["bytes"] = float(PINS["test_apk"]["bytes"])
        for pins in (None, swapped, extra, changed, float_size):
            with self.subTest(pins=pins), patch.object(binding, "_bound") as read:
                with self.assertRaisesRegex(core.TargetRefused, "^binding$"):
                    binding.verify_artifacts(pins)
                read.assert_not_called()

    def test_verified_artifacts_forward_the_bound_bytes_and_exact_method(self):
        files = fixture_files()
        with patch.object(binding, "_bound", side_effect=lambda pin: files[pin["path"]]) as read, \
             patch.object(binding, "_verify_dex") as dex:
            binding.verify_artifacts(copy.deepcopy(PINS))
        self.assertCountEqual([call.args[0] for call in read.call_args_list], [*PINS.values(), AUDIT_PIN])
        dex.assert_called_once_with(APP_BYTES, TEST_BYTES, CLASS, METHOD)

    def test_altered_build_or_pair_evidence_refuses_before_dex(self):
        variants = (
            (PINS["build"], b'{"head":"one","head":"two"}'),
            (PINS["build"], json.dumps({**build_report(), "exit_code": 1}).encode()),
            (AUDIT_PIN, json.dumps({**pair_report(), "target_package": "org.locallore.app"}).encode()),
            (AUDIT_PIN, json.dumps({**pair_report(), "selector_in_test_only": 1}).encode()),
            (AUDIT_PIN, json.dumps({**pair_report(), "test": pair_report()["app"]}).encode()),
        )
        for record, raw in variants:
            with self.subTest(path=record["path"], raw=raw):
                files = fixture_files()
                files[record["path"]] = raw
                with patch.object(binding, "_bound", side_effect=lambda pin: files[pin["path"]]), \
                     patch.object(binding, "_verify_dex") as dex:
                    with self.assertRaisesRegex(core.TargetRefused, "^binding$"):
                        binding.verify_artifacts(PINS)
                    dex.assert_not_called()

    def test_file_and_dex_errors_have_fixed_refusal_text(self):
        with patch.object(binding, "_bound", side_effect=OSError("private-path-canary")):
            with self.assertRaisesRegex(core.TargetRefused, "^binding$"):
                binding.verify_artifacts(PINS)
        files = fixture_files()
        with patch.object(binding, "_bound", side_effect=lambda pin: files[pin["path"]]), \
             patch.object(binding, "_verify_dex", side_effect=BadZipFile("private-zip-canary")):
            with self.assertRaisesRegex(core.TargetRefused, "^binding$"):
                binding.verify_artifacts(PINS)

    def test_exact_selector_and_complete_single_method_result(self):
        self.assertEqual((binding.APP, binding.TEST), (APP, TEST))
        self.assertEqual(binding.INSTRUMENTATIONS, ((KIND, CLASS, METHOD),))
        self.assertEqual(binding.instrumentation_argv(KIND), [
            "am", "instrument", "-w", "-r", "-e", "class", SELECTOR, TEST + "/" + RUNNER,
        ])
        raw = runner_bytes()
        self.assertEqual(binding.validate_result(KIND, raw), {
            "class": CLASS, "methods": [METHOD], "method_count": 1,
            "stdout_sha256": hashlib.sha256(raw).hexdigest(), "passed": True,
        })

    def test_wrong_kind_or_nonmatching_runner_output_refuses(self):
        raw = runner_bytes()
        for kind in (None, True, SELECTOR, "library_status"):
            with self.subTest(kind=kind):
                with self.assertRaisesRegex(core.TargetRefused, "^capability$"):
                    binding.instrumentation_argv(kind)
                with self.assertRaisesRegex(core.TargetRefused, "^capability$"):
                    binding.validate_result(kind, raw)
        for invalid in (
            raw[:-1],
            raw.replace(CLASS.encode(), b"org.locallore.app.ForeignTest", 1),
            raw.replace(METHOD.encode(), b"differentMethod", 1),
            raw.replace(b"INSTRUMENTATION_STATUS_CODE: 0", b"INSTRUMENTATION_STATUS_CODE: -2"),
        ):
            with self.subTest(raw=invalid):
                with self.assertRaisesRegex(evidence.EvidenceRefused, "^instrumentation_refused$"):
                    binding.validate_result(KIND, invalid)

    def test_read_only_report_binds_selector_and_refuses_arguments(self):
        with patch.object(binding, "verify_artifacts") as verify, redirect_stdout(StringIO()) as stdout:
            self.assertEqual(binding.main([]), 0)
        verify.assert_called_once_with(PINS)
        report = json.loads(stdout.getvalue())
        self.assertEqual(report["status"], "verified")
        self.assertIs(report["execution_authorized"], False)
        self.assertEqual(report["artifacts"], PINS)
        self.assertEqual(report["audit"], AUDIT_PIN)
        self.assertEqual(report["selector"], SELECTOR)
        self.assertEqual(report["instrumentation_argv"], binding.instrumentation_argv(KIND))

        with patch.object(binding, "verify_artifacts") as verify, redirect_stdout(StringIO()) as stdout:
            self.assertEqual(binding.main(["--execute"]), 1)
        verify.assert_not_called()
        self.assertEqual(json.loads(stdout.getvalue()), {
            "scope": "cross-owner-deletion-ui-binding-v1", "execution_authorized": False,
            "status": "refused", "reason": "schema",
        })
