"""Original SDK17 parent authority, worker and watchdog observation-port tests.

Only tiny retained test metadata is written. No actual authority, fresh helper,
native job, process, SDK, guest, registry or credential is used.
"""
import contextlib
import copy
import hashlib
import io
import json
import os
from pathlib import Path, PureWindowsPath
import sys
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import Mock, patch

from scripts import diagnostic_operation_contract as rules
from scripts import diagnostic_ui_fresh_contract as inner_rules
from scripts import run_diagnostic_operation as subject
from scripts.tests import test_diagnostic_fresh_stages as prior

CANARY='PRIVATE_PARENT_PORT_PAYLOAD_108'


def encoded(value): return (json.dumps(value,sort_keys=True,allow_nan=False)+'\n').encode()
def canonical(path): return str(PureWindowsPath(path))
def dummy(path): return dict(path=canonical(path),bytes=1,sha256=hashlib.sha256(canonical(path).encode()).hexdigest())


def authority():
    return dict(version=1,scope='sdk17-diagnostic-operation-authority-v1',fresh_head=rules.FRESH_HEAD,
        operator=dummy(rules.OPERATOR),contract=dummy(rules.CONTRACT),proposal=dummy(rules.PROPOSAL),
        fresh_authority=dummy(rules.FRESH_AUTHORITY),allow_one_operation=True,allow_model=False,
        allow_retirement=False,max_operation_seconds=2400,approval_reference='SYNTHETIC_SHARED_APPROVAL_NOT_GRANTED')


