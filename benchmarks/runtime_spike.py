"""Development-only, local runtime smoke checks. Never used by the Android app.

Workers read stdin before native import/child launch. Assign their process to
an owned Windows job before releasing that barrier; POSIX uses a process group.
Only fixed aggregate results are printable. Model text stays in memory.
"""
import argparse
import ctypes
import hashlib
import json
import math
import os
from pathlib import Path
import signal
import subprocess
import sys
import threading
import time
from dataclasses import dataclass, field

ROOT = Path(__file__).resolve().parents[1]
ARTIFACTS = {
    "litert": ("gemma4-e2b-litert", 2_588_147_712,
               "181938105e0eefd105961417e8da75903eacda102c4fce9ce90f50b97139a63c"),
    "llama": ("qwen3-0.6b-q8-smoke", 639_446_688,
              "9465e63a22add5354d9bb4b99e90117043c7124007664907259bd16d043bb031"),
}
WORKER_ERRORS = {"invalid_request", "model_missing", "model_invalid", "runtime_unavailable",
                 "model_unsupported", "context_overflow", "generation_failed", "output_too_large",
                 "unsupported_output", "executable_missing", "runtime_failed", "timeout", "output_limit",
                 "model_load_failed", "unsupported_template", "context_limit", "context_failed",
                 "sampling_failed", "decode_failed", "unexpected_output"}
DOMAIN_ERRORS = {"Version","Scope","Stale","RetryMismatch","Malformed","TooLarge","Agency",
                 "AuthorUiRequired","ClarificationRequired","UnknownReference","DeadActor","Location",
                 "Inventory","Resource","Ability","Knowledge","Rule","Cancelled","Provider","Timeout",
                 "Narration","CorruptHistory"}


class WindowsJob:
    """No inherited job handle; every descendant is terminated before closing it."""
    def __init__(self, pid):
        from ctypes import wintypes as w
        class Basic(ctypes.Structure):
            _fields_ = [("process_time", ctypes.c_int64), ("job_time", ctypes.c_int64),
                        ("flags", w.DWORD), ("min_ws", ctypes.c_size_t), ("max_ws", ctypes.c_size_t),
                        ("active_limit", w.DWORD), ("affinity", ctypes.c_size_t),
                        ("priority", w.DWORD), ("scheduling", w.DWORD)]
        class IO(ctypes.Structure):
            _fields_ = [(name, ctypes.c_uint64) for name in
                        ("read_ops", "write_ops", "other_ops", "read_bytes", "write_bytes", "other_bytes")]
        class Extended(ctypes.Structure):
            _fields_ = [("basic", Basic), ("io", IO), ("process_memory", ctypes.c_size_t),
                        ("job_memory", ctypes.c_size_t), ("peak_process", ctypes.c_size_t),
                        ("peak_job", ctypes.c_size_t)]
        class Accounting(ctypes.Structure):
            _fields_ = [(name, ctypes.c_int64) for name in ("user", "kernel", "period_user", "period_kernel")] + [
                (name, w.DWORD) for name in ("page_faults", "total", "active", "terminated")]
        self.accounting = Accounting
        k = ctypes.WinDLL("kernel32", use_last_error=True)
        signatures = {
            "CreateJobObjectW": ([ctypes.c_void_p, w.LPCWSTR], w.HANDLE),
            "SetInformationJobObject": ([w.HANDLE, ctypes.c_int, ctypes.c_void_p, w.DWORD], w.BOOL),
            "QueryInformationJobObject": ([w.HANDLE, ctypes.c_int, ctypes.c_void_p, w.DWORD, ctypes.c_void_p], w.BOOL),
            "OpenProcess": ([w.DWORD, w.BOOL, w.DWORD], w.HANDLE),
            "AssignProcessToJobObject": ([w.HANDLE, w.HANDLE], w.BOOL),
            "TerminateJobObject": ([w.HANDLE, w.UINT], w.BOOL),
            "CloseHandle": ([w.HANDLE], w.BOOL),
        }
        for name, (args, result) in signatures.items():
            function = getattr(k, name); function.argtypes = args; function.restype = result
        self.kernel = k
        self.handle = k.CreateJobObjectW(None, None)
        if not self.handle:
            raise OSError("job_create_failed")
        info = Extended(); info.basic.flags = 0x2000  # JOB_OBJECT_LIMIT_KILL_ON_JOB_CLOSE
        process = None
        try:
            if not k.SetInformationJobObject(self.handle, 9, ctypes.byref(info), ctypes.sizeof(info)):
                raise OSError("job_configure_failed")
            process = k.OpenProcess(0x0100 | 0x0001, False, pid)  # SET_QUOTA | TERMINATE
            if not process or not k.AssignProcessToJobObject(self.handle, process):
                raise OSError("job_assign_failed")
        except BaseException:
            k.CloseHandle(self.handle); self.handle = None
            raise
        finally:
            if process: k.CloseHandle(process)

    def close(self):
        if not self.handle: return True
        try:
            if not self.kernel.TerminateJobObject(self.handle, 1): return False
            until = time.monotonic() + 5
            while time.monotonic() < until:
                counts = self.accounting()
                if not self.kernel.QueryInformationJobObject(self.handle, 1, ctypes.byref(counts), ctypes.sizeof(counts), None):
                    return False
                if counts.active == 0: return True
                time.sleep(.01)
            return False
        finally:
            self.kernel.CloseHandle(self.handle); self.handle = None


