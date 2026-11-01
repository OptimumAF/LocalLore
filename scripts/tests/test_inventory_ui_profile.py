"""Independent SDK12 authority/ordering and closure metadata host oracles.

Only tiny synthetic D: files are written. Native, sockets, SDK execution,
registry transitions and image operations are traps, never qualifications.
Copyright 2026 LocalLore contributors. SPDX-License-Identifier: Apache-2.0
"""
import copy
from contextlib import ExitStack, redirect_stdout
import io
import os
from pathlib import Path, PureWindowsPath
import tempfile
import types
import unittest
from unittest.mock import patch

from benchmarks import android_process_client_v4 as wire
from benchmarks import android_process_inventory_ui_client as client
from benchmarks import android_process_inventory_ui_verification as verification
from benchmarks import owned_inventory_ui_contract as contract
from benchmarks import owned_inventory_ui_owner as owner
from benchmarks import owned_chat_ui_contract as previous
from benchmarks import owned_chat_ui_owner as previous_owner
from benchmarks import owned_target_contract as core
from benchmarks import owned_target_owner as mechanisms
from benchmarks import receipt_avd_retirement as retirement
from benchmarks import receipt_avd_storage as storage
from scripts.tests import test_owned_target_contract as legacy
from scripts.tests import test_presentation_process_runner_retirement as closure_data

PROTOCOL = 'owned-emulator-player-inventory-chat-ui-v1'
SDK_PROTOCOL = 'sdk-player-inventory-chat-ui-v1'
PROOF_PROTOCOL = 'player-inventory-chat-ui-socket-proof-v1'
GUEST = 'D:/Dev/Experiments/LocalLore/2026-11-01-inventory-ui-v1/avd-v1'
FIXTURES = Path('D:/Dev/Experiments/LocalLore/2026-11-01-inventory-ui-host-fixtures-v1/profile')
SELECTORS = (
    ('chat_ime_latest', 'org.locallore.app.ui.ChatImeInsetsTest',
     'injectedImeKeepsLatestAboveOcclusionWithoutDoublePaddingSystemBars'),
    ('chat_ime_composer', 'org.locallore.app.ui.ChatImeInsetsTest',
     'doubleFontComposerKeepsSendReachableAndDraftScopedAcrossInjectedImeChanges'),
    ('chat_status_history', 'org.locallore.app.ui.ChatStatusAnnouncementTest',
     'historyReaderKeepsItsAnchorWhileCurrentBusyAndOutcomeAnnouncementsStayAvailable'),
    ('chat_status_draft', 'org.locallore.app.ui.ChatStatusAnnouncementTest',
     'unicodeDialogueAndScopeStaySafeWhileEllipsizedNoticeKeepsFullSemantics'),
    ('chat_heading_selection', 'org.locallore.app.ui.StoryHeadingScreenTest',
     'selectedAuthoredTitlesStayInsideTheIntroWhileDemoAndUnresolvedControlsRemainExact'),
    ('chat_heading_draft', 'org.locallore.app.ui.StoryHeadingScreenTest',
     'titleRefreshRetainsDialogueButStoryAndBranchChangesFenceDraftsAndRetainedEdits'),
    ('chat_action_scope', 'org.locallore.app.ui.QuickActionScopeScreenTest',
     'retainedStoryAndBranchClicksStayQuietWhileFreshControlsPreserveTheUnsentDialogue'),
    ('chat_action_availability', 'org.locallore.app.ui.QuickActionScopeScreenTest',
     'persistentDemoAndWorkflowFencesDoNotTurnTextUnavailabilityIntoAnActionBlock'),
    ('inventory_entries', 'org.locallore.app.ui.PlayerInventoryScreenTest',
     'savedRowsKnownEmptyAndUnavailableStayDistinctWhileDemoKeepsItsOriginalPotionRow'),
    ('inventory_scope', 'org.locallore.app.ui.PlayerInventoryScreenTest',
     'scopeChangesFenceRetainedOpenAndCloseWhileAcceptedRefreshesKeepTheUnsentDialogue'),
    ('inventory_accessibility', 'org.locallore.app.ui.PlayerInventoryScreenTest',
     'doubledFontKeepsLongExactIdentifiersAllQuantitiesAndCloseReachableWithoutGameActions'),
)
NEW_SOURCES = frozenset((
    'owned_inventory_ui_contract.py', 'owned_inventory_ui_owner.py',
    'android_process_inventory_ui_client.py', 'android_process_inventory_ui_verification.py',
    'inventory_ui_build.py', 'inventory_ui_controller.py', 'inventory_ui_activation.py',
    'inventory_ui_build_baseline.json', 'android_instrumentation_evidence.py',
))


