"""SDK8/9 closure compatibility using tiny proof files, never image retirement.

No registry, admission, plan, process query, native acquisition or deletion runs.
Copyright 2026 LocalLore contributors. SPDX-License-Identifier: Apache-2.0
"""
import copy
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from benchmarks import receipt_avd_retirement as retirement
from benchmarks import receipt_avd_storage as storage
from scripts.tests import test_receipt_avd_retirement_fixtures as old

SDK8 = 'owned-emulator-player-presentation-ui-v1'
SDK9 = 'owned-emulator-presentation-process-v1'


class ClosureFiles:
    """Real bounded JSON bindings without TinyRetirement's planner/registry."""
    def __init__(self, protocol, change=None, closure_change=None):
        self.base = Path(tempfile.mkdtemp(prefix='locallore-profile-closure-'))
        assert self.base.drive.upper() == 'D:'
        self.root = self.base / 'synthetic-guest'
        self.root.mkdir()
        self.identities = [dict(pid=9100 + index, creation_filetime=900000 + index,
                                executable=str(self.base / 'historical-python.exe')) for index in range(5)]
        self.proposal = '7' * 64
        self.paths = {role: self.base / (role + '.json') for role in storage.ADAPTER_PROOFS}
        self.proofs = dict(
            admission=dict(version=1, protocol=protocol,
                           guest=dict(root=str(self.root), proposal=dict(sha256=self.proposal))),
            owner_result=dict(status='child_exited', worker_returncode=0,
                              cleanup_complete=True, output_capture_complete=True),
            worker_result=dict(protocol=protocol, worker=self.identities[1], server=self.identities[2],
                               guest=self.identities[4], guest_ancestry=self.identities[3:],
                               cleanup=dict.fromkeys(old.CLEANUP, True)),
            after=dict(owner=self.identities[0], process_handles_closed=True))
        if change is not None:
            change(self.proofs)
        self.write(self.paths['admission'], self.proofs['admission'])
        admitted = storage.binding(self.paths['admission'])
        self.proofs['worker_result']['admission'] = copy.deepcopy(admitted)
        self.proofs['after']['admission'] = copy.deepcopy(admitted)
        for role in ('worker_result', 'owner_result', 'after'):
            self.write(self.paths[role], self.proofs[role])
        closure = dict(proposal_sha256=self.proposal, closure_verified=True, cleanup_complete=True,
                       **{role: storage.binding(path) for role, path in self.paths.items()})
        if closure_change is not None:
            closure_change(closure)
        self.closure_path = self.base / 'guest-storage-closure-v1.json'
        self.write(self.closure_path, closure)
        self.entry = dict(root=str(self.root), proposal_sha256=self.proposal,
                          closure=storage.binding(self.closure_path))

    @staticmethod
    def write(path, value):
        with path.open('xb') as stream:
            stream.write(storage.encoded(value))


@unittest.skipUnless(os.name == 'nt', 'Real tiny D-only bound-file metadata')
class PresentationProcessRetirementTests(unittest.TestCase):
    def extract(self, fixture):
        with patch.object(retirement.windows, '_WindowsApi', side_effect=AssertionError('native API')), \
             patch.object(retirement.windows, 'WindowsImageSet', side_effect=AssertionError('image acquisition')), \
             patch.object(retirement.windows, 'closed_processes', side_effect=AssertionError('process query')), \
             patch.object(storage, 'plan_retirement', side_effect=AssertionError('planning')), \
             patch.object(storage, 'reserve_prepare', side_effect=AssertionError('admission')):
            return retirement._closure(fixture.entry)

    def assert_profile_positive(self, protocol):
        fixture = ClosureFiles(protocol)
        try:
            result = self.extract(fixture)
        except retirement.RetirementRefused as error:
            self.fail('Coherent fixed profile closure refused: ' + error.reason)
        self.assertEqual(result, fixture.identities)
        self.assertEqual(len(result), 5)
        self.assertEqual(set(fixture.proofs['worker_result']['cleanup']), set(old.CLEANUP))
        self.assertFalse((fixture.base / 'ledger-v1.json').exists())
        self.assertFalse((fixture.base / 'admission.lock').exists())

    def refused(self, fixture, reason='closure'):
        with self.assertRaises(retirement.RetirementRefused) as caught:
            self.extract(fixture)
        self.assertEqual(caught.exception.reason, reason)

    def test_closed_sdk8_ui_profile_preserves_exact_five_historical_identities(self):
        self.assert_profile_positive(SDK8)

    def test_closed_sdk9_process_profile_preserves_exact_five_historical_identities(self):
        self.assert_profile_positive(SDK9)

    def test_unknown_lookalike_and_cross_profile_closures_never_reach_native(self):
        for admission, worker in ((SDK8, SDK9), (SDK9, SDK8),
                                  ('unreviewed-profile', 'unreviewed-profile'),
                                  (SDK9.upper(), SDK9.upper()),
                                  (SDK9 + '-extra', SDK9 + '-extra')):
            def change(proofs):
                proofs['admission']['protocol'] = admission
                proofs['worker_result']['protocol'] = worker
            with self.subTest(admission=admission, worker=worker):
                self.refused(ClosureFiles(SDK9, change))

    def test_all_fifteen_cleanup_fields_require_exact_true_for_both_new_profiles(self):
        self.assertEqual(len(old.CLEANUP), 15)
        for protocol in (SDK8, SDK9):
            for field in old.CLEANUP:
                for mode in ('missing', 'false', 'integer'):
                    def change(proofs):
                        cleanup = proofs['worker_result']['cleanup']
                        if mode == 'missing':
                            del cleanup[field]
                        else:
                            cleanup[field] = False if mode == 'false' else 1
                    with self.subTest(protocol=protocol, field=field, mode=mode):
                        self.refused(ClosureFiles(protocol, change))

    def test_all_direct_proofs_are_required_and_current_bytes_cannot_be_replaced(self):
        for protocol in (SDK8, SDK9):
            for role in storage.ADAPTER_PROOFS:
                with self.subTest(protocol=protocol, missing=role):
                    self.refused(ClosureFiles(protocol, closure_change=lambda value: value.pop(role)))
                fixture = ClosureFiles(protocol)
                with fixture.paths[role].open('ab') as stream:
                    stream.write(b'\nchanged stale proof')
                with self.subTest(protocol=protocol, stale=role):
                    with self.assertRaises(storage.StorageRefused) as caught:
                        self.extract(fixture)
                    self.assertEqual(str(caught.exception), 'binding_changed')

    def test_scope_proposal_owner_and_handle_closure_cannot_be_borrowed(self):
        changes = (
            lambda p: p['admission']['guest'].update(root='D:/Synthetic/other-guest'),
            lambda p: p['admission']['guest']['proposal'].update(sha256='8' * 64),
            lambda p: p['owner_result'].update(cleanup_complete=False),
            lambda p: p['owner_result'].update(output_capture_complete=False),
            lambda p: p['owner_result'].update(worker_returncode=True),
            lambda p: p['after'].update(process_handles_closed=False),
        )
        for protocol in (SDK8, SDK9):
            for index, change in enumerate(changes):
                with self.subTest(protocol=protocol, mutation=index):
                    self.refused(ClosureFiles(protocol, change))

    def test_four_original_profiles_keep_exact_legacy_identity_extraction(self):
        for protocol in ('owned-emulator-target-v1', 'owned-emulator-restart-target-v1',
                         'owned-emulator-archive-ui-v1', 'owned-emulator-record-ui-v1'):
            with self.subTest(protocol=protocol):
                self.assert_profile_positive(protocol)


if __name__ == '__main__':
    unittest.main()
