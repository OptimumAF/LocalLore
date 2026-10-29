"""Original held-socket ownership fixtures and a fake backend; no IO probe.

Unknown client state is preserved. Only exact server ESTABLISHED5, held resource
identity and the fixed finite exchange can complete this narrowly scoped proof.
These fixtures do not authenticate any real server, SDK, device or execution.
Copyright 2026 LocalLore contributors. SPDX-License-Identifier: Apache-2.0
"""
from collections import Counter
import copy
import hashlib
import ipaddress
import json
import struct
import unittest

from benchmarks import adb_held_socket as t

SERVER_PID, CLIENT_PID, CLIENT_PORT = 8101, 8102, 42001
VERSION = '0029'
REPLY = b'OKAY0004'+VERSION.encode('ascii')
REPORT_KEYS = {'version','protocol','feature_acceptance','admission','status','reason','stages',
               'request_hex','request_sent','response_hex','response_complete','ownership_verified',
               'client_raw_state','elapsed_ms','socket_closed','process_handles_closed'}


def admission():
    path='C:\\Synthetic\\platform-tools\\adb.exe'
    return dict(version=1,protocol='adb-held-socket-server-owner-v1',
                server=dict(pid=SERVER_PID,creation_filetime=123456789,executable=path),
                adb_file=dict(path=path,bytes=9,sha256='a'*64,identity=[3,7,9,100,101]),
                candidates=[dict(family=2,address='127.0.0.1',port=5037,pid=SERVER_PID,scope_id=0)],
                expected_version=VERSION)


def wire_port(port):
    return int.from_bytes(port.to_bytes(2,'big'),'little')


def row4(*, local='127.0.0.1', local_port=5037, remote='0.0.0.0', remote_port=0,
         state=0, pid=SERVER_PID):
    address=lambda value:int.from_bytes(ipaddress.IPv4Address(value).packed,'little')
    return struct.pack('<6I',state,address(local),wire_port(local_port),
                       address(remote),wire_port(remote_port),pid)


def row6(*, local='::1', local_port=5037, remote='::', remote_port=0,
         state=0,pid=SERVER_PID,scope_id=0):
    scope=int.from_bytes(scope_id.to_bytes(4,'big'),'little')
    return struct.pack('<16sII16sIIII',ipaddress.IPv6Address(local).packed,scope,wire_port(local_port),
                       ipaddress.IPv6Address(remote).packed,0,wire_port(remote_port),state,pid)


def capture(family,*rows,allocated=None,table_class=5):
    raw=struct.pack('<I',len(rows))+b''.join(rows)
    return t.TableCapture(family,raw,len(raw) if allocated is None else allocated,table_class)


def snapshot(rows=(),*,v6=(),abi=True):
    return t.Snapshot((capture(2,*rows),capture(23,*v6)),abi_checked=abi)


def server_row(**changes):
    return row4(remote='127.0.0.1',remote_port=CLIENT_PORT,state=5,**changes)


def client_row(state=0,**changes):
    return row4(local_port=CLIENT_PORT,remote='127.0.0.1',remote_port=5037,
                pid=CLIENT_PID,state=state,**changes)


