"""Review teardown of the single spent SDK24 registration attempt.

Copyright 2026 LocalLore contributors. SPDX-License-Identifier: Apache-2.0
"""
import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import sys
import time

if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from benchmarks import cross_owner_deletion_ui_handoff as h
from benchmarks import cross_owner_deletion_ui_operation as operation
from benchmarks import owned_cross_owner_deletion_ui as owned
from benchmarks import receipt_avd_environment as env
from benchmarks import receipt_avd_retirement_windows as native
from benchmarks import receipt_avd_storage as storage

SCOPE = "sdk24-failed-registration-closure-review-v1"
OBSERVED = (h.OUT.parent / "2026-11-09-cross-owner-deletion-operation-v1"
            / "approved-activation-audit-v1" / "observed-owner-v1.json")
FAILED_STDOUT = b'{"qualified_target": false, "reason": "owner", "feature_acceptance": false}'
_need = env.require
_same = owned._same


def _terminal(pin, path, capture, expected_stdout):
    """Pin the joined watchdog and its exact failure channels."""
    value = h.at(pin, path)
    owned._obj(value, operation.TERMINAL_KEYS, "terminal")
    _need(value["status"] == "child_exited" and value["cleanup_complete"] is True
          and value["output_capture_complete"] is True and _same(value["worker_returncode"], 1)
          and type(value["elapsed_ms"]) is int and 0 <= value["elapsed_ms"] <= h.ACTIVATION_SECONDS * 1000,
          "terminal")
    stdout = (expected_stdout + b"\n", expected_stdout + b"\r\n") if expected_stdout else (b"",)
    pins = []
    for name, expected in (("stdout", stdout), ("stderr", (b"",))):
        leaf = storage.safe_path(capture / f"owner-{name}-v1.bin", exists=True)
        with leaf.open("rb") as stream:
            raw = stream.read(max(map(len, expected)) + 1)
        _need(raw in expected and _same(value[name + "_bytes"], len(raw)), "capture")
        pins.append(dict(path=str(leaf), bytes=len(raw), sha256=hashlib.sha256(raw).hexdigest()))
    return tuple(pins)


def _identities(request, outer, worker, observation, admission):
    identities = [request["parent"], outer["worker"], observation["owner"], worker["worker"],
                  worker["server"], worker["launcher"], worker["guest"]]
    for value in identities:
        owned._process(value)
    python = admission["python"]["executable"]["path"]
    paths = [python] * 4 + [admission["server"]["adb"]["path"], admission["guest"]["emulator"]["path"],
                            admission["guest"]["qemu"]["path"]]
    _need([value["executable"] for value in identities] == paths
          and len({value["pid"] for value in identities}) == len(identities)
          and all(first["creation_filetime"] <= second["creation_filetime"]
                  for first, second in zip(identities, identities[1:]))
          and _same(worker["guest_ancestry"], identities[-2:])
          and _same(observation["supervisor_worker"], outer["worker"]), "identity")
    return identities


def _retain_entry(ledger_pin, proposal_pin):
    lock = storage.safe_path(h.LEDGER.parent / "admission.lock")
    _need(not os.path.lexists(lock), "registry_locked")
    _, entry = h.ledger_entry(ledger_pin)
    _check_retained(entry, proposal_pin)
    _need(not os.path.lexists(lock), "registry_locked")
    return entry


def _check_retained(entry, proposal_pin):
    _need(entry["root"] == str(h.GUEST) and entry["state"] == "retained"
          and _same(entry["reserved_bytes"], storage.RESERVATION_BYTES)
          and entry["proposal_sha256"] == proposal_pin["sha256"]
          and all(entry.get(key) is None for key in ("closure", "recovery", "retirement", "retirement_receipt")),
          "retained")


def _without_success():
    for path in (h.COMPLETION, h.GUEST / "guest-storage-closure-v1.json",
                 h.OWNED_ROOT / "running-v1.json", h.OWNED_ROOT / "target-ready-v1.json",
                 h.OWNED_ROOT / "controller-v1", h.OWNED_ROOT / "after-v1.json"):
        storage.safe_path(path)
        _need(not os.path.lexists(path), "unexpected_success_evidence")


