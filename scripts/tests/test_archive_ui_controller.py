"""Actual fixed controller/closed replay over a genuine-DEX synthetic build and fake wire."""
import copy
import os
from pathlib import Path
import unittest

from benchmarks import archive_ui_controller as controller
from benchmarks import archive_ui_build as build
from benchmarks import receipt_avd_environment as env
from benchmarks import android_instrumentation_evidence as evidence
from scripts.tests import test_archive_ui_controller_fixtures as fixture
from scripts.tests import test_archive_ui_fixtures as f
from scripts.tests import test_archive_ui_build_fixtures as builds

REFUSALS = (env.EnvironmentRefused,f.legacy.n.TargetRefused,build.BuildRefused,evidence.EvidenceRefused)


@unittest.skipUnless(os.name == 'nt', 'D-only fixed SDK6 simulation')
class ArchiveUiControllerTests(unittest.TestCase):
    def test_full_fixed_flow_and_closed_replay_require_all_ten_real_junit_records(self):
        graph = fixture.ControllerGraph()
        with graph.inputs():
            result = graph.run()
            self.assertEqual(result['outcome'],'completed')
            self.assertEqual(result['client_count'],35)
            self.assertEqual(graph.instrumented,[row[0] for row in f.INSTRUMENTATIONS])
            self.assertEqual(len(result['methods']),10)
            for row in result['methods']:
                self.assertIsNotNone(row['record']); self.assertIsNotNone(row['evidence'])
            self.assertEqual(graph.verify(),result)
        self.assertEqual(graph.close_calls,1)
        self.assertTrue(graph.sockets); self.assertTrue(all(s.closed for s in graph.sockets))
        self.assertFalse(result['feature_acceptance'])

    def test_boot_readiness_can_poll_qualified_empty_and_zero_without_repeating_a_test(self):
        graph = fixture.ControllerGraph(boot=[b'',b'0\n',b'1\n'])
        with graph.inputs():
            result = graph.run()
            self.assertEqual(result['outcome'],'completed')
            setup = env.read_json(graph.output/'setup-v1.json')
            self.assertEqual(len(setup['boot']),3)
            self.assertEqual(result['client_count'],37)
            self.assertEqual(len(graph.instrumented),10)
            graph.verify()

    def test_exit_zero_without_real_start_pass_stops_after_failed_attempt_and_retains_raw(self):
        graph = fixture.ControllerGraph(fail='junit')
        with graph.inputs():
            result = graph.run()
            self.assertEqual(result['outcome'],'refused')
            self.assertEqual(result['phase'],'instrument')
            self.assertEqual(graph.instrumented,[row[0] for row in f.INSTRUMENTATIONS[:3]])
            self.assertEqual(len(result['methods']),3)
            failed = result['methods'][-1]
            self.assertIsNotNone(failed['record']); self.assertIsNone(failed['evidence'])
            record = env.read_json(Path(failed['record']['path']))
            self.assertEqual(record['returncode'],0)
            self.assertEqual(Path(record['stdout']['path']).read_bytes(),b'OK (1 test)\nINSTRUMENTATION_CODE: -1\n')
            with self.assertRaises(REFUSALS): graph.verify()
        self.assertEqual(graph.close_calls,1)

    def test_nonempty_getter_stderr_refuses_before_any_install_or_instrumentation(self):
        graph = fixture.ControllerGraph(fail='getter_stderr')
        with graph.inputs():
            result = graph.run()
            self.assertEqual(result['outcome'],'refused')
            self.assertEqual(result['phase'],'setup')
            self.assertEqual(graph.calls[-1],['getprop','ro.build.version.sdk'])
            self.assertFalse(graph.instrumented)
            self.assertFalse(any(command[0] in ('dd','pm') for command in graph.calls))
            setup = env.read_json(graph.output/'setup-v1.json')
            self.assertIsNotNone(setup['properties']['api'])

    def test_source_drift_after_ten_passes_preserves_records_but_cannot_complete(self):
        graph = fixture.ControllerGraph(fail='source_after')
        with graph.inputs():
            result = graph.run()
            self.assertEqual(len(graph.instrumented),10)
            self.assertEqual(len(result['methods']),10)
            self.assertEqual(result['outcome'],'refused')
            self.assertTrue(all(row['evidence'] is not None for row in result['methods']))
            with self.assertRaises(REFUSALS): graph.verify()

    def test_unknown_observer_close_never_qualifies_and_is_not_retried(self):
        graph = fixture.ControllerGraph(close=None)
        with graph.inputs():
            result = graph.run()
            self.assertEqual(len(graph.instrumented),10)
            self.assertEqual(result['outcome'],'refused')
            self.assertEqual(result['reason'],'resource_uncertain')
            self.assertIsNone(result['observer_handles_closed'])
            with self.assertRaises(REFUSALS): graph.verify()
        self.assertEqual(graph.close_calls,1)

    def test_closed_result_requires_independent_caller_and_canonical_evidence_roles(self):
        graph = fixture.ControllerGraph()
        with graph.inputs():
            result = graph.run(); self.assertEqual(result['outcome'],'completed')
            wrong = dict(graph.caller,creation_filetime=graph.caller['creation_filetime']+1)
            with self.assertRaises(REFUSALS): graph.verify(wrong)
            path = graph.output/'controller-result-v1.json'
            original = path.read_bytes()
            moved = graph.g.base/'borrowed-evidence.json'
            moved.write_bytes(Path(result['methods'][0]['evidence']['path']).read_bytes())
            changed = copy.deepcopy(result); changed['methods'][0]['evidence'] = builds.pin(moved)
            path.write_bytes(builds.encoded(changed))
            with self.assertRaises(REFUSALS): graph.verify()
            path.write_bytes(original)

    def test_closed_result_rejects_reordered_missing_or_duplicate_method_claims(self):
        graph = fixture.ControllerGraph()
        with graph.inputs():
            result = graph.run(); self.assertEqual(result['outcome'],'completed')
            path = graph.output/'controller-result-v1.json'
            for variant in ('reordered','missing','duplicate'):
                changed = copy.deepcopy(result)
                if variant == 'reordered': changed['methods'][:2] = changed['methods'][1::-1]
                elif variant == 'missing': changed['methods'].pop()
                else: changed['methods'][-1] = copy.deepcopy(changed['methods'][0])
                path.write_bytes(builds.encoded(changed))
                with self.subTest(variant=variant), self.assertRaises(REFUSALS): graph.verify()
