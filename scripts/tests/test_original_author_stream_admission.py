"""Original host adversaries for the fixed read-only batch; no SDK/native execution."""
import copy
import json
from pathlib import Path
import re
import sys
import unittest
from unittest.mock import patch

from benchmarks import original_author_stream_admission as b
APP = 'org.locallore.app.litertverify'
TEST = APP + '.test'
UIDS = {APP: 10431, TEST: 10432}
HASHES = {APP: 'b' * 64, TEST: 'c' * 64}
APP_PATH = '/data/app/~~batch-a==/org.locallore.app.litertverify-original==/base.apk'
TEST_PATH = '/data/app/~~batch-b==/org.locallore.app.litertverify.test-original==/base.apk'
MISSING = 2 * 2588147712
RESERVE = 2 * 1024**3
MEMORY = 4 * 1024**3


def fixture():
    return '\n'.join((
        'BATCH_V1_BEGIN', 'BOOT=1', 'SDK=35', 'ABI=x86_64', 'QEMU=1', 'USER=0',
        'APP_PATH=' + APP_PATH, 'TEST_PATH=' + TEST_PATH,
        'APP_SHA256=' + HASHES[APP], 'TEST_SHA256=' + HASHES[TEST],
        'PACKAGES_V1_BEGIN', 'package:' + APP + ' uid:10431', 'package:' + TEST + ' uid:10432', 'PACKAGES_V1_END',
        'RESOURCES_V1_BEGIN', 'Filesystem 1K-blocks Used Available Use% Mounted on',
        '/dev/block/dm-9 20000000 1000000 18000000 5% /data/user/0',
        'MemTotal: 8388608 kB', 'MemAvailable: 5242880 kB', 'HugePages_Total: 0',
        'RESOURCES_V1_END', 'BATCH_V1_END'))


def decode(text=None, *, missing=MISSING, uids=None, hashes=None):
    data = fixture().encode('ascii') if text is None else text.encode('ascii') if type(text) is str else text
    return b.decode(data, copy.deepcopy(UIDS if uids is None else uids), copy.deepcopy(HASHES if hashes is None else hashes), missing)


