"""Original SDK17 consumed-byte, prepared-state and input-publication oracles.

Only tiny retained physical-D fixtures use real environment/storage validators.
SDK, build, installed-state and admission observations are explicit fake ports;
these tests do not qualify an APK, device, private server or actual admission.
Copyright 2026 LocalLore contributors. SPDX-License-Identifier: Apache-2.0
"""
import copy
import hashlib
import io
import json
import os
from pathlib import Path, PureWindowsPath
from types import SimpleNamespace
import unittest
from unittest.mock import Mock,patch

from scripts import diagnostic_ui_fresh_contract as rules
from scripts import run_diagnostic_ui_fresh as bridge
from benchmarks import receipt_avd_environment as env
from benchmarks import receipt_avd_storage as storage
from benchmarks import prepare_recovery_contract as history
from scripts.tests.diagnostic_ui_fresh_input_fixture import FreshGraph

REFUSED=(rules.FreshRunRefused,env.EnvironmentRefused,storage.StorageRefused)


class ObservedBytes(io.BytesIO):
    def __init__(self,raw):
        super().__init__(raw);self.requests=[]
    def read(self,size=-1):
        self.requests.append(size)
        if size<0:raise AssertionError('unbounded artifact read')
        return super().read(size)


class DiagnosticFreshConsumedBytesTests(unittest.TestCase):
    def test_read_decodes_only_exact_pinned_bytes_with_a_bounded_consumption(self):
        raw=b'{"value":"A"}'
        pin=dict(path=str(PureWindowsPath('D:/Synthetic/pinned.json')),bytes=len(raw),sha256=hashlib.sha256(raw).hexdigest())
        decoder=Mock(side_effect=env.decode_json);check=Mock()
        api=SimpleNamespace(env=SimpleNamespace(check_binding=check,decode_json=decoder))
        stream=ObservedBytes(raw)
        with patch.object(bridge,'_parts',return_value=(rules,api)),patch.object(Path,'open',return_value=stream) as opened:
            value=bridge.read(pin,Path(pin['path']))
        self.assertEqual(value,{'value':'A'})
        self.assertEqual(stream.requests,[len(raw)+1]);opened.assert_called_once_with('rb')
        self.assertEqual(check.call_count,2);decoder.assert_called_once_with(raw)

    def test_same_length_wrong_consumed_bytes_refuse_even_when_path_checks_report_unchanged(self):
        expected=b'{"value":"A"}';observed=b'{"value":"B"}'
        self.assertEqual(len(expected),len(observed))
        pin=dict(path=str(PureWindowsPath('D:/Synthetic/pinned.json')),bytes=len(expected),sha256=hashlib.sha256(expected).hexdigest())
        api=SimpleNamespace(env=SimpleNamespace(check_binding=Mock(),decode_json=Mock(side_effect=env.decode_json)))
        stream=ObservedBytes(observed)
        with patch.object(bridge,'_parts',return_value=(rules,api)),patch.object(Path,'open',return_value=stream):
            with self.assertRaises(rules.FreshRunRefused):bridge.read(pin)
        api.env.decode_json.assert_not_called();self.assertEqual(stream.requests,[len(expected)+1])
        self.assertGreaterEqual(api.env.check_binding.call_count,1)

    def test_grown_or_short_consumption_refuses_before_decode_and_invalid_pin_before_open(self):
        raw=b'{"value":1}';pin=dict(path=str(PureWindowsPath('D:/Synthetic/pinned.json')),bytes=len(raw),sha256=hashlib.sha256(raw).hexdigest())
        for observed in (raw+b' '*50000,raw[:-1]):
            with self.subTest(length=len(observed)):
                api=SimpleNamespace(env=SimpleNamespace(check_binding=Mock(),decode_json=Mock()))
                stream=ObservedBytes(observed)
                with patch.object(bridge,'_parts',return_value=(rules,api)),patch.object(Path,'open',return_value=stream):
                    with self.assertRaises(rules.FreshRunRefused):bridge.read(pin)
                api.env.decode_json.assert_not_called();self.assertEqual(stream.requests,[len(raw)+1])
        api=SimpleNamespace(env=SimpleNamespace(check_binding=Mock(),decode_json=Mock()))
        bad=copy.deepcopy(pin);bad['bytes']=True
        with patch.object(bridge,'_parts',return_value=(rules,api)),patch.object(Path,'open') as opened:
            with self.assertRaises(rules.FreshRunRefused):bridge.read(bad)
        opened.assert_not_called();api.env.check_binding.assert_not_called()


