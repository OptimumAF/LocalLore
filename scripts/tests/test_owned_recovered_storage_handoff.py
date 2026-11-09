"""Recovered journal -> actual SDK14 owner storage wiring, using tiny D fixtures.

Recovery storage, RUN rebinding, admission schema and closure accounting are real.
Only the profile's literal guest path is redirected to the isolated fixture.
SDK/build/prepared-artifact, native process/capture and worker cleanup proofs are
explicit synthetic ports. These tests do not qualify Android or native cleanup.
Copyright 2026 LocalLore contributors. SPDX-License-Identifier: Apache-2.0
"""
from contextlib import ExitStack, contextmanager
import copy
from dataclasses import replace
import os
from pathlib import Path, PureWindowsPath
from types import SimpleNamespace
import unittest
from unittest.mock import Mock, patch

from benchmarks import owned_record_controls_ui_owner as sdk14
from benchmarks import owned_target_owner as owner
from benchmarks import prepare_recovery_contract as history
from benchmarks import receipt_avd_environment as env
from benchmarks import receipt_avd_storage as storage
from scripts.tests import test_prepare_recovery_adversaries as recovered_fixture
from scripts.tests import test_record_controls_ui_profile as sdk14_fixture


class _LaunchBoundary(RuntimeError):
    pass


