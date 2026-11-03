"""One explicitly approved fresh SDK18 prepare/run; no inferred authority.

The shared environment owns preparation and storage admission; the unchanged
SDK18 activation owns the guest, private server, controller and cleanup. This
bridge joins them under one bounded, barrier-started owner, without recovery.
Copyright 2026 LocalLore contributors. SPDX-License-Identifier: Apache-2.0
"""
import copy
import hashlib
import importlib.util
import json
import math
import os
from pathlib import Path, PurePosixPath, PureWindowsPath
import re
import subprocess
import sys
import threading
import time
from types import SimpleNamespace
import uuid

ROOT=Path(__file__).parents[1]
BARRIER=b'sdk18-fresh-operation-worker-v1\n'
_MODULES=None
_RULES=None
_SOURCE_FILE_COUNT = 2664


def _raw_file(pin, maximum=2*1024**2):
    """Bootstrap exact consumed bytes without importing operational modules."""
    r=_RULES;r.binding(pin,maximum=maximum)
    path=Path(pin['path'])
    for node in (path,*path.parents):
        r.need(node.resolve(strict=True)==node and not node.is_symlink() and
               not getattr(node.lstat(),'st_file_attributes',0)&1024,'source_path')
    r.need(path.is_file() and path.stat().st_nlink==1 and path.stat().st_size==pin['bytes'],'binding')
    with path.open('rb') as stream:
        raw=stream.read(pin['bytes']+1)
    r.need(len(raw)==pin['bytes'] and hashlib.sha256(raw).hexdigest()==pin['sha256'],'binding')
    r.need(path.resolve(strict=True)==path and path.stat().st_nlink==1 and path.stat().st_size==len(raw),'binding')
    return raw


def source_snapshot():
    r=_RULES
    raw=_raw_file(r.SOURCE_PUBLICATION)
    pub=json.loads(raw)
    r.need(type(pub) is dict and pub.get('final_commit')==r.SOURCE_HEAD and
           pub.get('final_tree')==r.SOURCE_TREE and type(pub.get('files')) is list and
           len(pub['files'])==_SOURCE_FILE_COUNT,'source_snapshot')
    rows=pub['files'];names=[];directories=set();tree={}
    for row in rows:
        r.need(type(row) is dict and set(row)=={'path','mode','git_blob','bytes','sha256'},'source_snapshot')
        name=row['path']
        r.need(type(name) is str and name and '\\' not in name and ':' not in name,'source_path')
        relative=PurePosixPath(name)
        r.need(not relative.is_absolute() and relative.as_posix()==name and
               all(part not in ('','.','..') for part in relative.parts),'source_path')
        r.need(row['mode'] in ('100644','100755') and type(row['bytes']) is int and
               0<=row['bytes']<=16*1024**2 and type(row['git_blob']) is str and
               re.fullmatch('[0-9a-f]{40}',row['git_blob']) is not None and
               type(row['sha256']) is str and re.fullmatch('[0-9a-f]{64}',row['sha256']) is not None,'source_snapshot')
        names.append(name)
        directories.update(parent.as_posix() for parent in relative.parents if parent!=PurePosixPath('.'))
        node=tree
        for part in relative.parts[:-1]:
            r.need(part not in node or type(node[part]) is dict,'source_snapshot')
            node=node.setdefault(part,{})
        r.need(relative.name not in node,'source_snapshot')
        node[relative.name]=(row['mode'],row['git_blob'])
    r.need(names==sorted(names) and len(set(names))==len({name.casefold() for name in names})==_SOURCE_FILE_COUNT,'source_snapshot')
    def git_tree(node):
        chunks=[]
        for name,value in sorted(node.items(),key=lambda row:(row[0]+('/' if type(row[1]) is dict else '')).encode('utf-8')):
            mode,oid=('40000',git_tree(value)) if type(value) is dict else value
            chunks.append(mode.encode('ascii')+b' '+name.encode('utf-8')+b'\0'+bytes.fromhex(oid))
        data=b''.join(chunks)
        return hashlib.sha1(b'tree '+str(len(data)).encode('ascii')+b'\0'+data).hexdigest()
    r.need(git_tree(tree)==r.SOURCE_TREE,'source_snapshot')
    for path in (r.SOURCE,*r.SOURCE.parents):
        r.need(path.resolve(strict=True)==path and not path.is_symlink() and
               not getattr(path.lstat(),'st_file_attributes',0)&1024,'source_path')
    r.need(r.SOURCE.is_dir(),'source_path')
    actual_files=set();actual_directories=set()
    for index,path in enumerate(r.SOURCE.rglob('*'),1):
        r.need(index<=4096,'source_snapshot')
        r.need(path.resolve(strict=True)==path and not path.is_symlink() and
               not getattr(path.lstat(),'st_file_attributes',0)&1024,'source_path')
        name=path.relative_to(r.SOURCE).as_posix()
        if path.is_file():actual_files.add(name)
        else:
            r.need(path.is_dir(),'source_path');actual_directories.add(name)
    r.need(actual_files==set(names) and actual_directories==directories,'source_snapshot')
    total=0
    for row in rows:
        p=r.SOURCE/row['path']
        r.need(p.resolve(strict=True)==p and p.is_file() and p.stat().st_nlink==1 and
               p.stat().st_size==row['bytes'],'source_path')
        with p.open('rb') as stream:data=stream.read(row['bytes']+1)
        total+=len(data)
        r.need(total<=64*1024**2 and len(data)==row['bytes'] and
               hashlib.sha256(data).hexdigest()==row['sha256'] and
               hashlib.sha1(b'blob '+str(len(data)).encode()+b'\0'+data).hexdigest()==row['git_blob'],'source_snapshot')
    r.need(_raw_file(r.SOURCE_PUBLICATION)==raw,'source_snapshot')



