"""Run one separately authorized SDK24 activation inside an owned Windows job.

Copyright 2026 LocalLore contributors. SPDX-License-Identifier: Apache-2.0
"""
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import time

ROOT = Path(__file__).resolve().parents[1]
if __package__ in (None, ""):
    sys.path.insert(0, str(ROOT))

from benchmarks import cross_owner_deletion_ui_admission as admission
from benchmarks import cross_owner_deletion_ui_closure as closure
from benchmarks import cross_owner_deletion_ui_handoff as h
from benchmarks import isolated_adb_owner as process
from benchmarks import owned_cross_owner_deletion_ui as owned
from benchmarks import owned_target_owner as mechanisms
from benchmarks import receipt_avd_environment as env

REQUEST = h.ATTEMPT_ROOT / "activation-request-v1.json"
STARTED = h.ATTEMPT_ROOT / "activation-started-v1.json"
TERMINAL = h.ATTEMPT_ROOT / "activation-supervisor-v1.json"
RESULT = h.ATTEMPT_ROOT / "operation-result-v1.json"
CAPTURE = h.ATTEMPT_ROOT / "activation-capture-v1"
BARRIER = b"locallore-sdk24-cross-owner-deletion-activation-v1\n"
REQUEST_KEYS = ("version", "scope", "authority", "attempt", "admission", "began_ns", "until_ns", "parent")
TAIL_SECONDS = 15
TERMINAL_KEYS = ("status", "cleanup_complete", "elapsed_ms", "output_capture_complete",
                 "worker_returncode", "stdout_bytes", "stderr_bytes")
SUCCESS_OUTPUT = (
    b'{"qualified_target": true, "reason": "stop_requested", "feature_acceptance": false}',
    b'{"passed": true, "feature_acceptance": false}',
)
_need = env.require
_same = owned._same


def _identity(pid, expected=None):
    handles = process.ProcessHandles(mechanisms._ProcessApi())
    try:
        _, identity = handles.add(pid, expected)
        handles.guard()
    finally:
        _need(handles.close() is True, "identity")
    return identity


def _save(path, value):
    env.create_json(path, value)
    pin, saved = h.read(path)
    _need(_same(value, saved), "publication")
    return pin


def _context():
    _need(os.name == "nt" and Path.cwd() == ROOT and h.HANDOFF_ENV not in os.environ
          and all(Path(os.environ.get(key, "")) == Path("D:/Dev/_Temp")
                  for key in ("TEMP", "TMP", "TMPDIR")), "environment")


def _gate(authority_pin):
    admission_pin, _ = h.read(h.ADMISSION)
    authority = h.read_approval(authority_pin, admission_pin)
    value = admission.verify_candidate(admission_pin, authority["ledger"])
    _need(value["python"]["executable"]["path"] == sys.executable, "identity")
    for pin in (authority_pin, authority["proposal"], authority["ledger"], admission_pin):
        env.check_binding(pin)
    return admission_pin


def _handoff(request, supervisor):
    return dict(version=1, scope=h.HANDOFF_SCOPE, authority=request["authority"],
                attempt=request["attempt"], admission=request["admission"], supervisor=supervisor,
                began_ns=request["began_ns"], until_ns=request["until_ns"])


def _await_started(request_pin, request):
    parent = request["parent"]
    api = mechanisms._ProcessApi()
    handles = process.ProcessHandles(api)
    try:
        handles.add(parent["pid"], parent)
        handle, worker = handles.add(os.getpid())
        _need(worker["executable"] == parent["executable"] == sys.executable
              and api.parent_pid(handle) == parent["pid"] and os.getpid() in api.current_job_pids(), "identity")
        # The watchdog releases stdin before its callback publishes STARTED.
        deadline = time.monotonic() + 5
        while not os.path.lexists(STARTED):
            handles.guard()
            _need(time.monotonic() < deadline, "identity")
            time.sleep(.02)
        started_pin, started = h.read(STARTED)
        _need(_same(started, dict(request=request_pin, worker=worker)), "identity")
        handles.guard()
    finally:
        _need(handles.close() is True, "identity")
    return started_pin, worker


