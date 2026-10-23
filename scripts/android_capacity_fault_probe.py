"""Build/audit the fixed opt-in helper-failure fixture. Never installs or uses ADB.

Copyright 2026 LocalLore contributors. SPDX-License-Identifier: Apache-2.0
"""
import android_capacity_relief_probe as relief


def fault_build_command(root, offline):
    return relief.relief_build_command(root, offline, faults=True)


def audit_fault_manifests(badging, tree, test_badging, test_tree):
    return relief.audit_relief_manifests(badging, tree, test_badging, test_tree, faults=True)


def audit_fault(root):
    return relief.audit_relief(root, faults=True)


if __name__ == "__main__":
    raise SystemExit(relief.main(faults=True))
