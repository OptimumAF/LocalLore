"""Strict owned-emulator authority and direct shell-v2 contracts; no import IO.

Copyright 2026 LocalLore contributors. SPDX-License-Identifier: Apache-2.0
"""
import copy
import hashlib
import math
import os
from pathlib import Path, PureWindowsPath
import re
import struct

from benchmarks import isolated_adb_lease as base

PROTOCOL='owned-emulator-target-v1'
SDK_PROTOCOL='sdk-owned-target-v1'
PROOF_PROTOCOL='owned-target-socket-proof-v1'
PORT=15937
APP='org.locallore.app.litertverify'
TEST=APP+'.test'
CLASS='org.locallore.app.OriginalAuthorModelInstrumentedTest'
METHODS=('importsTheVerifiedOriginalAuthorModelOnce','recordsOneRealAuthorCreationAndInferenceFreeReopen')
GUEST_ROOT=PureWindowsPath('D:/Dev/Experiments/LocalLore/2026-10-28-author-player-contract-v1/avd-v1')
MODEL_BYTES=2588147712
MODEL_SHA256='181938105e0eefd105961417e8da75903eacda102c4fce9ce90f50b97139a63c'
SOURCE_NAMES=base.SOURCE_NAMES|{'owned_target_contract.py','owned_target_owner.py',
 'android_process_client_v4.py','android_process_verification_v4.py'}
ADMISSION_KEYS={'version','protocol','run_id','root','seconds','server','guest','artifacts','sources','python','compatibility'}
GUEST_KEYS={'root','proposal','authorization','emulator','qemu','refuser','refuser_source',
 'console_port','adb_port','serial','memory_mib','cores','max_seconds','api','abi'}
RUNNING_KEYS={'version','protocol','admission','run_id','root','owner','worker','server','launcher','guest',
 'guest_ancestry','started_epoch','deadline_epoch','sdk_port','console_port','adb_port','serial','transport_id','sources','python','ready'}
SESSION_KEYS={'version','protocol','admission','running','descriptor','caller','sources','python','root','seconds','started_epoch','deadline_epoch'}
CONTEXT_KEYS={'index','phase','label','operation_sha256','transport_id'}
PROOF_KEYS={'version','protocol','session','context','admission','running','caller','endpoint','anchor','brackets',
 'observation','tables','version_response_hex','devices_response_hex','after_request','elapsed_ms'}
BRACKET_KEYS={'owner','worker','server','launcher','guest','sources','python','server_alive','guest_alive'}
CLIENT_KEYS={'version','protocol','session','index','label','operation','operation_sha256','transport_id','status','returncode',
 'cleanup_complete','elapsed_ms','effective_deadline_ms','stdout','stderr','stdin_sha256','stdin_bytes','stdin_complete',
 'server_before','server_after','client_qualified','socket_closed','sender_joined','input_closed'}

TargetRefused=base.LeaseRefused
_need=base._need
_obj=base._obj
_int=base._int
_same=base._same
_path=base._path
_process=base._process


def binding(value, *, project=True, max_bytes=64*1024*1024):
    _obj(value,('path','bytes','sha256'),'binding');_path(value['path'],project=project)
    _int(value['bytes'],0,max_bytes,'binding')
    _need(type(value['sha256'])is str and re.fullmatch('[0-9a-f]{64}',value['sha256'])is not None,'binding')
    _need('.android'not in(part.casefold()for part in PureWindowsPath(value['path']).parts),'auth')


def _sources(value):
    _need(type(value)is list and len(value)in(14,15),'source')
    for pin in value:binding(pin)
    paths=[p['path']for p in value];parsed=[PureWindowsPath(p)for p in paths]
    _need(paths==sorted(set(paths))and len({p.parent for p in parsed})==1 and parsed[0].parent.name=='benchmarks','source')
    _need({p.name for p in parsed}in(SOURCE_NAMES,SOURCE_NAMES|{'__init__.py'}),'source')