def admission():
    value = legacy.admission()
    value['protocol'] = PROTOCOL
    value['guest']['root'] = GUEST
    value['artifacts'] = {role: value['artifacts'][role]
                          for role in ('build', 'product_apk', 'test_apk')}
    value['sources'] = sorted([
        legacy.pin(PureWindowsPath('D:/Synthetic/LocalLore/benchmarks') / name)
        for name in core.SOURCE_NAMES | NEW_SOURCES], key=lambda pin: pin['path'])
    names = {PureWindowsPath(pin['path']).name: pin for pin in value['sources']}
    value['server']['sources'] = [copy.deepcopy(names[PureWindowsPath(pin['path']).name])
                                  for pin in value['server']['sources']]
    return value


def running(value):
    descriptor = legacy.running(value)
    descriptor['protocol'] = PROTOCOL
    return descriptor


def session(value):
    result = legacy.session(value)
    result['protocol'] = SDK_PROTOCOL
    result['descriptor']['protocol'] = PROTOCOL
    return result


def instrument(row):
    return ['am', 'instrument', '-w', '-r', '-e', 'class', row[1] + '#' + row[2],
            'org.locallore.app.test/androidx.test.runner.AndroidJUnitRunner']


def scratch():
    FIXTURES.mkdir(parents=True, exist_ok=True)
    return Path(tempfile.mkdtemp(prefix='case-', dir=FIXTURES))


class InventoryUiAuthorityTests(unittest.TestCase):
    def test_exact_sdk12_source_closed_roster_is_pure_and_detached(self):
        self.assertEqual((contract.PROTOCOL, contract.SDK_PROTOCOL, contract.PROOF_PROTOCOL),
                         (PROTOCOL, SDK_PROTOCOL, PROOF_PROTOCOL))
        self.assertEqual((contract.CLIENT_VERSION, contract.SESSION_FILE, contract.OWNER_SCRIPT,
                          contract.BOOT_CLAIM_FILE),
                         (12, 'sdk-session-v12.json', 'owned_inventory_ui_owner.py', 'owned-inventory-ui-boot-claim-v1.json'))
        self.assertEqual(contract.GUEST_ROOT, PureWindowsPath(GUEST))
        self.assertEqual((contract.APP, contract.TEST, contract.MODEL_MATERIAL),
                         ('org.locallore.app', 'org.locallore.app.test', False))
        self.assertEqual(contract.ARTIFACT_KEYS, frozenset(('build', 'product_apk', 'test_apk')))
        self.assertEqual(contract.SOURCE_NAMES, core.SOURCE_NAMES | NEW_SOURCES)
        self.assertEqual(len(contract.SOURCE_NAMES), 24)
        self.assertEqual(contract.INSTRUMENTATIONS, SELECTORS)
        value = admission()
        original = copy.deepcopy(value)
        with patch.object(Path, 'open', side_effect=AssertionError('metadata caused IO')):
            result = contract.validate_admission(value)
        self.assertEqual(result, original)
        result['sources'][0]['sha256'] = 'f' * 64
        self.assertEqual(value, original)

    def test_old_authority_and_changed_baseline_or_artifact_roles_cannot_retag(self):
        original = admission()
        for kind in ('protocol', 'guest', 'baseline', 'old_source', 'model', 'extra_apk', 'bool'):
            value = copy.deepcopy(original)
            if kind == 'protocol': value['protocol'] = previous.PROTOCOL
            elif kind == 'guest': value['guest']['root'] = str(previous.GUEST_ROOT)
            elif kind in ('baseline', 'old_source'):
                pin = next(p for p in value['sources'] if PureWindowsPath(p['path']).name == 'inventory_ui_build_baseline.json')
                if kind == 'baseline': value['sources'].remove(pin)
                else: pin['path'] = str(PureWindowsPath(pin['path']).with_name('chat_ui_build.py'))
            elif kind == 'bool': value['seconds'] = True
            else: value['artifacts'][kind] = legacy.pin('D:/Synthetic/extra.bin')
            with self.subTest(kind=kind), self.assertRaises(core.TargetRefused):
                contract.validate_admission(value)
        with self.assertRaises(core.TargetRefused):
            previous.validate_admission(original)

    def test_all_eleven_commands_are_fixed_one_method_vectors_without_general_shell(self):
        value = admission()
        for row in SELECTORS:
            argv = instrument(row)
            self.assertEqual(contract.instrumentation_kind(argv), row[0])
            self.assertEqual(contract.validate_operation(dict(argv=argv, stdin=None), value), dict(argv=argv, stdin=None))
        wrong = instrument(SELECTORS[-1])
        vectors = [wrong[:6] + [wrong[6] + ',other'] + wrong[7:],
                   wrong[:6] + ['org.locallore.app.ui.ForeignTest#unselected'] + wrong[7:],
                   wrong + ['--user', '0'], ['pidof', contract.APP],
                   ['am', 'force-stop', '--user', '0', contract.APP],
                   ['run-as', contract.APP, '--user', '0', 'cat', 'files/private'],
                   ['sh', '-c', 'echo unselected'], ['screencap', '-p'], ['df', '-k', '/data']]
        for argv in vectors:
            with self.subTest(argv=argv), self.assertRaises(core.TargetRefused):
                contract.validate_operation(dict(argv=argv, stdin=None), value)

    def test_sdk11_session_or_proof_cannot_be_renamed_to_sdk12(self):
        value = admission()
        current = session(value)
        self.assertEqual(contract.validate_session(current, value), current)
        proof = legacy.proof(current)
        proof.update(protocol=PROOF_PROTOCOL,
                     session=legacy.pin(PureWindowsPath(current['root']) / 'sdk-session-v12.json'))
        contract.validate_proof(proof, current, proof['context'])
        for which in ('sdk', 'owner', 'proof', 'session_path'):
            s, p = copy.deepcopy(current), copy.deepcopy(proof)
            if which == 'sdk': s['protocol'] = previous.SDK_PROTOCOL
            elif which == 'owner': s['descriptor']['protocol'] = previous.PROTOCOL
            elif which == 'proof': p['protocol'] = previous.PROOF_PROTOCOL
            else: p['session']['path'] = str(PureWindowsPath(current['root']) / 'sdk-session-v11.json')
            with self.subTest(which=which), self.assertRaises(core.TargetRefused):
                contract.validate_session(s, value)
                contract.validate_proof(p, s, p['context'])


