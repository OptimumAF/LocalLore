"""Independent synthetic Android-controller regressions; no ADB/model/device use."""
import json
import base64
import contextlib
import io
import shlex
import subprocess
import tempfile
import threading
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock, patch

import android_runtime_spike as spike


CANARY = "SYNTHETIC-PRIVATE-ANDROID-REVIEW-731"


def request(role):
    return dict(version=1, role=role, prompt="Synthetic Lantern Quay fixture", schema=None,
                max_tokens=350 if role == "director" else 220, context_tokens=4096, threads=4)


def worker_result(**changes):
    value = dict(version=1, status="completed", text=CANARY, error=None,
                 load_ms=1.0, generation_ms=2.0, input_tokens=16, output_tokens=2,
                 schema_enforced=True, thinking_disabled=True, template_applied=True)
    value.update(changes)
    return json.dumps(value).encode()


def remote(**changes):
    value = dict(status="completed", elapsed_ms=1, cleanup_complete=True,
                 stdout=worker_result(), returncode=0, adb_cleanup_complete=True,
                 directory_cleanup_complete=True)
    value.update(changes)
    return SimpleNamespace(**value)


def oracle_reply(worker, binary, operation, case, data=b""):
    if operation == "fixture":
        return dict(version=1, case="gift", preflight_error=None, revision=0,
                    director=request("director"))
    if operation == "validate":
        return dict(status="accepted", narrator=request("narrator"))
    return dict(status="committed", revision=1, events=1, exact_retry_unchanged=True,
                recipient_observations=1, absent_observations=0)


class AggregateOwnershipTests(unittest.TestCase):
    def test_incomplete_remote_or_adb_cleanup_and_nonzero_exit_cannot_commit(self):
        for changed in (dict(cleanup_complete=False), dict(adb_cleanup_complete=False),
                        dict(returncode=23)):
            with self.subTest(changed=changed):
                worker = SimpleNamespace(run=lambda *args, **kwargs: remote(**changed))
                with patch.object(spike, "oracle", side_effect=oracle_reply):
                    report = spike.experiment(None, worker, "worker", "oracle", "model")
                self.assertNotEqual(report["status"], "committed")
                self.assertEqual(report["attempted_roles"], 1)
                self.assertEqual(len(report["roles"]), 1)
                self.assertNotIn(CANARY, json.dumps(report))

    def test_role_failure_keeps_attempt_instead_of_escaping_to_setup_failure(self):
        def failed(*args, **kwargs):
            raise spike.Failure(CANARY)
        worker = SimpleNamespace(run=failed)
        with patch.object(spike, "oracle", side_effect=oracle_reply):
            report = spike.experiment(None, worker, "worker", "oracle", "model")
        self.assertEqual(report["attempted_roles"], 1)
        self.assertEqual(len(report["roles"]), 1)
        self.assertNotIn(CANARY, json.dumps(report))

    def test_unknown_or_malformed_preflight_error_never_calls_model(self):
        for error in (CANARY, [], {}, True):
            with self.subTest(error=error):
                fixture = oracle_reply(None, None, "fixture", "gift")
                fixture["preflight_error"] = error
                worker = SimpleNamespace(run=Mock())
                with patch.object(spike, "oracle", return_value=fixture):
                    report = spike.experiment(None, worker, "worker", "oracle", "model")
                self.assertEqual(report["status"], "oracle_failed")
                self.assertEqual(report["attempted_roles"], 0)
                self.assertNotIn(CANARY, json.dumps(report))
                worker.run.assert_not_called()

    def test_unknown_worker_error_and_false_template_or_thinking_flags_fail_closed(self):
        for changed in (dict(status="error", text="", error=CANARY),
                        dict(thinking_disabled=False), dict(template_applied=False)):
            with self.subTest(changed=changed):
                worker = SimpleNamespace(run=lambda *args, **kwargs: remote(stdout=worker_result(**changed)))
                with patch.object(spike, "oracle", side_effect=oracle_reply):
                    report = spike.experiment(None, worker, "worker", "oracle", "model")
                self.assertNotEqual(report["status"], "committed")
                self.assertEqual(report["attempted_roles"], 1)
                self.assertNotIn(CANARY, json.dumps(report))

    def test_commit_aggregate_fields_cannot_copy_private_strings_or_boolean_counts(self):
        for key, value in (("events", CANARY), ("revision", True),
                           ("recipient_observations", -1), ("exact_retry_unchanged", 1)):
            with self.subTest(key=key):
                def corrupt(worker, binary, operation, case, data=b""):
                    reply = oracle_reply(worker, binary, operation, case, data)
                    if operation == "commit":
                        reply[key] = value
                    return reply
                worker = SimpleNamespace(run=lambda *args, **kwargs: remote())
                with patch.object(spike, "oracle", side_effect=corrupt):
                    report = spike.experiment(None, worker, "worker", "oracle", "model")
                self.assertEqual(report["status"], "oracle_failed")
                self.assertEqual(report["attempted_roles"], 2)
                self.assertNotIn(CANARY, json.dumps(report))

    def test_narrator_receives_only_accepted_narrator_context(self):
        calls = []
        def run(binary, args, data, **kwargs):
            calls.append(json.loads(data))
            return remote()
        def isolated(worker, binary, operation, case, data=b""):
            reply = oracle_reply(worker, binary, operation, case, data)
            if operation == "fixture":
                reply["director"]["prompt"] = CANARY
            return reply
        with patch.object(spike, "oracle", side_effect=isolated):
            report = spike.experiment(None, SimpleNamespace(run=run), "worker", "oracle", "model")
        self.assertEqual(report["status"], "committed")
        self.assertEqual(len(calls), 2)
        self.assertEqual(calls[0]["prompt"], CANARY)
        self.assertNotIn(CANARY, json.dumps(calls[1]))
        self.assertNotIn(CANARY, json.dumps(report))


