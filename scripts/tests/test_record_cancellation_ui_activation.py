"""SDK18 activation orchestration with explicit, entirely synthetic observation ports.

Real cleanup, qualification, run and publication methods execute in these tests;
owner/process/storage observations are fake and cannot confer target authority.
"""
import contextlib
import copy
import io
import json
from pathlib import Path
from types import SimpleNamespace
import unittest
from unittest.mock import Mock, patch

from benchmarks import record_cancellation_ui_activation as a
from benchmarks import owned_record_cancellation_ui_contract as c
from scripts.tests import test_record_cancellation_ui_profile_fixtures as f


class ClosePort:
    def __init__(self, graph, name, result):
        self.graph, self.name, self.result = graph, name, result

    def close(self):
        self.graph.events.append(self.name)
        if isinstance(self.result, BaseException): raise self.result
        return self.result


class CleanupGraph:
    def __init__(self, *, observer=True, capture=True, code=0, stop_error=None, save_error=None):
        self.runtime, self.api, self.bound, self.verify, self.replay, self.check = f.qualification()
        r = self.runtime
        r.begin, r.until = 10.0, 11.0
        r.identity = dict(pid=20, created_filetime=8999)
        r.stop_attempted = r.stop_published = False
        self.events, self.saved = [], []
        self.clock = 10.0
        self.stop_error, self.save_error, self.code = stop_error, save_error, code
        r.observer = ClosePort(self, 'observer_close', observer)
        r.capture = ClosePort(self, 'capture_close', capture)
        def poll():
            self.events.append('owner_poll')
            if isinstance(self.code, BaseException): raise self.code
            return self.code
        r.child = SimpleNamespace(poll=poll)
        r.controller_owner = dict(status='child_exited', worker_returncode=0,
            cleanup_complete=True, output_capture_complete=True)

    def save(self, path, value):
        self.events.append('save:' + path.name)
        self.saved.append((str(path), copy.deepcopy(value)))
        if self.save_error == path.name: raise OSError('PRIVATE_SAVE_PAYLOAD')
        return f.legacy.pin(path)

    def stop(self, *_):
        self.events.append('stop')
        if self.stop_error is not None: raise self.stop_error

    @contextlib.contextmanager
    def ports(self):
        def sleep(seconds): self.clock += seconds
        with patch.object(a, '_api', return_value=self.api), \
             patch.object(a, '_bound', side_effect=lambda pin, *args: copy.deepcopy(self.bound[pin['path']])), \
             patch.object(a, '_inputs'), patch.object(a, '_publish_stop', side_effect=self.stop), \
             patch.object(a, '_save', side_effect=self.save), \
             patch.object(a.time, 'monotonic', side_effect=lambda: self.clock), \
             patch.object(a.time, 'sleep', side_effect=sleep):
            yield


