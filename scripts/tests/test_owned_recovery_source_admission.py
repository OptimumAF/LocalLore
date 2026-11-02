"""Original current-source admission attacks; no guest, ledger, SDK or socket IO.

Only non-source inputs and product verification are simulated. Current source
bindings and shared source revalidation remain real at each dispatch boundary.
Copyright 2026 LocalLore contributors. SPDX-License-Identifier: Apache-2.0
"""
import copy
from contextlib import redirect_stdout
import importlib
import io
import os
from pathlib import Path, PureWindowsPath
import tempfile
from types import SimpleNamespace
import unittest
from unittest import mock

from benchmarks import adb_held_socket_probe as probe
from benchmarks import android_process_client_v4 as wire
from benchmarks import android_process_record_controls_ui_client as client
from benchmarks import owned_record_controls_ui_contract as contract
from benchmarks import owned_record_controls_ui_owner as owner
from benchmarks import owned_target_contract as core
from benchmarks import owned_target_owner as mechanisms
from benchmarks import receipt_avd_environment as env
from benchmarks import record_controls_ui_activation as activation
from benchmarks import record_controls_ui_build as build
from benchmarks import record_controls_ui_controller as controller
from scripts.tests import test_owned_target_contract as legacy
from scripts.tests import test_record_controls_ui_profile as data

DEPENDENCY = 'prepare_recovery_contract.py'
ROOT = Path(__file__).resolve().parents[2]
PROFILES = ('owned_target_contract', 'owned_restart_contract', 'owned_live_death_contract',
    'owned_ui_contract', 'owned_record_ui_contract', 'owned_presentation_process_contract',
    'owned_player_presentation_ui_contract', 'owned_transcript_ui_contract',
    'owned_chat_ui_contract', 'owned_inventory_ui_contract', 'owned_profile_ui_contract',
    'owned_record_controls_ui_contract')


