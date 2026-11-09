"""Original host metadata oracles; all operational ports are synthetic and no files are opened."""
import copy
import io
import json
import unittest
from contextlib import ExitStack, redirect_stderr, redirect_stdout
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

from scripts import run_record_cancellation_ui_fresh as operator


PRIVATE = 'B120_PRIVATE_EXCEPTION_TEXT_NOT_A_REASON'
FORMATTED = []


class Refusal(Exception):
    def __str__(self):
        FORMATTED.append('exception_str')
        return PRIVATE

    def __repr__(self):
        FORMATTED.append('exception_repr')
        return PRIVATE


class FreshRunRefused(Refusal):
    pass


class EnvironmentRefused(Refusal):
    pass


class StorageRefused(Refusal):
    pass


class ObjectPayload:
    def __str__(self):
        FORMATTED.append('object_str')
        return PRIVATE

    def __repr__(self):
        FORMATTED.append('object_repr')
        return PRIVATE


class StringPayload(str):
    def __hash__(self):
        FORMATTED.append('string_hash')
        return super().__hash__()

    def __eq__(self, other):
        FORMATTED.append('string_equal')
        return super().__eq__(other)

    def __str__(self):
        FORMATTED.append('string_str')
        return PRIVATE

    def __repr__(self):
        FORMATTED.append('string_repr')
        return PRIVATE


def pin(name):
    # These are fake metadata bindings, never claimed as existing files or authority.
    return dict(path='D:/b120-synthetic-metadata/' + name, bytes=10, sha256='1' * 64)


class Flow:
    """A small operation-port script around the unchanged public stage function."""
    def __init__(self, fail_at=None, error=None, publication_error=None):
        self.fail_at, self.error = fail_at, error
        self.publication_error = publication_error
        self.calls, self.written, self.write_attempts = [], [], []
        self.frozen_count = self.budget_count = 0
        self.authority, self.attempt = pin('authority'), pin('attempt')
        self.prepare_proposal, self.ledger = pin('prepare-proposal'), pin('ledger')
        self.authorization = pin('prepare-authorization')
        self.inputs = dict(input=pin('activation-input'))
        self.activation_result, self.ledger_after = pin('activation-result'), pin('ledger-after')
        self.live = Path('D:/b120-synthetic-metadata/live')
        self.rules = SimpleNamespace(
            LIVE=self.live, ATTEMPT=Path(self.attempt['path']),
            GUEST=Path('D:/b120-synthetic-metadata/absent-guest'),
            PREPARE_AUTHORIZATION=self.live/'prepare-authorization-v1.json',
            FreshRunRefused=FreshRunRefused, same=lambda a, b: a == b,
            need=self.need, validate_attempt=self.validate_attempt,
        )
        self.api = SimpleNamespace(
            env=SimpleNamespace(EnvironmentRefused=EnvironmentRefused, binding=self.binding,
                                check_binding=self.check_binding, prepare=self.prepare),
            storage=SimpleNamespace(StorageRefused=StorageRefused),
            activation=SimpleNamespace(execute=self.activate),
        )
        self.stdout, self.stderr = io.StringIO(), io.StringIO()

    def event(self, name):
        self.calls.append(name)
        if self.fail_at == name:
            raise self.error

    def need(self, condition, reason):
        if not condition:
            raise FreshRunRefused(reason)

    def frozen(self, authority):
        assert authority == self.authority
        self.frozen_count += 1
        self.event('validate_inputs' if self.frozen_count == 1 else 'final_validation')
        return dict(ledger=self.ledger), dict(prepare_proposal=self.prepare_proposal), None

    def validate_attempt(self, value, authority, data):
        self.calls.append('validate_attempt')
        assert value == {'fixture_attempt': True} and authority == self.authority

    def binding(self, path):
        assert path == self.live/'worker-claim-v1.json'
        return pin('claim')

    def read(self, value, expected=None):
        if value == self.attempt:
            assert expected == self.rules.ATTEMPT
            return {'fixture_attempt': True}
        assert value == pin('claim')
        return dict(authority=self.authority, attempt=self.attempt)

    def budget(self, begin, remaining):
        assert begin == 0
        self.budget_count += 1
        assert remaining == (2100, 2000, 1900)[self.budget_count - 1]
        self.event(('initial_budget', 'prepare_budget', 'activation_budget')[self.budget_count - 1])

    def check_binding(self, value):
        assert value in (self.ledger, self.attempt)
        self.calls.append('check_ledger' if value == self.ledger else 'check_attempt')

    def save(self, path, value):
        self.write_attempts.append(path.name)
        if path == self.rules.PREPARE_AUTHORIZATION:
            self.event('prepare_authorization')
            assert value == dict(version=1, phase='prepare', proposal_sha256=self.prepare_proposal['sha256'],
                                 allow_environment_calls=True, root_go_pending=False)
            self.written.append((path.name, copy.deepcopy(value)))
            return self.authorization
        assert path == self.live/'stage-result-v1.json'
        if self.publication_error is not None:
            raise self.publication_error
        self.written.append((path.name, copy.deepcopy(value)))
        return pin('stage-result')

    def prepare(self, proposal_path, authorization_path):
        assert proposal_path == self.prepare_proposal['path'] and authorization_path == self.rules.PREPARE_AUTHORIZATION
        self.event('prepare_dispatch')

    def prepared(self, authority, authorization):
        assert authority == self.authority and authorization == self.authorization
        self.event('prepared_validation')

    def create_inputs(self, authority, authorization):
        assert authority == self.authority and authorization == self.authorization
        self.event('run_inputs')
        return self.inputs

    def activate(self, value):
        assert value == self.inputs['input']
        self.event('activation_dispatch')
        return {'fixture_activation': True}

    def accept(self, result, inputs):
        assert result == {'fixture_activation': True} and inputs == self.inputs
        self.event('activation_validation')
        return self.activation_result, self.ledger_after

    def run(self):
        with ExitStack() as stack:
            for name, value in dict(_parts=lambda: (self.rules, self.api), frozen_inputs=self.frozen,
                                    read=self.read, save=self.save, _budget=self.budget, prepared=self.prepared,
                                    create_inputs=self.create_inputs, _accept_activation=self.accept).items():
                stack.enter_context(patch.object(operator, name, value))
            stack.enter_context(patch.object(operator.os.path, 'lexists', return_value=False))
            stack.enter_context(patch.object(operator.time, 'monotonic', return_value=10.0))
            stack.enter_context(redirect_stdout(self.stdout))
            stack.enter_context(redirect_stderr(self.stderr))
            return operator._run_stages(self.authority, self.attempt, 0)


