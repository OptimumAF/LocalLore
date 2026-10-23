"""Explicit Android-only development experiment. Never imported by the app.

Only reviewed aggregate reports may be printed. Model text remains in memory.
The native supervisor, not the host ADB client, owns/reaps inference processes.
"""
import argparse
import base64
import hashlib
import json
import math
import os
from pathlib import Path
import re
import shlex
import subprocess
import tempfile
import threading
import time
import uuid
from dataclasses import dataclass, field

import runtime_spike as host

ROOT = Path(__file__).resolve().parents[1]
REMOTE = "/data/local/tmp/locallore-m01"
PACKAGE = "org.locallore.runtimebench.litert"


class Failure(Exception):
    """Internal fixed category only; never retain stderr or private exception text."""


def sha256(path):
    digest = hashlib.sha256()
    with Path(path).open("rb") as source:
        for block in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def strict_json(raw):
    def unique(pairs):
        value = {}
        for key, item in pairs:
            if key in value:
                raise ValueError("duplicate_key")
            value[key] = item
        return value
    return json.loads(raw.decode("utf-8"), object_pairs_hook=unique,
                      parse_constant=lambda _: (_ for _ in ()).throw(ValueError("nonfinite")))


def parse_stat(raw, pid):
    """Linux stat comm may contain spaces and closing parentheses."""
    try:
        value = raw.decode("ascii").strip()
        first, rest = value.split(" (", 1)
        fields = rest.rsplit(") ", 1)[1].split()
        if first != str(pid) or len(fields) < 20 or not fields[19].isdigit():
            return None
        return int(fields[19])
    except (ValueError, UnicodeError, IndexError):
        return None


def parse_done(raw):
    match = re.fullmatch(rb"(completed|failed|cancelled|timeout|cleanup_failed) ([0-9]{1,3})\r?\n", raw)
    if not match or int(match[2]) > 255:
        return None
    return match[1].decode("ascii"), int(match[2])


@dataclass
class RemoteResult:
    status: str
    elapsed_ms: int
    cleanup_complete: bool
    stdout: bytes = field(default=b"", repr=False)
    returncode: int = None
    adb_cleanup_complete: bool = False
    directory_cleanup_complete: bool = False
    metrics: dict = field(default_factory=dict, repr=False)


