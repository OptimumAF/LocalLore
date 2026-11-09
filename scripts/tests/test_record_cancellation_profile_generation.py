"""Original phase-one frozen-profile role tests; synthetic metadata, never consent."""
import builtins
import copy
import hashlib
from pathlib import Path
import sys
from types import SimpleNamespace
import unittest
from unittest.mock import Mock, call, patch

from benchmarks import record_cancellation_ui_activation as activation
from benchmarks import owned_record_cancellation_ui_contract as contract

OUT = Path('D:/Dev/Experiments/LocalLore/2026-11-03-record-refusal-freeze-v1')
FROZEN = OUT / 'frozen-profile-source-v1'
CONTROLS = OUT / 'run-controls-v1'
HELPER = FROZEN / 'benchmarks/record_cancellation_ui_activation.py'
RUNTIME = Path('D:/Dev/Experiments/LocalLore/2026-11-03-record-refusal-ui-runtime-v1')
OLD_PROFILE = Path('D:/Dev/Experiments/LocalLore/2026-11-03-record-cancellation-profile-v1/candidate-source-v1')
OLD_FRESH = Path('D:/Dev/Experiments/LocalLore/2026-11-03-record-cancellation-fresh-v1/candidate-source-v1')
OLD_READINESS = Path('D:/Dev/Experiments/LocalLore/2026-11-03-record-cancellation-readiness-v1/candidate-source-v1')



def pin(path):
    text = str(path)
    return dict(path=text, bytes=1, sha256=hashlib.sha256(('STRUCTURAL ' + text).encode()).hexdigest())


def source_ports():
    pins = [pin(FROZEN / 'benchmarks' / name) for name in sorted(contract.SOURCE_NAMES)]
    return SimpleNamespace(env=SimpleNamespace(safe_path=Mock(), check_binding=Mock()),
        contract=SimpleNamespace(source_bindings=Mock(return_value=copy.deepcopy(pins))),
        build=SimpleNamespace(revalidate_checker=Mock())), pins


