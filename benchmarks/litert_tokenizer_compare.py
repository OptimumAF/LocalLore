"""Pure host comparison seam; the caller authenticates and owns any native module.

No model, tokenizer file, SDK or extension is imported here. Raw-piece controls
are not the SDK callback; the None-JSON control is not a SentencePiece encoder.
Copyright 2026 LocalLore contributors. SPDX-License-Identifier: Apache-2.0
"""
import hashlib
import importlib.util
import json
from pathlib import Path


def _sibling(name):
    spec = importlib.util.spec_from_file_location("locallore_compare_" + name, Path(__file__).with_name(name + ".py"))
    value = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(value)
    return value


_oracle = _sibling("llguidance_oracle")
_metadata = _sibling("litert_tokenizer_oracle")
SCOPE = "locallore_litert_tokenizer_compare_v1"
REASONS = frozenset(("none", "input_invalid", "tokenizer_init", "tokenizer_state", "token_ids",
                     "tokenizer_runtime", "compile_runtime", "compile_refused", "matcher_runtime",
                     "matcher_state", "matcher_mask", "report_limit", "unexpected"))


class CompareRefused(Exception):
    def __init__(self, reason):
        self.reason = reason if type(reason) is str and reason in REASONS else "unexpected"
        super().__init__(self.reason)


def _require(condition, reason):
    if not condition:
        raise CompareRefused(reason)


def _call(reason, function, *args, **kwargs):
    try:
        return function(*args, **kwargs)
    except CompareRefused:
        raise
    except BaseException:
        raise CompareRefused(reason) from None


def _bytes(text):
    return text.encode("utf-8", "strict")


def _hash(data):
    return hashlib.sha256(data).hexdigest()


def _encoded(value):
    return json.dumps(value, ensure_ascii=False, allow_nan=False, separators=(",", ":")).encode("utf-8")


def _corpus(corpus):
    _require(type(corpus) is dict and type(corpus.get("cases")) is list, "input_invalid")
    _require(len(_encoded(corpus)) <= _oracle.MAX_INPUT, "input_invalid")
    # Only the optional, caller-bound pattern is removed from a validation copy.
    # Original schema/sample strings and all other inherited keys remain intact.
    plain = dict(corpus)
    plain["cases"] = []
    patterns = []
    for case in corpus["cases"]:
        _require(type(case) is dict, "input_invalid")
        copy = dict(case)
        pattern = copy.pop("finite_regex", None)
        if "finite_regex" in case:
            _require(type(pattern) is str and pattern.startswith("\\A(?:") and pattern.endswith(")\\z")
                     and 0 < len(_bytes(pattern)) <= 32768, "input_invalid")
        patterns.append(pattern)
        plain["cases"].append(copy)
    _oracle.validate_corpus(_encoded(plain))
    return plain, patterns


def _inputs(tokenizer_json, raw_tokens, eos, corpus):
    _require(type(raw_tokens) is tuple and 0 < len(raw_tokens) <= _metadata.MAX_VOCAB, "input_invalid")
    _require(all(type(piece) is bytes and len(piece) <= _metadata.MAX_PIECE for piece in raw_tokens), "input_invalid")
    _require(sum(map(len, raw_tokens)) <= _metadata.MAX_JSON and len(set(raw_tokens)) == len(raw_tokens), "input_invalid")
    _require(type(eos) is int and 0 <= eos < len(raw_tokens), "input_invalid")
    if tokenizer_json is not None:
        _require(type(tokenizer_json) is str and tokenizer_json.startswith("{"), "input_invalid")
        data = _bytes(tokenizer_json)
        _require(len(data) <= _metadata.MAX_JSON and _metadata.hf_raw_vocabulary(data) == raw_tokens, "input_invalid")
    return _corpus(corpus)


