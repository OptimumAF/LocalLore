"""SDK19 activation evidence and authority gates, with inert host/device ports."""

from contextlib import ExitStack, contextmanager
import copy
import hashlib
from pathlib import Path
from types import SimpleNamespace
import unittest
from unittest.mock import Mock, patch

from benchmarks import isolated_adb_owner as process
from benchmarks import receipt_avd_storage as storage
from benchmarks import record_large_text_ui_activation as a
from scripts.tests import test_owned_target_contract as legacy
from scripts.tests.test_record_large_text_ui_profile import admission as profile_admission


REFUSED = (ValueError, RuntimeError)
RUNTIME = Path("D:/Dev/Experiments/LocalLore/2026-11-09-record-large-text-ui-runtime-v1")
ADMISSION = RUNTIME / "admission-v1.json"
OWNED = RUNTIME / "owned-v1"
CONTROL = RUNTIME / "control-v1"
REGISTRY = Path("D:/Dev/_Migration/LocalLore-AVD-Storage")


def terminal(exit_code=0):
    return dict(status="child_exited", cleanup_complete=True, elapsed_ms=73,
                output_capture_complete=True, worker_returncode=exit_code,
                stdout_bytes=0, stderr_bytes=0)


class Records:
    """Return only synthetic named receipts with independent content-derived pins."""

    def __init__(self):
        self.values = {}

    def set(self, path, value):
        path = Path(path)
        self.values[path] = copy.deepcopy(value)
        return self.pin(path)

    def pin(self, path):
        path = Path(path)
        payload = a.env.encoded(self.values[path])
        return dict(path=str(path), bytes=len(payload),
                    sha256=hashlib.sha256(payload).hexdigest())

    def bound(self, pin, *args, **kwargs):
        if pin != self.pin(pin["path"]):
            raise a.env.EnvironmentRefused("binding")
        return copy.deepcopy(self.values[Path(pin["path"])])

    def read(self, path, *args, **kwargs):
        pin = self.pin(path)
        return pin, self.bound(pin)

    def check(self, pin):
        self.bound(pin)


