"""Pinned, fail-stop SDK clients; importing this module performs no observation.

Copyright 2026 LocalLore contributors. SPDX-License-Identifier: Apache-2.0
"""
from __future__ import annotations

import copy
import hashlib
import json
import math
import os
from pathlib import Path
import re
import shlex
import stat
import time

try:
    from benchmarks import receipt_avd_environment as environment
    from benchmarks import runtime_spike as host
except ModuleNotFoundError:
    import receipt_avd_environment as environment
    import runtime_spike as host

MAX_CAPTURE = 262144
SERVER_CAP = 16384
FILE_CAP = 64 * 1024 * 1024
STATUSES = {"completed", "timeout", "cancelled", "output_limit", "spawn_failed", "cleanup_failed"}


class ClientRefused(RuntimeError):
    """Only fixed reasons, never child output, paths or exception text."""


def _require(condition, reason="client_guard"):
    if not condition:
        raise ClientRefused(reason)


def _integer(value, low=1, high=2**31 - 1):
    _require(type(value) is int and low <= value <= high)
    return value


def _seconds(value):
    _require(type(value) in (int, float) and math.isfinite(value) and 0 < value <= 180)
    return value


def _plain(path, directory=False, missing=False):
    path = Path(path)
    _require(path.is_absolute() and str(path) == os.path.abspath(str(path)))
    for part in (path, *path.parents):
        if missing and part == path:
            _require(not part.exists() and not part.is_symlink())
            continue
        info = part.lstat()
        _require(not stat.S_ISLNK(info.st_mode) and not getattr(info, "st_file_attributes", 0) & 0x400)
        _require(stat.S_ISDIR(info.st_mode) if part != path or directory else stat.S_ISREG(info.st_mode))
    return path


def _identity(info):
    return info.st_dev, info.st_ino, info.st_size, info.st_mtime_ns


def _file_pin(path):
    path = _plain(path)
    before = path.lstat()
    _require(0 < before.st_size <= FILE_CAP)
    digest = hashlib.sha256()
    with path.open("rb") as source:
        held = os.fstat(source.fileno())
        # Python's Windows path/descriptor ctime can use different fields. Compare
        # file identity across APIs, and each API's ctime against itself over time.
        _require(_identity(held) == _identity(before))
        remaining = before.st_size
        while remaining:
            block = source.read(min(65536, remaining))
            _require(bool(block))
            digest.update(block)
            remaining -= len(block)
        after_held = os.fstat(source.fileno())
        _require(source.read(1) == b"" and _identity(after_held) == _identity(before)
                 and after_held.st_ctime_ns == held.st_ctime_ns)
    _plain(path)
    after = path.lstat()
    _require(_identity(after) == _identity(before) and after.st_ctime_ns == before.st_ctime_ns)
    return (*_identity(before), before.st_ctime_ns), digest.hexdigest()


def _process(value):
    _require(type(value) is dict and set(value) == {"pid", "creation_filetime", "executable"})
    _integer(value["pid"])
    _integer(value["creation_filetime"], high=2**64 - 1)
    name = value["executable"]
    _require(type(name) is str and 0 < len(name) <= 32768 and not any(ord(c) < 32 for c in name))
    _require(Path(name).is_absolute())
    return copy.deepcopy(value)


def _same_executable(left, right):
    return os.path.normcase(os.path.abspath(left)) == os.path.normcase(os.path.abspath(right))


def _listeners(pid, rows):
    _require(type(rows) is list and 1 <= len(rows) <= 4)
    result = []
    for row in rows:
        _require(type(row) is dict and set(row) == {"address", "port", "pid"})
        _require(type(row["address"]) is str and row["address"] in ("127.0.0.1", "::1"))
        _require(type(row["port"]) is int and row["port"] == 5037)
        _require(type(row["pid"]) is int and row["pid"] == pid)
        result.append(dict(row))
    _require(len({(r["address"], r["port"], r["pid"]) for r in result}) == len(result))
    return sorted(result, key=lambda r: (r["address"], r["port"], r["pid"]))


def _server_pin(value):
    _require(type(value) is dict and set(value) == {"pid", "creation_filetime", "executable", "listeners", "adb_sha256"})
    process = _process({k: value[k] for k in ("pid", "creation_filetime", "executable")})
    _require(type(value["adb_sha256"]) is str and re.fullmatch("[0-9a-f]{64}", value["adb_sha256"]))
    return dict(process, listeners=_listeners(process["pid"], value["listeners"]), adb_sha256=value["adb_sha256"])


