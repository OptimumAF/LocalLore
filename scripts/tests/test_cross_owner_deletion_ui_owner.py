"""Host-only owner boundary tests for the SDK24 deletion journey.

Copyright 2026 LocalLore contributors. SPDX-License-Identifier: Apache-2.0
"""

import copy
from pathlib import Path
from types import SimpleNamespace
import unittest
from unittest.mock import Mock, call, patch

from benchmarks import cross_owner_deletion_ui_closure as closure
from benchmarks import cross_owner_deletion_ui_controller as controller
from benchmarks import cross_owner_deletion_ui_handoff as handoff
from benchmarks import owned_cross_owner_deletion_ui as owner
from benchmarks import receipt_avd_environment as env
from benchmarks import receipt_avd_storage as storage


def pin(path, digit):
    return dict(path=str(path), bytes=80, sha256=digit * 64)


class CrossOwnerDeletionOwnerTests(unittest.TestCase):
    def setUp(self):
        executable = str(Path("D:/Synthetic/python.exe"))
        self.supervisor = dict(pid=101, creation_filetime=500, executable=executable)
        self.parent = dict(pid=102, creation_filetime=501, executable=executable)
        self.worker = dict(pid=103, creation_filetime=502, executable=executable)
        self.handoff_pin = pin(handoff.HANDOFF, "a")
        self.admission_pin = pin(handoff.ADMISSION, "b")
        self.authority_pin = pin(handoff.AUTHORITY, "c")
        self.attempt_pin = pin(handoff.ATTEMPT, "d")
        self.prepare_pin = pin(handoff.GUEST / "prepare-proposal-v1.json", "e")
        self.run_pin = pin(handoff.RUN, "f")
        self.run_authority = pin(handoff.RUN_AUTHORITY, "1")
        self.ledger_pin = pin(handoff.LEDGER, "2")
        self.proposal_pin = pin(handoff.PROPOSAL, "3")
        self.running_pin = pin(handoff.OWNED_ROOT / "running-v1.json", "4")
        self.record = dict(version=1, scope=handoff.HANDOFF_SCOPE,
                           admission=self.admission_pin, authority=self.authority_pin,
                           attempt=self.attempt_pin, supervisor=self.supervisor,
                           began_ns=100, until_ns=200)
        self.approval = dict(version=1, scope=handoff.AUTHORITY_SCOPE, proposal=self.proposal_pin,
                             admission=self.admission_pin, ledger=self.ledger_pin,
                             approval_reference="Synthetic approved activation",
                             allow_sdk_prepare=False, allow_one_boot=True, allow_model=False,
                             allow_retirement=False)
        self.launch_inputs = (self.prepare_pin, self.run_pin, self.run_authority)
        self.boot_proof = (self.handoff_pin, self.record, self.approval, self.launch_inputs)
        self.proof_env = {handoff.HANDOFF_ENV: self.handoff_pin["sha256"]}
        guest = dict(root=str(handoff.GUEST), proposal=self.run_pin, authorization=self.run_authority,
                     memory_mib=8192, cores=4, max_seconds=1800, console_port=5592,
                     serial="emulator-5592",
                     emulator=pin(Path("D:/Synthetic/sdk/emulator/emulator.exe"), "5"))
        self.admission = dict(root=str(handoff.OWNED_ROOT), seconds=handoff.OWNER_SECONDS,
                              python={"executable": pin(executable, "8")}, artifacts={},
                              server={"adb": pin(Path("D:/Synthetic/sdk/platform-tools/adb.exe"), "a")},
                              guest=guest)
        self.request = dict(admission=self.admission_pin, validated_admission=self.admission,
                            owner=self.parent)
        self.request_pin = pin(handoff.OWNED_ROOT / "request-v1.json", "6")

    def args(self):
        return ["--admission", str(handoff.ADMISSION), "--admission-sha256",
                self.admission_pin["sha256"]]

    def runtime(self):
        with (patch.object(handoff, "verify_boot", return_value=self.boot_proof),
              patch.object(owner, "_live_boot")):
            runtime = owner._CrossOwnerDeletionRuntime(self.request, self.request_pin,
                                                       handoff.OWNED_ROOT)
        runtime.proposal = dict(prepare_proposal=self.prepare_pin)
        runtime._running_binding = self.running_pin
        runtime.worker = self.worker
        return runtime

    def check_live(self, parent=None):
        return owner._live_boot(*self.boot_proof, parent=parent)

    def test_missing_or_malformed_proof_and_foreign_routes_refuse_before_dispatch(self):
        variants = (
            ({}, self.args()),
            ({}, ["_worker"]),
            ({handoff.HANDOFF_ENV: "x" * 64}, self.args()),
            ({"LOCALLORE_SAVED_LIBRARY_STATUS_HANDOFF_SHA256": "a" * 64}, self.args()),
            (self.proof_env, ["_worker", "extra"]),
            (self.proof_env, ["--admission", str(handoff.OUT / "other.json"),
                              "--admission-sha256", self.admission_pin["sha256"]]),
            (self.proof_env, [*self.args()[:-1], "x" * 64]),
        )
        with patch.object(owner.mechanisms, "_main_profile") as dispatch:
            for proof, args in variants:
                with self.subTest(proof=proof, args=args), patch.dict(owner.os.environ, proof, clear=True):
                    self.assertEqual(owner.main(args), 1)
            dispatch.assert_not_called()

    def test_worker_route_uses_fixed_runtime_and_scope_without_parent_completion(self):
        with (patch.dict(owner.os.environ, self.proof_env, clear=True),
              patch.object(owner.mechanisms, "_main_profile", return_value=0) as dispatch,
              patch.object(closure, "verify_result") as verify):
            self.assertEqual(owner.main(["_worker"]), 0)
        self.assertEqual(dispatch.call_args.args, (["_worker"],))
        options = dispatch.call_args.kwargs
        self.assertIs(options["_contract"], owner)
        self.assertIs(options["_verification"], owner.REPLAY)
        self.assertIs(options["_runtime_type"], owner._CrossOwnerDeletionRuntime)
        self.assertEqual(owner.REPLAY.c.RUN_SCOPE, owner.PROTOCOL)
        verify.assert_not_called()

    def test_parent_success_requires_exact_gate_and_joined_final_replay(self):
        steps = Mock()
        steps.verify_boot.return_value = self.boot_proof
        steps.closure.return_value = {"controller": self.running_pin}

        def dispatch(args, **options):
            self.assertEqual(args, self.args())
            options["_admission_check"](self.admission)
            return 0

        with (patch.dict(owner.os.environ, self.proof_env, clear=True),
              patch.object(handoff, "read", return_value=(self.admission_pin, self.admission)),
              patch.object(owner.os.path, "lexists", return_value=False),
              patch.object(handoff, "verify_boot", steps.verify_boot),
              patch.object(owner, "_live_boot", steps.live),
              patch.object(owner.mechanisms, "_main_profile", side_effect=dispatch),
              patch.object(closure, "verify_result", steps.closure),
              patch.object(handoff, "check_window", steps.window),
              patch.object(env, "check_binding", steps.binding),
              patch.object(env, "create_json", steps.write)):
            self.assertEqual(owner.main(self.args()), 0)
            steps.verify_boot.assert_called_once_with(self.admission_pin, self.admission)
            steps.closure.assert_called_once_with(self.admission_pin)
            steps.write.assert_called_once_with(handoff.COMPLETION,
                dict(version=1, scope=handoff.AUTHORITY_SCOPE, admission=self.admission_pin,
                     controller=self.running_pin))
            self.assertLess(steps.mock_calls.index(call.verify_boot(self.admission_pin, self.admission)),
                            steps.mock_calls.index(call.closure(self.admission_pin)))
            steps.reset_mock()
            steps.closure.side_effect = env.EnvironmentRefused("binding")
            self.assertEqual(owner.main(self.args()), 1)
            steps.closure.assert_called_once_with(self.admission_pin)
            steps.write.assert_not_called()

    def test_late_final_replay_refuses_before_completion_publication(self):
        window = Mock()

        def dispatch(args, **options):
            options["_admission_check"](self.admission)
            return 0

        def replay(admission_pin):
            self.assertEqual(admission_pin, self.admission_pin)
            window.side_effect = env.EnvironmentRefused("deadline")
            return {"controller": self.running_pin}

        with (patch.dict(owner.os.environ, self.proof_env, clear=True),
              patch.object(handoff, "read", return_value=(self.admission_pin, self.admission)),
              patch.object(owner.os.path, "lexists", return_value=False),
              patch.object(handoff, "verify_boot", return_value=self.boot_proof),
              patch.object(owner, "_live_boot"),
              patch.object(owner.mechanisms, "_main_profile", side_effect=dispatch),
              patch.object(closure, "verify_result", side_effect=replay) as verify,
              patch.object(handoff, "check_window", window),
              patch.object(env, "check_binding"),
              patch.object(env, "create_json") as write):
            self.assertEqual(owner.main(self.args()), 1)
            verify.assert_called_once_with(self.admission_pin)
            write.assert_not_called()

    def test_parent_gate_refuses_stale_admission_or_preexisting_owner_before_live_check(self):
        with (patch.dict(owner.os.environ, self.proof_env, clear=True),
              patch.object(owner.mechanisms, "_main_profile", return_value=27) as dispatch):
            self.assertEqual(owner.main(self.args()), 27)
        gate = dispatch.call_args.kwargs["_admission_check"]
        for current, admission, exists in (
            (dict(self.admission_pin, sha256="7" * 64), self.admission, False),
            (self.admission_pin, dict(self.admission, root=str(handoff.OUT)), False),
            (self.admission_pin, self.admission, True),
        ):
            with (self.subTest(pin=current, admission=admission, exists=exists),
                  patch.object(handoff, "read", return_value=(current, admission)),
                  patch.object(owner.os.path, "lexists", return_value=exists),
                  patch.object(handoff, "verify_boot") as verify,
                  patch.object(owner, "_live_boot") as live,
                  self.assertRaises(env.EnvironmentRefused)):
                gate(self.admission)
            verify.assert_not_called()
            live.assert_not_called()

    def test_worker_rechecks_handoff_before_runtime_initialization(self):
        with (patch.object(handoff, "verify_boot", side_effect=env.EnvironmentRefused("handoff")) as verify,
              patch.object(owner.mechanisms._TargetRuntimeCore, "__init__") as initialize,
              self.assertRaisesRegex(env.EnvironmentRefused, "^handoff$")):
            owner._CrossOwnerDeletionRuntime(self.request, self.request_pin, handoff.OWNED_ROOT)
        verify.assert_called_once_with(self.admission_pin, self.admission)
        initialize.assert_not_called()

    def test_live_boot_checks_digest_before_handles_and_closes_on_wrong_ancestry(self):
        api, handles = Mock(), Mock()
        handles.add.side_effect = lambda pid, expected: (pid + 100, expected)
        handles.close.return_value = True
        api.current_job_pids.return_value = [self.worker["pid"]]
        api.parent_pid.return_value = self.supervisor["pid"]
        with (patch.object(handoff, "read", return_value=(self.handoff_pin, self.record)),
              patch.object(owner.os, "getpid", return_value=self.worker["pid"]),
              patch.object(owner.os, "getppid", return_value=self.parent["pid"]),
              patch.object(owner.mechanisms, "_ProcessApi", return_value=api) as process_api,
              patch.object(owner.process, "ProcessHandles", return_value=handles),
              patch.object(env, "check_binding") as binding,
              patch.object(handoff, "check_window")):
            with (patch.dict(owner.os.environ, {handoff.HANDOFF_ENV: "7" * 64}, clear=True),
                  self.assertRaises(env.EnvironmentRefused)):
                self.check_live(self.parent)
            process_api.assert_not_called()
            with patch.dict(owner.os.environ, self.proof_env, clear=True):
                self.check_live(self.parent)
                handles.guard.assert_called_once_with()
                handles.close.assert_called_once_with()
                handles.add.assert_any_call(self.supervisor["pid"], self.supervisor)
                handles.add.assert_any_call(self.parent["pid"], self.parent)
                for wanted in (self.handoff_pin, self.authority_pin, self.attempt_pin,
                               self.admission_pin, *self.launch_inputs):
                    binding.assert_any_call(wanted)
                binding.reset_mock()
                api.parent_pid.return_value = 999
                with self.assertRaisesRegex(env.EnvironmentRefused, "^identity$"):
                    self.check_live(self.parent)
                binding.assert_not_called()
                self.assertEqual(handles.close.call_count, 2)

    def test_stale_ledger_refuses_private_server_after_live_check(self):
        runtime = self.runtime()
        steps = Mock()
        with (patch.object(owner, "_live_boot", steps.live),
              patch.object(env, "check_binding", steps.check),
              patch.object(owner.mechanisms._TargetRuntimeCore, "start_server", steps.server)):
            runtime.start_server()
            steps.check.assert_any_call(self.ledger_pin)
            steps.server.assert_called_once_with()
            self.assertEqual([c[0] for c in steps.mock_calls], ["live", "check", "server"])
            steps.reset_mock()
            steps.check.side_effect = env.EnvironmentRefused("binding_changed")
            with self.assertRaisesRegex(env.EnvironmentRefused, "^binding_changed$"):
                runtime.start_server()
            self.assertEqual([c[0] for c in steps.mock_calls], ["live", "check"])

    def test_locked_retention_binds_approved_ledger_and_rechecks_handoff(self):
        runtime = self.runtime()
        steps = Mock()
        with (patch.object(owner, "_live_boot", steps.live),
              patch.object(storage, "record_state", steps.retain)):
            runtime._retain_guest()
            retained = call.retain(handoff.GUEST, "retained", proposal_sha256=self.run_pin["sha256"],
                                   expected_prepare_sha256=self.prepare_pin["sha256"],
                                   expected_ledger=self.ledger_pin)
            self.assertEqual([c[0] for c in steps.mock_calls], ["live", "retain", "live"])
            self.assertEqual(steps.mock_calls[1], retained)
            steps.reset_mock()
            steps.retain.side_effect = storage.StorageRefused("ledger_changed")
            with self.assertRaisesRegex(env.EnvironmentRefused, "^storage_ledger_changed$"):
                runtime._retain_guest()
            self.assertEqual([c[0] for c in steps.mock_calls], ["live", "retain"])
            self.assertEqual(steps.mock_calls[1], retained)

            steps.reset_mock()
            steps.retain.side_effect = None
            steps.live.side_effect = [None, env.EnvironmentRefused("handoff")]
            with self.assertRaisesRegex(env.EnvironmentRefused, "^handoff$"):
                runtime._retain_guest()
            self.assertEqual([c[0] for c in steps.mock_calls], ["live", "retain", "live"])
            self.assertEqual(steps.mock_calls[1], retained)

    def test_shared_guest_input_replay_uses_the_scoped_run_authorization(self):
        runtime = self.runtime()
        guest = self.admission["guest"]
        proposal = dict(paths=dict(root=guest["root"], content=guest["root"]),
                        memory_mib=8192, cores=4, max_seconds=1800,
                        sdk=str(Path(guest["emulator"]["path"]).parent.parent),
                        prepared=self.prepare_pin, prepare_result=self.prepare_pin,
                        token={}, old_avd={}, bindings=[])
        receipt = pin(handoff.OWNED_ROOT / "guest-inputs-v1.json", "7")
        with (patch.object(runtime, "guard"),
              patch.object(env, "authorize", return_value=proposal) as authorize,
              patch.object(env, "verify_prepared", return_value={"immutable": []}),
              patch.object(env, "resource_facts", return_value={}),
              patch.object(Path, "stat", return_value=SimpleNamespace(st_size=0)),
              patch.object(Path, "read_bytes", return_value=b""),
              patch.object(env, "create_json") as write,
              patch.object(env, "binding", return_value=receipt),
              patch.object(owner.REPLAY, "verify_guest_inputs") as verify):
            self.assertEqual(runtime.prepare_guest(), receipt)
        authorize.assert_called_once_with(self.run_pin["path"], self.run_authority["path"],
                                          "run", run_scope=owner.PROTOCOL)
        verify.assert_called_once_with(receipt, self.admission, self.admission_pin)
        self.assertEqual(write.call_args.args[1]["authorization"], self.run_authority)

    def test_worker_runs_controller_once_and_requests_owned_stop_on_clean_or_failed_result(self):
        ready, guest_job = object(), object()
        result = dict(version=2, scope=controller.SCOPE, outcome="completed",
                      observer_handles_closed=True, admission=self.admission_pin,
                      running=self.running_pin, caller=self.worker)
        cases = (
            (result, None, True, True),
            (result, None, False, False),
            (dict(result, observer_handles_closed=False), None, True, False),
            (dict(result, outcome="refused"), None, True, False),
            (None, RuntimeError("synthetic controller failure"), True, False),
        )
        for returned, failure, initially_closed, expected_closed in cases:
            runtime = self.runtime()
            runtime.clients_closed = initially_closed
            steps = Mock()
            steps.admit.return_value = (ready, guest_job)
            steps.run.return_value = copy.deepcopy(returned)
            steps.run.side_effect = failure
            with (self.subTest(result=returned, failure=failure, initially_closed=initially_closed),
                  patch.object(owner.mechanisms._TargetRuntimeCore, "admit_guest", steps.admit),
                  patch.object(owner, "_live_boot", steps.live),
                  patch.object(controller, "run", steps.run),
                  patch.object(handoff, "check_window"),
                  patch.object(runtime, "guard", steps.guard),
                  patch.object(env, "create_json", steps.write),
                  patch.object(Path, "rename", steps.rename)):
                if failure is None:
                    self.assertEqual(runtime.admit_guest(), (ready, guest_job))
                else:
                    with self.assertRaisesRegex(RuntimeError, "^synthetic controller failure$"):
                        runtime.admit_guest()
                self.assertIs(runtime.clients_closed, expected_closed)
                steps.admit.assert_called_once_with()
                steps.run.assert_called_once_with(self.admission_pin, self.running_pin)
                steps.write.assert_called_once()
                steps.rename.assert_called_once_with(handoff.OWNED_ROOT / "stop-v1.json")
                self.assertEqual(steps.write.call_args.args[1],
                                 dict(version=1, protocol=owner.PROTOCOL,
                                      admission_sha256=self.admission_pin["sha256"], action="stop"))
                names = [c[0] for c in steps.mock_calls]
                self.assertLess(names.index("admit"), names.index("live"))
                self.assertLess(names.index("live"), names.index("run"))
                self.assertLess(names.index("run"), names.index("write"))
                self.assertLess(names.index("write"), names.index("rename"))

    def test_inline_controller_refuses_changed_handoff_before_dispatch(self):
        runtime = self.runtime()
        with (patch.object(owner.mechanisms._TargetRuntimeCore, "admit_guest"),
              patch.object(owner, "_live_boot", side_effect=env.EnvironmentRefused("handoff")),
              patch.object(controller, "run") as run,
              patch.object(env, "create_json") as write,
              self.assertRaisesRegex(env.EnvironmentRefused, "^handoff$")):
            runtime.admit_guest()
        run.assert_not_called()
        write.assert_not_called()

    def test_prepared_handoff_joins_scoped_run_and_exact_authority_before_live_dispatch(self):
        prepared = pin(handoff.GUEST / "prepared-v1.json", "8")
        prepare_result = pin(handoff.GUEST / "prepare-result-v1.json", "9")
        guest = self.admission["guest"]
        proposal = dict(paths=dict(root=str(handoff.GUEST)),
                        sdk=str(Path(guest["emulator"]["path"]).parent.parent),
                        adb_path=self.admission["server"]["adb"]["path"],
                        **{key: guest[key] for key in
                           ("memory_mib", "cores", "max_seconds", "console_port", "serial")},
                        prepare_proposal=self.prepare_pin, prepared=prepared,
                        prepare_result=prepare_result)
        attempt = dict(version=1, scope=handoff.AUTHORITY_SCOPE, authority=self.authority_pin,
                       no_retry=True)
        run_authority = dict(version=1, phase="run", proposal_sha256=self.run_pin["sha256"],
                             run_scope=owner.RUN_SCOPE, allow_environment_calls=True,
                             root_go_pending=False)
        records = {handoff.ADMISSION: self.admission, handoff.AUTHORITY: self.approval,
                   handoff.ATTEMPT: attempt, handoff.RUN: proposal,
                   handoff.RUN_AUTHORITY: run_authority}
        document = (f'Admission SHA-256 {self.admission_pin["sha256"]}\n'
                    f'Ledger SHA-256 {self.ledger_pin["sha256"]}\n').encode()
        entry = dict(state="prepared", reserved_bytes=storage.RESERVATION_BYTES,
                     proposal_sha256=self.prepare_pin["sha256"], closure=None,
                     recovery=None, retirement=None, retirement_receipt=None)
        with (patch.dict(owner.os.environ, self.proof_env, clear=True),
              patch.object(owner, "validate_admission", side_effect=lambda value: value),
              patch.object(handoff, "at", side_effect=lambda _, path, *args: records[path]),
              patch.object(handoff, "read", return_value=(self.handoff_pin, self.record)),
              patch.object(handoff, "_bound", return_value=document),
              patch.object(handoff, "check_window"),
              patch.object(env, "validate_proposal"),
              patch.object(env, "verify_prepared") as verify,
              patch.object(owner, "revalidate_inputs"),
              patch.object(owner.artifacts, "verify_artifacts"),
              patch.object(handoff, "ledger_entry", return_value=(self.ledger_pin, entry)) as ledger,
              patch.object(env, "safe_path", side_effect=lambda path, **_: path),
              patch.object(owner.os.path, "lexists", return_value=False),
              patch.object(env, "check_binding")):
            bound, record, approval, inputs = handoff.verify_boot(self.admission_pin, self.admission)
            self.assertEqual((bound, record, approval),
                             (self.handoff_pin, self.record, self.approval))
            self.assertEqual(inputs, (self.proposal_pin, self.run_pin, self.run_authority,
                                      self.prepare_pin, prepared, prepare_result))
            verify.assert_called_once_with(proposal, initial=True)
            ledger.assert_called_once_with(self.ledger_pin)

            verify.reset_mock()
            ledger.reset_mock()
            records[handoff.RUN_AUTHORITY] = {key: val for key, val in run_authority.items()
                                               if key != "run_scope"}
            with self.assertRaisesRegex(env.EnvironmentRefused, "^not_authorized$"):
                handoff.verify_boot(self.admission_pin, self.admission)
            verify.assert_not_called()
            ledger.assert_not_called()

            records[handoff.RUN_AUTHORITY] = run_authority
            records[handoff.RUN] = dict(proposal, serial="emulator-5594")
            with self.assertRaisesRegex(env.EnvironmentRefused, "^proposal$"):
                handoff.verify_boot(self.admission_pin, self.admission)
            verify.assert_not_called()
            ledger.assert_not_called()

            records[handoff.RUN] = proposal
            records[handoff.AUTHORITY] = dict(self.approval, allow_sdk_prepare=True)
            with self.assertRaisesRegex(env.EnvironmentRefused, "^authority$"):
                handoff.verify_boot(self.admission_pin, self.admission)
            verify.assert_not_called()
            ledger.assert_not_called()

    def test_prepared_ledger_rejects_stale_pin_before_reading_admission_row(self):
        stale = dict(self.ledger_pin, sha256="9" * 64)
        with (patch.object(handoff, "read", return_value=(stale, {})),
              patch.object(storage, "_validate") as validate,
              patch.object(storage, "_entry") as entry,
              self.assertRaisesRegex(env.EnvironmentRefused, "^ledger$")):
            handoff.ledger_entry(self.ledger_pin)
        validate.assert_not_called()
        entry.assert_not_called()

    def test_launch_window_reserves_controller_time_and_never_exceeds_activation_limit(self):
        began = 30 * handoff.NS
        deadline = began + handoff.ACTIVATION_SECONDS * handoff.NS
        last = deadline - handoff.LAUNCH_TAIL_SECONDS * handoff.NS
        with patch.object(handoff.time, "monotonic_ns", return_value=last - 1):
            handoff.check_window(began, deadline, minimum_seconds=handoff.LAUNCH_TAIL_SECONDS)
            with self.assertRaisesRegex(env.EnvironmentRefused, "^deadline$"):
                handoff.check_window(began, deadline + 1, minimum_seconds=handoff.LAUNCH_TAIL_SECONDS)
        with (patch.object(handoff.time, "monotonic_ns", return_value=last),
              self.assertRaisesRegex(env.EnvironmentRefused, "^deadline$")):
            handoff.check_window(began, deadline, minimum_seconds=handoff.LAUNCH_TAIL_SECONDS)
