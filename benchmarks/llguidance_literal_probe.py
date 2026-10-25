"""Fixed original-literal compiler/matcher investigation, no model or tokenizer file.

Copyright 2026 LocalLore contributors. SPDX-License-Identifier: Apache-2.0
"""
import hashlib
import importlib.util
import json
from pathlib import Path
import sys

_spec = importlib.util.spec_from_file_location("locallore_literal_checker", Path(__file__).with_name("llguidance_oracle.py"))
oracle = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(oracle)

ORIGINAL = 'Hello "Mira" \\ \u96ea.\nIs the tideglass here?'
MAX_EVALUATIONS = 128
SCOPE = "locallore_llguidance_literal_probe_v1"


def encoded(value):
    return json.dumps(value, ensure_ascii=False, separators=(",", ":"))


def schema(text):
    return encoded({"const": text, "type": "string"})


def minimize(text, rejects, budget=MAX_EVALUATIONS):
    """Deterministic deletion reduction; retain source indexes, never hide a budget exit."""
    if type(text) is not str or not 0 < len(text) <= 128 or type(budget) is not int or not 1 <= budget <= MAX_EVALUATIONS:
        raise oracle.OracleFailure("corpus_invalid")
    indexes, calls, granularity = list(range(len(text))), 0, 2
    cache = {}

    def test(candidate):
        nonlocal calls
        key = tuple(candidate)
        if key in cache:
            return cache[key]
        if calls >= budget:
            return None
        value = rejects("".join(text[i] for i in candidate))
        if type(value) is not bool:
            raise oracle.OracleFailure("backend_state")
        calls += 1
        cache[key] = value
        return value

    if test(indexes) is not True:
        return {"status": "not_reproduced", "indexes": indexes, "evaluations": calls}
    while indexes:
        size = max(1, (len(indexes) + granularity - 1) // granularity)
        changed = False
        for start in range(0, len(indexes), size):
            candidate = indexes[:start] + indexes[start + size:]
            rejected = test(candidate)
            if rejected is None:
                return {"status": "budget_exhausted", "indexes": indexes, "evaluations": calls}
            if rejected:
                indexes, granularity, changed = candidate, max(2, granularity - 1), True
                break
        if changed:
            continue
        if size == 1:
            return {"status": "deletion_minimal", "indexes": indexes, "evaluations": calls}
        granularity = min(len(indexes), granularity * 2)
    return {"status": "deletion_minimal", "indexes": indexes, "evaluations": calls}


def compare(backend, grammar, data):
    """Fresh native matchers; raw validation/direct acceptance never qualifies masking."""
    call = oracle._call
    masked = oracle.evaluate_sample(backend, grammar, data)
    validation = call(backend.matcher, grammar)
    oracle._state(validation)
    validated = call(validation.validate_tokens, list(data) + [backend.eos_token])
    oracle._state(validation)
    oracle.require(type(validated) is int and 0 <= validated <= len(data) + 1, "backend_state")
    direct = call(backend.matcher, grammar)
    oracle._state(direct)
    consumed = call(direct.consume_tokens, list(data))
    oracle.require(type(consumed) is bool, "backend_state")
    direct_error = call(direct.is_error)
    oracle.require(type(direct_error) is bool, "backend_state")
    oracle.require(consumed != direct_error, "backend_state")
    accepted = False
    if consumed and not direct_error:
        oracle._state(direct)
        accepting = call(direct.is_accepting)
        oracle.require(type(accepting) is bool, "backend_state")
        if accepting:
            eos = call(direct.consume_token, backend.eos_token)
            oracle._state(direct)
            accepted = eos is True and call(direct.is_stopped) is True
    elif consumed:
        raise oracle.OracleFailure("backend_state")
    result = {"mask": masked, "validated_tokens": validated, "tokens_with_eos": len(data) + 1,
              "direct_consumed": consumed, "direct_error": direct_error, "direct_complete": accepted}
    if masked["outcome"] == "BYTE_MASK":
        prefix = masked["checked_bytes"]
        witness = call(backend.matcher, grammar)
        oracle._state(witness)
        oracle.require(call(witness.consume_tokens, list(data[:prefix])) is True, "backend_state")
        oracle._state(witness)
        next_valid = call(witness.validate_tokens, [data[prefix]])
        oracle._state(witness)
        oracle.require(type(next_valid) is int and 0 <= next_valid <= 1, "backend_state")
        mask = oracle._mask(witness, backend.vocab_size)
        result["next_byte_validation"] = next_valid
        result["next_byte_mask"] = oracle._allowed(mask, data[prefix])
        result["mask_allowed_count"] = sum(byte.bit_count() if hasattr(byte, "bit_count") else bin(byte).count("1") for byte in mask)
        result["mask_allowed_tokens"] = [token for token in range(backend.vocab_size) if oracle._allowed(mask, token)]
    return result


def literal_regex(text):
    # Rust regex metacharacters; the JSON string's control chars are escaped already.
    return "".join("\\" + c if c in "\\.+*?()|[]{}^$" else c for c in text)


def run_probe(backend):
    oracle.require(backend.native is True, "dependency_state")
    controls = oracle._controls(backend)
    def rejects(text):
        grammar = oracle._call(backend.compile, schema(text))
        oracle.require(grammar is not None, "case_compile")
        return not oracle.evaluate_sample(backend, grammar, encoded(text).encode("utf-8"))["accepted"]
    reduction = minimize(ORIGINAL, rejects)
    reduced = "".join(ORIGINAL[i] for i in reduction["indexes"])
    cases = []
    for index, text in enumerate((ORIGINAL, reduced)):
        raw_schema, data = schema(text), encoded(text).encode("utf-8")
        prefix_len = (len(text.encode("utf-8")) - 1) % 31 + 1
        try:
            prefix = text.encode("utf-8")[:prefix_len].decode("utf-8", "strict")
        except UnicodeError:
            raise oracle.OracleFailure("corpus_invalid") from None
        truncated = encoded(prefix).encode("utf-8")
        constructors = (
            ("json_default", lambda: backend.compile(raw_schema)),
            ("lark_default", lambda: backend.module.LLMatcher.grammar_from_lark('%llguidance {}\nstart: %json ' + raw_schema)),
            ("lark_no_forcing", lambda: backend.module.LLMatcher.grammar_from_lark('%llguidance {"no_forcing":true}\nstart: %json ' + raw_schema)),
            ("regex_exact", lambda: backend.module.LLMatcher.grammar_from_regex(literal_regex(data.decode("utf-8")))),
        )
        rows = []
        for label, constructor in constructors:
            grammar = oracle._call(constructor)
            oracle.require(type(grammar) is str, "case_compile")
            error = oracle._call(lambda: backend.module.LLMatcher.validate_grammar(grammar, backend.tokenizer, limits=backend.limits))
            oracle.require(type(error) is str and not error, "case_compile")
            negative = oracle.evaluate_sample(backend, grammar, data + b"x")
            oracle.require(negative["accepted"] is False, "control_acceptance")
            short = oracle.evaluate_sample(backend, grammar, truncated)
            rows.append({"wrapper": label, "negative_rejected": True,
                         "truncated_accepted": short["accepted"], **compare(backend, grammar, data)})
        cases.append({"index": index, "schema_sha256": hashlib.sha256(raw_schema.encode("utf-8")).hexdigest(),
                      "sample_sha256": hashlib.sha256(data).hexdigest(), "sample_bytes": len(data),
                      "truncated_bytes": len(truncated), "truncated_sha256": hashlib.sha256(truncated).hexdigest(), "paths": rows})
    return {"version": 1, "scope": SCOPE, "native": True,
            "status": "observed", "controls": controls, "reduction": reduction, "cases": cases}


def validate_report(report):
    """Validate closed metadata against this fixed original, without native imports."""
    def integer(value, lo, hi):
        return type(value) is int and lo <= value <= hi
    try:
        if (type(report) is not dict or set(report) != {"version", "scope", "native", "status", "controls", "reduction", "cases"}
                or type(report["version"]) is not int or report["version"] != 1
                or report["scope"] != SCOPE or report["native"] is not True or report["status"] != "observed"
                or type(report["controls"]) is not dict or set(report["controls"]) != {"basic_compile", "valid_complete", "illegal_rejected", "incomplete_rejected", "unsupported_refused"}
                or any(v is not True for v in report["controls"].values())):
            return False
        reduction = report["reduction"]
        if (type(reduction) is not dict or set(reduction) != {"status", "indexes", "evaluations"}
                or reduction["status"] not in ("deletion_minimal", "budget_exhausted", "not_reproduced")
                or not integer(reduction["evaluations"], 1, MAX_EVALUATIONS)
                or type(reduction["indexes"]) is not list
                or not all(integer(i, 0, len(ORIGINAL) - 1) for i in reduction["indexes"])
                or sorted(set(reduction["indexes"])) != reduction["indexes"]):
            return False
        if reduction["status"] == "not_reproduced" and (reduction["indexes"] != list(range(len(ORIGINAL))) or reduction["evaluations"] != 1):
            return False
        texts = (ORIGINAL, "".join(ORIGINAL[i] for i in reduction["indexes"]))
        if type(report["cases"]) is not list or len(report["cases"]) != 2:
            return False
        for index, (case, text) in enumerate(zip(report["cases"], texts)):
            data = encoded(text).encode("utf-8")
            prefix_len = (len(text.encode("utf-8")) - 1) % 31 + 1
            truncated = encoded(text.encode("utf-8")[:prefix_len].decode("utf-8")).encode("utf-8")
            if (type(case) is not dict or set(case) != {"index", "schema_sha256", "sample_sha256", "sample_bytes", "truncated_bytes", "truncated_sha256", "paths"}
                    or not integer(case["index"], index, index)
                    or case["schema_sha256"] != hashlib.sha256(schema(text).encode("utf-8")).hexdigest()
                    or case["sample_sha256"] != hashlib.sha256(data).hexdigest()
                    or not integer(case["sample_bytes"], len(data), len(data))
                    or not integer(case["truncated_bytes"], len(truncated), len(truncated))
                    or case["truncated_sha256"] != hashlib.sha256(truncated).hexdigest()
                    or type(case["paths"]) is not list or len(case["paths"]) != 4):
                return False
            for path, label in zip(case["paths"], ("json_default", "lark_default", "lark_no_forcing", "regex_exact")):
                mask = path["mask"]
                keys = {"wrapper", "negative_rejected", "truncated_accepted", "mask", "validated_tokens", "tokens_with_eos", "direct_consumed", "direct_error", "direct_complete"}
                rejected = mask["outcome"] == "BYTE_MASK"
                if rejected:
                    keys |= {"next_byte_validation", "next_byte_mask", "mask_allowed_count", "mask_allowed_tokens"}
                if (type(path) is not dict or set(path) != keys or path["wrapper"] != label
                        or path["negative_rejected"] is not True
                        or any(type(path[k]) is not bool for k in ("truncated_accepted", "direct_consumed", "direct_error", "direct_complete"))
                        or not integer(path["tokens_with_eos"], len(data) + 1, len(data) + 1)
                        or not integer(path["validated_tokens"], 0, len(data) + 1)
                        or type(mask) is not dict or set(mask) != {"accepted", "outcome", "checked_bytes"}
                        or type(mask["accepted"]) is not bool or mask["outcome"] not in ("COMPLETE", "BYTE_MASK", "INCOMPLETE")
                        or mask["accepted"] != (mask["outcome"] == "COMPLETE")
                        or not integer(mask["checked_bytes"], 0, len(data) - 1 if rejected else len(data))
                        or (not rejected and mask["checked_bytes"] != len(data))
                        or path["direct_consumed"] == path["direct_error"]
                        or (path["direct_complete"] and (not path["direct_consumed"] or path["direct_error"]))):
                    return False
                if rejected and (not integer(path["next_byte_validation"], 0, 1) or type(path["next_byte_mask"]) is not bool
                        or not integer(path["mask_allowed_count"], 0, 262) or type(path["mask_allowed_tokens"]) is not list
                        or not all(integer(t, 0, 261) for t in path["mask_allowed_tokens"])
                        or sorted(set(path["mask_allowed_tokens"])) != path["mask_allowed_tokens"]
                        or len(path["mask_allowed_tokens"]) != path["mask_allowed_count"]):
                    return False
        expected_acceptance = reduction["status"] == "not_reproduced"
        return (all(c["paths"][0]["mask"]["accepted"] == expected_acceptance for c in report["cases"])
                and len(json.dumps(report).encode("utf-8")) <= 65536)
    except (ValueError, KeyError, TypeError, UnicodeError):
        return False


def validate_pattern_corpus(raw, corpus_raw):
    oracle.require(type(raw) is bytes and 0 < len(raw) <= oracle.MAX_INPUT, "corpus_invalid")
    corpus = oracle.validate_corpus(corpus_raw)
    try:
        value = oracle._json(raw.decode("utf-8", "strict"))
        oracle.require(type(value) is dict and set(value) == {"version", "scope", "source_corpus_sha256", "cases"}, "corpus_invalid")
        oracle.require(type(value["version"]) is int and value["version"] == 1 and value["scope"] == "locallore_finite_regex_corpus_v1"
                       and value["source_corpus_sha256"] == hashlib.sha256(corpus_raw).hexdigest(), "corpus_invalid")
        oracle.require(type(value["cases"]) is list and len(value["cases"]) == len(corpus["cases"]), "corpus_invalid")
        result = {}
        for index, (row, case) in enumerate(zip(value["cases"], corpus["cases"])):
            oracle.require(type(row) is dict and set(row) == {"index", "schema_sha256", "regex"}
                           and type(row["index"]) is int and row["index"] == index, "corpus_invalid")
            key = hashlib.sha256(case["schema_json"].encode("utf-8")).hexdigest()
            oracle.require(row["schema_sha256"] == key, "corpus_invalid")
            pattern = row["regex"]
            oracle.require(type(pattern) is str and pattern.startswith("\\A(?:") and pattern.endswith(")\\z")
                           and 0 < len(pattern.encode("utf-8", "strict")) <= 32768, "corpus_invalid")
            oracle.require(key not in result or result[key] == pattern, "corpus_invalid")
            result[key] = pattern
        return result
    except (UnicodeError, KeyError, TypeError):
        raise oracle.OracleFailure("corpus_invalid") from None


class FiniteBackend:
    """Actual JVM-produced patterns only; unchanged native sanity controls and byte matcher."""
    native = True

    def __init__(self, base, patterns):
        self.base, self.patterns = base, patterns
        self.eos_token, self.vocab_size = base.eos_token, base.vocab_size

    def compile(self, raw_schema):
        if raw_schema in (oracle.BASIC_SCHEMA, oracle.UNSUPPORTED_SCHEMA):
            return self.base.compile(raw_schema)
        key = hashlib.sha256(raw_schema.encode("utf-8")).hexdigest()
        oracle.require(key in self.patterns, "case_compile")
        grammar = self.base.module.LLMatcher.grammar_from_regex(self.patterns[key])
        error = self.base.module.LLMatcher.validate_grammar(grammar, self.base.tokenizer, limits=self.base.limits)
        oracle.require(type(error) is str, "backend_state")
        return None if error else grammar

    def matcher(self, grammar):
        return self.base.matcher(grammar)


def main():
    try:
        if len(sys.argv) == 3 and sys.argv[1] == "--module-root":
            backend = oracle.NativeBackend(sys.argv[2])
            report = run_probe(backend)
            oracle.require(validate_report(report), "backend_state")
            code = 0
        else:
            oracle.require(len(sys.argv) == 7 and sys.argv[1] == "--corpus" and sys.argv[3] == "--regex-corpus"
                           and sys.argv[5] == "--module-root", "arguments")
            with Path(sys.argv[2]).open("rb") as stream:
                corpus = stream.read(oracle.MAX_INPUT + 1)
            with Path(sys.argv[4]).open("rb") as stream:
                patterns_raw = stream.read(oracle.MAX_INPUT + 1)
            patterns = validate_pattern_corpus(patterns_raw, corpus)  # Before native import.
            backend = FiniteBackend(oracle.NativeBackend(sys.argv[6]), patterns)
            checked = oracle.run_oracle(corpus, backend)
            report = {"version": 1, "scope": "locallore_finite_regex_oracle_v1",
                      "pattern_corpus_sha256": hashlib.sha256(patterns_raw).hexdigest(), "oracle": checked}
            code = 0 if checked["status"] == "passed" else 1
    except oracle.OracleFailure as failure:
        report = {"version": 1, "scope": "locallore_llguidance_literal_probe_v1", "status": "failed", "reason": failure.reason}
        code = 2
    except BaseException:
        report = {"version": 1, "scope": "locallore_llguidance_literal_probe_v1", "status": "failed", "reason": "unexpected"}
        code = 2
    print(json.dumps(report, separators=(",", ":"), sort_keys=True))
    return code


if __name__ == "__main__":
    raise SystemExit(main())
