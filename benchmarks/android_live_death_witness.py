"""Strict consistency for a live Rust-workspace checkpoint and kernel witnesses.

These pure functions establish no SDK, process or filesystem authority. A fixed
closed reader must authenticate the original bytes, caller, command, ordering
and capture before using them. Legacy passive SDK5 records remain unchanged.
Copyright 2026 LocalLore contributors. SPDX-License-Identifier: Apache-2.0
"""
import copy
import json
import re

from benchmarks import android_process_verification_v5 as legacy
from benchmarks import original_author_model_proof as author

PACKAGE = 'org.locallore.app.litertverify'
CHECKPOINT_PROTOCOL = 'original-author-live-checkpoint-v1'
PROBE_PROTOCOL = 'android-author-process-probe-v2'
HOLD_NS = 120_000_000_000
MIN_FAULT_WINDOW_NS = 60_000_000_000
MAX_INTEGER = 2 ** 63 - 1
CHECKPOINT_KEYS = frozenset((
    'version', 'protocol', 'package', 'process', 'author_proof_sha256',
    'import_proof_sha256', 'catalog_sha256', 'snapshot_sha256',
    'workspace_open', 'model_owner_closed', 'pending',
    'ready_elapsed_ns', 'expires_elapsed_ns',
))
PROCESS_KEYS = frozenset(('pid', 'uid', 'start_elapsed_ms', 'start_ticks'))
PIN_KEYS = ('author_proof_sha256', 'import_proof_sha256', 'catalog_sha256', 'snapshot_sha256')
PROBE_KEYS = legacy.PROBE_KEYS | {'observed_boottime_ns'}
REASONS = frozenset(('malformed', 'shape', 'bounds', 'binding', 'identity',
                     'clock', 'lifetime', 'not_alive', 'not_dead', 'probe'))


class LiveDeathRefused(ValueError):
    """Fixed diagnostic categories; never echo raw evidence or private data."""
    def __init__(self, reason='malformed'):
        self.reason = reason if reason in REASONS else 'malformed'
        super().__init__(self.reason)


def _need(value, reason):
    if not value:
        raise LiveDeathRefused(reason)


def _integer(value, low=1, high=MAX_INTEGER):
    _need(type(value) is int and low <= value <= high, 'bounds')


def _object(value, keys):
    _need(type(value) is dict and set(value) == set(keys), 'shape')


def _hash(value):
    _need(type(value) is str and re.fullmatch('[0-9a-f]{64}', value) is not None, 'binding')


def _decoded(raw):
    _need(type(raw) is bytes, 'malformed')
    try:
        return author._json(raw, 8192)
    except (author.ProofRefused, ValueError, TypeError, UnicodeError, RecursionError):
        raise LiveDeathRefused('malformed') from None


def _checkpoint(value):
    _object(value, CHECKPOINT_KEYS)
    _need(type(value['version']) is int and value['version'] == 1 and
          value['protocol'] == CHECKPOINT_PROTOCOL and value['package'] == PACKAGE, 'binding')
    process = value['process']
    _object(process, PROCESS_KEYS)
    _integer(process['pid'], 1, 2 ** 31 - 1)
    _integer(process['uid'], 10000, 2 ** 31 - 1)
    _integer(process['start_elapsed_ms'])
    _integer(process['start_ticks'])
    for key in PIN_KEYS:
        _hash(value[key])
    _need(value['workspace_open'] is True and value['model_owner_closed'] is True and
          value['pending'] is False, 'lifetime')
    _integer(value['ready_elapsed_ns'], 1, MAX_INTEGER - HOLD_NS)
    _integer(value['expires_elapsed_ns'])
    _need(value['expires_elapsed_ns'] - value['ready_elapsed_ns'] == HOLD_NS and
          process['start_elapsed_ms'] * 1_000_000 <= value['ready_elapsed_ns'], 'clock')
    return value


def validate_checkpoint(raw, *, author_proof_sha256, import_proof_sha256,
                        expected_process, catalog_sha256, snapshot_sha256):
    """Join ready bytes to independently authenticated AUTHOR/baseline metadata."""
    value = _checkpoint(_decoded(raw))
    _object(expected_process, ('pid', 'uid', 'start_elapsed_ms'))
    for key in expected_process:
        _integer(expected_process[key])
        _need(value['process'][key] == expected_process[key], 'identity')
    expected = dict(author_proof_sha256=author_proof_sha256, import_proof_sha256=import_proof_sha256,
                    catalog_sha256=catalog_sha256, snapshot_sha256=snapshot_sha256)
    for key in PIN_KEYS:
        _hash(expected[key])
        _need(value[key] == expected[key], 'binding')
    return copy.deepcopy(value)


def parse_probe(raw):
    """Validate native v2 bytes, preserving the original v2 clock/protocol."""
    value = _decoded(raw)
    _object(value, PROBE_KEYS)
    _need(type(value['version']) is int and value['version'] == 2 and
          value['protocol'] == PROBE_PROTOCOL and value['mode'] == 'snapshot', 'probe')
    _integer(value['observed_boottime_ns'])
    semantic = {key: value[key] for key in legacy.PROBE_KEYS}
    semantic.update(version=1, protocol=legacy.PROBE_PROTOCOL)
    try:
        legacy.validate_probe_packet(json.dumps(semantic, separators=(',', ':')).encode('utf-8'))
    except (legacy.c.TargetRefused, ValueError, TypeError, RecursionError):
        raise LiveDeathRefused('probe') from None
    return copy.deepcopy(value)


def validate_before(checkpoint, raw_probe, expected_boot_id):
    """Refuse before any fault unless the exact instance is alive with time left."""
    selected = _checkpoint(checkpoint)
    value = parse_probe(raw_probe)
    process = selected['process']
    _need(value['state'] == 'alive', 'not_alive')
    _need(value['boot_id'] == expected_boot_id and value['pid'] == process['pid'] and
          value['expected_uid'] == process['uid'] and value['observed_uid'] == process['uid'] and
          value['start_ticks'] == process['start_ticks'], 'identity')
    _need(selected['ready_elapsed_ns'] <= value['observed_boottime_ns'] <=
          selected['expires_elapsed_ns'] - MIN_FAULT_WINDOW_NS, 'lifetime')
    return copy.deepcopy(value)


def validate_after(checkpoint, before, raw_probe):
    """Require a later gone/exited witness before the hold could expire normally."""
    _need(type(before) is dict, 'shape')
    try:
        prior_raw = json.dumps(before, separators=(',', ':')).encode('utf-8')
    except (ValueError, TypeError, RecursionError):
        raise LiveDeathRefused('malformed') from None
    prior = validate_before(checkpoint, prior_raw, before.get('boot_id'))
    value = parse_probe(raw_probe)
    _need(value['state'] in ('absent', 'exited'), 'not_dead')
    _need(value['boot_id'] == prior['boot_id'] and value['pid'] == prior['pid'] and
          value['expected_uid'] == prior['expected_uid'], 'identity')
    if value['state'] == 'exited':
        _need(value['start_ticks'] == prior['start_ticks'] and
              value['observed_uid'] == prior['observed_uid'], 'identity')
    _need(prior['observed_boottime_ns'] < value['observed_boottime_ns'] <
          checkpoint['expires_elapsed_ns'], 'lifetime')
    return copy.deepcopy(value)
