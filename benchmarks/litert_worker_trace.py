"""Strict passive worker observations; never a success or resource-ownership gate.

No controller, file, device or model operation runs at import. Counter snapshots
are independent historical observations, not a jointly consistent lifecycle.
Copyright 2026 LocalLore contributors. SPDX-License-Identifier: Apache-2.0
"""
from functools import lru_cache
import importlib.util
from pathlib import Path
import re

STATUS_KEY = "locallore_receipt_worker_v1"
STATUS_CODE = 1337
PREFIX = "INSTRUMENTATION_STATUS: " + STATUS_KEY + "="
STATUS = "INSTRUMENTATION_STATUS_CODE: " + str(STATUS_CODE)
MAX_BYTES = 4096
MAX_COUNT = 1_000_000
EVENTS = (
    "ADMISSION_ENTERED", "ADMISSION_RETURNED", "ENGINE_CREATE_ENTERED", "ENGINE_CREATE_RETURNED",
    "INITIALIZE_ADMISSION_ENTERED", "INITIALIZE_ADMISSION_RETURNED", "INITIALIZE_ENTERED", "INITIALIZE_RETURNED",
    "ROLE_ADMISSION_ENTERED", "ROLE_ADMISSION_RETURNED", "CONVERSATION_CREATE_ENTERED", "CONVERSATION_CREATE_RETURNED",
    "SEND_ADMISSION_ENTERED", "SEND_ADMISSION_RETURNED", "SEND_ENTERED", "SEND_RETURNED", "MESSAGE_ENTERED", "MESSAGE_RETURNED",
    "DONE_ENTERED", "DONE_RETURNED", "ERROR_ENTERED", "ERROR_RETURNED", "DRAIN_SETTLED", "CANCEL_ENTERED", "CANCEL_RETURNED",
    "CONVERSATION_CLOSE_ENTERED", "CONVERSATION_CLOSE_KNOWN", "ENGINE_CLOSE_ENTERED", "ENGINE_CLOSE_KNOWN", "UNCERTAIN",
)


@lru_cache(maxsize=1)
def _controller():
    # Load the exact sibling only when parsing/persisting, never as an import action.
    spec = importlib.util.spec_from_file_location("worker_trace_receipt_controller",
        Path(__file__).resolve().with_name("receipt_setup_qualification.py"))
    q = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(q)
    return q


def parse_worker_trace(rawbytes):
    """Decode only the finite wire vocabulary; no cross-counter inference."""
    assert type(rawbytes) is bytes and 0 < len(rawbytes) <= MAX_BYTES - len(PREFIX.encode("ascii"))
    assert all(32 <= byte <= 126 for byte in rawbytes)
    q = _controller()
    value = q.contract.strict_json(rawbytes)
    assert type(value) is dict and set(value) == {"version", "counts", "saturated"}
    assert type(value["version"]) is int and value["version"] == 1
    counts, saturated = value["counts"], value["saturated"]
    assert type(counts) is dict and set(counts) == set(EVENTS)
    assert all(type(count) is int and 0 <= count <= MAX_COUNT for count in counts.values())
    assert type(saturated) is list and all(type(event) is str and event in EVENTS for event in saturated)
    # An exact hit at MAX_COUNT need not mean overflow. Overflow flags must be
    # unique, in declared order, and refer only to counters at the bound.
    assert saturated == [event for event in EVENTS if event in saturated]
    assert all(counts[event] == MAX_COUNT for event in saturated)
    return value


def extract_worker_trace(rawbytes):
    q = _controller()
    text = q.normalized(rawbytes, 131072)
    lines = text.split("\n")
    positions = [index for index, line in enumerate(lines) if line.startswith(PREFIX)]
    # Include malformed spellings mentioning this code so a second disguised
    # 1337 cannot hide beside the one exact record. Unrelated runner codes stay
    # subject to the caller's unchanged runner parser.
    codes = [index for index, line in enumerate(lines)
             if re.match(r"^[ \t]*INSTRUMENTATION_STATUS_CODE[ \t]*:", line)
             and re.search(r"(?<![0-9])\+?0*1337(?![0-9])", line)]
    if not positions and not codes:
        assert STATUS_KEY not in text
        return None
    assert len(positions) == len(codes) == 1 and codes[0] == positions[0] + 1
    assert lines[codes[0]] == STATUS and text.count(STATUS_KEY) == 1
    assert not re.search(r"^OK \([0-9]+ tests?\)$", text, re.MULTILINE)
    return parse_worker_trace(lines[positions[0]][len(PREFIX):].encode("ascii"))


def observe_worker_trace(owner, raw, phase):
    """Persist PLAY diagnostics before the caller applies its original runner gate.

Other phases belong to the separate setup-failure channel, which shares 1337.
Only forbid this worker key there; never consume or reinterpret that channel.
Any persistence uncertainty propagates to the caller without later actions.
"""
    assert phase in ("SOURCE_PREFLIGHT", "IMPORT", "PLAY", "REOPEN")
    if phase != "PLAY":
        assert STATUS_KEY not in _controller().normalized(raw, 131072)
        return None
    value = extract_worker_trace(raw)
    if value is not None:
        _controller().write_json(owner.directory / "play-worker-trace-v1.json", value)
    return value
