"""Explicit owned-target smart-socket and binary shell-v2 client.

No ordinary ADB executable, legacy SDK capture or subprocess runner is used.
Importing this module performs no process, socket or device observation.
Copyright 2026 LocalLore contributors. SPDX-License-Identifier: Apache-2.0
"""
from __future__ import annotations

import copy
import hashlib
import math
import os
from pathlib import Path
import re
import shlex
import socket
import struct
import threading
import time

from benchmarks import owned_target_contract as contract
from benchmarks import android_process_verification_v4 as verification
from benchmarks import adb_held_socket_probe as file_guard
from benchmarks import receipt_avd_environment as environment
from benchmarks import windows_tcp_control as output_control

MAX_CAPTURE = 8 * 1024 * 1024
MAX_PACKET = 1024 * 1024
SDK_PROTOCOL = "sdk-owned-target-v1"


class ClientRefused(ValueError):
    """A sticky refusal, never an invitation to retry a target command."""


def _need(value, reason="client_guard"):
    if not value:
        raise ClientRefused(reason)


def _packet(channel, payload):
    _need(type(channel) is int and channel in (0, 4) and type(payload) is bytes)
    _need(len(payload) <= 65536 and (channel != 4 or not payload))
    return bytes((channel,)) + struct.pack("<I", len(payload)) + payload


def _smart_frame(service):
    _need(type(service) is bytes and 0 < len(service) <= 65535)
    return ("%04x" % len(service)).encode("ascii") + service


def _label(value):
    _need(type(value) is str and re.fullmatch(r"[a-z][a-z0-9_-]{0,47}", value) is not None)


def _number(value, high=1700):
    _need(type(value) in (int, float) and math.isfinite(value) and 0 < value <= high)


def _identity(path):
    value = environment.safe_path(path, directory=True).lstat()
    _need(not path.is_symlink() and not (getattr(value, "st_file_attributes", 0) & 0x400))
    return value.st_dev, value.st_ino


def _file_stamp(value):
    birth = getattr(value, "st_birthtime_ns", None)
    _need(type(birth) is int and birth >= 0, "input_identity")
    return (value.st_dev, value.st_ino, value.st_size, value.st_mtime_ns,
            value.st_ctime_ns, birth)


def _lease_class():
    # A fixed implementation, not a constructor argument, plugin or fallback.
    from benchmarks.owned_target_owner import LiveOwnedTarget
    return LiveOwnedTarget


