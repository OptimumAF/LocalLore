"""Selected existing PR361 WindowsJob regression oracles, unchanged bodies.

Only the14 real-constructor/fake-kernel methods apply to this dependency lift.
The absent Library recovery executor/transfer callers are not copied or claimed.
Copyright 2026 LocalLore contributors. SPDX-License-Identifier: Apache-2.0
"""
import ctypes
from ctypes import wintypes
import os
import threading
from types import SimpleNamespace
import unittest
from unittest.mock import patch
from benchmarks import runtime_spike as runtime
JOB, PROCESS, PID = 0x7711, 0x7722, 0x7733


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

@unittest.skipUnless(os.name == 'nt', 'Windows ABI; all native calls fake')
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
        second_done = threading.Event()
        results, second_results, errors = [], [], []
        def query(*args):
            if not entered.is_set():
                entered.set()
                if not release.wait(3): raise RuntimeError('synthetic query was not released')
            return original(*args)
        def first():
            try: results.append(job.close())
            except BaseException as error: errors.append(type(error).__name__)
        def second():
            try: second_results.append(job.close())
            except BaseException as error: errors.append(type(error).__name__)
            finally: second_done.set()
        kernel.QueryInformationJobObject.body = query
        with patch.object(runtime, 'time', SimpleNamespace(monotonic=clock.monotonic, sleep=clock.sleep)):
            thread = threading.Thread(target=first)
            other = threading.Thread(target=second)
            thread.start()
            try:
                self.assertTrue(entered.wait(3))
                other.start()
                self.assertTrue(second_done.wait(1), 'Second close waited for the blocked native query')
                self.assertFalse(release.is_set())
                self.assertTrue(thread.is_alive())
                self.assertEqual(second_results, [False])
            finally:
                release.set(); thread.join(timeout=3)
                if other.ident is not None: other.join(timeout=3)
                self.assertFalse(thread.is_alive())
                self.assertFalse(other.is_alive())
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
