"""Model-free hostile framing checks against the actual compiled application worker."""
import json
import subprocess
import sys


def main(executable):
    cases = [
        (b'{"version":1,"id":1,"op":"status"}\n', "completed"),
        (b'{"version":1,"id":1,"id":2,"op":"status"}\n', "error"),
        (b'{"version":1,"id":1,"op":"status","extra":true}\n', "error"),
        (b'{"version":2,"id":1,"op":"status"}\n', "error"),
        (b'{"version":1,"id":true,"op":"status"}\n', "error"),
        (b'{"version":1,"id":1,"op":"shell"}\n', "error"),
        (b'\xff\n', "error"),
        (b'{"version":1,"id":1,"op":"load"}\n', "error"),
        (b'{"version":1,"id":1,"op":"generate","generation":{}}\n', "error"),
    ]
    for frame, expected in cases:
        result = subprocess.run([executable, "--model", "missing-synthetic.gguf"], input=frame, capture_output=True, timeout=3, check=True)
        assert len(result.stdout) <= 32768 and len(result.stderr) <= 65536
        reply = json.loads(result.stdout)
        assert reply["status"] == expected and not reply["text"]
        assert reply["metrics"]["model_loads"] == 0
    for frame in [b'x' * 32769, b'{"version":1']:
        result = subprocess.run([executable, "--model", "missing-synthetic.gguf"], input=frame, capture_output=True, timeout=3, check=True)
        assert not result.stdout
    print(json.dumps({"status": "passed", "actual_native_model_free_cases": len(cases) + 2, "model_loaded": False}))


if __name__ == "__main__":
    main(sys.argv[1])