def _server_command(powershell):
    # No CIM time conversion: the native kernel observation supplies exact FILETIME.
    script = ("$ErrorActionPreference='Stop'; "
              "$l=@(Get-NetTCPConnection -LocalPort 5037 -State Listen -ErrorAction Stop); "
              "$ids=@($l.OwningProcess|Select-Object -Unique); "
              "if($ids.Count -ne 1){throw 'server_refused'}; "
              "[pscustomobject]@{pid=[int]$ids[0];listeners=@($l|ForEach-Object{"
              "[pscustomobject]@{address=$_.LocalAddress;port=[int]$_.LocalPort;pid=[int]$_.OwningProcess}})}"
              "|ConvertTo-Json -Depth 4 -Compress")
    return [str(powershell), "-NoLogo", "-NoProfile", "-NonInteractive", "-Command", script]


def _listener_json(raw):
    _require(type(raw) is bytes and 0 < len(raw) <= SERVER_CAP, "server_observation")
    def unique(pairs):
        result = {}
        for key, value in pairs:
            _require(key not in result, "server_observation")
            result[key] = value
        return result
    def constant(_):
        raise ClientRefused("server_observation")
    value = json.loads(raw.decode("utf-8"), object_pairs_hook=unique, parse_constant=constant)
    _require(type(value) is dict and set(value) == {"pid", "listeners"}, "server_observation")
    pid = _integer(value["pid"])
    return pid, _listeners(pid, value["listeners"])


def _result(result, cap):
    _require(type(result.status) is str and result.status in STATUSES)
    _require(type(result.stdout) is bytes and len(result.stdout) <= cap)
    _require(type(result.stderr_bytes) is int and 0 <= result.stderr_bytes <= cap - len(result.stdout))
    _require(type(result.cleanup_complete) is bool)
    _require(result.returncode is None or type(result.returncode) is int and -(2**31) <= result.returncode <= 2**32 - 1)
    return result


def _completed(result):
    _require(result.cleanup_complete is True and result.status == "completed" and
             type(result.returncode) is int and result.returncode == 0 and result.stderr_bytes == 0, "capture_failed")


def _snapshot(adb, powershell, capture):
    adb_before, ps_before = _file_pin(adb), _file_pin(powershell)
    pid, rows = _listener_json(capture(_server_command(powershell), "adb-server", 15, SERVER_CAP))
    process = _process(environment.process_identity(pid))
    _require(process["pid"] == pid and _same_executable(process["executable"], str(adb)), "server_observation")
    _require(_process(environment.process_identity(pid)) == process, "server_observation")
    _require(_file_pin(adb) == adb_before and _file_pin(powershell) == ps_before, "server_observation")
    return dict(process, listeners=rows, adb_sha256=adb_before[1])


def observe_server(adb: Path, powershell: Path) -> dict:
    """Observe only the existing loopback listener and its native process, without invoking ADB."""
    try:
        def capture(command, _label, seconds, cap):
            result = _result(host.run_process(command, request=b"", deadline=seconds, max_output=cap), cap)
            _completed(result)
            return result.stdout
        return _snapshot(Path(adb), Path(powershell), capture)
    except BaseException:
        raise ClientRefused("server_observation") from None


