"""Windows IO for the explicitly selected held-socket protocol, never legacy fallback.

Construction/import performs no file, DLL, process or socket observation. Full
native TCP tables stay in memory; the orchestration owns scoped evidence output.
Copyright 2026 LocalLore contributors. SPDX-License-Identifier: Apache-2.0
"""
import copy
import ctypes
from ctypes import wintypes
import hashlib
import math
import os
from pathlib import Path
import socket
import stat
import time

from benchmarks.adb_held_socket import (
    REQUEST, ProbeRefused, Snapshot, TableCapture, validate_admission,
)
from benchmarks.windows_tcp_observation import MAX_CAPTURE, decode_table


def _need(value, reason='backend'):
    if not value:
        raise ProbeRefused(reason)


class _Row4(ctypes.Structure):
    _fields_ = [('state', wintypes.DWORD), ('local', wintypes.DWORD),
                ('port', wintypes.DWORD), ('remote', wintypes.DWORD),
                ('remote_port', wintypes.DWORD), ('pid', wintypes.DWORD)]


class _Row6(ctypes.Structure):
    _fields_ = [('local', ctypes.c_ubyte * 16), ('local_scope', wintypes.DWORD),
                ('port', wintypes.DWORD), ('remote', ctypes.c_ubyte * 16),
                ('remote_scope', wintypes.DWORD), ('remote_port', wintypes.DWORD),
                ('state', wintypes.DWORD), ('pid', wintypes.DWORD)]


class _Table4(ctypes.Structure):
    _fields_ = [('count', wintypes.DWORD), ('rows', _Row4 * 1)]


class _Table6(ctypes.Structure):
    _fields_ = [('count', wintypes.DWORD), ('rows', _Row6 * 1)]


def _check_abi():
    _need(ctypes.sizeof(wintypes.DWORD) == 4 and ctypes.sizeof(_Row4) == 24
          and ctypes.sizeof(_Row6) == 56 and _Table4.rows.offset == 4
          and _Table6.rows.offset == 4, 'snapshot')
    _need([getattr(_Row4, field).offset for field, _ in _Row4._fields_]
          == [0, 4, 8, 12, 16, 20], 'snapshot')
    _need([getattr(_Row6, field).offset for field, _ in _Row6._fields_]
          == [0, 16, 20, 24, 40, 44, 48, 52], 'snapshot')


class _WindowsApi:
    """Small native adapter. Its constructor is called only by backend.open."""
    def __init__(self):
        _need(os.name == 'nt')
        _check_abi()
        kernel = ctypes.WinDLL('kernel32', use_last_error=True)
        network = ctypes.WinDLL('iphlpapi', use_last_error=True)
        self._open = kernel.OpenProcess
        self._open.argtypes = [wintypes.DWORD, wintypes.BOOL, wintypes.DWORD]
        self._open.restype = wintypes.HANDLE
        self._pid = kernel.GetProcessId
        self._pid.argtypes = [wintypes.HANDLE]
        self._pid.restype = wintypes.DWORD
        self._times = kernel.GetProcessTimes
        self._times.argtypes = [wintypes.HANDLE] + [ctypes.POINTER(wintypes.FILETIME)] * 4
        self._times.restype = wintypes.BOOL
        self._image = kernel.QueryFullProcessImageNameW
        self._image.argtypes = [wintypes.HANDLE, wintypes.DWORD, wintypes.LPWSTR,
                                ctypes.POINTER(wintypes.DWORD)]
        self._image.restype = wintypes.BOOL
        self._wait = kernel.WaitForSingleObject
        self._wait.argtypes = [wintypes.HANDLE, wintypes.DWORD]
        self._wait.restype = wintypes.DWORD
        self._close = kernel.CloseHandle
        self._close.argtypes = [wintypes.HANDLE]
        self._close.restype = wintypes.BOOL
        self._tcp = network.GetExtendedTcpTable
        self._tcp.argtypes = [ctypes.c_void_p, ctypes.POINTER(wintypes.DWORD),
                              wintypes.BOOL, wintypes.ULONG, ctypes.c_int, wintypes.ULONG]
        self._tcp.restype = wintypes.DWORD

    def open_process(self, pid):
        # Query and synchronization only: no terminate, suspend or memory rights.
        handle = self._open(0x1000 | 0x100000, False, pid)
        _need(handle not in (None, 0), 'identity')
        return handle

    def identity(self, handle):
        pid = int(self._pid(handle))
        created, exited, kernel, user = (wintypes.FILETIME() for _ in range(4))
        _need(pid > 0 and self._times(handle, ctypes.byref(created), ctypes.byref(exited),
                                     ctypes.byref(kernel), ctypes.byref(user)), 'identity')
        size = wintypes.DWORD(32768)
        image = ctypes.create_unicode_buffer(size.value)
        _need(self._image(handle, 0, image, ctypes.byref(size))
              and 0 < size.value < len(image), 'identity')
        return dict(pid=pid, creation_filetime=(int(created.dwHighDateTime) << 32)
                    | int(created.dwLowDateTime), executable=image.value)

    def alive(self, handle):
        # A non-signalled held process handle, not merely STILL_ACTIVE exit text.
        return self._wait(handle, 0) == 258

    def close_handle(self, handle):
        return bool(self._close(handle))

    def capture(self, family):
        _check_abi()
        _need(type(family) is int and family in (2, 23), 'snapshot')
        size = wintypes.DWORD(0)
        initial = int(self._tcp(None, ctypes.byref(size), False, family, 5, 0))
        _need(initial in (0, 122) and 4 <= size.value <= MAX_CAPTURE, 'snapshot')
        allocated = size.value
        buffer = ctypes.create_string_buffer(allocated)
        final = int(self._tcp(buffer, ctypes.byref(size), False, family, 5, 0))
        _need(final == 0 and 4 <= size.value <= allocated, 'snapshot')
        raw = bytes(buffer.raw[:size.value])
        try:
            decode_table(raw, family)  # Validate the entire returned view, no prefilter.
        except ValueError:
            raise ProbeRefused('snapshot') from None
        return TableCapture(family=family, raw=raw, allocated_bytes=allocated, table_class=5)


