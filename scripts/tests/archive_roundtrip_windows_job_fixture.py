"""Opt-in, retained Windows host proof for the archive supervisor stages.

Copyright 2026 LocalLore contributors. SPDX-License-Identifier: Apache-2.0
"""
from ctypes import WinDLL, byref, wintypes
import os
from pathlib import Path
import re
import shutil
import sys
import tempfile
import time
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from benchmarks import archive_roundtrip_supervisor as supervisor

env = supervisor.env
lifecycle = supervisor.lifecycle
handoff = supervisor.handoff
CONTROL_ENV = "LOCALLORE_ARCHIVE_JOB_FIXTURE_ROOT"
TEMP = Path("D:/Dev/_Temp")
PREFIX = "locallore-archive-job-v1-"
LIMIT = 1024 * 1024
RUNTIME_SECONDS = 20
CONTROLLER_SECONDS = 8
OBSERVE_SECONDS = 3
PROOF = "host-proof-v1.json"
RECEIPT = "synthetic-controller-v1.json"
OUTER_JOB = "outer-job-v1.json"
INNER_JOB = "inner-job-v1.json"
ROLES = ("authority", "attempt", "admission")


def require(condition, reason):
    if not condition:
        raise ValueError(reason)


def fixture_root(value):
    root = Path(value)
    require(root.parent == TEMP and re.fullmatch(PREFIX + "[a-z0-9_]{8}", root.name) is not None,
            "fixture_root")
    require(root.resolve(strict=True) == root, "fixture_root")
    return env.safe_path(root, directory=True)


def observe_member(job, pid, expected=None):
    api = supervisor.shared._ProcessApi()
    kernel = WinDLL("kernel32", use_last_error=True)
    in_job = kernel.IsProcessInJob
    in_job.argtypes = (wintypes.HANDLE, wintypes.HANDLE, wintypes.LPBOOL)
    in_job.restype = wintypes.BOOL
    handles = supervisor.process.ProcessHandles(api)
    try:
        handle, identity = handles.add(pid, expected)
        member = wintypes.BOOL()
        require(in_job(handle, job.handle, byref(member)), "fixture_job_query")
        handles.guard()
        return identity, bool(member.value)
    finally:
        require(handles.close() is True, "fixture_identity_cleanup")


def publish_job(root, name, value):
    path = supervisor.output_control.validate_output(str(root / name))
    pending = supervisor.output_control.validate_output(str(path.with_suffix(".pending.json")))
    supervisor._save(pending, value)
    pending.rename(path)


def await_job(root, name, child):
    path = root / name
    until = time.monotonic() + OBSERVE_SECONDS
    while not path.exists():
        require(child.poll() is None and time.monotonic() < until, "fixture_job_wait")
        time.sleep(.02)
    require(time.monotonic() < until and child.poll() is None, "fixture_job_wait")
    _, value = lifecycle._read(path, 4096)
    return value


def bounded(supervise, ceiling, root, *, outer):
    def run(command, barrier, capture, seconds, started):
        # Use the real barrier and Job; retain only the two fixture child PIDs.
        require(ceiling <= seconds and len(barrier) <= 4096, "fixture_budget")
        create_job = env.host.WindowsJob
        job = None

        def observe(pid):
            nonlocal job
            job = create_job(pid)
            return job

        def on_started(child):
            try:
                require(job is not None, "fixture_job_missing")
                identity, member = observe_member(job, child.pid)
                require(member, "fixture_job_assignment")
                if outer:
                    require(started(child) is True, "fixture_started")
                    inner = await_job(root, INNER_JOB, child)
                    supervisor.contract._obj(inner, ("controller", "runtime"), "binding")
                    supervisor.contract._process(inner["controller"])
                    require(supervisor._same(inner["runtime"], identity), "fixture_runtime_identity")
                    controller, nested = observe_member(job, inner["controller"]["pid"], inner["controller"])
                    require(nested, "fixture_controller_outside_outer")
                    publish_job(root, OUTER_JOB, dict(runtime=identity, controller=controller))
                    return True
                runtime, parent_inside = observe_member(job, os.getpid())
                require(not parent_inside, "fixture_runtime_inside_inner")
                publish_job(root, INNER_JOB, dict(controller=identity, runtime=runtime))
                membership = await_job(root, OUTER_JOB, child)
                require(supervisor._same(membership, dict(runtime=runtime, controller=identity)),
                        "fixture_job_nesting")
                return started(child)
            except (OSError, ValueError, KeyError, TypeError) as failure:
                reason = str(failure)
                if not re.fullmatch(r"fixture_[a-z_]{1,42}", reason):
                    reason = type(failure).__name__
                name = ("outer" if outer else "inner") + "-observation-failure-v1.json"
                supervisor._save(root / name, dict(reason=reason))
                raise

        with patch.object(env.host, "WindowsJob", observe):
            return supervise(command, barrier, capture, ceiling, on_started)
    return run


