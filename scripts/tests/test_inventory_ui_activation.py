"""Original SDK12 coordinator fault graph; no native or target qualification.

Metadata, authorization, bindings and create-only JSON use public validators.
Identities, completed owner records and controller outcomes are explicit simulated
boundaries. SDK/proof/JUnit replay belongs to the controller's separate cohort.
"""
import copy
from contextlib import ExitStack, redirect_stderr
import importlib.util
import io
import os
from pathlib import Path, PureWindowsPath
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import Mock, patch

from scripts.tests import test_inventory_ui_profile as profile


REPO = Path(__file__).resolve().parents[2]
SOURCE = REPO/'benchmarks/inventory_ui_activation.py'
spec = importlib.util.spec_from_file_location('_sdk12_activation_faults', SOURCE)
activation = importlib.util.module_from_spec(spec)
spec.loader.exec_module(activation)
with patch.object(activation, 'SOURCE_ROOT', REPO):
    REAL = activation._api()
FIXTURES = Path('D:/Dev/Experiments/LocalLore/2026-11-01-inventory-ui-host-fixtures-v1/activation')


def identity(pid, executable):
    return dict(pid=pid,creation_filetime=900000+pid,executable=executable)


class CoordinatorGraph:
    """Owned tiny byte records, with named native/process outcome boundaries."""
    def __init__(self):
        FIXTURES.mkdir(parents=True,exist_ok=True)
        self.root = Path(tempfile.mkdtemp(prefix='coordinator-',dir=FIXTURES))
        self.runtime = self.root/'runtime';self.owned = self.runtime/'owned-v1'
        self.control = self.runtime/'control-v1';self.control.mkdir(parents=True);self.owned.mkdir()
        self.helper = SOURCE;self.input_path = self.root/'run-input-v1.json'
        self.saves = [];self.verifications = [];self.owner_checks = [];self.faults = set()
        self.inputs_checked = 0;self.polls = 0;self.register_start = True
        self.terminal = dict(status='child_exited',worker_returncode=0,cleanup_complete=True,output_capture_complete=True)
        self.a = profile.admission();self.a.update(root=str(self.owned),seconds=1700)
        self.a['server'].update(root=str(self.owned/'server'),seconds=1700)
        self.a['sources'] = REAL.contract.source_bindings()
        by_name = {PureWindowsPath(pin['path']).name:pin for pin in self.a['sources']}
        self.a['server']['sources'] = sorted([copy.deepcopy(by_name[PureWindowsPath(pin['path']).name])
            for pin in self.a['server']['sources']],key=lambda pin:pin['path'])
        self.proposal = dict(phase='run',paths=dict(root=self.a['guest']['root']),memory_mib=8192,cores=4,max_seconds=1800)
        self.a['guest']['proposal'] = self.store(self.root/'proposal.json',self.proposal)
        self.auth = dict(version=1,phase='run',proposal_sha256=self.a['guest']['proposal']['sha256'],
                         allow_environment_calls=True,root_go_pending=False)
        self.a['guest']['authorization'] = self.store(self.root/'synthetic-authorization.json',self.auth)
        self.admission_pin = self.store(self.runtime/'admission-v1.json',self.a)
        self.value = dict(version=1,scope='inventory-ui-run-input-v1',admission=self.admission_pin,helper=REAL.env.binding(SOURCE))
        self.input_pin = self.store(self.input_path,self.value)
        exe = self.a['python']['executable']['path']
        self.parent,self.worker,self.owner,self.caller = [identity(pid,exe) for pid in (6100,6101,7101,7300)]
        self.request = dict(version=1,scope='inventory-ui-worker-request-v1',input=self.input_pin,parent=self.parent,running=None)
        self.store(self.control/'worker-request-v1.json',self.request)
        self.running = profile.running(self.a)
        self.running.update(admission=self.admission_pin,owner=self.owner)
        self.running_pin = self.store(self.owned/'running-v1.json',self.running)
        self.controller_path = self.owned/'controller-v1/controller-result-v1.json'
        self.controller_body = dict(scope='synthetic-controller-boundary-v1',outcome='completed',
                                    admission=self.admission_pin,running=self.running_pin,caller=self.caller)
        self.controller_pin = self.store(self.controller_path,self.controller_body)
        public_request = self.store(self.root/'owner-request.json',dict(owner=self.owner))
        public_started = self.store(self.root/'owner-started.json',dict(worker=self.running['worker']))
        self.worker_pin = self.store(self.root/'worker-result.json',dict(scope='simulated-worker-boundary-v1'))
        self.cleanup_record = dict(reason='stop_requested',cleanup={name:True for name in REAL.contract.CLEANUP_KEYS})
        self.public = dict(qualified_target=True,reason='stop_requested',admission=self.admission_pin,
            request=public_request,started=public_started,worker_result=self.worker_pin,
            owner=self.store(self.root/'native-owner.json',dict(scope='simulated-owner-boundary-v1')),
            after=self.store(self.root/'after.json',dict(scope='simulated-after-boundary-v1')))
        self.store(self.owned/'result-v1.json',self.public)
        self.closure = dict(closure_verified=True,cleanup_complete=True,admission=self.admission_pin,
            worker_result=self.worker_pin,owner_result=self.public['owner'],after=self.public['after'],
            proposal_sha256=self.a['guest']['proposal']['sha256'])
        self.closure_pin = self.store(self.root/'synthetic-closure.json',self.closure)
        self.registry = self.root/'synthetic-registry'
        self.store(self.registry/'ledger-v1.json',dict(entries=[dict(root=self.a['guest']['root'],state='closed',
            closure=self.closure_pin,proposal_sha256=self.a['guest']['proposal']['sha256'])]))
        for name in ('owner-stdout-v1.bin','owner-stderr-v1.bin'):
            p=self.control/'owner-console-v1'/name;p.parent.mkdir(exist_ok=True);p.write_bytes(b'')
        self.child = SimpleNamespace(pid=self.owner['pid'],poll=self.poll)
        self.capture = SimpleNamespace(start=Mock(),guard=Mock(),close=Mock(return_value=True))
        self.observer = SimpleNamespace(guard=Mock(),close=Mock(return_value=True))
        self.api = SimpleNamespace(contract=REAL.contract,
            env=SimpleNamespace(encoded=REAL.env.encoded,decode_json=REAL.env.decode_json,create_json=REAL.env.create_json,
                binding=self.binding,check_binding=REAL.env.check_binding,check_authorization=REAL.env.check_authorization,
                guest_storage=SimpleNamespace(DEFAULT_REGISTRY=self.registry),supervise=Mock(side_effect=self.supervise)),
            owner=SimpleNamespace(LiveOwnedInventoryUiTarget=Mock(return_value=self.observer)),
            process=SimpleNamespace(ServerCapture=Mock(return_value=self.capture)),
            controller=SimpleNamespace(verify_controller_result=Mock(side_effect=self.verify_controller),run=Mock()),
            verification=SimpleNamespace(verify_owned_target_result=Mock(side_effect=self.verify_owner)))

    @staticmethod
    def store(path,value):
        path.parent.mkdir(parents=True,exist_ok=True)
        REAL.env.create_json(path,value)
        return REAL.env.binding(path)

    def binding(self,path):
        path=Path(path)
        if 'capture_binding' in self.faults and path.name=='owner-stdout-v1.bin':raise OSError('capture evidence')
        if path==Path(self.a['guest']['root'])/'guest-storage-closure-v1.json':
            # Only this selected simulated external boundary maps into owned data.
            return copy.deepcopy(self.closure_pin)
        return REAL.env.binding(path)

    def save(self,path,value):
        self.saves.append(path.name)
        if path.name in self.faults:raise OSError('publication fault')
        return self.store(path,value)

    def inputs(self,pin,*,fresh=False):
        self.inputs_checked+=1
        REAL.env.check_binding(pin)
        if 'source_after' in self.faults:raise activation.ActivationRefused('source')
        return copy.deepcopy(self.value),activation._validate_metadata(self.value,self.a,self.proposal,self.auth)

    def process_identity(self,pid,expected=None):
        known={v['pid']:v for v in (self.owner,self.caller,self.parent,self.worker)}
        actual=known[pid]
        if expected is not None:activation._need(activation._same(actual,expected),'identity')
        return copy.deepcopy(actual)

    def poll(self):
        self.polls+=1
        if 'poll' in self.faults:raise OSError('owner wait fault')
        return 0

    def supervise(self,argv,barrier,capture,seconds,on_started):
        assert argv==[activation.sys.executable,'-I','-S','-B',str(SOURCE),'_controller']
        assert seconds==1230 and capture==self.control/'controller-owner-v1'
        request=REAL.env.decode_json(barrier[len(activation.BARRIER):])
        assert barrier.startswith(activation.BARRIER) and set(request)=={'request'}
        REAL.env.check_binding(request['request'])
        if self.register_start:on_started(SimpleNamespace(pid=self.caller['pid']))
        return copy.deepcopy(self.terminal)

    def verify_controller(self,result,admission,running,caller):
        self.verifications.append(copy.deepcopy((result,admission,running,caller)))
        # Explicit boundary simulation still verifies actual bytes and all joins.
        REAL.env.check_binding(result)
        assert result==self.controller_pin and admission==self.admission_pin
        assert running==self.running_pin and caller==self.caller
        assert REAL.env.read_json(result['path'])==self.controller_body
        return dict(outcome='completed')

    def verify_owner(self,result,a,admission,request,worker):
        self.owner_checks.append(copy.deepcopy((result,a,admission,request,worker)))
        assert result==self.worker_pin and a==self.a and admission==self.admission_pin
        assert request==self.public['request'] and worker==self.running['worker']
        for pin in (result,request,self.public['started']):REAL.env.check_binding(pin)
        return copy.deepcopy(self.cleanup_record)

    def patches(self):
        stack=ExitStack()
        for name,value in (('_api',lambda:self.api),('_identity',self.process_identity),('_inputs',self.inputs),('_save',self.save),
                           ('SOURCE_ROOT',REPO),('HELPER',SOURCE),('INPUT',self.input_path),('RUNTIME',self.runtime),('CONTROL',self.control)):
            stack.enter_context(patch.object(activation,name,value))
        stack.enter_context(patch.object(activation.subprocess,'Popen',return_value=self.child))
        return stack

    def run(self):
        runtime=activation._Runtime(self.request,self.worker,self.value,self.a)
        code=runtime.run()
        return runtime,code


