"""Original model/device-free binary transport regressions.

Copyright 2026 LocalLore contributors. SPDX-License-Identifier: Apache-2.0
"""
import base64
import copy
import hashlib
from pathlib import Path
import shlex
import sys
from types import SimpleNamespace
import unittest
from unittest.mock import Mock, patch

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "benchmarks"))
import android_recovery_transport as transport
import android_runtime_spike as spike
import runtime_spike as host

SESSION = "a" * 32
PRIVATE = "private-path-story-error-canary"
DATABASE = b"SQLite format 3\x00" + bytes(range(256)) + b"\r\n~.\n"
DIGEST = hashlib.sha256(DATABASE).hexdigest()


def response(raw=b"", code=0, cleaned=True, status="completed", stderr=0):
    return SimpleNamespace(stdout=raw, returncode=code, cleanup_complete=cleaned, status=status, stderr_bytes=stderr)


def facts(session=SESSION, data=DATABASE, sidecars=None):
    directory = "no_backup/locallore-cache-probe-v1-" + session
    lines = ["PATH|base|directory|4096|10231|10231|700|11|12|123|124",
        "PATH|session|directory|4096|10231|10231|700|11|13|123|124",
        "PATH|owner|regular file|34|10231|10231|600|11|14|123|124",
        "HASH|owner|" + transport.OWNER_SHA256 + "  " + directory + "/owner-v1"]
    files = {transport.NAMES[0]: data, **(sidecars or {})}
    for index, name in enumerate(transport.NAMES):
        if name not in files:
            lines.append("ABSENT|" + name)
        else:
            raw = files[name]
            lines += [f"FILE|{name}|regular file|{len(raw)}|10231|10231|600|11|{20+index}|123|124",
                f"HASH|{name}|{hashlib.sha256(raw).hexdigest()}  {directory}/{name}"]
    return ("\n".join(lines) + "\n").encode("ascii")


class Device:
    def __init__(self, override=None):
        self.clients_cleaned = True
        self.calls = []
        self.override = override

    def raw(self, arguments, **kwargs):
        if not self.clients_cleaned:
            raise AssertionError("dependent call after unknown ownership")
        self.calls.append((arguments, kwargs))
        if arguments == ["features"]:
            phase, result = "features", response(b"cmd,shell_v2,stat_v2\n")
        else:
            if arguments[:3] != ["shell", "-e", "none"]:
                raise AssertionError("wrong shell contract")
            command = shlex.split(arguments[3])
            if command[:4] != ["run-as", transport.PACKAGE, "/system/bin/sh", "-c"] or len(command) != 5:
                raise AssertionError("bad joined argv")
            script = command[4]
            if script == "exit 37":
                phase, result = "exit", response(code=37)
            elif script.startswith("printf '%b'"):
                phase, result = "binary", response(base64.b64encode(transport.BINARY_CONTROL))
            elif "PATH" in script:
                phase, result = "facts", response(facts())
            elif script.endswith('base64 -w 0 "$f"'):
                phase, result = "file", response(base64.b64encode(DATABASE))
            else:
                raise AssertionError("unexpected command")
        if self.override:
            result = self.override(phase, result)
        return result


