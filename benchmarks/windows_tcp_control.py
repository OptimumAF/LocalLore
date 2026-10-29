"""Opt-in Windows owned-socket controls; never SDK or service qualification.

Only three sockets created by this process are exercised. Native table rows
are retained only for their owned loopback ports (and PID where supplied).
Acquisition and observed LISTEN consistency are separate outcomes. Unknown
states remain unknown; neither a table class nor a successful exchange repairs
them. Importing this module creates no files or sockets and calls no native API.

Copyright 2026 LocalLore contributors. SPDX-License-Identifier: Apache-2.0
"""
import ctypes
from ctypes import wintypes
from contextlib import ExitStack
import hashlib
import ipaddress
import json
import os
from pathlib import Path
import re
import socket
import struct
import sys
import time

ROOT = Path(__file__).resolve().parents[1]
if __package__ in (None, ""):
    sys.path.insert(0, str(ROOT))
from benchmarks import receipt_avd_environment as env
from benchmarks.windows_tcp_observation import AF_INET, MAX_CAPTURE, MAX_ROWS, decode_table

SCOPE = "owned_loopback_controls_not_ADB_or_device_qualification"
BARRIER = b"LL_OWNED_TCP_CONTROL_V1\n"
PAYLOAD = b"LL_TCP_CONTROL_V1"
MAX_REPORT = 512 * 1024
REFERENCES = (
    "https://learn.microsoft.com/en-us/windows/win32/api/iphlpapi/nf-iphlpapi-getextendedtcptable",
    "https://learn.microsoft.com/en-us/windows/win32/api/tcpmib/ns-tcpmib-mib_tcptable_owner_pid",
    "https://learn.microsoft.com/en-us/windows/win32/api/tcpmib/ns-tcpmib-mib_tcp6table_owner_pid",
    "https://learn.microsoft.com/en-us/windows/win32/api/iprtrmib/ne-iprtrmib-tcp_table_class",
    "https://learn.microsoft.com/en-us/windows/win32/api/iphlpapi/nf-iphlpapi-gettcptable",
    "https://learn.microsoft.com/en-us/windows/win32/api/iphlpapi/nf-iphlpapi-gettcptable2",
    "https://learn.microsoft.com/en-us/windows/win32/api/tcpmib/ns-tcpmib-mib_tcprow2",
)
STAGES = ("bound_not_listening", "after_listen", "after_own_connect_and_accept")
ZERO_FLAGS = ("sdk_calls", "device_calls", "existing_service_connections",
              "existing_process_controls", "host_setting_changes", "server_lifecycle_operations")
EXPECTED_ABI = {
    "2": {"row_bytes": 24, "row_alignment": 4, "table_rows_offset": 4,
          "field_offsets": dict(state=0, local=4, port=8, remote=12, remote_port=16, pid=20)},
    "23": {"row_bytes": 56, "row_alignment": 4, "table_rows_offset": 4,
           "field_offsets": dict(local=0, local_scope_id=16, port=20, remote=24,
                                 remote_scope_id=40, remote_port=44, state=48, pid=52)},
    "GetTcpTable": {"row_bytes": 20, "row_alignment": 4, "table_rows_offset": 4,
                    "field_offsets": dict(state=0, local=4, port=8, remote=12, remote_port=16)},
    "GetTcpTable2": {"row_bytes": 28, "row_alignment": 4, "table_rows_offset": 4,
                     "field_offsets": dict(state=0, local=4, port=8, remote=12,
                                           remote_port=16, pid=20, offload_state=24)},
}


class ControlRefused(ValueError):
    """Fixed diagnostic category; never private paths or exception text."""
    def __init__(self, reason):
        self.reason = reason if reason in ("platform", "output", "layout", "request", "acquisition") else "acquisition"
        super().__init__(self.reason)


def _need(value, reason="acquisition"):
    if not value:
        raise ControlRefused(reason)


def _integer(value, low=0, high=2**32-1):
    _need(type(value) is int and low <= value <= high)
    return value


def _object(value, keys):
    _need(type(value) is dict and set(value) == set(keys))
    return value


