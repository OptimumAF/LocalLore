"""Independent complete/partial SDK9 acquisition graphs, entirely host synthetic.

All source/build/v3-proof/claim/client/closed-result validators remain real.
Copyright 2026 LocalLore contributors. SPDX-License-Identifier: Apache-2.0
"""
import copy
import os
from pathlib import Path
import unittest
from unittest.mock import patch

from benchmarks import owned_target_owner as native_owner
from benchmarks import owned_presentation_process_owner as owner
from benchmarks import owned_presentation_process_contract as contract
from benchmarks import presentation_process_controller as controller
from benchmarks import presentation_process_build as build
from benchmarks import receipt_avd_environment as env
from scripts.tests import test_presentation_process_runner_controller_fixtures as f


@unittest.skipUnless(os.name == 'nt', 'D-only synthetic acquisition graph; native and wire IO mocked')
class PresentationProcessRunnerControllerTests(unittest.TestCase):
    def test_complete_external_graph_replays_original_raw_records_all_three_packages_and_one_claim(self):
        graph = f.ControllerGraph(boot=[b'', b'1\n'])
        with graph.inputs():
            result = graph.run()
            self.assertEqual(result['outcome'], 'completed')
            self.assertEqual(result['client_count'], 40)
            self.assertEqual(graph.verify(), result)
        self.assertFalse(result['feature_acceptance'])
        self.assertEqual(graph.instrumented, ['presentation_process'])
        self.assertEqual(graph.close_calls, 1)
        self.assertEqual(graph.installed, set(f.PACKAGES))
        self.assertEqual(len(graph.proofs), 80)
        self.assertTrue(all(sock.closed for sock in graph.sockets))
        self.assertEqual(env.read_json(result['evidence']['path']), graph.result)
        for leaf in ('created', 'saved', 'commands'):
            raw = result['product_records'][leaf]['raw']
            self.assertEqual(Path(raw['path']).read_bytes(), graph.records[leaf])
            record = env.read_json(result['product_records'][leaf]['record']['path'])
            self.assertEqual(record['stdout'], raw)
        for phase in ('installed_before', 'installed_after'):
            packages = env.read_json(result[phase]['path'])['packages']
            self.assertEqual({row['package'] for row in packages.values()}, set(f.PACKAGES))
            self.assertEqual(len({row['uid'] for row in packages.values()}), 3)
        self.assertEqual(len(list((Path(graph.a['root']) / 'claims-v1').glob('*.json'))), 1)
        self.assertEqual(set(path.name for path in graph.output.iterdir()), {
            'request-v1.json', 'sdk-session-v9.json', 'setup-v1.json', 'installed-before-v1.json',
            'presentation-evidence-v1.json', 'installed-after-v1.json', 'controller-result-v1.json', 'clients', 'proofs'})

    def test_wrong_or_stale_build_and_missing_controller_refuse_before_native_owner_initialization(self):
        for mutation in ('missing', 'stale', 'wrong_manifest'):
            graph = f.ControllerGraph()
            if mutation == 'missing':
                del graph.a['artifacts']['controller_apk']
                graph.rebind_admission()
            elif mutation == 'stale':
                with graph.g.apks['controller_apk'].open('ab') as stream:
                    stream.write(b'changed after build admission')
            else:
                value = env.read_json(graph.g.spec['manifest_path'])
                value['scope'] = 'record-ui-build-v1'
                graph.g.write(graph.g.spec['manifest_path'], env.encoded(value))
                graph.a['artifacts']['build'] = env.binding(graph.g.spec['manifest_path'])
                graph.rebind_admission()
            with self.subTest(mutation=mutation), graph.inputs(), \
                 patch.object(native_owner._LiveOwnedTarget, '__init__', side_effect=AssertionError('native constructor')) as native:
                with self.assertRaises((contract.TargetRefused, build.BuildRefused,
                                        env.EnvironmentRefused, owner.OwnerRefused)):
                    owner.LiveOwnedPresentationProcessTarget(graph.admission, graph.running)
                native.assert_not_called()
            self.assertEqual(graph.calls, [])
            self.assertEqual(graph.sockets, [])
        class Derived(owner.LiveOwnedPresentationProcessTarget):
            pass
        graph = f.ControllerGraph()
        with graph.inputs(), patch.object(native_owner._LiveOwnedTarget, '__init__',
                                         side_effect=AssertionError('native constructor')) as native:
            with self.assertRaises(owner.OwnerRefused):
                Derived(graph.admission, graph.running)
            native.assert_not_called()

    def test_sdk_return_zero_without_real_v3_frame_is_preserved_refused_and_never_retried(self):
        graph = f.ControllerGraph(fail='invalid_exit_zero')
        with graph.inputs():
            result = graph.run()
        self.assertEqual(result['outcome'], 'refused')
        self.assertEqual(graph.instrumented, ['presentation_process'])
        self.assertIsNone(result['evidence'])
        self.assertIsNone(result['installed_after'])
        original = env.read_json(result['execution']['record']['path'])
        self.assertEqual(original['returncode'], 0)
        self.assertTrue(original['client_qualified'])
        self.assertEqual(Path(original['stdout']['path']).read_bytes(), b'OK (1 test)\nINSTRUMENTATION_CODE: -1\n')
        self.assertEqual(graph.close_calls, 1)

    def test_wrong_installed_package_or_probe_uid_never_becomes_completed_proof(self):
        for failure in ('wrong_installed_path', 'wrong_leaf_uid'):
            graph = f.ControllerGraph(fail=failure)
            with self.subTest(failure=failure), graph.inputs():
                result = graph.run()
            self.assertEqual(result['outcome'], 'refused')
            self.assertFalse(result['feature_acceptance'])
            self.assertIsNone(result['evidence'])
            self.assertIsNone(result['installed_after'])
            self.assertEqual(graph.close_calls, 1)
            self.assertTrue(all(sock.closed for sock in graph.sockets))

    def test_source_drift_or_unknown_observer_close_cannot_promote_successful_raw_case(self):
        for options in (dict(fail='source_after'), dict(close=False)):
            graph = f.ControllerGraph(**options)
            with self.subTest(options=options), graph.inputs():
                result = graph.run()
            self.assertEqual(result['outcome'], 'refused')
            self.assertFalse(result['feature_acceptance'])
            self.assertEqual(graph.close_calls, 1)
            self.assertLessEqual(len(graph.instrumented), 1)

    def test_closed_reader_rejects_wrong_caller_changed_raw_and_noncontiguous_client_roster(self):
        for mutation in ('caller', 'raw', 'roster'):
            graph = f.ControllerGraph()
            with graph.inputs():
                result = graph.run()
                self.assertEqual(result['outcome'], 'completed')
                self.assertEqual(graph.verify(), result)
                caller = copy.deepcopy(graph.caller)
                if mutation == 'caller':
                    caller['creation_filetime'] += 1
                elif mutation == 'raw':
                    record = env.read_json(result['execution']['record']['path'])
                    Path(record['stdout']['path']).write_bytes(b'substituted source-bound execution bytes')
                else:
                    path = graph.output / 'clients/command-0001.json'
                    path.rename(graph.g.base / 'retained-original-first-client.json')
                with self.subTest(mutation=mutation), self.assertRaises((contract.TargetRefused,
                        env.EnvironmentRefused, build.BuildRefused, owner.OwnerRefused, OSError)):
                    graph.verify(caller)


if __name__ == '__main__':
    unittest.main()
