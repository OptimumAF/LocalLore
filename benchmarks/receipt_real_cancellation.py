"""One fixed real-receipt cancellation/recovery control, disabled by default.

Reuses source preflight/import; never replaces the original four-phase family.
Copyright 2026 LocalLore contributors. SPDX-License-Identifier: Apache-2.0
"""
import argparse
import json
import os
from pathlib import Path
import re
import shlex
import sys
import time

sys.path.insert(0, str(Path(__file__).resolve().parent))
import receipt_real_candidate as r

q, environment, worker_trace = r.q, r.environment, r.worker_trace
SCOPE = "receipt_real_cancellation"
REQUEST = b"receipt-real-cancellation-v1\n"
PROOF_ROOT = "no_backup/receipt-cancel-proof-v1"
PHASES = {
    "CANCEL": ("cancel", "ReceiptRealCancelTest", "cancelsSampledPublicInferenceWithoutCommit", 170_000, frozenset((
        "prior_import_proof_exact", "memory_eligible", "candidate_access_receipt", "accepted_full_recheck",
        "runtime_guard_passed", "production_transport_local", "gateway_main_confined", "canonical_zero_before",
        "fixed_free_text_submitted_once", "sampled_public_inflight", "cancel_saved_called_once", "original_response_joined",
        "response_rejected_cancelled", "no_prepared_or_commit", "sdk_cancel_entered_returned", "worker_drain_closed_known",
        "canonical_zero_after", "accepted_post_sdk_full_recheck", "source_unopened", "candidate_owner_retained", "native_handle_closed"))),
    "RECOVER": ("recover", "ReceiptRealRecoverTest", "recoversCancelledWorkspaceAndCommitsOneRealGift", 170_000,
        (r.PHASES["PLAY"][4] - {"initial_revision_zero"}) | {"initial_canonical_zero", "prior_cancel_proof_exact",
            "process_identity_changed", "source_unopened", "gateway_main_confined"}),
    "REOPEN": ("reopen", "ReceiptRealCancelReopenTest", "reopensRecoveredReceiptWithoutSdk", 120_000,
        (r.PHASES["REOPEN"][4] - {"prior_play_proof_exact"}) | {"prior_recover_proof_exact", "gateway_main_confined"}),
}
SOURCE_FILES = (*r.SOURCE_FILES, "benchmarks/receipt_real_cancellation.py", "scripts/tests/test_receipt_real_cancellation.py",
    "apps/android/app/src/modelReceipt/java/org/locallore/app/CancellationProof.kt",
    "apps/android/app/src/modelReceiptTest/java/org/locallore/app/CancellationProofTest.kt",
    "apps/android/app/src/modelReceiptAndroidTest/java/org/locallore/app/ReceiptRealCancellationTest.kt",
    "docs/native/RECEIPT_REAL_CANCELLATION_PROTOCOL.md")
TRACES = {"CANCEL": ("cancel-sample-worker-v2.json", "cancel-worker-v2.json"), "RECOVER": ("recover-worker-v2.json",), "REOPEN": ()}
PRIOR = {"CANCEL": "import", "RECOVER": "cancel", "REOPEN": "recover"}


def selection(phase):
    assert phase in PHASES
    return ("am", "instrument", "-w", "-r", "-e", "class", "org.locallore.app." + PHASES[phase][1],
            q.TEST + "/androidx.test.runner.AndroidJUnitRunner")


def parse_runner(raw, phase):
    assert phase in PHASES
    # Preserve the shared runner's conservative 120-second gate, independently
    # of the fixture proof budgets (170/170/120 seconds) and client cap.
    return q._parse_selected_instrumentation(raw, "org.locallore.app." + PHASES[phase][1], frozenset((PHASES[phase][2],)))


def digest_field(value):
    assert type(value) is str and re.fullmatch(r"[a-f0-9]{64}", value)


