"""Exercise SDK24 review staging and exact activation authorization on the host.

Copyright 2026 LocalLore contributors. SPDX-License-Identifier: Apache-2.0
"""
import copy
import os
from pathlib import Path, PureWindowsPath
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import patch

from benchmarks import cross_owner_deletion_ui_admission as candidate
from benchmarks import cross_owner_deletion_ui_handoff as h
from benchmarks import cross_owner_deletion_ui_preparation as prep
from benchmarks import owned_cross_owner_deletion_ui as owned
from benchmarks import receipt_avd_environment as env
from benchmarks import receipt_avd_storage as storage
from scripts.tests import test_owned_target_contract as fixture


REFUSED = (ValueError, RuntimeError, OSError)


@unittest.skipUnless(os.name == "nt", "fixed D: Windows candidate paths")
class CrossOwnerDeletionAdmissionTests(unittest.TestCase):
    def setUp(self):
        self.directory = Path(self.enterContext(TemporaryDirectory(dir=os.environ["TEMP"])))
        out = self.directory / "activation"
        attempt = out / "attempt-v1"
        paths = dict(OUT=out, ATTEMPT_ROOT=attempt, PROPOSAL=out / "PROPOSED_OPERATION.md",
                     AUTHORITY=out / "human-authority-v1.json", ATTEMPT=attempt / "claim-v1.json",
                     ADMISSION=attempt / "admission-v1.json", HANDOFF=attempt / "boot-handoff-v1.json",
                     RUN=attempt / "run-proposal-v1.json", RUN_AUTHORITY=attempt / "run-authorization-v1.json",
                     OWNED_ROOT=attempt / "owned-v1", COMPLETION=attempt / "activation-result-v1.json",
                     LEDGER=self.directory / "ledger-v1.json")
        self.enterContext(patch.multiple(h, **paths))
        self.enterContext(patch.object(prep, "PLAN", self.directory / "plan-v1.json"))
        boot_claim = h.GUEST / owned.BOOT_CLAIM_FILE
        safe_path, lexists = env.safe_path, os.path.lexists
        self.enterContext(patch.object(env, "safe_path", side_effect=lambda path, *args, **kwargs:
                                     path if path == boot_claim else safe_path(path, *args, **kwargs)))
        self.enterContext(patch.object(os.path, "lexists", side_effect=lambda path:
                                     False if path == boot_claim else lexists(path)))

        source = PureWindowsPath("D:/Synthetic/LocalLore")
        sources = sorted(map(fixture.pin, (
            *(source / "benchmarks" / name for name in owned.SOURCE_NAMES),
            *(source / "scripts" / name for name in ("audit_apk.py", "audit_physical_model_apk.py")),
        )), key=lambda pin: pin["path"])
        base = fixture.admission()
        server, guest = base["server"], base["guest"]
        installed = {key: server[key] for key in ("adb", "tools", "capabilities", "source_review")}
        installed.update({key: guest[key] for key in ("emulator", "qemu", "refuser", "refuser_source")})
        installed.update(auth_key_path=server["auth_key"], compatibility=base["compatibility"])
        self.prepare = dict(phase="prepare", paths={"root": str(h.GUEST)}, memory_mib=8192, cores=4)
        prepare_pin = self.save(self.directory / "prepare-v1.json", self.prepare)
        self.proof = {key: self.save(self.directory / filename, {"result": key})
                      for key, filename in (("prepared", "prepared-v1.json"), ("result", "prepare-result-v1.json"))}
        self.plan = dict(version=1, scope="synthetic", source_root=str(source), sources=sources,
                         python=base["python"], artifacts=owned.artifacts.artifact_bindings(),
                         prepare=prepare_pin, installed=installed)
        self.plan_pin = self.save(prep.PLAN, self.plan)
        self.entry = dict(root=str(h.GUEST), state="prepared", reserved_bytes=storage.RESERVATION_BYTES,
                          proposal_sha256=prepare_pin["sha256"], closure=None, recovery=None,
                          retirement=None, retirement_receipt=None)
        self.ledger_pin = self.save(h.LEDGER, dict(version=2, entries=[self.entry]))
        self.enterContext(patch.object(h, "ledger_entry", side_effect=self.ledger_entry))
        self.enterContext(patch.object(prep, "load_plan", side_effect=self.load_plan))
        self.prep_replay = self.enterContext(patch.object(prep, "verify_preparation", return_value=self.proof))
        self.plan_run = self.enterContext(patch.object(env, "plan_run", side_effect=self.write_run))
        for name in ("validate_proposal", "verify_prepared", "verify_installation", "check_external_state"):
            self.enterContext(patch.object(env, name))
        self.enterContext(patch.object(owned, "source_bindings", return_value=sources))
        self.enterContext(patch.object(owned.artifacts, "verify_artifacts"))
        self.enterContext(patch.object(prep, "verify_installed"))
        self.preflight = self.enterContext(patch.object(prep, "verify_resources_and_ports"))
        self.revalidate = self.enterContext(patch.object(owned, "revalidate_inputs"))

    @staticmethod
    def save(path, value):
        env.create_json(path, value)
        return env.binding(path)

    def load_plan(self, pin):
        self.assertEqual(pin, self.plan_pin)
        return self.plan, self.prepare

    def ledger_entry(self, expected=None):
        pin, ledger = h.read(h.LEDGER)
        env.require(expected is None or owned._same(pin, expected), "ledger")
        return pin, ledger["entries"][0]

    def write_run(self, prepare, prepared, output, *, max_seconds):
        self.assertEqual((prepare, prepared, output, max_seconds),
                         (self.plan["prepare"]["path"], h.GUEST / "prepared-v1.json", h.RUN,
                          h.ACTIVATION_SECONDS))
        run = dict(self.prepare, phase="run", prepare_proposal=self.plan["prepare"],
                   prepared=self.proof["prepared"], prepare_result=self.proof["result"],
                   max_seconds=max_seconds)
        self.save(output, run)
        return run

    def approve(self, review, **overrides):
        authority = dict(version=1, scope=h.AUTHORITY_SCOPE, proposal=review["proposal"],
                         admission=review["admission"], ledger=review["ledger"],
                         approval_reference="Synthetic exact boot approval", allow_sdk_prepare=False,
                         allow_one_boot=True, allow_model=False, allow_retirement=False)
        authority.update(overrides)
        authority_pin = self.save(h.AUTHORITY, authority)
        attempt_pin = self.save(h.ATTEMPT, dict(version=1, scope=h.AUTHORITY_SCOPE, authority=authority_pin,
                                               no_retry=True))
        return authority_pin, attempt_pin

    def test_candidate_stages_review_records_without_authority(self):
        review = candidate.create_candidate(self.plan_pin)
        self.assertEqual(set(review), {"admission", "ledger", "proposal"})
        self.assertEqual(review["ledger"], self.ledger_pin)
        self.assertEqual({path.name for path in h.OUT.iterdir()}, {h.PROPOSAL.name, h.ATTEMPT_ROOT.name})
        self.assertEqual({path.name for path in h.ATTEMPT_ROOT.iterdir()}, {h.ADMISSION.name, h.RUN.name})
        markdown = h.PROPOSAL.read_text(encoding="utf-8")
        self.assertIn("Admission SHA-256 " + review["admission"]["sha256"], markdown)
        self.assertIn("Ledger SHA-256 " + review["ledger"]["sha256"], markdown)
        self.assertIn("#recoversRetainedStoryAfterAnotherOwnerDeletesSelection", markdown)
        self.assertEqual(env.binding(h.PROPOSAL), review["proposal"])
        admitted = candidate.verify_candidate(review["admission"], review["ledger"])
        self.assertEqual(admitted["guest"]["authorization"]["path"], str(h.RUN_AUTHORITY))
        self.assertFalse(h.RUN_AUTHORITY.exists())
        self.revalidate.assert_not_called()
        self.assertEqual(env.binding(h.LEDGER), self.ledger_pin)

    def test_prepared_row_mismatch_refuses_before_staging(self):
        h.LEDGER.write_bytes(env.encoded(dict(version=2, entries=[dict(self.entry, state="retained")])))
        with self.assertRaisesRegex(env.EnvironmentRefused, "^prepared$"):
            candidate.create_candidate(self.plan_pin)
        self.assertFalse(h.OUT.exists())
        self.plan_run.assert_not_called()

    def test_capacity_refusal_preserves_unused_activation_paths(self):
        self.preflight.side_effect = env.EnvironmentRefused("host_capacity")
        with self.assertRaisesRegex(env.EnvironmentRefused, "^host_capacity$"):
            candidate.create_candidate(self.plan_pin)
        self.assertFalse(h.OUT.exists())
        self.plan_run.assert_not_called()

    def test_existing_candidate_refuses_without_replacing_evidence(self):
        review = candidate.create_candidate(self.plan_pin)
        with self.assertRaisesRegex(env.EnvironmentRefused, "^already_used$"):
            candidate.create_candidate(self.plan_pin)
        self.assertEqual(env.binding(h.ADMISSION), review["admission"])
        self.assertEqual(env.binding(h.PROPOSAL), review["proposal"])
        self.plan_run.assert_called_once()

    def test_changed_ledger_refuses_before_materializing_authority(self):
        review = candidate.create_candidate(self.plan_pin)
        authority, attempt = self.approve(review)
        with h.LEDGER.open("ab") as stream:
            stream.write(b"\n")
        with self.assertRaisesRegex(env.EnvironmentRefused, "^ledger$"):
            candidate.materialize_run_authorization(review["admission"], authority, attempt)
        self.assertFalse(h.RUN_AUTHORITY.exists())
        self.revalidate.assert_not_called()

    def test_changed_run_bytes_refuse_even_if_ledger_unchanged(self):
        review = candidate.create_candidate(self.plan_pin)
        run = env.read_json(h.RUN)
        run["max_seconds"] = 1799
        h.RUN.write_bytes(env.encoded(run))
        with self.assertRaises(REFUSED):
            candidate.verify_candidate(review["admission"], review["ledger"])
        self.assertFalse(h.RUN_AUTHORITY.exists())

    def test_forged_prospective_authorization_refuses_even_with_resealed_review(self):
        review = candidate.create_candidate(self.plan_pin)
        admitted = env.read_json(h.ADMISSION)
        admitted["guest"]["authorization"]["sha256"] = "a" * 64
        h.ADMISSION.write_bytes(env.encoded(admitted))
        replacement = env.binding(h.ADMISSION)
        h.PROPOSAL.write_bytes(candidate._proposal_bytes(replacement, review["ledger"]))
        with self.assertRaisesRegex(env.EnvironmentRefused, "^admission$"):
            candidate.verify_candidate(replacement, review["ledger"])
        self.assertFalse(h.RUN_AUTHORITY.exists())

    def test_proposal_drift_during_preflight_refuses_before_returning_candidate(self):
        review = candidate.create_candidate(self.plan_pin)
        self.preflight.side_effect = lambda _: h.PROPOSAL.write_bytes(b"changed")
        with self.assertRaisesRegex(env.EnvironmentRefused, "^binding_changed$"):
            candidate.verify_candidate(review["admission"], review["ledger"])
        self.assertFalse(h.RUN_AUTHORITY.exists())

    def test_cross_scope_approval_refuses_without_writing_run_authorization(self):
        review = candidate.create_candidate(self.plan_pin)
        authority, attempt = self.approve(review, scope=prep.PREPARE_SCOPE)
        with self.assertRaisesRegex(env.EnvironmentRefused, "^authority$"):
            candidate.materialize_run_authorization(review["admission"], authority, attempt)
        self.assertFalse(h.RUN_AUTHORITY.exists())

    def test_approved_materialization_matches_prospective_pin_and_is_one_use(self):
        review = candidate.create_candidate(self.plan_pin)
        admitted = env.read_json(h.ADMISSION)
        authority, attempt = self.approve(review)
        pin = candidate.materialize_run_authorization(review["admission"], authority, attempt)
        self.assertEqual(pin, admitted["guest"]["authorization"])
        self.assertEqual(pin, env.binding(h.RUN_AUTHORITY))
        env.check_authorization(env.read_json(h.RUN_AUTHORITY), "run",
                                admitted["guest"]["proposal"]["sha256"], run_scope=owned.RUN_SCOPE)
        self.revalidate.assert_called_once_with(admitted)
        with self.assertRaisesRegex(env.EnvironmentRefused, "^already_used$"):
            candidate.materialize_run_authorization(review["admission"], authority, attempt)
        self.assertEqual(env.binding(h.RUN_AUTHORITY), pin)
        self.assertFalse(h.HANDOFF.exists())
        self.assertFalse(h.OWNED_ROOT.exists())
