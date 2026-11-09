"""One approved SDK19 preparation and test under a single Windows Job.

The operator consumes reviewed records. It never creates human approval.
Copyright 2026 LocalLore contributors. SPDX-License-Identifier: Apache-2.0
"""
import math
import os
from pathlib import Path, PureWindowsPath
import re
import subprocess
import sys
import time
import uuid

ROOT = Path(__file__).parents[1]
if __package__ in (None, ""):
    sys.path.insert(0, str(ROOT))

from benchmarks import adb_held_socket_probe as probe
from benchmarks import archive_ui_build as files
from benchmarks import isolated_adb_lease as server
from benchmarks import isolated_adb_owner as process
from benchmarks import owned_record_large_text_ui_contract as contract
from benchmarks import receipt_avd_environment as env
from benchmarks import receipt_avd_storage as storage
from benchmarks import record_large_text_ui_activation as activation
from benchmarks import runtime_spike as host

OUT = Path("D:/Dev/Experiments/LocalLore/2026-11-09-record-large-text-operation-v1")
PROPOSAL = OUT / "PROPOSED_OPERATION.md"
PLAN = OUT / "plan-v1.json"
AUTHORITY = OUT / "human-authority-v1.json"
PREPARE = OUT / "prepare-proposal-v1.json"
LIVE = OUT / "attempt-v1"
CLAIM = LIVE / "claim-v1.json"
GUEST = Path(contract.GUEST_ROOT)
LEDGER = storage.DEFAULT_REGISTRY / "ledger-v1.json"
SCOPE = "sdk19-prepare-and-one-record-large-text-run-v1"
PLAN_SCOPE = "sdk19-record-large-text-plan-v1"
SECONDS = 2400
BARRIER = b"sdk19-record-large-text-operation-v1\n"
_need = env.require
_same = contract._same
_read = activation._read
_at = activation._at
_save = activation._save


def _pin(pin, path, cap):
    contract.binding(pin, max_bytes=cap)
    _need(pin["path"] == str(path) and pin["bytes"] > 0, "binding")


def validate_authority(value):
    contract._obj(value, ("version", "scope", "proposal", "plan", "ledger", "approval_reference",
                          "allow_sdk_prepare", "allow_one_boot", "allow_model", "allow_retirement",
                          "max_operation_seconds"), "authority")
    ref = value["approval_reference"]
    _need(type(value["version"]) is int and value["version"] == 1 and value["scope"] == SCOPE
          and type(ref) is str and 0 < len(ref) <= 256 and ref.strip() == ref
          and all(32 <= ord(c) <= 126 for c in ref)
          and value["allow_sdk_prepare"] is True and value["allow_one_boot"] is True
          and value["allow_model"] is False and value["allow_retirement"] is False
          and type(value["max_operation_seconds"]) is int and value["max_operation_seconds"] == SECONDS,
          "authority")
    for role, path, cap in (("proposal", PROPOSAL, 65536), ("plan", PLAN, 131072),
                            ("ledger", LEDGER, 16 * 1024**2)):
        _pin(value[role], path, cap)
    return value


def _authority(pin):
    value = validate_authority(_at(pin, AUTHORITY, 16384))
    lines = files._bound(value["proposal"], cap=65536).decode("utf-8").splitlines()
    for label, role in (("Plan SHA-256", "plan"), ("Ledger SHA-256", "ledger")):
        expected = label + " " + value[role]["sha256"]
        _need([line for line in lines if line.startswith(label)] == [expected], "authority")
    _at(value["plan"], PLAN, 131072)
    env.check_binding(pin)
    return value


def _check_sources(value):
    contract._sources(value["sources"])
    _need(_same(value["sources"], contract.source_bindings())
          and _same(value["python"], probe._python_bindings()), "source")
    contract.verify_artifacts(value["artifacts"])


