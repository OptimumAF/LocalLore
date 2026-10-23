"""Finite build/audit failure cases. No emulator or SDK execution is simulated."""

import io
import json
from pathlib import Path
import subprocess
import tempfile
import unittest
from unittest.mock import patch
import zipfile

import build


class BuildAuditTests(unittest.TestCase):
    def test_any_requested_permission_fails_closed(self):
        response = subprocess.CompletedProcess([], 0, b"package: org.locallore.runtimebench.litert\nuses-permission: name='android.permission.INTERNET'\n", b"")
        with patch.object(build.subprocess, "run", return_value=response) as run:
            with self.assertRaisesRegex(ValueError, "permissions"):
                build.apk_audit(Path("unused.apk"), Path("unused-sdk"))
        self.assertEqual(run.call_count, 1)

    def test_unexpected_native_library_set_is_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            apk = Path(directory) / "synthetic.apk"
            with zipfile.ZipFile(apk, "w") as archive:
                archive.writestr("lib/arm64-v8a/liblitertlm_jni.so", b"synthetic")
            response = subprocess.CompletedProcess([], 0, b"package: org.locallore.runtimebench.litert\n", b"")
            with patch.object(build.subprocess, "run", return_value=response):
                with self.assertRaisesRegex(ValueError, "native library"):
                    build.apk_audit(apk, Path("unused-sdk"))

    def test_zipalign_failure_propagates(self):
        response = subprocess.CompletedProcess([], 0, b"package: org.locallore.runtimebench.litert\n", b"")
        with patch.object(build.subprocess, "run", side_effect=[response, subprocess.CalledProcessError(1, ["zipalign"])]):
            with self.assertRaises(subprocess.CalledProcessError):
                build.apk_audit(Path("unused.apk"), Path("unused-sdk"))

    def test_dependency_binary_missing_or_changed_cannot_pass(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            manifest = root / "docs/runtime/android/LITERT_DEPENDENCIES_2026-10-22.json"
            manifest.parent.mkdir(parents=True)
            manifest.write_text(json.dumps({"dependencies": [{"coordinate": "synthetic:artifact:1", "artifacts": [{"file": "artifact-1.jar", "sha256": build.hashlib.sha256(b"original").hexdigest()}]}]}))
            cache = root / "cache"
            binary = cache / "caches/modules-2/files-2.1/synthetic/artifact/1/slot/artifact-1.jar"
            with patch.object(build, "ROOT", root), patch.dict(build.os.environ, {"GRADLE_USER_HOME": str(cache)}):
                with self.assertRaisesRegex(ValueError, "identity mismatch"):
                    build.dependency_audit()
                binary.parent.mkdir(parents=True); binary.write_bytes(b"original")
                with patch("sys.stdout", new=io.StringIO()): build.dependency_audit()
                binary.write_bytes(b"changed")
                with self.assertRaisesRegex(ValueError, "identity mismatch"):
                    build.dependency_audit()


if __name__ == "__main__":
    unittest.main()
