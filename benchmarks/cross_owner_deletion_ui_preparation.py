"""Review and consume one exact SDK24 preparation-only approval.

Copyright 2026 LocalLore contributors. SPDX-License-Identifier: Apache-2.0
"""
import hashlib
import json
import os
from pathlib import Path, PureWindowsPath
import re
import sys

ROOT = Path(__file__).resolve().parents[1]
if __package__ in (None, ""):
    sys.path.insert(0, str(ROOT))

from benchmarks import adb_held_socket_probe as python_probe
from benchmarks import archive_ui_build as files
from benchmarks import cross_owner_deletion_ui_binding as artifacts
from benchmarks import cross_owner_deletion_ui_handoff as h
from benchmarks import isolated_adb_lease as server
from benchmarks import isolated_adb_owner as process
from benchmarks import owned_cross_owner_deletion_ui as owned
from benchmarks import owned_target_owner as mechanisms
from benchmarks import receipt_avd_environment as env
from benchmarks import receipt_avd_storage as storage

PREP_ROOT = Path("D:/Dev/Experiments/LocalLore/2026-11-09-cross-owner-deletion-preparation-v1")
PLAN = PREP_ROOT / "plan-v1.json"
PREPARE = PREP_ROOT / "prepare-proposal-v1.json"
PROPOSED_PREPARATION = PREP_ROOT / "PROPOSED_PREPARATION.md"
AUTHORITY = PREP_ROOT / "human-authority-v1.json"
CLAIM = PREP_ROOT / "claim-v1.json"
PREPARE_AUTH = PREP_ROOT / "prepare-authorization-v1.json"
RESULT = PREP_ROOT / "preparation-result-v1.json"
PREPARE_SCOPE = "sdk24-prepare-cross-owner-deletion-v1"
PLAN_SCOPE = "sdk24-cross-owner-deletion-preparation-plan-v1"
RECORDS_BYTES = 256 * 1024**2

_INSTALLED_KEYS = ("adb", "tools", "capabilities", "source_review", "auth_key_path",
                   "emulator", "qemu", "refuser", "refuser_source", "compatibility")
_RESULT_KEYS = ("version", "scope", "authority", "claim", "plan", "authorization",
                "ledger", "prepared", "result", "evidence")


def _save(path, value):
    env.create_json(path, value)
    pin, actual = h.read(path)
    env.require(owned._same(actual, value), "publication")
    return pin


def _fresh(*, pending):
    env.safe_path(PREP_ROOT, directory=True)
    env.safe_path(h.GUEST.parent, directory=True)
    paths = (h.GUEST, h.OUT, CLAIM, PREPARE_AUTH, RESULT)
    if pending:
        paths += (AUTHORITY,)
    for path in paths:
        env.safe_path(path, exists=False)
        env.require(not os.path.lexists(path), "already_used")


def server_admission(plan, run_id):
    installed = plan["installed"]
    sources = [pin for pin in plan["sources"]
               if PureWindowsPath(pin["path"]).name in server.SOURCE_NAMES | {"__init__.py"}]
    return dict(version=1, protocol=server.PROTOCOL, run_id=run_id,
                root=str(h.OWNED_ROOT / "server"), port=owned.PORT, seconds=h.OWNER_SECONDS,
                adb=installed["adb"], tools=installed["tools"], sdk_version=server.SDK_VERSION,
                expected_version="0029", sources=sources, python=plan["python"],
                auth_key=installed["auth_key_path"], capabilities=installed["capabilities"],
                source_review=installed["source_review"])


def build_plan(sdk, java_home, installed):
    """Write only the fixed, non-authorizing preparation inputs."""
    _fresh(pending=True)
    for path in (PREPARE, PLAN):
        env.safe_path(path, exists=False)
        env.require(not os.path.lexists(path), "already_used")
    owned._obj(installed, _INSTALLED_KEYS, "tool")
    pins = artifacts.artifact_bindings()
    artifacts.verify_artifacts(pins)
    sources, python = owned.source_bindings(), python_probe._python_bindings()
    installed = dict(installed, refuser_source=env.binding(ROOT / "benchmarks/native/deny_adb_client.c"))
    env.plan_prepare(h.GUEST, sdk, java_home, PREPARE, real_candidate=True, four_core_candidate=True)
    prepare_pin, _ = h.read(PREPARE, h.STORAGE_CAP)
    return _save(PLAN, dict(version=1, scope=PLAN_SCOPE, source_root=str(ROOT), sources=sources,
                            python=python, artifacts=pins, prepare=prepare_pin, installed=installed))


