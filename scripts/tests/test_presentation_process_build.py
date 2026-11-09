"""Synthetic, offline profile admission; never a build or Android execution.

Copyright 2026 LocalLore contributors. SPDX-License-Identifier: Apache-2.0
"""
from contextlib import ExitStack
import hashlib
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch
import zipfile

from scripts import audit_instrumentation_apk as pair
from scripts.tests import test_archive_audit_cli as cli_f
from scripts.tests import test_audit_apk as apk_f
from scripts.tests import test_audit_process_controller as controller_f
from scripts.tests import test_check as check_f
from scripts.tests import test_instrumentation_apk as pair_f


APP = "org.locallore.app.presentationprocessverify"
CONTROL = "org.locallore.app.presentationprocesscontroller"
INSTRUMENTATION = "org.locallore.presentationprocessverify.PresentationProcessRestoreInstrumentation"
FLAG = "--presentation-process-verification"
SIGNER = "a" * 64


def controller_metadata():
    # Remove the historical test-package query; the new controller has one product query.
    test_query = ('    E: package (line=4)\n'
                  '      A: android:name(0x01010003)="org.locallore.app.draftprocessverify.test"\n')
    tree = controller_f.TREE.replace(test_query, "")
    tree = tree.replace("org.locallore.app.draftprocesscontroller", CONTROL)
    tree = tree.replace("org.locallore.app.draftprocessverify", APP)
    tree = tree.replace("org.locallore.processverify.ProcessRestoreInstrumentation", INSTRUMENTATION)
    return controller_f.BADGING.replace("org.locallore.app.draftprocesscontroller", CONTROL), tree


