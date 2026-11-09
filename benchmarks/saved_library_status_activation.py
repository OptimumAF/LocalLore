"""One supervised SDK23 saved-library status controller on an approved prepared guest.

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
from benchmarks import saved_library_status_controller as controller
from benchmarks import saved_library_status_handoff as handoff
from benchmarks import saved_library_status_resume_handoff as resume_handoff
from benchmarks import isolated_adb_owner as process
from benchmarks import owned_saved_library_status as contract
from benchmarks import owned_target_owner as mechanisms
from benchmarks import receipt_avd_environment as env
from benchmarks.saved_library_status_closure import verify_closure
from benchmarks.owned_saved_library_status import LiveOwnedSavedLibraryStatusTarget

CONTROL = handoff.ATTEMPT_ROOT / "activation-v1"
SCOPE = "saved-library-status-activation-v1"
BARRIER = b"saved-library-status-activation-v1\n"
RESUME_CONTROL = resume_handoff.ATTEMPT_ROOT / "activation-v1"
RESUME_SCOPE = "saved-library-status-resume-activation-v1"
RESUME_BARRIER = b"saved-library-status-resume-activation-v1\n"
NS = handoff.NS
TAIL_SECONDS = handoff.TAIL_SECONDS
READY_SECONDS = 400
OPERATION_REQUEST = handoff.ATTEMPT_ROOT / "operation-request-v1.json"
OPERATION_STARTED = handoff.ATTEMPT_ROOT / "operation-started-v1.json"
OPERATION_CLAIM = handoff.ATTEMPT_ROOT / "operation-worker-claim-v1.json"
RESUME_OPERATION_REQUEST = resume_handoff.ATTEMPT_ROOT / "operation-request-v1.json"
RESUME_OPERATION_STARTED = resume_handoff.ATTEMPT_ROOT / "operation-started-v1.json"
RESUME_OPERATION_CLAIM = resume_handoff.ATTEMPT_ROOT / "operation-worker-claim-v1.json"
REQUEST_KEYS = ("version", "scope", "kind", "admission", "authority", "attempt",
                "began_ns", "until_ns", "running", "parent")
RUNTIME_KEYS = ("admission", "running", "owner_started", "owner_terminal",
                "controller_supervisor", "controller", "closure", "passed", "reason",
                "feature_acceptance", "request", "worker", "handoff")
_need = env.require
_same = contract._same
_read = handoff.read
_save = handoff.save


def _identity(pid, expected=None):
    handles = process.ProcessHandles(mechanisms._ProcessApi())
    try:
        return handles.add(pid, expected)[1]
    finally:
        _need(handles.close() is True, "identity")


def _capture_pins(root):
    remaining = process.CAP
    pins = {}
    for name in ("stdout", "stderr"):
        path = root / ("owner-" + name + "-v1.bin")
        raw = files._read(path, remaining)
        pins[name] = dict(path=str(path), bytes=len(raw), sha256=hashlib.sha256(raw).hexdigest())
        remaining -= len(raw)
    return pins


def _inputs(admission_pin, authority_pin, attempt_pin, *, resume=False):
    if resume:
        return resume_handoff.verify_admission(admission_pin, authority_pin, attempt_pin)
    admission = contract.validate_admission(handoff.at(admission_pin, handoff.ADMISSION))
    admission, launch_inputs = handoff.verify_prepared_admission(
        admission_pin, admission, authority_pin, attempt_pin, initial=False,
    )
    contract.revalidate_inputs(admission)
    for pin in (admission_pin, authority_pin, attempt_pin, *launch_inputs):
        env.check_binding(pin)
    return admission


def _outer_worker(authority_pin, attempt_pin, began_ns, *, resume=False):
    request_pin, request = _read(RESUME_OPERATION_REQUEST if resume else OPERATION_REQUEST)
    operation_scope = resume_handoff.OPERATION_SCOPE if resume else handoff.OPERATION_SCOPE
    contract._obj(request, ("version", "scope", "authority", "attempt", "began_ns", "parent"), "request")
    parent = request["parent"]
    contract._process(parent)
    _need(_same(request, dict(version=1, scope=operation_scope, authority=authority_pin,
                              attempt=attempt_pin, began_ns=began_ns, parent=parent)), "request")
    started_pin, started = _read(RESUME_OPERATION_STARTED if resume else OPERATION_STARTED)
    claim_pin, claim = _read(RESUME_OPERATION_CLAIM if resume else OPERATION_CLAIM)
    contract._obj(claim, ("request", "worker"), "identity")
    worker = claim["worker"]
    contract._process(worker)
    _need(_same(claim, started) and _same(claim["request"], request_pin)
          and worker["executable"] == parent["executable"] and worker["pid"] != parent["pid"]
          and worker["creation_filetime"] >= parent["creation_filetime"], "identity")
    for pin in (request_pin, started_pin, claim_pin):
        env.check_binding(pin)
    return worker, parent


def _live_outer_worker(authority_pin, attempt_pin, began_ns, *, resume=False):
    worker, parent = _outer_worker(authority_pin, attempt_pin, began_ns, **_resume_options(resume))
    pid = os.getpid()
    _need(os.getppid() == parent["pid"] and pid == worker["pid"], "identity")
    _identity(parent["pid"], parent)
    _identity(pid, worker)
    _need(pid in mechanisms._ProcessApi().current_job_pids(), "job")


def _resume_options(resume):
    return {"resume": True} if resume else {}


def _control(resume):
    return RESUME_CONTROL if resume else CONTROL


def _capture_dir(kind, *, resume=False):
    return _control(resume) / (kind + "-capture-v1")


def _request_path(kind, *, resume=False):
    return _control(resume) / (kind + "-request-v1.json")


def _started_path(kind, *, resume=False):
    return _control(resume) / (kind + "-started-v1.json")


def _terminal_path(kind, *, resume=False):
    return _control(resume) / (kind + "-supervisor-v1.json")


def _job_evidence(kind, terminal_pin, *, resume=False):
    options = _resume_options(resume)
    terminal = handoff.at(terminal_pin, _terminal_path(kind, **options))
    contract._obj(terminal, ("status", "worker_returncode", "cleanup_complete", "output_capture_complete",
                             "elapsed_ms", "stdout_bytes", "stderr_bytes"), "terminal")
    _need(terminal["status"] == "child_exited" and type(terminal["worker_returncode"]) is int
          and terminal["cleanup_complete"] is True and terminal["output_capture_complete"] is True
          and all(type(terminal[key]) is int and 0 <= terminal[key] <= 2**63-1
                  for key in ("elapsed_ms", "stdout_bytes", "stderr_bytes")), "terminal")
    request_pin, request = _read(_request_path(kind, **options))
    started_pin, started = _read(_started_path(kind, **options))
    contract._obj(started, ("request", "worker"), "identity")
    contract._process(started["worker"])
    _need(_same(started["request"], request_pin), "identity")
    captures = _capture_pins(_capture_dir(kind, **options))
    for channel, pin in captures.items():
        _need(pin["bytes"] == terminal[channel + "_bytes"], "capture")
    for pin in (request_pin, started_pin, terminal_pin, *captures.values()):
        env.check_binding(pin)
    return terminal, request_pin, request, started["worker"]


def _supervise(kind, admission_pin, authority_pin, attempt_pin, began_ns, until_ns, *, running_pin=None, resume=False):
    options = _resume_options(resume)
    scope = RESUME_SCOPE if resume else SCOPE
    barrier = RESUME_BARRIER if resume else BARRIER
    worker_arg = ("_resume_" if resume else "_") + kind
    now = handoff.check_window(began_ns, until_ns)
    limit = env.SUPERVISOR_MAX_SECONDS if kind == "runtime" else controller.SECONDS
    seconds = min(limit, (until_ns - now) // NS)
    _need(seconds > 0, "deadline")
    parent = _identity(os.getpid())
    request = _save(_request_path(kind, **options), dict(
        version=1, scope=scope, kind=kind, admission=admission_pin, authority=authority_pin,
        attempt=attempt_pin, began_ns=began_ns, until_ns=until_ns, running=running_pin, parent=parent,
    ))
    capture = env.safe_path(_capture_dir(kind, **options), exists=False)
    capture.mkdir(exist_ok=False)
    worker = None

    def started(child):
        nonlocal worker
        worker = _identity(child.pid)
        _need(worker["executable"] == parent["executable"], "identity")
        path = _started_path(kind, **options)
        pending = path.with_suffix(".pending.json")
        _save(pending, dict(request=request, worker=worker))
        pending.rename(path)
        return True

    # Recompute after setup. The outer runtime job owns all its descendants.
    remaining = (until_ns - handoff.check_window(began_ns, until_ns)) // NS
    seconds = min(seconds, remaining)
    _need(seconds > 0, "deadline")
    terminal = env.supervise([sys.executable, "-I", "-S", "-B", str(Path(__file__)), worker_arg],
                             barrier + env.encoded(request), capture, seconds, started)
    pin = _save(_terminal_path(kind, **options), terminal)
    known = False
    try:
        actual, request_pin, _, identified = _job_evidence(kind, pin, **options)
        known = _same(actual, terminal) and _same(request_pin, request) and _same(identified, worker)
    except Exception:
        pass
    return dict(terminal=terminal, pin=pin, worker=worker, request=request, known=known)


def _enter(kind, *, resume=False):
    options = _resume_options(resume)
    scope = RESUME_SCOPE if resume else SCOPE
    barrier = RESUME_BARRIER if resume else BARRIER
    raw = sys.stdin.buffer.read(131073)
    _need(len(raw) <= 131072 and raw.startswith(barrier), "barrier")
    pin = env.decode_json(raw[len(barrier):])
    request = handoff.at(pin, _request_path(kind, **options))
    contract._obj(request, REQUEST_KEYS, "request")
    contract._process(request["parent"])
    _need(_same(request["version"], 1) and request["scope"] == scope and request["kind"] == kind
          and request["parent"]["pid"] == os.getppid(), "request")
    _identity(os.getppid(), request["parent"])
    now = handoff.check_window(request["began_ns"], request["until_ns"])
    wait_until = min(request["until_ns"], now + 5 * NS)
    path = _started_path(kind, **options)
    while not os.path.lexists(path):
        _need(time.monotonic_ns() < wait_until, "identity")
        time.sleep(.02)
    started_pin, started = _read(path)
    contract._obj(started, ("request", "worker"), "identity")
    _need(_same(started["request"], pin), "request")
    worker = _identity(os.getpid(), started["worker"])
    _need(os.getpid() in mechanisms._ProcessApi().current_job_pids(), "job")
    env.check_binding(started_pin)
    env.check_binding(pin)
    handoff.check_window(request["began_ns"], request["until_ns"])
    return pin, request, worker


def _stop(observer, root, admission_pin, *, resume=False):
    selected = resume_handoff if resume else handoff
    _need(root == selected.OWNED_ROOT, "identity")
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


def _run_owned(admission_pin, admission, until_ns, *, began_ns, handoff_pin, resume=False):
    options = _resume_options(resume)
    selected = resume_handoff if resume else handoff
    control = _control(resume)
    root = Path(admission["root"])
    result = dict(admission=admission_pin, running=None, owner_started=None, owner_terminal=None,
                  controller_supervisor=None, controller=None, closure=None, passed=False,
                  reason=None, feature_acceptance=False)
    child = capture = observer = job = identity = running_pin = None
    stop = observer_closed = capture_closed = False
    code = None
    failure = None
    try:
        handoff.check_launch_window(began_ns, until_ns)
        actual, handoff_record = _read(selected.HANDOFF)
        _need(_same(actual, handoff_pin), "handoff")
        capture = process.ServerCapture(control / "owner-console-v1")
        child_env = dict(os.environ)
        child_env.pop(handoff.HANDOFF_ENV, None)
        child_env.pop(contract.RESUME_HANDOFF_ENV, None)
        proof_key = contract.RESUME_HANDOFF_ENV if resume else handoff.HANDOFF_ENV
        child_env[proof_key] = handoff_pin["sha256"]
        env.check_binding(handoff_pin)
        handoff.check_launch_window(began_ns, until_ns)
        child = subprocess.Popen([sys.executable, "-I", "-S", "-B", str(ROOT / "benchmarks" / contract.OWNER_SCRIPT),
                                  "--admission", admission_pin["path"], "--admission-sha256", admission_pin["sha256"]],
                                 stdin=subprocess.DEVNULL, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                                 bufsize=0, env=child_env, creationflags=subprocess.CREATE_NO_WINDOW)
        capture.start(child)
        identity = _identity(child.pid)
        _need(identity["executable"] == admission["python"]["executable"]["path"], "identity")
        result["owner_started"] = _save(control / "owner-started-v1.json",
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
        observer = LiveOwnedSavedLibraryStatusTarget(admission_pin, running_pin)
        observer.guard(min_seconds=controller.SECONDS + TAIL_SECONDS)
        env.check_binding(handoff_pin)
        handoff.check_launch_window(began_ns, until_ns)
        job = _supervise("controller", admission_pin, handoff_record["authority"], handoff_record["attempt"],
                         began_ns, until_ns, running_pin=running_pin, **options)
        result["controller_supervisor"] = job["pin"]
    except BaseException as error:
        failure = _reason(error)
    finally:
        if observer is not None:
            if job is not None and job["known"]:
                try:
                    _stop(observer, root, admission_pin, **options)
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
                    captures = _capture_pins(control / "owner-console-v1")
            except BaseException:
                capture_closed = False
        result["owner_terminal"] = _save(control / "owner-terminal-v1.json", dict(
            owner=identity, returncode=code, observer_closed=observer_closed,
            capture_closed=capture_closed, captures=captures, stop_published=stop,
        ))

    try:
        controller_path = root / "controller-v1" / controller.RESULT_FILE
        if job is not None and job["known"] and os.path.lexists(controller_path):
            result["controller"] = _read(controller_path)[0]
        _need(stop and observer_closed and capture_closed and type(code) is int and code == 0,
              "owner_terminal")
        result["closure"] = verify_closure(admission_pin, admission, running_pin, identity, **options)
        _need(failure is None and job["known"] and
              process._owner_ok(job["terminal"], _capture_dir("controller", **options)),
              "controller_terminal")
        _need(result["controller"] is not None, "controller_terminal")
        controller.verify_controller_result(result["controller"], admission_pin, running_pin, job["worker"])
        handoff.check_window(began_ns, until_ns)
        result["passed"] = True
    except BaseException as error:
        result["reason"] = failure or _reason(error)
    return result


def _verify_runtime(runtime_pin, job, admission, admission_pin, authority_pin, attempt_pin, began_ns, until_ns,
                    *, resume=False):
    options = _resume_options(resume)
    selected = resume_handoff if resume else handoff
    control = _control(resume)
    scope = RESUME_SCOPE if resume else SCOPE
    runtime = handoff.at(runtime_pin, control / "runtime-result-v1.json")
    contract._obj(runtime, RUNTIME_KEYS, "runtime")
    _need(runtime["passed"] is True and runtime["reason"] is None and runtime["feature_acceptance"] is False
          and _same(runtime["request"], job["request"]) and _same(runtime["worker"], job["worker"])
          and _same(runtime["admission"], admission_pin), "runtime")
    handoff_pin, handoff_record = selected.read_handoff(admission_pin, live=False)
    _need(_same(runtime["handoff"], handoff_pin) and _same(handoff_record["supervisor"], job["worker"])
          and _same(handoff_record["authority"], authority_pin) and _same(handoff_record["attempt"], attempt_pin)
          and _same(handoff_record["began_ns"], began_ns) and _same(handoff_record["until_ns"], until_ns), "handoff")
    started = handoff.at(runtime["owner_started"], control / "owner-started-v1.json")
    contract._obj(started, ("admission", "owner"), "identity")
    contract._process(started["owner"])
    _need(_same(started["admission"], admission_pin), "identity")
    terminal = handoff.at(runtime["owner_terminal"], control / "owner-terminal-v1.json")
    contract._obj(terminal, ("owner", "returncode", "observer_closed", "capture_closed", "captures",
                            "stop_published"), "terminal")
    _need(_same(terminal["owner"], started["owner"]) and _same(terminal["returncode"], 0)
          and all(terminal[key] is True for key in ("observer_closed", "capture_closed", "stop_published"))
          and _same(terminal["captures"], _capture_pins(control / "owner-console-v1")), "terminal")
    controller_terminal, _, request, worker = _job_evidence("controller", runtime["controller_supervisor"], **options)
    _need(process._owner_ok(controller_terminal, _capture_dir("controller", **options)), "controller_terminal")
    _need(_same(request, dict(version=1, scope=scope, kind="controller", admission=admission_pin,
                              authority=authority_pin, attempt=attempt_pin, began_ns=began_ns, until_ns=until_ns,
                              running=runtime["running"], parent=runtime["worker"])), "request")
    controller.verify_controller_result(runtime["controller"], admission_pin, runtime["running"], worker)
    _need(_same(runtime["closure"], verify_closure(admission_pin, admission, runtime["running"],
                                                  started["owner"], **options)), "closure")
    for pin in (runtime_pin, handoff_pin, runtime["owner_started"], runtime["owner_terminal"], runtime["controller_supervisor"],
                runtime["controller"], *terminal["captures"].values(), *runtime["closure"].values()):
        env.check_binding(pin)
    return runtime


def verify_result(pin, admission_pin, authority_pin, attempt_pin, *, began_ns, expected_parent, resume=False):
    """Replay the completed activation inside the enclosing operation."""
    options = _resume_options(resume)
    selected = resume_handoff if resume else handoff
    scope = RESUME_SCOPE if resume else SCOPE
    value = handoff.at(pin, _control(resume) / "activation-result-v1.json")
    contract._obj(value, ("version", "scope", "admission", "authority", "attempt", "supervisor",
                          "runtime", "passed", "reason", "feature_acceptance"), "activation")
    _need(_same(value["version"], 1) and value["scope"] == scope and value["passed"] is True
          and value["reason"] is None and value["feature_acceptance"] is False
          and _same(value["admission"], admission_pin) and _same(value["authority"], authority_pin)
          and _same(value["attempt"], attempt_pin), "activation")
    worker_claim, _ = _outer_worker(authority_pin, attempt_pin, began_ns, **options)
    _need(_same(worker_claim, expected_parent), "identity")
    terminal, request_pin, request, worker = _job_evidence("runtime", value["supervisor"], **options)
    _need(process._owner_ok(terminal, _capture_dir("runtime", **options)), "owner_terminal")
    contract._obj(request, REQUEST_KEYS, "request")
    contract._process(request["parent"])
    _need(_same(request, dict(version=1, scope=scope, kind="runtime", admission=admission_pin,
                              authority=authority_pin, attempt=attempt_pin, began_ns=began_ns,
                              until_ns=request["until_ns"], running=None, parent=expected_parent)), "request")
    handoff.check_bounds(began_ns, request["until_ns"])
    admission = contract.validate_admission(handoff.at(admission_pin, selected.ADMISSION))
    contract.revalidate_inputs(admission)
    runtime = _verify_runtime(value["runtime"], dict(request=request_pin, worker=worker), admission,
                              admission_pin, authority_pin, attempt_pin, began_ns, request["until_ns"], **options)
    for bound in (pin, value["supervisor"], value["runtime"], request_pin, admission_pin):
        env.check_binding(bound)
    return runtime["closure"]


def execute(admission_pin, authority_pin, attempt_pin, *, began_ns, resume=False):
    """Run activation within the outer operation's remaining approved budget."""
    options = _resume_options(resume)
    selected = resume_handoff if resume else handoff
    control = _control(resume)
    scope = RESUME_SCOPE if resume else SCOPE
    _need(os.name == "nt" and Path.cwd() == ROOT
          and all(Path(os.environ.get(name, "")) == Path("D:/Dev/_Temp")
                  for name in ("TEMP", "TMP", "TMPDIR")), "environment")
    now = time.monotonic_ns()
    _need(type(began_ns) is int, "deadline")
    until_ns = min(began_ns + handoff.SECONDS * NS, now + handoff.ACTIVATION_SECONDS * NS) - TAIL_SECONDS * NS
    handoff.check_launch_window(began_ns, until_ns)
    _live_outer_worker(authority_pin, attempt_pin, began_ns, **options)
    admission = _inputs(admission_pin, authority_pin, attempt_pin, **options)
    _need(not any(os.path.lexists(path) for path in (control, selected.HANDOFF, selected.OWNED_ROOT)), "already_used")
    _live_outer_worker(authority_pin, attempt_pin, began_ns, **options)
    handoff.check_launch_window(began_ns, until_ns)
    env.safe_path(control, exists=False).mkdir(exist_ok=False)
    result = dict(version=1, scope=scope, admission=admission_pin, authority=authority_pin, attempt=attempt_pin,
                  supervisor=None, runtime=None, passed=False, reason=None, feature_acceptance=False)
    try:
        job = _supervise("runtime", admission_pin, authority_pin, attempt_pin, began_ns, until_ns, **options)
        result["supervisor"] = job["pin"]
        runtime_path = control / "runtime-result-v1.json"
        if job["known"] and os.path.lexists(runtime_path):
            result["runtime"] = _read(runtime_path)[0]
        _need(result["runtime"] is not None and process._owner_ok(job["terminal"], _capture_dir("runtime", **options)),
              "owner_terminal")
        _verify_runtime(result["runtime"], job, admission, admission_pin, authority_pin, attempt_pin,
                        began_ns, until_ns, **options)
        selected.approved_plan(authority_pin, attempt_pin)
        for pin in (job["pin"], job["request"], result["runtime"], admission_pin, authority_pin, attempt_pin):
            env.check_binding(pin)
        handoff.check_window(began_ns, until_ns)
        result["passed"] = True
    except BaseException as error:
        result["reason"] = _reason(error)
    _save(control / "activation-result-v1.json", result)
    return result


