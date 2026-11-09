"""SDK10 activation control over synthetic host IO, never a target qualification.

Copyright 2026 LocalLore contributors. SPDX-License-Identifier: Apache-2.0
"""
import copy
from contextlib import ExitStack, redirect_stderr
import io
import importlib.util
import os
from pathlib import Path, PureWindowsPath
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import Mock, patch

ACTIVATION_PATH=Path(__file__).resolve().parents[2]/'benchmarks/transcript_ui_activation.py'
SPEC=importlib.util.spec_from_file_location('_b50_activation_under_test',ACTIVATION_PATH)
activation=importlib.util.module_from_spec(SPEC)
exec(compile(ACTIVATION_PATH.read_bytes(),str(ACTIVATION_PATH),'exec'),activation.__dict__)

# Other discovery modules may already cache this repository's benchmarks package.
# Test only: select that same repository while importing real public APIs, then
# immediately restore the production fixed CI root. No production guard changes.
TEST_REPO=Path(__file__).resolve().parents[2]
with patch.object(activation,'SOURCE_ROOT',TEST_REPO):
    REAL = activation._api()
from scripts.tests import test_transcript_ui_profile as fixture


def identity(pid, executable='C:/Synthetic/python.exe'):
    return dict(pid=pid,creation_filetime=100000+pid,executable=executable)


