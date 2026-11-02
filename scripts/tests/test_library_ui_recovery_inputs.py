"""File-only SDK15 inspection adversaries on tiny owned D fixtures.

Real binding/JSON/path operations stay active. Git observations, frozen-product
attestation and snapshot recovery planning are explicit ports, never evidence of
an SDK, a real ledger, authorization, native cleanup or executable readiness.
Copyright 2026 LocalLore contributors. SPDX-License-Identifier: Apache-2.0
"""
import copy
from contextlib import ExitStack, contextmanager, redirect_stdout
import io
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import Mock, patch

import benchmarks
from benchmarks import owned_library_ui_contract as profile
from benchmarks import receipt_avd_environment as env
from benchmarks import receipt_avd_storage as storage
from scripts import freeze_library_ui_recovery_inputs as tool

BASE = Path('D:/Dev/Experiments/LocalLore/2026-11-02-library-recovery-readiness-v1/test-agent-v1')
FILES = {'b80-byte-attestation-v1.json', 'recovery-plan-v1.json', 'static-installed-inputs-v1.json',
    'handoff-inputs-v1.json', 'result-v1.json'}
RECOVERY_SOURCES = {'receipt_avd_environment.py', 'receipt_avd_storage.py', 'runtime_spike.py',
    'host_commit_capacity.py', 'prepare_recovery_contract.py', 'receipt_avd_prepare_recovery.py', 'prepare_recovery_windows.py'}
SELECTORS = (
    ('library_recovery_equal', 'org.locallore.app.ui.LibraryActionScopeScreenTest',
     'oldRecoverCannotBorrowAnEqualFailedRetryAndFreshUnselectedRecoveryWorks'),
    ('library_story_popup', 'org.locallore.app.ui.LibraryActionScopeScreenTest',
     'oldStoryRowsAndOpenerCannotActOnReopenedOrEqualRefreshedLibrary'),
    ('library_timeline_popup', 'org.locallore.app.ui.LibraryActionScopeScreenTest',
     'oldTimelineRowCannotActOnReopenedMenuAndFreshChoiceWorks'),
    ('library_screen_remount', 'org.locallore.app.ui.LibraryActionScopeScreenTest',
     'disposedScreenRowCannotBorrowSameViewModelAfterRemount'),
)


def budget(extra=0):
    total = 0
    if BASE.exists():
        for root, folders, files in os.walk(BASE, followlinks=False):
            for name in folders + files:
                value = (Path(root) / name).lstat()
                if getattr(value, 'st_file_attributes', 0) & 1024: raise AssertionError('Fixture reparse refused')
            total += sum((Path(root) / name).stat().st_size for name in files)
    if total + extra > 64 * 1024 * 1024: raise RuntimeError('fixture_budget_refused')


