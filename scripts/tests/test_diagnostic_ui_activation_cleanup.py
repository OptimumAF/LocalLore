"""Original actual Runtime cleanup/run/publish oracles using fake observations.

No Runtime.dispatch, process, native observer, SDK, file writer or ledger is
executed. Qualification uses the original small synthetic metadata graph.
"""
import contextlib
import copy
import io
from pathlib import Path
import unittest
from unittest.mock import Mock, patch

from benchmarks import diagnostic_ui_activation as activation
from scripts.tests.test_diagnostic_ui_activation import qualification
from scripts.tests import test_diagnostic_ui_profile_fixtures as f

CANARY = 'PRIVATE_OS_PAYLOAD_MUST_NOT_APPEAR_105'


class ScriptedClose:
    def __init__(self, harness, label, outcomes):
        self.harness, self.label, self.outcomes = harness, label, list(outcomes)
        self.calls = 0

    def close(self):
        self.calls += 1
        self.harness.events.append(self.label)
        result = self.outcomes.pop(0) if len(self.outcomes) > 1 else self.outcomes[0]
        if isinstance(result, BaseException): raise result
        return result


class ScriptedChild:
    def __init__(self, harness, outcomes):
        self.harness, self.outcomes, self.calls = harness, list(outcomes), 0

    def poll(self):
        self.calls += 1
        self.harness.events.append('owner.poll')
        result = self.outcomes.pop(0) if len(self.outcomes) > 1 else self.outcomes[0]
        if isinstance(result, BaseException): raise result
        return result


class Harness:
    def __init__(self, *, observer=(True,), capture=(True,), poll=(0,), stop_error=None,
                 binding_error=None, save_error=None):
        self.runtime, self.api, self.bound, self.verify, self.replay, self.check = qualification()
        runtime = self.runtime
        self.events, self.saved, self.stops = [], [], []
        self.clock = 10.0
        self.stop_error, self.binding_error, self.save_error = stop_error, binding_error, save_error
        runtime.begin, runtime.until = 10.0, 11.0
        runtime.identity = dict(pid=20, created_filetime=8999)
        runtime.stop_attempted = runtime.stop_published = False
        runtime.observer = self.observer = ScriptedClose(self, 'observer.close', observer)
        runtime.capture = self.capture = ScriptedClose(self, 'capture.close', capture)
        runtime.child = self.child = ScriptedChild(self, poll)
        runtime.controller_owner = dict(status='child_exited', worker_returncode=0,
            cleanup_complete=True, output_capture_complete=True)
        # This represents a cohort accepted immediately before dispatch returns.
        # It lets a cancellation after that point test run's sticky failure gate.
        runtime.result['controller_passed'] = True
        self.api.env.binding = self.binding

    def binding(self, path):
        self.events.append('binding:' + Path(path).name)
        if self.binding_error is not None and self.binding_error[0] == Path(path).name:
            raise self.binding_error[1]
        return f.legacy.pin(path)

    def stop(self, observer, admission):
        self.events.append('stop')
        self.stops.append((observer, copy.deepcopy(admission)))
        if self.stop_error is not None: raise self.stop_error

    def save(self, path, value):
        self.events.append('save:' + Path(path).name)
        self.saved.append((Path(path), copy.deepcopy(value)))
        if self.save_error is not None and self.save_error[0] == Path(path).name:
            raise self.save_error[1]
        return f.legacy.pin(path)

    def sleep(self, seconds):
        self.clock += seconds

    @contextlib.contextmanager
    def ports(self):
        # Real cleanup/qualify/run/publish methods are not replaced. Every
        # external observation/writer port is narrow and explicitly synthetic.
        with patch.object(activation, '_api', return_value=self.api), \
             patch.object(activation, '_bound', side_effect=lambda pin, *a: copy.deepcopy(self.bound[pin['path']])), \
             patch.object(activation, '_inputs', return_value=None), \
             patch.object(activation, '_publish_stop', side_effect=self.stop), \
             patch.object(activation, '_save', side_effect=self.save), \
             patch.object(activation.time, 'monotonic', side_effect=lambda: self.clock), \
             patch.object(activation.time, 'sleep', side_effect=self.sleep):
            yield