class _Greedy:
    """Exact longest raw-byte segmentation, deliberately not an SP encoder."""
    def __init__(self, tokens):
        self.lookup = {piece: index for index, piece in enumerate(tokens) if piece}
        lengths = {}
        for piece in self.lookup:
            lengths.setdefault(piece[0], set()).add(len(piece))
        self.lengths = {byte: sorted(sizes, reverse=True) for byte, sizes in lengths.items()}

    def encode(self, data):
        ids, offset = [], 0
        while offset < len(data):
            token = None
            for size in self.lengths.get(data[offset], ()):
                if size <= len(data) - offset:
                    token = self.lookup.get(data[offset:offset + size])
                    if token is not None:
                        offset += size
                        ids.append(token)
                        break
            if token is None:
                return ids, offset
        return ids, offset


class _Raw:
    is_tokenizer_wrapper = True
    bos_token_id = None

    def __init__(self, tokens, eos, semantic, greedy):
        self.tokens, self.eos_token_id = list(tokens), eos
        self.special_token_ids = []
        self.semantic, self.greedy = semantic, greedy
        self.failure = None

    def __call__(self, text):
        # The pinned Rust Python-callback bridge unwraps exceptions. Never throw
        # across that boundary; the outer comparison checks this sticky flag.
        try:
            _require(type(text) is str and len(_bytes(text)) <= _oracle.MAX_TEXT, "token_ids")
            if self.semantic is not None:
                return _ids(_call("tokenizer_runtime", self.semantic.tokenize_str, text), len(self.tokens))
            data = _bytes(text)
            ids, consumed = self.greedy.encode(data)
            return ids if consumed == len(data) else []
        except BaseException as failure:
            if self.failure is None:
                self.failure = failure.reason if isinstance(failure, CompareRefused) else "tokenizer_runtime"
            return []


def _ids(value, vocab):
    _require(type(value) is list and len(value) <= _oracle.MAX_TEXT
             and all(type(token) is int and 0 <= token < vocab for token in value), "token_ids")
    return value


def _state(matcher, guard):
    guard()
    error = _call("matcher_runtime", matcher.is_error)
    reason = _call("matcher_runtime", matcher.stop_reason)
    _require(type(error) is bool and not error and type(reason) is str and reason in _oracle.SAFE_STOPS, "matcher_state")
    guard()