def load_plan(plan_pin):
    plan = h.at(plan_pin, PLAN, 131_072)
    owned._obj(plan, ("version", "scope", "source_root", "sources", "python", "artifacts",
                      "prepare", "installed"), "binding")
    env.require(owned._same(plan["version"], 1) and plan["scope"] == PLAN_SCOPE
                and plan["source_root"] == str(ROOT)
                and owned._same(plan["sources"], owned.source_bindings())
                and owned._same(plan["python"], python_probe._python_bindings()), "source")
    owned._obj(plan["installed"], _INSTALLED_KEYS, "tool")
    artifacts.verify_artifacts(plan["artifacts"])
    proposal = h.at(plan["prepare"], PREPARE, h.STORAGE_CAP)
    env.validate_proposal(proposal, "prepare")
    env.require(proposal["paths"]["root"] == str(h.GUEST)
                and owned._same(proposal["memory_mib"], 8192)
                and owned._same(proposal["cores"], 4), "invalid_profile")
    return plan, proposal


def verify_installed(plan, proposal):
    installed = plan["installed"]
    server.revalidate_inputs(server_admission(plan, "0" * 32))
    sdk = Path(proposal["sdk"])
    for role in ("emulator", "qemu", "refuser", "refuser_source", "compatibility"):
        owned.binding(installed[role], project=role not in ("emulator", "qemu"))
        env.check_binding(installed[role])
    env.require(installed["adb"]["path"] == proposal["adb_path"]
                and Path(installed["emulator"]["path"]) == sdk / "emulator/emulator.exe"
                and Path(installed["qemu"]["path"]) == sdk / "emulator/qemu/windows-x86_64/qemu-system-x86_64-headless.exe"
                and Path(installed["refuser"]["path"]).suffix.lower() == ".exe"
                and Path(installed["compatibility"]["path"]).suffix.lower() == ".md"
                and owned._same(installed["refuser_source"], env.binding(ROOT / "benchmarks/native/deny_adb_client.c")),
                "installed")
    key = Path(env.token_path()).parent / ".android/adbkey"
    env.require(installed["auth_key_path"] == str(key), "auth")
    key_info = env.safe_path(key).stat()
    env.require(key_info.st_size > 0 and key_info.st_nlink == 1, "auth")


def verify_resources_and_ports(proposal):
    facts = env.resource_facts(proposal)
    env.require(facts["free_bytes"]["D:"] >= proposal["host_free_min"]["D:"] + RECORDS_BYTES,
                "records_capacity")
    env.ports_free()
    private = process._exclusive_preflight(mechanisms._ProcessApi(), port=owned.PORT)
    env.require(private["exclusive_bind_succeeded"] is True
                and all(owned._same(private[key], 1) for key in
                        ("created_mask", "close_attempted_mask", "closed_mask")), "ports_unavailable")
    return facts


def _inspect(plan_pin, ledger_pin, *, pending):
    _fresh(pending=pending)
    plan, proposal = load_plan(plan_pin)
    ledger = h.at(ledger_pin, h.LEDGER, h.STORAGE_CAP)
    env.require(type(ledger) is dict and owned._same(ledger.get("version"), 2), "ledger")
    preview = storage.preview_prepare(h.GUEST)
    env.require(owned._same(preview["ledger"], ledger_pin) and preview["root"] == str(h.GUEST), "ledger")
    env.require(preview["would_fit"] is True and preview["admission_granted"] is False, "storage_capacity")
    verify_installed(plan, proposal)
    env.verify_installation(proposal)
    env.check_external_state(proposal)
    facts = verify_resources_and_ports(proposal)
    env.require(owned._same(plan["sources"], owned.source_bindings()), "source")
    artifacts.verify_artifacts(plan["artifacts"])
    for pin in (plan_pin, plan["prepare"], ledger_pin):
        env.check_binding(pin)
    _fresh(pending=pending)
    return dict(version=1, scope=PREPARE_SCOPE, plan=plan_pin, ledger=ledger_pin, resources=facts,
                storage=preview, ports_free=True, execution_authorized=False)


