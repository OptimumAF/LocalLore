"""Explicit SDK3 receipts and owned proof acquisition; legacy readers unchanged.

Receipts are source-bound evidence, not independent authentication. No process,
socket, SDK or device is started by importing this module.
Copyright 2026 LocalLore contributors. SPDX-License-Identifier: Apache-2.0
"""
import copy
import hashlib
import math
import os
from pathlib import Path, PureWindowsPath
import re
import sys

from benchmarks import adb_held_socket as held
from benchmarks import adb_held_socket_probe as probe_cli
from benchmarks import receipt_avd_environment as env

ROOT = Path(__file__).resolve().parents[1]
SDK_PROTOCOL = 'sdk-held-server-v3'
BUNDLE_PROTOCOL = 'sdk-held-server-proof-bundle-v1'
MAX_FILE = 16*1024*1024
MAX_BUNDLE = 32*1024*1024
SESSION_KEYS = {'version','protocol','server_admission','admission','sdk_sources','held_sources',
                'python','adb','powershell','owner','launcher'}
CONTEXT_KEYS = {'kind','index','phase','label','command_sha256','transport_id'}
ROW_KEYS = {'version','index','label','status','returncode','cleanup_complete','stdout_bytes','stdout_sha256',
            'stderr_bytes','elapsed_ms','effective_deadline_ms','protocol','server_admission','server_before',
            'server_after','transport_id','command_sha256','argv','client_qualified'}
LAUNCH_FILES = ('request-v1.json','started-v1.json','owner-result-v1.json','source-after-v1.json',
                'owner-stdout-v1.bin','owner-stderr-v1.bin')
HELD_FILES = ('request-v1.json','started-v1.json','owner-result-v1.json','report-v1.json','result-v1.json',
              'source-closure-before-v1.json','source-closure-after-v1.json','source-closure-final-v1.json',
              'python-before-v1.json','python-after-v1.json','python-final-v1.json',
              'owner-stdout-v1.bin','owner-stderr-v1.bin')
PROOF_FILES = tuple(sorted(['launch/'+name for name in LAUNCH_FILES]+['held/'+name for name in HELD_FILES]))
EXTRA_SOURCES = ('benchmarks/android_process_client_v3.py','benchmarks/android_process_verification_v3.py',
                 'benchmarks/android_process_client.py','benchmarks/android_process_verification.py')


class Sdk3Refused(ValueError):
    def __init__(self, reason='schema'):
        self.reason = reason if type(reason) is str and reason in {
            'schema','binding','source','session','proof','owner','budget','command','raw','roster','context','persistence'} else 'schema'
        super().__init__(self.reason)


def _need(value, reason='schema'):
    if not value:
        raise Sdk3Refused(reason)


def _obj(value, keys, reason='schema'):
    _need(type(value) is dict and set(value) == set(keys),reason)
    return value


def _int(value, low=0, high=2**63-1, reason='schema'):
    _need(type(value) is int and low <= value <= high,reason)
    return value


def _sha(value, reason='schema'):
    _need(type(value) is str and re.fullmatch('[0-9a-f]{64}',value) is not None,reason)


def _binding(value):
    _obj(value,('path','bytes','sha256'),'binding')
    _need(type(value['path']) is str and PureWindowsPath(value['path']).is_absolute() and
          not any(ord(char) < 32 for char in value['path']),'binding')
    _int(value['bytes'],0,64*1024*1024,'binding'); _sha(value['sha256'],'binding')
    return value


def _process(value):
    _obj(value,('pid','creation_filetime','executable'),'owner')
    _int(value['pid'],1,2**32-1,'owner'); _int(value['creation_filetime'],1,2**64-1,'owner')
    _need(type(value['executable']) is str and PureWindowsPath(value['executable']).is_absolute() and
          len(value['executable']) <= 32768 and not any(ord(c) < 32 for c in value['executable']),'owner')


def _source_list(value):
    _need(type(value) is list and 1 <= len(value) <= 64,'source')
    for pin in value:
        _binding(pin)
        _need(PureWindowsPath(pin['path']).drive.upper() == 'D:','source')
    names = [pin['path'] for pin in value]
    _need(names == sorted(set(names)),'source')


