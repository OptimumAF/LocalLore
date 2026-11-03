"""SDK17 shared-ledger dependency controls in tiny isolated D: registries.

These are synthetic metadata, not guests, run grants or production admission.
Copyright 2026 LocalLore contributors. SPDX-License-Identifier: Apache-2.0
"""
import json
import os
from pathlib import Path
import tempfile
import unittest

from benchmarks import receipt_avd_storage as storage


@unittest.skipUnless(os.name == 'nt', 'Physical D: storage guard')
class DiagnosticUiStorageTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix='sdk17-ledger-metadata-')
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.assertEqual(self.root.drive.upper(), 'D:')
        self.registry = self.root / 'synthetic-registry'
        self.registry.mkdir()
        self.ledger = self.registry / 'ledger-v1.json'
        # Literal user-policy values; not generated from implementation constants.
        value = dict(version=2, max_guests=2, budget_bytes=64 * 1024**3,
                     reservation_bytes=40 * 1024**3, entries=[])
        self.ledger.write_bytes(storage.encoded(value))

    def test_schema_v2_readonly_preview_preserves_ledger_and_grants_no_admission(self):
        before = self.ledger.read_bytes()
        guest = self.root / 'never-created-guest'
        result = storage.preview_prepare(guest, self.registry)
        self.assertIs(result['would_fit'], True)
        self.assertIs(result['admission_granted'], False)
        self.assertEqual(result['projected_bytes'], 40 * 1024**3)
        self.assertEqual(result['active_count'], 0)
        self.assertEqual(self.ledger.read_bytes(), before)
        self.assertFalse(guest.exists())

    def test_schema_v2_second_live_reservation_refuses_eighty_gib_without_sdk_or_root(self):
        first, second = self.root / 'first-metadata-root', self.root / 'second-metadata-root'
        storage.reserve_prepare(first, 'a' * 64, self.registry)
        before = self.ledger.read_bytes()
        saved = json.loads(before)
        self.assertEqual(saved['version'], 2)
        self.assertIsNone(saved['entries'][0]['recovery'])
        result = storage.preview_prepare(second, self.registry)
        self.assertEqual(result['active_count'], 1)
        self.assertEqual(result['charged_bytes'], 40 * 1024**3)
        self.assertEqual(result['projected_bytes'], 80 * 1024**3)
        self.assertIs(result['root_limit_exceeded'], False)
        self.assertIs(result['byte_limit_exceeded'], True)
        self.assertIs(result['would_fit'], False)
        self.assertIs(result['admission_granted'], False)
        with self.assertRaisesRegex(storage.StorageRefused, '^storage_capacity_exceeded$'):
            storage.reserve_prepare(second, 'b' * 64, self.registry)
        self.assertEqual(self.ledger.read_bytes(), before)
        self.assertFalse(first.exists())
        self.assertFalse(second.exists())
