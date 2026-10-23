"""Model/device-free checks for selecting exactly the newly built native test artifact."""
import contextlib
import io
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import storage_android_smoke as build
from audit_apk import AuditError

TARGET = "x86_64-linux-android"


class StorageUnitBuildTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.output = Path(self.tmp.name)
        self.binary = self.output / "rust" / TARGET / "release/deps/locallore_storage-current"
        self.binary.parent.mkdir(parents=True)
        self.binary.write_bytes(b"synthetic artifact")
        self.message = {"reason": "compiler-artifact", "target": {"name": "locallore_storage", "kind": ["lib"]},
                        "profile": {"test": True}, "executable": str(self.binary)}

    def select(self, *messages):
        return build.select_unit_artifact("\n".join(json.dumps(m) for m in messages), self.output, TARGET)

    def test_exact_cargo_artifact_wins_over_stale_files(self):
        (self.binary.parent / "locallore_storage-stale").write_bytes(b"stale")
        self.assertEqual(self.select({"reason": "build-finished", "success": True}, self.message), self.binary)

    def test_zero_duplicate_or_non_test_artifacts_fail(self):
        for messages in ([], [self.message, self.message],
                         [{**self.message, "profile": {"test": False}}],
                         [{**self.message, "profile": {"test": 1}}],
                         [{**self.message, "target": {"name": "other", "kind": ["lib"]}}],
                         [{**self.message, "target": {"name": "locallore_storage", "kind": ["example"]}}]):
            with self.subTest(messages=messages), self.assertRaises(AuditError):
                self.select(*messages)

    def test_missing_null_and_malformed_artifact_fail(self):
        for executable in (None, True, str(self.binary.parent / "locallore_storage-absent")):
            with self.subTest(executable=executable), self.assertRaises(AuditError):
                self.select({**self.message, "executable": executable})
        with self.assertRaises(json.JSONDecodeError):
            build.select_unit_artifact("not Cargo JSON", self.output, TARGET)

    def test_existing_wrong_directory_target_and_name_are_refused(self):
        for candidate in (self.output / "outside/locallore_storage-test",
                          self.output / "rust/aarch64-linux-android/release/deps/locallore_storage-test",
                          self.output / "rust" / TARGET / "debug/deps/locallore_storage-test",
                          self.binary.parent / "other-test"):
            candidate.parent.mkdir(parents=True, exist_ok=True)
            candidate.write_bytes(b"wrong artifact")
            with self.subTest(candidate=candidate), self.assertRaises(AuditError):
                self.select({**self.message, "executable": str(candidate)})

    def test_build_is_explicit_offline_no_run_and_uses_cargo_result(self):
        completed = subprocess.CompletedProcess([], 0, json.dumps(self.message))
        environment = {"TASK_SYNTHETIC": "yes"}
        with patch.object(build.subprocess, "run", return_value=completed) as run:
            self.assertEqual(build.unit_test_binary(self.output, TARGET, environment), self.binary)
        args, kwargs = run.call_args
        command = args[0]
        for flag in ("test", "--lib", "--no-run", "--locked", "--offline", "--release", "--message-format=json"):
            self.assertIn(flag, command)
        self.assertEqual(command[command.index("--package") + 1], "locallore-storage")
        self.assertEqual(command[command.index("--target") + 1], TARGET)
        self.assertIs(kwargs["env"], environment)
        self.assertTrue(kwargs["check"])
        self.assertFalse(kwargs["shell"])
        self.assertNotIn("adb", command)

    def test_failed_build_cannot_select_a_stale_executable(self):
        with patch.object(build.subprocess, "run", side_effect=subprocess.CalledProcessError(1, ["cargo"])):
            with self.assertRaises(subprocess.CalledProcessError):
                build.unit_test_binary(self.output, TARGET, {})

    def test_example_and_unit_test_modes_are_mutually_exclusive_before_build(self):
        with patch.object(build, "command") as command, contextlib.redirect_stderr(io.StringIO()):
            with self.assertRaises(SystemExit) as error:
                build.main(["--sdk", str(self.output), "--unit-tests", "--example", "durable_smoke"])
        self.assertEqual(error.exception.code, 2)
        command.assert_not_called()


if __name__ == "__main__":
    unittest.main()