def _plan(pin):
    value = _at(pin, PLAN, 131072)
    contract._obj(value, ("version", "scope", "source_root", "sources", "python", "artifacts",
                          "prepare", "installed", "execution_authorized", "model_material"), "plan")
    _need(type(value["version"]) is int and value["version"] == 1 and value["scope"] == PLAN_SCOPE
          and value["source_root"] == str(ROOT) and value["execution_authorized"] is False
          and value["model_material"] is False, "plan")
    _check_sources(value)
    installed = value["installed"]
    contract._obj(installed, ("adb", "tools", "emulator", "qemu", "refuser", "refuser_source",
                              "auth_key_path", "capabilities", "source_review", "compatibility"), "installed")
    prepare = _at(value["prepare"], PREPARE, 16 * 1024**2)
    env.validate_proposal(prepare, "prepare")
    _need(prepare["paths"]["root"] == str(GUEST) and _same(prepare["memory_mib"], 8192)
          and _same(prepare["cores"], 4) and prepare["adb_path"] == installed["adb"]["path"], "profile")
    env.check_binding(pin)
    return value, prepare


def _server(plan, run_id):
    installed = plan["installed"]
    return dict(version=1, protocol=server.PROTOCOL, run_id=run_id,
                root=str(activation.RUNTIME / "owned-v1/server"), port=contract.PORT,
                seconds=activation.OWNER_SECONDS, adb=installed["adb"], tools=installed["tools"],
                sdk_version=server.SDK_VERSION, expected_version="0029", python=plan["python"],
                auth_key=installed["auth_key_path"], capabilities=installed["capabilities"],
                source_review=installed["source_review"],
                sources=[pin for pin in plan["sources"]
                         if PureWindowsPath(pin["path"]).name in server.SOURCE_NAMES | {"__init__.py"}])


def _preflight(authority, plan, prepare):
    for path in (GUEST, activation.RUNTIME):
        env.safe_path(path, exists=False)
        _need(not os.path.lexists(path), "already_used")
    env.safe_path(GUEST.parent, directory=True)
    ledger = _at(authority["ledger"], LEDGER, 16 * 1024**2)
    storage._validate(ledger, storage.DEFAULT_REGISTRY)
    _need(type(ledger["version"]) is int and ledger["version"] == 2, "ledger")
    preview = storage.preview_prepare(GUEST)
    _need(preview["would_fit"] is True and preview["admission_granted"] is False, "storage_capacity")
    installed = plan["installed"]
    server.revalidate_inputs(_server(plan, "0" * 32))
    for role in ("emulator", "qemu", "refuser", "refuser_source", "compatibility"):
        contract.binding(installed[role], project=role not in ("emulator", "qemu"), max_bytes=256 * 1024**2)
        env.check_binding(installed[role])
    sdk = Path(prepare["sdk"])
    _need(installed["emulator"]["path"] == str(sdk / "emulator/emulator.exe")
          and installed["qemu"]["path"] == str(sdk / "emulator/qemu/windows-x86_64/qemu-system-x86_64-headless.exe")
          and Path(installed["refuser"]["path"]).suffix.lower() == ".exe"
          and Path(installed["compatibility"]["path"]).suffix == ".md"
          and _same(installed["refuser_source"], env.binding(ROOT / "benchmarks/native/deny_adb_client.c")),
          "installed")
    env.verify_installation(prepare)
    env.check_external_state(prepare)
    env.resource_facts(prepare)
    env.ports_free()
    private = process._exclusive_preflight(activation.owner_mechanisms._ProcessApi(), port=contract.PORT)
    _need(private["exclusive_bind_succeeded"] is True and private["closed_mask"] == 1, "ports_unavailable")
    env.check_binding(authority["ledger"])


def _authorization(phase, proposal):
    return dict(version=1, phase=phase, proposal_sha256=proposal["sha256"],
                allow_environment_calls=True, root_go_pending=False)


