"""Independent SDK15 operator authority and bounded orchestration adversaries.

Synthetic metadata is never an applicable human grant. Tests may create tiny
owned D records and replace explicit observation/SDK ports, never invoke live
recovery, shared storage, a native owner, Android, or a model.
Copyright 2026 LocalLore contributors. SPDX-License-Identifier: Apache-2.0
"""
import copy
from contextlib import ExitStack
import hashlib
import io
import json
import os
from pathlib import Path, PureWindowsPath
import subprocess
import sys
import tempfile
import time
from types import SimpleNamespace
import unittest
from unittest.mock import Mock, patch

from benchmarks import receipt_avd_environment as env
from benchmarks import receipt_avd_storage as storage
from scripts import library_ui_recovery_contract as contract
from scripts import library_ui_run_inputs as builder
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


def worker_records(graph):
    attempt = operator._attempt(graph.authority_pin, graph.authority)
    parent = dict(pid=5050, creation_filetime=105050, executable=sys.executable)
    worker = dict(pid=5051, creation_filetime=105051, executable=sys.executable)
    request = dict(version=1, scope='sdk15-recovery-operation-worker-request-v1', authority=graph.authority_pin,
        attempt=attempt, parent=parent, started_monotonic=100)
    request_pin = builder.save(contract.LIVE / 'worker-request-v1.json', request)
    builder.save(contract.LIVE / 'worker-started-v1.json', dict(request=request_pin, worker=worker))
    return request_pin, request, parent, worker


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

    def test_unknown_terminal_or_substituted_started_claim_and_stage_never_qualifies(self):
        from scripts.tests.library_ui_recovery_test_fixture import OperatorFixture
        for fault in ('expired', 'capture', 'cleanup', 'started', 'claim', 'stages'):
            with self.subTest(fault=fault), OperatorFixture() as graph:
                graph.fault = fault; value = operator.execute(graph.authority_pin)
                self.assertFalse(value['passed']); self.assertFalse(contract.INPUT.exists())
                self.assertEqual(graph.supervisor.call_count, 1)
                with self.assertRaises(contract.OperationRefused): operator.execute(graph.authority_pin)
                self.assertEqual(graph.supervisor.call_count, 1)

    def test_current_v2_or_changed_initial_ledger_never_creates_an_attempt(self):
        from scripts.tests.library_ui_recovery_test_fixture import OperatorFixture
        for damage in ('version', 'digest'):
            with self.subTest(damage=damage), OperatorFixture() as graph:
                path = graph.graph.fixture.registry / 'ledger-v1.json'
                if damage == 'digest': path.write_bytes(b' ' + path.read_bytes()[1:])
                else:
                    value = env.read_json(path); value['version'] = 2
                    for row in value['entries']: row['recovery'] = None
                    raw = env.encoded(value); path.write_bytes(raw + b' ' * (41230 - len(raw)))
                    # Keep the exact observed digest valid so the version predicate is tested.
                    contract.INITIAL_LEDGER_SHA256 = env.binding(path)['sha256']
                with self.assertRaises((contract.OperationRefused, env.EnvironmentRefused, ValueError)):
                    operator.execute(graph.authority_pin)
                self.assertFalse(contract.LIVE.exists()); graph.supervisor.assert_not_called()

    def test_worker_rejects_bad_or_oversized_barrier_before_imports_and_observations(self):
        for raw in (b'wrong\n', operator.BARRIER + b'x' * 131073):
            with patch.object(operator.sys, 'stdin', SimpleNamespace(buffer=io.BytesIO(raw))), \
                 patch.object(operator, '_parts', side_effect=AssertionError('Pre-barrier import')) as parts:
                self.assertEqual(operator._worker(), 1); parts.assert_not_called()

    def test_worker_actual_parent_child_started_receipt_and_claim_are_not_interchangeable(self):
        from scripts.tests.library_ui_recovery_test_fixture import OperatorFixture
        for fault in ('parent_pid', 'parent_creation', 'other_child', 'started_request', 'started_creation', 'old_claim'):
            with self.subTest(fault=fault), OperatorFixture() as graph:
                pin, request, parent, worker = worker_records(graph)
                current_pid = 5052 if fault == 'other_child' else worker['pid']
                actual_parent = 5059 if fault == 'parent_pid' else parent['pid']
                if fault in ('started_request', 'started_creation'):
                    path = contract.LIVE / 'worker-started-v1.json'; value = env.read_json(path)
                    if fault == 'started_request': value['request']['sha256'] = '0' * 64
                    else: value['worker']['creation_filetime'] += 1
                    path.write_bytes(env.encoded(value))
                claim = contract.LIVE / 'worker-claim-v1.json'
                if fault == 'old_claim': claim.write_bytes(b'{"preserved_old_claim":true}\n')
                def identity(pid):
                    value = dict(pid=pid, creation_filetime=100000 + pid, executable=sys.executable)
                    if fault == 'parent_creation' and pid == parent['pid']: value['creation_filetime'] += 1
                    return value
                with patch.object(operator.os, 'getpid', return_value=current_pid), \
                     patch.object(operator.os, 'getppid', return_value=actual_parent), \
                     patch.object(env, 'process_identity', side_effect=identity), \
                     patch.object(operator.sys, 'stdin', SimpleNamespace(buffer=io.BytesIO(operator.BARRIER + env.encoded(pin)))), \
                     patch.object(operator, '_run_stages', return_value={'passed': True}) as stages:
                    with self.assertRaises((contract.OperationRefused, FileExistsError)): operator._worker()
                    stages.assert_not_called()
                if fault == 'old_claim': self.assertEqual(claim.read_bytes(), b'{"preserved_old_claim":true}\n')
                else: self.assertFalse(claim.exists())

    def test_current_worker_claim_is_published_once_before_stages_and_cannot_be_retried(self):
        from scripts.tests.library_ui_recovery_test_fixture import OperatorFixture
        with OperatorFixture() as graph:
            pin, request, parent, worker = worker_records(graph)
            def stages(*args):
                claim = env.read_json(contract.LIVE / 'worker-claim-v1.json')
                self.assertEqual(claim['request'], pin); self.assertEqual(claim['worker'], worker)
                return {'passed': True}
            def identity(pid): return dict(pid=pid, creation_filetime=100000 + pid, executable=sys.executable)
            with patch.object(operator.os, 'getpid', return_value=worker['pid']), \
                 patch.object(operator.os, 'getppid', return_value=parent['pid']), \
                 patch.object(env, 'process_identity', side_effect=identity), \
                 patch.object(operator, '_run_stages', side_effect=stages) as run:
                with patch.object(operator.sys, 'stdin', SimpleNamespace(buffer=io.BytesIO(operator.BARRIER + env.encoded(pin)))):
                    self.assertEqual(operator._worker(), 0)
                before = (contract.LIVE / 'worker-claim-v1.json').read_bytes()
                with patch.object(operator.sys, 'stdin', SimpleNamespace(buffer=io.BytesIO(operator.BARRIER + env.encoded(pin)))):
                    with self.assertRaises(FileExistsError): operator._worker()
                self.assertEqual((contract.LIVE / 'worker-claim-v1.json').read_bytes(), before); self.assertEqual(run.call_count, 1)

    def test_cli_has_only_fixed_authority_digest_and_precheck_time_is_kept_in_the_same_budget(self):
        from scripts.tests.library_ui_recovery_test_fixture import OperatorFixture
        for argv in ([], ['--authority', 'D:/other.json'], ['--authority-sha256', 'F' * 64],
            ['--authority-sha256', '0' * 64, '--retry'], ['--seconds', '99999']):
            with patch.object(operator, '_parts', side_effect=AssertionError('Invalid CLI observed authority')) as parts:
                self.assertEqual(operator.main(argv), 1); parts.assert_not_called()
        with OperatorFixture() as graph:
            events = []
            def clock(): events.append('clock'); return 123
            def parts(): events.append('parts'); return contract, builder, graph.api
            with patch.object(operator.time, 'monotonic', side_effect=clock), patch.object(operator, '_parts', side_effect=parts), \
                 patch.object(operator, '_execute', return_value={'passed': False}) as execute, \
                 patch.object(operator.sys, 'stdout', io.StringIO()):
                self.assertEqual(operator.main(['--authority-sha256', graph.authority_pin['sha256']]), 1)
            self.assertEqual(events[:2], ['clock', 'parts'])
            self.assertEqual(execute.call_args.args, (graph.authority_pin, 123))

    def test_supervisor_assigns_job_and_started_receipt_before_one_binary_barrier(self):
        from scripts.tests.library_ui_recovery_test_fixture import SupervisorPorts
        with SupervisorPorts() as graph:
            result = graph.run()
            self.assertEqual(result['status'], 'child_exited'); self.assertEqual(result['worker_returncode'], 0)
            self.assertTrue(result['cleanup_complete']); self.assertTrue(result['output_capture_complete'])
            self.assertEqual(graph.raw_stdin, operator.BARRIER + env.encoded(graph.request))
            self.assertLess(graph.events.index('job'), graph.events.index('barrier'))
            self.assertLess(graph.events.index('started'), graph.events.index('barrier'))
            self.assertEqual(bytes(graph.capture.raw[0]), graph.stdout); self.assertEqual(bytes(graph.capture.raw[1]), graph.stderr)
            self.assertTrue(graph.job_closed); self.assertTrue(graph.capture_closed)

    def test_failed_job_or_worker_identity_never_releases_the_dispatch_barrier(self):
        from scripts.tests.library_ui_recovery_test_fixture import SupervisorPorts
        for fault in ('job', 'image', 'thread_start'):
            with self.subTest(fault=fault), SupervisorPorts(fault) as graph:
                result = graph.run(); self.assertEqual(result['status'], 'owner_failed')
                self.assertEqual(graph.raw_stdin, b'')
                if fault == 'job': self.assertTrue(graph.killed); self.assertFalse(graph.job_assigned)
                else: self.assertTrue(graph.job_closed)

    def test_timeout_unknown_capture_wait_or_reader_cleanup_remains_unqualified(self):
        from scripts.tests.library_ui_recovery_test_fixture import SupervisorPorts
        for fault in ('expired', 'capture', 'overflow', 'wait', 'job_close', 'capture_close', 'join', 'alive_query', 'stalled'):
            with self.subTest(fault=fault), SupervisorPorts(fault) as graph:
                result = graph.run()
                self.assertTrue(result['status'] != 'child_exited' or not result['cleanup_complete'] or not result['output_capture_complete'])
                self.assertTrue(graph.job_closed)
                if fault in ('join', 'alive_query', 'stalled'):
                    self.assertFalse(result['cleanup_complete']); self.assertFalse(result['output_capture_complete'])
                    self.assertFalse(graph.capture_closed); self.assertFalse(graph.child.stdout.closed)
                    self.assertIsNone(result['stdout_bytes']); self.assertIsNone(result['stderr_bytes'])

    def test_partial_final_publication_does_not_retry_or_turn_the_attempt_into_authority(self):
        from scripts.tests.library_ui_recovery_test_fixture import OperatorFixture
        with OperatorFixture() as graph:
            original = builder.save
            def save(path, value):
                if Path(path) == contract.LIVE / 'operation-result-v1.json': raise OSError('PRIVATE final publication')
                return original(path, value)
            with patch.object(builder, 'save', side_effect=save):
                with self.assertRaises(OSError): operator.execute(graph.authority_pin)
            self.assertTrue(contract.ATTEMPT.exists()); self.assertEqual(graph.supervisor.call_count, 1)
            with self.assertRaises(contract.OperationRefused): operator.execute(graph.authority_pin)
            self.assertEqual(graph.supervisor.call_count, 1)

    def test_recovery_failure_unknown_cleanup_or_input_failure_never_reaches_ui_activation(self):
        from scripts.tests.library_ui_recovery_test_fixture import OperatorFixture, REAL_RECOVERY_EXECUTE, REAL_RECORD_STATE
        for fault in ('recovery', 'cleanup', 'inputs'):
            with self.subTest(fault=fault), OperatorFixture() as graph:
                pin, request, _, worker = worker_records(graph)
                builder.save(contract.LIVE / 'worker-claim-v1.json', dict(version=1,
                    authority=graph.authority_pin, attempt=request['attempt'], request=pin, worker=worker))
                if fault == 'cleanup': graph.graph.fixture.close_known = False
                def isolated_recovery(*args):
                    if fault == 'recovery': raise OSError('PRIVATE synthetic recovery')
                    fixture = graph.graph.fixture
                    self.assertEqual(args, (contract.PLAN['path'], contract.RECOVERY_AUTHORIZATION, contract.EXECUTION))
                    self.assertEqual(Path(args[0]), graph.graph.plan_path)
                    self.assertEqual(Path(args[2]), fixture.base / 'run-1')
                    def transition(root, state, **kwargs):
                        self.assertEqual(Path(root), fixture.root); self.assertEqual(state, 'prepared')
                        self.assertEqual(Path(kwargs['registry']), fixture.registry)
                        return REAL_RECORD_STATE(root, state, **kwargs)
                    def facts(proposal):
                        self.assertEqual(proposal['paths']['root'], str(fixture.root))
                        return {'synthetic_readiness': True}
                    # Only this explicit tiny recovery port may prepare its own entry.
                    # Builder/outer phases retain the unconditional transition tripwire.
                    with patch.object(storage, 'record_state', side_effect=transition), \
                         patch.object(env, 'resource_facts', side_effect=facts):
                        return REAL_RECOVERY_EXECUTE(*args, registry=fixture.registry)
                execute = Mock(side_effect=isolated_recovery)
                with patch.object(graph.api.recovery, 'execute', execute), \
                     patch.object(builder, 'create_inputs', side_effect=contract.OperationRefused('synthetic_inputs')) as create, \
                     patch.object(graph.api.activation, 'execute', side_effect=AssertionError('UI after failed stage'), create=True) as activate:
                    value = operator._run_stages(graph.authority_pin, request['attempt'], 100)
                    self.assertFalse(value['passed']); self.assertNotIn('PRIVATE', json.dumps(value))
                    self.assertEqual(value['phase'], 'run_inputs' if fault == 'inputs' else 'recovery',
                        (value.get('failure_type'), value.get('reason')))
                    self.assertEqual(execute.call_count, 1); self.assertEqual(create.call_count, 1 if fault == 'inputs' else 0)
                    activate.assert_not_called(); self.assertFalse(contract.INPUT.exists())
                    stage = contract.LIVE / 'stage-result-v1.json'; original = stage.read_bytes()
                    with patch.object(operator.sys, 'stderr', io.StringIO()):
                        again = operator._run_stages(graph.authority_pin, request['attempt'], 100)
                    self.assertFalse(again['passed']); self.assertEqual(execute.call_count, 1)
                    self.assertEqual(stage.read_bytes(), original); activate.assert_not_called()

    def test_stale_worker_claim_or_insufficient_budget_stops_before_recovery_authorization(self):
        from scripts.tests.library_ui_recovery_test_fixture import OperatorFixture
        for fault in ('claim', 'budget'):
            with self.subTest(fault=fault), OperatorFixture() as graph:
                pin, request, _, worker = worker_records(graph)
                claim = dict(version=1, authority=graph.authority_pin, attempt=request['attempt'], request=pin, worker=worker)
                if fault == 'claim': claim['authority'] = dict(graph.authority_pin, sha256='0' * 64)
                builder.save(contract.LIVE / 'worker-claim-v1.json', claim)
                with patch.object(operator, '_budget', side_effect=contract.OperationRefused('operation_budget') if fault == 'budget' else None), \
                     patch.object(graph.api.recovery, 'execute', side_effect=AssertionError('Invalid stage reached recovery')) as execute, \
                     patch.object(graph.api.activation, 'execute', side_effect=AssertionError('Invalid stage reached UI'), create=True) as activate:
                    result = operator._run_stages(graph.authority_pin, request['attempt'], 100)
                    self.assertFalse(result['passed']); execute.assert_not_called(); activate.assert_not_called()
                    self.assertFalse(contract.RECOVERY_AUTHORIZATION.exists())

    def test_successful_ui_flags_cannot_infer_a_closed_ledger_or_override_unknown_runtime_cleanup(self):
        from scripts.tests.library_ui_recovery_test_fixture import BuilderFixture
        for fault in ('prepared_ledger', 'runtime', 'final'):
            with self.subTest(fault=fault), BuilderFixture() as graph:
                inputs = graph.create(); control = graph.root / 'synthetic-activation-control'; control.mkdir()
                graph.api.activation.CONTROL = control
                runtime = dict(passed=True, controller_passed=True, owner_qualified=True, storage_closed=True,
                    source_equal=True, cleanup_known=fault != 'runtime', input=inputs['input'])
                runtime_pin = graph.store(control / 'runtime-result-v1.json', runtime)
                value = dict(passed=True, feature_acceptance=False, input=inputs['input'], runtime=runtime_pin)
                graph.store(control / 'final-result-v1.json', {} if fault == 'final' else value)
                with patch.object(operator, '_parts', return_value=(contract, builder, graph.api)):
                    with self.assertRaises(contract.OperationRefused): operator._accept_activation(value, inputs)
                graph.fixture.assert_charge('prepared')
                self.assertEqual(graph.fixture.ledger_bytes(), graph.before_ledger)
                self.assertIsNone(graph.fixture.entry()['closure'])


