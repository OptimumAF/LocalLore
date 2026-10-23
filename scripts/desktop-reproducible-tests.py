#!/usr/bin/env python3
"""Synthetic comparator/refusal checks. No compiler, app, worker or model runs."""
import argparse
import importlib.util
import json
import os
from pathlib import Path
import struct
import tempfile
import unittest
from unittest.mock import patch
import zipfile

spec = importlib.util.spec_from_file_location("repro", Path(__file__).with_name("desktop-reproducible.py"))
repro = importlib.util.module_from_spec(spec)
spec.loader.exec_module(repro)


def synthetic_pe(text=b"synthetic section"):
    data = bytearray(512 + len(text))
    data[:2] = b"MZ"
    struct.pack_into("<I", data, 0x3c, 0x80)
    data[0x80:0x84] = b"PE\0\0"
    struct.pack_into("<HHIIIHH", data, 0x84, 0x8664, 1, 1234, 0, 0, 0, 0x22)
    struct.pack_into("<8sIIII", data, 0x98, b".test", len(text), 0x1000, len(text), 512)
    data[512:] = text
    return bytes(data)


class ReproTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="locallore-app-repro-test-")
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)

    def package(self, name, change=None, timestamp=(2026, 1, 1, 0, 0, 0), reverse=False):
        directory = self.root / name
        directory.mkdir()
        files = {"LocalLore Desktop.exe": synthetic_pe(), "build-manifest.json": b'{"fixed":true}',
                 "README.txt": b"synthetic package"}
        if change:
            files.update(change)
        for filename, data in files.items():
            (directory / filename).write_bytes(data)
        entries = list(sorted(files.items()))
        if reverse:
            entries.reverse()
        with zipfile.ZipFile(directory.with_suffix(".zip"), "x", compression=zipfile.ZIP_DEFLATED) as archive:
            for filename, data in entries:
                info = zipfile.ZipInfo(filename, date_time=timestamp)
                info.compress_type = zipfile.ZIP_DEFLATED
                info.external_attr = 0o100644 << 16
                archive.writestr(info, data)
        return directory

    def test_identical_actual_bytes_and_all_members_pass(self):
        result = repro.compare_packages(self.package("first"), self.package("longer second"))
        self.assertTrue(result["equal"])
        self.assertEqual(result["left_pe"]["sections"][0]["name"], ".test")
        self.assertIsNone(result["archive"]["first_different_offset"])

    def test_one_pe_byte_difference_is_not_normalized(self):
        changed = bytearray(synthetic_pe())
        changed[-1] ^= 1
        result = repro.compare_packages(self.package("first"), self.package("second", {"LocalLore Desktop.exe": changed}))
        self.assertFalse(result["equal"])
        self.assertFalse(result["executable"]["equal"])
        self.assertNotEqual(result["left_pe"]["sections"], result["right_pe"]["sections"])

    def test_manifest_difference_cannot_be_excluded(self):
        result = repro.compare_packages(self.package("first"), self.package("second", {"build-manifest.json": b'{"fixed":false}'}))
        self.assertFalse(result["equal"])
        self.assertIn("build-manifest.json", result["changed_zip_members_or_metadata"])
        self.assertTrue(result["executable"]["equal"])

    def test_zip_timestamp_difference_fails_with_equal_payloads(self):
        result = repro.compare_packages(self.package("first"), self.package("second", timestamp=(2026, 1, 2, 0, 0, 0)))
        self.assertFalse(result["equal"])
        self.assertTrue(result["folder_inventory_equal"])
        self.assertFalse(result["zip_metadata_and_member_order_equal"])

    def test_zip_member_order_difference_fails(self):
        result = repro.compare_packages(self.package("first"), self.package("second", reverse=True))
        self.assertFalse(result["equal"])
        self.assertTrue(result["folder_inventory_equal"])

    def test_zip_archive_comment_difference_fails(self):
        left, right = self.package("first"), self.package("second")
        with zipfile.ZipFile(right.with_suffix(".zip"), "a") as archive:
            archive.comment = b"nondeterministic metadata"
        result = repro.compare_packages(left, right)
        self.assertFalse(result["equal"])
        self.assertTrue(result["zip_metadata_and_member_order_equal"])
        self.assertFalse(result["archive"]["equal"])

    def test_frontend_tree_hashes_detect_content_and_extra_file(self):
        left, right = self.root / "left", self.root / "right"
        left.mkdir(); right.mkdir()
        (left / "app.js").write_bytes(b"normal")
        (right / "app.js").write_bytes(b"different")
        self.assertNotEqual(repro.tree_inventory(left), repro.tree_inventory(right))
        (right / "app.js").write_bytes(b"normal")
        (right / "extra.js").write_bytes(b"hook")
        self.assertNotEqual(repro.tree_inventory(left), repro.tree_inventory(right))

    def test_invalid_pe_and_out_of_bounds_sections_refuse(self):
        for data in (b"MZ", b"not PE", synthetic_pe()[:510]):
            with self.subTest(size=len(data)), self.assertRaises(ValueError):
                repro.pe_inventory(data)

    def test_new_output_no_overlap_and_no_overwrite(self):
        sentinel = self.root / "occupied"
        sentinel.mkdir()
        (sentinel / "keep").write_text("untouched")
        with self.assertRaisesRegex(ValueError, "new absolute"):
            repro.validate_destination(sentinel, [])
        with self.assertRaisesRegex(ValueError, "overlaps"):
            repro.validate_destination(self.root / "new", [self.root])
        self.assertEqual((sentinel / "keep").read_text(), "untouched")
        repro.validate_destination(self.root / "new space", [self.root / "unrelated"])

    def test_unsupported_unicode_and_relative_output_refuse(self):
        with self.assertRaisesRegex(ValueError, "ASCII"):
            repro.validate_destination(self.root / "unsupported-\u0394", [])
        with self.assertRaises(ValueError):
            repro.validate_destination(Path("relative"), [])

    def test_tree_and_file_budgets_refuse(self):
        (self.root / "too-big").write_bytes(b"012345")
        with self.assertRaises(ValueError):
            repro.ordinary(self.root / "too-big", 5)
        with patch.object(repro, "MAX_TREE", 5), self.assertRaisesRegex(ValueError, "tree budget"):
            repro.tree_inventory(self.root)

    def test_symlink_member_refuses_if_available(self):
        target = self.root / "target"
        target.write_bytes(b"synthetic")
        try:
            (self.root / "alias").symlink_to(target)
        except OSError:
            self.skipTest("symlink creation unavailable; no privilege setting changed")
        with self.assertRaisesRegex(ValueError, "Reparse"):
            repro.tree_inventory(self.root)

    def test_source_revision_drift_and_dirty_source_refuse(self):
        with patch.object(repro, "command", return_value="different"), self.assertRaisesRegex(ValueError, "revision"):
            repro.clean_source(self.root, "a" * 40)
        with patch.object(repro, "command", side_effect=["a" * 40, "modified"]), self.assertRaisesRegex(ValueError, "clean"):
            repro.clean_source(self.root, "a" * 40)

    def test_installed_lock_and_versions_must_match(self):
        package = self.root / "a"
        package.mkdir()
        (package / "package.json").write_text('{"version":"1"}')
        metadata = {"node_modules/a": {"version": "1", "integrity": "fixed", "resolved": "https://example.invalid/a"}}
        (self.root / ".package-lock.json").write_text(json.dumps({"packages": metadata}))
        result = repro.dependency_inventory(self.root, {"packages": metadata})
        self.assertEqual(result["versions"], {"node_modules/a": "1"})
        (package / "package.json").write_text('{"version":"2"}')
        with self.assertRaisesRegex(ValueError, "version differs"):
            repro.dependency_inventory(self.root, {"packages": metadata})

    def test_unapproved_worker_fails_before_subprocess_or_output(self):
        worker = self.root / "unapproved.exe"
        worker.write_bytes(b"MZ synthetic never executed")
        args = argparse.Namespace(source_commit="a" * 40, node=self.root / "node.exe",
            npm_cli=self.root / "npm-cli.js", dependencies=self.root / "dependencies",
            worker=worker, output=self.root / "new output")
        with patch.object(repro.sys, "platform", "win32"), patch.dict(os.environ, {}, clear=True), \
             patch.object(repro, "command") as child, self.assertRaisesRegex(ValueError, "UnapprovedWorker"):
            repro.run(args)
        child.assert_not_called()
        self.assertFalse(args.output.exists())

    def test_write_new_never_overwrites_retained_evidence(self):
        path = self.root / "evidence.json"
        repro.write_new(path, {"first": True})
        with self.assertRaises(FileExistsError):
            repro.write_new(path, {"second": True})
        self.assertEqual(json.loads(path.read_bytes()), {"first": True})


if __name__ == "__main__":
    unittest.main()
