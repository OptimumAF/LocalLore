"""Capacity artifact audits fail closed; synthetic AAPT data, no device calls."""
from pathlib import Path
import sys
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import android_capacity_probe as capacity
import audit_apk


BADGING = """package: name='org.locallore.app.capacityv3' versionCode='1'
minSdkVersion:'26'
targetSdkVersion:'36'
uses-permission: name='org.locallore.app.capacityv3.DYNAMIC_RECEIVER_NOT_EXPORTED_PERMISSION'
application-label:'LocalLore \u00b7 SQLite capacity test v3'
"""
TREE = """E: manifest (line=1)
  E: permission (line=2)
    A: android:name(0x1)="org.locallore.app.capacityv3.DYNAMIC_RECEIVER_NOT_EXPORTED_PERMISSION"
    A: android:protectionLevel(0x2)=0x2
  E: application (line=3)
    A: android:testOnly(0x3)=true
    E: meta-data (line=4)
      A: android:name(0x1)="org.locallore.capacity.pages" (Raw: "org.locallore.capacity.pages")
      A: android:value(0x2)=17
    E: meta-data (line=5)
      A: android:name(0x1)="org.locallore.capacity.prefix_turns" (Raw: "org.locallore.capacity.prefix_turns")
      A: android:value(0x2)=0
    E: meta-data (line=6)
      A: android:name(0x1)="org.locallore.capacity.format"
      A: android:value(0x2)=2
    E: meta-data (line=7)
      A: android:name(0x1)="org.locallore.capacity.schema_version"
      A: android:value(0x2)=3
"""
TEST_BADGING = """package: name='org.locallore.app.capacityv3.test' versionCode='1'
"""
TEST_TREE = """E: manifest (line=1)
  E: instrumentation (line=2)
    A: android:name(0x1)="androidx.test.runner.AndroidJUnitRunner"
    A: android:targetPackage(0x2)="org.locallore.app.capacityv3"
"""


class CapacityAuditTests(unittest.TestCase):
    def test_capacity_build_owns_distinct_task_history_as_well_as_outputs(self):
        root = Path("/synthetic/root")
        ordinary = capacity.check.Command(("java", "wrapper", "assembleDebug", "--offline"), root / "apps/android")
        with patch.object(capacity.check, "android_commands", return_value=[ordinary]):
            command = capacity.capacity_build_command(root, True)
        self.assertEqual(command.argv[-3:], ("-Plocallore.capacityTest=true", "--project-cache-dir",
                                            str(root / "apps/android/.gradle-capacity-v3")))
        self.assertEqual(command.cwd, ordinary.cwd)
        self.assertNotIn("--project-cache-dir", ordinary.argv)

    def test_exact_test_binary_identity_and_profile(self):
        result = capacity.audit_capacity_manifests(BADGING, TREE, TEST_BADGING, TEST_TREE)
        self.assertEqual(result, [capacity.PACKAGE + ".DYNAMIC_RECEIVER_NOT_EXPORTED_PERMISSION"])

    def test_wrong_profile_or_missing_test_identity_rejected(self):
        for tree in (TREE.replace("=17", "=18"), TREE.replace("=0\n", "=1\n"),
                     TREE.replace("=true", "=false"), TREE.replace("capacity.pages", "other.pages")):
            with self.subTest(tree=tree), self.assertRaises(audit_apk.AuditError):
                capacity.audit_capacity_manifests(BADGING, tree, TEST_BADGING, TEST_TREE)
        for badging in (BADGING.replace(capacity.LABEL, "LocalLore"),
                        BADGING + "uses-permission: name='android.permission.INTERNET'\n"):
            with self.subTest(badging=badging), self.assertRaises(audit_apk.AuditError):
                capacity.audit_capacity_manifests(badging, TREE, TEST_BADGING, TEST_TREE)

    def test_wrong_target_and_provider_collision_rejected(self):
        for test_badging, test_tree in ((TEST_BADGING, TEST_TREE.replace('="org.locallore.app.capacityv3"',
                                                                      '="org.locallore.app"')),
                                       (TEST_BADGING.replace("capacityv3.test", "test"), TEST_TREE),
                                       (TEST_BADGING, TEST_TREE + "  E: provider (line=3)"),
                                       (TEST_BADGING, TEST_TREE.replace("AndroidJUnitRunner", "OtherRunner")),
                                       (TEST_BADGING, TEST_TREE + TEST_TREE)):
            with self.subTest(test_badging=test_badging), self.assertRaises(audit_apk.AuditError):
                capacity.audit_capacity_manifests(BADGING, TREE, test_badging, test_tree)

    def test_schema3_profile_cannot_mix_legacy_or_duplicate_metadata(self):
        for tree in (TREE.replace("=17\n", "=15\n"), TREE.replace("=3\n", "=2\n"),
                     TREE.replace("=2\n", "=1\n"),
                     TREE + TREE[TREE.index('    E: meta-data'):],
                     TREE.replace("capacity.schema_version", "capacity.unexpected")):
            with self.subTest(tree=tree), self.assertRaises(audit_apk.AuditError):
                capacity.audit_capacity_manifests(BADGING, tree, TEST_BADGING, TEST_TREE)
        with self.assertRaises(audit_apk.AuditError):
            capacity.audit_capacity_manifests(BADGING.replace("capacityv3", "capacity"), TREE,
                                             TEST_BADGING, TEST_TREE)


if __name__ == "__main__":
    unittest.main()
