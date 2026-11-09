"""Verify closed SDK26 evidence with synthetic files and no live Android calls.

Copyright 2026 LocalLore contributors. SPDX-License-Identifier: Apache-2.0
"""
from dataclasses import replace
from pathlib import Path, PureWindowsPath
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import patch

from benchmarks import archive_provider_platform_closure as closure
from scripts.tests import test_owned_archive_provider_platform as profile_fixture
from scripts.tests import test_owned_target_contract as fixture

candidate, controller, env, owned, prep, storage = (
    closure.candidate, closure.controller, closure.env, closure.owned, closure.prep, closure.storage,
)
REFUSALS = (OSError, RuntimeError, ValueError)


class ArchiveProviderClosureTests(unittest.TestCase):
    def setUp(self):
        directory = Path(self.enterContext(TemporaryDirectory())).resolve()
        self.root = directory / "owned-v1"
        self.guest = directory / "avd-v1"
        self.ledger_root = directory / "ledger"
        self.capture = self.root / "worker-output-v1"
        self.output = self.root / "controller-v1"
        for path in (self.guest, self.ledger_root, self.capture, self.output):
            path.mkdir(parents=True)
        self.enterContext(patch.object(candidate, "ADMISSION", directory / "admission-v1.json"))
        self.enterContext(patch.object(candidate, "OWNED_ROOT", self.root))
        self.enterContext(patch.object(prep, "GUEST", self.guest))
        self.enterContext(patch.object(prep, "LEDGER", self.ledger_root / "ledger-v1.json"))
        self.enterContext(patch.object(storage, "DEFAULT_REGISTRY", self.ledger_root))
        self.enterContext(patch.object(owned._API, "profile", replace(
            owned._API.profile, GUEST_ROOT=PureWindowsPath(self.guest),
        )))

        self.admission = profile_fixture.admission()
        self.admission["root"] = str(self.root)
        self.admission["server"]["root"] = str(self.root / "server")
        self.admission["guest"]["root"] = str(self.guest)
        self.admission_pin = self.save(candidate.ADMISSION, self.admission)
        running = fixture.running(self.admission)
        running.update(protocol=owned.PROTOCOL, admission=self.admission_pin)
        self.expected_owner = running["owner"]
        self.worker = running["worker"]
        self.running_pin = self.save(self.root / "running-v1.json", running)
        request = self.save(self.root / "request-v1.json", dict(
            version=1, protocol=owned.PROTOCOL, admission=self.admission_pin, owner=self.expected_owner,
            validated_admission=self.admission, sources=self.admission["sources"], python=self.admission["python"],
            worker_script=next(pin for pin in self.admission["sources"]
                               if PureWindowsPath(pin["path"]).name == owned.OWNER_SCRIPT),
            owner_seconds=self.admission["seconds"] + 30,
        ))
        started = self.save(self.root / "started-v1.json", dict(worker=self.worker, request=request))
        terminal = self.save(self.root / "owner-result-v1.json", dict(
            status="child_exited", cleanup_complete=True, elapsed_ms=500, output_capture_complete=True,
            worker_returncode=0, stdout_bytes=0, stderr_bytes=0,
        ))
        for channel in ("stdout", "stderr"):
            (self.capture / f"owner-{channel}-v1.bin").write_bytes(b"")
        after = self.save(self.root / "after-v1.json", dict(
            admission=self.admission_pin, sources=self.admission["sources"], python=self.admission["python"],
            tools=self.admission["server"]["tools"], owner=self.expected_owner, process_handles_closed=True,
        ))
        self.stop = dict(version=1, protocol=owned.PROTOCOL, admission_sha256=self.admission_pin["sha256"], action="stop")
        self.stop_path = self.root / "stop-v1.json"
        self.save(self.stop_path, self.stop)
        self.worker_record = dict(reason="stop_requested", stop_requested=True, running=self.running_pin,
                                  cleanup={key: True for key in owned.CLEANUP_KEYS})
        self.worker_pin = self.save(self.root / "worker-result-v1.json", self.worker_record)
        self.owner_pin = self.save(self.root / "result-v1.json", dict(
            version=1, protocol=owned.PROTOCOL, admission=self.admission_pin, request=request, started=started,
            worker_result=self.worker_pin, owner=terminal, after=after, qualified_target=True,
            reason="stop_requested", feature_acceptance=False,
        ))
        proposal_sha256 = self.admission["guest"]["proposal"]["sha256"]
        self.closure_pin = self.save(self.guest / "guest-storage-closure-v1.json", dict(
            version=1, proposal_sha256=proposal_sha256, closure_verified=True, cleanup_complete=True,
            admission=self.admission_pin, owner_result=terminal, worker_result=self.worker_pin, after=after,
        ))
        self.entry = dict(root=str(self.guest), state="closed", proposal_sha256=proposal_sha256, reserved_bytes=42,
                          closure=self.closure_pin, retirement=None, retirement_receipt=None, recovery=None)
        self.ledger = dict(version=2, max_guests=storage.MAX_GUESTS, budget_bytes=storage.BUDGET_BYTES,
                           reservation_bytes=storage.RESERVATION_BYTES, entries=[self.entry])
        self.ledger_pin = self.save(prep.LEDGER, self.ledger)
        self.controller_pin = self.save(self.output / controller.RESULT_FILE, {"synthetic": "two qualified results"})
        self.shared_replay = self.enterContext(patch.object(
            owned.REPLAY, "verify_owned_target_result", return_value=self.worker_record,
        ))
        self.controller_replay = self.enterContext(patch.object(controller, "verify_controller_result"))
        self.enterContext(patch.object(env, "create_json", side_effect=AssertionError("unexpected evidence write")))
        self.enterContext(patch.object(storage, "record_closed", side_effect=AssertionError("unexpected ledger write")))
        self.enterContext(patch("subprocess.Popen", side_effect=AssertionError("unexpected process")))
        self.enterContext(patch("socket.socket", side_effect=AssertionError("unexpected socket")))

    @staticmethod
    def save(path, value):
        path.write_bytes(env.encoded(value))
        return env.binding(path)

    def verify(self):
        return closure.verify_result(self.admission_pin, self.expected_owner)

    def test_exact_stop_joins_both_tests_and_closed_ledger(self):
        self.assertEqual(self.verify(), dict(controller=self.controller_pin, owner=self.owner_pin,
                                            closure=self.closure_pin, ledger=self.ledger_pin))
        self.controller_replay.assert_called_once_with(
            self.controller_pin, self.admission_pin, self.running_pin, self.worker,
        )
        self.shared_replay.assert_called_once()
        self.assertEqual(self.shared_replay.call_args.args[-1], self.worker)

    def test_ledger_v1_without_recovery_key_remains_readable(self):
        self.ledger["version"] = 1
        del self.entry["recovery"]
        pin = self.save(prep.LEDGER, self.ledger)
        self.assertEqual(self.verify()["ledger"], pin)

    def test_foreign_observed_owner_refuses_before_worker_replay(self):
        with self.assertRaisesRegex(RuntimeError, "owner"):
            closure.verify_result(self.admission_pin, dict(self.expected_owner, creation_filetime=41))
        self.shared_replay.assert_not_called()
        self.controller_replay.assert_not_called()

    def test_missing_or_wrong_stop_refuses_before_worker_replay(self):
        self.stop_path.unlink()
        with self.assertRaises(REFUSALS):
            self.verify()
        self.save(self.stop_path, dict(self.stop, admission_sha256="0" * 64))
        with self.assertRaisesRegex(ValueError, "stop"):
            self.verify()
        self.shared_replay.assert_not_called()

    def test_failed_worker_cleanup_refuses_before_controller_replay(self):
        key = next(iter(owned.CLEANUP_KEYS))
        self.worker_record["cleanup"][key] = False
        with self.assertRaisesRegex(RuntimeError, "cleanup"):
            self.verify()
        self.controller_replay.assert_not_called()

    def test_ledger_must_name_the_same_closed_receipt(self):
        self.entry.update(state="retained", reserved_bytes=storage.RESERVATION_BYTES, closure=None)
        self.save(prep.LEDGER, self.ledger)
        with self.assertRaisesRegex(RuntimeError, "ledger"):
            self.verify()
        self.controller_replay.assert_not_called()

    def test_controller_failure_refuses_even_with_qualified_owner(self):
        self.controller_replay.side_effect = env.EnvironmentRefused("checks_failed")
        with self.assertRaisesRegex(RuntimeError, "checks_failed"):
            self.verify()

    def test_final_recheck_refuses_late_stop_drift(self):
        self.controller_replay.side_effect = lambda *_: self.stop_path.write_bytes(b"{}")
        with self.assertRaisesRegex(RuntimeError, "binding_changed"):
            self.verify()

    def test_final_recheck_refuses_late_owner_output_drift(self):
        capture = self.capture / "owner-stdout-v1.bin"
        self.controller_replay.side_effect = lambda *_: capture.write_bytes(b"unexpected owner output")
        with self.assertRaisesRegex(RuntimeError, "owner"):
            self.verify()
