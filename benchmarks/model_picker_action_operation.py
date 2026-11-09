"""One approved SDK22 preparation and synthetic picker test under a Windows Job.

Copyright 2026 LocalLore contributors. SPDX-License-Identifier: Apache-2.0
"""
import hashlib
import os
from pathlib import Path
import re
import sys
import time

ROOT = Path(__file__).resolve().parents[1]
if __package__ in (None, ""):
    sys.path.insert(0, str(ROOT))

from benchmarks import model_picker_action_activation as activation
from benchmarks import model_picker_action_preparation as preparation
from benchmarks import isolated_adb_owner as process
from benchmarks import archive_ui_build as files
from benchmarks import model_picker_action_handoff as handoff
from benchmarks import owned_model_picker_action as contract
from benchmarks import owned_target_owner as mechanisms
from benchmarks import receipt_avd_environment as env

REQUEST = handoff.ATTEMPT_ROOT / "operation-request-v1.json"
STARTED = handoff.ATTEMPT_ROOT / "operation-started-v1.json"
WORKER_CLAIM = handoff.ATTEMPT_ROOT / "operation-worker-claim-v1.json"
CAPTURE = handoff.ATTEMPT_ROOT / "operation-capture-v1"
TERMINAL = handoff.ATTEMPT_ROOT / "operation-supervisor-v1.json"
STAGE = handoff.ATTEMPT_ROOT / "operation-stage-v1.json"
RESULT = handoff.ATTEMPT_ROOT / "operation-result-v1.json"
PREPARE_AUTH = handoff.PREPARE_AUTH
PREFLIGHT = handoff.ATTEMPT_ROOT / "operation-preflight-v1.json"
PREPARED = handoff.GUEST / "prepare-result-v1.json"
ACTIVATED = activation.CONTROL / "activation-result-v1.json"
BARRIER = b"model-picker-action-operation-v1\n"
REQUEST_KEYS = ("version", "scope", "authority", "attempt", "began_ns", "parent")
STAGE_KEYS = ("version", "scope", "authority", "attempt", "worker", "phase", "preflight",
              "prepare", "prepare_evidence", "admission", "activation", "closure",
              "passed", "reason", "feature_acceptance")
NS = handoff.NS
PREPARE_BUDGET = 180 + handoff.ACTIVATION_SECONDS + 2 * handoff.TAIL_SECONDS
_need = env.require
_same = contract._same
_read = handoff.read
_save = handoff.save
_identity = activation._identity


def _attempt_record(authority_pin):
    return dict(version=1, scope=handoff.OPERATION_SCOPE, authority=authority_pin, no_retry=True)


def _budget(began_ns, minimum=0):
    now = time.monotonic_ns()
    _need(type(began_ns) is int and 0 < began_ns <= now
          and now - began_ns + minimum * NS < handoff.SECONDS * NS, "deadline")
    return now


def _reason(error):
    if isinstance(error, KeyboardInterrupt):
        return "cancelled"
    if type(error) is env.EnvironmentRefused and str(error) in {
        "activation", "already_used", "authority", "binding", "binding_changed", "deadline", "host_capacity",
        "host_commit_capacity", "host_cpu_capacity", "host_commit_unavailable", "identity", "invalid_profile",
        "ledger", "memory_unavailable", "not_authorized", "owner", "ports_unavailable", "prepare_failed",
        "prepared", "proposal_changed", "storage_capacity", "storage_ledger_changed", "storage_registry_locked",
        "storage_storage_capacity_exceeded",
    }:
        return str(error)
    return "operation_refused"


def _verify_prepare(pin, proposal):
    value = handoff.at(pin, PREPARED)
    _need(_same(value, dict(version=1, proposal_sha256=proposal["sha256"], status="completed",
                            closure_verified=True, child_cleanup_complete=True, prepared_created=True)), "prepared")
    return value