class RecoveryTests(unittest.TestCase):
    def fixture(self, override=None, sink=None):
        device = Device(override)
        records = []
        if sink is None:
            sink = lambda stage, raw, metadata: records.append((stage, raw, copy.deepcopy(metadata)))
        recovery = transport.ReadOnlyRecovery(device, SESSION, sink)
        return recovery, device, records

    def failure(self, category, operation):
        with self.assertRaises(transport.RecoveryFailure) as caught:
            operation()
        self.assertEqual(caught.exception.category, category)
        self.assertNotIn(PRIVATE, str(caught.exception))
        return caught.exception

    def assert_poisoned(self, recovery, device):
        count = len(device.calls)
        self.failure("recovery_poisoned", recovery.qualify)
        self.failure("recovery_poisoned", recovery.facts)
        self.failure("recovery_poisoned", lambda: recovery.read_file(transport.NAMES[0], len(DATABASE), DIGEST))
        self.assertEqual(len(device.calls), count)

    def test_qualification_facts_and_file_preserve_binary_without_decode_or_normalization(self):
        recovery, device, records = self.fixture()
        self.assertEqual(recovery.qualify()["binary_control_bytes"], 262)
        observed = recovery.facts()
        self.assertEqual(observed["files"][transport.NAMES[0]]["bytes"], len(DATABASE))
        self.assertEqual(observed["absent"], list(transport.NAMES[1:]))
        self.assertEqual(recovery.read_file(transport.NAMES[0], len(DATABASE), DIGEST), DATABASE)
        self.assertEqual([row[0] for row in records], ["001_features", "002_exit_control", "003_binary_control", "004_facts", "005_file_0"])
        self.assertEqual(records[-1][1], base64.b64encode(DATABASE))
        self.assertEqual(records[-1][2]["stdout_sha256"], hashlib.sha256(base64.b64encode(DATABASE)).hexdigest())
        self.assertTrue(recovery.clients_cleaned)
        self.assertEqual(len(device.calls), 5)
        self.assertTrue(all(kwargs == {"deadline": 20} for _, kwargs in device.calls[:-1]))
        self.assertEqual(device.calls[-1][1], {"deadline": 20, "max_output": 262144})

    def test_base_device_inserts_no_pty_and_roundtrip_preserves_raw_script_argument(self):
        recovery, _, _ = self.fixture()
        script = "printf '%s' 'space \"quotes\" $HOME `id` ; \\ ~.\n'"
        arguments = recovery._command(script)
        self.assertEqual(shlex.split(arguments[-1])[-1], script)
        with patch.object(host, "run_process", return_value=response()) as runner:
            spike.Device("explicit-adb", "explicit-target").raw(arguments)
        self.assertEqual(runner.call_args.args[0][:7], ["explicit-adb", "-s", "explicit-target", "shell", "-T", "-e", "none"])
        self.assertNotIn("-x", runner.call_args.args[0])
        self.assertNotIn("exec-out", runner.call_args.args[0])

    def test_official_execout_escaping_model_keeps_the_old_extra_quotes_literal(self):
        script = "printf '%b' '\\0000\\0001'"
        prequoted = shlex.quote(script)
        # AOSP exec-out escapes each remaining argv before the daemon shell parse.
        daemon_command = "run-as " + " ".join(shlex.quote(arg) for arg in [transport.PACKAGE, "/system/bin/sh", "-c", prequoted])
        inner_script = shlex.split(daemon_command)[-1]
        self.assertEqual(inner_script, prequoted)
        self.assertNotEqual(inner_script, script)
        self.assertEqual(shlex.split(inner_script), [script])

    def test_real_host_byte_pipes_preserve_all_bytes_and_nonzero_exit(self):
        script = ("import sys;sys.stdin.buffer.read(1);"
            "sys.stdout.buffer.write(bytes(range(256))+b'\\x00\\r\\n~.\\n');sys.stdout.buffer.flush();"
            "sys.exit(int(sys.argv[1]))")
        for code in (0, 37):
            with self.subTest(code=code):
                result = host.run_process([sys.executable, "-B", "-c", script, str(code)], deadline=5, max_output=4096)
                self.assertEqual(result.status, "completed")
                self.assertTrue(result.cleanup_complete)
                self.assertEqual(result.returncode, code)
                self.assertEqual(result.stderr_bytes, 0)
                self.assertEqual(result.stdout, transport.BINARY_CONTROL)

    def test_invalid_session_never_dispatches(self):
        for session in (None, True, "A"*32, "a"*31, "../"+"a"*29, "a"*32+"\n"):
            device = Device()
            self.failure("invalid_arguments", lambda: transport.ReadOnlyRecovery(device, session, Mock()))
            self.assertEqual(device.calls, [])

    def test_qualified_session_device_and_sink_bindings_have_no_public_setter(self):
        recovery, device, records = self.fixture()
        original_sink = recovery.raw_sink
        recovery.qualify()
        for attribute, value in (("directory", "no_backup/foreign"), ("device", Device()), ("raw_sink", Mock()),
                ("qualified", False), ("poisoned", False), ("clients_cleaned", True), ("sequence", 0)):
            with self.assertRaises(AttributeError):
                setattr(recovery, attribute, value)
        self.assertEqual(recovery.directory, "no_backup/locallore-cache-probe-v1-" + SESSION)
        self.assertIs(recovery.device, device)
        self.assertIs(recovery.raw_sink, original_sink)
        recovery.facts()
        self.assertEqual(records[-1][0], "004_facts")
        self.assertEqual(len(device.calls), 4)

    def test_unknown_cleanup_cannot_be_reset_through_public_state_or_device_flag(self):
        recovery, device, _ = self.fixture(lambda phase, old: response(b"partial", cleaned=False))
        self.failure("client_cleanup_unknown", recovery.qualify)
        self.assertTrue(recovery.poisoned)
        self.assertFalse(recovery.clients_cleaned)
        device.clients_cleaned = True
        for attribute, value in (("qualified", True), ("poisoned", False), ("clients_cleaned", True)):
            with self.assertRaises(AttributeError):
                setattr(recovery, attribute, value)
        self.assert_poisoned(recovery, device)
        self.assertFalse(recovery.clients_cleaned)

    def test_unqualified_reads_and_repeated_qualification_poison_without_dispatch(self):
        recovery, device, _ = self.fixture()
        self.failure("qualification_required", recovery.facts)
        self.assertEqual(device.calls, [])
        self.assert_poisoned(recovery, device)
        recovery, device, _ = self.fixture()
        recovery.qualify()
        self.failure("already_qualified", recovery.qualify)
        self.assertEqual(len(device.calls), 3)

    def test_missing_duplicate_and_malformed_feature_receipts_stop_before_controls(self):
        for raw in (b"cmd\n", b"shell_v2,shell_v2\n", b"shell_v2,,cmd\n", b"shell_v2\x00", b"shell_v2\n\ncmd", b"\xff", b"shell_v2\ncmd,stat_v2\n"):
            recovery, device, records = self.fixture(lambda phase, result: response(raw) if phase == "features" else result)
            with self.assertRaises(transport.RecoveryFailure):
                recovery.qualify()
            self.assertEqual(len(device.calls), 1)
            self.assertEqual(records[0][1], raw)
            self.assert_poisoned(recovery, device)

    def test_recorded_features_line_shape_and_single_comma_shape_are_supported(self):
        for raw in (b"shell_v2\r\ncmd\r\nstat_v2\r\n", b"shell_v2\ncmd\nstat_v2\n", b"shell_v2,cmd,stat_v2\n"):
            recovery, device, records = self.fixture(lambda phase, old: response(raw) if phase == "features" else old)
            self.assertEqual(recovery.qualify()["status"], "qualified")
            self.assertEqual(len(device.calls), 3)
            self.assertEqual(records[0][1], raw)

    def test_negative_exit_control_rejects_client_zero_bool_stderr_and_output(self):
        for result in (response(code=0), response(code=True), response(code=37, stderr=1), response(b"unexpected", code=37)):
            recovery, device, records = self.fixture(lambda phase, old: result if phase == "exit" else old)
            self.failure("command_failed", recovery.qualify)
            self.assertEqual(len(device.calls), 2)
            self.assertEqual(records[-1][1], result.stdout)
            self.assert_poisoned(recovery, device)

    def test_every_binary_mismatch_retains_raw_then_poison_stops_files(self):
        for raw in (b"", base64.b64encode(transport.BINARY_CONTROL[:-1]), base64.b64encode(transport.BINARY_CONTROL+b"x"), b"x"*1101, base64.b64encode(transport.BINARY_CONTROL.replace(b"\r\n", b"\n"))):
            recovery, device, records = self.fixture(lambda phase, old: response(raw) if phase == "binary" else old)
            with self.assertRaises(transport.RecoveryFailure):
                recovery.qualify()
            self.assertEqual(records[-1][1], raw)
            self.assert_poisoned(recovery, device)

    def test_process_failure_types_are_not_success_and_raw_is_retained(self):
        for result in (response(PRIVATE.encode(), status="timeout"), response(b"partial", status="output_limit"),
                response(b"x", cleaned=False), response(b"x", code=True), response("text"), response(b"x", stderr=True)):
            recovery, device, records = self.fixture(lambda phase, old: result if phase == "features" else old)
            with self.assertRaises(transport.RecoveryFailure):
                recovery.qualify()
            self.assertEqual(len(records), 1)
            self.assertEqual(records[0][1], result.stdout if type(result.stdout) is bytes else b"")
            self.assert_poisoned(recovery, device)

    def test_sink_is_before_parser_and_sink_failure_always_poisoned(self):
        calls = []
        recovery, device, _ = self.fixture(sink=lambda stage, raw, metadata: calls.append(raw))
        recovery.qualify()
        with patch.object(recovery, "_parse_facts", side_effect=ValueError(PRIVATE)):
            self.failure("facts_invalid", recovery.facts)
        self.assertEqual(calls[-1], facts())
        self.assert_poisoned(recovery, device)
        recovery, device, _ = self.fixture(sink=Mock(side_effect=OSError(PRIVATE)))
        self.failure("raw_sink_failed", recovery.qualify)
        self.assertEqual(len(device.calls), 1)
        self.assert_poisoned(recovery, device)

    def test_sink_revealed_unknown_cleanup_stops_even_a_valid_result(self):
        recovery, device, _ = self.fixture(sink=lambda *_: setattr(device, "clients_cleaned", False))
        error = self.failure("client_cleanup_unknown", recovery.qualify)
        self.assertFalse(error.clients_cleaned)
        self.assertEqual(len(device.calls), 1)
        self.assert_poisoned(recovery, device)

    def test_device_exception_fixed_category_retained_and_sticky(self):
        recovery, device, records = self.fixture()
        device.raw = Mock(side_effect=RuntimeError(PRIVATE))
        self.failure("device_call_failed", recovery.qualify)
        self.assertFalse(recovery.clients_cleaned)
        self.assertEqual(records[0][1], b"")
        self.assertEqual(records[0][2]["status"], "call_failed")
        self.assertEqual(device.raw.call_count, 1)
        self.failure("recovery_poisoned", recovery.facts)
        self.assertEqual(device.raw.call_count, 1)

    def test_known_device_exception_then_sink_unknown_retains_primary_and_false_cleanup(self):
        recovery, device, _ = self.fixture(sink=lambda *_: setattr(device, "clients_cleaned", False))
        device.raw = Mock(side_effect=spike.Failure(PRIVATE, command_cleaned=True))
        error = self.failure("device_call_failed", recovery.qualify)
        self.assertFalse(error.clients_cleaned)
        self.assertFalse(recovery.clients_cleaned)
        self.assertEqual(device.raw.call_count, 1)
        self.failure("recovery_poisoned", recovery.facts)
        self.assertEqual(device.raw.call_count, 1)

    def test_facts_reject_unknown_duplicate_missing_marker_path_metadata_and_records(self):
        good = facts()
        for raw in (b"", good+good, good+b"extra\n", good.replace(b"ABSENT|stories.sqlite3-wal\n", b""),
                good.replace(b"|regular file|34|", b"|regular file|33|"),
                good.replace(transport.OWNER_SHA256.encode(), b"f"*64),
                good.replace(b"PATH|base|directory", b"PATH|base|symbolic link"),
                good.replace(b"|11|20|", b"|11|0|"), good.replace(b"stories.sqlite3-wal", b"foreign"),
                good.replace(b"/owner-v1\n", b"/foreign\n"), good.replace(b"\n", b"\r\n", 1),
                good.replace(b"\n", b"\r\r\n"), good.replace(b"directory", b"direc\rtory", 1)):
            recovery, device, records = self.fixture(lambda phase, old: response(raw) if phase == "facts" else old)
            recovery.qualify()
            self.failure("facts_invalid", recovery.facts)
            self.assertEqual(records[-1][1], raw)
            self.assert_poisoned(recovery, device)

    def test_ancestor_marker_and_dangling_link_remote_refusals_stay_failed(self):
        for code in (71, 72):
            recovery, device, records = self.fixture(lambda phase, old: response(code=code) if phase == "facts" else old)
            recovery.qualify()
            self.failure("command_failed", recovery.facts)
            command = shlex.split(device.calls[-1][0][-1])[-1]
            for guard in ('[ ! -L no_backup ]', '[ ! -L "$q" ]', '[ ! -L "$m" ]', '[ ! -L "$f" ]', transport.OWNER_SHA256):
                self.assertIn(guard, command)
            self.assertNotIn('$(cat', command)
            self.assertEqual(records[-1][1], b"")
            self.assert_poisoned(recovery, device)

    def test_repeated_facts_detect_sidecar_and_ancestor_changes(self):
        recovery, device, _ = self.fixture()
        recovery.qualify()
        original = recovery.facts()
        self.assertEqual(recovery.facts(), original)
        for changed in (facts(sidecars={transport.NAMES[1]: b"new-wal"}), facts().replace(b"|11|13|", b"|11|99|")):
            recovery, device, _ = self.fixture()
            recovery.qualify()
            recovery.facts()
            device.override = lambda phase, old: response(changed) if phase == "facts" else old
            self.failure("facts_changed", recovery.facts)
            self.assert_poisoned(recovery, device)

    def test_zero_byte_regular_sidecar_with_fixed_empty_label_is_admitted(self):
        raw = facts(sidecars={transport.NAMES[3]: b""}).replace(b"FILE|stories.sqlite3-journal|regular file|0|", b"FILE|stories.sqlite3-journal|regular empty file|0|")
        recovery, device, _ = self.fixture(lambda phase, old: response(raw) if phase == "facts" else (response(b"") if phase == "file" else old))
        recovery.qualify()
        observed = recovery.facts()
        self.assertEqual(observed["files"][transport.NAMES[3]]["bytes"], 0)
        self.assertEqual(recovery.read_file(transport.NAMES[3], 0, hashlib.sha256(b"").hexdigest()), b"")
        self.assertEqual(len(device.calls), 5)

    def test_returned_facts_mutation_cannot_change_internal_admission(self):
        recovery, device, _ = self.fixture()
        recovery.qualify()
        observed = recovery.facts()
        observed["files"][transport.NAMES[0]]["sha256"] = "f"*64
        observed["files"][transport.NAMES[0]]["metadata"][1] = "0"
        observed["absent"].clear()
        self.assertEqual(recovery.read_file(transport.NAMES[0], len(DATABASE), DIGEST), DATABASE)
        self.assertEqual(len(device.calls), 5)

    def test_file_request_needs_fixed_name_strict_bounds_and_matching_prior_facts(self):
        for name, size, digest in (("../stories.sqlite3", 1, DIGEST), (True, 1, DIGEST),
                (transport.NAMES[0], True, DIGEST), (transport.NAMES[0], transport.MAX_FILE+1, DIGEST),
                (transport.NAMES[0], 1, "F"*64), (transport.NAMES[0], len(DATABASE)+1, DIGEST),
                (transport.NAMES[1], 0, hashlib.sha256(b"").hexdigest())):
            recovery, device, _ = self.fixture()
            recovery.qualify()
            recovery.facts()
            with self.assertRaises(transport.RecoveryFailure):
                recovery.read_file(name, size, digest)
            self.assertEqual(len(device.calls), 4)
            self.assert_poisoned(recovery, device)

    def test_file_mismatch_and_sqlite_header_failures_preserve_bounded_raw(self):
        for raw in (DATABASE[:-1], DATABASE+b"x", b"x"*len(DATABASE), b"x"*(transport.MAX_FILE+1)):
            wire = base64.b64encode(raw)
            recovery, device, records = self.fixture(lambda phase, old: response(wire) if phase == "file" else old)
            recovery.qualify()
            recovery.facts()
            with self.assertRaises(transport.RecoveryFailure):
                recovery.read_file(transport.NAMES[0], len(DATABASE), DIGEST)
            self.assertEqual(records[-1][1], wire)
            self.assert_poisoned(recovery, device)
        raw = b"not-a-database"
        recovery, device, records = self.fixture(lambda phase, old: response(facts(data=raw)) if phase == "facts" else (response(base64.b64encode(raw)) if phase == "file" else old))
        recovery.qualify()
        recovery.facts()
        self.failure("sqlite_header_invalid", lambda: recovery.read_file(transport.NAMES[0], len(raw), hashlib.sha256(raw).hexdigest()))
        self.assertEqual(records[-1][1], base64.b64encode(raw))
        self.assert_poisoned(recovery, device)

    def test_observed_lf_to_crlf_transformation_is_rejected_as_binary_but_safe_with_unwrapped_wire(self):
        observed = transport.BINARY_CONTROL.replace(b"\n", b"\r\n")
        self.assertEqual(len(observed), 265)
        recovery, device, records = self.fixture(lambda phase, old: response(observed) if phase == "binary" else old)
        self.failure("base64_invalid", recovery.qualify)
        self.assertEqual(records[-1][1], observed)
        self.assert_poisoned(recovery, device)
        recovery, device, records = self.fixture(lambda _, old: response(old.stdout.replace(b"\n", b"\r\n"), code=old.returncode))
        recovery.qualify()
        self.assertEqual(recovery.facts()["files"][transport.NAMES[0]]["sha256"], DIGEST)
        self.assertEqual(recovery.read_file(transport.NAMES[0], len(DATABASE), DIGEST), DATABASE)
        self.assertNotIn(b"\n", records[-1][1])
        self.assertEqual(records[-2][1], facts().replace(b"\n", b"\r\n"))

    def test_metadata_control_separators_cannot_substitute_for_lf(self):
        for separator in (b"\v", b"\f", b"\x1c", b"\x1d", b"\x1e"):
            raw = facts()[:-1].replace(b"\n", separator) + b"\n"
            recovery, device, records = self.fixture(lambda phase, old: response(raw) if phase == "facts" else old)
            recovery.qualify()
            self.failure("facts_invalid", recovery.facts)
            self.assertEqual(records[-1][1], raw)
            self.assert_poisoned(recovery, device)

    def test_canonical_base64_rejects_pad_bits_padding_alphabet_and_decoded_size(self):
        for wire in (b"Zh==", b"Zg===", b"Zg==\n", b"Zg==\r\n", b"Zg", b"Zg-_", b"%%%%", b"\xff", b" Zg==", b""):
            recovery, device, records = self.fixture(lambda phase, old: response(facts(sidecars={transport.NAMES[1]: b"f"})) if phase == "facts" else (response(wire) if phase == "file" else old))
            recovery.qualify()
            recovery.facts()
            with self.assertRaises(transport.RecoveryFailure):
                recovery.read_file(transport.NAMES[1], 1, hashlib.sha256(b"f").hexdigest())
            self.assertEqual(records[-1][1], wire)
            self.assert_poisoned(recovery, device)

    def test_base64_decoder_runs_only_after_wire_sink_and_remote_success(self):
        recovery, device, records = self.fixture()
        with patch.object(recovery, "_decode_wire", side_effect=lambda *_: (_ for _ in ()).throw(AssertionError("decoder reached"))):
            with self.assertRaisesRegex(AssertionError, "decoder reached"):
                recovery.qualify()
        self.assertEqual(records[-1][1], base64.b64encode(transport.BINARY_CONTROL))
        recovery, device, records = self.fixture(lambda phase, old: response(base64.b64encode(DATABASE), code=1) if phase == "file" else old)
        recovery.qualify()
        recovery.facts()
        with patch.object(recovery, "_decode_wire", side_effect=AssertionError("decoder must not run")):
            self.failure("command_failed", lambda: recovery.read_file(transport.NAMES[0], len(DATABASE), DIGEST))
        self.assertEqual(records[-1][1], base64.b64encode(DATABASE))
        self.assert_poisoned(recovery, device)

    def test_maximum_file_encoded_bound_and_only_file_larger_runner_budget(self):
        raw = b"SQLite format 3\x00" + b"\n"*(transport.MAX_FILE-16)
        wire = base64.b64encode(raw)
        self.assertEqual(len(wire), 174764)
        recovery, device, records = self.fixture(lambda phase, old: response(facts(data=raw)) if phase == "facts" else (response(wire) if phase == "file" else old))
        recovery.qualify()
        recovery.facts()
        self.assertEqual(recovery.read_file(transport.NAMES[0], len(raw), hashlib.sha256(raw).hexdigest()), raw)
        self.assertEqual(records[-1][1], wire)
        self.assertEqual(device.calls[-1][1], {"deadline": 20, "max_output": 262144})
        self.assertTrue(all("max_output" not in kwargs for _, kwargs in device.calls[:-1]))
        script = shlex.split(device.calls[-1][0][-1])[-1]
        self.assertTrue(script.endswith('base64 -w 0 "$f"'))
        self.assertNotIn(" | ", script)

    def test_file_wire_output_limit_and_extra_encoded_data_poison_before_decode(self):
        for result in (response(b"A"*transport.MAX_WIRE, status="output_limit"), response(b"A"*(transport.MAX_WIRE+1))):
            recovery, device, records = self.fixture(lambda phase, old: result if phase == "file" else old)
            recovery.qualify()
            recovery.facts()
            with patch.object(recovery, "_decode_wire", side_effect=AssertionError("decoder must not run")):
                self.failure("command_failed", lambda: recovery.read_file(transport.NAMES[0], len(DATABASE), DIGEST))
            self.assertEqual(records[-1][1], result.stdout)
            self.assert_poisoned(recovery, device)


if __name__ == "__main__":
    unittest.main()
