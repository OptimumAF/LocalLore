"""Fixed ordinary setup-to-play scene qualification, disabled until exact admission.

Reuses the original source preflight/import and owned clients. No input selects
an Activity, profile, phase sequence, proof path, SDK owner or stream program.
Copyright 2026 LocalLore contributors. SPDX-License-Identifier: Apache-2.0
"""
import argparse
import json
import os
from pathlib import Path
import re
import sys
import time

sys.path.insert(0, str(Path(__file__).resolve().parent))
import receipt_real_cancellation as n
import litert_send_trace as send_trace
import litert_callback_trace as callback_trace
import litert_status_trace as status_trace

r, q, worker_trace, environment = n.r, n.q, n.worker_trace, n.environment
SCOPE = "receipt_ordinary_scene"
REQUEST = b"receipt-ordinary-scene-v1\n"
PROOF_ROOT = "no_backup/receipt-ordinary-scene-proof-v1"
COMMON_CHECKS = frozenset(("memory_eligible", "setup_activity_exact", "setup_ready_visible", "start_enabled",
    "start_clicked_once", "setup_finished", "play_activity_exact", "play_resumed", "production_shell_viewmodel",
    "constructed_transport_observed", "production_transport_local", "source_unopened", "candidate_owner_retained", "native_handle_closed"))
PHASES = {
    "ORDINARY_START": ("start", "ReceiptOrdinaryStartTest", "startsFromSetupAndCommitsRealGift", 170_000,
        COMMON_CHECKS | {"prior_import_proof_exact", "new_story_clicked_once", "canonical_zero_before", "local_provider_visible",
            "fixed_action_visible", "send_clicked_once", "gift_visible", "gift_receipt_exact", "local_profile_exact",
            "canonical_revision_one", "single_receipt", "full_model_postcheck", "owner_guard_postcheck", "worker_closed_known"}),
    "ORDINARY_DIALOGUE": ("dialogue", "ReceiptOrdinaryDialogueTest", "inspectsGiftRejectsInvalidActionsAndRecordsDialogue", 170_000,
        COMMON_CHECKS | {"prior_start_proof_exact", "process_identity_changed", "initial_gift_receipts_exact", "progression_visible",
            "history_provenance_visible", "relationships_visible", "knowledge_known_truth_visible", "hidden_belief_search_empty",
            "hidden_beacon_search_empty", "event_source_navigation_visible", "inspector_canon_unchanged", "ability_action_rejected",
            "duplicate_gift_rejected", "guards_canon_unchanged", "guards_worker_zero", "dialogue_kind_selected", "fixed_dialogue_visible",
            "dialogue_send_clicked_once", "dialogue_visible", "literal_dialogue_receipt_exact", "statement_not_truth", "known_truth_unchanged",
            "gift_receipt_preserved", "canonical_revision_two", "two_receipts", "local_profile_exact", "full_model_postcheck",
            "owner_guard_postcheck", "worker_closed_known"}),
    "ORDINARY_REOPEN": ("reopen", "ReceiptOrdinaryReopenTest", "reopensTwoReceiptsThroughSetupWithoutSdk", 120_000,
        COMMON_CHECKS | {"prior_dialogue_proof_exact", "process_identity_changed", "two_receipts_exact", "retained_transcript_visible",
            "canonical_revision_two", "no_send_or_cancel", "worker_zero", "full_model_postcheck", "owner_guard_postcheck"}),
}
PRIOR_PHASE = {"ORDINARY_START": "IMPORT", "ORDINARY_DIALOGUE": "ORDINARY_START", "ORDINARY_REOPEN": "ORDINARY_DIALOGUE"}
PRIOR_KEY = {"ORDINARY_START": "import", "ORDINARY_DIALOGUE": "start", "ORDINARY_REOPEN": "dialogue"}
TRACES = {"ORDINARY_START": ("start-worker-v2.json",),
    "ORDINARY_DIALOGUE": ("guards-worker-v2.json", "dialogue-worker-v2.json"), "ORDINARY_REOPEN": ("reopen-worker-v2.json",)}
