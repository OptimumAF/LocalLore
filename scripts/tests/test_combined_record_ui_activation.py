"""Synthetic process and evidence ports for the SDK21 Story Record supervisor.

Copyright 2026 LocalLore contributors. SPDX-License-Identifier: Apache-2.0
"""

from contextlib import ExitStack, contextmanager
import copy
import hashlib
from io import BytesIO
from pathlib import Path
from types import SimpleNamespace
import unittest
from unittest.mock import Mock, call, patch

from benchmarks import combined_record_ui_activation as activation
from benchmarks import combined_record_ui_handoff as handoff
from scripts.tests.test_owned_combined_record_ui_contract import admission as profile_admission
from scripts.tests.test_owned_target_contract import pin, running


NANOSECOND = 10**9
REFUSED = (ValueError, RuntimeError)


def terminal(code=0):
    return dict(status="child_exited", cleanup_complete=True, elapsed_ms=10,
                output_capture_complete=True, worker_returncode=code,
                stdout_bytes=0, stderr_bytes=0)


class SyntheticRun:
    """The real supervisor consumes deterministic records and inert process ports."""

    def __init__(self, *, controller_code=0, known=True):
        self.records = {}
        self.events = []
        self.now_ns = 500 * NANOSECOND
        self.began_ns = 450 * NANOSECOND
        self.until_ns = 2100 * NANOSECOND
        self.admission = profile_admission()
        self.admission.update(root=str(handoff.OWNED_ROOT), seconds=handoff.OWNER_SECONDS)
        self.admission["server"].update(root=str(handoff.OWNED_ROOT / "server"), seconds=handoff.OWNER_SECONDS)
        self.admission_pin = self.save(handoff.ADMISSION, self.admission)
        self.descriptor = running(self.admission)
        self.descriptor.update(admission=self.admission_pin, protocol=activation.contract.PROTOCOL)
        self.running_path = handoff.OWNED_ROOT / "running-v1.json"
        self.running_pin = self.save(self.running_path, self.descriptor)
        self.owner_identity = self.descriptor["owner"]
        self.worker_identity = self.descriptor["worker"]
        self.caller = dict(self.worker_identity, pid=9901)
        self.authority_pin = self.save(handoff.AUTHORITY, {"synthetic": "approval"})
        self.attempt_pin = self.save(handoff.ATTEMPT, {"synthetic": "attempt"})
        self.operation_parent = dict(self.owner_identity, pid=9903)
        self.operation_worker = dict(self.worker_identity, pid=9902)
        self.operation_request_pin = self.save(activation.OPERATION_REQUEST, dict(
            version=1, scope=handoff.OPERATION_SCOPE, authority=self.authority_pin,
            attempt=self.attempt_pin, began_ns=self.began_ns, parent=self.operation_parent,
        ))
        self.operation_claim = dict(request=self.operation_request_pin, worker=self.operation_worker)
        self.save(activation.OPERATION_STARTED, self.operation_claim)
        self.save(activation.OPERATION_CLAIM, self.operation_claim)
        self.handoff_pin = self.save(handoff.HANDOFF, dict(
            version=1, scope=handoff.HANDOFF_SCOPE, authority=self.authority_pin,
            attempt=self.attempt_pin, admission=self.admission_pin, supervisor=self.worker_identity,
            began_ns=self.began_ns, until_ns=self.until_ns,
        ))
        self.closure = dict(
            owner=self.save(handoff.OWNED_ROOT / "result-v1.json", {"synthetic": "qualified owner"}),
            closure=self.save(handoff.GUEST / "guest-storage-closure-v1.json", {"synthetic": "closed guest"}),
            ledger=self.save(handoff.LEDGER, {"synthetic": "closed ledger"}),
        )
        self.capture_pins = {
            name: self.save(activation.CONTROL / "owner-console-v1" / f"owner-{name}-v1.bin", b"")
            for name in ("stdout", "stderr")
        }
        self.controller_pin = self.save(
            handoff.OWNED_ROOT / "controller-v1" / activation.controller.RESULT_FILE,
            {"outcome": "completed" if controller_code == 0 else "refused"},
        )
        record = terminal(controller_code)
        self.controller_job = dict(
            terminal=record,
            pin=self.save(activation.CONTROL / "controller-supervisor-v1.json", record),
            request=self.save(activation.CONTROL / "controller-request-v1.json", {"synthetic": "request"}),
            worker=self.caller, known=known,
        )
        self.exited = False
        self.child = Mock(pid=self.owner_identity["pid"])
        self.child.poll.side_effect = lambda: 0 if self.exited else None
        self.child.wait.side_effect = lambda *args, **kwargs: self.child.poll()
        self.capture = Mock()
        self.capture.close.side_effect = lambda: self.event("capture_close", True)
        self.capture.readers = [object(), object()]
        self.capture.pipes_closed = True
        self.observer = Mock()
        self.observer.close.side_effect = lambda: self.event("observer_close", True)
        self.launch = Mock(return_value=self.child)
        self.observe = Mock(return_value=self.observer)
        self.supervise = Mock(side_effect=self.supervise_controller)
        self.stop = Mock(side_effect=self.stop_owner)
        self.check_closure = Mock(side_effect=lambda *args: self.event("closure_replay", self.closure))
        self.check_controller = Mock(side_effect=lambda *args: self.event("controller_replay", {"outcome": "completed"}))

    def event(self, name, value=None):
        self.events.append(name)
        return value

    def supervise_controller(self, *args, **kwargs):
        self.events.append("controller")
        if not self.controller_job["known"]:
            self.exited = True
        return copy.deepcopy(self.controller_job)

    def stop_owner(self, *args):
        self.events.append("stop")
        self.exited = True

    def save(self, path, value):
        path = Path(path)
        raw = value if isinstance(value, bytes) else activation.env.encoded(value)
        binding = pin(path, size=len(raw), sha=hashlib.sha256(raw).hexdigest())
        self.records[path] = binding, copy.deepcopy(value)
        return copy.deepcopy(binding)

    def read(self, path, *args, **kwargs):
        if Path(path) not in self.records:
            raise activation.env.EnvironmentRefused("binding")
        return copy.deepcopy(self.records[Path(path)])

    def bound(self, binding, path, *args, **kwargs):
        actual, value = self.read(path)
        if binding != actual:
            raise activation.env.EnvironmentRefused("binding")
        return value

    def check(self, binding):
        self.bound(binding, binding["path"])

    def advance(self, seconds):
        self.now_ns += max(10, seconds) * NANOSECOND

    @contextmanager
    def ports(self):
        with ExitStack() as stack:
            for target, name, substitute in (
                (activation, "_read", self.read),
                (activation, "_save", self.save),
                (activation, "_identity", lambda pid, *args: self.owner_identity),
                (activation, "_supervise", self.supervise),
                (activation, "_stop", self.stop),
                (activation, "_capture_pins", lambda path: copy.deepcopy(self.capture_pins)),
                (activation, "verify_closure", self.check_closure),
                (activation, "LiveOwnedCombinedRecordUiTarget", self.observe),
                (activation.subprocess, "Popen", self.launch),
                (activation.process, "ServerCapture", lambda path: self.capture),
                (activation.process, "_owner_ok", lambda value, root: value["worker_returncode"] == 0),
                (activation.controller, "verify_controller_result", self.check_controller),
                (activation.env, "check_binding", self.check),
                (activation.time, "monotonic_ns", lambda: self.now_ns),
                (activation.time, "sleep", self.advance),
                (activation.os.path, "lexists", lambda path: Path(path) in self.records),
                (handoff, "read", self.read),
                (handoff, "at", self.bound),
            ):
                stack.enter_context(patch.object(target, name, substitute))
            yield

    def run(self):
        with self.ports():
            return activation._run_owned(self.admission_pin, self.admission, self.until_ns,
                                         began_ns=self.began_ns, handoff_pin=self.handoff_pin)


