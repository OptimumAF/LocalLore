"""Explicit private held-socket probe CLI, never legacy SDK/device admission.

Imports create no output or sockets and instantiate no Windows backend. The
installed interpreter/runtime and standard library remain a trusted tool
boundary; public source closure, the interpreter executable and exposed loaded
Python DLL are byte-bound before/after the supervised worker. A report alone
does not authenticate its acquisition.

The report's process_handles_closed covers only backend-owned native/file
resources. Reused supervisor and pre-backend metadata helpers are separately
source-bound; their handles are not covered by that report flag. Actual worker
closure/capture, final pin checks and external CLI-terminal evidence remain
additional requirements. No blanket all-Win32-handles assertion is made.

Copyright 2026 LocalLore contributors. SPDX-License-Identifier: Apache-2.0
"""
import ctypes
import hashlib
import importlib
import json
import os
from pathlib import Path
import re
import sys

ROOT = Path(__file__).resolve().parents[1]
if __package__ in (None, ""):
    sys.path.insert(0,str(ROOT))
from benchmarks import receipt_avd_environment as env
from benchmarks import windows_tcp_control as output_control
from benchmarks.windows_tcp_observation import decode_table

PROTOCOL = "adb-held-socket-server-owner-v1"
BARRIER = b"LL_ADB_HELD_SOCKET_PROBE_V1\n"
OWNER_SECONDS = 30
MAX_ADMISSION = 16384
MAX_REQUEST = 65536
MAX_REPORT = 512*1024
PUBLIC_SOURCES = (
    "benchmarks/adb_held_socket_probe.py", "benchmarks/adb_held_socket.py",
    "benchmarks/adb_held_socket_windows.py", "benchmarks/windows_tcp_control.py",
    "benchmarks/windows_tcp_observation.py", "benchmarks/receipt_avd_environment.py",
    "benchmarks/runtime_spike.py", "benchmarks/host_commit_capacity.py",
)


class CliRefused(ValueError):
    def __init__(self, reason="request"):
        self.reason = reason if reason in ("platform","output","admission","source","python","request","report") else "request"
        super().__init__(self.reason)


def _need(value, reason="request"):
    if not value:
        raise CliRefused(reason)


def _contract():
    return importlib.import_module("benchmarks.adb_held_socket")


def _same(left, right):
    if type(left) is not type(right):
        return False
    if type(left) is dict:
        return left.keys() == right.keys() and all(_same(left[k],right[k]) for k in left)
    if type(left) is list:
        return len(left) == len(right) and all(_same(a,b) for a,b in zip(left,right))
    return left == right


def _existing_D_file(value, reason):
    _need(type(value) is str and 0 < len(value) <= 2048,reason)
    path = Path(value)
    _need(path.is_absolute() and path.drive.upper() == "D:" and str(path) == os.path.abspath(value),reason)
    for part in path.parts[1:]:
        _need(part and not part.endswith(("."," ")) and
              not any(ord(c) < 32 or c in '<>:"|?*' for c in part) and
              re.fullmatch(r"(?i)(?:con|prn|aux|nul|com[1-9]|lpt[1-9])(?:\..*)?",part) is None,reason)
    env.safe_path(path)
    _need(path.resolve(strict=True) == path,reason)
    return path


def _read_bound(path, expected, cap, reason):
    _need(type(expected) is str and re.fullmatch("[0-9a-f]{64}",expected) is not None,reason)
    path = env.safe_path(path); before = path.stat()
    _need(0 < before.st_size <= cap,reason)
    with path.open("rb") as source:
        held = os.fstat(source.fileno())
        signature = lambda info: (info.st_dev,info.st_ino,info.st_size,info.st_mtime_ns,info.st_ctime_ns)
        _need(signature(held) == signature(before),reason)
        raw = source.read(cap+1)
        _need(signature(held) == signature(os.fstat(source.fileno())),reason)
    env.safe_path(path)
    _need(signature(before) == signature(path.stat()) and len(raw) == before.st_size and
          hashlib.sha256(raw).hexdigest() == expected,reason)
    value = env.decode_json(raw)
    return dict(path=str(path),bytes=len(raw),sha256=expected), value


def _load_admission(value, expected):
    try:
        path = _existing_D_file(value,"admission")
        binding, raw = _read_bound(path,expected,MAX_ADMISSION,"admission")
        admitted = _contract().validate_admission(raw)
        env.check_binding(binding)
        return binding, admitted
    except (OSError,ValueError,TypeError,KeyError,OverflowError,RecursionError,env.EnvironmentRefused):
        raise CliRefused("admission") from None


