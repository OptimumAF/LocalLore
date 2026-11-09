"""Original SDK16 coordinator fault graph; no native or target qualification.

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

from scripts.tests import test_knowledge_ui_controller_fixtures as profile


REPO = Path(__file__).resolve().parents[2]
SOURCE = REPO/'benchmarks/knowledge_ui_activation.py'
spec = importlib.util.spec_from_file_location('_sdk16_activation_faults', SOURCE)
activation = importlib.util.module_from_spec(spec)
spec.loader.exec_module(activation)
with patch.object(activation, 'SOURCE_ROOT', REPO):
    REAL = activation._api()
FIXTURES = profile.FIXTURE_ROOT / 'activation'


def identity(pid, executable):
    return dict(pid=pid,creation_filetime=900000+pid,executable=executable)


class CoordinatorGraph:
    """Owned tiny byte records, with named native/process outcome boundaries."""
    def __init__(self):
        profile.ensure_budget(1024 * 1024)
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
        self.value = dict(version=1,scope='knowledge-ui-run-input-v1',admission=self.admission_pin,helper=REAL.env.binding(SOURCE))
        self.input_pin = self.store(self.input_path,self.value)
        exe = self.a['python']['executable']['path']
        self.parent,self.worker,self.owner,self.caller = [identity(pid,exe) for pid in (6100,6101,7101,7300)]
        self.request = dict(version=1,scope='knowledge-ui-worker-request-v1',input=self.input_pin,parent=self.parent,running=None)
        self.store(self.control/'worker-request-v1.json',self.request)
        self.running = profile.running(self.a)
        self.running.update(admission=self.admission_pin,owner=copy.deepcopy(self.owner))
        self.running_pin = self.store(self.owned/'running-v1.json',self.running)
        self.controller_path = self.owned/'controller-v1/controller-result-v1.json'
        self.controller_body = dict(scope='synthetic-controller-boundary-v1',outcome='completed',
                                    admission=self.admission_pin,running=self.running_pin,caller=self.caller)
        self.controller_pin = self.store(self.controller_path,self.controller_body)
        public_request = self.store(self.root/'owner-request.json',dict(owner=copy.deepcopy(self.owner)))
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
            owner=SimpleNamespace(LiveOwnedKnowledgeUiTarget=Mock(return_value=self.observer)),
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


@unittest.skipUnless(os.name == 'nt', 'Tiny D records; native owners, identities and outcomes explicitly simulated')
class KnowledgeUiActivationTests(unittest.TestCase):
    def setUp(self):
        self.stack = ExitStack(); self.addCleanup(self.stack.close)
        for name in ('socket.socket', 'socket.create_connection', 'subprocess.run',
            'benchmarks.isolated_adb_owner.ProcessHandles', 'benchmarks.owned_target_owner._ProcessApi'):
            self.stack.enter_context(patch(name, side_effect=AssertionError('No real host lifecycle operation')))

    def test_lazy_definitions_preserve_fixed_sdk16_paths_and_all_existing_deadlines_without_io(self):
        self.assertEqual(REAL.contract.CLIENT_VERSION, 16)
        self.assertEqual(REAL.owner.LiveOwnedKnowledgeUiTarget.__name__, 'LiveOwnedKnowledgeUiTarget')
        self.assertEqual(REAL.controller.__name__, 'benchmarks.knowledge_ui_controller')
        self.assertEqual(REAL.build.__name__, 'benchmarks.knowledge_ui_profile_build')
        raw = SOURCE.read_bytes()
        with patch.object(Path, 'open', side_effect=AssertionError('Import read')), \
             patch.object(Path, 'resolve', side_effect=AssertionError('Import stat')):
            namespace = {'__file__': str(SOURCE), '__name__': 'definitions_only'}
            exec(compile(raw, str(SOURCE), 'exec'), namespace)
        self.assertIsNone(namespace['_MODULES'])
        frozen = Path('D:/Worktrees/LocalLore-original-input-compose-review-v1')
        controls = Path('D:/Dev/Experiments/LocalLore/2026-11-02-knowledge-ui-harness-v1/run-controls-v1')
        runtime = Path('D:/Dev/Experiments/LocalLore/2026-11-02-current-knowledge-ui-run-v1')
        self.assertEqual((namespace['SOURCE_ROOT'], namespace['HELPER']), (frozen, frozen / 'benchmarks/knowledge_ui_activation.py'))
        self.assertEqual((namespace['CONTROLS'], namespace['INPUT'], namespace['RUNTIME']),
            (controls, controls / 'run-input-v1.json', runtime))
        self.assertEqual(tuple(namespace[k] for k in ('OUTER_SECONDS', 'OWNER_SECONDS', 'PARENT_SECONDS',
            'CONTROLLER_SECONDS', 'CALLER_SECONDS')), (1800, 1700, 1730, 1200, 1230))

    def test_old_sdk_model_extra_or_changed_guest_resources_refuse_before_dispatch(self):
        for fault in ('sdk14', 'model', 'wrong_root', 'cores', 'budget', 'authorization', 'boolean_owner'):
            graph = CoordinatorGraph()
            if fault == 'sdk14': graph.a['protocol'] = 'owned-emulator-record-controls-ui-v1'
            elif fault == 'model': graph.a['artifacts']['model'] = profile.legacy.pin('D:/Synthetic/unselected.task')
            elif fault == 'wrong_root': graph.a['guest']['root'] = 'D:/Synthetic/fresh-not-authorized/avd-v1'
            elif fault == 'cores': graph.proposal['cores'] = 8
            elif fault == 'budget': graph.proposal['max_seconds'] = 1801
            elif fault == 'authorization': graph.auth['allow_environment_calls'] = False
            else: graph.a['seconds'] = True
            with self.subTest(fault=fault), graph.patches():
                with self.assertRaises((activation.ActivationRefused, REAL.contract.TargetRefused, REAL.env.EnvironmentRefused)):
                    activation._validate_metadata(graph.value, graph.a, graph.proposal, graph.auth)
                graph.api.env.supervise.assert_not_called()
                graph.api.owner.LiveOwnedKnowledgeUiTarget.assert_not_called()

    def test_complete_simulated_owner_handoff_joins_the_actual_started_caller_and_same_closed_guest(self):
        graph = CoordinatorGraph()
        with graph.patches(): runtime, code = graph.run()
        self.assertEqual(code, 0); self.assertTrue(runtime.result['passed'])
        self.assertTrue(runtime.result['storage_closed']); self.assertTrue(runtime.result['cleanup_known'])
        self.assertFalse(runtime.result['feature_acceptance'])
        self.assertEqual(graph.a['guest']['root'], str(PureWindowsPath(
            'D:/Dev/Experiments/LocalLore/2026-11-02-knowledge-ui-v1/avd-v1')))
        self.assertEqual(len(graph.verifications), 2)
        self.assertTrue(all(row[3] == graph.caller for row in graph.verifications))
        self.assertEqual(graph.saves.count('stop.pending-v1.json'), 1)
        self.assertEqual(graph.capture.close.call_count, 1); self.assertEqual(graph.observer.close.call_count, 1)

    def test_unknown_caller_terminal_or_missing_start_never_grants_a_stop_or_controller_success(self):
        for fault in ('output', 'cleanup', 'integer', 'deadline', 'missing_start'):
            graph = CoordinatorGraph()
            if fault == 'output': graph.terminal['output_capture_complete'] = False
            elif fault == 'cleanup': graph.terminal['cleanup_complete'] = False
            elif fault == 'integer': graph.terminal['worker_returncode'] = True
            elif fault == 'deadline': graph.terminal['status'] = 'deadline'
            else: graph.register_start = False
            with self.subTest(fault=fault), graph.patches(): runtime, code = graph.run()
            self.assertEqual(code, 1); self.assertFalse(runtime.stop_attempted)
            self.assertFalse(runtime.result['passed']); self.assertEqual(graph.verifications, [])
            self.assertFalse((graph.owned / 'stop-v1.json').exists())
            self.assertEqual(graph.capture.close.call_count, 1)

    def test_changed_started_identity_cannot_be_promoted_by_a_known_zero_exit(self):
        graph = CoordinatorGraph(); original = graph.supervise
        def changed(*args):
            terminal = original(*args)
            path = graph.control / 'controller-started-v1.json'
            value = REAL.env.read_json(path); value['worker']['creation_filetime'] += 1
            path.write_bytes(REAL.env.encoded(value)); return terminal
        graph.api.env.supervise.side_effect = changed
        with graph.patches(): runtime, code = graph.run()
        self.assertEqual(code, 1); self.assertFalse(runtime.result['controller_passed'])
        self.assertEqual(graph.verifications, []); self.assertFalse(runtime.result['passed'])
        self.assertEqual(graph.capture.close.call_count, 1); self.assertEqual(graph.observer.close.call_count, 1)

    def test_started_receipt_is_create_once_and_failed_second_publication_cannot_replace_the_first(self):
        graph = CoordinatorGraph(); path = graph.control / 'isolated-started-v1.json'
        request = REAL.env.binding(graph.control / 'worker-request-v1.json')
        with graph.patches():
            first = activation._started(path, request, SimpleNamespace(pid=graph.caller['pid']), graph.caller['executable'])
            raw = path.read_bytes()
            with self.assertRaises(FileExistsError):
                activation._started(path, request, SimpleNamespace(pid=graph.caller['pid']), graph.caller['executable'])
            self.assertEqual(path.read_bytes(), raw); self.assertEqual(first, graph.caller)
            with self.assertRaises(FileExistsError):
                activation._started(path, request, SimpleNamespace(pid=graph.caller['pid']), graph.caller['executable'])
        self.assertTrue(path.with_name(path.stem + '.pending.json').exists())
        graph.api.env.supervise.assert_not_called()

    def test_failed_stop_second_guard_is_spent_and_cleanup_cannot_retry_or_hide_it(self):
        graph = CoordinatorGraph(); graph.observer.guard.side_effect = [None, None, OSError('synthetic second stop guard')]
        with graph.patches(): runtime, code = graph.run(); runtime.cleanup()
        self.assertEqual(code, 1); self.assertTrue(runtime.stop_attempted); self.assertFalse(runtime.stop_published)
        self.assertFalse(runtime.result['cleanup_known']); self.assertFalse(runtime.result['passed'])
        self.assertEqual(graph.saves.count('stop.pending-v1.json'), 1)
        self.assertTrue((graph.owned / 'stop.pending-v1.json').exists())
        self.assertFalse((graph.owned / 'stop-v1.json').exists())

    def test_old_proposal_digest_or_changed_closure_join_cannot_close_the_current_recovered_handoff(self):
        for fault in ('ledger_digest', 'closure_digest', 'after', 'duplicate_root'):
            graph = CoordinatorGraph()
            if fault in ('ledger_digest', 'duplicate_root'):
                path = graph.registry / 'ledger-v1.json'; value = REAL.env.read_json(path)
                if fault == 'ledger_digest': value['entries'][0]['proposal_sha256'] = '0' * 64
                else: value['entries'].append(copy.deepcopy(value['entries'][0]))
                path.write_bytes(REAL.env.encoded(value))
            else:
                value = copy.deepcopy(graph.closure)
                if fault == 'closure_digest': value['proposal_sha256'] = '0' * 64
                else: value['after'] = graph.worker_pin
                path = Path(graph.closure_pin['path']); path.write_bytes(REAL.env.encoded(value))
                graph.closure_pin = REAL.env.binding(path)
            with self.subTest(fault=fault), graph.patches(): runtime, code = graph.run()
            self.assertEqual(code, 1); self.assertFalse(runtime.result['passed']); self.assertFalse(runtime.result['storage_closed'])
            self.assertTrue(runtime.stop_published); self.assertEqual(graph.saves.count('stop.pending-v1.json'), 1)

    def test_each_independent_cleanup_tail_runs_but_any_unknown_tail_keeps_qualification_false(self):
        for fault in ('poll', 'observer', 'capture', 'capture_binding', 'original-owner-terminal-v1.json'):
            graph = CoordinatorGraph()
            if fault == 'observer': graph.observer.close.side_effect = OSError('synthetic observer close')
            elif fault == 'capture': graph.capture.close.side_effect = OSError('synthetic capture close')
            else: graph.faults.add(fault)
            with self.subTest(fault=fault), graph.patches(): runtime, code = graph.run()
            self.assertEqual(code, 1); self.assertFalse(runtime.result['passed']); self.assertFalse(runtime.result['cleanup_known'])
            self.assertEqual(graph.capture.close.call_count, 1)
            self.assertIn('original-owner-terminal-v1.json', graph.saves); self.assertIn('runtime-result-v1.json', graph.saves)


    def test_old_sdk15_input_scope_profile_or_source_closure_never_dispatches(self):
        for fault in ('input_scope', 'profile_protocol', 'source_closure', 'boolean_input_version'):
            graph = CoordinatorGraph()
            if fault == 'input_scope': graph.value['scope'] = 'library-ui-run-input-v1'
            elif fault == 'profile_protocol': graph.a['protocol'] = 'owned-emulator-library-ui-v1'
            elif fault == 'source_closure':
                graph.a['sources'] = [pin for pin in graph.a['sources']
                    if PureWindowsPath(pin['path']).name != 'knowledge_ui_profile_build.py']
            else: graph.value['version'] = True
            with self.subTest(fault=fault), graph.patches():
                with self.assertRaises((activation.ActivationRefused, REAL.contract.TargetRefused)):
                    activation._validate_metadata(graph.value, graph.a, graph.proposal, graph.auth)
                graph.api.env.supervise.assert_not_called()
                graph.api.owner.LiveOwnedKnowledgeUiTarget.assert_not_called()
                graph.api.process.ServerCapture.assert_not_called()

    def test_early_caller_cancellation_has_no_stop_authority_but_still_closes_both_owned_observers(self):
        graph = CoordinatorGraph(); original = graph.supervise
        ledger = (graph.registry/'ledger-v1.json').read_bytes()
        def cancelled(*args):
            original(*args)
            raise KeyboardInterrupt('synthetic caller cancellation after started receipt')
        graph.api.env.supervise.side_effect = cancelled
        with graph.patches(): runtime, code = graph.run()
        self.assertEqual(code, 1); self.assertIsNotNone(runtime.caller)
        self.assertFalse(runtime.stop_attempted); self.assertFalse(runtime.stop_published)
        self.assertFalse(runtime.result['passed']); self.assertFalse(runtime.result['storage_closed'])
        self.assertFalse(runtime.result['feature_acceptance'])
        self.assertEqual(graph.capture.close.call_count, 1); self.assertEqual(graph.observer.close.call_count, 1)
        self.assertEqual((graph.registry/'ledger-v1.json').read_bytes(), ledger)
        self.assertNotIn('stop.pending-v1.json', graph.saves)
        # This graph has a simulated already-closed ledger; unchanged bytes are
        # not evidence of a real reservation transition or measured retention.

    def test_integer_or_missing_cleanup_receipts_cannot_qualify_known_caller_success(self):
        for fault in ('observer_integer', 'capture_integer', 'cleanup_integer', 'cleanup_missing'):
            graph = CoordinatorGraph()
            if fault == 'observer_integer': graph.observer.close.return_value = 1
            elif fault == 'capture_integer': graph.capture.close.return_value = 1
            else:
                key = sorted(REAL.contract.CLEANUP_KEYS)[0]
                if fault == 'cleanup_integer': graph.cleanup_record['cleanup'][key] = 1
                else: del graph.cleanup_record['cleanup'][key]
            with self.subTest(fault=fault), graph.patches(): runtime, code = graph.run()
            self.assertEqual(code, 1); self.assertTrue(runtime.stop_published)
            self.assertFalse(runtime.result['passed']); self.assertFalse(runtime.result['storage_closed'])
            self.assertFalse(runtime.result['feature_acceptance'])
            self.assertEqual(graph.capture.close.call_count, 1); self.assertEqual(graph.observer.close.call_count, 1)
            self.assertEqual(graph.saves.count('stop.pending-v1.json'), 1)


if __name__ == '__main__': unittest.main()
