"""Host-only storage admission wiring; no SDK, emulator or production ledger IO."""
import json
import tempfile
from pathlib import Path
import unittest
from unittest import mock
from benchmarks import receipt_avd_environment as env

class StorageIntegrationTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="locallore-storage-wiring-")
        self.addCleanup(self.temp.cleanup)
        self.base = Path(self.temp.name).resolve()
        self.root = self.base / "guest"
        self.sha = "a" * 64
        self.proposal = {"paths": {"root": str(self.root)}, "max_seconds": 60}
        for name, value in (("digest", self.sha), ("authorize", self.proposal),
                            ("resource_facts", {}), ("process_identity", {"pid": 1})):
            patch = mock.patch.object(env, name, return_value=value)
            patch.start(); self.addCleanup(patch.stop)
        for name in ("verify_prepared", "verify_installation", "check_external_state", "ports_free"):
            patch = mock.patch.object(env, name)
            patch.start(); self.addCleanup(patch.stop)

    def test_prepare_capacity_refusal_precedes_root_and_SDK(self):
        with mock.patch.object(env.guest_storage, "reserve_prepare", side_effect=env.guest_storage.StorageRefused("storage_capacity_exceeded")) as reserve, mock.patch.object(env, "prepare_contents") as child:
            with self.assertRaisesRegex(env.EnvironmentRefused, "^storage_storage_capacity_exceeded$"):
                env.prepare(self.base / "proposal.json", self.base / "authorization.json")
        reserve.assert_called_once_with(self.root, self.sha)
        child.assert_not_called(); self.assertFalse(self.root.exists())

    def test_prepare_reservation_is_before_root_creation_and_success_is_tracked(self):
        observed = []
        def reserve(root, digest):
            observed.append(root.exists())
        with mock.patch.object(env.guest_storage, "reserve_prepare", side_effect=reserve), mock.patch.object(env.guest_storage, "record_state") as state, mock.patch.object(env, "prepare_contents", return_value={"host_fixture": True}):
            env.prepare(self.base / "proposal.json", self.base / "authorization.json")
        self.assertEqual(observed, [False]); state.assert_called_once_with(self.root, "prepared")
        self.assertTrue((self.root / "prepared-v1.json").is_file())

    def test_prepare_failure_preserves_reservation_and_original_error(self):
        with mock.patch.object(env.guest_storage, "reserve_prepare") as reserve, mock.patch.object(env.guest_storage, "record_state") as state, mock.patch.object(env, "prepare_contents", side_effect=env.EnvironmentRefused("prepare_failed")):
            with self.assertRaisesRegex(env.EnvironmentRefused, "^prepare_failed$"):
                env.prepare(self.base / "proposal.json", self.base / "authorization.json")
        reserve.assert_called_once(); state.assert_not_called()
        self.assertEqual(json.loads((self.root / "prepare-result-v1.json").read_text())["status"], "refused")

    def test_run_quota_refusal_precedes_consumption_and_worker(self):
        self.root.mkdir()
        with mock.patch.object(env.guest_storage, "record_state", side_effect=env.guest_storage.StorageRefused("storage_capacity_exceeded")), mock.patch.object(env, "supervise") as worker:
            with self.assertRaises(env.EnvironmentRefused):
                env.run(self.base / "proposal.json", self.base / "authorization.json")
        worker.assert_not_called(); self.assertFalse((self.root / "run-start-v1.json").exists())

    def run_result(self, cleaned):
        self.root.mkdir()
        result = {"status": "child_exited", "cleanup_complete": cleaned,
                  "elapsed_ms": 1, "worker_returncode": 0, "stdout_bytes": 0,
                  "stderr_bytes": 0, "output_capture_complete": True}
        return mock.patch.object(env, "supervise", return_value=result)

    def test_verified_process_closure_is_recorded_after_owner_receipt(self):
        observed = []
        def closed(root, path):
            observed.append(json.loads(path.read_text())["closure_verified"])
        with self.run_result(True), mock.patch.object(env.guest_storage, "record_state") as state, mock.patch.object(env.guest_storage, "record_closed", side_effect=closed):
            result = env.run(self.base / "proposal.json", self.base / "authorization.json")
        self.assertEqual(observed, [True]); self.assertTrue(result["closure_verified"])
        state.assert_called_once_with(self.root, "retained", proposal_sha256=self.sha)
        self.assertFalse(result["guest_flush_claimed"])

    def test_unknown_process_cleanup_never_marks_storage_closed(self):
        with self.run_result(False), mock.patch.object(env.guest_storage, "record_state"), mock.patch.object(env.guest_storage, "record_closed") as closed:
            result = env.run(self.base / "proposal.json", self.base / "authorization.json")
        closed.assert_not_called(); self.assertFalse(result["closure_verified"])
        self.assertEqual(result["status"], "closure_failed")

    def test_storage_module_is_part_of_proposal_source_binding(self):
        with mock.patch.object(env, "safe_path", side_effect=lambda value, **_: Path(value)):
            roster = env.installation_files(self.base / "sdk", self.base / "java")
        self.assertIn(Path(env.guest_storage.__file__).resolve(), roster)

if __name__ == "__main__":
    unittest.main()
