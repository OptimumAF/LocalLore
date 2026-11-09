"""Prepare the fixed SDK25 guest through the shared scoped storage owner.

Copyright 2026 LocalLore contributors. SPDX-License-Identifier: Apache-2.0
"""
import hashlib
import os
from pathlib import Path
import re
import sys

from benchmarks import archive_roundtrip_admission as admission
from benchmarks import archive_roundtrip_supervisor as supervisor

contract = admission.contract
build = admission.build
env = admission.env
storage = admission.storage
lifecycle = admission.lifecycle
output_control = admission.output_control

SCOPE = "sdk25-archive-roundtrip-prepare-once-v1"
GUEST = Path(contract.GUEST_ROOT)
AUTHORITY = admission.CONTROL / "prepare-authority-v1.json"
AUTHORIZATION = admission.CONTROL / "prepare-authorization-v1.json"
ATTEMPT = admission.CONTROL / "prepare-attempt-v1.json"
RESULT = admission.CONTROL / "prepare-receipt-v1.json"
LEDGER = storage.DEFAULT_REGISTRY / "ledger-v1.json"

_need = admission._need
_same = contract._same
_at = lifecycle._at
_read = lifecycle._read
_save = supervisor._save


def _authority(pin):
    value = _at(pin, AUTHORITY, admission.AUTHORITY_CAP)
    contract._obj(value, ("version", "scope", "prepare", "authorization", "ledger", "artifacts",
                          "source_sha256", "approval_reference", "allow_prepare", "allow_boot"), "binding")
    reference = value["approval_reference"]
    _need(_same(value["version"], 1) and value["scope"] == SCOPE
          and value["allow_prepare"] is True and value["allow_boot"] is False
          and type(reference) is str and 0 < len(reference) <= 256 and reference == reference.strip()
          and all(32 <= ord(char) <= 126 for char in reference), "authority")
    expected_sources = hashlib.sha256(env.encoded(contract.source_bindings())).hexdigest()
    _need(value["source_sha256"] == expected_sources, "source")
    return value


def _preflight(authority_pin):
    authority = _authority(authority_pin)
    prepare = _at(authority["prepare"], admission.PREPARE_PROPOSAL)
    env.validate_proposal(prepare, "prepare")
    _need(prepare["paths"]["root"] == str(GUEST) and
          _same((prepare["memory_mib"], prepare["cores"]), (8192, 4)), "profile")
    authorization = _at(authority["authorization"], AUTHORIZATION, 4096)
    env.check_authorization(authorization, "prepare", authority["prepare"]["sha256"], prepare_scope=SCOPE)

    ledger = _at(authority["ledger"], LEDGER, lifecycle.LEDGER_CAP)
    _need(_same(ledger["version"], 2), "ledger_version")
    preview = storage.preview_prepare(GUEST)
    _need(_same(preview["ledger"], authority["ledger"]) and preview["would_fit"] is True
          and preview["admission_granted"] is False, "capacity")

    build.verify_current(dict(artifacts=authority["artifacts"]))
    checked = env.authorize(str(admission.PREPARE_PROPOSAL), str(AUTHORIZATION), "prepare",
                            prepare_scope=SCOPE, expected_proposal_sha256=authority["prepare"]["sha256"])
    _need(_same(checked, prepare), "proposal")
    env.resource_facts(prepare)
    for pin in (authority_pin, authority["prepare"], authority["authorization"], authority["ledger"]):
        env.check_binding(pin)
    return authority


def _attempt(authority_pin, authority):
    return dict(version=1, scope=SCOPE, authority=authority_pin, prepare=authority["prepare"],
                ledger=authority["ledger"], no_retry=True)


def _child_evidence(prepare_pin, expected_owner=None):
    start_pin, start = _read(GUEST / "prepare-start-v1.json", 4096)
    worker_pin, worker = _read(GUEST / "prepare-worker-claimed-v1.json", 4096)
    client_pin, client = _read(GUEST / "prepare-client-v1.json", 4096)
    contract._obj(start, ("proposal_sha256", "facts", "owner", "prepare_scope"), "prepared")
    contract._obj(worker, ("proposal_sha256", "worker", "prepare_scope"), "prepared")
    contract._obj(client, ("status", "returncode", "cleanup_complete", "elapsed_ms",
                           "stdout_sha256", "stderr_bytes"), "prepared")
    parent, child = start["owner"], worker["worker"]
    contract._process(parent)
    contract._process(child)
    _need(type(start["facts"]) is dict and (expected_owner is None or _same(parent, expected_owner))
          and parent["pid"] != child["pid"] and parent["executable"] == child["executable"]
          and parent["creation_filetime"] <= child["creation_filetime"]
          and all(row["proposal_sha256"] == prepare_pin["sha256"] and row["prepare_scope"] == SCOPE
                  for row in (start, worker)), "prepared")
    path = GUEST / "prepare-stdout-v1.bin"
    raw = lifecycle.bridge.files._read(path, env.MAX_OUTPUT)
    stdout = lifecycle.bridge._pin_bytes(path, raw)
    _need(client["status"] == "completed" and _same(client["returncode"], 0)
          and client["cleanup_complete"] is True and client["stdout_sha256"] == stdout["sha256"]
          and type(client["elapsed_ms"]) is int and client["elapsed_ms"] >= 0
          and type(client["stderr_bytes"]) is int and 0 <= client["stderr_bytes"] <= env.MAX_OUTPUT - len(raw),
          "prepared")
    for pin in (start_pin, worker_pin, client_pin, stdout):
        env.check_binding(pin)
    return dict(start=start_pin, worker=worker_pin, client=client_pin, stdout=stdout)


