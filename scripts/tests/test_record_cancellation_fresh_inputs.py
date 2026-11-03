"""Original SDK18 prepared-to-input joins over retained isolated metadata.

Shared proposal/prepared/storage validators are real. SDK installation, source,
build, token lookup and admission observations are explicitly synthetic ports.
"""
import copy
import os
from pathlib import Path
import unittest
from unittest.mock import patch

from scripts import run_record_cancellation_ui_fresh as subject
from scripts import record_cancellation_ui_fresh_contract as rules
from scripts.tests import test_record_cancellation_fresh_input_fixtures as f

REFUSED = (rules.FreshRunRefused, f.env.EnvironmentRefused, f.storage.StorageRefused)


@unittest.skipUnless(os.name == 'nt', 'shared validators require an isolated physical D fixture')
class RecordCancellationFreshInputsTests(unittest.TestCase):
    def test_fresh_prepared_positive_uses_real_shared_proofs_and_publishes_activation_input_last(self):
        with f.FreshGraph() as graph:
            ledger = (graph.registry / 'ledger-v1.json').read_bytes()
            with patch.object(f.history, 'validate_history', wraps=f.history.validate_history) as recovered_history:
                prepared_pin = graph.prepared()
                result = graph.create()
            self.assertEqual(prepared_pin, f.env.binding(graph.registry / 'ledger-v1.json'))
            self.assertEqual((graph.registry / 'ledger-v1.json').read_bytes(), ledger)
            self.assertEqual(recovered_history.call_count, 0)
            self.assertEqual(len(graph.sources), 28)
            self.assertEqual(len(graph.methods), 5)
            proposal = f.env.read_json(result['run_proposal']['path'])
            admission = f.env.read_json(result['admission']['path'])
            value = f.env.read_json(result['input']['path'])
            self.assertEqual(proposal['phase'], 'run')
            self.assertEqual(proposal['prepare_proposal'], graph.prepare_pin)
            self.assertEqual((admission['guest']['memory_mib'], admission['guest']['cores'], admission['guest']['api']), (8192, 4, 35))
            self.assertEqual(admission['protocol'], 'owned-emulator-record-cancellation-ui-v1')
            self.assertEqual(value, dict(version=1, scope='record-cancellation-ui-run-input-v1',
                admission=result['admission'], helper=f.env.binding(graph.api.activation.HELPER)))
            self.assertLess(graph.events.index('plan_run'), graph.events.index('authorize'))
            self.assertLess(graph.events.index('authorize'), graph.events.index('admission'))
            self.assertLess(graph.events.index('admission'), graph.events.index('build'))
            self.assertEqual(graph.api.env.plan_run.call_count, 1)
            self.assertEqual(graph.api.env.prepare.call_count, 0)
            self.assertEqual(graph.api.activation.execute.call_count, 0)

    def test_prepared_terminal_and_ledger_disagreements_refuse_before_run_planning(self):
        for mutation in ('terminal_bool', 'terminal_cleanup', 'terminal_proposal', 'entry_digest',
                         'entry_state', 'reservation_bool', 'recovery', 'retirement'):
            with self.subTest(mutation=mutation), f.FreshGraph() as graph:
                if mutation.startswith('terminal'):
                    value = copy.deepcopy(graph.prepare_result)
                    if mutation == 'terminal_bool': value['version'] = True
                    elif mutation == 'terminal_cleanup': value['child_cleanup_complete'] = False
                    else: value['proposal_sha256'] = '0' * 64
                    graph.write(graph.guest / 'prepare-result-v1.json', value)
                else:
                    if mutation == 'entry_digest': graph.entry['proposal_sha256'] = '0' * 64
                    elif mutation == 'entry_state': graph.entry['state'] = 'retained'
                    elif mutation == 'reservation_bool': graph.entry['reserved_bytes'] = True
                    elif mutation == 'recovery': graph.entry['recovery'] = {'outcome': 'unknown'}
                    else: graph.entry['retirement'] = {'unexpected': True}
                    graph.write_ledger()
                with self.assertRaises(REFUSED): graph.create()
                self.assertEqual(graph.api.env.plan_run.call_count, 0)
                self.assertEqual(graph.api.env.prepare.call_count, 0)
                self.assertEqual(graph.api.activation.execute.call_count, 0)
                self.assertFalse(rules.RUN_PROPOSAL.exists())
                self.assertFalse(rules.RUNTIME.exists())
                self.assertFalse(rules.INPUT.exists())

    def test_stale_source_or_authorization_does_not_publish_or_enter_activation(self):
        for mutation in ('source', 'authorization'):
            with self.subTest(mutation=mutation), f.FreshGraph() as graph:
                if mutation == 'source':
                    bad = copy.deepcopy(graph.sources); bad[0]['sha256'] = '0' * 64
                    graph.contract.source_bindings.return_value = bad
                    graph.contract.source_bindings.side_effect = None
                else:
                    with Path(graph.prepare_authorization['path']).open('ab') as stream:
                        stream.write(b' ')
                with self.assertRaises(REFUSED): graph.create()
                self.assertEqual(graph.api.env.plan_run.call_count, 0)
                self.assertEqual(graph.api.activation.execute.call_count, 0)
                self.assertFalse(rules.INPUT.exists())
                self.assertFalse(rules.RUNTIME.exists())

    def test_late_valid_ledger_rebinding_leaves_partial_inputs_spent_without_retry(self):
        with f.FreshGraph() as graph:
            def changed_after_admission_validation(admission):
                graph.events.append('build')
                # Value remains a valid prepared ledger; only its consumed raw
                # bytes/digest change after the first prepared snapshot.
                path = graph.registry / 'ledger-v1.json'
                with path.open('ab') as stream: stream.write(b' ')
            graph.api.profile_build.verify_current.side_effect = changed_after_admission_validation
            with self.assertRaises(REFUSED): graph.create()
            self.assertTrue(rules.RUN_PROPOSAL.exists())
            self.assertTrue(rules.RUN_AUTHORIZATION.exists())
            self.assertTrue(rules.ADMISSION.exists())
            self.assertFalse(rules.INPUT.exists())
            self.assertEqual(graph.api.env.plan_run.call_count, 1)
            self.assertEqual(graph.api.activation.execute.call_count, 0)
            with self.assertRaises(REFUSED): graph.create()
            self.assertEqual(graph.api.env.plan_run.call_count, 1)
            self.assertEqual(graph.api.env.prepare.call_count, 0)
            self.assertEqual(graph.api.activation.execute.call_count, 0)