def validate_admission(value):
    _obj(value,ADMISSION_KEYS);_int(value['version'],1,1);_need(value['protocol']==PROTOCOL)
    _need(type(value['run_id'])is str and re.fullmatch('[0-9a-f]{32}',value['run_id'])is not None)
    root=_path(value['root'],project=True);_int(value['seconds'],1200,1700,'budget')
    server=base.validate_admission(value['server'])
    _need(server['run_id']==value['run_id']and server['seconds']==value['seconds']and
          _path(server['root'],project=True)==root/'server','binding')
    _sources(value['sources']);_need(_same(value['python'],server['python']),'source')
    _need(_same([p for p in value['sources']if PureWindowsPath(p['path']).name in base.SOURCE_NAMES|{'__init__.py'}],
                server['sources']),'source')
    g=value['guest'];_obj(g,GUEST_KEYS)
    _need(_path(g['root'],project=True)==GUEST_ROOT and not root.is_relative_to(GUEST_ROOT)and
          not GUEST_ROOT.is_relative_to(root),'path')
    for key in('proposal','authorization','refuser','refuser_source'):binding(g[key])
    for key in('emulator','qemu'):binding(g[key],project=False)
    for key in('proposal','authorization'):_need(PureWindowsPath(g[key]['path']).suffix=='.json','path')
    _need(PureWindowsPath(g['emulator']['path']).name=='emulator.exe'and
          PureWindowsPath(g['qemu']['path'])==PureWindowsPath(g['emulator']['path']).parent/'qemu/windows-x86_64/qemu-system-x86_64.exe','tool')
    _need(PureWindowsPath(g['refuser']['path']).suffix.lower()=='.exe'and
          PureWindowsPath(g['refuser_source']['path']).name=='deny_adb_client.c','tool')
    for key,wanted in(('console_port',5592),('adb_port',5593),('memory_mib',8192),('cores',4),('max_seconds',1800),('api',35)):
        _int(g[key],wanted,wanted)
    _need(g['serial']=='emulator-5592'and g['abi']=='x86_64')
    a=value['artifacts'];_obj(a,('build','product_apk','test_apk','model','probe'))
    for key in('build','probe'):binding(a[key])
    for key in('product_apk','test_apk'):binding(a[key],max_bytes=256*1024*1024)
    binding(a['model'],max_bytes=4*1024**3)
    _need(a['model']['bytes']==MODEL_BYTES and a['model']['sha256']==MODEL_SHA256,'binding')
    _need(PureWindowsPath(a['probe']['path']).name=='physical_model_probe_v1.txt','binding')
    binding(value['compatibility']);_need(PureWindowsPath(value['compatibility']['path']).suffix=='.md','source')
    return copy.deepcopy(value)


def _clock(start,deadline,seconds):
    for x in(start,deadline):_need(type(x)in(int,float)and math.isfinite(x)and x>0,'clock')
    _need(deadline-start==seconds,'clock')


def validate_running(value, admission, admission_binding):
    a=validate_admission(admission);binding(admission_binding);_obj(value,RUNNING_KEYS)
    _int(value['version'],1,1);_need(value['protocol']==PROTOCOL and _same(value['admission'],admission_binding),'binding')
    for key in('run_id','root','sources','python'):_need(_same(value[key],a[key]),'source')
    expected={'owner':a['python']['executable']['path'],'worker':a['python']['executable']['path'],
     'server':a['server']['adb']['path'],'launcher':a['guest']['emulator']['path'],'guest':a['guest']['qemu']['path']}
    for key,path in expected.items():_process(value[key]);_need(value[key]['executable']==path,'identity')
    _need(len({value[k]['pid']for k in expected})==5,'identity')
    chain=value['guest_ancestry'];_need(type(chain)is list and 2<=len(chain)<=8,'identity')
    for p in chain:_process(p);_need(p['executable']in(expected['launcher'],expected['guest']),'identity')
    _need(_same(chain[0],value['launcher'])and _same(chain[-1],value['guest'])and
          len({p['pid']for p in chain})==len(chain),'identity')
    _need(all(x['creation_filetime']<=y['creation_filetime']for x,y in zip(chain,chain[1:])),'identity')
    _clock(value['started_epoch'],value['deadline_epoch'],a['seconds'])
    for key,wanted in(('sdk_port',PORT),('console_port',5592),('adb_port',5593)):_int(value[key],wanted,wanted)
    _need(value['serial']=='emulator-5592');_int(value['transport_id'],1,2**31-1,'identity')
    binding(value['ready']);_need(PureWindowsPath(value['ready']['path'])==PureWindowsPath(a['root'])/'target-ready-v1.json','binding')
    return copy.deepcopy(value)


