"""Original SDK16 bridge supervisor/worker adversaries, all ports synthetic.

No test here starts a process/thread, touches a guest/ledger/key/image, uses
WindowsJob, or creates an applicable approval. Root alone executes integration.
Copyright 2026 LocalLore contributors. SPDX-License-Identifier: Apache-2.0
"""
import copy
from contextlib import ExitStack
import hashlib
import io
import json
from pathlib import Path
import sys
from types import SimpleNamespace
import unittest
from unittest.mock import Mock, patch

from scripts import knowledge_ui_fresh_contract as rules
from scripts import run_knowledge_ui_fresh as operator


def encoded(value):
    return json.dumps(value, sort_keys=True, separators=(',', ':')).encode()


def pin(path, value=None):
    raw=encoded(value if value is not None else {'synthetic':str(path)})
    return dict(path=str(path), bytes=len(raw), sha256=hashlib.sha256(raw).hexdigest())


class Flag:
    def __init__(self): self.value=False
    def set(self): self.value=True
    def is_set(self): return self.value


class Pipe:
    def __init__(self, graph, channel=None, data=b''):
        self.graph,self.channel,self.data=graph,channel,io.BytesIO(data)
        self.closed=False
    def read(self, limit):
        if self.graph.fault=='read' and self.channel==0: raise OSError('private simulated pipe failure')
        return self.data.read(limit)
    def write(self, data):
        self.graph.events.append('barrier');self.graph.stdin.extend(data)
        if self.graph.fault=='barrier': raise OSError('private simulated write failure')
        return len(data)
    def close(self):
        self.closed=True;self.graph.events.append(('pipe_close',self.channel))
        if self.graph.fault=='pipe_close' and self.channel==0: raise OSError('private simulated close failure')


class SupervisorPorts:
    """No real thread/process/file: actual supervisor receives bounded fake ports."""
    def __init__(self, fault=None):
        self.fault=fault;self.events=[];self.stdin=bytearray();self.threads=[]
        self.stdout=b'A\x1a\x00\r\n\xff';self.stderr=b'\x00E\r\n';self.raw=[bytearray(),bytearray()]
        self.request=pin(rules.LIVE/'worker-request-v1.json')
        self.worker=dict(pid=420,creation_filetime=1420,executable=sys.executable)
        self.child=SimpleNamespace(pid=420,returncode=0,stdin=Pipe(self),
            stdout=Pipe(self,0,self.stdout),stderr=Pipe(self,1,self.stderr),
            poll=self.poll,wait=self.wait,kill=self.kill)
        self.capture=SimpleNamespace(failed=Flag(),overflow=Flag(),append=self.append,close=self.capture_close)
        self.capture_closed=False;self.job_close_calls=0;self.killed=False;self.started=[]
        self.api=SimpleNamespace(env=SimpleNamespace(LiveOutput=self.make_capture,
            host=SimpleNamespace(WindowsJob=self.make_job),process_identity=self.identity,encoded=encoded))
    def make_capture(self, root): self.events.append('capture');return self.capture
    def make_job(self, pid):
        self.events.append('assign_job')
        if self.fault=='job': raise OSError('private simulated AssignProcessToJobObject failure')
        return SimpleNamespace(close=self.job_close)
    def job_close(self):
        self.events.append('job_close');self.job_close_calls+=1
        if self.fault=='job_close_raise': raise OSError('private simulated CloseHandle failure')
        return self.fault!='job_close_false'
    def identity(self, pid):
        self.events.append('identity')
        return dict(self.worker,executable='D:\\wrong-python.exe') if self.fault=='identity' else copy.deepcopy(self.worker)
    def save(self, path, value):
        self.events.append('started');self.started.append(copy.deepcopy(value));return pin(path,value)
    def append(self, channel, data):
        self.raw[channel].extend(data)
        if self.fault=='capture': self.capture.failed.set();return False
        if self.fault=='overflow': self.capture.overflow.set();return False
        return True
    def capture_close(self):
        self.events.append('capture_close');self.capture_closed=True
        if self.fault=='capture_close_raise': raise OSError('private simulated capture flush failure')
        return self.fault!='capture_close_false'
    def poll(self):
        self.events.append('poll')
        if self.fault=='cancel': raise KeyboardInterrupt()
        return self.child.returncode
    def wait(self, **kwargs):
        self.events.append('wait')
        if self.fault=='wait': raise OSError('private simulated wait failure')
        return self.child.returncode
    def kill(self): self.events.append('kill');self.killed=True
    def make_thread(self, target, args, daemon):
        graph=self
        class Reader:
            ident=None
            def start(self):
                graph.events.append('thread_start')
                if graph.fault=='thread_start': raise RuntimeError('private simulated Thread.start failure')
                self.ident=1;target(*args)
            def join(self, timeout):
                graph.events.append('join')
                if graph.fault=='join': raise RuntimeError('private simulated Thread.join failure')
            def is_alive(self):
                graph.events.append('alive')
                if graph.fault=='alive_query': raise RuntimeError('private simulated Thread.is_alive failure')
                return graph.fault=='stalled'
        value=Reader();self.threads.append(value);return value
    def __enter__(self):
        self.stack=ExitStack()
        self.stack.enter_context(patch.object(operator,'_parts',return_value=(rules,self.api)))
        self.stack.enter_context(patch.object(operator,'save',side_effect=self.save))
        self.stack.enter_context(patch.object(Path,'mkdir',side_effect=lambda *a,**k:self.events.append('mkdir')))
        self.stack.enter_context(patch.object(operator.subprocess,'Popen',side_effect=lambda *a,**k:self.spawn(a,k)))
        self.stack.enter_context(patch.object(operator.threading,'Thread',side_effect=self.make_thread))
        self.stack.enter_context(patch.object(operator.time,'monotonic',return_value=2500 if self.fault=='expired' else 101))
        self.stack.enter_context(patch.object(operator.time,'sleep',side_effect=AssertionError('Synthetic exited child must not sleep')))
        return self
    def spawn(self, args, kwargs): self.events.append('spawn');self.spawn_args=(args,kwargs);return self.child
    def __exit__(self,*args): return self.stack.__exit__(*args)
    def run(self): return operator._supervise(self.request,100)


