"""Explicit held-socket ownership contract; no import-time filesystem/network IO.

Recorded bytes cannot authenticate their own acquisition. The source-pinned
Windows worker and its known owner/capture are separate evidence requirements.
Copyright 2026 LocalLore contributors. SPDX-License-Identifier: Apache-2.0
"""
import copy
from dataclasses import asdict, dataclass
import hashlib
import math
import re

from benchmarks.windows_tcp_observation import (
    AF_INET, AF_INET6, MAX_CAPTURE, MAX_ROWS, TcpRow, decode_table,
)

PROTOCOL = 'adb-held-socket-server-owner-v1'
REQUEST = b'000Chost:version'
MAX_SECONDS = 3.0
REASONS = {'admission','deadline','identity','candidates','snapshot','ownership',
           'endpoint','framing','backend','cancelled','cleanup'}
REPORT_KEYS = {'version','protocol','feature_acceptance','admission','status','reason',
               'stages','request_hex','request_sent','response_hex','response_complete',
               'ownership_verified','client_raw_state','elapsed_ms','socket_closed',
               'process_handles_closed'}


class ProbeRefused(ValueError):
    def __init__(self, reason='backend'):
        self.reason = reason if type(reason) is str and reason in REASONS else 'backend'
        super().__init__(self.reason)


@dataclass(frozen=True, slots=True)
class TableCapture:
    family: int
    raw: bytes
    allocated_bytes: int
    table_class: int = 5


@dataclass(frozen=True, slots=True)
class Snapshot:
    tables: tuple[TableCapture, TableCapture]
    abi_checked: bool = True


def _need(value, reason):
    if not value:
        raise ProbeRefused(reason)


def _int(value, low=0, high=2**64-1, reason='admission'):
    _need(type(value) is int and low <= value <= high, reason)
    return value


def _obj(value, keys, reason):
    _need(type(value) is dict and set(value) == set(keys), reason)
    return value


def _process(value, reason='identity'):
    _obj(value, ('pid','creation_filetime','executable'), reason)
    _int(value['pid'],1,2**32-1,reason)
    _int(value['creation_filetime'],1,reason=reason)
    name = value['executable']
    _need(type(name) is str and 3 < len(name) <= 32768 and
          re.match(r'^[A-Za-z]:[\\/]', name) is not None and
          not any(ord(char) < 32 for char in name), reason)


def _file(value, reason='identity'):
    _obj(value, ('path','bytes','sha256','identity'), reason)
    _need(type(value['path']) is str, reason)
    _int(value['bytes'],1,64*1024*1024,reason)
    _need(type(value['sha256']) is str and re.fullmatch('[0-9a-f]{64}',value['sha256']), reason)
    identity = value['identity']
    _need(type(identity) is list and len(identity) == 5, reason)
    for item in identity:
        _int(item,high=2**128-1,reason=reason)
    _need(identity[2] == value['bytes'],reason)


def _candidate_key(row):
    return row['family'],row['address'],row['port'],row['pid'],row['scope_id']


def validate_admission(value):
    _obj(value, ('version','protocol','server','adb_file','candidates','expected_version'), 'admission')
    _need(type(value['version']) is int and value['version'] == 1 and value['protocol'] == PROTOCOL,'admission')
    _process(value['server'],'admission'); _file(value['adb_file'],'admission')
    _need(value['adb_file']['path'] == value['server']['executable'],'admission')
    _need(type(value['expected_version']) is str and re.fullmatch('[0-9a-f]{4}',value['expected_version']), 'admission')
    candidates = value['candidates']
    _need(type(candidates) is list and 1 <= len(candidates) <= 2,'admission')
    for row in candidates:
        _obj(row, ('family','address','port','pid','scope_id'),'admission')
        _int(row['family'],reason='admission'); _int(row['port'],reason='admission')
        _int(row['pid'],reason='admission'); _int(row['scope_id'],reason='admission')
        _need((row['family'],row['address']) in ((2,'127.0.0.1'),(23,'::1')) and
              row['port'] == 5037 and row['pid'] == value['server']['pid'] and row['scope_id'] == 0,'admission')
    keys = [_candidate_key(row) for row in candidates]
    _need(keys == sorted(set(keys)) and any(row['family'] == 2 for row in candidates),'admission')
    return copy.deepcopy(value)


