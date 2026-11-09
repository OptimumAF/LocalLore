"""Original stage/outer-owner oracles with explicit synthetic observation ports.

Only tiny retained metadata is written in the test process TEMP directory.
No prepare, activation, native job, process, socket, guest or registry is real.
"""
import contextlib
import copy
import hashlib
import io
import json
import os
from pathlib import Path
import sys
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import Mock, patch

from scripts import run_diagnostic_ui_fresh as subject
from scripts import diagnostic_ui_fresh_contract as rules

CANARY = 'PRIVATE_STAGE_EXCEPTION_MUST_NOT_ESCAPE_107'


def encoded(value):
    return (json.dumps(value, sort_keys=True, allow_nan=False) + '\n').encode()


def fake_pin(path):
    return dict(path=str(path), bytes=1, sha256=hashlib.sha256(str(path).encode()).hexdigest())


class Flag:
    def __init__(self): self.value = False
    def set(self): self.value = True
    def is_set(self): return self.value


class Metadata:
    def __init__(self, live=True):
        self.base = Path(tempfile.mkdtemp(prefix='sdk17-fresh-stage-oracle-'))
        if os.name == 'nt': assert self.base.drive.upper() == 'D:'
        self.events, self.saved = [], []
        self.clock = 0.0
        self.fail_save = None
        self.r = SimpleNamespace(LIVE=self.base/'live', GUEST=self.base/'guest',
            ATTEMPT=self.base/'live/attempt-v1.json', PREPARE_AUTHORIZATION=self.base/'live/prepare-authorization-v1.json',
            OPERATOR=self.base/'operator.py', MAX_SECONDS=2400, need=rules.need, same=rules.same,
            validate_attempt=self.validate_attempt)
        if live: self.r.LIVE.mkdir()
        self.authority_pin = fake_pin(self.base/'authority.json')
        self.authority = dict(ledger=fake_pin(self.base/'ledger.json'), handoff=fake_pin(self.base/'handoff.json'),
            operator=fake_pin(self.r.OPERATOR), contract=fake_pin(self.base/'contract.py'))
        self.handoff = dict(prepare_proposal=fake_pin(self.base/'prepare-proposal.json'))
        self.attempt_pin = fake_pin(self.r.ATTEMPT)
        self.inputs = dict(input=fake_pin(self.base/'run-input.json'), run_proposal=fake_pin(self.base/'run-proposal.json'))
        self.api = SimpleNamespace(env=SimpleNamespace(encoded=encoded, binding=fake_pin,
            check_binding=lambda pin: self.events.append('check_binding'), prepare=self.prepare,
            safe_path=self.safe_path, process_identity=lambda pid: dict(pid=pid, executable=sys.executable)),
            activation=SimpleNamespace(execute=self.activate))

    def validate_attempt(self, value, authority, data):
        self.events.append('validate_attempt')
        rules.need(value['no_retry'] is True and value['authority']==authority, 'attempt')

    def safe_path(self, path, exists=False, **kwargs):
        rules.need(path.exists() is exists, 'already_used')
        return path

    def save(self, path, value):
        self.events.append('save:' + path.name)
        if path.name == self.fail_save: raise OSError(CANARY)
        with path.open('xb') as stream: stream.write(encoded(value))
        self.saved.append((path, copy.deepcopy(value)))
        return fake_pin(path)

    def read(self, pin, expected=None, maximum=None):
        self.events.append('read:' + Path(pin['path']).name)
        if Path(pin['path']) == self.r.ATTEMPT:
            return dict(version=1, no_retry=True, authority=self.authority_pin)
        if Path(pin['path']).name == 'worker-claim-v1.json':
            return dict(authority=self.authority_pin, attempt=self.attempt_pin)
        return json.loads(Path(pin['path']).read_bytes())

    def frozen(self, pin):
        self.events.append('frozen_inputs')
        return self.authority, self.handoff, dict()

    def prepare(self, proposal, authorization):
        self.events.append('prepare')

    def prepared(self, authority, authorization):
        self.events.append('prepared')
        return fake_pin(self.base/'prepared-ledger.json')

    def create_inputs(self, authority, authorization):
        self.events.append('create_inputs')
        return self.inputs

    def activate(self, value):
        self.events.append('activate')
        return dict(passed=True, feature_acceptance=False, input=value)

    def accept(self, value, inputs):
        self.events.append('accept_activation')
        rules.need(value.get('passed') is True and value.get('feature_acceptance') is False and
                   value.get('input') == inputs['input'], 'activation')
        return fake_pin(self.base/'activation-final.json'), fake_pin(self.base/'closed-ledger.json')

    @contextlib.contextmanager
    def stages(self):
        with patch.object(subject, '_parts', return_value=(self.r,self.api)), \
             patch.object(subject, 'save', side_effect=self.save), \
             patch.object(subject, 'read', side_effect=self.read), \
             patch.object(subject, 'frozen_inputs', side_effect=self.frozen), \
             patch.object(subject, 'prepared', side_effect=self.prepared), \
             patch.object(subject, 'create_inputs', side_effect=self.create_inputs), \
             patch.object(subject, '_accept_activation', side_effect=self.accept), \
             patch.object(subject.time, 'monotonic', side_effect=lambda:self.clock):
            yield


