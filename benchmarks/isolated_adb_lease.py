"""Distinct, source-admitted private ADB lease contracts; no import-time IO.

Metadata is not execution authentication or human authorization. Live owners
must admit actual source, binaries, native processes and endpoints separately.
This module never starts a server, queries a device or reads credential bytes.
Copyright 2026 LocalLore contributors. SPDX-License-Identifier: Apache-2.0
"""
import copy
import hashlib
import math
import os
from pathlib import Path, PureWindowsPath
import re
import struct

PROTOCOL = 'isolated-adb-lease-v2'
PORT = 15937
PHONE_PROTOCOL = 'owned-phone-discovery-service-v1'
PHONE_PORT = 5037
SDK_VERSION = '37.0.1-15733141'
ADB_SHA256 = 'b4a6b455702684652cccf7b46258b29e653538904359a58fd4931cf3ef286b3f'
TOOL_NAMES = {'adb.exe','AdbWinApi.dll','AdbWinUsbApi.dll','libwinpthread-1.dll','source.properties','NOTICE.txt'}
SOURCE_NAMES = {
    'adb_held_socket_probe.py','adb_held_socket.py','adb_held_socket_windows.py',
    'windows_tcp_control.py','windows_tcp_observation.py','receipt_avd_environment.py',
    'runtime_spike.py','host_commit_capacity.py','isolated_adb_lease.py','isolated_adb_owner.py',
}
FIXED_ENV = {'ADB_USB':'0','ADB_EMU':'0','ADB_MDNS':'0','ADB_MDNS_AUTO_CONNECT':'0',
             'ADB_LOCAL_TRANSPORT_MAX_PORT':'0','TEMP':'D:\\Dev\\_Temp','TMP':'D:\\Dev\\_Temp','TMPDIR':'D:\\Dev\\_Temp'}
ADMISSION_KEYS = {'version','protocol','run_id','root','port','seconds','adb','tools',
    'sdk_version','expected_version','sources','python','auth_key','capabilities','source_review'}
RUNNING_KEYS = {'version','protocol','admission','run_id','port','owner','worker','server',
    'started_epoch','deadline_epoch','sources','adb','version_proof','devices_proof'}
ROW_KEYS = {'family','local_address','local_port','remote_address','remote_port','local_scope_id',
    'remote_scope_id','state','pid','ordinal','raw_hex'}


class LeaseRefused(ValueError):
    def __init__(self, reason='schema'):
        self.reason = reason if reason in {'schema','path','binding','source','tool','version','environment',
            'identity','budget','clock','stop','observation','tuple','capability','auth'} else 'schema'
        super().__init__(self.reason)


def _need(value, reason='schema'):
    if not value:
        raise LeaseRefused(reason)


def _obj(value, keys, reason='schema'):
    _need(type(value) is dict and set(value) == set(keys),reason)


def _int(value, low=0, high=2**32-1, reason='schema'):
    _need(type(value) is int and low <= value <= high,reason)


def _same(left, right):
    if type(left) is not type(right):
        return False
    if type(left) is dict:
        return left.keys() == right.keys() and all(_same(left[k],right[k]) for k in left)
    if type(left) in (list,tuple):
        return len(left) == len(right) and all(_same(a,b) for a,b in zip(left,right))
    return left == right


def _path(value, *, project=False):
    _need(type(value) is str and 0 < len(value) <= 32768 and
          not any(ord(c) < 32 for c in value),'path')
    path = PureWindowsPath(value)
    _need(path.is_absolute() and path.drive.upper() in ({'D:'} if project else {'C:','D:'}),'path')
    pieces = re.split(r'[\\/]',value)
    _need(len(pieces) >= 3 and all(p and p not in ('.','..') and not p.endswith((' ','.')) and
          not any(c in '<>:"|?*' for c in p) and re.fullmatch(
              r'(?i)(?:con|prn|aux|nul|com[1-9]|lpt[1-9])(?:\..*)?',p) is None
          for p in pieces[1:]),'path')
    return path


def _binding(value, *, project=False):
    _obj(value,('path','bytes','sha256'),'binding')
    _path(value['path'],project=project); _int(value['bytes'],0,64*1024*1024,'binding')
    _need(type(value['sha256']) is str and re.fullmatch('[0-9a-f]{64}',value['sha256']) is not None,'binding')


