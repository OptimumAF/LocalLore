"""Tiny SDK10 closure metadata only; never a registry, image plan or retirement.

Copyright 2026 LocalLore contributors. SPDX-License-Identifier: Apache-2.0
"""
import os
from pathlib import Path
import unittest
from unittest.mock import patch

from benchmarks import receipt_avd_retirement as retirement
from benchmarks import receipt_avd_storage as storage
from scripts.tests.test_presentation_process_runner_retirement import ClosureFiles

PROTOCOL = 'owned-emulator-transcript-ui-v1'


@unittest.skipUnless(os.name == 'nt', 'Tiny ordinary physical D: proof files')
class TranscriptUiRetirementTests(unittest.TestCase):
    def extract(self, fixture):
        with patch.object(retirement.windows, '_WindowsApi', side_effect=AssertionError('native API')), \
             patch.object(retirement.windows, 'WindowsImageSet', side_effect=AssertionError('image handles')), \
             patch.object(retirement.windows, 'closed_processes', side_effect=AssertionError('process query')), \
             patch.object(storage, 'plan_retirement', side_effect=AssertionError('retirement plan')), \
             patch.object(storage, 'reserve_prepare', side_effect=AssertionError('reservation')):
            return retirement._closure(fixture.entry)

    def test_exact_new_protocol_accepts_only_complete_bound_closure_metadata(self):
        fixture = ClosureFiles(PROTOCOL)
        self.assertEqual(self.extract(fixture), fixture.identities)

    def test_unknown_or_borrowed_profile_never_becomes_a_new_protocol(self):
        unknown = ClosureFiles(PROTOCOL + '-foreign')
        with self.assertRaises(retirement.RetirementRefused):
            self.extract(unknown)
        borrowed = ClosureFiles(PROTOCOL, change=lambda proofs:
            proofs['worker_result'].update(protocol='owned-emulator-presentation-process-v1'))
        with self.assertRaises(retirement.RetirementRefused):
            self.extract(borrowed)

    def test_each_unknown_cleanup_flag_keeps_new_profile_unqualified(self):
        baseline = ClosureFiles(PROTOCOL)
        for key in baseline.proofs['worker_result']['cleanup']:
            for unknown in (None, False):
                fixture = ClosureFiles(PROTOCOL, change=lambda proofs, k=key, v=unknown:
                    proofs['worker_result']['cleanup'].update({k: v}))
                with self.subTest(flag=key, value=unknown), self.assertRaises(retirement.RetirementRefused):
                    self.extract(fixture)

    def test_missing_direct_proof_or_changed_original_cannot_qualify(self):
        for role in storage.ADAPTER_PROOFS:
            missing = ClosureFiles(PROTOCOL, closure_change=lambda closure, r=role: closure.pop(r))
            with self.subTest(role=role, variant='missing'), self.assertRaises(retirement.RetirementRefused):
                self.extract(missing)
            changed = ClosureFiles(PROTOCOL)
            with Path(changed.paths[role]).open('ab') as stream:
                stream.write(b'\nSYNTHETIC changed proof')
            with self.subTest(role=role, variant='changed'), self.assertRaises(storage.StorageRefused):
                self.extract(changed)


if __name__ == '__main__':
    unittest.main()
