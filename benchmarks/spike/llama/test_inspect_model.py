import importlib.util
from pathlib import Path
import struct
import tempfile
import unittest

spec = importlib.util.spec_from_file_location("inspect_gguf", Path(__file__).with_name("inspect_model.py"))
inspect_gguf = importlib.util.module_from_spec(spec)
spec.loader.exec_module(inspect_gguf)


class MetadataTests(unittest.TestCase):
    def test_wrong_and_truncated_header_fail(self):
        for content in (b"", b"GGUF", b"GGUF" + struct.pack("I", 2)):
            with tempfile.TemporaryDirectory() as directory:
                path = Path(directory) / "synthetic.gguf"
                path.write_bytes(content)
                with self.assertRaises(ValueError):
                    inspect_gguf.inspect(path)

    def test_metadata_count_is_bounded(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "synthetic.gguf"
            path.write_bytes(b"GGUF" + struct.pack("<IQQ", 3, 0, 4097))
            with self.assertRaisesRegex(ValueError, "metadata_limit"):
                inspect_gguf.inspect(path)

    def test_untrusted_metadata_string_cannot_request_huge_read(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "synthetic.gguf"
            path.write_bytes(b"GGUF" + struct.pack("<IQQQ", 3, 0, 1, 2**40))
            with self.assertRaisesRegex(ValueError, "metadata_limit"):
                inspect_gguf.inspect(path)


if __name__ == "__main__":
    unittest.main()
