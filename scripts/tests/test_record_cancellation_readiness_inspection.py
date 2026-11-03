"""Original late-snapshot oracles; retained tiny metadata, no operational calls."""
import os
import unittest

from scripts import record_cancellation_ui_prepare_inputs as inspection
from scripts.tests.test_record_cancellation_ui_prepare_inputs_fixtures import InspectionGraph


@unittest.skipUnless(os.name == 'nt', 'retained private inspection fixture requires physical D')
class RecordCancellationReadinessInspectionTests(unittest.TestCase):
    def test_current_snapshot_positive_is_still_not_preparation_authority(self):
        with InspectionGraph(inspection, fits=True) as graph:
            before = graph.ledger.read_bytes()
            result = graph.inspect()
            self.assertIs(result['execution_authorized'], False)
            self.assertIs(result['sdk_dispatched'], False)
            self.assertIs(result['model_material'], False)
            self.assertEqual(graph.ledger.read_bytes(), before)
            self.assertEqual(graph.api.activation._source.call_count, 1)
            self.assertTrue((graph.output / 'inspection-result-v1.json').is_file())
            self.assertFalse((graph.output / 'human-authority-v1.json').exists())
            for mutator in graph.mutators.values(): self.assertEqual(mutator.call_count, 0)

    def test_ledger_changed_during_last_activation_observation_cannot_publish_final_result(self):
        with InspectionGraph(inspection, fits=True) as graph:
            before = graph.ledger.read_bytes()
            # This is only the isolated fixture ledger. It changes after the
            # first equality check, inside a legitimate later observation port.
            def drift():
                graph.ledger.write_bytes(b'{"synthetic":true,"late_change":true}\n')
            graph.api.activation._source.side_effect = drift
            with self.assertRaises(inspection.PrepareInputsRefused):
                graph.inspect()
            self.assertEqual(graph.api.activation._source.call_count, 1)
            self.assertNotEqual(graph.ledger.read_bytes(), before)
            self.assertFalse((graph.output / 'inspection-result-v1.json').exists())
            self.assertFalse((graph.output / 'human-authority-v1.json').exists())
            for mutator in graph.mutators.values(): self.assertEqual(mutator.call_count, 0)