def _source_bindings():
    try:
        _need(ROOT.drive.upper() == "D:" and ROOT.resolve(strict=True) == ROOT,"source")
        names = list(PUBLIC_SOURCES)
        package = ROOT/"benchmarks/__init__.py"
        if os.path.lexists(package):
            names.append("benchmarks/__init__.py")
        return [env.binding(ROOT/name) for name in sorted(names)]
    except (OSError,ValueError,TypeError,env.EnvironmentRefused):
        raise CliRefused("source") from None


def _python_bindings():
    executable = env.binding(Path(sys.executable))
    runtime = None
    handle = getattr(sys,"dllhandle",None)
    if handle is not None:
        _need(type(handle) is int and handle > 0,"python")
        from ctypes import wintypes
        api = ctypes.WinDLL("kernel32",use_last_error=True).GetModuleFileNameW
        api.argtypes = [ctypes.c_void_p,wintypes.LPWSTR,wintypes.DWORD]
        api.restype = wintypes.DWORD
        buffer = ctypes.create_unicode_buffer(32768)
        count = int(api(ctypes.c_void_p(handle),buffer,len(buffer)))
        _need(0 < count < len(buffer),"python")
        runtime = env.binding(Path(buffer.value))
    return dict(executable=executable,runtime_dll=runtime)


def _check_bindings(sources, python):
    _need(_same(sources,_source_bindings()),"source")
    _need(_same(python,_python_bindings()),"python")
    for row in sources+[python["executable"]]+([python["runtime_dll"]] if python["runtime_dll"] is not None else []):
        env.check_binding(row)


def _set_temporary():
    temporary = env.safe_path(Path("D:/Dev/_Temp"),directory=True)
    _need(temporary.resolve(strict=True) == temporary,"output")
    os.environ.update(TEMP=str(temporary),TMP=str(temporary),TMPDIR=str(temporary))


def _report_bytes(report, admitted):
    """Bound the private serialization; proof authority stays with report_verified."""
    contract = _contract()
    _need(type(report) is dict and set(report) == contract.REPORT_KEYS,"report")
    _need(type(report["version"]) is int and report["version"] == 1 and report["protocol"] == PROTOCOL and
          report["feature_acceptance"] is False and _same(report["admission"],admitted),"report")
    _need(report["status"] in ("verified","refused") and
          (report["reason"] is None if report["status"] == "verified" else
           type(report["reason"]) is str and report["reason"] in contract.REASONS),"report")
    _need(report["request_hex"] == contract.REQUEST.hex(),"report")
    for key in ("request_sent","response_complete","ownership_verified","socket_closed","process_handles_closed"):
        _need(type(report[key]) is bool,"report")
    state = report["client_raw_state"]
    _need(state is None or type(state) is int and 0 <= state <= 2**32-1,"report")
    _need(type(report["elapsed_ms"]) is int and 0 <= report["elapsed_ms"] <= 2**63-1,"report")
    response = report["response_hex"]
    _need(type(response) is str and len(response) <= 26 and re.fullmatch("(?:[0-9a-f]{2})*",response) is not None,"report")
    stages = report["stages"]
    _need(type(stages) is list and len(stages) <= 5,"report")
    allowed = {
        "initial":{"stage","bracket","snapshot"}, "connected":{"stage","endpoint"},
        "presend":{"stage","endpoint_before","endpoint_after","bracket","snapshot"},
        "send_attempt":{"stage"}, "final":{"stage","endpoint","bracket","snapshot"},
    }
    client_port = None
    for stage in stages:
        _need(type(stage) is dict and type(stage.get("stage")) is str and stage["stage"] in allowed and
              set(stage) <= allowed[stage["stage"]],"report")
        if stage["stage"] == "connected" and type(stage.get("endpoint")) is dict:
            client_port = stage["endpoint"].get("local_port")
            _need(type(client_port) is int and 0 < client_port < 65536 and client_port != 5037,"report")
        if "snapshot" not in stage:
            continue
        snapshot = stage["snapshot"]
        _need(type(snapshot) is dict and set(snapshot) == {"abi_checked","tables","rows"},"report")
        _need(type(snapshot["tables"]) is list and len(snapshot["tables"]) == 2 and
              type(snapshot["rows"]) is list and len(snapshot["rows"]) <= 64,"report")
        for table in snapshot["tables"]:
            _need(type(table) is dict and set(table) == {"family","table_class","allocated_bytes","returned_bytes","count","raw_sha256"},"report")
        for record in snapshot["rows"]:
            _need(type(record) is dict and set(record) == {"family","ordinal","raw_hex","raw_sha256","row"},"report")
            family = record["family"]
            _need(type(family) is int and family in (2,23),"report")
            raw_hex = record["raw_hex"]; size = 24 if family == 2 else 56
            _need(type(raw_hex) is str and re.fullmatch("[0-9a-f]{"+str(size*2)+"}",raw_hex) is not None,"report")
            raw = bytes.fromhex(raw_hex)
            row = decode_table(b"\1\0\0\0"+raw,family)[0]
            _need(row.local_port == 5037 or client_port is not None and row.local_port == client_port,"report")
    raw = env.encoded(report)
    _need(0 < len(raw) <= MAX_REPORT,"report")
    return raw


