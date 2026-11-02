"""Original B94 host adversaries; synthetic metadata never grants real action.

Fixtures are retained on D:. Native/SDK/guest ports are explicit fakes; Root
owns execution. Copyright 2026 LocalLore contributors. SPDX-License-Identifier: Apache-2.0
"""
from contextlib import ExitStack
import copy
import ctypes
import hashlib
import importlib
import json
import math
import os
from pathlib import Path, PureWindowsPath
import socket
import subprocess
import sys
from types import SimpleNamespace
import unittest
from unittest.mock import Mock, patch

from scripts import knowledge_ui_fresh_contract as rules
from scripts import run_knowledge_ui_fresh as bridge
from benchmarks import receipt_avd_environment as env
from benchmarks import receipt_avd_storage as storage
from benchmarks import prepare_recovery_contract as history
from scripts.tests.knowledge_ui_fresh_test_fixture import FreshGraph


HOME = Path('D:/Dev/Experiments/LocalLore/2026-11-02-knowledge-fresh-bridge-v1/test-agent-v1/fixtures')
REFUSED=(rules.FreshRunRefused,env.EnvironmentRefused,storage.StorageRefused)


def synthetic_pin(path, digest='7' * 64):
    return dict(path=str(PureWindowsPath(path)), bytes=17, sha256=digest)


def authority():
    return dict(version=1, scope='sdk16-fresh-prepare-and-one-knowledge-ui-run-v1',
        source_head=rules.SOURCE_HEAD, operator_head='a' * 40,
        proposal=synthetic_pin(rules.PROPOSAL), operator=synthetic_pin(rules.OPERATOR),
        contract=synthetic_pin(rules.CONTRACT), handoff=copy.deepcopy(rules.HANDOFF),
        ledger=synthetic_pin(rules.REGISTRY/'ledger-v1.json'),
        allow_sdk_prepare=True, allow_one_boot=True, allow_model=False,
        allow_retirement=False, approval_reference='SYNTHETIC TEST ONLY; NOT HUMAN AUTHORITY',
        max_operation_seconds=2400)


def attempt(value, pin):
    return dict(version=1, scope='sdk16-fresh-operation-attempt-v1', authority=copy.deepcopy(pin),
        handoff=copy.deepcopy(value['handoff']), operator=copy.deepcopy(value['operator']),
        contract=copy.deepcopy(value['contract']), no_retry=True)


def no_io(stack):
    for name in ('open', 'resolve', 'stat', 'lstat', 'mkdir', 'unlink', 'rename'):
        stack.enter_context(patch.object(Path, name, side_effect=AssertionError('unexpected filesystem operation')))
    stack.enter_context(patch.object(ctypes, 'WinDLL', create=True,
        side_effect=AssertionError('unexpected native operation')))
    stack.enter_context(patch.object(subprocess, 'Popen', side_effect=AssertionError('unexpected process')))
    stack.enter_context(patch.object(subprocess, 'run', side_effect=AssertionError('unexpected process')))
    stack.enter_context(patch.object(socket, 'socket', side_effect=AssertionError('unexpected socket')))


