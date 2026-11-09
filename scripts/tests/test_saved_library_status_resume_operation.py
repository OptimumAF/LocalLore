"""Host-only SDK23 resume supervision with inert process and record bindings.

Copyright 2026 LocalLore contributors. SPDX-License-Identifier: Apache-2.0
"""

from contextlib import ExitStack, contextmanager
import copy
from io import BytesIO
from pathlib import Path
from types import SimpleNamespace
import unittest
from unittest.mock import Mock, call, patch

from benchmarks import saved_library_status_handoff as original
from benchmarks import saved_library_status_operation as fresh_operation
from benchmarks import saved_library_status_resume_handoff as resume
from benchmarks import saved_library_status_resume_operation as operation
from scripts.tests.test_saved_library_status_handoff import NOW, REFUSED
from scripts.tests.test_saved_library_status_resume_handoff import ResumeRecords


NS = original.NS


class ResumeOperationRecords(ResumeRecords):
    """Keep the real one-use claim and admission checks behind inert I/O."""

    def __init__(self):
        super().__init__()
        self.began_ns = NOW - 10 * NS
        self.now_ns = NOW
        self.parent = dict(pid=3200, creation_filetime=700,
                           executable=self.plan["python"]["executable"]["path"])
        self.worker = dict(self.parent, pid=3201, creation_filetime=750)
        self.preflight_value = dict(resources={"synthetic": "host capacity"},
                                    ledger=self.ledger_pin, ports_free=True)
        self.preflight = Mock(return_value=self.preflight_value)
        self.forbidden_prepare = Mock(side_effect=AssertionError("resume may not prepare"))
        self.activate = Mock(side_effect=self.complete_activation)
        self.verify_activation = Mock(side_effect=self.replay_activation)
        self.watchdog = Mock(side_effect=AssertionError("unexpected watchdog"))
        self.closure = None

    def mkdir(self, path, *args, **kwargs):
        path = Path(path)
        if path == operation.CAPTURE and resume.ATTEMPT_ROOT in self.present and path not in self.present:
            self.present.add(path)
            self.directories.append(path)
            return
        return super().mkdir(path, *args, **kwargs)

    def rename(self, source, target):
        if target in self.records:
            raise FileExistsError(target)
        _, value = self.records.pop(source)
        self.present.discard(source)
        self.create(target, value)
        return target

    def capture_stream(self, path, mode):
        if path.parent != operation.CAPTURE or path.name not in original.env.LiveOutput.names or mode != "rb":
            raise AssertionError("unexpected capture access")
        return BytesIO()

    def complete_activation(self, admission, authority, attempt, *, began_ns, resume):
        original.env.require(resume is True and began_ns == self.began_ns, "activation")
        self.closure = dict(
            owner=self.add("owner", operation.ACTIVATED.parent / "synthetic-owner-v1.json", {}),
            closure=self.add("closure", original.GUEST / "guest-storage-closure-v1.json", {}),
            ledger=self.add("closed_ledger", original.LEDGER, {"synthetic": "closed"}),
        )
        result = dict(admission=admission, authority=authority, attempt=attempt,
                      passed=True, reason=None, feature_acceptance=False)
        self.add("activated", operation.ACTIVATED, result)
        return result

    def replay_activation(self, binding, admission, authority, attempt, *, began_ns, expected_parent, resume):
        pin, result = self.read(operation.ACTIVATED)
        original.env.require(
            resume is True and binding == pin and result["admission"] == admission
            and result["authority"] == authority and result["attempt"] == attempt and result["passed"] is True
            and began_ns == self.began_ns and expected_parent == self.worker, "activation",
        )
        return copy.deepcopy(self.closure)

    def enter_records(self, attempt_pin):
        request = dict(version=1, scope=resume.OPERATION_SCOPE, authority=self.resume_authority,
                       attempt=attempt_pin, parent=self.parent, began_ns=self.began_ns)
        request_pin = self.add("request", operation.REQUEST, request)
        self.add("started", operation.STARTED, dict(request=request_pin, worker=self.worker))
        self.present.update((operation.REQUEST, operation.STARTED))
        return request_pin

    @contextmanager
    def worker_ports(self, barrier, *, in_job=True):
        pids = [self.worker["pid"]] if in_job else [self.parent["pid"]]
        with (patch.object(operation.sys, "stdin", SimpleNamespace(buffer=BytesIO(barrier))),
              patch.object(operation.os, "getpid", return_value=self.worker["pid"]),
              patch.object(operation.os, "getppid", return_value=self.parent["pid"]),
              patch.object(operation.mechanisms, "_ProcessApi",
                           return_value=SimpleNamespace(current_job_pids=lambda: pids))):
            yield

    def run_watchdog(self, command, request, capture, seconds, started):
        original.env.require(started(SimpleNamespace(pid=self.worker["pid"])) is True, "identity")
        with self.worker_ports(request):
            code = operation.main(["_worker"])
        result = dict(status="child_exited", cleanup_complete=True, output_capture_complete=True,
                      worker_returncode=code, elapsed_ms=8, stdout_bytes=0, stderr_bytes=0)
        return dict(result, **self.watchdog_changes)

    @contextmanager
    def ports(self):
        with super().ports(), ExitStack() as stack:
            for module, name, replacement in (
                (operation, "preflight", self.preflight),
                (operation.env, "prepare", self.forbidden_prepare),
                (operation.env, "supervise_operation", self.watchdog),
                (operation.activation, "execute", self.activate),
                (operation.activation, "verify_result", self.verify_activation),
                (operation.time, "monotonic_ns", lambda: self.now_ns),
                (operation.os.path, "lexists", lambda path: Path(path) in self.present or Path(path) in self.records),
                (Path, "rename", lambda source, target: self.rename(source, target)),
                (Path, "open", lambda path, mode: self.capture_stream(path, mode)),
                (Path, "cwd", lambda: original.ROOT),
                (operation, "_identity", lambda pid, expected=None:
                    self.worker if pid == self.worker["pid"] else self.parent),
                (operation.sys, "executable", self.parent["executable"]),
            ):
                stack.enter_context(patch.object(module, name, replacement))
            stack.enter_context(patch.dict(operation.os.environ, {
                "TEMP": "D:/Dev/_Temp", "TMP": "D:/Dev/_Temp", "TMPDIR": "D:/Dev/_Temp",
            }, clear=True))
            yield

    def stages(self, attempt_pin):
        with self.ports():
            return operation._run_stages(self.resume_authority, attempt_pin, self.began_ns, self.worker)

    def execute(self, **watchdog_changes):
        self.watchdog_changes = watchdog_changes
        self.watchdog.side_effect = self.run_watchdog
        with self.ports():
            return operation.execute(self.resume_authority, began_ns=self.began_ns)


