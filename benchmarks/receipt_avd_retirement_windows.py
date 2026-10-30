"""Held-object Windows retirement primitives; importing performs no I/O.

Only an explicitly invoked reviewed executor may use these primitives. Handles
deny content writes/deletion sharing, not other compatible readers. A successful
disposition request is not immediate unlink or multi-file atomicity.

Copyright 2026 LocalLore contributors. SPDX-License-Identifier: Apache-2.0
"""
import copy
import ctypes
import hashlib
import math
import os
from pathlib import Path, PureWindowsPath
import re
import stat
import time

CHUNK = 1024 * 1024
IDENTITY_KEYS = frozenset(("volume_serial", "file_index", "bytes", "links",
                           "creation_filetime", "write_filetime", "attributes"))


class RetirementWindowsError(RuntimeError):
    def __init__(self, reason, *, cleanup_known=True):
        self.reason = reason if type(reason) is str and re.fullmatch(r"[a-z][a-z0-9_]{0,63}", reason) else "native"
        self.cleanup_known = cleanup_known if type(cleanup_known) is bool else False
        super().__init__(self.reason)


def _need(value, reason):
    if not value:
        raise RetirementWindowsError(reason)


class _Clock:
    def __init__(self, deadline):
        _need(type(deadline) is float and math.isfinite(deadline) and deadline > 0, "deadline")
        self.deadline, self.last = deadline, None
        self.check()

    def check(self):
        now = time.monotonic()
        _need(type(now) in (int, float) and math.isfinite(now) and
              (self.last is None or now >= self.last) and now < self.deadline, "deadline")
        self.last = now


def _image_path(raw):
    _need(type(raw) is str and raw and not any(ord(c) < 32 for c in raw), "path")
    path = PureWindowsPath(raw)
    _need(path.is_absolute() and path.drive.upper() == "D:" and raw.count(":") == 1 and
          ".." not in path.parts and str(Path(raw)) == os.path.abspath(raw), "path")
    for part in path.parts[1:]:
        _need(part and not part.endswith((".", " ")) and
              not any(c in '<>:"|?*' for c in part) and
              re.fullmatch(r"(?i)(CON|PRN|AUX|NUL|COM[1-9¹²³]|LPT[1-9¹²³])(?:\..*)?", part) is None,
              "path")
    return Path(raw)


def _path_metadata(path):
    # Parent checks never resolve away a reparse point before inspecting it.
    for ancestor in (path, *path.parents):
        info = ancestor.lstat()
        _need(not stat.S_ISLNK(info.st_mode) and not getattr(info, "st_file_attributes", 0) & 0x400, "path")
    info = path.lstat()
    _need(stat.S_ISREG(info.st_mode) and info.st_nlink == 1, "path")


def _identity(value):
    _need(type(value) is dict and set(value) == IDENTITY_KEYS and
          all(type(v) is int and v >= 0 for v in value.values()), "metadata")
    _need(value["volume_serial"] <= 0xffffffff and 0 < value["file_index"] <= 0xffffffffffffffff and
          value["bytes"] <= 0xffffffffffffffff and value["links"] == 1 and
          0 < value["creation_filetime"] <= 0xffffffffffffffff and
          0 < value["write_filetime"] <= 0xffffffffffffffff and value["attributes"] <= 0xffffffff and
          value["attributes"] & (0x10 | 0x40 | 0x400) == 0, "metadata")
    return copy.deepcopy(value)


class _FILETIME(ctypes.Structure):
    _fields_ = [("low", ctypes.c_uint32), ("high", ctypes.c_uint32)]


class _BY_HANDLE_FILE_INFORMATION(ctypes.Structure):
    _fields_ = [("attributes", ctypes.c_uint32), ("creation", _FILETIME),
                ("access", _FILETIME), ("write", _FILETIME),
                ("volume", ctypes.c_uint32), ("size_high", ctypes.c_uint32),
                ("size_low", ctypes.c_uint32), ("links", ctypes.c_uint32),
                ("index_high", ctypes.c_uint32), ("index_low", ctypes.c_uint32)]


class _FILE_DISPOSITION_INFO(ctypes.Structure):
    # winbase.h BOOLEAN is one byte, unlike Win32 BOOL.
    _fields_ = [("DeleteFile", ctypes.c_ubyte)]


def _u64(low, high):
    return (int(high) << 32) | int(low)


