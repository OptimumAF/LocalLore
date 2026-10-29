"""Original shell-v2 byte and client flow tests. Every socket/owner is fake."""
import copy
import hashlib
import io
import os
from pathlib import Path
import struct
import tempfile
import unittest
from unittest.mock import Mock,patch

from benchmarks import android_process_client_v4 as c
from scripts.tests import test_owned_target_contract as f


def packet(channel,payload):return bytes([channel])+struct.pack('<I',len(payload))+payload


class FakeSocket:
    def __init__(self,raw=b'',*,fragment=2,close_error=False):
        self.raw=bytearray(raw);self.fragment=fragment;self.sent=bytearray();self.connects=[]
        self.closed=False;self.close_error=close_error;self.recvs=0;self.recv_error=None;self.eof_error=None
    def setsockopt(self,*args):pass
    def bind(self,endpoint):
        if endpoint!=('127.0.0.1',0):raise AssertionError('unscoped bind')
    def fileno(self):return -1 if self.closed else 81
    def getsockname(self):return('127.0.0.1',43101)
    def getpeername(self):return('127.0.0.1',15937)
    def settimeout(self,value):pass
    def connect(self,endpoint):self.connects.append(endpoint)
    def send(self,value):
        count=min(3,len(value));self.sent.extend(value[:count]);return count
    def recv(self,size):
        self.recvs+=1
        if self.recv_error is not None:raise self.recv_error
        if not self.raw and self.eof_error is not None:raise self.eof_error
        size=min(size,self.fragment,len(self.raw));raw=bytes(self.raw[:size]);del self.raw[:size];return raw
    def shutdown(self,*args):pass
    def close(self):
        if self.close_error:raise OSError('synthetic close refusal')
        self.closed=True


class InlineSender:
    fail_start=False
    stays_alive=False
    def __init__(self,target,args,daemon):self.target=target;self.args=args;self.started=False
    def start(self):
        if self.fail_start:raise RuntimeError('synthetic thread start refusal')
        self.started=True;self.target(*self.args)
    def join(self,timeout=None):pass
    def is_alive(self):return self.stays_alive


class ShellFramingTests(unittest.TestCase):
    def bare(self):
        owner=object.__new__(c.OwnedTargetSdkCapture);owner._timeout=lambda *args:None;owner._fast_guard=lambda *args:None
        return owner
    def state(self):return dict(stdout=bytearray(),stderr=bytearray(),returncode=None,sender_failed=False)

    def test_original_input_packet_and_smart_lengths_preserve_binary_bytes(self):
        raw=b'\0\x1a\xff\r\n';self.assertEqual(c._packet(0,raw),packet(0,raw));self.assertEqual(c._packet(4,b''),packet(4,b''))
        self.assertEqual(c._smart_frame(b'host:transport-id:7'),b'0013host:transport-id:7')
        for channel,payload in((True,b''),(3,b''),(4,b'x'),(0,bytearray(b'x')),(0,b'x'*65537)):
            with self.subTest(channel=channel,length=len(payload)):
                with self.assertRaises(c.ClientRefused):c._packet(channel,payload)

    def test_fragmented_stdout_stderr_and_one_byte_exit_followed_by_eof(self):
        state=self.state();sock=FakeSocket(packet(1,b'\0\x1a\xff\r\n')+packet(2,b'warning')+packet(3,b'\x07'))
        self.bare()._read_shell(sock,state,103,100)
        self.assertEqual(state['stdout'],b'\0\x1a\xff\r\n');self.assertEqual(state['stderr'],b'warning');self.assertEqual(state['returncode'],7)

    def test_unknown_channel_size_exit_length_trailing_data_and_missing_exit_refuse(self):
        for raw in(packet(0,b'x'),packet(4,b''),packet(3,b''),packet(3,b'\0\0'),
                   packet(3,b'\0')+packet(3,b'\0'),packet(3,b'\0')+packet(1,b'x'),packet(1,b'x'),
                   bytes([1])+struct.pack('<I',c.MAX_PACKET+1)):
            with self.subTest(raw=raw[:5]):
                with self.assertRaises(c.ClientRefused):self.bare()._read_shell(FakeSocket(raw),self.state(),103,100)

    def test_partial_payload_and_header_preserve_measured_bytes_on_eof(self):
        for raw,expected in((bytes([1])+struct.pack('<I',6)+b'abc',b'abc'),(b'\x01\x02',b'')):
            state=self.state()
            with self.assertRaises(c.ClientRefused):self.bare()._read_shell(FakeSocket(raw),state,103,100)
            self.assertEqual(state['stdout'],expected);self.assertIsNone(state['returncode'])

    def test_capture_limit_counts_both_channels_and_sender_failure_refuses(self):
        state=self.state()
        with self.assertRaises(c.ClientRefused):self.bare()._read_shell(FakeSocket(packet(1,b'ab')+packet(2,b'cd')),state,103,3)
        self.assertEqual(state['stdout'],b'ab');self.assertEqual(state['stderr'],b'')
        state=self.state();state['sender_failed']=True
        with self.assertRaises(c.ClientRefused):self.bare()._read_shell(FakeSocket(packet(3,b'\0')),state,103,100)

    def test_input_sender_hashes_only_payload_and_sends_exact_close_stdin(self):
        raw=b'original\0\x1a\xff\r\n';state=dict(input_limit=len(raw));sock=FakeSocket()
        self.bare()._send_shell(sock,io.BytesIO(raw),state,103)
        self.assertEqual(sock.sent,packet(0,raw)+packet(4,b''));self.assertEqual(state['stdin_bytes'],len(raw))
        self.assertEqual(state['stdin_sha256'],hashlib.sha256(raw).hexdigest());self.assertTrue(state['stdin_complete'])

    def test_input_truncation_and_growth_do_not_claim_complete(self):
        for raw,limit in((b'ab',3),(b'abcd',3)):
            state=dict(input_limit=limit);sock=FakeSocket();self.bare()._send_shell(sock,io.BytesIO(raw),state,103)
            self.assertTrue(state['sender_failed']);self.assertFalse(state.get('stdin_complete',False));self.assertLessEqual(state['stdin_bytes'],limit)


