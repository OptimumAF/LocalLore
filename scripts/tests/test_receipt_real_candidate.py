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
    env = Path(value["environment_proposal_path"]); env.write_bytes(encoded({"memory_mib":8192,"host_available_memory_min":12*r.GIB,"cores":2}))
    value["bindings"][str(env.resolve())] = q.sha(env.read_bytes())
    for name in r.SOURCE_FILES:
        p = (q.ROOT/name).resolve(); value["bindings"][str(p)] = q.sha(p.read_bytes())
    return value


def stream_result(clean=True):
    body={"version":1,"source_bytes":r.PROBE_BYTES,"source_verified":True,"client_returncode":0,
          "remote_exit_status_known":False,"destination_verified":False}
    return SimpleNamespace(status="completed",returncode=0,cleanup_complete=clean,stdout=encoded(body),stderr_bytes=0,elapsed_ms=1)


class RealCandidateTests(unittest.TestCase):
    def cpu_fixture(self, root, cores=4):
        value = proposal(root)
        env = Path(value["environment_proposal_path"])
        env.write_bytes(encoded({"memory_mib": 8192, "host_available_memory_min": 12*r.GIB, "cores": cores}))
        lease = fixture.Lease(value)
        owner = r.Owner(value, lease)
        owner.stage = "before"
        return owner, lease

    def test_four_core_guest_observation_precedes_work_and_is_one_shot(self):
        with tempfile.TemporaryDirectory() as directory:
            owner, lease = self.cpu_fixture(Path(directory))
            value = SimpleNamespace(status="completed", returncode=0, cleanup_complete=True,
                                    stdout=b"0-3\n", stderr_bytes=0, elapsed_ms=1)
            with patch.object(q.host, "run_process", return_value=value) as run:
                owner.check_guest_cpu_profile()
                self.assertEqual(owner.stage, "before")
                self.assertEqual(owner.methods, 0)
                self.assertEqual(run.call_count, 1)
                self.assertEqual(run.call_args.args[0][-2:], ["shell", "cat /sys/devices/system/cpu/online"])
                self.assertLessEqual(run.call_args.kwargs["deadline"], 5)
                self.assertEqual(run.call_args.kwargs["max_output"], 128)
                with self.assertRaises(AssertionError): owner.check_guest_cpu_profile()
                self.assertEqual(run.call_count, 1)
            self.assertEqual(json.loads((owner.directory/"guest-cpu-profile-v1.json").read_bytes()),
                             {"version": 1, "requested_cores": 4, "observed_online_cores": 4})

    def test_guest_cpu_mismatch_or_unknown_cleanup_stops_before_copy_and_sdk(self):
        for raw, clean in [(b"0-1\n", True), (b"0-7\n", True), (b"4\n", True), (b"", True),
                           (b"0-3\nextra\n", True), (b"0-3\n", False)]:
            with self.subTest(raw=raw, clean=clean), tempfile.TemporaryDirectory() as directory:
                owner, lease = self.cpu_fixture(Path(directory))
                value = SimpleNamespace(status="completed", returncode=0, cleanup_complete=clean,
                                        stdout=raw, stderr_bytes=0, elapsed_ms=1)
                with patch.object(q.host, "run_process", return_value=value) as run, \
                     patch.object(owner, "wait_boot"), patch.object(owner, "facts") as facts, \
                     patch.object(owner, "transfer") as transfer, patch.object(r, "run_selected") as selected:
                    with self.assertRaises(AssertionError): r.run_cohort(owner)
                    facts.assert_not_called(); transfer.assert_not_called(); selected.assert_not_called()
                    with self.assertRaises(AssertionError): owner.check_guest_cpu_profile()
                    self.assertEqual(run.call_count, 1)
                self.assertFalse((owner.directory/"guest-cpu-profile-v1.json").exists())

    def test_two_core_profile_dispatches_no_new_guest_command(self):
        with tempfile.TemporaryDirectory() as directory:
            owner, _ = self.cpu_fixture(Path(directory), 2)
            with patch.object(q.host, "run_process") as run:
                owner.check_guest_cpu_profile()
                run.assert_not_called()
            self.assertEqual(owner.stage, "before")
            self.assertEqual(list(owner.commands.iterdir()), [])
            self.assertFalse((owner.directory/"guest-cpu-profile-v1.json").exists())

    def test_guest_cpu_retention_failure_or_late_owner_loss_stops_and_keeps_raw_client(self):
        for mode in ("retention", "late-owner-loss"):
            with self.subTest(mode=mode), tempfile.TemporaryDirectory() as directory:
                owner, lease = self.cpu_fixture(Path(directory))
                value = SimpleNamespace(status="completed", returncode=0, cleanup_complete=True,
                                        stdout=b"0-3\n", stderr_bytes=0, elapsed_ms=1)
                original_write = q.write_json
                def write(path, data):
                    if mode == "retention" and Path(path).name == "guest-cpu-profile-v1.json":
                        raise OSError("private evidence failure")
                    return original_write(path, data)
                def dispatch(*args, **kwargs):
                    if mode == "late-owner-loss": lease.live = False
                    return value
                with patch.object(q.host, "run_process", side_effect=dispatch) as run, \
                     patch.object(q, "write_json", side_effect=write), patch.object(owner, "wait_boot"), \
                     patch.object(owner, "facts") as facts, patch.object(owner, "transfer") as transfer, \
                     patch.object(r, "run_selected") as selected:
                    with self.assertRaises((AssertionError, OSError, RuntimeError)): r.run_cohort(owner)
                    facts.assert_not_called(); transfer.assert_not_called(); selected.assert_not_called()
                    with self.assertRaises(AssertionError): owner.check_guest_cpu_profile()
                    self.assertEqual(run.call_count, 1)
                self.assertEqual((owner.commands/"command-0001.stdout.bin").read_bytes(), b"0-3\n")
                self.assertTrue((owner.commands/"command-0001.json").is_file())
                self.assertFalse((owner.directory/"guest-cpu-profile-v1.json").exists())

    def test_guest_cpu_guard_cannot_run_after_work_or_unknown_owner(self):
        for mode in ("stage", "methods", "owner", "boolean"):
            with self.subTest(mode=mode), tempfile.TemporaryDirectory() as directory:
                owner, lease = self.cpu_fixture(Path(directory), True if mode == "boolean" else 4)
                if mode == "stage": owner.stage = "after"
                if mode == "methods": owner.methods = 1
                if mode == "owner": lease.live = False
                with patch.object(q.host, "run_process") as run:
                    with self.assertRaises((AssertionError, RuntimeError)): owner.check_guest_cpu_profile()
                    run.assert_not_called()

    def test_v2_role_timing_is_retained_before_failed_runner_without_enabling_later_actions(self):
        counts = {event: 0 for event in r.worker_trace.EVENTS}
        counts.update(CONVERSATION_CREATE_ENTERED=2, CONVERSATION_CREATE_RETURNED=1)
        last = {event: None for event in r.worker_trace.EVENTS}
        last.update(CONVERSATION_CREATE_ENTERED=100, CONVERSATION_CREATE_RETURNED=50)
        value = {"version": 2, "counts": counts, "saturated": [], "last_ms": last,
                 "snapshot_ms": 200, "time_saturated": False, "creations_total": 2,
                 "creations_saturated": False, "creations": [
                     {"ordinal": 1, "role": "DIRECTOR", "entered_ms": 20, "returned_ms": 50,
                      "failed_ms": None, "failure": "NONE"},
                     {"ordinal": 2, "role": "NARRATOR", "entered_ms": 100, "returned_ms": None,
                      "failed_ms": None, "failure": "NONE"}]}
        wire = (r.worker_trace.PREFIX + encoded(value).decode("ascii") +
                "\nINSTRUMENTATION_STATUS_CODE: 1337\nFAILURES!!!\n").encode("ascii")
        with tempfile.TemporaryDirectory() as directory:
            owner = SimpleNamespace(directory=Path(directory), shell=lambda *a, **kw: wire)
            with patch.object(r, "read_proof") as read:
                with self.assertRaises(AssertionError): r.run_selected(owner, "PLAY")
                read.assert_not_called()
            self.assertEqual(value, json.loads((Path(directory) / "play-worker-trace-v2.json").read_bytes()))
            self.assertFalse((Path(directory) / "play-instrumentation-v1.json").exists())
        for phase in r.PHASES:
            with tempfile.TemporaryDirectory() as directory:
                owner = SimpleNamespace(directory=Path(directory), shell=lambda *a, **kw: wire + transcript(phase))
                with patch.object(r, "read_proof") as read:
                    with self.assertRaises(AssertionError): r.run_selected(owner, phase)
                    read.assert_not_called()
                self.assertEqual([], list(Path(directory).iterdir()))

    def test_play_worker_observation_is_retained_before_unchanged_failed_runner_gate(self):
        counts = {event: 0 for event in r.worker_trace.EVENTS}
        counts["INITIALIZE_ENTERED"] = 1
        value = {"version": 1, "counts": counts, "saturated": []}
        wire = ("INSTRUMENTATION_STATUS: locallore_receipt_worker_v1=" + encoded(value).decode("ascii") +
                "\nINSTRUMENTATION_STATUS_CODE: 1337\nFAILURES!!!\n").encode("ascii")
        with tempfile.TemporaryDirectory() as directory:
            owner = SimpleNamespace(directory=Path(directory), shell=lambda *a, **kw: wire)
            with patch.object(r, "read_proof") as read:
                with self.assertRaises(AssertionError): r.run_selected(owner, "PLAY")
                read.assert_not_called()
            self.assertEqual(value, json.loads((Path(directory) / "play-worker-trace-v1.json").read_bytes()))
            self.assertFalse((Path(directory) / "play-instrumentation-v1.json").exists())

    def test_play_worker_trace_cannot_qualify_success_or_appear_in_other_phases(self):
        value = {"version": 1, "counts": {event: 0 for event in r.worker_trace.EVENTS}, "saturated": []}
        wire = ("INSTRUMENTATION_STATUS: locallore_receipt_worker_v1=" + encoded(value).decode("ascii") +
                "\nINSTRUMENTATION_STATUS_CODE: 1337\n").encode("ascii")
        for phase in r.PHASES:
            with tempfile.TemporaryDirectory() as directory:
                owner = SimpleNamespace(directory=Path(directory), shell=lambda *a, **kw: wire + transcript(phase))
                with patch.object(r, "read_proof") as read:
                    with self.assertRaises(AssertionError): r.run_selected(owner, phase)
                    read.assert_not_called()
                self.assertEqual([], list(Path(directory).iterdir()))

    def reject_proof(self, value):
        with self.assertRaises((AssertionError, ValueError, KeyError)): r.parse_proof(encoded(value), value["phase"], 10310)

    def test_all_four_literal_schemas_and_56_checks_are_closed(self):
        self.assertEqual([len(v[4]) for v in r.PHASES.values()], [12,16,15,13])
        for phase in r.PHASES:
            self.assertEqual(r.parse_proof(encoded(proof(phase)),phase,10310),proof(phase))
            self.assertEqual(r.parse_runner(transcript(phase),phase)["passed"],1)
            with self.assertRaises(AssertionError):q.parse_instrumentation(transcript(phase),q.INITIAL_CLASS,q.INITIAL_METHODS)

    def test_runner_uses_each_existing_fixed_phase_budget_only(self):
        self.assertEqual([value[3] for value in r.PHASES.values()], [30000,150000,170000,120000])
        for phase in r.PHASES:
            budget = r.PHASES[phase][3]
            exact = transcript(phase).replace(b"Time: 0.04", b"Time: " + str(budget//1000).encode())
            with patch.object(q,"_parse_selected_instrumentation",wraps=q._parse_selected_instrumentation) as parse:
                self.assertEqual(r.parse_runner(exact,phase)["passed"],1)
                self.assertEqual(parse.call_args.kwargs,{"phase_budget_ms":budget})
            beyond = transcript(phase).replace(b"Time: 0.04", b"Time: " + str(budget//1000).encode() + b".000000001")
            with self.assertRaises(AssertionError):r.parse_runner(beyond,phase)

    def test_import_over_synthetic120_but_within_existing150_is_not_a_failed_app(self):
        raw=transcript("IMPORT").replace(b"Time: 0.04",b"Time: 134.086")
        self.assertEqual(r.parse_runner(raw,"IMPORT")["passed"],1)
        cls="org.locallore.app."+r.PHASES["IMPORT"][1];methods=frozenset((r.PHASES["IMPORT"][2],))
        with self.assertRaises(AssertionError):q._parse_selected_instrumentation(raw,cls,methods)
        self.assertEqual(q._parse_selected_instrumentation(raw,cls,methods,phase_budget_ms=150000)["passed"],1)

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

    def transfer_fixture(self,root,owner_type=r.Owner):
        value=fixture.proposal(root);value.update(phase="preflight",source={"bytes":r.PROBE_BYTES})
        lease=fixture.Lease(value);owner=owner_type(value,lease);owner.stage="source-stream";owner.uid_map={q.APP:10310,q.TEST:10311}
        owner.proposal_path=root/"proposal.json";owner.authorization_path=root/"auth.json"
        owner.proposal_path.write_bytes(b"proposal");owner.authorization_path.write_bytes(b"grant")
        q.write_json(owner.directory/"installed-facts.json",{"packages":value["apk_sha256"],"uid_map":owner.uid_map,
            "processes":{"target":[],"test_helper":[]},"userdata":{"available_bytes":q.contract.USERDATA_FLOOR+r.PROBE_BYTES}})
        return owner,lease

    def test_transfer_script_is_fixed_by_trusted_control_not_proposal_input(self):
        class FixedControl(r.Owner):
            STREAM_SCRIPT = Path(__file__).resolve().parent / "trusted-cancel-driver.py"
        for owner_type in (r.Owner, FixedControl):
            with self.subTest(owner=owner_type.__name__), tempfile.TemporaryDirectory() as directory:
                owner, lease = self.transfer_fixture(Path(directory), owner_type)
                owner.proposal["stream_script"] = "untrusted-proposal-selection.py"
                with patch.object(r.environment, "process_identity", return_value={"pid": 42, "creation_filetime": 3, "executable": sys.executable}), \
                     patch.object(q.host, "run_process", return_value=stream_result()) as run:
                    owner.transfer()
                self.assertEqual(run.call_args.args[0][3], str(owner_type.STREAM_SCRIPT))
                self.assertNotIn("untrusted-proposal-selection.py", run.call_args.args[0])
                self.assertEqual(run.call_args.args[0][4], "_stream")

    def test_stream_sharing_does_not_bypass_barrier_or_fixed_authorizer(self):
        value = {"scope": r.SCOPE}
        for raw in (b"", b"wrong\n", r.STREAM_REQUEST+b"1\n"):
            with self.subTest(raw=raw), patch.object(r.sys, "stdin", SimpleNamespace(buffer=io.BytesIO(raw))), \
                 patch.object(r, "authorize") as auth, patch.object(r, "stream_authorized") as shared:
                with self.assertRaises(AssertionError): r.stream_worker("p", "a", "e")
                auth.assert_not_called(); shared.assert_not_called()
        with patch.object(r.sys, "stdin", SimpleNamespace(buffer=io.BytesIO(r.STREAM_REQUEST+b"10310\n"))), \
             patch.object(r, "authorize", side_effect=AssertionError("refused")) as auth, \
             patch.object(r, "stream_authorized") as shared:
            with self.assertRaises(AssertionError): r.stream_worker("p", "a", "e")
            auth.assert_called_once_with("p", "a", "e"); shared.assert_not_called()
        with patch.object(r.sys, "stdin", SimpleNamespace(buffer=io.BytesIO(r.STREAM_REQUEST+b"10310\n"))), \
             patch.object(r, "authorize", return_value=value) as auth, \
             patch.object(r, "stream_authorized", return_value=37) as shared:
            self.assertEqual(r.stream_worker("p", "a", "e"), 37)
            auth.assert_called_once_with("p", "a", "e")
            shared.assert_called_once_with(value, 10310, "p", "a", "e")

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

    def test_first_ui_helper_binds_only_after_successful_import(self):
        uids={q.APP:10310,q.TEST:10311};empty=b"PID UID NAME\n"
        row=("PID UID NAME\n604 10311 "+q.TEST+"\n").encode()
        boundary=r.ContinuedBoundary({"target":[],"test_helper":[]})
        boundary.observe(empty,uids,label="continued-before",stage="before",methods=0)
        self.assertEqual(boundary.observe(row,uids,label="after-import",stage="after",methods=1)["test_helper"],
                         [{"pid":604,"uid":10311,"name":q.TEST}])
        boundary.observe(row,uids,label="after-play",stage="after",methods=2)
        boundary.observe(empty,uids,label="after-reopen",stage="after",methods=3)
        for early in (True,False):
            boundary=r.ContinuedBoundary({"target":[],"test_helper":[]})
            if early:
                with self.assertRaises(AssertionError):boundary.observe(row,uids,label="continued-before",stage="before",methods=0)
            else:
                boundary.observe(empty,uids,label="continued-before",stage="before",methods=0)
                boundary.observe(empty,uids,label="after-import",stage="after",methods=1)
                with self.assertRaises(AssertionError):boundary.observe(row,uids,label="after-play",stage="after",methods=2)

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