class FakeBackend:
    """Returns only original synthetic values, recording calls before injection."""
    def __init__(self,client_state=0,server_state=5,chunks=None):
        self.clock=100.0
        self.calls=[]
        self.counts=Counter()
        self.errors={}
        self.jumps={}
        self.sent=[]
        self.recv_limits=[]
        self.chunks=[REPLY,b''] if chunks is None else list(chunks)
        self.empty_error=None
        self.closed=False
        value=admission()
        bracket=dict(server=value['server'],client=dict(pid=CLIENT_PID,creation_filetime=223456789,
                     executable='D:\\Synthetic\\client.exe'),adb_file=value['adb_file'],held_processes_alive=True)
        self.brackets=[copy.deepcopy(bracket) for _ in range(3)]
        endpoint=dict(handle=77,socket_id=88,local_address='127.0.0.1',local_port=CLIENT_PORT,
                      peer_address='127.0.0.1',peer_port=5037)
        self.endpoints=[copy.deepcopy(endpoint) for _ in range(3)]
        self.snapshots=[snapshot((row4(),)),
                        snapshot((row4(),row4(remote='127.0.0.1',remote_port=CLIENT_PORT,
                                              state=server_state),client_row(client_state))),
                        snapshot((row4(),server_row(),client_row(client_state)))]
        self.close_result=dict(socket_closed=True,process_handles_closed=True)

    def now(self):
        self.clock+=0.0001
        return self.clock

    def call(self,name):
        ordinal=self.counts[name]
        self.counts[name]+=1
        self.calls.append(name)
        self.clock+=self.jumps.get((name,ordinal),0)
        if (name,ordinal) in self.errors:
            raise self.errors[(name,ordinal)]
        return ordinal

    def open(self,value,deadline):
        self.call('open')

    def bracket(self,value,deadline):
        return copy.deepcopy(self.brackets[self.call('bracket')])

    def snapshot(self,deadline):
        return self.snapshots[self.call('snapshot')]

    def connect(self,deadline):
        self.call('connect')

    def endpoint(self,deadline):
        return copy.deepcopy(self.endpoints[self.call('endpoint')])

    def send(self,data,deadline):
        self.sent.append(data)
        self.call('send')

    def recv(self,limit,deadline):
        self.recv_limits.append(limit)
        self.call('recv')
        if self.chunks:
            value=self.chunks.pop(0)
            if isinstance(value,BaseException):
                raise value
            return value
        if self.empty_error is not None:
            raise self.empty_error
        return b''

    def close(self):
        self.closed=True
        self.call('close')
        return copy.deepcopy(self.close_result)


class HeldSocketAdmissionTests(unittest.TestCase):
    def test_exact_admission_is_deep_copied_without_IO(self):
        value=admission()
        copied=t.validate_admission(value)
        self.assertEqual(copied,value)
        self.assertIsNot(copied,value)
        copied['server']['pid']+=1
        copied['adb_file']['identity'][1]+=1
        copied['candidates'][0]['pid']+=1
        self.assertEqual(value,admission())

    def test_admission_closed_fields_types_hashes_and_expected_version(self):
        for key,bad in (('version',True),('protocol','legacy-LISTEN2'),('expected_version','002A'),
                        ('expected_version','029'),('expected_version',None),('extra',1)):
            value=admission();value[key]=bad
            with self.subTest(key=key),self.assertRaises(t.ProbeRefused):
                t.validate_admission(value)
        for field,bad in (('pid',True),('pid',0),('creation_filetime',0),('executable','relative-adb.exe')):
            value=admission();value['server'][field]=bad
            with self.subTest(field=field),self.assertRaises(t.ProbeRefused):
                t.validate_admission(value)
        for field,bad in (('path','C:\\Other\\adb.exe'),('bytes',True),('sha256','A'*64),
                          ('identity',[3,7,8,100,101]),('identity',[3,7,9,100]),('identity',[3,7,9,True,101])):
            value=admission();value['adb_file'][field]=bad
            with self.subTest(field=field),self.assertRaises(t.ProbeRefused):
                t.validate_admission(value)

    def test_candidates_are_exact_loopback_roster_with_ipv4_required(self):
        ipv6=dict(family=23,address='::1',port=5037,pid=SERVER_PID,scope_id=0)
        good=admission();good['candidates'].append(ipv6)
        self.assertEqual(t.validate_admission(good),good)
        for replacement in ([],[ipv6],[ipv6,admission()['candidates'][0]],
                            admission()['candidates']*2):
            value=admission();value['candidates']=replacement
            with self.subTest(replacement=replacement),self.assertRaises(t.ProbeRefused):
                t.validate_admission(value)
        for field,bad in (('family',True),('address','0.0.0.0'),('port',5038),('pid',SERVER_PID+1),
                          ('scope_id',1),('raw_state',0)):
            value=admission();value['candidates'][0][field]=bad
            with self.subTest(field=field),self.assertRaises(t.ProbeRefused):
                t.validate_admission(value)


