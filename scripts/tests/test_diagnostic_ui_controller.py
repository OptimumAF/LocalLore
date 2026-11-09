"""Original complete SDK17 wire/replay oracles, entirely synthetic host IO."""
import copy
import json
import os
from pathlib import Path
import unittest
from unittest.mock import patch

from benchmarks import diagnostic_ui_controller as controller
from benchmarks import owned_diagnostic_ui_contract as c
from benchmarks import android_process_diagnostic_ui_client as client
from benchmarks import isolated_adb_lease as base
from scripts.tests import test_diagnostic_ui_profile_fixtures as f

REFUSED = (c.TargetRefused, controller.env.EnvironmentRefused, base.LeaseRefused)


@unittest.skipUnless(os.name == 'nt', 'physical D metadata/wire fixture requires Windows')
class DiagnosticUiControllerTests(unittest.TestCase):
    def completed(self, **kwargs):
        graph = f.ControllerGraph(**kwargs)
        with graph.inputs():
            result = graph.run()
            self.assertEqual(result['outcome'], 'completed')
            self.assertEqual(graph.verify(), result)
        return graph, result

    def update_result(self, graph, result):
        graph.replace(graph.output / 'controller-result-v1.json', result)

    def test_complete_one_boot_transcript_is_exactly31_commands_and_six_methods(self):
        graph, result = self.completed()
        self.assertEqual(result['client_count'], 31)
        self.assertEqual(len(graph.calls), 31)
        self.assertEqual(graph.instrumented, [row[0] for row in f.INSTRUMENTATIONS])
        self.assertEqual([(row['kind'], row['class'], row['method']) for row in result['methods']], list(f.INSTRUMENTATIONS))
        self.assertIs(result['observer_handles_closed'], True)
        self.assertIs(result['feature_acceptance'], False)
        self.assertEqual(graph.close_calls, 1)
        self.assertEqual(len(graph.proofs), 62)
        self.assertTrue(all(sock.closed for sock in graph.sockets))

    def test_boot_polling_changes_only_boot_count_and_keeps_all6_selected_methods(self):
        graph, result = self.completed(boot=[b'0\n', b'1\n'])
        self.assertEqual(result['client_count'], 32)
        setup = json.loads((graph.output / 'setup-v1.json').read_bytes())
        self.assertEqual(len(setup['boot']), 2)
        self.assertEqual(len(result['methods']), 6)

    def test_closed_result_rejects_missing_extra_reordered_and_borrowed_method_records(self):
        for mutation in ('missing', 'extra', 'reordered', 'borrowed', 'kind16'):
            with self.subTest(mutation=mutation):
                graph, result = self.completed()
                if mutation == 'missing': result['methods'].pop()
                elif mutation == 'extra': result['methods'].append(copy.deepcopy(result['methods'][0]))
                elif mutation == 'reordered': result['methods'].reverse()
                elif mutation == 'borrowed': result['methods'][1]['record'] = copy.deepcopy(result['methods'][0]['record'])
                else: result['methods'][0]['kind'] = 'knowledge_1'
                self.update_result(graph, result)
                with graph.inputs(), self.assertRaises(REFUSED): graph.verify()

    def test_closed_client_count_and_closure_flags_do_not_coerce_boolean_scalars(self):
        for key, value in (('client_count', True), ('client_count', 30), ('client_count', 32),
                           ('observer_handles_closed', 1), ('feature_acceptance', 0), ('elapsed_ms', False)):
            with self.subTest(key=key, value=value):
                graph, result = self.completed()
                result[key] = value
                self.update_result(graph, result)
                with graph.inputs(), self.assertRaises(REFUSED): graph.verify()

    def test_rebound_last_instrument_client_rejects_boolean_or_borrowed_identity(self):
        for mutation in ('returncode', 'index', 'qualified', 'session', 'operation'):
            with self.subTest(mutation=mutation):
                graph, result = self.completed()
                row = result['methods'][-1]
                path = Path(row['record']['path'])
                client_record = json.loads(path.read_bytes())
                if mutation == 'returncode': client_record['returncode'] = False
                elif mutation == 'index': client_record['index'] = True
                elif mutation == 'qualified': client_record['client_qualified'] = 1
                elif mutation == 'session': client_record['session']['path'] = str(graph.output / 'sdk-session-v16.json')
                else: client_record['operation']['argv'] = f.instrument(f.INSTRUMENTATIONS[0])
                row['record'] = graph.replace(path, client_record)
                self.update_result(graph, result)
                with graph.inputs(), self.assertRaises(REFUSED): graph.verify()

    def test_pre_post_uid_path_and_hash_identity_cannot_be_borrowed(self):
        for mutation in ('uid', 'path', 'package', 'hash'):
            with self.subTest(mutation=mutation):
                graph, result = self.completed()
                path = graph.output / 'installed-after-v1.json'
                installed = json.loads(path.read_bytes())
                item = installed['packages']['product_apk']
                if mutation == 'uid': item['uid'] += 1
                elif mutation == 'path': item['path'] = '/data/app/foreign/base.apk'
                elif mutation == 'package': item['package'] = f.TEST
                else: item['checks']['sha256'] = copy.deepcopy(installed['packages']['test_apk']['checks']['sha256'])
                result['installed_after'] = graph.replace(path, installed)
                self.update_result(graph, result)
                with graph.inputs(), self.assertRaises(REFUSED): graph.verify()

    def test_unlisted_output_and_raw_junit_summary_cannot_qualify_a_complete_cohort(self):
        graph, _ = self.completed()
        graph.g.write(graph.output / 'borrowed-result-v16.json', b'{}')
        with graph.inputs(), self.assertRaises(REFUSED): graph.verify()
        # Accepted fixture emits summary-only instrumentation output for the
        # third diagnostic method. This must fail actual raw-JUnit validation.
        graph = f.ControllerGraph(fail='junit')
        with graph.inputs(): result = graph.run()
        self.assertEqual(result['outcome'], 'refused')
        self.assertFalse(result['feature_acceptance'])
        self.assertEqual(graph.close_calls, 1)

    def test_unknown_observer_or_capture_close_still_attempts_remaining_cleanup(self):
        for observed in (False, None, 1):
            with self.subTest(observer=observed):
                graph = f.ControllerGraph(close=observed)
                with graph.inputs(): result = graph.run()
                self.assertEqual(result['outcome'], 'refused')
                self.assertIsNot(result['observer_handles_closed'], True)
                self.assertEqual(graph.close_calls, 1)
        original = client.OwnedDiagnosticUiSdkCapture.close
        for outcome in ('false', 'raise'):
            with self.subTest(capture=outcome):
                graph = f.ControllerGraph()
                def uncertain(cap):
                    original(cap)
                    if outcome == 'raise': raise KeyboardInterrupt()
                    return False
                with graph.inputs(), patch.object(client.OwnedDiagnosticUiSdkCapture, 'close', uncertain):
                    result = graph.run()
                self.assertEqual(result['outcome'], 'refused')
                self.assertEqual(graph.close_calls, 1)
                self.assertTrue(all(sock.closed for sock in graph.sockets))

    def test_late_source_drift_or_cancelled_command_is_terminal_refused(self):
        graph = f.ControllerGraph(fail='source_after')
        with graph.inputs(): result = graph.run()
        self.assertEqual(result['outcome'], 'refused')
        self.assertEqual(graph.close_calls, 1)
        graph = f.ControllerGraph()
        original = graph.response
        def cancelled(argv):
            if argv[:2] == ['am', 'instrument']: raise KeyboardInterrupt()
            return original(argv)
        with graph.inputs(), patch.object(graph, 'response', side_effect=cancelled):
            result = graph.run()
        self.assertEqual(result['outcome'], 'refused')
        self.assertIs(result['feature_acceptance'], False)
        self.assertEqual(graph.close_calls, 1)
        self.assertTrue(all(sock.closed for sock in graph.sockets))