def parse_proof(raw, phase, uid):
    assert phase in PHASES and type(raw) is bytes and 0 < len(raw) <= 4096
    r.integer(uid, 10000, 2 ** 31 - 1)
    extra = {"prior_pid", "prior_start", "prior_" + PRIOR[phase] + "_sha256", "revision", "receipt_count"}
    if phase == "CANCEL": extra |= {"sample_worker_trace_sha256", "worker_trace_sha256"}
    else: extra |= {"receipt_sha256"}
    if phase == "RECOVER": extra |= {"repairs", "fallback", "worker_trace_sha256"}
    value = q.contract.strict_json(raw)
    assert type(value) is dict and set(value) == r.COMMON_KEYS | extra
    assert type(value["version"]) is int and value["version"] == 1 and value["phase"] == phase
    r.integer(value["pid"], 1, 2 ** 31 - 1); r.integer(value["start"], 0)
    assert type(value["uid"]) is int and value["uid"] == uid and value["process"] == q.APP
    assert type(value["model_bytes"]) is int and value["model_bytes"] == r.MODEL_BYTES and value["model_sha256"] == r.MODEL_SHA
    for kind in ("verify", "import"):
        for suffix in ("opened", "closed", "bytes"):
            assert type(value["source_" + kind + "_" + suffix]) is int and value["source_" + kind + "_" + suffix] == 0
    assert value["sdk_invoked"] is (phase != "REOPEN") and value["publication_native_invoked"] is False
    r.integer(value["elapsed_ms"], 0, PHASES[phase][3])
    total = r.integer(value["memory_total_bytes"], 7 * r.GIB, 8 * r.GIB)
    r.integer(value["memory_available_before"], 4 * r.GIB, total)
    r.integer(value["memory_available_after"], 0, total)
    for when in ("before", "after"):
        r.integer(value["userdata_free_" + when], q.contract.USERDATA_FLOOR)
        r.integer(value["external_free_" + when], 2 * r.GIB)
    assert type(value["checks"]) is dict and set(value["checks"]) == PHASES[phase][4]
    assert all(check is True for check in value["checks"].values())
    r.integer(value["prior_pid"], 1, 2 ** 31 - 1); r.integer(value["prior_start"], 0)
    for key in extra:
        if key.endswith("_sha256"): digest_field(value[key])
    revision = 0 if phase == "CANCEL" else 1
    assert type(value["revision"]) is int and value["revision"] == revision
    assert type(value["receipt_count"]) is int and value["receipt_count"] == revision
    if phase == "RECOVER":
        r.integer(value["repairs"], 0, 1); assert type(value["fallback"]) is bool
    return value


def link_proofs(prior, prior_raw, current):
    assert q.contract.strict_json(prior_raw) == prior
    assert prior["phase"] == PRIOR[current["phase"]].upper()
    assert (current["prior_pid"], current["prior_start"], current["prior_" + PRIOR[current["phase"]] + "_sha256"]) == (
        prior["pid"], prior["start"], q.sha(prior_raw))
    assert (current["uid"], current["process"]) == (prior["uid"], prior["process"])
    if current["phase"] != "CANCEL":
        assert (current["pid"], current["start"]) != (prior["pid"], prior["start"])
    if current["phase"] == "REOPEN": assert current["receipt_sha256"] == prior["receipt_sha256"]


def validate_proposal(value):
    assert type(value) is dict and value.get("scope") == SCOPE and value.get("phase") == "candidate"
    base = dict(value, scope=r.SCOPE)
    r.validate_proposal(base)
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


class ContinuedBoundary:
    observations = (("continued-before", "before", 0), ("after-import", "after", 1),
        ("after-cancel", "after", 2), ("after-recover", "after", 3), ("after-reopen", "after", 4))

    def __init__(self, previous):
        assert set(previous) == {"target", "test_helper"} and previous["target"] == [] and len(previous["test_helper"]) <= 1
        self.helper = json.loads(json.dumps(previous["test_helper"]))
        self.retired = not self.helper
        self.bind_after_import = not self.helper
        self.next, self.refused = 0, False

    def observe(self, raw, uids, *, label, stage, methods):
        # Same helper retirement/binding rule as the original family, with
        # five fixed observations. No helper is rebound after retirement.
        try:
            assert not self.refused and self.next < len(self.observations)
            assert (label, stage, methods) == self.observations[self.next]
            parsed = q.contract.parse_processes(raw, uids, {})
            assert parsed["passive"] == [] and len(parsed["owned"]) <= 1
            rows = parsed["owned"]; assert all(row["name"] == q.TEST for row in rows)
            if self.next == 1 and self.bind_after_import:
                self.helper = json.loads(json.dumps(rows)); self.retired = not rows
                self.bind_after_import = False
            elif rows: assert not self.retired and rows == self.helper
            else: self.retired = True
            self.next += 1
            return {"target": [], "test_helper": [dict(row) for row in rows]}
        except BaseException:
            self.refused = True
            raise


