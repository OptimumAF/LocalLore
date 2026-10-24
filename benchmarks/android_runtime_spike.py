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
    def __init__(self, category, command_cleaned=False):
        super().__init__(category)
        self.command_cleaned = command_cleaned is True


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
    failure_stage: str = field(default="none", repr=False)
    cleanup_failure_stage: str = field(default="none", repr=False)


CONTROL_STAGES = {"none", "unknown", "invoke_worker", "native_create_run", "native_link_worker",
    "native_write_request", "native_launch_owner", "native_read_owner", "native_verify_owner",
    "native_release_owner", "native_wait_worker", "native_read_done", "native_verify_reap",
    "native_cancel", "native_remove_run", "native_join_adb", "sdk_verify_package", "sdk_write_request",
    "sdk_launch_instrumentation", "sdk_wait_instrumentation", "sdk_stop_identity", "sdk_stop_command",
    "sdk_stop_absence", "sdk_parse_worker", "sdk_join_adb", "sdk_request_cleanup"}
CONTROL_STATUSES = {"completed", "failed", "cancelled", "timeout", "output_limit", "spawn_failed",
                    "cleanup_failed", "setup_failed", "owner_failed", "invalid_worker_response"}


def remote_metadata(result):
    """Project only fixed enums and bounded numbers, even for a defective adapter."""
    def stage(name):
        value = getattr(result, name, "none")
        return value if type(value) is str and value in CONTROL_STAGES else "unknown"
    elapsed = getattr(result, "elapsed_ms", 0)
    elapsed = round(elapsed) if type(elapsed) in (int, float) and 0 <= elapsed <= 2 ** 31 and math.isfinite(elapsed) else 0
    status = getattr(result, "status", None)
    status = status if type(status) is str and status in CONTROL_STATUSES else "owner_failed"
    code = getattr(result, "returncode", None)
    code = code if type(code) is int and 0 <= code <= 255 else None
    return {"process_status": status, "wall_ms": elapsed, "worker_exit_code": code,
            "cleanup_complete": getattr(result, "cleanup_complete", None) is True,
            "adb_cleanup_complete": getattr(result, "adb_cleanup_complete", None) is True,
            "directory_cleanup_complete": getattr(result, "directory_cleanup_complete", None) is True,
            "failure_stage": stage("failure_stage"), "cleanup_failure_stage": stage("cleanup_failure_stage")}


def remove_run(device, run):
    """Only a UUID this invocation created, after all possible writers are drained."""
    device.shell("rm", "-f", "--", *[run + "/" + name for name in
                 ("worker", "request", "owner", "owner.tmp", "done", "done.tmp", "release", "cancel")])
    device.shell("rmdir", run)


