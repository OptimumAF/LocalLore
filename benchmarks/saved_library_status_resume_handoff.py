"""Bind one new activation of the preserved SDK23 prepared guest.

Copyright 2026 LocalLore contributors. SPDX-License-Identifier: Apache-2.0
"""
import copy
import os
from pathlib import Path
import uuid

from benchmarks import adb_held_socket_probe as python_pins
from benchmarks import isolated_adb_lease as server
from benchmarks import owned_saved_library_status as owner
from benchmarks import receipt_avd_environment as env
from benchmarks import receipt_avd_storage as storage
from benchmarks import saved_library_status_binding as artifacts
from benchmarks import saved_library_status_handoff as h
from benchmarks import saved_library_status_prepared_review as review

OUT = h.OUT.with_name("2026-11-09-saved-library-prepared-activation-v1")
PLAN = OUT / "plan-v1.json"
PROPOSAL = OUT / "PROPOSED_OPERATION.md"
AUTHORITY = OUT / "human-authority-v1.json"
ATTEMPT_ROOT = OUT / "attempt-v1"
ATTEMPT = ATTEMPT_ROOT / "claim-v1.json"
RUN = ATTEMPT_ROOT / "run-proposal-v1.json"
RUN_AUTHORITY = ATTEMPT_ROOT / "run-authorization-v1.json"
ADMISSION = ATTEMPT_ROOT / "admission-v1.json"
HANDOFF = ATTEMPT_ROOT / "boot-handoff-v1.json"
OWNED_ROOT = ATTEMPT_ROOT / "owned-v1"
OPERATION_SCOPE = "sdk23-activate-existing-saved-library-v1"
PLAN_SCOPE = "sdk23-saved-library-resume-plan-v1"
HANDOFF_SCOPE = "saved-library-status-resume-handoff-v1"
RUN_SCOPE = "owned-emulator-saved-library-status-resume-v1"
_HISTORY = {
    "original_authority": ("plan/human-authority-v1.json", h.AUTHORITY, 16384),
    "original_run": ("attempt/run-proposal-v1.json", h.RUN, h.STORAGE_CAP),
    "original_admission": ("attempt/admission-v1.json", h.ADMISSION, h.RECORD_CAP),
}
_need = env.require
_same = owner._same


def _history(manifest_pin):
    rows = h.at(manifest_pin, review.MANIFEST)["records_by_name"]
    pins = {key: rows[name] for key, (name, _, _) in _HISTORY.items()}
    for key, (_, path, cap) in _HISTORY.items():
        h._pin_at(pins[key], path, cap)
        env.check_binding(pins[key])
    return pins


def _canonical_run(pin):
    raw = h.files._bound(pin, cap=h.STORAGE_CAP)
    value = env.decode_json(raw)
    _need(env.encoded(value) == raw and value["phase"] == "run"
          and value["paths"]["root"] == str(h.GUEST)
          and _same(value["max_seconds"], h.ACTIVATION_SECONDS), "proposal")
    return value


def _source():
    return dict(source_root=str(h.ROOT), sources=owner.source_bindings(),
                handoff_source=env.binding(Path(__file__).resolve()),
                review_source=env.binding(Path(review.__file__).resolve()), python=python_pins._python_bindings(),
                artifacts=artifacts.artifact_bindings())


def inspect_plan(manifest_pin, ledger_pin):
    """Derive a prospective plan without creating an approval or attempt."""
    _need(not os.path.lexists(ATTEMPT_ROOT), "already_used")
    evidence = review.inspect(manifest_pin, ledger_pin)
    history = _history(manifest_pin)
    _canonical_run(history["original_run"])
    _need(not os.path.lexists(ATTEMPT_ROOT), "already_used")
    return dict(version=1, scope=PLAN_SCOPE, evidence=evidence, **_source(), **history)


