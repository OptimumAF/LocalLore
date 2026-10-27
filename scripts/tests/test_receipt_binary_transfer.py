"""Original tiny transport adversaries; all clients and supervisors are mocked.

No model payload, native runtime, OS memory API or device is accessed here.
Copyright 2026 LocalLore contributors. SPDX-License-Identifier: Apache-2.0
"""
from contextlib import ExitStack, redirect_stdout
import copy
import io
import json
from pathlib import Path
import subprocess
import sys
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import patch

from scripts.tests import test_receipt_real_stream_guards as guards
from scripts.tests import test_receipt_transfer_probe as probe_fixture

r, q, p = guards.r, guards.q, probe_fixture.p
UID = 10310


def body(size):
    return {"version": 1, "source_bytes": size, "source_verified": True, "client_returncode": 0,
            "remote_exit_status_known": False, "destination_verified": False}


def receipt(raw):
    return {"status": "child_exited", "worker_returncode": 0, "cleanup_complete": True,
            "output_capture_complete": True, "stdout_bytes": len(raw), "stderr_bytes": 0, "elapsed_ms": 7}


class State:
    def __init__(self, root, phase="candidate"):
        self.value = guards.candidate(root) if phase == "candidate" else guards.fixture.proposal(root)
        self.lease = guards.fixture.fixture.Lease(self.value)
        self.owner = r.Owner(self.value, self.lease)
        self.owner.uid_map = {q.APP: UID, q.TEST: UID + 1}
        self.owner.stage = "source-stream"
        self.owner.proposal_path, self.owner.authorization_path = root / "p.json", root / "a.json"
        self.owner.proposal_path.write_bytes(guards.fixture.encoded(self.value))
        self.owner.authorization_path.write_bytes(b"original synthetic test grant, never admitted")
        self.facts = {"packages": dict(self.value["apk_sha256"]), "uid_map": dict(self.owner.uid_map),
                      "processes": {"target": [], "test_helper": []},
                      "userdata": {"available_bytes": q.contract.USERDATA_FLOOR + r.MODEL_BYTES}}
        name = "continued-before-facts.json" if phase == "candidate" else "installed-facts.json"
        (self.owner.directory / name).write_bytes(guards.fixture.encoded(self.facts))
        self.raw = guards.fixture.encoded(body(self.value["source"]["bytes"]))

    def fake_supervise(self, changes=None, raw=None, lost=False):
        def run(command, request, directory, seconds, on_started):
            assert command[0] == sys.executable and command[1:3] == ["-B", "-E"]
            assert command[3] == str(self.owner.STREAM_SCRIPT) and command[4] == "_stream"
            assert request == r.STREAM_REQUEST + b"10310\n"
            assert type(seconds) is int and 5 < seconds <= 240 and callable(on_started)
            assert directory == self.owner.directory / "model-stream-driver-v2"
            assert (directory / "start-v2.json").is_file()
            payload = self.raw if raw is None else raw
            with (directory / "owner-stdout-v1.bin").open("xb") as stream: stream.write(payload)
            with (directory / "owner-stderr-v1.bin").open("xb") as stream: stream.write(b"")
            if lost: self.lease.live = False
            return receipt(payload) | (changes or {})
        return run

    def mocks(self, stack, supervisor=None, preflight=None):
        stack.enter_context(patch.object(r.environment, "process_identity", side_effect=lambda pid:
            {"pid": pid, "creation_filetime": 1, "executable": sys.executable}))
        stack.enter_context(patch.object(r.time, "monotonic", return_value=1000.0))
        stack.enter_context(patch.object(r.time, "time", return_value=2000.0))
        self.owner.until = 1870.0
        owned = stack.enter_context(patch.object(r.environment, "supervise", side_effect=supervisor or self.fake_supervise()))
        generic = stack.enter_context(patch.object(q.host, "run_process", side_effect=preflight or
            AssertionError("Generic client must not execute a model stream")))
        return owned, generic


