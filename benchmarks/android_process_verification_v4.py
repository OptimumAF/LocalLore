"""Closed byte-bound owned-target replay; no process, socket or credential API.

Copyright 2026 LocalLore contributors. SPDX-License-Identifier: Apache-2.0
"""
import copy
import hashlib
from pathlib import Path, PureWindowsPath

from benchmarks import owned_target_contract as c
from benchmarks import isolated_adb_lease as base
from benchmarks import receipt_avd_environment as env
from benchmarks import host_commit_capacity as commit


def _raw(pin,cap=2*1024*1024):
    c.binding(pin,max_bytes=cap)
    return base._read_bound(pin,cap=cap)


def _json(pin):return env.decode_json(_raw(pin))


def _at(pin,path):
    c.binding(pin);c._need(PureWindowsPath(pin['path'])==PureWindowsPath(path),'binding')
    return _json(pin)


def _pin(path):
    c._path(str(path),project=True);return env.binding(path)


def _equal(a,b,reason='binding'):c._need(c._same(a,b),reason)


def verify_proof(pin,session,context):
    root=PureWindowsPath(session['root'])/'proofs'
    expected=root/('command-%04d-%s.json'%(context['index'],context['phase']))
    proof=c.validate_proof(_at(pin,expected),session,context)
    session_pin=_pin(Path(session['root'])/'sdk-session-v4.json')
    _equal(proof['session'],session_pin)
    q=c.validate_query_bundle(_json(proof['queries']),session['descriptor'],session['caller'],
                             session['admission'],session['running'])
    c._need(q==session['descriptor']['transport_id'],'identity')
    queries=_json(proof['queries'])['queries']
    _equal([proof['version_response_hex'],proof['devices_response_hex']],[x['response_hex']for x in queries])
    return proof


def verify_client_record(binding,session,admission):
    a=c.validate_admission(admission);s=c.validate_session(session,a)
    session_pin=_pin(Path(s['root'])/'sdk-session-v4.json');_equal(_json(session_pin),s)
    _equal(c.validate_admission(_json(s['admission'])),a)
    _equal(c.validate_running(_json(s['running']),a,s['admission']),s['descriptor'])
    value=c.validate_client_record(_json(binding),s)
    expected=PureWindowsPath(s['root'])/'clients'/('command-%04d.json'%value['index'])
    c._need(PureWindowsPath(binding['path'])==expected,'binding')
    _equal(value['session'],session_pin)
    c.validate_operation(value['operation'],a)
    total=0
    for channel in('stdout','stderr'):
        raw_path=expected.with_suffix('.'+channel+'.bin')
        c._need(PureWindowsPath(value[channel]['path'])==raw_path,'binding')
        raw=_raw(value[channel],cap=16*1024*1024);total+=len(raw)
    c._need(total<=16*1024*1024,'binding')
    c._need(value['client_qualified']is True,'capability')
    proofs=[]
    for phase,key in(('before','server_before'),('after','server_after')):
        context=dict(index=value['index'],phase=phase,label=value['label'],
          operation_sha256=value['operation_sha256'],transport_id=value['transport_id'])
        proofs.append(verify_proof(value[key],s,context))
    for key in('anchor','endpoint','caller'):_equal(proofs[0][key],proofs[1][key])
    if value['operation']['stdin']is not None:
        env.check_binding(value['operation']['stdin'])
    if value['operation']['argv'][:2]==['am','instrument']:
        method=value['operation']['argv'][6]
        kind='import'if method.endswith(c.METHODS[0])else'author'
        path=Path(a['root'])/'claims-v1'/(kind+'-v1.json')
        c.validate_claim(_json(_pin(path)),s['admission'],s['caller'],kind,value['operation_sha256'])
    return copy.deepcopy(value)


