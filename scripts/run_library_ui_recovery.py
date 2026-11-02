"""One explicitly authorized SDK15 recovery and UI run, under one owned job.

Import performs no I/O. No authority is created here. Old grants, retry, image
deletion, arbitrary commands and lifecycle control of other projects are absent.
Copyright 2026 LocalLore contributors. SPDX-License-Identifier: Apache-2.0
"""
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import threading
import time

ROOT=Path(__file__).parents[1]
BARRIER=b'sdk15-recovery-operation-worker-v1\n'


def _parts():
    sys.path.insert(0,str(ROOT))
    from scripts import library_ui_recovery_contract as rules
    from scripts import library_ui_run_inputs as builder
    rules.need(Path(rules.__file__).resolve()==ROOT/'scripts/library_ui_recovery_contract.py' and
               Path(builder.__file__).resolve()==ROOT/'scripts/library_ui_run_inputs.py', 'operator_source')
    return rules,builder,builder._api()


def _budget(begin, minimum):
    r,_,_=_parts();elapsed=time.monotonic()-begin
    r.need(0<=elapsed and elapsed+minimum<=r.MAX_SECONDS, 'operation_budget')


def _initial(authority_pin):
    r,b,api=_parts()
    r.need(Path.cwd()==r.SOURCE and all(Path(os.environ.get(k,''))==Path('D:/Dev/_Temp')
        for k in ('TEMP','TMP','TMPDIR')), 'environment')
    authority,h,_=b.frozen_inputs(authority_pin)
    api.env.safe_path(r.OUT,exists=True,directory=True)
    for path in (r.LIVE,r.EXECUTION,r.GUEST,r.GUEST.parent,r.RUNTIME,r.CONTROLS):
        r.need(not os.path.lexists(path), 'already_used')
    ledger_pin=api.env.binding(r.REGISTRY/'ledger-v1.json');ledger=b.read(ledger_pin)
    api.storage._validate(ledger,r.REGISTRY)
    r.need(type(ledger['version']) is int and ledger['version']==1 and ledger_pin['bytes']==41230 and
           ledger_pin['sha256']==r.INITIAL_LEDGER_SHA256 and
           r.same(api.storage._entry(ledger,r.GUEST),b.read(r.PLAN)['prior_entry']), 'initial_ledger')
    api.env.check_binding(ledger_pin)
    return authority,h,ledger_pin


def _attempt(authority_pin, authority):
    r,b,api=_parts()
    api.env.safe_path(r.LIVE,exists=False);r.LIVE.mkdir()
    record=dict(version=1,scope='sdk15-recovery-operation-attempt-v1',authority=authority_pin,
        handoff=authority['handoff'],recovery_plan=authority['recovery_plan'],operator=authority['operator'],
        builder=authority['builder'],contract=authority['contract'],no_retry=True)
    r.validate_attempt(record,authority_pin,authority)
    return b.save(r.ATTEMPT,record)


def _accept_activation(value, inputs):
    r,b,api=_parts()
    r.need(type(value) is dict and value.get('passed') is True and value.get('feature_acceptance') is False and
           r.same(value.get('input'),inputs['input']), 'activation')
    final_pin=api.env.binding(api.activation.CONTROL/'final-result-v1.json')
    r.need(r.same(b.read(final_pin),value), 'activation_result')
    runtime=b.read(value['runtime'],api.activation.CONTROL/'runtime-result-v1.json')
    r.need(all(runtime.get(key) is True for key in ('passed','controller_passed','owner_qualified',
        'storage_closed','source_equal','cleanup_known')) and r.same(runtime['input'],inputs['input']), 'activation_cleanup')
    ledger_pin=api.env.binding(r.REGISTRY/'ledger-v1.json');ledger=b.read(ledger_pin)
    api.storage._validate(ledger,r.REGISTRY);entry=api.storage._entry(ledger,r.GUEST)
    api.history.validate_history(entry,r.REGISTRY);api.history.require_cleanup(entry)
    r.need(entry['state']=='closed' and entry['proposal_sha256']==inputs['run_proposal']['sha256'] and
           entry['closure'] is not None, 'storage_closure')
    closure=b.read(entry['closure'],r.GUEST/'guest-storage-closure-v1.json')
    r.need(closure['closure_verified'] is True and closure['cleanup_complete'] is True and
           closure['proposal_sha256']==inputs['run_proposal']['sha256'] and
           r.same(closure['admission'],inputs['admission']), 'storage_closure')
    api.env.check_binding(ledger_pin)
    return final_pin,ledger_pin