class FreshSupervisorAdversaries(unittest.TestCase):
    def test_job_and_started_identity_precede_exact_binary_barrier(self):
        with SupervisorPorts() as g: value=g.run()
        self.assertEqual((value['status'],value['worker_returncode']),('child_exited',0))
        self.assertTrue(value['cleanup_complete']);self.assertTrue(value['output_capture_complete'])
        self.assertLess(g.events.index('assign_job'),g.events.index('started'))
        self.assertLess(g.events.index('started'),g.events.index('barrier'))
        self.assertEqual(bytes(g.stdin),operator.BARRIER+encoded(g.request))
        self.assertEqual(g.started,[dict(request=g.request,worker=g.worker)])
        self.assertEqual([bytes(x) for x in g.raw],[g.stdout,g.stderr])
        self.assertEqual(g.job_close_calls,1);self.assertTrue(g.capture_closed)
        self.assertEqual(g.spawn_args[0][0],[sys.executable,'-I','-S','-B',str(rules.OPERATOR),'_worker'])

    def test_failed_job_assignment_kills_only_fake_child_and_never_releases_barrier(self):
        with SupervisorPorts('job') as g: value=g.run()
        self.assertEqual(value['status'],'owner_failed');self.assertFalse(value['cleanup_complete'])
        self.assertTrue(g.killed);self.assertEqual(g.stdin,b'');self.assertEqual(g.started,[])
        self.assertEqual(g.job_close_calls,0)

    def test_bad_worker_image_or_thread_start_never_releases_barrier(self):
        for fault in ('identity','thread_start'):
            with self.subTest(fault=fault),SupervisorPorts(fault) as g: value=g.run()
            self.assertEqual(value['status'],'owner_failed');self.assertEqual(g.stdin,b'')
            self.assertEqual(g.job_close_calls,1)

    def test_false_or_raising_job_close_cannot_qualify_cleanup(self):
        for fault in ('job_close_false','job_close_raise'):
            with self.subTest(fault=fault),SupervisorPorts(fault) as g: value=g.run()
            self.assertEqual(value['status'],'child_exited');self.assertFalse(value['cleanup_complete'])
            self.assertEqual(g.job_close_calls,1);self.assertIn('wait',g.events)
            self.assertTrue(g.capture_closed)

    def test_capture_read_append_and_overflow_refuse_terminal_success(self):
        for fault,status in (('read','capture_failed'),('capture','capture_failed'),('overflow','output_limit')):
            with self.subTest(fault=fault),SupervisorPorts(fault) as g: value=g.run()
            self.assertEqual(value['status'],status);self.assertFalse(value['output_capture_complete'])
            self.assertEqual(g.job_close_calls,1)
            if fault!='overflow':self.assertFalse(value['cleanup_complete'])

    def test_capture_close_false_or_exception_stays_unknown(self):
        for fault in ('capture_close_false','capture_close_raise'):
            with self.subTest(fault=fault),SupervisorPorts(fault) as g: value=g.run()
            self.assertFalse(value['cleanup_complete']);self.assertFalse(value['output_capture_complete'])
            self.assertTrue(g.capture_closed);self.assertEqual(g.job_close_calls,1)

    def test_expiry_and_keyboard_cancellation_close_fake_owner_without_success_status(self):
        for fault,status in (('expired','expired'),('cancel','cancelled')):
            with self.subTest(fault=fault),SupervisorPorts(fault) as g: value=g.run()
            self.assertEqual(value['status'],status);self.assertEqual(g.job_close_calls,1)
            self.assertIn('wait',g.events)

    def test_wait_or_pipe_close_failure_cannot_claim_known_cleanup(self):
        for fault in ('wait','pipe_close'):
            with self.subTest(fault=fault),SupervisorPorts(fault) as g: value=g.run()
            self.assertFalse(value['cleanup_complete']);self.assertEqual(g.job_close_calls,1)
            self.assertTrue(g.capture_closed)

    def test_join_failure_keeps_reader_pipes_and_capture_open_and_unknown(self):
        with SupervisorPorts('join') as g: value=g.run()
        self.assertFalse(value['cleanup_complete']);self.assertFalse(value['output_capture_complete'])
        self.assertFalse(g.child.stdout.closed);self.assertFalse(g.child.stderr.closed)
        self.assertFalse(g.capture_closed);self.assertEqual(g.job_close_calls,1)

    def test_alive_query_exception_returns_unknown_instead_of_escaping_finally(self):
        with SupervisorPorts('alive_query') as g: value=g.run()
        self.assertFalse(value['cleanup_complete']);self.assertFalse(value['output_capture_complete'])
        self.assertFalse(g.child.stdout.closed);self.assertFalse(g.capture_closed)
        self.assertEqual(g.job_close_calls,1)

    def test_still_live_reader_is_not_closed_or_qualified(self):
        with SupervisorPorts('stalled') as g: value=g.run()
        self.assertFalse(value['cleanup_complete']);self.assertFalse(value['output_capture_complete'])
        self.assertFalse(g.child.stdout.closed);self.assertFalse(g.capture_closed)

    def test_barrier_write_failure_still_closes_owned_fake_job(self):
        with SupervisorPorts('barrier') as g: value=g.run()
        self.assertEqual(value['status'],'owner_failed');self.assertEqual(g.job_close_calls,1)
        self.assertTrue(g.capture_closed)


