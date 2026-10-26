"""Original pure host adversaries; every client, supervisor and OS identity is mocked.

Copyright 2026 LocalLore contributors. SPDX-License-Identifier: Apache-2.0
"""
from contextlib import redirect_stdout
import copy
import io
import json
import os
from pathlib import Path
import sys
import tempfile
import time
from types import SimpleNamespace
import unittest
from unittest.mock import Mock, patch

sys.path.insert(0, str(Path(__file__).resolve().parents[2]/'benchmarks'))
import physical_model_probe as p

UID = 10341


def encoded(v):
    return json.dumps(v, separators=(',', ':')).encode()


def response(raw=b'', *, clean=True, code=0, status='completed', stderr=0):
    return SimpleNamespace(stdout=raw, cleanup_complete=clean, returncode=code, status=status, stderr_bytes=stderr)


def sample(installed=False):
    return dict(version=1, authorized=True, physical=True, model='SM-S918U1', api=36, soc_model='SM8550', board_platform='kalama',
        abis=['arm64-v8a','armeabi-v7a','armeabi'], page_bytes=4096, memory_total_bytes=11*p.contract.GIB,
        memory_available_bytes=5*p.contract.GIB, internal_free_bytes=16*p.contract.GIB,
        battery_level=80, battery_scale=100, usb_powered=True, temperature_tenths_celsius=250, thermal_status=0,
        new_app_absent=not installed, new_test_absent=not installed, prior_pair_unchanged=True)


def target():
    return dict(serial='ORIGINAL_PHONE', usb='1-2', product='original', model='SM_S918U1', device='original', transport_id=7)


def server():
    return dict(pid=4001, creation_filetime=12345, executable=str(p.ADB), listeners=[dict(address='127.0.0.1',port=5037,pid=4001)], adb_sha256=p.sha(b'adb'))


def proof(phase, prior=None):
    i=p.ORDER.index(phase)
    v=dict(version=1,scope=p.PROOF_SCOPE,profile=p.contract.PROFILE,phase=phase,pid=700+i,start=100+i,uid=UID,process=p.APP,
        model_bytes=p.contract.MODEL_BYTES,model_sha256=p.contract.MODEL_SHA256,elapsed_ms=10,
        shared_free_before=16*p.contract.GIB,shared_free_after=4*p.contract.GIB,
        memory_total_bytes=11*p.contract.GIB,memory_available_before=5*p.contract.GIB,memory_available_after=p.contract.GIB,
        low_memory_before=False,low_memory_after=False,sdk_invoked=phase in ('CANCEL','GIFT','DIALOGUE'),publication_native_invoked=False,
        checks={k:True for k in p.PHASES[phase][4]})
    for kind in ('verify','import'):
        for suffix in ('opened','closed','bytes'):
            v['source_'+kind+'_'+suffix]=(p.contract.MODEL_BYTES if suffix=='bytes' else 1) if phase=='IMPORT' else 0
    if i:
        v.update(prior_pid=prior['pid'] if prior else 699+i,prior_start=prior['start'] if prior else 99+i,prior_proof_sha256=p.sha(encoded(prior)) if prior else 'a'*64)
    if i>=2:v.update(revision=0 if phase=='CANCEL' else 1 if phase=='GIFT' else 2,receipt_count=0 if phase=='CANCEL' else 1 if phase=='GIFT' else 2,story_sha256='b'*64,receipts_sha256=('c' if phase=='CANCEL' else 'd' if phase=='GIFT' else 'e')*64,worker_trace_sha256='f'*64)
    if phase=='CANCEL':v['sample_trace_sha256']='a'*64
    if phase in ('GIFT','DIALOGUE'):v.update(repairs=0,fallback=False)
    if phase in ('GIFT','DIALOGUE','REOPEN'):v['gift_receipt_sha256']='1'*64
    if phase in ('DIALOGUE','REOPEN'):v['dialogue_receipt_sha256']='2'*64
    if phase=='DIALOGUE':v['guards_trace_sha256']='3'*64
    return v