def sdk_source_bindings():
    names = set(EXTRA_SOURCES) | set(probe_cli.PUBLIC_SOURCES)
    if os.path.lexists(ROOT/'benchmarks/__init__.py'):
        names.add('benchmarks/__init__.py')
    _need(ROOT.drive.upper() == 'D:' and ROOT.resolve(strict=True) == ROOT,'source')
    return [env.binding(ROOT/name) for name in sorted(names)]


def python_bindings():
    return probe_cli._python_bindings()


def validate_session(value):
    _obj(value,SESSION_KEYS,'session')
    _need(type(value['version']) is int and value['version'] == 1 and value['protocol'] == SDK_PROTOCOL,'session')
    _binding(value['server_admission']); admitted = held.validate_admission(value['admission'])
    _source_list(value['sdk_sources']); _source_list(value['held_sources'])
    _need({pin['path'] for pin in value['held_sources']} <= {pin['path'] for pin in value['sdk_sources']},'source')
    for pin in value['held_sources']:
        _need(pin in value['sdk_sources'],'source')
    _obj(value['python'],('executable','runtime_dll'),'source')
    _binding(value['python']['executable'])
    if value['python']['runtime_dll'] is not None:
        _binding(value['python']['runtime_dll'])
    _binding(value['adb']); _binding(value['powershell']); _process(value['owner'])
    if value['launcher'] is not None:
        _process(value['launcher'])
    _need(value['adb']['path'] == admitted['server']['executable'] == admitted['adb_file']['path'] and
          value['adb']['bytes'] == admitted['adb_file']['bytes'] and value['adb']['sha256'] == admitted['adb_file']['sha256'] and
          value['owner']['executable'] == value['python']['executable']['path'] and
          value['owner']['pid'] != admitted['server']['pid'],'session')
    return copy.deepcopy(value)


def command_digest(argv):
    _need(type(argv) is list and 1 <= len(argv) <= 128 and
          all(type(item) is str and 0 < len(item) <= 32768 and '\0' not in item for item in argv),'command')
    raw = env.encoded(argv); _need(len(raw) <= 131072,'command')
    return hashlib.sha256(raw).hexdigest()


def validate_command(argv, adb_path, transport_id):
    command_digest(argv)
    _need(type(adb_path) is str and argv[:5] == [adb_path,'-H','127.0.0.1','-P','5037'],'command')
    operation = argv[5:]
    if transport_id is None:
        _need(operation == ['devices','-l'],'command'); return
    _int(transport_id,1,2**31-1,'command')
    _need(len(operation) >= 3 and operation[:2] == ['-t',str(transport_id)],'command')
    _need(not operation[2].startswith('-') and operation[2] not in {
        'start-server','kill-server','server','fork-server','nodaemon','host','devices','connect',
        'disconnect','pair','mdns','reconnect','track-devices'},'command')


def _context(value):
    _obj(value,CONTEXT_KEYS,'context'); _int(value['index'],1,10000,'context')
    _need(type(value['label']) is str and re.fullmatch('[a-z][a-z0-9_-]{0,47}',value['label']),'context')
    if value['transport_id'] is not None:
        _int(value['transport_id'],1,2**31-1,'context')
    if value['kind'] == 'check':
        _need(value['phase'] == 'check' and value['label'] == 'check-server' and value['command_sha256'] is None,'context')
    else:
        _need(value['kind'] in ('command','external') and value['phase'] in ('before','after'),'context')
        _sha(value['command_sha256'],'context')
        if value['kind'] == 'external':
            _need(value['transport_id'] is not None,'context')
    return copy.deepcopy(value)


def _context_name(context):
    return ('check-%04d' % context['index'] if context['kind'] == 'check' else
            '%s-%04d-%s' % (context['kind'],context['index'],context['phase']))


def _dpath(path, *, directory=False):
    path = env.safe_path(path,directory=directory)
    _need(path.drive.upper() == 'D:' and path.resolve(strict=True) == path,'binding')
    _need(all(not os.path.lexists(parent/'.git') for parent in (path,*path.parents)),'binding')
    return path


