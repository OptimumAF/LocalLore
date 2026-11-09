"""Run one approved SDK25 exchange under the shared bounded Windows Jobs.

Copyright 2026 LocalLore contributors. SPDX-License-Identifier: Apache-2.0
"""
import os
from pathlib import Path
import re
import subprocess
import sys
import time

ROOT = Path(__file__).resolve().parents[1]
if __package__ in (None, ""):
    sys.path.insert(0, str(ROOT))

from benchmarks import archive_roundtrip_admission as admission
from benchmarks import archive_roundtrip_bridge as bridge
from benchmarks import archive_roundtrip_handoff as handoff
from benchmarks import archive_roundtrip_lifecycle as lifecycle
from benchmarks import archive_roundtrip_outbound as outbound
from benchmarks import isolated_adb_owner as process
from benchmarks import owned_archive_roundtrip_contract as contract
from benchmarks import owned_archive_roundtrip_owner as owner
from benchmarks import owned_target_owner as shared
from benchmarks import receipt_avd_environment as env
from benchmarks import windows_tcp_control as output_control

SCOPE = "sdk25-archive-roundtrip-supervision-v1"
BARRIER = b"locallore-sdk25-supervision-v1\n"
STOP_GATE = admission.CONTROL / "qualified-stop-v1.json"
RUNTIME_RESULT = admission.CONTROL / "runtime-result-v1.json"
OWNER_CONSOLE = admission.CONTROL / "owner-console-v1"
OWNER_STARTED = admission.CONTROL / "owner-started-v1.json"
OWNER_TERMINAL = admission.CONTROL / "owner-terminal-v1.json"
READY_SECONDS = 240
TAIL_SECONDS = 20
STAGES = ("runtime", "controller")
CONTEXT_KEYS = ("authority", "attempt", "admission", "began_ns", "until_ns")
REFUSALS = frozenset(("admission", "authority", "barrier", "controller_budget", "deadline", "handoff",
                      "identity", "observer_cleanup", "owner_not_ready", "owner_terminal", "platform",
                      "publication", "request", "runtime", "stage", "stage_terminal", "stop"))


def _need(condition, reason):
    admission._need(condition, reason)


def _same(left, right):
    return contract._same(left, right)


def _save(path, value):
    env.create_json(path, value)
    pin, actual = lifecycle._read(path)
    _need(_same(actual, value), "publication")
    return pin


def _path(kind, name):
    _need(kind in STAGES, "stage")
    return admission.CONTROL / f"{kind}-{name}-v1.json"


def _capture(kind):
    _need(kind in STAGES, "stage")
    return admission.CONTROL / (kind + "-capture-v1")


def _identity(pid, expected=None):
    handles = process.ProcessHandles(shared._ProcessApi())
    try:
        return handles.add(pid, expected)[1]
    finally:
        _need(handles.close() is True, "identity")


def _remaining(record):
    handoff.check_window(record)
    remaining = (record["until_ns"] - time.monotonic_ns()) // handoff.NS
    _need(remaining > 0, "deadline")
    return remaining


def _request(kind, authority_pin, attempt_pin, admission_pin, window, running_pin):
    return dict(version=1, scope=SCOPE, kind=kind, authority=authority_pin, attempt=attempt_pin,
                admission=admission_pin, began_ns=window["began_ns"], until_ns=window["until_ns"],
                running=running_pin, parent=_identity(os.getpid()))


def _check_request(value, kind):
    contract._obj(value, ("version", "scope", "kind", "authority", "attempt", "admission",
                          "began_ns", "until_ns", "running", "parent"), "binding")
    _need(_same(value["version"], 1) and value["scope"] == SCOPE and value["kind"] == kind,
          "request")
    contract._process(value["parent"])
    for key in ("authority", "attempt", "admission"):
        contract.binding(value[key], max_bytes=lifecycle.RECORD_CAP)
    if kind == "controller":
        contract.binding(value["running"], max_bytes=lifecycle.RECORD_CAP)
    else:
        _need(value["running"] is None, "request")


def _terminal(kind, terminal_pin):
    value = lifecycle._at(terminal_pin, _path(kind, "terminal"))
    _need(process._owner_ok(value, _capture(kind)), "stage_terminal")
    request_pin, request = lifecycle._read(_path(kind, "request"))
    started_pin, started = lifecycle._read(_path(kind, "started"))
    _check_request(request, kind)
    contract._obj(started, ("request", "worker"), "binding")
    contract._process(started["worker"])
    _need(_same(started["request"], request_pin) and
          started["worker"]["executable"] == request["parent"]["executable"] and
          started["worker"]["pid"] != request["parent"]["pid"] and
          started["worker"]["creation_filetime"] >= request["parent"]["creation_filetime"], "identity")
    for pin in (terminal_pin, request_pin, started_pin):
        env.check_binding(pin)
    return request, started["worker"]


