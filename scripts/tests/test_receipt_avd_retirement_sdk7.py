"""Fixed SDK7 closure compatibility over tiny isolated, mock-native D fixtures.

No real guest, process ownership, image or production registry is exercised.
Copyright 2026 LocalLore contributors. SPDX-License-Identifier: Apache-2.0
"""
import copy
import os
from pathlib import Path
import unittest
from unittest.mock import patch

from benchmarks import receipt_avd_retirement as retirement
from benchmarks import receipt_avd_storage as storage
from scripts.tests import test_receipt_avd_retirement_fixtures as f

SDK7 = 'owned-emulator-record-ui-v1'


def profile(proofs, *, admission=SDK7, worker=SDK7):
    """Rebind actual tiny JSON bytes so profile checks, not stale pins, are causal."""
    proofs['admission']['protocol'] = admission
    proofs['worker_result']['protocol'] = worker
    path = Path(proofs['worker_result']['admission']['path'])
    path.write_bytes(storage.encoded(proofs['admission']))
    bound = storage.binding(path)
    proofs['worker_result']['admission'] = bound
    proofs['after']['admission'] = copy.deepcopy(bound)


@unittest.skipUnless(os.name == 'nt', 'Tiny D-only synthetic retirement registry')
class RetirementSdk7Tests(unittest.TestCase):
    def assert_before_native(self, fixture):
        originals = [path.read_bytes() for path in fixture.images]
        with patch.object(retirement.windows, 'WindowsImageSet', side_effect=AssertionError('native acquisition')) as images, \
             patch.object(retirement.windows, 'closed_processes', side_effect=AssertionError('native process query')) as processes, \
             patch.object(storage, '_record_retired_locked', side_effect=AssertionError('finalization')) as finalizer:
            result = retirement._execute(fixture.plan_binding, fixture.output, fixture.registry, execute_reviewed_plan=True)
        self.assertEqual(result['outcome'], 'refused')
        self.assertEqual(result['phase'], 'admission')
        self.assertEqual(result['reason'], 'closure')
        self.assertEqual(result['attempted_count'], 0)
        self.assertEqual(result['marked_count'], 0)
        self.assertIs(result['cleanup_known'], True)
        self.assertIs(result['retirement_recorded'], False)
        images.assert_not_called(); processes.assert_not_called(); finalizer.assert_not_called()
        self.assertEqual([path.read_bytes() for path in fixture.images], originals)
        fixture.assert_closed_charge(self)
        self.assertFalse((fixture.registry / 'admission.lock').exists())

    def test_coherent_sdk7_closure_extracts_exact_historical_identities_without_native_calls(self):
        fixture = f.TinyRetirement(profile)
        with patch.object(retirement.windows, '_WindowsApi', side_effect=AssertionError('native API')):
            try:
                identities = retirement._closure(fixture.entry())
            except retirement.RetirementRefused as error:
                self.fail('Coherent fixed SDK7 closure refused: ' + error.reason)
        self.assertEqual(identities, fixture.identities)
        self.assertEqual(len(identities), 5)
        self.assertEqual(set(fixture.proofs['worker_result']['cleanup']), set(f.CLEANUP))
        self.assertTrue(all(value is True for value in fixture.proofs['worker_result']['cleanup'].values()))

    def test_sdk7_exact_plan_completes_only_through_existing_mock_native_ownership_and_finalizer(self):
        fixture = f.TinyRetirement(profile)
        fake = f.FakeNative(fixture, retirement.windows.RetirementWindowsError)
        with patch.object(retirement.windows, 'WindowsImageSet', fake.ImageSet), \
             patch.object(retirement.windows, 'closed_processes', side_effect=fake.processes):
            result = retirement._execute(fixture.plan_binding, fixture.output, fixture.registry, execute_reviewed_plan=True)
        self.assertEqual(result['outcome'], 'completed')
        self.assertEqual(result['attempted_count'], 2)
        self.assertEqual(result['marked_count'], 2)
        self.assertIs(result['cleanup_known'], True)
        self.assertIs(result['retirement_recorded'], True)
        self.assertEqual(fake.events[:2], ['acquire-all', 'processes'])
        self.assertEqual(fake.process_inputs, fixture.identities)
        self.assertEqual(fake.instances[0].close_calls, 1)
        self.assertEqual(fixture.entry()['state'], 'retired')
        self.assertTrue(all(not path.exists() for path in fixture.images))
        self.assertEqual(storage._charge(fixture.entry()), fixture.expected_retained_charge())
        self.assertGreater(fixture.expected_retained_charge(), 0)

    def test_cross_profile_unknown_and_lookalike_sdk7_closures_refuse_before_native(self):
        variants = (
            ('owned-emulator-archive-ui-v1', SDK7),
            (SDK7, 'owned-emulator-archive-ui-v1'),
            ('unreviewed-profile', 'unreviewed-profile'),
            (SDK7.upper(), SDK7.upper()),
            (SDK7 + '-extra', SDK7 + '-extra'),
        )
        for admission, worker in variants:
            with self.subTest(admission=admission, worker=worker):
                fixture = f.TinyRetirement(lambda proofs: profile(proofs, admission=admission, worker=worker))
                self.assert_before_native(fixture)

    def test_every_sdk7_cleanup_field_is_required_and_true_before_native(self):
        for field in f.CLEANUP:
            for variant in ('missing', 'false'):
                def changed(proofs):
                    profile(proofs)
                    if variant == 'missing': del proofs['worker_result']['cleanup'][field]
                    else: proofs['worker_result']['cleanup'][field] = False
                with self.subTest(field=field, variant=variant):
                    self.assert_before_native(f.TinyRetirement(changed))

    def test_all_three_legacy_profiles_retain_their_existing_identity_extraction(self):
        for protocol in ('owned-emulator-target-v1', 'owned-emulator-restart-target-v1', 'owned-emulator-archive-ui-v1'):
            with self.subTest(protocol=protocol):
                fixture = f.TinyRetirement(lambda proofs: profile(proofs, admission=protocol, worker=protocol))
                with patch.object(retirement.windows, '_WindowsApi', side_effect=AssertionError('native API')):
                    self.assertEqual(retirement._closure(fixture.entry()), fixture.identities)


if __name__ == '__main__':
    unittest.main()