def _verify_result(authority, returned, expected_owner):
    prepared_pin, prepared = _read(GUEST / "prepared-v1.json")
    result_pin, result = _read(GUEST / "prepare-result-v1.json")
    prepare_pin = authority["prepare"]
    expected = dict(version=1, proposal_sha256=prepare_pin["sha256"], status="completed",
                    closure_verified=True, child_cleanup_complete=True, prepared_created=True)
    _need(_same(result, expected) and _same(prepared, returned)
          and prepared["proposal_sha256"] == prepare_pin["sha256"]
          and prepared["userdata_absent"] is True and prepared["guest_boot_verified"] is False, "prepared")
    child = _child_evidence(prepare_pin, expected_owner)
    ledger_pin, _ = _read(LEDGER, lifecycle.LEDGER_CAP)
    admission._prepared_entry(ledger_pin, {"guest": {"root": str(GUEST)}}, {"prepare_proposal": prepare_pin})
    for pin in (prepared_pin, result_pin, ledger_pin):
        env.check_binding(pin)
    return dict(prepared=prepared_pin, prepare_result=result_pin, prepared_ledger=ledger_pin, child=child)


def verify_receipt(receipt_pin, proposal, artifacts):
    """Replay scoped preparation before run admission, with a separate fresh ledger pin."""
    value = _at(receipt_pin, RESULT)
    contract._obj(value, ("version", "scope", "authority", "attempt", "prepared",
                          "prepare_result", "prepared_ledger", "child"), "prepared")
    _need(_same(value["version"], 1) and value["scope"] == SCOPE
          and _same(value["prepared"], proposal["prepared"])
          and _same(value["prepare_result"], proposal["prepare_result"]), "prepared")
    prior = _authority(value["authority"])
    prepare_pin = proposal["prepare_proposal"]
    _need(_same(prior["prepare"], prepare_pin) and _same(prior["artifacts"], artifacts), "prepared")
    attempt = _at(value["attempt"], ATTEMPT, admission.AUTHORITY_CAP)
    _need(_same(attempt, _attempt(value["authority"], prior)), "prepared")
    for historical in (prior["ledger"], value["prepared_ledger"]):
        contract.binding(historical, max_bytes=lifecycle.LEDGER_CAP)
        _need(historical["path"] == str(LEDGER), "prepared")
    authorization = _at(prior["authorization"], AUTHORIZATION, 4096)
    env.check_authorization(authorization, "prepare", prepare_pin["sha256"], prepare_scope=SCOPE)
    _need(_same(value["child"], _child_evidence(prepare_pin)), "prepared")
    for pin in (receipt_pin, value["authority"], value["attempt"], prior["authorization"]):
        env.check_binding(pin)


def execute(authority_pin):
    """Spend one external prepare-only approval; never authorize or start a run."""
    _need(os.name == "nt", "platform")
    output_control._prepare_environment()
    attempt_path = output_control.validate_output(str(ATTEMPT))
    result_path = output_control.validate_output(str(RESULT))
    authority = _preflight(authority_pin)
    owner = supervisor._identity(os.getpid())
    attempt = _save(attempt_path, _attempt(authority_pin, authority))
    _need(_same(_authority(authority_pin), authority), "authority")
    for pin in (attempt, authority["prepare"], authority["authorization"]):
        env.check_binding(pin)
    prepared = env.prepare(
        str(admission.PREPARE_PROPOSAL), str(AUTHORIZATION), expected_ledger=authority["ledger"],
        expected_proposal_sha256=authority["prepare"]["sha256"], prepare_scope=SCOPE,
    )
    proof = _verify_result(authority, prepared, owner)
    _need(_same(_authority(authority_pin), authority), "authority")
    for pin in (authority_pin, attempt, authority["prepare"], authority["authorization"]):
        env.check_binding(pin)
    return _save(result_path, dict(version=1, scope=SCOPE, authority=authority_pin, attempt=attempt, **proof))


def main(argv=None):
    args = sys.argv[1:] if argv is None else argv
    try:
        _need(os.name == "nt" and type(args) is list and len(args) == 2 and args[0] == "--authority-sha256"
              and type(args[1]) is str and re.fullmatch("[0-9a-f]{64}", args[1]) is not None, "authority")
        pin, _ = _read(AUTHORITY, admission.AUTHORITY_CAP)
        _need(pin["sha256"] == args[1], "authority")
        execute(pin)
        return 0
    except (OSError, ValueError, RuntimeError, KeyError, TypeError):
        print("SDK25 preparation refused", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
