"""SDK11 original closed-authority and byte-replay adversaries using synthetic IO only.

No guest, installed SDK, native ownership, credentials or real socket is exercised.
Copyright 2026 LocalLore contributors. SPDX-License-Identifier: Apache-2.0
"""
import copy
from contextlib import redirect_stdout
import io
import os
from pathlib import Path, PureWindowsPath
import tempfile
import threading
import types
import unittest
from unittest.mock import Mock, patch

from benchmarks import owned_chat_ui_contract as contract
from benchmarks import owned_chat_ui_owner as owner
from benchmarks import android_process_chat_ui_client as client
from benchmarks import android_process_chat_ui_verification as replay
from benchmarks import owned_target_contract as core
from benchmarks import owned_target_owner as mechanisms
from benchmarks import android_process_client_v4 as wire
from benchmarks import owned_transcript_ui_contract as previous
from benchmarks import owned_transcript_ui_owner as previous_owner
from benchmarks import android_process_transcript_ui_verification as previous_replay
from scripts.tests import test_owned_target_contract as legacy
from scripts.tests import test_android_process_client_v4 as framing
from scripts.tests import test_transcript_ui_profile as previous_fixture

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
)
EXTRA_SOURCES = frozenset(('owned_chat_ui_contract.py', 'owned_chat_ui_owner.py',
    'android_process_chat_ui_client.py', 'android_process_chat_ui_verification.py',
    'chat_ui_build.py', 'chat_ui_controller.py', 'chat_ui_activation.py', 'android_instrumentation_evidence.py'))
FIXTURES = Path('D:/Dev/Experiments/LocalLore/2026-11-01-current-chat-host-fixtures-v1/profile')


def admission():
    value = legacy.admission()
    value['protocol'] = 'owned-emulator-current-chat-ui-v1'
    value['guest']['root'] = 'D:/Dev/Experiments/LocalLore/2026-11-01-current-chat-ui-v1/avd-v1'
    value['artifacts'] = {key: value['artifacts'][key] for key in ('build', 'product_apk', 'test_apk')}
    value['sources'] = sorted([legacy.pin(PureWindowsPath('D:/Synthetic/LocalLore/benchmarks') / name)
        for name in core.SOURCE_NAMES | EXTRA_SOURCES], key=lambda row: row['path'])
    by_name = {PureWindowsPath(row['path']).name: row for row in value['sources']}
    value['server']['sources'] = [copy.deepcopy(by_name[PureWindowsPath(row['path']).name])
        for row in value['server']['sources']]
    return value


def running(value):
    result = legacy.running(value)
    result['protocol'] = 'owned-emulator-current-chat-ui-v1'
    return result


def session(value):
    result = legacy.session(value)
    result['protocol'] = 'sdk-current-chat-ui-v1'
    result['descriptor']['protocol'] = 'owned-emulator-current-chat-ui-v1'
    return result


def instrument(row):
    return ['am', 'instrument', '-w', '-r', '-e', 'class', row[1] + '#' + row[2],
        'org.locallore.app.test/androidx.test.runner.AndroidJUnitRunner']


def scratch():
    FIXTURES.mkdir(parents=True, exist_ok=True)
    return Path(tempfile.mkdtemp(prefix='case-', dir=FIXTURES))


