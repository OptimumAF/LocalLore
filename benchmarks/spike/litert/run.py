"""One-shot, CPU-only LiteRT-LM 0.18.1 compatibility worker.

Development experiment only. The coordinator verifies model bytes and owns the
outer process deadline/output cap. No tools, network fetches, cache directory,
story persistence, or automatic repair are configured here.
"""

from __future__ import annotations

import argparse
from contextlib import contextmanager
import importlib.metadata
import json
import os
from pathlib import Path
import sys
import time

MAX_REQUEST_BYTES = 32768
MAX_TEXT_BYTES = 16384
VERSION = "0.18.1"
REQUEST_KEYS = {
    "version", "role", "prompt", "max_tokens", "context_tokens", "threads", "schema"
}


class WorkerError(Exception):
    """Only fixed categories cross the worker boundary."""


def reject_duplicates(pairs):
    value = {}
    for key, item in pairs:
        if key in value:
            raise WorkerError("invalid_request")
        value[key] = item
    return value


def parse_request(data: bytes) -> dict:
    if len(data) > MAX_REQUEST_BYTES:
        raise WorkerError("invalid_request")
    try:
        request = json.loads(
            data.decode("utf-8"), object_pairs_hook=reject_duplicates,
            parse_constant=lambda _: (_ for _ in ()).throw(WorkerError("invalid_request")),
        )
    except (UnicodeError, ValueError, RecursionError):
        raise WorkerError("invalid_request") from None
    if not isinstance(request, dict) or set(request) != REQUEST_KEYS:
        raise WorkerError("invalid_request")
    if (
        type(request["version"]) is not int or request["version"] != 1
        or request["role"] not in ("director", "narrator")
        or not isinstance(request["prompt"], str) or not request["prompt"].strip()
        or "\x00" in request["prompt"]
        or type(request["max_tokens"]) is not int
        or not 1 <= request["max_tokens"] <= 350
        or type(request["context_tokens"]) is not int or request["context_tokens"] != 4096
        or type(request["threads"]) is not int or request["threads"] != 4
        or (request["schema"] is not None and not isinstance(request["schema"], dict))
    ):
        raise WorkerError("invalid_request")
    try:
        request["prompt"].encode("utf-8")
    except UnicodeError:
        raise WorkerError("invalid_request") from None
    return request


def result(error=None):
    return {
        "version": 1, "status": "error" if error else "completed", "text": "",
        "error": error, "load_ms": None, "generation_ms": None,
        "output_tokens": None, "input_tokens": None, "schema_enforced": False,
        "thinking_disabled": False, "template_applied": False,
    }


@contextmanager
def quiet_native():
    """Discard SDK diagnostics, including model paths and native CRT logging."""
    sys.stdout.flush()
    sys.stderr.flush()
    saved = [os.dup(fd) for fd in (1, 2)]
    try:
        with open(os.devnull, "wb") as sink:
            os.dup2(sink.fileno(), 1)
            os.dup2(sink.fileno(), 2)
            yield
            sys.stdout.flush()
            sys.stderr.flush()
    finally:
        for fd, original in zip((1, 2), saved):
            os.dup2(original, fd)
            os.close(original)


def final_text(message) -> str:
    """Never serialize reasoning channels, tool calls, or unknown content."""
    if not isinstance(message, dict) or message.get("tool_calls"):
        raise WorkerError("unsupported_output")
    content = message.get("content", [])
    if isinstance(content, str):
        content = [{"type": "text", "text": content}]
    if not isinstance(content, list):
        raise WorkerError("unsupported_output")
    parts = []
    for item in content:
        if not isinstance(item, dict) or item.get("type") != "text":
            raise WorkerError("unsupported_output")
        if item.get("channel") not in (None, "final"):
            raise WorkerError("unsupported_output")
        text = item.get("text")
        if not isinstance(text, str):
            raise WorkerError("unsupported_output")
        parts.append(text)
    text = "".join(parts)
    if not text or len(text.encode("utf-8")) > MAX_TEXT_BYTES:
        raise WorkerError("output_too_large" if text else "unsupported_output")
    return text


