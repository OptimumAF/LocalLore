"""Strict no-model phase-probe observations, never a process-exit cause diagnosis.

Copyright 2026 LocalLore contributors. SPDX-License-Identifier: Apache-2.0
"""
import re

from android_runtime_spike import strict_json

MAX_RAW = 16_384
MAX_INTEGER = 2 ** 31 - 1
BASE = {"version", "status", "error", "model_execution"}
COMPLETED = BASE | {"journal_valid", "checkpoint_count", "last_phase", "last_role",
                    "fresh_reader_process", "exit_history_available", "exit_records_examined",
                    "exit_instance_matches", "exit_instance_matched", "exit_reason", "exit_status"}


def _integer(value, minimum=0, maximum=MAX_INTEGER):
    return type(value) is int and minimum <= value <= maximum


def _valid(value):
    if (type(value) is not dict or not BASE <= set(value)
            or type(value["version"]) is not int or value["version"] != 1
            or value["model_execution"] is not False):
        return False
    if value["status"] == "error":
        return set(value) == BASE and value["error"] == "phase_probe_failed"
    if (value["status"] != "completed" or value["error"] != "none"
            or set(value) != COMPLETED or value["journal_valid"] is not True
            or not _integer(value["checkpoint_count"], 1, 2)
            or value["last_role"] != "none"
            or type(value["fresh_reader_process"]) is not bool):
        return False
    expected_phase = "probe_ready" if value["checkpoint_count"] == 1 else "probe_kill"
    if value["last_phase"] != expected_phase:
        return False
    if (type(value["exit_history_available"]) is not bool
            or type(value["exit_instance_matched"]) is not bool
            or not _integer(value["exit_records_examined"], 0, 16)
            or not _integer(value["exit_instance_matches"], 0, 16)
            or value["exit_instance_matches"] > value["exit_records_examined"]
            or not _integer(value["exit_reason"], -1)
            or not _integer(value["exit_status"], -1)):
        return False
    if not value["exit_history_available"] and (
            value["exit_records_examined"] != 0 or value["exit_instance_matches"] != 0):
        return False
    if value["exit_instance_matches"] == 1:
        return (value["exit_instance_matched"] is True
                and value["exit_history_available"] is True
                and value["exit_reason"] >= 0 and value["exit_status"] >= 0)
    return (value["exit_instance_matched"] is False
            and value["exit_reason"] == -1 and value["exit_status"] == -1)


def parse_result(raw):
    """Decode exactly one bounded terminal; caller retains raw before calling.

    Uniform LF or CRLF is framing only. No bytes from a journal, model or trace
    enter this schema. A valid observation can still lack an exit-instance match.
    """
    try:
        if type(raw) is not bytes or len(raw) > MAX_RAW:
            return None
        if b"\r" in raw:
            normalized = raw.replace(b"\r\n", b"\n")
            if b"\r" in normalized or normalized.replace(b"\n", b"\r\n") != raw:
                return None
            raw = normalized
        match = re.fullmatch(rb"INSTRUMENTATION_RESULT: phase_result=([^\n]*)\n"
                             rb"INSTRUMENTATION_CODE: -1\n?", raw)
        if match is None:
            return None
        value = strict_json(match[1])
        return dict(value) if _valid(value) else None
    except (ValueError, TypeError, KeyError, UnicodeError, OverflowError, RecursionError):
        return None


def journal_verified(value):
    """A fresh reader observed both deterministic checkpoints; not a cause claim."""
    return (_valid(value) and value["status"] == "completed"
            and value["checkpoint_count"] == 2 and value["last_phase"] == "probe_kill"
            and value["fresh_reader_process"] is True)


def control_passed(value):
    """Require one exact process-instance match in addition to the durable journal.

    OS reason/status remain observations. They do not diagnose another SDK exit.
    """
    return (journal_verified(value) and value["exit_history_available"] is True
            and value["exit_instance_matches"] == 1 and value["exit_instance_matched"] is True)
