"""Original SDK15 authority and dispatch adversaries; synthetic metadata is not a device result."""
import copy
from contextlib import ExitStack, redirect_stdout
import io
import os
from pathlib import Path, PureWindowsPath
import unittest
from unittest.mock import patch

from benchmarks import android_process_client_v4 as wire
from benchmarks import android_process_library_ui_client as client
from benchmarks import android_process_library_ui_verification as verification
from benchmarks import library_ui_build as build
from benchmarks import owned_library_ui_contract as contract
from benchmarks import owned_library_ui_owner as owner
from benchmarks import owned_record_controls_ui_contract as sdk14
from benchmarks import owned_target_contract as core
from benchmarks import owned_target_owner as mechanisms
from benchmarks import receipt_avd_storage as storage
from scripts.tests import test_library_ui_controller_fixtures as data
from scripts.tests import test_owned_target_contract as legacy

PROTOCOL = 'owned-emulator-library-ui-v1'
SDK_PROTOCOL = 'sdk-library-ui-v1'
PROOF_PROTOCOL = 'library-ui-socket-proof-v1'


class LibraryUiAuthorityTests(unittest.TestCase):
    def test_literal_four_method_authority_is_distinct_from_nineteen_method_sdk14(self):
        self.assertEqual((contract.PROTOCOL, contract.SDK_PROTOCOL, contract.PROOF_PROTOCOL),
            (PROTOCOL, SDK_PROTOCOL, PROOF_PROTOCOL))
        self.assertEqual((contract.CLIENT_VERSION, contract.SESSION_FILE, contract.OWNER_SCRIPT, contract.BOOT_CLAIM_FILE),
            (15, 'sdk-session-v15.json', 'owned_library_ui_owner.py', 'owned-library-ui-boot-claim-v1.json'))
        self.assertEqual(contract.INSTRUMENTATIONS, data.SELECTORS)
        self.assertEqual(contract.CLAIM_KINDS, tuple(row[0] for row in data.SELECTORS))
        self.assertEqual(len(contract.INSTRUMENTATIONS), 4)
        self.assertEqual(contract.GUEST_ROOT, sdk14.GUEST_ROOT)
        self.assertEqual(str(contract.GUEST_ROOT), str(PureWindowsPath(
            'D:/Dev/Experiments/LocalLore/2026-11-01-record-controls-ui-v1/avd-v1')))
        self.assertEqual((contract.APP, contract.TEST, contract.MODEL_MATERIAL), ('org.locallore.app', 'org.locallore.app.test', False))
        self.assertEqual(contract.ARTIFACT_KEYS, {'build', 'product_apk', 'test_apk'})
        self.assertEqual(len(sdk14.INSTRUMENTATIONS), 19)

    def test_imported_definitions_cannot_observe_allocate_publish_or_launch(self):
        root = Path(__file__).resolve().parents[2] / 'benchmarks'
        names = ('owned_library_ui_contract.py', 'owned_library_ui_owner.py',
            'android_process_library_ui_client.py', 'android_process_library_ui_verification.py', 'library_ui_controller.py')
        sources = {name: (root / name).read_bytes() for name in names}
        with ExitStack() as stack:
            for target, name in ((Path, 'open'), (Path, 'stat'), (Path, 'mkdir'), (wire.socket, 'socket'),
                (mechanisms.subprocess, 'Popen'), (wire.environment, 'create_json'),
                (storage, 'reserve_prepare'), (storage, 'record_state'), (storage, 'record_closed')):
                stack.enter_context(patch.object(target, name, side_effect=AssertionError('Import performed host work')))
            for name, raw in sources.items():
                exec(compile(raw, str(root / name), 'exec'), {'__name__': 'benchmarks._sdk15_import_probe',
                    '__package__': 'benchmarks', '__file__': str(root / name)})

    def test_exact_metadata_requires_current_recovery_dependency_and_never_retags_old_sdk(self):
        value = data.admission(); original = copy.deepcopy(value)
        self.assertEqual(len(contract.SOURCE_NAMES), 25)
        self.assertIn('prepare_recovery_contract.py', contract.SOURCE_NAMES)
        with patch.object(Path, 'open', side_effect=AssertionError('Structural reader performed IO')):
            self.assertEqual(contract.validate_admission(value), original)
        for mode in ('old_protocol', 'old_methods', 'missing_dependency', 'model', 'extra_source'):
            value = copy.deepcopy(original)
            if mode == 'old_protocol': value['protocol'] = sdk14.PROTOCOL
            elif mode == 'old_methods':
                value['sources'] = [dict(p, path=p['path'].replace('library_ui', 'record_controls_ui')) for p in value['sources']]
                value['sources'].sort(key=lambda p: p['path'])
            elif mode == 'missing_dependency': value['sources'] = [p for p in value['sources'] if PureWindowsPath(p['path']).name != 'prepare_recovery_contract.py']
            elif mode == 'model': value['artifacts']['model'] = legacy.pin('D:/Synthetic/not-authorized.task')
            else: value['sources'].append(legacy.pin('D:/Synthetic/LocalLore/benchmarks/unselected.py')); value['sources'].sort(key=lambda p: p['path'])
            with self.subTest(mode=mode), self.assertRaises(core.TargetRefused): contract.validate_admission(value)
        self.assertEqual(original, data.admission())
        with self.assertRaises(core.TargetRefused): sdk14.validate_admission(original)

    def test_only_literal_single_method_vectors_have_claim_authority(self):
        a = data.admission()
        for kind, cls, method in data.SELECTORS:
            argv = ['am', 'instrument', '-w', '-r', '-e', 'class', cls + '#' + method,
                contract.TEST + '/androidx.test.runner.AndroidJUnitRunner']
            self.assertEqual(contract.instrumentation_kind(argv), kind)
            self.assertEqual(contract.validate_operation({'argv': argv, 'stdin': None}, a)['argv'], argv)
            invalid = (argv + ['--user', '0'], argv[:6] + [cls + '#' + method + ',other'] + argv[7:])
            for vector in invalid:
                with self.assertRaises(core.TargetRefused): contract.validate_operation({'argv': vector, 'stdin': None}, a)
        old = sdk14.INSTRUMENTATIONS[0]
        invalid = (['am', 'instrument', '-w', '-r', '-e', 'class', old[1] + '#' + old[2], contract.TEST + '/androidx.test.runner.AndroidJUnitRunner'],
            ['pidof', contract.APP], ['am', 'force-stop', '--user', '0', contract.APP], ['sh', '-c', 'echo scope'],
            ['run-as', contract.APP, 'cat', 'files/private'], ['screencap', '-p'])
        for vector in invalid:
            with self.subTest(vector=vector), self.assertRaises(core.TargetRefused):
                contract.validate_operation({'argv': vector, 'stdin': None}, a)

    def test_claims_join_exact_admission_caller_kind_and_operation_without_a_fifth_kind(self):
        a = data.admission(); d = data.running(a); caller = d['worker']; binding = d['admission']
        for row in data.SELECTORS:
            operation = {'argv': ['am', 'instrument', '-w', '-r', '-e', 'class', row[1] + '#' + row[2],
                contract.TEST + '/androidx.test.runner.AndroidJUnitRunner'], 'stdin': None}
            digest = contract.operation_digest(operation)
            claim = contract.claim_record(binding, caller, row[0], digest)
            self.assertEqual(contract.validate_claim(claim, binding, caller, row[0], digest), claim)
            for change in ({'protocol': sdk14.PROTOCOL}, {'kind': 'library_fifth'}, {'admission_sha256': '0' * 64},
                {'operation_sha256': 'f' * 64}, {'caller': dict(caller, creation_filetime=caller['creation_filetime'] + 1)}):
                with self.subTest(kind=row[0], change=change), self.assertRaises(core.TargetRefused):
                    contract.validate_claim(dict(claim, **change), binding, caller, row[0], digest)

    def test_sdk15_client_session_and_every_cleanup_bit_remain_required(self):
        a = data.admission(); s = legacy.session(a)
        s['protocol'] = SDK_PROTOCOL; s['descriptor']['protocol'] = PROTOCOL
        self.assertEqual(contract.validate_session(s, a), s)
        row = legacy.GuestAndRecordTests().record()
        row.update(version=15, protocol=SDK_PROTOCOL, session=legacy.pin(PureWindowsPath(s['root']) / 'sdk-session-v15.json'))
        self.assertEqual(contract.validate_client_record(row, s), row)
        for key, bad in (('version', 14), ('protocol', sdk14.SDK_PROTOCOL), ('returncode', True),
            ('socket_closed', False), ('sender_joined', False), ('input_closed', False), ('cleanup_complete', False), ('server_after', None)):
            with self.subTest(key=key), self.assertRaises(core.TargetRefused):
                contract.validate_client_record(dict(row, **{key: bad}), s)

    @unittest.skipUnless(os.name == 'nt', 'Tiny physical D constructor fixtures')
    def test_product_refusal_precedes_public_owner_worker_and_native_observer(self):
        files = data.SyntheticFiles(); path = files.base / 'admission.json'
        wire.environment.create_json(path, data.admission()); pin = wire.environment.binding(path)
        with patch.object(build, 'verify_current', side_effect=build.BuildRefused('synthetic unqualified product')) as gate, \
             patch.object(mechanisms._LiveOwnedTarget, '__init__') as live, \
             patch.object(mechanisms._TargetRuntimeCore, '__init__') as worker, \
             patch.object(mechanisms, '_parent') as parent:
            with self.assertRaises(build.BuildRefused): owner.LiveOwnedLibraryUiTarget(pin, pin)
            with self.assertRaises(build.BuildRefused): owner._LibraryUiTargetRuntime({'validated_admission': data.admission()}, pin, files.base)
            with redirect_stdout(io.StringIO()):
                self.assertEqual(owner.main(['--admission', pin['path'], '--admission-sha256', pin['sha256']]), 1)
            live.assert_not_called(); worker.assert_not_called(); parent.assert_not_called(); self.assertEqual(gate.call_count, 3)

    @unittest.skipUnless(os.name == 'nt', 'Real source bytes and synthetic external artifact pins')
    def test_stale_or_wrong_recovery_dependency_refuses_before_native_or_parent_dispatch(self):
        graph = data.ControllerGraph(); real_verify = build.verify_current
        for missing in (False, True):
            value = copy.deepcopy(graph.a)
            if missing: value['sources'] = [p for p in value['sources'] if PureWindowsPath(p['path']).name != 'prepare_recovery_contract.py']
            else: next(p for p in value['sources'] if PureWindowsPath(p['path']).name == 'prepare_recovery_contract.py')['sha256'] = 'f' * 64
            path = graph.g.base / ('missing.json' if missing else 'wrong.json'); wire.environment.create_json(path, value)
            pin = wire.environment.binding(path)
            with graph.inputs(), patch.object(build, 'verify_current', side_effect=real_verify), \
                 patch.object(build, 'verify_frozen_product') as product, \
                 patch.object(mechanisms._LiveOwnedTarget, '__init__') as live, patch.object(mechanisms, '_parent') as parent:
                with self.assertRaises(core.TargetRefused): owner.LiveOwnedLibraryUiTarget(pin, graph.running)
                with redirect_stdout(io.StringIO()):
                    self.assertEqual(owner.main(['--admission', pin['path'], '--admission-sha256', pin['sha256']]), 1)
                product.assert_not_called(); live.assert_not_called(); parent.assert_not_called()


if __name__ == '__main__': unittest.main()
