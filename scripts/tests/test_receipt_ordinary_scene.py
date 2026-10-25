"""Pure ordinary-route host qualification checks. All clients/SDKs are mocked.

Copyright 2026 LocalLore contributors. SPDX-License-Identifier: Apache-2.0
"""
from contextlib import redirect_stdout
import copy
import importlib.util
import io
import json
from pathlib import Path
import sys
import tempfile
import time
from types import SimpleNamespace
import unittest
from unittest.mock import patch
from scripts.tests import test_receipt_real_cancellation as api
from scripts.tests import test_litert_send_trace as send_wire

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "benchmarks"))
import receipt_ordinary_scene as s
n, r, q = s.n, s.r, s.q
encoded, UIDS = api.encoded, api.UIDS


def trace(phase):
    value = api.trace("RECOVER")
    if phase in ("GUARDS", "ORDINARY_REOPEN"):
        value.update(counts={k: 0 for k in s.worker_trace.EVENTS}, last_ms={k: None for k in s.worker_trace.EVENTS},
            creations=[], creations_total=0, snapshot_ms=9)
    return value


def proof(phase, prior=None):
    value = {k: v for k, v in api.old.proof("PLAY").items() if k in r.COMMON_KEYS}
    index = list(s.PHASES).index(phase)
    value.update(phase=phase, pid=701+index, start=1000*(index+1), sdk_invoked=phase!="ORDINARY_REOPEN",
        checks={k: True for k in s.PHASES[phase][4]}, prior_pid=600+index, prior_start=500,
        revision=1 if phase=="ORDINARY_START" else 2, receipt_count=1 if phase=="ORDINARY_START" else 2,
        receipts_sha256=("b" if phase=="ORDINARY_START" else "c")*64, gift_receipt_sha256="d"*64,
        worker_trace_sha256=q.sha(encoded(trace(phase))))
    value["prior_"+s.PRIOR_KEY[phase]+"_sha256"]="e"*64
    if prior is not None:
        value.update(prior_pid=prior["pid"], prior_start=prior["start"])
        value["prior_"+s.PRIOR_KEY[phase]+"_sha256"]=q.sha(encoded(prior))
    if phase!="ORDINARY_START": value["dialogue_receipt_sha256"]="f"*64
    if phase!="ORDINARY_REOPEN": value.update(repairs=0, fallback=False)
    if phase=="ORDINARY_DIALOGUE": value["guards_worker_trace_sha256"]=q.sha(encoded(trace("GUARDS")))
    return value


def transcript(phase, passed=True):
    return api.transcript("RECOVER", passed).replace(n.PHASES["RECOVER"][1].encode(), s.PHASES[phase][1].encode()).replace(
        n.PHASES["RECOVER"][2].encode(), s.PHASES[phase][2].encode())


def candidate(root):
    value=api.candidate(root); value["scope"]=s.SCOPE
    for name in s.SOURCE_FILES:
        path=(q.ROOT/name).resolve(); value["bindings"][str(path)]=q.sha(path.read_bytes())
    return value


def owner_fixture(root):
    value=candidate(root); lease=api.old.fixture.Lease(value)
    lease.descriptor["deadline_epoch"]=time.time()+1500
    return s.Owner(value,lease),lease


