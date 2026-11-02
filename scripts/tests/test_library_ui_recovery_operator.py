"""Independent SDK15 operator authority and bounded orchestration adversaries.

Synthetic metadata is never an applicable human grant. Tests may create tiny
owned D records and replace explicit observation/SDK ports, never invoke live
recovery, shared storage, a native owner, Android, or a model.
Copyright 2026 LocalLore contributors. SPDX-License-Identifier: Apache-2.0
"""
import copy
from contextlib import ExitStack
import hashlib
import os
from pathlib import Path, PureWindowsPath
import subprocess
import unittest
from unittest.mock import patch

from scripts import library_ui_recovery_contract as contract
from scripts import run_library_ui_recovery as operator


def synthetic_pin(path):
    value = str(PureWindowsPath(path))
    return dict(path=value, bytes=31, sha256=hashlib.sha256(('synthetic metadata: ' + value).encode()).hexdigest())


def synthetic_authority():
    value = dict(version=1, scope='sdk15-recovery-and-one-library-ui-run-v1',
        source_head='18809566af72530408e2e25007ee4d501e6bf12a', operator_head='7' * 40,
        proposal=synthetic_pin(contract.PROPOSAL), operator=synthetic_pin(contract.OPERATOR),
        builder=synthetic_pin(contract.BUILDER), contract=synthetic_pin(contract.CONTRACT),
        handoff=copy.deepcopy(contract.HANDOFF), recovery_plan=copy.deepcopy(contract.PLAN),
        allow_ledger_v2=True, allow_sdk_prepare=True, allow_one_boot=True, accept_operator_observation=True,
        allow_model=False, approval_reference='SYNTHETIC metadata only; no real approval or execution',
        max_operation_seconds=2400)
    return value


def synthetic_attempt(authority_pin, authority):
    return dict(version=1, scope='sdk15-recovery-operation-attempt-v1', authority=copy.deepcopy(authority_pin),
        **{role: copy.deepcopy(authority[role]) for role in ('handoff', 'recovery_plan', 'operator', 'builder', 'contract')},
        no_retry=True)