@unittest.skipUnless(os.name=='nt','real shared validation over retained tiny physical-D files')
class DiagnosticFreshInputTests(unittest.TestCase):
    def test_historical_blocked_preview_is_not_admission_and_fresh_prepared_validates_without_mutation(self):
        with FreshGraph() as g:
            before=(g.registry/'ledger-v1.json').read_bytes()
            a,h,installed=bridge.frozen_inputs(g.authority_pin)
            self.assertFalse(env.read_json(h['capacity_preview']['path'])['would_fit'])
            self.assertFalse(h['execution_authorized']);self.assertFalse(h['model_material'])
            self.assertEqual(a,g.authority);self.assertEqual(installed,g.installed)
            self.assertEqual(g.prepared(),env.binding(g.registry/'ledger-v1.json'))
            self.assertEqual((g.registry/'ledger-v1.json').read_bytes(),before)
            self.assertIsNone(g.entry['recovery'])
            self.assertFalse((g.guest/g.contract.BOOT_CLAIM_FILE).exists())
            g.api.env.prepare.assert_not_called();g.api.activation.execute.assert_not_called()
            g.api.env.plan_run.assert_not_called()

    def test_exact_source_closure_and_live_byte_drift_refuse_before_any_run_planning(self):
        for damage in ('same_count_hash','missing_recovery','foreign_parent','live_bytes'):
            with self.subTest(damage=damage),FreshGraph() as g:
                if damage=='live_bytes':Path(g.sources[0]['path']).write_bytes(b'changed source')
                else:
                    current=copy.deepcopy(g.sources)
                    if damage=='same_count_hash':current[0]['sha256']='0'*64
                    elif damage=='missing_recovery':current=[p for p in current if PureWindowsPath(p['path']).name!='prepare_recovery_contract.py']
                    else:current[0]['path']=str(g.base/'borrowed-source.py')
                    g.contract.source_bindings.side_effect=None;g.contract.source_bindings.return_value=current
                with self.assertRaises(REFUSED):g.create()
                g.api.env.plan_run.assert_not_called();g.api.activation.execute.assert_not_called()
                self.assertFalse(rules.INPUT.exists())

    def test_actual_python_executable_or_runtime_dll_mismatch_refuses_before_installation_and_run(self):
        for role in ('executable','runtime_dll'):
            with self.subTest(role=role),FreshGraph() as g:
                wrong=copy.deepcopy(g.python)
                wrong[role]=dict(path=str(g.base/'different-runtime'),bytes=19,sha256='0'*64)
                g.api.probe._python_bindings.return_value=wrong
                with self.assertRaisesRegex(rules.FreshRunRefused,'python'):g.create()
                g.api.env.verify_installation.assert_not_called();g.api.env.plan_run.assert_not_called()
                g.api.activation.execute.assert_not_called();self.assertFalse(rules.INPUT.exists())

    def test_prepare_proposal_is_current_and_fixed_profile_before_prepared_or_planning(self):
        for damage in ('changed_bytes','wrong_root','boolean_cores','calls_already_allowed'):
            with self.subTest(damage=damage),FreshGraph() as g:
                if damage=='changed_bytes':
                    g.prepare_path.write_bytes(g.prepare_path.read_bytes()+b' ')
                    with self.assertRaises(REFUSED):g.create()
                else:
                    proposal=copy.deepcopy(g.proposal)
                    if damage=='wrong_root':proposal['paths']['root']=str(g.base/'borrowed-root')
                    elif damage=='boolean_cores':proposal['cores']=True
                    else:proposal['allow_environment_calls']=True;proposal['root_go_pending']=False
                    prepare_pin=g.write(g.prepare_path,proposal)
                    g.handoff['prepare_proposal']=prepare_pin
                    with patch.object(rules,'PREPARE_PIN',prepare_pin):
                        handoff_pin=g.write(g.handoff_path,g.handoff)
                        with patch.object(rules,'HANDOFF',handoff_pin):
                            g.authority['handoff']=copy.deepcopy(handoff_pin)
                            g.authority_pin=g.write(rules.AUTHORITY,g.authority)
                            with self.assertRaises(REFUSED):g.create()
                g.api.env.plan_run.assert_not_called();g.api.activation.execute.assert_not_called()
                self.assertFalse(rules.INPUT.exists())

    def test_raw_build_copy_and_exact_six_selected_triples_must_join_before_planning(self):
        for damage in ('copy_mismatch','five','seven','reordered','class','method','selector'):
            with self.subTest(damage=damage),FreshGraph() as g:
                changed=copy.deepcopy(g.manifest)
                if damage=='copy_mismatch':changed['scope']='other-saved-build'
                elif damage=='five':changed['selected_methods'].pop()
                elif damage=='seven':changed['selected_methods'].append(copy.deepcopy(changed['selected_methods'][0]))
                elif damage=='reordered':changed['selected_methods'].reverse()
                else:changed['selected_methods'][0][damage]='borrowed'
                if damage=='copy_mismatch':
                    g.api.build.verify_frozen_product.side_effect=lambda artifacts:changed
                    with self.assertRaises(REFUSED):g.create()
                else:
                    g.manifest=changed;build_pin=g.write(g.build_path,changed)
                    g.handoff['artifacts']['build']=build_pin
                    with patch.object(rules,'BUILD_PIN',build_pin):
                        handoff_pin=g.write(g.handoff_path,g.handoff)
                        with patch.object(rules,'HANDOFF',handoff_pin):
                            g.authority['handoff']=copy.deepcopy(handoff_pin)
                            g.authority_pin=g.write(rules.AUTHORITY,g.authority)
                            with self.assertRaises(REFUSED):g.create()
                g.api.env.plan_run.assert_not_called();g.api.activation.execute.assert_not_called()
                self.assertFalse(rules.INPUT.exists())

    def test_real_prepared_validation_rejects_cleanup_unknown_receipt_disk_config_or_boot_reuse(self):
        for damage in ('cleanup_false','cleanup_one','proposal_sha','config','disk','userdata','boot_claim'):
            with self.subTest(damage=damage),FreshGraph() as g:
                if damage in ('cleanup_false','cleanup_one','proposal_sha'):
                    if damage=='proposal_sha':g.prepare_result['proposal_sha256']='0'*64
                    else:g.prepare_result['child_cleanup_complete']=False if damage=='cleanup_false' else 1
                    g.write(g.guest/'prepare-result-v1.json',g.prepare_result)
                elif damage=='config':Path(g.prepared_record['immutable'][0]['path']).write_bytes(b'changed configuration')
                elif damage=='disk':Path(g.prepared_record['initial_sdcard']['path']).write_bytes(b'changed synthetic disk')
                elif damage=='userdata':(Path(g.proposal['paths']['content'])/'userdata-qemu.img').write_bytes(b'prior synthetic boot')
                else:(g.guest/g.contract.BOOT_CLAIM_FILE).write_bytes(b'prior synthetic boot claim')
                with self.assertRaises(REFUSED):g.create()
                g.api.env.plan_run.assert_not_called();g.api.activation.execute.assert_not_called()
                self.assertFalse(rules.INPUT.exists())

    def test_real_ledger_validation_requires_fresh_v2_exact_root_sha_charge_and_unlinked_history_absence(self):
        for damage in ('v1','root','state','sha','boolean_charge','undercharge','history','retirement','unlinked_intent'):
            with self.subTest(damage=damage),FreshGraph() as g:
                if damage=='v1':g.ledger['version']=1;del g.entry['recovery']
                elif damage=='root':g.entry['root']=str(g.base/'borrowed-root')
                elif damage=='state':g.entry['state']='preparing'
                elif damage=='sha':g.entry['proposal_sha256']='0'*64
                elif damage=='boolean_charge':g.entry['reserved_bytes']=True
                elif damage=='undercharge':g.entry['reserved_bytes']=40*1024**3-1
                elif damage=='history':g.entry['recovery']={}
                elif damage=='retirement':g.entry['retirement']={}
                else:history.claim_path(g.registry,g.guest).write_bytes(b'unlinked synthetic intent')
                g.write_ledger()
                with self.assertRaises(REFUSED):g.create()
                g.api.env.plan_run.assert_not_called();g.api.activation.execute.assert_not_called()
                self.assertFalse(rules.INPUT.exists())

    def test_input_publication_joins_real_public_plan_authorization_and_prepared_receipts(self):
        with FreshGraph() as g:
            before=(g.registry/'ledger-v1.json').read_bytes()
            value=g.create()
            self.assertEqual(set(value),{'authority','prepare_authorization','ledger','run_proposal','run_authorization','admission','input'})
            for bound in value.values():env.check_binding(bound)
            run=env.read_json(value['run_proposal']['path'])
            env.validate_proposal(run,'run');env.verify_prepared(run,initial=True)
            self.assertEqual((run['phase'],run['memory_mib'],run['cores'],run['max_seconds']),('run',8192,4,1800))
            self.assertEqual(run['prepare_proposal'],g.prepare_pin)
            self.assertEqual(run['prepared'],env.binding(g.guest/'prepared-v1.json'))
            self.assertEqual(run['prepare_result'],env.binding(g.guest/'prepare-result-v1.json'))
            self.assertEqual(env.read_json(value['run_authorization']['path']),dict(version=1,phase='run',proposal_sha256=value['run_proposal']['sha256'],allow_environment_calls=True,root_go_pending=False))
            admission=env.read_json(value['admission']['path'])
            self.assertEqual(admission['protocol'],'owned-emulator-diagnostic-ui-v1')
            self.assertEqual(admission['guest']['proposal'],value['run_proposal'])
            self.assertEqual(admission['guest']['authorization'],value['run_authorization'])
            self.assertEqual((admission['guest']['memory_mib'],admission['guest']['cores'],admission['guest']['api'],admission['guest']['max_seconds']),(8192,4,35,1800))
            self.assertEqual(admission['sources'],g.sources);self.assertEqual(admission['artifacts'],g.handoff['artifacts'])
            self.assertEqual(env.read_json(value['input']['path']),dict(version=1,scope='diagnostic-ui-run-input-v1',admission=value['admission'],helper=env.binding(g.api.activation.HELPER)))
            self.assertLess(g.events.index('plan_run'),g.events.index('authorize'))
            self.assertLess(g.events.index('authorize'),g.events.index('admission'))
            self.assertLess(g.events.index('admission'),g.events.index('revalidate'))
            self.assertLess(g.events.index('revalidate'),g.events.index('build'))
            self.assertEqual((g.registry/'ledger-v1.json').read_bytes(),before)
            g.api.activation.execute.assert_not_called();g.api.env.prepare.assert_not_called()
            with self.assertRaises(REFUSED):g.create()
            self.assertEqual((g.registry/'ledger-v1.json').read_bytes(),before)

    def test_late_valid_ledger_drift_keeps_partial_admission_but_never_publishes_run_input(self):
        with FreshGraph() as g:
            old=g.api.profile_build.verify_current.side_effect
            def drift(admission):
                old(admission)
                # Still a valid V2 ledger, same guest/count/reservation; a
                # different valid state must not borrow the earlier ledger pin.
                g.entry['state']='retained';g.write_ledger()
            g.api.profile_build.verify_current.side_effect=drift
            with self.assertRaises(REFUSED):g.create()
            self.assertTrue(rules.RUN_PROPOSAL.exists());self.assertTrue(rules.ADMISSION.exists())
            self.assertFalse(rules.INPUT.exists());self.assertEqual(g.entry['state'],'retained')
            g.api.activation.execute.assert_not_called();g.api.env.prepare.assert_not_called()
            retained=rules.ADMISSION.read_bytes()
            with self.assertRaises(REFUSED):g.create()
            self.assertEqual(rules.ADMISSION.read_bytes(),retained)

    def test_initial_current_ledger_and_capacity_are_independent_of_historical_preview(self):
        for damage in ('ledger_bytes','capacity_blocked','capacity_grants','capacity_wrong_pin'):
            with self.subTest(damage=damage),FreshGraph() as g:
                original=(g.registry/'ledger-v1.json').read_bytes()
                capacity=dict(would_fit=True,admission_granted=False,ledger=copy.deepcopy(g.authority['ledger']))
                if damage=='ledger_bytes':(g.registry/'ledger-v1.json').write_bytes(original+b' ')
                elif damage=='capacity_blocked':capacity['would_fit']=False
                elif damage=='capacity_grants':capacity['admission_granted']=True
                else:capacity['ledger']['sha256']='0'*64
                # This test isolates current-ledger/capacity admission joins;
                # unused-root safety has its own real path tests below.
                with patch.object(bridge,'_unused'),patch.object(Path,'cwd',return_value=g.source), \
                     patch.dict(os.environ,{k:'D:/Dev/_Temp' for k in ('TEMP','TMP','TMPDIR')}), \
                     patch.object(storage,'preview_prepare',return_value=capacity):
                    with self.assertRaises(REFUSED):bridge._initial(g.authority_pin)
                g.api.env.prepare.assert_not_called();g.api.env.plan_run.assert_not_called()
                self.assertFalse(rules.INPUT.exists())

    def test_unused_path_gate_refuses_existing_any_owned_namespace_without_deleting_evidence(self):
        for role in ('LIVE','GUEST','RUNTIME','CONTROLS'):
            with self.subTest(role=role),FreshGraph() as g:
                # Other names become distinct absent synthetic candidates;
                # only this actual existing target is the refusal trigger.
                actual=getattr(rules,role)
                if not actual.exists():actual.mkdir()
                marker=actual/'retained-evidence';marker.write_bytes(b'KEEP')
                with patch.multiple(rules,**{name:g.base/('unused-'+name.lower()) for name in ('LIVE','GUEST','RUNTIME','CONTROLS') if name!=role}):
                    with self.assertRaises(REFUSED):bridge._unused()
                self.assertEqual(marker.read_bytes(),b'KEEP')
                g.api.env.prepare.assert_not_called();g.api.activation.execute.assert_not_called()

    def test_existing_and_failed_publications_are_spent_without_overwrite_or_activation(self):
        for role in ('RUN_PROPOSAL','RUN_AUTHORIZATION','RUNTIME','CONTROLS'):
            with self.subTest(role=role),FreshGraph() as g:
                target=getattr(rules,role)
                if role in ('RUNTIME','CONTROLS'):
                    target.mkdir();target=target/'retained-failure'
                target.write_bytes(b'prior failed operation')
                with self.assertRaises(REFUSED):g.create()
                self.assertEqual(target.read_bytes(),b'prior failed operation')
                g.api.env.plan_run.assert_not_called();g.api.activation.execute.assert_not_called()
                self.assertFalse(rules.INPUT.exists())
        with FreshGraph() as g:
            original=bridge.save
            def fail_final(path,value):
                if path==rules.INPUT:raise OSError('SYNTHETIC publication failure')
                return original(path,value)
            with patch.object(bridge,'save',side_effect=fail_final):
                with self.assertRaises(OSError):g.create()
            self.assertTrue(rules.ADMISSION.exists());self.assertFalse(rules.INPUT.exists())
            preserved=rules.ADMISSION.read_bytes()
            with self.assertRaises(REFUSED):g.create()
            self.assertEqual(rules.ADMISSION.read_bytes(),preserved)
            g.api.activation.execute.assert_not_called()

    def test_unselected_activation_or_stale_authority_refuses_without_input(self):
        for damage in ('activation','authority','handoff'):
            with self.subTest(damage=damage),FreshGraph() as g:
                if damage=='activation':
                    helper=g.base/'borrowed-activation.py';helper.write_bytes(b'SYNTHETIC unselected helper')
                    g.api.activation.HELPER=helper
                elif damage=='authority':rules.AUTHORITY.write_bytes(rules.AUTHORITY.read_bytes()+b' ')
                else:g.handoff_path.write_bytes(g.handoff_path.read_bytes()+b' ')
                with self.assertRaises(REFUSED):g.create()
                self.assertFalse(rules.INPUT.exists());g.api.activation.execute.assert_not_called()
                if damage!='activation':g.api.env.plan_run.assert_not_called()