class ParserOwnershipTests(unittest.TestCase):
    def test_raw_worker_text_is_never_part_of_remote_result_repr(self):
        result = spike.RemoteResult("failed", 1, False, CANARY.encode(), 23, True)
        self.assertNotIn(CANARY, repr(result))

    def test_proc_start_time_parsing_handles_spaces_and_closing_parentheses(self):
        fields = ["S"] + ["0"] * 18 + ["731"] + ["0"] * 8
        raw = ("123 (worker ) with spaces)) " + " ".join(fields) + "\n").encode()
        self.assertEqual(spike.parse_stat(raw, 123), 731)
        for bad in (b"", b"\xff", raw.replace(b"123 (", b"124 (", 1),
                    b"123 (worker) S 1", raw.replace(b"731", b"-1")):
            with self.subTest(raw=bad):
                self.assertIsNone(spike.parse_stat(bad, 123))

    def test_done_record_is_exact_bounded_and_never_contains_private_error_text(self):
        self.assertEqual(spike.parse_done(b"completed 0\n"), ("completed", 0))
        self.assertEqual(spike.parse_done(b"cancelled 143\n"), ("cancelled", 143))
        for raw in (b"", b"completed 256\n", b"completed -1\n", b"completed 0\nextra",
                    b"completed 0", CANARY.encode() + b" 1\n", b"failed true\n"):
            with self.subTest(raw=raw):
                self.assertIsNone(spike.parse_done(raw))

    def test_deep_or_duplicate_oracle_json_is_rejected_without_exception(self):
        for raw in (b"[" * 2000 + b"]" * 2000,
                    b'{"status":"accepted","status":"rejected"}', b"[]", b"\xff"):
            with self.subTest(raw=raw[:50]):
                worker = SimpleNamespace(run=lambda *args, **kwargs: remote(stdout=raw))
                self.assertIsNone(spike.oracle(worker, "oracle", "fixture", "gift"))

    def test_adb_shell_quotes_every_argument_including_shell_syntax(self):
        device = spike.Device("adb", "synthetic-emulator")
        args = ["/fixed path/worker", "$(touch private)", "a'b", "a;echo private", ""]
        with patch.object(device, "raw", return_value=remote(stdout=b"")) as raw:
            device.shell(*args)
        self.assertEqual(shlex.split(raw.call_args.args[0][1]), args)