def _process(value):
    _obj(value,('pid','creation_filetime','executable'),'identity')
    _int(value['pid'],1,reason='identity'); _int(value['creation_filetime'],1,2**64-1,'identity')
    _path(value['executable'])


def _sources(value):
    _need(type(value) is list and len(value) in (10,11),'source')
    for pin in value:
        _binding(pin,project=True)
    paths = [pin['path'] for pin in value]
    _need(paths == sorted(set(paths)),'source')
    parsed = [PureWindowsPath(path) for path in paths]
    names = {p.name for p in parsed}
    _need(names in (SOURCE_NAMES,SOURCE_NAMES|{'__init__.py'}) and len(names) == len(parsed) and
          len({p.parent for p in parsed}) == 1 and parsed[0].parent.name == 'benchmarks','source')


def port_for_protocol(protocol):
    """Select one fixed profile; public metadata is not execution authority."""
    _need(type(protocol) is str and protocol in (PROTOCOL,PHONE_PROTOCOL))
    return PHONE_PORT if protocol == PHONE_PROTOCOL else PORT


def _port(port):
    _need(type(port) is int and port in (PORT,PHONE_PORT),'tuple')
    return port


def validate_admission(value):
    try:
        _obj(value,ADMISSION_KEYS)
        _int(value['version'],1,1); port = port_for_protocol(value['protocol'])
        _need(type(value['run_id']) is str and re.fullmatch('[0-9a-f]{32}',value['run_id']) is not None)
        _path(value['root'],project=True); _int(value['port'],port,port)
        _int(value['seconds'],30,120 if value['protocol'] == PHONE_PROTOCOL else 1700,'budget')
        _binding(value['adb']); _need(value['adb']['sha256'] == ADB_SHA256,'tool')
        _need(PureWindowsPath(value['adb']['path']).name == 'adb.exe','tool')
        tools = value['tools']; _need(type(tools) is list and len(tools) == len(TOOL_NAMES),'tool')
        for pin in tools:
            _binding(pin)
        paths = [pin['path'] for pin in tools]; parsed = [PureWindowsPath(path) for path in paths]
        _need(paths == sorted(set(paths)) and {p.name for p in parsed} == TOOL_NAMES and
              len({p.parent for p in parsed}) == 1 and parsed[0].parent.name == 'platform-tools' and
              value['adb'] in tools,'tool')
        _need(value['sdk_version'] == SDK_VERSION and value['expected_version'] == '0029','version')
        _sources(value['sources'])
        _obj(value['python'],('executable','runtime_dll'),'source')
        _binding(value['python']['executable'])
        if value['python']['runtime_dll'] is not None:
            _binding(value['python']['runtime_dll'])
        auth = _path(value['auth_key'])
        _need(auth.name == 'adbkey' and auth.parent.name == '.android','auth')
        for key,suffix in (('capabilities','.json'),('source_review','.md')):
            _binding(value[key],project=True)
            reference = PureWindowsPath(value[key]['path'])
            _need(reference.suffix.casefold() == suffix and
                  '.android' not in (part.casefold() for part in reference.parts),'auth')
        return copy.deepcopy(value)
    except LeaseRefused:
        raise
    except (ValueError,TypeError,KeyError,AttributeError,RecursionError):
        raise LeaseRefused('schema') from None


def server_command(admission):
    value = validate_admission(admission)
    # ADB accepts only its literal local-host spelling here. This selects the
    # native IPv4 loopback branch; a numeric hostname hits its unsupported path.
    return [value['adb']['path'],'-L','tcp:localhost:%d' % value['port'],'server','nodaemon']


def child_environment(admission, inherited):
    value = validate_admission(admission)
    _need(type(inherited) is dict and all(type(k) is str and type(v) is str and
          k and '=' not in k and '\0' not in k+v for k,v in inherited.items()),'environment')
    aliases = {'ADBHOST','ADBPORT','ADBSERVERPORT','ANDROIDADBPORT','TEMP','TMP','TMPDIR'}
    result = {k:v for k,v in inherited.items() if not k.upper().startswith(('ADB_','ANDROID_')) and k.upper() not in aliases}
    result.update(FIXED_ENV)
    if value['protocol'] == PHONE_PROTOCOL:
        result['ADB_USB'] = '1'
    result['ANDROID_ADB_LOG_PATH'] = str(PureWindowsPath(value['root'])/'adb.log')
    return result