class Pipe:
    def __init__(self, h, name): self.h,self.name,self.closed = h,name,False
    def read(self, size): return b''
    def write(self, value): self.h.events.append('barrier');self.h.released.append(value);return len(value)
    def close(self): self.closed=True;self.h.events.append('close:'+self.name)


class Child:
    def __init__(self,h):
        self.h,self.pid,self.returncode = h,700,0
        self.stdin,self.stdout,self.stderr = (Pipe(h,n) for n in ('stdin','stdout','stderr'))
    def poll(self):
        self.h.events.append('poll')
        if self.h.poll_error: raise self.h.poll_error
        return None if self.h.never_exits else self.returncode
    def wait(self,timeout): self.h.events.append('wait');return self.returncode
    def kill(self): self.h.events.append('kill')


class Capture:
    def __init__(self,h): self.h,self.failed,self.overflow = h,Flag(),Flag()
    def append(self,channel,block): return True
    def close(self):
        self.h.events.append('capture.close')
        if isinstance(self.h.capture_result,BaseException): raise self.h.capture_result
        return self.h.capture_result


class Job:
    def __init__(self,h): self.h=h
    def close(self):
        self.h.events.append('job.close')
        if isinstance(self.h.job_result,BaseException): raise self.h.job_result
        return self.h.job_result


class InlineThread:
    def __init__(self,h,*,target,args,daemon): self.h,self.target,self.args,self.ident = h,target,args,None
    def start(self): self.ident=1;self.h.events.append('reader.start');self.target(*self.args)
    def join(self,timeout): self.h.events.append('reader.join')
    def is_alive(self): self.h.events.append('reader.alive');return False


class Supervisor(Metadata):
    def __init__(self, **kwargs):
        super().__init__()
        self.released=[]
        self.capture_result=True;self.job_result=True;self.job_error=None;self.wrong_identity=False
        self.poll_error=None;self.never_exits=False
        self.__dict__.update(kwargs)
        self.child=Child(self);self.capture=Capture(self)
        self.api.env.LiveOutput=lambda path:self.capture
        self.api.env.host=SimpleNamespace(WindowsJob=self.make_job)
        self.api.env.process_identity=self.identity

    def make_job(self,pid):
        self.events.append('job.assign')
        if self.job_error: raise self.job_error
        return Job(self)

    def identity(self,pid):
        self.events.append('identity')
        return dict(pid=pid, executable='foreign.exe' if self.wrong_identity else sys.executable)

    def sleep(self,seconds): self.clock+=1200 if self.never_exits else seconds

    @contextlib.contextmanager
    def ports(self):
        with patch.object(subject, '_parts', return_value=(self.r,self.api)), \
             patch.object(subject, 'save', side_effect=self.save), \
             patch.object(subject.subprocess, 'Popen', return_value=self.child) as spawn, \
             patch.object(subject.subprocess, 'CREATE_NO_WINDOW', 0, create=True), \
             patch.object(subject.threading, 'Thread', side_effect=lambda **kw:InlineThread(self,**kw)), \
             patch.object(subject.time, 'monotonic', side_effect=lambda:self.clock), \
             patch.object(subject.time, 'sleep', side_effect=self.sleep):
            yield spawn


