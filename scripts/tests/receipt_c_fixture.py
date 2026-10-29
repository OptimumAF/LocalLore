"""Explicit lexical-C test volume backed exclusively by fresh physical D IO.

This is scoped filesystem simulation, not a real C volume or an OS sandbox.
Drive labels, environment helpers, validators, hashes and verdicts are untouched.
Use only in serial tests: all contexts share narrowly patched Path IO methods.
"""
from contextlib import ExitStack
import hashlib
import os
from pathlib import Path, PureWindowsPath
import stat
from types import SimpleNamespace
from unittest.mock import patch


_RAW_LSTAT = Path.lstat
_RAW_INFO = getattr(Path, "info", None)
_IS_RESERVED = getattr(os.path, "isreserved", None)
_RAW = {name: getattr(Path, name) for name in (
    "open", "mkdir", "stat", "lstat", "exists", "is_file", "is_dir",
    "is_symlink", "iterdir", "resolve",
)}
_UNSUPPORTED = tuple(name for name in (
    "touch", "chmod", "lchmod", "unlink", "rmdir", "rename", "replace",
    "symlink_to", "hardlink_to", "link_to", "readlink", "glob", "rglob", "walk",
    "copy", "copy_into", "move", "move_into", "owner", "group", "is_mount",
    "is_junction", "is_block_device", "is_char_device", "is_fifo", "is_socket",
) if hasattr(Path, name))
_RAW.update({name: getattr(Path, name) for name in _UNSUPPORTED})
_VOLUMES = []
_PATCHES = None


def _refuse(reason="synthetic_c_scope"):
    raise ValueError(reason)


def _canonical(value, drive):
    path = Path(value)
    if _IS_RESERVED is not None:
        reserved = _IS_RESERVED(str(path))
    else:
        # isreserved arrived in Python 3.13. The older pure-path check is
        # lexical too, but checks only the last component on older runtimes.
        components = path.parts[1:]
        reserved = any(PureWindowsPath(part).is_reserved() or
                       part.endswith((".", " ")) or
                       any(ord(char) < 32 or char in ':*?"<>|' for char in part)
                       for part in components)
    if (not path.is_absolute() or path.drive.upper() != drive or
            str(path) != os.path.abspath(str(path)) or ".." in path.parts or
            reserved):
        _refuse()
    return path


def _physical_metadata(path):
    """Never resolve away a link; inspect each currently existing D ancestor."""
    path = _canonical(path, "D:")
    for part in (path, *path.parents):
        try:
            info = _RAW_LSTAT(part)
        except FileNotFoundError:
            continue
        if stat.S_ISLNK(info.st_mode) or getattr(info, "st_file_attributes", 0) & 0x400:
            _refuse("synthetic_c_backing")
    return path


def _route(path):
    path = Path(path)
    if path.drive.upper() == "C:":
        path = _canonical(path, "C:")
        for volume in _VOLUMES:
            if path.is_relative_to(volume.anchor):
                physical = volume.physical(path)
                return volume, physical, False
        if any(volume.anchor.is_relative_to(path) for volume in _VOLUMES):
            return None, None, True
        _refuse()
    # UNC/device namespaces must never fall through to a remote filesystem.
    if path.drive.startswith("\\") or path.root.startswith("\\\\"):
        _refuse()
    return None, path, False


def _event(volume, operation, lexical, physical=None):
    if volume is not None:
        volume._events.append(dict(operation=operation, lexical=str(lexical), physical=str(physical)))


def _directory_metadata():
    # Explicit simulation above a volume anchor, never observed C metadata.
    return SimpleNamespace(st_mode=stat.S_IFDIR | 0o700, st_file_attributes=0,
                           st_size=0, st_ino=0, st_dev=0, st_nlink=1,
                           st_mtime_ns=0, st_ctime_ns=0)


def _metadata(name):
    def call(path, *args, **kwargs):
        volume, physical, ancestor = _route(path)
        if ancestor:
            if name in ("stat", "lstat"):
                return _directory_metadata()
            return name in ("exists", "is_dir")
        _event(volume, name, path, physical)
        return _RAW[name](physical, *args, **kwargs)
    return call


def _ordinary(name):
    def call(path, *args, **kwargs):
        volume, physical, ancestor = _route(path)
        if ancestor:
            _refuse("synthetic_c_unsupported")
        _event(volume, name, path, physical)
        return _RAW[name](physical, *args, **kwargs)
    return call


