"""Synthetic supervision evidence for the saved-library resume profile.

Copyright 2026 LocalLore contributors. SPDX-License-Identifier: Apache-2.0
"""

from contextlib import ExitStack, contextmanager
from io import BytesIO
from pathlib import Path
from types import SimpleNamespace
import unittest
from unittest.mock import Mock, patch

from benchmarks import owned_saved_library_status as owner
from benchmarks import receipt_avd_storage as storage
from benchmarks import saved_library_status_activation as activation
from benchmarks import saved_library_status_closure as closure
from benchmarks import saved_library_status_handoff as original
from benchmarks import saved_library_status_resume_handoff as resume_handoff
from scripts.tests.test_saved_library_status_activation import NANOSECOND, SyntheticRun, terminal
from scripts.tests.test_saved_library_status_closure import ClosedRun

CONTROL = resume_handoff.ATTEMPT_ROOT / "activation-v1"
SCOPE = "saved-library-status-resume-activation-v1"
REFUSED = (ValueError, RuntimeError)


@contextmanager
def resume_fixture_paths():
    """Build records at resume paths, then restore production defaults before replay."""
    with ExitStack() as stack:
        for name in ("OWNED_ROOT", "ADMISSION", "AUTHORITY", "ATTEMPT", "OPERATION_SCOPE",
                     "HANDOFF", "HANDOFF_SCOPE"):
            stack.enter_context(patch.object(original, name, getattr(resume_handoff, name)))
        for name, value in (
            ("CONTROL", CONTROL),
            ("OPERATION_REQUEST", resume_handoff.ATTEMPT_ROOT / "operation-request-v1.json"),
            ("OPERATION_STARTED", resume_handoff.ATTEMPT_ROOT / "operation-started-v1.json"),
            ("OPERATION_CLAIM", resume_handoff.ATTEMPT_ROOT / "operation-worker-claim-v1.json"),
        ):
            stack.enter_context(patch.object(activation, name, value))
        yield


class ResumeRun(SyntheticRun):
    def __init__(self, **kwargs):
        with resume_fixture_paths():
            super().__init__(**kwargs)
        self.check_closure.side_effect = lambda *args, **kw: self.event("closure_replay", self.closure)
        self.stop.side_effect = lambda *args, **kw: self.stop_owner(*args)

    @contextmanager
    def ports(self):
        with super().ports(), patch.object(resume_handoff, "approved_plan", Mock()), patch.object(
            resume_handoff, "verify_admission", return_value=self.admission
        ):
            yield

    def run(self):
        with self.ports():
            return activation._run_owned(self.admission_pin, self.admission, self.until_ns,
                                         began_ns=self.began_ns, handoff_pin=self.handoff_pin, resume=True)

    def request(self, kind, *, parent=None, running=None):
        return dict(version=1, scope=SCOPE, kind=kind, admission=self.admission_pin,
                    authority=self.authority_pin, attempt=self.attempt_pin, began_ns=self.began_ns,
                    until_ns=self.until_ns, parent=parent or self.operation_worker, running=running)


