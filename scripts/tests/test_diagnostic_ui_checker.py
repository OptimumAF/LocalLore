"""Original SDK17 checker guards; tiny retained D: fixtures, no SDK/native calls.

Copyright 2026 LocalLore contributors. SPDX-License-Identifier: Apache-2.0

Private __file__/sys.modules patches transport fixed source into isolated tiny
fixtures. They are not production path overrides. Real shared hash/path reader
is preserved for positive/drift cases. No original source is modified.
"""
import contextlib
import hashlib
import inspect
import os
from pathlib import Path
import sys
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import patch

from benchmarks import archive_ui_build as files
from benchmarks import diagnostic_ui_profile_build as adapter


EXPECTED_CHECKERS = (
    ('scripts/audit_physical_model_apk.py', 23249,
     '9a9f06d299e5182ffd026c3fe5dbce5b13a6edb11d2be32daf81a01da02eae9a'),
    ('scripts/audit_apk.py', 42803,
     '1c54e10dc9b8b24baa7ced0baf3ed8efdbf679e1ab9a6d0adf9639ab358562ad'),
)


@unittest.skipUnless(os.name == 'nt', 'Physical D: checker source tests')
class DiagnosticUiCheckerTests(unittest.TestCase):
    def setUp(self):
        self.live_root = Path(adapter.__file__).parents[1]
        # Retained after success/failure. The bounded host owner sets TEMP on D:.
        self.root = Path(tempfile.mkdtemp(prefix='diagnostic-ui-checker-'))
        self.assertEqual('D:', self.root.drive.upper())
        self.assertEqual(self.root, self.root.resolve(strict=True))
        (self.root / 'benchmarks').mkdir()
        (self.root / 'scripts').mkdir()
        self.originals = {}
        for relative, size, digest in EXPECTED_CHECKERS:
            raw = (self.live_root / relative).read_bytes()
            self.assertEqual(size, len(raw), 'Fixture must use the frozen parent checker bytes')
            self.assertEqual(digest, hashlib.sha256(raw).hexdigest())
            (self.root / relative).write_bytes(raw)
            self.originals[relative] = raw
        self.real_bound = files._bound

    @contextlib.contextmanager
    def transported_origins(self):
        good_base = SimpleNamespace(__file__=str(self.root / 'scripts/audit_apk.py'))
        decoder = SimpleNamespace(
            __file__=str(self.root / 'scripts/audit_physical_model_apk.py'),
            base=good_base,
        )
        aliases = {
            'benchmarks.diagnostic_ui_build': SimpleNamespace(
                __file__=str(self.root / 'benchmarks/diagnostic_ui_build.py')),
            'benchmarks.archive_ui_build': files,
            'scripts.audit_physical_model_apk': decoder,
            'scripts.audit_apk': good_base,
            'audit_apk': good_base,
        }
        with patch.object(adapter, '__file__', str(self.root / 'benchmarks/diagnostic_ui_profile_build.py')), \
                patch.object(files, '__file__', str(self.root / 'benchmarks/archive_ui_build.py')), \
                patch.dict(sys.modules, aliases):
            self.assertIs(self.real_bound, files._bound)
            yield aliases

    def assert_source_refusal(self):
        with self.assertRaises(adapter.contract.TargetRefused) as caught:
            adapter.revalidate_checker()
        self.assertEqual('source', str(caught.exception))
        self.assertNotIn('PRIVATE', str(caught.exception))

    def test_fixed_pins_zero_argument_api_and_actual_positive_hashes(self):
        self.assertEqual(EXPECTED_CHECKERS, adapter.CHECKERS)
        self.assertEqual({}, dict(inspect.signature(adapter.revalidate_checker).parameters))
        with self.transported_origins():
            self.assertIsNone(adapter.revalidate_checker())
            self.assertIsNone(adapter.revalidate_checker())
            self.assertIs(self.real_bound, files._bound)
        # No public path/hash/callback parameter can select different checker code.
        with self.assertRaises(TypeError):
            adapter.revalidate_checker(self.root)
        with self.assertRaises(TypeError):
            adapter.revalidate_checker(callback=lambda: None)

    def test_each_script_same_size_and_restored_mtime_drift_fails_real_hash(self):
        with self.transported_origins():
            self.assertIsNone(adapter.revalidate_checker())
            for relative, _, _ in EXPECTED_CHECKERS:
                with self.subTest(relative=relative):
                    target = self.root / relative
                    original = self.originals[relative]
                    before = target.stat()
                    # Same length/inode/mtime: metadata-only checking must not pass.
                    mutated = bytes([original[0] ^ 1]) + original[1:]
                    retained = self.root / ('mutant-' + target.name + '.bin')
                    retained.write_bytes(mutated)
                    try:
                        target.write_bytes(mutated)
                        os.utime(target, ns=(before.st_atime_ns, before.st_mtime_ns))
                        after = target.stat()
                        self.assertEqual((before.st_ino, before.st_size, before.st_mtime_ns),
                                         (after.st_ino, after.st_size, after.st_mtime_ns))
                        self.assertIs(self.real_bound, files._bound)
                        self.assert_source_refusal()
                    finally:
                        target.write_bytes(original)
                        os.utime(target, ns=(before.st_atime_ns, before.st_mtime_ns))
                    self.assertIsNone(adapter.revalidate_checker())

    def test_cached_foreign_bare_base_is_rejected_even_with_identical_bytes(self):
        foreign = self.root / 'foreign'
        foreign.mkdir()
        source = foreign / 'audit_apk.py'
        source.write_bytes(self.originals['scripts/audit_apk.py'])
        foreign_module = SimpleNamespace(__file__=str(source))
        with self.transported_origins() as good:
            self.assertIsNone(adapter.revalidate_checker())
            sys.modules['audit_apk'] = foreign_module
            self.assert_source_refusal()
            sys.modules['audit_apk'] = good['audit_apk']
            self.assertIsNone(adapter.revalidate_checker())

    def test_decoder_base_origin_is_checked_separately_from_good_cached_alias(self):
        with self.transported_origins() as good:
            self.assertIsNone(adapter.revalidate_checker())
            decoder = good['scripts.audit_physical_model_apk']
            prior = decoder.base
            try:
                decoder.base = SimpleNamespace(__file__=str(self.root / 'PRIVATE-other/audit_apk.py'))
                # Bare and namespaced aliases remain the correct fixed module.
                self.assertIs(prior, sys.modules['audit_apk'])
                self.assertIs(prior, sys.modules['scripts.audit_apk'])
                self.assert_source_refusal()
            finally:
                decoder.base = prior
            self.assertIsNone(adapter.revalidate_checker())

    def test_each_other_loaded_checker_origin_must_match_current_root(self):
        names = ('benchmarks.diagnostic_ui_build', 'benchmarks.archive_ui_build',
                 'scripts.audit_physical_model_apk', 'scripts.audit_apk')
        with self.transported_origins() as good:
            self.assertIsNone(adapter.revalidate_checker())
            for name in names:
                with self.subTest(module=name):
                    try:
                        sys.modules[name] = SimpleNamespace(
                            __file__=str(self.root / 'PRIVATE-foreign' / name.replace('.', '-')))
                        self.assert_source_refusal()
                    finally:
                        sys.modules[name] = good[name]
                    self.assertIsNone(adapter.revalidate_checker())

    def test_missing_or_malformed_origin_metadata_is_a_fixed_source_refusal(self):
        with self.transported_origins() as good:
            self.assertIsNone(adapter.revalidate_checker())
            for module in (SimpleNamespace(), SimpleNamespace(__file__=None),
                           SimpleNamespace(__file__=17)):
                with self.subTest(module=module):
                    try:
                        sys.modules['audit_apk'] = module
                        self.assert_source_refusal()
                    finally:
                        sys.modules['audit_apk'] = good['audit_apk']
            self.assertIsNone(adapter.revalidate_checker())

    def test_unloaded_decoder_stays_unloaded_and_checker_never_reenters_verification(self):
        with self.transported_origins():
            for name in ('scripts.audit_physical_model_apk', 'scripts.audit_apk', 'audit_apk'):
                sys.modules[name] = None
            with patch.object(adapter.contract, 'revalidate_inputs',
                              side_effect=AssertionError('Checker must not recurse through contract')), \
                    patch.object(adapter, 'verify_current',
                                 side_effect=AssertionError('Checker must not enter build verification')), \
                    patch.object(adapter.build, 'verify_frozen_product',
                                 side_effect=AssertionError('Checker must not enter attestation')):
                self.assertIsNone(adapter.revalidate_checker())
            for name in ('scripts.audit_physical_model_apk', 'scripts.audit_apk', 'audit_apk'):
                self.assertIsNone(sys.modules[name])

    def test_shared_reader_failure_is_normalized_without_private_payload(self):
        with self.transported_origins():
            self.assertIsNone(adapter.revalidate_checker())
            for failure in (OSError('PRIVATE local path'), ValueError('PRIVATE binding')):
                with self.subTest(kind=type(failure).__name__):
                    # Only this error-boundary test injects a failed reader.
                    # The actual-byte drift tests above keep the real validator.
                    with patch.object(files, '_bound', side_effect=failure):
                        self.assert_source_refusal()
            self.assertIsNone(adapter.revalidate_checker())