class Device:
    def __init__(self, adb, serial):
        self.adb, self.serial = str(adb), serial

    def raw(self, args, request=b"", deadline=20, cancel=None):
        args = list(args)
        if args and args[0] == "shell":
            args.insert(1, "-T")  # No terminal processing; fixed markers also admit Windows ADB CRLF.
        return host.run_process([self.adb, "-s", self.serial] + args, request,
                                deadline=deadline, cancel=cancel)

    def shell(self, *args, deadline=20, request=b""):
        # adb shell joins its argv into shell text; quote every remote argument ourselves.
        result = self.raw(["shell", shlex.join(str(arg) for arg in args)], request, deadline)
        if result.status != "completed" or result.returncode != 0 or not result.cleanup_complete:
            raise Failure("device_command_failed")
        return result.stdout

    def script(self, command, deadline=20):
        return self.shell("/system/bin/sh", "-c", command, deadline=deadline)

    def read_optional(self, path):
        quoted = shlex.quote(path)
        return self.script(f"if [ -f {quoted} ]; then cat {quoted}; fi")

    def initialize(self):
        q = shlex.quote(REMOTE)
        command = (f"umask 077; if [ -d {q} ]; then "
                   f"[ \"$(cat {q}/owner-v1 2>/dev/null)\" = locallore-runtime-v1 ] || exit 1; "
                   f"else mkdir {q} && printf '%s\\n' locallore-runtime-v1 > {q}/owner-v1 || exit 1; fi; "
                   f"mkdir -p {q}/cache {q}/runs")
        self.script(command)

    def put(self, path, destination):
        result = self.raw(["push", str(path), destination], deadline=180)
        if result.status != "completed" or result.returncode != 0 or not result.cleanup_complete:
            raise Failure("transfer_failed")

    def put_bytes(self, data, destination):
        if len(data) > 131072:
            raise Failure("request_too_large")
        (ROOT / "target").mkdir(exist_ok=True)
        with tempfile.TemporaryDirectory(dir=ROOT / "target") as temporary:
            path = Path(temporary) / "input"
            path.write_bytes(data)
            self.put(path, destination)

    def cached(self, path, suffix="elf"):
        if suffix not in ("elf", "gguf"):
            raise Failure("invalid_artifact")
        path = Path(path)
        digest = sha256(path)
        destination = f"{REMOTE}/cache/{digest}.{suffix}"
        q = shlex.quote(destination)
        current = self.script(f"if [ -f {q} ]; then sha256sum {q}; fi", deadline=90)
        if current:
            if current.split()[0].decode("ascii") != digest:
                raise Failure("device_hash_mismatch")
            return destination
        disk = self.shell("df", "-k", "/data").splitlines()[-1].split()
        if len(disk) < 4 or not disk[3].isdigit() or int(disk[3]) * 1024 < path.stat().st_size + 1024 ** 3:
            raise Failure("device_storage_gate")
        stage = destination + ".partial." + uuid.uuid4().hex
        self.put(path, stage)
        observed = self.shell("sha256sum", stage, deadline=90)
        if not observed or observed.split()[0].decode("ascii") != digest:
            raise Failure("device_hash_mismatch")
        self.shell("mv", stage, destination)
        self.shell("chmod", "700" if suffix == "elf" else "600", destination)
        return destination

    def identity(self, pid):
        # No signal is sent from the host. Identity is used only to verify launch/absence.
        if type(pid) is not int or not 1 <= pid <= 2147483647:
            raise Failure("invalid_owner")
        raw = self.script(f"if [ -r /proc/{pid}/stat ]; then cat /proc/{pid}/stat; fi")
        if not raw:
            return None
        ticks = parse_stat(raw, pid)
        if ticks is None:
            raise Failure("invalid_owner")
        command = self.shell("cat", f"/proc/{pid}/cmdline")
        return ticks, command.rstrip(b"\0").split(b"\0")

    def private_write(self, data):
        if len(data) > 32768:
            raise Failure("request_too_large")
        command = shlex.join(["run-as", PACKAGE, "/system/bin/sh", "-c", "cat > files/request.json"])
        result = self.raw(["exec-in", command], request=data)
        if result.status != "completed" or result.returncode != 0 or not result.cleanup_complete:
            raise Failure("transfer_failed")

    def provision_private_model(self, path):
        if host.verify_model("litert", path):
            raise Failure("model_hash_mismatch")
        self.shell("run-as", PACKAGE, "mkdir", "-p", "files")
        expected = host.ARTIFACTS["litert"][2]
        final = "files/gemma4-e2b.litertlm"
        current = self.script(shlex.join(["run-as", PACKAGE, "/system/bin/sh", "-c",
                                          f"if [ -f {final} ]; then sha256sum {final}; fi"]), deadline=90)
        if current:
            if current.split()[0].decode("ascii") != expected:
                raise Failure("device_hash_mismatch")
            return
        disk = self.shell("df", "-k", "/data").splitlines()[-1].split()
        if int(disk[3]) * 1024 < Path(path).stat().st_size + 1024 ** 3:
            raise Failure("device_storage_gate")
        stage = "files/model.partial." + uuid.uuid4().hex
        command = [self.adb, "-s", self.serial, "exec-in",
                   shlex.join(["run-as", PACKAGE, "/system/bin/sh", "-c", "cat > " + stage])]
        # Transfer only: native inference cannot start here. Keep model bytes out of Python memory.
        with Path(path).open("rb") as source:
            options = {"creationflags": subprocess.CREATE_NO_WINDOW} if os.name == "nt" else {"start_new_session": True}
            # No transfer diagnostics are retained, even if the trusted client exits quickly.
            process = subprocess.Popen(command, stdin=source, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, **options)
            job = None
            try:
                if os.name == "nt":
                    job = host.WindowsJob(process.pid)
                until = time.monotonic() + 180
                while process.poll() is None:
                    if time.monotonic() >= until:
                        raise Failure("transfer_failed")
                    time.sleep(.02)
                if process.returncode != 0:
                    raise Failure("transfer_failed")
            finally:
                if job:
                    cleaned = job.close()
                else:
                    process.kill() if process.poll() is None else None
                    cleaned = True
                try:
                    process.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    raise Failure("transfer_failed") from None
                if not cleaned:
                    raise Failure("transfer_failed")
        observed = self.shell("run-as", PACKAGE, "sha256sum", stage, deadline=90)
        if not observed or observed.split()[0].decode("ascii") != expected:
            raise Failure("device_hash_mismatch")
        self.shell("run-as", PACKAGE, "mv", stage, final)