SOURCE_FILES = (*r.SOURCE_FILES, "benchmarks/receipt_real_cancellation.py", "scripts/tests/test_receipt_real_cancellation.py",
    "benchmarks/litert_send_trace.py", "scripts/tests/test_litert_send_trace.py",
    "apps/android/app/src/litert/java/org/locallore/app/LiteRtSendTrace.kt",
    "apps/android/app/src/litertTest/java/org/locallore/app/LiteRtSendTraceTest.kt",
    "docs/native/LITERT_SEND_TRACE_CONTRACT.md",
    "benchmarks/litert_callback_trace.py", "scripts/tests/test_litert_callback_trace.py",
    "apps/android/app/src/litert/java/org/locallore/app/LiteRtCallbackTrace.kt",
    "apps/android/app/src/litertTest/java/org/locallore/app/LiteRtCallbackTraceTest.kt",
    "apps/android/app/src/litertTest/java/org/locallore/app/LiteRtCallbackIntegrationTest.kt",
    "docs/native/LITERT_CALLBACK_TRACE_CONTRACT.md",
    "benchmarks/litert_status_trace.py", "scripts/tests/test_litert_status_trace.py",
    "apps/android/app/src/litert/java/org/locallore/app/LiteRtStatusTrace.kt",
    "apps/android/app/src/litertTest/java/org/locallore/app/LiteRtStatusTraceTest.kt",
    "apps/android/app/src/litertTest/java/org/locallore/app/LiteRtStatusIntegrationTest.kt",
    "docs/native/LITERT_STATUS_TRACE_CONTRACT.md",
    "apps/android/app/src/modelReceipt/java/org/locallore/app/CancellationProof.kt",
    "apps/android/app/src/modelReceiptTest/java/org/locallore/app/CancellationProofTest.kt",
    "benchmarks/receipt_ordinary_scene.py", "scripts/tests/test_receipt_ordinary_scene.py",
    "apps/android/app/src/modelReceipt/java/org/locallore/app/OrdinaryRouteProof.kt",
    "apps/android/app/src/modelReceiptTest/java/org/locallore/app/OrdinaryRouteProofTest.kt",
    "apps/android/app/src/modelReceiptAndroidTest/java/org/locallore/app/ReceiptOrdinaryRouteTest.kt",
    "docs/native/RECEIPT_ORDINARY_ROUTE_PROTOCOL.md",
    "apps/android/app/src/main/java/org/locallore/app/MainActivity.kt",
    "apps/android/app/src/litert/java/org/locallore/app/CandidateLocalModel.kt",
    "apps/android/app/src/litert/java/org/locallore/app/LocalModelSetupActivity.kt",
    "apps/android/app/src/litert/java/org/locallore/app/LocalModelSetupViewModel.kt",
    "apps/android/app/src/main/java/org/locallore/app/ShellViewModel.kt",
    "apps/android/app/src/main/java/org/locallore/app/StoryRecord.kt",
    "apps/android/app/src/main/java/org/locallore/app/StoryRecordWire.kt",
    "apps/android/app/src/main/java/org/locallore/app/StoryRecordController.kt",
    "apps/android/app/src/main/java/org/locallore/app/ui/StoryRecordDialog.kt",
    "apps/android/app/src/main/java/org/locallore/app/ui/LocalLoreScreen.kt",
    "apps/android/app/src/main/java/org/locallore/app/ui/PlayInputComposer.kt",
    "fixtures/lantern_quay.json", "crates/locallore/src/intent_guard.rs", "crates/locallore/src/play.rs",
    "crates/locallore/src/play/director_budget.rs", "crates/locallore/tests/portable_dialogue_schema.rs",
    "docs/native/PORTABLE_DIALOGUE_SCHEMA.md")


def selection(phase):
    assert phase in PHASES
    return ("am", "instrument", "-w", "-r", "-e", "class", "org.locallore.app." + PHASES[phase][1],
        q.TEST + "/androidx.test.runner.AndroidJUnitRunner")


def parse_runner(raw, phase):
    assert phase in PHASES
    # Keep the conservative runner Time<=120s gate separate from proof/client caps.
    return q._parse_selected_instrumentation(raw, "org.locallore.app." + PHASES[phase][1], frozenset((PHASES[phase][2],)))