class Graph:
    def __init__(self):
        budget(1024 * 1024); BASE.mkdir(parents=True, exist_ok=True)
        self.root = Path(tempfile.mkdtemp(prefix='inspection-', dir=BASE))
        self.source = self.root / 'frozen-source'; (self.source / 'benchmarks/native').mkdir(parents=True)
        self.out = self.root / 'inspection'; self.out.mkdir(); self.output = self.out / 'frozen-inputs-v1'
        self.registry = self.root / 'isolated-registry'; self.registry.mkdir()
        self.guest = self.root / 'absent-guest-parent' / 'avd-v1'
        self.credential = self.root / 'credential-path-only' / 'adbkey'
        self.source_pins = []
        for name in sorted(profile.SOURCE_NAMES):
            path = self.source / 'benchmarks' / name; path.write_bytes(('SYNTHETIC source: ' + name).encode())
            self.source_pins.append(env.binding(path))
        self.recovery_pins = [copy.deepcopy(p) for p in self.source_pins if Path(p['path']).name in RECOVERY_SOURCES]
        # Recovery-only dependencies are not all part of the 25 owner bindings.
        for name in sorted(RECOVERY_SOURCES - {Path(p['path']).name for p in self.recovery_pins}):
            path = self.source / 'benchmarks' / name; path.write_bytes(('SYNTHETIC recovery source: ' + name).encode())
            self.recovery_pins.append(env.binding(path))
        self.recovery_pins.sort(key=lambda p: p['path'])
        self.ledger = self.registry / 'ledger-v1.json'
        raw = b'{"synthetic_snapshot_only":true}'
        self.ledger.write_bytes(raw + b' ' * (41230 - len(raw)))
        self.before_ledger = self.ledger.read_bytes()
        self.ledger_sha256 = env.binding(self.ledger)['sha256']
        self.failure = self.store(self.root / 'operator-failure.json', {'synthetic_observation': True})
        native = self.source / 'benchmarks/native/deny_adb_client.c'; native.write_bytes(b'SYNTHETIC read-only refuser source')
        old_native = self.root / 'old-refuser-source.c'; old_native.write_bytes(native.read_bytes())
        def marker(name):
            path = self.root / name; path.write_bytes(b'SYNTHETIC inert installed metadata: ' + name.encode()); return env.binding(path)
        adb = marker('adb.exe'); python = marker('python.exe'); runtime = marker('python314.dll')
        self.installed = dict(adb=adb, tools=[adb, marker('AdbWinApi.dll')],
            python={'executable': python, 'runtime_dll': runtime}, capabilities=marker('capabilities.json'),
            source_review=marker('source-review.md'), compatibility=marker('compatibility.md'),
            emulator=marker('emulator.exe'), qemu=marker('qemu-system-x86_64-headless.exe'),
            refuser=marker('deny-adb-client.exe'), refuser_source=env.binding(old_native), auth_key_path=str(self.credential))
        self.static = self.store(self.root / 'old-static.json', self.installed)
        self.build_pin = self.store(self.root / 'build.json', {'synthetic_product_port': True})
        self.apks = {'product_apk': marker('product-not-an-apk.bin'), 'test_apk': marker('tests-not-an-apk.bin')}
        self.expected_artifacts = dict(build=copy.deepcopy(self.build_pin), **copy.deepcopy(self.apks))
        self.manifest = dict(roster=[list(row) for row in SELECTORS], synthetic_byte_attestation=True)
        self.writes = []; self.git_count = 0; self.on_git = lambda index: None
        self.before_write = lambda name, value: None; self.after_write = lambda name, path, value: None
        self.plan_sources = None; self.plan_mismatch = False; self.forbidden = []
        def forbid(name):
            value = Mock(side_effect=AssertionError('Forbidden inspection mechanism: ' + name))
            self.forbidden.append(value); return value
        self.api_env = SimpleNamespace(encoded=env.encoded, binding=self.binding, check_binding=self.check,
            read_json=env.read_json, safe_path=env.safe_path, create_json=self.create,
            resource_facts=forbid('resource_facts'), authorize=forbid('authorize'), prepare=forbid('prepare'),
            plan_run=forbid('plan_run'), supervise=forbid('supervise'), process_identity=forbid('process_identity'))
        self.api_storage = SimpleNamespace(DEFAULT_REGISTRY=self.registry,
            reserve_prepare=forbid('reserve_prepare'), record_state=forbid('record_state'),
            record_closed=forbid('record_closed'), _locked=forbid('ledger_lock'))
        self.recovery = SimpleNamespace(plan=Mock(side_effect=self.plan), _sources=Mock(side_effect=lambda: copy.deepcopy(self.recovery_pins)),
            execute=forbid('recovery_execute'))
        self.contract = SimpleNamespace(CLIENT_VERSION=15, MODEL_MATERIAL=False, INSTRUMENTATIONS=SELECTORS,
            ARTIFACT_KEYS={'build', 'product_apk', 'test_apk'}, GUEST_ROOT=self.guest,
            source_bindings=Mock(side_effect=lambda: copy.deepcopy(self.source_pins)))
        self.activation = SimpleNamespace(SOURCE_ROOT=self.source, HELPER=self.source / 'benchmarks/library_ui_activation.py',
            CONTROLS=self.root / 'absent-controls', RUNTIME=self.root / 'absent-runtime')
        self.build = SimpleNamespace(_FIXED={'apks': self.apks}, verify_frozen_product=Mock(side_effect=self.verify_build))
        self.api = SimpleNamespace(env=self.api_env, storage=self.api_storage, recovery=self.recovery,
            contract=self.contract, activation=self.activation, build=self.build)

    @staticmethod
    def store(path, value):
        env.create_json(path, value); return env.binding(path)
    def binding(self, path):
        if Path(path) == self.credential: raise AssertionError('Credential bytes were observed')
        return env.binding(path)
    def check(self, pin):
        if Path(pin['path']) == self.credential: raise AssertionError('Credential bytes were observed')
        return env.check_binding(pin)
    def create(self, path, value):
        path = Path(path)
        if path.parent != self.output or path.name not in FILES: raise AssertionError('Executable/foreign record publication')
        self.before_write(path.name, value); self.writes.append(path.name)
        env.create_json(path, value); self.after_write(path.name, path, value)
    def verify_build(self, artifacts):
        if artifacts != self.expected_artifacts: raise ValueError('Synthetic fixed artifact mismatch')
        for pin in artifacts.values(): env.check_binding(pin)
        return copy.deepcopy(self.manifest)
    def plan(self, root, failure, output):
        if root != self.guest or Path(failure) != Path(self.failure['path']): raise AssertionError('Wrong plan delegation')
        value = dict(version=1, action='recover_failed_root_mkdir_once', root=str(root), registry=str(self.registry),
            sources=copy.deepcopy(self.recovery_pins if self.plan_sources is None else self.plan_sources),
            synthetic_snapshot_port=True)
        self.create(output, {} if self.plan_mismatch else value)
        return value
    def git(self):
        self.git_count += 1; self.on_git(self.git_count)

    @contextmanager
    def ports(self):
        with ExitStack() as stack:
            for name, value in dict(SOURCE=self.source, OUT=self.out, OUTPUT=self.output, REGISTRY=self.registry,
                GUEST=self.guest, LEDGER_SHA256=self.ledger_sha256, FAILURE=self.failure,
                STATIC=self.static, BUILD=self.build_pin).items():
                stack.enter_context(patch.object(tool, name, value))
            stack.enter_context(patch.object(tool, '_api', return_value=self.api))
            stack.enter_context(patch.object(tool, '_git', side_effect=self.git))
            stack.enter_context(patch.object(Path, 'cwd', return_value=self.source))
            stack.enter_context(patch.dict(os.environ, {name: 'D:/Dev/_Temp' for name in ('TEMP', 'TMP', 'TMPDIR')}))
            for target, name in ((subprocess, 'run'), (subprocess, 'Popen'), (env, 'resource_facts'),
                (env, 'authorize'), (env, 'prepare'), (storage, '_locked'), (storage, '_atomic_write')):
                guard = stack.enter_context(patch.object(target, name, side_effect=AssertionError('Native/ledger mechanism')))
                self.forbidden.append(guard)
            try: yield self
            finally:
                for forbidden in self.forbidden: forbidden.assert_not_called()
                budget()