def check_stop(value,sha):
    _obj(value,('version','protocol','admission_sha256','action'),'stop');_int(value['version'],1,1,'stop')
    _need(type(sha)is str and re.fullmatch('[0-9a-f]{64}',sha)is not None,'stop')
    _need(value['protocol']==PROTOCOL and value['admission_sha256']==sha and value['action']=='stop','stop')


def validate_session(value,admission):
    a=validate_admission(admission);_obj(value,SESSION_KEYS);_int(value['version'],1,1)
    _need(value['protocol']==SDK_PROTOCOL);binding(value['admission']);binding(value['running'])
    d=validate_running(value['descriptor'],a,value['admission'])
    _need(PureWindowsPath(value['running']['path'])==PureWindowsPath(a['root'])/'running-v1.json','binding')
    _process(value['caller']);_need(value['caller']['executable']==a['python']['executable']['path']and
      value['caller']['pid']not in(d['server']['pid'],d['launcher']['pid'],d['guest']['pid']),'identity')
    _sources(value['sources']);_need(_same(value['sources'],a['sources'])and _same(value['python'],a['python']),'source')
    _path(value['root'],project=True);_int(value['seconds'],1,1700,'budget')
    _clock(value['started_epoch'],value['deadline_epoch'],value['seconds'])
    _need(d['started_epoch']<=value['started_epoch']<value['deadline_epoch']<=d['deadline_epoch'],'clock')
    return copy.deepcopy(value)


def _relative(path):
    _need(type(path)is str and path.startswith(('no_backup/','files/'))and
          all(p and p not in('.','..')and re.fullmatch('[A-Za-z0-9_.-]+',p)is not None for p in path.split('/')),'command')


def validate_operation(value,admission):
    a=validate_admission(admission);_obj(value,('argv','stdin'),'command')
    argv=value['argv'];_need(type(argv)is list and 1<=len(argv)<=64 and all(type(x)is str and x and
      len(x.encode('utf-8'))<=8192 and not any(ord(c)<32 for c in x)for x in argv),'command')
    _need(len(str(argv).encode('utf-8'))<=16384,'command')
    source=value['stdin'];expected=None;ok=False
    apk_paths=('/data/local/tmp/locallore-product-v1.apk','/data/local/tmp/locallore-test-v1.apk')
    if argv[:1]==['getprop']:
        ok=len(argv)==2 and argv[1]in('sys.boot_completed','ro.build.version.sdk','ro.product.cpu.abi','ro.kernel.qemu')
    elif argv==['am','get-current-user']:ok=True
    elif argv[:3]==['am','force-stop','--user']:ok=len(argv)==5 and argv[3]=='0'and argv[4]in(APP,TEST)
    elif argv[:1]==['am']:
        ok=any(argv==['am','instrument','-w','-r','-e','class',CLASS+'#'+m,TEST+'/androidx.test.runner.AndroidJUnitRunner']for m in METHODS)
    elif argv[:1]==['cmd']:
        ok=any(argv==['cmd','package','list','packages','-U','--user','0',p]or
               argv==['cmd','package','path','--user','0',p]for p in(APP,TEST))
    elif argv[:1]==['pm']:ok=any(argv==['pm','install','-r','-t','--user','0',p]for p in apk_paths)
    elif argv[:1]==['sha256sum']:
        ok=len(argv)==2 and(argv[1]in apk_paths or re.fullmatch(r'/data/app/[A-Za-z0-9_~=/.-]+/base\.apk',argv[1])is not None)
        if ok:_need(all(p not in('','.','..')for p in argv[1].split('/')[1:]),'command')
    elif argv==['df','-k','/data']or argv==['cat','/proc/meminfo']or argv==['screencap','-p']:ok=True
    elif argv[:1]==['pidof']:ok=len(argv)==2 and argv[1]in(APP,TEST)
    elif argv[:1]==['dd']:
        for name,path in zip(('product_apk','test_apk'),apk_paths):
            if argv==['dd','of='+path,'bs=65536']:ok=True;expected=a['artifacts'][name]
    elif argv[:4]==['run-as',APP,'--user','0']:
        op=argv[4:]
        if op==['mkdir','-p','no_backup/original-author-source-v1']:ok=True
        elif len(op)==3 and op[0]=='dd'and op[2]=='bs=65536':
            for name,path in(('model','no_backup/original-author-source-v1/model.litertlm'),
                              ('probe','no_backup/original-author-transfer-probe-v1.bin')):
                if op[1]=='of='+path:ok=True;expected=a['artifacts'][name]
        elif len(op)>=2 and op[0]in('cat','sha256sum','stat','ls'):
            for path in op[1:]:_relative(path)
            ok=True
        elif len(op)>=4 and op[:3]==['tar','-cf','-']:
            for path in op[3:]:_relative(path)
            ok=True
    _need(ok and _same(source,expected),'command')
    if source is not None:binding(source,max_bytes=4*1024**3)
    return copy.deepcopy(value)


