"""Fixed read-only phone inventory contract; no import-time IO or authorization.

Recorded consistency is not acquisition. Human authorization, source/worker pins
and known external ownership remain separate from these private report checks.
Copyright 2026 LocalLore contributors. SPDX-License-Identifier: Apache-2.0
"""
import copy
import json
import re
import shlex
import struct

from benchmarks import adb_held_socket as old
from benchmarks import adb_device_roster as roster

PROTOCOL = 'physical-phone-inventory-v1'
MAX_SECONDS = 20.0
MAX_WIRE = 65536
MAX_STDOUT = 32768
MAX_STDERR = 4096
MAX_PACKETS = 256
MAX_REPORT = 2 * 1024 * 1024
IDENTITY = ('ro.build.fingerprint', 'ro.product.model', 'ro.build.version.sdk',
            'ro.soc.model', 'ro.board.platform', 'ro.product.cpu.abilist', 'ro.kernel.qemu')
SCRIPT = (
    'u=$(am get-current-user) || exit 40; [ "$u" = 0 ] || exit 41; '
    'printf "LLPI_V1\\nUSER\\n%s\\nPROPERTIES\\n" "$u"; '
    'for k in ' + ' '.join(IDENTITY) + '; do printf "%s=" "$k"; getprop "$k" || exit 42; done; '
    'printf "PAGE\\n"; getconf PAGESIZE || exit 43; '
    'printf "MEMORY\\n"; grep -E "^(MemTotal|MemAvailable):" /proc/meminfo || exit 44; '
    'printf "SPACE\\n"; stat -f -c "%a|%S" /data/local/tmp || exit 45; '
    'printf "BATTERY\\n"; dumpsys battery | grep -E "^ *(USB powered|level|scale|temperature): " || exit 46; '
    'printf "THERMAL\\n"; dumpsys thermalservice | grep "^Thermal Status: " || exit 47; '
    'printf "END\\n"'
)


def _frame(service):
    return ('%04x' % len(service)).encode('ascii') + service


TPORT_REQUEST = _frame(b'host:tport:usb')
SHELL_REQUEST = _frame(b'shell,v2,raw:' + shlex.join(('sh', '-c', SCRIPT)).encode('utf-8'))
CLOSE_STDIN = b'\x04\x00\x00\x00\x00'
REASONS = roster.REASONS | {'roster', 'target', 'transport', 'shell', 'facts'}
REPORT_KEYS = frozenset(('version protocol feature_acceptance admission status reason roster_proof target '
    'stages tport_attempted device_request_attempted stdin_close_attempted tport_sent '
    'device_request_sent stdin_closed wire_hex response_complete ownership_verified client_raw_state '
    'facts elapsed_ms socket_closed process_handles_closed').split())
STAGES = ('initial', 'connected', 'tport', 'service', 'stdin', 'final')
_SEND_KEYS = {'stage', 'endpoint_before', 'endpoint_after', 'bracket', 'snapshot', 'client_raw_state'}
_STAGE_KEYS = {'initial': {'stage', 'bracket', 'snapshot'}, 'connected': {'stage', 'endpoint'},
               **{name: _SEND_KEYS for name in ('tport', 'service', 'stdin')},
               'final': {'stage', 'endpoint', 'bracket', 'snapshot'}}


class InventoryRefused(ValueError):
    def __init__(self, reason='facts'):
        self.reason = reason if type(reason) is str and reason in REASONS else 'backend'
        super().__init__(self.reason)


class InventoryReceiveRefused(old.ProbeRefused):
    """Actual bounded received bytes, retained without accepting their verdict."""
    def __init__(self, reason, received):
        old._need(type(received) is bytes and len(received) <= MAX_WIRE + 1, 'framing')
        self.received = received
        super().__init__(reason)


def _need(value, reason='facts'):
    if not value:
        raise InventoryRefused(reason)


def validate_admission(value):
    old._obj(value, ('version', 'protocol', 'server', 'adb_file', 'candidates',
                     'expected_version', 'authorized_serial'), 'admission')
    _need(value['protocol'] == PROTOCOL, 'admission')
    serial = value['authorized_serial']
    _need(type(serial) is str and re.fullmatch('[A-Za-z0-9_-]{4,128}', serial) is not None
          and not serial.startswith('emulator-'), 'admission')
    translated = copy.deepcopy(value)
    del translated['authorized_serial']
    translated['protocol'] = roster.PROTOCOL
    roster.validate_admission(translated)
    return copy.deepcopy(value)


