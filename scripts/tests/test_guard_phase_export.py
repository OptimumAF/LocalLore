"""Best-effort host guard diagnostics; all target/native/socket IO is simulated."""
import copy
import os
from pathlib import Path
import unittest
from unittest.mock import patch

from benchmarks import original_author_restart_controller as controller
from scripts.tests.test_original_author_restart_controller import ControllerFlow

PHASES = ('total','budget_before','inputs','metadata','observation','validation','budget_after')
RESULT_KEYS = frozenset(('version','protocol','request','session','prerequisite','restart_instrumentation',
    'boot_final','restart_proof','restart_artifacts','client_count','outcome','phase','reason',
    'observer_handles_closed','feature_acceptance','elapsed_ms'))


def snapshot(*, valid=True):
    return dict(version=1,scope='owned-target-guard-phases-v1',valid=valid,
        reason=None if valid else 'clock',observer_closed=True,open_phases=0,
        complete=valid,feature_acceptance=False,instrumentation_overhead_included=True,
        rows=[dict(phase=phase,calls=1,completed=1,raised=0,wall_ns=10,max_ns=10) for phase in PHASES])


@unittest.skipUnless(os.name == 'nt', 'physical D controller fixtures')
class GuardPhaseExportFlowTests(unittest.TestCase):
    def check_result(self,flow,result,outcome):
        self.assertEqual(set(result),RESULT_KEYS)
        self.assertEqual(result['outcome'],outcome)
        self.assertTrue(result['observer_handles_closed'])
        self.assertTrue(flow.live_closed)
        self.assertTrue(all(sock.closed for sock in flow.sockets))
        self.assertEqual(controller.env.read_json(flow.output/'controller-result-v1.json'),result)

    def test_completed_exports_only_after_cleanup_and_authoritative_result(self):
        flow=ControllerFlow();expected=snapshot();calls=[]
        def observed(live):
            self.assertTrue(flow.live_closed)
            recorded=controller.env.read_json(flow.output/'controller-result-v1.json')
            self.assertEqual(set(recorded),RESULT_KEYS)
            self.assertEqual(recorded['outcome'],'completed')
            calls.append(True)
            return copy.deepcopy(expected)
        with patch.object(controller.LiveOwnedRestartTarget,'guard_phase_snapshot',new=observed,create=True):
            result=flow.execute()
        self.check_result(flow,result,'completed')
        path=flow.output/'host-guard-phases-v1.json'
        self.assertTrue(path.is_file(),'closed observation should be exported')
        self.assertEqual(controller.env.read_json(path),expected)
        self.assertEqual(calls,[True])

    def test_refused_primary_publishes_invalid_known_closed_observation_without_acceptance(self):
        flow=ControllerFlow(fail='probe');expected=snapshot(valid=False);calls=[]
        def observed(live):
            self.assertTrue(flow.live_closed)
            self.assertEqual(controller.env.read_json(flow.output/'controller-result-v1.json')['outcome'],'refused')
            calls.append(True)
            return copy.deepcopy(expected)
        with patch.object(controller.LiveOwnedRestartTarget,'guard_phase_snapshot',new=observed,create=True):
            result=flow.execute()
        self.check_result(flow,result,'refused')
        self.assertEqual(result['reason'],'checks_failed')
        path=flow.output/'host-guard-phases-v1.json'
        self.assertTrue(path.is_file(),'invalid diagnostic is retained only as observation')
        self.assertEqual(controller.env.read_json(path),expected)
        self.assertFalse(controller.env.read_json(path)['complete'])
        self.assertEqual(calls,[True])

    def test_ordinary_export_io_failure_preserves_completed_result_and_cleanup(self):
        flow=ControllerFlow();calls=[];original=controller.env.create_json
        def write(path,value):
            if Path(path).name=='host-guard-phases-v1.json':
                self.assertTrue(flow.live_closed)
                self.assertEqual(controller.env.read_json(flow.output/'controller-result-v1.json')['outcome'],'completed')
                calls.append(True)
                raise OSError('synthetic diagnostic output failure')
            return original(path,value)
        with patch.object(controller.LiveOwnedRestartTarget,'guard_phase_snapshot',new=lambda live:snapshot(),create=True), \
                patch.object(controller.env,'create_json',side_effect=write):
            result=flow.execute()
        self.check_result(flow,result,'completed')
        self.assertIsNone(result['reason'])
        self.assertEqual(calls,[True],'diagnostic write should be attempted exactly once')
        self.assertFalse((flow.output/'host-guard-phases-v1.json').exists())


if __name__=='__main__':unittest.main()