class _WindowsApi:
    """One fixed Kernel32 adapter. Tests may patch this private factory."""
    def __init__(self):
        _need(os.name == "nt", "platform")
        _need(ctypes.sizeof(_FILETIME) == 8 and ctypes.sizeof(_BY_HANDLE_FILE_INFORMATION) == 52 and
              ctypes.sizeof(_FILE_DISPOSITION_INFO) == 1, "abi")
        dll = ctypes.WinDLL("kernel32", use_last_error=True)
        handle, dword, boolean = ctypes.c_void_p, ctypes.c_uint32, ctypes.c_int
        pointer, wide = ctypes.c_void_p, ctypes.c_wchar_p
        specs = {
            "CreateFileW": ([wide, dword, dword, pointer, dword, dword, handle], handle),
            "GetFileType": ([handle], dword),
            "GetFileInformationByHandle": ([handle, ctypes.POINTER(_BY_HANDLE_FILE_INFORMATION)], boolean),
            "GetVolumeInformationByHandleW": ([handle, wide, dword, ctypes.POINTER(dword),
                ctypes.POINTER(dword), ctypes.POINTER(dword), wide, dword], boolean),
            "ReadFile": ([handle, pointer, dword, ctypes.POINTER(dword), pointer], boolean),
            "SetFileInformationByHandle": ([handle, ctypes.c_int, pointer, dword], boolean),
            "CloseHandle": ([handle], boolean),
            "OpenProcess": ([dword, boolean, dword], handle),
            "GetProcessTimes": ([handle, *([ctypes.POINTER(_FILETIME)] * 4)], boolean),
            "QueryFullProcessImageNameW": ([handle, dword, wide, ctypes.POINTER(dword)], boolean),
            "WaitForSingleObject": ([handle, dword], dword),
        }
        self.dll = dll
        for name, (args, result) in specs.items():
            function = getattr(dll, name)
            function.argtypes, function.restype = args, result

    def _open(self, path, access, sharing, flags):
        result = self.dll.CreateFileW(str(path), access, sharing, None, 3, flags, None)
        _need(result not in (None, 0, ctypes.c_void_p(-1).value), "image_open")
        return int(result)

    def open_image(self, path):
        # OPEN_EXISTING; GENERIC_READ|DELETE; FILE_SHARE_READ. Never DELETE_ON_CLOSE.
        return self._open(path, 0x80000000 | 0x10000, 1, 0x00200000 | 0x08000000)

    def open_probe(self, path):
        # Metadata-only access does not conflict with the held DELETE access.
        return self._open(path, 0, 1 | 2 | 4, 0x00200000 | 0x02000000)

    def information(self, handle):
        _need(self.dll.GetFileType(handle) == 1, "metadata")
        value = _BY_HANDLE_FILE_INFORMATION()
        _need(self.dll.GetFileInformationByHandle(handle, ctypes.byref(value)), "metadata")
        return dict(volume_serial=int(value.volume), file_index=_u64(value.index_low, value.index_high),
                    bytes=_u64(value.size_low, value.size_high), links=int(value.links),
                    creation_filetime=_u64(value.creation.low, value.creation.high),
                    write_filetime=_u64(value.write.low, value.write.high), attributes=int(value.attributes))

    def filesystem(self, handle):
        name = ctypes.create_unicode_buffer(256)
        _need(self.dll.GetVolumeInformationByHandleW(handle, None, 0, None, None, None,
                                                     name, len(name)), "filesystem")
        return name.value

    def read(self, handle, limit):
        _need(type(limit) is int and 1 <= limit <= CHUNK, "read")
        buffer = ctypes.create_string_buffer(limit)
        count = ctypes.c_uint32()
        _need(self.dll.ReadFile(handle, buffer, limit, ctypes.byref(count), None), "read")
        _need(count.value <= limit, "read")
        return buffer.raw[:count.value]

    def mark(self, handle):
        value = _FILE_DISPOSITION_INFO(1)
        _need(self.dll.SetFileInformationByHandle(handle, 4, ctypes.byref(value), ctypes.sizeof(value)), "mark")
        return True

    def close(self, handle):
        return bool(self.dll.CloseHandle(handle))

    def open_process(self, pid):
        # Query identity and wait(0), without terminate/write/debug rights.
        handle = self.dll.OpenProcess(0x1000 | 0x100000, False, pid)
        error = ctypes.get_last_error() if not handle else 0
        if not handle:
            _need(error == 87, "process_open")
            return None
        return int(handle)

    def process_creation(self, handle):
        values = [_FILETIME() for _ in range(4)]
        _need(self.dll.GetProcessTimes(handle, *(ctypes.byref(v) for v in values)), "process_query")
        return _u64(values[0].low, values[0].high)

    def process_image(self, handle):
        buffer = ctypes.create_unicode_buffer(32768)
        count = ctypes.c_uint32(len(buffer))
        _need(self.dll.QueryFullProcessImageNameW(handle, 0, buffer, ctypes.byref(count)), "process_query")
        _need(0 < count.value < len(buffer), "process_query")
        return buffer[:count.value]

    def process_wait(self, handle):
        return int(self.dll.WaitForSingleObject(handle, 0))


