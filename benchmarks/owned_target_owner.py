"""Explicit finite owner and live observer for one admitted fresh emulator.

Host-only leases are never target authority. Importing this module performs no
native observation, credential access, process launch or socket operation.
Copyright 2026 LocalLore contributors. SPDX-License-Identifier: Apache-2.0
"""
from __future__ import annotations

import copy
import ctypes
from ctypes import wintypes
from dataclasses import asdict
import hashlib
import json
import math
import os
from pathlib import Path
import re
import socket
import subprocess
import sys
import threading
import time

ROOT = Path(__file__).resolve().parents[1]
if __package__ in (None, ""):
    sys.path.insert(0, str(ROOT))
from benchmarks import owned_target_contract as contract
from benchmarks import android_process_verification_v4 as verification
from benchmarks import isolated_adb_owner as primitives
from benchmarks import isolated_adb_lease as server_contract
from benchmarks import adb_held_socket_probe as file_guard
from benchmarks import adb_held_socket_windows as native
from benchmarks import receipt_avd_environment as environment
from benchmarks import windows_tcp_control as output_control
from benchmarks.windows_tcp_observation import decode_table

CAP = 262144
BARRIER = b"LL_OWNED_TARGET_OWNER_V1\n"


class OwnerRefused(ValueError):
    pass


def _need(value, reason="owner"):
    if not value:
        raise OwnerRefused(reason)


def _same(left, right):
    return file_guard._same(left, right)


def _read_json(pin, cap=2 * 1024 * 1024):
    contract.binding(copy.deepcopy(pin))
    _, value = file_guard._read_bound(Path(pin["path"]), pin["sha256"], cap, "source")
    environment.check_binding(pin)
    return value


def _observe(api, *, guest=False):
    """Keep all and only the frozen local-or-remote port scope, raw state intact."""
    native._check_abi()
    rows, tables = [], []
    ports = (5592, 5593) if guest else (contract.PORT,)
    for family in (2, 23):
        table = api.capture(family)
        decoded = decode_table(table.raw, family)
        stride = 24 if family == 2 else 56
        tables.append(dict(family=family, table_class=5, allocated_bytes=table.allocated_bytes,
            returned_bytes=len(table.raw), count=len(decoded),
            raw_sha256=hashlib.sha256(table.raw).hexdigest(), abi_checked=True))
        for ordinal, row in enumerate(decoded):
            if row.local_port in ports or row.remote_port in ports:
                _need(len(rows) < 128, "observation")
                value = asdict(row)
                value.update(ordinal=ordinal,
                    raw_hex=table.raw[4 + ordinal * stride:4 + (ordinal + 1) * stride].hex())
                rows.append(value)
    result = dict(version=1, families=[2, 23], rows=rows)
    result["ports" if guest else "port"] = [5592, 5593] if guest else contract.PORT
    return result, tables


def _endpoint(item):
    local, peer = item.getsockname(), item.getpeername()
    result = dict(local_address=local[0], local_port=local[1], peer_address=peer[0], peer_port=peer[1])
    _need(result["local_address"] == result["peer_address"] == "127.0.0.1" and
          type(local[1]) is int and 0 < local[1] <= 65535 and
          local[1] not in (5037, contract.PORT, 5592, 5593) and peer[1] == contract.PORT, "tuple")
    return result


def _anchor(item):
    local = item.getsockname()
    return dict(handle=item.fileno(), socket_id=id(item), local_address=local[0], local_port=local[1])


class _BasicProcessInformation(ctypes.Structure):
    # Microsoft PROCESS_BASIC_INFORMATION, pointer-width-aware natural ABI.
    _fields_ = [("exit_status", wintypes.LONG), ("peb", ctypes.c_void_p),
        ("affinity", ctypes.c_size_t), ("priority", wintypes.LONG),
        ("pid", ctypes.c_size_t), ("parent_pid", ctypes.c_size_t)]


class _JobProcessIds(ctypes.Structure):
    _fields_ = [("assigned", wintypes.DWORD), ("count", wintypes.DWORD),
                ("pids", ctypes.c_size_t * 512)]


class _ProcessApi(native._WindowsApi):
    def __init__(self):
        super().__init__()
        _need(ctypes.sizeof(ctypes.c_void_p) == 8 and ctypes.sizeof(_BasicProcessInformation) == 48 and
              [getattr(_BasicProcessInformation, name).offset for name, _ in _BasicProcessInformation._fields_]
              == [0, 8, 16, 24, 32, 40] and _JobProcessIds.pids.offset == 8, "abi")
        # Official definitions: learn.microsoft.com/windows/win32/api/winternl/
        # nf-winternl-ntqueryinformationprocess and jobapi2/QueryInformationJobObject.
        system = ctypes.WinDLL("ntdll", use_last_error=True)
        kernel = ctypes.WinDLL("kernel32", use_last_error=True)
        self._basic = system.NtQueryInformationProcess
        self._basic.argtypes = [wintypes.HANDLE, ctypes.c_int, ctypes.c_void_p,
                                wintypes.ULONG, ctypes.POINTER(wintypes.ULONG)]
        self._basic.restype = wintypes.LONG
        self._job = kernel.QueryInformationJobObject
        self._job.argtypes = [wintypes.HANDLE, ctypes.c_int, ctypes.c_void_p,
                              wintypes.DWORD, ctypes.POINTER(wintypes.DWORD)]
        self._job.restype = wintypes.BOOL
        self._terminate = kernel.TerminateProcess
        self._terminate.argtypes = [wintypes.HANDLE, wintypes.UINT]
        self._terminate.restype = wintypes.BOOL
        self._exit = kernel.GetExitCodeProcess
        self._exit.argtypes = [wintypes.HANDLE, ctypes.POINTER(wintypes.DWORD)]
        self._exit.restype = wintypes.BOOL

    def open_process(self, pid):
        handle = self._open(0x0400 | 0x1000 | 0x100000, False, pid)
        _need(handle not in (None, 0), "identity")
        return handle

    def open_guest(self, pid):
        handle = self._open(0x0400 | 0x1000 | 0x100000 | 0x0001, False, pid)
        _need(handle not in (None, 0), "identity")
        return handle

    def terminate_guest(self, handle):
        _need(self._terminate(handle, 1), "cleanup")

    def wait_guest(self, handle):
        _need(self._wait(handle, 5000) == 0, "cleanup")
        code = wintypes.DWORD()
        _need(self._exit(handle, ctypes.byref(code)), "cleanup")
        return int(code.value)

    def parent_pid(self, handle):
        value, returned = _BasicProcessInformation(), wintypes.ULONG()
        _need(self._basic(handle, 0, ctypes.byref(value), ctypes.sizeof(value), ctypes.byref(returned)) == 0 and
              returned.value == ctypes.sizeof(value) and value.pid == self.identity(handle)["pid"] and
              0 < value.parent_pid <= 2**32 - 1, "ancestry")
        return int(value.parent_pid)

    def current_job_pids(self):
        value, returned = _JobProcessIds(), wintypes.DWORD()
        # NULL selects the calling worker's immediate actual inherited job.
        # One fixed bounded acquisition; an incomplete roster refuses.
        _need(self._job(None, 3, ctypes.byref(value), ctypes.sizeof(value), ctypes.byref(returned)) and
              0 < value.count == value.assigned <= 512 and
              8 + value.count * ctypes.sizeof(ctypes.c_size_t) <= returned.value <= ctypes.sizeof(value), "job")
        pids = [int(value.pids[i]) for i in range(value.count)]
        _need(all(0 < pid <= 2**32 - 1 for pid in pids) and len(set(pids)) == len(pids), "job")
        return sorted(pids)


