"""Inert SDK24 controller, owner and ledger evidence fixtures.

Copyright 2026 LocalLore contributors. SPDX-License-Identifier: Apache-2.0
"""
import copy
import hashlib
from contextlib import ExitStack
from io import BytesIO
from pathlib import Path, PureWindowsPath
from types import SimpleNamespace
import unittest
from unittest.mock import Mock, patch

from benchmarks import cross_owner_deletion_ui_closure as closure
from benchmarks import receipt_avd_storage as storage
from scripts.tests import test_owned_target_contract as fixture

env = closure.env
handoff = closure.handoff
owned = closure.owned
controller = closure.controller
REFUSED = (ValueError, RuntimeError)


class ClosedRun:
    def __init__(self, adversary=None):
        self.adversary = adversary
        self.files = {}
        self.root, self.guest = handoff.OWNED_ROOT, handoff.GUEST
        self.admission = fixture.admission()
        self.admission.update(root=str(self.root), seconds=1700, protocol=owned.PROTOCOL,
                              artifacts=owned.artifacts.artifact_bindings())
        self.admission["server"].update(root=str(self.root / "server"), seconds=1700)
        self.admission["guest"]["root"] = str(self.guest)
        sources = PureWindowsPath("D:/Synthetic/LocalLore")
        paths = [*(sources / "benchmarks" / name for name in owned.SOURCE_NAMES),
                 *(sources / "scripts" / name for name in ("audit_apk.py", "audit_physical_model_apk.py"))]
        self.admission["sources"] = sorted(map(fixture.pin, paths), key=lambda pin: pin["path"])
        self.admission_pin = self.record("admission", handoff.ADMISSION, self.admission)

        descriptor = fixture.running(self.admission)
        descriptor.update(protocol=owned.PROTOCOL, admission=self.admission_pin)
        self.owner_identity = copy.deepcopy(descriptor["owner"])
        self.worker_identity = copy.deepcopy(descriptor["worker"])
        self.running = self.record("running", self.root / "running-v1.json", descriptor)
        script = next(pin for pin in self.admission["sources"]
                      if PureWindowsPath(pin["path"]).name == owned.OWNER_SCRIPT)
        self.request = self.record("request", self.root / "request-v1.json", dict(
            version=1, protocol=owned.PROTOCOL, admission=self.admission_pin,
            validated_admission=self.admission, owner=self.owner_identity, sources=self.admission["sources"],
            python=self.admission["python"], worker_script=script, owner_seconds=1730))
        started = self.record("started", self.root / "started-v1.json",
                              dict(worker=self.worker_identity, request=self.request))
        terminal = self.record("terminal", self.root / "owner-result-v1.json", dict(
            status="child_exited", cleanup_complete=True, elapsed_ms=50, output_capture_complete=True,
            worker_returncode=0, stdout_bytes=0, stderr_bytes=0))
        after = self.record("after", self.root / "after-v1.json", dict(
            admission=self.admission_pin, sources=self.admission["sources"], python=self.admission["python"],
            tools=self.admission["server"]["tools"], owner=self.owner_identity, process_handles_closed=True))
        self.worker_path = self.root / "worker-result-v1.json"
        self.worker = self.record("worker", self.worker_path, dict(
            reason="stop_requested", stop_requested=True, running=self.running,
            cleanup={key: True for key in owned.CLEANUP_KEYS}))
        self.public = self.record("public", self.root / "result-v1.json", dict(
            version=1, protocol=owned.PROTOCOL, admission=self.admission_pin, request=self.request,
            started=started, owner=terminal, worker_result=self.worker, after=after, qualified_target=True,
            reason="stop_requested", feature_acceptance=False))

        run_sha = self.admission["guest"]["proposal"]["sha256"]
        self.closed = self.record("closure", self.guest / "guest-storage-closure-v1.json", dict(
            version=1, proposal_sha256=run_sha, closure_verified=True, cleanup_complete=True,
            admission=self.admission_pin, owner_result=terminal, worker_result=self.worker, after=after))
        entry = dict(root=str(self.guest), proposal_sha256=run_sha, state="closed", reserved_bytes=42,
                     closure=self.closed, retirement=None, retirement_receipt=None, recovery=None)
        self.mutate("entry", entry)
        self.ledger = self.record("ledger", handoff.LEDGER, dict(version=2, entries=[entry]))

        output = self.root / "controller-v1"
        self.controller_path = output / controller.RESULT_FILE
        session = self.record("session", output / owned.SESSION_FILE, dict(started_epoch=1800000020.0))
        self.readiness = dict(completed_epoch=1800000019.0)
        self.journey = dict(tests=[dict(passed=True)])
        self.controller = self.record("controller", self.controller_path, dict(
            version=2, scope=controller.SCOPE, admission=self.admission_pin, running=self.running,
            session=session, caller=self.worker_identity, client_count=26, readiness=self.readiness,
            journey=self.journey, outcome="completed", reason=None, observer_handles_closed=True, elapsed_ms=4))
        self.captures = {self.root / "worker-output-v1" / f"owner-{role}-v1.bin": b""
                         for role in ("stdout", "stderr")}
        self.mutate("captures", self.captures)

        self.replay = Mock(side_effect=lambda pin, *_: self.at(pin, self.worker_path))
        self.read_ledger = Mock(return_value=(self.ledger, entry))
        self.checked = Mock(side_effect=lambda pin: self.at(pin, Path(pin["path"])))
        self.ready_replay = Mock(return_value=self.readiness)
        self.journey_replay = Mock(return_value=self.journey)
        self.controller_replay = Mock(wraps=controller.verify_controller_result)

    def mutate(self, role, value):
        if self.adversary is not None and self.adversary[0] == role:
            self.adversary[1](value)

    def record(self, role, path, value):
        value = copy.deepcopy(value)
        self.mutate(role, value)
        self.files[path] = env.encoded(value)
        return self.read(path)[0]

    def read(self, path):
        env.require(path in self.files, "binding")
        payload = self.files[path]
        return fixture.pin(path, size=len(payload), sha=hashlib.sha256(payload).hexdigest()), env.decode_json(payload)

    def at(self, pin, path):
        actual, value = self.read(path)
        env.require(owned._same(pin, actual), "binding")
        return value

    def capture_path(self, path):
        env.require(path in self.captures, "capture")
        return SimpleNamespace(open=lambda mode: BytesIO(self.captures[path]))

    def verify(self, admission_pin=None):
        with ExitStack() as stack:
            for module, name, substitute in (
                (handoff, "read", self.read), (handoff, "at", self.at),
                (handoff, "ledger_entry", self.read_ledger), (env, "check_binding", self.checked),
                (env, "safe_path", self.capture_path), (owned.REPLAY, "verify_owned_target_result", self.replay),
                (owned.REPLAY, "_pin", lambda path: self.read(path)[0]),
                (owned.REPLAY, "_json", lambda pin: self.at(pin, Path(pin["path"]))),
                (owned.REPLAY, "_at", self.at), (owned, "verify_capture", self.journey_replay),
                (controller.boot, "verify_readiness", self.ready_replay),
                (controller, "verify_controller_result", self.controller_replay),
            ):
                stack.enter_context(patch.object(module, name, substitute))
            stack.enter_context(patch.object(env, "create_json", side_effect=AssertionError("evidence write")))
            stack.enter_context(patch.object(storage, "record_closed", side_effect=AssertionError("ledger write")))
            return closure.verify_result(self.admission_pin if admission_pin is None else admission_pin)


