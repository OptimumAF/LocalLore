"""Recovery protocol attacks on tiny isolated D: ledgers; no SDK or native-fence claims.

The directory port below models atomic creation/identity only. Separate native
tests qualify the Windows handle fence. No import operates the production ledger.
Copyright 2026 LocalLore contributors. SPDX-License-Identifier: Apache-2.0
"""
import hashlib
import os
from pathlib import Path
import shutil
import tempfile
import threading
import unittest
from unittest import mock

from benchmarks import receipt_avd_environment as env
from benchmarks import receipt_avd_prepare_recovery as recovery
from benchmarks import receipt_avd_storage as storage
from benchmarks import prepare_recovery_contract as contract


class DirectoryPort:
    """Synthetic port, never evidence of a real held Windows handle."""
    def __init__(self, fixture):
        self.fixture = fixture
        self.held = []
    def hold(self, value):
        path = storage.safe_path(value, exists=True, directory=True)
        info = path.stat()
        self.held.append((path, info.st_dev, info.st_ino))
    def create(self, value):
        path = Path(value)
        if self.fixture.fail_create == path:
            raise self.fixture.fault
        path.mkdir()
        self.hold(path)
    def verify(self):
        for path, device, inode in self.held:
            info = storage.safe_path(path, exists=True, directory=True).stat()
            if (info.st_dev, info.st_ino) != (device, inode):
                raise RuntimeError("synthetic directory identity changed")
    def close(self):
        return self.fixture.close_known


