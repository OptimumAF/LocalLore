"""Adversarial real-candidate admission tests using tiny original data and mocks.

Copyright 2026 LocalLore contributors. SPDX-License-Identifier: Apache-2.0
"""
from contextlib import ExitStack, redirect_stdout
import copy
import io
import json
import os
from pathlib import Path
import shlex
import sys
import tempfile
import time
from types import SimpleNamespace
import unittest
from unittest.mock import patch

from scripts.tests import test_receipt_real_candidate as fixture

r, q = fixture.r, fixture.q


def grant(value, proposal_raw, *, promote=False):
    return {"version": 1, "proposal_sha256": q.sha(proposal_raw), "allow_device_calls": True,
            "root_go_pending": False, "allow_local_weight_copy": promote, "allow_sdk_calls": promote}


def candidate(root):
    """Valid linked metadata; source_path is mocked separately, never weight IO."""
    value = fixture.proposal(root)
    source = root / "synthetic-not-model-input.txt"
    source.write_bytes(r.PROBE_PATH.read_bytes())
    value.update(phase="candidate", source={"path": str(source), "bytes": r.MODEL_BYTES, "sha256": r.MODEL_SHA},
        human_consent={"reference": "synthetic_explicit_scope_v1", "action": "local_copy_and_sdk_fresh_receipt_emulator",
                       "model_sha256": r.MODEL_SHA, "destination_package": q.APP})
    facts = {"packages": dict(value["apk_sha256"]), "uid_map": {q.APP: 10310, q.TEST: 10311},
             "processes": {"target": [], "test_helper": []}, "volume": {"id": "public:253,80", "uuid": "0000-0000"},
             "userdata": {"available_bytes": q.contract.USERDATA_FLOOR + r.MODEL_BYTES}}
    proof = fixture.proof("SOURCE_PREFLIGHT")
    result = {"scope": r.SCOPE, "phase": "preflight", "status": "observed", "failure": None,
              "clients_cleaned": True, "owner_live": True, "running_sha256": value["running_sha256"],
              "instrumentation_commands": 1, "result": {"proof": proof, "after": facts}}
    owned = {"status": "child_exited", "worker_returncode": 0, "cleanup_complete": True, "output_capture_complete": True}
    value["preflight"] = {}
    for key, body in (("result", result), ("facts", facts), ("proof", proof), ("owned_result", owned)):
        path = root / ("prior-" + key + ".json")
        path.write_bytes(fixture.encoded(body))
        digest = q.sha(path.read_bytes())
        value["preflight"][key] = {"path": str(path), "sha256": digest}
        value["bindings"][str(path.resolve())] = digest
    return value


class StreamFixture:
    def __init__(self, root):
        self.root = root
        self.value = fixture.proposal(root)
        self.lease = fixture.fixture.Lease(self.value)
        self.cohort = root / "cohort"
        self.cohort.mkdir()
        self.proposal, self.authorization = root / "stream-proposal.json", root / "stream-auth.json"
        self.proposal.write_bytes(fixture.encoded(self.value))
        self.authorization.write_bytes(fixture.encoded(grant(self.value, self.proposal.read_bytes())))
        self.identity = {"pid": 4242, "creation_filetime": 30, "executable": sys.executable}
        self.facts = {"packages": dict(self.value["apk_sha256"]), "uid_map": {q.APP: 10310, q.TEST: 10311},
                      "processes": {"target": [], "test_helper": []},
                      "userdata": {"available_bytes": q.contract.USERDATA_FLOOR + r.PROBE_BYTES}}
        self.fact_path = self.cohort / "installed-facts.json"
        self.fact_path.write_bytes(fixture.encoded(self.facts))
        self.parent = {"version": 1, "parent": self.identity, "proposal_sha256": q.sha(self.proposal.read_bytes()),
            "authorization_sha256": q.sha(self.authorization.read_bytes()), "phase": "preflight", "uid": 10310,
            "facts_sha256": q.sha(self.fact_path.read_bytes()), "deadline_epoch": time.time() + 90}
        self.parent_path = self.cohort / "stream-parent-v1.json"
        self.parent_path.write_bytes(fixture.encoded(self.parent))

    def rewrite_parent(self):
        self.parent_path.write_bytes(fixture.encoded(self.parent))

    def rewrite_facts(self):
        self.fact_path.write_bytes(fixture.encoded(self.facts))
        self.parent["facts_sha256"] = q.sha(self.fact_path.read_bytes())
        self.rewrite_parent()

    def mocks(self, stack, child=None, identity=None, actual_parent=4242, source=None):
        stack.enter_context(patch.object(r, "authorize", return_value=self.value))
        stack.enter_context(patch.object(q, "open_lease", return_value=self.lease))
        stack.enter_context(patch.object(q, "APK_HASHES", self.value["apk_sha256"]))
        stack.enter_context(patch.object(r.os, "getppid", return_value=actual_parent))
        stack.enter_context(patch.object(r.environment, "process_identity", side_effect=identity or
            (lambda pid: self.identity if pid == 4242 else dict(self.identity, pid=pid))))
        stack.enter_context(patch.object(r.sys, "stdin", SimpleNamespace(buffer=io.BytesIO(r.STREAM_REQUEST + b"10310\n"))))
        if source is not None:
            stack.enter_context(patch.object(r, "source_path", return_value=source))
        return stack.enter_context(patch.object(r.subprocess, "run", side_effect=child,
                                                return_value=SimpleNamespace(returncode=0)))

    def invoke(self):
        with redirect_stdout(io.StringIO()) as output:
            status = r.stream_worker(self.proposal, self.authorization, self.root)
        return status, output.getvalue()