class ReceiptBinaryTransferTests(unittest.TestCase):
    def test_fixed_modes_refuse_windows_shell_without_silent_fallback(self):
        with patch.object(r.sys, "platform", "win32"):
            for mode in ("CAT", "DD_1M"): self.assertEqual(("exec-in",), r.binary_stdin_operation(mode))
            for mode in ("SHELL_CAT", "SHELL_BINARY"):
                with self.assertRaisesRegex(ValueError, "^windows_shell_binary_refused$"):
                    r.binary_stdin_operation(mode)
            for mode in (True, None, "cat", "SHELL_BIN", "CAT;id", b"CAT"):
                with self.assertRaises(AssertionError): r.binary_stdin_operation(mode)
        with patch.object(r.sys, "platform", "linux"):
            for mode in ("SHELL_CAT", "SHELL_BINARY"):
                self.assertEqual(("shell", "-T", "-e", "none"), r.binary_stdin_operation(mode))

    def test_windows_probe_shell_refuses_before_lease_claim_or_any_client(self):
        with tempfile.TemporaryDirectory() as directory, patch.object(r.sys, "platform", "win32"), \
             patch.object(q, "open_lease") as lease, patch.object(q.host, "run_process") as client, \
             patch.object(r.environment, "supervise") as supervisor:
            root = Path(directory)
            for mode in ("SHELL_CAT", "SHELL_BINARY"):
                with self.assertRaisesRegex(ValueError, "^windows_shell_binary_refused$"):
                    p._stream_authorized({}, mode, UID, root / "p", root / "a", root, None)
                with self.assertRaisesRegex(ValueError, "^windows_shell_binary_refused$"):
                    p.Owner.transfer(SimpleNamespace(), mode)
            with self.assertRaisesRegex(ValueError, "^windows_shell_binary_refused$"):
                p.Owner.shell_gate(SimpleNamespace())
            lease.assert_not_called(); client.assert_not_called(); supervisor.assert_not_called()
            self.assertEqual([], list(root.iterdir()))

    def test_parent_budget_is_fixed_by_phase_not_cli_or_guest_profile(self):
        self.assertEqual(240, r.MODEL_STREAM_SECONDS)
        self.assertEqual(240, r.stream_parent_seconds("candidate")); self.assertEqual(180, r.stream_parent_seconds("preflight"))
        for phase in (None, True, "model", "candidate ", "candidate;id"):
            with self.assertRaises(AssertionError): r.stream_parent_seconds(phase)
        self.assertEqual(150000, r.PHASES["IMPORT"][3]); self.assertEqual(170000, r.PHASES["PLAY"][3])
        self.assertEqual(180000, r.source_trace.MAX_ELAPSED_MS)

    def test_actual_model_adapter_retains_receipt_and_old_summary_without_destination_authority(self):
        with tempfile.TemporaryDirectory() as directory, ExitStack() as stack:
            state = State(Path(directory)); owned, generic = state.mocks(stack)
            result = state.owner.transfer()
            self.assertEqual(body(r.MODEL_BYTES), result); self.assertEqual(1, owned.call_count); generic.assert_not_called()
            self.assertFalse(result["remote_exit_status_known"]); self.assertFalse(result["destination_verified"])
            driver = state.owner.directory / "model-stream-driver-v2"
            self.assertEqual(receipt(state.raw), json.loads((driver / "result-v1.json").read_bytes()))
            start = json.loads((driver / "start-v2.json").read_bytes())
            self.assertEqual({"version": 2, "deadline_seconds": 240, "client_cap_seconds": 150, "summary_cap_bytes": 4096,
                              "source_bytes": r.MODEL_BYTES, "source_sha256": r.MODEL_SHA}, start)
            parent = json.loads((state.owner.directory / "stream-parent-v1.json").read_bytes())
            self.assertEqual(2240.0, parent["deadline_epoch"])
            self.assertEqual(state.raw, (state.owner.commands / "command-0001.stdout.bin").read_bytes())
            self.assertEqual(0, state.owner.methods)
            with self.assertRaises(AssertionError): state.owner.transfer()
            self.assertEqual(1, owned.call_count)

    def test_preflight_still_uses_generic_180_second_helper(self):
        with tempfile.TemporaryDirectory() as directory, ExitStack() as stack:
            state = State(Path(directory), "preflight")
            def run(*args, **kwargs):
                self.assertEqual(180, kwargs["deadline"]); self.assertEqual(4096, kwargs["max_output"])
                return SimpleNamespace(status="completed", returncode=0, cleanup_complete=True,
                                       stdout=state.raw, stderr_bytes=0)
            owned, generic = state.mocks(stack, preflight=run)
            self.assertEqual(body(r.PROBE_BYTES), state.owner.transfer()); owned.assert_not_called()
            self.assertEqual(1, generic.call_count)

    def test_model_parent_clips_to_remaining_aggregate_without_reset(self):
        with tempfile.TemporaryDirectory() as directory, ExitStack() as stack:
            state = State(Path(directory)); owned, _ = state.mocks(stack)
            state.owner.until = 1200.9
            state.owner.transfer()
            self.assertEqual(200, owned.call_args.args[3]); self.assertEqual(1200.9, state.owner.until)
            parent = json.loads((state.owner.directory / "stream-parent-v1.json").read_bytes())
            self.assertEqual(2200.0, parent["deadline_epoch"])

    def test_expired_reserve_consumes_attempt_but_spawns_no_client(self):
        for remaining in (0, 5, 5.999):
            with self.subTest(remaining=remaining), tempfile.TemporaryDirectory() as directory, ExitStack() as stack:
                state = State(Path(directory)); owned, generic = state.mocks(stack); state.owner.until = 1000 + remaining
                with self.assertRaises(AssertionError): state.owner.transfer()
                self.assertTrue(state.owner.stream_attempted); self.assertEqual(0, state.owner.methods)
                owned.assert_not_called(); generic.assert_not_called()
                self.assertFalse((state.owner.directory / "model-stream-driver-v2").exists())

    def test_model_only_source_and_exact_integer_supervisor_caps_before_allocation(self):
        for change in ("phase", "bytes", "bool_bytes", "sha", "short", "long", "bool", "float"):
            with self.subTest(change=change), tempfile.TemporaryDirectory() as directory, ExitStack() as stack:
                state = State(Path(directory)); owned, generic = state.mocks(stack); seconds = 240
                if change == "phase": state.owner.real_phase = "preflight"
                if change == "bytes": state.value["source"]["bytes"] += 1
                if change == "bool_bytes": state.value["source"]["bytes"] = True
                if change == "sha": state.value["source"]["sha256"] = "0" * 64
                if change == "short": seconds = 5
                if change == "long": seconds = 241
                if change == "bool": seconds = True
                if change == "float": seconds = 6.0
                with self.assertRaises(AssertionError): state.owner._model_stream(["not-run"], b"", seconds)
                owned.assert_not_called(); generic.assert_not_called()
                self.assertFalse((state.owner.directory / "model-stream-driver-v2").exists())

    def test_unknown_supervisor_states_poison_transfer_before_import_and_keep_raw(self):
        variants = [{"status": "expired"}, {"status": "evidence_failed"}, {"worker_returncode": 2}, {"worker_returncode": False},
                    {"cleanup_complete": False}, {"cleanup_complete": 1}, {"output_capture_complete": False},
                    {"output_capture_complete": 1}, {"stdout_bytes": True}, {"stdout_bytes": -1}, {"stdout_bytes": 4097},
                    {"stderr_bytes": 1}, {"stderr_bytes": False}]
        for changes in variants:
            with self.subTest(changes=changes), tempfile.TemporaryDirectory() as directory, ExitStack() as stack:
                state = State(Path(directory)); owned, generic = state.mocks(stack, state.fake_supervise(changes))
                stack.enter_context(patch.object(state.owner, "wait_boot")); stack.enter_context(patch.object(state.owner, "check_guest_cpu_profile"))
                stack.enter_context(patch.object(state.owner, "facts", return_value=state.facts))
                selected = stack.enter_context(patch.object(r, "run_selected"))
                with self.assertRaises(AssertionError): r.run_cohort(state.owner)
                self.assertFalse(state.owner.clean); selected.assert_not_called(); generic.assert_not_called()
                driver = state.owner.directory / "model-stream-driver-v2"
                self.assertEqual(state.raw, (driver / "owner-stdout-v1.bin").read_bytes())
                self.assertEqual(receipt(state.raw) | changes, json.loads((driver / "result-v1.json").read_bytes()))
                with self.assertRaises(AssertionError): state.owner.transfer()
                self.assertEqual(1, owned.call_count)

    def test_raw_length_mismatch_and_malformed_closed_summary_cannot_qualify_copy(self):
        for change in ("length", "empty", "extra", "bool_size", "destination", "remote"):
            with self.subTest(change=change), tempfile.TemporaryDirectory() as directory, ExitStack() as stack:
                state = State(Path(directory)); payload = body(r.MODEL_BYTES); changes = {}
                if change == "extra": payload["private"] = "original canary"
                if change == "bool_size": payload["source_bytes"] = True
                if change == "destination": payload["destination_verified"] = True
                if change == "remote": payload["remote_exit_status_known"] = True
                raw = b"" if change == "empty" else guards.fixture.encoded(payload)
                if change == "length": changes["stdout_bytes"] = len(raw) - 1
                state.mocks(stack, state.fake_supervise(changes, raw))
                with self.assertRaises((AssertionError, ValueError)): state.owner.transfer()
                # Bad summary content is not unknown OS cleanup. The consumed
                # one-shot and raised error still prohibit any later phase.
                self.assertEqual(change != "length", state.owner.clean)
                self.assertTrue(state.owner.stream_attempted); self.assertEqual(0, state.owner.methods)
                with self.assertRaises(AssertionError): state.owner.transfer()
                self.assertEqual(raw, (state.owner.directory / "model-stream-driver-v2/owner-stdout-v1.bin").read_bytes())

    def test_4096_byte_summary_is_accepted_but_not_4097(self):
        for size in (4096, 4097):
            with self.subTest(size=size), tempfile.TemporaryDirectory() as directory, ExitStack() as stack:
                state = State(Path(directory)); raw = state.raw + b" " * (size - len(state.raw))
                state.mocks(stack, state.fake_supervise(raw=raw))
                if size == 4096: self.assertEqual(body(r.MODEL_BYTES), state.owner.transfer())
                else:
                    with self.assertRaises(AssertionError): state.owner.transfer()

    def test_existing_capture_path_and_owner_loss_refuse_without_retry(self):
        for mode in ("existing", "lost"):
            with self.subTest(mode=mode), tempfile.TemporaryDirectory() as directory, ExitStack() as stack:
                state = State(Path(directory)); owned, generic = state.mocks(stack, state.fake_supervise(lost=mode == "lost"))
                driver = state.owner.directory / "model-stream-driver-v2"
                if mode == "existing":
                    driver.mkdir(); (driver / "owner-stdout-v1.bin").write_bytes(b"preserve original")
                with self.assertRaises((FileExistsError, RuntimeError)): state.owner.transfer()
                self.assertFalse(state.owner.clean if mode == "existing" else state.owner.owner_live)
                generic.assert_not_called(); self.assertEqual(0 if mode == "existing" else 1, owned.call_count)
                if mode == "existing": self.assertEqual(b"preserve original", (driver / "owner-stdout-v1.bin").read_bytes())

    def test_result_retention_failure_preserves_original_and_forbids_later_import(self):
        with tempfile.TemporaryDirectory() as directory, ExitStack() as stack:
            state = State(Path(directory)); owned, generic = state.mocks(stack)
            original, write = OSError("original synthetic retention failure"), q.write_json
            def retain(path, value):
                if Path(path).name == "result-v1.json": raise original
                return write(path, value)
            stack.enter_context(patch.object(q, "write_json", side_effect=retain))
            with self.assertRaises(OSError) as caught: state.owner.transfer()
            self.assertIs(original, caught.exception); self.assertFalse(state.owner.clean)
            self.assertEqual(1, owned.call_count); generic.assert_not_called()
            self.assertTrue((state.owner.directory / "model-stream-driver-v2/owner-stdout-v1.bin").is_file())

    def test_phase_specific_child_deadline_preserves_150_second_client_and_full_held_fd(self):
        for phase, parent_span, expected_timeout in (("preflight", 180, 95), ("candidate", 240, 150)):
            with self.subTest(phase=phase), tempfile.TemporaryDirectory() as directory, ExitStack() as stack:
                state = guards.StreamFixture(Path(directory))
                # Only the authorization/source-path unit seams use the original
                # tiny probe here; this is not real-candidate admission evidence.
                state.value["phase"] = phase; state.parent["phase"] = phase
                state.parent["deadline_epoch"] = 100 + parent_span; state.rewrite_parent()
                if phase == "candidate": (state.cohort / "continued-before-facts.json").write_bytes(state.fact_path.read_bytes())
                def child(argv, **kwargs):
                    self.assertEqual(["exec-in"], argv[-2:-1]); self.assertIsNone(kwargs.get("input"))
                    self.assertEqual(expected_timeout, kwargs["timeout"])
                    self.assertEqual(r.PROBE_PATH.read_bytes(), kwargs["stdin"].read())
                    return SimpleNamespace(returncode=0)
                run = state.mocks(stack, child=child, source=r.PROBE_PATH)
                stack.enter_context(patch.object(r.time, "time", side_effect=[100.0, 180.0]))
                self.assertEqual(0, state.invoke()[0]); self.assertEqual(1, run.call_count)

    def test_child_parent_cap_or_post_hash_reserve_refuses_before_client(self):
        for phase, span, after_hash in (("preflight", 181, None), ("candidate", 241, None), ("candidate", 240, 335)):
            with self.subTest(phase=phase, span=span), tempfile.TemporaryDirectory() as directory, ExitStack() as stack:
                state = guards.StreamFixture(Path(directory)); state.value["phase"] = phase; state.parent["phase"] = phase
                state.parent["deadline_epoch"] = 100 + span; state.rewrite_parent()
                if phase == "candidate": (state.cohort / "continued-before-facts.json").write_bytes(state.fact_path.read_bytes())
                run = state.mocks(stack, source=r.PROBE_PATH)
                stack.enter_context(patch.object(r.time, "time", side_effect=[100.0] if after_hash is None else [100.0, after_hash]))
                with self.assertRaises(AssertionError): state.invoke()
                run.assert_not_called()
                self.assertEqual(after_hash is not None, (state.cohort / "stream-worker-claimed-v1.json").exists())

    def test_coherently_rebound_prior_bool_counters_and_uid_aliases_refuse(self):
        for change in ("baseline", "method_bool", "return_bool", "uid_alias", "uid_bool", "uid_string", "uid_low"):
            with self.subTest(change=change), tempfile.TemporaryDirectory() as directory, ExitStack() as stack:
                root = Path(directory); value = guards.candidate(root)
                records = {key: json.loads(Path(item["path"]).read_bytes()) for key, item in value["preflight"].items()}
                if change == "method_bool": records["result"]["instrumentation_commands"] = True
                if change == "return_bool": records["owned_result"]["worker_returncode"] = False
                replacements = {"uid_alias": UID, "uid_bool": True, "uid_string": str(UID + 1), "uid_low": 9999}
                if change in replacements: records["facts"]["uid_map"][q.TEST] = replacements[change]
                records["result"]["result"]["after"] = copy.deepcopy(records["facts"])
                for key, record in records.items():
                    path = Path(value["preflight"][key]["path"]); path.write_bytes(guards.fixture.encoded(record))
                    digest = q.sha(path.read_bytes()); value["preflight"][key]["sha256"] = digest; value["bindings"][str(path.resolve())] = digest
                stack.enter_context(patch.object(q, "APK_HASHES", value["apk_sha256"]))
                stack.enter_context(patch.object(r, "source_path", return_value=root / "synthetic-not-model-input.txt"))
                if change == "baseline": self.assertTrue(r.validate_proposal(value))
                else:
                    with self.assertRaises(AssertionError): r.validate_proposal(value)


if __name__ == "__main__":
    unittest.main()
