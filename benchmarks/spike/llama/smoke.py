"""Explicit real-model host compatibility checks; no performance/quality verdict."""
import argparse
import hashlib
import json
from pathlib import Path
import subprocess
import tempfile
import time

import run as worker


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--model", required=True, type=Path)
    parser.add_argument("--executable", required=True, type=Path)
    args = parser.parse_args()
    if not worker.verify_model(args.model):
        raise SystemExit("Exact reviewed model bytes required")
    executable = str(args.executable.resolve())
    model = str(args.model.resolve())
    base = dict(version=1, role="director", prompt="Return an object with a single boolean property ok set true.",
                max_tokens=40, context_tokens=4096, threads=4,
                schema={"type":"object", "properties":{"ok":{"type":"boolean"}}, "required":["ok"], "additionalProperties":False})
    rows = []
    with tempfile.TemporaryDirectory() as directory:
        missing = str(Path(directory) / "absent.gguf")
        corrupt = Path(directory) / "corrupt.gguf"
        corrupt.write_bytes(b"GGUF" + bytes(28))
        narrator = dict(base, role="narrator", schema=None, max_tokens=80,
                        prompt="Write one short sentence: Mira thanks the player for the accepted gift of one healing potion. Add no events.")
        cases = [("schema", model, base, None), ("narrator", model, narrator, None),
                 ("reload_schema", model, base, None), ("missing", missing, base, "model_load_failed"),
                 ("corrupt", str(corrupt), base, "model_load_failed"),
                 ("context_limit", model, dict(base, prompt="Lantern Quay. " * 2000), "context_limit")]
        for name, path, request, expected_error in cases:
            code, raw, transport_error = worker.capture([executable, "--model", path], json.dumps(request).encode())
            result = worker.validate_response(raw)
            assert transport_error is None and result["error"] == expected_error
            assert (code == 0) == (expected_error is None)
            if name in ("schema", "reload_schema"):
                assert result["schema_enforced"] and json.loads(result["text"]) == {"ok":True}
            if name == "narrator":
                assert result["text"] and not result["schema_enforced"]
            rows.append(dict(case=name, exit_code=code, passed=True,
                             visible_text_bytes=len(result.pop("text").encode()), response=result))
        # Prove process termination/reaping during real native loading/generation.
        process = subprocess.Popen([executable, "--model", model], stdin=subprocess.PIPE,
                                   stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        process.stdin.write(json.dumps(dict(base, max_tokens=350)).encode())
        process.stdin.close()
        time.sleep(0.02)
        assert process.poll() is None
        process.kill()
        process.wait(timeout=5)
        stdout, stderr = process.stdout.read(), process.stderr.read()
        process.stdout.close()
        process.stderr.close()
        assert process.returncode != 0 and not stdout and not stderr
        rows.append(dict(case="terminate_real_native_process", passed=True, exit_code=process.returncode,
                         stdout_bytes=len(stdout), stderr_bytes=len(stderr)))
    print(json.dumps(dict(kind="host_compatibility_smoke", runtime_commit="620d2225cc436ab0b001e3200e590e3b286ef9ab",
                          model_sha256=worker.MODEL_SHA256,
                          helper_sha256=hashlib.sha256(args.executable.read_bytes()).hexdigest(), checks=rows), indent=2))


if __name__ == "__main__":
    main()
