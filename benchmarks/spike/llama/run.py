"""One cold, bounded, local llama.cpp call. No imports beyond Python stdlib."""
import argparse
import hashlib
import json
import math
import os
from pathlib import Path
import subprocess
import sys
import threading
import time

MODEL_SHA256 = "9465e63a22add5354d9bb4b99e90117043c7124007664907259bd16d043bb031"
MODEL_BYTES = 639446688
MAX_REQUEST = 32768
MAX_CAPTURE = 65536
MAX_TEXT = 16384
REQUEST_KEYS = {"version", "role", "prompt", "max_tokens", "context_tokens", "threads", "schema"}
RESPONSE_KEYS = {"version", "status", "text", "error", "load_ms", "generation_ms", "output_tokens", "input_tokens", "schema_enforced", "thinking_disabled", "template_applied"}
ERRORS = {"invalid_request", "model_load_failed", "unsupported_template", "context_limit", "context_failed", "sampling_failed", "decode_failed", "output_limit", "unexpected_output", "runtime_failed"}


def failure(category):
    return dict(version=1, status="error", text="", error=category, load_ms=None,
                generation_ms=None, output_tokens=None, input_tokens=None,
                schema_enforced=False, thinking_disabled=False, template_applied=False)


def unique_object(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError("duplicate_key")
        result[key] = value
    return result


def parse_request(raw):
    if len(raw) > MAX_REQUEST:
        raise ValueError("invalid_request")
    req = json.loads(raw.decode("utf-8"), object_pairs_hook=unique_object,
                     parse_constant=lambda _: (_ for _ in ()).throw(ValueError("nonfinite")))
    if not isinstance(req, dict) or set(req) != REQUEST_KEYS:
        raise ValueError("invalid_request")
    if any(type(req[key]) is not int for key in ("version", "max_tokens", "context_tokens", "threads")):
        raise ValueError("invalid_request")
    if (req["version"] != 1 or req["role"] not in ("director", "narrator") or
            type(req["prompt"]) is not str or not req["prompt"] or
            "\0" in req["prompt"] or not 1 <= req["max_tokens"] <= 350 or
            req["context_tokens"] != 4096 or req["threads"] != 4 or
            (req["schema"] is not None and type(req["schema"]) is not dict)):
        raise ValueError("invalid_request")
    return req


def verify_model(path):
    if not path.is_file() or path.stat().st_size != MODEL_BYTES:
        return False
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1048576), b""):
            digest.update(block)
    return digest.hexdigest() == MODEL_SHA256


def capture(command, request, timeout=55):
    """Bound both pipes while reading concurrently; this helper cannot spawn children."""
    env = {key: value for key, value in os.environ.items()
           if not key.upper().startswith(("LLAMA_", "GGML_", "HF_", "HUGGINGFACE_"))}
    proc = subprocess.Popen(command, stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                            stderr=subprocess.PIPE, env=env, shell=False)
    chunks = [bytearray(), bytearray()]
    overflow = threading.Event()

    def drain(stream, index):
        try:
            while True:
                data = stream.read(4096)
                if not data:
                    return
                remaining = MAX_CAPTURE - len(chunks[index])
                chunks[index].extend(data[:remaining])
                if len(data) > remaining:
                    overflow.set()
                    return
        finally:
            stream.close()

    readers = [threading.Thread(target=drain, args=(stream, index), daemon=True)
               for index, stream in enumerate((proc.stdout, proc.stderr))]
    for reader in readers:
        reader.start()
    def send():
        try:
            proc.stdin.write(request)
        except (BrokenPipeError, OSError):
            pass
        finally:
            proc.stdin.close()
    writer = threading.Thread(target=send, daemon=True)
    writer.start()
    category = None
    try:
        deadline = time.monotonic() + timeout
        while proc.poll() is None:
            if overflow.is_set():
                category = "output_limit"
                break
            if time.monotonic() >= deadline:
                category = "timeout"
                break
            time.sleep(0.01)
    finally:
        if proc.poll() is None:
            proc.kill()
        proc.wait()
        writer.join()
        for reader in readers:
            reader.join()
    if overflow.is_set():
        category = "output_limit"
    return proc.returncode, bytes(chunks[0]), category


def validate_response(raw):
    data = json.loads(raw.decode("utf-8"), object_pairs_hook=unique_object)
    if type(data) is not dict or set(data) != RESPONSE_KEYS or type(data["version"]) is not int or data["version"] != 1:
        raise ValueError("invalid_response")
    if data["status"] not in ("completed", "error") or type(data["text"]) is not str or len(data["text"].encode("utf-8")) > MAX_TEXT:
        raise ValueError("invalid_response")
    for key in ("schema_enforced", "thinking_disabled", "template_applied"):
        if type(data[key]) is not bool:
            raise ValueError("invalid_response")
    for key in ("load_ms", "generation_ms"):
        value = data[key]
        if value is not None and (type(value) not in (int, float) or not math.isfinite(value) or value < 0):
            raise ValueError("invalid_response")
    for key, maximum in (("input_tokens", 4096), ("output_tokens", 350)):
        value = data[key]
        if value is not None and (type(value) is not int or not 0 <= value <= maximum):
            raise ValueError("invalid_response")
    if data["status"] == "completed":
        if (data["error"] is not None or not data["thinking_disabled"] or not data["template_applied"] or
                any(data[key] is None for key in ("load_ms", "generation_ms", "input_tokens", "output_tokens")) or
                "<think>" in data["text"] or "</think>" in data["text"]):
            raise ValueError("invalid_response")
    elif data["error"] not in ERRORS or data["text"]:
        raise ValueError("invalid_response")
    return data


class QuietParser(argparse.ArgumentParser):
    def error(self, message):
        raise ValueError("invalid_arguments")


def main():
    result = failure("invalid_request")
    try:
        parser = QuietParser()
        parser.add_argument("--model", required=True)
        parser.add_argument("--executable", required=True)
        args = parser.parse_args()
        req = parse_request(sys.stdin.buffer.read(MAX_REQUEST + 1))
        model, executable = Path(args.model).resolve(), Path(args.executable).resolve()
        if not verify_model(model):
            result = failure("model_invalid")
        elif not executable.is_file():
            result = failure("executable_missing")
        else:
            result = failure("runtime_failed")
            code, raw, error = capture([str(executable), "--model", str(model)], json.dumps(req, ensure_ascii=False).encode("utf-8"))
            result = failure(error) if error else validate_response(raw)
            if not error and ((code == 0) != (result["status"] == "completed")):
                result = failure("runtime_failed")
    except Exception:
        # Never print exception messages, paths, prompts, native stderr, or reasoning.
        pass
    sys.stdout.write(json.dumps(result, ensure_ascii=False, allow_nan=False) + "\n")
    return 0 if result["status"] == "completed" else 1


if __name__ == "__main__":
    sys.exit(main())
