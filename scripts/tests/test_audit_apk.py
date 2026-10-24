"""Artifact regressions with synthetic ZIP/ELF data, not a second Android build.

Copyright 2026 LocalLore contributors. SPDX-License-Identifier: Apache-2.0
"""
import importlib.util
from pathlib import Path
import struct
import tempfile
import unittest
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

    def test_capacity_package_requires_explicit_allowlist_and_own_permission(self):
        for package in ("org.locallore.app.capacity", "org.locallore.app.capacityrelief"):
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
