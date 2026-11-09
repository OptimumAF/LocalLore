"""Synthetic cold-navigation closure records. All process and ledger ports are inert.

Copyright 2026 LocalLore contributors. SPDX-License-Identifier: Apache-2.0
"""
from contextlib import ExitStack, contextmanager
import copy
import hashlib
from io import BytesIO
from pathlib import Path, PureWindowsPath
from types import SimpleNamespace
import unittest
from unittest.mock import Mock, patch

from benchmarks import cold_navigation_ui_closure as closure
from scripts.tests.test_owned_cold_navigation_ui_contract import admission as cold_admission
from scripts.tests.test_owned_target_contract import pin, running

owner = closure.owner
contract = closure.contract
REFUSED = (ValueError, RuntimeError)


class ClosureRecords:
    def __init__(self, adversary=None):
        self.adversary = adversary
        self.records = {}
        self.root, self.guest = owner.OWNED_ROOT, owner.GUEST
        self.admission = cold_admission()
        self.admission.update(root=str(self.root), seconds=owner.OWNER_SECONDS)
        self.admission["server"].update(root=str(self.root / "server"), seconds=owner.OWNER_SECONDS)
        self.admission_pin = self.record("admission", owner.ADMISSION, self.admission)

        descriptor = running(self.admission)
        descriptor.update(protocol=contract.PROTOCOL, admission=self.admission_pin)
        self.owner_identity = copy.deepcopy(descriptor["owner"])
        self.worker_identity = copy.deepcopy(descriptor["worker"])
        self.running_pin = self.record("running", self.root / "running-v1.json", descriptor)
        script = next(row for row in self.admission["sources"]
                      if PureWindowsPath(row["path"]).name == contract.OWNER_SCRIPT)
        self.request = self.record("request", self.root / "request-v1.json", dict(
            version=1, protocol=contract.PROTOCOL, admission=self.admission_pin,
            validated_admission=self.admission, owner=self.owner_identity, sources=self.admission["sources"],
            python=self.admission["python"], worker_script=script, owner_seconds=owner.OWNER_SECONDS + 30))
        started = self.record("started", self.root / "started-v1.json",
                              dict(worker=self.worker_identity, request=self.request))
        terminal = self.record("terminal", self.root / "owner-result-v1.json", dict(
            status="child_exited", cleanup_complete=True, elapsed_ms=50, output_capture_complete=True,
            worker_returncode=0, stdout_bytes=0, stderr_bytes=0))
        after = self.record("after", self.root / "after-v1.json", dict(
            admission=self.admission_pin, sources=self.admission["sources"], python=self.admission["python"],
            tools=self.admission["server"]["tools"], owner=self.owner_identity, process_handles_closed=True))
        worker_path = self.root / "worker-result-v1.json"
        self.worker = self.record("worker", worker_path, dict(
            reason="stop_requested", stop_requested=True, running=self.running_pin,
            cleanup={key: True for key in contract.CLEANUP_KEYS}))
        self.public = self.record("public", self.root / "result-v1.json", dict(
            version=1, protocol=contract.PROTOCOL, admission=self.admission_pin, request=self.request,
            started=started, owner=terminal, worker_result=self.worker, after=after, qualified_target=True,
            reason="stop_requested", feature_acceptance=False))
        run_sha = self.admission["guest"]["proposal"]["sha256"]
        self.closed = self.record("closure", self.guest / "guest-storage-closure-v1.json", dict(
            version=1, proposal_sha256=run_sha, closure_verified=True, cleanup_complete=True,
            admission=self.admission_pin, owner_result=terminal, worker_result=self.worker, after=after))
        entry = dict(root=str(self.guest), proposal_sha256=run_sha, state="closed", reserved_bytes=42,
                     closure=self.closed, retirement=None, retirement_receipt=None, recovery=None)
        self.mutate("entry", entry)
        self.ledger = self.record("ledger", owner.LEDGER, {"version": 2, "entries": [entry]})
        self.captures = {self.root / "worker-output-v1" / f"owner-{role}-v1.bin": b""
                         for role in ("stdout", "stderr")}
        self.mutate("captures", self.captures)
        self.replay = Mock(side_effect=lambda binding, *_: owner._at(binding, worker_path))
        self.checked = Mock(side_effect=lambda binding: owner.files._bound(binding))
        self.read_ledger = Mock(return_value=(self.ledger, entry))

    def mutate(self, name, value):
        if self.adversary is not None and self.adversary[0] == name:
            self.adversary[1](value)

    def record(self, name, path, value):
        value = copy.deepcopy(value)
        self.mutate(name, value)
        payload = owner.env.encoded(value)
        self.records[path] = payload
        return pin(path, size=len(payload), sha=hashlib.sha256(payload).hexdigest())

    def raw(self, path, cap, *, project=True):
        if project is not True:
            raise AssertionError("fixture cannot read installed paths")
        data = self.records.get(Path(path))
        owner.env.require(data is not None and len(data) <= cap, "binding")
        return data

    def capture_path(self, path):
        data = self.captures.get(path)
        owner.env.require(data is not None, "capture")
        return SimpleNamespace(open=lambda mode: BytesIO(data))

    @contextmanager
    def ports(self):
        with ExitStack() as stack:
            for module, name, substitute in (
                (owner.files, "_read", self.raw),
                (owner, "_ledger", self.read_ledger),
                (closure.env, "check_binding", self.checked),
                (closure.env, "safe_path", self.capture_path),
                (closure.client._REPLAY, "verify_owned_target_result", self.replay),
            ):
                stack.enter_context(patch.object(module, name, substitute))
            yield

    def verify(self):
        with self.ports():
            return closure.verify_closure(self.admission_pin, self.admission, self.running_pin, self.owner_identity)


