"""Actual D: file guards. No SDK, subprocess, guest or model operation.

Copyright 2026 LocalLore contributors. SPDX-License-Identifier: Apache-2.0
"""
import hashlib
import io
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
from contextlib import redirect_stderr, redirect_stdout

from benchmarks import diagnostic_ui_build as build


class DiagnosticUiXmlAndCliTests(unittest.TestCase):
    def test_xml_requires_utf8_and_refuses_dtd_in_other_encodings(self):
        class Reader:
            def read(self, pin, data=False):
                return raw
        for raw in (b'<testsuite name="plain"/>',
                    '<!DOCTYPE testsuite [<!ENTITY s "expanded">]><testsuite name="&s;"/>'.encode(),
                    '<?xml version="1.0" encoding="UTF-16"?><!DOCTYPE testsuite [<!ENTITY s "expanded">]><testsuite name="&s;"/>'.encode("utf-16")):
            pin = {"path": "synthetic.xml", "bytes": len(raw), "sha256": hashlib.sha256(raw).hexdigest()}
            if raw.startswith(b"<testsuite"):
                self.assertEqual(build._xml(Reader(), pin).get("name"), "plain")
            else:
                with self.assertRaises(build.BuildRefused):
                    build._xml(Reader(), pin)

    def test_cli_pre_pin_exceptions_emit_only_fixed_refusal(self):
        from benchmarks import archive_ui_build
        raw = build.BASELINE_PATH.read_bytes()
        class Reader:
            def read(self, pin, data=False):
                return raw
            def final(self):
                pass
        for error in (FileNotFoundError("PRIVATE_PATH_SENTINEL"),
                      archive_ui_build.BuildRefused("PRIVATE_PATH_SENTINEL")):
            stdout, stderr = io.StringIO(), io.StringIO()
            with patch.object(build, "_Reader", return_value=Reader()), \
                 patch.object(archive_ui_build, "_pin", side_effect=error), \
                 redirect_stdout(stdout), redirect_stderr(stderr):
                self.assertEqual(build.main(["verify"]), 1)
            self.assertEqual(stdout.getvalue(), "")
            self.assertEqual(stderr.getvalue(), "diagnostic build refused: artifact\n")

    def test_cli_unknown_action_never_constructs_reader(self):
        with patch.object(build, "_Reader", side_effect=AssertionError("reader")), \
             redirect_stderr(io.StringIO()):
            self.assertEqual(build.main(["install"]), 2)


@unittest.skipUnless(os.name == "nt", "Physical D: guarded file tests")
class DiagnosticUiFileTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="diagnostic-ui-reader-")
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.assertEqual(self.root.drive.upper(), "D:")
        self.file = self.root / "fixture.bin"
        self.file.write_bytes(b"original-bytes")
        self.pin = {"path": str(self.file), "bytes": 14,
                    "sha256": hashlib.sha256(b"original-bytes").hexdigest()}

    def test_actual_guarded_bytes_cache_and_final_content_revalidation(self):
        reader = build._Reader()
        self.assertEqual(reader.read(self.pin), self.pin["sha256"])
        self.assertEqual(reader.read(self.pin, data=True), b"original-bytes")
        self.assertEqual(reader.total, 14)
        reader.final()
        self.assertEqual(reader.total, 28)

    def test_final_hash_refuses_same_inode_size_and_restored_mtime_mutation(self):
        reader = build._Reader()
        reader.read(self.pin)
        before = self.file.stat()
        self.file.write_bytes(b"replaced-bytes")
        os.utime(self.file, ns=(before.st_atime_ns, before.st_mtime_ns))
        self.assertEqual(self.file.stat().st_size, before.st_size)
        with self.assertRaises(ValueError):
            reader.final()

    def test_cached_path_cannot_rebind_to_different_digest(self):
        reader = build._Reader()
        reader.read(self.pin)
        with self.assertRaises(build.BuildRefused):
            reader.read(dict(self.pin, sha256="0" * 64))

    def test_hardlinked_file_is_refused_by_shared_reader(self):
        linked = self.root / "linked.bin"
        os.link(self.file, linked)
        reader = build._Reader()
        with self.assertRaises(ValueError):
            reader.read(self.pin)

    def test_read_budget_and_resident_budget_refuse_before_file_read(self):
        for name in ("MAX_TOTAL", "MAX_RESIDENT"):
            reader = build._Reader()
            with patch.object(build, name, 13), self.assertRaises(build.BuildRefused):
                reader.read(self.pin)

    def test_session_deadline_is_checked_before_and_after_reads(self):
        reader = build._Reader()
        with patch.object(build.time, "monotonic", return_value=reader.started + 121), self.assertRaises(build.BuildRefused):
            reader.read(self.pin)

    def test_parent_mutation_is_not_hidden_by_cached_file_bytes(self):
        reader = build._Reader()
        reader.read(self.pin)
        # A deterministic ancestor stamp mutation, independent of clock granularity.
        before = self.root.stat()
        os.utime(self.root, ns=(before.st_atime_ns, before.st_mtime_ns + 1000000000))
        with self.assertRaises(build.BuildRefused):
            reader.final()

    def test_dex_parser_receives_only_the_already_verified_bytes(self):
        from scripts import audit_physical_model_apk as parser
        reader = build._Reader()
        def decode(stream, *, with_code):
            self.assertIs(with_code, True)
            self.assertEqual(stream.read(), b"original-bytes")
            return {b"synthetic": (1, [])}
        with patch.object(parser, "dex_classes", side_effect=decode):
            self.assertEqual(reader.definitions(self.pin), {b"synthetic": (1, [])})
        reader.final()

    def test_json_size_limit_refuses_before_large_file_or_bad_binding_is_opened(self):
        reader = build._Reader()
        with self.assertRaises(build.BuildRefused):
            reader.json(dict(self.pin, bytes=build.MAX_JSON + 1))
        self.assertEqual(reader.total, 0)