def trace(kind):
    counts={k:0 for k in p.worker.EVENTS}; number=0 if kind=='ZERO' else 2 if kind=='ROLES' else 1
    if kind=='SAMPLE':counts.update(SEND_ENTERED=1,SEND_RETURNED=1,MESSAGE_RETURNED=1)
    elif kind=='CANCEL':counts.update(SEND_ENTERED=1,SEND_RETURNED=1,MESSAGE_RETURNED=2,DONE_ENTERED=1,DONE_RETURNED=1,CANCEL_ENTERED=1,CANCEL_RETURNED=1,DRAIN_SETTLED=1,CONVERSATION_CLOSE_ENTERED=1,CONVERSATION_CLOSE_KNOWN=1,ENGINE_CLOSE_ENTERED=1,ENGINE_CLOSE_KNOWN=1)
    elif kind=='ROLES':
        for k in ('CONVERSATION_CREATE_ENTERED','CONVERSATION_CREATE_RETURNED','SEND_ENTERED','SEND_RETURNED','DONE_ENTERED','DONE_RETURNED','DRAIN_SETTLED','CONVERSATION_CLOSE_ENTERED','CONVERSATION_CLOSE_KNOWN'):counts[k]=2
        counts.update(MESSAGE_RETURNED=5,ENGINE_CLOSE_ENTERED=1,ENGINE_CLOSE_KNOWN=1)
    roles=[] if number==0 else ['DIRECTOR','NARRATOR'] if number==2 else ['DIRECTOR']
    return dict(version=2,counts=counts,saturated=[],last_ms={k:3 if n else None for k,n in counts.items()},snapshot_ms=10,time_saturated=False,
        creations_total=number,creations_saturated=False,creations=[dict(ordinal=i,role=role,entered_ms=1,returned_ms=2,failed_ms=None,failure='NONE') for i,role in enumerate(roles,1)])


def transcript(phase, passed=True):
    cls='org.locallore.app.'+p.PHASES[phase][1]; rows=[]
    for code in (1,0 if passed else -2):
        fields=dict(**{'class':cls},current='1',id='AndroidJUnitRunner',numtests='1',stream='.' if code==0 else '',test=p.PHASES[phase][2])
        rows += ['INSTRUMENTATION_STATUS: '+k+'='+v for k,v in fields.items()]
        rows += ['INSTRUMENTATION_STATUS_CODE: '+str(code)]
    summary='OK (1 test)' if passed else 'FAILURES!!!\nTests run: 1, Failures: 1'
    return ('\n'.join(rows)+'\nINSTRUMENTATION_RESULT: stream=\n\nTime: 0.1\n\n'+summary+'\n\nINSTRUMENTATION_CODE: -1\n').encode()


class PhysicalProbeTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.root=Path(self.tmp.name)
        self.addCleanup(self.tmp.cleanup)
        self.host=self.enterContext(patch.object(p.q.host,'run_process',side_effect=AssertionError('UNMOCKED_CLIENT')))
        self.supervisor=self.enterContext(patch.object(p.environment,'supervise',side_effect=AssertionError('UNMOCKED_SUPERVISOR')))
        self.os_identity=self.enterContext(patch.object(p.environment,'process_identity',side_effect=AssertionError('UNMOCKED_OS_IDENTITY')))
        self.adb=self.root/'adb.exe';self.adb.write_bytes(b'adb')
        self.ps=self.root/'powershell.exe';self.ps.write_bytes(b'ps')
        self.enterContext(patch.object(p,'ADB',self.adb));self.enterContext(patch.object(p,'POWERSHELL',self.ps))
        self.apks={}
        for k,name in ((p.APP,'app.apk'),(p.TEST,'test.apk')):
            f=self.root/name;f.write_bytes(name.encode());self.apks[k]=str(f)
        self.pins={k:p.sha(Path(v).read_bytes()) for k,v in self.apks.items()}
        self.enterContext(patch.object(p,'APK_HASHES',self.pins))

    def fixture(self, phase='precheck'):
        identity=self.root/'identity.json';identity.write_bytes(encoded({'state':'device','serial':target()['serial']}))
        baseline={k:dict(uid=10200+i,sha256=h) for i,(k,h) in enumerate(p.PRIOR_PAIR.items())}
        facts=dict(version=1,target=target(),properties={k:'original' for k in p.IDENTITY},packages=baseline,processes=[],sample=sample())
        d=dict(version=1,scope=p.SCOPE,status='observed',identity_sha256=p.sha(identity.read_bytes()),server=server(),target=target(),facts=facts,clients_cleaned=True)
        discovery=self.root/'discovery.json';discovery.write_bytes(encoded(d))
        source=self.root/'probe.txt';source.write_bytes(b'LocalLore physical candidate source probe v1. No model or story.\n')
        self.enterContext(patch.object(p,'PROBE_PATH',source))
        self.enterContext(patch.object(p,'SOURCE_FILES',('source.py',)))
        self.enterContext(patch.object(p,'ROOT',self.root))
        f=self.root/'source.py';f.write_bytes(b'original source')
        value=dict(version=1,scope=p.SCOPE,phase=phase,identity_path=str(identity),identity_sha256=p.sha(identity.read_bytes()),
            discovery_path=str(discovery),discovery_sha256=p.sha(discovery.read_bytes()),adb_sha256=p.sha(b'adb'),powershell_sha256=p.sha(b'ps'),
            apk_paths=self.apks,bindings={str(f.resolve()):p.sha(f.read_bytes())},source=dict(path=str(source),bytes=p.PROBE_BYTES,sha256=p.PROBE_SHA),prior=None,evidence_root=str(self.root/'evidence'))
        if phase=='model':
            installed=copy.deepcopy(facts);installed['packages'].update({k:dict(uid=UID+i,sha256=self.pins[k]) for i,k in enumerate((p.APP,p.TEST))});installed['sample']=sample(True)
            prv=proof('PRECHECK')
            result=dict(version=1,scope=p.SCOPE,phase='precheck',status='observed',clients_cleaned=True,stage='boundary',command_count=10,methods=1,installs=2,result=dict(proof=prv,proof_sha256=p.sha(encoded(prv))))
            prior={}
            for kind,v in (('proof',prv),('facts',installed),('result',result)):
                f=self.root/(kind+'.json');f.write_bytes(encoded(v));prior[kind+'_path']=str(f);prior[kind+'_sha256']=p.sha(f.read_bytes())
            value.update(prior=prior,source=dict(path=str(source),bytes=p.contract.MODEL_BYTES,sha256=p.contract.MODEL_SHA256))
        return value

    def test_source_fixture_and_fixed_closed_92_check_schema(self):
        self.assertEqual([len(v[4]) for v in p.PHASES.values()],[13,17,18,15,16,13])
        self.assertEqual(p.PROBE_PATH.read_bytes(),b'LocalLore physical candidate source probe v1. No model or story.\n')
        self.assertEqual(p.sha(p.PROBE_PATH.read_bytes()),p.PROBE_SHA)
        self.assertEqual(p.sha(p.OWNER_BYTES),p.OWNER_SHA)
        self.assertTrue(any(n.endswith('PhysicalModelProof.kt') for n in p.SOURCE_FILES))
        previous=None
        for phase in p.ORDER:
            v=proof(phase,previous);self.assertEqual(p.parse_proof(encoded(v),phase,UID),v)
            if previous:p.link_proofs(previous,encoded(previous),v)
            self.assertEqual(p.parse_runner(transcript(phase),phase)['passed'],1)
            previous=v

    def test_proofs_refuse_private_fields_bool_repair_sdk_and_bad_resource_values(self):
        for phase in p.ORDER:
            for key,value in (('uid',True),('pid',True),('model_bytes',True),('low_memory_after',True),('sdk_invoked',None),('elapsed_ms',p.PHASES[phase][3]+1),('memory_available_before',1),('private_path','CANARY')):
                v=proof(phase);v[key]=value
                with self.subTest(phase=phase,key=key),self.assertRaises(AssertionError):p.parse_proof(encoded(v),phase,UID)
        for phase in ('GIFT','DIALOGUE'):
            v=proof(phase);v['repairs']=True
            with self.assertRaises(AssertionError):p.parse_proof(encoded(v),phase,UID)
            v['repairs']=1
            with self.assertRaises(AssertionError):p.parse_proof(encoded(v),phase,UID)

    def test_process_and_canonical_links_reject_replay_and_receipt_story_drift(self):
        before=proof('CANCEL');current=proof('GIFT',before)
        for key,value in (('prior_proof_sha256','0'*64),('prior_pid',1),('story_sha256','0'*64)):
            v=copy.deepcopy(current);v[key]=value
            with self.assertRaises(AssertionError):p.link_proofs(before,encoded(before),v)
        v=copy.deepcopy(current);v.update(pid=before['pid'],start=before['start'])
        with self.assertRaises(AssertionError):p.link_proofs(before,encoded(before),v)
        v['start']+=1;p.link_proofs(before,encoded(before),v) # PID reuse is valid with a new start.
        dialogue=proof('DIALOGUE',current);reopen=proof('REOPEN',dialogue)
        for key in ('receipts_sha256','gift_receipt_sha256','dialogue_receipt_sha256'):
            v=copy.deepcopy(reopen);v[key]='0'*64
            with self.assertRaises(AssertionError):p.link_proofs(dialogue,encoded(dialogue),v)

    def test_trace_cancel_requires_join_checks_and_same_history_not_ack_only(self):
        s=trace('SAMPLE');v=trace('CANCEL');p.trace_predicates(s,'CANCEL_SAMPLE');p.trace_predicates(v,'CANCEL',s)
        for key in ('DRAIN_SETTLED','ENGINE_CLOSE_KNOWN','CANCEL_RETURNED'):
            bad=copy.deepcopy(v);bad['counts'][key]=0
            with self.assertRaises(AssertionError):p.trace_predicates(bad,'CANCEL',s)
        bad=copy.deepcopy(v);bad['snapshot_ms']=9
        with self.assertRaises(AssertionError):p.trace_predicates(bad,'CANCEL',s)
        bad=copy.deepcopy(v);bad['creations'][0]['returned_ms']=3
        with self.assertRaises(AssertionError):p.trace_predicates(bad,'CANCEL',s)
        proof_bad=proof('CANCEL');proof_bad['checks']['cancel_ack_joined']=False
        with self.assertRaises(AssertionError):p.parse_proof(encoded(proof_bad),'CANCEL',UID)

    def test_two_roles_zero_reopen_and_zero_guard_history(self):
        roles=trace('ROLES');zero=trace('ZERO')
        p.trace_predicates(roles,'GIFT');p.trace_predicates(roles,'DIALOGUE',zero);p.trace_predicates(zero,'REOPEN')
        for bad in (trace('ROLES'),dict(zero,last_ms={k:0 for k in p.worker.EVENTS}),dict(zero,time_saturated=True)):
            with self.assertRaises(AssertionError):p.trace_predicates(bad,'REOPEN')
        bad=copy.deepcopy(roles);bad['creations'][1]['role']='DIRECTOR'
        with self.assertRaises(AssertionError):p.trace_predicates(bad,'GIFT')

    def test_usb_transport_parser_never_adopts_absent_other_phone_or_network(self):
        good=b'List of devices attached\nORIGINAL_PHONE device usb:1-2 product:original model:SM_S918U1 device:original transport_id:7\n'
        self.assertEqual(p.parse_devices(good,'ORIGINAL_PHONE'),target())
        self.assertIsNone(p.parse_devices(good.replace(b'ORIGINAL_PHONE',b'OTHER_PHONE'),'ORIGINAL_PHONE'))
        for raw in (good+good.split(b'\n',1)[1],good.replace(b' device usb:',b' unauthorized usb:'),good.replace(b'usb:1-2 ',b''),good.replace(b'transport_id:7',b'transport_id:7 transport_id:8')):
            with self.assertRaises(AssertionError):p.parse_devices(raw,'ORIGINAL_PHONE')
        with self.assertRaises(AssertionError):p.parse_devices(good,'127.0.0.1:5555')

    def test_absent_discovery_makes_no_target_calls_or_claim_or_install(self):
        identity=self.root/'id.json';identity.write_bytes(encoded(dict(state='device',serial='ORIGINAL_PHONE')))
        raw_server=encoded({k:v for k,v in server().items() if k!='adb_sha256'})
        calls=[]
        def run(args,**kw):
            calls.append(args)
            self.assertNotIn('-t',args)
            return response(raw_server if args[0]==str(self.ps) else b'List of devices attached\nemulator-5554 device product:original model:sdk device:sdk transport_id:1\n')
        self.host.side_effect=run
        with redirect_stdout(io.StringIO()):value=p.discover(identity,self.root/'absent')
        self.assertEqual(value['status'],'absent');self.assertEqual(value['target_calls'],0)
        self.assertEqual(len(calls),3);self.supervisor.assert_not_called()

    def test_server_requires_creation_binary_identity_and_only_loopback_listener(self):
        s=server();raw={k:v for k,v in s.items() if k!='adb_sha256'}
        self.assertEqual(p.parse_server(encoded(raw),s['adb_sha256']),s)
        for key,value in (('pid',True),('creation_filetime',0),('executable','foreign.exe')):
            v=copy.deepcopy(raw);v[key]=value
            with self.assertRaises(AssertionError):p.parse_server(encoded(v),s['adb_sha256'])
        v=copy.deepcopy(raw);v['listeners'][0]['address']='0.0.0.0'
        with self.assertRaises(AssertionError):p.parse_server(encoded(v),s['adb_sha256'])

    def test_any_client_or_retention_failure_is_sticky_and_raw_is_first(self):
        for i,bad in enumerate((response(b'raw',clean=False),response(b'raw',code=1),response(b'raw',status='expired'),response(b'raw',stderr=1))):
            owner=p.Capture(self.root/str(i),10);self.host.side_effect=None;self.host.return_value=bad
            with self.assertRaises(AssertionError):owner.capture(['fixed'],'fixed')
            self.assertEqual((owner.directory/'command-0001.stdout.bin').read_bytes(),b'raw');self.assertFalse(owner.clean)
            count=self.host.call_count
            with self.assertRaises(AssertionError):owner.capture(['fixed'],'never')
            self.assertEqual(self.host.call_count,count)
        owner=p.Capture(self.root/'retention',10);self.host.return_value=response(b'raw')
        with patch.object(p,'write',side_effect=OSError('synthetic')),self.assertRaises(OSError):owner.capture(['fixed'],'fixed')
        self.assertFalse(owner.clean);self.assertEqual((owner.directory/'command-0001.stdout.bin').read_bytes(),b'raw')

    def test_server_drift_stops_before_target_and_cannot_be_reset(self):
        owner=p.Capture(self.root/'server',10);owner.target=target();owner.server=server();owner.adb_sha=p.sha(b'adb')
        s=server();s['creation_filetime']+=1;self.host.side_effect=None;self.host.return_value=response(encoded({k:v for k,v in s.items() if k!='adb_sha256'}))
        with self.assertRaises(AssertionError):owner.adb(['get-state'],'state')
        self.assertFalse(owner.clean);self.assertEqual(self.host.call_count,1)
        with self.assertRaises(AssertionError):owner.adb(['get-state'],'state')
        self.assertEqual(self.host.call_count,1)

    def test_policy_uses_shared_two_copy_reserve_exact_boundary_and_ongoing_memory(self):
        facts=dict(sample=sample(True));facts['sample']['internal_free_bytes']=p.contract.REQUIRED_INTERNAL_FREE_BYTES
        p.resources(facts,installed=True,missing=2*p.contract.MODEL_BYTES)
        facts['sample']['internal_free_bytes']-=1
        with self.assertRaises(AssertionError):p.resources(facts,installed=True,missing=2*p.contract.MODEL_BYTES)
        facts['sample']['internal_free_bytes']=p.contract.SHARED_RESERVE_BYTES
        facts['sample']['memory_available_bytes']=p.contract.GIB
        with self.assertRaises(AssertionError):p.resources(facts,installed=True,missing=0)
        p.resources(facts,installed=True,missing=0,initial=False)
        facts['sample']['memory_available_bytes']=facts['sample']['memory_total_bytes']+1
        with self.assertRaises(AssertionError):p.resources(facts,installed=True,missing=0,initial=False)

    def test_proposal_authority_strict_source_binding_no_apk_default_and_bool_grant(self):
        v=self.fixture();self.assertIs(p.validate_proposal(v),v)
        with patch.object(p,'APK_HASHES',{}),self.assertRaises(AssertionError):p.validate_proposal(v)
        f=self.root/'proposal.json';f.write_bytes(encoded(v));auth=self.root/'auth.json'
        a=dict(version=1,proposal_sha256=p.sha(f.read_bytes()),allow_device_calls=True,allow_new_install=True,allow_model_copy=False,allow_sdk=False,root_go_pending=False)
        auth.write_bytes(encoded(a));self.assertEqual(p.authorize(f,auth,v['evidence_root']),v)
        a['allow_model_copy']=True;auth.write_bytes(encoded(a))
        with self.assertRaises(AssertionError):p.authorize(f,auth,v['evidence_root'])
        (self.root/'source.py').write_bytes(b'changed')
        with self.assertRaises(AssertionError):p.validate_proposal(v)
        self.host.assert_not_called();self.supervisor.assert_not_called()

    def test_commands_are_fixed_internal_no_replace_delete_or_unsafe_selector(self):
        for action in ('create','probe','model'):
            op=p.source_command(UID,action);self.assertEqual(op[:4],('run-as',p.APP,'sh','-c'))
            self.assertIn('no_backup',op[4]);self.assertNotIn('mkdir -p',op[4]);self.assertNotIn('chmod',op[4]);self.assertNotIn('rm ',op[4])
        with self.assertRaises(AssertionError):p.source_command(True,'model')
        with self.assertRaises(AssertionError):p.source_command(UID,'external')
        with self.assertRaises(AssertionError):p.proof_command(UID,'../old.json')
        for phase in p.ORDER:
            self.assertIn('org.locallore.app.'+p.PHASES[phase][1],p.selection(phase))
            self.assertNotIn('modelvolumeverify',' '.join(p.selection(phase)))

    def test_failed_runner_retains_raw_before_gate_no_proof_or_later_phase(self):
        owner=SimpleNamespace(clean=True,facts=Mock(),shell=Mock(return_value=transcript('CANCEL',False)),directory=self.root,methods=0,stage='before',last_pass=None)
        with patch.object(p,'read_phase') as read,self.assertRaises(AssertionError):p.run_selected(owner,'CANCEL')
        read.assert_not_called();self.assertFalse(owner.clean);self.assertIsNone(owner.last_pass)
        with self.assertRaises(AssertionError):p.run_selected(owner,'GIFT')
        self.assertEqual(owner.shell.call_count,1)

    def test_ready_manifest_traces_and_guard_hash_bind_before_proof_success(self):
        v=proof('DIALOGUE');ts=[trace('ZERO'),trace('ROLES')]
        v['guards_trace_sha256']=p.sha(encoded(ts[0]));v['worker_trace_sha256']=p.sha(encoded(ts[1]))
        names=set()
        for phase in p.ORDER[:5]:names|={p.PHASES[phase][0]+'-v1.json',p.PHASES[phase][0]+'-ready-v1.txt',*p.TRACES[phase]}
        manifest=('\n'.join(sorted(p.PROOF_ROOT+'/'+n for n in names))+'\n').encode()
        owner=SimpleNamespace(uids={p.APP:UID},directory=self.root,shell=Mock(side_effect=[manifest,b'',encoded(v),encoded(ts[0]),encoded(ts[1])]))
        actual,raw=p.read_phase(owner,'DIALOGUE');self.assertEqual(actual,v);self.assertEqual(raw,encoded(v))
        other=self.root/'bad';other.mkdir();v['guards_trace_sha256']='0'*64
        owner=SimpleNamespace(uids={p.APP:UID},directory=other,shell=Mock(side_effect=[manifest,b'',encoded(v),encoded(ts[0])]))
        with self.assertRaises(AssertionError):p.read_phase(owner,'DIALOGUE')
        self.assertTrue((other/'dialogue-proof.raw.json').exists());self.assertFalse((other/'dialogue-proof-v1.json').exists())

    def test_force_stop_permitted_only_after_known_pass_no_old_apps_or_pidof(self):
        v=self.fixture();root=Path(v['evidence_root']);root.mkdir();owner=p.Owner(v,root);owner.uids={p.APP:UID,p.TEST:UID+1}
        owner.shell=Mock(return_value=b'')
        with self.assertRaises(AssertionError):owner.stop_between()
        owner.shell.assert_not_called();owner.last_pass='IMPORT';owner.stage='passed'
        owner.shell.side_effect=[b'',b'',b'PID UID NAME\n']
        owner.stop_between();self.assertEqual(owner.stage,'boundary')
        self.assertEqual([call.args[0] for call in owner.shell.call_args_list[:2]],[('am','force-stop',p.APP),('am','force-stop',p.TEST)])
        self.assertFalse(any('pidof' in str(c) for c in owner.shell.call_args_list))

    def test_process_rows_require_exact_own_uid_and_empty_unknown_not_pidof_errors(self):
        uids={p.APP:UID,p.TEST:UID+1};p.process_rows(b'PID UID NAME\n1 0 init\n',uids)
        for raw in (f'PID UID NAME\n4 {UID} {p.APP}:unknown\n'.encode(),f'PID UID NAME\n4 {UID+2} {p.APP}\n'.encode(),b'permission denied\n'):
            with self.assertRaises((AssertionError,ValueError)):p.process_rows(raw,uids)

    def test_model_stream_parent_240_clipped_aggregate_and_unknown_stops_postchecks(self):
        v=self.fixture('model');root=Path(v['evidence_root']);root.mkdir();owner=p.Owner(v,root);owner.uids={p.APP:UID,p.TEST:UID+1};owner.stage='boundary'
        owner.facts=Mock();owner.check_server=Mock()
        (owner.directory/'before-stream-facts.json').write_bytes(b'original facts')
        proposal=self.root/'proposal.json';proposal.write_bytes(encoded(v));auth=self.root/'auth.json';auth.write_bytes(b'{}')
        self.os_identity.side_effect=None;self.os_identity.return_value=dict(pid=10,creation_filetime=20,executable=sys.executable)
        owner.until=time.monotonic()+80
        self.supervisor.side_effect=None;self.supervisor.return_value=dict(status='expired',worker_returncode=2,cleanup_complete=False,output_capture_complete=True,stdout_bytes=0,stderr_bytes=0)
        with self.assertRaises(AssertionError):owner.transfer(proposal,auth)
        self.assertFalse(owner.clean);owner.check_server.assert_not_called()
        self.assertLessEqual(self.supervisor.call_args.args[3],80);self.assertGreater(self.supervisor.call_args.args[3],6)
        self.assertTrue((owner.directory/'stream-result-v1.json').exists())
        with self.assertRaises(AssertionError):owner.transfer(proposal,auth)
        self.assertEqual(self.supervisor.call_count,1)

    def test_expired_aggregate_dispatches_no_client(self):
        owner=p.Capture(self.root/'expired',1);owner.until=time.monotonic()-1
        with self.assertRaises(AssertionError):owner.capture(['fixed'],'expired')
        self.host.assert_not_called();self.assertFalse(owner.clean)

    def test_phase_failure_prevents_recovery_and_reopen(self):
        v=self.fixture('model');prior=v['prior'];root=Path(v['evidence_root']);root.mkdir();owner=p.Owner(v,root);owner.uids={p.APP:UID,p.TEST:UID+1}
        facts=json.loads(Path(prior['facts_path']).read_bytes());owner.facts=Mock(return_value=facts);owner.transfer=Mock();owner.stop_between=Mock()
        imported=proof('IMPORT',proof('PRECHECK'))
        phases=[]
        def selected(o,phase):
            phases.append(phase)
            if phase=='CANCEL':o.clean=False;raise AssertionError('original cancellation failed')
            return imported,encoded(imported)
        with patch.object(p,'run_selected',side_effect=selected),self.assertRaises(AssertionError):p.run_cohort(owner,'proposal','auth')
        self.assertEqual(phases,['IMPORT','CANCEL']);self.assertEqual(owner.stop_between.call_count,1);self.assertFalse(owner.clean)

    def test_full_fixed_model_sequence_links_all_proofs_and_preserves_reopen(self):
        v=self.fixture('model');root=Path(v['evidence_root']);root.mkdir();owner=p.Owner(v,root);owner.uids={p.APP:UID,p.TEST:UID+1}
        facts=json.loads(Path(v['prior']['facts_path']).read_bytes());owner.facts=Mock(return_value=facts);owner.transfer=Mock()
        proofs={};previous=proof('PRECHECK')
        for phase in p.ORDER[1:]:
            current=proof(phase,previous)
            for i,name in enumerate(p.TRACES[phase]):
                t=trace('SAMPLE' if phase=='CANCEL' and i==0 else 'CANCEL' if phase=='CANCEL' else 'ZERO' if phase=='REOPEN' or phase=='DIALOGUE' and i==0 else 'ROLES')
                key='sample_trace_sha256' if phase=='CANCEL' and i==0 else 'guards_trace_sha256' if phase=='DIALOGUE' and i==0 else 'worker_trace_sha256'
                current[key]=p.sha(encoded(t))
            proofs[phase]=current;previous=current
        order=[];active=[None]
        def shell(op,label,**kwargs):
            for phase in p.ORDER[1:]:
                if op==p.selection(phase):active[0]=phase;order.append(phase);return transcript(phase)
            phase=active[0]
            if op[:2]==('am','force-stop'):self.assertIn(op[2],(p.APP,p.TEST));return b''
            if op==p.PS:return b'PID UID NAME\n'
            if op==p.manifest_command(UID):
                names=set()
                for a in p.ORDER[:p.ORDER.index(phase)+1]:names|={p.PHASES[a][0]+'-v1.json',p.PHASES[a][0]+'-ready-v1.txt',*p.TRACES[a]}
                return ('\n'.join(sorted(p.PROOF_ROOT+'/'+n for n in names))+'\n').encode()
            stem=p.PHASES[phase][0]
            if op==p.proof_command(UID,stem+'-ready-v1.txt'):return b''
            if op==p.proof_command(UID,stem+'-v1.json'):return encoded(proofs[phase])
            for i,name in enumerate(p.TRACES[phase]):
                if op==p.proof_command(UID,name):return encoded(trace('SAMPLE' if phase=='CANCEL' and i==0 else 'CANCEL' if phase=='CANCEL' else 'ZERO' if phase=='REOPEN' or phase=='DIALOGUE' and i==0 else 'ROLES'))
            raise AssertionError('unknown fixed operation')
        owner.shell=Mock(side_effect=shell)
        result=p.run_cohort(owner,'proposal','auth')
        self.assertEqual(order,list(p.ORDER[1:]));self.assertEqual(owner.methods,5);self.assertTrue(owner.clean)
        self.assertEqual(result['proofs']['REOPEN']['receipts_sha256'],proofs['DIALOGUE']['receipts_sha256'])
        self.assertFalse(result['proofs']['REOPEN']['sdk_invoked']);self.assertEqual(owner.last_pass,'REOPEN')

    def test_stream_tiny_original_held_fd_barrier_and_parent_replay_refusal(self):
        v=self.fixture();root=Path(v['evidence_root']);root.mkdir();cohort=root/'cohort';cohort.mkdir()
        props={k:'original' for k in p.IDENTITY}
        facts=dict(target=target(),packages={p.APP:dict(uid=UID)},processes=[],properties=props)
        factpath=cohort/'before-stream-facts.json';factpath.write_bytes(encoded(facts))
        proposal=self.root/'proposal.json';proposal.write_bytes(encoded(v));auth=self.root/'auth.json';auth.write_bytes(b'{}')
        identity=dict(pid=22,creation_filetime=33,executable=sys.executable)
        parent=dict(version=1,parent=identity,proposal_sha256=p.sha(proposal.read_bytes()),authorization_sha256=p.sha(auth.read_bytes()),deadline_epoch=time.time()+60,uid=UID,facts_sha256=p.sha(factpath.read_bytes()))
        (cohort/'stream-parent-v1.json').write_bytes(encoded(parent))
        class FakeCapture:
            def __init__(self,*a):self.target=None
            def check_server(self):pass
            def capture(self,*a):return b'List of devices attached\nORIGINAL_PHONE device usb:1-2 product:original model:SM_S918U1 device:original transport_id:7\n'
            def adb(self,*a,**kw):return b'device\n'
            def shell(self,op,*a,**kw):return b'4096\n' if op==p.PAGE else ''.join(k+'='+props[k]+'\n' for k in p.IDENTITY).encode()
        self.os_identity.side_effect=None;self.os_identity.return_value=identity
        calls=[]
        def child(argv,**kw):
            calls.append(argv);self.assertEqual(kw['stdin'].read(),Path(v['source']['path']).read_bytes())
            self.assertIn('exec-in',argv);self.assertIn('-t',argv);self.assertNotIn('-s',argv);self.assertLessEqual(kw['timeout'],150)
            return SimpleNamespace(returncode=0)
        with patch.object(p,'authorize',return_value=v),patch.object(p,'Capture',FakeCapture),patch.object(p.os,'getppid',return_value=22),patch.object(p.subprocess,'run',side_effect=child) as sdk,patch.object(sys,'stdin',SimpleNamespace(buffer=io.BytesIO(p.STREAM_REQUEST))),redirect_stdout(io.StringIO()):
            self.assertEqual(p.stream_worker(proposal,auth,root),0)
            with patch.object(sys,'stdin',SimpleNamespace(buffer=io.BytesIO(p.STREAM_REQUEST))),self.assertRaises(FileExistsError):p.stream_worker(proposal,auth,root)
        self.assertEqual(len(calls),1);self.host.assert_not_called();self.supervisor.assert_not_called()

    def test_rebound_precheck_bool_completion_refuses_before_any_host_client(self):
        v=self.fixture('model');source=Path(v['source']['path']);original=Path.stat
        def metadata(path,*args,**kwargs):
            value=original(path,*args,**kwargs)
            if path==source:
                fields=list(value);fields[6]=p.contract.MODEL_BYTES;return os.stat_result(fields)
            return value
        with patch.object(Path,'stat',metadata):
            self.assertIs(p.validate_proposal(v),v)
            f=Path(v['prior']['result_path']);r=json.loads(f.read_bytes());r['methods']=True;f.write_bytes(encoded(r));v['prior']['result_sha256']=p.sha(f.read_bytes())
            with self.assertRaises(AssertionError):p.validate_proposal(v)
        self.host.assert_not_called();self.supervisor.assert_not_called()

    def test_run_and_worker_barriers_supervisor_fixed_deadlines_and_no_cli_profile(self):
        v=self.fixture();root=Path(v['evidence_root']);root.mkdir()
        proposal=self.root/'proposal.json';proposal.write_bytes(encoded(v));auth=self.root/'auth.json';auth.write_bytes(b'{}')
        with patch.object(p,'authorize',return_value=v),patch.object(sys,'stdin',SimpleNamespace(buffer=io.BytesIO(b'wrong'))),self.assertRaises(AssertionError):p.worker_main(proposal,auth,root)
        self.os_identity.assert_not_called();self.supervisor.assert_not_called()
        def supervise(command,request,driver,seconds,started):
            self.assertEqual(seconds,180);self.assertEqual(request,p.REQUEST);self.assertIn(str(p.SCRIPT),command)
            (driver/'owner-stdout-v1.bin').write_bytes(b'{}')
            return dict(status='child_exited',worker_returncode=0,cleanup_complete=True,output_capture_complete=True,stdout_bytes=2,stderr_bytes=0)
        self.supervisor.side_effect=supervise
        self.os_identity.side_effect=None;self.os_identity.return_value=dict(pid=22,creation_filetime=33,executable=sys.executable)
        with patch.object(p,'authorize',return_value=v),redirect_stdout(io.StringIO()):self.assertEqual(p.run_owned(proposal,auth,root),0)
        self.assertEqual(p.main(['run','--evidence',str(root)]),2)

    def test_new_package_uids_cannot_alias_legacy_or_bool_even_when_hashes_match(self):
        baseline={k:dict(uid=10080+i,sha256=h) for i,(k,h) in enumerate(p.PRIOR_PAIR.items())}
        current=copy.deepcopy(baseline);current.update({k:dict(uid=UID+i,sha256=self.pins[k]) for i,k in enumerate((p.APP,p.TEST))})
        p.validate_packages(current,baseline,True)
        for uid in (True,UID+1,next(iter(baseline.values()))['uid']):
            v=copy.deepcopy(current);v[p.APP]['uid']=uid
            with self.assertRaises(AssertionError):p.validate_packages(v,baseline,True)

    def test_relative_apk_or_evidence_cannot_become_command_option_surface(self):
        v=self.fixture()
        for field,value in (('evidence_root','relative'),('identity_path','relative')):
            bad=copy.deepcopy(v);bad[field]=value
            with self.assertRaises(AssertionError):p.validate_proposal(bad)
        bad=copy.deepcopy(v);bad['apk_paths'][p.APP]='--replace'
        with self.assertRaises(AssertionError):p.validate_proposal(bad)
        self.host.assert_not_called();self.supervisor.assert_not_called()


if __name__=='__main__':unittest.main()