class Metadata:
    def __init__(self,live=True):
        self.base=Path(tempfile.mkdtemp(prefix='sdk17-parent-oracle-'))
        if os.name=='nt': assert self.base.drive.upper()=='D:'
        self.events=[];self.records={};self.saved=[];self.clock=20.0;self.fail_save=None
        self.python=dict(executable=dummy(self.base/'python.exe'),runtime_dll=None)
        self.handoff=dict(python=copy.deepcopy(self.python))
        self.r=SimpleNamespace(**{name:getattr(rules,name) for name in
            ('AUTHORITY','FRESH_AUTHORITY','FRESH_OPERATOR','FRESH_CONTRACT','FRESH_LIVE','REGISTRY','GUEST','MAX_SECONDS')})
        self.r.LIVE=self.base/'live';self.r.ATTEMPT=self.r.LIVE/'attempt-v1.json';self.r.OPERATOR=rules.OPERATOR
        self.r.need=rules.need;self.r.same=rules.same;self.r.validate_authority=rules.validate_authority;self.r.validate_attempt=rules.validate_attempt
        if live:self.r.LIVE.mkdir()
        self.a=authority()
        self.inner=dict(version=1,scope='sdk17-fresh-prepare-and-one-diagnostic-ui-run-v1',source_head=inner_rules.SOURCE_HEAD,
            proposal=self.a['proposal'],operator=copy.deepcopy(rules.FRESH_OPERATOR),contract=copy.deepcopy(rules.FRESH_CONTRACT),
            handoff=copy.deepcopy(inner_rules.HANDOFF),ledger=dummy(inner_rules.REGISTRY/'ledger-v1.json'),
            allow_sdk_prepare=True,allow_one_boot=True,allow_model=False,allow_retirement=False,
            approval_reference=self.a['approval_reference'],max_operation_seconds=2400)
        self.refresh_authorities()
        self.fresh_attempt=self.put(inner_rules.ATTEMPT,dict(version=1,scope='sdk17-fresh-operation-attempt-v1',
            authority=self.inner_pin,handoff=self.inner['handoff'],operator=self.inner['operator'],contract=self.inner['contract'],no_retry=True))
        self.owner=dict(status='child_exited',worker_returncode=0,cleanup_complete=True,output_capture_complete=True,worker={})
        self.input_pin=dummy(inner_rules.INPUT);self.run_pin=dummy(inner_rules.RUN_PROPOSAL)
        self.runtime=dict(input=self.input_pin,passed=True,controller_passed=True,owner_qualified=True,storage_closed=True,source_equal=True,cleanup_known=True)
        self.activation=dict(passed=True,feature_acceptance=False,input=self.input_pin)
        self.entry=dict(root=str(rules.GUEST),state='closed',recovery=None,retirement=None,
            closure=dummy(rules.GUEST/'guest-storage-closure-v1.json'),proposal_sha256=self.run_pin['sha256'])
        self.ledger=dict(version=2,entries=[self.entry])
        self.stage=dict(version=1,scope='sdk17-fresh-operation-stages-v1',passed=True,phase='completed',
            authority=self.inner_pin,attempt=self.fresh_attempt,feature_acceptance=False,
            inputs=dict(input=self.input_pin,run_proposal=self.run_pin))
        self.final=dict(version=1,scope='sdk17-fresh-operation-final-v1',passed=True,authority=self.inner_pin,
            attempt=self.fresh_attempt,feature_acceptance=False)
        self.rebuild()
        fresh=SimpleNamespace(_execute=Mock(side_effect=lambda pin,begin:copy.deepcopy(self.final)),
            _parts=Mock(side_effect=AssertionError('heavy fresh parts outside worker')),
            read_authority=Mock(side_effect=AssertionError('heavy fresh authority outside worker')))
        self.api=SimpleNamespace(env=SimpleNamespace(encoded=encoded,decode_json=json.loads,binding=self.binding,
            check_binding=self.check,safe_path=self.safe_path,process_identity=lambda pid:dict(pid=pid,executable=sys.executable)),
            fresh=fresh,fresh_rules=inner_rules,
            probe=SimpleNamespace(_python_bindings=Mock(side_effect=lambda:copy.deepcopy(self.python))),
            storage=SimpleNamespace(_validate=Mock(),_entry=lambda ledger,path:ledger['entries'][0]),
            history=SimpleNamespace(require_cleanup=Mock()))

    def put(self,path,value):
        path=canonical(path);raw=encoded(value);self.records[path]=raw
        return dict(path=path,bytes=len(raw),sha256=hashlib.sha256(raw).hexdigest())

    def refresh_authorities(self):
        self.inner_pin=self.put(rules.FRESH_AUTHORITY,self.inner)
        self.a['fresh_authority']=self.inner_pin
        self.authority_pin=self.put(rules.AUTHORITY,self.a)

    def rebuild(self):
        runtime=self.put(inner_rules.RUNTIME/'control-v1/runtime-result-v1.json',self.runtime)
        self.activation['runtime']=runtime
        self.stage['activation_result']=self.put(inner_rules.RUNTIME/'control-v1/final-result-v1.json',self.activation)
        self.stage['ledger_after']=self.put(rules.REGISTRY/'ledger-v1.json',self.ledger)
        self.final['owner']=self.put(inner_rules.LIVE/'outer-owner-result-v1.json',self.owner)
        self.final['stages']=self.put(inner_rules.LIVE/'stage-result-v1.json',self.stage)
        self.final_pin=self.put(inner_rules.LIVE/'operation-result-v1.json',self.final)

    def binding(self,path):
        key=canonical(path);rules.need(key in self.records,'fixture_missing')
        raw=self.records[key];return dict(path=key,bytes=len(raw),sha256=hashlib.sha256(raw).hexdigest())

    def check(self,pin):
        # Exact source pins are a declared fake byte-observation port. No file
        # is opened at any real authority/proposal/operator path.
        if pin in (self.a['operator'],self.a['contract'],self.a['proposal'],rules.FRESH_OPERATOR,rules.FRESH_CONTRACT):return
        rules.need(pin==self.binding(pin['path']),'fixture_binding')

    def read(self,pin,expected=None,maximum=2*1024**2):
        rules.binding(pin,expected,maximum);self.check(pin)
        return json.loads(self.records[pin['path']])

    def save(self,path,value):
        self.events.append('save:'+path.name)
        if path.name==self.fail_save:raise OSError(CANARY)
        rules.need(path.is_relative_to(self.base),'outside_fixture')
        with path.open('xb') as stream:stream.write(encoded(value))
        self.saved.append((path,copy.deepcopy(value)));return self.put(path,value)

    def safe_path(self,path,exists=False,**kwargs):
        rules.need(path.exists() is exists,'already_used');return path

    def make_attempt(self):
        return self.save(self.r.ATTEMPT,dict(version=1,scope='sdk17-diagnostic-operation-attempt-v1',
            authority=self.authority_pin,operator=self.a['operator'],contract=self.a['contract'],
            fresh_authority=self.a['fresh_authority'],no_retry=True))

    @contextlib.contextmanager
    def ports(self):
        with patch.object(subject,'_parts',return_value=(self.r,self.api)), \
             patch.object(subject,'_bootstrap',side_effect=lambda:copy.deepcopy(self.handoff)), \
             patch.object(subject,'read',side_effect=self.read), \
             patch.object(subject,'save',side_effect=self.save), \
             patch.object(subject.time,'monotonic',side_effect=lambda:self.clock):yield


