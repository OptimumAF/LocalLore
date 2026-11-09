"""Fixed preparation inputs for the guarded synthetic picker operation.

Copyright 2026 LocalLore contributors. SPDX-License-Identifier: Apache-2.0
"""
import os
from pathlib import Path, PureWindowsPath
import uuid

from benchmarks import model_picker_action_binding as artifacts
from benchmarks import model_picker_action_handoff as h
from benchmarks import isolated_adb_lease as server
from benchmarks import isolated_adb_owner as process
from benchmarks import owned_model_picker_action as contract
from benchmarks import owned_target_owner as mechanisms
from benchmarks import receipt_avd_environment as env
from benchmarks import receipt_avd_storage as storage

CONTROL = h.ATTEMPT_ROOT / "activation-v1"


def _fresh_outputs(*, guest=False, pending=False):
    paths = (h.ADMISSION, h.RUN, h.RUN_AUTHORITY, h.HANDOFF, h.OWNED_ROOT, CONTROL)
    if pending:
        paths = (h.AUTHORITY, h.ATTEMPT_ROOT, *paths)
    else:
        env.safe_path(h.ATTEMPT_ROOT, directory=True)
    if guest:
        env.safe_path(h.GUEST.parent, directory=True)
        paths = (h.GUEST, *paths)
    for path in paths:
        env.safe_path(path, exists=False)
        env.require(not os.path.lexists(path), "already_used")


def _server(plan, run_id):
    installed = plan["installed"]
    sources = [pin for pin in plan["sources"]
               if PureWindowsPath(pin["path"]).name in server.SOURCE_NAMES | {"__init__.py"}]
    return dict(version=1, protocol=server.PROTOCOL, run_id=run_id,
                root=str(h.OWNED_ROOT / "server"), port=contract.PORT, seconds=h.OWNER_SECONDS,
                adb=installed["adb"], tools=installed["tools"], sdk_version=server.SDK_VERSION,
                expected_version="0029", sources=sources, python=plan["python"],
                auth_key=installed["auth_key_path"], capabilities=installed["capabilities"],
                source_review=installed["source_review"])


def _check_source_and_apks(plan):
    env.require(contract._same(plan["sources"], contract.source_bindings()), "source")
    artifacts.verify_artifacts(plan["artifacts"])


def _preflight(ledger_pin, plan, prepare, *, pending):
    _fresh_outputs(guest=True, pending=pending)
    env.require(contract._same(h.prepare_plan(plan), prepare), "plan")
    ledger = h.at(ledger_pin, h.LEDGER, cap=h.STORAGE_CAP)
    env.require(type(ledger) is dict and contract._same(ledger.get("version"), 2), "ledger")
    storage._validate(ledger, storage.DEFAULT_REGISTRY)
    preview = storage.preview_prepare(h.GUEST)
    env.require(contract._same(preview["ledger"], ledger_pin) and preview["root"] == str(h.GUEST), "binding")
    env.require(preview["would_fit"] is True and preview["admission_granted"] is False, "storage_capacity")

    _check_source_and_apks(plan)
    server.revalidate_inputs(_server(plan, "0" * 32))
    installed = plan["installed"]
    for role in ("emulator", "qemu", "refuser", "refuser_source", "compatibility"):
        contract.binding(installed[role], project=role not in ("emulator", "qemu"))
        env.check_binding(installed[role])
    sdk = Path(prepare["sdk"])
    qemu = sdk / "emulator/qemu/windows-x86_64/qemu-system-x86_64-headless.exe"
    refuser_source = h.ROOT / "benchmarks/native/deny_adb_client.c"
    env.require(installed["adb"]["path"] == prepare["adb_path"]
                and installed["emulator"]["path"] == str(sdk / "emulator/emulator.exe")
                and installed["qemu"]["path"] == str(qemu)
                and Path(installed["refuser"]["path"]).suffix.lower() == ".exe"
                and Path(installed["compatibility"]["path"]).suffix == ".md"
                and contract._same(installed["refuser_source"], env.binding(refuser_source)), "installed")
    env.verify_installation(prepare)
    env.check_external_state(prepare)
    key = Path(env.token_path()).parent / ".android/adbkey"
    env.require(installed["auth_key_path"] == str(key), "auth")
    key_info = env.safe_path(key).stat()
    env.require(key_info.st_size > 0 and key_info.st_nlink == 1, "auth")

    facts = env.resource_facts(prepare)
    env.ports_free()
    private = process._exclusive_preflight(mechanisms._ProcessApi(), port=contract.PORT)
    env.require(private["exclusive_bind_succeeded"] is True and
                all(contract._same(private[key], 1) for key in
                    ("created_mask", "close_attempted_mask", "closed_mask")), "ports_unavailable")
    _check_source_and_apks(plan)
    env.check_binding(plan["prepare"])
    env.check_binding(ledger_pin)
    _fresh_outputs(guest=True, pending=pending)
    return dict(resources=facts, storage=preview, ports_free=True)


