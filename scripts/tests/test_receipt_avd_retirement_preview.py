# Copyright 2026 LocalLore contributors. SPDX-License-Identifier: Apache-2.0
"""Original read-only preview oracles; tiny synthetic D: files, never real AVDs."""
import ast
import contextlib
import ctypes
import importlib
import io
import json
import os
from pathlib import Path
import subprocess
import unittest
from unittest.mock import patch

from benchmarks import receipt_avd_storage as storage
from benchmarks import receipt_avd_retirement as executor
from scripts.tests import test_receipt_avd_retirement_fixtures as fixtures


IMAGE_NAMES = (
    'cache.img', 'cache.img.qcow2', 'encryptionkey.img', 'encryptionkey.img.qcow2',
    'sdcard.img', 'sdcard.img.qcow2', 'userdata-qemu.img', 'userdata-qemu.img.qcow2',
    'snapshots/default_boot/ram.img',
)
PREVIEW_KEYS = frozenset(('version', 'scope', 'ledger_binding', 'plan', 'remove_bytes',
                          'preserve_bytes', 'snapshot_only', 'pins_plan',
                          'deletes_images', 'registry_written'))


def snapshot(base):
    """Content and stable file metadata, deliberately excluding access time."""
    result = {}
    for parent, folders, files in os.walk(str(base), followlinks=False):
        for name in folders + files:
            path = Path(parent) / name
            info = path.lstat()
            result[path.relative_to(base).as_posix()] = (
                info.st_dev, info.st_ino, info.st_size, info.st_mtime_ns,
                getattr(info, 'st_birthtime_ns', None),
                path.read_bytes() if path.is_file() else None)
    return result


@contextlib.contextmanager
def no_writes():
    """Apply after fixture setup; allow actual reads, prohibit every writer seam."""
    original_open = Path.open
    original_os_open = os.open

    def opened(path, mode='r', *args, **kwargs):
        if any(letter in mode for letter in 'wax+'):
            raise AssertionError('preview attempted a file write')
        return original_open(path, mode, *args, **kwargs)

    def low_open(path, flags, *args, **kwargs):
        if flags & (os.O_WRONLY | os.O_RDWR | os.O_CREAT | os.O_TRUNC | os.O_APPEND):
            raise AssertionError('preview attempted a low-level write')
        return original_os_open(path, flags, *args, **kwargs)

    with contextlib.ExitStack() as stack:
        stack.enter_context(patch.object(Path, 'open', opened))
        stack.enter_context(patch.object(os, 'open', low_open))
        for method in ('mkdir', 'unlink', 'rmdir', 'rename', 'replace', 'write_bytes', 'write_text'):
            stack.enter_context(patch.object(Path, method, side_effect=AssertionError('preview mutation')))
        for method in ('mkdir', 'unlink', 'remove', 'rmdir', 'rename', 'replace'):
            stack.enter_context(patch.object(os, method, side_effect=AssertionError('preview mutation')))
        for name in ('_initialize_registry', '_locked', '_atomic_write', 'reserve_prepare',
                     'record_closed', 'record_state', 'plan_retirement', 'record_retired'):
            stack.enter_context(patch.object(storage, name, side_effect=AssertionError('preview mutator')))
        stack.enter_context(patch.object(ctypes, 'WinDLL', create=True, side_effect=AssertionError('native call')))
        stack.enter_context(patch.object(subprocess, 'Popen', side_effect=AssertionError('process call')))
        yield


class PreviewImportTests(unittest.TestCase):
    def test_import_is_io_free_and_both_public_sources_keep_python39_syntax(self):
        try:
            cli = importlib.import_module('benchmarks.receipt_avd_retirement_preview')
        except ModuleNotFoundError:
            self.fail('preview CLI feature is unavailable, not a behavioral bypass')
        for module in (storage, cli):
            ast.parse(Path(module.__file__).read_text(encoding='utf8'), feature_version=(3, 9))
        try:
            with contextlib.ExitStack() as stack:
                for method in ('resolve', 'stat', 'lstat', 'open', 'mkdir'):
                    stack.enter_context(patch.object(Path, method, side_effect=AssertionError('import IO')))
                stack.enter_context(patch.object(ctypes, 'WinDLL', create=True, side_effect=AssertionError('native IO')))
                stack.enter_context(patch.object(subprocess, 'Popen', side_effect=AssertionError('process IO')))
                importlib.reload(storage)
                importlib.reload(cli)
        finally:
            importlib.reload(storage)
            importlib.reload(cli)


