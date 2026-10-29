"""Bounded, private cost observations of fixed CLOSED restart validators.

This is not a target lease or an acceptance reader. It cannot execute a device
recipe. The only controller-result phase requires the preserved refused result;
it measures that early refusal, not the unvisited successful-result graph.
Copyright 2026 LocalLore contributors. SPDX-License-Identifier: Apache-2.0
"""
import argparse
import contextlib
import copy
import hashlib
import os
from pathlib import Path
import re
import sys

ROOT = Path(__file__).resolve().parents[1]
if __package__ in (None, ""):
    sys.path.insert(0, str(ROOT))
from benchmarks import receipt_avd_environment as env
from benchmarks import owned_restart_contract as contract
from benchmarks import android_process_verification_v5 as reader
from benchmarks import windows_tcp_control as output_control

SCOPE = "closed-validation-cost-plan-v1"
PHASES = ("inputs", "proof_before", "proof_after", "controller_refusal")
ROLES = frozenset(("admission", "running", "session", "client", "controller_launch",
                   "controller_started", "target_result", "target_started", "controller_result"))
GO = b"LL_CLOSED_PROFILE_V1\n"
CAP = 4 * 1024 * 1024


def need(value, reason):
    if not value:
        raise ValueError(reason)


def metadata(path):
    need(isinstance(path, (str, Path)) and Path(path).suffix.lower() == ".json", "metadata_filename")
    path = env.safe_path(path)
    need(path.drive.upper() == "D:", "physical_D")
    need(0 < path.stat().st_size <= CAP, "metadata_size")
    with path.open("rb") as stream:
        data = stream.read(CAP + 1)
    need(0 < len(data) <= CAP, "metadata_size")
    return dict(path=str(path), bytes=len(data), sha256=hashlib.sha256(data).hexdigest()), data


def pin(path):
    return metadata(path)[0]


def read(binding):
    need(type(binding) is dict and set(binding) == {"path", "bytes", "sha256"}, "binding")
    need(type(binding["path"]) is str and type(binding["bytes"]) is int and 0 <= binding["bytes"] <= CAP and
         type(binding["sha256"]) is str and re.fullmatch("[0-9a-f]{64}", binding["sha256"]) is not None, "binding")
    actual, data = metadata(binding["path"])
    need(actual == binding, "binding_changed")
    return env.decode_json(data)


def same_path(binding, wanted):
    need(Path(binding["path"]) == wanted, "canonical_path")
    return read(binding)


def sources():
    paths = sorted(p for p in (ROOT / "benchmarks").rglob("*") if p.suffix in (".py", ".c"))
    return {str(p.relative_to(ROOT)): env.binding(env.safe_path(p))["sha256"] for p in paths}


def terminal(value, code):
    need(type(value) is dict and value.get("status") == "child_exited" and
         type(value.get("worker_returncode")) is int and value["worker_returncode"] == code and
         value.get("cleanup_complete") is True and value.get("output_capture_complete") is True and
         all(type(value.get(k)) is int and value[k] == 0 for k in ("stderr_bytes", "stdout_bytes")) and
         type(value.get("elapsed_ms")) is int and 0 <= value["elapsed_ms"] <= 2**63 - 1, "not_terminal")


def role_filenames(plan):
    names = dict(admission=r"target-admission-v[1-9][0-9]*\.json", running=r"running-v1\.json",
        session=r"sdk-session-v5\.json", client=r"command-[0-9]{4,5}\.json",
        controller_launch=r"launch-result-v1\.json", controller_started=r"started-v1\.json",
        target_result=r"result-v1\.json", target_started=r"started-v1\.json",
        controller_result=r"controller-result-v1\.json")
    for role in ROLES:
        binding = plan[role]
        need(type(binding) is dict and set(binding) == {"path", "bytes", "sha256"} and
             type(binding["path"]) is str and
             re.fullmatch(names[role], Path(binding["path"]).name, flags=re.IGNORECASE) is not None, "canonical_path")


def existing_output(path):
    """Reuse the missing-output validator on a child without creating that child."""
    path = env.safe_path(path, directory=True)
    output_control.validate_output(str(path / "profile-worker-output-guard-v1"))
    return path


