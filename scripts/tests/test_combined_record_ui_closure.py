"""Inert process and ledger evidence for the SDK21 closure replay.

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

from benchmarks import combined_record_ui_closure as closure
from benchmarks import receipt_avd_storage as storage
from scripts.tests.test_owned_combined_record_ui_contract import admission as profile_admission
from scripts.tests.test_owned_target_contract import pin, running

contract = closure.contract
env = closure.env
handoff = closure.handoff
REFUSED = (ValueError, RuntimeError)


class ClosedRun:
    def __init__(self, adversary=None):
        self.adversary = adversary
        self.files = {}
        self.root, self.guest = handoff.OWNED_ROOT, handoff.GUEST
        self.admission = profile_admission()
        self.admission.update(root=str(self.root), seconds=1700)
        self.admission["server"].update(root=str(self.root / "server"), seconds=1700)
        self.admission_pin = self.record("admission", handoff.ADMISSION, self.admission)
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
        self.ledger = self.record("ledger", handoff.LEDGER, dict(version=2, entries=[entry]))
        self.captures = {self.root / "worker-output-v1" / f"owner-{role}-v1.bin": b""
                         for role in ("stdout", "stderr")}
        self.mutate("captures", self.captures)
        self.replay = Mock(side_effect=lambda binding, *_: self.at(binding, self.worker_path))
        self.read_ledger = Mock(return_value=(self.ledger, entry))
        self.checked = Mock(side_effect=lambda binding: self.at(binding, Path(binding["path"])))

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
        return pin(path, size=len(payload), sha=hashlib.sha256(payload).hexdigest()), env.decode_json(payload)

    def at(self, binding, path):
        actual, value = self.read(path)
        env.require(contract._same(binding, actual), "binding")
        return value

    def capture_path(self, path):
        env.require(path in self.captures, "capture")
        return SimpleNamespace(open=lambda mode: BytesIO(self.captures[path]))

    def verify(self, *, owner_identity=None):
        with ExitStack() as stack:
            for module, name, substitute in (
                (handoff, "read", self.read), (handoff, "at", self.at),
                (handoff, "ledger_entry", self.read_ledger), (env, "check_binding", self.checked),
                (env, "safe_path", self.capture_path), (closure.client.REPLAY, "verify_owned_target_result", self.replay),
            ):
                stack.enter_context(patch.object(module, name, substitute))
            stack.enter_context(patch.object(env, "create_json", side_effect=AssertionError("evidence write")))
            stack.enter_context(patch.object(storage, "record_closed", side_effect=AssertionError("ledger write")))
            return closure.verify_closure(self.admission_pin, self.admission, self.running_pin,
                                          self.owner_identity if owner_identity is None else owner_identity)


class CombinedRecordUiClosureTests(unittest.TestCase):
    def test_normal_stop_binds_owner_worker_storage_and_ledger(self):
        graph = ClosedRun()
        self.assertEqual(graph.verify(), dict(owner=graph.public, closure=graph.closed, ledger=graph.ledger))
        graph.replay.assert_called_once_with(graph.worker, graph.admission, graph.admission_pin,
                                            graph.request, graph.worker_identity)
        graph.read_ledger.assert_called_once_with(graph.guest)
        self.assertEqual(graph.checked.call_count, 10)
        for expected in (graph.public, graph.admission_pin, graph.running_pin, graph.closed, graph.ledger):
            graph.checked.assert_any_call(expected)

    def test_independently_observed_owner_must_match_the_saved_identity(self):
        graph = ClosedRun()
        wrong = dict(graph.owner_identity, creation_filetime=graph.owner_identity["creation_filetime"] + 1)
        with self.assertRaises(REFUSED):
            graph.verify(owner_identity=wrong)
        graph.replay.assert_not_called()
        graph.read_ledger.assert_not_called()

    def test_rebound_owner_refusals_stop_before_worker_replay(self):
        for role, mutate in (
            ("public", lambda row: row.update(reason="expired")),
            ("public", lambda row: row.update(version=True)),
            ("running", lambda row: row["owner"].update(pid=7002)),
            ("started", lambda row: row["worker"].update(pid=7003)),
            ("started", lambda row: row.update(request=pin("D:/Synthetic/foreign.json"))),
            ("terminal", lambda row: row.update(cleanup_complete=1)),
            ("terminal", lambda row: row.update(worker_returncode=2)),
            ("terminal", lambda row: row.update(output_capture_complete=False)),
            ("captures", lambda rows: rows.update({next(iter(rows)): b"unexpected output"})),
            ("after", lambda row: row["sources"][0].update(sha256="a" * 64)),
            ("after", lambda row: row.update(process_handles_closed=False)),
        ):
            with self.subTest(role=role, mutate=mutate):
                graph = ClosedRun((role, mutate))
                with self.assertRaises(REFUSED):
                    graph.verify()
                graph.replay.assert_not_called()
                graph.read_ledger.assert_not_called()

    def test_rebound_worker_and_storage_refusals_do_not_qualify_closure(self):
        for role, mutate in (
            ("worker", lambda row: row.update(reason="expired")),
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
            ("entry", lambda row: row.update(retirement_receipt={})),
        ):
            with self.subTest(role=role, mutate=mutate), self.assertRaises(REFUSED):
                ClosedRun((role, mutate)).verify()

    def test_missing_owner_worker_and_storage_records_refuse(self):
        for location, filename in (
            (handoff.OWNED_ROOT, "result-v1.json"), (handoff.OWNED_ROOT, "started-v1.json"),
            (handoff.OWNED_ROOT, "worker-result-v1.json"), (handoff.GUEST, "guest-storage-closure-v1.json"),
        ):
            with self.subTest(filename=filename):
                graph = ClosedRun()
                del graph.files[location / filename]
                with self.assertRaises(REFUSED):
                    graph.verify()

    def test_final_recheck_refuses_a_late_ledger_replacement(self):
        graph = ClosedRun()

        def replace_ledger(root):
            self.assertEqual(root, graph.guest)
            graph.files[handoff.LEDGER] += b" "
            return graph.read_ledger.return_value

        graph.read_ledger.side_effect = replace_ledger
        with self.assertRaises(REFUSED):
            graph.verify()
        graph.checked.assert_any_call(graph.ledger)
