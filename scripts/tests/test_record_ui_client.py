# Copyright 2026 LocalLore contributors. SPDX-License-Identifier: Apache-2.0
"""FIRST real SDK7 framing/replay with synthetic IO only; never live SDK authority."""
import copy
import os
from pathlib import Path
from types import SimpleNamespace
import unittest
from unittest.mock import Mock, patch

from benchmarks import android_process_client_v4 as wire
from benchmarks import android_process_record_ui_client as client
from benchmarks import android_process_record_ui_verification as replay
from benchmarks import android_process_verification_v6 as old_replay
from benchmarks import owned_record_ui_contract as contract
from benchmarks import owned_record_ui_owner as owner
from scripts.tests import test_archive_ui_client as previous
from scripts.tests import test_record_ui_fixtures as f
from scripts.tests import test_android_process_client_v4 as framing


@unittest.skipUnless(os.name == 'nt', 'Windows metadata fixtures, all native/socket IO mocked')
class RecordUiClientTests(unittest.TestCase):
    enter = previous.ArchiveUiClientTests.enter
    response = previous.ArchiveUiClientTests.response
    record = previous.ArchiveUiClientTests.record

    def setUp(self):
        # Reuse only fixture setup methods, not inherited TestCase methods.
        self.enter(patch.object(previous, 'f', f))
        self.enter(patch.object(previous, 'owner', SimpleNamespace(LiveOwnedUiTarget=owner.LiveOwnedRecordUiTarget)))
        previous.ArchiveUiClientTests.setUp(self)

    def capture(self):
        self.index += 1
        parent = self.base / ('record-session-%02d' % self.index); parent.mkdir()
        return client.OwnedRecordUiSdkCapture(parent / 'clients', 100, self.live)

    def prove(self, path, session, context, sock, anchor, after=False):
        self.clock += self.proof_cost.get(context['phase'], 0)
        if context['phase'] in self.fail_proof: raise ValueError('synthetic proof refused')
        value = f.proof(session, after=after)
        value.update(context=copy.deepcopy(context), anchor=copy.deepcopy(anchor),
                     session=wire.environment.binding(Path(session['root']) / f.SESSION_FILE))
        queries = path.with_name(path.stem + '-queries-v1.json')
        wire.environment.create_json(queries, f.query_bundle(session)); value['queries'] = wire.environment.binding(queries)
        wire.environment.create_json(path, value)
        return wire.environment.binding(path)

    def test_original_binary_output_replays_only_through_sdk7_and_keeps_fixed_properties(self):
        cap = self.capture()
        raw = b'original\0\x1a\xff\r\n'
        self.assertEqual(cap.shell(['getprop', 'sys.boot_completed'], 'boot'), raw)
        row = self.record(cap)
        self.assertEqual((row['version'], row['protocol']), (7, f.SDK_PROTOCOL))
        self.assertTrue(row['client_qualified']); self.assertEqual(Path(row['session']['path']).name, f.SESSION_FILE)
        replay.verify_client_record(wire.environment.binding(cap.directory / 'command-0001.json'), cap.session, self.a)
        replay.require_current_clients(cap.directory.parent, 1, cap.session_binding, self.a)
        with self.assertRaises(contract.TargetRefused):
            old_replay.verify_client_record(wire.environment.binding(cap.directory / 'command-0001.json'), cap.session, self.a)
        for name in ('_contract', '_verification', '_expected_lease_class'):
            with self.assertRaises(AttributeError): setattr(cap, name, object())
        self.assertIs(cap._contract, contract); self.assertIs(cap._verification, replay)

    def test_old_owner_subclasses_and_forbidden_selectors_cannot_open_any_socket(self):
        from benchmarks.owned_ui_owner import LiveOwnedUiTarget
        class Derived(owner.LiveOwnedRecordUiTarget): pass
        for kind in (LiveOwnedUiTarget, Derived):
            wrong = object.__new__(kind); wrong.guard = Mock()
            parent = self.base / kind.__name__; parent.mkdir()
            with self.assertRaises(wire.ClientRefused): client.OwnedRecordUiSdkCapture(parent / 'clients', 30, wrong)
            wrong.guard.assert_not_called(); self.assertEqual(list(parent.iterdir()), [])
        for argv in (['run-as', f.APP, '--user', '0', 'ls', 'files'], ['sh', '-c', 'id'],
                     ['am', 'instrument', '-w', '-r', '-e', 'class', 'foreign.Test#test', f.TEST + '/androidx.test.runner.AndroidJUnitRunner']):
            cap = self.capture()
            with self.assertRaises(wire.ClientRefused): cap.shell(argv, 'forbidden')
            self.assertFalse(cap.clean); self.assertEqual(cap.count, 0)
        self.socket_factory.assert_not_called()

    def test_ten_create_only_claims_bind_the_actual_worker_and_cannot_repeat_across_sessions(self):
        for triple in f.INSTRUMENTATIONS:
            self.sock = framing.FakeSocket(self.response()); cap = self.capture()
            cap.shell(f.instrument(triple), triple[0])
            claim = wire.environment.read_json(self.base / 'lease/claims-v1' / (triple[0] + '-v1.json'))
            self.assertEqual((claim['protocol'], claim['caller']), (f.PROTOCOL, self.d['worker']))
            self.assertEqual(claim['operation_sha256'], contract.operation_digest({'argv': f.instrument(triple), 'stdin': None}))
        self.assertEqual(len(list((self.base / 'lease/claims-v1').glob('*.json'))), 10)
        self.sock = framing.FakeSocket(self.response()); cap = self.capture()
        with self.assertRaises(wire.ClientRefused): cap.shell(f.instrument(f.INSTRUMENTATIONS[0]), 'duplicate')
        self.assertEqual(cap.count, 0); self.assertEqual(self.sock.sent, b'')

    def test_postproof_failure_keeps_real_bytes_unqualified_and_wrong_apk_role_never_streams(self):
        self.fail_proof = {'after'}; cap = self.capture()
        with self.assertRaises(wire.ClientRefused): cap.shell(['getprop', 'sys.boot_completed'], 'boot')
        row = self.record(cap)
        self.assertEqual(row['returncode'], 0); self.assertFalse(row['client_qualified'])
        self.assertEqual(Path(row['stdout']['path']).read_bytes(), b'original\0\x1a\xff\r\n')
        self.assertTrue(self.sock.closed); self.assertFalse(cap.clean)
        self.fail_proof = set(); self.sock = framing.FakeSocket(self.response()); cap = self.capture()
        with self.assertRaises(wire.ClientRefused):
            cap.stream(['dd', 'of=/data/local/tmp/locallore-product-v1.apk', 'bs=65536'], self.a['artifacts']['test_apk'], 'wrong-role', seconds=15)
        self.assertEqual(cap.count, 0); self.assertEqual(self.sock.sent, b'')