class SavedLibraryStatusResumeActivationTests(unittest.TestCase):
    def test_owner_receives_only_the_resume_proof_and_runs_existing_controller(self):
        graph = ResumeRun()
        with patch.dict(activation.os.environ, {original.HANDOFF_ENV: "old", owner.RESUME_HANDOFF_ENV: "stale"}):
            result = graph.run()
        self.assertIs(result["passed"], True)
        self.assertEqual(result["closure"], graph.closure)
        argv = graph.launch.call_args.args[0]
        self.assertEqual(Path(argv[-5]).name, owner.OWNER_SCRIPT)
        self.assertEqual(argv[-4:], ["--admission", graph.admission_pin["path"],
                                     "--admission-sha256", graph.admission_pin["sha256"]])
        child_env = graph.launch.call_args.kwargs["env"]
        self.assertEqual(child_env[owner.RESUME_HANDOFF_ENV], graph.handoff_pin["sha256"])
        self.assertNotIn(original.HANDOFF_ENV, child_env)
        graph.supervise.assert_called_once_with(
            "controller", graph.admission_pin, graph.authority_pin, graph.attempt_pin,
            graph.began_ns, graph.until_ns, running_pin=graph.running_pin, resume=True,
        )
        graph.check_controller.assert_called_once_with(graph.controller_pin, graph.admission_pin,
                                                        graph.running_pin, graph.caller)
        graph.check_closure.assert_called_once_with(graph.admission_pin, graph.admission,
                                                    graph.running_pin, graph.owner_identity, resume=True)
        self.assertEqual(graph.events, ["controller", "stop", "observer_close", "capture_close",
                                        "closure_replay", "controller_replay"])
        self.assertNotIn(activation.CONTROL / "owner-terminal-v1.json", graph.records)

    def test_unknown_controller_job_cannot_publish_stop_or_qualify_cleanup(self):
        graph = ResumeRun(known=False)
        result = graph.run()
        self.assertIs(result["passed"], False)
        self.assertIsNone(result["closure"])
        graph.stop.assert_not_called()
        graph.check_closure.assert_not_called()
        graph.check_controller.assert_not_called()

    def test_resume_worker_jobs_have_distinct_arguments_barrier_and_records(self):
        supervise = activation._supervise
        for kind in ("runtime", "controller"):
            graph = ResumeRun()
            worker = dict(graph.worker_identity, pid=graph.operation_worker["pid"] + 100)
            start_path = CONTROL / f"{kind}-started-v1.json"

            def rename(source, destination):
                value = graph.read(source)[1]
                self.assertEqual(destination, start_path)
                graph.save(destination, value)

            def dispatch(argv, raw, directory, seconds, started):
                self.assertEqual(argv[-1], "_resume_" + kind)
                self.assertTrue(raw.startswith(activation.RESUME_BARRIER))
                self.assertFalse(raw.startswith(activation.BARRIER))
                self.assertEqual(directory, capture)
                self.assertGreater(seconds, 0)
                request_pin = activation.env.decode_json(raw[len(activation.RESUME_BARRIER):])
                self.assertEqual(graph.bound(request_pin, CONTROL / f"{kind}-request-v1.json"),
                                 graph.request(kind, running=running_pin))
                self.assertIs(started(SimpleNamespace(pid=worker["pid"])), True)
                return terminal()

            running_pin = graph.running_pin if kind == "controller" else None
            capture = Mock()
            with (self.subTest(kind=kind), graph.ports(),
                  patch.object(activation.env, "safe_path", return_value=capture) as safe_path,
                  patch.object(activation.env, "supervise", side_effect=dispatch) as launch,
                  patch.object(activation, "_identity",
                               side_effect=lambda pid: worker if pid == worker["pid"] else graph.operation_worker),
                  patch.object(Path, "rename", rename)):
                job = supervise(kind, graph.admission_pin, graph.authority_pin, graph.attempt_pin,
                                graph.began_ns, graph.until_ns, running_pin=running_pin, resume=True)
            self.assertIs(job["known"], True)
            self.assertEqual(job["worker"], worker)
            safe_path.assert_called_once_with(CONTROL / f"{kind}-capture-v1", exists=False)
            capture.mkdir.assert_called_once_with(exist_ok=False)
            launch.assert_called_once()

    def test_resume_worker_refuses_fresh_barrier_before_reading_request(self):
        stdin = SimpleNamespace(buffer=BytesIO(activation.BARRIER + b"{}"))
        with (patch.object(activation.sys, "stdin", stdin), patch.object(original, "at") as read,
              self.assertRaisesRegex(activation.env.EnvironmentRefused, "^barrier$")):
            activation._enter("runtime", resume=True)
        read.assert_not_called()

    def test_resume_runtime_worker_publishes_exact_handoff_before_owner_dispatch(self):
        graph = ResumeRun()
        del graph.records[resume_handoff.HANDOFF]
        request = graph.request("runtime")
        request_pin = graph.save(CONTROL / "runtime-request-v1.json", request)

        def dispatch(admission_pin, admission, until_ns, *, began_ns, handoff_pin, resume):
            self.assertIs(resume, True)
            self.assertEqual((admission_pin, admission, began_ns, until_ns),
                             (graph.admission_pin, graph.admission, graph.began_ns, graph.until_ns))
            pin, published = graph.read(resume_handoff.HANDOFF)
            self.assertEqual(pin, handoff_pin)
            self.assertEqual(published, dict(
                version=1, scope=resume_handoff.HANDOFF_SCOPE, authority=graph.authority_pin,
                attempt=graph.attempt_pin, admission=graph.admission_pin, supervisor=graph.worker_identity,
                began_ns=graph.began_ns, until_ns=graph.until_ns,
            ))
            return dict(passed=False, reason="synthetic-refusal")

        with (graph.ports(), patch.object(activation, "_enter",
                  return_value=(request_pin, request, graph.worker_identity)) as enter,
              patch.object(activation, "_run_owned", side_effect=dispatch) as run):
            self.assertEqual(activation.main(["_resume_runtime"]), 1)
        enter.assert_called_once_with("runtime", resume=True)
        run.assert_called_once()
        self.assertEqual(graph.read(CONTROL / "runtime-result-v1.json")[1]["reason"], "synthetic-refusal")
        self.assertNotIn(original.HANDOFF, graph.records)

    def test_resume_controller_requires_matching_live_parent_and_current_approval(self):
        graph = ResumeRun()
        request = graph.request("controller", parent=graph.worker_identity, running=graph.running_pin)
        request_pin = graph.save(CONTROL / "controller-request-v1.json", request)
        for changes, drift, code in (({}, False, 0), (dict(parent=graph.owner_identity), False, 1), ({}, True, 1)):
            approval_failure = activation.env.EnvironmentRefused("authority") if drift else None
            with (self.subTest(changes=changes, drift=drift), graph.ports(),
                  patch.object(resume_handoff, "approved_plan", side_effect=approval_failure),
                  patch.object(activation, "_enter",
                               return_value=(request_pin, dict(request, **changes), graph.caller)) as enter,
                  patch.object(activation.controller, "run", return_value={"outcome": "completed"}) as run):
                self.assertEqual(activation.main(["_resume_controller"]), code)
                enter.assert_called_once_with("controller", resume=True)
            if code == 0:
                run.assert_called_once_with(graph.admission_pin, graph.running_pin)
            else:
                run.assert_not_called()

    def test_resume_execute_and_completed_replay_join_the_same_controller_and_closure(self):
        graph = ResumeRun()
        graph.until_ns = min(graph.began_ns + original.SECONDS * NANOSECOND,
                             graph.now_ns + original.ACTIVATION_SECONDS * NANOSECOND) - original.TAIL_SECONDS * NANOSECOND
        _, handoff = graph.read(resume_handoff.HANDOFF)
        graph.handoff_pin = graph.save(resume_handoff.HANDOFF, dict(handoff, until_ns=graph.until_ns))
        result = graph.run()
        self.assertIs(result["passed"], True)
        del graph.records[resume_handoff.HANDOFF]
        controller_request = graph.save(
            CONTROL / "controller-request-v1.json",
            graph.request("controller", parent=graph.worker_identity, running=graph.running_pin),
        )
        graph.save(CONTROL / "controller-started-v1.json", dict(request=controller_request, worker=graph.caller))
        runtime_request = graph.save(CONTROL / "runtime-request-v1.json", graph.request("runtime"))
        graph.save(CONTROL / "runtime-started-v1.json", dict(request=runtime_request, worker=graph.worker_identity))
        runtime_terminal = graph.save(CONTROL / "runtime-supervisor-v1.json", terminal())
        job = dict(terminal=terminal(), pin=runtime_terminal, worker=graph.worker_identity,
                   request=runtime_request, known=True)

        def dispatch(kind, admission_pin, authority_pin, attempt_pin, began_ns, until_ns, *, resume):
            self.assertIs(resume, True)
            self.assertEqual((kind, admission_pin, authority_pin, attempt_pin, began_ns, until_ns),
                             ("runtime", graph.admission_pin, graph.authority_pin, graph.attempt_pin,
                              graph.began_ns, graph.until_ns))
            pin = graph.save(resume_handoff.HANDOFF, dict(handoff, until_ns=graph.until_ns))
            graph.save(CONTROL / "runtime-result-v1.json",
                       dict(result, request=runtime_request, worker=graph.worker_identity, handoff=pin))
            return job

        with (graph.ports(), patch.object(activation.contract, "revalidate_inputs"),
              patch.object(activation, "_live_outer_worker"),
              patch.object(activation, "_supervise", side_effect=dispatch) as launch,
              patch.object(Path, "cwd", return_value=original.ROOT),
              patch.object(activation.env, "safe_path", return_value=Mock()),
              patch.dict(activation.os.environ, {key: "D:/Dev/_Temp" for key in ("TEMP", "TMP", "TMPDIR")},
                         clear=True)):
            completed = activation.execute(graph.admission_pin, graph.authority_pin, graph.attempt_pin,
                                           began_ns=graph.began_ns, resume=True)
            self.assertIs(completed["passed"], True)
            self.assertEqual(completed["scope"], SCOPE)
            final_pin = graph.read(CONTROL / "activation-result-v1.json")[0]
            graph.now_ns = graph.until_ns + NANOSECOND
            replay = (final_pin, graph.admission_pin, graph.authority_pin, graph.attempt_pin)
            self.assertEqual(activation.verify_result(*replay, began_ns=graph.began_ns,
                                                      expected_parent=graph.operation_worker, resume=True),
                             graph.closure)
            with self.assertRaises(REFUSED):
                activation.verify_result(*replay, began_ns=graph.began_ns, expected_parent=graph.operation_worker)
        launch.assert_called_once()
        self.assertNotIn(activation.CONTROL / "activation-result-v1.json", graph.records)


