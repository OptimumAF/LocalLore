"""Capacity artifact audits fail closed; synthetic AAPT data, no device calls."""
from pathlib import Path
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import android_capacity_probe as capacity
import audit_apk


BADGING = """package: name='org.locallore.app.capacity' versionCode='1'
minSdkVersion:'26'
targetSdkVersion:'36'
uses-permission: name='org.locallore.app.capacity.DYNAMIC_RECEIVER_NOT_EXPORTED_PERMISSION'
application-label:'LocalLore \u00b7 SQLite capacity test'
"""
TREE = """E: manifest (line=1)
  E: permission (line=2)
    A: android:name(0x1)="org.locallore.app.capacity.DYNAMIC_RECEIVER_NOT_EXPORTED_PERMISSION"
    A: android:protectionLevel(0x2)=0x2
  E: application (line=3)
    A: android:testOnly(0x3)=true
    E: meta-data (line=4)
      A: android:name(0x1)="org.locallore.capacity.pages" (Raw: "org.locallore.capacity.pages")
      A: android:value(0x2)=15
    E: meta-data (line=5)
      A: android:name(0x1)="org.locallore.capacity.prefix_turns" (Raw: "org.locallore.capacity.prefix_turns")
      A: android:value(0x2)=0
"""
TEST_BADGING = """package: name='org.locallore.app.capacity.test' versionCode='1'
"""
TEST_TREE = """E: manifest (line=1)
  E: instrumentation (line=2)
    A: android:name(0x1)="androidx.test.runner.AndroidJUnitRunner"
    A: android:targetPackage(0x2)="org.locallore.app.capacity"
"""


class CapacityAuditTests(unittest.TestCase):
    def test_exact_test_binary_identity_and_profile(self):
        result = capacity.audit_capacity_manifests(BADGING, TREE, TEST_BADGING, TEST_TREE)
        self.assertEqual(result, [capacity.PACKAGE + ".DYNAMIC_RECEIVER_NOT_EXPORTED_PERMISSION"])

    def test_wrong_profile_or_missing_test_identity_rejected(self):
        for tree in (TREE.replace("=15", "=16"), TREE.replace("=0\n", "=1\n"),
                     TREE.replace("=true", "=false"), TREE.replace("capacity.pages", "other.pages")):
            with self.subTest(tree=tree), self.assertRaises(audit_apk.AuditError):
                capacity.audit_capacity_manifests(BADGING, tree, TEST_BADGING, TEST_TREE)
        for badging in (BADGING.replace(capacity.LABEL, "LocalLore"),
                        BADGING + "uses-permission: name='android.permission.INTERNET'\n"):
            with self.subTest(badging=badging), self.assertRaises(audit_apk.AuditError):
                capacity.audit_capacity_manifests(badging, TREE, TEST_BADGING, TEST_TREE)

    def test_wrong_target_and_provider_collision_rejected(self):
        for test_badging, test_tree in ((TEST_BADGING, TEST_TREE.replace('="org.locallore.app.capacity"',
                                                                      '="org.locallore.app"')),
                                       (TEST_BADGING.replace("capacity.test", "test"), TEST_TREE),
                                       (TEST_BADGING, TEST_TREE + "  E: provider (line=3)"),
                                       (TEST_BADGING, TEST_TREE.replace("AndroidJUnitRunner", "OtherRunner")),
                                       (TEST_BADGING, TEST_TREE + TEST_TREE)):
            with self.subTest(test_badging=test_badging), self.assertRaises(audit_apk.AuditError):
                capacity.audit_capacity_manifests(BADGING, TREE, test_badging, test_tree)


if __name__ == "__main__":
    unittest.main()
