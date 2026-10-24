"""Fixed real-candidate controller rules. All transports are mocked; no weights.

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
from scripts.tests import test_receipt_setup_qualification as fixture

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "benchmarks"))
import receipt_real_candidate as r
q = r.q


def encoded(value): return json.dumps(value, sort_keys=True, separators=(",", ":")).encode("ascii")


def proof(phase):
    value = {"version": 1, "phase": phase, "pid": 601, "start": 1000, "uid": 10310, "process": q.APP,
        "model_bytes": r.MODEL_BYTES, "model_sha256": r.MODEL_SHA, "sdk_invoked": phase == "PLAY", "publication_native_invoked": False,
        "elapsed_ms": 1, "userdata_free_before": q.contract.USERDATA_FLOOR + r.MODEL_BYTES,
        "userdata_free_after": q.contract.USERDATA_FLOOR + r.MODEL_BYTES, "external_free_before": 2 * r.GIB + r.MODEL_BYTES,
        "external_free_after": 2 * r.GIB + r.MODEL_BYTES, "memory_total_bytes": 8 * r.GIB, "memory_available_before": 4 * r.GIB,
        "memory_available_after": 0, "checks": {key: True for key in r.PHASES[phase][4]}}
    for kind in ("verify", "import"):
        for suffix in ("opened", "closed", "bytes"):
            value["source_" + kind + "_" + suffix] = (r.MODEL_BYTES if suffix == "bytes" else 1) if phase == "IMPORT" else 0
    if phase != "SOURCE_PREFLIGHT":
        prior = {"IMPORT": "preflight", "PLAY": "import", "REOPEN": "play"}[phase]
        value.update(prior_pid=601, prior_start=1000); value["prior_" + prior + "_sha256"] = "c" * 64
    if phase in ("PLAY", "REOPEN"): value.update(revision=1, receipt_count=1, receipt_sha256="d" * 64)
    if phase == "PLAY": value.update(repairs=0, fallback=False)
    if phase == "REOPEN": value.update(pid=602, start=2000)
    return value


def transcript(phase):
    cls, method = "org.locallore.app." + r.PHASES[phase][1], r.PHASES[phase][2]
    rows = []
    for code in (1, 0):
        fields = {"class": cls, "current": "1", "id": "AndroidJUnitRunner", "numtests": "1", "stream": "." if code == 0 else "", "test": method}
        rows.extend("INSTRUMENTATION_STATUS: " + key + "=" + value for key, value in fields.items())
        rows.append("INSTRUMENTATION_STATUS_CODE: " + str(code))
    return ("\n".join(rows) + "\nINSTRUMENTATION_RESULT: stream=\n\nTime: 0.04\n\nOK (1 test)\n\nINSTRUMENTATION_CODE: -1\n").encode()


def proposal(root):
    value = fixture.proposal(root); value.update(scope=r.SCOPE, phase="preflight", preflight=None, human_consent=None,
        source={"path": str(r.PROBE_PATH.resolve()), "bytes": r.PROBE_BYTES, "sha256": r.PROBE_SHA})
    env = Path(value["environment_proposal_path"]); env.write_bytes(encoded({"memory_mib":8192,"host_available_memory_min":12*r.GIB}))
    value["bindings"][str(env.resolve())] = q.sha(env.read_bytes())
    for name in r.SOURCE_FILES:
        p = (q.ROOT/name).resolve(); value["bindings"][str(p)] = q.sha(p.read_bytes())
    return value


def stream_result(clean=True):
    body={"version":1,"source_bytes":r.PROBE_BYTES,"source_verified":True,"client_returncode":0,
          "remote_exit_status_known":False,"destination_verified":False}
    return SimpleNamespace(status="completed",returncode=0,cleanup_complete=clean,stdout=encoded(body),stderr_bytes=0,elapsed_ms=1)


class RealCandidateTests(unittest.TestCase):
    def reject_proof(self, value):
        with self.assertRaises((AssertionError, ValueError, KeyError)): r.parse_proof(encoded(value), value["phase"], 10310)

    def test_all_four_literal_schemas_and_56_checks_are_closed(self):
        self.assertEqual([len(v[4]) for v in r.PHASES.values()], [12,16,15,13])
        for phase in r.PHASES:
            self.assertEqual(r.parse_proof(encoded(proof(phase)),phase,10310),proof(phase))
            self.assertEqual(r.parse_runner(transcript(phase),phase)["passed"],1)
            with self.assertRaises(AssertionError):q.parse_instrumentation(transcript(phase),q.INITIAL_CLASS,q.INITIAL_METHODS)

    def test_unknown_keys_missing_checks_wrong_types_and_bounds_refuse(self):
        for phase in r.PHASES:
            for key,invalid in (("version",True),("uid",True),("model_bytes",True),("pid",0),("memory_available_before",4*r.GIB-1),
                ("memory_total_bytes",2*r.GIB),("elapsed_ms",r.PHASES[phase][3]+1),("sdk_invoked",1),("publication_native_invoked",True)):
                value=proof(phase);value[key]=invalid;self.reject_proof(value)
            value=proof(phase);value["private_path"]="secret";self.reject_proof(value)
            value=proof(phase);value["checks"].pop(next(iter(value["checks"])));self.reject_proof(value)
            value=proof(phase);value["checks"][next(iter(value["checks"]))]=1;self.reject_proof(value)
            value=proof(phase);value["source_verify_opened"]=2;self.reject_proof(value)
            with self.assertRaises(AssertionError):r.parse_proof(encoded(proof(phase))+b" "*4096,phase,10310)

    def test_capacity_after_copy_is_independent_from_expected_identity(self):
        for phase in r.PHASES:
            for key in ("userdata_free_before","userdata_free_after","external_free_before","external_free_after"):
                value=proof(phase);value[key]=0;self.reject_proof(value)
        value=proof("PLAY");value["fallback"]=True;value["repairs"]=1
        self.assertTrue(r.parse_proof(encoded(value),"PLAY",10310)["fallback"])
        for invalid in (True,2,-1):
            value=proof("PLAY");value["repairs"]=invalid;self.reject_proof(value)

    def test_exact_hash_links_and_changed_reopen_identity_are_required(self):
        prior=proof("SOURCE_PREFLIGHT")
        for phase,key in (("IMPORT","preflight"),("PLAY","import"),("REOPEN","play")):
            raw=encoded(prior);current=proof(phase);current["prior_"+key+"_sha256"]=q.sha(raw)
            self.assertTrue(r.link_proofs(prior,raw,current))
            wrong=copy.deepcopy(current);wrong["prior_"+key+"_sha256"]="0"*64
            with self.assertRaises(AssertionError):r.link_proofs(prior,raw,wrong)
            prior=current
        prior=proof("PLAY");current=proof("REOPEN");current["prior_play_sha256"]=q.sha(encoded(prior));current.update(pid=601,start=1000)
        with self.assertRaises(AssertionError):r.link_proofs(prior,encoded(prior),current)

    def test_failed_skipped_foreign_and_duplicate_runner_never_qualify(self):
        for phase in r.PHASES:
            raw=transcript(phase)
            for wrong in (raw.replace(b"STATUS_CODE: 0",b"STATUS_CODE: -2"),raw.replace(b"STATUS_CODE: 0",b"STATUS_CODE: -4"),
                          raw+raw,raw.replace(b"numtests=1",b"numtests=2"),raw.replace(b"org.locallore.app.",b"org.other.app.")):
                with self.assertRaises((AssertionError,ValueError)):r.parse_runner(wrong,phase)

    def test_preflight_admission_never_grants_model_or_sdk_authority(self):
        with tempfile.TemporaryDirectory() as directory:
            value=proposal(Path(directory))
            with patch.object(q,"APK_HASHES",value["apk_sha256"]):
                self.assertTrue(r.validate_proposal(value))
                p,a=Path(directory)/"p.json",Path(directory)/"a.json";p.write_bytes(encoded(value))
                grant={"version":1,"proposal_sha256":q.sha(p.read_bytes()),"allow_device_calls":True,"root_go_pending":False,
                       "allow_local_weight_copy":False,"allow_sdk_calls":False}
                a.write_bytes(encoded(grant));self.assertEqual(r.authorize(p,a,directory),value)
                for key in ("allow_local_weight_copy","allow_sdk_calls"):
                    a.write_bytes(encoded(dict(grant,**{key:True})))
                    with self.assertRaises(AssertionError):r.authorize(p,a,directory)
                wrong=copy.deepcopy(value);wrong["phase"]="candidate"
                with self.assertRaises((AssertionError,TypeError)):r.validate_proposal(wrong)

    def test_wrong_source_identity_and_symlink_refuse_without_reading_weights(self):
        self.assertEqual(r.source_path({"path":str(r.PROBE_PATH.resolve()),"bytes":r.PROBE_BYTES,"sha256":r.PROBE_SHA},"preflight"),r.PROBE_PATH.resolve())
        with tempfile.TemporaryDirectory() as directory:
            p=Path(directory)/"not-a-model.litertlm";p.write_bytes(b"Original tiny refusal fixture")
            with self.assertRaises(AssertionError):r.source_path({"path":str(p),"bytes":r.MODEL_BYTES,"sha256":r.MODEL_SHA},"candidate")
            link=Path(directory)/"linked.litertlm"
            try:link.symlink_to(p)
            except OSError:return  # Platform may prohibit creating links; wrong-size oracle above still ran.
            with self.assertRaises(AssertionError):r.source_path({"path":str(link),"bytes":r.MODEL_BYTES,"sha256":r.MODEL_SHA},"candidate")

    def test_fixed_source_scripts_have_no_adopt_replace_or_shell_temp_path(self):
        for phase,name in (("preflight","probe.txt"),("candidate","model.litertlm")):
            command=r.source_write(10310,phase)
            self.assertEqual(command[:4],("run-as",q.APP,"sh","-c"))
            self.assertIn("set -C",command[4]);self.assertIn("-eq 25",command[4]);self.assertTrue(command[4].endswith("cat > "+r.SOURCE_ROOT+"/"+name))
            self.assertNotIn("/data/local/tmp",command[4]);self.assertNotIn("rm ",command[4]);self.assertNotIn("mv ",command[4])
        for uid in (True,1,-1,"10310"):
            with self.assertRaises(AssertionError):r.source_write(uid,"candidate")

    def transfer_fixture(self,root):
        value=fixture.proposal(root);value.update(phase="preflight",source={"bytes":r.PROBE_BYTES})
        lease=fixture.Lease(value);owner=r.Owner(value,lease);owner.stage="source-stream";owner.uid_map={q.APP:10310,q.TEST:10311}
        owner.proposal_path=root/"proposal.json";owner.authorization_path=root/"auth.json"
        owner.proposal_path.write_bytes(b"proposal");owner.authorization_path.write_bytes(b"grant")
        q.write_json(owner.directory/"installed-facts.json",{"packages":value["apk_sha256"],"uid_map":owner.uid_map,
            "processes":{"target":[],"test_helper":[]},"userdata":{"available_bytes":q.contract.USERDATA_FLOOR+r.PROBE_BYTES}})
        return owner,lease

    def test_transfer_is_one_shot_and_client_zero_never_verifies_destination(self):
        with tempfile.TemporaryDirectory() as directory:
            owner,lease=self.transfer_fixture(Path(directory))
            with patch.object(r.environment,"process_identity",return_value={"pid":42,"creation_filetime":3,"executable":sys.executable}),patch.object(q.host,"run_process",return_value=stream_result()) as run:
                body=owner.transfer();self.assertFalse(body["destination_verified"]);self.assertFalse(body["remote_exit_status_known"])
                with self.assertRaises(AssertionError):owner.transfer()
                self.assertEqual(run.call_count,1)
                self.assertTrue(run.call_args.kwargs["request"].startswith(r.STREAM_REQUEST))
                self.assertLessEqual(run.call_args.kwargs["deadline"],180)

    def test_unknown_cleanup_loss_spawn_or_retention_error_fences_transfer(self):
        for mode in ("unclean","lost","spawn","retention"):
            with self.subTest(mode=mode),tempfile.TemporaryDirectory() as directory:
                owner,lease=self.transfer_fixture(Path(directory))
                def send(*args,**kwargs):
                    if mode=="spawn":raise OSError("private spawn error")
                    if mode=="lost":lease.live=False
                    return stream_result(mode!="unclean")
                original_write=q.write_json
                def retain(path,value):
                    if mode=="retention" and Path(path).name.startswith("command-"):raise OSError("private retention error")
                    return original_write(path,value)
                with patch.object(r.environment,"process_identity",return_value={"pid":42,"creation_filetime":3,"executable":sys.executable}), \
                     patch.object(q.host,"run_process",side_effect=send) as run,patch.object(q,"write_json",side_effect=retain):
                    with self.assertRaises((AssertionError,OSError,RuntimeError)):owner.transfer()
                    with self.assertRaises((AssertionError,OSError,RuntimeError)):owner.transfer()
                    self.assertEqual(run.call_count,1)
                if mode not in ("spawn",):self.assertTrue((owner.commands/"command-0001.stdout.bin").is_file())

    def test_continuation_helper_is_bound_and_sticky_without_app_authority(self):
        row={"pid":604,"uid":10311,"name":q.TEST};b=r.ContinuedBoundary({"target":[],"test_helper":[row]});row["pid"]=999
        uids={q.APP:10310,q.TEST:10311};raw=("PID UID NAME\n604 10311 "+q.TEST+"\n").encode()
        self.assertEqual(b.observe(raw,uids,label="continued-before",stage="before",methods=0)["target"],[])
        b.observe(b"PID UID NAME\n",uids,label="after-import",stage="after",methods=1)
        with self.assertRaises(AssertionError):b.observe(raw,uids,label="after-play",stage="after",methods=2)
        with self.assertRaises(AssertionError):b.observe(b"PID UID NAME\n",uids,label="after-play",stage="after",methods=2)

    def test_worker_barrier_refuses_before_authorization_or_any_device_action(self):
        for prefix in (b"",b"wrong\n"):
            with patch.object(r.sys,"stdin",SimpleNamespace(buffer=io.BytesIO(prefix))),patch.object(r,"authorize") as auth:
                with self.assertRaises(AssertionError):r.worker("p","a","e")
                auth.assert_not_called()
                with self.assertRaises(AssertionError):r.stream_worker("p","a","e")
                auth.assert_not_called()

    def test_stream_worker_hashes_held_fd_under_live_parent_and_claims_once(self):
        with tempfile.TemporaryDirectory() as directory:
            owner,lease=self.transfer_fixture(Path(directory));value=owner.proposal
            value["source"]={"path":str(r.PROBE_PATH.resolve()),"bytes":r.PROBE_BYTES,"sha256":r.PROBE_SHA}
            identity={"pid":42,"creation_filetime":3,"executable":sys.executable}
            parent={"version":1,"parent":identity,"proposal_sha256":q.sha(owner.proposal_path.read_bytes()),
                "authorization_sha256":q.sha(owner.authorization_path.read_bytes()),"phase":"preflight","uid":10310,
                "facts_sha256":q.sha((owner.directory/"installed-facts.json").read_bytes()),"deadline_epoch":time.time()+90}
            q.write_json(owner.directory/"stream-parent-v1.json",parent)
            def child(argv,**kwargs):
                self.assertEqual(argv[1:7],["-H","127.0.0.1","-P","5037","-s",lease.descriptor["serial"]])
                self.assertEqual(argv[7],"exec-in");self.assertEqual(kwargs["stdin"].read(),r.PROBE_PATH.read_bytes())
                self.assertEqual(kwargs["stdout"],r.subprocess.DEVNULL);self.assertEqual(kwargs["stderr"],r.subprocess.DEVNULL)
                self.assertLessEqual(kwargs["timeout"],150)
                return SimpleNamespace(returncode=0)
            with patch.object(r,"authorize",return_value=value),patch.object(q,"open_lease",return_value=lease), \
                 patch.object(q,"APK_HASHES",value["apk_sha256"]),patch.object(r.environment,"process_identity",return_value=identity),patch.object(r.os,"getppid",return_value=42), \
                 patch.object(r.subprocess,"CREATE_NO_WINDOW",0,create=True),patch.object(r.subprocess,"run",side_effect=child) as run, \
                 patch.object(r.sys,"stdin",SimpleNamespace(buffer=io.BytesIO(r.STREAM_REQUEST+b"10310\n"))):
                output=io.StringIO()
                with redirect_stdout(output):self.assertEqual(r.stream_worker(owner.proposal_path,owner.authorization_path,directory),0)
                self.assertFalse(json.loads(output.getvalue())["destination_verified"])
                with patch.object(r.sys,"stdin",SimpleNamespace(buffer=io.BytesIO(r.STREAM_REQUEST+b"10310\n"))):
                    with self.assertRaises(FileExistsError):r.stream_worker(owner.proposal_path,owner.authorization_path,directory)
                self.assertEqual(run.call_count,1)
            self.assertTrue((owner.directory/"stream-worker-claimed-v1.json").is_file())

    def test_stream_without_parent_or_with_expired_parent_cannot_spawn(self):
        for expired in (False,True):
            with tempfile.TemporaryDirectory() as directory:
                owner,lease=self.transfer_fixture(Path(directory));value=owner.proposal
                if expired:
                    q.write_json(owner.directory/"stream-parent-v1.json",{"version":1,"parent":{"pid":42,"creation_filetime":3,"executable":sys.executable},
                        "proposal_sha256":q.sha(owner.proposal_path.read_bytes()),"authorization_sha256":q.sha(owner.authorization_path.read_bytes()),
                        "phase":"preflight","uid":10310,"facts_sha256":"c"*64,"deadline_epoch":time.time()-1})
                with patch.object(r,"authorize",return_value=value),patch.object(q,"open_lease",return_value=lease), \
                     patch.object(r.environment,"process_identity",return_value={"pid":42,"creation_filetime":3,"executable":sys.executable}),patch.object(r.os,"getppid",return_value=42), \
                     patch.object(r.subprocess,"run") as run,patch.object(r.sys,"stdin",SimpleNamespace(buffer=io.BytesIO(r.STREAM_REQUEST+b"10310\n"))):
                    with self.assertRaises((AssertionError,FileNotFoundError)):r.stream_worker(owner.proposal_path,owner.authorization_path,directory)
                    run.assert_not_called()

    def test_complete_mock_preflight_never_moves_weights_or_enters_sdk(self):
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory);value=proposal(root);lease=fixture.Lease(value);owner=r.Owner(value,lease)
            owner.proposal_path=root/"p.json";owner.authorization_path=root/"a.json"
            owner.proposal_path.write_bytes(encoded(value));owner.authorization_path.write_bytes(b"mock grant")
            transport=fixture.Transport(value,lease)
            def dispatch(argv,**kwargs):
                if argv[0]==sys.executable:return stream_result()
                if argv[3]=="shell":
                    op=tuple(shlex.split(argv[4]))
                    if op==r.source_create(10310):raw=b""
                    elif op==r.selection("SOURCE_PREFLIGHT"):
                        transport.instruments+=1;raw=transcript("SOURCE_PREFLIGHT")
                    elif op==r.proof_command("SOURCE_PREFLIGHT",10310,True):raw=b""
                    elif op==r.proof_command("SOURCE_PREFLIGHT",10310):raw=encoded(proof("SOURCE_PREFLIGHT"))
                    else:return transport(argv,**kwargs)
                    return SimpleNamespace(status="completed",returncode=0,cleanup_complete=True,stdout=raw,stderr_bytes=0,elapsed_ms=1)
                return transport(argv,**kwargs)
            with patch.object(q,"APK_HASHES",value["apk_sha256"]),patch.object(q.host,"run_process",side_effect=dispatch), \
                 patch.object(q.shutil,"disk_usage",return_value=SimpleNamespace(free=20*r.GIB)), \
                 patch.object(r.environment,"process_identity",return_value={"pid":42,"creation_filetime":3,"executable":sys.executable}):
                result=r.run_cohort(owner)
            self.assertFalse(result["model_copied"]);self.assertFalse(result["guarded_sdk_gift_observed"])
            self.assertEqual(transport.instruments,1);self.assertEqual(transport.installs,2)
            self.assertEqual(result["proof"],proof("SOURCE_PREFLIGHT"))


if __name__=="__main__":unittest.main()
