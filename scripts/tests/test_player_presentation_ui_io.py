# Copyright 2026 LocalLore contributors. SPDX-License-Identifier: Apache-2.0
"""Owned tiny-D files and mocked wire only; no live process, socket, SDK or guest."""
import copy
import hashlib
import importlib.machinery
from pathlib import Path
from types import SimpleNamespace
import tempfile
import sys
import unittest
from unittest.mock import patch

from benchmarks import android_process_client_v4 as wire
from benchmarks import android_process_player_presentation_ui_client as client
from benchmarks import android_process_player_presentation_ui_verification as replay
from benchmarks import android_process_record_ui_verification as old_replay
from benchmarks import owned_player_presentation_ui_contract as contract
from benchmarks import owned_player_presentation_ui_owner as owner
from benchmarks import player_presentation_ui_build as build
from scripts.tests import test_record_ui_client as previous
from scripts.tests import test_android_process_client_v4 as framing
from scripts.tests import test_player_presentation_ui_profile as first


def running(value=None):
    result = first.old.legacy.running(first.admission() if value is None else value)
    result['protocol'] = first.PROTOCOL
    return result


def query_bundle(value):
    result = first.old.legacy.query_bundle(value)
    result['protocol'] = first.PROOF
    return result


class PlayerPresentationUiClientTests(unittest.TestCase):
    enter = previous.RecordUiClientTests.enter
    response = previous.RecordUiClientTests.response
    record = previous.RecordUiClientTests.record

    def setUp(self):
        fixture = SimpleNamespace(admission=first.admission, running=running, session=first.session,
                                  query_bundle=query_bundle, SESSION_FILE='sdk-session-v8.json')
        self.enter(patch.object(previous, 'f', fixture))
        self.enter(patch.object(previous, 'owner', SimpleNamespace(LiveOwnedRecordUiTarget=owner.LiveOwnedPlayerPresentationUiTarget)))
        previous.RecordUiClientTests.setUp(self)

    def prove(self, path, session, context, sock, anchor, after=False):
        self.clock += self.proof_cost.get(context['phase'], 0)
        if context['phase'] in self.fail_proof:
            raise ValueError('synthetic post-observation refused')
        value = first.old.legacy.proof(session, after=after)
        value.update(protocol=first.PROOF, context=copy.deepcopy(context), anchor=copy.deepcopy(anchor),
                     session=wire.environment.binding(Path(session['root']) / 'sdk-session-v8.json'))
        queries = path.with_name(path.stem + '-queries-v1.json')
        wire.environment.create_json(queries, query_bundle(session))
        value['queries'] = wire.environment.binding(queries)
        wire.environment.create_json(path, value)
        return wire.environment.binding(path)

    def capture(self):
        self.index += 1
        parent = self.base / ('sdk8-%d' % self.index); parent.mkdir()
        return client.OwnedPlayerPresentationUiSdkCapture(parent / 'clients', 100, self.live)

    def test_actual_fixed_client_preserves_binary_bytes_and_replays_only_as_sdk8(self):
        cap = self.capture()
        raw = b'original\0\x1a\xff\r\n'
        self.assertEqual(cap.shell(['getprop', 'sys.boot_completed'], 'boot'), raw)
        record = self.record(cap)
        self.assertEqual((record['version'], record['protocol']), (8, first.SDK))
        self.assertEqual(Path(record['session']['path']).name, 'sdk-session-v8.json')
        binding = wire.environment.binding(cap.directory / 'command-0001.json')
        self.assertEqual(replay.verify_client_record(binding, cap.session, self.a), record)
        replay.require_current_clients(cap.directory.parent, 1, cap.session_binding, self.a)
        with self.assertRaises(contract.TargetRefused): old_replay.verify_client_record(binding, cap.session, self.a)
        self.assertTrue(self.sock.closed)

    def test_fixed_instrumentation_claim_is_create_only_and_duplicate_dispatch_sends_no_bytes(self):
        triple = first.old.INSTRUMENTATIONS[0]
        cap = self.capture(); cap.shell(first.old.instrument(triple), triple[0])
        claim = wire.environment.read_json(self.base / 'lease/claims-v1' / (triple[0] + '-v1.json'))
        self.assertEqual(claim['protocol'], first.PROTOCOL)
        self.assertEqual(claim['caller'], self.d['worker'])
        self.sock = framing.FakeSocket(self.response()); second = self.capture()
        with self.assertRaises(wire.ClientRefused): second.shell(first.old.instrument(triple), 'again')
        self.assertEqual(self.sock.sent, b''); self.assertEqual(second.count, 0)

    def test_postproof_refusal_retains_actual_raw_bytes_and_never_qualifies_exit_zero(self):
        self.fail_proof = {'after'}; cap = self.capture()
        with self.assertRaises(wire.ClientRefused): cap.shell(['getprop', 'sys.boot_completed'], 'boot')
        record = self.record(cap)
        self.assertEqual(record['returncode'], 0); self.assertFalse(record['client_qualified'])
        self.assertEqual(Path(record['stdout']['path']).read_bytes(), b'original\0\x1a\xff\r\n')
        self.assertTrue(self.sock.closed); self.assertFalse(cap.clean)


