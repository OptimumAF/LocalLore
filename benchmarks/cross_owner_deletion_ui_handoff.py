"""Check the exact SDK24 prepared-activation handoff without writing records.

Copyright 2026 LocalLore contributors. SPDX-License-Identifier: Apache-2.0
"""
import hashlib
import os
from pathlib import Path
import time

from benchmarks import archive_ui_build as files
from benchmarks import cross_owner_deletion_ui_binding as artifacts
from benchmarks import owned_cross_owner_deletion_ui as owned
from benchmarks import receipt_avd_environment as env
from benchmarks import receipt_avd_storage as storage

OUT = Path("D:/Dev/Experiments/LocalLore/2026-11-09-cross-owner-deletion-activation-v1")
ATTEMPT_ROOT = OUT / "attempt-v1"
PROPOSAL = OUT / "PROPOSED_OPERATION.md"
AUTHORITY = OUT / "human-authority-v1.json"
ATTEMPT = ATTEMPT_ROOT / "claim-v1.json"
ADMISSION = ATTEMPT_ROOT / "admission-v1.json"
HANDOFF = ATTEMPT_ROOT / "boot-handoff-v1.json"
RUN = ATTEMPT_ROOT / "run-proposal-v1.json"
RUN_AUTHORITY = ATTEMPT_ROOT / "run-authorization-v1.json"
OWNED_ROOT = ATTEMPT_ROOT / "owned-v1"
COMPLETION = ATTEMPT_ROOT / "activation-result-v1.json"
GUEST = Path(owned.GUEST_ROOT)
LEDGER = storage.DEFAULT_REGISTRY / "ledger-v1.json"
AUTHORITY_SCOPE = "sdk24-activate-prepared-cross-owner-deletion-v1"
HANDOFF_SCOPE = "sdk24-cross-owner-deletion-boot-handoff-v1"
HANDOFF_ENV = "LOCALLORE_CROSS_OWNER_DELETION_HANDOFF_SHA256"
NS = 1_000_000_000
ACTIVATION_SECONDS = 1800
OWNER_SECONDS = 1700
LAUNCH_TAIL_SECONDS = 1220
RECORD_CAP = 2 * 1024**2
STORAGE_CAP = 16 * 1024**2


def _bound(pin, path, cap):
    owned.binding(pin, max_bytes=cap)
    env.require(pin["path"] == str(path) and pin["bytes"] > 0, "binding")
    return files._bound(pin, cap=cap)


def read(path, cap=RECORD_CAP):
    raw = files._read(path, cap)
    pin = dict(path=str(path), bytes=len(raw), sha256=hashlib.sha256(raw).hexdigest())
    return pin, env.decode_json(raw)


def at(pin, path, cap=RECORD_CAP):
    return env.decode_json(_bound(pin, path, cap))


def ledger_entry(expected=None):
    pin, ledger = read(LEDGER, STORAGE_CAP)
    env.require(expected is None or owned._same(pin, expected), "ledger")
    env.require(type(ledger) is dict and owned._same(ledger.get("version"), 2), "ledger")
    storage._validate(ledger, storage.DEFAULT_REGISTRY)
    entry = storage._entry(ledger, GUEST)
    env.check_binding(pin)
    return pin, entry


def check_window(began_ns, until_ns, *, minimum_seconds=0):
    now = time.monotonic_ns()
    env.require(type(began_ns) is int and type(until_ns) is int
                and 0 < began_ns <= now < until_ns <= began_ns + ACTIVATION_SECONDS * NS
                and until_ns - now > minimum_seconds * NS, "deadline")