class SdkCapture:
    """A monotonic client/evidence owner. Any failed guard or capture permanently closes dispatch."""
    def __init__(self, directory: Path, seconds: int, adb: Path, powershell: Path,
                 server_pin: dict, launcher_pin: dict | None = None):
        self.clean = False
        self._failed = True
        self.count = 0
        self.target = None
        try:
            _require(type(seconds) is int and 0 < seconds <= 2**31 - 1)
            self.until = time.monotonic() + seconds
            self.adb_path, self.powershell = Path(adb), Path(powershell)
            self._server = _server_pin(server_pin)
            self._launcher = None if launcher_pin is None else _process(launcher_pin)
            self._adb_file, self._powershell_file = _file_pin(self.adb_path), _file_pin(self.powershell)
            _require(self._adb_file[1] == self._server["adb_sha256"] and
                     _same_executable(self._server["executable"], str(self.adb_path)), "server_changed")
            self.directory = _plain(directory, directory=True, missing=True)
            self.directory.mkdir(exist_ok=False)
            self._directory_id = self._directory_guard()
            self._target_id = None
            self._failed = False
            self.clean = True
        except BaseException:
            raise ClientRefused("client_guard") from None

    def _directory_guard(self):
        directory = _plain(self.directory, directory=True)
        info = directory.lstat()
        result = info.st_dev, info.st_ino
        if hasattr(self, "_directory_id"):
            _require(result == self._directory_id, "persistence_failed")
        return result

    def _guard(self):
        _require(self.clean is True and self._failed is False, "client_closed")
        _require(time.monotonic() < self.until, "client_deadline")
        self._directory_guard()
        _require(_file_pin(self.adb_path) == self._adb_file and
                 _file_pin(self.powershell) == self._powershell_file, "server_changed")
        if self._launcher is not None:
            _require(_process(environment.process_identity(self._launcher["pid"])) == self._launcher, "launcher_changed")

    def check_server(self) -> None:
        try:
            self._guard()
            current = _snapshot(self.adb_path, self.powershell, self.capture)
            _require(current == self._server, "server_changed")
            self._guard()
        except BaseException:
            self.clean = False
            self._failed = True
            raise ClientRefused("server_changed") from None

    def _command(self, command):
        _require(type(command) is list and 1 <= len(command) <= 128 and
                 all(type(x) is str and 0 < len(x) <= 32768 and "\x00" not in x for x in command))
        if command == _server_command(self.powershell):
            return False
        prefix = [str(self.adb_path), "-H", "127.0.0.1", "-P", "5037"]
        _require(command[:5] == prefix)
        operation = command[5:]
        if operation == ["devices", "-l"]:
            return True
        _require(len(operation) >= 3 and operation[0] == "-t")
        _require(type(self.target) is dict and "transport_id" in self.target)
        target = _integer(self.target["transport_id"])
        _require(operation[1] == str(target))
        if self._target_id is not None:
            _require(target == self._target_id)
        self._target_id = target
        verb = operation[2]
        _require(not verb.startswith("-") and verb not in
                 {"start-server", "kill-server", "server", "fork-server", "nodaemon", "host", "devices",
                  "connect", "disconnect", "pair", "mdns", "reconnect", "track-devices"})
        return True

    def _persist(self, result, label, stem):
        raw = stem.with_suffix(".stdout.bin")
        with raw.open("xb") as sink:
            remaining = memoryview(result.stdout)
            while remaining:
                count = sink.write(remaining)
                _require(type(count) is int and 0 < count <= len(remaining), "persistence_failed")
                remaining = remaining[count:]
            sink.flush()
            os.fsync(sink.fileno())
        environment.create_json(stem.with_suffix(".json"), {
            "version": 1, "index": self.count, "label": label, "status": result.status,
            "returncode": result.returncode, "cleanup_complete": result.cleanup_complete,
            "stdout_bytes": len(result.stdout), "stdout_sha256": hashlib.sha256(result.stdout).hexdigest(),
            "stderr_bytes": result.stderr_bytes,
        })
        self._directory_guard()

    def capture(self, command: list[str], label: str, seconds=15, cap=131072) -> bytes:
        try:
            self._guard()
            _require(type(label) is str and re.fullmatch("[a-z][a-z0-9_-]{0,47}", label))
            _seconds(seconds)
            _integer(cap, high=MAX_CAPTURE)
            sdk = self._command(command)
            if sdk:
                self.check_server()
            self._guard()
            remaining = self.until - time.monotonic()
            _require(remaining > 0, "client_deadline")
            self.count += 1
            stem = self.directory / ("command-%04d" % self.count)
            try:
                result = _result(host.run_process(command, request=b"", deadline=min(seconds, remaining), max_output=cap), cap)
            except BaseException:
                # No ownership/result proof is available; retain a fixed failure record and stop.
                result = host.ProcessResult("spawn_failed", 0, cleanup_complete=False)
                self._persist(result, label, stem)
                raise ClientRefused("capture_failed") from None
            self._persist(result, label, stem)
            _completed(result)
            self._guard()
            if sdk:
                self.check_server()
            return result.stdout
        except BaseException:
            self.clean = False
            self._failed = True
            raise ClientRefused("capture_failed") from None

    def adb(self, operation: list[str], label: str, seconds=15, cap=131072) -> bytes:
        try:
            _require(type(self.target) is dict and "transport_id" in self.target)
            target = _integer(self.target["transport_id"])
            _require(type(operation) is list and bool(operation))
            return self.capture([str(self.adb_path), "-H", "127.0.0.1", "-P", "5037", "-t", str(target), *operation], label, seconds, cap)
        except BaseException:
            self.clean = False
            self._failed = True
            raise ClientRefused("capture_failed") from None

    def shell(self, op: list[str], label: str, seconds=15, cap=131072) -> bytes:
        try:
            _require(type(op) is list and bool(op) and all(type(x) is str and "\x00" not in x for x in op))
            return self.adb(["shell", shlex.join(op)], label, seconds, cap)
        except BaseException:
            self.clean = False
            self._failed = True
            raise ClientRefused("capture_failed") from None