def _read_pin(pin):
    _binding(pin); path = _dpath(pin['path'])
    _need(pin['bytes'] <= MAX_FILE,'binding')
    before = path.stat()
    with path.open('rb') as stream:
        held_before = os.fstat(stream.fileno())
        signature = lambda x:(x.st_dev,x.st_ino,x.st_size,x.st_mtime_ns)
        _need(signature(before) == signature(held_before),'binding')
        raw = stream.read(MAX_FILE+1)
        held_after = os.fstat(stream.fileno())
    after = _dpath(path).stat()
    _need(signature(before) == signature(held_after) == signature(after) and
          before.st_ctime_ns == after.st_ctime_ns and held_before.st_ctime_ns == held_after.st_ctime_ns and
          len(raw) == pin['bytes'] == before.st_size and hashlib.sha256(raw).hexdigest() == pin['sha256'],'binding')
    return raw


def _json_pin(pin):
    raw = _read_pin(pin); _need(bool(raw),'binding'); return env.decode_json(raw)


def _decode(raw):
    return env.decode_json(raw)


def _owner(value, stdout, stderr):
    _obj(value,('status','cleanup_complete','elapsed_ms','output_capture_complete',
                'worker_returncode','stdout_bytes','stderr_bytes'),'owner')
    _need(value['status'] == 'child_exited' and type(value['worker_returncode']) is int and
          value['worker_returncode'] == 0 and value['cleanup_complete'] is True and
          value['output_capture_complete'] is True and value['stderr_bytes'] == len(stderr) == 0,'owner')
    for field in ('elapsed_ms','stdout_bytes','stderr_bytes'):
        _int(value[field],reason='owner')
    _need(value['stdout_bytes'] == len(stdout),'owner')


def _cli_command(session, directory):
    return [session['python']['executable']['path'],'-I','-S','-B',str(ROOT/'benchmarks/adb_held_socket_probe.py'),
            '--admission',session['server_admission']['path'],'--admission-sha256',session['server_admission']['sha256'],
            '--output',str(directory/'held')]