def read_stage(kind):
    pin, _ = lifecycle._read(supervisor._path(kind, "terminal"))
    request, child = supervisor._terminal(kind, pin)
    return dict(terminal=pin, request=request, child=child)


def check_controller(root, runtime, controller):
    request = controller["request"]
    require(supervisor._same_context(request, runtime["request"]) and
            request["parent"] == runtime["child"], "controller_parent")
    require(supervisor._same(lifecycle._at(request["running"], root / "fixture-running-v1.json"),
                             dict(version=1, synthetic=True)), "fixture_running")
    _, receipt = lifecycle._read(root / RECEIPT)
    require(supervisor._same(receipt, dict(version=1, synthetic=True, request=request, member=True)),
            "controller_receipt")
    _, outer = lifecycle._read(root / OUTER_JOB, 4096)
    _, inner = lifecycle._read(root / INNER_JOB, 4096)
    expected = dict(runtime=runtime["child"], controller=controller["child"])
    require(supervisor._same(outer, expected) and supervisor._same(inner, expected), "fixture_job_proof")


def stage(root, mode):
    kind = "controller" if mode == "_controller" else "runtime"
    request = supervisor._enter(kind)
    require(os.getpid() in supervisor.shared._ProcessApi().current_job_pids(), "fixture_job_members")
    if kind == "controller":
        supervisor._save(root / RECEIPT, dict(version=1, synthetic=True, request=request, member=True))
        return
    running = supervisor._save(root / "fixture-running-v1.json", dict(version=1, synthetic=True))
    controller_request = supervisor._request("controller", request["authority"], request["attempt"],
                                             request["admission"], request, running)
    terminal, child = supervisor._supervise(controller_request)
    closed = read_stage("controller")
    require(closed == dict(terminal=terminal, request=controller_request, child=child), "controller_terminal")
    check_controller(root, dict(request=request, child=controller_request["parent"]), closed)


def check_inventory(root, proof):
    records = {RECEIPT, OUTER_JOB, INNER_JOB, "fixture-running-v1.json"}
    records.update(f"fixture-{role}-v1.json" for role in ROLES)
    records.update(supervisor._path(kind, name).name for kind in supervisor.STAGES
                   for name in ("request", "started", "terminal"))
    captures = {supervisor._capture(kind).name for kind in supervisor.STAGES}
    require({item.name for item in root.iterdir()} == records | captures, "fixture_roster")
    size = sum(env.safe_path(root / name).stat().st_size for name in records)
    for name in captures:
        capture = env.safe_path(root / name, directory=True)
        require({item.name for item in capture.iterdir()} == set(env.LiveOutput.names), "fixture_roster")
        size += sum(env.safe_path(capture / stream).stat().st_size for stream in env.LiveOutput.names)
    require(size + len(env.encoded(proof)) <= LIMIT, "fixture_budget")


def host_check(root):
    pins = {
        role: supervisor._save(root / f"fixture-{role}-v1.json", dict(version=1, synthetic=True, role=role))
        for role in ROLES
    }
    now = time.monotonic_ns()
    window = dict(began_ns=now, until_ns=now + handoff.MAX_SECONDS * handoff.NS)
    request = supervisor._request("runtime", *(pins[role] for role in ROLES), window, None)
    terminal, child = supervisor._supervise(request)
    runtime = read_stage("runtime")
    require(runtime == dict(terminal=terminal, request=request, child=child), "runtime_terminal")
    controller = read_stage("controller")
    check_controller(root, runtime, controller)
    proof = dict(version=1, synthetic=True, runtime=runtime, controller=controller)
    for role, pin in pins.items():
        require(supervisor._same(lifecycle._at(pin, root / f"fixture-{role}-v1.json"),
                                 dict(version=1, synthetic=True, role=role)), "fixture_input")
    check_inventory(root, proof)
    supervisor._save(root / PROOF, proof)


def main():
    args = sys.argv[1:]
    require(os.name == "nt" and TEMP.resolve(strict=True) == TEMP, "fixture_platform")
    if args == ["--host-check"]:
        require(CONTROL_ENV not in os.environ and shutil.disk_usage(TEMP).free >= LIMIT, "fixture_admission")
        root = fixture_root(tempfile.mkdtemp(prefix=PREFIX, dir=TEMP))
        # Print the retained root even if a stage later refuses.
        print(root, flush=True)
    else:
        require(args in [["_runtime"], ["_controller"]] and CONTROL_ENV in os.environ, "fixture_entry")
        root = fixture_root(os.environ[CONTROL_ENV])
    with (patch.dict(os.environ, {CONTROL_ENV: str(root)}),
          patch.object(supervisor.admission, "CONTROL", root),
          patch.object(supervisor, "__file__", str(Path(__file__).resolve())),
          patch.object(env, "supervise_operation", bounded(env.supervise_operation, RUNTIME_SECONDS, root, outer=True)),
          patch.object(env, "supervise", bounded(env.supervise, CONTROLLER_SECONDS, root, outer=False))):
        if args == ["--host-check"]:
            host_check(root)
        else:
            stage(root, args[0])


if __name__ == "__main__":
    main()
