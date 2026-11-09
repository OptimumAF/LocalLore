"""One fixed SDK18 invocation under a checked parent job, including preflight.

Small source/authority bootstrap and final metadata reads remain cooperative.
No import grants or performs a guest, SDK, model or retirement operation.
Copyright 2026 LocalLore contributors. SPDX-License-Identifier: Apache-2.0
"""
import copy
import hashlib
import importlib.util
import json
import math
import os
from pathlib import Path, PureWindowsPath
import re
import subprocess
import sys
import threading
import time
from types import SimpleNamespace

ROOT=Path(__file__).parents[1]
BARRIER=b'sdk18-record-cancellation-operation-worker-v1\n'
_RULES=None
_MODULES=None


def _load(path,name):
    spec=importlib.util.spec_from_file_location(name,path)
    module=importlib.util.module_from_spec(spec)
    sys.modules[name]=module;spec.loader.exec_module(module)
    return module


def _raw(pin,maximum=2*1024**2):
    r=_RULES;r.binding(pin,maximum=maximum)
    path=Path(pin['path'])
    for item in (path,*path.parents):
        r.need(item.resolve(strict=True)==item and not item.is_symlink() and
               not getattr(item.lstat(),'st_file_attributes',0)&1024,'path')
    r.need(path.is_file() and path.stat().st_nlink==1 and path.stat().st_size==pin['bytes'],'binding')
    with path.open('rb') as stream:data=stream.read(pin['bytes']+1)
    r.need(len(data)==pin['bytes'] and hashlib.sha256(data).hexdigest()==pin['sha256'],'binding')
    r.need(path.resolve(strict=True)==path and path.stat().st_nlink==1 and path.stat().st_size==len(data),'binding')
    return data


def _bootstrap():
    r=_RULES;h=json.loads(_raw(r.HANDOFF))
    r.need(h['source_root']==str(r.SOURCE) and len(h['sources'])==28,'source')
    total=0;names=set()
    for pin in h['sources']:
        path=PureWindowsPath(pin['path'])
        r.need(path.parent==PureWindowsPath(r.SOURCE/'benchmarks') and path.name not in names,'source')
        names.add(path.name);total+=len(_raw(pin));r.need(total<=2*1024**2,'source')
    for pin in (r.FRESH_OPERATOR,r.FRESH_CONTRACT):_raw(pin)
    return h


def _parts():
    global _RULES,_MODULES
    if _RULES is None:_RULES=_load(ROOT/'scripts/record_cancellation_operation_contract.py','_sdk18_parent_rules')
    r=_RULES
    r.need(Path(__file__)==r.OPERATOR and ROOT==r.OPERATOR_ROOT and
           Path(r.__file__).resolve()==r.CONTRACT,'operator')
    if _MODULES is None:
        h=_bootstrap()
        original=list(sys.path)
        try:
            sys.path.insert(0,str(r.SOURCE))
            from benchmarks import receipt_avd_environment as env
            from benchmarks import receipt_avd_storage as storage
            from benchmarks import prepare_recovery_contract as history
            from benchmarks import adb_held_socket_probe as probe
            from benchmarks import record_cancellation_ui_activation as activation
            # The frozen activation loader prepends SOURCE on first import.
            # Scope that trusted import-only initialization to this temporary
            # path context. The later inner fresh loader must see one source,
            # with no namespace duplication or weakened origin check.
            activation_path=list(sys.path)
            try:activation._api()
            finally:sys.path[:]=activation_path
            for name,module in tuple(sys.modules.items()):
                if name=='benchmarks' or name.startswith('benchmarks.'):
                    file=getattr(module,'__file__',None)
                    if name=='benchmarks' and file is None:
                        r.need(list(module.__path__)==[str(r.SOURCE/'benchmarks')],'module_source')
                    else:r.need(file is not None and Path(file).resolve().parent==r.SOURCE/'benchmarks' and
                        Path(file).name in {PureWindowsPath(p['path']).name for p in h['sources']},'module_source')
        finally:sys.path[:]=original
        fresh_rules=_load(Path(r.FRESH_CONTRACT['path']),'_sdk18_inner_metadata')
        fresh=_load(Path(r.FRESH_OPERATOR['path']),'_sdk18_inner_operation')
        r.need(fresh_rules.AUTHORITY==r.FRESH_AUTHORITY and fresh_rules.PROPOSAL==r.PROPOSAL and
               fresh_rules.LIVE==r.FRESH_LIVE and fresh_rules.SOURCE==r.SOURCE and
               storage.DEFAULT_REGISTRY==r.REGISTRY,'profile')
        r.need(r.same(probe._python_bindings(),h['python']),'python')
        for pin in h['python'].values():
            if pin is not None:env.check_binding(pin)
        _MODULES=SimpleNamespace(env=env,storage=storage,history=history,probe=probe,fresh=fresh,fresh_rules=fresh_rules)
    return r,_MODULES