def preflight(authority, plan, prepare):
    """Observe the exact approved inputs before reservation."""
    return _preflight(authority["ledger"], plan, prepare, pending=False)


def preflight_pending(ledger_pin, plan, prepare):
    """Observe the same gates before any human approval or attempt exists."""
    return _preflight(ledger_pin, plan, prepare, pending=True)


def create_admission(plan):
    """Bind the one prepared guest to the fixed scoped run."""
    _fresh_outputs()
    boot_claim = env.safe_path(h.GUEST / contract.BOOT_CLAIM_FILE, exists=False)
    env.require(not os.path.lexists(boot_claim), "already_used")
    h.prepare_plan(plan)
    prepare_pin = plan["prepare"]
    ledger_pin, entry = h.ledger_entry(h.GUEST)
    env.require(entry["state"] == "prepared" and entry["proposal_sha256"] == prepare_pin["sha256"]
                and contract._same(entry["reserved_bytes"], storage.RESERVATION_BYTES)
                and all(entry[key] is None for key in ("closure", "recovery", "retirement", "retirement_receipt")),
                "prepared")
    _check_source_and_apks(plan)
    proposal = env.plan_run(prepare_pin["path"], h.GUEST / "prepared-v1.json", h.RUN,
                            max_seconds=h.ACTIVATION_SECONDS)
    run_pin, saved = h.read(h.RUN, h.STORAGE_CAP)
    env.require(contract._same(proposal, saved) and contract._same(proposal["prepare_proposal"], prepare_pin),
                "proposal")
    run_auth = h.save(h.RUN_AUTHORITY, dict(
        version=1, phase="run", run_scope=contract.RUN_SCOPE, proposal_sha256=run_pin["sha256"],
        allow_environment_calls=True, root_go_pending=False,
    ))

    installed = plan["installed"]
    run_id = uuid.uuid4().hex
    guest = dict(root=str(h.GUEST), proposal=run_pin, authorization=run_auth,
                 emulator=installed["emulator"], qemu=installed["qemu"], refuser=installed["refuser"],
                 refuser_source=installed["refuser_source"], console_port=5592, adb_port=5593,
                 serial="emulator-5592", memory_mib=8192, cores=4, max_seconds=h.ACTIVATION_SECONDS,
                 api=35, abi="x86_64")
    admission = contract.validate_admission(dict(
        version=1, protocol=contract.PROTOCOL, run_id=run_id, root=str(h.OWNED_ROOT),
        seconds=h.OWNER_SECONDS, server=_server(plan, run_id), guest=guest, artifacts=plan["artifacts"],
        sources=plan["sources"], python=plan["python"], compatibility=installed["compatibility"],
    ))
    contract.revalidate_inputs(admission)
    env.check_binding(ledger_pin)
    return h.save(h.ADMISSION, admission)