def main(argv=None):
    args = sys.argv[1:] if argv is None else argv
    resume = args in (["_resume_runtime"], ["_resume_controller"])
    options = _resume_options(resume)
    selected = resume_handoff if resume else handoff
    try:
        if args in (["_runtime"], ["_resume_runtime"]):
            request_pin, request, worker = _enter("runtime", **options)
            _need(request["running"] is None, "request")
            outer_worker, _ = _outer_worker(request["authority"], request["attempt"], request["began_ns"], **options)
            _need(_same(outer_worker, request["parent"]), "identity")
            admission = _inputs(request["admission"], request["authority"], request["attempt"], **options)
            handoff.check_launch_window(request["began_ns"], request["until_ns"])
            handoff_pin = _save(selected.HANDOFF, dict(version=1, scope=selected.HANDOFF_SCOPE, authority=request["authority"],
                                      attempt=request["attempt"], admission=request["admission"], supervisor=worker,
                                      began_ns=request["began_ns"], until_ns=request["until_ns"]))
            result = _run_owned(request["admission"], admission, request["until_ns"],
                                began_ns=request["began_ns"], handoff_pin=handoff_pin, **options)
            _save(_control(resume) / "runtime-result-v1.json",
                  dict(result, request=request_pin, worker=worker, handoff=handoff_pin))
            return 0 if result["passed"] else 1
        if args in (["_controller"], ["_resume_controller"]):
            _, request, _ = _enter("controller", **options)
            handoff_pin, handoff_record = selected.read_handoff(request["admission"])
            _need(all(_same(handoff_record[key], request[key]) for key in ("authority", "attempt", "began_ns", "until_ns"))
                  and _same(handoff_record["supervisor"], request["parent"]), "handoff")
            selected.approved_plan(request["authority"], request["attempt"])
            env.check_binding(handoff_pin)
            handoff.check_window(request["began_ns"], request["until_ns"])
            result = controller.run(request["admission"], request["running"])
            return 0 if result["outcome"] == "completed" else 1
    except BaseException:
        pass
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