def validate_running(value, admission, admission_binding):
    admitted = validate_admission(admission); _binding(admission_binding,project=True)
    _obj(value,RUNNING_KEYS)
    _int(value['version'],1,1); _need(value['protocol'] == admitted['protocol'])
    _need(_same(value['admission'],admission_binding) and value['run_id'] == admitted['run_id'] and
          type(value['port']) is int and value['port'] == admitted['port'])
    for key in ('owner','worker','server'):
        _process(value[key])
    _need(len({value[k]['pid'] for k in ('owner','worker','server')}) == 3,'identity')
    _need(value['server']['executable'] == admitted['adb']['path'] and
          value['owner']['executable'] == value['worker']['executable'] == admitted['python']['executable']['path'],'identity')
    for key in ('started_epoch','deadline_epoch'):
        _need(type(value[key]) in (int,float) and math.isfinite(value[key]) and value[key] > 0,'clock')
    _need(value['deadline_epoch']-value['started_epoch'] == admitted['seconds'],'clock')
    _need(_same(value['sources'],admitted['sources']) and _same(value['adb'],admitted['adb']),'source')
    for key,name in (('version_proof','proof-version-v1.json'),('devices_proof','proof-devices-v1.json')):
        if admitted['protocol'] == PHONE_PROTOCOL:
            _need(value[key] is None,'capability')
        else:
            _binding(value[key],project=True)
            _need(PureWindowsPath(value[key]['path']) == PureWindowsPath(admitted['root'])/name,'binding')
    return copy.deepcopy(value)


def check_stop(value, admission_sha256, protocol=PROTOCOL):
    port_for_protocol(protocol)
    _need(type(admission_sha256) is str and re.fullmatch('[0-9a-f]{64}',admission_sha256) is not None,'stop')
    _obj(value,('version','protocol','admission_sha256','action'),'stop')
    _int(value['version'],1,1,'stop')
    _need(value['protocol'] == protocol and value['admission_sha256'] == admission_sha256 and value['action'] == 'stop','stop')


def validate_observation(value, server, client, endpoint, *, require_empty=False,
                         after_request=False, completed_ports=(), port=PORT):
    from benchmarks.windows_tcp_observation import decode_table
    port = _port(port)
    _need(type(require_empty) is bool and type(after_request) is bool,'observation')
    _need(type(completed_ports) is tuple and len(completed_ports) <= 2,'tuple')
    for completed in completed_ports:
        _int(completed,1,65535,'tuple'); _need(completed not in (PHONE_PORT,PORT),'tuple')
    _need(len(set(completed_ports)) == len(completed_ports),'tuple')
    _obj(value,('version','port','rows','families'),'observation')
    _int(value['version'],1,1); _int(value['port'],port,port)
    _need(_same(value['families'],[2,23]),'observation')
    rows = value['rows']; _need(type(rows) is list and len(rows) <= 64,'observation')
    decoded,ordinals = [],set()
    for row in rows:
        _obj(row,ROW_KEYS,'observation')
        _need(type(row['family']) is int and row['family'] in (2,23),'observation')
        _int(row['ordinal'],0,16383,'observation')
        key = row['family'],row['ordinal']; _need(key not in ordinals,'observation'); ordinals.add(key)
        size = 24 if row['family'] == 2 else 56
        _need(type(row['raw_hex']) is str and len(row['raw_hex']) == size*2 and
              re.fullmatch('[0-9a-f]+',row['raw_hex']) is not None,'observation')
        item = decode_table(struct.pack('<I',1)+bytes.fromhex(row['raw_hex']),row['family'])[0]
        fields = {k:getattr(item,k) for k in ROW_KEYS-{'raw_hex','ordinal'}}
        _need(_same(fields,{k:row[k] for k in fields}),'observation')
        decoded.append(row)
    if require_empty:
        _need(server is client is endpoint is None and not after_request and not completed_ports and not rows,'observation')
        return None
    _process(server)
    _need((client is None) == (endpoint is None),'tuple')
    if endpoint is not None:
        _process(client); _need(client['pid'] != server['pid'],'identity')
        _obj(endpoint,('local_address','local_port','peer_address','peer_port'),'tuple')
        _need(endpoint['local_address'] == endpoint['peer_address'] == '127.0.0.1','tuple')
        _int(endpoint['peer_port'],port,port,'tuple'); _int(endpoint['local_port'],1,65535,'tuple')
        _need(endpoint['local_port'] not in (PORT,PHONE_PORT,*completed_ports),'tuple')
    else:
        _need(not after_request,'tuple')
    candidates,servers,clients,historical = [],[],[],set()
    for row in decoded:
        _need(row['family'] == 2 and row['local_address'] == '127.0.0.1' and
              row['local_scope_id'] == row['remote_scope_id'] == 0,'observation')
        if row['local_port'] == port and row['remote_address'] == '0.0.0.0' and row['remote_port'] == 0:
            candidates.append(row); _need(row['pid'] == server['pid'],'identity')
        elif endpoint is not None and row['local_port'] == port and row['remote_address'] == '127.0.0.1' and row['remote_port'] == endpoint['local_port']:
            servers.append(row); _need(row['pid'] in ((0,server['pid']) if after_request else (server['pid'],)),'identity')
        elif endpoint is not None and row['local_port'] == endpoint['local_port'] and row['remote_address'] == '127.0.0.1' and row['remote_port'] == port:
            clients.append(row); _need(row['pid'] in ((0,client['pid']) if after_request else (client['pid'],)),'identity')
        elif row['local_port'] == port and row['remote_address'] == '127.0.0.1' and row['remote_port'] in completed_ports:
            _need(row['pid'] in (0,server['pid']),'identity')
            _need(row['remote_port'] not in historical,'tuple'); historical.add(row['remote_port'])
        else:
            raise LeaseRefused('tuple')
    _need(len(candidates) == 1,'observation')
    if endpoint is not None:
        _need(len(servers) <= 1 and len(clients) <= 1,'tuple')
        if not after_request:
            _need(len(servers) == len(clients) == 1,'tuple')
    return None


