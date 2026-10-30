"""Bounded, read-only held server roster; no import-time filesystem/network IO.

Rows are untrusted private server metadata, never phone identity or authority.
Recorded consistency alone cannot authenticate acquisition or OS ownership.
Copyright 2026 LocalLore contributors. SPDX-License-Identifier: Apache-2.0
"""
import copy
import json
import re

from benchmarks import adb_held_socket as old

PROTOCOL = 'adb-held-device-roster-v1'
REQUEST = b'000Ehost:devices-l'
MAX_SECONDS = 3.0
MAX_BODY = 65535
MAX_RESPONSE = 65543
MAX_ROWS = 256
MAX_REPORT = 2 * 1024 * 1024
REPORT_KEYS = old.REPORT_KEYS | {'version_proof', 'rows'}
REASONS = old.REASONS | {'version', 'devices'}
ROW_KEYS = frozenset(('serial', 'state', 'devpath', 'product', 'model', 'device', 'transport_id'))
STATES = ('offline', 'bootloader', 'device', 'host', 'recovery', 'rescue', 'sideload',
          'unauthorized', 'authorizing', 'connecting', 'detached', 'any')
NO_PERMISSIONS = re.compile(r'^no permissions(?: \([^\r\n]*\))?; see \[http://developer\.android\.com/tools/device\.html\]')


class RosterRefused(ValueError):
    def __init__(self, reason='devices'):
        self.reason = reason if type(reason) is str and reason in REASONS else 'backend'
        super().__init__(self.reason)


class ReceiveRefused(old.ProbeRefused):
    """A bounded private byte channel after IO, never an accepted response."""
    def __init__(self, reason, received):
        old._need(type(received) is bytes and len(received) <= MAX_RESPONSE+1, 'framing')
        self.received = received
        super().__init__(reason)


def _need(value, reason='devices'):
    if not value:
        raise RosterRefused(reason)


def _same(left, right):
    if type(left) is not type(right):
        return False
    if type(left) is dict:
        return left.keys() == right.keys() and all(_same(left[k], right[k]) for k in left)
    if type(left) is list:
        return len(left) == len(right) and all(_same(a, b) for a, b in zip(left, right))
    return left == right


def validate_admission(value):
    try:
        old._obj(value, ('version', 'protocol', 'server', 'adb_file', 'candidates', 'expected_version'), 'admission')
        _need(value['protocol'] == PROTOCOL, 'admission')
        translated = copy.deepcopy(value)
        translated['protocol'] = old.PROTOCOL
        old.validate_admission(translated)
        return copy.deepcopy(value)
    except old.ProbeRefused:
        raise RosterRefused('admission') from None


def backend_admission(value):
    translated = validate_admission(value)
    translated['protocol'] = old.PROTOCOL
    return translated


def _scalar(value, cap):
    _need(type(value) is str and 0 < len(value.encode('utf-8')) <= cap)
    _need(not any(ord(c) < 32 or ord(c) == 127 for c in value))
    return value


def _state(rest):
    for word in STATES:
        if rest == word or rest.startswith(word + ' '):
            return word, rest[len(word):]
    match = NO_PERMISSIONS.match(rest)
    _need(match is not None and (match.end() == len(rest) or rest[match.end()] == ' '))
    return match.group(), rest[match.end():]


