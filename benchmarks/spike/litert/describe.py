"""Print allowlisted bundle capabilities without loading an inference engine."""

import argparse
import importlib.metadata
import json
from pathlib import Path

from run import VERSION, quiet_native


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--model", required=True, type=Path)
    args = parser.parse_args()
    if not args.model.is_file():
        print('{"status":"error","error":"model_missing"}')
        return 2
    try:
        with quiet_native():
            if importlib.metadata.version("litert-lm-api") != VERSION:
                raise ValueError()
            import litert_lm as lm
            lm.set_min_log_severity(lm.LogSeverity.ERROR)
            with lm.ModelInfo(args.model) as info:
                data = {
                    "status": "completed", "runtime_version": VERSION,
                    "model_type": info.model_type.name,
                    "max_context_tokens": info.max_context_tokens,
                    "dynamic_context": info.is_dynamic_context,
                    "minimum_runtime": info.min_runtime_version,
                    "input_modalities": {
                        name: bool(getattr(info.input_modalities, name))
                        for name in ("text", "vision", "audio", "video")
                    },
                    "text_backends": info.supported_backends_for_modality(lm.LiteRtLmModality.TEXT),
                    "thinking_supported": info.llm.supports_thinking() if info.llm else None,
                    "function_calling_supported": info.llm.supports_function_calling() if info.llm else None,
                    "speculative_supported": info.llm.has_speculative_decoding_support() if info.llm else None,
                }
        print(json.dumps(data, ensure_ascii=True, separators=(",", ":")))
        return 0
    except Exception:
        print('{"status":"error","error":"model_invalid"}')
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