def _strict_equal(left, right):
    if type(left) is not type(right):
        return False
    if type(left) is dict:
        return left.keys() == right.keys() and all(_strict_equal(left[k], right[k]) for k in left)
    if type(left) is list:
        return len(left) == len(right) and all(_strict_equal(a, b) for a, b in zip(left, right))
    return left == right


def validate_output(value: str) -> Path:
    """Admit one missing physical D: output directory, without creating it."""
    if os.name != "nt":
        raise ControlRefused("platform")
    try:
        _need(type(value) is str and 0 < len(value) <= 2048, "output")
        path = Path(value)
        _need(path.is_absolute() and path.drive.upper() == "D:" and
              str(path) == os.path.abspath(value), "output")
        _need(not path.exists() and not path.is_symlink(), "output")
        env.safe_path(path, exists=False)
        env.safe_path(path.parent, directory=True)
        _need(path.resolve(strict=False) == path and not path.is_relative_to(ROOT), "output")
        _need(ROOT.drive.upper() == "D:" and ROOT.resolve(strict=True) == ROOT, "output")
        cwd = Path.cwd()
        _need(cwd.drive.upper() == "D:" and cwd.resolve(strict=True) == cwd, "output")
        for ancestor in path.parents:
            _need(not (ancestor/".git").exists(), "output")
        return path
    except (OSError, ValueError, TypeError, env.EnvironmentRefused):
        raise ControlRefused("output") from None


def _prepare_environment():
    temporary = Path("D:/Dev/_Temp")
    env.safe_path(temporary, directory=True)
    _need(temporary.resolve(strict=True) == temporary, "output")
    os.environ.update(TEMP=str(temporary), TMP=str(temporary), TMPDIR=str(temporary))


class Row4(ctypes.Structure):
    _fields_ = [("state", wintypes.DWORD), ("local", wintypes.DWORD), ("port", wintypes.DWORD),
                ("remote", wintypes.DWORD), ("remote_port", wintypes.DWORD), ("pid", wintypes.DWORD)]


class Row6(ctypes.Structure):
    _fields_ = [("local", ctypes.c_ubyte*16), ("local_scope_id", wintypes.DWORD), ("port", wintypes.DWORD),
                ("remote", ctypes.c_ubyte*16), ("remote_scope_id", wintypes.DWORD),
                ("remote_port", wintypes.DWORD), ("state", wintypes.DWORD), ("pid", wintypes.DWORD)]


class BasicRow4(ctypes.Structure):
    _fields_ = Row4._fields_[:5]


class Owner2Row4(ctypes.Structure):
    _fields_ = Row4._fields_ + [("offload_state", wintypes.DWORD)]


class Table4(ctypes.Structure):
    _fields_ = [("count", wintypes.DWORD), ("rows", Row4*1)]


class Table6(ctypes.Structure):
    _fields_ = [("count", wintypes.DWORD), ("rows", Row6*1)]


class BasicTable4(ctypes.Structure):
    _fields_ = [("count", wintypes.DWORD), ("rows", BasicRow4*1)]


class Owner2Table4(ctypes.Structure):
    _fields_ = [("count", wintypes.DWORD), ("rows", Owner2Row4*1)]


def _layout():
    result = {name: dict(row_bytes=ctypes.sizeof(row), row_alignment=ctypes.alignment(row),
              table_rows_offset=table.rows.offset,
              field_offsets={field:getattr(row, field).offset for field, _ in row._fields_})
              for name, row, table in (("2", Row4, Table4), ("23", Row6, Table6),
                  ("GetTcpTable", BasicRow4, BasicTable4), ("GetTcpTable2", Owner2Row4, Owner2Table4))}
    _need(ctypes.sizeof(wintypes.DWORD) == 4 and _strict_equal(result, EXPECTED_ABI), "layout")
    return result


def _decoded_raw(raw, *, basic=False):
    if basic:
        state, local, local_port, remote, remote_port = struct.unpack("<5I", raw)
        return dict(family=2, local_address=str(ipaddress.IPv4Address(local.to_bytes(4,"little"))),
                    local_port=int.from_bytes((local_port & 65535).to_bytes(2,"little"),"big"),
                    remote_address=str(ipaddress.IPv4Address(remote.to_bytes(4,"little"))),
                    remote_port=int.from_bytes((remote_port & 65535).to_bytes(2,"little"),"big"),
                    state=state, pid=None)
    row = decode_table(struct.pack("<I", 1)+raw[:24], AF_INET)[0]
    return dict(family=row.family, local_address=row.local_address, local_port=row.local_port,
                remote_address=row.remote_address, remote_port=row.remote_port, state=row.state, pid=row.pid)