def _line(raw):
    # printf's width is bytes. Its unsanitized exotic strings are not universally
    # reversible; accept the bounded ordinary grammar and refuse ambiguity.
    _need(raw.count(b' transport_id:') == 1)
    match = re.fullmatch(rb'(.*) transport_id:([1-9][0-9]{0,19})', raw)
    _need(match is not None)
    identifier = int(match[2]); _need(identifier <= 2**64-1)
    prefix = match[1]
    candidates = []
    for offset, byte in enumerate(prefix):
        if byte != 32 or offset < 22:
            continue
        padded = prefix[:offset]
        serial_raw = padded.rstrip(b' ')
        if not serial_raw or padded != serial_raw + b' ' * max(0, 22-len(serial_raw)):
            continue
        serial = serial_raw.decode('utf-8')
        if serial != '(no serial number)' and any(c.isspace() for c in serial):
            continue
        rest = prefix[offset+1:].decode('utf-8')
        try:
            state, remainder = _state(rest)
        except RosterRefused:
            continue
        candidates.append((serial, state, remainder))
    _need(len(candidates) == 1)
    serial, state, remainder = candidates[0]
    _scalar(serial, 256); _scalar(state, 512)
    _need(not remainder or remainder.startswith(' '))
    text = remainder
    markers = list(re.finditer(r' (product|model|device):', text))
    keys = [m[1] for m in markers]
    order = {'product': 0, 'model': 1, 'device': 2}
    _need(len(keys) == len(set(keys)) and [order[k] for k in keys] == sorted(order[k] for k in keys))
    row = dict(serial=None if serial == '(no serial number)' else serial,
               state=state, devpath=None, product=None, model=None, device=None, transport_id=identifier)
    keyless = text[:markers[0].start()] if markers else text
    if keyless:
        _need(keyless.startswith(' '))
        row['devpath'] = _scalar(keyless[1:], 256)
    for index, marker in enumerate(markers):
        end = markers[index+1].start() if index+1 < len(markers) else len(text)
        value = _scalar(text[marker.end():end], 256)
        if marker[1] == 'model':
            _need(re.fullmatch('[A-Za-z0-9_]+', value) is not None)
        row[marker[1]] = value
    return row


def parse_devices(payload):
    """Decode bounded ordinary AOSP long rows; unsupported rows remain raw only."""
    try:
        _need(type(payload) is bytes and len(payload) <= MAX_BODY)
        if payload == b'':
            return []
        _need(payload.endswith(b'\n') and not any(b < 32 and b != 10 or b == 127 for b in payload))
        payload.decode('utf-8')  # Strict whole-body validation before any row.
        lines = payload[:-1].split(b'\n')
        _need(1 <= len(lines) <= MAX_ROWS and all(lines))
        rows = [_line(raw) for raw in lines]
        serials = [r['serial'] for r in rows if r['serial'] is not None]
        _need(len(serials) == len(set(serials)) and
              len({r['transport_id'] for r in rows}) == len(rows))
        return rows
    except (UnicodeError, OverflowError):
        raise RosterRefused('devices') from None


def _decode_response(raw):
    _need(type(raw) is bytes and 8 <= len(raw) <= MAX_RESPONSE, 'framing')
    _need(raw[:4] == b'OKAY' and re.fullmatch(b'[0-9a-fA-F]{4}', raw[4:8]) is not None, 'framing')
    _need(len(raw) == 8 + int(raw[4:8], 16), 'framing')
    return parse_devices(raw[8:])


def _selected_rows(snapshot, client_port=None):
    rows = old._record_rows(snapshot)
    allowed = {5037} if client_port is None else {5037, client_port}
    _need(all(row.local_port in allowed for row in rows), 'snapshot')
    return rows


def _version_verified(value, resource):
    if not old.report_verified(value, resource):
        return False
    try:
        first, connected, presend, _, final = value['stages']
        port = connected['endpoint']['local_port']
        _selected_rows(first['snapshot'])
        _selected_rows(presend['snapshot'], port)
        _selected_rows(final['snapshot'], port)
        return True
    except (ValueError, KeyError, TypeError, AttributeError):
        return False


