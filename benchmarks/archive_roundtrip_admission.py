"""Read-only SDK25 prepared-run admission and create-only attempt claim.

Copyright 2026 LocalLore contributors. SPDX-License-Identifier: Apache-2.0
"""
import os
from pathlib import Path, PureWindowsPath

from benchmarks import archive_roundtrip_build as build
from benchmarks import archive_roundtrip_lifecycle as lifecycle
from benchmarks import owned_archive_roundtrip_contract as contract
from benchmarks import receipt_avd_environment as env
from benchmarks import receipt_avd_storage as storage
from benchmarks import windows_tcp_control as output_control

SCOPE = "sdk25-prepared-archive-roundtrip-once-v1"
CONTROL = Path(str(contract.GUEST_ROOT.parent)) / "operation-v1"
ADMISSION = CONTROL / "admission-v1.json"
AUTHORITY = CONTROL / "run-authority-v1.json"
ATTEMPT = CONTROL / "attempt-v1.json"
RUN_PROPOSAL = CONTROL / "run-proposal-v1.json"
RUN_AUTHORIZATION = CONTROL / "run-authorization-v1.json"
PREPARE_PROPOSAL = CONTROL / "prepare-proposal-v1.json"
OWNED_ROOT = CONTROL / "owned-v1"
OWNER_SECONDS = 1700
GUEST_SECONDS = 1800
AUTHORITY_CAP = 16 * 1024


class AdmissionRefused(ValueError):
    """A fixed refusal without raw evidence or private paths."""


def _need(condition, reason):
    if not condition:
        raise AdmissionRefused(reason)


def _same(left, right):
    return contract._same(left, right)


def _at(pin, path, cap=lifecycle.RECORD_CAP):
    return lifecycle._at(pin, path, cap)


def _authority(pin):
    value = _at(pin, AUTHORITY, AUTHORITY_CAP)
    contract._obj(value, ("version", "scope", "admission", "ledger", "prepare_receipt", "approval_reference",
                          "allow_one_boot", "allow_prepare", "allow_model", "allow_retirement",
                          "owner_seconds", "guest_seconds"), "auth")
    reference = value["approval_reference"]
    _need(_same(value["version"], 1) and value["scope"] == SCOPE and
          value["allow_one_boot"] is True and value["allow_prepare"] is False and
          value["allow_model"] is False and value["allow_retirement"] is False and
          _same(value["owner_seconds"], OWNER_SECONDS) and _same(value["guest_seconds"], GUEST_SECONDS) and
          type(reference) is str and 0 < len(reference) <= 256 and reference == reference.strip() and
          all(32 <= ord(char) <= 126 for char in reference), "authority")
    return value


def _proposal(admission):
    guest = admission["guest"]
    proposal_pin, authorization_pin = guest["proposal"], guest["authorization"]
    proposal = _at(proposal_pin, RUN_PROPOSAL)
    authorization = _at(authorization_pin, RUN_AUTHORIZATION, 4096)
    env.validate_proposal(proposal, "run")
    env.check_authorization(authorization, "run", proposal_pin["sha256"], run_scope=contract.RUN_SCOPE)
    prepare_pin = proposal["prepare_proposal"]
    contract.binding(prepare_pin)
    _need(PureWindowsPath(prepare_pin["path"]) == PureWindowsPath(str(PREPARE_PROPOSAL)) and
          proposal["paths"]["root"] == guest["root"] and
          _same(proposal["memory_mib"], guest["memory_mib"]) and
          _same(proposal["cores"], guest["cores"]) and
          _same(proposal["max_seconds"], GUEST_SECONDS) and
          proposal["adb_path"] == admission["server"]["adb"]["path"] and
          PureWindowsPath(proposal["sdk"]) / "emulator" / "emulator.exe" == PureWindowsPath(guest["emulator"]["path"]),
          "proposal")
    return proposal


def _check_ledger_unlocked():
    _need(not os.path.lexists(storage.DEFAULT_REGISTRY / "admission.lock"), "ledger_lock")


