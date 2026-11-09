"""SDK11 host simulation: actual wire/claims/replay/JUnit, no Android execution.

The isolated fixture explicitly replaces build and native observations. Its
synthetic payloads never qualify a genuine APK or an operating-system owner.
Copyright 2026 LocalLore contributors. SPDX-License-Identifier: Apache-2.0
"""
import copy
import os
from pathlib import Path
import unittest

from benchmarks import android_instrumentation_evidence as evidence
from benchmarks import android_process_chat_ui_verification as replay
from benchmarks import chat_ui_build as build
from benchmarks import owned_chat_ui_contract as contract
from benchmarks import receipt_avd_environment as env
from scripts.tests import test_archive_ui_build_fixtures as data
from scripts.tests import test_chat_ui_controller_fixtures as fixture


REFUSED = (env.EnvironmentRefused, contract.TargetRefused,
           build.BuildRefused, evidence.EvidenceRefused)
KINDS = ('chat_ime_latest', 'chat_ime_composer', 'chat_status_history',
         'chat_status_draft', 'chat_heading_selection', 'chat_heading_draft',
         'chat_action_scope', 'chat_action_availability')


def write(path, value):
    Path(path).write_bytes(data.encoded(value))
    return data.pin(path)


@unittest.skipUnless(os.name == 'nt', 'Physical D-only isolated host fixtures')
class ChatUiControllerTests(unittest.TestCase):
    def complete(self, graph):
        result = graph.run()
        self.assertEqual(result['outcome'], 'completed')
        self.assertEqual(graph.verify(), result)
        return result

    def test_complete_eight_claims_replay_original_binary_clients_and_distinct_sdk11_session(self):
        graph = fixture.ControllerGraph()
        with graph.inputs():
            result = self.complete(graph)
            self.assertEqual(tuple(graph.instrumented), KINDS)
            self.assertEqual(result['client_count'], 33)  # One boot plus 32 fixed operations.
            self.assertEqual(len(result['methods']), 8)
            session = env.read_json(Path(result['session']['path']))
            self.assertEqual(session['protocol'], 'sdk-current-chat-ui-v1')
            self.assertEqual(Path(result['session']['path']).name, 'sdk-session-v11.json')
            self.assertEqual(len(list((Path(graph.a['root']) / 'claims-v1').glob('*.json'))), 8)
            self.assertTrue(all(row['record'] and row['evidence'] for row in result['methods']))
            self.assertFalse(result['feature_acceptance'])
        self.assertEqual(graph.close_calls, 1)
        self.assertTrue(graph.sockets)
        self.assertTrue(all(sock.closed for sock in graph.sockets))

    def test_boot_waits_add_observations_without_repeating_any_method(self):
        graph = fixture.ControllerGraph(boot=[b'', b'0\n', b'1\n'])
        with graph.inputs():
            result = self.complete(graph)
            self.assertEqual(result['client_count'], 35)
            self.assertEqual(tuple(graph.instrumented), KINDS)

    def test_build_roster_and_known_wrong_package_filter_refuse_before_any_transfer(self):
        for fail, phase in [('build', 'admission'), ('roster', 'admission'), ('wrong_filter', 'setup')]:
            with self.subTest(fail=fail):
                graph = fixture.ControllerGraph(fail=fail)
                with graph.inputs():
                    result = graph.run()
                self.assertEqual(result['outcome'], 'refused')
                self.assertEqual(result['phase'], phase)
                self.assertFalse(graph.instrumented)
                self.assertFalse(any(argv[0] in ('dd', 'pm') for argv in graph.calls))
                if phase == 'admission':
                    self.assertFalse(graph.sockets)
                    self.assertEqual(graph.close_calls, 0)

    def test_returncode_zero_is_insufficient_and_uncertain_exit_never_dispatches_next_method(self):
        for fail, attempted in [('junit', 3), ('missing_exit', 1)]:
            with self.subTest(fail=fail):
                graph = fixture.ControllerGraph(fail=fail)
                with graph.inputs():
                    result = graph.run()
                    self.assertEqual(result['outcome'], 'refused')
                    self.assertEqual(tuple(graph.instrumented), KINDS[:attempted])
                    self.assertEqual(len(result['methods']), attempted)
                    last = result['methods'][-1]
                    self.assertIsNotNone(last['record'])
                    self.assertIsNone(last['evidence'])
                    if fail == 'junit':
                        self.assertEqual(env.read_json(Path(last['record']['path']))['returncode'], 0)
                    with self.assertRaises(REFUSED):
                        graph.verify()
                self.assertEqual(graph.close_calls, 1)
                self.assertTrue(all(sock.closed for sock in graph.sockets))

    def test_missing_duplicate_reordered_and_borrowed_claim_evidence_cannot_complete(self):
        graph = fixture.ControllerGraph()
        with graph.inputs():
            result = self.complete(graph)
            path = graph.output / 'controller-result-v1.json'
            for change in ('skip', 'duplicate', 'reorder', 'foreign', 'boolean'):
                candidate = copy.deepcopy(result)
                if change == 'skip':
                    candidate['methods'].pop(3)
                elif change == 'duplicate':
                    candidate['methods'][-1] = copy.deepcopy(candidate['methods'][0])
                elif change == 'reorder':
                    candidate['methods'][2:4] = candidate['methods'][3:1:-1]
                elif change == 'foreign':
                    candidate['methods'][0]['class'] = 'org.locallore.app.ui.UnselectedTest'
                else:
                    candidate['client_count'] = True
                write(path, candidate)
                with self.subTest(change=change), self.assertRaises(REFUSED):
                    graph.verify()
            write(path, result)
            claim = Path(graph.a['root']) / 'claims-v1' / (KINDS[0] + '-v1.json')
            original = claim.read_bytes()
            changed = env.read_json(claim)
            changed['caller']['creation_filetime'] += 1
            write(claim, changed)
            with self.assertRaises(REFUSED):
                graph.verify()
            claim.write_bytes(original)
            self.assertEqual(graph.verify(), result)

    def test_complete_graph_requires_actual_caller_and_no_additional_top_level_artifact(self):
        graph = fixture.ControllerGraph()
        with graph.inputs():
            result = self.complete(graph)
            wrong = dict(graph.caller, creation_filetime=graph.caller['creation_filetime'] + 1)
            with self.assertRaises(REFUSED):
                graph.verify(wrong)
            extra = graph.output / 'unselected-method-v1.json'
            extra.write_bytes(b'{}')
            with self.assertRaises(REFUSED):
                graph.verify()
            # Preserve the hostile artifact outside the exact closed output roster.
            extra.rename(graph.g.base / 'retained-unselected-method-v1.json')
            self.assertEqual(graph.verify(), result)

    def test_fresh_hashes_and_generic_proofs_cannot_widen_method_label_or_deadline(self):
        graph = fixture.ControllerGraph()
        with graph.inputs():
            result = self.complete(graph)
            result_path = graph.output / 'controller-result-v1.json'
            record_path = Path(result['methods'][0]['record']['path'])
            original_record = record_path.read_bytes()
            record = env.read_json(record_path)
            proof_bytes = {phase: Path(record[phase]['path']).read_bytes()
                           for phase in ('server_before', 'server_after')}
            for mutation in ('label', 'deadline'):
                current = env.decode_json(original_record)
                if mutation == 'deadline':
                    current['effective_deadline_ms'] = 90001
                else:
                    current['label'] = 'unselected_role'
                    for phase in proof_bytes:
                        proof = env.decode_json(proof_bytes[phase])
                        proof['context']['label'] = current['label']
                        current[phase] = write(current[phase]['path'], proof)
                candidate = copy.deepcopy(result)
                candidate['methods'][0]['record'] = write(record_path, current)
                write(result_path, candidate)
                # The generic SDK grammar accepts these complete fresh proof graphs;
                # the narrower controller role must still refuse them.
                self.assertEqual(len(replay.require_current_clients(
                    graph.output, 33, result['session'], graph.a)), 33)
                with self.subTest(mutation=mutation), self.assertRaises(REFUSED):
                    graph.verify()
                for phase, raw in proof_bytes.items():
                    Path(record[phase]['path']).write_bytes(raw)
                record_path.write_bytes(original_record)
            write(result_path, result)
            self.assertEqual(graph.verify(), result)

    def test_staging_role_combined_capture_limit_is_not_generic_sdk_limit(self):
        graph = fixture.ControllerGraph()
        with graph.inputs():
            result = self.complete(graph)
            setup_path = Path(result['setup']['path'])
            setup = env.read_json(setup_path)
            record_path = Path(setup['staged']['product_apk']['transfer']['path'])
            record = env.read_json(record_path)
            stderr = Path(record['stderr']['path'])
            stderr.write_bytes(b'd' * 131073)
            record['stderr'] = data.pin(stderr)
            setup['staged']['product_apk']['transfer'] = write(record_path, record)
            changed = copy.deepcopy(result)
            changed['setup'] = write(setup_path, setup)
            write(graph.output / 'controller-result-v1.json', changed)
            self.assertEqual(len(replay.require_current_clients(
                graph.output, 33, result['session'], graph.a)), 33)
            with self.assertRaises(REFUSED):
                graph.verify()

    def test_consistently_rebound_installed_uid_drift_cannot_replace_original_package(self):
        graph = fixture.ControllerGraph()
        with graph.inputs():
            result = self.complete(graph)
            after_path = Path(result['installed_after']['path'])
            after = env.read_json(after_path)
            entry = after['packages']['product_apk']
            record_path = Path(entry['checks']['uid']['path'])
            record = env.read_json(record_path)
            raw_path = Path(record['stdout']['path'])
            raw_path.write_bytes(raw_path.read_bytes().replace(b'uid:10001', b'uid:10003'))
            record['stdout'] = data.pin(raw_path)
            entry['uid'] = 10003
            entry['checks']['uid'] = write(record_path, record)
            changed = copy.deepcopy(result)
            changed['installed_after'] = write(after_path, after)
            write(graph.output / 'controller-result-v1.json', changed)
            with self.assertRaises(REFUSED):
                graph.verify()

    def test_source_drift_or_unknown_observer_cleanup_preserves_methods_without_qualification(self):
        for fault, close in [('source_after', True), (None, None)]:
            with self.subTest(fault=fault, close=close):
                graph = fixture.ControllerGraph(fail=fault, close=close)
                with graph.inputs():
                    result = graph.run()
                    self.assertEqual(tuple(graph.instrumented), KINDS)
                    self.assertTrue(all(row['record'] and row['evidence'] for row in result['methods']))
                    self.assertEqual(result['outcome'], 'refused')
                    with self.assertRaises(REFUSED):
                        graph.verify()
                self.assertEqual(graph.close_calls, 1)


if __name__ == '__main__':
    unittest.main()