def probe(backend, admission, version_proof):
    """One roster attempt after a complete version proof, no retries or fallback."""
    report = dict(version=1, protocol=PROTOCOL, feature_acceptance=False, admission=None,
        status='refused', reason='admission', stages=[], request_hex=REQUEST.hex(), request_sent=False,
        response_hex='', response_complete=False, ownership_verified=False, client_raw_state=None,
        elapsed_ms=0, socket_closed=False, process_handles_closed=False, version_proof=None, rows=None)
    started = last = None
    response = bytearray()
    try:
        admitted = validate_admission(admission); report['admission'] = admitted
        resource = backend_admission(admitted)
        _need(_version_verified(version_proof, resource), 'version')
        report['version_proof'] = copy.deepcopy(version_proof)
        prior_client = version_proof['stages'][0]['bracket']['client']
        started = last = old._now(backend); until = started + MAX_SECONDS
        def tick():
            nonlocal last
            current = old._now(backend)
            _need(last <= current < until, 'deadline'); last = current
        def call(name, *args):
            tick(); value = getattr(backend, name)(*copy.deepcopy(args), until); tick()
            return value
        call('open', resource)
        initial = old._bracket(call('bracket', resource), resource)
        rows, snapshot = old._snapshot(call('snapshot'))
        report['stages'].append(dict(stage='initial', bracket=initial, snapshot=snapshot))
        _need(_same(initial['client'], prior_client), 'identity')
        old._candidates(rows, resource)
        call('connect')
        endpoint = old._endpoint(call('endpoint'))
        report['stages'].append(dict(stage='connected', endpoint=endpoint))
        rows, snapshot = old._snapshot(call('snapshot'), endpoint)
        presend = dict(stage='presend', endpoint_before=endpoint, snapshot=snapshot)
        report['stages'].append(presend)
        presend['endpoint_after'] = old._endpoint(call('endpoint'), endpoint)
        presend['bracket'] = old._bracket(call('bracket', resource), resource, initial)
        old._candidates(rows, resource)
        report['client_raw_state'] = old._join(rows, endpoint, resource['server']['pid'], initial['client']['pid'])
        report['ownership_verified'] = True
        report['stages'].append(dict(stage='send_attempt'))
        call('send', REQUEST); report['request_sent'] = True
        while True:
            limit = MAX_RESPONSE + 1 - len(response)
            tick()
            try:
                part = backend.recv(limit, until)
            except ReceiveRefused as failure:
                # Actual owned IO can complete before a post-read clock/resource
                # refusal. Preserve its bounded bytes without accepting them.
                response.extend(failure.received[:limit])
                report['response_hex'] = response.hex()
                raise
            _need(type(part) is bytes, 'framing')
            response.extend(part[:limit]); report['response_hex'] = response.hex()
            _need(len(part) <= limit and len(response) <= MAX_RESPONSE, 'framing')
            tick()
            if not part:
                break
        report['rows'] = _decode_response(bytes(response)); report['response_complete'] = True
        final = dict(stage='final', endpoint=old._endpoint(call('endpoint'), endpoint),
                     bracket=old._bracket(call('bracket', resource), resource, initial))
        report['stages'].append(final)
        rows, final['snapshot'] = old._snapshot(call('snapshot'), endpoint)
        old._candidates(rows, resource)
        report['status'], report['reason'] = 'observed', None
    except BaseException as error:
        report['reason'] = (error.reason if isinstance(error, (RosterRefused, old.ProbeRefused)) else
                            'cancelled' if isinstance(error, (KeyboardInterrupt, InterruptedError)) else 'backend')
    finally:
        try:
            closed = backend.close()
            old._obj(closed, ('socket_closed', 'process_handles_closed'), 'cleanup')
            for key, value in closed.items():
                _need(type(value) is bool, 'cleanup'); report[key] = value
            _need(all(closed.values()), 'cleanup')
        except BaseException:
            report['status'], report['reason'] = 'refused', 'cleanup'
        if started is not None:
            try:
                current = old._now(backend); _need(current >= last, 'deadline')
                report['elapsed_ms'] = int((current-started)*1000)
                _need(current-started < MAX_SECONDS, 'deadline')
            except BaseException:
                report['status'], report['reason'] = 'refused', 'deadline'
    return report