def _supervise(request):
    kind = request["kind"]
    _check_request(request, kind)
    path = output_control.validate_output(str(_capture(kind)))
    path.mkdir()
    request_pin = _save(_path(kind, "request"), request)
    worker = None

    def started(child):
        nonlocal worker
        _remaining(request)
        worker = _identity(child.pid)
        _need(worker["executable"] == request["parent"]["executable"], "identity")
        pending = output_control.validate_output(str(_path(kind, "started").with_suffix(".pending.json")))
        final_path = output_control.validate_output(str(_path(kind, "started")))
        _save(pending, dict(request=request_pin, worker=worker))
        pending.rename(final_path)
        return True

    remaining = _remaining(request)
    seconds = remaining if kind == "runtime" else min(remaining - TAIL_SECONDS, 1280)
    _need(kind == "runtime" or seconds >= lifecycle.SECONDS, "controller_budget")
    command = [request["parent"]["executable"], "-I", "-S", "-B", str(Path(__file__)), "_" + kind]
    supervise = env.supervise_operation if kind == "runtime" else env.supervise
    value = supervise(command, BARRIER + env.encoded(request_pin), path, seconds, started)
    pin = _save(_path(kind, "terminal"), value)
    actual_request, identified = _terminal(kind, pin)
    _need(worker is not None and _same(identified, worker) and _same(actual_request, request), "identity")
    return pin, worker


def _enter(kind):
    raw = sys.stdin.buffer.read(131073)
    _need(len(raw) <= 131072 and raw.startswith(BARRIER), "barrier")
    request_pin = env.decode_json(raw[len(BARRIER):])
    request = lifecycle._at(request_pin, _path(kind, "request"))
    _check_request(request, kind)
    _need(os.getppid() == request["parent"]["pid"], "identity")
    _identity(os.getppid(), request["parent"])
    _need(os.getpid() in shared._ProcessApi().current_job_pids(), "identity")
    _remaining(request)
    until = min(request["until_ns"], time.monotonic_ns() + 5 * handoff.NS)
    path = _path(kind, "started")
    while not os.path.lexists(path):
        _need(time.monotonic_ns() < until, "identity")
        time.sleep(.02)
    started_pin, started = lifecycle._read(path)
    contract._obj(started, ("request", "worker"), "binding")
    _need(_same(started["request"], request_pin), "request")
    _identity(os.getpid(), started["worker"])
    env.check_binding(started_pin)
    env.check_binding(request_pin)
    _remaining(request)
    return request


def _read_handoff(pin):
    launch = lifecycle._at(pin, handoff.HANDOFF, admission.AUTHORITY_CAP)
    contract._obj(launch, ("version", "scope", "supervisor", *CONTEXT_KEYS), "binding")
    _need(_same(launch["version"], 1) and launch["scope"] == handoff.SCOPE, "handoff")
    contract._process(launch["supervisor"])
    return launch


def _same_context(left, right):
    return all(_same(left[key], right[key]) for key in CONTEXT_KEYS)


def _controller():
    request = _enter("controller")
    pin, _ = lifecycle._read(handoff.HANDOFF, admission.AUTHORITY_CAP)
    launch = _read_handoff(pin)
    _need(_same(launch["supervisor"], request["parent"]) and _same_context(launch, request), "handoff")
    _remaining(request)
    lifecycle.drive(request["admission"], request["running"])


def _stop_gate(request, launch_pin, running_pin, controller_pin, terminal_pin):
    root = admission.OWNED_ROOT
    stop = bridge._pin_bytes(root / "stop-v1.json", env.encoded(lifecycle.stop_value(request["admission"])))
    return dict(version=1, scope=SCOPE, handoff=launch_pin, admission=request["admission"],
                running=running_pin, controller=controller_pin, terminal=terminal_pin, stop=stop)


