"""Spend one SDK26 activation grant inside the shared Windows watchdog.

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

from benchmarks import archive_provider_platform_admission as candidate
from benchmarks import archive_provider_platform_closure as closure
from benchmarks import archive_provider_platform_handoff as handoff
from benchmarks import archive_provider_platform_preparation as prep
from benchmarks import archive_ui_build as files
from benchmarks import isolated_adb_owner as process
from benchmarks import owned_archive_provider_platform as owned
from benchmarks import owned_target_owner as mechanisms
from benchmarks import receipt_avd_environment as env

REQUEST = candidate.OUT / "activation-request-v1.json"
STARTED = candidate.OUT / "activation-started-v1.json"
OWNER_STARTED = candidate.OUT / "activation-owner-started-v1.json"
TERMINAL = candidate.OUT / "activation-supervisor-v1.json"
RESULT = candidate.OUT / "operation-result-v1.json"
CAPTURE = candidate.OUT / "activation-capture-v1"
BARRIER = b"locallore-sdk26-archive-provider-activation-v1\n"
OWNER_BARRIER = b"locallore-sdk26-archive-provider-owner-v1\n"
REQUEST_KEYS = ("version", "scope", "authority", "attempt", "candidate", "admission",
                "began_ns", "until_ns", "parent")
TERMINAL_KEYS = ("status", "cleanup_complete", "elapsed_ms", "output_capture_complete",
                 "worker_returncode", "stdout_bytes", "stderr_bytes")
SUCCESS_OUTPUT = (
    b'{"qualified_target": true, "reason": "stop_requested", "feature_acceptance": false}',
    b'{"passed": true, "feature_acceptance": false}',
)
REPLAY_SECONDS = 60
_need = env.require
_same = owned._same
_save = prep._save


def _read(path, limit=131072):
    raw = files._read(path, limit)
    return candidate._pin_for_bytes(path, raw), env.decode_json(raw)


def _at(pin, path):
    return env.decode_json(prep._bound(pin, path, 131072))


def _identity(pid, expected=None):
    handles = process.ProcessHandles(mechanisms._ProcessApi())
    try:
        _, value = handles.add(pid, expected)
        handles.guard()
    finally:
        _need(handles.close() is True, "identity")
    return value


def _context(*, allow_handoff=False):
    _need(os.name == "nt" and ROOT.drive.upper() == "D:" and Path.cwd() == ROOT
          and (allow_handoff or owned.HANDOFF_ENV not in os.environ)
          and all(Path(os.environ.get(key, "")) == Path("D:/Dev/_Temp")
                  for key in ("TEMP", "TMP", "TMPDIR")), "environment")


def _gate(authority_pin, candidate_pin):
    approved = handoff.read_approval(authority_pin, candidate_pin)
    admission = candidate.verify_candidate(candidate_pin, approved["ledger"])
    _need(admission["python"]["executable"]["path"] == sys.executable, "identity")
    for pin in (authority_pin, candidate_pin, approved["proposal"], approved["admission"], approved["ledger"]):
        env.check_binding(pin)
    return approved["admission"]


def _request(request_pin):
    request = _at(request_pin, REQUEST)
    owned._obj(request, REQUEST_KEYS, "request")
    owned._process(request["parent"])
    _need(_same(request["version"], 1) and request["scope"] == handoff.AUTHORITY_SCOPE, "request")
    handoff.check_window(request["began_ns"], request["until_ns"],
                         minimum_seconds=handoff.LAUNCH_TAIL_SECONDS)
    return request


def _handoff(request, worker):
    return dict(version=1, scope=handoff.HANDOFF_SCOPE, authority=request["authority"],
                attempt=request["attempt"], candidate=request["candidate"], admission=request["admission"],
                supervisor=worker, began_ns=request["began_ns"], until_ns=request["until_ns"])


def _await_started(request_pin, request):
    parent = request["parent"]
    _need(parent["pid"] == os.getppid() and parent["executable"] == sys.executable, "identity")
    api = mechanisms._ProcessApi()
    handles = process.ProcessHandles(api)
    try:
        handles.add(parent["pid"], parent)
        worker_handle, worker = handles.add(os.getpid())
        _need(worker["executable"] == sys.executable and api.parent_pid(worker_handle) == parent["pid"]
              and os.getpid() in api.current_job_pids(), "identity")
        deadline = time.monotonic() + 5
        while not os.path.lexists(STARTED):
            handles.guard()
            _need(time.monotonic() < deadline, "identity")
            time.sleep(.02)
        started_pin, started = _read(STARTED)
        _need(_same(started, dict(request=request_pin, worker=worker)), "identity")
        handles.guard()
    finally:
        _need(handles.close() is True, "identity")
    return started_pin, worker


def _start_owner(request_pin, request, handoff_pin):
    child_env = dict(os.environ)
    child_env[owned.HANDOFF_ENV] = handoff_pin["sha256"]
    api = mechanisms._ProcessApi()
    handles = process.ProcessHandles(api)
    child = subprocess.Popen(
        [sys.executable, "-I", "-S", "-B", str(Path(__file__).resolve()), "_owner"],
        stdin=subprocess.PIPE, env=child_env, cwd=ROOT, creationflags=subprocess.CREATE_NO_WINDOW,
    )
    try:
        with child.stdin as stream:
            child_handle, identity = handles.add(child.pid)
            _need(child.poll() is None and identity["executable"] == sys.executable
                  and api.parent_pid(child_handle) == os.getpid()
                  and {os.getpid(), child.pid} <= set(api.current_job_pids()), "identity")
            owner_pin = _save(OWNER_STARTED, dict(request=request_pin, handoff=handoff_pin, owner=identity))
            for pin in (request_pin, handoff_pin, owner_pin):
                env.check_binding(pin)
            handles.guard()
            handoff.check_window(request["began_ns"], request["until_ns"],
                                 minimum_seconds=handoff.LAUNCH_TAIL_SECONDS)
            payload = OWNER_BARRIER + env.encoded(request_pin)
            _need(stream.write(payload) == len(payload), "barrier")
        seconds = (request["until_ns"] - time.monotonic_ns()) / handoff.NS
        _need(seconds > 0, "deadline")
        return 0 if child.wait(timeout=seconds) == 0 else 1
    finally:
        # The outer job owns cleanup even when release or the bounded wait fails.
        _need(handles.close() is True, "identity")


def _run_worker(request_pin):
    _context()
    request = _request(request_pin)
    started_pin, worker = _await_started(request_pin, request)
    admission_pin = _gate(request["authority"], request["candidate"])
    _need(_same(admission_pin, request["admission"]), "admission")
    run_auth = handoff.materialize_run_authorization(
        request["authority"], request["candidate"], request["attempt"],
    )
    handoff_pin = _save(candidate.HANDOFF, _handoff(request, worker))
    for pin in (request_pin, started_pin, request["authority"], request["attempt"], request["candidate"],
                admission_pin, run_auth, handoff_pin):
        env.check_binding(pin)
    handoff.check_window(request["began_ns"], request["until_ns"],
                         minimum_seconds=handoff.LAUNCH_TAIL_SECONDS)
    return _start_owner(request_pin, request, handoff_pin)


def _run_owner(request_pin):
    _context(allow_handoff=True)
    request = _request(request_pin)
    started_pin, started = _read(STARTED)
    owned._obj(started, ("request", "worker"), "identity")
    worker = started["worker"]
    owned._process(worker)
    _need(_same(started["request"], request_pin) and worker["pid"] == os.getppid(), "identity")
    _identity(worker["pid"], worker)
    identity = _identity(os.getpid())
    _need(identity["executable"] == worker["executable"] == sys.executable
          and {worker["pid"], identity["pid"]} <= set(mechanisms._ProcessApi().current_job_pids()), "identity")
    handoff_pin, value = _read(candidate.HANDOFF)
    _need(handoff_pin["sha256"] == os.environ.get(owned.HANDOFF_ENV)
          and _same(value, _handoff(request, worker)), "handoff")
    owner_pin, observed = _read(OWNER_STARTED)
    _need(_same(observed, dict(request=request_pin, handoff=handoff_pin, owner=identity)), "identity")
    for pin in (request_pin, started_pin, handoff_pin, owner_pin):
        env.check_binding(pin)
    admission_pin = request["admission"]
    return owned.main(["--admission", admission_pin["path"], "--admission-sha256", admission_pin["sha256"]])


def _verify_capture(terminal):
    owned._obj(terminal, TERMINAL_KEYS, "owner")
    stdout, stderr = (terminal[key] for key in ("stdout_bytes", "stderr_bytes"))
    elapsed = terminal["elapsed_ms"]
    expected = [newline.join((*SUCCESS_OUTPUT, b"")) for newline in (b"\r\n", b"\n")]
    _need(terminal["status"] == "child_exited" and terminal["cleanup_complete"] is True
          and terminal["output_capture_complete"] is True and _same(terminal["worker_returncode"], 0)
          and type(elapsed) is int and 0 <= elapsed <= env.REAL_MAX_SECONDS * 1000
          and type(stdout) is int and stdout in {len(value) for value in expected}
          and _same(stderr, 0), "owner")
    pins = {}
    for channel, size in (("stdout", stdout), ("stderr", stderr)):
        path = env.safe_path(CAPTURE / ("owner-" + channel + "-v1.bin"))
        with path.open("rb") as stream:
            raw = stream.read(size + 1)
        _need(len(raw) == size and (raw in expected if channel == "stdout" else not raw), "owner")
        pins[channel] = candidate._pin_for_bytes(path, raw)
    return pins


def _verify_terminal(request_pin, request, worker, terminal_pin, terminal):
    _need(worker is not None and _same(_at(terminal_pin, TERMINAL), terminal)
          and _same(_at(request_pin, REQUEST), request), "owner")
    capture = _verify_capture(terminal)
    started_pin, started = _read(STARTED)
    _need(_same(started, dict(request=request_pin, worker=worker)), "identity")
    handoff_pin, value = _read(candidate.HANDOFF)
    _need(_same(value, _handoff(request, worker)), "handoff")
    observed_pin, observed = _read(OWNER_STARTED)
    owned._obj(observed, ("request", "handoff", "owner"), "identity")
    owner = observed["owner"]
    owned._process(owner)
    _need(_same(observed["request"], request_pin) and _same(observed["handoff"], handoff_pin)
          and owner["executable"] == worker["executable"]
          and owner["pid"] not in (worker["pid"], request["parent"]["pid"])
          and worker["creation_filetime"] <= owner["creation_filetime"], "identity")
    approved = handoff.read_approval(request["authority"], request["candidate"])
    handoff._claim_matches(request["attempt"], request["authority"], request["candidate"])
    admission_pin = request["admission"]
    _need(_same(admission_pin, approved["admission"]), "admission")
    evidence = closure.verify_result(admission_pin, owner)
    completion, value = _read(candidate.COMPLETION)
    _need(_same(value, dict(version=1, scope=handoff.AUTHORITY_SCOPE,
                            admission=admission_pin, **evidence)), "binding")
    for pin in (request_pin, terminal_pin, started_pin, handoff_pin, observed_pin, completion, admission_pin,
                request["authority"], request["attempt"], request["candidate"], approved["proposal"],
                *evidence.values(), *capture.values()):
        env.check_binding(pin)
    return dict(completion=completion, started=started_pin, handoff=handoff_pin,
                observed_owner=observed_pin, capture=capture)


def execute(authority_pin, candidate_pin):
    """Spend the exact activation grant before launching the one supervised worker."""
    _context()
    began_ns = time.monotonic_ns()
    until_ns = began_ns + env.REAL_MAX_SECONDS * handoff.NS
    deadline_ns = until_ns + REPLAY_SECONDS * handoff.NS
    pending = STARTED.with_suffix(".pending.json")
    for path in (handoff.ATTEMPT, candidate.RUN_AUTHORITY, candidate.HANDOFF, candidate.OWNED_ROOT,
                 candidate.COMPLETION, REQUEST, STARTED, pending, OWNER_STARTED, TERMINAL, RESULT, CAPTURE):
        env.safe_path(path, exists=False)
        _need(not os.path.lexists(path), "already_used")
    admission_pin = _gate(authority_pin, candidate_pin)
    handoff.check_window(began_ns, until_ns, minimum_seconds=handoff.LAUNCH_TAIL_SECONDS)
    parent = _identity(os.getpid())
    _need(parent["executable"] == sys.executable, "identity")
    attempt = _save(handoff.ATTEMPT, handoff.claim_value(authority_pin, candidate_pin))
    request = dict(version=1, scope=handoff.AUTHORITY_SCOPE, authority=authority_pin, attempt=attempt,
                   candidate=candidate_pin, admission=admission_pin, began_ns=began_ns, until_ns=until_ns,
                   parent=parent)
    result = dict(version=1, scope=handoff.AUTHORITY_SCOPE, authority=authority_pin, attempt=attempt,
                  request=None, supervisor=None, completion=None, evidence=None, passed=False,
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
            _save(pending, dict(request=request_pin, worker=worker))
            pending.rename(STARTED)
            return True

        handoff.check_window(began_ns, until_ns, minimum_seconds=handoff.LAUNCH_TAIL_SECONDS)
        seconds = (until_ns - time.monotonic_ns()) // handoff.NS
        terminal = env.supervise_operation(
            [sys.executable, "-I", "-S", "-B", str(Path(__file__).resolve()), "_worker"],
            BARRIER + env.encoded(request_pin), CAPTURE, seconds, started,
        )
        result["supervisor"] = _save(TERMINAL, terminal)
        _need(time.monotonic_ns() < deadline_ns, "deadline")
        verified = _verify_terminal(request_pin, request, worker, result["supervisor"], terminal)
        _need(time.monotonic_ns() < deadline_ns, "deadline")
        result.update(completion=verified.pop("completion"), evidence=verified, passed=True, reason=None)
    except (Exception, KeyboardInterrupt) as error:
        if isinstance(error, KeyboardInterrupt):
            result["reason"] = "cancelled"
        elif isinstance(error, env.EnvironmentRefused) and str(error) in {
            "deadline", "owner", "identity", "handoff", "binding", "publication",
        }:
            result["reason"] = str(error)
    _save(RESULT, result)
    return result


def _barrier(prefix):
    raw = sys.stdin.buffer.read(131073)
    _need(len(raw) <= 131072 and raw.startswith(prefix), "barrier")
    return env.decode_json(raw[len(prefix):])


def main(argv=None):
    args = sys.argv[1:] if argv is None else argv
    try:
        if args == ["_worker"]:
            return _run_worker(_barrier(BARRIER))
        if args == ["_owner"]:
            return _run_owner(_barrier(OWNER_BARRIER))
        _need(type(args) is list and len(args) == 2 and args[0] == "--authority-sha256"
              and type(args[1]) is str and re.fullmatch("[0-9a-f]{64}", args[1]) is not None, "authority")
        _context()
        authority_pin, _ = _read(handoff.AUTHORITY, 16384)
        _need(authority_pin["sha256"] == args[1], "authority")
        candidate_pin, _ = _read(candidate.CANDIDATE)
        result = execute(authority_pin, candidate_pin)
        print(json.dumps(dict(passed=result["passed"], reason=result["reason"], feature_acceptance=False)),
              flush=True)
        return 0 if result["passed"] else 1
    except (Exception, KeyboardInterrupt):
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
