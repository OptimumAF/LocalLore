"""Original pre-guest exchange guard regression with synthetic clocks/bytes.

No socket, process, native TCP, authentication, SDK or device operation occurs.
"""
import copy
import ipaddress
import struct
from types import SimpleNamespace
import unittest
from unittest.mock import patch

from benchmarks import owned_target_owner as target
from benchmarks import isolated_adb_owner as primitive
from benchmarks.adb_held_socket import TableCapture


PORT=15937
LOCAL=43261
SERVER=dict(pid=9101,creation_filetime=1109101,executable='C:\\Synthetic\\adb.exe')
WORKER=dict(pid=9102,creation_filetime=1109102,executable='C:\\Synthetic\\python.exe')


def pin(name):return dict(path='D:\\Synthetic\\initial-guard\\'+name,bytes=17,sha256='a'*64)


def raw_row(local,lp,remote,rp,state,pid):
    address=lambda value:int.from_bytes(ipaddress.IPv4Address(value).packed,'little')
    port=lambda value:int.from_bytes(value.to_bytes(2,'big'),'little')
    return struct.pack('<6I',state,address(local),port(lp),address(remote),port(rp),pid)


class Clock:
    def __init__(self):self.value=0.0
    def advance(self,value):self.value+=value
    def __call__(self):return self.value


class Api:
    def __init__(self,events):self.events=events;self.handles={};self.next_handle=700;self.closed=[];self.identity_changed=False
    def open_process(self,pid):
        self.next_handle+=1;self.handles[self.next_handle]=copy.deepcopy(SERVER if pid==SERVER['pid']else WORKER);return self.next_handle
    def identity(self,handle):
        value=copy.deepcopy(self.handles[handle])
        if self.identity_changed:value['creation_filetime']+=1
        return value
    def alive(self,handle):return True
    def close_handle(self,handle):self.closed.append(handle);self.handles.pop(handle);return True
    def capture(self,family):
        self.events.append('table-'+str(family))
        if family==23:return TableCapture(23,struct.pack('<I',0),4)
        # Original opaque states, never used to select ownership roles.
        rows=[raw_row('127.0.0.1',PORT,'0.0.0.0',0,0,SERVER['pid']),
              raw_row('127.0.0.1',PORT,'127.0.0.1',LOCAL,0,SERVER['pid']),
              raw_row('127.0.0.1',LOCAL,'127.0.0.1',PORT,1,WORKER['pid'])]
        raw=struct.pack('<I',len(rows))+b''.join(rows);return TableCapture(2,raw,len(raw))


class Runtime:
    def __init__(self,*,fail_full=None,source_change=False):
        self.clock=Clock();self.events=[];self.api=Api(self.events);self.processes=primitive.ProcessHandles(self.api)
        self.processes.add(SERVER['pid'],SERVER);self.processes.add(WORKER['pid'],WORKER)
        self.worker=copy.deepcopy(WORKER);self.server=copy.deepcopy(SERVER);self.until=50.0
        self.binding=pin('target-admission-v1.json');self.request_binding=pin('target-request-v1.json')
        self.server_binding=pin('server-admission-v1.json');self.sources=[pin('source.py')];self.tools=[pin('tool.exe')]
        self.admission=dict(server=dict(sources=self.sources,tools=self.tools))
        self.full_calls=0;self.fast_calls=0;self.auth_calls=0;self.checked=[];self.fail_full=fail_full
        self.change_on_connect=source_change;self.source_changed=False;self.auth_failed=False
        self.auth=SimpleNamespace(check=self.auth_check)
    def auth_check(self):
        self.auth_calls+=1;self.clock.advance(.001);self.events.append('auth')
        if self.auth_failed:raise target.OwnerRefused('auth')
        return dict(path='C:\\Synthetic\\.android\\adbkey',metadata={'identity':'original-metadata-only'})
    def fast_guard(self):
        self.fast_calls+=1;self.clock.advance(.001);self.events.append('fast')
        self.processes.guard()
    def guard(self):
        started=self.clock();self.full_calls+=1;self.events.append('full-'+str(self.full_calls))
        self.fast_guard();self.auth_check()
        # Total cost includes the mocked held/small/auth subchecks.
        self.clock.advance(.5-(self.clock()-started))
        if self.source_changed or self.full_calls==self.fail_full:raise target.OwnerRefused('source')
    def binding_check(self,value):
        self.checked.append(copy.deepcopy(value));self.clock.advance(.001);self.events.append('small-binding')
    def source_bindings(self):self.clock.advance(.001);self.events.append('source-metadata');return copy.deepcopy(self.sources)


