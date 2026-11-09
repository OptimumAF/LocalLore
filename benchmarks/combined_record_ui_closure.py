"""Replay a normally stopped SDK21 guest and private ADB from saved evidence.

Copyright 2026 LocalLore contributors. SPDX-License-Identifier: Apache-2.0
"""
from pathlib import Path

from benchmarks import combined_record_ui_handoff as handoff
from benchmarks import isolated_adb_owner as process
from benchmarks import owned_combined_record_ui_client as client
from benchmarks import owned_combined_record_ui_contract as contract
from benchmarks import receipt_avd_environment as env

_need = env.require
_same = contract._same


def verify_closure(admission_pin, admission, running_pin, owner_identity):
    """Join the qualified owner and storage closure to the observed owner."""
    contract._process(owner_identity)
    admission = contract.validate_admission(admission)
    root = Path(admission["root"])
    guest = Path(admission["guest"]["root"])
    _need(root == handoff.OWNED_ROOT and guest == handoff.GUEST
          and _same(handoff.at(admission_pin, handoff.ADMISSION), admission), "admission")
    public_pin, public = handoff.read(root / "result-v1.json")
    contract._obj(public, ("version", "protocol", "admission", "request", "started", "worker_result",
                           "owner", "after", "qualified_target", "reason", "feature_acceptance"), "owner")
    _need(_same(public["version"], 1) and public["protocol"] == contract.PROTOCOL
          and public["qualified_target"] is True and public["feature_acceptance"] is False
          and public["reason"] == "stop_requested" and _same(public["admission"], admission_pin), "owner")
    request = handoff.at(public["request"], root / "request-v1.json")
    started = handoff.at(public["started"], root / "started-v1.json")
    terminal = handoff.at(public["owner"], root / "owner-result-v1.json")
    after = handoff.at(public["after"], root / "after-v1.json")
    running = contract.validate_running(handoff.at(running_pin, root / "running-v1.json"), admission, admission_pin)
    contract._obj(request, contract.REQUEST_KEYS, "request")
    contract._obj(started, ("worker", "request"), "owner")
    _need(_same(request["owner"], owner_identity) and _same(running["owner"], owner_identity)
          and _same(running["worker"], started["worker"]) and _same(started["request"], public["request"])
          and process._owner_ok(terminal, root / "worker-output-v1"), "owner")
    _need(_same(after, dict(admission=admission_pin, sources=admission["sources"], python=admission["python"],
                            tools=admission["server"]["tools"], owner=owner_identity,
                            process_handles_closed=True)), "owner")
    worker = client.REPLAY.verify_owned_target_result(public["worker_result"], admission, admission_pin,
                                                      public["request"], started["worker"])
    contract._obj(worker["cleanup"], contract.CLEANUP_KEYS, "identity")
    _need(worker["reason"] == "stop_requested" and worker["stop_requested"] is True
          and _same(worker["running"], running_pin)
          and all(flag is True for flag in worker["cleanup"].values()), "cleanup")
    closure_pin, closure = handoff.read(guest / "guest-storage-closure-v1.json")
    _need(_same(closure, dict(version=1, proposal_sha256=admission["guest"]["proposal"]["sha256"],
                              closure_verified=True, cleanup_complete=True, admission=admission_pin,
                              owner_result=public["owner"], worker_result=public["worker_result"],
                              after=public["after"])), "closure")
    ledger_pin, entry = handoff.ledger_entry(guest)
    _need(entry["root"] == str(guest) and entry["state"] == "closed"
          and entry["proposal_sha256"] == closure["proposal_sha256"]
          and entry["recovery"] is None and entry["retirement"] is None and entry["retirement_receipt"] is None
          and _same(entry["closure"], closure_pin), "ledger")
    for pin in (admission_pin, public_pin, running_pin, public["request"], public["started"], public["owner"],
                public["worker_result"], public["after"], closure_pin, ledger_pin):
        env.check_binding(pin)
    return dict(owner=public_pin, closure=closure_pin, ledger=ledger_pin)