def source_bindings():
    from benchmarks import receipt_avd_environment as env
    root = Path(__file__).resolve().parents[1]
    _need(root.drive.upper() == 'D:' and root.resolve(strict=True) == root,'source')
    names = set(SOURCE_NAMES)
    if (root/'benchmarks/__init__.py').exists():
        names.add('__init__.py')
    return [env.binding(root/'benchmarks'/name) for name in sorted(names)]


def _read_bound(pin, *, project=True, cap=2*1024*1024):
    from benchmarks import receipt_avd_environment as env
    _binding(pin,project=project); path = env.safe_path(pin['path'])
    _need(not project or path.resolve(strict=True) == path and
          all(not os.path.lexists(p/'.git') for p in (path,*path.parents)),'path')
    env.check_binding(pin); _need(pin['bytes'] <= cap,'binding')
    with path.open('rb') as source:
        raw = source.read(cap+1)
    env.check_binding(pin)
    _need(len(raw) == pin['bytes'] and hashlib.sha256(raw).hexdigest() == pin['sha256'],'binding')
    return raw


def validate_capabilities(binding, admission):
    from benchmarks import receipt_avd_environment as env
    admitted = validate_admission(admission); _need(_same(binding,admitted['capabilities']),'capability')
    value = env.decode_json(_read_bound(binding)); base = Path(binding['path']).parent
    _obj(value,('version','passed','offline_CLI_calls','server_requests','device_calls','sources_equal','rows'),'capability')
    _int(value['version'],1,1); _int(value['offline_CLI_calls'],2,2)
    _int(value['server_requests'],0,0); _int(value['device_calls'],0,0)
    _need(value['passed'] is True and value['sources_equal'] is True,'capability')
    _need(type(value['rows']) is list and len(value['rows']) == 2,'capability')
    outputs = []
    for index,command,row in zip((1,2),('version','help'),value['rows']):
        _obj(row,('index','argv','owner','stdout'),'capability'); _int(row['index'],index,index)
        _need(_same(row['argv'],[admitted['adb']['path'],command]),'capability')
        owner = row['owner']; _obj(owner,('status','elapsed_ms','returncode','cleanup_complete','stderr_bytes'),'capability')
        _need(owner['status'] == 'completed' and owner['cleanup_complete'] is True,'capability')
        _int(owner['elapsed_ms'],0,15000); _int(owner['returncode'],0,0); _int(owner['stderr_bytes'],0,0)
        _need(Path(row['stdout']['path']) == base/('command-%02d.stdout.bin' % index),'capability')
        outputs.append(_read_bound(row['stdout']).decode('utf-8'))
    _need(outputs[0].splitlines()[:2] == ['Android Debug Bridge version 1.0.41','Version '+SDK_VERSION],'capability')
    _need(all(token in outputs[1] for token in ('-L SOCKET','server nodaemon','ADB_LOCAL_TRANSPORT_MAX_PORT','ADB_MDNS_AUTO_CONNECT')),'capability')
    return copy.deepcopy(value)