def _parts():
    global _MODULES,_RULES
    if _RULES is None:
        path=ROOT/'scripts/record_cancellation_ui_fresh_contract.py'
        spec=importlib.util.spec_from_file_location('_sdk18_fresh_rules',path)
        _RULES=importlib.util.module_from_spec(spec);spec.loader.exec_module(_RULES)
    r=_RULES
    r.need(Path(r.__file__).resolve()==ROOT/'scripts/record_cancellation_ui_fresh_contract.py' and
           ROOT==r.OPERATOR_ROOT and Path(__file__)==r.OPERATOR,'contract_source')
    if _MODULES is None:
        source_snapshot()
        sys.path.insert(0,str(r.SOURCE))
        from benchmarks import receipt_avd_environment as env
        from benchmarks import receipt_avd_storage as storage
        from benchmarks import owned_record_cancellation_ui_contract as contract
        from benchmarks import record_cancellation_ui_activation as activation
        from benchmarks import record_cancellation_ui_build as build
        from benchmarks import adb_held_socket_probe as probe
        from benchmarks import isolated_adb_lease as base
        from benchmarks import prepare_recovery_contract as history
        from benchmarks import record_cancellation_ui_profile_build as profile_build
        for name,module in tuple(sys.modules.items()):
            if name=='benchmarks' or name.startswith('benchmarks.'):
                file=getattr(module,'__file__',None)
                if name=='benchmarks' and file is None:
                    r.need(list(module.__path__)==[str(r.SOURCE/'benchmarks')],'module_source')
                else:
                    r.need(file is not None and Path(file).resolve().parent==r.SOURCE/'benchmarks','module_source')
        r.need(storage.DEFAULT_REGISTRY==r.REGISTRY and activation.SOURCE_ROOT==r.SOURCE and
               activation.RUNTIME==r.RUNTIME and activation.CONTROLS==r.CONTROLS and
               Path(contract.GUEST_ROOT)==r.GUEST and contract.CLIENT_VERSION==18 and
               contract.MODEL_MATERIAL is False,'profile')
        activation._source()
        _MODULES=SimpleNamespace(env=env,storage=storage,contract=contract,activation=activation,
            build=build,probe=probe,base=base,history=history,profile_build=profile_build)
    return r,_MODULES