def _run_stages(authority_pin, attempt_pin, begin):
    r,b,api=_parts()
    result=dict(version=1,scope='sdk15-recovery-operation-stages-v1',passed=False,phase='initial',
        authority=authority_pin,attempt=attempt_pin,recovery_authorization=None,recovery_result=None,
        inputs=None,activation_result=None,ledger_after=None,feature_acceptance=False)
    try:
        authority=b.read_authority(authority_pin)
        r.validate_attempt(b.read(attempt_pin,r.ATTEMPT),authority_pin,authority)
        worker_claim=b.read(api.env.binding(r.LIVE/'worker-claim-v1.json'))
        r.need(r.same(worker_claim['attempt'],attempt_pin) and r.same(worker_claim['authority'],authority_pin), 'worker_claim')
        b.frozen_inputs(authority_pin);_budget(begin,2100)
        result['phase']='recovery'
        auth=dict(version=1,action='recover_failed_root_mkdir_once',plan_sha256=r.PLAN['sha256'],
                  allow_sdk_prepare=True,accept_operator_observation=True)
        recovery_auth=b.save(r.RECOVERY_AUTHORIZATION,auth);result['recovery_authorization']=recovery_auth
        # This current public entry point owns its native fence, SDK job and
        # immutable history. Never retry or manually infer its cleanup.
        returned=api.recovery.execute(r.PLAN['path'],r.RECOVERY_AUTHORIZATION,r.EXECUTION)
        recovery_pin=api.env.binding(r.RECOVERY_RESULT)
        r.need(r.same(b.read(recovery_pin),returned), 'recovery_result')
        b.recovered(authority_pin,recovery_auth,recovery_pin);result['recovery_result']=recovery_pin
        result['phase']='run_inputs';_budget(begin,2000)
        inputs=b.create_inputs(authority_pin,recovery_auth,recovery_pin);result['inputs']=inputs
        _budget(begin,2000)
        result['phase']='activation'
        activation=api.activation.execute(inputs['input'])
        final_pin,ledger_pin=_accept_activation(activation,inputs)
        b.frozen_inputs(authority_pin);api.env.check_binding(authority_pin)
        result.update(passed=True,phase='completed',activation_result=final_pin,ledger_after=ledger_pin)
    except BaseException as error:
        result.update(failure_type=type(error).__name__,reason=str(error) if type(error) is r.OperationRefused else 'operation_failed')
    result['elapsed_ms']=round(max(0,time.monotonic()-begin)*1000)
    try:b.save(r.LIVE/'stage-result-v1.json',result)
    except BaseException:
        result.update(passed=False,publication_failed=True)
        sys.stderr.write('{"scope":"sdk15-recovery-operation-stages-v1","publication_failed":true}\n')
    return result


def _worker():
    # No target imports, Git subprocess or observation before job assignment.
    if sys.stdin.buffer.readline(len(BARRIER)+1)!=BARRIER:return 1
    payload=sys.stdin.buffer.read(131073)
    if len(payload)>131072:return 1
    r,b,api=_parts()
    request_pin=api.env.decode_json(payload)
    request=b.read(request_pin,r.LIVE/'worker-request-v1.json')
    r.need(type(request) is dict and set(request)=={'version','scope','authority','attempt','parent','started_monotonic'} and
           type(request['version']) is int and request['version']==1 and
           request['scope']=='sdk15-recovery-operation-worker-request-v1' and
           type(request['started_monotonic']) in (int,float), 'request')
    authority=b.read_authority(request['authority'])
    r.validate_attempt(b.read(request['attempt'],r.ATTEMPT),request['authority'],authority)
    r.need(os.getppid()==request['parent']['pid'] and
           r.same(api.env.process_identity(os.getppid()),request['parent']) and
           request['parent']['executable']==sys.executable, 'parent_identity')
    identity=api.env.process_identity(os.getpid())
    started=b.read(api.env.binding(r.LIVE/'worker-started-v1.json'))
    r.need(type(started) is dict and set(started)=={'request','worker'} and
           r.same(started['request'],request_pin) and r.same(started['worker'],identity), 'worker_identity')
    _budget(request['started_monotonic'],2100)
    # Even a failed pre-intent dispatch consumes this worker claim. A new parent
    # or a missing output directory cannot turn it into another attempt.
    b.save(r.LIVE/'worker-claim-v1.json',dict(version=1,authority=request['authority'],attempt=request['attempt'],
        request=request_pin,worker=identity))
    result=_run_stages(request['authority'],request['attempt'],request['started_monotonic'])
    return 0 if result['passed'] else 1


