"""Original SDK18 authority/build boundary oracles; all observations are metadata ports."""
import copy
import os
from pathlib import Path, PureWindowsPath
import socket
from types import SimpleNamespace
import unittest
from unittest.mock import Mock, patch

from benchmarks import owned_target_contract as core
from benchmarks import owned_diagnostic_ui_contract as sdk17
from benchmarks import owned_record_cancellation_ui_contract as c
from benchmarks import owned_record_cancellation_ui_owner as owner
from benchmarks import android_process_record_cancellation_ui_client as client
from benchmarks import record_cancellation_ui_profile_build as build
from scripts.tests import test_record_cancellation_ui_profile_fixtures as f

ADDITIONS = {
    'owned_record_cancellation_ui_contract.py', 'owned_record_cancellation_ui_owner.py',
    'android_process_record_cancellation_ui_client.py', 'android_process_record_cancellation_ui_verification.py',
    'record_cancellation_ui_profile_build.py', 'record_cancellation_ui_controller.py',
    'record_cancellation_ui_activation.py', 'record_cancellation_ui_build.py',
    'record_cancellation_ui_build_baseline.json', 'diagnostic_ui_build.py',
    'archive_ui_build.py', 'android_instrumentation_evidence.py',
}


class RecordCancellationUiProfileTests(unittest.TestCase):
    def test_sdk18_literal_authority_has_five_exact_claims_and_no_model(self):
        self.assertEqual((c.PROTOCOL, c.SDK_PROTOCOL, c.PROOF_PROTOCOL),
            ('owned-emulator-record-cancellation-ui-v1', 'sdk-record-cancellation-ui-v1',
             'record-cancellation-ui-socket-proof-v1'))
        self.assertEqual((c.CLIENT_VERSION, c.SESSION_FILE), (18, 'sdk-session-v18.json'))
        self.assertEqual(str(c.GUEST_ROOT), str(PureWindowsPath(
            'D:/Dev/Experiments/LocalLore/2026-11-03-record-cancellation-ui-v1/avd-v1')))
        self.assertEqual(c.OWNER_SCRIPT, 'owned_record_cancellation_ui_owner.py')
        self.assertEqual(c.BOOT_CLAIM_FILE, 'owned-record-cancellation-ui-boot-claim-v1.json')
        self.assertEqual(c.CERTIFICATE_SHA256, f.CERTIFICATE)
        self.assertEqual(tuple(c.INSTRUMENTATIONS), f.INSTRUMENTATIONS)
        self.assertEqual(tuple(c.CLAIM_KINDS), ('record_cancel_1', 'record_cancel_2', 'record_cancel_3', 'record_cancel_4', 'record_cancel_5'))
        self.assertIs(c.MODEL_MATERIAL, False)
        self.assertEqual(c.SOURCE_NAMES, core.SOURCE_NAMES | core.CURRENT_STORAGE_SOURCES | ADDITIONS)
        self.assertEqual(len(c.SOURCE_NAMES), 28)

    def test_retagging_sdk17_cannot_borrow_its_root_or_replace_source_closure(self):
        value = f.admission()
        c.validate_admission(value)
        variants = []
        for key, wrong in (('protocol', 'owned-emulator-diagnostic-ui-v1'), ('root', str(sdk17.GUEST_ROOT))):
            bad = copy.deepcopy(value)
            (bad['guest'] if key == 'root' else bad)[key] = wrong
            variants.append(bad)
        bad = copy.deepcopy(value)
        bad['sources'] = [row for row in bad['sources']
            if PureWindowsPath(row['path']).name != 'record_cancellation_ui_profile_build.py']
        variants.append(bad)
        bad = copy.deepcopy(value)
        bad['sources'][0]['path'] = 'D:/Foreign/benchmarks/' + PureWindowsPath(bad['sources'][0]['path']).name
        variants.append(bad)
        observations = Mock(side_effect=AssertionError('unexpected observation'))
        with patch.object(Path, 'open', observations), patch.object(socket, 'socket', observations):
            for bad in variants:
                with self.subTest(bad=bad['protocol']), self.assertRaises(c.TargetRefused):
                    c.validate_admission(bad)
        self.assertEqual(observations.call_count, 0)

    def test_validation_detaches_caller_data_and_rejects_new_authority_fields(self):
        value = f.admission(); before = copy.deepcopy(value)
        detached = c.validate_admission(value)
        detached['sources'][0]['sha256'] = '0' * 64
        self.assertEqual(value, before)
        for field in ('registry', 'profile', 'implementation', 'selectors', 'model'):
            bad = copy.deepcopy(value); bad[field] = 'caller-selected'
            with self.subTest(field=field), self.assertRaises(c.TargetRefused): c.validate_admission(bad)
        for bad_number in (True, 1200.0):
            bad = copy.deepcopy(value); bad['seconds'] = bad_number
            with self.assertRaises(c.TargetRefused): c.validate_admission(bad)

    def test_finite_command_grammar_cannot_widen_a_selected_test_or_gain_shell_authority(self):
        value = f.admission()
        for triple in f.INSTRUMENTATIONS:
            operation = dict(argv=f.instrument(triple), stdin=None)
            self.assertEqual(c.validate_operation(operation, value), operation)
            self.assertEqual(c.instrumentation_kind(operation['argv']), triple[0])
        forbidden = [
            ['sh', '-c', 'id'], ['pidof', f.APP], ['am', 'force-stop', f.APP],
            ['am', 'instrument', '-w', f.TEST + '/androidx.test.runner.AndroidJUnitRunner'],
            f.instrument(f.INSTRUMENTATIONS[0]) + ['-e', 'class', 'foreign.Class#method'],
            ['run-as', f.APP, 'cat', 'files/model.bin'],
        ]
        for argv in forbidden:
            with self.subTest(argv=argv), self.assertRaises(c.TargetRefused):
                c.validate_operation(dict(argv=argv, stdin=None), value)

    def test_sdk17_session_and_proof_cannot_be_relabelled_into_sdk18(self):
        value = f.admission(); session = f.session(value); proof = f.proof(session)
        c.validate_session(session, value); c.validate_proof(proof, session, proof['context'])
        for field in ('tag', 'session_file', 'descriptor'):
            wrong = copy.deepcopy(proof); s = copy.deepcopy(session)
            if field == 'tag': wrong['protocol'] = 'diagnostic-ui-socket-proof-v1'
            elif field == 'session_file': wrong['session']['path'] = str(PureWindowsPath(s['root']) / 'sdk-session-v17.json')
            else: s['descriptor']['run_id'] = 'f' * 32
            with self.subTest(field=field), self.assertRaises(c.TargetRefused):
                c.validate_session(s, value); c.validate_proof(wrong, s, wrong['context'])

    def test_foreign_concrete_types_are_rejected_without_file_or_socket_attempts(self):
        class DerivedOwner(owner.LiveOwnedRecordCancellationUiTarget): pass
        class DerivedRuntime(owner._RecordCancellationUiTargetRuntime): pass
        class DerivedCapture(client.OwnedRecordCancellationUiSdkCapture): pass
        observed = Mock(side_effect=AssertionError('unapproved observation'))
        with patch.object(Path, 'open', observed), patch.object(socket, 'socket', observed):
            with self.assertRaisesRegex(owner.OwnerRefused, '^owner_type$'): DerivedOwner({}, {})
            with self.assertRaisesRegex(owner.OwnerRefused, '^owner_type$'): DerivedRuntime({}, {}, Path('D:/Unused'))
            with self.assertRaises(client.ClientRefused): DerivedCapture(Path('D:/Unused'), 10, object())
        self.assertEqual(observed.call_count, 0)

    def test_b111_projection_is_detached_and_preserves_only_fixed_apk_identity(self):
        raw = f.raw_manifest(); before = copy.deepcopy(raw)
        result = build.project_manifest(raw)
        self.assertEqual(result['roster'], [list(row) for row in f.INSTRUMENTATIONS])
        for role, package in (('product_apk', f.APP), ('test_apk', f.TEST)):
            self.assertEqual(result['apks'][role], dict(binding=raw['artifacts'][role], package=package, certificate_sha256=f.CERTIFICATE))
        result['roster'][0][2] = 'borrowedMethod'
        result['apks']['product_apk']['binding']['sha256'] = '0' * 64
        self.assertEqual(raw, before)

    def test_projection_refuses_wrong_provenance_boolean_facts_or_borrowed_body_units(self):
        for change in ('head', 'tree', 'scope', 'mode', 'bool_count', 'authority', 'units', 'boolean_units', 'reordered', 'class', 'extra_row_key'):
            raw = f.raw_manifest()
            if change in ('head', 'tree'): raw['product'][change] = '0' * 40
            elif change == 'scope': raw['scope'] = 'diagnostic-ui-build-v1'
            elif change == 'mode': raw['mode'] = 'fixed-b103-raw-git-attestation-v1'
            elif change == 'bool_count': raw['facts']['recorded_jvm_cases'] = True
            elif change == 'authority': raw['facts']['run_authority'] = True
            elif change == 'units': raw['facts']['selected_methods'][0]['instruction_units'] = 536
            elif change == 'boolean_units': raw['facts']['selected_methods'][0]['instruction_units'] = True
            elif change == 'reordered': raw['instrumentations'].reverse()
            elif change == 'class': raw['facts']['selected_methods'][0]['class_name'] = 'org.locallore.app.DiagnosticsIntegrationTest'
            else: raw['facts']['selected_methods'][0]['compiled'] = True
            with self.subTest(change=change), self.assertRaises(c.TargetRefused): build.project_manifest(raw)

    def test_audit_signer_permissions_short_pins_and_artifact_roles_are_joined(self):
        for change in ('signer', 'package', 'permissions', 'size', 'sha', 'extra_role', 'legacy_shape'):
            raw = f.raw_manifest(); audit = raw['facts']['package_audit']
            if change == 'signer': audit['certificate_sha256'] = '0' * 64
            elif change == 'package': audit['package'] = f.TEST
            elif change == 'permissions': audit['test_permissions'].append('android.permission.INTERNET')
            elif change == 'size': audit['app']['bytes'] = True
            elif change == 'sha': audit['test']['sha256'] = raw['artifacts']['product_apk']['sha256']
            elif change == 'extra_role': raw['artifacts']['model'] = f.legacy.pin('D:/Synthetic/model.bin')
            else: raw = dict(roster=[list(row) for row in f.INSTRUMENTATIONS], apks=raw['artifacts'])
            with self.subTest(change=change), self.assertRaises(c.TargetRefused): build.project_manifest(raw)

    def test_wrapper_orders_two_guards_around_verifier_and_returns_identical_raw_object(self):
        admission = f.admission(); raw = f.raw_manifest(admission['artifacts']); original = copy.deepcopy(raw)
        order = []
        with patch.object(c, 'revalidate_inputs', side_effect=lambda _: order.append('guard')), \
             patch.object(build.build, 'verify_frozen_product', side_effect=lambda pins: order.append(('verify', copy.deepcopy(pins))) or raw):
            returned = build.verify_current(admission)
        self.assertIs(returned, raw)
        self.assertEqual(raw, original)
        self.assertEqual(order, ['guard', ('verify', admission['artifacts']), 'guard'])

    def test_invalid_admission_never_attempts_verifier_and_late_guard_is_fatal(self):
        wrong = f.admission(); wrong['protocol'] = 'owned-emulator-diagnostic-ui-v1'
        with patch.object(c, 'revalidate_inputs') as guards, patch.object(build.build, 'verify_frozen_product') as verifier:
            with self.assertRaises(c.TargetRefused): build.verify_current(wrong)
        self.assertEqual(guards.call_count, 0); self.assertEqual(verifier.call_count, 0)
        admission = f.admission(); raw = f.raw_manifest(admission['artifacts'])
        with patch.object(c, 'revalidate_inputs', side_effect=[None, c.TargetRefused('source')]) as guards, \
             patch.object(build.build, 'verify_frozen_product', return_value=raw) as verifier:
            with self.assertRaises(c.TargetRefused): build.verify_current(admission)
        self.assertEqual(guards.call_count, 2); self.assertEqual(verifier.call_count, 1)

    def test_checker_runs_on_both_sides_and_cached_transitive_module_cannot_move(self):
        order = []
        with patch.object(build, 'revalidate_checker', side_effect=lambda: order.append('checker')), \
             patch.object(core._Contract, 'revalidate_inputs', side_effect=lambda a: order.append('shared') or a):
            self.assertEqual(c.revalidate_inputs(f.admission()), f.admission())
        self.assertEqual(order, ['checker', 'shared', 'checker'])
        if os.name != 'nt': return
        from benchmarks import archive_ui_build as reader
        root = Path(build.__file__).parents[1]
        decoder = SimpleNamespace(__file__=str(root / 'scripts/audit_physical_model_apk.py'),
            base=SimpleNamespace(__file__=str(root / 'scripts/audit_apk.py')))
        with patch.object(reader, '_bound') as pins, patch.dict(build.sys.modules, {'scripts.audit_physical_model_apk': decoder}):
            build.revalidate_checker()
            self.assertEqual(pins.call_count, 2)
            decoder.base.__file__ = str(root / 'scripts/borrowed_audit.py')
            with self.assertRaises(c.TargetRefused): build.revalidate_checker()