@dataclass
class ProcessResult:
    status: str
    elapsed_ms: int
    stdout: bytes = field(default=b"", repr=False)
    stderr_bytes: int = 0
    returncode: int = None
    cleanup_complete: bool = False


def run_process(command, request=b"", deadline=60, cancel=None, max_output=131_072, cancel_at=None):
    """Bound both pipes together, including descendants holding inherited pipes."""
    return _run_process(command, request, deadline, cancel, max_output, cancel_at)


def run_resource_table(command):
    """Capture a complete tool resource table with a fixed, separate metadata budget."""
    return _run_process(command, deadline=15, max_output=4 * 1024 * 1024,
                        output_ceiling=4 * 1024 * 1024)


def _run_process(command, request=b"", deadline=60, cancel=None, max_output=131_072, cancel_at=None,
                 *, output_ceiling=262_144):
    if output_ceiling not in (262_144, 4 * 1024 * 1024):
        raise ValueError("invalid_process_budget")
    if not 0 < deadline <= 180 or not 0 < max_output <= output_ceiling or len(request) > 131_072:
        raise ValueError("invalid_process_budget")
    start = time.monotonic()
    if cancel is not None and cancel.is_set():
        return ProcessResult("cancelled",0,cleanup_complete=True)
    process = None; job = None; readers = []; writer = None
    output = bytearray(); counts = [0, 0]; lock = threading.Lock(); overflow = threading.Event()
    status = "spawn_failed"; cleaned = False
    # Remove development credentials/options from children; no host inference servers are used.
    env = {k:v for k,v in os.environ.items() if not k.upper().startswith(("HF_", "HUGGING_FACE_", "LLAMA_ARG_"))}
    env.update(HF_HUB_OFFLINE="1", TRANSFORMERS_OFFLINE="1")
    try:
        options = {"creationflags":subprocess.CREATE_NO_WINDOW} if os.name == "nt" else {"start_new_session":True}
        process = subprocess.Popen(command, stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                                   stderr=subprocess.PIPE, env=env, bufsize=0, **options)
        if os.name == "nt": job = WindowsJob(process.pid)

        def drain(stream, channel):
            try:
                while True:
                    chunk = stream.read(4096)
                    if not chunk: break
                    with lock:
                        left = max_output - sum(counts)
                        counts[channel] += min(len(chunk), max(0, left))
                        if channel == 0: output.extend(chunk[:max(0, left)])
                        if len(chunk) > left: overflow.set(); break
            except (OSError, ValueError):
                pass  # Cleanup can close a pipe. Its content is never logged.

        def send():
            try:
                remaining=memoryview(request)
                while remaining:
                    written=process.stdin.write(remaining)
                    if not written: break
                    remaining=remaining[written:]
                process.stdin.close()
            except (OSError, ValueError):
                pass

        for channel, stream in enumerate((process.stdout, process.stderr)):
            thread = threading.Thread(target=drain, args=(stream,channel), daemon=True)
            readers.append(thread); thread.start()
        # Input is released only after Windows job assignment succeeds.
        writer = threading.Thread(target=send, daemon=True); writer.start()
        status = "completed"
        while True:
            if overflow.is_set(): status = "output_limit"; break
            if cancel is not None and cancel.is_set(): status = "cancelled"; break
            if cancel_at is not None and time.monotonic()>=cancel_at: status = "cancelled"; break
            if time.monotonic()-start >= deadline: status = "timeout"; break
            if process.poll() is not None and not any(t.is_alive() for t in readers) and not writer.is_alive():
                break
            time.sleep(.01)
    except KeyboardInterrupt:
        status = "cancelled"
    except (OSError, ValueError):
        status = "spawn_failed"
    finally:
        if process is not None:
            if job is not None:
                cleaned = job.close()
            elif os.name != "nt":
                try: os.killpg(process.pid, signal.SIGKILL)
                except ProcessLookupError: pass
                cleaned = True
            else:
                # Before the stdin barrier, the trusted worker cannot launch descendants.
                process.kill()
                cleaned = True
            try: process.wait(timeout=5)
            except subprocess.TimeoutExpired: cleaned = False
            for thread in readers + ([writer] if writer else []): thread.join(timeout=2)
            cleaned = cleaned and not any(t.is_alive() for t in readers) and (writer is None or not writer.is_alive())
            # Never take a buffered pipe lock from a reader which failed to exit.
            # Failed cleanup is reported; do not turn a deadline into a blocking close.
            if cleaned:
                for stream in (process.stdin,process.stdout,process.stderr): stream.close()
        if not cleaned and process is not None: status = "cleanup_failed"
    return ProcessResult(status, round((time.monotonic()-start)*1000), bytes(output), counts[1],
                         process.returncode if process else None, cleaned)


