# Copyright 2026 LocalLore contributors. SPDX-License-Identifier: Apache-2.0
"""FIRST fixed controller/closed replay oracles; real validators, synthetic IO."""
import copy
import os
from pathlib import Path
import unittest

from benchmarks import record_ui_controller as controller
from benchmarks import record_ui_build as build
from benchmarks import receipt_avd_environment as env
from benchmarks import android_instrumentation_evidence as evidence
from scripts.tests import test_record_ui_fixtures as f

REFUSALS = (env.EnvironmentRefused, f.core.TargetRefused, build.BuildRefused, evidence.EvidenceRefused)


@unittest.skipUnless(os.name == 'nt', 'Fixed SDK7 simulation with all OS/native/socket IO mocked')
class RecordUiControllerTests(unittest.TestCase):
    def test_full_fixed_ten_method_flow_and_independent_closed_replay_use_only_sdk7(self):
        graph = f.ControllerGraph()
        with graph.inputs():
            result = graph.run()
            self.assertEqual(result['outcome'], 'completed'); self.assertEqual(result['scope'], 'record-ui-controller-v1')
            self.assertEqual(result['client_count'], 35)
            self.assertEqual(graph.instrumented, [row[0] for row in f.INSTRUMENTATIONS])
            self.assertEqual([(row['kind'], row['class'], row['method']) for row in result['methods']], list(f.INSTRUMENTATIONS))
            self.assertEqual(graph.verify(), result)
            self.assertEqual(env.read_json(graph.output / 'request-v1.json')['scope'], 'record-ui-controller-request-v1')
            self.assertEqual(env.read_json(graph.output / 'setup-v1.json')['scope'], 'record-ui-setup-v1')
            self.assertEqual(env.read_json(graph.output / 'installed-after-v1.json')['scope'], 'record-ui-installed-v1')
            self.assertEqual(Path(result['session']['path']).name, f.SESSION_FILE)
            for row in result['methods']:
                self.assertIsNotNone(row['evidence']); self.assertTrue(env.read_json(Path(row['evidence']['path']))['passed'])
                client = env.read_json(Path(row['record']['path']))
                self.assertEqual((client['version'], client['protocol']), (7, f.SDK_PROTOCOL)); self.assertTrue(client['client_qualified'])
        self.assertEqual(graph.close_calls, 1); self.assertTrue(graph.sockets); self.assertTrue(all(sock.closed for sock in graph.sockets))
        self.assertFalse(result['feature_acceptance'])

    def test_exit_zero_without_real_junit_start_pass_refuses_and_retains_attempted_raw(self):
        graph = f.ControllerGraph(fail='junit')
        with graph.inputs():
            result = graph.run()
            self.assertEqual((result['outcome'], result['phase']), ('refused', 'instrument'))
            self.assertEqual(graph.instrumented, [row[0] for row in f.INSTRUMENTATIONS[:3]])
            self.assertEqual(len(result['methods']), 3)
            failed = result['methods'][-1]; self.assertIsNotNone(failed['record']); self.assertIsNone(failed['evidence'])
            client = env.read_json(Path(failed['record']['path']))
            self.assertEqual(client['returncode'], 0)
            self.assertEqual(Path(client['stdout']['path']).read_bytes(), b'OK (1 test)\nINSTRUMENTATION_CODE: -1\n')
            with self.assertRaises(REFUSALS): graph.verify()
        self.assertEqual(graph.close_calls, 1)

    def test_stale_or_cross_profile_build_refuses_before_target_or_socket_activity(self):
        graph = f.ControllerGraph()
        changed = copy.deepcopy(graph.g.manifest); changed['scope'] = 'archive-ui-build-v1'
        graph.g.write(graph.g.manifest_path, f.encoded(changed)); graph.a['artifacts']['build'] = f.pin(graph.g.manifest_path)
        graph.g.write(graph.ap, f.encoded(graph.a)); graph.admission = f.pin(graph.ap)
        graph.d['admission'] = copy.deepcopy(graph.admission)
        graph.g.write(graph.rp, f.encoded(graph.d)); graph.running = f.pin(graph.rp)
        with graph.inputs():
            result = graph.run()
            self.assertEqual((result['outcome'], result['phase']), ('refused', 'admission'))
            self.assertEqual(graph.calls, []); self.assertEqual(graph.sockets, []); self.assertEqual(graph.instrumented, [])
            self.assertEqual(graph.close_calls, 0)

    def test_post_cohort_source_drift_and_unknown_owner_close_never_become_complete(self):
        for kwargs in ({'fail': 'source_after'}, {'close': None}):
            graph = f.ControllerGraph(**kwargs)
            with graph.inputs():
                result = graph.run()
                self.assertEqual(len(graph.instrumented), 10); self.assertEqual(len(result['methods']), 10)
                self.assertTrue(all(row['evidence'] is not None for row in result['methods']))
                self.assertEqual(result['outcome'], 'refused')
                if 'close' in kwargs: self.assertEqual(result['reason'], 'resource_uncertain')
                with self.assertRaises(REFUSALS): graph.verify()
            self.assertEqual(graph.close_calls, 1)

    def test_closed_result_requires_external_caller_and_canonical_order_and_evidence_roles(self):
        graph = f.ControllerGraph()
        with graph.inputs():
            result = graph.run(); self.assertEqual(result['outcome'], 'completed')
            wrong = dict(graph.caller, creation_filetime=graph.caller['creation_filetime'] + 1)
            with self.assertRaises(REFUSALS): graph.verify(wrong)
            path = graph.output / 'controller-result-v1.json'; original = path.read_bytes()
            borrowed = graph.g.base / 'borrowed-evidence.json'
            borrowed.write_bytes(Path(result['methods'][0]['evidence']['path']).read_bytes())
            for fault in ('order', 'missing', 'duplicate', 'evidence', 'scope'):
                changed = copy.deepcopy(result)
                if fault == 'order': changed['methods'][:2] = changed['methods'][1::-1]
                elif fault == 'missing': changed['methods'].pop()
                elif fault == 'duplicate': changed['methods'][-1] = copy.deepcopy(changed['methods'][0])
                elif fault == 'evidence': changed['methods'][0]['evidence'] = f.pin(borrowed)
                else: changed['scope'] = 'archive-ui-controller-v1'
                path.write_bytes(f.encoded(changed))
                with self.subTest(fault=fault), self.assertRaises(REFUSALS): graph.verify()
                path.write_bytes(original)
            self.assertEqual(graph.verify(), result)
