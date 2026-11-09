"""Host-only checks for the exact two archive provider test capabilities."""
import copy
import hashlib
from io import BytesIO
import json
from pathlib import PureWindowsPath
import unittest
from unittest.mock import patch
from zipfile import BadZipFile

from benchmarks import android_instrumentation_evidence as evidence
from benchmarks import archive_provider_platform_binding as binding
from benchmarks import owned_target_contract as core
from scripts.tests.test_android_instrumentation_evidence import bundle, ending


APP = "org.locallore.app.archiveverify"
TEST = APP + ".test"
CLASS = "org.locallore.app.ArchiveProviderPlatformTest"
IMPORT = "cancelledReadOnlyOpenDrainsAndNextImportReadsExactlyTheAssetSlice"
EXPORT = "cancelledReadWriteOpenClosesTheLateDestinationAndNextExportWrites"
ROSTER = (("archive_import_open", CLASS, IMPORT), ("archive_export_open", CLASS, EXPORT))
DESCRIPTOR = b"Lorg/locallore/app/ArchiveProviderPlatformTest;"
PROVIDER = b"Lorg/locallore/app/ArchiveDocumentProvider;"
HEAD = "91de52b4e82fae062584713f84f61c47cdd76769"
ROOT = PureWindowsPath("D:/Dev/Experiments/LocalLore/2026-11-09-archive-provider-both-platform-v1")
OUTPUT = PureWindowsPath("D:/Worktrees/LocalLore-archive-provider-both-platform-v1/"
                         "apps/android/app/build-archive-verification/outputs/apk")
APP_BYTES = b"synthetic product APK"
TEST_BYTES = b"synthetic instrumentation APK"
METHODS = [(IMPORT.encode(), (b"V", 0), 17, True, 20),
           (EXPORT.encode(), (b"V", 0), 1, True, 18)]


def pin(filename, size, digest):
    return {"path": str(ROOT / filename), "bytes": size, "sha256": digest}


PINS = {
    "build": pin("verified-pair-91de52b4.json", 1373,
                 "fbd26daf7c7a111d1edd080c8cc5315bae6cde1872dbd0d0d74d35bbc0db08b2"),
    "product_apk": pin("app-debug.apk", 28161304,
                       "a0b92505aabae6fe2758e426a4ab1c9ffecf03c8ebd53a24aee40b80e6510350"),
    "test_apk": pin("app-debug-androidTest.apk", 2560246,
                    "bb10b70f8b374d6593a5b50b88d71a7f44667958c98f084a11ef8efb7710f17c"),
}


def build_report():
    apks = []
    for role, relative in (("product_apk", "debug/app-debug.apk"),
                           ("test_apk", "androidTest/debug/app-debug-androidTest.apk")):
        apks.append({"path": str(OUTPUT / relative), "bytes": PINS[role]["bytes"],
                     "sha256": PINS[role]["sha256"], "signature_verified": True})
    return {
        "source": HEAD,
        "app_id": APP,
        "test_id": TEST,
        "provider_process": ":archive_test_provider",
        "selectors": [klass + "#" + method for _, klass, method in ROSTER],
        "test_permissions": ["android.permission.REORDER_TASKS"],
        "apks": apks,
        "jvm": {"suites": 92, "tests": 724, "errors": 0, "failures": 0, "skipped": 0},
        "android_executed": False,
    }


class ArtifactFixture:
    def __init__(self):
        self.reads = []
        self.decodes = []
        self.files = {
            PINS["build"]["path"]: json.dumps(build_report()).encode(),
            PINS["product_apk"]["path"]: APP_BYTES,
            PINS["test_apk"]["path"]: TEST_BYTES,
        }
        self.classes = {
            APP_BYTES: {},
            TEST_BYTES: {DESCRIPTOR: (17, list(METHODS)), PROVIDER: (17, [])},
        }

    def read(self, record, *, cap):
        self.reads.append((record, cap))
        return self.files[record["path"]]

    def decode(self, stream, **kwargs):
        if not isinstance(stream, BytesIO):
            raise AssertionError("DEX must consume the already verified APK bytes")
        raw = stream.read()
        self.decodes.append((raw, kwargs))
        return self.classes[raw]

    def verify(self, pins=PINS):
        with (patch.object(binding.files, "_bound", side_effect=self.read),
              patch.object(binding, "dex_classes", side_effect=self.decode)):
            return binding.verify_artifacts(pins)


def runner_bytes(*methods):
    return ("".join(bundle(method, i, 1, cls=CLASS, count=len(methods))
                    + bundle(method, i, 0, cls=CLASS, count=len(methods))
                    for i, method in enumerate(methods, 1)) + ending(len(methods))).encode()