def _mask(matcher, vocab, guard):
    _state(matcher, guard)
    value = _call("matcher_runtime", matcher.compute_bitmask)
    _state(matcher, guard)
    # Pinned LLGuidance 1.3.0 returns the entire SimpleVob backing allocation,
    # unlike its pointer API's ceil(V/32) words. TokTrie requests capacity V+1;
    # SimpleVob.resize allocates floor(capacity/32)+1 u32 words. Sources at
    # guidance-ai/llguidance commit 29e33a219f77be1cc37d8394630440f448d19945:
    # python_ext/src/llmatcher.rs426-430, toktrie/src/toktree.rs239-246,
    # toktrie/src/svob.rs75-80,252-256. Padding never names a token: all consumed
    # IDs and EOS are independently bounded; prefix counts mask it out below.
    expected = (((vocab + 1) // 32) + 1) * 4
    _require(type(value) is bytes and len(value) == expected, "matcher_mask")
    return value


def _allowed(mask, token):
    return bool(mask[token // 8] & (1 << (token % 8)))


def _evaluate(module, tokenizer, grammar, limits, ids, vocab, eos, guard):
    matcher = _call("matcher_runtime", module.LLMatcher, tokenizer, grammar, log_level=0, limits=limits)
    _state(matcher, guard)
    for index, token in enumerate(ids):
        if not _allowed(_mask(matcher, vocab, guard), token):
            return "TOKEN_MASK", False, index
        _require(_call("matcher_runtime", matcher.consume_token, token) is True, "matcher_state")
        _state(matcher, guard)
    mask = _mask(matcher, vocab, guard)
    accepting = _call("matcher_runtime", matcher.is_accepting)
    _state(matcher, guard)
    _require(type(accepting) is bool and accepting == _allowed(mask, eos), "matcher_state")
    if not accepting:
        return "INCOMPLETE", False, len(ids)
    _require(_call("matcher_runtime", matcher.consume_token, eos) is True, "matcher_state")
    _state(matcher, guard)
    _require(_call("matcher_runtime", matcher.is_stopped) is True, "matcher_state")
    return "COMPLETE", True, len(ids)


def _prefix(module, tokenizer, grammar, limits, ids, vocab, guard):
    matcher = _call("matcher_runtime", module.LLMatcher, tokenizer, grammar, log_level=0, limits=limits)
    _state(matcher, guard)
    for index, token in enumerate(ids):
        if not _allowed(_mask(matcher, vocab, guard), token):
            return "PREFIX_REJECTED", index, None
        _require(_call("matcher_runtime", matcher.consume_token, token) is True, "matcher_state")
        _state(matcher, guard)
    mask = _mask(matcher, vocab, guard)
    # Python3.9-compatible count, ignoring packed-word padding above vocabulary.
    count = bin(int.from_bytes(mask, "little") & ((1 << vocab) - 1)).count("1")
    return "MASK_COMPUTED", len(ids), count


def _result(outcome="UNRUN", reason="none"):
    return {"outcome": outcome, "accepted": None, "checked_tokens": 0, "roundtrip": None, "reason": reason}


def _failed(report, reason):
    report["status"] = "failed"
    if report["reason"] == "none":
        report["reason"] = reason


def _compare(module, tokenizer_json, raw_tokens, eos, corpus):
    plain, patterns = _inputs(tokenizer_json, raw_tokens, eos, corpus)
    names = ("semantic_hf", "raw_piece") if tokenizer_json is not None else ("raw_piece",)
    report = {"version": 1, "scope": SCOPE, "status": "passed", "reason": "none",
              "sdk_equivalent": False, "sp_encoder": False, "callback_equivalent": False,
              "synthetic_callback": tokenizer_json is None, "vocab_size": len(raw_tokens), "eos": eos,
              "tokenizer_json_sha256": _hash(_bytes(tokenizer_json)) if tokenizer_json is not None else None,
              "raw_vocabulary_sha256": _metadata.vocabulary_report(raw_tokens)["sha256"],
              "corpus_json_sha256": _hash(_encoded(corpus)), "refusals": len(plain["refusals"]),
              "sample_count": 0, "positive_count": 0, "negative_count": 0,
              "mode_disagreements": 0, "first_divergence": None, "modes": {}, "cases": []}
    for name in names:
        report["modes"][name] = {"checked": 0, "mismatches": 0, "unencodable": 0,
                                 "non_roundtrip": 0, "compile_refusals": 0, "runtime_failures": 0}
    for case_index, (case, pattern) in enumerate(zip(plain["cases"], patterns)):
        row = {"index": case_index, "schema_sha256": _hash(_bytes(case["schema_json"])),
               "finite_regex_sha256": _hash(_bytes(pattern)) if pattern is not None else None,
               "compile": {name: "UNRUN" for name in names}, "samples": []}
        for category in ("positives", "negatives"):
            expected = category == "positives"
            for index, sample in enumerate(case[category]):
                data = _bytes(sample["json"])
                row["samples"].append({"index": index, "positive": expected, "sha256": _hash(data), "bytes": len(data),
                                       "encoding": {"tokens": 0, "bytes": 0, "complete": False},
                                       **{name: _result() for name in names}})
                report["sample_count"] += 1
                report["positive_count" if expected else "negative_count"] += 1
        report["cases"].append(row)

    try:
        greedy = _Greedy(raw_tokens)
        semantic = None
        limits = _call("tokenizer_init", module.LLParserLimits, verbose_errors=False)
        tokenizers = {}
        if tokenizer_json is not None:
            semantic = _call("tokenizer_init", module.LLTokenizer, tokenizer_json, eos_token=eos, slices=[])
            tokenizers["semantic_hf"] = semantic
        wrapper = _Raw(raw_tokens, eos, semantic, greedy)
        tokenizers["raw_piece"] = _call("tokenizer_init", module.LLTokenizer, wrapper, slices=[])
        for tokenizer in tokenizers.values():
            _require(type(tokenizer.vocab_size) is int and tokenizer.vocab_size == len(raw_tokens)
                     and type(tokenizer.eos_token) is int and tokenizer.eos_token == eos, "tokenizer_state")
        _require(wrapper.failure is None, wrapper.failure or "tokenizer_runtime")
    except BaseException as failure:
        _failed(report, failure.reason if isinstance(failure, CompareRefused) else "tokenizer_init")
        return report

    for case_index, (case, pattern, row) in enumerate(zip(plain["cases"], patterns, report["cases"])):
        grammars = {}
        for name, tokenizer in tokenizers.items():
            try:
                factory = module.LLMatcher.grammar_from_regex if pattern is not None else module.LLMatcher.grammar_from_json_schema
                grammar = _call("compile_runtime", factory, pattern if pattern is not None else case["schema_json"])
                _require(type(grammar) is str, "compile_runtime")
                error = _call("compile_runtime", module.LLMatcher.validate_grammar, grammar, tokenizer, limits=limits)
                if name == "raw_piece":
                    _require(wrapper.failure is None, wrapper.failure or "tokenizer_runtime")
                _require(type(error) is str, "compile_runtime")
                if error:
                    row["compile"][name] = "REFUSED"
                    report["modes"][name]["compile_refusals"] += 1
                    _failed(report, "compile_refused")
                else:
                    row["compile"][name] = "COMPILED"
                    grammars[name] = grammar
            except BaseException:
                row["compile"][name] = "FAILED"
                report["modes"][name]["runtime_failures"] += 1
                _failed(report, "compile_runtime")
        source_samples = [sample for category in ("positives", "negatives") for sample in case[category]]
        for sample, item in zip(source_samples, row["samples"]):
            data = _bytes(sample["json"])
            try:
                if semantic is not None:
                    ids = _ids(_call("tokenizer_runtime", semantic.tokenize_str, sample["json"]), len(raw_tokens))
                    _require(bool(ids), "token_ids")
                    consumed = len(data)
                else:
                    ids, consumed = greedy.encode(data)
                item["encoding"] = {"tokens": len(ids), "bytes": consumed, "complete": consumed == len(data)}
            except BaseException as failure:
                reason = failure.reason if isinstance(failure, CompareRefused) else "tokenizer_runtime"
                for name in names:
                    item[name] = _result("FAILED", reason)
                    report["modes"][name]["runtime_failures"] += 1
                _failed(report, reason)
                continue
            for name, tokenizer in tokenizers.items():
                stats = report["modes"][name]
                guard = (lambda: _require(wrapper.failure is None, wrapper.failure or "tokenizer_runtime")) if name == "raw_piece" else (lambda: None)
                if consumed != len(data):
                    value = _result("UNENCODABLE")
                    value.update(prefix_outcome="UNRUN", next_allowed_count=None)
                    if name in grammars:
                        try:
                            outcome, checked, count = _prefix(module, tokenizer, grammars[name], limits, ids, len(raw_tokens), guard)
                            value.update(prefix_outcome=outcome, checked_tokens=checked, next_allowed_count=count)
                        except BaseException as failure:
                            reason = failure.reason if isinstance(failure, CompareRefused) else "matcher_runtime"
                            value.update(prefix_outcome="FAILED", reason=reason)
                            stats["runtime_failures"] += 1
                            _failed(report, reason)
                    item[name] = value
                    stats["unencodable"] += 1
                    if report["status"] != "failed": report["status"] = "mismatch"
                    continue
                if name not in grammars:
                    item[name] = _result("COMPILE_REFUSED", "compile_refused") if row["compile"][name] == "REFUSED" else _result()
                    continue
                try:
                    decoded = _call("tokenizer_runtime", tokenizer.decode_bytes, ids)
                    _require(type(decoded) is bytes and len(decoded) <= _metadata.MAX_JSON, "tokenizer_state")
                    roundtrip = decoded == data
                    outcome, accepted, checked = _evaluate(module, tokenizer, grammars[name], limits, ids, len(raw_tokens), eos, guard)
                    item[name] = {"outcome": outcome, "accepted": accepted, "checked_tokens": checked,
                                  "roundtrip": roundtrip, "reason": "none"}
                    stats["checked"] += 1
                    stats["non_roundtrip"] += not roundtrip
                    if not roundtrip or accepted != item["positive"]:
                        stats["mismatches"] += 1
                        if report["status"] != "failed": report["status"] = "mismatch"
                except BaseException as failure:
                    reason = failure.reason if isinstance(failure, CompareRefused) else "matcher_runtime"
                    item[name] = _result("FAILED", reason)
                    stats["runtime_failures"] += 1
                    _failed(report, reason)
            if len(names) == 2 and item[names[0]] != item[names[1]]:
                report["mode_disagreements"] += 1
                if report["first_divergence"] is None:
                    rejected = [item[name]["checked_tokens"] for name in names if item[name]["outcome"] == "TOKEN_MASK"]
                    report["first_divergence"] = {"case": case_index, "sample": item["index"], "positive": item["positive"],
                                                   "token": min(rejected) if rejected else None}
    _require(len(_encoded(report)) <= _oracle.MAX_REPORT, "report_limit")
    return report


def compare_tokenizers(module, tokenizer_json_str, raw_tokens, eos, corpus):
    """Use only the supplied module; ownership, authentication and deadline are external.

    With JSON, both modes consume the semantic tokenizer's IDs. Without JSON,
    raw longest-piece segmentation is synthetic; unencodable originals stay in
    the report and are never counted as successfully rejected negatives.
    """
    try:
        return _compare(module, tokenizer_json_str, raw_tokens, eos, corpus)
    except CompareRefused as failure:
        return {"version": 1, "scope": SCOPE, "status": "failed", "reason": failure.reason}
    except (_oracle.OracleFailure, _metadata.TokenizerOracleRefused, UnicodeError, ValueError, TypeError):
        return {"version": 1, "scope": SCOPE, "status": "failed", "reason": "input_invalid"}
    except BaseException:
        return {"version": 1, "scope": SCOPE, "status": "failed", "reason": "unexpected"}


def validate_report(report, corpus):
    """Check closed coverage/accounting, not native provenance or SDK equivalence."""
    def integer(value, maximum):
        return type(value) is int and 0 <= value <= maximum

    def digest(value):
        return type(value) is str and len(value) == 64 and all(char in "0123456789abcdef" for char in value)

    try:
        plain, patterns = _corpus(corpus)
        keys = {"version", "scope", "status", "reason", "sdk_equivalent", "sp_encoder", "callback_equivalent",
                "synthetic_callback", "vocab_size", "eos", "tokenizer_json_sha256", "raw_vocabulary_sha256",
                "corpus_json_sha256", "refusals", "sample_count", "positive_count", "negative_count",
                "mode_disagreements", "first_divergence", "modes", "cases"}
        _require(type(report) is dict and set(report) == keys, "input_invalid")
        _require(type(report["version"]) is int and report["version"] == 1 and report["scope"] == SCOPE, "input_invalid")
        _require(type(report["status"]) is str and report["status"] in ("passed", "mismatch", "failed")
                 and type(report["reason"]) is str and report["reason"] in REASONS, "input_invalid")
        _require(all(report[key] is False for key in ("sdk_equivalent", "sp_encoder", "callback_equivalent"))
                 and type(report["synthetic_callback"]) is bool, "input_invalid")
        names = ("raw_piece",) if report["synthetic_callback"] else ("semantic_hf", "raw_piece")
        _require(integer(report["vocab_size"], _metadata.MAX_VOCAB) and report["vocab_size"] > 0
                 and integer(report["eos"], report["vocab_size"] - 1), "input_invalid")
        _require((report["tokenizer_json_sha256"] is None if report["synthetic_callback"] else digest(report["tokenizer_json_sha256"]))
                 and digest(report["raw_vocabulary_sha256"]), "input_invalid")
        _require(report["corpus_json_sha256"] == _hash(_encoded(corpus))
                 and type(report["refusals"]) is int and report["refusals"] == len(plain["refusals"]), "input_invalid")
        _require(type(report["modes"]) is dict and set(report["modes"]) == set(names)
                 and type(report["cases"]) is list and len(report["cases"]) == len(plain["cases"]), "input_invalid")
        stats = {name: dict(checked=0, mismatches=0, unencodable=0, non_roundtrip=0,
                           compile_refusals=0, runtime_failures=0) for name in names}
        sample_count = positive_count = negative_count = disagreements = 0
        first = None
        failed = mismatch = unrun = False
        for case_index, (case, pattern, row) in enumerate(zip(plain["cases"], patterns, report["cases"])):
            _require(type(row) is dict and set(row) == {"index", "schema_sha256", "finite_regex_sha256", "compile", "samples"}
                     and type(row["index"]) is int and row["index"] == case_index
                     and row["schema_sha256"] == _hash(_bytes(case["schema_json"]))
                     and row["finite_regex_sha256"] == (_hash(_bytes(pattern)) if pattern is not None else None), "input_invalid")
            _require(type(row["compile"]) is dict and set(row["compile"]) == set(names), "input_invalid")
            for name in names:
                status = row["compile"][name]
                _require(type(status) is str and status in ("UNRUN", "COMPILED", "REFUSED", "FAILED"), "input_invalid")
                stats[name]["compile_refusals"] += status == "REFUSED"
                stats[name]["runtime_failures"] += status == "FAILED"
                failed |= status in ("REFUSED", "FAILED")
                unrun |= status == "UNRUN"
            samples = [(expected, index, sample) for category, expected in (("positives", True), ("negatives", False))
                       for index, sample in enumerate(case[category])]
            _require(type(row["samples"]) is list and len(row["samples"]) == len(samples), "input_invalid")
            for (expected, index, sample), item in zip(samples, row["samples"]):
                data = _bytes(sample["json"])
                _require(type(item) is dict and set(item) == {"index", "positive", "sha256", "bytes", "encoding", *names}
                         and type(item["index"]) is int and item["index"] == index and item["positive"] is expected
                         and item["sha256"] == _hash(data) and type(item["bytes"]) is int and item["bytes"] == len(data), "input_invalid")
                encoding = item["encoding"]
                _require(type(encoding) is dict and set(encoding) == {"tokens", "bytes", "complete"}
                         and integer(encoding["tokens"], _oracle.MAX_TEXT) and integer(encoding["bytes"], len(data))
                         and type(encoding["complete"]) is bool and encoding["complete"] == (encoding["bytes"] == len(data)), "input_invalid")
                sample_count += 1
                positive_count += expected
                negative_count += not expected
                for name in names:
                    value, count = item[name], stats[name]
                    _require(type(value) is dict and type(value.get("outcome")) is str, "input_invalid")
                    outcome = value["outcome"]
                    extra = {"prefix_outcome", "next_allowed_count"} if outcome == "UNENCODABLE" else set()
                    _require(set(value) == {"outcome", "accepted", "checked_tokens", "roundtrip", "reason"} | extra
                             and integer(value["checked_tokens"], encoding["tokens"])
                             and type(value["reason"]) is str and value["reason"] in REASONS, "input_invalid")
                    if outcome in ("COMPLETE", "TOKEN_MASK", "INCOMPLETE"):
                        _require(row["compile"][name] == "COMPILED" and encoding["complete"]
                                 and type(value["accepted"]) is bool and value["accepted"] == (outcome == "COMPLETE")
                                 and type(value["roundtrip"]) is bool and value["reason"] == "none"
                                 and (value["checked_tokens"] < encoding["tokens"] if outcome == "TOKEN_MASK"
                                      else value["checked_tokens"] == encoding["tokens"]), "input_invalid")
                        count["checked"] += 1
                        count["non_roundtrip"] += not value["roundtrip"]
                        differs = not value["roundtrip"] or value["accepted"] != expected
                        count["mismatches"] += differs
                        mismatch |= differs
                    else:
                        _require(value["accepted"] is None and value["roundtrip"] is None, "input_invalid")
                        if outcome == "UNENCODABLE":
                            _require(not encoding["complete"] and report["synthetic_callback"], "input_invalid")
                            prefix = value["prefix_outcome"]
                            _require(type(prefix) is str and prefix in ("UNRUN", "MASK_COMPUTED", "PREFIX_REJECTED", "FAILED"), "input_invalid")
                            _require(integer(value["next_allowed_count"], report["vocab_size"]) if prefix == "MASK_COMPUTED"
                                     else value["next_allowed_count"] is None, "input_invalid")
                            _require((value["reason"] != "none") == (prefix == "FAILED"), "input_invalid")
                            _require((row["compile"][name] == "COMPILED") == (prefix != "UNRUN"), "input_invalid")
                            if prefix == "MASK_COMPUTED":
                                _require(value["checked_tokens"] == encoding["tokens"], "input_invalid")
                            elif prefix == "PREFIX_REJECTED":
                                _require(value["checked_tokens"] < encoding["tokens"], "input_invalid")
                            elif prefix == "UNRUN":
                                _require(value["checked_tokens"] == 0, "input_invalid")
                            count["unencodable"] += 1
                            count["runtime_failures"] += prefix == "FAILED"
                            failed |= prefix == "FAILED"
                            mismatch = True
                        elif outcome == "COMPILE_REFUSED":
                            _require(row["compile"][name] == "REFUSED" and value["reason"] == "compile_refused" and value["checked_tokens"] == 0, "input_invalid")
                        elif outcome == "FAILED":
                            _require(value["reason"] != "none", "input_invalid")
                            count["runtime_failures"] += 1
                            failed = True
                        else:
                            _require(outcome == "UNRUN" and value["reason"] == "none" and value["checked_tokens"] == 0
                                     and row["compile"][name] in ("UNRUN", "FAILED"), "input_invalid")
                            unrun = True
                if len(names) == 2 and item[names[0]] != item[names[1]]:
                    disagreements += 1
                    if first is None:
                        rejected = [item[name]["checked_tokens"] for name in names if item[name]["outcome"] == "TOKEN_MASK"]
                        first = {"case": case_index, "sample": index, "positive": expected,
                                 "token": min(rejected) if rejected else None}
        expected_status = "failed" if failed or unrun else "mismatch" if mismatch else "passed"
        _require(report["status"] == expected_status and (report["reason"] == "none") == (expected_status != "failed"), "input_invalid")
        actual_first = report["first_divergence"]
        if actual_first is not None:
            _require(type(actual_first) is dict and set(actual_first) == {"case", "sample", "positive", "token"}
                     and integer(actual_first["case"], _oracle.MAX_CASES) and integer(actual_first["sample"], _oracle.MAX_SAMPLES)
                     and type(actual_first["positive"]) is bool
                     and (actual_first["token"] is None or integer(actual_first["token"], _oracle.MAX_TEXT)), "input_invalid")
        _require(actual_first == first, "input_invalid")
        for key, expected in (("sample_count", sample_count), ("positive_count", positive_count),
                              ("negative_count", negative_count), ("mode_disagreements", disagreements)):
            _require(type(report[key]) is int and report[key] == expected, "input_invalid")
        for name in names:
            _require(type(report["modes"][name]) is dict and set(report["modes"][name]) == set(stats[name])
                     and all(type(report["modes"][name][key]) is int and report["modes"][name][key] == value
                             for key, value in stats[name].items()), "input_invalid")
        return len(_encoded(report)) <= _oracle.MAX_REPORT
    except BaseException:
        return False
