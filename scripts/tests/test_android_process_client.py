"""Original platform-independent client failures; never invoke an SDK or native process query.

Copyright 2026 LocalLore contributors. SPDX-License-Identifier: Apache-2.0
"""
import copy
import hashlib
import json
from pathlib import Path
import shlex
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import patch

from benchmarks import android_process_client as client


class AndroidProcessClientTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name).resolve()
        self.adb = self.root / "adb.exe"
        self.powershell = self.root / "powershell.exe"
        self.adb.write_bytes(b"synthetic SDK binary; never executed")
        self.powershell.write_bytes(b"synthetic PowerShell binary; never executed")
        self.server = {"pid": 41, "creation_filetime": 123456789023, "executable": str(self.adb)}
        self.launcher = {"pid": 42, "creation_filetime": 123456789027, "executable": str(self.root / "emulator.exe")}
        self.rows = [{"address": "::1", "port": 5037, "pid": 41}, {"address": "127.0.0.1", "port": 5037, "pid": 41}]
        self.pin = dict(self.server, listeners=copy.deepcopy(sorted(self.rows, key=lambda x: x["address"])),
                        adb_sha256=hashlib.sha256(self.adb.read_bytes()).hexdigest())
        self.now = 100.0
        self.payload = b"binary\x00\x1a\xff\r\n\n"
        self.sdk_result = None
        self.sdk_after = None
        self.observation = None
        self.native = self.enter_context(patch.object(client.environment, "process_identity", side_effect=self.identity))
        self.runner = self.enter_context(patch.object(client.host, "run_process", side_effect=self.fake_run))
        self.enter_context(patch.object(client.time, "monotonic", side_effect=lambda: self.now))

    # addCleanup rather than TestCase.enterContext keeps the tests portable across Python minors.
    def enter_context(self, context):
        result = context.__enter__()
        self.addCleanup(context.__exit__, None, None, None)
        return result

    def identity(self, pid):
        return copy.deepcopy(self.launcher if pid == self.launcher["pid"] else self.server)

    def completed(self, raw):
        return client.host.ProcessResult("completed", 1, raw, 0, 0, True)

    def fake_run(self, command, **_):
        if command[0] == str(self.powershell):
            raw = self.observation if self.observation is not None else json.dumps({"pid": 41, "listeners": self.rows}).encode()
            return self.completed(raw)
        if self.sdk_after is not None:
            self.sdk_after()
        return self.sdk_result if self.sdk_result is not None else self.completed(self.payload)

    def owner(self, **kwargs):
        return client.SdkCapture(self.root / "clients", 100, self.adb, self.powershell, self.pin, **kwargs)

    def records(self, owner):
        return [json.loads((owner.directory / ("command-%04d.json" % n)).read_bytes()) for n in range(1, owner.count + 1)]

    def assert_stopped(self, owner):
        calls = self.runner.call_count
        with self.assertRaises(client.ClientRefused):
            owner.capture(client._server_command(self.powershell), "later")
        self.assertFalse(owner.clean)
        self.assertEqual(calls, self.runner.call_count)

    def test_observe_server_uses_kernel_filetime_and_sorted_loopback_without_adb(self):
        value = client.observe_server(self.adb, self.powershell)
        self.assertEqual(self.pin, value)
        self.assertEqual(123456789023, value["creation_filetime"])
        self.assertEqual(1, self.runner.call_count)
        command = self.runner.call_args.args[0]
        self.assertEqual(str(self.powershell), command[0])
        self.assertEqual(["-NoLogo", "-NoProfile", "-NonInteractive", "-Command"], command[1:5])
        self.assertIn("Get-NetTCPConnection -LocalPort 5037 -State Listen", command[5])
        self.assertNotIn("Cim", command[5])
        self.assertEqual({"request": b"", "deadline": 15, "max_output": 16384}, self.runner.call_args.kwargs)
        self.assertEqual([41, 41], [call.args[0] for call in self.native.call_args_list])

    def test_observation_rejects_unknown_duplicate_nonloopback_and_coerced_rows(self):
        valid = {"pid": 41, "listeners": self.rows}
        variants = [b'{"pid":41,"pid":41,"listeners":[]}',
                    b'{"pid":41,"listeners":[{"address":"127.0.0.1","port":5037,"port":5037,"pid":41}]}',
                    b'{"pid":NaN,"listeners":[]}', b'\xff',
                    json.dumps(dict(valid, extra=True)).encode(),
                    json.dumps(dict(valid, pid=True)).encode()]
        for change in ({"address": "0.0.0.0"}, {"address": "127.0.0.2"}, {"port": 5038},
                       {"port": True}, {"pid": 42}, {"pid": True}, {"extra": "CANARY"}):
            variants.append(json.dumps({"pid": 41, "listeners": [dict(self.rows[0], **change)]}).encode())
        variants.append(json.dumps({"pid": 41, "listeners": [self.rows[0], self.rows[0]]}).encode())
        for raw in variants:
            with self.subTest(raw=raw):
                self.observation = raw
                with self.assertRaises(client.ClientRefused) as caught:
                    client.observe_server(self.adb, self.powershell)
                self.assertEqual("server_observation", str(caught.exception))

    def test_observation_refuses_pid_reuse_wrong_image_and_native_bool(self):
        for identities in ([self.server, dict(self.server, creation_filetime=123456789024)],
                           [dict(self.server, executable=str(self.powershell))],
                           [dict(self.server, pid=True)], [dict(self.server, creation_filetime=True)]):
            with self.subTest(identities=identities):
                self.native.side_effect = copy.deepcopy(identities)
                with self.assertRaises(client.ClientRefused):
                    client.observe_server(self.adb, self.powershell)

    def test_observation_refuses_changed_adb_bytes_during_client(self):
        def changed(command, **kwargs):
            self.adb.write_bytes(b"changed")
            return self.fake_run(command, **kwargs)
        self.runner.side_effect = changed
        with self.assertRaises(client.ClientRefused):
            client.observe_server(self.adb, self.powershell)

    def test_windows_path_descriptor_ctime_difference_preserves_identity_and_hash_guards(self):
        original = client.os.fstat
        def descriptor(fd):
            value = original(fd)
            return SimpleNamespace(st_dev=value.st_dev, st_ino=value.st_ino, st_size=value.st_size,
                                   st_mtime_ns=value.st_mtime_ns, st_ctime_ns=value.st_ctime_ns + 100)
        with patch.object(client.os, "fstat", side_effect=descriptor):
            self.assertEqual(hashlib.sha256(self.adb.read_bytes()).hexdigest(), client._file_pin(self.adb)[1])

    def test_binary_sdk_capture_persists_all_three_clients_before_return(self):
        owner = self.owner()
        owner.target = {"transport_id": 7, "serial": "synthetic-only"}
        self.assertEqual(self.payload, owner.adb(["exec-out", "fixed"], "binary"))
        self.assertEqual(3, owner.count)
        records = self.records(owner)
        self.assertEqual(["adb-server", "binary", "adb-server"], [r["label"] for r in records])
        self.assertEqual(self.payload, (owner.directory / "command-0002.stdout.bin").read_bytes())
        self.assertEqual(hashlib.sha256(self.payload).hexdigest(), records[1]["stdout_sha256"])
        self.assertEqual(len(self.payload), records[1]["stdout_bytes"])
        self.assertTrue(owner.clean)
        self.assertEqual([str(self.adb), "-H", "127.0.0.1", "-P", "5037", "-t", "7", "exec-out", "fixed"],
                         self.runner.call_args_list[1].args[0])
        expected = {"version", "index", "label", "status", "returncode", "cleanup_complete", "stdout_bytes", "stdout_sha256", "stderr_bytes"}
        self.assertTrue(all(set(r) == expected for r in records))

    def test_fixed_discovery_is_pinned_and_does_not_choose_target(self):
        owner = self.owner()
        command = [str(self.adb), "-H", "127.0.0.1", "-P", "5037", "devices", "-l"]
        self.assertEqual(self.payload, owner.capture(command, "devices"))
        self.assertIsNone(owner.target)
        self.assertEqual(3, owner.count)

    def test_shell_joins_literal_arguments_without_host_shell_interpolation(self):
        owner = self.owner()
        owner.target = {"transport_id": 7}
        words = ["printf", "%s", "single ' quote; $literal\n\"double\""]
        owner.shell(words, "literal")
        self.assertEqual(["shell", shlex.join(words)], self.runner.call_args_list[1].args[0][-2:])

    def test_no_device_dispatch_without_transport_and_failure_is_sticky(self):
        owner = self.owner()
        with self.assertRaises(client.ClientRefused):
            owner.adb(["get-state"], "state")
        self.assertEqual(0, self.runner.call_count)
        owner.target = {"transport_id": 7}
        self.assert_stopped(owner)
        owner.clean = True
        self.assert_stopped(owner)  # A public flag cannot revive the private failed owner.

    def test_constructor_keeps_initial_pin_without_adoption_or_mutable_alias(self):
        owner = self.owner()
        self.pin["creation_filetime"] += 1
        self.pin["listeners"][0]["address"] = "0.0.0.0"
        owner.check_server()
        self.assertTrue(owner.clean)
        self.server["creation_filetime"] += 1
        with self.assertRaises(client.ClientRefused):
            owner.check_server()
        self.assert_stopped(owner)

    def test_server_change_before_sdk_only_records_observation(self):
        owner = self.owner()
        owner.target = {"transport_id": 7}
        self.server["creation_filetime"] += 1
        with self.assertRaises(client.ClientRefused):
            owner.adb(["get-state"], "state")
        self.assertEqual(1, owner.count)
        self.assertEqual([str(self.powershell)], [call.args[0][0] for call in self.runner.call_args_list])
        self.assert_stopped(owner)

    def test_changed_server_after_sdk_suppresses_output_and_retains_all_records(self):
        owner = self.owner()
        owner.target = {"transport_id": 7}
        self.sdk_after = lambda: self.server.update(creation_filetime=self.server["creation_filetime"] + 1)
        with self.assertRaises(client.ClientRefused):
            owner.adb(["get-state"], "state")
        self.assertEqual(3, owner.count)
        self.assertEqual(self.payload, (owner.directory / "command-0002.stdout.bin").read_bytes())
        self.assertEqual(3, len(self.records(owner)))
        self.assert_stopped(owner)

    def test_each_client_checks_optional_launcher_before_and_after(self):
        owner = self.owner(launcher_pin=self.launcher)
        original = self.fake_run
        def changed(command, **kwargs):
            result = original(command, **kwargs)
            self.launcher["creation_filetime"] += 1
            return result
        self.runner.side_effect = changed
        with self.assertRaises(client.ClientRefused):
            owner.check_server()
        self.assertEqual(1, owner.count)
        self.assert_stopped(owner)

    def test_pin_binary_change_is_refused_before_any_new_process(self):
        owner = self.owner()
        self.powershell.write_bytes(b"changed PowerShell")
        with self.assertRaises(client.ClientRefused):
            owner.check_server()
        self.assertEqual(0, self.runner.call_count)
        self.assert_stopped(owner)

    def test_bad_completion_retains_result_then_permanently_refuses(self):
        for changes in ({"status": "timeout"}, {"status": "output_limit"}, {"status": "cancelled"},
                        {"status": "spawn_failed"}, {"status": "cleanup_failed"},
                        {"returncode": 1}, {"stderr_bytes": 1}, {"cleanup_complete": False}):
            with self.subTest(changes=changes):
                directory = self.root / ("bad-%d" % len(list(self.root.glob("bad-*"))))
                owner = client.SdkCapture(directory, 100, self.adb, self.powershell, self.pin)
                owner.target = {"transport_id": 7}
                self.sdk_result = self.completed(self.payload)
                for key, value in changes.items():
                    setattr(self.sdk_result, key, value)
                with self.assertRaises(client.ClientRefused):
                    owner.adb(["get-state"], "state")
                self.assertEqual(2, owner.count)
                record = self.records(owner)[1]
                self.assertEqual(changes.get("status", "completed"), record["status"])
                self.assert_stopped(owner)
        self.sdk_result = None

    def test_malformed_owner_result_and_runner_exception_have_closed_failure_records(self):
        variants = [self.completed(self.payload) for _ in range(4)]
        variants[0].returncode = True
        variants[1].stdout = "CANARY"
        variants[2].status = "CANARY"
        variants[3].cleanup_complete = 1
        for index, value in enumerate(variants + [OSError("CANARY private path")]):
            with self.subTest(index=index):
                owner = client.SdkCapture(self.root / ("malformed-%d" % index), 100, self.adb, self.powershell, self.pin)
                self.runner.side_effect = value if isinstance(value, Exception) else lambda *a, **k: value
                with self.assertRaises(client.ClientRefused) as caught:
                    owner.capture(client._server_command(self.powershell), "observation")
                self.assertEqual(1, owner.count)
                record = self.records(owner)[0]
                self.assertEqual("spawn_failed", record["status"])
                self.assertIs(record["cleanup_complete"], False)
                self.assertNotIn("CANARY", json.dumps(record) + str(caught.exception))
                self.assert_stopped(owner)

    def test_metadata_persistence_failure_never_returns_payload_or_dispatches_again(self):
        owner = self.owner()
        with patch.object(client.environment, "create_json", side_effect=OSError("CANARY")):
            with self.assertRaises(client.ClientRefused) as caught:
                owner.capture(client._server_command(self.powershell), "observation")
        self.assertNotIn("CANARY", str(caught.exception))
        self.assertEqual(1, owner.count)
        self.assertTrue((owner.directory / "command-0001.stdout.bin").is_file())
        self.assert_stopped(owner)

    def test_fsync_failure_is_sticky_and_never_creates_success_metadata(self):
        owner = self.owner()
        with patch.object(client.os, "fsync", side_effect=OSError("CANARY")):
            with self.assertRaises(client.ClientRefused):
                owner.capture(client._server_command(self.powershell), "observation")
        self.assertFalse((owner.directory / "command-0001.json").exists())
        self.assert_stopped(owner)

    def test_existing_capture_is_never_overwritten_and_blocks_next_command(self):
        owner = self.owner()
        path = owner.directory / "command-0001.stdout.bin"
        path.write_bytes(b"existing synthetic evidence")
        with self.assertRaises(client.ClientRefused):
            owner.capture(client._server_command(self.powershell), "observation")
        self.assertEqual(b"existing synthetic evidence", path.read_bytes())
        self.assert_stopped(owner)

    def test_remaining_monotonic_deadline_clamps_the_owned_process(self):
        owner = self.owner()
        self.now = 198.75
        owner.capture(client._server_command(self.powershell), "observation", seconds=15)
        self.assertEqual(1.25, self.runner.call_args.kwargs["deadline"])
        self.assertEqual(b"", self.runner.call_args.kwargs["request"])

    def test_expired_owner_does_not_launch_and_late_completion_is_not_accepted(self):
        owner = self.owner()
        self.now = 200
        with self.assertRaises(client.ClientRefused):
            owner.check_server()
        self.assertEqual(0, self.runner.call_count)
        self.assert_stopped(owner)
        other = client.SdkCapture(self.root / "late", 10, self.adb, self.powershell, self.pin)
        def late(command, **kwargs):
            value = self.fake_run(command, **kwargs)
            self.now = 211
            return value
        self.runner.side_effect = late
        with self.assertRaises(client.ClientRefused):
            other.capture(client._server_command(self.powershell), "observation")
        self.assertEqual(1, len(self.records(other)))
        self.assert_stopped(other)

    def test_invalid_budgets_labels_targets_and_commands_fail_without_dispatch(self):
        variants = [(client._server_command(self.powershell), "bad\nCANARY", 15, 10),
                    (client._server_command(self.powershell), "valid", True, 10),
                    (client._server_command(self.powershell), "valid", float("nan"), 10),
                    (client._server_command(self.powershell), "valid", 181, 10),
                    (client._server_command(self.powershell), "valid", 15, True),
                    (client._server_command(self.powershell), "valid", 15, 262145),
                    ([str(self.powershell), "-Command", "CANARY"], "valid", 15, 10),
                    ([str(self.adb), "kill-server"], "valid", 15, 10),
                    ([str(self.adb), "-H", "other", "-P", "5037", "devices", "-l"], "valid", 15, 10)]
        for index, (command, label, seconds, cap) in enumerate(variants):
            owner = client.SdkCapture(self.root / ("guard-%d" % index), 100, self.adb, self.powershell, self.pin)
            before = self.runner.call_count
            with self.assertRaises(client.ClientRefused):
                owner.capture(command, label, seconds, cap)
            self.assertEqual(before, self.runner.call_count)
            self.assert_stopped(owner)

    def test_selected_daemon_commands_and_transport_retargeting_are_rejected(self):
        for index, operation in enumerate((["kill-server"], ["start-server"], ["server"], ["fork-server"],
                                           ["connect", "other"], ["disconnect"], ["pair", "other"], ["mdns"],
                                           ["reconnect"], ["track-devices"], ["-H", "other"])):
            owner = client.SdkCapture(self.root / ("daemon-%d" % index), 100, self.adb, self.powershell, self.pin)
            owner.target = {"transport_id": 7}
            before = self.runner.call_count
            with self.assertRaises(client.ClientRefused):
                owner.adb(operation, "daemon")
            self.assertEqual(before, self.runner.call_count)
            self.assert_stopped(owner)
        owner = self.owner()
        owner.target = {"transport_id": 7}
        owner.adb(["get-state"], "state")
        calls = self.runner.call_count
        owner.target = {"transport_id": 8}
        with self.assertRaises(client.ClientRefused):
            owner.adb(["get-state"], "retarget")
        self.assertEqual(calls, self.runner.call_count)
        self.assert_stopped(owner)

    def test_replaced_evidence_directory_refuses_before_process_launch(self):
        owner = self.owner()
        owner.directory.rename(self.root / "preserved-clients")
        owner.directory.mkdir()
        with self.assertRaises(client.ClientRefused):
            owner.check_server()
        self.assertEqual(0, self.runner.call_count)
        self.assert_stopped(owner)

    def test_existing_directory_and_incorrect_initial_file_pin_are_not_adopted(self):
        existing = self.root / "existing"
        existing.mkdir()
        with self.assertRaises(client.ClientRefused):
            client.SdkCapture(existing, 100, self.adb, self.powershell, self.pin)
        wrong = dict(self.pin, adb_sha256="0" * 64)
        with self.assertRaises(client.ClientRefused):
            client.SdkCapture(self.root / "wrong", 100, self.adb, self.powershell, wrong)
        self.assertFalse((self.root / "wrong").exists())
        self.assertEqual(0, self.runner.call_count)


if __name__ == "__main__":
    unittest.main()