def _held_handle(handles, pid):
    matches = [handle for handle, value in handles.handles.items()
               if value is not None and value["pid"] == pid]
    _need(bool(matches), "identity")
    return matches[0]


def _check_ancestry(api, handles, chain):
    handles.guard()
    for parent, child in zip(chain, chain[1:]):
        _need(api.parent_pid(_held_handle(handles, child["pid"])) == parent["pid"] and
              parent["creation_filetime"] <= child["creation_filetime"], "ancestry")


class LiveOwnedTarget:
    """One observer's held handles; never a borrowed job or target lifecycle owner."""

    def __init__(self, admission_binding, running_binding):
        self._closed = True
        self._api = None
        self._handles = None
        self._last_time = None
        self._clock_lock = threading.Lock()
        try:
            _need(os.name == "nt", "platform")
            self._admission_binding = copy.deepcopy(admission_binding)
            self._running_binding = copy.deepcopy(running_binding)
            self._admission = contract.validate_admission(_read_json(self._admission_binding))
            self._descriptor = contract.validate_running(_read_json(self._running_binding),
                self._admission, self._admission_binding)
            _need(Path(self._running_binding["path"]) == Path(self._admission["root"]) / "running-v1.json", "binding")
            contract.revalidate_inputs(self._admission)
            self._api = _ProcessApi()
            self._handles = primitives.ProcessHandles(self._api)
            _, self._caller = self._handles.add(os.getpid())
            _need(self._caller["executable"] == self._admission["python"]["executable"]["path"], "identity")
            for key in ("owner", "worker", "server", "launcher", "guest"):
                self._handles.add(self._descriptor[key]["pid"], self._descriptor[key])
            for identity in self._descriptor["guest_ancestry"]:
                if not any(value is not None and value["pid"] == identity["pid"]
                           for value in self._handles.handles.values()):
                    self._handles.add(identity["pid"], identity)
            self._closed = False
            self._deadline = time.monotonic() + self._descriptor["deadline_epoch"] - time.time()
            self.guard()
        except BaseException:
            self.close()
            raise OwnerRefused("target") from None

    @property
    def admission(self):
        return copy.deepcopy(self._admission)

    @property
    def descriptor(self):
        return copy.deepcopy(self._descriptor)

    @property
    def admission_binding(self):
        return copy.deepcopy(self._admission_binding)

    @property
    def running_binding(self):
        return copy.deepcopy(self._running_binding)

    @property
    def caller(self):
        return copy.deepcopy(self._caller)

    def fast_guard(self):
        _need(not self._closed, "closed")
        with self._clock_lock:
            current = time.monotonic()
            _need(type(current) in (int, float) and math.isfinite(current) and
                  (self._last_time is None or current >= self._last_time) and current < self._deadline, "deadline")
            self._last_time = current
        wall = time.time()
        _need(self._descriptor["started_epoch"] <= wall < self._descriptor["deadline_epoch"], "deadline")
        self._handles.guard()
        _check_ancestry(self._api, self._handles, self._descriptor["guest_ancestry"])
        stop = Path(self._admission["root"]) / "stop-v1.json"
        if os.path.lexists(stop):
            contract.check_stop(_read_json(environment.binding(stop)), self._admission_binding["sha256"])
            raise OwnerRefused("stop")

    def guard(self, min_seconds=0):
        _need(type(min_seconds) in (int, float) and math.isfinite(min_seconds) and min_seconds >= 0, "deadline")
        self.fast_guard()
        _need(self._deadline - time.monotonic() >= min_seconds and
              self._descriptor["deadline_epoch"] - time.time() >= min_seconds, "deadline")
        contract.revalidate_inputs(self._admission)
        _need(_same(_read_json(self._admission_binding), self._admission) and
              _same(_read_json(self._running_binding), self._descriptor), "source")
        observation, tables = _observe(self._api, guest=True)
        contract.validate_guest_observation(observation, self._descriptor["guest"], self._descriptor["server"])
        server_contract._tables(tables, observation)
        self.fast_guard()

    def _bracket(self):
        self.guard()
        result = {key: copy.deepcopy(self._descriptor[key]) for key in ("owner", "worker", "server", "launcher", "guest")}
        result.update(sources=contract.source_bindings(), python=file_guard._python_bindings(),
                      server_alive=True, guest_alive=True)
        return result

    def claim_once(self, kind, operation_sha256):
        self.guard()
        _need(kind in ("import", "author") and type(operation_sha256) is str and
              re.fullmatch("[0-9a-f]{64}", operation_sha256) is not None, "claim")
        root = Path(self._admission["root"]) / "claims-v1"
        if not os.path.lexists(root):
            try:
                root.mkdir(exist_ok=False)
            except FileExistsError:
                pass
        environment.safe_path(root, directory=True)
        path = output_control.validate_output(str(root / (kind + "-v1.json")))
        # A durable claim is spent even if a later pre-dispatch guard refuses.
        environment.create_json(path, dict(version=1, protocol=contract.PROTOCOL,
            admission_sha256=self._admission_binding["sha256"], kind=kind,
            operation_sha256=operation_sha256, caller=self.caller))
        self.guard()

    def _query(self, kind):
        _need(kind in ("version", "devices"), "query")
        request = b"000Chost:version" if kind == "version" else b"000Ehost:devices-l"
        record = dict(kind=kind, request_hex=request.hex(), response_hex="", endpoint=None,
            anchor=None, brackets={"before": None, "after": None}, observation_before=None,
            observation_after=None, tables_before=None, tables_after=None,
            eof=False, socket_closed=False, elapsed_ms=0)
        item, received, failure = None, bytearray(), None
        begin = time.monotonic()
        until = min(self._deadline, getattr(self, "_query_deadline", self._deadline), begin + 3)
        try:
            self.guard()
            item = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            item.setsockopt(socket.SOL_SOCKET, socket.SO_EXCLUSIVEADDRUSE, 1)
            item.bind(("127.0.0.1", 0))
            record["anchor"] = _anchor(item)
            item.settimeout(_left(until))
            item.connect(("127.0.0.1", contract.PORT))
            record["endpoint"] = _endpoint(item)
            record["brackets"]["before"] = self._bracket()
            observation, tables = _observe(self._api)
            record["observation_before"], record["tables_before"] = observation, tables
            contract.validate_observation(observation, self._descriptor["server"], self._caller,
                record["endpoint"], self._descriptor["guest"], after=False)
            server_contract._tables(tables, observation)
            _need(_same(_anchor(item), record["anchor"]), "tuple")
            self.fast_guard()
            _send(item, request, until, self.fast_guard)
            _receive_host(item, received, until, self.fast_guard)
            record["eof"] = True
            if kind == "version":
                _need(bytes(received) == b"OKAY00040029", "version")
            else:
                if self._descriptor["transport_id"] is None:
                    _waiting_devices(bytes(received)[8:])
                else:
                    _need(contract.device_transport(bytes(received)[8:]) == self._descriptor["transport_id"], "target")
            _need(_same(_anchor(item), record["anchor"]) and
                  _same(_endpoint(item), record["endpoint"]), "tuple")
            observation, tables = _observe(self._api)
            record["observation_after"], record["tables_after"] = observation, tables
            contract.validate_observation(observation, self._descriptor["server"], self._caller,
                record["endpoint"], self._descriptor["guest"], after=True)
            server_contract._tables(tables, observation)
            record["brackets"]["after"] = self._bracket()
            _left(until)
        except BaseException as error:
            failure = error
        finally:
            record["response_hex"] = received.hex()
            if item is not None:
                try:
                    item.close()
                    record["socket_closed"] = item.fileno() == -1
                except (OSError, ValueError):
                    pass
            record["elapsed_ms"] = math.ceil(max(0, time.monotonic() - begin) * 1000)
            if not record["socket_closed"]:
                failure = OwnerRefused("cleanup")
        return record, failure

    def prove(self, path, session, context, socket, anchor, after=False):
        """Observe the same held client socket, plus two separately closed queries."""
        self.guard()
        session = contract.validate_session(copy.deepcopy(session), self._admission)
        _need(_same(session["descriptor"], self._descriptor) and
              _same(session["caller"], self._caller) and type(after) is bool, "session")
        expected = Path(session["root"]) / "proofs" / ("command-%04d-%s.json" % (context["index"], context["phase"]))
        _need(Path(path) == expected and context["phase"] == ("after" if after else "before"), "proof")
        path = output_control.validate_output(str(path))
        session_binding = environment.binding(Path(session["root"]) / "sdk-session-v4.json")
        _need(_same(_read_json(session_binding), session), "session")
        _need(_same(_anchor(socket), anchor), "tuple")
        endpoint = _endpoint(socket)
        begin = time.monotonic()
        before = self._bracket()
        observation, tables = _observe(self._api)
        contract.validate_observation(observation, self._descriptor["server"], self._caller,
            endpoint, self._descriptor["guest"], after=after)
        server_contract._tables(tables, observation)
        queries = []
        query_path = output_control.validate_output(str(path.with_name(path.stem + "-queries-v1.json")))
        for kind in ("version", "devices"):
            query, failure = self._query(kind)
            queries.append(query)
            if failure is not None:
                environment.create_json(query_path, dict(version=1, protocol=contract.PROOF_PROTOCOL,
                    admission=self.admission_binding, running=self.running_binding, caller=self.caller, queries=queries))
                raise OwnerRefused("query") from None
        environment.create_json(query_path, dict(version=1, protocol=contract.PROOF_PROTOCOL,
            admission=self.admission_binding, running=self.running_binding, caller=self.caller, queries=queries))
        contract.validate_query_bundle(_read_json(environment.binding(query_path)), self._descriptor,
            self._caller, self.admission_binding, self.running_binding)
        _need(_same(_anchor(socket), anchor) and _same(_endpoint(socket), endpoint), "tuple")
        after_bracket = self._bracket()
        proof = dict(version=1, protocol=contract.PROOF_PROTOCOL, session=session_binding,
            context=copy.deepcopy(context), admission=self.admission_binding, running=self.running_binding,
            caller=self.caller, endpoint=endpoint, anchor=copy.deepcopy(anchor),
            brackets=dict(before=before, after=after_bracket), observation=observation, tables=tables,
            version_response_hex=queries[0]["response_hex"], devices_response_hex=queries[1]["response_hex"],
            queries=environment.binding(query_path), after_request=after,
            elapsed_ms=math.ceil(max(0, time.monotonic() - begin) * 1000))
        contract.validate_proof(copy.deepcopy(proof), session, copy.deepcopy(context))
        self.guard()
        environment.create_json(path, proof)
        binding = environment.binding(path)
        verification.verify_proof(binding, session, copy.deepcopy(context))
        self.guard()
        return binding

    def close(self):
        self._closed = True
        return self._handles.close() if self._handles is not None else True


