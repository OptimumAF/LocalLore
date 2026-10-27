"""Artifact regressions with synthetic ZIP/ELF data, not a second Android build.

Copyright 2026 LocalLore contributors. SPDX-License-Identifier: Apache-2.0
"""
import importlib.util
import hashlib
from pathlib import Path
import struct
import tempfile
import unittest
from unittest.mock import patch
import warnings
import zipfile

SPEC = importlib.util.spec_from_file_location("audit_apk", Path(__file__).resolve().parents[1] / "audit_apk.py")
audit = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(audit)


def library(machine=62, alignment=16384):
    data = bytearray(120)
    data[:7] = b"\x7fELF\x02\x01\x01"
    struct.pack_into("<HH", data, 16, 3, machine)
    struct.pack_into("<Q", data, 32, 64)
    struct.pack_into("<HH", data, 54, 56, 1)
    struct.pack_into("<IIQQQQQQ", data, 64, 1, 5, 0, 0, 0, 120, 120, alignment)
    return data


BADGING = """package: name='org.locallore.app' versionCode='1'
minSdkVersion:'26'
targetSdkVersion:'36'
uses-permission: name='org.locallore.app.DYNAMIC_RECEIVER_NOT_EXPORTED_PERMISSION'
"""
TREE = """  E: manifest (line=2)
      E: permission (line=11)
        A: http://schemas.android.com/apk/res/android:name(0x01010003)="org.locallore.app.DYNAMIC_RECEIVER_NOT_EXPORTED_PERMISSION"
        A: http://schemas.android.com/apk/res/android:protectionLevel(0x01010009)=0x00000002
      E: uses-permission (line=15)
        A: http://schemas.android.com/apk/res/android:name(0x01010003)="org.locallore.app.DYNAMIC_RECEIVER_NOT_EXPORTED_PERMISSION"
"""