def run(request: dict, model_path: Path) -> dict:
    output = result()
    if not model_path.is_file():
        raise WorkerError("model_missing")
    if model_path.suffix.lower() != ".litertlm":
        raise WorkerError("model_invalid")
    try:
        if importlib.metadata.version("litert-lm-api") != VERSION:
            raise WorkerError("runtime_unavailable")
        import litert_lm as lm
    except (ImportError, OSError, importlib.metadata.PackageNotFoundError):
        raise WorkerError("runtime_unavailable") from None
    lm.set_min_log_severity(lm.LogSeverity.ERROR)
    try:
        with lm.ModelInfo(model_path) as info:
            if (
                not info.is_llm_model or not info.input_modalities.text
                or "cpu" not in info.supported_backends_for_modality(lm.LiteRtLmModality.TEXT)
                or info.max_context_tokens < request["context_tokens"]
                or (not info.is_dynamic_context and info.max_context_tokens != 4096)
            ):
                raise WorkerError("model_unsupported")
    except (RuntimeError, ValueError, OSError):
        raise WorkerError("model_invalid") from None
    started = time.monotonic_ns()
    try:
        with lm.Engine(
            str(model_path), backend=lm.Backend.CPU(thread_count=4),
            max_num_tokens=4096, enable_benchmark=True,
            enable_speculative_decoding=False,
        ) as engine:
            output["load_ms"] = (time.monotonic_ns() - started) / 1_000_000
            thinking = lm.ThinkingConfig(enable_thinking=False, thinking_token_budget=0)
            constrained = None
            if request["schema"] is not None:
                constrained = lm.ConstrainedDecodingConfig(
                    enable=True, provider=lm.LiteRtLmConstraintProviderType.LL_GUIDANCE,
                )
            with engine.create_conversation(
                automatic_tool_calling=False, thinking_config=thinking,
                sampler_config=lm.SamplerConfig(top_k=1, temperature=0.0, seed=1),
                max_output_tokens=request["max_tokens"],
                constrained_decoding_config=constrained,
                enable_speculative_decoding=False,
            ) as conversation:
                rendered = conversation.render_message_to_string(request["prompt"])
                if not rendered:
                    raise WorkerError("model_unsupported")
                # The native prefill can insert BOS. Reserve one even if the
                # rendered template already contains it; never truncate input.
                count = len(engine.tokenize(rendered)) + 1
                output["input_tokens"] = count
                if count + request["max_tokens"] > 4096:
                    raise WorkerError("context_overflow")
                output["thinking_disabled"] = True
                output["template_applied"] = True
                response_format = (
                    lm.ResponseFormat.json(request["schema"])
                    if request["schema"] is not None else None
                )
                began = time.monotonic_ns()
                response = conversation.send_message(
                    request["prompt"], max_output_tokens=request["max_tokens"],
                    thinking_config=thinking, response_format=response_format,
                )
                output["generation_ms"] = (time.monotonic_ns() - began) / 1_000_000
                stats = conversation.get_benchmark_info()
                output["input_tokens"] = stats.last_prefill_token_count
                output["output_tokens"] = stats.last_decode_token_count
                if (
                    type(output["input_tokens"]) is not int
                    or type(output["output_tokens"]) is not int
                    or output["input_tokens"] <= 0
                    or not 0 < output["output_tokens"] <= request["max_tokens"]
                    or output["input_tokens"] + output["output_tokens"] > 4096
                ):
                    raise WorkerError("context_overflow")
                output["text"] = final_text(response)
                output["schema_enforced"] = response_format is not None
                return output
    except WorkerError:
        raise
    except (RuntimeError, ValueError, OSError, TypeError):
        raise WorkerError("generation_failed") from None


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--model", required=True, type=Path)
    args = parser.parse_args(argv)
    try:
        request = parse_request(sys.stdin.buffer.read(MAX_REQUEST_BYTES + 1))
        with quiet_native():
            output = run(request, args.model)
    except WorkerError as error:
        output = result(str(error))
    except Exception:
        output = result("generation_failed")
    sys.stdout.write(json.dumps(output, ensure_ascii=True, separators=(",", ":")) + "\n")
    return 0 if output["status"] == "completed" else 2


if __name__ == "__main__":
    raise SystemExit(main())