def roster_admission(value):
    translated = validate_admission(value)
    del translated['authorized_serial']
    translated['protocol'] = roster.PROTOCOL
    return translated


def backend_admission(value):
    return roster.backend_admission(roster_admission(value))


def selected_target(admission, proof):
    admitted = validate_admission(admission)
    _need(roster.report_verified(proof, roster_admission(admitted)), 'roster')
    selected = [row for row in proof['rows'] if row['serial'] == admitted['authorized_serial']]
    _need(len(selected) == 1 and selected[0]['state'] == 'device' and
          all(type(selected[0][key]) is str and selected[0][key]
              for key in ('product', 'model', 'device')), 'target')
    return copy.deepcopy(selected[0])


def _decimal(text, low=0, high=2**63-1):
    _need(type(text) is str and re.fullmatch('0|[1-9][0-9]{0,19}', text) is not None)
    number = int(text)
    _need(low <= number <= high)
    return number


def parse_facts(raw):
    """Parse fixed read-only output; facts do not grant pre-install eligibility."""
    _need(type(raw) is bytes and 0 < len(raw) <= MAX_STDOUT)
    text = raw.decode('utf-8', errors='strict')
    _need(text.endswith('\n') and not any(ord(c) < 32 and c not in '\n\t' or ord(c) == 127 for c in text))
    lines = text.splitlines()
    markers = ('LLPI_V1', 'USER', 'PROPERTIES', 'PAGE', 'MEMORY', 'SPACE', 'BATTERY', 'THERMAL', 'END')
    _need(lines[0] == markers[0] and lines[-1] == markers[-1])
    positions = []
    for marker in markers:
        hits = [i for i, line in enumerate(lines) if line == marker]
        _need(len(hits) == 1)
        positions.append(hits[0])
    _need(positions == sorted(positions) and positions[:2] == [0, 1])
    blocks = {markers[i]: lines[positions[i]+1:positions[i+1]] for i in range(1, len(markers)-1)}
    _need(blocks['USER'] == ['0'])
    properties = {}
    _need(len(blocks['PROPERTIES']) == len(IDENTITY))
    for expected, line in zip(IDENTITY, blocks['PROPERTIES']):
        key, sep, value = line.partition('=')
        _need(sep and key == expected and len(value.encode('utf-8')) <= (512 if key == IDENTITY[0] else 128)
              and not any(ord(c) < 32 or ord(c) == 127 for c in value))
        properties[key] = value
    _need(all(properties[key] for key in IDENTITY[:-1]) and properties['ro.kernel.qemu'] in ('', '0'))
    _decimal(properties['ro.build.version.sdk'], 1, 65535)
    abis = properties['ro.product.cpu.abilist'].split(',')
    _need(1 <= len(abis) <= 8 and len(abis) == len(set(abis)) and
          all(re.fullmatch('[A-Za-z0-9_-]{1,32}', abi) is not None for abi in abis))
    _need(len(blocks['PAGE']) == 1)
    page = _decimal(blocks['PAGE'][0], 4096, 65536)
    _need(page & (page-1) == 0)
    memory = {}
    _need(len(blocks['MEMORY']) == 2)
    for line in blocks['MEMORY']:
        match = re.fullmatch(r'(MemTotal|MemAvailable):[ \t]+([0-9]+) kB', line)
        _need(match is not None and match[1] not in memory)
        memory[match[1]] = _decimal(match[2], 0, (2**63-1)//1024) * 1024
    _need(set(memory) == {'MemTotal', 'MemAvailable'} and 0 <= memory['MemAvailable'] <= memory['MemTotal']
          and memory['MemTotal'] > 0)
    _need(len(blocks['SPACE']) == 1)
    space = blocks['SPACE'][0].split('|')
    _need(len(space) == 2)
    free = _decimal(space[0]) * _decimal(space[1], 1)
    _need(free <= 2**63-1)
    battery = {}
    for line in blocks['BATTERY']:
        key, sep, value = line.strip().partition(': ')
        _need(sep and key in ('USB powered', 'level', 'scale', 'temperature') and key not in battery)
        battery[key] = value
    _need(set(battery) == {'USB powered', 'level', 'scale', 'temperature'} and
          battery['USB powered'] in ('true', 'false'))
    level = _decimal(battery['level'], 0, 100)
    scale = _decimal(battery['scale'], 1, 100)
    _need(level <= scale and re.fullmatch('-?(?:0|[1-9][0-9]{0,3})', battery['temperature']) is not None)
    temperature = int(battery['temperature'])
    _need(-1000 <= temperature <= 2000)
    _need(len(blocks['THERMAL']) == 1)
    thermal = re.fullmatch(r'Thermal Status: ([0-6])[ \t]*', blocks['THERMAL'][0])
    _need(thermal is not None)
    return dict(current_user=0, properties=properties, page_bytes=page,
        memory_total_bytes=memory['MemTotal'], memory_available_bytes=memory['MemAvailable'],
        internal_free_bytes=free, battery=dict(usb_powered=battery['USB powered'] == 'true',
            level=level, scale=scale, temperature_tenths_celsius=temperature), thermal_status=int(thermal[1]))


def decode_wire(raw, transport_id):
    """Strict complete stream decoding. Actual EOF is an extra acquisition gate."""
    _need(type(raw) is bytes and 16 <= len(raw) <= MAX_WIRE, 'framing')
    old._int(transport_id, 1, 2**64-1, 'transport')
    _need(raw[:4] == b'OKAY' and struct.unpack('<Q', raw[4:12])[0] == transport_id, 'transport')
    _need(raw[12:16] == b'OKAY', 'shell')
    cursor, count, exited = 16, 0, False
    stdout, stderr = bytearray(), bytearray()
    while cursor < len(raw):
        count += 1
        _need(count <= MAX_PACKETS and not exited and len(raw)-cursor >= 5, 'framing')
        channel, size = raw[cursor], struct.unpack('<I', raw[cursor+1:cursor+5])[0]
        cursor += 5
        _need(channel in (1, 2, 3) and size <= MAX_STDOUT and cursor+size <= len(raw), 'framing')
        payload = raw[cursor:cursor+size]
        cursor += size
        if channel == 3:
            _need(size == 1 and payload == b'\x00', 'shell')
            exited = True
        else:
            sink, limit = (stdout, MAX_STDOUT) if channel == 1 else (stderr, MAX_STDERR)
            _need(len(sink)+size <= limit, 'framing')
            sink.extend(payload)
    _need(exited and not stderr, 'shell')
    return parse_facts(bytes(stdout))


def _candidates(rows, admission, prior):
    roster.validate_candidates(rows, roster_admission(admission), prior['version_proof'], prior)


def probe(backend, admission, roster_proof):
    report = dict(version=1, protocol=PROTOCOL, feature_acceptance=False, admission=None,
        status='refused', reason='admission', roster_proof=None, target=None, stages=[],
        tport_attempted=False, device_request_attempted=False, stdin_close_attempted=False,
        tport_sent=False, device_request_sent=False, stdin_closed=False, wire_hex='',
        response_complete=False, ownership_verified=False, client_raw_state=None,
        facts=None, elapsed_ms=0, socket_closed=False, process_handles_closed=False)
    started = last = None
    wire = bytearray()
    try:
        admitted = validate_admission(admission)
        report['admission'] = admitted
        prior = copy.deepcopy(roster_proof)
        target = selected_target(admitted, prior)
        report['roster_proof'], report['target'] = copy.deepcopy(prior), target
        resource = backend_admission(admitted)
        started = last = old._now(backend)
        until = started + MAX_SECONDS
        def tick():
            nonlocal last
            now = old._now(backend)
            _need(last <= now < until, 'deadline')
            last = now
        def call(name, *args):
            tick()
            value = getattr(backend, name)(*copy.deepcopy(args), until)
            tick()
            return value
        def receive(limit):
            tick()
            try:
                part = backend.recv(limit, until)
            except InventoryReceiveRefused as error:
                wire.extend(error.received[:limit])
                report['wire_hex'] = wire.hex()
                raise
            _need(type(part) is bytes, 'framing')
            wire.extend(part[:limit])
            report['wire_hex'] = wire.hex()
            _need(len(part) <= limit and len(wire) <= MAX_WIRE, 'framing')
            tick()
            return part
        def exact(size):
            chunks = bytearray()
            while len(chunks) < size:
                part = receive(size-len(chunks))
                _need(part, 'framing')
                chunks.extend(part)
            return bytes(chunks)
        call('open', resource)
        initial = old._bracket(call('bracket', resource), resource)
        _need(roster._same(initial['client'], prior['stages'][0]['bracket']['client']), 'identity')
        rows, snapshot = old._snapshot(call('snapshot'))
        report['stages'].append(dict(stage='initial', bracket=initial, snapshot=snapshot))
        _candidates(rows, admitted, prior)
        call('connect')
        endpoint = old._endpoint(call('endpoint'))
        report['stages'].append(dict(stage='connected', endpoint=endpoint))
        def send_stage(name, data, attempted, completed):
            before = old._endpoint(call('endpoint'), endpoint)
            rows, snapshot = old._snapshot(call('snapshot'), endpoint)
            after = old._endpoint(call('endpoint'), endpoint)
            bracket = old._bracket(call('bracket', resource), resource, initial)
            _candidates(rows, admitted, prior)
            state = old._join(rows, endpoint, resource['server']['pid'], initial['client']['pid'])
            report['stages'].append(dict(stage=name, endpoint_before=before, endpoint_after=after,
                bracket=bracket, snapshot=snapshot, client_raw_state=state))
            if name == 'tport':
                report['client_raw_state'] = state
            report['ownership_verified'] = True
            report[attempted] = True
            call('send', data)
            report[completed] = True
        send_stage('tport', TPORT_REQUEST, 'tport_attempted', 'tport_sent')
        selected = exact(12)
        _need(selected[:4] == b'OKAY' and struct.unpack('<Q', selected[4:])[0] == target['transport_id'], 'transport')
        send_stage('service', SHELL_REQUEST, 'device_request_attempted', 'device_request_sent')
        _need(exact(4) == b'OKAY', 'shell')
        send_stage('stdin', CLOSE_STDIN, 'stdin_close_attempted', 'stdin_closed')
        while receive(MAX_WIRE+1-len(wire)):
            pass
        report['facts'] = decode_wire(bytes(wire), target['transport_id'])
        report['response_complete'] = True
        final = dict(stage='final', endpoint=old._endpoint(call('endpoint'), endpoint),
                     bracket=old._bracket(call('bracket', resource), resource, initial))
        report['stages'].append(final)
        rows, final['snapshot'] = old._snapshot(call('snapshot'), endpoint)
        _candidates(rows, admitted, prior)
        report['status'], report['reason'] = 'observed', None
    except BaseException as error:
        report['reason'] = (error.reason if isinstance(error, (InventoryRefused, old.ProbeRefused, roster.RosterRefused)) else
            'cancelled' if isinstance(error, (KeyboardInterrupt, InterruptedError)) else 'backend')
    finally:
        try:
            closed = backend.close()
            old._obj(closed, ('socket_closed', 'process_handles_closed'), 'cleanup')
            for name, value in closed.items():
                _need(type(value) is bool, 'cleanup')
                report[name] = value
            _need(all(closed.values()), 'cleanup')
        except BaseException:
            report['status'], report['reason'] = 'refused', 'cleanup'
        if started is not None:
            try:
                now = old._now(backend)
                _need(now >= last, 'deadline')
                report['elapsed_ms'] = int((now-started)*1000)
                _need(now-started < MAX_SECONDS, 'deadline')
            except BaseException:
                report['status'], report['reason'] = 'refused', 'deadline'
    return report


def report_verified(value, expected_admission):
    """Closed-report consistency; it cannot authenticate execution or authority."""
    try:
        admitted = validate_admission(expected_admission)
        report_bytes(value, admitted)
        _need(value['status'] == 'observed' and value['reason'] is None and
              all(value[name] is True for name in ('tport_attempted', 'device_request_attempted', 'stdin_close_attempted',
                  'tport_sent', 'device_request_sent', 'stdin_closed', 'response_complete', 'ownership_verified',
                  'socket_closed', 'process_handles_closed')), 'backend')
        old._int(value['elapsed_ms'], 0, int(MAX_SECONDS*1000)-1, 'deadline')
        target = selected_target(admitted, value['roster_proof'])
        _need(roster._same(value['target'], target) and roster._same(value['facts'],
              decode_wire(bytes.fromhex(value['wire_hex']), target['transport_id'])), 'facts')
        stages, resource = value['stages'], backend_admission(admitted)
        _need(len(stages) == len(STAGES), 'backend')
        for stage in stages:
            old._obj(stage, _STAGE_KEYS[stage['stage']], 'backend')
        first, connected, tport, service, stdin, final = stages
        bracket = old._bracket(first['bracket'], resource)
        _need(roster._same(bracket['client'], value['roster_proof']['stages'][0]['bracket']['client']), 'identity')
        endpoint = old._endpoint(connected['endpoint'])
        for index, stage in enumerate((first, tport, service, stdin, final)):
            if index:
                old._bracket(stage['bracket'], resource, bracket)
            rows = roster._selected_rows(stage['snapshot'], None if index == 0 else endpoint['local_port'])
            _candidates(rows, admitted, value['roster_proof'])
            if stage['stage'] in ('tport', 'service', 'stdin'):
                old._endpoint(stage['endpoint_before'], endpoint)
                old._endpoint(stage['endpoint_after'], endpoint)
                state = old._join(rows, endpoint, resource['server']['pid'], bracket['client']['pid'])
                _need(type(stage['client_raw_state']) is int and stage['client_raw_state'] == state, 'ownership')
        old._endpoint(final['endpoint'], endpoint)
        _need(type(value['client_raw_state']) is int and value['client_raw_state'] == tport['client_raw_state'], 'ownership')
        return True
    except (ValueError, TypeError, KeyError, AttributeError, IndexError, OverflowError, RecursionError):
        return False


def report_bytes(value, expected_admission):
    admitted = validate_admission(expected_admission)
    old._obj(value, REPORT_KEYS, 'admission')
    _need(type(value['version']) is int and value['version'] == 1 and value['protocol'] == PROTOCOL and
          value['feature_acceptance'] is False and roster._same(value['admission'], admitted), 'admission')
    _need(value['status'] in ('observed', 'refused') and (value['reason'] is None if value['status'] == 'observed' else
          type(value['reason']) is str and value['reason'] in REASONS), 'backend')
    for name in ('tport_attempted', 'device_request_attempted', 'stdin_close_attempted', 'tport_sent',
                 'device_request_sent', 'stdin_closed', 'response_complete', 'ownership_verified',
                 'socket_closed', 'process_handles_closed'):
        _need(type(value[name]) is bool, 'backend')
    old._int(value['elapsed_ms'], 0, 2**63-1, 'deadline')
    if value['client_raw_state'] is not None:
        old._int(value['client_raw_state'], 0, 2**32-1, 'ownership')
    _need(type(value['wire_hex']) is str and len(value['wire_hex']) <= 2*(MAX_WIRE+1) and
          re.fullmatch('(?:[0-9a-f]{2})*', value['wire_hex']) is not None, 'framing')
    if value['roster_proof'] is not None:
        _need(roster.report_verified(value['roster_proof'], roster_admission(admitted)), 'roster')
    if value['target'] is not None:
        _need(roster._same(value['target'], selected_target(admitted, value['roster_proof'])), 'target')
    if value['facts'] is not None:
        _need(value['target'] is not None and roster._same(value['facts'],
              decode_wire(bytes.fromhex(value['wire_hex']), value['target']['transport_id'])), 'facts')
    stages = value['stages']
    _need(type(stages) is list and len(stages) <= len(STAGES) and
          [s.get('stage') for s in stages] == list(STAGES[:len(stages)]), 'backend')
    endpoint = None
    for stage in stages:
        _need(type(stage) is dict and set(stage) <= _STAGE_KEYS[stage['stage']], 'backend')
        if 'bracket' in stage:
            old._bracket(stage['bracket'], backend_admission(admitted))
        for name in ('endpoint', 'endpoint_before', 'endpoint_after'):
            if name in stage:
                old._endpoint(stage[name])
                endpoint = stage[name]
        if 'snapshot' in stage:
            roster._selected_rows(stage['snapshot'], None if stage['stage'] == 'initial' else
                                  endpoint['local_port'] if endpoint is not None else None)
    raw = (json.dumps(value, ensure_ascii=True, allow_nan=False, sort_keys=True, separators=(',', ':'))+'\n').encode()
    _need(0 < len(raw) <= MAX_REPORT, 'framing')
    return raw
