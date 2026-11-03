"""Original SDK18 parent vertical joins and dispatch-order oracles, metadata only."""
import copy
from pathlib import PureWindowsPath
import sys
from types import SimpleNamespace
import unittest
from unittest.mock import Mock, patch

from benchmarks import receipt_avd_storage as storage
from benchmarks import prepare_recovery_contract as history
from scripts import run_record_cancellation_operation as subject
from scripts import record_cancellation_operation_contract as rules
from scripts import record_cancellation_ui_fresh_contract as fresh
from scripts.tests import test_record_cancellation_fresh_contract as pure


class ClosedFreshGraph:
    """Explicit observation graph for actual parent _accept_fresh, not a ledger."""
    def __init__(self):
        p = pure.pin
        self.authority_pin = p(rules.FRESH_AUTHORITY)
        self.inner = pure.fresh_authority()
        self.inner['operator'] = copy.deepcopy(rules.FRESH_OPERATOR)
        self.inner['contract'] = copy.deepcopy(rules.FRESH_CONTRACT)
        self.final_pin = p(rules.FRESH_LIVE / 'operation-result-v1.json')
        self.value = dict(version=1, scope='sdk18-fresh-operation-final-v1', passed=True,
            authority=copy.deepcopy(self.authority_pin), attempt=p(fresh.ATTEMPT),
            owner=p(rules.FRESH_LIVE / 'outer-owner-result-v1.json'), stages=p(rules.FRESH_LIVE / 'stage-result-v1.json'),
            feature_acceptance=False)
        attempt = dict(version=1, scope='sdk18-fresh-operation-attempt-v1', authority=copy.deepcopy(self.authority_pin),
            handoff=copy.deepcopy(self.inner['handoff']), operator=copy.deepcopy(self.inner['operator']),
            contract=copy.deepcopy(self.inner['contract']), no_retry=True)
        self.owner = dict(status='child_exited', worker_returncode=0, cleanup_complete=True, output_capture_complete=True)
        self.stage = dict(scope='sdk18-fresh-operation-stages-v1', passed=True, phase='completed', feature_acceptance=False,
            authority=copy.deepcopy(self.authority_pin), attempt=p(fresh.ATTEMPT),
            activation_result=p(fresh.RUNTIME / 'control-v1/final-result-v1.json'),
            inputs=dict(input=p(fresh.INPUT), run_proposal=p(fresh.RUN_PROPOSAL)), ledger_after=p(rules.REGISTRY / 'ledger-v1.json'))
        self.activation = dict(passed=True, feature_acceptance=False, input=p(fresh.INPUT),
            runtime=p(fresh.RUNTIME / 'control-v1/runtime-result-v1.json'))
        self.runtime = dict(passed=True, controller_passed=True, owner_qualified=True, storage_closed=True,
            source_equal=True, cleanup_known=True, input=p(fresh.INPUT))
        self.entry = dict(root=str(rules.GUEST), state='closed', proposal_sha256=p(fresh.RUN_PROPOSAL)['sha256'],
            recovery=None, retirement=None, closure=p(rules.GUEST / 'guest-storage-closure-v1.json'))
        self.ledger = dict(version=2, entries=[self.entry])
        self.bound = {self.final_pin['path']: self.value, self.authority_pin['path']: self.inner,
            self.value['attempt']['path']: attempt, self.value['owner']['path']: self.owner,
            self.value['stages']['path']: self.stage, self.stage['activation_result']['path']: self.activation,
            self.activation['runtime']['path']: self.runtime, self.stage['ledger_after']['path']: self.ledger}
        self.checked = Mock()
        self.api = SimpleNamespace(env=SimpleNamespace(binding=p, check_binding=self.checked), fresh_rules=fresh,
            storage=SimpleNamespace(_validate=Mock(), _entry=storage._entry), history=history)

    def read(self, pin, expected=None, maximum=None):
        if expected is not None:
            assert PureWindowsPath(pin['path']) == PureWindowsPath(str(expected))
        return copy.deepcopy(self.bound[pin['path']])