class OwnedTargetSdkCapture:
    """A finite direct transport session bound to one immutable live target."""

    def __init__(self, directory, seconds, lease):
        self.clean = False
        self.count = 0
        self._failed = True
        self._last_time = None
        self._time_lock = threading.Lock()
        self.lease = lease
        try:
            _need(type(lease) is _lease_class(), "lease_type")
            _number(seconds)
            lease.guard(min_seconds=seconds)
            self._admission = copy.deepcopy(lease.admission)
            self._descriptor = copy.deepcopy(lease.descriptor)
            self._admission_binding = copy.deepcopy(lease.admission_binding)
            self._running_binding = copy.deepcopy(lease.running_binding)
            contract.validate_admission(copy.deepcopy(self._admission))
            contract.validate_running(copy.deepcopy(self._descriptor), copy.deepcopy(self._admission),
                                      copy.deepcopy(self._admission_binding))
            self._target = {"transport_id": self._descriptor["transport_id"]}
            self.directory = output_control.validate_output(str(directory))
            _need(self.directory.name == "clients")
            self._proofs = output_control.validate_output(str(self.directory.parent / "proofs"))
            session_path = output_control.validate_output(str(self.directory.parent / "sdk-session-v4.json"))
            started_epoch = time.time()
            self.until = self._now() + seconds
            self._deadline_limit = self.until
            self._session = dict(version=1, protocol=SDK_PROTOCOL,
                admission=copy.deepcopy(self._admission_binding), running=copy.deepcopy(self._running_binding),
                descriptor=copy.deepcopy(self._descriptor), caller=copy.deepcopy(lease.caller),
                sources=copy.deepcopy(self._admission["sources"]), python=copy.deepcopy(self._admission["python"]),
                root=str(self.directory.parent), seconds=seconds, started_epoch=started_epoch,
                deadline_epoch=started_epoch + seconds)
            contract.validate_session(copy.deepcopy(self._session), copy.deepcopy(self._admission))
            self.directory.mkdir(exist_ok=False)
            self._proofs.mkdir(exist_ok=False)
            self._directory_id = _identity(self.directory)
            self._proofs_id = _identity(self._proofs)
            self._parent_id = _identity(self.directory.parent)
            environment.create_json(session_path, self._session)
            self._session_binding = environment.binding(session_path)
            self.clean, self._failed = True, False
            self._guard()
        except BaseException:
            self._poison()
            raise ClientRefused("client_guard") from None

    @property
    def target(self):
        return copy.deepcopy(self._target)

    @target.setter
    def target(self, value):
        self._poison()
        raise ClientRefused("target_immutable")

    @property
    def session(self):
        return copy.deepcopy(self._session)

    @property
    def session_binding(self):
        return copy.deepcopy(self._session_binding)

    def _poison(self):
        self.clean, self._failed = False, True

    def _now(self):
        with self._time_lock:
            value = time.monotonic()
            _need(type(value) in (int, float) and math.isfinite(value) and
                  (self._last_time is None or value >= self._last_time), "client_deadline")
            self._last_time = value
            return value

    def _directory_guard(self):
        _need(_identity(self.directory) == self._directory_id and
              _identity(self._proofs) == self._proofs_id and
              _identity(self.directory.parent) == self._parent_id, "persistence_failed")

    def _fast_guard(self, deadline):
        _need(self.clean is True and self._failed is False, "client_closed")
        _need(type(self.until) in (int, float) and math.isfinite(self.until) and
              self.until <= self._deadline_limit and self._now() < min(deadline, self.until),
              "client_deadline")
        self.lease.fast_guard()

    def _guard(self):
        self._fast_guard(self.until)
        self._directory_guard()
        environment.check_binding(self._session_binding)
        _need(self.lease.admission == self._admission and
              self.lease.descriptor == self._descriptor and self.lease.caller == self._session["caller"] and
              self.lease.admission_binding == self._admission_binding and
              self.lease.running_binding == self._running_binding, "target_changed")
        self.lease.guard()

    def _timeout(self, sock, deadline):
        self._fast_guard(deadline)
        sock.settimeout(min(0.25, min(deadline, self.until) - self._now()))

    def _send(self, sock, raw, deadline, input_state=None, input_digest=None):
        remaining = memoryview(raw)
        offset = 0
        while remaining:
            self._timeout(sock, deadline)
            try:
                count = sock.send(remaining)
            except socket.timeout:
                continue
            _need(type(count) is int and 0 < count <= len(remaining), "framing")
            if input_state is not None:
                start, end = max(5, offset), offset + count
                if end > start:
                    payload = raw[start:end]
                    input_digest.update(payload)
                    input_state["stdin_bytes"] += len(payload)
            offset += count
            remaining = remaining[count:]

    def _recv(self, sock, size, deadline):
        raw = bytearray()
        while len(raw) < size:
            self._timeout(sock, deadline)
            try:
                part = sock.recv(size - len(raw))
            except socket.timeout:
                continue
            _need(type(part) is bytes and 0 < len(part) <= size - len(raw), "framing")
            raw.extend(part)
        return bytes(raw)

    def _status(self, sock, deadline):
        status = self._recv(sock, 4, deadline)
        if status == b"FAIL":
            size_raw = self._recv(sock, 4, deadline)
            _need(re.fullmatch(b"[0-9a-fA-F]{4}", size_raw) is not None, "framing")
            size = int(size_raw, 16)
            _need(size <= 4096, "framing")
            if size:
                self._recv(sock, size, deadline)
            raise ClientRefused("service_refused")
        _need(status == b"OKAY", "framing")

    def _send_shell(self, sock, source, state, deadline):
        digest = hashlib.sha256()
        state["stdin_bytes"] = 0
        try:
            if source is not None:
                left = state["input_limit"]
                while True:
                    self._fast_guard(deadline)
                    raw = source.read(min(65536, left) if left else 1)
                    _need(type(raw) is bytes, "input")
                    if left == 0:
                        _need(raw == b"", "input_identity")
                        break
                    _need(0 < len(raw) <= min(65536, left), "input_identity")
                    self._send(sock, _packet(0, raw), deadline, state, digest)
                    left -= len(raw)
            self._send(sock, _packet(4, b""), deadline)
            state["stdin_complete"] = True
        except BaseException:
            state["sender_failed"] = True
        finally:
            state["stdin_sha256"] = None if source is None else digest.hexdigest()

    def _read_shell(self, sock, state, deadline, cap):
        while True:
            _need(not state["sender_failed"], "input")
            header = self._recv(sock, 5, deadline)
            channel, size = header[0], struct.unpack("<I", header[1:])[0]
            _need(channel in (1, 2, 3) and size <= MAX_PACKET, "framing")
            if channel == 3:
                _need(size == 1, "framing")
                state["returncode"] = self._recv(sock, 1, deadline)[0]
                while True:
                    self._timeout(sock, deadline)
                    try:
                        trailing = sock.recv(1)
                    except socket.timeout:
                        continue
                    _need(type(trailing) is bytes and trailing == b"", "framing")
                    return
            _need(len(state["stdout"]) + len(state["stderr"]) + size <= cap, "capture_limit")
            output = state["stdout" if channel == 1 else "stderr"]
            while size:
                _need(not state["sender_failed"], "input")
                self._timeout(sock, deadline)
                try:
                    payload = sock.recv(min(size, 65536))
                except socket.timeout:
                    continue
                _need(type(payload) is bytes and 0 < len(payload) <= size, "framing")
                output.extend(payload)
                size -= len(payload)

    def _proof(self, path, context, sock, anchor, after=False):
        self._guard()
        original = copy.deepcopy(context)
        pin = copy.deepcopy(self.lease.prove(path, self.session, copy.deepcopy(context), sock,
                                             copy.deepcopy(anchor), after=after))
        contract.binding(copy.deepcopy(pin))
        environment.check_binding(pin)
        value = verification.verify_proof(copy.deepcopy(pin), self.session, copy.deepcopy(original))
        _need(file_guard._same(value["session"], self.session_binding), "session_changed")
        # The independent owner is responsible for the complete proof graph;
        # do not substitute an arbitrary caller-supplied boolean provider.
        self._guard()
        _need(context == original, "context_changed")
        return pin

    def _write_bytes(self, path, raw):
        self._directory_guard()
        with path.open("xb") as sink:
            rest = memoryview(raw)
            while rest:
                size = sink.write(rest)
                _need(type(size) is int and 0 < size <= len(rest), "persistence_failed")
                rest = rest[size:]
            sink.flush()
            os.fsync(sink.fileno())
        self._directory_guard()
        return environment.binding(path)

    def shell(self, argv, label, seconds=15, cap=131072, *, full_budget=False):
        return self._execute(argv, None, label, seconds, cap, full_budget)

    def check_server(self):
        try:
            self._guard()
        except BaseException:
            self._poison()
            raise ClientRefused("client_guard") from None
        return None

    def stream(self, argv, source_binding, label, seconds=180, cap=131072, *, full_budget=True):
        if type(source_binding) is not dict:
            self._poison()
            raise ClientRefused("input")
        return self._execute(argv, source_binding, label, seconds, cap, full_budget)

    def _execute(self, argv, source_binding, label, seconds, cap, full_budget):
        sock = source = sender = None
        sender_started = False
        dispatched = False
        socket_closed = sender_joined = input_closed = False
        before = after = None
        qualified = False
        elapsed = effective_ms = None
        state = dict(stdout=bytearray(), stderr=bytearray(), returncode=None,
                     stdin_bytes=0, stdin_sha256=None, stdin_complete=False, sender_failed=False)
        status = "refused"
        input_path = path_before = held_before = None
        try:
            self._guard()
            _label(label)
            _number(seconds)
            _need(type(cap) is int and 0 < cap <= MAX_CAPTURE and type(full_budget) is bool)
            operation = dict(argv=copy.deepcopy(argv), stdin=copy.deepcopy(source_binding))
            contract.validate_operation(copy.deepcopy(operation), copy.deepcopy(self._admission))
            source_binding = copy.deepcopy(operation["stdin"])
            operation_sha = contract.operation_digest(copy.deepcopy(operation))
            index = self.count + 1
            context = dict(index=index, phase="before", label=label,
                operation_sha256=operation_sha, transport_id=self._target["transport_id"])
            if source_binding is not None:
                input_path = file_guard._existing_D_file(source_binding["path"], "input")
                environment.check_binding(source_binding)
                path_before = _file_stamp(input_path.stat())
                source = input_path.open("rb")
                held_before = _file_stamp(os.fstat(source.fileno()))
                _need(path_before[:4] == held_before[:4] and path_before[5] == held_before[5], "input_identity")
                state["input_limit"] = source_binding["bytes"]
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.setsockopt(socket.SOL_SOCKET, socket.SO_EXCLUSIVEADDRUSE, 1)
            sock.bind(("127.0.0.1", 0))
            local = sock.getsockname()
            _need(type(local[1]) is int and 0 < local[1] <= 65535 and local[1] != 15937)
            anchor = dict(handle=sock.fileno(), socket_id=id(sock), local_address=local[0], local_port=local[1])
            self._timeout(sock, self.until)
            sock.connect(("127.0.0.1", 15937))
            before = self._proof(self._proofs / ("command-%04d-before.json" % index), context, sock, anchor)
            self._guard()
            remaining = self.until - self._now()
            _need(remaining > 0 and (not full_budget or remaining >= seconds), "client_deadline")
            effective = min(seconds, remaining)
            effective_ms = math.ceil(effective * 1000)
            started = self._now()
            deadline = started + effective
            if operation["argv"][:2] == ["am", "instrument"]:
                method = operation["argv"][6]
                kind = "import" if method == contract.CLASS + "#" + contract.METHODS[0] else "author"
                self.lease.claim_once(kind, operation_sha)
                self._fast_guard(deadline)
            # Dispatch is counted exactly once, immediately before the first
            # target-selecting frame. A failed pre-proof is not a SDK command.
            self.count, dispatched = index, True
            self._send(sock, _smart_frame(("host:transport-id:%d" % self._target["transport_id"]).encode("ascii")), deadline)
            self._status(sock, deadline)
            self._send(sock, _smart_frame(("shell,v2,raw:" + shlex.join(operation["argv"])).encode("utf-8")), deadline)
            self._status(sock, deadline)
            sender = threading.Thread(target=self._send_shell, args=(sock, source, state, deadline), daemon=True)
            sender.start()
            sender_started = True
            self._read_shell(sock, state, deadline, cap)
            # Exit plus EOF is the measured shell outcome even if a sender or
            # resource cannot subsequently be joined/closed and qualified.
            status = "completed"
            sender.join(timeout=min(1.0, max(0.0, deadline - self._now())))
            sender_joined = not sender.is_alive()
            _need(sender_joined and not state["sender_failed"] and state["stdin_complete"], "input")
            # This describes the actual shell protocol outcome. Later source,
            # proof or cleanup refusals change qualification, not that outcome.
            if source is not None:
                _need(_file_stamp(os.fstat(source.fileno())) == held_before and
                      _file_stamp(input_path.stat()) == path_before, "input_identity")
                _need(state["stdin_bytes"] == source_binding["bytes"] and
                      state["stdin_sha256"] == source_binding["sha256"], "input_identity")
                environment.check_binding(source_binding)
            context["phase"] = "after"
            after = self._proof(self._proofs / ("command-%04d-after.json" % index), context, sock, anchor, after=True)
            self._guard()
        except BaseException as error:
            if status != "completed":
                if isinstance(error, (TimeoutError, socket.timeout)) or str(error) == "client_deadline":
                    status = "timeout"
                elif isinstance(error, (KeyboardInterrupt, SystemExit)):
                    status = "cancelled"
                elif isinstance(error, OSError):
                    status = "io_error"
        finally:
            if dispatched:
                try:
                    elapsed = math.ceil(max(0, self._now() - started) * 1000)
                except BaseException:
                    elapsed = None
            # A reader failure may leave a blocked sender. Interrupt only this
            # owned connection before joining; do not race a live file reader.
            if sender is not None and sender_started:
                try:
                    if sender.is_alive() and sock is not None:
                        try:
                            sock.shutdown(socket.SHUT_RDWR)
                        except OSError:
                            pass
                    sender.join(timeout=1.0)
                    sender_joined = not sender.is_alive()
                except BaseException:
                    sender_joined = False
            else:
                sender_joined = True
            if source is None:
                input_closed = True
            elif sender_joined:
                try:
                    source.close()
                    input_closed = True
                except BaseException:
                    input_closed = False
            if sock is not None:
                try:
                    sock.close()
                    socket_closed = True
                except BaseException:
                    socket_closed = False
            if dispatched:
                try:
                    self._guard()
                    qualified = (status == "completed" and state["returncode"] == 0 and before is not None and
                        after is not None and sender_joined and input_closed and socket_closed and
                        state["stdin_complete"] and not state["sender_failed"])
                except BaseException:
                    qualified = False
                try:
                    stem = self.directory / ("command-%04d" % self.count)
                    stdout = self._write_bytes(stem.with_suffix(".stdout.bin"), bytes(state["stdout"]))
                    stderr = self._write_bytes(stem.with_suffix(".stderr.bin"), bytes(state["stderr"]))
                    record = dict(version=4, protocol=SDK_PROTOCOL, session=self.session_binding,
                        index=self.count, label=label, operation=copy.deepcopy(operation),
                        operation_sha256=operation_sha, transport_id=self._target["transport_id"],
                        status=status, returncode=state["returncode"],
                        cleanup_complete=socket_closed and sender_joined and input_closed,
                        elapsed_ms=elapsed, effective_deadline_ms=effective_ms, stdout=stdout, stderr=stderr,
                        stdin_sha256=state["stdin_sha256"], stdin_bytes=state["stdin_bytes"],
                        stdin_complete=state["stdin_complete"], server_before=before, server_after=after,
                        client_qualified=qualified, socket_closed=socket_closed,
                        sender_joined=sender_joined, input_closed=input_closed)
                    contract.validate_client_record(copy.deepcopy(record), self.session)
                    environment.create_json(stem.with_suffix(".json"), record)
                    self._directory_guard()
                except BaseException:
                    qualified = False
            if not qualified:
                self._poison()
        _need(qualified, "capture_failed")
        return bytes(state["stdout"])

    def close(self):
        self._poison()