def _left(until):
    value = until - time.monotonic()
    _need(math.isfinite(value) and value > 0, "deadline")
    return value


def _send(item, raw, until, guard):
    rest = memoryview(raw)
    while rest:
        guard()
        item.settimeout(min(.25, _left(until)))
        try:
            size = item.send(rest)
        except socket.timeout:
            continue
        _need(type(size) is int and 0 < size <= len(rest), "framing")
        rest = rest[size:]


def _receive_host(item, received, until, guard):
    expected = None
    while True:
        guard()
        item.settimeout(min(.25, _left(until)))
        try:
            raw = item.recv(min(4097, 4105 - len(received)))
        except socket.timeout:
            continue
        _need(type(raw) is bytes, "framing")
        if not raw:
            _need(expected is not None and len(received) == expected, "framing")
            return
        received.extend(raw)
        _need(len(received) <= 4104 and (len(received) < 4 or received[:4] == b"OKAY"), "framing")
        if len(received) >= 8:
            _need(re.fullmatch(b"[0-9a-fA-F]{4}", received[4:8]) is not None, "framing")
            expected = 8 + int(received[4:8], 16)
            _need(expected <= 4104 and len(received) <= expected, "framing")


def _waiting_devices(raw):
    state, transport = contract.device_status(raw)
    return transport if state == "device" else None


class _InitialServerView:
    """Adapter for fixed pre-guest host exchanges, never live v2 authority."""
    def __init__(self, runtime, binding):
        self.runtime = runtime
        self.admission = copy.deepcopy(runtime.admission["server"])
        self.binding = copy.deepcopy(binding)
        self.completed_ports = []
        self.clients_closed = True

    def __getattr__(self, key):
        return getattr(self.runtime, key)

    def guard(self):
        self.runtime.guard()
        environment.check_binding(self.binding)

    def bracket(self, item, anchor):
        self.guard()
        _need(_same(_anchor(item), anchor), "tuple")
        return dict(worker=copy.deepcopy(self.worker), server=copy.deepcopy(self.server),
            sources=server_contract.source_bindings(), tools=copy.deepcopy(self.admission["tools"]),
            auth=self.auth.check(), server_alive=True, socket=copy.deepcopy(anchor))