class CrossOwnerDeletionUiClosureTests(unittest.TestCase):
    def test_clean_stop_joins_controller_and_closed_ledger_without_writing(self):
        graph = ClosedRun()
        self.assertEqual(graph.verify(), dict(controller=graph.controller, owner=graph.public,
                                             closure=graph.closed, ledger=graph.ledger))
        graph.replay.assert_called_once_with(graph.worker, graph.admission, graph.admission_pin,
                                            graph.request, graph.worker_identity)
        graph.controller_replay.assert_called_once_with(graph.controller, graph.admission_pin, graph.running,
                                                       graph.worker_identity)
        graph.read_ledger.assert_called_once_with()
        for pin in (graph.admission_pin, graph.running, graph.public, graph.closed, graph.ledger, graph.controller):
            graph.checked.assert_any_call(pin)

    def test_foreign_admission_path_refuses_before_worker_replay(self):
        graph = ClosedRun()
        with self.assertRaises(REFUSED):
            graph.verify(admission_pin=dict(graph.admission_pin, path="D:/Synthetic/foreign.json"))
        graph.replay.assert_not_called()

    def test_owner_result_and_identity_refusals_stop_before_worker_replay(self):
        for role, mutate in (
            ("public", lambda row: row.update(protocol="owned-emulator-target-v1")),
            ("public", lambda row: row.update(reason="expired")),
            ("public", lambda row: row.update(qualified_target=1)),
            ("public", lambda row: row.update(feature_acceptance=True)),
            ("request", lambda row: row["owner"].update(pid=7001)),
            ("running", lambda row: row["owner"].update(creation_filetime=100)),
            ("started", lambda row: row["worker"].update(pid=7002)),
            ("started", lambda row: row.update(request=fixture.pin("D:/Synthetic/foreign.json"))),
            ("terminal", lambda row: row.update(worker_returncode=2)),
            ("captures", lambda rows: rows.update({next(iter(rows)): b"unexpected output"})),
            ("after", lambda row: row.update(process_handles_closed=False)),
        ):
            with self.subTest(role=role, mutate=mutate):
                graph = ClosedRun((role, mutate))
                with self.assertRaises(REFUSED):
                    graph.verify()
                graph.replay.assert_not_called()

    def test_worker_cleanup_and_ledger_must_qualify_before_controller_replay(self):
        for role, mutate in (
            ("worker", lambda row: row.update(reason="expired")),
            ("worker", lambda row: row.update(stop_requested=False)),
            ("worker", lambda row: row.update(running=fixture.pin("D:/Synthetic/foreign.json"))),
            ("worker", lambda row: row["cleanup"].update(guest_wait_completed=1)),
            ("worker", lambda row: row["cleanup"].pop("server_pipes_closed")),
            ("closure", lambda row: row.update(cleanup_complete=False)),
            ("closure", lambda row: row.update(owner_result=fixture.pin("D:/Synthetic/foreign.json"))),
            ("entry", lambda row: row.update(state="retained")),
            ("entry", lambda row: row.update(closure=fixture.pin("D:/Synthetic/foreign.json"))),
            ("entry", lambda row: row.update(proposal_sha256="a" * 64)),
            ("entry", lambda row: row.update(retirement_receipt={})),
        ):
            with self.subTest(role=role, mutate=mutate):
                graph = ClosedRun((role, mutate))
                with self.assertRaises(REFUSED):
                    graph.verify()
                graph.controller_replay.assert_not_called()

    def test_controller_must_belong_to_the_started_worker_and_complete(self):
        for mutate in (
            lambda row: row["caller"].update(pid=7001),
            lambda row: row.update(outcome="refused", reason="checks_failed"),
            lambda row: row.update(observer_handles_closed=False),
            lambda row: row.update(journey=dict(tests=[dict(passed=False)])),
        ):
            with self.subTest(mutate=mutate):
                graph = ClosedRun(("controller", mutate))
                with self.assertRaises(REFUSED):
                    graph.verify()
                graph.controller_replay.assert_called_once()

    def test_missing_evidence_refuses_without_repair(self):
        for directory, filename in (
            (handoff.OWNED_ROOT, "result-v1.json"), (handoff.OWNED_ROOT, "started-v1.json"),
            (handoff.OWNED_ROOT, "worker-result-v1.json"), (handoff.GUEST, "guest-storage-closure-v1.json"),
            (handoff.OWNED_ROOT / "controller-v1", controller.RESULT_FILE),
        ):
            with self.subTest(filename=filename):
                graph = ClosedRun()
                del graph.files[directory / filename]
                with self.assertRaises(REFUSED):
                    graph.verify()

    def test_final_recheck_refuses_ledger_or_controller_changed_after_replay(self):
        for path in (handoff.LEDGER, handoff.OWNED_ROOT / "controller-v1" / controller.RESULT_FILE):
            with self.subTest(path=path):
                graph = ClosedRun()

                verify_controller = controller.verify_controller_result

                def replace_after_replay(*args):
                    result = verify_controller(*args)
                    graph.files[path] += b" "
                    return result

                graph.controller_replay.side_effect = replace_after_replay
                with self.assertRaises(REFUSED):
                    graph.verify()
                graph.checked.assert_called_with(graph.ledger if path == handoff.LEDGER else graph.controller)