def operation_digest(value):
    from benchmarks import receipt_avd_environment as env
    _obj(value,('argv','stdin'),'command');return hashlib.sha256(env.encoded(value)).hexdigest()


def _rows(value,port_key,ports):
    from benchmarks.windows_tcp_observation import decode_table
    _obj(value,('version',port_key,'families','rows'),'observation');_int(value['version'],1,1)
    _need(_same(value[port_key],ports)and _same(value['families'],[2,23]),'observation')
    rows=value['rows'];_need(type(rows)is list and len(rows)<=128,'observation');seen=set()
    for row in rows:
        _obj(row,base.ROW_KEYS,'observation');_need(type(row['family'])is int and row['family']in(2,23),'observation')
        _int(row['ordinal'],0,16383,'observation');key=row['family'],row['ordinal'];_need(key not in seen,'observation');seen.add(key)
        size=24 if row['family']==2 else 56
        _need(type(row['raw_hex'])is str and re.fullmatch('[0-9a-f]{%d}'%(size*2),row['raw_hex'])is not None,'observation')
        decoded=decode_table(struct.pack('<I',1)+bytes.fromhex(row['raw_hex']),row['family'])[0]
        fields={k:getattr(decoded,k)for k in base.ROW_KEYS-{'raw_hex','ordinal'}}
        _need(_same(fields,{k:row[k]for k in fields}),'observation')
    return rows


def validate_observation(value,server,caller,endpoint,guest,after=False):
    _need(type(after)is bool,'observation');_process(server);_process(caller);_process(guest)
    _need(len({p['pid']for p in(server,caller,guest)})==3,'identity')
    _obj(endpoint,('local_address','local_port','peer_address','peer_port'),'tuple')
    _need(endpoint['local_address']==endpoint['peer_address']=='127.0.0.1','tuple')
    _int(endpoint['peer_port'],PORT,PORT,'tuple');_int(endpoint['local_port'],1,65535,'tuple')
    local=endpoint['local_port'];_need(local not in(5037,PORT,5592,5593),'tuple')
    listen=sr=cr=0
    for r in _rows(value,'port',PORT):
        _need(r['family']==2 and r['local_address']=='127.0.0.1'and r['local_scope_id']==r['remote_scope_id']==0,'observation')
        if r['local_port']==PORT:
            if r['remote_address']=='0.0.0.0'and r['remote_port']==0:
                listen+=1;_need(r['pid']==server['pid'],'identity')
            else:
                _need(r['remote_address']=='127.0.0.1'and r['remote_port']not in(0,PORT,5037),'tuple')
                if r['remote_port']==local:sr+=1;_need(r['pid']in((0,server['pid'])if after else(server['pid'],)),'identity')
                else:_need(r['pid']in(0,server['pid']),'identity')
        else:
            _need(r['remote_address']=='127.0.0.1'and r['remote_port']==PORT and r['local_port']not in(0,PORT,5037),'tuple')
            if r['local_port']==local:cr+=1;_need(r['pid']in((0,caller['pid'])if after else(caller['pid'],)),'identity')
            else:_need(r['pid']in(0,caller['pid'],guest['pid']),'identity')
    _need(listen==1 and sr<=1 and cr<=1 and(after or sr==cr==1),'observation')


