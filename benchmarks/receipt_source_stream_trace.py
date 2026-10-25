"""Passive host stream observations only; no IO, transfer or source authority.

Copyright 2026 LocalLore contributors. SPDX-License-Identifier: Apache-2.0
"""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
import json
import threading
import time

PREFIX = "LOCALLORE_RECEIPT_SOURCE_STREAM_V1="
MAX_BYTES = 1024  # Complete prefix plus printable ASCII JSON, excluding newline.
MAX_CAPTURE = 4096
MAX_EXPECTED_BYTES = 16 * 1024 * 1024 * 1024
MAX_CLIENT_MS = 150_000
MAX_ELAPSED_MS = 180_000
_KEYS = {"version", "phase", "expected_bytes", "source_verified", "client_timeout_ms",
         "client_returncode", "client_timed_out", "source_position", "elapsed_ms", "time_saturated"}


class StreamPhase(str, Enum):
    GATE = "GATE"
    SOURCE_OPEN = "SOURCE_OPEN"
    SOURCE_HASH = "SOURCE_HASH"
    CLIENT = "CLIENT"
    SOURCE_POSTCHECK = "SOURCE_POSTCHECK"
    LEASE_POSTCHECK = "LEASE_POSTCHECK"
    COMPLETE = "COMPLETE"


class SourceStreamTraceRefused(ValueError):
    def __init__(self):
        super().__init__("source_stream_trace_invalid")


def _require(condition):
    if not condition:
        raise SourceStreamTraceRefused()


def _integer(value, low, high):
    _require(type(value) is int and low <= value <= high)


def _validate(value):
    _require(type(value) is dict and set(value) == _KEYS)
    _require(type(value["version"]) is int and value["version"] == 1)
    _require(type(value["phase"]) is str and value["phase"] in {phase.value for phase in StreamPhase})
    _integer(value["expected_bytes"], 1, MAX_EXPECTED_BYTES)
    _require(type(value["source_verified"]) is bool and type(value["client_timed_out"]) is bool)
    _integer(value["client_timeout_ms"], 0, MAX_CLIENT_MS)
    code = value["client_returncode"]
    if code is not None:
        _integer(code, -(1 << 31), (1 << 31) - 1)
    _require(not (code is not None and value["client_timed_out"]))
    if value["client_timeout_ms"] == 0:
        _require(code is None and not value["client_timed_out"])
    else:
        _require(value["source_verified"])
    position = value["source_position"]
    if position is not None:
        _integer(position, 0, value["expected_bytes"])
    _integer(value["elapsed_ms"], 0, MAX_ELAPSED_MS)
    _require(type(value["time_saturated"]) is bool)
    _require(not value["time_saturated"] or value["elapsed_ms"] == MAX_ELAPSED_MS)
    return value


@dataclass(frozen=True)
class SourceStreamSnapshot:
    phase: StreamPhase
    expected_bytes: int
    source_verified: bool = False
    client_timeout_ms: int = 0
    client_returncode: int | None = None
    client_timed_out: bool = False
    source_position: int | None = None
    elapsed_ms: int = 0
    time_saturated: bool = False

    def __post_init__(self):
        _require(type(self.phase) is StreamPhase)
        _validate(self.as_dict())

    def as_dict(self):
        return {"version": 1, "phase": self.phase.value, "expected_bytes": self.expected_bytes,
                "source_verified": self.source_verified, "client_timeout_ms": self.client_timeout_ms,
                "client_returncode": self.client_returncode, "client_timed_out": self.client_timed_out,
                "source_position": self.source_position, "elapsed_ms": self.elapsed_ms,
                "time_saturated": self.time_saturated}

    def json(self):
        payload = _validate(self.as_dict())
        failed = False
        try:
            value = json.dumps(payload, separators=(",", ":"), ensure_ascii=True, allow_nan=False)
        except Exception:
            failed = True
        if failed:
            raise SourceStreamTraceRefused()
        _require(len(PREFIX) + len(value) <= MAX_BYTES and all(32 <= ord(char) <= 126 for char in value))
        return value