def synthetic_authority():
    return dict(version=1,scope='sdk16-fresh-prepare-and-one-knowledge-ui-run-v1',
        source_head=rules.SOURCE_HEAD,operator_head='7'*40,
        proposal=pin(rules.PROPOSAL),operator=pin(rules.OPERATOR),contract=pin(rules.CONTRACT),
        handoff=copy.deepcopy(rules.HANDOFF),ledger=pin(rules.REGISTRY/'ledger-v1.json'),
        allow_sdk_prepare=True,allow_one_boot=True,allow_model=False,allow_retirement=False,
        approval_reference='SYNTHETIC TEST METADATA, NOT HUMAN AUTHORITY',max_operation_seconds=2400)


class WorkerPorts:
    """In-memory immutable records; no operational import, write or OS identity call."""
    def __init__(self):
        self.records={};self.claims=[];self.authority=synthetic_authority();self.authority_pin=pin(rules.AUTHORITY,self.authority)
        self.parent=dict(pid=410,creation_filetime=1410,executable=sys.executable)
        self.worker=dict(pid=420,creation_filetime=1420,executable=sys.executable)
        attempt=dict(version=1,scope='sdk16-fresh-operation-attempt-v1',authority=self.authority_pin,
            **{k:copy.deepcopy(self.authority[k]) for k in ('handoff','operator','contract')},no_retry=True)
        self.attempt_pin=self.put(rules.ATTEMPT,attempt)
        request=dict(version=1,scope='sdk16-fresh-operation-worker-request-v1',authority=self.authority_pin,
            attempt=self.attempt_pin,parent=self.parent,started_monotonic=100)
        self.request_pin=self.put(rules.LIVE/'worker-request-v1.json',request)
        self.put(rules.LIVE/'worker-started-v1.json',dict(request=self.request_pin,worker=self.worker))
        self.api=SimpleNamespace(env=SimpleNamespace(decode_json=json.loads,binding=self.binding,process_identity=self.identity))
    def put(self,path,value): self.records[str(path)]=copy.deepcopy(value);return pin(path,value)
    def read(self,p,expected=None,maximum=None):
        if expected is not None: rules.need(Path(p['path'])==Path(expected),'test_expected_path')
        value=self.records[p['path']];rules.need(pin(p['path'],value)==p,'test_immutable_binding');return copy.deepcopy(value)
    def binding(self,path): return pin(path,self.records[str(path)])
    def identity(self,pid):
        if pid==410:return copy.deepcopy(self.parent)
        if pid==420:return copy.deepcopy(self.worker)
        return dict(self.worker,pid=pid,creation_filetime=2000+pid)
    def save(self,path,value):
        if str(path) in self.records:raise FileExistsError('Synthetic create-only record')
        self.claims.append(copy.deepcopy(value));return self.put(path,value)
    def __enter__(self):
        self.stack=ExitStack()
        self.stack.enter_context(patch.object(operator,'_parts',return_value=(rules,self.api)))
        self.stack.enter_context(patch.object(operator,'read',side_effect=self.read))
        self.stack.enter_context(patch.object(operator,'read_authority',return_value=copy.deepcopy(self.authority)))
        self.stack.enter_context(patch.object(operator,'save',side_effect=self.save))
        self.stack.enter_context(patch.object(operator,'_run_stages',return_value={'passed':True}))
        self.stack.enter_context(patch.object(operator.sys,'stdin',SimpleNamespace(buffer=io.BytesIO(operator.BARRIER+encoded(self.request_pin)))))
        self.stack.enter_context(patch.object(operator.os,'getppid',return_value=410))
        self.stack.enter_context(patch.object(operator.os,'getpid',return_value=420))
        self.stack.enter_context(patch.object(operator.time,'monotonic',return_value=101))
        return self
    def __exit__(self,*args):return self.stack.__exit__(*args)