def _registration(worker, admission_pin):
    root = h.OWNED_ROOT
    readiness = h.at(worker["readiness"], root / "readiness-v1.json")
    _need(type(readiness) is list and 3 <= len(readiness) <= 300, "registration")
    stages = [row["stage"] for row in readiness]
    _need(stages[-1] == "registration" and stages.count("registration") == 1
          and set(stages[:-1]) == {"guest_process", "guest_ports"}, "registration")
    registration_pin = readiness[-1]["queries"]
    record = h.at(registration_pin, root / "registration-0001-v1.json")
    owned._obj(record, ("version", "protocol", "admission", "running", "caller", "queries"), "registration")
    queries = record["queries"]
    _need(_same(record["version"], 1) and record["protocol"] == owned.PROOF_PROTOCOL
          and _same(record["admission"], admission_pin) and record["running"] is None
          and _same(record["caller"], worker["worker"]) and type(queries) is list and len(queries) == 2,
          "registration")
    version, devices = queries
    _need(version["kind"] == "version" and devices["kind"] == "devices"
          and version["response_hex"] == b"OKAY00040029".hex()
          and version["brackets"]["after"] is not None and devices["brackets"]["after"] is None
          and devices["observation_before"] is not None and devices["observation_after"] is None
          and all(query["eof"] is True and query["socket_closed"] is True for query in queries),
          "registration")
    raw = devices["response_hex"]
    _need(type(raw) is str and 16 < len(raw) <= 8208, "registration")
    response = bytes.fromhex(raw)
    _need(response[:4] == b"OKAY" and re.fullmatch(b"[0-9a-fA-F]{4}", response[4:8]) is not None
          and int(response[4:8], 16) == len(response) - 8
          and owned.device_status(response[8:])[0] == "offline", "registration")
    return registration_pin


