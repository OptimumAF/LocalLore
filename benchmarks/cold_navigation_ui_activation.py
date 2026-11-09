"""One supervised cold-navigation controller on an approved prepared guest.

Copyright 2026 LocalLore contributors. SPDX-License-Identifier: Apache-2.0
"""
import hashlib
import os
from pathlib import Path
import subprocess
import sys
import time

ROOT = Path(__file__).resolve().parents[1]
if __package__ in (None, ""):
    sys.path.insert(0, str(ROOT))

from benchmarks import archive_ui_build as files
from benchmarks import cold_navigation_ui_controller as controller
from benchmarks import isolated_adb_owner as process
from benchmarks import owned_cold_navigation_ui_owner as owner
from benchmarks import receipt_avd_environment as env
from benchmarks.cold_navigation_ui_closure import verify_closure
from benchmarks.owned_cold_navigation_ui_client import LiveOwnedColdNavigationUiTarget

CONTROL = owner.ATTEMPT_ROOT / "activation-v1"
SCOPE = "cold-navigation-activation-v1"
BARRIER = b"cold-navigation-activation-v1\n"
NS = owner.NS
TAIL_SECONDS = owner.TAIL_SECONDS
READY_SECONDS = 400
REQUEST_KEYS = ("version", "scope", "kind", "admission", "authority", "attempt",
                "began_ns", "until_ns", "running", "parent")
RUNTIME_KEYS = ("admission", "running", "owner_started", "owner_terminal",
                "controller_supervisor", "controller", "closure", "passed", "reason",
                "feature_acceptance", "request", "worker", "handoff")
contract = owner.contract
_need = env.require
_same = contract._same
_read = owner._read
_identity = owner._identity


def _save(path, value):
    env.create_json(path, value)
    pin, actual = _read(path)
    _need(_same(actual, value), "publication")
    return pin


def _capture_pins(root):
    remaining = process.CAP
    pins = {}
    for name in ("stdout", "stderr"):
        path = root / ("owner-" + name + "-v1.bin")
        raw = files._read(path, remaining)
        pins[name] = dict(path=str(path), bytes=len(raw), sha256=hashlib.sha256(raw).hexdigest())
        remaining -= len(raw)
    return pins


def _inputs(admission_pin, authority_pin, attempt_pin):
    admission = contract.validate_admission(owner._at(admission_pin, owner.ADMISSION))
    owner._check_boot_records(admission_pin, admission, authority_pin, attempt_pin, initial=False)
    contract.revalidate_inputs(admission)
    return admission


def _capture_dir(kind):
    return CONTROL / (kind + "-capture-v1")


def _request_path(kind):
    return CONTROL / (kind + "-request-v1.json")


def _started_path(kind):
    return CONTROL / (kind + "-started-v1.json")


def _terminal_path(kind):
    return CONTROL / (kind + "-supervisor-v1.json")


def _job_evidence(kind, terminal_pin):
    terminal = owner._at(terminal_pin, _terminal_path(kind))
    contract._obj(terminal, ("status", "worker_returncode", "cleanup_complete", "output_capture_complete",
                             "elapsed_ms", "stdout_bytes", "stderr_bytes"), "terminal")
    _need(terminal["status"] == "child_exited" and type(terminal["worker_returncode"]) is int
          and terminal["cleanup_complete"] is True and terminal["output_capture_complete"] is True
          and all(type(terminal[key]) is int and 0 <= terminal[key] <= 2**63-1
                  for key in ("elapsed_ms", "stdout_bytes", "stderr_bytes")), "terminal")
    request_pin, request = _read(_request_path(kind))
    started_pin, started = _read(_started_path(kind))
    contract._obj(started, ("request", "worker"), "identity")
    contract._process(started["worker"])
    _need(_same(started["request"], request_pin), "identity")
    captures = _capture_pins(_capture_dir(kind))
    for channel, pin in captures.items():
        _need(pin["bytes"] == terminal[channel + "_bytes"], "capture")
    for pin in (request_pin, started_pin, terminal_pin, *captures.values()):
        env.check_binding(pin)
    return terminal, request_pin, request, started["worker"]


