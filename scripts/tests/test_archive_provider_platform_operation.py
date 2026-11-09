"""Host-only adversarial checks for the SDK26 one-use activation supervisor.

Copyright 2026 LocalLore contributors. SPDX-License-Identifier: Apache-2.0
"""
import io
import os
from pathlib import Path
import sys
from tempfile import TemporaryDirectory
from types import SimpleNamespace
import unittest
from unittest.mock import Mock, patch

from benchmarks import archive_provider_platform_admission as candidate
from benchmarks import archive_provider_platform_handoff as handoff
from benchmarks import archive_provider_platform_operation as operation
from benchmarks import owned_archive_provider_platform as owned
from benchmarks import receipt_avd_environment as env


OWNER_STDOUT = (b'{"qualified_target": true, "reason": "stop_requested", "feature_acceptance": false}\n'
                b'{"passed": true, "feature_acceptance": false}\n')


class ArchiveProviderOperationTests(unittest.TestCase):
    def setUp(self):
        self.root = Path(self.enterContext(TemporaryDirectory())).resolve()
        for module, names in (
            (handoff, ("AUTHORITY", "ATTEMPT")),
            (candidate, ("CANDIDATE", "ADMISSION", "RUN_AUTHORITY", "HANDOFF", "OWNED_ROOT", "COMPLETION")),
            (operation, ("REQUEST", "STARTED", "OWNER_STARTED", "TERMINAL", "RESULT", "CAPTURE")),
        ):
            for name in names:
                self.enterContext(patch.object(module, name, self.root / name.lower()))
        self.enterContext(patch.object(operation, "_context"))
        self.parent = self.identity_value(7101)
        self.worker = self.identity_value(7102)
        self.owner = self.identity_value(7103)
        self.authority_pin = self.save(handoff.AUTHORITY, {"synthetic": "authority"})
        self.candidate_pin = self.save(candidate.CANDIDATE, {"synthetic": "candidate"})
        self.admission_pin = self.save(candidate.ADMISSION, {"synthetic": "admission"})
        self.gate = self.enterContext(patch.object(operation, "_gate", return_value=self.admission_pin))
        self.identity = self.enterContext(patch.object(operation, "_identity", side_effect=self.observed_identity))
        self.popen = self.enterContext(patch("subprocess.Popen", side_effect=AssertionError("unexpected process")))
        self.enterContext(patch("socket.socket", side_effect=AssertionError("unexpected socket")))

    @staticmethod
    def identity_value(pid):
        return dict(pid=pid, creation_filetime=100000 + pid, executable=sys.executable)

    @staticmethod
    def save(path, value):
        env.create_json(path, value)
        return env.binding(path)

    def observed_identity(self, pid, expected=None):
        identity = self.identity_value(pid)
        if expected is not None and identity != expected:
            raise env.EnvironmentRefused("identity")
        return identity

    def make_request(self, *, started=True, **changes):
        began_ns = operation.time.monotonic_ns()
        attempt = self.save(handoff.ATTEMPT, handoff.claim_value(self.authority_pin, self.candidate_pin))
        request = dict(version=1, scope=handoff.AUTHORITY_SCOPE, authority=self.authority_pin,
                       attempt=attempt, candidate=self.candidate_pin, admission=self.admission_pin,
                       began_ns=began_ns, until_ns=began_ns + 1750 * handoff.NS, parent=self.parent)
        request.update(changes)
        request_pin = self.save(operation.REQUEST, request)
        if started:
            self.save(operation.STARTED, dict(request=request_pin, worker=self.worker))
        return request_pin, request

    def execute(self):
        with patch.object(os, "getpid", return_value=self.parent["pid"]):
            return operation.execute(self.authority_pin, self.candidate_pin)

    def test_malformed_cold_cli_never_reads_authority_or_dispatches(self):
        for args in ([], ["--authority-sha256", "A" * 64], ["--authority-sha256", "a" * 64, "extra"],
                     ["--authority-sha256", "a" * 63]):
            with self.subTest(args=args), patch.object(operation, "_read") as read:
                self.assertEqual(operation.main(args), 1)
                read.assert_not_called()
        self.gate.assert_not_called()
        self.popen.assert_not_called()
        self.assertFalse(handoff.ATTEMPT.exists())

    def test_forged_barrier_input_never_reaches_worker(self):
        for raw in (b"", b"wrong-prefix\n{}", operation.BARRIER + b"{" + b" " * 131072,
                    operation.BARRIER + b'{"a":1,"a":2}'):
            with (self.subTest(size=len(raw)),
                  patch.object(sys, "stdin", SimpleNamespace(buffer=io.BytesIO(raw))),
                  patch.object(operation, "_run_worker") as worker):
                self.assertEqual(operation.main(["_worker"]), 1)
                worker.assert_not_called()
        self.popen.assert_not_called()

    def test_candidate_gate_refusal_leaves_authority_unspent(self):
        self.gate.side_effect = env.EnvironmentRefused("ledger_changed")
        with (patch.object(env, "supervise_operation") as supervise,
              self.assertRaisesRegex(env.EnvironmentRefused, "^ledger_changed$")):
            self.execute()
        supervise.assert_not_called()
        self.gate.assert_called_once_with(self.authority_pin, self.candidate_pin)
        self.popen.assert_not_called()
        self.assertFalse(handoff.ATTEMPT.exists())
        self.assertFalse(operation.REQUEST.exists())

    def test_prior_claim_cannot_be_reopened_or_replaced(self):
        prior = self.save(handoff.ATTEMPT, {"prior": "refused"})
        with (patch.object(env, "supervise_operation") as supervise,
              self.assertRaisesRegex(env.EnvironmentRefused, "^already_used$")):
            self.execute()
        supervise.assert_not_called()
        self.gate.assert_not_called()
        self.popen.assert_not_called()
        self.assertEqual(env.binding(handoff.ATTEMPT), prior)

    def test_stale_owner_observation_blocks_a_new_attempt_before_gate(self):
        prior = self.save(operation.OWNER_STARTED, {"prior": "owner"})
        with (patch.object(env, "supervise_operation") as supervise,
              self.assertRaisesRegex(env.EnvironmentRefused, "^already_used$")):
            self.execute()
        supervise.assert_not_called()
        self.gate.assert_not_called()
        self.popen.assert_not_called()
        self.assertEqual(env.binding(operation.OWNER_STARTED), prior)
        self.assertFalse(handoff.ATTEMPT.exists())

    def test_supervisor_spends_once_and_requires_terminal_replay(self):
        completion = self.save(self.root / "verified", {"synthetic": "completion"})
        terminal = {"synthetic": "supervised terminal"}

        def supervise(command, raw, capture, seconds, started):
            self.assertEqual(env.read_json(handoff.ATTEMPT),
                             handoff.claim_value(self.authority_pin, self.candidate_pin))
            self.assertEqual(command[-1], "_worker")
            self.assertEqual(capture, operation.CAPTURE)
            self.assertGreater(seconds, handoff.LAUNCH_TAIL_SECONDS)
            self.assertLessEqual(seconds, env.REAL_MAX_SECONDS)
            self.assertTrue(raw.startswith(operation.BARRIER))
            pin = env.decode_json(raw[len(operation.BARRIER):])
            self.assertEqual(pin, env.binding(operation.REQUEST))
            self.assertTrue(started(SimpleNamespace(pid=self.worker["pid"])))
            self.assertEqual(env.read_json(operation.STARTED), dict(request=pin, worker=self.worker))
            return terminal

        with (patch.object(env, "supervise_operation", side_effect=supervise) as watchdog,
              patch.object(operation, "_verify_terminal", return_value=completion) as replay):
            result = self.execute()
            self.assertIs(result["passed"], True)
            self.assertIs(result["feature_acceptance"], False)
            self.assertEqual(result["completion"], completion)
            self.assertEqual(env.read_json(operation.RESULT), result)
            with self.assertRaisesRegex(env.EnvironmentRefused, "^already_used$"):
                self.execute()
        watchdog.assert_called_once()
        replay.assert_called_once()
        self.popen.assert_not_called()

    def test_expired_terminal_keeps_spent_claim_and_failure_evidence(self):
        terminal = dict(status="expired", cleanup_complete=True, elapsed_ms=100,
                        output_capture_complete=True, worker_returncode=1, stdout_bytes=0, stderr_bytes=0)
        with patch.object(env, "supervise_operation", return_value=terminal) as watchdog:
            result = self.execute()
            self.assertIs(result["passed"], False)
            self.assertIs(result["feature_acceptance"], False)
            self.assertIsNone(result["completion"])
            self.assertEqual(result["supervisor"], env.binding(operation.TERMINAL))
            self.assertEqual(result["attempt"], env.binding(handoff.ATTEMPT))
            self.assertEqual(env.read_json(operation.TERMINAL), terminal)
            self.assertEqual(env.read_json(operation.RESULT), result)
            with self.assertRaisesRegex(env.EnvironmentRefused, "^already_used$"):
                self.execute()
        watchdog.assert_called_once()
        self.popen.assert_not_called()

    def test_terminal_replay_uses_owner_observed_by_worker(self):
        request_pin, request = self.make_request()
        terminal = dict(status="child_exited", cleanup_complete=True, elapsed_ms=100,
                        output_capture_complete=True, worker_returncode=0, stdout_bytes=0, stderr_bytes=0)
        operation.CAPTURE.mkdir()
        for channel in ("stdout", "stderr"):
            raw = b""
            if channel == "stdout":
                raw = OWNER_STDOUT.replace(b"\n", b"\r\n")
            (operation.CAPTURE / ("owner-" + channel + "-v1.bin")).write_bytes(raw)
            terminal[channel + "_bytes"] = len(raw)
        terminal_pin = self.save(operation.TERMINAL, terminal)
        handoff_pin = self.save(candidate.HANDOFF, operation._handoff(request, self.worker))
        self.save(operation.OWNER_STARTED, dict(request=request_pin, handoff=handoff_pin, owner=self.owner))
        evidence = {name: self.save(self.root / name, {"synthetic": name})
                    for name in ("controller", "owner-result", "closure", "ledger")}
        evidence["owner"] = evidence.pop("owner-result")
        completion_value = dict(version=1, scope=handoff.AUTHORITY_SCOPE, admission=self.admission_pin, **evidence)
        completion = self.save(candidate.COMPLETION, completion_value)
        approved = dict(admission=self.admission_pin, ledger=evidence["ledger"],
                        proposal=self.save(self.root / "proposal", {"synthetic": "proposal"}))

        with (patch.object(handoff, "read_approval", return_value=approved),
              patch.object(operation.closure, "verify_result", return_value=evidence) as replay):
            self.assertEqual(operation._verify_terminal(request_pin, request, self.worker, terminal_pin, terminal),
                             completion)
        replay.assert_called_once_with(self.admission_pin, self.owner)
        self.popen.assert_not_called()

    def native_api(self, members):
        api = Mock()
        api.open_process.side_effect = lambda pid: pid
        api.alive.return_value = True
        api.identity.side_effect = self.identity_value
        api.close_handle.return_value = True
        api.current_job_pids.return_value = members
        api.parent_pid.side_effect = {
            self.worker["pid"]: self.parent["pid"], self.owner["pid"]: self.worker["pid"],
        }.__getitem__
        return api

    def test_worker_requires_live_job_before_materializing_authority(self):
        request_pin, _ = self.make_request()
        api = self.native_api([])
        with (patch.object(os, "getpid", return_value=self.worker["pid"]),
              patch.object(os, "getppid", return_value=self.parent["pid"]),
              patch.object(operation.mechanisms, "_ProcessApi", return_value=api),
              patch.object(handoff, "materialize_run_authorization") as materialize,
              patch.object(operation, "_start_owner") as owner):
            with self.assertRaises((RuntimeError, ValueError)):
                operation._run_worker(request_pin)
        materialize.assert_not_called()
        owner.assert_not_called()
        self.popen.assert_not_called()
        self.assertFalse(candidate.HANDOFF.exists())

    def test_worker_waits_for_starter_receipt_before_materializing_authority(self):
        request_pin, request = self.make_request(started=False)
        api = self.native_api([self.worker["pid"]])

        def publish_started(_):
            self.assertFalse(candidate.HANDOFF.exists())
            self.save(operation.STARTED, dict(request=request_pin, worker=self.worker))

        def launch(actual_request_pin, actual_request, handoff_pin):
            self.assertEqual(actual_request_pin, request_pin)
            self.assertEqual(actual_request, request)
            self.assertEqual(handoff_pin, env.binding(candidate.HANDOFF))
            self.assertEqual(env.read_json(candidate.HANDOFF), operation._handoff(request, self.worker))
            return 0

        with (patch.object(os, "getpid", return_value=self.worker["pid"]),
              patch.object(os, "getppid", return_value=self.parent["pid"]),
              patch.object(operation.mechanisms, "_ProcessApi", return_value=api),
              patch.object(operation.time, "sleep", side_effect=publish_started) as wait,
              patch.object(handoff, "materialize_run_authorization",
                           return_value=self.save(candidate.RUN_AUTHORITY, {"synthetic": "run"})) as materialize,
              patch.object(operation, "_start_owner", side_effect=launch) as owner):
            self.assertEqual(operation._run_worker(request_pin), 0)
        wait.assert_called_once()
        materialize.assert_called_once_with(self.authority_pin, self.candidate_pin, request["attempt"])
        owner.assert_called_once()
        self.popen.assert_not_called()

    def test_worker_refuses_started_record_for_another_request(self):
        request_pin, _ = self.make_request(started=False)
        different = self.save(self.root / "foreign-request.json", {"synthetic": "borrowed"})
        self.save(operation.STARTED, dict(request=different, worker=self.worker))
        api = self.native_api([self.worker["pid"]])
        with (patch.object(os, "getpid", return_value=self.worker["pid"]),
              patch.object(os, "getppid", return_value=self.parent["pid"]),
              patch.object(operation.mechanisms, "_ProcessApi", return_value=api),
              patch.object(handoff, "materialize_run_authorization") as materialize,
              patch.object(operation, "_start_owner") as owner,
              self.assertRaises((RuntimeError, ValueError))):
            operation._run_worker(request_pin)
        materialize.assert_not_called()
        owner.assert_not_called()
        self.popen.assert_not_called()

    def test_owner_barrier_releases_only_after_live_identity_is_published(self):
        request_pin, request = self.make_request()
        handoff_pin = self.save(candidate.HANDOFF, operation._handoff(request, self.worker))
        api = self.native_api([self.worker["pid"], self.owner["pid"]])
        child = self.popen.return_value
        child.pid = self.owner["pid"]
        child.poll.return_value = None
        child.wait.return_value = 0
        self.popen.side_effect = None

        def release(raw):
            self.assertTrue(raw.startswith(operation.OWNER_BARRIER))
            self.assertEqual(env.decode_json(raw[len(operation.OWNER_BARRIER):]), request_pin)
            self.assertEqual(env.read_json(operation.OWNER_STARTED),
                             dict(request=request_pin, handoff=handoff_pin, owner=self.owner))
            return len(raw)

        child.stdin.__enter__.return_value = child.stdin
        child.stdin.write.side_effect = release
        with (patch.object(os, "getpid", return_value=self.worker["pid"]),
              patch.object(os, "getppid", return_value=self.parent["pid"]),
              patch.object(operation.mechanisms, "_ProcessApi", return_value=api)):
            self.assertEqual(operation._start_owner(request_pin, request, handoff_pin), 0)
        self.popen.assert_called_once()
        self.assertEqual(self.popen.call_args.args[0][-1], "_owner")
        child.stdin.write.assert_called_once()
        child.stdin.__exit__.assert_called_once()
        child.wait.assert_called()

    def test_foreign_owner_job_never_releases_the_owner_barrier(self):
        request_pin, request = self.make_request()
        handoff_pin = self.save(candidate.HANDOFF, operation._handoff(request, self.worker))
        api = self.native_api([self.worker["pid"]])
        child = self.popen.return_value
        child.pid = self.owner["pid"]
        child.poll.return_value = None
        child.wait.return_value = 1
        self.popen.side_effect = None
        with (patch.object(os, "getpid", return_value=self.worker["pid"]),
              patch.object(os, "getppid", return_value=self.parent["pid"]),
              patch.object(operation.mechanisms, "_ProcessApi", return_value=api),
              self.assertRaises((RuntimeError, ValueError))):
            operation._start_owner(request_pin, request, handoff_pin)
        child.stdin.write.assert_not_called()
        self.assertFalse(operation.OWNER_STARTED.exists())

    def test_owner_gate_never_dispatches_with_missing_live_observation(self):
        request_pin, request = self.make_request()
        handoff_pin = self.save(candidate.HANDOFF, operation._handoff(request, self.worker))
        api = self.native_api([self.worker["pid"], self.owner["pid"]])
        with (patch.object(os, "getpid", return_value=self.owner["pid"]),
              patch.object(os, "getppid", return_value=self.worker["pid"]),
              patch.object(operation.mechanisms, "_ProcessApi", return_value=api),
              patch.dict(os.environ, {owned.HANDOFF_ENV: handoff_pin["sha256"]}),
              patch.object(owned, "main") as owner,
              self.assertRaises((OSError, RuntimeError, ValueError))):
            operation._run_owner(request_pin)
        owner.assert_not_called()
        self.popen.assert_not_called()

    def test_claim_race_preserves_first_publication_and_never_dispatches(self):
        competitor = {"synthetic": "competing claim"}

        def gate(*_):
            self.save(handoff.ATTEMPT, competitor)
            return self.admission_pin

        self.gate.side_effect = gate
        with (patch.object(env, "supervise_operation") as supervise,
              self.assertRaises(FileExistsError)):
            self.execute()
        self.assertEqual(env.read_json(handoff.ATTEMPT), competitor)
        supervise.assert_not_called()
        self.popen.assert_not_called()
        self.assertFalse(operation.REQUEST.exists())

    def test_outer_capture_refuses_stderr_or_substituted_success(self):
        operation.CAPTURE.mkdir()
        stdout = OWNER_STDOUT
        terminal = dict(status="child_exited", cleanup_complete=True, elapsed_ms=100,
                        output_capture_complete=True, worker_returncode=0, stdout_bytes=len(stdout), stderr_bytes=0)
        out = operation.CAPTURE / "owner-stdout-v1.bin"
        err = operation.CAPTURE / "owner-stderr-v1.bin"
        out.write_bytes(stdout)
        err.write_bytes(b"")
        operation._verify_capture(terminal)

        for changed, suffix in ((stdout.replace(b"stop_requested", b"stop_spoofed!!"), b""),
                                (stdout + b"\n", b""),
                                (stdout, b"x")):
            with self.subTest(stdout=changed, stderr=suffix):
                out.write_bytes(changed)
                err.write_bytes(suffix)
                with self.assertRaisesRegex(env.EnvironmentRefused, "^owner$"):
                    operation._verify_capture(terminal)

    def test_owner_gate_refuses_pid_reuse_before_dispatch(self):
        request_pin, request = self.make_request()
        handoff_pin = self.save(candidate.HANDOFF, operation._handoff(request, self.worker))
        stale = dict(self.owner, creation_filetime=self.owner["creation_filetime"] - 1)
        self.save(operation.OWNER_STARTED, dict(request=request_pin, handoff=handoff_pin, owner=stale))
        api = self.native_api([self.worker["pid"], self.owner["pid"]])
        with (patch.object(os, "getpid", return_value=self.owner["pid"]),
              patch.object(os, "getppid", return_value=self.worker["pid"]),
              patch.object(operation.mechanisms, "_ProcessApi", return_value=api),
              patch.dict(os.environ, {owned.HANDOFF_ENV: handoff_pin["sha256"]}),
              patch.object(owned, "main") as owner,
              self.assertRaisesRegex(env.EnvironmentRefused, "^identity$")):
            operation._run_owner(request_pin)
        owner.assert_not_called()
        self.popen.assert_not_called()