class WindowsBackend:
    """Own one socket and held process identities; no IO until open is called."""
    def __init__(self):
        self._api = None
        self._admission = None
        self._client = None
        self._handles = []
        self._uncertain_handles = set()
        self._handle_close_failed = False
        self._held = {}
        self._file_fds = set()
        self._uncertain_file_fds = set()
        self._file_close_failed = False
        self._socket = None
        self._socket_anchor = None
        self._socket_handle = None
        self._socket_id = None
        self._endpoint_pin = None
        self._open_called = False
        self._opened = False
        self._connect_called = False
        self._connected = False
        self._send_called = False
        self._sent = False
        self._closed = False
        self._poisoned = False
        self._socket_closed = True
        self._socket_close_attempted = False
        self._deadline = None
        self._last_clock = None

    def now(self):
        return time.monotonic()

    def _remaining(self, deadline):
        now = self.now()
        _need(type(deadline) in (int, float) and math.isfinite(deadline)
              and type(now) in (int, float) and math.isfinite(now) and deadline > now, 'deadline')
        _need(self._deadline is None or deadline == self._deadline, 'deadline')
        _need(self._last_clock is None or now >= self._last_clock, 'deadline')
        self._last_clock = now
        return deadline - now

    def _operation(self, deadline, action, opened=True):
        try:
            self._remaining(deadline)
            _need(not self._closed and not self._poisoned and (self._opened or not opened))
            result = action()
            self._remaining(deadline)
            return result
        except ProbeRefused:
            self._poisoned = True
            raise
        except (KeyboardInterrupt, InterruptedError, SystemExit):
            self._poisoned = True
            raise
        except BaseException:
            self._poisoned = True
            raise ProbeRefused('backend') from None

    def _make_api(self):
        return _WindowsApi()

    def _current_pid(self):
        return os.getpid()

    def _fresh_identity(self, pid):
        # This independent PID lookup has its own checked, tracked temporary
        # handle. It must not silently lose a failed CloseHandle result.
        handle = self._acquire_handle(pid)
        try:
            _need(self._api.alive(handle) is True, 'identity')
            identity = self._api.identity(handle)
            _need(identity.get('pid') == pid and self._api.alive(handle) is True, 'identity')
            return identity
        finally:
            _need(self._release_handle(handle), 'identity')

    def _acquire_handle(self, pid):
        handle = self._api.open_process(pid)
        _need(type(handle) is int and handle > 0 and handle not in self._handles, 'identity')
        self._handles.append(handle)
        return handle

    def _release_handle(self, handle):
        try:
            success = self._api.close_handle(handle) is True
        except BaseException:
            success = False
        if success:
            self._handles.remove(handle)
        else:
            self._uncertain_handles.add(handle)
            self._handle_close_failed = True
        return success

    def _process_bracket(self):
        observed = {}
        for name in ('server', 'client'):
            handle, expected = self._held[name]
            _need(self._api.alive(handle) is True, 'identity')
            identity = self._api.identity(handle)
            _need(identity == expected and self._fresh_identity(expected['pid']) == expected
                  and self._api.alive(handle) is True, 'identity')
            observed[name] = identity
        return observed

    @staticmethod
    def _identity(info):
        return [info.st_dev, info.st_ino, info.st_size, info.st_mtime_ns, info.st_ctime_ns]

    @staticmethod
    def _regular_stat(path):
        for component in (path, *path.parents):
            info = component.lstat()
            _need(not stat.S_ISLNK(info.st_mode)
                  and not (getattr(info, 'st_file_attributes', 0) & 0x400), 'identity')
        info = path.lstat()
        _need(stat.S_ISREG(info.st_mode), 'identity')
        _need(os.path.normcase(str(path.resolve(strict=True)))
              == os.path.normcase(os.path.abspath(path)), 'identity')
        return info

    def _pin_file(self, deadline):
        expected = self._admission['adb_file']
        path = Path(expected['path'])
        self._remaining(deadline)
        before = self._regular_stat(path)
        _need(self._identity(before) == expected['identity'], 'identity')
        fd = os.open(path, os.O_RDONLY | getattr(os, 'O_BINARY', 0))
        self._file_fds.add(fd)
        try:
            held = os.fstat(fd)
            _need(self._identity(held) == expected['identity'], 'identity')
            count = 0
            hashed = hashlib.sha256()
            while True:
                self._remaining(deadline)
                block = os.read(fd, min(1024 * 1024, expected['bytes'] - count + 1))
                if not block:
                    break
                count += len(block)
                _need(count <= expected['bytes'], 'identity')
                hashed.update(block)
            self._remaining(deadline)
            _need(count == expected['bytes'] and hashed.hexdigest() == expected['sha256']
                  and self._identity(os.fstat(fd)) == expected['identity']
                  and self._identity(self._regular_stat(path)) == expected['identity'], 'identity')
            return copy.deepcopy(expected)
        finally:
            try:
                os.close(fd)
                self._file_fds.remove(fd)
            except BaseException:
                self._file_close_failed = True
                self._uncertain_file_fds.add(fd)
                raise ProbeRefused('identity') from None

    def open(self, admission, deadline):
        def action():
            _need(not self._open_called)
            self._open_called = True
            self._deadline = deadline
            self._admission = validate_admission(admission)
            self._api = self._make_api()
            own_pid = self._current_pid()
            _need(type(own_pid) is int and own_pid > 0
                  and own_pid != self._admission['server']['pid'], 'identity')
            for name, pid in (('server', self._admission['server']['pid']), ('client', own_pid)):
                self._remaining(deadline)
                handle = self._acquire_handle(pid)
                identity = self._api.identity(handle)
                _need(type(identity) is dict and identity.get('pid') == pid, 'identity')
                if name == 'server':
                    _need(identity == self._admission['server'], 'identity')
                self._held[name] = (handle, copy.deepcopy(identity))
            self._client = copy.deepcopy(self._held['client'][1])
            self._process_bracket()
            self._opened = True
        return self._operation(deadline, action, opened=False)

    def bracket(self, admission, deadline):
        def action():
            _need(validate_admission(admission) == self._admission, 'identity')
            processes = self._process_bracket()
            pin = self._pin_file(deadline)
            _need(self._process_bracket() == processes, 'identity')
            return dict(server=copy.deepcopy(processes['server']), client=copy.deepcopy(processes['client']),
                        adb_file=pin, held_processes_alive=True)
        return self._operation(deadline, action)

    def snapshot(self, deadline):
        def action():
            _check_abi()
            tables = []
            for family in (2, 23):
                self._remaining(deadline)
                captured = self._api.capture(family)
                self._remaining(deadline)
                _need(type(captured) is TableCapture and type(captured.family) is int and captured.family == family
                      and type(captured.table_class) is int and captured.table_class == 5
                      and type(captured.allocated_bytes) is int and type(captured.raw) is bytes
                      and 4 <= len(captured.raw) <= captured.allocated_bytes <= MAX_CAPTURE, 'snapshot')
                try:
                    decode_table(captured.raw, family)
                except ValueError:
                    raise ProbeRefused('snapshot') from None
                tables.append(captured)
            return Snapshot(tuple(tables), abi_checked=True)
        return self._operation(deadline, action)

    def _owned_socket(self):
        _need(self._socket is not None and self._socket is self._socket_anchor
              and id(self._socket) == self._socket_id, 'endpoint')
        handle = self._socket.fileno()
        _need(type(handle) is int and handle == self._socket_handle, 'endpoint')
        return self._socket

    def _read_endpoint(self):
        owned = self._owned_socket()
        local, peer = owned.getsockname(), owned.getpeername()
        _need(type(local) is tuple and len(local) == 2 and type(peer) is tuple and len(peer) == 2
              and local[0] == peer[0] == '127.0.0.1' and type(local[1]) is int
              and 0 < local[1] < 65536 and local[1] != 5037 and peer[1] == 5037, 'endpoint')
        result = dict(handle=self._socket_handle, socket_id=self._socket_id,
                      local_address=local[0], local_port=local[1], peer_address=peer[0], peer_port=peer[1])
        _need(self._endpoint_pin is None or result == self._endpoint_pin, 'endpoint')
        return result

    def connect(self, deadline):
        def action():
            _need(not self._connect_called, 'endpoint')
            self._connect_called = True
            owned = socket.socket(socket.AF_INET, socket.SOCK_STREAM, socket.IPPROTO_TCP)
            self._socket = self._socket_anchor = owned
            self._socket_closed = False
            self._socket_id = id(owned)
            self._socket_handle = owned.fileno()
            _need(type(self._socket_handle) is int and self._socket_handle > 0, 'endpoint')
            owned.settimeout(self._remaining(deadline))
            owned.connect(('127.0.0.1', 5037))
            self._endpoint_pin = self._read_endpoint()
            self._connected = True
        return self._operation(deadline, action)

    def endpoint(self, deadline):
        def action():
            _need(self._connected, 'endpoint')
            return copy.deepcopy(self._read_endpoint())
        return self._operation(deadline, action)

    def send(self, data, deadline):
        def action():
            _need(self._connected and not self._send_called and type(data) is bytes and data == REQUEST)
            self._send_called = True
            self._read_endpoint()
            owned = self._owned_socket()
            owned.settimeout(self._remaining(deadline))
            owned.sendall(REQUEST)
            self._sent = True
        return self._operation(deadline, action)

    def recv(self, limit, deadline):
        def action():
            _need(self._sent and type(limit) is int and 1 <= limit <= 13)
            self._read_endpoint()
            owned = self._owned_socket()
            owned.settimeout(self._remaining(deadline))
            data = owned.recv(limit)
            _need(type(data) is bytes and len(data) <= limit)
            return data
        return self._operation(deadline, action)

    def close(self):
        """Attempt every owned close, even after expiry or another close failure.

        process_handles_closed is conservative: it also requires all transient
        read-only file descriptors closed without an earlier close failure.
        Values with an uncertain failed close are retained, never blindly
        retried after possible handle/descriptor reuse. The bounded worker must
        refuse qualification and exit with cleanup=false in that case.
        """
        self._closed = True
        if (self._socket_anchor is not None and not self._socket_closed
                and not self._socket_close_attempted):
            self._socket_close_attempted = True
            try:
                # Never close a replacement handle/object as though it were
                # the one created and retained by this backend.
                _need(id(self._socket_anchor) == self._socket_id
                      and self._socket_anchor.fileno() == self._socket_handle, 'cleanup')
                self._socket_anchor.close()
                self._socket_closed = self._socket_anchor.fileno() == -1
            except BaseException:
                self._socket_closed = False
        all_closed = not self._file_close_failed and not self._handle_close_failed
        for fd in tuple(self._file_fds):
            if fd in self._uncertain_file_fds:
                all_closed = False
                continue
            try:
                os.close(fd)
                self._file_fds.remove(fd)
            except BaseException:
                self._uncertain_file_fds.add(fd)
                self._file_close_failed = True
                all_closed = False
        for handle in tuple(self._handles):
            if handle in self._uncertain_handles:
                all_closed = False
                continue
            try:
                if self._api.close_handle(handle) is True:
                    self._handles.remove(handle)
                else:
                    self._uncertain_handles.add(handle)
                    self._handle_close_failed = True
                    all_closed = False
            except BaseException:
                self._uncertain_handles.add(handle)
                self._handle_close_failed = True
                all_closed = False
        return dict(socket_closed=self._socket_closed,
                    process_handles_closed=all_closed and not self._handles and not self._file_fds)