def parse_proof(raw, phase, uid):
    assert phase in PHASES and type(raw) is bytes and 0 < len(raw) <= 4096
    r.integer(uid, 10000, 2**31-1)
    extra = {"prior_pid", "prior_start", "prior_" + PRIOR_KEY[phase] + "_sha256", "revision", "receipt_count",
        "receipts_sha256", "gift_receipt_sha256", "worker_trace_sha256"}
    if phase != "ORDINARY_START": extra |= {"dialogue_receipt_sha256"}
    if phase != "ORDINARY_REOPEN": extra |= {"repairs", "fallback"}
    if phase == "ORDINARY_DIALOGUE": extra |= {"guards_worker_trace_sha256"}
    value = q.contract.strict_json(raw)
    assert type(value) is dict and set(value) == r.COMMON_KEYS | extra
    assert type(value["version"]) is int and value["version"] == 1 and value["phase"] == phase
    r.integer(value["pid"], 1, 2**31-1); r.integer(value["start"], 0)
    assert type(value["uid"]) is int and value["uid"] == uid and value["process"] == q.APP
    assert type(value["model_bytes"]) is int and value["model_bytes"] == r.MODEL_BYTES and value["model_sha256"] == r.MODEL_SHA
    for kind in ("verify", "import"):
        for suffix in ("opened", "closed", "bytes"):
            assert type(value["source_" + kind + "_" + suffix]) is int and value["source_" + kind + "_" + suffix] == 0
    assert value["sdk_invoked"] is (phase != "ORDINARY_REOPEN") and value["publication_native_invoked"] is False
    r.integer(value["elapsed_ms"], 0, PHASES[phase][3])
    total = r.integer(value["memory_total_bytes"], 7*r.GIB, 8*r.GIB)
    r.integer(value["memory_available_before"], 4*r.GIB, total); r.integer(value["memory_available_after"], 0, total)
    for when in ("before", "after"):
        r.integer(value["userdata_free_" + when], q.contract.USERDATA_FLOOR)
        r.integer(value["external_free_" + when], 2*r.GIB)
    assert type(value["checks"]) is dict and set(value["checks"]) == PHASES[phase][4]
    assert all(check is True for check in value["checks"].values())
    r.integer(value["prior_pid"], 1, 2**31-1); r.integer(value["prior_start"], 0)
    for key in extra:
        if key.endswith("_sha256"): n.digest_field(value[key])
    revision = 1 if phase == "ORDINARY_START" else 2
    assert type(value["revision"]) is int and value["revision"] == revision
    assert type(value["receipt_count"]) is int and value["receipt_count"] == revision
    if phase != "ORDINARY_REOPEN":
        r.integer(value["repairs"], 0, 1); assert type(value["fallback"]) is bool
    return value


def link_proofs(prior, prior_raw, current):
    phase = current["phase"]
    assert phase in PHASES and q.contract.strict_json(prior_raw) == prior and prior["phase"] == PRIOR_PHASE[phase]
    assert (current["prior_pid"], current["prior_start"], current["prior_" + PRIOR_KEY[phase] + "_sha256"]) == (
        prior["pid"], prior["start"], q.sha(prior_raw))
    assert (current["uid"], current["process"]) == (prior["uid"], prior["process"])
    # Every ordinary phase starts a new process, including the first after import.
    assert (current["pid"], current["start"]) != (prior["pid"], prior["start"])
    if phase != "ORDINARY_START":
        assert current["gift_receipt_sha256"] == prior["gift_receipt_sha256"]
    if phase == "ORDINARY_REOPEN":
        assert current["receipts_sha256"] == prior["receipts_sha256"]
        assert current["dialogue_receipt_sha256"] == prior["dialogue_receipt_sha256"]


def validate_proposal(value):
    assert type(value) is dict and value.get("scope") == SCOPE and value.get("phase") == "candidate"
    # Only the top-level scope is adapted. Bound old preflight evidence stays old r scope.
    r.validate_proposal(dict(value, scope=r.SCOPE))
    assert all(str((q.ROOT / name).resolve()) in value["bindings"] for name in SOURCE_FILES)
    env = q.contract.strict_json(Path(value["environment_proposal_path"]).read_bytes())
    assert type(env["cores"]) is int and env["cores"] == 4
    return True


