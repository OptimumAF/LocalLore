"""Original complete SDK18 transcript adversaries over synthetic wire observations."""
import copy
import hashlib
import io
import json
import os
from pathlib import Path
from types import SimpleNamespace
import unittest
from unittest.mock import Mock, patch

from benchmarks import record_cancellation_ui_controller as controller
from benchmarks import owned_record_cancellation_ui_contract as c
from benchmarks import android_process_record_cancellation_ui_client as client
from benchmarks import isolated_adb_lease as base
from scripts.tests import test_record_cancellation_ui_profile_fixtures as f

REFUSED = (c.TargetRefused, controller.env.EnvironmentRefused, base.LeaseRefused)


class RecordCancellationUiBoundedReadTests(unittest.TestCase):
    def test_failed_full_inputs_never_attempts_output_creation_or_owner_construction(self):
        # A shape-valid admission alone is insufficient authority to create a
        # controller directory. Source/running/build checks must precede mkdir.
        mkdir = Mock()
        output = SimpleNamespace(mkdir=mkdir)
        checked = Mock(side_effect=c.TargetRefused('source'))
        with patch.object(controller, '_json', return_value=f.admission()), \
             patch.object(controller, '_output', return_value=output), \
             patch.object(controller, '_directory_identity', return_value=(1, 2)), \
             patch.object(controller, '_inputs', checked), \
             patch.object(controller, '_write', return_value=None), \
             patch.object(controller, 'LiveOwnedRecordCancellationUiTarget') as live, \
             patch.object(controller, 'OwnedRecordCancellationUiSdkCapture') as capture:
            try:
                controller.run(f.legacy.pin('D:/Synthetic/admission.json'), f.legacy.pin('D:/Synthetic/running.json'))
            except c.TargetRefused:
                pass
        self.assertGreaterEqual(checked.call_count, 1)
        self.assertEqual(mkdir.call_count, 0)
        self.assertEqual(live.call_count, 0)
        self.assertEqual(capture.call_count, 0)

    def test_raw_reader_caps_growth_and_binds_returned_bytes_between_two_pin_checks(self):
        expected = b'original reviewed bytes'
        pin = dict(path='D:/Synthetic/only-mocked-stream.bin', bytes=len(expected), sha256=hashlib.sha256(expected).hexdigest())
        for actual in (expected, expected + b'growth', b'X' * len(expected)):
            sizes = []
            class Stream(io.BytesIO):
                def read(self, size=-1):
                    sizes.append(size)
                    return super().read(size)
            opened = Mock(side_effect=lambda *a, **k: Stream(actual))
            checked = Mock()
            with patch.object(controller, '_pin', checked), patch.object(controller.env, 'safe_path', return_value=SimpleNamespace(open=opened)):
                if actual == expected:
                    self.assertEqual(controller._raw(pin), expected)
                else:
                    with self.assertRaises(controller.env.EnvironmentRefused): controller._raw(pin)
            self.assertEqual(sizes, [len(expected) + 1])
            self.assertEqual(opened.call_count, 1)
            self.assertEqual(opened.call_args.args, ('rb',))
            self.assertEqual(checked.call_count, 2)