@unittest.skipUnless(os.name == "nt", "D-only Windows preparation protocol")
class PrepareRecoveryAdversaries(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="locallore-recovery-attacks-", dir="D:/Dev/_Temp")
        self.addCleanup(self.temp.cleanup)
        self.base = Path(self.temp.name).resolve()
        self.registry = self.base / "registry"
        self.root = self.base / "experiment" / "avd-v1"
        self.sdk = self.base / "synthetic-sdk"; self.sdk.mkdir()
        self.java = self.base / "synthetic-jdk"; self.java.mkdir()
        self.legacy = self.base / "legacy" / "receipt_avd_environment.py"
        self.legacy.parent.mkdir(); self.legacy.write_bytes(b"synthetic reviewed reserve -> mkdir -> SDK source\n")
        self.operator = self.base / "operator.txt"
        self.operator.write_bytes(b"Synthetic operator observation; not process closure or a device result.\n")
        self.token = self.base / "synthetic-console-token"
        self.token.write_bytes(b"synthetic test token, not a credential")
        current = self.base / "current-sources"; current.mkdir()
        for name in contract.SOURCE_NAMES:
            (current / name).write_bytes(("synthetic current source " + name + "\n").encode("ascii"))
        self.sources = [storage.binding(current / name) for name in sorted(contract.SOURCE_NAMES)]
        self.source_patch = self.patch(recovery, "_sources", return_value=self.sources)
        self.patch(contract, "LEGACY_MKDIR_SOURCES", frozenset((storage.binding(self.legacy)["sha256"],)))
        # A closed synthetic control plus the failed preparing root models both live slots.
        self.other = self.base / "closed-control"
        storage.reserve_prepare(self.other, "b" * 64, registry=self.registry)
        self.other.mkdir()
        self.write(self.other / "closure.json", dict(proposal_sha256="b" * 64,
            closure_verified=True, child_cleanup_complete=True))
        storage.record_closed(self.other, self.other / "closure.json", registry=self.registry)
        self.prior = self.base / "prior-proposal.json"
        self.write(self.prior, dict(phase="prepare", sdk=str(self.sdk), java_home=str(self.java),
            paths=env.paths(self.root), memory_mib=8192, cores=4,
            host_available_memory_min=12 * storage.GIB, bindings=[storage.binding(self.legacy)]))
        self.old_entry = storage.reserve_prepare(self.root, self.pin(self.prior)["sha256"], registry=self.registry)
        self.failure = self.base / "observed-failure.json"
        self.failure_value = dict(version=1, scope="sdk14-prepare-observed-failure-v1",
            status="failed-spent-no-retry", exception_type="FileNotFoundError", winerror=3,
            site="receipt_avd_environment.prepare:synthetic root.mkdir()", sdk_worker_reached=False,
            guest_root_exists=False, proposal=self.pin(self.prior), entry=self.old_entry,
            provenance="Synthetic old-mkdir observation, never a process-closure proof", operator=self.pin(self.operator))
        self.write(self.failure, self.failure_value)
        self.immutable = {path: path.read_bytes() for path in (self.prior, self.legacy, self.failure, self.operator)}
        self.sequence = 0; self.fail_create = None; self.close_known = True
        self.fault = OSError("synthetic recovery interruption")
        self.fences = []
        def fence():
            value = DirectoryPort(self); self.fences.append(value); return value
        self.patch(recovery, "DirectoryFence", side_effect=fence)
        self.resources = self.patch(env, "resource_facts", return_value={"synthetic_resources": True})
        self.patch(env, "process_identity", return_value=dict(pid=7, creation_filetime=11,
            executable="D:/synthetic/python.exe"))
        self.patch(env, "token_path", return_value=str(self.token))
        self.patch(env, "verify_installation")
        self.patch(env, "check_external_state")
        self.builder = self.patch(env, "_prepare_proposal_value", side_effect=self.current_proposal)
        self.worker = self.patch(env, "prepare_contents", side_effect=self.synthetic_worker)
        self.real_locked = storage._locked
        def isolated_locked(registry):
            self.assertEqual(Path(registry), self.registry, "No production registry may be accessed")
            return self.real_locked(registry)
        self.patch(storage, "_locked", side_effect=isolated_locked)
        self.patch(env.host, "run_process", side_effect=AssertionError("No SDK process"))
        self.patch(env.subprocess, "run", side_effect=AssertionError("No subprocess"))
        self.patch(env.subprocess, "Popen", side_effect=AssertionError("No subprocess"))

    def patch(self, owner, name, value=mock.DEFAULT, **kwargs):
        item = mock.patch.object(owner, name, value, **kwargs)
        result = item.start(); self.addCleanup(item.stop); return result
    @staticmethod
    def write(path, value):
        path.write_bytes(storage.encoded(value))
    @staticmethod
    def pin(path):
        raw = path.read_bytes()
        return dict(path=str(path), bytes=len(raw), sha256=hashlib.sha256(raw).hexdigest())
    def ledger(self):
        return storage.read_json(self.registry / "ledger-v1.json")
    def entry(self):
        return next(row for row in self.ledger()["entries"] if row["root"] == str(self.root))
    def ledger_bytes(self):
        return (self.registry / "ledger-v1.json").read_bytes()
    def assert_old_evidence(self):
        for path, raw in self.immutable.items():
            self.assertEqual(path.read_bytes(), raw)
    def assert_charge(self, state=None):
        ledger = self.ledger(); row = self.entry()
        self.assertEqual(len(ledger["entries"]), 2)
        self.assertEqual(row["reserved_bytes"], 40 * storage.GIB)
        if state is not None:
            self.assertEqual(row["state"], state)
        self.assertEqual(next(e for e in ledger["entries"] if e["root"] == str(self.other))["state"], "closed")
    def make_plan(self):
        path = self.base / "plan.json"
        value = recovery.plan(self.root, self.failure, path, registry=self.registry)
        auth = self.base / "recovery-authorization.json"
        self.write(auth, dict(version=1, action=contract.ACTION, plan_sha256=self.pin(path)["sha256"],
            allow_sdk_prepare=True, accept_operator_observation=True))
        return path, auth, value
    def execute(self, path, auth):
        self.sequence += 1
        return recovery.execute(path, auth, self.base / ("run-" + str(self.sequence)), registry=self.registry)
    def current_proposal(self, root, sdk, java_home, real_candidate=False, four_core_candidate=False):
        self.assertTrue(real_candidate); self.assertTrue(four_core_candidate)
        self.assertTrue(contract.claim_path(self.registry, self.root).is_file())
        self.assertTrue(self.root.is_dir())
        self.assertEqual(Path(root), self.root)
        self.assertEqual((sdk, java_home), (str(self.sdk), str(self.java)))
        files = [Path(env.__file__).resolve(), Path(env.host.__file__).resolve(),
                 Path(env.commit_capacity.__file__).resolve(), Path(env.guest_storage.__file__).resolve(),
                 Path(contract.__file__).resolve()]
        for relative in ("platform-tools/adb.exe", "emulator/emulator.exe", "cmdline-tools/latest/bin/avdmanager.bat",
                         "system-images/android-35/google_apis/x86_64/data/empty_data_disk"):
            path = self.sdk / relative; path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(b"synthetic SDK marker; never executable")
            files.append(path)
        return dict(version=1, phase="prepare", avd_name=env.NAME, serial="emulator-5592", console_port=5592,
            sdk=str(self.sdk), java_home=str(self.java), paths=env.paths(self.root),
            adb_path=str(self.sdk / "platform-tools/adb.exe"), token=self.pin(self.token),
            old_avd={"synthetic": True}, bindings=[self.pin(p) for p in files],
            userdata_mib=12288, sdcard_mib=8192, memory_mib=8192, cores=4,
            host_free_min=env.root_free_min(self.root), host_available_memory_min=12 * storage.GIB,
            allow_environment_calls=False, root_go_pending=True)
    def synthetic_worker(self, proposal, *_):
        self.assertEqual(proposal["paths"]["root"], str(self.root))
        self.write(self.root / "prepare-client-v1.json", dict(cleanup_complete=True, synthetic=True))
        return {"synthetic_child": "protocol fixture only, not an SDK or cleanup qualification"}
    def successful(self):
        path, auth, plan = self.make_plan(); result = self.execute(path, auth)
        self.assertEqual(result["status"], "completed")
        self.assertEqual(self.builder.call_count, 1); self.assertEqual(self.worker.call_count, 1)
        self.assert_charge("prepared")
        self.assertEqual(self.ledger()["version"], 2)
        self.assertNotEqual(self.entry()["proposal_sha256"], self.old_entry["proposal_sha256"])
        self.assertIsNone(self.entry()["closure"])
        self.assertFalse((self.root / "guest-storage-closure-v1.json").exists())
        self.assert_old_evidence()
        return path, auth, plan

    def test_plan_is_snapshot_only_and_does_not_initialize_or_discount_any_root(self):
        before = self.ledger_bytes(); names = sorted(p.name for p in self.registry.iterdir())
        path, _, plan = self.make_plan()
        self.assertEqual(plan["parent_mode"], "create_one")
        self.assertEqual(plan["prior_entry"], self.old_entry)
        self.assertTrue(path.is_file()); self.assertEqual(before, self.ledger_bytes())
        self.assertEqual(names, sorted(p.name for p in self.registry.iterdir()))
        self.assertFalse(self.root.parent.exists()); self.assertFalse(self.root.exists())
        self.assertFalse(self.fences); self.resources.assert_not_called()
        self.builder.assert_not_called(); self.worker.assert_not_called(); self.assert_old_evidence()

    def test_absent_root_without_observed_failure_is_not_recovery_authority(self):
        before = self.ledger_bytes()
        with self.assertRaises(storage.StorageRefused):
            recovery.plan(self.root, self.base / "missing-proof.json", self.base / "bad-plan.json", registry=self.registry)
        self.assertEqual(before, self.ledger_bytes()); self.assertFalse(self.root.parent.exists())
        self.worker.assert_not_called(); self.builder.assert_not_called()

    def test_uncertain_stage_sdk_reached_boolean_or_unreviewed_source_cannot_make_a_plan(self):
        changes = [dict(exception_type="RuntimeError"), dict(winerror=None), dict(sdk_worker_reached=True),
                   dict(guest_root_exists=True), dict(site="prepare: SDK worker"), dict(provenance=""),
                   dict(winerror=True), dict(version=True)]
        before = self.ledger_bytes()
        for index, change in enumerate(changes):
            with self.subTest(change=change):
                self.write(self.failure, dict(self.failure_value, **change))
                with self.assertRaises(storage.StorageRefused):
                    recovery.plan(self.root, self.failure, self.base / ("bad-stage-" + str(index)), registry=self.registry)
                self.assertEqual(before, self.ledger_bytes()); self.assertFalse(self.root.parent.exists())
        self.write(self.failure, self.failure_value)
        with mock.patch.object(contract, "LEGACY_MKDIR_SOURCES", frozenset()):
            with self.assertRaises(storage.StorageRefused):
                recovery.plan(self.root, self.failure, self.base / "unreviewed-plan", registry=self.registry)
        self.worker.assert_not_called(); self.builder.assert_not_called(); self.assert_old_evidence()

    def test_missing_stale_extra_or_integer_authorization_cannot_consume_a_claim(self):
        path, auth, _ = self.make_plan(); original = storage.read_json(auth); before = self.ledger_bytes()
        with self.assertRaises(storage.StorageRefused):
            self.execute(path, self.base / "missing-authorization")
        changes = [dict(plan_sha256="f" * 64), dict(allow_sdk_prepare=False), dict(accept_operator_observation=False),
                   dict(allow_sdk_prepare=1), dict(accept_operator_observation=1), dict(version=True), dict(extra=True)]
        for change in changes:
            with self.subTest(change=change):
                self.write(auth, dict(original, **change))
                with self.assertRaises(storage.StorageRefused): self.execute(path, auth)
                self.assertEqual(before, self.ledger_bytes())
                self.assertFalse(contract.claim_path(self.registry, self.root).exists())
        self.assertFalse(self.root.parent.exists()); self.worker.assert_not_called(); self.builder.assert_not_called()

    def test_old_entry_and_each_bound_evidence_or_source_drift_refuse_without_mutation(self):
        path, auth, _ = self.make_plan(); original_ledger = self.ledger_bytes()
        changed = self.ledger(); next(e for e in changed["entries"] if e["root"] == str(self.root))["proposal_sha256"] = "c" * 64
        self.write(self.registry / "ledger-v1.json", changed)
        before = self.ledger_bytes()
        with self.assertRaises(storage.StorageRefused): self.execute(path, auth)
        self.assertEqual(before, self.ledger_bytes())
        (self.registry / "ledger-v1.json").write_bytes(original_ledger)
        for source in (self.prior, self.legacy, self.failure, self.operator, Path(self.sources[0]["path"])):
            with self.subTest(source=source.name):
                raw = source.read_bytes(); source.write_bytes(raw + b"\n")
                try:
                    with self.assertRaises(storage.StorageRefused): self.execute(path, auth)
                    self.assertEqual(original_ledger, self.ledger_bytes())
                finally: source.write_bytes(raw)
        self.worker.assert_not_called(); self.builder.assert_not_called()
        self.assertFalse(contract.claim_path(self.registry, self.root).exists()); self.assert_old_evidence()

    def test_existing_guest_is_never_adopted_even_with_the_bound_old_failure(self):
        path, auth, _ = self.make_plan(); before = self.ledger_bytes()
        self.root.parent.mkdir(); self.root.mkdir(); sentinel = self.root / "preserve.txt"
        sentinel.write_bytes(b"synthetic foreign root")
        with self.assertRaises(storage.StorageRefused): self.execute(path, auth)
        self.assertEqual(sentinel.read_bytes(), b"synthetic foreign root")
        self.assertEqual(before, self.ledger_bytes()); self.worker.assert_not_called()

    def test_success_creates_only_the_declared_parent_and_rebinds_same_two_root_charge(self):
        self.successful()
        self.assertTrue(self.root.parent.is_dir())
        self.assertTrue(self.root.is_dir())
        self.assertEqual(len(self.fences), 1)

    def test_existing_ordinary_parent_uses_the_same_one_use_prepared_flow(self):
        self.root.parent.mkdir()
        _, _, plan = self.successful()
        self.assertEqual(plan["parent_mode"], "existing")

    def spent_failure(self, stage):
        path, auth, _ = self.make_plan(); fault = OSError("synthetic failure at " + stage)
        if stage == "intent":
            original = storage._atomic_write
            def atomic(target, value):
                if Path(target) == self.registry / "ledger-v1.json" and value["version"] == 2:
                    raise fault
                return original(target, value)
            patcher = mock.patch.object(storage, "_atomic_write", side_effect=atomic)
        elif stage == "mkdir":
            self.fail_create = self.root.parent; self.fault = fault
            patcher = mock.patch.object(self, "close_known", True)
        elif stage == "rebind": patcher = mock.patch.object(recovery, "_rebind", side_effect=fault)
        else: patcher = mock.patch.object(self.worker, "side_effect", fault)
        with patcher, self.assertRaises(OSError) as caught:
            self.execute(path, auth)
        self.assertIs(caught.exception, fault)
        self.assertTrue(contract.claim_path(self.registry, self.root).is_file())
        self.assert_charge("preparing")
        before = self.worker.call_count
        with self.assertRaises(storage.StorageRefused): self.execute(path, auth)
        self.assertEqual(before, self.worker.call_count)
        self.assert_old_evidence()
        return path, auth

    def test_intent_publication_interruption_is_spent_even_before_migration_finishes(self):
        self.spent_failure("intent")
        self.assertFalse(self.root.exists()); self.builder.assert_not_called(); self.worker.assert_not_called()
        with self.assertRaises(storage.StorageRefused): storage._validate(self.ledger(), self.registry)

    def test_atomic_directory_failure_is_spent_and_cannot_be_retried(self):
        self.spent_failure("mkdir")
        self.assertFalse(self.root.parent.exists()); self.builder.assert_not_called(); self.worker.assert_not_called()

    def test_pre_rebind_failure_keeps_installed_old_digest_and_root_removal_cannot_reset_it(self):
        path, auth = self.spent_failure("rebind")
        entry = self.entry()
        self.assertEqual(entry["proposal_sha256"], self.old_entry["proposal_sha256"])
        outcome = storage.read_json(entry["recovery"]["outcome"]["path"])
        self.assertEqual(outcome["proposal_sha256"], entry["proposal_sha256"])
        storage._validate(self.ledger(), self.registry)
        before = self.ledger_bytes()
        with self.assertRaises(storage.StorageRefused): storage.record_state(self.root, "prepared", registry=self.registry)
        self.assertEqual(before, self.ledger_bytes())
        self.assertEqual([p.name for p in self.root.iterdir()], ["prepare-recovery-intent-v1.json"])
        (self.root / "prepare-recovery-intent-v1.json").unlink(); self.root.rmdir()
        with self.assertRaises(storage.StorageRefused): self.execute(path, auth)
        self.worker.assert_not_called(); self.assert_charge("preparing")

    def test_worker_failure_keeps_rebound_charge_and_refuses_ordinary_retention(self):
        self.spent_failure("worker")
        self.assertNotEqual(self.entry()["proposal_sha256"], self.old_entry["proposal_sha256"])
        before = self.ledger_bytes()
        with self.assertRaises(storage.StorageRefused): storage.record_state(self.root, "retained", registry=self.registry)
        self.assertEqual(before, self.ledger_bytes()); self.assert_charge("preparing")

    def test_two_contenders_cannot_dispatch_two_workers_or_add_another_charge(self):
        path, auth, _ = self.make_plan(); barrier = threading.Barrier(2)
        results = []; guard = threading.Lock()
        def contender(index):
            try:
                barrier.wait(timeout=5)
                result = recovery.execute(path, auth, self.base / ("contender-" + str(index)), registry=self.registry)
                with guard: results.append(("ok", result))
            except storage.StorageRefused as error:
                with guard: results.append(("refused", str(error)))
            except BaseException as error:
                with guard: results.append(("unexpected", type(error).__name__))
        threads = [threading.Thread(target=contender, args=(i,), daemon=True) for i in range(2)]
        for thread in threads: thread.start()
        for thread in threads: thread.join(timeout=10)
        self.assertFalse(any(thread.is_alive() for thread in threads))
        self.assertEqual(len(results), 2); self.assertFalse(any(kind == "unexpected" for kind, _ in results), results)
        self.assertEqual(sum(kind == "ok" for kind, _ in results), 1, results)
        self.assertEqual(self.worker.call_count, 1); self.assert_charge("prepared")

    def test_missing_tampered_or_unlinked_history_cannot_be_validated_as_ordinary_storage(self):
        self.successful(); original = self.ledger_bytes(); entry = self.entry()
        for role in ("intent", "completion", "outcome"):
            path = Path(entry["recovery"][role]["path"]); raw = path.read_bytes()
            try:
                path.write_bytes(raw + b"\n")
                with self.assertRaises(storage.StorageRefused): storage._validate(self.ledger(), self.registry)
                path.unlink()
                with self.assertRaises(storage.StorageRefused): storage._validate(self.ledger(), self.registry)
            finally: path.write_bytes(raw)
        changed = self.ledger(); next(e for e in changed["entries"] if e["root"] == str(self.root))["recovery"] = None
        self.write(self.registry / "ledger-v1.json", changed)
        with self.assertRaises(storage.StorageRefused): storage._validate(self.ledger(), self.registry)
        (self.registry / "ledger-v1.json").write_bytes(original)
        storage._validate(self.ledger(), self.registry)

    def test_unknown_fence_cleanup_never_qualifies_retained_or_closed_state(self):
        self.close_known = False; path, auth, _ = self.make_plan()
        with self.assertRaises(storage.StorageRefused): self.execute(path, auth)
        self.assert_charge("prepared")
        terminal = storage.read_json(self.entry()["recovery"]["outcome"]["path"])
        self.assertFalse(terminal["fence_cleanup_known"]); self.assertTrue(terminal["sdk_cleanup_known"])
        closure = self.root / "synthetic-closure.json"
        self.write(closure, dict(proposal_sha256=self.entry()["proposal_sha256"], closure_verified=True, child_cleanup_complete=True))
        before = self.ledger_bytes()
        with self.assertRaises(storage.StorageRefused): storage.record_state(self.root, "retained", registry=self.registry)
        with self.assertRaises(storage.StorageRefused): storage.record_closed(self.root, closure, registry=self.registry)
        self.assertEqual(before, self.ledger_bytes()); self.assertIsNone(self.entry()["closure"])

    def test_closed_and_retired_charge_deduplicates_all_required_external_history_not_sdk_trees(self):
        self.successful(); entry = self.entry(); reference = entry["recovery"]
        intent = storage.read_json(reference["intent"]["path"]); plan = storage.read_json(intent["plan"]["path"])
        complete = storage.read_json(reference["completion"]["path"])
        outcome = storage.read_json(reference["outcome"]["path"])
        expected = {Path(reference[r]["path"]) for r in ("intent", "completion", "outcome")}
        expected.update(Path(p["path"]) for p in [intent["plan"], intent["authorization"], plan["failure"],
            plan["prior_proposal"], plan["legacy_source"], self.pin(self.operator)] + plan["sources"])
        expected.update(Path(complete[r]["path"]) for r in ("proposal", "authorization", "marker"))
        expected.add(Path(outcome["prepare_result"]["path"]))
        self.assertEqual(set(contract.history_paths(entry)), expected)
        unrelated = self.sdk / "unbound-sdk-tree.bin"; unrelated.write_bytes(b"x" * 8192)
        source_extra = Path(self.sources[0]["path"]).parent / "unbound-source.txt"; source_extra.write_bytes(b"unbound")
        self.assertNotIn(unrelated, expected); self.assertNotIn(source_extra, expected)
        closure = self.root / "synthetic-closure.json"
        self.write(closure, dict(proposal_sha256=entry["proposal_sha256"], closure_verified=True, child_cleanup_complete=True))
        storage.record_closed(self.root, closure, registry=self.registry)
        entry = self.entry()
        charged = storage._logical_bytes(list(storage._files(self.root).values()) + list(expected) + [closure])
        self.assertEqual(entry["reserved_bytes"], charged); self.assertEqual(storage._charge(entry), charged)
        storage.record_closed(self.root, closure, registry=self.registry)
        self.assertEqual(self.entry()["reserved_bytes"], charged)
        before = self.ledger_bytes()
        with self.assertRaises(storage.StorageRefused): storage.reserve_prepare(self.base / "third", "f" * 64, registry=self.registry)
        self.assertEqual(before, self.ledger_bytes())
        image = self.root / "content" / "locallore_receipt_api35_v1.avd" / "cache.img"
        image.parent.mkdir(parents=True); image.write_bytes(b"tiny synthetic disposable marker, not an emulator image")
        archive = self.base / "retained-copies"; archive.mkdir(); rows = []
        for relative, source in storage._files(self.root).items():
            if relative in storage.DISPOSABLE: continue
            target = archive / relative; target.parent.mkdir(parents=True, exist_ok=True); shutil.copyfile(source, target)
            rows.append(dict(relative=relative, binding=self.pin(target)))
        manifest = archive / "manifest.json"
        self.write(manifest, dict(version=1, root=str(self.root), complete=True, files=rows))
        retired_plan = storage.plan_retirement(self.root, manifest, registry=self.registry)
        self.assertEqual(len(retired_plan["remove"]), 1)
        image.unlink()  # Only the tiny byte marker created by this test.
        storage.record_retired(self.root, retired_plan, registry=self.registry)
        retired = self.entry(); retained = list(storage._files(self.root).values()) + list(expected) + [manifest, closure]
        retained += [Path(row["binding"]["path"]) for row in rows]
        retained.append(Path(retired["retirement_receipt"]["path"]))
        self.assertEqual(storage._charge(retired), storage._logical_bytes(retained))
        self.assert_old_evidence()


if __name__ == "__main__":
    unittest.main()