def _check_table(table, ports, pid, kind):
    extended = type(kind) is int
    common = {"family", "initial_return", "final_return", "returned_bytes", "allocated_bytes", "count",
              "count_header_hex", "table_rows_offset", "row_stride", "captured_scope", "selected_rows"}
    _object(table, common | ({"table_class"} if extended else {"api"}))
    _need(type(table["family"]) is int and table["family"] == 2)
    _need(type(table["table_class"]) is int and table["table_class"] == kind if extended else table["api"] == kind)
    stride = 24 if extended else 20 if kind == "GetTcpTable" else 28
    _need(_integer(table["initial_return"]) in (0,122) and _integer(table["final_return"]) == 0)
    returned = _integer(table["returned_bytes"],4,MAX_CAPTURE)
    _need(returned <= _integer(table["allocated_bytes"],4,MAX_CAPTURE))
    count = _integer(table["count"],0,MAX_ROWS)
    _need(type(table["count_header_hex"]) is str and re.fullmatch("[0-9a-f]{8}", table["count_header_hex"]) is not None)
    _need(struct.unpack("<I", bytes.fromhex(table["count_header_hex"]))[0] == count)
    _need(_integer(table["table_rows_offset"]) == 4 and _integer(table["row_stride"]) == stride and 4+count*stride <= returned)
    scope = "exact_owned_PID_and_owned_ports_only" if extended else "selected_owned_loopback_ports_PID_when_API_supplies_PID"
    _need(table["captured_scope"] == scope)
    rows = table["selected_rows"]; _need(type(rows) is list and len(rows) <= 3)
    previous = -1
    for row in rows:
        fields = {"ordinal","original_offset","row_bytes","raw_hex","raw_sha256","family","local_address",
                  "local_port","remote_address","remote_port","state","pid","has_listen_state"}
        _object(row, fields | ({"local_scope_id","remote_scope_id"} if extended else {"selection_owner_pid","offload_state"}))
        ordinal = _integer(row["ordinal"],0,count-1)
        _need(ordinal > previous); previous = ordinal
        _need(_integer(row["original_offset"]) == 4+ordinal*stride and _integer(row["row_bytes"]) == stride)
        _need(type(row["raw_hex"]) is str and re.fullmatch("[0-9a-f]{"+str(stride*2)+"}", row["raw_hex"]) is not None)
        raw = bytes.fromhex(row["raw_hex"])
        _need(type(row["raw_sha256"]) is str and row["raw_sha256"] == hashlib.sha256(raw).hexdigest())
        basic = kind == "GetTcpTable"
        decoded = _decoded_raw(raw, basic=basic)
        _need(all(_strict_equal(row[key], value) for key, value in decoded.items()))
        _need(row["local_address"] == "127.0.0.1" and row["local_port"] in ports and
              type(row["local_port"]) is int and type(row["remote_port"]) is int)
        _need(type(row["state"]) is int and type(row["has_listen_state"]) is bool and row["has_listen_state"] == (row["state"] == 2))
        if extended:
            _need(_integer(row["local_scope_id"]) == _integer(row["remote_scope_id"]) == 0 and row["pid"] == pid)
        else:
            _need(type(row["selection_owner_pid"]) is int and row["selection_owner_pid"] == pid)
            if basic:
                _need(row["pid"] is None and row["offload_state"] is None)
            else:
                _need(row["pid"] == pid and _integer(row["offload_state"]) == struct.unpack_from("<I",raw,24)[0])
    return rows


