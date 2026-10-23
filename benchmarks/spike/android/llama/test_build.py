"""Synthetic acceptance failures for source pins and ELF qualification."""
import importlib.util
from pathlib import Path
import struct
import tempfile
import unittest
from unittest.mock import patch

spec = importlib.util.spec_from_file_location("android_llama_build", Path(__file__).with_name("build.py"))
build = importlib.util.module_from_spec(spec)
spec.loader.exec_module(build)


def executable():
    raw = bytearray(1024)
    raw[:6] = b"\x7fELF\x02\x01"
    struct.pack_into("<HH", raw, 16, 3, 62)
    struct.pack_into("<Q", raw, 32, 64)
    struct.pack_into("<HH", raw, 54, 56, 3)
    struct.pack_into("<IIQQQQQQ", raw, 64, 1, 5, 0, 0, 0, 1024, 1024, 16384)
    interp = b"/system/bin/linker64\0"
    struct.pack_into("<IIQQQQQQ", raw, 120, 3, 4, 256, 256, 0, len(interp), len(interp), 1)
    struct.pack_into("<IIQQQQQQ", raw, 176, 2, 6, 320, 320, 0, 64, 64, 8)
    raw[256:256 + len(interp)] = interp
    for index, pair in enumerate(((5, 512), (1, 0), (0x6ffffffb, 0x08000000), (0, 0))):
        struct.pack_into("<QQ", raw, 320 + index * 16, *pair)
    raw[512:520] = b"libc.so\0"
    return raw


def initialized_executable(relative=False, machine=62):
    raw = executable() + bytearray(1024)
    struct.pack_into("<H", raw, 18, machine)
    struct.pack_into("<Q", raw, 40, 1024)
    struct.pack_into("<HH", raw, 58, 64, 5)
    sections = (
        (0, 0, 0, 0, 0, 0, 0, 0, 0, 0),
        (0, 14, 0, 600, 600, 8, 0, 0, 8, 8),
        (0, 2, 0, 0, 640, 48, 3, 0, 8, 24),
        (0, 3, 0, 0, 704, 40, 0, 0, 1, 0),
        (0, 4, 0, 0, 768, 24, 0, 0, 8, 24),
    )
    for index, section in enumerate(sections):
        struct.pack_into("<IIQQQQIIQQ", raw, 1024 + index * 64, *section)
    symbol_name = b"\0locallore_android_arm_deadline\0"
    raw[704:704 + len(symbol_name)] = symbol_name
    struct.pack_into("<IBBHQQ", raw, 664, 1, 18, 0, 1, 900, 30)
    struct.pack_into("<Q", raw, 600, 0 if relative else 900)
    struct.pack_into("<QQq", raw, 768, 600, 8 if machine == 62 else 1027, 900 if relative else 0)
    return raw


class BuildTests(unittest.TestCase):
    def inspect(self, raw):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "binary"
            path.write_bytes(raw)
            return build.elf_report(path)

    def inspect_deadline(self, raw):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "binary"
            path.write_bytes(raw)
            return build.deadline_report(path)

    def test_deadline_initializer_direct_array_entry(self):
        result = self.inspect_deadline(initialized_executable())
        self.assertTrue(result["initializer_retained"])
        self.assertEqual(result["fixed_seconds"], 90)

    def test_deadline_initializer_x86_relative_relocation(self):
        self.assertTrue(self.inspect_deadline(initialized_executable(True))["initializer_retained"])

    def test_deadline_initializer_arm64_relative_relocation(self):
        self.assertTrue(self.inspect_deadline(initialized_executable(True, 183))["initializer_retained"])

    def test_rejects_deadline_symbol_without_retained_initializer(self):
        raw = initialized_executable()
        struct.pack_into("<Q", raw, 600, 0)
        with self.assertRaisesRegex(ValueError, "not retained"):
            self.inspect_deadline(raw)

    def test_rejects_missing_deadline_symbol(self):
        with self.assertRaisesRegex(ValueError, "absent"):
            self.inspect_deadline(executable())

    def test_valid_pie_has_exact_size_hash_dependencies_and_alignment(self):
        result = self.inspect(executable())
        self.assertEqual(result["bytes"], 1024)
        self.assertEqual(len(result["sha256"]), 64)
        self.assertEqual(result["needed"], ["libc.so"])
        self.assertEqual(result["load_alignments"], [16384])

    def test_rejects_non_elf_or_wrong_class(self):
        with self.assertRaises(ValueError):
            self.inspect(b"invalid")

    def test_rejects_4k_alignment(self):
        raw = executable()
        struct.pack_into("<Q", raw, 112, 4096)
        with self.assertRaisesRegex(ValueError, "aligned"):
            self.inspect(raw)

    def test_rejects_wrong_architecture(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "binary"
            path.write_bytes(executable())
            with self.assertRaisesRegex(ValueError, "architecture"):
                build.elf_report(path, 183)

    def test_rejects_non_pie(self):
        raw = executable()
        struct.pack_into("<Q", raw, 360, 0)
        with self.assertRaisesRegex(ValueError, "PIE"):
            self.inspect(raw)

    def test_rejects_unreviewed_shared_library(self):
        raw = executable()
        raw[512:527] = b"libc++_shared\0\0\0"
        with self.assertRaisesRegex(ValueError, "dependency"):
            self.inspect(raw)

    def test_wrong_source_pin_stops_before_build(self):
        with patch.object(build.subprocess, "check_output", return_value="other\n") as check:
            with self.assertRaisesRegex(ValueError, "revision"):
                build.source_check(Path("unused"))
            self.assertEqual(check.call_count, 1)

    def test_dirty_source_is_rejected(self):
        with patch.object(build.subprocess, "check_output", side_effect=[build.PIN, "?? injected.h\n"]):
            with self.assertRaisesRegex(ValueError, "source"):
                build.source_check(Path("unused"))


if __name__ == "__main__":
    unittest.main()
