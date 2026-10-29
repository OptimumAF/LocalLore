"""Small D-only host fixtures; no SDK, VM, real registry or historical data.

Copyright 2026 LocalLore contributors. SPDX-License-Identifier: Apache-2.0
"""
import ast
import copy
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import threading
import unittest
from unittest import mock

from benchmarks import receipt_avd_storage as storage


class StorageTests(unittest.TestCase):
    def setUp(self):
        self.assertEqual(Path(tempfile.gettempdir()).drive.upper(), "D:")
        self.temp = tempfile.TemporaryDirectory(prefix="locallore-storage-", dir="D:/Dev/_Temp")
        self.addCleanup(self.temp.cleanup)
        self.base = Path(self.temp.name)
        self.registry = self.base / "registry"
        self.root = self.base / "guest"
        self.sha = "a" * 64

    def reserve(self, root=None):
        return storage.reserve_prepare(root or self.root, self.sha, self.registry)

    def write(self, path, value):
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(storage.encoded(value))

    def close_empty(self):
        self.root.mkdir()
        closure = self.root / "prepare-result-v1.json"
        self.write(closure, {"proposal_sha256": self.sha, "closure_verified": True, "child_cleanup_complete": True})
        storage.record_closed(self.root, closure, self.registry)

    def closed_guest(self):
        self.reserve()
        self.root.mkdir()
        for index, relative in enumerate(sorted(storage.DISPOSABLE)):
            path = self.root / relative
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(("image %d" % index).encode("ascii"))
        (self.root / "config.ini").write_bytes(b"original config\n")
        (self.root / "failed-output.bin").write_bytes(b"preserved failed evidence\n")
        closure = self.root / "owner-result-v1.json"
        self.write(closure, {"proposal_sha256": self.sha, "closure_verified": True, "cleanup_complete": True})
        storage.record_closed(self.root, closure, self.registry)
        self.manifest = self.base / "archive" / "manifest.json"
        items = []
        for relative, path in storage._files(self.root).items():
            if relative in storage.DISPOSABLE:
                continue
            target = self.manifest.parent / relative
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(str(path), str(target))
            items.append({"relative": relative, "binding": storage.binding(target)})
        self.write(self.manifest, {"version": 1, "root": str(self.root), "complete": True, "files": items})

    def plan(self):
        return storage.plan_retirement(self.root, self.manifest, self.registry)

    def assert_refused(self, reason, callback):
        with self.assertRaisesRegex(storage.StorageRefused, "^" + reason + "$"):
            callback()

    def test_import_has_no_filesystem_effect_and_python39_syntax(self):
        source = Path(storage.__file__).read_text(encoding="utf-8")
        ast.parse(source, feature_version=(3, 9))
        code = ("from unittest import mock; import pathlib; "
                "p=mock.patch.object(pathlib.Path,'mkdir',side_effect=AssertionError('import IO')); p.start(); "
                "import benchmarks.receipt_avd_storage")
        result = subprocess.run([sys.executable, "-B", "-c", code], capture_output=True, check=False)
        self.assertEqual(result.returncode, 0, result.stderr.decode())
        self.assertFalse(self.registry.exists())

    def test_third_guest_denied_across_unrelated_parents(self):
        self.reserve()
        self.close_empty()
        other = self.base / "unrelated" / "second"
        other.parent.mkdir()
        self.reserve(other)
        self.assert_refused("storage_capacity_exceeded", lambda: self.reserve(self.base / "third"))
        self.assertFalse((self.base / "third").exists())
        ledger = storage.read_json(self.registry / "ledger-v1.json")
        self.assertLessEqual(sum(item["reserved_bytes"] for item in ledger["entries"]), 64 * storage.GIB)
        self.assertEqual(ledger["reservation_bytes"], 40 * storage.GIB)

    def test_interrupted_prepare_reservation_cannot_disappear_or_be_reused(self):
        self.reserve()
        self.assertFalse(self.root.exists())
        self.assert_refused("root_already_tracked", self.reserve)
        self.assert_refused("storage_capacity_exceeded", lambda: self.reserve(self.base / "second"))
        self.assertEqual(len(storage.read_json(self.registry / "ledger-v1.json")["entries"]), 1)

    def test_corrupt_duplicate_or_missing_ledger_fails_closed(self):
        for data in (b"broken", b'{"version":1,"version":1}', b'{}'):
            with self.subTest(data=data):
                if not self.registry.exists():
                    self.reserve()
                (self.registry / "ledger-v1.json").write_bytes(data)
                with self.assertRaises(storage.StorageRefused):
                    self.reserve(self.base / "other")
        (self.registry / "ledger-v1.json").unlink()
        self.assert_refused("ledger_missing", lambda: self.reserve(self.base / "other"))

    def test_missing_prepared_root_blocks_new_admission(self):
        self.reserve()
        self.root.mkdir()
        storage.record_state(self.root, "prepared", self.registry)
        self.root.rmdir()
        self.assert_refused("tracked_root_missing", lambda: self.reserve(self.base / "other"))

    def test_ledger_policy_cannot_be_increased(self):
        self.reserve()
        ledger = storage.read_json(self.registry / "ledger-v1.json")
        ledger["max_guests"] = 100
        self.write(self.registry / "ledger-v1.json", ledger)
        self.assert_refused("invalid_ledger", lambda: self.reserve(self.base / "other"))

    def test_measured_closed_charge_and_reopening_cannot_exceed_budget(self):
        self.reserve()
        self.close_empty()
        ledger = storage.read_json(self.registry / "ledger-v1.json")
        ledger["entries"][0]["reserved_bytes"] = 25 * storage.GIB
        self.write(self.registry / "ledger-v1.json", ledger)
        self.assert_refused("storage_capacity_exceeded", lambda: self.reserve(self.base / "other"))
        ledger["entries"][0]["reserved_bytes"] = 23 * storage.GIB
        self.write(self.registry / "ledger-v1.json", ledger)
        self.reserve(self.base / "other")
        self.assert_refused("storage_capacity_exceeded", lambda: storage.record_state(self.root, "retained", self.registry))
        self.assertEqual(storage.read_json(self.registry / "ledger-v1.json")["entries"][0]["state"], "closed")

    def test_stale_or_live_lock_refuses_without_reclaiming(self):
        self.reserve()
        lock = self.registry / "admission.lock"
        lock.write_bytes(b"stale owner")
        self.assert_refused("registry_locked", lambda: self.reserve(self.base / "other"))
        self.assertEqual(lock.read_bytes(), b"stale owner")

    def test_atomic_replace_failure_preserves_old_reservation(self):
        self.reserve()
        self.close_empty()
        original = (self.registry / "ledger-v1.json").read_bytes()
        with mock.patch.object(storage.os, "replace", side_effect=OSError("synthetic replacement failure")):
            with self.assertRaises(OSError):
                self.reserve(self.base / "other")
        self.assertEqual((self.registry / "ledger-v1.json").read_bytes(), original)
        self.assertFalse((self.base / "other").exists())
        self.assertEqual(list(self.registry.glob("pending-*.json")), [])
        self.assertFalse((self.registry / "admission.lock").exists())
        self.reserve(self.base / "other")

    def test_hardlinked_ledger_and_registry_junction_refused(self):
        self.reserve()
        outside = self.base / "hardlinked-ledger"
        os.link(str(self.registry / "ledger-v1.json"), str(outside))
        self.assert_refused("linked_or_special_file", lambda: self.reserve(self.base / "other"))
        outside.unlink()
        link = self.base / "registry-junction"
        import _winapi
        _winapi.CreateJunction(str(self.registry), str(link))
        try:
            self.assert_refused("linked_path", lambda: storage.reserve_prepare(self.base / "other", self.sha, link))
        finally:
            os.rmdir(str(link))

    def test_concurrent_admissions_never_exceed_cap(self):
        self.reserve()
        self.close_empty()
        results = []
        barrier = threading.Barrier(5)
        def attempt(index):
            barrier.wait()
            try:
                self.reserve(self.base / ("guest-%d" % index))
                results.append("admitted")
            except storage.StorageRefused as error:
                results.append(str(error))
        threads = [threading.Thread(target=attempt, args=(index,)) for index in range(5)]
        for thread in threads:
            thread.start()
        for thread in threads:
            thread.join(timeout=10)
            self.assertFalse(thread.is_alive())
        self.assertEqual(results.count("admitted"), 1)
        self.assertTrue(all(result in ("admitted", "registry_locked", "storage_capacity_exceeded") for result in results))
        self.assertEqual(len(storage.read_json(self.registry / "ledger-v1.json")["entries"]), 2)

    def test_first_registry_is_complete_before_initializer_reaches_lock(self):
        initializer_before_lock = threading.Event()
        contender_finished = threading.Event()
        original_open = storage.os.open
        outcomes = []
        initializer_identity = []
        def pause_initializer(path, flags, mode=0o777, **kwargs):
            if (str(path) == str(self.registry / "admission.lock") and
                    threading.get_ident() == initializer_identity[0]):
                initializer_before_lock.set()
                if not contender_finished.wait(timeout=10):
                    raise AssertionError("contender did not finish")
            return original_open(path, flags, mode, **kwargs)
        def initializer():
            initializer_identity.append(threading.get_ident())
            try:
                self.reserve()
                outcomes.append("admitted")
            except storage.StorageRefused as error:
                outcomes.append(str(error))
        with mock.patch.object(storage.os, "open", side_effect=pause_initializer):
            thread = threading.Thread(target=initializer)
            thread.start()
            try:
                self.assertTrue(initializer_before_lock.wait(timeout=10))
                # This contender used to see the creator's empty registry directory.
                self.reserve(self.base / "contender")
            finally:
                contender_finished.set()
                thread.join(timeout=10)
        self.assertFalse(thread.is_alive())
        self.assertEqual(outcomes, ["storage_capacity_exceeded"])
        ledger = storage.read_json(self.registry / "ledger-v1.json")
        self.assertEqual([entry["root"] for entry in ledger["entries"]], [str(self.base / "contender")])
        self.assertFalse(self.root.exists())

    def test_preexisting_empty_registry_is_not_initialized_implicitly(self):
        self.registry.mkdir()
        self.assert_refused("ledger_missing", self.reserve)
        self.assertFalse((self.registry / "ledger-v1.json").exists())

    def test_initial_publication_never_overwrites_preexisting_directory_race(self):
        original_rename = storage.os.rename
        def create_unknown_directory(source, destination):
            if Path(destination) == self.registry:
                self.registry.mkdir()
            return original_rename(source, destination)
        with mock.patch.object(storage.os, "rename", side_effect=create_unknown_directory):
            self.assert_refused("ledger_missing", self.reserve)
        self.assertEqual(list(self.registry.iterdir()), [])
        self.assertEqual(list(self.base.glob(".registry-initialize-*")), [])

    def test_path_must_be_physical_d_and_no_nested_registration(self):
        self.assert_refused("unsafe_path", lambda: storage.reserve_prepare("C:/never-create-guest", self.sha, self.registry))
        self.reserve()
        self.assert_refused("root_already_tracked", lambda: self.reserve(self.root / "nested"))
        self.assert_refused("overlapping_roots", lambda: storage.reserve_prepare(self.base / "new-registry", self.sha,
                            self.base / "new-registry" / "ledger"))

    def test_exact_nine_image_roster_and_dry_run_preserves_all_bytes(self):
        self.closed_guest()
        before = {name: storage.binding(path) for name, path in storage._files(self.root).items()}
        plan = self.plan()
        self.assertEqual(len(plan["remove"]), 9)
        self.assertEqual({Path(item["path"]).relative_to(self.root).as_posix() for item in plan["remove"]}, storage.DISPOSABLE)
        self.assertEqual(before, {name: storage.binding(path) for name, path in storage._files(self.root).items()})
        self.assertEqual(len(plan["preserve"]), 3)

    def test_active_and_unverified_closures_cannot_retire(self):
        self.reserve()
        self.root.mkdir()
        self.assert_refused("guest_not_closed", lambda: storage.plan_retirement(self.root, self.base / "missing", self.registry))
        closure = self.root / "owner-result-v1.json"
        for closed, cleaned in ((False, True), (True, False), (True, 1)):
            self.write(closure, {"proposal_sha256": self.sha, "closure_verified": closed, "cleanup_complete": cleaned})
            self.assert_refused("closure_unverified", lambda: storage.record_closed(self.root, closure, self.registry))

    def test_prepare_closure_and_distinct_run_digest(self):
        self.reserve()
        self.root.mkdir()
        closure = self.root / "prepare-result-v1.json"
        self.write(closure, {"proposal_sha256": self.sha, "closure_verified": True, "child_cleanup_complete": True})
        storage.record_closed(self.root, closure, self.registry)
        run_sha = "b" * 64
        storage.record_state(self.root, "retained", self.registry, proposal_sha256=run_sha)
        self.assert_refused("closure_unverified", lambda: storage.record_closed(self.root, closure, self.registry))
        self.write(closure, {"proposal_sha256": run_sha, "closure_verified": True, "cleanup_complete": True})
        storage.record_closed(self.root, closure, self.registry)

    def test_adapter_closure_requires_all_four_bound_proofs(self):
        closure = {"proposal_sha256": self.sha, "closure_verified": True, "cleanup_complete": True}
        for key in storage.ADAPTER_PROOFS:
            path = self.base / (key + ".json")
            self.write(path, {"proof": key})
            closure[key] = storage.binding(path)
        storage._closed(closure, self.sha)
        for key in storage.ADAPTER_PROOFS:
            with self.subTest(missing=key):
                incomplete = copy.deepcopy(closure)
                del incomplete[key]
                self.assert_refused("closure_proofs_incomplete", lambda: storage._closed(incomplete, self.sha))
        for key in storage.ADAPTER_PROOFS:
            with self.subTest(changed=key):
                changed = copy.deepcopy(closure)
                changed[key]["sha256"] = "f" * 64
                self.assert_refused("binding_changed", lambda: storage._closed(changed, self.sha))

    def test_adapter_proof_paths_are_charged_once_closed_and_retired(self):
        self.closed_guest()
        closure_path = self.root / "owner-result-v1.json"
        closure = storage.read_json(closure_path)
        outside = self.base / "outside-proof.bin"
        outside.write_bytes(b"declared owner evidence" * 10)
        # Shared outside references and two references to existing guest files
        # demonstrate deduplication against the root roster as well as each other.
        closure.update(admission=storage.binding(outside), owner_result=storage.binding(outside),
                       worker_result=storage.binding(self.root / "config.ini"),
                       after=storage.binding(self.root / "failed-output.bin"))
        self.write(closure_path, closure)
        ledger = storage.read_json(self.registry / "ledger-v1.json")
        ledger["entries"][0].update(state="retained", reserved_bytes=storage.RESERVATION_BYTES,
                                    closure=None, retirement=None)
        self.write(self.registry / "ledger-v1.json", ledger)
        storage.record_closed(self.root, closure_path, self.registry)
        entry = storage.read_json(self.registry / "ledger-v1.json")["entries"][0]
        guest_bytes = sum(path.stat().st_size for path in storage._files(self.root).values())
        self.assertEqual(storage._charge(entry), guest_bytes + outside.stat().st_size)
        # Refresh only this synthetic closure's archived copy and binding.
        manifest = storage.read_json(self.manifest)
        copied = self.manifest.parent / "owner-result-v1.json"
        shutil.copyfile(str(closure_path), str(copied))
        for item in manifest["files"]:
            if item["relative"] == "owner-result-v1.json":
                item["binding"] = storage.binding(copied)
        self.write(self.manifest, manifest)
        plan = self.plan()
        for item in plan["remove"]:
            Path(item["path"]).unlink()
        storage.record_retired(self.root, plan, self.registry)
        entry = storage.read_json(self.registry / "ledger-v1.json")["entries"][0]
        retained = list(storage._files(self.root).values()) + [outside, self.manifest,
                   Path(entry["retirement_receipt"]["path"])] + [Path(item["binding"]["path"]) for item in manifest["files"]]
        self.assertEqual(storage._charge(entry), sum(path.stat().st_size for path in set(retained)))
    def test_run_reopens_closed_state_and_invalidates_old_retirement(self):
        self.closed_guest()
        plan = self.plan()
        storage.record_state(self.root, "retained", self.registry)
        self.assert_refused("guest_not_closed", self.plan)
        self.assert_refused("guest_not_closed", lambda: storage.record_retired(self.root, plan, self.registry))

    def test_evidence_manifest_inside_guest_refused(self):
        self.closed_guest()
        local = self.root / "manifest.json"
        shutil.copyfile(str(self.manifest), str(local))
        self.assert_refused("evidence_inside_guest", lambda: storage.plan_retirement(self.root, local, self.registry))

    def test_missing_tampered_or_incomplete_outside_evidence_refused(self):
        for mode in ("missing", "tampered", "incomplete", "claim"):
            with self.subTest(mode=mode):
                self.closed_guest()
                value = storage.read_json(self.manifest)
                target = Path(value["files"][0]["binding"]["path"])
                if mode == "missing":
                    target.unlink()
                elif mode == "tampered":
                    target.write_bytes(b"tampered")
                elif mode == "incomplete":
                    value["files"].pop()
                    self.write(self.manifest, value)
                else:
                    value["complete"] = False
                    self.write(self.manifest, value)
                with self.assertRaises(storage.StorageRefused):
                    self.plan()
                # Synthetic fixture reset, never actual guest data.
                shutil.rmtree(str(self.root))
                shutil.rmtree(str(self.registry))

    def test_unknown_image_refused_and_new_nonimage_demands_evidence(self):
        self.closed_guest()
        unknown = self.root / (storage.CONTENT + "unexpected.img")
        unknown.write_bytes(b"unknown")
        self.assert_refused("unknown_guest_image", self.plan)
        unknown.unlink()
        (self.root / "new-failed-capture.bin").write_bytes(b"failure")
        self.assert_refused("incomplete_evidence", self.plan)

    def test_hardlinked_guest_and_evidence_refused(self):
        self.closed_guest()
        image = self.root / sorted(storage.DISPOSABLE)[0]
        outside = self.base / "outside-hardlink"
        os.link(str(image), str(outside))
        self.assert_refused("linked_or_special_file", self.plan)
        outside.unlink()
        value = storage.read_json(self.manifest)
        evidence = Path(value["files"][0]["binding"]["path"])
        os.link(str(evidence), str(outside))
        self.assert_refused("linked_or_special_file", self.plan)

    def test_symlink_or_windows_junction_refused(self):
        self.closed_guest()
        outside = self.base / "outside-directory"
        outside.mkdir()
        link = self.root / "linked-directory"
        try:
            os.symlink(str(outside), str(link), target_is_directory=True)
        except OSError:
            # Junctions do not require Windows developer-mode symlink privileges.
            import _winapi
            _winapi.CreateJunction(str(outside), str(link))
        try:
            self.assert_refused("linked_path", self.plan)
        finally:
            if link.is_symlink():
                link.unlink()
            else:
                os.rmdir(str(link))

    def test_retirement_requires_exact_pinned_plan_and_all_images_absent(self):
        self.closed_guest()
        plan = self.plan()
        changed = copy.deepcopy(plan)
        changed["remove"].pop()
        self.assert_refused("retirement_plan_changed", lambda: storage.record_retired(self.root, changed, self.registry))
        self.assert_refused("images_remain", lambda: storage.record_retired(self.root, plan, self.registry))
        Path(plan["remove"][0]["path"]).unlink()
        self.assert_refused("images_remain", lambda: storage.record_retired(self.root, plan, self.registry))

    def test_external_synthetic_retirement_releases_one_slot_and_keeps_tombstone(self):
        self.closed_guest()
        plan = self.plan()
        self.reserve(self.base / "second")
        for item in plan["remove"]:
            Path(item["path"]).unlink()  # Explicit fixture-only host operation.
        storage.record_retired(self.root, plan, self.registry)
        self.close_second = self.base / "second"
        self.close_second.mkdir()
        closure = self.close_second / "prepare-result-v1.json"
        self.write(closure, {"proposal_sha256": self.sha, "closure_verified": True, "child_cleanup_complete": True})
        storage.record_closed(self.close_second, closure, self.registry)
        self.reserve(self.base / "third")
        entry = storage.read_json(self.registry / "ledger-v1.json")["entries"][0]
        self.assertEqual(entry["state"], "retired")
        self.assertEqual(entry["retirement"], plan)
        self.assertTrue((self.root / "failed-output.bin").exists())
        self.assertTrue((self.root / "config.ini").exists())
        self.assert_refused("target_exists", self.reserve)

    def test_changed_preserved_files_prevent_retirement_acknowledgement(self):
        self.closed_guest()
        plan = self.plan()
        for item in plan["remove"]:
            Path(item["path"]).unlink()
        (self.root / "failed-output.bin").write_bytes(b"changed")
        self.assert_refused("binding_changed", lambda: storage.record_retired(self.root, plan, self.registry))

    def test_corrupt_retired_state_cannot_release_quota_while_images_remain(self):
        self.closed_guest()
        ledger = storage.read_json(self.registry / "ledger-v1.json")
        ledger["entries"][0].update(state="retired", closure={}, retirement={})
        self.write(self.registry / "ledger-v1.json", ledger)
        with self.assertRaises(storage.StorageRefused):
            self.reserve(self.base / "must-not-be-admitted")
        self.assertFalse((self.base / "must-not-be-admitted").exists())
        self.assertTrue(all((self.root / relative).exists() for relative in storage.DISPOSABLE))

    def retire_fixture(self):
        self.closed_guest()
        plan = self.plan()
        for item in plan["remove"]:
            Path(item["path"]).unlink()
        storage.record_retired(self.root, plan, self.registry)
        return plan

    def test_retired_entry_rechecks_images_before_charge_or_new_admission(self):
        self.retire_fixture()
        image = self.root / sorted(storage.DISPOSABLE)[0]
        image.write_bytes(b"resurrected guest image")
        entry = storage.read_json(self.registry / "ledger-v1.json")["entries"][0]
        self.assert_refused("images_remain", lambda: storage._charge(entry))
        self.assert_refused("images_remain", lambda: self.reserve(self.base / "must-not-be-admitted"))

    def test_retired_root_and_declared_archive_remain_charged_to_budget(self):
        # Small accounting units test real files/hashes without allocating GiB fixtures.
        with mock.patch.object(storage, "RESERVATION_BYTES", 10000), mock.patch.object(storage, "BUDGET_BYTES", 20000):
            self.retire_fixture()
            ledger = storage.read_json(self.registry / "ledger-v1.json")
            entry = ledger["entries"][0]
            guest_bytes = sum(path.stat().st_size for path in storage._files(self.root).values())
            evidence_paths = {str(path).casefold(): path for path in (
                [Path(item["binding"]["path"]) for item in storage.read_json(self.manifest)["files"]] +
                [self.manifest, Path(entry["retirement_receipt"]["path"])])}
            expected = guest_bytes + sum(path.stat().st_size for path in evidence_paths.values())
            self.assertGreater(expected, guest_bytes)
            self.assertEqual(storage._charge(entry), expected)
            # Exact accounting threshold refuses an otherwise fitting fresh reservation.
            ledger["budget_bytes"] = expected + storage.RESERVATION_BYTES - 1
            self.write(self.registry / "ledger-v1.json", ledger)
            with mock.patch.object(storage, "BUDGET_BYTES", ledger["budget_bytes"]):
                self.assert_refused("storage_capacity_exceeded", lambda: self.reserve(self.base / "other"))
            ledger["budget_bytes"] += 1
            self.write(self.registry / "ledger-v1.json", ledger)
            with mock.patch.object(storage, "BUDGET_BYTES", ledger["budget_bytes"]):
                self.reserve(self.base / "other")

    def test_retired_evidence_or_tombstone_drift_blocks_admission(self):
        self.retire_fixture()
        ledger = storage.read_json(self.registry / "ledger-v1.json")
        receipt = ledger["entries"][0]["retirement_receipt"]
        path = Path(receipt["path"])
        original = path.read_bytes()
        path.write_bytes(b"{}")
        self.assert_refused("binding_changed", lambda: self.reserve(self.base / "other"))
        path.write_bytes(original)
        evidence = Path(storage.read_json(self.manifest)["files"][0]["binding"]["path"])
        evidence.write_bytes(b"tampered after finalization")
        self.assert_refused("binding_changed", lambda: self.reserve(self.base / "other"))

    def test_retired_preserved_guest_file_drift_blocks_admission(self):
        self.retire_fixture()
        (self.root / "failed-output.bin").write_bytes(b"tampered after finalization")
        self.assert_refused("binding_changed", lambda: self.reserve(self.base / "other"))

    def test_retirement_receipt_before_failed_ledger_write_is_recoverable_without_freeing_quota(self):
        self.closed_guest()
        plan = self.plan()
        for item in plan["remove"]:
            Path(item["path"]).unlink()
        with mock.patch.object(storage.os, "replace", side_effect=OSError("synthetic finalization failure")):
            with self.assertRaises(OSError):
                storage.record_retired(self.root, plan, self.registry)
        self.assertEqual(storage.read_json(self.registry / "ledger-v1.json")["entries"][0]["state"], "closed")
        self.assertEqual(len(list(self.registry.glob("retired-*.json"))), 1)
        storage.record_retired(self.root, plan, self.registry)
        self.assertEqual(storage.read_json(self.registry / "ledger-v1.json")["entries"][0]["state"], "retired")

    def test_unreadable_subtree_blocks_planning_admission_and_finalization(self):
        self.closed_guest()
        hidden = self.root / "unreadable-state"
        hidden.mkdir()
        (hidden / "private-state.bin").write_bytes(b"must never be omitted")
        original_scandir = os.scandir
        def deny_hidden(path):
            if Path(path) == hidden:
                raise PermissionError("synthetic unreadable subtree")
            return original_scandir(path)
        with mock.patch.object(storage.os, "scandir", side_effect=deny_hidden):
            self.assert_refused("guest_tree_unreadable", self.plan)
            self.assert_refused("guest_tree_unreadable", lambda: self.reserve(self.base / "other"))
        # Add the previously inaccessible evidence, then obtain a valid pinned plan.
        target = self.manifest.parent / "unreadable-state" / "private-state.bin"
        target.parent.mkdir()
        shutil.copyfile(str(hidden / "private-state.bin"), str(target))
        manifest = storage.read_json(self.manifest)
        manifest["files"].append({"relative": "unreadable-state/private-state.bin", "binding": storage.binding(target)})
        self.write(self.manifest, manifest)
        plan = self.plan()
        for item in plan["remove"]:
            Path(item["path"]).unlink()
        with mock.patch.object(storage.os, "scandir", side_effect=deny_hidden):
            self.assert_refused("guest_tree_unreadable", lambda: storage.record_retired(self.root, plan, self.registry))
        self.assertEqual(storage.read_json(self.registry / "ledger-v1.json")["entries"][0]["state"], "closed")


if __name__ == "__main__":
    unittest.main()
