"""Host-driver regressions; actual Windows binary child plus synthetic refusals.

Copyright 2026 LocalLore contributors. SPDX-License-Identifier: Apache-2.0
"""
import hashlib
import io
import json
import os
from pathlib import Path
import sys
import tempfile
import unittest
from types import SimpleNamespace
from unittest.mock import patch

from benchmarks import android_process_verification as driver


class DriverTests(unittest.TestCase):
    def test_existing_destination_is_never_reused(self):
        with tempfile.TemporaryDirectory() as root:
            path = Path(root)
            marker = path / "original"
            marker.write_bytes(b"keep")
            with self.assertRaises(driver.VerificationRefused):
                driver.output_path(path)
            self.assertEqual(marker.read_bytes(), b"keep")

    def test_evidence_inside_source_is_refused_before_creation(self):
        path = driver.ROOT / "never-create-process-evidence"
        self.assertFalse(path.exists())
        with self.assertRaises(driver.VerificationRefused):
            driver.output_path(path)
        self.assertFalse(path.exists())

    def test_wrong_artifact_package_order_is_refused(self):
        with tempfile.TemporaryDirectory() as root:
            path = Path(root) / "artifacts.json"
            path.write_text(json.dumps({"version": 1, "build_profile": "input-process", "apks":
                [{"package": p} for p in reversed(driver.PACKAGES)]}), encoding="utf-8")
            with self.assertRaises(driver.VerificationRefused):
                driver.checked_apks(path)

    def test_changed_apk_refuses_old_manifest_even_with_same_size(self):
        with tempfile.TemporaryDirectory() as root:
            directory = Path(root)
            apks = []
            for n, package in enumerate(driver.PACKAGES):
                apk = directory / (str(n) + ".apk")
                apk.write_bytes(b"old")
                apks.append(dict(driver.env.binding(apk), package=package))
            path = directory / "artifacts.json"
            path.write_text(json.dumps({"version": 1, "build_profile": "input-process", "apks": apks}))
            driver.checked_apks(path)
            Path(apks[1]["path"]).write_bytes(b"new")
            with self.assertRaises(driver.env.EnvironmentRefused):
                driver.checked_apks(path)

    def test_passed_label_without_owner_and_bound_records_is_refused(self):
        with tempfile.TemporaryDirectory() as root:
            path = Path(root) / "result-v1.json"
            path.write_text(json.dumps({"version": 1, "phase": "build", "passed": True}))
            with self.assertRaises(driver.VerificationRefused):
                driver.qualified_build(path)

    def test_boolean_returncode_cannot_qualify_an_owner(self):
        self.assertFalse(driver.owner_ok(dict(status="child_exited", worker_returncode=False,
            cleanup_complete=True, output_capture_complete=True)))

    def test_worker_source_drift_refuses_before_build_dispatch(self):
        with tempfile.TemporaryDirectory() as root:
            out = Path(root)
            snapshot = out / "sources.json"
            snapshot.write_text(json.dumps({"input": "before"}))
            request = dict(phase="build", out=root, sdk=root, java=root, build=None, running=None,
                proposal=None, server=None, powershell=None, inputs=[], sources=driver.env.binding(snapshot),
                driver_sha256=driver.env.digest(Path(driver.__file__)))
            path = out / "request-v1.json"
            path.write_text(json.dumps(request))
            data = (str(path) + "\n" + driver.env.digest(path) + "\n").encode()
            with patch.object(sys, "argv", ["driver", "_worker"]), \
                 patch.object(sys, "stdin", SimpleNamespace(buffer=io.BytesIO(data))), \
                 patch.object(driver, "source_map", return_value={"input": "after"}), \
                 patch.object(driver, "build_worker") as build:
                with self.assertRaises(driver.VerificationRefused):
                    driver.main()
                build.assert_not_called()

    @unittest.skipUnless(os.name == "nt", "Windows execution path")
    def test_actual_isolated_interpreter_can_load_versioned_driver(self):
        with tempfile.TemporaryDirectory() as root:
            out = Path(root)
            raw = driver.run_command(out, "isolated-help", [sys.executable, "-I", "-B",
                str(Path(driver.__file__)), "--help"], out, dict(os.environ))
            self.assertIn(b"components", raw)

    @unittest.skipUnless(os.name == "nt", "Windows execution path")
    def test_actual_child_bytes_survive_ctrl_z_nul_non_ascii_and_lf(self):
        payload = bytes(range(256)) + b"\x1a\n\x00\xffEND\n"
        with tempfile.TemporaryDirectory() as root:
            out = Path(root)
            command = [sys.executable, "-I", "-B", "-c",
                       "import sys;sys.stdout.buffer.write(bytes.fromhex('" + payload.hex() + "'))"]
            actual = driver.run_command(out, "binary-child", command, out, dict(os.environ))
            self.assertEqual(actual, payload)
            record = json.loads((out / "binary-child.json").read_text())
            self.assertEqual(record["stdout"]["sha256"], hashlib.sha256(payload).hexdigest())
            self.assertEqual(record["stderr"]["bytes"], 0)

    @unittest.skipUnless(os.name == "nt", "Windows execution path")
    def test_actual_child_failure_is_retained_and_not_passed(self):
        with tempfile.TemporaryDirectory() as root:
            out = Path(root)
            with self.assertRaises(driver.VerificationRefused):
                driver.run_command(out, "failed-child", [sys.executable, "-I", "-B", "-c",
                    "import sys;sys.stdout.buffer.write(b'partial');sys.exit(7)"], out, dict(os.environ))
            self.assertEqual((out / "failed-child.stdout.raw").read_bytes(), b"partial")
            self.assertEqual(json.loads((out / "failed-child.json").read_text())["returncode"], 7)

    @unittest.skipUnless(os.name == "nt", "Windows execution path")
    def test_existing_capture_refuses_before_child_spawn(self):
        with tempfile.TemporaryDirectory() as root:
            out = Path(root)
            (out / "existing.stdout.raw").write_bytes(b"keep")
            with patch.object(driver.subprocess, "Popen") as spawn:
                with self.assertRaises(FileExistsError):
                    driver.run_command(out, "existing", [sys.executable], out, dict(os.environ))
                spawn.assert_not_called()
            self.assertEqual((out / "existing.stdout.raw").read_bytes(), b"keep")

    @unittest.skipUnless(os.name == "nt", "Windows execution path")
    def test_actual_output_overflow_is_bounded_and_cannot_pass(self):
        with tempfile.TemporaryDirectory() as root:
            out = Path(root)
            with patch.object(driver, "MAX_COMMAND_BYTES", 512):
                with self.assertRaises(driver.VerificationRefused):
                    driver.run_command(out, "overflow", [sys.executable, "-I", "-B", "-c",
                        "import sys;sys.stdout.buffer.write(b'x'*1000000)"], out, dict(os.environ))
            record = json.loads((out / "overflow.json").read_text())
            self.assertTrue(record["output_limit"])
            self.assertLessEqual(record["stdout"]["bytes"] + record["stderr"]["bytes"], 512)

    @unittest.skipUnless(os.name == "nt", "Windows execution path")
    def test_deadline_refuses_even_when_child_finishes_zero_during_cleanup(self):
        with tempfile.TemporaryDirectory() as root:
            out = Path(root)
            child = SimpleNamespace(stdout=io.BytesIO(b"done"), stderr=io.BytesIO(b""),
                                    poll=lambda: 0, wait=lambda timeout: 0, returncode=0)
            with patch.object(driver.subprocess, "Popen", return_value=child), \
                 patch.object(driver.time, "monotonic", side_effect=[0, 601]):
                with self.assertRaises(driver.VerificationRefused):
                    driver.run_command(out, "late", ["fixed-test-child"], out, dict(os.environ))
            record = json.loads((out / "late.json").read_text())
            self.assertEqual(record["returncode"], 0)
            self.assertTrue(record["timed_out"])

    @unittest.skipUnless(os.name == "nt", "Windows supervisor entry")
    def test_cleanup_failure_and_source_drift_cannot_publish_success(self):
        for cleanup, after in ((False, {"input": "same"}), (True, {"input": "changed"})):
            with self.subTest(cleanup=cleanup, after=after), tempfile.TemporaryDirectory() as root:
                out = Path(root) / "fresh"
                request = dict(phase="build", out=str(out), sdk=root, java=root, build=None,
                               running=None, server=None, powershell=None)
                owner = dict(status="child_exited", worker_returncode=0, cleanup_complete=cleanup,
                             output_capture_complete=True, elapsed_ms=1, stdout_bytes=0, stderr_bytes=0)
                with patch.object(driver, "input_bindings", return_value=[]), \
                     patch.object(driver, "source_map", side_effect=[{"input": "same"}, after]), \
                     patch.object(driver.env, "supervise", return_value=owner):
                    with self.assertRaises(driver.VerificationRefused):
                        driver.supervise(request)
                self.assertEqual(json.loads((out / "owner-result-v1.json").read_text()), owner)
                result = json.loads((out / "result-v1.json").read_text())
                self.assertFalse(result["passed"])
                self.assertNotIn("artifacts", result)


if __name__ == "__main__":
    unittest.main()