def authorize(proposal_path, authorization_path, evidence):
    raw = Path(proposal_path).read_bytes(); value = q.contract.strict_json(raw)
    auth = q.contract.strict_json(Path(authorization_path).read_bytes())
    assert type(auth) is dict and set(auth) == {"version", "proposal_sha256", "allow_device_calls", "root_go_pending", "allow_local_weight_copy", "allow_sdk_calls"}
    assert type(auth["version"]) is int and auth["version"] == 1 and auth["proposal_sha256"] == q.sha(raw)
    assert auth["allow_device_calls"] is True and auth["root_go_pending"] is False
    assert auth["allow_local_weight_copy"] is True and auth["allow_sdk_calls"] is True
    assert Path(value["evidence_root"]).resolve() == Path(evidence).resolve()
    validate_proposal(value)
    return value


class ContinuedBoundary(n.ContinuedBoundary):
    observations = (("continued-before", "before", 0), ("after-import", "after", 1),
        ("after-start", "after", 2), ("after-dialogue", "after", 3), ("after-reopen", "after", 4))


class Owner(r.Owner):
    STREAM_SCRIPT = Path(__file__).resolve()

    def __init__(self, value, lease):
        super().__init__(value, lease)
        self.instrumentation_steps = tuple((r.selection(p) if p == "IMPORT" else selection(p), "instrument-" + p, i)
            for i, p in enumerate(("IMPORT", *PHASES)))
        facts = q.contract.strict_json(Path(value["preflight"]["facts"]["path"]).read_bytes())
        self.process_boundary = ContinuedBoundary(facts["processes"])
        self.namespace_absence_attempted = False

    def check_namespace_absent(self):
        assert self.stage == "after" and self.methods == 1 and not self.namespace_absence_attempted
        self.namespace_absence_attempted = True
        assert n.read_fixed(self, namespace_command(self.uid_map[q.APP], True)) == b""


def proof_command(name, uid):
    assert name in {PHASES[p][0] + suffix for p in PHASES for suffix in ("-v1.json", "-ready-v1.txt")} | {x for xs in TRACES.values() for x in xs}
    r.integer(uid, 10000, 2**31-1)
    path = PROOF_ROOT + "/" + name
    size = "-eq 0" if name.endswith("-ready-v1.txt") else "-gt 0"
    script = "test -d no_backup && test ! -L no_backup && test -d " + PROOF_ROOT + " && test ! -L " + PROOF_ROOT
    script += " && test $(stat -c %u " + PROOF_ROOT + ") -eq " + str(uid)
    script += " && test -f " + path + " && test ! -L " + path + " && test $(stat -c %u " + path + ") -eq " + str(uid)
    script += " && test $(wc -c < " + path + ") " + size + " && test $(wc -c < " + path + ") -le 4096 && cat " + path
    return ("run-as", q.APP, "sh", "-c", script)


def namespace_command(uid, absent=False):
    r.integer(uid, 10000, 2**31-1); assert type(absent) is bool
    script = "test -d no_backup && test ! -L no_backup"
    if absent: script += " && test ! -e " + PROOF_ROOT + " && test ! -L " + PROOF_ROOT
    else:
        script += " && test -d " + PROOF_ROOT + " && test ! -L " + PROOF_ROOT
        script += " && test $(stat -c %u " + PROOF_ROOT + ") -eq " + str(uid)
        script += " && find " + PROOF_ROOT + " -mindepth 1 -maxdepth 1 -print"
    return ("run-as", q.APP, "sh", "-c", script)


def trace_predicates(value, phase, guards=None):
    assert value["version"] == 2 and value["saturated"] == [] and value["time_saturated"] is False and value["creations_saturated"] is False
    if phase in ("GUARDS", "ORDINARY_REOPEN"):
        assert value["creations_total"] == 0 and value["creations"] == []
        assert all(number == 0 for number in value["counts"].values())
        assert all(observed is None for observed in value["last_ms"].values())
    else:
        assert phase in ("ORDINARY_START", "ORDINARY_DIALOGUE")
        n.trace_predicates(value, "RECOVER")
        if phase == "ORDINARY_DIALOGUE":
            assert guards is not None and value["snapshot_ms"] >= guards["snapshot_ms"]
            for event in worker_trace.EVENTS:
                assert value["counts"][event] >= guards["counts"][event]
                if guards["last_ms"][event] is not None:
                    assert value["last_ms"][event] is not None and value["last_ms"][event] >= guards["last_ms"][event]