def read(pin,expected=None,maximum=2*1024**2):
    r,api=_parts();r.binding(pin,expected,maximum)
    api.env.check_binding(pin);raw=_raw(pin,maximum);api.env.check_binding(pin)
    return api.env.decode_json(raw)


def save(path,value):
    r,api=_parts();api.env.create_json(path,value);pin=api.env.binding(path)
    r.need(r.same(read(pin,path),value),'publication')
    return pin


def read_authority(pin):
    r,api=_parts();a=r.validate_authority(read(pin,r.AUTHORITY,16384))
    h=_bootstrap();r.need(r.same(api.probe._python_bindings(),h['python']),'python')
    for role in ('operator','contract','proposal','fresh_authority'):api.env.check_binding(a[role])
    inner=api.fresh_rules.validate_authority(read(a['fresh_authority'],r.FRESH_AUTHORITY,16384))
    r.need(r.same(inner['operator'],r.FRESH_OPERATOR) and r.same(inner['contract'],r.FRESH_CONTRACT) and
           r.same(inner['proposal'],a['proposal']) and inner['approval_reference']==a['approval_reference'],'inner_authority')
    api.env.check_binding(pin)
    return a


def _budget(begin):
    r,_=_parts();now=time.monotonic()
    r.need(type(begin) in (int,float) and math.isfinite(begin) and 0<=now-begin<r.MAX_SECONDS,'budget')


def _initial(pin):
    r,api=_parts()
    r.need(os.name=='nt' and Path.cwd()==r.SOURCE and all(Path(os.environ.get(k,''))==Path('D:/Dev/_Temp')
        for k in ('TEMP','TMP','TMPDIR')),'environment')
    a=read_authority(pin)
    for path in (r.LIVE,r.FRESH_LIVE,r.GUEST):
        api.env.safe_path(path,exists=False);r.need(not os.path.lexists(path),'already_used')
        api.env.safe_path(path.parent,exists=True,directory=True)
    return a


def _attempt(pin,authority):
    r,api=_parts();api.env.safe_path(r.LIVE,exists=False);r.LIVE.mkdir()
    value=dict(version=1,scope='sdk18-record-cancellation-operation-attempt-v1',authority=pin,
        operator=authority['operator'],contract=authority['contract'],fresh_authority=authority['fresh_authority'],no_retry=True)
    r.validate_attempt(value,pin,authority)
    return save(r.ATTEMPT,value)