class LibraryUiRecoveryAuthorityTests(unittest.TestCase):
    def test_definitions_and_pure_validators_do_not_read_publish_or_observe_anything(self):
        path = Path(contract.__file__); raw = path.read_bytes()
        value = synthetic_authority(); pin = synthetic_pin(contract.AUTHORITY); attempt = synthetic_attempt(pin, value)
        with ExitStack() as stack:
            for target, name in ((Path, 'open'), (Path, 'stat'), (Path, 'mkdir'),
                (subprocess, 'run'), (subprocess, 'Popen')):
                stack.enter_context(patch.object(target, name, side_effect=AssertionError('Pure metadata performed IO')))
            namespace = {'__name__': 'pure_sdk15_contract_probe', '__file__': str(path)}
            exec(compile(raw, str(path), 'exec'), namespace)
            self.assertEqual(contract.validate_authority(value), value)
            self.assertEqual(contract.validate_attempt(attempt, pin, value), attempt)

    def test_fixed_paths_keep_the_old_charged_guest_and_new_operation_destinations_separate(self):
        root = Path('D:/Dev/Experiments/LocalLore/2026-11-02-library-recovery-operator-v1')
        self.assertEqual(contract.OUT, root)
        self.assertEqual((contract.LIVE, contract.EXECUTION, contract.AUTHORITY),
            (root / 'live-operation-v1', root / 'recovery-execution-v1', root / 'human-authority-v1.json'))
        self.assertEqual(contract.GUEST, Path('D:/Dev/Experiments/LocalLore/2026-11-01-record-controls-ui-v1/avd-v1'))
        self.assertEqual(contract.SOURCE, Path('D:/Worktrees/locallore-record-actions-tests-v1'))
        self.assertEqual(contract.SOURCE_HEAD, '18809566af72530408e2e25007ee4d501e6bf12a')
        self.assertEqual(contract.MAX_SECONDS, 2400)
        self.assertEqual(contract.RUN_AUTHORIZATION, contract.LIVE / 'run-authorization-v1.json')
        self.assertEqual(contract.RECOVERY_RESULT, contract.EXECUTION / 'recovery-result-v1.json')
        self.assertNotEqual(contract.CONTROLS, contract.RUNTIME)

    def test_closed_authority_validation_returns_detached_metadata_without_minting_a_grant(self):
        value = synthetic_authority(); frozen = copy.deepcopy(value)
        actual = contract.validate_authority(value)
        self.assertEqual(actual, frozen); self.assertIsNot(actual, value)
        actual['operator']['sha256'] = '0' * 64
        self.assertEqual(value, frozen)

    def test_every_required_flag_is_literal_true_and_model_flag_is_literal_false(self):
        for field in ('allow_ledger_v2', 'allow_sdk_prepare', 'allow_one_boot', 'accept_operator_observation'):
            for bad in (False, 0, 1, None, 'true'):
                value = synthetic_authority(); value[field] = bad
                with self.subTest(field=field, bad=bad), self.assertRaises(contract.OperationRefused):
                    contract.validate_authority(value)
        for bad in (True, 0, 1, None, 'false'):
            value = synthetic_authority(); value['allow_model'] = bad
            with self.subTest(model=bad), self.assertRaises(contract.OperationRefused): contract.validate_authority(value)

    def test_versions_heads_budget_and_schema_cannot_borrow_boolean_or_extra_fields(self):
        for field, bad in (('version', True), ('version', 2), ('scope', 'sdk14-recovery-and-one-ui-run-v1'),
            ('source_head', '0' * 40), ('operator_head', '7' * 39), ('operator_head', 'F' * 40),
            ('max_operation_seconds', True), ('max_operation_seconds', 2399), ('max_operation_seconds', 2401),
            ('runtime_override', 'D:\\Synthetic\\not-authorized')):
            value = synthetic_authority(); value[field] = bad
            with self.subTest(field=field, bad=bad), self.assertRaises(contract.OperationRefused): contract.validate_authority(value)
        value = synthetic_authority(); del value['approval_reference']
        with self.assertRaises(contract.OperationRefused): contract.validate_authority(value)

    def test_empty_control_character_or_oversized_approval_reference_refuses(self):
        for bad in ('', 'x' * 257, 'line\nbreak', 'carriage\rreturn', 'nul\0', 'tab\t'):
            value = synthetic_authority(); value['approval_reference'] = bad
            with self.subTest(reference=repr(bad)), self.assertRaises(contract.OperationRefused): contract.validate_authority(value)
        value = synthetic_authority(); value['approval_reference'] = 'x' * 256
        self.assertEqual(contract.validate_authority(value), value)

    def test_all_six_bound_authority_roles_require_fixed_canonical_physical_d_paths(self):
        for role in ('proposal', 'operator', 'builder', 'contract', 'handoff', 'recovery_plan'):
            for mode in ('slash', 'c_drive', 'foreign', 'relative'):
                value = synthetic_authority(); pin = value[role]
                if mode == 'slash': pin['path'] = pin['path'].replace('\\', '/')
                elif mode == 'c_drive': pin['path'] = 'C:' + pin['path'][2:]
                elif mode == 'foreign': pin['path'] = str(PureWindowsPath(pin['path']).with_name('foreign.json'))
                else: pin['path'] = 'relative.json'
                with self.subTest(role=role, mode=mode), self.assertRaises(contract.OperationRefused): contract.validate_authority(value)

    def test_binding_size_digest_and_key_types_remain_closed(self):
        original = synthetic_pin(contract.OPERATOR)
        for change in ({'bytes': True}, {'bytes': 0}, {'bytes': 2 * 1024**2 + 1}, {'sha256': 'A' * 64},
            {'sha256': '0' * 63}, {'extra': True}, {'path': 17}):
            with self.subTest(change=change), self.assertRaises(contract.OperationRefused):
                contract.binding(dict(original, **change), contract.OPERATOR)

    def test_original_handoff_and_plan_pins_cannot_be_resealed_or_substituted(self):
        for role in ('handoff', 'recovery_plan'):
            for field, bad in (('sha256', 'f' * 64), ('bytes', 17)):
                value = synthetic_authority(); value[role][field] = bad
                with self.subTest(role=role, field=field), self.assertRaises(contract.OperationRefused): contract.validate_authority(value)
        self.assertFalse(contract.same(True, 1))

    def test_attempt_binds_exact_authority_and_all_operation_inputs_with_no_retry(self):
        authority = synthetic_authority(); pin = synthetic_pin(contract.AUTHORITY)
        attempt = synthetic_attempt(pin, authority)
        self.assertEqual(contract.validate_attempt(attempt, pin, authority), attempt)
        for role in ('authority', 'handoff', 'recovery_plan', 'operator', 'builder', 'contract'):
            value = copy.deepcopy(attempt); value[role]['sha256'] = 'f' * 64
            with self.subTest(role=role), self.assertRaises(contract.OperationRefused): contract.validate_attempt(value, pin, authority)
        for change in ({'no_retry': False}, {'no_retry': 1}, {'version': True}, {'scope': 'unselected'}, {'retry': True}):
            with self.subTest(change=change), self.assertRaises(contract.OperationRefused):
                contract.validate_attempt(dict(attempt, **change), pin, authority)


@unittest.skipUnless(os.name == 'nt', 'Tiny D operator records and mocked worker outcome')
class LibraryUiRecoveryOperatorTests(unittest.TestCase):
    def test_boolean_worker_exit_cannot_qualify_even_with_coherent_started_claim_and_passed_stage(self):
        from scripts.tests.library_ui_recovery_test_fixture import OperatorFixture
        with OperatorFixture() as graph:
            graph.fault = 'boolean_code'
            value = operator.execute(graph.authority_pin)
            self.assertFalse(value['passed'], 'False must not be accepted as an integer zero worker exit code')
            self.assertEqual(graph.graph.fixture.ledger_bytes(), graph.before_ledger)
            self.assertFalse(contract.INPUT.exists())

    def test_known_simulated_worker_joins_do_not_execute_the_fake_passed_stage_twice(self):
        from scripts.tests.library_ui_recovery_test_fixture import OperatorFixture
        with OperatorFixture() as graph:
            value = operator.execute(graph.authority_pin)
            self.assertTrue(value['passed']); self.assertFalse(value['feature_acceptance'])
            self.assertEqual(graph.supervisor.call_count, 1)
            before = {p: p.read_bytes() for p in contract.LIVE.rglob('*') if p.is_file()}
            with self.assertRaises(contract.OperationRefused): operator.execute(graph.authority_pin)
            self.assertEqual({p: p.read_bytes() for p in before}, before)
            self.assertEqual(graph.supervisor.call_count, 1)
            self.assertEqual(graph.graph.fixture.ledger_bytes(), graph.before_ledger)


if __name__ == '__main__': unittest.main()