class Owner(r.Owner):
    STREAM_SCRIPT = Path(__file__).resolve()

    def __init__(self, value, lease):
        super().__init__(value, lease)
        phases = ("IMPORT", *PHASES)
        self.instrumentation_steps = tuple((r.selection(phase) if phase == "IMPORT" else selection(phase),
            "instrument-" + phase, index) for index, phase in enumerate(phases))
        facts = q.contract.strict_json(Path(value["preflight"]["facts"]["path"]).read_bytes())
        self.process_boundary = ContinuedBoundary(facts["processes"])
        self.namespace_absence_attempted = False

    def check_cancel_namespace_absent(self):
        assert self.stage == "after" and self.methods == 1 and not self.namespace_absence_attempted
        self.namespace_absence_attempted = True
        assert read_fixed(self, namespace_command(self.uid_map[q.APP], True)) == b""


def proof_command(name, uid):
    assert name in {PHASES[p][0] + suffix for p in PHASES for suffix in ("-v1.json", "-ready-v1.txt")} | {n for files in TRACES.values() for n in files}
    r.integer(uid, 10000, 2 ** 31 - 1)
    path = PROOF_ROOT + "/" + name
    size = "-eq 0" if name.endswith("-ready-v1.txt") else "-gt 0"
    script = "test -d no_backup && test ! -L no_backup && test -d " + PROOF_ROOT + " && test ! -L " + PROOF_ROOT
    script += " && test $(stat -c %u " + PROOF_ROOT + ") -eq " + str(uid)
    script += " && test -f " + path + " && test ! -L " + path + " && test $(stat -c %u " + path + ") -eq " + str(uid)
    script += " && test $(wc -c < " + path + ") " + size + " && test $(wc -c < " + path + ") -le 4096 && cat " + path
    return ("run-as", q.APP, "sh", "-c", script)


def namespace_command(uid, absent=False):
    r.integer(uid, 10000, 2 ** 31 - 1); assert type(absent) is bool
    script = "test -d no_backup && test ! -L no_backup"
    if absent: script += " && test ! -e " + PROOF_ROOT + " && test ! -L " + PROOF_ROOT
    else:
        script += " && test -d " + PROOF_ROOT + " && test ! -L " + PROOF_ROOT
        script += " && test $(stat -c %u " + PROOF_ROOT + ") -eq " + str(uid)
        script += " && find " + PROOF_ROOT + " -mindepth 1 -maxdepth 1 -print"
    return ("run-as", q.APP, "sh", "-c", script)


def read_fixed(owner, command):
    owner.stage = "proofs"; owner.pending_read = command
    return owner.shell(command, cap=4096)