def _bracket(value, admission, previous=None):
    _obj(value, ('server','client','adb_file','held_processes_alive'),'identity')
    _process(value['server']); _process(value['client']); _file(value['adb_file'])
    _need(value['held_processes_alive'] is True and value['server'] == admission['server'] and
          value['adb_file'] == admission['adb_file'] and value['client']['pid'] != value['server']['pid'],'identity')
    if previous is not None:
        _need(value == previous,'identity')
    return copy.deepcopy(value)


def _endpoint(value, previous=None):
    _obj(value, ('handle','socket_id','local_address','local_port','peer_address','peer_port'),'endpoint')
    for key in ('handle','socket_id'):
        _int(value[key],1,2**128-1,'endpoint')
    _int(value['local_port'],1,65535,'endpoint'); _int(value['peer_port'],1,65535,'endpoint')
    _need(value['local_address'] == value['peer_address'] == '127.0.0.1' and
          value['peer_port'] == 5037 and value['local_port'] != 5037,'endpoint')
    _need(previous is None or previous == value,'endpoint')
    return copy.deepcopy(value)


def _row_record(row, ordinal, raw):
    return dict(family=row.family,ordinal=ordinal,raw_hex=raw.hex(),
                raw_sha256=hashlib.sha256(raw).hexdigest(),row=asdict(row))


def _snapshot(value, endpoint=None):
    _need(type(value) is Snapshot and value.abi_checked is True and
          type(value.tables) is tuple and len(value.tables) == 2,'snapshot')
    rows, tables, selected = [], [], []
    for table, family in zip(value.tables,(AF_INET,AF_INET6)):
        _need(type(table) is TableCapture and type(table.family) is int and table.family == family and
              type(table.table_class) is int and table.table_class == 5,'snapshot')
        _int(table.allocated_bytes,4,MAX_CAPTURE,'snapshot')
        _need(type(table.raw) is bytes and 4 <= len(table.raw) <= table.allocated_bytes,'snapshot')
        try:
            decoded = decode_table(table.raw,family)
        except ValueError:
            raise ProbeRefused('snapshot') from None
        tables.append(dict(family=family,table_class=5,allocated_bytes=table.allocated_bytes,
                           returned_bytes=len(table.raw),count=len(decoded),raw_sha256=hashlib.sha256(table.raw).hexdigest()))
        stride = 24 if family == 2 else 56
        for ordinal,row in enumerate(decoded):
            rows.append(row)
            if row.local_port == 5037 or endpoint is not None and row.local_port == endpoint['local_port']:
                _need(len(selected) < 64,'snapshot')
                selected.append(_row_record(row,ordinal,table.raw[4+ordinal*stride:4+(ordinal+1)*stride]))
    return rows,dict(abi_checked=True,tables=tables,rows=selected)


def _candidates(rows, admission):
    candidates = []
    for row in rows:
        if row.local_port != 5037:
            continue
        _need((row.family,row.local_address) in ((2,'127.0.0.1'),(23,'::1')) and
              row.local_scope_id == 0 and row.pid == admission['server']['pid'],'candidates')
        if row.state == 2 or row.remote_port == 0 and row.remote_address in ('0.0.0.0','::'):
            candidates.append(dict(family=row.family,address=row.local_address,port=row.local_port,
                                   pid=row.pid,scope_id=row.local_scope_id))
    _need(sorted(candidates,key=_candidate_key) == admission['candidates'],'candidates')


def _join(rows, endpoint, server_pid, client_pid):
    # Select every matching tuple first. Never hide ambiguity with a PID filter.
    server = [row for row in rows if row.family == 2 and row.local_address == '127.0.0.1' and
              row.local_port == 5037 and row.remote_address == '127.0.0.1' and row.remote_port == endpoint['local_port']]
    client = [row for row in rows if row.family == 2 and row.local_address == '127.0.0.1' and
              row.local_port == endpoint['local_port'] and row.remote_address == '127.0.0.1' and row.remote_port == 5037]
    _need(len(server) == len(client) == 1,'ownership')
    _need(server[0].pid == server_pid and server[0].state == 5 and client[0].pid == client_pid and
          server[0].local_scope_id == server[0].remote_scope_id ==
          client[0].local_scope_id == client[0].remote_scope_id == 0,'ownership')
    return client[0].state