def _validated_report(report):
    keys = {"version","scope","feature_acceptance","acquisition_completed","own_process","ABI","actions","stages",
            "owned_socket_objects_closed","required_native_LISTEN_state","IPv6_attempted","references", *ZERO_FLAGS}
    _object(report, keys)
    _need(type(report["version"]) is int and report["version"] == 1 and report["scope"] == SCOPE and report["feature_acceptance"] is False)
    _need(report["acquisition_completed"] is True and report["owned_socket_objects_closed"] is True and report["IPv6_attempted"] is False)
    _need(_integer(report["required_native_LISTEN_state"]) == 2 and all(_integer(report[k]) == 0 for k in ZERO_FLAGS))
    process = _object(report["own_process"], ("pid","creation_filetime","executable")); pid = _integer(process["pid"],1)
    _integer(process["creation_filetime"],1,2**64-1)
    _need(type(process["executable"]) is str and 0 < len(process["executable"]) <= 32768 and
          (re.match(r"^[A-Za-z]:[\\/]",process["executable"]) is not None or process["executable"].startswith("/")))
    _need(_strict_equal(report["ABI"],EXPECTED_ABI) and _strict_equal(report["references"],list(REFERENCES)))
    actions = report["actions"]; _need(type(actions) is list and len(actions) == 6)
    names = ("bind_owned_loopback","listen_owned_loopback","connect_only_owned_listener","accept_only_owned_client",
             "one_fixed_owned_loopback_exchange","owned_socket_contexts_closed")
    fields = ({"address","port"},{"address","port"},{"address","port","client_port"},{"peer_address","peer_port"},
              {"bytes"},{"count","all_fileno_minus_one"})
    previous = -1
    for index, (action, name, extra) in enumerate(zip(actions,names,fields)):
        _object(action, {"ordinal","action","elapsed_ns"}|extra)
        _need(_integer(action["ordinal"]) == index and action["action"] == name)
        elapsed = _integer(action["elapsed_ns"],0,2**63-1); _need(elapsed >= previous); previous = elapsed
    port = _integer(actions[0]["port"],1,65535); client = _integer(actions[2]["client_port"],1,65535)
    _need(port != client and 5037 not in (port,client))
    for action in actions[:3]:
        _need(action["address"] == "127.0.0.1" and _integer(action["port"]) == port)
    _need(actions[3]["peer_address"] == "127.0.0.1" and _integer(actions[3]["peer_port"]) == client)
    _need(_integer(actions[4]["bytes"]) == 17 and _integer(actions[5]["count"]) == 3 and actions[5]["all_fileno_minus_one"] is True)
    stages = report["stages"]; _need(type(stages) is list and len(stages) == 3)
    result = []
    for index, stage in enumerate(stages):
        _object(stage, ("stage","socket_acceptconn","owned_ports","native","native_alternatives"))
        _need(stage["stage"] == STAGES[index] and _integer(stage["socket_acceptconn"],0,1) in (0,1))
        ports = [port] if index < 2 else sorted((port,client))
        _need(_strict_equal(stage["owned_ports"],ports))
        _need(type(stage["native"]) is list and len(stage["native"]) == 2 and
              type(stage["native_alternatives"]) is list and len(stage["native_alternatives"]) == 2)
        rows = [_check_table(table,ports,pid,kind) for table,kind in
                zip(stage["native"]+stage["native_alternatives"],(3,5,"GetTcpTable","GetTcpTable2"))]
        result.append((stage["socket_acceptconn"],rows))
    return port, result


def assess_controls(report) -> bool:
    """Assess bounded metadata and raw observations, never authenticate execution.

    Basic GetTcpTable rows contain no PID; their selection label is not ownership
    evidence. Neither this assessment nor a true result qualifies any service.
    """
    try:
        port, stages = _validated_report(report)
        if [stage[0] for stage in stages] != [0,1,1]:
            return False
        if any(row["state"] == 2 for rows in stages[0][1] for row in rows):
            return False
        for _, paths in stages[1:]:
            for rows in paths:
                listening = [row for row in rows if row["state"] == 2]
                if len(listening) != 1 or listening[0]["local_port"] != port:
                    return False
        return True
    except (ControlRefused, ValueError, TypeError, KeyError, OverflowError, AttributeError, RecursionError):
        return False


