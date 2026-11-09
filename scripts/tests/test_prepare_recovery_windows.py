"""Native directory fences on tiny D: fixtures; no guest/SDK/process/ledger IO.

Copyright 2026 LocalLore contributors. SPDX-License-Identifier: Apache-2.0
"""
import ast
import ctypes
import importlib.util
import os
from pathlib import Path
import tempfile
from types import SimpleNamespace
import unittest
from unittest import mock

from benchmarks import prepare_recovery_windows as native


@unittest.skipUnless(os.name == 'nt', 'Windows native directory handles')
class DirectoryFenceTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix='locallore-recovery-native-', dir='D:/Dev/_Temp')
        self.addCleanup(self.temp.cleanup)
        self.base = Path(self.temp.name).resolve()
        self.fences = []
        self.addCleanup(self.close_fences)

    def close_fences(self):
        for fence in self.fences:
            try:
                fence.close()
            except native.NativeRefused:
                pass  # A synthetic false result may already have closed the actual handle.

    def fence(self):
        fence = native.DirectoryFence()
        self.fences.append(fence)
        return fence

    def test_import_has_no_native_call_and_python39_syntax(self):
        path = Path(native.__file__)
        ast.parse(path.read_text(encoding='utf-8'), feature_version=(3, 9))
        spec = importlib.util.spec_from_file_location('synthetic_directory_fence_import', path)
        module = importlib.util.module_from_spec(spec)
        with mock.patch.object(ctypes, 'WinDLL', side_effect=AssertionError('import native call')):
            spec.loader.exec_module(module)

    def test_atomic_creation_retains_handle_before_return_and_allows_child_io(self):
        fence = self.fence()
        root = self.base / 'created'
        identity = fence.create(root)
        self.assertGreater(identity['file_index'], 0)
        self.assertTrue(root.is_dir())
        child = root / 'tiny.txt'
        child.write_bytes(b'not guest data')
        child.write_bytes(b'rewritten tiny fixture')
        self.assertEqual(child.read_bytes(), b'rewritten tiny fixture')
        child.unlink()
        self.assertTrue(fence.verify())
        with self.assertRaises(OSError):
            root.rmdir()
        with self.assertRaises(OSError):
            root.rename(self.base / 'moved')
        self.assertTrue(fence.close())
        root.rename(self.base / 'moved')
        (self.base / 'moved').rmdir()

    def test_existing_directory_is_never_adopted_by_create(self):
        root = self.base / 'existing'
        root.mkdir()
        (root / 'preserved.txt').write_bytes(b'keep')
        fence = self.fence()
        with self.assertRaisesRegex(native.NativeRefused, '^create$'):
            fence.create(root)
        self.assertEqual((root / 'preserved.txt').read_bytes(), b'keep')
        self.assertFalse(any(e['path'] == root for e in fence._entries))

    def test_holding_existing_directory_protects_all_ancestors_until_close(self):
        parent = self.base / 'parent'
        parent.mkdir()
        root = parent / 'existing'
        root.mkdir()
        fence = self.fence()
        self.assertTrue(fence.hold(root))
        self.assertEqual([e['path'] for e in fence._entries], list(reversed([root] + list(root.parents))))
        for item in (root, parent, self.base):
            with self.subTest(item=item.name):
                with self.assertRaises(OSError):
                    item.rename(item.with_name(item.name + '-moved'))
        with self.assertRaises(OSError):
            root.rmdir()
        self.assertTrue(fence.close())
        root.rmdir()
        parent.rmdir()

    def test_missing_file_relative_and_other_drive_paths_refuse(self):
        ordinary_file = self.base / 'file'
        ordinary_file.write_bytes(b'preserve')
        for path in (self.base / 'missing', ordinary_file, Path('relative'), Path('C:/not-a-project')):
            with self.subTest(path=str(path)):
                fence = self.fence()
                with self.assertRaises(native.NativeRefused):
                    fence.hold(path)
                fence.close()
        self.assertEqual(ordinary_file.read_bytes(), b'preserve')

    def test_reparse_metadata_refuses_without_opening_that_parent(self):
        parent = self.base / 'reparse'
        parent.mkdir()
        original = Path.lstat
        def metadata(path, *args, **kwargs):
            if path == parent:
                return SimpleNamespace(st_mode=0o40700, st_file_attributes=0x400)
            return original(path, *args, **kwargs)
        fence = self.fence()
        opened = fence._api.open
        with mock.patch.object(fence._api, 'open', wraps=opened) as calls, \
                mock.patch.object(Path, 'lstat', new=metadata):
            with self.assertRaisesRegex(native.NativeRefused, '^directory$'):
                fence.hold(parent)
            self.assertNotIn(mock.call(parent), calls.call_args_list)

    def test_hold_is_idempotent_and_closed_fence_cannot_reopen_or_create(self):
        fence = self.fence()
        fence.hold(self.base)
        size = len(fence._entries)
        fence.hold(self.base)
        self.assertEqual(len(fence._entries), size)
        self.assertTrue(fence.close())
        self.assertTrue(fence.close())
        for operation in (lambda: fence.hold(self.base), lambda: fence.create(self.base/'new'), fence.verify):
            with self.assertRaisesRegex(native.NativeRefused, '^closed$'):
                operation()
        self.assertFalse((self.base/'new').exists())

    def test_source_identity_change_refuses_before_any_claim_can_proceed(self):
        fence = self.fence()
        fence.hold(self.base)
        information = fence._api.information
        def changed(handle):
            value = information(handle)
            return dict(value, file_index=value['file_index'] + 1)
        with mock.patch.object(fence._api, 'information', side_effect=changed):
            with self.assertRaisesRegex(native.NativeRefused, '^identity$'):
                fence.verify()

    def test_all_owned_closes_attempt_once_after_injected_unknown_close(self):
        fence = self.fence()
        fence.create(self.base/'created')
        original = fence._api.close
        calls = []
        def close(handle):
            calls.append(handle)
            self.assertTrue(original(handle))
            return len(calls) != 1  # Actual handle closed; simulate unknown reporting.
        with mock.patch.object(fence._api, 'close', side_effect=close):
            with self.assertRaises(native.NativeRefused) as first:
                fence.close()
            self.assertFalse(first.exception.cleanup_known)
            self.assertEqual(len(calls), len(fence._entries))
            self.assertEqual(len(calls), len(set(calls)))
            with self.assertRaises(native.NativeRefused) as second:
                fence.close()
            self.assertFalse(second.exception.cleanup_known)
            self.assertEqual(len(calls), len(fence._entries))

    def test_probe_close_fault_is_unknown_and_does_not_skip_owned_cleanup(self):
        fence = self.fence()
        fence.hold(self.base)
        original = fence._api.close
        def close_probe(handle):
            self.assertTrue(original(handle))
            return False
        with mock.patch.object(fence._api, 'close', side_effect=close_probe):
            with self.assertRaises(native.NativeRefused) as error:
                fence.verify()
            self.assertFalse(error.exception.cleanup_known)
        with self.assertRaises(native.NativeRefused):
            fence.close()
        self.assertTrue(all(e['attempted'] and e['closed'] for e in fence._entries))

    def test_missing_atomic_api_fails_closed_without_create_fallback(self):
        with mock.patch.object(ctypes, 'WinDLL', return_value=SimpleNamespace()):
            with self.assertRaisesRegex(native.NativeRefused, '^atomic_directory_api_unavailable$'):
                native.DirectoryFence()


if __name__ == '__main__':
    unittest.main()
