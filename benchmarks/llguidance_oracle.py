"""Bounded host-only grammar oracle; native code loads only on explicit CLI run.

The backend seam permits stdlib tests and is not a CLI backend selector. Reports
contain indexes, enums, counts and hashes only; corpus/schema/sample bytes stay
private to the caller. This does not qualify a model tokenizer or an SDK failure.
Copyright 2026 LocalLore contributors. SPDX-License-Identifier: Apache-2.0
"""
import argparse
import hashlib
import importlib
import importlib.metadata
import json
from pathlib import Path
import re
import sys

SCOPE = "locallore_llguidance_oracle_v1"
VERSION = "1.3.0"
MAX_INPUT = 1024 * 1024
MAX_CASES = 16
MAX_TEXT = 16384
MAX_SAMPLES = 256
MAX_REPORT = 131072
SAFE_STOPS = frozenset(("NotStopped", "NoExtension", "NoExtensionBias", "EndOfSentence"))
REASONS = frozenset(("arguments", "input_io", "corpus_invalid", "module_root", "dependency_state", "dependency_version",
    "dependency_path", "byte_tokenizer", "backend_runtime", "backend_state", "backend_mask", "control_compile",
    "control_acceptance", "unsupported_control", "case_compile", "report_limit", "unexpected"))
BASIC_SCHEMA = '{"type":"object","properties":{"x":{"type":"integer"}},"required":["x"],"additionalProperties":false}'
UNSUPPORTED_SCHEMA = '{"type":"array","items":{"type":"string"},"uniqueItems":true}'


class OracleFailure(Exception):
    def __init__(self, reason):
        self.reason = reason if reason in REASONS else "unexpected"
        super().__init__(self.reason)


def require(condition, reason):
    if not condition: raise OracleFailure(reason)


def _pairs(pairs):
    value = {}
    for key, item in pairs:
        require(key not in value, "corpus_invalid")
        value[key] = item
    return value


def _json(raw):
    def nonfinite(_): raise OracleFailure("corpus_invalid")
    try: return json.loads(raw, object_pairs_hook=_pairs, parse_constant=nonfinite)
    except Exception: raise OracleFailure("corpus_invalid") from None


def _text(value, limit):
    require(type(value) is str, "corpus_invalid")
    try: data = value.encode("utf-8", "strict")
    except Exception: raise OracleFailure("corpus_invalid") from None
    require(0 < len(data) <= limit, "corpus_invalid")
    return data


def _id(value):
    require(type(value) is str and re.fullmatch(r"[a-z][a-z0-9-]{0,47}", value) is not None, "corpus_invalid")


def validate_corpus(rawbytes):
    require(type(rawbytes) is bytes and 0 < len(rawbytes) <= MAX_INPUT, "corpus_invalid")
    try: text = rawbytes.decode("utf-8", "strict")
    except Exception: raise OracleFailure("corpus_invalid") from None
    corpus = _json(text)
    require(type(corpus) is dict and set(corpus) == {"version", "scope", "cases", "refusals"}, "corpus_invalid")
    require(type(corpus["version"]) is int and corpus["version"] == 1 and corpus["scope"] == SCOPE, "corpus_invalid")
    cases, refusals = corpus["cases"], corpus["refusals"]
    require(type(cases) is list and 1 <= len(cases) <= MAX_CASES, "corpus_invalid")
    require(type(refusals) is list and len(refusals) <= MAX_CASES, "corpus_invalid")
    case_ids, sample_count = set(), 0
    for case in cases:
        require(type(case) is dict and set(case) == {"id", "schema_json", "positives", "negatives"}, "corpus_invalid")
        _id(case["id"]); require(case["id"] not in case_ids, "corpus_invalid"); case_ids.add(case["id"])
        schema = _text(case["schema_json"], MAX_TEXT)
        require(type(_json(schema.decode("utf-8"))) is dict, "corpus_invalid")
        sample_ids = set()
        for category in ("positives", "negatives"):
            samples = case[category]
            require(type(samples) is list and 1 <= len(samples) <= MAX_SAMPLES, "corpus_invalid")
            sample_count += len(samples); require(sample_count <= MAX_SAMPLES, "corpus_invalid")
            for sample in samples:
                require(type(sample) is dict and set(sample) == {"id", "json"}, "corpus_invalid")
                _id(sample["id"]); require(sample["id"] not in sample_ids, "corpus_invalid"); sample_ids.add(sample["id"])
                # Preserve exact candidate bytes, including deliberately malformed negatives.
                _text(sample["json"], MAX_TEXT)
    refusal_ids = set()
    for refusal in refusals:
        require(type(refusal) is dict and set(refusal) == {"id", "error", "provider_calls", "canon_unchanged"}, "corpus_invalid")
        _id(refusal["id"]); require(refusal["id"] not in refusal_ids, "corpus_invalid"); refusal_ids.add(refusal["id"])
        require(refusal["error"] in ("ClarificationRequired", "TooLarge"), "corpus_invalid")
        require(type(refusal["provider_calls"]) is int and refusal["provider_calls"] == 0 and refusal["canon_unchanged"] is True, "corpus_invalid")
    return corpus