class SavedLibraryStatusResumeClosureTests(unittest.TestCase):
    def test_closure_uses_resume_replay_and_rejects_unclean_evidence(self):
        for adversary in (None, ("worker", lambda row: row["cleanup"].update(guest_wait_completed=1)),
                          ("entry", lambda row: row.update(state="retained"))):
            with resume_fixture_paths():
                graph = ClosedRun(adversary)
            with (self.subTest(adversary=adversary),
                  patch.object(original, "read", graph.read), patch.object(original, "at", graph.at),
                  patch.object(original, "ledger_entry", graph.read_ledger),
                  patch.object(closure.env, "check_binding", graph.checked),
                  patch.object(closure.env, "safe_path", graph.capture_path),
                  patch.object(closure.env, "create_json", side_effect=AssertionError("evidence write")),
                  patch.object(storage, "record_closed", side_effect=AssertionError("ledger write")),
                  patch.object(owner.REPLAY, "verify_owned_target_result") as fresh,
                  patch.object(owner.RESUME_REPLAY, "verify_owned_target_result", graph.replay)):
                args = (graph.admission_pin, graph.admission, graph.running_pin, graph.owner_identity)
                if adversary is None:
                    self.assertEqual(closure.verify_closure(*args, resume=True),
                                     dict(owner=graph.public, closure=graph.closed, ledger=graph.ledger))
                    with self.assertRaises(REFUSED):
                        closure.verify_closure(*args)
                else:
                    with self.assertRaises(REFUSED):
                        closure.verify_closure(*args, resume=True)
                fresh.assert_not_called()
                graph.replay.assert_called_once_with(graph.worker, graph.admission, graph.admission_pin,
                                                     graph.request, graph.worker_identity)
