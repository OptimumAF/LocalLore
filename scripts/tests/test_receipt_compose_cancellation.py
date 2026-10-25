"""Pure fixed UI-controller tests. Every child/transport is mocked; no SDK/model.

Copyright 2026 LocalLore contributors. SPDX-License-Identifier: Apache-2.0
"""
from contextlib import redirect_stdout
import copy
import importlib.util
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
from scripts.tests import test_receipt_real_cancellation as api

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "benchmarks"))
import receipt_compose_cancellation as u
n, r, q = u.n, u.r, u.q
encoded, trace, UIDS = api.encoded, api.trace, api.UIDS


def proof(phase, prior=None):
    value = api.proof(u.BASE[phase])
    value.update(phase=phase, checks={key: True for key in u.PHASES[phase][4]})
    if prior is not None:
        value.update(prior_pid=prior["pid"], prior_start=prior["start"])
        value["prior_"+u.PRIOR_KEY[phase]+"_sha256"] = q.sha(encoded(prior))
    return value


def transcript(phase, passed=True):
    base=u.BASE[phase]
    return api.transcript(base,passed).replace(n.PHASES[base][1].encode(),u.PHASES[phase][1].encode()).replace(
        n.PHASES[base][2].encode(),u.PHASES[phase][2].encode())


def candidate(root):
    value=api.candidate(root);value["scope"]=u.SCOPE
    for name in u.SOURCE_FILES:
        p=(q.ROOT/name).resolve();value["bindings"][str(p)]=q.sha(p.read_bytes())
    return value


def owner_fixture(root):
    value=candidate(root);lease=api.old.fixture.Lease(value)
    lease.descriptor["deadline_epoch"]=time.time()+1500
    return u.Owner(value,lease),lease