class PresentationProcessBuildTests(unittest.TestCase):
    def controller(self, badging=None, tree=None, **kwargs):
        good_badging, good_tree = controller_metadata()
        return controller_f.audit.audit(good_badging if badging is None else badging,
                                        good_tree if tree is None else tree,
                                        controller_f.entries(), **kwargs)

    def test_new_android_plan_contains_all_fresh_tasks_fixed_cache_and_four_artifact_gates(self):
        check = check_f.check
        root = check.ROOT
        with patch.object(check, "java_executable", return_value="D:/Synthetic/java.exe"):
            for offline in (False, True):
                for clean in (False, True):
                    commands = check.android_commands(root, offline, clean,
                                                       presentation_process_verification=True)
                    self.assertEqual(len(commands), 4)
                    gradle = commands[0].argv
                    self.assertEqual(gradle[:4], ("D:/Synthetic/java.exe", "-classpath",
                        str(root / "apps/android/gradle/wrapper/gradle-wrapper.jar"),
                        "org.gradle.wrapper.GradleWrapperMain"))
                    for task in (":app:assembleDebug", ":app:assembleDebugAndroidTest",
                                 ":app:testDebugUnitTest", ":app:lintDebug",
                                 ":presentation-process-controller:assembleDebug",
                                 ":presentation-process-controller:lintDebug"):
                        self.assertEqual(gradle.count(task), 1)
                    self.assertEqual(gradle.count("clean"), int(clean))
                    self.assertEqual(gradle.count("--offline"), int(offline))
                    self.assertEqual(gradle[gradle.index("--project-cache-dir") + 1],
                                     ".gradle-presentation-process")
                    self.assertEqual(gradle.count("-PlocalLoreInputDraftVerification=true"), 1)
                    self.assertEqual(gradle.count("-PlocalLorePresentationProcessVerification=true"), 1)
                    self.assertNotIn("-PlocalLoreInputProcessVerification=true", gradle)
                    self.assertNotIn("-PlocalLoreArchiveVerification=true", gradle)
                    self.assertNotIn("-x", gradle)
                    self.assertIn("-Pandroid.builder.sdkDownload=false", gradle)
                    app = root / "apps/android/app/build-presentation-process/outputs/apk/debug/app-debug.apk"
                    test = root / "apps/android/app/build-presentation-process/outputs/apk/androidTest/debug/app-debug-androidTest.apk"
                    controller = root / "apps/android/presentation-process-controller/build/outputs/apk/debug/presentation-process-controller-debug.apk"
                    self.assertEqual([command.argv for command in commands[1:]], [
                        (sys.executable, str(root / "scripts/audit_apk.py"), str(app), FLAG),
                        (sys.executable, str(root / "scripts/audit_instrumentation_apk.py"), str(app), str(test), FLAG),
                        (sys.executable, str(root / "scripts/audit_process_controller.py"), str(controller), FLAG)])
                    self.assertEqual([command.cwd for command in commands], [root / "apps/android", root, root, root])

    def test_default_and_archive_plans_keep_their_original_three_vectors(self):
        check = check_f.check
        root = check.ROOT
        with patch.object(check, "java_executable", return_value="D:/Synthetic/java.exe"):
            for archive in (False, True):
                commands = check.android_commands(root, True, False, archive_verification=archive)
                self.assertEqual(len(commands), 3)
                gradle = ["D:/Synthetic/java.exe", "-classpath",
                          str(root / "apps/android/gradle/wrapper/gradle-wrapper.jar"),
                          "org.gradle.wrapper.GradleWrapperMain", ":app:assembleDebug",
                          ":app:assembleDebugAndroidTest", ":app:testDebugUnitTest", ":app:lintDebug",
                          "--no-daemon", "--console=plain", "-Pandroid.builder.sdkDownload=false"]
                if archive:
                    gradle.append("-PlocalLoreArchiveVerification=true")
                gradle.append("--offline")
                self.assertEqual(commands[0].argv, tuple(gradle))
                build = "build-archive-verification" if archive else "build"
                app = str(root / "apps/android/app" / build / "outputs/apk/debug/app-debug.apk")
                test = str(root / "apps/android/app" / build / "outputs/apk/androidTest/debug/app-debug-androidTest.apk")
                suffix = ("--archive-verification",) if archive else ()
                self.assertEqual(commands[1].argv, (sys.executable, str(root / "scripts/audit_apk.py"), app, *suffix))
                self.assertEqual(commands[2].argv, (sys.executable, str(root / "scripts/audit_instrumentation_apk.py"), app, test, *suffix))

    def test_selection_is_strict_boolean_exclusive_and_cli_never_sends_host_or_conflicting_work(self):
        check = check_f.check
        with patch.object(check, "java_executable", side_effect=AssertionError("early refusal needed")):
            for invalid in (0, 1, None, "true", [], {}):
                with self.subTest(invalid=repr(invalid)):
                    with self.assertRaises((ValueError, TypeError)):
                        check.android_commands(check.ROOT, True, False, presentation_process_verification=invalid)
            with self.assertRaises((ValueError, TypeError)):
                check.android_commands(check.ROOT, True, False, archive_verification=True,
                                       presentation_process_verification=True)
        selected = [check.Command(("never-executed",), check.ROOT)]
        with patch.object(check, "android_commands", return_value=selected) as android, \
             patch.object(check, "host_commands", side_effect=AssertionError("host selected")), \
             patch.object(check, "run_commands", return_value=0) as dispatch:
            code, text, _ = cli_f.invoke(check.main, ["android", FLAG, "--offline", "--clean"])
            self.assertEqual(code, 0, text)
            self.assertEqual(android.call_args.args[:3], (check.ROOT, True, True))
            self.assertIs(android.call_args.kwargs["presentation_process_verification"], True)
            dispatch.assert_called_once_with(selected)
        for argv in (["host", FLAG], ["android", FLAG, "--archive-verification"],
                     ["android", FLAG + "-typo"]):
            with patch.object(check, "run_commands", side_effect=AssertionError("dispatch forbidden")), \
                 patch.object(check, "android_commands", side_effect=AssertionError("planning forbidden")), \
                 patch.object(check, "host_commands", side_effect=AssertionError("planning forbidden")):
                code, _, _ = cli_f.invoke(check.main, argv)
                self.assertIn(code, (1, 2))

    def test_product_cli_routes_only_the_new_namespace_through_real_zip_manifest_backup_guards(self):
        fixture = cli_f.ArchiveAuditCliTests()
        fixture.setUp()
        for crlf in (False, True):
            (code, text, _), spies, calls = fixture.audit((FLAG,), package=APP, crlf=crlf)
            self.assertEqual(code, 0, text)
            self.assertEqual(json.loads(text)["permissions"], [APP + ".DYNAMIC_RECEIVER_NOT_EXPORTED_PERMISSION"])
            for name in ("audit_zip", "audit_manifest", "audit_backup_resource", "audit_backup_rules"):
                spies[name].assert_called_once()
            self.assertEqual(spies["audit_manifest"].call_args.args[2], APP)
            self.assertEqual(spies["audit_backup_resource"].call_args.args[2], APP)
            self.assertTrue(calls)
        for package in ("org.locallore.app", "org.locallore.app.archiveverify",
                        "org.locallore.app.draftprocessverify", APP + ".other", APP.upper()):
            (code, _, _), _, _ = fixture.audit((FLAG,), package=package)
            self.assertEqual(code, 1)

    def test_product_cli_rejects_every_profile_conflict_before_any_zip_or_tool_work(self):
        fixture = cli_f.ArchiveAuditCliTests()
        fixture.setUp()
        for flag in (*cli_f.MODEL_FLAGS, "--archive-verification"):
            with self.subTest(conflicting=flag):
                (code, _, _), spies, calls = fixture.audit((FLAG, flag), package=APP)
                self.assertIn(code, (1, 2))
                spies["audit_zip"].assert_not_called()
                self.assertEqual(calls, [])

    def test_pair_manifest_selection_preserves_normal_archive_and_exact_new_package(self):
        for package, options in ((APP, dict(presentation_process_verification=True)),
                                 ("org.locallore.app", {}),
                                 ("org.locallore.app.archiveverify", dict(archive_verification=True))):
            for crlf in (False, True):
                values = pair_f.captures(package)
                if crlf:
                    values = [text.replace("\n", "\r\n") for text in values]
                result = pair.audit_manifests(*values, **options)
                self.assertEqual(result, dict(package=package, test_package=package + ".test",
                                             test_permissions=["android.permission.REORDER_TASKS"]))
        values = pair_f.captures(APP)
        for invalid in (0, 1, None, "true"):
            with self.assertRaises(pair.base.AuditError):
                pair.audit_manifests(*values, presentation_process_verification=invalid)
            with patch.object(pair.physical, "apk_identity", side_effect=AssertionError("no file work")):
                with self.assertRaises(pair.base.AuditError):
                    pair.audit_pair(Path("missing-app.apk"), Path("missing-test.apk"),
                                    presentation_process_verification=invalid)
        with self.assertRaises(pair.base.AuditError):
            pair.audit_manifests(*values, archive_verification=True, presentation_process_verification=True)

    def test_pair_refuses_cross_profile_owner_target_permission_and_component_drift(self):
        good = pair_f.captures(APP)
        variants = []
        for index in range(4):
            bad = list(good)
            bad[index] = bad[index].replace(APP, "org.locallore.app.draftprocessverify")
            variants.append(bad)
        for tree in (good[1].replace(APP + ".DYNAMIC", "org.foreign.DYNAMIC"),
                     good[1].replace("  E: manifest (line=2)\n",
                                     '  E: manifest (line=2)\n    A: android:sharedUserId="shared"\n')):
            variants.append([good[0], tree, *good[2:]])
        variants.append([*good[:2], good[2] + "uses-permission: name='android.permission.INTERNET'\n", good[3]])
        variants.append([*good[:3], good[3].replace("androidx.test.runner.AndroidJUnitRunner", "foreign.Runner")])
        variants.append([*good[:3], good[3].replace(APP + ".test.chooser.control", "foreign.control")])
        for index, values in enumerate(variants):
            self.assertNotEqual(values, good, "adversary must change the valid fixture")
            with self.subTest(case=index), self.assertRaises(pair.base.AuditError):
                pair.audit_manifests(*values, presentation_process_verification=True)
        for package in ("org.locallore.app", "org.locallore.app.archiveverify", APP + ".other"):
            with self.assertRaises(pair.base.AuditError):
                pair.audit_manifests(*pair_f.captures(package), presentation_process_verification=True)

    def paired_artifacts(self, *, mismatch=False, malformed_signer=False):
        directory = Path(tempfile.mkdtemp(prefix="locallore-presentation-pair-"))
        app = apk_f.ApkAuditTests().archive(directory)
        test = directory / "instrumentation.apk"
        with zipfile.ZipFile(test, "x") as archive:
            archive.writestr("AndroidManifest.xml", b"synthetic test manifest")
        sdk = directory / "sdk"
        (sdk / "lib").mkdir(parents=True)
        (sdk / "lib/apksigner.jar").write_bytes(b"never executed")
        aapt = sdk / "aapt2.exe"
        aapt.write_bytes(b"never executed")
        java = directory / "java.exe"
        java.write_bytes(b"never executed")
        values = pair_f.captures(APP)
        before = {"app": app.read_bytes(), "test": test.read_bytes()}
        calls = []

        def tool(argv):
            calls.append(tuple(map(str, argv)))
            if "--print-certs" in argv:
                digest = "b" * 64 if mismatch and Path(argv[-1]) == test else SIGNER
                return ("Number of signers: 2\n" if malformed_signer else "Number of signers: 1\n") + \
                    "Signer #1 certificate SHA-256 digest: " + digest + "\n"
            index = 0 if Path(argv[-1]) == app or app in argv else 2
            if argv[2] == "badging":
                return values[index]
            self.assertEqual(argv[2], "xmltree")
            self.assertEqual(argv[-1], "AndroidManifest.xml")
            return values[index + 1]

        with ExitStack() as stack:
            stack.enter_context(patch.object(pair.base, "aapt2_path", return_value=aapt))
            stack.enter_context(patch.object(pair.runner, "java_executable", return_value=str(java)))
            stack.enter_context(patch.object(pair.physical, "tool", side_effect=tool))
            result = pair.audit_pair(app, test, presentation_process_verification=True)
        return result, before, calls

    def test_new_pair_joins_real_zip_identities_and_real_single_signer_parser(self):
        result, before, calls = self.paired_artifacts()
        self.assertEqual(set(result), {"status", "package", "test_package", "test_permissions", "certificate_sha256", "app", "test"})
        self.assertEqual((result["status"], result["package"], result["test_package"], result["certificate_sha256"]),
                         ("passed", APP, APP + ".test", SIGNER))
        for role in ("app", "test"):
            self.assertEqual(result[role], dict(bytes=len(before[role]), sha256=hashlib.sha256(before[role]).hexdigest()))
        self.assertEqual(sum("--print-certs" in argv for argv in calls), 2)
        for options in (dict(mismatch=True), dict(malformed_signer=True)):
            with self.subTest(options=options), self.assertRaises(pair.base.AuditError):
                self.paired_artifacts(**options)

    def test_controller_accepts_only_fixed_self_targeted_instrumentation_and_one_product_query(self):
        badging, tree = controller_metadata()
        for newline in ("\n", "\r\n"):
            result = self.controller(badging.replace("\n", newline), tree.replace("\n", newline),
                                     presentation_process_verification=True)
            self.assertEqual((result["package"], result["target"], result["instrumentation"]),
                             (CONTROL, CONTROL, INSTRUMENTATION))
            self.assertEqual((result["version"], result["scope"]),
                             (1, "locallore_presentation_process_controller_apk_audit_v1"))
            self.assertEqual((result["permissions"], result["components"]), ([], 0))
        old = controller_f.audit.audit(controller_f.BADGING, controller_f.TREE, controller_f.entries())
        self.assertEqual(old["package"], "org.locallore.app.draftprocesscontroller")
        with self.assertRaises(controller_f.audit.AuditError):
            self.controller()
        with self.assertRaises(controller_f.audit.AuditError):
            controller_f.audit.audit(controller_f.BADGING, controller_f.TREE, controller_f.entries(),
                                     presentation_process_verification=True)

    def test_controller_rejects_extra_test_or_helper_queries_and_all_identity_privilege_drift(self):
        badging, tree = controller_metadata()
        query = '    E: package (line=4)\n      A: android:name(0x01010003)="' + APP + '"\n'
        cases = [tree.replace(query, ""), tree.replace(query, query * 2),
                 tree.replace(query, query + query.replace(APP, APP + ".test")),
                 tree.replace(query, query.replace(APP, "org.locallore.app.draftprocessverify")),
                 tree.replace(INSTRUMENTATION, "org.locallore.processverify.ProcessRestoreInstrumentation"),
                 tree.replace('targetPackage(0x01010021)="' + CONTROL, 'targetPackage(0x01010021)="' + APP),
                 tree.replace("  E: uses-sdk", '  A: android:sharedUserId="shared"\n  E: uses-sdk'),
                 tree + '  E: uses-permission\n    A: android:name="android.permission.INTERNET"\n',
                 tree.replace("  E: instrumentation", '    E: service\n      A: android:name="foreign.Service"\n  E: instrumentation')]
        for index, candidate in enumerate(cases):
            with self.subTest(case=index), self.assertRaises(controller_f.audit.AuditError):
                self.controller(badging, candidate, presentation_process_verification=True)
        for invalid in (0, 1, None, "true"):
            with self.assertRaises(controller_f.audit.AuditError):
                self.controller(presentation_process_verification=invalid)


if __name__ == "__main__":
    unittest.main()