class Device:
    def __init__(self, adb, serial):
        self.adb, self.serial = str(adb), serial

    def raw(self, args, request=b"", deadline=20, cancel=None, max_output=None):
        # Trusted encoded recovery may need more wire bytes than decoded file
        # bytes. Keep the old default and the existing runner's absolute cap.
        if max_output is not None and (type(max_output) is not int or not 0 < max_output <= 262_144):
            raise Failure("invalid_output_budget", command_cleaned=True)
        args = list(args)
        if args and args[0] == "shell":
            args.insert(1, "-T")  # No terminal processing; fixed markers also admit Windows ADB CRLF.
        options = {} if max_output is None else {"max_output": max_output}
        return host.run_process([self.adb, "-s", self.serial] + args, request,
                                deadline=deadline, cancel=cancel, **options)

    def shell(self, *args, deadline=20, request=b""):
        # adb shell joins its argv into shell text; quote every remote argument ourselves.
        result = self.raw(["shell", shlex.join(str(arg) for arg in args)], request, deadline)
        if result.status != "completed" or result.returncode != 0 or not result.cleanup_complete:
            raise Failure("device_command_failed", command_cleaned=result.cleanup_complete)
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
            raise Failure("transfer_failed", command_cleaned=result.cleanup_complete)

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
            raise Failure("transfer_failed", command_cleaned=result.cleanup_complete)

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
            if type(value[key]) not in (int, float) or not 0 <= value[key] <= 2 ** 31 or not math.isfinite(value[key]):
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
        self.stop_stage = "none"

    def verify_package(self):
        path = self.device.shell("pm", "path", PACKAGE).strip()
        if not path.startswith(b"package:") or b"\n" in path:
            raise Failure("package_identity_failed", command_cleaned=True)
        installed = path[len(b"package:"):].decode("utf-8")
        observed = self.device.shell("sha256sum", installed)
        if not observed or observed.split()[0].decode("ascii") != self.apk_sha256:
            raise Failure("package_identity_failed", command_cleaned=True)

    def stop(self):
        self.stop_stage = "sdk_stop_identity"
        self.verify_package()
        self.stop_stage = "sdk_stop_command"
        self.device.shell("am", "force-stop", PACKAGE)
        self.stop_stage = "sdk_stop_absence"
        until = time.monotonic() + 5
        while time.monotonic() < until:
            state = self.device.script("pidof " + PACKAGE + " >/dev/null; result=$?; "
                "case $result in 0) printf running;; 1) printf absent;; *) exit 1;; esac").strip()
            if state == b"absent":
                self.stop_stage = "none"
                return True
            if state != b"running":
                raise Failure("invalid_process_probe", command_cleaned=True)
            time.sleep(.05)
        return False

    def cleanup_request(self):
        # The private request/corrupt test artifact can survive failed instrumentation.
        # Never touch files in a package whose installed bytes have changed.
        self.verify_package()
        self.device.shell("run-as", PACKAGE, "rm", "-f", "--", "files/request.json", "files/corrupt-spike-model.litertlm")
        self.device.shell("run-as", PACKAGE, "/system/bin/sh", "-c",
                          "[ ! -e files/request.json ] && [ ! -L files/request.json ] && "
                          "[ ! -e files/corrupt-spike-model.litertlm ] && [ ! -L files/corrupt-spike-model.litertlm ]")
        return True

    def run(self, binary, args, data=b"", deadline=60, cancel_after=None):
        del binary, args
        if not 1 <= deadline <= 90 or (cancel_after is not None and not 0 < cancel_after <= deadline):
            raise Failure("invalid_budget")
        start = time.monotonic()
        phase, failure, cleanup_failure = "sdk_verify_package", "none", "none"
        try:
            self.verify_package()
            if not self.stop():
                return RemoteResult("cleanup_failed", round((time.monotonic() - start) * 1000), False,
                                    failure_stage="sdk_stop_absence", cleanup_failure_stage="sdk_stop_absence")
            phase = "sdk_write_request"
            if self.mode in ("generate", "cancel"):
                self.device.private_write(data)
        except Exception as error:
            # No new instrumentation was launched. Failed preparation is still reported,
            # and cleanup will require a newly verified package rather than assumed ownership.
            phase = self.stop_stage if self.stop_stage != "none" else phase
            cleaned, files = False, False
            adb_cleaned = getattr(error, "command_cleaned", False) is True
            try:
                cleaned = self.stop()
                if not cleaned:
                    cleanup_failure = "sdk_stop_absence"
                elif adb_cleaned:
                    files = self.cleanup_request()
            except Exception as cleanup_error:
                adb_cleaned = adb_cleaned and getattr(cleanup_error, "command_cleaned", False) is True
                cleanup_failure = self.stop_stage if self.stop_stage != "none" else "sdk_request_cleanup"
            return RemoteResult("setup_failed", round((time.monotonic() - start) * 1000), cleaned,
                                adb_cleanup_complete=adb_cleaned, directory_cleanup_complete=files,
                                failure_stage=phase, cleanup_failure_stage=cleanup_failure)
        elapsed = time.monotonic() - start
        expired = "cancelled" if cancel_after is not None and elapsed >= cancel_after else "timeout" if elapsed >= deadline else None
        if expired:
            files = False
            try:
                files = self.cleanup_request()
            except Exception as cleanup_error:
                adb_cleaned = getattr(cleanup_error, "command_cleaned", False) is True
                cleanup_failure = "sdk_request_cleanup"
            return RemoteResult(expired, round((time.monotonic() - start) * 1000), True,
                                adb_cleanup_complete=adb_cleaned if cleanup_failure != "none" else True, directory_cleanup_complete=files,
                                failure_stage="sdk_wait_instrumentation" if expired == "timeout" else "none",
                                cleanup_failure_stage=cleanup_failure)
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
        thread = None
        status, output, code, cleanup, files, metrics = "owner_failed", b"", None, False, False, {}
        try:
            phase = "sdk_launch_instrumentation"
            thread = threading.Thread(target=execute, daemon=True)
            thread.start()
            phase = "sdk_wait_instrumentation"
            while not finished.wait(.01):
                elapsed = time.monotonic() - start
                if cancel_after is not None and elapsed >= cancel_after:
                    status = "cancelled"
                    break
                if elapsed >= deadline:
                    status = "timeout"
                    failure = phase
                    break
        except Exception:
            failure = phase
        finally:
            # Drain the only local launcher before the final package stop. Stopping first
            # permits a delayed launcher to create another process after an absence check.
            host_cancel.set()
            if thread is not None and thread.ident is not None:
                thread.join(timeout=8)
            launcher_cleaned = thread is None or bool((thread.ident is None or (results and results[0].cleanup_complete is True))
                                                     and not thread.is_alive())
            adb_cleaned = launcher_cleaned
            if results and results[0].status == "spawn_failed":
                failure = "sdk_launch_instrumentation"
            try:
                cleanup = self.stop()  # Reverify the installed bytes before every stop.
                if not cleanup:
                    cleanup_failure = "sdk_stop_absence"
                elif adb_cleaned:
                    files = self.cleanup_request()
            except Exception as cleanup_error:
                adb_cleaned = adb_cleaned and getattr(cleanup_error, "command_cleaned", False) is True
                cleanup = False if self.stop_stage != "none" else cleanup
                cleanup_failure = self.stop_stage if self.stop_stage != "none" else "sdk_request_cleanup"
            if not launcher_cleaned:
                cleanup_failure = "sdk_join_adb"
                cleanup = False
        if cleanup and adb_cleaned and failure == "none" and status not in ("cancelled", "timeout"):
            phase = "sdk_parse_worker"
            if results:
                result = results[0]
                parsed = sdk_response(result.stdout)
                if result.status == "completed" and type(result.returncode) is int and result.returncode == 0 and parsed:
                    output, metrics = parsed
                    status, code = "completed", 0
                else:
                    status = "invalid_worker_response"
                    failure = phase
        if not cleanup or not adb_cleaned:
            status = "cleanup_failed"
        if status != "completed":
            output, metrics = b"", {}
        return RemoteResult(status, round((time.monotonic() - start) * 1000), cleanup,
                            output, code, adb_cleaned, files, metrics, failure, cleanup_failure)


