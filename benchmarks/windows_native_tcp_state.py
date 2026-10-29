"""Explicit native owned-socket diagnostic; never service or device admission.

The report assessor is pure. Only main() starts a source-admitted native binary;
its build provenance remains the caller's separate obligation. Raw diagnostics
stay in a new physical-D folder outside Git. No legacy gate is changed.
Copyright 2026 LocalLore contributors. SPDX-License-Identifier: Apache-2.0
"""
import ipaddress
import json
from pathlib import Path, PureWindowsPath
import re
import struct

PROTOCOL = 'windows-native-owned-tcp-state-v1'
BARRIER = b'LL_NATIVE_TCP_STATE_V1\n'
PAYLOAD = b'LL_NTCP_CONTROL1!'
MAX_REPORT = 512*1024
PHASES = ('after_listen','connected','exchanged')
QUERIES = ('owner_listener','owner_all','basic','owner2')
ABI = {
    'owner_pid': dict(row_bytes=24,row_offset=4,field_offsets=[0,4,8,12,16,20]),
    'basic': dict(row_bytes=20,row_offset=4,field_offsets=[0,4,8,12,16]),
    'owner2': dict(row_bytes=28,row_offset=4,field_offsets=[0,4,8,12,16,20,24]),
}


class NativeControlRefused(ValueError):
    def __init__(self, reason='schema'):
        self.reason = reason if reason in {'schema','bounds','identity','abi','roster','raw',
            'exchange','cleanup','owner','source','output','binary','platform'} else 'schema'
        super().__init__(self.reason)


def _need(value, reason='schema'):
    if not value:
        raise NativeControlRefused(reason)


def _obj(value, keys, reason='schema'):
    _need(type(value) is dict and set(value) == set(keys),reason)


def _int(value, low=0, high=2**32-1, reason='schema'):
    _need(type(value) is int and low <= value <= high,reason)


def _same(left, right):
    if type(left) is not type(right):
        return False
    if type(left) is dict:
        return left.keys() == right.keys() and all(_same(left[k],right[k]) for k in left)
    if type(left) is list:
        return len(left) == len(right) and all(_same(a,b) for a,b in zip(left,right))
    return left == right


def _pairs(pairs):
    value = {}
    for key,item in pairs:
        _need(key not in value)
        value[key] = item
    return value


def _hex(value, size):
    _need(type(value) is str and len(value) == size*2 and
          re.fullmatch('[0-9a-f]*',value) is not None,'raw')
    return bytes.fromhex(value)


