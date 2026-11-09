"""Read-only replay of a normally stopped cold-navigation guest and private ADB.

Copyright 2026 LocalLore contributors. SPDX-License-Identifier: Apache-2.0
"""
from pathlib import Path

from benchmarks import isolated_adb_owner as process
from benchmarks import owned_cold_navigation_ui_client as client
from benchmarks import owned_cold_navigation_ui_contract as contract
from benchmarks import owned_cold_navigation_ui_owner as owner
from benchmarks import receipt_avd_environment as env

_need = env.require
_same = contract._same


def verify_closure(admission_pin, admission, running_pin, owner_identity):
    """Join qualified process and storage closure to the observed owner identity."""
    admission = contract.validate_admission(admission)
    root = Path(admission["root"])
    guest = Path(admission["guest"]["root"])
    _need(admission["root"] == str(owner.OWNED_ROOT) and admission["guest"]["root"] == str(owner.GUEST)
          and _same(owner._at(admission_pin, owner.ADMISSION), admission), "admission")
    public_pin, public = owner._read(root / "result-v1.json")
    contract._obj(public, ("version", "protocol", "admission", "request", "started", "worker_result",
                           "owner", "after", "qualified_target", "reason", "feature_acceptance"), "owner")
    _need(_same(public["version"], 1) and public["protocol"] == contract.PROTOCOL
          and public["qualified_target"] is True and public["feature_acceptance"] is False
          and public["reason"] == "stop_requested" and _same(public["admission"], admission_pin), "owner")
    request = owner._at(public["request"], root / "request-v1.json")
    started = owner._at(public["started"], root / "started-v1.json")
    terminal = owner._at(public["owner"], root / "owner-result-v1.json")
    after = owner._at(public["after"], root / "after-v1.json")
    running = contract.validate_running(owner._at(running_pin, root / "running-v1.json"), admission, admission_pin)
    contract._obj(request, contract.REQUEST_KEYS, "request")
    contract._obj(started, ("worker", "request"), "owner")
    _need(_same(request["owner"], owner_identity) and _same(running["owner"], owner_identity)
          and _same(running["worker"], started["worker"]) and _same(started["request"], public["request"])
          and process._owner_ok(terminal, root / "worker-output-v1"), "owner")
    _need(_same(after, dict(admission=admission_pin, sources=admission["sources"], python=admission["python"],
                            tools=admission["server"]["tools"], owner=owner_identity,
                            process_handles_closed=True)), "owner")
    worker = client._REPLAY.verify_owned_target_result(public["worker_result"], admission, admission_pin,
                                                       public["request"], started["worker"])
    _need(worker["reason"] == "stop_requested" and worker["stop_requested"] is True
          and _same(worker["running"], running_pin) and set(worker["cleanup"]) == set(contract.CLEANUP_KEYS)
          and all(flag is True for flag in worker["cleanup"].values()), "cleanup")
    closure_pin, closure = owner._read(guest / "guest-storage-closure-v1.json")
    _need(_same(closure, dict(version=1, proposal_sha256=admission["guest"]["proposal"]["sha256"],
                              closure_verified=True, cleanup_complete=True, admission=admission_pin,
                              owner_result=public["owner"], worker_result=public["worker_result"],
                              after=public["after"])), "closure")
    ledger_pin, entry = owner._ledger(guest)
    _need(entry["state"] == "closed" and entry["proposal_sha256"] == closure["proposal_sha256"]
          and entry["recovery"] is None and entry["retirement"] is None
          and _same(entry["closure"], closure_pin), "ledger")
    for pin in (admission_pin, public_pin, running_pin, public["request"], public["started"], public["owner"],
                public["worker_result"], public["after"], closure_pin, ledger_pin):
        env.check_binding(pin)
    return dict(owner=public_pin, closure=closure_pin, ledger=ledger_pin)
