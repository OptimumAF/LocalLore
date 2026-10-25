"""Pure space-representation controls; native admission and deadlines are external.

Every sample keeps its original correspondence. No SDK/SP equivalence is implied.
Copyright 2026 LocalLore contributors. SPDX-License-Identifier: Apache-2.0
"""
import copy
import json
import math
from types import SimpleNamespace

try:
    from . import litert_tokenizer_compare as compare
except ImportError:
    import importlib.util
    from pathlib import Path
    _spec = importlib.util.spec_from_file_location("escape_compare", Path(__file__).with_name("litert_tokenizer_compare.py"))
    compare = importlib.util.module_from_spec(_spec)
    _spec.loader.exec_module(compare)

SCOPE = "locallore_litert_json_escape_probe_v1"
REPRESENTATIONS = ("ORIGINAL", "SPACE_ESCAPES")
PATTERNS = ("ORIGINAL", "SPACE_ALTERNATIVES")
FORCING = ("DEFAULT", "DISABLED")
STATUSES = ("ORIGINAL", "UNCHANGED", "SPACE_ESCAPED", "NOT_APPLICABLE")


class Refused(Exception):
    pass


def require(value):
    if not value:
        raise Refused()


def encoded(value):
    return compare._encoded(value)


def digest(data):
    return compare._hash(data)


def _json(text):
    value = compare._oracle._json(text)
    def check(item):
        if type(item) is str:
            item.encode("utf-8", "strict")
        elif type(item) is float:
            require(math.isfinite(item))
        elif type(item) is list:
            for child in item: check(child)
        elif type(item) is dict:
            for key, child in item.items(): check(key); check(child)
    check(value)
    return value


def _typed(value):
    if type(value) is dict:
        return (dict, tuple((key, _typed(child)) for key, child in value.items()))
    if type(value) is list:
        return (list, tuple(map(_typed, value)))
    return (type(value), value)


def space_escapes(text):
    """Replace only literal U+0020 inside strict JSON strings, preserving bytes otherwise."""
    try:
        original = _json(text)
        result, inside, index = [], False, 0
        while index < len(text):
            char = text[index]
            if inside and char == "\\":
                result.append(text[index:index + 2]); index += 2; continue
            if char == '"': inside = not inside
            result.append("\\u0020" if inside and char == " " else char)
            index += 1
        changed = "".join(result)
        require(_typed(original) == _typed(_json(changed)))
        if len(changed.encode("utf-8")) > compare._oracle.MAX_TEXT:
            return text, "NOT_APPLICABLE", "IDENTICAL_BYTES"
        return changed, "SPACE_ESCAPED" if changed != text else "UNCHANGED", "DECODED_EQUAL"
    except Exception:
        return text, "NOT_APPLICABLE", "IDENTICAL_BYTES"


def space_alternatives(pattern):
    """Restrict to the canonical codec's literal/group/alternation regex language.

    No classes, wildcards, repetition, flags, lookarounds or escaped whitespace.
    Every raw space must be inside a JSON string on every alternative path.
    """
    require(type(pattern) is str and pattern.startswith(r"\A(?:") and pattern.endswith(r")\z"))
    body, at = pattern[5:-3], 0
    meta = "\\.+*?()|[]{}^$"

    def literal(states, char):
        result = set()
        for inside, escape in states:
            if char == " ": require(inside and not escape)
            require(ord(char) >= 32)
            if escape:
                result.add((inside, False))
            elif inside and char == "\\":
                result.add((inside, True))
            elif char == '"':
                result.add((not inside, False))
            else:
                result.add((inside, False))
        return result

    def group(states, depth):
        nonlocal at
        require(depth <= 64)
        ends, current = set(), states
        while at < len(body):
            char = body[at]
            if body.startswith("(?:", at):
                at += 3; current = group(current, depth + 1)
            elif char == ")":
                require(depth > 0); at += 1; return ends | current
            elif char == "|":
                ends |= current; current = states; at += 1
            elif char == "\\":
                require(at + 1 < len(body) and body[at + 1] in meta)
                current = literal(current, body[at + 1]); at += 2
            else:
                require(char not in meta)
                current = literal(current, char); at += 1
        require(depth == 0)
        return ends | current

    require(group({(False, False)}, 0) == {(False, False)} and at == len(body))
    result = pattern.replace(" ", r"(?: |\\u0020)")
    require(len(result.encode("utf-8")) <= 32768)
    return result


