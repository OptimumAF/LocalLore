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


class BuildTests(unittest.TestCase):
    def inspect(self, raw):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "binary"
            path.write_bytes(raw)
            return build.elf_report(path)

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