def _iterdir(path):
    volume, physical, ancestor = _route(path)
    if ancestor:
        _refuse("synthetic_c_unsupported")
    _event(volume, "iterdir", path, physical)
    for child in _RAW["iterdir"](physical):
        yield Path(path) / child.name if volume is not None else child


def _resolve(path, strict=False):
    volume, physical, ancestor = _route(path)
    if ancestor:
        return Path(path)
    resolved = _RAW["resolve"](physical, strict=strict)
    if volume is None:
        return resolved
    _physical_metadata(resolved)
    if not resolved.is_relative_to(volume.backing):
        _refuse()
    _event(volume, "resolve", path, physical)
    return volume.anchor / resolved.relative_to(volume.backing)


def _unsupported(name):
    def call(path, *args, **kwargs):
        candidates = (path, *args, *kwargs.values())
        for value in candidates:
            if isinstance(value, (str, os.PathLike)):
                selected = Path(value)
                if selected.drive.upper() == "C:" or selected.drive.startswith("\\"):
                    _refuse("synthetic_c_unsupported")
        return _RAW[name](path, *args, **kwargs)
    return call


def _path_info(path):
    # Python 3.14 PathInfo bypasses these method hooks and caches its results.
    # Do not manufacture cached C metadata or permit a real C/UNC lookup.
    selected = Path(path)
    if selected.drive.upper() == "C:" or selected.drive.startswith("\\"):
        _refuse("synthetic_c_unsupported")
    return _RAW_INFO.__get__(path, type(path))


def _install():
    global _PATCHES
    stack = ExitStack()
    try:
        for name in ("stat", "lstat", "exists", "is_file", "is_dir", "is_symlink"):
            stack.enter_context(patch.object(Path, name, new=_metadata(name)))
        for name in ("open", "mkdir"):
            stack.enter_context(patch.object(Path, name, new=_ordinary(name)))
        stack.enter_context(patch.object(Path, "iterdir", new=_iterdir))
        stack.enter_context(patch.object(Path, "resolve", new=_resolve))
        if _RAW_INFO is not None:
            stack.enter_context(patch.object(Path, "info", new=property(_path_info)))
        for name in _UNSUPPORTED:
            stack.enter_context(patch.object(Path, name, new=_unsupported(name)))
    except BaseException:
        stack.close()
        raise
    _PATCHES = stack


class SyntheticCVolume:
    """A single-use lexical C namespace with a disjoint, empty D backing."""

    def __init__(self, backing: Path):
        if os.name != "nt":
            _refuse("synthetic_c_platform")
        self.backing = _physical_metadata(backing)
        label = hashlib.sha256(str(self.backing).casefold().encode("utf-8")).hexdigest()[:20]
        self.anchor = Path("C:/__locallore_test__") / ("volume-" + label)
        self.root = self.anchor / "new-avd"
        self._state = "new"
        self._events = []

    @property
    def io_events(self):
        return [dict(item) for item in self._events]

    def physical(self, path):
        selected = _canonical(path, "C:")
        if not selected.is_relative_to(self.anchor):
            _refuse()
        physical = self.backing / selected.relative_to(self.anchor)
        return _physical_metadata(physical)

    def __enter__(self):
        global _PATCHES
        if self._state != "new":
            _refuse("synthetic_c_lifecycle")
        for volume in _VOLUMES:
            if (self.backing.is_relative_to(volume.backing) or
                    volume.backing.is_relative_to(self.backing)):
                _refuse("synthetic_c_overlap")
        _physical_metadata(self.backing)
        try:
            info = _RAW_LSTAT(self.backing)
        except FileNotFoundError:
            _RAW["mkdir"](self.backing)
        else:
            if not stat.S_ISDIR(info.st_mode) or any(_RAW["iterdir"](self.backing)):
                _refuse("synthetic_c_backing")
        if not _VOLUMES:
            _install()
        _VOLUMES.append(self)
        self._state = "active"
        return self

    def __exit__(self, exc_type, exc, traceback):
        global _PATCHES
        if self._state != "active":
            _refuse("synthetic_c_lifecycle")
        _VOLUMES.remove(self)
        self._state = "closed"
        if not _VOLUMES:
            stack, _PATCHES = _PATCHES, None
            stack.close()
        return False
