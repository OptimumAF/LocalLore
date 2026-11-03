"""SDK17 activation data/qualification oracles with explicit observation ports.

All owner, storage, controller and binding observations here are fake metadata.
No actual prepare/run authorization, admission, guest, ledger or process exists.
"""
import copy
from pathlib import Path
from types import SimpleNamespace
import unittest
from unittest.mock import Mock, patch

from benchmarks import diagnostic_ui_activation as activation
from benchmarks import owned_diagnostic_ui_contract as c
from benchmarks import receipt_avd_environment as env
from scripts.tests import test_diagnostic_ui_profile_fixtures as f


def input_value():
    return dict(version=1, scope='diagnostic-ui-run-input-v1',
        admission=f.legacy.pin(activation.RUNTIME / 'admission-v1.json'), helper=f.legacy.pin(activation.HELPER))


def admitted():
    a = f.admission()
    a['root'] = str(activation.RUNTIME / 'owned-v1')
    a['server']['root'] = str(Path(a['root']) / 'server')
    a['seconds'] = a['server']['seconds'] = 1700
    return a


def qualification():
    """Positive graph through actual qualify, with every external port explicit."""
    runtime = object.__new__(activation._Runtime)
    runtime.admission = a = admitted()
    runtime.value = value = input_value()
    runtime.request = dict(input=f.legacy.pin(activation.INPUT))
    runtime.original_owner = dict(pid=21, created_filetime=9000)
    runtime.running = f.legacy.pin('D:/Synthetic/running-v1.json')
    runtime.caller = dict(pid=22, created_filetime=9001)
    runtime.controller_result = f.legacy.pin('D:/Synthetic/controller-result-v1.json')
    runtime.stop_published = True
    runtime.result = dict(passed=False, cleanup_known=True, owner_wait_known=True,
        original_owner_returncode=0, capture_complete=True, capture_evidence_known=True,
        owner_terminal_published=True, controller_passed=True, observer_closed=True)
    owner_request = f.legacy.pin('D:/Synthetic/owner-request-v1.json')
    worker_result = f.legacy.pin('D:/Synthetic/worker-result-v1.json')
    started = f.legacy.pin('D:/Synthetic/started-v1.json')
    owner_result = f.legacy.pin('D:/Synthetic/owner-result-v1.json')
    after = f.legacy.pin('D:/Synthetic/after-v1.json')
    closure_path = Path(a['guest']['root']) / 'guest-storage-closure-v1.json'
    closure_pin = f.legacy.pin(closure_path)
    registry = Path('D:/Synthetic/metadata-only-registry')
    ledger_pin = f.legacy.pin(registry / 'ledger-v1.json')
    public = dict(qualified_target=True, reason='stop_requested', admission=value['admission'],
        request=owner_request, worker_result=worker_result, started=started, owner=owner_result, after=after)
    closure = dict(closure_verified=True, cleanup_complete=True, admission=value['admission'],
        worker_result=worker_result, owner_result=owner_result, after=after,
        proposal_sha256=a['guest']['proposal']['sha256'])
    bound = {
        str(Path(a['root']) / 'result-v1.json'): public,
        owner_request['path']: dict(owner=runtime.original_owner),
        started['path']: dict(worker=dict(pid=23, created_filetime=9002)),
        str(closure_path): closure,
        str(registry / 'ledger-v1.json'): dict(entries=[dict(root=a['guest']['root'], state='closed',
            closure=closure_pin, proposal_sha256=a['guest']['proposal']['sha256'])]),
    }
    verify = Mock(return_value=dict(reason='stop_requested', cleanup={key: True for key in c.CLEANUP_KEYS}))
    replay = Mock(return_value=dict(outcome='completed'))
    check = Mock()
    api = SimpleNamespace(contract=c,
        env=SimpleNamespace(binding=f.legacy.pin, encoded=env.encoded, check_binding=check,
                            guest_storage=SimpleNamespace(DEFAULT_REGISTRY=registry)),
        verification=SimpleNamespace(verify_owned_target_result=verify),
        controller=SimpleNamespace(verify_controller_result=replay))
    return runtime, api, bound, verify, replay, check