def read_proof(owner, phase):
    assert phase in PHASES
    wanted = set()
    for p in PHASES:
        wanted |= {PROOF_ROOT + "/" + PHASES[p][0] + suffix for suffix in ("-v1.json", "-ready-v1.txt")}
        wanted |= {PROOF_ROOT + "/" + name for name in TRACES[p]}
        if p == phase: break
    manifest = q.normalized(n.read_fixed(owner, namespace_command(owner.uid_map[q.APP])), 4096).splitlines()
    assert len(manifest) == len(wanted) and set(manifest) == wanted
    stem = PHASES[phase][0]
    assert n.read_fixed(owner, proof_command(stem + "-ready-v1.txt", owner.uid_map[q.APP])) == b""
    raw = n.read_fixed(owner, proof_command(stem + "-v1.json", owner.uid_map[q.APP]))
    with (owner.directory / (stem + "-proof.raw.json")).open("xb") as stream:
        stream.write(raw); stream.flush(); os.fsync(stream.fileno())
    value = parse_proof(raw, phase, owner.uid_map[q.APP]); traces = []
    for index, name in enumerate(TRACES[phase]):
        data = n.read_fixed(owner, proof_command(name, owner.uid_map[q.APP]))
        with (owner.directory / (name + ".raw")).open("xb") as stream:
            stream.write(data); stream.flush(); os.fsync(stream.fileno())
        key = "guards_worker_trace_sha256" if phase == "ORDINARY_DIALOGUE" and index == 0 else "worker_trace_sha256"
        assert q.sha(data) == value[key]
        trace = worker_trace.parse_worker_trace(data)
        trace_predicates(trace, "GUARDS" if phase == "ORDINARY_DIALOGUE" and index == 0 else phase, traces[0] if traces else None)
        q.write_json(owner.directory / name, trace); traces.append(trace)
    q.write_json(owner.directory / (stem + "-proof-v1.json"), value)
    return value, raw


def run_selected(owner, phase):
    assert phase in PHASES
    owner.stage = "instrument-" + phase
    raw = owner.shell(selection(phase), deadline=180, cap=131072)
    status = status_trace.extract_status_trace(raw)
    if status is not None: q.write_json(owner.directory / (PHASES[phase][0] + "-failure-status-v1.json"), status)
    callback = callback_trace.extract_callback_trace(raw)
    if callback is not None: q.write_json(owner.directory / (PHASES[phase][0] + "-failure-callback-v1.json"), callback)
    send = send_trace.extract_send_trace(raw)
    if send is not None: q.write_json(owner.directory / (PHASES[phase][0] + "-failure-send-v1.json"), send)
    if phase != "ORDINARY_REOPEN":
        trace = worker_trace.extract_worker_trace(raw)
        if trace is not None: q.write_json(owner.directory / (PHASES[phase][0] + "-failure-worker-v" + str(trace["version"]) + ".json"), trace)
    else:
        worker_trace.observe_worker_trace(owner, raw, "REOPEN")
        q.observe_failure_trace(owner, raw, "restart")
    result = parse_runner(raw, phase)
    q.write_json(owner.directory / (PHASES[phase][0] + "-instrumentation-v1.json"), result)
    return read_proof(owner, phase)