def _supervise(kind, admission_pin, authority_pin, attempt_pin, began_ns, until_ns, *, running_pin=None):
    now = owner.check_window(began_ns, until_ns)
    limit = env.SUPERVISOR_MAX_SECONDS if kind == "runtime" else controller.SECONDS
    seconds = min(limit, (until_ns - now) // NS)
    _need(seconds > 0, "deadline")
    parent = _identity(os.getpid())
    request = _save(_request_path(kind), dict(
        version=1, scope=SCOPE, kind=kind, admission=admission_pin, authority=authority_pin,
        attempt=attempt_pin, began_ns=began_ns, until_ns=until_ns, running=running_pin, parent=parent,
    ))
    capture = env.safe_path(_capture_dir(kind), exists=False)
    capture.mkdir(exist_ok=False)
    worker = None

    def started(child):
        nonlocal worker
        worker = _identity(child.pid)
        _need(worker["executable"] == parent["executable"], "identity")
        path = _started_path(kind)
        pending = path.with_suffix(".pending.json")
        _save(pending, dict(request=request, worker=worker))
        pending.rename(path)
        return True

    # Recompute after setup. The outer runtime job owns all its descendants.
    remaining = (until_ns - owner.check_window(began_ns, until_ns)) // NS
    seconds = min(seconds, remaining)
    _need(seconds > 0, "deadline")
    terminal = env.supervise([sys.executable, "-I", "-S", "-B", str(Path(__file__)), "_" + kind],
                             BARRIER + env.encoded(request), capture, seconds, started)
    pin = _save(_terminal_path(kind), terminal)
    known = False
    try:
        actual, request_pin, _, identified = _job_evidence(kind, pin)
        known = _same(actual, terminal) and _same(request_pin, request) and _same(identified, worker)
    except Exception:
        pass
    return dict(terminal=terminal, pin=pin, worker=worker, request=request, known=known)


def _enter(kind):
    raw = sys.stdin.buffer.read(131073)
    _need(len(raw) <= 131072 and raw.startswith(BARRIER), "barrier")
    pin = env.decode_json(raw[len(BARRIER):])
    request = owner._at(pin, _request_path(kind))
    contract._obj(request, REQUEST_KEYS, "request")
    contract._process(request["parent"])
    _need(_same(request["version"], 1) and request["scope"] == SCOPE and request["kind"] == kind
          and request["parent"]["pid"] == os.getppid(), "request")
    _identity(os.getppid(), request["parent"])
    now = owner.check_window(request["began_ns"], request["until_ns"])
    wait_until = min(request["until_ns"], now + 5 * NS)
    path = _started_path(kind)
    while not os.path.lexists(path):
        _need(time.monotonic_ns() < wait_until, "identity")
        time.sleep(.02)
    started_pin, started = _read(path)
    contract._obj(started, ("request", "worker"), "identity")
    _need(_same(started["request"], pin), "request")
    worker = _identity(os.getpid(), started["worker"])
    _need(os.getpid() in owner.mechanisms._ProcessApi().current_job_pids(), "job")
    env.check_binding(started_pin)
    env.check_binding(pin)
    owner.check_window(request["began_ns"], request["until_ns"])
    return pin, request, worker


def _stop(observer, root, admission_pin):
    value = dict(version=1, protocol=contract.PROTOCOL, admission_sha256=admission_pin["sha256"], action="stop")
    contract.check_stop(value, admission_pin["sha256"])
    observer.guard(min_seconds=5)
    pending = root / "stop.pending-v1.json"
    _save(pending, value)
    observer.guard(min_seconds=5)
    pending.rename(root / "stop-v1.json")


def _reason(error):
    if isinstance(error, KeyboardInterrupt):
        return "cancelled"
    if type(error) is env.EnvironmentRefused and str(error) in {
        "deadline", "owner_not_ready", "identity", "owner_terminal", "controller_terminal", "binding", "handoff",
    }:
        return str(error)
    return "activation_refused"


def _run_owned(admission_pin, admission, until_ns, *, began_ns, handoff_pin):
    root = Path(admission["root"])
    result = dict(admission=admission_pin, running=None, owner_started=None, owner_terminal=None,
                  controller_supervisor=None, controller=None, closure=None, passed=False,
                  reason=None, feature_acceptance=False)
    child = capture = observer = job = identity = running_pin = None
    stop = observer_closed = capture_closed = False
    code = None
    failure = None
    try:
        owner.check_launch_window(began_ns, until_ns)
        actual, handoff = _read(owner.HANDOFF)
        _need(_same(actual, handoff_pin), "handoff")
        capture = process.ServerCapture(CONTROL / "owner-console-v1")
        child_env = dict(os.environ, **{owner.HANDOFF_ENV: handoff_pin["sha256"]})
        env.check_binding(handoff_pin)
        owner.check_launch_window(began_ns, until_ns)
        child = subprocess.Popen([sys.executable, "-I", "-S", "-B", str(ROOT / "benchmarks" / contract.OWNER_SCRIPT),
                                  "--admission", admission_pin["path"], "--admission-sha256", admission_pin["sha256"]],
                                 stdin=subprocess.DEVNULL, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                                 bufsize=0, env=child_env, creationflags=subprocess.CREATE_NO_WINDOW)
        capture.start(child)
        identity = _identity(child.pid)
        _need(identity["executable"] == admission["python"]["executable"]["path"], "identity")
        result["owner_started"] = _save(CONTROL / "owner-started-v1.json",
                                        dict(admission=admission_pin, owner=identity))
        path = root / "running-v1.json"
        ready_until = min(until_ns - (controller.SECONDS + TAIL_SECONDS) * NS,
                          time.monotonic_ns() + READY_SECONDS * NS)
        while not os.path.lexists(path):
            _need(child.poll() is None and time.monotonic_ns() < ready_until, "owner_not_ready")
            capture.guard()
            time.sleep(.1)
        capture.guard()
        _need(child.poll() is None and time.monotonic_ns() < ready_until, "owner_not_ready")
        running_pin, value = _read(path)
        running = contract.validate_running(value, admission, admission_pin)
        _need(_same(running["owner"], identity), "identity")
        result["running"] = running_pin
        observer = LiveOwnedColdNavigationUiTarget(admission_pin, running_pin)
        observer.guard(min_seconds=controller.SECONDS + TAIL_SECONDS)
        env.check_binding(handoff_pin)
        owner.check_launch_window(began_ns, until_ns)
        job = _supervise("controller", admission_pin, handoff["authority"], handoff["attempt"],
                         began_ns, until_ns, running_pin=running_pin)
        result["controller_supervisor"] = job["pin"]
    except BaseException as error:
        failure = _reason(error)
    finally:
        if observer is not None:
            if job is not None and job["known"]:
                try:
                    _stop(observer, root, admission_pin)
                    stop = True
                except BaseException:
                    failure = failure or "stop_refused"
            try:
                observer_closed = observer.close() is True
            except BaseException:
                pass
        if child is not None:
            try:
                code = child.poll()
                while stop and code is None and time.monotonic_ns() < until_ns:
                    time.sleep(.1)
                    code = child.poll()
            except BaseException:
                code = None
        captures = None
        if capture is not None:
            try:
                capture_closed = capture.close() is True
                if capture_closed:
                    captures = _capture_pins(CONTROL / "owner-console-v1")
            except BaseException:
                capture_closed = False
        result["owner_terminal"] = _save(CONTROL / "owner-terminal-v1.json", dict(
            owner=identity, returncode=code, observer_closed=observer_closed,
            capture_closed=capture_closed, captures=captures, stop_published=stop,
        ))

    try:
        controller_path = root / "controller-v1" / controller.RESULT_FILE
        if job is not None and job["known"] and os.path.lexists(controller_path):
            result["controller"] = _read(controller_path)[0]
        _need(stop and observer_closed and capture_closed and type(code) is int and code == 0,
              "owner_terminal")
        result["closure"] = verify_closure(admission_pin, admission, running_pin, identity)
        _need(failure is None and job["known"] and process._owner_ok(job["terminal"], _capture_dir("controller")),
              "controller_terminal")
        _need(result["controller"] is not None, "controller_terminal")
        controller.verify_controller_result(result["controller"], admission_pin, running_pin, job["worker"])
        owner.check_window(began_ns, until_ns)
        result["passed"] = True
    except BaseException as error:
        result["reason"] = failure or _reason(error)
    return result


def _verify_runtime(runtime_pin, job, admission, admission_pin, authority_pin, attempt_pin, began_ns, until_ns):
    runtime = owner._at(runtime_pin, CONTROL / "runtime-result-v1.json")
    contract._obj(runtime, RUNTIME_KEYS, "runtime")
    _need(runtime["passed"] is True and runtime["reason"] is None and runtime["feature_acceptance"] is False
          and _same(runtime["request"], job["request"]) and _same(runtime["worker"], job["worker"])
          and _same(runtime["admission"], admission_pin), "runtime")
    handoff_pin, handoff = owner._read_handoff(admission_pin, live=False)
    _need(_same(runtime["handoff"], handoff_pin) and _same(handoff["supervisor"], job["worker"])
          and _same(handoff["authority"], authority_pin) and _same(handoff["attempt"], attempt_pin)
          and _same(handoff["began_ns"], began_ns) and _same(handoff["until_ns"], until_ns), "handoff")
    started = owner._at(runtime["owner_started"], CONTROL / "owner-started-v1.json")
    contract._obj(started, ("admission", "owner"), "identity")
    contract._process(started["owner"])
    _need(_same(started["admission"], admission_pin), "identity")
    terminal = owner._at(runtime["owner_terminal"], CONTROL / "owner-terminal-v1.json")
    contract._obj(terminal, ("owner", "returncode", "observer_closed", "capture_closed", "captures",
                            "stop_published"), "terminal")
    _need(_same(terminal["owner"], started["owner"]) and _same(terminal["returncode"], 0)
          and all(terminal[key] is True for key in ("observer_closed", "capture_closed", "stop_published"))
          and _same(terminal["captures"], _capture_pins(CONTROL / "owner-console-v1")), "terminal")
    controller_terminal, _, request, worker = _job_evidence("controller", runtime["controller_supervisor"])
    _need(process._owner_ok(controller_terminal, _capture_dir("controller")), "controller_terminal")
    _need(_same(request, dict(version=1, scope=SCOPE, kind="controller", admission=admission_pin,
                              authority=authority_pin, attempt=attempt_pin, began_ns=began_ns, until_ns=until_ns,
                              running=runtime["running"], parent=runtime["worker"])), "request")
    controller.verify_controller_result(runtime["controller"], admission_pin, runtime["running"], worker)
    _need(_same(runtime["closure"], verify_closure(admission_pin, admission, runtime["running"], started["owner"])),
          "closure")
    for pin in (runtime_pin, handoff_pin, runtime["owner_started"], runtime["owner_terminal"], runtime["controller_supervisor"],
                runtime["controller"], *terminal["captures"].values(), *runtime["closure"].values()):
        env.check_binding(pin)
    return runtime


def verify_result(pin, admission_pin, authority_pin, attempt_pin, *, began_ns, expected_parent):
    """Replay the completed activation inside the enclosing operation."""
    value = owner._at(pin, CONTROL / "activation-result-v1.json")
    contract._obj(value, ("version", "scope", "admission", "authority", "attempt", "supervisor",
                          "runtime", "passed", "reason", "feature_acceptance"), "activation")
    _need(_same(value["version"], 1) and value["scope"] == SCOPE and value["passed"] is True
          and value["reason"] is None and value["feature_acceptance"] is False
          and _same(value["admission"], admission_pin) and _same(value["authority"], authority_pin)
          and _same(value["attempt"], attempt_pin), "activation")
    terminal, request_pin, request, worker = _job_evidence("runtime", value["supervisor"])
    _need(process._owner_ok(terminal, _capture_dir("runtime")), "owner_terminal")
    contract._obj(request, REQUEST_KEYS, "request")
    contract._process(request["parent"])
    _need(_same(request, dict(version=1, scope=SCOPE, kind="runtime", admission=admission_pin,
                              authority=authority_pin, attempt=attempt_pin, began_ns=began_ns,
                              until_ns=request["until_ns"], running=None, parent=expected_parent)), "request")
    owner.check_bounds(began_ns, request["until_ns"])
    admission = contract.validate_admission(owner._at(admission_pin, owner.ADMISSION))
    contract.revalidate_inputs(admission)
    runtime = _verify_runtime(value["runtime"], dict(request=request_pin, worker=worker), admission,
                              admission_pin, authority_pin, attempt_pin, began_ns, request["until_ns"])
    for bound in (pin, value["supervisor"], value["runtime"], request_pin, admission_pin):
        env.check_binding(bound)
    return runtime["closure"]


def execute(admission_pin, authority_pin, attempt_pin, *, began_ns):
    """Run activation within the outer operation's remaining approved budget."""
    _need(os.name == "nt" and Path.cwd() == ROOT
          and all(Path(os.environ.get(name, "")) == Path("D:/Dev/_Temp")
                  for name in ("TEMP", "TMP", "TMPDIR")), "environment")
    now = time.monotonic_ns()
    _need(type(began_ns) is int, "deadline")
    until_ns = min(began_ns + owner.SECONDS * NS, now + owner.ACTIVATION_SECONDS * NS) - TAIL_SECONDS * NS
    owner.check_launch_window(began_ns, until_ns)
    admission = _inputs(admission_pin, authority_pin, attempt_pin)
    _need(not any(os.path.lexists(path) for path in (CONTROL, owner.HANDOFF, owner.OWNED_ROOT)), "already_used")
    owner.check_launch_window(began_ns, until_ns)
    env.safe_path(CONTROL, exists=False).mkdir(exist_ok=False)
    result = dict(version=1, scope=SCOPE, admission=admission_pin, authority=authority_pin, attempt=attempt_pin,
                  supervisor=None, runtime=None, passed=False, reason=None, feature_acceptance=False)
    try:
        job = _supervise("runtime", admission_pin, authority_pin, attempt_pin, began_ns, until_ns)
        result["supervisor"] = job["pin"]
        runtime_path = CONTROL / "runtime-result-v1.json"
        if job["known"] and os.path.lexists(runtime_path):
            result["runtime"] = _read(runtime_path)[0]
        _need(result["runtime"] is not None and process._owner_ok(job["terminal"], _capture_dir("runtime")),
              "owner_terminal")
        _verify_runtime(result["runtime"], job, admission, admission_pin, authority_pin, attempt_pin,
                        began_ns, until_ns)
        owner._approved_plan(authority_pin, attempt_pin)
        for pin in (job["pin"], job["request"], result["runtime"], admission_pin, authority_pin, attempt_pin):
            env.check_binding(pin)
        owner.check_window(began_ns, until_ns)
        result["passed"] = True
    except BaseException as error:
        result["reason"] = _reason(error)
    _save(CONTROL / "activation-result-v1.json", result)
    return result


def main(argv=None):
    args = sys.argv[1:] if argv is None else argv
    try:
        if args == ["_runtime"]:
            request_pin, request, worker = _enter("runtime")
            _need(request["running"] is None, "request")
            admission = _inputs(request["admission"], request["authority"], request["attempt"])
            owner.check_launch_window(request["began_ns"], request["until_ns"])
            handoff = _save(owner.HANDOFF, dict(version=2, scope=owner.HANDOFF_SCOPE, authority=request["authority"],
                                      attempt=request["attempt"], admission=request["admission"], supervisor=worker,
                                      began_ns=request["began_ns"], until_ns=request["until_ns"]))
            result = _run_owned(request["admission"], admission, request["until_ns"],
                                began_ns=request["began_ns"], handoff_pin=handoff)
            _save(CONTROL / "runtime-result-v1.json", dict(result, request=request_pin, worker=worker, handoff=handoff))
            return 0 if result["passed"] else 1
        if args == ["_controller"]:
            _, request, _ = _enter("controller")
            handoff_pin, handoff = owner._read_handoff(request["admission"])
            _need(all(_same(handoff[key], request[key]) for key in ("authority", "attempt", "began_ns", "until_ns"))
                  and _same(handoff["supervisor"], request["parent"]), "handoff")
            env.check_binding(handoff_pin)
            result = controller.run(request["admission"], request["running"])
            return 0 if result["outcome"] == "completed" else 1
    except BaseException:
        pass
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
