"""Inspect or consume one exact preparation-only approval for SDK26.

Copyright 2026 LocalLore contributors. SPDX-License-Identifier: Apache-2.0
"""
import json
import os
from pathlib import Path
import re
import sys

ROOT = Path(__file__).resolve().parents[1]
if __package__ in (None, ""):
    sys.path.insert(0, str(ROOT))

from benchmarks import adb_held_socket_probe as python_probe
from benchmarks import archive_provider_platform_binding as artifacts
from benchmarks import archive_ui_build as files
from benchmarks import owned_archive_provider_platform as owned
from benchmarks import receipt_avd_environment as env
from benchmarks import receipt_avd_storage as storage

GUEST = Path(owned.GUEST_ROOT)
# The v1 slots preserve the earlier capacity refusal and pre-supervisor pins.
PLAN = GUEST.parent / "preparation-plan-sdk26-v2.json"
PREPARE = GUEST.parent / "prepare-proposal-sdk26-v2.json"
PROPOSED_PREPARATION = GUEST.parent / "PROPOSED_PREPARATION.md"
AUTHORITY = GUEST.parent / "human-authority-v1.json"
CLAIM = GUEST.parent / "prepare-claim-v1.json"
PREPARE_AUTH = GUEST.parent / "prepare-authorization-v1.json"
RESULT = GUEST.parent / "preparation-result-v1.json"
LEDGER = storage.DEFAULT_REGISTRY / "ledger-v1.json"
PREPARE_SCOPE = "sdk26-prepare-archive-provider-platform-v1"
PLAN_SCOPE = "sdk26-archive-provider-platform-preparation-plan-v1"
RECORD_CAP = 2 * 1024**2


def _bound(pin, path, cap=RECORD_CAP):
    owned.binding(pin, max_bytes=cap)
    env.require(pin["path"] == str(path), "binding")
    return files._bound(pin, cap=cap)


def _save(path, value):
    env.create_json(path, value)
    pin = env.binding(path)
    env.require(owned._same(env.decode_json(_bound(pin, path)), value), "publication")
    return pin


def _fresh(*, pending):
    env.safe_path(GUEST.parent, directory=True)
    paths = (GUEST, CLAIM, PREPARE_AUTH, RESULT)
    if pending:
        paths += (AUTHORITY,)
    for path in paths:
        env.safe_path(path, exists=False)
        env.require(not os.path.lexists(path), "already_used")


def capacity_preview():
    """Read shared capacity without granting admission or touching the guest."""
    return storage.preview_prepare(GUEST)


def build_plan(sdk, java_home):
    """Publish only preparation inputs; the experiment parent already exists."""
    _fresh(pending=True)
    for path in (PREPARE, PLAN):
        env.safe_path(path, exists=False)
        env.require(not os.path.lexists(path), "already_used")
    pins = artifacts.artifact_bindings()
    artifacts.verify_artifacts(pins)
    sources = owned.source_bindings()
    python = python_probe._python_bindings()
    env.plan_prepare(GUEST, sdk, java_home, PREPARE, real_candidate=True, four_core_candidate=True)
    return _save(PLAN, dict(version=1, scope=PLAN_SCOPE, sources=sources, python=python,
                            artifacts=pins, prepare=env.binding(PREPARE)))


def load_plan(plan_pin):
    plan = env.decode_json(_bound(plan_pin, PLAN))
    owned._obj(plan, ("version", "scope", "sources", "python", "artifacts", "prepare"), "plan")
    env.require(owned._same(plan["version"], 1) and plan["scope"] == PLAN_SCOPE, "plan")
    env.require(owned._same(plan["sources"], owned.source_bindings())
                and owned._same(plan["python"], python_probe._python_bindings()), "source")
    artifacts.verify_artifacts(plan["artifacts"])
    proposal = env.decode_json(_bound(plan["prepare"], PREPARE))
    env.validate_proposal(proposal, "prepare")
    env.require(proposal["paths"]["root"] == str(GUEST)
                and owned._same(proposal["memory_mib"], 8192)
                and owned._same(proposal["cores"], 4), "profile")
    return plan, proposal