class _TargetRuntime:
    def __init__(self, request, request_binding, root):
        self.request = copy.deepcopy(request)
        self.request_binding = copy.deepcopy(request_binding)
        self.admission = copy.deepcopy(request["validated_admission"])
        self.binding = copy.deepcopy(request["admission"])
        self.root = root
        self.api = self.processes = self.worker = self.server = self.launcher = self.guest = None
        self.child = self.guest_child = None
        self.guest_stop_handle = None
        self.guest_stop_verified = False
        self.capture = self.guest_capture = None
        self.auth = primitives.AuthKeyGuard()
        self.proposal = None
        self.started_epoch = self.until = None
        self.clients_closed = True
        self.guest_ancestry = []
        self._descriptor = self._caller = None
        self._running_binding = None
        self._api = None
        self._deadline = None
        self.stop_requested = False

    @property
    def admission_binding(self):
        return copy.deepcopy(self.binding)

    @property
    def running_binding(self):
        return copy.deepcopy(self._running_binding)

    @property
    def caller(self):
        return copy.deepcopy(self.worker)

    def open_identity(self):
        self.api = self._api = _ProcessApi()
        self.processes = primitives.ProcessHandles(self.api)
        _, self.worker = self.processes.add(os.getpid())
        _need(self.worker["executable"] == self.admission["python"]["executable"]["path"] and
              os.getppid() == self.request["owner"]["pid"], "identity")
        self.processes.add(os.getppid(), self.request["owner"])
        self._caller = copy.deepcopy(self.worker)

    def wait_receipt(self):
        until = time.monotonic() + 5
        path = self.root / "started-v1.json"
        while not os.path.lexists(path):
            self.processes.guard()
            _left(until)
            time.sleep(.02)
        value = _read_json(environment.binding(path))
        _need(_same(value, dict(worker=self.worker, request=self.request_binding)), "receipt")
        self.processes.guard()
        contract.revalidate_inputs(self.admission)
        self.started_epoch = time.time()
        self.until = self._deadline = time.monotonic() + self.admission["seconds"]

    def fast_guard(self):
        _need(self.until - time.monotonic() > 0, "expired")
        self.processes.guard()
        if self.guest_ancestry:
            _check_ancestry(self.api, self.processes, self.guest_ancestry)
        for child, identity in ((self.child, self.server), (self.guest_child, self.launcher)):
            if child is not None:
                _need(child.poll() is None and identity is not None, "identity")
        for capture in (self.capture, self.guest_capture):
            if capture is not None:
                capture.guard()
        stop = self.root / "stop-v1.json"
        if os.path.lexists(stop):
            contract.check_stop(_read_json(environment.binding(stop)), self.binding["sha256"])
            self.stop_requested = True
            raise OwnerRefused("stop_requested")
        _left(self.until)

    def guard(self):
        self.fast_guard()
        contract.revalidate_inputs(self.admission)
        environment.check_binding(self.binding)
        environment.check_binding(self.request_binding)
        self.auth.check()
        if self.proposal is not None:
            environment.check_external_state(self.proposal)
            environment.verify_prepared(self.proposal)
        for root in (self.root, self.root / "server"):
            log = root / "adb.log"
            if os.path.lexists(log):
                environment.safe_path(log)
                _need(log.is_file() and log.stat().st_size <= CAP, "capture")
        _left(self.until)

    def start_server(self):
        self.guard()
        self.capture = primitives.ServerCapture(self.root / "server-output-v1")
        self.child = subprocess.Popen(server_contract.server_command(self.admission["server"]),
            stdin=subprocess.DEVNULL, stdout=subprocess.PIPE, stderr=subprocess.PIPE, bufsize=0,
            env=server_contract.child_environment(self.admission["server"], dict(os.environ)),
            creationflags=subprocess.CREATE_NO_WINDOW)
        self.capture.start(self.child)
        _, self.server = self.processes.add(self.child.pid)
        _need(self.server["executable"] == self.admission["server"]["adb"]["path"] and
              self.server["pid"] not in (self.worker["pid"], self.request["owner"]["pid"]) and
              self.server["creation_filetime"] >= self.worker["creation_filetime"], "identity")
        self.guard()

    def initial_server(self):
        server_root = self.root / "server"
        view = _InitialServerView(self, environment.binding(server_root / "admission-v1.json"))
        records, failure = primitives._ready(view)
        environment.create_json(server_root / "readiness-v1.json", records)
        _need(failure is None, "readiness")
        for kind in ("version", "devices"):
            proof, failure = primitives._exchange(view, kind)
            path = server_root / ("proof-%s-v1.json" % kind)
            environment.create_json(path, proof)
            _need(failure is None, "proof")
            server_contract.validate_proof(environment.binding(path), self.admission["server"],
                view.binding, self.worker, self.server, kind, completed_ports=tuple(view.completed_ports))
            view.completed_ports.append(proof["endpoint"]["local_port"])
        self.clients_closed = view.clients_closed

    def prepare_guest(self):
        self.guard()
        guest = self.admission["guest"]
        self.proposal = environment.authorize(guest["proposal"]["path"], guest["authorization"]["path"], "run")
        _need(self.proposal["paths"]["root"] == guest["root"] and self.proposal["memory_mib"] == 8192 and
              self.proposal["cores"] == 4 and self.proposal["max_seconds"] == 1800 and
              Path(self.proposal["sdk"]) / "emulator/emulator.exe" == Path(guest["emulator"]["path"]), "guest")
        prepared = environment.verify_prepared(self.proposal, initial=True)
        config_path = Path(self.proposal["paths"]["content"]) / "config.ini"
        _need(config_path.stat().st_size <= CAP, "guest")
        configuration = environment.ini(config_path.read_bytes())
        actual = configuration.get("test.quitAfterBootTimeOut")
        _need(actual in (None, "-1", "0"), "timer")
        facts = environment.resource_facts(self.proposal)
        value = dict(version=1, protocol=contract.PROTOCOL, admission=self.admission_binding,
            proposal=copy.deepcopy(guest["proposal"]), authorization=copy.deepcopy(guest["authorization"]),
            prepared=copy.deepcopy(self.proposal["prepared"]), prepare_result=copy.deepcopy(self.proposal["prepare_result"]),
            token=copy.deepcopy(self.proposal["token"]), original_avd=copy.deepcopy(self.proposal["old_avd"]),
            configuration=copy.deepcopy(prepared["immutable"]), tools=copy.deepcopy(self.proposal["bindings"]),
            facts=facts, timer=dict(key="test.quitAfterBootTimeOut", actual=actual,
                effective=-1 if actual is None else int(actual), default_used=actual is None, enabled=False))
        path = self.root / "guest-inputs-v1.json"
        environment.create_json(path, value)
        verification.verify_guest_inputs(environment.binding(path), self.admission, self.binding)
        self.guard()
        return environment.binding(path)

    def start_guest(self):
        self.guard()
        _need(self.proposal is not None, "guest")
        environment.verify_prepared(self.proposal, initial=True)
        claim_path = Path(self.admission["guest"]["root"]) / "owned-target-boot-claim-v1.json"
        environment.create_json(claim_path, dict(version=1, protocol=contract.PROTOCOL,
            admission=self.admission_binding, worker=copy.deepcopy(self.worker),
            proposal=copy.deepcopy(self.admission["guest"]["proposal"])))
        scoped = environment.scoped_env(self.proposal)
        child_env = server_contract.child_environment(self.admission["server"], scoped)
        # Restore only the fixed physical-D Android locations, after removing
        # inherited routing aliases. Emulator direct notification uses this port.
        for key in ("ANDROID_AVD_HOME", "ANDROID_USER_HOME", "ANDROID_EMULATOR_HOME", "ANDROID_SDK_ROOT", "ANDROID_HOME"):
            if key in scoped:
                child_env[key] = scoped[key]
        child_env["ANDROID_ADB_SERVER_PORT"] = str(contract.PORT)
        command = environment.emulator_command(self.proposal) + ["-adb-path", self.admission["guest"]["refuser"]["path"]]
        _need("-no-direct-adb" not in command and not any("quit-after-boot" in arg for arg in command), "guest")
        self.guest_capture = primitives.ServerCapture(self.root / "guest-output-v1")
        self.guest_child = subprocess.Popen(command, stdin=subprocess.DEVNULL, stdout=subprocess.PIPE,
            stderr=subprocess.PIPE, bufsize=0, env=child_env, creationflags=subprocess.CREATE_NO_WINDOW)
        self.guest_capture.start(self.guest_child)
        _, self.launcher = self.processes.add(self.guest_child.pid)
        _need(self.launcher["executable"] == self.admission["guest"]["emulator"]["path"] and
              self.launcher["creation_filetime"] >= self.worker["creation_filetime"], "identity")
        self.guard()

    def discover_guest(self):
        self.guard()
        candidates = []
        for pid in self.api.current_job_pids():
            if any(value is not None and value["pid"] == pid for value in self.processes.handles.values()):
                continue
            handle, identity = self.processes.add(pid)
            if identity["executable"] == self.admission["guest"]["qemu"]["path"]:
                candidates.append(identity)
            else:
                _need(self.processes.release(handle), "cleanup")
        _need(len(candidates) <= 1, "guest")
        if not candidates:
            return False
        self.guest = copy.deepcopy(candidates[0])
        chain = [copy.deepcopy(self.guest)]
        while chain[-1]["pid"] != self.launcher["pid"]:
            _need(len(chain) < 8, "ancestry")
            parent_pid = self.api.parent_pid(_held_handle(self.processes, chain[-1]["pid"]))
            found = [value for value in self.processes.handles.values()
                     if value is not None and value["pid"] == parent_pid]
            if found:
                identity = copy.deepcopy(found[0])
            else:
                _, identity = self.processes.add(parent_pid)
            _need(identity["executable"] in (self.admission["guest"]["emulator"]["path"],
                    self.admission["guest"]["qemu"]["path"]) and
                  identity["pid"] not in {value["pid"] for value in chain}, "ancestry")
            chain.append(identity)
        self.guest_ancestry = list(reversed(chain))
        _check_ancestry(self.api, self.processes, self.guest_ancestry)
        self.guest_stop_handle = self.api.open_guest(self.guest["pid"])
        _need(self.guest_stop_handle not in self.processes.handles, "identity")
        self.processes.close_attempted.discard(self.guest_stop_handle)
        self.processes.handles[self.guest_stop_handle] = None
        _need(_same(self.api.identity(self.guest_stop_handle), self.guest) and
              self.api.alive(self.guest_stop_handle), "identity")
        self.processes.handles[self.guest_stop_handle] = copy.deepcopy(self.guest)
        self.guest_stop_verified = True
        self._descriptor = {key: copy.deepcopy(value) for key, value in (
            ("owner", self.request["owner"]), ("worker", self.worker), ("server", self.server),
            ("launcher", self.launcher), ("guest", self.guest))}
        self._descriptor["transport_id"] = None
        self._descriptor["sources"] = copy.deepcopy(self.admission["sources"])
        self._descriptor["python"] = copy.deepcopy(self.admission["python"])
        return True

    def admit_guest(self):
        records = []
        readiness_path = self.root / "readiness-v1.json"
        begin = time.monotonic()
        try:
            until = min(self.until, begin + 30)
            for _ in range(120):
                self.guard()
                found = self.discover_guest()
                records.append(dict(elapsed_ms=math.ceil((time.monotonic() - begin) * 1000),
                    stage="guest_process", observation=None, tables=None, queries=None))
                _left(until)
                if found:
                    break
                time.sleep(min(.25, _left(until)))
            else:
                raise OwnerRefused("readiness")
            until = min(self.until, time.monotonic() + 30)
            for _ in range(120):
                self.guard()
                observation, tables = _observe(self.api, guest=True)
                contract.validate_guest_prefix(observation, self.guest, self.server)
                server_contract._tables(tables, observation)
                records.append(dict(elapsed_ms=math.ceil((time.monotonic() - begin) * 1000),
                    stage="guest_ports", observation=observation, tables=tables, queries=None))
                _left(until)
                listeners = {(row["local_port"], row["family"]) for row in observation["rows"]
                    if row["remote_port"] == 0}
                if {(5592, 2), (5593, 2)} <= listeners:
                    contract.validate_guest_observation(observation, self.guest, self.server)
                    break
                time.sleep(min(.25, _left(until)))
            else:
                raise OwnerRefused("readiness")
            until = min(self.until, begin + 180, time.monotonic() + 120)
            self._query_deadline = until
            for index in range(1, 61):
                self.guard()
                _left(until)
                observation, tables = _observe(self.api, guest=True)
                contract.validate_guest_observation(observation, self.guest, self.server)
                queries = []
                failure = None
                for kind in ("version", "devices"):
                    query, failure = self._query(kind)
                    queries.append(query)
                    if not query["socket_closed"]:
                        self.clients_closed = False
                    if failure is not None:
                        break
                transport_id = None
                if failure is None:
                    transport_id = _waiting_devices(bytes.fromhex(queries[1]["response_hex"])[8:])
                path = self.root / ("target-registration-v1.json" if transport_id is not None else
                                    "registration-%04d-v1.json" % index)
                bundle = dict(version=1, protocol=contract.PROOF_PROTOCOL, admission=self.admission_binding,
                    running=None, caller=self.caller, queries=queries)
                environment.create_json(path, bundle)
                records.append(dict(elapsed_ms=math.ceil((time.monotonic() - begin) * 1000),
                    stage="registration", observation=observation, tables=tables, queries=environment.binding(path)))
                _need(failure is None, "registration")
                contract.validate_query_bundle(bundle, self._descriptor, self._caller, self.binding, None,
                    require_device=False)
                _left(until)
                if transport_id is not None:
                    self._descriptor["transport_id"] = transport_id
                    roster = self.api.current_job_pids()
                    identities = {key: copy.deepcopy(value) for key, value in (
                        ("worker", self.worker), ("server", self.server), ("launcher", self.launcher), ("guest", self.guest))}
                    _need(all(value["pid"] in roster for value in identities.values()), "job")
                    environment.create_json(readiness_path, records)
                    job_path = self.root / "guest-job-v1.json"
                    environment.create_json(job_path, dict(version=1, protocol=contract.PROTOCOL,
                        worker=copy.deepcopy(self.worker), processes=roster, identities=identities, checked=True,
                        source="QueryInformationJobObject(NULL,JobObjectBasicProcessIdList)"))
                    ready = dict(version=1, protocol=contract.PROTOCOL, admission=self.admission_binding,
                        identities={key: copy.deepcopy(self._descriptor[key]) for key in
                            ("owner", "worker", "server", "launcher", "guest")},
                        guest_ancestry=copy.deepcopy(self.guest_ancestry), guest_job=environment.binding(job_path),
                        guest_observation=observation, guest_tables=tables, queries=environment.binding(path),
                        sources=contract.source_bindings(), python=file_guard._python_bindings())
                    ready_path = self.root / "target-ready-v1.json"
                    self.guard()
                    environment.create_json(ready_path, ready)
                    descriptor = dict(version=1, protocol=contract.PROTOCOL, admission=self.admission_binding,
                        run_id=self.admission["run_id"], root=self.admission["root"],
                        **{key: copy.deepcopy(self._descriptor[key]) for key in ("owner", "worker", "server", "launcher", "guest")},
                        guest_ancestry=copy.deepcopy(self.guest_ancestry), started_epoch=self.started_epoch,
                        deadline_epoch=self.started_epoch + self.admission["seconds"], sdk_port=contract.PORT,
                        console_port=5592, adb_port=5593, serial="emulator-5592", transport_id=transport_id,
                        sources=contract.source_bindings(), python=file_guard._python_bindings(), ready=environment.binding(ready_path))
                    contract.validate_running(descriptor, self.admission, self.binding)
                    contract.validate_ready(ready, descriptor, self.admission)
                    contract.validate_guest_job(_read_json(environment.binding(job_path)), descriptor)
                    contract.validate_query_bundle(bundle, descriptor, self.worker, self.binding, None)
                    environment.create_json(self.root / "running-v1.json", descriptor)
                    self._descriptor = descriptor
                    self._running_binding = environment.binding(self.root / "running-v1.json")
                    return environment.binding(ready_path), environment.binding(job_path)
                time.sleep(min(2, _left(until)))
            raise OwnerRefused("registration")
        finally:
            # A failed prefix remains an actual failed prefix, never rewritten
            # into a valid final registration after another observation.
            if not os.path.lexists(readiness_path):
                environment.create_json(readiness_path, records)

    _query = LiveOwnedTarget._query
    _bracket = LiveOwnedTarget._bracket


