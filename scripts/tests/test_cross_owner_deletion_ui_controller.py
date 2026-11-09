"""Host checks for the fixed SDK24 controller on an already owned target.

Copyright 2026 LocalLore contributors. SPDX-License-Identifier: Apache-2.0
"""
import copy
from pathlib import Path
import tempfile
import time
import unittest
from unittest.mock import Mock, call, patch

from benchmarks import cross_owner_deletion_ui_binding as binding
from benchmarks import cross_owner_deletion_ui_boot as boot
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
        self.boot_output = self.output / "boot-readiness-v1"
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
        self.boot_wire = Mock(count=0, clean=True)
        self.boot_wire.shell.side_effect = self.probe
        self.boot_replies = [b"1\n"]
        self.boot_stderr = b""
        self.boot_qualified = True
        self.boot_capture_lifetime = 120
        self.journey_start_offset = 0
        self.probes = []
        self.sleep = self.enterContext(patch.object(boot.time, "sleep"))
        self.enterContext(patch.object(owned, "LiveOwnedCrossOwnerDeletionTarget", return_value=self.live))
        self.make_capture = self.enterContext(patch.object(
            owned, "OwnedCrossOwnerDeletionSdkCapture", side_effect=self.open_capture))
        self.enterContext(patch.object(owned, "validate_admission", return_value=self.admission))
        self.enterContext(patch.object(owned, "validate_running", return_value=self.running))
        self.enterContext(patch.object(owned, "validate_session", side_effect=lambda value, _: value))
        self.enterContext(patch.object(owned, "revalidate_inputs"))
        self.enterContext(patch.object(binding, "verify_artifacts"))
        self.replay_clients = Mock(side_effect=self.read_journey_roster)
        self.replay_readiness = Mock(side_effect=self.read_readiness_roster)
        self.enterContext(patch.object(
            capture.shared._Verifier, "require_current_clients", side_effect=self.read_client_roster))
        self.capture_lifetime = 1200
        self.unqualified_at = None
        self.live_reply_override = None

    @staticmethod
    def write(path, value):
        env.create_json(path, value)
        return env.binding(path)

    def open_capture(self, directory, seconds, lease):
        self.assertIs(lease, self.live)
        started = time.time()
        if directory == self.boot_output / "clients":
            self.assertEqual(seconds, 120)
            wire = self.boot_wire
            lifetime = self.boot_capture_lifetime
        else:
            self.assertEqual(directory, self.output / "clients")
            self.assertEqual(seconds, 1200)
            self.boot_wire.close.assert_called_once_with()
            self.replay_readiness.assert_called_once()
            wire = self.wire
            lifetime = self.capture_lifetime
            started += self.journey_start_offset

        directory.mkdir()
        wire.directory = directory
        wire.until = time.monotonic() + lifetime
        wire.session = dict(admission=self.admission_pin, running=self.running_pin,
                            descriptor=self.running, caller=self.caller, seconds=seconds,
                            root=str(directory.parent), started_epoch=started,
                            deadline_epoch=started + seconds)
        wire.session_binding = self.write(directory.parent / owned.SESSION_FILE, wire.session)
        return wire

    def probe(self, argv, label, *, seconds, cap, **_):
        self.assertEqual(argv, ["getprop", "sys.boot_completed"])
        self.assertEqual(label, "boot-ready")
        self.assertGreater(seconds, 0)
        self.assertLessEqual(seconds, 15)
        self.assertEqual(cap, 16)
        index = self.boot_wire.count + 1
        self.probes.append(argv.copy())
        stdout = self.boot_replies[index - 1]
        self.record_command(self.boot_wire, index, label, argv, None, stdout,
                            self.boot_stderr, 0, 15_000, self.boot_qualified)
        return stdout

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
        self.record_command(self.wire, index, label, argv, source, expected["stdout"],
                            expected["stderr"], expected["returncode"], deadline_ms,
                            index != self.unqualified_at)
        if self.live_reply_override and index == self.live_reply_override[0]:
            return self.live_reply_override[1]
        return expected["stdout"]

    def record_command(self, wire, index, label, argv, source, stdout, stderr,
                       returncode, deadline_ms, qualified):
        stem = wire.directory / f"command-{index:04d}"
        row = dict(index=index, label=label, effective_deadline_ms=deadline_ms,
                   client_qualified=qualified, status="completed", returncode=returncode,
                   operation=dict(argv=argv, stdin=source))
        for channel, data in (("stdout", stdout), ("stderr", stderr)):
            path = stem.with_suffix(f".{channel}.bin")
            path.write_bytes(data)
            row[channel] = env.binding(path)
        self.write(stem.with_suffix(".json"), row)
        wire.count = index

    @staticmethod
    def read_rows(output, count):
        return [env.read_json(output / "clients" / f"command-{index:04d}.json")
                for index in range(1, count + 1)]

    def read_client_roster(self, output, count, session_pin, admission):
        replay = self.replay_readiness if output == self.boot_output else self.replay_clients
        return replay(output, count, session_pin, admission)

    def read_readiness_roster(self, output, count, session_pin, admission):
        self.assertEqual((output, count, session_pin, admission),
                         (self.boot_output, self.boot_wire.count,
                          self.boot_wire.session_binding, self.admission))
        return self.read_rows(output, count)

    def read_journey_roster(self, output, count, session_pin, admission):
        self.assertEqual((output, count, session_pin, admission),
                         (self.output, 26, self.wire.session_binding, self.admission))
        return self.read_rows(output, count)

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
        self.assertEqual(result["version"], 2)
        self.assertEqual(result["readiness"]["session"], self.boot_wire.session_binding)
        self.assertEqual(result["readiness"]["client_count"], 1)
        self.assertLessEqual(result["readiness"]["completed_epoch"], self.wire.session["started_epoch"])
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
        self.assertEqual(self.replay_readiness.call_count, 2)

    def assert_readiness_refused(self, reason, count):
        result = self.run_controller()
        self.assertEqual((result["outcome"], result["reason"], result["client_count"]),
                         ("refused", reason, 0))
        self.assertIsNone(result["readiness"])
        self.assertIsNone(result["journey"])
        self.assertEqual(len(self.probes), count)
        self.assertEqual(self.steps, [])
        self.make_capture.assert_called_once_with(self.boot_output / "clients", 120, self.live)
        self.boot_wire.close.assert_called_once_with()
        self.live.close.assert_called_once_with()
        self.assertFalse((self.output / "clients").exists())

    def test_readiness_polls_empty_and_zero_before_opening_fixed_journey(self):
        self.boot_replies = [b"\n", b"0\n", b"1\n"]
        result = self.run_controller()
        self.assertEqual(result["outcome"], "completed")
        self.assertEqual(result["readiness"]["client_count"], 3)
        self.assertEqual(self.probes, [["getprop", "sys.boot_completed"]] * 3)
        self.assertEqual(self.sleep.call_args_list, [call(5), call(5)])
        self.assertEqual(len(self.read_rows(self.boot_output, 3)), 3)
        self.assertEqual(len(self.read_rows(self.output, 26)), 26)
        self.assertEqual(self.verify_result(), result)

    def test_expired_readiness_capture_dispatches_no_commands(self):
        self.boot_capture_lifetime = -1
        self.assert_readiness_refused("deadline", 0)

    def test_readiness_poll_exhaustion_keeps_the_partial_capture(self):
        self.boot_replies = [b"0\n"] * 24
        self.assert_readiness_refused("deadline", 24)
        self.assertEqual(len(self.read_rows(self.boot_output, 24)), 24)
        self.assertEqual(self.sleep.call_count, 23)

    def test_malformed_ready_reply_cannot_dispatch_the_journey(self):
        self.boot_replies = [b"01\n"]
        self.assert_readiness_refused("checks_failed", 1)

    def test_readiness_stderr_cannot_dispatch_the_journey(self):
        self.boot_stderr = b"unexpected"
        self.assert_readiness_refused("checks_failed", 1)

    def test_unqualified_ready_reply_cannot_dispatch_the_journey(self):
        self.boot_qualified = False
        self.assert_readiness_refused("checks_failed", 1)

    def test_failed_readiness_close_cannot_dispatch_the_journey(self):
        self.boot_wire.close.side_effect = OSError("synthetic readiness close")
        self.assert_readiness_refused("resource_uncertain", 1)

    def test_journey_session_cannot_predate_readiness_completion(self):
        self.journey_start_offset = -5
        result = self.run_controller()
        self.assertEqual((result["outcome"], result["reason"], result["client_count"]),
                         ("refused", "checks_failed", 0))
        self.assertEqual(self.steps, [])
        self.wire.close.assert_called_once_with()

    def test_transport_ready_without_android_boot_refuses_before_any_writes(self):
        self.tape[0]["stdout"] = b""
        result = self.run_controller()
        self.assertEqual((result["outcome"], result["client_count"]), ("refused", 1))
        self.assertEqual([step["label"] for step in self.steps], ["boot"])
        self.wire.stream.assert_not_called()
        self.replay_clients.assert_not_called()
        self.live.close.assert_called_once_with()

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

    def test_replay_refuses_readiness_from_a_foreign_caller(self):
        result = self.run_controller()
        session_path = self.boot_output / owned.SESSION_FILE
        session = env.read_json(session_path)
        session["caller"] = {**self.caller, "pid": 9999}
        session_path.write_bytes(env.encoded(session))
        result["readiness"]["session"] = env.binding(session_path)
        self.result_path.write_bytes(env.encoded(result))
        with self.assertRaises(core.TargetRefused):
            self.verify_result()

    def test_replay_refuses_readiness_session_outside_its_owned_output(self):
        result = self.run_controller()
        foreign_pin = self.write(self.root / owned.SESSION_FILE, self.boot_wire.session)
        result["readiness"]["session"] = foreign_pin
        self.result_path.write_bytes(env.encoded(result))
        with self.assertRaises(core.TargetRefused):
            self.verify_result()

    def test_replay_refuses_readiness_completion_after_journey_start(self):
        result = self.run_controller()
        result["readiness"]["completed_epoch"] = self.wire.session["started_epoch"] + 1
        self.result_path.write_bytes(env.encoded(result))
        with self.assertRaises(core.TargetRefused):
            self.verify_result()

    def test_replay_rechecks_the_terminal_ready_reply(self):
        result = self.run_controller()
        stdout = self.boot_output / "clients" / "command-0001.stdout.bin"
        stdout.write_bytes(b"0\n")
        row_path = stdout.with_name("command-0001.json")
        row = env.read_json(row_path)
        row["stdout"] = env.binding(stdout)
        row_path.write_bytes(env.encoded(row))
        with self.assertRaises(core.TargetRefused):
            self.verify_result()

    def test_replay_refuses_controller_result_without_readiness(self):
        result = self.run_controller()
        del result["readiness"]
        result["version"] = 1
        self.result_path.write_bytes(env.encoded(result))
        with self.assertRaises(core.TargetRefused):
            self.verify_result()

    def test_replay_refuses_a_result_copied_outside_the_owned_output(self):
        result = self.run_controller()
        foreign_pin = self.write(self.root / "copied-result.json", result)
        with self.assertRaises((core.TargetRefused, env.EnvironmentRefused)):
            self.verify_result(foreign_pin)