def _prepare_evidence(proposal, worker_identity):
    start_pin, start = _read(handoff.GUEST / "prepare-start-v1.json")
    claim_pin, claim = _read(handoff.GUEST / "prepare-worker-claimed-v1.json")
    client_pin, capture = _read(handoff.GUEST / "prepare-client-v1.json")
    contract._obj(start, ("proposal_sha256", "facts", "owner", "prepare_scope"), "prepared")
    contract._obj(claim, ("proposal_sha256", "worker", "prepare_scope"), "prepared")
    contract._obj(capture, ("status", "returncode", "cleanup_complete", "elapsed_ms",
                            "stdout_sha256", "stderr_bytes"), "prepared")
    child = claim["worker"]
    contract._process(child)
    _need(_same(start["owner"], worker_identity) and type(start["facts"]) is dict
          and child["pid"] != worker_identity["pid"] and child["executable"] == worker_identity["executable"]
          and child["creation_filetime"] >= worker_identity["creation_filetime"]
          and all(row["proposal_sha256"] == proposal["sha256"] and row["prepare_scope"] == handoff.OPERATION_SCOPE
                  for row in (start, claim)), "prepared")
    path = handoff.GUEST / "prepare-stdout-v1.bin"
    raw = files._read(path, env.MAX_OUTPUT)
    stdout = dict(path=str(path), bytes=len(raw), sha256=hashlib.sha256(raw).hexdigest())
    _need(capture["status"] == "completed" and _same(capture["returncode"], 0)
          and capture["cleanup_complete"] is True and capture["stdout_sha256"] == stdout["sha256"]
          and type(capture["elapsed_ms"]) is int and capture["elapsed_ms"] >= 0
          and type(capture["stderr_bytes"]) is int and 0 <= capture["stderr_bytes"] <= env.MAX_OUTPUT - len(raw),
          "prepared")
    for pin in (start_pin, claim_pin, client_pin, stdout):
        env.check_binding(pin)
    return dict(start=start_pin, worker=claim_pin, client=client_pin, stdout=stdout)


def _run_stages(authority_pin, attempt_pin, began_ns, worker_identity):
    stage = dict(version=1, scope=handoff.OPERATION_SCOPE, authority=authority_pin, attempt=attempt_pin,
                 worker=worker_identity, phase="preflight", preflight=None, prepare=None, prepare_evidence=None,
                 admission=None,
                 activation=None, closure=None, passed=False, reason=None, feature_acceptance=False)
    try:
        _budget(began_ns, PREPARE_BUDGET)
        authority, plan = handoff.approved_plan(authority_pin, attempt_pin)
        prepare = handoff.prepare_plan(plan)
        stage["preflight"] = _save(PREFLIGHT, preparation.preflight(authority, plan, prepare))
        _need(_same(handoff.approved_plan(authority_pin, attempt_pin), (authority, plan))
              and _same(handoff.prepare_plan(plan), prepare), "binding")
        _budget(began_ns, PREPARE_BUDGET)
        prepare_pin = plan["prepare"]
        stage["phase"] = "prepare"
        auth_pin = _save(PREPARE_AUTH, dict(
            version=1, phase="prepare", proposal_sha256=prepare_pin["sha256"],
            prepare_scope=handoff.OPERATION_SCOPE, allow_environment_calls=True, root_go_pending=False,
        ))
        _need(_same(handoff.approved_plan(authority_pin, attempt_pin), (authority, plan))
              and _same(handoff.prepare_plan(plan), prepare), "binding")
        _budget(began_ns, PREPARE_BUDGET)
        env.prepare(prepare_pin["path"], auth_pin["path"], expected_ledger=authority["ledger"],
                    expected_proposal_sha256=prepare_pin["sha256"], prepare_scope=handoff.OPERATION_SCOPE)
        stage["prepare"] = _read(PREPARED)[0]
        _verify_prepare(stage["prepare"], prepare_pin)
        stage["prepare_evidence"] = _prepare_evidence(prepare_pin, worker_identity)
        env.check_binding(auth_pin)

        stage["phase"] = "run_inputs"
        _budget(began_ns, handoff.ACTIVATION_SECONDS)
        _need(_same(handoff.approved_plan(authority_pin, attempt_pin), (authority, plan))
              and _same(handoff.prepare_plan(plan), prepare), "binding")
        stage["admission"] = preparation.create_admission(plan)
        stage["phase"] = "activation"
        _budget(began_ns, handoff.ACTIVATION_SECONDS)
        value = activation.execute(stage["admission"], authority_pin, attempt_pin, began_ns=began_ns)
        stage["activation"], saved = _read(ACTIVATED)
        _need(_same(saved, value) and value["passed"] is True, "activation")
        stage["closure"] = activation.verify_result(stage["activation"], stage["admission"], authority_pin,
                                                    attempt_pin, began_ns=began_ns,
                                                    expected_parent=worker_identity)
        _need(_same(handoff.approved_plan(authority_pin, attempt_pin), (authority, plan)), "authority")
        _budget(began_ns)
        stage.update(phase="completed", passed=True)
    except BaseException as error:
        stage["reason"] = _reason(error)
        if stage["phase"] == "prepare" and stage["prepare"] is None and os.path.lexists(PREPARED):
            try:
                pin, partial = _read(PREPARED)
                if partial["proposal_sha256"] == prepare_pin["sha256"]:
                    stage["prepare"] = pin
            except (KeyError, OSError, TypeError, ValueError, RuntimeError):
                pass
    _save(STAGE, stage)
    return stage