def prepare(plan):
    """Join canonical closed files and independent started identities BEFORE timing."""
    need(type(plan) is dict and set(plan) == ROLES | {"version", "scope"} and
         type(plan["version"]) is int and plan["version"] == 1 and plan["scope"] == SCOPE, "plan")
    role_filenames(plan)
    values = {role: read(plan[role]) for role in ROLES}
    admission = contract.validate_admission(values["admission"])
    running = contract.validate_running(values["running"], admission, plan["admission"])
    session = contract.validate_session(values["session"], admission)
    case_root = Path(session["root"])
    target_root = Path(admission["root"])
    launch_root = Path(plan["controller_launch"]["path"]).parent
    need(not case_root.is_relative_to(ROOT) and not target_root.is_relative_to(ROOT), "under_Git")
    for role, expected in (("running", target_root / "running-v1.json"),
                           ("session", case_root / contract.SESSION_FILE),
                           ("controller_result", case_root / "controller-result-v1.json"),
                           ("controller_started", launch_root / "started-v1.json"),
                           ("controller_launch", launch_root / "launch-result-v1.json"),
                           ("target_result", target_root / "result-v1.json"),
                           ("target_started", target_root / "started-v1.json")):
        need(Path(plan[role]["path"]) == expected, "canonical_path")
    launch, started = values["controller_launch"], values["controller_started"]
    need(launch["started"] == plan["controller_started"] and started["request"] == launch["request"] and
         launch["controller_result"] == plan["controller_result"] and launch["passed"] is False and
         launch["process_handles_closed"] is True and launch["sources_equal"] is True, "launch")
    terminal(launch["owner"], 1)
    need(same_path(pin(launch_root / "owner-result-v1.json"), launch_root / "owner-result-v1.json") == launch["owner"], "owner")
    request = same_path(launch["request"], launch_root / "launch-request-v1.json")
    need(request["admission"] == plan["admission"] and request["running"] == plan["running"] and
         Path(request["controller_root"]) == case_root, "launch_binding")
    contract._process(started["worker"])
    need(session["caller"] == started["worker"] and session["running"] == plan["running"] and
         session["descriptor"] == running, "caller")
    target, target_started = values["target_result"], values["target_started"]
    need(target["admission"] == plan["admission"] and target["started"] == plan["target_started"] and
         target_started["request"] == target["request"] and target["qualified_target"] is True and
         target["reason"] == "stop_requested", "target")
    terminal(same_path(target["owner"], target_root / "owner-result-v1.json"), 0)
    target_request = same_path(target["request"], target_root / "request-v1.json")
    worker = same_path(target["worker_result"], target_root / "worker-result-v1.json")
    need(target_started["worker"] == worker["worker"] == running["worker"] and
         target_request["owner"] == running["owner"] and worker["reason"] == "stop_requested" and
         worker["stop_requested"] is True and set(worker["cleanup"]) == set(contract.CLEANUP_KEYS) and
         all(v is True for v in worker["cleanup"].values()), "target_closed")
    need(started["worker"] != target_started["worker"], "independent_workers")
    result = values["controller_result"]
    need(result["outcome"] == "refused" and result["phase"] == "death" and
         result["reason"] == "resource_uncertain" and result["observer_handles_closed"] is True and
         result["session"] == plan["session"] and result["feature_acceptance"] is False, "refusal_only")
    record = contract.validate_client_record(values["client"], session)
    need(Path(plan["client"]["path"]) == case_root / "clients" / ("command-%04d.json" % record["index"]) and
         record["session"] == plan["session"] and record["index"] == result["client_count"], "client")
    proofs = {}
    for phase in ("before", "after"):
        binding = record["server_" + phase]
        expected = case_root / "proofs" / ("command-%04d-%s.json" % (record["index"], phase))
        need(type(binding) is dict and Path(binding["path"]) == expected, "canonical_path")
        context = dict(index=record["index"], phase=phase, label=record["label"],
                       operation_sha256=record["operation_sha256"], transport_id=record["transport_id"])
        proof = read(binding)
        need(type(proof["queries"]) is dict and Path(proof["queries"]["path"]) ==
             expected.with_name(expected.stem + "-queries-v1.json"), "canonical_path")
        read(proof["queries"])  # Same strict shape and bounded bytes as top-level metadata.
        need(proof["caller"] == started["worker"] and proof["context"] == context and
             proof["session"] == plan["session"], "proof_caller")
        proofs[phase] = (binding, context, proof["queries"])
    return dict(admission=admission, session=session, running=running,
                caller=started["worker"], proofs=proofs)


def input_pins(admission):
    """Explicit inventory; never recurse into model, APK, auth or guest-image pins."""
    a = admission
    result = list(a["sources"]) + list(a["server"]["sources"]) + list(a["server"]["tools"])
    result += [p for p in a["python"].values() if p is not None]
    result += [a["server"]["source_review"], a["compatibility"], a["server"]["capabilities"]]
    capabilities = read(a["server"]["capabilities"])
    result += [row["stdout"] for row in capabilities["rows"]]
    result += [a["guest"][k] for k in ("proposal", "authorization", "emulator", "qemu", "refuser", "refuser_source")]
    result += [a["artifacts"]["probe"], a["artifacts"]["process_probe_source"]]
    by_path = {}
    for binding in result:
        path = str(env.safe_path(binding["path"]))
        need(path not in by_path or by_path[path] == binding, "conflicting_pin")
        by_path[path] = binding
    return by_path