def read(pin, expected=None, maximum=2*1024**2):
    r,api=_parts();r.binding(pin,expected,maximum)
    api.env.check_binding(pin)
    with Path(pin['path']).open('rb') as stream:
        raw=stream.read(pin['bytes']+1)
    r.need(len(raw)==pin['bytes'] and hashlib.sha256(raw).hexdigest()==pin['sha256'],'binding')
    api.env.check_binding(pin)
    return api.env.decode_json(raw)


def save(path, value):
    r,api=_parts();api.env.create_json(path,value);pin=api.env.binding(path)
    r.need(r.same(read(pin,path),value), 'publication')
    return pin


def read_authority(pin):
    r,api=_parts();a=r.validate_authority(read(pin,r.AUTHORITY,16384))
    source_snapshot()
    for role in ('proposal','operator','contract','handoff'):
        api.env.check_binding(a[role])
    r.need(Path(__file__)==r.OPERATOR and ROOT==r.OPERATOR_ROOT,'operator_source')
    return a


def _installed(h):
    r,api=_parts();v=read(r.STATIC)
    r.need(type(v) is dict and set(v)=={'adb','tools','python','capabilities','source_review',
        'compatibility','emulator','qemu','refuser','refuser_source','auth_key_path'} and
        type(v['tools']) is list and 0<len(v['tools'])<=32, 'installed')
    key=v['auth_key_path']
    r.need(type(key) is str and PureWindowsPath(key).is_absolute() and
           not any(ord(c)<32 for c in key), 'key_path')
    # ADB credential path is metadata only; never stat/open/hash/copy key bytes.
    for role in ('adb','capabilities','source_review','compatibility','emulator','qemu','refuser','refuser_source'):
        api.env.check_binding(v[role])
    for pin in v['tools']+[p for p in v['python'].values() if p is not None]:api.env.check_binding(pin)
    r.need(r.same(v['python'],h['python']) and r.same(api.probe._python_bindings(),h['python']), 'python')
    result=copy.deepcopy(v)
    result['refuser_source']=api.env.binding(r.SOURCE/'benchmarks/native/deny_adb_client.c')
    r.need(all(result['refuser_source'][k]==v['refuser_source'][k] for k in ('bytes','sha256')), 'refuser_source')
    return result


def frozen_inputs(authority_pin):
    r,api=_parts();authority=read_authority(authority_pin)
    h=r.validate_handoff(read(r.HANDOFF))
    r.need(r.same(h['sources'],api.contract.source_bindings()),'source_closure')
    for pin in h['sources']+[p for p in h['python'].values() if p is not None]:
        api.env.check_binding(pin)
    r.need(r.same(api.probe._python_bindings(),h['python']),'python')
    proposal=read(h['prepare_proposal']);api.env.validate_proposal(proposal,'prepare')
    r.need(proposal['paths']['root']==str(r.GUEST) and type(proposal['memory_mib']) is int and
           proposal['memory_mib']==8192 and type(proposal['cores']) is int and proposal['cores']==4 and
           proposal['allow_environment_calls'] is False and proposal['root_go_pending'] is True,'profile')
    api.env.verify_installation(proposal);api.env.check_external_state(proposal)
    # Original capacity is historical after separately approved retirement.
    # Current locked admission and authority ledger are checked independently.
    capacity=read(h['capacity_preview'])
    r.need(type(capacity) is dict and capacity.get('scope')=='receipt-avd-prepare-capacity-preview-v1' and
           capacity.get('root')==str(r.GUEST) and capacity.get('admission_granted') is False,'capacity')
    manifest=api.build.verify_frozen_product(h['artifacts'])
    r.need(r.same(read(h['artifacts']['build']),manifest),'build_copy')
    selected=manifest['facts']['selected_methods']
    r.need(r.same([[row['selector'],row['class_name'],row['method']] for row in selected],
                  [list(row) for row in api.contract.INSTRUMENTATIONS]),'build')
    installed=_installed(h)
    api.env.check_binding(authority_pin)
    return authority,h,installed