@unittest.skipUnless(os.name == 'nt', 'Tiny physical D inspection records only')
class LibraryUiRecoveryInputsTests(unittest.TestCase):
    def test_import_has_no_io_and_operational_constants_remain_frozen(self):
        path = Path(tool.__file__); raw = path.read_bytes()
        with patch.object(Path, 'open', side_effect=AssertionError('Import IO')), \
             patch.object(Path, 'stat', side_effect=AssertionError('Import IO')), \
             patch.object(Path, 'mkdir', side_effect=AssertionError('Import IO')), \
             patch.object(subprocess, 'run', side_effect=AssertionError('Import process')):
            namespace = {'__name__': 'inspection_definitions_only', '__file__': str(path)}
            exec(compile(raw, str(path), 'exec'), namespace)
        self.assertIsNone(namespace['_MODULES'])
        self.assertEqual(namespace['SOURCE'], Path('D:/Worktrees/locallore-record-actions-tests-v1'))
        self.assertEqual(namespace['SOURCE_HEAD'], '18809566af72530408e2e25007ee4d501e6bf12a')
        self.assertEqual(namespace['OUTPUT'], Path('D:/Dev/Experiments/LocalLore/2026-11-02-library-recovery-readiness-v1/frozen-inputs-v1'))
        self.assertEqual(namespace['BUILD']['sha256'], '496f6358a860c2f5ff8809610d0d2f83e93dd867fbfdfe5e6c4c551871058ad3')
        self.assertEqual(namespace['FILES'], FILES)

    def test_fixed_real_pins_match_native_windows_binding_paths_without_relaxing_arbitrary_callers(self):
        expected = {
            'FAILURE': (2171, 'e21cf804358ba01c8f10c5b9a426da749b32cbc9c6c4920751e93ca8a1571505'),
            'STATIC': (3678, 'd2ca3f1ef02ed01169b84bb62090f663aca610db159e8db97606d1e1becccf99'),
            'BUILD': (30730, '496f6358a860c2f5ff8809610d0d2f83e93dd867fbfdfe5e6c4c551871058ad3'),
        }
        for role, (size, digest) in expected.items():
            pin = copy.deepcopy(getattr(tool, role))
            native = dict(path=str(Path(pin['path'])), bytes=size, sha256=digest)
            with self.subTest(role=role), patch.object(env, 'binding', return_value=native) as observed, \
                 patch.object(Path, 'open', side_effect=AssertionError('No real artifact read')), \
                 patch.object(Path, 'stat', side_effect=AssertionError('No real artifact stat')):
                self.assertEqual((pin['bytes'], pin['sha256']), (size, digest))
                try:
                    env.check_binding(pin)  # Keep the production reader and dictionary equality unchanged.
                except env.EnvironmentRefused:
                    self.fail(role + ' fixed pin cannot match the native Windows path emitted by binding')
                observed.assert_called_once_with(pin['path'])
        arbitrary = dict(path='D:/Synthetic/noncanonical-caller.json', bytes=17, sha256='a' * 64)
        canonical = dict(arbitrary, path=str(Path(arbitrary['path'])))
        self.assertNotEqual(arbitrary['path'], canonical['path'])
        with patch.object(env, 'binding', return_value=canonical), \
             patch.object(Path, 'open', side_effect=AssertionError('No caller artifact read')):
            with self.assertRaises(env.EnvironmentRefused): env.check_binding(arbitrary)

    def test_complete_inspection_emits_exactly_five_bound_non_executable_records(self):
        graph = Graph()
        with graph.ports(): result = tool.inspect()
        self.assertEqual({p.name for p in graph.output.iterdir()}, FILES)
        self.assertEqual(result['status'], 'completed-file-only')
        self.assertEqual((result['source_count'], result['recovery_source_count'], result['method_count']), (25, 7, 4))
        self.assertEqual(set(result['records']), {'attestation', 'recovery_plan', 'static_inputs', 'handoff'})
        for pin in result['records'].values(): env.check_binding(pin)
        handoff = env.read_json(result['handoff']['path'])
        self.assertEqual(handoff['fixed_roster'], [list(row) for row in SELECTORS])
        self.assertEqual(len(handoff['pending']), 6); self.assertFalse(handoff['approval_inferred'])
        self.assertTrue(handoff['original_observation_acceptance_required']); self.assertTrue(handoff['no_historical_process_closure_claim'])
        for key in ('ready_for_execution', 'approval_inferred', 'recovery_executed', 'authority_created',
            'guest_parent_created', 'admission_created', 'activation_input_created', 'resource_or_process_observation', 'sdk_or_adb_executed'):
            self.assertIs(result[key], False)
        self.assertEqual(graph.ledger.read_bytes(), graph.before_ledger)
        self.assertFalse(graph.guest.parent.exists()); self.assertFalse(graph.activation.CONTROLS.exists())
        self.assertFalse(graph.activation.RUNTIME.exists()); self.assertEqual(graph.git_count, 2)
        self.assertEqual(graph.contract.source_bindings.call_count, 2)
        graph.build.verify_frozen_product.assert_called_once_with(graph.expected_artifacts)
        graph.recovery.plan.assert_called_once_with(graph.guest, Path(graph.failure['path']), graph.output / 'recovery-plan-v1.json')

    def test_credential_path_is_metadata_and_never_statted_opened_hashed_or_copied(self):
        graph = Graph(); real_stat = Path.stat; real_open = Path.open; real_lstat = Path.lstat
        def guard(operation):
            def observed(path, *args, **kwargs):
                if Path(path) == graph.credential: raise AssertionError('Credential path observed')
                return operation(path, *args, **kwargs)
            return observed
        with graph.ports(), patch.object(Path, 'stat', guard(real_stat)), patch.object(Path, 'lstat', guard(real_lstat)), \
             patch.object(Path, 'open', guard(real_open)):
            tool.inspect()
        copied = env.read_json(graph.output / 'static-installed-inputs-v1.json')
        self.assertEqual(copied['auth_key_path'], str(graph.credential))

    def test_cli_accepts_only_inspect_and_valid_cli_still_reports_unready(self):
        for argv in ([], ['prepare'], ['inspect', '--runtime', 'D:/other'], ['inspect', '--registry', 'D:/other'], ['inspect', '--profile', '14']):
            with patch.object(tool, 'inspect', side_effect=AssertionError('Invalid CLI reached inspection')) as inspect:
                self.assertEqual(tool.main(argv), 1); inspect.assert_not_called()
        graph = Graph(); output = io.StringIO()
        with graph.ports(), redirect_stdout(output): self.assertEqual(tool.main(['inspect']), 0)
        value = json.loads(output.getvalue()); self.assertFalse(value['ready_for_execution']); self.assertFalse(value['authority_created'])

    def test_dirty_wrong_head_or_git_fault_refuses_before_any_plan_or_record(self):
        real_git = tool._git
        for fault in ('dirty', 'head', 'stderr', 'unbounded'):
            graph = Graph()
            first = SimpleNamespace(returncode=0, stdout=(tool.SOURCE_HEAD + '\n').encode(), stderr=b'')
            second = SimpleNamespace(returncode=0, stdout=b'', stderr=b'')
            if fault == 'dirty': second.stdout = b' M source.py\n'
            elif fault == 'head': first.stdout = b'f' * 40 + b'\n'
            elif fault == 'stderr': first.stderr = b'synthetic git refused'
            else: second.stdout = b'x' * 131073
            with graph.ports(), patch.object(tool, '_git', side_effect=real_git), \
                 patch.object(subprocess, 'run', side_effect=[first, second]) as git, self.subTest(fault=fault):
                with self.assertRaises(tool.InspectionRefused): tool.inspect()
                self.assertTrue(all(call.args[0][:4] == ['git', '--no-optional-locks', '-C', str(graph.source)] for call in git.call_args_list))
            graph.recovery.plan.assert_not_called(); self.assertFalse(graph.output.exists())

    def test_lazy_api_refuses_a_module_from_another_checkout_before_caching_it(self):
        graph = Graph(); api = tool._api
        names = ('receipt_avd_environment', 'receipt_avd_storage', 'receipt_avd_prepare_recovery',
            'owned_library_ui_contract', 'library_ui_activation', 'library_ui_build')
        with ExitStack() as stack:
            stack.enter_context(patch.object(tool, 'SOURCE', graph.source))
            stack.enter_context(patch.object(tool, '_MODULES', None))
            stack.enter_context(patch.object(sys, 'path', list(sys.path)))
            for name in names:
                path = graph.source / 'benchmarks' / (name + '.py')
                if name == 'library_ui_build': path = graph.root / 'foreign-checkout/benchmarks/library_ui_build.py'
                stack.enter_context(patch.object(benchmarks, name, SimpleNamespace(__file__=str(path)), create=True))
            with self.assertRaisesRegex(tool.InspectionRefused, 'module_source'): api()
            self.assertIsNone(tool._MODULES)

    def test_old_profile_missing_dependency_or_retargeted_fixed_paths_refuses_before_publication(self):
        for fault in ('sdk14', 'model', 'missing', 'registry', 'activation', 'guest'):
            graph = Graph()
            if fault == 'sdk14': graph.contract.CLIENT_VERSION = 14
            elif fault == 'model': graph.contract.MODEL_MATERIAL = True
            elif fault == 'missing': graph.source_pins = [p for p in graph.source_pins if Path(p['path']).name != 'prepare_recovery_contract.py']
            elif fault == 'registry': graph.api_storage.DEFAULT_REGISTRY = graph.root / 'another-registry'
            elif fault == 'activation': graph.activation.SOURCE_ROOT = graph.root / 'another-source'
            else: graph.contract.GUEST_ROOT = graph.root / 'another-guest'
            with graph.ports(), self.subTest(fault=fault):
                with self.assertRaises(tool.InspectionRefused): tool.inspect()
            graph.recovery.plan.assert_not_called(); self.assertFalse(graph.output.exists())

    def test_stale_input_bindings_or_changed_original_refuser_source_never_produce_a_plan(self):
        for fault in ('source', 'failure', 'static', 'build', 'apk', 'refuser', 'ledger'):
            graph = Graph()
            path = {'source': Path(graph.source_pins[0]['path']), 'failure': Path(graph.failure['path']),
                'static': Path(graph.static['path']), 'build': Path(graph.build_pin['path']),
                'apk': Path(graph.apks['test_apk']['path']), 'refuser': graph.source / 'benchmarks/native/deny_adb_client.c',
                'ledger': graph.ledger}[fault]
            raw = path.read_bytes()
            path.write_bytes(b'X' + raw[1:] if fault == 'ledger' else raw + b' changed')
            with graph.ports(), self.subTest(fault=fault):
                with self.assertRaises((env.EnvironmentRefused, tool.InspectionRefused)): tool.inspect()
            graph.recovery.plan.assert_not_called(); self.assertFalse(graph.output.exists())

    def test_existing_guest_parent_runtime_or_controls_is_never_adopted(self):
        for fault in ('guest_parent', 'guest', 'controls', 'runtime'):
            graph = Graph(); path = {'guest_parent': graph.guest.parent, 'guest': graph.guest,
                'controls': graph.activation.CONTROLS, 'runtime': graph.activation.RUNTIME}[fault]
            path.mkdir(parents=True); sentinel = path / 'preserve.bin'; sentinel.write_bytes(b'preserve tiny foreign fixture')
            with graph.ports(), self.subTest(fault=fault):
                with self.assertRaises(tool.InspectionRefused): tool.inspect()
            self.assertEqual(sentinel.read_bytes(), b'preserve tiny foreign fixture'); self.assertFalse(graph.output.exists())

    def test_changed_ledger_or_fresh_rebound_source_between_observations_cannot_complete(self):
        for fault in ('ledger', 'source', 'root'):
            graph = Graph()
            def change(index):
                if index != 2: return
                if fault == 'ledger': graph.ledger.write_bytes(b'changed isolated snapshot')
                elif fault == 'root': graph.guest.parent.mkdir()
                else:
                    path = Path(graph.source_pins[0]['path']); path.write_bytes(path.read_bytes() + b' rebound')
                    graph.source_pins[0] = env.binding(path)
            graph.on_git = change
            with graph.ports(), self.subTest(fault=fault):
                with self.assertRaises((env.EnvironmentRefused, tool.InspectionRefused)): tool.inspect()
            self.assertTrue(graph.output.is_dir()); self.assertFalse((graph.output / 'result-v1.json').exists())

    def test_recovery_plan_must_match_written_bytes_and_seven_frozen_source_bindings(self):
        for fault in ('mismatch', 'six', 'foreign', 'rebound'):
            graph = Graph(); graph.plan_sources = copy.deepcopy(graph.recovery_pins)
            if fault == 'mismatch': graph.plan_mismatch = True
            elif fault == 'six': graph.plan_sources.pop()
            elif fault == 'foreign': graph.plan_sources[0]['path'] = str(graph.root / 'foreign-source.py')
            else: graph.plan_sources[0]['sha256'] = '0' * 64
            with graph.ports(), self.subTest(fault=fault):
                with self.assertRaises((env.EnvironmentRefused, tool.InspectionRefused)): tool.inspect()
            self.assertFalse((graph.output / 'handoff-inputs-v1.json').exists()); self.assertFalse((graph.output / 'result-v1.json').exists())

    def test_each_initial_copy_is_read_back_before_its_new_binding_can_qualify_it(self):
        for name in ('b80-byte-attestation-v1.json', 'recovery-plan-v1.json', 'static-installed-inputs-v1.json', 'result-v1.json'):
            graph = Graph()
            graph.after_write = lambda actual, path, value: path.write_bytes(b'{}\n') if actual == name else None
            with graph.ports(), self.subTest(name=name):
                with self.assertRaises((env.EnvironmentRefused, tool.InspectionRefused)): tool.inspect()
            self.assertNotEqual(env.read_json(graph.output / name).get('status'), 'completed-file-only')

    def test_late_changed_generated_record_is_not_repaired_by_fresh_binding_observations(self):
        for name in ('b80-byte-attestation-v1.json', 'recovery-plan-v1.json', 'static-installed-inputs-v1.json', 'handoff-inputs-v1.json'):
            graph = Graph()
            graph.on_git = lambda index: (graph.output / name).write_bytes(b'{}\n') if index == 2 else None
            with graph.ports(), self.subTest(name=name):
                with self.assertRaises((env.EnvironmentRefused, tool.InspectionRefused)): tool.inspect()
            self.assertFalse((graph.output / 'result-v1.json').exists())

    def test_result_publication_cannot_mask_a_late_changed_handoff_or_attestation(self):
        for name in ('handoff-inputs-v1.json', 'b80-byte-attestation-v1.json'):
            graph = Graph()
            graph.after_write = lambda actual, path, value: (graph.output / name).write_bytes(b'{}\n') if actual == 'result-v1.json' else None
            with graph.ports(), self.subTest(name=name):
                with self.assertRaises((env.EnvironmentRefused, tool.InspectionRefused)): tool.inspect()
            self.assertTrue((graph.output / 'result-v1.json').exists())  # Preserved partial receipt never becomes a returned success.

    def test_partial_publication_is_preserved_and_reinspection_never_overwrites_or_retries(self):
        graph = Graph()
        def refuse(name, value):
            if name == 'handoff-inputs-v1.json': raise OSError('PRIVATE synthetic publication failure')
        graph.before_write = refuse; output = io.StringIO()
        with graph.ports(), redirect_stdout(output): self.assertEqual(tool.main(['inspect']), 1)
        refusal = json.loads(output.getvalue()); self.assertFalse(refusal['ready_for_execution']); self.assertNotIn('PRIVATE', output.getvalue())
        before = {p: p.read_bytes() for p in graph.output.iterdir()}
        self.assertEqual({p.name for p in before}, FILES - {'handoff-inputs-v1.json', 'result-v1.json'})
        graph.before_write = lambda name, value: None
        with graph.ports():
            with self.assertRaises(tool.InspectionRefused): tool.inspect()
        self.assertEqual({p: p.read_bytes() for p in graph.output.iterdir()}, before)
        self.assertEqual(graph.recovery.plan.call_count, 1)

    def test_completed_output_is_create_once_and_wrong_output_basename_is_not_a_new_destination(self):
        graph = Graph()
        with graph.ports(): tool.inspect()
        before = {p: p.read_bytes() for p in graph.output.iterdir()}
        with graph.ports():
            with self.assertRaises(tool.InspectionRefused): tool.inspect()
        self.assertEqual({p: p.read_bytes() for p in graph.output.iterdir()}, before)
        self.assertEqual(graph.recovery.plan.call_count, 1)
        fresh = Graph(); fresh.output = fresh.out / 'admission-v1'
        with fresh.ports():
            with self.assertRaises(tool.InspectionRefused): tool.inspect()
        self.assertFalse(fresh.output.exists()); fresh.recovery.plan.assert_not_called()


if __name__ == '__main__': unittest.main()