class RecordPreparationRefusalTest(unittest.TestCase):
    def setUp(self):
        FORMATTED.clear()

    def safe(self, flow, result):
        # Outside the operator's exception handler: swallowed formatting attempts still fail.
        self.assertEqual([], FORMATTED)
        self.assertNotIn(PRIVATE, json.dumps(result) + flow.stdout.getvalue() + flow.stderr.getvalue())

    def test_positive_flow_prepares_once_activates_once_and_has_no_failure_metadata(self):
        flow = Flow()
        result = flow.run()
        self.assertIs(result['passed'], True)
        self.assertEqual('completed', result['phase'])
        self.assertIs(result['feature_acceptance'], False)
        self.assertNotIn('reason', result)
        self.assertNotIn('failure_type', result)
        self.assertEqual(1, flow.calls.count('prepare_dispatch'))
        self.assertEqual(1, flow.calls.count('activation_dispatch'))
        self.assertEqual(result, flow.written[-1][1])
        self.safe(flow, result)

    def test_exact_trusted_refusals_keep_only_the_closed_reason_vocabulary(self):
        families = [
            (FreshRunRefused, ('operation_budget', 'prepare_terminal', 'prepared_state', 'already_used',
                'worker_claim', 'source_snapshot', 'source_closure', 'binding', 'ledger_changed',
                'activation', 'activation_cleanup', 'storage_closure')),
            (EnvironmentRefused, ('host_capacity', 'host_commit_capacity', 'host_commit_unavailable',
                'ports_unavailable', 'storage_registry_locked', 'storage_storage_capacity_exceeded')),
            (StorageRefused, ('registry_locked', 'storage_capacity_exceeded')),
        ]
        for family, reasons in families:
            for reason in reasons:
                with self.subTest(family=family.__name__, reason=reason):
                    flow = Flow('prepare_dispatch', family(reason)); result = flow.run()
                    self.safe(flow, result)
                    self.assertIs(result['passed'], False)
                    self.assertEqual(family.__name__, result.get('failure_type'))
                    self.assertEqual(reason, result.get('reason'))
                    self.assertEqual('prepare_dispatch', result.get('step'))
                    self.assertNotIn('prepared_validation', flow.calls)
                    self.assertNotIn('run_inputs', flow.calls)
                    self.assertNotIn('activation_dispatch', flow.calls)

    def test_same_failure_is_attributed_to_each_exact_operation_step(self):
        sites = [('validate_inputs', 'initial'), ('prepare_authorization', 'initial'),
                 ('prepare_dispatch', 'prepare'), ('prepared_validation', 'prepare'),
                 ('prepare_budget', 'prepare'), ('run_inputs', 'run_inputs'),
                 ('activation_budget', 'run_inputs'), ('activation_dispatch', 'activation'),
                 ('activation_validation', 'activation'), ('final_validation', 'activation')]
        for index, (site, phase) in enumerate(sites):
            with self.subTest(step=site):
                flow = Flow(site, FreshRunRefused('binding')); result = flow.run()
                self.safe(flow, result)
                self.assertIs(result['passed'], False)
                self.assertEqual(site, result.get('step'))
                self.assertEqual(phase, result['phase'])
                self.assertEqual('binding', result.get('reason'))
                self.assertEqual(1, flow.calls.count(site))
                for later, _ in sites[index + 1:]:
                    self.assertNotIn(later, flow.calls)

    def test_spoofed_names_and_subclasses_do_not_inherit_trusted_error_identity(self):
        kinds = [type('EnvironmentRefused', (Exception,), {}),
                 type('FreshRunRefused', (FreshRunRefused,), {}),
                 type('StorageRefused', (StorageRefused,), {}),
                 type('OSError', (Exception,), {}),
                 type('KeyboardInterrupt', (BaseException,), {})]
        for index, kind in enumerate(kinds):
            with self.subTest(variant=index):
                flow = Flow('prepare_dispatch', kind('host_commit_capacity')); result = flow.run()
                self.safe(flow, result)
                self.assertIs(result['passed'], False)
                self.assertEqual('operation_failed', result.get('failure_type'))
                self.assertEqual('operation_failed', result.get('reason'))

    def test_hostile_arguments_and_exception_chains_are_never_rendered(self):
        cases = [(EnvironmentRefused(), 'operation_failed'),
                 (EnvironmentRefused('host_commit_capacity', PRIVATE), 'operation_failed'),
                 (EnvironmentRefused(ObjectPayload()), 'operation_failed'),
                 (EnvironmentRefused(StringPayload('host_commit_capacity')), 'operation_failed'),
                 (EnvironmentRefused(PRIVATE), 'operation_failed'),
                 (EnvironmentRefused('host_commit_capacity'), 'host_commit_capacity')]
        for index, (error, expected) in enumerate(cases):
            error.__cause__ = Refusal(PRIVATE)
            error.__context__ = Refusal(PRIVATE)
            with self.subTest(variant=index):
                flow = Flow('prepare_dispatch', error); result = flow.run()
                self.safe(flow, result)
                self.assertEqual('EnvironmentRefused', result.get('failure_type'))
                self.assertEqual(expected, result.get('reason'))

    def test_builtin_identity_and_interrupts_have_finite_non_payload_reasons(self):
        kinds = [OSError, FileNotFoundError, FileExistsError, PermissionError, ValueError, KeyError, TypeError,
                 KeyboardInterrupt, SystemExit]
        for kind in kinds:
            with self.subTest(variant=kind.__name__):
                flow = Flow('prepare_dispatch', kind(PRIVATE)); result = flow.run()
                self.safe(flow, result)
                self.assertIs(result['passed'], False)
                self.assertEqual('operation_failed' if kind is SystemExit else kind.__name__, result.get('failure_type'))
                self.assertEqual('cancelled' if kind is KeyboardInterrupt else 'operation_failed', result.get('reason'))
                self.assertNotIn('activation_dispatch', flow.calls)

    def test_completed_step_and_late_validation_failure_cannot_be_confused(self):
        positive = Flow(); completed = positive.run()
        self.assertIs(completed['passed'], True)
        self.assertEqual('completed', completed.get('step'))
        flow = Flow('final_validation', FreshRunRefused('ledger_changed')); result = flow.run()
        self.safe(flow, result)
        self.assertIs(result['passed'], False)
        self.assertEqual('final_validation', result.get('step'))
        self.assertEqual('ledger_changed', result.get('reason'))
        self.assertEqual(1, flow.calls.count('prepare_dispatch'))
        self.assertEqual(1, flow.calls.count('activation_dispatch'))
        self.assertEqual(1, flow.calls.count('activation_validation'))
        self.assertEqual(2, flow.frozen_count)
        self.assertIsNone(result['activation_result'])
        self.assertIsNone(result['ledger_after'])

    def test_publication_failure_after_positive_flow_stays_failed_with_safe_fixed_stderr(self):
        for kind in [RuntimeError, KeyboardInterrupt, SystemExit]:
            with self.subTest(variant=kind.__name__):
                flow = Flow(publication_error=kind(PRIVATE)); result = flow.run()
                self.safe(flow, result)
                self.assertIs(result['passed'], False)
                self.assertIs(result['publication_failed'], True)
                self.assertEqual(1, flow.calls.count('prepare_dispatch'))
                self.assertEqual(1, flow.calls.count('activation_dispatch'))
                self.assertEqual(1, flow.write_attempts.count('stage-result-v1.json'))
                self.assertEqual(['prepare-authorization-v1.json'], [p for p, _ in flow.written])
                self.assertEqual({'scope': 'sdk18-fresh-operation-stages-v1', 'publication_failed': True},
                                 json.loads(flow.stderr.getvalue()))
