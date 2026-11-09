"""Supervise one prepared SDK19 Story Record guest and verify its closure.

Copyright 2026 LocalLore contributors. SPDX-License-Identifier: Apache-2.0
"""
import hashlib
import os
from pathlib import Path
import re
import subprocess
import sys
import time

ROOT = Path(__file__).parents[1]
if __package__ in (None, ""):
    sys.path.insert(0, str(ROOT))

from benchmarks import android_process_record_large_text_ui_verification as verification
from benchmarks import archive_ui_build as files
from benchmarks import isolated_adb_owner as process
from benchmarks import owned_record_large_text_ui_contract as contract
from benchmarks import owned_target_owner as owner_mechanisms
from benchmarks import receipt_avd_environment as env
from benchmarks import receipt_avd_storage as storage
from benchmarks import record_large_text_ui_controller as controller
from benchmarks.owned_record_large_text_ui_owner import LiveOwnedRecordLargeTextUiTarget

RUNTIME = Path("D:/Dev/Experiments/LocalLore/2026-11-09-record-large-text-ui-runtime-v1")
ADMISSION = RUNTIME / "admission-v1.json"
CONTROL = RUNTIME / "control-v1"
BARRIER = b"record-large-text-ui-activation-v1\n"
SCOPE = "record-large-text-ui-activation-v1"
OWNER_SECONDS = 1700
OUTER_SECONDS = 1800
TERMINAL_KEYS = frozenset(("status", "worker_returncode", "cleanup_complete", "output_capture_complete",
                           "elapsed_ms", "stdout_bytes", "stderr_bytes"))
_need = env.require
_same = contract._same


def _file(path, maximum):
    raw = files._read(path, maximum)
    return dict(path=str(path), bytes=len(raw), sha256=hashlib.sha256(raw).hexdigest()), raw


def _read(path, maximum=2 * 1024**2):
    pin, raw = _file(path, maximum)
    return pin, env.decode_json(raw)


def _bound(pin, maximum=2 * 1024**2):
    contract.binding(pin, max_bytes=maximum)
    return env.decode_json(files._bound(pin, cap=maximum))


def _at(pin, path, maximum=2 * 1024**2):
    _need(type(pin) is dict and pin.get("path") == str(path), "binding")
    return _bound(pin, maximum)


def _save(path, value):
    env.create_json(path, value)
    pin, saved = _read(path)
    _need(_same(saved, value), "publication")
    return pin


def _ledger(root):
    pin, value = _read(storage.DEFAULT_REGISTRY / "ledger-v1.json", 16 * 1024**2)
    storage._validate(value, storage.DEFAULT_REGISTRY)
    _need(type(value["version"]) is int and value["version"] == 2, "ledger")
    entry = storage._entry(value, root)
    env.check_binding(pin)
    return pin, entry


def _inputs(admission_pin, *, fresh=False):
    admission = contract.validate_admission(_at(admission_pin, ADMISSION))
    _need(Path(admission["root"]) == RUNTIME / "owned-v1"
          and admission["seconds"] == OWNER_SECONDS, "admission")
    guest = admission["guest"]
    proposal = _bound(guest["proposal"], 16 * 1024**2)
    authorization = _bound(guest["authorization"], 4096)
    env.validate_proposal(proposal, "run")
    env.check_authorization(authorization, "run", guest["proposal"]["sha256"])
    _need(proposal["paths"]["root"] == guest["root"]
          and proposal["memory_mib"] == guest["memory_mib"]
          and proposal["cores"] == guest["cores"]
          and proposal["max_seconds"] == guest["max_seconds"], "proposal")
    contract.revalidate_inputs(admission)
    contract.verify_current(admission)
    env.verify_prepared(proposal, initial=fresh)
    root = Path(guest["root"])
    prepared = _at(proposal["prepare_result"], root / "prepare-result-v1.json")
    _need(_same(prepared, dict(version=1, proposal_sha256=proposal["prepare_proposal"]["sha256"],
                               status="completed", closure_verified=True,
                               child_cleanup_complete=True, prepared_created=True)), "prepared")
    if fresh:
        ledger_pin, entry = _ledger(root)
        _need(entry["state"] == "prepared" and entry["reserved_bytes"] == storage.RESERVATION_BYTES
              and entry["proposal_sha256"] == proposal["prepare_proposal"]["sha256"]
              and entry["closure"] is None and entry["recovery"] is None
              and entry["retirement"] is None, "prepared")
        _need(not os.path.lexists(admission["root"]) and not os.path.lexists(root / contract.BOOT_CLAIM_FILE),
              "already_used")
        env.check_binding(ledger_pin)
    for pin in (admission_pin, guest["proposal"], guest["authorization"]):
        env.check_binding(pin)
    return admission