def _write_bytes(path, raw):
    env.safe_path(path,exists=False)
    with path.open("xb") as target:
        _need(target.write(raw) == len(raw),"report"); target.flush(); os.fsync(target.fileno())


def _worker(path, sha):
    _need(sys.stdin.buffer.read(len(BARRIER)+1) == BARRIER,"request")
    path = _existing_D_file(str(path),"request")
    _, request = _read_bound(path,sha,MAX_REQUEST,"request")
    _need(type(request) is dict and set(request) == {"version","protocol","output","admission","validated_admission",
          "owner_seconds","parent","source_closure","python"},"request")
    _need(type(request["version"]) is int and request["version"] == 1 and request["protocol"] == PROTOCOL and
          type(request["owner_seconds"]) is int and request["owner_seconds"] == OWNER_SECONDS,"request")
    output = env.safe_path(request["output"],directory=True)
    _need(output.drive.upper() == "D:" and output.resolve(strict=True) == output and
          not output.is_relative_to(ROOT) and path == output/"request-v1.json","request")
    cwd = Path.cwd()
    _need(cwd.drive.upper() == "D:" and cwd.resolve(strict=True) == cwd and
          all(not os.path.lexists(parent/".git") for parent in (output,*output.parents)),"request")
    _need(env.process_identity(os.getppid()) == request["parent"],"request")
    _check_bindings(request["source_closure"],request["python"])
    bound, admitted = _load_admission(request["admission"]["path"],request["admission"]["sha256"])
    _need(_same(bound,request["admission"]) and _same(admitted,request["validated_admission"]),"admission")
    _set_temporary()
    backend_type = importlib.import_module("benchmarks.adb_held_socket_windows").WindowsBackend
    report = _contract().probe(backend_type(),admitted)
    _write_bytes(output/"report-v1.json",_report_bytes(report,admitted))
    _check_bindings(request["source_closure"],request["python"]); env.check_binding(bound)
    print("held_socket_probe_report_acquired",flush=True)
    return 0


def _snapshot_after(path, function, reason):
    try:
        value = function()
        env.create_json(path,dict(version=1,status="completed",reason=None,bindings=value))
        return value
    except (CliRefused,env.EnvironmentRefused,OSError,ValueError,TypeError,KeyError,OverflowError):
        env.create_json(path,dict(version=1,status="refused",reason=reason,bindings=None))
        return None


def _worker_identity(report, started, python):
    try:
        _need(type(started) is dict and set(started) == {"worker"},"report")
        worker = started["worker"]
        _need(type(worker) is dict and set(worker) == {"pid","creation_filetime","executable"},"report")
        _need(type(worker["pid"]) is int and worker["pid"] > 0 and type(worker["creation_filetime"]) is int and
              worker["creation_filetime"] > 0 and worker["executable"] == python["executable"]["path"],"report")
        return _same(report["stages"][0]["bracket"]["client"],worker)
    except (CliRefused,KeyError,TypeError,IndexError):
        return False