SDK_BOOL_METRICS = {"worker_off_main", "cancel_called", "terminal_callback", "reload_completed",
                    "generated_text_logged", "owners_balanced", "request_delete_failed", "model_info_closed",
                    "dynamic_context", "cpu_text_supported", "native_invalid_model_rejected", "corrupt_delete_failed",
                    "cancel_terminal_callback", "generate_terminal_callback", "cancelled_text_discarded",
                    "cleanup_requires_process_termination"}
SDK_NUMBER_METRICS = {"engines_opened", "engines_closed", "conversations_opened", "conversations_closed",
                      "main_pulses", "max_context_tokens", "cancel_call_ms", "generation_main_pulses",
                      "cancel_main_pulses", "generate_main_pulses"}


def sdk_response(raw):
    try:
        values = re.findall(rb"^INSTRUMENTATION_RESULT: result_base64=([A-Za-z0-9+/=]+)\r?$", raw, re.MULTILINE)
        metrics = re.findall(rb"^INSTRUMENTATION_RESULT: metrics=(.*)\r?$", raw, re.MULTILINE)
        if len(values) != 1 or len(metrics) != 1:
            return None
        output = base64.b64decode(values[0], validate=True)
        if host.parse_worker(output) is None:
            return None
        value = strict_json(metrics[0])
        if not isinstance(value, dict) or any(type(value.get(key)) is not bool for key in
                ("worker_off_main", "owners_balanced", "generated_text_logged")):
            return None
        safe = {}
        for key in SDK_BOOL_METRICS & value.keys():
            if type(value[key]) is not bool:
                return None
            safe[key] = value[key]
        for key in SDK_NUMBER_METRICS & value.keys():
            if type(value[key]) not in (int, float) or not math.isfinite(value[key]) or not 0 <= value[key] <= 2 ** 31:
                return None
            safe[key] = value[key]
        if not safe["worker_off_main"] or not safe["owners_balanced"] or safe["generated_text_logged"]:
            return None
        for key in ("engines_opened", "engines_closed", "conversations_opened", "conversations_closed", "main_pulses"):
            if type(safe.get(key)) is not int:
                return None
        if (safe["engines_opened"] != safe["engines_closed"]
                or safe["conversations_opened"] != safe["conversations_closed"] or safe["main_pulses"] < 1):
            return None
        return output, safe
    except (ValueError, UnicodeError, TypeError, RecursionError):
        return None


class SdkWorker:
    def __init__(self, device, apk_sha256, mode="generate"):
        if mode not in ("generate", "metadata", "missing", "corrupt", "cancel"):
            raise Failure("invalid_budget")
        self.device, self.apk_sha256, self.mode = device, apk_sha256, mode

    def verify_package(self):
        path = self.device.shell("pm", "path", PACKAGE).strip()
        if not path.startswith(b"package:") or b"\n" in path:
            raise Failure("package_identity_failed")
        installed = path[len(b"package:"):].decode("utf-8")
        observed = self.device.shell("sha256sum", installed)
        if not observed or observed.split()[0].decode("ascii") != self.apk_sha256:
            raise Failure("package_identity_failed")

    def stop(self):
        self.verify_package()
        self.device.shell("am", "force-stop", PACKAGE)
        until = time.monotonic() + 5
        while time.monotonic() < until:
            if not self.device.script("pidof " + PACKAGE + " || true").strip():
                return True
            time.sleep(.05)
        return False

    def run(self, binary, args, data=b"", deadline=60, cancel_after=None):
        del binary, args
        if not 1 <= deadline <= 90 or (cancel_after is not None and not 0 < cancel_after <= deadline):
            raise Failure("invalid_budget")
        start = time.monotonic()
        self.verify_package()
        if self.mode in ("generate", "cancel"):
            self.device.private_write(data)
        results, finished, host_cancel = [], threading.Event(), threading.Event()
        def execute():
            try:
                results.append(self.device.raw(["shell", shlex.join(["am", "instrument", "-w", "-r", "-e", "mode",
                                self.mode, PACKAGE + "/.SpikeInstrumentation"])],
                                               deadline=min(180, deadline + 15), cancel=host_cancel))
            except Exception:
                results.append(host.ProcessResult("spawn_failed", 0))
            finally:
                finished.set()
        thread = threading.Thread(target=execute, daemon=True)
        thread.start()
        status, output, code, cleanup, metrics = "owner_failed", b"", None, False, {}
        try:
            while not finished.wait(.01):
                elapsed = time.monotonic() - start
                if cancel_after is not None and elapsed >= cancel_after:
                    status = "cancelled"
                    break
                if elapsed >= deadline:
                    status = "timeout"
                    break
            cleanup = self.stop()  # Only this hash-verified, isolated benchmark package.
            if not finished.wait(7):
                host_cancel.set()
                finished.wait(8)
            if status not in ("cancelled", "timeout") and results:
                result = results[0]
                parsed = sdk_response(result.stdout)
                if result.status == "completed" and result.returncode == 0 and parsed:
                    output, metrics = parsed
                    status, code = "completed", 0
                else:
                    status = "invalid_worker_response"
        except (Failure, OSError):
            cleanup = False
        finally:
            host_cancel.set()
            thread.join(timeout=8)
        adb_cleaned = bool(results and results[0].cleanup_complete and not thread.is_alive())
        if not cleanup or not adb_cleaned:
            status = "cleanup_failed"
        return RemoteResult(status, round((time.monotonic() - start) * 1000), cleanup,
                            output, code, adb_cleaned, True, metrics)


