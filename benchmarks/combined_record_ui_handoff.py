"""Read-only approval and prepared-guest binding for the fixed SDK21 boot.

Copyright 2026 LocalLore contributors. SPDX-License-Identifier: Apache-2.0
"""
import hashlib
import os
from pathlib import Path
import time

from benchmarks import archive_ui_build as files
from benchmarks import combined_record_ui_binding as artifacts
from benchmarks import owned_combined_record_ui_contract as contract
from benchmarks import receipt_avd_environment as env
from benchmarks import receipt_avd_storage as storage

ROOT = Path(__file__).resolve().parents[1]
OUT = Path("D:/Dev/Experiments/LocalLore/2026-11-09-combined-record-ui-operation-v1")
PLAN = OUT / "plan-v1.json"
PROPOSAL = OUT / "PROPOSED_OPERATION.md"
AUTHORITY = OUT / "human-authority-v1.json"
PREPARE = OUT / "prepare-proposal-v1.json"
ATTEMPT_ROOT = OUT / "attempt-v1"
ATTEMPT = ATTEMPT_ROOT / "claim-v1.json"
PREPARE_AUTH = ATTEMPT_ROOT / "prepare-authorization-v1.json"
HANDOFF = ATTEMPT_ROOT / "boot-handoff-v1.json"
ADMISSION = ATTEMPT_ROOT / "admission-v1.json"
RUN = ATTEMPT_ROOT / "run-proposal-v1.json"
RUN_AUTHORITY = ATTEMPT_ROOT / "run-authorization-v1.json"
OWNED_ROOT = ATTEMPT_ROOT / "owned-v1"
LEDGER = storage.DEFAULT_REGISTRY / "ledger-v1.json"
GUEST = Path(contract.GUEST_ROOT)
OPERATION_SCOPE = "sdk21-prepare-and-one-combined-record-run-v1"
PLAN_SCOPE = "sdk21-combined-record-plan-v1"
HANDOFF_SCOPE = "combined-record-boot-handoff-v1"
HANDOFF_ENV = "LOCALLORE_COMBINED_RECORD_HANDOFF_SHA256"
NS = 1_000_000_000
SECONDS = 2400
ACTIVATION_SECONDS = 1800
TAIL_SECONDS = 20
OWNER_SECONDS = 1700
CONTROLLER_SECONDS = 1200
RECORD_CAP = 2 * 1024**2
STORAGE_CAP = 16 * 1024**2
_need = env.require
_same = contract._same


def _pin_at(pin, path, cap):
    contract.binding(pin, max_bytes=cap)
    _need(pin["path"] == str(path) and pin["bytes"] > 0, "binding")


def read(path, cap=RECORD_CAP):
    raw = files._read(path, cap)
    pin = dict(path=str(path), bytes=len(raw), sha256=hashlib.sha256(raw).hexdigest())
    return pin, env.decode_json(raw)


def at(pin, path, cap=RECORD_CAP):
    _pin_at(pin, path, cap)
    return env.decode_json(files._bound(pin, cap=cap))


def ledger_entry(root):
    _need(Path(root) == GUEST, "ledger")
    pin, ledger = read(LEDGER, STORAGE_CAP)
    _need(type(ledger) is dict and _same(ledger.get("version"), 2), "ledger")
    storage._validate(ledger, storage.DEFAULT_REGISTRY)
    entry = storage._entry(ledger, GUEST)
    env.check_binding(pin)
    return pin, entry