def _identity(pid, expected=None):
    handles = process.ProcessHandles(owner_mechanisms._ProcessApi())
    try:
        _, value = handles.add(pid, expected)
        return value
    finally:
        _need(handles.close() is True, "identity_close")


def _known_terminal(value):
    return (type(value) is dict and set(value) == TERMINAL_KEYS and value["status"] == "child_exited"
            and type(value["worker_returncode"]) is int and value["cleanup_complete"] is True
            and value["output_capture_complete"] is True
            and all(type(value[key]) is int and 0 <= value[key] <= 2**63-1
                    for key in ("elapsed_ms", "stdout_bytes", "stderr_bytes"))
            and value["stdout_bytes"] + value["stderr_bytes"] <= process.CAP)


def _capture_pins(root):
    pins = {name: _file(root / ("owner-" + name + "-v1.bin"), process.CAP)[0]
            for name in ("stdout", "stderr")}
    _need(sum(pin["bytes"] for pin in pins.values()) <= process.CAP, "capture")
    return pins


def _verify_closure(admission_pin, admission, running_pin, owner_identity):
    root = Path(admission["root"])
    guest = Path(admission["guest"]["root"])
    public_pin, public = _read(root / "result-v1.json")
    contract._obj(public, ("version", "protocol", "admission", "request", "started", "worker_result",
                           "owner", "after", "qualified_target", "reason", "feature_acceptance"), "owner")
    _need(type(public["version"]) is int and public["version"] == 1 and public["protocol"] == contract.PROTOCOL
          and public["qualified_target"] is True and public["feature_acceptance"] is False
          and public["reason"] == "stop_requested" and _same(public["admission"], admission_pin), "owner")
    request = _at(public["request"], root / "request-v1.json")
    started = _at(public["started"], root / "started-v1.json")
    terminal = _at(public["owner"], root / "owner-result-v1.json")
    after = _at(public["after"], root / "after-v1.json")
    running = contract.validate_running(_at(running_pin, root / "running-v1.json"), admission, admission_pin)
    contract._obj(started, ("worker", "request"), "owner")
    contract._process(started["worker"])
    _need(_same(request["owner"], owner_identity) and _same(running["owner"], owner_identity)
          and _same(running["worker"], started["worker"]) and _same(started["request"], public["request"])
          and process._owner_ok(terminal, root / "worker-output-v1"), "owner")
    _need(_same(after, dict(admission=admission_pin, sources=admission["sources"], python=admission["python"],
                            tools=admission["server"]["tools"], owner=owner_identity,
                            process_handles_closed=True)), "owner")
    worker = verification.verify_owned_target_result(public["worker_result"], admission, admission_pin,
                                                      public["request"], started["worker"])
    _need(worker["reason"] == "stop_requested" and _same(worker["running"], running_pin)
          and set(worker["cleanup"]) == set(contract.CLEANUP_KEYS)
          and all(flag is True for flag in worker["cleanup"].values()), "cleanup")
    closure_pin, closure = _read(guest / "guest-storage-closure-v1.json")
    _need(_same(closure, dict(version=1, proposal_sha256=admission["guest"]["proposal"]["sha256"],
                              closure_verified=True, cleanup_complete=True, admission=admission_pin,
                              owner_result=public["owner"], worker_result=public["worker_result"],
                              after=public["after"])), "closure")
    ledger_pin, entry = _ledger(guest)
    _need(entry["state"] == "closed" and entry["proposal_sha256"] == closure["proposal_sha256"]
          and entry["recovery"] is None and entry["retirement"] is None
          and _same(entry["closure"], closure_pin), "ledger")
    for pin in (public_pin, running_pin, public["request"], public["started"], public["owner"],
                public["worker_result"], public["after"], closure_pin, ledger_pin):
        env.check_binding(pin)
    return dict(owner=public_pin, closure=closure_pin, ledger=ledger_pin)