def _inspect(plan_pin, ledger_pin, *, pending):
    _fresh(pending=pending)
    plan, proposal = load_plan(plan_pin)
    preview = capacity_preview()
    env.require(owned._same(preview["ledger"], ledger_pin) and preview["root"] == str(GUEST)
                and preview["admission_granted"] is False, "ledger")
    resources = None
    if preview["would_fit"] is True:
        env.verify_installation(proposal)
        env.check_external_state(proposal)
        resources = env.resource_facts(proposal)
    for pin in (plan_pin, plan["prepare"], ledger_pin):
        env.check_binding(pin)
    _fresh(pending=pending)
    return dict(version=1, scope=PREPARE_SCOPE, plan=plan_pin, ledger=ledger_pin,
                storage=preview, resources=resources, execution_authorized=False)


def inspect(plan_pin, ledger_pin):
    return _inspect(plan_pin, ledger_pin, pending=True)


def _read_authority(pin):
    authority = env.decode_json(_bound(pin, AUTHORITY, 16_384))
    owned._obj(authority, ("version", "scope", "proposal", "plan", "ledger", "approval_reference",
                           "allow_sdk_prepare", "allow_one_boot", "allow_model", "allow_retirement"), "authority")
    reference = authority["approval_reference"]
    env.require(owned._same(authority["version"], 1) and authority["scope"] == PREPARE_SCOPE
                and type(reference) is str and 0 < len(reference) <= 256 and reference == reference.strip()
                and all(32 <= ord(char) <= 126 for char in reference)
                and authority["allow_sdk_prepare"] is True and authority["allow_one_boot"] is False
                and authority["allow_model"] is False and authority["allow_retirement"] is False, "authority")
    owned.binding(authority["plan"], max_bytes=RECORD_CAP)
    owned.binding(authority["ledger"], max_bytes=16 * 1024**2)
    env.require(authority["plan"]["path"] == str(PLAN) and authority["ledger"]["path"] == str(LEDGER), "authority")
    lines = _bound(authority["proposal"], PROPOSED_PREPARATION, 65_536).decode("utf-8").splitlines()
    for label, role in (("Plan SHA-256", "plan"), ("Ledger SHA-256", "ledger")):
        env.require([line for line in lines if line.startswith(label)]
                    == [label + " " + authority[role]["sha256"]], "authority")
    return authority


def _claim(authority_pin):
    return dict(version=1, scope=PREPARE_SCOPE, authority=authority_pin, no_retry=True)


def _prepared_ledger(prepare_pin):
    ledger = env.binding(LEDGER)
    value = storage.read_json(LEDGER, expected=ledger)
    storage._validate(value, storage.DEFAULT_REGISTRY)
    entries = [row for row in value["entries"] if row["root"] == str(GUEST)]
    env.require(len(entries) == 1, "prepared")
    entry = entries[0]
    env.require(entry["state"] == "prepared" and entry["proposal_sha256"] == prepare_pin["sha256"]
                and owned._same(entry["reserved_bytes"], storage.RESERVATION_BYTES)
                and all(entry[key] is None for key in ("closure", "recovery", "retirement", "retirement_receipt")),
                "prepared")
    env.check_binding(ledger)
    return ledger