@unittest.skipUnless(os.name == 'nt', 'Physical D source bindings, synthetic dispatch only')
class RecoveredOwnerSourceAdmissionTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix='locallore-source-admission-', dir='D:/Dev/_Temp')
        self.addCleanup(self.temp.cleanup)
        self.directory = Path(self.temp.name).resolve()
        self.patch(core.base, 'revalidate_inputs')
        self.patch(env, 'check_binding')  # All non-source artifact pins are synthetic.
        self.python = self.patch(probe, '_python_bindings', return_value=data.admission()['python'])
        artifacts = data.admission()['artifacts']
        manifest = dict(roster=[list(row) for row in contract.INSTRUMENTATIONS],
            apks={role: dict(binding=artifacts[role], package=package, certificate_sha256='a' * 64)
                  for role, package in (('product_apk', contract.APP), ('test_apk', contract.TEST))})
        self.product = self.patch(build, 'verify_frozen_product', return_value=manifest)
        self.socket = self.patch(wire.socket, 'socket', side_effect=AssertionError('No socket admission'))
        self.process = self.patch(mechanisms.subprocess, 'Popen', side_effect=AssertionError('No process admission'))

    def patch(self, target, name, value=mock.DEFAULT, **kwargs):
        change = mock.patch.object(target, name, value, **kwargs)
        answer = change.start(); self.addCleanup(change.stop); return answer

    def admission(self, *, current=False, init=False):
        answer = data.admission()
        names = set(contract.SOURCE_NAMES) | ({DEPENDENCY} if current else set())
        if init: names.add('__init__.py')
        pins = []
        for name in names:
            path = ROOT / 'benchmarks' / name
            pins.append(env.binding(path) if path.is_file() else legacy.pin(path))
        answer['sources'] = sorted(pins, key=lambda pin: pin['path'])
        by_name = {PureWindowsPath(pin['path']).name: pin for pin in answer['sources']}
        server_names = set(core.base.SOURCE_NAMES) | ({'__init__.py'} if init else set())
        answer['server']['sources'] = sorted([copy.deepcopy(by_name[name]) for name in server_names], key=lambda pin: pin['path'])
        answer['guest']['refuser_source'] = env.binding(ROOT / 'benchmarks/native/deny_adb_client.c')
        return answer

    def stale_variants(self):
        old = self.admission()
        changed = self.admission(current=True)
        next(pin for pin in changed['sources'] if PureWindowsPath(pin['path']).name == DEPENDENCY)['sha256'] = 'f' * 64
        return (old, changed)

    def require_refused(self, call):
        with self.assertRaises(core.TargetRefused): call()

    def check_accepts(self, call):
        try: return call()
        except core.TargetRefused as error: self.fail('Valid closed current source metadata refused: ' + str(error))

    def test_every_current_profile_emits_the_new_shared_storage_dependency(self):
        for name in PROFILES:
            with self.subTest(profile=name):
                module = importlib.import_module('benchmarks.' + name)
                actual = module.source_bindings()
                names = {PureWindowsPath(pin['path']).name for pin in actual}
                self.assertEqual(names, set(module.SOURCE_NAMES) | {DEPENDENCY} |
                    ({'__init__.py'} if (ROOT / 'benchmarks/__init__.py').exists() else set()))
                self.assertEqual(next(pin for pin in actual if PureWindowsPath(pin['path']).name == DEPENDENCY),
                    env.binding(ROOT / 'benchmarks' / DEPENDENCY))

    def test_legacy_twenty_four_source_metadata_remains_structurally_readable(self):
        value = self.admission(); frozen = copy.deepcopy(value)
        self.assertEqual(len(contract.SOURCE_NAMES), 24)
        self.assertEqual(contract.validate_admission(value), frozen)
        self.assertEqual(value, frozen)

    def test_exact_current_twenty_five_source_metadata_is_accepted_without_expanding_profile(self):
        value = self.admission(current=True); frozen = copy.deepcopy(value)
        self.assertEqual(len(value['sources']), 25)
        self.assertEqual(self.check_accepts(lambda: contract.validate_admission(value)), frozen)
        self.assertNotIn(DEPENDENCY, contract.SOURCE_NAMES)
        self.assertEqual(value, frozen)

    def test_optional_init_is_accepted_for_both_closed_sets_with_matching_embedded_server(self):
        for current in (False, True):
            with self.subTest(current=current):
                value = self.admission(current=current, init=True)
                self.assertEqual(self.check_accepts(lambda: contract.validate_admission(value)), value)

    def test_dependency_does_not_allow_arbitrary_extras_missing_members_or_mixed_parents(self):
        for mode in ('extra', 'missing', 'replacement', 'mixed_parent', 'duplicate', 'unsorted'):
            value = self.admission(current=True)
            if mode == 'extra': value['sources'].append(legacy.pin(ROOT / 'benchmarks/arbitrary.py'))
            elif mode == 'missing': value['sources'] = [p for p in value['sources'] if PureWindowsPath(p['path']).name != 'receipt_avd_storage.py']
            elif mode == 'replacement':
                next(p for p in value['sources'] if PureWindowsPath(p['path']).name == DEPENDENCY)['path'] = str(ROOT / 'benchmarks/arbitrary.py')
            elif mode == 'mixed_parent':
                next(p for p in value['sources'] if PureWindowsPath(p['path']).name == DEPENDENCY)['path'] = 'D:/Foreign/benchmarks/' + DEPENDENCY
            elif mode == 'duplicate': value['sources'].append(copy.deepcopy(value['sources'][0]))
            if mode == 'unsorted': value['sources'].reverse()
            else: value['sources'].sort(key=lambda pin: pin['path'])
            with self.subTest(mode=mode): self.require_refused(lambda: contract.validate_admission(value))

    def test_legacy_structure_cannot_be_revalidated_as_current_dispatch_authority(self):
        self.require_refused(lambda: contract.revalidate_inputs(self.admission()))

    def test_current_hash_and_length_must_both_match_the_real_new_dependency(self):
        for field, wrong in (('sha256', '0' * 64), ('bytes', 1)):
            value = self.admission(current=True)
            next(pin for pin in value['sources'] if PureWindowsPath(pin['path']).name == DEPENDENCY)[field] = wrong
            with self.subTest(field=field): self.require_refused(lambda: contract.revalidate_inputs(value))

    def test_exact_current_sources_revalidate_without_product_or_runtime_operations(self):
        value = self.admission(current=True)
        self.assertIsNone(self.check_accepts(lambda: contract.revalidate_inputs(value)))
        self.product.assert_not_called(); self.socket.assert_not_called(); self.process.assert_not_called()

    def test_owner_public_main_refuses_before_parent_dispatch_and_product_verification(self):
        parent = self.patch(mechanisms, '_parent', return_value=0)
        for value in self.stale_variants():
            path = self.directory / ('admission-' + str(len(list(self.directory.iterdir()))) + '.json')
            env.create_json(path, value); pin = env.binding(path)
            with redirect_stdout(io.StringIO()):
                self.assertEqual(owner.main(['--admission', pin['path'], '--admission-sha256', pin['sha256']]), 1)
            parent.assert_not_called(); self.product.assert_not_called()

    def test_live_target_constructor_refuses_before_native_observer_initialization(self):
        native = self.patch(mechanisms._LiveOwnedTarget, '__init__', return_value=None)
        for value in self.stale_variants():
            with mock.patch.object(mechanisms, '_read_json', return_value=value):
                self.require_refused(lambda: owner.LiveOwnedRecordControlsUiTarget(legacy.pin('D:/Synthetic/admission.json'),
                    legacy.pin('D:/Synthetic/running.json')))
            native.assert_not_called(); self.product.assert_not_called()

    def test_worker_runtime_constructor_refuses_before_native_owner_state(self):
        native = self.patch(mechanisms._TargetRuntimeCore, '__init__', return_value=None)
        for value in self.stale_variants():
            self.require_refused(lambda: owner._RecordControlsUiTargetRuntime(
                {'validated_admission': value}, legacy.pin('D:/Synthetic/request.json'), self.directory))
            native.assert_not_called(); self.product.assert_not_called()

    def test_public_worker_framing_reaches_source_gate_before_runtime_dispatch(self):
        run = self.patch(mechanisms, '_run_worker', return_value=0)
        self.patch(mechanisms.output_control, '_prepare_environment')
        for value in self.stale_variants():
            admission_pin = legacy.pin('D:/Synthetic/admission-v1.json')
            request_pin = legacy.pin(PureWindowsPath(value['root']) / 'request-v1.json')
            request = dict(version=1, protocol=contract.PROTOCOL, admission=admission_pin,
                validated_admission=value, owner=data.running(value)['owner'], sources=value['sources'],
                python=value['python'], worker_script=env.binding(ROOT / 'benchmarks' / contract.OWNER_SCRIPT),
                owner_seconds=value['seconds'] + 30)
            framed = mechanisms.BARRIER + env.encoded({'request': request_pin})
            def read(pin, **_): return request if pin == request_pin else value
            with mock.patch.object(mechanisms, '_read_json', side_effect=read), \
                 mock.patch.object(mechanisms.sys, 'stdin', SimpleNamespace(buffer=io.BytesIO(framed))), \
                 redirect_stdout(io.StringIO()):
                self.assertEqual(owner.main(['_worker']), 1)
            run.assert_not_called()

    def test_controller_inputs_refuse_before_build_or_controller_lease(self):
        lease = self.patch(controller, 'LiveOwnedRecordControlsUiTarget')
        for value in self.stale_variants():
            running = data.running(value)
            admission_pin = running['admission']; running_pin = legacy.pin('D:/Synthetic/running-v1.json')
            with mock.patch.object(controller, '_json', side_effect=lambda pin: value if pin == admission_pin else running):
                self.require_refused(lambda: controller._inputs(admission_pin, running_pin))
            lease.assert_not_called(); self.product.assert_not_called()

    def test_client_lease_source_guard_refuses_before_output_directories_or_socket(self):
        output = self.patch(wire.output_control, 'validate_output', side_effect=AssertionError('No client output'))
        for value in self.stale_variants():
            lease = object.__new__(owner.LiveOwnedRecordControlsUiTarget)
            lease._admission = value; lease._descriptor = data.running(value)
            lease._admission_binding = lease._descriptor['admission']
            lease._running_binding = legacy.pin(PureWindowsPath(value['root']) / 'running-v1.json')
            lease._caller = lease._descriptor['worker']
            # Native/clock observation is synthetic; source authorization stays real.
            with mock.patch.object(owner.LiveOwnedRecordControlsUiTarget, 'guard',
                    side_effect=lambda **_: contract.revalidate_inputs(value)):
                with self.assertRaises(client.ClientRefused):
                    client.OwnedRecordControlsUiSdkCapture(self.directory / 'clients', 1200, lease)
            output.assert_not_called(); self.socket.assert_not_called()

    def test_activation_inputs_refuse_before_run_authorization_or_prepared_guest_observation(self):
        helper = Path(activation.__file__).resolve()
        self.patch(activation, 'HELPER', helper)
        self.patch(activation, 'INPUT', self.directory / 'input.json')
        runtime = self.directory / 'runtime'
        self.patch(activation, 'RUNTIME', runtime)
        self.patch(activation, '_source')  # Avoid git subprocess; source admission remains below.
        self.patch(activation, '_api', return_value=SimpleNamespace(env=env, contract=contract, build=build))
        authorize = self.patch(env, 'authorize')
        prepared = self.patch(env, 'verify_prepared')
        for value in self.stale_variants():
            value['root'] = str(runtime / 'owned-v1'); value['server']['root'] = str(runtime / 'owned-v1/server')
            value['seconds'] = value['server']['seconds'] = activation.OWNER_SECONDS
            admission_pin = legacy.pin(runtime / 'admission-v1.json')
            input_pin = legacy.pin(activation.INPUT)
            source = dict(version=1, scope='record-controls-ui-run-input-v1', admission=admission_pin, helper=env.binding(helper))
            proposal = dict(phase='run', paths={'root': value['guest']['root']}, memory_mib=8192, cores=4, max_seconds=1800)
            authorize.return_value = proposal
            auth = dict(version=1, phase='run', proposal_sha256=value['guest']['proposal']['sha256'],
                allow_environment_calls=True, root_go_pending=False)
            def bound(pin, *_):
                if pin == input_pin: return source
                if pin == admission_pin: return value
                if pin == value['guest']['proposal']: return proposal
                if pin == value['guest']['authorization']: return auth
                raise AssertionError('Unexpected synthetic input read')
            with mock.patch.object(activation, '_bound', side_effect=bound):
                self.require_refused(lambda: activation._inputs(input_pin, fresh=True))
            authorize.assert_not_called(); prepared.assert_not_called(); self.product.assert_not_called()


if __name__ == '__main__':
    unittest.main()