def _raw(value):
    raw = value if type(value) is bytes else encoded(value)
    require(type(raw) is bytes and 0 < len(raw) <= compare._oracle.MAX_INPUT)
    return raw


def _prepare(corpus, sidecar, representation, pattern_mode, forcing):
    require(type(representation) is str and representation in REPRESENTATIONS
            and type(pattern_mode) is str and pattern_mode in PATTERNS
            and type(forcing) is str and forcing in FORCING)
    original_raw, sidecar_raw = _raw(corpus), _raw(sidecar)
    original = compare._oracle.validate_corpus(original_raw)
    value = compare._oracle._json(sidecar_raw.decode("utf-8", "strict"))
    require(type(value) is dict and set(value) == {"version", "scope", "source_corpus_sha256", "cases"}
            and type(value["version"]) is int and value["version"] == 1
            and value["scope"] == "locallore_finite_regex_corpus_v1"
            and value["source_corpus_sha256"] == digest(original_raw)
            and type(value["cases"]) is list and len(value["cases"]) == len(original["cases"]))
    effective, rows, pattern_rows = copy.deepcopy(original), [], []
    seen = {}
    for index, (case, source, target) in enumerate(zip(value["cases"], original["cases"], effective["cases"])):
        require(type(case) is dict and set(case) == {"index", "schema_sha256", "regex"}
                and type(case["index"]) is int and case["index"] == index
                and case["schema_sha256"] == digest(source["schema_json"].encode("utf-8")))
        pattern = case["regex"]
        require(type(pattern) is str and 0 < len(pattern.encode("utf-8")) <= 32768
                and pattern.startswith(r"\A(?:") and pattern.endswith(r")\z"))
        key = case["schema_sha256"]
        require(key not in seen or seen[key] == pattern); seen[key] = pattern
        transformed = space_alternatives(pattern) if pattern_mode == "SPACE_ALTERNATIVES" else pattern
        target["finite_regex"] = transformed
        pattern_rows.append([digest(pattern.encode("utf-8")), digest(transformed.encode("utf-8"))])
        for category in ("positives", "negatives"):
            for sample, changed in zip(source[category], target[category]):
                text = sample["json"]
                if representation == "ORIGINAL":
                    try:
                        _json(text)
                        status = "ORIGINAL"
                    except Exception:
                        status = "NOT_APPLICABLE"
                    new, equivalence = text, "IDENTICAL_BYTES"
                else:
                    new, status, equivalence = space_escapes(text)
                changed["json"] = new
                rows.append([digest(text.encode("utf-8")), len(text.encode("utf-8")), status, equivalence])
    compare._corpus(effective)
    return original_raw, sidecar_raw, effective, rows, pattern_rows


def _proxy(module, forcing, grammar_hashes):
    class Matcher:
        def __new__(cls, *args, **kwargs): return module.LLMatcher(*args, **kwargs)
        validate_grammar = staticmethod(module.LLMatcher.validate_grammar)

        @staticmethod
        def grammar_from_regex(pattern):
            grammar = module.LLMatcher.grammar_from_regex(pattern)
            require(type(grammar) is str)
            if forcing == "DISABLED":
                # Verified public API at guidance-ai/llguidance commit
                # 29e33a219f77be1cc37d8394630440f448d19945:
                # api.rs332-336 emits a single regex
                # lark_grammar; api.rs30-39 defines this Lark directive. No JSON
                # options are guessed/added. grammar_from_lark returns its input.
                value = compare._oracle._json(grammar)
                require(type(value) is dict and set(value) == {"grammars", "max_tokens"}
                        and value["max_tokens"] is None and type(value["grammars"]) is list
                        and len(value["grammars"]) == 1)
                row = value["grammars"][0]
                require(type(row) is dict and set(row) == {"name", "json_schema", "lark_grammar"}
                        and row["name"] == "regex" and row["json_schema"] is None)
                lark = row["lark_grammar"]
                require(type(lark) is str and lark.startswith("start: /") and lark.endswith("/")
                        and "\n" not in lark and "\r" not in lark)
                lark = '%llguidance {"no_forcing":true}\n' + lark
                grammar = module.LLMatcher.grammar_from_lark(lark)
                require(type(grammar) is str and grammar == lark)
            grammar_hashes.append(digest(grammar.encode("utf-8")))
            return grammar
    return SimpleNamespace(LLMatcher=Matcher, LLTokenizer=module.LLTokenizer, LLParserLimits=module.LLParserLimits)