def trace_predicates(value, phase, sample=None):
    assert value["version"] == 2 and value["saturated"] == [] and value["time_saturated"] is False and value["creations_saturated"] is False
    counts, creations = value["counts"], value["creations"]
    number = value["creations_total"]
    assert all(c["returned_ms"] is not None and c["failed_ms"] is None and c["failure"] == "NONE" for c in creations)
    if phase in ("SAMPLE", "CANCEL"):
        assert number == 1 and [c["role"] for c in creations] == ["DIRECTOR"]
        assert counts["SEND_ENTERED"] == counts["SEND_RETURNED"] == 1
        assert counts["UNCERTAIN"] == 0
        if phase == "SAMPLE":
            assert counts["MESSAGE_RETURNED"] >= 1
            assert all(counts[key] == 0 for key in ("DONE_ENTERED", "ERROR_ENTERED", "CANCEL_ENTERED", "ENGINE_CLOSE_ENTERED"))
        else:
            assert all(counts[key] == 1 for key in ("CANCEL_ENTERED", "CANCEL_RETURNED", "DRAIN_SETTLED",
                "CONVERSATION_CLOSE_ENTERED", "CONVERSATION_CLOSE_KNOWN", "ENGINE_CLOSE_ENTERED", "ENGINE_CLOSE_KNOWN"))
            terminal = (counts["DONE_ENTERED"], counts["DONE_RETURNED"], counts["ERROR_ENTERED"], counts["ERROR_RETURNED"])
            assert terminal in ((1, 1, 0, 0), (0, 0, 1, 1))
            # Necessary same-object history consistency, not jointly atomic
            # native state or proof of what caused the public terminal.
            assert sample is not None and value["snapshot_ms"] >= sample["snapshot_ms"]
            assert creations[0] == sample["creations"][0]
            for event in worker_trace.EVENTS:
                assert counts[event] >= sample["counts"][event]
                if sample["last_ms"][event] is not None:
                    assert value["last_ms"][event] is not None and value["last_ms"][event] >= sample["last_ms"][event]
    else:
        assert phase == "RECOVER" and number in (2, 3)
        assert [c["role"] for c in creations] == (["DIRECTOR", "NARRATOR"] if number == 2 else ["DIRECTOR", "DIRECTOR", "NARRATOR"])
        assert all(counts[key] == number for key in ("CONVERSATION_CREATE_ENTERED", "CONVERSATION_CREATE_RETURNED", "SEND_ENTERED",
            "SEND_RETURNED", "DONE_ENTERED", "DONE_RETURNED", "DRAIN_SETTLED", "CONVERSATION_CLOSE_ENTERED", "CONVERSATION_CLOSE_KNOWN"))
        assert all(counts[key] == 0 for key in ("ERROR_ENTERED", "ERROR_RETURNED", "CANCEL_ENTERED", "CANCEL_RETURNED", "UNCERTAIN"))
        assert counts["ENGINE_CLOSE_ENTERED"] == counts["ENGINE_CLOSE_KNOWN"] == 1 and counts["MESSAGE_RETURNED"] > 0


def read_proof(owner, phase):
    assert phase in PHASES
    wanted = set()
    for p in PHASES:
        wanted |= {PROOF_ROOT + "/" + PHASES[p][0] + suffix for suffix in ("-v1.json", "-ready-v1.txt")}
        wanted |= {PROOF_ROOT + "/" + name for name in TRACES[p]}
        if p == phase: break
    manifest = q.normalized(read_fixed(owner, namespace_command(owner.uid_map[q.APP])), 4096).splitlines()
    assert len(manifest) == len(wanted) and set(manifest) == wanted
    stem = PHASES[phase][0]
    assert read_fixed(owner, proof_command(stem + "-ready-v1.txt", owner.uid_map[q.APP])) == b""
    raw = read_fixed(owner, proof_command(stem + "-v1.json", owner.uid_map[q.APP]))
    with (owner.directory / (stem + "-proof.raw.json")).open("xb") as stream:
        stream.write(raw); stream.flush(); os.fsync(stream.fileno())
    value = parse_proof(raw, phase, owner.uid_map[q.APP])
    traces = []
    for index, name in enumerate(TRACES[phase]):
        data = read_fixed(owner, proof_command(name, owner.uid_map[q.APP]))
        with (owner.directory / (name + ".raw")).open("xb") as stream:
            stream.write(data); stream.flush(); os.fsync(stream.fileno())
        key = "sample_worker_trace_sha256" if phase == "CANCEL" and index == 0 else "worker_trace_sha256"
        assert q.sha(data) == value[key]
        trace = worker_trace.parse_worker_trace(data)
        trace_predicates(trace, "SAMPLE" if phase == "CANCEL" and index == 0 else phase, traces[0] if traces else None)
        q.write_json(owner.directory / name, trace); traces.append(trace)
    q.write_json(owner.directory / (stem + "-proof-v1.json"), value)
    return value, raw


def run_selected(owner, phase):
    owner.stage = "instrument-" + phase
    raw = owner.shell(selection(phase), deadline=180, cap=131072)
    if phase in ("CANCEL", "RECOVER"):
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
        owner.stage = "after"; owner.facts("after-" + phase.lower(), q.APK_HASHES)
    return {"before": before, "transfer": transfer, "proofs": proofs, "model_copied": True,
        "real_sdk_cancellation_observed": True, "guarded_sdk_gift_observed": True,
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
    except BaseException: failure = "receipt_real_cancellation_stopped"
    # Inherited methods counts admitted step attempts, including a step refused
    # by the remaining-budget check. Raw client records establish dispatch.
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


if __name__ == "__main__":
    raise SystemExit(main())
