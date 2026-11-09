"""Use a tiny isolated v2 ledger to exercise the SDK24 guarded failed close.

Copyright 2026 LocalLore contributors. SPDX-License-Identifier: Apache-2.0
"""
import copy
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import patch

from benchmarks import cross_owner_deletion_ui_failed_close as operator
from benchmarks import receipt_avd_environment as env
from benchmarks import receipt_avd_retirement as retirement
from benchmarks import receipt_avd_storage as storage


REFUSALS = (OSError, RuntimeError, ValueError)


class CrossOwnerDeletionFailedCloseTests(unittest.TestCase):
    def setUp(self):
        self.base = Path(self.enterContext(TemporaryDirectory(dir="D:/Dev/_Temp"))).resolve()
        self.registry = self.base / "registry"
        self.guest = self.base / "guest"
        self.other = self.base / "other"
        self.output = self.base / "records"
        for path in (self.registry, self.guest, self.other, self.output):
            path.mkdir()
        self.ledger = self.registry / "ledger-v1.json"
        self.lock = self.registry / "admission.lock"
        self.closure = self.guest / "guest-storage-closure-v1.json"
        self.enterContext(patch.object(storage, "DEFAULT_REGISTRY", self.registry))
        self.enterContext(patch.object(operator.h, "LEDGER", self.ledger))
        self.enterContext(patch.object(operator.h, "GUEST", self.guest))
        self.enterContext(patch.object(operator, "OUT", self.output))
        for name in ("PLAN", "AUTHORITY", "CLAIM", "BEFORE", "AFTER", "REVIEW"):
            self.enterContext(patch.object(operator, name, self.output / (name.lower() + ".json")))
        self.config = self.guest / "config.ini"
        self.image = self.guest / (storage.CONTENT + "userdata-qemu.img")
        self.image.parent.mkdir(parents=True)
        self.config.write_bytes(b"synthetic preserved configuration\n")
        self.image.write_bytes(b"synthetic retained image\n")
        self.other_config = self.other / "config.ini"
        self.other_config.write_bytes(b"unrelated guest\n")
        other_sha = "a" * 64
        other_closure = self.save(self.other / "closure.json", dict(
            proposal_sha256=other_sha, closure_verified=True, cleanup_complete=True,
        ))
        other_bytes = self.other_config.stat().st_size + other_closure["bytes"]
        self.other_entry = self.entry(self.other, other_sha, state="closed", reserved_bytes=other_bytes,
                                      closure=other_closure)
        self.evidence = {}
        for role in ("operation", "observed", "run", "admission", "inner_terminal", "worker"):
            self.evidence[role] = self.save(self.base / (role + ".json"), {"synthetic": role})
        self.proposal_sha = self.evidence["run"]["sha256"]
        self.entry_before = self.entry(self.guest, self.proposal_sha)
        self.initial = dict(version=2, max_guests=storage.MAX_GUESTS, budget_bytes=storage.BUDGET_BYTES,
                            reservation_bytes=storage.RESERVATION_BYTES,
                            entries=[self.other_entry, self.entry_before])
        storage._validate(self.initial, self.registry)
        self.ledger_pin = self.save(self.ledger, self.initial)
        self.evidence["ledger"] = self.ledger_pin
        identities = [dict(pid=i, creation_filetime=1000 + i, executable=r"C:\Synthetic\python.exe")
                      for i in range(31, 38)]
        self.report = dict(version=1, scope="sdk24-failed-registration-closure-review-v1",
                           disposition="guarded_closure_review_required", existing_retirement_eligible=False,
                           execution_authorized=False, evidence=self.evidence,
                           processes=[dict(identity=value, status="pid_absent") for value in identities])
        self.review_pin = self.save(operator.REVIEW, self.report)
        self.fresh = self.enterContext(patch.object(operator, "_fresh_review", side_effect=self.fresh_review))
        self.enterContext(patch("subprocess.Popen", side_effect=AssertionError("unexpected process")))
        self.enterContext(patch("socket.socket", side_effect=AssertionError("unexpected socket")))

    @staticmethod
    def save(path, value):
        env.create_json(path, value)
        return storage.binding(path)

    @staticmethod
    def entry(root, proposal_sha256, **overrides):
        return dict(dict(root=str(root), proposal_sha256=proposal_sha256, state="retained",
                         reserved_bytes=storage.RESERVATION_BYTES, closure=None,
                         retirement=None, retirement_receipt=None, recovery=None), **overrides)

    def fresh_review(self, review_pin, ledger_pin, *, locked_entry=None):
        self.assertEqual(review_pin, self.review_pin)
        self.assertEqual(ledger_pin, self.ledger_pin)
        self.assertEqual(self.lock.exists(), locked_entry is not None)
        if locked_entry is not None:
            self.assertEqual(locked_entry, self.entry_before)
        return copy.deepcopy(self.report)

    def approve(self, **changes):
        value = operator.build_plan(self.review_pin)
        plan = self.save(operator.PLAN, value)
        authority = dict(version=1, scope=operator.AUTHORITY_SCOPE, plan=plan,
                         approval_reference="synthetic closure-only approval", allow_close=True,
                         allow_retirement=False, allow_boot=False)
        return self.save(operator.AUTHORITY, dict(authority, **changes))

    def assert_unused(self):
        for path in (operator.CLAIM, operator.BEFORE, operator.AFTER, self.closure, self.lock):
            self.assertFalse(path.exists(), str(path))

    def test_plan_is_read_only_and_seals_retained_guest_roster(self):
        before = {path: storage.binding(path) for path in self.base.rglob("*") if path.is_file()}
        plan = operator.build_plan(self.review_pin)
        self.assertEqual(plan["root"], str(self.guest))
        self.assertEqual(plan["review"], self.review_pin)
        self.assertEqual(plan["ledger"], self.ledger_pin)
        self.assertEqual(plan["proposal_sha256"], self.proposal_sha)
        self.assertEqual(plan["retained_bytes"], storage.RESERVATION_BYTES)
        self.assertEqual(plan["guest_bytes"], self.config.stat().st_size + self.image.stat().st_size)
        self.assertEqual({path: storage.binding(path) for path in self.base.rglob("*") if path.is_file()}, before)
        self.assertFalse(operator.PLAN.exists())
        self.assert_unused()

    def test_guarded_close_updates_only_one_entry_and_conserves_chargeable_proofs(self):
        authority = self.approve()
        expected_originals = tuple(self.evidence[role] for role in self.evidence if role != "ledger")
        expected_originals += tuple(storage.binding(path) for path in (self.config, self.image, self.other_config))
        before = self.ledger.read_bytes()
        result = operator.execute(authority)

        self.assertEqual(result["ledger"], storage.binding(self.ledger))
        self.assertEqual(result["closure"], storage.binding(self.closure))
        self.assertEqual(result["android_methods_executed"], 0)
        self.assertEqual(operator.BEFORE.read_bytes(), before)
        self.assertTrue(operator.CLAIM.is_file())
        self.assertTrue(operator.AFTER.is_file())
        self.assertFalse(self.lock.exists())
        for pin in expected_originals:
            self.assertEqual(storage.binding(pin["path"]), pin)

        ledger = storage.read_json(self.ledger)
        storage._validate(ledger, self.registry)
        self.assertEqual(storage._entry(ledger, self.other), self.other_entry)
        entry = storage._entry(ledger, self.guest)
        self.assertEqual(entry, dict(self.entry_before, state="closed",
                                     reserved_bytes=result["reserved_bytes"], closure=result["closure"]))
        record = storage.read_json(self.closure)
        self.assertEqual(record["scope"], operator.CLOSURE_SCOPE)
        self.assertEqual(record["after"], storage.binding(operator.AFTER))
        proofs = storage._closed(record, self.proposal_sha)
        self.assertIn(operator.AFTER, proofs)
        self.assertEqual(entry["reserved_bytes"], storage._logical_bytes(
            list(storage._files(self.guest).values()) + proofs,
        ))
        self.assertLess(entry["reserved_bytes"], self.entry_before["reserved_bytes"])
        self.assertEqual(storage._charge(entry), entry["reserved_bytes"])
        self.assertTrue(any(call.kwargs.get("locked_entry") is not None for call in self.fresh.call_args_list))

    def test_missing_or_foreign_authority_does_not_spend_the_attempt(self):
        foreign = self.save(self.output / "foreign.json", {"synthetic": True})
        missing = dict(foreign, path=str(operator.AUTHORITY))
        for pin in (foreign, missing):
            with self.subTest(path=pin["path"]), self.assertRaises(REFUSALS):
                operator.execute(pin)
            self.assert_unused()
        self.assertEqual(storage.binding(self.ledger), self.ledger_pin)

    def test_boot_scope_in_a_closure_grant_refuses_without_a_claim(self):
        authority = self.approve(allow_boot=True)
        with self.assertRaises(REFUSALS):
            operator.execute(authority)
        self.assert_unused()
        self.assertEqual(storage.binding(self.ledger), self.ledger_pin)

    def test_stale_but_semantically_equal_ledger_refuses_before_claim(self):
        authority = self.approve()
        changed = self.ledger.read_bytes() + b" "
        self.ledger.write_bytes(changed)
        with self.assertRaises(REFUSALS):
            operator.execute(authority)
        self.assert_unused()
        self.assertEqual(self.ledger.read_bytes(), changed)
        self.assertEqual(storage.read_json(self.ledger), self.initial)

    def test_guest_roster_change_refuses_without_a_claim(self):
        authority = self.approve()
        self.image.write_bytes(b"different synthetic image size\n")
        with self.assertRaises(REFUSALS):
            operator.execute(authority)
        self.assert_unused()
        self.assertEqual(storage.binding(self.ledger), self.ledger_pin)

    def test_finalization_failure_preserves_spent_claim_and_retained_charge(self):
        authority = self.approve()

        def refuse(*_args, **_kwargs):
            self.assertTrue(self.lock.is_file())
            self.assertTrue(operator.CLAIM.is_file())
            raise storage.StorageRefused("synthetic_finalization_refusal")

        with (patch.object(storage, "_record_closed_locked", side_effect=refuse) as record,
              self.assertRaisesRegex(storage.StorageRefused, "^synthetic_finalization_refusal$")):
            operator.execute(authority)
        record.assert_called_once()
        self.assertFalse(self.lock.exists())
        self.assertEqual(storage.binding(self.ledger), self.ledger_pin)
        self.assertEqual(storage._entry(storage.read_json(self.ledger), self.guest), self.entry_before)
        claim = storage.binding(operator.CLAIM)
        with self.assertRaises(REFUSALS):
            operator.execute(authority)
        self.assertEqual(storage.binding(operator.CLAIM), claim)
        self.assertEqual(storage.binding(self.ledger), self.ledger_pin)

    def test_closed_charge_refuses_changed_external_proof(self):
        result = operator.execute(self.approve())
        self.assertEqual(result["closure"], storage.binding(self.closure))
        entry = storage._entry(storage.read_json(self.ledger), self.guest)
        old = operator.AFTER.read_bytes()
        operator.AFTER.write_bytes(old + b" ")
        with self.assertRaises(storage.StorageRefused):
            storage._charge(entry)

    def test_failed_locked_review_does_not_spend_the_grant(self):
        authority = self.approve()

        def refuse(_review_pin, _ledger_pin, *, locked_entry=None):
            self.assertTrue(self.lock.is_file())
            self.assertEqual(locked_entry, self.entry_before)
            raise env.EnvironmentRefused("synthetic_process_uncertainty")

        self.fresh.side_effect = refuse
        with self.assertRaisesRegex(env.EnvironmentRefused, "^synthetic_process_uncertainty$"):
            operator.execute(authority)
        self.assert_unused()
        self.assertEqual(storage.binding(self.ledger), self.ledger_pin)

    def test_retirement_reader_requires_typed_proof_and_exact_original_ledger_backup(self):
        operator.execute(self.approve())
        entry = storage._entry(storage.read_json(self.ledger), self.guest)
        expected = [row["identity"] for row in self.report["processes"]]
        self.assertEqual(retirement._closure(entry), expected)
        operator.BEFORE.write_bytes(operator.BEFORE.read_bytes() + b" ")
        with self.assertRaises(REFUSALS):
            retirement._closure(entry)