class SourceStreamTrace:
    """Last ENTERED phase, not completed work. All observations are diagnostic.

    client_timeout_ms is the authorized client budget, not its duration. Position
    is a caller-sampled HOST held-FD cursor, not bytes delivered or verified at a
    destination. Root call sites guard every diagnostic, including clock/JSON
    failure, and alone decide whether to emit this optional failure-only record.
    """
    def __init__(self, expected_bytes, *, clock_ns=time.monotonic_ns):
        _integer(expected_bytes, 1, MAX_EXPECTED_BYTES)
        self._clock_ns = clock_ns
        self._started = self._clock()
        self._lock = threading.RLock()
        self._phase = StreamPhase.GATE
        self._expected = expected_bytes
        self._verified = False
        self._timeout = 0
        self._code = None
        self._timed_out = False
        self._position = None
        self._elapsed_ns = 0
        self._saturated = False

    def _clock(self):
        failed = False
        try:
            value = self._clock_ns()
        except Exception:
            failed = True
        if failed:
            raise SourceStreamTraceRefused()
        _require(type(value) is int)
        return value

    def phase(self, value):
        _require(type(value) is StreamPhase)
        with self._lock:
            self._phase = value

    def source_verified(self):
        with self._lock:
            self._verified = True

    def client_start(self, timeout_ms):
        _integer(timeout_ms, 1, MAX_CLIENT_MS)
        with self._lock:
            _require(self._verified and self._timeout == 0)
            self._phase = StreamPhase.CLIENT
            self._timeout = timeout_ms

    def client_return(self, code):
        _integer(code, -(1 << 31), (1 << 31) - 1)
        with self._lock:
            _require(self._timeout > 0 and self._code is None and not self._timed_out)
            self._code = code

    def client_timeout(self):
        with self._lock:
            _require(self._timeout > 0 and self._code is None and not self._timed_out)
            self._timed_out = True

    def position(self, value):
        _integer(value, 0, self._expected)
        with self._lock:
            self._position = value

    def snapshot(self):
        with self._lock:
            self._elapsed_ns = max(self._elapsed_ns, self._clock() - self._started, 0)
            cap = MAX_ELAPSED_MS * 1_000_000
            self._saturated = self._saturated or self._elapsed_ns > cap
            return SourceStreamSnapshot(self._phase, self._expected, self._verified, self._timeout,
                self._code, self._timed_out, self._position, min(self._elapsed_ns, cap) // 1_000_000,
                self._saturated)

    def json(self):
        return self.snapshot().json()


def parse_source_stream_trace(rawbytes):
    """Closed metadata decode, not remote-exit, success or cleanup classification."""
    _require(type(rawbytes) is bytes and 0 < len(rawbytes) <= MAX_BYTES - len(PREFIX))
    _require(all(32 <= char <= 126 for char in rawbytes))

    def pairs(entries):
        result = {}
        for key, value in entries:
            if key in result:
                raise ValueError()
            result[key] = value
        return result

    def constant(_):
        raise ValueError()

    failed = False
    try:
        value = json.loads(rawbytes.decode("ascii"), object_pairs_hook=pairs, parse_constant=constant)
    except (ValueError, UnicodeError, RecursionError):
        failed = True
    if failed:
        raise SourceStreamTraceRefused()
    return _validate(value)


def extract_source_stream_trace(rawbytes):
    """One exact line, with LF or CRLF; legacy outcome parsing stays separate."""
    _require(type(rawbytes) is bytes and len(rawbytes) <= MAX_CAPTURE)
    failed = False
    try:
        text = rawbytes.decode("ascii", "strict")
    except UnicodeError:
        failed = True
    if failed:
        raise SourceStreamTraceRefused()
    text = text.replace("\r\n", "\n")
    _require(all(char == "\n" or 32 <= ord(char) <= 126 for char in text))
    lines = text.split("\n")
    matches = [line for line in lines if line.startswith(PREFIX)]
    if not matches:
        _require(PREFIX[:-1] not in text)
        return None
    _require(len(matches) == 1 and text.count(PREFIX[:-1]) == 1)
    return parse_source_stream_trace(matches[0][len(PREFIX):].encode("ascii"))
