"""Best-effort host guard diagnostics; all target/native/socket IO is simulated."""
import copy
import os
import tempfile
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
        rows=[dict(phase=phase,calls=1,completed=1,raised=0,
            wall_ns=100 if phase=='total' else 10,max_ns=100 if phase=='total' else 10) for phase in PHASES])


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


class _ClosedObservation:
    def __init__(self,value=None,error=None):
        self.value=copy.deepcopy(snapshot() if value is None else value)
        self.error=error
        self.calls=0
    def guard_phase_snapshot(self):
        self.calls+=1
        if self.error is not None:
            raise self.error
        return copy.deepcopy(self.value)


@unittest.skipUnless(os.name == 'nt', 'physical D diagnostic fixtures')
class GuardPhaseExportBoundaryTests(unittest.TestCase):
    def setUp(self):
        self.base=Path(tempfile.mkdtemp(prefix='locallore-guard-export-',dir='D:/Dev/_Temp'))
        self.output=self.base/'output';self.output.mkdir()
        self.identity=controller.directory_checks._identity(self.output)
        self.result=self.output/'controller-result-v1.json'
        self.result.write_bytes(b'original authoritative result sentinel\0\x1a')
        self.before=self.result.read_bytes()
    def export(self,live,*,preserve_failure=False,identity=None,closed=True):
        controller._export_guard_phases(self.output,self.identity if identity is None else identity,
            live,closed,preserve_failure=preserve_failure)
        self.assertEqual(self.result.read_bytes(),self.before)
    def test_existing_diagnostic_cannot_be_overwritten_or_repaired(self):
        target=self.output/'host-guard-phases-v1.json';sentinel=b'partial retained diagnostic\0\x1a'
        target.write_bytes(sentinel)
        self.export(_ClosedObservation())
        self.assertEqual(target.read_bytes(),sentinel)
    def test_directory_identity_drift_refuses_before_snapshot_or_write(self):
        live=_ClosedObservation()
        with patch.object(controller.directory_checks,'_identity',return_value=(self.identity[0],self.identity[1]+1)):
            self.export(live)
        self.assertEqual(live.calls,0)
        self.assertFalse((self.output/'host-guard-phases-v1.json').exists())
    def test_unavailable_identity_or_unknown_close_never_requests_observation(self):
        for identity,closed in ((None,True),(self.identity,False),(self.identity,None)):
            with self.subTest(identity=identity,closed=closed):
                live=_ClosedObservation()
                controller._export_guard_phases(self.output,identity,live,closed,preserve_failure=False)
                self.assertEqual(live.calls,0)
                self.assertFalse((self.output/'host-guard-phases-v1.json').exists())
                self.assertEqual(self.result.read_bytes(),self.before)
    def test_snapshot_without_known_close_is_not_published(self):
        value=snapshot();value.update(observer_closed=False,complete=False)
        self.export(_ClosedObservation(value))
        self.assertFalse((self.output/'host-guard-phases-v1.json').exists())
    def test_malformed_private_canaries_are_never_serialized(self):
        mutations=(lambda v:v.update(raw_story='PRIVATE_TOP_CANARY'),
            lambda v:v['rows'][0].update(arguments='PRIVATE_ROW_CANARY'),
            lambda v:v['rows'][0].update(phase='PRIVATE_PHASE_CANARY'),
            lambda v:v.update(feature_acceptance=True),
            lambda v:v['rows'][0].update(calls=True))
        for change in mutations:
            with self.subTest(mutation=change):
                value=snapshot();change(value)
                self.export(_ClosedObservation(value))
                self.assertFalse((self.output/'host-guard-phases-v1.json').exists())
    def test_interrupt_identity_propagates_without_primary_failure(self):
        for error in (KeyboardInterrupt('synthetic interrupt'),SystemExit(7)):
            for stage in ('snapshot','write'):
                with self.subTest(error=type(error).__name__,stage=stage):
                    live=_ClosedObservation(error=error if stage=='snapshot' else None)
                    original=controller.env.create_json
                    def write(path,value):
                        if Path(path).name=='host-guard-phases-v1.json':raise error
                        return original(path,value)
                    with patch.object(controller.env,'create_json',side_effect=write):
                        with self.assertRaises(BaseException) as raised:
                            self.export(live)
                    self.assertIs(raised.exception,error)
                    self.assertEqual(self.result.read_bytes(),self.before)
                    self.assertFalse((self.output/'host-guard-phases-v1.json').exists())
    def test_interrupt_does_not_replace_already_refused_primary(self):
        for error in (KeyboardInterrupt('synthetic interrupt'),SystemExit(7)):
            for stage in ('snapshot','write'):
                with self.subTest(error=type(error).__name__,stage=stage):
                    live=_ClosedObservation(error=error if stage=='snapshot' else None)
                    original=controller.env.create_json
                    def write(path,value):
                        if Path(path).name=='host-guard-phases-v1.json':raise error
                        return original(path,value)
                    with patch.object(controller.env,'create_json',side_effect=write):
                        self.export(live,preserve_failure=True)
                    self.assertFalse((self.output/'host-guard-phases-v1.json').exists())
    def test_initial_identity_errors_are_observational_but_interrupt_is_not_success(self):
        with patch.object(controller.directory_checks,'_identity',side_effect=OSError('synthetic stat failure')):
            self.assertIsNone(controller._diagnostic_directory_identity(self.output))
        error=KeyboardInterrupt('synthetic capture interrupt')
        with patch.object(controller.directory_checks,'_identity',side_effect=error):
            with self.assertRaises(KeyboardInterrupt) as raised:
                controller._diagnostic_directory_identity(self.output)
        self.assertIs(raised.exception,error)
        self.assertEqual(self.result.read_bytes(),self.before)


if __name__=='__main__':unittest.main()