def _dispatch(output, admission, admitted):
    _set_temporary()
    sources = _source_bindings(); python = _python_bindings()
    parent = env.process_identity(os.getpid())
    output = output_control.validate_output(str(output))
    env.check_binding(admission); _check_bindings(sources,python)
    output.mkdir()
    env.create_json(output/"source-closure-before-v1.json",dict(version=1,status="completed",reason=None,bindings=sources))
    env.create_json(output/"python-before-v1.json",dict(version=1,status="completed",reason=None,bindings=python))
    request = dict(version=1,protocol=PROTOCOL,output=str(output),admission=admission,validated_admission=admitted,
                   owner_seconds=OWNER_SECONDS,parent=parent,source_closure=sources,python=python)
    env.create_json(output/"request-v1.json",request)
    def started(child):
        env.create_json(output/"started-v1.json",dict(worker=env.process_identity(child.pid))); return True
    owner = env.supervise([sys.executable,"-I","-S","-B",str(Path(__file__).resolve()),"_worker",
        str(output/"request-v1.json"),env.digest(output/"request-v1.json")],BARRIER,output,OWNER_SECONDS,started)
    env.create_json(output/"owner-result-v1.json",owner)
    after = _snapshot_after(output/"source-closure-after-v1.json",_source_bindings,"source")
    python_after = _snapshot_after(output/"python-after-v1.json",_python_bindings,"python")
    source_equal, python_equal = _same(sources,after), _same(python,python_after)
    known = (owner["status"] == "child_exited" and type(owner["worker_returncode"]) is int and owner["worker_returncode"] == 0
        and owner["cleanup_complete"] is True and owner["output_capture_complete"] is True and owner["stderr_bytes"] == 0)
    acquired = False; verified = False; reason = "owner_failed"; report_pin = None; started_pin = None
    try:
        if os.path.lexists(output/"started-v1.json"):
            started_pin = env.binding(output/"started-v1.json")
        _need(known,"report")
        if not source_equal:
            reason = "source_changed"; raise CliRefused("source")
        if not python_equal:
            reason = "python_changed"; raise CliRefused("python")
        reason = "admission_changed"; env.check_binding(admission)
        report_path = output/"report-v1.json"
        reason = "report_missing"; report_pin = env.binding(report_path)
        reason = "report_invalid"
        _, report = _read_bound(report_path,report_pin["sha256"],MAX_REPORT,"report")
        _report_bytes(report,admitted); env.check_binding(report_pin)
        acquired = True; reason = "proof_refused"
        candidate = _contract().report_verified(report,admitted)
        if candidate is True:
            reason = "worker_identity"
            _need(started_pin is not None,"report")
            _, actual_started = _read_bound(output/"started-v1.json",started_pin["sha256"],MAX_ADMISSION,"report")
            verified = _worker_identity(report,actual_started,python)
            env.check_binding(started_pin)
        _check_bindings(sources,python); env.check_binding(admission); env.check_binding(report_pin)
        if verified:
            reason = None
    except (CliRefused,env.EnvironmentRefused,OSError,ValueError,TypeError,KeyError,OverflowError,RecursionError):
        verified = False
    # Keep both immediate post-owner and final checks. Later mutation must not
    # leave a stale successful source flag or a verified proof in the result.
    final_sources = _snapshot_after(output/"source-closure-final-v1.json",_source_bindings,"source")
    final_python = _snapshot_after(output/"python-final-v1.json",_python_bindings,"python")
    source_equal = source_equal and _same(sources,final_sources)
    python_equal = python_equal and _same(python,final_python)
    if not source_equal:
        acquired = verified = False; reason = "source_changed"
    elif not python_equal:
        acquired = verified = False; reason = "python_changed"
    else:
        try:
            env.check_binding(admission)
        except (env.EnvironmentRefused,OSError,ValueError,TypeError,KeyError,OverflowError):
            acquired = verified = False; reason = "admission_changed"
        if report_pin is not None:
            try:
                env.check_binding(report_pin)
            except (env.EnvironmentRefused,OSError,ValueError,TypeError,KeyError,OverflowError):
                acquired = verified = False; reason = "report_invalid"
        if started_pin is not None:
            try:
                env.check_binding(started_pin)
            except (env.EnvironmentRefused,OSError,ValueError,TypeError,KeyError,OverflowError):
                verified = False; reason = "worker_identity"
    status = "verified" if verified else "refused"
    env.create_json(output/"result-v1.json",dict(version=1,protocol=PROTOCOL,status=status,reason=reason,
        acquisition_completed=acquired,server_proof_verified=verified,feature_acceptance=False,
        sources_equal=source_equal,python_equal=python_equal,admission=admission,
        request=env.binding(output/"request-v1.json"),owner=env.binding(output/"owner-result-v1.json"),
        report=report_pin,worker=started_pin))
    print(json.dumps(dict(status=status,reason=reason,acquisition_completed=acquired,
        server_proof_verified=verified,feature_acceptance=False)),flush=True)
    return 0 if verified else 1


def _arguments(args):
    _need(type(args) is list and len(args) == 6,"request")
    values = {}
    for index in range(0,6,2):
        key, value = args[index:index+2]
        _need(type(key) is str and key in ("--admission","--admission-sha256","--output") and
              key not in values and type(value) is str,"request")
        values[key] = value
    return values


def main(argv=None):
    args = sys.argv[1:] if argv is None else argv
    try:
        if os.name != "nt":
            raise CliRefused("platform")
        if type(args) is list and len(args) == 3 and args[0] == "_worker":
            return _worker(Path(args[1]),args[2])
        if args == ["--help"]:
            print("python -B -m benchmarks.adb_held_socket_probe --admission <D: JSON> --admission-sha256 <sha256> --output <missing physical D: directory>")
            return 0
        options = _arguments(args)
        output = output_control.validate_output(options["--output"])
        binding, admitted = _load_admission(options["--admission"],options["--admission-sha256"])
        return _dispatch(output,binding,admitted)
    except (CliRefused,output_control.ControlRefused,env.EnvironmentRefused,OSError,ValueError,TypeError,KeyError,OverflowError,RecursionError) as error:
        reason = error.reason if type(error) in (CliRefused,output_control.ControlRefused) else "request"
        print(json.dumps(dict(status="refused",reason=reason,acquisition_completed=False,
            server_proof_verified=False,feature_acceptance=False)),flush=True)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
