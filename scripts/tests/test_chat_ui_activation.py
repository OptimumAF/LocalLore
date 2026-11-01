"""SDK11 activation control over synthetic host IO, never a target qualification.

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

ACTIVATION_PATH=Path(__file__).resolve().parents[2]/'benchmarks/chat_ui_activation.py'
SPEC=importlib.util.spec_from_file_location('_b56_activation_under_test',ACTIVATION_PATH)
activation=importlib.util.module_from_spec(SPEC)
exec(compile(ACTIVATION_PATH.read_bytes(),str(ACTIVATION_PATH),'exec'),activation.__dict__)

# Other discovery modules may already cache this repository's benchmarks package.
# Test only: select that same repository while importing real public APIs, then
# immediately restore the production fixed CI root. No production guard changes.
TEST_REPO=Path(__file__).resolve().parents[2]
with patch.object(activation,'SOURCE_ROOT',TEST_REPO):
    REAL = activation._api()
from scripts.tests import test_chat_ui_controller_fixtures as fixture


def identity(pid, executable='C:/Synthetic/python.exe'):
    return dict(pid=pid,creation_filetime=100000+pid,executable=executable)


class Graph:
    """Coordinator-only fault harness; never a product or native qualification.

    Real admission/authorization grammar and create-only JSON are used. Stored
    owner/closure/controller outcomes and process identity are explicit boundary
    simulations; actual SDK/proof/JUnit replay has its own byte-backed cohort.
    """
    def __init__(self, root):
        self.root=root;self.runtime=root/'runtime';self.control=self.runtime/'control-v1'
        self.control.mkdir(parents=True);self.owned=self.runtime/'owned-v1';self.owned.mkdir()
        self.input_path=root/'controls/run-input-v1.json';self.input_path.parent.mkdir()
        self.a=fixture.admission();self.a.update(root=str(self.owned),seconds=1700)
        self.a['server'].update(root=str(self.owned/'server'),seconds=1700)
        self.admission_pin=fixture.legacy.pin(self.runtime/'admission-v1.json')
        self.value=dict(version=1,scope='chat-ui-run-input-v1',admission=self.admission_pin,
                        helper=fixture.legacy.pin(ACTIVATION_PATH))
        self.proposal=dict(phase='run',paths=dict(root=self.a['guest']['root']),memory_mib=8192,cores=4,max_seconds=1800)
        self.auth=dict(version=1,phase='run',proposal_sha256=self.a['guest']['proposal']['sha256'],
                       allow_environment_calls=True,root_go_pending=False)
        self.input_pin=fixture.legacy.pin(self.input_path)
        python=self.a['python']['executable']['path']
        self.parent=identity(9000,python);self.worker=identity(9001,python)
        self.owner=identity(7101,python);self.caller=identity(7200,python)
        self.request=dict(version=1,scope='chat-ui-worker-request-v1',input=self.input_pin,parent=self.parent,running=None)
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
        self.controller_path=self.owned/'controller-v1/controller-result-v1.json'
        self.controller_path.parent.mkdir()
        REAL.env.create_json(self.controller_path,dict(outcome='completed'))
        self.controller_pin=REAL.env.binding(self.controller_path)
        self.controller_verifications=[]
        for name in ('owner-stdout-v1.bin','owner-stderr-v1.bin'):
            path=self.control/'owner-console-v1'/name;path.parent.mkdir(exist_ok=True);path.write_bytes(b'')
        self.api=SimpleNamespace(env=SimpleNamespace(encoded=REAL.env.encoded,decode_json=REAL.env.decode_json,
            create_json=REAL.env.create_json,binding=self.binding,check_binding=self.check,
            check_authorization=REAL.env.check_authorization,
            supervise=Mock(side_effect=self.supervise),guest_storage=SimpleNamespace(DEFAULT_REGISTRY=registry)),
            contract=REAL.contract,owner=SimpleNamespace(LiveOwnedChatUiTarget=Mock(return_value=self.observer)),
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
        self.controller_verifications.append(copy.deepcopy((result,admission,running,caller)))
        REAL.env.check_binding(result)
        assert activation._same(result,self.controller_pin) and activation._same(admission,self.admission_pin)
        assert activation._same(running,self.running_pin) and activation._same(caller,self.caller)
        assert REAL.env.read_json(result['path']) == dict(outcome='completed')
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


class ChatUiActivationImportTests(unittest.TestCase):
    def test_import_has_no_filesystem_process_or_native_effect_and_paths_are_fixed(self):
        source = ACTIVATION_PATH.read_bytes()
        namespace = {'__file__': str(ACTIVATION_PATH), '__name__': '_b56_import_only'}
        with patch.object(Path, 'open', side_effect=AssertionError('unexpected open')), \
             patch.object(Path, 'stat', side_effect=AssertionError('unexpected stat')), \
             patch.object(Path, 'resolve', side_effect=AssertionError('unexpected resolve')), \
             patch.object(activation.subprocess, 'Popen', side_effect=AssertionError('unexpected process')):
            exec(compile(source, str(ACTIVATION_PATH), 'exec'), namespace)
        self.assertEqual(namespace['SOURCE_ROOT'].as_posix(),
                         "D:/Dev/Projects/The Hero's Journey/LocalLore-control-review")
        self.assertEqual(namespace['HELPER'], namespace['SOURCE_ROOT'] / 'benchmarks/chat_ui_activation.py')
        self.assertEqual(namespace['RUNTIME'].as_posix(),
                         'D:/Dev/Experiments/LocalLore/2026-11-01-current-chat-ui-run-v1')
        self.assertEqual(namespace['BARRIER'], b'chat-ui-activation-worker-v1\n')
        self.assertEqual((namespace['OUTER_SECONDS'], namespace['OWNER_SECONDS'],
                          namespace['CALLER_SECONDS'], namespace['CONTROLLER_SECONDS']),
                         (1800, 1700, 1230, 1200))
        self.assertNotIn('SOURCE_HEAD', namespace)


@unittest.skipUnless(os.name == 'nt', 'Actual tiny files require physical D:')
class ChatUiActivationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        parent = Path('D:/Dev/Experiments/LocalLore/2026-11-01-current-chat-host-fixtures-v1/controller')
        parent.mkdir(parents=True, exist_ok=True)
        cls.base = Path(tempfile.mkdtemp(prefix='activation-', dir=parent))

    def graph(self):
        return Graph(Path(tempfile.mkdtemp(prefix='case-', dir=self.base)))

    def test_sdk11_metadata_requires_exact_profile_authorization_resources_and_input(self):
        g = self.graph()
        with g.patches():
            self.assertEqual(REAL.contract.CLIENT_VERSION, 11)
            self.assertEqual(activation._validate_metadata(g.value, g.a, g.proposal, g.auth), g.a)
            for value in [dict(g.a, protocol='owned-emulator-transcript-ui-v1'),
                          dict(g.a, artifacts=dict(g.a['artifacts'], model=fixture.legacy.pin('D:/Synthetic/model.task'))),
                          dict(g.a, seconds=True)]:
                with self.assertRaises((ValueError, REAL.contract.TargetRefused)):
                    activation._validate_metadata(g.value, value, g.proposal, g.auth)
            for key, value in [('memory_mib', True), ('cores', 2), ('max_seconds', 1801)]:
                with self.assertRaises(ValueError):
                    activation._validate_metadata(g.value, g.a, dict(g.proposal, **{key: value}), g.auth)
            for auth in [dict(g.auth, root_go_pending=True),
                         dict(g.auth, proposal_sha256='a' * 64)]:
                with self.assertRaises(REAL.env.EnvironmentRefused):
                    activation._validate_metadata(g.value, g.a, g.proposal, auth)

    def test_metadata_refusal_precedes_source_build_and_any_process_dispatch(self):
        real_inputs = activation._inputs
        for fault in ('scope', 'helper', 'authorization'):
            g = self.graph()
            if fault == 'scope':
                g.data[str(g.input_path)][1]['scope'] = 'transcript-ui-run-input-v1'
            elif fault == 'helper':
                g.data[str(g.input_path)][1]['helper']['path'] = 'D:/Synthetic/other.py'
            else:
                g.data[g.a['guest']['authorization']['path']][1]['root_go_pending'] = True
            with g.patches(), patch.object(activation, '_inputs', real_inputs), \
                 patch.object(activation, '_source', side_effect=AssertionError('source reached')), \
                 patch.object(activation.subprocess, 'Popen') as popen:
                with self.assertRaises((ValueError, REAL.env.EnvironmentRefused)):
                    activation._inputs(g.input_pin)
                popen.assert_not_called()
                g.api.env.supervise.assert_not_called()

    def test_complete_coordinator_replays_identical_controller_binding_after_cleanup(self):
        g = self.graph()
        with g.patches():
            runtime = activation._Runtime(g.request, g.worker, g.value, g.a)
            self.assertEqual(runtime.run(), 0)
            self.assertTrue(runtime.result['passed'])
            self.assertTrue(runtime.result['storage_closed'])
            self.assertEqual(len(g.controller_verifications), 2)
            self.assertEqual(g.controller_verifications[0], g.controller_verifications[1])
            self.assertTrue(runtime.stop_published)
            self.assertEqual(g.capture.close.call_count, 1)
            self.assertEqual(g.observer.close.call_count, 1)
            self.assertEqual(g.api.env.supervise.call_count, 1)
            self.assertLess(g.saves.index('controller-owner-result-v1.json'),
                            g.saves.index('original-owner-terminal-v1.json'))
            self.assertLess(g.saves.index('original-owner-terminal-v1.json'),
                            g.saves.index('runtime-result-v1.json'))

    def test_changed_controller_bytes_between_first_replay_and_owner_cleanup_cannot_pass(self):
        g = self.graph()
        def close():
            g.controller_path.write_bytes(REAL.env.encoded(dict(outcome='refused')))
            return True
        g.observer.close.side_effect = close
        with g.patches():
            runtime = activation._Runtime(g.request, g.worker, g.value, g.a)
            self.assertEqual(runtime.run(), 1)
            self.assertTrue(runtime.result['cleanup_known'])
            self.assertTrue(runtime.result['owner_wait_known'])
            self.assertFalse(runtime.result['passed'])
            self.assertEqual(len(g.controller_verifications), 2)
            self.assertEqual(g.controller_verifications[0], g.controller_verifications[1])
            self.assertIn('runtime-result-v1.json', g.saves)
            self.assertEqual(g.controller_pin['sha256'],
                             g.controller_verifications[-1][0]['sha256'])

    def test_running_owner_birth_mismatch_never_opens_observer_or_dispatches_controller(self):
        g = self.graph()
        g.running['owner']['creation_filetime'] += 1
        g.put(g.owned / 'running-v1.json', g.running, touch=True)
        with g.patches():
            runtime = activation._Runtime(g.request, g.worker, g.value, g.a)
            self.assertEqual(runtime.run(), 1)
            g.api.owner.LiveOwnedChatUiTarget.assert_not_called()
            g.api.env.supervise.assert_not_called()
            self.assertFalse(runtime.stop_attempted)

    def test_unknown_caller_terminal_or_missing_actual_start_prohibits_stop(self):
        for fault in ('capture', 'cleanup', 'returncode', 'missing_start'):
            g = self.graph()
            if fault == 'capture':
                g.terminal['output_capture_complete'] = False
            elif fault == 'cleanup':
                g.terminal['cleanup_complete'] = False
            elif fault == 'returncode':
                g.terminal['worker_returncode'] = True
            else:
                g.api.env.supervise.side_effect = lambda *args: copy.deepcopy(g.terminal)
            with g.patches():
                runtime = activation._Runtime(g.request, g.worker, g.value, g.a)
                self.assertEqual(runtime.run(), 1)
                self.assertFalse(runtime.stop_attempted)
                self.assertFalse((g.owned / 'stop-v1.json').exists())
                g.api.controller.verify_controller_result.assert_not_called()
                self.assertIn('controller-owner-result-v1.json', g.saves)

    def test_failed_caller_or_raw_result_publication_still_stops_only_known_process_once(self):
        for fault in ('failed_caller', 'controller-owner-result-v1.json'):
            g = self.graph()
            if fault == 'failed_caller':
                g.terminal['worker_returncode'] = 1
            else:
                g.faults.add(fault)
            with g.patches():
                runtime = activation._Runtime(g.request, g.worker, g.value, g.a)
                self.assertEqual(runtime.run(), 1)
                self.assertTrue(runtime.stop_attempted)
                self.assertTrue(runtime.stop_published)
                self.assertFalse(runtime.result['controller_passed'])
                self.assertEqual(g.saves.count('controller-owner-result-v1.json'), 1)
                self.assertIn('runtime-result-v1.json', g.saves)

    def test_poll_close_capture_and_terminal_faults_are_sticky_with_independent_publication(self):
        for fault in ('poll', 'observer', 'capture', 'binding',
                      'original-owner-terminal-v1.json', 'request_binding'):
            g = self.graph()
            if fault == 'observer':
                g.observer.close.side_effect = OSError('synthetic observer close')
            elif fault == 'capture':
                g.capture.close.side_effect = OSError('synthetic capture close')
            else:
                g.faults.add(fault)
            with g.patches():
                runtime = activation._Runtime(g.request, g.worker, g.value, g.a)
                self.assertEqual(runtime.run(), 1)
                self.assertFalse(runtime.result['cleanup_known'])
                self.assertEqual(g.capture.close.call_count, 1)
                self.assertIn('original-owner-terminal-v1.json', g.saves)
                self.assertIn('runtime-result-v1.json', g.saves)
                if fault == 'poll':
                    self.assertEqual(g.polls, 1)
                    self.assertFalse(runtime.result['owner_wait_known'])

    def test_runtime_publication_failure_returns_failure_and_one_bounded_diagnostic(self):
        g = self.graph()
        g.faults.add('runtime-result-v1.json')
        stderr = io.StringIO()
        with g.patches(), redirect_stderr(stderr):
            runtime = activation._Runtime(g.request, g.worker, g.value, g.a)
            self.assertEqual(runtime.run(), 1)
            self.assertFalse(runtime.result['passed'])
            self.assertFalse(runtime.result['cleanup_known'])
        self.assertEqual(g.saves.count('runtime-result-v1.json'), 1)
        self.assertEqual(len(stderr.getvalue().splitlines()), 1)
        self.assertLess(len(stderr.getvalue()), 256)

    def test_cleanup_flags_crossbound_closure_and_source_drift_cannot_be_repaired(self):
        for fault in ('cleanup', 'closure', 'source'):
            g = self.graph()
            if fault == 'cleanup':
                g.record['cleanup'][next(iter(g.record['cleanup']))] = False
            elif fault == 'closure':
                g.data[str(g.closure_path)][1]['owner_result'] = fixture.legacy.pin('D:/Synthetic/foreign.json')
            else:
                g.faults.add('post_source')
            with g.patches():
                runtime = activation._Runtime(g.request, g.worker, g.value, g.a)
                self.assertEqual(runtime.run(), 1)
                self.assertFalse(runtime.result['passed'])
                self.assertIn('runtime-result-v1.json', g.saves)

    def test_uncertain_atomic_stop_retains_pending_and_is_never_retried(self):
        g = self.graph()
        g.observer.guard.side_effect = [None, OSError('second guard failed')]
        with g.patches():
            runtime = activation._Runtime(g.request, g.worker, g.value, g.a)
            runtime.child, runtime.capture, runtime.observer = g.child, g.capture, g.observer
            runtime.original_owner, runtime.caller, runtime.controller_owner = g.owner, g.caller, g.terminal
            runtime.cleanup()
            self.assertTrue(runtime.stop_attempted)
            self.assertFalse(runtime.stop_published)
            self.assertFalse(runtime.result['cleanup_known'])
            self.assertTrue((g.owned / 'stop.pending-v1.json').exists())
            self.assertFalse((g.owned / 'stop-v1.json').exists())
            runtime.cleanup()
            self.assertEqual(g.observer.guard.call_count, 2)

    def barrier(self, g):
        request = dict(version=1, scope='chat-ui-controller-request-v1', input=g.input_pin,
                       parent=g.parent, running=g.running_pin)
        pin = g.put(g.control / 'controller-request-v1.json', request, touch=True)
        g.put(g.control / 'controller-started-v1.json', dict(request=pin, worker=g.worker), touch=True)
        return activation.BARRIER + REAL.env.encoded(dict(request=pin))

    def test_controller_entry_requires_actual_start_request_self_birth_and_parent(self):
        for fault in (None, 'barrier', 'request', 'birth', 'parent'):
            g = self.graph()
            raw = self.barrier(g)
            if fault == 'barrier':
                raw = b'transcript-ui-activation-worker-v1\n' + raw
            elif fault == 'request':
                g.data[str(g.control / 'controller-started-v1.json')][1]['request'] = g.input_pin
            elif fault == 'birth':
                g.data[str(g.control / 'controller-started-v1.json')][1]['worker']['creation_filetime'] += 1
            with g.patches(), patch.object(activation.sys, 'stdin', SimpleNamespace(buffer=io.BytesIO(raw))), \
                 patch.object(activation.os, 'getpid', return_value=9001), \
                 patch.object(activation.os, 'getppid', return_value=9999 if fault == 'parent' else 9000):
                if fault is None:
                    self.assertEqual(activation._controller_worker(), 0)
                    g.api.controller.run.assert_called_once_with(g.admission_pin, g.running_pin)
                else:
                    with self.assertRaises(ValueError):
                        activation._controller_worker()
                    g.api.controller.run.assert_not_called()


if __name__ == '__main__':
    unittest.main()