class Supervisor(prior.Supervisor):
    def __init__(self,**kwargs):
        super().__init__(**kwargs);self.r.need=rules.need;self.r.same=rules.same

    @contextlib.contextmanager
    def ports(self):
        with patch.object(subject,'_parts',return_value=(self.r,self.api)), \
             patch.object(subject,'save',side_effect=self.save), \
             patch.object(subject.subprocess,'Popen',return_value=self.child), \
             patch.object(subject.subprocess,'CREATE_NO_WINDOW',0,create=True), \
             patch.object(subject.threading,'Thread',side_effect=lambda **kw:prior.InlineThread(self,**kw)), \
             patch.object(subject.time,'monotonic',side_effect=lambda:self.clock), \
             patch.object(subject.time,'sleep',side_effect=self.sleep):yield


class ParentAuthorityTests(unittest.TestCase):
    def test_authority_is_closed_typed_detached_and_fixed_to_one_parent_operation(self):
        value=authority();before=copy.deepcopy(value)
        with patch.object(Path,'open',side_effect=AssertionError('IO')):
            actual=rules.validate_authority(value)
        self.assertEqual(actual,before);actual['operator']['sha256']='0'*64;self.assertEqual(value,before)
        mutations=[('version',True),('fresh_head','a'*40),('allow_one_operation',1),('allow_model',True),
            ('allow_retirement',True),('max_operation_seconds',2400.0),('scope','sdk16-operation'),('operator_head','invented')]
        for key,wrong in mutations:
            with self.subTest(key=key):
                bad=copy.deepcopy(value);bad[key]=wrong
                with self.assertRaises(rules.OperationRefused):rules.validate_authority(bad)