def _verify_stage(stage_pin, authority_pin, attempt_pin, began_ns, worker_identity):
    stage = handoff.at(stage_pin, STAGE)
    contract._obj(stage, STAGE_KEYS, "stage")
    _need(_same(stage["version"], 1) and stage["scope"] == handoff.OPERATION_SCOPE
          and _same(stage["authority"], authority_pin) and _same(stage["attempt"], attempt_pin)
          and _same(stage["worker"], worker_identity) and stage["phase"] == "completed"
          and stage["passed"] is True and stage["reason"] is None and stage["feature_acceptance"] is False, "stage")
    authority, plan = handoff.approved_plan(authority_pin, attempt_pin)
    handoff.prepare_plan(plan)
    preflight = handoff.at(stage["preflight"], PREFLIGHT)
    _need(type(preflight) is dict and preflight.get("ports_free") is True
          and _same(preflight["storage"]["ledger"], authority["ledger"])
          and preflight["storage"]["would_fit"] is True
          and preflight["storage"]["admission_granted"] is False, "ledger")
    _verify_prepare(stage["prepare"], plan["prepare"])
    _need(_same(stage["prepare_evidence"], _prepare_evidence(plan["prepare"], worker_identity)), "prepared")
    auth_pin, authorization = _read(PREPARE_AUTH, 4096)
    env.check_authorization(authorization, "prepare", plan["prepare"]["sha256"], prepare_scope=handoff.OPERATION_SCOPE)
    closure = activation.verify_result(stage["activation"], stage["admission"], authority_pin, attempt_pin,
                                       began_ns=began_ns, expected_parent=worker_identity)
    _need(_same(stage["closure"], closure), "activation")
    for pin in (stage_pin, authority_pin, attempt_pin, authority["proposal"], authority["plan"], plan["prepare"],
                stage["preflight"], stage["prepare"], auth_pin, stage["admission"], stage["activation"],
                *closure.values()):
        env.check_binding(pin)
    return stage


def _supervise(request_pin, began_ns):
    until_ns = began_ns + (handoff.SECONDS - handoff.TAIL_SECONDS) * NS
    worker = None
    capture = env.safe_path(CAPTURE, exists=False)
    capture.mkdir(exist_ok=False)

    def started(child):
        nonlocal worker
        worker = _identity(child.pid)
        _need(worker["executable"] == sys.executable, "identity")
        pending = STARTED.with_suffix(".pending.json")
        _save(pending, dict(request=request_pin, worker=worker))
        pending.rename(STARTED)
        return True

    seconds = (until_ns - _budget(began_ns)) // NS
    _need(seconds > 0, "deadline")
    terminal = env.supervise_operation(
        [sys.executable, "-I", "-S", "-B", str(Path(__file__)), "_worker"],
        BARRIER + env.encoded(request_pin), capture, seconds, started,
    )
    return dict(terminal=terminal, pin=_save(TERMINAL, terminal), worker=worker)