class FreshContractTests(unittest.TestCase):
    def test_module_bodies_and_structural_positive_require_no_io(self):
        # Obtain source before fencing, then execute module bodies without using
        # a loader's unavoidable source read as an alleged product import effect.
        bodies = [(Path(module.__file__).read_bytes(), module.__name__)
                  for module in (rules, bridge)]
        value = authority(); pin = synthetic_pin(rules.AUTHORITY)
        with ExitStack() as stack:
            no_io(stack)
            for raw, name in bodies:
                namespace = dict(__name__=name+'__original_import_oracle', __file__='D:/Synthetic/module.py')
                exec(compile(raw, namespace['__file__'], 'exec'), namespace)
            accepted = rules.validate_authority(value)
            accepted_attempt = rules.validate_attempt(attempt(value, pin), pin, value)
        self.assertEqual(accepted, value)
        self.assertIsNot(accepted, value)
        self.assertEqual(accepted_attempt['authority'], pin)
        accepted['operator']['sha256'] = '0' * 64
        self.assertEqual(value['operator']['sha256'], '7' * 64)

    def test_authority_is_closed_strict_and_cannot_expand_scope_or_borrow_paths(self):
        cases = []
        for key, values in (
            ('version', (True, '1', 2)), ('source_head', ('0' * 40,)),
            ('operator_head', ('A' * 40, 'a' * 39)),
            ('scope', ('sdk15-recovered-library-ui-run-v1',)),
            ('allow_sdk_prepare', (1, False)), ('allow_one_boot', (1, False)),
            ('allow_model', (0, True)), ('allow_retirement', (0, True)),
            ('max_operation_seconds', (True, 2401, 2400.0)),
            ('approval_reference', ('', 'line\nbreak', 'x' * 257))):
            for v in values:
                bad=authority();bad[key]=v;cases.append((key, bad))
        for role in ('proposal', 'operator', 'contract', 'handoff', 'ledger'):
            bad=authority();bad[role]['path']=str(PureWindowsPath('D:/Synthetic/borrowed.json'));cases.append((role,bad))
        bad=authority();bad['unknown']=False;cases.append(('extra',bad))
        bad=authority();del bad['allow_retirement'];cases.append(('missing',bad))
        bad=authority();bad['handoff']['sha256']='9'*64;cases.append(('handoff-byte-pin',bad))
        for label,bad in cases:
            with self.subTest(case=label), ExitStack() as stack:
                no_io(stack)
                with self.assertRaises(rules.FreshRunRefused):rules.validate_authority(bad)

    def test_binding_rejects_boolean_size_noncanonical_or_non_d_paths_and_extra_fields(self):
        cases=[]
        for key,values in (('bytes',(True,0,-1,2*1024**2+1)),
                           ('sha256',('A'*64,'0'*63)),
                           ('path',('C:\\Synthetic\\file.json','relative.json','D:/Synthetic/file.json'))):
            for value in values:
                bad=synthetic_pin('D:/Synthetic/file.json');bad[key]=value;cases.append((key,bad))
        bad=synthetic_pin('D:/Synthetic/file.json');bad['extra']=None;cases.append(('extra',bad))
        for label,bad in cases:
            with self.subTest(case=label), self.assertRaises(rules.FreshRunRefused):rules.binding(bad)

    def test_attempt_is_bound_to_exact_authority_helper_handoff_and_no_retry_boolean(self):
        value=authority();pin=synthetic_pin(rules.AUTHORITY)
        for role in ('authority','operator','contract','handoff'):
            bad=attempt(value,pin);bad[role]['sha256']='0'*64
            with self.subTest(role=role),self.assertRaises(rules.FreshRunRefused):
                rules.validate_attempt(bad,pin,value)
        for key,value2 in (('no_retry',1),('no_retry',False),('version',True),('unknown',False)):
            bad=attempt(value,pin);bad[key]=value2
            with self.subTest(field=key,value=value2),self.assertRaises(rules.FreshRunRefused):
                rules.validate_attempt(bad,pin,value)
        wrong_pin=synthetic_pin('D:/Synthetic/copied-authority.json')
        with self.assertRaises(rules.FreshRunRefused):rules.validate_attempt(attempt(value,wrong_pin),wrong_pin,value)