class ImmediateDevice:
    """A fake completed supervisor whose final owned-directory removal fails."""
    def __init__(self):
        self.ready = threading.Event()
        self.command = None
        self.identities = 0
        self.scripts = []
        self.shells = []

    def shell(self, *args, **kwargs):
        self.shells.append(args)
        if args[0] == "rmdir":
            raise spike.Failure(CANARY)
        return b""

    def put_bytes(self, data, path):
        pass

    def raw(self, args, **kwargs):
        self.command = shlex.split(args[1])[1:]
        self.ready.set()
        return SimpleNamespace(status="completed", stdout=b"synthetic", returncode=0,
                               cleanup_complete=True)

    def read_optional(self, path):
        self.ready.wait(1)
        return b"123\n" if path.endswith("/owner") else b"completed 0\n"

    def identity(self, pid):
        self.identities += 1
        return (17, [part.encode() for part in self.command]) if self.identities == 1 else None

    def script(self, command, **kwargs):
        self.scripts.append(command)
        return b""


class DirectoryOwnershipTests(unittest.TestCase):
    def test_adb_thread_exception_cannot_print_private_error_or_escape(self):
        device = ImmediateDevice()
        def failed(*args, **kwargs):
            raise OSError(CANARY)
        device.raw = failed
        device.read_optional = lambda path: b""
        stderr = io.StringIO()
        with contextlib.redirect_stderr(stderr):
            result = spike.NativeWorker(device, "/fixed/owner").run("/fixed/binary", [])
        self.assertEqual(result.status, "cleanup_failed")
        self.assertFalse(result.cleanup_complete)
        self.assertNotIn(CANARY, stderr.getvalue())

    def test_directory_removal_failure_does_not_erase_verified_process_result(self):
        result = spike.NativeWorker(ImmediateDevice(), "/fixed/owner").run("/fixed/binary", [])
        self.assertTrue(result.cleanup_complete)
        self.assertTrue(result.adb_cleanup_complete)
        self.assertFalse(result.directory_cleanup_complete)
        self.assertNotIn(CANARY, repr(result))

    def test_malformed_owner_never_releases_worker_or_removes_unverified_directory(self):
        device = ImmediateDevice()
        original = device.read_optional
        device.read_optional = lambda path: b"123 extra\n" if path.endswith("/owner") else original(path)
        result = spike.NativeWorker(device, "/fixed/owner").run("/fixed/binary", [])
        self.assertFalse(result.cleanup_complete)
        self.assertEqual(result.status, "cleanup_failed")
        self.assertFalse(any("/release" in script for script in device.scripts))
        self.assertTrue(any("/cancel" in script for script in device.scripts))
        self.assertFalse(any(command[0] in ("rm", "rmdir", "kill", "pkill") for command in device.shells))

    def test_wrong_owner_command_never_releases_or_signals_a_pid(self):
        device = ImmediateDevice()
        device.identity = lambda pid: (17, [b"/unrelated/worker"])
        result = spike.NativeWorker(device, "/fixed/owner").run("/fixed/binary", [])
        self.assertFalse(result.cleanup_complete)
        self.assertFalse(any("/release" in script for script in device.scripts))
        self.assertFalse(any(command[0] in ("kill", "pkill") for command in device.shells))


