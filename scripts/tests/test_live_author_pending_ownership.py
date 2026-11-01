"""Pending-worker ownership faults with original D metadata and native fakes.

No synthetic session here establishes SDK authority; deep success replay belongs
to the separate SDK6 reader cohort. No process, socket or device is launched.
"""
import copy
from pathlib import Path
import tempfile
import threading
import time
from types import SimpleNamespace
import unittest
from unittest.mock import patch

from benchmarks import original_author_live_death_controller as c
from scripts.tests import test_owned_live_death_contract as metadata
from scripts.tests import test_owned_restart_contract as previous


class FakeThread:
    def __init__(self, *args, **kwargs):
        self.active = True
        self.joined = 0

    def start(self):
        pass

    def is_alive(self):
        return self.active

    def join(self, seconds):
        self.joined += 1
        self.active = False


class FakeApi:
    def __init__(self, identity):
        self.value = copy.deepcopy(identity)
        self.closed = []
        self.close_ok = True

    def open_process(self, pid):
        if pid != self.value['pid']:
            raise AssertionError('foreign PID requested')
        return 73

    def identity(self, handle):
        if handle != 73:
            raise AssertionError('foreign handle')
        return copy.deepcopy(self.value)

    def alive(self, handle):
        return handle == 73

    def close_handle(self, handle):
        self.closed.append(handle)
        return self.close_ok


class PendingFixture:
    def __init__(self):
        self.base = Path(tempfile.mkdtemp(prefix='locallore-live-pending-', dir='D:/Dev/_Temp')).resolve()
        self.a = metadata.admission()
        self.a['root'] = str(self.base/'owner')
        self.a['server']['root'] = str(self.base/'owner/server')
        self.admission = self.save(self.base/'admission.json', self.a)
        descriptor = previous.running(self.a)
        descriptor.update(protocol=c.c6.PROTOCOL, admission=self.admission)
        self.running = self.save(self.base/'owner/running-v1.json', descriptor)
        self.session = previous.session(self.a)
        self.session.update(protocol=c.c6.SDK_PROTOCOL, admission=self.admission,
            running=self.running, descriptor=descriptor, root=str(self.base/'control'),
            seconds=c.AUTHOR_SECONDS, started_epoch=1800000010.0,
            deadline_epoch=1800000010.0+c.AUTHOR_SECONDS)
        self.worker = copy.deepcopy(self.session['caller'])
        self.worker['pid'] += 20
        self.session['caller'] = copy.deepcopy(self.worker)
        self.root = self.base/'control/pending-author-v1'
        self.root.mkdir(parents=True)
        self.session['root'] = str(self.root/'capture-v1')
        self.session_pin = self.save(self.root/'capture-v1'/c.c6.SESSION_FILE, self.session)
        self.p = c.PendingAuthor.__new__(c.PendingAuthor)
        p = self.p
        p.root, p.admission, p.admission_pin, p.running_pin = self.root, self.a, self.admission, self.running
        p.control = dict(started_epoch=self.session['started_epoch']-10,
                         deadline_epoch=self.session['deadline_epoch']+20)
        p.request = dict(control_session=self.session_pin)
        p.request_pin = self.save(self.root/'request-v1.json', dict(version=1, original=True))
        p.expected = copy.deepcopy(self.worker)
        p.started_pin = self.save(self.root/'started-v1.json', dict(request=p.request_pin, worker=self.worker))
        self.ready = dict(version=1, protocol='owned-live-author-ready-v1', request=p.request_pin,
                          worker=copy.deepcopy(self.worker), session=self.session_pin)
        p.ready_pin = self.save(self.root/'worker-ready-v1.json', self.ready)
        p.thread, p.failed, p.owner_result = FakeThread(), False, None
        p.lock, p.until = threading.Lock(), time.monotonic()+10
        self.api = FakeApi(self.worker)
        p.handles = c.primitives.ProcessHandles(self.api)
        p.handles.add(self.worker['pid'])
        (self.root/'worker-output-v1').mkdir()

    def save(self, path, value):
        path.parent.mkdir(parents=True, exist_ok=True)
        c.env.create_json(path, value)
        return c.env.binding(path)

    def replace(self, path, value):
        Path(path).write_bytes(c.env.encoded(value))

    def start(self):
        self.p.thread = None
        with patch.object(c.threading, 'Thread', FakeThread):
            return self.p.start()