def _unused():
    r,api=_parts()
    for path in (r.LIVE,r.GUEST,r.RUNTIME,r.CONTROLS):
        api.env.safe_path(path,exists=False)
        r.need(not os.path.lexists(path), 'already_used')
        api.env.safe_path(path.parent,exists=True,directory=True)


def _initial(authority_pin):
    r,api=_parts()
    r.need(os.name=='nt' and Path.cwd()==r.SOURCE and all(Path(os.environ.get(k,''))==Path('D:/Dev/_Temp')
        for k in ('TEMP','TMP','TMPDIR')), 'environment')
    authority,h,_=frozen_inputs(authority_pin);_unused()
    api.env.check_binding(authority['ledger'])
    ledger=read(authority['ledger']);api.storage._validate(ledger,r.REGISTRY)
    r.need(type(ledger['version']) is int and ledger['version']==2, 'ledger_version')
    capacity=api.storage.preview_prepare(r.GUEST)
    r.need(capacity['would_fit'] is True and capacity['admission_granted'] is False and
           r.same(capacity['ledger'],authority['ledger']), 'capacity')
    api.env.check_binding(authority['ledger'])
    return authority,h


def _attempt(authority_pin,authority):
    r,api=_parts();api.env.safe_path(r.LIVE,exists=False);r.LIVE.mkdir()
    record=dict(version=1,scope='sdk18-fresh-operation-attempt-v1',authority=authority_pin,
        handoff=authority['handoff'],operator=authority['operator'],contract=authority['contract'],no_retry=True)
    r.validate_attempt(record,authority_pin,authority)
    return save(r.ATTEMPT,record)


def prepared(authority_pin,prepare_authorization_pin):
    r,api=_parts();_,h,_=frozen_inputs(authority_pin)
    auth=read(prepare_authorization_pin,r.PREPARE_AUTHORIZATION,4096)
    api.env.check_authorization(auth,'prepare',h['prepare_proposal']['sha256'])
    proposal=copy.deepcopy(read(h['prepare_proposal']))
    proposal.update(phase='run',prepare_proposal=h['prepare_proposal'],
        prepared=api.env.binding(r.GUEST/'prepared-v1.json'),
        prepare_result=api.env.binding(r.GUEST/'prepare-result-v1.json'),max_seconds=1800)
    api.env.validate_proposal(proposal,'run');api.env.verify_prepared(proposal,initial=True)
    terminal=read(proposal['prepare_result'],r.GUEST/'prepare-result-v1.json')
    r.need(type(terminal) is dict and set(terminal)=={'version','proposal_sha256','status',
        'closure_verified','child_cleanup_complete','prepared_created'} and
        type(terminal['version']) is int and terminal['version']==1 and terminal['status']=='completed' and
        terminal['proposal_sha256']==h['prepare_proposal']['sha256'] and
        all(terminal[k] is True for k in ('closure_verified','child_cleanup_complete','prepared_created')), 'prepare_terminal')
    pin=api.env.binding(r.REGISTRY/'ledger-v1.json');ledger=read(pin)
    api.storage._validate(ledger,r.REGISTRY);entry=api.storage._entry(ledger,r.GUEST)
    # _validate owns recovery-history validation for recovered entries. Fresh
    # entries have no recovery history and must not enter that validator.
    api.history.require_cleanup(entry)
    r.need(type(ledger['version']) is int and ledger['version']==2 and entry['state']=='prepared' and
           type(entry['reserved_bytes']) is int and entry['reserved_bytes']==40*1024**3 and
           entry['proposal_sha256']==h['prepare_proposal']['sha256'] and entry['closure'] is None and
           entry.get('recovery') is None and entry['retirement'] is None, 'prepared_state')
    r.need(not os.path.lexists(r.GUEST/api.contract.BOOT_CLAIM_FILE), 'already_used')
    api.env.check_binding(pin);api.env.check_binding(prepare_authorization_pin)
    return pin