class ApkAuditTests(unittest.TestCase):
    def archive(self, directory, *, wrong_abi=False, unaligned=False, compressed=False,
                missing=False, duplicate=False, legacy=False):
        path = Path(directory) / "hero's build.apk"
        with zipfile.ZipFile(path, "w") as apk:
            apk.writestr("AndroidManifest.xml", b"synthetic binary manifest; aapt output tested separately")
            for abi, machine in (("x86_64", 62), ("arm64-v8a", 183)):
                for name in ("liblocallore_android.so", "libandroidx.graphics.path.so"):
                    if missing and abi == "arm64-v8a" and name == "liblocallore_android.so":
                        continue
                    entry = zipfile.ZipInfo(f"lib/{abi}/{name}")
                    if not unaligned:
                        # Align an independently generated ZIP local record to a full page.
                        offset = apk.fp.tell() + 30 + len(entry.filename.encode("utf-8"))
                        padding = (16384 - (offset + 4) % 16384) % 16384
                        entry.extra = struct.pack("<HH", 0xCAFE, padding) + bytes(padding)
                    entry.compress_type = zipfile.ZIP_DEFLATED if compressed else zipfile.ZIP_STORED
                    apk.writestr(entry, library(62 if wrong_abi else machine))
            if duplicate:
                with warnings.catch_warnings():
                    warnings.simplefilter("ignore", UserWarning)
                    apk.writestr("AndroidManifest.xml", b"shadowed manifest")
            if legacy:
                apk.writestr("assets/lantern_quay_cases.json", b"old recorded authority")
        return path

    def test_actual_contract_accepts_both_aligned_native_abis(self):
        with tempfile.TemporaryDirectory() as directory:
            result = audit.audit_zip(self.archive(directory))
            self.assertEqual(len(result), 4)
            self.assertTrue(all(item["elf_load_alignment"] == [16384] for item in result))

    def test_missing_engine_wrong_architecture_and_bad_zip_alignment_rejected(self):
        for option in ("missing", "wrong_abi", "unaligned", "compressed", "duplicate", "legacy"):
            with self.subTest(option=option), tempfile.TemporaryDirectory() as directory:
                with self.assertRaises(audit.AuditError):
                    audit.audit_zip(self.archive(directory, **{option: True}))

    def test_elf_rejects_small_alignment_and_truncated_out_of_bounds_headers(self):
        for data in (library(alignment=4096), library()[:90], bytes(120)):
            with self.subTest(data=data[:7]), self.assertRaises(audit.AuditError):
                audit.elf_alignments(data, 62)
        invalid = library()
        struct.pack_into("<Q", invalid, 64 + 32, 4096)  # LOAD bytes cannot exceed the file.
        with self.assertRaises(audit.AuditError):
            audit.elf_alignments(invalid, 62)

    def test_manifest_allows_only_current_app_owned_signature_permission(self):
        self.assertEqual(audit.audit_manifest(BADGING, TREE), [audit.PERMISSION])

    def test_actual_windows_aapt_crlf_preserves_exact_sdk_contract(self):
        self.assertEqual(audit.audit_manifest(BADGING.replace("\n", "\r\n"), TREE.replace("\n", "\r\n")), [audit.PERMISSION])
        for malformed in (BADGING.replace("\n", "\r"), BADGING.replace("\n", "\r\n", 1),
                          BADGING.replace("\n", "\v", 1), BADGING.replace("\n", "\f", 1),
                          BADGING.replace("\n", "\x85", 1), BADGING + "\0"):
            with self.subTest(malformed=repr(malformed)), self.assertRaises(audit.AuditError):
                audit.audit_manifest(malformed, TREE)

    def test_sdk_rows_cannot_be_duplicate_conflicting_malformed_or_truthy(self):
        for malformed in (BADGING + "minSdkVersion:'26'\n", BADGING + "minSdkVersion:'25'\n",
                          BADGING + "targetSdkVersion:'36'\n", BADGING + "targetSdkVersion:'37'\n",
                          BADGING + " minSdkVersion:'26'\n", BADGING + "minSdkVersion:26\n",
                          BADGING + "sdkVersion:'26'\n", BADGING.replace("minSdkVersion:'26'", "minSdkVersion:'026'"),
                          BADGING.replace("minSdkVersion:'26'", "minSdkVersion:'true'"),
                          BADGING.replace("targetSdkVersion:'36'", "targetSdkVersion:'35'"),
                          BADGING.replace("minSdkVersion:'26'\n", "")):
            with self.subTest(malformed=malformed), self.assertRaises(audit.AuditError):
                audit.audit_manifest(malformed, TREE)

    def test_aapt_normalization_is_closed_and_does_not_strip_controls(self):
        for malformed in (None, b"text", "A\rB", "A\r\nB\n", "A\nB\r\n", "A\u2028B", "A\u2029B", "A\x7fB"):
            with self.subTest(malformed=malformed), self.assertRaises(audit.AuditError):
                audit.aapt_text(malformed)
        self.assertEqual(audit.aapt_text("label='日本語'\r\n\tvalue\r\n"), "label='日本語'\n\tvalue\n")

    def test_capacity_package_requires_explicit_allowlist_and_own_permission(self):
        for package in ("org.locallore.app.capacity", "org.locallore.app.capacityrelief", "org.locallore.app.cancelack"):
            badging = BADGING.replace("org.locallore.app", package)
            tree = TREE.replace("org.locallore.app", package)
            with self.subTest(package=package):
                with self.assertRaises(audit.AuditError):
                    audit.audit_manifest(badging, tree)
                self.assertEqual(audit.audit_manifest(badging, tree, package),
                                 [package + ".DYNAMIC_RECEIVER_NOT_EXPORTED_PERMISSION"])
        for package, candidate_tree in (("arbitrary.app", tree), ("org.locallore.app.capacity", TREE)):
            with self.subTest(package=package), self.assertRaises(audit.AuditError):
                audit.audit_manifest(badging, candidate_tree, package)

    def test_external_verification_requires_exact_package_and_own_permission(self):
        package = "org.locallore.app.externalverify"
        badging = BADGING.replace("org.locallore.app", package)
        tree = TREE.replace("org.locallore.app", package)
        self.assertEqual(audit.audit_manifest(badging, tree, package),
                         [package + ".DYNAMIC_RECEIVER_NOT_EXPORTED_PERMISSION"])
        for candidate in (package + ".other", package + ".test", "org.locallore.app.external"):
            with self.subTest(package=candidate), self.assertRaises(audit.AuditError):
                audit.audit_manifest(badging.replace(package, candidate), tree, candidate)
        for candidate_badging, candidate_tree in (
                (badging, TREE),
                (badging + "uses-permission: name='android.permission.INTERNET'\n", tree),
                (badging, tree.replace("0x00000002", "0x00000000"))):
            with self.subTest(tree=candidate_tree), self.assertRaises(audit.AuditError):
                audit.audit_manifest(candidate_badging, candidate_tree, package)

    def test_input_draft_profile_keeps_package_permission_and_capability_boundary(self):
        package = "org.locallore.app.draftverify"
        badging = BADGING.replace("org.locallore.app", package)
        tree = TREE.replace("org.locallore.app", package)
        self.assertEqual(audit.audit_manifest(badging, tree, package),
                         [package + ".DYNAMIC_RECEIVER_NOT_EXPORTED_PERMISSION"])
        for candidate, candidate_badging, candidate_tree in (
                ("org.locallore.app", badging, tree),
                (package + ".other", badging.replace(package, package + ".other"), tree),
                (package, badging, TREE),
                (package, badging + "uses-permission: name='android.permission.INTERNET'\n", tree),
                (package, badging, tree.replace("0x00000002", "0x00000000"))):
            with self.subTest(candidate=candidate), self.assertRaises(audit.AuditError):
                audit.audit_manifest(candidate_badging, candidate_tree, candidate)

    def test_input_draft_cli_refuses_model_modes_before_reading_any_artifact(self):
        flags = ("--litert-verification", "--model-provisioning", "--model-picker-fixture",
                 "--model-volume-verification", "--model-receipt-verification")
        with patch.object(audit, "audit_zip", side_effect=AssertionError("artifact read")) as read, \
                patch("builtins.print"):
            for flag in flags:
                with self.subTest(flag=flag):
                    self.assertEqual(audit.main(["unread.apk", "--input-draft-verification", flag]), 1)
            read.assert_not_called()

    def test_model_setup_is_separate_from_existing_candidate_and_has_no_network(self):
        package = "org.locallore.app.modelverify"
        badging, tree = BADGING.replace("org.locallore.app", package), TREE.replace("org.locallore.app", package)
        self.assertEqual(audit.audit_manifest(badging, tree, package),
                         [package + ".DYNAMIC_RECEIVER_NOT_EXPORTED_PERMISSION"])
        for selected, manifest, metadata in (
                ("org.locallore.app.litertverify", badging, tree),
                (package, badging, TREE),
                (package, badging + "uses-permission: name='android.permission.INTERNET'\n", tree),
                (package + ".other", badging, tree)):
            with self.subTest(package=selected), self.assertRaises(audit.AuditError):
                audit.audit_manifest(manifest, metadata, selected)

    def test_model_setup_audit_requires_sdk_native_and_notice_mode(self):
        with patch("builtins.print"):
            self.assertEqual(audit.main(["not-read.apk", "--model-provisioning"]), 1)
            self.assertEqual(audit.main(["not-read.apk", "--model-picker-fixture"]), 1)
            self.assertEqual(audit.main(["not-read.apk", "--litert-verification", "--model-picker-fixture"]), 1)

    def test_removable_profile_has_exact_package_and_no_storage_permissions(self):
        package = "org.locallore.app.modelvolumeverify"
        badging = BADGING.replace("org.locallore.app", package)
        tree = TREE.replace("org.locallore.app", package)
        self.assertEqual(audit.audit_manifest(badging, tree, package),
                         [package + ".DYNAMIC_RECEIVER_NOT_EXPORTED_PERMISSION"])
        for permission in ("android.permission.MANAGE_EXTERNAL_STORAGE",
                           "android.permission.READ_EXTERNAL_STORAGE", "android.permission.INTERNET"):
            with self.subTest(permission=permission), self.assertRaises(audit.AuditError):
                audit.audit_manifest(badging + "uses-permission: name='" + permission + "'\n", tree, package)
        with patch("builtins.print"):
            self.assertEqual(audit.main(["not-read.apk", "--model-volume-verification"]), 1)
            self.assertEqual(audit.main(["not-read.apk", "--litert-verification", "--model-provisioning",
                                         "--model-volume-verification", "--model-picker-fixture"]), 1)

    def test_model_picker_fixture_requires_explicit_mode_and_excludes_provider_from_app(self):
        with tempfile.TemporaryDirectory() as directory:
            path = self.archive(directory)
            with zipfile.ZipFile(path, "a") as apk:
                apk.writestr("classes.dex", b"original synthetic helper-only marker ModelPickerFixture")
            with self.assertRaises(audit.AuditError):
                audit.audit_zip(path)
        with tempfile.TemporaryDirectory() as directory:
            path, hashes, notices = self.candidate_archive(directory)
            with zipfile.ZipFile(path, "a") as apk:
                apk.writestr("classes.dex", b"original synthetic DEX markers ModelPickerFixtureActivity ModelPickerInterruptionFixtureActivity ModelPickerPendingFixtureActivity ModelSetupRecoveryFixtureActivity")
            with patch.dict(audit.LITERT_NATIVE_HASHES, hashes, clear=True), patch.dict(audit.LITERT_NOTICES, notices, clear=True):
                self.assertEqual(len(audit.audit_zip(path, litert=True, model_picker=True)), 6)
                with self.assertRaises(audit.AuditError):
                    audit.audit_zip(path, litert=True)
                with zipfile.ZipFile(path, "a") as apk:
                    apk.writestr("classes10.dex", b"original synthetic marker ModelPickerDocumentsProvider")
                with self.assertRaises(audit.AuditError):
                    audit.audit_zip(path, litert=True, model_picker=True)

    def test_interruption_helpers_cannot_leak_or_replace_the_private_activity(self):
        for marker in (b"ModelPickerInterruption", b"ModelPickerInterruptionFixtureActivity"):
            with self.subTest(marker=marker), tempfile.TemporaryDirectory() as directory:
                path = self.archive(directory)
                with zipfile.ZipFile(path, "a") as apk:
                    apk.writestr("classes.dex", marker)
                with self.assertRaises(audit.AuditError):
                    audit.audit_zip(path)
        for marker in (b"ModelPickerFixtureActivity", b"ModelPickerFixtureActivity ModelPickerInterruption",
                       b"ModelPickerFixtureActivity ModelPickerInterruptionFixtureActivity ModelPickerInterruptionTest"):
            with self.subTest(marker=marker), tempfile.TemporaryDirectory() as directory:
                path, hashes, notices = self.candidate_archive(directory)
                with zipfile.ZipFile(path, "a") as apk:
                    apk.writestr("classes.dex", b"ModelPickerPendingFixtureActivity ModelSetupRecoveryFixtureActivity " + marker)
                with patch.dict(audit.LITERT_NATIVE_HASHES, hashes, clear=True), patch.dict(audit.LITERT_NOTICES, notices, clear=True):
                    with self.assertRaises(audit.AuditError):
                        audit.audit_zip(path, litert=True, model_picker=True)

    def test_pending_picker_helpers_require_the_private_implementation_and_test_exclusion(self):
        base = b"ModelPickerFixtureActivity ModelPickerInterruptionFixtureActivity ModelSetupRecoveryFixtureActivity "
        for marker in (b"ModelPickerPending", b"ModelPickerPendingFixtureActivity"):
            with self.subTest(marker=marker), tempfile.TemporaryDirectory() as directory:
                path = self.archive(directory)
                with zipfile.ZipFile(path, "a") as apk:
                    apk.writestr("classes.dex", marker)
                with self.assertRaises(audit.AuditError):
                    audit.audit_zip(path)
        for marker in (b"", b"ModelPickerPending", b"ModelPickerPendingFixtureActivity ModelPickerPendingTest"):
            with self.subTest(marker=marker), tempfile.TemporaryDirectory() as directory:
                path, hashes, notices = self.candidate_archive(directory)
                with zipfile.ZipFile(path, "a") as apk:
                    apk.writestr("classes.dex", base + marker)
                with patch.dict(audit.LITERT_NATIVE_HASHES, hashes, clear=True), patch.dict(audit.LITERT_NOTICES, notices, clear=True):
                    with self.assertRaises(audit.AuditError):
                        audit.audit_zip(path, litert=True, model_picker=True)

    def test_setup_recovery_helpers_require_explicit_private_implementation_and_test_exclusion(self):
        base = b"ModelPickerFixtureActivity ModelPickerInterruptionFixtureActivity ModelPickerPendingFixtureActivity "
        for marker in (b"ModelSetupRecovery", b"ModelSetupRecoveryFixtureActivity"):
            with self.subTest(marker=marker), tempfile.TemporaryDirectory() as directory:
                path, hashes, notices = self.candidate_archive(directory)
                with zipfile.ZipFile(path, "a") as apk:
                    apk.writestr("classes.dex", marker)
                with patch.dict(audit.LITERT_NATIVE_HASHES, hashes, clear=True), patch.dict(audit.LITERT_NOTICES, notices, clear=True):
                    for litert in (False, True):
                        with self.subTest(litert=litert), self.assertRaises(audit.AuditError):
                            audit.audit_zip(path, litert=litert)
        for marker in (b"", b"ModelSetupRecovery", b"ModelSetupRecoveryFixtureActivity ModelSetupRecoveryTest"):
            with self.subTest(marker=marker), tempfile.TemporaryDirectory() as directory:
                path, hashes, notices = self.candidate_archive(directory)
                with zipfile.ZipFile(path, "a") as apk:
                    apk.writestr("classes.dex", base + marker)
                with patch.dict(audit.LITERT_NATIVE_HASHES, hashes, clear=True), patch.dict(audit.LITERT_NOTICES, notices, clear=True):
                    with self.assertRaises(audit.AuditError):
                        audit.audit_zip(path, litert=True, model_picker=True)

    def test_receipt_service_requires_private_same_uid_process_in_volume_only(self):
        service = ('    E: service (line=1)\n'
                   '      A: android:name(1)="org.locallore.app.ReceiptProofService"\n'
                   '      A: android:exported(2)=false\n'
                   '      A: android:process(3)=":receiptproof"\n'
                   '      A: android:isolatedProcess(4)=false\n')
        self.assertEqual(audit.audit_receipt_service(service, model_volume=True),
                         {"receipt_service": True, "exported": False})
        self.assertFalse(audit.audit_receipt_service("")["receipt_service"])
        for malformed in ("", service.replace("exported(2)=false", "exported(2)=true"),
                          service.replace(":receiptproof", ":other"),
                          service.replace("isolatedProcess(4)=false", "isolatedProcess(4)=true"),
                          service.replace('      A: android:isolatedProcess(4)=false\n', ""),
                          service + '      E: intent-filter (line=2)\n',
                          service + '      A: android:permission(5)="custom.permission"\n',
                          service + service,
                          service.replace("ReceiptProofService", "UnexpectedService")):
            with self.subTest(malformed=malformed), self.assertRaises(audit.AuditError):
                audit.audit_receipt_service(malformed, model_volume=True)
        with self.assertRaises(audit.AuditError):
            audit.audit_receipt_service(service)

    def test_receipt_implementation_cannot_leak_into_ordinary_or_regular_sdk_apk(self):
        for marker in (b"ReceiptProofService", b"ReceiptAndroidFixture", b"ReceiptVolumeQualificationTest"):
            with self.subTest(marker=marker), tempfile.TemporaryDirectory() as directory:
                path = self.archive(directory)
                with zipfile.ZipFile(path, "a") as apk:
                    apk.writestr("classes.dex", marker)
                with self.assertRaises(audit.AuditError):
                    audit.audit_zip(path)
            with self.subTest(sdk=marker), tempfile.TemporaryDirectory() as directory:
                path, hashes, notices = self.candidate_archive(directory)
                with zipfile.ZipFile(path, "a") as apk:
                    apk.writestr("classes.dex", marker)
                with patch.dict(audit.LITERT_NATIVE_HASHES, hashes, clear=True), patch.dict(audit.LITERT_NOTICES, notices, clear=True):
                    with self.assertRaises(audit.AuditError):
                        audit.audit_zip(path, litert=True)

    def test_volume_receipt_apk_requires_both_implementations_and_excludes_test_class(self):
        both = b"ReceiptProofService ReceiptAndroidFixture"
        for marker in (b"", b"ReceiptProofService", b"ReceiptAndroidFixture",
                       both + b" ReceiptVolumeQualificationTest", both):
            with self.subTest(marker=marker), tempfile.TemporaryDirectory() as directory:
                path, hashes, notices = self.candidate_archive(directory)
                with zipfile.ZipFile(path, "a") as apk:
                    apk.writestr("classes.dex", marker)
                with patch.dict(audit.LITERT_NATIVE_HASHES, hashes, clear=True), patch.dict(audit.LITERT_NOTICES, notices, clear=True):
                    if marker == both:
                        self.assertEqual(len(audit.audit_zip(path, litert=True, model_volume=True)), 6)
                    else:
                        with self.assertRaises(audit.AuditError):
                            audit.audit_zip(path, litert=True, model_volume=True)
        with tempfile.TemporaryDirectory() as directory:
            with self.assertRaises(audit.AuditError):
                audit.audit_zip(self.archive(directory), model_volume=True)
            with self.assertRaises(audit.AuditError):
                audit.audit_zip(self.archive(directory), litert=True, model_volume=True, model_picker=True)

    def test_receipt_setup_classes_require_explicit_profile_and_cannot_include_tests(self):
        volume = b"ReceiptProofService ReceiptAndroidFixture "
        names = audit.RECEIPT_SETUP_CLASSES
        complete = " ".join(names).encode("ascii")
        variants = [complete, b"", *(complete.replace(name.encode("ascii"), b"") for name in names),
                    complete + b" ReceiptSetupQualificationTest", complete + b" ReceiptSetupRestartTest",
                    complete + b" ReceiptSetupFailureTraceTest", complete + b" ReceiptSetupFailureTransportTest",
                    complete + b" ReceiptRealSourcePreflightTest",
                    *(complete + b" " + name for name in (
                        b"ReceiptComposeCancellationTest", b"ReceiptComposeCancelTest", b"ReceiptComposeRecoverTest",
                        b"ReceiptComposeReopenTest", b"ComposeCancellationProofTest", b"ReceiptOrdinaryRouteTest",
                        b"ReceiptOrdinaryStartTest", b"ReceiptOrdinaryDialogueTest", b"ReceiptOrdinaryReopenTest",
                        b"OrdinaryRouteProofTest", b"LiteRtSendTraceTest"))]
        for marker in variants:
            with self.subTest(marker=marker), tempfile.TemporaryDirectory() as directory:
                path, hashes, notices = self.candidate_archive(directory)
                with zipfile.ZipFile(path, "a") as apk:
                    apk.writestr("classes.dex", volume + marker)
                with patch.dict(audit.LITERT_NATIVE_HASHES, hashes, clear=True), patch.dict(audit.LITERT_NOTICES, notices, clear=True):
                    if marker == complete:
                        self.assertEqual(len(audit.audit_zip(path, litert=True, model_volume=True, model_receipt=True)), 6)
                    else:
                        with self.assertRaises(audit.AuditError):
                            audit.audit_zip(path, litert=True, model_volume=True, model_receipt=True)
                    if marker:
                        with self.assertRaises(audit.AuditError):
                            audit.audit_zip(path, litert=True, model_volume=True)
                    with self.assertRaises(audit.AuditError):
                        audit.audit_zip(path, litert=True, model_receipt=True)

    def test_receipt_setup_cli_refuses_incomplete_profiles_before_any_tool_call(self):
        for flags in (["--model-receipt-verification"],
                      ["--litert-verification", "--model-provisioning", "--model-receipt-verification"],
                      ["--litert-verification", "--model-provisioning", "--model-receipt-verification",
                       "--model-volume-verification", "--model-picker-fixture"]):
            with self.subTest(flags=flags), patch.object(audit, "aapt2_path") as tool, patch.object(audit, "audit_zip") as archive:
                self.assertEqual(audit.main(["absent.apk", *flags]), 1)
                tool.assert_not_called()
                archive.assert_not_called()

    def test_receipt_setup_activities_are_complete_private_and_have_no_extra_authority(self):
        setup = "org.locallore.app.LocalModelSetupActivity"
        def activity(name, exported="false", extra="", children=""):
            return (f'    E: activity (line=1)\n'
                    f'      A: android:name(1)="{name}"\n'
                    f'      A: android:exported(2)={exported}\n' + extra + children)
        launcher = activity(setup, "true", '      A: android:launchMode(3)=0x2\n',
                            '      E: intent-filter (line=2)\n'
                            '        E: category (line=3)\n'
                            '          A: android:name(1)="android.intent.category.LAUNCHER"\n')
        ordinary = launcher + activity("org.locallore.app.LiteRtPlayActivity", extra='      A: android:launchMode(3)=0x2\n') + activity("org.locallore.app.MainActivity")
        names = ["org.locallore.app." + name for name in audit.RECEIPT_SETUP_ACTIVITIES]
        fixtures = "".join(activity(name) for name in names)
        badging = f"launchable-activity: name='{setup}' label='LocalLore'\n"
        self.assertEqual(audit.audit_model_launcher(badging, ordinary + fixtures, model_receipt=True)["launcher"], setup)
        with self.assertRaises(audit.AuditError):
            audit.audit_model_launcher(badging, ordinary + fixtures)
        with self.assertRaises(audit.AuditError):
            audit.audit_model_launcher(badging, ordinary + fixtures, model_receipt=True, model_picker=True)
        for name in names:
            replacements = ["", activity(name, "true"), activity(name, children='      E: intent-filter (line=2)\n'),
                            activity(name, extra='      A: android:process(3)=":other"\n'),
                            activity(name, extra='      A: android:permission(3)="foreign"\n'),
                            activity(name, extra='      A: android:taskAffinity(3)="other"\n'),
                            activity(name, extra='      A: android:launchMode(3)=0x2\n')]
            for replacement in replacements:
                with self.subTest(name=name, replacement=replacement), self.assertRaises(audit.AuditError):
                    audit.audit_model_launcher(badging, ordinary + fixtures.replace(activity(name), replacement), model_receipt=True)

    def test_model_picker_document_provider_retains_platform_grants_and_exact_control_boundary(self):
        document = "org.locallore.app.ModelPickerDocumentsProvider"
        authority = "org.locallore.app.modelpickerverify.test.modelpicker"
        def provider(name, selected, extra="", children=""):
            return (f'    E: provider (line=1)\n'
                    f'      A: android:name(1)="{name}"\n'
                    f'      A: android:authorities(2)="{selected}"\n'
                    f'      A: android:process(3)=":model_picker_provider"\n'
                    f'      A: android:exported(4)=true\n' + extra + children)
        protection = ('      A: android:permission(5)="android.permission.MANAGE_DOCUMENTS"\n'
                      '      A: android:grantUriPermissions(6)=true\n')
        discovery = ('      E: intent-filter (line=2)\n'
                     '        E: action (line=3)\n'
                     '          A: android:name(1)="android.content.action.DOCUMENTS_PROVIDER"\n')
        doc = provider(document, authority, protection, discovery)
        ctrl = provider(document + "$Control", authority + ".control")
        tree = doc + ctrl
        self.assertEqual(audit.audit_model_picker_test_manifest(tree)["document_authority"], authority)
        variants = [doc, ctrl, tree + ctrl,
                    tree.replace("MANAGE_DOCUMENTS", "INTERNET"),
                    tree.replace('grantUriPermissions(6)=true', 'grantUriPermissions(6)=false'),
                    tree.replace(':model_picker_provider', ':other'),
                    tree.replace('android:exported(4)=true', 'android:exported(4)=false'),
                    tree.replace(ctrl, provider(document + "$Control", authority + ".wrong")),
                    tree.replace(ctrl, provider(document + "$Control", authority + ".control", protection)),
                    tree.replace(protection, protection + '      A: android:readPermission(7)=""\n'),
                    tree + provider("org.locallore.app.ExtraProvider", authority + ".extra")]
        for candidate in variants:
            with self.subTest(tree=candidate), self.assertRaises(audit.AuditError):
                audit.audit_model_picker_test_manifest(candidate)

    def test_model_launcher_rejects_scripted_export_and_stale_or_extra_entry_points(self):
        setup = "org.locallore.app.LocalModelSetupActivity"
        play = "org.locallore.app.LiteRtPlayActivity"
        main = "org.locallore.app.MainActivity"
        def activity(name, exported, mode="", extra=""):
            return (f'    E: activity (line=1)\n'
                    f'      A: android:name(1)="{name}"\n'
                    f'      A: android:exported(2)={exported}\n' +
                    (f'      A: android:launchMode(3)={mode}\n' if mode else "") + extra)
        filter_text = ('      E: intent-filter (line=2)\n'
                       '        E: category (line=3)\n'
                       '          A: android:name(1)="android.intent.category.LAUNCHER"\n')
        tree = activity(setup, "true", "0x2", filter_text) + activity(play, "false", "0x2") + activity(main, "false")
        badging = f"launchable-activity: name='{setup}' label='LocalLore'\n"
        self.assertEqual(audit.audit_model_launcher(badging, tree)["launcher"], setup)
        self.assertEqual(audit.audit_model_launcher(badging, tree.replace("=0x2", "=2"))["launcher"], setup)
        variants = [
            (badging.replace(setup, main), tree),
            (badging + badging, tree),
            (badging, tree.replace(activity(main, "false"), activity(main, "true"))),
            (badging, tree.replace(activity(play, "false", "0x2"), activity(play, "true", "0x2"))),
            (badging, tree.replace("launchMode(3)=0x2", "launchMode(3)=0x0")),
            (badging, tree.replace("launchMode(3)=0x2", "launchMode(3)=3")),
            (badging, tree + activity(main + "Other", "true")),
            (badging, tree + "    E: activity-alias (line=1)\n"),
            (badging, tree.replace(activity(main, "false"), activity(main, "false", extra=filter_text))),
        ]
        for candidate_badging, candidate_tree in variants:
            with self.subTest(tree=candidate_tree), self.assertRaises(audit.AuditError):
                audit.audit_model_launcher(candidate_badging, candidate_tree)

        fixture = "org.locallore.app.ModelPickerFixtureActivity"
        interruption = "org.locallore.app.ModelPickerInterruptionFixtureActivity"
        pending = "org.locallore.app.ModelPickerPendingFixtureActivity"
        recovery = "org.locallore.app.ModelSetupRecoveryFixtureActivity"
        fixture_tree = (tree + activity(fixture, "false") + activity(interruption, "false") +
                        activity(pending, "false") + activity(recovery, "false"))
        self.assertEqual(audit.audit_model_launcher(badging, fixture_tree, model_picker=True)["launcher"], setup)
        for candidate in (tree, fixture_tree.replace(activity(fixture, "false"), activity(fixture, "true")),
                          fixture_tree.replace(activity(fixture, "false"), activity(fixture, "false", extra=filter_text)),
                          fixture_tree.replace(activity(interruption, "false"), ""),
                          fixture_tree.replace(activity(interruption, "false"), activity(interruption, "true")),
                          fixture_tree.replace(activity(interruption, "false"), activity(interruption, "false", extra=filter_text)),
                          fixture_tree + activity(interruption + "Other", "false"),
                          fixture_tree.replace(activity(pending, "false"), ""),
                          fixture_tree.replace(activity(pending, "false"), activity(pending, "true")),
                          fixture_tree.replace(activity(pending, "false"), activity(pending, "false", extra=filter_text)),
                          fixture_tree + activity(pending + "Other", "false"),
                          fixture_tree.replace(activity(recovery, "false"), ""),
                          fixture_tree.replace(activity(recovery, "false"), activity(recovery, "true")),
                          fixture_tree.replace(activity(recovery, "false"), activity(recovery, "false", extra=filter_text)),
                          fixture_tree + activity(recovery + "Other", "false")):
            with self.subTest(tree=candidate), self.assertRaises(audit.AuditError):
                audit.audit_model_launcher(badging, candidate, model_picker=True)
        with self.assertRaises(audit.AuditError):
            audit.audit_model_launcher(badging, fixture_tree)

    def candidate_archive(self, directory, *, omitted=None, altered=None):
        path = self.archive(directory)
        hashes = {}
        with zipfile.ZipFile(path, "a") as apk:
            for abi, machine in (("x86_64", 62), ("arm64-v8a", 183)):
                name = f"lib/{abi}/liblitertlm_jni.so"
                data = library(machine)
                hashes[name] = hashlib.sha256(data).hexdigest()
                if name == omitted:
                    continue
                entry = zipfile.ZipInfo(name)
                offset = apk.fp.tell() + 30 + len(name.encode("utf-8"))
                padding = (16384 - (offset + 4) % 16384) % 16384
                entry.extra = struct.pack("<HH", 0xCAFE, padding) + bytes(padding)
                apk.writestr(entry, data if name != altered else library(machine, 4096))
            notices = {}
            for name in audit.LITERT_NOTICES:
                data = b"synthetic notice: " + name.encode("ascii")
                notices[name] = hashlib.sha256(data).hexdigest()
                if name != omitted:
                    apk.writestr(name, data if name != altered else b"changed")
        return path, hashes, notices

    def test_litert_candidate_requires_explicit_native_and_notice_contract(self):
        with tempfile.TemporaryDirectory() as directory:
            path, hashes, notices = self.candidate_archive(directory)
            with patch.dict(audit.LITERT_NATIVE_HASHES, hashes, clear=True), patch.dict(audit.LITERT_NOTICES, notices, clear=True):
                self.assertEqual(len(audit.audit_zip(path, litert=True)), 6)
                with self.assertRaises(audit.AuditError):
                    audit.audit_zip(path)

    def test_litert_missing_or_modified_binary_and_notices_fail_closed(self):
        for name in (*audit.LITERT_NATIVE_HASHES, *audit.LITERT_NOTICES):
            for option in ("omitted", "altered"):
                with self.subTest(name=name, option=option), tempfile.TemporaryDirectory() as directory:
                    path, hashes, notices = self.candidate_archive(directory, **{option: name})
                    with patch.dict(audit.LITERT_NATIVE_HASHES, hashes, clear=True), patch.dict(audit.LITERT_NOTICES, notices, clear=True):
                        with self.assertRaises(audit.AuditError):
                            audit.audit_zip(path, litert=True)
        with tempfile.TemporaryDirectory() as directory, self.assertRaises(audit.AuditError):
            audit.audit_zip(self.archive(directory), litert=True)

    def test_litert_identity_does_not_relax_permission_or_package_boundaries(self):
        package = "org.locallore.app.litertverify"
        badging, tree = BADGING.replace("org.locallore.app", package), TREE.replace("org.locallore.app", package)
        self.assertEqual(audit.audit_manifest(badging, tree, package), [package + ".DYNAMIC_RECEIVER_NOT_EXPORTED_PERMISSION"])
        for name, candidate, metadata in ((package, badging + "uses-permission: name='android.permission.INTERNET'\n", tree),
                                         (package, badging, TREE),
                                         (package + ".other", badging, tree)):
            with self.subTest(name=name), self.assertRaises(audit.AuditError):
                audit.audit_manifest(candidate, metadata, name)

    def test_manifest_rejects_extra_capabilities_or_weakened_permission(self):
        cases = [
            (BADGING + "uses-permission: name='android.permission.INTERNET'\n", TREE),
            (BADGING + "uses-permission-sdk-23: name='android.permission.READ_CONTACTS'\n", TREE),
            (BADGING.replace("minSdkVersion:'26'", "minSdkVersion:'23'"), TREE),
            (BADGING.replace("org.locallore.app'", "org.other.app'"), TREE),
            (BADGING, TREE.replace("0x00000002", "0x00000000")),
            (BADGING, TREE.replace("E: permission (", "E: permission-tree (")),
            (BADGING, TREE + TREE),
        ]
        for badging, tree in cases:
            with self.subTest(badging=badging, tree=tree), self.assertRaises(audit.AuditError):
                audit.audit_manifest(badging, tree)


if __name__ == "__main__":
    unittest.main()