def run_cohort(owner):
    owner.wait_boot(); owner.check_guest_cpu_profile()
    before = owner.facts("continued-before", q.APK_HASHES)
    assert before["userdata"]["available_bytes"] - q.contract.USERDATA_FLOOR >= r.MODEL_BYTES
    owner.stage = "source-stream"; transfer = owner.transfer()
    previous_raw = Path(owner.proposal["preflight"]["proof"]["path"]).read_bytes()
    previous = r.parse_proof(previous_raw, "SOURCE_PREFLIGHT", owner.uid_map[q.APP])
    imported, imported_raw = r.run_selected(owner, "IMPORT"); r.link_proofs(previous, previous_raw, imported)
    owner.stage = "after"; owner.facts("after-import", q.APK_HASHES)
    owner.check_namespace_absent()
    previous, previous_raw = imported, imported_raw; proofs = {"IMPORT": imported}
    for phase in PHASES:
        value, raw = run_selected(owner, phase); link_proofs(previous, previous_raw, value)
        proofs[phase] = value; previous, previous_raw = value, raw
        owner.stage = "after"; owner.facts("after-" + PHASES[phase][0], q.APK_HASHES)
    return {"before": before, "transfer": transfer, "proofs": proofs, "model_copied": True,
        "ordinary_setup_start_observed": True, "guarded_sdk_gift_dialogue_observed": True,
        "inspector_and_no_sdk_reopen_observed": True, "physical_phone_qualified": False, "DocumentsUI_qualified": False}


def stream_worker(proposal_path, authorization_path, evidence):
    raw = sys.stdin.buffer.read(128)
    assert raw.startswith(r.STREAM_REQUEST) and re.fullmatch(rb"[1-9][0-9]{4,9}\n", raw[len(r.STREAM_REQUEST):])
    uid = r.integer(int(raw[len(r.STREAM_REQUEST):]), 10000, 2**31-1)
    value = authorize(proposal_path, authorization_path, evidence)
    return r.stream_authorized(value, uid, proposal_path, authorization_path, evidence)


def worker(proposal_path, authorization_path, evidence):
    assert sys.stdin.buffer.read(128) == REQUEST
    value = authorize(proposal_path, authorization_path, evidence)
    owner = Owner(value, q.open_lease(value)); owner.proposal_path = proposal_path; owner.authorization_path = authorization_path
    result, failure = None, None
    try: result = run_cohort(owner)
    except BaseException: failure = "receipt_ordinary_scene_stopped"
    # Methods counts attempts; retained raw client records establish actual dispatch.
    body = {"version": 1, "scope": SCOPE, "phase": "candidate", "status": "observed" if failure is None else "stopped",
        "failure": failure, "running_sha256": value["running_sha256"], "stage": owner.stage, "clients_cleaned": owner.clean,
        "owner_live": owner.owner_live, "command_count": owner.count, "instrumentation_commands": owner.methods,
        "installs": owner.installs, "result": result}
    q.write_json(owner.directory / "result-v1.json", body)
    print(json.dumps({key: body[key] for key in body if key != "result"}))
    return 0 if failure is None and owner.clean and owner.owner_live else 2


def run_owned(proposal_path, authorization_path, evidence):
    value = authorize(proposal_path, authorization_path, evidence); lease = q.open_lease(value); lease.check()
    assert lease.descriptor["deadline_epoch"] - time.time() >= 920
    root = Path(evidence); driver = root / "driver"; driver.mkdir(exist_ok=False)
    q.write_json(root / "receipt-owned-start-v1.json", {"version": 1, "deadline_seconds": 900,
        "proposal_sha256": q.sha(Path(proposal_path).read_bytes()), "authorization_sha256": q.sha(Path(authorization_path).read_bytes())})
    result = environment.supervise([sys.executable, "-B", "-E", str(Path(__file__).resolve()), "worker",
        "--proposal", str(proposal_path), "--authorization", str(authorization_path), "--evidence", str(evidence)],
        REQUEST, driver, 900, lambda child: True)
    q.write_json(root / "receipt-owned-result-v1.json", result); print(json.dumps(result))
    return 0 if result["status"] == "child_exited" and result["worker_returncode"] == 0 and result["cleanup_complete"] and result["output_capture_complete"] else 2


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("action", choices=("run", "worker", "_stream"))
    for name in ("proposal", "authorization", "evidence"): parser.add_argument("--" + name, type=Path, required=True)
    args = parser.parse_args(argv)
    if sys.flags.optimize: raise ValueError("optimized_controller_refused")
    if args.action == "_stream":
        try: return stream_worker(args.proposal, args.authorization, args.evidence)
        except BaseException:
            print(json.dumps({"status": "stream_failed", "remote_exit_status_known": False})); return 2
    return (run_owned if args.action == "run" else worker)(args.proposal, args.authorization, args.evidence)


if __name__ == "__main__": raise SystemExit(main())
