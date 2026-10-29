"""Original ELF/ZIP symbol adversaries; no Android tool or native execution.

Copyright 2026 LocalLore contributors. SPDX-License-Identifier: Apache-2.0
"""
from pathlib import Path
import struct
import tempfile
import unittest
from unittest.mock import patch
import zipfile
from scripts.tests import test_audit_apk as legacy

audit = legacy.audit
SYMBOL = b"Java_org_locallore_app_NativeModelPublication_publishNoReplace"


def sections(data):
    return struct.unpack_from("<Q", data, 40)[0]


def symbol_offset(data):
    return struct.unpack_from("<Q", data, sections(data) + 3 * 64 + 24)[0] + 24


def candidate(directory, overrides):
    original, hashes, notices = legacy.ApkAuditTests().candidate_archive(directory)
    result = Path(directory) / "publication.apk"
    with zipfile.ZipFile(original) as source, zipfile.ZipFile(result, "w") as target:
        for old in source.infolist():
            contents = overrides.get(old.filename, source.read(old))
            entry = zipfile.ZipInfo(old.filename)
            if old.filename.endswith(".so"):
                offset = target.fp.tell() + 30 + len(entry.filename.encode())
                padding = (16384 - (offset + 4) % 16384) % 16384
                entry.extra = struct.pack("<HH", 0xCAFE, padding) + bytes(padding)
            target.writestr(entry, contents)
    return result, hashes, notices


class PublicationAuditTests(unittest.TestCase):
    def assert_symbol_refused(self, mutate):
        data = legacy.library(publication=True)
        mutate(data)
        with self.assertRaises(audit.AuditError):
            audit.elf_model_publication_export(data, 62)

    def test_candidate_requires_defined_export_in_each_abi(self):
        # Integration RED on the old auditor: its alignment-only ELF check lets
        # each missing publication export through a complete pinned SDK APK.
        for abi, machine in audit.ABIS.items():
            with self.subTest(abi=abi), tempfile.TemporaryDirectory() as directory:
                path, hashes, notices = candidate(directory, {f"lib/{abi}/liblocallore_android.so": legacy.library(machine)})
                with patch.dict(audit.LITERT_NATIVE_HASHES, hashes, clear=True), patch.dict(audit.LITERT_NOTICES, notices, clear=True):
                    with self.assertRaisesRegex(audit.AuditError, "publication|symbol|section"):
                        audit.audit_zip(path, litert=True)

    def test_defined_global_default_function_accepts_both_abis(self):
        for machine in audit.ABIS.values():
            with self.subTest(machine=machine):
                self.assertEqual(audit.elf_model_publication_export(legacy.library(machine, publication=True), machine), SYMBOL.decode())
        with tempfile.TemporaryDirectory() as directory:
            path, hashes, notices = candidate(directory, {})
            with patch.dict(audit.LITERT_NATIVE_HASHES, hashes, clear=True), patch.dict(audit.LITERT_NOTICES, notices, clear=True):
                self.assertEqual(len(audit.audit_zip(path, litert=True)), 6)

    def test_ordinary_profile_retains_alignment_only_contract(self):
        with tempfile.TemporaryDirectory() as directory:
            path = legacy.ApkAuditTests().archive(directory)
            with patch.object(audit, "elf_model_publication_export", side_effect=AssertionError("candidate-only check")) as checked:
                self.assertEqual(len(audit.audit_zip(path)), 4)
                checked.assert_not_called()

    def test_literal_name_without_dynamic_symbol_is_not_an_export(self):
        data = legacy.library()
        data.extend(b"\0" + SYMBOL + b"\0")
        with self.assertRaises(audit.AuditError): audit.elf_model_publication_export(data, 62)
        self.assert_symbol_refused(lambda d: struct.pack_into("<I", d, symbol_offset(d), 0))

    def test_undefined_local_weak_hidden_or_non_function_symbol_is_refused(self):
        for field, value in (("section", 0), ("section", 0xFFF1), ("section", 0xFFFF),
                             ("binding", 0x02), ("binding", 0x22), ("binding", 0x11),
                             ("visibility", 1), ("visibility", 2), ("visibility", 3)):
            with self.subTest(field=field, value=value):
                def change(data):
                    offset = symbol_offset(data)
                    if field == "section": struct.pack_into("<H", data, offset + 6, value)
                    else: data[offset + (4 if field == "binding" else 5)] = value
                self.assert_symbol_refused(change)

    def test_symbol_must_fit_executable_file_backed_definition_and_load(self):
        changes = (
            lambda d: struct.pack_into("<I", d, sections(d) + 64 + 4, 8),  # NOBITS is not code.
            lambda d: struct.pack_into("<Q", d, sections(d) + 64 + 8, 2),  # Allocated but not executable.
            lambda d: struct.pack_into("<Q", d, symbol_offset(d) + 8, 0),
            lambda d: struct.pack_into("<Q", d, symbol_offset(d) + 8, 144),
            lambda d: struct.pack_into("<Q", d, symbol_offset(d) + 16, 0),
            lambda d: struct.pack_into("<Q", d, symbol_offset(d) + 16, 17),
            lambda d: struct.pack_into("<I", d, 64 + 4, 4),  # LOAD not executable.
            lambda d: struct.pack_into("<Q", d, 64 + 16, 16384),  # Section/symbol unmapped.
        )
        for index, change in enumerate(changes):
            with self.subTest(index=index): self.assert_symbol_refused(change)

    def test_section_table_and_symbol_table_bounds_are_closed(self):
        changes = (
            lambda d: struct.pack_into("<Q", d, 40, len(d) - 32),
            lambda d: struct.pack_into("<H", d, 58, 32),
            lambda d: struct.pack_into("<H", d, 60, 0),
            lambda d: struct.pack_into("<H", d, 60, 8193),
            lambda d: struct.pack_into("<Q", d, sections(d) + 64 + 24, len(d) + 1),
            lambda d: struct.pack_into("<Q", d, sections(d) + 64 + 32, len(d)),
            lambda d: struct.pack_into("<I", d, sections(d) + 3 * 64 + 40, 4),
            lambda d: struct.pack_into("<I", d, sections(d) + 2 * 64 + 4, 1),
            lambda d: struct.pack_into("<Q", d, sections(d) + 3 * 64 + 56, 16),
            lambda d: struct.pack_into("<Q", d, sections(d) + 3 * 64 + 32, 47),
            lambda d: struct.pack_into("<I", d, symbol_offset(d), 0xFFFFFFFF),
        )
        for index, change in enumerate(changes):
            with self.subTest(index=index): self.assert_symbol_refused(change)

    def test_symbol_name_must_be_terminated_and_exact(self):
        def no_terminator(data):
            strings = struct.unpack_from("<Q", data, sections(data) + 2 * 64 + 24)[0]
            data[strings + len(SYMBOL) + 1] = ord("x")
        self.assert_symbol_refused(no_terminator)
        def suffix_name(data):
            strings = struct.unpack_from("<Q", data, sections(data) + 2 * 64 + 24)[0]
            data[strings + len(SYMBOL)] = ord("X")
        self.assert_symbol_refused(suffix_name)

    def test_wrong_machine_and_truncation_cannot_escape_as_struct_error(self):
        with self.assertRaises(audit.AuditError): audit.elf_model_publication_export(legacy.library(183, publication=True), 62)
        for count in (0, 63, 119, 128, 250):
            with self.subTest(count=count), self.assertRaises(audit.AuditError):
                audit.elf_model_publication_export(legacy.library(publication=True)[:count], 62)


if __name__ == "__main__": unittest.main()
