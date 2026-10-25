"""Pure cancellation-controller checks: no Android, SDK, weights or builds.

Copyright 2026 LocalLore contributors. SPDX-License-Identifier: Apache-2.0
"""
from contextlib import redirect_stdout
import copy
import io
import json
from pathlib import Path
import shlex
import sys
import tempfile
import time
from types import SimpleNamespace
import unittest
from unittest.mock import patch
from scripts.tests import test_receipt_real_candidate as old

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "benchmarks"))
import receipt_real_cancellation as n
r, q = n.r, n.q
encoded = old.encoded
UIDS = {q.APP: 10310, q.TEST: 10311}


def trace(phase, count=2):
    number = count if phase == "RECOVER" else 1
    counts = {key: 0 for key in n.worker_trace.EVENTS}
    if phase == "SAMPLE": counts.update(SEND_ENTERED=1, SEND_RETURNED=1, MESSAGE_RETURNED=1)
    elif phase == "CANCEL":
        counts.update(SEND_ENTERED=1, SEND_RETURNED=1, MESSAGE_RETURNED=2, DONE_ENTERED=1, DONE_RETURNED=1,
            CANCEL_ENTERED=1, CANCEL_RETURNED=1, DRAIN_SETTLED=1, CONVERSATION_CLOSE_ENTERED=1,
            CONVERSATION_CLOSE_KNOWN=1, ENGINE_CLOSE_ENTERED=1, ENGINE_CLOSE_KNOWN=1)
    else:
        for key in ("CONVERSATION_CREATE_ENTERED", "CONVERSATION_CREATE_RETURNED", "SEND_ENTERED", "SEND_RETURNED",
                "DONE_ENTERED", "DONE_RETURNED", "DRAIN_SETTLED", "CONVERSATION_CLOSE_ENTERED", "CONVERSATION_CLOSE_KNOWN"):
            counts[key] = number
        counts.update(MESSAGE_RETURNED=5, ENGINE_CLOSE_ENTERED=1, ENGINE_CLOSE_KNOWN=1)
    roles = ["DIRECTOR"] * (number - 1) + ["NARRATOR"] if phase == "RECOVER" else ["DIRECTOR"]
    return {"version": 2, "counts": counts, "saturated": [], "last_ms": {key: 3 if value else None for key, value in counts.items()},
        "snapshot_ms": 10, "time_saturated": False, "creations_total": number, "creations_saturated": False,
        "creations": [dict(ordinal=i, role=role, entered_ms=1, returned_ms=2, failed_ms=None, failure="NONE")
            for i, role in enumerate(roles, 1)]}


def proof(phase, prior=None):
    value = {key: value for key, value in old.proof("PLAY").items() if key in r.COMMON_KEYS}
    value.update(phase=phase, pid={"CANCEL": 601, "RECOVER": 602, "REOPEN": 603}[phase],
        start={"CANCEL": 1000, "RECOVER": 2000, "REOPEN": 3000}[phase],
        sdk_invoked=phase != "REOPEN", checks={key: True for key in n.PHASES[phase][4]},
        prior_pid=601, prior_start=1000, revision=0 if phase == "CANCEL" else 1, receipt_count=0 if phase == "CANCEL" else 1)
    value["prior_" + n.PRIOR[phase] + "_sha256"] = "c" * 64
    if prior is not None:
        value.update(prior_pid=prior["pid"], prior_start=prior["start"])
        value["prior_" + n.PRIOR[phase] + "_sha256"] = q.sha(encoded(prior))
    if phase == "CANCEL":
        value.update(sample_worker_trace_sha256=q.sha(encoded(trace("SAMPLE"))), worker_trace_sha256=q.sha(encoded(trace("CANCEL"))))
    else: value["receipt_sha256"] = "d" * 64
    if phase == "RECOVER": value.update(repairs=0, fallback=False, worker_trace_sha256=q.sha(encoded(trace("RECOVER"))))
    return value