@unittest.skipUnless(os.name == 'nt', 'physical D synthetic transcript requires Windows')
class RecordCancellationUiControllerTests(unittest.TestCase):
    def completed(self, **kw):
        graph = f.ControllerGraph(**kw)
        with graph.inputs():
            result = graph.run()
            self.assertEqual(result['outcome'], 'completed')
            self.assertEqual(graph.verify(), result)
        return graph, result

    def replace_result(self, graph, result):
        graph.replace(graph.output / 'controller-result-v1.json', result)

    def test_one_boot_has_thirty_commands_sixty_brackets_and_five_exact_methods(self):
        graph, result = self.completed()
        self.assertEqual((result['client_count'], len(graph.calls)), (30, 30))
        self.assertEqual(graph.instrumented, ['record_cancel_1', 'record_cancel_2', 'record_cancel_3', 'record_cancel_4', 'record_cancel_5'])
        self.assertEqual([(r['kind'], r['class'], r['method']) for r in result['methods']], list(f.INSTRUMENTATIONS))
        self.assertEqual(graph.proofs, [(i, p) for i in range(1, 31) for p in ('before', 'after')])
        self.assertEqual(graph.close_calls, 1)
        self.assertIs(result['observer_handles_closed'], True)
        self.assertIs(result['feature_acceptance'], False)
        self.assertTrue(all(sock.closed for sock in graph.sockets))

    def test_boot_prefix_varies_without_borrowing_a_sixth_or_reordered_method(self):
        graph, original = self.completed(boot=[b'0\n', b'1\n'])
        self.assertEqual(original['client_count'], 31)
        self.assertEqual(len(json.loads((graph.output / 'setup-v1.json').read_bytes())['boot']), 2)
        for mutation in ('sixth', 'missing', 'reversed', 'borrowed_record', 'sdk17_kind'):
            result = copy.deepcopy(original)
            if mutation == 'sixth': result['methods'].append(copy.deepcopy(result['methods'][-1]))
            elif mutation == 'missing': result['methods'].pop()
            elif mutation == 'reversed': result['methods'].reverse()
            elif mutation == 'borrowed_record': result['methods'][1]['record'] = copy.deepcopy(result['methods'][0]['record'])
            else: result['methods'][0]['kind'] = 'diagnostic_1'
            self.replace_result(graph, result)
            with self.subTest(mutation=mutation), graph.inputs(), self.assertRaises(REFUSED): graph.verify()

    def test_rebound_last_client_cannot_borrow_sdk17_session_claim_or_preproof(self):
        graph, original = self.completed()
        row = original['methods'][-1]; path = Path(row['record']['path'])
        record = json.loads(path.read_bytes())
        for mutation in ('old_session', 'wrong_index', 'boolean_exit', 'borrowed_preproof'):
            altered = copy.deepcopy(record)
            if mutation == 'old_session': altered['session']['path'] = str(graph.output / 'sdk-session-v17.json')
            elif mutation == 'wrong_index': altered['index'] -= 1
            elif mutation == 'boolean_exit': altered['returncode'] = False
            else: altered['server_before'] = copy.deepcopy(altered['server_after'])
            result = copy.deepcopy(original)
            result['methods'][-1]['record'] = graph.replace(path, altered)
            self.replace_result(graph, result)
            with self.subTest(mutation=mutation), graph.inputs(), self.assertRaises(REFUSED): graph.verify()

    def test_post_identity_is_replayed_from_raw_uid_path_and_hash_not_just_summary(self):
        graph, original = self.completed()
        path = graph.output / 'installed-after-v1.json'
        installed = json.loads(path.read_bytes())
        for mutation in ('uid', 'path', 'borrowed_hash'):
            altered = copy.deepcopy(installed); entry = altered['packages']['test_apk']
            if mutation == 'uid': entry['uid'] = altered['packages']['product_apk']['uid']
            elif mutation == 'path': entry['path'] = altered['packages']['product_apk']['path']
            else: entry['checks']['sha256'] = copy.deepcopy(altered['packages']['product_apk']['checks']['sha256'])
            result = copy.deepcopy(original); result['installed_after'] = graph.replace(path, altered)
            self.replace_result(graph, result)
            with self.subTest(mutation=mutation), graph.inputs(), self.assertRaises(REFUSED): graph.verify()

    def test_method_evidence_cannot_be_rebound_to_a_different_selected_test(self):
        graph, original = self.completed()
        evidence_path = Path(original['methods'][0]['evidence']['path'])
        other = json.loads(Path(original['methods'][1]['evidence']['path']).read_bytes())
        result = copy.deepcopy(original)
        result['methods'][0]['evidence'] = graph.replace(evidence_path, other)
        self.replace_result(graph, result)
        with graph.inputs(), self.assertRaises(REFUSED): graph.verify()
        # Raw summary-only JUnit is not made valid by an otherwise complete SDK
        # client/proof graph or by a process exit code of zero.
        rejected = f.ControllerGraph(fail='junit')
        with rejected.inputs(): returned = rejected.run()
        self.assertEqual(returned['outcome'], 'refused')
        self.assertEqual(len(returned['methods']), 3)
        self.assertEqual(rejected.close_calls, 1)

    def test_late_cancellation_and_unknown_observer_close_remain_refused_after_cleanup(self):
        for close in (None, 1, False):
            graph = f.ControllerGraph(close=close)
            with graph.inputs(): result = graph.run()
            self.assertEqual(result['outcome'], 'refused')
            self.assertIsNot(result['observer_handles_closed'], True)
            self.assertEqual(graph.close_calls, 1)
        graph = f.ControllerGraph(); response = graph.response
        def cancel(argv):
            if argv[:2] == ['am', 'instrument'] and argv[6].endswith(f.INSTRUMENTATIONS[-1][2]):
                raise KeyboardInterrupt('PRIVATE_CANCEL_PAYLOAD')
            return response(argv)
        with graph.inputs(), patch.object(graph, 'response', side_effect=cancel): result = graph.run()
        self.assertEqual(result['outcome'], 'refused')
        self.assertIs(result['feature_acceptance'], False)
        self.assertEqual(graph.close_calls, 1)
        self.assertTrue(all(sock.closed for sock in graph.sockets))
        self.assertNotIn('PRIVATE_CANCEL_PAYLOAD', json.dumps(result))

    def test_capture_close_none_is_expected_but_false_or_exception_never_qualifies(self):
        original = client.OwnedRecordCancellationUiSdkCapture.close
        for outcome in (False, KeyboardInterrupt('PRIVATE_CLOSE_PAYLOAD')):
            graph = f.ControllerGraph()
            def close(cap):
                self.assertIsNone(original(cap))
                if isinstance(outcome, BaseException): raise outcome
                return outcome
            with graph.inputs(), patch.object(client.OwnedRecordCancellationUiSdkCapture, 'close', close): result = graph.run()
            self.assertEqual(result['outcome'], 'refused')
            self.assertEqual(result['reason'], 'resource_uncertain')
            self.assertEqual(graph.close_calls, 1)
            self.assertTrue(all(sock.closed for sock in graph.sockets))
            self.assertNotIn('PRIVATE_CLOSE_PAYLOAD', json.dumps(result))
