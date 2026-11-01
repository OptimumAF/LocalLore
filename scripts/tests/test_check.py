"""Check orchestration failures without running a compiler, Gradle, or a shell."""

import contextlib
import importlib.util
import io
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch


SPEC = importlib.util.spec_from_file_location("locallore_check", Path(__file__).resolve().parents[1] / "check.py")
check = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = check
SPEC.loader.exec_module(check)


class CheckRunnerTests(unittest.TestCase):
    def test_failure_stops_before_later_commands_and_preserves_code(self):
        commands = [check.Command(("first", "argument with ' spaces"), Path("directory with ' spaces")),
                    check.Command(("must-not-run",), Path("elsewhere"))]
        with patch.object(check.subprocess, "run", return_value=subprocess.CompletedProcess([], 7)) as run:
            self.assertEqual(check.run_commands(commands), 7)
        run.assert_called_once_with(["first", "argument with ' spaces"], cwd=commands[0].cwd,
                                    shell=False, check=False)

    def test_success_runs_each_command_without_changing_environment(self):
        commands = [check.Command(("first",), Path("one")), check.Command(("second",), Path("two"))]
        with patch.object(check.subprocess, "run", return_value=subprocess.CompletedProcess([], 0)) as run:
            self.assertEqual(check.run_commands(commands), 0)
        self.assertEqual(run.call_count, 2)
        self.assertNotIn("env", run.call_args.kwargs)

    def test_host_offline_and_pinned_tools_keep_test_arguments_separate(self):
        root = Path("repository with ' spaces")
        commands = check.host_commands(root, True)
        cargo = [command.argv for command in commands if command.argv[0] == "cargo"]
        self.assertTrue(all(argv[1] == "+1.93.1" for argv in cargo))
        self.assertTrue(all("--offline" in argv for argv in cargo[1:]))
        self.assertNotIn("--offline", cargo[0])
        self.assertEqual(cargo[-1][-2:], ("--", "--check"))
        self.assertTrue(all(command.cwd == root for command in commands))
        self.assertEqual(commands[-1].argv[0], str(root / "target/checks" / (
            "native-linker-tests.exe" if os.name == "nt" else "native-linker-tests")))
        self.assertFalse(any("--offline" in command.argv for command in check.host_commands(root, False)))

    def test_wrapper_integrity_checks_actual_tracked_files(self):
        check.verify_wrapper(check.ROOT)

    def test_portable_workspace_commands_exclude_only_desktop(self):
        # --workspace ignores default-members: a missing exclusion would compile
        # Tauri/GTK on the portable Linux runner. Inspect the actual selected
        # command arguments, including online and offline entrypoints.
        for offline in (False, True):
            commands = check.host_commands(check.ROOT, offline)
            workspace = [command.argv for command in commands if "--workspace" in command.argv]
            self.assertEqual({argv[2] for argv in workspace}, {"test", "clippy"})
            for argv in workspace:
                exclusions = [argv[index + 1] for index, value in enumerate(argv) if value == "--exclude"]
                self.assertEqual(exclusions, ["locallore-desktop-spike"])
                self.assertNotIn("-p", argv)  # Keep every portable workspace member.
                self.assertLess(argv.index("--exclude"), argv.index("--locked"))
            other = [command.argv for command in commands if "--workspace" not in command.argv]
            self.assertTrue(all("--exclude" not in argv for argv in other))

    def test_android_commands_do_not_select_desktop_workspace(self):
        commands = check.android_commands(check.ROOT, True, False)
        self.assertTrue(all("--workspace" not in command.argv for command in commands))
        self.assertTrue(all("locallore-desktop-spike" not in command.argv for command in commands))

    @unittest.skipUnless(shutil.which("cargo"), "Cargo metadata check requires the provisioned pinned toolchain")
    def test_actual_cargo_manifest_selection_and_lock_ownership(self):
        root = check.ROOT
        lock = (root / "Cargo.lock").read_bytes()

        def metadata(manifest):
            result = subprocess.run(
                ["cargo", "+1.93.1", "metadata", "--manifest-path", str(manifest),
                 "--no-deps", "--format-version", "1", "--locked", "--offline"],
                cwd=root, shell=False, capture_output=True, text=True, timeout=60)
            self.assertEqual(result.returncode, 0, result.stderr)
            return json.loads(result.stdout)

        portable = {"locallore", "locallore-android", "locallore-storage", "locallore-workspace"}
        data = metadata(root / "Cargo.toml")
        names = {package["id"]: package["name"] for package in data["packages"]}
        self.assertEqual({names[key] for key in data["workspace_default_members"]}, portable)
        self.assertEqual({names[key] for key in data["workspace_members"]}, portable | {"locallore-desktop-spike"})
        desktop = metadata(root / "apps/desktop/src-tauri/Cargo.toml")
        self.assertEqual(Path(desktop["workspace_root"]), root)
        self.assertEqual(desktop["workspace_default_members"], [
            package["id"] for package in desktop["packages"] if package["name"] == "locallore-desktop-spike"])
        expected_target = Path(os.environ.get("CARGO_TARGET_DIR", root / "target"))
        if not expected_target.is_absolute():
            expected_target = root / expected_target
        self.assertEqual(Path(desktop["target_directory"]), expected_target.resolve())
        self.assertFalse((root / "apps/desktop/src-tauri/Cargo.lock").exists())
        self.assertEqual((root / "Cargo.lock").read_bytes(), lock)
        for name in ("locallore-local-runtime", "locallore-eval"):
            standalone = root / "crates" / name
            self.assertEqual(Path(metadata(standalone / "Cargo.toml")["workspace_root"]), standalone)
            self.assertTrue((standalone / "Cargo.lock").is_file())

    def test_native_harnesses_bind_consumed_lock_and_explicit_target(self):
        root = check.ROOT / "apps/desktop"
        for name in ("archive-harness.mjs", "durable-harness.mjs", "evaluation-harness.mjs",
                     "export-harness.mjs", "harness.mjs", "inspector-harness.mjs",
                     "legacy-harness.mjs", "model-harness.mjs", "trace-harness.mjs"):
            with self.subTest(harness=name):
                source = (root / name).read_text(encoding="utf-8")
                self.assertNotIn('"src-tauri/Cargo.lock"', source)
                self.assertIn('"../../Cargo.lock"', source)
                # The root workspace changes Cargo's default target directory.
                # Every native harness supplies its chosen target explicitly.
                self.assertRegex(source, r'"--target-dir",\s*target')

    def test_modified_wrapper_never_starts_a_process(self):
        with tempfile.TemporaryDirectory(prefix="check with ' spaces ") as temporary:
            root = Path(temporary)
            wrapper = root / "apps/android/gradle/wrapper"
            wrapper.mkdir(parents=True)
            (wrapper / "gradle-wrapper.jar").write_bytes(b"modified executable")
            with patch.object(check, "ROOT", root), patch.object(check.subprocess, "run") as run:
                with contextlib.redirect_stderr(io.StringIO()):
                    self.assertEqual(check.main(["android"]), 1)
                run.assert_not_called()

    def test_modified_distribution_and_duplicate_properties_are_rejected(self):
        source = check.ROOT / "apps/android/gradle/wrapper"
        for modification in (
            lambda text: text.replace("gradle-8.11.1-bin.zip", "unexpected.zip"),
            lambda text: text.replace(check.DISTRIBUTION_SHA256, "0" * 64),
            lambda text: text + "\ndistributionUrl=malicious\n",
            lambda text: text + "\nunknownProperty=unexpected\n",
        ):
            with self.subTest(modification=modification), tempfile.TemporaryDirectory() as temporary:
                root = Path(temporary)
                wrapper = root / "apps/android/gradle/wrapper"
                wrapper.mkdir(parents=True)
                (wrapper / "gradle-wrapper.jar").write_bytes((source / "gradle-wrapper.jar").read_bytes())
                original = (source / "gradle-wrapper.properties").read_text(encoding="utf-8")
                (wrapper / "gradle-wrapper.properties").write_text(modification(original), encoding="utf-8")
                with self.assertRaises(ValueError):
                    check.verify_wrapper(root)

    def test_android_uses_java_argv_and_disables_sdk_provisioning(self):
        with patch.object(check, "java_executable", return_value="JDK with ' spaces/bin/java"):
            command, audit, pair = check.android_commands(check.ROOT, True, True)
        self.assertEqual(command.argv[:2], ("JDK with ' spaces/bin/java", "-classpath"))
        self.assertEqual(command.argv[3:5], ("org.gradle.wrapper.GradleWrapperMain", "clean"))
        self.assertIn("--offline", command.argv)
        self.assertIn("-Pandroid.builder.sdkDownload=false", command.argv)
        self.assertNotIn("connectedDebugAndroidTest", " ".join(command.argv))
        self.assertEqual(audit.argv, (sys.executable, str(check.ROOT / "scripts/audit_apk.py"),
                                     str(check.ROOT / "apps/android/app/build/outputs/apk/debug/app-debug.apk")))
        self.assertEqual(pair.argv, (sys.executable, str(check.ROOT / "scripts/audit_instrumentation_apk.py"),
                                    str(check.ROOT / "apps/android/app/build/outputs/apk/debug/app-debug.apk"),
                                    str(check.ROOT / "apps/android/app/build/outputs/apk/androidTest/debug/app-debug-androidTest.apk")))
        self.assertEqual(pair.cwd, check.ROOT)

    def test_java_home_with_spaces_remains_one_executable(self):
        with tempfile.TemporaryDirectory(prefix="JDK with ' spaces ") as temporary:
            java = Path(temporary) / "bin" / ("java.exe" if os.name == "nt" else "java")
            java.parent.mkdir()
            java.touch()
            with patch.dict(os.environ, {"JAVA_HOME": temporary}):
                self.assertEqual(check.java_executable(), str(java))

    def test_interruption_does_not_continue_and_returns_130(self):
        with patch.object(check.subprocess, "run", side_effect=KeyboardInterrupt) as run:
            with contextlib.redirect_stderr(io.StringIO()):
                self.assertEqual(check.main(["host", "--offline"]), 130)
        self.assertEqual(run.call_count, 1)

    def test_missing_command_returns_failure(self):
        with patch.object(check.subprocess, "run", side_effect=FileNotFoundError("missing tool")):
            with contextlib.redirect_stderr(io.StringIO()):
                self.assertEqual(check.main(["host"]), 1)

    def test_invalid_arguments_do_not_start_commands(self):
        for argv in ([], ["unknown"], ["host", "--clean"], ["android", "--install-sdk"]):
            with self.subTest(argv=argv), patch.object(check.subprocess, "run") as run:
                with contextlib.redirect_stderr(io.StringIO()), self.assertRaises(SystemExit) as error:
                    check.main(argv)
                self.assertEqual(error.exception.code, 2)
                run.assert_not_called()

    def test_entrypoint_from_unrelated_directory(self):
        with tempfile.TemporaryDirectory(prefix="outside repository ' ") as temporary:
            result = subprocess.run([sys.executable, str(Path(check.__file__)), "--help"],
                                    cwd=temporary, shell=False, capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("host", result.stdout)

    def test_main_anchors_commands_to_checkout_from_unrelated_cwd(self):
        original = Path.cwd()
        with tempfile.TemporaryDirectory(prefix="outside repository ' ") as temporary:
            try:
                os.chdir(temporary)
                with patch.object(check, "run_commands", return_value=0) as run:
                    self.assertEqual(check.main(["host", "--offline"]), 0)
                self.assertTrue(all(command.cwd == check.ROOT for command in run.call_args.args[0]))
                self.assertTrue(Path(run.call_args.args[0][-1].argv[0]).is_absolute())
            finally:
                os.chdir(original)


if __name__ == "__main__":
    unittest.main()
