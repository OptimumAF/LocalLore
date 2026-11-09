"""Inert process and storage ports for the SDK21 owner entry."""

from contextlib import ExitStack
from pathlib import Path
import unittest
from unittest.mock import Mock, call, patch

from benchmarks import owned_combined_record_ui_owner as owner


class CombinedRecordBootOwnerTests(unittest.TestCase):
    def setUp(self):
        self.pin = dict(path=str(owner.handoff.HANDOFF), bytes=200, sha256="a" * 64)
        executable = r"D:\Synthetic\python.exe"
        self.supervisor = dict(pid=101, creation_filetime=500, executable=executable)
        self.parent = dict(pid=102, creation_filetime=501, executable=executable)
        self.approved = dict(supervisor=self.supervisor, began_ns=100, until_ns=200,
                             authority=dict(path=str(owner.handoff.AUTHORITY), bytes=250, sha256="b" * 64),
                             attempt=dict(path=str(owner.handoff.ATTEMPT), bytes=150, sha256="c" * 64),
                             admission=dict(path=str(owner.handoff.ADMISSION), bytes=350, sha256="d" * 64))

    def test_only_fixed_parent_arguments_and_exact_worker_route_reach_shared_owner(self):
        with patch.object(owner.mechanisms, "_main_profile", return_value=27) as profile:
            for args in ([], ("_worker",), ["_worker", "extra"],
                         ["--admission", r"D:\Synthetic\admission-v1.json", "--admission-sha256", "a" * 64]):
                with self.subTest(args=args):
                    self.assertEqual(owner.main(args), 1)
            profile.assert_not_called()
            self.assertEqual(owner.main(["_worker"]), 27)
            self.assertEqual(profile.call_args.args, (["_worker"],))
            self.assertIs(profile.call_args.kwargs["_contract"], owner.contract)
            self.assertIs(profile.call_args.kwargs["_verification"], owner.REPLAY)
            self.assertIs(profile.call_args.kwargs["_runtime_type"], owner._CombinedRecordUiTargetRuntime)

    def test_parent_gate_rechecks_exact_admission_and_refuses_existing_owner(self):
        admission = {"root": str(owner.handoff.OWNED_ROOT)}
        pin = dict(path=str(owner.handoff.ADMISSION), bytes=200, sha256="b" * 64)
        args = ["--admission", str(owner.handoff.ADMISSION), "--admission-sha256", pin["sha256"]]
        with patch.object(owner.mechanisms, "_main_profile", return_value=27) as profile:
            self.assertEqual(owner.main(args), 27)
            gate = profile.call_args.kwargs["_admission_check"]
        for current, existing, reason in ((pin, False, None), (pin, True, "already_used"),
                                          (dict(pin, sha256="c" * 64), False, "admission")):
            with self.subTest(reason=reason), \
                 patch.object(owner.handoff, "read", return_value=(current, admission)), \
                 patch.object(owner.os.path, "lexists", return_value=existing), \
                 patch.object(owner.handoff, "verify_boot_handoff",
                              return_value=(self.pin, self.approved)) as verify, \
                 patch.object(owner, "_live_boot") as live:
                if reason is None:
                    gate(admission)
                    verify.assert_called_once_with(pin, admission)
                    live.assert_called_once_with(self.pin, self.approved)
                else:
                    with self.assertRaisesRegex(owner.env.EnvironmentRefused, f"^{reason}$"):
                        gate(admission)
                    verify.assert_not_called()
                    live.assert_not_called()

    def test_worker_revalidates_approval_before_native_runtime_construction(self):
        request = {"admission": {}, "validated_admission": {}, "owner": self.parent}
        with patch.object(owner.handoff, "verify_boot_handoff",
                          side_effect=owner.env.EnvironmentRefused("authority")) as verify, \
             patch.object(owner.mechanisms._TargetRuntimeCore, "__init__") as initialize:
            with self.assertRaisesRegex(owner.env.EnvironmentRefused, "^authority$"):
                owner._CombinedRecordUiTargetRuntime(request, {}, Path(owner.handoff.OWNED_ROOT))
            verify.assert_called_once_with(request["admission"], request["validated_admission"])
            initialize.assert_not_called()

    def test_live_boot_refuses_inherited_digest_or_record_drift_before_opening_handles(self):
        for digest, pin, approved in (("b" * 64, self.pin, self.approved),
                                     ("a" * 64, dict(self.pin, bytes=201), self.approved),
                                     ("a" * 64, self.pin, dict(self.approved, until_ns=201))):
            with self.subTest(digest=digest, bytes=pin["bytes"], until=approved["until_ns"]), \
                 patch.dict(owner.os.environ, {owner.handoff.HANDOFF_ENV: digest}), \
                 patch.object(owner.handoff, "read", return_value=(pin, approved)), \
                 patch.object(owner.mechanisms, "_ProcessApi") as native:
                with self.assertRaisesRegex(owner.env.EnvironmentRefused, "^handoff$"):
                    owner._live_boot(self.pin, self.approved)
                native.assert_not_called()

    def test_live_boot_joins_actual_processes_and_job_and_requires_handle_closure(self):
        for parent, ppid, ancestor, job, close, accepted in (
            (None, 101, 0, [101, 103], True, True),
            (None, 101, 0, [103], True, False),
            (self.parent, 102, 101, [103], True, True),
            (self.parent, 102, 999, [103], True, False),
            (self.parent, 999, 101, [103], True, False),
            (self.parent, 102, 101, [102], True, False),
            (self.parent, 102, 101, [103], False, False),
        ):
            with self.subTest(parent=parent, ppid=ppid, ancestor=ancestor, job=job, close=close):
                api, handles = Mock(), Mock()
                api.parent_pid.return_value = ancestor
                api.current_job_pids.return_value = job
                handles.add.side_effect = lambda pid, expected: (pid + 100, expected)
                handles.close.return_value = close
                with ExitStack() as stack:
                    for module, name, replacement in (
                        (owner.handoff, "read", Mock(return_value=(self.pin, self.approved))),
                        (owner.os, "getpid", Mock(return_value=103)),
                        (owner.os, "getppid", Mock(return_value=ppid)),
                        (owner.mechanisms, "_ProcessApi", Mock(return_value=api)),
                        (owner.process, "ProcessHandles", Mock(return_value=handles)),
                        (owner.env, "check_binding", Mock()),
                        (owner.handoff, "check_launch_window", Mock()),
                    ):
                        stack.enter_context(patch.object(module, name, replacement))
                    stack.enter_context(patch.dict(owner.os.environ, {owner.handoff.HANDOFF_ENV: "a" * 64}))
                    if accepted:
                        owner._live_boot(self.pin, self.approved, parent)
                        self.assertEqual(owner.env.check_binding.call_args_list, [
                            call(self.pin), call(self.approved["authority"]),
                            call(self.approved["attempt"]), call(self.approved["admission"]),
                        ])
                        owner.handoff.check_launch_window.assert_called_once_with(100, 200)
                    else:
                        with self.assertRaisesRegex(owner.env.EnvironmentRefused, "^identity$"):
                            owner._live_boot(self.pin, self.approved, parent)
                        owner.env.check_binding.assert_not_called()
                    handles.add.assert_any_call(self.supervisor["pid"], self.supervisor)
                    if parent is not None:
                        handles.add.assert_any_call(parent["pid"], parent)
                    handles.close.assert_called_once_with()

    def test_late_authority_attempt_or_admission_drift_refuses_before_launch(self):
        api, handles = Mock(), Mock()
        api.current_job_pids.return_value = [101, 103]
        handles.close.return_value = True
        for field in ("authority", "attempt", "admission"):
            with self.subTest(field=field):
                def changed(pin):
                    if pin == self.approved[field]:
                        raise owner.env.EnvironmentRefused("binding_changed")

                with patch.object(owner.handoff, "read", return_value=(self.pin, self.approved)), \
                     patch.object(owner.os, "getpid", return_value=103), \
                     patch.object(owner.os, "getppid", return_value=101), \
                     patch.object(owner.mechanisms, "_ProcessApi", return_value=api), \
                     patch.object(owner.process, "ProcessHandles", return_value=handles), \
                     patch.object(owner.env, "check_binding", side_effect=changed) as check, \
                     patch.object(owner.handoff, "check_launch_window") as launch, \
                     patch.dict(owner.os.environ, {owner.handoff.HANDOFF_ENV: "a" * 64}):
                    with self.assertRaisesRegex(owner.env.EnvironmentRefused, "^binding_changed$"):
                        owner._live_boot(self.pin, self.approved)
                    check.assert_any_call(self.approved[field])
                    launch.assert_not_called()

    def test_server_and_storage_transition_recheck_handoff_and_bind_prepared_digest(self):
        runtime = object.__new__(owner._CombinedRecordUiTargetRuntime)
        runtime.request = {"owner": self.parent}
        runtime._handoff_pin = self.pin
        runtime._handoff = self.approved
        guest = str(owner.contract.GUEST_ROOT)
        runtime.admission = {"guest": {"root": guest, "proposal": {"sha256": "b" * 64}}}
        runtime.proposal = {"prepare_proposal": {"sha256": "c" * 64}}
        with patch.object(owner, "_live_boot") as live, \
             patch.object(owner.env, "storage_transition") as transition, \
             patch.object(owner.mechanisms._TargetRuntimeCore, "start_server") as server:
            runtime.start_server()
            runtime._retain_guest()
            self.assertEqual(live.call_count, 3)
            live.assert_called_with(self.pin, self.approved, self.parent)
            server.assert_called_once_with()
            transition.assert_called_once_with(owner.storage.record_state, Path(guest), "retained",
                                               proposal_sha256="b" * 64,
                                               expected_prepare_sha256="c" * 64)
            live.side_effect = owner.env.EnvironmentRefused("handoff")
            with self.assertRaisesRegex(owner.env.EnvironmentRefused, "^handoff$"):
                runtime.start_server()
            with self.assertRaisesRegex(owner.env.EnvironmentRefused, "^handoff$"):
                runtime._retain_guest()
            self.assertEqual(server.call_count, 1)
            self.assertEqual(transition.call_count, 1)

    def test_delayed_retention_rechecks_launch_window_before_boot(self):
        runtime = object.__new__(owner._CombinedRecordUiTargetRuntime)
        runtime.request = {"owner": self.parent}
        runtime._handoff_pin = self.pin
        runtime._handoff = self.approved
        guest = str(owner.contract.GUEST_ROOT)
        runtime.admission = {"guest": {"root": guest, "proposal": {"sha256": "b" * 64}}}
        runtime.proposal = {"prepare_proposal": {"sha256": "c" * 64}}
        with patch.object(owner, "_live_boot",
                          side_effect=[None, owner.env.EnvironmentRefused("deadline")]), \
             patch.object(owner.env, "storage_transition") as transition:
            with self.assertRaisesRegex(owner.env.EnvironmentRefused, "^deadline$"):
                runtime._retain_guest()
            transition.assert_called_once()