def _guest_preflight(api):
    observation, tables = _observe(api, guest=True)
    contract._rows(observation, "ports", [5592, 5593])
    server_contract._tables(tables, observation)
    _need(not observation["rows"], "port")
    created = attempted = closed = 0
    sockets = []
    bound = False
    try:
        for ordinal, (family, address, port) in enumerate(
                ((socket.AF_INET, "127.0.0.1", 5592), (socket.AF_INET, "127.0.0.1", 5593),
                 (socket.AF_INET6, "::1", 5592), (socket.AF_INET6, "::1", 5593))):
            item = socket.socket(family, socket.SOCK_STREAM)
            bit = 1 << ordinal
            sockets.append((item, bit))
            created |= bit
            item.setsockopt(socket.SOL_SOCKET, socket.SO_EXCLUSIVEADDRUSE, 1)
            if family == socket.AF_INET6:
                item.setsockopt(socket.IPPROTO_IPV6, socket.IPV6_V6ONLY, 1)
            item.bind((address, port))
        bound = True
    except (OSError, ValueError):
        pass
    finally:
        for item, bit in sockets:
            attempted |= bit
            try:
                item.close()
                if item.fileno() == -1:
                    closed |= bit
            except (OSError, ValueError):
                pass
    return dict(observation=observation, tables=tables, created_mask=created,
        close_attempted_mask=attempted, closed_mask=closed, exclusive_bind_succeeded=bound)