class DiagnosticUiActivationTests(unittest.TestCase):
    def test_input_is_closed_to_its_own_scope_paths_and_concrete_version(self):
        api = SimpleNamespace(contract=c)
        value = input_value()
        with patch.object(activation, '_api', return_value=api):
            activation._validate_input(value)
            for mutation in ('version', 'scope', 'admission', 'helper', 'extra'):
                with self.subTest(mutation=mutation):
                    bad = copy.deepcopy(value)
                    if mutation == 'version': bad['version'] = True
                    elif mutation == 'scope': bad['scope'] = 'knowledge-ui-run-input-v1'
                    elif mutation == 'admission': bad['admission']['path'] = str(activation.CONTROLS / 'admission-v1.json')
                    elif mutation == 'helper': bad['helper']['path'] = str(activation.HELPER.with_name('knowledge_ui_activation.py'))
                    else: bad['implementation'] = 'caller-selected'
                    with self.assertRaises(activation.ActivationRefused): activation._validate_input(bad)

    def test_run_metadata_requires_exact_current_8192_four_core_1800_profile(self):
        check = Mock()
        api = SimpleNamespace(contract=c, env=SimpleNamespace(check_authorization=check))
        value, a = input_value(), admitted()
        proposal = dict(phase='run', paths=dict(root=a['guest']['root']), memory_mib=8192, cores=4, max_seconds=1800)
        authorization = dict(synthetic=True)
        with patch.object(activation, '_api', return_value=api):
            self.assertEqual(activation._validate_metadata(value, a, proposal, authorization), a)
            check.assert_called_once_with(authorization, 'run', a['guest']['proposal']['sha256'])
            for key, wrong in (('phase', 'prepare'), ('memory_mib', 4096), ('cores', True), ('max_seconds', 1800.0)):
                with self.subTest(key=key):
                    bad = copy.deepcopy(proposal); bad[key] = wrong
                    with self.assertRaises(activation.ActivationRefused): activation._validate_metadata(value, a, bad, authorization)
        self.assertEqual(check.call_count, 1)

    def test_known_terminal_is_cleanup_knowledge_not_success_or_boolean_returncode(self):
        positive = dict(status='child_exited', worker_returncode=1, cleanup_complete=True, output_capture_complete=True)
        self.assertTrue(activation._known_terminal(positive))
        for key, wrong in (('status', 'running'), ('worker_returncode', False), ('cleanup_complete', 1), ('output_capture_complete', False)):
            with self.subTest(key=key):
                bad = copy.deepcopy(positive); bad[key] = wrong
                self.assertFalse(activation._known_terminal(bad))

    def test_controller_worker_routes_only_bound_admission_and_current_running_receipt(self):
        request = dict(input=f.legacy.pin(activation.INPUT), running=f.legacy.pin('D:/Synthetic/running.json'))
        value = input_value()
        run = Mock(return_value=dict(outcome='completed'))
        api = SimpleNamespace(controller=SimpleNamespace(run=run))
        with patch.object(activation, '_enter', return_value=(request, None)) as enter, \
             patch.object(activation, '_inputs', return_value=(value, admitted())) as inputs, \
             patch.object(activation, '_api', return_value=api):
            self.assertEqual(activation._controller_worker(), 0)
            enter.assert_called_once_with('controller')
            inputs.assert_called_once_with(request['input'])
            run.assert_called_once_with(value['admission'], request['running'])
            run.return_value = dict(outcome='refused')
            self.assertEqual(activation._controller_worker(), 1)
            request['running'] = None
            with self.assertRaises(activation.ActivationRefused): activation._controller_worker()
        self.assertEqual(run.call_count, 2)

    def test_positive_file_only_qualification_joins_closed_owner_controller_and_storage(self):
        runtime, api, bound, verify, replay, check = qualification()
        before = copy.deepcopy(bound)
        with patch.object(activation, '_api', return_value=api), \
             patch.object(activation, '_bound', side_effect=lambda pin, *a: copy.deepcopy(bound[pin['path']])), \
             patch.object(activation, '_inputs', return_value=None):
            runtime.qualify()
        self.assertIs(runtime.result['passed'], True)
        self.assertEqual(bound, before)
        self.assertIs(runtime.result['owner_qualified'], True)
        self.assertIs(runtime.result['storage_closed'], True)
        self.assertEqual(verify.call_count, 1)
        replay.assert_called_once_with(runtime.controller_result, runtime.value['admission'], runtime.running, runtime.caller)
        self.assertEqual(check.call_count, 2)

    def test_unknown_owner_cleanup_or_boolean_observation_never_qualifies(self):
        mutations = [(key, False) for key in ('cleanup_known', 'owner_wait_known', 'capture_complete',
            'capture_evidence_known', 'owner_terminal_published')]
        mutations += [('cleanup_known', 1), ('original_owner_returncode', False), ('original_owner_returncode', 1)]
        for key, value in mutations:
            with self.subTest(key=key, value=value):
                runtime, api, _, _, _, _ = qualification()
                runtime.result[key] = value
                with patch.object(activation, '_api', return_value=api), \
                     patch.object(activation, '_bound', side_effect=AssertionError('unknown owner reached public records')):
                    with self.assertRaises(activation.ActivationRefused): runtime.qualify()
                self.assertIs(runtime.result['passed'], False)
        for key in ('controller_passed', 'observer_closed'):
            with self.subTest(final_gate=key):
                runtime, api, bound, _, _, _ = qualification()
                runtime.result[key] = False
                with patch.object(activation, '_api', return_value=api), \
                     patch.object(activation, '_bound', side_effect=lambda pin, *a: copy.deepcopy(bound[pin['path']])), \
                     patch.object(activation, '_inputs', return_value=None): runtime.qualify()
                self.assertIs(runtime.result['passed'], False)
