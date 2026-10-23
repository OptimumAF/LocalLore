"""Helper-failure profile isolation; synthetic manifests, never devices."""
from pathlib import Path
import sys
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import android_capacity_fault_probe as faults
import android_capacity_relief_probe as relief
import audit_apk
from test_android_capacity_relief_probe import BADGING, TREE, TEST_BADGING, TEST_TREE

FAULT_BADGING = BADGING.replace(relief.PACKAGE, relief.FAULT_PACKAGE).replace(relief.LABEL, relief.FAULT_LABEL)
FAULT_TEST_BADGING = TEST_BADGING.replace(relief.PACKAGE, relief.FAULT_PACKAGE)
FAULT_TEST_TREE = TEST_TREE.replace(relief.PACKAGE, relief.FAULT_PACKAGE)
FAULT_TREE = TREE.replace(relief.PACKAGE, relief.FAULT_PACKAGE) + """    E: meta-data (line=9)
      A: android:name(0x1)="org.locallore.capacity.relief.faults_format"
      A: android:value(0x2)=1
"""


class FaultProfileAuditTests(unittest.TestCase):
    def test_fault_build_has_exclusive_flag_and_history(self):
        root = Path('/synthetic/root')
        ordinary = relief.check.Command(('java', 'wrapper', 'assembleDebug'), root / 'apps/android')
        with patch.object(relief.check, 'android_commands', return_value=[ordinary]):
            actual = faults.fault_build_command(root, True)
            normal = relief.relief_build_command(root, True)
        self.assertEqual(actual.argv[-3:], ('-Plocallore.capacityReliefFaultTest=true', '--project-cache-dir',
                                          str(root / 'apps/android/.gradle-capacity-faults-v3')))
        self.assertNotEqual(actual.argv, normal.argv)
        self.assertEqual(actual.cwd, ordinary.cwd)

    def test_exact_fault_profile_admitted(self):
        self.assertEqual(faults.audit_fault_manifests(FAULT_BADGING, FAULT_TREE, FAULT_TEST_BADGING, FAULT_TEST_TREE),
                         [relief.FAULT_PACKAGE + '.DYNAMIC_RECEIVER_NOT_EXPORTED_PERMISSION'])

    def test_normal_relief_cannot_admit_fault_metadata_or_identity(self):
        for tree in (FAULT_TREE, FAULT_TREE.replace(relief.FAULT_PACKAGE, relief.PACKAGE)):
            with self.subTest(tree=tree), self.assertRaises(audit_apk.AuditError):
                relief.audit_relief_manifests(BADGING, tree, TEST_BADGING, TEST_TREE)
        with self.assertRaises(audit_apk.AuditError):
            faults.audit_fault_manifests(BADGING, TREE, TEST_BADGING, TEST_TREE)

    def test_fault_control_version_must_be_unique_exact_integer(self):
        extra = FAULT_TREE[FAULT_TREE.rindex('    E: meta-data'):]
        for tree in (FAULT_TREE.replace('faults_format', 'unknown_faults'),
                     FAULT_TREE.replace('=1\n', '=2\n'), FAULT_TREE.replace('=1\n', '=1.0\n'),
                     FAULT_TREE + extra, FAULT_TREE[:-len(extra)]):
            with self.subTest(tree=tree), self.assertRaises(audit_apk.AuditError):
                faults.audit_fault_manifests(FAULT_BADGING, tree, FAULT_TEST_BADGING, FAULT_TEST_TREE)

    def test_wrong_target_permissions_and_test_only_rejected(self):
        for badging, tree, target in (
                (FAULT_BADGING, FAULT_TREE, TEST_TREE),
                (FAULT_BADGING, FAULT_TREE.replace('=true', '=false'), FAULT_TEST_TREE),
                (FAULT_BADGING + "uses-permission: name='android.permission.INTERNET'\n", FAULT_TREE, FAULT_TEST_TREE),
                (FAULT_BADGING.replace(relief.FAULT_LABEL, relief.LABEL), FAULT_TREE, FAULT_TEST_TREE)):
            with self.subTest(tree=tree), self.assertRaises(audit_apk.AuditError):
                faults.audit_fault_manifests(badging, tree, FAULT_TEST_BADGING, target)


if __name__ == '__main__':
    unittest.main()