def read_authority(authority_pin):
    authority = at(authority_pin, AUTHORITY, cap=16384)
    contract._obj(authority, ("version", "scope", "proposal", "plan", "ledger", "approval_reference",
                              "allow_sdk_prepare", "allow_one_boot", "allow_model", "allow_retirement",
                              "max_operation_seconds"), "auth")
    ref = authority["approval_reference"]
    _need(_same(authority["version"], 1) and authority["scope"] == OPERATION_SCOPE
          and type(ref) is str and 0 < len(ref) <= 256 and ref == ref.strip()
          and all(32 <= ord(char) <= 126 for char in ref)
          and authority["allow_sdk_prepare"] is True and authority["allow_one_boot"] is True
          and authority["allow_model"] is False and authority["allow_retirement"] is False
          and _same(authority["max_operation_seconds"], SECONDS), "authority")
    _pin_at(authority["proposal"], PROPOSAL, 65536)
    _pin_at(authority["ledger"], LEDGER, STORAGE_CAP)
    lines = files._bound(authority["proposal"], cap=65536).decode("utf-8").splitlines()
    for label, role in (("Plan SHA-256", "plan"), ("Ledger SHA-256", "ledger")):
        _need([line for line in lines if line.startswith(label)] ==
              [label + " " + authority[role]["sha256"]], "authority")
    plan = at(authority["plan"], PLAN, cap=131072)
    env.check_binding(authority_pin)
    return authority, plan


def approved_plan(authority_pin, attempt_pin):
    authority, plan = read_authority(authority_pin)
    expected = dict(version=1, scope=OPERATION_SCOPE, authority=authority_pin, no_retry=True)
    _need(_same(at(attempt_pin, ATTEMPT, cap=16384), expected), "attempt")
    return authority, plan


def prepare_plan(plan):
    contract._obj(plan, ("version", "scope", "source_root", "sources", "python", "artifacts", "prepare",
                         "installed", "execution_authorized", "model_material"), "binding")
    _need(_same(plan["version"], 1) and plan["scope"] == PLAN_SCOPE and plan["source_root"] == str(ROOT)
          and plan["execution_authorized"] is False and plan["model_material"] is False, "plan")
    installed = plan["installed"]
    contract._obj(installed, ("adb", "tools", "emulator", "qemu", "refuser", "refuser_source",
                              "auth_key_path", "capabilities", "source_review", "compatibility"), "binding")
    prepare = at(plan["prepare"], PREPARE, cap=STORAGE_CAP)
    env.validate_proposal(prepare, "prepare")
    _need(prepare["paths"]["root"] == str(GUEST) and prepare["adb_path"] == installed["adb"]["path"]
          and _same(prepare["memory_mib"], 8192) and _same(prepare["cores"], 4), "profile")
    return prepare


def check_window(began_ns, until_ns):
    _need(type(began_ns) is int and type(until_ns) is int
          and 0 < began_ns < until_ns <= began_ns + SECONDS * NS, "deadline")
    now = time.monotonic_ns()
    _need(began_ns <= now < until_ns and until_ns - now <= ACTIVATION_SECONDS * NS, "deadline")
    return now


def check_launch_window(began_ns, until_ns):
    now = check_window(began_ns, until_ns)
    _need(now + (CONTROLLER_SECONDS + TAIL_SECONDS) * NS < until_ns, "deadline")
    return now


def _verify_preparation(plan, admission, proposal):
    prepare_pin = plan["prepare"]
    prepared = at(proposal["prepare_result"], GUEST / "prepare-result-v1.json")
    _need(_same(prepared, dict(version=1, proposal_sha256=prepare_pin["sha256"], status="completed",
                               closure_verified=True, child_cleanup_complete=True, prepared_created=True)), "prepared")
    authorization_pin, authorization = read(PREPARE_AUTH, 4096)
    env.check_authorization(authorization, "prepare", prepare_pin["sha256"], prepare_scope=OPERATION_SCOPE)
    started_pin, started = read(GUEST / "prepare-start-v1.json", 8192)
    worker_pin, claim = read(GUEST / "prepare-worker-claimed-v1.json", 8192)
    contract._obj(started, ("proposal_sha256", "facts", "owner", "prepare_scope"), "binding")
    contract._obj(claim, ("proposal_sha256", "worker", "prepare_scope"), "binding")
    owner, worker = started["owner"], claim["worker"]
    contract._process(owner)
    contract._process(worker)
    _need(type(started["facts"]) is dict and owner["pid"] != worker["pid"]
          and owner["executable"] == worker["executable"] == admission["python"]["executable"]["path"]
          and owner["creation_filetime"] <= worker["creation_filetime"]
          and all(row["prepare_scope"] == OPERATION_SCOPE and row["proposal_sha256"] == prepare_pin["sha256"]
                  for row in (started, claim)), "prepared")
    return authorization_pin, started_pin, worker_pin


