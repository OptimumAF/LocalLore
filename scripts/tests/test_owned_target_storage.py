"""D-only SDK4/SDK5 shared owner storage tests; no SDK, guest or native APIs.

Copyright 2026 LocalLore contributors. SPDX-License-Identifier: Apache-2.0
"""
from contextlib import ExitStack
import copy
from pathlib import Path, PureWindowsPath
import shutil
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import Mock, patch

from benchmarks import owned_target_owner as owner
from benchmarks import owned_restart_owner as restart
from benchmarks import receipt_avd_storage as storage
from scripts.tests import test_owned_target_contract as sdk4_fixture
from scripts.tests import test_owned_restart_contract as sdk5_fixture


class OwnedTargetStorageTests(unittest.TestCase):
    def setUp(self):
        self.assertEqual(Path(tempfile.gettempdir()).drive.upper(), "D:")
        self.temp = tempfile.TemporaryDirectory(prefix="owned-target-storage-", dir="D:/Dev/_Temp")
        self.addCleanup(self.temp.cleanup)
        self.base = Path(self.temp.name)
        self.registry = self.base / "registry"
        self.guest = self.base / "guest"
        self.proposal = self.base / "guest-proposal.json"
        owner.environment.create_json(self.proposal, {"synthetic": True})
        self.proposal_binding = owner.environment.binding(self.proposal)
        self.original_transition = owner.environment.storage_transition

    def transition(self, operation, *args, **kwargs):
        return self.original_transition(operation, *args, registry=self.registry, **kwargs)

    def prepare_tracked(self):
        storage.reserve_prepare(self.guest, "a" * 64, self.registry)
        self.guest.mkdir()
        storage.record_state(self.guest, "prepared", self.registry)

    def entry(self):
        return storage.read_json(self.registry / "ledger-v1.json")["entries"][0]

    def runtime(self, runtime_type):
        runtime = runtime_type.__new__(runtime_type)
        runtime.guard = Mock()
        runtime.proposal = {"synthetic": True}
        runtime.admission = {"guest": {"root": str(self.guest), "proposal": self.proposal_binding}}
        runtime.binding = self.proposal_binding
        runtime.worker = {"pid": 22}
        return runtime

    def test_both_shared_runtimes_reserve_before_boot_claim_or_launch(self):
        self.prepare_tracked()
        for runtime_type in (owner._TargetRuntime, restart._RestartTargetRuntime):
            with self.subTest(runtime=runtime_type.__name__):
                runtime = self.runtime(runtime_type)
                def claim(path, value):
                    self.assertEqual(self.entry()["state"], "retained")
                    self.assertEqual(self.entry()["proposal_sha256"], self.proposal_binding["sha256"])
                    self.assertEqual(self.entry()["reserved_bytes"], 40 * storage.GIB)
                    raise RuntimeError("stop before any SDK launch")
                with patch.object(owner.environment, "verify_prepared"), \
                        patch.object(owner.environment, "storage_transition", side_effect=self.transition), \
                        patch.object(owner.environment, "create_json", side_effect=claim), \
                        patch.object(owner.subprocess, "Popen") as launch:
                    with self.assertRaisesRegex(RuntimeError, "stop before any SDK launch"):
                        runtime.start_guest()
                    launch.assert_not_called()

    def test_untracked_guest_refuses_both_profiles_before_claim_or_launch(self):
        self.guest.mkdir()
        for runtime_type in (owner._TargetRuntime, restart._RestartTargetRuntime):
            with self.subTest(runtime=runtime_type.__name__):
                runtime = self.runtime(runtime_type)
                with patch.object(owner.environment, "verify_prepared"), \
                        patch.object(owner.environment, "storage_transition", side_effect=self.transition), \
                        patch.object(owner.environment, "create_json") as claim, \
                        patch.object(owner.subprocess, "Popen") as launch:
                    with self.assertRaisesRegex(owner.environment.EnvironmentRefused, "^storage_untracked_root$"):
                        runtime.start_guest()
                    claim.assert_not_called()
                    launch.assert_not_called()

    def test_changed_proposal_refuses_before_storage_or_boot_claim(self):
        self.prepare_tracked()
        self.proposal.write_bytes(b"changed source")
        runtime = self.runtime(restart._RestartTargetRuntime)
        with patch.object(owner.environment, "verify_prepared"), \
                patch.object(owner.environment, "storage_transition") as transition, \
                patch.object(owner.environment, "create_json") as claim, \
                patch.object(owner.subprocess, "Popen") as launch:
            with self.assertRaises(owner.environment.EnvironmentRefused):
                runtime.start_guest()
            transition.assert_not_called()
            claim.assert_not_called()
            launch.assert_not_called()

    def run_parent(self, fixture, selected, reader, *, failure=None):
        admission = fixture.admission()
        out = self.base / ("owner-" + selected.PROTOCOL)
        admission["root"] = str(out)
        admission["guest"].update(root=str(self.guest), proposal=self.proposal_binding)
        admission_path = self.base / (selected.PROTOCOL + "-admission.json")
        owner.environment.create_json(admission_path, admission)
        admitted = owner.environment.binding(admission_path)
        process_owner = {"pid": 11, "creation_filetime": 100, "executable": admission["python"]["executable"]["path"]}
        process_worker = {"pid": 22, "creation_filetime": 101, "executable": admission["python"]["executable"]["path"]}
        handles = Mock()
        handles.add.side_effect = [(1, process_owner), (2, process_worker)]
        handles.close.return_value = failure != "handles"
        api = Mock()
        api.identity.return_value = copy.deepcopy(process_owner)
        api.alive.return_value = True
        verified = []
        def verify(*args):
            verified.append(True)
            if failure == "worker":
                raise owner.OwnerRefused("cleanup")
            return {"reason": "stop_requested"}
        def supervise(command, request, output, seconds, started):
            started(SimpleNamespace(pid=22))
            owner.environment.create_json(out / "worker-result-v1.json", {"synthetic": "verified by mocked reader"})
            return {"cleanup_complete": failure != "owner", "synthetic": True}
        def transition(operation, *args, **kwargs):
            self.assertTrue(verified)
            self.assertTrue(handles.close.called)
            self.assertTrue((out / "after-v1.json").is_file())
            if failure == "storage":
                raise owner.environment.EnvironmentRefused("storage_registry_locked")
            return self.transition(operation, *args, **kwargs)
        with ExitStack() as stack:
            stack.enter_context(patch.object(owner.output_control, "validate_output", return_value=out))
            stack.enter_context(patch.object(owner.output_control, "_prepare_environment"))
            stack.enter_context(patch.object(owner, "_inputs"))
            stack.enter_context(patch.object(owner, "_ProcessApi", return_value=api))
            stack.enter_context(patch.object(owner.primitives, "ProcessHandles", return_value=handles))
            stack.enter_context(patch.object(owner.primitives, "_owner_ok", return_value=failure != "owner"))
            stack.enter_context(patch.object(owner.environment, "supervise", side_effect=supervise))
            stack.enter_context(patch.object(owner, "_read_json", side_effect=lambda pin, **_: owner.environment.read_json(pin["path"])))
            stack.enter_context(patch.object(reader, "verify_owned_target_result", side_effect=verify))
            stack.enter_context(patch.object(selected, "source_bindings", return_value=copy.deepcopy(admission["sources"])))
            stack.enter_context(patch.object(owner.file_guard, "_python_bindings", return_value=copy.deepcopy(admission["python"])))
            stack.enter_context(patch.object(owner.environment, "storage_transition", side_effect=transition))
            if failure == "source":
                selected.source_bindings.return_value = []
            elif failure == "storage_source":
                def changed_storage_source():
                    self.assertTrue(verified)
                    self.assertTrue(handles.close.called)
                    changed = copy.deepcopy(admission["sources"])
                    matching = [pin for pin in changed if PureWindowsPath(pin["path"]).name == "receipt_avd_storage.py"]
                    self.assertEqual(len(matching), 1)
                    pin = matching[0]
                    pin["sha256"] = ("0" if pin["sha256"][0] != "0" else "1") + pin["sha256"][1:]
                    self.assertEqual(sum(left != right for left, right in zip(changed, admission["sources"])), 1)
                    return changed
                selected.source_bindings.side_effect = changed_storage_source
            result = owner._parent(admitted, admission, _contract=selected, _verification=reader)
        return result, out

    def test_qualified_sdk4_and_sdk5_close_storage_with_separate_bound_guest_record(self):
        for fixture, selected, reader in (
                (sdk4_fixture, owner.contract, owner.verification),
                (sdk5_fixture, restart.contract, restart.verification)):
            with self.subTest(protocol=selected.PROTOCOL):
                self.registry = self.base / ("registry-" + selected.PROTOCOL)
                self.guest = self.base / ("guest-" + selected.PROTOCOL)
                self.prepare_tracked()
                storage.record_state(self.guest, "retained", self.registry, proposal_sha256=self.proposal_binding["sha256"])
                result, out = self.run_parent(fixture, selected, reader)
                self.assertEqual(result, 0)
                self.assertEqual(self.entry()["state"], "closed")
                closure = self.guest / "guest-storage-closure-v1.json"
                value = owner.environment.read_json(closure)
                self.assertEqual(value["proposal_sha256"], self.proposal_binding["sha256"])
                self.assertTrue(value["cleanup_complete"] and value["closure_verified"])
                for key in ("owner_result", "worker_result", "after"):
                    owner.environment.check_binding(value[key])
                self.assertEqual(owner.environment.read_json(out / "owner-result-v1.json"),
                                 {"cleanup_complete": True, "synthetic": True})
                self.assertLess(self.entry()["reserved_bytes"], 40 * storage.GIB)

    def test_unqualified_or_unknown_cleanup_never_reduces_reservation(self):
        self.prepare_tracked()
        storage.record_state(self.guest, "retained", self.registry, proposal_sha256=self.proposal_binding["sha256"])
        for failure in ("owner", "worker", "handles", "source", "storage"):
            with self.subTest(failure=failure):
                self.base = Path(self.temp.name) / failure
                self.base.mkdir()
                result, out = self.run_parent(sdk5_fixture, restart.contract, restart.verification, failure=failure)
                self.assertEqual(result, 1)
                self.assertFalse(owner.environment.read_json(out / "result-v1.json")["qualified_target"])
                self.assertEqual(self.entry()["state"], "retained")
                self.assertEqual(self.entry()["reserved_bytes"], 40 * storage.GIB)
                closure = self.guest / "guest-storage-closure-v1.json"
                if closure.exists():
                    self.assertEqual(failure, "storage")

    def test_final_parent_storage_source_drift_keeps_full_reservation_for_both_profiles(self):
        for fixture, selected, reader in (
                (sdk4_fixture, owner.contract, owner.verification),
                (sdk5_fixture, restart.contract, restart.verification)):
            with self.subTest(protocol=selected.PROTOCOL):
                self.registry = self.base / ("registry-" + selected.PROTOCOL)
                self.guest = self.base / ("guest-" + selected.PROTOCOL)
                self.prepare_tracked()
                storage.record_state(self.guest, "retained", self.registry, proposal_sha256=self.proposal_binding["sha256"])
                result, out = self.run_parent(fixture, selected, reader, failure="storage_source")
                self.assertEqual(result, 1)
                terminal = owner.environment.read_json(out / "result-v1.json")
                self.assertFalse(terminal["qualified_target"])
                self.assertEqual(terminal["reason"], "source")
                self.assertEqual(self.entry()["state"], "retained")
                self.assertEqual(self.entry()["reserved_bytes"], 40 * storage.GIB)
                self.assertFalse((self.guest / "guest-storage-closure-v1.json").exists())

    def test_missing_storage_source_is_rejected_by_both_actual_admission_validators(self):
        for fixture, selected in ((sdk4_fixture, owner.contract), (sdk5_fixture, restart.contract)):
            with self.subTest(protocol=selected.PROTOCOL):
                admission = fixture.admission()
                selected.validate_admission(admission)
                without_storage = [pin for pin in admission["sources"]
                                   if PureWindowsPath(pin["path"]).name != "receipt_avd_storage.py"]
                self.assertEqual(len(without_storage), len(admission["sources"]) - 1)
                admission["sources"] = without_storage
                with self.assertRaisesRegex(selected.TargetRefused, "source"):
                    selected.validate_admission(admission)

    def test_qualified_closure_external_owner_proof_drift_refuses_all_lifecycle_operations(self):
        original_base = self.base
        for mode in ("mutated", "deleted"):
            with self.subTest(proof=mode):
                self.base = original_base / mode
                self.base.mkdir()
                self.registry, self.guest = self.base / "registry", self.base / "guest"
                self.prepare_tracked()
                image = self.guest / (storage.CONTENT + "cache.img")
                image.parent.mkdir(parents=True)
                image.write_bytes(b"synthetic disposable image")
                storage.record_state(self.guest, "retained", self.registry,
                                     proposal_sha256=self.proposal_binding["sha256"])
                result, out = self.run_parent(sdk5_fixture, restart.contract, restart.verification)
                self.assertEqual(result, 0)
                archive = self.base / "archive"
                archive.mkdir()
                files = []
                for relative, path in storage._files(self.guest).items():
                    if relative in storage.DISPOSABLE:
                        continue
                    target = archive / relative
                    target.parent.mkdir(parents=True, exist_ok=True)
                    shutil.copyfile(str(path), str(target))
                    files.append({"relative": relative, "binding": storage.binding(target)})
                manifest = archive / "manifest.json"
                owner.environment.create_json(manifest, {"version": 1, "root": str(self.guest),
                                                         "complete": True, "files": files})
                plan = storage.plan_retirement(self.guest, manifest, self.registry)
                owner_proof = out / "owner-result-v1.json"
                if mode == "mutated":
                    owner_proof.write_bytes(b"changed external owner proof")
                else:
                    owner_proof.unlink()
                reason = "binding_changed" if mode == "mutated" else "missing_path"
                for operation in (
                        lambda: storage.plan_retirement(self.guest, manifest, self.registry),
                        lambda: storage.reserve_prepare(self.base / "new-guest", "b" * 64, self.registry)):
                    with self.assertRaisesRegex(storage.StorageRefused, "^" + reason + "$"):
                        operation()
                image.unlink()  # Tiny synthetic file only; explicit fixture retirement.
                with self.assertRaisesRegex(storage.StorageRefused, "^" + reason + "$"):
                    storage.record_retired(self.guest, plan, self.registry)
                self.assertEqual(self.entry()["state"], "closed")
                self.assertTrue((self.guest / "guest-storage-closure-v1.json").exists())


if __name__ == "__main__":
    unittest.main()
