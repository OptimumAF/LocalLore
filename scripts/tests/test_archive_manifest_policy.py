"""Exact archive-verification package policy; synthetic AAPT text only.

Copyright 2026 LocalLore contributors. SPDX-License-Identifier: Apache-2.0
"""
import unittest

from scripts.tests import test_audit_apk as f


ARCHIVE = "org.locallore.app.archiveverify"


def manifest(package):
    return (f.BADGING.replace("org.locallore.app", package),
            f.TREE.replace("org.locallore.app", package))


class ArchiveManifestPolicyTests(unittest.TestCase):
    def test_existing_archive_profile_accepts_only_its_scoped_signature_permission(self):
        self.assertEqual(f.audit.audit_manifest(f.BADGING, f.TREE),
                         ["org.locallore.app.DYNAMIC_RECEIVER_NOT_EXPORTED_PERMISSION"])
        badging, tree = manifest(ARCHIVE)
        error = None
        accepted = None
        try:
            accepted = f.audit.audit_manifest(badging, tree, ARCHIVE)
        except f.audit.AuditError as exc:
            error = str(exc)
        self.assertIsNone(error, "existing archive verification profile was refused: " + str(error))
        self.assertEqual(accepted, [ARCHIVE + ".DYNAMIC_RECEIVER_NOT_EXPORTED_PERMISSION"])

    def test_archive_admission_preserves_exact_package_owner_permission_and_sdk_policy(self):
        badging, tree = manifest(ARCHIVE)
        cases = []
        for package in ("org.locallore.app.archiveverify.test",
                        "org.locallore.app.Archiveverify",
                        "org.locallore.app.archiveverification",
                        "arbitrary.app.archiveverify"):
            alternate_badging, alternate_tree = manifest(package)
            cases.append(("unreviewed:" + package, alternate_badging, alternate_tree, package))
        cases.extend((
            ("manifest_package", f.BADGING, tree, ARCHIVE),
            ("permission_owner", badging, f.TREE, ARCHIVE),
            ("internet", badging + "uses-permission: name='android.permission.INTERNET'\n", tree, ARCHIVE),
            ("weak_signature", badging, tree.replace("=0x00000002", "=0x00000000"), ARCHIVE),
            ("minimum_sdk", badging.replace("minSdkVersion:'26'", "minSdkVersion:'25'"), tree, ARCHIVE),
            ("target_sdk", badging.replace("targetSdkVersion:'36'", "targetSdkVersion:'35'"), tree, ARCHIVE),
        ))
        for label, item_badging, item_tree, selected in cases:
            with self.subTest(case=label), self.assertRaises(f.audit.AuditError):
                f.audit.audit_manifest(item_badging, item_tree, selected)


if __name__ == "__main__":
    unittest.main()
