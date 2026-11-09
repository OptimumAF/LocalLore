"""Replay the SDK26 controller, normal owner shutdown and closed storage receipt.

Copyright 2026 LocalLore contributors. SPDX-License-Identifier: Apache-2.0
"""
from pathlib import Path

from benchmarks import archive_provider_platform_admission as candidate
from benchmarks import archive_provider_platform_controller as controller
from benchmarks import archive_provider_platform_preparation as prep
from benchmarks import archive_ui_build as files
from benchmarks import isolated_adb_owner as process
from benchmarks import owned_archive_provider_platform as owned
from benchmarks import receipt_avd_environment as env
from benchmarks import receipt_avd_storage as storage


def _at(pin, path):
    return env.decode_json(prep._bound(pin, path))


def _read(path, cap=prep.RECORD_CAP):
    raw = files._read(path, cap)
    return candidate._pin_for_bytes(path, raw), env.decode_json(raw)


def verify_result(admission_pin, expected_owner):
    """Join both test results to the observed owner and its exact closed guest."""
    owned._process(expected_owner)
    admission = owned.validate_admission(_at(admission_pin, candidate.ADMISSION))
    root, guest = Path(admission["root"]), Path(admission["guest"]["root"])
    env.require(root == candidate.OWNED_ROOT and guest == prep.GUEST, "admission")

    public_pin, public = _read(root / "result-v1.json")
    owned._obj(public, ("version", "protocol", "admission", "request", "started", "worker_result",
                       "owner", "after", "qualified_target", "reason", "feature_acceptance"), "owner")
    env.require(owned._same(public["version"], 1) and public["protocol"] == owned.PROTOCOL
                and public["qualified_target"] is True and public["feature_acceptance"] is False
                and public["reason"] == "stop_requested"
                and owned._same(public["admission"], admission_pin), "owner")
    request = _at(public["request"], root / "request-v1.json")
    started = _at(public["started"], root / "started-v1.json")
    terminal = _at(public["owner"], root / "owner-result-v1.json")
    after = _at(public["after"], root / "after-v1.json")
    running_pin, running = _read(root / "running-v1.json")
    running = owned.validate_running(running, admission, admission_pin)
    owned._obj(request, owned.REQUEST_KEYS, "request")
    owned._obj(started, ("worker", "request"), "owner")
    capture = root / "worker-output-v1"
    env.require(owned._same(request["owner"], expected_owner)
                and owned._same(running["owner"], expected_owner)
                and owned._same(started["worker"], running["worker"])
                and owned._same(started["request"], public["request"])
                and process._owner_ok(terminal, capture), "owner")
    env.require(owned._same(after, dict(admission=admission_pin, sources=admission["sources"],
                                       python=admission["python"], tools=admission["server"]["tools"],
                                       owner=expected_owner, process_handles_closed=True)), "owner")

    stop_pin, stop = _read(root / "stop-v1.json")
    owned.check_stop(stop, admission_pin["sha256"])
    worker = owned.REPLAY.verify_owned_target_result(public["worker_result"], admission, admission_pin,
                                                     public["request"], started["worker"])
    owned._obj(worker["cleanup"], owned.CLEANUP_KEYS, "cleanup")
    env.require(worker["reason"] == "stop_requested" and worker["stop_requested"] is True
                and owned._same(worker["running"], running_pin)
                and all(flag is True for flag in worker["cleanup"].values()), "cleanup")

    closure_pin, closure = _read(guest / "guest-storage-closure-v1.json")
    proposal = admission["guest"]["proposal"]["sha256"]
    env.require(owned._same(closure, dict(version=1, proposal_sha256=proposal, closure_verified=True,
                                         cleanup_complete=True, admission=admission_pin, owner_result=public["owner"],
                                         worker_result=public["worker_result"], after=public["after"])), "closure")
    ledger_pin, ledger = _read(prep.LEDGER, 16 * 1024**2)
    storage._validate(ledger, storage.DEFAULT_REGISTRY)
    entry = storage._entry(ledger, guest)
    env.require(entry["root"] == str(guest) and entry["state"] == "closed"
                and entry["proposal_sha256"] == proposal
                and all(entry.get(key) is None for key in ("recovery", "retirement", "retirement_receipt"))
                and owned._same(entry["closure"], closure_pin), "ledger")

    controller_pin, _ = _read(root / "controller-v1" / controller.RESULT_FILE)
    controller.verify_controller_result(controller_pin, admission_pin, running_pin, started["worker"])
    env.require(process._owner_ok(terminal, capture), "owner")
    for pin in (admission_pin, public_pin, running_pin, stop_pin, public["request"], public["started"],
                public["owner"], public["worker_result"], public["after"], closure_pin, ledger_pin, controller_pin):
        env.check_binding(pin)
    return dict(controller=controller_pin, owner=public_pin, closure=closure_pin, ledger=ledger_pin)