def _close_popen(child, capture, *, allow_terminate):
    result = dict(terminate_attempted=False, wait_completed=False, process_handle_closed=False,
                  pipes_closed=False, output_capture_complete=False)
    code = None
    if child is not None and allow_terminate:
        try:
            if child.poll() is None:
                result["terminate_attempted"] = True
                child.terminate()
        except (OSError, ValueError):
            pass
        try:
            code = child.wait(timeout=5)
            result["wait_completed"] = type(code) is int
        except (OSError, ValueError, subprocess.TimeoutExpired):
            pass
    if capture is not None:
        try:
            result["output_capture_complete"] = capture.close() is True
        except (OSError, ValueError, RuntimeError):
            pass
        result["pipes_closed"] = capture.pipes_closed is True
    if child is not None and result["wait_completed"]:
        try:
            child._handle.Close()
            result["process_handle_closed"] = child._handle.closed is True
        except (OSError, ValueError, AttributeError):
            pass
    return result, code


def _capture_binding(runtime, kind, result, code):
    child = runtime.child if kind == "server" else runtime.guest_child
    identity = runtime.server if kind == "server" else runtime.launcher
    capture = runtime.capture if kind == "server" else runtime.guest_capture
    if capture is None or not result["output_capture_complete"] or not result["pipes_closed"]:
        return None
    if child is not None and (not result["wait_completed"] or identity is None):
        return None
    sizes = capture.capture.sizes
    _need(type(sizes) is list and len(sizes) == 2 and all(type(n) is int and n >= 0 for n in sizes), "capture")
    root = runtime.root / (kind + "-output-v1")
    value = dict(version=1, protocol=contract.PROTOCOL, server=copy.deepcopy(identity),
        status="not_started" if child is None else "terminated" if result["terminate_attempted"] else "exited",
        returncode=code, stdout=environment.binding(root / "owner-stdout-v1.bin"),
        stderr=environment.binding(root / "owner-stderr-v1.bin"), stdout_bytes=sizes[0], stderr_bytes=sizes[1],
        capture_complete=True, pipes_closed=True)
    _need(sizes[0] + sizes[1] <= CAP, "capture")
    path = runtime.root / (kind + "-capture-v1.json")
    environment.create_json(path, value)
    return environment.binding(path)


