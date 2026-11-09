"""Replay the fixed SDK24 deletion test and its normally stopped guest.

Copyright 2026 LocalLore contributors. SPDX-License-Identifier: Apache-2.0
"""
from pathlib import Path

from benchmarks import cross_owner_deletion_ui_controller as controller
from benchmarks import cross_owner_deletion_ui_handoff as handoff
from benchmarks import isolated_adb_owner as process
from benchmarks import owned_cross_owner_deletion_ui as owned
from benchmarks import receipt_avd_environment as env

_need = env.require
_same = owned._same


def verify_result(admission_pin):
    """Join controller, worker, owner and closed-ledger evidence for one run."""
    admission = owned.validate_admission(handoff.at(admission_pin, handoff.ADMISSION))
    root, guest = Path(admission["root"]), Path(admission["guest"]["root"])
    _need(root == handoff.OWNED_ROOT and guest == handoff.GUEST, "admission")

    public_pin, public = handoff.read(root / "result-v1.json")
    owned._obj(public, ("version", "protocol", "admission", "request", "started", "worker_result",
                        "owner", "after", "qualified_target", "reason", "feature_acceptance"), "owner")
    _need(_same(public["version"], 1) and public["protocol"] == owned.PROTOCOL
          and public["qualified_target"] is True and public["feature_acceptance"] is False
          and public["reason"] == "stop_requested" and _same(public["admission"], admission_pin), "owner")

    request = handoff.at(public["request"], root / "request-v1.json")
    started = handoff.at(public["started"], root / "started-v1.json")
    terminal = handoff.at(public["owner"], root / "owner-result-v1.json")
    after = handoff.at(public["after"], root / "after-v1.json")
    running_pin, running = handoff.read(root / "running-v1.json")
    running = owned.validate_running(running, admission, admission_pin)
    owned._obj(request, owned.REQUEST_KEYS, "request")
    owned._obj(started, ("worker", "request"), "owner")
    _need(_same(request["owner"], running["owner"])
          and _same(started["worker"], running["worker"]) and _same(started["request"], public["request"])
          and process._owner_ok(terminal, root / "worker-output-v1"), "owner")
    _need(_same(after, dict(admission=admission_pin, sources=admission["sources"], python=admission["python"],
                            tools=admission["server"]["tools"], owner=running["owner"],
                            process_handles_closed=True)), "owner")

    worker = owned.REPLAY.verify_owned_target_result(public["worker_result"], admission, admission_pin,
                                                    public["request"], started["worker"])
    owned._obj(worker["cleanup"], owned.CLEANUP_KEYS, "identity")
    _need(worker["reason"] == "stop_requested" and worker["stop_requested"] is True
          and _same(worker["running"], running_pin)
          and all(flag is True for flag in worker["cleanup"].values()), "cleanup")

    closure_pin, closure = handoff.read(guest / "guest-storage-closure-v1.json")
    _need(_same(closure, dict(version=1, proposal_sha256=admission["guest"]["proposal"]["sha256"],
                              closure_verified=True, cleanup_complete=True, admission=admission_pin,
                              owner_result=public["owner"], worker_result=public["worker_result"],
                              after=public["after"])), "closure")
    ledger_pin, entry = handoff.ledger_entry()
    _need(entry["root"] == str(guest) and entry["state"] == "closed"
          and entry["proposal_sha256"] == closure["proposal_sha256"]
          and entry["recovery"] is None and entry["retirement"] is None and entry["retirement_receipt"] is None
          and _same(entry["closure"], closure_pin), "ledger")

    controller_pin = owned.REPLAY._pin(root / "controller-v1" / controller.RESULT_FILE)
    controller.verify_controller_result(controller_pin, admission_pin, running_pin, started["worker"])
    for pin in (admission_pin, public_pin, running_pin, public["request"], public["started"], public["owner"],
                public["worker_result"], public["after"], closure_pin, ledger_pin, controller_pin):
        env.check_binding(pin)
    return dict(controller=controller_pin, owner=public_pin, closure=closure_pin, ledger=ledger_pin)