class LiveAuthorPendingOwnershipTests(unittest.TestCase):
    def test_ready_session_and_held_identity_are_checked_without_success_authority(self):
        f = PendingFixture()
        self.assertIs(f.start(), f.p)
        f.p.require_pending()
        self.assertEqual(f.api.closed, [])
        self.assertTrue(f.p.cancel())
        self.assertEqual(f.api.closed, [73])
        self.assertFalse((f.root/'result-v1.json').exists())

    def test_wrong_request_worker_protocol_or_session_ready_refuses(self):
        changes = [lambda f: f.ready.update(request=f.admission),
                   lambda f: f.ready['worker'].update(pid=f.worker['pid']+1),
                   lambda f: f.ready.update(protocol='owned-live-author-ready-v0'),
                   lambda f: f.ready.pop('session'),
                   lambda f: f.session.update(root=str(f.base/'foreign-capture')),
                   lambda f: f.session['caller'].update(pid=f.worker['pid']+1),
                   lambda f: f.session.update(seconds=c.AUTHOR_SECONDS-1),
                   lambda f: f.session.update(running=f.admission)]
        for index, change in enumerate(changes):
            f = PendingFixture(); change(f)
            f.replace(f.session_pin['path'], f.session)
            f.ready['session'] = c.env.binding(f.session_pin['path']) if 'session' in f.ready else None
            if f.ready['session'] is None:
                del f.ready['session']
            f.replace(f.root/'worker-ready-v1.json', f.ready)
            with self.subTest(change=index), self.assertRaises((ValueError, c.env.EnvironmentRefused)):
                f.start()
            self.assertTrue(f.p.cancel())
            self.assertEqual(f.api.closed, [73])

    def test_terminal_client_or_worker_and_rebound_receipts_block_pending(self):
        for field in ('worker-result-v1.json', 'capture-v1/clients/command-0001.json',
                      'started-v1.json', 'request-v1.json', 'worker-ready-v1.json'):
            f = PendingFixture()
            path = f.root/field
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(b'{"changed":true}\n')
            with self.subTest(field=field), self.assertRaises((ValueError, c.env.EnvironmentRefused)):
                f.p.require_pending()
            self.assertTrue(f.p.cancel())
            self.assertFalse((f.root/'result-v1.json').exists())

    def test_failed_terminal_verdict_still_closes_retained_local_handle_on_cancel(self):
        f = PendingFixture(); f.p.failed = True
        with self.assertRaises((ValueError, c.env.EnvironmentRefused)):
            f.p.cancel()
        self.assertEqual(f.api.closed, [73])
        self.assertEqual(f.p.handles.handles, {})
        self.assertFalse((f.root/'result-v1.json').exists())

    def test_uncertain_handle_close_is_not_retried_or_reported_closed(self):
        f = PendingFixture(); f.api.close_ok = False; f.p.thread.active = False
        self.assertFalse(f.p.cancel())
        self.assertFalse(f.p.cancel())
        self.assertEqual(f.api.closed, [73])
        self.assertIn(73, f.p.handles.handles)
        self.assertFalse((f.root/'result-v1.json').exists())

    def test_partial_owner_capture_cannot_publish_pending_success(self):
        for change in (dict(cleanup_complete=False), dict(output_capture_complete=False),
                       dict(worker_returncode=1), dict(status='expired'), dict(stdout_bytes=1),
                       dict(stderr_bytes=1)):
            f = PendingFixture(); f.p.thread.active = False
            f.p.owner_result = dict(status='child_exited', worker_returncode=0,
                cleanup_complete=True, output_capture_complete=True, elapsed_ms=1,
                stdout_bytes=0, stderr_bytes=0)
            f.p.owner_result.update(change)
            with self.subTest(change=change), self.assertRaises((ValueError, c.env.EnvironmentRefused)):
                f.p.finish()
            self.assertEqual(f.api.closed, [73])
            self.assertFalse((f.root/'result-v1.json').exists())

    def test_cancel_publishes_exact_stop_only_in_owned_worker_capture_namespace(self):
        f = PendingFixture()
        self.assertTrue(f.p.cancel())
        path = f.root/'worker-output-v1/stop-v1.json'
        self.assertEqual(c.env.read_json(path), dict(version=1, action='stop',
            proposal_sha256=f.p.request_pin['sha256']))
        self.assertFalse((f.root/'stop-v1.json').exists())
        self.assertFalse((f.root/'worker-output-v1/stop.pending-v1.json').exists())
        self.assertTrue(f.p.cancel())
        self.assertEqual(f.api.closed, [73])

    def test_cancel_control_write_failure_still_joins_and_closes_owned_handles(self):
        for operation in ('create', 'rename'):
            f = PendingFixture()
            target, name = (c.env, 'create_json') if operation == 'create' else (Path, 'rename')
            with self.subTest(operation=operation), patch.object(target, name, side_effect=OSError('synthetic write failure')):
                with self.assertRaises(OSError):
                    f.p.cancel()
            self.assertEqual(f.p.thread.joined, 1)
            self.assertFalse(f.p.thread.is_alive())
            self.assertEqual(f.api.closed, [73])
            self.assertEqual(f.p.handles.handles, {})

    def worker_request(self, f):
        root = f.base/'worker-case'
        root.mkdir()
        request = dict(version=1, protocol='owned-live-author-request-v1',
            admission=f.admission, running=f.running, control_session=f.session_pin,
            root=str(root), sources=f.a['sources'], python=f.a['python'],
            controller=c.env.binding(Path(c.__file__).resolve()),
            seconds=c.AUTHOR_SECONDS, owner_seconds=c.AUTHOR_OWNER_SECONDS)
        return root, f.save(root/'request-v1.json', request)

    def test_worker_rejects_wrong_receipt_before_input_guard_or_observer_construction(self):
        for change in ('request', 'worker', 'shape'):
            f = PendingFixture(); root, request = self.worker_request(f)
            receipt = dict(request=request, worker=copy.deepcopy(f.worker))
            if change == 'request': receipt['request'] = f.admission
            elif change == 'worker': receipt['worker']['pid'] += 1
            else: receipt['private'] = 'PRIVATE_CANARY'
            f.save(root/'started-v1.json', receipt)
            with self.subTest(change=change), \
                 patch.object(c.env, 'process_identity', return_value=f.worker), \
                 patch.object(c.c6, 'revalidate_inputs', side_effect=AssertionError('unexpected input IO')) as inputs, \
                 patch.object(c.owner, 'LiveOwnedLiveDeathTarget', side_effect=AssertionError('unexpected observer')) as observer:
                with self.assertRaises((ValueError, c.env.EnvironmentRefused)):
                    c._worker(request)
                inputs.assert_not_called()
                observer.assert_not_called()
            self.assertFalse((root/'worker-ready-v1.json').exists())

    def test_missing_worker_receipt_exhausts_only_its_fixed_wait_without_observer(self):
        f = PendingFixture(); root, request = self.worker_request(f)
        ticks = iter((1.0, 7.0))
        clock = SimpleNamespace(monotonic=lambda: next(ticks), sleep=lambda seconds: None)
        with patch.object(c, 'time', clock), \
             patch.object(c.owner, 'LiveOwnedLiveDeathTarget', side_effect=AssertionError('unexpected observer')) as observer:
            with self.assertRaises((ValueError, c.env.EnvironmentRefused)):
                c._worker(request)
            observer.assert_not_called()
        self.assertFalse((root/'started-v1.json').exists())
        self.assertFalse((root/'worker-ready-v1.json').exists())

    def test_cancel_preserves_publication_exception_when_terminal_verdict_also_fails(self):
        f = PendingFixture(); f.p.failed = True
        primary = OSError('original synthetic publication error')
        with patch.object(c.env, 'create_json', side_effect=primary):
            with self.assertRaises(OSError) as caught:
                f.p.cancel()
        self.assertIs(caught.exception, primary)
        self.assertEqual(f.p.thread.joined, 1)
        self.assertEqual(f.api.closed, [73])
        self.assertEqual(f.p.handles.handles, {})


if __name__ == '__main__':
    unittest.main()