def _native_table(api, kind, pid, ports):
    size = wintypes.DWORD(0)
    initial = int(api(None,ctypes.byref(size),False,AF_INET,kind,0))
    _need(initial in (0,122) and 4 <= size.value <= MAX_CAPTURE)
    buffer = ctypes.create_string_buffer(size.value)
    returned = int(api(buffer,ctypes.byref(size),False,AF_INET,kind,0))
    _need(returned == 0 and 4 <= size.value <= len(buffer))
    raw_table = buffer.raw[:size.value]
    decoded = decode_table(raw_table, AF_INET)
    selected = []
    for ordinal, actual in enumerate(decoded):
        start = Table4.rows.offset+ordinal*ctypes.sizeof(Row4)
        raw = raw_table[start:start+ctypes.sizeof(Row4)]; row = Row4.from_buffer_copy(raw)
        # Independent native-layout decoding must agree before a row is selected.
        _need((actual.state,actual.pid,actual.local_address,actual.local_port,actual.remote_address,actual.remote_port) ==
              (int(row.state),int(row.pid),socket.inet_ntop(socket.AF_INET,struct.pack("<I",row.local)),socket.ntohs(int(row.port)&65535),
               socket.inet_ntop(socket.AF_INET,struct.pack("<I",row.remote)),socket.ntohs(int(row.remote_port)&65535)), "layout")
        if actual.pid != pid or actual.local_port not in ports or actual.local_address != "127.0.0.1":
            continue
        selected.append(dict(ordinal=ordinal,original_offset=start,row_bytes=24,raw_hex=raw.hex(),
            raw_sha256=hashlib.sha256(raw).hexdigest(),family=2,local_address=actual.local_address,
            local_port=actual.local_port,remote_address=actual.remote_address,remote_port=actual.remote_port,
            state=actual.state,pid=actual.pid,local_scope_id=0,remote_scope_id=0,has_listen_state=actual.state == 2))
    _need(len(selected) <= 3)
    return dict(family=2,table_class=kind,initial_return=initial,final_return=returned,returned_bytes=size.value,
                allocated_bytes=len(buffer),count=len(decoded),count_header_hex=raw_table[:4].hex(),
                table_rows_offset=4,row_stride=24,captured_scope="exact_owned_PID_and_owned_ports_only",selected_rows=selected)


def _alternative_table(api, name, rowtype, tabletype, pid, ports):
    size = wintypes.ULONG(0)
    initial = int(api(None,ctypes.byref(size),False))
    _need(initial in (0,122) and 4 <= size.value <= MAX_CAPTURE)
    buffer = ctypes.create_string_buffer(size.value)
    returned = int(api(buffer,ctypes.byref(size),False))
    _need(returned == 0 and 4 <= size.value <= len(buffer))
    count = struct.unpack_from("<I",buffer.raw)[0]; stride = ctypes.sizeof(rowtype); offset = tabletype.rows.offset
    _need(count <= MAX_ROWS and offset+count*stride <= size.value)
    selected = []
    for ordinal in range(count):
        start = offset+ordinal*stride; raw = buffer.raw[start:start+stride]; row = rowtype.from_buffer_copy(raw)
        port = socket.ntohs(int(row.port)&65535); address = socket.inet_ntop(socket.AF_INET,struct.pack("<I",row.local))
        if port not in ports or address != "127.0.0.1":
            continue
        observed_pid = int(row.pid) if hasattr(row,"pid") else None
        if observed_pid is not None and observed_pid != pid:
            continue
        selected.append(dict(ordinal=ordinal,original_offset=start,row_bytes=stride,raw_hex=raw.hex(),
            raw_sha256=hashlib.sha256(raw).hexdigest(),family=2,local_address=address,local_port=port,
            remote_address=socket.inet_ntop(socket.AF_INET,struct.pack("<I",row.remote)),
            remote_port=socket.ntohs(int(row.remote_port)&65535),state=int(row.state),pid=observed_pid,
            selection_owner_pid=pid,offload_state=int(row.offload_state) if hasattr(row,"offload_state") else None,
            has_listen_state=int(row.state) == 2))
    _need(len(selected) <= 3)
    return dict(api=name,family=2,initial_return=initial,final_return=returned,returned_bytes=size.value,
                allocated_bytes=len(buffer),count=count,count_header_hex=buffer.raw[:4].hex(),table_rows_offset=offset,
                row_stride=stride,captured_scope="selected_owned_loopback_ports_PID_when_API_supplies_PID",selected_rows=selected)