class Socket:
    def __init__(self,runtime,*,kind='version',wire_cost=0.0,eof_at=None,mutate_anchor=False):
        self.r=runtime;self.handle=881;self.closed=False;self.sent=bytearray();self.connects=[]
        self.reply=bytearray(b'OKAY00040029'if kind=='version'else b'OKAY0000')
        self.wire_cost=wire_cost;self.eof_at=eof_at;self.mutate_anchor=mutate_anchor
    def fileno(self):return self.handle
    def getsockname(self):return('127.0.0.1',LOCAL)
    def getpeername(self):return('127.0.0.1',PORT)
    def setsockopt(self,*args):pass
    def bind(self,address):
        if address!=('127.0.0.1',0):raise AssertionError('unexpected address')
    def settimeout(self,value):
        if not 0<value<=3:raise AssertionError('deadline expanded')
    def connect(self,address):
        self.r.events.append('connect');self.connects.append(address)
        if self.r.change_on_connect:self.r.source_changed=True
        if self.mutate_anchor:self.handle+=1
    def send(self,raw):
        self.r.events.append('send');self.sent.extend(raw);return len(raw)
    def recv(self,size):
        if self.reply:
            count=min(size,3,len(self.reply));raw=bytes(self.reply[:count]);del self.reply[:count];return raw
        self.r.events.append('EOF')
        if self.eof_at is None:self.r.clock.advance(self.wire_cost)
        else:
            if self.eof_at<self.r.clock():raise AssertionError('fixture clock rollback')
            self.r.clock.value=self.eof_at
        return b''
    def close(self):self.closed=True;self.handle=-1;self.r.events.append('socket-close')


