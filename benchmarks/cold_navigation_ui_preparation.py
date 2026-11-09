"""Fixed preparation inputs for the guarded cold-navigation operator.

Copyright 2026 LocalLore contributors. SPDX-License-Identifier: Apache-2.0
"""
import os
from pathlib import Path, PureWindowsPath
import uuid

from benchmarks import cold_navigation_ui_activation as activation
from benchmarks import isolated_adb_lease as server
from benchmarks import isolated_adb_owner as process
from benchmarks import owned_cold_navigation_ui_contract as contract
from benchmarks import owned_cold_navigation_ui_owner as owner
from benchmarks import receipt_avd_environment as env
from benchmarks import receipt_avd_storage as storage


def _fresh_outputs(*, guest=False, pending=False):
    paths = (owner.ADMISSION, owner.RUN, owner.RUN_AUTHORITY, owner.HANDOFF,
             owner.OWNED_ROOT, activation.CONTROL)
    if pending:
        paths = (owner.AUTHORITY, owner.ATTEMPT_ROOT, *paths)
    else:
        env.safe_path(owner.ATTEMPT_ROOT, directory=True)
    if guest:
        env.safe_path(owner.GUEST.parent, directory=True)
        paths = (owner.GUEST, *paths)
    for path in paths:
        env.safe_path(path, exists=False)
        env.require(not os.path.lexists(path), "already_used")


def _server(plan, run_id):
    installed = plan["installed"]
    sources = [pin for pin in plan["sources"]
               if PureWindowsPath(pin["path"]).name in server.SOURCE_NAMES | {"__init__.py"}]
    return dict(version=1, protocol=server.PROTOCOL, run_id=run_id,
                root=str(owner.OWNED_ROOT / "server"), port=contract.PORT, seconds=owner.OWNER_SECONDS,
                adb=installed["adb"], tools=installed["tools"], sdk_version=server.SDK_VERSION,
                expected_version="0029", sources=sources, python=plan["python"],
                auth_key=installed["auth_key_path"], capabilities=installed["capabilities"],
                source_review=installed["source_review"])


def _check_source_and_apks(plan):
    env.require(contract._same(plan["sources"], contract.source_bindings()), "source")
    contract.verify_artifacts(plan["artifacts"])


def _preflight(ledger_pin, plan, prepare, *, pending):
    _fresh_outputs(guest=True, pending=pending)
    ledger = owner._at(ledger_pin, owner.LEDGER, cap=owner._STORAGE_CAP)
    storage._validate(ledger, storage.DEFAULT_REGISTRY)
    env.require(contract._same(ledger["version"], 2), "ledger")
    preview = storage.preview_prepare(owner.GUEST)
    env.require(contract._same(preview["ledger"], ledger_pin) and preview["root"] == str(owner.GUEST), "binding")
    env.require(preview["would_fit"] is True and preview["admission_granted"] is False, "storage_capacity")

    _check_source_and_apks(plan)
    server.revalidate_inputs(_server(plan, "0" * 32))
    installed = plan["installed"]
    for role in ("emulator", "qemu", "refuser", "refuser_source", "compatibility"):
        contract.binding(installed[role], project=role not in ("emulator", "qemu"))
        env.check_binding(installed[role])
    sdk = Path(prepare["sdk"])
    qemu = sdk / "emulator/qemu/windows-x86_64/qemu-system-x86_64-headless.exe"
    refuser_source = owner.ROOT / "benchmarks/native/deny_adb_client.c"
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
    private = process._exclusive_preflight(owner.mechanisms._ProcessApi(), port=contract.PORT)
    env.require(private["exclusive_bind_succeeded"] is True and
                all(contract._same(private[key], 1) for key in
                    ("created_mask", "close_attempted_mask", "closed_mask")), "ports_unavailable")
    if pending:
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
    """Bind the one prepared guest to the fixed scoped run; return the published pin."""
    _fresh_outputs()
    boot_claim = env.safe_path(owner.GUEST / contract.BOOT_CLAIM_FILE, exists=False)
    env.require(not os.path.lexists(boot_claim), "already_used")
    prepare_pin = plan["prepare"]
    ledger_pin, entry = owner._ledger(owner.GUEST)
    env.require(entry["state"] == "prepared" and entry["proposal_sha256"] == prepare_pin["sha256"]
                and entry["reserved_bytes"] == storage.RESERVATION_BYTES
                and all(entry[key] is None for key in ("closure", "recovery", "retirement")),
                "prepared")
    proposal = env.plan_run(prepare_pin["path"], owner.GUEST / "prepared-v1.json", owner.RUN,
                            max_seconds=owner.ACTIVATION_SECONDS)
    run_pin, saved = owner._read(owner.RUN, owner._STORAGE_CAP)
    env.require(contract._same(proposal, saved) and contract._same(proposal["prepare_proposal"], prepare_pin),
                "proposal")
    run_auth = activation._save(owner.RUN_AUTHORITY, dict(
        version=1, phase="run", run_scope=contract.RUN_SCOPE, proposal_sha256=run_pin["sha256"],
        allow_environment_calls=True, root_go_pending=False,
    ))

    installed = plan["installed"]
    run_id = uuid.uuid4().hex
    guest = dict(root=str(owner.GUEST), proposal=run_pin, authorization=run_auth,
                 emulator=installed["emulator"], qemu=installed["qemu"], refuser=installed["refuser"],
                 refuser_source=installed["refuser_source"], console_port=5592, adb_port=5593,
                 serial="emulator-5592", memory_mib=8192, cores=4, max_seconds=owner.ACTIVATION_SECONDS,
                 api=35, abi="x86_64")
    admission = contract.validate_admission(dict(
        version=1, protocol=contract.PROTOCOL, run_id=run_id, root=str(owner.OWNED_ROOT),
        seconds=owner.OWNER_SECONDS, server=_server(plan, run_id), guest=guest, artifacts=plan["artifacts"],
        sources=plan["sources"], python=plan["python"], compatibility=installed["compatibility"],
    ))
    contract.revalidate_inputs(admission)
    env.check_binding(ledger_pin)
    return activation._save(owner.ADMISSION, admission)