def create_inputs(authority_pin,prepare_authorization_pin):
    r,api=_parts();_,h,installed=frozen_inputs(authority_pin)
    ledger=prepared(authority_pin,prepare_authorization_pin)
    for path in (r.RUN_PROPOSAL,r.RUN_AUTHORIZATION,r.RUNTIME,r.CONTROLS):
        api.env.safe_path(path,exists=False);r.need(not os.path.lexists(path), 'already_used')
    proposal=api.env.plan_run(h['prepare_proposal']['path'],r.GUEST/'prepared-v1.json',r.RUN_PROPOSAL,max_seconds=1800)
    proposal_pin=api.env.binding(r.RUN_PROPOSAL)
    r.need(r.same(read(proposal_pin),proposal), 'run_proposal')
    auth=dict(version=1,phase='run',proposal_sha256=proposal_pin['sha256'],allow_environment_calls=True,root_go_pending=False)
    auth_pin=save(r.RUN_AUTHORIZATION,auth)
    r.need(r.same(api.env.authorize(r.RUN_PROPOSAL,r.RUN_AUTHORIZATION,'run'),proposal), 'run_authorization')
    run_id=uuid.uuid4().hex
    server=dict(version=1,protocol=api.base.PROTOCOL,run_id=run_id,root=str(r.RUNTIME/'owned-v1/server'),
        port=15937,seconds=1700,adb=installed['adb'],tools=installed['tools'],sdk_version=api.base.SDK_VERSION,
        expected_version='0029',sources=[p for p in h['sources'] if PureWindowsPath(p['path']).name in api.base.SOURCE_NAMES|{'__init__.py'}],
        python=installed['python'],auth_key=installed['auth_key_path'],capabilities=installed['capabilities'],source_review=installed['source_review'])
    guest=dict(root=str(r.GUEST),proposal=proposal_pin,authorization=auth_pin,emulator=installed['emulator'],
        qemu=installed['qemu'],refuser=installed['refuser'],refuser_source=installed['refuser_source'],
        console_port=5592,adb_port=5593,serial='emulator-5592',memory_mib=8192,cores=4,max_seconds=1800,api=35,abi='x86_64')
    admission=dict(version=1,protocol=api.contract.PROTOCOL,run_id=run_id,root=str(r.RUNTIME/'owned-v1'),seconds=1700,
        server=server,guest=guest,artifacts=copy.deepcopy(h['artifacts']),sources=copy.deepcopy(h['sources']),
        python=copy.deepcopy(installed['python']),compatibility=installed['compatibility'])
    api.contract.validate_admission(admission);api.contract.revalidate_inputs(admission);api.profile_build.verify_current(admission)
    for folder in (r.RUNTIME,r.CONTROLS):
        api.env.safe_path(folder.parent,exists=True,directory=True);folder.mkdir()
    admission_pin=save(r.ADMISSION,admission)
    r.need(r.same(ledger,prepared(authority_pin,prepare_authorization_pin)), 'ledger_changed')
    for pin in (authority_pin,proposal_pin,auth_pin,admission_pin):api.env.check_binding(pin)
    activation=api.env.binding(api.activation.HELPER)
    r.need(any(r.same(activation,p) for p in h['sources']), 'activation_source')
    # Final publication only after every pre-input join; partials stay spent.
    input_pin=save(r.INPUT,dict(version=1,scope='record-cancellation-ui-run-input-v1',admission=admission_pin,helper=activation))
    api.env.check_binding(input_pin);api.env.check_binding(admission_pin)
    return dict(authority=authority_pin,prepare_authorization=prepare_authorization_pin,
        ledger=ledger,run_proposal=proposal_pin,run_authorization=auth_pin,admission=admission_pin,input=input_pin)