def verify_model(runtime, path):
    _, size, expected = ARTIFACTS[runtime]
    path = Path(path)
    if not path.is_file(): return "model_missing"
    if path.stat().st_size != size: return "model_size_mismatch"
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for block in iter(lambda:source.read(1024*1024),b""): digest.update(block)
    return None if digest.hexdigest() == expected else "model_hash_mismatch"


def parse_worker(data):
    required = {"version","status","text","error","load_ms","generation_ms","output_tokens",
                "input_tokens","schema_enforced","thinking_disabled","template_applied"}
    def unique(pairs):
        value={}
        for key,item in pairs:
            if key in value: raise ValueError("duplicate_key")
            value[key]=item
        return value
    try:
        value = json.loads(data,object_pairs_hook=unique,
                           parse_constant=lambda _: (_ for _ in ()).throw(ValueError("nonfinite")))
        return validate_worker(value,required)
    except (ValueError,UnicodeError,TypeError,RecursionError,OverflowError):
        return None


def validate_worker(value,required):
    if not isinstance(value,dict) or set(value)!=required or type(value["version"]) is not int or value["version"]!=1:
        return None
    if value["status"] not in ("completed","error") or type(value["text"]) is not str:
        return None
    if len(value["text"].encode("utf-8")) > 16_384: return None
    if value["status"]=="completed" and value["error"] is not None: return None
    if value["status"]=="error" and (type(value["error"]) is not str or value["error"] not in WORKER_ERRORS or value["text"]): return None
    for name in ("schema_enforced","thinking_disabled","template_applied"):
        if type(value[name]) is not bool: return None
    for name in ("load_ms","generation_ms"):
        item = value[name]
        if item is not None and (type(item) not in (int,float) or not 0<=item<=180_000 or not math.isfinite(item)): return None
    for name,limit in (("input_tokens",4096),("output_tokens",350)):
        item=value[name]
        if item is not None and (type(item) is not int or not 0<=item<=limit): return None
    return value


def oracle(executable, operation, case, data=b""):
    result = run_process([str(executable),operation,case],data,deadline=10)
    if result.status!="completed" or result.returncode!=0: return None
    try: value=json.loads(result.stdout)
    except (ValueError,UnicodeError,RecursionError): return None
    return value if isinstance(value,dict) else None


