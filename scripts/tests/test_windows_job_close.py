"""Windows Job cleanup oracles, with no actual native/process/SDK operations.

The real WindowsJob constructor sets the ctypes signatures and creates its real
accounting structure; a finite fake kernel32 supplies raw Win32 BOOL outcomes.
The caller graphs use synchronous in-memory pipe workers and explicitly fake
process/capture owners. They prove cleanup control flow, not real termination.
No generated files or target state are created by these methods.
Copyright 2026 LocalLore contributors. SPDX-License-Identifier: Apache-2.0
"""
from contextlib import ExitStack
import ctypes
from ctypes import wintypes
import io
import os
import sys
from pathlib import Path
import threading
from types import SimpleNamespace
import unittest
from unittest.mock import patch

from benchmarks import runtime_spike as runtime
from benchmarks import receipt_avd_environment as environment
from benchmarks import windows_native_tcp_state as native_tcp
from scripts import run_library_ui_recovery as recovery
# The legacy Android module uses this fixed flat alias; no CLI/main is invoked.
with patch.dict(sys.modules, {'runtime_spike': runtime}):
    from benchmarks import android_runtime_spike as android


JOB = 0x7711
PROCESS = 0x7722
PID = 0x7733


class NativeFunction:
    """An assignable ctypes signature plus a finite, inspectable call body."""
    def __init__(self, name, kernel, body):
        self.name, self.kernel, self.body = name, kernel, body
        self.argtypes = None
        self.restype = None

    def __call__(self, *args):
        self.kernel.calls.append((self.name, args))
        return self.body(*args)


def raised(value):
    if isinstance(value, BaseException):
        raise value
    return value


class Kernel:
    def __init__(self, *, terminate=1, query=1, close=1, active=(0,),
                 create=JOB, configure=1, opened=PROCESS, assign=1, process_close=1):
        self.terminate_result, self.query_result, self.close_result = terminate, query, close
        self.active = list(active)
        self.process_close = process_close
        self.calls = []
        self.query_count = 0
        self.CreateJobObjectW = NativeFunction('CreateJobObjectW', self, lambda *_: raised(create))
        self.SetInformationJobObject = NativeFunction('SetInformationJobObject', self, lambda *_: raised(configure))
        self.OpenProcess = NativeFunction('OpenProcess', self, lambda *_: raised(opened))
        self.AssignProcessToJobObject = NativeFunction('AssignProcessToJobObject', self, lambda *_: raised(assign))
        self.TerminateJobObject = NativeFunction('TerminateJobObject', self, lambda *_: raised(self.terminate_result))
        self.QueryInformationJobObject = NativeFunction('QueryInformationJobObject', self, self.query)
        self.CloseHandle = NativeFunction('CloseHandle', self, self.close)

    def query(self, handle, information, pointer, size, returned):
        assert handle == JOB and information == 1 and returned is None
        self.query_count += 1
        result = raised(self.query_result)
        if result:
            # byref receives the real constructor-defined Accounting structure.
            assert size == ctypes.sizeof(pointer._obj)
            pointer._obj.active = self.active[min(self.query_count - 1, len(self.active) - 1)]
        return result

    def close(self, handle):
        assert handle in (PROCESS, JOB)
        return raised(self.process_close if handle == PROCESS else self.close_result)

    def names(self):
        return [name for name, _ in self.calls]

    def closes(self, handle):
        return [args for name, args in self.calls if name == 'CloseHandle' and args == (handle,)]


class Clock:
    """A finite synthetic clock; even all-active timeout tests never sleep."""
    def __init__(self, *, clock_error=None, sleep_error=None):
        self.tick = 0
        self.clock_error = clock_error
        self.sleep_error = sleep_error
        self.monotonic_calls = 0
        self.sleep_calls = 0

    def monotonic(self):
        self.monotonic_calls += 1
        if self.clock_error is not None:
            error, self.clock_error = self.clock_error, None
            raise error
        self.tick += 1
        return float(self.tick)

    def sleep(self, seconds):
        assert seconds == .01
        self.sleep_calls += 1
        if self.sleep_error is not None:
            error, self.sleep_error = self.sleep_error, None
            raise error