def _create_admission(plan):
    run_proposal = LIVE / "run-proposal-v1.json"
    proposal = env.plan_run(plan["prepare"]["path"], GUEST / "prepared-v1.json", run_proposal, max_seconds=1800)
    proposal_pin, saved = _read(run_proposal, 16 * 1024**2)
    _need(_same(saved, proposal) and _same(proposal["prepare_proposal"], plan["prepare"]), "proposal")
    run_auth = _save(LIVE / "run-authorization-v1.json", _authorization("run", proposal_pin))
    installed = plan["installed"]
    run_id = uuid.uuid4().hex
    guest = dict(root=str(GUEST), proposal=proposal_pin, authorization=run_auth,
                 emulator=installed["emulator"], qemu=installed["qemu"], refuser=installed["refuser"],
                 refuser_source=installed["refuser_source"], console_port=5592, adb_port=5593,
                 serial="emulator-5592", memory_mib=8192, cores=4, max_seconds=1800, api=35, abi="x86_64")
    admission = dict(version=1, protocol=contract.PROTOCOL, run_id=run_id, root=str(activation.RUNTIME / "owned-v1"),
                     seconds=activation.OWNER_SECONDS, server=_server(plan, run_id), guest=guest,
                     artifacts=plan["artifacts"], sources=plan["sources"], python=plan["python"],
                     compatibility=installed["compatibility"])
    contract.revalidate_inputs(contract.validate_admission(admission))
    activation.RUNTIME.mkdir()
    pin = _save(activation.ADMISSION, admission)
    _need(_same(activation._inputs(pin, fresh=True), admission), "admission")
    return pin


def _accept_activation(value, admission_pin):
    _pin(admission_pin, activation.ADMISSION, 2 * 1024**2)
    pin, saved = _read(activation.CONTROL / "activation-result-v1.json")
    _need(_same(saved, value), "activation")
    contract._obj(saved, ("version", "scope", "admission", "passed", "supervisor", "runtime",
                          "feature_acceptance"), "activation")
    _need(type(saved["version"]) is int and saved["version"] == 1 and saved["scope"] == activation.SCOPE
          and saved["passed"] is True and saved["feature_acceptance"] is False
          and _same(saved["admission"], admission_pin), "activation")
    runtime = _at(saved["runtime"], activation.CONTROL / "runtime-result-v1.json")
    _need(runtime["passed"] is True and runtime["feature_acceptance"] is False
          and _same(runtime["admission"], admission_pin), "activation")
    supervisor = _at(saved["supervisor"], activation.CONTROL / "runtime-supervisor-v1.json")
    _need(process._owner_ok(supervisor, activation.CONTROL / "runtime-capture-v1"), "cleanup")
    closure = runtime["closure"]
    contract._obj(closure, ("owner", "closure", "ledger"), "closure")
    owned = activation.RUNTIME / "owned-v1"
    _pin(closure["owner"], owned / "result-v1.json", 2 * 1024**2)
    _pin(runtime["controller"], owned / "controller-v1/controller-result-v1.json", 2 * 1024**2)
    proof = _at(closure["closure"], GUEST / "guest-storage-closure-v1.json")
    ledger_pin, entry = activation._ledger(GUEST)
    _need(_same(closure["ledger"], ledger_pin) and entry["state"] == "closed"
          and entry["recovery"] is None and entry["retirement"] is None
          and _same(closure["closure"], entry["closure"]) and _same(proof["admission"], admission_pin)
          and proof["closure_verified"] is True and proof["cleanup_complete"] is True
          and proof["proposal_sha256"] == entry["proposal_sha256"], "closure")
    for bound in (pin, saved["runtime"], saved["supervisor"], runtime["controller"], *closure.values()):
        env.check_binding(bound)
    return pin, ledger_pin


def _attempt_value(authority_pin):
    return dict(version=1, scope=SCOPE, authority=authority_pin, no_retry=True)


def _verify_attempt(attempt_pin, authority_pin):
    _need(_same(_at(attempt_pin, CLAIM, 16384), _attempt_value(authority_pin)), "attempt")


def _budget(begin, minimum=0):
    now = time.monotonic()
    _need(type(begin) in (int, float) and math.isfinite(begin) and 0 <= now - begin < SECONDS
          and now - begin + minimum <= SECONDS, "budget")


def _reason(error):
    if type(error) is KeyboardInterrupt:
        return "cancelled"
    if type(error) in (env.EnvironmentRefused, storage.StorageRefused):
        args = error.args
        if len(args) == 1 and type(args[0]) is str and args[0] in {
            "already_used", "authority", "binding", "budget", "host_capacity", "host_commit_capacity",
            "host_commit_unavailable", "ports_unavailable", "storage_capacity", "registry_locked", "source",
            "storage_capacity_exceeded", "storage_storage_capacity_exceeded", "storage_registry_locked",
        }:
            return args[0]
    return "operation_refused"


