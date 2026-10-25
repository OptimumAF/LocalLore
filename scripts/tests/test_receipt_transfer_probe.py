"""Independent controller adversaries; tiny files and mocked clients only.

Copyright 2026 LocalLore contributors. SPDX-License-Identifier: Apache-2.0
"""
from contextlib import ExitStack, redirect_stdout
import io
import json
from pathlib import Path
import shlex
import stat
import subprocess
import sys
import tempfile
import time
from types import SimpleNamespace
import unittest
from unittest.mock import patch

from scripts.tests import test_receipt_real_candidate as fixture

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "benchmarks"))
import receipt_transfer_probe as p

q, c, e = p.q, p.c, p.e
UID = 10310


def encoded(value):
    return json.dumps(value, separators=(",", ":")).encode("ascii")


def proof_bytes(mode, *, binary=False):
    size, digest = (len(c.BINARY_PAYLOAD), c.BINARY_SHA256) if binary else (c.SOURCE_BYTES, c.SOURCE_SHA256)
    leaf = "binary-v1.bin" if binary else {"CAT": "cat.bin", "DD_1M": "dd-1m.bin", "SHELL_CAT": "shell-cat.bin"}[mode]
    return (str(UID) + "|" + str(size) + "\n" + digest + "  " + c.ROOT + "/" + leaf + "\n").encode("ascii")


def summary(mode):
    return {"version": 1, "mode": mode, "source_bytes": len(c.BINARY_PAYLOAD) if mode == "SHELL_BINARY" else c.SOURCE_BYTES, "source_verified": True,
            "client_returncode": 0, "remote_exit_status_known": False, "destination_verified": False,
            "client_elapsed_ms": 7}


def completed(raw=b"", *, clean=True, code=0, status="completed"):
    return SimpleNamespace(stdout=raw, cleanup_complete=clean, returncode=code, status=status,
                           stderr_bytes=0, elapsed_ms=7)


class Inputs:
    """Original preflight lineage, with tiny synthetic APK/source files."""
    def __init__(self, root):
        self.root = root
        self.value = fixture.fixture.proposal(root)
        self.value["scope"] = p.SCOPE
        self.source = root / p.SOURCE_NAME
        self.source.write_bytes(b"Original tiny synthetic transfer fixture.\x00\r\n\xff")
        self.value["source"] = {"path": str(self.source), "bytes": c.SOURCE_BYTES, "sha256": c.SOURCE_SHA256}
        self.environment = Path(self.value["environment_proposal_path"])
        self.environment.write_bytes(encoded({"memory_mib": 8192, "cores": 4,
                                             "host_available_memory_min": 12 * p.r.GIB}))
        for name in p.SOURCE_FILES:
            path = (q.ROOT / name).resolve()
            self.value["bindings"][str(path)] = q.sha(path.read_bytes())
        self.value["bindings"][str(self.environment)] = q.sha(self.environment.read_bytes())
        self.facts = {"packages": self.value["apk_sha256"], "uid_map": {q.APP: UID, q.TEST: UID + 1},
                      "processes": {"target": [], "test_helper": []}, "volume": "synthetic-volume",
                      "userdata": {"available_bytes": 4 * c.SOURCE_BYTES + q.contract.USERDATA_FLOOR}}
        self.proof = fixture.proof("SOURCE_PREFLIGHT")
        self.result = {"scope": p.r.SCOPE, "phase": "preflight", "status": "observed", "failure": None,
                       "clients_cleaned": True, "owner_live": True, "running_sha256": self.value["running_sha256"],
                       "instrumentation_commands": 1, "result": {"proof": self.proof, "after": self.facts}}
        self.owned = {"status": "child_exited", "worker_returncode": 0,
                      "cleanup_complete": True, "output_capture_complete": True}
        self.value["preflight"] = {}
        self.pp, self.ap = root / "proposal.json", root / "authorization.json"
        self.sync()

    def sync(self):
        for key, value in (("facts", self.facts), ("proof", self.proof), ("result", self.result), ("owned_result", self.owned)):
            path = self.root / ("preflight-" + key + ".json")
            path.write_bytes(encoded(value))
            digest = q.sha(path.read_bytes())
            self.value["preflight"][key] = {"path": str(path), "sha256": digest}
            self.value["bindings"][str(path)] = digest
        self.pp.write_bytes(encoded(self.value))
        self.auth = {"version": 1, "proposal_sha256": q.sha(self.pp.read_bytes()), "allow_device_calls": True,
                     "root_go_pending": False, "allow_synthetic_copy": True}
        self.ap.write_bytes(encoded(self.auth))

    def admitted(self):
        stack = ExitStack()
        stack.enter_context(patch.object(q, "APK_HASHES", self.value["apk_sha256"]))
        # Only fixed-size source metadata is substituted; q's actual hash bindings,
        # APK parser and r's actual twelve-check preflight proof parser still run.
        stack.enter_context(patch.object(p, "source_path", return_value=self.source))
        stack.enter_context(patch.dict(p.os.environ, {}, clear=True))
        return stack

    def owner(self):
        lease = fixture.fixture.Lease(self.value)
        owner = p.Owner(self.value, lease)
        owner.proposal_path, owner.authorization_path = self.pp, self.ap
        (owner.directory / "continued-before-facts.json").write_bytes(encoded(self.facts))
        return owner, lease


