"""Strict optional callback metadata, never outcome or resource authority.

Retained calls and counters are independent observations, not a lifecycle model.
No controller, file, SDK, device or model operation runs at import.
Copyright 2026 LocalLore contributors. SPDX-License-Identifier: Apache-2.0
"""
from functools import lru_cache
import importlib.util
from pathlib import Path
import re

STATUS_KEY = "locallore_receipt_callback_v1"
STATUS_CODE = 1339
PREFIX = "INSTRUMENTATION_STATUS: " + STATUS_KEY + "="
STATUS = "INSTRUMENTATION_STATUS_CODE: " + str(STATUS_CODE)
MAX_BYTES = 4096
MAX_COUNT = 1_000_000
MAX_CALLS = 3
EVENTS = ("OUTPUT_CHUNKS", "OUTPUT_BYTES", "DONE", "CANCELLED", "SDK_JNI", "OTHER")
CALL_KEYS = frozenset(("ordinal", "role", "context_tokens", "max_output_tokens", "prompt_bytes", "schema_bytes", "counts", "saturated"))


@lru_cache(maxsize=1)
def _controller():
    spec = importlib.util.spec_from_file_location("callback_trace_receipt_controller",
        Path(__file__).resolve().with_name("receipt_setup_qualification.py"))
    q = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(q)
    return q


def _integer(value, lower, upper):
    assert type(value) is int and lower <= value <= upper
    return value


def parse_callback_trace(rawbytes):
    """Decode finite noncontent data without inferring callback order or cleanup."""
    assert type(rawbytes) is bytes and 0 < len(rawbytes) <= MAX_BYTES - len(PREFIX.encode("ascii"))
    assert all(32 <= byte <= 126 for byte in rawbytes)
    value = _controller().contract.strict_json(rawbytes)
    assert type(value) is dict and set(value) == {"version", "requests", "requests_saturated", "calls"}
    assert type(value["version"]) is int and value["version"] == 1
    requests = _integer(value["requests"], 0, MAX_COUNT)
    assert type(value["requests_saturated"]) is bool and (not value["requests_saturated"] or requests == MAX_COUNT)
    calls = value["calls"]
    assert type(calls) is list and len(calls) == min(requests, MAX_CALLS)
    for ordinal, call in enumerate(calls, 1):
        assert type(call) is dict and set(call) == CALL_KEYS
        assert type(call["ordinal"]) is int and call["ordinal"] == ordinal
        assert type(call["role"]) is str and call["role"] in ("DIRECTOR", "NARRATOR")
        _integer(call["context_tokens"], 512, 4096)
        _integer(call["max_output_tokens"], 1, 350)
        prompt = _integer(call["prompt_bytes"], 0, 32768)
        schema = _integer(call["schema_bytes"], 2, 32768)
        assert prompt + schema <= 32768
        counts, saturated = call["counts"], call["saturated"]
        assert type(counts) is dict and set(counts) == set(EVENTS)
        assert all(type(count) is int and 0 <= count <= MAX_COUNT for count in counts.values())
        assert type(saturated) is list and all(type(event) is str and event in EVENTS for event in saturated)
        assert saturated == [event for event in EVENTS if event in saturated]
        assert all(counts[event] == MAX_COUNT for event in saturated)
    return value


def extract_callback_trace(rawbytes):
    """Extract one adjacent failure-only record, leaving other channels separate."""
    text = _controller().normalized(rawbytes, 131072)
    lines = text.split("\n")
    positions = [index for index, line in enumerate(lines) if line.startswith(PREFIX)]
    codes = [index for index, line in enumerate(lines)
        if re.match(r"^[ \t]*INSTRUMENTATION_STATUS_CODE[ \t]*:", line)
        and re.search(r"(?<![0-9])\+?0*1339(?![0-9])", line)]
    if not positions and not codes:
        assert STATUS_KEY not in text
        return None
    assert len(positions) == len(codes) == 1 and codes[0] == positions[0] + 1
    assert lines[codes[0]] == STATUS and text.count(STATUS_KEY) == 1
    assert not re.search(r"^OK \([0-9]+ tests?\)$", text, re.MULTILINE)
    return parse_callback_trace(lines[positions[0]][len(PREFIX):].encode("ascii"))
