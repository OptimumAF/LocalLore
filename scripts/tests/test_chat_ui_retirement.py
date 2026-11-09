"""SDK11 closure metadata only; no image, process or shared-ledger operation.

Copyright 2026 LocalLore contributors. SPDX-License-Identifier: Apache-2.0
"""
from contextlib import ExitStack
import os
from pathlib import Path
import unittest
from unittest.mock import patch

from benchmarks import owned_chat_ui_contract as contract
from benchmarks import receipt_avd_retirement as retirement
from benchmarks import receipt_avd_storage as storage
from scripts.tests.test_presentation_process_runner_retirement import ClosureFiles

PROTOCOL = 'owned-emulator-current-chat-ui-v1'
OLD_PROTOCOL = 'owned-emulator-transcript-ui-v1'


@unittest.skipUnless(os.name == 'nt', 'Ordinary synthetic D: metadata files')
class ChatUiRetirementTests(unittest.TestCase):
    def extract(self, fixture):
        with ExitStack() as stack:
            denied = [stack.enter_context(patch.object(module, name,
                       side_effect=AssertionError('No native, registry or image action')))
                      for module, name in (
                          (retirement.windows, '_WindowsApi'),
                          (retirement.windows, 'WindowsImageSet'),
                          (retirement.windows, 'closed_processes'),
                          (storage, 'reserve_prepare'),
                          (storage, 'plan_retirement'),
                          (storage, 'record_retired'),
                      )]
            try:
                return retirement._closure(fixture.entry)
            finally:
                for action in denied:
                    action.assert_not_called()

    def assert_coherent(self, fixture):
        try:
            identities = self.extract(fixture)
        except retirement.RetirementRefused as error:
            self.fail('Complete SDK11 closure metadata refused: ' + error.reason)
        self.assertEqual(identities, fixture.identities)
        self.assertEqual(len(identities), 5)
        self.assertFalse((fixture.base / 'ledger-v1.json').exists())
        self.assertFalse((fixture.base / 'admission.lock').exists())

    def test_exact_sdk11_closed_metadata_keeps_all_five_historical_identities(self):
        self.assertEqual(contract.PROTOCOL, PROTOCOL)
        self.assertEqual(len(contract.CLEANUP_KEYS), 15)
        self.assert_coherent(ClosureFiles(PROTOCOL))

    def test_known_failed_feature_exit_is_still_only_closed_metadata(self):
        # Image retirement needs known closure, not a claim that UI tests passed.
        fixture = ClosureFiles(PROTOCOL, change=lambda proofs:
            proofs['owner_result'].update(worker_returncode=17))
        self.assert_coherent(fixture)

    def test_foreign_lookalikes_and_cross_sdk10_records_cannot_borrow_the_new_name(self):
        for unknown in (PROTOCOL.upper(), PROTOCOL + '-extra', PROTOCOL + '-foreign'):
            with self.subTest(protocol=unknown), self.assertRaises(retirement.RetirementRefused):
                self.extract(ClosureFiles(unknown))
        for admission, worker in ((PROTOCOL, OLD_PROTOCOL), (OLD_PROTOCOL, PROTOCOL)):
            def change(proofs):
                proofs['admission']['protocol'] = admission
                proofs['worker_result']['protocol'] = worker
            with self.subTest(admission=admission, worker=worker), self.assertRaises(retirement.RetirementRefused):
                self.extract(ClosureFiles(PROTOCOL, change=change))

    def test_all_fifteen_cleanup_fields_require_boolean_true(self):
        for key in contract.CLEANUP_KEYS:
            for value in (None, False, 1, 'true'):
                fixture = ClosureFiles(PROTOCOL, change=lambda proofs, k=key, v=value:
                    proofs['worker_result']['cleanup'].update({k: v}))
                with self.subTest(flag=key, value=value), self.assertRaises(retirement.RetirementRefused):
                    self.extract(fixture)

    def test_missing_and_changed_direct_proofs_refuse_before_native_access(self):
        for role in storage.ADAPTER_PROOFS:
            missing = ClosureFiles(PROTOCOL, closure_change=lambda value, r=role: value.pop(r))
            with self.subTest(role=role, kind='missing'), self.assertRaises(retirement.RetirementRefused):
                self.extract(missing)
            changed = ClosureFiles(PROTOCOL)
            with Path(changed.paths[role]).open('ab') as stream:
                stream.write(b'\nSYNTHETIC changed proof')
            with self.subTest(role=role, kind='changed'), self.assertRaises(storage.StorageRefused):
                self.extract(changed)

    def test_unknown_owner_terminal_capture_or_boolean_return_code_refuses(self):
        cases = (
            ('status', 'unknown'), ('cleanup_complete', False),
            ('output_capture_complete', False), ('worker_returncode', True),
        )
        for key, value in cases:
            fixture = ClosureFiles(PROTOCOL, change=lambda proofs, k=key, v=value:
                proofs['owner_result'].update({k: v}))
            with self.subTest(field=key, value=value), self.assertRaises(retirement.RetirementRefused):
                self.extract(fixture)


if __name__ == '__main__':
    unittest.main()