class RecordCancellationOperationTests(unittest.TestCase):
    def test_source_refusal_precedes_attempt_and_parent_never_invokes_inner_preflight_directly(self):
        authority_pin = pure.pin(rules.AUTHORITY)
        authority = pure.parent_authority()
        forbidden_inner = Mock(side_effect=AssertionError('inner preflight outside worker'))
        api = SimpleNamespace(fresh=SimpleNamespace(_execute=forbidden_inner),
            env=SimpleNamespace(process_identity=Mock(return_value=dict(pid=1, executable=sys.executable)), check_binding=Mock()))
        with patch.object(subject, '_parts', return_value=(rules, api)), \
             patch.object(subject, '_initial', side_effect=rules.OperationRefused('source')), \
             patch.object(subject, '_attempt') as attempt, patch.object(subject, 'save') as save, \
             patch.object(subject, '_supervise') as supervise:
            with self.assertRaises(rules.OperationRefused): subject._execute(authority_pin, 100.0)
        self.assertEqual(attempt.call_count, 0)
        self.assertEqual(save.call_count, 0)
        self.assertEqual(supervise.call_count, 0)
        self.assertEqual(forbidden_inner.call_count, 0)
        events = []
        def save(path, value): events.append('save:' + path.name); return pure.pin(path)
        def attempt(*args): events.append('attempt'); return pure.pin(rules.ATTEMPT)
        def supervised(request, begin):
            events.append('supervise')
            self.assertEqual(begin, 100.0)
            return dict(status='expired', worker_returncode=1, cleanup_complete=True, output_capture_complete=True)
        with patch.object(subject, '_parts', return_value=(rules, api)), patch.object(subject, '_initial', return_value=authority), \
             patch.object(subject, '_budget'), patch.object(subject, '_attempt', side_effect=attempt), \
             patch.object(subject, 'save', side_effect=save), patch.object(subject, '_supervise', side_effect=supervised):
            result = subject._execute(authority_pin, 100.0)
        self.assertIs(result['passed'], False)
        self.assertIs(result['feature_acceptance'], False)
        self.assertLess(events.index('attempt'), events.index('save:worker-request-v1.json'))
        self.assertLess(events.index('save:worker-request-v1.json'), events.index('supervise'))
        self.assertEqual(forbidden_inner.call_count, 0)

    def test_child_stage_preserves_parent_begin_and_late_refusal_cannot_heal_into_pass(self):
        authority = pure.parent_authority(); authority_pin = pure.pin(rules.AUTHORITY); attempt_pin = pure.pin(rules.ATTEMPT)
        attempt = dict(version=1, scope='sdk18-record-cancellation-operation-attempt-v1', authority=authority_pin,
            operator=copy.deepcopy(authority['operator']), contract=copy.deepcopy(authority['contract']),
            fresh_authority=copy.deepcopy(authority['fresh_authority']), no_retry=True)
        for failure in ('none', 'inner_cancel', 'unknown_closure', 'late_authority'):
            inner = Mock(return_value={'synthetic_terminal': True})
            if failure == 'inner_cancel': inner.side_effect = KeyboardInterrupt('PRIVATE_CHILD_PAYLOAD')
            api = SimpleNamespace(fresh=SimpleNamespace(_execute=inner), env=SimpleNamespace(check_binding=Mock()))
            auth = Mock(side_effect=[authority, rules.OperationRefused('source')] if failure == 'late_authority' else None,
                return_value=authority)
            accept = Mock(return_value=pure.pin(rules.FRESH_LIVE / 'operation-result-v1.json'))
            if failure == 'unknown_closure': accept.side_effect = rules.OperationRefused('fresh_cleanup')
            with patch.object(subject, '_parts', return_value=(rules, api)), patch.object(subject, 'read_authority', auth), \
                 patch.object(subject, 'read', return_value=attempt), patch.object(subject, '_budget') as budget, \
                 patch.object(subject, '_accept_fresh', accept), patch.object(subject, 'save', side_effect=lambda path, value: pure.pin(path)) as save:
                returned = subject._invoke_fresh(authority_pin, attempt_pin, 83.25)
            inner.assert_called_once_with(authority['fresh_authority'], 83.25)
            budget.assert_called_once_with(83.25)
            self.assertIs(returned['passed'], failure == 'none')
            self.assertIs(returned['feature_acceptance'], False)
            self.assertEqual(auth.call_count, 2 if failure in ('none', 'late_authority') else 1)
            self.assertEqual(save.call_count, 1)
            self.assertEqual(save.call_args.args[0], rules.LIVE / 'stage-result-v1.json')
            self.assertNotIn('PRIVATE_CHILD_PAYLOAD', str(returned))

    def test_actual_nested_result_qualifier_requires_same_authority_owner_runtime_and_closed_root(self):
        for mutation in ('none', 'boolean_exit', 'unknown_runtime', 'borrowed_stage', 'wrong_root', 'missing_closure', 'wrong_input'):
            graph = ClosedFreshGraph()
            if mutation == 'boolean_exit': graph.owner['worker_returncode'] = False
            elif mutation == 'unknown_runtime': graph.runtime['cleanup_known'] = 1
            elif mutation == 'borrowed_stage': graph.stage['authority']['sha256'] = '0' * 64
            elif mutation == 'wrong_root': graph.entry['root'] = str(rules.GUEST.parent / 'another.avd')
            elif mutation == 'missing_closure': graph.entry['closure'] = None
            elif mutation == 'wrong_input': graph.activation['input']['sha256'] = '0' * 64
            with patch.object(subject, '_parts', return_value=(rules, graph.api)), patch.object(subject, 'read', side_effect=graph.read):
                if mutation == 'none':
                    self.assertEqual(subject._accept_fresh(graph.value, graph.authority_pin), graph.final_pin)
                    self.assertEqual(graph.checked.call_count, 5)
                else:
                    with self.subTest(mutation=mutation), self.assertRaises((rules.OperationRefused, storage.StorageRefused)):
                        subject._accept_fresh(graph.value, graph.authority_pin)
                    self.assertEqual(graph.checked.call_count, 0)