def _prepared_records(plan, proposal):
    env.require(not os.path.lexists(GUEST / owned.BOOT_CLAIM_FILE), "already_used")
    prepared = env.binding(GUEST / "prepared-v1.json")
    result = env.binding(GUEST / "prepare-result-v1.json")
    run = dict(proposal, phase="run", prepare_proposal=plan["prepare"], prepared=prepared,
               prepare_result=result, max_seconds=env.REAL_MAX_SECONDS)
    env.validate_proposal(run, "run")
    env.verify_prepared(run, initial=True)

    evidence = {name: env.binding(GUEST / leaf) for name, leaf in (
        ("start", "prepare-start-v1.json"), ("worker", "prepare-worker-claimed-v1.json"),
        ("client", "prepare-client-v1.json"), ("stdout", "prepare-stdout-v1.bin"),
    )}
    start = env.decode_json(files._bound(evidence["start"], cap=8192))
    worker = env.decode_json(files._bound(evidence["worker"], cap=8192))
    client = env.decode_json(files._bound(evidence["client"], cap=8192))
    files._bound(evidence["stdout"], cap=env.MAX_OUTPUT)
    owned._obj(start, ("proposal_sha256", "facts", "owner", "prepare_scope"), "prepared")
    owned._obj(worker, ("proposal_sha256", "worker", "prepare_scope"), "prepared")
    owned._obj(client, ("status", "returncode", "cleanup_complete", "elapsed_ms",
                        "stdout_sha256", "stderr_bytes"), "prepared")
    owner, child = start["owner"], worker["worker"]
    owned._process(owner)
    owned._process(child)
    env.require(owner["pid"] != child["pid"] and owner["creation_filetime"] <= child["creation_filetime"]
                and owner["executable"] == child["executable"] == plan["python"]["executable"]["path"]
                and all(row["proposal_sha256"] == plan["prepare"]["sha256"] and row["prepare_scope"] == PREPARE_SCOPE
                        for row in (start, worker))
                and type(start["facts"]) is dict, "prepared")
    env.require(client["status"] == "completed" and owned._same(client["returncode"], 0)
                and client["cleanup_complete"] is True and client["stdout_sha256"] == evidence["stdout"]["sha256"],
                "prepared")
    # The shared worker enforces its execution deadline before joining resources.
    # Its receipt measures elapsed time through cleanup.
    owned._int(client["elapsed_ms"], 0, 2**31 - 1, "prepared")
    owned._int(client["stderr_bytes"], 0, env.MAX_OUTPUT - evidence["stdout"]["bytes"], "prepared")
    return prepared, result, evidence


def prepare(authority_pin):
    """Consume the preparation grant through the shared locked reservation."""
    authority = _read_authority(authority_pin)
    plan_pin, ledger_pin = authority["plan"], authority["ledger"]
    observed = _inspect(plan_pin, ledger_pin, pending=False)
    env.require(observed["storage"]["would_fit"] is True, "storage_capacity")
    plan, proposal = load_plan(plan_pin)
    prepare_pin = plan["prepare"]
    claim = _save(CLAIM, _claim(authority_pin))
    authorization = _save(PREPARE_AUTH, dict(version=1, phase="prepare", prepare_scope=PREPARE_SCOPE,
                                              proposal_sha256=prepare_pin["sha256"],
                                              allow_environment_calls=True, root_go_pending=False))
    for pin in (authority_pin, authority["proposal"], plan_pin, ledger_pin, prepare_pin, claim, authorization):
        env.check_binding(pin)
    env.prepare(prepare_pin["path"], authorization["path"], expected_ledger=ledger_pin,
                expected_proposal_sha256=prepare_pin["sha256"], prepare_scope=PREPARE_SCOPE)
    prepared, result, evidence = _prepared_records(plan, proposal)
    prepared_ledger = _prepared_ledger(prepare_pin)
    for pin in (authority_pin, authority["proposal"], plan_pin, prepare_pin, claim, authorization,
                prepared_ledger, prepared, result, *evidence.values()):
        env.check_binding(pin)
    record = dict(version=1, scope=PREPARE_SCOPE, authority=authority_pin, claim=claim, plan=plan_pin,
                  authorization=authorization, ledger=prepared_ledger, prepared=prepared, result=result,
                  evidence=evidence, activation_authorized=False)
    _save(RESULT, record)
    return record


def main(argv=None):
    args = sys.argv[1:] if argv is None else argv
    try:
        env.require(type(args) is list and len(args) == 2 and args[0] == "--authority-sha256"
                    and type(args[1]) is str and re.fullmatch(r"[0-9a-f]{64}", args[1]) is not None, "authority")
        pin = env.binding(AUTHORITY)
        env.require(pin["sha256"] == args[1], "authority")
        prepare(pin)
    except (OSError, RuntimeError, ValueError, TypeError, KeyError):
        print(json.dumps(dict(scope=PREPARE_SCOPE, prepared=False)), flush=True)
        return 1
    print(json.dumps(dict(scope=PREPARE_SCOPE, prepared=True, activation_authorized=False)), flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