def _budget(begin,minimum):
    r,_=_parts();now=time.monotonic()
    r.need(type(begin) in (int,float) and math.isfinite(begin) and 0<=now-begin and
           now-begin+minimum<=r.MAX_SECONDS, 'operation_budget')


def _accept_activation(value,inputs):
    r,api=_parts()
    r.need(type(value) is dict and value.get('passed') is True and value.get('feature_acceptance') is False and
           r.same(value.get('input'),inputs['input']), 'activation')
    final_pin=api.env.binding(api.activation.CONTROL/'final-result-v1.json')
    r.need(r.same(read(final_pin),value), 'activation_result')
    runtime=read(value['runtime'],api.activation.CONTROL/'runtime-result-v1.json')
    r.need(all(runtime.get(k) is True for k in ('passed','controller_passed','owner_qualified','storage_closed','source_equal','cleanup_known')) and
           r.same(runtime['input'],inputs['input']), 'activation_cleanup')
    pin=api.env.binding(r.REGISTRY/'ledger-v1.json');ledger=read(pin)
    api.storage._validate(ledger,r.REGISTRY);entry=api.storage._entry(ledger,r.GUEST)
    api.history.require_cleanup(entry)
    r.need(entry['state']=='closed' and entry.get('recovery') is None and entry['retirement'] is None and
           entry['proposal_sha256']==inputs['run_proposal']['sha256'] and entry['closure'] is not None, 'storage_closure')
    closure=read(entry['closure'],r.GUEST/'guest-storage-closure-v1.json')
    r.need(closure['closure_verified'] is True and closure['cleanup_complete'] is True and
           closure['proposal_sha256']==inputs['run_proposal']['sha256'] and r.same(closure['admission'],inputs['admission']), 'storage_closure')
    api.env.check_binding(pin)
    return final_pin,pin


def _run_stages(authority_pin,attempt_pin,begin):
    r,api=_parts()
    result=dict(version=1,scope='sdk18-fresh-operation-stages-v1',passed=False,phase='initial',authority=authority_pin,
        attempt=attempt_pin,prepare_authorization=None,inputs=None,activation_result=None,ledger_after=None,feature_acceptance=False)
    try:
        a,h,_=frozen_inputs(authority_pin);r.validate_attempt(read(attempt_pin,r.ATTEMPT),authority_pin,a)
        claim=read(api.env.binding(r.LIVE/'worker-claim-v1.json'))
        r.need(r.same(claim['attempt'],attempt_pin) and r.same(claim['authority'],authority_pin), 'worker_claim')
        _budget(begin,2100)
        # Fresh locked admission happens inside the current public preparation.
        # A historical preview and the recorded grant never replace it.
        api.env.check_binding(a['ledger'])
        r.need(not os.path.lexists(r.GUEST), 'already_used')
        auth=save(r.PREPARE_AUTHORIZATION,dict(version=1,phase='prepare',proposal_sha256=h['prepare_proposal']['sha256'],
            allow_environment_calls=True,root_go_pending=False))
        result.update(phase='prepare',prepare_authorization=auth)
        api.env.prepare(h['prepare_proposal']['path'],r.PREPARE_AUTHORIZATION)
        prepared(authority_pin,auth);_budget(begin,2000)
        result['phase']='run_inputs';inputs=create_inputs(authority_pin,auth);result['inputs']=inputs
        _budget(begin,1900);result['phase']='activation'
        final_pin,ledger=_accept_activation(api.activation.execute(inputs['input']),inputs)
        frozen_inputs(authority_pin);api.env.check_binding(attempt_pin)
        result.update(passed=True,phase='completed',activation_result=final_pin,ledger_after=ledger)
    except BaseException as error:
        # No exception text (including paths/tokens/SDK stderr) is public output.
        result['passed']=False
        kind=type(error).__name__
        result['failure_type']=kind if kind in {'FreshRunRefused','EnvironmentRefused','StorageRefused','KeyboardInterrupt',
            'OSError','FileNotFoundError','FileExistsError','PermissionError','ValueError','KeyError','TypeError'} else 'operation_failed'
    result['elapsed_ms']=round(max(0,time.monotonic()-begin)*1000)
    try:save(r.LIVE/'stage-result-v1.json',result)
    except BaseException:
        result.update(passed=False,publication_failed=True)
        sys.stderr.write('{"scope":"sdk18-fresh-operation-stages-v1","publication_failed":true}\n')
    return result


