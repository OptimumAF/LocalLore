"""Exercise the frozen saved-library APK binding with synthetic file and DEX evidence."""
import copy
import hashlib
import json
from io import BytesIO
from pathlib import PureWindowsPath
import unittest
from unittest.mock import patch
from zipfile import BadZipFile

from benchmarks import android_instrumentation_evidence as evidence
from benchmarks import owned_target_contract as core
from benchmarks import saved_library_status_binding as binding
from scripts.tests.test_android_instrumentation_evidence import bundle, ending


KIND = "library_status"
CLASS = "org.locallore.app.ui.SavedLibraryStatusScreenTest"
METHOD = "catalogAdviceTracksConfirmedLibraryState"
SELECTOR = CLASS + "#" + METHOD
DESCRIPTOR = ("L" + CLASS.replace(".", "/") + ";").encode()
APP = "org.locallore.app"
TEST = APP + ".test"
HEAD = "3d967b6332f342a57044383bf79c0d18a95a3074"
SIGNER = "17ed497138b20dc1657d54039802305cfe0e3b782c73feaad20359c954707564"
ROOT = PureWindowsPath("D:/Dev/Experiments/LocalLore/2026-11-09-saved-library-recovery-v1")
APP_BYTES = b"synthetic app bytes"
TEST_BYTES = b"synthetic test bytes"
METHOD_DEFINITION = (METHOD.encode(), (b"V", 0), 1, True)


def pin(filename, size, digest):
    return {"path": str(ROOT / filename), "bytes": size, "sha256": digest}


PINS = {
    "build": pin("host-evidence-3d967b63-v1.json", 737,
                 "e1167dd52882ee673e3170ed96526bb16afd0a388e4fa32935c62bd5674d37fc"),
    "product_apk": pin("app-debug.apk", 28012664,
                       "327bf8f7ee40610e23fa949b743d02d36cb02d78e1919ce2025136cbc3f8450d"),
    "test_apk": pin("app-debug-androidTest.apk", 2269058,
                    "3eb72b9fb1c0c22b37a52eb277122ab000cb59a8d59a64e7696eb8e863e71d24"),
}
AUDIT_PIN = pin("audit-pair-3d967b63-v1.log", 456,
                "246b4899be2a819106ee39c2fa21ce6b09ee6d66a4bedbea62e591bce9e2b16e")


def apk_record(role):
    return {key: PINS[role][key] for key in ("bytes", "sha256")}


def build_report():
    return {
        "head": HEAD,
        "baseline": {"tests": 5, "failures": 3, "errors": 0, "skipped": 0},
        "jvm": {"suites": 49, "tests": 422, "failures": 0, "errors": 0, "skipped": 0, "new_tests": 5},
        "lint": {"Warning": 1, "Hint": 1},
        "app": apk_record("product_apk"),
        "test": apk_record("test_apk"),
        "compose_selector": SELECTOR,
        "android_executed": False,
    }


def pair_report():
    return {
        "app": apk_record("product_apk"),
        "test": apk_record("test_apk"),
        "certificate_sha256": SIGNER,
        "package": APP,
        "status": "passed",
        "test_package": TEST,
        "test_permissions": ["android.permission.REORDER_TASKS"],
    }


class ArtifactFixture:
    def __init__(self):
        self.reads = []
        self.decodes = []
        self.files = {
            PINS["build"]["path"]: json.dumps(build_report()).encode(),
            AUDIT_PIN["path"]: json.dumps(pair_report()).encode(),
            PINS["product_apk"]["path"]: APP_BYTES,
            PINS["test_apk"]["path"]: TEST_BYTES,
        }
        self.classes = {APP_BYTES: {}, TEST_BYTES: {DESCRIPTOR: (1, [METHOD_DEFINITION])}}

    def read(self, record, *, cap):
        self.reads.append((record, cap))
        return self.files[record["path"]]

    def decode(self, stream):
        if not isinstance(stream, BytesIO):
            raise AssertionError("DEX parser must consume the already verified APK bytes")
        raw = stream.read()
        self.decodes.append(raw)
        return self.classes[raw]

    def verify(self, pins=PINS):
        with patch.object(binding.files, "_bound", side_effect=self.read), \
             patch.object(binding, "dex_classes", side_effect=self.decode):
            return binding.verify_artifacts(pins)


def runner_bytes():
    return (bundle(METHOD, 1, 1, cls=CLASS, count=1)
            + bundle(METHOD, 1, 0, cls=CLASS, count=1)
            + ending(1)).encode()


