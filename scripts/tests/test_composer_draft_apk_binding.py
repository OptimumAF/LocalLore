"""Exercise the fixed composer draft APK and DEX proof on synthetic inputs.

Copyright 2026 LocalLore contributors. SPDX-License-Identifier: Apache-2.0
"""
import copy
from io import BytesIO
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import patch

from benchmarks import archive_ui_build as files
from benchmarks import composer_draft_apk_binding as binding
from scripts import audit_physical_model_apk as audit
from scripts.tests.test_audit_physical_model_apk import manifests
from benchmarks import receipt_avd_environment as env


METHODS = tuple(sorted((
    "exactKindAndTextRestoreAcrossSameScopeHeadsAndOnlyExplicitSendDispatches",
    "unresolvedAsyncAndRecoveryHideSavedPayloadUntilOnlyItsExactScopeReturns",
    "settledBranchAndStorySwitchesDiscardTheSingleDraftWithoutPerStoryResurrection",
    "retainedEditAndSendActionsCannotChangeOrSubmitTheNewScopeDraft",
    "disposedComposerActionsCannotEditAReopenedDraftForTheSameScope",
    "saveBoundUsesUtf8BytesAndDoesNotRelaxTheSmallerSendBound",
    "unsafeSavedPayloadIsOmittedWholeWithPersistentReentryNoticeAndOriginalKind",
    "sameRenderKindThenTextRetainsBothLatestFields",
    "sameRenderTextThenKindRetainsBothLatestFields",
    "retainedSendAfterSameRenderEditsSubmitsLatestScopedInputOnce",
    "retainedEnabledSendAfterSameRenderClearDoesNotSubmit",
)))
DESCRIPTOR = b"Lorg/locallore/app/PlayDraftRestorationTest;"
PRODUCT = b"synthetic composer app bytes"
TEST = b"synthetic composer test bytes"


def row(name, *, prototype=(b"V", 0), flags=17, annotated=True, units=5):
    return name.encode("ascii"), prototype, flags, annotated, units


class ComposerDraftDexTests(unittest.TestCase):
    def setUp(self):
        self.rows = [row(name) for name in reversed(METHODS)]
        self.classes = {PRODUCT: {}, TEST: {DESCRIPTOR: (17, self.rows)}}
        self.dex = self.enterContext(patch.object(binding, "dex_classes", side_effect=self.decode))

    def decode(self, stream, *, with_code=False):
        self.assertIsInstance(stream, BytesIO)
        raw = stream.read()
        if raw == TEST:
            self.assertIs(with_code, True)
        return self.classes[raw]

    def assert_refused(self):
        with self.assertRaisesRegex(files.BuildRefused, "^binding$"):
            binding._verify_dex(PRODUCT, TEST)

    def test_exact_annotated_roster_ignores_non_test_helpers_and_dex_order(self):
        self.rows.append(row("helper", flags=2, annotated=False))
        self.assertEqual(binding._verify_dex(PRODUCT, TEST), METHODS)
        self.assertEqual(self.dex.call_count, 2)

    def test_product_class_leak_or_missing_test_class_refuses(self):
        self.classes[PRODUCT][DESCRIPTOR] = (17, self.rows)
        self.assert_refused()
        self.classes[PRODUCT].clear()
        self.classes[TEST].clear()
        self.assert_refused()

    def test_missing_unexpected_duplicate_or_unannotated_test_refuses(self):
        for rows in (self.rows[:-1], [*self.rows, row("foreignMethod")], [*self.rows, self.rows[0]],
                     [*self.rows[:-1], row(METHODS[0], annotated=False)]):
            with self.subTest(rows=rows):
                self.classes[TEST][DESCRIPTOR] = (17, rows)
                self.assert_refused()

    def test_non_public_abstract_or_interface_class_refuses(self):
        for flags in (0, 0x201, 0x401):
            with self.subTest(flags=flags):
                self.classes[TEST][DESCRIPTOR] = (flags, self.rows)
                self.assert_refused()

    def test_invalid_test_method_signature_or_missing_code_refuses(self):
        for changes in (
            {"prototype": (b"I", 0)}, {"prototype": (b"V", 1)},
            {"flags": 2}, {"flags": 0x9}, {"flags": 0x101}, {"flags": 0x401},
            {"units": 0}, {"units": None}, {"units": True},
        ):
            with self.subTest(changes=changes):
                self.classes[TEST][DESCRIPTOR] = (17, [*self.rows[:-1], row(METHODS[0], **changes)])
                self.assert_refused()

