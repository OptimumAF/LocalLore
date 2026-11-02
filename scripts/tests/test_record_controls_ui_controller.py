"""SDK14 closed replay over ONE synthetic binary graph and preserved deltas.

Build/native observation boundaries are explicit mocks. Wire framing, source
bindings, claims, socket-proof replay and JUnit parsing use production code.
No Android tool, actual ownership or product qualification follows.
Copyright 2026 LocalLore contributors. SPDX-License-Identifier: Apache-2.0
"""
import copy
import os
from pathlib import Path
import unittest

from benchmarks import android_instrumentation_evidence as evidence
from benchmarks import android_process_record_controls_ui_verification as replay
from benchmarks import record_controls_ui_build as build
from benchmarks import owned_record_controls_ui_contract as contract
from benchmarks import receipt_avd_environment as env
from scripts.tests import test_archive_ui_build_fixtures as pins
from scripts.tests import test_record_controls_ui_controller_fixtures as data
from scripts.tests.test_record_controls_ui_controller_fixtures import SELECTORS

REFUSED = (env.EnvironmentRefused, contract.TargetRefused, build.BuildRefused,
           evidence.EvidenceRefused, FileNotFoundError)


def write(path, value):
    Path(path).write_bytes(pins.encoded(value))
    return pins.pin(path)