class RecordCancellationProfileGenerationTests(unittest.TestCase):
    def test_frozen_profile_and_controls_are_separate_fixed_roles_not_a_new_sdk(self):
        self.assertEqual(activation.SOURCE_ROOT, FROZEN)
        self.assertEqual(activation.HELPER, HELPER)
        self.assertEqual(activation.CONTROLS, CONTROLS)
        self.assertEqual(activation.INPUT, CONTROLS / 'run-input-v1.json')
        self.assertEqual(activation.RUNTIME, RUNTIME)
        self.assertNotEqual(activation.SOURCE_ROOT, OUT / 'candidate-source-v1')
        self.assertEqual((activation.OUTER_SECONDS, activation.OWNER_SECONDS, activation.PARENT_SECONDS), (1800, 1700, 1730))
        self.assertEqual((contract.PROTOCOL, contract.SDK_PROTOCOL, contract.PROOF_PROTOCOL, contract.CLIENT_VERSION),
            ('owned-emulator-record-cancellation-ui-v1', 'sdk-record-cancellation-ui-v1', 'record-cancellation-ui-socket-proof-v1', 18))
        self.assertEqual(str(contract.GUEST_ROOT).replace('\\', '/'), 'D:/Dev/Experiments/LocalLore/2026-11-03-record-refusal-ui-v1/avd-v1')
        self.assertEqual([row[0] for row in contract.INSTRUMENTATIONS], ['record_cancel_1', 'record_cancel_2', 'record_cancel_3', 'record_cancel_4', 'record_cancel_5'])
        self.assertEqual({row[1] for row in contract.INSTRUMENTATIONS}, {'org.locallore.app.StoryRecordCancellationScreenTest'})
        self.assertEqual(tuple(row[2] for row in contract.INSTRUMENTATIONS), (
            'cancelledCurrentPageShowsSafeRetryAndReusesTheExactFrozenCursor',
            'cancelledScopedDetailRendersSafeProblemAndRetriesTheSamePlayerLens',
            'obsoletePageCancellationCannotReplaceSectionSelectionOrClosedAndReopenedRecords',
            'oldDetailCancellationAfterBackCannotFinishTheReplacementDetail',
            'disposedOwnerAndRemountedScreenCannotBorrowOldReadsOrRetainedCallbacks'))
        self.assertIs(contract.MODEL_MATERIAL, False)

    def test_source_observation_uses_frozen_closure_and_refuses_old_executing_file(self):
        api, pins = source_ports()
        self.assertEqual(len(pins), 28)
        with patch.object(activation, '_api', return_value=api), \
             patch.object(activation, '__file__', str(HELPER)), \
             patch.object(Path, 'resolve', lambda path, **kwargs: path):
            activation._source()
        api.env.safe_path.assert_called_once_with(FROZEN, exists=True, directory=True)
        self.assertEqual(api.env.check_binding.call_args_list, [call(row) for row in pins])
        self.assertEqual(api.build.revalidate_checker.call_count, 1)
        for old in (OLD_PROFILE, OLD_FRESH, OLD_READINESS):
            api, _ = source_ports()
            with self.subTest(old=str(old)), patch.object(activation, '_api', return_value=api), \
                 patch.object(activation, '__file__', str(old / 'benchmarks/record_cancellation_ui_activation.py')), \
                 patch.object(Path, 'resolve', lambda path, **kwargs: path):
                with self.assertRaises(activation.ActivationRefused): activation._source()
            self.assertEqual(api.contract.source_bindings.call_count, 0)
            self.assertEqual(api.env.check_binding.call_count, 0)
            self.assertEqual(api.build.revalidate_checker.call_count, 0)

    def test_cold_api_import_ports_bind_only_frozen_module_origins(self):
        names = ('receipt_avd_environment', 'owned_record_cancellation_ui_contract',
            'owned_record_cancellation_ui_owner', 'owned_target_owner', 'isolated_adb_owner',
            'record_cancellation_ui_profile_build', 'record_cancellation_ui_controller',
            'android_process_record_cancellation_ui_verification')
        original_import = builtins.__import__
        for foreign in (None, 'record_cancellation_ui_profile_build'):
            attempted = Mock(side_effect=AssertionError('unexpected operation'))
            modules = {name: SimpleNamespace(__file__=str(FROZEN / 'benchmarks' / (name + '.py')),
                prepare=attempted, execute=attempted) for name in names}
            if foreign: modules[foreign].__file__ = str(OLD_PROFILE / 'benchmarks' / (foreign + '.py'))
            imports = []
            def importer(name, globals=None, locals=None, fromlist=(), level=0):
                if name == 'benchmarks' and fromlist:
                    self.assertTrue(set(fromlist) <= set(names))
                    imports.extend(fromlist)
                    return SimpleNamespace(**modules)
                return original_import(name, globals, locals, fromlist, level)
            before_path = list(sys.path)
            try:
                with self.subTest(foreign=foreign), patch.object(activation, '_MODULES', None), \
                     patch.object(builtins, '__import__', side_effect=importer), \
                     patch.object(Path, 'resolve', lambda path, **kwargs: path):
                    if foreign:
                        with self.assertRaises(activation.ActivationRefused): activation._api()
                    else:
                        api = activation._api()
                        self.assertIs(api.env, modules['receipt_avd_environment'])
                        self.assertIs(api.build, modules['record_cancellation_ui_profile_build'])
            finally:
                sys.path[:] = before_path
            self.assertEqual(imports, list(names))
            self.assertEqual(attempted.call_count, 0)

    def test_old_control_slots_refuse_before_payload_reads_and_missing_current_input_grants_nothing(self):
        api = SimpleNamespace()
        missing = activation.ActivationRefused('synthetic_missing_input')
        source = Mock(side_effect=AssertionError('source after missing input'))
        publish = Mock(side_effect=AssertionError('unexpected publication'))
        with patch.object(activation, '_api', return_value=api), patch.object(activation, '__file__', str(HELPER)), \
             patch.object(activation, '_source', source), patch.object(activation, '_save', publish):
            current = Mock(side_effect=missing)
            with patch.object(activation, '_bound', current):
                with self.assertRaises(activation.ActivationRefused): activation._inputs(pin(CONTROLS / 'run-input-v1.json'))
            self.assertEqual(current.call_count, 1)
            for old_controls in (OLD_PROFILE.parent / 'run-controls-v1', OLD_FRESH.parent / 'run-controls-v1', OLD_READINESS.parent / 'run-controls-v1'):
                observed = Mock(side_effect=missing)
                with self.subTest(old=str(old_controls)), patch.object(activation, '_bound', observed):
                    with self.assertRaises(activation.ActivationRefused): activation._inputs(pin(old_controls / 'run-input-v1.json'))
                self.assertEqual(observed.call_count, 0)
        self.assertEqual(source.call_count, 0)
        self.assertEqual(publish.call_count, 0)