def transcript(phase, passed=True):
    cls, method = "org.locallore.app." + n.PHASES[phase][1], n.PHASES[phase][2]
    rows = []
    for code in (1, 0 if passed else -2):
        fields = {"class": cls, "current": "1", "id": "AndroidJUnitRunner", "numtests": "1", "stream": "." if code == 0 else "", "test": method}
        rows += ["INSTRUMENTATION_STATUS: " + key + "=" + value for key, value in fields.items()]
        rows.append("INSTRUMENTATION_STATUS_CODE: " + str(code))
    summary = "OK (1 test)" if passed else "FAILURES!!!\nTests run: 1, Failures: 1"
    return ("\n".join(rows) + "\nINSTRUMENTATION_RESULT: stream=\n\nTime: 0.1\n\n" + summary + "\n\nINSTRUMENTATION_CODE: -1\n").encode()


def candidate(root):
    value = old.proposal(root)
    env = Path(value["environment_proposal_path"])
    env.write_bytes(encoded({"memory_mib": 8192, "host_available_memory_min": 12*r.GIB, "cores": 4}))
    value["bindings"][str(env.resolve())] = q.sha(env.read_bytes())
    p = old.proof("SOURCE_PREFLIGHT")
    facts = {"packages": value["apk_sha256"], "uid_map": UIDS, "processes": {"target": [], "test_helper": []},
        "volume": {"id": "public:8,1", "uuid": "ABCD-1234"}, "userdata": {"available_bytes": q.contract.USERDATA_FLOOR+r.MODEL_BYTES}}
    result = {"scope": r.SCOPE, "phase": "preflight", "status": "observed", "failure": None,
        "clients_cleaned": True, "owner_live": True, "running_sha256": value["running_sha256"],
        "instrumentation_commands": 1, "result": {"proof": p, "after": facts}}
    owned = {"status": "child_exited", "worker_returncode": 0, "cleanup_complete": True, "output_capture_complete": True}
    previous = {}
    for name, body in (("proof", p), ("facts", facts), ("result", result), ("owned_result", owned)):
        f = root / ("preflight-" + name + ".json"); f.write_bytes(encoded(body))
        previous[name] = {"path": str(f.resolve()), "sha256": q.sha(f.read_bytes())}
        value["bindings"][str(f.resolve())] = q.sha(f.read_bytes())
    value.update(scope=n.SCOPE, phase="candidate", preflight=previous,
        human_consent={"reference": "synthetic_consent", "action": "local_copy_and_sdk_fresh_receipt_emulator",
            "model_sha256": r.MODEL_SHA, "destination_package": q.APP},
        source={"path": str(root / "never-opened-synthetic-source"), "bytes": r.MODEL_BYTES, "sha256": r.MODEL_SHA})
    for name in n.SOURCE_FILES:
        path = (q.ROOT / name).resolve(); value["bindings"][str(path)] = q.sha(path.read_bytes())
    return value


def owner_fixture(root):
    value = candidate(root); lease = old.fixture.Lease(value)
    lease.descriptor["deadline_epoch"] = time.time()+1500
    return n.Owner(value, lease), lease


def client(raw=b"", clean=True):
    return SimpleNamespace(status="completed", returncode=0, cleanup_complete=clean, stdout=raw, stderr_bytes=0, elapsed_ms=1)