class SavedLibraryStatusBindingTests(unittest.TestCase):
    def assert_binding_refused(self, fixture, pins=PINS):
        with self.assertRaisesRegex(core.TargetRefused, "^binding$"):
            fixture.verify(pins)

    def test_pin_map_matches_frozen_artifacts_and_is_fresh(self):
        pins = binding.artifact_bindings()
        self.assertEqual(pins, PINS)
        pins["build"]["sha256"] = "0" * 64
        pins.pop("test_apk")
        self.assertEqual(binding.artifact_bindings(), PINS)

    def test_verified_bytes_go_directly_to_dex_parser(self):
        fixture = ArtifactFixture()
        fixture.verify()
        records = (PINS["build"], AUDIT_PIN, PINS["product_apk"], PINS["test_apk"])
        self.assertEqual(fixture.reads, [(record, record["bytes"]) for record in records])
        self.assertCountEqual(fixture.decodes, (APP_BYTES, TEST_BYTES))

    def test_replaced_roles_or_changed_file_pins_refuse_before_reading(self):
        extra = {**PINS, "spare": PINS["test_apk"]}
        swapped = {**PINS, "product_apk": PINS["test_apk"], "test_apk": PINS["product_apk"]}
        digest = copy.deepcopy(PINS)
        digest["build"]["sha256"] = "0" * 64
        size = copy.deepcopy(PINS)
        size["test_apk"]["bytes"] += 1
        alias = copy.deepcopy(PINS)
        alias["product_apk"]["path"] = str(ROOT / "renamed.apk")
        float_size = copy.deepcopy(PINS)
        float_size["test_apk"]["bytes"] = float(PINS["test_apk"]["bytes"])
        for pins in (None, extra, swapped, digest, size, alias, float_size):
            with self.subTest(pins=pins):
                fixture = ArtifactFixture()
                self.assert_binding_refused(fixture, pins)
                self.assertEqual(fixture.reads, [])
                self.assertEqual(fixture.decodes, [])

    def test_missing_bound_apk_refuses_without_exposing_path(self):
        fixture = ArtifactFixture()

        def read(record, *, cap):
            if record == PINS["test_apk"]:
                raise OSError("private-path-canary")
            return fixture.read(record, cap=cap)

        with patch.object(fixture, "read", side_effect=read):
            self.assert_binding_refused(fixture)

    def test_malformed_or_substituted_build_report_refuses(self):
        reports = (
            b'{"head":',
            b'{"head":"one","head":"two"}',
            json.dumps({**build_report(), "head": "0" * 40}).encode(),
            json.dumps({**build_report(), "compose_selector": CLASS + "#foreign"}).encode(),
            json.dumps({**build_report(), "android_executed": True}).encode(),
            json.dumps({**build_report(), "android_executed": 0}).encode(),
        )
        for raw in reports:
            with self.subTest(raw=raw):
                fixture = ArtifactFixture()
                fixture.files[PINS["build"]["path"]] = raw
                self.assert_binding_refused(fixture)
                self.assertEqual(fixture.decodes, [])

    def test_substituted_signer_package_permissions_or_audited_bytes_refuse(self):
        for changed in (
            {"certificate_sha256": "0" * 64},
            {"package": APP + ".wrong"},
            {"test_package": TEST + ".wrong"},
            {"test_permissions": ["android.permission.INTERNET"]},
            {"test": apk_record("product_apk")},
            {"status": "failed"},
        ):
            with self.subTest(changed=changed):
                fixture = ArtifactFixture()
                fixture.files[AUDIT_PIN["path"]] = json.dumps({**pair_report(), **changed}).encode()
                self.assert_binding_refused(fixture)
                self.assertEqual(fixture.decodes, [])

    def test_dex_requires_one_annotated_method_in_public_concrete_test_class(self):
        variants = (
            {},
            {DESCRIPTOR: (0, [METHOD_DEFINITION])},
            {DESCRIPTOR: (0x401, [METHOD_DEFINITION])},
            {DESCRIPTOR: (1, [(METHOD.encode(), (b"V", 0), 1, False)])},
            {DESCRIPTOR: (1, [(METHOD.encode(), (b"V", 1), 1, True)])},
            {DESCRIPTOR: (1, [(METHOD.encode(), (b"V", 0), 9, True)])},
            {DESCRIPTOR: (1, [(b"foreign", (b"V", 0), 1, True)])},
            {DESCRIPTOR: (1, [METHOD_DEFINITION, (b"extra", (b"V", 0), 1, True)])},
        )
        for classes in variants:
            with self.subTest(classes=classes):
                fixture = ArtifactFixture()
                fixture.classes[TEST_BYTES] = classes
                self.assert_binding_refused(fixture)

    def test_bad_zip_dex_evidence_refuses_without_exposing_details(self):
        fixture = ArtifactFixture()
        with patch.object(fixture, "decode", side_effect=BadZipFile("private-zip-canary")):
            self.assert_binding_refused(fixture)

    def test_test_class_in_app_refuses(self):
        fixture = ArtifactFixture()
        fixture.classes[APP_BYTES] = {DESCRIPTOR: (1, [])}
        self.assert_binding_refused(fixture)

    def test_exact_command_and_complete_single_test_result(self):
        self.assertEqual(binding.INSTRUMENTATIONS, ((KIND, CLASS, METHOD),))
        self.assertEqual(binding.instrumentation_argv(KIND), [
            "am", "instrument", "-w", "-r", "-e", "class", SELECTOR,
            TEST + "/androidx.test.runner.AndroidJUnitRunner",
        ])
        raw = runner_bytes()
        self.assertEqual(binding.validate_result(KIND, raw), {
            "class": CLASS, "methods": [METHOD], "method_count": 1,
            "stdout_sha256": hashlib.sha256(raw).hexdigest(), "passed": True,
        })

    def test_unknown_capability_and_wrong_runner_evidence_refuse(self):
        for kind in (None, "", SELECTOR, "another_profile", True):
            with self.subTest(kind=kind):
                with self.assertRaisesRegex(core.TargetRefused, "^capability$"):
                    binding.instrumentation_argv(kind)
                with self.assertRaisesRegex(core.TargetRefused, "^capability$"):
                    binding.validate_result(kind, runner_bytes())
        raw = runner_bytes()
        for invalid in (
            raw[:-1],
            raw.replace(CLASS.encode(), b"org.locallore.app.WrongTest", 1),
            raw.replace(METHOD.encode(), b"foreignMethod", 1),
            raw.replace(b"INSTRUMENTATION_STATUS_CODE: 0", b"INSTRUMENTATION_STATUS_CODE: -2"),
            raw + b"unexpected trailing content\n",
        ):
            with self.subTest(invalid=invalid):
                with self.assertRaisesRegex(evidence.EvidenceRefused, "^instrumentation_refused$"):
                    binding.validate_result(KIND, invalid)
