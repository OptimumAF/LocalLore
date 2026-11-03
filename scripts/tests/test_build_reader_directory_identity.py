"""Original directory identity/readback guards over retained tiny D: files.

Only stat observation ports are synthetic. File opens, byte hashing, held
file checks and the production Reader are real; no artifact/device is opened.
"""
from contextlib import contextmanager
import hashlib
import os
from pathlib import Path
import stat
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import patch

from benchmarks import diagnostic_ui_build as build
from benchmarks import receipt_avd_environment as env


@unittest.skipUnless(os.name == 'nt', 'Actual guarded project reader requires physical D:')
class BuildReaderDirectoryIdentityTests(unittest.TestCase):
    def setUp(self):
        # The owned runner supplies its packet scratch as process tempfiledir.
        # No cleanup: preserve every synthetic original and failed attempt.
        self.root = Path(tempfile.mkdtemp(prefix='directory-reader-identity-'))
        self.assertEqual(self.root.drive.upper(), 'D:')
        self.assertEqual(self.root.resolve(strict=True), self.root)
        self.first = self.root / 'first.bin'
        self.second = self.root / 'second.bin'
        self.first.write_bytes(b'FIRST-CONTENT')
        self.second.write_bytes(b'SECOND-CONTENT')
        self.first_pin = self.pin(self.first)
        self.second_pin = self.pin(self.second)

    @staticmethod
    def pin(path):
        raw = path.read_bytes()
        return dict(path=str(path), bytes=len(raw), sha256=hashlib.sha256(raw).hexdigest())

    @contextmanager
    def observation(self, target, **changes):
        original = Path.lstat
        attempts = []
        def varied(path, *args, **kwargs):
            info = original(path, *args, **kwargs)
            if path != target: return info
            attempts.append(str(path))
            fields = {name: getattr(info, name) for name in dir(info) if name.startswith('st_')}
            fields.update(changes)
            return SimpleNamespace(**fields)
        with patch.object(Path, 'lstat', varied):
            yield attempts

    def test_directory_size_only_variation_preserves_read_and_final_guard(self):
        control = build._Reader()
        self.assertEqual(control.read(self.first_pin, data=True), b'FIRST-CONTENT')
        control.final()
        reader = build._Reader()
        self.assertEqual(reader.read(self.first_pin), self.first_pin['sha256'])
        before = self.root.lstat()
        # Reproduce the observed field class without claiming the OS cause or
        # relying on actual allocation/clock behavior of a host filesystem.
        with self.observation(self.root, st_size=before.st_size + 20480) as calls:
            self.assertEqual(reader.read(self.second_pin, data=True), b'SECOND-CONTENT')
            self.assertEqual(reader.read(self.first_pin, data=True), b'FIRST-CONTENT')
            reader.final()
        self.assertGreaterEqual(len(calls), 2)
        self.assertEqual(reader.total, 2 * (len(b'FIRST-CONTENT') + len(b'SECOND-CONTENT')))

    def test_directory_identity_or_link_changes_remain_refused(self):
        info = self.root.lstat()
        changes = [('dev', dict(st_dev=info.st_dev + 1)),
            ('inode', dict(st_ino=info.st_ino + 1)),
            ('mode', dict(st_mode=stat.S_IFREG | stat.S_IMODE(info.st_mode))),
            ('mtime', dict(st_mtime_ns=info.st_mtime_ns + 1000000000)),
            ('nlink', dict(st_nlink=info.st_nlink + 1)),
            ('symlink', dict(st_mode=stat.S_IFLNK | stat.S_IMODE(info.st_mode))),
            ('reparse', dict(st_file_attributes=getattr(info, 'st_file_attributes', 0) | 0x400))]
        for name, fields in changes:
            reader = build._Reader(); reader.read(self.first_pin)
            refused = (ValueError, env.EnvironmentRefused) if name in ('symlink', 'reparse') else ValueError
            with self.subTest(field=name), self.observation(self.root, **fields) as calls:
                with self.assertRaises(refused): reader.final()
            self.assertGreater(len(calls), 0)

    def test_regular_file_size_and_identity_fields_are_not_generalized_away(self):
        info = self.first.lstat()
        changes = [('size', dict(st_size=info.st_size + 20480)),
            ('dev', dict(st_dev=info.st_dev + 1)),
            ('inode', dict(st_ino=info.st_ino + 1)),
            ('mode', dict(st_mode=stat.S_IFDIR | stat.S_IMODE(info.st_mode))),
            ('mtime', dict(st_mtime_ns=info.st_mtime_ns + 1000000000)),
            ('nlink', dict(st_nlink=info.st_nlink + 1)),
            ('symlink', dict(st_mode=stat.S_IFLNK | stat.S_IMODE(info.st_mode))),
            ('reparse', dict(st_file_attributes=getattr(info, 'st_file_attributes', 0) | 0x400))]
        for name, fields in changes:
            reader = build._Reader(); reader.read(self.first_pin)
            refused = (ValueError, env.EnvironmentRefused) if name in ('symlink', 'reparse') else ValueError
            with self.subTest(field=name), self.observation(self.first, **fields) as calls:
                with self.assertRaises(refused): reader.final()
            self.assertGreater(len(calls), 0)

    def test_final_actual_byte_hash_refuses_same_size_restored_mtime_rewrite(self):
        reader = build._Reader()
        self.assertEqual(reader.read(self.first_pin, data=True), b'FIRST-CONTENT')
        before = self.first.stat()
        changed = b'OTHER-CONTENT'
        self.assertEqual(len(changed), self.first_pin['bytes'])
        self.first.write_bytes(changed)
        os.utime(self.first, ns=(before.st_atime_ns, before.st_mtime_ns))
        self.assertEqual(self.first.stat().st_size, before.st_size)
        self.assertEqual(self.first.stat().st_mtime_ns, before.st_mtime_ns)
        with self.assertRaises(ValueError): reader.final()