def _check_plan(plan):
    owner._obj(plan, ("version", "scope", "source_root", "sources", "handoff_source", "review_source",
                      "python", "artifacts",
                      "evidence", *_HISTORY), "plan")
    _need(_same(plan["version"], 1) and plan["scope"] == PLAN_SCOPE, "plan")
    _need(all(_same(plan[key], value) for key, value in _source().items()), "source")
    evidence = plan["evidence"]
    owner._obj(evidence, ("version", "scope", "status", "manifest", "ledger", "guest_inputs",
                          "reserved_bytes", "execution_authorized"), "plan")
    _need(_same(evidence["version"], 1) and evidence["scope"] == review.SCOPE
          and evidence["status"] == "prepared_candidate" and evidence["execution_authorized"] is False
          and _same(evidence["reserved_bytes"], storage.RESERVATION_BYTES), "plan")
    h._pin_at(evidence["ledger"], h.LEDGER, h.STORAGE_CAP)
    receipt_path = h.OWNED_ROOT / "guest-inputs-v1.json"
    h._pin_at(evidence["guest_inputs"], receipt_path, h.RECORD_CAP)
    env.check_binding(evidence["guest_inputs"])
    _need(all(_same(plan[key], pin) for key, pin in _history(evidence["manifest"]).items()), "plan")


def read_authority(authority_pin):
    """Read only the new activation grant. The old grant is historical evidence."""
    authority = h.at(authority_pin, AUTHORITY, cap=16384)
    owner._obj(authority, ("version", "scope", "proposal", "plan", "approval_reference",
                           "allow_sdk_prepare", "allow_one_boot", "allow_model", "allow_retirement",
                           "max_operation_seconds"), "authority")
    ref = authority["approval_reference"]
    _need(_same(authority["version"], 1) and authority["scope"] == OPERATION_SCOPE
          and type(ref) is str and 0 < len(ref) <= 256 and ref == ref.strip()
          and all(32 <= ord(char) <= 126 for char in ref)
          and authority["allow_sdk_prepare"] is False and authority["allow_one_boot"] is True
          and authority["allow_model"] is False and authority["allow_retirement"] is False
          and _same(authority["max_operation_seconds"], h.SECONDS), "authority")
    plan = h.at(authority["plan"], PLAN, cap=131072)
    _check_plan(plan)
    prior, _ = h.read_authority(plan["original_authority"])
    _need(ref != prior["approval_reference"], "authority")
    h._pin_at(authority["proposal"], PROPOSAL, 65536)
    lines = h.files._bound(authority["proposal"], cap=65536).decode("utf-8").splitlines()
    labels = {"Plan SHA-256": authority["plan"], "Manifest SHA-256": plan["evidence"]["manifest"],
              "Ledger SHA-256": plan["evidence"]["ledger"]}
    for label, pin in labels.items():
        _need([line for line in lines if line.startswith(label)] == [label + " " + pin["sha256"]], "authority")
    env.check_binding(authority_pin)
    return authority, plan


def _claim(authority_pin):
    return dict(version=1, scope=OPERATION_SCOPE, authority=authority_pin, no_retry=True)


def begin_attempt(authority_pin):
    """Consume one separately granted attempt after replaying the live review."""
    _, plan = read_authority(authority_pin)
    evidence = plan["evidence"]
    _need(_same(inspect_plan(evidence["manifest"], evidence["ledger"]), plan), "plan")
    env.check_binding(authority_pin)
    env.safe_path(ATTEMPT_ROOT, exists=False).mkdir(exist_ok=False)
    return h.save(ATTEMPT, _claim(authority_pin))


def _approved_attempt(authority_pin, attempt_pin):
    authority, plan = read_authority(authority_pin)
    _need(_same(h.at(attempt_pin, ATTEMPT, cap=16384), _claim(authority_pin)), "attempt")
    return authority, plan


def _prepared(plan):
    proposal = _canonical_run(plan["original_run"])
    lock = h.LEDGER.with_name("admission.lock")
    _need(not os.path.lexists(lock), "ledger")
    current, entry = h.ledger_entry(h.GUEST)
    _need(_same(current, plan["evidence"]["ledger"]), "ledger")
    review._check_ledger_entry(entry, proposal["prepare_proposal"]["sha256"])
    for key in ("prepare_proposal", "prepared", "prepare_result"):
        env.check_binding(proposal[key])
    _need(not any(os.path.lexists(path) for path in (lock, h.GUEST / owner.BOOT_CLAIM_FILE,
               h.GUEST / "guest-storage-closure-v1.json", Path(proposal["paths"]["content"]) / "userdata-qemu.img")),
          "already_used")
    return proposal