def run_escape_probe(module, raw_tokens, eos, corpus, regex_sidecar, representation, pattern_mode, forcing):
    """Run exactly one control. Prefer original artifact bytes for exact SHA binding."""
    try:
        raw, sidecar, effective, rows, patterns = _prepare(corpus, regex_sidecar, representation, pattern_mode, forcing)
    except Exception:
        return {"version": 1, "scope": SCOPE, "status": "failed", "reason": "input_invalid"}
    grammars = []
    try:
        native = compare.compare_tokenizers(_proxy(module, forcing, grammars), None, raw_tokens, eos, effective)
        require(compare.validate_report(native, effective))
        report = {"version": 1, "scope": SCOPE, "status": native["status"], "reason": native["reason"],
                  "representation": representation, "pattern_mode": pattern_mode, "forcing": forcing,
                  "source_corpus_sha256": digest(raw), "regex_sidecar_sha256": digest(sidecar),
                  "correspondence": rows, "patterns": patterns, "grammars": grammars,
                  "representation_counts": {key: sum(row[2] == key for row in rows) for key in STATUSES},
                  "comparison": native}
        require(len(encoded(report)) <= compare._oracle.MAX_REPORT)
        return report
    except Exception:
        return {"version": 1, "scope": SCOPE, "status": "failed", "reason": "comparison_invalid"}


def validate_report(report, corpus, regex_sidecar, representation=None, pattern_mode=None, forcing=None):
    """Validate closed correspondence/accounting; external ownership/provenance remains external."""
    try:
        require(type(report) is dict and set(report) == {"version", "scope", "status", "reason", "representation",
                "pattern_mode", "forcing", "source_corpus_sha256", "regex_sidecar_sha256", "correspondence",
                "patterns", "grammars", "representation_counts", "comparison"})
        require(type(report["version"]) is int and report["version"] == 1 and report["scope"] == SCOPE)
        for key, expected in (("representation", representation), ("pattern_mode", pattern_mode), ("forcing", forcing)):
            if expected is not None: require(report[key] == expected)
        raw, sidecar, effective, rows, patterns = _prepare(corpus, regex_sidecar, report["representation"], report["pattern_mode"], report["forcing"])
        require(report["source_corpus_sha256"] == digest(raw) and report["regex_sidecar_sha256"] == digest(sidecar)
                and report["correspondence"] == rows and report["patterns"] == patterns)
        # Equality alone admits bool-as-int; canonical serialization binds exact JSON types.
        require(encoded(report["correspondence"]) == encoded(rows))
        counts = {key: sum(row[2] == key for row in rows) for key in STATUSES}
        require(encoded(report["representation_counts"]) == encoded(counts))
        require(type(report["grammars"]) is list and len(report["grammars"]) <= len(effective["cases"])
                and all(type(key) is str and len(key) == 64 and all(c in "0123456789abcdef" for c in key) for key in report["grammars"]))
        require(compare.validate_report(report["comparison"], effective)
                and report["status"] == report["comparison"]["status"] and report["reason"] == report["comparison"]["reason"])
        compiled = sum(row["compile"]["raw_piece"] in ("COMPILED", "REFUSED") for row in report["comparison"]["cases"])
        require(len(report["grammars"]) >= compiled and len(encoded(report)) <= compare._oracle.MAX_REPORT)
        return True
    except Exception:
        return False