def experiment(runtime, python, model, oracle_exe, executable=None, case="gift", deadline=60, cancel=None, cancel_after=None):
    artifact, size, digest = ARTIFACTS[runtime]
    report = {"version":1,"scope":"windows_host_cold_smoke" if os.name=="nt" else "host_cold_smoke",
              "runtime":runtime,"artifact":artifact,"model_bytes":size,"model_sha256":digest,
              "case":case,"attempted_roles":0,"roles":[],"status":"not_started",
              "quality_assessed":False,"phone_qualified":False,"warm_full_turn_measured":False}
    fixture = oracle(oracle_exe,"fixture",case)
    if (fixture is None or set(fixture)!={"version","case","preflight_error","revision","director"}
            or type(fixture["version"]) is not int or fixture["version"]!=1 or fixture["case"]!=case):
        report["status"]="oracle_failed"; return report
    if fixture.get("preflight_error"):
        if type(fixture["preflight_error"]) is not str or fixture["preflight_error"] not in DOMAIN_ERRORS:
            report["status"]="oracle_failed"; return report
        report.update(status="preflight_rejected", domain_error=fixture["preflight_error"])
        return report
    if not isinstance(fixture["director"],dict): report["status"]="oracle_failed"; return report
    try: error=verify_model(runtime,model)
    except OSError: error="model_unreadable"
    if error: report["status"]=error; return report
    command = [str(python),str(ROOT/"benchmarks"/"spike"/runtime/"run.py"),"--model",str(Path(model).resolve())]
    if runtime=="llama":
        if executable is None: report["status"]="runtime_missing"; return report
        command += ["--executable",str(Path(executable).resolve())]
    request=fixture["director"]; proposal=None
    inference_start=time.monotonic()
    cancel_at=None if cancel_after is None else inference_start+cancel_after
    for role_name in ("director","narrator"):
        if request["role"]!=role_name: report["status"]="oracle_failed"; return report
        payload=json.dumps(request,separators=(",",":")).encode("utf-8")
        if len(payload)>32_768: report["status"]="request_too_large"; return report
        report["attempted_roles"]+=1
        remaining=deadline-(time.monotonic()-inference_start)
        result=(run_process(command,payload,remaining,cancel,cancel_at=cancel_at) if remaining>0
                else ProcessResult("timeout",0,cleanup_complete=True))
        aggregate={"role":role_name,"process_status":result.status,"wall_ms":result.elapsed_ms,
                   "cleanup_complete":result.cleanup_complete,"stderr_bytes":result.stderr_bytes}
        report["roles"].append(aggregate)
        if result.status!="completed": report["status"]=result.status; return report
        generated=parse_worker(result.stdout)
        if generated is None: report["status"]="invalid_worker_response"; return report
        aggregate.update({k:v for k,v in generated.items() if k not in ("version","text")})
        if generated["status"]!="completed": report["status"]=generated["error"]; return report
        if result.returncode!=0 or not generated["thinking_disabled"] or not generated["template_applied"]:
            report["status"]="unsupported_output"; return report
        if role_name=="director":
            proposal=generated["text"]
            accepted=oracle(oracle_exe,"validate",case,proposal.encode("utf-8"))
            if (accepted is None or accepted.get("status") not in ("accepted","rejected")
                    or (accepted.get("error") is not None and
                        (type(accepted["error"]) is not str or accepted["error"] not in DOMAIN_ERRORS))):
                report["status"]="oracle_failed"; return report
            aggregate["engine_status"]=accepted.get("status")
            aggregate["engine_error"]=accepted.get("error")
            if accepted.get("status")!="accepted": report["status"]="engine_rejected"; return report
            request=accepted["narrator"]
        else:
            completion=json.dumps({"proposal":proposal,"narration":generated["text"]}).encode("utf-8")
            committed=oracle(oracle_exe,"commit",case,completion)
            if (committed is None or committed.get("status") not in ("committed","rejected")
                    or (committed.get("error") is not None and
                        (type(committed["error"]) is not str or committed["error"] not in DOMAIN_ERRORS))):
                report["status"]="oracle_failed"; return report
            aggregate["engine_status"]=committed.get("status"); aggregate["engine_error"]=committed.get("error")
            report["status"]="committed" if committed.get("status")=="committed" else "engine_rejected"
            # Whitelist engine-owned counters; no generated text or private error is printed.
            for key in ("revision","events","exact_retry_unchanged","recipient_observations","absent_observations"):
                if key in committed: report[key]=committed[key]
    return report


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--runtime",choices=ARTIFACTS,required=True)
    parser.add_argument("--python",type=Path,default=Path(sys.executable))
    parser.add_argument("--model",type=Path,required=True)
    parser.add_argument("--oracle",type=Path,required=True)
    parser.add_argument("--executable",type=Path)
    parser.add_argument("--case",choices=("gift","spent","unlearned"),default="gift")
    parser.add_argument("--deadline",type=float,default=60)
    parser.add_argument("--cancel-after",type=float)
    parser.add_argument("--output",type=Path)
    args=parser.parse_args()
    if not 0<args.deadline<=180 or (args.cancel_after is not None and not 0<args.cancel_after<=args.deadline):
        parser.error("invalid deadline/cancellation budget")
    result=experiment(args.runtime,args.python,args.model,args.oracle,args.executable,args.case,
                      args.deadline,cancel_after=args.cancel_after)
    text=json.dumps(result,indent=2,allow_nan=False)+"\n"
    if args.output: args.output.write_text(text,encoding="utf-8")
    print(text,end="")
    return 0 if result["status"] in ("committed","preflight_rejected") else 2


if __name__=="__main__": raise SystemExit(main())
