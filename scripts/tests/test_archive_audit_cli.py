"""Archive-profile CLI routing with synthetic APK/AAPT data, never SDK execution.

Copyright 2026 LocalLore contributors. SPDX-License-Identifier: Apache-2.0
"""
from contextlib import ExitStack, redirect_stderr, redirect_stdout
import io
import json
from pathlib import Path
import sys
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import patch

from scripts.tests import test_audit_apk as f
from scripts.tests import test_apk_backup_audit as backup
from scripts.tests import test_check as check_fixture


APP = "org.locallore.app.archiveverify"
MODEL_FLAGS = ("--litert-verification", "--model-provisioning", "--model-picker-fixture",
               "--model-volume-verification", "--model-receipt-verification",
               "--input-draft-verification", "--input-process-verification")


def metadata(package):
    return tuple(text.replace("org.locallore.app", package)
                 for text in (f.BADGING, backup.manifest(), backup.RESOURCE))


def invoke(main, argv):
    out, err = io.StringIO(), io.StringIO()
    with redirect_stdout(out), redirect_stderr(err):
        try:
            code = main(argv)
        except SystemExit as exc:
            code = exc.code
    return code, out.getvalue(), err.getvalue()


class ArchiveAuditCliTests(unittest.TestCase):
    def setUp(self):
        self.directory = Path(tempfile.mkdtemp(prefix="locallore-archive-cli-"))
        self.apk = f.ApkAuditTests().archive(self.directory)

    def audit(self, flags=(), *, package=APP, badging=None, tree=None,
              resources=None, rules=None, crlf=False):
        defaults = metadata(package)
        badging = defaults[0] if badging is None else badging
        tree = defaults[1] if tree is None else tree
        resources = defaults[2] if resources is None else resources
        rules = backup.rules() if rules is None else rules
        if crlf:
            badging, tree, resources, rules = (s.replace("\n", "\r\n")
                                               for s in (badging, tree, resources, rules))
        calls = []

        def tool(argv, **kwargs):
            self.assertEqual(argv[:2], [str(Path("D:/Synthetic/aapt2.exe")), "dump"])
            self.assertEqual(kwargs, dict(check=True, capture_output=True,
                                         text=True, encoding="utf-8", shell=False))
            calls.append(tuple(argv))
            if argv[2] == "badging":
                value = badging
            elif argv[2] == "resources":
                value = resources
            elif argv[2] == "xmltree":
                name = argv[argv.index("--file") + 1]
                self.assertIn(name, ("AndroidManifest.xml", backup.RULE_PATH))
                value = tree if name == "AndroidManifest.xml" else rules
            else:
                raise AssertionError("unexpected synthetic aapt command")
            return SimpleNamespace(stdout=value)

        with ExitStack() as stack:
            stack.enter_context(patch.object(f.audit, "aapt2_path", return_value=Path("D:/Synthetic/aapt2.exe")))
            stack.enter_context(patch.object(f.audit.subprocess, "run", side_effect=tool))
            spies = {name: stack.enter_context(patch.object(f.audit, name, wraps=getattr(f.audit, name)))
                     for name in ("audit_zip", "audit_manifest", "audit_backup_resource", "audit_backup_rules")}
            result = invoke(f.audit.main, [str(self.apk), *flags])
        return result, spies, calls

    def test_archive_cli_routes_own_package_and_backup_resources_through_real_auditors(self):
        for crlf in (False, True):
            with self.subTest(crlf=crlf):
                (code, text, _), spies, calls = self.audit(("--archive-verification",), crlf=crlf)
                self.assertEqual(code, 0, text)
                observed = json.loads(text)
                self.assertEqual(set(observed), {"status", "permissions", "libraries"})
                self.assertEqual(observed["status"], "passed")
                self.assertEqual(observed["permissions"], [APP + ".DYNAMIC_RECEIVER_NOT_EXPORTED_PERMISSION"])
                self.assertCountEqual(observed["libraries"], [
                    {"entry": "lib/arm64-v8a/libandroidx.graphics.path.so", "elf_load_alignment": [16384]},
                    {"entry": "lib/arm64-v8a/liblocallore_android.so", "elf_load_alignment": [16384]},
                    {"entry": "lib/x86_64/libandroidx.graphics.path.so", "elf_load_alignment": [16384]},
                    {"entry": "lib/x86_64/liblocallore_android.so", "elf_load_alignment": [16384]}])
                spies["audit_manifest"].assert_called_once()
                spies["audit_backup_resource"].assert_called_once()
                spies["audit_backup_rules"].assert_called_once()
                self.assertEqual(spies["audit_manifest"].call_args.args[2], APP)
                self.assertEqual(spies["audit_backup_resource"].call_args.args[2], APP)
                self.assertEqual([c[2] for c in calls].count("resources"), 1)
                self.assertTrue(any(c[-1] == backup.RULE_PATH for c in calls))

    def test_default_profile_and_unknown_option_controls_keep_archive_explicit(self):
        (code, text, _), _, _ = self.audit(package="org.locallore.app")
        self.assertEqual(code, 0, text)
        self.assertEqual(json.loads(text)["permissions"], [f.audit.PERMISSION])
        (code, text, _), _, _ = self.audit()
        self.assertEqual(code, 1)
        self.assertNotIn('"status": "passed"', text)
        (code, _, _), spies, calls = self.audit(("--archive-verification-typo",))
        self.assertIn(code, (1, 2))
        spies["audit_zip"].assert_not_called()
        self.assertEqual(calls, [])

    def test_archive_conflicts_with_every_existing_model_and_input_flag_before_artifact_work(self):
        for flag in MODEL_FLAGS:
            with self.subTest(flag=flag):
                (code, text, _), spies, calls = self.audit(("--archive-verification", flag))
                self.assertIn(code, (1, 2))
                self.assertNotIn('"status": "passed"', text)
                spies["audit_zip"].assert_not_called()
                self.assertEqual(calls, [])

    def test_archive_flag_cannot_bless_foreign_packages_or_unsafe_backup_and_permission_metadata(self):
        good_badging, good_tree, good_resources = metadata(APP)
        cases = []
        for package in ("org.locallore.app", APP + ".other", "org.locallore.app.Archiveverify"):
            badging, tree, resources = metadata(package)
            cases.append(("package:" + package, dict(badging=badging, tree=tree, resources=resources)))
        cases.extend((
            ("permission_owner", dict(tree=good_tree.replace(APP + ".DYNAMIC", "org.foreign.app.DYNAMIC"))),
            ("internet", dict(badging=good_badging + "uses-permission: name='android.permission.INTERNET'\n")),
            ("backup_enabled", dict(tree=good_tree.replace("allowBackup(0x01010280)=false", "allowBackup(0x01010280)=true"))),
            ("resource_namespace", dict(resources=good_resources.replace("name=" + APP, "name=org.foreign.app"))),
            ("permissive_rules", dict(rules=backup.rules().replace("E: exclude", "E: include", 1))),
        ))
        for label, values in cases:
            with self.subTest(case=label):
                (code, text, _), _, _ = self.audit(("--archive-verification",), **values)
                self.assertEqual(code, 1, text)
                self.assertNotIn('"status": "passed"', text)

    def test_default_android_build_and_product_prefix_are_retained_before_pair_audit(self):
        check = check_fixture.check
        root = check.ROOT
        with patch.object(check, "java_executable", return_value="D:/Synthetic/java.exe"):
            for offline in (False, True):
                for clean in (False, True):
                    with self.subTest(offline=offline, clean=clean):
                        commands = check.android_commands(root, offline, clean)
                        gradle = ["D:/Synthetic/java.exe", "-classpath",
                            str(root / "apps/android/gradle/wrapper/gradle-wrapper.jar"), "org.gradle.wrapper.GradleWrapperMain"]
                        if clean:
                            gradle.append("clean")
                        gradle += [":app:assembleDebug", ":app:assembleDebugAndroidTest", ":app:testDebugUnitTest",
                                   ":app:lintDebug", "--no-daemon", "--console=plain", "-Pandroid.builder.sdkDownload=false"]
                        if offline:
                            gradle.append("--offline")
                        self.assertEqual(commands[:2], [check.Command(tuple(gradle), root / "apps/android"),
                            check.Command((sys.executable, str(root / "scripts/audit_apk.py"),
                                str(root / "apps/android/app/build/outputs/apk/debug/app-debug.apk")), root)])
                        self.assertEqual(len(commands), 3)
                        self.assertEqual(commands[2], check.Command((sys.executable,
                            str(root / "scripts/audit_instrumentation_apk.py"),
                            str(root / "apps/android/app/build/outputs/apk/debug/app-debug.apk"),
                            str(root / "apps/android/app/build/outputs/apk/androidTest/debug/app-debug-androidTest.apk")), root))

    def test_archive_android_command_selects_only_fixed_property_output_and_audit_flag(self):
        check = check_fixture.check
        with patch.object(check, "java_executable", return_value="D:/Synthetic/java.exe"):
            default = check.android_commands(check.ROOT, True, True)
            error, commands = None, None
            try:
                commands = check.android_commands(check.ROOT, True, True, archive_verification=True)
            except TypeError as exc:
                error = str(exc)
        self.assertIsNone(error, "archive command selection was not accepted: " + str(error))
        self.assertEqual(len(commands), 3)
        self.assertEqual(commands[0].argv.count("-PlocalLoreArchiveVerification=true"), 1)
        self.assertEqual(tuple(a for a in commands[0].argv if a != "-PlocalLoreArchiveVerification=true"), default[0].argv)
        expected_apk = str(check.ROOT / "apps/android/app/build-archive-verification/outputs/apk/debug/app-debug.apk")
        self.assertEqual(commands[1].argv[:2], default[1].argv[:2])
        self.assertEqual(set(commands[1].argv[2:]), {expected_apk, "--archive-verification"})
        self.assertEqual(len(commands[1].argv), 4)
        self.assertEqual(commands[2].argv, (sys.executable,
            str(check.ROOT / "scripts/audit_instrumentation_apk.py"), expected_apk,
            str(check.ROOT / "apps/android/app/build-archive-verification/outputs/apk/androidTest/debug/app-debug-androidTest.apk"),
            "--archive-verification"))
        self.assertEqual([c.cwd for c in commands], [c.cwd for c in default])

    def test_check_android_cli_forwards_archive_selection_without_running_commands(self):
        check = check_fixture.check
        selected = [check.Command(("never-executed",), check.ROOT)]
        with patch.object(check, "android_commands", return_value=selected) as android, \
                patch.object(check, "host_commands", side_effect=AssertionError("host was selected")), \
                patch.object(check, "run_commands", return_value=0) as dispatch:
            code, text, _ = invoke(check.main, ["android", "--offline", "--clean", "--archive-verification"])
            self.assertEqual(code, 0, text)
            android.assert_called_once()
            self.assertEqual(android.call_args.args[:3], (check.ROOT, True, True))
            args, kwargs = android.call_args
            value = kwargs.get("archive_verification", args[3] if len(args) > 3 else False)
            self.assertIs(value, True)
            dispatch.assert_called_once_with(selected)

    def test_check_host_archive_and_unknown_flags_refuse_before_directory_or_command_work(self):
        check = check_fixture.check
        for argv in (["host", "--archive-verification"], ["android", "--archive-verification-typo"]):
            with self.subTest(argv=argv), patch.object(Path, "mkdir", side_effect=AssertionError("mkdir before refusal")), \
                    patch.object(check, "host_commands") as host, patch.object(check, "android_commands") as android, \
                    patch.object(check, "run_commands") as dispatch:
                code, _, _ = invoke(check.main, argv)
                self.assertIn(code, (1, 2))
                host.assert_not_called()
                android.assert_not_called()
                dispatch.assert_not_called()


if __name__ == "__main__":
    unittest.main()