class CombinedRecordUiActivationTests(unittest.TestCase):
    def test_success_replays_exact_controller_caller_and_known_owner_closure(self):
        run = SyntheticRun()
        result = run.run()

        self.assertIs(result["passed"], True)
        self.assertIs(result["feature_acceptance"], False)
        self.assertEqual(result["closure"], run.closure)
        self.assertEqual(result["controller"], run.controller_pin)
        argv = run.launch.call_args.args[0]
        self.assertEqual(Path(argv[-5]).name, activation.contract.OWNER_SCRIPT)
        self.assertEqual(argv[-4:], ["--admission", run.admission_pin["path"],
                                    "--admission-sha256", run.admission_pin["sha256"]])
        run.stop.assert_called_once_with(run.observer, handoff.OWNED_ROOT, run.admission_pin)
        run.check_closure.assert_called_once_with(run.admission_pin, run.admission,
                                                  run.running_pin, run.owner_identity)
        run.check_controller.assert_called_once_with(run.controller_pin, run.admission_pin,
                                                     run.running_pin, run.caller)
        self.assertEqual(run.events, ["controller", "stop", "observer_close", "capture_close",
                                      "closure_replay", "controller_replay"])

    def test_known_failed_controller_still_gets_stop_and_verified_closure(self):
        run = SyntheticRun(controller_code=1)
        result = run.run()

        self.assertIs(result["passed"], False)
        self.assertEqual(result["closure"], run.closure)
        run.stop.assert_called_once()
        run.check_closure.assert_called_once()
        self.assertLess(run.events.index("stop"), run.events.index("closure_replay"))
        self.assertEqual(run.read(run.controller_pin["path"])[0], run.controller_pin)

    def test_unknown_controller_cleanup_cannot_publish_a_stop_or_qualify(self):
        run = SyntheticRun(known=False)
        result = run.run()

        self.assertIs(result["passed"], False)
        run.stop.assert_not_called()
        run.check_closure.assert_not_called()
        run.check_controller.assert_not_called()
        run.observer.close.assert_called_once()
        run.capture.close.assert_called_once()
        self.assertEqual(run.read(run.controller_job["pin"]["path"])[1], terminal())

    def test_wrong_ready_owner_cannot_dispatch_controller(self):
        run = SyntheticRun()
        run.descriptor["owner"] = dict(run.owner_identity, pid=run.owner_identity["pid"] + 100)
        run.save(run.running_path, run.descriptor)
        result = run.run()

        self.assertIs(result["passed"], False)
        self.assertEqual(result["reason"], "identity")
        run.observe.assert_not_called()
        run.supervise.assert_not_called()
        run.stop.assert_not_called()
        run.check_closure.assert_not_called()
        run.capture.close.assert_called_once()

    def test_lost_closure_replay_refuses_an_otherwise_successful_test(self):
        run = SyntheticRun()
        run.check_closure.side_effect = activation.env.EnvironmentRefused("closure")
        result = run.run()

        self.assertIs(result["passed"], False)
        self.assertIsNone(result["closure"])
        run.stop.assert_called_once()
        run.check_closure.assert_called_once()
        self.assertEqual(run.read(run.controller_pin["path"])[0], run.controller_pin)

    def test_capture_close_failure_preserves_attempt_and_prevents_a_pass(self):
        run = SyntheticRun()
        run.capture.close.side_effect = lambda: run.event("capture_close", False)
        result = run.run()

        self.assertIs(result["passed"], False)
        self.assertEqual(run.read(run.controller_pin["path"])[0], run.controller_pin)
        self.assertEqual(run.read(run.controller_job["pin"]["path"])[0], run.controller_job["pin"])
        run.stop.assert_called_once()
        run.capture.close.assert_called_once()

    def test_expired_budget_refuses_before_owner_spawn(self):
        run = SyntheticRun()
        run.until_ns = run.now_ns
        with run.ports():
            try:
                result = activation._run_owned(run.admission_pin, run.admission, run.until_ns,
                                               began_ns=run.began_ns, handoff_pin=run.handoff_pin)
            except REFUSED:
                pass
            else:
                self.assertIs(result["passed"], False)
        run.launch.assert_not_called()
        run.supervise.assert_not_called()
        run.stop.assert_not_called()

    def test_unexpired_but_insufficient_controller_budget_cannot_launch_owner(self):
        run = SyntheticRun()
        run.until_ns = run.now_ns + activation.controller.SECONDS * NANOSECOND
        result = run.run()

        self.assertIs(result["passed"], False)
        self.assertEqual(result["reason"], "deadline")
        run.launch.assert_not_called()
        run.supervise.assert_not_called()

    def test_replaced_handoff_refuses_before_owner_launch(self):
        run = SyntheticRun()
        _, record = run.read(handoff.HANDOFF)
        run.save(handoff.HANDOFF, dict(record, began_ns=record["began_ns"] - 1))
        result = run.run()
        run.launch.assert_not_called()
        self.assertFalse(result["passed"])
        self.assertEqual(result["reason"], "handoff")

    def test_capture_reads_cannot_exceed_the_shared_output_budget(self):
        root = activation.CONTROL / "owner-console-v1"
        first = b"y" * 16
        with patch.object(activation.files, "_read", side_effect=[first, b"z"]) as read:
            pins = activation._capture_pins(root)
        self.assertEqual(pins["stdout"]["bytes"], len(first))
        self.assertEqual(pins["stderr"]["bytes"], 1)
        self.assertEqual(read.call_args_list[0].args,
                         (root / "owner-stdout-v1.bin", activation.process.CAP))
        self.assertEqual(read.call_args_list[1].args,
                         (root / "owner-stderr-v1.bin", activation.process.CAP - len(first)))

    def test_stop_uses_the_fixed_admission_and_checks_live_owner_before_publication(self):
        run = SyntheticRun()
        events = []
        pending = handoff.OWNED_ROOT / "stop.pending-v1.json"
        stop = handoff.OWNED_ROOT / "stop-v1.json"

        def save(path, value):
            self.assertEqual(path, pending)
            self.assertEqual(value, dict(version=1, protocol=activation.contract.PROTOCOL,
                                         admission_sha256=run.admission_pin["sha256"], action="stop"))
            events.append("pending")
            return run.save(path, value)

        run.observer.guard.side_effect = lambda **kwargs: events.append("guard")
        with patch.object(activation, "_save", side_effect=save), \
             patch.object(Path, "rename", autospec=True,
                          side_effect=lambda *args: events.append("publish")) as rename:
            activation._stop(run.observer, handoff.OWNED_ROOT, run.admission_pin)

        self.assertEqual(events, ["guard", "pending", "guard", "publish"])
        rename.assert_called_once_with(pending, stop)

    def test_expiry_during_stop_write_preserves_pending_record_and_refuses_publish(self):
        run = SyntheticRun()
        pending = handoff.OWNED_ROOT / "stop.pending-v1.json"
        run.observer.guard.side_effect = (None, activation.env.EnvironmentRefused("deadline"))
        with patch.object(activation, "_save", side_effect=run.save), \
             patch.object(Path, "rename") as rename, self.assertRaises(REFUSED):
            activation._stop(run.observer, handoff.OWNED_ROOT, run.admission_pin)

        self.assertEqual(run.read(pending)[1]["admission_sha256"], run.admission_pin["sha256"])
        rename.assert_not_called()

    def test_failed_controller_has_known_job_closure_only_with_coherent_capture(self):
        run = SyntheticRun(controller_code=1)
        kind = "controller"
        started = activation._started_path(kind)
        run.save(started, dict(request=run.controller_job["request"], worker=run.caller))
        with run.ports():
            actual = activation._job_evidence(kind, run.controller_job["pin"])
            self.assertEqual(actual[0]["worker_returncode"], 1)
            self.assertEqual(actual[-1], run.caller)
            for change in (dict(cleanup_complete=1), dict(worker_returncode=False),
                           dict(status="expired"), dict(stdout_bytes=3)):
                with self.subTest(change=change), self.assertRaises(REFUSED):
                    updated = run.save(activation._terminal_path(kind), dict(terminal(1), **change))
                    activation._job_evidence(kind, updated)

    def test_runtime_worker_requires_the_exact_started_identity_in_a_job(self):
        run = SyntheticRun()
        kind = "runtime"
        request = dict(version=1, scope=activation.SCOPE, kind=kind,
                       admission=run.admission_pin, authority=run.authority_pin, attempt=run.attempt_pin,
                       began_ns=run.began_ns, until_ns=run.until_ns, running=None, parent=run.owner_identity)
        request_pin = run.save(activation._request_path(kind), request)
        started = dict(request=request_pin, worker=run.worker_identity)
        run.save(activation._started_path(kind), started)
        identity = Mock(side_effect=lambda pid, expected: expected)
        job_pids = Mock(return_value=[run.worker_identity["pid"]])
        raw = activation.BARRIER + activation.env.encoded(request_pin)

        with run.ports(), patch.object(activation, "_identity", identity), \
             patch.object(activation.os, "getppid", return_value=run.owner_identity["pid"]), \
             patch.object(activation.os, "getpid", return_value=run.worker_identity["pid"]), \
             patch.object(activation.mechanisms, "_ProcessApi", return_value=SimpleNamespace(current_job_pids=job_pids)):
            with patch.object(activation.sys, "stdin", SimpleNamespace(buffer=BytesIO(raw))):
                self.assertEqual(activation._enter(kind), (request_pin, request, run.worker_identity))

            self.assertEqual(identity.call_args_list, [
                call(run.owner_identity["pid"], run.owner_identity),
                call(run.worker_identity["pid"], run.worker_identity),
            ])
            job_pids.return_value = [run.worker_identity["pid"] + 1]
            with patch.object(activation.sys, "stdin", SimpleNamespace(buffer=BytesIO(raw))), \
                 self.assertRaisesRegex(activation.env.EnvironmentRefused, "job"):
                activation._enter(kind)

    def test_runtime_publishes_handoff_from_the_supervised_worker_before_owner_dispatch(self):
        run = SyntheticRun()
        run.records.pop(handoff.HANDOFF)
        request = dict(admission=run.admission_pin, authority=run.authority_pin, attempt=run.attempt_pin,
                       running=None, began_ns=run.began_ns, until_ns=run.until_ns, parent=run.operation_worker)
        request_pin = run.save(activation._request_path("runtime"), request)

        def dispatch(admission_pin, admission, until_ns, *, began_ns, handoff_pin):
            self.assertEqual(admission_pin, run.admission_pin)
            self.assertEqual(admission, run.admission)
            self.assertEqual((began_ns, until_ns), (run.began_ns, run.until_ns))
            self.assertEqual(handoff_pin, run.read(handoff.HANDOFF)[0])
            self.assertEqual(run.read(handoff.HANDOFF)[1], dict(
                version=1, scope=handoff.HANDOFF_SCOPE, supervisor=run.worker_identity,
                **{key: value for key, value in request.items() if key not in ("running", "parent")},
            ))
            return dict(passed=False, feature_acceptance=False, reason="synthetic-refusal")

        with run.ports(), patch.object(activation, "_enter",
                 return_value=(request_pin, request, run.worker_identity)) as enter, \
             patch.object(activation, "_inputs", return_value=run.admission) as inputs, \
             patch.object(activation, "_run_owned", side_effect=dispatch) as owned:
            self.assertEqual(activation.main(["_runtime"]), 1)

        enter.assert_called_once_with("runtime")
        inputs.assert_called_once_with(run.admission_pin, run.authority_pin, run.attempt_pin)
        owned.assert_called_once()
        _, retained = run.read(activation.CONTROL / "runtime-result-v1.json")
        self.assertEqual(retained, dict(passed=False, feature_acceptance=False, reason="synthetic-refusal",
                                        request=request_pin, worker=run.worker_identity,
                                        handoff=run.read(handoff.HANDOFF)[0]))

    def test_controller_child_refuses_a_foreign_parent_or_operation_window(self):
        run = SyntheticRun()
        request = dict(admission=run.admission_pin, authority=run.authority_pin, attempt=run.attempt_pin,
                       running=run.running_pin, parent=run.worker_identity,
                       began_ns=run.began_ns, until_ns=run.until_ns)
        for changes, exit_code in (({}, 0), (dict(parent=run.owner_identity), 1),
                                   (dict(until_ns=run.until_ns - 1), 1)):
            request_pin = run.save(activation._request_path("controller"), dict(request, **changes))
            with self.subTest(changes=changes), run.ports(), patch.object(
                activation, "_enter", return_value=(request_pin, dict(request, **changes), run.caller),
            ), patch.object(activation.controller, "run", return_value={"outcome": "completed"}) as controller:
                self.assertEqual(activation.main(["_controller"]), exit_code)
            if changes:
                controller.assert_not_called()
            else:
                controller.assert_called_once_with(run.admission_pin, run.running_pin)

    def test_outer_runtime_replay_joins_live_handoff_controller_and_closure_records(self):
        run = SyntheticRun()
        result = run.run()
        self.assertIs(result["passed"], True)
        request = dict(version=1, scope=activation.SCOPE, kind="controller",
                       admission=run.admission_pin, authority=run.authority_pin, attempt=run.attempt_pin,
                       began_ns=run.began_ns, until_ns=run.until_ns,
                       running=run.running_pin, parent=run.worker_identity)
        controller_request = run.save(activation._request_path("controller"), request)
        run.save(activation._started_path("controller"),
                 dict(request=controller_request, worker=run.caller))
        runtime_path = activation.CONTROL / "runtime-result-v1.json"
        parent = run.operation_worker
        runtime_request = run.save(activation._request_path("runtime"),
                                   dict(request, kind="runtime", running=None, parent=parent))
        run.save(activation._started_path("runtime"), dict(request=runtime_request, worker=run.worker_identity))
        runtime_terminal = run.save(activation._terminal_path("runtime"), terminal())
        runtime = dict(result, request=runtime_request, worker=run.worker_identity, handoff=run.handoff_pin)

        def replay(value, expected_parent=parent):
            runtime_pin = run.save(runtime_path, value)
            result_pin = run.save(activation.CONTROL / "activation-result-v1.json", dict(
                version=1, scope=activation.SCOPE, admission=run.admission_pin, authority=run.authority_pin,
                attempt=run.attempt_pin, supervisor=runtime_terminal, runtime=runtime_pin,
                passed=True, reason=None, feature_acceptance=False,
            ))
            return activation.verify_result(result_pin, run.admission_pin, run.authority_pin, run.attempt_pin,
                                            began_ns=run.began_ns, expected_parent=expected_parent)

        # Outer replay can occur after the inner live activation window closes.
        run.now_ns = run.until_ns + NANOSECOND
        with run.ports(), patch.object(activation.contract, "revalidate_inputs"):
            self.assertEqual(replay(runtime), run.closure)
            with self.assertRaises(REFUSED):
                replay(runtime, expected_parent=run.operation_parent)
            owner_terminal = run.read(runtime["owner_terminal"]["path"])[1]
            changed_terminal = run.save(runtime["owner_terminal"]["path"],
                                        dict(owner_terminal, observer_closed=1))
            with self.assertRaises(REFUSED):
                replay(dict(runtime, owner_terminal=changed_terminal))
            run.save(runtime["owner_terminal"]["path"], owner_terminal)
            altered = run.save(activation._request_path("controller"), dict(request, until_ns=run.until_ns - 1))
            run.save(activation._started_path("controller"), dict(request=altered, worker=run.caller))
            with self.assertRaises(REFUSED):
                replay(runtime)

    def test_execute_refuses_impossible_remaining_operation_budget_before_job(self):
        run = SyntheticRun()
        run.records.pop(handoff.HANDOFF)
        run.now_ns = run.began_ns + (handoff.SECONDS - activation.controller.SECONDS) * NANOSECOND
        with run.ports(), patch.object(Path, "cwd", return_value=handoff.ROOT), \
             patch.dict(activation.os.environ, {key: "D:/Dev/_Temp" for key in ("TEMP", "TMP", "TMPDIR")}), \
             patch.object(activation, "_live_outer_worker"), \
             patch.object(activation, "_inputs", return_value=run.admission), \
             patch.object(Path, "mkdir") as mkdir, self.assertRaisesRegex(activation.env.EnvironmentRefused, "^deadline$"):
            activation.execute(run.admission_pin, run.authority_pin, run.attempt_pin,
                               began_ns=run.began_ns)

        mkdir.assert_not_called()
        run.supervise.assert_not_called()

    def test_missing_prepared_inputs_refuse_before_creation_or_dispatch(self):
        run = SyntheticRun()
        with patch.object(Path, "cwd", return_value=handoff.ROOT), \
             patch.dict(activation.os.environ, {key: "D:/Dev/_Temp" for key in ("TEMP", "TMP", "TMPDIR")}), \
             patch.object(activation, "_live_outer_worker"), \
             patch.object(activation, "_inputs", side_effect=activation.env.EnvironmentRefused("binding")) as inputs, \
             patch.object(activation, "_supervise") as dispatch, patch.object(Path, "mkdir") as mkdir, \
             patch.object(activation.time, "monotonic_ns", return_value=run.now_ns):
            try:
                result = activation.execute(run.admission_pin, run.authority_pin, run.attempt_pin,
                                            began_ns=run.began_ns)
            except REFUSED:
                pass
            else:
                self.assertIs(result["passed"], False)

        inputs.assert_called_once_with(run.admission_pin, run.authority_pin, run.attempt_pin)
        mkdir.assert_not_called()
        dispatch.assert_not_called()

    def test_outer_worker_claim_must_match_request_and_independent_start(self):
        run = SyntheticRun()
        with run.ports():
            self.assertEqual(activation._outer_worker(run.authority_pin, run.attempt_pin, run.began_ns),
                             (run.operation_worker, run.operation_parent))
            run.save(activation.OPERATION_CLAIM, dict(run.operation_claim, worker=run.operation_parent))
            with self.assertRaises(REFUSED):
                activation._outer_worker(run.authority_pin, run.attempt_pin, run.began_ns)
            run.save(activation.OPERATION_CLAIM, run.operation_claim)
            with self.assertRaises(REFUSED):
                activation._outer_worker(run.authority_pin, run.attempt_pin, run.began_ns + 1)

    def test_activation_requires_the_claimed_process_inside_outer_job(self):
        run = SyntheticRun()
        job_pids = Mock(return_value=[run.operation_worker["pid"]])
        with run.ports(), patch.object(activation.os, "getpid", return_value=run.operation_worker["pid"]), \
             patch.object(activation.os, "getppid", return_value=run.operation_parent["pid"]), \
             patch.object(activation, "_identity", side_effect=lambda pid, expected: expected) as identity, \
             patch.object(activation.mechanisms, "_ProcessApi",
                          return_value=SimpleNamespace(current_job_pids=job_pids)):
            activation._live_outer_worker(run.authority_pin, run.attempt_pin, run.began_ns)
            self.assertEqual(identity.call_args_list, [
                call(run.operation_parent["pid"], run.operation_parent),
                call(run.operation_worker["pid"], run.operation_worker),
            ])
            job_pids.return_value = [run.operation_parent["pid"]]
            with self.assertRaisesRegex(activation.env.EnvironmentRefused, "^job$"):
                activation._live_outer_worker(run.authority_pin, run.attempt_pin, run.began_ns)

    def test_runtime_child_refuses_before_handoff_if_outer_claim_has_foreign_worker(self):
        run = SyntheticRun()
        run.records.pop(handoff.HANDOFF)
        request = dict(admission=run.admission_pin, authority=run.authority_pin, attempt=run.attempt_pin,
                       running=None, began_ns=run.began_ns, until_ns=run.until_ns, parent=run.owner_identity)
        request_pin = run.save(activation._request_path("runtime"), request)
        with run.ports(), patch.object(activation, "_enter", return_value=(request_pin, request, run.worker_identity)), \
             patch.object(activation, "_inputs") as inputs:
            self.assertEqual(activation.main(["_runtime"]), 1)
        inputs.assert_not_called()
        self.assertNotIn(handoff.HANDOFF, run.records)


if __name__ == "__main__":
    unittest.main()