def inspect(plan_pin, ledger_pin):
    """Observe the exact pending preparation without creating an approval or claim."""
    return _inspect(plan_pin, ledger_pin, pending=True)


def _read_approval(pin):
    authority = h.at(pin, AUTHORITY, 16_384)
    owned._obj(authority, ("version", "scope", "proposal", "plan", "ledger", "approval_reference",
                            "allow_sdk_prepare", "allow_one_boot", "allow_model", "allow_retirement"), "auth")
    reference = authority["approval_reference"]
    env.require(owned._same(authority["version"], 1) and authority["scope"] == PREPARE_SCOPE
                and type(reference) is str and 0 < len(reference) <= 256 and reference == reference.strip()
                and all(32 <= ord(char) <= 126 for char in reference)
                and authority["allow_sdk_prepare"] is True and authority["allow_one_boot"] is False
                and authority["allow_model"] is False and authority["allow_retirement"] is False, "authority")
    owned.binding(authority["plan"], max_bytes=131_072)
    owned.binding(authority["ledger"], max_bytes=h.STORAGE_CAP)
    env.require(authority["plan"]["path"] == str(PLAN) and authority["ledger"]["path"] == str(h.LEDGER),
                "authority")
    lines = h._bound(authority["proposal"], PROPOSED_PREPARATION, 65_536).decode("utf-8").splitlines()
    for label, role in (("Plan SHA-256", "plan"), ("Ledger SHA-256", "ledger")):
        env.require([line for line in lines if line.startswith(label)]
                    == [label + " " + authority[role]["sha256"]], "authority")
    return authority


def _claim(authority_pin):
    return dict(version=1, scope=PREPARE_SCOPE, authority=authority_pin, no_retry=True)


def _prepared_ledger(prepare_pin):
    ledger_pin, entry = h.ledger_entry()
    env.require(entry["state"] == "prepared" and entry["proposal_sha256"] == prepare_pin["sha256"]
                and owned._same(entry["reserved_bytes"], storage.RESERVATION_BYTES)
                and all(entry[key] is None for key in ("closure", "recovery", "retirement", "retirement_receipt")),
                "prepared")
    return ledger_pin


def _prepare_evidence(prepare_pin, python_path):
    start_pin, start = h.read(h.GUEST / "prepare-start-v1.json", 8192)
    worker_pin, claim = h.read(h.GUEST / "prepare-worker-claimed-v1.json", 8192)
    client_pin, client = h.read(h.GUEST / "prepare-client-v1.json", 8192)
    owned._obj(start, ("proposal_sha256", "facts", "owner", "prepare_scope"), "prepared")
    owned._obj(claim, ("proposal_sha256", "worker", "prepare_scope"), "prepared")
    owned._obj(client, ("status", "returncode", "cleanup_complete", "elapsed_ms",
                         "stdout_sha256", "stderr_bytes"), "prepared")
    owner, worker = start["owner"], claim["worker"]
    owned._process(owner)
    owned._process(worker)
    env.require(owner["pid"] != worker["pid"] and owner["executable"] == worker["executable"] == python_path
                and owner["creation_filetime"] <= worker["creation_filetime"] and type(start["facts"]) is dict
                and all(row["proposal_sha256"] == prepare_pin["sha256"] and row["prepare_scope"] == PREPARE_SCOPE
                        for row in (start, claim)), "prepared")
    path = h.GUEST / "prepare-stdout-v1.bin"
    raw = files._read(path, env.MAX_OUTPUT)
    stdout = dict(path=str(path), bytes=len(raw), sha256=hashlib.sha256(raw).hexdigest())
    env.require(client["status"] == "completed" and owned._same(client["returncode"], 0)
                and client["cleanup_complete"] is True and client["stdout_sha256"] == stdout["sha256"]
                and type(client["elapsed_ms"]) is int and client["elapsed_ms"] >= 0
                and type(client["stderr_bytes"]) is int and 0 <= client["stderr_bytes"] <= env.MAX_OUTPUT - len(raw),
                "prepared")
    for pin in (start_pin, worker_pin, client_pin, stdout):
        env.check_binding(pin)
    return dict(start=start_pin, worker=worker_pin, client=client_pin, stdout=stdout)