class WindowsImageSet:
    """Acquire all handles first, hash all, then permit explicit dispositions.

    snapshots.identity has exactly IDENTITY_KEYS, all integers from the same
    BY_HANDLE_FILE_INFORMATION API. NTFS is required because its held 64-bit
    file index is the identity used here; ReFS/unknown filesystems refuse.
    """
    def __init__(self, bindings, deadline):
        self._images, self._probes = [], []
        self._api = None
        self._qualified = self._closed = self._close_failed = self._poisoned = False
        try:
            self._clock = _Clock(deadline)
            _need(type(bindings) is list and len(bindings) <= 64, "bindings")
            checked, paths = [], set()
            for binding in bindings:
                _need(type(binding) is dict and set(binding) == {"path", "bytes", "sha256"} and
                      type(binding["bytes"]) is int and 0 <= binding["bytes"] <= 0x7fffffffffffffff and
                      type(binding["sha256"]) is str and re.fullmatch("[0-9a-f]{64}", binding["sha256"]), "bindings")
                path = _image_path(binding["path"])
                _need(path not in paths, "bindings")
                paths.add(path)
                _path_metadata(path)
                checked.append((copy.deepcopy(binding), path))
            self._clock.check()
            if checked:
                self._api = _WindowsApi()
            # No content read or disposition occurs until every image is held.
            for binding, path in checked:
                self._clock.check()
                _path_metadata(path)
                entry = self._own(self._api.open_image(path), self._images)
                entry.update(binding=binding, path=path, marked=False, mark_attempted=False)
            identities = set()
            for entry in self._images:
                self._clock.check()
                _need(self._api.filesystem(entry["handle"]) == "NTFS", "filesystem")
                identity = _identity(self._api.information(entry["handle"]))
                key = (identity["volume_serial"], identity["file_index"])
                _need(key not in identities and identity["bytes"] == entry["binding"]["bytes"], "metadata")
                identities.add(key)
                entry["identity"] = identity
                digest, remaining = hashlib.sha256(), identity["bytes"]
                while remaining:
                    self._clock.check()
                    raw = self._api.read(entry["handle"], min(CHUNK, remaining))
                    _need(type(raw) is bytes and 0 < len(raw) <= min(CHUNK, remaining), "hash")
                    digest.update(raw)
                    remaining -= len(raw)
                self._clock.check()
                eof = self._api.read(entry["handle"], 1)
                _need(type(eof) is bytes and eof == b"" and
                      digest.hexdigest() == entry["binding"]["sha256"], "hash")
                self._check_entry(entry)
            self._clock.check()
            self._qualified = True
        except BaseException as error:
            known = True
            try:
                self.close()
            except BaseException:
                known = False
            reason = error.reason if isinstance(error, RetirementWindowsError) else "native"
            raise RetirementWindowsError(reason, cleanup_known=known and
                getattr(error, "cleanup_known", True)) from None

    def _own(self, handle, collection):
        _need(type(handle) is int and handle > 0, "handle")
        if any(v["handle"] == handle and not v["closed"] for v in self._images + self._probes):
            self._close_failed = True
            raise RetirementWindowsError("handle", cleanup_known=False)
        entry = dict(handle=handle, attempted=False, closed=False)
        collection.append(entry)
        return entry

    def _close_entry(self, entry):
        if not entry["attempted"]:
            entry["attempted"] = True
            try:
                entry["closed"] = self._api.close(entry["handle"]) is True
            except BaseException:
                entry["closed"] = False
            if not entry["closed"]:
                self._close_failed = True
        return entry["closed"]

    def _check_entry(self, entry):
        self._clock.check()
        _path_metadata(entry["path"])
        _need(_identity(self._api.information(entry["handle"])) == entry["identity"], "identity")
        probe = self._own(self._api.open_probe(entry["path"]), self._probes)
        try:
            _need(_identity(self._api.information(probe["handle"])) == entry["identity"], "identity")
            _path_metadata(entry["path"])
            self._clock.check()
        finally:
            if not self._close_entry(probe):
                raise RetirementWindowsError("close", cleanup_known=False)

    def _state(self):
        _need(self._qualified and not self._closed and not self._poisoned and
              not self._close_failed and not any(e["attempted"] for e in self._images), "state")
        self._clock.check()

    @property
    def snapshots(self):
        _need(self._qualified, "state")
        return copy.deepcopy([dict(binding=e["binding"], identity=e["identity"]) for e in self._images])

    def verify(self):
        try:
            self._state()
            for entry in self._images:
                if not entry["marked"]:
                    self._check_entry(entry)
            return True
        except BaseException as error:
            self._poisoned = True
            if isinstance(error, RetirementWindowsError):
                raise
            raise RetirementWindowsError("verify", cleanup_known=not self._close_failed) from None

    def mark_delete(self, index):
        try:
            self._state()
            _need(type(index) is int and 0 <= index < len(self._images), "index")
            entry = self._images[index]
            _need(not entry["marked"] and not entry["mark_attempted"], "state")
            self._check_entry(entry)
            self._clock.check()
            entry["mark_attempted"] = True
            _need(self._api.mark(entry["handle"]) is True, "mark")
            entry["marked"] = True
        except BaseException as error:
            self._poisoned = True
            if isinstance(error, RetirementWindowsError):
                raise
            raise RetirementWindowsError("mark", cleanup_known=not self._close_failed) from None

    def close(self):
        # Deliberately no clock check: cleanup attempts every known handle even
        # after expiry/failure. An uncertain attempt is never retried.
        for entry in self._images + self._probes:
            self._close_entry(entry)
        self._closed = not self._close_failed and all(e["closed"] for e in self._images + self._probes)
        if not self._closed:
            raise RetirementWindowsError("close", cleanup_known=False)
        return True

    @property
    def closed(self):
        return self._closed is True and not self._close_failed