@unittest.skipUnless(os.name == 'nt', 'Owned tiny D files; no native constructor')
class InventoryUiConstructorTests(unittest.TestCase):
    def setUp(self):
        self.root = scratch()
        self.value = admission()
        self.path = self.root / 'admission.json'
        wire.environment.create_json(self.path, self.value)
        self.pin = wire.environment.binding(self.path)

    def test_explicit_product_failure_precedes_every_native_or_parent_entry(self):
        fake = types.ModuleType('benchmarks.inventory_ui_build')
        seen = []
        def refuse(value):
            contract.validate_admission(value)
            seen.append(copy.deepcopy(value))
            raise ValueError('synthetic product boundary refusal')
        fake.verify_current = refuse
        with patch.dict('sys.modules', {'benchmarks.inventory_ui_build': fake}), \
             patch.object(mechanisms._LiveOwnedTarget, '__init__', side_effect=AssertionError('native live')) as live, \
             patch.object(mechanisms._TargetRuntimeCore, '__init__', side_effect=AssertionError('native worker')) as worker, \
             patch.object(mechanisms, '_parent', side_effect=AssertionError('parent dispatch')) as parent:
            with self.assertRaisesRegex(ValueError, 'product boundary refusal'):
                owner.LiveOwnedInventoryUiTarget(self.pin, self.pin)
            with self.assertRaisesRegex(ValueError, 'product boundary refusal'):
                owner._InventoryUiTargetRuntime(dict(validated_admission=self.value), self.pin, self.root)
            with redirect_stdout(io.StringIO()):
                self.assertEqual(owner.main(['--admission', self.pin['path'], '--admission-sha256', self.pin['sha256']]), 1)
            live.assert_not_called(); worker.assert_not_called(); parent.assert_not_called()
        self.assertEqual(seen, [self.value, self.value, self.value])

    def test_concrete_types_and_cli_hooks_cannot_select_another_profile(self):
        class DerivedLive(owner.LiveOwnedInventoryUiTarget): pass
        class DerivedRuntime(owner._InventoryUiTargetRuntime): pass
        class DerivedCapture(client.OwnedInventoryUiSdkCapture): pass
        with patch.object(owner, '_verify_build', side_effect=AssertionError('subclass reached build')) as gate:
            with self.assertRaises(owner.OwnerRefused): DerivedLive(self.pin, self.pin)
            with self.assertRaises(owner.OwnerRefused): DerivedRuntime({}, self.pin, self.root)
            gate.assert_not_called()
        old = object.__new__(previous_owner.LiveOwnedChatUiTarget)
        with patch.object(mechanisms._LiveOwnedTarget, 'guard', side_effect=AssertionError('wrong lease guard')) as guard, \
             patch.object(wire.socket, 'socket', side_effect=AssertionError('socket')) as sock:
            with self.assertRaises(client.ClientRefused): client.OwnedInventoryUiSdkCapture(self.root / 'clients', 1200, old)
            with self.assertRaises(client.ClientRefused): DerivedCapture(self.root / 'clients', 1200, old)
            guard.assert_not_called(); sock.assert_not_called()
        with patch.object(mechanisms, '_main_profile', return_value=29) as main:
            self.assertEqual(owner.main(['synthetic']), 29)
            _, options = main.call_args
            self.assertIs(options['_contract'], contract)
            self.assertIs(options['_verification'], verification)
            self.assertIs(options['_runtime_type'], owner._InventoryUiTargetRuntime)
            self.assertIs(options['_admission_check'], owner._verify_build)

    def test_extra_model_is_rejected_before_even_the_product_boundary(self):
        value = copy.deepcopy(self.value)
        value['artifacts']['model'] = legacy.pin('D:/Synthetic/not-authorized.task')
        path = self.root / 'expanded.json'
        wire.environment.create_json(path, value)
        with patch.object(owner, '_verify_build', side_effect=AssertionError('expanded admission reached build')) as gate:
            with self.assertRaises(core.TargetRefused):
                owner.LiveOwnedInventoryUiTarget(wire.environment.binding(path), self.pin)
            gate.assert_not_called()