class ChatUiAuthorityTests(unittest.TestCase):
    def test_profile_is_exact_sdk11_and_admission_is_pure_detached_metadata(self):
        self.assertEqual((contract.PROTOCOL, contract.SDK_PROTOCOL, contract.PROOF_PROTOCOL),
            ('owned-emulator-current-chat-ui-v1', 'sdk-current-chat-ui-v1', 'current-chat-ui-socket-proof-v1'))
        self.assertEqual((contract.CLIENT_VERSION, contract.SESSION_FILE, contract.OWNER_SCRIPT, contract.BOOT_CLAIM_FILE),
            (11, 'sdk-session-v11.json', 'owned_chat_ui_owner.py', 'owned-chat-ui-boot-claim-v1.json'))
        self.assertEqual((contract.APP, contract.TEST, contract.MODEL_MATERIAL),
            ('org.locallore.app', 'org.locallore.app.test', False))
        self.assertEqual(contract.INSTRUMENTATIONS, SELECTORS)
        self.assertEqual(contract.CLAIM_KINDS, tuple(row[0] for row in SELECTORS))
        self.assertEqual(contract.ARTIFACT_KEYS, frozenset(('build', 'product_apk', 'test_apk')))
        self.assertEqual(contract.SOURCE_NAMES, core.SOURCE_NAMES | EXTRA_SOURCES)
        value = admission()
        before = copy.deepcopy(value)
        with patch.object(Path, 'open', side_effect=AssertionError('schema must not open files')), \
             patch.object(Path, 'stat', side_effect=AssertionError('schema must not query paths')):
            result = contract.validate_admission(value)
        self.assertEqual(result, before)
        result['sources'].clear()
        result['guest']['memory_mib'] = 1
        self.assertEqual(value, before)

    def test_previous_profile_root_and_protocol_are_not_current_authority(self):
        old = previous_fixture.admission()
        previous.validate_admission(old)
        with self.assertRaises(core.TargetRefused): contract.validate_admission(old)
        current = admission()
        contract.validate_admission(current)
        with self.assertRaises(core.TargetRefused): previous.validate_admission(current)
        for field, replacement in [('protocol', previous.PROTOCOL), ('guest_root', str(previous.GUEST_ROOT))]:
            changed = copy.deepcopy(current)
            if field == 'guest_root': changed['guest']['root'] = replacement
            else: changed[field] = replacement
            with self.subTest(field=field), self.assertRaises(core.TargetRefused): contract.validate_admission(changed)

    def test_source_omission_retag_extra_artifact_and_bool_budget_are_refused(self):
        for mutation in ['missing_activation', 'retag_build', 'extra_model', 'extra_probe', 'extra_controller',
                         'caller_selector', 'bool_version', 'bool_seconds', 'wrong_memory', 'unknown_field']:
            changed = admission()
            if mutation == 'missing_activation':
                changed['sources'] = [p for p in changed['sources'] if PureWindowsPath(p['path']).name != 'chat_ui_activation.py']
            elif mutation == 'retag_build':
                next(p for p in changed['sources'] if PureWindowsPath(p['path']).name == 'chat_ui_build.py')['path'] = 'D:/Synthetic/LocalLore/benchmarks/transcript_ui_build.py'
            elif mutation.startswith('extra_'): changed['artifacts'][mutation[6:]] = legacy.pin('D:/Synthetic/extra.bin')
            elif mutation == 'caller_selector': changed['selectors'] = list(SELECTORS)
            elif mutation == 'bool_version': changed['version'] = True
            elif mutation == 'bool_seconds': changed['seconds'] = True
            elif mutation == 'wrong_memory': changed['guest']['memory_mib'] = 4096
            else: changed['private_canary'] = 'SYNTHETIC_ONLY'
            with self.subTest(mutation=mutation), self.assertRaises(core.TargetRefused): contract.validate_admission(changed)

    def test_exact_eight_literal_vectors_work_and_nearby_selectors_do_not(self):
        value = admission()
        for row in SELECTORS:
            operation = dict(argv=instrument(row), stdin=None)
            self.assertEqual(contract.validate_operation(operation, value), operation)
            self.assertEqual(contract.instrumentation_kind(operation['argv']), row[0])
        bad = [instrument(SELECTORS[0])[:-1] + ['org.locallore.app.archiveverify.test/androidx.test.runner.AndroidJUnitRunner'],
            instrument(SELECTORS[1]) + ['-e', 'package', 'org.locallore.app'],
            instrument(SELECTORS[2])[:6] + [SELECTORS[2][1], instrument(SELECTORS[2])[-1]],
            previous_fixture.instrument(previous_fixture.SELECTORS[0])]
        for argv in bad:
            with self.subTest(argv=argv), self.assertRaises(core.TargetRefused):
                contract.validate_operation(dict(argv=argv, stdin=None), value)
            with self.assertRaises(core.TargetRefused): contract.instrumentation_kind(argv)

    def test_unused_process_model_and_general_shell_commands_have_no_authority(self):
        value = admission()
        vectors = [['pidof', 'org.locallore.app'], ['am', 'force-stop', '--user', '0', 'org.locallore.app'],
            ['run-as', 'org.locallore.app', '--user', '0', 'cat', 'files/save'], ['sh', '-c', 'id'],
            ['df', '-k', '/data'], ['cat', '/proc/meminfo'], ['screencap', '-p'],
            ['getprop', 'ro.serialno'], ['sha256sum', '/data/app/foreign/base.apk']]
        for argv in vectors:
            with self.subTest(argv=argv), self.assertRaises(core.TargetRefused):
                contract.validate_operation(dict(argv=argv, stdin=None), value)
        transfer = dict(argv=['dd', 'of=/data/local/tmp/locallore-product-v1.apk', 'bs=65536'],
                        stdin=value['artifacts']['product_apk'])
        self.assertEqual(contract.validate_operation(transfer, value), transfer)
        transfer['stdin'] = value['artifacts']['test_apk']
        with self.assertRaises(core.TargetRefused): contract.validate_operation(transfer, value)

    def test_sessions_and_proofs_reject_old_protocol_and_cross_version_relabelling(self):
        value = admission()
        current = session(value)
        self.assertEqual(contract.validate_session(current, value), current)
        proof = legacy.proof(current)
        proof.update(protocol='current-chat-ui-socket-proof-v1',
            session=legacy.pin(PureWindowsPath(current['root']) / 'sdk-session-v11.json'))
        contract.validate_proof(proof, current, proof['context'])
        for key, replacement in [('protocol', previous.SDK_PROTOCOL), ('version', 10), ('version', True)]:
            changed = copy.deepcopy(current); changed[key] = replacement
            with self.subTest(key=key, replacement=replacement), self.assertRaises(core.TargetRefused):
                contract.validate_session(changed, value)
        changed = copy.deepcopy(proof); changed['protocol'] = previous.PROOF_PROTOCOL
        with self.assertRaises(core.TargetRefused): contract.validate_proof(changed, current, changed['context'])
        changed = copy.deepcopy(proof); changed['session']['path'] = str(PureWindowsPath(current['root']) / 'sdk-session-v10.json')
        with self.assertRaises(core.TargetRefused): contract.validate_proof(changed, current, changed['context'])