def revalidate_inputs(admission):
    """Explicit local byte checks; no native API, credentials or server request."""
    from benchmarks import receipt_avd_environment as env
    from benchmarks import adb_held_socket_probe as probe
    value = validate_admission(admission)
    _need(_same(value['sources'],source_bindings()) and _same(value['python'],probe._python_bindings()),'source')
    for pin in value['sources']+value['tools']+[value['source_review']]:
        env.check_binding(pin)
    validate_capabilities(value['capabilities'],value)
    raw = _read_bound(value['adb'],project=False,cap=16*1024*1024)
    _need(all(name+b'\0' in raw for name in (b'ADB_USB',b'ADB_EMU',b'ADB_MDNS')),'tool')
    _read_bound(value['source_review'])
    return None


AUTH_META_KEYS = {'volume_serial','file_index','bytes','attributes','creation_filetime','write_filetime','links'}
CLEANUP_KEYS = {'server_terminate_attempted','server_wait_completed','server_process_handle_closed',
    'server_pipes_closed','server_output_capture_complete','auth_handle_closed','process_handles_closed',
    'preflight_sockets_closed','client_sockets_closed'}
PROOF_KEYS = {'version','protocol','kind','admission','worker','server','client','endpoint','brackets',
    'observations','tables','request_hex','request_sent','response_hex','response_complete','elapsed_ms',
    'socket_closed','client_handle_closed','completed_ports'}
WORKER_KEYS = {'version','protocol','admission','request','worker','server','auth','preflight','readiness',
    'proofs','running','stop_requested','reason','elapsed_ms','server_returncode','server_capture','cleanup','sources_after'}


def _json_bound(pin):
    from benchmarks import receipt_avd_environment as env
    return env.decode_json(_read_bound(pin))


def _auth(value, admission):
    _obj(value,('path','native_profile','metadata'),'auth')
    _need(value['path'] == admission['auth_key'] and
          _path(value['native_profile']) == PureWindowsPath(value['path']).parent.parent,'auth')
    meta = value['metadata']; _obj(meta,AUTH_META_KEYS,'auth')
    for key in ('volume_serial','attributes'):
        _int(meta[key],reason='auth')
    _int(meta['file_index'],0,2**64-1,'auth'); _int(meta['bytes'],1,2**63-1,'auth')
    _int(meta['creation_filetime'],1,2**64-1,'auth'); _int(meta['write_filetime'],1,2**64-1,'auth')
    _int(meta['links'],1,2**32-1,'auth')
    _need(meta['attributes'] & (0x10|0x400) == 0,'auth')


def _tables(value, observation):
    _need(type(value) is list and len(value) == 2,'observation')
    for item,family in zip(value,(2,23)):
        _obj(item,('family','table_class','allocated_bytes','returned_bytes','count','raw_sha256','abi_checked'),'observation')
        _int(item['family'],family,family); _int(item['table_class'],5,5)
        _int(item['allocated_bytes'],4,1024*1024); _int(item['returned_bytes'],4,item['allocated_bytes'])
        _int(item['count'],0,16384); _need(item['abi_checked'] is True,'observation')
        _need(type(item['raw_sha256']) is str and re.fullmatch('[0-9a-f]{64}',item['raw_sha256']) is not None,'observation')
        _need(4+item['count']*(24 if family == 2 else 56) <= item['returned_bytes'],'observation')
        for row in observation['rows']:
            if row['family'] == family:
                _need(row['ordinal'] < item['count'],'observation')