class NativeWorker:
    def __init__(self, device, owner):
        self.device, self.owner = device, owner

    def run(self, binary, args, data=b"", deadline=60, cancel_after=None, release=True):
        if not 1 <= deadline <= 90 or (cancel_after is not None and not 0 < cancel_after <= deadline):
            raise Failure("invalid_budget")
        start = time.monotonic()
        run = REMOTE + "/runs/" + uuid.uuid4().hex
        device = self.device
        created, phase = False, "native_create_run"
        def setup_failure(adb_cleaned):
            files, cleanup_failure = False, "none"
            if created and adb_cleaned:
                try:
                    remove_run(device, run)
                    files = True
                except Exception as cleanup_error:
                    adb_cleaned = adb_cleaned and getattr(cleanup_error, "command_cleaned", False) is True
                    cleanup_failure = "native_remove_run"
            # No native launcher was started, independently of directory/ADB cleanup.
            return RemoteResult("setup_failed", round((time.monotonic() - start) * 1000), True,
                                adb_cleanup_complete=adb_cleaned, directory_cleanup_complete=files,
                                failure_stage=phase, cleanup_failure_stage=cleanup_failure)
        try:
            device.shell("mkdir", "-m", "700", run)
            created, phase = True, "native_link_worker"
            device.shell("ln", "-s", binary, run + "/worker")
            phase = "native_write_request"
            device.put_bytes(data, run + "/request")
        except Exception as error:
            return setup_failure(getattr(error, "command_cleaned", False) is True)
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
        phase = "native_launch_owner"
        try:
            thread = threading.Thread(target=execute, daemon=True)
            thread.start()
        except Exception:
            if "thread" not in locals() or thread.ident is None:
                return setup_failure(True)
            host_cancel.set()
            try:
                device.script(": > " + shlex.quote(run + "/cancel"))
            except Exception:
                pass
            thread.join(timeout=8)
            return RemoteResult("cleanup_failed", round((time.monotonic() - start) * 1000), False,
                                failure_stage=phase, cleanup_failure_stage="native_verify_reap")
        pid, identity = None, None
        status, cleanup, directory_cleanup = "owner_failed", False, False
        output, code = b"", None
        failure, cleanup_failure, commands_cleaned = "none", "none", True
        try:
            phase = "native_read_owner"
            until = time.monotonic() + min(8, deadline)
            while time.monotonic() < until:
                raw = device.read_optional(run + "/owner")
                if raw:
                    if re.fullmatch(rb"[1-9][0-9]{0,9}\r?\n", raw) is None:
                        raise Failure("invalid_owner", command_cleaned=True)
                    pid = int(raw)
                    phase = "native_verify_owner"
                    identity = device.identity(pid)
                    if identity is None or identity[1] != [arg.encode("utf-8") for arg in command]:
                        raise Failure("invalid_owner", command_cleaned=True)
                    break
                if stopped.is_set():
                    raise Failure("owner_failed", command_cleaned=True)
                time.sleep(.02)
            if identity is None:
                raise Failure("owner_failed", command_cleaned=True)
            requested = None
            elapsed = time.monotonic() - start
            if cancel_after is not None and elapsed >= cancel_after:
                requested = "cancelled"
            elif elapsed >= deadline:
                requested = "timeout"
            if release and requested is None:
                phase = "native_release_owner"
                device.script(": > " + shlex.quote(run + "/release"))
            phase = "native_wait_worker"
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
                phase = "native_cancel"
                device.script(": > " + shlex.quote(run + "/cancel"))
            if not stopped.wait(7):
                host_cancel.set()
                stopped.wait(8)
            result = results[0] if results else None
            phase = "native_read_done"
            done = parse_done(device.read_optional(run + "/done"))
            if done:
                status, code = done
                phase = "native_verify_reap"
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
                elif result.status == "completed" and (type(result.returncode) is not int or result.returncode != 0):
                    status, failure = "owner_failed", "native_wait_worker"
                    output = b""
            if not cleanup:
                status = "cleanup_failed"
                failure, cleanup_failure = phase, "native_verify_reap"
        except Exception as error:
            commands_cleaned = getattr(error, "command_cleaned", False) is True
            failure, cleanup_failure = phase, "native_verify_reap"
            if results and results[0].status == "spawn_failed":
                failure = "native_launch_owner"
            status = "cleanup_failed"
            try:
                device.script(": > " + shlex.quote(run + "/cancel"))
            except Exception as cleanup_error:
                commands_cleaned = commands_cleaned and getattr(cleanup_error, "command_cleaned", False) is True
                cleanup_failure = "native_cancel"
        finally:
            host_cancel.set()
            thread.join(timeout=8)
            if cleanup:
                # Only known files in the exact UUID directory; never recursive deletion.
                try:
                    remove_run(device, run)
                    directory_cleanup = True
                except Exception as cleanup_error:
                    commands_cleaned = commands_cleaned and getattr(cleanup_error, "command_cleaned", False) is True
                    cleanup_failure = "native_remove_run"
        launcher_cleaned = bool(results and results[0].cleanup_complete is True and not thread.is_alive())
        adb_cleaned = commands_cleaned and launcher_cleaned
        if not launcher_cleaned:
            cleanup_failure = "native_join_adb"
        return RemoteResult(status, round((time.monotonic() - start) * 1000), cleanup,
                            output, code, adb_cleaned, directory_cleanup, failure_stage=failure,
                            cleanup_failure_stage=cleanup_failure)