def report_verified(value, expected_admission):
    """File-only consistency. Source/actual owner/terminal evidence is additional."""
    try:
        admitted = validate_admission(expected_admission); resource = backend_admission(admitted)
        old._obj(value, REPORT_KEYS, 'admission')
        _need(type(value['version']) is int and value['version'] == 1 and value['protocol'] == PROTOCOL and
              value['feature_acceptance'] is False and _same(validate_admission(value['admission']), admitted), 'admission')
        _need(value['status'] == 'observed' and value['reason'] is None and
              all(value[k] is True for k in ('request_sent', 'response_complete', 'ownership_verified',
                  'socket_closed', 'process_handles_closed')), 'backend')
        _need(_version_verified(value['version_proof'], resource), 'version')
        _need(value['request_hex'] == REQUEST.hex() and type(value['response_hex']) is str and
              len(value['response_hex']) <= MAX_RESPONSE*2 and
              re.fullmatch('(?:[0-9a-f]{2})*', value['response_hex']) is not None, 'framing')
        _need(_same(value['rows'], _decode_response(bytes.fromhex(value['response_hex']))))
        old._int(value['elapsed_ms'], 0, 2999, 'deadline')
        stages = value['stages']
        _need(type(stages) is list and len(stages) == 5 and
              [s.get('stage') for s in stages] == ['initial', 'connected', 'presend', 'send_attempt', 'final'], 'backend')
        first, connected, presend, sent, final = stages
        for stage, keys in ((first, ('stage', 'bracket', 'snapshot')), (connected, ('stage', 'endpoint')),
            (presend, ('stage', 'endpoint_before', 'endpoint_after', 'bracket', 'snapshot')),
            (sent, ('stage',)), (final, ('stage', 'endpoint', 'bracket', 'snapshot'))):
            old._obj(stage, keys, 'backend')
        bracket = old._bracket(first['bracket'], resource)
        _need(_same(bracket['client'], value['version_proof']['stages'][0]['bracket']['client']), 'identity')
        endpoint = old._endpoint(connected['endpoint'])
        for item in (presend['endpoint_before'], presend['endpoint_after'], final['endpoint']):
            old._endpoint(item, endpoint)
        for item in (presend['bracket'], final['bracket']):
            old._bracket(item, resource, bracket)
        for index, stage in enumerate((first, presend, final)):
            old._candidates(_selected_rows(stage['snapshot'], None if index == 0 else endpoint['local_port']), resource)
        state = old._join(_selected_rows(presend['snapshot'], endpoint['local_port']), endpoint, resource['server']['pid'], bracket['client']['pid'])
        _need(type(value['client_raw_state']) is int and value['client_raw_state'] == state, 'ownership')
        return True
    except (ValueError, TypeError, KeyError, AttributeError, OverflowError, RecursionError):
        return False


def report_bytes(value, expected_admission):
    """Bound private raw serialization without turning refusal into authority."""
    admitted = validate_admission(expected_admission); resource = backend_admission(admitted)
    old._obj(value, REPORT_KEYS, 'admission')
    _need(type(value['version']) is int and value['version'] == 1 and value['protocol'] == PROTOCOL and
          value['feature_acceptance'] is False and _same(value['admission'], admitted), 'admission')
    _need(value['status'] in ('observed', 'refused') and
          (value['reason'] is None if value['status'] == 'observed' else
           type(value['reason']) is str and value['reason'] in REASONS), 'backend')
    _need(value['request_hex'] == REQUEST.hex() and type(value['response_hex']) is str and
          len(value['response_hex']) <= 2*(MAX_RESPONSE+1) and
          re.fullmatch('(?:[0-9a-f]{2})*', value['response_hex']) is not None, 'framing')
    for key in ('request_sent', 'response_complete', 'ownership_verified', 'socket_closed', 'process_handles_closed'):
        _need(type(value[key]) is bool, 'backend')
    old._int(value['elapsed_ms'], 0, 2**63-1, 'deadline')
    if value['client_raw_state'] is not None:
        old._int(value['client_raw_state'], 0, 2**32-1, 'ownership')
    _need(value['version_proof'] is None or _version_verified(value['version_proof'], resource), 'version')
    _need(value['rows'] is None or _same(value['rows'], _decode_response(bytes.fromhex(value['response_hex']))))
    stages = value['stages']; _need(type(stages) is list and len(stages) <= 5, 'backend')
    allowed = dict(initial={'stage', 'bracket', 'snapshot'}, connected={'stage', 'endpoint'},
        presend={'stage', 'endpoint_before', 'endpoint_after', 'bracket', 'snapshot'},
        send_attempt={'stage'}, final={'stage', 'endpoint', 'bracket', 'snapshot'})
    _need([s.get('stage') for s in stages] == list(allowed)[:len(stages)], 'backend')
    client_port = None
    for stage in stages:
        _need(type(stage) is dict and set(stage) <= allowed[stage['stage']], 'backend')
        if 'bracket' in stage:
            old._bracket(stage['bracket'], resource)
        for name in ('endpoint', 'endpoint_before', 'endpoint_after'):
            if name in stage:
                old._endpoint(stage[name])
        if stage['stage'] == 'connected' and 'endpoint' in stage:
            client_port = stage['endpoint']['local_port']
        if 'snapshot' in stage:
            _selected_rows(stage['snapshot'], None if stage['stage'] == 'initial' else client_port)
    raw = (json.dumps(value, ensure_ascii=True, allow_nan=False, sort_keys=True, separators=(',', ':'))+'\n').encode()
    _need(0 < len(raw) <= MAX_REPORT, 'framing')
    return raw