def validate_proof(binding, admission, admission_binding, worker, server, kind, *, completed_ports=()):
    """Replay one closed owned-lease exchange; never query its former socket."""
    admitted = validate_admission(admission); _binding(admission_binding,project=True)
    _need(admitted['protocol'] == PROTOCOL and kind in ('version','devices'),'schema'); _binding(binding,project=True)
    _need(type(completed_ports) is tuple,'tuple')
    _need(PureWindowsPath(binding['path']) == PureWindowsPath(admitted['root'])/('proof-%s-v1.json'%kind),'binding')
    value = _json_bound(binding); _obj(value,PROOF_KEYS)
    _int(value['version'],1,1); _need(value['protocol'] == PROTOCOL and value['kind'] == kind)
    _need(_same(value['admission'],admission_binding),'binding')
    for key,expected in (('worker',worker),('client',worker),('server',server)):
        _process(expected); _need(_same(value[key],expected),'identity')
    _need(_same(value['completed_ports'],list(completed_ports)),'tuple')
    endpoint = value['endpoint']
    _obj(value['observations'],('before_send','after_request'),'observation')
    _obj(value['tables'],('before_send','after_request'),'observation')
    for phase in ('before_send','after_request'):
        obs = value['observations'][phase]
        validate_observation(obs,server,worker,endpoint,after_request=phase=='after_request',completed_ports=completed_ports)
        _tables(value['tables'][phase],obs)
    _obj(value['brackets'],('before_connect','before_send','after_response'),'identity')
    baseline_auth = baseline_socket = None
    for phase in ('before_connect','before_send','after_response'):
        bracket = value['brackets'][phase]
        _obj(bracket,('worker','server','sources','tools','auth','server_alive','socket'),'identity')
        _need(_same(bracket['worker'],worker) and _same(bracket['server'],server) and bracket['server_alive'] is True,'identity')
        _need(_same(bracket['sources'],admitted['sources']) and _same(bracket['tools'],admitted['tools']),'source')
        _auth(bracket['auth'],admitted)
        sock = bracket['socket']; _obj(sock,('handle','socket_id','local_address','local_port'),'tuple')
        _int(sock['handle'],1,2**64-1,'tuple'); _int(sock['socket_id'],1,2**64-1,'tuple')
        _need(sock['local_address'] == endpoint['local_address'] and
              type(sock['local_port']) is int and sock['local_port'] == endpoint['local_port'],'tuple')
        if phase == 'before_connect':
            baseline_auth,baseline_socket = bracket['auth'],sock
        else:
            _need(_same(bracket['auth'],baseline_auth) and _same(sock,baseline_socket),'identity')
    request,response = ((b'000Chost:version',b'OKAY00040029') if kind=='version' else
                        (b'000Ehost:devices-l',b'OKAY0000'))
    _need(value['request_hex'] == request.hex() and value['response_hex'] == response.hex(),'capability')
    _need(all(value[k] is True for k in ('request_sent','response_complete','socket_closed','client_handle_closed')),'capability')
    _int(value['elapsed_ms'],0,3000,'budget')
    return copy.deepcopy(value)


