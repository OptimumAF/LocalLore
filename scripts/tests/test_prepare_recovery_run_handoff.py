"""Later RUN digests preserve preparation recovery history; synthetic host only.

Copyright 2026 LocalLore contributors. SPDX-License-Identifier: Apache-2.0
"""
import copy
import os
from pathlib import Path
import unittest
from scripts.tests import test_prepare_recovery_adversaries as fixtures
from benchmarks import receipt_avd_storage as storage
from benchmarks import prepare_recovery_contract as contract


@unittest.skipUnless(os.name == 'nt', 'D-only Windows preparation protocol')
class RecoveryRunHandoffTests(unittest.TestCase):
    def setUp(self):
        self.fixture = fixtures.PrepareRecoveryAdversaries()
        self.addCleanup(self.fixture.doCleanups)
        self.fixture.setUp()

    def test_run_digest_changes_without_rewriting_prepare_history_or_corrupting_state(self):
        f = self.fixture
        f.successful()
        prepared = f.entry()
        prepare_sha = prepared['proposal_sha256']
        reference = copy.deepcopy(prepared['recovery'])
        run_sha = 'd' * 64
        self.assertNotEqual(prepare_sha, run_sha)
        storage.record_state(f.root, 'retained', registry=f.registry, proposal_sha256=run_sha)
        retained = f.entry()
        storage._validate(f.ledger(), f.registry)
        self.assertEqual(retained['proposal_sha256'], run_sha)
        self.assertEqual(retained['reserved_bytes'], storage.RESERVATION_BYTES)
        self.assertEqual(retained['recovery'], reference)
        completion = storage.read_json(reference['completion']['path'])
        outcome = storage.read_json(reference['outcome']['path'])
        self.assertEqual(completion['proposal']['sha256'], prepare_sha)
        self.assertEqual(outcome['proposal_sha256'], prepare_sha)
        closure = f.root / 'synthetic-run-closure.json'
        f.write(closure, dict(proposal_sha256=run_sha, closure_verified=True, cleanup_complete=True))
        storage.record_closed(f.root, closure, registry=f.registry)
        closed = f.entry()
        storage._validate(f.ledger(), f.registry)
        self.assertEqual(closed['proposal_sha256'], run_sha)
        self.assertEqual(closed['recovery'], reference)
        expected = storage._logical_bytes(list(storage._files(f.root).values()) +
                                         contract.history_paths(closed) + [Path(closure)])
        self.assertEqual(closed['reserved_bytes'], expected)
        self.assertEqual(storage._charge(closed), expected)
        # Returning a RUN digest to 'prepared' would contradict its historical
        # prepare binding. Refusal must preserve the previously valid ledger.
        before = f.ledger_bytes()
        with self.assertRaises(storage.StorageRefused):
            storage.record_state(f.root, 'prepared', registry=f.registry)
        self.assertEqual(f.ledger_bytes(), before)
        storage._validate(f.ledger(), f.registry)
        f.assert_old_evidence()
