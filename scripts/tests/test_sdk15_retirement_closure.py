"""Original SDK15 retirement-proof oracles over retained tiny synthetic ledgers.

No test executes retirement, launches a process, or touches a production ledger.
Copyright 2026 LocalLore contributors. SPDX-License-Identifier: Apache-2.0
"""
import contextlib
import copy
import hashlib
from pathlib import Path
import unittest
from unittest.mock import patch

from benchmarks import receipt_avd_retirement as retirement
from benchmarks import receipt_avd_storage as storage
from scripts.tests import test_receipt_avd_retirement_fixtures as fixtures


HOME = Path('D:/Dev/Experiments/LocalLore/2026-11-02-knowledge-prepare-inputs-v1/test-agent-v1/retirement-fixtures')
SDK15 = 'owned-emulator-library-ui-v1'
SDK14 = 'owned-emulator-record-controls-ui-v1'
SDK16 = 'owned-emulator-knowledge-ui-v1'


@unittest.skipUnless(HOME.drive.upper() == 'D:', 'requires physical D: fixtures')
class Sdk15RetirementClosureTests(unittest.TestCase):
    def make_fixture(self, change=None):
        HOME.mkdir(parents=True, exist_ok=True)
        self.assertEqual(HOME.resolve().drive.upper(), 'D:')
        original_mkdtemp = fixtures.tempfile.mkdtemp

        def retained_directory(*args, **kwargs):
            self.assertNotIn('dir', kwargs)
            return original_mkdtemp(*args, dir=str(HOME), **kwargs)

        def sdk15(proofs):
            proofs['admission']['protocol'] = SDK15
            proofs['worker_result']['protocol'] = SDK15
            if change is not None:
                change(proofs)
            # TinyRetirement intentionally preserves caller-supplied bindings.
            # Compute the final admission pin before its final serialization;
            # malformed semantic records therefore still have fresh bindings.
            raw = storage.encoded(proofs['admission'])
            pin = dict(path=proofs['worker_result']['admission']['path'],
                       bytes=len(raw), sha256=hashlib.sha256(raw).hexdigest())
            proofs['worker_result']['admission'] = copy.deepcopy(pin)
            proofs['after']['admission'] = copy.deepcopy(pin)

        with patch.object(fixtures.tempfile, 'mkdtemp', side_effect=retained_directory):
            return fixtures.TinyRetirement(change=sdk15)

    def refused(self, fixture):
        with self.assertRaises(retirement.RetirementRefused):
            retirement._closure(fixture.entry())
        with self.assertRaises(retirement.RetirementRefused):
            retirement._preflight(fixture.plan, fixture.entry())
        self.assertEqual(fixture.entry()['state'], 'closed')
        for image in fixture.images:
            self.assertTrue(image.is_file(), 'semantic inspection must not remove an image')

    def test_sdk15_closed_proof_deduplicates_guest_and_preflights_without_mutation(self):
        fixture = self.make_fixture()
        before = {p: p.read_bytes() for p in fixture.base.rglob('*') if p.is_file()}
        identities = retirement._closure(fixture.entry())
        self.assertEqual(identities, fixture.identities)
        self.assertEqual(len(identities), 5)
        self.assertEqual(len({item['pid'] for item in identities}), 5)
        root, preflight_identities = retirement._preflight(fixture.plan, fixture.entry())
        self.assertEqual(root, fixture.root)
        self.assertEqual(preflight_identities, identities)
        self.assertEqual({p: p.read_bytes() for p in fixture.base.rglob('*') if p.is_file()}, before)
        self.assertFalse(fixture.output.exists())

    def test_sdk14_still_valid_but_mixed_protocols_and_unrun_sdk16_refuse(self):
        fixture = self.make_fixture(lambda p: (
            p['admission'].update(protocol=SDK14), p['worker_result'].update(protocol=SDK14)))
        self.assertEqual(retirement._closure(fixture.entry()), fixture.identities)
        changes = (
            lambda p: p['admission'].update(protocol=SDK14),
            lambda p: p['worker_result'].update(protocol=SDK14),
            lambda p: (p['admission'].update(protocol=SDK16),
                       p['worker_result'].update(protocol=SDK16)),
        )
        for change in changes:
            with self.subTest(change=changes.index(change)):
                self.refused(self.make_fixture(change))

    def test_each_worker_cleanup_fact_and_owner_after_capture_fact_must_be_true(self):
        for key in fixtures.CLEANUP:
            with self.subTest(worker_cleanup=key):
                self.refused(self.make_fixture(
                    lambda p, key=key: p['worker_result']['cleanup'].__setitem__(key, False)))
        changes = (
            lambda p: p['owner_result'].update(cleanup_complete=False),
            lambda p: p['owner_result'].update(output_capture_complete=False),
            lambda p: p['after'].update(process_handles_closed=False),
            lambda p: p['worker_result']['cleanup'].pop('guest_wait_completed'),
            lambda p: p['worker_result']['cleanup'].update(unrecognized_cleanup=True),
            lambda p: p['worker_result']['cleanup'].update(guest_wait_completed=1),
        )
        for index, change in enumerate(changes):
            with self.subTest(closure_fact=index):
                self.refused(self.make_fixture(change))

    def test_owner_returncode_is_concrete_integer_and_owner_must_have_exited(self):
        for value in (False, True, None, '0', 0.0):
            with self.subTest(returncode=value):
                self.refused(self.make_fixture(lambda p, value=value:
                    p['owner_result'].update(worker_returncode=value)))
        self.refused(self.make_fixture(lambda p: p['owner_result'].update(status='running')))

    def test_ancestry_must_be_nonempty_bounded_list_of_complete_identities(self):
        for ancestry in ([], {}, [None], [{'pid': 8123}], [None] * 33):
            with self.subTest(ancestry=ancestry):
                self.refused(self.make_fixture(lambda p, ancestry=ancestry:
                    p['worker_result'].update(guest_ancestry=ancestry)))

    def test_colliding_pid_cannot_hide_changed_creation_or_executable_or_boolean_identity(self):
        changes = (
            lambda p: p['worker_result']['guest_ancestry'].append(
                dict(p['worker_result']['guest'], creation_filetime=999999)),
            lambda p: p['worker_result']['guest_ancestry'].append(
                dict(p['worker_result']['guest'], executable='D:/synthetic/borrowed.exe')),
            lambda p: p['worker_result']['worker'].update(pid=True),
            lambda p: p['after']['owner'].update(creation_filetime=True),
            lambda p: p['worker_result']['server'].update(executable='relative.exe'),
        )
        for index, change in enumerate(changes):
            with self.subTest(identity=index):
                self.refused(self.make_fixture(change))

    def test_admission_cannot_borrow_other_root_or_proposal_even_with_fresh_hashes(self):
        changes = (
            lambda p: p['admission']['guest'].update(root=str(HOME/'another-guest')),
            lambda p: p['admission']['guest']['proposal'].update(sha256='8' * 64),
            lambda p: p['admission']['guest'].update(proposal=None),
        )
        for index, change in enumerate(changes):
            with self.subTest(admission=index):
                self.refused(self.make_fixture(change))

    def test_plan_closure_and_bound_admission_cannot_be_substituted_after_review(self):
        fixture = self.make_fixture()
        original = copy.deepcopy(fixture.plan)
        for field, value in (('root', str(HOME/'another-guest')),
                             ('proposal_sha256', '8' * 64)):
            plan = copy.deepcopy(original)
            plan[field] = value
            with self.subTest(plan_field=field), self.assertRaises(retirement.RetirementRefused):
                retirement._preflight(plan, fixture.entry())
        plan = copy.deepcopy(original)
        plan['closure']['sha256'] = '0' * 64
        with self.assertRaises(retirement.RetirementRefused):
            retirement._preflight(plan, fixture.entry())
        # Keep this changed proof as failed evidence. Its reviewed binding must
        # reject; this oracle deliberately differs from the fresh-hash cases.
        fixture.write(fixture.proof_paths['admission'], dict(fixture.proofs['admission'], protocol=SDK14))
        with self.assertRaises((retirement.RetirementRefused, storage.StorageRefused)):
            retirement._closure(fixture.entry())

    def test_absent_or_nonboolean_consent_precedes_json_native_and_filesystem_io(self):
        for flag in (False, None, 0, 1, 'true', []):
            with self.subTest(consent=flag), contextlib.ExitStack() as stack:
                reader = stack.enter_context(patch.object(retirement, '_json',
                    side_effect=AssertionError('consent must precede JSON reads')))
                native = stack.enter_context(patch.object(retirement.windows, 'WindowsImageSet',
                    side_effect=AssertionError('consent must precede native operations')))
                for method in ('resolve', 'open', 'stat', 'lstat', 'mkdir', 'unlink'):
                    stack.enter_context(patch.object(Path, method,
                        side_effect=AssertionError('consent must precede filesystem IO')))
                for call in (
                    lambda: retirement.execute({}, str(HOME/'never-output'), execute_reviewed_plan=flag),
                    lambda: retirement._execute({}, str(HOME/'never-output'), str(HOME/'never-registry'),
                                                execute_reviewed_plan=flag),
                ):
                    with self.assertRaises(retirement.RetirementRefused) as error:
                        call()
                    self.assertEqual(error.exception.reason, 'not_authorized')
                reader.assert_not_called()
                native.assert_not_called()


if __name__ == '__main__':
    unittest.main()