class StreamInputs(Inputs):
    def __init__(self, root, mode="CAT"):
        super().__init__(root)
        self.mode = mode
        self.value["source"].update(bytes=self.source.stat().st_size, sha256=q.sha(self.source.read_bytes()))
        self.cohort = root / "cohort"
        self.cohort.mkdir()
        prior = ("continued-before" if mode == "CAT" else "after-dd-1m" if mode == "SHELL_BINARY"
                 else "after-" + c.MODES[c.MODES.index(mode)-1].lower().replace("_", "-"))
        self.fp = self.cohort / (prior + "-facts.json")
        self.fp.write_bytes(encoded(self.facts))
        self.identity = {"pid": 4242, "started": "synthetic-instance", "executable": str(Path(sys.executable))}
        self.parent = {"version": 1, "parent": self.identity, "proposal_sha256": q.sha(self.pp.read_bytes()),
                       "authorization_sha256": q.sha(self.ap.read_bytes()), "mode": mode, "uid": UID,
                       "facts_sha256": q.sha(self.fp.read_bytes()), "deadline_epoch": time.time() + 90}
        self.parent_path = self.cohort / ("stream-" + mode.lower() + "-parent-v1.json")
        self.save_parent()
        self.claim = self.cohort / ("stream-" + mode.lower() + "-worker-claimed-v1.json")
        self.lease = fixture.fixture.Lease(self.value)
        if mode == "SHELL_CAT":
            (self.cohort / "shell-binary-proof.raw.txt").write_bytes(proof_bytes(mode, binary=True))

    def save_parent(self):
        self.parent_path.write_bytes(encoded(self.parent))

    def patches(self):
        stack = ExitStack()
        stack.enter_context(patch.object(q, "open_lease", return_value=self.lease))
        stack.enter_context(patch.object(q, "APK_HASHES", self.value["apk_sha256"]))
        stack.enter_context(patch.object(p, "source_path", return_value=self.source))
        stack.enter_context(patch.object(p.os, "getppid", return_value=4242))
        stack.enter_context(patch.object(e, "process_identity", return_value=self.identity))
        return stack

    def invoke(self):
        with redirect_stdout(io.StringIO()) as out:
            result = p.stream_authorized(self.value, self.mode, UID, self.pp, self.ap, self.root)
        return result, out.getvalue()