class ReadObserver:
    """Python audit events only: not an OS sandbox or a measurement of disk IO."""
    DENIED = frozenset(("subprocess.Popen", "os.system", "os.exec", "os.posix_spawn",
                       "socket.__new__", "socket.connect", "os.remove", "os.rename",
                       "os.mkdir", "os.rmdir", "os.truncate", "os.link", "os.symlink", "os.chmod",
                       "os.fork", "os.forkpty", "os.chdir", "os.utime", "os.chown"))

    def __init__(self):
        self.active = False
        self.allowed = {}
        self.counts = {}
        self.violation = False
        self.failed = False

    def event(self, event, args):
        if not self.active:
            return
        try:
            need(event not in self.DENIED and not event.startswith(("socket.", "os.startfile", "os.posix_spawn")), "side_effect")
            if event == "open":
                path, mode, flags = args
                need(type(path) is str and os.path.isabs(path), "read_path")
                key = os.path.normcase(os.path.normpath(path))
                write = sum(getattr(os, n, 0) for n in ("O_WRONLY", "O_RDWR", "O_CREAT", "O_TRUNC", "O_APPEND", "O_TEMPORARY"))
                need(mode in (None, "r", "rb") and type(flags) is int and not flags & write and key in self.allowed, "read_not_admitted")
                self.counts[key] = self.counts.get(key, 0) + 1
        except BaseException:
            self.violation = True
            self.failed = True
            raise

    @contextlib.contextmanager
    def observe(self, allowed):
        need(not self.active and not self.failed, "observer_active")
        self.allowed = {os.path.normcase(os.path.normpath(k)): v for k, v in allowed.items()}
        self.counts, self.violation = {}, False
        self.active = True
        try:
            yield
        finally:
            self.active = False

    def snapshot(self):
        need(not self.active and not self.violation and not self.failed, "observer_failed")
        rows = [dict(binding=self.allowed[key], read_open_calls=count,
                     declared_size_times_opens=self.allowed[key]["bytes"] * count)
                for key, count in sorted(self.counts.items())]
        return dict(scope="python-read-open-observation-v1", rows=rows,
                    read_open_calls=sum(self.counts.values()),
                    declared_size_times_opens=sum(row["declared_size_times_opens"] for row in rows),
                    actual_OS_bytes_measured=False)


def action(phase, plan, case):
    need(phase in PHASES, "phase")
    if phase == "inputs":
        contract.revalidate_inputs(copy.deepcopy(case["admission"]))
        return "returned"
    if phase.startswith("proof_"):
        binding, context, _ = case["proofs"][phase.removeprefix("proof_")]
        reader.verify_proof(binding, case["session"], context)
        return "returned"
    need(phase == "controller_refusal", "phase")
    try:
        reader.verify_controller_result(plan["controller_result"], case["admission"], plan["admission"], plan["running"], case["caller"])
    except contract.TargetRefused as error:
        need(str(error) == "capability", "unexpected_refusal")
        return "refused_capability"
    raise ValueError("expected_refusal_missing")