def verify_boot_handoff(admission_pin, admission):
    """Join a live-window handoff to one spent approval and a prepared v2 entry."""
    admission = contract.validate_admission(admission)
    _need(admission["root"] == str(OWNED_ROOT) and _same(admission["seconds"], OWNER_SECONDS)
          and _same(at(admission_pin, ADMISSION), admission), "admission")
    handoff_pin, handoff = read(HANDOFF)
    contract._obj(handoff, ("version", "scope", "authority", "attempt", "admission",
                            "supervisor", "began_ns", "until_ns"), "binding")
    _need(_same(handoff["version"], 1) and handoff["scope"] == HANDOFF_SCOPE
          and _same(handoff["admission"], admission_pin), "handoff")
    contract._process(handoff["supervisor"])
    _need(handoff["supervisor"]["executable"] == admission["python"]["executable"]["path"], "identity")
    check_launch_window(handoff["began_ns"], handoff["until_ns"])
    authority, plan = approved_plan(handoff["authority"], handoff["attempt"])
    prepare = prepare_plan(plan)
    _need(all(_same(plan[key], admission[key]) for key in ("sources", "python", "artifacts")), "plan")
    server, guest = admission["server"], admission["guest"]
    installed = {key: server[key] for key in ("adb", "tools", "capabilities", "source_review")}
    installed.update({key: guest[key] for key in ("emulator", "qemu", "refuser", "refuser_source")})
    installed.update(auth_key_path=server["auth_key"], compatibility=admission["compatibility"])
    _need(_same(plan["installed"], installed), "installed")

    proposal = at(guest["proposal"], RUN, cap=STORAGE_CAP)
    env.validate_proposal(proposal, "run")
    expected = dict(prepare, phase="run", prepare_proposal=plan["prepare"],
                    prepared=proposal["prepared"], prepare_result=proposal["prepare_result"],
                    max_seconds=ACTIVATION_SECONDS)
    _need(_same(proposal, expected) and guest["root"] == str(GUEST)
          and _same(guest["max_seconds"], ACTIVATION_SECONDS), "proposal")
    authorization = at(guest["authorization"], RUN_AUTHORITY, cap=4096)
    env.check_authorization(authorization, "run", guest["proposal"]["sha256"], run_scope=contract.RUN_SCOPE)
    preparation_pins = _verify_preparation(plan, admission, proposal)
    artifacts.verify_artifacts(admission["artifacts"])
    env.verify_prepared(proposal, initial=True)
    ledger_pin, entry = ledger_entry(GUEST)
    _need(entry["state"] == "prepared" and _same(entry["reserved_bytes"], storage.RESERVATION_BYTES)
          and entry["proposal_sha256"] == plan["prepare"]["sha256"]
          and all(entry[key] is None for key in ("closure", "recovery", "retirement", "retirement_receipt")),
          "prepared")
    claim = env.safe_path(GUEST / contract.BOOT_CLAIM_FILE, exists=False)
    _need(not os.path.lexists(claim), "already_used")
    for pin in (handoff_pin, admission_pin, handoff["authority"], handoff["attempt"], authority["proposal"],
                authority["plan"], plan["prepare"], guest["proposal"], guest["authorization"],
                proposal["prepare_result"], ledger_pin, *preparation_pins):
        env.check_binding(pin)
    check_launch_window(handoff["began_ns"], handoff["until_ns"])
    return handoff_pin, handoff