class PlayerPresentationUiProductLoaderTests(unittest.TestCase):
    def test_loader_executes_exact_verified_source_and_never_sourcefileloader_cached_code(self):
        root = Path(tempfile.mkdtemp(prefix='locallore-sdk8-product-loader-'))
        folder = root / 'benchmarks'; folder.mkdir()
        source = folder / 'record_ui_build.py'
        raw = (b'from pathlib import Path\nimport sys\nROOT=Path(__file__).parents[1]\n'
               b'if __package__ in (None, ""):\n    sys.path.insert(0,str(ROOT))\nmarker="verified-source"\n')
        source.write_bytes(raw)
        cache = folder / '__pycache__'; cache.mkdir(); (cache / 'record_ui_build.pyc').write_bytes(b'not executable source')
        with patch.object(build, 'PRODUCT_ROOT', root), patch.object(build, 'FROZEN_VERIFIER_SHA256', hashlib.sha256(raw).hexdigest()), \
             patch.object(build, '_product_head'), patch.object(build, '_shared_consumers', return_value={}), \
             patch.object(importlib.machinery.SourceFileLoader, 'exec_module', side_effect=AssertionError('cached loader forbidden')):
            before = list(sys.path)
            module = build._load_verified_product()
            self.assertEqual(module.marker, 'verified-source'); self.assertEqual(module.ROOT, root)
            self.assertEqual(module.__package__, 'benchmarks'); self.assertEqual(sys.path, before)
            source.write_bytes(raw.replace(b'verified-source', b'changed-source'))
            with self.assertRaises(build.BuildRefused): build._load_verified_product()

    def test_shared_lazy_consumers_require_real_equal_bytes_and_expected_module_file(self):
        root = Path(tempfile.mkdtemp(prefix='locallore-sdk8-shared-source-'))
        product, launch = root / 'product', root / 'launcher'
        product.mkdir(); launch.mkdir()
        for parent in (product, launch):
            (parent / 'shared.py').write_bytes(b'# original shared bytes\n')
        with patch.object(build, 'PRODUCT_ROOT', product), patch.object(build, 'LAUNCH_ROOT', launch), \
             patch.object(build, 'SHARED_CONSUMERS', (('synthetic.shared', 'shared.py'),)), \
             patch.object(build.importlib, 'import_module', return_value=SimpleNamespace(__file__=str(launch / 'shared.py'))):
            self.assertEqual(len(build._shared_consumers()), 1)
            (launch / 'shared.py').write_bytes(b'# changed shared bytes\n')
            with self.assertRaises(build.BuildRefused): build._shared_consumers()
            (launch / 'shared.py').write_bytes(b'# original shared bytes\n')
            with patch.object(build.importlib, 'import_module', return_value=SimpleNamespace(__file__=str(product / 'shared.py'))):
                with self.assertRaises(build.BuildRefused): build._shared_consumers()