def validate_worker_result(binding, admission, admission_binding, request_binding, expected_worker):
    """Deep closed replay after the actual admitted worker has terminated."""
    admitted = validate_admission(admission)
    for pin in (binding,admission_binding,request_binding):
        _binding(pin,project=True)
    root = PureWindowsPath(admitted['root'])
    _need(PureWindowsPath(binding['path']) == root/'worker-result-v1.json','binding')
    _need(PureWindowsPath(request_binding['path']) == root/'request-v1.json','binding')
    value = _json_bound(binding); _obj(value,WORKER_KEYS)
    _int(value['version'],1,1); _need(value['protocol'] == admitted['protocol'])
    _need(_same(value['admission'],admission_binding) and _same(value['request'],request_binding),'binding')
    _process(expected_worker); _need(_same(value['worker'],expected_worker),'identity')
    server = value['server']; _process(server)
    _need(server['executable'] == admitted['adb']['path'] and server['pid'] != expected_worker['pid'],'identity')
    _auth(value['auth'],admitted)
    _need(type(value['stop_requested']) is bool and value['reason'] in ('stop_requested','expired') and
          value['stop_requested'] == (value['reason']=='stop_requested'),'stop')
    _int(value['elapsed_ms'],0,(admitted['seconds']+30)*1000,'budget')
    _int(value['server_returncode'],-2**31,2**32-1,'identity')
    _obj(value['cleanup'],CLEANUP_KEYS,'identity'); _need(all(v is True for v in value['cleanup'].values()),'identity')
    _binding(value['server_capture'],project=True)
    _need(PureWindowsPath(value['server_capture']['path']) == root/'server-capture-v1.json','binding')
    capture = _json_bound(value['server_capture'])
    _obj(capture,('version','protocol','server','status','returncode','stdout','stderr','stdout_bytes','stderr_bytes',
                  'capture_complete','pipes_closed'),'binding')
    _int(capture['version'],1,1); _need(capture['protocol'] == admitted['protocol'])
    _need(_same(capture['server'],server) and capture['status'] == 'terminated' and
          type(capture['returncode']) is int and capture['returncode'] == value['server_returncode'] and
          capture['capture_complete'] is True and capture['pipes_closed'] is True,'identity')
    for channel in ('stdout','stderr'):
        _int(capture[channel+'_bytes'],0,262144,'binding')
        _binding(capture[channel],project=True)
        _need(PureWindowsPath(capture[channel]['path']) == root/'server-output-v1'/('owner-'+channel+'-v1.bin'),'binding')
        raw = _read_bound(capture[channel]); _need(len(raw) == capture[channel+'_bytes'],'binding')
    _need(capture['stdout_bytes']+capture['stderr_bytes'] <= 262144,'binding')
    after = value['sources_after']; _obj(after,('sources','python','tools','auth'),'source')
    _need(_same(after,dict(sources=admitted['sources'],python=admitted['python'],tools=admitted['tools'],auth=value['auth'])),'source')
    _binding(value['preflight'],project=True)
    _need(PureWindowsPath(value['preflight']['path']) == root/'preflight-v1.json','binding')
    pre = _json_bound(value['preflight'])
    _obj(pre,('observation','tables','created_mask','close_attempted_mask','closed_mask','exclusive_bind_succeeded'))
    validate_observation(pre['observation'],None,None,None,require_empty=True,port=admitted['port']); _tables(pre['tables'],pre['observation'])
    for key in ('created_mask','close_attempted_mask','closed_mask'):
        _int(pre[key],1,1)
    _need(pre['exclusive_bind_succeeded'] is True,'observation')
    _binding(value['readiness'],project=True)
    _need(PureWindowsPath(value['readiness']['path']) == root/'readiness-v1.json','binding')
    readiness = _json_bound(value['readiness']); _need(type(readiness) is list and 1 <= len(readiness) <= 200,'observation')
    for index,entry in enumerate(readiness):
        _obj(entry,('observation','tables'))
        if index < len(readiness)-1:
            validate_observation(entry['observation'],None,None,None,require_empty=True,port=admitted['port'])
        else:
            validate_observation(entry['observation'],server,None,None,port=admitted['port'])
        _tables(entry['tables'],entry['observation'])
    _need(type(value['proofs']) is list and len(value['proofs']) == (0 if admitted['protocol'] == PHONE_PROTOCOL else 2),'capability')
    history = ()
    for kind,pin in zip(('version','devices'),value['proofs']):
        proof = validate_proof(pin,admitted,admission_binding,expected_worker,server,kind,completed_ports=history)
        _need(_same(proof['brackets']['before_connect']['auth'],value['auth']),'auth')
        history += (proof['endpoint']['local_port'],)
    _binding(value['running'],project=True)
    _need(PureWindowsPath(value['running']['path']) == root/'running-v1.json','binding')
    running = validate_running(_json_bound(value['running']),admitted,admission_binding)
    request = _json_bound(request_binding)
    _obj(request,('version','protocol','admission','validated_admission','owner','sources','python','worker_script','owner_seconds'))
    _int(request['version'],1,1); _need(request['protocol'] == admitted['protocol'])
    _process(request['owner'])
    script = next(pin for pin in admitted['sources'] if PureWindowsPath(pin['path']).name == 'isolated_adb_owner.py')
    _need(_same(request['admission'],admission_binding) and _same(request['validated_admission'],admitted) and
          _same(request['sources'],admitted['sources']) and _same(request['python'],admitted['python']) and
          _same(request['worker_script'],script),'source')
    _int(request['owner_seconds'],admitted['seconds']+30,admitted['seconds']+30,'budget')
    _need(_same(running['worker'],expected_worker) and _same(running['server'],server) and
          _same(running['owner'],request['owner']),'identity')
    if admitted['protocol'] == PROTOCOL:
        _need(_same(running['version_proof'],value['proofs'][0]) and
              _same(running['devices_proof'],value['proofs'][1]),'identity')
    return copy.deepcopy(value)
