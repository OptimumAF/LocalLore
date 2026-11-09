"""Exercise the fixed SDK26 owner launch adapter without starting a device.

Copyright 2026 LocalLore contributors. SPDX-License-Identifier: Apache-2.0
"""
import os
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import Mock, call, patch

from benchmarks import archive_provider_platform_admission as candidate
from benchmarks import archive_provider_platform_closure as closure
from benchmarks import archive_provider_platform_controller as controller
from benchmarks import archive_provider_platform_handoff as handoff
from benchmarks import isolated_adb_owner as process
from benchmarks import owned_archive_provider_platform as owner
from benchmarks import receipt_avd_environment as env
from benchmarks import receipt_avd_storage as storage


class ArchiveProviderLaunchTests(unittest.TestCase):
    def setUp(self):
        self.root = Path(self.enterContext(TemporaryDirectory())).resolve()
        for name, leaf in (
            ("HANDOFF", "boot-handoff-v1.json"), ("ADMISSION", "admission-v1.json"),
            ("OWNED_ROOT", "owned-v1"), ("COMPLETION", "activation-completion-v1.json"),
            ("RUN", "run-proposal-v1.json"),
        ):
            self.enterContext(patch.object(candidate, name, self.root / leaf))
        self.python = r"C:\Synthetic\python.exe"
        self.supervisor = self.identity(7101)
        self.parent = self.identity(7102)
        self.worker = self.identity(7103)
        self.admission_pin = self.pin(candidate.ADMISSION)
        self.ledger = self.pin(self.root / "ledger-v1.json")
        self.record = dict(
            authority=self.pin(self.root / "activation-authority-v1.json"),
            attempt=self.pin(self.root / "activation-claim-v1.json"),
            supervisor=self.supervisor, began_ns=100, until_ns=200,
        )
        self.handoff_pin = self.pin(candidate.HANDOFF)
        self.approved = dict(admission=self.admission_pin, ledger=self.ledger,
                             candidate=self.pin(self.root / "candidate-v1.json"))
        self.prepare_pin = self.pin(self.root / "prepare.json")
        self.run_pin = self.pin(self.root / "run.json")
        self.proposal = dict(prepare_proposal=self.prepare_pin, host_free_min={"D:": 40 * 1024**3})
        self.inputs = (self.run_pin, self.prepare_pin)
        self.launch = (self.handoff_pin, self.record, self.approved, self.inputs)
        self.admission = dict(guest={"root": str(self.root / "avd-v1"), "proposal": self.run_pin},
                              python={"executable": {"path": self.python}})
        self.spawn = self.enterContext(patch("subprocess.Popen", side_effect=AssertionError("unexpected child")))
        self.socket = self.enterContext(patch("socket.socket", side_effect=AssertionError("unexpected socket")))
        self.sdk_prepare = self.enterContext(patch.object(env, "prepare"))
        self.addCleanup(self.assert_no_dispatch)

    def assert_no_dispatch(self):
        self.spawn.assert_not_called()
        self.socket.assert_not_called()
        self.sdk_prepare.assert_not_called()

    def identity(self, pid):
        return dict(pid=pid, creation_filetime=100000 + pid, executable=self.python)

    @staticmethod
    def pin(path):
        return dict(path=str(path), bytes=1, sha256="a" * 64)

    def runtime(self):
        runtime = object.__new__(owner._ArchiveProviderPlatformRuntime)
        runtime._launch = self.launch
        runtime.request = {"owner": self.parent}
        runtime.admission = self.admission
        runtime.proposal = self.proposal
        runtime.root = self.root
        runtime.binding = self.admission_pin
        runtime._running_binding = self.pin(self.root / "running.json")
        runtime.clients_closed = True
        return runtime

    def test_live_parent_rechecks_exact_job_and_bound_inputs(self):
        api, handles = Mock(), Mock()
        api.current_job_pids.return_value = [self.supervisor["pid"], self.parent["pid"]]
        handles.close.return_value = True
        with (patch.dict(os.environ, {owner.HANDOFF_ENV: self.handoff_pin["sha256"]}, clear=True),
              patch.object(owner.os, "getppid", return_value=self.supervisor["pid"]),
              patch.object(owner.os, "getpid", return_value=self.parent["pid"]),
              patch.object(owner.mechanisms, "_ProcessApi", return_value=api),
              patch.object(process, "ProcessHandles", return_value=handles),
              patch.object(env, "check_binding") as check,
              patch.object(handoff, "check_window") as window):
            owner._live_boot(*self.launch)
        handles.add.assert_called_once_with(self.supervisor["pid"], self.supervisor)
        handles.guard.assert_called_once_with()
        handles.close.assert_called_once_with()
        self.assertEqual(check.call_args_list, [call(pin) for pin in
            (self.handoff_pin, self.record["authority"], self.record["attempt"],
             self.admission_pin, *self.inputs)])
        window.assert_called_once_with(100, 200, minimum_seconds=handoff.LAUNCH_TAIL_SECONDS)

    def test_live_parent_refuses_missing_job_member_and_uncertain_handle_close(self):
        for pids, closed in (([self.parent["pid"]], True),
                             ([self.supervisor["pid"], self.parent["pid"]], False)):
            with self.subTest(pids=pids, closed=closed):
                api, handles = Mock(), Mock()
                api.current_job_pids.return_value = pids
                handles.close.return_value = closed
                with (patch.dict(os.environ, {owner.HANDOFF_ENV: self.handoff_pin["sha256"]}, clear=True),
                      patch.object(owner.os, "getppid", return_value=self.supervisor["pid"]),
                      patch.object(owner.os, "getpid", return_value=self.parent["pid"]),
                      patch.object(owner.mechanisms, "_ProcessApi", return_value=api),
                      patch.object(process, "ProcessHandles", return_value=handles),
                      patch.object(env, "check_binding") as check):
                    with self.assertRaisesRegex(env.EnvironmentRefused, "^identity$"):
                        owner._live_boot(*self.launch)
                handles.close.assert_called_once_with()
                check.assert_not_called()

    def test_live_worker_checks_parent_ancestry_in_its_nested_job(self):
        api, handles = Mock(), Mock()
        api.current_job_pids.return_value = [self.worker["pid"]]
        api.parent_pid.return_value = self.supervisor["pid"]
        handles.add.side_effect = [("supervisor", self.supervisor), ("parent", self.parent)]
        handles.close.return_value = True
        with (patch.dict(os.environ, {owner.HANDOFF_ENV: self.handoff_pin["sha256"]}, clear=True),
              patch.object(owner.os, "getppid", return_value=self.parent["pid"]),
              patch.object(owner.os, "getpid", return_value=self.worker["pid"]),
              patch.object(owner.mechanisms, "_ProcessApi", return_value=api),
              patch.object(process, "ProcessHandles", return_value=handles),
              patch.object(env, "check_binding"),
              patch.object(handoff, "check_window")):
            owner._live_boot(*self.launch, parent=self.parent)
        self.assertEqual(handles.add.call_args_list, [
            call(self.supervisor["pid"], self.supervisor), call(self.parent["pid"], self.parent),
        ])
        api.parent_pid.assert_called_once_with("parent")
        handles.close.assert_called_once_with()

    def test_live_worker_refuses_foreign_parent_ancestry_before_replay(self):
        api, handles = Mock(), Mock()
        api.current_job_pids.return_value = [self.worker["pid"]]
        api.parent_pid.return_value = 42
        handles.add.side_effect = [("supervisor", self.supervisor), ("parent", self.parent)]
        handles.close.return_value = True
        with (patch.dict(os.environ, {owner.HANDOFF_ENV: self.handoff_pin["sha256"]}, clear=True),
              patch.object(owner.os, "getppid", return_value=self.parent["pid"]),
              patch.object(owner.os, "getpid", return_value=self.worker["pid"]),
              patch.object(owner.mechanisms, "_ProcessApi", return_value=api),
              patch.object(process, "ProcessHandles", return_value=handles),
              patch.object(env, "check_binding") as check):
            with self.assertRaisesRegex(env.EnvironmentRefused, "^identity$"):
                owner._live_boot(*self.launch, parent=self.parent)
        handles.close.assert_called_once_with()
        check.assert_not_called()

    def test_bad_handoff_digest_or_path_refuses_before_native_handles(self):
        for pin, digest in ((self.handoff_pin, "b" * 64),
                            (self.pin(self.root / "foreign-handoff.json"), "a" * 64)):
            with (self.subTest(pin=pin, digest=digest),
                  patch.dict(os.environ, {owner.HANDOFF_ENV: digest}, clear=True),
                  patch.object(owner.mechanisms, "_ProcessApi") as api):
                with self.assertRaisesRegex(env.EnvironmentRefused, "^handoff$"):
                    owner._live_boot(pin, *self.launch[1:])
                api.assert_not_called()

    def test_runtime_replays_and_checks_live_before_shared_initialization(self):
        sequence = Mock()
        sequence.replay.return_value = self.launch
        sequence.initialize.return_value = None
        request = dict(admission=self.admission_pin, validated_admission=self.admission, owner=self.parent)
        request_pin = self.pin(self.root / "request-v1.json")
        with (patch.object(owner, "_load_live_boot", sequence.replay),
              patch.object(owner, "_live_boot", sequence.live),
              patch.object(owner.mechanisms._TargetRuntimeCore, "__init__", sequence.initialize)):
            owner._ArchiveProviderPlatformRuntime(request, request_pin, self.root)
            self.assertEqual(sequence.mock_calls, [
                call.replay(self.admission_pin, self.admission),
                call.live(*self.launch, parent=self.parent),
                call.initialize(request, request_pin, self.root),
            ])
            sequence.reset_mock()
            sequence.live.side_effect = env.EnvironmentRefused("identity")
            with self.assertRaisesRegex(env.EnvironmentRefused, "^identity$"):
                owner._ArchiveProviderPlatformRuntime(request, request_pin, self.root)
            sequence.initialize.assert_not_called()

    def test_prelaunch_orders_live_checks_resources_ports_and_ledger(self):
        runtime = self.runtime()
        sequence = Mock()
        with (patch.object(owner, "_live_boot", sequence.live),
              patch.object(owner, "_check_resources", sequence.resources),
              patch.object(env, "ports_free", sequence.ports),
              patch.object(env, "check_binding", sequence.binding)):
            runtime._prelaunch(self.proposal)
        self.assertEqual(sequence.mock_calls, [
            call.live(*self.launch, parent=self.parent), call.binding(self.ledger),
            call.resources(self.proposal), call.ports(),
            call.live(*self.launch, parent=self.parent), call.binding(self.ledger),
        ])

    def test_host_budget_requires_the_separate_records_allowance(self):
        floor = self.proposal["host_free_min"]["D:"]
        allowance = 256 * 1024**2
        with patch.object(env, "resource_facts", return_value={"free_bytes": {"D:": floor + allowance - 1}}) as facts:
            with self.assertRaisesRegex(env.EnvironmentRefused, "^records_capacity$"):
                owner._check_resources(self.proposal)
            facts.assert_called_once_with(self.proposal)
            facts.return_value = {"free_bytes": {"D:": floor + allowance}}
            owner._check_resources(self.proposal)

    def test_stale_ledger_refuses_before_probing_ports_or_delegating_server_launch(self):
        runtime = self.runtime()
        env.create_json(candidate.RUN, self.proposal)
        runtime.admission = dict(self.admission, guest=dict(self.admission["guest"], proposal=env.binding(candidate.RUN)))
        with (patch.object(owner, "_live_boot"),
              patch.object(env, "check_binding", side_effect=env.EnvironmentRefused("binding_changed")),
              patch.object(owner, "_check_resources") as resources,
              patch.object(env, "ports_free") as ports,
              patch.object(owner.mechanisms._TargetRuntimeCore, "start_server") as start):
            with self.assertRaisesRegex(env.EnvironmentRefused, "^binding_changed$"):
                runtime.start_server()
        resources.assert_not_called()
        ports.assert_not_called()
        start.assert_not_called()

    def test_retention_passes_the_exact_ledger_to_the_locked_transition(self):
        runtime = self.runtime()
        sequence = Mock()
        expected = call.retain(
            storage.record_state, Path(self.admission["guest"]["root"]), "retained",
            proposal_sha256=self.run_pin["sha256"], expected_prepare_sha256=self.prepare_pin["sha256"],
            expected_ledger=self.ledger,
        )
        with (patch.object(runtime, "_prelaunch", sequence.prelaunch),
              patch.object(env, "storage_transition", sequence.retain),
              patch.object(owner, "_live_boot", sequence.live)):
            runtime._retain_guest()
            self.assertEqual(sequence.mock_calls, [
                call.prelaunch(self.proposal), expected, call.live(*self.launch, parent=self.parent),
            ])
            sequence.reset_mock()
            sequence.retain.side_effect = env.EnvironmentRefused("storage_ledger_changed")
            with self.assertRaisesRegex(env.EnvironmentRefused, "^storage_ledger_changed$"):
                runtime._retain_guest()
            self.assertEqual(sequence.mock_calls, [call.prelaunch(self.proposal), expected])

    def test_admitted_guest_publishes_scoped_stop_and_tracks_controller_closure(self):
        for outcome, observer_closed, prior_closed in (
            ("completed", True, True), ("refused", True, True), ("completed", False, True),
            ("completed", True, False),
        ):
            with self.subTest(outcome=outcome, observer_closed=observer_closed, prior_closed=prior_closed):
                with TemporaryDirectory() as root:
                    runtime = self.runtime()
                    runtime.root = Path(root)
                    runtime.clients_closed = prior_closed
                    ready = ("ready", "job")
                    with (patch.object(owner.mechanisms._TargetRuntimeCore, "admit_guest", return_value=ready),
                          patch.object(owner, "_live_boot"),
                          patch.object(runtime, "guard"),
                          patch.object(controller, "run", return_value={
                              "outcome": outcome, "observer_handles_closed": observer_closed,
                          }) as run):
                        self.assertEqual(runtime.admit_guest(), ready)
                    run.assert_called_once_with(self.admission_pin, runtime.running_binding)
                    self.assertIs(runtime.clients_closed, prior_closed and outcome == "completed" and observer_closed)
                    stop = runtime.root / "stop-v1.json"
                    self.assertEqual(env.read_json(stop), dict(
                        version=1, protocol=owner.PROTOCOL, admission_sha256=self.admission_pin["sha256"],
                        action="stop",
                    ))
                    self.assertFalse((runtime.root / "stop.pending-v1.json").exists())

    def test_controller_failure_still_requests_stop_and_retains_uncertain_charge(self):
        runtime = self.runtime()
        with (patch.object(owner.mechanisms._TargetRuntimeCore, "admit_guest"),
              patch.object(owner, "_live_boot"), patch.object(runtime, "guard"),
              patch.object(controller, "run", side_effect=env.EnvironmentRefused("binding"))):
            with self.assertRaisesRegex(env.EnvironmentRefused, "^binding$"):
                runtime.admit_guest()
        self.assertFalse(runtime.clients_closed)
        self.assertTrue((self.root / "stop-v1.json").is_file())

    def test_cold_owner_refuses_wrong_env_path_and_missing_handoff_before_dispatch(self):
        args = ["--admission", str(candidate.ADMISSION), "--admission-sha256", self.admission_pin["sha256"]]
        cases = (
            (args, {}), (args, {owner.HANDOFF_ENV: "invalid"}),
            (args, {owner.HANDOFF_ENV: self.handoff_pin["sha256"]}),
            (["_worker"], {owner.HANDOFF_ENV: self.handoff_pin["sha256"]}),
            ([*args[:1], str(self.root / "foreign.json"), *args[2:]],
             {owner.HANDOFF_ENV: self.handoff_pin["sha256"]}),
        )
        for argv, variables in cases:
            with (self.subTest(argv=argv, variables=variables),
                  patch.dict(os.environ, variables, clear=True),
                  patch.object(owner.mechanisms, "_main_profile") as dispatch,
                  patch.object(owner.mechanisms, "_ProcessApi") as api):
                self.assertEqual(owner.main(argv), 1)
                dispatch.assert_not_called()
                api.assert_not_called()

    def parent_completion(self, closure_error=None):
        env.create_json(candidate.HANDOFF, self.record)
        env.create_json(candidate.ADMISSION, self.admission)
        handoff_pin = env.binding(candidate.HANDOFF)
        admission_pin = env.binding(candidate.ADMISSION)
        launch = (handoff_pin, self.record, dict(self.approved, admission=admission_pin), self.inputs)
        args = ["--admission", str(candidate.ADMISSION), "--admission-sha256", admission_pin["sha256"]]
        result = {"controller": self.pin(self.root / "controller.json")}

        def dispatch(argv, *, _contract, _verification, _runtime_type, _admission_check):
            self.assertEqual(argv, args)
            self.assertIs(_contract, owner)
            self.assertIs(_verification, owner.REPLAY)
            self.assertIs(_runtime_type, owner._ArchiveProviderPlatformRuntime)
            _admission_check(self.admission)
            return 0

        with (patch.dict(os.environ, {owner.HANDOFF_ENV: handoff_pin["sha256"]}, clear=True),
              patch.object(owner.mechanisms, "_main_profile", side_effect=dispatch),
              patch.object(owner, "_load_live_boot", return_value=launch),
              patch.object(owner, "_live_boot"), patch.object(handoff, "check_window"),
              patch.object(env, "process_identity", return_value=self.parent),
              patch.object(env, "check_binding"),
              patch.object(closure, "verify_result", return_value=result, side_effect=closure_error) as verify):
            status = owner.main(args)
            verify.assert_called_once_with(admission_pin, self.parent)
        return status, admission_pin, result

    def test_parent_refuses_unverified_closure_without_publishing_completion(self):
        status, _, _ = self.parent_completion(env.EnvironmentRefused("cleanup"))
        self.assertEqual(status, 1)
        self.assertFalse(candidate.COMPLETION.exists())

    def test_parent_completion_requires_independently_observed_owner_closure(self):
        status, admission_pin, result = self.parent_completion()
        self.assertEqual(status, 0)
        completed = env.read_json(candidate.COMPLETION)
        self.assertEqual(completed["admission"], admission_pin)
        self.assertEqual(completed["controller"], result["controller"])