class Graph:
    """Real contract/authorization/JSON; only process, SDK and file lookup seams are fake."""
    def __init__(self, root):
        self.root=root;self.runtime=root/'runtime';self.control=self.runtime/'control-v1'
        self.control.mkdir(parents=True);self.owned=self.runtime/'owned-v1';self.owned.mkdir()
        self.input_path=root/'controls/run-input-v1.json';self.input_path.parent.mkdir()
        self.a=fixture.admission();self.a.update(root=str(self.owned),seconds=1700)
        self.a['server'].update(root=str(self.owned/'server'),seconds=1700)
        self.admission_pin=fixture.legacy.pin(self.runtime/'admission-v1.json')
        self.value=dict(version=1,scope='transcript-ui-run-input-v1',admission=self.admission_pin,
                        helper=fixture.legacy.pin(ACTIVATION_PATH))
        self.proposal=dict(phase='run',paths=dict(root=self.a['guest']['root']),memory_mib=8192,cores=4,max_seconds=1800)
        self.auth=dict(version=1,phase='run',proposal_sha256=self.a['guest']['proposal']['sha256'],
                       allow_environment_calls=True,root_go_pending=False)
        self.input_pin=fixture.legacy.pin(self.input_path)
        python=self.a['python']['executable']['path']
        self.parent=identity(9000,python);self.worker=identity(9001,python)
        self.owner=identity(7101,python);self.caller=identity(7200,python)
        self.request=dict(version=1,scope='transcript-ui-worker-request-v1',input=self.input_pin,parent=self.parent,running=None)
        self.data={};self.saves=[];self.faults=set();self.inputs_calls=0;self.polls=0
        self.inputs_calls=1 # The runtime starts only after its initial validated input.
        for pin,value in [(self.input_pin,self.value),(self.admission_pin,self.a),
                          (self.a['guest']['proposal'],self.proposal),(self.a['guest']['authorization'],self.auth),
                          (self.value['helper'],{})]:
            self.data[pin['path']]=(pin,copy.deepcopy(value))
        self.child=SimpleNamespace(pid=7101,poll=self.poll)
        self.observer=SimpleNamespace(guard=Mock(),close=Mock(return_value=True))
        self.capture=SimpleNamespace(start=Mock(),guard=Mock(),close=Mock(return_value=True))
        self.terminal=dict(status='child_exited',worker_returncode=0,cleanup_complete=True,output_capture_complete=True)
        self.running=fixture.running(self.a);self.running['admission']=self.admission_pin;self.running['owner']=self.owner
        self.running_pin=self.put(self.owned/'running-v1.json',self.running,touch=True)
        self.put(self.control/'worker-request-v1.json',self.request,touch=True)
        self.public_request=self.put(root/'public-request.json',dict(owner=self.owner))
        self.public_started=self.put(root/'public-started.json',dict(worker=self.running['worker']))
        self.worker_result=self.put(root/'worker-result.json',{})
        self.public=dict(qualified_target=True,reason='stop_requested',admission=self.admission_pin,
            request=self.public_request,started=self.public_started,worker_result=self.worker_result,
            owner=fixture.legacy.pin(root/'owner.json'),after=fixture.legacy.pin(root/'after.json'))
        self.put(self.owned/'result-v1.json',self.public)
        self.record=dict(reason='stop_requested',cleanup={key:True for key in REAL.contract.CLEANUP_KEYS})
        closure=dict(closure_verified=True,cleanup_complete=True,admission=self.admission_pin,
            worker_result=self.worker_result,owner_result=self.public['owner'],after=self.public['after'],
            proposal_sha256=self.a['guest']['proposal']['sha256'])
        self.closure_path=Path(self.a['guest']['root'])/'guest-storage-closure-v1.json'
        self.closure_pin=self.put(self.closure_path,closure)
        registry=root/'registry';self.ledger_path=registry/'ledger-v1.json'
        self.put(self.ledger_path,dict(entries=[dict(root=self.a['guest']['root'],state='closed',
            proposal_sha256=self.a['guest']['proposal']['sha256'],closure=self.closure_pin)]))
        self.controller_pin=self.put(self.owned/'controller-v1/controller-result-v1.json',dict(outcome='completed'))
        for name in ('owner-stdout-v1.bin','owner-stderr-v1.bin'):
            path=self.control/'owner-console-v1'/name;path.parent.mkdir(exist_ok=True);path.write_bytes(b'')
        self.api=SimpleNamespace(env=SimpleNamespace(encoded=REAL.env.encoded,decode_json=REAL.env.decode_json,
            create_json=REAL.env.create_json,binding=self.binding,check_binding=self.check,
            check_authorization=REAL.env.check_authorization,
            supervise=Mock(side_effect=self.supervise),guest_storage=SimpleNamespace(DEFAULT_REGISTRY=registry)),
            contract=REAL.contract,owner=SimpleNamespace(LiveOwnedTranscriptUiTarget=Mock(return_value=self.observer)),
            process=SimpleNamespace(ServerCapture=Mock(return_value=self.capture)),controller=SimpleNamespace(
                run=Mock(return_value=dict(outcome='completed')),verify_controller_result=Mock(side_effect=self.verify_controller)),
            verification=SimpleNamespace(verify_owned_target_result=Mock(side_effect=self.verify_owner)))

    def put(self,path,data,touch=False):
        pin=fixture.legacy.pin(path);self.data[str(path)]=(pin,copy.deepcopy(data))
        if touch:
            path.parent.mkdir(parents=True,exist_ok=True);path.write_bytes(REAL.env.encoded(data))
        return pin

    def binding(self,path):
        path=Path(path)
        if 'binding' in self.faults and path.name=='owner-stdout-v1.bin':raise OSError('synthetic')
        if 'request_binding' in self.faults and path.name=='worker-request-v1.json':raise OSError('synthetic')
        return copy.deepcopy(self.data[str(path)][0]) if str(path) in self.data else REAL.env.binding(path)

    def check(self,pin):
        assert REAL.env.encoded(pin)==REAL.env.encoded(self.binding(pin['path']))

    def bound(self,pin,cap=131072):
        if str(pin['path']) in self.data:
            assert activation._same(pin,self.data[str(pin['path'])][0]);return copy.deepcopy(self.data[str(pin['path'])][1])
        return REAL.env.read_json(pin['path'])

    def save(self,path,value):
        name=path.name;self.saves.append(name)
        if name in self.faults:raise OSError('synthetic publication failure')
        REAL.env.create_json(path,value)
        return REAL.env.binding(path)

    def inputs(self,pin,fresh=False):
        self.inputs_calls+=1
        if 'post_source' in self.faults and self.inputs_calls>1:raise activation.ActivationRefused('source')
        return copy.deepcopy(self.value),activation._validate_metadata(self.value,self.a,self.proposal,self.auth)

    def poll(self):
        self.polls+=1
        if 'poll' in self.faults:raise OSError('synthetic poll failure')
        return 0

    def process_identity(self,pid,expected=None):
        value={7101:self.owner,7200:self.caller,9000:self.parent,9001:self.worker}[pid]
        if expected is not None and not activation._same(value,expected):raise activation.ActivationRefused('identity')
        return copy.deepcopy(value)

    def supervise(self,command,barrier,capture,seconds,on_started):
        assert command[-1]=='_controller' and seconds==1230
        assert barrier.startswith(activation.BARRIER)
        on_started(SimpleNamespace(pid=7200))
        return copy.deepcopy(self.terminal)

    def verify_controller(self,result,admission,running,caller):
        assert activation._same(result,self.controller_pin) and activation._same(admission,self.admission_pin)
        assert activation._same(running,self.running_pin) and activation._same(caller,self.caller)
        return dict(outcome='completed')

    def verify_owner(self,result,a,admission,request,worker):
        assert activation._same(result,self.worker_result) and activation._same(a,self.a)
        assert activation._same(admission,self.admission_pin) and activation._same(request,self.public_request)
        assert activation._same(worker,self.running['worker'])
        return copy.deepcopy(self.record)

    def patches(self):
        stack=ExitStack()
        for name,value in [('_api',lambda:self.api),('_identity',self.process_identity),('_bound',self.bound),
                           ('_inputs',self.inputs),('_save',self.save)]:stack.enter_context(patch.object(activation,name,value))
        for name,value in [('RUNTIME',self.runtime),('CONTROL',self.control),('INPUT',self.input_path),('HELPER',ACTIVATION_PATH)]:
            stack.enter_context(patch.object(activation,name,value))
        stack.enter_context(patch.object(activation.subprocess,'Popen',return_value=self.child))
        return stack