def _prepared_entry(ledger_pin, admission, proposal):
    _check_ledger_unlocked()
    registry = storage.DEFAULT_REGISTRY
    ledger = _at(ledger_pin, registry / "ledger-v1.json", lifecycle.LEDGER_CAP)
    storage._validate(ledger, registry)
    # The locked, expected-ledger prepared-to-retained transition requires v2.
    _need(_same(ledger["version"], 2), "ledger_version")
    entry = storage._entry(ledger, Path(admission["guest"]["root"]))
    _need(entry["state"] == "prepared" and _same(entry["reserved_bytes"], storage.RESERVATION_BYTES) and
          entry["proposal_sha256"] == proposal["prepare_proposal"]["sha256"] and
          all(entry[key] is None for key in ("closure", "recovery", "retirement", "retirement_receipt")),
          "prepared")
    _check_ledger_unlocked()


def preboot(authority_pin, *, owner_created=False):
    """Revalidate the one approved prepared-run context without spending it."""
    from benchmarks import archive_roundtrip_prepare as preparation

    authority = _authority(authority_pin)
    admission_pin = authority["admission"]
    admission = contract.validate_admission(_at(admission_pin, ADMISSION))
    guest = admission["guest"]
    _need(admission["root"] == str(OWNED_ROOT) and _same(admission["seconds"], OWNER_SECONDS) and
          _same(guest["max_seconds"], GUEST_SECONDS), "admission")
    if owner_created:
        env.safe_path(OWNED_ROOT, directory=True)
    else:
        _need(not os.path.lexists(OWNED_ROOT), "already_used")
    _need(not os.path.lexists(Path(guest["root"]) / contract.BOOT_CLAIM_FILE), "already_used")
    proposal = _proposal(admission)
    _prepared_entry(authority["ledger"], admission, proposal)
    preparation.verify_receipt(authority["prepare_receipt"], proposal, admission["artifacts"])
    build.verify_current(admission)
    contract.revalidate_inputs(admission)
    current = env.authorize(str(RUN_PROPOSAL), str(RUN_AUTHORIZATION), "run",
                            run_scope=contract.RUN_SCOPE,
                            expected_proposal_sha256=guest["proposal"]["sha256"])
    _need(_same(current, proposal), "proposal")
    env.verify_prepared(proposal, initial=True)
    for pin in (authority_pin, admission_pin, authority["ledger"], authority["prepare_receipt"], guest["proposal"],
                guest["authorization"], proposal["prepare_proposal"], proposal["prepared"],
                proposal["prepare_result"]):
        env.check_binding(pin)
    _check_ledger_unlocked()
    return dict(admission=admission, admission_pin=admission_pin, ledger=authority["ledger"],
                prepare_sha256=proposal["prepare_proposal"]["sha256"])


def _claim(authority_pin, context):
    return dict(version=1, scope=SCOPE, authority=authority_pin,
                admission=context["admission_pin"], ledger=context["ledger"],
                prepare_sha256=context["prepare_sha256"], no_retry=True)


def spend(authority_pin):
    """Create the one attempt record after fresh checks. No process is launched."""
    path = output_control.validate_output(str(ATTEMPT))
    context = preboot(authority_pin)
    value = _claim(authority_pin, context)
    env.create_json(path, value)
    pin, retained = lifecycle._read(path, AUTHORITY_CAP)
    _need(_same(retained, value), "attempt")
    env.check_binding(authority_pin)
    env.check_binding(context["ledger"])
    return pin


def verify_spent(authority_pin, attempt_pin, *, owner_created=False):
    """Bind the spent attempt to the unchanged preboot context before launch."""
    retained = _at(attempt_pin, ATTEMPT, AUTHORITY_CAP)
    context = preboot(authority_pin, owner_created=owner_created)
    _need(_same(retained, _claim(authority_pin, context)), "attempt")
    env.check_binding(attempt_pin)
    return context