def _run_stages(authority_pin, attempt_pin, begin):
    result = dict(version=1, scope=SCOPE, authority=authority_pin, attempt=attempt_pin,
                  phase="initial", step="authority", passed=False, admission=None, activation=None,
                  ledger=None, reason=None, feature_acceptance=False)
    try:
        authority = _authority(authority_pin)
        _verify_attempt(attempt_pin, authority_pin)
        result.update(phase="preflight", step="readiness")
        _budget(begin, 2100)
        plan, prepare = _plan(authority["plan"])
        _preflight(authority, plan, prepare)
        _budget(begin, 2100)
        _need(_same(_authority(authority_pin), authority), "authority")
        _verify_attempt(attempt_pin, authority_pin)
        _check_sources(plan)
        env.check_binding(plan["prepare"])
        env.check_binding(authority["ledger"])
        result.update(phase="prepare", step="prepare_dispatch")
        prepare_auth = _save(LIVE / "prepare-authorization-v1.json", _authorization("prepare", plan["prepare"]))
        _budget(begin, 2100)
        env.prepare(plan["prepare"]["path"], prepare_auth["path"])
        result.update(phase="run_inputs", step="create_admission")
        _budget(begin, 1900)
        _need(_same(_authority(authority_pin), authority) and _same(_plan(authority["plan"]), (plan, prepare)), "binding")
        _verify_attempt(attempt_pin, authority_pin)
        admission = _create_admission(plan)
        result.update(admission=admission, phase="activation", step="activation_dispatch")
        _budget(begin, 1800)
        final, ledger = _accept_activation(activation.execute(admission), admission)
        _need(_same(_authority(authority_pin), authority), "authority")
        _verify_attempt(attempt_pin, authority_pin)
        _budget(begin)
        result.update(passed=True, phase="completed", step="completed", activation=final, ledger=ledger)
    except BaseException as error:
        result.update(passed=False, reason=_reason(error))
    _save(LIVE / "stage-result-v1.json", result)
    return result


def _supervise(request_pin, begin):
    child = job = capture = worker = captures = None
    closed = drained = False
    status = "spawn_failed"
    try:
        _budget(begin)
        capture = process.ServerCapture(LIVE / "worker-capture-v1")
        child = subprocess.Popen([sys.executable, "-I", "-S", "-B", str(Path(__file__)), "_worker"],
                                 stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                                 bufsize=0, creationflags=subprocess.CREATE_NO_WINDOW)
        job = host.WindowsJob(child.pid)
        capture.start(child)
        worker = activation._identity(child.pid)
        _need(worker["executable"] == sys.executable, "identity")
        _save(LIVE / "worker-started-v1.json", dict(request=request_pin, worker=worker))
        _budget(begin)
        child.stdin.write(BARRIER + env.encoded(request_pin))
        child.stdin.close()
        status = "running"
        while time.monotonic() - begin < SECONDS:
            capture.guard()
            if child.poll() is not None:
                status = "child_exited"
                break
            time.sleep(.05)
        if status == "running":
            status = "expired"
    except BaseException as error:
        status = "cancelled" if type(error) is KeyboardInterrupt else "owner_failed"
    finally:
        if child is not None:
            try:
                if job is not None:
                    closed = job.close() is True
                else:
                    child.kill()
            except BaseException:
                closed = False
            try:
                child.wait(timeout=5)
                child.stdin.close()
            except BaseException:
                closed = False
        if capture is not None:
            try:
                capture_closed = capture.close() is True
                drained = capture_closed and child is not None and len(capture.readers) == 2
                if drained:
                    captures = activation._capture_pins(LIVE / "worker-capture-v1")
            except BaseException:
                drained = False
            if child is not None and not capture.pipes:
                for stream in (child.stdout, child.stderr):
                    try:
                        stream.close()
                    except BaseException:
                        closed = False
    return dict(status=status, worker_returncode=child.returncode if child is not None else None,
                cleanup_complete=closed and drained, capture_complete=drained, worker=worker, captures=captures,
                elapsed_ms=round(max(0, time.monotonic()-begin) * 1000))