def _supervise(kind, admission_pin, running_pin, seconds):
    request = _save(CONTROL / (kind + "-request-v1.json"),
                    dict(version=1, scope=SCOPE, kind=kind, admission=admission_pin,
                         running=running_pin, parent=_identity(os.getpid())))
    started_path = CONTROL / (kind + "-started-v1.json")
    capture = CONTROL / (kind + "-capture-v1")
    capture.mkdir()
    worker = None

    def on_started(child):
        nonlocal worker
        worker = _identity(child.pid)
        _need(worker["executable"] == sys.executable, "identity")
        pending = started_path.with_suffix(".pending.json")
        _save(pending, dict(request=request, worker=worker))
        pending.rename(started_path)
        return True

    terminal = env.supervise([sys.executable, "-I", "-S", "-B", str(Path(__file__)), "_" + kind],
                             BARRIER + env.encoded(request), capture, seconds, on_started)
    terminal_pin = _save(CONTROL / (kind + "-supervisor-v1.json"), terminal)
    known = False
    if worker is not None and _known_terminal(terminal):
        _, started = _read(started_path)
        pins = _capture_pins(capture)
        known = (_same(started, dict(request=request, worker=worker))
                 and all(pins[name]["bytes"] == terminal[name + "_bytes"] for name in pins))
        env.check_binding(request)
    return dict(terminal=terminal, pin=terminal_pin, worker=worker, request=request, known=known)


def _enter(kind):
    raw = sys.stdin.buffer.read(131073)
    _need(len(raw) <= 131072 and raw.startswith(BARRIER), "barrier")
    pin = env.decode_json(raw[len(BARRIER):])
    request = _at(pin, CONTROL / (kind + "-request-v1.json"))
    contract._obj(request, ("version", "scope", "kind", "admission", "running", "parent"), "request")
    _need(type(request["version"]) is int and request["version"] == 1 and request["scope"] == SCOPE
          and request["kind"] == kind and os.getppid() == request["parent"]["pid"], "request")
    _identity(os.getppid(), request["parent"])
    started_path = CONTROL / (kind + "-started-v1.json")
    until = time.monotonic() + 5
    while not os.path.lexists(started_path):
        _need(time.monotonic() < until, "started_timeout")
        time.sleep(.02)
    _, started = _read(started_path)
    contract._obj(started, ("request", "worker"), "request")
    _need(_same(started["request"], pin), "request")
    _identity(os.getpid(), started["worker"])
    return request


def _stop(observer, root, admission_pin):
    value = dict(version=1, protocol=contract.PROTOCOL, admission_sha256=admission_pin["sha256"], action="stop")
    contract.check_stop(value, admission_pin["sha256"])
    observer.guard(min_seconds=5)
    pending = root / "stop.pending-v1.json"
    _save(pending, value)
    observer.guard(min_seconds=5)
    pending.rename(root / "stop-v1.json")


def _reason(error):
    return "cancelled" if isinstance(error, KeyboardInterrupt) else "activation_refused"


def _run_owned(admission_pin, admission, until):
    root = Path(admission["root"])
    result = dict(admission=admission_pin, passed=False, controller=None, closure=None,
                  controller_supervisor=None, owner_terminal=None, feature_acceptance=False)
    child = capture = observer = controller_job = owner_identity = running_pin = None
    stop = observer_closed = capture_closed = False
    exit_code = None
    dispatch_error = None
    try:
        _need(time.monotonic() < until, "deadline")
        capture = process.ServerCapture(CONTROL / "owner-console-v1")
        child = subprocess.Popen([sys.executable, "-I", "-S", "-B", str(ROOT / "benchmarks" / contract.OWNER_SCRIPT),
                                  "--admission", admission_pin["path"], "--admission-sha256", admission_pin["sha256"]],
                                 stdin=subprocess.DEVNULL, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                                 bufsize=0, creationflags=subprocess.CREATE_NO_WINDOW)
        capture.start(child)
        owner_identity = _identity(child.pid)
        _need(owner_identity["executable"] == admission["python"]["executable"]["path"], "identity")
        _save(CONTROL / "owner-started-v1.json", dict(admission=admission_pin, owner=owner_identity))
        path = root / "running-v1.json"
        ready_until = min(until, time.monotonic() + 400)
        while not os.path.lexists(path):
            _need(child.poll() is None and time.monotonic() < ready_until, "owner_not_ready")
            capture.guard()
            time.sleep(.1)
        capture.guard()
        running_pin, descriptor = _read(path)
        running = contract.validate_running(descriptor, admission, admission_pin)
        _need(_same(running["owner"], owner_identity) and time.monotonic() + controller.SECONDS < until, "owner")
        observer = LiveOwnedRecordLargeTextUiTarget(admission_pin, running_pin)
        observer.guard(min_seconds=controller.SECONDS)
        _need(time.monotonic() + controller.SECONDS < until, "deadline")
        controller_job = _supervise("controller", admission_pin, running_pin, controller.SECONDS)
        result["controller_supervisor"] = controller_job["pin"]
    except BaseException as error:
        dispatch_error = _reason(error)
    finally:
        if observer is not None:
            if controller_job is not None and controller_job["known"]:
                try:
                    _stop(observer, root, admission_pin)
                    stop = True
                except BaseException:
                    dispatch_error = dispatch_error or "stop_refused"
            try:
                observer_closed = observer.close() is True
            except BaseException:
                pass
        if child is not None:
            try:
                exit_code = child.poll()
                while exit_code is None and time.monotonic() < until:
                    time.sleep(.1)
                    exit_code = child.poll()
            except BaseException:
                exit_code = None
        if capture is not None:
            try:
                capture_closed = capture.close() is True
            except BaseException:
                pass

    captures = None
    if capture_closed:
        try:
            captures = _capture_pins(CONTROL / "owner-console-v1")
        except BaseException as error:
            capture_closed = False
            dispatch_error = dispatch_error or _reason(error)
    result["owner_terminal"] = _save(CONTROL / "owner-terminal-v1.json",
        dict(owner=owner_identity, returncode=exit_code, observer_closed=observer_closed,
             capture_closed=capture_closed, captures=captures, stop_published=stop))
    try:
        _need(dispatch_error is None and stop and observer_closed and capture_closed
              and type(exit_code) is int and exit_code == 0, "owner_terminal")
        result["closure"] = _verify_closure(admission_pin, admission, running_pin, owner_identity)
        _need(controller_job["known"] and process._owner_ok(controller_job["terminal"],
              CONTROL / "controller-capture-v1"), "controller_terminal")
        controller_pin, _ = _read(root / "controller-v1/controller-result-v1.json")
        verified = controller.verify_controller_result(controller_pin, admission_pin, running_pin, controller_job["worker"])
        _need(verified["outcome"] == "completed" and _same(_inputs(admission_pin), admission)
              and time.monotonic() < until, "controller")
        for pin in (controller_pin, controller_job["pin"], result["owner_terminal"],
                    *captures.values(), *result["closure"].values()):
            env.check_binding(pin)
        result.update(passed=True, controller=controller_pin)
    except BaseException as error:
        result.update(passed=False, reason=dispatch_error or _reason(error))
    return result