def validate_guest_observation(value,guest,server):
    _process(guest);_process(server);listeners=set()
    for r in _rows(value,'ports',[5592,5593]):
        loop='127.0.0.1'if r['family']==2 else'::1';unspecified='0.0.0.0'if r['family']==2 else'::'
        _need(r['local_address']==loop and r['local_scope_id']==r['remote_scope_id']==0,'observation')
        if r['local_port']in(5592,5593):
            if r['remote_address']==unspecified and r['remote_port']==0:
                key=r['local_port'],r['family'];_need(key not in listeners,'observation');listeners.add(key)
                _need(r['pid']==guest['pid'],'identity')
            else:_need(r['local_port']==5593 and r['remote_address']==loop and r['remote_port']>0 and r['pid']in(0,guest['pid']),'identity')
        else:_need(r['remote_port']==5593 and r['remote_address']==loop and r['pid']in(0,server['pid']),'identity')
    _need((5592,2)in listeners and(5593,2)in listeners,'observation')


def device_transport(raw):
    _need(type(raw)is bytes and 0<len(raw)<=4096,'capability')
    try:lines=raw.decode('ascii').splitlines()
    except UnicodeError:raise TargetRefused('capability')from None
    _need(len(lines)==1,'capability');words=lines[0].split()
    _need(len(words)>=3 and words[:2]==['emulator-5592','device'],'identity')
    ids=[x[13:]for x in words[2:]if x.startswith('transport_id:')]
    _need(len(ids)==1 and re.fullmatch('[1-9][0-9]*',ids[0])is not None,'identity')
    result=int(ids[0]);_int(result,1,2**31-1,'identity');return result


def validate_proof(value,session,context):
    _obj(value,PROOF_KEYS);_int(value['version'],1,1);_need(value['protocol']==PROOF_PROTOCOL)
    _obj(context,CONTEXT_KEYS);_need(_same(value['context'],context),'binding')
    _int(context['index'],1,10000);_need(context['phase']in('before','after')and
      type(context['label'])is str and re.fullmatch('[a-z][a-z0-9_-]{0,47}',context['label'])is not None,'binding')
    _need(type(context['operation_sha256'])is str and re.fullmatch('[0-9a-f]{64}',context['operation_sha256'])is not None,'binding')
    d=session['descriptor'];_need(type(context['transport_id'])is int and context['transport_id']==d['transport_id'],'identity')
    binding(value['session']);_need(PureWindowsPath(value['session']['path'])==PureWindowsPath(session['root'])/'sdk-session-v4.json','binding')
    for key in('admission','running','caller'):_need(_same(value[key],session[key]),'binding')
    _need(value['after_request']is(context['phase']=='after'),'observation')
    _obj(value['anchor'],('handle','socket_id','local_address','local_port'),'tuple')
    for key in('handle','socket_id'):_int(value['anchor'][key],1,2**64-1,'tuple')
    _need(value['anchor']['local_address']==value['endpoint']['local_address']and
          type(value['anchor']['local_port'])is int and value['anchor']['local_port']==value['endpoint']['local_port'],'tuple')
    validate_observation(value['observation'],d['server'],session['caller'],value['endpoint'],d['guest'],after=value['after_request'])
    base._tables(value['tables'],value['observation'])
    _obj(value['brackets'],('before','after'),'identity')
    for bracket in value['brackets'].values():
        _obj(bracket,BRACKET_KEYS,'identity')
        for key in('owner','worker','server','launcher','guest'):_need(_same(bracket[key],d[key]),'identity')
        _need(_same(bracket['sources'],session['sources'])and _same(bracket['python'],session['python']),'source')
        _need(bracket['server_alive']is True and bracket['guest_alive']is True,'identity')
    _need(value['version_response_hex']==b'OKAY00040029'.hex(),'capability')
    raw=value['devices_response_hex'];_need(type(raw)is str and re.fullmatch('[0-9a-f]+',raw)is not None and len(raw)<=8224,'capability')
    data=bytes.fromhex(raw);_need(data[:4]==b'OKAY'and re.fullmatch(b'[0-9a-fA-F]{4}',data[4:8])is not None,'capability')
    _need(len(data)==8+int(data[4:8],16)and device_transport(data[8:])==d['transport_id'],'capability')
    _int(value['elapsed_ms'],0,15000,'budget');return copy.deepcopy(value)