@unittest.skipUnless(os.name == 'nt', 'D-only Windows recovered owner fixture')
class RecoveredOwnerStorageTests(unittest.TestCase):
    @contextmanager
    def recovered(self, *, known=True):
        fixture = recovered_fixture.PrepareRecoveryAdversaries(methodName='runTest')
        try:
            fixture.setUp()
            def worker(proposal, proposal_path, authorization_path, digest):
                fixture.synthetic_worker(proposal)
                return dict(proposal_sha256=digest, synthetic_prepared=True)
            fixture.worker.side_effect = worker
            fixture.close_known = known
            if known:
                fixture.successful()
            else:
                plan, authorization, _ = fixture.make_plan()
                with self.assertRaisesRegex(storage.StorageRefused, 'cleanup_unknown'):
                    fixture.execute(plan, authorization)
                fixture.assert_charge('prepared')
            completion = storage.read_json(fixture.entry()['recovery']['completion']['path'])
            fixture.current_prepare = completion['proposal']
            fixture.run_proposal = fixture.base / 'distinct-run-proposal.json'
            # Tiny synthetic preparation has no actual image/configuration. Keep
            # the ordinary plan/auth schemas, mock only SDK artifact readiness.
            with patch.object(env, 'verify_prepared'):
                env.plan_run(fixture.current_prepare['path'], fixture.root/'prepared-v1.json',
                             fixture.run_proposal, max_seconds=1800)
            fixture.run_pin = env.binding(fixture.run_proposal)
            fixture.run_authorization = fixture.base/'distinct-run-authorization.json'
            env.create_json(fixture.run_authorization, dict(version=1, phase='run',
                proposal_sha256=fixture.run_pin['sha256'], allow_environment_calls=True, root_go_pending=False))
            profile = replace(sdk14.contract._API.profile, GUEST_ROOT=PureWindowsPath(fixture.root))
            with patch.object(sdk14.contract._API, 'profile', profile):
                yield fixture
        finally:
            fixture.doCleanups()

    def admission(self, fixture, output):
        value = sdk14_fixture.admission()
        value['root'] = str(output)
        value['server']['root'] = str(output/'server')
        value['guest'].update(root=str(fixture.root), proposal=copy.deepcopy(fixture.run_pin),
            authorization=env.binding(fixture.run_authorization))
        # All production SDK14 constants and nineteen selectors remain in use.
        self.assertEqual(len(sdk14.contract.INSTRUMENTATIONS), 19)
        self.assertEqual(value['protocol'], sdk14.contract.PROTOCOL)
        self.assertEqual(sdk14.contract.validate_admission(value), value)
        return value

    @contextmanager
    def runtime(self, fixture, *, mutate_admission=None):
        output = fixture.base/'runtime-owner'
        output.mkdir()
        admission = self.admission(fixture, output)
        if mutate_admission is not None:
            mutate_admission(admission)
        admission_path = fixture.base/'runtime-admission.json'
        env.create_json(admission_path, admission)
        binding = env.binding(admission_path)
        worker = dict(pid=22, creation_filetime=101, executable=admission['python']['executable']['path'])
        with patch.object(sdk14, '_verify_build') as build:
            try:
                runtime = sdk14._RecordControlsUiTargetRuntime(
                    dict(validated_admission=admission, admission=binding), binding, output)
            except sdk14.contract.TargetRefused:
                build.assert_not_called()
                raise
        build.assert_called_once_with(admission)
        runtime.guard = Mock()  # No native process/socket or live resource ownership claim.
        runtime.proposal = env.read_json(fixture.run_proposal)
        runtime.worker = worker
        original_transition = env.storage_transition
        def isolated(operation, *args, **kwargs):
            return original_transition(operation, *args, registry=fixture.registry, **kwargs)
        with patch.object(env, 'verify_prepared') as readiness, \
                patch.object(env, 'storage_transition', side_effect=isolated), \
                patch.object(owner.primitives, 'ServerCapture', return_value=Mock()), \
                patch.object(owner.subprocess, 'Popen') as launch:
            yield runtime, admission, readiness, launch

    def reach_launch(self, fixture):
        before_prepare = fixture.current_prepare['sha256']
        self.assertNotEqual(before_prepare, fixture.run_pin['sha256'])
        with self.runtime(fixture) as (runtime, admission, readiness, launch):
            def sentinel(*args, **kwargs):
                entry = fixture.entry()
                self.assertEqual((entry['state'], entry['reserved_bytes'], entry['proposal_sha256']),
                                 ('retained', 40*storage.GIB, fixture.run_pin['sha256']))
                claim = env.read_json(fixture.root/sdk14.contract.BOOT_CLAIM_FILE)
                self.assertEqual(claim['proposal'], fixture.run_pin)
                self.assertEqual(claim['protocol'], sdk14.contract.PROTOCOL)
                raise _LaunchBoundary('mocked launch reached only after real storage and claim')
            launch.side_effect = sentinel
            with self.assertRaises(_LaunchBoundary):
                runtime.start_guest()
            launch.assert_called_once()
            readiness.assert_called_once_with(runtime.proposal, initial=True)
        self.assertEqual(len(fixture.ledger()['entries']), 2)
        self.assertEqual(storage.read_json(fixture.entry()['recovery']['completion']['path'])['proposal'],
                         fixture.current_prepare)
        return before_prepare

    def parent(self, fixture, *, failure=None):
        """Actual parent spine, actual schema and storage; simulated cleanup ports."""
        output = fixture.base/'closure-owner'
        admission = self.admission(fixture, output)
        admission_path = fixture.base/'closure-admission.json'
        env.create_json(admission_path, admission)
        binding = env.binding(admission_path)
        parent = dict(pid=11, creation_filetime=100, executable=admission['python']['executable']['path'])
        child = dict(pid=22, creation_filetime=101, executable=admission['python']['executable']['path'])
        handles = Mock()
        handles.add.side_effect = [(1, parent), (2, child)]
        handles.close.return_value = failure != 'handles'
        api = Mock()
        api.identity.return_value = parent
        api.alive.return_value = True
        verified = []
        def inputs(actual, admitted, **kwargs):
            self.assertIs(kwargs['_contract'], sdk14.contract)
            sdk14.contract.validate_admission(actual)
            self.assertEqual(env.read_json(admitted['path']), actual)
            for pin in (admitted, actual['guest']['proposal'], actual['guest']['authorization']):
                env.check_binding(pin)
        def verify(*args):
            verified.append(True)
            if failure == 'worker':
                raise owner.OwnerRefused('cleanup')
            return dict(reason='stop_requested')
        def supervise(command, request, capture, seconds, started):
            self.assertEqual(Path(command[4]).name, sdk14.contract.OWNER_SCRIPT)
            started(SimpleNamespace(pid=22))
            env.create_json(output/'worker-result-v1.json', dict(synthetic_verified_worker=True))
            return dict(cleanup_complete=failure != 'owner', synthetic_owner=True)
        original_transition = env.storage_transition
        def close_storage(operation, *args, **kwargs):
            self.assertIs(operation, storage.record_closed)
            self.assertTrue(verified)
            self.assertTrue(handles.close.called)
            self.assertTrue((output/'after-v1.json').is_file())
            if failure == 'storage':
                raise env.EnvironmentRefused('storage_registry_locked')
            return original_transition(operation, *args, registry=fixture.registry, **kwargs)
        with ExitStack() as stack:
            for target, name, options in (
                (owner.output_control, 'validate_output', dict(return_value=output)),
                (owner.output_control, '_prepare_environment', {}),
                (owner, '_inputs', dict(side_effect=inputs)),
                (owner, '_ProcessApi', dict(return_value=api)),
                (owner.primitives, 'ProcessHandles', dict(return_value=handles)),
                (owner.primitives, '_owner_ok', dict(return_value=failure != 'owner')),
                (env, 'supervise', dict(side_effect=supervise)),
                (owner, '_read_json', dict(side_effect=lambda pin, **_: env.read_json(pin['path']))),
                (sdk14.verification, 'verify_owned_target_result', dict(side_effect=verify)),
                (sdk14.contract, 'source_bindings', dict(return_value=[] if failure == 'source'
                                                       else copy.deepcopy(admission['sources']))),
                (owner.file_guard, '_python_bindings', dict(return_value=copy.deepcopy(admission['python']))),
                (env, 'storage_transition', dict(side_effect=close_storage)),
            ):
                stack.enter_context(patch.object(target, name, **options))
            result = owner._parent(binding, admission, _contract=sdk14.contract,
                                   _verification=sdk14.verification)
        return result, output

    def test_same_recovered_root_retains_run_digest_before_sdk14_claim_and_launch(self):
        with self.recovered() as fixture:
            prepare_digest = self.reach_launch(fixture)
            intent = storage.read_json(fixture.entry()['recovery']['intent']['path'])
            plan = storage.read_json(intent['plan']['path'])
            self.assertEqual(plan['prior_entry'], fixture.old_entry)
            self.assertNotEqual(prepare_digest, fixture.old_entry['proposal_sha256'])
            fixture.assert_old_evidence()

    def test_unknown_recovery_cleanup_cannot_retain_or_publish_sdk14_boot_claim(self):
        with self.recovered(known=False) as fixture:
            before = fixture.ledger_bytes()
            with self.runtime(fixture) as (runtime, _, _, launch):
                with self.assertRaisesRegex(env.EnvironmentRefused, 'recovery_cleanup_unknown'):
                    runtime.start_guest()
                launch.assert_not_called()
            self.assertEqual(before, fixture.ledger_bytes())
            fixture.assert_charge('prepared')
            self.assertFalse((fixture.root/sdk14.contract.BOOT_CLAIM_FILE).exists())

    def test_missing_history_or_mutated_recovery_source_refuses_before_claim_and_launch(self):
        for damage in ('intent', 'outcome', 'prior', 'source'):
            with self.subTest(damage=damage), self.recovered() as fixture:
                reference = fixture.entry()['recovery']
                path = Path(reference[damage]['path']) if damage in ('intent', 'outcome') else \
                    fixture.prior if damage == 'prior' else Path(fixture.sources[0]['path'])
                original = path.read_bytes()
                before = fixture.ledger_bytes()
                if damage in ('intent', 'outcome'):
                    path.unlink()
                else:
                    path.write_bytes(original+b'changed fixture input')
                try:
                    with self.runtime(fixture) as (runtime, _, _, launch):
                        with self.assertRaises((env.EnvironmentRefused, storage.StorageRefused)):
                            runtime.start_guest()
                        launch.assert_not_called()
                    self.assertEqual(before, fixture.ledger_bytes())
                    self.assertEqual(fixture.entry()['reserved_bytes'], 40*storage.GIB)
                    self.assertFalse((fixture.root/sdk14.contract.BOOT_CLAIM_FILE).exists())
                finally:
                    path.write_bytes(original)

    def test_stale_run_proposal_refuses_before_storage_transition_and_claim(self):
        with self.recovered() as fixture:
            with self.runtime(fixture) as (runtime, _, _, launch):
                before = fixture.ledger_bytes()
                fixture.run_proposal.write_bytes(b'changed RUN input')
                with self.assertRaises(env.EnvironmentRefused):
                    runtime.start_guest()
                launch.assert_not_called()
            self.assertEqual(before, fixture.ledger_bytes())
            fixture.assert_charge('prepared')
            self.assertFalse((fixture.root/sdk14.contract.BOOT_CLAIM_FILE).exists())

    def test_actual_sdk14_constructor_rejects_wrong_protocol_or_missing_storage_source(self):
        for damage in ('protocol', 'source'):
            with self.subTest(damage=damage), self.recovered() as fixture:
                def mutate(value):
                    if damage == 'protocol':
                        value['protocol'] = 'owned-emulator-target-v1'
                    else:
                        value['sources'] = [pin for pin in value['sources']
                            if PureWindowsPath(pin['path']).name != 'receipt_avd_storage.py']
                before = fixture.ledger_bytes()
                with self.assertRaises(sdk14.contract.TargetRefused):
                    with self.runtime(fixture, mutate_admission=mutate):
                        self.fail('invalid SDK14 admission reached runtime')
                self.assertEqual(before, fixture.ledger_bytes())
                self.assertFalse((fixture.root/sdk14.contract.BOOT_CLAIM_FILE).exists())

    def test_simulated_known_owner_closure_charges_history_and_preserves_prepare_digest(self):
        with self.recovered() as fixture:
            prepare_digest = self.reach_launch(fixture)
            result, output = self.parent(fixture)
            self.assertEqual(result, 0)
            entry = fixture.entry()
            self.assertEqual(entry['state'], 'closed')
            self.assertEqual(entry['proposal_sha256'], fixture.run_pin['sha256'])
            self.assertEqual(storage.read_json(entry['recovery']['completion']['path'])['proposal']['sha256'],
                             prepare_digest)
            closure = fixture.root/'guest-storage-closure-v1.json'
            value = storage.read_json(closure)
            self.assertEqual(value['proposal_sha256'], fixture.run_pin['sha256'])
            paths = list(storage._files(fixture.root).values()) + [closure] + history.history_paths(entry)
            paths += [Path(value[key]['path']) for key in storage.ADAPTER_PROOFS]
            self.assertEqual(entry['reserved_bytes'], storage._logical_bytes(paths))
            self.assertLess(entry['reserved_bytes'], 40*storage.GIB)
            for pin in (entry['recovery']['intent'], entry['recovery']['completion'], entry['recovery']['outcome']):
                self.assertIn(Path(pin['path']), history.history_paths(entry))
            fixture.assert_old_evidence()

    def test_unknown_parent_worker_handles_source_or_storage_never_reduce_run_reservation(self):
        for failure in ('owner', 'worker', 'handles', 'source', 'storage'):
            with self.subTest(failure=failure), self.recovered() as fixture:
                self.reach_launch(fixture)
                result, output = self.parent(fixture, failure=failure)
                self.assertEqual(result, 1)
                self.assertFalse(env.read_json(output/'result-v1.json')['qualified_target'])
                fixture.assert_charge('retained')
                self.assertEqual(fixture.entry()['proposal_sha256'], fixture.run_pin['sha256'])
                self.assertEqual(storage.read_json(fixture.entry()['recovery']['completion']['path'])['proposal'],
                                 fixture.current_prepare)
                if (fixture.root/'guest-storage-closure-v1.json').exists():
                    self.assertEqual(failure, 'storage')
                fixture.assert_old_evidence()


if __name__ == '__main__':
    unittest.main()