def _contents(value, root, expected_session, expected_context, *, manifest_present):
    session = validate_session(expected_session); context = _context(expected_context)
    _obj(value,('version','protocol','session','context','verified','files'),'proof')
    _need(type(value['version']) is int and value['version'] == 1 and value['protocol'] == BUNDLE_PROTOCOL and
          value['verified'] is True and probe_cli._same(value['context'],context),'proof')
    saved_session = validate_session(_json_pin(value['session']))
    _need(probe_cli._same(saved_session,session),'session')
    base = Path(value['session']['path']).parent
    _need(Path(value['session']['path']).name == 'sdk-session-v3.json' and
          root == base/'server-proofs-v3'/_context_name(context),'context')
    files = value['files']; _need(type(files) is list and len(files) == len(PROOF_FILES),'roster')
    _need([entry.get('relative') for entry in files] == list(PROOF_FILES),'roster')
    raw, pins, total = {}, {}, 0
    for entry in files:
        _obj(entry,('relative','binding'),'roster'); name = entry['relative']
        _need(Path(entry['binding']['path']) == root/name,'binding')
        raw[name] = _read_pin(entry['binding']); pins[name] = entry['binding']; total += len(raw[name])
        _need(total <= MAX_BUNDLE,'binding')
    expected_root = {'launch','held'} | ({'bundle-v1.json'} if manifest_present else set())
    _need({p.name for p in root.iterdir()} == expected_root,'roster')
    for folder,leaves in (('launch',LAUNCH_FILES),('held',HELD_FILES)):
        _dpath(root/folder,directory=True)
        _need({p.name for p in (root/folder).iterdir()} == set(leaves),'roster')
    get = lambda name:_decode(raw[name])
    launch = get('launch/request-v1.json')
    _obj(launch,('version','protocol','session','context','caller','sdk_sources','held_sources',
                 'python','command','owner_seconds'),'proof')
    _need(type(launch['version']) is int and launch['version'] == 1 and launch['protocol'] == BUNDLE_PROTOCOL and
          probe_cli._same(launch['session'],value['session']) and probe_cli._same(launch['context'],context) and
          probe_cli._same(launch['caller'],session['owner']) and probe_cli._same(launch['sdk_sources'],session['sdk_sources']) and
          probe_cli._same(launch['held_sources'],session['held_sources']) and probe_cli._same(launch['python'],session['python']) and
          launch['command'] == _cli_command(session,root),'proof')
    _int(launch['owner_seconds'],1,45,'budget')
    after = get('launch/source-after-v1.json')
    _obj(after,('sdk_sources','held_sources','python','caller'),'source')
    _need(probe_cli._same(after,{key:launch[key] for key in after}),'source')
    started = get('launch/started-v1.json'); _obj(started,('CLI',),'owner'); _process(started['CLI'])
    _need(started['CLI']['executable'] == session['python']['executable']['path'] and
          started['CLI']['pid'] != session['owner']['pid'],'owner')
    _owner(get('launch/owner-result-v1.json'),raw['launch/owner-stdout-v1.bin'],raw['launch/owner-stderr-v1.bin'])
    _owner(get('held/owner-result-v1.json'),raw['held/owner-stdout-v1.bin'],raw['held/owner-stderr-v1.bin'])
    _need(probe_cli._same(get('launch/owner-stdout-v1.bin'),dict(status='verified',reason=None,
          acquisition_completed=True,server_proof_verified=True,feature_acceptance=False)) and
          raw['held/owner-stdout-v1.bin'].strip() == b'held_socket_probe_report_acquired','owner')
    request = get('held/request-v1.json')
    _obj(request,('version','protocol','output','admission','validated_admission','owner_seconds',
                  'parent','source_closure','python'),'proof')
    _need(type(request['version']) is int and request['version'] == 1 and request['protocol'] == held.PROTOCOL and
          Path(request['output']) == root/'held' and probe_cli._same(request['admission'],session['server_admission']) and
          probe_cli._same(request['validated_admission'],session['admission']) and type(request['owner_seconds']) is int and
          request['owner_seconds'] == 30 and probe_cli._same(request['parent'],started['CLI']) and
          probe_cli._same(request['source_closure'],session['held_sources']) and probe_cli._same(request['python'],session['python']),'proof')
    inner_started = get('held/started-v1.json'); _obj(inner_started,('worker',),'owner'); _process(inner_started['worker'])
    _need(inner_started['worker']['pid'] not in (started['CLI']['pid'],session['owner']['pid']) and
          inner_started['worker']['executable'] == session['python']['executable']['path'],'owner')
    for phase in ('before','after','final'):
        for prefix,expected in (('source-closure',session['held_sources']),('python',session['python'])):
            item = get('held/%s-%s-v1.json' % (prefix,phase))
            _obj(item,('version','status','reason','bindings'),'source')
            _need(type(item['version']) is int and item['version'] == 1 and item['status'] == 'completed' and
                  item['reason'] is None and probe_cli._same(item['bindings'],expected),'source')
    result = get('held/result-v1.json')
    _obj(result,('version','protocol','status','reason','acquisition_completed','server_proof_verified','feature_acceptance',
                'sources_equal','python_equal','admission','request','owner','report','worker'),'proof')
    _need(type(result['version']) is int and result['version'] == 1 and result['protocol'] == held.PROTOCOL and
          result['status'] == 'verified' and result['reason'] is None and result['feature_acceptance'] is False and
          all(result[key] is True for key in ('acquisition_completed','server_proof_verified','sources_equal','python_equal')) and
          probe_cli._same(result['admission'],session['server_admission']),'proof')
    for key,name in (('request','request-v1.json'),('owner','owner-result-v1.json'),('report','report-v1.json'),('worker','started-v1.json')):
        _need(probe_cli._same(result[key],pins['held/'+name]),'binding')
    report = get('held/report-v1.json')
    _need(held.report_verified(report,session['admission']) and
          probe_cli._same(report['stages'][0]['bracket']['client'],inner_started['worker']),'proof')
    # Privacy/schema replay must agree byte-for-byte with the actual saved JSON.
    _need(probe_cli._report_bytes(report,session['admission']) == raw['held/report-v1.json'],'proof')
    return True


