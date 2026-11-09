"""Host checks for the fixed SDK24 controller on an already owned target.

Copyright 2026 LocalLore contributors. SPDX-License-Identifier: Apache-2.0
"""
import copy
from pathlib import Path
import tempfile
import time
import unittest
from unittest.mock import Mock, patch

from benchmarks import cross_owner_deletion_ui_binding as binding
from benchmarks import cross_owner_deletion_ui_capture as capture
from benchmarks import cross_owner_deletion_ui_controller as controller
from benchmarks import cross_owner_deletion_ui_replay as journey
from benchmarks import owned_cross_owner_deletion_ui as owned
from benchmarks import owned_target_contract as core
from benchmarks import receipt_avd_environment as env
from scripts.tests.test_cross_owner_deletion_ui_capture import RECORDS
from scripts.tests.test_cross_owner_deletion_ui_replay import command_tape


class CrossOwnerDeletionUiControllerTests(unittest.TestCase):
    def setUp(self):
        self.root = Path(self.enterContext(tempfile.TemporaryDirectory())).resolve()
        self.output = self.root / "controller-v1"
        self.result_path = self.output / controller.RESULT_FILE
        self.pins = binding.artifact_bindings()
        self.admission = dict(root=str(self.root), artifacts=self.pins)
        self.running = dict(transport_id=1)
        self.admission_pin = self.write(self.root / "admission-v1.json", self.admission)
        self.running_pin = self.write(self.root / "running-v1.json", self.running)
        self.caller = dict(pid=1234, creation_filetime=5678, executable="C:/Synthetic/python.exe")
        self.tape = command_tape(self.pins)
        self.steps = []
        self.live = Mock(admission=self.admission, caller=self.caller)
        self.live.close.return_value = True
        self.wire = Mock(count=0, clean=True)
        self.wire.shell.side_effect = self.shell
        self.wire.stream.side_effect = self.stream
        self.enterContext(patch.object(owned, "LiveOwnedCrossOwnerDeletionTarget", return_value=self.live))
        self.make_capture = self.enterContext(patch.object(
            owned, "OwnedCrossOwnerDeletionSdkCapture", side_effect=self.open_capture))
        self.enterContext(patch.object(owned, "validate_admission", return_value=self.admission))
        self.enterContext(patch.object(owned, "validate_running", return_value=self.running))
        self.enterContext(patch.object(owned, "validate_session", side_effect=lambda value, _: value))
        self.enterContext(patch.object(owned, "revalidate_inputs"))
        self.enterContext(patch.object(binding, "verify_artifacts"))
        self.replay_clients = self.enterContext(patch.object(
            capture.shared._Verifier, "require_current_clients", side_effect=self.read_client_roster))
        self.capture_lifetime = 1200
        self.unqualified_at = None
        self.live_reply_override = None

    @staticmethod
    def write(path, value):
        env.create_json(path, value)
        return env.binding(path)

    def open_capture(self, directory, seconds, lease):
        self.assertEqual(directory, self.output / "clients")
        self.assertEqual(seconds, 1200)
        self.assertIs(lease, self.live)
        directory.mkdir()
        self.wire.directory = directory
        self.wire.until = time.monotonic() + self.capture_lifetime
        self.wire.session = dict(admission=self.admission_pin, running=self.running_pin,
                                 descriptor=self.running, caller=self.caller, seconds=seconds,
                                 root=str(self.output))
        self.wire.session_binding = self.write(self.output / owned.SESSION_FILE, self.wire.session)
        return self.wire

    def shell(self, argv, label, *, seconds, cap, **_):
        return self.command(argv, label, None, seconds, cap)

    def stream(self, argv, source, label, *, seconds, cap, **_):
        return self.command(argv, label, source, seconds, cap)

    def command(self, argv, label, source, seconds, cap):
        index = self.wire.count + 1
        expected = self.tape[index - 1]
        wanted_label, deadline_ms = RECORDS[index - 1]
        self.steps.append(dict(argv=argv.copy(), stdin=copy.deepcopy(source), label=label))
        self.assertEqual(label, wanted_label)
        self.assertGreater(seconds, 0)
        self.assertLessEqual(seconds, deadline_ms / 1000)
        self.assertLessEqual(max(len(expected["stdout"]), len(expected["stderr"])), cap)
        stem = self.wire.directory / f"command-{index:04d}"
        row = dict(index=index, label=label, effective_deadline_ms=deadline_ms,
                   client_qualified=index != self.unqualified_at, status="completed",
                   returncode=expected["returncode"], operation=dict(argv=argv, stdin=source))
        for channel in ("stdout", "stderr"):
            path = stem.with_suffix(f".{channel}.bin")
            path.write_bytes(expected[channel])
            row[channel] = env.binding(path)
        self.write(stem.with_suffix(".json"), row)
        self.wire.count = index
        if self.live_reply_override and index == self.live_reply_override[0]:
            return self.live_reply_override[1]
        return expected["stdout"]

    def read_client_roster(self, output, count, session_pin, admission):
        self.assertEqual((output, count, session_pin, admission),
                         (self.output, 26, self.wire.session_binding, self.admission))
        return [env.read_json(output / "clients" / f"command-{index:04d}.json")
                for index in range(1, count + 1)]

    def run_controller(self):
        result = controller.run(self.admission_pin, self.running_pin)
        self.assertEqual(env.read_json(self.result_path), result)
        return result

    def verify_result(self, result_pin=None, caller=None):
        return controller.verify_controller_result(
            env.binding(self.result_path) if result_pin is None else result_pin,
            self.admission_pin, self.running_pin, self.caller if caller is None else caller,
        )

    def test_exact_commands_are_captured_and_replayed_before_completed_result(self):
        result = self.run_controller()
        self.assertEqual(self.steps, [
            dict(argv=step["argv"], stdin=step["stdin"], label=label)
            for step, (label, _) in zip(self.tape, RECORDS, strict=True)
        ])
        self.assertEqual(result["outcome"], "completed")
        self.assertIsNone(result["reason"])
        self.assertEqual(result["caller"], self.caller)
        self.assertEqual(result["client_count"], 26)
        self.assertIs(result["observer_handles_closed"], True)
        self.assertEqual(result["journey"], journey.replay(self.tape, self.pins))
        self.assertIs(result["journey"]["runtime_verified"], False)
        self.assertIs(result["journey"]["execution_authorized"], False)
        self.wire.close.assert_called_once_with()
        self.live.close.assert_called_once_with()
        self.replay_clients.assert_called_once()
        self.assertEqual(self.verify_result(), result)
        self.assertEqual(self.replay_clients.call_count, 2)

    def test_occupied_package_refuses_before_staging_either_apk(self):
        self.tape[6]["stdout"] = f"package:{binding.TEST} uid:10002\n".encode()
        result = self.run_controller()
        self.assertEqual((result["outcome"], result["client_count"]), ("refused", 7))
        self.assertEqual(self.steps[-1]["label"], "package-absent")
        self.wire.stream.assert_not_called()
        self.replay_clients.assert_not_called()
        self.live.close.assert_called_once_with()

    def test_bad_staged_hash_refuses_before_install_or_instrumentation(self):
        self.tape[8]["stdout"] = self.tape[8]["stdout"].replace(
            self.pins["product_apk"]["sha256"].encode(), b"0" * 64)
        result = self.run_controller()
        self.assertEqual((result["outcome"], result["client_count"]), ("refused", 9))
        self.assertEqual(self.steps[-1]["label"], "staged-hash")
        self.assertNotIn("install", [step["label"] for step in self.steps])
        self.wire.close.assert_called_once_with()
        self.replay_clients.assert_not_called()

    def test_unqualified_client_stops_before_using_its_apparent_success(self):
        self.unqualified_at = 7
        result = self.run_controller()
        self.assertEqual((result["outcome"], result["client_count"]), ("refused", 7))
        self.wire.stream.assert_not_called()
        self.replay_clients.assert_not_called()

    def test_unbound_live_stdout_stops_before_next_command(self):
        self.tape[6]["stdout"] = b"recorded altered reply"
        self.live_reply_override = (7, b"")
        result = self.run_controller()
        self.assertEqual((result["outcome"], result["client_count"]), ("refused", 7))
        self.wire.stream.assert_not_called()
        self.replay_clients.assert_not_called()

    def test_expired_capture_does_not_dispatch_any_command(self):
        self.capture_lifetime = -1
        result = self.run_controller()
        self.assertEqual((result["outcome"], result["client_count"]), ("refused", 0))
        self.assertEqual(self.steps, [])
        self.wire.close.assert_called_once_with()
        self.live.close.assert_called_once_with()

    def test_failed_capture_close_cannot_be_replayed_as_completed(self):
        self.wire.close.side_effect = OSError("synthetic client close")
        result = self.run_controller()
        self.assertEqual(result["outcome"], "refused")
        self.assertIs(result["observer_handles_closed"], True)
        self.assertEqual(result["client_count"], 26)
        self.live.close.assert_called_once_with()
        with self.assertRaises((core.TargetRefused, env.EnvironmentRefused)):
            self.verify_result()

    def test_unknown_observer_cleanup_cannot_be_replayed_as_completed(self):
        self.live.close.return_value = False
        result = self.run_controller()
        self.assertEqual(result["outcome"], "refused")
        self.assertIs(result["observer_handles_closed"], False)
        self.assertEqual(result["client_count"], 26)
        self.live.close.assert_called_once_with()
        with self.assertRaises((core.TargetRefused, env.EnvironmentRefused)):
            self.verify_result()

    def test_existing_controller_directory_is_preserved(self):
        self.output.mkdir()
        self.result_path.write_bytes(b"prior record")
        with self.assertRaises(FileExistsError):
            controller.run(self.admission_pin, self.running_pin)
        self.assertEqual(self.result_path.read_bytes(), b"prior record")
        self.make_capture.assert_not_called()
        self.live.close.assert_called_once_with()

    def test_replay_requires_expected_caller_and_independent_capture_result(self):
        result = self.run_controller()
        with self.assertRaises((core.TargetRefused, env.EnvironmentRefused)):
            self.verify_result(caller={**self.caller, "pid": 9999})

        recorded = copy.deepcopy(result["journey"])
        recorded["tests"][0]["passed"] = False
        with patch.object(owned, "verify_capture", return_value=recorded) as verify:
            with self.assertRaises((core.TargetRefused, env.EnvironmentRefused)):
                self.verify_result()
            verify.assert_called_once_with(
                self.admission_pin, self.running_pin, self.wire.session_binding, self.caller)

    def test_replay_refuses_a_result_copied_outside_the_owned_output(self):
        result = self.run_controller()
        foreign_pin = self.write(self.root / "copied-result.json", result)
        with self.assertRaises((core.TargetRefused, env.EnvironmentRefused)):
            self.verify_result(foreign_pin)