def _accept_fresh(value,fresh_authority):
    r,api=_parts()
    r.need(type(value) is dict and set(value)=={'version','scope','passed','authority','attempt','owner','stages','feature_acceptance'} and
           type(value['version']) is int and value['version']==1 and value['scope']=='sdk18-fresh-operation-final-v1' and
           value['passed'] is True and value['feature_acceptance'] is False and r.same(value['authority'],fresh_authority),'fresh_result')
    final_pin=api.env.binding(r.FRESH_LIVE/'operation-result-v1.json')
    r.need(r.same(read(final_pin),value),'fresh_result')
    attempt=read(value['attempt'],r.FRESH_LIVE/'attempt-v1.json')
    inner=api.fresh_rules.validate_authority(read(fresh_authority,r.FRESH_AUTHORITY,16384))
    api.fresh_rules.validate_attempt(attempt,fresh_authority,inner)
    owner=read(value['owner'],r.FRESH_LIVE/'outer-owner-result-v1.json')
    r.need(owner['status']=='child_exited' and type(owner['worker_returncode']) is int and owner['worker_returncode']==0 and
           owner['cleanup_complete'] is True and owner['output_capture_complete'] is True,'fresh_cleanup')
    stage=read(value['stages'],r.FRESH_LIVE/'stage-result-v1.json')
    r.need(stage['scope']=='sdk18-fresh-operation-stages-v1' and stage['passed'] is True and stage['phase']=='completed' and
           stage['feature_acceptance'] is False and r.same(stage['authority'],fresh_authority) and
           r.same(stage['attempt'],value['attempt']),'fresh_stage')
    activation=read(stage['activation_result'],api.fresh_rules.RUNTIME/'control-v1/final-result-v1.json')
    r.need(activation['passed'] is True and activation['feature_acceptance'] is False and
           r.same(activation['input'],stage['inputs']['input']),'fresh_activation')
    runtime=read(activation['runtime'],api.fresh_rules.RUNTIME/'control-v1/runtime-result-v1.json')
    r.need(all(runtime.get(k) is True for k in ('passed','controller_passed','owner_qualified','storage_closed','source_equal','cleanup_known')) and
           r.same(runtime['input'],stage['inputs']['input']),'fresh_cleanup')
    ledger=read(stage['ledger_after'],r.REGISTRY/'ledger-v1.json')
    api.storage._validate(ledger,r.REGISTRY);entry=api.storage._entry(ledger,r.GUEST)
    api.history.require_cleanup(entry)
    r.need(type(ledger['version']) is int and ledger['version']==2 and entry['state']=='closed' and
           entry.get('recovery') is None and entry['retirement'] is None and entry['closure'] is not None and
           entry['proposal_sha256']==stage['inputs']['run_proposal']['sha256'],'fresh_storage')
    for pin in (final_pin,value['attempt'],value['owner'],value['stages'],stage['ledger_after']):api.env.check_binding(pin)
    return final_pin


def _invoke_fresh(authority_pin,attempt_pin,begin):
    r,api=_parts()
    result=dict(version=1,scope='sdk18-record-cancellation-operation-stages-v1',passed=False,authority=authority_pin,
        attempt=attempt_pin,fresh_authority=None,fresh_result=None,feature_acceptance=False)
    try:
        a=read_authority(authority_pin);r.validate_attempt(read(attempt_pin,r.ATTEMPT),authority_pin,a)
        _budget(begin);result['fresh_authority']=a['fresh_authority']
        # This call, including ALL expensive inner preflight, is made only by
        # the assigned barrier-controlled child. Never invoke it in the parent.
        value=api.fresh._execute(a['fresh_authority'],begin)
        result['fresh_result']=_accept_fresh(value,a['fresh_authority'])
        read_authority(authority_pin);api.env.check_binding(attempt_pin)
        result['passed']=True
    except BaseException:
        result.update(passed=False,reason='operation_failed')
    try:save(r.LIVE/'stage-result-v1.json',result)
    except BaseException:result.update(passed=False,publication_failed=True)
    return result