def _run_worker(request_pin):
    _context()
    request = h.at(request_pin, REQUEST)
    owned._obj(request, REQUEST_KEYS, "request")
    owned._process(request["parent"])
    _need(_same(request["version"], 1) and request["scope"] == h.AUTHORITY_SCOPE
          and request["parent"]["pid"] == os.getppid(), "request")
    window = (request["began_ns"], request["until_ns"])
    h.check_window(*window, minimum_seconds=h.LAUNCH_TAIL_SECONDS)
    started_pin, worker = _await_started(request_pin, request)
    h.check_window(*window, minimum_seconds=h.LAUNCH_TAIL_SECONDS)
    admission_pin = _gate(request["authority"])
    _need(_same(admission_pin, request["admission"]), "admission")
    run_auth = admission.materialize_run_authorization(admission_pin, request["authority"], request["attempt"])
    handoff = _save(h.HANDOFF, _handoff(request, worker))
    for pin in (request_pin, started_pin, request["authority"], request["attempt"], admission_pin, run_auth, handoff):
        env.check_binding(pin)
    h.check_window(*window, minimum_seconds=h.LAUNCH_TAIL_SECONDS)
    child_env = dict(os.environ)
    child_env[h.HANDOFF_ENV] = handoff["sha256"]
    child = subprocess.run(
        [sys.executable, "-I", "-S", "-B", str(ROOT / "benchmarks" / owned.OWNER_SCRIPT),
         "--admission", admission_pin["path"], "--admission-sha256", admission_pin["sha256"]],
        stdin=subprocess.DEVNULL, env=child_env, cwd=ROOT, creationflags=subprocess.CREATE_NO_WINDOW,
        check=False,
    )
    return 0 if child.returncode == 0 else 1


def _capture_ok(terminal):
    if type(terminal) is not dict or set(terminal) != set(TERMINAL_KEYS):
        return False
    expected = [newline.join((*SUCCESS_OUTPUT, b"")) for newline in (b"\r\n", b"\n")]
    stdout, stderr = (terminal[key] for key in ("stdout_bytes", "stderr_bytes"))
    elapsed = terminal["elapsed_ms"]
    if not (terminal["status"] == "child_exited" and terminal["cleanup_complete"] is True
            and terminal["output_capture_complete"] is True and _same(terminal["worker_returncode"], 0)
            and type(elapsed) is int and 0 <= elapsed <= h.ACTIVATION_SECONDS * 1000
            and type(stdout) is int and stdout in {len(value) for value in expected} and _same(stderr, 0)):
        return False
    with env.safe_path(CAPTURE / "owner-stdout-v1.bin").open("rb") as stream:
        output = stream.read(stdout + 1)
    with env.safe_path(CAPTURE / "owner-stderr-v1.bin").open("rb") as stream:
        error = stream.read(1)
    return len(output) == stdout and output in expected and not error


def _verify_terminal(request_pin, request, worker, terminal_pin, terminal):
    _need(worker is not None and _capture_ok(terminal), "owner")
    _need(_same(h.at(terminal_pin, TERMINAL), terminal), "owner")
    started_pin, started = h.read(STARTED)
    _need(_same(started, dict(request=request_pin, worker=worker)), "identity")
    handoff_pin, handoff = h.read(h.HANDOFF)
    _need(_same(handoff, _handoff(request, worker)), "handoff")
    admission_pin = request["admission"]
    h._approval(request["authority"], request["attempt"], admission_pin)
    evidence = closure.verify_result(admission_pin)
    completion, value = h.read(h.COMPLETION)
    _need(_same(value, dict(version=1, scope=h.AUTHORITY_SCOPE, admission=admission_pin, **evidence)), "binding")
    for pin in (request_pin, terminal_pin, started_pin, handoff_pin, completion, admission_pin,
                request["authority"], request["attempt"], *evidence.values()):
        env.check_binding(pin)
    _need(_capture_ok(terminal), "owner")
    return completion