@unittest.skipUnless(os.name=='nt','real shared validators over tiny retained physical D: files')
class FreshBridgeTests(unittest.TestCase):
    def test_fresh_prepared_without_recovery_history_qualifies_with_real_shared_validators(self):
        with FreshGraph() as g:
            original=(g.registry/'ledger-v1.json').read_bytes()
            storage._validate(g.ledger,g.registry)
            self.assertIsNone(g.entry['recovery'])
            pin=g.prepared()
            env.check_binding(pin)
            self.assertEqual(pin,env.binding(g.registry/'ledger-v1.json'))
            self.assertEqual((g.registry/'ledger-v1.json').read_bytes(),original)
            self.assertFalse((g.guest/g.api.contract.BOOT_CLAIM_FILE).exists())
            g.api.env.prepare.assert_not_called();g.api.activation.execute.assert_not_called()

    def test_prepared_receipt_cleanup_root_immutable_disk_and_profile_cannot_be_forged(self):
        for damage in ('closure','child_cleanup','created','proposal_sha','root','profile','immutable','sdcard','userdata'):
            with self.subTest(damage=damage),FreshGraph() as g:
                if damage in ('closure','child_cleanup','created'):
                    field={'closure':'closure_verified','child_cleanup':'child_cleanup_complete','created':'prepared_created'}[damage]
                    g.prepare_result[field]=False;g.write(g.guest/'prepare-result-v1.json',g.prepare_result)
                elif damage=='proposal_sha':
                    g.prepare_result['proposal_sha256']='0'*64;g.write(g.guest/'prepare-result-v1.json',g.prepare_result)
                elif damage in ('root','profile'):
                    proposal=copy.deepcopy(g.proposal)
                    if damage=='root':proposal['paths']['root']=str(g.base/'borrowed-guest')
                    else:proposal['cores']=True
                    g.handoff['prepare_proposal']=g.write(g.prepare_path,proposal)
                    g.write(g.handoff_path,g.handoff)
                    with patch.object(rules,'HANDOFF',env.binding(g.handoff_path)):
                        # A freshly rebound handoff does not authorize altered
                        # root/profile or inherit an unrelated prepared receipt.
                        g.authority['handoff']=copy.deepcopy(rules.HANDOFF)
                        g.authority_pin=g.write(rules.AUTHORITY,g.authority)
                        with self.assertRaises(REFUSED):g.prepared()
                    continue
                elif damage=='immutable':Path(g.prepared_record['immutable'][0]['path']).write_bytes(b'changed config')
                elif damage=='sdcard':Path(g.prepared_record['initial_sdcard']['path']).write_bytes(b'changed tiny disk')
                else:(Path(g.proposal['paths']['content'])/'userdata-qemu.img').write_bytes(b'old guest boot evidence')
                with self.assertRaises(REFUSED):g.prepared()
                g.api.env.plan_run.assert_not_called();g.api.activation.execute.assert_not_called()

    def test_prepared_ledger_requires_exact_root_v2_state_sha_charge_and_no_recovery_or_retirement(self):
        changes=(lambda g:g.ledger.update(version=1),lambda g:g.entry.update(root=str(g.base/'borrowed-root')),
            lambda g:g.entry.update(state='retained'),lambda g:g.entry.update(proposal_sha256='0'*64),
            lambda g:g.entry.update(reserved_bytes=True),lambda g:g.entry.update(reserved_bytes=40*1024**3-1),
            lambda g:g.entry.update(recovery={}),lambda g:g.entry.update(retirement={}))
        for index,change in enumerate(changes):
            with self.subTest(change=index),FreshGraph() as g:
                change(g);g.write_ledger()
                with self.assertRaises(REFUSED):g.prepared()
                g.api.env.plan_run.assert_not_called();g.api.activation.execute.assert_not_called()
        with FreshGraph() as g:
            claim=history.claim_path(g.registry,g.guest);claim.write_bytes(b'unlinked synthetic intent')
            with self.assertRaises(storage.StorageRefused):g.prepared()

    def test_inputs_qualify_prepare_before_planning_then_admission_before_activation_input(self):
        with FreshGraph() as g:
            before=(g.registry/'ledger-v1.json').read_bytes()
            value=g.create()
            self.assertEqual(set(value),{'authority','prepare_authorization','ledger','run_proposal','run_authorization','admission','input'})
            for pin in value.values():env.check_binding(pin)
            run=env.read_json(value['run_proposal']['path'])
            self.assertEqual((run['phase'],run['memory_mib'],run['cores'],run['max_seconds']),('run',8192,4,1800))
            self.assertEqual(env.read_json(value['run_authorization']['path']),dict(version=1,phase='run',proposal_sha256=value['run_proposal']['sha256'],allow_environment_calls=True,root_go_pending=False))
            admission=env.read_json(value['admission']['path'])
            self.assertEqual((admission['protocol'],admission['guest']['root'],admission['guest']['proposal']),('owned-emulator-knowledge-ui-v1',str(g.guest),value['run_proposal']))
            self.assertEqual((admission['guest']['memory_mib'],admission['guest']['cores'],admission['guest']['api']),(8192,4,35))
            self.assertEqual(env.read_json(value['input']['path']),dict(version=1,scope='knowledge-ui-run-input-v1',admission=value['admission'],helper=env.binding(g.api.activation.HELPER)))
            self.assertLess(g.events.index('plan_run'),g.events.index('authorize'))
            self.assertLess(g.events.index('authorize'),g.events.index('admission'))
            self.assertLess(g.events.index('admission'),g.events.index('revalidate'))
            self.assertLess(g.events.index('revalidate'),g.events.index('build'))
            self.assertEqual((g.registry/'ledger-v1.json').read_bytes(),before)
            g.api.activation.execute.assert_not_called()

    def test_stale_authority_source_handoff_and_late_ledger_or_activation_source_refuse(self):
        for damage in ('authority','source','handoff','ledger_after_admission','activation_source'):
            with self.subTest(damage=damage),FreshGraph() as g:
                if damage=='authority':rules.AUTHORITY.write_bytes(rules.AUTHORITY.read_bytes()+b' ')
                elif damage=='source':Path(g.sources[0]['path']).write_bytes(b'changed source')
                elif damage=='handoff':g.handoff_path.write_bytes(g.handoff_path.read_bytes()+b' ')
                elif damage=='activation_source':
                    p=g.base/'unselected-activation.py';p.write_bytes(b'SYNTHETIC borrowed helper');g.api.activation.HELPER=p
                else:
                    original=g.api.profile_build.verify_current.side_effect
                    def drift(admission):
                        original(admission);g.ledger['budget_bytes']-=1;g.write_ledger()
                    g.api.profile_build.verify_current.side_effect=drift
                with self.assertRaises(REFUSED):g.create()
                self.assertFalse(rules.INPUT.exists());g.api.activation.execute.assert_not_called()
                if damage in ('authority','source','handoff'):g.api.env.plan_run.assert_not_called()

    def test_existing_and_partial_publication_are_retained_spent_and_never_retried(self):
        with FreshGraph() as g:
            rules.RUN_PROPOSAL.write_bytes(b'prior failed proposal evidence')
            with self.assertRaises(REFUSED):g.create()
            self.assertEqual(rules.RUN_PROPOSAL.read_bytes(),b'prior failed proposal evidence')
            g.api.env.plan_run.assert_not_called();self.assertFalse(rules.INPUT.exists())
        with FreshGraph() as g:
            real_prepared=bridge.prepared;calls=[]
            def fail_second(*args):
                calls.append(1)
                if len(calls)==2:raise rules.FreshRunRefused('synthetic_late_prepared_failure')
                return real_prepared(*args)
            with patch.object(bridge,'prepared',side_effect=fail_second):
                with self.assertRaises(REFUSED):g.create()
            self.assertTrue(rules.ADMISSION.is_file());self.assertFalse(rules.INPUT.exists())
            kept={p:p.read_bytes() for p in (rules.RUN_PROPOSAL,rules.RUN_AUTHORIZATION,rules.ADMISSION)}
            with self.assertRaises(REFUSED):g.create()
            self.assertEqual({p:p.read_bytes() for p in kept},kept)
            self.assertEqual(g.api.env.plan_run.call_count,1);g.api.activation.execute.assert_not_called()

    def test_stage_activation_failure_cancellation_and_budget_failure_remain_failed_without_retry(self):
        for fault in ('failed','cancelled','budget'):
            with self.subTest(fault=fault),FreshGraph() as g:
                attempt_pin=g.stage_ready();begin=10000.0
                source_lexists=os.path.lexists
                inputs=dict(input=synthetic_pin(g.base/'synthetic-input.json'))
                def lexists(path):return False if Path(path)==g.guest else source_lexists(path)
                if fault=='cancelled':g.api.activation.execute.side_effect=KeyboardInterrupt('PRIVATE_CANCELLATION_CANARY')
                g.api.activation.execute.return_value=dict(passed=False,feature_acceptance=False,input=inputs['input'])
                with ExitStack() as stack:
                    stack.enter_context(patch.object(bridge.os.path,'lexists',side_effect=lexists))
                    stack.enter_context(patch.object(rules,'PREPARE_AUTHORIZATION',g.live/'stage-only-authorization.json'))
                    stack.enter_context(patch.object(bridge,'prepared',return_value=env.binding(g.registry/'ledger-v1.json')))
                    stack.enter_context(patch.object(bridge,'create_inputs',return_value=inputs))
                    stack.enter_context(patch.object(bridge.time,'monotonic',return_value=begin+(301 if fault=='budget' else 0)))
                    result=bridge._run_stages(g.authority_pin,attempt_pin,begin)
                    self.assertIs(result['passed'],False);self.assertIs(result['feature_acceptance'],False)
                    self.assertNotIn('PRIVATE_CANCELLATION_CANARY',json.dumps(result))
                    if fault=='budget':g.api.env.prepare.assert_not_called();g.api.activation.execute.assert_not_called()
                    else:
                        g.api.env.prepare.assert_called_once();g.api.activation.execute.assert_called_once()
                        self.assertEqual(result['phase'],'activation')
                    kept=(g.live/'stage-result-v1.json').read_bytes()
                    again=bridge._run_stages(g.authority_pin,attempt_pin,begin)
                    self.assertIs(again['passed'],False)
                    self.assertEqual((g.live/'stage-result-v1.json').read_bytes(),kept)
                    self.assertLessEqual(g.api.env.prepare.call_count,1)

    def test_final_owner_and_stage_failures_cannot_become_success_even_with_other_positive_records(self):
        cases=('positive','cleanup','capture','returncode_bool','cancelled','stage_failed','stage_borrowed')
        for case in cases:
            with self.subTest(case=case),FreshGraph() as g:
                attempt_pin=g.stage_ready();worker=dict(pid=222,creation_filetime=333,executable=sys.executable)
                g.api.env.process_identity=Mock(return_value=dict(pid=111,creation_filetime=222,executable=sys.executable))
                owner=dict(status='child_exited',worker_returncode=0,cleanup_complete=True,output_capture_complete=True,worker=worker)
                if case=='cleanup':owner['cleanup_complete']=False
                if case=='capture':owner['output_capture_complete']=False
                if case=='returncode_bool':owner['worker_returncode']=False
                if case=='cancelled':owner['status']='cancelled'
                def supervise(request,begin):
                    g.write(g.live/'worker-started-v1.json',dict(request=request,worker=worker))
                    g.write(g.live/'worker-claim-v1.json',dict(version=1,authority=g.authority_pin,attempt=attempt_pin,request=request,worker=worker))
                    stage=dict(passed=case!='stage_failed',phase='completed',authority=g.authority_pin,attempt=copy.deepcopy(attempt_pin),feature_acceptance=False)
                    if case=='stage_borrowed':stage['attempt']['sha256']='0'*64
                    g.write(g.live/'stage-result-v1.json',stage);return owner
                with patch.object(bridge,'_initial',return_value=(g.authority,g.handoff)),patch.object(bridge,'_attempt',return_value=attempt_pin),patch.object(bridge,'_supervise',side_effect=supervise):
                    result=bridge.execute(g.authority_pin)
                self.assertIs(result['passed'],case=='positive')
                self.assertIs(result['feature_acceptance'],False)
                self.assertEqual(env.read_json(g.live/'operation-result-v1.json'),result)

    def activation_result(self,g,inputs):
        control=g.api.activation.CONTROL;control.mkdir()
        runtime=dict.fromkeys(('passed','controller_passed','owner_qualified','storage_closed','source_equal','cleanup_known'),True)
        runtime['input']=inputs['input'];runtime_pin=g.write(control/'runtime-result-v1.json',runtime)
        value=dict(passed=True,feature_acceptance=False,input=inputs['input'],runtime=runtime_pin)
        g.write(control/'final-result-v1.json',value)
        proofs=dict(admission=inputs['admission'])
        for role in ('owner_result','worker_result','after'):proofs[role]=g.write(g.guest/(role+'.json'),dict(synthetic=True))
        closure=dict(proposal_sha256=inputs['run_proposal']['sha256'],closure_verified=True,cleanup_complete=True,**proofs)
        closure_pin=g.write(g.guest/'guest-storage-closure-v1.json',closure)
        g.entry.update(state='closed',proposal_sha256=inputs['run_proposal']['sha256'],closure=closure_pin)
        g.write_ledger();return value,runtime,closure

    def test_activation_requires_qualified_runtime_exact_input_and_closed_run_ledger(self):
        for fault in ('positive','passed_bool','feature','runtime_cleanup','runtime_input','closure_cleanup','closure_admission','ledger_sha'):
            with self.subTest(fault=fault),FreshGraph() as g:
                inputs=g.create();value,runtime,closure=self.activation_result(g,inputs)
                if fault=='passed_bool':value['passed']=1
                elif fault=='feature':value['feature_acceptance']=True
                elif fault=='runtime_cleanup':runtime['cleanup_known']=False;value['runtime']=g.write(g.api.activation.CONTROL/'runtime-result-v1.json',runtime)
                elif fault=='runtime_input':
                    runtime['input']=dict(inputs['input'],sha256='0'*64);value['runtime']=g.write(g.api.activation.CONTROL/'runtime-result-v1.json',runtime)
                elif fault in ('closure_cleanup','closure_admission'):
                    if fault=='closure_cleanup':closure['cleanup_complete']=False
                    else:closure['admission']=dict(inputs['admission'],sha256='0'*64)
                    g.entry['closure']=g.write(g.guest/'guest-storage-closure-v1.json',closure);g.write_ledger()
                elif fault=='ledger_sha':g.entry['proposal_sha256']='0'*64;g.write_ledger()
                g.write(g.api.activation.CONTROL/'final-result-v1.json',value)
                if fault=='positive':
                    final,ledger=bridge._accept_activation(value,inputs);env.check_binding(final);env.check_binding(ledger)
                else:
                    with self.assertRaises(REFUSED):bridge._accept_activation(value,inputs)

    def test_budget_is_finite_not_boolean_and_read_save_are_bound_create_only(self):
        with FreshGraph() as g,patch.object(bridge.time,'monotonic',return_value=10000.0):
            bridge._budget(10000.0,2100)
            for begin in (True,math.nan,math.inf,10001.0,7000.0):
                with self.subTest(begin=begin),self.assertRaises(rules.FreshRunRefused):bridge._budget(begin,2100)
            path=g.base/'new-record.json';pin=bridge.save(path,dict(version=1,passed=False))
            self.assertEqual(bridge.read(pin,path),dict(version=1,passed=False))
            kept=path.read_bytes()
            with self.assertRaises(FileExistsError):bridge.save(path,dict(version=1,passed=True))
            self.assertEqual(path.read_bytes(),kept)
            bad=dict(pin,sha256='0'*64)
            with self.assertRaises(REFUSED):bridge.read(bad,path)


if __name__=='__main__':
    unittest.main()