class ComposeControllerTests(unittest.TestCase):
    def test_closed_ui_schema_counts_caps_and_exact_selectors(self):
        self.assertEqual([len(v[4]) for v in u.PHASES.values()],[26,24,17])
        self.assertEqual(sum(len(v[4]) for v in u.PHASES.values())+12+16,95)
        self.assertEqual([v[3] for v in u.PHASES.values()],[170000,170000,120000])
        for phase in u.PHASES:
            self.assertEqual(u.parse_proof(encoded(proof(phase)),phase,UIDS[q.APP]),proof(phase))
            self.assertEqual(u.parse_runner(transcript(phase),phase)["passed"],1)
            self.assertEqual(u.parse_runner(transcript(phase).replace(b"Time: 0.1",b"Time: 120"),phase)["passed"],1)
            with self.assertRaises(AssertionError):u.parse_runner(transcript(phase).replace(b"Time: 0.1",b"Time: 120.001"),phase)
            with self.assertRaises(AssertionError):u.parse_runner(api.transcript(u.BASE[phase]),phase)
            with self.assertRaises(AssertionError):u.parse_proof(encoded(api.proof(u.BASE[phase])),phase,UIDS[q.APP])

    def test_every_visible_ui_check_is_required_and_private_fields_refuse(self):
        for phase in u.PHASES:
            for key in u.PHASES[phase][4]:
                changed=proof(phase);changed["checks"][key]=False
                with self.subTest(phase=phase,key=key),self.assertRaises(AssertionError):u.parse_proof(encoded(changed),phase,UIDS[q.APP])
            changed=proof(phase);changed["checks"]["gateway_api_instead_of_click"]=True
            with self.assertRaises(AssertionError):u.parse_proof(encoded(changed),phase,UIDS[q.APP])
            for key,invalid in (("sdk_invoked",phase=="UI_REOPEN"),("source_import_opened",1),("revision",True),
                    ("receipt_count",9),("uid",True),("elapsed_ms",u.PHASES[phase][3]+1),
                    ("memory_available_before",4*r.GIB-1),("external_free_after",2*r.GIB-1),
                    ("userdata_free_after",q.contract.USERDATA_FLOOR-1)):
                changed=proof(phase);changed[key]=invalid
                with self.subTest(phase=phase,key=key),self.assertRaises(AssertionError):u.parse_proof(encoded(changed),phase,UIDS[q.APP])
            changed=proof(phase);changed["private_error"]="PRIVATE_CANARY"
            with self.assertRaises(AssertionError) as error:u.parse_proof(encoded(changed),phase,UIDS[q.APP])
            self.assertNotIn("PRIVATE_CANARY",str(error.exception))
            with self.assertRaises(AssertionError):u.parse_proof(encoded(proof(phase))+b" "*4096,phase,UIDS[q.APP])

    def test_ui_lineage_changes_process_and_keeps_actual_receipt_hash(self):
        prior=api.old.proof("IMPORT")
        for phase in u.PHASES:
            value=proof(phase,prior);u.link_proofs(prior,encoded(prior),value)
            wrong=copy.deepcopy(value);wrong["prior_"+u.PRIOR_KEY[phase]+"_sha256"]="0"*64
            with self.assertRaises(AssertionError):u.link_proofs(prior,encoded(prior),wrong)
            if phase!="UI_CANCEL":
                wrong=copy.deepcopy(value);wrong.update(pid=prior["pid"],start=prior["start"])
                with self.assertRaises(AssertionError):u.link_proofs(prior,encoded(prior),wrong)
                foreign=copy.deepcopy(prior);foreign["phase"]=u.BASE[prior["phase"]]
                wrong=proof(phase,foreign)
                with self.assertRaises(AssertionError):u.link_proofs(foreign,encoded(foreign),wrong)
            if phase=="UI_REOPEN":
                wrong=copy.deepcopy(value);wrong["receipt_sha256"]="0"*64
                with self.assertRaises(AssertionError):u.link_proofs(prior,encoded(prior),wrong)
            prior=value

    def test_fixed_namespace_reuses_guards_without_old_root_or_global_mutation(self):
        before=(copy.deepcopy(n.PHASES),n.PROOF_ROOT,n.SCOPE,copy.deepcopy(r.PHASES))
        for name in ("cancel-v1.json","recover-ready-v1.txt","reopen-v1.json","cancel-sample-worker-v2.json"):
            command=u.proof_command(name,10310)
            self.assertEqual(command[:4],("run-as",q.APP,"sh","-c"))
            self.assertIn(u.PROOF_ROOT,command[4]);self.assertNotIn(n.PROOF_ROOT,command[4]);self.assertNotIn(r.PROOF_ROOT,command[4])
            self.assertIn("test ! -L",command[4]);self.assertIn("-eq 10310",command[4]);self.assertIn("-le 4096",command[4])
        for absent in (False,True):
            command=u.namespace_command(10310,absent)
            self.assertIn(u.PROOF_ROOT,command[4]);self.assertNotIn(n.PROOF_ROOT,command[4])
        for name in ("../model.litertlm","IMPORT","source-preflight-v1.json","cancel-v1.json; echo private"):
            with self.assertRaises(AssertionError):u.proof_command(name,10310)
        self.assertEqual(before,(n.PHASES,n.PROOF_ROOT,n.SCOPE,r.PHASES))

    def reader(self,root,phase,mode=None):
        files={}
        for p in u.PHASES:
            stem=u.PHASES[p][0];files[stem+"-ready-v1.txt"]=b"";files[stem+"-v1.json"]=encoded(proof(p))
            for i,name in enumerate(u.TRACES[p]):files[name]=encoded(trace("SAMPLE" if p=="UI_CANCEL" and i==0 else u.BASE[p]))
            if p==phase:break
        if mode=="old-root":prefix=n.PROOF_ROOT
        else:prefix=u.PROOF_ROOT
        if mode=="trace-hash":files["cancel-worker-v2.json"]=encoded(trace("SAMPLE"))
        if mode=="api-proof":files["cancel-v1.json"]=encoded(api.proof("CANCEL"))
        if mode=="history":
            value=trace("CANCEL");value["snapshot_ms"]=9;files["cancel-worker-v2.json"]=encoded(value)
            p=json.loads(files["cancel-v1.json"]);p["worker_trace_sha256"]=q.sha(encoded(value));files["cancel-v1.json"]=encoded(p)
        calls=[]
        def shell(op,**kwargs):
            calls.append(op)
            if op==u.namespace_command(10310):return ("\n".join(prefix+"/"+name for name in files)+"\n").encode()
            for name,raw in files.items():
                if op==u.proof_command(name,10310):return raw
            raise AssertionError("Unexpected proof command")
        return SimpleNamespace(directory=root,uid_map=UIDS,shell=shell),calls

    def test_progressive_ui_files_and_shared_trace_validation(self):
        for phase,count in zip(u.PHASES,(4,7,9)):
            with tempfile.TemporaryDirectory() as directory:
                owner,calls=self.reader(Path(directory),phase)
                with patch.object(n,"trace_predicates",wraps=n.trace_predicates) as validate:
                    value,raw=u.read_proof(owner,phase)
                self.assertEqual(value,proof(phase));self.assertEqual(raw,encoded(value))
                self.assertEqual(len(calls),3+len(u.TRACES[phase]))
                self.assertEqual(validate.call_count,len(u.TRACES[phase]))
                if phase=="UI_CANCEL":self.assertEqual([x.args[1] for x in validate.call_args_list],["SAMPLE","CANCEL"])
                if phase=="UI_RECOVER":self.assertEqual(validate.call_args.args[1],"RECOVER")
                self.assertEqual(count,len({u.PROOF_ROOT+"/"+name for p in list(u.PHASES)[:list(u.PHASES).index(phase)+1]
                    for name in (u.PHASES[p][0]+"-v1.json",u.PHASES[p][0]+"-ready-v1.txt",*u.TRACES[p])}))

    def test_old_namespace_api_proof_hash_and_history_drift_stop(self):
        for mode in ("old-root","api-proof","trace-hash","history"):
            with self.subTest(mode=mode),tempfile.TemporaryDirectory() as directory:
                owner,calls=self.reader(Path(directory),"UI_CANCEL",mode)
                with self.assertRaises(AssertionError):u.read_proof(owner,"UI_CANCEL")
                if mode=="old-root":self.assertEqual(len(calls),1)
                self.assertFalse((Path(directory)/"cancel-proof-v1.json").exists())
                if mode=="api-proof":self.assertTrue((Path(directory)/"cancel-proof.raw.json").exists())

    def test_ui_runner_failure_diagnostics_never_authorize_proof(self):
        for phase in u.PHASES:
            with tempfile.TemporaryDirectory() as directory:
                owner=SimpleNamespace(directory=Path(directory),shell=lambda *a,**kw:transcript(phase,False))
                with patch.object(u,"read_proof") as read:
                    with self.assertRaises(AssertionError):u.run_selected(owner,phase)
                    read.assert_not_called()
        wire=u.worker_trace.PREFIX.encode()+encoded(trace("RECOVER"))+b"\n"+u.worker_trace.STATUS.encode()+b"\n"
        for phase in u.PHASES:
            with tempfile.TemporaryDirectory() as directory:
                owner=SimpleNamespace(directory=Path(directory),shell=lambda *a,**kw:wire+transcript(phase,False))
                with patch.object(u,"read_proof") as read:
                    with self.assertRaises(AssertionError):u.run_selected(owner,phase)
                    read.assert_not_called()
                self.assertEqual((Path(directory)/(u.PHASES[phase][0]+"-failure-worker-v2.json")).exists(),phase!="UI_REOPEN")
                owner.shell=lambda *a,**kw:wire+transcript(phase)
                with self.assertRaises(AssertionError):u.run_selected(owner,phase)

    def test_candidate_authority_binds_ui_sources_and_retains_old_preflight(self):
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory);value=candidate(root);p,a=root/"p.json",root/"a.json";p.write_bytes(encoded(value))
            grant={"version":1,"proposal_sha256":q.sha(p.read_bytes()),"allow_device_calls":True,"root_go_pending":False,
                "allow_local_weight_copy":True,"allow_sdk_calls":True};a.write_bytes(encoded(grant))
            with patch.object(q,"APK_HASHES",value["apk_sha256"]),patch.object(r,"source_path"):
                self.assertEqual(u.authorize(p,a,root),value)
                for field,bad in (("scope",n.SCOPE),("scope",r.SCOPE),("phase","preflight"),("allow_device_calls",True)):
                    changed=copy.deepcopy(value);changed[field]=bad
                    with self.assertRaises(AssertionError):u.validate_proposal(changed)
                changed=copy.deepcopy(value);changed["ui_selector"]="API"
                with self.assertRaises(AssertionError):u.validate_proposal(changed)
                for name in ("apps/android/app/src/modelReceipt/java/org/locallore/app/ReceiptComposeCancellationActivity.kt",
                        "apps/android/app/src/main/java/org/locallore/app/MainActivity.kt"):
                    changed=copy.deepcopy(value);changed["bindings"].pop(str((q.ROOT/name).resolve()))
                    with self.assertRaises(AssertionError):u.validate_proposal(changed)
                for key,bad in (("proposal_sha256","0"*64),("allow_sdk_calls",False),("allow_local_weight_copy",False),
                        ("allow_device_calls",False),("root_go_pending",True),("version",True)):
                    a.write_bytes(encoded(dict(grant,**{key:bad})))
                    with self.assertRaises(AssertionError):u.authorize(p,a,root)
            self.assertEqual(json.loads(Path(value["preflight"]["result"]["path"]).read_bytes())["scope"],r.SCOPE)

    def test_owner_has_only_new_ui_steps_and_one_new_namespace_check(self):
        with tempfile.TemporaryDirectory() as directory:
            owner,_=owner_fixture(Path(directory))
            self.assertEqual(owner.STREAM_SCRIPT,Path(u.__file__).resolve());self.assertNotEqual(owner.STREAM_SCRIPT,n.Owner.STREAM_SCRIPT)
            self.assertEqual([x[1] for x in owner.instrumentation_steps],["instrument-IMPORT",*["instrument-"+p for p in u.PHASES]])
            owner.stage="instrument-UI_CANCEL";owner.methods=1
            with patch.object(q.host,"run_process") as run:
                with self.assertRaises(AssertionError):owner.shell(n.selection("CANCEL"))
                run.assert_not_called()
            owner.stage="after"
            with patch.object(q.host,"run_process",return_value=api.client()) as run:
                owner.check_cancel_namespace_absent()
                self.assertIn(u.PROOF_ROOT,run.call_args.args[0][-1]);self.assertNotIn(n.PROOF_ROOT,run.call_args.args[0][-1])
                with self.assertRaises(AssertionError):owner.check_cancel_namespace_absent()
                self.assertEqual(run.call_count,1)

    def flow(self,root,mode="pass"):
        owner,_=owner_fixture(root);events=[];imported=api.old.proof("IMPORT")
        imported["prior_preflight_sha256"]=q.sha(Path(owner.proposal["preflight"]["proof"]["path"]).read_bytes());prior=[imported]
        def boot():owner.stage="before";events.append("boot")
        def facts(label,packages):
            events.append(label)
            if mode=="overhead" and label=="after-import":owner.until=time.monotonic()-1
            if mode=="uid" and label=="after-cancel":raise AssertionError("Synthetic UID drift")
            return {"userdata":{"available_bytes":q.contract.USERDATA_FLOOR+r.MODEL_BYTES-(1 if mode=="capacity" else 0)}}
        def selected(actual,phase):
            self.assertIs(actual,owner);events.append(phase)
            command=r.selection(phase) if phase=="IMPORT" else u.selection(phase)
            self.assertEqual(owner.instrumentation_steps[owner.methods],(command,"instrument-"+phase,owner.methods));owner.methods+=1
            if phase=="IMPORT":return imported,encoded(imported)
            value=proof(phase,prior[0]);prior[0]=value
            if mode=="missed-click" and phase=="UI_CANCEL":value["checks"]["cancel_clicked_once"]=False
            if mode=="commit-race" and phase=="UI_CANCEL":value.update(revision=1,receipt_count=1)
            if mode=="same-process" and phase=="UI_RECOVER":value.update(pid=value["prior_pid"],start=value["prior_start"])
            u.parse_proof(encoded(value),phase,UIDS[q.APP])
            return value,encoded(value)
        def dispatch(*args,**kwargs):events.append("namespace");return api.client(clean=mode!="cleanup")
        with patch.object(owner,"wait_boot",side_effect=boot),patch.object(owner,"check_guest_cpu_profile",side_effect=lambda:events.append("cpu")), \
             patch.object(owner,"facts",side_effect=facts),patch.object(owner,"transfer",side_effect=lambda:events.append("copy") or {}), \
             patch.object(r,"run_selected",side_effect=selected),patch.object(u,"run_selected",side_effect=selected),patch.object(q.host,"run_process",side_effect=dispatch):
            if mode=="pass":
                result=u.run_cohort(owner);self.assertEqual(list(result["proofs"]),["IMPORT",*u.PHASES])
                self.assertTrue(result["compose_send_cancel_observed"])
            else:
                with self.assertRaises(AssertionError):u.run_cohort(owner)
        return events

    def test_mocked_full_ui_cohort_and_failure_stop_points(self):
        with tempfile.TemporaryDirectory() as directory:
            self.assertEqual(self.flow(Path(directory)),["boot","cpu","continued-before","copy","IMPORT","after-import","namespace",
                "UI_CANCEL","after-cancel","UI_RECOVER","after-recover","UI_REOPEN","after-reopen"])
        for mode in ("capacity","overhead","cleanup","missed-click","commit-race","same-process","uid"):
            with self.subTest(mode=mode),tempfile.TemporaryDirectory() as directory:
                events=self.flow(Path(directory),mode)
                if mode=="capacity":self.assertNotIn("copy",events)
                if mode in ("capacity","overhead","cleanup"):self.assertNotIn("UI_CANCEL",events)
                if mode=="overhead":self.assertNotIn("namespace",events)
                if mode in ("missed-click","commit-race","uid"):self.assertNotIn("UI_RECOVER",events)
                self.assertNotIn("UI_REOPEN",events)

    def test_unknown_cleanup_and_lost_owner_retain_raw_and_stop(self):
        for mode in ("cleanup","owner"):
            with tempfile.TemporaryDirectory() as directory:
                owner,lease=owner_fixture(Path(directory));owner.stage="instrument-UI_CANCEL";owner.methods=1
                def run(*a,**kw):
                    if mode=="owner":lease.live=False
                    return api.client(b"bounded raw",mode!="cleanup")
                with patch.object(q.host,"run_process",side_effect=run) as child:
                    with self.assertRaises((AssertionError,RuntimeError)):owner.shell(u.selection("UI_CANCEL"))
                    with self.assertRaises((AssertionError,RuntimeError)):owner.shell(u.selection("UI_RECOVER"))
                    self.assertEqual(child.call_count,1)
                self.assertEqual((owner.commands/"command-0001.stdout.bin").read_bytes(),b"bounded raw")

    def test_inherited_client_clipping_counts_attempt_not_unsent_dispatch(self):
        with tempfile.TemporaryDirectory() as directory:
            owner,_=owner_fixture(Path(directory));owner.stage="instrument-UI_CANCEL";owner.methods=1;owner.until=time.monotonic()+.25
            with patch.object(q.host,"run_process",return_value=api.client()) as child:
                owner.shell(u.selection("UI_CANCEL"),deadline=180);self.assertLessEqual(child.call_args.kwargs["deadline"],.25)
                owner.stage="instrument-UI_RECOVER";owner.until=time.monotonic()-1
                with self.assertRaises(AssertionError):owner.shell(u.selection("UI_RECOVER"),deadline=180)
                self.assertEqual(child.call_count,1);self.assertEqual(owner.methods,3);self.assertEqual(owner.count,1)

    def test_stream_barrier_keeps_new_authority_and_exact_root_transfer(self):
        value={"scope":u.SCOPE}
        with patch.object(sys,"stdin",SimpleNamespace(buffer=io.BytesIO(r.STREAM_REQUEST+b"10310\n"))), \
             patch.object(u,"authorize",return_value=value) as auth,patch.object(r,"stream_authorized",return_value=0) as transfer:
            self.assertEqual(u.stream_worker("p","a","e"),0);auth.assert_called_once_with("p","a","e")
            transfer.assert_called_once_with(value,10310,"p","a","e")
        with patch.object(sys,"stdin",SimpleNamespace(buffer=io.BytesIO(n.REQUEST))),patch.object(u,"authorize") as auth:
            with self.assertRaises(AssertionError):u.stream_worker("p","a","e")
            auth.assert_not_called()

    def test_outer_900_920_one_shot_and_unknown_capture_remain_strict(self):
        for mode in ("pass","child","cleanup","capture","deadline"):
            with self.subTest(mode=mode),tempfile.TemporaryDirectory() as directory:
                root=Path(directory);p,a=root/"p",root/"a";p.write_bytes(b"p");a.write_bytes(b"a")
                lease=SimpleNamespace(descriptor={"deadline_epoch":1019 if mode=="deadline" else 1020},check=lambda:None)
                result={"status":"child_exited","worker_returncode":2 if mode=="child" else 0,
                    "cleanup_complete":mode!="cleanup","output_capture_complete":mode!="capture"}
                with patch.object(u,"authorize",return_value={}),patch.object(q,"open_lease",return_value=lease), \
                     patch.object(u.time,"time",return_value=100),patch.object(u.environment,"supervise",return_value=result) as run,redirect_stdout(io.StringIO()):
                    if mode=="deadline":
                        with self.assertRaises(AssertionError):u.run_owned(p,a,root)
                        run.assert_not_called()
                    else:
                        self.assertEqual(u.run_owned(p,a,root),0 if mode=="pass" else 2)
                        self.assertEqual(run.call_args.args[1],u.REQUEST);self.assertEqual(run.call_args.args[3],900)
                        self.assertIn(str(Path(u.__file__).resolve()),run.call_args.args[0])
                        with self.assertRaises(FileExistsError):u.run_owned(p,a,root)
                        self.assertEqual(run.call_count,1)

    def test_cli_has_no_phase_scope_serial_or_namespace_selector(self):
        for selector in ("--phase","--scope","--serial","--proof-root"):
            with patch.object(u,"run_owned") as run,redirect_stdout(io.StringIO()),patch.object(sys,"stderr",io.StringIO()):
                with self.assertRaises(SystemExit):u.main(["run","--proposal","p","--authorization","a","--evidence","e",selector,"value"])
                run.assert_not_called()

    def test_import_has_no_source_file_reads_or_model_actions(self):
        path=Path(u.__file__);spec=importlib.util.spec_from_file_location("ui_cancel_inert",path);module=importlib.util.module_from_spec(spec)
        with patch.object(Path,"read_bytes",side_effect=AssertionError("Unexpected file read")),patch.object(q.host,"run_process",side_effect=AssertionError("Unexpected client")):
            spec.loader.exec_module(module)
        self.assertEqual(module.SCOPE,u.SCOPE)


if __name__ == "__main__":unittest.main()