@unittest.skipUnless(os.name=='nt','physical D fixtures')
class OwnedClientFlowTests(unittest.TestCase):
    def setUp(self):
        self.base=Path(tempfile.mkdtemp(prefix='locallore-sdk4-client-',dir='D:/Dev/_Temp'))
        self.clock=100.0;self.proof_cost={};self.proof_fail=set();self.guard_fail=False;self.proof_calls=[];self.claims=set();self.index=0;self.on_proof=None
        self.admitted=f.admission();self.descriptor=f.running(self.admitted)
        self.probe=self.base/'physical_model_probe_v1.txt';self.payload=b'original probe\0\x1a\xff\r\n';self.probe.write_bytes(self.payload)
        self.admitted['artifacts']['probe']=c.environment.binding(self.probe)
        self.admission_pin=f.pin(self.base/'admission-v1.json');self.running_pin=f.pin(Path(self.admitted['root'])/'running-v1.json')
        self.descriptor['admission']=copy.deepcopy(self.admission_pin)
        self.lease=Mock();self.lease.admission=copy.deepcopy(self.admitted);self.lease.descriptor=copy.deepcopy(self.descriptor)
        self.lease.admission_binding=copy.deepcopy(self.admission_pin);self.lease.running_binding=copy.deepcopy(self.running_pin)
        self.lease.caller=copy.deepcopy(self.descriptor['worker']);self.lease.guard.side_effect=self.guard;self.lease.fast_guard.side_effect=self.guard
        self.lease.prove.side_effect=self.prove;self.lease.claim_once.side_effect=self.claim
        self.enter(patch.object(c.time,'monotonic',side_effect=lambda:self.clock));self.enter(patch.object(c.time,'time',return_value=1800000010.0))
        self.enter(patch.object(c.threading,'Thread',InlineSender))
        self.socket=FakeSocket(self.response());self.factory=self.enter(patch.object(c.socket,'socket',side_effect=lambda *args:self.socket))
    def enter(self,context):
        result=context.__enter__();self.addCleanup(context.__exit__,None,None,None);return result
    def guard(self,**kwargs):
        if self.guard_fail:raise ValueError('synthetic source changed')
    def claim(self,kind,digest):
        if kind in self.claims:raise ValueError('already claimed')
        self.claims.add(kind)
    def response(self,code=0,stdout=b'hello\0\x1a\xff\r\n',stderr=b''):
        return b'OKAYOKAY'+packet(1,stdout)+packet(2,stderr)+packet(3,bytes([code]))
    def owner(self,seconds=100):
        self.index+=1;parent=self.base/('session-%02d'%self.index);parent.mkdir()
        return c.OwnedTargetSdkCapture(parent/'clients',seconds,self.lease)
    def prove(self,path,session,context,sock,anchor,after=False):
        self.proof_calls.append(copy.deepcopy(context));self.clock+=self.proof_cost.get(context['phase'],0)
        if context['phase']in self.proof_fail:raise ValueError('synthetic proof failure')
        value=f.proof(session,after=after);value.update(context=copy.deepcopy(context),anchor=copy.deepcopy(anchor))
        value['session']=c.environment.binding(Path(session['root'])/'sdk-session-v4.json')
        query_path=path.with_name(path.stem+'-queries-v1.json')
        c.environment.create_json(query_path,f.query_bundle(session));value['queries']=c.environment.binding(query_path)
        c.environment.create_json(path,value)
        if self.on_proof is not None:self.on_proof(context)
        return c.environment.binding(path)
    def row(self,owner):return c.environment.read_json(owner.directory/'command-0001.json')
    def poisoned(self,owner):
        self.assertFalse(owner.clean);calls=self.factory.call_count
        with self.assertRaises(c.ClientRefused):owner.shell(['getprop','sys.boot_completed'],'later')
        self.assertEqual(self.factory.call_count,calls)

    def test_actual_socket_flow_has_private_route_two_statuses_and_exact_binary_records(self):
        owner=self.owner();raw=owner.shell(['getprop','sys.boot_completed'],'boot')
        row=self.row(owner);self.assertEqual(raw,b'hello\0\x1a\xff\r\n');self.assertTrue(row['client_qualified'])
        self.assertEqual(row['status'],'completed');self.assertEqual(row['returncode'],0);self.assertTrue(row['cleanup_complete'])
        self.assertEqual(self.socket.connects,[('127.0.0.1',15937)]);self.assertIn(b'host:transport-id:7',self.socket.sent)
        self.assertIn(b'shell,v2,raw:getprop sys.boot_completed',self.socket.sent)
        self.assertEqual(self.socket.sent[-5:],packet(4,b''));self.assertEqual(len(self.proof_calls),2)
        self.assertEqual(Path(row['stdout']['path']).read_bytes(),raw);self.assertEqual(Path(row['stderr']['path']).read_bytes(),b'')

    def test_target_is_copied_and_immutable_even_for_same_transport(self):
        owner=self.owner();owner.target['transport_id']=99;self.assertEqual(owner.target,{'transport_id':7})
        with self.assertRaises(c.ClientRefused):owner.target={'transport_id':7}
        self.poisoned(owner);self.factory.assert_not_called()

    def test_bad_operation_legacy_adb_and_wrong_target_never_connect(self):
        for argv in(['adb','-P','5037','shell','id'],['host:transport-id:8'],['sh','-c','id']):
            owner=self.owner()
            with self.assertRaises(c.ClientRefused):owner.shell(argv,'bad')
            self.poisoned(owner)
        self.factory.assert_not_called()

    def test_expired_stopped_changed_owner_or_deadline_extension_refuses_before_socket(self):
        for mode in('expired','guard','descriptor','extension'):
            self.guard_fail=False;self.lease.descriptor=copy.deepcopy(self.descriptor);self.clock=100
            owner=self.owner()
            if mode=='expired':self.clock=owner.until
            elif mode=='guard':self.guard_fail=True
            elif mode=='descriptor':self.lease.descriptor['guest']['pid']=999
            else:owner.until+=1
            with self.assertRaises(c.ClientRefused):owner.shell(['getprop','sys.boot_completed'],'boot')
            self.poisoned(owner)
        self.factory.assert_not_called()

    def test_preproof_refusal_has_no_dispatch_record_and_closes_only_own_socket(self):
        owner=self.owner();self.proof_fail.add('before')
        with self.assertRaises(c.ClientRefused):owner.shell(['getprop','sys.boot_completed'],'boot')
        self.assertEqual(owner.count,0);self.assertEqual(self.socket.sent,b'');self.assertTrue(self.socket.closed)
        self.assertEqual(list(owner.directory.iterdir()),[]);self.poisoned(owner)

    def test_full_budget_charges_preproof_cost_before_first_target_frame(self):
        owner=self.owner(seconds=20);self.proof_cost['before']=6
        with self.assertRaises(c.ClientRefused):owner.shell(['getprop','sys.boot_completed'],'boot',seconds=15,full_budget=True)
        self.assertEqual(owner.count,0);self.assertEqual(self.socket.sent,b'');self.poisoned(owner)

    def test_failed_postproof_retains_actual_exit_and_binary_measurement(self):
        owner=self.owner();self.proof_fail.add('after')
        with self.assertRaises(c.ClientRefused):owner.shell(['getprop','sys.boot_completed'],'boot')
        row=self.row(owner);self.assertEqual(row['status'],'completed');self.assertEqual(row['returncode'],0)
        self.assertFalse(row['client_qualified']);self.assertIsNone(row['server_after']);self.assertTrue(row['socket_closed'])
        self.assertEqual(Path(row['stdout']['path']).read_bytes(),b'hello\0\x1a\xff\r\n');self.poisoned(owner)

    def test_nonzero_exit_retains_output_and_postproof_without_claiming_success(self):
        self.socket=FakeSocket(self.response(code=7));owner=self.owner()
        with self.assertRaises(c.ClientRefused):owner.shell(['getprop','sys.boot_completed'],'boot')
        row=self.row(owner);self.assertEqual(row['returncode'],7);self.assertEqual(row['status'],'completed')
        self.assertIsNotNone(row['server_after']);self.assertFalse(row['client_qualified']);self.poisoned(owner)

    def test_partial_output_and_truncation_are_truthful_not_completed(self):
        self.socket=FakeSocket(b'OKAYOKAY'+bytes([1])+struct.pack('<I',10)+b'abc');owner=self.owner()
        with self.assertRaises(c.ClientRefused):owner.shell(['getprop','sys.boot_completed'],'boot')
        row=self.row(owner);self.assertEqual(Path(row['stdout']['path']).read_bytes(),b'abc');self.assertIsNone(row['returncode'])
        self.assertFalse(row['client_qualified']);self.assertIsNone(row['server_after']);self.poisoned(owner)

    def test_cancellation_retains_partial_stdout_and_known_socket_close(self):
        self.socket=FakeSocket(b'OKAYOKAY'+packet(1,b'measured\0\x1a'));self.socket.eof_error=KeyboardInterrupt()
        owner=self.owner()
        with self.assertRaises(c.ClientRefused):owner.shell(['getprop','sys.boot_completed'],'boot')
        row=self.row(owner);self.assertEqual(row['status'],'cancelled');self.assertIsNone(row['returncode'])
        self.assertEqual(Path(row['stdout']['path']).read_bytes(),b'measured\0\x1a');self.assertTrue(row['socket_closed']);self.poisoned(owner)

    def test_sender_that_does_not_join_cannot_qualify_completed_protocol(self):
        owner=self.owner()
        with patch.object(InlineSender,'stays_alive',True):
            with self.assertRaises(c.ClientRefused):owner.shell(['getprop','sys.boot_completed'],'boot')
        row=self.row(owner);self.assertFalse(row['sender_joined']);self.assertFalse(row['cleanup_complete'])
        self.assertFalse(row['client_qualified']);self.poisoned(owner)

    def test_real_exit_and_eof_remain_completed_when_sender_closure_is_unknown(self):
        owner=self.owner()
        with patch.object(InlineSender,'stays_alive',True):
            with self.assertRaises(c.ClientRefused):owner.shell(['getprop','sys.boot_completed'],'boot')
        row=self.row(owner);self.assertEqual(row['returncode'],0)
        self.assertEqual(Path(row['stdout']['path']).read_bytes(),b'hello\0\x1a\xff\r\n')
        self.assertEqual(row['status'],'completed','actual exit and EOF are distinct from sender cleanup qualification')
        self.assertFalse(row['sender_joined']);self.assertFalse(row['cleanup_complete']);self.assertFalse(row['client_qualified']);self.poisoned(owner)

    def test_changed_input_binding_refuses_before_any_socket_or_target_frame(self):
        owner=self.owner();self.probe.write_bytes(b'changed original synthetic probe')
        with self.assertRaises(c.ClientRefused):
            owner.stream(['run-as',c.contract.APP,'--user','0','dd','of=no_backup/original-author-transfer-probe-v1.bin','bs=65536'],
                         self.admitted['artifacts']['probe'],'probe',seconds=15)
        self.factory.assert_not_called();self.assertEqual(owner.count,0);self.poisoned(owner)

    def test_sender_start_or_socket_close_failure_poison_and_retain_measurement(self):
        for start_failure,close_failure in((True,False),(False,True)):
            self.socket=FakeSocket(self.response(),close_error=close_failure);owner=self.owner()
            with patch.object(InlineSender,'fail_start',start_failure):
                with self.assertRaises(c.ClientRefused):owner.shell(['getprop','sys.boot_completed'],'boot')
            row=self.row(owner);self.assertFalse(row['client_qualified'])
            if close_failure:self.assertEqual(row['status'],'completed');self.assertFalse(row['cleanup_complete'])
            self.poisoned(owner)

    def test_original_probe_stream_uses_binary_packets_and_bound_input_digest(self):
        owner=self.owner();owner.stream(['run-as',c.contract.APP,'--user','0','dd','of=no_backup/original-author-transfer-probe-v1.bin','bs=65536'],
                                      self.admitted['artifacts']['probe'],'probe',seconds=15)
        row=self.row(owner);self.assertEqual(row['stdin_bytes'],len(self.payload));self.assertTrue(row['stdin_complete'])
        self.assertEqual(row['stdin_sha256'],hashlib.sha256(self.payload).hexdigest());self.assertIn(packet(0,self.payload),self.socket.sent)

    def test_import_once_is_admission_wide_across_two_sdk_sessions(self):
        argv=['am','instrument','-w','-r','-e','class',c.contract.CLASS+'#'+c.contract.METHODS[0],c.contract.TEST+'/androidx.test.runner.AndroidJUnitRunner']
        first=self.owner();first.shell(argv,'import')
        self.socket=FakeSocket(self.response());second=self.owner()
        with self.assertRaises(c.ClientRefused):second.shell(argv,'import')
        self.assertEqual(second.count,0);self.assertEqual(self.socket.sent,b'');self.poisoned(second)

    def test_same_size_changed_probe_keeps_actual_unqualified_stream_measurement(self):
        owner=self.owner();changed=b'X'+self.payload[1:]
        self.assertEqual(len(changed),len(self.payload));self.assertNotEqual(hashlib.sha256(changed).hexdigest(),self.admitted['artifacts']['probe']['sha256'])
        def mutate(context):
            if context['phase']=='before':self.probe.write_bytes(changed)
        self.on_proof=mutate
        with self.assertRaises(c.ClientRefused):
            owner.stream(['run-as',c.contract.APP,'--user','0','dd','of=no_backup/original-author-transfer-probe-v1.bin','bs=65536'],
                         self.admitted['artifacts']['probe'],'probe',seconds=15)
        self.assertIn(packet(0,changed),self.socket.sent);self.assertEqual(self.socket.sent[-5:],packet(4,b''))
        self.assertTrue((owner.directory/'command-0001.json').is_file(),'actual measured stream must have an unqualified JSON record')
        row=self.row(owner);self.assertFalse(row['client_qualified']);self.assertEqual(row['status'],'completed');self.assertEqual(row['returncode'],0)
        self.assertEqual(row['stdin_bytes'],len(changed));self.assertEqual(row['stdin_sha256'],hashlib.sha256(changed).hexdigest())
        self.assertTrue(row['stdin_complete']);self.assertIsNone(row['server_after']);self.poisoned(owner)


if __name__=='__main__':unittest.main()
