"""Fixed SDK10 authority and real closed framing over synthetic host-only IO.

No Android executable, native ownership, real socket, guest or ledger is used.
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

from benchmarks import android_process_client_v4 as wire
from benchmarks import android_process_transcript_ui_client as client
from benchmarks import android_process_transcript_ui_verification as replay
from benchmarks import owned_target_contract as core
from benchmarks import owned_target_owner as shared_owner
from benchmarks import owned_transcript_ui_contract as contract
from benchmarks import owned_transcript_ui_owner as owner
from benchmarks import owned_player_presentation_ui_contract as old_contract
from benchmarks import owned_player_presentation_ui_owner as old_owner
from benchmarks import android_process_player_presentation_ui_verification as old_replay
from scripts.tests import test_android_process_client_v4 as framing
from scripts.tests import test_owned_target_contract as legacy


SELECTORS = (
    ('transcript_history', 'org.locallore.app.TranscriptFollowScreenTest',
     'readingHistoryKeepsPositionUntilLatestAndPreservesTheUnsentDialogue'),
    ('transcript_tail', 'org.locallore.app.TranscriptFollowScreenTest',
     'seeingOnlyTheHeadOfALongTailDoesNotAuthorizeFollowingAnAppend'),
    ('transcript_composer', 'org.locallore.app.TranscriptFollowScreenTest',
     'readingTheComposerPastTheTailFollowsTheNewReplyWithoutSubmittingTheDraft'),
    ('transcript_branch', 'org.locallore.app.TranscriptFollowScreenTest',
     'retainedLatestCallbackCannotNavigateAnotherBranchWithReusedMessageIds'),
    ('transcript_rollover_follow', 'org.locallore.app.ui.TranscriptRolloverUiTest',
     'readerBelowFortyRowTailSeesRolledReplyWithoutScrollingOrSendingDraft'),
    ('transcript_rollover_history', 'org.locallore.app.ui.TranscriptRolloverUiTest',
     'historyReaderKeepsSurvivingRowUntilLatestAndKeepsOriginalDraft'),
)
NEW_SOURCES = frozenset((
    'owned_transcript_ui_contract.py', 'owned_transcript_ui_owner.py',
    'android_process_transcript_ui_client.py', 'android_process_transcript_ui_verification.py',
    'transcript_ui_build.py', 'transcript_ui_controller.py', 'android_instrumentation_evidence.py',
))


def admission():
    value = legacy.admission()
    value['protocol'] = 'owned-emulator-transcript-ui-v1'
    value['guest']['root'] = 'D:/Dev/Experiments/LocalLore/2026-11-01-transcript-navigation-ui-v1/avd-v1'
    value['artifacts'] = {key: value['artifacts'][key] for key in ('build', 'product_apk', 'test_apk')}
    value['sources'] = sorted([legacy.pin(PureWindowsPath('D:/Synthetic/LocalLore/benchmarks') / name)
                               for name in core.SOURCE_NAMES | NEW_SOURCES], key=lambda row: row['path'])
    by_name = {PureWindowsPath(row['path']).name: row for row in value['sources']}
    value['server']['sources'] = [copy.deepcopy(by_name[PureWindowsPath(row['path']).name])
                                  for row in value['server']['sources']]
    return value


def instrument(row):
    return ['am', 'instrument', '-w', '-r', '-e', 'class', row[1] + '#' + row[2],
            'org.locallore.app.test/androidx.test.runner.AndroidJUnitRunner']


def running(value):
    result = legacy.running(value)
    result['protocol'] = 'owned-emulator-transcript-ui-v1'
    return result


class TranscriptUiProfileTests(unittest.TestCase):
    def test_fixed_ordinary_profile_and_exact_six_selectors_are_pure_and_copy_inputs(self):
        self.assertEqual((contract.PROTOCOL, contract.SDK_PROTOCOL, contract.PROOF_PROTOCOL),
                         ('owned-emulator-transcript-ui-v1', 'sdk-transcript-ui-v1', 'transcript-ui-socket-proof-v1'))
        self.assertEqual((contract.CLIENT_VERSION, contract.SESSION_FILE), (10, 'sdk-session-v10.json'))
        self.assertEqual((contract.APP, contract.TEST, contract.MODEL_MATERIAL),
                         ('org.locallore.app', 'org.locallore.app.test', False))
        self.assertEqual(contract.INSTRUMENTATIONS, SELECTORS)
        self.assertEqual(contract.CLAIM_KINDS, tuple(row[0] for row in SELECTORS))
        self.assertEqual(contract.SOURCE_NAMES, core.SOURCE_NAMES | NEW_SOURCES)
        value = admission()
        before = copy.deepcopy(value)
        with patch.object(Path, 'open', side_effect=AssertionError('file IO')):
            actual = contract.validate_admission(value)
        self.assertEqual(actual, before)
        actual['sources'].clear()
        self.assertEqual(value, before)

    def test_legacy_protocol_root_source_closure_and_artifact_expansion_refuse(self):
        original = admission()
        contract.validate_admission(original)
        for mutation in ('protocol', 'root', 'source', 'model', 'controller', 'selectors'):
            value = copy.deepcopy(original)
            if mutation == 'protocol':
                value['protocol'] = old_contract.PROTOCOL
            elif mutation == 'root':
                value['guest']['root'] = str(old_contract.GUEST_ROOT)
            elif mutation == 'source':
                value['sources'] = [row for row in value['sources'] if PureWindowsPath(row['path']).name != 'transcript_ui_build.py']
            elif mutation in ('model', 'controller'):
                value['artifacts'][mutation] = legacy.pin('D:/Synthetic/' + mutation)
            else:
                value['selectors'] = list(SELECTORS)
            with self.subTest(mutation=mutation), self.assertRaises(core.TargetRefused):
                contract.validate_admission(value)
        with self.assertRaises(core.TargetRefused):
            old_contract.validate_admission(original)

    def test_only_six_closed_ordinary_runner_vectors_can_claim_a_method(self):
        value = admission()
        for row in SELECTORS:
            argv = instrument(row)
            self.assertEqual(contract.instrumentation_kind(argv), row[0])
            self.assertEqual(contract.validate_operation(dict(argv=argv, stdin=None), value), dict(argv=argv, stdin=None))
        for argv in (
            instrument(SELECTORS[4])[:6] + [SELECTORS[4][1].replace('.app.ui.', '.app.') + '#' + SELECTORS[4][2], instrument(SELECTORS[4])[-1]],
            instrument(SELECTORS[0])[:-1] + ['org.locallore.app.archiveverify.test/androidx.test.runner.AndroidJUnitRunner'],
            instrument(SELECTORS[0]) + ['-e', 'package', 'org.locallore.app'],
            ['am', 'instrument', '-w', '-r', '-e', 'class', SELECTORS[0][1], instrument(SELECTORS[0])[-1]],
        ):
            with self.subTest(argv=argv), self.assertRaises(core.TargetRefused):
                contract.validate_operation(dict(argv=argv, stdin=None), value)

    def test_unused_process_model_shell_and_foreign_apk_authority_is_denied(self):
        value = admission()
        for argv in (['pidof', 'org.locallore.app'], ['am', 'force-stop', '--user', '0', 'org.locallore.app'],
                     ['sh', '-c', 'id'], ['run-as', 'org.locallore.app', 'cat', 'files/private'],
                     ['df', '-k', '/data'], ['cat', '/proc/meminfo'], ['screencap', '-p'],
                     ['getprop', 'ro.serialno'], ['sha256sum', '/data/app/foreign-pkg/base.apk']):
            with self.subTest(argv=argv), self.assertRaises(core.TargetRefused):
                contract.validate_operation(dict(argv=argv, stdin=None), value)
        operation = dict(argv=['dd', 'of=/data/local/tmp/locallore-product-v1.apk', 'bs=65536'],
                         stdin=value['artifacts']['product_apk'])
        self.assertEqual(contract.validate_operation(operation, value), operation)
        operation['stdin'] = value['artifacts']['test_apk']
        with self.assertRaises(core.TargetRefused):
            contract.validate_operation(operation, value)

    def test_session_and_proof_cannot_be_relabelled_from_earlier_cohorts(self):
        value = admission()
        session = legacy.session(value)
        session['protocol'] = contract.SDK_PROTOCOL
        session['descriptor']['protocol'] = contract.PROTOCOL
        self.assertEqual(contract.validate_session(session, value), session)
        proof = legacy.proof(session)
        proof.update(protocol=contract.PROOF_PROTOCOL,
                     session=legacy.pin(PureWindowsPath(session['root']) / 'sdk-session-v10.json'))
        contract.validate_proof(proof, session, proof['context'])
        for key, changed in (('protocol', 'sdk-player-presentation-ui-v1'), ('version', 8)):
            bad = copy.deepcopy(session)
            bad[key] = changed
            with self.subTest(key=key), self.assertRaises(core.TargetRefused):
                contract.validate_session(bad, value)
        bad = copy.deepcopy(proof)
        bad['protocol'] = old_contract.PROOF_PROTOCOL
        with self.assertRaises(core.TargetRefused):
            contract.validate_proof(bad, session, proof['context'])

    @unittest.skipUnless(os.name == 'nt', 'Tiny D metadata; all native/launch hooks trapped')
    def test_fixed_lazy_build_gate_precedes_live_worker_and_parent_native_hooks(self):
        root = Path(tempfile.mkdtemp(prefix='locallore-transcript-owner-'))
        self.assertEqual(root.drive.upper(), 'D:')
        value = admission()
        path = root / 'admission-v1.json'
        wire.environment.create_json(path, value)
        binding = wire.environment.binding(path)
        module = types.ModuleType('benchmarks.transcript_ui_build')
        calls = []
        def refuse(admitted):
            self.assertEqual(contract.validate_admission(admitted), value)
            calls.append(copy.deepcopy(admitted))
            raise ValueError('synthetic required build refusal')
        module.verify_current = refuse
        with patch.dict('sys.modules', {'benchmarks.transcript_ui_build': module}), \
             patch.object(shared_owner._LiveOwnedTarget, '__init__', side_effect=AssertionError('native live')) as live, \
             patch.object(shared_owner._TargetRuntimeCore, '__init__', side_effect=AssertionError('native worker')) as worker, \
             patch.object(shared_owner, '_parent', side_effect=AssertionError('parent launch')) as parent:
            with self.assertRaisesRegex(ValueError, 'required build refusal'):
                owner.LiveOwnedTranscriptUiTarget(binding, binding)
            with self.assertRaisesRegex(ValueError, 'required build refusal'):
                owner._TranscriptUiTargetRuntime(dict(validated_admission=value), binding, root)
            with redirect_stdout(io.StringIO()):
                code = owner.main(['--admission', binding['path'], '--admission-sha256', binding['sha256']])
            self.assertEqual(code, 1)
            live.assert_not_called(); worker.assert_not_called(); parent.assert_not_called()
        self.assertEqual(len(calls), 3)


@unittest.skipUnless(os.name == 'nt', 'Synthetic wire and tiny owned D files only')
class TranscriptUiWireTests(unittest.TestCase):
    def enter(self, context):
        value = context.__enter__()
        self.addCleanup(context.__exit__, None, None, None)
        return value

    def setUp(self):
        self.base = Path(tempfile.mkdtemp(prefix='locallore-transcript-wire-'))
        self.assertEqual(self.base.drive.upper(), 'D:')
        self.a = admission()
        self.a['root'] = str(self.base / 'lease')
        self.a['server']['root'] = str(self.base / 'lease/server')
        for role in ('product_apk', 'test_apk'):
            path = self.base / (role + '.apk')
            path.write_bytes(b'SYNTHETIC WIRE INPUT ' + role.encode())
            self.a['artifacts'][role] = wire.environment.binding(path)
        self.ap = self.base / 'admission-v1.json'
        wire.environment.create_json(self.ap, self.a)
        self.admission = wire.environment.binding(self.ap)
        self.d = running(self.a)
        self.d['admission'] = self.admission
        self.rp = self.base / 'lease/running-v1.json'
        self.rp.parent.mkdir()
        wire.environment.create_json(self.rp, self.d)
        self.running = wire.environment.binding(self.rp)
        self.live = object.__new__(owner.LiveOwnedTranscriptUiTarget)
        self.live._admission = copy.deepcopy(self.a)
        self.live._descriptor = copy.deepcopy(self.d)
        self.live._admission_binding = copy.deepcopy(self.admission)
        self.live._running_binding = copy.deepcopy(self.running)
        self.live._caller = copy.deepcopy(self.d['worker'])
        self.live.guard = Mock(); self.live.fast_guard = Mock()
        self.live.prove = Mock(side_effect=self.prove)
        self.clock, self.index, self.fail_proof = 100.0, 0, set()
        self.enter(patch.object(wire.time, 'monotonic', side_effect=lambda: self.clock))
        self.enter(patch.object(wire.time, 'time', return_value=1800000010.0))
        # Isolate this sender seam; never mutate the stdlib Thread implementation.
        self.enter(patch.object(wire, 'threading', types.SimpleNamespace(Thread=framing.InlineSender, Lock=threading.Lock)))
        self.sock = framing.FakeSocket(self.response())
        self.socket_factory = self.enter(patch.object(wire.socket, 'socket', side_effect=lambda *args: self.sock))

    @staticmethod
    def response(body=b'original\0\x1a\xff\r\n'):
        return b'OKAYOKAY' + framing.packet(1, body) + framing.packet(3, b'\0')

    def capture(self):
        self.index += 1
        root = self.base / ('session-%02d' % self.index)
        root.mkdir()
        return client.OwnedTranscriptUiSdkCapture(root / 'clients', 30, self.live)

    def prove(self, path, session, context, sock, anchor, after=False):
        if context['phase'] in self.fail_proof:
            raise ValueError('synthetic held observation refusal')
        value = legacy.proof(session, after=after)
        value.update(protocol='transcript-ui-socket-proof-v1', context=copy.deepcopy(context),
                     anchor=copy.deepcopy(anchor),
                     session=wire.environment.binding(Path(session['root']) / 'sdk-session-v10.json'))
        queries = path.with_name(path.stem + '-queries-v1.json')
        bundle = legacy.query_bundle(session)
        bundle['protocol'] = 'transcript-ui-socket-proof-v1'
        wire.environment.create_json(queries, bundle)
        value['queries'] = wire.environment.binding(queries)
        wire.environment.create_json(path, value)
        return wire.environment.binding(path)

    def record(self, cap):
        return wire.environment.read_json(cap.directory / 'command-0001.json')

    def test_binary_bytes_and_complete_proofs_replay_only_under_sdk10(self):
        cap = self.capture()
        self.assertEqual(cap.shell(['getprop', 'sys.boot_completed'], 'boot'), b'original\0\x1a\xff\r\n')
        row = self.record(cap)
        self.assertEqual((row['version'], row['protocol']), (10, 'sdk-transcript-ui-v1'))
        self.assertTrue(row['client_qualified'])
        pin = wire.environment.binding(cap.directory / 'command-0001.json')
        replay.verify_client_record(pin, cap.session, self.a)
        replay.require_current_clients(cap.directory.parent, 1, cap.session_binding, self.a)
        with self.assertRaises(core.TargetRefused):
            old_replay.verify_client_record(pin, cap.session, self.a)
        for name in ('_contract', '_verification', '_expected_lease_class'):
            with self.assertRaises(AttributeError): setattr(cap, name, object())

    def test_each_instrumentation_claim_is_spent_admission_wide_before_second_wire_dispatch(self):
        for selector in SELECTORS:
            cap = self.capture()
            self.sock = framing.FakeSocket(self.response())
            cap.shell(instrument(selector), selector[0])
            claim_path = self.base / 'lease/claims-v1' / (selector[0] + '-v1.json')
            claim = wire.environment.read_json(claim_path)
            self.assertEqual(claim['caller'], self.d['worker'])
            self.assertEqual(claim['operation_sha256'], contract.operation_digest(dict(argv=instrument(selector), stdin=None)))
            self.sock = framing.FakeSocket(self.response())
            retry = self.capture()
            with self.assertRaises(client.ClientRefused): retry.shell(instrument(selector), selector[0])
            self.assertEqual(retry.count, 0)
            self.assertEqual(self.sock.sent, b'')
        self.assertEqual(len(list((self.base / 'lease/claims-v1').glob('*.json'))), 6)

    def test_legacy_observer_client_subclasses_and_invalid_selector_refuse_before_socket(self):
        class Derived(owner.LiveOwnedTranscriptUiTarget): pass
        for kind in (old_owner.LiveOwnedPlayerPresentationUiTarget, Derived):
            wrong = object.__new__(kind)
            wrong.guard = Mock()
            path = self.base / kind.__name__
            path.mkdir()
            with self.assertRaises(client.ClientRefused): client.OwnedTranscriptUiSdkCapture(path / 'clients', 30, wrong)
            wrong.guard.assert_not_called()
            self.assertEqual(list(path.iterdir()), [])
        class DerivedCapture(client.OwnedTranscriptUiSdkCapture): pass
        with self.assertRaises(client.ClientRefused): DerivedCapture(self.base / 'unused', 30, self.live)
        cap = self.capture()
        bad = instrument(SELECTORS[4]); bad[6] = bad[6].replace('.app.ui.', '.app.')
        with self.assertRaises(client.ClientRefused): cap.shell(bad, 'wrong')
        self.socket_factory.assert_not_called()

    def test_after_proof_refusal_keeps_success_bytes_unqualified_and_poisons_retry(self):
        self.fail_proof = {'after'}
        cap = self.capture()
        with self.assertRaises(client.ClientRefused): cap.shell(['getprop', 'sys.boot_completed'], 'boot')
        row = self.record(cap)
        self.assertEqual(row['returncode'], 0)
        self.assertFalse(row['client_qualified'])
        self.assertEqual(Path(row['stdout']['path']).read_bytes(), b'original\0\x1a\xff\r\n')
        self.assertTrue(self.sock.closed)
        calls = self.socket_factory.call_count
        with self.assertRaises(client.ClientRefused): cap.shell(['getprop', 'sys.boot_completed'], 'retry')
        self.assertEqual(self.socket_factory.call_count, calls)

    def test_closed_reader_refuses_changed_caller_and_mutated_raw_capture(self):
        cap = self.capture()
        cap.shell(['getprop', 'sys.boot_completed'], 'boot')
        pin = wire.environment.binding(cap.directory / 'command-0001.json')
        session = copy.deepcopy(cap.session)
        session['caller']['creation_filetime'] += 1
        with self.assertRaises(core.TargetRefused): replay.verify_client_record(pin, session, self.a)
        row = self.record(cap)
        Path(row['stdout']['path']).write_bytes(b'substituted stdout')
        with self.assertRaises((core.TargetRefused, wire.environment.EnvironmentRefused)):
            replay.verify_client_record(pin, cap.session, self.a)


if __name__ == '__main__':
    unittest.main()