def execute(admission_pin):
    """Start only an admitted prepared SDK19 run under the existing Windows job."""
    _need(os.name == "nt" and Path.cwd() == ROOT and ROOT.resolve(strict=True) == ROOT
          and all(Path(os.environ.get(name, "")) == Path("D:/Dev/_Temp")
                  for name in ("TEMP", "TMP", "TMPDIR")), "environment")
    admission = _inputs(admission_pin, fresh=True)
    env.safe_path(CONTROL, exists=False)
    CONTROL.mkdir()
    result = dict(version=1, scope=SCOPE, admission=admission_pin, passed=False,
                  supervisor=None, runtime=None, feature_acceptance=False)
    try:
        job = _supervise("runtime", admission_pin, None, OUTER_SECONDS)
        result["supervisor"] = job["pin"]
        _need(job["known"] and process._owner_ok(job["terminal"], CONTROL / "runtime-capture-v1"), "runtime")
        runtime_pin, runtime = _read(CONTROL / "runtime-result-v1.json")
        _need(runtime["passed"] is True and runtime["feature_acceptance"] is False
              and _same(runtime["worker"], job["worker"]) and _same(runtime["admission"], admission_pin)
              and _same(runtime["request"], job["request"])
              and _same(_inputs(admission_pin), admission), "runtime")
        for pin in (runtime_pin, job["pin"], job["request"], runtime["controller"], *runtime["closure"].values()):
            env.check_binding(pin)
        result.update(passed=True, runtime=runtime_pin)
    except BaseException as error:
        result.update(passed=False, reason=_reason(error))
    _save(CONTROL / "activation-result-v1.json", result)
    return result


def main(argv=None):
    args = sys.argv[1:] if argv is None else argv
    try:
        if args == ["_runtime"]:
            begin = time.monotonic()
            request = _enter("runtime")
            _need(request["running"] is None, "request")
            admission = _inputs(request["admission"], fresh=True)
            result = _run_owned(request["admission"], admission, begin + OUTER_SECONDS - 10)
            result["worker"] = _identity(os.getpid())
            result["request"] = _read(CONTROL / "runtime-request-v1.json")[0]
            _save(CONTROL / "runtime-result-v1.json", result)
            return 0 if result["passed"] else 1
        if args == ["_controller"]:
            request = _enter("controller")
            _inputs(request["admission"])
            result = controller.run(request["admission"], request["running"])
            return 0 if result["outcome"] == "completed" else 1
        if len(args) == 2 and args[0] == "--admission-sha256" and re.fullmatch("[0-9a-f]{64}", args[1]):
            pin, _ = _read(ADMISSION)
            _need(pin["sha256"] == args[1], "binding")
            return 0 if execute(pin)["passed"] else 1
    except BaseException:
        pass
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