def execute(authority_pin):
    """Spend the exact activation grant before launching the one supervised worker."""
    _context()
    began_ns = time.monotonic_ns()
    deadline_ns = began_ns + h.ACTIVATION_SECONDS * h.NS
    until_ns = deadline_ns - TAIL_SECONDS * h.NS
    for path in (h.ATTEMPT, h.RUN_AUTHORITY, h.HANDOFF, h.OWNED_ROOT, h.COMPLETION,
                 REQUEST, STARTED, STARTED.with_suffix(".pending.json"), TERMINAL, RESULT, CAPTURE):
        env.safe_path(path, exists=False)
        _need(not os.path.lexists(path), "already_used")
    admission_pin = _gate(authority_pin)
    h.check_window(began_ns, until_ns, minimum_seconds=h.LAUNCH_TAIL_SECONDS)
    parent = _identity(os.getpid())
    _need(parent["executable"] == sys.executable, "identity")
    attempt = _save(h.ATTEMPT, dict(version=1, scope=h.AUTHORITY_SCOPE, authority=authority_pin, no_retry=True))
    request = dict(version=1, scope=h.AUTHORITY_SCOPE, authority=authority_pin, attempt=attempt,
                   admission=admission_pin, began_ns=began_ns, until_ns=until_ns, parent=parent)
    result = dict(version=1, scope=h.AUTHORITY_SCOPE, authority=authority_pin, attempt=attempt,
                  request=None, supervisor=None, completion=None, passed=False,
                  reason="activation_refused", feature_acceptance=False)
    worker = None
    try:
        request_pin = _save(REQUEST, request)
        result["request"] = request_pin
        CAPTURE.mkdir(exist_ok=False)

        def started(child):
            nonlocal worker
            worker = _identity(child.pid)
            _need(worker["executable"] == sys.executable, "identity")
            pending = STARTED.with_suffix(".pending.json")
            _save(pending, dict(request=request_pin, worker=worker))
            pending.rename(STARTED)
            return True

        h.check_window(began_ns, until_ns, minimum_seconds=h.LAUNCH_TAIL_SECONDS)
        seconds = (until_ns - time.monotonic_ns()) // h.NS
        terminal = env.supervise_operation(
            [sys.executable, "-I", "-S", "-B", str(Path(__file__)), "_worker"],
            BARRIER + env.encoded(request_pin), CAPTURE, seconds, started,
        )
        result["supervisor"] = _save(TERMINAL, terminal)
        h.check_window(began_ns, deadline_ns)
        result["completion"] = _verify_terminal(request_pin, request, worker, result["supervisor"], terminal)
        h.check_window(began_ns, deadline_ns)
        result.update(passed=True, reason=None)
    except Exception as error:
        if isinstance(error, env.EnvironmentRefused) and str(error) in {
            "deadline", "owner", "identity", "handoff", "binding", "publication",
        }:
            result["reason"] = str(error)
    _save(RESULT, result)
    return result


def main(argv=None):
    args = sys.argv[1:] if argv is None else argv
    try:
        if args == ["_worker"]:
            raw = sys.stdin.buffer.read(131073)
            _need(len(raw) <= 131072 and raw.startswith(BARRIER), "barrier")
            return _run_worker(env.decode_json(raw[len(BARRIER):]))
        _need(type(args) is list and len(args) == 2 and args[0] == "--authority-sha256"
              and type(args[1]) is str and re.fullmatch("[0-9a-f]{64}", args[1]) is not None, "authority")
        pin, _ = h.read(h.AUTHORITY, 16384)
        _need(pin["sha256"] == args[1], "authority")
        result = execute(pin)
        print(json.dumps(dict(passed=result["passed"], reason=result["reason"], feature_acceptance=False)), flush=True)
        return 0 if result["passed"] else 1
    except Exception:
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