def _now(backend):
    value = backend.now()
    _need(type(value) in (int,float) and math.isfinite(value) and value >= 0,'deadline')
    return value


def probe(backend, admission):
    """One attempt. A false request_sent after send_attempt leaves partial send unknown."""
    report = dict(version=1,protocol=PROTOCOL,feature_acceptance=False,admission=None,status='refused',
        reason='admission',stages=[],request_hex=REQUEST.hex(),request_sent=False,response_hex='',
        response_complete=False,ownership_verified=False,client_raw_state=None,elapsed_ms=0,
        socket_closed=False,process_handles_closed=False)
    started = None
    response = bytearray()
    try:
        admitted = validate_admission(admission); report['admission'] = admitted
        started = _now(backend); until = started+MAX_SECONDS
        def call(name,*args):
            _need(_now(backend) < until,'deadline')
            result = getattr(backend,name)(*args,until)
            _need(_now(backend) < until,'deadline')
            return result
        call('open',admitted)
        initial = _bracket(call('bracket',admitted),admitted)
        rows,snapshot = _snapshot(call('snapshot'))
        report['stages'].append(dict(stage='initial',bracket=initial,snapshot=snapshot))
        _candidates(rows,admitted)
        call('connect')
        endpoint = _endpoint(call('endpoint'))
        report['stages'].append(dict(stage='connected',endpoint=endpoint))
        rows,snapshot = _snapshot(call('snapshot'),endpoint)
        presend = dict(stage='presend',endpoint_before=endpoint,snapshot=snapshot)
        report['stages'].append(presend)
        presend['endpoint_after'] = _endpoint(call('endpoint'),endpoint)
        presend['bracket'] = _bracket(call('bracket',admitted),admitted,initial)
        _candidates(rows,admitted)
        report['client_raw_state'] = _join(rows,endpoint,admitted['server']['pid'],initial['client']['pid'])
        report['ownership_verified'] = True
        report['stages'].append(dict(stage='send_attempt'))
        call('send',REQUEST); report['request_sent'] = True
        while True:
            part = call('recv',13-len(response))
            _need(type(part) is bytes and len(part) <= 13-len(response),'framing')
            response.extend(part); report['response_hex'] = response.hex()
            if not part:
                break
            _need(len(response) < 13,'framing')
        _need(bytes(response) == b'OKAY0004'+admitted['expected_version'].encode('ascii'),'framing')
        report['response_complete'] = True
        final = dict(stage='final',endpoint=_endpoint(call('endpoint'),endpoint),
                     bracket=_bracket(call('bracket',admitted),admitted,initial))
        report['stages'].append(final)
        rows,final['snapshot'] = _snapshot(call('snapshot'),endpoint)
        _candidates(rows,admitted)
        report['status'],report['reason'] = 'verified',None
    except BaseException as error:
        report['reason'] = (error.reason if type(error) is ProbeRefused else
                            'cancelled' if isinstance(error,(KeyboardInterrupt,InterruptedError)) else 'backend')
    finally:
        try:
            closed = backend.close()
            _obj(closed,('socket_closed','process_handles_closed'),'cleanup')
            for key in closed:
                _need(type(closed[key]) is bool,'cleanup'); report[key] = closed[key]
            _need(all(closed.values()),'cleanup')
        except BaseException:
            report['status'],report['reason'] = 'refused','cleanup'
        if started is not None:
            try:
                elapsed = _now(backend)-started
                _need(elapsed >= 0,'deadline')
                report['elapsed_ms'] = int(elapsed*1000)
                if elapsed >= MAX_SECONDS:
                    report['status'],report['reason'] = 'refused','deadline'
            except BaseException:
                report['status'],report['reason'] = 'refused','deadline'
    return report


