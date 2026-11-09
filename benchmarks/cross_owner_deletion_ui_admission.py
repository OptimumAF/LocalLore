"""Stage the exact SDK24 prepared admission without granting boot authority.

Copyright 2026 LocalLore contributors. SPDX-License-Identifier: Apache-2.0
"""
import hashlib
import os
from pathlib import Path
import uuid

from benchmarks import archive_ui_build as files
from benchmarks import cross_owner_deletion_ui_binding as artifacts
from benchmarks import cross_owner_deletion_ui_handoff as h
from benchmarks import cross_owner_deletion_ui_preparation as prep
from benchmarks import owned_cross_owner_deletion_ui as owned
from benchmarks import receipt_avd_environment as env
from benchmarks import receipt_avd_storage as storage


def _no_activation(*, staging=False):
    paths = (h.RUN_AUTHORITY, h.HANDOFF, h.OWNED_ROOT, h.COMPLETION, h.GUEST / owned.BOOT_CLAIM_FILE)
    if staging:
        paths += (h.ATTEMPT_ROOT, h.AUTHORITY, h.PROPOSAL)
    for path in paths:
        env.safe_path(path, exists=False)
        env.require(not os.path.lexists(path), "already_used")


def _prepared_inputs(plan_pin, ledger_pin=None):
    plan, prepare = prep.load_plan(plan_pin)
    proof = prep.verify_preparation(plan_pin)
    current, entry = h.ledger_entry(ledger_pin)
    env.require(entry["root"] == str(h.GUEST) and entry["state"] == "prepared"
                and owned._same(entry["reserved_bytes"], storage.RESERVATION_BYTES)
                and entry["proposal_sha256"] == plan["prepare"]["sha256"]
                and all(entry[key] is None for key in ("closure", "recovery", "retirement", "retirement_receipt")),
                "prepared")
    return plan, prepare, proof, current


def _auth_value(run_pin):
    return dict(version=1, phase="run", run_scope=owned.RUN_SCOPE,
                proposal_sha256=run_pin["sha256"], allow_environment_calls=True, root_go_pending=False)


def _pin_for_bytes(path, value):
    return dict(path=str(path), bytes=len(value), sha256=hashlib.sha256(value).hexdigest())


def _admission(plan, run_pin, run_id):
    installed = plan["installed"]
    guest = dict(root=str(h.GUEST), proposal=run_pin,
                 authorization=_pin_for_bytes(h.RUN_AUTHORITY, env.encoded(_auth_value(run_pin))),
                 emulator=installed["emulator"], qemu=installed["qemu"], refuser=installed["refuser"],
                 refuser_source=installed["refuser_source"], console_port=5592, adb_port=5593,
                 serial="emulator-5592", memory_mib=8192, cores=4, max_seconds=h.ACTIVATION_SECONDS,
                 api=35, abi="x86_64")
    return owned.validate_admission(dict(
        version=1, protocol=owned.PROTOCOL, run_id=run_id, root=str(h.OWNED_ROOT),
        seconds=h.OWNER_SECONDS, server=prep.server_admission(plan, run_id), guest=guest, artifacts=plan["artifacts"],
        sources=plan["sources"], python=plan["python"], compatibility=installed["compatibility"],
    ))


def _proposal_bytes(admission_pin, ledger_pin):
    _, klass, method = owned.INSTRUMENTATIONS[0]
    pins = artifacts.artifact_bindings()
    return (f"# Activate the prepared LocalLore SDK24 test guest once\n\n"
            f"Admission SHA-256 {admission_pin['sha256']}\n"
            f"Ledger SHA-256 {ledger_pin['sha256']}\n\n"
            f"Boot the prepared API 35 x86_64 guest at {h.GUEST} once with 8 GiB RAM and four cores. "
            "Reuse its existing 40 GiB reservation. The activation ceiling is 30 minutes. "
            "Allow up to 256 MiB for local records and recovery.\n\n"
            f"Run one model-free test, `{klass}#{method}`.\n\n"
            f"Product APK SHA-256 {pins['product_apk']['sha256']}\n"
            f"Test APK SHA-256 {pins['test_apk']['sha256']}\n\n"
            "Start and stop only the owned emulator on ports 5592 and 5593 and its private ADB service "
            "on port 15937. Admission requires "
            "fresh storage, host, port and ownership checks under the fixed SDK24 scope.\n\n"
            "This proposal covers activation only. Preparation, other guests, shared ADB, model operations, "
            "deletion, retirement, settings changes and merge are outside scope.\n").encode("utf-8")