class InitialServerGuardTests(unittest.TestCase):
    def exchange(self,*,kind='version',wire_cost=0.0,eof_at=None,fail_full=None,source_change=False,mutate_anchor=False):
        runtime=Runtime(fail_full=fail_full,source_change=source_change)
        view=target._InitialServerView(runtime,runtime.server_binding)
        item=Socket(runtime,kind=kind,wire_cost=wire_cost,eof_at=eof_at,mutate_anchor=mutate_anchor)
        with patch.object(primitive.socket,'socket',return_value=item),patch.object(primitive.time,'monotonic',runtime.clock), \
             patch.object(primitive.os,'getpid',return_value=WORKER['pid']),patch.object(primitive.native,'_check_abi'), \
             patch.object(target.environment,'check_binding',side_effect=runtime.binding_check), \
             patch.object(target.server_contract,'source_bindings',side_effect=runtime.source_bindings):
            proof,failure=primitive._exchange(view,kind)
        return proof,failure,runtime,item,view

    def test_cheap_outer_guard_keeps_held_identity_auth_and_server_admission_binding(self):
        runtime=Runtime();view=target._InitialServerView(runtime,runtime.server_binding)
        with patch.object(target.environment,'check_binding',side_effect=runtime.binding_check):view.guard()
        self.assertEqual(runtime.full_calls,0);self.assertEqual(runtime.fast_calls,1);self.assertEqual(runtime.auth_calls,1)
        self.assertIn(runtime.server_binding,runtime.checked);self.assertLess(runtime.clock(),.01)

    def test_version_uses_exactly_three_full_brackets_before_connect_send_and_after_response(self):
        proof,failure,runtime,item,_=self.exchange()
        self.assertIsNone(failure);self.assertEqual(runtime.full_calls,3);self.assertGreaterEqual(runtime.fast_calls,5)
        events=runtime.events
        self.assertLess(events.index('full-1'),events.index('connect'))
        self.assertLess(events.index('connect'),events.index('full-2'));self.assertLess(events.index('full-2'),events.index('send'))
        self.assertLess(events.index('EOF'),events.index('full-3'));self.assertEqual(bytes(item.sent),b'000Chost:version')
        self.assertTrue(proof['response_complete']);self.assertTrue(proof['socket_closed']);self.assertTrue(proof['client_handle_closed'])
        self.assertEqual([proof['brackets'][name]['sources']for name in('before_connect','before_send','after_response')],[runtime.sources]*3)
        self.assertEqual([row['state']for row in proof['observations']['before_send']['rows']],[0,0,1])

    def test_empty_devices_reply_preserves_the_same_three_full_validation_brackets(self):
        proof,failure,runtime,item,_=self.exchange(kind='devices')
        self.assertIsNone(failure);self.assertEqual(runtime.full_calls,3);self.assertEqual(bytes(item.sent),b'000Ehost:devices-l')
        self.assertEqual(proof['response_hex'],b'OKAY0000'.hex());self.assertTrue(proof['response_complete'])

    def test_500ms_full_guards_plus_700ms_wire_fit_without_redundant_whole_target_hashes(self):
        proof,failure,runtime,_,_=self.exchange(wire_cost=.7)
        self.assertIsNone(failure);self.assertEqual(runtime.full_calls,3);self.assertLess(proof['elapsed_ms'],3000)
        self.assertTrue(proof['request_sent']);self.assertTrue(proof['response_complete'])

    def test_full_source_failure_before_either_connection_or_send_never_sends_a_request(self):
        for failed in(1,2):
            with self.subTest(full=failed):
                proof,failure,_,item,_=self.exchange(fail_full=failed)
                self.assertIsNotNone(failure);self.assertEqual(bytes(item.sent),b'');self.assertFalse(proof['request_sent'])
                self.assertTrue(proof['socket_closed']);self.assertTrue(proof['client_handle_closed'])

    def test_source_change_after_connect_is_detected_by_full_presend_bracket(self):
        proof,failure,runtime,item,_=self.exchange(source_change=True)
        self.assertIsNotNone(failure);self.assertTrue(runtime.source_changed);self.assertEqual(item.connects,[('127.0.0.1',PORT)])
        self.assertEqual(bytes(item.sent),b'');self.assertFalse(proof['request_sent']);self.assertIsNone(proof['brackets']['before_send'])

    def test_native_socket_anchor_change_still_refuses_before_send(self):
        proof,failure,_,item,_=self.exchange(mutate_anchor=True)
        self.assertIsNotNone(failure);self.assertEqual(bytes(item.sent),b'');self.assertFalse(proof['request_sent'])
        self.assertTrue(proof['socket_closed']);self.assertTrue(proof['client_handle_closed'])

    def test_complete_response_and_closure_at_3219ms_remain_a_deadline_refusal(self):
        proof,failure,_,item,_=self.exchange(eof_at=3.219)
        self.assertEqual(failure,'deadline');self.assertEqual(proof['elapsed_ms'],3219)
        self.assertTrue(proof['request_sent']);self.assertTrue(proof['response_complete']);self.assertTrue(proof['socket_closed'])
        self.assertTrue(proof['client_handle_closed']);self.assertEqual(bytes(item.sent),b'000Chost:version')

    def test_exact_three_second_exhaustion_is_not_relaxed_into_success(self):
        proof,failure,_,_,_=self.exchange(eof_at=3.0)
        self.assertEqual(failure,'deadline');self.assertEqual(proof['elapsed_ms'],3000);self.assertTrue(proof['response_complete'])