def worker(output, request_sha):
    need(Path.cwd() == ROOT and ROOT.drive.upper() == "D:", "physical_D_cwd")
    output = existing_output(output)
    need(output.drive.upper() == "D:" and not output.is_relative_to(ROOT), "output")
    need(sys.stdin.buffer.read(len(GO)) == GO, "barrier")
    request_pin = pin(output / "request-v1.json")
    need(request_pin["sha256"] == request_sha, "request_changed")
    request = read(request_pin)
    need(set(request) == {"version", "scope", "plan", "sources", "output", "repeat", "seconds"} and
         type(request["version"]) is int and request["version"] == 1 and
         request["scope"] == "closed-validation-profile-owner-v1" and request["output"] == str(output) and
         type(request["repeat"]) is int and 1 <= request["repeat"] <= 3 and
         type(request["seconds"]) is int and request["seconds"] == 180, "request")
    need(request["sources"] == sources(), "source_changed")
    plan = read(request["plan"])
    case = prepare(plan)
    all_inputs = input_pins(case["admission"])
    frozen = dict(all_inputs)
    frozen.update({plan[role]["path"]: plan[role] for role in ROLES})
    for binding, _, queries in case["proofs"].values():
        frozen.update({binding["path"]: binding, queries["path"]: queries})
    def check_frozen():
        for binding in frozen.values():
            if Path(binding["path"]).suffix.lower() == ".json":
                need(pin(binding["path"]) == binding, "binding_changed")
            else:
                env.check_binding(binding)
    check_frozen()
    # Resolve the already-loaded interpreter DLL location before audit/profiling.
    # The unchanged inputs phase repeats its own lookup; no former PID is queried.
    contract.revalidate_inputs(copy.deepcopy(case["admission"]))
    from benchmarks.validation_profile_stats import ProfileCapture
    observer = ReadObserver()
    sys.addaudithook(observer.event)
    rows = []
    for phase in PHASES:
        allowed = dict(all_inputs) if phase in ("inputs", "controller_refusal") else {}
        bindings = [plan["session"]]
        if phase.startswith("proof_"):
            binding, _, queries = case["proofs"][phase.removeprefix("proof_")]
            bindings += [binding, queries]
        if phase == "controller_refusal":
            bindings += [plan["controller_result"]]
        allowed.update({p["path"]: p for p in bindings})
        for iteration in range(request["repeat"]):
            with ProfileCapture() as sample:
                with observer.observe(allowed):
                    observed = action(phase, plan, case)
            rows.append(dict(phase=phase, iteration=iteration + 1, observed=observed,
                             costs=sample.snapshot(), reads=observer.snapshot()))
    check_frozen()
    need(prepare(read(request["plan"])) == case and request["sources"] == sources(), "input_or_source_changed")
    env.check_binding(request_pin)
    env.create_json(output / "profile-v1.json", dict(version=1, scope="closed-validation-profile-v1",
        request=request_pin, rows=rows, unique_input_files=len(all_inputs),
        unique_declared_input_bytes=sum(p["bytes"] for p in all_inputs.values()),
        original_runtime_requalified=False, feature_acceptance=False, profiling_overhead_included=True))


def run(plan_path, plan_sha, output, repeat):
    need(type(repeat) is int and 1 <= repeat <= 3, "repeat")
    need(re.fullmatch("[0-9a-f]{64}", plan_sha) is not None, "plan_sha")
    env.safe_path(ROOT, directory=True)
    need(Path.cwd() == ROOT and ROOT.drive.upper() == "D:", "physical_D_cwd")
    output = output_control.validate_output(str(output))
    for key in ("TEMP", "TMP", "TMPDIR"):
        os.environ[key] = "D:/Dev/_Temp"
    plan_pin = pin(plan_path)
    need(plan_pin["sha256"] == plan_sha, "plan_changed")
    prepare(read(plan_pin))
    output.mkdir()
    before = sources()
    request = dict(version=1, scope="closed-validation-profile-owner-v1", plan=plan_pin,
                   sources=before, output=str(output), repeat=repeat, seconds=180)
    env.create_json(output / "request-v1.json", request)
    def started(child):
        env.create_json(output / "started-v1.json", dict(worker=env.process_identity(child.pid)))
        return True
    outcome = env.supervise([sys.executable, "-I", "-S", "-B", str(Path(__file__)), "_worker", str(output), env.digest(output / "request-v1.json")], GO, output, 180, started)
    env.create_json(output / "owner-result-v1.json", outcome)
    try:
        stable = before == sources()
        env.check_binding(plan_pin)
    except (OSError, ValueError):
        stable = False
    passed = (outcome["status"] == "child_exited" and type(outcome["worker_returncode"]) is int and
              outcome["worker_returncode"] == 0 and outcome["cleanup_complete"] is True and
              outcome["output_capture_complete"] is True and outcome["stderr_bytes"] == 0 and stable and
              (output / "profile-v1.json").is_file())
    env.create_json(output / "result-v1.json", dict(version=1, passed=passed, owner=outcome,
        sources_equal=stable, profile=pin(output / "profile-v1.json") if (output / "profile-v1.json").exists() else None,
        feature_acceptance=False, original_runtime_requalified=False))
    print(env.encoded(dict(passed=passed, feature_acceptance=False)).decode(), end="")
    return 0 if passed else 1


def main():
    if len(sys.argv) == 4 and sys.argv[1] == "_worker":
        output = existing_output(sys.argv[2])
        need(output.drive.upper() == "D:" and not output.is_relative_to(ROOT), "output")
        try:
            worker(output, sys.argv[3])
            return 0
        except BaseException as error:
            reason = str(error) if isinstance(error, ValueError) and re.fullmatch("[a-z_]{1,48}", str(error)) else "checks_failed"
            env.create_json(output / "worker-refusal-v1.json", dict(reason=reason, feature_acceptance=False))
            return 1
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--plan", required=True)
    parser.add_argument("--plan-sha256", required=True)
    parser.add_argument("--output", required=True)
    parser.add_argument("--repeat", type=int, choices=(1, 2, 3), default=1)
    args = parser.parse_args()
    return run(args.plan, args.plan_sha256, args.output, args.repeat)


if __name__ == "__main__":
    raise SystemExit(main())
