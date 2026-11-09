"""Inert owner checks for activation of the preserved SDK23 preparation.

Copyright 2026 LocalLore contributors. SPDX-License-Identifier: Apache-2.0
"""

import copy
from pathlib import Path
from types import SimpleNamespace
import unittest
from unittest.mock import Mock, call, patch

from benchmarks import owned_saved_library_status as owner
from benchmarks import receipt_avd_environment as env
from benchmarks import receipt_avd_storage as storage
from benchmarks import saved_library_status_handoff as original
from benchmarks import saved_library_status_prepared_review as review
from benchmarks import saved_library_status_resume_handoff as resume
from scripts.tests.test_saved_library_status_resume_handoff import ResumeRecords


class SavedLibraryStatusResumeOwnerTests(unittest.TestCase):
    def setUp(self):
        self.graph = ResumeRecords()
        attempt = self.graph.begin()
        self.admission_pin = self.graph.bind(attempt)
        self.handoff_pin = self.graph.handoff(attempt, self.admission_pin)
        _, self.approved = self.graph.read(resume.HANDOFF)
        _, self.admission = self.graph.read(resume.ADMISSION)
        self.env_proof = {owner.RESUME_HANDOFF_ENV: self.handoff_pin["sha256"]}

    def _boot(self, *, owner_created=False):
        with self.graph.ports(), patch.dict(owner.os.environ, self.env_proof, clear=True):
            return owner._resume_boot(self.admission_pin, owner_created=owner_created)

    def _args(self, path):
        return ["--admission", str(path), "--admission-sha256", self.admission_pin["sha256"]]

    def _runtime(self):
        pin, approved, admission, ledger, launch_inputs = self._boot()
        runtime = object.__new__(owner._SavedLibraryResumeRuntime)
        runtime.request = {"owner": self.graph.prepare_owner}
        runtime.admission = admission
        runtime.proposal = self.graph.run_proposal
        runtime._resume_pin = pin
        runtime._handoff = approved
        runtime._ledger = ledger
        runtime._launch_inputs = launch_inputs
        return runtime

    def _live_call(self, runtime):
        return call.live(runtime._resume_pin, runtime._handoff, runtime._launch_inputs,
                         runtime.request["owner"], path=resume.HANDOFF,
                         env_key=owner.RESUME_HANDOFF_ENV)

    def test_profile_scope_is_distinct_but_admission_shape_stays_fixed(self):
        self.assertEqual(owner._RESUME_CONTRACT.validate_admission(self.admission), self.admission)
        self.assertEqual(owner._RESUME_CONTRACT.RUN_SCOPE, resume.RUN_SCOPE)
        self.assertNotEqual(owner._RESUME_CONTRACT.RUN_SCOPE, owner.RUN_SCOPE)
        self.assertIs(owner.RESUME_REPLAY.c, owner._RESUME_CONTRACT)
        self.assertEqual(owner.REPLAY.c.RUN_SCOPE, owner.RUN_SCOPE)

    def test_boot_reads_exact_resume_handoff_and_binds_ledger_separately(self):
        pin, approved, admission, ledger, launch_inputs = self._boot()
        self.assertEqual(pin, self.handoff_pin)
        self.assertEqual(approved, self.approved)
        self.assertEqual(admission, self.admission)
        self.assertEqual(ledger, self.graph.ledger_pin)
        self.assertNotIn(ledger, launch_inputs)
        self.assertIn(self.graph.original_run, launch_inputs)
        self.assertIn(self.admission["guest"]["authorization"], launch_inputs)

    def test_boot_without_exact_environment_proof_refuses_before_replay(self):
        for proof in ({}, {owner.RESUME_HANDOFF_ENV: "f" * 64},
                      {original.HANDOFF_ENV: self.handoff_pin["sha256"]}):
            with (self.subTest(proof=proof), self.graph.ports(),
                  patch.dict(owner.os.environ, proof, clear=True),
                  patch.object(resume, "verify_handoff") as verify,
                  self.assertRaisesRegex(env.EnvironmentRefused, "^handoff$")):
                owner._resume_boot(self.admission_pin)
            verify.assert_not_called()

    def test_only_worker_path_can_verify_after_owner_output_creation(self):
        with self.assertRaisesRegex(env.EnvironmentRefused, "^already_used$"):
            self._boot(owner_created=True)
        self.graph.present.add(resume.OWNED_ROOT)
        with self.assertRaisesRegex(env.EnvironmentRefused, "^already_used$"):
            self._boot()
        self.assertEqual(self._boot(owner_created=True)[2], self.admission)

    def test_parent_route_requires_the_new_path_and_rechecks_live_owner(self):
        with (self.graph.ports(), patch.dict(owner.os.environ, self.env_proof, clear=True),
              patch.object(owner.mechanisms, "_main_profile", return_value=0) as dispatch,
              patch.object(owner, "_live_handoff") as live):
            args = self._args(resume.ADMISSION)
            self.assertEqual(owner.main(args), 0)
            self.assertEqual(dispatch.call_args.args, (args,))
            selected = dispatch.call_args.kwargs
            self.assertIs(selected["_contract"], owner._RESUME_CONTRACT)
            self.assertIs(selected["_verification"], owner.RESUME_REPLAY)
            self.assertIs(selected["_runtime_type"], owner._SavedLibraryResumeRuntime)
            check = selected["_admission_check"]
            changed = dict(self.admission, root=str(original.OWNED_ROOT))
            with self.assertRaisesRegex(env.EnvironmentRefused, "^admission$"):
                check(changed)
            live.assert_not_called()
            check(self.admission)
            self.assertEqual(live.call_args.args[:2], (self.handoff_pin, self.approved))
            self.assertEqual(live.call_args.kwargs["path"], resume.HANDOFF)
            self.assertEqual(live.call_args.kwargs["env_key"], owner.RESUME_HANDOFF_ENV)

    def test_resume_parent_refuses_missing_cross_scope_and_dual_proofs(self):
        cases = (
            (resume.ADMISSION, {}),
            (resume.ADMISSION, {original.HANDOFF_ENV: self.handoff_pin["sha256"]}),
            (resume.ADMISSION, {owner.RESUME_HANDOFF_ENV: "invalid"}),
            (original.ADMISSION, self.env_proof),
            (resume.OUT / "another.json", self.env_proof),
            (resume.ADMISSION, dict(self.env_proof, **{original.HANDOFF_ENV: "a" * 64})),
        )
        for path, proof in cases:
            with (self.subTest(path=path, proof=proof), self.graph.ports(),
                  patch.dict(owner.os.environ, proof, clear=True),
                  patch.object(owner.mechanisms, "_main_profile") as dispatch):
                self.assertEqual(owner.main(self._args(path)), 1)
            dispatch.assert_not_called()

    def test_worker_dispatch_uses_matching_scope_without_changing_fresh_route(self):
        cases = (
            (self.env_proof, owner._RESUME_CONTRACT, owner._SavedLibraryResumeRuntime),
            ({original.HANDOFF_ENV: "a" * 64}, owner._CONTRACT, owner._SavedLibraryStatusRuntime),
        )
        for proof, selected, runtime in cases:
            with (self.subTest(proof=proof), patch.dict(owner.os.environ, proof, clear=True),
                  patch.object(owner.mechanisms, "_main_profile", return_value=0) as dispatch):
                self.assertEqual(owner.main(["_worker"]), 0)
                self.assertIs(dispatch.call_args.kwargs["_contract"], selected)
                self.assertIs(dispatch.call_args.kwargs["_runtime_type"], runtime)

    def test_worker_replays_the_handoff_before_initializing_runtime(self):
        self.graph.present.add(resume.OWNED_ROOT)
        boot = self._boot(owner_created=True)
        request = dict(admission=self.admission_pin, validated_admission=self.admission,
                       owner=self.graph.prepare_worker)
        request_pin = self.graph.add("request", resume.OWNED_ROOT / "request-v1.json", request)
        sequence = Mock()
        sequence.boot.return_value = boot
        sequence.initialize.return_value = None

        with (patch.object(owner, "_resume_boot", sequence.boot),
              patch.object(owner, "_live_handoff", sequence.live),
              patch.object(owner.mechanisms._TargetRuntimeCore, "__init__", sequence.initialize)):
            runtime = owner._SavedLibraryResumeRuntime(request, request_pin, resume.OWNED_ROOT)
            runtime.request = request
            self.assertEqual(sequence.mock_calls, [
                call.boot(self.admission_pin, owner_created=True),
                self._live_call(runtime),
                call.initialize(request, request_pin, resume.OWNED_ROOT),
            ])
            sequence.reset_mock()
            changed = dict(request, validated_admission=dict(self.admission, root=str(original.OWNED_ROOT)))
            with self.assertRaisesRegex(owner.OwnerRefused, "^admission$"):
                owner._SavedLibraryResumeRuntime(changed, request_pin, resume.OWNED_ROOT)
            self.assertEqual(sequence.mock_calls, [call.boot(self.admission_pin, owner_created=True)])

    def test_runtime_uses_only_the_pinned_original_preparation_context(self):
        runtime = object.__new__(owner._SavedLibraryResumeRuntime)
        self.assertEqual(runtime._preparation_options(), {"preparation_root": review.EXECUTED_ROOT})
        self.assertNotEqual(review.EXECUTED_ROOT, original.ROOT)

    def test_shared_owner_receipt_path_authorizes_using_the_original_source_context(self):
        runtime = self._runtime()
        runtime.root = resume.OWNED_ROOT
        runtime.binding = self.admission_pin
        proposal = copy.deepcopy(runtime.proposal)
        guest = self.admission["guest"]
        proposal.update(sdk=str(Path(guest["emulator"]["path"]).parent.parent),
                        token={}, old_avd={}, bindings=[])
        receipt_path = resume.OWNED_ROOT / "guest-inputs-v1.json"
        receipt = dict(self.admission_pin, path=str(receipt_path))

        with (patch.object(runtime, "guard"),
              patch.object(env, "authorize", return_value=proposal) as authorize,
              patch.object(env, "verify_prepared", return_value={"immutable": []}) as verify,
              patch.object(env, "resource_facts", return_value={}),
              patch.object(Path, "stat", return_value=SimpleNamespace(st_size=0)),
              patch.object(Path, "read_bytes", return_value=b""),
              patch.object(env, "create_json") as write,
              patch.object(env, "binding", return_value=receipt),
              patch.object(owner.RESUME_REPLAY, "verify_guest_inputs") as replay):
            self.assertEqual(runtime.prepare_guest(), receipt)

        authorize.assert_called_once_with(guest["proposal"]["path"], guest["authorization"]["path"],
                                          "run", run_scope=resume.RUN_SCOPE,
                                          preparation_root=review.EXECUTED_ROOT)
        verify.assert_called_once_with(proposal, initial=True, preparation_root=review.EXECUTED_ROOT)
        self.assertEqual(write.call_args.args[0], receipt_path)
        self.assertEqual(write.call_args.args[1]["authorization"], guest["authorization"])
        replay.assert_called_once_with(receipt, self.admission, self.admission_pin)

    def test_server_dispatch_follows_a_live_recheck_and_refuses_when_it_fails(self):
        runtime = self._runtime()
        sequence = Mock()
        with (patch.object(owner, "_live_handoff", sequence.live),
              patch.object(env, "check_binding", sequence.binding),
              patch.object(owner.mechanisms._TargetRuntimeCore, "start_server", sequence.server)):
            runtime.start_server()
            self.assertEqual(sequence.mock_calls,
                             [self._live_call(runtime), call.binding(self.graph.ledger_pin), call.server()])
            sequence.reset_mock()
            sequence.live.side_effect = env.EnvironmentRefused("handoff")
            with self.assertRaisesRegex(env.EnvironmentRefused, "^handoff$"):
                runtime.start_server()
            self.assertEqual(sequence.mock_calls, [self._live_call(runtime)])

            sequence.reset_mock()
            sequence.live.side_effect = None
            sequence.binding.side_effect = env.EnvironmentRefused("binding")
            with self.assertRaisesRegex(env.EnvironmentRefused, "^binding$"):
                runtime.start_server()
            self.assertEqual(sequence.mock_calls, [self._live_call(runtime), call.binding(self.graph.ledger_pin)])

    def test_retention_uses_the_exact_ledger_and_prepare_digest_between_live_checks(self):
        runtime = self._runtime()
        sequence = Mock()
        with (patch.object(owner, "_live_handoff", sequence.live),
              patch.object(storage, "record_state", sequence.retain)):
            runtime._retain_guest()
            claim = call.retain(original.GUEST, "retained",
                                proposal_sha256=self.admission["guest"]["proposal"]["sha256"],
                                expected_prepare_sha256=self.graph.prepare_pin["sha256"],
                                expected_ledger=self.graph.ledger_pin)
            self.assertEqual(sequence.mock_calls,
                             [self._live_call(runtime), claim, self._live_call(runtime)])

            sequence.reset_mock()
            sequence.retain.side_effect = storage.StorageRefused("ledger_changed")
            with self.assertRaisesRegex(env.EnvironmentRefused, "^storage_ledger_changed$"):
                runtime._retain_guest()
            self.assertEqual(sequence.mock_calls, [self._live_call(runtime), claim])

    def test_resume_worker_checks_ancestry_and_closes_process_handles_on_refusal(self):
        pin, approved, _, _, launch_inputs = self._boot()
        supervisor = approved["supervisor"]
        parent = self.graph.prepare_worker
        api = Mock()
        api.parent_pid.return_value = supervisor["pid"]
        api.current_job_pids.return_value = [730]
        handles = Mock()
        handles.add.return_value = (45, parent)
        handles.close.return_value = True

        def check():
            owner._live_handoff(pin, approved, launch_inputs, parent,
                                path=resume.HANDOFF, env_key=owner.RESUME_HANDOFF_ENV)

        with (self.graph.ports(), patch.dict(owner.os.environ, self.env_proof, clear=True),
              patch.object(owner.os, "getpid", return_value=730),
              patch.object(owner.os, "getppid", return_value=parent["pid"]),
              patch.object(owner.mechanisms, "_ProcessApi", return_value=api),
              patch.object(owner.process, "ProcessHandles", return_value=handles)):
            check()
            handles.guard.assert_called_once_with()
            handles.close.assert_called_once_with()
            api.current_job_pids.return_value = [parent["pid"]]
            with self.assertRaisesRegex(env.EnvironmentRefused, "^identity$"):
                check()
            self.assertEqual(handles.guard.call_count, 1)
            self.assertEqual(handles.close.call_count, 2)