@unittest.skipUnless(os.name == 'nt', 'Tiny bound closure JSON only')
class InventoryUiClosureMetadataTests(unittest.TestCase):
    def fixture(self, protocol, change=None):
        parent = scratch()
        original = tempfile.mkdtemp
        def owned(*args, **kwargs):
            kwargs['dir'] = parent
            return original(*args, **kwargs)
        with patch.object(closure_data.tempfile, 'mkdtemp', owned):
            return closure_data.ClosureFiles(protocol, change=change)

    def extract(self, value):
        with ExitStack() as stack:
            traps = [stack.enter_context(patch.object(module, name, side_effect=AssertionError('lifecycle operation')))
                     for module, name in ((retirement.windows, '_WindowsApi'), (retirement.windows, 'WindowsImageSet'),
                         (retirement.windows, 'closed_processes'), (storage, 'reserve_prepare'),
                         (storage, 'plan_retirement'), (storage, 'record_retired'))]
            try: return retirement._closure(value.entry)
            finally:
                for trap in traps: trap.assert_not_called()

    def test_exact_sdk12_closed_identity_metadata_accepts_without_lifecycle_operations(self):
        value = self.fixture(PROTOCOL)
        self.assertEqual(self.extract(value), value.identities)
        self.assertEqual(len(value.identities), 5)
        self.assertEqual(len(contract.CLEANUP_KEYS), 15)
        self.assertFalse((value.base / 'ledger-v1.json').exists())
        self.assertFalse((value.base / 'admission.lock').exists())

    def test_mixed_unknown_or_incomplete_cleanup_cannot_borrow_sdk12_closure(self):
        for protocol in (PROTOCOL + '-extra', 'owned-emulator-not-authorized-v1'):
            with self.subTest(protocol=protocol), self.assertRaises(retirement.RetirementRefused):
                self.extract(self.fixture(protocol))
        for admission_protocol, worker_protocol in ((PROTOCOL, previous.PROTOCOL), (previous.PROTOCOL, PROTOCOL)):
            def change(proofs):
                proofs['admission']['protocol'] = admission_protocol
                proofs['worker_result']['protocol'] = worker_protocol
            with self.subTest(admission=admission_protocol, worker=worker_protocol), self.assertRaises(retirement.RetirementRefused):
                self.extract(self.fixture(PROTOCOL, change))
        for key in contract.CLEANUP_KEYS:
            with self.subTest(cleanup=key), self.assertRaises(retirement.RetirementRefused):
                self.extract(self.fixture(PROTOCOL, lambda proofs, k=key: proofs['worker_result']['cleanup'].update({k: False})))


if __name__ == '__main__':
    unittest.main()
