"""Read GGUF v3 metadata/tensor types without loading or publishing tensor bytes."""
import argparse
import collections
import hashlib
import json
from pathlib import Path
import struct


def inspect(path):
    size = path.stat().st_size
    with path.open("rb") as stream:
        def read(count):
            value = stream.read(count)
            if len(value) != count:
                raise ValueError("truncated_gguf")
            return value

        def number(fmt):
            return struct.unpack("<" + fmt, read(struct.calcsize(fmt)))[0]

        def string():
            count = number("Q")
            if count > 1048576:
                raise ValueError("metadata_limit")
            return read(count).decode("utf-8")

        def value(kind, retain=True):
            formats = {0:"B", 1:"b", 2:"H", 3:"h", 4:"I", 5:"i", 6:"f", 7:"?", 10:"Q", 11:"q", 12:"d"}
            if kind in formats:
                result = number(formats[kind])
            elif kind == 8:
                result = string()
            elif kind == 9:
                subtype, count = number("I"), number("Q")
                if count > 1000000 or subtype == 9:
                    raise ValueError("metadata_limit")
                if subtype in formats and not retain:
                    count_bytes = struct.calcsize(formats[subtype]) * count
                    if stream.tell() + count_bytes > size:
                        raise ValueError("truncated_gguf")
                    stream.seek(count_bytes, 1)
                else:
                    for _ in range(count):
                        value(subtype, False)
                result = {"element_type":subtype, "count":count}
            else:
                raise ValueError("unknown_metadata_type")
            return result if retain else None

        if read(4) != b"GGUF" or number("I") != 3:
            raise ValueError("unsupported_gguf")
        tensor_count, metadata_count = number("Q"), number("Q")
        if tensor_count > 100000 or metadata_count > 4096:
            raise ValueError("metadata_limit")
        metadata = {}
        keep = {"general.architecture", "general.file_type", "general.quantization_version", "qwen3.context_length",
                "qwen3.block_count", "qwen3.embedding_length", "tokenizer.ggml.model", "tokenizer.ggml.pre",
                "tokenizer.ggml.bos_token_id", "tokenizer.ggml.eos_token_id", "tokenizer.ggml.padding_token_id",
                "tokenizer.ggml.add_bos_token", "tokenizer.ggml.add_eos_token", "tokenizer.ggml.tokens", "tokenizer.chat_template"}
        for _ in range(metadata_count):
            key, kind = string(), number("I")
            result = value(kind, key in keep)
            if key in keep:
                metadata[key] = result
        template = metadata.pop("tokenizer.chat_template")
        metadata["chat_template_sha256"] = hashlib.sha256(template.encode("utf-8")).hexdigest()
        metadata["chat_template_utf8_bytes"] = len(template.encode("utf-8"))
        metadata["template_mentions_enable_thinking"] = "enable_thinking" in template
        counts = collections.Counter()
        for _ in range(tensor_count):
            string()
            dimensions = number("I")
            if not 1 <= dimensions <= 4:
                raise ValueError("unsupported_tensor")
            for _ in range(dimensions):
                number("Q")
            counts[number("I")] += 1
            number("Q")
        return {"gguf_version":3, "artifact_bytes":size, "metadata_count":metadata_count,
                "tensor_count":tensor_count, "tensor_type_counts":dict(sorted(counts.items())), "metadata":metadata}


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("model", type=Path)
    print(json.dumps(inspect(parser.parse_args().model), indent=2))
