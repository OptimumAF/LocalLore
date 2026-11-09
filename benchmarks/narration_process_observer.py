"""Held Windows Job observations for the fixed narration comparison harness.

This module observes an existing Job and never starts or terminates a process.
Copyright 2026 LocalLore contributors. SPDX-License-Identifier: Apache-2.0
"""
import ctypes
from ctypes import wintypes as win
import os
from pathlib import PureWindowsPath
import time

WAIT_OBJECT_0 = 0
WAIT_TIMEOUT = 258
MAX_MEMBERS = 64
MAX_TRANSIENTS = 16
EXIT_GRACE_MS = 50
TERMINAL_SECONDS = 5


class ObservationRefused(ValueError):
    """The required process identity or closure could not be established."""


class ImageUnavailable(ObservationRefused):
    def __init__(self, code):
        super().__init__("image")
        self.code = code
        self.pid = None
        self.creation_filetime = None


def _need(condition, reason):
    if not condition:
        raise ObservationRefused(reason)


class _JobPids(ctypes.Structure):
    _fields_ = [("assigned", win.DWORD), ("count", win.DWORD), ("pids", ctypes.c_size_t * MAX_MEMBERS)]


class WindowsProcessApi:
    def __init__(self):
        _need(os.name == "nt", "platform")
        self.kernel = ctypes.WinDLL("kernel32", use_last_error=True)
        signatures = {
            "OpenProcess": ([win.DWORD, win.BOOL, win.DWORD], win.HANDLE),
            "CloseHandle": ([win.HANDLE], win.BOOL),
            "GetProcessId": ([win.HANDLE], win.DWORD),
            "GetProcessTimes": ([win.HANDLE] + [ctypes.POINTER(win.FILETIME)] * 4, win.BOOL),
            "IsProcessInJob": ([win.HANDLE, win.HANDLE, win.LPBOOL], win.BOOL),
            "QueryFullProcessImageNameW": ([win.HANDLE, win.DWORD, win.LPWSTR, win.LPDWORD], win.BOOL),
            "QueryInformationJobObject": ([win.HANDLE, ctypes.c_int, win.LPVOID, win.DWORD, win.LPDWORD], win.BOOL),
            "WaitForSingleObject": ([win.HANDLE, win.DWORD], win.DWORD),
            "GetExitCodeProcess": ([win.HANDLE, win.LPDWORD], win.BOOL),
        }
        for name, (args, result) in signatures.items():
            fn = getattr(self.kernel, name)
            fn.argtypes, fn.restype = args, result

    def members(self, job):
        value, returned = _JobPids(), win.DWORD()
        _need(self.kernel.QueryInformationJobObject(job, 3, ctypes.byref(value), ctypes.sizeof(value),
                                                   ctypes.byref(returned))
              and value.count == value.assigned <= MAX_MEMBERS
              and 8 + value.count * ctypes.sizeof(ctypes.c_size_t) <= returned.value <= ctypes.sizeof(value),
              "job_roster")
        members = set(value.pids[:value.count])
        _need(len(members) == value.count and 0 not in members, "job_roster")
        return members

    def open(self, pid):
        return self.kernel.OpenProcess(0x1000 | 0x100000, False, pid)

    def member(self, handle, job):
        present = win.BOOL()
        _need(self.kernel.IsProcessInJob(handle, job, ctypes.byref(present)), "job_query")
        return bool(present.value)

    def creation(self, handle, pid):
        times = [win.FILETIME() for _ in range(4)]
        _need(self.kernel.GetProcessId(handle) == pid and
              self.kernel.GetProcessTimes(handle, *(ctypes.byref(value) for value in times)), "identity")
        created = (times[0].dwHighDateTime << 32) | times[0].dwLowDateTime
        _need(created > 0, "identity")
        return created

    def image(self, handle):
        path = ctypes.create_unicode_buffer(32768)
        size = win.DWORD(len(path))
        if not self.kernel.QueryFullProcessImageNameW(handle, 0, path, ctypes.byref(size)):
            raise ImageUnavailable(ctypes.get_last_error())
        _need(0 < size.value < len(path), "image")
        return path.value

    def wait(self, handle, milliseconds):
        return self.kernel.WaitForSingleObject(handle, milliseconds)

    def exit_code(self, handle):
        value = win.DWORD()
        _need(self.kernel.GetExitCodeProcess(handle, ctypes.byref(value)), "exit_code")
        return int(value.value)

    def close(self, handle):
        return bool(self.kernel.CloseHandle(handle))