def verify_stop(admitted, admission_pin, worker, *, expected_handoff_sha256=None):
    """Required by the SDK25 parent before it can write shared storage closure."""
    _need(worker["reason"] == "stop_requested" and worker["stop_requested"] is True, "stop")
    gate_pin, gate = lifecycle._read(STOP_GATE)
    contract._obj(gate, ("version", "scope", "handoff", "admission", "running", "controller",
                         "terminal", "stop"), "binding")
    _need(_same(gate["version"], 1) and gate["scope"] == SCOPE and _same(gate["admission"], admission_pin)
          and _same(gate["running"], worker["running"]), "stop")
    launch = _read_handoff(gate["handoff"])
    _need((expected_handoff_sha256 is None or gate["handoff"]["sha256"] == expected_handoff_sha256)
          and _same(launch["admission"], admission_pin), "handoff")
    request, controller = _terminal("controller", gate["terminal"])
    _need(_same(request["parent"], launch["supervisor"]) and _same(request["running"], gate["running"])
          and _same_context(request, launch), "request")
    expected = _stop_gate(request, gate["handoff"], gate["running"], gate["controller"], gate["terminal"])
    _need(_same(gate, expected), "stop")
    stop = lifecycle._at(gate["stop"], admission.OWNED_ROOT / "stop-v1.json")
    _need(_same(stop, lifecycle.stop_value(admission_pin)), "stop")
    actual, running = lifecycle._inputs(admission_pin, gate["running"])
    _need(_same(admitted, actual), "admission")
    lifecycle.verify_transfer(admission_pin, gate["running"], admitted, running, gate["controller"], controller)
    for pin in (gate_pin, gate["handoff"], gate["stop"], request["authority"], request["attempt"]):
        env.check_binding(pin)
    return gate


def _publish_stop(request, admitted, launch_pin, running_pin, running, controller_pin, terminal_pin):
    controller_request, controller = _terminal("controller", terminal_pin)
    _need(_same(controller_request["parent"], _identity(os.getpid())) and
          _same(controller_request["running"], running_pin) and _same_context(controller_request, request),
          "request")
    lifecycle.verify_transfer(request["admission"], running_pin, admitted, running, controller_pin, controller)
    _remaining(request)
    gate = _stop_gate(request, launch_pin, running_pin, controller_pin, terminal_pin)
    observer = owner.LiveOwnedArchiveRoundtripTarget(request["admission"], running_pin)
    try:
        pending = lifecycle.prepare_stop(admission.OWNED_ROOT, request["admission"], observer)
    finally:
        _need(observer.close() is True, "observer_cleanup")
    _remaining(request)
    _save(STOP_GATE, gate)
    _remaining(request)
    stop = lifecycle.commit_stop(admission.OWNED_ROOT, request["admission"], pending)
    _need(_same(stop, gate["stop"]), "stop")
    return controller


def _wait_ready(child, capture, request, admitted, identity):
    path = admission.OWNED_ROOT / "running-v1.json"
    latest = min(request["until_ns"] - (lifecycle.SECONDS + TAIL_SECONDS) * handoff.NS,
                 time.monotonic_ns() + READY_SECONDS * handoff.NS)
    while True:
        _need(child.poll() is None and time.monotonic_ns() < latest, "owner_not_ready")
        capture.guard()
        if os.path.lexists(path):
            break
        time.sleep(.1)
    pin, raw = lifecycle._read(path)
    running = contract.validate_running(raw, admitted, request["admission"])
    _need(_same(running["owner"], identity) and
          running["deadline_epoch"] - time.time() >= lifecycle.SECONDS + lifecycle.STOP_RESERVE,
          "controller_budget")
    return pin, running


def _owner_terminal(pin, identity):
    value = lifecycle._at(pin, OWNER_TERMINAL)
    contract._obj(value, ("owner", "returncode", "cleanup"), "binding")
    expected_cleanup = dict(terminate_attempted=False, wait_completed=True, process_handle_closed=True,
                            pipes_closed=True, output_capture_complete=True)
    _need(_same(value["owner"], identity) and _same(value["returncode"], 0) and
          _same(value["cleanup"], expected_cleanup), "owner_terminal")
    stdout = bridge.files._read(OWNER_CONSOLE / "owner-stdout-v1.bin", process.CAP)
    stderr = bridge.files._read(OWNER_CONSOLE / "owner-stderr-v1.bin", process.CAP - len(stdout))
    _need(not stderr and _same(env.decode_json(stdout),
          dict(qualified_target=True, reason="stop_requested", feature_acceptance=False)), "owner_terminal")