def _worker():
    # No operational imports or subprocess before assignment to the owned job.
    if sys.stdin.buffer.readline(len(BARRIER)+1)!=BARRIER:return 1
    raw=sys.stdin.buffer.read(131073)
    if len(raw)>131072:return 1
    r,api=_parts();pin=api.env.decode_json(raw)
    request=read(pin,r.LIVE/'worker-request-v1.json')
    r.need(type(request) is dict and set(request)=={'version','scope','authority','attempt','parent','started_monotonic'} and
           type(request['version']) is int and request['version']==1 and request['scope']=='sdk18-fresh-operation-worker-request-v1', 'request')
    a=read_authority(request['authority']);r.validate_attempt(read(request['attempt'],r.ATTEMPT),request['authority'],a)
    parent=api.env.process_identity(os.getppid());worker=api.env.process_identity(os.getpid())
    r.need(r.same(parent,request['parent']) and parent['executable']==worker['executable']==sys.executable, 'identity')
    started=read(api.env.binding(r.LIVE/'worker-started-v1.json'))
    r.need(r.same(started,dict(request=pin,worker=worker)), 'worker_join');_budget(request['started_monotonic'],2100)
    save(r.LIVE/'worker-claim-v1.json',dict(version=1,authority=request['authority'],attempt=request['attempt'],request=pin,worker=worker))
    return 0 if _run_stages(request['authority'],request['attempt'],request['started_monotonic'])['passed'] else 1


def _supervise(request_pin,begin):
    # The environment supervisor is capped at1800s. Keep its reviewed job and
    # capture mechanisms, with a fixed40-minute outer ceiling for prepare+run.
    # Request release occurs only AFTER job assignment and exact started join.
    r,api=_parts();root=r.LIVE/'outer-owner-v1';root.mkdir()
    child=job=capture=None;threads=[];worker=None;status='spawn_failed';closed=False;stalled=False;readers_started=False
    try:
        capture=api.env.LiveOutput(root)
        child=subprocess.Popen([sys.executable,'-I','-S','-B',str(r.OPERATOR),'_worker'],stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,stderr=subprocess.PIPE,bufsize=0,creationflags=subprocess.CREATE_NO_WINDOW)
        job=api.env.host.WindowsJob(child.pid)
        worker=api.env.process_identity(child.pid)
        r.need(worker['executable']==sys.executable, 'identity')
        save(r.LIVE/'worker-started-v1.json',dict(request=request_pin,worker=worker))
        def drain(stream,channel):
            try:
                while True:
                    block=stream.read(4096)
                    if not block:break
                    if not capture.append(channel,block):break
            except BaseException:capture.failed.set()
        for channel,stream in enumerate((child.stdout,child.stderr)):
            thread=threading.Thread(target=drain,args=(stream,channel),daemon=True);threads.append(thread);thread.start()
        readers_started=True
        child.stdin.write(BARRIER+api.env.encoded(request_pin));child.stdin.close()
        status='running'
        while True:
            if capture.failed.is_set():status='capture_failed';break
            if capture.overflow.is_set():status='output_limit';break
            if time.monotonic()-begin>=r.MAX_SECONDS:status='expired';break
            if child.poll() is not None:status='child_exited';break
            time.sleep(.05)
    except KeyboardInterrupt:status='cancelled'
    except BaseException:status='owner_failed'
    finally:
        if child is not None:
            try:
                if job is not None:closed=job.close() is True
                else:child.kill();closed=False
            except BaseException:closed=False
            try:child.wait(timeout=5)
            except BaseException:closed=False
        for thread in threads:
            try:
                if thread.ident is not None:thread.join(timeout=2)
            except BaseException:stalled=True
        for thread in threads:
            try:
                if thread.is_alive():stalled=True
            except BaseException:stalled=True
        if child is not None and not stalled:
            for stream in (child.stdin,child.stdout,child.stderr):
                try:stream.close()
                except BaseException:closed=False
        if capture is not None:
            # Closing empty capture files cannot qualify unread child pipes.
            if child is not None and not readers_started:capture.failed.set()
            if stalled:capture.failed.set()
            else:
                try:
                    if capture.close() is not True:capture.failed.set()
                except BaseException:capture.failed.set()
            if capture.failed.is_set():closed=False
    complete=capture is not None and not stalled and not capture.failed.is_set() and not capture.overflow.is_set()
    return dict(status=status,worker_returncode=child.returncode if child is not None else None,
        cleanup_complete=closed and not stalled,output_capture_complete=complete,worker=worker,
        elapsed_ms=round(max(0,time.monotonic()-begin)*1000))