class FreshWorkerAndDeadlineAdversaries(unittest.TestCase):
    def test_bad_or_oversized_dispatch_is_rejected_before_operational_imports(self):
        for data in (b'',b'wrong\n',operator.BARRIER+b'x'*131073):
            with self.subTest(length=len(data)),patch.object(operator.sys,'stdin',SimpleNamespace(buffer=io.BytesIO(data))),\
                 patch.object(operator,'_parts',side_effect=AssertionError('Operational import before barrier')) as parts:
                self.assertEqual(operator._worker(),1);parts.assert_not_called()

    def test_current_worker_claim_is_create_only_and_stages_never_retry(self):
        with WorkerPorts() as g:
            stages=operator._run_stages
            self.assertEqual(operator._worker(),0);self.assertEqual(stages.call_count,1)
            self.assertEqual(g.claims,[dict(version=1,authority=g.authority_pin,attempt=g.attempt_pin,
                request=g.request_pin,worker=g.worker)])
            with patch.object(operator.sys,'stdin',SimpleNamespace(buffer=io.BytesIO(operator.BARRIER+encoded(g.request_pin)))):
                with self.assertRaises(FileExistsError):operator._worker()
            self.assertEqual(stages.call_count,1)

    def test_foreign_parent_child_or_started_identity_never_claims_or_stages(self):
        for fault in ('parent','child','started_worker','started_request'):
            with self.subTest(fault=fault),WorkerPorts() as g:
                if fault=='parent':
                    g.records[g.request_pin['path']]['parent']['creation_filetime']+=1
                    g.request_pin=g.put(rules.LIVE/'worker-request-v1.json',g.records[g.request_pin['path']])
                if fault=='child':g.stack.enter_context(patch.object(operator.os,'getpid',return_value=421))
                if fault=='started_worker':g.records[str(rules.LIVE/'worker-started-v1.json')]['worker']['creation_filetime']+=1
                if fault=='started_request':g.records[str(rules.LIVE/'worker-started-v1.json')]['request']['sha256']='0'*64
                with patch.object(operator.sys,'stdin',SimpleNamespace(buffer=io.BytesIO(operator.BARRIER+encoded(g.request_pin)))):
                    with self.assertRaises(rules.FreshRunRefused):operator._worker()
                operator._run_stages.assert_not_called();self.assertEqual(g.claims,[])

    def test_wrong_request_schema_or_boolean_version_never_dispatches_stages(self):
        for fault in ('version','extra'):
            with self.subTest(fault=fault),WorkerPorts() as g:
                value=copy.deepcopy(g.records[g.request_pin['path']])
                if fault=='version':value['version']=True
                else:value['surprise']='not admitted'
                g.request_pin=g.put(rules.LIVE/'worker-request-v1.json',value)
                with patch.object(operator.sys,'stdin',SimpleNamespace(buffer=io.BytesIO(operator.BARRIER+encoded(g.request_pin)))):
                    with self.assertRaises(rules.FreshRunRefused):operator._worker()
                operator._run_stages.assert_not_called();self.assertEqual(g.claims,[])

    def test_worker_budget_refusal_precedes_claim_and_stage(self):
        with WorkerPorts() as g,patch.object(operator.time,'monotonic',return_value=401):
            with self.assertRaises(rules.FreshRunRefused):operator._worker()
            operator._run_stages.assert_not_called();self.assertEqual(g.claims,[])

    def test_cli_clock_starts_before_parts_and_authority_binding(self):
        events=[];authority=pin(rules.AUTHORITY)
        def clock():events.append('clock');return 123
        def parts():events.append('parts');return rules,SimpleNamespace(env=SimpleNamespace(binding=lambda path:authority,encoded=encoded))
        with patch.object(operator.time,'monotonic',side_effect=clock),patch.object(operator,'_parts',side_effect=parts),\
             patch.object(operator,'execute',return_value={'passed':False}),\
             patch.object(operator,'_execute',create=True,return_value={'passed':False}) as private_execute,\
             patch.object(operator.sys,'stdout',io.StringIO()):
            self.assertEqual(operator.main(['--authority-sha256',authority['sha256']]),1)
        self.assertEqual(events[0],'clock','Import/authority lookup must consume the original CLI deadline')
        self.assertEqual(private_execute.call_args.args,(authority,123))

    def test_public_execute_clock_precedes_initial_validation_even_on_refusal(self):
        events=[]
        def clock():events.append('clock');return 123
        def parts():events.append('parts');return rules,SimpleNamespace()
        with patch.object(operator.time,'monotonic',side_effect=clock),patch.object(operator,'_parts',side_effect=parts),\
             patch.object(operator,'_initial',side_effect=rules.FreshRunRefused('synthetic_initial')):
            with self.assertRaises(rules.FreshRunRefused):operator.execute(pin(rules.AUTHORITY))
        self.assertEqual(events[0],'clock')


if __name__=='__main__':unittest.main()