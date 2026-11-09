"""Host-only checks for the bounded SDK25 supervisor and its stop fence."""
import copy
import io
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import Mock, patch

from benchmarks import archive_roundtrip_supervisor as supervisor
from scripts.tests import test_archive_roundtrip_lifecycle as fixture
from scripts.tests import test_owned_target_contract as legacy

admission = supervisor.admission
handoff = supervisor.handoff
lifecycle = supervisor.lifecycle
env = supervisor.env


class SupervisorTests(unittest.TestCase):
    def setUp(self):
        self.admitted = fixture.admission()
        self.running = fixture.running(self.admitted)
        self.python = self.admitted["python"]["executable"]["path"]
        self.runtime = fixture.caller(self.running)
        self.controller = dict(self.runtime, pid=self.runtime["pid"] + 1)
        self.live = legacy.pin(str(admission.OWNED_ROOT / "running-v1.json"))
        self.authority = legacy.pin(str(admission.AUTHORITY))
        self.attempt = legacy.pin(str(admission.ATTEMPT))
        self.admit = legacy.pin(str(admission.ADMISSION))
        self.launch = legacy.pin(str(handoff.HANDOFF))
        self.result = legacy.pin(str(admission.OWNED_ROOT / supervisor.outbound.OUTPUT / lifecycle.RESULT))
        self.terminal = legacy.pin(str(supervisor._path("controller", "terminal")))
        self.window = dict(began_ns=3 * handoff.NS, until_ns=1803 * handoff.NS)
        self.request = dict(version=1, scope=supervisor.SCOPE, kind="runtime", authority=self.authority,
                            attempt=self.attempt, admission=self.admit, running=None,
                            parent=dict(self.runtime, pid=self.runtime["pid"] - 1), **self.window)
        self.controller_request = dict(self.request, kind="controller", running=self.live, parent=self.runtime)
        self.launch_record = dict(version=1, scope=handoff.SCOPE, supervisor=self.runtime,
                                  **{key: self.request[key] for key in supervisor.CONTEXT_KEYS})
        self.worker_result = dict(reason="stop_requested", stop_requested=True, running=self.live)
        self.gate = supervisor._stop_gate(self.request, self.launch, self.live, self.result, self.terminal)
        self.context = dict(admission=self.admitted, admission_pin=self.admit)
        self.binding = self.enterContext(patch.object(env, "check_binding"))

    def test_authority_spent_once_before_supervision(self):
        with (patch.object(supervisor.os, "name", "nt"),
              patch.object(supervisor.output_control, "_prepare_environment"),
              patch.object(supervisor.time, "monotonic_ns", return_value=self.window["began_ns"]),
              patch.object(handoff, "check_window") as deadline,
              patch.object(admission, "spend", return_value=self.attempt) as spend,
              patch.object(admission, "verify_spent", return_value=self.context) as verify,
              patch.object(supervisor, "_identity", return_value=self.request["parent"]),
              patch.object(supervisor, "_supervise", return_value=(self.terminal, self.runtime)) as run,
              patch.object(supervisor, "_verify_runtime", return_value=self.gate) as replay):
            self.assertEqual(supervisor.execute(self.authority), self.gate)
            spend.assert_called_once_with(self.authority)
            verify.assert_called_once_with(self.authority, self.attempt)
            deadline.assert_called_once_with(self.request, launching=True)
            run.assert_called_once_with(self.request)
            replay.assert_called_once_with(self.request, self.runtime)

    def test_refused_authority_or_wrong_python_cannot_start_child(self):
        with (patch.object(supervisor.os, "name", "nt"),
              patch.object(supervisor.output_control, "_prepare_environment"),
              patch.object(admission, "spend", side_effect=admission.AdmissionRefused("authority")) as spend,
              patch.object(admission, "verify_spent", return_value=self.context),
              patch.object(supervisor, "_identity", return_value=dict(self.runtime, executable="D:/wrong.exe")),
              patch.object(supervisor, "_supervise") as run):
            with self.assertRaisesRegex(admission.AdmissionRefused, "^authority$"):
                supervisor.execute(self.authority)
            spend.side_effect = None
            spend.return_value = self.attempt
            with self.assertRaisesRegex(admission.AdmissionRefused, "^identity$"):
                supervisor.execute(self.authority)
            run.assert_not_called()

    def test_stage_launch_uses_only_fixed_barrier_and_held_windows_job(self):
        path = Mock()
        request_pin = self.admit
        for kind, request, identity, seconds in (
            ("runtime", self.request, self.runtime, 1350),
            ("controller", self.controller_request, self.controller, 1280),
        ):
            with self.subTest(kind=kind):
                def run(command, payload, output, budget, on_started):
                    self.assertEqual(command, [self.python, "-I", "-S", "-B", str(Path(supervisor.__file__)),
                                               "_" + kind])
                    self.assertEqual(payload, supervisor.BARRIER + env.encoded(request_pin))
                    self.assertIs(output, path)
                    self.assertEqual(budget, seconds)
                    self.assertTrue(on_started(Mock(pid=identity["pid"])))
                    return {"status": "child_exited"}

                with (patch.object(supervisor.output_control, "validate_output", return_value=path),
                      patch.object(supervisor, "_remaining", return_value=1350),
                      patch.object(supervisor, "_identity", return_value=identity),
                      patch.object(supervisor, "_save", side_effect=[request_pin, request_pin, self.terminal]),
                      patch.object(supervisor, "_terminal", return_value=(request, identity)),
                      patch.object(env, "supervise_operation", side_effect=run) as outer,
                      patch.object(env, "supervise", side_effect=run) as inner):
                    self.assertEqual(supervisor._supervise(request), (self.terminal, identity))
                    self.assertEqual((outer.call_count, inner.call_count),
                                     (int(kind == "runtime"), int(kind == "controller")))
        self.assertEqual(path.rename.call_count, 2)

    def test_stage_refuses_inadequate_controller_time_without_job_launch(self):
        with (patch.object(supervisor.output_control, "validate_output", return_value=Mock()),
              patch.object(supervisor, "_remaining", return_value=lifecycle.SECONDS + supervisor.TAIL_SECONDS - 1),
              patch.object(supervisor, "_save"),
              patch.object(env, "supervise") as inner):
            with self.assertRaisesRegex(admission.AdmissionRefused, "^controller_budget$"):
                supervisor._supervise(self.controller_request)
            inner.assert_not_called()

    def test_stage_refuses_unknown_job_terminal_before_replaying_identity(self):
        terminal = dict(cleanup_complete=False)
        with (patch.object(lifecycle, "_at", return_value=terminal),
              patch.object(supervisor.process, "_owner_ok", return_value=False),
              patch.object(lifecycle, "_read") as read):
            with self.assertRaisesRegex(admission.AdmissionRefused, "^stage_terminal$"):
                supervisor._terminal("controller", self.terminal)
            read.assert_not_called()

    def test_enter_requires_same_parent_and_live_job_membership(self):
        stream = Mock(buffer=io.BytesIO(supervisor.BARRIER + env.encoded(self.admit)))
        api = Mock()
        api.current_job_pids.return_value = []
        with (patch.object(supervisor.sys, "stdin", stream),
              patch.object(supervisor.os, "getppid", return_value=self.runtime["pid"]),
              patch.object(supervisor, "_identity") as identity,
              patch.object(supervisor.shared, "_ProcessApi", return_value=api),
              patch.object(lifecycle, "_at", return_value=self.controller_request),
              patch.object(lifecycle, "_read") as read):
            with self.assertRaisesRegex(admission.AdmissionRefused, "^identity$"):
                supervisor._enter("controller")
            identity.assert_called_once_with(self.runtime["pid"], self.runtime)
            read.assert_not_called()

    def _stop_replay(self):
        self.enterContext(patch.object(lifecycle, "_read", return_value=(self.admit, self.gate)))
        self.enterContext(patch.object(lifecycle, "_at", side_effect=[
            self.launch_record, lifecycle.stop_value(self.admit)]))
        self.enterContext(patch.object(supervisor, "_terminal",
                                       return_value=(self.controller_request, self.controller)))
        self.enterContext(patch.object(lifecycle, "_inputs", return_value=(self.admitted, self.running)))
        return self.enterContext(patch.object(lifecycle, "verify_transfer"))

    def test_stop_replays_exact_controller_and_inherited_owner_pin(self):
        transfer = self._stop_replay()
        value = supervisor.verify_stop(self.admitted, self.admit, self.worker_result,
                                       expected_handoff_sha256=self.launch["sha256"])
        self.assertEqual(value, self.gate)
        transfer.assert_called_once_with(self.admit, self.live, self.admitted, self.running,
                                         self.result, self.controller)

    def test_live_owner_refuses_replacement_of_inherited_handoff(self):
        transfer = self._stop_replay()
        with self.assertRaisesRegex(admission.AdmissionRefused, "^handoff$"):
            supervisor.verify_stop(self.admitted, self.admit, self.worker_result, expected_handoff_sha256="f" * 64)
        transfer.assert_not_called()

    def test_expired_owner_refuses_even_with_a_gate(self):
        with patch.object(lifecycle, "_read") as read:
            with self.assertRaisesRegex(admission.AdmissionRefused, "^stop$"):
                supervisor.verify_stop(self.admitted, self.admit,
                                       dict(self.worker_result, reason="expired", stop_requested=False))
            read.assert_not_called()

    def test_stop_refuses_controller_from_different_attempt(self):
        transfer = self._stop_replay()
        self.controller_request["attempt"] = legacy.pin("D:/Synthetic/different.json")
        with self.assertRaisesRegex(admission.AdmissionRefused, "^request$"):
            supervisor.verify_stop(self.admitted, self.admit, self.worker_result)
        transfer.assert_not_called()

    def _stop_publication(self):
        calls = Mock()
        calls.prepare.return_value = self.attempt
        calls.commit.return_value = self.gate["stop"]
        calls.close.return_value = True
        for target, name, mock in (
            (supervisor, "_identity", Mock(return_value=self.runtime)),
            (supervisor, "_remaining", Mock(return_value=30)),
            (supervisor, "_terminal", Mock(return_value=(self.controller_request, self.controller))),
            (lifecycle, "verify_transfer", calls.transfer),
            (supervisor.owner, "LiveOwnedArchiveRoundtripTarget", Mock(return_value=calls)),
            (lifecycle, "prepare_stop", calls.prepare),
            (lifecycle, "commit_stop", calls.commit),
            (supervisor, "_save", calls.publish),
        ):
            self.enterContext(patch.object(target, name, mock))
        return calls

    def _publish(self):
        return supervisor._publish_stop(self.request, self.admitted, self.launch, self.live,
                                        self.running, self.result, self.terminal)

    def test_stop_is_committed_only_after_observer_closes_and_gate_exists(self):
        calls = self._stop_publication()
        self.assertEqual(self._publish(), self.controller)
        self.assertEqual([item[0] for item in calls.mock_calls], ["transfer", "prepare", "close", "publish", "commit"])
        calls.publish.assert_called_once_with(supervisor.STOP_GATE, self.gate)

    @unittest.skipUnless(os.name == "nt" and Path(tempfile.gettempdir()).drive.upper() == "D:",
                         "requires the physical D: Windows fixture directory")
    def test_windows_stop_rename_preserves_a_competing_stop(self):
        root = Path(self.enterContext(tempfile.TemporaryDirectory()))
        observer = Mock()
        pending = lifecycle.prepare_stop(root, self.admit, observer)
        stop = root / "stop-v1.json"
        self.assertFalse(stop.exists())
        stop.write_bytes(b"competing stop")
        with self.assertRaises(ValueError):
            lifecycle.commit_stop(root, self.admit, pending)
        self.assertEqual(stop.read_bytes(), b"competing stop")
        self.assertTrue(Path(pending["path"]).is_file())

    @unittest.skipUnless(os.name == "nt" and Path(tempfile.gettempdir()).drive.upper() == "D:",
                         "requires the physical D: Windows fixture directory")
    def test_windows_stop_rename_preserves_exact_bytes(self):
        root = Path(self.enterContext(tempfile.TemporaryDirectory()))
        pending = lifecycle.prepare_stop(root, self.admit, Mock())
        result = lifecycle.commit_stop(root, self.admit, pending)
        stop = root / "stop-v1.json"
        self.assertFalse(Path(pending["path"]).exists())
        self.assertEqual(result, supervisor.bridge._pin_bytes(stop, env.encoded(lifecycle.stop_value(self.admit))))
        self.assertEqual(env.read_json(stop), lifecycle.stop_value(self.admit))

    def test_observer_cleanup_failure_keeps_final_stop_absent(self):
        calls = self._stop_publication()
        calls.close.return_value = False
        with self.assertRaisesRegex(admission.AdmissionRefused, "^observer_cleanup$"):
            self._publish()
        calls.prepare.assert_called_once()
        calls.publish.assert_not_called()
        calls.commit.assert_not_called()

    def test_outer_deadline_after_gate_leaves_stop_unpublished(self):
        calls = self._stop_publication()
        supervisor._remaining.side_effect = [30, 30, admission.AdmissionRefused("deadline")]
        with self.assertRaisesRegex(admission.AdmissionRefused, "^deadline$"):
            self._publish()
        calls.publish.assert_called_once()
        calls.commit.assert_not_called()

    def _mock_runtime(self, *, failed=False):
        calls = Mock()
        calls.child.poll.side_effect = [None] if failed else [None, 0, 0]
        calls.spawn.return_value = calls.child
        calls.capture.return_value = calls.console
        calls.supervise.side_effect = admission.AdmissionRefused("stage_terminal") if failed else None
        calls.supervise.return_value = self.terminal, self.controller
        calls.stop.return_value = self.controller
        calls.close.return_value = {}, 0
        calls.save.return_value = self.admit
        owner = self.running["owner"]
        for target, name, value in (
            (supervisor, "_enter", Mock(return_value=self.request)),
            (admission, "verify_spent", Mock(return_value=self.context)),
            (handoff, "write", Mock(return_value=self.launch)),
            (handoff, "check_window", Mock()),
            (supervisor, "_remaining", Mock(return_value=40)),
            (supervisor.output_control, "validate_output", Mock(return_value=supervisor.OWNER_CONSOLE)),
            (supervisor.process, "ServerCapture", calls.capture),
            (supervisor.subprocess, "Popen", calls.spawn),
            (supervisor.subprocess, "CREATE_NO_WINDOW", 0),
            (supervisor, "_identity", Mock(return_value=owner)),
            (supervisor, "_wait_ready", Mock(return_value=(self.live, self.running))),
            (supervisor, "_supervise", calls.supervise),
            (lifecycle, "_read", Mock(return_value=(self.result, {}))),
            (supervisor, "_publish_stop", calls.stop),
            (supervisor.shared, "_close_popen", calls.close),
            (supervisor, "_owner_terminal", calls.owner_terminal),
            (lifecycle, "verify", calls.replay),
            (supervisor, "_save", calls.save),
        ):
            self.enterContext(patch.object(target, name, value, create=True))
        return calls

    def test_runtime_replays_and_records_only_after_controller_stop_and_owner_exit(self):
        calls = self._mock_runtime()
        supervisor._runtime()
        self.assertEqual(calls.spawn.call_args.kwargs["env"][handoff.HANDOFF_ENV], self.launch["sha256"])
        names = [item[0] for item in calls.mock_calls]
        self.assertLess(names.index("supervise"), names.index("stop"))
        self.assertLess(names.index("stop"), names.index("owner_terminal"))
        self.assertLess(names.index("owner_terminal"), names.index("replay"))
        calls.close.assert_called_once_with(calls.child, calls.console, allow_terminate=True)
        self.assertEqual(calls.save.call_args.args[0], supervisor.RUNTIME_RESULT)

    def test_failed_controller_does_not_publish_stop_or_claim_owner_closure(self):
        calls = self._mock_runtime(failed=True)
        with self.assertRaisesRegex(admission.AdmissionRefused, "^stage_terminal$"):
            supervisor._runtime()
        calls.stop.assert_not_called()
        calls.replay.assert_not_called()
        calls.close.assert_called_once_with(calls.child, calls.console, allow_terminate=False)
        self.assertEqual(calls.save.call_args.args[0], supervisor.OWNER_TERMINAL)

    def test_closed_replay_refuses_handoff_context_drift(self):
        value = dict(version=1, scope=supervisor.SCOPE, admission=self.admit, running=self.live,
                     started=self.admit, terminal=self.terminal, controller=self.result,
                     controller_terminal=self.terminal, proof=self.result)
        launch = copy.deepcopy(self.launch_record)
        launch["until_ns"] -= 1
        with (patch.object(lifecycle, "_read", return_value=(self.result, value)),
              patch.object(lifecycle, "_at", return_value={"owner": self.running["owner"], "handoff": self.launch}),
              patch.object(supervisor, "_read_handoff", return_value=launch),
              patch.object(supervisor, "_owner_terminal") as terminal):
            with self.assertRaisesRegex(admission.AdmissionRefused, "^handoff$"):
                supervisor._verify_runtime(self.request, self.runtime)
            terminal.assert_not_called()

    def test_bad_cli_does_not_read_or_spend_authority(self):
        with (patch.object(os, "name", "nt"), patch.object(lifecycle, "_read") as read,
              patch.object(supervisor, "execute") as run, patch("sys.stderr", new_callable=io.StringIO) as error):
            self.assertEqual(supervisor.main(["--authority-sha256", "invalid"]), 1)
            self.assertEqual(error.getvalue(), "authority\n")
            read.assert_not_called()
            run.assert_not_called()


if __name__ == "__main__":
    unittest.main()
