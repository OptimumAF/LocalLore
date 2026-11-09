"""Original whole-stage failure stickiness; all operation observations are fake."""
import copy
import io
import json
from types import SimpleNamespace
import unittest
from unittest.mock import Mock, patch

from scripts import run_record_cancellation_ui_fresh as subject
from scripts import record_cancellation_ui_fresh_contract as rules
from scripts.tests import test_record_cancellation_fresh_contract as pure


class RecordCancellationFreshStageTests(unittest.TestCase):
    def test_prepare_activation_late_source_and_success_edge_faults_never_repair_pass(self):
        for mode in ('positive', 'budget_bool', 'prepare_cancel', 'activation_cleanup', 'late_source', 'success_edge', 'publication'):
            authority = pure.fresh_authority(); authority_pin = pure.pin(rules.AUTHORITY); attempt_pin = pure.pin(rules.ATTEMPT)
            attempt = dict(version=1, scope='sdk18-fresh-operation-attempt-v1', authority=authority_pin,
                handoff=copy.deepcopy(authority['handoff']), operator=copy.deepcopy(authority['operator']),
                contract=copy.deepcopy(authority['contract']), no_retry=True)
            handoff = dict(prepare_proposal=copy.deepcopy(rules.PREPARE_PIN))
            inputs = dict(input=pure.pin(rules.INPUT), run_proposal=pure.pin(rules.RUN_PROPOSAL))
            saved, events = [], []
            class Result(dict):
                def update(self, *args, **kwargs):
                    super().update(*args, **kwargs)
                    if kwargs.get('passed') is True:
                        events.append('success_written')
                        if mode == 'success_edge': raise KeyboardInterrupt('PRIVATE_STAGE_PAYLOAD')
            def save(path, value):
                saved.append((str(path), copy.deepcopy(dict(value))))
                if mode == 'publication' and path.name == 'stage-result-v1.json':
                    raise OSError('PRIVATE_STAGE_PAYLOAD')
                return pure.pin(path)
            def read(pin, expected=None, maximum=None):
                if pin == attempt_pin: return copy.deepcopy(attempt)
                return dict(authority=authority_pin, attempt=attempt_pin)
            prepare = Mock(side_effect=KeyboardInterrupt('PRIVATE_STAGE_PAYLOAD') if mode == 'prepare_cancel' else None)
            activate = Mock(return_value={'synthetic_only': True})
            api = SimpleNamespace(env=SimpleNamespace(check_binding=Mock(), prepare=prepare, binding=pure.pin),
                activation=SimpleNamespace(execute=activate))
            frozen = Mock(return_value=(authority, handoff, {}))
            if mode == 'late_source': frozen.side_effect = [(authority, handoff, {}), rules.FreshRunRefused('source')]
            accept = Mock(return_value=(pure.pin(rules.RUNTIME / 'control-v1/final-result-v1.json'), pure.pin(rules.REGISTRY / 'ledger-v1.json')))
            if mode == 'activation_cleanup': accept.side_effect = rules.FreshRunRefused('activation_cleanup')
            with patch.object(subject, '_parts', return_value=(rules, api)), \
                 patch.object(subject, 'dict', Result, create=True), \
                 patch.object(subject, 'frozen_inputs', frozen), patch.object(subject, 'read', side_effect=read), \
                 patch.object(subject, 'prepared') as prepared, patch.object(subject, 'create_inputs', return_value=inputs) as create, \
                 patch.object(subject, '_accept_activation', accept), patch.object(subject, 'save', side_effect=save), \
                 patch.object(subject.os.path, 'lexists', return_value=False), \
                 patch.object(subject.time, 'monotonic', return_value=100.0), \
                 patch.object(subject.sys, 'stderr', io.StringIO()) as stderr:
                returned = subject._run_stages(authority_pin, attempt_pin, True if mode == 'budget_bool' else 100.0)
            self.assertIs(returned['passed'], mode == 'positive')
            self.assertIs(returned['feature_acceptance'], False)
            self.assertEqual(saved[-1][0], str(rules.LIVE / 'stage-result-v1.json'))
            self.assertEqual(prepare.call_count, 0 if mode == 'budget_bool' else 1)
            self.assertEqual(prepared.call_count, 0 if mode in ('budget_bool', 'prepare_cancel') else 1)
            self.assertEqual(create.call_count, 0 if mode in ('budget_bool', 'prepare_cancel') else 1)
            self.assertEqual(activate.call_count, 0 if mode in ('budget_bool', 'prepare_cancel') else 1)
            self.assertEqual(events, ['success_written'] if mode in ('positive', 'success_edge', 'publication') else [])
            self.assertNotIn('PRIVATE_STAGE_PAYLOAD', json.dumps(returned))
            self.assertNotIn('PRIVATE_STAGE_PAYLOAD', json.dumps(saved))
            self.assertNotIn('PRIVATE_STAGE_PAYLOAD', stderr.getvalue())
            if mode == 'publication':
                self.assertIs(returned['publication_failed'], True)
                self.assertEqual(json.loads(stderr.getvalue()), dict(scope='sdk18-fresh-operation-stages-v1', publication_failed=True))