def _run_controls(output):
    abi = _layout(); own = env.process_identity(os.getpid())
    dll = ctypes.WinDLL("iphlpapi",use_last_error=True)
    extended = dll.GetExtendedTcpTable
    extended.argtypes = [ctypes.c_void_p,ctypes.POINTER(wintypes.DWORD),wintypes.BOOL,wintypes.ULONG,ctypes.c_int,wintypes.ULONG]
    extended.restype = wintypes.DWORD
    basic, owner2 = dll.GetTcpTable, dll.GetTcpTable2
    for alternate in (basic,owner2):
        alternate.argtypes = [ctypes.c_void_p,ctypes.POINTER(wintypes.ULONG),wintypes.BOOL]
        alternate.restype = wintypes.ULONG
    sockets = []; actions = []; stages = []; completed = False; started = time.monotonic_ns()
    def action(name, **fields):
        actions.append(dict(ordinal=len(actions),action=name,elapsed_ns=time.monotonic_ns()-started,**fields))
    def observe(name, listener, ports):
        _need(env.process_identity(os.getpid()) == own)
        stages.append(dict(stage=name,socket_acceptconn=listener.getsockopt(socket.SOL_SOCKET,socket.SO_ACCEPTCONN),
            owned_ports=sorted(ports),native=[_native_table(extended,kind,own["pid"],ports) for kind in (3,5)],
            native_alternatives=[_alternative_table(basic,"GetTcpTable",BasicRow4,BasicTable4,own["pid"],ports),
                _alternative_table(owner2,"GetTcpTable2",Owner2Row4,Owner2Table4,own["pid"],ports)]))
    try:
        with ExitStack() as resources:
            listener = resources.enter_context(socket.socket(socket.AF_INET,socket.SOCK_STREAM)); sockets.append(listener)
            listener.settimeout(2); listener.setsockopt(socket.SOL_SOCKET,socket.SO_EXCLUSIVEADDRUSE,1)
            listener.bind(("127.0.0.1",0)); address, port = listener.getsockname()
            _need(address == "127.0.0.1" and type(port) is int and 0 < port < 65536 and port != 5037)
            action("bind_owned_loopback",address=address,port=port); observe(STAGES[0],listener,{port})
            listener.listen(1); action("listen_owned_loopback",address=address,port=port); observe(STAGES[1],listener,{port})
            client = resources.enter_context(socket.socket(socket.AF_INET,socket.SOCK_STREAM)); sockets.append(client); client.settimeout(2)
            client.connect((address,port)); client_address, client_port = client.getsockname()
            _need(client_address == "127.0.0.1" and 0 < client_port < 65536 and client_port != 5037)
            action("connect_only_owned_listener",address=address,port=port,client_port=client_port)
            accepted, peer = listener.accept(); resources.enter_context(accepted); sockets.append(accepted); accepted.settimeout(2)
            _need(peer == client.getsockname()); action("accept_only_owned_client",peer_address=peer[0],peer_port=peer[1])
            observe(STAGES[2],listener,{port,client_port}); client.sendall(PAYLOAD)
            received = bytearray()
            while len(received) < len(PAYLOAD):
                part = accepted.recv(len(PAYLOAD)-len(received))
                _need(0 < len(part) <= len(PAYLOAD)-len(received)); received.extend(part)
            _need(bytes(received) == PAYLOAD); action("one_fixed_owned_loopback_exchange",bytes=len(PAYLOAD))
        completed = True
    finally:
        closed = all(item.fileno() == -1 for item in sockets)
        action("owned_socket_contexts_closed",count=len(sockets),all_fileno_minus_one=closed)
        report = dict(version=1,scope=SCOPE,feature_acceptance=False,acquisition_completed=completed,own_process=own,ABI=abi,
            actions=actions,stages=stages,owned_socket_objects_closed=closed,required_native_LISTEN_state=2,IPv6_attempted=False,
            **{key:0 for key in ZERO_FLAGS},references=list(REFERENCES))
        env.create_json(output/"controls-v1.json",report)
    _need(completed and closed)