class ArchiveProviderPlatformBindingTests(unittest.TestCase):
    def assert_refused(self, fixture, pins=PINS):
        with self.assertRaisesRegex(core.TargetRefused, "^binding$"):
            fixture.verify(pins)

    def test_pin_map_is_exact_and_fresh(self):
        pins = binding.artifact_bindings()
        self.assertEqual(pins, PINS)
        pins["build"].clear()
        pins.pop("test_apk")
        self.assertEqual(binding.artifact_bindings(), PINS)

    def test_verified_apk_bytes_go_directly_to_dex_parser(self):
        fixture = ArtifactFixture()
        fixture.verify()
        self.assertCountEqual(fixture.reads, [(pin, pin["bytes"]) for pin in PINS.values()])
        self.assertCountEqual(fixture.decodes, [(APP_BYTES, {}), (TEST_BYTES, {"with_code": True})])

    def test_wrong_paths_hashes_types_or_roles_refuse_before_io(self):
        for role, key, replacement in (
            ("product_apk", "path", str(ROOT / "alias.apk")),
            ("build", "sha256", "0" * 64),
            ("test_apk", "bytes", 2560246.0),
            ("test_apk", "bytes", 2560247),
        ):
            pins = copy.deepcopy(PINS)
            pins[role][key] = replacement
            with self.subTest(role=role, key=key):
                fixture = ArtifactFixture()
                self.assert_refused(fixture, pins)
                self.assertEqual(fixture.reads, [])
        for pins in (None, {**PINS, "other": PINS["build"]},
                     {**PINS, "product_apk": PINS["test_apk"], "test_apk": PINS["product_apk"]}):
            with self.subTest(pins=pins):
                fixture = ArtifactFixture()
                self.assert_refused(fixture, pins)
                self.assertEqual(fixture.reads, [])

    def test_malformed_or_substituted_report_refuses_before_dex(self):
        reports = [b'{"source":', b'{"source":"one","source":"two"}']
        for changes in ({"source": "0" * 40}, {"selectors": [CLASS + "#" + IMPORT]},
                        {"android_executed": True}, {"android_executed": 0},
                        {"apks": list(reversed(build_report()["apks"]))}):
            reports.append(json.dumps({**build_report(), **changes}).encode())
        for raw in reports:
            with self.subTest(raw=raw):
                fixture = ArtifactFixture()
                fixture.files[PINS["build"]["path"]] = raw
                self.assert_refused(fixture)
                self.assertEqual(fixture.decodes, [])

    def test_missing_file_or_invalid_archive_refuses_with_fixed_reason(self):
        fixture = ArtifactFixture()
        with patch.object(fixture, "read", side_effect=OSError("private file detail")):
            self.assert_refused(fixture)
        with patch.object(fixture, "decode", side_effect=BadZipFile("private APK detail")):
            self.assert_refused(fixture)

    def test_fixture_and_test_class_must_both_be_isolated_to_test_apk(self):
        for descriptor in (PROVIDER, DESCRIPTOR):
            with self.subTest(descriptor=descriptor):
                leaked = ArtifactFixture()
                leaked.classes[APP_BYTES][descriptor] = (1, [])
                self.assert_refused(leaked)
                missing = ArtifactFixture()
                del missing.classes[TEST_BYTES][descriptor]
                self.assert_refused(missing)

    def test_exact_two_public_concrete_junit_methods_required(self):
        for flags, methods in (
            (0, METHODS),
            (0x401, METHODS),
            (1, METHODS[:1]),
            (1, [*METHODS, (b"foreign", (b"V", 0), 17, True, 12)]),
            (1, [*METHODS, (IMPORT.encode(), (b"V", 1), 1, False, 12)]),
            (1, [METHODS[0], (EXPORT.encode(), (b"V", 0), 1, False, 18)]),
            (1, [METHODS[0], (EXPORT.encode(), (b"V", 1), 1, True, 18)]),
            (1, [METHODS[0], (EXPORT.encode(), (b"V", 0), 9, True, 18)]),
            (1, [METHODS[0], (EXPORT.encode(), (b"V", 0), 1, True, 0)]),
        ):
            with self.subTest(flags=flags, methods=methods):
                fixture = ArtifactFixture()
                fixture.classes[TEST_BYTES][DESCRIPTOR] = (flags, methods)
                self.assert_refused(fixture)

    def test_allowed_labels_select_exactly_one_method_and_accept_its_result(self):
        self.assertEqual(binding.INSTRUMENTATIONS, ROSTER)
        for kind, klass, method in ROSTER:
            with self.subTest(kind=kind):
                self.assertEqual(binding.instrumentation_argv(kind), [
                    "am", "instrument", "-w", "-r", "-e", "class", klass + "#" + method,
                    TEST + "/androidx.test.runner.AndroidJUnitRunner",
                ])
                raw = runner_bytes(method)
                self.assertEqual(binding.validate_result(kind, raw), {
                    "class": klass, "methods": [method], "method_count": 1, "passed": True,
                    "stdout_sha256": hashlib.sha256(raw).hexdigest(),
                })

    def test_selector_text_unknown_labels_and_mismatched_evidence_refuse(self):
        for kind in (None, True, "", CLASS, CLASS + "#" + IMPORT, "archive_import_open,archive_export_open"):
            with self.subTest(kind=kind):
                with self.assertRaisesRegex(core.TargetRefused, "^capability$"):
                    binding.instrumentation_argv(kind)
                with self.assertRaisesRegex(core.TargetRefused, "^capability$"):
                    binding.validate_result(kind, runner_bytes(IMPORT))
        for kind, _, method in ROSTER:
            other = EXPORT if method == IMPORT else IMPORT
            for raw in (runner_bytes(other), runner_bytes(IMPORT, EXPORT),
                        runner_bytes(method)[:-1],
                        runner_bytes(method).replace(b"STATUS_CODE: 0", b"STATUS_CODE: -2")):
                with self.subTest(kind=kind, raw=raw):
                    with self.assertRaisesRegex(evidence.EvidenceRefused, "^instrumentation_refused$"):
                        binding.validate_result(kind, raw)
