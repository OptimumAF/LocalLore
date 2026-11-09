"""Fresh SDK15 inputs over real isolated history; no applicable grants or native execution."""
import copy
import os
from pathlib import Path
import unittest
from unittest.mock import patch

from benchmarks import prepare_recovery_contract as history
from benchmarks import receipt_avd_environment as env
from benchmarks import receipt_avd_storage as storage
from scripts import library_ui_recovery_contract as rules
from scripts import library_ui_run_inputs as builder
from scripts.tests.library_ui_recovery_test_fixture import BuilderFixture

REFUSED = (rules.OperationRefused, env.EnvironmentRefused, storage.StorageRefused)


@unittest.skipUnless(os.name == 'nt', 'Tiny D recovery and source files, SDK/build/native ports mocked')
class LibraryUiRunInputTests(unittest.TestCase):
    def test_known_recovery_produces_fresh_bound_run_and_admission_without_transitioning_the_ledger(self):
        with BuilderFixture() as graph:
            result = graph.create()
            self.assertEqual(set(result), {'version', 'scope', 'authority', 'recovery_authorization', 'recovery_result',
                'ledger_before', 'run_proposal', 'run_authorization', 'admission', 'input'})
            self.assertEqual(result['scope'], 'sdk15-post-recovery-inputs-v1')
            for role in ('run_proposal', 'run_authorization', 'admission', 'input'): env.check_binding(result[role])
            run = env.read_json(result['run_proposal']['path']); auth = env.read_json(result['run_authorization']['path'])
            self.assertEqual((run['phase'], run['memory_mib'], run['cores'], run['max_seconds']), ('run', 8192, 4, 1800))
            self.assertEqual(auth, dict(version=1, phase='run', proposal_sha256=result['run_proposal']['sha256'],
                allow_environment_calls=True, root_go_pending=False))
            admission = env.read_json(result['admission']['path'])
            graph.api.contract.validate_admission(admission); graph.api.contract.revalidate_inputs(admission)
            self.assertEqual((admission['protocol'], admission['guest']['root'], admission['guest']['proposal']),
                ('owned-emulator-library-ui-v1', str(graph.fixture.root), result['run_proposal']))
            self.assertEqual(len(admission['sources']), 25); self.assertEqual(len(graph.api.contract.INSTRUMENTATIONS), 4)
            self.assertEqual(env.read_json(result['input']['path']), dict(version=1, scope='library-ui-run-input-v1',
                admission=result['admission'], helper=graph.handoff['activation']))
            self.assertEqual(graph.fixture.ledger_bytes(), graph.before_ledger)
            graph.fixture.assert_charge('prepared'); graph.fixture.assert_old_evidence()
            self.assertFalse((graph.fixture.root / graph.api.contract.BOOT_CLAIM_FILE).exists())
            graph.planner.assert_called_once()

    def test_genuine_legacy_v1_entry_refuses_before_any_run_or_activation_input(self):
        with BuilderFixture() as graph:
            f = graph.fixture; original = f.ledger_bytes()
            claim = history.claim_path(f.registry, f.root); preserved = f.base / 'preserved-intent.json'
            claim.rename(preserved)
            legacy = f.ledger(); legacy['version'] = 1
            for row in legacy['entries']: row.pop('recovery')
            (f.registry / 'ledger-v1.json').write_bytes(storage.encoded(legacy))
            try:
                storage._validate(legacy, f.registry)  # A valid legacy ledger, not a malformed-fixture refusal.
                before = f.ledger_bytes()
                with self.assertRaises(rules.OperationRefused): graph.create()
                self.assertEqual(f.ledger_bytes(), before); graph.planner.assert_not_called()
                self.assertFalse(rules.RUN_PROPOSAL.exists()); self.assertFalse(rules.INPUT.exists())
            finally:
                preserved.rename(claim); (f.registry / 'ledger-v1.json').write_bytes(original)

    def test_unknown_recovery_cleanup_never_reaches_run_planning_or_input_publication(self):
        with BuilderFixture(known=False) as graph:
            with self.assertRaises(REFUSED): graph.create()
            graph.planner.assert_not_called(); graph.fixture.assert_charge('prepared')
            self.assertEqual(graph.fixture.ledger_bytes(), graph.before_ledger)
            self.assertFalse(rules.RUN_PROPOSAL.exists()); self.assertFalse(rules.ADMISSION.exists()); self.assertFalse(rules.INPUT.exists())

    def test_missing_changed_or_unlinked_recovery_history_cannot_be_replaced_by_known_terminal_flags(self):
        for damage in ('completion', 'prepare_authorization', 'marker', 'source'):
            with self.subTest(damage=damage), BuilderFixture() as graph:
                entry = graph.fixture.entry(); completion = env.read_json(entry['recovery']['completion']['path'])
                path = Path({'completion': entry['recovery']['completion']['path'],
                    'prepare_authorization': completion['authorization']['path'], 'marker': completion['marker']['path'],
                    'source': graph.fixture.sources[0]['path']}[damage])
                original = path.read_bytes()
                try:
                    path.write_bytes(original + b' changed')
                    with self.assertRaises(REFUSED): graph.create()
                    graph.planner.assert_not_called(); self.assertFalse(rules.INPUT.exists())
                    self.assertEqual(graph.fixture.ledger_bytes(), graph.before_ledger)
                finally: path.write_bytes(original)

    def test_freshly_bound_authority_without_one_boot_consent_refuses_before_planning(self):
        with BuilderFixture() as graph:
            value = copy.deepcopy(graph.authority); value['allow_one_boot'] = False
            rules.AUTHORITY.write_bytes(env.encoded(value)); graph.authority_pin = env.binding(rules.AUTHORITY)
            with self.assertRaises(rules.OperationRefused): graph.create()
            graph.planner.assert_not_called(); self.assertFalse(rules.RUN_AUTHORIZATION.exists()); self.assertFalse(rules.INPUT.exists())

    def test_frozen_handoff_static_or_current_source_drift_never_becomes_fresh_inputs(self):
        for damage in ('handoff', 'static', 'source', 'activation'):
            with self.subTest(damage=damage), BuilderFixture() as graph:
                if damage == 'source':
                    original = graph.api.contract.source_bindings
                    with patch.object(graph.api.contract, 'source_bindings', return_value=original()[:-1]):
                        with self.assertRaises(REFUSED): graph.create()
                elif damage == 'activation':
                    with patch.object(graph.api.activation, 'HELPER', Path(graph.fixture.base / 'unselected-helper.py')):
                        with self.assertRaises(REFUSED): graph.create()
                else:
                    path = Path(rules.HANDOFF['path'] if damage == 'handoff' else graph.static_pin['path'])
                    path.write_bytes(path.read_bytes() + b' changed')
                    with self.assertRaises(REFUSED): graph.create()
                graph.planner.assert_not_called(); self.assertFalse(rules.INPUT.exists())

    def test_all_existing_output_or_boot_claim_destinations_remain_spent_and_unchanged(self):
        for role in ('runtime', 'controls', 'run', 'authorization', 'claim'):
            with self.subTest(role=role), BuilderFixture() as graph:
                path = {'runtime': rules.RUNTIME, 'controls': rules.CONTROLS, 'run': rules.RUN_PROPOSAL,
                    'authorization': rules.RUN_AUTHORIZATION, 'claim': rules.GUEST / graph.api.contract.BOOT_CLAIM_FILE}[role]
                if role in ('runtime', 'controls'):
                    path.mkdir(); marker = path / 'preserve.bin'; marker.write_bytes(b'preserve synthetic prior state')
                else: marker = path; marker.write_bytes(b'preserve synthetic prior state')
                with self.assertRaises(rules.OperationRefused): graph.create()
                self.assertEqual(marker.read_bytes(), b'preserve synthetic prior state'); graph.planner.assert_not_called()
                self.assertEqual(graph.fixture.ledger_bytes(), graph.before_ledger)

    def test_planner_failure_or_changed_written_proposal_never_authorizes_or_publishes_ui_input(self):
        for damage in ('failure', 'mismatch'):
            with self.subTest(damage=damage), BuilderFixture() as graph:
                original = graph.planner._mock_wraps
                def plan(*args, **kwargs):
                    if damage == 'failure': raise OSError('PRIVATE synthetic SDK planning fault')
                    value = original(*args, **kwargs); rules.RUN_PROPOSAL.write_bytes(env.encoded(dict(value, max_seconds=1799)))
                    return value
                graph.planner.side_effect = plan
                with self.assertRaises((OSError, *REFUSED)): graph.create()
                self.assertFalse(rules.RUN_AUTHORIZATION.exists()); self.assertFalse(rules.INPUT.exists())
                self.assertEqual(graph.fixture.ledger_bytes(), graph.before_ledger)

    def test_run_authorization_failure_preserves_partial_files_without_any_retry(self):
        with BuilderFixture() as graph:
            with patch.object(env, 'authorize', side_effect=env.EnvironmentRefused('synthetic_authorize_refused')):
                with self.assertRaises(env.EnvironmentRefused): graph.create()
            before = {p: p.read_bytes() for p in (rules.RUN_PROPOSAL, rules.RUN_AUTHORIZATION)}
            self.assertFalse(rules.INPUT.exists()); self.assertFalse(rules.ADMISSION.exists())
            with self.assertRaises(rules.OperationRefused): graph.create()
            self.assertEqual({p: p.read_bytes() for p in before}, before)
            self.assertEqual(graph.fixture.ledger_bytes(), graph.before_ledger); self.assertEqual(graph.planner.call_count, 1)

    def test_final_ledger_drift_or_source_refusal_happens_before_activation_input_publication(self):
        for damage in ('ledger', 'source'):
            with self.subTest(damage=damage), BuilderFixture() as graph:
                original_recovered = builder.recovered; original_frozen = builder.frozen_inputs
                counts = {'recovered': 0, 'frozen': 0}
                def recovered(*args):
                    counts['recovered'] += 1
                    if damage == 'ledger' and counts['recovered'] == 2:
                        path = graph.fixture.registry / 'ledger-v1.json'; path.write_bytes(path.read_bytes() + b'\n')
                    return original_recovered(*args)
                def frozen(*args):
                    counts['frozen'] += 1
                    if damage == 'source' and counts['frozen'] == 2: raise rules.OperationRefused('source')
                    return original_frozen(*args)
                with patch.object(builder, 'recovered', side_effect=recovered), patch.object(builder, 'frozen_inputs', side_effect=frozen):
                    with self.assertRaises(rules.OperationRefused): graph.create()
                self.assertTrue(rules.ADMISSION.exists()); self.assertFalse(rules.INPUT.exists())
                graph.fixture.assert_charge('prepared')

    def test_initial_record_mutation_is_rejected_by_public_save_readback_without_input(self):
        with BuilderFixture() as graph:
            original = env.create_json
            def changed(path, value):
                original(path, value)
                if Path(path) == rules.RUN_AUTHORIZATION: Path(path).write_bytes(b'{}\n')
            with patch.object(env, 'create_json', side_effect=changed):
                with self.assertRaises(rules.OperationRefused): graph.create()
            self.assertFalse(rules.ADMISSION.exists()); self.assertFalse(rules.INPUT.exists())
            self.assertEqual(graph.fixture.ledger_bytes(), graph.before_ledger)

    def test_actual_interpreter_and_runtime_dll_must_match_pinned_inputs_before_attempt_or_recovery(self):
        from scripts import run_library_ui_recovery as operator
        from scripts.tests.library_ui_recovery_test_fixture import OperatorFixture
        with OperatorFixture() as graph:
            _, _, installed = builder.frozen_inputs(graph.authority_pin)
            self.assertEqual(graph.api.probe._python_bindings(), installed['python'])
            self.assertFalse(rules.LIVE.exists()); graph.supervisor.assert_not_called()
        for component in ('executable', 'runtime_dll'):
            for entry in ('frozen_inputs', 'operator'):
                with self.subTest(component=component, entry=entry), OperatorFixture() as graph:
                    actual = graph.graph.wire.runtime_bindings()
                    path = graph.root / ('different-actual-' + component + '.bin')
                    path.write_bytes(b'SYNTHETIC other interpreter/runtime observation; never executed')
                    actual[component] = env.binding(path)
                    self.assertNotEqual(actual, graph.graph.installed['python'])
                    with patch.object(graph.api.probe, '_python_bindings', return_value=actual):
                        with self.assertRaises(rules.OperationRefused) as refused:
                            if entry == 'frozen_inputs': builder.frozen_inputs(graph.authority_pin)
                            else: operator.execute(graph.authority_pin)
                    self.assertEqual(str(refused.exception), 'python')
                    graph.api.build.verify_frozen_product.assert_not_called(); graph.supervisor.assert_not_called()
                    self.assertFalse(rules.LIVE.exists()); self.assertFalse(rules.EXECUTION.exists())
                    self.assertFalse(rules.INPUT.exists())
                    self.assertEqual(graph.graph.fixture.ledger_bytes(), graph.before_ledger)


if __name__ == '__main__': unittest.main()
