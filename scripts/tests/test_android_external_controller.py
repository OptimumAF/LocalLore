"""Synthetic host orchestration only. All SDK/owner observations are mocked."""
import copy
import hashlib
import io
import json
from pathlib import Path
import subprocess
import sys
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import patch

from benchmarks import android_external_controller as external
from scripts.tests import test_android_process_controller_evidence as controller_fixture


class ExternalControllerTests(unittest.TestCase):
    def test_all_case_dispatches_are_create_only_pinned_and_bounded(self):
        for case in external.CASES:
            expected = controller_fixture.pins(case)
            request = dict(case=case, run_id=expected["run_id"])
            operation = external.controller_operation(request, expected)
            self.assertEqual(operation[:7], ["exec-out", "am", "instrument", "--user", "0", "-w", "-r"])
            self.assertEqual(operation[-1], external.driver.CONTROL + "/org.locallore.processverify.ProcessRestoreInstrumentation")
            self.assertIn("create", operation)
            self.assertNotIn("reuse", operation)
            self.assertEqual("fixture_test_sha256" in operation, case in external.RETIRED)

    def test_read_script_has_owner_no_link_and_positive_bounded_fixed_leaf_guards(self):
        body = external.read_script("no_backup/process-verify-v1/0123456789abcdef/saved.json", 12345, 4096)
        self.assertIn("test $(id -u) -eq 12345", body)
        self.assertIn("test ! -L no_backup/process-verify-v1", body)
        self.assertIn("-le 4096", body)
        self.assertIn("-gt 0", body)
        for path in ("/arbitrary", "no_backup/../foreign", "no_backup/./foreign", "no_backup//foreign", "no_backup/file;other"):
            with self.assertRaises(external.ExternalRefused):
                external.read_script(path, 12345, 4096)
        for uid, cap in ((True, 4096), (9999, 4096), (12345, 262145), (12345, True)):
            with self.assertRaises(external.ExternalRefused):
                external.read_script("no_backup/fixed.json", uid, cap)

    def test_transport_requires_exact_original_json_lf_and_both_zero_footers(self):
        bodies = {mode: b'{"synthetic":true}\n' for mode in ("load", "probe", "retire")}
        suffix = b"\nLL_RETIRED_HELPER_EXIT_V1=0\n\nLL_PROCESS_EXIT_V1=0\n"
        wires = {mode: body + suffix for mode, body in bodies.items()}
        external.helper_transports(bodies, wires)
        for changed in (dict(wires, retire=wires["retire"].replace(b"EXIT_V1=0", b"EXIT_V1=1", 1)),
                        dict(wires, retire=wires["retire"] + b"chatter\n"), dict(wires, probe=wires["probe"].replace(b"\n", b"\r\n"))):
            with self.assertRaises(external.ExternalRefused):
                external.helper_transports(bodies, changed)

    def test_host_claim_is_create_only_and_case_independent_per_guest(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            path = root / external.CLAIM
            external.environment.create_json(path, {"case": external.CASES[0]})
            with self.assertRaises(FileExistsError):
                external.environment.create_json(path, {"case": external.CASES[3]})
            self.assertEqual(json.loads(path.read_bytes()), {"case": external.CASES[0]})

    def test_same_guest_reuse_requires_both_lease_paths_and_same_server_pin(self):
        request = dict(running="running", proposal="proposal", sdk="sdk", powershell="ps", server="current")
        gate = dict(request, server="gate")
        with patch.object(external.environment, "read_json", return_value={"pid": 1}):
            self.assertTrue(external.reuse_installation(request, gate))
            self.assertFalse(external.reuse_installation(request, dict(gate, running="other", proposal="other")))
            with self.assertRaises(external.ExternalRefused):
                external.reuse_installation(request, dict(gate, running="other"))
        with patch.object(external.environment, "read_json", side_effect=[{"pid": 1}, {"pid": 2}]):
            with self.assertRaises(external.ExternalRefused):
                external.reuse_installation(request, gate)

    def test_qualified_gate_does_not_trust_passed_label(self):
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / "result-v1.json"
            path.write_text(json.dumps({"version": 1, "phase": "components", "passed": True}))
            with self.assertRaises(external.ExternalRefused):
                external.qualified_gate(path, path)

    def test_json_comparison_distinguishes_bool_integer_and_array_order(self):
        self.assertTrue(external.same_json({"a": [1, True]}, {"a": [1, True]}))
        self.assertFalse(external.same_json({"head": 0}, {"head": False}))
        self.assertFalse(external.same_json([1, 2], [2, 1]))

    def test_session_owner_failure_is_sticky_without_further_client(self):
        session = external.Session.__new__(external.Session)
        session.request, session.sources, session.failed = {}, {}, False
        session.live = SimpleNamespace(check=lambda: (_ for _ in ()).throw(RuntimeError("private")))
        session.capture = SimpleNamespace(clean=True, adb=lambda *a: self.fail("SDK dispatched"))
        with self.assertRaises(external.ExternalRefused):
            session.adb(["get-state"], "state")
        self.assertTrue(session.failed)
        self.assertFalse(session.capture.clean)
        with self.assertRaises(external.ExternalRefused):
            session.check()

    def test_bound_blob_checks_physical_size_before_hash_or_load(self):
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / "blob"
            path.write_bytes(b"more-than-declared")
            with patch.object(external.environment, "check_binding") as check:
                with self.assertRaises(external.ExternalRefused):
                    external.bound_bytes({"path": str(path), "bytes": 1, "sha256": "a" * 64}, path, 4096)
                check.assert_not_called()

    def test_client_records_and_exact_copy_correspondence_are_revalidated(self):
        with tempfile.TemporaryDirectory() as temporary:
            out = Path(temporary)
            (out / "clients").mkdir()
            body = b"original synthetic raw"
            stem = out / "clients/command-0001"
            stem.with_suffix(".stdout.bin").write_bytes(body)
            record = dict(version=1, index=1, label="controller", status="completed", returncode=0, cleanup_complete=True,
                          stdout_bytes=len(body), stdout_sha256=hashlib.sha256(body).hexdigest(), stderr_bytes=0)
            stem.with_suffix(".json").write_text(json.dumps(record))
            external.validate_clients(out, 1, {"controller": body})
            for changes in ({"returncode": False}, {"cleanup_complete": False}, {"stdout_sha256": "a" * 64}, {"index": True}):
                stem.with_suffix(".json").write_text(json.dumps(dict(record, **changes)))
                with self.assertRaises(external.ExternalRefused):
                    external.validate_clients(out, 1, {"controller": body})

    def test_parse_packages_rejects_duplicates_unrelated_or_non_numeric_shape(self):
        package = external.driver.APP
        self.assertEqual(external.parse_packages(("package:" + package + " uid:12345\n").encode()), {package: 12345})
        for raw in (b"package:x uid:True\n", b"package:x uid:9999\n", b"package:x uid:12345\npackage:x uid:12345\n"):
            with self.assertRaises(external.ExternalRefused):
                external.parse_packages(raw)

    def test_no_adoption_of_packages_without_same_guest_gate(self):
        package = external.driver.APP
        session = SimpleNamespace(shell=lambda *a, **k: ("package:" + package + " uid:12345\n").encode(),
                                  adb=lambda *a, **k: self.fail("install dispatched"))
        with self.assertRaises(external.ExternalRefused):
            external.install_or_verify(session, {"apks": []}, False)

    def test_barrier_rejects_bad_request_before_worker_or_sdk(self):
        for data in (b"", b"x" * 4097, b"path\v" + b"a" * 64 + b"\n", b"path\n" + b"a" * 64):
            with patch.object(sys, "argv", ["driver", "_worker"]), patch.object(sys, "stdin", SimpleNamespace(buffer=io.BytesIO(data))), \
                 patch.object(external, "worker") as worker:
                with self.assertRaises(external.ExternalRefused):
                    external.main()
                worker.assert_not_called()

    def test_worker_request_sha_and_source_admission_precede_dispatch(self):
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / "request-v1.json"
            path.write_text(json.dumps({"out": temporary}))
            data = (str(path) + "\n" + "a" * 64 + "\n").encode()
            with patch.object(sys, "argv", ["driver", "_worker"]), patch.object(sys, "stdin", SimpleNamespace(buffer=io.BytesIO(data))), \
                 patch.object(external, "worker") as worker:
                with self.assertRaises(external.environment.EnvironmentRefused):
                    external.main()
                worker.assert_not_called()

    def test_unknown_outer_cleanup_retains_owner_before_any_dependent_validation(self):
        with tempfile.TemporaryDirectory() as temporary:
            out = Path(temporary) / "new"
            request = {key: temporary for key in external.FIELDS}
            request.update(out=str(out), case=external.CASES[0], run_id="0123456789abcdef")
            owner = dict(status="child_exited", worker_returncode=0, cleanup_complete=False,
                         output_capture_complete=True, elapsed_ms=1, stdout_bytes=0, stderr_bytes=0)
            with patch.object(external, "bindings", return_value=[]), patch.object(external, "admit"), \
                 patch.object(external.driver, "source_map", return_value={}), \
                 patch.object(external.environment, "supervise", return_value=owner), \
                 patch.object(external, "validate_execution") as validate:
                with self.assertRaises(external.ExternalRefused):
                    external.supervise(request)
                validate.assert_not_called()
            self.assertEqual(json.loads((out / "owner-result-v1.json").read_bytes()), owner)
            self.assertFalse(json.loads((out / "result-v1.json").read_bytes())["passed"])
            self.assertFalse((out / "sources-after-v1.json").exists())

    def test_isolated_cli_help_is_inert(self):
        result = subprocess.run([sys.executable, "-I", "-B", str(Path(external.__file__)), "--help"],
                                stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=15)
        self.assertEqual(result.returncode, 0)
        self.assertEqual(result.stderr, b"")
        self.assertIn(b"--case", result.stdout)


if __name__ == "__main__":
    unittest.main()