class TranscriptUiActivationImportTests(unittest.TestCase):
    def test_fixed_production_source_helper_and_barrier_literals_remain_unchanged(self):
        self.assertEqual("D:/Dev/Projects/The Hero's Journey/LocalLore-ci-review",activation.SOURCE_ROOT.as_posix())
        self.assertEqual('ed9b8e3e40e061e59c1a3404d77641a929bcbe32',activation.SOURCE_HEAD)
        self.assertEqual("D:/Dev/Projects/The Hero's Journey/LocalLore-android-review/benchmarks/transcript_ui_activation.py",
                         activation.HELPER.as_posix())
        self.assertEqual(b'transcript-ui-activation-worker-v1\n',activation.BARRIER)
        self.assertEqual((1800,1700,1730,1200,1230),(activation.OUTER_SECONDS,activation.OWNER_SECONDS,
            activation.PARENT_SECONDS,activation.CONTROLLER_SECONDS,activation.CALLER_SECONDS))


@unittest.skipUnless(os.name=='nt','Actual file fixtures require physical Windows D:')
class TranscriptUiActivationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.base=Path(tempfile.mkdtemp(prefix='locallore-b50-activation-',dir='D:/Dev/_Temp'))

    def graph(self):return Graph(Path(tempfile.mkdtemp(prefix='case-',dir=self.base)))

    def test_current_sdk10_metadata_is_real_contract_valid_and_detached(self):
        g=self.graph()
        with g.patches():
            admitted=activation._validate_metadata(g.value,g.a,g.proposal,g.auth)
            self.assertEqual(10,REAL.contract.CLIENT_VERSION);self.assertEqual(g.a,admitted)
            admitted['root']='changed';self.assertNotEqual(admitted,g.a)

    def test_old_crossprofile_model_extra_artifacts_and_bool_budgets_refuse(self):
        g=self.graph();bad=[]
        bad.append(dict(g.a,protocol='owned-emulator-player-presentation-ui-v1'))
        bad.append(dict(g.a,artifacts=dict(g.a['artifacts'],model=fixture.legacy.pin('D:/Synthetic/model.task'))))
        bad.append(dict(g.a,artifacts=dict(g.a['artifacts'],controller_apk=g.a['artifacts']['test_apk'])))
        bad.append(dict(g.a,seconds=True))
        with g.patches():
            for a in bad:
                with self.subTest(a=a),self.assertRaises((ValueError,REAL.contract.TargetRefused)):
                    activation._validate_metadata(g.value,a,g.proposal,g.auth)
            for key,value in [('memory_mib',True),('memory_mib',2048),('cores',2),('max_seconds',1801)]:
                with self.subTest(key=key),self.assertRaises(ValueError):
                    activation._validate_metadata(g.value,g.a,dict(g.proposal,**{key:value}),g.auth)

    def test_authorization_and_exact_input_paths_cannot_be_retargeted(self):
        g=self.graph()
        with g.patches():
            for auth in [dict(g.auth,root_go_pending=True),dict(g.auth,proposal_sha256='0'*64),dict(g.auth,extra=True)]:
                with self.assertRaises(REAL.env.EnvironmentRefused):activation._validate_metadata(g.value,g.a,g.proposal,auth)
            for v in [dict(g.value,version=True),dict(g.value,scope='old'),dict(g.value,callback='ignored'),
                      dict(g.value,helper=fixture.legacy.pin('D:/Synthetic/other.py'))]:
                with self.assertRaises(ValueError):activation._validate_input(v)

    def test_package_cache_cannot_select_a_foreign_build_module(self):
        import benchmarks
        fake=SimpleNamespace(__file__='D:/Synthetic/foreign/transcript_ui_build.py')
        with patch.object(activation,'SOURCE_ROOT',TEST_REPO),patch.object(activation,'_MODULES',None), \
             patch.object(benchmarks,'transcript_ui_build',fake):
            with self.assertRaises(activation.ActivationRefused):activation._api()
        self.assertEqual(TEST_REPO/'benchmarks',Path(REAL.build.__file__).parent)

    def test_complete_runtime_control_graph_passes_with_known_owner_caller_and_closure_joins(self):
        g=self.graph()
        with g.patches():
            runtime=activation._Runtime(g.request,g.worker,g.value,g.a)
            self.assertEqual(0,runtime.run())
            self.assertTrue(runtime.result['passed']);self.assertTrue(runtime.result['storage_closed'])
            self.assertEqual(1,g.api.env.supervise.call_count)
            self.assertEqual(1,g.api.controller.verify_controller_result.call_count)
            self.assertEqual(1,g.api.verification.verify_owned_target_result.call_count)
            self.assertEqual(2,g.observer.guard.call_count-1) # one readiness guard, two stop guards
            self.assertEqual(1,g.capture.close.call_count)
            self.assertTrue((g.owned/'stop-v1.json').exists())

    def test_foreign_running_owner_is_refused_before_observer_or_controller(self):
        g=self.graph();g.running['owner']=identity(7300,g.owner['executable']);g.put(g.owned/'running-v1.json',g.running,touch=True)
        with g.patches():
            runtime=activation._Runtime(g.request,g.worker,g.value,g.a)
            self.assertEqual(1,runtime.run());g.api.owner.LiveOwnedTranscriptUiTarget.assert_not_called()
            g.api.env.supervise.assert_not_called();self.assertFalse(runtime.stop_attempted)

    def test_owner_exit_before_ready_or_capture_fault_cannot_dispatch_controller(self):
        for fault in ['no_ready','capture']:
            g=self.graph()
            if fault=='no_ready':(g.owned/'running-v1.json').rename(g.owned/'retained-running.json')
            else:g.capture.guard.side_effect=OSError('synthetic')
            with g.patches():
                runtime=activation._Runtime(g.request,g.worker,g.value,g.a)
                self.assertEqual(1,runtime.run());g.api.env.supervise.assert_not_called()
                self.assertIn('runtime-result-v1.json',g.saves)

    def test_known_failed_controller_is_retained_and_stops_once_without_acceptance(self):
        g=self.graph();g.terminal['worker_returncode']=1
        with g.patches():
            runtime=activation._Runtime(g.request,g.worker,g.value,g.a)
            self.assertEqual(1,runtime.run());self.assertTrue(runtime.stop_attempted);self.assertTrue(runtime.stop_published)
            self.assertIn('controller-owner-result-v1.json',g.saves);self.assertFalse(runtime.result['controller_passed'])

    def test_unknown_controller_capture_cannot_accept_or_publish_stop(self):
        g=self.graph();g.terminal['output_capture_complete']=False
        with g.patches():
            runtime=activation._Runtime(g.request,g.worker,g.value,g.a)
            self.assertEqual(1,runtime.run());self.assertFalse(runtime.stop_attempted)

    def test_missing_actual_started_callback_cannot_accept_or_stop(self):
        g=self.graph();g.api.env.supervise.side_effect=lambda *args:copy.deepcopy(g.terminal)
        with g.patches():
            runtime=activation._Runtime(g.request,g.worker,g.value,g.a)
            self.assertEqual(1,runtime.run());self.assertIsNone(runtime.caller)
            self.assertFalse(runtime.stop_attempted);g.api.controller.verify_controller_result.assert_not_called()

    def test_invalid_helper_authorization_or_input_refuses_before_any_process_dispatch(self):
        original_inputs=activation._inputs
        for fault in ['helper','authorization','scope']:
            g=self.graph()
            if fault=='helper':g.data[str(g.input_path)][1]['helper']['sha256']='0'*64
            elif fault=='scope':g.data[str(g.input_path)][1]['scope']='old'
            else:g.data[g.a['guest']['authorization']['path']][1]['root_go_pending']=True
            with g.patches(),patch.object(activation,'_inputs',original_inputs), \
                 patch.object(activation,'_source',side_effect=AssertionError('metadata should refuse first')), \
                 patch.object(activation.subprocess,'Popen') as popen:
                with self.assertRaises((ValueError,REAL.env.EnvironmentRefused)):
                    activation._inputs(g.input_pin)
                popen.assert_not_called();g.api.env.supervise.assert_not_called()

    def test_raw_controller_owner_save_fault_preserves_known_terminal_safe_stop_but_not_pass(self):
        g=self.graph();g.faults.add('controller-owner-result-v1.json')
        with g.patches():
            runtime=activation._Runtime(g.request,g.worker,g.value,g.a)
            self.assertEqual(1,runtime.run());self.assertTrue(runtime.stop_published)
            g.api.controller.verify_controller_result.assert_not_called()

    def test_poll_error_is_sticky_and_capture_terminal_and_runtime_are_still_attempted(self):
        g=self.graph();g.faults.add('poll')
        with g.patches():
            runtime=activation._Runtime(g.request,g.worker,g.value,g.a)
            self.assertEqual(1,runtime.run());self.assertEqual(1,g.polls)
            self.assertFalse(runtime.result['owner_wait_known']);self.assertFalse(runtime.result['cleanup_known'])
            self.assertEqual(1,g.capture.close.call_count)
            self.assertIn('original-owner-terminal-v1.json',g.saves);self.assertIn('runtime-result-v1.json',g.saves)

    def test_independent_observer_capture_binding_and_terminal_faults_cannot_repair_cleanup(self):
        for fault in ['observer','capture','binding','original-owner-terminal-v1.json','request_binding']:
            g=self.graph()
            if fault=='observer':g.observer.close.side_effect=OSError('synthetic')
            elif fault=='capture':g.capture.close.side_effect=OSError('synthetic')
            else:g.faults.add(fault)
            with g.patches():
                runtime=activation._Runtime(g.request,g.worker,g.value,g.a)
                self.assertEqual(1,runtime.run());self.assertFalse(runtime.result['cleanup_known'])
                self.assertEqual(1,g.capture.close.call_count);self.assertIn('runtime-result-v1.json',g.saves)

    def test_runtime_publication_fault_emits_one_bounded_diagnostic_without_alternate_file(self):
        g=self.graph();g.faults.add('runtime-result-v1.json');stderr=io.StringIO()
        with g.patches(),redirect_stderr(stderr):
            runtime=activation._Runtime(g.request,g.worker,g.value,g.a)
            self.assertEqual(1,runtime.run());self.assertFalse(runtime.result['passed'])
        self.assertEqual(1,g.saves.count('runtime-result-v1.json'));self.assertEqual(1,len(stderr.getvalue().splitlines()))
        self.assertLess(len(stderr.getvalue()),256)

    def test_outer_execute_joins_worker_and_independently_attempts_final_receipt_after_faults(self):
        for fault in [None,'outer-owner-result-v1.json','final-result-v1.json','missing_callback']:
            g=self.graph();g.control.rename(g.root/'retained-controls')
            g.data.pop(str(g.control/'worker-request-v1.json'))
            g.api.env.safe_path=REAL.env.safe_path
            if fault in ['outer-owner-result-v1.json','final-result-v1.json']:g.faults.add(fault)
            def supervise(command,barrier,capture,seconds,on_started):
                self.assertEqual('_worker',command[-1]);self.assertEqual(1800,seconds)
                envelope=REAL.env.decode_json(barrier[len(activation.BARRIER):])
                if fault!='missing_callback':on_started(SimpleNamespace(pid=9001))
                g.put(g.control/'runtime-result-v1.json',dict(passed=True,input=g.input_pin,
                    request=envelope['request'],worker=g.worker),touch=True)
                return copy.deepcopy(g.terminal)
            g.api.env.supervise.side_effect=supervise;stderr=io.StringIO()
            with g.patches(),patch.object(activation.os,'getpid',return_value=9000), \
                 patch.object(activation.Path,'cwd',return_value=activation.SOURCE_ROOT), \
                 patch.object(activation.sys,'executable',g.parent['executable']),redirect_stderr(stderr):
                result=activation.execute(g.input_pin)
            self.assertIs(result['passed'],fault is None)
            self.assertEqual(1,g.saves.count('final-result-v1.json'))
            if fault=='final-result-v1.json':
                self.assertTrue(result['publication_error']);self.assertEqual(1,len(stderr.getvalue().splitlines()))
            elif fault is not None:self.assertFalse(result['passed'])

    def test_cleanup_flags_storage_binding_and_post_source_drift_prevent_success(self):
        for fault in ['cleanup','closure','post_source']:
            g=self.graph()
            if fault=='cleanup':g.record['cleanup'][next(iter(g.record['cleanup']))]=False
            elif fault=='closure':g.data[str(g.closure_path)][1]['owner_result']=fixture.legacy.pin('D:/Synthetic/wrong-owner.json')
            else:g.faults.add('post_source')
            with g.patches():
                runtime=activation._Runtime(g.request,g.worker,g.value,g.a)
                self.assertEqual(1,runtime.run());self.assertFalse(runtime.result['passed'])

    def test_stop_attempt_is_spent_before_guard_and_pending_is_retained_without_retry(self):
        g=self.graph();g.observer.guard.side_effect=[None,OSError('second guard')]
        with g.patches():
            runtime=activation._Runtime(g.request,g.worker,g.value,g.a)
            runtime.child=g.child;runtime.capture=g.capture;runtime.observer=g.observer
            runtime.original_owner=g.owner;runtime.caller=g.caller;runtime.controller_owner=g.terminal
            runtime.cleanup();self.assertTrue(runtime.stop_attempted);self.assertFalse(runtime.stop_published)
            self.assertTrue((g.owned/'stop.pending-v1.json').exists());self.assertFalse((g.owned/'stop-v1.json').exists())
            runtime.cleanup();self.assertEqual(2,g.observer.guard.call_count)

    def barrier(self,g,kind='controller'):
        request=dict(version=1,scope='transcript-ui-'+kind+'-request-v1',input=g.input_pin,parent=g.parent,
                     running=g.running_pin if kind=='controller' else None)
        pin=g.put(g.control/(kind+'-request-v1.json'),request,touch=True)
        g.put(g.control/(kind+'-started-v1.json'),dict(request=pin,worker=g.worker),touch=True)
        return activation.BARRIER+REAL.env.encoded(dict(request=pin))

    def test_controller_barrier_requires_actual_started_self_and_parent_before_dispatch(self):
        g=self.graph();raw=self.barrier(g)
        with g.patches(),patch.object(activation.sys,'stdin',SimpleNamespace(buffer=io.BytesIO(raw))), \
             patch.object(activation.os,'getpid',return_value=9001),patch.object(activation.os,'getppid',return_value=9000):
            self.assertEqual(0,activation._controller_worker())
            g.api.controller.run.assert_called_once_with(g.admission_pin,g.running_pin)

    def test_wrong_barrier_request_start_self_birth_or_parent_never_calls_controller(self):
        for fault in ['barrier','request','start','birth','parent']:
            g=self.graph();raw=self.barrier(g)
            if fault=='barrier':raw=b'old-worker\n'+raw
            elif fault=='request':g.data[str(g.control/'controller-request-v1.json')][1]['scope']='old'
            elif fault=='start':g.data[str(g.control/'controller-started-v1.json')][1]['request']=g.input_pin
            elif fault=='birth':g.data[str(g.control/'controller-started-v1.json')][1]['worker']['creation_filetime']+=1
            with g.patches(),patch.object(activation.sys,'stdin',SimpleNamespace(buffer=io.BytesIO(raw))), \
                 patch.object(activation.os,'getpid',return_value=9001),patch.object(activation.os,'getppid',return_value=9999 if fault=='parent' else 9000):
                with self.assertRaises(ValueError):activation._controller_worker()
                g.api.controller.run.assert_not_called()


if __name__=='__main__':
    unittest.main()
