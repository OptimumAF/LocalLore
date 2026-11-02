"""Original SDK16 authority and dispatch adversaries; synthetic metadata is not a device result."""
import copy
from contextlib import ExitStack, redirect_stdout
import io
import os
from pathlib import Path, PureWindowsPath
import unittest
from unittest.mock import patch

from benchmarks import android_process_client_v4 as wire
from benchmarks import android_process_knowledge_ui_client as client
from benchmarks import android_process_knowledge_ui_verification as verification
from benchmarks import knowledge_ui_profile_build as build
from benchmarks import owned_knowledge_ui_contract as contract
from benchmarks import owned_knowledge_ui_owner as owner
from benchmarks import owned_record_controls_ui_contract as sdk14
from benchmarks import owned_library_ui_contract as sdk15
from benchmarks import owned_target_contract as core
from benchmarks import owned_target_owner as mechanisms
from benchmarks import receipt_avd_storage as storage
from scripts.tests import test_knowledge_ui_controller_fixtures as data
from scripts.tests import test_owned_target_contract as legacy

PROTOCOL = 'owned-emulator-knowledge-ui-v1'
SDK_PROTOCOL = 'sdk-knowledge-ui-v1'
PROOF_PROTOCOL = 'knowledge-ui-socket-proof-v1'