class InventoryActivationTests(unittest.TestCase):
    def setUp(self):
        self.stack=ExitStack();self.addCleanup(self.stack.close)
        for target in ('socket.socket','socket.create_connection','subprocess.run',
                       'benchmarks.isolated_adb_owner.ProcessHandles','benchmarks.owned_target_owner._ProcessApi'):
            self.stack.enter_context(patch(target,side_effect=AssertionError('native/process/network forbidden')))

    def test_exact_sdk12_import_api_and_import_without_side_effects(self):
        self.assertEqual(REAL.contract.CLIENT_VERSION,12)
        self.assertIs(REAL.contract,profile.contract)
        self.assertEqual(REAL.owner.LiveOwnedInventoryUiTarget.__name__,'LiveOwnedInventoryUiTarget')
        self.assertEqual(REAL.controller.__name__,'benchmarks.inventory_ui_controller')
        raw=SOURCE.read_bytes()
        with patch.object(Path,'open',side_effect=AssertionError('import read')),patch.object(Path,'resolve',side_effect=AssertionError('import stat')):
            namespace={'__file__':str(SOURCE),'__name__':'import_only'}
            exec(compile(raw,str(SOURCE),'exec'),namespace)
        self.assertIsNone(namespace['_MODULES'])
        self.assertEqual((namespace['OUTER_SECONDS'],namespace['OWNER_SECONDS'],namespace['PARENT_SECONDS'],
                          namespace['CONTROLLER_SECONDS'],namespace['CALLER_SECONDS']),(1800,1700,1730,1200,1230))

    def test_metadata_and_authority_fences_precede_every_dispatch(self):
        original_inputs=activation._inputs
        for kind in ('protocol','root','input_scope','input_extra_model','helper','model','authorization','resource'):
            g=CoordinatorGraph()
            if kind=='protocol':g.a['protocol']='owned-emulator-current-chat-ui-v1'
            elif kind=='root':g.a['root']=str(g.runtime/'foreign-v1')
            elif kind=='input_scope':g.value['scope']='chat-ui-run-input-v1'
            elif kind=='input_extra_model':g.value['model']=g.value['helper']
            elif kind=='helper':g.value['helper']=dict(g.value['helper'],sha256='0'*64)
            elif kind=='model':g.a['artifacts']['model']=g.a['artifacts']['build']
            elif kind=='authorization':g.auth['root_go_pending']=True
            elif kind=='resource':g.proposal['cores']=2
            # Rebind only owned metadata so the actual validators see the fault.
            Path(g.a['guest']['proposal']['path']).write_bytes(REAL.env.encoded(g.proposal))
            g.a['guest']['proposal']=REAL.env.binding(g.a['guest']['proposal']['path'])
            g.auth['proposal_sha256']=g.a['guest']['proposal']['sha256']
            Path(g.a['guest']['authorization']['path']).write_bytes(REAL.env.encoded(g.auth))
            g.a['guest']['authorization']=REAL.env.binding(g.a['guest']['authorization']['path'])
            Path(g.admission_pin['path']).write_bytes(REAL.env.encoded(g.a))
            g.value['admission']=REAL.env.binding(g.admission_pin['path'])
            g.input_path.write_bytes(REAL.env.encoded(g.value));input_pin=REAL.env.binding(g.input_path)
            with self.subTest(kind=kind),g.patches(),patch.object(activation,'_inputs',original_inputs), \
                 patch.object(activation,'_source',side_effect=AssertionError('source reached before refusal')), \
                 patch.dict(os.environ,TEMP='D:/Dev/_Temp',TMP='D:/Dev/_Temp',TMPDIR='D:/Dev/_Temp'):
                with self.assertRaises((ValueError,REAL.env.EnvironmentRefused)):activation.execute(input_pin)
                activation.subprocess.Popen.assert_not_called();g.api.env.supervise.assert_not_called()

    def test_happy_flow_replays_identical_controller_binding_after_known_cleanup(self):
        g=CoordinatorGraph()
        with g.patches():runtime,code=g.run()
        self.assertEqual(code,0);self.assertTrue(runtime.result['passed'])
        self.assertTrue(runtime.result['owner_qualified']);self.assertTrue(runtime.result['storage_closed'])
        self.assertEqual(len(g.verifications),2);self.assertEqual(g.verifications[0],g.verifications[1])
        self.assertEqual(len(g.owner_checks),1);self.assertEqual(len(runtime.result['ledger']),3)
        self.assertTrue(runtime.stop_published);self.assertTrue(runtime.result['observer_closed'])
        self.assertEqual(g.capture.close.call_count,1);self.assertEqual(g.observer.close.call_count,1)
        self.assertEqual(g.api.env.supervise.call_count,1)
        self.assertEqual(g.saves.count('stop.pending-v1.json'),1)
        stop=REAL.env.read_json(g.owned/'stop-v1.json');REAL.contract.check_stop(stop,g.admission_pin['sha256'])
        self.assertFalse((g.owned/'stop.pending-v1.json').exists())
        self.assertLess(g.saves.index('controller-owner-result-v1.json'),g.saves.index('original-owner-terminal-v1.json'))
        self.assertLess(g.saves.index('original-owner-terminal-v1.json'),g.saves.index('runtime-result-v1.json'))
        self.assertFalse(runtime.result['feature_acceptance'])

    def test_controller_body_changed_during_owner_cleanup_keeps_original_binding_and_refuses(self):
        g=CoordinatorGraph()
        def close():
            g.controller_path.write_bytes(REAL.env.encoded(dict(g.controller_body,outcome='refused')))
            return True
        g.observer.close.side_effect=close
        with g.patches():runtime,code=g.run()
        self.assertEqual(code,1);self.assertFalse(runtime.result['passed'])
        self.assertTrue(runtime.result['cleanup_known']);self.assertEqual(len(g.verifications),2)
        self.assertEqual(g.verifications[0],g.verifications[1]);self.assertTrue(runtime.stop_published)
        self.assertEqual(g.verifications[1][0],g.controller_pin)
        self.assertIn('qualification_error',runtime.result)

    def test_unknown_caller_or_missing_actual_start_never_attempts_stop(self):
        for kind in ('capture','cleanup','noninteger','expired','no_start'):
            g=CoordinatorGraph()
            if kind=='capture':g.terminal['output_capture_complete']=False
            elif kind=='cleanup':g.terminal['cleanup_complete']=False
            elif kind=='noninteger':g.terminal['worker_returncode']=True
            elif kind=='expired':g.terminal['status']='deadline'
            else:g.register_start=False
            with self.subTest(kind=kind),g.patches():runtime,code=g.run()
            self.assertEqual(code,1);self.assertFalse(runtime.stop_attempted)
            self.assertFalse((g.owned/'stop-v1.json').exists());self.assertFalse((g.owned/'stop.pending-v1.json').exists())
            self.assertEqual(g.verifications,[]);self.assertIn('controller-owner-result-v1.json',g.saves)
            self.assertEqual(g.capture.close.call_count,1)

    def test_failed_known_caller_or_owner_result_save_failure_still_has_one_safe_stop(self):
        for kind in ('exit','publication'):
            g=CoordinatorGraph()
            if kind=='exit':g.terminal['worker_returncode']=1
            else:g.faults.add('controller-owner-result-v1.json')
            with self.subTest(kind=kind),g.patches():runtime,code=g.run()
            self.assertEqual(code,1);self.assertTrue(runtime.stop_published)
            self.assertFalse(runtime.result['controller_passed']);self.assertFalse(runtime.result['passed'])
            self.assertEqual(g.saves.count('stop.pending-v1.json'),1)
            self.assertIn('runtime-result-v1.json',g.saves)

    def test_atomic_stop_second_guard_failure_is_spent_and_never_retried(self):
        g=CoordinatorGraph();g.observer.guard.side_effect=[None,None,OSError('stop second guard')]
        with g.patches():
            runtime,code=g.run();runtime.cleanup()
        self.assertEqual(code,1);self.assertTrue(runtime.stop_attempted);self.assertFalse(runtime.stop_published)
        self.assertTrue((g.owned/'stop.pending-v1.json').exists());self.assertFalse((g.owned/'stop-v1.json').exists())
        self.assertFalse(runtime.result['cleanup_known']);self.assertEqual(g.saves.count('stop.pending-v1.json'),1)
        self.assertEqual(g.observer.guard.call_count,3)

    def test_cleanup_faults_stay_unknown_but_attempt_every_independent_tail(self):
        for kind in ('poll','observer','capture','capture_binding','original-owner-terminal-v1.json'):
            g=CoordinatorGraph()
            if kind=='observer':g.observer.close.side_effect=OSError('observer close')
            elif kind=='capture':g.capture.close.side_effect=OSError('capture close')
            else:g.faults.add(kind)
            with self.subTest(kind=kind),g.patches():runtime,code=g.run()
            self.assertEqual(code,1);self.assertFalse(runtime.result['passed']);self.assertFalse(runtime.result['cleanup_known'])
            self.assertEqual(g.capture.close.call_count,1);self.assertIn('original-owner-terminal-v1.json',g.saves)
            self.assertIn('runtime-result-v1.json',g.saves)
            if kind=='poll':self.assertEqual(g.polls,1);self.assertFalse(runtime.result['owner_wait_known'])

    def test_runtime_result_publication_failure_keeps_one_bounded_diagnostic(self):
        g=CoordinatorGraph();g.faults.add('runtime-result-v1.json');stderr=io.StringIO()
        with g.patches(),redirect_stderr(stderr):runtime,code=g.run()
        self.assertEqual(code,1);self.assertFalse(runtime.result['passed']);self.assertFalse(runtime.result['cleanup_known'])
        self.assertEqual(g.saves.count('runtime-result-v1.json'),1)
        self.assertEqual(len(stderr.getvalue().splitlines()),1);self.assertLess(len(stderr.getvalue()),256)

    def test_post_cleanup_source_or_cleanup_proof_cross_binding_never_qualifies(self):
        for kind in ('source','cleanup','closure'):
            g=CoordinatorGraph()
            if kind=='source':g.faults.add('source_after')
            elif kind=='cleanup':g.cleanup_record['cleanup'][next(iter(g.cleanup_record['cleanup']))]=False
            else:
                g.closure['after']=g.worker_pin
                Path(g.closure_pin['path']).write_bytes(REAL.env.encoded(g.closure))
                g.closure_pin=REAL.env.binding(g.closure_pin['path'])
            with self.subTest(kind=kind),g.patches():runtime,code=g.run()
            self.assertEqual(code,1);self.assertFalse(runtime.result['passed']);self.assertTrue(runtime.stop_published)
            self.assertIn('runtime-result-v1.json',g.saves)


if __name__=='__main__':
    unittest.main()
