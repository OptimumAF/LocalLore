"""Original SDK17 contract/build/type oracles; no live authority is constructed."""
import copy
import os
from pathlib import Path, PureWindowsPath
import socket
from types import SimpleNamespace
import unittest
from unittest.mock import patch

from benchmarks import owned_target_contract as core
from benchmarks import owned_record_ui_contract as old
from benchmarks import owned_diagnostic_ui_contract as c
from benchmarks import owned_diagnostic_ui_owner as owner
from benchmarks import android_process_diagnostic_ui_client as client
from benchmarks import diagnostic_ui_profile_build as build
from benchmarks import diagnostic_ui_controller as controller
from scripts.tests import test_diagnostic_ui_profile_fixtures as f

NEW_SOURCES = {
    'owned_diagnostic_ui_contract.py', 'owned_diagnostic_ui_owner.py',
    'android_process_diagnostic_ui_client.py', 'android_process_diagnostic_ui_verification.py',
    'diagnostic_ui_profile_build.py', 'diagnostic_ui_controller.py', 'diagnostic_ui_activation.py',
    'diagnostic_ui_build.py', 'diagnostic_ui_build_baseline.json',
    'archive_ui_build.py', 'android_instrumentation_evidence.py',
}


class DiagnosticUiProfileTests(unittest.TestCase):
    def test_fixed_seventeen_namespace_root_signer_roster_and_complete_source_closure(self):
        self.assertEqual((c.PROTOCOL, c.SDK_PROTOCOL, c.PROOF_PROTOCOL), (f.PROTOCOL, f.SDK_PROTOCOL, f.PROOF_PROTOCOL))
        self.assertEqual((c.CLIENT_VERSION, c.SESSION_FILE), (17, 'sdk-session-v17.json'))
        self.assertEqual(c.GUEST_ROOT, f.GUEST_ROOT)
        self.assertEqual(c.OWNER_SCRIPT, 'owned_diagnostic_ui_owner.py')
        self.assertEqual(c.BOOT_CLAIM_FILE, 'owned-diagnostic-ui-boot-claim-v1.json')
        self.assertEqual(c.CERTIFICATE_SHA256, f.CERTIFICATE)
        self.assertEqual((c.APP, c.TEST, c.MODEL_MATERIAL), (f.APP, f.TEST, False))
        self.assertEqual(tuple(c.INSTRUMENTATIONS), f.INSTRUMENTATIONS)
        self.assertEqual(tuple(c.CLAIM_KINDS), tuple(row[0] for row in f.INSTRUMENTATIONS))
        self.assertEqual(c.ARTIFACT_KEYS, frozenset(('build', 'product_apk', 'test_apk')))
        self.assertEqual(c.SOURCE_NAMES, core.SOURCE_NAMES | core.CURRENT_STORAGE_SOURCES | NEW_SOURCES)

    def test_admission_is_detached_and_observation_free(self):
        value = f.admission()
        before = copy.deepcopy(value)
        with patch.object(Path, 'open', side_effect=AssertionError('file observation')), \
             patch.object(socket, 'socket', side_effect=AssertionError('socket observation')):
            actual = c.validate_admission(value)
        self.assertEqual(actual, before)
        actual['sources'].clear()
        self.assertEqual(value, before)

    def test_borrowed_sdk16_and_legacy_roots_protocols_or_retagged_sources_refuse(self):
        value = f.admission()
        self.assertEqual(c.validate_admission(value), value)
        borrowed = copy.deepcopy(value)
        borrowed['protocol'] = 'owned-emulator-knowledge-ui-v1'
        borrowed['guest']['root'] = 'D:/Dev/Experiments/LocalLore/2026-11-02-knowledge-ui-v1/avd-v1'
        for bad in (borrowed, f.legacy.admission()):
            with self.assertRaises(core.TargetRefused): c.validate_admission(bad)
        for wrong in (str(old.GUEST_ROOT), str(f.GUEST_ROOT.parent / 'other.avd')):
            bad = copy.deepcopy(value); bad['guest']['root'] = wrong
            with self.assertRaises(core.TargetRefused): c.validate_admission(bad)
        bad = copy.deepcopy(value)
        bad['sources'] = [row for row in bad['sources'] if PureWindowsPath(row['path']).name != 'diagnostic_ui_activation.py']
        with self.assertRaises(core.TargetRefused): c.validate_admission(bad)
        with self.assertRaises(core.TargetRefused): old.validate_admission(value)

    def test_sources_cannot_be_missing_duplicated_reparented_or_mistyped(self):
        for mutation in ('missing', 'duplicate', 'foreign_parent', 'extra', 'bool_size'):
            with self.subTest(mutation=mutation):
                value = f.admission()
                if mutation == 'missing': value['sources'] = value['sources'][:-1]
                elif mutation == 'duplicate': value['sources'].append(copy.deepcopy(value['sources'][0]))
                elif mutation == 'foreign_parent': value['sources'][0]['path'] = 'D:/Foreign/' + PureWindowsPath(value['sources'][0]['path']).name
                elif mutation == 'extra': value['sources'].append(f.legacy.pin('D:/Synthetic/LocalLore/benchmarks/caller_profile.py'))
                else: value['sources'][0]['bytes'] = True
                with self.assertRaises(core.TargetRefused): c.validate_admission(value)

    def test_no_extra_authority_model_artifacts_or_scalar_coercion(self):
        for mutation in ('model', 'profile', 'implementation', 'selectors', 'registry', 'bool_seconds', 'float_seconds'):
            with self.subTest(mutation=mutation):
                value = f.admission()
                if mutation == 'model': value['artifacts']['model'] = f.legacy.pin('D:/Synthetic/model.bin')
                elif mutation == 'bool_seconds': value['seconds'] = True
                elif mutation == 'float_seconds': value['seconds'] = float(value['seconds'])
                else: value[mutation] = 'caller-controlled'
                with self.assertRaises(core.TargetRefused): c.validate_admission(value)

    def test_only_exact_six_instrumentations_have_their_own_claim_kinds(self):
        value = f.admission()
        for triple in f.INSTRUMENTATIONS:
            command = dict(argv=f.instrument(triple), stdin=None)
            self.assertEqual(c.validate_operation(command, value), command)
            self.assertEqual(c.instrumentation_kind(command['argv']), triple[0])
        bad_commands = [
            ['sh', '-c', 'id'], ['pidof', f.APP], ['am', 'force-stop', f.APP],
            ['am', 'instrument', '-w', f.TEST + '/androidx.test.runner.AndroidJUnitRunner'],
            f.instrument(f.INSTRUMENTATIONS[0]) + ['-e', 'debug', 'true'],
            f.instrument(('foreign', f.INSTRUMENTATIONS[0][1], 'notTheSelectedMethod')),
            f.instrument(f.INSTRUMENTATIONS[0])[:-1] + ['foreign.test/androidx.test.runner.AndroidJUnitRunner'],
        ]
        for argv in bad_commands:
            with self.subTest(argv=argv), self.assertRaises(core.TargetRefused):
                c.validate_operation(dict(argv=argv, stdin=None), value)

    def test_session_and_proof_cannot_borrow_sdk16_tags_or_another_descriptor(self):
        value = f.admission(); session = f.session(value)
        self.assertEqual(c.validate_session(session, value), session)
        proof = f.proof(session)
        c.validate_proof(proof, session, proof['context'])
        for mutation in ('session_protocol', 'proof_protocol', 'proof_file', 'descriptor'):
            with self.subTest(mutation=mutation):
                s, p = copy.deepcopy(session), copy.deepcopy(proof)
                if mutation == 'session_protocol': s['protocol'] = 'sdk-knowledge-ui-v1'
                elif mutation == 'proof_protocol': p['protocol'] = 'knowledge-ui-socket-proof-v1'
                elif mutation == 'proof_file': p['session']['path'] = str(PureWindowsPath(s['root']) / 'sdk-session-v16.json')
                else: s['descriptor']['run_id'] = 'f' * 32
                with self.assertRaises(core.TargetRefused):
                    c.validate_session(s, value)
                    c.validate_proof(p, s, p['context'])

    def test_concrete_owner_runtime_and_client_subclasses_refuse_before_io(self):
        class ForeignOwner(owner.LiveOwnedDiagnosticUiTarget): pass
        class ForeignRuntime(owner._DiagnosticUiTargetRuntime): pass
        class ForeignCapture(client.OwnedDiagnosticUiSdkCapture): pass
        with patch.object(Path, 'open', side_effect=AssertionError('unexpected file')):
            with self.assertRaisesRegex(owner.OwnerRefused, '^owner_type$'): ForeignOwner({}, {})
            with self.assertRaisesRegex(owner.OwnerRefused, '^owner_type$'): ForeignRuntime({}, {}, Path('D:/Unused'))
            with self.assertRaises(client.ClientRefused): ForeignCapture(Path('D:/Unused'), 10, object())
        with self.assertRaises(client.ClientRefused):
            client.OwnedDiagnosticUiSdkCapture(Path('D:/Unused'), 10, object())

    def test_wrapper_revalidates_before_after_and_returns_same_raw_b104_object(self):
        value = f.admission(); manifest = f.raw_manifest(value['artifacts']); before = copy.deepcopy(manifest)
        calls = []
        with patch.object(c, 'revalidate_inputs', side_effect=lambda a: calls.append(('inputs', copy.deepcopy(a)))), \
             patch.object(build.build, 'verify_frozen_product', side_effect=lambda artifacts: calls.append(('build', copy.deepcopy(artifacts))) or manifest):
            actual = build.verify_current(value)
        self.assertIs(actual, manifest)
        self.assertEqual(manifest, before)
        self.assertEqual([name for name, _ in calls], ['inputs', 'build', 'inputs'])
        self.assertEqual(calls[1][1], value['artifacts'])
        self.assertNotIn('roster', actual)

    def test_wrapper_refuses_borrowed_or_uncompiled_roster_after_verifier_return(self):
        for mutation in ('scope', 'mode', 'missing', 'extra', 'reordered', 'borrowed', 'bool_units', 'zero_units'):
            with self.subTest(mutation=mutation):
                value = f.admission(); raw = f.raw_manifest(value['artifacts'])
                if mutation == 'scope': raw['scope'] = 'knowledge-ui-build-v1'
                elif mutation == 'mode': raw['mode'] = 'caller-selected'
                elif mutation == 'missing': raw['selected_methods'].pop()
                elif mutation == 'extra': raw['selected_methods'].append(copy.deepcopy(raw['selected_methods'][0]))
                elif mutation == 'reordered': raw['selected_methods'].reverse()
                elif mutation == 'borrowed': raw['selected_methods'][0]['selector'] = 'knowledge_1'
                elif mutation == 'bool_units': raw['selected_methods'][0]['instruction_units'] = True
                else: raw['selected_methods'][0]['instruction_units'] = 0
                with patch.object(c, 'revalidate_inputs'), patch.object(build.build, 'verify_frozen_product', return_value=raw):
                    with self.assertRaises(core.TargetRefused): build.verify_current(value)

    def test_late_revalidation_failure_or_build_refusal_never_returns_metadata(self):
        value = f.admission(); raw = f.raw_manifest(value['artifacts'])
        with patch.object(c, 'revalidate_inputs', side_effect=[None, core.TargetRefused('changed')]), \
             patch.object(build.build, 'verify_frozen_product', return_value=raw):
            with self.assertRaises(core.TargetRefused): build.verify_current(value)
        with patch.object(c, 'revalidate_inputs') as check, \
             patch.object(build.build, 'verify_frozen_product', side_effect=build.BuildRefused('changed')):
            with self.assertRaises(build.BuildRefused): build.verify_current(value)
        self.assertEqual(check.call_count, 1)

    def test_projection_uses_exact_raw_shape_fixed_packages_and_fixed_signer(self):
        raw = f.raw_manifest(); original = copy.deepcopy(raw)
        projected = controller._projection(raw)
        self.assertEqual(raw, original)
        self.assertEqual(projected['roster'], [list(row) for row in f.INSTRUMENTATIONS])
        for role, package in (('product_apk', f.APP), ('test_apk', f.TEST)):
            self.assertEqual(projected['apks'][role], dict(binding=raw['apks'][role], package=package, certificate_sha256=f.CERTIFICATE))
        projected['apks']['product_apk']['binding']['sha256'] = '0' * 64
        self.assertEqual(raw, original)
        for mutation in ('legacy', 'authority', 'extra_role', 'true_version', 'extra_key'):
            with self.subTest(mutation=mutation):
                bad = copy.deepcopy(raw)
                if mutation == 'legacy': bad = copy.deepcopy(projected)
                elif mutation == 'authority': bad['facts']['run_authority'] = True
                elif mutation == 'extra_role': bad['apks']['model'] = f.legacy.pin('D:/Synthetic/model')
                elif mutation == 'true_version': bad['version'] = True
                else: bad['certificate_sha256'] = '0' * 64
                with self.assertRaises(controller.env.EnvironmentRefused): controller._projection(bad)

    def test_checker_guards_wrap_shared_revalidation_without_native_observation(self):
        calls = []
        with patch.object(build, 'revalidate_checker', side_effect=lambda: calls.append('checker')), \
             patch.object(core._Contract, 'revalidate_inputs', side_effect=lambda a: calls.append('shared') or a):
            value = f.admission()
            self.assertEqual(c.revalidate_inputs(value), value)
        self.assertEqual(calls, ['checker', 'shared', 'checker'])

    @unittest.skipUnless(os.name == 'nt', 'fixed source path is a physical D Windows checkout')
    def test_cached_decoder_cannot_retarget_its_transitive_audit_module(self):
        from benchmarks import archive_ui_build as reader
        root = Path(build.__file__).parents[1]
        good = SimpleNamespace(__file__=str(root / 'scripts/audit_physical_model_apk.py'),
                               base=SimpleNamespace(__file__=str(root / 'scripts/audit_apk.py')))
        with patch.object(reader, '_bound') as checks, \
             patch.dict(build.sys.modules, {'scripts.audit_physical_model_apk': good}):
            build.revalidate_checker()
            self.assertEqual(checks.call_count, 2)
            for call, (relative, size, sha) in zip(checks.call_args_list, build.CHECKERS):
                self.assertEqual(call.args, (dict(path=str(root / relative), bytes=size, sha256=sha),))
            good.base.__file__ = str(root / 'scripts/foreign_audit.py')
            with self.assertRaises(c.TargetRefused): build.revalidate_checker()