class NativeWorker:
    def __init__(self, device, owner):
        self.device, self.owner = device, owner

    def run(self, binary, args, data=b"", deadline=60, cancel_after=None, release=True):
        if not 1 <= deadline <= 90 or (cancel_after is not None and not 0 < cancel_after <= deadline):
            raise Failure("invalid_budget")
        start = time.monotonic()
        run = REMOTE + "/runs/" + uuid.uuid4().hex
        device = self.device
        try:
            device.shell("mkdir", "-m", "700", run)
            device.shell("ln", "-s", binary, run + "/worker")
            device.put_bytes(data, run + "/request")
        except (Failure, OSError):
            return RemoteResult("setup_failed", round((time.monotonic() - start) * 1000), False)
        command = [self.owner, run, str(math.ceil(deadline)), run + "/worker"] + list(args)
        stopped = threading.Event()
        host_cancel = threading.Event()
        results = []

        def execute():
            try:
                results.append(device.raw(["shell", "exec " + shlex.join(command)],
                                          deadline=min(180, deadline + 25), cancel=host_cancel))
            except Exception:
                results.append(host.ProcessResult("spawn_failed", 0))
            finally:
                stopped.set()
        thread = threading.Thread(target=execute, daemon=True)
        thread.start()
        pid, identity = None, None
        status, cleanup, directory_cleanup = "owner_failed", False, False
        output, code = b"", None
        try:
            until = time.monotonic() + min(8, deadline)
            while time.monotonic() < until:
                raw = device.read_optional(run + "/owner")
                if raw:
                    if re.fullmatch(rb"[1-9][0-9]{0,9}\r?\n", raw) is None:
                        raise Failure("invalid_owner")
                    pid = int(raw)
                    identity = device.identity(pid)
                    if identity is None or identity[1] != [arg.encode("utf-8") for arg in command]:
                        raise Failure("invalid_owner")
                    break
                if stopped.is_set():
                    raise Failure("owner_failed")
                time.sleep(.02)
            if identity is None:
                raise Failure("owner_failed")
            requested = None
            elapsed = time.monotonic() - start
            if cancel_after is not None and elapsed >= cancel_after:
                requested = "cancelled"
            elif elapsed >= deadline:
                requested = "timeout"
            if release and requested is None:
                device.script(": > " + shlex.quote(run + "/release"))
            while not stopped.wait(.01):
                if requested:
                    break
                elapsed = time.monotonic() - start
                if cancel_after is not None and elapsed >= cancel_after:
                    requested = "cancelled"
                    break
                if elapsed >= deadline:
                    requested = "timeout"
                    break
            if requested:
                device.script(": > " + shlex.quote(run + "/cancel"))
            if not stopped.wait(7):
                host_cancel.set()
                stopped.wait(8)
            result = results[0] if results else None
            done = parse_done(device.read_optional(run + "/done"))
            if done:
                status, code = done
                until = time.monotonic() + 3
                while time.monotonic() < until:
                    observed = device.identity(pid)
                    if observed is None or observed[0] != identity[0]:
                        cleanup = status != "cleanup_failed"
                        break
                    time.sleep(.02)
            if requested:
                status = requested
            if result:
                output = result.stdout
                if result.status != "completed" and not requested:
                    status = result.status
            if not cleanup:
                status = "cleanup_failed"
        except (Failure, OSError):
            status = "cleanup_failed"
            try:
                device.script(": > " + shlex.quote(run + "/cancel"))
            except Failure:
                pass
        finally:
            host_cancel.set()
            thread.join(timeout=8)
            if cleanup:
                # Only known files in the exact UUID directory; never recursive deletion.
                try:
                    device.shell("rm", "-f", "--", *[run + "/" + name for name in
                                 ("worker", "request", "owner", "owner.tmp", "done", "done.tmp", "release", "cancel")])
                    device.shell("rmdir", run)
                    directory_cleanup = True
                except (Failure, OSError):
                    pass
        adb_cleaned = bool(results and results[0].cleanup_complete and not thread.is_alive())
        return RemoteResult(status, round((time.monotonic() - start) * 1000), cleanup,
                            output, code, adb_cleaned, directory_cleanup)