def require_current_clients(root,count,session_binding,admission):
    c._int(count,1,10000);root=Path(root)
    s=c.validate_session(_json(session_binding),admission)
    c._need(PureWindowsPath(s['root'])==PureWindowsPath(str(root)),'binding')
    _equal(session_binding,_pin(root/'sdk-session-v4.json'))
    expected_clients=set();expected_proofs=set();rows=[]
    for index in range(1,count+1):
        stem='command-%04d'%index
        expected_clients|={stem+'.json',stem+'.stdout.bin',stem+'.stderr.bin'}
        for phase in('before','after'):
            expected_proofs|={stem+'-'+phase+'.json',stem+'-'+phase+'-queries-v1.json'}
        rows.append(verify_client_record(_pin(root/'clients'/(stem+'.json')),s,admission))
        c._need(rows[-1]['index']==index,'binding')
    for folder,names in(('clients',expected_clients),('proofs',expected_proofs)):
        directory=env.safe_path(root/folder,directory=True)
        c._need({p.name for p in directory.iterdir()}==names,'binding')
        for path in directory.iterdir():env.safe_path(path)
    return rows


def _capture(pin,path,process,returncode):
    c._need(path.name in('server-output-v1','guest-output-v1'),'binding')
    value=_at(pin,path.parent/(path.name.replace('-output-','-capture-')+'.json'))
    c._obj(value,('version','protocol','server','status','returncode','stdout','stderr','stdout_bytes','stderr_bytes',
                  'capture_complete','pipes_closed'))
    c._int(value['version'],1,1);c._need(value['protocol']==c.PROTOCOL)
    _equal(value['server'],process)
    c._need(value['status']in('terminated','exited')and type(value['returncode'])is int and
            value['returncode']==returncode and value['capture_complete']is True and value['pipes_closed']is True,'identity')
    for channel in('stdout','stderr'):
        c._int(value[channel+'_bytes'],0,262144,'binding')
        c._need(PureWindowsPath(value[channel]['path'])==PureWindowsPath(str(path))/('owner-'+channel+'-v1.bin'),'binding')
        c._need(len(_raw(value[channel]))==value[channel+'_bytes'],'binding')
    c._need(value['stdout_bytes']+value['stderr_bytes']<=262144,'binding')
    return value


def _preflight(pin,path,guest=False):
    v=_at(pin,path)
    c._obj(v,('observation','tables','created_mask','close_attempted_mask','closed_mask','exclusive_bind_succeeded'))
    if guest:c._need(not c._rows(v['observation'],'ports',[5592,5593]),'observation')
    else:base.validate_observation(v['observation'],None,None,None,require_empty=True)
    base._tables(v['tables'],v['observation'])
    for key in('created_mask','close_attempted_mask','closed_mask'):c._int(v[key],15 if guest else 1,15 if guest else 1)
    c._need(v['exclusive_bind_succeeded']is True,'observation');return v


