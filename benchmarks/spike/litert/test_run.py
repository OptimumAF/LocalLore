"""Finite worker boundary tests; no model/performance claims."""

import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import MagicMock, patch

spec = importlib.util.spec_from_file_location("litert_worker", Path(__file__).with_name("run.py"))
worker = importlib.util.module_from_spec(spec)
spec.loader.exec_module(worker)


def request():
    return dict(version=1, role="director", prompt="Synthetic fixture.",
                max_tokens=32, context_tokens=4096, threads=4, schema=None)


class RequestTests(unittest.TestCase):
    def test_exact_request(self):
        self.assertEqual(worker.parse_request(json.dumps(request()).encode()), request())

    def test_invalid_json_duplicate_nonfinite_and_extra(self):
        samples = [b"{", b"[]", b'{"version":1,"version":1}', b"NaN", b"\xff",
                   json.dumps(dict(request(), tool="execute")).encode(), b" " * 32769]
        for sample in samples:
            with self.subTest(sample=sample[:60]), self.assertRaisesRegex(worker.WorkerError, "invalid_request"):
                worker.parse_request(sample)

    def test_strict_types_ranges_and_required_keys(self):
        for key, values in {
            "version": [True, 2, None], "role": ["tool", [], None],
            "prompt": ["", " ", "x\x00", "\ud800", 1],
            "max_tokens": [True, 0, 351, 1.0], "context_tokens": [True, 8192, 4096.0],
            "threads": [True, 0, 8, 4.0], "schema": [[], "{}", True],
        }.items():
            for value in values:
                sample = request()
                sample[key] = value
                with self.subTest(key=key, value=value), self.assertRaisesRegex(worker.WorkerError, "invalid_request"):
                    worker.parse_request(json.dumps(sample).encode())
        sample = request()
        del sample["schema"]
        with self.assertRaises(worker.WorkerError):
            worker.parse_request(json.dumps(sample).encode())

    def test_final_channel_omits_thoughts(self):
        self.assertEqual(worker.final_text({"content": [{"type": "text", "text": "Visible."}],
                                            "channels": {"thought": "must not escape"}}), "Visible.")

    def test_tools_unknown_content_empty_and_oversize_rejected(self):
        for message in [None, {"tool_calls": [{}]}, {"content": []},
                        {"content": [{"type": "image", "path": "private"}]},
                        {"content": [{"type": "text", "text": "private", "channel": "thought"}]},
                        {"content": "x" * 16385}]:
            with self.subTest(message_type=type(message).__name__), self.assertRaises(worker.WorkerError):
                worker.final_text(message)

    def test_missing_model_is_sanitized(self):
        with tempfile.TemporaryDirectory() as directory:
            completed = subprocess.run(
                [sys.executable, str(Path(worker.__file__)), "--model", str(Path(directory) / "private-missing.litertlm")],
                input=json.dumps(request()).encode(), capture_output=True, timeout=15,
            )
            self.assertEqual(completed.returncode, 2)
            data = json.loads(completed.stdout)
            self.assertEqual(data, worker.result("model_missing"))
            self.assertEqual(completed.stderr, b"")
            self.assertNotIn(b"private", completed.stdout)

    def test_buffered_diagnostics_are_discarded_when_sdk_raises(self):
        script = """
import json, sys
sys.path.insert(0, sys.argv[1])
import run
try:
    with run.quiet_native():
        print('SYNTHETIC-PRIVATE-STDOUT-731', end='')
        print('SYNTHETIC-PRIVATE-STDERR-731', end='', file=sys.stderr)
        raise RuntimeError('SYNTHETIC-PRIVATE-EXCEPTION-731')
except RuntimeError:
    print(json.dumps(run.result('generation_failed')))
"""
        completed = subprocess.run(
            [sys.executable, "-c", script, str(Path(worker.__file__).parent)],
            capture_output=True, timeout=15,
        )
        self.assertEqual(completed.returncode, 0)
        self.assertEqual(json.loads(completed.stdout), worker.result("generation_failed"))
        self.assertEqual(completed.stderr, b"")
        self.assertNotIn(b"SYNTHETIC-PRIVATE", completed.stdout)

    def configured_fake(self):
        """Only worker ownership/settings tests; never real-model evidence."""
        lm = MagicMock()
        info = lm.ModelInfo.return_value.__enter__.return_value
        info.is_llm_model = True
        info.input_modalities.text = True
        info.supported_backends_for_modality.return_value = ["cpu"]
        info.max_context_tokens = 32768
        info.is_dynamic_context = True
        engine = lm.Engine.return_value.__enter__.return_value
        engine.tokenize.return_value = list(range(8))
        conversation = engine.create_conversation.return_value.__enter__.return_value
        conversation.render_message_to_string.return_value = "<synthetic template>"
        conversation.send_message.return_value = {
            "content": [{"type": "text", "text": "Visible."}],
            "channels": {"thought": "Never expose this."},
        }
        stats = conversation.get_benchmark_info.return_value
        stats.last_prefill_token_count = 9
        stats.last_decode_token_count = 4
        return lm, engine, conversation

    def test_caps_thinking_tool_isolation_and_cleanup(self):
        lm, engine, conversation = self.configured_fake()
        sample = dict(request(), schema={"type": "object"})
        with tempfile.TemporaryDirectory() as directory:
            model = Path(directory) / "synthetic.litertlm"
            model.touch()
            with patch.dict(sys.modules, {"litert_lm": lm}), patch.object(worker.importlib.metadata, "version", return_value="0.18.1"):
                output = worker.run(sample, model)
        self.assertEqual(output["text"], "Visible.")
        self.assertTrue(output["schema_enforced"])
        self.assertEqual(output["input_tokens"], 9)
        self.assertEqual(output["output_tokens"], 4)
        lm.ThinkingConfig.assert_called_once_with(enable_thinking=False, thinking_token_budget=0)
        self.assertEqual(lm.Engine.call_args.kwargs["max_num_tokens"], 4096)
        self.assertFalse(engine.create_conversation.call_args.kwargs["automatic_tool_calling"])
        self.assertNotIn("tools", engine.create_conversation.call_args.kwargs)
        self.assertEqual(conversation.send_message.call_args.kwargs["max_output_tokens"], 32)
        engine.create_conversation.return_value.__exit__.assert_called_once()
        lm.Engine.return_value.__exit__.assert_called_once()

    def test_context_overflow_never_sends_and_closes_both_owners(self):
        lm, engine, conversation = self.configured_fake()
        engine.tokenize.return_value = list(range(4090))
        with tempfile.TemporaryDirectory() as directory:
            model = Path(directory) / "synthetic.litertlm"
            model.touch()
            with patch.dict(sys.modules, {"litert_lm": lm}), patch.object(worker.importlib.metadata, "version", return_value="0.18.1"):
                with self.assertRaisesRegex(worker.WorkerError, "context_overflow"):
                    worker.run(request(), model)
        conversation.send_message.assert_not_called()
        engine.create_conversation.return_value.__exit__.assert_called_once()
        lm.Engine.return_value.__exit__.assert_called_once()

    def test_generation_failure_closes_without_exposing_exception(self):
        lm, engine, conversation = self.configured_fake()
        conversation.send_message.side_effect = RuntimeError("private model path or content")
        with tempfile.TemporaryDirectory() as directory:
            model = Path(directory) / "synthetic.litertlm"
            model.touch()
            with patch.dict(sys.modules, {"litert_lm": lm}), patch.object(worker.importlib.metadata, "version", return_value="0.18.1"):
                with self.assertRaisesRegex(worker.WorkerError, "^generation_failed$"):
                    worker.run(request(), model)
        engine.create_conversation.return_value.__exit__.assert_called_once()
        lm.Engine.return_value.__exit__.assert_called_once()


if __name__ == "__main__":
    unittest.main()