class DiagnosticUiActivationCleanupTests(unittest.TestCase):
    def test_positive_cleanup_and_run_qualify_only_after_all_safe_tails(self):
        h = Harness()
        with h.ports(), patch.object(h.runtime, 'dispatch', return_value=None) as dispatch:
            self.assertEqual(h.runtime.run(), 0)
        dispatch.assert_called_once_with()
        self.assertEqual(h.events[:4], ['stop', 'observer.close', 'owner.poll', 'capture.close'])
        self.assertEqual(len(h.stops), 1)
        self.assertIs(h.runtime.result['cleanup_known'], True)
        self.assertIs(h.runtime.result['owner_wait_known'], True)
        self.assertEqual(h.runtime.result['original_owner_returncode'], 0)
        self.assertIs(h.runtime.result['capture_complete'], True)
        self.assertIs(h.runtime.result['passed'], True)
        self.assertIs(h.runtime.result['feature_acceptance'], False)
        self.assertEqual((h.observer.calls, h.child.calls, h.capture.calls), (1, 1, 1))
        self.assertEqual([path.name for path, _ in h.saved], ['original-owner-terminal-v1.json', 'runtime-result-v1.json'])

    def test_observer_close_false_nonboolean_or_cancellation_never_skips_owner_and_capture(self):
        for result in (False, None, 1, KeyboardInterrupt(CANARY), SystemExit(CANARY)):
            with self.subTest(result=type(result).__name__):
                h = Harness(observer=(result,))
                with h.ports(): h.runtime.cleanup()
                self.assertIs(h.runtime.result['cleanup_known'], False)
                self.assertIs(h.runtime.result['observer_closed'], False)
                self.assertEqual((h.observer.calls, h.child.calls, h.capture.calls), (1, 1, 1))
                self.assertTrue(h.runtime.result['owner_terminal_published'])
                self.assertEqual(h.saved[-1][0].name, 'original-owner-terminal-v1.json')
                self.assertNotIn(CANARY, repr(h.runtime.result))

    def test_capture_close_false_nonboolean_or_raise_preserves_terminal_failure(self):
        for result in (False, None, 1, RuntimeError(CANARY), KeyboardInterrupt(CANARY)):
            with self.subTest(result=type(result).__name__):
                h = Harness(capture=(result,))
                with h.ports(): h.runtime.cleanup()
                self.assertIs(h.runtime.result['cleanup_known'], False)
                self.assertIs(h.runtime.result['capture_complete'], False)
                self.assertIs(h.runtime.result['capture_evidence_known'], False)
                self.assertTrue(h.runtime.result['owner_terminal_published'])
                self.assertEqual((h.observer.calls, h.child.calls, h.capture.calls), (1, 1, 1))
                terminal = h.saved[-1][1]
                self.assertIsNone(terminal['stdout'])
                self.assertIsNone(terminal['stderr'])
                self.assertIs(terminal['cleanup_known'], False)
                self.assertNotIn(CANARY, repr(terminal))

    def test_unknown_wait_boolean_exit_and_poll_cancellation_still_close_capture(self):
        for outcome in ((None,), (False,), (KeyboardInterrupt(CANARY),), (RuntimeError(CANARY),)):
            with self.subTest(outcome=type(outcome[0]).__name__):
                h = Harness(poll=outcome)
                with h.ports(): h.runtime.cleanup()
                self.assertIs(h.runtime.result['owner_wait_known'], False)
                self.assertIsNone(h.runtime.result['original_owner_returncode'])
                self.assertIs(h.runtime.result['cleanup_known'], False)
                self.assertEqual(h.capture.calls, 1)
                self.assertTrue(h.runtime.result['owner_terminal_published'])
                self.assertLessEqual(h.child.calls, 12)

    def test_failed_stop_is_spent_no_retry_and_later_success_cannot_heal_unknown_cleanup(self):
        h = Harness(stop_error=KeyboardInterrupt(CANARY), observer=(False, True), capture=(False, True))
        with h.ports():
            h.runtime.cleanup()
            self.assertTrue(h.runtime.stop_attempted)
            self.assertFalse(h.runtime.stop_published)
            self.assertIs(h.runtime.result['cleanup_known'], False)
            h.stop_error = None
            h.runtime.cleanup()
        self.assertEqual(len(h.stops), 1)
        self.assertFalse(h.runtime.stop_published)
        self.assertIs(h.runtime.result['cleanup_known'], False)
        self.assertEqual((h.observer.calls, h.capture.calls), (2, 2))
        self.assertNotIn(CANARY, repr(h.runtime.result))

    def test_unknown_controller_caller_never_publishes_stop_but_remaining_tails_run(self):
        for mutation in ('caller', 'terminal', 'capture'):
            with self.subTest(mutation=mutation):
                h = Harness()
                if mutation == 'caller': h.runtime.caller = None
                elif mutation == 'terminal': h.runtime.controller_owner['cleanup_complete'] = False
                else: h.runtime.controller_owner['output_capture_complete'] = False
                with h.ports(): h.runtime.cleanup()
                self.assertEqual(h.stops, [])
                self.assertFalse(h.runtime.stop_attempted)
                self.assertFalse(h.runtime.stop_published)
                self.assertEqual((h.observer.calls, h.child.calls, h.capture.calls), (1, 1, 1))

    def test_capture_binding_and_terminal_publication_failures_keep_other_tails_known(self):
        for mutation in ('binding', 'save'):
            with self.subTest(mutation=mutation):
                kwargs = (dict(binding_error=('owner-stderr-v1.bin', OSError(CANARY))) if mutation == 'binding'
                          else dict(save_error=('original-owner-terminal-v1.json', KeyboardInterrupt(CANARY))))
                h = Harness(**kwargs)
                with h.ports(): h.runtime.cleanup()
                self.assertIs(h.runtime.result['cleanup_known'], False)
                self.assertEqual((h.observer.calls, h.child.calls, h.capture.calls), (1, 1, 1))
                self.assertEqual([p.name for p, _ in h.saved], ['original-owner-terminal-v1.json'])
                self.assertNotIn(CANARY, repr(h.runtime.result))

    def test_dispatch_cancellation_is_sticky_even_after_an_accepted_controller_cohort(self):
        for error in (KeyboardInterrupt(CANARY), SystemExit(CANARY), RuntimeError(CANARY)):
            with self.subTest(error=type(error).__name__):
                h = Harness()
                with h.ports(), patch.object(h.runtime, 'dispatch', side_effect=error):
                    code = h.runtime.run()
                self.assertEqual(code, 1)
                self.assertIs(h.runtime.result['passed'], False)
                self.assertEqual(h.runtime.result['dispatch_error'], type(error).__name__)
                self.assertEqual((h.observer.calls, h.child.calls, h.capture.calls), (1, 1, 1))
                self.assertNotIn(CANARY, repr(h.saved))

    def test_qualification_return_edge_cancellation_cannot_preserve_the_success_mark(self):
        # This extension was authored after the return-edge guard was fixed.
        # It carries no additional FIRST/RED claim.
        for error in (KeyboardInterrupt(CANARY), SystemExit(CANARY), RuntimeError(CANARY)):
            with self.subTest(error=type(error).__name__):
                h = Harness()
                actual_qualify = h.runtime.qualify
                reached = []
                def interrupted_after_qualification():
                    actual_qualify()
                    self.assertIs(h.runtime.result['passed'], True)
                    reached.append('positive qualification completed')
                    raise error
                with h.ports(), patch.object(h.runtime, 'dispatch', return_value=None), \
                     patch.object(h.runtime, 'qualify', side_effect=interrupted_after_qualification) as qualify:
                    code = h.runtime.run()
                self.assertEqual(reached, ['positive qualification completed'])
                qualify.assert_called_once_with()
                self.assertEqual(code, 1)
                self.assertIs(h.runtime.result['passed'], False)
                self.assertEqual(h.runtime.result['qualification_error'], type(error).__name__)
                self.assertIs(h.runtime.result['cleanup_known'], True)
                self.assertEqual((h.observer.calls, h.child.calls, h.capture.calls), (1, 1, 1))
                self.assertEqual([path.name for path, _ in h.saved],
                                 ['original-owner-terminal-v1.json', 'runtime-result-v1.json'])
                self.assertNotIn(CANARY, repr(h.saved))
                self.assertNotIn(CANARY, repr(h.runtime.result))

    def test_publish_is_one_attempt_and_request_clock_or_writer_failure_cannot_report_success(self):
        for mutation in ('binding', 'clock', 'writer'):
            with self.subTest(mutation=mutation):
                h = Harness()
                h.runtime.result['passed'] = True
                output = io.StringIO()
                with h.ports(), patch.object(activation.sys, 'stderr', output):
                    if mutation == 'binding':
                        h.binding_error = ('worker-request-v1.json', OSError(CANARY))
                        code = h.runtime.publish()
                    elif mutation == 'clock':
                        with patch.object(activation.time, 'monotonic', side_effect=KeyboardInterrupt(CANARY)):
                            code = h.runtime.publish()
                    else:
                        h.save_error = ('runtime-result-v1.json', SystemExit(CANARY))
                        code = h.runtime.publish()
                self.assertEqual(code, 1)
                self.assertIs(h.runtime.result['passed'], False)
                self.assertIs(h.runtime.result['cleanup_known'], False)
                self.assertEqual([p.name for p, _ in h.saved], ['runtime-result-v1.json'])
                self.assertNotIn(CANARY, output.getvalue())
                self.assertNotIn(CANARY, repr(h.runtime.result))
                if mutation == 'writer':
                    self.assertEqual(output.getvalue(), '{"scope":"diagnostic-ui-activation-runtime-v1","passed":false,"publication_error":true}\n')