def validate_client_record(value,session):
    _obj(value,CLIENT_KEYS);_int(value['version'],4,4);_need(value['protocol']==SDK_PROTOCOL)
    binding(value['session']);_need(PureWindowsPath(value['session']['path'])==PureWindowsPath(session['root'])/'sdk-session-v4.json','binding')
    _int(value['index'],1,10000);_need(type(value['label'])is str and re.fullmatch('[a-z][a-z0-9_-]{0,47}',value['label'])is not None)
    _need(value['operation_sha256']==operation_digest(value['operation']),'binding')
    _need(type(value['transport_id'])is int and value['transport_id']==session['descriptor']['transport_id'],'identity')
    _need(value['status']in('completed','refused','timeout','io_error','cancelled'),'schema')
    if value['returncode']is not None:_int(value['returncode'],0,255)
    if value['elapsed_ms']is not None:_int(value['elapsed_ms'],0,2**63-1)
    _int(value['effective_deadline_ms'],1,1700000,'budget')
    for key in('cleanup_complete','stdin_complete','client_qualified','socket_closed','sender_joined','input_closed'):
        _need(type(value[key])is bool)
    for key in('stdout','stderr'):binding(value[key],max_bytes=16*1024*1024)
    _int(value['stdin_bytes'],0,4*1024**3,'binding')
    source=value['operation']['stdin']
    if source is None:_need(value['stdin_sha256']is None and value['stdin_bytes']==0,'binding')
    else:
        binding(source,max_bytes=4*1024**3)
        _need(value['stdin_bytes']<=source['bytes'],'binding')
        if value['stdin_sha256']is not None:_need(type(value['stdin_sha256'])is str and re.fullmatch('[0-9a-f]{64}',value['stdin_sha256'])is not None,'binding')
        if value['stdin_complete']:_need(value['stdin_bytes']==source['bytes']and value['stdin_sha256']==source['sha256'],'binding')
    for key in('server_before','server_after'):
        if value[key]is not None:binding(value[key])
    if value['client_qualified']:
        _need(value['status']=='completed'and type(value['returncode'])is int and value['returncode']==0 and
         value['elapsed_ms']is not None and all(value[k]is True for k in('cleanup_complete','stdin_complete','socket_closed','sender_joined','input_closed'))and
         value['server_before']is not None and value['server_after']is not None,'capability')
    return copy.deepcopy(value)


def source_bindings():
    from benchmarks import receipt_avd_environment as env
    root=Path(__file__).resolve().parents[1];_need(root.drive.upper()=='D:'and root.resolve(strict=True)==root,'source')
    names=SOURCE_NAMES|({'__init__.py'}if(root/'benchmarks/__init__.py').exists()else set())
    return[env.binding(root/'benchmarks'/name)for name in sorted(names)]


def revalidate_inputs(admission):
    from benchmarks import receipt_avd_environment as env
    from benchmarks import adb_held_socket_probe as probe
    a=validate_admission(admission);base.revalidate_inputs(a['server'])
    _need(_same(a['sources'],source_bindings())and _same(a['python'],probe._python_bindings()),'source')
    for pin in a['sources']+[a['compatibility']]+[a['guest'][k]for k in('proposal','authorization','emulator','qemu','refuser','refuser_source')]:env.check_binding(pin)
    # Large model/APK byte hashing belongs to explicit build/transfer gates, not
    # every streaming liveness poll. No credential bytes enter this function.
    return None