def _admission_value(plan, run_pin, authorization_pin, run_id):
    original = h.at(plan["original_admission"], h.ADMISSION)
    admission = copy.deepcopy(owner.validate_admission(original))
    _need(run_id != admission["run_id"], "admission")
    admission.update(root=str(OWNED_ROOT), run_id=run_id, sources=plan["sources"],
                     python=plan["python"], artifacts=plan["artifacts"])
    admission["server"].update(root=str(OWNED_ROOT / "server"), run_id=run_id,
                               sources=server.source_bindings(), python=plan["python"])
    refuser_source = env.binding(h.ROOT / "benchmarks/native/deny_adb_client.c")
    _need(all(refuser_source[key] == admission["guest"]["refuser_source"][key]
              for key in ("bytes", "sha256")), "source")
    admission["guest"].update(proposal=run_pin, authorization=authorization_pin, refuser_source=refuser_source)
    return owner.validate_admission(admission)


def bind_admission(authority_pin, attempt_pin):
    """Publish only the fresh run inputs for the existing prepared guest."""
    _, plan = _approved_attempt(authority_pin, attempt_pin)
    _need(not any(os.path.lexists(path) for path in (RUN, RUN_AUTHORITY, ADMISSION, HANDOFF, OWNED_ROOT)),
          "already_used")
    proposal = _prepared(plan)
    run = h.save(RUN, proposal)
    _need(all(run[key] == plan["original_run"][key] for key in ("bytes", "sha256")), "proposal")
    authorization = h.save(RUN_AUTHORITY, dict(
        version=1, phase="run", run_scope=RUN_SCOPE, proposal_sha256=run["sha256"],
        allow_environment_calls=True, root_go_pending=False,
    ))
    admission = _admission_value(plan, run, authorization, uuid.uuid4().hex)
    owner.revalidate_inputs(admission)
    _prepared(plan)
    for pin in (authority_pin, attempt_pin, run, authorization):
        env.check_binding(pin)
    return h.save(ADMISSION, admission)


def verify_handoff(handoff_pin, admission_pin):
    """Replay a new activation handoff before any owned runtime is dispatched."""
    handoff = h.at(handoff_pin, HANDOFF)
    owner._obj(handoff, ("version", "scope", "authority", "attempt", "admission", "supervisor",
                         "began_ns", "until_ns"), "handoff")
    _need(_same(handoff["version"], 1) and handoff["scope"] == HANDOFF_SCOPE
          and _same(handoff["admission"], admission_pin), "handoff")
    owner._process(handoff["supervisor"])
    h.check_launch_window(handoff["began_ns"], handoff["until_ns"])
    _, plan = _approved_attempt(handoff["authority"], handoff["attempt"])
    _need(handoff["supervisor"]["executable"] == plan["python"]["executable"]["path"], "identity")
    proposal = _prepared(plan)
    admission = owner.validate_admission(h.at(admission_pin, ADMISSION))
    guest = admission["guest"]
    run, authorization = guest["proposal"], guest["authorization"]
    _need(_same(h.at(run, RUN, cap=h.STORAGE_CAP), proposal)
          and all(run[key] == plan["original_run"][key] for key in ("bytes", "sha256")), "proposal")
    env.check_authorization(h.at(authorization, RUN_AUTHORITY, cap=4096), "run", run["sha256"],
                            run_scope=RUN_SCOPE)
    _need(_same(admission, _admission_value(plan, run, authorization, admission["run_id"])), "admission")
    owner.revalidate_inputs(admission)
    for pin in (handoff_pin, admission_pin, handoff["authority"], handoff["attempt"], run, authorization,
                plan["evidence"]["ledger"]):
        env.check_binding(pin)
    h.check_launch_window(handoff["began_ns"], handoff["until_ns"])
    return handoff, admission