class ActivationGraph:
    def __init__(self):
        self.records = Records()
        self.admission = profile_admission()
        self.admission.update(root=str(OWNED), seconds=1700)
        self.admission["server"].update(root=str(OWNED / "server"), seconds=1700)
        self.guest = Path(self.admission["guest"]["root"])
        self.prepare = self.records.set(RUNTIME / "prepare-proposal-v1.json", dict(phase="prepare"))
        self.prepare_result = dict(version=1, proposal_sha256=self.prepare["sha256"],
                                   status="completed", closure_verified=True,
                                   child_cleanup_complete=True, prepared_created=True)
        self.prepare_result_pin = self.records.set(self.guest / "prepare-result-v1.json", self.prepare_result)
        self.proposal = dict(phase="run", paths=dict(root=str(self.guest)),
                             memory_mib=8192, cores=4, max_seconds=1800,
                             prepare_proposal=self.prepare, prepare_result=self.prepare_result_pin)
        self.proposal_pin = self.records.set(RUNTIME / "run-proposal-v1.json", self.proposal)
        self.authorization = dict(version=1, phase="run", proposal_sha256=self.proposal_pin["sha256"],
                                  allow_environment_calls=True, root_go_pending=False)
        self.authorization_pin = self.records.set(RUNTIME / "run-authorization-v1.json", self.authorization)
        self.admission["guest"].update(proposal=self.proposal_pin, authorization=self.authorization_pin)
        self.admission_pin = self.records.set(ADMISSION, self.admission)
        self.entry = dict(root=str(self.guest), proposal_sha256=self.prepare["sha256"],
                          state="prepared", reserved_bytes=40 * 1024**3, closure=None,
                          retirement=None, retirement_receipt=None, recovery=None)
        self.ledger = dict(version=2, max_guests=2, budget_bytes=64 * 1024**3,
                           reservation_bytes=40 * 1024**3, entries=[self.entry])
        self.ledger_pin = self.records.set(REGISTRY / "ledger-v1.json", self.ledger)
        self.revalidate = Mock()
        self.verify_artifacts = Mock()
        self.verify_prepared = Mock()
        self.validate_proposal = Mock()
        self.check_authorization = Mock(wraps=a.env.check_authorization)
        self.storage_validate = Mock()
        self.storage_entry = Mock(side_effect=lambda ledger, root: next(
            item for item in ledger["entries"] if Path(item["root"]) == Path(root)))
        self.exists = Mock(return_value=False)
        self.replay = Mock()

    @contextmanager
    def ports(self):
        with ExitStack() as stack:
            for module, name, substitute in (
                (a, "_bound", self.records.bound),
                (a, "_read", self.records.read),
                (a.env, "binding", self.records.pin),
                (a.env, "check_binding", self.records.check),
                (a.env, "validate_proposal", self.validate_proposal),
                (a.env, "check_authorization", self.check_authorization),
                (a.env, "verify_prepared", self.verify_prepared),
                (a.env, "safe_path", lambda path, *args, **kwargs: Path(path)),
                (a.contract, "revalidate_inputs", self.revalidate),
                (a.contract, "verify_current", self.verify_artifacts),
                (a.os.path, "lexists", self.exists),
                (storage, "_validate", self.storage_validate),
                (storage, "_entry", self.storage_entry),
                (a.verification, "verify_owned_target_result", self.replay),
            ):
                stack.enter_context(patch.object(module, name, substitute))
            yield

    def close_graph(self):
        running = legacy.running(self.admission)
        running.update(protocol="owned-emulator-record-large-text-ui-v1", admission=self.admission_pin)
        self.owner, self.worker = running["owner"], running["worker"]
        self.running_pin = self.records.set(OWNED / "running-v1.json", running)
        self.request_pin = self.records.set(OWNED / "request-v1.json", dict(
            version=1, protocol="owned-emulator-record-large-text-ui-v1",
            admission=self.admission_pin, validated_admission=self.admission, owner=self.owner,
            sources=self.admission["sources"], python=self.admission["python"],
            worker_script=next(pin for pin in self.admission["sources"]
                               if Path(pin["path"]).name == "owned_record_large_text_ui_owner.py"),
            owner_seconds=1730))
        self.started_pin = self.records.set(OWNED / "started-v1.json", dict(request=self.request_pin, worker=self.worker))
        self.worker_pin = self.records.set(OWNED / "worker-result-v1.json", dict(
            reason="stop_requested", running=self.running_pin,
            cleanup={key: True for key in a.contract.CLEANUP_KEYS}))
        self.replay.return_value = self.records.bound(self.worker_pin)
        self.owner_receipt = self.records.set(OWNED / "owner-result-v1.json", terminal())
        self.after_pin = self.records.set(OWNED / "after-v1.json", dict(
            admission=self.admission_pin, sources=self.admission["sources"],
            python=self.admission["python"], tools=self.admission["server"]["tools"],
            owner=self.owner, process_handles_closed=True))
        self.public = dict(version=1, protocol="owned-emulator-record-large-text-ui-v1",
                           admission=self.admission_pin, request=self.request_pin, started=self.started_pin,
                           worker_result=self.worker_pin, owner=self.owner_receipt, after=self.after_pin,
                           qualified_target=True, reason="stop_requested", feature_acceptance=False)
        self.public_pin = self.records.set(OWNED / "result-v1.json", self.public)
        self.closure = dict(version=1, proposal_sha256=self.proposal_pin["sha256"],
                            closure_verified=True, cleanup_complete=True, admission=self.admission_pin,
                            owner_result=self.owner_receipt, worker_result=self.worker_pin, after=self.after_pin)
        self.closure_pin = self.records.set(self.guest / "guest-storage-closure-v1.json", self.closure)
        self.entry.update(state="closed", reserved_bytes=1234, proposal_sha256=self.proposal_pin["sha256"],
                          closure=self.closure_pin)
        self.ledger_pin = self.records.set(REGISTRY / "ledger-v1.json", self.ledger)
        return self

    def verify_closure(self):
        return a._verify_closure(self.admission_pin, self.admission, self.running_pin, self.owner)