class SdkOwnershipFollowupTests(unittest.TestCase):
    def envelope(self):
        metrics = dict(worker_off_main=True, owners_balanced=True, generated_text_logged=False,
                       engines_opened=1, engines_closed=1, conversations_opened=1,
                       conversations_closed=1, main_pulses=2)
        return (b"INSTRUMENTATION_RESULT: result_base64=" + base64.b64encode(worker_result())
                + b"\nINSTRUMENTATION_RESULT: metrics=" + json.dumps(metrics).encode() + b"\n")

    def test_returned_sdk_output_cannot_establish_cleanup_when_package_stop_fails(self):
        device = SimpleNamespace(private_write=Mock(), raw=Mock(return_value=remote(stdout=self.envelope())))
        worker = spike.SdkWorker(device, "1" * 64)
        worker.verify_package = Mock()
        worker.stop = Mock(return_value=False)
        result = worker.run("unused", [], b"synthetic")
        self.assertEqual(result.status, "cleanup_failed")
        self.assertFalse(result.cleanup_complete)
        self.assertNotIn(CANARY, repr(result))

    def test_cancelled_sdk_discards_late_completed_output_after_explicit_stop(self):
        release = threading.Event()
        def raw(*args, **kwargs):
            release.wait(1)
            return remote(stdout=self.envelope())
        device = SimpleNamespace(private_write=Mock(), raw=raw)
        worker = spike.SdkWorker(device, "1" * 64)
        worker.verify_package = Mock()
        def stop():
            release.set()
            return True
        worker.stop = stop
        result = worker.run("unused", [], b"synthetic", deadline=1, cancel_after=.01)
        self.assertEqual(result.status, "cancelled")
        self.assertEqual(result.stdout, b"")
        self.assertEqual(result.metrics, {})
        self.assertTrue(result.cleanup_complete)

    def test_unrecognized_installed_apk_cannot_write_request_or_launch_sdk(self):
        device = SimpleNamespace(shell=Mock(return_value=b"package:/data/app/base.apk\n"),
                                 private_write=Mock(), raw=Mock())
        worker = spike.SdkWorker(device, "1" * 64)
        with self.assertRaises(spike.Failure):
            worker.run("unused", [], b"synthetic")
        device.private_write.assert_not_called()
        device.raw.assert_not_called()
        self.assertFalse(any(call.args[0] == "am" for call in device.shell.call_args_list))

    def test_split_or_multiple_package_paths_cannot_authorize_force_stop(self):
        device = SimpleNamespace(shell=Mock(return_value=b"package:/data/app/base.apk\npackage:/other/split.apk\n"))
        with self.assertRaises(spike.Failure):
            spike.SdkWorker(device, "1" * 64).stop()
        self.assertEqual(device.shell.call_count, 1)

    def test_transfer_cleanup_timeout_is_a_fixed_failure_without_private_exception(self):
        class Process:
            pid = 731
            def poll(self):
                return None
            def wait(self, timeout=None):
                raise subprocess.TimeoutExpired(CANARY, timeout)
            def kill(self):
                pass
        class Job:
            def __init__(self, pid):
                pass
            def close(self):
                return False
        device = spike.Device("adb", "synthetic-emulator")
        device.script = Mock(return_value=b"")
        device.shell = Mock(side_effect=[b"", b"fs blocks used available\nfs 10000000 1 9999999 1% /data\n"])
        with tempfile.TemporaryDirectory() as directory:
            model = Path(directory) / "synthetic-model"
            model.write_bytes(b"abc")
            with patch.object(spike.host, "verify_model", return_value=None), \
                    patch.object(spike.subprocess, "Popen", return_value=Process()) as spawn, \
                    patch.object(spike.host, "WindowsJob", Job), \
                    patch.object(spike.time, "monotonic", side_effect=[0, 181]), \
                    self.assertRaises(spike.Failure) as failure:
                device.provision_private_model(model)
        self.assertNotIn(CANARY, str(failure.exception))
        self.assertEqual(spawn.call_args.kwargs["stdout"], subprocess.DEVNULL)
        self.assertEqual(spawn.call_args.kwargs["stderr"], subprocess.DEVNULL)


if __name__ == "__main__":
    unittest.main()