def _prepared_records(plan, proposal):
    prepared, _ = h.read(h.GUEST / "prepared-v1.json")
    result, _ = h.read(h.GUEST / "prepare-result-v1.json", 8192)
    # Reuse central prepared replay without publishing any run proposal.
    run = dict(proposal, phase="run", prepare_proposal=plan["prepare"], prepared=prepared,
               prepare_result=result, max_seconds=h.ACTIVATION_SECONDS)
    env.validate_proposal(run, "run")
    env.verify_prepared(run, initial=True)
    evidence = _prepare_evidence(plan["prepare"], plan["python"]["executable"]["path"])
    return prepared, result, evidence


def prepare(approval_pin):
    """Consume a preparation-only grant through the central locked prepare path."""
    authority = _read_approval(approval_pin)
    plan_pin, ledger_pin = authority["plan"], authority["ledger"]
    _inspect(plan_pin, ledger_pin, pending=False)
    plan, proposal = load_plan(plan_pin)
    claim_pin = _save(CLAIM, _claim(approval_pin))
    prepare_pin = plan["prepare"]
    for pin in (approval_pin, authority["proposal"], plan_pin, ledger_pin, prepare_pin, claim_pin):
        env.check_binding(pin)
    authorization = _save(PREPARE_AUTH, dict(
        version=1, phase="prepare", prepare_scope=PREPARE_SCOPE, proposal_sha256=prepare_pin["sha256"],
        allow_environment_calls=True, root_go_pending=False,
    ))
    env.prepare(prepare_pin["path"], authorization["path"], expected_ledger=ledger_pin,
                expected_proposal_sha256=prepare_pin["sha256"], prepare_scope=PREPARE_SCOPE)
    prepared, result, evidence = _prepared_records(plan, proposal)
    prepared_ledger = _prepared_ledger(prepare_pin)
    for pin in (approval_pin, authority["proposal"], plan_pin, prepare_pin, claim_pin, authorization,
                prepared_ledger, prepared, result, *evidence.values()):
        env.check_binding(pin)
    record = dict(version=1, scope=PREPARE_SCOPE, authority=approval_pin, claim=claim_pin, plan=plan_pin,
                  authorization=authorization, ledger=prepared_ledger, prepared=prepared, result=result,
                  evidence=evidence)
    _save(RESULT, record)
    return record


def verify_preparation(plan_pin):
    """Read back the successful preparation while its fixed guest is still unused."""
    result_pin, record = h.read(RESULT)
    owned._obj(record, _RESULT_KEYS, "prepared")
    env.require(owned._same(record["version"], 1) and record["scope"] == PREPARE_SCOPE
                and owned._same(record["plan"], plan_pin), "prepared")
    authority = _read_approval(record["authority"])
    env.require(owned._same(authority["plan"], plan_pin)
                and owned._same(h.at(record["claim"], CLAIM, 16_384), _claim(record["authority"])),
                "authority")
    plan, proposal = load_plan(plan_pin)
    auth = h.at(record["authorization"], PREPARE_AUTH, 4096)
    env.check_authorization(auth, "prepare", plan["prepare"]["sha256"], prepare_scope=PREPARE_SCOPE)
    prepared, result, evidence = _prepared_records(plan, proposal)
    env.require(owned._same(record["prepared"], prepared) and owned._same(record["result"], result)
                and owned._same(record["evidence"], evidence), "prepared")
    owned.binding(record["ledger"], max_bytes=h.STORAGE_CAP)
    env.require(record["ledger"]["path"] == str(h.LEDGER), "ledger")
    current_ledger = _prepared_ledger(plan["prepare"])
    for pin in (result_pin, plan_pin, record["authority"], authority["proposal"], record["claim"],
                record["authorization"], prepared, result, current_ledger, *evidence.values()):
        env.check_binding(pin)
    return record


def main(argv=None):
    args = sys.argv[1:] if argv is None else argv
    try:
        env.require(type(args) is list and len(args) == 2 and args[0] == "--authority-sha256"
                    and type(args[1]) is str and re.fullmatch("[0-9a-f]{64}", args[1]) is not None,
                    "authority")
        pin, _ = h.read(AUTHORITY, 16_384)
        env.require(pin["sha256"] == args[1], "authority")
        prepare(pin)
    except (OSError, RuntimeError, ValueError, TypeError, KeyError):
        print(json.dumps(dict(scope=PREPARE_SCOPE, prepared=False)), flush=True)
        return 1
    print(json.dumps(dict(scope=PREPARE_SCOPE, prepared=True, activation_authorized=False)), flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
