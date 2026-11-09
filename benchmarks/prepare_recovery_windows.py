"""D-only directory lifetime fence for explicitly authorized prepare recovery.

No import performs IO. Creation returns an already-held native handle; it never
uses a mkdir/open gap, adopts an existing directory or falls back to weaker APIs.
Copyright 2026 LocalLore contributors. SPDX-License-Identifier: Apache-2.0
"""
import ctypes
import os
from pathlib import Path
import re
import stat


class NativeRefused(RuntimeError):
    def __init__(self, reason, *, cleanup_known=True):
        self.reason = reason
        self.cleanup_known = cleanup_known
        super().__init__(reason)


def _need(condition, reason):
    if not condition:
        raise NativeRefused(reason)


def _path(value):
    path = Path(value)
    _need(path.is_absolute() and path.drive.upper() == 'D:' and
          str(path) == os.path.abspath(str(path)) and str(path).count(':') == 1, 'path')
    for part in path.parts[1:]:
        _need(part and not part.endswith(('.', ' ')) and
              not any(c in '<>:"|?*' or ord(c) < 32 for c in part) and
              re.fullmatch(r'(?i)(CON|PRN|AUX|NUL|COM[1-9]|LPT[1-9])(?:\..*)?', part) is None,
              'path')
    return path


def _ordinary(path):
    try:
        info = path.lstat()
    except OSError:
        raise NativeRefused('directory') from None
    _need(stat.S_ISDIR(info.st_mode) and not stat.S_ISLNK(info.st_mode) and
          not getattr(info, 'st_file_attributes', 0) & 0x400, 'directory')


class _FileTime(ctypes.Structure):
    _fields_ = [('low', ctypes.c_uint32), ('high', ctypes.c_uint32)]


class _Information(ctypes.Structure):
    _fields_ = [('attributes', ctypes.c_uint32), ('creation', _FileTime),
               ('access', _FileTime), ('write', _FileTime), ('volume', ctypes.c_uint32),
               ('size_high', ctypes.c_uint32), ('size_low', ctypes.c_uint32),
               ('links', ctypes.c_uint32), ('index_high', ctypes.c_uint32),
               ('index_low', ctypes.c_uint32)]


class _UnicodeString(ctypes.Structure):
    _fields_ = [('length', ctypes.c_ushort), ('maximum_length', ctypes.c_ushort),
               ('buffer', ctypes.c_wchar_p)]


class _ObjectAttributes(ctypes.Structure):
    _fields_ = [('length', ctypes.c_uint32), ('root', ctypes.c_void_p),
               ('name', ctypes.POINTER(_UnicodeString)), ('attributes', ctypes.c_uint32),
               ('security', ctypes.c_void_p), ('quality', ctypes.c_void_p)]


class _IoStatus(ctypes.Structure):
    _fields_ = [('status_or_pointer', ctypes.c_void_p), ('information', ctypes.c_size_t)]


