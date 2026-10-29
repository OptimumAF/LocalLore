"""Fixed SDK5 flow adversaries with real profile/proof readers and fake wire IO."""
import copy
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import Mock,patch

from benchmarks import android_process_client_v5 as c
from benchmarks import android_process_client_v4 as wire
from benchmarks import owned_restart_owner as owner
from scripts.tests import test_owned_restart_contract as f
from scripts.tests.test_android_process_client_v4 import FakeSocket,InlineSender,packet


@unittest.skipUnless(os.name=='nt','physical D client fixtures')
class OwnedRestartClientTests(unittest.TestCase):
    def setUp(self):
        self.base=Path(tempfile.mkdtemp(prefix='locallore-sdk5-client-',dir='D:/Dev/_Temp'))
        self.a=f.admission();self.a['root']=str(self.base/'lease');self.a['server']['root']=str(self.base/'lease/server')
        self.probe=self.base/'physical_model_probe_v1.txt';self.probe.write_bytes(b'original\0\x1a\xff\r\n')
        self.a['artifacts']['probe']=wire.environment.binding(self.probe)
        self.process_probe=self.base/'android-author-process-probe-v1';self.process_probe.write_bytes(b'\x7fELF\0\x1a-original fake bytes')
        self.a['artifacts']['process_probe']=wire.environment.binding(self.process_probe)
        self.admission=self.base/'admission-v1.json';wire.environment.create_json(self.admission,self.a)
        self.admission_pin=wire.environment.binding(self.admission);self.d=f.running(self.a);self.d['admission']=self.admission_pin
        self.running=self.base/'lease/running-v1.json';self.running.parent.mkdir();wire.environment.create_json(self.running,self.d)
        self.running_pin=wire.environment.binding(self.running)
        # Exact fixed owner type; kernel/live IO is explicitly mocked, while
        # its real claim_once method and complete proof readers remain active.
        self.lease=object.__new__(owner.LiveOwnedRestartTarget)
        self.lease._admission=copy.deepcopy(self.a);self.lease._descriptor=copy.deepcopy(self.d)
        self.lease._admission_binding=copy.deepcopy(self.admission_pin);self.lease._running_binding=copy.deepcopy(self.running_pin)
        self.lease._caller=copy.deepcopy(self.d['worker']);self.lease.guard=Mock();self.lease.fast_guard=Mock();self.lease.prove=Mock(side_effect=self.prove)
        self.clock=100.0;self.proof_fail=set();self.proof_cost={};self.index=0;self.on_proof=None
        self.enter(patch.object(wire.time,'monotonic',side_effect=lambda:self.clock));self.enter(patch.object(wire.time,'time',return_value=1800000010.0))
        self.enter(patch.object(wire.threading,'Thread',InlineSender))
        self.sock=FakeSocket(self.response());self.factory=self.enter(patch.object(wire.socket,'socket',side_effect=lambda *args:self.sock))
    def enter(self,context):
        result=context.__enter__();self.addCleanup(context.__exit__,None,None,None);return result
    def response(self,code=0,body=b'original\0\x1a\xff\r\n'):return b'OKAYOKAY'+packet(1,body)+packet(3,bytes([code]))
    def capture(self,seconds=100):
        self.index+=1;parent=self.base/('session-%02d'%self.index);parent.mkdir();return c.OwnedRestartSdkCapture(parent/'clients',seconds,self.lease)
    def prove(self,path,session,context,sock,anchor,after=False):
        self.clock+=self.proof_cost.get(context['phase'],0)
        if context['phase']in self.proof_fail:raise ValueError('synthetic failed observation')
        proof=f.proof(session,after=after);proof.update(context=copy.deepcopy(context),anchor=copy.deepcopy(anchor))
        proof['session']=wire.environment.binding(Path(session['root'])/'sdk-session-v5.json')
        queries=path.with_name(path.stem+'-queries-v1.json');wire.environment.create_json(queries,f.query_bundle(session));proof['queries']=wire.environment.binding(queries)
        wire.environment.create_json(path,proof)
        if self.on_proof:self.on_proof(context)
        return wire.environment.binding(path)
    def row(self,capture):return wire.environment.read_json(capture.directory/'command-0001.json')
    def poisoned(self,capture):
        self.assertFalse(capture.clean);count=self.factory.call_count
        with self.assertRaises(c.ClientRefused):capture.shell(['getprop','sys.boot_completed'],'later')
        self.assertEqual(self.factory.call_count,count)

    def test_exact_fixed_new_owner_records_v5_session_and_binary_data(self):
        capture=self.capture();result=capture.shell(['getprop','sys.boot_completed'],'boot');row=self.row(capture)
        self.assertEqual(result,b'original\0\x1a\xff\r\n');self.assertEqual(row['version'],5);self.assertEqual(row['protocol'],f.SDK_PROTOCOL)
        self.assertTrue(row['client_qualified']);self.assertTrue(Path(capture.session_binding['path']).name=='sdk-session-v5.json')
        self.assertEqual(self.sock.connects,[('127.0.0.1',15937)])

    def test_old_and_subclass_owner_types_refuse_before_any_guard_or_output(self):
        from benchmarks.owned_target_owner import LiveOwnedTarget
        class Derived(owner.LiveOwnedRestartTarget):pass
        for invalid in(object.__new__(LiveOwnedTarget),object.__new__(Derived),Mock()):
            invalid.guard=Mock();parent=self.base/('invalid-'+type(invalid).__name__);parent.mkdir()
            with self.assertRaises(c.ClientRefused):c.OwnedRestartSdkCapture(parent/'clients',100,invalid)
            invalid.guard.assert_not_called();self.assertEqual(list(parent.iterdir()),[])
        self.factory.assert_not_called()

    def test_old_sdk4_constructor_rejects_new_exact_owner_without_dispatch(self):
        parent=self.base/'old-sdk4';parent.mkdir()
        with self.assertRaises(wire.ClientRefused):wire.OwnedTargetSdkCapture(parent/'clients',100,self.lease)
        self.lease.guard.assert_not_called();self.factory.assert_not_called()

    def test_fixed_contract_and_verifier_properties_cannot_be_caller_replaced(self):
        capture=self.capture()
        for key,value in(('_contract',wire.contract),('_verification',wire.verification),('_expected_lease_class',object)):
            with self.subTest(key=key):
                with self.assertRaises(AttributeError):setattr(capture,key,value)
        self.assertIs(capture._contract,f.r);self.assertIs(capture._verification,f.reader)

    def test_import_claim_is_real_create_only_and_admission_wide_across_sessions(self):
        first=self.capture();first.shell(f.instrumentation('import'),'import')
        claim=self.base/'lease/claims-v1/import-v1.json';self.assertTrue(claim.is_file());value=wire.environment.read_json(claim)
        self.assertIsNone(value['prerequisite'])
        self.sock=FakeSocket(self.response());second=self.capture()
        with self.assertRaises(c.ClientRefused):second.shell(f.instrumentation('import'),'import')
        self.assertEqual(second.count,0);self.assertEqual(self.sock.sent,b'');self.poisoned(second)

    def test_missing_restart_prerequisite_refuses_before_target_frame_and_claim(self):
        capture=self.capture()
        with self.assertRaises(c.ClientRefused):capture.shell(f.instrumentation('restart'),'restart')
        self.assertEqual(capture.count,0);self.assertEqual(self.sock.sent,b'');self.assertFalse((self.base/'lease/claims-v1/restart-v1.json').exists());self.poisoned(capture)

    def test_failed_preproof_closes_owned_socket_without_sdk_record(self):
        capture=self.capture();self.proof_fail.add('before')
        with self.assertRaises(c.ClientRefused):capture.shell(['getprop','sys.boot_completed'],'boot')
        self.assertEqual(capture.count,0);self.assertEqual(list(capture.directory.iterdir()),[]);self.assertTrue(self.sock.closed);self.poisoned(capture)

    def test_full_budget_charges_proof_time_and_failed_postproof_preserves_measurement(self):
        capture=self.capture(seconds=20);self.proof_cost['before']=6
        with self.assertRaises(c.ClientRefused):capture.shell(['getprop','sys.boot_completed'],'boot',seconds=15,full_budget=True)
        self.assertEqual(capture.count,0);self.assertEqual(self.sock.sent,b'');self.poisoned(capture)
        self.proof_cost={};self.proof_fail={'after'};self.sock=FakeSocket(self.response());capture=self.capture()
        with self.assertRaises(c.ClientRefused):capture.shell(['getprop','sys.boot_completed'],'boot')
        row=self.row(capture);self.assertEqual(row['status'],'completed');self.assertEqual(row['returncode'],0)
        self.assertFalse(row['client_qualified']);self.assertIsNone(row['server_after']);self.poisoned(capture)

    def test_bound_process_probe_stream_preserves_binary_input_and_digest(self):
        capture=self.capture();capture.stream(['dd','of='+f.PROBE_PATH,'bs=65536'],self.a['artifacts']['process_probe'],'stage-probe',seconds=15)
        row=self.row(capture);self.assertTrue(row['stdin_complete']);self.assertEqual(row['stdin_bytes'],self.process_probe.stat().st_size)
        self.assertEqual(row['stdin_sha256'],self.a['artifacts']['process_probe']['sha256']);self.assertIn(packet(0,self.process_probe.read_bytes()),self.sock.sent)

    def test_cancelled_partial_bytes_and_unknown_close_remain_unqualified(self):
        self.sock=FakeSocket(b'OKAYOKAY'+packet(1,b'measured\0\x1a'));self.sock.eof_error=KeyboardInterrupt();capture=self.capture()
        with self.assertRaises(c.ClientRefused):capture.shell(['getprop','sys.boot_completed'],'boot')
        row=self.row(capture);self.assertEqual(row['status'],'cancelled');self.assertEqual(Path(row['stdout']['path']).read_bytes(),b'measured\0\x1a');self.poisoned(capture)
        self.sock=FakeSocket(self.response(),close_error=True);capture=self.capture()
        with self.assertRaises(c.ClientRefused):capture.shell(['getprop','sys.boot_completed'],'boot')
        row=self.row(capture);self.assertEqual(row['status'],'completed');self.assertFalse(row['socket_closed']);self.assertFalse(row['client_qualified']);self.poisoned(capture)


if __name__=='__main__':unittest.main()
