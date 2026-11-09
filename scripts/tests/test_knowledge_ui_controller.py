"""Original SDK16 closed replay and first-failure oracles over SDK4 binary wire fixtures."""
import copy
import os
from pathlib import Path
import unittest
from unittest.mock import patch

from benchmarks import android_instrumentation_evidence as junit
from benchmarks import android_process_knowledge_ui_verification as replay
from benchmarks import knowledge_ui_profile_build as build
from benchmarks import knowledge_ui_controller as controller
from benchmarks import owned_knowledge_ui_contract as contract
from benchmarks import receipt_avd_environment as env
from scripts.tests import test_archive_ui_build_fixtures as pins
from scripts.tests import test_knowledge_ui_controller_fixtures as data

REFUSED = (env.EnvironmentRefused, contract.TargetRefused, build.BuildRefused,
    junit.EvidenceRefused, FileNotFoundError)


def write(path, value):
    Path(path).write_bytes(pins.encoded(value)); return pins.pin(path)


@unittest.skipUnless(os.name == 'nt', 'Tiny owned D byte graphs; SDK/native/build observation mocked')
class KnowledgeUiControllerTests(unittest.TestCase):
    def test_closed_roster_requires_all_four_files_and_rejects_every_missing_or_fifth_method(self):
        files = data.SyntheticFiles(); root = files.base / 'rosters'; root.mkdir()
        names = ('request-v1.json', 'sdk-session-v16.json', 'setup-v1.json', 'installed-before-v1.json',
            'installed-after-v1.json', 'controller-result-v1.json')
        for omitted in (None, 1, 2, 3, 4, 'extra'):
            output = root / str(omitted); output.mkdir()
            for directory in ('clients', 'proofs'): (output / directory).mkdir()
            for name in names: files.write(output / name, b'{}\n')
            for index in range(1, 5):
                if index != omitted: files.write(output / ('method-%02d-v1.json' % index), b'{}\n')
            if omitted == 'extra': files.write(output / 'method-05-v1.json', b'{}\n')
            with self.subTest(omitted=omitted):
                if omitted is None: self.assertIsNone(controller._closed_roster(output))
                else:
                    with self.assertRaises(env.EnvironmentRefused): controller._closed_roster(output)

    def test_one_graph_has_four_exact_claims_twenty_nine_clients_and_binary_safe_staging(self):
        graph = data.shared_graph()
        with graph.inputs():
            result = graph.verify()
            self.assertEqual(result, graph.baseline_result)
            self.assertEqual(result['client_count'], 29)
            self.assertEqual([(r['kind'], r['class'], r['method']) for r in result['methods']], list(data.SELECTORS))
            self.assertEqual([Path(r['record']['path']).name for r in result['methods']],
                ['command-%04d.json' % i for i in range(20, 24)])
            self.assertEqual(graph.instrumented, [r[0] for r in data.SELECTORS])
            self.assertEqual(len(list((Path(graph.a['root']) / 'claims-v1').glob('*.json'))), 4)
            self.assertEqual(Path(result['session']['path']).name, 'sdk-session-v16.json')
            setup = env.read_json(result['setup']['path'])
            for role in ('product_apk', 'test_apk'):
                raw = Path(graph.a['artifacts'][role]['path']).read_bytes()
                self.assertIn(b'\x00\x1a\r\n\xff', raw)
                record = env.read_json(setup['staged'][role]['transfer']['path'])
                self.assertEqual(record['stdin_bytes'], len(raw)); self.assertTrue(record['stdin_complete'])
                self.assertEqual(record['stdin_sha256'], graph.a['artifacts'][role]['sha256'])
                self.assertTrue(any(raw in bytes(sock.sent) for sock in graph.sockets))
            self.assertFalse(result['feature_acceptance'])
        self.assertEqual(graph.close_calls, 1); self.assertTrue(all(sock.closed for sock in graph.sockets))

    def test_every_method_is_required_in_order_with_its_own_unborrowed_claim(self):
        graph = data.shared_graph()
        for index in range(4):
            with graph.inputs(), data.Mutation(graph, 'missing-method-%d' % index), self.subTest(index=index):
                result = copy.deepcopy(graph.baseline_result); result['methods'].pop(index)
                write(graph.output / 'controller-result-v1.json', result)
                with self.assertRaises(REFUSED): graph.verify()
        for fault in ('reordered', 'duplicated', 'borrowed_claim', 'fifth'):
            with graph.inputs(), data.Mutation(graph, fault), self.subTest(fault=fault):
                result = copy.deepcopy(graph.baseline_result)
                if fault == 'reordered': result['methods'][1:3] = list(reversed(result['methods'][1:3]))
                elif fault == 'duplicated': result['methods'][-1] = copy.deepcopy(result['methods'][0])
                elif fault == 'fifth': result['methods'].append(copy.deepcopy(result['methods'][-1]))
                else:
                    claim = Path(graph.a['root']) / 'claims-v1' / (data.SELECTORS[2][0] + '-v1.json')
                    value = env.read_json(claim); value['kind'] = data.SELECTORS[1][0]; write(claim, value)
                write(graph.output / 'controller-result-v1.json', result)
                with self.assertRaises(REFUSED): graph.verify()

    def test_each_failed_method_spends_its_claim_retains_partial_bytes_and_stops_before_the_next(self):
        for index, row in enumerate(data.SELECTORS):
            graph = data.ControllerGraph(fail='skip:' + row[0])
            with graph.inputs(), self.subTest(kind=row[0]):
                result = graph.run()
                self.assertEqual(result['outcome'], 'refused'); self.assertEqual(result['phase'], 'instrument')
                self.assertEqual(graph.instrumented, [r[0] for r in data.SELECTORS[:index + 1]])
                self.assertEqual(len(result['methods']), index + 1)
                self.assertTrue(all(r['evidence'] is not None for r in result['methods'][:-1]))
                self.assertIsNotNone(result['methods'][-1]['record']); self.assertIsNone(result['methods'][-1]['evidence'])
                self.assertIsNone(result['installed_after'])
                for later in data.SELECTORS[index + 1:]:
                    self.assertFalse((Path(graph.a['root']) / 'claims-v1' / (later[0] + '-v1.json')).exists())
                calls = list(graph.calls)
                with self.assertRaises(FileExistsError): graph.run()
                self.assertEqual(graph.calls, calls)
                with self.assertRaises(REFUSED): graph.verify()
            self.assertEqual(graph.close_calls, 1); self.assertTrue(all(sock.closed for sock in graph.sockets))

    def test_missing_shell_exit_or_late_junit_failure_never_becomes_an_extra_attempt(self):
        for fault in ('missing_exit', 'junit_late'):
            graph = data.ControllerGraph(fail=fault)
            with graph.inputs(), self.subTest(fault=fault):
                result = graph.run()
                self.assertEqual(result['outcome'], 'refused'); self.assertEqual(graph.instrumented, [data.SELECTORS[0][0]])
                self.assertEqual(len(result['methods']), 1); self.assertIsNone(result['methods'][0]['evidence'])
                self.assertFalse((graph.output / 'method-02-v1.json').exists())
                with self.assertRaises(REFUSED): graph.verify()
            self.assertEqual(graph.close_calls, 1); self.assertTrue(all(sock.closed for sock in graph.sockets))

    def test_rebound_exit_zero_without_junit_start_pass_cannot_replace_raw_method_evidence(self):
        graph = data.shared_graph()
        for index in range(4):
            with graph.inputs(), data.Mutation(graph, 'junit-no-start-%d' % index), self.subTest(index=index):
                result = copy.deepcopy(graph.baseline_result); path = Path(result['methods'][index]['record']['path'])
                row = env.read_json(path); Path(row['stdout']['path']).write_bytes(b'OK (1 test)\nINSTRUMENTATION_CODE: -1\n')
                row['stdout'] = pins.pin(row['stdout']['path']); result['methods'][index]['record'] = write(path, row)
                write(graph.output / 'controller-result-v1.json', result)
                self.assertEqual(len(replay.require_current_clients(graph.output, 29, result['session'], graph.a)), 29)
                with self.assertRaises(REFUSED): graph.verify()

    def test_transfer_truncation_receipt_unknown_cleanup_and_old_sdk_scope_refuse_with_fresh_hashes(self):
        graph = data.shared_graph()
        for fault in ('stdin', 'cleanup', 'scope', 'caller'):
            with graph.inputs(), data.Mutation(graph, 'receipt-' + fault), self.subTest(fault=fault):
                result = copy.deepcopy(graph.baseline_result)
                if fault == 'stdin':
                    setup = env.read_json(result['setup']['path']); path = Path(setup['staged']['product_apk']['transfer']['path'])
                    row = env.read_json(path); row['stdin_bytes'] -= 1
                    setup['staged']['product_apk']['transfer'] = write(path, row)
                    result['setup'] = write(result['setup']['path'], setup)
                elif fault == 'cleanup': result['observer_handles_closed'] = None
                elif fault == 'scope': result['scope'] = 'record-controls-ui-controller-v1'
                else:
                    wrong = dict(graph.caller, creation_filetime=graph.caller['creation_filetime'] + 1)
                    with self.assertRaises(REFUSED): graph.verify(wrong)
                    continue
                write(graph.output / 'controller-result-v1.json', result)
                with self.assertRaises(REFUSED): graph.verify()

    def test_unknown_observer_close_or_mid_run_runtime_source_drift_cannot_qualify_four_passes(self):
        for fault in ('close', 'source'):
            graph = data.ControllerGraph(close=None if fault == 'close' else True,
                fail='source_after' if fault == 'source' else None)
            with graph.inputs(), self.subTest(fault=fault):
                result = graph.run()
                self.assertEqual(graph.instrumented, [r[0] for r in data.SELECTORS])
                self.assertEqual(result['outcome'], 'refused'); self.assertFalse(result['feature_acceptance'])
                with self.assertRaises(REFUSED): graph.verify()
            self.assertEqual(graph.close_calls, 1); self.assertTrue(all(sock.closed for sock in graph.sockets))


    def test_raw_b88_projection_is_private_detached_and_never_accepts_the_old_compatibility_shape(self):
        raw = data.raw_manifest(data.admission()); before = copy.deepcopy(raw)
        projected = controller._projection(raw)
        self.assertEqual(set(projected), {'roster', 'apks'})
        self.assertEqual(projected['roster'], [list(row) for row in data.SELECTORS])
        self.assertEqual(projected['apks']['product_apk']['package'], 'org.locallore.app')
        self.assertEqual(projected['apks']['test_apk']['package'], 'org.locallore.app.test')
        self.assertEqual(raw, before)
        projected['roster'][0][0] = 'cannot mutate raw'
        projected['apks']['product_apk']['binding']['sha256'] = '0' * 64
        self.assertEqual(raw, before)
        with self.assertRaises(env.EnvironmentRefused): controller._projection(projected)
        for fault in ('boolean_version', 'old_scope', 'old_mode', 'extra_role', 'extra_outer',
                      'missing_outer', 'reordered', 'fifth', 'wrong_package', 'audit_failed'):
            value = copy.deepcopy(raw)
            if fault == 'boolean_version': value['version'] = True
            elif fault == 'old_scope': value['scope'] = 'library-ui-build-v1'
            elif fault == 'old_mode': value['mode'] = 'fixed-b80-byte-attestation-v1'
            elif fault == 'extra_role': value['artifacts']['model'] = copy.deepcopy(value['artifacts']['product_apk'])
            elif fault == 'extra_outer': value['roster'] = copy.deepcopy(value['instrumentations'])
            elif fault == 'missing_outer': del value['evidence']
            elif fault == 'reordered': value['instrumentations'][:2] = reversed(value['instrumentations'][:2])
            elif fault == 'fifth': value['instrumentations'].append(value['instrumentations'][0])
            elif fault == 'wrong_package': value['facts']['package_audit']['test_package'] = 'org.locallore.app.litertverify.test'
            else: value['facts']['package_audit']['status'] = 'compiled_only'
            with self.subTest(fault=fault), self.assertRaises(env.EnvironmentRefused):
                controller._projection(value)

    def test_invalid_raw_certificate_or_artifact_binding_refuses_before_native_observer_creation(self):
        graph = data.shared_graph()
        for fault in ('boolean_certificate', 'upper_certificate', 'wrong_binding', 'missing_artifact'):
            raw = data.raw_manifest(graph.a)
            if fault == 'boolean_certificate': raw['facts']['package_audit']['certificate_sha256'] = True
            elif fault == 'upper_certificate': raw['facts']['package_audit']['certificate_sha256'] = 'A' * 64
            elif fault == 'wrong_binding': raw['artifacts']['product_apk'] = copy.deepcopy(raw['artifacts']['test_apk'])
            else: del raw['artifacts']['test_apk']
            with self.subTest(fault=fault), graph.inputs(), \
                 patch.object(controller, 'verify_current', return_value=raw), \
                 patch.object(controller, 'LiveOwnedKnowledgeUiTarget') as live:
                with self.assertRaises(REFUSED): controller._inputs(graph.admission, graph.running)
                live.assert_not_called()

    def test_complete_client_replay_refuses_missing_reordered_borrowed_or_boolean_receipts(self):
        graph = data.shared_graph(); result = graph.baseline_result
        with graph.inputs():
            rows = replay.require_current_clients(graph.output, 29, result['session'], graph.a)
            self.assertEqual([row['index'] for row in rows], list(range(1, 30)))
            self.assertEqual([row['version'] for row in rows], [16] * 29)
        for fault in ('missing', 'reordered', 'borrowed', 'boolean_index', 'boolean_returncode', 'integer_cleanup', 'old_version'):
            with self.subTest(fault=fault), graph.inputs(), data.Mutation(graph, 'client-shape-' + fault):
                first = graph.output/'clients/command-0001.json'
                second = graph.output/'clients/command-0002.json'
                row = env.read_json(first)
                if fault == 'missing':
                    # Preserve bytes outside the closed client directory; Mutation
                    # archives that addition and restores the original afterward.
                    first.rename(graph.g.base/'quarantined-missing-client.json')
                elif fault == 'reordered':
                    other = env.read_json(second); write(first, other); write(second, row)
                elif fault == 'borrowed':
                    row['server_before'] = env.read_json(second)['server_before']; write(first, row)
                else:
                    key, bad = {'boolean_index': ('index', True), 'boolean_returncode': ('returncode', True),
                                'integer_cleanup': ('cleanup_complete', 1), 'old_version': ('version', 15)}[fault]
                    row[key] = bad; write(first, row)
                with self.assertRaises(REFUSED):
                    replay.require_current_clients(graph.output, 29, result['session'], graph.a)
                with self.assertRaises(REFUSED): graph.verify()

    def test_cancellation_during_first_instrument_retains_claim_and_closes_every_owned_socket_once(self):
        graph = data.ControllerGraph(); original = graph.response
        def cancelled(argv):
            if argv[:2] == ['am', 'instrument']:
                raise KeyboardInterrupt('synthetic cancelled caller')
            return original(argv)
        with graph.inputs(), patch.object(graph, 'response', side_effect=cancelled):
            result = graph.run()
            self.assertEqual(result['outcome'], 'refused'); self.assertFalse(result['feature_acceptance'])
            self.assertEqual(result['phase'], 'instrument'); self.assertIsNone(result['installed_after'])
            self.assertTrue((Path(graph.a['root'])/'claims-v1'/(data.SELECTORS[0][0]+'-v1.json')).exists())
            self.assertFalse((Path(graph.a['root'])/'claims-v1'/(data.SELECTORS[1][0]+'-v1.json')).exists())
            with self.assertRaises(REFUSED): graph.verify()
        self.assertEqual(graph.close_calls, 1)
        self.assertTrue(graph.sockets); self.assertTrue(all(sock.closed for sock in graph.sockets))


if __name__ == '__main__': unittest.main()