def _call(function, *args):
    try: return function(*args)
    except OracleFailure: raise
    except BaseException: raise OracleFailure("backend_runtime") from None


def _state(matcher):
    error = _call(matcher.is_error)
    reason = _call(matcher.stop_reason)
    require(type(error) is bool and not error and type(reason) is str and reason in SAFE_STOPS, "backend_state")


def _mask(matcher, vocab_size):
    _state(matcher)
    mask = _call(matcher.compute_bitmask)
    _state(matcher)
    require(type(mask) is bytes and len(mask) == ((vocab_size+31)//32)*4, "backend_mask")
    return mask


def _allowed(mask, token):
    return bool(mask[token//8] & (1 << (token%8)))


def evaluate_sample(backend, grammar, data):
    require(type(data) is bytes and 0 < len(data) <= MAX_TEXT and 255 not in data, "corpus_invalid")
    matcher = _call(backend.matcher, grammar)
    _state(matcher)
    for offset, token in enumerate(data):
        mask = _mask(matcher, backend.vocab_size)
        if not _allowed(mask, token):
            return {"accepted": False, "outcome": "BYTE_MASK", "checked_bytes": offset}
        require(_call(matcher.consume_token, token) is True, "backend_state")
        _state(matcher)
    mask = _mask(matcher, backend.vocab_size)
    accepting = _call(matcher.is_accepting)
    _state(matcher)
    require(type(accepting) is bool, "backend_state")
    eos = _allowed(mask, backend.eos_token)
    require(accepting == eos, "backend_state")
    if not accepting: return {"accepted": False, "outcome": "INCOMPLETE", "checked_bytes": len(data)}
    require(_call(matcher.consume_token, backend.eos_token) is True, "backend_state")
    _state(matcher)
    require(_call(matcher.is_stopped) is True, "backend_state")
    return {"accepted": True, "outcome": "COMPLETE", "checked_bytes": len(data)}


def _controls(backend):
    grammar = _call(backend.compile, BASIC_SCHEMA)
    require(grammar is not None, "control_compile")
    valid = evaluate_sample(backend, grammar, b'{"x":1}')
    illegal = evaluate_sample(backend, grammar, b'{"x":"wrong"}')
    prefix = evaluate_sample(backend, grammar, b'{"x":')
    require(valid["accepted"] and illegal["outcome"] == "BYTE_MASK" and prefix["outcome"] == "INCOMPLETE", "control_acceptance")
    require(_call(backend.compile, UNSUPPORTED_SCHEMA) is None, "unsupported_control")
    return {"basic_compile": True, "valid_complete": True, "illegal_rejected": True, "incomplete_rejected": True, "unsupported_refused": True}


def run_oracle(rawbytes, backend):
    corpus = validate_corpus(rawbytes)
    require(type(backend.native) is bool and type(backend.vocab_size) is int and backend.vocab_size == 262 and
        type(backend.eos_token) is int and backend.eos_token == 261, "byte_tokenizer")
    report = {"version": 1, "scope": SCOPE, "status": "passed", "native": backend.native,
        "corpus_sha256": hashlib.sha256(rawbytes).hexdigest(), "controls": _controls(backend), "cases": [], "sample_count": 0,
        "refusals": len(corpus["refusals"])}
    for case_index, case in enumerate(corpus["cases"]):
        grammar = _call(backend.compile, case["schema_json"])
        require(grammar is not None, "case_compile")
        row = {"index": case_index, "schema_sha256": hashlib.sha256(case["schema_json"].encode("utf-8")).hexdigest(), "positives": [], "negatives": []}
        for category in ("positives", "negatives"):
            for index, sample in enumerate(case[category]):
                data = sample["json"].encode("utf-8")
                result = evaluate_sample(backend, grammar, data)
                if result["accepted"] != (category == "positives"): report["status"] = "mismatch"
                row[category].append({"index": index, "sha256": hashlib.sha256(data).hexdigest(), "bytes": len(data), **result})
                report["sample_count"] += 1
        report["cases"].append(row)
    require(len(json.dumps(report, separators=(",", ":")).encode("ascii")) <= MAX_REPORT, "report_limit")
    return report


class NativeBackend:
    """Explicitly admitted wheel only; no HF/tokenizer files or interpreter FF API.

    Official v1.3.0 sources: python_ext/src/py.rs37–59 reserves 'byte';
    toktrie/src/tokenv.rs145–167 defines byte IDs0..255/EOS261/vocab262.
    python_ext/src/llmatcher.rs277–350 requires validate_grammar beyond wrapper;
    No public FF helpers are called. Default inference flags do not disable
    every internal forced-byte optimization (tokenparser.rs can_force_bytes).
    https://github.com/guidance-ai/llguidance/tree/v1.3.0
    """
    native = True

    def __init__(self, module_root):
        root = Path(module_root)
        require(root.is_absolute() and root.is_dir() and not root.is_symlink() and root.resolve() == root, "module_root")
        require(not any(name == "llguidance" or name.startswith("llguidance.") for name in sys.modules), "dependency_state")
        sys.path.insert(0, str(root))
        try:
            distribution = importlib.metadata.distribution("llguidance")
            require(importlib.metadata.version("llguidance") == VERSION and distribution.version == VERSION, "dependency_version")
            require(Path(distribution.locate_file("")).resolve() == root, "dependency_path")
            module = importlib.import_module("llguidance")
            require(Path(module.__file__).resolve() == root / "llguidance" / "__init__.py", "dependency_path")
            extension = sys.modules.get("llguidance._lib")
            require(extension is not None and Path(extension.__file__).resolve().parent == root / "llguidance", "dependency_path")
            self.tokenizer = module.LLTokenizer("byte", slices=[])
            self.vocab_size, self.eos_token = self.tokenizer.vocab_size, self.tokenizer.eos_token
            require(type(self.vocab_size) is int and self.vocab_size == 262 and type(self.eos_token) is int and self.eos_token == 261, "byte_tokenizer")
            # TokTrie reserves 0xff as its special-token marker. Valid UTF-8
            # corpus text cannot contain it; inspect only ordinary byte IDs.
            require(all(self.tokenizer.decode_bytes([byte]) == bytes([byte]) for byte in range(255)), "byte_tokenizer")
            require(self.tokenizer.is_special_token(255) is True and self.tokenizer.is_special_token(261) is True, "byte_tokenizer")
            self.module = module
            self.limits = module.LLParserLimits(verbose_errors=False)
        except OracleFailure: raise
        except BaseException: raise OracleFailure("dependency_state") from None

    def compile(self, schema):
        grammar = self.module.LLMatcher.grammar_from_json_schema(schema)
        require(type(grammar) is str, "backend_state")
        error = self.module.LLMatcher.validate_grammar(grammar, self.tokenizer, limits=self.limits)
        require(type(error) is str, "backend_state")
        return None if error else grammar

    def matcher(self, grammar):
        return self.module.LLMatcher(self.tokenizer, grammar, log_level=0, limits=self.limits)


class _Arguments(argparse.ArgumentParser):
    def error(self, message): raise OracleFailure("arguments")


def main(argv=None, *, backend_factory=NativeBackend):
    try:
        parser = _Arguments(add_help=False, allow_abbrev=False)
        parser.add_argument("--corpus", type=Path, required=True)
        parser.add_argument("--module-root", type=Path, required=True)
        args = parser.parse_args(argv)
        try:
            with args.corpus.open("rb") as stream: rawbytes = stream.read(MAX_INPUT+1)
        except BaseException: raise OracleFailure("input_io") from None
        validate_corpus(rawbytes)  # Before any native import or installed-metadata lookup.
        backend = backend_factory(args.module_root)
        report = run_oracle(rawbytes, backend)
        code = 0 if report["status"] == "passed" else 1
    except OracleFailure as failure:
        report = {"version": 1, "scope": SCOPE, "status": "failed", "reason": failure.reason}; code = 2
    except BaseException:
        report = {"version": 1, "scope": SCOPE, "status": "failed", "reason": "unexpected"}; code = 2
    print(json.dumps(report, sort_keys=True, separators=(",", ":")))
    return code


if __name__ == "__main__": raise SystemExit(main())