class OrdinaryControllerTests(unittest.TestCase):
    def test_closed_122_checks_exact_phases_and_independent_caps(self):
        self.assertEqual([len(v[4]) for v in s.PHASES.values()],[28,43,23])
        self.assertEqual(sum(len(v[4]) for v in s.PHASES.values())+12+16,122)
        self.assertEqual([v[3] for v in s.PHASES.values()],[170000,170000,120000])
        for phase in s.PHASES:
            self.assertEqual(s.parse_proof(encoded(proof(phase)),phase,UIDS[q.APP]),proof(phase))
            self.assertEqual(s.parse_runner(transcript(phase),phase)["passed"],1)
            self.assertEqual(s.parse_runner(transcript(phase).replace(b"Time: 0.1",b"Time: 120"),phase)["passed"],1)
            with self.assertRaises(AssertionError):s.parse_runner(transcript(phase).replace(b"Time: 0.1",b"Time: 120.001"),phase)
            for old in (api.transcript("RECOVER"),api.old.transcript("PLAY")):
                with self.assertRaises(AssertionError):s.parse_runner(old,phase)

    def test_missing_checks_private_fields_types_and_limits_refuse(self):
        for phase in s.PHASES:
            for key in s.PHASES[phase][4]:
                changed=proof(phase);changed["checks"][key]=False
                with self.subTest(phase=phase,key=key),self.assertRaises(AssertionError):s.parse_proof(encoded(changed),phase,UIDS[q.APP])
            for key,wrong in (("version",True),("uid",True),("source_verify_bytes",1),("source_import_opened",1),
                    ("sdk_invoked",phase=="ORDINARY_REOPEN"),("publication_native_invoked",True),("revision",True),
                    ("receipt_count",0),("elapsed_ms",s.PHASES[phase][3]+1),("memory_available_before",4*r.GIB-1),
                    ("external_free_after",2*r.GIB-1),("userdata_free_after",q.contract.USERDATA_FLOOR-1),
                    ("gift_receipt_sha256","PRIVATE_CANARY")):
                changed=proof(phase);changed[key]=wrong
                with self.subTest(phase=phase,key=key),self.assertRaises(AssertionError) as caught:s.parse_proof(encoded(changed),phase,UIDS[q.APP])
                self.assertNotIn("PRIVATE_CANARY",str(caught.exception))
            for changed in (dict(proof(phase),private_path="PRIVATE_CANARY"),dict(proof(phase),phase="PLAY")):
                with self.assertRaises(AssertionError):s.parse_proof(encoded(changed),phase,UIDS[q.APP])
            with self.assertRaises(AssertionError):s.parse_proof(encoded(proof(phase))+b" "*4096,phase,UIDS[q.APP])
            raw=encoded(proof(phase)).replace(b'"version":1',b'"version":1,"version":1')
            with self.assertRaises((AssertionError,ValueError)):s.parse_proof(raw,phase,UIDS[q.APP])

    def test_every_phase_changes_process_and_exact_receipts_survive(self):
        prior=api.old.proof("IMPORT")
        for phase in s.PHASES:
            value=proof(phase,prior);s.link_proofs(prior,encoded(prior),value)
            for changed in (dict(value,pid=prior["pid"],start=prior["start"]),
                    dict(value,**{"prior_"+s.PRIOR_KEY[phase]+"_sha256":"0"*64}),dict(value,prior_pid=5)):
                with self.assertRaises(AssertionError):s.link_proofs(prior,encoded(prior),changed)
            # PID reuse is permitted when the actual process start identity changes.
            s.link_proofs(prior,encoded(prior),dict(value,pid=prior["pid"],start=prior["start"]+1))
            if phase!="ORDINARY_START":
                with self.assertRaises(AssertionError):s.link_proofs(prior,encoded(prior),dict(value,gift_receipt_sha256="0"*64))
            if phase=="ORDINARY_REOPEN":
                for key in ("receipts_sha256","dialogue_receipt_sha256"):
                    with self.assertRaises(AssertionError):s.link_proofs(prior,encoded(prior),dict(value,**{key:"0"*64}))
            prior=value

    def test_fixed_namespace_no_old_proof_selection_or_global_mutation(self):
        before=(copy.deepcopy(n.PHASES),n.PROOF_ROOT,n.SCOPE,copy.deepcopy(r.PHASES))
        for phase in s.PHASES:
            self.assertIn(s.PHASES[phase][1],s.selection(phase)[6])
            for name in (s.PHASES[phase][0]+"-v1.json",s.PHASES[phase][0]+"-ready-v1.txt",*s.TRACES[phase]):
                command=s.proof_command(name,10310)
                self.assertEqual(command[:4],("run-as",q.APP,"sh","-c"))
                self.assertIn(s.PROOF_ROOT,command[4]);self.assertNotIn(n.PROOF_ROOT,command[4]);self.assertNotIn(r.PROOF_ROOT,command[4])
                for text in ("test ! -L","-eq 10310","-le 4096"):self.assertIn(text,command[4])
        for name in ("cancel-v1.json","../model.litertlm","IMPORT","start-v1.json; cat private"):
            with self.assertRaises(AssertionError):s.proof_command(name,10310)
        for absent in (False,True):self.assertIn(s.PROOF_ROOT,s.namespace_command(10310,absent)[4])
        self.assertEqual(before,(n.PHASES,n.PROOF_ROOT,n.SCOPE,r.PHASES))

    def test_positive_roles_zero_worker_and_guard_history_are_distinct(self):
        for phase in s.PHASES:
            s.trace_predicates(trace(phase),phase,trace("GUARDS") if phase=="ORDINARY_DIALOGUE" else None)
        for mode in ("work","saturation","creation","last-time","private-role","history"):
            zero=trace("GUARDS");positive=trace("ORDINARY_DIALOGUE")
            if mode=="work":zero["counts"]["ADMISSION_ENTERED"]=1;zero["last_ms"]["ADMISSION_ENTERED"]=1
            if mode=="saturation":zero["time_saturated"]=True;zero["snapshot_ms"]=180000
            if mode=="creation":zero["creations_total"]=1;zero["creations"]=positive["creations"][:1]
            if mode=="last-time":zero["last_ms"]["MESSAGE_RETURNED"]=1
            if mode=="private-role":positive["creations"][0]["role"]="NARRATOR"
            if mode=="history":zero["snapshot_ms"]=positive["snapshot_ms"]+1
            with self.subTest(mode=mode),self.assertRaises(AssertionError):
                s.trace_predicates(zero,"GUARDS");s.trace_predicates(positive,"ORDINARY_DIALOGUE",zero)
        # Elapsed time by itself is not SDK work.
        zero=trace("ORDINARY_REOPEN");zero["snapshot_ms"]=179999;s.trace_predicates(zero,"ORDINARY_REOPEN")
        with self.assertRaises(AssertionError):s.trace_predicates(trace("ORDINARY_START"),"ORDINARY_REOPEN")

    def reader(self,root,phase,mode=None):
        files={}
        for p in s.PHASES:
            stem=s.PHASES[p][0];files[stem+"-ready-v1.txt"]=b"";files[stem+"-v1.json"]=encoded(proof(p))
            for i,name in enumerate(s.TRACES[p]):files[name]=encoded(trace("GUARDS" if p=="ORDINARY_DIALOGUE" and i==0 else p))
            if p==phase:break
        if mode=="hash":files[s.TRACES[phase][-1]]=encoded(trace("GUARDS"))
        if mode=="trace-work":
            name=s.TRACES[phase][0];files[name]=encoded(trace("ORDINARY_START"))
            value=proof(phase);value["worker_trace_sha256"]=q.sha(files[name]);files[s.PHASES[phase][0]+"-v1.json"]=encoded(value)
        if mode=="history":
            name="guards-worker-v2.json";zero=trace("GUARDS");zero["snapshot_ms"]=11;files[name]=encoded(zero)
            value=proof(phase);value["guards_worker_trace_sha256"]=q.sha(files[name]);files["dialogue-v1.json"]=encoded(value)
        if mode=="private-proof":files[s.PHASES[phase][0]+"-v1.json"]=encoded(dict(proof(phase),private_error="PRIVATE_CANARY"))
        if mode=="nonempty-ready":files[s.PHASES[phase][0]+"-ready-v1.txt"]=b"1"
        prefix=n.PROOF_ROOT if mode=="old-root" else s.PROOF_ROOT
        calls=[]
        def shell(op,**kwargs):
            calls.append(op)
            if op==s.namespace_command(10310):
                names=list(files)+([list(files)[0]] if mode=="duplicate-file" else [])
                return ("\n".join(prefix+"/"+name for name in names)+"\n").encode()
            for name,raw in files.items():
                if op==s.proof_command(name,10310):return raw
            raise AssertionError("Unexpected proof command")
        return SimpleNamespace(directory=root,uid_map=UIDS,shell=shell),calls

    def test_progressive_3_7_10_manifest_actual_trace_hashes_and_raw_retention(self):
        for phase,count in zip(s.PHASES,(3,7,10)):
            with tempfile.TemporaryDirectory() as directory:
                root=Path(directory);owner,calls=self.reader(root,phase)
                value,raw=s.read_proof(owner,phase)
                self.assertEqual(value,proof(phase));self.assertEqual(raw,encoded(value));self.assertEqual(len(calls),3+len(s.TRACES[phase]))
                self.assertEqual((root/(s.PHASES[phase][0]+"-proof.raw.json")).read_bytes(),raw)
                self.assertEqual(count,sum(2+len(s.TRACES[p]) for p in list(s.PHASES)[:list(s.PHASES).index(phase)+1]))
        for mode,phase in (("old-root","ORDINARY_START"),("duplicate-file","ORDINARY_START"),("nonempty-ready","ORDINARY_START"),
                ("hash","ORDINARY_START"),("private-proof","ORDINARY_START"),("trace-work","ORDINARY_REOPEN"),("history","ORDINARY_DIALOGUE")):
            with self.subTest(mode=mode),tempfile.TemporaryDirectory() as directory:
                root=Path(directory);owner,calls=self.reader(root,phase,mode)
                with self.assertRaises(AssertionError):s.read_proof(owner,phase)
                self.assertFalse((root/(s.PHASES[phase][0]+"-proof-v1.json")).exists())
                if mode in ("old-root","duplicate-file"):self.assertEqual(len(calls),1)
                if mode in ("private-proof","hash"):self.assertTrue((root/(s.PHASES[phase][0]+"-proof.raw.json")).exists())

    def test_failed_runner_diagnostics_never_authorize_later_proof(self):
        wire=s.worker_trace.PREFIX.encode()+encoded(trace("ORDINARY_START"))+b"\n"+s.worker_trace.STATUS.encode()+b"\n"
        send=send_wire.record()
        for phase in s.PHASES:
            for diagnostic in (b"",wire,send,wire+send):
                with tempfile.TemporaryDirectory() as directory:
                    root=Path(directory);owner=SimpleNamespace(directory=root,shell=lambda *a,**kw:diagnostic+transcript(phase,False))
                    with patch.object(s,"read_proof") as read:
                        with self.assertRaises(AssertionError):s.run_selected(owner,phase)
                        read.assert_not_called()
                    self.assertEqual((root/(s.PHASES[phase][0]+"-failure-worker-v2.json")).exists(),wire in diagnostic and phase!="ORDINARY_REOPEN")
                    self.assertEqual((root/(s.PHASES[phase][0]+"-failure-send-v1.json")).exists(),send in diagnostic)
                    if diagnostic:
                        owner.shell=lambda *a,**kw:diagnostic+transcript(phase)
                        with self.assertRaises(AssertionError):s.run_selected(owner,phase)

    def test_both_failure_channels_keep_actual_client_raw_and_stop_cohort(self):
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory);owner,_=owner_fixture(root)
            imported=api.old.proof("IMPORT")
            imported["prior_preflight_sha256"]=q.sha(Path(owner.proposal["preflight"]["proof"]["path"]).read_bytes())
            wire=s.worker_trace.PREFIX.encode()+encoded(trace("ORDINARY_START"))+b"\n"+s.worker_trace.STATUS.encode()+b"\n"
            raw=wire+send_wire.record()+transcript("ORDINARY_START",False)
            def boot(): owner.stage="before"
            def imported_result(actual,phase):
                self.assertEqual(phase,"IMPORT");owner.methods=1
                return imported,encoded(imported)
            with patch.object(owner,"wait_boot",side_effect=boot),patch.object(owner,"check_guest_cpu_profile"), \
                 patch.object(owner,"facts",return_value={"userdata":{"available_bytes":q.contract.USERDATA_FLOOR+r.MODEL_BYTES}}), \
                 patch.object(owner,"transfer",return_value={}),patch.object(r,"run_selected",side_effect=imported_result), \
                 patch.object(q.host,"run_process",side_effect=[api.client(),api.client(raw)]) as client, \
                 patch.object(s,"read_proof") as read:
                with self.assertRaises(AssertionError):s.run_cohort(owner)
                self.assertEqual(client.call_count,2);read.assert_not_called()
            self.assertEqual((owner.commands/"command-0002.stdout.bin").read_bytes(),raw)
            self.assertEqual(json.loads((owner.directory/"start-failure-send-v1.json").read_bytes()),send_wire.value())
            self.assertTrue((owner.directory/"start-failure-worker-v2.json").exists())
            self.assertFalse((owner.directory/"start-proof.raw.json").exists())
            self.assertFalse((owner.directory/"dialogue-instrumentation-v1.json").exists())

    def test_send_persistence_uncertainty_never_reaches_runner_or_proof(self):
        with tempfile.TemporaryDirectory() as directory:
            owner=SimpleNamespace(directory=Path(directory),shell=lambda *a,**kw:send_wire.record()+transcript("ORDINARY_START",False))
            with patch.object(q,"write_json",side_effect=OSError("synthetic_persistence")) as write, \
                 patch.object(s,"parse_runner") as runner,patch.object(s,"read_proof") as read:
                with self.assertRaises(OSError):s.run_selected(owner,"ORDINARY_START")
                self.assertEqual(write.call_args.args[0].name,"start-failure-send-v1.json")
                runner.assert_not_called();read.assert_not_called()

    def test_candidate_authority_exact_bindings_and_actual_old_preflight_lineage(self):
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory);value=candidate(root);p,a=root/"p.json",root/"a.json";p.write_bytes(encoded(value))
            grant={"version":1,"proposal_sha256":q.sha(p.read_bytes()),"allow_device_calls":True,"root_go_pending":False,
                "allow_local_weight_copy":True,"allow_sdk_calls":True};a.write_bytes(encoded(grant))
            with patch.object(q,"APK_HASHES",value["apk_sha256"]),patch.object(r,"source_path"):
                self.assertEqual(s.authorize(p,a,root),value)
                for field,bad in (("scope",n.SCOPE),("scope",r.SCOPE),("phase","preflight"),("ordinary_activity","FakeActivity")):
                    changed=copy.deepcopy(value);changed[field]=bad
                    with self.assertRaises(AssertionError):s.validate_proposal(changed)
                for name in s.SOURCE_FILES:
                    changed=copy.deepcopy(value);changed["bindings"].pop(str((q.ROOT/name).resolve()))
                    with self.subTest(name=name),self.assertRaises(AssertionError):s.validate_proposal(changed)
                for key,bad in (("proposal_sha256","0"*64),("allow_sdk_calls",False),("allow_local_weight_copy",False),
                        ("allow_device_calls",False),("root_go_pending",True),("version",True)):
                    a.write_bytes(encoded(dict(grant,**{key:bad})))
                    with self.assertRaises(AssertionError):s.authorize(p,a,root)
            self.assertEqual(json.loads(Path(value["preflight"]["result"]["path"]).read_bytes())["scope"],r.SCOPE)

    def test_owner_fixed_steps_namespace_once_and_helper_retirement(self):
        with tempfile.TemporaryDirectory() as directory:
            owner,_=owner_fixture(Path(directory))
            self.assertEqual(owner.STREAM_SCRIPT,Path(s.__file__).resolve());self.assertNotEqual(owner.STREAM_SCRIPT,n.Owner.STREAM_SCRIPT)
            self.assertEqual([x[1] for x in owner.instrumentation_steps],["instrument-IMPORT",*["instrument-"+p for p in s.PHASES]])
            owner.stage="instrument-ORDINARY_START";owner.methods=1
            with patch.object(q.host,"run_process") as run:
                with self.assertRaises(AssertionError):owner.shell(n.selection("RECOVER"))
                run.assert_not_called()
            owner.stage="after"
            with patch.object(q.host,"run_process",return_value=api.client()) as run:
                owner.check_namespace_absent();self.assertIn(s.PROOF_ROOT,run.call_args.args[0][-1])
                with self.assertRaises(AssertionError):owner.check_namespace_absent()
                self.assertEqual(run.call_count,1)
        boundary=s.ContinuedBoundary({"target":[],"test_helper":[]})
        for label,stage,methods in boundary.observations:
            self.assertEqual(boundary.observe(b"PID UID NAME\n",UIDS,label=label,stage=stage,methods=methods),{"target":[],"test_helper":[]})
        with self.assertRaises(AssertionError):boundary.observe(b"PID UID NAME\n",UIDS,label="after-reopen",stage="after",methods=4)
        boundary=s.ContinuedBoundary({"target":[],"test_helper":[]})
        with self.assertRaises(AssertionError):boundary.observe(b"PID UID NAME\n",UIDS,label="after-cancel",stage="after",methods=2)
        boundary=s.ContinuedBoundary({"target":[],"test_helper":[]})
        boundary.observe(b"PID UID NAME\n",UIDS,label="continued-before",stage="before",methods=0)
        helper=("PID UID NAME\n900 10311 "+q.TEST+"\n").encode()
        boundary.observe(helper,UIDS,label="after-import",stage="after",methods=1)
        boundary.observe(b"PID UID NAME\n",UIDS,label="after-start",stage="after",methods=2)
        with self.assertRaises(AssertionError):boundary.observe(helper,UIDS,label="after-dialogue",stage="after",methods=3)
        with self.assertRaises(AssertionError):boundary.observe(b"PID UID NAME\n",UIDS,label="after-dialogue",stage="after",methods=3)

    def flow(self,root,mode="pass"):
        owner,_=owner_fixture(root);events=[];imported=api.old.proof("IMPORT")
        imported["prior_preflight_sha256"]=q.sha(Path(owner.proposal["preflight"]["proof"]["path"]).read_bytes());prior=[imported]
        def boot():owner.stage="before";events.append("boot")
        def facts(label,packages):
            events.append(label)
            if mode=="overhead" and label=="after-import":owner.until=time.monotonic()-1
            if mode=="uid" and label=="after-start":raise AssertionError("Synthetic UID drift")
            return {"userdata":{"available_bytes":q.contract.USERDATA_FLOOR+r.MODEL_BYTES-(1 if mode=="capacity" else 0)}}
        def selected(actual,phase):
            self.assertIs(actual,owner);events.append(phase)
            command=r.selection(phase) if phase=="IMPORT" else s.selection(phase)
            self.assertEqual(owner.instrumentation_steps[owner.methods],(command,"instrument-"+phase,owner.methods));owner.methods+=1
            if phase=="IMPORT":return imported,encoded(imported)
            value=proof(phase,prior[0]);prior[0]=value
            if mode=="missed-start" and phase=="ORDINARY_START":value["checks"]["start_clicked_once"]=False
            if mode=="extra-commit" and phase=="ORDINARY_DIALOGUE":value.update(revision=3,receipt_count=3)
            if mode=="same-process" and phase=="ORDINARY_START":value.update(pid=value["prior_pid"],start=value["prior_start"])
            s.parse_proof(encoded(value),phase,UIDS[q.APP]);return value,encoded(value)
        def dispatch(*args,**kwargs):events.append("namespace");return api.client(clean=mode!="cleanup")
        with patch.object(owner,"wait_boot",side_effect=boot),patch.object(owner,"check_guest_cpu_profile",side_effect=lambda:events.append("cpu")), \
             patch.object(owner,"facts",side_effect=facts),patch.object(owner,"transfer",side_effect=lambda:events.append("copy") or {}), \
             patch.object(r,"run_selected",side_effect=selected),patch.object(s,"run_selected",side_effect=selected),patch.object(q.host,"run_process",side_effect=dispatch):
            if mode=="pass":
                result=s.run_cohort(owner);self.assertEqual(list(result["proofs"]),["IMPORT",*s.PHASES]);self.assertTrue(result["ordinary_setup_start_observed"])
            else:
                with self.assertRaises(AssertionError):s.run_cohort(owner)
        return events

    def test_mocked_full_flow_and_failure_stop_before_next_phase(self):
        with tempfile.TemporaryDirectory() as directory:
            self.assertEqual(self.flow(Path(directory)),["boot","cpu","continued-before","copy","IMPORT","after-import","namespace",
                "ORDINARY_START","after-start","ORDINARY_DIALOGUE","after-dialogue","ORDINARY_REOPEN","after-reopen"])
        for mode in ("capacity","overhead","cleanup","missed-start","same-process","uid","extra-commit"):
            with self.subTest(mode=mode),tempfile.TemporaryDirectory() as directory:
                events=self.flow(Path(directory),mode)
                if mode=="capacity":self.assertNotIn("copy",events)
                if mode in ("capacity","overhead","cleanup"):self.assertNotIn("ORDINARY_START",events)
                if mode=="overhead":self.assertNotIn("namespace",events)
                if mode in ("missed-start","same-process","uid"):self.assertNotIn("ORDINARY_DIALOGUE",events)
                self.assertNotIn("ORDINARY_REOPEN",events)

    def test_unknown_cleanup_and_owner_loss_retain_raw_with_no_next_dispatch(self):
        for mode in ("cleanup","owner"):
            with tempfile.TemporaryDirectory() as directory:
                owner,lease=owner_fixture(Path(directory));owner.stage="instrument-ORDINARY_START";owner.methods=1
                def run(*a,**kw):
                    if mode=="owner":lease.live=False
                    return api.client(b"bounded raw",mode!="cleanup")
                with patch.object(q.host,"run_process",side_effect=run) as child:
                    with self.assertRaises((AssertionError,RuntimeError)):owner.shell(s.selection("ORDINARY_START"))
                    with self.assertRaises((AssertionError,RuntimeError)):owner.shell(s.selection("ORDINARY_DIALOGUE"))
                    self.assertEqual(child.call_count,1)
                self.assertEqual((owner.commands/"command-0001.stdout.bin").read_bytes(),b"bounded raw")

    def test_remaining_budget_clips_calls_and_refusal_has_no_dispatch(self):
        with tempfile.TemporaryDirectory() as directory:
            owner,_=owner_fixture(Path(directory));owner.stage="instrument-ORDINARY_START";owner.methods=1;owner.until=time.monotonic()+.25
            with patch.object(q.host,"run_process",return_value=api.client()) as child:
                owner.shell(s.selection("ORDINARY_START"),deadline=180);self.assertLessEqual(child.call_args.kwargs["deadline"],.25)
                owner.stage="instrument-ORDINARY_DIALOGUE";owner.until=time.monotonic()-1
                with self.assertRaises(AssertionError):owner.shell(s.selection("ORDINARY_DIALOGUE"),deadline=180)
                self.assertEqual(child.call_count,1);self.assertEqual(owner.methods,3);self.assertEqual(owner.count,1)

    def test_stream_barrier_own_authority_precedes_existing_fixed_transfer(self):
        value={"scope":s.SCOPE}
        with patch.object(sys,"stdin",SimpleNamespace(buffer=io.BytesIO(r.STREAM_REQUEST+b"10310\n"))), \
             patch.object(s,"authorize",return_value=value) as auth,patch.object(r,"stream_authorized",return_value=0) as transfer:
            self.assertEqual(s.stream_worker("p","a","e"),0);auth.assert_called_once_with("p","a","e")
            transfer.assert_called_once_with(value,10310,"p","a","e")
        with patch.object(sys,"stdin",SimpleNamespace(buffer=io.BytesIO(n.REQUEST))),patch.object(s,"authorize") as auth:
            with self.assertRaises(AssertionError):s.stream_worker("p","a","e")
            auth.assert_not_called()

    def test_900_outer_920_entry_create_only_and_uncertain_capture_stop(self):
        for mode in ("pass","child","cleanup","capture","deadline"):
            with self.subTest(mode=mode),tempfile.TemporaryDirectory() as directory:
                root=Path(directory);p,a=root/"p",root/"a";p.write_bytes(b"p");a.write_bytes(b"a")
                lease=SimpleNamespace(descriptor={"deadline_epoch":1019 if mode=="deadline" else 1020},check=lambda:None)
                result={"status":"child_exited","worker_returncode":2 if mode=="child" else 0,
                    "cleanup_complete":mode!="cleanup","output_capture_complete":mode!="capture"}
                with patch.object(s,"authorize",return_value={}),patch.object(q,"open_lease",return_value=lease), \
                     patch.object(s.time,"time",return_value=100),patch.object(s.environment,"supervise",return_value=result) as run,redirect_stdout(io.StringIO()):
                    if mode=="deadline":
                        with self.assertRaises(AssertionError):s.run_owned(p,a,root)
                        run.assert_not_called()
                    else:
                        self.assertEqual(s.run_owned(p,a,root),0 if mode=="pass" else 2)
                        self.assertEqual(run.call_args.args[1],s.REQUEST);self.assertEqual(run.call_args.args[3],900)
                        self.assertIn(str(Path(s.__file__).resolve()),run.call_args.args[0])
                        with self.assertRaises(FileExistsError):s.run_owned(p,a,root)
                        self.assertEqual(run.call_count,1)

    def test_worker_uses_exact_barrier_and_records_stopped_result(self):
        for fail in (False,True):
            with tempfile.TemporaryDirectory() as directory:
                root=Path(directory);owner=SimpleNamespace(directory=root,stage="instrument-ORDINARY_START",clean=True,owner_live=True,count=1,methods=2,installs=0)
                with patch.object(sys,"stdin",SimpleNamespace(buffer=io.BytesIO(s.REQUEST))),patch.object(s,"authorize",return_value={"running_sha256":"a"*64}), \
                     patch.object(q,"open_lease"),patch.object(s,"Owner",return_value=owner),redirect_stdout(io.StringIO()), \
                     patch.object(s,"run_cohort",side_effect=AssertionError if fail else None,return_value={}) as cohort:
                    self.assertEqual(s.worker("p","a",root),2 if fail else 0);cohort.assert_called_once_with(owner)
                body=json.loads((root/"result-v1.json").read_bytes());self.assertEqual(body["scope"],s.SCOPE)
                self.assertEqual(body["status"],"stopped" if fail else "observed")
        with patch.object(sys,"stdin",SimpleNamespace(buffer=io.BytesIO(n.REQUEST))),patch.object(s,"authorize") as auth:
            with self.assertRaises(AssertionError):s.worker("p","a","e")
            auth.assert_not_called()

    def test_no_cli_selector_or_import_time_model_io(self):
        for flag in ("--phase","--scope","--serial","--proof-root","--activity"):
            with patch.object(s,"run_owned") as run,redirect_stdout(io.StringIO()),patch.object(sys,"stderr",io.StringIO()):
                with self.assertRaises(SystemExit):s.main(["run","--proposal","p","--authorization","a","--evidence","e",flag,"value"])
                run.assert_not_called()
        spec=importlib.util.spec_from_file_location("ordinary_scene_inert",Path(s.__file__));module=importlib.util.module_from_spec(spec)
        with patch.object(Path,"read_bytes",side_effect=AssertionError("Unexpected file read")),patch.object(q.host,"run_process",side_effect=AssertionError("Unexpected client")):
            spec.loader.exec_module(module)
        self.assertEqual(module.SCOPE,s.SCOPE)


if __name__=="__main__":unittest.main()