def execute(authority_pin):
    return _execute(authority_pin,time.monotonic())


def _execute(authority_pin,begin):
    r,api=_parts();a,_=_initial(authority_pin);_budget(begin,2100)
    attempt=_attempt(authority_pin,a)
    result=dict(version=1,scope='sdk18-fresh-operation-final-v1',passed=False,authority=authority_pin,
        attempt=attempt,owner=None,stages=None,feature_acceptance=False)
    try:
        parent=api.env.process_identity(os.getpid());r.need(parent['executable']==sys.executable, 'identity')
        request=save(r.LIVE/'worker-request-v1.json',dict(version=1,scope='sdk18-fresh-operation-worker-request-v1',
            authority=authority_pin,attempt=attempt,parent=parent,started_monotonic=begin))
        owner=_supervise(request,begin);result['owner']=save(r.LIVE/'outer-owner-result-v1.json',owner)
        r.need(owner['status']=='child_exited' and type(owner['worker_returncode']) is int and owner['worker_returncode']==0 and
               owner['cleanup_complete'] is True and owner['output_capture_complete'] is True, 'outer_terminal')
        r.need(r.same(read(api.env.binding(r.LIVE/'worker-started-v1.json')),dict(request=request,worker=owner['worker'])), 'worker_join')
        claim=read(api.env.binding(r.LIVE/'worker-claim-v1.json'))
        r.need(r.same(claim,dict(version=1,authority=authority_pin,attempt=attempt,request=request,worker=owner['worker'])), 'worker_join')
        pin=api.env.binding(r.LIVE/'stage-result-v1.json');stage=read(pin)
        r.need(stage['passed'] is True and stage['phase']=='completed' and r.same(stage['authority'],authority_pin) and
               r.same(stage['attempt'],attempt) and stage['feature_acceptance'] is False, 'stages')
        read_authority(authority_pin);api.env.check_binding(attempt)
        result.update(passed=True,stages=pin)
    except BaseException:
        result.update(passed=False,reason='operation_failed')
    save(r.LIVE/'operation-result-v1.json',result)
    return result


def main(argv=None):
    begin=time.monotonic()
    args=sys.argv[1:] if argv is None else argv
    if args==['_worker']:return _worker()
    if len(args)!=2 or args[0]!='--authority-sha256' or re.fullmatch('[0-9a-f]{64}',args[1]) is None:return 1
    try:
        r,api=_parts();pin=api.env.binding(r.AUTHORITY);r.need(pin['sha256']==args[1], 'authority_digest')
        result=_execute(pin,begin)
        print(api.env.encoded(result).decode('utf-8'))
        return 0 if result['passed'] else 1
    except BaseException:
        print('{"scope":"sdk18-fresh-operation-final-v1","passed":false,"reason":"operation_failed"}')
        return 1


if __name__=='__main__':
    raise SystemExit(main())