class ReceiptRealStreamGuardTests(unittest.TestCase):
    def test_stream_claim_binds_parent_and_replay_cannot_spawn_twice(self):
        with tempfile.TemporaryDirectory() as directory, ExitStack() as stack:
            state = StreamFixture(Path(directory))
            def child(argv, **kwargs):
                self.assertTrue((state.cohort / "stream-worker-claimed-v1.json").is_file())
                claim = q.contract.strict_json((state.cohort / "stream-worker-claimed-v1.json").read_bytes())
                self.assertEqual(claim["parent_sha256"], q.sha(state.parent_path.read_bytes()))
                self.assertEqual(kwargs["stdin"].read(), r.PROBE_PATH.read_bytes())
                self.assertGreater(kwargs["timeout"], 0)
                self.assertLessEqual(kwargs["timeout"], 150)
                return SimpleNamespace(returncode=0)
            run = state.mocks(stack, child=child)
            status, output = state.invoke()
            self.assertEqual(status, 0)
            self.assertFalse(json.loads(output)["destination_verified"])
            stack.enter_context(patch.object(r.sys, "stdin", SimpleNamespace(buffer=io.BytesIO(r.STREAM_REQUEST + b"10310\n"))))
            with self.assertRaises(FileExistsError):
                state.invoke()
            self.assertEqual(run.call_count, 1)

    def test_orphan_live_unrelated_parent_and_replaced_identity_refuse_before_claim(self):
        for mode in ("absent", "unrelated", "replaced", "executable"):
            with self.subTest(mode=mode), tempfile.TemporaryDirectory() as directory, ExitStack() as stack:
                state = StreamFixture(Path(directory))
                if mode == "absent":
                    state.parent_path.unlink()
                def identity(pid):
                    if mode == "replaced":
                        return dict(state.identity, creation_filetime=31)
                    if mode == "executable":
                        return dict(state.identity, executable="wrong-python.exe")
                    return state.identity
                run = state.mocks(stack, identity=identity, actual_parent=7 if mode == "unrelated" else 4242)
                with self.assertRaises((AssertionError, FileNotFoundError)):
                    state.invoke()
                run.assert_not_called()
                self.assertFalse((state.cohort / "stream-worker-claimed-v1.json").exists())

    def test_closed_parent_phase_uid_deadline_and_hash_fields_refuse_before_child(self):
        changes = ({"version": True}, {"phase": "candidate"}, {"uid": True}, {"uid": 10312},
                   {"deadline_epoch": time.time() - 1}, {"deadline_epoch": time.time() + 300},
                   {"deadline_epoch": True}, {"proposal_sha256": "0" * 64},
                   {"authorization_sha256": "0" * 64}, {"facts_sha256": "0" * 64}, {"unexpected": True})
        for change in changes:
            with self.subTest(change=change), tempfile.TemporaryDirectory() as directory, ExitStack() as stack:
                state = StreamFixture(Path(directory)); state.parent.update(change); state.rewrite_parent()
                run = state.mocks(stack)
                with self.assertRaises(AssertionError):
                    state.invoke()
                run.assert_not_called()
                self.assertFalse((state.cohort / "stream-worker-claimed-v1.json").exists())

    def test_mismatched_current_facts_or_capacity_refuse_before_stream_claim(self):
        for mode in ("package", "uid", "target", "capacity"):
            with self.subTest(mode=mode), tempfile.TemporaryDirectory() as directory, ExitStack() as stack:
                state = StreamFixture(Path(directory))
                if mode == "package": state.facts["packages"][q.APP] = "0" * 64
                elif mode == "uid": state.facts["uid_map"][q.APP] = 10312
                elif mode == "target": state.facts["processes"]["target"] = [{"pid": 1, "uid": 10310, "name": q.APP}]
                else: state.facts["userdata"]["available_bytes"] -= 1
                state.rewrite_facts()
                run = state.mocks(stack)
                with self.assertRaises(AssertionError): state.invoke()
                run.assert_not_called()
                self.assertFalse((state.cohort / "stream-worker-claimed-v1.json").exists())

    def test_wrong_held_fd_digest_and_size_refuse_before_child_but_keep_claim(self):
        for content in (b"x" * 61, b"Original shorter stream fixture"):
            with self.subTest(size=len(content)), tempfile.TemporaryDirectory() as directory, ExitStack() as stack:
                state = StreamFixture(Path(directory)); source = state.root / "tiny-source.txt"; source.write_bytes(content)
                run = state.mocks(stack, source=source)
                with self.assertRaises(AssertionError): state.invoke()
                run.assert_not_called()
                self.assertTrue((state.cohort / "stream-worker-claimed-v1.json").is_file())
                self.assertEqual(source.read_bytes(), content)

    def test_parent_is_rechecked_after_hash_and_cannot_disappear_before_child(self):
        with tempfile.TemporaryDirectory() as directory, ExitStack() as stack:
            state = StreamFixture(Path(directory)); lookups = []
            def identity(pid):
                if pid == 4242:
                    lookups.append(pid)
                    if len(lookups) > 1:
                        raise r.environment.EnvironmentRefused("parent_lost")
                return dict(state.identity, pid=pid)
            run = state.mocks(stack, identity=identity)
            with self.assertRaises(r.environment.EnvironmentRefused): state.invoke()
            run.assert_not_called()
            self.assertEqual(len(lookups), 2)

    def test_actual_parent_relationship_is_rechecked_before_spawn(self):
        with tempfile.TemporaryDirectory() as directory, ExitStack() as stack:
            state = StreamFixture(Path(directory))
            run = state.mocks(stack)
            stack.enter_context(patch.object(r.os, "getppid", side_effect=[4242, 7]))
            with self.assertRaises(AssertionError): state.invoke()
            run.assert_not_called()

    def test_source_mutation_after_client_does_not_emit_verified_summary(self):
        with tempfile.TemporaryDirectory() as directory, ExitStack() as stack:
            state = StreamFixture(Path(directory)); source = state.root / "tiny-source.txt"; source.write_bytes(r.PROBE_PATH.read_bytes())
            def child(*args, **kwargs):
                with source.open("ab") as changed: changed.write(b"changed")
                return SimpleNamespace(returncode=0)
            run = state.mocks(stack, source=source, child=child)
            with redirect_stdout(io.StringIO()) as output, self.assertRaises(AssertionError):
                r.stream_worker(state.proposal, state.authorization, state.root)
            self.assertEqual(output.getvalue(), "")
            self.assertEqual(run.call_count, 1)

    def test_stream_barrier_bad_requests_refuse_before_authorization(self):
        for request in (b"", r.STREAM_REQUEST, r.STREAM_REQUEST + b"true\n", r.STREAM_REQUEST + b"10310\nextra"):
            with self.subTest(request=request), patch.object(r.sys, "stdin", SimpleNamespace(buffer=io.BytesIO(request))), patch.object(r, "authorize") as auth:
                with self.assertRaises(AssertionError): r.stream_worker("p", "a", "e")
                auth.assert_not_called()

    def test_candidate_requires_real_linked_preflight_and_explicit_consent(self):
        with tempfile.TemporaryDirectory() as directory, ExitStack() as stack:
            root = Path(directory); value = candidate(root)
            stack.enter_context(patch.object(q, "APK_HASHES", value["apk_sha256"]))
            source = stack.enter_context(patch.object(r, "source_path", return_value=Path(value["source"]["path"])))
            self.assertTrue(r.validate_proposal(value))
            for change in (None, {}, dict(value["human_consent"], reference="spaces refuse"),
                           dict(value["human_consent"], action="preflight_only"),
                           dict(value["human_consent"], model_sha256="0" * 64),
                           dict(value["human_consent"], destination_package=q.TEST)):
                source.reset_mock()
                with self.subTest(consent=change), self.assertRaises((AssertionError, TypeError)):
                    r.validate_proposal(dict(value, human_consent=change))
                source.assert_called_once_with(value["source"], "candidate")

    def test_candidate_authorization_never_promotes_preflight_flags_or_wrong_digest(self):
        with tempfile.TemporaryDirectory() as directory, ExitStack() as stack:
            root = Path(directory); value = candidate(root)
            stack.enter_context(patch.object(q, "APK_HASHES", value["apk_sha256"]))
            stack.enter_context(patch.object(r, "source_path", return_value=Path(value["source"]["path"])))
            proposal, authorization = root / "candidate.json", root / "candidate-auth.json"
            proposal.write_bytes(fixture.encoded(value))
            permitted = grant(value, proposal.read_bytes(), promote=True)
            authorization.write_bytes(fixture.encoded(permitted))
            self.assertEqual(r.authorize(proposal, authorization, root), value)
            for change in ({"allow_local_weight_copy": False}, {"allow_sdk_calls": False},
                           {"allow_sdk_calls": 1}, {"proposal_sha256": "0" * 64}, {"root_go_pending": True}):
                authorization.write_bytes(fixture.encoded(dict(permitted, **change)))
                with self.subTest(change=change), self.assertRaises(AssertionError):
                    r.authorize(proposal, authorization, root)

    def test_owned_phase_budget_barrier_and_capture_cleanup_refusals(self):
        for phase, seconds in (("preflight", 180), ("candidate", 900)):
            for failure in (None, "capture", "cleanup", "child"):
                with self.subTest(phase=phase, failure=failure), tempfile.TemporaryDirectory() as directory, ExitStack() as stack:
                    root = Path(directory); value = {"phase": phase}
                    proposal, authorization = root / "p.json", root / "a.json"
                    proposal.write_bytes(b"synthetic admitted proposal"); authorization.write_bytes(b"synthetic grant")
                    lease = SimpleNamespace(descriptor={"deadline_epoch": time.time() + seconds + 60}, check=lambda: None)
                    result = {"status": "child_exited", "worker_returncode": 0, "cleanup_complete": True, "output_capture_complete": True}
                    if failure == "capture": result["output_capture_complete"] = False
                    if failure == "cleanup": result["cleanup_complete"] = False
                    if failure == "child": result["worker_returncode"] = 2
                    stack.enter_context(patch.object(r, "authorize", return_value=value))
                    stack.enter_context(patch.object(q, "open_lease", return_value=lease))
                    supervise = stack.enter_context(patch.object(r.environment, "supervise", return_value=result))
                    with redirect_stdout(io.StringIO()):
                        self.assertEqual(r.run_owned(proposal, authorization, root), 0 if failure is None else 2)
                    args = supervise.call_args.args
                    self.assertEqual(args[1], r.REQUEST)
                    self.assertEqual(args[3], seconds)
                    self.assertEqual(args[0][1:4], ["-B", "-E", str(Path(r.__file__).resolve())])
                    self.assertEqual(q.contract.strict_json((root / "receipt-owned-start-v1.json").read_bytes())["deadline_seconds"], seconds)
                    self.assertTrue((root / "receipt-owned-result-v1.json").is_file())

    def test_owned_phase_requires_remaining_supervisor_lifetime_before_writes(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            lease = SimpleNamespace(descriptor={"deadline_epoch": time.time() + 919}, check=lambda: None)
            with patch.object(r, "authorize", return_value={"phase": "candidate"}), patch.object(q, "open_lease", return_value=lease), patch.object(r.environment, "supervise") as run:
                with self.assertRaises(AssertionError): r.run_owned(root / "p", root / "a", root)
            run.assert_not_called()
            self.assertEqual(list(root.iterdir()), [])

    def test_mock_candidate_import_play_reopen_and_failure_stop_without_reinstall(self):
        for failed in (None, "IMPORT", "PLAY"):
            with self.subTest(failed=failed), tempfile.TemporaryDirectory() as directory, ExitStack() as stack:
                root = Path(directory); value = candidate(root)
                lease = fixture.fixture.Lease(value); owner = r.Owner(value, lease)
                owner.proposal_path, owner.authorization_path = root / "p", root / "a"
                owner.proposal_path.write_bytes(b"synthetic proposal"); owner.authorization_path.write_bytes(b"synthetic grant")
                transport = fixture.fixture.Transport(value, lease); transport.installs = 2
                phases = []
                previous_raw = Path(value["preflight"]["proof"]["path"]).read_bytes()
                proofs = {}
                for phase, key in (("IMPORT", "preflight"), ("PLAY", "import"), ("REOPEN", "play")):
                    body = fixture.proof(phase); body["prior_" + key + "_sha256"] = q.sha(previous_raw)
                    previous_raw = fixture.encoded(body); proofs[phase] = previous_raw
                def dispatch(argv, **kwargs):
                    if argv[0] == sys.executable:
                        result = fixture.stream_result()
                        body = json.loads(result.stdout); body["source_bytes"] = r.MODEL_BYTES
                        result.stdout = fixture.encoded(body)
                        return result
                    if argv[3] == "shell":
                        op = tuple(shlex.split(argv[4]))
                        for phase in ("IMPORT", "PLAY", "REOPEN"):
                            if op == r.selection(phase):
                                phases.append(phase); transport.instruments += 1
                                raw = fixture.transcript(phase)
                                if phase == failed: raw = raw.replace(b"STATUS_CODE: 0", b"STATUS_CODE: -2")
                                return SimpleNamespace(status="completed", returncode=0, cleanup_complete=True, stdout=raw, stderr_bytes=0, elapsed_ms=1)
                            if op == r.proof_command(phase, 10310, True): raw = b""
                            elif op == r.proof_command(phase, 10310): raw = proofs[phase]
                            else: continue
                            return SimpleNamespace(status="completed", returncode=0, cleanup_complete=True, stdout=raw, stderr_bytes=0, elapsed_ms=1)
                    return transport(argv, **kwargs)
                stack.enter_context(patch.object(q, "APK_HASHES", value["apk_sha256"]))
                stack.enter_context(patch.object(q.host, "run_process", side_effect=dispatch))
                stack.enter_context(patch.object(q.shutil, "disk_usage", return_value=SimpleNamespace(free=20 * r.GIB)))
                stack.enter_context(patch.object(r.environment, "process_identity", return_value={"pid": 42, "creation_filetime": 3, "executable": sys.executable}))
                if failed:
                    with self.assertRaises(AssertionError): r.run_cohort(owner)
                    self.assertEqual(phases, ["IMPORT"] if failed == "IMPORT" else ["IMPORT", "PLAY"])
                    self.assertFalse((owner.directory / (r.PHASES["REOPEN"][0] + "-instrumentation-v1.json")).exists())
                else:
                    result = r.run_cohort(owner)
                    self.assertEqual(phases, ["IMPORT", "PLAY", "REOPEN"])
                    self.assertEqual(set(result["proofs"]), {"IMPORT", "PLAY", "REOPEN"})
                self.assertEqual(owner.installs, {q.APP: 0, q.TEST: 0})
                self.assertFalse(any(command[3] == "install" for command, _ in transport.calls))


if __name__ == "__main__":
    unittest.main()
