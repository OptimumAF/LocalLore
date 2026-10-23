"""Build/audit the fixed synthetic SQLite-capacity APKs. Never installs or uses ADB.

Copyright 2026 LocalLore contributors. SPDX-License-Identifier: Apache-2.0
"""
import argparse
import json
from pathlib import Path
import re
import subprocess
import zipfile

import audit_apk
import check

PACKAGE = "org.locallore.app.capacity"
LABEL = "LocalLore \u00b7 SQLite capacity test"
PAGES = 15


def capacity_build_command(root, offline):
    command = check.android_commands(root, offline, False)[0]
    return check.Command(command.argv + ("-Plocallore.capacityTest=true", "--project-cache-dir",
                                         str(root / "apps/android/.gradle-capacity")), command.cwd)


def audit_capacity_manifests(badging, tree, test_badging, test_tree):
    permissions = audit_apk.audit_manifest(badging, tree, PACKAGE)
    audit_apk.require("application-label:'" + LABEL + "'" in badging, "Missing capacity test label")
    audit_apk.require(re.search(r':testOnly\([^)]*\)=true\b', tree), "Capacity app must be testOnly")
    # AAPT's typed integer records, paired within each metadata element.
    for key, value in (("pages", "15"), ("prefix_turns", "0")):
        audit_apk.require(re.search(
            r'E: meta-data \([^\n]*\)\s+[^\n]*:name\([^)]*\)="org\.locallore\.capacity\.'
            + key + r'"[^\n]*\n\s+[^\n]*:value\([^)]*\)=' + value + r'\b', tree),
            "Missing fixed capacity metadata")
    audit_apk.require(re.search(r"^package: name='" + re.escape(PACKAGE) + r"\.test' ", test_badging, re.M),
                      "Wrong capacity test package")
    blocks = []
    lines = test_tree.splitlines()
    for index, line in enumerate(lines):
        match = re.match(r"(\s*)E: instrumentation \(", line)
        if match:
            block = []
            for following in lines[index + 1:]:
                if following.strip() and len(following) - len(following.lstrip()) <= len(match[1]):
                    break
                block.append(following)
            blocks.append("\n".join(block))
    audit_apk.require(len(blocks) == 1, "Expected one instrumentation runner")
    audit_apk.require(re.search(r':name\([^)]*\)="androidx\.test\.runner\.AndroidJUnitRunner"', blocks[0]),
                      "Wrong instrumentation runner")
    audit_apk.require(re.search(r':targetPackage\([^)]*\)="' + re.escape(PACKAGE) + r'"', blocks[0]),
                      "Wrong instrumentation target")
    audit_apk.require("E: provider (" not in test_tree, "Capacity test must not register a diagnostic provider")
    return permissions


def audit_capacity(root):
    output = root / "apps/android/app/build-capacity/outputs/apk"
    app = output / "debug/app-debug.apk"
    test = output / "androidTest/debug/app-debug-androidTest.apk"
    libraries = audit_apk.audit_zip(app)
    aapt = str(audit_apk.aapt2_path())
    def dump(path, *args):
        return subprocess.run([aapt, "dump", *args, str(path)], check=True, capture_output=True,
                              encoding="utf-8", shell=False).stdout
    def tree(path):
        return subprocess.run([aapt, "dump", "xmltree", str(path), "--file", "AndroidManifest.xml"],
                              check=True, capture_output=True, encoding="utf-8", shell=False).stdout
    permissions = audit_capacity_manifests(dump(app, "badging"), tree(app), dump(test, "badging"), tree(test))
    with zipfile.ZipFile(app) as archive:
        for abi in audit_apk.ABIS:
            data = archive.read("lib/" + abi + "/liblocallore_android.so")
            audit_apk.require(b"MAX_PAGE_COUNT=15\x00" in data, "Missing fixed native SQLite compile option")
            audit_apk.require(b"MAX_PAGE_COUNT=0xfffffffe\x00" not in data, "Default SQLite limit in capped binary")
    return {"status": "passed", "scope": "synthetic_capacity_test_binary", "pages": PAGES,
            "prefix_turns": 0, "package": PACKAGE, "permissions": permissions, "libraries": libraries}


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("action", choices=("build", "audit"))
    parser.add_argument("--offline", action="store_true")
    args = parser.parse_args(argv)
    try:
        if args.action == "build":
            status = check.run_commands([capacity_build_command(check.ROOT, args.offline)])
            if status:
                return status
        print(json.dumps(audit_capacity(check.ROOT), indent=2))
        return 0
    except (OSError, ValueError, zipfile.BadZipFile, subprocess.CalledProcessError) as error:
        print("Capacity check failed: " + str(error))
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