@unittest.skipUnless(os.name == 'nt', 'Real tiny D: host files, no native/socket calls')
class RecordControlsUiControllerTests(unittest.TestCase):
    def test_one_complete_graph_has_exact_nineteen_claims_and_forty_four_clients(self):
        g = data.shared_graph()
        with g.inputs():
            result = g.verify()
            self.assertEqual(result, g.baseline_result)
            self.assertEqual(result['scope'], 'record-controls-ui-controller-v1')
            self.assertEqual(result['client_count'], 44)
            self.assertEqual(g.instrumented, [row[0] for row in SELECTORS])
            self.assertEqual([(r['kind'], r['class'], r['method']) for r in result['methods']], list(SELECTORS))
            self.assertEqual([Path(r['record']['path']).name for r in result['methods']],
                             ['command-%04d.json' % i for i in range(20, 39)])
            self.assertEqual(len(list((Path(g.a['root']) / 'claims-v1').glob('*.json'))), 19)
            self.assertEqual(Path(result['session']['path']).name, 'sdk-session-v14.json')
            self.assertFalse(result['feature_acceptance'])
        self.assertEqual(g.successful_graphs, 1)
        self.assertEqual(g.close_calls, 1)
        self.assertTrue(all(s.closed for s in g.sockets))

    def test_method_skip_duplicate_reorder_boolean_or_claim_skip_cannot_complete(self):
        g = data.shared_graph()
        for kind in ('missing', 'duplicate', 'reorder', 'boolean', 'claim'):
            with g.inputs(), data.Mutation(g, 'method-' + kind), self.subTest(kind=kind):
                result = copy.deepcopy(g.baseline_result)
                if kind == 'claim':
                    path = Path(g.a['root']) / 'claims-v1' / (SELECTORS[-1][0] + '-v1.json')
                    path.rename(g.g.base / 'preserved-deltas' / ('method-' + kind) / 'omitted-claim-v1.json')
                else:
                    if kind == 'missing': result['methods'].pop(11)
                    elif kind == 'duplicate': result['methods'][-1] = copy.deepcopy(result['methods'][0])
                    elif kind == 'reorder': result['methods'][8:10] = result['methods'][9:7:-1]
                    else: result['client_count'] = True
                    write(g.output / 'controller-result-v1.json', result)
                with self.assertRaises(REFUSED): g.verify()

    def test_foreign_caller_borrowed_proof_and_unknown_close_are_never_qualified(self):
        g = data.shared_graph()
        with g.inputs():
            wrong = dict(g.caller, creation_filetime=g.caller['creation_filetime'] + 1)
            with self.assertRaises(REFUSED): g.verify(wrong)
        for kind in ('borrowed', 'close', 'scope'):
            with g.inputs(), data.Mutation(g, 'ownership-' + kind):
                result = copy.deepcopy(g.baseline_result)
                if kind == 'close':
                    result['observer_handles_closed'] = None
                elif kind == 'scope':
                    result['scope'] = 'inventory-ui-controller-v1'
                else:
                    path = Path(result['methods'][0]['record']['path'])
                    row = env.read_json(path)
                    borrowed = env.read_json(Path(result['methods'][1]['record']['path']))
                    row['server_after'] = borrowed['server_after']
                    result['methods'][0]['record'] = write(path, row)
                write(g.output / 'controller-result-v1.json', result)
                with self.assertRaises(REFUSED): g.verify()

    def test_fresh_consistent_generic_proofs_cannot_widen_labels_or_method_deadlines(self):
        g = data.shared_graph()
        for kind in ('label', 'deadline'):
            with g.inputs(), data.Mutation(g, 'role-' + kind):
                result = copy.deepcopy(g.baseline_result)
                path = Path(result['methods'][-1]['record']['path'])
                row = env.read_json(path)
                if kind == 'deadline': row['effective_deadline_ms'] = 90001
                else:
                    row['label'] = 'unselected_role'
                    for phase in ('server_before', 'server_after'):
                        proof = env.read_json(Path(row[phase]['path']))
                        proof['context']['label'] = row['label']
                        row[phase] = write(row[phase]['path'], proof)
                result['methods'][-1]['record'] = write(path, row)
                write(g.output / 'controller-result-v1.json', result)
                self.assertEqual(len(replay.require_current_clients(g.output, 44, result['session'], g.a)), 44)
                with self.assertRaises(REFUSED): g.verify()

    def test_returncode_zero_and_rebound_raw_hash_do_not_replace_junit_start_pass_frames(self):
        g = data.shared_graph()
        with g.inputs(), data.Mutation(g, 'junit-exit-zero'):
            result = copy.deepcopy(g.baseline_result)
            path = Path(result['methods'][13]['record']['path'])
            row = env.read_json(path)
            stdout = Path(row['stdout']['path'])
            stdout.write_bytes(b'OK (1 test)\nINSTRUMENTATION_CODE: -1\n')
            row['stdout'] = pins.pin(stdout)
            self.assertEqual(row['returncode'], 0)
            result['methods'][13]['record'] = write(path, row)
            write(g.output / 'controller-result-v1.json', result)
            self.assertEqual(len(replay.require_current_clients(g.output, 44, result['session'], g.a)), 44)
            with self.assertRaises(REFUSED): g.verify()

    def test_stage_capture_limit_applies_even_to_nonempty_dd_stderr_with_fresh_hashes(self):
        g = data.shared_graph()
        with g.inputs(), data.Mutation(g, 'stage-cap'):
            result = copy.deepcopy(g.baseline_result)
            setup = env.read_json(Path(result['setup']['path']))
            path = Path(setup['staged']['product_apk']['transfer']['path'])
            row = env.read_json(path)
            Path(row['stderr']['path']).write_bytes(b'x' * 131073)
            row['stderr'] = pins.pin(row['stderr']['path'])
            setup['staged']['product_apk']['transfer'] = write(path, row)
            result['setup'] = write(result['setup']['path'], setup)
            write(g.output / 'controller-result-v1.json', result)
            self.assertEqual(len(replay.require_current_clients(g.output, 44, result['session'], g.a)), 44)
            with self.assertRaises(REFUSED): g.verify()

    def test_fresh_installed_uid_drift_and_bound_runtime_source_drift_both_refuse(self):
        g = data.shared_graph()
        for kind in ('uid', 'source'):
            with g.inputs(), data.Mutation(g, 'drift-' + kind):
                if kind == 'source':
                    with Path(g.python['executable']['path']).open('ab') as stream: stream.write(b'changed')
                else:
                    result = copy.deepcopy(g.baseline_result)
                    installed = env.read_json(Path(result['installed_after']['path']))
                    item = installed['packages']['product_apk']
                    path = Path(item['checks']['uid']['path'])
                    row = env.read_json(path)
                    stdout = Path(row['stdout']['path'])
                    stdout.write_bytes(stdout.read_bytes().replace(b'uid:10001', b'uid:10003'))
                    row['stdout'] = pins.pin(stdout)
                    item['uid'] = 10003
                    item['checks']['uid'] = write(path, row)
                    result['installed_after'] = write(result['installed_after']['path'], installed)
                    write(g.output / 'controller-result-v1.json', result)
                with self.assertRaises(REFUSED): g.verify()

    def test_first_uncertain_method_retains_partial_capture_and_never_sends_the_next_claim(self):
        g = data.ControllerGraph(fail='missing_exit')
        with g.inputs():
            result = g.run()
            self.assertEqual(result['outcome'], 'refused')
            self.assertEqual(result['phase'], 'instrument')
            self.assertEqual(g.instrumented, [SELECTORS[0][0]])
            self.assertEqual(len(result['methods']), 1)
            self.assertIsNotNone(result['methods'][0]['record'])
            self.assertIsNone(result['methods'][0]['evidence'])
            self.assertIsNone(result['installed_after'])
            with self.assertRaises(REFUSED): g.verify()
        self.assertEqual(g.close_calls, 1)
        self.assertTrue(all(s.closed for s in g.sockets))

    def test_skipped_later_profile_method_keeps_prior_evidence_and_never_claims_final_method(self):
        g = data.ControllerGraph(fail='skipped_profile')
        with g.inputs():
            result = g.run()
            self.assertEqual(result['outcome'], 'refused')
            self.assertEqual(result['phase'], 'instrument')
            self.assertEqual(g.instrumented, [row[0] for row in SELECTORS[:13]])
            self.assertEqual(len(result['methods']), 13)
            self.assertTrue(all(row['evidence'] is not None for row in result['methods'][:12]))
            self.assertIsNotNone(result['methods'][-1]['record'])
            self.assertIsNone(result['methods'][-1]['evidence'])
            self.assertIsNone(result['installed_after'])
            self.assertFalse((Path(g.a['root']) / 'claims-v1' / 'profile_accessibility-v1.json').exists())
            with self.assertRaises(REFUSED): g.verify()
        self.assertEqual(g.close_calls, 1)
        self.assertTrue(all(s.closed for s in g.sockets))

    def test_each_of_the_five_new_journeys_is_required_in_the_closed_roster(self):
        g = data.shared_graph()
        self.assertEqual(len(SELECTORS), 19)
        self.assertEqual([row[0] for row in SELECTORS[14:]],
                         ['record_scope_story', 'record_scope_reopen', 'record_scope_detail',
                          'promise_status_browse', 'promise_status_scope'])
        for index in range(14, 19):
            with g.inputs(), data.Mutation(g, 'new-method-missing-%02d' % index), self.subTest(index=index):
                result = copy.deepcopy(g.baseline_result)
                result['methods'].pop(index)
                write(g.output / 'controller-result-v1.json', result)
                with self.assertRaises(REFUSED):
                    g.verify()

    def test_each_new_method_failure_spends_only_its_claim_and_never_attempts_the_next(self):
        for index in range(14, 19):
            kind = SELECTORS[index][0]
            g = data.ControllerGraph(fail='skip:' + kind)
            with self.subTest(kind=kind), g.inputs():
                result = g.run()
                self.assertEqual(result['outcome'], 'refused')
                self.assertEqual(result['phase'], 'instrument')
                self.assertEqual(g.instrumented, [row[0] for row in SELECTORS[:index + 1]])
                self.assertEqual(len(result['methods']), index + 1)
                self.assertTrue(all(row['evidence'] is not None for row in result['methods'][:-1]))
                self.assertIsNotNone(result['methods'][-1]['record'])
                self.assertIsNone(result['methods'][-1]['evidence'])
                self.assertIsNone(result['installed_after'])
                for later, _, _ in SELECTORS[index + 1:]:
                    self.assertFalse((Path(g.a['root']) / 'claims-v1' / (later + '-v1.json')).exists())
                with self.assertRaises(REFUSED):
                    g.verify()
            self.assertEqual(g.close_calls, 1)
            self.assertTrue(all(sock.closed for sock in g.sockets))

    def test_new_journey_order_and_legacy_controller_scope_cannot_retag_complete_evidence(self):
        g = data.shared_graph()
        for fault in ('new_order', 'sdk13_scope'):
            with g.inputs(), data.Mutation(g, 'new-scope-' + fault), self.subTest(fault=fault):
                result = copy.deepcopy(g.baseline_result)
                if fault == 'new_order':
                    result['methods'][14:19] = list(reversed(result['methods'][14:19]))
                else:
                    result['scope'] = 'profile-ui-controller-v1'
                write(g.output / 'controller-result-v1.json', result)
                with self.assertRaises(REFUSED):
                    g.verify()


if __name__ == '__main__':
    unittest.main()
