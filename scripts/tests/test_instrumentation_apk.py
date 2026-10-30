"""Original paired-APK policy tests using byte-backed ZIPs and simulated tools.

Copyright 2026 LocalLore contributors. SPDX-License-Identifier: Apache-2.0
"""
from contextlib import ExitStack, redirect_stderr, redirect_stdout
import hashlib
import importlib.util
import io
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch
import zipfile

from scripts.tests import test_audit_apk as f
from scripts.tests import test_apk_backup_audit as backup
from scripts.tests import test_physical_backup_linkage as linkage
from scripts.tests import test_check as check_fixture


ROOT = Path(__file__).resolve().parents[2]
NORMAL = "org.locallore.app"
ARCHIVE = NORMAL + ".archiveverify"
SIGNER = "a" * 64


def captures(app):
    old = linkage.manifests()
    badging = f.BADGING.replace(NORMAL, app)
    tree = backup.manifest().replace(NORMAL, app) + backup.attribute("debuggable", "0x0101000f", "true")
    test_badging, test_tree = (v.replace(linkage.p.APP, app) for v in old[2:4])
    return [badging, tree, test_badging, test_tree]


def invoke(main, argv):
    out, err = io.StringIO(), io.StringIO()
    with redirect_stdout(out), redirect_stderr(err):
        try:
            code = main(argv)
        except SystemExit as exc:
            code = exc.code
    return code, out.getvalue(), err.getvalue()


