"""Real SDK9 framing, claims and replay over explicitly synthetic wire IO.

No SDK executable, native ownership, socket or Android process is exercised.
Copyright 2026 LocalLore contributors. SPDX-License-Identifier: Apache-2.0
"""
import copy
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import Mock, patch

from benchmarks import android_process_client_v4 as wire
from benchmarks import android_process_presentation_process_client as client
from benchmarks import android_process_presentation_process_verification as replay
from benchmarks import android_process_player_presentation_ui_verification as old_replay
from benchmarks import owned_presentation_process_contract as contract
from benchmarks import owned_presentation_process_owner as owner
from benchmarks import owned_player_presentation_ui_owner as old_owner
from scripts.tests import test_android_process_client_v4 as framing
from scripts.tests import test_presentation_process_runner_fixtures as f


@unittest.skipUnless(os.name == 'nt', 'Windows byte-bound metadata; all native/wire IO simulated')
class PresentationProcessRunnerClientTests(unittest.TestCase):
    def enter(self, context):
        result = context.__enter__()
        self.addCleanup(context.__exit__, None, None, None)
        return result

    def setUp(self):
        self.base = Path(tempfile.mkdtemp(prefix='locallore-presentation-wire-'))
        self.assertEqual(self.base.drive.upper(), 'D:')
        self.a = f.admission(contract)
        self.a['root'] = str(self.base / 'lease')
        self.a['server']['root'] = str(self.base / 'lease/server')
        for role in f.STAGED:
            path = self.base / (role + '.apk')
            path.write_bytes(b'PK\0SYNTHETIC-WIRE-ONLY-' + role.encode())
            self.a['artifacts'][role] = wire.environment.binding(path)
        self.ap = self.base / 'admission-v1.json'
        wire.environment.create_json(self.ap, self.a)
        self.admission = wire.environment.binding(self.ap)
        self.d = f.running(self.a)
        self.d['admission'] = self.admission
        self.rp = self.base / 'lease/running-v1.json'
        self.rp.parent.mkdir()
        wire.environment.create_json(self.rp, self.d)
        self.running = wire.environment.binding(self.rp)
        # Skip only actual native constructor/observations. The concrete class,
        # fixed profile, claim_once, wire and byte-bound readers remain real.
        self.live = object.__new__(owner.LiveOwnedPresentationProcessTarget)
        self.live._admission = copy.deepcopy(self.a)
        self.live._descriptor = copy.deepcopy(self.d)
        self.live._admission_binding = copy.deepcopy(self.admission)
        self.live._running_binding = copy.deepcopy(self.running)
        self.live._caller = copy.deepcopy(self.d['worker'])
        self.live.guard = Mock()
        self.live.fast_guard = Mock()
        self.live.prove = Mock(side_effect=self.prove)
        self.clock, self.index, self.fail_proof = 100.0, 0, set()
        self.enter(patch.object(wire.time, 'monotonic', side_effect=lambda: self.clock))
        self.enter(patch.object(wire.time, 'time', return_value=1800000010.0))
        self.enter(patch.object(wire.threading, 'Thread', framing.InlineSender))
        self.sock = framing.FakeSocket(self.response())
        self.socket_factory = self.enter(patch.object(wire.socket, 'socket', side_effect=lambda *args: self.sock))

    @staticmethod
    def response(body=b'original\0\x1a\xff\r\n'):
        return b'OKAYOKAY' + framing.packet(1, body) + framing.packet(3, b'\0')

    def capture(self):
        self.index += 1
        root = self.base / ('session-%02d' % self.index)
        root.mkdir()
        return client.OwnedPresentationProcessSdkCapture(root / 'clients', 100, self.live)

    def prove(self, path, session, context, sock, anchor, after=False):
        if context['phase'] in self.fail_proof:
            raise ValueError('synthetic held observation refusal')
        value = f.proof(session, after=after)
        value.update(context=copy.deepcopy(context), anchor=copy.deepcopy(anchor),
                     session=wire.environment.binding(Path(session['root']) / 'sdk-session-v9.json'))
        queries = path.with_name(path.stem + '-queries-v1.json')
        wire.environment.create_json(queries, f.query_bundle(session))
        value['queries'] = wire.environment.binding(queries)
        wire.environment.create_json(path, value)
        return wire.environment.binding(path)

    def record(self, cap):
        return wire.environment.read_json(cap.directory / 'command-0001.json')

    def test_binary_terminal_bytes_replay_as_sdk9_only_with_immutable_concrete_profile(self):
        cap = self.capture()
        raw = b'original\0\x1a\xff\r\n'
        self.assertEqual(cap.shell(['getprop', 'sys.boot_completed'], 'boot'), raw)
        row = self.record(cap)
        self.assertEqual((row['version'], row['protocol']), (9, f.SDK_PROTOCOL))
        self.assertTrue(row['client_qualified'])
        self.assertEqual(Path(row['session']['path']).name, 'sdk-session-v9.json')
        pin = wire.environment.binding(cap.directory / 'command-0001.json')
        replay.verify_client_record(pin, cap.session, self.a)
        replay.require_current_clients(cap.directory.parent, 1, cap.session_binding, self.a)
        with self.assertRaises(old_owner.contract.TargetRefused):
            old_replay.verify_client_record(pin, cap.session, self.a)
        for name in ('_contract', '_verification', '_expected_lease_class'):
            with self.assertRaises(AttributeError):
                setattr(cap, name, object())

    def test_external_case_claim_is_once_for_admission_even_in_another_sdk_session(self):
        cap = self.capture()
        cap.shell(f.instrument(self.a), 'presentation_process')
        path = self.base / 'lease/claims-v1/presentation_process-v1.json'
        claim = wire.environment.read_json(path)
        self.assertEqual(claim['caller'], self.d['worker'])
        self.assertEqual(claim['protocol'], f.PROTOCOL)
        self.assertEqual(claim['operation_sha256'], contract.operation_digest(dict(argv=f.instrument(self.a), stdin=None)))
        self.sock = framing.FakeSocket(self.response())
        retry = self.capture()
        with self.assertRaises(client.ClientRefused):
            retry.shell(f.instrument(self.a), 'presentation_process')
        self.assertEqual(retry.count, 0)
        self.assertEqual(self.sock.sent, b'')
        self.assertEqual(len(list(path.parent.glob('*.json'))), 1)

    def test_third_apk_transfer_uses_exact_controller_bytes_and_refuses_role_substitution(self):
        cap = self.capture()
        source = self.a['artifacts']['controller_apk']
        argv = ['dd', 'of=' + f.STAGED['controller_apk'], 'bs=65536']
        cap.stream(argv, source, 'controller-stage', seconds=15)
        row = self.record(cap)
        self.assertTrue(row['client_qualified'])
        self.assertEqual((row['stdin_bytes'], row['stdin_sha256']), (source['bytes'], source['sha256']))
        self.assertIn(framing.packet(0, Path(source['path']).read_bytes()), self.sock.sent)
        self.sock = framing.FakeSocket(self.response())
        wrong = self.capture()
        with self.assertRaises(client.ClientRefused):
            wrong.stream(argv, self.a['artifacts']['test_apk'], 'wrong-role', seconds=15)
        self.assertEqual(wrong.count, 0)
        self.assertEqual(self.sock.sent, b'')

    def test_wrong_owner_types_and_unadmitted_external_arguments_refuse_before_socket_dispatch(self):
        class Derived(owner.LiveOwnedPresentationProcessTarget):
            pass
        for kind in (old_owner.LiveOwnedPlayerPresentationUiTarget, Derived):
            wrong = object.__new__(kind)
            wrong.guard = Mock()
            root = self.base / kind.__name__
            root.mkdir()
            with self.assertRaises(client.ClientRefused):
                client.OwnedPresentationProcessSdkCapture(root / 'clients', 30, wrong)
            wrong.guard.assert_not_called()
            self.assertEqual(list(root.iterdir()), [])
        for index, value in ((6, 'restore_non_default'), (9, 'f' * 16), (12, '0' * 64), (13, 'foreign/Runner')):
            argv = f.instrument(self.a)
            argv[index] = value
            cap = self.capture()
            with self.assertRaises(client.ClientRefused):
                cap.shell(argv, 'forbidden')
            self.assertEqual(cap.count, 0)
        self.socket_factory.assert_not_called()
        self.assertFalse((self.base / 'lease/claims-v1').exists())

    def test_failed_after_proof_keeps_raw_success_unqualified_and_cannot_retry(self):
        self.fail_proof = {'after'}
        cap = self.capture()
        with self.assertRaises(client.ClientRefused):
            cap.shell(['getprop', 'sys.boot_completed'], 'boot')
        row = self.record(cap)
        self.assertEqual(row['returncode'], 0)
        self.assertFalse(row['client_qualified'])
        self.assertEqual(Path(row['stdout']['path']).read_bytes(), b'original\0\x1a\xff\r\n')
        self.assertTrue(self.sock.closed)
        count = self.socket_factory.call_count
        with self.assertRaises(client.ClientRefused):
            cap.shell(['getprop', 'sys.boot_completed'], 'retry')
        self.assertEqual(self.socket_factory.call_count, count)

    def test_closed_replay_refuses_mutated_raw_bytes_and_wrong_current_caller(self):
        cap = self.capture()
        cap.shell(['getprop', 'sys.boot_completed'], 'boot')
        row = self.record(cap)
        path = cap.directory / 'command-0001.json'
        session = copy.deepcopy(cap.session)
        session['caller']['creation_filetime'] += 1
        with self.assertRaises(contract.TargetRefused):
            replay.verify_client_record(wire.environment.binding(path), session, self.a)
        Path(row['stdout']['path']).write_bytes(b'substituted stdout')
        with self.assertRaises((contract.TargetRefused, wire.environment.EnvironmentRefused)):
            replay.verify_client_record(wire.environment.binding(path), cap.session, self.a)


if __name__ == '__main__':
    unittest.main()