def _supervise(request_pin, begin):
    """Fixed worker only; own 40-minute job, unchanged component supervisors."""
    r,b,api=_parts();root=r.LIVE/'outer-owner-v1';root.mkdir()
    child=job=capture=None;readers=[];status='spawn_failed';closed=False
    worker=None
    try:
        capture=api.env.LiveOutput(root)
        child=subprocess.Popen([sys.executable,'-I','-S','-B',str(r.OPERATOR),'_worker'],stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,stderr=subprocess.PIPE,bufsize=0,creationflags=subprocess.CREATE_NO_WINDOW)
        job=api.env.host.WindowsJob(child.pid)
        worker=api.env.process_identity(child.pid)
        r.need(worker['executable']==sys.executable, 'worker_identity')
        b.save(r.LIVE/'worker-started-v1.json',dict(request=request_pin,worker=worker))
        def drain(stream,channel):
            try:
                while True:
                    block=stream.read(4096)
                    if not block:break
                    if not capture.append(channel,block):break
            except BaseException:capture.failed.set()
        for channel,stream in enumerate((child.stdout,child.stderr)):
            thread=threading.Thread(target=drain,args=(stream,channel),daemon=True);readers.append(thread);thread.start()
        # The job owns the child before the only dispatch barrier is released.
        child.stdin.write(BARRIER+api.env.encoded(request_pin));child.stdin.close()
        status='running'
        while True:
            if capture.failed.is_set():status='capture_failed';break
            if capture.overflow.is_set():status='output_limit';break
            if time.monotonic()-begin>=r.MAX_SECONDS:status='expired';break
            if child.poll() is not None:status='child_exited';break
            time.sleep(.05)
    except BaseException:status='owner_failed'
    finally:
        if child is not None:
            try:
                if job is not None:closed=job.close() is True
                else:child.kill();closed=True  # No barrier release without a job.
                child.wait(timeout=5)
            except BaseException:closed=False
        joined=True
        for thread in readers:
            try:
                if thread.ident is not None:thread.join(timeout=2)
            except BaseException:joined=False
        try:stalled=not joined or any(thread.is_alive() for thread in readers)
        except BaseException:stalled=True
        if child is not None and not stalled:
            for stream in (child.stdin,child.stdout,child.stderr):
                try:stream.close()
                except BaseException:closed=False
        if capture is not None:
            if stalled:capture.failed.set()
            else:
                try:capture.close()
                except BaseException:capture.failed.set()
    complete=capture is not None and not stalled and not capture.failed.is_set() and not capture.overflow.is_set()
    return dict(status=status,worker_returncode=child.returncode if child is not None else None,
        cleanup_complete=closed and not stalled,output_capture_complete=complete,
        worker=worker,stdout_bytes=capture.sizes[0] if capture is not None and not stalled else None,
        stderr_bytes=capture.sizes[1] if capture is not None and not stalled else None,
        elapsed_ms=round(max(0,time.monotonic()-begin)*1000))


def execute(authority_pin):
    r,b,api=_parts();begin=time.monotonic()
    authority,_,ledger=_initial(authority_pin);_budget(begin,2100)
    attempt=_attempt(authority_pin,authority)
    result=dict(version=1,scope='sdk15-recovery-operation-final-v1',passed=False,authority=authority_pin,
                attempt=attempt,ledger_before=ledger,owner=None,stages=None,feature_acceptance=False)
    try:
        parent=api.env.process_identity(os.getpid())
        r.need(parent['executable']==sys.executable, 'parent_identity')
        request=b.save(r.LIVE/'worker-request-v1.json',dict(version=1,scope='sdk15-recovery-operation-worker-request-v1',
            authority=authority_pin,attempt=attempt,parent=parent,started_monotonic=begin))
        returned=_supervise(request,begin);result['owner']=b.save(r.LIVE/'outer-owner-result-v1.json',returned)
        r.need(returned['status']=='child_exited' and returned['worker_returncode']==0 and
               returned['cleanup_complete'] is True and returned['output_capture_complete'] is True, 'outer_terminal')
        started=b.read(api.env.binding(r.LIVE/'worker-started-v1.json'))
        claim=b.read(api.env.binding(r.LIVE/'worker-claim-v1.json'))
        r.need(r.same(started,dict(request=request,worker=returned['worker'])) and
               type(claim) is dict and set(claim)=={'version','authority','attempt','request','worker'} and
               type(claim['version']) is int and claim['version']==1 and
               r.same(claim['authority'],authority_pin) and r.same(claim['attempt'],attempt) and
               r.same(claim['request'],request) and r.same(claim['worker'],returned['worker']), 'worker_join')
        stages_pin=api.env.binding(r.LIVE/'stage-result-v1.json');stages=b.read(stages_pin)
        r.need(stages['passed'] is True and stages['phase']=='completed' and r.same(stages['authority'],authority_pin) and
               r.same(stages['attempt'],attempt) and stages['feature_acceptance'] is False, 'stages')
        b.read_authority(authority_pin);api.env.check_binding(attempt)
        result.update(passed=True,stages=stages_pin)
    except BaseException as error:
        result.update(failure_type=type(error).__name__,reason=str(error) if type(error) is r.OperationRefused else 'operation_failed')
    b.save(r.LIVE/'operation-result-v1.json',result)
    return result


def main(argv=None):
    args=sys.argv[1:] if argv is None else argv
    if args==['_worker']:return _worker()
    if len(args)!=2 or args[0]!='--authority-sha256' or re.fullmatch('[0-9a-f]{64}',args[1]) is None:return 1
    try:
        r,_,api=_parts();pin=api.env.binding(r.AUTHORITY)
        r.need(pin['sha256']==args[1], 'authority_digest')
        value=execute(pin)
    except BaseException as error:
        print(json.dumps(dict(scope='sdk15-recovery-operation-final-v1',passed=False,failure_type=type(error).__name__)))
        return 1
    print(api.env.encoded(value).decode('utf-8'))
    return 0 if value['passed'] else 1


if __name__=='__main__':
    raise SystemExit(main())