def _process_identity(value):
    _need(type(value) is dict and set(value) == {"pid", "creation_filetime", "executable"} and
          type(value["pid"]) is int and 1 <= value["pid"] <= 0xffffffff and
          type(value["creation_filetime"]) is int and 1 <= value["creation_filetime"] <= 0xffffffffffffffff,
          "process_identity")
    path = value["executable"]
    _need(type(path) is str and path and not any(ord(c) < 32 for c in path), "process_identity")
    parsed = PureWindowsPath(path)
    _need(parsed.is_absolute() and re.fullmatch("[A-Za-z]:", parsed.drive) and
          path.count(":") == 1 and ".." not in parsed.parts, "process_identity")
    return copy.deepcopy(value)


def closed_processes(identities, deadline):
    """Fresh read-only process checks; a recycled PID is never queried further."""
    _need(type(identities) is list and len(identities) <= 512, "process_identity")
    admitted = [_process_identity(v) for v in identities]
    clock = _Clock(deadline)
    api = _WindowsApi() if admitted else None
    result = []
    for identity in admitted:
        clock.check()
        handle = None
        failure = None
        try:
            handle = api.open_process(identity["pid"])
            if handle is None:
                status = "pid_absent"
            else:
                _need(type(handle) is int and handle > 0, "process_open")
                creation = api.process_creation(handle)
                _need(type(creation) is int and 1 <= creation <= 0xffffffffffffffff, "process_query")
                if creation != identity["creation_filetime"]:
                    status = "pid_reused"
                else:
                    image = api.process_image(handle)
                    _process_identity(dict(identity, executable=image))
                    _need(PureWindowsPath(image) == PureWindowsPath(identity["executable"]), "process_identity")
                    wait = api.process_wait(handle)
                    _need(type(wait) is int and wait in (0, 258), "process_query")
                    _need(wait == 0, "process_live")
                    status = "exited"
            clock.check()
        except BaseException as error:
            failure = error
        finally:
            if handle is not None:
                # Exactly one close attempt, even if the query expired or failed.
                try:
                    closed = api.close(handle) is True
                except BaseException:
                    closed = False
                if not closed:
                    raise RetirementWindowsError("process_close", cleanup_known=False) from None
        if failure is not None:
            reason = failure.reason if isinstance(failure, RetirementWindowsError) else "process_query"
            raise RetirementWindowsError(reason, cleanup_known=getattr(failure, "cleanup_known", True)) from None
        result.append(dict(identity=identity, status=status))
    return result