def read_approval(authority_pin, admission_pin):
    approved = at(authority_pin, AUTHORITY, 16_384)
    owned._obj(approved, ("version", "scope", "proposal", "admission", "ledger", "approval_reference",
                          "allow_sdk_prepare", "allow_one_boot", "allow_model", "allow_retirement"), "auth")
    reference = approved["approval_reference"]
    env.require(owned._same(approved["version"], 1) and approved["scope"] == AUTHORITY_SCOPE
                and owned._same(approved["admission"], admission_pin)
                and type(reference) is str and 0 < len(reference) <= 256 and reference == reference.strip()
                and all(32 <= ord(char) <= 126 for char in reference)
                and approved["allow_sdk_prepare"] is False and approved["allow_one_boot"] is True
                and approved["allow_model"] is False and approved["allow_retirement"] is False, "authority")
    lines = _bound(approved["proposal"], PROPOSAL, 65_536).decode("utf-8").splitlines()
    owned.binding(approved["ledger"], max_bytes=STORAGE_CAP)
    env.require(approved["ledger"]["path"] == str(LEDGER), "ledger")
    for label, role in (("Admission SHA-256", "admission"), ("Ledger SHA-256", "ledger")):
        env.require([line for line in lines if line.startswith(label)]
                    == [label + " " + approved[role]["sha256"]], "authority")
    return approved


def _approval(authority_pin, attempt_pin, admission_pin):
    approved = read_approval(authority_pin, admission_pin)
    env.require(owned._same(at(attempt_pin, ATTEMPT, 16_384),
                           dict(version=1, scope=AUTHORITY_SCOPE, authority=authority_pin, no_retry=True)), "attempt")
    return approved


def verify_boot(admission_pin, admission):
    """Require one exact approved and still-prepared SDK24 admission."""
    admission = owned.validate_admission(admission)
    env.require(admission["root"] == str(OWNED_ROOT) and owned._same(admission["seconds"], OWNER_SECONDS)
                and owned._same(at(admission_pin, ADMISSION), admission), "admission")
    pin, handoff = read(HANDOFF)
    owned._obj(handoff, ("version", "scope", "authority", "attempt", "admission",
                         "supervisor", "began_ns", "until_ns"), "binding")
    env.require(owned._same(handoff["version"], 1) and handoff["scope"] == HANDOFF_SCOPE
                and owned._same(handoff["admission"], admission_pin)
                and pin["sha256"] == os.environ.get(HANDOFF_ENV), "handoff")
    owned._process(handoff["supervisor"])
    env.require(handoff["supervisor"]["executable"] == admission["python"]["executable"]["path"], "identity")
    check_window(handoff["began_ns"], handoff["until_ns"], minimum_seconds=LAUNCH_TAIL_SECONDS)
    approved = _approval(handoff["authority"], handoff["attempt"], admission_pin)

    guest = admission["guest"]
    proposal = at(guest["proposal"], RUN, STORAGE_CAP)
    env.validate_proposal(proposal, "run")
    env.require(proposal["paths"]["root"] == guest["root"] == str(GUEST)
                and all(owned._same(proposal[key], guest[key])
                        for key in ("memory_mib", "cores", "max_seconds", "console_port", "serial"))
                and Path(proposal["sdk"]) / "emulator/emulator.exe" == Path(guest["emulator"]["path"])
                and proposal["adb_path"] == admission["server"]["adb"]["path"], "proposal")
    authorization = at(guest["authorization"], RUN_AUTHORITY, 4096)
    env.check_authorization(authorization, "run", guest["proposal"]["sha256"], run_scope=owned.RUN_SCOPE)
    env.verify_prepared(proposal, initial=True)
    owned.revalidate_inputs(admission)
    artifacts.verify_artifacts(admission["artifacts"])

    ledger_pin, entry = ledger_entry(approved["ledger"])
    env.require(entry["state"] == "prepared" and owned._same(entry["reserved_bytes"], storage.RESERVATION_BYTES)
                and entry["proposal_sha256"] == proposal["prepare_proposal"]["sha256"]
                and all(entry[key] is None for key in ("closure", "recovery", "retirement", "retirement_receipt")), "prepared")
    claim = env.safe_path(GUEST / owned.BOOT_CLAIM_FILE, exists=False)
    env.require(not os.path.lexists(claim), "already_used")
    inputs = (approved["proposal"], guest["proposal"], guest["authorization"], proposal["prepare_proposal"],
              proposal["prepared"], proposal["prepare_result"])
    for binding in (pin, handoff["authority"], handoff["attempt"], admission_pin, ledger_pin, *inputs):
        env.check_binding(binding)
    check_window(handoff["began_ns"], handoff["until_ns"], minimum_seconds=LAUNCH_TAIL_SECONDS)
    return pin, handoff, approved, inputs