class BatchAdversaries(unittest.TestCase):
    def refused(self, text, **kwargs):
        with self.assertRaises(b.BatchRefused) as caught:
            decode(text, **kwargs)
        message = str(caught.exception)
        self.assertRegex(message, r'^[a-z_]{1,64}$')
        self.assertNotIn('/data/', message)
        self.assertNotIn('secret_weather_note', message)
        return message

    def test_original_fixture_exact_closed_result_for_lf_crlf_and_one_terminal_lf(self):
        expected = {'version': 1, 'scope': 'real_author_stream_pretransfer_batch_v1',
                    'properties': {'boot_completed': '1', 'api': '35', 'abi': 'x86_64', 'qemu': '1'}, 'current_user': 0,
                    'packages': {APP: {'uid': 10431, 'path': APP_PATH, 'sha256': 'b' * 64},
                                 TEST: {'uid': 10432, 'path': TEST_PATH, 'sha256': 'c' * 64}},
                    'resources': {'source': '/proc/meminfo', 'memory_available_bytes': 5 * 1024**3, 'low_memory': None,
                                  'free_bytes': 18000000 * 1024, 'missing_bytes': MISSING, 'reserve_bytes': RESERVE}}
        for text in (fixture(), fixture() + '\n', fixture().replace('\n', '\r\n'), (fixture() + '\n').replace('\n', '\r\n')):
            with self.subTest(framing='crlf' if '\r' in text else 'lf', terminal=text.endswith('\n')):
                observed = decode(text)
                self.assertEqual(observed, expected)
                self.assertIs(type(observed['version']), int); self.assertIs(type(observed['current_user']), int)
                for package in observed['packages'].values(): self.assertIs(type(package['uid']), int)
                for key in ('memory_available_bytes', 'free_bytes', 'missing_bytes', 'reserve_bytes'):
                    self.assertIs(type(observed['resources'][key]), int)

    def test_package_row_order_is_data_and_callers_are_unchanged(self):
        original = fixture()
        rows = original.splitlines(); rows[11], rows[12] = rows[12], rows[11]
        self.assertEqual(decode('\n'.join(rows)), decode())
        uids, hashes = copy.deepcopy(UIDS), copy.deepcopy(HASHES)
        b.decode(original.encode(), uids, hashes, MISSING)
        self.assertEqual(uids, UIDS); self.assertEqual(hashes, HASHES)

    def test_same_capacity_floors_and_exact_boundaries(self):
        exact = fixture().replace('18000000 5%', str((MISSING + RESERVE) // 1024) + ' 5%').replace('5242880 kB', '4194304 kB')
        observed = decode(exact)
        self.assertEqual(observed['resources']['memory_available_bytes'], MEMORY)
        self.assertEqual(observed['resources']['free_bytes'], MISSING + RESERVE)
        self.refused(exact.replace('4194304 kB', '4194303 kB'))
        self.refused(exact.replace(str((MISSING + RESERVE) // 1024) + ' 5%', str((MISSING + RESERVE) // 1024 - 1) + ' 5%'))
        self.assertEqual(decode(missing=0)['resources']['missing_bytes'], 0)
        self.assertEqual(decode(missing=2588147712)['resources']['missing_bytes'], 2588147712)

    def test_missing_duplicate_extra_reordered_or_unknown_frames_refused(self):
        lines = fixture().splitlines()
        for index in range(14):
            with self.subTest(kind='missing', index=index): self.refused('\n'.join(lines[:index] + lines[index + 1:]))
            with self.subTest(kind='duplicate', index=index): self.refused('\n'.join(lines[:index] + [lines[index]] + lines[index:]))
        for text in (fixture() + '\n\n', '\n' + fixture(), fixture() + '\nEXTRA=secret_weather_note',
                     fixture().replace('RESOURCES_V1_END\nBATCH_V1_END', 'BATCH_V1_END\nRESOURCES_V1_END'),
                     fixture().replace('BOOT=1\nSDK=35', 'SDK=35\nBOOT=1'),
                     fixture().replace('USER=0', 'USER=0\nEXTRA=1'), fixture().replace('BATCH_V1_BEGIN', 'BATCH_V2_BEGIN')):
            with self.subTest(text=text[:70]): self.refused(text)

    def test_wrong_profile_or_current_user_cannot_pass_as_truthy(self):
        for field, good, bads in (('BOOT', '1', ('0', 'true', '01', '1 ')), ('SDK', '35', ('34', '36', '035', 'true')),
                                 ('ABI', 'x86_64', ('arm64-v8a', 'x86', 'x86_64 ')), ('QEMU', '1', ('0', 'true', '01')),
                                 ('USER', '0', ('10', 'false', '00', '-1'))):
            for bad in bads:
                with self.subTest(field=field, value=bad): self.refused(fixture().replace(field + '=' + good, field + '=' + bad))

    def test_uid_roster_is_exact_distinct_numeric_and_bound(self):
        app = 'package:' + APP + ' uid:10431'; test = 'package:' + TEST + ' uid:10432'
        for replacement in ('package:' + APP + ' uid:10432', 'package:' + APP + ' uid:10433',
                            'package:' + APP + ' uid:0', 'package:' + APP + ' uid:010431',
                            'package:' + APP + ' uid:-1', 'package:' + APP + ' uid:true',
                            'package:' + APP + '.other uid:10431', 'package:' + APP + ' uid:10431 extra',
                            ' ' + app, app + ' ', test):
            with self.subTest(row=replacement): self.refused(fixture().replace(app, replacement))
        self.refused(fixture().replace(test, app))
        self.refused(fixture().replace('PACKAGES_V1_END', 'package:original.secret_weather_note uid:10499\nPACKAGES_V1_END'))

    def test_apk_paths_reject_traversal_shell_syntax_aliases_and_foreign_roots(self):
        bads = ('/data/app/../base.apk', '/data/app/a//base.apk', 'relative/base.apk',
                '/sdcard/app/base.apk', '/data/app/a/base.apk;secret_weather_note', '/data/app/a/base.apk$(id)',
                '/data/app/a/base.apk\tother', '/data/app/a/base.apk/child', '/data/app/a/base.apk ',
                '/data/app/a/not-base.apk', '/data/app/a/../../base.apk')
        for bad in bads:
            with self.subTest(path=bad): self.refused(fixture().replace('APP_PATH=' + APP_PATH, 'APP_PATH=' + bad))
        self.refused(fixture().replace('APP_PATH=' + APP_PATH, 'APP_PATH=package:' + APP_PATH))
        self.refused(fixture().replace('TEST_PATH=' + TEST_PATH, 'TEST_PATH=' + APP_PATH))

    def test_apk_hashes_are_lowercase_full_and_cross_bound(self):
        for bad in ('a' * 64, 'B' * 64, 'b' * 63, 'b' * 65, 'g' * 64, 'true', ''):
            with self.subTest(hash=bad): self.refused(fixture().replace('APP_SHA256=' + HASHES[APP], 'APP_SHA256=' + bad))
        self.refused(fixture().replace('TEST_SHA256=' + HASHES[TEST], 'TEST_SHA256=' + HASHES[APP]))
        self.refused(fixture().replace('APP_SHA256=', 'APP_SHA256_EXTRA='))

    def test_resource_rows_are_closed_unambiguous_nonnegative_and_bounded(self):
        for text in (fixture().replace('MemAvailable: 5242880 kB', 'MemAvailable: 5242880 kB\nMemAvailable: 5242880 kB'),
                     fixture().replace('MemAvailable: 5242880 kB', 'MemAvailable: -1 kB'),
                     fixture().replace('MemAvailable: 5242880 kB', 'MemAvailable: 5e6 kB'),
                     fixture().replace('MemAvailable: 5242880 kB', 'MemAvailable: 5242880'),
                     fixture().replace('MemAvailable: 5242880 kB', 'MemAvailable: 5242880 MB'),
                     fixture().replace('MemAvailable: 5242880 kB', ''),
                     fixture().replace('HugePages_Total: 0', 'unexpected memory row'),
                     fixture().replace('Filesystem 1K-blocks Used Available Use% Mounted on', 'Filesystem wrong columns'),
                     fixture().replace('/dev/block/dm-9 20000000 1000000 18000000 5% /data/user/0',
                                       '/dev/block/dm-9 20000000 1000000 18000000 5% /data/user/0\n/dev/block/dm-10 20000000 0 19000000 0% /data'),
                     fixture().replace('18000000 5%', '-1 5%'), fixture().replace('18000000 5%', '20000001 5%'),
                     fixture().replace('/data/user/0', '/sdcard'), fixture().replace('5% /data/user/0', '101% /data/user/0')):
            with self.subTest(text=text[-130:]): self.refused(text)

    def test_decoder_input_bounds_ascii_and_crlf_rules(self):
        for value in (b'', b' ' * 16385, fixture(), None, bytearray(fixture().encode()),
                      fixture().encode() + b'\x00', fixture().encode() + b'\xff',
                      fixture().replace('\n', '\r').encode(), fixture().replace('BOOT=1', 'BOOT=1\rX').encode(),
                      fixture().replace('BOOT=1', 'BOOT=1\x0bsecret_weather_note').encode()):
            with self.subTest(kind=type(value).__name__):
                # Call directly so a str cannot be silently encoded by this test helper.
                with self.assertRaises(b.BatchRefused): b.decode(value, UIDS, HASHES, MISSING)

    def test_expected_bindings_and_missing_space_are_typed_and_closed(self):
        for bad in (-1, True, 2 * 2588147712 + 1, '0', None):
            with self.subTest(missing=bad): self.refused(fixture(), missing=bad)
        for uids in ({}, {APP: 10431}, dict(UIDS, extra=10433), {APP: True, TEST: 10432}, {APP: 10431, TEST: 10431}, {APP: 9999, TEST: 10432}):
            with self.subTest(uids=uids): self.refused(fixture(), uids=uids)
        for hashes in ({}, {APP: 'b' * 64}, dict(HASHES, extra='d' * 64), {APP: 'B' * 64, TEST: 'c' * 64}, {APP: None, TEST: 'c' * 64}):
            with self.subTest(hashes=hashes): self.refused(fixture(), hashes=hashes)

    def test_fixed_script_is_readonly_bounded_and_rejects_injection_arguments(self):
        result = b.script(10431, 10432, 'b' * 64, 'c' * 64)
        self.assertIs(type(result), str); self.assertLessEqual(len(result.encode()), 16384)
        for marker in ('getprop', 'get-current-user', '/proc/meminfo', 'sha256sum', APP, TEST, 'BATCH_V1_BEGIN', 'BATCH_V1_END'):
            self.assertIn(marker, result)
        self.assertNotRegex(result, r'\b(?:install|force-stop|uninstall|mkdir|rm|mv|cp|chmod|setprop|reboot|tee)\b')
        self.assertNotRegex(result, r'(?<![12])>(?!&)')
        for args in ((True, 10432, 'b' * 64, 'c' * 64), (10431, 10431, 'b' * 64, 'c' * 64),
                     (9999, 10432, 'b' * 64, 'c' * 64), (10431, 10432, 'B' * 64, 'c' * 64),
                     ('10431;secret_weather_note', 10432, 'b' * 64, 'c' * 64), (10431, 10432, 'b' * 64, 'c' * 64 + '$(id)')):
            with self.subTest(args=args), self.assertRaises(b.BatchRefused): b.script(*args)

    def test_pure_calls_perform_no_file_or_process_operations(self):
        original = fixture().encode()
        with patch('builtins.open', side_effect=AssertionError('file read')), patch.object(Path, 'open', side_effect=AssertionError('file read')), \
                patch('subprocess.Popen', side_effect=AssertionError('process')), patch('os.system', side_effect=AssertionError('process')):
            self.assertEqual(b.decode(original, UIDS, HASHES, MISSING)['current_user'], 0)
            self.assertIn('BATCH_V1_BEGIN', b.script(10431, 10432, 'b' * 64, 'c' * 64))


    def test_oversized_decimals_refuse_without_conversion_errors(self):
        digits = '1' * 5000
        candidates = (
            fixture().replace('uid:10431', 'uid:' + digits),
            fixture().replace('18000000 5%', digits + ' 5%'),
            fixture().replace('MemAvailable: 5242880 kB', 'MemAvailable: ' + digits + ' kB'),
            fixture().replace('HugePages_Total: 0', 'HugePages_Total: ' + digits),
        )
        for index, text in enumerate(candidates):
            with self.subTest(index=index):
                self.assertLessEqual(len(text.encode('ascii')), 16384)
                self.refused(text)
        # An ordinary wider kernel count remains valid; the decimal guard does
        # not change availability units or the model-copy/memory floors.
        under_limit = fixture().replace('HugePages_Total: 0', 'HugePages_Total: 0\nVmallocTotal: 34359738367 kB')
        self.assertEqual(decode(under_limit), decode())


if __name__ == '__main__':
    suite = unittest.defaultTestLoader.loadTestsFromTestCase(BatchAdversaries)
    expected = suite.countTestCases()
    result = unittest.TextTestRunner(stream=sys.stdout, verbosity=2).run(suite)
    print(json.dumps({'version': 1, 'scope': 'pure_batched_stream_admission_adversaries_v1', 'expected': expected,
                      'run': result.testsRun, 'failures': len(result.failures), 'errors': len(result.errors),
                      'skipped': len(result.skipped), 'passed': result.wasSuccessful() and result.testsRun == expected}), flush=True)
    raise SystemExit(0 if result.wasSuccessful() and result.testsRun == expected else 1)