def _worker():
    raw = sys.stdin.buffer.read(131073)
    _need(len(raw) <= 131072 and raw.startswith(BARRIER), "barrier")
    request_pin = env.decode_json(raw[len(BARRIER):])
    request = _at(request_pin, LIVE / "worker-request-v1.json")
    contract._obj(request, ("version", "scope", "authority", "attempt", "parent", "begin"), "request")
    _need(type(request["version"]) is int and request["version"] == 1 and request["scope"] == SCOPE
          and request["parent"]["pid"] == os.getppid(), "request")
    activation._identity(os.getppid(), request["parent"])
    _, started = _read(LIVE / "worker-started-v1.json")
    contract._obj(started, ("request", "worker"), "request")
    _need(_same(started["request"], request_pin), "request")
    worker = activation._identity(os.getpid(), started["worker"])
    _budget(request["begin"])
    _save(LIVE / "worker-claim-v1.json", dict(request=request_pin, worker=worker))
    return 0 if _run_stages(request["authority"], request["attempt"], request["begin"])["passed"] else 1


def execute(authority_pin, begin=None):
    if begin is None:
        begin = time.monotonic()
    _need(os.name == "nt" and Path.cwd() == ROOT and ROOT.resolve(strict=True) == ROOT
          and all(Path(os.environ.get(key, "")) == Path("D:/Dev/_Temp")
                  for key in ("TEMP", "TMP", "TMPDIR")), "environment")
    _authority(authority_pin)
    _budget(begin, 2100)
    env.safe_path(LIVE, exists=False)
    LIVE.mkdir()
    attempt = _save(CLAIM, _attempt_value(authority_pin))
    result = dict(version=1, scope=SCOPE, authority=authority_pin, attempt=attempt, owner=None,
                  stages=None, passed=False, reason=None, feature_acceptance=False)
    try:
        parent = activation._identity(os.getpid())
        _need(parent["executable"] == sys.executable, "identity")
        request = _save(LIVE / "worker-request-v1.json", dict(version=1, scope=SCOPE,
                        authority=authority_pin, attempt=attempt, parent=parent, begin=begin))
        owner = _supervise(request, begin)
        result["owner"] = _save(LIVE / "outer-owner-result-v1.json", owner)
        _need(owner["status"] == "child_exited" and type(owner["worker_returncode"]) is int
              and owner["worker_returncode"] == 0 and owner["cleanup_complete"] is True
              and owner["capture_complete"] is True, "owner")
        contract._process(owner["worker"])
        contract._obj(owner["captures"], ("stdout", "stderr"), "capture")
        for channel, pin in owner["captures"].items():
            path = LIVE / "worker-capture-v1" / ("owner-" + channel + "-v1.bin")
            _need(pin["path"] == str(path) and files._bound(pin, cap=process.CAP) == b"", "capture")
        expected = dict(request=request, worker=owner["worker"])
        for name in ("worker-started-v1.json", "worker-claim-v1.json"):
            _need(_same(_read(LIVE / name)[1], expected), "worker")
        stage_pin, stage = _read(LIVE / "stage-result-v1.json")
        _need(stage["passed"] is True and stage["feature_acceptance"] is False
              and stage["scope"] == SCOPE and stage["phase"] == stage["step"] == "completed"
              and _same(stage["authority"], authority_pin) and _same(stage["attempt"], attempt), "stage")
        activation_value = _at(stage["activation"], activation.CONTROL / "activation-result-v1.json")
        _need(_same(_accept_activation(activation_value, stage["admission"]),
                    (stage["activation"], stage["ledger"])), "activation")
        _authority(authority_pin)
        _verify_attempt(attempt, authority_pin)
        env.check_binding(stage_pin)
        _budget(begin)
        result.update(passed=True, stages=stage_pin)
    except BaseException as error:
        result.update(passed=False, reason=_reason(error))
    _save(LIVE / "operation-result-v1.json", result)
    return result


def main(argv=None):
    begin = time.monotonic()
    args = sys.argv[1:] if argv is None else argv
    try:
        if args == ["_worker"]:
            return _worker()
        if len(args) == 2 and args[0] == "--authority-sha256" and re.fullmatch("[0-9a-f]{64}", args[1]):
            pin, _ = _read(AUTHORITY, 16384)
            _need(pin["sha256"] == args[1], "authority")
            return 0 if execute(pin, begin)["passed"] else 1
    except BaseException:
        pass
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
