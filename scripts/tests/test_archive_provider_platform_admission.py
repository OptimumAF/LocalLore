"""Exercise SDK26 candidate admission with private synthetic records only.

Copyright 2026 LocalLore contributors. SPDX-License-Identifier: Apache-2.0
"""
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import patch

from benchmarks import archive_provider_platform_admission as admission
from benchmarks import archive_provider_platform_preparation as prep


REFUSALS = (OSError, RuntimeError, ValueError)


class ArchiveProviderAdmissionTests(unittest.TestCase):
    def setUp(self):
        self.root = Path(self.enterContext(TemporaryDirectory())).resolve()
        guest = self.root / "avd-v1"
        output = self.root / "activation-v1"
        for name, leaf in {
            "GUEST": "avd-v1", "PLAN": "plan.json", "PREPARE": "prepare.json",
            "PROPOSED_PREPARATION": "PROPOSED_PREPARATION.md", "AUTHORITY": "prepare-authority.json",
            "CLAIM": "prepare-claim.json", "PREPARE_AUTH": "prepare-authorization.json",
            "RESULT": "preparation-result.json", "LEDGER": "ledger-v1.json",
        }.items():
            self.enterContext(patch.object(prep, name, self.root / leaf))
        self.enterContext(patch.object(admission, "OUT", output))
        self.enterContext(patch.object(admission, "GUEST", guest, create=True))
        self.enterContext(patch.object(admission, "LEDGER", prep.LEDGER, create=True))
        for name, leaf in {
            "RUN": "run-proposal-v1.json", "ADMISSION": "admission-v1.json",
            "PROPOSAL": "PROPOSED_OPERATION.md", "CANDIDATE": "candidate-v1.json",
            "RUN_AUTHORITY": "run-authorization-v1.json", "HANDOFF": "boot-handoff-v1.json",
            "COMPLETION": "activation-completion-v1.json",
            "OWNED_ROOT": "owned-v1", "AUTHORITY": "human-authority-v1.json", "CLAIM": "claim-v1.json",
        }.items():
            self.enterContext(patch.object(admission, name, output / leaf, create=True))

        self.enterContext(patch.object(prep.env, "validate_proposal"))
        self.verify_prepared = self.enterContext(patch.object(prep.env, "verify_prepared"))
        self.enterContext(patch.object(prep.storage, "_validate"))
        self.enterContext(patch.object(prep.artifacts, "verify_artifacts"))
        self.sdk_prepare = self.enterContext(patch.object(prep.env, "prepare"))
        self.start = self.enterContext(patch("subprocess.Popen", side_effect=AssertionError("unexpected child")))
        self.socket = self.enterContext(patch("socket.socket", side_effect=AssertionError("unexpected socket")))

        self.proposal = dict(version=1, phase="prepare", paths={"root": str(guest)}, memory_mib=8192, cores=4,
                             sdk=str(self.root / "sdk"), adb_path=str(self.root / "sdk" / "adb.exe"),
                             allow_environment_calls=False, root_go_pending=True)
        self.prepare_pin = self.save(prep.PREPARE, self.proposal)
        self.initial_ledger = self.save(prep.LEDGER, {"version": 2, "entries": []})
        python = self.save(self.root / "python.exe", {"synthetic": True})
        sources = [self.save(self.root / "source.json", {"synthetic": True})]
        self.plan = dict(version=1, scope=prep.PLAN_SCOPE, sources=sources,
                         python={"executable": python, "runtime_dll": None},
                         artifacts=prep.artifacts.artifact_bindings(), prepare=self.prepare_pin)
        self.enterContext(patch.object(prep.owned, "source_bindings", return_value=sources))
        self.enterContext(patch.object(prep.python_probe, "_python_bindings", return_value=self.plan["python"]))
        self.plan_pin = self.save(prep.PLAN, self.plan)
        prep.PROPOSED_PREPARATION.write_text(
            f"Plan SHA-256 {self.plan_pin['sha256']}\nLedger SHA-256 {self.initial_ledger['sha256']}\n",
            encoding="utf-8")
        authority = self.save(prep.AUTHORITY, dict(
            version=1, scope=prep.PREPARE_SCOPE, proposal=prep.env.binding(prep.PROPOSED_PREPARATION),
            plan=self.plan_pin, ledger=self.initial_ledger, approval_reference="synthetic approval",
            allow_sdk_prepare=True, allow_one_boot=False, allow_model=False, allow_retirement=False))
        claim = self.save(prep.CLAIM, prep._claim(authority))
        authorization = self.save(prep.PREPARE_AUTH, dict(
            version=1, phase="prepare", prepare_scope=prep.PREPARE_SCOPE,
            proposal_sha256=self.prepare_pin["sha256"], allow_environment_calls=True, root_go_pending=False))

        guest.mkdir()
        prepared = self.save(guest / "prepared-v1.json", {"proposal_sha256": self.prepare_pin["sha256"]})
        result = self.save(guest / "prepare-result-v1.json", {"status": "completed"})
        process = dict(pid=7101, creation_filetime=107101, executable=python["path"])
        start = self.save(guest / "prepare-start-v1.json", dict(
            proposal_sha256=self.prepare_pin["sha256"], facts={}, owner=process, prepare_scope=prep.PREPARE_SCOPE))
        worker = self.save(guest / "prepare-worker-claimed-v1.json", dict(
            proposal_sha256=self.prepare_pin["sha256"], worker=dict(process, pid=7102, creation_filetime=107102),
            prepare_scope=prep.PREPARE_SCOPE))
        stdout_path = guest / "prepare-stdout-v1.bin"
        stdout_path.write_bytes(b"synthetic successful preparation\n")
        stdout = prep.env.binding(stdout_path)
        client = self.save(guest / "prepare-client-v1.json", dict(
            status="completed", returncode=0, cleanup_complete=True, elapsed_ms=14000,
            stdout_sha256=stdout["sha256"], stderr_bytes=0))
        self.entry = dict(root=str(guest), state="prepared", proposal_sha256=self.prepare_pin["sha256"],
                          reserved_bytes=prep.storage.RESERVATION_BYTES,
                          closure=None, recovery=None, retirement=None, retirement_receipt=None)
        self.ledger = self.write(prep.LEDGER, {"version": 2, "entries": [self.entry]})
        self.proof = dict(version=1, scope=prep.PREPARE_SCOPE, authority=authority, claim=claim,
                          plan=self.plan_pin, authorization=authorization, ledger=self.ledger,
                          prepared=prepared, result=result, activation_authorized=False,
                          evidence=dict(start=start, worker=worker, client=client, stdout=stdout))
        self.preparation_pin = self.save(prep.RESULT, self.proof)

        self.installed = dict(
            adb={"synthetic": "adb"}, tools=[], capabilities={"synthetic": "capabilities"},
            source_review={"synthetic": "review"}, auth_key="C:/Synthetic/.android/adbkey",
            emulator={"synthetic": "emulator"}, qemu={"synthetic": "qemu"}, refuser={"synthetic": "refuser"},
            refuser_source={"synthetic": "refuser source"}, compatibility={"synthetic": "compatibility"},
        )
        self.enterContext(patch.object(admission, "_admission", side_effect=self.assemble_admission))
        self.check_inputs = self.enterContext(patch.object(admission, "_check_inputs"))
        self.enterContext(patch.object(prep.owned, "validate_admission", side_effect=lambda value: value))
        self.addCleanup(self.assert_no_dispatch)

    @staticmethod
    def save(path, value):
        prep.env.create_json(path, value)
        return prep.env.binding(path)

    @staticmethod
    def write(path, value):
        path.write_bytes(prep.env.encoded(value))
        return prep.env.binding(path)

    def assemble_admission(self, plan, run_pin, installed, run_id):
        self.assertEqual(installed, self.installed)
        server = {key: installed[key] for key in ("adb", "tools", "capabilities", "source_review", "auth_key")}
        guest = {key: installed[key] for key in ("emulator", "qemu", "refuser", "refuser_source")}
        guest.update(root=str(prep.GUEST), proposal=run_pin,
                     authorization=dict(path=str(admission.RUN_AUTHORITY), bytes=1, sha256="a" * 64))
        return dict(run_id=run_id, guest=guest, server=server, artifacts=plan["artifacts"],
                    compatibility=installed["compatibility"])

    def assert_no_dispatch(self):
        self.sdk_prepare.assert_not_called()
        self.start.assert_not_called()
        self.socket.assert_not_called()

    def verify_preparation(self, proof_pin=None):
        return admission.verify_preparation(self.plan_pin, proof_pin or self.preparation_pin)

    def stage(self):
        return admission.create_candidate(self.plan_pin, self.preparation_pin, self.installed)

    def test_preparation_replays_completed_receipt_and_current_reservation(self):
        self.assertEqual(self.verify_preparation(), (self.plan, self.proposal, self.proof, self.ledger))
        self.verify_prepared.assert_called_once()
        self.assertTrue(self.verify_prepared.call_args.kwargs["initial"])
        self.assertFalse(admission.OUT.exists())

    def test_missing_or_borrowed_preparation_refuses_without_publication(self):
        borrowed = self.save(self.root / "borrowed-result.json", self.proof)
        with self.assertRaises(REFUSALS):
            self.verify_preparation(borrowed)
        prep.RESULT.unlink()
        with self.assertRaises(REFUSALS):
            self.stage()
        self.assertFalse(admission.OUT.exists())
        self.check_inputs.assert_not_called()

    def test_prep_authorization_cannot_be_replaced_with_run_authorization(self):
        value = prep.env.read_json(prep.PREPARE_AUTH)
        wrong = self.write(prep.PREPARE_AUTH, dict(value, phase="run"))
        forged = self.write(prep.RESULT, dict(self.proof, authorization=wrong))
        with self.assertRaises(REFUSALS):
            self.verify_preparation(forged)
        self.assertFalse(admission.OUT.exists())

    def test_changed_worker_receipt_or_spent_boot_claim_refuses(self):
        worker_path = Path(self.proof["evidence"]["worker"]["path"])
        worker = prep.env.read_json(worker_path)
        self.write(worker_path, dict(worker, worker=dict(worker["worker"], pid=7103)))
        with self.assertRaises(REFUSALS):
            self.stage()
        self.write(worker_path, worker)
        self.save(prep.GUEST / prep.owned.BOOT_CLAIM_FILE, {"spent": True})
        with self.assertRaises(REFUSALS):
            self.stage()
        self.assertFalse(admission.OUT.exists())

    def test_wrong_state_and_reservation_refuse(self):
        for changes in ({"state": "closed"}, {"reserved_bytes": 1}, {"proposal_sha256": "0" * 64}):
            with self.subTest(changes=changes):
                self.write(prep.LEDGER, {"version": 2, "entries": [dict(self.entry, **changes)]})
                with self.assertRaises(REFUSALS):
                    self.stage()
        self.assertFalse(admission.OUT.exists())
        self.check_inputs.assert_not_called()

    def test_stages_two_exact_tests_without_executable_authority(self):
        candidate_pin = self.stage()
        candidate = prep.env.read_json(admission.CANDIDATE)
        self.assertEqual(candidate_pin, prep.env.binding(admission.CANDIDATE))
        self.assertEqual(candidate, dict(version=1, scope=admission.SCOPE, plan=self.plan_pin,
                                         preparation=self.preparation_pin, ledger=self.ledger,
                                         admission=prep.env.binding(admission.ADMISSION),
                                         proposal=prep.env.binding(admission.PROPOSAL),
                                         execution_authorized=False))
        run = prep.env.read_json(admission.RUN)
        self.assertIs(run["allow_environment_calls"], False)
        self.assertEqual(run["prepared"], self.proof["prepared"])
        self.assertEqual(run["prepare_result"], self.proof["result"])
        review = admission.PROPOSAL.read_text(encoding="utf-8")
        for _, klass, method in prep.owned.INSTRUMENTATIONS:
            self.assertEqual(review.count(klass + "#" + method), 1)
        self.assertIn(candidate["admission"]["sha256"], review)
        self.assertIn(self.ledger["sha256"], review)
        before = {path.name: path.read_bytes() for path in admission.OUT.iterdir()}
        self.assertEqual(admission.verify_candidate(candidate_pin, self.ledger),
                         prep.env.read_json(admission.ADMISSION))
        self.assertEqual({path.name: path.read_bytes() for path in admission.OUT.iterdir()}, before)
        for path in (admission.RUN_AUTHORITY, admission.HANDOFF, admission.OWNED_ROOT):
            self.assertFalse(path.exists())

    def test_candidate_refuses_unrelated_ledger_drift_after_review(self):
        candidate = self.stage()
        changed = self.write(prep.LEDGER, {"version": 2, "entries": [self.entry], "change": "unrelated"})
        for ledger in (self.ledger, changed):
            with self.subTest(ledger=ledger), self.assertRaises(REFUSALS):
                admission.verify_candidate(candidate, ledger)
        self.assertFalse(admission.RUN_AUTHORITY.exists())

    def test_changed_review_and_existing_output_are_preserved(self):
        candidate = self.stage()
        admission.PROPOSAL.write_text("modified review\n", encoding="utf-8")
        before = {path.name: path.read_bytes() for path in admission.OUT.iterdir()}
        with self.assertRaises(REFUSALS):
            admission.verify_candidate(candidate, self.ledger)
        with self.assertRaises(REFUSALS):
            self.stage()
        self.assertEqual({path.name: path.read_bytes() for path in admission.OUT.iterdir()}, before)

    def test_verified_candidate_is_not_a_boot_authority(self):
        candidate = self.stage()
        self.save(admission.RUN_AUTHORITY, {"synthetic": "already exists"})
        with self.assertRaises(REFUSALS):
            admission.verify_candidate(candidate, self.ledger)
        self.assertEqual(prep.env.read_json(admission.RUN_AUTHORITY), {"synthetic": "already exists"})

    def change_worker_during_tool_checks(self, *_):
        path = Path(self.proof["evidence"]["worker"]["path"])
        worker = prep.env.read_json(path)
        self.write(path, dict(worker, worker=dict(worker["worker"], pid=7103)))

    def test_staging_refuses_worker_drift_during_tool_checks(self):
        self.check_inputs.side_effect = self.change_worker_during_tool_checks
        with self.assertRaises(REFUSALS):
            self.stage()
        self.check_inputs.assert_called_once()
        self.assertFalse(admission.CANDIDATE.exists())
        self.assertFalse(admission.RUN_AUTHORITY.exists())

    def test_verification_refuses_worker_drift_during_tool_checks(self):
        candidate = self.stage()
        self.check_inputs.reset_mock()
        self.check_inputs.side_effect = self.change_worker_during_tool_checks
        with self.assertRaises(REFUSALS):
            admission.verify_candidate(candidate, self.ledger)
        self.check_inputs.assert_called_once()
        self.assertEqual(prep.env.binding(admission.CANDIDATE), candidate)
        self.assertFalse(admission.RUN_AUTHORITY.exists())