class RecordCancellationUiActivationTests(unittest.TestCase):
    def test_only_sdk18_run_input_and_exact_fixed_paths_pass_the_pure_gate(self):
        api = SimpleNamespace(contract=c)
        original = f.input_value()
        attempts = Mock(side_effect=AssertionError('unexpected authority observation'))
        with patch.object(a, '_api', return_value=api), patch.object(a, '_bound', attempts):
            self.assertIsNone(a._validate_input(original))
            for mutation in ('version', 'scope', 'helper', 'admission', 'override'):
                value = copy.deepcopy(original)
                if mutation == 'version': value['version'] = True
                elif mutation == 'scope': value['scope'] = 'diagnostic-ui-run-input-v1'
                elif mutation == 'helper': value['helper']['path'] = str(a.HELPER.with_name('diagnostic_ui_activation.py'))
                elif mutation == 'admission': value['admission']['path'] = str(a.CONTROLS / 'admission-v1.json')
                else: value['implementation'] = 'caller-chosen'
                with self.subTest(mutation=mutation), self.assertRaises(a.ActivationRefused): a._validate_input(value)
        self.assertEqual(attempts.call_count, 0)

    def test_mismatched_run_profile_refuses_before_authorization_is_consulted(self):
        check = Mock()
        api = SimpleNamespace(contract=c, env=SimpleNamespace(check_authorization=check))
        value, admission = f.input_value(), f.admitted()
        proposal = dict(phase='run', paths=dict(root=admission['guest']['root']), memory_mib=8192, cores=4, max_seconds=1800)
        with patch.object(a, '_api', return_value=api):
            self.assertEqual(a._validate_metadata(value, admission, proposal, {'metadata_only': True}), admission)
            self.assertEqual(check.call_count, 1)
            check.reset_mock()
            for mutation in ('phase', 'cores', 'memory_mib', 'max_seconds', 'root'):
                bad = copy.deepcopy(proposal)
                if mutation == 'phase': bad['phase'] = 'prepare'
                elif mutation == 'root': bad['paths']['root'] = 'D:/Dev/Experiments/LocalLore/2026-11-03-diagnostic-ui-v1/avd-v1'
                else: bad[mutation] = {'cores': True, 'memory_mib': 4096, 'max_seconds': 1800.0}[mutation]
                with self.subTest(mutation=mutation), self.assertRaises(a.ActivationRefused):
                    a._validate_metadata(value, admission, bad, {})
        self.assertEqual(check.call_count, 0)

    def test_terminal_knowledge_is_not_zero_exit_or_boolean_aliasing(self):
        known = dict(status='child_exited', worker_returncode=7, cleanup_complete=True, output_capture_complete=True)
        self.assertTrue(a._known_terminal(known))
        for key, value in (('status', 'running'), ('worker_returncode', False), ('cleanup_complete', 1), ('output_capture_complete', None)):
            bad = dict(known); bad[key] = value
            with self.subTest(key=key): self.assertFalse(a._known_terminal(bad))

    def test_actual_qualification_replays_same_controller_and_bound_closed_ledger(self):
        runtime, api, bound, verify, replay, check = f.qualification()
        inputs = Mock()
        with patch.object(a, '_api', return_value=api), \
             patch.object(a, '_bound', side_effect=lambda pin, *args: copy.deepcopy(bound[pin['path']])), \
             patch.object(a, '_inputs', inputs): runtime.qualify()
        self.assertIs(runtime.result['passed'], True)
        self.assertIs(runtime.result['storage_closed'], True)
        self.assertIs(runtime.result['source_equal'], True)
        self.assertEqual(verify.call_count, 1)
        replay.assert_called_once_with(runtime.controller_result, runtime.value['admission'], runtime.running, runtime.caller)
        inputs.assert_called_once_with(runtime.request['input'])
        self.assertEqual(check.call_args_list[-2].args, (runtime.controller_result,))
        self.assertEqual(check.call_args_list[-1].args, (runtime.result['ledger'],))

    def test_unknown_owner_terminal_is_rejected_before_any_result_or_ledger_read(self):
        for key, value in (('cleanup_known', 1), ('owner_wait_known', False), ('original_owner_returncode', False),
                ('capture_complete', None), ('capture_evidence_known', 1), ('owner_terminal_published', False)):
            runtime, api, _, _, _, _ = f.qualification()
            runtime.result[key] = value
            attempted = Mock(side_effect=AssertionError('must refuse before bound read'))
            with patch.object(a, '_api', return_value=api), patch.object(a, '_bound', attempted):
                with self.subTest(key=key), self.assertRaises(a.ActivationRefused): runtime.qualify()
            self.assertEqual(attempted.call_count, 0)
            self.assertIs(runtime.result['passed'], False)

    def test_binding_cleanup_and_storage_disagreements_cannot_qualify(self):
        for mutation in ('worker_cleanup', 'closure_admission', 'duplicate_root', 'live_root', 'retired_root', 'proposal', 'controller'):
            runtime, api, bound, verify, replay, _ = f.qualification()
            closure = bound[str(Path(runtime.admission['guest']['root']) / 'guest-storage-closure-v1.json')]
            ledger = bound[str(api.env.guest_storage.DEFAULT_REGISTRY / 'ledger-v1.json')]
            if mutation == 'worker_cleanup': verify.return_value['cleanup'][next(iter(c.CLEANUP_KEYS))] = False
            elif mutation == 'closure_admission': closure['admission']['sha256'] = '0' * 64
            elif mutation == 'duplicate_root': ledger['entries'].append(copy.deepcopy(ledger['entries'][0]))
            elif mutation == 'live_root': ledger['entries'][0]['state'] = 'live'
            elif mutation == 'retired_root': ledger['entries'][0]['state'] = 'retired'
            elif mutation == 'proposal': ledger['entries'][0]['proposal_sha256'] = '0' * 64
            else: replay.return_value['outcome'] = 'refused'
            with patch.object(a, '_api', return_value=api), \
                 patch.object(a, '_bound', side_effect=lambda pin, *args: copy.deepcopy(bound[pin['path']])), patch.object(a, '_inputs'):
                with self.subTest(mutation=mutation), self.assertRaises(a.ActivationRefused): runtime.qualify()
            self.assertIs(runtime.result['passed'], False)

    def test_cleanup_attempts_wait_capture_and_terminal_after_stop_or_observer_cancellation(self):
        for kwargs in (dict(stop_error=KeyboardInterrupt('PRIVATE_STOP_PAYLOAD')),
                dict(observer=SystemExit('PRIVATE_OBSERVER_PAYLOAD')), dict(code=True),
                dict(code=RuntimeError('PRIVATE_WAIT_PAYLOAD')), dict(capture=None),
                dict(save_error='original-owner-terminal-v1.json')):
            graph = CleanupGraph(**kwargs)
            with graph.ports(): graph.runtime.cleanup()
            self.assertIs(graph.runtime.result['cleanup_known'], False)
            self.assertIn('observer_close', graph.events)
            self.assertIn('owner_poll', graph.events)
            self.assertIn('capture_close', graph.events)
            self.assertIn('save:original-owner-terminal-v1.json', graph.events)
            self.assertEqual(graph.events.count('stop'), 1)
            self.assertIs(graph.runtime.result['passed'], False)
            self.assertNotIn('PRIVATE_', json.dumps(graph.runtime.result))

    def test_dispatch_interruption_cannot_be_healed_by_later_positive_qualification(self):
        for error in (KeyboardInterrupt('PRIVATE_DISPATCH_PAYLOAD'), SystemExit('PRIVATE_DISPATCH_PAYLOAD'), RuntimeError('PRIVATE_DISPATCH_PAYLOAD')):
            graph = CleanupGraph()
            with graph.ports(), patch.object(graph.runtime, 'dispatch', side_effect=error) as dispatch:
                returned = graph.runtime.run()
            self.assertEqual(returned, 1)
            self.assertEqual(dispatch.call_count, 1)
            self.assertEqual(graph.replay.call_count, 1)
            self.assertIs(graph.runtime.result['owner_qualified'], True)
            self.assertIs(graph.runtime.result['passed'], False)
            self.assertEqual(graph.events.count('stop'), 1)
            self.assertEqual(graph.events.count('capture_close'), 1)
            self.assertNotIn('PRIVATE_DISPATCH_PAYLOAD', json.dumps(graph.saved))

    def test_postqualification_interruption_revokes_pass_and_positive_run_still_works(self):
        positive = CleanupGraph()
        with positive.ports(), patch.object(positive.runtime, 'dispatch'):
            self.assertEqual(positive.runtime.run(), 0)
        self.assertIs(positive.runtime.result['passed'], True)
        for error in (KeyboardInterrupt('PRIVATE_QUALIFY_PAYLOAD'), SystemExit('PRIVATE_QUALIFY_PAYLOAD'), RuntimeError('PRIVATE_QUALIFY_PAYLOAD')):
            graph = CleanupGraph(); qualify = graph.runtime.qualify
            def interrupted():
                qualify()
                self.assertIs(graph.runtime.result['passed'], True)
                raise error
            with graph.ports(), patch.object(graph.runtime, 'dispatch'), patch.object(graph.runtime, 'qualify', side_effect=interrupted):
                self.assertEqual(graph.runtime.run(), 1)
            self.assertIs(graph.runtime.result['passed'], False)
            self.assertEqual(graph.events.count('capture_close'), 1)
            self.assertNotIn('PRIVATE_QUALIFY_PAYLOAD', json.dumps(graph.saved))

    def test_failed_runtime_publication_is_finite_private_and_never_retried(self):
        graph = CleanupGraph(save_error='runtime-result-v1.json')
        stderr = io.StringIO()
        with graph.ports(), patch.object(graph.runtime, 'dispatch'), patch.object(a.sys, 'stderr', stderr):
            self.assertEqual(graph.runtime.run(), 1)
        self.assertIs(graph.runtime.result['passed'], False)
        self.assertIs(graph.runtime.result['cleanup_known'], False)
        self.assertEqual(graph.events.count('save:runtime-result-v1.json'), 1)
        self.assertEqual(graph.events.count('capture_close'), 1)
        self.assertEqual(json.loads(stderr.getvalue()), dict(scope='record-cancellation-ui-activation-runtime-v1', passed=False, publication_error=True))
        self.assertNotIn('PRIVATE_SAVE_PAYLOAD', stderr.getvalue())