def _worker():
    if sys.stdin.buffer.readline(len(BARRIER)+1)!=BARRIER:return 1
    raw=sys.stdin.buffer.read(131073)
    if len(raw)>131072:return 1
    r,api=_parts();pin=api.env.decode_json(raw);request=read(pin,r.LIVE/'worker-request-v1.json')
    r.need(type(request) is dict and set(request)=={'version','scope','authority','attempt','parent','started_monotonic'} and
           type(request['version']) is int and request['version']==1 and
           request['scope']=='sdk18-record-cancellation-operation-worker-request-v1','request')
    a=read_authority(request['authority']);r.validate_attempt(read(request['attempt'],r.ATTEMPT),request['authority'],a)
    _budget(request['started_monotonic'])
    parent=api.env.process_identity(os.getppid());worker=api.env.process_identity(os.getpid())
    r.need(r.same(parent,request['parent']) and parent['executable']==worker['executable']==sys.executable,'identity')
    started=read(api.env.binding(r.LIVE/'worker-started-v1.json'))
    r.need(r.same(started,dict(request=pin,worker=worker)),'worker_join')
    save(r.LIVE/'worker-claim-v1.json',dict(version=1,authority=request['authority'],attempt=request['attempt'],request=pin,worker=worker))
    return 0 if _invoke_fresh(request['authority'],request['attempt'],request['started_monotonic'])['passed'] else 1


def execute(pin):
    return _execute(pin,time.monotonic())


def _execute(pin,begin):
    r,api=_parts();authority=_initial(pin);_budget(begin);attempt=_attempt(pin,authority)
    result=dict(version=1,scope='sdk18-record-cancellation-operation-final-v1',passed=False,authority=pin,
        attempt=attempt,owner=None,stages=None,feature_acceptance=False)
    try:
        parent=api.env.process_identity(os.getpid());r.need(parent['executable']==sys.executable,'identity')
        request=save(r.LIVE/'worker-request-v1.json',dict(version=1,scope='sdk18-record-cancellation-operation-worker-request-v1',
            authority=pin,attempt=attempt,parent=parent,started_monotonic=begin))
        owner=_supervise(request,begin);result['owner']=save(r.LIVE/'outer-owner-result-v1.json',owner)
        r.need(owner['status']=='child_exited' and type(owner['worker_returncode']) is int and owner['worker_returncode']==0 and
               owner['cleanup_complete'] is True and owner['output_capture_complete'] is True,'owner')
        r.need(r.same(read(api.env.binding(r.LIVE/'worker-started-v1.json')),dict(request=request,worker=owner['worker'])),'worker_join')
        claim=read(api.env.binding(r.LIVE/'worker-claim-v1.json'))
        r.need(r.same(claim,dict(version=1,authority=pin,attempt=attempt,request=request,worker=owner['worker'])),'worker_join')
        stage_pin=api.env.binding(r.LIVE/'stage-result-v1.json');stage=read(stage_pin)
        r.need(stage['passed'] is True and stage['scope']=='sdk18-record-cancellation-operation-stages-v1' and
               stage['feature_acceptance'] is False and r.same(stage['authority'],pin) and r.same(stage['attempt'],attempt) and
               r.same(stage['fresh_authority'],authority['fresh_authority']),'stage')
        fresh_value=read(stage['fresh_result'],r.FRESH_LIVE/'operation-result-v1.json')
        _accept_fresh(fresh_value,authority['fresh_authority'])
        read_authority(pin);api.env.check_binding(attempt)
        result.update(passed=True,stages=stage_pin)
    except BaseException:result.update(passed=False,reason='operation_failed')
    save(r.LIVE/'operation-result-v1.json',result)
    return result


def main(argv=None):
    begin=time.monotonic();args=sys.argv[1:] if argv is None else argv
    if args==['_worker']:return _worker()
    if len(args)!=2 or args[0]!='--authority-sha256' or re.fullmatch('[0-9a-f]{64}',args[1]) is None:return 1
    try:
        r,api=_parts();pin=api.env.binding(r.AUTHORITY);r.need(pin['sha256']==args[1],'authority_digest')
        value=_execute(pin,begin);print(api.env.encoded(value).decode('utf-8'))
        return 0 if value['passed'] else 1
    except BaseException:
        print('{"scope":"sdk18-record-cancellation-operation-final-v1","passed":false,"reason":"operation_failed"}')
        return 1


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


if __name__=="__main__":
    raise SystemExit(main())
