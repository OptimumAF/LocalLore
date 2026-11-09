"""Actual SDK10 sequencing/replay with explicitly mocked build/native/socket IO.

No test runs an Android tool, creates a real guest, or changes the shared ledger.
Copyright 2026 LocalLore contributors. SPDX-License-Identifier: Apache-2.0
"""
import copy
import os
from pathlib import Path
import unittest

from benchmarks import android_instrumentation_evidence as evidence
from benchmarks import owned_transcript_ui_contract as contract
from benchmarks import receipt_avd_environment as env
from benchmarks import transcript_ui_build as build
from scripts.tests import test_archive_ui_build_fixtures as data
from scripts.tests import test_transcript_ui_controller_fixtures as fixture

REFUSALS = (env.EnvironmentRefused, contract.TargetRefused, build.BuildRefused,
            evidence.EvidenceRefused)


@unittest.skipUnless(os.name == 'nt', 'Fixed D-only synthetic controller files')
class TranscriptUiControllerTests(unittest.TestCase):
    def test_complete_six_method_graph_and_closed_replay_use_all_original_clients(self):
        graph = fixture.ControllerGraph()
        with graph.inputs():
            result = graph.run()
            self.assertEqual(result['outcome'], 'completed')
            self.assertEqual(result['client_count'], 31)
            self.assertEqual(graph.instrumented, [row[0] for row in contract.INSTRUMENTATIONS])
            self.assertEqual(len(result['methods']), 6)
            self.assertTrue(all(row['record'] and row['evidence'] for row in result['methods']))
            self.assertEqual(graph.verify(), result)
        self.assertEqual(graph.close_calls, 1)
        self.assertTrue(graph.sockets)
        self.assertTrue(all(sock.closed for sock in graph.sockets))
        self.assertFalse(result['feature_acceptance'])

    def test_boot_polling_adds_clients_without_repeating_any_instrumentation(self):
        graph = fixture.ControllerGraph(boot=[b'', b'0\n', b'1\n'])
        with graph.inputs():
            result = graph.run()
            self.assertEqual(result['outcome'], 'completed')
            self.assertEqual(result['client_count'], 33)
            self.assertEqual(len(graph.instrumented), 6)
            self.assertEqual(graph.verify(), result)

    def test_wrong_known_package_filter_refuses_before_staging_any_apk(self):
        graph = fixture.ControllerGraph(fail='wrong_filter')
        with graph.inputs():
            result = graph.run()
        self.assertEqual(result['outcome'], 'refused')
        self.assertEqual(result['phase'], 'setup')
        self.assertFalse(any(argv[0] in ('dd', 'pm') for argv in graph.calls))
        self.assertFalse(graph.instrumented)

    def test_exit_zero_without_junit_start_pass_retains_failed_attempt_and_stops(self):
        graph = fixture.ControllerGraph(fail='junit')
        with graph.inputs():
            result = graph.run()
            self.assertEqual(result['outcome'], 'refused')
            self.assertEqual(result['phase'], 'instrument')
            self.assertEqual(graph.instrumented, list(contract.CLAIM_KINDS[:3]))
            self.assertEqual(len(result['methods']), 3)
            row = result['methods'][-1]
            self.assertIsNotNone(row['record'])
            self.assertIsNone(row['evidence'])
            captured = env.read_json(Path(row['record']['path']))
            self.assertEqual(captured['returncode'], 0)
            self.assertEqual(Path(captured['stdout']['path']).read_bytes(),
                             b'OK (1 test)\nINSTRUMENTATION_CODE: -1\n')
            with self.assertRaises(REFUSALS):
                graph.verify()
        self.assertEqual(graph.close_calls, 1)

    def test_late_junit_failure_after_pass_prefix_stops_at_first_attempt(self):
        graph = fixture.ControllerGraph(fail='junit_late')
        with graph.inputs():
            result = graph.run()
            self.assertEqual(result['outcome'], 'refused')
            self.assertEqual(graph.instrumented, list(contract.CLAIM_KINDS[:1]))
            self.assertEqual(len(result['methods']), 1)
            self.assertIsNotNone(result['methods'][0]['record'])
            self.assertIsNone(result['methods'][0]['evidence'])
            with self.assertRaises(REFUSALS):
                graph.verify()

    def test_missing_shell_exit_is_uncertain_and_cannot_dispatch_later_methods(self):
        graph = fixture.ControllerGraph(fail='missing_exit')
        with graph.inputs():
            result = graph.run()
            self.assertEqual(result['outcome'], 'refused')
            self.assertEqual(result['phase'], 'instrument')
            self.assertEqual(len(result['methods']), 1)
            self.assertEqual(graph.instrumented, list(contract.CLAIM_KINDS[:1]))
            self.assertIsNotNone(result['methods'][0]['record'])
            self.assertIsNone(result['methods'][0]['evidence'])
            with self.assertRaises(REFUSALS):
                graph.verify()
        self.assertTrue(all(sock.closed for sock in graph.sockets))

    def test_unexpected_getter_stderr_refuses_without_install_or_test(self):
        graph = fixture.ControllerGraph(fail='getter_stderr')
        with graph.inputs():
            result = graph.run()
            self.assertEqual(result['outcome'], 'refused')
            self.assertEqual(result['phase'], 'setup')
            self.assertFalse(graph.instrumented)
            self.assertFalse(any(argv[0] in ('dd', 'pm') for argv in graph.calls))

    def test_rejected_build_proof_never_enters_native_or_wire_owner(self):
        graph = fixture.ControllerGraph(fail='build')
        with graph.inputs():
            result = graph.run()
        self.assertEqual(result['outcome'], 'refused')
        self.assertEqual(result['phase'], 'admission')
        self.assertEqual(result['client_count'], 0)
        self.assertFalse(graph.calls)
        self.assertFalse(graph.sockets)
        self.assertEqual(graph.close_calls, 0)

    def test_source_drift_after_passes_preserves_results_without_qualifying(self):
        graph = fixture.ControllerGraph(fail='source_after')
        with graph.inputs():
            result = graph.run()
            self.assertEqual(len(graph.instrumented), 6)
            self.assertEqual(result['outcome'], 'refused')
            self.assertTrue(all(row['evidence'] for row in result['methods']))
            with self.assertRaises(REFUSALS):
                graph.verify()

    def test_unknown_or_failed_observer_close_never_completes_or_retries_close(self):
        for close in (None, False):
            with self.subTest(close=close):
                graph = fixture.ControllerGraph(close=close)
                with graph.inputs():
                    result = graph.run()
                    self.assertEqual(result['outcome'], 'refused')
                    self.assertEqual(result['reason'], 'resource_uncertain')
                    self.assertIs(result['observer_handles_closed'], close)
                    self.assertFalse(result['feature_acceptance'])
                    with self.assertRaises(REFUSALS):
                        graph.verify()
                self.assertEqual(graph.close_calls, 1)

    def test_closed_replay_requires_exact_caller_and_canonical_evidence_location(self):
        graph = fixture.ControllerGraph()
        with graph.inputs():
            result = graph.run()
            self.assertEqual(result['outcome'], 'completed')
            wrong = dict(graph.caller, creation_filetime=graph.caller['creation_filetime'] + 1)
            with self.assertRaises(REFUSALS):
                graph.verify(wrong)
            path = graph.output / 'controller-result-v1.json'
            original = path.read_bytes()
            moved = graph.g.base / 'borrowed-evidence.json'
            moved.write_bytes(Path(result['methods'][0]['evidence']['path']).read_bytes())
            changed = copy.deepcopy(result)
            changed['methods'][0]['evidence'] = data.pin(moved)
            path.write_bytes(data.encoded(changed))
            with self.assertRaises(REFUSALS):
                graph.verify()
            path.write_bytes(original)

    def test_reordered_missing_duplicate_foreign_or_boolean_result_cannot_replay(self):
        graph = fixture.ControllerGraph()
        with graph.inputs():
            result = graph.run()
            self.assertEqual(result['outcome'], 'completed')
            path = graph.output / 'controller-result-v1.json'
            for variant in ('reordered', 'missing', 'duplicate', 'foreign', 'boolean'):
                changed = copy.deepcopy(result)
                if variant == 'reordered':
                    changed['methods'][:2] = changed['methods'][1::-1]
                elif variant == 'missing':
                    changed['methods'].pop()
                elif variant == 'duplicate':
                    changed['methods'][-1] = copy.deepcopy(changed['methods'][0])
                elif variant == 'foreign':
                    changed['methods'][0]['class'] = 'org.locallore.app.ForeignTest'
                else:
                    changed['version'] = True
                path.write_bytes(data.encoded(changed))
                with self.subTest(variant=variant), self.assertRaises(REFUSALS):
                    graph.verify()

    def test_closed_replay_rejects_a_method_deadline_over_ninety_seconds(self):
        graph = fixture.ControllerGraph()
        with graph.inputs():
            result = graph.run()
            self.assertEqual(result['outcome'], 'completed')
            record_path = Path(result['methods'][0]['record']['path'])
            record = env.read_json(record_path)
            record['effective_deadline_ms'] = 90001
            record_path.write_bytes(data.encoded(record))
            result['methods'][0]['record'] = data.pin(record_path)
            (graph.output / 'controller-result-v1.json').write_bytes(data.encoded(result))
            # All hashes are fresh and the generic SDK permits this duration;
            # the controller must enforce its own fixed method-role budget.
            with self.assertRaises(REFUSALS):
                graph.verify()

    def test_closed_replay_rejects_wrong_method_label_with_consistent_proof_contexts(self):
        graph = fixture.ControllerGraph()
        with graph.inputs():
            result = graph.run()
            self.assertEqual(result['outcome'], 'completed')
            record_path = Path(result['methods'][0]['record']['path'])
            record = env.read_json(record_path)
            record['label'] = 'foreign_role'
            for phase in ('server_before', 'server_after'):
                proof_path = Path(record[phase]['path'])
                proof = env.read_json(proof_path)
                proof['context']['label'] = record['label']
                proof_path.write_bytes(data.encoded(proof))
                record[phase] = data.pin(proof_path)
            record_path.write_bytes(data.encoded(record))
            result['methods'][0]['record'] = data.pin(record_path)
            (graph.output / 'controller-result-v1.json').write_bytes(data.encoded(result))
            # Consistent generic proof labels cannot replace the role fixed by
            # this controller's source-defined sequence.
            with self.assertRaises(REFUSALS):
                graph.verify()

    def test_closed_replay_rejects_staging_capture_over_the_runtime_byte_limit(self):
        graph = fixture.ControllerGraph()
        with graph.inputs():
            result = graph.run()
            self.assertEqual(result['outcome'], 'completed')
            setup_path = Path(result['setup']['path'])
            setup = env.read_json(setup_path)
            record_path = Path(setup['staged']['product_apk']['transfer']['path'])
            record = env.read_json(record_path)
            stderr_path = Path(record['stderr']['path'])
            stderr_path.write_bytes(b'S' * 131073)
            record['stderr'] = data.pin(stderr_path)
            record_path.write_bytes(data.encoded(record))
            setup['staged']['product_apk']['transfer'] = data.pin(record_path)
            setup_path.write_bytes(data.encoded(setup))
            result['setup'] = data.pin(setup_path)
            (graph.output / 'controller-result-v1.json').write_bytes(data.encoded(result))
            # Generic SDK records allow larger captures. This role used a
            # 131072-byte producer limit, including its nonempty dd stderr.
            with self.assertRaises(REFUSALS):
                graph.verify()


if __name__ == '__main__':
    unittest.main()
