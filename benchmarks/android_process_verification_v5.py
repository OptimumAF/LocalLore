"""Fixed restart-profile closed replay and native observation consistency.

No process, socket, device, model or credential operation is performed here.
Copyright 2026 LocalLore contributors. SPDX-License-Identifier: Apache-2.0
"""
import copy
import re

from benchmarks import android_process_verification_v4 as shared
from benchmarks import original_author_model_proof as author
from benchmarks import owned_restart_contract as c

PROBE_PROTOCOL = 'android-author-process-probe-v1'
PROBE_KEYS = frozenset((
    'version', 'protocol', 'mode', 'boot_id', 'pid', 'expected_uid',
    'observed_uid', 'start_ticks', 'state', 'pidfd_opened', 'poll_revents',
    'pidfd_closed', 'proc_opened', 'proc_closed', 'error', 'errno',
))
PROBE_ERRORS = frozenset((
    'pidfd_unsupported', 'pidfd_permission', 'proc_permission', 'proc_race',
    'uid_mismatch', 'io', 'close', 'malformed',
))


def validate_probe_packet(raw):
    """Retain a complete refused packet as data; never promote it to absence."""
    try:
        value = author._json(raw, 4096)
        c._obj(value, PROBE_KEYS)
        c._int(value['version'], 1, 1)
        c._need(value['protocol'] == PROBE_PROTOCOL, 'probe')
        c._need(value['mode'] in ('boot', 'snapshot') and
                value['state'] in ('boot', 'alive', 'exited', 'absent', 'refused'), 'probe')
        if value['boot_id'] is not None:
            c._need(type(value['boot_id']) is str and re.fullmatch(
                r'[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}', value['boot_id']) is not None, 'probe')
        if value['mode'] == 'boot':
            c._need(all(value[k] is None for k in ('pid', 'expected_uid', 'observed_uid', 'start_ticks')), 'probe')
        else:
            c._int(value['pid'], 1, 2**31-1, 'probe')
            c._int(value['expected_uid'], 10000, 2**31-1, 'probe')
        if value['observed_uid'] is not None:
            c._int(value['observed_uid'], 0, 2**31-1, 'probe')
        if value['start_ticks'] is not None:
            c._int(value['start_ticks'], 1, 2**63-1, 'probe')
        c._int(value['errno'], 0, 4095, 'probe')
        for opened, closed in (('pidfd_opened', 'pidfd_closed'), ('proc_opened', 'proc_closed')):
            c._need(type(value[opened]) is bool and
                    (value[closed] is None or type(value[closed]) is bool), 'probe')
            c._need(value[opened] or value[closed] is None, 'probe')
        if value['poll_revents'] is not None:
            c._int(value['poll_revents'], 0, 65535, 'probe')
        c._need(value['pidfd_opened'] or value['poll_revents'] is None, 'probe')
        if value['state'] == 'refused':
            c._need(value['error'] in PROBE_ERRORS, 'probe')
        else:
            c._need(value['boot_id'] is not None and value['error'] is None, 'probe')
            if value['state'] == 'boot':
                c._need(value['mode'] == 'boot' and value['errno'] == 0 and
                        value['pidfd_opened'] is value['proc_opened'] is False and
                        value['poll_revents'] is value['pidfd_closed'] is value['proc_closed'] is None, 'probe')
            elif value['state'] == 'absent':
                c._need(value['mode'] == 'snapshot' and value['errno'] == 3 and
                        value['observed_uid'] is value['start_ticks'] is None and
                        value['pidfd_opened'] is False and value['poll_revents'] is value['pidfd_closed'] is None and
                        (value['proc_opened'] is False and value['proc_closed'] is None or
                         value['proc_opened'] is True and value['proc_closed'] is True), 'probe')
            else:
                c._need(value['mode'] == 'snapshot' and value['errno'] == 0 and
                        value['observed_uid'] == value['expected_uid'] and value['start_ticks'] is not None and
                        value['pidfd_opened'] is value['pidfd_closed'] is value['proc_opened'] is value['proc_closed'] is True,
                        'probe')
                c._need(value['poll_revents'] == 0 if value['state'] == 'alive' else
                        value['poll_revents'] in (1, 16, 17), 'probe')
        return copy.deepcopy(value)
    except c.TargetRefused:
        raise
    except (author.ProofRefused, ValueError, TypeError, KeyError, UnicodeError, OverflowError, RecursionError):
        raise c.TargetRefused('probe') from None


def parse_probe(raw, mode, pid=None, uid=None):
    value = validate_probe_packet(raw)
    c._need(value['state'] != 'refused' and value['mode'] == mode, 'probe')
    c._need((mode == 'boot' and pid is uid is None) or
            (mode == 'snapshot' and type(pid) is type(uid) is int and
             value['pid'] == pid and value['expected_uid'] == uid), 'probe')
    return value


def verify_proof(pin, session, context):
    return shared._verify_proof(c, pin, session, context)


def verify_client_record(binding, session, admission):
    return shared._verify_client_record(c, binding, session, admission)


def require_current_clients(root, count, session_binding, admission):
    return shared._require_current_clients(c, root, count, session_binding, admission)


def verify_owned_target_result(*args, **kwargs):
    return shared._verify_owned_target_result(c, *args, **kwargs)
