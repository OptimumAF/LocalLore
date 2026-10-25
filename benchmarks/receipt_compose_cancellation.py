"""Fixed real Compose Send/Cancel, visible recovery and reopen control.

Disabled until a fresh exact grant. The earlier gateway API control is unchanged.
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

r, q, worker_trace, environment = n.r, n.q, n.worker_trace, n.environment
SCOPE = "receipt_compose_cancellation"
REQUEST = b"receipt-compose-cancellation-v1\n"
PROOF_ROOT = "no_backup/receipt-compose-cancel-proof-v1"
BASE = {"UI_CANCEL": "CANCEL", "UI_RECOVER": "RECOVER", "UI_REOPEN": "REOPEN"}
PHASES = {
    "UI_CANCEL": ("cancel", "ReceiptComposeCancelTest", "cancelsRealTurnThroughComposeControls", 170_000, frozenset((
        "prior_import_proof_exact", "memory_eligible", "candidate_access_receipt", "accepted_full_recheck", "runtime_guard_passed",
        "production_main_activity", "production_shell_viewmodel", "production_transport_local", "empty_library_visible",
        "new_story_clicked_once", "canonical_zero_before", "initial_zero_visible", "local_provider_visible", "fixed_input_visible",
        "send_clicked_once", "preparing_visible", "sampled_public_inflight", "cancel_clicked_once", "cancellation_settled_visible",
        "worker_drain_closed_known", "canonical_zero_after", "accepted_post_sdk_full_recheck", "source_unopened",
        "candidate_owner_retained", "native_handle_closed", "cancel_control_displayed"))),
    "UI_RECOVER": ("recover", "ReceiptComposeRecoverTest", "sendsRecoveryGiftThroughCompose", 170_000, frozenset((
        "prior_cancel_proof_exact", "process_identity_changed", "memory_eligible", "candidate_access_receipt", "accepted_full_recheck",
        "runtime_guard_passed", "production_main_activity", "production_shell_viewmodel", "production_transport_local",
        "initial_canonical_zero", "initial_zero_visible", "local_provider_visible", "fixed_input_visible", "send_clicked_once",
        "accepted_gift_visible", "worker_drain_closed_known", "canonical_revision_one", "canonical_given_to_mira",
        "canonical_single_receipt", "local_profile_exact", "accepted_post_sdk_full_recheck", "source_unopened",
        "candidate_owner_retained", "native_handle_closed"))),
    "UI_REOPEN": ("reopen", "ReceiptComposeReopenTest", "showsRecoveredGiftWithoutSdk", 120_000, frozenset((
        "prior_recover_proof_exact", "process_identity_changed", "memory_eligible", "candidate_access_receipt", "accepted_full_recheck",
        "runtime_guard_passed", "production_main_activity", "production_shell_viewmodel", "production_transport_local",
        "retained_gift_visible", "no_send_or_cancel", "no_worker_events", "canonical_revision_one", "canonical_gift_receipt_unchanged",
        "source_unopened", "candidate_owner_retained", "native_handle_closed"))),
}
PRIOR_PHASE = {"UI_CANCEL": "IMPORT", "UI_RECOVER": "UI_CANCEL", "UI_REOPEN": "UI_RECOVER"}
PRIOR_KEY = {"UI_CANCEL": "import", "UI_RECOVER": "cancel", "UI_REOPEN": "recover"}
TRACES = {phase: n.TRACES[base] for phase, base in BASE.items()}
SOURCE_FILES = (*n.SOURCE_FILES, "benchmarks/receipt_compose_cancellation.py", "scripts/tests/test_receipt_compose_cancellation.py",
    "apps/android/app/src/modelReceipt/java/org/locallore/app/ReceiptComposeCancellationActivity.kt",
    "apps/android/app/src/modelReceipt/java/org/locallore/app/ComposeCancellationProof.kt",
    "apps/android/app/src/modelReceiptTest/java/org/locallore/app/ComposeCancellationProofTest.kt",
    "apps/android/app/src/modelReceiptAndroidTest/java/org/locallore/app/ReceiptComposeCancellationTest.kt",
    "docs/native/RECEIPT_COMPOSE_CANCELLATION_PROTOCOL.md", "apps/android/app/src/modelReceipt/AndroidManifest.xml",
    "apps/android/app/src/main/java/org/locallore/app/MainActivity.kt",
    "apps/android/app/src/main/java/org/locallore/app/ShellViewModel.kt",
    "apps/android/app/src/main/java/org/locallore/app/ui/LocalLoreScreen.kt",
    "apps/android/app/src/main/java/org/locallore/app/ui/PlayInputComposer.kt")


def selection(phase):
    assert phase in PHASES
    return ("am", "instrument", "-w", "-r", "-e", "class", "org.locallore.app." + PHASES[phase][1],
            q.TEST + "/androidx.test.runner.AndroidJUnitRunner")


def parse_runner(raw, phase):
    assert phase in PHASES
    # The unchanged shared runner has a conservative 120-second bound,
    # separately from the 170/170/120-second proof and 180-second client caps.
    return q._parse_selected_instrumentation(raw, "org.locallore.app." + PHASES[phase][1], frozenset((PHASES[phase][2],)))


def parse_proof(raw, phase, uid):
    assert phase in PHASES and type(raw) is bytes and 0 < len(raw) <= 4096
    r.integer(uid, 10000, 2 ** 31 - 1)
    extra = {"prior_pid", "prior_start", "prior_" + PRIOR_KEY[phase] + "_sha256", "revision", "receipt_count"}
    if phase == "UI_CANCEL": extra |= {"sample_worker_trace_sha256", "worker_trace_sha256"}
    else: extra |= {"receipt_sha256"}
    if phase == "UI_RECOVER": extra |= {"repairs", "fallback", "worker_trace_sha256"}
    value = q.contract.strict_json(raw)
    assert type(value) is dict and set(value) == r.COMMON_KEYS | extra
    assert type(value["version"]) is int and value["version"] == 1 and value["phase"] == phase
    r.integer(value["pid"], 1, 2 ** 31 - 1); r.integer(value["start"], 0)
    assert type(value["uid"]) is int and value["uid"] == uid and value["process"] == q.APP
    assert type(value["model_bytes"]) is int and value["model_bytes"] == r.MODEL_BYTES and value["model_sha256"] == r.MODEL_SHA
    for kind in ("verify", "import"):
        for suffix in ("opened", "closed", "bytes"):
            assert type(value["source_" + kind + "_" + suffix]) is int and value["source_" + kind + "_" + suffix] == 0
    assert value["sdk_invoked"] is (phase != "UI_REOPEN") and value["publication_native_invoked"] is False
    r.integer(value["elapsed_ms"], 0, PHASES[phase][3])
    total = r.integer(value["memory_total_bytes"], 7*r.GIB, 8*r.GIB)
    r.integer(value["memory_available_before"], 4*r.GIB, total); r.integer(value["memory_available_after"], 0, total)
    for when in ("before", "after"):
        r.integer(value["userdata_free_" + when], q.contract.USERDATA_FLOOR)
        r.integer(value["external_free_" + when], 2*r.GIB)
    assert type(value["checks"]) is dict and set(value["checks"]) == PHASES[phase][4]
    assert all(check is True for check in value["checks"].values())
    r.integer(value["prior_pid"], 1, 2 ** 31 - 1); r.integer(value["prior_start"], 0)
    for key in extra:
        if key.endswith("_sha256"): n.digest_field(value[key])
    revision = 0 if phase == "UI_CANCEL" else 1
    assert type(value["revision"]) is int and value["revision"] == revision
    assert type(value["receipt_count"]) is int and value["receipt_count"] == revision
    if phase == "UI_RECOVER":
        r.integer(value["repairs"], 0, 1); assert type(value["fallback"]) is bool
    return value


def link_proofs(prior, prior_raw, current):
    phase = current["phase"]
    assert phase in PHASES and q.contract.strict_json(prior_raw) == prior and prior["phase"] == PRIOR_PHASE[phase]
    assert (current["prior_pid"], current["prior_start"], current["prior_" + PRIOR_KEY[phase] + "_sha256"]) == (
        prior["pid"], prior["start"], q.sha(prior_raw))
    assert (current["uid"], current["process"]) == (prior["uid"], prior["process"])
    if phase != "UI_CANCEL": assert (current["pid"], current["start"]) != (prior["pid"], prior["start"])
    if phase == "UI_REOPEN": assert current["receipt_sha256"] == prior["receipt_sha256"]


def validate_proposal(value):
    assert type(value) is dict and value.get("scope") == SCOPE and value.get("phase") == "candidate"
    n.validate_proposal(dict(value, scope=n.SCOPE))
    assert all(str((q.ROOT / name).resolve()) in value["bindings"] for name in SOURCE_FILES)
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


def _compose_root(command):
    # Transform only the literal namespace in the existing closed grammar.
    # No proposal, CLI argument or external string chooses a path.
    assert len(command) == 5 and command[:4] == ("run-as", q.APP, "sh", "-c") and n.PROOF_ROOT in command[4]
    script = command[4].replace(n.PROOF_ROOT, PROOF_ROOT)
    assert n.PROOF_ROOT not in script
    return (*command[:4], script)


def proof_command(name, uid): return _compose_root(n.proof_command(name, uid))
def namespace_command(uid, absent=False): return _compose_root(n.namespace_command(uid, absent))


class Owner(n.Owner):
    STREAM_SCRIPT = Path(__file__).resolve()

    def __init__(self, value, lease):
        super().__init__(value, lease)
        self.instrumentation_steps = tuple((r.selection(phase) if phase == "IMPORT" else selection(phase),
            "instrument-" + phase, index) for index, phase in enumerate(("IMPORT", *PHASES)))

    def check_cancel_namespace_absent(self):
        assert self.stage == "after" and self.methods == 1 and not self.namespace_absence_attempted
        self.namespace_absence_attempted = True
        assert n.read_fixed(self, namespace_command(self.uid_map[q.APP], True)) == b""


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
        key = "sample_worker_trace_sha256" if phase == "UI_CANCEL" and index == 0 else "worker_trace_sha256"
        assert q.sha(data) == value[key]
        trace = worker_trace.parse_worker_trace(data)
        n.trace_predicates(trace, "SAMPLE" if phase == "UI_CANCEL" and index == 0 else BASE[phase], traces[0] if traces else None)
        q.write_json(owner.directory / name, trace); traces.append(trace)
    q.write_json(owner.directory / (stem + "-proof-v1.json"), value)
    return value, raw


def run_selected(owner, phase):
    assert phase in PHASES
    owner.stage = "instrument-" + phase
    raw = owner.shell(selection(phase), deadline=180, cap=131072)
    if phase != "UI_REOPEN":
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
    owner.check_cancel_namespace_absent()
    previous, previous_raw = imported, imported_raw; proofs = {"IMPORT": imported}
    for phase in PHASES:
        value, raw = run_selected(owner, phase); link_proofs(previous, previous_raw, value)
        proofs[phase] = value; previous, previous_raw = value, raw
        owner.stage = "after"; owner.facts("after-" + PHASES[phase][0], q.APK_HASHES)
    return {"before": before, "transfer": transfer, "proofs": proofs, "model_copied": True,
        "compose_send_cancel_observed": True, "visible_recovery_reopen_observed": True, "guarded_sdk_gift_observed": True,
        "physical_phone_qualified": False, "DocumentsUI_qualified": False}


def stream_worker(proposal_path, authorization_path, evidence):
    raw = sys.stdin.buffer.read(128)
    assert raw.startswith(r.STREAM_REQUEST) and re.fullmatch(rb"[1-9][0-9]{4,9}\n", raw[len(r.STREAM_REQUEST):])
    uid = r.integer(int(raw[len(r.STREAM_REQUEST):]), 10000, 2 ** 31 - 1)
    value = authorize(proposal_path, authorization_path, evidence)
    return r.stream_authorized(value, uid, proposal_path, authorization_path, evidence)


def worker(proposal_path, authorization_path, evidence):
    assert sys.stdin.buffer.read(128) == REQUEST
    value = authorize(proposal_path, authorization_path, evidence)
    owner = Owner(value, q.open_lease(value)); owner.proposal_path = proposal_path; owner.authorization_path = authorization_path
    result, failure = None, None
    try: result = run_cohort(owner)
    except BaseException: failure = "receipt_compose_cancellation_stopped"
    # Inherited methods counts attempts; raw retained clients establish dispatch.
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
