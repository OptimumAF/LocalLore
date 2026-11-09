"""Drive and reverify SDK25 over the existing owned-target lifecycle.

Copyright 2026 LocalLore contributors. SPDX-License-Identifier: Apache-2.0
"""
from pathlib import Path

from benchmarks import archive_roundtrip_bridge as bridge
from benchmarks import archive_roundtrip_final as final
from benchmarks import archive_roundtrip_outbound as outbound
from benchmarks import isolated_adb_owner as process
from benchmarks import owned_archive_roundtrip_client as client
from benchmarks import owned_archive_roundtrip_contract as contract
from benchmarks import owned_archive_roundtrip_owner as owner
from benchmarks import receipt_avd_environment as env
from benchmarks import receipt_avd_storage as storage
from benchmarks import windows_tcp_control as output_control

SCOPE = "archive-roundtrip-controller-v1"
SECONDS = 1200
STOP_RESERVE = 10
RECORD_CAP = 2 * 1024 * 1024
LEDGER_CAP = 16 * 1024 * 1024
RESULT = "controller-result-v1.json"


class LifecycleRefused(ValueError):
    """A fixed refusal without raw process or filesystem details."""


def _need(condition, reason):
    if not condition:
        raise LifecycleRefused(reason)


def _at(pin, path, cap=RECORD_CAP):
    return env.decode_json(bridge._read(pin, path, cap))


def _read(path, cap=RECORD_CAP):
    pin = bridge._pin(path, cap)
    return pin, _at(pin, path, cap)


def _same(left, right):
    return contract._same(left, right)


def _inputs(admission_pin, running_pin):
    contract.binding(admission_pin, max_bytes=RECORD_CAP)
    admission = contract.validate_admission(_at(admission_pin, Path(admission_pin["path"])))
    root = Path(admission["root"])
    running = contract.validate_running(_at(running_pin, root / "running-v1.json"), admission, admission_pin)
    return admission, running


def _check_caller(caller, running):
    contract._process(caller)
    _need(caller["executable"] == running["python"]["executable"]["path"] and caller["pid"] not in
          {running[key]["pid"] for key in ("owner", "worker", "server", "launcher", "guest")},
          "controller_identity")


def _verify_exchange(admission_pin, running_pin, admission, running, caller, exchange):
    contract._obj(exchange, ("session", "bridge", "final"), "binding")
    session = outbound._session(admission, exchange["session"])
    _need(_same(session["admission"], admission_pin) and _same(session["running"], running_pin)
          and _same(session["descriptor"], running) and _same(session["caller"], caller), "session")
    return final.verify(admission, exchange["session"], exchange["bridge"], exchange["final"])


def stop_value(admission_pin):
    return dict(version=1, protocol=contract.PROTOCOL,
                admission_sha256=admission_pin["sha256"], action="stop")


def prepare_stop(root, admission_pin, observer):
    output_control.validate_output(str(root / "stop-v1.json"))
    pending = output_control.validate_output(str(root / "stop.pending-v1.json"))
    value = stop_value(admission_pin)
    contract.check_stop(value, admission_pin["sha256"])
    observer.guard(min_seconds=STOP_RESERVE)
    env.create_json(pending, value)
    pending_pin, retained = _read(pending)
    _need(_same(value, retained), "stop")
    observer.guard(min_seconds=STOP_RESERVE)
    return pending_pin


def commit_stop(root, admission_pin, pending_pin):
    path = output_control.validate_output(str(root / "stop-v1.json"))
    pending = root / "stop.pending-v1.json"
    value = stop_value(admission_pin)
    _need(_same(_at(pending_pin, pending), value), "stop")
    # The Windows-only output guard makes this a non-replacing rename.
    pending.rename(path)
    expected = dict(pending_pin, path=str(path))
    _need(_same(_at(expected, path), value), "stop")
    return expected


def drive(admission_pin, running_pin):
    """Exercise one already-running lease and close the controller observer."""
    admission, running = _inputs(admission_pin, running_pin)
    _need(admission["seconds"] > SECONDS + STOP_RESERVE, "controller_budget")
    root = Path(admission["root"])
    output = output_control.validate_output(str(root / outbound.OUTPUT))
    for name in ("stop-v1.json", "stop.pending-v1.json"):
        output_control.validate_output(str(root / name))
    observer = owner.LiveOwnedArchiveRoundtripTarget(admission_pin, running_pin)
    try:
        caller = observer.caller
        _check_caller(caller, running)
        observer.guard(min_seconds=SECONDS + STOP_RESERVE)
        output.mkdir()
        capture = client.OwnedArchiveRoundtripSdkCapture(output / "clients", SECONDS, observer)
        exchange = final.exchange(capture)
        _need(capture.clean is False, "capture")
        _verify_exchange(admission_pin, running_pin, admission, running, caller, exchange)
    finally:
        try:
            observer_closed = observer.close() is True
        except Exception as failure:
            raise LifecycleRefused("observer_cleanup") from failure
        _need(observer_closed, "observer_cleanup")
    path = output / RESULT
    value = dict(version=1, scope=SCOPE, admission=admission_pin, running=running_pin,
                 caller=caller, exchange=exchange, observer_closed=True)
    env.create_json(path, value)
    pin, retained = _read(path)
    _need(_same(retained, value), "controller_result")
    return pin


