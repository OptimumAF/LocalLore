"""Strict stopped-session SDK diagnostics; never canonical outcome or cause evidence.

Copyright 2026 LocalLore contributors. SPDX-License-Identifier: Apache-2.0
"""
import re

from android_runtime_spike import strict_json

MAX_RAW = 16384
PHASES = frozenset({"instrumentation_start", "terminal"} | {
    prefix + suffix for prefix in (
        "native_create", "native_submit", "native_prepare", "native_respond", "native_commit", "native_reopen",
        "model_create", "model_initialize", "model_close", "role_open", "role_start", "role_drain", "role_cancel", "role_close")
    for suffix in ("_before", "_after")})
BASE = {"version", "status", "error", "model_execution"}
COMPLETED = BASE | {"journal_valid", "checkpoint_count", "last_phase", "last_role", "fresh_reader_process",
    "exit_history_available", "exit_records_examined", "exit_instance_matches", "exit_instance_matched", "exit_reason", "exit_status"}


def _integer(value, minimum=0, maximum=2 ** 31 - 1):
    return type(value) is int and minimum <= value <= maximum


def valid(value):
    if (type(value) is not dict or not BASE <= set(value) or type(value['version']) is not int
            or value['version'] != 1 or value['model_execution'] is not False):
        return False
    if value['status'] == 'error':
        return set(value) == BASE and value['error'] == 'sdk_phase_read_failed'
    if (value['status'] != 'completed' or value['error'] != 'none' or set(value) != COMPLETED
            or value['journal_valid'] is not True or not _integer(value['checkpoint_count'], 1, 96)
            or type(value['last_phase']) is not str or value['last_phase'] not in PHASES
            or type(value['last_role']) is not str or value['last_role'] not in {'none', 'director', 'narrator'}
            or type(value['fresh_reader_process']) is not bool):
        return False
    generation = value['last_phase'].startswith(('role_', 'model_create_', 'model_initialize_', 'native_respond_'))
    if generation == (value['last_role'] == 'none'):
        return False
    if value['checkpoint_count'] == 1 and value['last_phase'] != 'instrumentation_start':
        return False
    if (type(value['exit_history_available']) is not bool or type(value['exit_instance_matched']) is not bool
            or not _integer(value['exit_records_examined'], 0, 16) or not _integer(value['exit_instance_matches'], 0, 16)
            or value['exit_instance_matches'] > value['exit_records_examined']
            or not _integer(value['exit_reason'], -1) or not _integer(value['exit_status'], -1)):
        return False
    if not value['exit_history_available'] and (value['exit_records_examined'] or value['exit_instance_matches']):
        return False
    if value['exit_instance_matches'] == 1:
        return (value['exit_instance_matched'] is True and value['exit_history_available'] is True
                and value['exit_reason'] >= 0 and value['exit_status'] >= 0)
    return value['exit_instance_matched'] is False and value['exit_reason'] == value['exit_status'] == -1


def parse_result(raw):
    """The caller retains complete raw bytes before calling; no identity is exported."""
    try:
        if type(raw) is not bytes or len(raw) > MAX_RAW:
            return None
        if b'\r' in raw:
            normalized = raw.replace(b'\r\n', b'\n')
            if b'\r' in normalized or normalized.replace(b'\n', b'\r\n') != raw:
                return None
            raw = normalized
        match = re.fullmatch(rb'INSTRUMENTATION_RESULT: sdk_phase_result=([^\n]*)\nINSTRUMENTATION_CODE: -1\n?', raw)
        if match is None:
            return None
        value = strict_json(match[1])
        return dict(value) if valid(value) else None
    except (ValueError, TypeError, KeyError, UnicodeError, OverflowError, RecursionError):
        return None


def journal_verified(value):
    return valid(value) and value['status'] == 'completed' and value['fresh_reader_process'] is True


def instance_matched(value):
    return journal_verified(value) and value['exit_instance_matched'] is True