def oracle(worker, binary, operation, case, data=b""):
    result = worker.run(binary, [operation, case], data, deadline=10)
    metadata = remote_metadata(result)
    if (metadata["process_status"] != "completed" or not metadata["cleanup_complete"] or not metadata["adb_cleanup_complete"]
            or metadata["worker_exit_code"] != 0):
        return None
    try:
        value = strict_json(result.stdout)
    except (ValueError, UnicodeError, RecursionError, OverflowError):
        return None
    return value if isinstance(value, dict) else None


class ObservedOracle:
    """Retain fixed per-call diagnostics when an oracle cannot even start."""
    def __init__(self, worker, rows):
        self.worker, self.rows = worker, rows

    def run(self, binary, args, data=b"", **kwargs):
        operation = args[0] if args and args[0] in ("fixture", "validate", "commit") else "unknown"
        try:
            result = self.worker.run(binary, args, data, **kwargs)
        except Exception:
            result = RemoteResult("owner_failed", 0, False, failure_stage="invoke_worker")
        self.rows.append(dict(operation=operation, **remote_metadata(result)))
        return result


def safe_sdk_metrics(raw):
    if not isinstance(raw, dict):
        return {}
    safe = {k: raw[k] for k in SDK_BOOL_METRICS & raw.keys() if type(raw[k]) is bool}
    safe.update({k: raw[k] for k in SDK_NUMBER_METRICS & raw.keys() if type(raw[k]) in (int, float)
                 and 0 <= raw[k] <= 2 ** 31 and math.isfinite(raw[k])})
    return safe