def _enter():
    raw = sys.stdin.buffer.read(131073)
    _need(len(raw) <= 131072 and raw.startswith(BARRIER), "barrier")
    pin = env.decode_json(raw[len(BARRIER):])
    request = handoff.at(pin, REQUEST)
    contract._obj(request, REQUEST_KEYS, "request")
    contract._process(request["parent"])
    _need(_same(request["version"], 1) and request["scope"] == handoff.OPERATION_SCOPE
          and request["parent"]["pid"] == os.getppid(), "request")
    _identity(os.getppid(), request["parent"])
    wait_until = _budget(request["began_ns"], PREPARE_BUDGET) + 5 * NS
    while not os.path.lexists(STARTED):
        _need(time.monotonic_ns() < wait_until, "identity")
        time.sleep(.02)
    started_pin, started = _read(STARTED)
    contract._obj(started, ("request", "worker"), "identity")
    contract._process(started["worker"])
    _need(_same(started["request"], pin), "request")
    worker = _identity(os.getpid(), started["worker"])
    _need(worker["executable"] == request["parent"]["executable"]
          and os.getpid() in mechanisms._ProcessApi().current_job_pids(), "job")
    env.check_binding(started_pin)
    env.check_binding(pin)
    _budget(request["began_ns"], PREPARE_BUDGET)
    return pin, request, worker


def execute(authority_pin, *, began_ns=None):
    """Consume an approved attempt once. SDK work is confined to the owned worker."""
    if began_ns is None:
        began_ns = time.monotonic_ns()
    _need(os.name == "nt" and Path.cwd() == ROOT
          and all(Path(os.environ.get(key, "")) == Path("D:/Dev/_Temp")
                  for key in ("TEMP", "TMP", "TMPDIR")), "environment")
    _budget(began_ns, PREPARE_BUDGET)
    _, plan = handoff.read_authority(authority_pin)
    handoff.prepare_plan(plan)
    _budget(began_ns, PREPARE_BUDGET)
    _need(not any(os.path.lexists(path) for path in (handoff.ATTEMPT_ROOT, handoff.GUEST)), "already_used")
    env.safe_path(handoff.ATTEMPT_ROOT, exists=False).mkdir(exist_ok=False)
    attempt_pin = _save(handoff.ATTEMPT, _attempt_record(authority_pin))
    result = dict(version=1, scope=handoff.OPERATION_SCOPE, authority=authority_pin, attempt=attempt_pin,
                  supervisor=None, stages=None, passed=False, reason=None, feature_acceptance=False)
    try:
        parent = _identity(os.getpid())
        _need(parent["executable"] == sys.executable, "identity")
        request = _save(REQUEST, dict(version=1, scope=handoff.OPERATION_SCOPE, authority=authority_pin,
                                     attempt=attempt_pin, began_ns=began_ns, parent=parent))
        job = _supervise(request, began_ns)
        result["supervisor"] = job["pin"]
        if os.path.lexists(STAGE):
            result["stages"] = _read(STAGE)[0]
        _need(result["stages"] is not None and process._owner_ok(job["terminal"], CAPTURE), "owner")
        worker = job["worker"]
        contract._process(worker)
        _need(_same(handoff.at(job["pin"], TERMINAL), job["terminal"]), "owner")
        expected = dict(request=request, worker=worker)
        for path in (STARTED, WORKER_CLAIM):
            pin, actual = _read(path)
            _need(_same(actual, expected), "identity")
            env.check_binding(pin)
        _verify_stage(result["stages"], authority_pin, attempt_pin, began_ns, worker)
        for pin in (request, job["pin"], result["stages"]):
            env.check_binding(pin)
        _budget(began_ns)
        result["passed"] = True
    except BaseException as error:
        result["reason"] = _reason(error)
    _save(RESULT, result)
    return result


def main(argv=None):
    began_ns = time.monotonic_ns()
    args = sys.argv[1:] if argv is None else argv
    try:
        if args == ["_worker"]:
            pin, request, worker = _enter()
            _save(WORKER_CLAIM, dict(request=pin, worker=worker))
            stage = _run_stages(request["authority"], request["attempt"], request["began_ns"], worker)
            return 0 if stage["passed"] else 1
        if (type(args) is list and len(args) == 2 and args[0] == "--authority-sha256"
                and type(args[1]) is str and re.fullmatch("[0-9a-f]{64}", args[1])):
            pin, _ = _read(handoff.AUTHORITY, 16384)
            _need(pin["sha256"] == args[1], "authority")
            return 0 if execute(pin, began_ns=began_ns)["passed"] else 1
    except BaseException:
        pass
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
