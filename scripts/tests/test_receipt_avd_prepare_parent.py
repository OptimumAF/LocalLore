"""Host-only parent preflight; all SDK/resource/storage operations are synthetic mocks.

No production registry, installed SDK, AVD, device or credential is accessed.
Copyright 2026 LocalLore contributors. SPDX-License-Identifier: Apache-2.0
"""
from contextlib import contextmanager
import json
import os
from pathlib import Path
import stat
import tempfile
from types import SimpleNamespace
import unittest
from unittest import mock

from benchmarks import receipt_avd_environment as env


@unittest.skipUnless(os.name == "nt", "Windows parent-path preflight")
class PrepareParentTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="locallore-prepare-parent-", dir="D:/Dev/_Temp")
        self.addCleanup(self.temp.cleanup)
        self.base = Path(self.temp.name).resolve()
        self.sdk = self.base / "synthetic-sdk"
        self.java = self.base / "synthetic-jdk"
        # Only these isolated test fixtures create ancestors, never the production subject.
        factory = self.sdk / "system-images/android-35/google_apis/x86_64/data/empty_data_disk"
        factory.parent.mkdir(parents=True)
        factory.write_bytes(b"synthetic factory file, not an Android image")
        self.java.mkdir()
        self.proposal = self.base / "proposal.json"
        self.authorization = self.base / "authorization.json"
        self.proposal.write_bytes(b'{"synthetic_test_only":true}\n')
        self.authorization.write_bytes(b'{"synthetic_test_only":true}\n')
        self.installation = self.patch(env, "installation_files", return_value=[])
        self.token_path = self.patch(env, "token_path", return_value=str(self.base / "synthetic-token"))
        self.token = self.patch(env, "token_binding", return_value={"synthetic": "no credential"})
        self.old_registry = self.patch(env, "old_registry_snapshot", return_value={"synthetic": True})
        self.authorize = self.patch(env, "authorize")
        self.resources = self.patch(env, "resource_facts", return_value={"synthetic": True})
        self.contents = self.patch(env, "prepare_contents", return_value={"synthetic": "not SDK"})
        self.verify = self.patch(env, "verify_installation")
        self.external = self.patch(env, "check_external_state")
        self.identity = self.patch(env, "process_identity", return_value={"synthetic_pid": 1})
        self.reserve = self.patch(env.guest_storage, "reserve_prepare")
        self.state = self.patch(env.guest_storage, "record_state")
        self.closed = self.patch(env.guest_storage, "record_closed")
        self.retirement = [self.patch(env.guest_storage, name,
            side_effect=AssertionError("No registry retirement is allowed in this test"))
            for name in ("preview_retirement", "plan_retirement", "record_retired")]
        self.locked = self.patch(env.guest_storage, "_locked",
            side_effect=AssertionError("No production ledger access is allowed"))
        self.sdk_child = self.patch(env.host, "run_process",
            side_effect=AssertionError("No real SDK child is allowed"))
        self.run_child = self.patch(env.subprocess, "run",
            side_effect=AssertionError("No subprocess is allowed"))
        self.popen = self.patch(env.subprocess, "Popen",
            side_effect=AssertionError("No subprocess is allowed"))

    def patch(self, owner, name, **kwargs):
        patcher = mock.patch.object(owner, name, **kwargs)
        value = patcher.start()
        self.addCleanup(patcher.stop)
        return value

    @contextmanager
    def reparse(self, parent):
        original = Path.lstat
        def metadata(path, *args, **kwargs):
            if path == parent:
                return SimpleNamespace(st_mode=stat.S_IFDIR | 0o700, st_file_attributes=0x400)
            return original(path, *args, **kwargs)
        with mock.patch.object(Path, "lstat", new=metadata):
            yield

    @staticmethod
    def capture(operation):
        try:
            operation()
        except Exception as error:
            return error
        return None

    def assert_no_runtime_or_registry_effects(self):
        self.state.assert_not_called()
        self.closed.assert_not_called()
        self.locked.assert_not_called()
        for operation in self.retirement:
            operation.assert_not_called()
        self.sdk_child.assert_not_called()
        self.run_child.assert_not_called()
        self.popen.assert_not_called()

    def assert_plan_parent_refused(self, root):
        output = self.base / "planned.json"
        error = self.capture(lambda: env.plan_prepare(root, self.sdk, self.java, output))
        observed = {"error": type(error).__name__ if error else None,
                    "installation": self.installation.call_count,
                    "token": self.token.call_count, "old_registry": self.old_registry.call_count,
                    "proposal_created": output.exists(), "root_created": root.exists()}
        self.assertTrue(isinstance(error, env.EnvironmentRefused) and
            not any((self.installation.call_count, self.token_path.call_count, self.token.call_count,
                     self.old_registry.call_count, output.exists(), root.exists())),
            "Parent must refuse before installed/protected metadata or plan output: " + repr(observed))
        self.authorize.assert_not_called()
        self.resources.assert_not_called()
        self.reserve.assert_not_called()
        self.contents.assert_not_called()
        self.assert_no_runtime_or_registry_effects()

    def assert_prepare_parent_refused(self, root):
        proposal = {"paths": {"root": str(root)}}
        self.authorize.return_value = proposal
        error = self.capture(lambda: env.prepare(self.proposal, self.authorization))
        observed = {"error": type(error).__name__ if error else None,
                    "resource_calls": self.resources.call_count, "reservations": self.reserve.call_count,
                    "prepare_contents": self.contents.call_count, "root_created": root.exists()}
        self.assertTrue(isinstance(error, env.EnvironmentRefused) and
            not any((self.resources.call_count, self.reserve.call_count,
                     self.contents.call_count, root.exists())),
            "Invalid parent must refuse before resources, reservation, creation or SDK: " + repr(observed))
        self.assert_no_runtime_or_registry_effects()

    def test_plan_missing_parent_refuses_before_metadata_and_does_not_create_ancestors(self):
        root = self.base / "absent-experiment" / "guest"
        self.assert_plan_parent_refused(root)
        self.assertFalse(root.parent.exists())

    def test_plan_file_parent_refuses_before_installed_or_protected_metadata(self):
        parent = self.base / "parent-is-a-file"
        parent.write_bytes(b"preserve synthetic parent")
        self.assert_plan_parent_refused(parent / "guest")
        self.assertEqual(parent.read_bytes(), b"preserve synthetic parent")

    def test_plan_reparse_parent_remains_a_refusal_without_metadata_or_output(self):
        parent = self.base / "synthetic-reparse"
        parent.mkdir()
        with self.reparse(parent):
            self.assert_plan_parent_refused(parent / "guest")
        self.assertEqual(list(parent.iterdir()), [])

    def test_plan_ordinary_existing_parent_keeps_the_existing_mocked_plan_flow(self):
        parent = self.base / "ordinary-parent"
        parent.mkdir()
        root = parent / "guest"
        output = self.base / "valid-plan.json"
        value = env.plan_prepare(root, self.sdk, self.java, output)
        self.assertEqual(value["paths"]["root"], str(root))
        self.assertEqual(value["phase"], "prepare")
        self.assertEqual(json.loads(output.read_text(encoding="utf-8")), value)
        self.installation.assert_called_once_with(self.sdk, self.java)
        self.token.assert_called_once()
        self.old_registry.assert_called_once()
        self.assertFalse(root.exists())
        self.assertEqual(list(parent.iterdir()), [])
        self.resources.assert_not_called()
        self.reserve.assert_not_called()
        self.contents.assert_not_called()
        self.assert_no_runtime_or_registry_effects()

    def test_prepare_missing_parent_refuses_controlled_before_resource_probe_or_charge(self):
        root = self.base / "missing-prepare-parent" / "guest"
        self.assert_prepare_parent_refused(root)
        self.assertFalse(root.parent.exists())

    def test_prepare_file_parent_refuses_controlled_without_charge_or_parent_mutation(self):
        parent = self.base / "prepare-file-parent"
        parent.write_bytes(b"preserved ordinary file")
        self.assert_prepare_parent_refused(parent / "guest")
        self.assertEqual(parent.read_bytes(), b"preserved ordinary file")

    def test_prepare_reparse_parent_refuses_before_resource_probe_reservation_and_creation(self):
        parent = self.base / "prepare-reparse-parent"
        parent.mkdir()
        with self.reparse(parent):
            self.assert_prepare_parent_refused(parent / "guest")
        self.assertEqual(list(parent.iterdir()), [])

    def test_prepare_ordinary_parent_reserves_before_creation_and_reaches_only_mocked_contents(self):
        parent = self.base / "existing-prepare-parent"
        parent.mkdir()
        root = parent / "guest"
        self.authorize.return_value = {"paths": {"root": str(root)}}
        observed = []
        def resources(proposal):
            observed.append(("resources", root.exists()))
            return {"synthetic": True}
        def reserve(target, digest):
            self.assertEqual(target, root)
            observed.append(("reserve", root.exists()))
        def contents(*args):
            observed.append(("mocked_contents", root.exists()))
            return {"synthetic": "not SDK"}
        self.resources.side_effect = resources
        self.reserve.side_effect = reserve
        self.contents.side_effect = contents
        self.assertEqual(env.prepare(self.proposal, self.authorization), {"synthetic": "not SDK"})
        self.assertEqual(observed, [("resources", False), ("reserve", False), ("mocked_contents", True)])
        self.state.assert_called_once_with(root, "prepared")
        self.assertTrue((root / "prepare-start-v1.json").is_file())
        result = json.loads((root / "prepare-result-v1.json").read_text(encoding="utf-8"))
        self.assertEqual(result["status"], "completed")
        self.assertFalse(result["child_cleanup_complete"])  # No real or claimed SDK child exists.
        self.closed.assert_not_called()
        self.locked.assert_not_called()
        for operation in self.retirement:
            operation.assert_not_called()
        self.sdk_child.assert_not_called(); self.run_child.assert_not_called(); self.popen.assert_not_called()

    def test_post_reservation_mkdir_or_sdk_failure_never_releases_the_synthetic_charge(self):
        for stage in ("mkdir", "sdk"):
            with self.subTest(stage=stage):
                root = self.base / ("late-failure-" + stage)
                self.authorize.return_value = {"paths": {"root": str(root)}}
                for operation in (self.reserve, self.state, self.closed, self.contents):
                    operation.reset_mock()
                charged = set()
                self.reserve.side_effect = lambda target, digest: charged.add(target)
                fault = OSError("synthetic post-reserve mkdir failure") if stage == "mkdir" \
                    else env.EnvironmentRefused("synthetic_sdk_failure")
                original_mkdir = Path.mkdir
                def mkdir(path, *args, **kwargs):
                    if path == root:
                        raise fault
                    return original_mkdir(path, *args, **kwargs)
                self.contents.side_effect = fault if stage == "sdk" else None
                with mock.patch.object(Path, "mkdir", new=mkdir if stage == "mkdir" else original_mkdir):
                    error = self.capture(lambda: env.prepare(self.proposal, self.authorization))
                self.assertIs(error, fault)
                self.assertEqual(charged, {root})
                self.reserve.assert_called_once_with(root, env.digest(self.proposal))
                self.state.assert_not_called()
                self.closed.assert_not_called()
                self.locked.assert_not_called()
                for operation in self.retirement:
                    operation.assert_not_called()
                if stage == "mkdir":
                    self.contents.assert_not_called()
                    self.assertFalse(root.exists())
                else:
                    self.contents.assert_called_once()
                    result = json.loads((root / "prepare-result-v1.json").read_text(encoding="utf-8"))
                    self.assertEqual(result["status"], "refused")
                    self.assertFalse((root / "prepared-v1.json").exists())
                self.sdk_child.assert_not_called(); self.run_child.assert_not_called(); self.popen.assert_not_called()


if __name__ == "__main__":
    unittest.main()