@unittest.skipUnless(os.name == 'nt', 'Owned tiny D bindings; native/launch hooks are mocked')
class ChatUiBuildBoundaryTests(unittest.TestCase):
    def setUp(self):
        self.root = scratch()
        self.value = admission()
        self.path = self.root / 'synthetic-admission.json'
        wire.environment.create_json(self.path, self.value)
        self.pin = wire.environment.binding(self.path)

    def test_build_refusal_precedes_live_worker_and_parent_native_construction(self):
        module = types.ModuleType('benchmarks.chat_ui_build'); calls = []
        def refuse(value):
            calls.append(copy.deepcopy(value)); contract.validate_admission(value)
            raise ValueError('synthetic required product refusal')
        module.verify_current = refuse
        with patch.dict('sys.modules', {'benchmarks.chat_ui_build': module}), \
             patch.object(mechanisms._LiveOwnedTarget, '__init__', side_effect=AssertionError('native live')) as live, \
             patch.object(mechanisms._TargetRuntimeCore, '__init__', side_effect=AssertionError('native worker')) as worker, \
             patch.object(mechanisms, '_parent', side_effect=AssertionError('parent launch')) as parent:
            with self.assertRaisesRegex(ValueError, 'product refusal'): owner.LiveOwnedChatUiTarget(self.pin, self.pin)
            with self.assertRaisesRegex(ValueError, 'product refusal'):
                owner._ChatUiTargetRuntime(dict(validated_admission=self.value), self.pin, self.root)
            with redirect_stdout(io.StringIO()):
                result = owner.main(['--admission', self.pin['path'], '--admission-sha256', self.pin['sha256']])
            self.assertEqual(result, 1)
            live.assert_not_called(); worker.assert_not_called(); parent.assert_not_called()
        self.assertEqual(calls, [self.value, self.value, self.value])

    def test_positive_gate_order_and_exact_concrete_classes_are_fixed(self):
        module = types.ModuleType('benchmarks.chat_ui_build'); order = []
        module.verify_current = lambda value: order.append('build')
        with patch.dict('sys.modules', {'benchmarks.chat_ui_build': module}), \
             patch.object(mechanisms._LiveOwnedTarget, '__init__', side_effect=lambda *a: order.append('live')), \
             patch.object(mechanisms._TargetRuntimeCore, '__init__', side_effect=lambda *a: order.append('worker')):
            owner.LiveOwnedChatUiTarget(self.pin, self.pin)
            owner._ChatUiTargetRuntime(dict(validated_admission=self.value), self.pin, self.root)
        self.assertEqual(order, ['build', 'live', 'build', 'worker'])
        class DerivedLive(owner.LiveOwnedChatUiTarget): pass
        class DerivedWorker(owner._ChatUiTargetRuntime): pass
        with patch.object(owner, '_verify_build', side_effect=AssertionError('must refuse earlier')) as build:
            with self.assertRaises(owner.OwnerRefused): DerivedLive(self.pin, self.pin)
            with self.assertRaises(owner.OwnerRefused): DerivedWorker({}, self.pin, self.root)
            build.assert_not_called()

    def test_bad_admission_cannot_reach_product_guard_and_main_binds_only_fixed_hooks(self):
        bad = copy.deepcopy(self.value); bad['artifacts']['model'] = legacy.pin('D:/Synthetic/model.bin')
        badpath = self.root / 'synthetic-expanded.json'; wire.environment.create_json(badpath, bad)
        with patch.object(owner, '_verify_build', side_effect=AssertionError('expanded artifacts')) as build:
            with self.assertRaises(core.TargetRefused): owner.LiveOwnedChatUiTarget(wire.environment.binding(badpath), self.pin)
            build.assert_not_called()
        with patch.object(mechanisms, '_main_profile', return_value=23) as main:
            self.assertEqual(owner.main(['synthetic']), 23)
            args, kwargs = main.call_args
            self.assertEqual(args, (['synthetic'],))
            self.assertIs(kwargs['_contract'], contract)
            self.assertIs(kwargs['_verification'], replay)
            self.assertIs(kwargs['_runtime_type'], owner._ChatUiTargetRuntime)
            self.assertIs(kwargs['_admission_check'], owner._verify_build)