class ColdNavigationClosureTests(unittest.TestCase):
    def test_replays_exact_normal_stop_before_reporting_closed_ledger(self):
        graph = ClosureRecords()
        self.assertEqual(graph.verify(), dict(owner=graph.public, closure=graph.closed, ledger=graph.ledger))
        graph.replay.assert_called_once_with(graph.worker, graph.admission, graph.admission_pin,
                                            graph.request, graph.worker_identity)
        graph.read_ledger.assert_called_once_with(graph.guest)
        self.assertEqual(graph.checked.call_count, 10)
        for expected in (graph.public, graph.admission_pin, graph.running_pin, graph.closed, graph.ledger):
            graph.checked.assert_any_call(expected)

    def test_coherently_rebound_foreign_or_uncertain_owner_refuses_before_replay(self):
        for role, mutate in (
            ("public", lambda row: row.update(reason="expired")),
            ("public", lambda row: row.update(version=True)),
            ("public", lambda row: row.update(admission=pin("D:/Synthetic/foreign.json"))),
            ("request", lambda row: row["owner"].update(creation_filetime=7001)),
            ("running", lambda row: row["owner"].update(pid=7002)),
            ("started", lambda row: row["worker"].update(pid=7003)),
            ("started", lambda row: row.update(request=pin("D:/Synthetic/foreign.json"))),
            ("terminal", lambda row: row.update(cleanup_complete=1)),
            ("terminal", lambda row: row.update(output_capture_complete=False)),
            ("captures", lambda rows: rows.update({next(iter(rows)): b"unexpected output"})),
            ("after", lambda row: row["sources"][0].update(sha256="a" * 64)),
            ("after", lambda row: row.update(process_handles_closed=False)),
        ):
            with self.subTest(role=role, mutate=mutate):
                graph = ClosureRecords((role, mutate))
                with self.assertRaises(REFUSED):
                    graph.verify()
                graph.replay.assert_not_called()
                graph.read_ledger.assert_not_called()

    def test_coherently_rebound_worker_and_storage_closure_still_refuse(self):
        for role, mutate in (
            ("worker", lambda row: row.update(stop_requested=False)),
            ("worker", lambda row: row.update(running=pin("D:/Synthetic/foreign.json"))),
            ("worker", lambda row: row["cleanup"].update(guest_wait_completed=1)),
            ("worker", lambda row: row["cleanup"].pop("server_pipes_closed")),
            ("closure", lambda row: row.update(cleanup_complete=False)),
            ("closure", lambda row: row.update(owner_result=pin("D:/Synthetic/foreign.json"))),
            ("entry", lambda row: row.update(state="retained")),
            ("entry", lambda row: row.update(closure=pin("D:/Synthetic/foreign.json"))),
            ("entry", lambda row: row.update(proposal_sha256="a" * 64)),
            ("entry", lambda row: row.update(recovery={})),
        ):
            with self.subTest(role=role, mutate=mutate), self.assertRaises(REFUSED):
                ClosureRecords((role, mutate)).verify()

    def test_missing_required_records_refuse_without_reconstruction(self):
        for relative in ("result-v1.json", "started-v1.json", "worker-result-v1.json"):
            with self.subTest(relative=relative):
                graph = ClosureRecords()
                del graph.records[graph.root / relative]
                with self.assertRaises(REFUSED):
                    graph.verify()

    def test_final_ledger_binding_refuses_a_late_replacement(self):
        graph = ClosureRecords()

        def changed_ledger(root):
            self.assertEqual(root, graph.guest)
            payload = graph.records[owner.LEDGER]
            graph.records[owner.LEDGER] = payload + b" "
            return graph.read_ledger.return_value

        graph.read_ledger.side_effect = changed_ledger
        with self.assertRaises(REFUSED):
            graph.verify()
        graph.checked.assert_any_call(graph.ledger)


if __name__ == "__main__":
    unittest.main()