class RecordLargeTextActivationTests(unittest.TestCase):
    def test_known_terminal_separates_exit_status_from_cleanup_knowledge(self):
        self.assertIs(a._known_terminal(terminal(exit_code=7)), True)
        for change in (dict(status="expired"), dict(worker_returncode=False),
                       dict(cleanup_complete=1), dict(output_capture_complete=None),
                       dict(elapsed_ms=-1), dict(stdout_bytes=True), dict(stderr_bytes=-1),
                       dict(foreign=True)):
            with self.subTest(change=change):
                self.assertIs(a._known_terminal(dict(terminal(), **change)), False)

    def test_fixed_admission_requires_run_authorization_and_prepared_reservation(self):
        graph = ActivationGraph()
        with graph.ports():
            self.assertEqual(a._inputs(graph.admission_pin, fresh=True), graph.admission)
        graph.validate_proposal.assert_called_once_with(graph.proposal, "run")
        graph.check_authorization.assert_called_once_with(
            graph.authorization, "run", graph.proposal_pin["sha256"])
        graph.verify_prepared.assert_called_once_with(graph.proposal, initial=True)
        graph.revalidate.assert_called()
        graph.verify_artifacts.assert_called()
        self.assertEqual(graph.storage_entry.call_args.args, (graph.ledger, graph.guest))

    def test_other_admission_path_and_wrong_authority_refuse_without_preparation(self):
        graph = ActivationGraph()
        other_pin = graph.records.set(RUNTIME / "other-admission.json", graph.admission)
        with graph.ports(), self.assertRaises(REFUSED):
            a._inputs(other_pin, fresh=True)
        graph.check_authorization.assert_not_called()
        graph.verify_prepared.assert_not_called()

        # The digest binds these exact bytes, but they authorize preparation, not a run.
        graph.authorization["phase"] = "prepare"
        graph.admission["guest"]["authorization"] = graph.records.set(
            graph.authorization_pin["path"], graph.authorization)
        graph.admission_pin = graph.records.set(ADMISSION, graph.admission)
        with graph.ports(), self.assertRaises(REFUSED):
            a._inputs(graph.admission_pin, fresh=True)
        graph.verify_prepared.assert_not_called()

    def test_prepared_state_or_existing_launch_receipt_cannot_be_borrowed(self):
        for mutation in ("schema", "state", "proposal", "bytes", "output", "claim"):
            with self.subTest(mutation=mutation):
                graph = ActivationGraph()
                if mutation == "schema":
                    graph.ledger["version"] = 1
                elif mutation == "state":
                    graph.entry["state"] = "retained"
                elif mutation == "proposal":
                    graph.entry["proposal_sha256"] = graph.proposal_pin["sha256"]
                elif mutation == "bytes":
                    graph.entry["reserved_bytes"] -= 1
                else:
                    forbidden = OWNED if mutation == "output" else graph.guest / "owned-record-large-text-ui-boot-claim-v1.json"
                    graph.exists.side_effect = lambda path: Path(path) == forbidden
                graph.records.set(REGISTRY / "ledger-v1.json", graph.ledger)
                with graph.ports(), self.assertRaises(REFUSED):
                    a._inputs(graph.admission_pin, fresh=True)

    def test_bound_prepare_result_refuses_boolean_integer_aliases(self):
        for key, value in (("version", True), ("closure_verified", 1),
                           ("child_cleanup_complete", 1), ("prepared_created", 1)):
            with self.subTest(key=key):
                graph = ActivationGraph()
                graph.prepare_result[key] = value
                graph.proposal["prepare_result"] = graph.records.set(
                    graph.prepare_result_pin["path"], graph.prepare_result)
                graph.admission["guest"]["proposal"] = graph.records.set(
                    graph.proposal_pin["path"], graph.proposal)
                graph.authorization["proposal_sha256"] = graph.admission["guest"]["proposal"]["sha256"]
                graph.admission["guest"]["authorization"] = graph.records.set(
                    graph.authorization_pin["path"], graph.authorization)
                graph.admission_pin = graph.records.set(ADMISSION, graph.admission)
                with graph.ports(), self.assertRaises(REFUSED):
                    a._inputs(graph.admission_pin, fresh=True)
                graph.verify_prepared.assert_called_once_with(graph.proposal, initial=True)
                graph.storage_entry.assert_not_called()

    def test_closed_guest_replays_exact_live_owner_and_returns_bound_records(self):
        graph = ActivationGraph().close_graph()
        with graph.ports(), patch.object(process, "_owner_ok", return_value=True) as owner_check:
            self.assertEqual(graph.verify_closure(), dict(
                owner=graph.public_pin, closure=graph.closure_pin, ledger=graph.ledger_pin))
        owner_check.assert_called_once_with(terminal(), OWNED / "worker-output-v1")
        graph.replay.assert_called_once_with(
            graph.worker_pin, graph.admission, graph.admission_pin, graph.request_pin, graph.worker)

    def test_wrong_owner_result_and_started_receipt_fail_before_worker_replay(self):
        for mutation in ("other_owner", "unknown_capture", "false_version", "foreign_started"):
            with self.subTest(mutation=mutation):
                graph = ActivationGraph().close_graph()
                owner_known = mutation != "unknown_capture"
                if mutation == "other_owner":
                    graph.owner = dict(graph.owner, pid=9999)
                elif mutation == "false_version":
                    graph.public["version"] = True
                    graph.records.set(OWNED / "result-v1.json", graph.public)
                elif mutation == "foreign_started":
                    graph.public["started"] = graph.records.set(OWNED / "started-v1.json", dict(
                        request=legacy.pin(OWNED / "foreign-request.json"), worker=graph.worker))
                    graph.records.set(OWNED / "result-v1.json", graph.public)
                with graph.ports(), patch.object(process, "_owner_ok", return_value=owner_known):
                    with self.assertRaises(REFUSED):
                        graph.verify_closure()
                graph.replay.assert_not_called()

    def test_worker_running_cleanup_closure_and_ledger_drift_each_refuse(self):
        for mutation in ("running", "cleanup", "closure", "ledger", "late_ledger_pin"):
            with self.subTest(mutation=mutation):
                graph = ActivationGraph().close_graph()
                if mutation == "running":
                    graph.replay.return_value["running"] = legacy.pin(OWNED / "other-running.json")
                elif mutation == "cleanup":
                    graph.replay.return_value["cleanup"][next(iter(a.contract.CLEANUP_KEYS))] = False
                elif mutation == "closure":
                    graph.closure["owner_result"] = legacy.pin(OWNED / "foreign-owner-result-v1.json")
                    graph.entry["closure"] = graph.records.set(
                        graph.guest / "guest-storage-closure-v1.json", graph.closure)
                    graph.records.set(REGISTRY / "ledger-v1.json", graph.ledger)
                elif mutation == "ledger":
                    graph.entry["closure"] = legacy.pin(graph.guest / "foreign-closure.json")
                    graph.records.set(REGISTRY / "ledger-v1.json", graph.ledger)
                else:
                    check = graph.records.check
                    def changed(pin):
                        if pin == graph.ledger_pin:
                            raise a.env.EnvironmentRefused("changed")
                        check(pin)
                    graph.records.check = changed
                with graph.ports(), patch.object(process, "_owner_ok", return_value=True):
                    with self.assertRaises(REFUSED):
                        graph.verify_closure()

    def test_execute_refuses_fresh_inputs_before_output_or_supervisor(self):
        graph = ActivationGraph()
        with patch.object(Path, "cwd", return_value=Path(a.__file__).resolve().parents[1]), \
             patch.dict(a.os.environ, {key: "D:/Dev/_Temp" for key in ("TEMP", "TMP", "TMPDIR")}), \
             patch.object(a, "_inputs", side_effect=ValueError("synthetic-refusal")) as inputs, \
             patch.object(a.env, "supervise") as supervise, patch.object(Path, "mkdir") as mkdir:
            with self.assertRaises(REFUSED):
                a.execute(graph.admission_pin)
        inputs.assert_called_once_with(graph.admission_pin, fresh=True)
        mkdir.assert_not_called()
        supervise.assert_not_called()

    def test_unknown_outer_cleanup_never_reads_success_claims(self):
        graph = ActivationGraph()
        terminal_value = dict(terminal(), cleanup_complete=False)
        supervisor_pin = graph.records.set(CONTROL / "runtime-supervisor-v1.json", terminal_value)
        attempted = Mock(side_effect=AssertionError("must refuse before reading runtime claim"))
        with graph.ports(), \
             patch.object(Path, "cwd", return_value=a.ROOT), \
             patch.dict(a.os.environ, {key: "D:/Dev/_Temp" for key in ("TEMP", "TMP", "TMPDIR")}), \
             patch.object(a, "_supervise", return_value=dict(
                 terminal=terminal_value, pin=supervisor_pin, worker=None, known=False)) as supervise, \
             patch.object(a, "_read", side_effect=lambda path, *args:
                          attempted(path) if Path(path) == CONTROL / "runtime-result-v1.json"
                          else graph.records.read(path)), \
             patch.object(a, "_save", side_effect=graph.records.set) as save, \
             patch.object(Path, "mkdir") as mkdir:
            result = a.execute(graph.admission_pin)
        supervise.assert_called_once_with("runtime", graph.admission_pin, None, 1800)
        mkdir.assert_called_once_with()
        attempted.assert_not_called()
        save.assert_called_once_with(CONTROL / "activation-result-v1.json", result)
        self.assertIs(result["passed"], False)
        self.assertIs(result["feature_acceptance"], False)
        self.assertEqual(result["supervisor"], supervisor_pin)
        self.assertIsNone(result["runtime"])

    def test_run_owned_requires_supervised_controller_and_one_stop_before_replay(self):
        for known in (True, False):
            with self.subTest(known=known):
                graph = ActivationGraph().close_graph()
                graph.exists.side_effect = lambda path: Path(path) == OWNED / "running-v1.json"
                controller_pin = graph.records.set(
                    OWNED / "controller-v1/controller-result-v1.json", dict(outcome="completed"))
                caller = dict(graph.worker, pid=9011)
                terminal_value = dict(terminal(), cleanup_complete=known)
                supervisor_pin = graph.records.set(CONTROL / "controller-supervisor-v1.json", terminal_value)
                capture_pins = {name: graph.records.set(CONTROL / "owner-console-v1" / (name + ".bin"), "")
                                for name in ("stdout", "stderr")}
                child = SimpleNamespace(pid=graph.owner["pid"], poll=Mock(return_value=0 if known else 1))
                capture = Mock()
                capture.close.return_value = True
                observer = Mock()
                observer.close.return_value = True
                events = []
                def replay(*args):
                    self.assertEqual(events, ["stop", "observer_close", "capture_close"])
                    return {"outcome": "completed"}
                observer.close.side_effect = lambda: (events.append("observer_close"), True)[1]
                capture.close.side_effect = lambda: (events.append("capture_close"), True)[1]
                with graph.ports(), \
                     patch.object(a, "_identity", return_value=graph.owner), \
                     patch.object(a.subprocess, "Popen", return_value=child) as popen, \
                     patch.object(process, "ServerCapture", return_value=capture), \
                     patch.object(process, "_owner_ok", return_value=True), \
                     patch.object(a, "LiveOwnedRecordLargeTextUiTarget", return_value=observer), \
                     patch.object(a, "_supervise", return_value=dict(
                         terminal=terminal_value, pin=supervisor_pin, worker=caller, known=known)) as supervise, \
                     patch.object(a, "_stop", side_effect=lambda *args: events.append("stop")) as stop, \
                     patch.object(a, "_capture_pins", return_value=capture_pins), \
                     patch.object(a, "_inputs", return_value=graph.admission), \
                     patch.object(a, "_save", side_effect=graph.records.set), \
                     patch.object(a.controller, "verify_controller_result", side_effect=replay) as verify, \
                     patch.object(a.time, "monotonic", return_value=100):
                    result = a._run_owned(graph.admission_pin, graph.admission, until=1700)
                self.assertIs(result["passed"], known)
                self.assertEqual(result["controller_supervisor"], supervisor_pin)
                self.assertEqual(popen.call_args.args[0][-4:],
                                 ["--admission", graph.admission_pin["path"],
                                  "--admission-sha256", graph.admission_pin["sha256"]])
                supervise.assert_called_once_with("controller", graph.admission_pin, graph.running_pin, 1200)
                observer.close.assert_called_once_with()
                capture.close.assert_called_once_with()
                if known:
                    stop.assert_called_once_with(observer, OWNED, graph.admission_pin)
                    verify.assert_called_once_with(
                        controller_pin, graph.admission_pin, graph.running_pin, caller)
                    self.assertEqual(result["controller"], controller_pin)
                else:
                    stop.assert_not_called()
                    graph.replay.assert_not_called()
                    verify.assert_not_called()
                    self.assertEqual(events, ["observer_close", "capture_close"])

    def test_outer_interruption_after_success_update_revokes_the_result(self):
        for interrupted in (False, True):
            with self.subTest(interrupted=interrupted):
                graph = ActivationGraph().close_graph()
                request = graph.records.set(CONTROL / "runtime-request-v1.json", dict(kind="runtime"))
                receipt = graph.records.set(CONTROL / "runtime-supervisor-v1.json", terminal())
                controller = graph.records.set(OWNED / "controller-v1/controller-result-v1.json",
                                               dict(outcome="completed"))
                runtime = graph.records.set(CONTROL / "runtime-result-v1.json", dict(
                    passed=True, feature_acceptance=False, worker=graph.worker, admission=graph.admission_pin,
                    request=request, controller=controller, closure=dict(
                        owner=graph.public_pin, closure=graph.closure_pin, ledger=graph.ledger_pin)))
                success_updates = []

                class Result(dict):
                    def update(self, **values):
                        super().update(**values)
                        if values.get("passed") is True:
                            success_updates.append(values["runtime"])
                            if interrupted:
                                raise KeyboardInterrupt("private-activation-context")

                with graph.ports(), patch.object(a, "dict", Result, create=True), \
                     patch.object(a, "_inputs", return_value=graph.admission), \
                     patch.object(Path, "cwd", return_value=a.ROOT), \
                     patch.dict(a.os.environ, {key: "D:/Dev/_Temp" for key in ("TEMP", "TMP", "TMPDIR")}), \
                     patch.object(a, "_supervise", return_value=dict(
                         terminal=terminal(), pin=receipt, worker=graph.worker, request=request, known=True)), \
                     patch.object(process, "_owner_ok", return_value=True), \
                     patch.object(a, "_save", side_effect=graph.records.set) as save, \
                     patch.object(Path, "mkdir"):
                    result = a.execute(graph.admission_pin)
                self.assertEqual(success_updates, [runtime])
                self.assertIs(result["passed"], not interrupted)
                self.assertEqual(result.get("reason"), "cancelled" if interrupted else None)
                self.assertIs(result["feature_acceptance"], False)
                save.assert_called_once_with(CONTROL / "activation-result-v1.json", result)


if __name__ == "__main__":
    unittest.main()