def _expected_run(plan, prepare, proof):
    return dict(prepare, phase="run", prepare_proposal=plan["prepare"], prepared=proof["prepared"],
                prepare_result=proof["result"], max_seconds=h.ACTIVATION_SECONDS)


def _inspect(plan_pin, plan, prepare, proof, admission_pin, admission, ledger_pin):
    run_pin = admission["guest"]["proposal"]
    run = h.at(run_pin, h.RUN, h.STORAGE_CAP)
    expected = _expected_run(plan, prepare, proof)
    env.require(owned._same(run, expected)
                and owned._same(admission, _admission(plan, run_pin, admission["run_id"])), "admission")
    env.validate_proposal(run, "run")
    env.verify_prepared(run, initial=True)
    env.verify_installation(run)
    env.check_external_state(run)
    env.require(owned._same(plan["sources"], owned.source_bindings()), "source")
    artifacts.verify_artifacts(admission["artifacts"])
    prep.verify_installed(plan, run)
    prep.verify_resources_and_ports(run)
    for pin in (plan_pin, plan["prepare"], proof["prepared"], proof["result"], admission_pin, ledger_pin, run_pin):
        env.check_binding(pin)


def create_candidate(plan_pin):
    """Publish only review inputs for an already prepared, verified guest."""
    _no_activation(staging=True)
    plan, prepare, proof, ledger_pin = _prepared_inputs(plan_pin)
    prep.verify_resources_and_ports(_expected_run(plan, prepare, proof))
    env.check_binding(ledger_pin)
    _no_activation(staging=True)
    env.safe_path(h.OUT.parent, directory=True)
    env.safe_path(h.OUT, exists=False).mkdir(exist_ok=True)
    h.ATTEMPT_ROOT.mkdir(exist_ok=False)
    run = env.plan_run(plan["prepare"]["path"], h.GUEST / "prepared-v1.json", h.RUN,
                       max_seconds=h.ACTIVATION_SECONDS)
    run_pin, stored = h.read(h.RUN, h.STORAGE_CAP)
    env.require(owned._same(stored, run), "proposal")
    admission = _admission(plan, run_pin, uuid.uuid4().hex)
    env.create_json(h.ADMISSION, admission)
    admission_pin = env.binding(h.ADMISSION)
    _inspect(plan_pin, plan, prepare, proof, admission_pin, admission, ledger_pin)
    _no_activation()
    env.require(not os.path.lexists(h.AUTHORITY) and not os.path.lexists(h.ATTEMPT), "already_used")
    markdown = _proposal_bytes(admission_pin, ledger_pin)
    proposal = _pin_for_bytes(h.PROPOSAL, markdown)
    with env.safe_path(h.PROPOSAL, exists=False).open("xb") as output:
        output.write(markdown)
        output.flush()
        os.fsync(output.fileno())
    env.check_binding(proposal)
    return dict(admission=admission_pin, ledger=ledger_pin, proposal=proposal)


def verify_candidate(admission_pin, ledger_pin):
    """Recheck review inputs before any executable run authorization exists."""
    _no_activation()
    admission = owned.validate_admission(h.at(admission_pin, h.ADMISSION))
    plan_pin, _ = h.read(prep.PLAN, 131_072)
    plan, prepare, proof, current = _prepared_inputs(plan_pin, ledger_pin)
    env.require(owned._same(current, ledger_pin), "ledger")
    markdown = _proposal_bytes(admission_pin, ledger_pin)
    env.require(files._read(h.PROPOSAL, 65_536) == markdown, "proposal")
    _inspect(plan_pin, plan, prepare, proof, admission_pin, admission, ledger_pin)
    env.check_binding(_pin_for_bytes(h.PROPOSAL, markdown))
    _no_activation()
    return admission


def materialize_run_authorization(admission_pin, authority_pin, attempt_pin):
    """Write the already bound authorization only for an exact approved attempt."""
    approved = h._approval(authority_pin, attempt_pin, admission_pin)
    admission = verify_candidate(admission_pin, approved["ledger"])
    env.require(owned._same(h._approval(authority_pin, attempt_pin, admission_pin), approved), "authority")
    env.check_binding(approved["ledger"])
    guest = admission["guest"]
    env.create_json(h.RUN_AUTHORITY, _auth_value(guest["proposal"]))
    pin = env.binding(h.RUN_AUTHORITY)
    env.require(owned._same(pin, guest["authorization"]), "authorization")
    owned.revalidate_inputs(admission)
    env.check_binding(approved["ledger"])
    env.require(owned._same(h._approval(authority_pin, attempt_pin, admission_pin), approved), "authority")
    return pin