class CancellationTests(unittest.TestCase):
    def test_closed_three_proofs_and_fixed_single_method_selection(self):
        self.assertEqual([len(v[4]) for v in n.PHASES.values()], [21, 19, 14])
        self.assertEqual([v[3] for v in n.PHASES.values()], [170000, 170000, 120000])
        for phase in n.PHASES:
            self.assertEqual(n.parse_proof(encoded(proof(phase)), phase, UIDS[q.APP]), proof(phase))
            self.assertEqual(n.parse_runner(transcript(phase), phase)["passed"], 1)
            with self.assertRaises(AssertionError): n.parse_runner(old.transcript("REOPEN"), phase)
            self.assertEqual(n.parse_runner(transcript(phase).replace(b"Time: 0.1",b"Time: 120"),phase)["passed"],1)
            with self.assertRaises(AssertionError): n.parse_runner(transcript(phase).replace(b"Time: 0.1",b"Time: 120.001"),phase)

    def test_proof_unknown_private_fields_types_bounds_and_missing_join_refuse(self):
        for phase in n.PHASES:
            for key, invalid in (("version", True), ("sdk_invoked", 1), ("model_bytes", True), ("uid", True),
                    ("source_verify_bytes", 1), ("pid", 0), ("memory_available_before", 4*r.GIB-1),
                    ("external_free_after", 2*r.GIB-1), ("userdata_free_after", q.contract.USERDATA_FLOOR-1),
                    ("elapsed_ms", n.PHASES[phase][3]+1), ("revision", 9), ("receipt_count", True)):
                changed = proof(phase); changed[key] = invalid
                with self.subTest(phase=phase, key=key), self.assertRaises(AssertionError): n.parse_proof(encoded(changed), phase, UIDS[q.APP])
            changed = proof(phase); changed["private_error"] = "PRIVATE_CANARY"
            with self.assertRaises(AssertionError): n.parse_proof(encoded(changed), phase, UIDS[q.APP])
            changed = proof(phase); changed["checks"][next(iter(changed["checks"]))] = 1
            with self.assertRaises(AssertionError): n.parse_proof(encoded(changed), phase, UIDS[q.APP])
            with self.assertRaises(AssertionError): n.parse_proof(encoded(proof(phase))+b" "*4096, phase, UIDS[q.APP])
        changed = proof("CANCEL"); del changed["checks"]["original_response_joined"]
        with self.assertRaises(AssertionError): n.parse_proof(encoded(changed), "CANCEL", UIDS[q.APP])
        changed = proof("CANCEL"); changed["receipt_sha256"] = "0"*64
        with self.assertRaises(AssertionError): n.parse_proof(encoded(changed), "CANCEL", UIDS[q.APP])

    def test_complete_hash_chain_process_instance_and_receipt_continuity(self):
        prior = old.proof("IMPORT")
        for phase in n.PHASES:
            current = proof(phase, prior)
            n.link_proofs(prior, encoded(prior), current)
            for key, bad in (("prior_pid", 1), ("prior_start", 1), ("prior_"+n.PRIOR[phase]+"_sha256", "0"*64), ("uid", 10311)):
                wrong = copy.deepcopy(current); wrong[key] = bad
                with self.assertRaises(AssertionError): n.link_proofs(prior, encoded(prior), wrong)
            if phase != "CANCEL":
                wrong = copy.deepcopy(current); wrong.update(pid=prior["pid"], start=prior["start"])
                with self.assertRaises(AssertionError): n.link_proofs(prior, encoded(prior), wrong)
            if phase == "REOPEN":
                wrong = copy.deepcopy(current); wrong["receipt_sha256"] = "0"*64
                with self.assertRaises(AssertionError): n.link_proofs(prior, encoded(prior), wrong)
            prior = current

    def test_positive_trace_observations_are_closed_not_resource_authority(self):
        sample = trace("SAMPLE"); n.trace_predicates(sample, "SAMPLE")
        n.trace_predicates(trace("CANCEL"), "CANCEL", sample)
        error = trace("CANCEL"); error["counts"].update(DONE_ENTERED=0, DONE_RETURNED=0, ERROR_ENTERED=1, ERROR_RETURNED=1)
        n.trace_predicates(error, "CANCEL", sample)
        for count in (2, 3): n.trace_predicates(trace("RECOVER", count), "RECOVER")
        # The plain wire parser imposes no positive-phase success policy.
        zero = trace("SAMPLE"); zero["counts"]["MESSAGE_RETURNED"] = 0; zero["last_ms"]["MESSAGE_RETURNED"] = None
        n.worker_trace.parse_worker_trace(encoded(zero))
        with self.assertRaises(AssertionError): n.trace_predicates(zero, "SAMPLE")

    def test_missed_window_cancel_or_recovery_observation_stops(self):
        mutations = [("SAMPLE", "DONE_ENTERED", 1), ("SAMPLE", "SEND_RETURNED", 0),
            ("CANCEL", "CANCEL_RETURNED", 0), ("CANCEL", "ENGINE_CLOSE_KNOWN", 0), ("CANCEL", "DONE_RETURNED", 0),
            ("CANCEL", "MESSAGE_RETURNED", 0), ("RECOVER", "CONVERSATION_CREATE_RETURNED", 1),
            ("RECOVER", "ERROR_ENTERED", 1), ("RECOVER", "UNCERTAIN", 1)]
        for phase, key, value in mutations:
            changed = trace(phase); changed["counts"][key] = value
            with self.subTest(phase=phase, key=key), self.assertRaises(AssertionError): n.trace_predicates(changed, phase, trace("SAMPLE"))
        for phase in ("SAMPLE", "CANCEL", "RECOVER"):
            for key in ("time_saturated", "creations_saturated"):
                changed = trace(phase); changed[key] = True
                with self.assertRaises(AssertionError): n.trace_predicates(changed, phase, trace("SAMPLE"))
            changed = trace(phase); changed["creations"][-1]["role"] = "DIRECTOR" if phase == "RECOVER" else "NARRATOR"
            with self.assertRaises(AssertionError): n.trace_predicates(changed, phase, trace("SAMPLE"))

    def test_cancel_pair_keeps_monotonic_observation_history_not_causality(self):
        sample=trace("SAMPLE")
        for mode in ("clock","creation","count","last","missing-last"):
            changed=trace("CANCEL")
            if mode=="clock":changed["snapshot_ms"]=9
            if mode=="creation":changed["creations"][0]["returned_ms"]=3
            if mode=="count":
                sample=trace("SAMPLE");sample["counts"]["ADMISSION_ENTERED"]=2;sample["last_ms"]["ADMISSION_ENTERED"]=3
            if mode=="last":changed["last_ms"]["SEND_ENTERED"]=2
            if mode=="missing-last":changed["last_ms"]["SEND_ENTERED"]=None
            with self.subTest(mode=mode),self.assertRaises(AssertionError):n.trace_predicates(changed,"CANCEL",sample)
            sample=trace("SAMPLE")
        changed=trace("CANCEL");changed["snapshot_ms"]=11;changed["last_ms"]["SEND_ENTERED"]=4
        n.trace_predicates(changed,"CANCEL",sample)

    def proof_reader(self, root, phase, change=None):
        value = proof(phase); files = {}
        for p in n.PHASES:
            stem = n.PHASES[p][0]
            files[stem+"-ready-v1.txt"] = b""; files[stem+"-v1.json"] = encoded(value if p == phase else proof(p))
            for i, name in enumerate(n.TRACES[p]): files[name] = encoded(trace("SAMPLE" if p == "CANCEL" and i == 0 else p))
            if p == phase: break
        if change: change(files)
        calls = []
        def shell(command, **kwargs):
            calls.append(command)
            if command == n.namespace_command(UIDS[q.APP]): return ("\n".join(n.PROOF_ROOT+"/"+name for name in files)+"\n").encode()
            for name, raw in files.items():
                if command == n.proof_command(name, UIDS[q.APP]): return raw
            raise AssertionError("Unexpected fixed proof read")
        return SimpleNamespace(directory=root, uid_map=UIDS, shell=shell), calls

    def test_progressive_manifests_and_trace_hashes_accept_exact_files(self):
        for phase, count in zip(n.PHASES, (4, 7, 9)):
            with tempfile.TemporaryDirectory() as directory:
                owner, calls = self.proof_reader(Path(directory), phase)
                value, raw = n.read_proof(owner, phase)
                self.assertEqual(value, proof(phase)); self.assertEqual(raw, encoded(value))
                self.assertEqual(len(calls), 3+len(n.TRACES[phase]))
                self.assertEqual(count, len({n.PROOF_ROOT+"/"+name for p in list(n.PHASES)[:list(n.PHASES).index(phase)+1]
                    for name in (n.PHASES[p][0]+"-v1.json", n.PHASES[p][0]+"-ready-v1.txt", *n.TRACES[p])}))

    def test_manifest_drift_or_bad_trace_hash_refuses_before_later_reads(self):
        for mode in ("missing", "extra", "trace", "legacy-trace", "proof"):
            with self.subTest(mode=mode), tempfile.TemporaryDirectory() as directory:
                def change(files):
                    if mode == "missing": del files["cancel-worker-v2.json"]
                    if mode == "extra": files["PRIVATE_CANARY"] = b""
                    if mode == "trace": files["cancel-worker-v2.json"] = encoded(trace("SAMPLE"))
                    if mode == "legacy-trace":
                        legacy={"version":1,"counts":trace("CANCEL")["counts"],"saturated":[]}
                        files["cancel-worker-v2.json"]=encoded(legacy)
                        value=json.loads(files["cancel-v1.json"]);value["worker_trace_sha256"]=q.sha(encoded(legacy))
                        files["cancel-v1.json"]=encoded(value)
                    if mode == "proof": files["cancel-v1.json"] = b"{}"
                owner, calls = self.proof_reader(Path(directory), "CANCEL", change)
                with self.assertRaises((AssertionError, KeyError)): n.read_proof(owner, "CANCEL")
                if mode in ("missing", "extra"): self.assertEqual(len(calls), 1)
                if mode == "proof": self.assertEqual((Path(directory)/"cancel-proof.raw.json").read_bytes(), b"{}")
                self.assertFalse((Path(directory)/"cancel-proof-v1.json").exists())

    def test_fixed_proof_paths_uid_and_nonlink_size_guards(self):
        command = n.proof_command("cancel-worker-v2.json", 10310)
        self.assertEqual(command[:4], ("run-as", q.APP, "sh", "-c"))
        for expected in ("test ! -L", "-eq 10310", "-gt 0", "-le 4096"): self.assertIn(expected, command[4])
        self.assertIn("-eq 0", n.proof_command("cancel-ready-v1.txt", 10310)[4])
        for name in ("../model.litertlm", "cancel-v1.json; echo private", "import-v1.json", "PRIVATE_CANARY"):
            with self.assertRaises(AssertionError): n.proof_command(name, 10310)
        for uid in (True, 0, -1, "10310"):
            with self.assertRaises(AssertionError): n.proof_command("cancel-v1.json", uid)
        self.assertNotIn("rm ", command[4]); self.assertNotIn("force-stop", command[4])

    def test_boundary_is_five_steps_sticky_and_never_rebinds_helper(self):
        raw = b"PID UID NAME\n"; helper = b"PID UID NAME\n900 10311 " + q.TEST.encode() + b"\n"
        boundary = n.ContinuedBoundary({"target": [], "test_helper": []})
        for index, (label, stage, methods) in enumerate(boundary.observations):
            boundary.observe(helper if index in (1, 2) else raw, UIDS, label=label, stage=stage, methods=methods)
        with self.assertRaises(AssertionError): boundary.observe(raw, UIDS, label="after-reopen", stage="after", methods=4)
        boundary = n.ContinuedBoundary({"target": [], "test_helper": []})
        boundary.observe(raw, UIDS, label="continued-before", stage="before", methods=0)
        boundary.observe(helper, UIDS, label="after-import", stage="after", methods=1)
        boundary.observe(raw, UIDS, label="after-cancel", stage="after", methods=2)
        with self.assertRaises(AssertionError): boundary.observe(helper, UIDS, label="after-recover", stage="after", methods=3)
        with self.assertRaises(AssertionError): boundary.observe(raw, UIDS, label="after-recover", stage="after", methods=3)

    def test_foreign_or_target_process_and_wrong_schedule_refuse(self):
        for raw in (b"PID UID NAME\n1 10310 "+q.APP.encode()+b"\n", b"PID UID NAME\n1 10312 org.locallore.foreign\n"):
            boundary = n.ContinuedBoundary({"target": [], "test_helper": []})
            with self.assertRaises(AssertionError): boundary.observe(raw, UIDS, label="continued-before", stage="before", methods=0)
            self.assertTrue(boundary.refused)
        boundary = n.ContinuedBoundary({"target": [], "test_helper": []})
        with self.assertRaises(AssertionError): boundary.observe(b"PID UID NAME\n", UIDS, label="after-cancel", stage="after", methods=2)
        self.assertTrue(boundary.refused)

    def test_admission_reuses_old_preflight_scope_and_only_four_core_candidate(self):
        with tempfile.TemporaryDirectory() as directory:
            value = candidate(Path(directory))
            with patch.object(q, "APK_HASHES", value["apk_sha256"]), patch.object(r, "source_path") as source:
                self.assertTrue(n.validate_proposal(value)); source.assert_called_once()
                for field, bad in (("scope", r.SCOPE), ("phase", "preflight"), ("allow_device_calls", True)):
                    changed = copy.deepcopy(value); changed[field] = bad
                    with self.assertRaises(AssertionError): n.validate_proposal(changed)
                for cores in (2, True):
                    env = Path(value["environment_proposal_path"])
                    env.write_bytes(encoded({"memory_mib":8192,"host_available_memory_min":12*r.GIB,"cores":cores}))
                    value["bindings"][str(env.resolve())] = q.sha(env.read_bytes())
                    with self.assertRaises(AssertionError): n.validate_proposal(value)

    def test_scope_does_not_rewrite_bound_prior_result_or_accept_missing_source_binding(self):
        with tempfile.TemporaryDirectory() as directory:
            value = candidate(Path(directory)); path = Path(value["preflight"]["result"]["path"])
            body = json.loads(path.read_bytes()); body["scope"] = n.SCOPE; path.write_bytes(encoded(body))
            value["bindings"][str(path.resolve())] = q.sha(path.read_bytes()); value["preflight"]["result"]["sha256"] = q.sha(path.read_bytes())
            with patch.object(q, "APK_HASHES", value["apk_sha256"]), patch.object(r, "source_path"):
                with self.assertRaises(AssertionError): n.validate_proposal(value)
        with tempfile.TemporaryDirectory() as directory:
            value = candidate(Path(directory)); value["bindings"].pop(str((q.ROOT/"benchmarks/receipt_real_cancellation.py").resolve()))
            with patch.object(q, "APK_HASHES", value["apk_sha256"]), patch.object(r, "source_path"):
                with self.assertRaises(AssertionError): n.validate_proposal(value)

    def test_authority_is_exact_hash_bound_and_all_sensitive_flags_true(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory); value = candidate(root); p, a = root/"p.json", root/"a.json"; p.write_bytes(encoded(value))
            grant = {"version":1,"proposal_sha256":q.sha(p.read_bytes()),"allow_device_calls":True,
                "root_go_pending":False,"allow_local_weight_copy":True,"allow_sdk_calls":True}
            with patch.object(q, "APK_HASHES", value["apk_sha256"]), patch.object(r, "source_path"):
                a.write_bytes(encoded(grant)); self.assertEqual(n.authorize(p,a,root),value)
                for key, bad in (("proposal_sha256","0"*64),("allow_sdk_calls",False),("allow_local_weight_copy",False),
                        ("allow_device_calls",False),("root_go_pending",True),("version",True)):
                    a.write_bytes(encoded(dict(grant,**{key:bad})))
                    with self.assertRaises(AssertionError): n.authorize(p,a,root)

    def test_actual_owner_steps_source_script_and_namespace_absence_are_fixed(self):
        with tempfile.TemporaryDirectory() as directory:
            owner, _ = owner_fixture(Path(directory))
            self.assertEqual(owner.STREAM_SCRIPT, Path(n.__file__).resolve())
            self.assertNotEqual(owner.STREAM_SCRIPT, r.Owner.STREAM_SCRIPT)
            self.assertEqual([s[1] for s in owner.instrumentation_steps], ["instrument-IMPORT","instrument-CANCEL","instrument-RECOVER","instrument-REOPEN"])
            owner.stage="after";owner.methods=1
            with patch.object(q.host,"run_process",return_value=client()) as run:
                owner.check_cancel_namespace_absent()
                with self.assertRaises(AssertionError): owner.check_cancel_namespace_absent()
                self.assertEqual(run.call_count,1)
            self.assertTrue(owner.namespace_absence_attempted)

    def test_raw_first_unknown_cleanup_or_owner_loss_stops_later_dispatch(self):
        for mode in ("cleanup","owner"):
            with tempfile.TemporaryDirectory() as directory:
                owner, lease = owner_fixture(Path(directory));owner.stage="instrument-CANCEL";owner.methods=1
                def run(*args,**kwargs):
                    if mode=="owner":lease.live=False
                    return client(b"bounded failure",mode!="cleanup")
                with patch.object(q.host,"run_process",side_effect=run) as send:
                    with self.assertRaises((AssertionError,RuntimeError)):owner.shell(n.selection("CANCEL"))
                    with self.assertRaises((AssertionError,RuntimeError)):owner.shell(n.selection("RECOVER"))
                    self.assertEqual(send.call_count,1)
                self.assertEqual((owner.commands/"command-0001.stdout.bin").read_bytes(),b"bounded failure")

    def test_remaining_aggregate_clips_client_and_exhaustion_has_no_later_action(self):
        with tempfile.TemporaryDirectory() as directory:
            owner, _ = owner_fixture(Path(directory));owner.stage="instrument-CANCEL";owner.methods=1;owner.until=time.monotonic()+.25
            with patch.object(q.host,"run_process",return_value=client()) as send:
                owner.shell(n.selection("CANCEL"),deadline=180)
                self.assertLessEqual(send.call_args.kwargs["deadline"],.25)
                owner.stage="instrument-RECOVER";owner.until=time.monotonic()-1
                with self.assertRaises(AssertionError):owner.shell(n.selection("RECOVER"),deadline=180)
                self.assertEqual(send.call_count,1)
                self.assertEqual(owner.methods,3)  # Attempts are not dispatched-client evidence.
                self.assertEqual(owner.count,1)
                self.assertFalse((owner.commands/"command-0002.json").exists())

    def test_failed_runner_or_failed_worker_record_never_reads_proof(self):
        for phase in n.PHASES:
            with tempfile.TemporaryDirectory() as directory:
                owner=SimpleNamespace(directory=Path(directory),shell=lambda *args,**kwargs:transcript(phase,False))
                with patch.object(n,"read_proof") as read:
                    with self.assertRaises(AssertionError):n.run_selected(owner,phase)
                    read.assert_not_called()
        for phase in ("CANCEL","RECOVER"):
            with tempfile.TemporaryDirectory() as directory:
                wire=n.worker_trace.PREFIX.encode()+encoded(trace("RECOVER"))+b"\n"+n.worker_trace.STATUS.encode()+b"\n"
                owner=SimpleNamespace(directory=Path(directory),shell=lambda *args,**kwargs:wire+transcript(phase,False))
                with patch.object(n,"read_proof") as read:
                    with self.assertRaises(AssertionError):n.run_selected(owner,phase)
                    read.assert_not_called()
                self.assertTrue((Path(directory)/(phase.lower()+"-failure-worker-v2.json")).exists())
                owner.shell=lambda *a,**kw:wire+transcript(phase)
                with self.assertRaises(AssertionError):n.run_selected(owner,phase)
        with tempfile.TemporaryDirectory() as directory:
            wire=n.worker_trace.PREFIX.encode()+encoded(trace("RECOVER"))+b"\n"+n.worker_trace.STATUS.encode()+b"\n"
            owner=SimpleNamespace(directory=Path(directory),shell=lambda *a,**kw:wire+transcript("REOPEN",False))
            with patch.object(n,"read_proof") as read:
                with self.assertRaises(AssertionError):n.run_selected(owner,"REOPEN")
                read.assert_not_called()
            self.assertEqual(list(Path(directory).iterdir()),[])

    def test_stream_worker_requires_barrier_and_uses_root_authorized_transfer(self):
        value={"scope":n.SCOPE}
        with patch.object(sys,"stdin",SimpleNamespace(buffer=io.BytesIO(r.STREAM_REQUEST+b"10310\n"))), \
             patch.object(n,"authorize",return_value=value) as auth, patch.object(r,"stream_authorized",return_value=0) as transfer:
            self.assertEqual(n.stream_worker("p","a","e"),0)
            auth.assert_called_once_with("p","a","e");transfer.assert_called_once_with(value,10310,"p","a","e")
        with patch.object(sys,"stdin",SimpleNamespace(buffer=io.BytesIO(b"wrong\n"))), patch.object(n,"authorize") as auth:
            with self.assertRaises(AssertionError):n.stream_worker("p","a","e")
            auth.assert_not_called()

    def run_flow(self, root, mode="pass"):
        owner, _ = owner_fixture(root); events=[]
        imported=old.proof("IMPORT")
        imported["prior_preflight_sha256"]=q.sha(Path(owner.proposal["preflight"]["proof"]["path"]).read_bytes())
        prior=[imported]
        def boot(): owner.stage="before";events.append("boot")
        def facts(label, packages):
            self.assertEqual(packages,q.APK_HASHES);events.append(label)
            if mode=="uid-drift" and label=="after-cancel":raise AssertionError("Synthetic UID drift")
            if mode=="overhead" and label=="after-import":owner.until=time.monotonic()-1
            return {"userdata":{"available_bytes":q.contract.USERDATA_FLOOR+r.MODEL_BYTES-(1 if mode=="capacity" else 0)}}
        def selected(actual, phase):
            self.assertIs(actual,owner)
            command=r.selection(phase) if phase=="IMPORT" else n.selection(phase)
            self.assertEqual(owner.instrumentation_steps[owner.methods],(command,"instrument-"+phase,owner.methods))
            owner.methods+=1;owner.stage="instrument-"+phase;events.append(phase)
            if mode=="cancel-fails" and phase=="CANCEL":raise AssertionError("Synthetic failed cancellation")
            if phase=="IMPORT":return imported,encoded(imported)
            value=proof(phase,prior[0])
            if mode=="same-process" and phase=="RECOVER":value.update(pid=prior[0]["pid"],start=prior[0]["start"])
            prior[0]=value
            return value,encoded(value)
        def host(*args,**kwargs):
            events.append("namespace")
            self.assertEqual(args[0][-2:],["shell",shlex.join(n.namespace_command(UIDS[q.APP],True))])
            return client(clean=mode!="cleanup")
        with patch.object(owner,"wait_boot",side_effect=boot),patch.object(owner,"check_guest_cpu_profile",side_effect=lambda:events.append("cpu")), \
             patch.object(owner,"facts",side_effect=facts),patch.object(owner,"transfer",side_effect=lambda:events.append("copy") or {}), \
             patch.object(r,"run_selected",side_effect=selected),patch.object(n,"run_selected",side_effect=selected),patch.object(q.host,"run_process",side_effect=host):
            if mode=="pass":
                result=n.run_cohort(owner)
                self.assertEqual(list(result["proofs"]),["IMPORT","CANCEL","RECOVER","REOPEN"])
                self.assertTrue(result["real_sdk_cancellation_observed"])
            else:
                with self.assertRaises(AssertionError):n.run_cohort(owner)
        return events

    def test_mocked_cohort_preserves_import_cancel_recover_reopen_order(self):
        with tempfile.TemporaryDirectory() as directory:
            self.assertEqual(self.run_flow(Path(directory)),["boot","cpu","continued-before","copy","IMPORT", "after-import",
                "namespace","CANCEL","after-cancel","RECOVER","after-recover","REOPEN","after-reopen"])

    def test_cohort_capacity_cleanup_overhead_and_failed_phase_stop_later_work(self):
        for mode in ("capacity","cleanup","overhead","cancel-fails","same-process","uid-drift"):
            with self.subTest(mode=mode),tempfile.TemporaryDirectory() as directory:
                events=self.run_flow(Path(directory),mode)
                if mode=="capacity":self.assertNotIn("copy",events);self.assertNotIn("IMPORT",events)
                if mode in ("cleanup","overhead"):self.assertNotIn("CANCEL",events)
                if mode=="overhead":self.assertNotIn("namespace",events)
                if mode in ("cancel-fails","uid-drift"):self.assertNotIn("RECOVER",events)
                self.assertNotIn("REOPEN",events)

    def test_outer_run_preserves_900_920_limits_and_child_status(self):
        for mode in ("pass","child","cleanup","capture","deadline"):
            with self.subTest(mode=mode),tempfile.TemporaryDirectory() as directory:
                root=Path(directory);p,a=root/"p",root/"a";p.write_bytes(b"p");a.write_bytes(b"a")
                lease=SimpleNamespace(descriptor={"deadline_epoch":1019 if mode=="deadline" else 1020},check=lambda:None)
                result={"status":"child_exited","worker_returncode":2 if mode=="child" else 0,
                    "cleanup_complete":mode!="cleanup","output_capture_complete":mode!="capture"}
                with patch.object(n,"authorize",return_value={}),patch.object(q,"open_lease",return_value=lease), \
                     patch.object(n.time,"time",return_value=100),patch.object(n.environment,"supervise",return_value=result) as run,redirect_stdout(io.StringIO()):
                    if mode=="deadline":
                        with self.assertRaises(AssertionError):n.run_owned(p,a,root)
                        run.assert_not_called()
                    else:
                        self.assertEqual(n.run_owned(p,a,root),0 if mode=="pass" else 2)
                        self.assertEqual(run.call_args.args[1],n.REQUEST);self.assertEqual(run.call_args.args[3],900)
                        with self.assertRaises(FileExistsError):n.run_owned(p,a,root)
                        self.assertEqual(run.call_count,1)


if __name__ == "__main__": unittest.main()
