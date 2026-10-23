"""Build/audit the fixed synthetic SQLite capacity-relief APKs. Never installs or uses ADB.

Copyright 2026 LocalLore contributors. SPDX-License-Identifier: Apache-2.0
"""
import argparse
import json
import re
import subprocess
import zipfile

import audit_apk
import check

PACKAGE = "org.locallore.app.capacityreliefv4"
LABEL = "LocalLore \u00b7 SQLite capacity relief test v4"
PAGES = 32
FAULT_PACKAGE = "org.locallore.app.capacityfaultsv4"
FAULT_LABEL = "LocalLore \u00b7 SQLite helper faults v4"


def relief_build_command(root, offline, *, faults=False):
    command = check.android_commands(root, offline, False)[0]
    option = "capacityReliefFaultTest" if faults else "capacityReliefTest"
    cache = ".gradle-capacity-faults-v4" if faults else ".gradle-capacity-relief-v4"
    # Recompile the complete test module; partial K2 recompilation has rejected
    # unchanged internal fixture declarations after observation-type changes.
    complete_module = ("-Pkotlin.incremental=false",) if faults else ()
    return check.Command(command.argv + complete_module + ("-Plocallore." + option + "=true", "--project-cache-dir",
                                         str(root / "apps/android" / cache)), command.cwd)


def audit_relief_manifests(badging, tree, test_badging, test_tree, *, faults=False):
    package, label = (FAULT_PACKAGE, FAULT_LABEL) if faults else (PACKAGE, LABEL)
    permissions = audit_apk.audit_manifest(badging, tree, package)
    audit_apk.require("application-label:'" + label + "'" in badging, "Missing capacity relief test label")
    audit_apk.require(re.search(r':testOnly\([^)]*\)=true\b', tree), "Relief app must be testOnly")
    metadata = {"pages": 32, "format": 3, "schema_version": 4, "initial_pages": 23, "padding_rows": 14}
    if faults:
        metadata["faults_format"] = 1
    audit_apk.audit_fixed_metadata(tree, "org.locallore.capacity.relief.", metadata)
    audit_apk.require(re.search(r"^package: name='" + re.escape(package) + r"\.test' ", test_badging, re.M),
                      "Wrong capacity relief test package")
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
    audit_apk.require(re.search(r':targetPackage\([^)]*\)="' + re.escape(package) + r'"', blocks[0]),
                      "Wrong instrumentation target")
    audit_apk.require("E: provider (" not in test_tree, "Relief test must not register a diagnostic provider")
    return permissions


def audit_relief(root, *, faults=False):
    build = "build-capacity-faults-v4" if faults else "build-capacity-relief-v4"
    output = root / "apps/android/app" / build / "outputs/apk"
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
    permissions = audit_relief_manifests(dump(app, "badging"), tree(app), dump(test, "badging"), tree(test), faults=faults)
    with zipfile.ZipFile(app) as archive:
        for abi in audit_apk.ABIS:
            data = archive.read("lib/" + abi + "/liblocallore_android.so")
            audit_apk.require(b"MAX_PAGE_COUNT=32\x00" in data, "Missing fixed native SQLite compile option")
            audit_apk.require(b"MAX_PAGE_COUNT=0xfffffffe\x00" not in data, "Default SQLite limit in capped binary")
            audit_apk.require(all(option not in data for option in (b"MAX_PAGE_COUNT=17\x00", b"MAX_PAGE_COUNT=23\x00")), "Other test profile in relief binary")
    return {"status": "passed", "scope": "synthetic_helper_fault_test_binary" if faults else "synthetic_capacity_relief_test_binary", "pages": PAGES,
            "fixture_format": 3, "database_schema_version": 4,
            **({"faults_format": 1} if faults else {}),
            "package": FAULT_PACKAGE if faults else PACKAGE, "permissions": permissions, "libraries": libraries}


def main(argv=None, *, faults=False):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("action", choices=("build", "audit"))
    parser.add_argument("--offline", action="store_true")
    args = parser.parse_args(argv)
    try:
        if args.action == "build":
            status = check.run_commands([relief_build_command(check.ROOT, args.offline, faults=faults)])
            if status:
                return status
        print(json.dumps(audit_relief(check.ROOT, faults=faults), indent=2))
        return 0
    except (OSError, ValueError, zipfile.BadZipFile, subprocess.CalledProcessError) as error:
        print("Relief check failed: " + str(error))
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