@unittest.skipUnless(os.name == 'nt', 'One bounded benign owned child; no SDK, authority or device')
class LibraryUiRecoveryNativeSupervisorTests(unittest.TestCase):
    def test_real_owned_windows_job_captures_binary_output_and_starts_only_after_its_join_record(self):
        from scripts.tests.library_ui_recovery_test_fixture import BASE, budget
        budget(1024 * 1024); BASE.mkdir(parents=True, exist_ok=True)
        root = Path(tempfile.mkdtemp(prefix='native-job-', dir=BASE)); live = root / 'live'; live.mkdir()
        child = root / 'benign-owned-worker.py'
        child.write_bytes((
            "import json,os,pathlib,sys\n"
            "barrier=sys.stdin.buffer.readline()\n"
            "assert barrier==b'sdk15-recovery-operation-worker-v1\\n'\n"
            "pin=json.loads(sys.stdin.buffer.read())\n"
            "record=json.loads((pathlib.Path(__file__).parent/'live/worker-started-v1.json').read_bytes())\n"
            "assert record['request']==pin and record['worker']['pid']==os.getpid()\n"
            "sys.stdout.buffer.write(bytes([0,26,13,10,255,65]));sys.stdout.buffer.flush()\n"
            "sys.stderr.buffer.write(bytes([255,26,0,13,10,66]));sys.stderr.buffer.flush()\n").encode())
        request_path = root / 'benign-request.json'; env.create_json(request_path, {'synthetic_host_only': True})
        request = env.binding(request_path)
        fake_rules = SimpleNamespace(LIVE=live, OPERATOR=child, MAX_SECONDS=2400, need=contract.need)
        def save(path, value): env.create_json(path, value); return env.binding(path)
        ports = (fake_rules, SimpleNamespace(save=save), SimpleNamespace(env=env))
        with patch.object(operator, '_parts', return_value=ports):
            result = operator._supervise(request, time.monotonic())
        self.assertEqual((result['status'], result['worker_returncode']), ('child_exited', 0))
        self.assertTrue(result['cleanup_complete']); self.assertTrue(result['output_capture_complete'])
        self.assertEqual((live / 'outer-owner-v1/owner-stdout-v1.bin').read_bytes(), bytes([0, 26, 13, 10, 255, 65]))
        self.assertEqual((live / 'outer-owner-v1/owner-stderr-v1.bin').read_bytes(), bytes([255, 26, 0, 13, 10, 66]))
        started = env.read_json(live / 'worker-started-v1.json')
        self.assertEqual(started, dict(request=request, worker=result['worker']))
        self.assertFalse((live / 'worker-claim-v1.json').exists()); budget()


if __name__ == '__main__': unittest.main()
