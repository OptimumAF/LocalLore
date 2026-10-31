# Copyright 2026 LocalLore contributors. SPDX-License-Identifier: Apache-2.0
"""FIRST pure SDK7 authority oracles. Missing modules are setup, not RED."""
import copy
from pathlib import Path
import socket
import unittest
from unittest.mock import patch

from benchmarks import owned_record_ui_contract as c
from benchmarks import owned_target_contract as legacy
from benchmarks import owned_ui_contract as archive
from scripts.tests import test_archive_ui_fixtures as old
from scripts.tests import test_record_ui_fixtures as f


class RecordUiContractTests(unittest.TestCase):
    def refused(self, call):
        with self.assertRaises(c.TargetRefused): call()

    def test_fixed_sdk7_selectors_protocol_and_profile_cannot_be_chosen_by_admission(self):
        self.assertEqual((c.PROTOCOL, c.SDK_PROTOCOL, c.PROOF_PROTOCOL), (f.PROTOCOL, f.SDK_PROTOCOL, f.PROOF_PROTOCOL))
        self.assertEqual((c.CLIENT_VERSION, c.SESSION_FILE), (7, f.SESSION_FILE))
        self.assertEqual(c.OWNER_SCRIPT, 'owned_record_ui_owner.py')
        self.assertEqual(c.BOOT_CLAIM_FILE, 'owned-record-ui-boot-claim-v1.json')
        self.assertEqual(c.GUEST_ROOT, f.GUEST_ROOT)
        self.assertEqual((c.APP, c.TEST, set(c.ARTIFACT_KEYS)), (f.APP, f.TEST, {'build', 'product_apk', 'test_apk'}))
        self.assertEqual(tuple(c.INSTRUMENTATIONS), f.INSTRUMENTATIONS)
        self.assertEqual(tuple(c.CLAIM_KINDS), tuple(row[0] for row in f.INSTRUMENTATIONS))
        self.assertEqual(c.SOURCE_NAMES, f.SOURCE_NAMES)
        value = f.admission(); original = copy.deepcopy(value)
        with patch.object(Path, 'open', side_effect=AssertionError('file IO')), patch.object(Path, 'stat', side_effect=AssertionError('stat IO')), patch.object(socket, 'socket', side_effect=AssertionError('socket IO')):
            decoded = c.validate_admission(value)
        self.assertEqual(decoded, original); decoded['sources'].clear(); self.assertEqual(value, original)
        for name in ('profile', 'module', 'selectors', 'verifier'):
            bad = f.admission(); bad[name] = 'caller-selected'
            with self.subTest(name=name): self.refused(lambda: c.validate_admission(bad))

    def test_archive_and_model_profiles_cannot_cross_retag_or_lose_required_model_material(self):
        self.refused(lambda: c.validate_admission(old.admission()))
        self.refused(lambda: archive.validate_admission(f.admission()))
        self.refused(lambda: legacy.validate_admission(f.admission()))
        for extra in ('model', 'probe', 'process_probe'):
            bad = f.admission(); bad['artifacts'][extra] = f.legacy.pin('D:/Synthetic/' + extra)
            with self.subTest(extra=extra): self.refused(lambda: c.validate_admission(bad))
        for missing in ('model', 'probe'):
            bad = f.legacy.admission(); del bad['artifacts'][missing]
            with self.subTest(missing=missing): self.refused(lambda: legacy.validate_admission(bad))
        self.assertTrue(legacy._legacy_spec().MODEL_MATERIAL)
        bad = old.admission(); bad['protocol'] = f.PROTOCOL; bad['guest']['root'] = str(f.GUEST_ROOT)
        self.refused(lambda: c.validate_admission(bad))  # Old source closure is not the new code profile.

    def test_only_exact_record_instrumentation_and_own_package_paths_are_commands(self):
        admission = f.admission()
        for triple in f.INSTRUMENTATIONS:
            operation = {'argv': f.instrument(triple), 'stdin': None}
            self.assertEqual(c.instrumentation_kind(operation['argv']), triple[0])
            self.assertEqual(c.validate_operation(operation, admission), operation)
            for selector in (triple[1] + '#unknown', 'foreign.Class#' + triple[2]):
                bad = copy.deepcopy(operation); bad['argv'][6] = selector
                with self.subTest(selector=selector): self.refused(lambda: c.validate_operation(bad, admission))
        for triple in old.INSTRUMENTATIONS:
            self.refused(lambda: c.validate_operation({'argv': old.instrument(triple), 'stdin': None}, admission))
        for argv in (['sh', '-c', 'id'], ['run-as', f.APP, '--user', '0', 'ls', 'files'], ['df', '-k', '/data'],
                     ['getprop', 'ro.serialno'], ['sha256sum', '/data/app/~~x/unrelated.app-x/base.apk']):
            with self.subTest(argv=argv): self.refused(lambda: c.validate_operation({'argv': argv, 'stdin': None}, admission))

    def test_apk_transfer_has_exact_role_bytes_and_no_path_or_input_escape(self):
        admission = f.admission()
        for role, remote in (('product_apk', '/data/local/tmp/locallore-product-v1.apk'), ('test_apk', '/data/local/tmp/locallore-test-v1.apk')):
            source = admission['artifacts'][role]
            operation = {'argv': ['dd', 'of=' + remote, 'bs=65536'], 'stdin': source}
            self.assertEqual(c.validate_operation(operation, admission), operation)
            for wrong in (None, admission['artifacts']['build'], dict(source, sha256='0' * 64)):
                self.refused(lambda: c.validate_operation(dict(operation, stdin=wrong), admission))
            bad = copy.deepcopy(operation); bad['argv'][1] += '/../escape'
            self.refused(lambda: c.validate_operation(bad, admission))

    def test_session_and_claims_require_exact_source_caller_deadline_and_profile(self):
        admission = f.admission(); session = f.session(admission)
        self.assertEqual(c.validate_session(session, admission), session)
        for change in (lambda row: row.update(protocol=old.SDK_PROTOCOL), lambda row: row['sources'][0].update(sha256='0' * 64),
                       lambda row: row['caller'].update(pid=row['descriptor']['guest']['pid']), lambda row: row.update(seconds=True),
                       lambda row: row.update(deadline_epoch=row['deadline_epoch'] + 1)):
            bad = copy.deepcopy(session); change(bad)
            self.refused(lambda: c.validate_session(bad, admission))
        triple = f.INSTRUMENTATIONS[0]; digest = c.operation_digest({'argv': f.instrument(triple), 'stdin': None})
        claim = c.claim_record(session['admission'], session['caller'], triple[0], digest)
        self.assertEqual(c.validate_claim(claim, session['admission'], session['caller'], triple[0], digest), claim)
        for change in (lambda row: row.update(protocol=old.PROTOCOL), lambda row: row.update(kind=old.INSTRUMENTATIONS[0][0]),
                       lambda row: row['caller'].update(creation_filetime=row['caller']['creation_filetime'] + 1),
                       lambda row: row.update(operation_sha256='0' * 64), lambda row: row.update(version=True)):
            bad = copy.deepcopy(claim); change(bad)
            self.refused(lambda: c.validate_claim(bad, session['admission'], session['caller'], triple[0], digest))