def oracle(worker, binary, operation, case, data=b""):
    result = worker.run(binary, [operation, case], data, deadline=10)
    if (result.status != "completed" or not result.cleanup_complete or not result.adb_cleanup_complete
            or result.returncode != 0):
        return None
    try:
        value = strict_json(result.stdout)
    except (ValueError, UnicodeError, RecursionError, OverflowError):
        return None
    return value if isinstance(value, dict) else None


def experiment(device, worker, binary, oracle_binary, model, case="gift", cancel_after=None,
               runtime="llama", oracle_worker=None):
    report = {"version": 1, "scope": "android_x86_64_cold_smoke", "runtime": runtime,
              "case": case, "status": "not_started", "attempted_roles": 0, "roles": [],
              "phone_qualified": False, "quality_assessed": False, "durable_state": False}
    oracle_worker = oracle_worker or worker
    fixture = oracle(oracle_worker, oracle_binary, "fixture", case)
    if not fixture:
        report["status"] = "oracle_failed"
        return report
    preflight = fixture.get("preflight_error")
    if preflight is not None:
        if type(preflight) is str and preflight in host.DOMAIN_ERRORS:
            report.update(status="preflight_rejected", domain_error=preflight)
        else:
            report["status"] = "oracle_failed"
        return report
    request = fixture.get("director")
    if not isinstance(request, dict):
        report["status"] = "oracle_failed"
        return report
    proposal = None
    start = time.monotonic()
    for role in ("director", "narrator"):
        remaining = 60 - (time.monotonic() - start)
        if remaining < 1:
            report["status"] = "timeout"
            return report
        report["attempted_roles"] += 1
        try:
            result = worker.run(binary, ["--model", model], json.dumps(request).encode("utf-8"), deadline=remaining,
                                cancel_after=cancel_after if role == "director" else None)
        except (Failure, OSError):
            result = RemoteResult("owner_failed", 0, False)
        aggregate = {"role": role, "process_status": result.status, "wall_ms": result.elapsed_ms,
                     "cleanup_complete": result.cleanup_complete, "adb_cleanup_complete": result.adb_cleanup_complete,
                     "directory_cleanup_complete": getattr(result, "directory_cleanup_complete", False),
                     "worker_exit_code": result.returncode}
        report["roles"].append(aggregate)
        if getattr(result, "metrics", None):
            aggregate["sdk"] = result.metrics
        if result.status != "completed":
            report["status"] = result.status
            if result.status == "failed" and result.cleanup_complete and result.adb_cleanup_complete:
                error_reply = host.parse_worker(result.stdout)
                if error_reply and error_reply["status"] == "error":
                    aggregate.update({key: value for key, value in error_reply.items() if key not in ("version", "text")})
                    report["status"] = error_reply["error"]
            return report
        if not result.cleanup_complete or not result.adb_cleanup_complete:
            report["status"] = "cleanup_failed"
            return report
        if result.returncode != 0:
            report["status"] = "worker_failed"
            return report
        generated = host.parse_worker(result.stdout)
        if generated is None:
            report["status"] = "invalid_worker_response"
            return report
        aggregate.update({key: value for key, value in generated.items() if key not in ("version", "text")})
        if generated["status"] != "completed":
            report["status"] = generated["error"]
            return report
        if not generated["thinking_disabled"] or not generated["template_applied"]:
            report["status"] = "unsupported_output"
            return report
        if role == "director":
            proposal = generated["text"]
            accepted = oracle(oracle_worker, oracle_binary, "validate", case, proposal.encode("utf-8"))
            if not accepted or accepted.get("status") != "accepted":
                report["status"] = "engine_rejected"
                return report
            request = accepted["narrator"]
        else:
            completion = json.dumps({"proposal": proposal, "narration": generated["text"]}).encode("utf-8")
            accepted = oracle(oracle_worker, oracle_binary, "commit", case, completion)
            if not accepted or accepted.get("status") != "committed":
                report["status"] = "engine_rejected"
                return report
            if (any(type(accepted.get(key)) is not int or accepted[key] < 0 for key in
                    ("revision", "events", "recipient_observations", "absent_observations"))
                    or type(accepted.get("exact_retry_unchanged")) is not bool):
                report["status"] = "oracle_failed"
                return report
            expected = {"revision": 1, "events": 1, "recipient_observations": 1,
                        "absent_observations": 0, "exact_retry_unchanged": True}
            if any(accepted.get(key) != value for key, value in expected.items()):
                report["status"] = "engine_result_failed"
                return report
            report.update({key: accepted[key] for key in
                           ("revision", "events", "exact_retry_unchanged", "recipient_observations", "absent_observations")})
            report["status"] = "committed"
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--adb", type=Path, required=True)
    parser.add_argument("--serial", required=True)
    parser.add_argument("--owner", type=Path, required=True)
    parser.add_argument("--binary", type=Path, required=True)
    parser.add_argument("--oracle", type=Path, required=True)
    parser.add_argument("--model", type=Path, required=True)
    parser.add_argument("--runtime", choices=("llama", "litert"), default="llama")
    parser.add_argument("--apk", type=Path, help="already installed, source-built isolated SDK APK")
    parser.add_argument("--sdk-mode", choices=("generate", "metadata", "missing", "corrupt", "cancel"), default="generate")
    parser.add_argument("--case", choices=("gift", "spent", "unlearned"), default="gift")
    parser.add_argument("--cancel-after", type=float)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    if args.cancel_after is not None and (not math.isfinite(args.cancel_after) or not 0 < args.cancel_after <= 60):
        parser.error("Cancellation offset must be finite and between 0 and 60 seconds")
    try:
        device = Device(args.adb, args.serial)
        device.initialize()
        owner, oracle_binary = [device.cached(path) for path in (args.owner, args.oracle)]
        native = NativeWorker(device, owner)
        if args.case != "gift":
            report = experiment(device, native, "unused", oracle_binary, "unused", args.case, runtime=args.runtime)
        else:
            error = host.verify_model(args.runtime, args.model)
            if error:
                raise Failure(error)
            if args.runtime == "llama":
                binary = device.cached(args.binary)
                model = device.cached(args.model, "gguf")
                report = experiment(device, native, binary, oracle_binary, model, args.case, args.cancel_after)
            else:
                if args.apk is None:
                    raise Failure("package_identity_failed")
                sdk = SdkWorker(device, sha256(args.apk), args.sdk_mode)
                sdk.verify_package()
                device.provision_private_model(args.model)
                if args.sdk_mode == "generate":
                    report = experiment(device, sdk, "unused", oracle_binary, "private_model", args.case,
                                        args.cancel_after, runtime="litert", oracle_worker=native)
                else:
                    fixture = oracle(native, oracle_binary, "fixture", "gift")
                    result = sdk.run("unused", [], json.dumps(fixture["director"]).encode("utf-8"), deadline=80)
                    parsed = host.parse_worker(result.stdout)
                    report = {"version": 1, "scope": "android_sdk_boundary_smoke", "mode": args.sdk_mode,
                              "status": result.status, "cleanup_complete": result.cleanup_complete,
                              "adb_cleanup_complete": result.adb_cleanup_complete, "sdk": result.metrics,
                              "worker_status": parsed["status"] if parsed else None,
                              "worker_error": parsed["error"] if parsed else None}
                    expected = {"metadata": None, "missing": "model_missing", "corrupt": "model_invalid", "cancel": None}
                    report["check_passed"] = bool(result.status == "completed" and result.cleanup_complete
                        and result.adb_cleanup_complete and parsed and parsed["error"] == expected[args.sdk_mode]
                        and (args.sdk_mode != "cancel" or (result.metrics.get("cancel_terminal_callback") is True
                                                          and result.metrics.get("reload_completed") is True)))
        report.update(artifact=host.ARTIFACTS[args.runtime][0], model_sha256=host.ARTIFACTS[args.runtime][2])
    except (Failure, OSError, ValueError):
        report = {"version": 1, "status": "setup_failed", "attempted_roles": 0, "roles": []}
    text = json.dumps(report, indent=2, allow_nan=False) + "\n"
    args.output.write_text(text, encoding="utf-8")
    print(text, end="")
    return 0 if report["status"] in ("committed", "preflight_rejected") or report.get("check_passed") is True else 2


if __name__ == "__main__":
    raise SystemExit(main())