def verify_guest_inputs(pin,admission,admission_binding):
    a=c.validate_admission(admission);g=a['guest'];root=Path(a['root'])
    value=_at(pin,root/'guest-inputs-v1.json')
    c._obj(value,('version','protocol','admission','proposal','authorization','prepared','prepare_result','token',
                 'original_avd','configuration','tools','facts','timer'))
    c._int(value['version'],1,1);c._need(value['protocol']==c.PROTOCOL)
    for key,wanted in(('admission',admission_binding),('proposal',g['proposal']),('authorization',g['authorization'])):_equal(value[key],wanted)
    proposal=_json(g['proposal']);authorization=_json(g['authorization'])
    env.check_authorization(authorization,'run',g['proposal']['sha256'])
    _equal(proposal['host_free_min'],env.root_free_min(g['root']))
    c._int(proposal['host_available_memory_min'],12*1024**3,12*1024**3,'budget')
    c._need(proposal['version']==1 and proposal['phase']=='run'and
      proposal['paths']['root']==g['root']and proposal['serial']==g['serial']and
      type(proposal['memory_mib'])is int and proposal['memory_mib']==8192 and type(proposal['cores'])is int and proposal['cores']==4 and
      proposal['max_seconds']==1800 and proposal['console_port']==5592 and
      proposal['adb_path']==a['server']['adb']['path'],'binding')
    for key in('prepared','prepare_result'):_equal(value[key],proposal[key])
    prepared=_json(value['prepared']);result=_json(value['prepare_result'])
    env.check_binding(proposal['prepare_proposal'])
    c._need(prepared['proposal_sha256']==proposal['prepare_proposal']['sha256']and
      prepared['avd_name']=='locallore_receipt_api35_v1'and prepared['guest_boot_verified']is False and
      prepared['userdata_absent']is True,'binding')
    _equal(result,dict(version=1,proposal_sha256=proposal['prepare_proposal']['sha256'],status='completed',
      closure_verified=True,child_cleanup_complete=True,prepared_created=True))
    for key,pkey in(('token','token'),('original_avd','old_avd'),('tools','bindings')):_equal(value[key],proposal[pkey])
    _equal(value['configuration'],prepared['immutable'])
    for conf in value['configuration']:env.check_binding(conf)
    timer=value['timer'];c._obj(timer,('key','actual','effective','default_used','enabled'))
    c._need(timer['key']=='test.quitAfterBootTimeOut'and timer['enabled']is False and
      type(timer['effective'])is int and timer['effective']in(-1,0)and type(timer['default_used'])is bool,'binding')
    c._need((timer['actual']is None and timer['default_used']is True and timer['effective']==-1)or
      (timer['actual']in('-1','0')and timer['default_used']is False and timer['effective']==int(timer['actual'])),'binding')
    config=next(p for p in value['configuration']if PureWindowsPath(p['path']).name=='config.ini')
    config_values=env.ini(_raw(config));c._need(config_values.get(timer['key'])==timer['actual'],'binding')
    facts=value['facts'];c._obj(facts,('free_bytes','available_memory','logical_cpus','commit_capacity'))
    c._int(facts['available_memory'],12*1024**3,2**63-1);c._int(facts['logical_cpus'],8,2**31-1)
    c._obj(facts['free_bytes'],proposal['host_free_min'].keys())
    for drive,floor in proposal['host_free_min'].items():c._int(facts['free_bytes'][drive],floor,2**63-1)
    capacity=facts['commit_capacity']
    c._obj(capacity,('version','commit_total_bytes','commit_limit_bytes','available_commit_bytes',
                    'guest_memory_bytes','required_commit_bytes','reserve_bytes'))
    snapshot={k:capacity[k]for k in('version','commit_total_bytes','commit_limit_bytes','available_commit_bytes')}
    try:expected_capacity=commit.require_capacity(snapshot,8192)
    except commit.HostCommitRefused:raise c.TargetRefused('budget')from None
    _equal(capacity,expected_capacity)
    return value