def _cleanup(runtime, preflight, guest_preflight):
    cleanup = {key: False for key in contract.CLEANUP_KEYS}
    cleanup["preflight_sockets_closed"] = (preflight is not None and
        preflight["created_mask"] == preflight["close_attempted_mask"] == preflight["closed_mask"] == 1)
    cleanup["guest_preflight_sockets_closed"] = (guest_preflight is not None and
        guest_preflight["created_mask"] == guest_preflight["close_attempted_mask"] == guest_preflight["closed_mask"] == 15)
    cleanup["client_sockets_closed"] = runtime.clients_closed
    terminal_binding = None
    vm_wait = vm_closed = False
    vm_terminate = False
    vm_code = None
    if runtime.guest_stop_verified:
        try:
            if runtime.api.alive(runtime.guest_stop_handle):
                vm_terminate = True
                runtime.api.terminate_guest(runtime.guest_stop_handle)
        except (OSError, ValueError):
            pass
        try:
            vm_code = runtime.api.wait_guest(runtime.guest_stop_handle)
            vm_wait = type(vm_code) is int
        except (OSError, ValueError):
            pass
        vm_closed = runtime.processes.release(runtime.guest_stop_handle)
        terminal = dict(version=1, protocol=contract.PROTOCOL, guest=copy.deepcopy(runtime.guest),
            terminate_attempted=vm_terminate, wait_completed=vm_wait, returncode=vm_code, handle_closed=vm_closed)
        path = runtime.root / "guest-terminal-v1.json"
        try:
            environment.create_json(path, terminal)
            terminal_binding = environment.binding(path)
        except (OSError, ValueError):
            pass
    guest_result, guest_code = _close_popen(runtime.guest_child, runtime.guest_capture, allow_terminate=True)
    for key, value in guest_result.items():
        cleanup["guest_" + key] = value
    cleanup["guest_terminate_attempted"] = vm_terminate or guest_result["terminate_attempted"]
    cleanup["guest_wait_completed"] = vm_wait and guest_result["wait_completed"]
    cleanup["guest_process_handle_closed"] = vm_closed and guest_result["process_handle_closed"]
    # Stop the actual guest VM and launcher before stopping the server. If VM
    # identity/closure is unknown, leave service cleanup to the known outer job;
    # never claim an ordered closure that was not observed.
    server_allowed = runtime.guest_child is None or (vm_wait and guest_result["wait_completed"])
    server_result, server_code = _close_popen(runtime.child, runtime.capture, allow_terminate=server_allowed)
    for key, value in server_result.items():
        cleanup["server_" + key] = value
    server_capture = guest_capture = None
    try:
        server_capture = _capture_binding(runtime, "server", server_result, server_code)
    except (OSError, ValueError, KeyError):
        cleanup["server_output_capture_complete"] = False
    try:
        guest_capture = _capture_binding(runtime, "guest", guest_result, guest_code)
    except (OSError, ValueError, KeyError):
        cleanup["guest_output_capture_complete"] = False
    try:
        cleanup["auth_handle_closed"] = runtime.auth.close() is True
    except (OSError, ValueError):
        pass
    if runtime.processes is not None:
        cleanup["process_handles_closed"] = runtime.processes.close() is True
    return cleanup, server_code, guest_code, server_capture, guest_capture, terminal_binding


def _reason(error, default="owner"):
    value = getattr(error, "reason", str(error))
    allowed = {"owner", "platform", "admission", "source", "python", "identity", "receipt", "auth", "port",
        "startup", "readiness", "proof", "framing", "deadline", "stop", "capture", "cleanup", "output",
        "stop_requested", "expired", "guest", "timer", "ancestry", "registration", "job", "target", "binding"}
    return value if value in allowed else default


def _validate_request(value, binding):
    keys = {"version", "protocol", "admission", "validated_admission", "owner", "sources", "python",
            "worker_script", "owner_seconds"}
    _need(type(value) is dict and set(value) == keys, "receipt")
    contract._int(value["version"], 1, 1)
    _need(value["protocol"] == contract.PROTOCOL, "receipt")
    admitted = contract.validate_admission(copy.deepcopy(value["validated_admission"]))
    _need(_same(_read_json(value["admission"]), admitted), "admission")
    _need(Path(binding["path"]) == Path(admitted["root"]) / "request-v1.json" and
          _same(value["sources"], admitted["sources"]) and _same(value["python"], admitted["python"]) and
          type(value["owner_seconds"]) is int and value["owner_seconds"] == admitted["seconds"] + 30,
          "receipt")
    contract._process(value["owner"])
    _need(value["owner"]["executable"] == admitted["python"]["executable"]["path"] and
          _same(value["worker_script"], environment.binding(Path(__file__).resolve())), "source")
    contract.revalidate_inputs(admitted)
    return copy.deepcopy(value)


def _run_worker(request, request_binding, root):
    begin = time.monotonic()
    runtime = _TargetRuntime(request, request_binding, root)
    preflight = guest_preflight = None
    preflight_binding = guest_preflight_binding = inputs_binding = ready_binding = job_binding = None
    sources_after = None
    reason = "owner"
    try:
        runtime.open_identity()
        runtime.wait_receipt()
        runtime.auth.open(runtime.admission["server"]["auth_key"])
        runtime.guard()
        server_root = root / "server"
        server_root.mkdir(exist_ok=False)
        environment.create_json(server_root / "admission-v1.json", runtime.admission["server"])
        preflight = primitives._exclusive_preflight(runtime.api)
        environment.create_json(server_root / "preflight-v1.json", preflight)
        preflight_binding = environment.binding(server_root / "preflight-v1.json")
        _need(preflight["created_mask"] == preflight["close_attempted_mask"] == preflight["closed_mask"] == 1 and
              preflight["exclusive_bind_succeeded"] is True, "port")
        runtime.start_server()
        runtime.initial_server()
        inputs_binding = runtime.prepare_guest()
        guest_preflight = _guest_preflight(runtime.api)
        environment.create_json(root / "guest-preflight-v1.json", guest_preflight)
        guest_preflight_binding = environment.binding(root / "guest-preflight-v1.json")
        _need(guest_preflight["created_mask"] == guest_preflight["close_attempted_mask"] ==
              guest_preflight["closed_mask"] == 15 and guest_preflight["exclusive_bind_succeeded"] is True, "port")
        runtime.start_guest()
        ready_binding, job_binding = runtime.admit_guest()
        while True:
            runtime.guard()
            time.sleep(min(.1, _left(runtime.until)))
    except BaseException as error:
        reason = _reason(error)
    finally:
        try:
            contract.revalidate_inputs(runtime.admission)
            environment.check_binding(runtime.binding)
            environment.check_binding(request_binding)
            _need(runtime.auth.key is not None and runtime.auth.descriptor is not None, "auth")
            sources_after = dict(sources=contract.source_bindings(), python=file_guard._python_bindings(),
                tools=copy.deepcopy(runtime.admission["server"]["tools"]), auth=runtime.auth.check())
        except BaseException as error:
            if reason in ("stop_requested", "expired"):
                reason = _reason(error, "source")
        cleanup, server_code, guest_code, server_capture, guest_capture, terminal = _cleanup(runtime, preflight, guest_preflight)
        if reason in ("stop_requested", "expired") and (
                not all(cleanup.values()) or terminal is None or server_capture is None or guest_capture is None):
            reason = "cleanup"
        if runtime.auth.failed_close or runtime.processes is not None and runtime.processes.failed_close:
            reason = "cleanup"
        readiness = root / "readiness-v1.json"
        boot_claim = Path(runtime.admission["guest"]["root"]) / "owned-target-boot-claim-v1.json"
        value = dict(version=1, protocol=contract.PROTOCOL, admission=copy.deepcopy(runtime.binding),
            request=copy.deepcopy(request_binding), worker=copy.deepcopy(runtime.worker),
            server=copy.deepcopy(runtime.server), launcher=copy.deepcopy(runtime.launcher), guest=copy.deepcopy(runtime.guest),
            guest_ancestry=copy.deepcopy(runtime.guest_ancestry), auth=copy.deepcopy(runtime.auth.descriptor),
            preflight=preflight_binding, guest_preflight=guest_preflight_binding,
            readiness=environment.binding(readiness) if os.path.lexists(readiness) else None,
            ready=ready_binding, running=runtime.running_binding, server_capture=server_capture,
            guest_capture=guest_capture, server_returncode=server_code, guest_returncode=guest_code,
            reason=reason, cleanup=cleanup, sources_after=sources_after,
            stop_requested=runtime.stop_requested, elapsed_ms=math.ceil(max(0, time.monotonic() - begin) * 1000),
            guest_job=job_binding, guest_inputs=inputs_binding, guest_terminal=terminal,
            boot_claim=environment.binding(boot_claim) if os.path.lexists(boot_claim) else None)
        _need(set(value) == contract.WORKER_KEYS, "output")
        environment.create_json(root / "worker-result-v1.json", value)
    return 0 if reason in ("stop_requested", "expired") and runtime.running_binding is not None else 1