class DiagnosticFreshStageTests(unittest.TestCase):
    def test_positive_stage_order_and_supervisor_barrier_have_explicit_controls(self):
        h=Metadata()
        with h.stages(): result=subject._run_stages(h.authority_pin,h.attempt_pin,0.0)
        self.assertIs(result['passed'],True)
        self.assertEqual(result['phase'],'completed')
        self.assertLess(h.events.index('validate_attempt'),h.events.index('prepare'))
        self.assertLess(h.events.index('read:worker-claim-v1.json'),h.events.index('prepare'))
        self.assertLess(h.events.index('prepared'),h.events.index('create_inputs'))
        self.assertLess(h.events.index('create_inputs'),h.events.index('activate'))
        self.assertIs(result['feature_acceptance'],False)
        supervisor=Supervisor()
        with supervisor.ports() as spawn: owned=subject._supervise(fake_pin(supervisor.base/'request.json'),0.0)
        self.assertEqual(owned['status'],'child_exited')
        self.assertIs(owned['cleanup_complete'],True)
        self.assertIs(owned['output_capture_complete'],True)
        self.assertLess(supervisor.events.index('job.assign'),supervisor.events.index('barrier'))
        self.assertLess(supervisor.events.index('identity'),supervisor.events.index('barrier'))
        self.assertLess(supervisor.events.index('save:worker-started-v1.json'),supervisor.events.index('barrier'))
        self.assertEqual(supervisor.events.count('reader.start'),2)
        self.assertEqual(len(supervisor.released),1)
        self.assertTrue(supervisor.released[0].startswith(subject.BARRIER))
        self.assertTrue(all(p.closed for p in (supervisor.child.stdin,supervisor.child.stdout,supervisor.child.stderr)))
        spawn.assert_called_once()
        with patch.object(subject.sys,'stdin',SimpleNamespace(buffer=io.BytesIO(b'wrong barrier\n'))), \
             patch.object(subject,'_parts',side_effect=AssertionError('operational import before barrier')):
            self.assertEqual(subject._worker(),1)

    def test_assignment_identity_or_started_failure_never_releases_worker(self):
        for mutation in ('job','identity','started'):
            with self.subTest(mutation=mutation):
                h=Supervisor(job_error=OSError(CANARY) if mutation=='job' else None,
                             wrong_identity=mutation=='identity')
                if mutation=='started': h.fail_save='worker-started-v1.json'
                with h.ports(): result=subject._supervise(fake_pin(h.base/'request.json'),0.0)
                self.assertEqual(h.released,[])
                self.assertIs(result['cleanup_complete'],False)
                self.assertIs(result['output_capture_complete'],False)
                self.assertIn('wait',h.events)
                self.assertNotIn(CANARY,repr(result))
                if mutation=='job': self.assertIn('kill',h.events)
                else: self.assertIn('job.close',h.events)

    def test_unknown_job_or_capture_close_and_finite_timeout_cannot_qualify(self):
        # True is the explicit positive control above. LiveOutput.close is bool;
        # None/1 are unknown observation-port outcomes, not SDK capture semantics.
        variants=[dict(job_result=False),dict(job_result=KeyboardInterrupt(CANARY)),
                  dict(capture_result=False),dict(capture_result=None),dict(capture_result=1),
                  dict(capture_result=SystemExit(CANARY))]
        for kwargs in variants:
            with self.subTest(kwargs=repr(kwargs)):
                h=Supervisor(**kwargs)
                with h.ports(): result=subject._supervise(fake_pin(h.base/'request.json'),0.0)
                self.assertIs(result['cleanup_complete'],False)
                self.assertIn('wait',h.events)
                self.assertEqual(h.events.count('reader.join'),2)
                self.assertEqual(h.events.count('capture.close'),1)
                self.assertTrue(h.child.stdout.closed and h.child.stderr.closed)
                self.assertNotIn(CANARY,repr(result))
        h=Supervisor(never_exits=True)
        with h.ports(): result=subject._supervise(fake_pin(h.base/'request.json'),0.0)
        self.assertEqual(result['status'],'expired')
        self.assertGreaterEqual(result['elapsed_ms'],2400000)
        self.assertLessEqual(h.events.count('poll'),2)
        self.assertIn('job.close',h.events)
        h=Supervisor(poll_error=KeyboardInterrupt(CANARY))
        with h.ports(): result=subject._supervise(fake_pin(h.base/'request.json'),0.0)
        self.assertEqual(result['status'],'cancelled')
        self.assertIn('wait',h.events)

    def test_prepare_cancellation_partial_inputs_and_activation_failure_are_terminal(self):
        for mutation in ('keyboard','exit','partial_inputs','activation','budget'):
            with self.subTest(mutation=mutation):
                h=Metadata()
                def prepare(*args):
                    h.events.append('prepare')
                    if mutation=='keyboard': raise KeyboardInterrupt(CANARY)
                    if mutation=='exit': raise SystemExit(CANARY)
                    if mutation=='budget': h.clock=501
                def partial(*args):
                    h.events.append('create_inputs')
                    if mutation=='partial_inputs':
                        h.save(h.r.LIVE/'partial-run-proposal.json',dict(partial=True))
                        raise OSError(CANARY)
                    return h.inputs
                with h.stages(), patch.object(h.api.env,'prepare',side_effect=prepare), \
                     patch.object(subject,'create_inputs',side_effect=partial), \
                     patch.object(h.api.activation,'execute',return_value=dict(passed=False)) as activate:
                    result=subject._run_stages(h.authority_pin,h.attempt_pin,0.0)
                self.assertIs(result['passed'],False)
                self.assertEqual(h.events.count('prepare'),1)
                if mutation!='activation': activate.assert_not_called()
                else: activate.assert_called_once_with(h.inputs['input'])
                self.assertIs(result['feature_acceptance'],False)
                self.assertNotIn(CANARY,repr(result))
                if mutation=='partial_inputs': self.assertTrue((h.r.LIVE/'partial-run-proposal.json').is_file())

    def test_stage_publication_failure_revokes_success_without_retry_or_payload(self):
        h=Metadata();h.fail_save='stage-result-v1.json';stderr=io.StringIO()
        with h.stages(), patch.object(subject.sys,'stderr',stderr):
            result=subject._run_stages(h.authority_pin,h.attempt_pin,0.0)
        self.assertIs(result['passed'],False)
        self.assertIs(result['publication_failed'],True)
        self.assertEqual(h.events.count('prepare'),1)
        self.assertEqual(h.events.count('activate'),1)
        self.assertEqual(h.events.count('save:stage-result-v1.json'),1)
        self.assertEqual(stderr.getvalue(),'{"scope":"sdk17-fresh-operation-stages-v1","publication_failed":true}\n')
        self.assertNotIn(CANARY,repr(result))

    def test_durable_attempt_is_spent_before_supervision_even_after_partial_failure(self):
        for failure in ('owner','attempt_save'):
            with self.subTest(failure=failure):
                h=Metadata(live=False);seen=[]
                if failure=='attempt_save': h.fail_save='attempt-v1.json'
                def supervise(request,begin):
                    seen.append(h.r.ATTEMPT.read_bytes())
                    return dict(status='owner_failed',worker_returncode=None,cleanup_complete=False,
                                output_capture_complete=False,worker=None)
                with h.stages(), patch.object(subject,'_initial',return_value=(h.authority,h.handoff)), \
                     patch.object(subject,'_supervise',side_effect=supervise) as owner:
                    if failure=='attempt_save':
                        with self.assertRaises(OSError): subject._execute(h.authority_pin,0.0)
                        self.assertEqual(seen,[])
                    else:
                        result=subject._execute(h.authority_pin,0.0)
                        self.assertIs(result['passed'],False)
                        self.assertEqual(len(seen),1)
                        self.assertIs(json.loads(seen[0])['no_retry'],True)
                    self.assertTrue(h.r.LIVE.is_dir())
                    with self.assertRaises(rules.FreshRunRefused): subject._execute(h.authority_pin,0.0)
                self.assertEqual(owner.call_count,1 if failure=='owner' else 0)
                self.assertNotIn('prepare',h.events)
                if seen: self.assertEqual(h.r.ATTEMPT.read_bytes(),seen[0])