def verify_owned_server_bundle(binding, expected_session, expected_context):
    try:
        _binding(binding); path = _dpath(binding['path'])
        _need(path.name == 'bundle-v1.json','binding')
        return _contents(_json_pin(binding),path.parent,expected_session,expected_context,manifest_present=True)
    except Sdk3Refused:
        raise
    except (OSError,ValueError,TypeError,KeyError,IndexError,AttributeError,OverflowError,RecursionError,env.EnvironmentRefused):
        raise Sdk3Refused('proof') from None


def acquire_owned_server_bundle(directory, session_binding, context, seconds):
    """One fixed host-only CLI. Refused attempts are retained; never retry here."""
    context = _context(context); _int(seconds,1,45,'budget')
    session = validate_session(_json_pin(session_binding))
    _need(probe_cli._same(session['sdk_sources'],sdk_source_bindings()) and
          probe_cli._same(session['held_sources'],probe_cli._source_bindings()) and
          probe_cli._same(session['python'],python_bindings()) and
          probe_cli._same(session['owner'],env.process_identity(os.getpid())),'source')
    _need(held.validate_admission(_json_pin(session['server_admission'])) == session['admission'],'session')
    for pin in session['sdk_sources']+session['held_sources']+[session['adb'],session['powershell']]:
        env.check_binding(pin)
    root = probe_cli.output_control.validate_output(str(directory))
    _need(root == Path(session_binding['path']).parent/'server-proofs-v3'/_context_name(context),'context')
    command = _cli_command(session,root)
    root.mkdir(); (root/'launch').mkdir()
    request = dict(version=1,protocol=BUNDLE_PROTOCOL,session=copy.deepcopy(session_binding),context=context,
        caller=session['owner'],sdk_sources=session['sdk_sources'],held_sources=session['held_sources'],
        python=session['python'],command=command,owner_seconds=seconds)
    env.create_json(root/'launch/request-v1.json',request)
    def started(child):
        env.create_json(root/'launch/started-v1.json',dict(CLI=env.process_identity(child.pid))); return True
    owner = env.supervise(command,b'',root/'launch',seconds,started)
    env.create_json(root/'launch/owner-result-v1.json',owner)
    after = dict(sdk_sources=sdk_source_bindings(),held_sources=probe_cli._source_bindings(),
                 python=python_bindings(),caller=env.process_identity(os.getpid()))
    env.create_json(root/'launch/source-after-v1.json',after)
    files = [dict(relative=name,binding=env.binding(root/name)) for name in PROOF_FILES if (root/name).is_file()]
    value = dict(version=1,protocol=BUNDLE_PROTOCOL,session=copy.deepcopy(session_binding),context=context,verified=True,files=files)
    try:
        _contents(value,root,session,context,manifest_present=False)
        env.check_binding(session_binding); env.check_binding(session['server_admission'])
        for pin in session['sdk_sources']+session['held_sources']+[session['adb'],session['powershell']]:
            env.check_binding(pin)
    except (Sdk3Refused,OSError,ValueError,TypeError,KeyError,IndexError,AttributeError,env.EnvironmentRefused):
        value['verified'] = False
    env.create_json(root/'bundle-v1.json',value)
    return env.binding(root/'bundle-v1.json')


def client_record_shape_v3(value):
    try:
        _obj(value,ROW_KEYS)
        _need(type(value['version']) is int and value['version'] == 3 and value['protocol'] == SDK_PROTOCOL)
        _int(value['index'],1,10000)
        _need(type(value['label']) is str and re.fullmatch('[a-z][a-z0-9_-]{0,47}',value['label']))
        _need(value['status'] in ('completed','timeout','cancelled','output_limit','spawn_failed','cleanup_failed') and
              type(value['cleanup_complete']) is bool and type(value['client_qualified']) is bool)
        _need(value['returncode'] is None or type(value['returncode']) is int and -(2**31) <= value['returncode'] <= 2**32-1)
        _int(value['stdout_bytes'],0,262144); _int(value['stderr_bytes'],0,262144-value['stdout_bytes'])
        _sha(value['stdout_sha256']); _int(value['effective_deadline_ms'],1,180000)
        if value['elapsed_ms'] is None:
            _need(value['status'] == 'spawn_failed' and value['cleanup_complete'] is False and value['returncode'] is None and
                  value['stdout_bytes'] == value['stderr_bytes'] == 0 and value['stdout_sha256'] == hashlib.sha256(b'').hexdigest())
        else:
            _int(value['elapsed_ms'])
        _binding(value['server_admission']); _binding(value['server_before'])
        if value['server_after'] is not None:
            _binding(value['server_after'])
        if value['transport_id'] is not None:
            _int(value['transport_id'],1,2**31-1)
        _need(command_digest(value['argv']) == value['command_sha256'])
        validate_command(value['argv'],value['argv'][0],value['transport_id'])
        if value['client_qualified']:
            _need(value['status'] == 'completed' and type(value['returncode']) is int and value['returncode'] == 0 and
                  value['cleanup_complete'] is True and value['stderr_bytes'] == 0 and
                  value['elapsed_ms'] is not None and value['server_after'] is not None)
        return True
    except (Sdk3Refused,ValueError,TypeError,KeyError,IndexError,OverflowError,RecursionError):
        return False


