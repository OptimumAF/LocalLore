"""Bounded cooperative API cancellation smoke; caller supplies a 60 s watchdog.

Read the worker's original synthetic request from stdin. Cancel the official
stream after its first nonempty final-visible content event, drain it, close both
native owners, then reload for one short call. Never emit generation text.
"""

import argparse
import importlib.metadata
import json
from pathlib import Path
import sys
import time

from run import MAX_REQUEST_BYTES, VERSION, WorkerError, parse_request, quiet_native, run


def has_visible_text(message):
    if not isinstance(message, dict):
        return False
    content = message.get("content", [])
    if isinstance(content, str):
        return bool(content)
    return isinstance(content, list) and any(
        isinstance(item, dict) and item.get("type") == "text"
        and item.get("channel") in (None, "final")
        and isinstance(item.get("text"), str) and bool(item["text"])
        for item in content
    )


def elapsed(started):
    return round((time.monotonic_ns() - started) / 1_000_000, 3)


def smoke(request, model):
    import litert_lm as lm
    lm.set_min_log_severity(lm.LogSeverity.ERROR)
    report = {
        "version": 1, "status": "error", "error": None,
        "scope": "windows_x64_cpu_cooperative_api_smoke_not_phone_benchmark",
        "first_visible_event_observed": False, "cancel_called": False,
        "cancel_returned": False, "cancel_call_ms": None,
        "stream_ended": False, "stream_drain_ms": None,
        "events_after_cancel": 0, "native_owners_closed": False,
        "reload_status": None, "reload_error": None,
        "reload_input_tokens": None, "reload_output_tokens": None,
        "raw_text_persisted": False,
    }
    with lm.Engine(
        str(model), backend=lm.Backend.CPU(thread_count=4), max_num_tokens=4096,
        enable_benchmark=True, enable_speculative_decoding=False,
    ) as engine:
        thinking = lm.ThinkingConfig(enable_thinking=False, thinking_token_budget=0)
        constraint = None
        if request["schema"] is not None:
            constraint = lm.ConstrainedDecodingConfig(
                enable=True, provider=lm.LiteRtLmConstraintProviderType.LL_GUIDANCE,
            )
        with engine.create_conversation(
            automatic_tool_calling=False, thinking_config=thinking,
            sampler_config=lm.SamplerConfig(top_k=1, temperature=0.0, seed=1),
            max_output_tokens=request["max_tokens"],
            constrained_decoding_config=constraint,
            enable_speculative_decoding=False,
        ) as conversation:
            rendered = conversation.render_message_to_string(request["prompt"])
            if not rendered or len(engine.tokenize(rendered)) + 1 + request["max_tokens"] > 4096:
                raise WorkerError("context_overflow")
            response_format = lm.ResponseFormat.json(request["schema"]) if request["schema"] is not None else None
            cancelled_at = None
            for event in conversation.send_message_async(
                request["prompt"], max_output_tokens=request["max_tokens"],
                thinking_config=thinking, response_format=response_format,
            ):
                if cancelled_at is not None:
                    report["events_after_cancel"] += 1
                elif has_visible_text(event):
                    report["first_visible_event_observed"] = True
                    report["cancel_called"] = True
                    cancelled_at = time.monotonic_ns()
                    conversation.cancel_process()
                    report["cancel_call_ms"] = elapsed(cancelled_at)
                    report["cancel_returned"] = True
            report["stream_ended"] = True
            if cancelled_at is not None:
                report["stream_drain_ms"] = elapsed(cancelled_at)
    report["native_owners_closed"] = True
    if not report["cancel_called"]:
        report["error"] = "no_visible_event"
        return report
    reload_request = dict(
        version=1, role="narrator", prompt="Reply with only the word Lantern.",
        max_tokens=8, context_tokens=4096, threads=4, schema=None,
    )
    try:
        reloaded = run(reload_request, model)
        report["reload_status"] = reloaded["status"]
        report["reload_input_tokens"] = reloaded["input_tokens"]
        report["reload_output_tokens"] = reloaded["output_tokens"]
        report["status"] = "completed"
    except WorkerError as error:
        report["reload_status"] = "error"
        report["reload_error"] = str(error)
        report["error"] = "reload_failed"
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--model", required=True, type=Path)
    args = parser.parse_args()
    try:
        request = parse_request(sys.stdin.buffer.read(MAX_REQUEST_BYTES + 1))
        if not args.model.is_file():
            raise WorkerError("model_missing")
        with quiet_native():
            if importlib.metadata.version("litert-lm-api") != VERSION:
                raise WorkerError("runtime_unavailable")
            report = smoke(request, args.model)
    except WorkerError as error:
        report = {"version": 1, "status": "error", "error": str(error), "raw_text_persisted": False}
    except Exception:
        report = {"version": 1, "status": "error", "error": "native_api_failure", "raw_text_persisted": False}
    print(json.dumps(report, ensure_ascii=True, separators=(",", ":")))
    return 0 if report["status"] == "completed" else 2


if __name__ == "__main__":
    raise SystemExit(main())
