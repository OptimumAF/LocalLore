"""Supervise one approved activation of the existing SDK23 prepared guest.

Copyright 2026 LocalLore contributors. SPDX-License-Identifier: Apache-2.0
"""
import os
from pathlib import Path
import re
import sys
import time

ROOT = Path(__file__).resolve().parents[1]
if __package__ in (None, ""):
    sys.path.insert(0, str(ROOT))

from benchmarks import isolated_adb_owner as process
from benchmarks import owned_saved_library_status as contract
from benchmarks import owned_target_owner as mechanisms
from benchmarks import receipt_avd_environment as env
from benchmarks import saved_library_status_activation as activation
from benchmarks import saved_library_status_handoff as handoff
from benchmarks import saved_library_status_operation as original
from benchmarks import saved_library_status_resume_handoff as resume

REQUEST = resume.ATTEMPT_ROOT / "operation-request-v1.json"
STARTED = resume.ATTEMPT_ROOT / "operation-started-v1.json"
WORKER_CLAIM = resume.ATTEMPT_ROOT / "operation-worker-claim-v1.json"
CAPTURE = resume.ATTEMPT_ROOT / "operation-capture-v1"
TERMINAL = resume.ATTEMPT_ROOT / "operation-supervisor-v1.json"
STAGE = resume.ATTEMPT_ROOT / "operation-stage-v1.json"
RESULT = resume.ATTEMPT_ROOT / "operation-result-v1.json"
PREFLIGHT = resume.ATTEMPT_ROOT / "operation-preflight-v1.json"
ACTIVATED = resume.ATTEMPT_ROOT / "activation-v1/activation-result-v1.json"
BARRIER = b"saved-library-status-resume-operation-v1\n"
REQUEST_KEYS = original.REQUEST_KEYS
STAGE_KEYS = ("version", "scope", "authority", "attempt", "worker", "phase", "preflight",
              "admission", "activation", "closure", "passed", "reason", "feature_acceptance")
NS = handoff.NS
ACTIVATION_BUDGET = handoff.ACTIVATION_SECONDS + 2 * handoff.TAIL_SECONDS
_need = env.require
_same = contract._same
_read = handoff.read
_save = handoff.save
_identity = activation._identity
_budget = original._budget
_reason = original._reason


def preflight(plan):
    """Recheck the existing prepared guest and required host resources."""
    proposal = resume._prepared(plan)
    context = {"preparation_root": resume.review.EXECUTED_ROOT}
    env.validate_proposal(proposal, "run", **context)
    env.verify_installation(proposal, **context)
    env.check_external_state(proposal)
    facts = env.resource_facts(proposal)
    env.ports_free()
    private = process._exclusive_preflight(mechanisms._ProcessApi(), port=contract.PORT)
    _need(private["exclusive_bind_succeeded"] is True and
          all(_same(private[key], 1) for key in ("created_mask", "close_attempted_mask", "closed_mask")),
          "ports_unavailable")
    _need(_same(resume._prepared(plan), proposal), "prepared")
    return dict(resources=facts, ledger=plan["evidence"]["ledger"], ports_free=True)


def _run_stages(authority_pin, attempt_pin, began_ns, worker_identity):
    stage = dict(version=1, scope=resume.OPERATION_SCOPE, authority=authority_pin, attempt=attempt_pin,
                 worker=worker_identity, phase="preflight", preflight=None, admission=None,
                 activation=None, closure=None, passed=False, reason=None, feature_acceptance=False)
    try:
        _budget(began_ns, ACTIVATION_BUDGET)
        authority, plan = resume.approved_plan(authority_pin, attempt_pin)
        stage["preflight"] = _save(PREFLIGHT, preflight(plan))
        _need(_same(resume.approved_plan(authority_pin, attempt_pin), (authority, plan)), "authority")
        _budget(began_ns, ACTIVATION_BUDGET)
        stage["phase"] = "run_inputs"
        stage["admission"] = resume.bind_admission(authority_pin, attempt_pin)
        stage["phase"] = "activation"
        _budget(began_ns, ACTIVATION_BUDGET)
        value = activation.execute(stage["admission"], authority_pin, attempt_pin, began_ns=began_ns, resume=True)
        stage["activation"], saved = _read(ACTIVATED)
        _need(_same(saved, value) and value["passed"] is True, "activation")
        stage["closure"] = activation.verify_result(stage["activation"], stage["admission"], authority_pin,
                                                    attempt_pin, began_ns=began_ns,
                                                    expected_parent=worker_identity, resume=True)
        _need(_same(resume.approved_plan(authority_pin, attempt_pin), (authority, plan)), "authority")
        _budget(began_ns)
        stage.update(phase="completed", passed=True)
    except BaseException as error:
        stage["reason"] = _reason(error)
    _save(STAGE, stage)
    return stage