def require_current_clients_v3(out, count, expected_session):
    try:
        _int(count,1,10000,'roster'); base = _dpath(out,directory=True)
        session = validate_session(expected_session)
        session_pin = env.binding(base/'sdk-session-v3.json')
        _need(probe_cli._same(validate_session(_json_pin(session_pin)),session),'session')
        clients = _dpath(base/'clients',directory=True); proofs = _dpath(base/'server-proofs-v3',directory=True)
        expected_files = {'command-%04d%s' % (i,suffix) for i in range(1,count+1) for suffix in ('.json','.stdout.bin')}
        _need({p.name for p in clients.iterdir()} == expected_files,'roster')
        used = set(); transport = None
        for index in range(1,count+1):
            stem = clients/('command-%04d' % index); row = _json_pin(env.binding(stem.with_suffix('.json')))
            _need(client_record_shape_v3(row) and row['index'] == index and row['client_qualified'] is True,'raw')
            _need(probe_cli._same(row['server_admission'],session['server_admission']),'session')
            if row['transport_id'] is None:
                _need(transport is None,'command')
            else:
                _need(transport is None or transport == row['transport_id'],'command'); transport = row['transport_id']
            validate_command(row['argv'],session['adb']['path'],row['transport_id'])
            raw_pin = env.binding(stem.with_suffix('.stdout.bin')); raw = _read_pin(raw_pin)
            _need(len(raw) == row['stdout_bytes'] and hashlib.sha256(raw).hexdigest() == row['stdout_sha256'],'raw')
            for phase,key in (('before','server_before'),('after','server_after')):
                context = dict(kind='command',index=index,phase=phase,label=row['label'],
                    command_sha256=row['command_sha256'],transport_id=row['transport_id'])
                pin = row[key]; _need(pin['path'] not in used,'proof'); used.add(pin['path'])
                verify_owned_server_bundle(pin,session,context)
        command_dirs = {'command-%04d-%s' % (i,phase) for i in range(1,count+1) for phase in ('before','after')}
        checks, externals = [], {}
        for folder in proofs.iterdir():
            _dpath(folder,directory=True)
            if folder.name in command_dirs:
                continue
            pin = env.binding(folder/'bundle-v1.json'); value = _json_pin(pin); context = _context(value['context'])
            _need(context['kind'] in ('check','external'),'roster')
            verify_owned_server_bundle(pin,session,context)
            if context['kind'] == 'check':
                checks.append(context['index'])
            else:
                externals.setdefault(context['index'],{})[context['phase']] = context
        _need(sorted(checks) == list(range(1,len(checks)+1)),'roster')
        for pair in externals.values():
            _need(set(pair) == {'before','after'} and all(pair['before'][key] == pair['after'][key]
                  for key in ('index','label','command_sha256','transport_id')),'context')
        _need({p.name for p in clients.iterdir()} == expected_files and command_dirs <= {p.name for p in proofs.iterdir()},'roster')
    except Sdk3Refused:
        raise
    except (OSError,ValueError,TypeError,KeyError,IndexError,AttributeError,OverflowError,env.EnvironmentRefused):
        raise Sdk3Refused('proof') from None
