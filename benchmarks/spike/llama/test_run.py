import copy
import importlib.util
import json
from pathlib import Path
import sys
import tempfile
import time
import unittest

spec = importlib.util.spec_from_file_location("llama_worker", Path(__file__).with_name("run.py"))
worker = importlib.util.module_from_spec(spec)
spec.loader.exec_module(worker)


def request():
    return dict(version=1, role="director", prompt="Original synthetic scene", max_tokens=350,
                context_tokens=4096, threads=4, schema={"type":"object"})


class WorkerTests(unittest.TestCase):
    def test_valid_request(self):
        value = request()
        self.assertEqual(value, worker.parse_request(json.dumps(value).encode()))

    def test_strict_keys_integer_types_and_bounds(self):
        for key, value in (("version", True), ("max_tokens", 351), ("max_tokens", 0),
                           ("max_tokens", 1.0), ("context_tokens", 8192), ("threads", 8),
                           ("role", "archivist"), ("prompt", ""), ("schema", []),
                           ("prompt", "secret\0suffix"), ("extra", "--server")):
            attempt = request()
            attempt[key] = value
            with self.subTest(key=key, value=value), self.assertRaises(ValueError):
                worker.parse_request(json.dumps(attempt).encode())

    def test_duplicate_nested_key_and_nonfinite_rejected(self):
        for raw in (b'{"version":1,"version":1}', b'{"x":NaN}',
                    json.dumps(request()).replace('"type": "object"', '"type":"object","type":"array"').encode()):
            with self.assertRaises(ValueError):
                worker.parse_request(raw)

    def test_oversize_invalid_utf8_and_multiple_documents_rejected(self):
        for raw in (b" " * 32769, b"\xff", json.dumps(request()).encode() + b" {}"):
            with self.assertRaises(ValueError):
                worker.parse_request(raw)

    def test_wrong_and_missing_model_never_load(self):
        with tempfile.TemporaryDirectory() as directory:
            model = Path(directory) / "synthetic-invalid.gguf"
            self.assertFalse(worker.verify_model(model))
            model.write_bytes(b"GGUF" + bytes(28))
            self.assertFalse(worker.verify_model(model))

    def test_capture_both_pipes_without_deadlock(self):
        code, stdout, error = worker.capture([sys.executable, "-c",
            "import sys; r=sys.stdin.buffer.read(); sys.stdout.buffer.write(r); sys.stderr.buffer.write(b'x'*8192)"],
            b"synthetic request")
        self.assertEqual((0, b"synthetic request", None), (code, stdout, error))

    def test_stdout_overflow_kills_and_bounds_capture(self):
        code, stdout, error = worker.capture([sys.executable, "-c",
            "import sys,time; sys.stdout.buffer.write(b'x'*200000); sys.stdout.flush(); time.sleep(30)"], b"")
        self.assertEqual(error, "output_limit")
        self.assertLessEqual(len(stdout), worker.MAX_CAPTURE)
        self.assertNotEqual(code, 0)

    def test_stderr_overflow_is_not_forwarded(self):
        _, stdout, error = worker.capture([sys.executable, "-c",
            "import sys,time; sys.stderr.buffer.write(b'PRIVATE'*40000); sys.stderr.flush(); time.sleep(30)"], b"")
        self.assertEqual((b"", "output_limit"), (stdout, error))

    def test_timeout_includes_child_not_reading_stdin(self):
        start = time.monotonic()
        code, stdout, error = worker.capture([sys.executable, "-c", "import time; time.sleep(30)"],
                                              b"x" * 32768, timeout=0.2)
        self.assertEqual((b"", "timeout"), (stdout, error))
        self.assertNotEqual(code, 0)
        self.assertLess(time.monotonic() - start, 3)

    def test_response_rejects_raw_chatter_unbounded_or_reasoning(self):
        good = worker.failure(None)
        good.update(status="completed", text="Visible synthetic output", error=None, load_ms=1,
                    generation_ms=2, input_tokens=25, output_tokens=4,
                    schema_enforced=True, template_applied=True, thinking_disabled=True)
        self.assertEqual(good, worker.validate_response(json.dumps(good).encode()))
        for key, value in (("text", "<think>private</think>"), ("text", "x" * 16385),
                           ("load_ms", float("nan")), ("input_tokens", 4097),
                           ("output_tokens", True), ("thinking_disabled", False), ("extra", "private")):
            attempt = copy.deepcopy(good)
            attempt[key] = value
            with self.subTest(key=key), self.assertRaises(ValueError):
                worker.validate_response(json.dumps(attempt).encode())
        with self.assertRaises(ValueError):
            worker.validate_response(b"native raw chatter\n" + json.dumps(good).encode())

    def test_error_responses_are_fixed_and_empty(self):
        self.assertEqual("model_load_failed", worker.validate_response(json.dumps(worker.failure("model_load_failed")).encode())["error"])
        for error, text in (("private path or story", ""), ("runtime_failed", "private output")):
            value = worker.failure(error)
            value["text"] = text
            with self.assertRaises(ValueError):
                worker.validate_response(json.dumps(value).encode())


if __name__ == "__main__":
    unittest.main()