class _WindowsApi:
    def __init__(self):
        _need(os.name == 'nt', 'platform')
        _need(ctypes.sizeof(_Information) == 52, 'abi')
        self.dll = ctypes.WinDLL('kernel32', use_last_error=True)
        self.nt = ctypes.WinDLL('ntdll', use_last_error=True)
        _need(hasattr(self.nt, 'NtCreateFile'), 'atomic_directory_api_unavailable')
        handle, dword = ctypes.c_void_p, ctypes.c_uint32
        specs = {
            'CreateFileW': ([ctypes.c_wchar_p, dword, dword, ctypes.c_void_p, dword, dword, handle], handle),
            'GetFileType': ([handle], dword),
            'GetFileInformationByHandle': ([handle, ctypes.POINTER(_Information)], ctypes.c_int),
            'GetVolumeInformationByHandleW': ([handle, ctypes.c_wchar_p, dword,
                ctypes.POINTER(dword), ctypes.POINTER(dword), ctypes.POINTER(dword),
                ctypes.c_wchar_p, dword], ctypes.c_int),
            'CloseHandle': ([handle], ctypes.c_int),
        }
        for name, (arguments, result) in specs.items():
            function = getattr(self.dll, name)
            function.argtypes, function.restype = arguments, result
        self.nt.NtCreateFile.argtypes = [ctypes.POINTER(handle), dword,
            ctypes.POINTER(_ObjectAttributes), ctypes.POINTER(_IoStatus), ctypes.c_void_p,
            dword, dword, dword, dword, ctypes.c_void_p, dword]
        self.nt.NtCreateFile.restype = ctypes.c_int32

    def open(self, path):
        # LIST_DIRECTORY|TRAVERSE|READ_ATTRIBUTES|SYNCHRONIZE engages sharing
        # enforcement. Metadata-only READ_ATTRIBUTES does not fence rename.
        value = self.dll.CreateFileW(str(path), 0x1000a1, 3, None, 3, 0x02200000, None)
        _need(value not in (None, 0, ctypes.c_void_p(-1).value), 'open')
        return int(value)

    def create(self, path, parent_handle):
        # One literal child relative to the already-held directory object.
        # FILE_CREATE refuses an existing name; no full-path redirect or reopen.
        buffer = ctypes.create_unicode_buffer(path.name)
        count = len(path.name.encode('utf-16-le'))
        _need(0 < count <= 65532, 'path')
        name = _UnicodeString(count, count + 2, ctypes.cast(buffer, ctypes.c_wchar_p))
        attributes = _ObjectAttributes(ctypes.sizeof(_ObjectAttributes), parent_handle,
            ctypes.pointer(name), 0x40, None, None)
        io = _IoStatus()
        handle = ctypes.c_void_p()
        status = self.nt.NtCreateFile(ctypes.byref(handle), 0x1000a1,
            ctypes.byref(attributes), ctypes.byref(io), None, 0x10, 3, 2,
            1 | 0x20, None, 0)
        _need(status >= 0 and handle.value not in (None, 0, ctypes.c_void_p(-1).value), 'create')
        if io.information != 2:  # FILE_CREATED; never accept opened/superseded.
            known = self.close(handle.value)
            raise NativeRefused('create', cleanup_known=known is True)
        return int(handle.value)

    def information(self, handle):
        _need(self.dll.GetFileType(handle) == 1, 'metadata')
        value = _Information()
        _need(self.dll.GetFileInformationByHandle(handle, ctypes.byref(value)), 'metadata')
        _need(value.attributes & 0x10 and not value.attributes & 0x400, 'directory')
        name = ctypes.create_unicode_buffer(64)
        _need(self.dll.GetVolumeInformationByHandleW(handle, None, 0, None, None, None,
              name, len(name)) and name.value == 'NTFS', 'filesystem')
        return dict(volume_serial=int(value.volume),
                    file_index=(int(value.index_high) << 32) | int(value.index_low),
                    creation_filetime=(int(value.creation.high) << 32) | int(value.creation.low))

    def close(self, handle):
        return bool(self.dll.CloseHandle(handle))


class DirectoryFence:
    """Hold ordinary D: ancestors and atomically-created children until close.

    No-delete sharing prevents ordinary rename/removal while held; child file IO
    remains permitted. This is not protection from privileged kernel/admin action.
    Every acquired handle is closed at most once, including after a close fault.
    """
    def __init__(self):
        self._api = _WindowsApi()
        self._entries = []
        self._closed = False
        self._close_failed = False

    def _add(self, path, handle):
        _need(type(handle) is int and handle > 0 and
              not any(e['handle'] == handle and not e['attempted'] for e in self._entries), 'handle')
        entry = dict(path=path, handle=handle, attempted=False, closed=False, identity=None)
        self._entries.append(entry)
        _ordinary(path)
        entry['identity'] = self._api.information(handle)
        return entry

    def hold(self, value):
        _need(not self._closed, 'closed')
        path = _path(value)
        for ancestor in reversed([path] + list(path.parents)):
            if any(e['path'] == ancestor for e in self._entries):
                continue
            _ordinary(ancestor)
            self._add(ancestor, self._api.open(ancestor))
        self.verify()
        return True

    def create(self, value):
        _need(not self._closed, 'closed')
        path = _path(value)
        self.hold(path.parent)
        # Never test exists then adopt: only atomic CREATE may produce this handle.
        parent = next(e for e in self._entries if e['path'] == path.parent)
        entry = self._add(path, self._api.create(path, parent['handle']))
        self.verify()
        return dict(entry['identity'])

    def verify(self):
        _need(not self._closed, 'closed')
        for entry in self._entries:
            _ordinary(entry['path'])
            _need(self._api.information(entry['handle']) == entry['identity'], 'identity')
            probe = self._api.open(entry['path'])
            try:
                _need(self._api.information(probe) == entry['identity'], 'identity')
            finally:
                try:
                    closed = self._api.close(probe) is True
                except BaseException:
                    closed = False
                if not closed:
                    self._close_failed = True
                    raise NativeRefused('close', cleanup_known=False)
        return True

    def close(self):
        self._closed = True
        for entry in reversed(self._entries):
            if not entry['attempted']:
                entry['attempted'] = True
                try:
                    entry['closed'] = self._api.close(entry['handle']) is True
                except BaseException:
                    entry['closed'] = False
                if not entry['closed']:
                    self._close_failed = True
        if self._close_failed:
            raise NativeRefused('close', cleanup_known=False)
        return True