class TransferProbeTests(unittest.TestCase):
    def test_original_twelve_check_preflight_and_exact_synthetic_grant(self):
        with tempfile.TemporaryDirectory() as directory:
            data = Inputs(Path(directory))
            with data.admitted(), patch.object(q, "open_lease") as lease, patch.object(p.subprocess, "run") as run:
                self.assertEqual(p.authorize(data.pp, data.ap, data.root), data.value)
                lease.assert_not_called(); run.assert_not_called()
            self.assertNotIn(str(data.source), data.value["bindings"])

    def test_grant_truthiness_extra_capabilities_hash_and_evidence_refused(self):
        for key, value in (("version", True), ("allow_device_calls", 1), ("allow_synthetic_copy", 1),
                           ("root_go_pending", 0), ("proposal_sha256", "0" * 64), ("allow_model_copy", True)):
            with self.subTest(key=key), tempfile.TemporaryDirectory() as directory:
                data = Inputs(Path(directory)); data.auth[key] = value; data.ap.write_bytes(encoded(data.auth))
                with data.admitted(), patch.object(q, "open_lease") as lease, patch.object(p.subprocess, "run") as run:
                    with self.assertRaises(AssertionError): p.authorize(data.pp, data.ap, data.root)
                    lease.assert_not_called(); run.assert_not_called()
        with tempfile.TemporaryDirectory() as directory:
            data = Inputs(Path(directory))
            with data.admitted(), self.assertRaises(AssertionError): p.authorize(data.pp, data.ap, data.root / "foreign")

    def test_hash_rebound_failed_or_incomplete_preflight_is_not_authority(self):
        cases = (("result", "clients_cleaned", False), ("result", "owner_live", False),
                 ("result", "status", "stopped"), ("result", "failure", "failed"),
                 ("result", "running_sha256", "0" * 64), ("owned", "status", "running"),
                 ("owned", "cleanup_complete", False), ("owned", "output_capture_complete", False))
        for target, key, value in cases:
            with self.subTest(target=target, key=key), tempfile.TemporaryDirectory() as directory:
                data = Inputs(Path(directory)); getattr(data, target)[key] = value; data.sync()
                with data.admitted(), self.assertRaises(AssertionError): p.authorize(data.pp, data.ap, data.root)

    def test_preflight_boolean_completion_counters_are_not_integers(self):
        for target, key, value in (("owned", "worker_returncode", False), ("result", "instrumentation_commands", True)):
            with self.subTest(key=key), tempfile.TemporaryDirectory() as directory:
                data = Inputs(Path(directory)); getattr(data, target)[key] = value; data.sync()
                with data.admitted(), self.assertRaises(AssertionError): p.authorize(data.pp, data.ap, data.root)

    def test_preflight_uids_require_distinct_exact_bounded_integers(self):
        for package, value in ((q.APP, True), (q.APP, 9999), (q.APP, 2 ** 31),
                               (q.TEST, True), (q.TEST, 9999), (q.TEST, 2 ** 31), (q.TEST, UID)):
            with self.subTest(package=package, value=value), tempfile.TemporaryDirectory() as directory:
                data = Inputs(Path(directory)); data.facts["uid_map"][package] = value; data.sync()
                with data.admitted(), self.assertRaises(AssertionError): p.authorize(data.pp, data.ap, data.root)

    def test_real_preflight_proof_cannot_claim_sdk_or_omit_a_check(self):
        for change in ("sdk", "check", "foreign_uid"):
            with self.subTest(change=change), tempfile.TemporaryDirectory() as directory:
                data = Inputs(Path(directory))
                if change == "sdk": data.proof["sdk_invoked"] = True
                if change == "check": data.proof["checks"].pop(next(iter(data.proof["checks"])))
                if change == "foreign_uid": data.proof["uid"] += 1
                data.sync()
                with data.admitted(), self.assertRaises(AssertionError): p.authorize(data.pp, data.ap, data.root)

    def test_source_is_not_generic_binding_and_fixed_profile_is_required(self):
        for change in ("bound_source", "cores", "memory", "socket"):
            with self.subTest(change=change), tempfile.TemporaryDirectory() as directory:
                data = Inputs(Path(directory))
                if change == "bound_source": data.value["bindings"][str(data.source)] = q.sha(data.source.read_bytes())
                if change in ("cores", "memory"):
                    env = json.loads(data.environment.read_bytes()); env["cores" if change == "cores" else "memory_mib"] = 2
                    data.environment.write_bytes(encoded(env)); data.value["bindings"][str(data.environment)] = q.sha(data.environment.read_bytes())
                data.sync()
                with data.admitted():
                    with patch.dict(p.os.environ, {"ADB_SERVER_SOCKET": "untrusted"} if change == "socket" else {}):
                        with self.assertRaises(AssertionError): p.authorize(data.pp, data.ap, data.root)

    def test_source_path_rejects_wrong_size_relative_alias_and_boolean_size(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory).resolve() / p.SOURCE_NAME; path.write_bytes(b"tiny")
            valid = {"path": str(path), "bytes": c.SOURCE_BYTES, "sha256": c.SOURCE_SHA256}
            for change in ({}, {"path": p.SOURCE_NAME}, {"bytes": True}, {"sha256": "0" * 64}, {"extra": "no"}):
                with self.subTest(change=change), self.assertRaises(AssertionError): p.source_path(dict(valid, **change))
            fake = SimpleNamespace(st_mode=0o100600, st_file_attributes=0x400)
            with patch.object(Path, "lstat", return_value=fake), self.assertRaises(AssertionError): p.source_path(valid)

    def test_stream_barrier_refuses_before_authorization(self):
        for raw in (b"", p.STREAM_REQUEST, p.STREAM_REQUEST + b"CAT\n010310\n",
                    p.STREAM_REQUEST + b"CUSTOM\n10310\n", p.STREAM_REQUEST + b"CAT\n10310\nextra"):
            with self.subTest(raw=raw), patch.object(p.sys, "stdin", SimpleNamespace(buffer=io.BytesIO(raw))), \
                 patch.object(p, "authorize") as authorize, patch.object(p, "stream_authorized") as stream:
                with self.assertRaises(AssertionError): p.stream_worker("p", "a", "e")
                authorize.assert_not_called(); stream.assert_not_called()

    def test_all_modes_use_held_verified_fd_and_closed_transport_without_term(self):
        for mode in c.MODES:
            with self.subTest(mode=mode), tempfile.TemporaryDirectory() as directory:
                data = StreamInputs(Path(directory), mode); expected = data.source.read_bytes(); held = []
                def client(argv, **kwargs):
                    self.assertTrue(data.claim.is_file())
                    self.assertEqual(kwargs["stdin"].tell(), 0)
                    self.assertEqual(kwargs["stdin"].read(), expected); held.append(kwargs["stdin"])
                    op = ["shell", "-T", "-e", "none"] if mode == "SHELL_CAT" else ["exec-in"]
                    self.assertEqual(argv[7:], [*op, shlex.join(c.write_command(UID, mode))])
                    self.assertEqual(argv[1:7], ["-H", "127.0.0.1", "-P", "5037", "-s", data.lease.descriptor["serial"]])
                    self.assertNotIn("TERM", kwargs["env"])
                    self.assertEqual(kwargs["stdout"], subprocess.DEVNULL); self.assertEqual(kwargs["stderr"], subprocess.DEVNULL)
                    self.assertGreater(kwargs["timeout"], 0); self.assertLessEqual(kwargs["timeout"], 150)
                    return SimpleNamespace(returncode=0)
                with data.patches(), patch.dict(p.os.environ, {"TERM": "must-not-reach-child"}), \
                     patch.object(p.subprocess, "run", side_effect=client) as run:
                    code, raw = data.invoke(); self.assertEqual(code, 0)
                    value = json.loads(raw); self.assertFalse(value["destination_verified"]); self.assertFalse(value["remote_exit_status_known"])
                    self.assertEqual(value["source_bytes"], len(expected)); self.assertEqual(run.call_count, 1)
                    with self.assertRaises(FileExistsError): data.invoke()
                    self.assertEqual(run.call_count, 1)
                self.assertTrue(held[0].closed)

    def test_parent_identity_deadline_and_hash_refuse_before_claim_or_client(self):
        for change in ("pid", "identity", "proposal", "authorization", "mode", "uid", "deadline_bool", "expired", "overlong", "extra"):
            with self.subTest(change=change), tempfile.TemporaryDirectory() as directory:
                data = StreamInputs(Path(directory))
                if change == "pid": data.parent["parent"]["pid"] = 4243
                elif change == "identity": data.parent["parent"] = dict(data.identity, started="other")
                elif change in ("proposal", "authorization"): data.parent[change + "_sha256"] = "0" * 64
                elif change == "mode": data.parent["mode"] = "DD_1M"
                elif change == "uid": data.parent["uid"] = True
                elif change == "deadline_bool": data.parent["deadline_epoch"] = True
                elif change == "expired": data.parent["deadline_epoch"] = time.time() - 1
                elif change == "overlong": data.parent["deadline_epoch"] = time.time() + 200
                else: data.parent["extra"] = "no"
                data.save_parent()
                with data.patches(), patch.object(p.subprocess, "run") as run:
                    with self.assertRaises(AssertionError): data.invoke()
                    run.assert_not_called(); self.assertFalse(data.claim.exists())

    def test_parent_facts_hash_packages_process_and_floor_fence_client(self):
        for change in ("hash", "package", "uid", "process", "space"):
            with self.subTest(change=change), tempfile.TemporaryDirectory() as directory:
                data = StreamInputs(Path(directory))
                if change == "package": data.facts["packages"] = {}
                elif change == "uid": data.facts["uid_map"][q.APP] += 1
                elif change == "process": data.facts["processes"]["target"] = ["untrusted"]
                elif change == "space": data.facts["userdata"]["available_bytes"] = c.SOURCE_BYTES + q.contract.USERDATA_FLOOR - 1
                data.fp.write_bytes(encoded(data.facts))
                if change != "hash": data.parent["facts_sha256"] = q.sha(data.fp.read_bytes())
                else: data.parent["facts_sha256"] = "0" * 64
                data.save_parent()
                with data.patches(), patch.object(p.subprocess, "run") as run:
                    with self.assertRaises(AssertionError): data.invoke()
                    run.assert_not_called(); self.assertFalse(data.claim.exists())

    def test_shell_large_worker_requires_retained_binary_proof_before_claim(self):
        with tempfile.TemporaryDirectory() as directory:
            data = StreamInputs(Path(directory), "SHELL_CAT")
            (data.cohort / "shell-binary-proof.raw.txt").write_bytes(b"not a binary proof")
            with data.patches(), patch.object(p.subprocess, "run") as run:
                with self.assertRaises(c.TransferContractRefused): data.invoke()
                run.assert_not_called(); self.assertFalse(data.claim.exists())

    def test_hash_mismatch_parent_loss_and_source_mutation_prevent_success(self):
        for change in ("hash", "late_parent", "mutated"):
            with self.subTest(change=change), tempfile.TemporaryDirectory() as directory:
                data = StreamInputs(Path(directory))
                if change == "hash": data.value["source"]["sha256"] = "0" * 64
                def client(*args, **kwargs):
                    with data.source.open("ab") as out: out.write(b"mutation")
                    return SimpleNamespace(returncode=0)
                with data.patches(), patch.object(p.subprocess, "run", side_effect=client) as run:
                    with patch.object(p.os, "getppid", side_effect=[4242, 9999] if change == "late_parent" else [4242, 4242]):
                        with self.assertRaises(AssertionError): data.invoke()
                    self.assertEqual(run.call_count, 1 if change == "mutated" else 0)
                    self.assertTrue(data.claim.exists())

    def test_timeout_and_diagnostic_failure_preserve_original_exception_and_close_fd(self):
        with tempfile.TemporaryDirectory() as directory:
            data = StreamInputs(Path(directory)); original = subprocess.TimeoutExpired("fixed", 1); held = []
            def timeout(*args, **kwargs): held.append(kwargs["stdin"]); raise original
            with data.patches(), patch.object(p.subprocess, "run", side_effect=timeout), \
                 patch.object(p.r.source_trace, "SourceStreamTrace", side_effect=RuntimeError("private diagnostic")), \
                 redirect_stdout(io.StringIO()):
                with self.assertRaises(subprocess.TimeoutExpired) as error: data.invoke()
                self.assertIs(error.exception, original)
            self.assertTrue(held[0].closed)

    def test_summary_strict_types_and_no_destination_authority(self):
        self.assertEqual(p.parse_summary(encoded(summary("CAT")), "CAT"), summary("CAT"))
        for key, bad in (("version", True), ("mode", "DD_1M"), ("source_bytes", True), ("source_verified", 1),
                         ("client_returncode", False), ("remote_exit_status_known", True), ("destination_verified", True),
                         ("client_elapsed_ms", True), ("client_elapsed_ms", 180001), ("extra", "private")):
            with self.subTest(key=key, bad=bad), self.assertRaises(AssertionError):
                p.parse_summary(encoded(dict(summary("CAT"), **{key: bad})), "CAT")
        for raw in (b"", b"x" * 4097, b'{"version":1,"version":1}'):
            with self.subTest(raw=raw[:30]), self.assertRaises((AssertionError, ValueError)): p.parse_summary(raw, "CAT")

    def test_transfer_unknown_cleanup_nonzero_and_bad_summary_are_consumed_with_raw(self):
        for change in ("cleanup", "capture", "nonzero", "summary", "owner"):
            with self.subTest(change=change), tempfile.TemporaryDirectory() as directory:
                data = Inputs(Path(directory)); owner, lease = data.owner(); owner.created = True; owner.stage = "source-stream"
                result = completed(encoded(summary("CAT")), clean=change != "cleanup", code=2 if change == "nonzero" else 0,
                                   status="capture_failed" if change == "capture" else "completed")
                if change == "summary": result.stdout = b"bad-summary"
                def run(*args, **kwargs):
                    if change == "owner": lease.live = False
                    return result
                with patch.object(q.host, "run_process", side_effect=run) as client, \
                     patch.object(e, "process_identity", return_value={"pid": 1}):
                    with self.assertRaises((AssertionError, ValueError, RuntimeError)): owner.transfer("CAT")
                    self.assertEqual(owner.attempted, ["CAT"]); self.assertEqual(owner.verified, [])
                    self.assertEqual((owner.commands / "command-0001.stdout.bin").read_bytes(), result.stdout)
                    with self.assertRaises(AssertionError): owner.transfer("DD_1M")
                    self.assertEqual(client.call_count, 1)
                    self.assertEqual(client.call_args.kwargs["request"], p.STREAM_REQUEST + b"CAT\n10310\n")
                if change == "cleanup": self.assertFalse(owner.clean)

    def test_transfer_retention_failure_poisoned_after_raw_and_never_retries(self):
        with tempfile.TemporaryDirectory() as directory:
            data = Inputs(Path(directory)); owner, _ = data.owner(); owner.created = True; owner.stage = "source-stream"
            original_write = q.write_json
            def write(path, value):
                if Path(path).name == "command-0001.json": raise OSError("private retention error")
                return original_write(path, value)
            with patch.object(q.host, "run_process", return_value=completed(encoded(summary("CAT")))) as run, \
                 patch.object(q, "write_json", side_effect=write), patch.object(e, "process_identity", return_value={"pid": 1}):
                with self.assertRaises(OSError): owner.transfer("CAT")
                self.assertFalse(owner.clean); self.assertTrue((owner.commands / "command-0001.stdout.bin").exists())
                with self.assertRaises(AssertionError): owner.transfer("CAT")
                self.assertEqual(run.call_count, 1)

    def shell_owner(self, root):
        data = Inputs(root); owner, lease = data.owner(); owner.stage = "shell-gate"; owner.created = True
        owner.attempted = ["CAT", "DD_1M"]; owner.verified = list(owner.attempted)
        (owner.directory / "after-dd-1m-facts.json").write_bytes(encoded(data.facts))
        return owner, lease

    def test_shell_gate_exact_protocol_binary_request_and_raw_before_decode(self):
        with tempfile.TemporaryDirectory() as directory:
            owner, _ = self.shell_owner(Path(directory))
            results = [completed(b"shell_v2\ncmd\n"), completed(code=42), completed(), completed(encoded(summary("SHELL_BINARY")))]
            with patch.dict(p.os.environ, {}, clear=True), patch.object(q.host, "run_process", side_effect=results) as run, \
                 patch.object(e, "process_identity", return_value={"pid": 1}), \
                 patch.object(owner, "shell", return_value=proof_bytes("SHELL_CAT", binary=True)) as read:
                owner.shell_gate()
                self.assertTrue(owner.binary_verified); self.assertEqual(run.call_count, 4)
                calls = run.call_args_list
                self.assertEqual(calls[0].args[0][-1:], ["features"])
                for call in calls[1:3]:
                    self.assertEqual(call.args[0][7:11], ["shell", "-T", "-e", "none"])
                    self.assertLessEqual(call.kwargs["deadline"], 10); self.assertEqual(call.kwargs["max_output"], 4096)
                self.assertIn("_stream", calls[-1].args[0])
                self.assertEqual(calls[-1].kwargs["request"], p.STREAM_REQUEST + b"SHELL_BINARY\n10310\n")
                self.assertLessEqual(calls[-1].kwargs["deadline"], 180)
                self.assertEqual(json.loads((owner.directory / "shell-binary-transfer-v1.json").read_bytes()), summary("SHELL_BINARY"))
                self.assertEqual(read.call_args.args[0], c.binary_proof_command(UID))
                self.assertEqual((owner.directory / "shell-binary-proof.raw.txt").read_bytes(), proof_bytes("SHELL_CAT", binary=True))
                with self.assertRaises(AssertionError): owner.shell_gate()
                self.assertEqual(run.call_count, 4)

    def test_shell_features_exit_or_ownership_failure_stops_candidate_and_retains_raw(self):
        cases = (([completed(b"cmd\n")], 1), ([completed(b"shell_v2\nshell_v2\n")], 1),
                 ([completed(b"shell_v2\n", clean=False)], 1),
                 ([completed(b"shell_v2\n"), completed(code=0)], 2),
                 ([completed(b"shell_v2\n"), completed(b"unexpected", code=42)], 2))
        for results, count in cases:
            with self.subTest(count=count, first=results[0].stdout), tempfile.TemporaryDirectory() as directory:
                owner, _ = self.shell_owner(Path(directory))
                with patch.dict(p.os.environ, {}, clear=True), patch.object(q.host, "run_process", side_effect=results) as run, \
                     patch.object(owner, "shell") as proof:
                    with self.assertRaises(AssertionError): owner.shell_gate()
                    self.assertEqual(run.call_count, count); proof.assert_not_called(); self.assertFalse(owner.binary_verified)
                    self.assertEqual((owner.commands / "command-0001.stdout.bin").read_bytes(), results[0].stdout)
                    with self.assertRaises(AssertionError): owner.shell_gate()
                    self.assertEqual(run.call_count, count)
                    owner.stage = "source-stream"
                    with self.assertRaises(AssertionError): owner.transfer("SHELL_CAT")

    def test_bad_binary_proof_retained_but_no_large_shell_dispatch(self):
        with tempfile.TemporaryDirectory() as directory:
            owner, _ = self.shell_owner(Path(directory))
            with patch.dict(p.os.environ, {}, clear=True), \
                 patch.object(q.host, "run_process", side_effect=[completed(b"shell_v2\n"), completed(code=42), completed(), completed(encoded(summary("SHELL_BINARY")))]) as run, \
                 patch.object(e, "process_identity", return_value={"pid": 1}), \
                 patch.object(owner, "shell", return_value=b"bad-proof"):
                with self.assertRaises(c.TransferContractRefused): owner.shell_gate()
                self.assertEqual((owner.directory / "shell-binary-proof.raw.txt").read_bytes(), b"bad-proof")
                owner.stage = "source-stream"
                with self.assertRaises(AssertionError): owner.transfer("SHELL_CAT")
                self.assertEqual(run.call_count, 4); self.assertEqual(owner.verified, ["CAT", "DD_1M"])

    def test_binary_worker_reads_exact_fixed_768_bytes_through_regular_fd(self):
        with tempfile.TemporaryDirectory() as directory:
            data = StreamInputs(Path(directory), "SHELL_BINARY"); held = []
            def client(argv, **kwargs):
                stream = kwargs["stdin"]; held.append(stream)
                self.assertTrue(stat.S_ISREG(p.os.fstat(stream.fileno()).st_mode))
                self.assertEqual(Path(stream.name), data.cohort / "shell-binary-source-v1.bin")
                self.assertEqual(stream.tell(), 0); self.assertEqual(stream.read(), bytes(range(256)) * 3)
                self.assertEqual(argv[7:], ["shell", "-T", "-e", "none", shlex.join(c.binary_write_command(UID))])
                self.assertNotIn("TERM", kwargs["env"])
                self.assertEqual(kwargs["stdout"], subprocess.DEVNULL); self.assertEqual(kwargs["stderr"], subprocess.DEVNULL)
                self.assertGreater(kwargs["timeout"], 0); self.assertLessEqual(kwargs["timeout"], 150)
                return SimpleNamespace(returncode=0)
            with data.patches(), patch.object(p, "source_path", side_effect=AssertionError("caller source must not select binary bytes")) as source, \
                 patch.object(p.subprocess, "run", side_effect=client) as run:
                status, raw = data.invoke()
                self.assertEqual(status, 0); p.parse_summary(raw.encode("ascii"), "SHELL_BINARY")
                self.assertEqual(json.loads(raw)["source_bytes"], 768); source.assert_not_called()
                with self.assertRaises(FileExistsError): data.invoke()
                self.assertEqual(run.call_count, 1)
            self.assertTrue(held[0].closed)

    def test_binary_internal_selector_has_fixed_summary_and_barrier(self):
        self.assertNotIn("SHELL_BINARY", c.MODES)
        with self.assertRaises(AssertionError): p.mode_value("SHELL_BINARY")
        value = summary("SHELL_BINARY")
        self.assertEqual(p.parse_summary(encoded(value), "SHELL_BINARY"), value)
        for size in (True, 767, 769, c.SOURCE_BYTES):
            with self.subTest(size=size), self.assertRaises(AssertionError):
                p.parse_summary(encoded(dict(value, source_bytes=size)), "SHELL_BINARY")
        request = p.STREAM_REQUEST + b"SHELL_BINARY\n10310\n"
        with patch.object(p.sys, "stdin", SimpleNamespace(buffer=io.BytesIO(request))), \
             patch.object(p, "authorize", return_value={"synthetic": True}) as authorize, \
             patch.object(p, "stream_authorized", return_value=0) as stream:
            self.assertEqual(p.stream_worker("proposal", "grant", "evidence"), 0)
            authorize.assert_called_once_with("proposal", "grant", "evidence")
            stream.assert_called_once_with({"synthetic": True}, "SHELL_BINARY", UID, "proposal", "grant", "evidence")

    def test_binary_parent_facts_and_original_lease_still_fence_before_creation(self):
        for change in ("parent", "facts", "lease"):
            with self.subTest(change=change), tempfile.TemporaryDirectory() as directory:
                data = StreamInputs(Path(directory), "SHELL_BINARY")
                if change == "parent": data.parent["mode"] = "SHELL_CAT"; data.save_parent()
                if change == "facts": data.fp.write_bytes(encoded(dict(data.facts, processes={"target": ["active"], "test_helper": []})))
                if change == "lease": data.lease.live = False
                with data.patches(), patch.object(p.subprocess, "run") as run:
                    with self.assertRaises((AssertionError, RuntimeError)): data.invoke()
                    run.assert_not_called(); self.assertFalse(data.claim.exists())
                    self.assertFalse((data.cohort / "shell-binary-source-v1.bin").exists())

    def test_binary_source_create_only_hash_and_post_fd_mutation_refuse(self):
        for change in ("existing", "hash", "mutated"):
            with self.subTest(change=change), tempfile.TemporaryDirectory() as directory:
                data = StreamInputs(Path(directory), "SHELL_BINARY")
                binary = data.cohort / "shell-binary-source-v1.bin"
                if change == "existing": binary.write_bytes(b"existing caller bytes")
                def client(*args, **kwargs):
                    with binary.open("ab") as out: out.write(b"changed")
                    return SimpleNamespace(returncode=0)
                with data.patches(), patch.object(p.subprocess, "run", side_effect=client) as run, \
                     patch.object(c, "BINARY_SHA256", "0" * 64 if change == "hash" else c.BINARY_SHA256):
                    with self.assertRaises((AssertionError, FileExistsError)): data.invoke()
                    self.assertTrue(data.claim.exists())
                    self.assertEqual(run.call_count, 1 if change == "mutated" else 0)
                    if change == "existing": self.assertEqual(binary.read_bytes(), b"existing caller bytes")

    def test_binary_owner_requires_consumed_shell_gate_and_does_not_advance_large_modes(self):
        for change in ("stage", "gate", "prior", "success", "unknown"):
            with self.subTest(change=change), tempfile.TemporaryDirectory() as directory:
                owner, _ = self.shell_owner(Path(directory)); owner.stage = "shell-gate-binary"; owner.shell_gate_attempted = True
                if change == "stage": owner.stage = "source-stream"
                if change == "gate": owner.shell_gate_attempted = False
                if change == "prior": owner.attempted = ["CAT"]
                value = completed(encoded(summary("SHELL_BINARY")), clean=change != "unknown")
                with patch.object(q.host, "run_process", return_value=value) as run, \
                     patch.object(e, "process_identity", return_value={"pid": 1}):
                    if change == "success": self.assertEqual(owner.transfer("SHELL_BINARY"), summary("SHELL_BINARY"))
                    else:
                        with self.assertRaises(AssertionError): owner.transfer("SHELL_BINARY")
                    self.assertEqual(run.call_count, 1 if change in ("success", "unknown") else 0)
                    self.assertEqual(owner.verified, ["CAT", "DD_1M"])
                    if change in ("success", "unknown"):
                        self.assertEqual(owner.attempted, ["CAT", "DD_1M"]); self.assertTrue(owner.binary_stream_attempted)
                        with self.assertRaises(AssertionError): owner.transfer("SHELL_BINARY")
                        self.assertEqual(run.call_count, 1)
                    self.assertFalse(owner.binary_verified)

    def test_binary_unknown_cleanup_stops_before_guest_proof_or_large_shell(self):
        with tempfile.TemporaryDirectory() as directory:
            owner, _ = self.shell_owner(Path(directory))
            results = [completed(b"shell_v2\n"), completed(code=42), completed(),
                       completed(encoded(summary("SHELL_BINARY")), clean=False)]
            with patch.dict(p.os.environ, {}, clear=True), patch.object(q.host, "run_process", side_effect=results) as run, \
                 patch.object(e, "process_identity", return_value={"pid": 1}), patch.object(owner, "shell") as proof:
                with self.assertRaises(AssertionError): owner.shell_gate()
                self.assertFalse(owner.clean); self.assertFalse(owner.binary_verified); proof.assert_not_called()
                self.assertEqual((owner.commands / "command-0004.stdout.bin").read_bytes(), results[-1].stdout)
                with self.assertRaises(AssertionError): owner.shell_gate()
                owner.stage = "source-stream"
                with self.assertRaises(AssertionError): owner.transfer("SHELL_CAT")
                self.assertEqual(run.call_count, 4)

    def cohort(self, root, fail=None):
        owner, _ = Inputs(root).owner(); events = []
        def facts(label, hashes):
            events.append(label)
            if fail == label: raise RuntimeError("bounded synthetic facts failure")
            return {"userdata": {"available_bytes": len(c.MODES) * c.SOURCE_BYTES + q.contract.USERDATA_FLOOR}}
        def shell(command, **kwargs):
            if owner.stage == "probe-root": owner.created = True; events.append("create"); return b""
            mode = owner.stage[len("proof-"):]; events.append("proof-" + mode)
            return b"bad-proof" if fail == "proof-" + mode else proof_bytes(mode)
        def transfer(mode):
            events.append("transfer-" + mode); owner.attempted.append(mode); return summary(mode)
        def gate():
            events.append("shell-gate")
            if fail == "shell-gate": raise AssertionError("synthetic binary refusal")
            owner.binary_verified = True
        owner.facts, owner.shell, owner.transfer, owner.shell_gate = facts, shell, transfer, gate
        return owner, events

    def test_proof_and_fresh_facts_precede_every_next_mode_and_shell_gate(self):
        with tempfile.TemporaryDirectory() as directory:
            owner, events = self.cohort(Path(directory)); result = p.run_cohort(owner)
            self.assertEqual(events, ["continued-before", "create", "transfer-CAT", "proof-CAT", "after-cat",
                                      "transfer-DD_1M", "proof-DD_1M", "after-dd-1m", "shell-gate",
                                      "transfer-SHELL_CAT", "proof-SHELL_CAT", "after-shell-cat"])
            self.assertEqual([row["mode"] for row in result["controls"]], list(c.MODES))
            self.assertFalse(result["model_copied"]); self.assertFalse(result["sdk_invoked"]); self.assertFalse(result["story_mutated"])

    def test_failed_proof_facts_or_binary_gate_dispatches_no_later_mode(self):
        for failure, expected in (("proof-CAT", ["CAT"]), ("after-cat", ["CAT"]),
                                  ("proof-DD_1M", ["CAT", "DD_1M"]), ("shell-gate", ["CAT", "DD_1M"])):
            with self.subTest(failure=failure), tempfile.TemporaryDirectory() as directory:
                owner, events = self.cohort(Path(directory), failure)
                with self.assertRaises((AssertionError, RuntimeError, c.TransferContractRefused)): p.run_cohort(owner)
                self.assertEqual(owner.attempted, expected)
                self.assertNotIn("transfer-SHELL_CAT", events)
                if expected == ["CAT"]: self.assertNotIn("transfer-DD_1M", events)

    def test_process_boundary_is_ordered_empty_only_and_sticky(self):
        uids = {q.APP: UID, q.TEST: UID + 1}
        boundary = p.ProcessBoundary()
        with patch.object(q.contract, "parse_processes", return_value={"passive": [], "owned": []}):
            self.assertEqual(boundary.observe(b"fixed empty census", uids, label="continued-before", stage="before", methods=0),
                             {"target": [], "test_helper": []})
            with self.assertRaises(AssertionError): boundary.observe(b"", uids, label="after-dd-1m", stage="after", methods=0)
            with self.assertRaises(AssertionError): boundary.observe(b"", uids, label="after-cat", stage="after", methods=0)
        for parsed in ({"passive": ["foreign"], "owned": []}, {"passive": [], "owned": ["ours"]}):
            with self.subTest(parsed=parsed), patch.object(q.contract, "parse_processes", return_value=parsed):
                with self.assertRaises(AssertionError): p.ProcessBoundary().observe(b"", uids, label="continued-before", stage="before", methods=0)

    def test_outer_owner_lease_floor_and_cleanup_capture_are_not_success(self):
        for change in ("floor", "cleanup", "capture", "worker", "status"):
            with self.subTest(change=change), tempfile.TemporaryDirectory() as directory:
                data = Inputs(Path(directory)); lease = fixture.fixture.Lease(data.value)
                lease.descriptor["deadline_epoch"] = time.time() + (919 if change == "floor" else 1000)
                value = {"status": "child_exited", "worker_returncode": 0, "cleanup_complete": True, "output_capture_complete": True}
                if change == "cleanup": value["cleanup_complete"] = False
                if change == "capture": value["output_capture_complete"] = False
                if change == "worker": value["worker_returncode"] = 2
                if change == "status": value["status"] = "deadline"
                with patch.object(p, "authorize", return_value=data.value), patch.object(q, "open_lease", return_value=lease), \
                     patch.object(e, "supervise", return_value=value) as supervise, redirect_stdout(io.StringIO()):
                    if change == "floor":
                        with self.assertRaises(AssertionError): p.run_owned(data.pp, data.ap, data.root)
                        supervise.assert_not_called()
                    else:
                        self.assertEqual(p.run_owned(data.pp, data.ap, data.root), 2)
                        self.assertEqual(supervise.call_args.args[1], p.REQUEST)
                        self.assertEqual(supervise.call_args.args[3], 900)
                        self.assertEqual(json.loads((data.root / "receipt-owned-result-v1.json").read_bytes()), value)


if __name__ == "__main__":
    unittest.main()
