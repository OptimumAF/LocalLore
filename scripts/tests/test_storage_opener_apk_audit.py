"""Synthetic tests for the opt-in isolated storage-opener APK audit.

Copyright 2026 LocalLore contributors. SPDX-License-Identifier: Apache-2.0
"""
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import patch

from scripts import audit_instrumentation_apk as audit
from scripts.tests.test_instrumentation_apk import ARCHIVE, captures


SELECTORS = [
    "org.locallore.app.ui.ArchiveOpenScopeScreenTest#retainedArchiveOpenerCannotBorrowAReplacementRenderedFrame",
    "org.locallore.app.ui.DeletionOpenScopeScreenTest#retainedDeletionOpenersCannotBorrowTheReplacementStoryOrTimeline",
]
RUNNER = "androidx.test.runner.AndroidJUnitRunner"


def descriptor(selector):
    return ("L" + selector.split("#", 1)[0].replace(".", "/") + ";").encode("ascii")


def method(selector, *, prototype=(b"V", 0), access=17, annotated=True, code=3):
    return selector.split("#", 1)[1].encode("ascii"), prototype, access, annotated, code


def definitions():
    return {descriptor(selector): (17, [method(selector)]) for selector in reversed(SELECTORS)}


class StorageOpenerSelectorTests(unittest.TestCase):
    def setUp(self):
        self.app = {}
        self.test = definitions()

    def verify(self):
        return audit.audit_storage_opener_selectors(self.app, self.test)

    def assert_refused(self):
        with self.assertRaises(audit.AuditError):
            self.verify()

    def test_exact_selector_order_ignores_unannotated_helpers(self):
        self.test[descriptor(SELECTORS[0])][1].append((b"helper", (b"I", 1), 2, False, 3))
        self.assertEqual(self.verify(), SELECTORS)

    def test_missing_test_class_or_product_leak_refuses_for_each_selector(self):
        for selector in SELECTORS:
            with self.subTest(selector=selector):
                name = descriptor(selector)
                self.app[name] = self.test[name]
                self.assert_refused()
                self.app.clear()
                removed = self.test.pop(name)
                try:
                    self.assert_refused()
                finally:
                    self.test[name] = removed

    def test_unannotated_expected_method_overload_or_extra_test_refuses(self):
        selector = SELECTORS[0]
        name = descriptor(selector)
        exact = method(selector)
        foreign = method(selector.split("#", 1)[0] + "#anotherMethod")
        for rows in (
            [], [method(selector, annotated=False)], [exact, exact], [exact, foreign],
            [exact, method(selector, prototype=(b"V", 1), annotated=False)],
        ):
            with self.subTest(rows=rows):
                self.test[name] = (17, rows)
                self.assert_refused()

    def test_non_public_interface_or_abstract_test_class_refuses(self):
        name = descriptor(SELECTORS[1])
        for flags in (0, 0x201, 0x401):
            with self.subTest(flags=flags):
                self.test[name] = (flags, [method(SELECTORS[1])])
                self.assert_refused()

    def test_non_executable_public_instance_void_no_arg_contract_refuses(self):
        selector = SELECTORS[1]
        name = descriptor(selector)
        for changes in (
            {"prototype": (b"I", 0)}, {"prototype": (b"V", 1)},
            {"access": 2}, {"access": 9}, {"access": 0x101}, {"access": 0x401},
            {"code": None}, {"code": 0}, {"code": True},
        ):
            with self.subTest(changes=changes):
                self.test[name] = (17, [method(selector, **changes)])
                self.assert_refused()


class StorageOpenerPairTests(unittest.TestCase):
    def test_selector_mode_requires_archive_profile_before_touching_apks(self):
        with patch.object(audit, "Path", side_effect=AssertionError("unexpected APK path access")) as path:
            for options in (
                {"storage_opener_selectors": True},
                {"storage_opener_selectors": True, "cold_navigation_verification": True},
                {"storage_opener_selectors": True, "presentation_process_verification": True},
                {"storage_opener_selectors": 1, "archive_verification": True},
            ):
                with self.subTest(options=options), self.assertRaises(audit.AuditError):
                    audit.audit_pair("app.apk", "test.apk", **options)
        path.assert_not_called()

    def test_archive_pair_opt_in_reports_runner_and_two_verified_selectors(self):
        temp = TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        root = Path(temp.name)
        app, test = root / "product.apk", root / "instrumentation.apk"
        app.write_bytes(b"synthetic product")
        test.write_bytes(b"synthetic instrumentation")
        app_badging, app_tree, test_badging, test_tree = captures(ARCHIVE)
        responses = [app_badging, test_badging, app_tree, test_tree]
        signer = "a" * 64

        def dex(path, *, with_code=False):
            if path == app:
                return {}
            self.assertEqual(path, test)
            self.assertIs(with_code, True)
            return definitions()

        with (patch.object(audit.base, "audit_zip"),
              patch.object(audit.base, "aapt2_path", return_value=root / "aapt2.exe"),
              patch.object(audit.runner, "java_executable", return_value=root / "java.exe"),
              patch.object(audit.physical, "tool", side_effect=responses * 2),
              patch.object(audit.physical, "certificate", return_value=signer),
              patch.object(audit.physical, "dex_classes", side_effect=dex) as parse,
              patch("subprocess.Popen", side_effect=AssertionError("unexpected tool process"))):
            result = audit.audit_pair(app, test, archive_verification=True, storage_opener_selectors=True)
            self.assertEqual(result["status"], "passed")
            self.assertEqual(result["package"], ARCHIVE)
            self.assertEqual(result["test_package"], ARCHIVE + ".test")
            self.assertEqual(result["scope"], "storage-opener-apk-pair-v1")
            self.assertEqual(result["runner"], RUNNER)
            self.assertEqual(result["selectors"], SELECTORS)
            self.assertEqual(parse.call_count, 2)
            parse.reset_mock()
            legacy = audit.audit_pair(app, test, archive_verification=True)
            self.assertFalse({"scope", "runner", "selectors"} & legacy.keys())
            parse.assert_not_called()

    def test_cli_passes_explicit_selector_opt_in_to_the_archive_pair_audit(self):
        app = Path("D:/Synthetic/product.apk")
        test = Path("D:/Synthetic/instrumentation.apk")
        with (patch.object(audit, "audit_pair", return_value={"status": "passed"}) as pair,
              patch("builtins.print")):
            result = audit.main([str(app), str(test), "--archive-verification", "--storage-opener-selectors"])
        self.assertEqual(result, 0)
        pair.assert_called_once_with(app, test, archive_verification=True, cold_navigation_verification=False,
                                     presentation_process_verification=False, storage_opener_selectors=True)