@unittest.skipUnless(os.name=='nt','retained physical D parent port fixtures require Windows')
class ParentOperationTests(unittest.TestCase):
    def test_authority_references_must_agree_without_heavy_fresh_helpers(self):
        h=Metadata()
        with h.ports():self.assertEqual(subject.read_authority(h.authority_pin),h.a)
        h.api.fresh._parts.assert_not_called();h.api.fresh.read_authority.assert_not_called();h.api.fresh._execute.assert_not_called()
        h.inner['approval_reference']='different-unapproved-reference';h.refresh_authorities()
        with h.ports(),self.assertRaises(rules.OperationRefused):subject.read_authority(h.authority_pin)
        h.api.fresh._execute.assert_not_called()
        h=Metadata();h.python['executable']=dummy(h.base/'different-python.exe')
        with h.ports(),self.assertRaises(rules.OperationRefused):subject.read_authority(h.authority_pin)
        self.assertEqual(h.saved,[]);h.api.fresh._execute.assert_not_called()

    def test_worker_barrier_precedes_import_and_forwards_original_begin_once(self):
        with patch.object(subject.sys,'stdin',SimpleNamespace(buffer=io.BytesIO(b'not the barrier\n'))), \
             patch.object(subject,'_parts',side_effect=AssertionError('operational bootstrap before barrier')):
            self.assertEqual(subject._worker(),1)
        h=Metadata();attempt=h.make_attempt();begin=12.25
        parent=dict(pid=os.getppid(),executable=sys.executable);worker=dict(pid=os.getpid(),executable=sys.executable)
        request=h.save(h.r.LIVE/'worker-request-v1.json',dict(version=1,scope='sdk17-diagnostic-operation-worker-request-v1',
            authority=h.authority_pin,attempt=attempt,parent=parent,started_monotonic=begin))
        h.save(h.r.LIVE/'worker-started-v1.json',dict(request=request,worker=worker))
        with h.ports(),patch.object(subject.sys,'stdin',SimpleNamespace(buffer=io.BytesIO(subject.BARRIER+encoded(request)))):
            self.assertEqual(subject._worker(),0)
        h.api.fresh._execute.assert_called_once_with(h.inner_pin,begin)
        h.api.fresh._parts.assert_not_called();h.api.fresh.read_authority.assert_not_called()
        self.assertTrue((h.r.LIVE/'worker-claim-v1.json').is_file())
        self.assertEqual(h.events.count('save:stage-result-v1.json'),1)

    def test_supervisor_positive_and_pre_release_failures_have_owned_order(self):
        h=Supervisor()
        with h.ports():result=subject._supervise(prior.fake_pin(h.base/'request.json'),0.0)
        self.assertEqual(result['status'],'child_exited');self.assertIs(result['cleanup_complete'],True)
        self.assertIs(result['output_capture_complete'],True)
        self.assertLess(h.events.index('job.assign'),h.events.index('barrier'))
        self.assertLess(h.events.index('identity'),h.events.index('barrier'))
        self.assertLess(h.events.index('save:worker-started-v1.json'),h.events.index('barrier'))
        self.assertTrue(h.released[0].startswith(subject.BARRIER))
        for mutation in ('job','identity','started'):
            with self.subTest(mutation=mutation):
                h=Supervisor(job_error=OSError(CANARY) if mutation=='job' else None,wrong_identity=mutation=='identity')
                if mutation=='started':h.fail_save='worker-started-v1.json'
                with h.ports():result=subject._supervise(prior.fake_pin(h.base/'request.json'),0.0)
                self.assertEqual(h.released,[]);self.assertIs(result['cleanup_complete'],False)
                self.assertIs(result['output_capture_complete'],False);self.assertIn('wait',h.events)
                self.assertNotIn(CANARY,repr(result))

    def test_full_invocation_clock_and_unknown_closes_cannot_qualify_parent(self):
        for kwargs in (dict(job_result=False),dict(job_result=KeyboardInterrupt(CANARY)),dict(capture_result=None),
                       dict(capture_result=1),dict(capture_result=SystemExit(CANARY))):
            with self.subTest(kwargs=repr(kwargs)):
                h=Supervisor(**kwargs)
                with h.ports():result=subject._supervise(prior.fake_pin(h.base/'request.json'),0.0)
                self.assertIs(result['cleanup_complete'],False);self.assertIn('wait',h.events)
                self.assertEqual(h.events.count('reader.join'),2);self.assertEqual(h.events.count('capture.close'),1)
        h=Supervisor(never_exits=True);h.clock=2399.0
        with h.ports():result=subject._supervise(prior.fake_pin(h.base/'request.json'),0.0)
        self.assertEqual(result['status'],'expired');self.assertLessEqual(h.events.count('poll'),1)
        self.assertGreaterEqual(result['elapsed_ms'],2400000);self.assertIn('job.close',h.events)
        h=Supervisor(poll_error=KeyboardInterrupt(CANARY))
        with h.ports():result=subject._supervise(prior.fake_pin(h.base/'request.json'),0.0)
        self.assertEqual(result['status'],'cancelled');self.assertIn('wait',h.events)

    def test_fresh_result_nested_joins_require_exact_typed_closed_evidence(self):
        positive=Metadata()
        with positive.ports():self.assertEqual(subject._accept_fresh(positive.final,positive.inner_pin),positive.final_pin)
        for mutation in ('owner_bool','owner_unknown','stage_authority','stage_attempt','activation','runtime','ledger','feature'):
            with self.subTest(mutation=mutation):
                h=Metadata()
                if mutation=='owner_bool':h.owner['worker_returncode']=False
                elif mutation=='owner_unknown':h.owner['cleanup_complete']=False
                elif mutation=='stage_authority':h.stage['authority']=dummy(rules.AUTHORITY)
                elif mutation=='stage_attempt':h.stage['attempt']=dummy(inner_rules.LIVE/'borrowed-attempt.json')
                elif mutation=='activation':h.activation['input']=dummy(inner_rules.RUNTIME/'borrowed-input.json')
                elif mutation=='runtime':h.runtime['cleanup_known']=1
                elif mutation=='ledger':h.entry['state']='prepared'
                else:h.final['feature_acceptance']=True
                h.rebuild()
                with h.ports(),self.assertRaises(rules.OperationRefused):subject._accept_fresh(h.final,h.inner_pin)
                h.api.fresh._execute.assert_not_called()

    def test_invocation_and_publication_errors_revoke_success_and_do_not_retry(self):
        positive=Metadata();attempt=positive.make_attempt()
        with positive.ports():passed=subject._invoke_fresh(positive.authority_pin,attempt,12.25)
        self.assertIs(passed['passed'],True);positive.api.fresh._execute.assert_called_once_with(positive.inner_pin,12.25)
        for failure in ('cancel','exit','changed_authority','publication'):
            with self.subTest(failure=failure):
                h=Metadata();attempt=h.make_attempt()
                if failure=='cancel':h.api.fresh._execute.side_effect=KeyboardInterrupt(CANARY)
                elif failure=='exit':h.api.fresh._execute.side_effect=SystemExit(CANARY)
                elif failure=='publication':h.fail_save='stage-result-v1.json'
                with h.ports():
                    if failure=='changed_authority':
                        with patch.object(subject,'read_authority',side_effect=[h.a,rules.OperationRefused('stale')]):
                            result=subject._invoke_fresh(h.authority_pin,attempt,12.25)
                    else:result=subject._invoke_fresh(h.authority_pin,attempt,12.25)
                self.assertIs(result['passed'],False);self.assertEqual(h.api.fresh._execute.call_count,1)
                self.assertEqual(h.events.count('save:stage-result-v1.json'),1)
                self.assertNotIn(CANARY,repr(result))

    def test_parent_attempt_is_durable_before_supervision_and_never_reused(self):
        h=Metadata(live=False);seen=[]
        def failed_owner(request,begin):
            seen.append(h.r.ATTEMPT.read_bytes())
            return dict(status='owner_failed',worker_returncode=None,cleanup_complete=False,output_capture_complete=False,worker=None)
        with h.ports(),patch.object(subject,'_initial',return_value=h.a),patch.object(subject,'_supervise',side_effect=failed_owner) as own:
            result=subject._execute(h.authority_pin,12.25)
            self.assertIs(result['passed'],False);self.assertEqual(len(seen),1)
            self.assertIs(json.loads(seen[0])['no_retry'],True)
            with self.assertRaises(rules.OperationRefused):subject._execute(h.authority_pin,12.25)
        self.assertEqual(own.call_count,1);self.assertEqual(h.r.ATTEMPT.read_bytes(),seen[0])
        h.api.fresh._execute.assert_not_called()
