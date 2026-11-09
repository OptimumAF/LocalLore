"""Exercise the SDK26 activation handoff using only synthetic records.

Copyright 2026 LocalLore contributors. SPDX-License-Identifier: Apache-2.0
"""
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import patch

from benchmarks import archive_provider_platform_admission as admission
from benchmarks import archive_provider_platform_handoff as handoff
from benchmarks import archive_provider_platform_preparation as prep
from benchmarks import owned_archive_provider_platform as owned


REFUSALS = (OSError, RuntimeError, ValueError)
NS = 1_000_000_000


class ArchiveProviderHandoffTests(unittest.TestCase):
    def setUp(self):
        self.root = Path(self.enterContext(TemporaryDirectory())).resolve()
        guest = self.root / "avd-v1"
        output = self.root / "activation-v1"
        output.mkdir()
        guest.mkdir()
        for name, value in {
            "GUEST": guest, "LEDGER": self.root / "ledger-v1.json",
            "RESULT": self.root / "preparation-result.json",
        }.items():
            self.enterContext(patch.object(prep, name, value))
        for name, value in {
            "OUT": output, "RUN": output / "run-proposal-v1.json",
            "ADMISSION": output / "admission-v1.json", "PROPOSAL": output / "PROPOSED_OPERATION.md",
            "CANDIDATE": output / "candidate-v1.json", "RUN_AUTHORITY": output / "run-authorization-v1.json",
            "HANDOFF": output / "boot-handoff-v1.json", "OWNED_ROOT": output / "owned-v1",
        }.items():
            self.enterContext(patch.object(admission, name, value))
        self.enterContext(patch.object(handoff, "AUTHORITY", output / "activation-authority-v1.json"))
        self.enterContext(patch.object(handoff, "ATTEMPT", output / "activation-claim-v1.json"))

        self.ledger = self.save(prep.LEDGER, {"version": 2, "entries": []})
        self.prepare = self.save(self.root / "prepare.json", {"phase": "prepare"})
        self.prepared = self.save(guest / "prepared-v1.json", {"synthetic": "prepared"})
        self.result = self.save(guest / "prepare-result-v1.json", {"synthetic": "completed"})
        self.run = self.save(admission.RUN, {
            "version": 1, "phase": "run", "paths": {"root": str(guest)},
            "prepare_proposal": self.prepare, "prepared": self.prepared, "prepare_result": self.result,
            "memory_mib": 8192, "cores": 4, "max_seconds": prep.env.REAL_MAX_SECONDS,
            "console_port": 5592, "serial": "emulator-5592",
        })
        self.run_authority = dict(
            version=1, phase="run", run_scope=owned.PROTOCOL, proposal_sha256=self.run["sha256"],
            allow_environment_calls=True, root_go_pending=False,
        )
        self.expected_run_authority = admission._pin_for_bytes(
            admission.RUN_AUTHORITY, prep.env.encoded(self.run_authority),
        )
        python = self.save(self.root / "python.exe", {"synthetic": "python"})
        self.admitted = {
            "root": str(admission.OWNED_ROOT), "seconds": admission.OWNER_SECONDS,
            "guest": {
                "root": str(guest), "proposal": self.run, "authorization": self.expected_run_authority,
                "memory_mib": 8192, "cores": 4, "max_seconds": prep.env.REAL_MAX_SECONDS,
                "console_port": 5592, "serial": "emulator-5592",
            },
            "python": {"executable": python, "runtime_dll": None},
        }
        self.admission_pin = self.save(admission.ADMISSION, self.admitted)
        self.proposal = self.write(admission.PROPOSAL, admission._review_bytes(self.admission_pin, self.ledger))
        self.preparation = self.save(prep.RESULT, {
            "authority": self.save(self.root / "preparation-authority.json", {"synthetic": "authority"}),
            "claim": self.save(self.root / "preparation-claim.json", {"synthetic": "claim"}),
            "authorization": self.save(self.root / "preparation-authorization.json", {"synthetic": "authorization"}),
            "evidence": {"worker": self.save(guest / "prepare-worker-claimed-v1.json", {"synthetic": "worker"})},
        })
        self.candidate = self.save(admission.CANDIDATE, dict(
            version=1, scope=admission.SCOPE,
            plan=self.save(self.root / "plan.json", {"synthetic": "plan"}),
            preparation=self.preparation,
            ledger=self.ledger, admission=self.admission_pin, proposal=self.proposal, execution_authorized=False,
        ))
        self.approved = dict(
            version=1, scope=handoff.AUTHORITY_SCOPE, candidate=self.candidate,
            proposal=self.proposal, admission=self.admission_pin, ledger=self.ledger,
            approval_reference="synthetic one-boot approval",
            allow_sdk_prepare=False, allow_one_boot=True, allow_model=False, allow_retirement=False,
        )
        self.authority = self.save(handoff.AUTHORITY, self.approved)
        self.attempt = self.save(handoff.ATTEMPT, handoff.claim_value(self.authority, self.candidate))
        self.supervisor = dict(pid=7101, creation_filetime=107101, executable=python["path"])
        self.began_ns = 100 * NS
        self.until_ns = self.began_ns + 1700 * NS
        self.boot_record = dict(
            version=1, scope=handoff.HANDOFF_SCOPE, authority=self.authority, attempt=self.attempt,
            candidate=self.candidate, admission=self.admission_pin, supervisor=self.supervisor,
            began_ns=self.began_ns, until_ns=self.until_ns,
        )
        self.replay_before = self.enterContext(
            patch.object(admission, "verify_candidate", return_value=self.admitted),
        )
        self.replay_boot = self.enterContext(
            patch.object(admission, "_verify_candidate", return_value=self.admitted, create=True),
        )
        self.enterContext(patch.object(owned, "validate_admission", side_effect=lambda value: value))
        self.enterContext(patch.object(owned, "revalidate_inputs"))
        self.enterContext(patch.object(handoff.time, "monotonic_ns", return_value=self.began_ns + NS))
        self.start = self.enterContext(patch("subprocess.Popen", side_effect=AssertionError("unexpected child")))
        self.socket = self.enterContext(patch("socket.socket", side_effect=AssertionError("unexpected socket")))
        self.sdk_prepare = self.enterContext(patch.object(prep.env, "prepare"))
        self.addCleanup(self.assert_no_dispatch)

    @staticmethod
    def write(path, raw):
        path.write_bytes(raw)
        return prep.env.binding(path)

    @classmethod
    def save(cls, path, value):
        return cls.write(path, prep.env.encoded(value))

    def assert_no_dispatch(self):
        self.start.assert_not_called()
        self.socket.assert_not_called()
        self.sdk_prepare.assert_not_called()

    def materialize(self):
        return handoff.materialize_run_authorization(self.authority, self.candidate, self.attempt)

    def verify_boot(self, record=None):
        pin = self.save(admission.HANDOFF, self.boot_record if record is None else record)
        return handoff.verify_boot(self.admission_pin, self.admitted, pin)

    def test_exact_activation_authority_and_attempt_are_file_only(self):
        self.assertEqual(handoff.read_approval(self.authority, self.candidate), self.approved)
        self.assertEqual(prep.env.read_json(handoff.ATTEMPT), dict(
            version=1, scope=handoff.AUTHORITY_SCOPE, authority=self.authority,
            candidate=self.candidate, no_retry=True,
        ))
        self.assertFalse(admission.RUN_AUTHORITY.exists())
        self.assertFalse(admission.HANDOFF.exists())
        self.replay_before.assert_not_called()

    def test_wrong_scope_and_broadened_flags_refuse_before_candidate_replay(self):
        for changes in (
            {"scope": prep.PREPARE_SCOPE}, {"allow_sdk_prepare": True}, {"allow_one_boot": 1},
            {"allow_model": True}, {"allow_retirement": True}, {"approval_reference": " "},
        ):
            with self.subTest(changes=changes):
                pin = self.save(handoff.AUTHORITY, dict(self.approved, **changes))
                with self.assertRaises(REFUSALS):
                    handoff.read_approval(pin, self.candidate)
        self.replay_before.assert_not_called()
        self.assertFalse(admission.RUN_AUTHORITY.exists())

    def test_missing_or_borrowed_approval_and_changed_review_refuse(self):
        missing = dict(self.authority, path=str(self.root / "missing-authority.json"))
        borrowed = self.save(self.root / "borrowed-authority.json", self.approved)
        for pin in (missing, borrowed):
            with self.subTest(path=pin["path"]), self.assertRaises(REFUSALS):
                handoff.read_approval(pin, self.candidate)
        self.write(admission.PROPOSAL, b"changed review\n")
        with self.assertRaises(REFUSALS):
            handoff.read_approval(self.authority, self.candidate)

    def test_authority_cannot_borrow_candidate_or_ledger(self):
        different_candidate = self.save(self.root / "borrowed-candidate.json", {"synthetic": "borrowed"})
        with self.assertRaises(REFUSALS):
            handoff.read_approval(self.authority, different_candidate)
        changed = self.save(handoff.AUTHORITY, dict(self.approved, ledger=dict(self.ledger, sha256="b" * 64)))
        with self.assertRaises(REFUSALS):
            handoff.read_approval(changed, self.candidate)

    def test_materializes_exact_one_boot_authorization_once(self):
        self.assertEqual(self.materialize(), self.expected_run_authority)
        self.assertEqual(prep.env.read_json(admission.RUN_AUTHORITY), self.run_authority)
        self.replay_before.assert_called_once_with(self.candidate, self.ledger)
        with self.assertRaises(REFUSALS):
            self.materialize()
        self.assertEqual(prep.env.binding(admission.RUN_AUTHORITY), self.expected_run_authority)
        self.assertFalse(admission.HANDOFF.exists())
        self.assertFalse(admission.OWNED_ROOT.exists())

    def test_changed_or_borrowed_attempt_refuses_before_materializing(self):
        altered = handoff.claim_value(self.authority, self.candidate) | {"no_retry": False}
        changed = self.save(handoff.ATTEMPT, altered)
        borrowed = self.save(self.root / "borrowed-claim.json", handoff.claim_value(self.authority, self.candidate))
        for pin in (changed, borrowed):
            with self.subTest(path=pin["path"]), self.assertRaises(REFUSALS):
                handoff.materialize_run_authorization(self.authority, self.candidate, pin)
        self.replay_before.assert_not_called()
        self.assertFalse(admission.RUN_AUTHORITY.exists())

    def test_candidate_replay_refusal_keeps_attempt_but_writes_no_authorization(self):
        self.replay_before.side_effect = prep.env.EnvironmentRefused("ledger_changed")
        with self.assertRaises(REFUSALS):
            self.materialize()
        self.assertEqual(prep.env.binding(handoff.ATTEMPT), self.attempt)
        self.assertFalse(admission.RUN_AUTHORITY.exists())

    def test_candidate_cannot_change_the_authorization_digest_before_write(self):
        guest = dict(self.admitted["guest"], authorization=dict(self.expected_run_authority, sha256="b" * 64))
        self.replay_before.return_value = dict(self.admitted, guest=guest)
        with self.assertRaises(REFUSALS):
            self.materialize()
        self.assertFalse(admission.RUN_AUTHORITY.exists())

    def test_boot_handoff_binds_exact_supervisor_candidate_and_scoped_authorization(self):
        self.materialize()
        record, approval, inputs = self.verify_boot()
        self.assertEqual((record, approval), (self.boot_record, self.approved))
        self.assertIn(self.expected_run_authority, inputs)
        self.assertIn(self.run, inputs)
        self.assertIn(self.preparation, inputs)
        self.assertIn(self.prepared, inputs)
        self.assertIn(self.result, inputs)
        self.replay_boot.assert_called_once_with(self.candidate, self.ledger)
        self.assertFalse(admission.OWNED_ROOT.exists())

    def test_boot_handoff_refuses_wrong_supervisor_or_time_window(self):
        self.materialize()
        for changes in (
            {"supervisor": dict(self.supervisor, executable=str(self.root / "foreign.exe"))},
            {"scope": handoff.AUTHORITY_SCOPE}, {"until_ns": self.began_ns + NS},
            {"began_ns": self.began_ns + 2 * NS}, {"until_ns": self.began_ns + 1810 * NS},
        ):
            with self.subTest(changes=changes), self.assertRaises(REFUSALS):
                self.verify_boot(dict(self.boot_record, **changes))
        self.assertFalse(admission.OWNED_ROOT.exists())

    def test_boot_handoff_refuses_missing_or_changed_run_authorization(self):
        with self.assertRaises(REFUSALS):
            self.verify_boot()
        self.materialize()
        self.save(admission.RUN_AUTHORITY, dict(self.run_authority, run_scope=prep.PREPARE_SCOPE))
        with self.assertRaises(REFUSALS):
            self.verify_boot()

    def test_boot_handoff_replays_candidate_again_and_refuses_ledger_drift(self):
        self.materialize()
        self.replay_boot.side_effect = prep.env.EnvironmentRefused("ledger_changed")
        with self.assertRaises(REFUSALS):
            self.verify_boot()
        self.replay_boot.assert_called_once_with(self.candidate, self.ledger)
        self.assertFalse(admission.OWNED_ROOT.exists())

    def test_boot_handoff_refuses_a_spent_boot_claim(self):
        self.materialize()
        self.save(prep.GUEST / owned.BOOT_CLAIM_FILE, {"spent": True})
        with self.assertRaises(REFUSALS):
            self.verify_boot()
        self.assertFalse(admission.OWNED_ROOT.exists())

    def test_boot_handoff_refuses_worker_drift_after_candidate_replay(self):
        self.materialize()

        def drift(*_):
            self.save(prep.GUEST / "prepare-worker-claimed-v1.json", {"synthetic": "changed worker"})
            return self.admitted

        self.replay_boot.side_effect = drift
        with self.assertRaises(REFUSALS):
            self.verify_boot()
        self.replay_boot.assert_called_once_with(self.candidate, self.ledger)
        self.assertFalse(admission.OWNED_ROOT.exists())