def _snapshot(operation_pin, observation_pin, ledger_pin, *, locked_entry=None):
    result = h.at(operation_pin, operation.RESULT)
    owned._obj(result, ("version", "scope", "authority", "attempt", "request", "supervisor",
                        "completion", "passed", "reason", "feature_acceptance"), "operation")
    _need(_same(result["version"], 1) and result["scope"] == h.AUTHORITY_SCOPE
          and result["completion"] is None and result["passed"] is False and result["reason"] == "owner"
          and result["feature_acceptance"] is False, "operation")
    request = h.at(result["request"], operation.REQUEST)
    owned._obj(request, operation.REQUEST_KEYS, "request")
    _need(_same(request["version"], 1) and request["scope"] == h.AUTHORITY_SCOPE
          and all(_same(request[key], result[key]) for key in ("authority", "attempt"))
          and type(request["began_ns"]) is int and type(request["until_ns"]) is int
          and 0 < request["until_ns"] - request["began_ns"] <= h.ACTIVATION_SECONDS * h.NS, "request")
    admission_pin = request["admission"]
    approval = h._approval(result["authority"], result["attempt"], admission_pin)
    admission = owned.validate_admission(h.at(admission_pin, h.ADMISSION))
    guest = admission["guest"]
    _need(admission["root"] == str(h.OWNED_ROOT) and guest["root"] == str(h.GUEST)
          and _same(admission["seconds"], h.OWNER_SECONDS), "admission")
    script = next(pin for pin in admission["sources"] if Path(pin["path"]).name == owned.OWNER_SCRIPT)
    run = h.at(guest["proposal"], h.RUN, h.STORAGE_CAP)
    # Validate against the preparation helpers recorded by the spent run.
    env.validate_proposal(run, "run", preparation_root=Path(script["path"]).parents[1])
    _need(run["paths"]["root"] == str(h.GUEST)
          and all(_same(run[key], guest[key])
                  for key in ("serial", "console_port", "memory_mib", "cores", "max_seconds"))
          and run["adb_path"] == admission["server"]["adb"]["path"]
          and Path(run["sdk"]) / "emulator/emulator.exe" == Path(guest["emulator"]["path"]), "admission")
    env.check_authorization(h.at(guest["authorization"], h.RUN_AUTHORITY, 4096), "run",
                            guest["proposal"]["sha256"], run_scope=owned.RUN_SCOPE)
    if locked_entry is None:
        _retain_entry(ledger_pin, guest["proposal"])
    else:
        _check_retained(locked_entry, guest["proposal"])
    _without_success()

    supervisor = result["supervisor"]
    outer_stdout, outer_stderr = _terminal(supervisor, operation.TERMINAL, operation.CAPTURE, FAILED_STDOUT)
    outer_pin, outer = h.read(operation.STARTED)
    owned._obj(outer, ("request", "worker"), "identity")
    _need(_same(outer["request"], result["request"]), "request")
    handoff_pin, handoff = h.read(h.HANDOFF)
    _need(_same(handoff, operation._handoff(request, outer["worker"])), "handoff")

    root = h.OWNED_ROOT
    public_pin, public = h.read(root / "result-v1.json")
    owned._obj(public, ("version", "protocol", "admission", "request", "started", "worker_result",
                        "owner", "after", "qualified_target", "reason", "feature_acceptance"), "owner")
    _need(_same(public["version"], 1) and public["protocol"] == owned.PROTOCOL
          and _same(public["admission"], admission_pin) and public["after"] is None
          and public["qualified_target"] is False and public["reason"] == "owner"
          and public["feature_acceptance"] is False, "owner")
    inner = h.at(public["request"], root / "request-v1.json")
    started = h.at(public["started"], root / "started-v1.json")
    owned._obj(inner, owned.REQUEST_KEYS, "request")
    owned._obj(started, ("request", "worker"), "identity")
    _need(_same(inner, dict(version=1, protocol=owned.PROTOCOL, admission=admission_pin,
                            validated_admission=admission, owner=inner["owner"], sources=admission["sources"],
                            python=admission["python"], worker_script=script, owner_seconds=h.OWNER_SECONDS + 30))
          and _same(started["request"], public["request"]), "request")
    observed = h.at(observation_pin, OBSERVED)
    _need(_same(observed, dict(owner=inner["owner"], supervisor_worker=outer["worker"],
                              owner_request=public["request"], worker_started=outer_pin)), "identity")
    inner_stdout, inner_stderr = _terminal(public["owner"], root / "owner-result-v1.json",
                                           root / "worker-output-v1", b"")
    worker = h.at(public["worker_result"], root / "worker-result-v1.json")
    owned._obj(worker, owned.WORKER_KEYS, "worker")
    owned._obj(worker["cleanup"], owned.CLEANUP_KEYS, "cleanup")
    _need(_same(worker["version"], 1) and worker["protocol"] == owned.PROTOCOL
          and _same(worker["admission"], admission_pin) and _same(worker["request"], public["request"])
          and _same(worker["worker"], started["worker"]) and worker["reason"] == "registration"
          and type(worker["elapsed_ms"]) is int and 0 <= worker["elapsed_ms"] <= h.OWNER_SECONDS * 1000
          and worker["stop_requested"] is False and all(worker[key] is None for key in ("ready", "running", "guest_job"))
          and _same(worker["sources_after"], dict(sources=admission["sources"], python=admission["python"],
                                                  tools=admission["server"]["tools"], auth=worker["auth"]))
          and all(value is True for value in worker["cleanup"].values()), "cleanup")
    identities = _identities(request, outer, worker, observed, admission)
    registration_pin = _registration(worker, admission_pin)

    boot = h.at(worker["boot_claim"], h.GUEST / owned.BOOT_CLAIM_FILE)
    _need(_same(boot, dict(version=1, protocol=owned.PROTOCOL, admission=admission_pin,
                           worker=worker["worker"], proposal=guest["proposal"])), "boot_claim")
    terminal = h.at(worker["guest_terminal"], root / "guest-terminal-v1.json")
    owned._obj(terminal, ("version", "protocol", "guest", "returncode", "terminate_attempted",
                          "wait_completed", "handle_closed"), "guest_terminal")
    _need(_same(terminal["version"], 1) and terminal["protocol"] == owned.PROTOCOL
          and _same(terminal["guest"], worker["guest"]) and type(terminal["returncode"]) is int
          and all(terminal[key] is True for key in ("terminate_attempted", "wait_completed", "handle_closed")),
          "guest_terminal")
    server_capture = owned.REPLAY._capture(worker["server_capture"], root / "server-output-v1",
                                          worker["server"], worker["server_returncode"])
    guest_capture = owned.REPLAY._capture(worker["guest_capture"], root / "guest-output-v1",
                                         worker["launcher"], worker["guest_returncode"])

    return dict(operation=operation_pin, request=result["request"], attempt=result["attempt"],
                authority=result["authority"], proposal=approval["proposal"], admission=admission_pin,
                run=guest["proposal"], run_authority=guest["authorization"], ledger=ledger_pin,
                outer_started=outer_pin, handoff=handoff_pin, observed=observation_pin,
                outer_terminal=supervisor, outer_stdout=outer_stdout, outer_stderr=outer_stderr,
                owner=public_pin, owner_request=public["request"], owner_started=public["started"],
                inner_terminal=public["owner"], inner_stdout=inner_stdout, inner_stderr=inner_stderr,
                worker=public["worker_result"], boot=worker["boot_claim"], guest_terminal=worker["guest_terminal"],
                readiness=worker["readiness"], registration=registration_pin,
                server_capture=worker["server_capture"], guest_capture=worker["guest_capture"],
                server_stdout=server_capture["stdout"], server_stderr=server_capture["stderr"],
                guest_stdout=guest_capture["stdout"], guest_stderr=guest_capture["stderr"],
                **{f"source_{index:02d}": pin for index, pin in enumerate(admission["sources"], 1)}), identities