def _ledger(guest):
    registry = storage.DEFAULT_REGISTRY
    pin, ledger = _read(registry / "ledger-v1.json", LEDGER_CAP)
    storage._validate(ledger, registry)

    return pin, storage._entry(ledger, guest)


def _owner_closure(admission_pin, running_pin, admission, running, expected_owner):
    root = Path(admission["root"])
    guest = Path(admission["guest"]["root"])
    public_pin, public = _read(root / "result-v1.json")
    contract._obj(public, ("version", "protocol", "admission", "request", "started", "worker_result",
                           "owner", "after", "qualified_target", "reason", "feature_acceptance"), "binding")
    _need(_same(public["version"], 1) and public["protocol"] == contract.PROTOCOL and
          public["qualified_target"] is True and public["feature_acceptance"] is False and
          public["reason"] == "stop_requested" and _same(public["admission"], admission_pin), "owner")
    request = _at(public["request"], root / "request-v1.json")
    started = _at(public["started"], root / "started-v1.json")
    terminal = _at(public["owner"], root / "owner-result-v1.json")
    after = _at(public["after"], root / "after-v1.json")
    contract._obj(request, contract.REQUEST_KEYS, "binding")
    contract._obj(started, ("worker", "request"), "binding")
    _need(_same(request["version"], 1) and request["protocol"] == contract.PROTOCOL and
          _same(request["admission"], admission_pin) and _same(request["validated_admission"], admission)
          and _same(request["owner"], expected_owner) and _same(running["owner"], expected_owner)
          and _same(running["worker"], started["worker"]) and _same(started["request"], public["request"])
          and process._owner_ok(terminal, root / "worker-output-v1"), "owner")
    _need(_same(after, dict(admission=admission_pin, sources=admission["sources"], python=admission["python"],
                            tools=admission["server"]["tools"], owner=expected_owner,
                            process_handles_closed=True)), "owner")
    worker = owner.VERIFIER.verify_owned_target_result(public["worker_result"], admission, admission_pin,
                                                      public["request"], started["worker"])
    _need(worker["reason"] == "stop_requested" and worker["stop_requested"] is True
          and _same(worker["running"], running_pin) and set(worker["cleanup"]) == set(contract.CLEANUP_KEYS)
          and all(flag is True for flag in worker["cleanup"].values()), "worker_cleanup")
    closure_pin, closure = _read(guest / "guest-storage-closure-v1.json")
    _need(_same(closure, dict(version=1, proposal_sha256=admission["guest"]["proposal"]["sha256"],
                              closure_verified=True, cleanup_complete=True, admission=admission_pin,
                              owner_result=public["owner"], worker_result=public["worker_result"],
                              after=public["after"])), "closure")
    ledger_pin, entry = _ledger(guest)
    _need(entry["state"] == "closed" and entry["proposal_sha256"] == closure["proposal_sha256"]
          and entry.get("recovery") is None and entry["retirement"] is None
          and _same(entry["closure"], closure_pin), "ledger")
    for pin in (public_pin, public["request"], public["started"], public["owner"], public["worker_result"],
                public["after"], closure_pin, ledger_pin):
        env.check_binding(pin)
    return dict(owner=public_pin, closure=closure_pin, ledger=ledger_pin)


def verify_transfer(admission_pin, running_pin, admission, running, controller_pin, expected_caller):
    """Reverify the exchange and the separate controller's closed observer."""
    root = Path(admission["root"])
    _check_caller(expected_caller, running)
    value = _at(controller_pin, root / outbound.OUTPUT / RESULT)
    contract._obj(value, ("version", "scope", "admission", "running", "caller", "exchange",
                          "observer_closed"), "binding")
    _need(_same(value["version"], 1) and value["scope"] == SCOPE and value["observer_closed"] is True
          and _same(value["admission"], admission_pin) and _same(value["running"], running_pin)
          and _same(value["caller"], expected_caller), "controller_result")
    _verify_exchange(admission_pin, running_pin, admission, running, expected_caller, value["exchange"])
    env.check_binding(controller_pin)
    return value["exchange"]


def verify(admission_pin, running_pin, controller_pin, *, expected_owner, expected_caller):
    """Reverify the exact exchange and shared closure without acting on a guest."""
    admission, running = _inputs(admission_pin, running_pin)
    root = Path(admission["root"])
    stop_pin, stop = _read(root / "stop-v1.json")
    contract.check_stop(stop, admission_pin["sha256"])
    exchange = verify_transfer(admission_pin, running_pin, admission, running, controller_pin, expected_caller)
    closure = _owner_closure(admission_pin, running_pin, admission, running, expected_owner)
    for pin in (admission_pin, running_pin, controller_pin, stop_pin):
        env.check_binding(pin)
    return dict(closure, controller=controller_pin, final=exchange["final"])
