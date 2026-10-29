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

PROTOCOL = 'isolated-adb-lease-v1'
PORT = 15937
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


def validate_admission(value):
    try:
        _obj(value,ADMISSION_KEYS)
        _int(value['version'],1,1); _need(value['protocol'] == PROTOCOL)
        _need(type(value['run_id']) is str and re.fullmatch('[0-9a-f]{32}',value['run_id']) is not None)
        _path(value['root'],project=True); _int(value['port'],PORT,PORT)
        _int(value['seconds'],30,1700,'budget')
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
        _binding(value['capabilities'],project=True); _binding(value['source_review'],project=True)
        return copy.deepcopy(value)
    except LeaseRefused:
        raise
    except (ValueError,TypeError,KeyError,AttributeError,RecursionError):
        raise LeaseRefused('schema') from None


def server_command(admission):
    value = validate_admission(admission)
    return [value['adb']['path'],'-L','tcp:127.0.0.1:%d' % PORT,'server','nodaemon']


def child_environment(admission, inherited):
    value = validate_admission(admission)
    _need(type(inherited) is dict and all(type(k) is str and type(v) is str and
          k and '=' not in k and '\0' not in k+v for k,v in inherited.items()),'environment')
    aliases = {'ADBHOST','ADBPORT','ADBSERVERPORT','ANDROIDADBPORT','TEMP','TMP','TMPDIR'}
    result = {k:v for k,v in inherited.items() if not k.upper().startswith(('ADB_','ANDROID_')) and k.upper() not in aliases}
    result.update(FIXED_ENV)
    result['ANDROID_ADB_LOG_PATH'] = str(PureWindowsPath(value['root'])/'adb.log')
    return result


def validate_running(value, admission, admission_binding):
    admitted = validate_admission(admission); _binding(admission_binding,project=True)
    _obj(value,RUNNING_KEYS)
    _int(value['version'],1,1); _need(value['protocol'] == PROTOCOL)
    _need(_same(value['admission'],admission_binding) and value['run_id'] == admitted['run_id'] and
          type(value['port']) is int and value['port'] == PORT)
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
        _binding(value[key],project=True)
        _need(PureWindowsPath(value[key]['path']) == PureWindowsPath(admitted['root'])/name,'binding')
    return copy.deepcopy(value)


def check_stop(value, admission_sha256):
    _need(type(admission_sha256) is str and re.fullmatch('[0-9a-f]{64}',admission_sha256) is not None,'stop')
    _obj(value,('version','protocol','admission_sha256','action'),'stop')
    _int(value['version'],1,1,'stop')
    _need(value['protocol'] == PROTOCOL and value['admission_sha256'] == admission_sha256 and value['action'] == 'stop','stop')


def validate_observation(value, server, client, endpoint, *, require_empty=False,
                         after_request=False, completed_ports=()):
    from benchmarks.windows_tcp_observation import decode_table
    _need(type(require_empty) is bool and type(after_request) is bool,'observation')
    _need(type(completed_ports) is tuple and len(completed_ports) <= 2,'tuple')
    for port in completed_ports:
        _int(port,1,65535,'tuple'); _need(port not in (5037,PORT),'tuple')
    _need(len(set(completed_ports)) == len(completed_ports),'tuple')
    _obj(value,('version','port','rows','families'),'observation')
    _int(value['version'],1,1); _int(value['port'],PORT,PORT)
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
        _int(endpoint['peer_port'],PORT,PORT,'tuple'); _int(endpoint['local_port'],1,65535,'tuple')
        _need(endpoint['local_port'] not in (PORT,5037,*completed_ports),'tuple')
    else:
        _need(not after_request,'tuple')
    candidates,servers,clients,historical = [],[],[],set()
    for row in decoded:
        _need(row['family'] == 2 and row['local_address'] == '127.0.0.1' and
              row['local_scope_id'] == row['remote_scope_id'] == 0,'observation')
        if row['local_port'] == PORT and row['remote_address'] == '0.0.0.0' and row['remote_port'] == 0:
            candidates.append(row); _need(row['pid'] == server['pid'],'identity')
        elif endpoint is not None and row['local_port'] == PORT and row['remote_address'] == '127.0.0.1' and row['remote_port'] == endpoint['local_port']:
            servers.append(row); _need(row['pid'] in ((0,server['pid']) if after_request else (server['pid'],)),'identity')
        elif endpoint is not None and row['local_port'] == endpoint['local_port'] and row['remote_address'] == '127.0.0.1' and row['remote_port'] == PORT:
            clients.append(row); _need(row['pid'] in ((0,client['pid']) if after_request else (client['pid'],)),'identity')
        elif row['local_port'] == PORT and row['remote_address'] == '127.0.0.1' and row['remote_port'] in completed_ports:
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
