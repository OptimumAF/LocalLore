"""Independent SDK9 FIRST contracts. Missing implementation is setup, not RED.

Copyright 2026 LocalLore contributors. SPDX-License-Identifier: Apache-2.0
"""
import copy
from pathlib import Path
import socket
import subprocess
import unittest
from unittest.mock import patch

from benchmarks import owned_presentation_process_contract as contract
from benchmarks import owned_target_contract as old4
from benchmarks import owned_record_ui_contract as old7
from benchmarks import owned_player_presentation_ui_contract as old8
from scripts.tests import test_record_ui_fixtures as record_f
from scripts.tests import test_presentation_process_runner_fixtures as f


class PresentationProcessRunnerContractTests(unittest.TestCase):
    def refused(self, operation):
        with self.assertRaises(contract.TargetRefused):
            operation()

    def test_fixed_model_free_sdk9_profile_has_one_external_claim_and_no_junit_selectors(self):
        self.assertEqual((contract.PROTOCOL, contract.SDK_PROTOCOL, contract.PROOF_PROTOCOL),
                         (f.PROTOCOL, f.SDK_PROTOCOL, f.PROOF_PROTOCOL))
        self.assertEqual((contract.CLIENT_VERSION, contract.SESSION_FILE), (9, 'sdk-session-v9.json'))
        self.assertEqual(contract.OWNER_SCRIPT, 'owned_presentation_process_owner.py')
        self.assertEqual(contract.BOOT_CLAIM_FILE, 'owned-presentation-process-boot-claim-v1.json')
        self.assertEqual(contract.GUEST_ROOT, f.GUEST_ROOT)
        self.assertEqual((contract.APP, contract.TEST, contract.CONTROL), (f.APP, f.TEST, f.CONTROL))
        self.assertFalse(contract.MODEL_MATERIAL)
        self.assertEqual(tuple(contract.INSTRUMENTATIONS), ())
        self.assertEqual(tuple(contract.CLAIM_KINDS), ('presentation_process',))
        self.assertEqual(set(contract.ARTIFACT_KEYS), {'build', 'product_apk', 'test_apk', 'controller_apk'})
        value = f.admission(contract)
        original = copy.deepcopy(value)
        with patch.object(Path, 'open', side_effect=AssertionError('unexpected file IO')), \
             patch.object(Path, 'stat', side_effect=AssertionError('unexpected metadata IO')), \
             patch.object(socket, 'socket', side_effect=AssertionError('unexpected socket')), \
             patch.object(subprocess, 'Popen', side_effect=AssertionError('unexpected process')):
            decoded = contract.validate_admission(value)
        self.assertEqual(decoded, original)
        decoded['artifacts'].clear()
        self.assertEqual(value, original)

    def test_admission_cannot_select_a_profile_drop_the_third_apk_or_retag_old_sources(self):
        for key in ('profile', 'module', 'selectors', 'verifier', 'controller'):
            bad = f.admission(contract)
            bad[key] = 'caller-selected'
            self.refused(lambda: contract.validate_admission(bad))
        for role in ('build', 'product_apk', 'test_apk', 'controller_apk'):
            bad = f.admission(contract)
            del bad['artifacts'][role]
            self.refused(lambda: contract.validate_admission(bad))
        for role in ('model', 'probe', 'process_probe'):
            bad = f.admission(contract)
            bad['artifacts'][role] = f.legacy.pin('D:/Synthetic/' + role)
            self.refused(lambda: contract.validate_admission(bad))
        old = record_f.admission()
        self.refused(lambda: contract.validate_admission(old))
        old['protocol'] = f.PROTOCOL
        old['guest']['root'] = str(f.GUEST_ROOT)
        old['artifacts']['controller_apk'] = f.legacy.pin('D:/Synthetic/controller-debug.apk')
        self.refused(lambda: contract.validate_admission(old))
        for reader in (old4, old7, old8):
            with self.assertRaises(reader.TargetRefused):
                reader.validate_admission(f.admission(contract))
        self.assertTrue(old4._legacy_spec().MODEL_MATERIAL)

    def test_external_argv_has_exact_admission_run_product_hash_case_and_component(self):
        value = f.admission(contract)
        expected = f.instrument(value)
        self.assertEqual(len(expected), 14)
        self.assertEqual(contract.controller_run_id(value), value['run_id'][:16])
        self.assertEqual(contract.instrument_argv(value), expected)
        self.assertEqual(contract.instrumentation_kind(expected), 'presentation_process')
        self.assertEqual(contract.validate_operation({'argv': expected, 'stdin': None}, value),
                         {'argv': expected, 'stdin': None})
        for index, replacement in ((6, 'restore_non_default'), (9, 'f' * 16),
                                   (9, '../escaped'), (12, '0' * 64),
                                   (13, f.TEST + '/androidx.test.runner.AndroidJUnitRunner')):
            bad = list(expected)
            bad[index] = replacement
            self.refused(lambda: contract.validate_operation({'argv': bad, 'stdin': None}, value))
        for bad in (expected + ['-e', 'class', 'foreign.Test#method'], expected[:-1],
                    expected + [';id'], ['am', 'instrument', '-w', '-r', '-e', 'class',
                                       'foreign.Test#method', f.COMPONENT]):
            self.refused(lambda: contract.validate_operation({'argv': bad, 'stdin': None}, value))
        self.refused(lambda: contract.validate_operation({'argv': expected, 'stdin': value['artifacts']['build']}, value))

    def test_three_staging_transfers_install_queries_and_hashes_are_role_bound(self):
        value = f.admission(contract)
        for role, remote in f.STAGED.items():
            operation = dict(argv=['dd', 'of=' + remote, 'bs=65536'], stdin=value['artifacts'][role])
            self.assertEqual(contract.validate_operation(operation, value), operation)
            for wrong in (None, value['artifacts']['build'],
                          value['artifacts']['test_apk' if role != 'test_apk' else 'controller_apk']):
                self.refused(lambda: contract.validate_operation(dict(operation, stdin=wrong), value))
            for path in (remote + '.other', remote + '/../escape', '/data/local/tmp/arbitrary.apk'):
                bad = dict(argv=['dd', 'of=' + path, 'bs=65536'], stdin=value['artifacts'][role])
                self.refused(lambda: contract.validate_operation(bad, value))
            install = dict(argv=['pm', 'install', '-r', '-t', '--user', '0', remote], stdin=None)
            self.assertEqual(contract.validate_operation(install, value), install)
        for package in (f.APP, f.TEST, f.CONTROL):
            for argv in (['cmd', 'package', 'list', 'packages', '-U', '--user', '0', package],
                         ['cmd', 'package', 'path', '--user', '0', package],
                         ['sha256sum', '/data/app/~~token/' + package + '-token/base.apk']):
                operation = dict(argv=argv, stdin=None)
                self.assertEqual(contract.validate_operation(operation, value), operation)
        for argv in (['pm', 'install', '-r', '-t', '--user', '10', f.STAGED['controller_apk']],
                     ['cmd', 'package', 'path', '--user', '0', f.CONTROL + '.test'],
                     ['sha256sum', '/data/app/~~token/unrelated.package-token/base.apk']):
            self.refused(lambda: contract.validate_operation(dict(argv=argv, stdin=None), value))

    def test_only_three_uid_checked_bounded_regular_probe_leaf_reads_are_commands(self):
        value = f.admission(contract)
        for leaf in ('created', 'saved', 'commands'):
            argv = contract.probe_read_argv(value, leaf)
            self.assertEqual(argv[:6], ['run-as', f.APP, '--user', '0', 'sh', '-c'])
            self.assertEqual(len(argv), 7)
            script = argv[6]
            self.assertIn('no_backup/process-verify-v3/' + value['run_id'][:16], script)
            self.assertIn(leaf + '.json', script)
            for guard in ('id -u', '%u', '%h', '4096', '! -L', '-f'):
                self.assertIn(guard, script)
            operation = dict(argv=argv, stdin=None)
            self.assertEqual(contract.validate_operation(operation, value), operation)
            for script_suffix in ('; id', ' && cat files/private', ' '):
                bad = list(argv)
                bad[6] += script_suffix
                self.refused(lambda: contract.validate_operation(dict(argv=bad, stdin=None), value))
            bad = list(argv)
            bad[1] = f.CONTROL
            self.refused(lambda: contract.validate_operation(dict(argv=bad, stdin=None), value))
        for leaf in ('created.json', '../created', '', 'other', None, 1):
            self.refused(lambda: contract.probe_read_argv(value, leaf))

    def test_sdk_profile_has_no_generic_shell_force_stop_pidof_model_or_foreign_test_authority(self):
        value = f.admission(contract)
        for argv in (['sh', '-c', 'id'], ['run-as', f.APP, '--user', '0', 'ls', 'files'],
                     ['am', 'force-stop', '--user', '0', f.APP], ['pidof', f.APP],
                     ['df', '-k', '/data'], ['cat', '/proc/meminfo'], ['screencap', '-p'],
                     ['getprop', 'ro.serialno'], ['am', 'start', '-n', f.APP + '/.MainActivity']):
            self.refused(lambda: contract.validate_operation(dict(argv=argv, stdin=None), value))

    def test_session_claim_and_operation_digest_retain_exact_source_worker_and_admission(self):
        value = f.admission(contract)
        session = f.session(contract, value)
        self.assertEqual(contract.validate_session(session, value), session)
        argv = f.instrument(value)
        digest = contract.operation_digest(dict(argv=argv, stdin=None))
        claim = contract.claim_record(session['admission'], session['caller'], 'presentation_process', digest)
        self.assertEqual(contract.validate_claim(claim, session['admission'], session['caller'],
                                                'presentation_process', digest), claim)
        for mutate in (lambda row: row.update(protocol='owned-emulator-player-presentation-ui-v1'),
                       lambda row: row.update(kind='record_native_pages'),
                       lambda row: row.update(operation_sha256='0' * 64),
                       lambda row: row['caller'].update(creation_filetime=row['caller']['creation_filetime'] + 1),
                       lambda row: row.update(admission_sha256='0' * 64)):
            bad = copy.deepcopy(claim)
            mutate(bad)
            self.refused(lambda: contract.validate_claim(bad, session['admission'], session['caller'],
                                                         'presentation_process', digest))
        for mutate in (lambda row: row.update(protocol='sdk-player-presentation-ui-v1'),
                       lambda row: row['sources'][0].update(sha256='0' * 64),
                       lambda row: row.update(seconds=True),
                       lambda row: row['caller'].update(pid=row['descriptor']['guest']['pid'])):
            bad = copy.deepcopy(session)
            mutate(bad)
            self.refused(lambda: contract.validate_session(bad, value))


if __name__ == '__main__':
    unittest.main()