@unittest.skipUnless(os.name == 'nt', 'Existing storage contract requires physical D: fixtures')
class RetirementPreviewTests(unittest.TestCase):
    def fixture(self, *, pinned=False):
        fixture = fixtures.TinyRetirement(image_names=IMAGE_NAMES)
        if not pinned:
            # Real closed-state API clears TinyRetirement's earlier fixture plan.
            storage.record_closed(fixture.root, fixture.closure, fixture.registry)
            self.assertIsNone(fixture.entry()['retirement'])
        return fixture

    def preview(self, fixture, **kwargs):
        function = getattr(storage, 'preview_retirement', None)
        self.assertTrue(callable(function), 'preview feature unavailable; not a product behavioral RED')
        return function(fixture.root, fixture.evidence, registry=fixture.registry, **kwargs)

    def cli(self):
        try:
            return importlib.import_module('benchmarks.receipt_avd_retirement_preview')
        except ModuleNotFoundError:
            self.fail('preview CLI feature unavailable; not a product behavioral RED')

    def main(self, fixture, output, extra=()):
        cli = self.cli()
        stdout, stderr = io.StringIO(), io.StringIO()
        with patch.object(cli.storage, 'DEFAULT_REGISTRY', fixture.registry), \
                contextlib.redirect_stdout(stdout), contextlib.redirect_stderr(stderr):
            code = cli.main(['--root', str(fixture.root), '--evidence-manifest', str(fixture.evidence),
                             '--output', str(output)] + list(extra))
        return code, stdout.getvalue(), stderr.getvalue()

    def assert_refused(self, callback, reason=None):
        with self.assertRaises(storage.StorageRefused) as caught:
            callback()
        if reason is not None:
            self.assertEqual(str(caught.exception), reason)

    def while_first_image_is_hashed(self, fixture, change):
        original = storage.binding
        changed = []

        def observed(path):
            result = original(path)
            if Path(path) == fixture.images[0] and not changed:
                changed.append(True)
                change()
            return result
        return patch.object(storage, 'binding', side_effect=observed), changed

    def test_full_nine_image_preview_is_an_exact_snapshot_without_any_write_or_lock(self):
        fixture = self.fixture()
        before = snapshot(fixture.base)
        ledger = storage.binding(fixture.registry / 'ledger-v1.json')
        with no_writes():
            result = self.preview(fixture)
        self.assertEqual(snapshot(fixture.base), before)
        self.assertEqual(set(result), PREVIEW_KEYS)
        self.assertIs(type(result['version']), int)
        self.assertEqual((result['version'], result['scope']), (1, 'receipt-avd-retirement-preview-v1'))
        self.assertEqual(result['ledger_binding'], ledger)
        self.assertEqual(result['plan'], fixture.plan)
        self.assertEqual({Path(pin['path']).relative_to(fixture.root).as_posix()
                          for pin in result['plan']['remove']},
                         {storage.CONTENT + name for name in IMAGE_NAMES})
        self.assertEqual(result['remove_bytes'], sum(len(path.read_bytes()) for path in fixture.images))
        self.assertEqual(result['preserve_bytes'], sum(pin['bytes'] for pin in fixture.plan['preserve']))
        self.assertIs(result['snapshot_only'], True)
        for key in ('pins_plan', 'deletes_images', 'registry_written'):
            self.assertIs(result[key], False)
        self.assertIsNone(fixture.entry()['retirement'])
        self.assertFalse((fixture.registry / 'admission.lock').exists())

    def test_existing_pinned_plan_is_preserved_and_mutating_returned_data_changes_no_disk(self):
        fixture = self.fixture(pinned=True)
        before = snapshot(fixture.base)
        with no_writes():
            result = self.preview(fixture)
        self.assertIs(result['pins_plan'], False)
        result['plan']['remove'].clear()
        result['plan']['preserve'][0]['sha256'] = '0' * 64
        result['ledger_binding']['bytes'] = 0
        self.assertEqual(fixture.entry()['retirement'], fixture.plan)
        self.assertEqual(snapshot(fixture.base), before)
        self.assertEqual(self.preview(fixture)['plan'], fixture.plan)

    def test_missing_registry_ledger_untracked_and_not_closed_never_initialize_or_pin(self):
        for fault in ('registry', 'ledger', 'untracked', 'not-closed', 'malformed'):
            fixture = self.fixture()
            ledger_path = fixture.registry / 'ledger-v1.json'
            if fault == 'registry':
                fixture.registry = fixture.base / 'never-created-registry'
            elif fault == 'ledger':
                ledger_path.unlink()
            elif fault == 'malformed':
                ledger_path.write_bytes(b'{"version":1,"version":1}')
            else:
                ledger = storage.read_json(ledger_path)
                if fault == 'untracked': ledger['entries'] = []
                else:
                    ledger['entries'][0].update(state='retained', closure=None, retirement=None,
                                                 reserved_bytes=storage.RESERVATION_BYTES)
                fixture.write(ledger_path, ledger)
            before = snapshot(fixture.base)
            with self.subTest(fault=fault), no_writes():
                self.assert_refused(lambda: self.preview(fixture))
            self.assertEqual(snapshot(fixture.base), before)

    def test_real_closure_copies_manifest_scope_and_unknown_images_still_gate_preview(self):
        for fault in ('copy-missing', 'copy-drift', 'preserved-drift', 'manifest-incomplete',
                      'foreign-root', 'partial-proofs', 'unknown-image'):
            fixture = self.fixture()
            manifest = storage.read_json(fixture.evidence)
            if fault == 'copy-missing': Path(manifest['files'][0]['binding']['path']).unlink()
            elif fault == 'copy-drift': Path(manifest['files'][0]['binding']['path']).write_bytes(b'changed copy')
            elif fault == 'preserved-drift': (fixture.root / 'failed-output.bin').write_bytes(b'changed original')
            elif fault == 'manifest-incomplete':
                manifest['complete'] = False; fixture.write(fixture.evidence, manifest)
            elif fault == 'foreign-root':
                manifest['root'] = str(fixture.base / 'other-guest'); fixture.write(fixture.evidence, manifest)
            elif fault == 'unknown-image': fixture.write(fixture.root / 'unreviewed.img', b'tiny unknown image')
            else:
                closure = storage.read_json(fixture.closure); closure.pop('after')
                fixture.write(fixture.closure, closure)
                ledger_path = fixture.registry / 'ledger-v1.json'
                ledger = storage.read_json(ledger_path)
                ledger['entries'][0]['closure'] = storage.binding(fixture.closure)
                fixture.write(ledger_path, ledger)
            before = snapshot(fixture.base)
            with self.subTest(fault=fault), no_writes():
                self.assert_refused(lambda: self.preview(fixture))
            self.assertEqual(snapshot(fixture.base), before)

    def test_observed_lock_at_entry_or_after_hashing_refuses_without_reclaiming_it(self):
        fixture = self.fixture()
        lock = fixture.registry / 'admission.lock'
        lock.write_bytes(b'other owner retained')
        before = snapshot(fixture.base)
        with no_writes(): self.assert_refused(lambda: self.preview(fixture), 'registry_locked')
        self.assertEqual(snapshot(fixture.base), before)
        second = self.fixture()
        late = second.registry / 'admission.lock'
        hook, changed = self.while_first_image_is_hashed(second, lambda: late.write_bytes(b'new contender'))
        with hook: self.assert_refused(lambda: self.preview(second), 'registry_locked')
        self.assertTrue(changed)
        self.assertEqual(late.read_bytes(), b'new contender')
        self.assertIsNone(second.entry()['retirement'])

    def test_ledger_bytes_changed_during_real_image_hashing_refuse_even_if_json_remains_valid(self):
        fixture = self.fixture()
        ledger = fixture.registry / 'ledger-v1.json'
        before = ledger.read_bytes()
        hook, changed = self.while_first_image_is_hashed(fixture, lambda: ledger.write_bytes(before + b' '))
        with hook: self.assert_refused(lambda: self.preview(fixture), 'preview_ledger_changed')
        self.assertTrue(changed)
        self.assertEqual(ledger.read_bytes(), before + b' ')
        self.assertIsNone(fixture.entry()['retirement'])

    def test_new_retained_record_after_initial_scan_refuses_the_snapshot_without_a_plan_pin(self):
        fixture = self.fixture()
        added = fixture.root / 'late-retained-record.txt'
        hook, changed = self.while_first_image_is_hashed(fixture, lambda: added.write_bytes(b'late record'))
        with hook: self.assert_refused(lambda: self.preview(fixture), 'preview_guest_tree_changed')
        self.assertTrue(changed)
        self.assertEqual(added.read_bytes(), b'late record')
        self.assertIsNone(fixture.entry()['retirement'])

    def test_late_preserved_copy_and_closure_changes_are_rechecked_after_images(self):
        for role in ('preserved', 'copy', 'closure'):
            fixture = self.fixture()
            targets = {'preserved': fixture.root / 'failed-output.bin', 'closure': fixture.closure,
                       'copy': Path(storage.read_json(fixture.evidence)['files'][0]['binding']['path'])}
            target = targets[role]
            hook, changed = self.while_first_image_is_hashed(fixture, lambda: target.write_bytes(b'late changed bytes'))
            with self.subTest(role=role), hook:
                self.assert_refused(lambda: self.preview(fixture))
            self.assertTrue(changed)
            self.assertEqual(target.read_bytes(), b'late changed bytes')
            self.assertFalse((fixture.registry / 'admission.lock').exists())

    def test_hardlinked_and_reparse_inputs_refuse_before_following_any_alias(self):
        fixture = self.fixture()
        os.link(fixture.images[0], fixture.base / 'own-tiny-hardlink')
        before = snapshot(fixture.base)
        with no_writes(): self.assert_refused(lambda: self.preview(fixture))
        self.assertEqual(snapshot(fixture.base), before)
        second = self.fixture()
        original = Path.lstat

        def reparse(path, *args, **kwargs):
            info = original(path, *args, **kwargs)
            if path == second.images[0]:
                from types import SimpleNamespace
                return SimpleNamespace(st_mode=info.st_mode, st_nlink=info.st_nlink,
                                       st_file_attributes=getattr(info, 'st_file_attributes', 0) | 0x400)
            return info
        with patch.object(Path, 'lstat', reparse), no_writes():
            self.assert_refused(lambda: self.preview(second), 'linked_path')

    def test_preview_envelope_is_not_an_executor_plan_and_never_acquires_native_images(self):
        fixture = self.fixture()
        result = self.preview(fixture)
        path = fixture.base / 'snapshot-only-preview.json'; fixture.write(path, result)
        with patch.object(executor.windows, 'WindowsImageSet', side_effect=AssertionError('native ownership')) as native:
            with self.assertRaises(executor.RetirementRefused):
                executor._execute(storage.binding(path), fixture.output, fixture.registry, execute_reviewed_plan=True)
        native.assert_not_called()
        self.assertFalse(fixture.output.exists())
        self.assertIsNone(fixture.entry()['retirement'])
        self.assertTrue(all(path.is_file() for path in fixture.images))

    def test_cli_creates_only_the_explicit_external_result_and_prints_its_actual_binding(self):
        fixture = self.fixture()
        output = fixture.base / 'explicit-preview-result.json'
        before = snapshot(fixture.base)
        original = Path.open

        def opened(path, mode='r', *args, **kwargs):
            if any(letter in mode for letter in 'wax+'):
                self.assertEqual(path, output); self.assertEqual(mode, 'xb')
            return original(path, mode, *args, **kwargs)
        with patch.object(Path, 'open', opened), \
                patch.object(storage, '_locked', side_effect=AssertionError('CLI registry lock')), \
                patch.object(subprocess, 'Popen', side_effect=AssertionError('CLI process')):
            code, stdout, stderr = self.main(fixture, output)
        self.assertEqual(code, 0)
        self.assertEqual(json.loads(stdout), storage.binding(output))
        result = storage.read_json(output)
        self.assertEqual(result['scope'], 'receipt-avd-retirement-preview-v1')
        self.assertEqual(result['plan'], fixture.plan)
        after = snapshot(fixture.base); after.pop(output.relative_to(fixture.base).as_posix())
        self.assertEqual(after, before)
        self.assertNotIn(str(fixture.root), stderr)
        self.assertIsNone(fixture.entry()['retirement'])

    def test_cli_rejects_existing_linked_missing_parent_registry_and_every_tracked_guest_output(self):
        for fault in ('existing', 'linked', 'parent-missing', 'unsafe-stream', 'registry', 'selected-guest', 'other-guest'):
            fixture = self.fixture()
            output = fixture.base / 'refused-preview.json'
            if fault in ('existing', 'linked'):
                output.write_bytes(b'original retained output')
                if fault == 'linked': os.link(output, fixture.base / 'own-output-alias')
            elif fault == 'parent-missing': output = fixture.base / 'missing-parent/result.json'
            elif fault == 'unsafe-stream': output = fixture.base / 'result.json:stream'
            elif fault == 'registry': output = fixture.registry / 'not-allowed.json'
            elif fault == 'selected-guest': output = fixture.root / 'not-allowed.json'
            else:
                other = fixture.base / 'other-tracked-guest'
                storage.reserve_prepare(other, 'a' * 64, fixture.registry); other.mkdir()
                output = other / 'not-allowed.json'
            before = snapshot(fixture.base)
            with self.subTest(fault=fault):
                code, stdout, stderr = self.main(fixture, output)
                self.assertEqual(code, 1); self.assertEqual(stdout, '')
                self.assertNotIn(str(fixture.base), stderr)
                self.assertEqual(snapshot(fixture.base), before)

    def test_cli_unknown_registry_or_execution_switch_refuses_before_preview_io(self):
        fixture = self.fixture(); cli = self.cli()
        for option in ('--registry', '--execute-reviewed-plan', '--execute'):
            with self.subTest(option=option), patch.object(storage, 'preview_retirement', side_effect=AssertionError('unexpected preview')):
                with self.assertRaises(SystemExit) as caught:
                    self.main(fixture, fixture.base / 'not-created.json', (option,))
                self.assertEqual(caught.exception.code, 2)
        self.assertFalse((fixture.base / 'not-created.json').exists())

    def test_cli_partial_output_write_failure_keeps_partial_file_and_never_mutates_registry(self):
        fixture = self.fixture(); output = fixture.base / 'partial-output.json'
        before = snapshot(fixture.base); original = Path.open

        class FailingWriter:
            def __init__(self, file): self.file = file
            def __enter__(self): self.file.__enter__(); return self
            def __exit__(self, *args): return self.file.__exit__(*args)
            def write(self, data):
                self.file.write(data[:17]); self.file.flush()
                raise OSError('synthetic output interruption')
            def __getattr__(self, name): return getattr(self.file, name)

        def opened(path, mode='r', *args, **kwargs):
            stream = original(path, mode, *args, **kwargs)
            return FailingWriter(stream) if path == output and mode == 'xb' else stream
        with patch.object(Path, 'open', opened):
            code, stdout, stderr = self.main(fixture, output)
        self.assertEqual(code, 1); self.assertEqual(stdout, '')
        self.assertEqual(output.stat().st_size, 17)
        after = snapshot(fixture.base); after.pop(output.relative_to(fixture.base).as_posix())
        self.assertEqual(after, before)
        self.assertNotIn(str(fixture.base), stderr)
        self.assertIsNone(fixture.entry()['retirement'])