class SavedLibraryStatusResumeOperationTests(unittest.TestCase):
    def test_absent_or_spent_authority_refuses_before_creating_attempt(self):
        for absent in (False, True):
            with self.subTest(absent=absent):
                graph = ResumeOperationRecords()
                if absent:
                    graph.records.pop(resume.AUTHORITY)
                pin = graph.resume_authority if absent else graph.original_authority
                with graph.ports(), self.assertRaises(REFUSED):
                    operation.execute(pin, began_ns=graph.began_ns)
                self.assertEqual(graph.directories, [])
                graph.watchdog.assert_not_called()

    def test_existing_claim_and_elapsed_window_refuse_without_dispatch(self):
        graph = ResumeOperationRecords()
        attempt = graph.begin()
        with graph.ports(), self.assertRaises((OSError, *REFUSED)):
            operation.execute(graph.resume_authority, began_ns=graph.began_ns)
        self.assertEqual(graph.read(resume.ATTEMPT)[0], attempt)
        graph.watchdog.assert_not_called()

        graph = ResumeOperationRecords()
        graph.now_ns = graph.began_ns + original.SECONDS * NS
        with graph.ports(), self.assertRaises(REFUSED):
            operation.execute(graph.resume_authority, began_ns=graph.began_ns)
        self.assertEqual(graph.directories, [])
        graph.watchdog.assert_not_called()

    def test_one_use_outer_supervisor_joins_the_exact_resume_controller_and_closure(self):
        graph = ResumeOperationRecords()
        historical = graph.read(original.ATTEMPT)
        result = graph.execute()
        self.assertIs(result["passed"], True)
        self.assertIs(result["feature_acceptance"], False)
        self.assertEqual(graph.read(operation.RESULT)[1], result)
        _, stage = graph.read(operation.STAGE)
        self.assertEqual(stage["phase"], "completed")
        self.assertEqual(stage["closure"], graph.closure)
        self.assertEqual(graph.read(original.ATTEMPT), historical)
        self.assertEqual(graph.read(resume.RUN)[0]["sha256"], graph.original_run["sha256"])
        graph.forbidden_prepare.assert_not_called()
        graph.watchdog.assert_called_once()
        command, barrier, capture, seconds, _ = graph.watchdog.call_args.args
        self.assertEqual(command[-1], "_worker")
        request_pin, request = graph.read(operation.REQUEST)
        self.assertEqual(barrier, operation.BARRIER + original.env.encoded(request_pin))
        self.assertEqual(capture, operation.CAPTURE)
        self.assertEqual(seconds, original.SECONDS - original.TAIL_SECONDS - 10)
        self.assertEqual(request["scope"], resume.OPERATION_SCOPE)
        self.assertEqual(graph.read(operation.WORKER_CLAIM)[1], dict(request=request_pin, worker=graph.worker))
        graph.activate.assert_called_once_with(
            stage["admission"], graph.resume_authority, result["attempt"], began_ns=graph.began_ns, resume=True,
        )
        self.assertEqual(graph.verify_activation.call_count, 2)
        self.assertTrue(all(call.kwargs["resume"] is True for call in graph.verify_activation.call_args_list))

    def test_terminal_rejects_bad_exit_or_cleanup_without_qualifying_successful_worker(self):
        for changes in ({"worker_returncode": True}, {"worker_returncode": 1},
                        {"cleanup_complete": False}, {"output_capture_complete": False}):
            with self.subTest(changes=changes):
                graph = ResumeOperationRecords()
                result = graph.execute(**changes)
                self.assertIs(result["passed"], False)
                self.assertEqual(result["supervisor"], graph.read(operation.TERMINAL)[0])
                self.assertEqual(result["stages"], graph.read(operation.STAGE)[0])
                graph.verify_activation.assert_called_once()

    def test_preflight_uses_the_historical_root_and_requires_private_socket_cleanup(self):
        graph = ResumeOperationRecords()
        proposal = graph.run_proposal
        root = resume.review.EXECUTED_ROOT
        for closed_mask in (1, True, 0):
            with self.subTest(closed_mask=closed_mask):
                io = Mock()
                io.prepared.return_value = proposal
                io.facts.return_value = graph.preflight_value["resources"]
                io.exclusive.return_value = dict(
                    exclusive_bind_succeeded=True, created_mask=1, close_attempted_mask=1,
                    closed_mask=closed_mask,
                )
                api = object()
                with ExitStack() as stack:
                    for module, name, replacement in (
                        (resume, "_prepared", io.prepared),
                        (operation.env, "validate_proposal", io.validate),
                        (operation.env, "verify_installation", io.installation),
                        (operation.env, "check_external_state", io.external),
                        (operation.env, "resource_facts", io.facts),
                        (operation.env, "ports_free", io.ports),
                        (operation.process, "_exclusive_preflight", io.exclusive),
                        (operation.mechanisms, "_ProcessApi", Mock(return_value=api)),
                    ):
                        stack.enter_context(patch.object(module, name, replacement))
                    if type(closed_mask) is int and closed_mask == 1:
                        self.assertEqual(operation.preflight(graph.plan), graph.preflight_value)
                    else:
                        with self.assertRaisesRegex(original.env.EnvironmentRefused, "^ports_unavailable$"):
                            operation.preflight(graph.plan)
                expected = [
                    call.prepared(graph.plan), call.validate(proposal, "run", preparation_root=root),
                    call.installation(proposal, preparation_root=root), call.external(proposal),
                    call.facts(proposal), call.ports(), call.exclusive(api, port=operation.contract.PORT),
                ]
                if type(closed_mask) is int and closed_mask == 1:
                    expected.append(call.prepared(graph.plan))
                self.assertEqual(io.mock_calls, expected)

    def test_wrong_or_invalid_cli_digest_never_dispatches_the_operation(self):
        graph = ResumeOperationRecords()
        with graph.ports(), patch.object(operation, "execute") as execute:
            for digest in ("0" * 64, "A" * 64, graph.original_authority["sha256"]):
                with self.subTest(digest=digest):
                    self.assertEqual(operation.main(["--authority-sha256", digest]), 1)
            execute.assert_not_called()
        self.assertEqual(graph.directories, [])

    def test_failed_readiness_preserves_refusal_before_admission_or_activation(self):
        graph = ResumeOperationRecords()
        attempt = graph.begin()
        graph.preflight.side_effect = original.env.EnvironmentRefused("ports_unavailable")
        stage = graph.stages(attempt)
        self.assertIs(stage["passed"], False)
        self.assertEqual(stage["phase"], "preflight")
        self.assertIsNotNone(stage["reason"])
        self.assertEqual(graph.read(operation.STAGE)[1], stage)
        self.assertNotIn(resume.ADMISSION, graph.records)
        graph.activate.assert_not_called()
        graph.forbidden_prepare.assert_not_called()

    def test_preflight_does_not_reset_deadline_or_allow_a_changed_plan(self):
        for drift in ("deadline", "plan"):
            with self.subTest(drift=drift):
                graph = ResumeOperationRecords()
                attempt = graph.begin()

                def change(_plan):
                    if drift == "deadline":
                        graph.now_ns = graph.began_ns + (original.SECONDS - 1) * NS
                    else:
                        graph.add("changed_plan", resume.PLAN, dict(graph.plan, scope="foreign"))
                    return graph.preflight_value

                graph.preflight.side_effect = change
                stage = graph.stages(attempt)
                self.assertIs(stage["passed"], False)
                self.assertNotIn(resume.ADMISSION, graph.records)
                graph.activate.assert_not_called()

    def test_ledger_change_during_preflight_cannot_bind_the_guest(self):
        graph = ResumeOperationRecords()
        attempt = graph.begin()

        def change(_plan):
            graph.add("changed_ledger", original.LEDGER, {"synthetic": "changed"})
            return graph.preflight_value

        graph.preflight.side_effect = change
        stage = graph.stages(attempt)
        self.assertIs(stage["passed"], False)
        self.assertNotIn(resume.ADMISSION, graph.records)
        graph.activate.assert_not_called()

    def test_failed_activation_retains_the_partial_records_without_retry(self):
        graph = ResumeOperationRecords()
        attempt = graph.begin()

        def refuse(admission, authority, attempt, **kwargs):
            result = dict(admission=admission, authority=authority, attempt=attempt,
                          passed=False, reason="owner_terminal", feature_acceptance=False)
            graph.add("activation_refused", operation.ACTIVATED, result)
            return result

        graph.activate.side_effect = refuse
        stage = graph.stages(attempt)
        self.assertIs(stage["passed"], False)
        self.assertEqual(stage["activation"], graph.read(operation.ACTIVATED)[0])
        self.assertIn(resume.ADMISSION, graph.records)
        graph.activate.assert_called_once()
        graph.verify_activation.assert_not_called()

    def test_stage_replay_rejects_resealed_preflight_and_foreign_worker(self):
        for defect in ("ledger", "ports", "identity"):
            with self.subTest(defect=defect):
                graph = ResumeOperationRecords()
                attempt = graph.begin()
                stage = graph.stages(attempt)
                _, preflight = graph.read(operation.PREFLIGHT)
                if defect == "identity":
                    stage["worker"] = graph.parent
                else:
                    preflight["ledger" if defect == "ledger" else "ports_free"] = (
                        dict(graph.ledger_pin, sha256="0" * 64) if defect == "ledger" else False
                    )
                    stage["preflight"] = graph.add("drift", operation.PREFLIGHT, preflight)
                resealed = graph.add("stage_drift", operation.STAGE, stage)
                with graph.ports(), self.assertRaises(REFUSED):
                    operation._verify_stage(resealed, graph.resume_authority, attempt, graph.began_ns, graph.worker)
                graph.verify_activation.assert_called_once()

    def test_worker_rejects_foreign_barrier_and_unowned_job(self):
        for wrong_barrier in (True, False):
            with self.subTest(wrong_barrier=wrong_barrier):
                graph = ResumeOperationRecords()
                attempt = graph.begin()
                request_pin = graph.enter_records(attempt)
                barrier = fresh_operation.BARRIER if wrong_barrier else operation.BARRIER
                with graph.ports(), graph.worker_ports(barrier + original.env.encoded(request_pin), in_job=False):
                    self.assertEqual(operation.main(["_worker"]), 1)
                self.assertNotIn(operation.WORKER_CLAIM, graph.records)
                graph.preflight.assert_not_called()
                graph.activate.assert_not_called()