class InstrumentationApkTests(unittest.TestCase):
    def module(self):
        path = ROOT / "scripts/audit_instrumentation_apk.py"
        self.assertTrue(path.is_file(), "public paired instrumentation audit is not implemented")
        spec = importlib.util.spec_from_file_location("instrumentation_apk_test_target", path)
        module = importlib.util.module_from_spec(spec)
        sys.modules[spec.name] = module
        spec.loader.exec_module(module)
        return module

    def pure(self, values, *, archive=False):
        return self.module().audit_manifests(*values, archive_verification=archive)

    def rejected(self, values, *, archive=False):
        module = self.module()
        with self.assertRaises(module.base.AuditError):
            module.audit_manifests(*values, archive_verification=archive)

    def pair(self, *, archive=False, main=False, flags=None, selected_package=None,
             same=False, mutate=False, signing=None, tool_failure=None):
        module = self.module()
        directory = Path(tempfile.mkdtemp(prefix="locallore-test-apk-"))
        app = f.ApkAuditTests().archive(directory)
        test = directory / "instrumentation.apk"
        with zipfile.ZipFile(test, "x") as z:
            z.writestr("AndroidManifest.xml", b"synthetic compiled test manifest")
        sdk = directory / "sdk"
        (sdk / "lib").mkdir(parents=True)
        (sdk / "lib/apksigner.jar").write_bytes(b"inert signing-tool placeholder")
        aapt = sdk / "aapt2.exe"
        aapt.write_bytes(b"inert AAPT placeholder")
        java = directory / "jdk"
        (java / "bin").mkdir(parents=True)
        (java / "bin" / ("java.exe" if os.name == "nt" else "java")).write_bytes(b"never executed")
        package = selected_package or (ARCHIVE if archive else NORMAL)
        values = captures(package)
        calls = []
        changed = False

        def tool(command):
            nonlocal changed
            argv = [str(v) for v in command]
            calls.append(argv)
            if tool_failure and tool_failure in argv:
                raise module.base.AuditError("synthetic captured tool failure")
            if "--print-certs" in argv:
                target = app if str(app) in argv else test
                if mutate and not changed:
                    app.write_bytes(app.read_bytes() + b"changed after identity capture")
                    changed = True
                default = "Number of signers: 1\nSigner #1 certificate SHA-256 digest: " + SIGNER + "\n"
                return (signing or {}).get("app" if target == app else "test", default)
            self.assertEqual(argv[:2], [str(aapt), "dump"])
            self.assertTrue(str(app) in argv or str(test) in argv)
            index = 0 if str(app) in argv else 2
            if argv[2] == "badging":
                return values[index]
            if argv[2] == "xmltree":
                name = argv[argv.index("--file") + 1]
                if name == "AndroidManifest.xml":
                    return values[index + 1]
                self.assertEqual(name, backup.RULE_PATH)
                return backup.rules()
            if argv[2] == "resources":
                return backup.RESOURCE.replace(NORMAL, package)
            raise AssertionError("unexpected synthetic tool command")

        before = {"app": app.read_bytes(), "test": test.read_bytes()}
        with patch.object(module.base, "aapt2_path", return_value=aapt), \
                patch.object(module.physical, "tool", side_effect=tool), \
                patch.dict(os.environ, {"JAVA_HOME": str(java)}):
            if main:
                args = [str(app), str(app if same else test)]
                args += (["--archive-verification"] if archive else []) if flags is None else flags
                value = invoke(module.main, args)
            else:
                value = module.audit_pair(app, app if same else test, archive_verification=archive)
        return value, before, calls

    def test_normal_and_archive_manifest_pairs_accept_lf_and_crlf_with_exact_result_schema(self):
        for archive, package in ((False, NORMAL), (True, ARCHIVE)):
            for crlf in (False, True):
                values = captures(package)
                if crlf:
                    values = [v.replace("\n", "\r\n") for v in values]
                with self.subTest(archive=archive, crlf=crlf):
                    self.assertEqual(self.pure(values, archive=archive), dict(package=package,
                        test_package=package + ".test", test_permissions=["android.permission.REORDER_TASKS"]))

    def test_shared_test_policy_is_reusable_without_changing_the_old_phone_manifest_api(self):
        legacy = linkage.p.audit_manifests(*linkage.manifests())
        self.assertEqual(legacy["permissions"], [linkage.p.APP + ".DYNAMIC_RECEIVER_NOT_EXPORTED_PERMISSION"])
        self.assertEqual(legacy["test_methods"], 6)
        module = self.module()
        shared = getattr(module.physical, "audit_test_manifest", None)
        self.assertTrue(callable(shared), "shared closed test-manifest policy is not implemented")
        for package in (NORMAL, ARCHIVE, linkage.p.APP):
            _, _, badging, tree = captures(package)
            with self.subTest(package=package):
                shared(badging, tree, package)
                with self.assertRaises(module.base.AuditError):
                    shared(badging + "uses-permission: name='android.permission.INTERNET'\n", tree, package)

    def test_package_target_runner_and_instrumentation_count_are_bound_to_the_selected_pair(self):
        good = captures(NORMAL)
        variants = []
        for index in (0, 1, 2, 3):
            value = list(good); value[index] = value[index].replace(NORMAL, "org.foreign.app")
            variants.append(("foreign:" + str(index), value))
        for label, tree in (("target", good[3].replace('targetPackage(0x01010021)="' + NORMAL, 'targetPackage(0x01010021)="org.foreign.app')),
                            ("runner", good[3].replace("androidx.test.runner.AndroidJUnitRunner", "org.foreign.Runner")),
                            ("duplicate", good[3] + '      E: instrumentation (line=99)\n' + linkage.attr("name", "0x01010003", linkage.p.RUNNER) + linkage.attr("targetPackage", "0x01010021", NORMAL)),
                            ("target_process", good[3].replace('      E: application', linkage.attr("targetProcesses", "0x01010426", ":other") + '      E: application'))):
            variants.append((label, [*good[:3], tree]))
        for label, values in variants:
            with self.subTest(case=label):
                self.rejected(values)
        self.rejected(captures(ARCHIVE))
        self.rejected(captures(NORMAL), archive=True)

    def test_malformed_sdk_and_extra_duplicate_or_hidden_test_permissions_are_refused(self):
        good = captures(NORMAL)
        permission = "uses-permission: name='android.permission.REORDER_TASKS'\n"
        for label, badging in (("minimum", good[2].replace("minSdkVersion:'26'", "minSdkVersion:'25'")),
            ("duplicate_sdk", good[2] + "targetSdkVersion:'36'\n"),
            ("malformed_sdk", good[2].replace("targetSdkVersion:'36'", "targetSdkVersion:true")),
            ("internet", good[2] + "uses-permission: name='android.permission.INTERNET'\n"),
            ("duplicate_permission", good[2] + permission)):
            with self.subTest(case=label):
                self.rejected([good[0], good[1], badging, good[3]])
        for tag in ("permission", "uses-permission-sdk-23"):
            with self.subTest(hidden=tag):
                tree = good[3] + "      E: " + tag + " (line=99)\n" + linkage.attr("name", "0x01010003", "android.permission.INTERNET")
                self.rejected([*good[:3], tree])

    def test_provider_inventory_namespace_process_export_and_document_grants_are_closed(self):
        good = captures(NORMAL)
        for label, tree in (("authority", good[3].replace(NORMAL + ".test.chooser.control", "org.foreign.control")),
            ("process", good[3].replace(":archive_test_provider", ":other")),
            ("exported", good[3].replace("exported(0x01010010)=true", "exported(0x01010010)=false", 1)),
            ("permission", good[3].replace("android.permission.MANAGE_DOCUMENTS", "android.permission.INTERNET")),
            ("grant", good[3].replace("grantUriPermissions(0x0101001b)=true", "grantUriPermissions(0x0101001b)=false")),
            ("missing_provider", good[3].replace("ChooserArchiveProvider$Control", "UnexpectedProvider")),
            ("extra_child", good[3] + "              E: grant-uri-permission (line=99)\n")):
            with self.subTest(case=label):
                self.rejected([*good[:3], tree])

    def test_unexpected_components_activities_shared_uid_and_application_overrides_are_refused(self):
        good = captures(NORMAL)
        variants = [("component:" + tag, good[3] + "          E: " + tag + " (line=99)\n" + linkage.attr("name", "0x01010003", "org.foreign.Component", 12))
                    for tag in ("service", "receiver", "activity", "activity-alias")]
        variants.append(("shared_uid", good[3].replace("      E: instrumentation", linkage.attr("sharedUserId", "0x0101000b", "org.foreign.shared", 4) + "      E: instrumentation", 1)))
        for name, identity in (("process", "0x01010011"), ("permission", "0x01010006"), ("taskAffinity", "0x01010012")):
            variants.append(("application:" + name, good[3].replace('      E: application (line=5)\n', '      E: application (line=5)\n' + linkage.attr(name, identity, "org.foreign.override"))))
        for label, tree in variants:
            with self.subTest(case=label):
                self.rejected([*good[:3], tree])

    def test_pair_binds_real_zip_bytes_and_same_single_signer_for_both_profiles(self):
        for archive, package in ((False, NORMAL), (True, ARCHIVE)):
            with self.subTest(archive=archive):
                value, before, calls = self.pair(archive=archive)
                self.assertEqual(set(value), {"status", "package", "test_package", "test_permissions", "certificate_sha256", "app", "test"})
                self.assertEqual(value["status"], "passed")
                self.assertEqual((value["package"], value["test_package"], value["certificate_sha256"]), (package, package + ".test", SIGNER))
                for label in ("app", "test"):
                    self.assertEqual(value[label], dict(bytes=len(before[label]), sha256=hashlib.sha256(before[label]).hexdigest()))
                self.assertEqual(sum("--print-certs" in c for c in calls), 2)

    def test_same_apk_and_bytes_changed_during_signer_capture_cannot_qualify(self):
        module = self.module()
        for label, options in (("same", {"same": True}), ("changed", {"mutate": True})):
            with self.subTest(case=label), self.assertRaises(module.base.AuditError):
                self.pair(**options)

    def test_signer_mismatch_multiple_missing_duplicate_and_tool_failure_are_refused(self):
        module = self.module()
        for label, output in (("mismatch", "Number of signers: 1\nSigner #1 certificate SHA-256 digest: " + "b" * 64 + "\n"),
            ("multiple", "Number of signers: 2\nSigner #1 certificate SHA-256 digest: " + SIGNER + "\n"),
            ("missing", "Number of signers: 1\n"),
            ("duplicate", "Number of signers: 1\n" + ("Signer #1 certificate SHA-256 digest: " + SIGNER + "\n") * 2)):
            with self.subTest(case=label), self.assertRaises(module.base.AuditError):
                self.pair(signing={"test": output})
        with self.assertRaises(module.base.AuditError):
            self.pair(tool_failure="--print-certs")

    def test_public_cli_normal_archive_unknown_and_unselected_archive_controls(self):
        self.module()
        for archive in (False, True):
            with self.subTest(archive=archive):
                (code, text, _), _, _ = self.pair(main=True, archive=archive)
                self.assertEqual(code, 0, text)
                self.assertEqual(json.loads(text)["status"], "passed")
        (code, text, _), _, _ = self.pair(main=True, selected_package=ARCHIVE, flags=[])
        self.assertEqual(code, 1)
        self.assertNotIn('"status": "passed"', text)
        (code, _, _), _, calls = self.pair(main=True, flags=["--arbitrary-package"])
        self.assertIn(code, (1, 2))
        self.assertEqual(calls, [])

    def test_standard_plan_preserves_first_two_commands_and_adds_fixed_pair_audit(self):
        check = check_fixture.check
        root = check.ROOT
        with patch.object(check, "java_executable", return_value="synthetic-java"):
            for archive in (False, True):
                for offline in (False, True):
                    for clean in (False, True):
                        with self.subTest(archive=archive, offline=offline, clean=clean):
                            commands = check.android_commands(root, offline, clean, archive_verification=archive)
                            self.assertEqual(len(commands), 3)
                            gradle = ["synthetic-java", "-classpath", str(root / "apps/android/gradle/wrapper/gradle-wrapper.jar"), "org.gradle.wrapper.GradleWrapperMain"]
                            if clean: gradle.append("clean")
                            gradle += [":app:assembleDebug", ":app:assembleDebugAndroidTest", ":app:testDebugUnitTest", ":app:lintDebug", "--no-daemon", "--console=plain", "-Pandroid.builder.sdkDownload=false"]
                            if archive: gradle.append("-PlocalLoreArchiveVerification=true")
                            if offline: gradle.append("--offline")
                            base = root / "apps/android/app" / ("build-archive-verification" if archive else "build") / "outputs/apk"
                            app = str(base / "debug/app-debug.apk")
                            test = str(base / "androidTest/debug/app-debug-androidTest.apk")
                            flag = ("--archive-verification",) if archive else ()
                            self.assertEqual(commands, [check.Command(tuple(gradle), root / "apps/android"),
                                check.Command((sys.executable, str(root / "scripts/audit_apk.py"), app, *flag), root),
                                check.Command((sys.executable, str(root / "scripts/audit_instrumentation_apk.py"), app, test, *flag), root)])

    def test_standard_runner_propagates_third_audit_failure_without_running_real_commands(self):
        check = check_fixture.check
        with patch.object(check, "java_executable", return_value="synthetic-java"):
            commands = check.android_commands(check.ROOT, True, False)
        self.assertEqual(len(commands), 3)
        with patch.object(check.subprocess, "run", side_effect=[subprocess.CompletedProcess([], 0), subprocess.CompletedProcess([], 0), subprocess.CompletedProcess([], 7)]) as dispatch, redirect_stdout(io.StringIO()):
            self.assertEqual(check.run_commands(commands), 7)
        self.assertEqual(dispatch.call_count, 3)
        self.assertEqual(dispatch.call_args.args[0], list(commands[2].argv))
        self.assertIs(dispatch.call_args.kwargs["shell"], False)


if __name__ == "__main__":
    unittest.main()