def _verify_stage(stage_pin, authority_pin, attempt_pin, began_ns, worker_identity):
    stage = handoff.at(stage_pin, STAGE)
    contract._obj(stage, STAGE_KEYS, "stage")
    _need(_same(stage["version"], 1) and stage["scope"] == resume.OPERATION_SCOPE
          and _same(stage["authority"], authority_pin) and _same(stage["attempt"], attempt_pin)
          and _same(stage["worker"], worker_identity) and stage["phase"] == "completed"
          and stage["passed"] is True and stage["reason"] is None and stage["feature_acceptance"] is False, "stage")
    authority, plan = resume.approved_plan(authority_pin, attempt_pin)
    facts = handoff.at(stage["preflight"], PREFLIGHT)
    contract._obj(facts, ("resources", "ledger", "ports_free"), "facts")
    _need(type(facts["resources"]) is dict and facts["ports_free"] is True
          and _same(facts["ledger"], plan["evidence"]["ledger"]), "ledger")
    closure = activation.verify_result(stage["activation"], stage["admission"], authority_pin, attempt_pin,
                                       began_ns=began_ns, expected_parent=worker_identity, resume=True)
    _need(_same(stage["closure"], closure), "activation")
    for pin in (stage_pin, authority_pin, attempt_pin, authority["proposal"], authority["plan"],
                plan["operation_source"], plan["handoff_source"], plan["review_source"],
                stage["preflight"], stage["admission"], stage["activation"], *closure.values()):
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
    _need(_same(request["version"], 1) and request["scope"] == resume.OPERATION_SCOPE
          and request["parent"]["pid"] == os.getppid(), "request")
    _identity(os.getppid(), request["parent"])
    wait_until = _budget(request["began_ns"], ACTIVATION_BUDGET) + 5 * NS
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
    _budget(request["began_ns"], ACTIVATION_BUDGET)
    return pin, request, worker


def execute(authority_pin, *, began_ns=None):
    """Consume one resume grant and supervise activation of its existing guest."""
    if began_ns is None:
        began_ns = time.monotonic_ns()
    _need(os.name == "nt" and Path.cwd() == ROOT
          and all(Path(os.environ.get(key, "")) == Path("D:/Dev/_Temp")
                  for key in ("TEMP", "TMP", "TMPDIR")), "environment")
    _budget(began_ns, ACTIVATION_BUDGET)
    _need(not any(key in os.environ for key in (handoff.HANDOFF_ENV, contract.RESUME_HANDOFF_ENV)), "environment")
    attempt_pin = resume.begin_attempt(authority_pin)
    result = dict(version=1, scope=resume.OPERATION_SCOPE, authority=authority_pin, attempt=attempt_pin,
                  supervisor=None, stages=None, passed=False, reason=None, feature_acceptance=False)
    try:
        _budget(began_ns, ACTIVATION_BUDGET)
        parent = _identity(os.getpid())
        _need(parent["executable"] == sys.executable, "identity")
        request = _save(REQUEST, dict(version=1, scope=resume.OPERATION_SCOPE, authority=authority_pin,
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
            pin, _ = _read(resume.AUTHORITY, 16384)
            _need(pin["sha256"] == args[1], "authority")
            return 0 if execute(pin, began_ns=began_ns)["passed"] else 1
    except BaseException:
        pass
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