def _record_rows(value):
    _obj(value,('abi_checked','tables','rows'),'snapshot')
    _need(value['abi_checked'] is True and type(value['tables']) is list and len(value['tables']) == 2 and
          type(value['rows']) is list and len(value['rows']) <= 64,'snapshot')
    counts = {}
    for table,family in zip(value['tables'],(2,23)):
        _obj(table,('family','table_class','allocated_bytes','returned_bytes','count','raw_sha256'),'snapshot')
        _need(type(table['family']) is int and table['family'] == family and
              type(table['table_class']) is int and table['table_class'] == 5,'snapshot')
        allocated = _int(table['allocated_bytes'],4,MAX_CAPTURE,'snapshot')
        returned = _int(table['returned_bytes'],4,allocated,'snapshot')
        count = _int(table['count'],0,MAX_ROWS,'snapshot')
        _need(4+count*(24 if family == 2 else 56) <= returned and
              type(table['raw_sha256']) is str and re.fullmatch('[0-9a-f]{64}',table['raw_sha256']),'snapshot')
        counts[family] = count
    rows,seen = [],[]
    for record in value['rows']:
        _obj(record,('family','ordinal','raw_hex','raw_sha256','row'),'snapshot')
        family = record['family']; _need(type(family) is int and family in counts,'snapshot')
        ordinal = _int(record['ordinal'],0,counts[family]-1,'snapshot')
        raw_hex = record['raw_hex']; size = 24 if family == 2 else 56
        _need(type(raw_hex) is str and re.fullmatch('[0-9a-f]{'+str(size*2)+'}',raw_hex),'snapshot')
        raw = bytes.fromhex(raw_hex)
        _need(hashlib.sha256(raw).hexdigest() == record['raw_sha256'],'snapshot')
        row = decode_table(b'\x01\0\0\0'+raw,family)[0]
        _need(type(record['row']) is dict and set(record['row']) == set(asdict(row)) and
              all(type(record['row'][key]) is type(item) and record['row'][key] == item
                  for key,item in asdict(row).items()),'snapshot')
        rows.append(row);seen.append((family,ordinal))
    _need(seen == sorted(set(seen)),'snapshot')
    return rows


def report_verified(value, expected_admission):
    """Structural replay only; source-pinned acquisition/owner evidence is additional."""
    try:
        admitted = validate_admission(expected_admission)
        _obj(value,REPORT_KEYS,'admission')
        _need(type(value['version']) is int and value['version'] == 1 and value['protocol'] == PROTOCOL and
              value['feature_acceptance'] is False and validate_admission(value['admission']) == admitted,'admission')
        _need(value['status'] == 'verified' and value['reason'] is None and
              all(value[key] is True for key in ('request_sent','response_complete','ownership_verified',
                  'socket_closed','process_handles_closed')),'backend')
        _need(value['request_hex'] == REQUEST.hex() and
              value['response_hex'] == (b'OKAY0004'+admitted['expected_version'].encode()).hex(),'framing')
        _int(value['elapsed_ms'],0,2999,'deadline')
        stages = value['stages']
        _need(type(stages) is list and len(stages) == 5 and
              [stage.get('stage') for stage in stages] == ['initial','connected','presend','send_attempt','final'],'backend')
        first,connected,presend,sent,final = stages
        for stage,keys in ((first,('stage','bracket','snapshot')),(connected,('stage','endpoint')),
            (presend,('stage','endpoint_before','endpoint_after','bracket','snapshot')),
            (sent,('stage',)),(final,('stage','endpoint','bracket','snapshot'))):
            _obj(stage,keys,'backend')
        bracket = _bracket(first['bracket'],admitted)
        endpoint = _endpoint(connected['endpoint'])
        _endpoint(presend['endpoint_before'],endpoint); _endpoint(presend['endpoint_after'],endpoint)
        _endpoint(final['endpoint'],endpoint)
        _bracket(presend['bracket'],admitted,bracket); _bracket(final['bracket'],admitted,bracket)
        for stage in (first,presend,final):
            _candidates(_record_rows(stage['snapshot']),admitted)
        state = _join(_record_rows(presend['snapshot']),endpoint,admitted['server']['pid'],bracket['client']['pid'])
        _need(type(value['client_raw_state']) is int and value['client_raw_state'] == state,'ownership')
        return True
    except (ValueError,TypeError,KeyError,AttributeError,OverflowError,RecursionError):
        return False
