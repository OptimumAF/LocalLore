"""Strict optional wrapper-declared status metadata, never runtime authority.

CODE_0 is an error-callback observation, not success. UNRECOGNIZED is not health.
No controller, file, SDK, device or model operation runs at import.
Copyright 2026 LocalLore contributors. SPDX-License-Identifier: Apache-2.0
"""
from functools import lru_cache
import importlib.util
from pathlib import Path
import re

STATUS_KEY = "locallore_receipt_status_v1"
STATUS_CODE = 1340
PREFIX = "INSTRUMENTATION_STATUS: " + STATUS_KEY + "="
STATUS = "INSTRUMENTATION_STATUS_CODE: " + str(STATUS_CODE)
MAX_BYTES = 2048
MAX_COUNT = 1_000_000
EVENTS = tuple("CODE_" + str(code) for code in range(17)) + ("UNRECOGNIZED",)


@lru_cache(maxsize=1)
def _controller():
    spec = importlib.util.spec_from_file_location("status_trace_receipt_controller",
        Path(__file__).resolve().with_name("receipt_setup_qualification.py"))
    q = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(q)
    return q


def parse_status_trace(rawbytes):
    """Decode independent finite counts without reclassifying any outcome."""
    assert type(rawbytes) is bytes and 0 < len(rawbytes) <= MAX_BYTES - len(PREFIX.encode("ascii"))
    assert all(32 <= byte <= 126 for byte in rawbytes)
    value = _controller().contract.strict_json(rawbytes)
    assert type(value) is dict and set(value) == {"version", "counts", "saturated"}
    assert type(value["version"]) is int and value["version"] == 1
    counts, saturated = value["counts"], value["saturated"]
    assert type(counts) is dict and set(counts) == set(EVENTS)
    assert all(type(count) is int and 0 <= count <= MAX_COUNT for count in counts.values())
    assert type(saturated) is list and all(type(event) is str and event in EVENTS for event in saturated)
    assert saturated == [event for event in EVENTS if event in saturated]
    assert all(counts[event] == MAX_COUNT for event in saturated)
    return value


def extract_status_trace(rawbytes):
    """Extract at most one exact failure record, leaving other channels separate."""
    text = _controller().normalized(rawbytes, 131072)
    lines = text.split("\n")
    positions = [index for index, line in enumerate(lines) if line.startswith(PREFIX)]
    codes = [index for index, line in enumerate(lines)
        if re.match(r"^[ \t]*INSTRUMENTATION_STATUS_CODE[ \t]*:", line)
        and re.search(r"(?<![0-9])\+?0*1340(?![0-9])", line)]
    if not positions and not codes:
        assert STATUS_KEY not in text
        return None
    assert len(positions) == len(codes) == 1 and codes[0] == positions[0] + 1
    assert lines[codes[0]] == STATUS and text.count(STATUS_KEY) == 1
    assert not re.search(r"^OK \([0-9]+ tests?\)$", text, re.MULTILINE)
    return parse_status_trace(lines[positions[0]][len(PREFIX):].encode("ascii"))