def verify_owned_target_result(binding,admission,admission_binding,request_binding,expected_worker):
    a=c.validate_admission(admission);root=Path(a['root'])
    value=_at(binding,root/'worker-result-v1.json');c._obj(value,c.WORKER_KEYS)
    c._int(value['version'],1,1);c._need(value['protocol']==c.PROTOCOL)
    for key,wanted in(('admission',admission_binding),('request',request_binding),('worker',expected_worker)):_equal(value[key],wanted)
    req=_at(request_binding,root/'request-v1.json');c._obj(req,c.REQUEST_KEYS)
    c._int(req['version'],1,1);c._need(req['protocol']==c.PROTOCOL)
    _equal(req['admission'],admission_binding);_equal(req['validated_admission'],a)
    _equal(req['sources'],a['sources']);_equal(req['python'],a['python']);c._process(req['owner'])
    c._int(req['owner_seconds'],a['seconds']+30,a['seconds']+30)
    script=next(p for p in a['sources']if PureWindowsPath(p['path']).name=='owned_target_owner.py');_equal(req['worker_script'],script)
    c._need(value['reason']in('stop_requested','expired')and type(value['stop_requested'])is bool and
      value['stop_requested']==(value['reason']=='stop_requested'),'stop')
    c._int(value['elapsed_ms'],0,(a['seconds']+30)*1000,'budget')
    c._obj(value['cleanup'],c.CLEANUP_KEYS);c._need(all(x is True for x in value['cleanup'].values()),'identity')
    running=c.validate_running(_at(value['running'],root/'running-v1.json'),a,admission_binding)
    for key in('worker','server','launcher','guest','guest_ancestry'):_equal(value[key],running[key])
    _equal(req['owner'],running['owner'])
    base._auth(value['auth'],a['server'])
    _equal(value['sources_after'],dict(sources=a['sources'],python=a['python'],tools=a['server']['tools'],auth=value['auth']))
    _preflight(value['preflight'],root/'server/preflight-v1.json')
    _preflight(value['guest_preflight'],root/'guest-preflight-v1.json',True)
    server_admission=_pin(root/'server/admission-v1.json');_equal(_json(server_admission),a['server'])
    history=()
    for kind in('version','devices'):
        p=base.validate_proof(_pin(root/'server'/('proof-'+kind+'-v1.json')),a['server'],server_admission,
                             expected_worker,value['server'],kind,completed_ports=history)
        history+=(p['endpoint']['local_port'],)
    initial=env.read_json(root/'server/readiness-v1.json')
    c._need(type(initial)is list and 1<=len(initial)<=200,'observation')
    for i,item in enumerate(initial):
        c._obj(item,('observation','tables'))
        if i<len(initial)-1:base.validate_observation(item['observation'],None,None,None,require_empty=True)
        else:base.validate_observation(item['observation'],value['server'],None,None)
        base._tables(item['tables'],item['observation'])
    ready=c.validate_ready(_at(value['ready'],root/'target-ready-v1.json'),running,a)
    _equal(value['ready'],running['ready']);_equal(value['guest_job'],ready['guest_job'])
    c.validate_guest_job(_json(value['guest_job']),running)
    registration=_json(ready['queries'])
    c._need(c.validate_query_bundle(registration,running,expected_worker,admission_binding,None)==running['transport_id'],'identity')
    verify_guest_inputs(value['guest_inputs'],a,admission_binding)
    boot=_at(value['boot_claim'],Path(a['guest']['root'])/'owned-target-boot-claim-v1.json')
    c._obj(boot,('version','protocol','admission','worker','proposal'));c._int(boot['version'],1,1)
    c._need(boot['protocol']==c.PROTOCOL);_equal(boot['admission'],admission_binding)
    _equal(boot['worker'],expected_worker);_equal(boot['proposal'],a['guest']['proposal'])
    readiness=_at(value['readiness'],root/'readiness-v1.json')
    c._need(type(readiness)is list and 1<=len(readiness)<=300,'observation')
    last_ms=-1;registration_count=0;last_stage=-1;seen_stages=set()
    for entry in readiness:
        c._obj(entry,('elapsed_ms','stage','observation','tables','queries'));c._int(entry['elapsed_ms'],0,180000,'budget')
        c._need(entry['elapsed_ms']>=last_ms,'clock');last_ms=entry['elapsed_ms']
        c._need(entry['stage']in('guest_process','guest_ports','registration'))
        stage=('guest_process','guest_ports','registration').index(entry['stage'])
        c._need(stage>=last_stage,'clock');last_stage=stage;seen_stages.add(stage)
        if entry['stage']=='guest_process':
            c._need(entry['observation']is entry['tables']is entry['queries']is None)
        else:
            c.validate_guest_prefix(entry['observation'],running['guest'],running['server'])
            base._tables(entry['tables'],entry['observation'])
            if entry['stage']=='registration':
                registration_count+=1;c._need(registration_count<=60,'budget')
                q=_json(entry['queries']);c.validate_query_bundle(q,running,expected_worker,admission_binding,None,require_device=False)
            else:c._need(entry['queries']is None)
    c._need(seen_stages=={0,1,2}and readiness[-1]['stage']=='registration','observation')
    _equal(readiness[-1]['queries'],ready['queries'])
    _equal(readiness[-1]['observation'],ready['guest_observation'])
    _equal(readiness[-1]['tables'],ready['guest_tables'])
    for key in('server_returncode','guest_returncode'):c._int(value[key],-2**31,2**32-1,'identity')
    _capture(value['server_capture'],root/'server-output-v1',value['server'],value['server_returncode'])
    _capture(value['guest_capture'],root/'guest-output-v1',value['launcher'],value['guest_returncode'])
    terminal=_at(value['guest_terminal'],root/'guest-terminal-v1.json')
    c._obj(terminal,('version','protocol','guest','terminate_attempted','wait_completed','returncode','handle_closed'))
    c._int(terminal['version'],1,1);c._need(terminal['protocol']==c.PROTOCOL);_equal(terminal['guest'],value['guest'])
    c._need(all(terminal[k]is True for k in('terminate_attempted','wait_completed','handle_closed')),'identity')
    c._int(terminal['returncode'],-2**31,2**32-1,'identity')
    if value['stop_requested']:c.check_stop(_json(_pin(root/'stop-v1.json')),admission_binding['sha256'])
    c.revalidate_inputs(a)
    return copy.deepcopy(value)