class MemoryPipe(io.BytesIO):
    def __init__(self, events, label, raw=b''):
        super().__init__(raw)
        self.events, self.label = events, label
        self.close_calls = 0

    def read(self, size=-1):
        self.events.append(('read', self.label))
        return super().read(size)

    def write(self, raw):
        self.events.append(('write', self.label, bytes(raw)))
        return super().write(raw)

    def close(self):
        self.close_calls += 1
        self.events.append(('pipe-close', self.label))
        super().close()


class MemoryProcess:
    def __init__(self, events):
        self.events = events
        self.pid = PID
        self.returncode = 0
        self.stdin = MemoryPipe(events, 'stdin')
        self.stdout = MemoryPipe(events, 'stdout', b'ordinary\x00\x1a\r\noutput')
        self.stderr = MemoryPipe(events, 'stderr', b'private-error-bytes')
        self.wait_calls = self.kill_calls = 0

    def poll(self):
        self.events.append(('poll',))
        return self.returncode

    def wait(self, timeout):
        assert timeout == 5
        self.wait_calls += 1
        self.events.append(('wait',))
        return self.returncode

    def kill(self):
        self.kill_calls += 1
        self.events.append(('kill',))


class InlineThread:
    """Runs finite BytesIO drains synchronously; no OS thread is created."""
    def __init__(self, events, target, args=(), daemon=False):
        assert daemon is True
        self.events, self.target, self.args = events, target, args
        self.started = False
        self.ident = None
        self.joins = []

    def start(self):
        self.started = True
        self.ident = 17
        self.events.append(('thread-start',))
        self.target(*self.args)

    def join(self, timeout):
        assert timeout == 2
        self.joins.append(timeout)
        self.events.append(('thread-join',))

    def is_alive(self):
        return False


class MemoryCapture:
    def __init__(self, events):
        self.events = events
        self.failed = threading.Event()
        self.overflow = threading.Event()
        self.channels = [bytearray(), bytearray()]
        self.close_calls = 0

    @property
    def sizes(self):
        return [len(raw) for raw in self.channels]

    def append(self, channel, data):
        self.channels[channel].extend(data)
        return True

    def close(self):
        self.close_calls += 1
        self.events.append(('capture-close',))
        return True


class CallerGraph:
    """No Popen, native job, real thread, capture file or target operation."""
    def __init__(self, close_result=True, construction_error=None):
        self.events = []
        self.child = MemoryProcess(self.events)
        self.capture = MemoryCapture(self.events)
        self.threads = []
        self.close_result = close_result
        self.construction_error = construction_error
        self.constructor_calls = 0
        self.close_calls = 0
        self.job = SimpleNamespace(close=self.close)

    def make_job(self, pid):
        assert pid == PID
        self.constructor_calls += 1
        self.events.append(('job-construct',))
        if self.construction_error is not None:
            raise self.construction_error
        return self.job

    def close(self):
        self.close_calls += 1
        self.events.append(('job-close',))
        return raised(self.close_result)

    def thread(self, **kwargs):
        thread = InlineThread(self.events, **kwargs)
        self.threads.append(thread)
        return thread

    def patches(self, mode):
        module = runtime if mode == 'runtime' else environment
        stack = ExitStack()
        stack.enter_context(patch.object(module.subprocess, 'Popen', return_value=self.child))
        stack.enter_context(patch.object(runtime, 'WindowsJob', side_effect=self.make_job))
        thread_api = SimpleNamespace(Lock=threading.Lock, Event=threading.Event, Thread=self.thread)
        stack.enter_context(patch.object(module, 'threading', thread_api))
        stack.enter_context(patch.object(ctypes, 'WinDLL', side_effect=AssertionError('Caller graph reached native API')))
        if mode in ('supervisor', 'tcp'):
            stack.enter_context(patch.object(environment, 'LiveOutput', return_value=self.capture))
        if mode == 'tcp':
            # _supervise imports threading locally; patch just its finite factory.
            stack.enter_context(patch.object(threading, 'Thread', side_effect=self.thread))
            stack.enter_context(patch.object(native_tcp, '_runtime', return_value=(environment, None, None)))
        if mode == 'recovery':
            live = Path('D:/Dev/_Temp/never-created-job-recovery')
            def need(value, reason):
                if not value: raise ValueError(reason)
            rules = SimpleNamespace(LIVE=live, OPERATOR=live/'unused-operator.py', MAX_SECONDS=2400, need=need)
            fake_env = SimpleNamespace(LiveOutput=lambda _: self.capture,
                host=SimpleNamespace(WindowsJob=self.make_job), encoded=environment.encoded,
                process_identity=lambda pid: dict(pid=pid, creation_filetime=1234, executable=sys.executable))
            parts = (rules, SimpleNamespace(save=lambda *_: None), SimpleNamespace(env=fake_env))
            stack.enter_context(patch.object(recovery, '_parts', return_value=parts))
            stack.enter_context(patch.object(recovery, 'threading', thread_api))
            def mkdir(path, *args, **kwargs):
                assert path == live/'outer-owner-v1'
                self.events.append(('synthetic-root-mkdir',))
            stack.enter_context(patch.object(Path, 'mkdir', new=mkdir))
        return stack

    def run(self, mode):
        with self.patches(mode):
            if mode == 'runtime':
                return runtime.run_process(['synthetic-never-executed'], request=b'barrier', deadline=5)
            root = Path('D:/Dev/_Temp/never-created-windows-job-test')
            if mode == 'supervisor':
                return environment.supervise(['synthetic-never-executed'], b'barrier', root, 5, lambda _: True)
            if mode == 'tcp':
                return native_tcp._supervise(['synthetic-never-executed'], b'barrier', root, 5, lambda _: True)
            assert mode == 'recovery'
            return recovery._supervise({'synthetic_request': True}, recovery.time.monotonic())