def inspect(operation_pin, observation_pin, ledger_pin):
    """Read one failed attempt without writing closure or altering its storage charge."""
    return _inspect(operation_pin, observation_pin, ledger_pin)


def _inspect(operation_pin, observation_pin, ledger_pin, *, locked_entry=None):
    if locked_entry is None:
        evidence, identities = _snapshot(operation_pin, observation_pin, ledger_pin)
    else:
        evidence, identities = _snapshot(operation_pin, observation_pin, ledger_pin, locked_entry=locked_entry)
    for pin in evidence.values():
        env.check_binding(pin)
    processes = native.closed_processes(identities, time.monotonic() + 5)
    _need(type(processes) is list and len(processes) == len(identities), "process_status")
    for observed, expected in zip(processes, identities):
        owned._obj(observed, ("identity", "status"), "process_status")
        _need(_same(observed["identity"], expected)
              and observed["status"] in ("pid_absent", "pid_reused", "exited"), "process_status")
    for pin in evidence.values():
        env.check_binding(pin)
    if locked_entry is None:
        _retain_entry(ledger_pin, evidence["run"])
    else:
        _check_retained(locked_entry, evidence["run"])
    _without_success()
    return dict(version=1, scope=SCOPE, disposition="guarded_closure_review_required",
                existing_retirement_eligible=False, execution_authorized=False, evidence=evidence,
                processes=processes)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    for key in ("operation", "observation", "ledger"):
        parser.add_argument(f"--{key}-sha256", required=True)
    args = parser.parse_args(argv)
    try:
        pins = []
        for path, sha in ((operation.RESULT, args.operation_sha256), (OBSERVED, args.observation_sha256),
                          (h.LEDGER, args.ledger_sha256)):
            _need(re.fullmatch("[0-9a-f]{64}", sha) is not None, "digest")
            pin = storage.binding(path)
            _need(pin["sha256"] == sha, "digest")
            pins.append(pin)
        report = inspect(*pins)
    except (OSError, RuntimeError, TypeError, ValueError, KeyError):
        print(json.dumps(dict(scope=SCOPE, disposition="refused", execution_authorized=False)), flush=True)
        return 1
    print(json.dumps(report, sort_keys=True), flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