@unittest.skipUnless(os.name == 'nt', 'Tiny synthetic D captures with mocked wire/process observers')
class ChatUiByteReplayTests(unittest.TestCase):
    def enter(self, context):
        value = context.__enter__(); self.addCleanup(context.__exit__, None, None, None); return value

    def setUp(self):
        self.root = scratch()
        self.value = admission(); self.value['root'] = str(self.root / 'lease')
        self.value['server']['root'] = str(self.root / 'lease/server')
        for role in ('product_apk', 'test_apk'):
            path = self.root / (role + '.apk'); path.write_bytes(b'SYNTHETIC BYTE INPUT ' + role.encode())
            self.value['artifacts'][role] = wire.environment.binding(path)
        ap = self.root / 'synthetic-admission.json'; wire.environment.create_json(ap, self.value)
        self.admission = wire.environment.binding(ap)
        self.descriptor = running(self.value); self.descriptor['admission'] = self.admission
        rp = self.root / 'lease/running-v1.json'; rp.parent.mkdir(); wire.environment.create_json(rp, self.descriptor)
        self.running = wire.environment.binding(rp)
        self.live = object.__new__(owner.LiveOwnedChatUiTarget)
        self.live._admission = copy.deepcopy(self.value); self.live._descriptor = copy.deepcopy(self.descriptor)
        self.live._admission_binding = copy.deepcopy(self.admission); self.live._running_binding = copy.deepcopy(self.running)
        self.live._caller = copy.deepcopy(self.descriptor['worker'])
        self.live.guard = Mock(); self.live.fast_guard = Mock(); self.live.prove = Mock(side_effect=self.prove)
        self.clock, self.number, self.fail_phase = 100.0, 0, None
        self.enter(patch.object(wire.time, 'monotonic', side_effect=lambda: self.clock))
        self.enter(patch.object(wire.time, 'time', return_value=1800000010.0))
        self.enter(patch.object(wire, 'threading', types.SimpleNamespace(Thread=framing.InlineSender, Lock=threading.Lock)))
        self.sock = framing.FakeSocket(self.response())
        self.sockets = self.enter(patch.object(wire.socket, 'socket', side_effect=lambda *args: self.sock))

    @staticmethod
    def response():
        return b'OKAYOKAY' + framing.packet(1, b'SYNTHETIC original\0\x1a\xff\r\n') + framing.packet(3, b'\0')

    def capture(self):
        self.number += 1; path = self.root / ('session-%02d' % self.number); path.mkdir()
        return client.OwnedChatUiSdkCapture(path / 'clients', 30, self.live)

    def prove(self, path, active_session, context, sock, anchor, after=False):
        if context['phase'] == self.fail_phase: raise ValueError('synthetic after-proof refusal')
        value = legacy.proof(active_session, after=after)
        value.update(protocol='current-chat-ui-socket-proof-v1', context=copy.deepcopy(context),
            anchor=copy.deepcopy(anchor), session=wire.environment.binding(Path(active_session['root']) / 'sdk-session-v11.json'))
        queries = path.with_name(path.stem + '-queries-v1.json'); bundle = legacy.query_bundle(active_session)
        bundle['protocol'] = 'current-chat-ui-socket-proof-v1'
        wire.environment.create_json(queries, bundle); value['queries'] = wire.environment.binding(queries)
        wire.environment.create_json(path, value); return wire.environment.binding(path)

    def test_binary_output_real_closed_proof_replay_and_prior_sdk_rejection(self):
        cap = self.capture()
        self.assertEqual(cap.shell(['getprop', 'sys.boot_completed'], 'boot'), b'SYNTHETIC original\0\x1a\xff\r\n')
        pin = wire.environment.binding(cap.directory / 'command-0001.json')
        row = wire.environment.read_json(pin['path'])
        self.assertEqual((row['version'], row['protocol']), (11, 'sdk-current-chat-ui-v1'))
        self.assertTrue(row['client_qualified'])
        replay.verify_client_record(pin, cap.session, self.value)
        replay.require_current_clients(cap.directory.parent, 1, cap.session_binding, self.value)
        with self.assertRaises(core.TargetRefused): previous_replay.verify_client_record(pin, cap.session, self.value)
        for name in ('_contract', '_verification', '_expected_lease_class'):
            with self.assertRaises(AttributeError): setattr(cap, name, previous)

    def test_all_eight_claims_are_spent_before_duplicate_capture_can_send(self):
        for selector in SELECTORS:
            cap = self.capture(); self.sock = framing.FakeSocket(self.response())
            cap.shell(instrument(selector), selector[0])
            claimpath = self.root / 'lease/claims-v1' / (selector[0] + '-v1.json')
            claim = wire.environment.read_json(claimpath)
            self.assertEqual(claim['caller'], self.descriptor['worker'])
            self.assertEqual(claim['operation_sha256'], contract.operation_digest(dict(argv=instrument(selector), stdin=None)))
            retry = self.capture(); self.sock = framing.FakeSocket(self.response())
            with self.assertRaises(client.ClientRefused): retry.shell(instrument(selector), selector[0])
            self.assertEqual(retry.count, 0); self.assertEqual(self.sock.sent, b'')
        self.assertEqual(len(list((self.root / 'lease/claims-v1').iterdir())), 8)

    def test_old_or_subclassed_observers_and_capture_subclasses_refuse_before_guard_or_socket(self):
        class Derived(owner.LiveOwnedChatUiTarget): pass
        for kind in (previous_owner.LiveOwnedTranscriptUiTarget, Derived):
            bad = object.__new__(kind); bad.guard = Mock()
            path = self.root / kind.__name__; path.mkdir()
            with self.assertRaises(client.ClientRefused): client.OwnedChatUiSdkCapture(path / 'clients', 30, bad)
            bad.guard.assert_not_called(); self.assertEqual(list(path.iterdir()), [])
        class DerivedCapture(client.OwnedChatUiSdkCapture): pass
        with self.assertRaises(client.ClientRefused): DerivedCapture(self.root / 'unused', 30, self.live)
        cap = self.capture()
        with self.assertRaises(client.ClientRefused): cap.shell(previous_fixture.instrument(previous_fixture.SELECTORS[0]), 'wrong')
        self.sockets.assert_not_called()

    def test_success_exit_with_failed_after_proof_is_retained_unqualified_and_retry_stays_poisoned(self):
        self.fail_phase = 'after'; cap = self.capture()
        with self.assertRaises(client.ClientRefused): cap.shell(['getprop', 'sys.boot_completed'], 'boot')
        row = wire.environment.read_json(cap.directory / 'command-0001.json')
        self.assertEqual(row['returncode'], 0); self.assertFalse(row['client_qualified'])
        self.assertEqual(Path(row['stdout']['path']).read_bytes(), b'SYNTHETIC original\0\x1a\xff\r\n')
        self.assertTrue(self.sock.closed)
        attempts = self.sockets.call_count
        with self.assertRaises(client.ClientRefused): cap.shell(['getprop', 'sys.boot_completed'], 'retry')
        self.assertEqual(attempts, self.sockets.call_count)

    def test_changed_caller_and_raw_substitution_cannot_pass_closed_replay(self):
        cap = self.capture(); cap.shell(['getprop', 'sys.boot_completed'], 'boot')
        pin = wire.environment.binding(cap.directory / 'command-0001.json')
        wrong = copy.deepcopy(cap.session); wrong['caller']['creation_filetime'] += 1
        with self.assertRaises(core.TargetRefused): replay.verify_client_record(pin, wrong, self.value)
        row = wire.environment.read_json(pin['path']); Path(row['stdout']['path']).write_bytes(b'SYNTHETIC substitution')
        with self.assertRaises((core.TargetRefused, wire.environment.EnvironmentRefused)):
            replay.verify_client_record(pin, cap.session, self.value)


if __name__ == '__main__':
    unittest.main()