class HeldSocketProbeTests(unittest.TestCase):
    def refused(self,backend,*,sent=False,reason=None):
        value=t.probe(backend,admission())
        self.assertEqual(set(value),REPORT_KEYS)
        self.assertEqual(value['status'],'refused')
        self.assertIs(value['feature_acceptance'],False)
        self.assertIs(value['request_sent'],sent)
        self.assertFalse(t.report_verified(value,admission()))
        if reason is not None:
            self.assertEqual(value['reason'],reason)
        self.assertTrue(backend.closed)
        self.assertEqual(backend.counts['close'],1)
        return value

    def test_one_exact_owned_exchange_without_poll_reconnect_or_resend(self):
        backend=FakeBackend()
        value=t.probe(backend,admission())
        self.assertEqual(set(value),REPORT_KEYS)
        self.assertEqual(value['status'],'verified')
        self.assertIsNone(value['reason'])
        self.assertIs(value['ownership_verified'],True)
        self.assertIs(value['response_complete'],True)
        self.assertIs(value['socket_closed'],True)
        self.assertIs(value['process_handles_closed'],True)
        self.assertIs(value['feature_acceptance'],False)
        self.assertEqual(value['request_hex'],t.REQUEST.hex())
        self.assertEqual(value['response_hex'],REPLY.hex())
        self.assertEqual(backend.sent,[b'000Chost:version'])
        self.assertEqual(backend.calls,['open','bracket','snapshot','connect','endpoint','snapshot',
                         'endpoint','bracket','send','recv','recv','endpoint','bracket','snapshot','close'])
        self.assertEqual([s['stage'] for s in value['stages']],['initial','connected','presend','send_attempt','final'])
        self.assertTrue(t.report_verified(value,admission()))

    def test_all_client_DWORD_states_preserve_exact_value_with_same_ownership_outcome(self):
        for state in (0,1,2,3,5,12,255,4294967295):
            backend=FakeBackend(client_state=state)
            value=t.probe(backend,admission())
            with self.subTest(state=state):
                self.assertEqual(value['status'],'verified')
                self.assertEqual(value['client_raw_state'],state)
                self.assertTrue(t.report_verified(value,admission()))
                self.assertEqual(backend.counts['snapshot'],3)
                self.assertEqual(backend.counts['send'],1)

    def test_every_server_state_other_than5_refuses_before_send(self):
        for state in tuple(x for x in range(13) if x!=5)+(255,4294967295):
            backend=FakeBackend(server_state=state)
            with self.subTest(state=state):
                self.refused(backend)
                self.assertEqual(backend.sent,[])
                self.assertEqual(backend.counts['snapshot'],2)

    def test_missing_duplicate_foreign_and_nonreciprocal_connection_rows_refuse(self):
        for mode in ('no-server','no-client','duplicate-server','duplicate-client','foreign-server',
                     'foreign-client','wrong-server-peer','wrong-client-peer'):
            backend=FakeBackend()
            rows=[row4(),server_row(),client_row()]
            if mode=='no-server': del rows[1]
            elif mode=='no-client': rows.pop()
            elif mode=='duplicate-server': rows.append(server_row())
            elif mode=='duplicate-client': rows.append(client_row())
            elif mode=='foreign-server': rows[1]=server_row(pid=SERVER_PID+1)
            elif mode=='foreign-client': rows[2]=row4(local_port=CLIENT_PORT,remote='127.0.0.1',
                                                    remote_port=5037,pid=CLIENT_PID+1)
            elif mode=='wrong-server-peer': rows[1]=row4(remote='127.0.0.1',remote_port=CLIENT_PORT+1,state=5)
            else: rows[2]=row4(local_port=CLIENT_PORT,remote='127.0.0.1',remote_port=5038,pid=CLIENT_PID)
            backend.snapshots[1]=snapshot(rows)
            with self.subTest(mode=mode):
                self.refused(backend)
                self.assertEqual(backend.sent,[])

    def test_candidate_view_rejects_wildcard_ipv6_foreign_and_duplicate_rows(self):
        for extra in (row4(local='0.0.0.0'),row4(local='192.0.2.1'),row4(pid=SERVER_PID+1),row4()):
            backend=FakeBackend();backend.snapshots[0]=snapshot((row4(),extra))
            self.refused(backend)
            self.assertEqual(backend.counts['connect'],0)
        backend=FakeBackend();backend.snapshots[0]=snapshot((row4(),),v6=(row6(),))
        self.refused(backend)
        self.assertEqual(backend.counts['connect'],0)

    def test_each_snapshot_is_complete_bounded_owner_pid_all_with_checked_ABI(self):
        bad=[t.Snapshot((capture(23),capture(2,row4()))),
             t.Snapshot((capture(2,row4()),)),
             t.Snapshot((capture(2,row4()),capture(2))),
             t.Snapshot([capture(2,row4()),capture(23)]),
             snapshot((row4(),),abi=False),
             t.Snapshot((capture(2,row4(),table_class=3),capture(23))),
             t.Snapshot((t.TableCapture(2,b'\x01\x00\x00\x00',4),capture(23))),
             t.Snapshot((capture(2,row4(),allocated=3),capture(23))),
             t.Snapshot((capture(2,row4(),allocated=1048577),capture(23)))]
        for sample in bad:
            backend=FakeBackend();backend.snapshots[0]=sample
            with self.subTest(sample=repr(sample)[:80]):
                self.refused(backend)
                self.assertEqual(backend.counts['connect'],0)

    def test_handle_object_or_endpoint_change_refuses_without_rejoining_or_retry(self):
        for index in (1,2):
            for field,bad in (('handle',78),('socket_id',89),('local_port',CLIENT_PORT+1),
                              ('local_address','192.0.2.1'),('peer_address','192.0.2.2'),('peer_port',5038)):
                backend=FakeBackend();backend.endpoints[index][field]=bad
                with self.subTest(index=index,field=field):
                    self.refused(backend,sent=index==2)
                    self.assertEqual(backend.counts['connect'],1)
                    self.assertLessEqual(backend.counts['send'],1)

    def test_process_and_file_replacement_refuse_in_each_identity_bracket(self):
        for index in (1,2):
            for mode in ('server-pid','server-creation','client-creation','file-identity','file-hash','held-dead'):
                backend=FakeBackend();bracket=backend.brackets[index]
                if mode=='server-pid': bracket['server']['pid']+=1
                elif mode=='server-creation': bracket['server']['creation_filetime']+=1
                elif mode=='client-creation': bracket['client']['creation_filetime']+=1
                elif mode=='file-identity': bracket['adb_file']['identity'][1]+=1
                elif mode=='file-hash': bracket['adb_file']['sha256']='b'*64
                else: bracket['held_processes_alive']=False
                with self.subTest(index=index,mode=mode):
                    self.refused(backend,sent=index==2)

    def test_backend_cannot_replace_the_preserved_admission_during_open(self):
        class MutatingBackend(FakeBackend):
            def open(self,value,deadline):
                super().open(value,deadline)
                value['adb_file']['identity'][1]+=1
                for bracket in self.brackets:
                    bracket['adb_file']=copy.deepcopy(value['adb_file'])

        original=admission()
        backend=MutatingBackend()
        value=t.probe(backend,original)
        self.assertEqual(original,admission())
        self.assertEqual(value['admission'],admission())
        self.assertEqual(value['status'],'refused')
        self.assertEqual(backend.sent,[])
        self.assertTrue(backend.closed)

    def test_backend_cannot_mutate_expected_file_pin_in_presend_bracket(self):
        class MutatingBackend(FakeBackend):
            def bracket(self,value,deadline):
                index=self.call('bracket')
                if index==1:
                    value['adb_file']['identity'][1]+=1
                    for bracket in self.brackets[1:]:
                        bracket['adb_file']=copy.deepcopy(value['adb_file'])
                return copy.deepcopy(self.brackets[index])

        backend=MutatingBackend()
        value=t.probe(backend,admission())
        self.assertEqual(value['admission'],admission())
        self.assertEqual(value['status'],'refused')
        self.assertEqual(backend.sent,[])
        self.assertTrue(backend.closed)

    def test_post_exchange_candidate_change_remains_refused_after_actual_send(self):
        backend=FakeBackend();backend.snapshots[2]=snapshot((row4(),row4(local='0.0.0.0')))
        self.refused(backend,sent=True)
        self.assertEqual(backend.counts['snapshot'],3)
        self.assertEqual(backend.sent,[t.REQUEST])

    def test_fragmented_reply_requires_all_fixed_bytes_and_orderly_EOF(self):
        backend=FakeBackend(chunks=[b'O',b'K',b'AY0',b'004',b'002',b'9',b''])
        value=t.probe(backend,admission())
        self.assertEqual(value['status'],'verified')
        self.assertEqual(value['response_hex'],REPLY.hex())
        self.assertTrue(t.report_verified(value,admission()))
        self.assertTrue(all(type(limit) is int and 0<limit<=13 for limit in backend.recv_limits))
        self.assertEqual(backend.counts['send'],1)

    def test_wrong_status_length_hex_case_and_version_are_not_learned_or_repaired(self):
        for raw in (b'FAIL0004nope',b'OKAY00030029',b'OKAY000g0029',b'Okay00040029',
                    b'OKAY0004002a',b'OKAY0004002A',b'OKAY00040029x',b'\xffKAY00040029'):
            backend=FakeBackend(chunks=[raw,b''])
            with self.subTest(raw=raw):
                value=self.refused(backend,sent=True,reason='framing')
                self.assertFalse(value['response_complete'])
                self.assertEqual(backend.counts['send'],1)

    def test_partial_EOF_preserves_exact_partial_reply(self):
        backend=FakeBackend(chunks=[b'OKAY0004',b''])
        value=self.refused(backend,sent=True,reason='framing')
        self.assertEqual(value['response_hex'],b'OKAY0004'.hex())
        self.assertFalse(value['response_complete'])

    def test_missing_EOF_is_not_a_complete_response(self):
        backend=FakeBackend(chunks=[REPLY]);backend.empty_error=TimeoutError('synthetic timeout')
        # An early backend timeout is not evidence the total clock budget expired.
        value=self.refused(backend,sent=True,reason='backend')
        self.assertEqual(value['response_hex'],REPLY.hex())
        self.assertFalse(value['response_complete'])

    def test_missing_EOF_with_observed_exhausted_clock_retains_deadline_failure(self):
        backend=FakeBackend(chunks=[REPLY]);backend.empty_error=TimeoutError('synthetic timeout')
        backend.jumps[('recv',1)]=4.0
        value=self.refused(backend,sent=True,reason='deadline')
        self.assertEqual(value['response_hex'],REPLY.hex())
        self.assertFalse(value['response_complete'])
        self.assertTrue(value['socket_closed'])
        self.assertTrue(value['process_handles_closed'])

    def test_one_total_deadline_is_not_reset_for_each_fragment(self):
        backend=FakeBackend(chunks=[b'O',b'K',b'A',b'Y',b'0',b'0',b'0',b'4',b'0',b'0',b'2',b'9',b''])
        for index in range(13): backend.jumps[('recv',index)]=0.6
        value=self.refused(backend,sent=True,reason='deadline')
        self.assertLess(backend.counts['recv'],13)
        self.assertLessEqual(len(bytes.fromhex(value['response_hex'])),13)

    def test_expired_presend_guard_sends_nothing(self):
        backend=FakeBackend();backend.jumps[('snapshot',1)]=4.0
        self.refused(backend,reason='deadline')
        self.assertEqual(backend.sent,[])

    def test_intermediate_clock_rollback_refuses_even_above_initial_time(self):
        backend=FakeBackend()
        backend.jumps[('open',0)]=0.5
        backend.jumps[('endpoint',1)]=-0.1
        self.refused(backend,reason='deadline')
        self.assertEqual(backend.sent,[])

    def test_cancellation_preserves_partial_response_and_attempts_close(self):
        for error in (InterruptedError('synthetic cancel'),KeyboardInterrupt()):
            backend=FakeBackend(chunks=[b'OKAY',error])
            with self.subTest(error=type(error).__name__):
                value=self.refused(backend,sent=True,reason='cancelled')
                self.assertEqual(value['response_hex'],b'OKAY'.hex())

    def test_send_exception_preserves_attempt_without_claiming_zero_transmitted_bytes(self):
        backend=FakeBackend();backend.errors[('send',0)]=OSError('private synthetic error')
        value=self.refused(backend,reason='backend')
        self.assertEqual(backend.sent,[t.REQUEST])
        self.assertIn('send_attempt',[stage['stage'] for stage in value['stages']])
        self.assertTrue(value['ownership_verified'])
        self.assertNotIn('private synthetic error',json.dumps(value))

    def test_cleanup_failure_never_leaves_a_verified_report(self):
        for result in (dict(socket_closed=False,process_handles_closed=True),
                       dict(socket_closed=True,process_handles_closed=False),
                       dict(socket_closed=1,process_handles_closed=True),
                       dict(socket_closed=True),None):
            backend=FakeBackend();backend.close_result=result
            with self.subTest(result=result):
                self.refused(backend,sent=True,reason='cleanup')
        backend=FakeBackend();backend.errors[('close',0)]=OSError('private close error')
        value=self.refused(backend,sent=True,reason='cleanup')
        self.assertNotIn('private close error',json.dumps(value))

    def test_backend_error_is_fixed_and_never_echoes_provider_text(self):
        backend=FakeBackend();backend.errors[('snapshot',0)]=RuntimeError('PRIVATE fake path / not authority')
        value=self.refused(backend,reason='backend')
        self.assertNotIn('PRIVATE',json.dumps(value))
        self.assertEqual(backend.counts['connect'],0)

    def test_report_verifier_is_readonly_and_rejects_forged_success_fields(self):
        value=t.probe(FakeBackend(),admission())
        before=copy.deepcopy(value)
        self.assertTrue(t.report_verified(value,admission()))
        self.assertEqual(value,before)
        for field,bad in (('version',True),('protocol','legacy-LISTEN2'),('feature_acceptance',True),
                          ('status','refused'),('reason','backend'),('ownership_verified',False),
                          ('client_raw_state',5),('request_sent',False),('response_complete',False),
                          ('socket_closed',False),('process_handles_closed',False),('response_hex','00')):
            changed=copy.deepcopy(value);changed[field]=bad
            with self.subTest(field=field):
                self.assertFalse(t.report_verified(changed,admission()))
        changed=admission();changed['expected_version']='002a'
        self.assertFalse(t.report_verified(value,changed))

    def test_report_verifier_requires_exact_stage_order_and_snapshot_byte_binding(self):
        value=t.probe(FakeBackend(),admission())
        for mode in ('missing','reordered','raw-hash'):
            changed=copy.deepcopy(value)
            if mode=='missing': changed['stages'].pop()
            elif mode=='reordered': changed['stages'].reverse()
            else:
                rows=changed['stages'][2]['snapshot']['rows']
                rows[0]['raw_sha256']='0'*64
            with self.subTest(mode=mode):
                self.assertFalse(t.report_verified(changed,admission()))


if __name__=='__main__':
    unittest.main()
