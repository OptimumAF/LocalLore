"""One read-only SDK diagnostic invocation after known original-process absence.

Copyright 2026 LocalLore contributors. SPDX-License-Identifier: Apache-2.0
"""
import re
import shlex

import android_cache_control as cache
import android_sdk_phase_result as decoder

# Dispatch stays disabled until the new readback-capable APK is qualified.
READBACK_APK_SHA256 = None

def _uid(client):
    raw = client.shell('run-as', cache.PACKAGE, 'id', '-u')
    match = re.fullmatch(rb'([1-9][0-9]{0,9})\r?\n?', raw)
    if match is None or int(match[1]) > 2 ** 31 - 1:
        raise cache._Failure('uid_identity_failed')
    return int(match[1])


def _absent(client, phase):
    client.stage = phase + '_absence'
    if cache._process(client, phase) is not None:
        raise cache._Failure('original_process_present')
    client.stage = phase + '_namespace'
    packet = client.raw(['shell', shlex.join(['ps', '-A', '-o', 'PID,NAME'])])
    raw = getattr(packet, 'stdout', None)
    if (packet.status != 'completed' or type(packet.returncode) is not int or packet.returncode != 0
            or type(raw) is not bytes or len(raw) > 16384):
        raise cache._Failure('process_namespace_failed')
    rows = raw.decode('ascii').splitlines()
    if not rows or rows[0].split() != ['PID', 'NAME']:
        raise cache._Failure('process_namespace_failed')
    for row in rows[1:]:
        fields = row.split()
        if len(fields) != 2 or not fields[0].isdigit():
            raise cache._Failure('process_namespace_failed')
        if fields[1] == cache.PACKAGE or fields[1].startswith(cache.PACKAGE + ':'):
            raise cache._Failure('original_process_present')


def read_phase(device, apk_sha, session_nonce, raw_sink):
    """No pre-stop, inference, model read, filesystem repair or generation retry.

    Caller performs fresh storage and preservation gates. raw_sink only retains
    this call's bytes privately; the device must retain raw command metadata too.
    """
    report = dict(version=1, scope='android_sdk_phase_readback', status='input_refused', result=None,
        failure_stage='none', cleanup_failure_stage='none', dispatched=False, raw_protocol_retained=False,
        clients_cleaned=False, process_absent=False, journal_verified=False, instance_matched=False)
    if (type(apk_sha) is not str or apk_sha != READBACK_APK_SHA256
            or type(session_nonce) is not str or re.fullmatch(r'[a-f0-9]{32}', session_nonce) is None
            or not callable(raw_sink)):
        report['failure_stage'] = 'input'
        return report
    client = cache._Client(device, apk_sha)
    dispatched = False; identity = None
    try:
        if not client.known():
            raise cache._Failure('client_cleanup_unknown')
        cache._package(client, 'initial')
        client.stage = 'initial_uid'; identity = _uid(client)
        _absent(client, 'initial')
        client.stage = 'read_phase'
        command = shlex.join(['am', 'instrument', '-w', '-r', '-e', 'operation', 'read_phase',
            '-e', 'session', session_nonce, cache.PACKAGE + '/' + cache.INSTRUMENTATION])
        dispatched = True; report['dispatched'] = True
        result = client.raw(['shell', command], deadline=45, retain_unclean=True)
        raw = getattr(result, 'stdout', None)
        if type(raw) is not bytes:
            raise cache._Failure('invalid_raw')
        client.stage = 'raw_retention'; raw_sink(raw); report['raw_protocol_retained'] = True
        if not client.known():
            raise cache._Failure('client_cleanup_unknown')
        client.stage = 'read_transport'
        if (len(raw) > decoder.MAX_RAW or result.status != 'completed'
                or type(result.returncode) is not int or result.returncode != 0):
            raise cache._Failure('read_transport_failed')
        client.stage = 'read_terminal'; observed = decoder.parse_result(raw)
        if observed is None:
            raise cache._Failure('read_terminal_failed')
        report['result'] = observed
        report['status'] = 'observed'
        report['journal_verified'] = decoder.journal_verified(observed)
        report['instance_matched'] = decoder.instance_matched(observed)
    except Exception:
        report['failure_stage'] = client.stage if client.stage != 'none' else 'initial_client_cleanup'
    finally:
        if dispatched and client.known():
            try:
                cache._package(client, 'final')
                client.stage = 'final_uid'
                if _uid(client) != identity:
                    raise cache._Failure('uid_identity_changed')
                cache._stop(client, 'final', package_verified=True)
                _absent(client, 'final')
                report['process_absent'] = True
            except Exception:
                report['cleanup_failure_stage'] = client.stage
        elif dispatched:
            report['cleanup_failure_stage'] = 'client_cleanup_unknown'
        report['clients_cleaned'] = client.known()
        if not report['clients_cleaned'] or not report['process_absent']:
            report['journal_verified'] = report['instance_matched'] = False
    return report