class ComposerDraftArtifactTests(unittest.TestCase):
    def setUp(self):
        self.root = Path(self.enterContext(TemporaryDirectory(dir="D:/Dev/_Temp"))).resolve()
        self.build = self.root / "build.json"
        self.product = self.root / "app.apk"
        self.test = self.root / "test.apk"
        self.product.write_bytes(PRODUCT)
        self.test.write_bytes(TEST)
        self.pins = dict(product_apk=env.binding(self.product), test_apk=env.binding(self.test))
        self.report = binding._build_record(self.pins)
        self.build.write_bytes(env.encoded(self.report))
        self.pins["build"] = env.binding(self.build)
        self.enterContext(patch.object(binding, "artifact_bindings", side_effect=lambda: copy.deepcopy(self.pins)))
        self.dex = self.enterContext(patch.object(binding, "dex_classes", side_effect=self.decode))
        self.enterContext(patch("subprocess.Popen", side_effect=AssertionError("unexpected tool process")))
        self.enterContext(patch("socket.socket", side_effect=AssertionError("unexpected socket")))

    def decode(self, stream, *, with_code=False):
        self.assertIsInstance(stream, BytesIO)
        raw = stream.read()
        if raw == PRODUCT:
            return {}
        self.assertEqual(raw, TEST)
        self.assertIs(with_code, True)
        return {DESCRIPTOR: (17, [row(name) for name in METHODS])}

    def test_verified_apk_bytes_go_directly_to_dex_reader(self):
        self.assertEqual(binding.verify_artifacts(self.pins), METHODS)
        self.assertEqual(self.dex.call_count, 2)

    def test_missing_swapped_or_aliased_role_refuses_before_file_reads(self):
        swapped = dict(self.pins, product_apk=self.pins["test_apk"], test_apk=self.pins["product_apk"])
        alias = dict(self.pins, product_apk=dict(self.pins["product_apk"], path=str(self.root / "alias.apk")))
        missing = {key: pin for key, pin in self.pins.items() if key != "test_apk"}
        with patch.object(files, "_bound", side_effect=AssertionError("unexpected file read")) as read:
            for supplied in (swapped, alias, missing, dict(self.pins, extra=self.pins["build"])):
                with self.subTest(supplied=supplied), self.assertRaisesRegex(files.BuildRefused, "^binding$"):
                    binding.verify_artifacts(supplied)
        read.assert_not_called()
        self.dex.assert_not_called()

    def test_exact_metadata_shape_and_claims_refuse_even_when_bytes_are_pinned(self):
        candidates = (
            env.encoded(dict(self.report, source="f" * 40)),
            env.encoded(dict(self.report, android_executed=True)),
            env.encoded(dict(self.report, extra=True)),
            env.encoded(dict(self.report, selectors=self.report["selectors"][:-1])),
            b'{"version":1,"version":1}',
        )
        for candidate in candidates:
            with self.subTest(candidate=candidate):
                self.build.write_bytes(candidate)
                self.pins["build"] = env.binding(self.build)
                with self.assertRaisesRegex(files.BuildRefused, "^binding$"):
                    binding.verify_artifacts(self.pins)
        self.dex.assert_not_called()

    def test_changed_same_size_apk_refuses_before_dex_decoding(self):
        for path in (self.product, self.test):
            original = path.read_bytes()
            path.write_bytes(original.upper())
            try:
                with self.subTest(path=path), self.assertRaisesRegex(files.BuildRefused, "^binding$"):
                    binding.verify_artifacts(self.pins)
            finally:
                path.write_bytes(original)
        self.dex.assert_not_called()


class ComposerDraftManifestTests(unittest.TestCase):
    def test_exact_isolated_test_package_and_runner_target(self):
        app = "org.locallore.app.draftverify"
        badging, tree = (value.replace(audit.APP, app) for value in manifests()[2:4])
        self.assertEqual(audit.audit_test_manifest(badging, tree, app), ["android.permission.REORDER_TASKS"])
        foreign = tree.replace('="' + app + '"', '="org.locallore.app"')
        with self.assertRaisesRegex(audit.AuditError, "^Wrong manifest targetPackage$"):
            audit.audit_test_manifest(badging, foreign, app)