class NarrationProcessObserver:
    """Observe one exact probe and one exact worker under an already owned Job."""

    def __init__(self, api, job, direct_pid, direct_image, worker_image, *, gate_pid=None):
        self.direct_image = PureWindowsPath(direct_image)
        self.worker_image = PureWindowsPath(worker_image)
        _need(self.direct_image.is_absolute() and self.worker_image.is_absolute()
              and self.direct_image != self.worker_image, "images")
        _need(type(direct_pid) is int and 0 < direct_pid < 2**32
              and (gate_pid is None or type(gate_pid) is int and 0 < gate_pid < 2**32 and gate_pid != direct_pid),
              "identity")
        self.api = api
        self.job = job
        self.direct_pid = direct_pid
        self.gate_pid = gate_pid
        self.held = {}
        self.transients = {}
        self.refused = False
        self.closed = False
        self.close_failed = False

    def _release(self, handle):
        try:
            closed = self.api.close(handle) is True
        except BaseException:
            closed = False
        self.close_failed = self.close_failed or not closed
        return closed

    def _members(self):
        members = self.api.members(self.job)
        _need(type(members) is set and len(members) <= MAX_MEMBERS
              and all(type(pid) is int and 0 < pid < 2**32 for pid in members), "job_roster")
        return members

    def _observe(self, pid):
        required = pid == self.direct_pid
        handle = self.api.open(pid)
        if not handle:
            _need(not required and pid not in self._members(), "process_open")
            return
        try:
            _need(self.api.member(handle, self.job), "job_member")
            created = self.api.creation(handle, pid)
            try:
                actual = PureWindowsPath(self.api.image(handle))
            except ImageUnavailable as error:
                # No role can be inferred from an image failure. Only a distinct,
                # signaled member after both positive identities can be recorded.
                _need(type(error.code) is int and 0 <= error.code < 2**32, "image")
                if (required or self.held.keys() != {"direct", "worker"}
                        or self.api.wait(handle, EXIT_GRACE_MS) != WAIT_OBJECT_0):
                    error.pid = pid
                    error.creation_filetime = created
                    raise
                key = (pid, created)
                _need(key in self.transients or len(self.transients) < MAX_TRANSIENTS, "transient_roster")
                self.transients[key] = dict(pid=pid, creation_filetime=created,
                                            image_error=error.code, exit=self.api.exit_code(handle))
                return

            _need(actual.is_absolute(), "image")
            if required:
                _need(actual == self.direct_image, "direct_image")
                role = "direct"
            elif actual.name.casefold() == self.worker_image.name.casefold():
                _need(actual == self.worker_image, "worker_image")
                role = "worker"
            else:
                return
            _need(role not in self.held and self.api.wait(handle, 0) == WAIT_TIMEOUT, "required_identity")
            self.held[role] = (handle, dict(pid=pid, creation_filetime=created, executable=str(actual)))
            handle = None
        finally:
            if handle is not None:
                _need(self._release(handle), "handle_close")

    def poll(self):
        """Check the current Job roster, retaining exact role handles once observed."""
        _need(not self.refused and not self.closed, "observer_state")
        try:
            members = self._members()
            retained = {identity["pid"] for _, identity in self.held.values()}
            pending = members - retained - {self.gate_pid}
            if "direct" not in self.held:
                _need(self.direct_pid in pending, "direct_missing")
                self._observe(self.direct_pid)
                pending.remove(self.direct_pid)
            for pid in sorted(pending):
                self._observe(pid)
        except (OSError, ValueError):
            self.refused = True
            raise
        return self.held.keys() == {"direct", "worker"}

    def finish(self):
        """Require known exits and release every retained handle before returning proof."""
        terminal = {}
        deadline = time.monotonic() + TERMINAL_SECONDS
        try:
            _need(not self.refused and not self.closed and self.held.keys() == {"direct", "worker"}, "required_roles")
            for role, (handle, identity) in self.held.items():
                wait_ms = max(0, int((deadline - time.monotonic()) * 1000))
                _need(self.api.wait(handle, wait_ms) == WAIT_OBJECT_0, "process_exit")
                terminal[role] = dict(identity, exit=self.api.exit_code(handle))
        finally:
            _need(self.close(), "handle_close")
        terminal["unclassified_exits"] = [self.transients[key] for key in sorted(self.transients)]
        terminal["handles_closed"] = True
        return terminal

    def close(self):
        """Try each held handle once, even if another handle has uncertain closure."""
        if not self.closed:
            self.closed = True
            for handle, _ in self.held.values():
                self._release(handle)
            self.held.clear()
        return not self.close_failed