def _row(raw, name):
    size = 20 if name == 'basic' else 28 if name == 'owner2' else 24
    values = struct.unpack('<%dI' % (size//4),raw)
    address = lambda n:str(ipaddress.IPv4Address(n.to_bytes(4,'little')))
    port = lambda n:int.from_bytes((n & 65535).to_bytes(2,'little'),'big')
    return dict(state=values[0],local=address(values[1]),local_port=port(values[2]),
        remote=address(values[3]),remote_port=port(values[4]),
        pid=None if name == 'basic' else values[5])


def _query(value, name, listener, client, connected, pid):
    _obj(value,('name','initial_code','final_code','allocated_bytes','returned_bytes','count','rows'))
    _need(value['name'] == name,'roster')
    _int(value['initial_code']); _need(value['initial_code'] in (0,122),'raw')
    _int(value['final_code']); _need(value['final_code'] == 0,'raw')
    _int(value['allocated_bytes'],4,1024*1024,'bounds')
    _int(value['returned_bytes'],4,value['allocated_bytes'],'bounds')
    _int(value['count'],0,16384,'bounds')
    size = 20 if name == 'basic' else 28 if name == 'owner2' else 24
    _need(4+value['count']*size <= value['returned_bytes'],'bounds')
    rows = value['rows']; _need(type(rows) is list and len(rows) <= 8,'bounds')
    decoded, ordinals = [], []
    for item in rows:
        _obj(item,('ordinal','raw_hex'))
        _int(item['ordinal'],0,value['count']-1,'raw'); ordinals.append(item['ordinal'])
        row = _row(_hex(item['raw_hex'],size),name)
        _need(row['local'] == '127.0.0.1' and row['local_port'] in
              ({listener,client} if connected else {listener}),'raw')
        _need(row['pid'] is None or row['pid'] == pid,'identity')
        decoded.append(row)
    _need(ordinals == sorted(set(ordinals)),'raw')
    if not connected or name == 'owner_listener':
        _need(len(decoded) == 1 and decoded[0]['local_port'] == listener,'roster')
        return decoded[0]['state'],None,len(decoded)
    # Roles come from held endpoint tuples, never from a favorable state value.
    servers = [r for r in decoded if r['local_port'] == listener and
               r['remote'] == '127.0.0.1' and r['remote_port'] == client]
    clients = [r for r in decoded if r['local_port'] == client and
               r['remote'] == '127.0.0.1' and r['remote_port'] == listener]
    _need(len(decoded) == 3 and len(servers) == len(clients) == 1,'roster')
    listeners = [r for r in decoded if r is not servers[0] and r is not clients[0]]
    # LISTEN remote fields are undefined. The unique remaining listener-local
    # row is not required to have zero remote fields or a preferred raw state.
    _need(len(listeners) == 1 and listeners[0]['local_port'] == listener,'roster')
    return listeners[0]['state'],(servers[0]['state'],clients[0]['state']),len(decoded)


def assess_report(raw: bytes, expected_process: dict) -> dict:
    """Validate a full acquired report; preserve inconsistent states as evidence."""
    try:
        _need(type(raw) is bytes and 0 < len(raw) <= MAX_REPORT,'bounds')
        report = json.loads(raw.decode('utf-8'),object_pairs_hook=_pairs,
            parse_constant=lambda _:(_need(False)))
        _obj(expected_process,('pid','creation_filetime','executable'),'identity')
        _int(expected_process['pid'],1,2**32-1,'identity')
        _int(expected_process['creation_filetime'],1,2**64-1,'identity')
        _need(type(expected_process['executable']) is str and
              PureWindowsPath(expected_process['executable']).is_absolute(),'identity')
        _obj(report,('version','protocol','pid','creation_filetime','abi','listener_port','client_port',
            'stages','exchange','resources','acquisition_completed','reason','elapsed_ms'))
        _int(report['version'],1,1); _need(report['protocol'] == PROTOCOL)
        _int(report['pid'],1); _int(report['creation_filetime'],1,2**64-1)
        _need(report['pid'] == expected_process['pid'] and
              report['creation_filetime'] == expected_process['creation_filetime'],'identity')
        _need(_same(report['abi'],ABI),'abi')
        _need(report['acquisition_completed'] is True and report['reason'] is None)
        _int(report['elapsed_ms'],0,2**63-1)
        listener,client = report['listener_port'],report['client_port']
        for port in (listener,client):
            _int(port,1,65535); _need(port != 5037,'identity')
        _need(listener != client,'identity')
        resources = report['resources']
        _obj(resources,('created_mask','close_attempted_mask','closed_mask','winsock_started',
            'winsock_cleanup_attempted','winsock_cleanup_succeeded'),'cleanup')
        for key in ('created_mask','close_attempted_mask','closed_mask'):
            _int(resources[key],7,7,'cleanup')
        _need(all(resources[k] is True for k in ('winsock_started','winsock_cleanup_attempted',
                  'winsock_cleanup_succeeded')),'cleanup')
        exchange = report['exchange']
        _obj(exchange,('client_sent','server_received','server_sent','client_received','server_hex','client_hex'),'exchange')
        for key in ('client_sent','server_received','server_sent','client_received'):
            _int(exchange[key],len(PAYLOAD),len(PAYLOAD),'exchange')
        _need(_hex(exchange['server_hex'],len(PAYLOAD)) == PAYLOAD and
              _hex(exchange['client_hex'],len(PAYLOAD)) == PAYLOAD,'exchange')
        stages = report['stages']; _need(type(stages) is list and len(stages) == len(PHASES),'roster')
        listeners,connections,selected = [],[],0
        for stage,name in zip(stages,PHASES):
            _obj(stage,('stage','acceptconn','queries')); _need(stage['stage'] == name,'roster')
            _int(stage['acceptconn'],0,1)
            _need(type(stage['queries']) is list and len(stage['queries']) == len(QUERIES),'roster')
            for query,qname in zip(stage['queries'],QUERIES):
                state,pair,count = _query(query,qname,listener,client,name != 'after_listen',report['pid'])
                listeners.append(state); selected += count
                if pair is not None:
                    connections.append(dict(stage=name,query=qname,server=pair[0],client=pair[1]))
        consistent = all(stage['acceptconn'] == 1 for stage in stages) and all(state == 2 for state in listeners) and all(
            row['server'] == row['client'] == 5 for row in connections)
        return dict(version=1,protocol=PROTOCOL,feature_acceptance=False,acquisition_completed=True,
            observation_consistent=consistent,listener_states=listeners,connection_states=connections,
            selected_rows=selected,resources_closed=True)
    except NativeControlRefused:
        raise
    except (ValueError,TypeError,KeyError,OverflowError,RecursionError,UnicodeError,struct.error):
        raise NativeControlRefused('schema') from None


def _runtime():
    # Explicit launcher imports; no native observation occurs on module import.
    from benchmarks import receipt_avd_environment as env
    from benchmarks import windows_tcp_control as control
    from benchmarks import adb_held_socket_probe as probe
    return env,control,probe


def _source_bindings(env, probe):
    root = Path(__file__).resolve().parents[1]
    names = set(probe.PUBLIC_SOURCES) | {'benchmarks/windows_native_tcp_state.py',
        'benchmarks/native/windows_tcp_state_control.c'}
    if (root/'benchmarks/__init__.py').exists():
        names.add('benchmarks/__init__.py')
    return [env.binding(root/name) for name in sorted(names)]


def main(argv=None):
    import argparse
    import os
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--binary',required=True)
    parser.add_argument('--binary-sha256',required=True)
    parser.add_argument('--output',required=True)
    args = parser.parse_args(argv)
    env,control,probe = _runtime()
    control._prepare_environment()
    out = control.validate_output(args.output)
    binary = env.safe_path(args.binary)
    _need(binary.drive.upper() == 'D:' and binary.resolve(strict=True) == binary and
          binary.suffix.lower() == '.exe','binary')
    _need(all(not os.path.lexists(p/'.git') for p in (binary,*binary.parents)),'binary')
    pin = env.binding(binary)
    _need(type(args.binary_sha256) is str and re.fullmatch('[0-9a-f]{64}',args.binary_sha256) is not None and
          pin['sha256'] == args.binary_sha256 and pin['bytes'] <= 4*1024*1024,'binary')
    sources,python = _source_bindings(env,probe),probe._python_bindings()
    caller = env.process_identity(os.getpid())
    request = dict(version=1,protocol=PROTOCOL,binary=pin,sources=sources,python=python,owner=caller,
        command=[str(binary)],owner_seconds=30,feature_acceptance=False)
    out.mkdir()
    env.create_json(out/'request-v1.json',request)
    started_value = None
    def started(child):
        nonlocal started_value
        started_value = env.process_identity(child.pid)
        _need(started_value['executable'] == str(binary),'identity')
        env.create_json(out/'started-v1.json',dict(worker=started_value)); return True
    owner = env.supervise([str(binary)],BARRIER,out,30,started)
    env.create_json(out/'owner-result-v1.json',owner)
    after = dict(binary=env.binding(binary),sources=_source_bindings(env,probe),
        python=probe._python_bindings(),owner=env.process_identity(os.getpid()))
    env.create_json(out/'after-v1.json',after)
    stable = _same(after,dict(binary=pin,sources=sources,python=python,owner=caller))
    raw = (out/'owner-stdout-v1.bin').read_bytes()
    stderr = (out/'owner-stderr-v1.bin').read_bytes()
    qualified = owner['status'] == 'child_exited' and type(owner['worker_returncode']) is int and \
        owner['worker_returncode'] == 0 and owner['cleanup_complete'] is True and \
        owner['output_capture_complete'] is True and owner['stderr_bytes'] == len(stderr) == 0 and \
        owner['stdout_bytes'] == len(raw) and stable and started_value is not None
    assessment,reason = None,None
    if qualified:
        try:
            assessment = assess_report(raw,started_value)
        except NativeControlRefused as exc:
            reason = exc.reason; qualified = False
    else:
        reason = 'source' if not stable else 'owner'
    result = dict(version=1,protocol=PROTOCOL,feature_acceptance=False,qualified_acquisition=qualified,
        observation_consistent=bool(qualified and assessment['observation_consistent']),
        reason=reason,assessment=assessment,sources_equal=stable,
        request=env.binding(out/'request-v1.json'),owner=env.binding(out/'owner-result-v1.json'),
        raw=env.binding(out/'owner-stdout-v1.bin'),stderr=env.binding(out/'owner-stderr-v1.bin'))
    env.create_json(out/'result-v1.json',result)
    print(json.dumps(dict(qualified_acquisition=qualified,observation_consistent=result['observation_consistent'],
        feature_acceptance=False,reason=reason),sort_keys=True))
    return 0 if result['observation_consistent'] else 2 if qualified else 1


if __name__ == '__main__':
    raise SystemExit(main())