def _worker(request_path, request_sha):
    _need(sys.stdin.buffer.read(len(BARRIER)+1) == BARRIER,"request")
    request = env.read_bound_json(request_path,request_sha)
    _object(request,("version","scope","output","max_owner_seconds","pins"))
    _need(type(request["version"]) is int and request["version"] == 1 and request["scope"] == SCOPE and request["max_owner_seconds"] == 30,"request")
    output = env.safe_path(request["output"],directory=True)
    _need(output.drive.upper() == "D:" and not output.is_relative_to(ROOT) and request_path == output/"request-v1.json","request")
    _need(type(request["pins"]) is list and len(request["pins"]) == 5,"request")
    for pin in request["pins"]:
        env.check_binding(pin)
    _prepare_environment(); _run_controls(output)
    for pin in request["pins"]:
        env.check_binding(pin)
    print("owned_socket_control_acquisition_completed",flush=True)
    return 0


def _dispatch(output):
    _prepare_environment(); output.mkdir()
    pins = [env.binding(path) for path in (Path(__file__).resolve(),Path(sys.executable),
        ROOT/"benchmarks/receipt_avd_environment.py",ROOT/"benchmarks/runtime_spike.py",ROOT/"benchmarks/windows_tcp_observation.py")]
    request = dict(version=1,scope=SCOPE,output=str(output),max_owner_seconds=30,pins=pins)
    env.create_json(output/"request-v1.json",request)
    def started(child):
        env.create_json(output/"started-v1.json",dict(worker=env.process_identity(child.pid))); return True
    owner = env.supervise([sys.executable,"-I","-B",str(Path(__file__).resolve()),"_worker",str(output/"request-v1.json"),
        env.digest(output/"request-v1.json")],BARRIER,output,30,started)
    env.create_json(output/"owner-result-v1.json",owner)
    acquired = (owner["status"] == "child_exited" and type(owner["worker_returncode"]) is int and owner["worker_returncode"] == 0
        and owner["cleanup_complete"] is True and owner["output_capture_complete"] is True and owner["stderr_bytes"] == 0)
    report_path = output/"controls-v1.json"; report_pin = None; consistent = None
    try:
        for pin in pins:
            env.check_binding(pin)
        if report_path.exists():
            report_pin = env.binding(report_path); _need(report_pin["bytes"] <= MAX_REPORT)
            report = env.read_bound_json(report_path,report_pin["sha256"])
            _validated_report(report)
            acquired = acquired and report["acquisition_completed"] is True and report["owned_socket_objects_closed"] is True
            if acquired:
                consistent = assess_controls(report)
            env.check_binding(report_pin)
        else:
            acquired = False
    except (ControlRefused,env.EnvironmentRefused,OSError,ValueError,TypeError,KeyError,OverflowError):
        acquired = False; consistent = None
    status = "completed" if acquired and consistent is True else "observation_inconsistent" if acquired else "acquisition_failed"
    env.create_json(output/"result-v1.json",dict(version=1,scope=SCOPE,status=status,acquisition_completed=acquired,
        listener_state_consistent=consistent,feature_acceptance=False,owner=env.binding(output/"owner-result-v1.json"),report=report_pin))
    print(json.dumps(dict(status=status,acquisition_completed=acquired,listener_state_consistent=consistent,feature_acceptance=False)),flush=True)
    return 0 if status == "completed" else 2 if status == "observation_inconsistent" else 1


def main(argv=None):
    """Run only after explicit CLI selection; no implicit socket or output use."""
    args = sys.argv[1:] if argv is None else argv
    try:
        if os.name != "nt":
            raise ControlRefused("platform")
        if type(args) is list and len(args) == 3 and args[0] == "_worker":
            return _worker(Path(args[1]),args[2])
        if args == ["--help"]:
            print("python -B -m benchmarks.windows_tcp_control --output <missing physical D: directory outside repository>")
            return 0
        _need(type(args) is list and len(args) == 2 and args[0] == "--output","request")
        return _dispatch(validate_output(args[1]))
    except (ControlRefused,env.EnvironmentRefused,OSError,ValueError,TypeError,KeyError,OverflowError) as error:
        reason = error.reason if type(error) is ControlRefused else "acquisition"
        print(json.dumps(dict(status="acquisition_failed",reason=reason,acquisition_completed=False,
            listener_state_consistent=None,feature_acceptance=False)),flush=True)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
