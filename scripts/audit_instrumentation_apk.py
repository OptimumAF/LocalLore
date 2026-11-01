"""Offline instrumentation pair audit for the ordinary or explicit archive app.

This verifies package/signature/manifest boundaries, never test execution.
Copyright 2026 LocalLore contributors. SPDX-License-Identifier: Apache-2.0
"""
import argparse
import json
from pathlib import Path
import re
import struct
import sys
import zipfile

sys.path.insert(0, str(Path(__file__).resolve().parent))
import audit_physical_model_apk as physical
import audit_apk as base
import check as runner

AuditError = base.AuditError
require = base.require


def audit_manifests(app_badging, app_tree, test_badging, test_tree, *, archive_verification=False):
    require(type(archive_verification) is bool, "Invalid archive verification selection")
    app = "org.locallore.app.archiveverify" if archive_verification else "org.locallore.app"
    test = app + ".test"
    app_badging, app_tree, test_badging, test_tree = (
        base.aapt_text(value) for value in (app_badging, app_tree, test_badging, test_tree))
    for badging, tree, package in ((app_badging, app_tree, app), (test_badging, test_tree, test)):
        manifests = physical.blocks(tree, "manifest")
        require(len(manifests) == 1, "Wrong manifest root count")
        physical.one(manifests[0][0], "package", package)
        require(re.findall(r"^package: name='([^']+)'", badging, re.M) == [package], "Wrong manifest package")
    base.audit_manifest(app_badging, app_tree, app)
    require(not physical.blocks(app_tree, "instrumentation"), "Instrumentation in app")
    require(not physical.attr(app_tree + "\n" + test_tree, "sharedUserId") and
            not physical.blocks(app_tree, "activity-alias") and not physical.blocks(test_tree, "activity-alias"),
            "Shared or aliased identity")
    applications = physical.blocks(test_tree, "application")
    require(len(applications) == 1, "Wrong test application count")
    require(not any(physical.attr(applications[0][0], name) for name in ("process", "permission", "backupAgent", "taskAffinity")),
            "Unexpected test application override")
    permissions = physical.audit_test_manifest(test_badging, test_tree, app)
    return {"package": app, "test_package": test, "test_permissions": permissions}


def audit_pair(app, test, *, archive_verification=False):
    require(type(archive_verification) is bool, "Invalid archive verification selection")
    app, test = Path(app), Path(test)
    require(app.resolve() != test.resolve() and app.is_file() and test.is_file(), "Invalid APK pair")
    app_before, test_before = physical.apk_identity(app), physical.apk_identity(test)
    require(app_before[1][:2] != test_before[1][:2], "APK pair must use distinct files")
    base.audit_zip(app)
    aapt = base.aapt2_path()
    java = runner.java_executable()
    app_badging = physical.tool([aapt, "dump", "badging", app])
    test_badging = physical.tool([aapt, "dump", "badging", test])
    app_tree = physical.tool([aapt, "dump", "xmltree", app, "--file", "AndroidManifest.xml"])
    test_tree = physical.tool([aapt, "dump", "xmltree", test, "--file", "AndroidManifest.xml"])
    manifests = audit_manifests(app_badging, app_tree, test_badging, test_tree,
                               archive_verification=archive_verification)
    signer = physical.certificate(app, aapt, java=java)
    require(physical.certificate(test, aapt, java=java) == signer, "APK signing identities differ")
    require(physical.apk_identity(app) == app_before and physical.apk_identity(test) == test_before,
            "APK pair changed during audit")
    return {"status": "passed", **manifests, "certificate_sha256": signer,
            "app": app_before[0], "test": test_before[0]}


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("app", type=Path)
    parser.add_argument("test", type=Path)
    parser.add_argument("--archive-verification", action="store_true",
                        help="Audit only the isolated archive verification app/test pair")
    args = parser.parse_args(argv)
    try:
        print(json.dumps(audit_pair(args.app, args.test, archive_verification=args.archive_verification), sort_keys=True))
        return 0
    except AuditError as error:
        print(json.dumps({"status": "failed", "error": str(error)[:256]}))
        return 1
    except (OSError, ValueError, zipfile.BadZipFile, struct.error):
        print(json.dumps({"status": "failed", "error": "audit_failed"}))
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