@unittest.skipUnless(os.name == 'nt', 'Windows BOOL ABI and Windows caller paths; all native calls are fake')
class WindowsJobCloseTests(unittest.TestCase):
    def construct(self, kernel):
        with patch.object(ctypes, 'WinDLL', return_value=kernel) as load:
            job = runtime.WindowsJob(PID)
        load.assert_called_once_with('kernel32', use_last_error=True)
        self.assertEqual(kernel.names(), ['CreateJobObjectW', 'SetInformationJobObject',
            'OpenProcess', 'AssignProcessToJobObject', 'CloseHandle'])
        self.assertEqual(kernel.closes(PROCESS), [(PROCESS,)])
        self.assertEqual(kernel.closes(JOB), [])
        self.assertIs(kernel.CloseHandle.restype, wintypes.BOOL)
        self.assertIs(kernel.TerminateJobObject.restype, wintypes.BOOL)
        self.assertIs(kernel.QueryInformationJobObject.restype, wintypes.BOOL)
        kernel.calls.clear()
        return job

    def result(self, job, clock):
        with patch.object(runtime, 'time', SimpleNamespace(monotonic=clock.monotonic, sleep=clock.sleep)):
            try:
                return job.close()
            except BaseException as error:
                # KeyboardInterrupt must become a bounded oracle failure rather
                # than aborting the central unittest runner or hiding later cases.
                self.fail('WindowsJob.close leaked ' + type(error).__name__)

    def sticky(self, job, kernel, clock, expected):
        self.assertIs(self.result(job, clock), expected)
        calls = list(kernel.calls)
        counters = (clock.monotonic_calls, clock.sleep_calls, kernel.query_count)
        self.assertIs(self.result(job, clock), expected)
        self.assertEqual(kernel.calls, calls)
        self.assertEqual((clock.monotonic_calls, clock.sleep_calls, kernel.query_count), counters)
        self.assertEqual(kernel.closes(JOB), [(JOB,)])

    def constructor_error(self, kernel):
        value = error = None
        with patch.object(ctypes, 'WinDLL', return_value=kernel):
            try:
                value = runtime.WindowsJob(PID)
            except BaseException as caught:
                error = caught
        self.assertIsNone(value, 'An owner escaped failed constructor cleanup')
        self.assertIsInstance(error, OSError)
        self.assertLessEqual(len(str(error)), 96)
        self.assertNotIn('SYNTHETIC_PRIVATE_HANDLE_CANARY', str(error))
        return error

    def test_reentrant_close_cannot_retry_a_handle_or_turn_an_inflight_false_into_true(self):
        kernel = Kernel(); job = self.construct(kernel); clock = Clock()
        original = kernel.QueryInformationJobObject.body
        entered, nested = [], []
        def query(*args):
            if not entered:
                entered.append(True)
                nested.append(job.close())
            return original(*args)
        kernel.QueryInformationJobObject.body = query
        self.assertIs(self.result(job, clock), False)
        self.assertEqual(nested, [False])
        self.assertEqual(kernel.names(), ['TerminateJobObject', 'QueryInformationJobObject', 'CloseHandle'])
        self.sticky(job, kernel, clock, False)

    def test_overlapping_close_returns_without_waiting_for_native_work_and_poisoned_result_stays_false(self):
        kernel = Kernel(); job = self.construct(kernel); clock = Clock()
        original = kernel.QueryInformationJobObject.body
        entered, release = threading.Event(), threading.Event()
        results, errors = [], []
        def query(*args):
            if not entered.is_set():
                entered.set()
                if not release.wait(3): raise RuntimeError('synthetic query was not released')
            return original(*args)
        def first():
            try: results.append(job.close())
            except BaseException as error: errors.append(type(error).__name__)
        kernel.QueryInformationJobObject.body = query
        with patch.object(runtime, 'time', SimpleNamespace(monotonic=clock.monotonic, sleep=clock.sleep)):
            thread = threading.Thread(target=first)
            thread.start()
            try:
                self.assertTrue(entered.wait(3))
                self.assertIs(self.result(job, clock), False)
            finally:
                release.set(); thread.join(timeout=3)
                self.assertFalse(thread.is_alive())
        self.assertEqual(errors, [])
        self.assertEqual(results, [False])
        self.assertEqual(kernel.names(), ['TerminateJobObject', 'QueryInformationJobObject', 'CloseHandle'])
        self.sticky(job, kernel, clock, False)

    def test_create_failure_never_opens_or_closes_a_nonexistent_handle(self):
        for failure in (0, OSError('SYNTHETIC_PRIVATE_HANDLE_CANARY')):
            with self.subTest(failure=type(failure).__name__):
                kernel = Kernel(create=failure)
                self.constructor_error(kernel)
                self.assertEqual(kernel.names(), ['CreateJobObjectW'])

    def test_configuration_open_and_assignment_refusal_close_exactly_the_acquired_handles(self):
        for stage in ('configure', 'opened', 'assign'):
            with self.subTest(stage=stage):
                kernel = Kernel(**{stage: 0})
                self.constructor_error(kernel)
                self.assertEqual(kernel.closes(JOB), [(JOB,)])
                self.assertEqual(kernel.closes(PROCESS), [(PROCESS,)] if stage == 'assign' else [])
                self.assertEqual(kernel.names().count('TerminateJobObject'), 0)
                self.assertEqual(kernel.names().count('QueryInformationJobObject'), 0)

    def test_temporary_process_close_failure_refuses_constructor_and_independently_closes_job_once(self):
        for failure in (0, OSError('SYNTHETIC_PRIVATE_HANDLE_CANARY'),
                        KeyboardInterrupt('SYNTHETIC_PRIVATE_HANDLE_CANARY'),
                        SystemExit('SYNTHETIC_PRIVATE_HANDLE_CANARY')):
            with self.subTest(failure=type(failure).__name__):
                kernel = Kernel(process_close=failure)
                error = self.constructor_error(kernel)
                self.assertEqual(str(error), 'job_cleanup_failed')
                self.assertEqual(kernel.closes(PROCESS), [(PROCESS,)])
                self.assertEqual(kernel.closes(JOB), [(JOB,)])
                self.assertEqual(kernel.names()[-2:], ['CloseHandle', 'CloseHandle'])

    def test_unknown_cleanup_cannot_hide_a_second_acquired_handle_or_leak_private_native_error(self):
        for first in (0, OSError('SYNTHETIC_PRIVATE_HANDLE_CANARY')):
            for second in (0, OSError('SYNTHETIC_PRIVATE_HANDLE_CANARY')):
                with self.subTest(process_close=type(first).__name__, job_close=type(second).__name__):
                    kernel = Kernel(assign=0, process_close=first, close=second)
                    error = self.constructor_error(kernel)
                    self.assertEqual(str(error), 'job_cleanup_failed')
                    self.assertEqual(kernel.closes(PROCESS), [(PROCESS,)])
                    self.assertEqual(kernel.closes(JOB), [(JOB,)])

    def test_success_requires_terminate_observed_zero_and_close_and_accepts_every_nonzero_native_bool(self):
        for native_true in (1, 2, -1):
            with self.subTest(native_true=native_true):
                kernel = Kernel(terminate=native_true, query=native_true, close=native_true,
                                configure=native_true, assign=native_true, process_close=native_true)
                job = self.construct(kernel); clock = Clock()
                self.sticky(job, kernel, clock, True)
                self.assertEqual(kernel.names(), ['TerminateJobObject', 'QueryInformationJobObject', 'CloseHandle'])
                self.assertEqual(kernel.query_count, 1)
                self.assertEqual(clock.sleep_calls, 0)

    def test_closehandle_zero_cannot_qualify_even_after_a_successful_zero_active_query(self):
        kernel = Kernel(close=0); job = self.construct(kernel); clock = Clock()
        self.sticky(job, kernel, clock, False)
        self.assertEqual(kernel.names(), ['TerminateJobObject', 'QueryInformationJobObject', 'CloseHandle'])
        self.assertEqual(kernel.query_count, 1)

    def test_terminate_zero_is_sticky_refusal_and_does_not_claim_a_zero_active_observation(self):
        kernel = Kernel(terminate=0); job = self.construct(kernel); clock = Clock()
        self.sticky(job, kernel, clock, False)
        self.assertEqual(kernel.names(), ['TerminateJobObject', 'CloseHandle'])
        self.assertEqual(kernel.query_count, 0)

    def test_query_zero_is_sticky_refusal_even_though_closehandle_succeeds(self):
        kernel = Kernel(query=0); job = self.construct(kernel); clock = Clock()
        self.sticky(job, kernel, clock, False)
        self.assertEqual(kernel.names(), ['TerminateJobObject', 'QueryInformationJobObject', 'CloseHandle'])
        self.assertEqual(kernel.query_count, 1)

    def test_nonzero_active_counts_require_a_later_actual_zero_before_success(self):
        kernel = Kernel(active=(3, 1, 0)); job = self.construct(kernel); clock = Clock()
        self.sticky(job, kernel, clock, True)
        self.assertEqual(kernel.query_count, 3)
        self.assertEqual(clock.sleep_calls, 2)
        self.assertEqual(kernel.names(), ['TerminateJobObject'] + ['QueryInformationJobObject'] * 3 + ['CloseHandle'])

    def test_deadline_with_active_processes_is_sticky_false_with_one_handle_close(self):
        kernel = Kernel(active=(1,)); job = self.construct(kernel); clock = Clock()
        self.sticky(job, kernel, clock, False)
        self.assertGreater(kernel.query_count, 0)
        self.assertLessEqual(kernel.query_count, 5)
        self.assertEqual(kernel.names()[0], 'TerminateJobObject')
        self.assertEqual(kernel.names()[-1], 'CloseHandle')

    def test_terminate_query_and_close_exceptions_or_cancellation_always_close_once_and_return_sticky_false(self):
        for stage in ('terminate', 'query', 'close'):
            for error_type in (OSError, ValueError, KeyboardInterrupt, SystemExit):
                with self.subTest(stage=stage, error=error_type.__name__):
                    kernel = Kernel(**{stage: error_type('synthetic native boundary')})
                    job = self.construct(kernel); clock = Clock()
                    self.sticky(job, kernel, clock, False)
                    self.assertEqual(kernel.names()[0], 'TerminateJobObject')
                    self.assertEqual(kernel.names()[-1], 'CloseHandle')
                    self.assertEqual(kernel.query_count, 0 if stage == 'terminate' else 1)

    def test_clock_or_sleep_exceptions_and_cancellation_are_sticky_refusals_after_one_close_attempt(self):
        for stage in ('clock_error', 'sleep_error'):
            for error_type in (OSError, ValueError, KeyboardInterrupt, SystemExit):
                with self.subTest(stage=stage, error=error_type.__name__):
                    kernel = Kernel(active=(1,)); job = self.construct(kernel)
                    clock = Clock(**{stage: error_type('synthetic time boundary')})
                    self.sticky(job, kernel, clock, False)
                    self.assertEqual(kernel.names()[0], 'TerminateJobObject')
                    self.assertEqual(kernel.names()[-1], 'CloseHandle')
                    self.assertEqual(kernel.query_count, 0 if stage == 'clock_error' else 1)

    def caller_result(self, graph, mode):
        value = error = None
        try:
            value = graph.run(mode)
        except BaseException as caught:
            error = caught
        # Check the independent cleanup tails before inspecting the error. The
        # old unguarded close exception must fail for skipped cleanup, not merely
        # because some compatible exception class happened to reach the caller.
        self.assertEqual(graph.close_calls, 0 if graph.construction_error is not None else 1)
        self.assertEqual(graph.constructor_calls, 1)
        self.assertEqual(graph.child.wait_calls, 1)
        self.assertEqual(graph.child.kill_calls, 1 if graph.construction_error is not None else 0)
        self.assertEqual(len(graph.threads), 0 if graph.construction_error is not None else 3 if mode == 'runtime' else 2)
        self.assertTrue(all(thread.started for thread in graph.threads))
        self.assertTrue(all(thread.joins == [2] for thread in graph.threads))
        if graph.construction_error is None:
            self.assertLess(graph.events.index(('job-close',)), graph.events.index(('wait',)))
        if mode != 'runtime':
            self.assertEqual(graph.capture.close_calls, 1)
            self.assertLess(graph.events.index(('wait',)), graph.events.index(('capture-close',)))
        self.assertTrue(all(pipe.closed for pipe in (graph.child.stdin, graph.child.stdout, graph.child.stderr)))
        self.assertIsNone(error, 'Caller leaked cleanup exception: ' + (type(error).__name__ if error else 'none'))
        return value

    def test_runtime_success_keeps_exact_output_and_closes_owned_pipes_after_wait_and_joins(self):
        graph = CallerGraph()
        result = self.caller_result(graph, 'runtime')
        self.assertEqual(result.status, 'completed'); self.assertIs(result.cleanup_complete, True)
        self.assertEqual(result.stdout, b'ordinary\x00\x1a\r\noutput')
        self.assertEqual(result.stderr_bytes, len(b'private-error-bytes'))
        self.assertEqual(result.returncode, 0)
        self.assertTrue(all(pipe.closed for pipe in (graph.child.stdin, graph.child.stdout, graph.child.stderr)))

    def test_runtime_false_close_cannot_be_healed_by_zero_child_exit_or_completed_readers(self):
        graph = CallerGraph(False)
        result = self.caller_result(graph, 'runtime')
        self.assertEqual(result.status, 'cleanup_failed'); self.assertIs(result.cleanup_complete, False)
        self.assertEqual(result.returncode, 0)
        self.assertEqual(result.stdout, b'ordinary\x00\x1a\r\noutput')

    def test_runtime_close_exceptions_and_cancellation_still_wait_and_join_every_owned_worker(self):
        for error_type in (OSError, ValueError, KeyboardInterrupt, SystemExit):
            with self.subTest(error=error_type.__name__):
                result = self.caller_result(CallerGraph(error_type('synthetic job close')), 'runtime')
                self.assertEqual(result.status, 'cleanup_failed'); self.assertIs(result.cleanup_complete, False)
                self.assertEqual(result.returncode, 0)

    def test_receipt_success_still_preserves_both_channels_and_closes_capture_after_wait(self):
        graph = CallerGraph()
        result = self.caller_result(graph, 'supervisor')
        self.assertEqual(result['status'], 'child_exited')
        self.assertIs(result['cleanup_complete'], True); self.assertIs(result['output_capture_complete'], True)
        self.assertEqual(result['worker_returncode'], 0)
        self.assertEqual(result['stdout_bytes'], len(b'ordinary\x00\x1a\r\noutput'))
        self.assertEqual(result['stderr_bytes'], len(b'private-error-bytes'))

    def test_receipt_false_close_cannot_qualify_even_with_zero_exit_and_complete_capture(self):
        graph = CallerGraph(False)
        result = self.caller_result(graph, 'supervisor')
        self.assertIs(result['cleanup_complete'], False); self.assertIs(result['output_capture_complete'], True)
        self.assertEqual(result['worker_returncode'], 0)

    def test_receipt_close_exceptions_and_cancellation_do_not_skip_wait_readers_or_capture_close(self):
        for error_type in (OSError, ValueError, KeyboardInterrupt, SystemExit):
            with self.subTest(error=error_type.__name__):
                graph = CallerGraph(error_type('synthetic job close'))
                result = self.caller_result(graph, 'supervisor')
                self.assertIs(result['cleanup_complete'], False); self.assertIs(result['output_capture_complete'], True)
                self.assertEqual(result['worker_returncode'], 0)


    def test_every_result_returning_windows_caller_keeps_constructor_failure_unknown_after_fallback_wait(self):
        for mode in ('runtime', 'supervisor', 'tcp', 'recovery'):
            with self.subTest(mode=mode):
                graph = CallerGraph(construction_error=OSError('job_cleanup_failed'))
                result = self.caller_result(graph, mode)
                cleaned = result.cleanup_complete if mode == 'runtime' else result['cleanup_complete']
                self.assertIs(cleaned, False)
                self.assertFalse(any(event[0] == 'write' for event in graph.events))
                if mode == 'runtime': self.assertEqual(result.status, 'cleanup_failed')
                else: self.assertEqual(result['worker_returncode'], 0)

    def test_tcp_and_recovery_owners_keep_failed_job_close_false_but_finish_their_safe_cleanup_tails(self):
        for mode in ('tcp', 'recovery'):
            for failure in (False, OSError('synthetic close'), KeyboardInterrupt('synthetic cancel'), SystemExit('synthetic exit')):
                with self.subTest(mode=mode, failure=type(failure).__name__):
                    result = self.caller_result(CallerGraph(failure), mode)
                    self.assertIs(result['cleanup_complete'], False)
                    self.assertIs(result['output_capture_complete'], True)
                    self.assertEqual(result['worker_returncode'], 0)

    def test_tcp_and_recovery_positive_owner_paths_do_not_touch_real_profiles_or_execute_target_operations(self):
        for mode in ('tcp', 'recovery'):
            with self.subTest(mode=mode):
                result = self.caller_result(CallerGraph(), mode)
                self.assertIs(result['cleanup_complete'], True)
                self.assertIs(result['output_capture_complete'], True)
                self.assertEqual(result['status'], 'child_exited')

    def android_transfer(self, *, close=True, construction_error=None):
        graph = CallerGraph(close, construction_error=construction_error)
        device = android.Device('D:/Synthetic/never-executed-adb.exe', 'no-real-device')
        expected = android.host.ARTIFACTS['litert'][2]
        calls = []
        def shell(*args, **kwargs):
            calls.append(args)
            if args[:1] == ('df',): return b'Filesystem K Used Available Use Mounted\nfake 4000000 0 4000000 0% /data\n'
            if args[:3] == ('run-as', android.PACKAGE, 'mkdir'): return b''
            if args[:3] == ('run-as', android.PACKAGE, 'sha256sum'): return (expected+'  fake-stage\n').encode()
            if args[:3] == ('run-as', android.PACKAGE, 'mv'): return b''
            raise AssertionError('Unexpected synthetic transfer command')
        source = io.BytesIO(b'not-a-model')
        fake_path = SimpleNamespace(open=lambda *_: source, stat=lambda: SimpleNamespace(st_size=11))
        with patch.object(android.host, 'verify_model', return_value=None), \
             patch.object(android.uuid, 'uuid4', return_value=SimpleNamespace(hex='a' * 32)), \
             patch.object(android.host, 'WindowsJob', side_effect=graph.make_job), \
             patch.object(android.subprocess, 'Popen', return_value=graph.child), \
             patch.object(android, 'Path', return_value=fake_path), \
             patch.object(device, 'script', return_value=b''), \
             patch.object(device, 'shell', side_effect=shell):
            error = None
            try: device.provision_private_model('D:/Synthetic/never-read-model')
            except BaseException as caught: error = caught
        self.assertEqual(graph.constructor_calls, 1)
        self.assertEqual(graph.close_calls, 0 if construction_error is not None else 1)
        self.assertEqual(graph.child.wait_calls, 1)
        self.assertTrue(source.closed)
        if close is True and construction_error is None:
            self.assertIsNone(error)
            self.assertEqual(sum(row[:3] == ('run-as', android.PACKAGE, 'sha256sum') for row in calls), 1)
            self.assertEqual(sum(row[:3] == ('run-as', android.PACKAGE, 'mv') for row in calls), 1)
        else:
            self.assertIsInstance(error, android.Failure)
            self.assertEqual(str(error), 'transfer_failed')
            self.assertIs(error.command_cleaned, False)
            self.assertFalse(any(row[:3] in (('run-as', android.PACKAGE, 'sha256sum'),
                                             ('run-as', android.PACKAGE, 'mv')) for row in calls))

    def test_transfer_positive_is_only_a_synthetic_file_and_shell_boundary(self):
        self.android_transfer()

    def test_transfer_failed_close_and_constructor_cleanup_never_reach_posttransfer_hash_or_move(self):
        self.android_transfer(close=False)
        self.android_transfer(construction_error=OSError('job_cleanup_failed'))

    def test_transfer_close_exceptions_and_cancellation_still_wait_and_refuse_boundedly(self):
        for error_type in (OSError, ValueError, KeyboardInterrupt, SystemExit):
            with self.subTest(error=error_type.__name__):
                self.android_transfer(close=error_type('SYNTHETIC_PRIVATE_HANDLE_CANARY'))


    def test_capture_close_failure_never_certifies_cleanup_or_skips_other_safe_caller_tails(self):
        for mode in ('supervisor', 'tcp', 'recovery'):
            for fault in (False, OSError('synthetic capture close'), ValueError('synthetic capture close'),
                          KeyboardInterrupt(), SystemExit()):
                with self.subTest(mode=mode, fault=type(fault).__name__):
                    graph = CallerGraph()
                    original = graph.capture.close
                    def close():
                        original()
                        return raised(fault)
                    graph.capture.close = close
                    result = graph.run(mode)
                    self.assertIs(result['cleanup_complete'], False)
                    self.assertIs(result['output_capture_complete'], False)
                    self.assertEqual(graph.child.wait_calls, 1)
                    self.assertEqual(graph.capture.close_calls, 1)
                    self.assertTrue(all(pipe.closed for pipe in
                        (graph.child.stdin, graph.child.stdout, graph.child.stderr)))
                    self.assertTrue(all(thread.joins == [2] for thread in graph.threads))

    def test_capture_file_close_cancellation_attempts_all_files_once_and_stays_failed(self):
        for fault in (OSError('synthetic file close'), ValueError('synthetic file close'),
                      KeyboardInterrupt(), SystemExit()):
            with self.subTest(fault=type(fault).__name__):
                calls = []
                class File:
                    def __init__(self, index): self.index = index
                    def close(self):
                        calls.append(self.index)
                        if self.index == 0: raise fault
                capture = object.__new__(environment.LiveOutput)
                capture._lock, capture._closed = threading.Lock(), False
                capture._files, capture.failed = [File(0), File(1)], threading.Event()
                error = None
                try: result = capture.close()
                except BaseException as caught: error = type(caught).__name__
                self.assertIsNone(error, 'Capture close escaped before completing every file tail')
                self.assertIs(result, False)
                self.assertEqual(calls, [0, 1])
                self.assertIs(capture.close(), False)
                self.assertEqual(calls, [0, 1])


if __name__ == '__main__':
    unittest.main()