def sdk_diagnostic(sdk, native, oracle_binary, mode):
    rows = []
    report = {"version": 1, "scope": "android_sdk_boundary_smoke", "mode": mode,
              "status": "oracle_failed", "check_passed": False, "oracle_runs": rows}
    fixture = oracle(ObservedOracle(native, rows), oracle_binary, "fixture", "gift")
    if not fixture or not isinstance(fixture.get("director"), dict):
        return report
    try:
        result = sdk.run("unused", [], json.dumps(fixture["director"]).encode("utf-8"), deadline=80)
    except Exception:
        result = RemoteResult("owner_failed", 0, False, failure_stage="invoke_worker")
    metadata = remote_metadata(result)
    parsed = host.parse_worker(result.stdout)
    metrics = safe_sdk_metrics(result.metrics)
    report.update(metadata)
    report.update(status=metadata["process_status"], sdk=metrics,
                  worker_status=parsed["status"] if parsed else None,
                  worker_error=parsed["error"] if parsed else None)
    expected = {"metadata": None, "missing": "model_missing", "corrupt": "model_invalid", "cancel": None}
    report["check_passed"] = bool(metadata["process_status"] == "completed" and metadata["cleanup_complete"]
        and metadata["adb_cleanup_complete"] and metadata["worker_exit_code"] == 0 and parsed
        and parsed["error"] == expected[mode] and (mode != "cancel"
        or (metrics.get("cancel_terminal_callback") is True and metrics.get("reload_completed") is True)))
    return report


def experiment(device, worker, binary, oracle_binary, model, case="gift", cancel_after=None,
               runtime="llama", oracle_worker=None):
    report = {"version": 1, "scope": "android_x86_64_cold_smoke", "runtime": runtime,
              "case": case, "status": "not_started", "attempted_roles": 0, "roles": [],
              "phone_qualified": False, "quality_assessed": False, "durable_state": False, "oracle_runs": []}
    oracle_worker = ObservedOracle(oracle_worker or worker, report["oracle_runs"])
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
        except Exception:
            result = RemoteResult("owner_failed", 0, False, failure_stage="invoke_worker")
        aggregate = dict(role=role, **remote_metadata(result))
        report["roles"].append(aggregate)
        if getattr(result, "metrics", None):
            aggregate["sdk"] = safe_sdk_metrics(result.metrics)
        if aggregate["process_status"] != "completed":
            report["status"] = aggregate["process_status"]
            if aggregate["process_status"] == "failed" and aggregate["cleanup_complete"] and aggregate["adb_cleanup_complete"]:
                error_reply = host.parse_worker(result.stdout)
                if error_reply and error_reply["status"] == "error":
                    aggregate.update({key: value for key, value in error_reply.items() if key not in ("version", "text")})
                    report["status"] = error_reply["error"]
            return report
        if not aggregate["cleanup_complete"] or not aggregate["adb_cleanup_complete"]:
            report["status"] = "cleanup_failed"
            return report
        if aggregate["worker_exit_code"] != 0:
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
                    report = sdk_diagnostic(sdk, native, oracle_binary, args.sdk_mode)
        report.update(artifact=host.ARTIFACTS[args.runtime][0], model_sha256=host.ARTIFACTS[args.runtime][2])
    except (Failure, OSError, ValueError):
        report = {"version": 1, "status": "setup_failed", "attempted_roles": 0, "roles": []}
    text = json.dumps(report, indent=2, allow_nan=False) + "\n"
    args.output.write_text(text, encoding="utf-8")
    print(text, end="")
    return 0 if report["status"] in ("committed", "preflight_rejected") or report.get("check_passed") is True else 2


if __name__ == "__main__":
    raise SystemExit(main())