class KnowledgeUiAuthorityTests(unittest.TestCase):
    def test_literal_four_method_authority_is_distinct_from_nineteen_method_sdk14(self):
        self.assertEqual((contract.PROTOCOL, contract.SDK_PROTOCOL, contract.PROOF_PROTOCOL),
            (PROTOCOL, SDK_PROTOCOL, PROOF_PROTOCOL))
        self.assertEqual((contract.CLIENT_VERSION, contract.SESSION_FILE, contract.OWNER_SCRIPT, contract.BOOT_CLAIM_FILE),
            (16, 'sdk-session-v16.json', 'owned_knowledge_ui_owner.py', 'owned-knowledge-ui-boot-claim-v1.json'))
        self.assertEqual(contract.INSTRUMENTATIONS, data.SELECTORS)
        self.assertEqual(contract.CLAIM_KINDS, tuple(row[0] for row in data.SELECTORS))
        self.assertEqual(len(contract.INSTRUMENTATIONS), 4)
        self.assertNotEqual(contract.GUEST_ROOT, sdk14.GUEST_ROOT)
        self.assertEqual(str(contract.GUEST_ROOT), str(PureWindowsPath(
            'D:/Dev/Experiments/LocalLore/2026-11-02-knowledge-ui-v1/avd-v1')))
        self.assertEqual((contract.APP, contract.TEST, contract.MODEL_MATERIAL), ('org.locallore.app', 'org.locallore.app.test', False))
        self.assertEqual(contract.ARTIFACT_KEYS, {'build', 'product_apk', 'test_apk'})
        self.assertEqual(len(sdk14.INSTRUMENTATIONS), 19)

    def test_imported_definitions_cannot_observe_allocate_publish_or_launch(self):
        root = Path(__file__).resolve().parents[2] / 'benchmarks'
        names = ('owned_knowledge_ui_contract.py', 'owned_knowledge_ui_owner.py',
            'android_process_knowledge_ui_client.py', 'android_process_knowledge_ui_verification.py',
            'knowledge_ui_profile_build.py', 'knowledge_ui_controller.py', 'knowledge_ui_activation.py')
        sources = {name: (root / name).read_bytes() for name in names}
        with ExitStack() as stack:
            for target, name in ((Path, 'open'), (Path, 'stat'), (Path, 'mkdir'), (wire.socket, 'socket'),
                (mechanisms.subprocess, 'Popen'), (wire.environment, 'create_json'),
                (storage, 'reserve_prepare'), (storage, 'record_state'), (storage, 'record_closed')):
                stack.enter_context(patch.object(target, name, side_effect=AssertionError('Import performed host work')))
            for name, raw in sources.items():
                exec(compile(raw, str(root / name), 'exec'), {'__name__': 'benchmarks._sdk16_import_probe',
                    '__package__': 'benchmarks', '__file__': str(root / name)})

    def test_exact_metadata_requires_current_recovery_dependency_and_never_retags_old_sdk(self):
        value = data.admission(); original = copy.deepcopy(value)
        self.assertEqual(len(contract.SOURCE_NAMES), 28)
        self.assertIn('prepare_recovery_contract.py', contract.SOURCE_NAMES)
        with patch.object(Path, 'open', side_effect=AssertionError('Structural reader performed IO')):
            self.assertEqual(contract.validate_admission(value), original)
        for mode in ('old_protocol', 'old_methods', 'missing_dependency', 'model', 'extra_source'):
            value = copy.deepcopy(original)
            if mode == 'old_protocol': value['protocol'] = sdk14.PROTOCOL
            elif mode == 'old_methods':
                value['sources'] = [dict(p, path=p['path'].replace('knowledge_ui', 'record_controls_ui')) for p in value['sources']]
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

    def test_sdk16_client_session_and_every_cleanup_bit_remain_required(self):
        a = data.admission(); s = legacy.session(a)
        s['protocol'] = SDK_PROTOCOL; s['descriptor']['protocol'] = PROTOCOL
        self.assertEqual(contract.validate_session(s, a), s)
        row = legacy.GuestAndRecordTests().record()
        row.update(version=16, protocol=SDK_PROTOCOL, session=legacy.pin(PureWindowsPath(s['root']) / 'sdk-session-v16.json'))
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
            with self.assertRaises(build.BuildRefused): owner.LiveOwnedKnowledgeUiTarget(pin, pin)
            with self.assertRaises(build.BuildRefused): owner._KnowledgeUiTargetRuntime({'validated_admission': data.admission()}, pin, files.base)
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
                 patch.object(build.build, 'verify_frozen_product') as product, \
                 patch.object(mechanisms._LiveOwnedTarget, '__init__') as live, patch.object(mechanisms, '_parent') as parent:
                with self.assertRaises(core.TargetRefused): owner.LiveOwnedKnowledgeUiTarget(pin, graph.running)
                with redirect_stdout(io.StringIO()):
                    self.assertEqual(owner.main(['--admission', pin['path'], '--admission-sha256', pin['sha256']]), 1)
                product.assert_not_called(); live.assert_not_called(); parent.assert_not_called()


    def test_independent_literal_source_closure_has_no_unselected_owner_or_old_profile(self):
        expected = {
            'adb_held_socket_probe.py', 'adb_held_socket.py', 'adb_held_socket_windows.py',
            'windows_tcp_control.py', 'windows_tcp_observation.py', 'receipt_avd_environment.py',
            'runtime_spike.py', 'host_commit_capacity.py', 'isolated_adb_lease.py', 'isolated_adb_owner.py',
            'owned_target_contract.py', 'owned_target_owner.py', 'receipt_avd_storage.py',
            'android_process_client_v4.py', 'android_process_verification_v4.py',
            'prepare_recovery_contract.py', 'owned_knowledge_ui_contract.py',
            'owned_knowledge_ui_owner.py', 'android_process_knowledge_ui_client.py',
            'android_process_knowledge_ui_verification.py', 'knowledge_ui_profile_build.py',
            'knowledge_ui_controller.py', 'knowledge_ui_activation.py', 'knowledge_ui_build.py',
            'knowledge_ui_build_baseline.json', 'library_ui_build.py',
            'library_ui_build_baseline.json', 'android_instrumentation_evidence.py',
        }
        self.assertEqual(contract.SOURCE_NAMES, expected)
        self.assertNotEqual(contract.SOURCE_NAMES, sdk15.SOURCE_NAMES)
        original = data.admission()
        for name in sorted(expected):
            value = copy.deepcopy(original)
            value['sources'] = [pin for pin in value['sources'] if PureWindowsPath(pin['path']).name != name]
            with self.subTest(missing=name), self.assertRaises(core.TargetRefused):
                contract.validate_admission(value)

    def test_unchanged_sdk15_metadata_and_selectors_cannot_be_retagged_by_same_guest_or_packages(self):
        original = data.admission()
        old = copy.deepcopy(original)
        old['protocol'] = sdk15.PROTOCOL
        old['sources'] = sorted([legacy.pin(PureWindowsPath('D:/Synthetic/LocalLore/benchmarks') / name)
                                  for name in sdk15.SOURCE_NAMES], key=lambda pin: pin['path'])
        self.assertEqual(sdk15.validate_admission(old), old)
        with self.assertRaises(core.TargetRefused): contract.validate_admission(old)
        old['protocol'] = contract.PROTOCOL
        with self.assertRaises(core.TargetRefused): contract.validate_admission(old)
        with self.assertRaises(core.TargetRefused): sdk15.validate_admission(original)
        for kind, cls, method in sdk15.INSTRUMENTATIONS:
            argv = ['am', 'instrument', '-w', '-r', '-e', 'class', cls+'#'+method,
                    contract.TEST+'/androidx.test.runner.AndroidJUnitRunner']
            with self.subTest(kind=kind), self.assertRaises(core.TargetRefused):
                contract.validate_operation(dict(argv=argv, stdin=None), original)
        session = legacy.session(original)
        session['protocol'] = sdk15.SDK_PROTOCOL
        session['descriptor']['protocol'] = sdk15.PROTOCOL
        with self.assertRaises(core.TargetRefused): contract.validate_session(session, original)

    def test_build_wrapper_revalidates_on_both_sides_and_returns_the_exact_raw_object(self):
        # Deliberately mocked freshness; this is not operational admission evidence.
        admission = data.admission(); raw = data.raw_manifest(admission)
        before = copy.deepcopy(raw); order = []
        def validate(value):
            order.append('freshness'); self.assertEqual(value, admission)
        def product(artifacts):
            order.append('product'); self.assertEqual(artifacts, admission['artifacts']); return raw
        with patch.object(build.contract, 'revalidate_inputs', side_effect=validate) as fresh, \
             patch.object(build.build, 'verify_frozen_product', side_effect=product) as frozen:
            result = build.verify_current(admission)
        self.assertIs(result, raw); self.assertEqual(result, before)
        self.assertEqual(order, ['freshness', 'product', 'freshness'])
        self.assertEqual(fresh.call_count, 2); frozen.assert_called_once_with(admission['artifacts'])
        self.assertNotIn('roster', result); self.assertNotIn('apks', result)

    def test_build_wrapper_refuses_old_projection_wrong_roster_and_late_source_change(self):
        admission = data.admission()
        for fault in ('old_projection', 'reordered', 'fifth', 'sdk15', 'missing', 'late_source'):
            raw = data.raw_manifest(admission)
            if fault == 'old_projection': raw = {'roster': raw['instrumentations'], 'apks': raw['artifacts']}
            elif fault == 'reordered': raw['instrumentations'][0:2] = reversed(raw['instrumentations'][0:2])
            elif fault == 'fifth': raw['instrumentations'].append(raw['instrumentations'][0])
            elif fault == 'sdk15': raw['instrumentations'] = [list(row) for row in sdk15.INSTRUMENTATIONS]
            elif fault == 'missing': raw['instrumentations'].pop()
            freshness = [None, core.TargetRefused('synthetic late source drift')] if fault == 'late_source' else None
            with self.subTest(fault=fault), \
                 patch.object(build.contract, 'revalidate_inputs', side_effect=freshness) as fresh, \
                 patch.object(build.build, 'verify_frozen_product', return_value=raw) as product:
                with self.assertRaises(core.TargetRefused): build.verify_current(admission)
                product.assert_called_once_with(admission['artifacts'])
                self.assertEqual(fresh.call_count, 2 if fault == 'late_source' else 1)

    def test_build_wrapper_never_calls_product_after_structural_or_initial_freshness_refusal(self):
        admission = data.admission()
        with patch.object(build.contract, 'revalidate_inputs', side_effect=core.TargetRefused('synthetic stale source')), \
             patch.object(build.build, 'verify_frozen_product') as product:
            with self.assertRaises(core.TargetRefused): build.verify_current(admission)
            product.assert_not_called()
        for key, bad in (('protocol', sdk15.PROTOCOL), ('version', True), ('seconds', True)):
            value = copy.deepcopy(admission); value[key] = bad
            with self.subTest(key=key), patch.object(build.contract, 'revalidate_inputs') as fresh, \
                 patch.object(build.build, 'verify_frozen_product') as product:
                with self.assertRaises(core.TargetRefused): build.verify_current(value)
                fresh.assert_not_called(); product.assert_not_called()


    def test_concrete_owner_and_capture_types_cannot_be_subclassed_or_caller_selected(self):
        class SubstituteOwner(owner.LiveOwnedKnowledgeUiTarget): pass
        class SubstituteWorker(owner._KnowledgeUiTargetRuntime): pass
        class SubstituteCapture(client.OwnedKnowledgeUiSdkCapture): pass
        self.assertIs(client._lease_class(), owner.LiveOwnedKnowledgeUiTarget)
        with patch.object(mechanisms._LiveOwnedTarget, '__init__') as live, \
             patch.object(mechanisms._TargetRuntimeCore, '__init__') as worker, \
             patch.object(wire._OwnedTargetSdkCapture, '__init__') as capture, \
             patch.object(build, 'verify_current') as product:
            with self.assertRaisesRegex(owner.OwnerRefused, '^owner_type$'): SubstituteOwner({}, {})
            with self.assertRaisesRegex(owner.OwnerRefused, '^owner_type$'): SubstituteWorker({}, {}, None)
            with self.assertRaises(client.ClientRefused): SubstituteCapture(None, 1, None)
            live.assert_not_called(); worker.assert_not_called(); capture.assert_not_called()
            product.assert_not_called()


    @unittest.skipUnless(os.name == 'nt', 'Windows paths; no SDK or native calls')
    def test_public_environment_rejects_old_source_proposal_before_reading_authorization(self):
        # Metadata only: neither proposal nor authority is published. Token lookup
        # is mocked so even the installed Windows profile API is not invoked.
        env = wire.environment
        root = Path('D:/Synthetic/LocalLore/source-bound-guest')
        sdk = Path('D:/Synthetic/LocalLore/sdk')
        current = [Path(env.__file__).resolve(), Path(env.host.__file__).resolve(),
            Path(env.commit_capacity.__file__).resolve(), Path(env.guest_storage.__file__).resolve(),
            Path(env.__file__).with_name('prepare_recovery_contract.py').resolve()]
        tools = [sdk/'platform-tools/adb.exe', sdk/'emulator/emulator.exe',
            sdk/'cmdline-tools/latest/bin/avdmanager.bat',
            sdk/'system-images/android-35/google_apis/x86_64/data/empty_data_disk']
        token = 'D:/Synthetic/LocalLore/token'
        proposal = dict(version=1, phase='run', avd_name=env.NAME, serial='emulator-5592',
            console_port=env.PORT, sdk=str(sdk), java_home='D:/Synthetic/LocalLore/jdk',
            paths=env.paths(root), adb_path=str(tools[0]), token={'path': token}, old_avd={},
            bindings=[{'path': str(p)} for p in current+tools], userdata_mib=12288, sdcard_mib=8192,
            memory_mib=8192, cores=4, host_free_min=env.root_free_min(root),
            host_available_memory_min=12*env.GIB, allow_environment_calls=False, root_go_pending=True,
            prepare_proposal={}, prepared={}, prepare_result={}, max_seconds=1800)
        with patch.object(env, 'token_path', return_value=token):
            self.assertIsNone(env.validate_proposal(proposal, 'run'))
            old = copy.deepcopy(proposal)
            for pin in old['bindings'][:len(current)]:
                pin['path'] = str(Path('D:/Worktrees/locallore-record-actions-tests-v1/benchmarks') /
                                  Path(pin['path']).name)
            with patch.object(env, 'read_json', return_value=old) as read, \
                 patch.object(env, 'verify_installation') as installation, \
                 patch.object(env, 'check_external_state') as external:
                with self.assertRaises(env.EnvironmentRefused):
                    env.authorize('unpublished-proposal.json', 'unpublished-authority.json', 'run')
                read.assert_called_once_with('unpublished-proposal.json')
                installation.assert_not_called(); external.assert_not_called()
            self.assertIsNone(env.validate_proposal(proposal, 'run'))


if __name__ == '__main__': unittest.main()
