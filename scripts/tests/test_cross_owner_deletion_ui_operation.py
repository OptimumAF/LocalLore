"""Host-only checks for the SDK24 activation supervisor.

Copyright 2026 LocalLore contributors. SPDX-License-Identifier: Apache-2.0
"""
import copy
import os
from pathlib import Path
import sys
import tempfile
import unittest
from types import SimpleNamespace
from unittest.mock import patch

from benchmarks import cross_owner_deletion_ui_operation as operation

h = operation.h
env = operation.env


class CrossOwnerDeletionOperationTests(unittest.TestCase):
    def setUp(self):
        self.root = Path(self.enterContext(tempfile.TemporaryDirectory())).resolve()
        for name in ("ATTEMPT", "RUN_AUTHORITY", "HANDOFF", "OWNED_ROOT", "COMPLETION"):
            self.enterContext(patch.object(h, name, self.root / name.lower()))
        for name in ("REQUEST", "STARTED", "TERMINAL", "RESULT", "CAPTURE"):
            self.enterContext(patch.object(operation, name, self.root / name.lower()))
        self.enterContext(patch.object(operation, "_context"))
        self.enterContext(patch.object(h, "check_window"))
        self.parent = dict(pid=31, creation_filetime=100, executable=sys.executable)
        self.worker = dict(pid=32, creation_filetime=101, executable=sys.executable)
        self.authority = self.write("authority", {"approved": True})
        self.admitted = self.write("admission", {"admitted": True})
        self.started = self.enterContext(patch.object(operation, "_identity", side_effect=self.identity))
        self.gate = self.enterContext(patch.object(operation, "_gate", return_value=self.admitted))

    def write(self, name, value):
        return operation._save(self.root / name, value)

    def identity(self, pid, expected=None):
        identity = self.parent if pid == self.parent["pid"] else self.worker
        if expected is not None:
            self.assertEqual(expected, identity)
        return identity

    def request(self):
        attempt = self.write("attempt", dict(version=1, scope=h.AUTHORITY_SCOPE,
                                             authority=self.authority, no_retry=True))
        request = dict(version=1, scope=h.AUTHORITY_SCOPE, authority=self.authority, attempt=attempt,
                       admission=self.admitted, began_ns=100, until_ns=200, parent=self.parent)
        request_pin = operation._save(operation.REQUEST, request)
        operation._save(operation.STARTED, dict(request=request_pin, worker=self.worker))
        return request_pin, request

    def test_cold_cli_refuses_without_an_exact_digest(self):
        with patch.object(h, "read") as read:
            for args in ([], ["--authority-sha256", "A" * 64], ["--authority-sha256", "a" * 64, "extra"]):
                self.assertEqual(operation.main(args), 1)
            read.assert_not_called()

    def test_already_claimed_never_reopens_the_attempt(self):
        self.write("attempt", {"previous": True})
        with patch.object(env, "supervise_operation") as supervise:
            with self.assertRaisesRegex(env.EnvironmentRefused, "^already_used$"):
                operation.execute(self.authority)
        supervise.assert_not_called()
        self.gate.assert_not_called()
        self.assertEqual(env.read_json(h.ATTEMPT), {"previous": True})

    def test_gate_refusal_never_spends_the_grant(self):
        self.gate.side_effect = env.EnvironmentRefused("ledger")
        with patch.object(env, "supervise_operation") as supervise:
            with self.assertRaisesRegex(env.EnvironmentRefused, "^ledger$"):
                operation.execute(self.authority)
        self.assertFalse(h.ATTEMPT.exists())
        supervise.assert_not_called()

    def test_success_requires_joined_terminal_and_spends_one_claim(self):
        completion = self.write("verified", {"passed": True})

        def supervise(command, request, capture, seconds, started):
            self.assertTrue(h.ATTEMPT.is_file())
            self.assertEqual(command[-1], "_worker")
            self.assertEqual(capture, operation.CAPTURE)
            self.assertGreater(seconds, 0)
            self.assertLessEqual(seconds, h.ACTIVATION_SECONDS)
            self.assertTrue(started(SimpleNamespace(pid=self.worker["pid"])))
            self.assertEqual(env.decode_json(request[len(operation.BARRIER):]),
                             env.binding(operation.REQUEST))
            return {"fixture": "closed_job"}

        with patch.object(os, "getpid", return_value=self.parent["pid"]), \
                patch.object(env, "supervise_operation", side_effect=supervise) as supervisor, \
                patch.object(operation, "_verify_terminal", return_value=completion):
            result = operation.execute(self.authority)
            self.assertIs(result["passed"], True)
            self.assertEqual(result["completion"], completion)
            self.assertEqual(env.read_json(operation.RESULT), result)
            with self.assertRaisesRegex(env.EnvironmentRefused, "^already_used$"):
                operation.execute(self.authority)
            supervisor.assert_called_once()

    def test_terminal_refusal_retains_the_spent_claim_and_owner_record(self):
        with patch.object(os, "getpid", return_value=self.parent["pid"]), \
                patch.object(env, "supervise_operation", return_value={"fixture": "failed_job"}), \
                patch.object(operation, "_verify_terminal", side_effect=env.EnvironmentRefused("owner")):
            result = operation.execute(self.authority)
        self.assertIs(result["passed"], False)
        self.assertEqual(result["reason"], "owner")
        self.assertEqual(result["supervisor"], env.binding(operation.TERMINAL))
        self.assertEqual(result["attempt"], env.binding(h.ATTEMPT))

    def test_worker_refuses_outside_the_owned_job_before_authorization(self):
        request, _ = self.request()
        with patch.object(os, "getppid", return_value=self.parent["pid"]), \
                patch.object(os, "getpid", return_value=self.worker["pid"]), \
                patch.object(operation.mechanisms, "_ProcessApi") as api, \
                patch.object(operation.admission, "materialize_run_authorization") as materialize, \
                patch.object(operation.subprocess, "run") as launch:
            api.return_value.current_job_pids.return_value = []
            with self.assertRaisesRegex(env.EnvironmentRefused, "^identity$"):
                operation._run_worker(request)
        materialize.assert_not_called()
        launch.assert_not_called()

    def test_worker_materializes_exact_handoff_before_launch(self):
        request_pin, request = self.request()
        run_auth = self.write("run-auth", {"scope": "synthetic"})

        def launch(command, **kwargs):
            pin = env.binding(h.HANDOFF)
            self.assertEqual(kwargs["env"][h.HANDOFF_ENV], pin["sha256"])
            self.assertEqual(env.read_json(h.HANDOFF), operation._handoff(request, self.worker))
            self.assertEqual(command[-4:], ["--admission", self.admitted["path"],
                                           "--admission-sha256", self.admitted["sha256"]])
            return SimpleNamespace(returncode=0)

        with patch.object(os, "getppid", return_value=self.parent["pid"]), \
                patch.object(os, "getpid", return_value=self.worker["pid"]), \
                patch.object(operation.mechanisms, "_ProcessApi") as api, \
                patch.object(operation.admission, "materialize_run_authorization", return_value=run_auth) as materialize, \
                patch.object(operation.subprocess, "run", side_effect=launch) as child:
            api.return_value.current_job_pids.return_value = [self.worker["pid"]]
            self.assertEqual(operation._run_worker(request_pin), 0)
        materialize.assert_called_once_with(self.admitted, self.authority, request["attempt"])
        child.assert_called_once()

    def test_terminal_replay_refuses_substituted_handoff_or_completion(self):
        request_pin, request = self.request()
        terminal = {"fixture": "closed_job"}
        terminal_pin = operation._save(operation.TERMINAL, terminal)
        handoff = operation._handoff(request, self.worker)
        evidence = {"closure": self.write("closure", {"closed": True})}
        value = dict(version=1, scope=h.AUTHORITY_SCOPE, admission=self.admitted, **evidence)
        operation._save(h.HANDOFF, handoff)
        completion = operation._save(h.COMPLETION, value)
        with patch.object(operation.process, "_owner_ok", return_value=True), \
                patch.object(h, "_approval"), patch.object(operation.closure, "verify_result", return_value=evidence):
            self.assertEqual(operation._verify_terminal(request_pin, request, self.worker, terminal_pin, terminal),
                             completion)
            changed = dict(value, scope="foreign")
            h.COMPLETION.write_bytes(env.encoded(changed))
            with self.assertRaisesRegex(env.EnvironmentRefused, "^binding$"):
                operation._verify_terminal(request_pin, request, self.worker, terminal_pin, terminal)
            changed = copy.deepcopy(handoff)
            changed["supervisor"]["pid"] = 99
            h.HANDOFF.write_bytes(env.encoded(changed))
            with self.assertRaisesRegex(env.EnvironmentRefused, "^handoff$"):
                operation._verify_terminal(request_pin, request, self.worker, terminal_pin, terminal)
