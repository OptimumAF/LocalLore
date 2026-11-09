"""Original SDK13 fixed authority, constructor ordering and closure metadata oracles.

Synthetic files stay in the new D: authority capture; no SDK/native/socket call.
Build rejection is an explicitly simulated boundary, not product validation.
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
from benchmarks import android_process_profile_ui_client as client
from benchmarks import android_process_profile_ui_verification as verification
from benchmarks import owned_profile_ui_contract as contract
from benchmarks import owned_profile_ui_owner as owner
from benchmarks import owned_inventory_ui_contract as previous
from benchmarks import owned_inventory_ui_owner as previous_owner
from benchmarks import owned_target_contract as core
from benchmarks import owned_target_owner as mechanisms
from benchmarks import receipt_avd_retirement as retirement
from benchmarks import receipt_avd_storage as storage
from scripts.tests import test_owned_target_contract as legacy
from scripts.tests import test_presentation_process_runner_retirement as closure_data

PROTOCOL = 'owned-emulator-player-profile-chat-ui-v1'
SDK_PROTOCOL = 'sdk-player-profile-chat-ui-v1'
PROOF_PROTOCOL = 'player-profile-chat-ui-socket-proof-v1'
GUEST = 'D:/Dev/Experiments/LocalLore/2026-11-01-profile-ui-v1/avd-v1'
FIXTURES = Path('D:/Dev/Experiments/LocalLore/2026-11-01-profile-ui-harness-v1/authority-v1/fixtures')
SELECTORS = (('chat_ime_latest',
  'org.locallore.app.ui.ChatImeInsetsTest',
  'injectedImeKeepsLatestAboveOcclusionWithoutDoublePaddingSystemBars'),
 ('chat_ime_composer',
  'org.locallore.app.ui.ChatImeInsetsTest',
  'doubleFontComposerKeepsSendReachableAndDraftScopedAcrossInjectedImeChanges'),
 ('chat_status_history',
  'org.locallore.app.ui.ChatStatusAnnouncementTest',
  'historyReaderKeepsItsAnchorWhileCurrentBusyAndOutcomeAnnouncementsStayAvailable'),
 ('chat_status_draft',
  'org.locallore.app.ui.ChatStatusAnnouncementTest',
  'unicodeDialogueAndScopeStaySafeWhileEllipsizedNoticeKeepsFullSemantics'),
 ('chat_heading_selection',
  'org.locallore.app.ui.StoryHeadingScreenTest',
  'selectedAuthoredTitlesStayInsideTheIntroWhileDemoAndUnresolvedControlsRemainExact'),
 ('chat_heading_draft',
  'org.locallore.app.ui.StoryHeadingScreenTest',
  'titleRefreshRetainsDialogueButStoryAndBranchChangesFenceDraftsAndRetainedEdits'),
 ('chat_action_scope',
  'org.locallore.app.ui.QuickActionScopeScreenTest',
  'retainedStoryAndBranchClicksStayQuietWhileFreshControlsPreserveTheUnsentDialogue'),
 ('chat_action_availability',
  'org.locallore.app.ui.QuickActionScopeScreenTest',
  'persistentDemoAndWorkflowFencesDoNotTurnTextUnavailabilityIntoAnActionBlock'),
 ('inventory_entries',
  'org.locallore.app.ui.PlayerInventoryScreenTest',
  'savedRowsKnownEmptyAndUnavailableStayDistinctWhileDemoKeepsItsOriginalPotionRow'),
 ('inventory_scope',
  'org.locallore.app.ui.PlayerInventoryScreenTest',
  'scopeChangesFenceRetainedOpenAndCloseWhileAcceptedRefreshesKeepTheUnsentDialogue'),
 ('inventory_accessibility',
  'org.locallore.app.ui.PlayerInventoryScreenTest',
  'doubledFontKeepsLongExactIdentifiersAllQuantitiesAndCloseReachableWithoutGameActions'),
 ('profile_fields',
  'org.locallore.app.ui.PlayerSelfProfileScreenTest',
  'acceptedFieldsEmptyUnavailableAndNarrativeApplicabilityStaySeparateFromDemo'),
 ('profile_scope',
  'org.locallore.app.ui.PlayerSelfProfileScreenTest',
  'retainedInspectorCallbacksRespectScopesWorkflowClosureAndAcceptedRefreshWithoutSendingDraft'),
 ('profile_accessibility',
  'org.locallore.app.ui.PlayerSelfProfileScreenTest',
  'doubledFontKeepsFullUnicodeCollectionsAndCloseReachableWithoutCanonicalCallbacks'))
NEW_SOURCES = frozenset((
    'owned_profile_ui_contract.py', 'owned_profile_ui_owner.py',
    'android_process_profile_ui_client.py', 'android_process_profile_ui_verification.py',
    'profile_ui_build.py', 'profile_ui_controller.py', 'profile_ui_activation.py',
    'profile_ui_build_baseline.json', 'android_instrumentation_evidence.py',
))


def admission():
    value = legacy.admission()
    value['protocol'] = PROTOCOL
    value['guest']['root'] = GUEST
    value['artifacts'] = {key: value['artifacts'][key] for key in ('build', 'product_apk', 'test_apk')}
    value['sources'] = sorted([legacy.pin(PureWindowsPath('D:/Synthetic/LocalLore/benchmarks') / name)
                               for name in core.SOURCE_NAMES | NEW_SOURCES], key=lambda row: row['path'])
    names = {PureWindowsPath(row['path']).name: row for row in value['sources']}
    value['server']['sources'] = [copy.deepcopy(names[PureWindowsPath(row['path']).name])
                                  for row in value['server']['sources']]
    return value


def running(value):
    result = legacy.running(value)
    result['protocol'] = PROTOCOL
    return result


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


class ProfileUiAuthorityTests(unittest.TestCase):
    def test_fixed_sdk13_roster_and_closed_sources_validate_without_io_or_input_mutation(self):
        self.assertEqual((contract.PROTOCOL, contract.SDK_PROTOCOL, contract.PROOF_PROTOCOL),
                         (PROTOCOL, SDK_PROTOCOL, PROOF_PROTOCOL))
        self.assertEqual((contract.CLIENT_VERSION, contract.SESSION_FILE, contract.OWNER_SCRIPT,
                          contract.BOOT_CLAIM_FILE, contract.GUEST_ROOT),
                         (13, 'sdk-session-v13.json', 'owned_profile_ui_owner.py',
                          'owned-profile-ui-boot-claim-v1.json', PureWindowsPath(GUEST)))
        self.assertEqual(contract.INSTRUMENTATIONS, SELECTORS)
        self.assertEqual(contract.CLAIM_KINDS, tuple(row[0] for row in SELECTORS))
        self.assertEqual(len(set(contract.CLAIM_KINDS)), 14)
        self.assertEqual(contract.SOURCE_NAMES, core.SOURCE_NAMES | NEW_SOURCES)
        self.assertEqual(len(contract.SOURCE_NAMES), 24)
        self.assertEqual((contract.APP, contract.TEST, contract.MODEL_MATERIAL),
                         ('org.locallore.app', 'org.locallore.app.test', False))
        original = admission()
        with patch.object(Path, 'open', side_effect=AssertionError('metadata IO')), \
             patch.object(Path, 'stat', side_effect=AssertionError('metadata IO')):
            result = contract.validate_admission(original)
        self.assertEqual(result, original)
        result['guest']['cores'] = 99
        self.assertEqual(original['guest']['cores'], 4)

    def test_sdk12_guest_authority_artifacts_and_source_aliases_cannot_be_retagged(self):
        original = admission()
        changes = [lambda v: v.update(protocol=previous.PROTOCOL),
                   lambda v: v['guest'].update(root=str(previous.GUEST_ROOT)),
                   lambda v: v['artifacts'].update(model=legacy.pin('D:/Synthetic/model.task')),
                   lambda v: v['artifacts'].update(controller_apk=legacy.pin('D:/Synthetic/extra.apk')),
                   lambda v: v['sources'].pop(), lambda v: v['sources'].reverse(),
                   lambda v: v['sources'][0].update(path='D:/Foreign/benchmarks/adb_held_socket.py'),
                   lambda v: v.update(seconds=True), lambda v: v['server'].update(seconds=1201)]
        for change in changes:
            value = copy.deepcopy(original); change(value)
            with self.subTest(change=change), self.assertRaises(core.TargetRefused):
                contract.validate_admission(value)
        with self.assertRaises(core.TargetRefused): previous.validate_admission(original)
        old = copy.deepcopy(original)
        old.update(protocol=previous.PROTOCOL)
        old['guest']['root'] = str(previous.GUEST_ROOT)
        for row in old['sources']:
            name = PureWindowsPath(row['path']).name
            if name in NEW_SOURCES and name != 'android_instrumentation_evidence.py':
                row['path'] = str(PureWindowsPath(row['path']).with_name(name.replace('profile_ui', 'inventory_ui')))
        old['sources'].sort(key=lambda row: row['path'])
        self.assertEqual(previous.validate_admission(old), old)

    def test_all_fourteen_operations_accept_only_the_literal_single_method_vector(self):
        a = admission()
        for row in SELECTORS:
            operation = dict(argv=instrument(row), stdin=None)
            self.assertEqual(contract.instrumentation_kind(operation['argv']), row[0])
            self.assertEqual(contract.validate_operation(operation, a), operation)
        good = instrument(SELECTORS[-1])
        invalid = [good + ['--user', '0'], good[:6] + [good[6] + ',other'] + good[7:],
                   good[:6] + ['org.locallore.app.ui.ForeignTest#other'] + good[7:],
                   ['run-as', contract.APP, 'cat', 'files/private'], ['pidof', contract.APP],
                   ['am', 'force-stop', '--user', '0', contract.APP], ['sh', '-c', 'echo command'],
                   ['screencap', '-p'], ['df', '-k', '/data']]
        for argv in invalid:
            with self.subTest(argv=argv), self.assertRaises(core.TargetRefused):
                contract.validate_operation(dict(argv=argv, stdin=None), a)
        with self.assertRaises(core.TargetRefused):
            contract.validate_operation(dict(argv=good, stdin=legacy.pin('D:/Synthetic/input.bin')), a)

    def test_session_and_raw_proof_cannot_borrow_old_protocol_or_session_filename(self):
        a = admission(); s = session(a)
        self.assertEqual(contract.validate_session(s, a), s)
        p = legacy.proof(s)
        p.update(protocol=PROOF_PROTOCOL, session=legacy.pin(PureWindowsPath(s['root']) / 'sdk-session-v13.json'))
        self.assertEqual(contract.validate_proof(p, s, p['context']), p)
        for part in ('session', 'owner', 'proof', 'filename'):
            other_s, other_p = copy.deepcopy(s), copy.deepcopy(p)
            if part == 'session': other_s['protocol'] = previous.SDK_PROTOCOL
            elif part == 'owner': other_s['descriptor']['protocol'] = previous.PROTOCOL
            elif part == 'proof': other_p['protocol'] = previous.PROOF_PROTOCOL
            else: other_p['session']['path'] = str(PureWindowsPath(s['root']) / 'sdk-session-v12.json')
            with self.subTest(part=part), self.assertRaises(core.TargetRefused):
                contract.validate_session(other_s, a)
                contract.validate_proof(other_p, other_s, other_p['context'])

    def test_running_identity_clock_port_and_source_drift_are_not_ready_authority(self):
        a = admission(); d = running(a)
        self.assertEqual(contract.validate_running(d, a, d['admission']), d)
        changes = [lambda v: v['owner'].update(pid=v['worker']['pid']),
                   lambda v: v['guest'].update(creation_filetime=True),
                   lambda v: v.update(deadline_epoch=v['deadline_epoch'] + 1),
                   lambda v: v.update(sdk_port=5037),
                   lambda v: v['sources'][0].update(sha256='0' * 64),
                   lambda v: v['guest_ancestry'].reverse()]
        for change in changes:
            value = copy.deepcopy(d); change(value)
            with self.subTest(change=change), self.assertRaises(core.TargetRefused):
                contract.validate_running(value, a, d['admission'])

    def test_claims_bind_exact_caller_kind_admission_and_operation_digest(self):
        a = admission(); d = running(a); caller = d['worker']; admitted = d['admission']
        for row in SELECTORS:
            digest = contract.operation_digest(dict(argv=instrument(row), stdin=None))
            claim = contract.claim_record(admitted, caller, row[0], digest)
            self.assertEqual(contract.validate_claim(claim, admitted, caller, row[0], digest), claim)
            for change in (dict(protocol=previous.PROTOCOL), dict(kind='unselected'),
                           dict(admission_sha256='0' * 64), dict(operation_sha256='f' * 64),
                           dict(caller=dict(caller, creation_filetime=caller['creation_filetime'] + 1)),
                           dict(prerequisite=None)):
                with self.subTest(row=row[0], change=change), self.assertRaises(core.TargetRefused):
                    contract.validate_claim(dict(claim, **change), admitted, caller, row[0], digest)

    def test_qualified_client_requires_every_cleanup_bit_but_partial_failure_remains_partial(self):
        s = session(admission()); record = legacy.GuestAndRecordTests().record()
        record.update(version=13, protocol=SDK_PROTOCOL, session=legacy.pin(PureWindowsPath(s['root']) / 'sdk-session-v13.json'))
        self.assertEqual(contract.validate_client_record(record, s), record)
        for key, bad in [('returncode', 1), ('version', 12), ('protocol', previous.SDK_PROTOCOL),
                         ('cleanup_complete', False), ('socket_closed', False), ('sender_joined', False),
                         ('input_closed', False), ('server_after', None), ('client_qualified', 1)]:
            value = copy.deepcopy(record); value[key] = bad
            with self.subTest(key=key), self.assertRaises(core.TargetRefused):
                contract.validate_client_record(value, s)
        partial = dict(record, client_qualified=False, cleanup_complete=False, socket_closed=False,
                       status='cancelled', returncode=None, server_after=None)
        self.assertEqual(contract.validate_client_record(partial, s), partial)
        self.assertIs(partial['client_qualified'], False)

    def test_stop_is_typed_profile_and_admission_bound_without_process_selectors(self):
        stop = dict(version=1, protocol=PROTOCOL, admission_sha256='a' * 64, action='stop')
        self.assertIsNone(contract.check_stop(stop, 'a' * 64))
        for change in (dict(protocol=previous.PROTOCOL), dict(action='kill'), dict(pid=9100),
                       dict(version=True), dict(admission_sha256='b' * 64)):
            with self.subTest(change=change), self.assertRaises(core.TargetRefused):
                contract.check_stop(dict(stop, **change), 'a' * 64)


@unittest.skipUnless(os.name == 'nt', 'Tiny physical D bound-file constructor metadata')
class ProfileUiConstructorTests(unittest.TestCase):
    def setUp(self):
        self.root = scratch(); self.value = admission(); self.path = self.root / 'admission.json'
        wire.environment.create_json(self.path, self.value); self.pin = wire.environment.binding(self.path)

    def test_product_rejection_precedes_live_runtime_native_and_parent_dispatch(self):
        fake = types.ModuleType('benchmarks.profile_ui_build'); seen = []
        def refuse(value):
            contract.validate_admission(value); seen.append(copy.deepcopy(value))
            raise ValueError('synthetic product refused')
        fake.verify_current = refuse
        with patch.dict('sys.modules', {'benchmarks.profile_ui_build': fake}), \
             patch.object(mechanisms._LiveOwnedTarget, '__init__', side_effect=AssertionError('native live')) as live, \
             patch.object(mechanisms._TargetRuntimeCore, '__init__', side_effect=AssertionError('native worker')) as worker, \
             patch.object(mechanisms, '_parent', side_effect=AssertionError('owner dispatch')) as parent:
            with self.assertRaisesRegex(ValueError, 'synthetic product refused'):
                owner.LiveOwnedProfileUiTarget(self.pin, self.pin)
            with self.assertRaisesRegex(ValueError, 'synthetic product refused'):
                owner._ProfileUiTargetRuntime(dict(validated_admission=self.value), self.pin, self.root)
            with redirect_stdout(io.StringIO()):
                self.assertEqual(owner.main(['--admission', self.pin['path'], '--admission-sha256', self.pin['sha256']]), 1)
            live.assert_not_called(); worker.assert_not_called(); parent.assert_not_called()
        self.assertEqual(seen, [self.value] * 3)

    def test_concrete_client_and_owner_types_refuse_subclasses_old_lease_and_foreign_cli_hooks(self):
        class OtherLive(owner.LiveOwnedProfileUiTarget): pass
        class OtherRuntime(owner._ProfileUiTargetRuntime): pass
        class OtherCapture(client.OwnedProfileUiSdkCapture): pass
        with patch.object(owner, '_verify_build', side_effect=AssertionError('subclass build')) as gate:
            with self.assertRaises(owner.OwnerRefused): OtherLive(self.pin, self.pin)
            with self.assertRaises(owner.OwnerRefused): OtherRuntime({}, self.pin, self.root)
            gate.assert_not_called()
        old_lease = object.__new__(previous_owner.LiveOwnedInventoryUiTarget)
        with patch.object(mechanisms._LiveOwnedTarget, 'guard', side_effect=AssertionError('foreign lease guard')) as guard, \
             patch.object(wire.socket, 'socket', side_effect=AssertionError('socket')) as sock:
            with self.assertRaises(client.ClientRefused): client.OwnedProfileUiSdkCapture(self.root / 'clients', 1200, old_lease)
            with self.assertRaises(client.ClientRefused): OtherCapture(self.root / 'clients', 1200, old_lease)
            guard.assert_not_called(); sock.assert_not_called()
        with patch.object(mechanisms, '_main_profile', return_value=31) as main:
            self.assertEqual(owner.main(['synthetic']), 31)
            _, options = main.call_args
            self.assertIs(options['_contract'], contract)
            self.assertIs(options['_verification'], verification)
            self.assertIs(options['_runtime_type'], owner._ProfileUiTargetRuntime)
            self.assertIs(options['_admission_check'], owner._verify_build)

    def test_expanded_admission_refuses_before_even_the_mocked_build_gate(self):
        value = copy.deepcopy(self.value); value['artifacts']['model'] = legacy.pin('D:/Synthetic/model.task')
        path = self.root / 'expanded.json'; wire.environment.create_json(path, value)
        with patch.object(owner, '_verify_build', side_effect=AssertionError('model reached build')) as gate:
            with self.assertRaises(core.TargetRefused):
                owner.LiveOwnedProfileUiTarget(wire.environment.binding(path), self.pin)
            gate.assert_not_called()


@unittest.skipUnless(os.name == 'nt', 'Tiny physical D closure proof files only')
class ProfileUiClosureTests(unittest.TestCase):
    def fixture(self, change=None):
        directory = scratch(); original = tempfile.mkdtemp
        def owned(*args, **kwargs):
            kwargs['dir'] = directory
            return original(*args, **kwargs)
        with patch.object(closure_data.tempfile, 'mkdtemp', owned):
            return closure_data.ClosureFiles(PROTOCOL, change=change)

    def extract(self, fixture):
        with ExitStack() as stack:
            mocks = [stack.enter_context(patch.object(module, name, side_effect=AssertionError('lifecycle operation')))
                     for module, name in ((retirement.windows, '_WindowsApi'), (retirement.windows, 'WindowsImageSet'),
                         (retirement.windows, 'closed_processes'), (storage, 'reserve_prepare'),
                         (storage, 'plan_retirement'), (storage, 'record_retired'))]
            try: return retirement._closure(fixture.entry)
            finally:
                for mocked in mocks: mocked.assert_not_called()

    def test_qualified_sdk13_closure_metadata_preserves_five_identities(self):
        fixture = self.fixture()
        try: result = self.extract(fixture)
        except retirement.RetirementRefused as error:
            self.fail('Coherent SDK13 closure metadata refused: ' + error.reason)
        self.assertEqual(result, fixture.identities)
        self.assertEqual(len(result), 5)
        self.assertEqual(set(fixture.proofs['worker_result']['cleanup']), set(contract.CLEANUP_KEYS))
        self.assertEqual(len(contract.CLEANUP_KEYS), 15)
        self.assertFalse((fixture.base / 'ledger-v1.json').exists())
        self.assertFalse((fixture.base / 'admission.lock').exists())

    def test_mixed_profile_unknown_cleanup_or_unclosed_owner_cannot_borrow_qualification(self):
        changes = [lambda p: p['worker_result'].update(protocol=previous.PROTOCOL),
                   lambda p: p['after'].update(process_handles_closed=False),
                   lambda p: p['owner_result'].update(output_capture_complete=False),
                   lambda p: p['worker_result']['cleanup'].update(unknown=True)]
        for key in contract.CLEANUP_KEYS:
            changes.extend([lambda p, k=key: p['worker_result']['cleanup'].pop(k),
                            lambda p, k=key: p['worker_result']['cleanup'].update({k: False}),
                            lambda p, k=key: p['worker_result']['cleanup'].update({k: 1})])
        for index, change in enumerate(changes):
            with self.subTest(index=index), self.assertRaises(retirement.RetirementRefused):
                self.extract(self.fixture(change))


if __name__ == '__main__':
    unittest.main()