def _worker():
    try:
        raw = sys.stdin.buffer.read(131073)
        _need(type(raw) is bytes and raw.startswith(BARRIER) and len(raw) <= 131072, "receipt")
        value = environment.decode_json(raw[len(BARRIER):])
        _need(type(value) is dict and set(value) == {"request"}, "receipt")
        binding = value["request"]
        request = _validate_request(_read_json(binding), binding)
        return _run_worker(request, binding, Path(request["validated_admission"]["root"]))
    except BaseException as error:
        print(json.dumps(dict(qualified_target=False, reason=_reason(error), feature_acceptance=False)), flush=True)
        return 1


def _inputs(admission, binding):
    contract.revalidate_inputs(copy.deepcopy(admission))
    _need(_same(_read_json(binding), admission), "admission")


def _parent(admission_binding, admission):
    out = output_control.validate_output(admission["root"])
    _inputs(admission, admission_binding)
    output_control._prepare_environment()
    api, handles = _ProcessApi(), None
    qualified, reason = False, "owner"
    request_binding = started_binding = worker_binding = owner_binding = after_binding = None
    expected_worker = None
    handles_closed = False
    try:
        handles = primitives.ProcessHandles(api)
        owner_handle, owner_identity = handles.add(os.getpid())
        _need(owner_identity["executable"] == admission["python"]["executable"]["path"], "identity")
        out.mkdir(exist_ok=False)
        request = dict(version=1, protocol=contract.PROTOCOL, admission=copy.deepcopy(admission_binding),
            validated_admission=copy.deepcopy(admission), owner=copy.deepcopy(owner_identity),
            sources=copy.deepcopy(admission["sources"]), python=copy.deepcopy(admission["python"]),
            worker_script=environment.binding(Path(__file__).resolve()), owner_seconds=admission["seconds"] + 30)
        _need(set(request) == contract.REQUEST_KEYS, "output")
        environment.create_json(out / "request-v1.json", request)
        request_binding = environment.binding(out / "request-v1.json")
        # The legacy supervisor owns a different stop schema. Its bounded raw
        # capture and stop namespace must never consume this target's stop file.
        worker_output = out / "worker-output-v1"
        worker_output.mkdir(exist_ok=False)

        def started(child):
            nonlocal started_binding, expected_worker
            handles.guard()
            _, expected_worker = handles.add(child.pid)
            _need(expected_worker["executable"] == admission["python"]["executable"]["path"], "identity")
            _inputs(admission, admission_binding)
            environment.check_binding(request_binding)
            pending = out / "started.pending-v1.json"
            environment.create_json(pending, dict(worker=copy.deepcopy(expected_worker), request=copy.deepcopy(request_binding)))
            # Windows create-only rename publishes complete fsynced bytes;
            # malformed existing receipts are never retried or replaced.
            pending.rename(out / "started-v1.json")
            started_binding = environment.binding(out / "started-v1.json")
            return True

        owner = environment.supervise([sys.executable, "-I", "-S", "-B", str(Path(__file__).resolve()), "_worker"],
            BARRIER + environment.encoded(dict(request=request_binding)), worker_output, admission["seconds"] + 30, started)
        environment.create_json(out / "owner-result-v1.json", owner)
        owner_binding = environment.binding(out / "owner-result-v1.json")
        _need(primitives._owner_ok(owner, worker_output) and started_binding is not None, "owner")
        _need(_same(_read_json(started_binding), dict(worker=expected_worker, request=request_binding)), "receipt")
        _inputs(admission, admission_binding)
        worker_binding = environment.binding(out / "worker-result-v1.json")
        record = verification.verify_owned_target_result(worker_binding, admission, admission_binding,
            request_binding, expected_worker)
        _inputs(admission, admission_binding)
        current_owner = api.identity(owner_handle)
        _need(api.alive(owner_handle) and _same(current_owner, owner_identity), "identity")
        handles_closed = handles.close() is True
        _need(handles_closed, "cleanup")
        after = dict(admission=copy.deepcopy(admission_binding), sources=contract.source_bindings(),
            python=file_guard._python_bindings(), tools=copy.deepcopy(admission["server"]["tools"]),
            owner=current_owner, process_handles_closed=handles_closed)
        _need(_same(after, dict(admission=admission_binding, sources=admission["sources"], python=admission["python"],
            tools=admission["server"]["tools"], owner=owner_identity, process_handles_closed=True)), "source")
        environment.create_json(out / "after-v1.json", after)
        after_binding = environment.binding(out / "after-v1.json")
        for pin in (admission_binding, request_binding, started_binding, worker_binding, owner_binding, after_binding):
            environment.check_binding(pin)
        _inputs(admission, admission_binding)
        qualified, reason = True, record["reason"]
    except BaseException as error:
        reason = _reason(error)
        if worker_binding is None and out.is_dir() and os.path.lexists(out / "worker-result-v1.json"):
            try:
                worker_binding = environment.binding(out / "worker-result-v1.json")
            except (OSError, ValueError):
                pass
    finally:
        if handles is not None and not handles_closed:
            handles_closed = handles.close() is True
            if not handles_closed:
                qualified, reason = False, "cleanup"
    _need(out.is_dir(), "output")
    result = dict(version=1, protocol=contract.PROTOCOL, admission=copy.deepcopy(admission_binding),
        request=request_binding, started=started_binding, worker_result=worker_binding, owner=owner_binding,
        after=after_binding, qualified_target=qualified, reason=reason, feature_acceptance=False)
    environment.create_json(out / "result-v1.json", result)
    print(json.dumps(dict(qualified_target=qualified, reason=reason, feature_acceptance=False)), flush=True)
    return 0 if qualified else 1


def main(argv=None):
    args = sys.argv[1:] if argv is None else argv
    try:
        _need(os.name == "nt", "platform")
        if args == ["_worker"]:
            output_control._prepare_environment()
            return _worker()
        _need(type(args) is list and len(args) == 4 and args[0] == "--admission" and args[2] == "--admission-sha256" and
              type(args[1]) is str and type(args[3]) is str and re.fullmatch("[0-9a-f]{64}", args[3]) is not None, "admission")
        path = file_guard._existing_D_file(args[1], "admission")
        _need(path.suffix == ".json", "admission")
        binding, value = file_guard._read_bound(path, args[3], 2 * 1024 * 1024, "admission")
        admitted = contract.validate_admission(value)
        return _parent(binding, admitted)
    except BaseException as error:
        print(json.dumps(dict(qualified_target=False, reason=_reason(error), feature_acceptance=False)), flush=True)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