def _runtime():
    request = _enter("runtime")
    context = admission.verify_spent(request["authority"], request["attempt"])
    _need(_same(context["admission_pin"], request["admission"]), "admission")
    admitted = context["admission"]
    launch_pin = handoff.write(request["authority"], request["attempt"],
                               began_ns=request["began_ns"], until_ns=request["until_ns"])
    _remaining(request)
    capture = process.ServerCapture(output_control.validate_output(str(OWNER_CONSOLE)))
    child = identity = None
    try:
        executable = admitted["python"]["executable"]["path"]
        env.check_binding(launch_pin)
        handoff.check_window(request, launching=True)
        child = subprocess.Popen(
            [executable, "-I", "-S", "-B", str(ROOT / "benchmarks" / contract.OWNER_SCRIPT),
             "--admission", str(admission.ADMISSION), "--admission-sha256", request["admission"]["sha256"]],
            stdin=subprocess.DEVNULL, stdout=subprocess.PIPE, stderr=subprocess.PIPE, bufsize=0,
            env=dict(os.environ, **{handoff.HANDOFF_ENV: launch_pin["sha256"]}),
            creationflags=subprocess.CREATE_NO_WINDOW)
        capture.start(child)
        identity = _identity(child.pid)
        _need(identity["executable"] == executable, "identity")
        started = _save(OWNER_STARTED, dict(owner=identity, handoff=launch_pin))
        running_pin, running = _wait_ready(child, capture, request, admitted, identity)
        controller_request = _request("controller", request["authority"], request["attempt"],
                                      request["admission"], request, running_pin)
        terminal_pin, worker = _supervise(controller_request)
        _need(child.poll() is None, "owner_terminal")
        capture.guard()
        controller_pin, _ = lifecycle._read(admission.OWNED_ROOT / outbound.OUTPUT / lifecycle.RESULT)
        _need(_same(_publish_stop(request, admitted, launch_pin, running_pin, running, controller_pin, terminal_pin),
                    worker), "identity")
        while child.poll() is None:
            _remaining(request)
            capture.guard()
            time.sleep(.1)
    finally:
        try:
            exited = child is not None and child.poll() is not None
        except (OSError, ValueError):
            exited = False
        cleanup, code = shared._close_popen(child, capture, allow_terminate=exited)
        owner_terminal = _save(OWNER_TERMINAL, dict(owner=identity, returncode=code, cleanup=cleanup))
    _owner_terminal(owner_terminal, identity)
    proof = lifecycle.verify(request["admission"], running_pin, controller_pin,
                             expected_owner=identity, expected_caller=worker)
    _save(RUNTIME_RESULT, dict(version=1, scope=SCOPE, admission=request["admission"], running=running_pin,
                              started=started, terminal=owner_terminal, controller=controller_pin,
                              controller_terminal=terminal_pin, proof=proof))


def _verify_runtime(request, runtime):
    _, value = lifecycle._read(RUNTIME_RESULT)
    contract._obj(value, ("version", "scope", "admission", "running", "started", "terminal",
                          "controller", "controller_terminal", "proof"), "binding")
    _need(_same(value["version"], 1) and value["scope"] == SCOPE and
          _same(value["admission"], request["admission"]), "runtime")
    started = lifecycle._at(value["started"], OWNER_STARTED)
    contract._obj(started, ("owner", "handoff"), "binding")
    launch = _read_handoff(started["handoff"])
    _need(_same(launch["supervisor"], runtime) and _same_context(launch, request), "handoff")
    _owner_terminal(value["terminal"], started["owner"])
    controller_request, controller = _terminal("controller", value["controller_terminal"])
    _need(_same(controller_request["parent"], runtime) and _same(controller_request["running"], value["running"])
          and _same_context(controller_request, request), "request")
    gate_pin, gate = lifecycle._read(STOP_GATE)
    expected = _stop_gate(request, started["handoff"], value["running"], value["controller"],
                          value["controller_terminal"])
    _need(_same(gate, expected), "stop")
    proof = lifecycle.verify(request["admission"], value["running"], value["controller"],
                             expected_owner=started["owner"], expected_caller=controller)
    env.check_binding(gate_pin)
    _need(_same(proof, value["proof"]), "runtime")
    return proof


def execute(authority_pin):
    """Spend one fixed authority and supervise one owned operation."""
    _need(os.name == "nt", "platform")
    output_control._prepare_environment()
    began = time.monotonic_ns()
    window = dict(began_ns=began, until_ns=began + handoff.MAX_SECONDS * handoff.NS)
    attempt = admission.spend(authority_pin)
    context = admission.verify_spent(authority_pin, attempt)
    request = _request("runtime", authority_pin, attempt, context["admission_pin"], window, None)
    _need(request["parent"]["executable"] == context["admission"]["python"]["executable"]["path"], "identity")
    handoff.check_window(request, launching=True)
    terminal, runtime = _supervise(request)
    proof = _verify_runtime(request, runtime)
    env.check_binding(terminal)
    return proof


def main(argv=None):
    args = sys.argv[1:] if argv is None else argv
    try:
        _need(os.name == "nt", "platform")
        if args == ["_runtime"]:
            _runtime()
        elif args == ["_controller"]:
            _controller()
        else:
            _need(type(args) is list and len(args) == 2 and args[0] == "--authority-sha256"
                  and re.fullmatch("[0-9a-f]{64}", args[1]) is not None, "authority")
            pin, _ = lifecycle._read(admission.AUTHORITY, admission.AUTHORITY_CAP)
            _need(pin["sha256"] == args[1], "authority")
            execute(pin)
        return 0
    except Exception as error:
        reason = str(error) if type(error) is admission.AdmissionRefused else ""
        print(reason if reason in REFUSALS else "supervision_failed", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
