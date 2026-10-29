"""SDK3 client flow adversaries. Proofs, process identities and SDK execution are fake.

The independent reader suite supplies complete original synthetic proof bundles;
these tests isolate client ordering, budgets, byte persistence and fail-stop flow.
No fake manifest here is claimed to satisfy the real bundle reader.
"""
import copy
import hashlib
import json
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from benchmarks import android_process_client_v3 as c
from scripts.tests import test_adb_held_socket as held_fixture


@unittest.skipUnless(os.name=='nt','physical D: client fixtures require Windows')
class Sdk3ClientTests(unittest.TestCase):
    def setUp(self):
        self.base=Path(tempfile.mkdtemp(prefix='locallore-sdk3-client-',dir='D:/Dev/_Temp'))
        self.adb=self.base/'adb.exe';self.adb.write_bytes(b'synthetic ADB; never executed')
        self.ps=self.base/'powershell.exe';self.ps.write_bytes(b'synthetic PowerShell; never executed')
        self.py=self.base/'python.exe';self.py.write_bytes(b'synthetic Python pin; never executed')
        self.dll=self.base/'python314.dll';self.dll.write_bytes(b'synthetic DLL pin; never loaded')
        self.sdk_source=self.base/'sdk-source.py';self.sdk_source.write_bytes(b'# synthetic SDK source\n')
        self.held_source=self.base/'held-source.py';self.held_source.write_bytes(b'# synthetic held source\n')
        self.caller=dict(pid=9001,creation_filetime=900100,executable=str(self.py))
        self.launcher=dict(pid=9002,creation_filetime=900200,executable=str(self.base/'emulator.exe'))
        pin,sha=c.legacy._file_pin(self.adb)
        admitted=held_fixture.admission();admitted['server']['executable']=str(self.adb)
        admitted['adb_file']=dict(path=str(self.adb),bytes=self.adb.stat().st_size,sha256=sha,identity=list(pin))
        self.admission=self.base/'admission.json';c.environment.create_json(self.admission,admitted)
        self.admission_binding=c.environment.binding(self.admission)
        self.clock=100.0;self.session_index=0;self.proof_calls=[];self.proof_cost={}
        self.acquire_fail=set();self.verify_fail=set();self.mutate_context=None
        self.sdk_after=None;self.sdk_result=None;self.sdk_error=None
        self.payload=b'original\x00\x1a\xff\r\n\n'
        self.enter(patch.object(c.time,'monotonic',side_effect=lambda:self.clock))
        self.enter(patch.object(c.os,'getpid',return_value=self.caller['pid']))
        self.identity=self.enter(patch.object(c.environment,'process_identity',side_effect=self.process_identity))
        self.sdk_sources=self.enter(patch.object(c.verification,'sdk_source_bindings',side_effect=lambda:[c.environment.binding(self.sdk_source)]))
        self.held_sources=self.enter(patch.object(c.held_probe,'_source_bindings',side_effect=lambda:[c.environment.binding(self.held_source)]))
        self.python=self.enter(patch.object(c.verification,'python_bindings',side_effect=lambda:dict(executable=c.environment.binding(self.py),runtime_dll=c.environment.binding(self.dll))))
        self.enter(patch.object(c.verification,'validate_session',side_effect=copy.deepcopy))
        # Row schema/real proof admission belongs to the separate reader suite.
        # Keeping this seam explicit isolates orchestration from schema updates.
        self.enter(patch.object(c.verification,'client_record_shape_v3',return_value=True))
        self.acquire=self.enter(patch.object(c.verification,'acquire_owned_server_bundle',side_effect=self.fake_acquire))
        self.verify=self.enter(patch.object(c.verification,'verify_owned_server_bundle',side_effect=self.fake_verify))
        self.runner=self.enter(patch.object(c.host,'run_process',side_effect=self.run_sdk))
        self.legacy_observer=self.enter(patch.object(c.legacy,'observe_server',side_effect=AssertionError('legacy observer')))
        self.legacy_constructor=self.enter(patch.object(c.legacy,'SdkCapture',side_effect=AssertionError('legacy constructor')))

    def enter(self,context):
        value=context.__enter__();self.addCleanup(context.__exit__,None,None,None);return value

    def process_identity(self,pid):
        self.assertIn(pid,(9001,9002));return copy.deepcopy(self.caller if pid==9001 else self.launcher)

    def owner(self,seconds=100,launcher=False):
        self.session_index+=1;parent=self.base/f'session-{self.session_index:03d}';parent.mkdir()
        return c.HeldServerSdkCapture(parent/'clients',seconds,self.adb,self.ps,self.admission_binding,
                                      self.launcher if launcher else None)

    def command(self,owner,operation=None):
        prefix=[str(self.adb),'-H','127.0.0.1','-P','5037']
        return prefix+(['devices','-l']if owner.target is None else ['-t',str(owner.target['transport_id']),*(operation or ['get-state'])])

    def fake_acquire(self,directory,session_binding,context,seconds):
        original=copy.deepcopy(context)
        self.proof_calls.append(dict(directory=directory,session=copy.deepcopy(session_binding),context=original,seconds=seconds))
        self.assertIs(type(seconds),int);self.assertGreater(seconds,0);self.assertLessEqual(seconds,45)
        directory.mkdir()
        if self.mutate_context is not None:self.mutate_context(context)
        c.environment.create_json(directory/'bundle-v1.json',dict(context=copy.deepcopy(context),session=copy.deepcopy(session_binding),verified=context['phase']not in self.verify_fail))
        self.clock+=self.proof_cost.get(original['phase'],0)
        if original['phase']in self.acquire_fail:raise RuntimeError('SYNTHETIC_PRIVATE_PROVIDER_TEXT')
        return c.environment.binding(directory/'bundle-v1.json')

    def fake_verify(self,binding,session,context):
        c.environment.check_binding(binding);record=c.environment.read_json(binding['path'])
        self.assertEqual(session['protocol'],c.verification.SDK_PROTOCOL)
        if record['context']!=context or record['verified']is not True:raise ValueError('synthetic refused proof')
        return True

    def run_sdk(self,command,**kwargs):
        self.assertEqual(command[0],str(self.adb));self.assertEqual(kwargs['request'],b'')
        if self.sdk_after:self.sdk_after(command)
        if self.sdk_error:raise self.sdk_error
        return self.sdk_result or c.host.ProcessResult('completed',7,self.payload,0,0,True)

    def row(self,owner,index=1):return c.environment.read_json(owner.directory/f'command-{index:04d}.json')

    def stopped(self,owner):
        calls=self.runner.call_count;proofs=self.acquire.call_count
        owner.clean=True
        with self.assertRaises(c.ClientRefused):owner.capture(self.command(owner),'later')
        self.assertFalse(owner.clean);self.assertEqual(self.runner.call_count,calls);self.assertEqual(self.acquire.call_count,proofs)

    def test_binary_sdk_bytes_have_exact_v3_row_and_fresh_before_after(self):
        owner=self.owner();owner.target={'transport_id':7}
        self.assertEqual(owner.adb(['get-state'],'state'),self.payload)
        row=self.row(owner);self.assertEqual(owner.count,1);self.assertTrue(owner.clean)
        self.assertEqual((owner.directory/'command-0001.stdout.bin').read_bytes(),self.payload)
        self.assertEqual(row['stdout_sha256'],hashlib.sha256(self.payload).hexdigest())
        self.assertEqual(row['version'],3);self.assertEqual(row['protocol'],c.verification.SDK_PROTOCOL)
        self.assertEqual(row['argv'],self.command(owner));self.assertEqual(row['command_sha256'],c.verification.command_digest(row['argv']))
        self.assertEqual(row['elapsed_ms'],7);self.assertEqual(row['effective_deadline_ms'],15000)
        self.assertEqual([(x['context']['kind'],x['context']['phase'],x['context']['index'])for x in self.proof_calls],[('command','before',1),('command','after',1)])
        self.assertNotEqual(row['server_before'],row['server_after']);self.legacy_observer.assert_not_called();self.legacy_constructor.assert_not_called()

    def test_discovery_only_before_target_and_target_is_copied_immutable(self):
        owner=self.owner();owner.capture(self.command(owner),'devices')
        target={'transport_id':7};owner.target=target;target['transport_id']=8
        owner.target['transport_id']=9;self.assertEqual(owner.target,{'transport_id':7})
        with self.assertRaises(c.ClientRefused):owner.capture([str(self.adb),'-H','127.0.0.1','-P','5037','devices','-l'],'again')
        self.assertEqual(self.runner.call_count,1);self.stopped(owner)

    def test_retarget_or_clear_after_selection_refuses(self):
        for target in ({'transport_id':8},None):
            with self.subTest(target=target):
                owner=self.owner();owner.target={'transport_id':7}
                with self.assertRaises(c.ClientRefused):owner.target=target
                self.stopped(owner)
        self.runner.assert_not_called()

    def test_old_server_observer_and_global_reconnect_commands_never_dispatch(self):
        for op in (['kill-server'],['start-server'],['reconnect'],['connect','x'],['devices'],['-s','foreign','get-state']):
            with self.subTest(op=op):
                owner=self.owner();owner.target={'transport_id':7}
                with self.assertRaises(c.ClientRefused):owner.capture([str(self.adb),'-H','127.0.0.1','-P','5037',*op],'global')
                self.stopped(owner)
        owner=self.owner()
        with self.assertRaises(c.ClientRefused):owner.capture(c.legacy._server_command(self.ps),'observer')
        self.runner.assert_not_called();self.acquire.assert_not_called()

    def test_preproof_refusal_retains_attempt_without_sdk_row(self):
        owner=self.owner();self.verify_fail.add('before')
        with self.assertRaises(c.ClientRefused):owner.capture(self.command(owner),'devices')
        self.assertEqual(owner.count,0);self.assertEqual(list(owner.directory.iterdir()),[])
        self.assertTrue((owner.directory.parent/'server-proofs-v3/command-0001-before/bundle-v1.json').is_file())
        self.runner.assert_not_called();self.stopped(owner)

    def test_refused_postproof_keeps_successful_sdk_measurement_and_bytes(self):
        owner=self.owner();self.verify_fail.add('after')
        with self.assertRaises(c.ClientRefused):owner.capture(self.command(owner),'devices')
        row=self.row(owner);self.assertEqual(row['status'],'completed');self.assertTrue(row['cleanup_complete'])
        self.assertEqual(row['elapsed_ms'],7);self.assertIsNotNone(row['server_after'])
        self.assertEqual((owner.directory/'command-0001.stdout.bin').read_bytes(),self.payload);self.stopped(owner)

    def test_missing_postproof_retains_null_without_reusing_preproof(self):
        owner=self.owner();self.sdk_after=lambda command:setattr(self,'clock',owner.until-0.5)
        with self.assertRaises(c.ClientRefused):owner.capture(self.command(owner),'devices')
        row=self.row(owner);self.assertEqual(row['status'],'completed');self.assertIsNone(row['server_after'])
        self.assertEqual(self.acquire.call_count,1);self.stopped(owner)

    def test_full_budget_is_checked_after_consuming_preproof(self):
        owner=self.owner(seconds=20);self.proof_cost['before']=6
        with self.assertRaises(c.ClientRefused):owner.capture(self.command(owner),'devices',seconds=15,full_budget=True)
        self.assertEqual(owner.count,0);self.runner.assert_not_called();self.assertEqual(self.acquire.call_count,1);self.stopped(owner)

    def test_exact_remaining_sdk_budget_and_integer_floor_proof_owner_budget(self):
        owner=self.owner(seconds=20);self.proof_cost['before']=6.25
        owner.capture(self.command(owner),'devices',seconds=15)
        self.assertEqual(self.runner.call_args.kwargs['deadline'],13.75)
        self.assertEqual(self.row(owner)['effective_deadline_ms'],13750)
        self.assertEqual([x['seconds']for x in self.proof_calls],[20,13])

    def test_short_remaining_proof_budget_refuses_before_acquisition(self):
        owner=self.owner();self.clock=owner.until-0.75
        with self.assertRaises(c.ClientRefused):owner.check_server()
        self.acquire.assert_not_called();self.runner.assert_not_called();self.stopped(owner)

    def test_trusted_cancelled_partial_result_is_preserved_without_postproof(self):
        owner=self.owner();self.sdk_result=c.host.ProcessResult('cancelled',23,self.payload,0,None,False)
        with self.assertRaises(c.ClientRefused):owner.capture(self.command(owner),'devices')
        row=self.row(owner);self.assertEqual(row['status'],'cancelled');self.assertEqual(row['elapsed_ms'],23)
        self.assertIsNone(row['returncode']);self.assertFalse(row['cleanup_complete']);self.assertIsNone(row['server_after'])
        self.assertEqual(self.acquire.call_count,1);self.stopped(owner)

    def test_unknown_runner_failure_does_not_infer_elapsed_or_cleanup(self):
        owner=self.owner();self.sdk_error=KeyboardInterrupt()
        with self.assertRaises(c.ClientRefused):owner.capture(self.command(owner),'devices')
        row=self.row(owner);self.assertEqual(row['status'],'spawn_failed');self.assertIsNone(row['elapsed_ms'])
        self.assertFalse(row['cleanup_complete']);self.assertIsNone(row['returncode']);self.assertIsNone(row['server_after'])
        self.assertEqual(row['stdout_bytes'],0);self.assertEqual(self.acquire.call_count,1);self.stopped(owner)

    def test_failed_sdk_status_keeps_real_partial_bytes_and_postproof_when_safe(self):
        owner=self.owner();self.sdk_result=c.host.ProcessResult('completed',33,self.payload,0,2,True)
        with self.assertRaises(c.ClientRefused):owner.capture(self.command(owner),'devices')
        row=self.row(owner);self.assertEqual(row['returncode'],2);self.assertEqual(row['elapsed_ms'],33)
        self.assertIsNotNone(row['server_after']);self.assertEqual(self.acquire.call_count,2);self.stopped(owner)

    def test_check_server_has_separate_indices_and_no_fake_sdk_rows(self):
        owner=self.owner();first=owner.check_server();second=owner.check_server()
        self.assertNotEqual(first,second);self.assertEqual(owner.count,0);self.runner.assert_not_called()
        self.assertEqual([(x['context']['kind'],x['context']['phase'],x['context']['label'],x['context']['index'])for x in self.proof_calls],[('check','check','check-server',1),('check','check','check-server',2)])

    def test_external_proofs_pair_exact_context_but_do_not_claim_transfer(self):
        owner=self.owner();owner.target={'transport_id':7};command=self.command(owner,['exec-out','echo','synthetic'])
        before=owner.prove_external(command,'stream','before',1);after=owner.prove_external(command,'stream','after',1)
        self.assertNotEqual(before,after);self.assertEqual(owner.count,0);self.runner.assert_not_called()
        self.assertEqual([x['context']['phase']for x in self.proof_calls],['before','after'])
        self.assertEqual(list(owner.directory.iterdir()),[])

    def test_external_after_cannot_borrow_another_command_or_index(self):
        owner=self.owner();owner.target={'transport_id':7};command=self.command(owner,['exec-out','echo','one'])
        owner.prove_external(command,'stream','before',1)
        with self.assertRaises(c.ClientRefused):owner.prove_external(self.command(owner,['exec-out','echo','two']),'stream','after',1)
        self.assertEqual(self.acquire.call_count,1);self.stopped(owner)

    def test_external_pending_context_blocks_regular_capture_and_checks(self):
        owner=self.owner();owner.target={'transport_id':7};owner.prove_external(self.command(owner),'stream','before',1)
        with self.assertRaises(c.ClientRefused):owner.capture(self.command(owner),'state')
        self.runner.assert_not_called();self.assertEqual(self.acquire.call_count,1);self.stopped(owner)

    def test_copied_session_properties_cannot_rewrite_live_pins(self):
        owner=self.owner();value=owner.session;value['owner']['pid']+=1
        pin=owner.session_binding;pin['sha256']='0'*64
        owner.check_server();self.assertEqual(owner.session['owner'],self.caller)

    def test_tool_source_session_and_caller_changes_poison_before_sdk(self):
        for changed in ('source','session','caller','launcher','tool'):
            with self.subTest(changed=changed):
                owner=self.owner(launcher=True)
                if changed=='tool':self.adb.write_bytes(b'changed synthetic tool')
                elif changed=='source':self.sdk_source.write_bytes(b'# changed synthetic source')
                elif changed=='session':(owner.directory.parent/'sdk-session-v3.json').write_bytes(b'{"changed":true}')
                elif changed=='caller':self.caller['creation_filetime']+=1
                else:self.launcher['creation_filetime']+=1
                with self.assertRaises(c.ClientRefused):owner.capture(self.command(owner),'devices')
                self.stopped(owner)
        self.runner.assert_not_called()

    def test_acquisition_cannot_mutate_expected_preproof_context(self):
        owner=self.owner();self.mutate_context=lambda context:context.update(phase='after')
        with self.assertRaises(c.ClientRefused):owner.capture(self.command(owner),'devices')
        self.runner.assert_not_called();self.stopped(owner)

    def test_sdk_runner_cannot_rewrite_original_argv_and_proof_context(self):
        owner=self.owner();owner.target={'transport_id':7};original=self.command(owner)
        self.sdk_after=lambda command:command.__setitem__(-1,'get-serialno')
        with self.assertRaises(c.ClientRefused):owner.capture(original,'state')
        self.assertEqual(original,self.command(owner));self.assertEqual(self.row(owner)['argv'],original);self.stopped(owner)

    def test_public_deadline_cannot_extend_original_session_budget(self):
        owner=self.owner(seconds=10);owner.until+=100
        with self.assertRaises(c.ClientRefused):owner.check_server()
        self.acquire.assert_not_called();self.stopped(owner)

    def test_public_deadline_may_be_shortened(self):
        owner=self.owner(seconds=100);owner.until=min(owner.until,self.clock+10)
        owner.check_server();self.assertEqual(self.proof_calls[0]['seconds'],10)

    def test_clock_rollback_refuses_before_proof_or_sdk(self):
        owner=self.owner();self.clock-=0.01
        with self.assertRaises(c.ClientRefused):owner.check_server()
        self.acquire.assert_not_called();self.runner.assert_not_called();self.stopped(owner)


if __name__=='__main__':unittest.main()
