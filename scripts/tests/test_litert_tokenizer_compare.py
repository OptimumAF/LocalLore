"""Original fake-module controls; never load a native tokenizer or model.

Copyright 2026 LocalLore contributors. SPDX-License-Identifier: Apache-2.0
"""
import copy
import hashlib
import importlib.util
import json
from pathlib import Path
import unittest


PATH = Path(__file__).resolve().parents[2] / "benchmarks/litert_tokenizer_compare.py"
SPEC = importlib.util.spec_from_file_location("tokenizer_compare_under_test", PATH)
c = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(c)
PRIVATE = "PRIVATE-TOKENIZER-COMPARE-CANARY"
GOOD = '"a b"'
TOKENS = (b"<eos>", b'"', b"a", "\u2581".encode(), b"b", b"!", b"{", b"}")
HF_JSON = json.dumps({"model": {"type": "BPE", "vocab": {piece.decode(): index for index, piece in enumerate(TOKENS)}},
                      "added_tokens": []}, separators=(",", ":"))


def corpus():
    return {"version": 1, "scope": c._oracle.SCOPE, "cases": [{"id": "original-case",
            "schema_json": '{ "const":"a b", "type":"string" }',
            "positives": [{"id": "original-positive", "json": GOOD}],
            "negatives": [{"id": "illegal", "json": '"a!b"'}, {"id": "incomplete", "json": '"a'}]}],
            "refusals": [{"id": "refusal", "error": "TooLarge", "provider_calls": 0, "canon_unchanged": True}]}


class FakeTokenizer:
    def __init__(self, owner, wrapper=None):
        self.owner, self.wrapper = owner, wrapper
        self.mode = "semantic_hf" if wrapper is None else "raw_piece"
        self.vocab_size = len(owner.tokens)
        self.eos_token = owner.eos

    def tokenize_str(self, text):
        if self.owner.bad_ids is not None:
            return self.owner.bad_ids
        table = {piece.decode(): index for index, piece in enumerate(self.owner.tokens)}
        table[" "] = table.get("\u2581", table.get(" ", -1))
        return [table[char] for char in text]

    def piece(self, token):
        raw = self.owner.tokens[token]
        return b" " if self.mode == "semantic_hf" and raw == "\u2581".encode() else raw

    def decode_bytes(self, ids):
        if self.owner.fault == "decode-throw":
            raise ValueError(PRIVATE)
        return b"".join(self.piece(token) for token in ids)


class FakeMatcher:
    def __init__(self, owner, tokenizer):
        self.owner, self.tokenizer = owner, tokenizer
        self.prefix, self.error, self.stopped, self.ready = b"", False, False, False
        self.allowed = owner.allowed

    def is_error(self):
        return self.error or self.owner.fault == "initial-error"

    def stop_reason(self):
        return "LexerTooComplex" if self.owner.fault == "unsafe-stop" else "EndOfSentence" if self.stopped else "NotStopped"

    def is_stopped(self):
        return self.stopped and self.owner.fault != "unstopped-eos"

    def compute_bitmask(self):
        self.owner.events.append(("mask", self.tokenizer.mode, len(self.prefix)))
        if self.owner.fault == "throw-mask":
            raise RuntimeError(PRIVATE)
        if self.owner.fault == "wrong-mask":
            return b""
        # Match the pinned Python API's complete SimpleVob allocation, including
        # its extra capacity word at vocabulary boundaries.
        vocab = len(self.owner.tokens)
        mask = bytearray((((vocab + 1) // 32) + 1) * 4)
        for token in range(len(self.owner.tokens)):
            allowed = any(text == self.prefix for text in self.allowed) if token == self.owner.eos else any(
                text.startswith(self.prefix + self.tokenizer.piece(token)) for text in self.allowed)
            if allowed:
                mask[token // 8] |= 1 << (token % 8)
        if self.owner.fault in ("eos-mismatch", "padding-eos-mismatch"):
            mask[self.owner.eos // 8] &= ~(1 << (self.owner.eos % 8))
        if self.owner.fault in ("padding-ones", "padding-only", "padding-error", "padding-eos-mismatch"):
            if self.owner.fault == "padding-only":
                mask[:] = bytes(len(mask))
            for token in range(vocab, len(mask) * 8):
                mask[token // 8] |= 1 << (token % 8)
        self.ready = True
        if self.owner.fault in ("mask-error", "padding-error"):
            self.error = True
        return bytes(mask)

    def consume_token(self, token):
        if not self.ready:
            raise AssertionError("mask must precede consume")
        self.owner.events.append(("consume", self.tokenizer.mode, token))
        self.ready = False
        if self.owner.fault == "false-consume" or token == self.owner.eos and self.owner.fault == "false-eos":
            return False
        if token == self.owner.eos:
            self.stopped = True
        else:
            self.prefix += self.tokenizer.piece(token)
        if self.owner.fault == "consume-error":
            self.error = True
        return True

    def is_accepting(self):
        return self.prefix in self.allowed


class FakeModule:
    def __init__(self, fault=None, tokens=TOKENS):
        self.fault, self.tokens = fault, tokens
        self.eos = 0
        self.allowed = (GOOD.encode(),)
        self.events, self.schemas, self.patterns, self.wrappers = [], [], [], []
        self.bad_ids = None
        owner = self

        class Matcher:
            def __new__(cls, tokenizer, grammar, **kwargs):
                owner.events.append(("matcher", tokenizer.mode))
                return FakeMatcher(owner, tokenizer)

            @staticmethod
            def grammar_from_json_schema(value):
                owner.schemas.append(value)
                return "JSON:" + value

            @staticmethod
            def grammar_from_regex(value):
                owner.patterns.append(value)
                return "REGEX:" + value

            @staticmethod
            def validate_grammar(grammar, tokenizer, **kwargs):
                if owner.fault == "compile-throw":
                    raise RuntimeError(PRIVATE)
                return PRIVATE if owner.fault == "compile-refuse" else ""

        self.LLMatcher = Matcher

    def LLParserLimits(self, **kwargs):
        self.events.append(("limits", kwargs))
        return kwargs

    def LLTokenizer(self, value, **kwargs):
        self.events.append(("tokenizer", type(value).__name__, kwargs))
        if self.fault == "init-throw":
            raise RuntimeError(PRIVATE)
        wrapper = None if type(value) is str else value
        if wrapper is not None:
            self.wrappers.append(wrapper)
        return FakeTokenizer(self, wrapper)


class CompareTests(unittest.TestCase):
    def run_compare(self, module=None, value=None, *, raw=TOKENS, tokenizer_json=HF_JSON):
        actual = value or corpus()
        report = c.compare_tokenizers(module or FakeModule(), tokenizer_json, raw, 0, actual)
        if "cases" in report:
            self.assertTrue(c.validate_report(report, actual))
        return report

    def test_exact_pinned_storage_sizes_and_all_other_lengths_refused(self):
        class StaticMask:
            def is_error(self): return False
            def stop_reason(self): return "NotStopped"
            def compute_bitmask(self): return self.mask

        # Literal expectations independently pin both V % 32 == 0 and == 31.
        sizes = {1: 4, 30: 4, 31: 8, 32: 8, 33: 8, 62: 8, 63: 12,
                 64: 12, 65: 12, 95: 16, 96: 16, 97: 16, 262144: 32772}
        matcher = StaticMask()
        for vocab, expected in sizes.items():
            with self.subTest(vocab=vocab):
                matcher.mask = bytes(expected)
                self.assertEqual(c._mask(matcher, vocab, lambda: None), matcher.mask)
                packed = ((vocab + 31) // 32) * 4
                wrong = {0, expected - 4, expected - 1, expected + 1, expected + 4, packed} - {expected}
                for size in wrong:
                    matcher.mask = bytes(size)
                    with self.assertRaises(c.CompareRefused) as failure:
                        c._mask(matcher, vocab, lambda: None)
                    self.assertEqual(failure.exception.reason, "matcher_mask")
                matcher.mask = bytearray(expected)
                with self.assertRaises(c.CompareRefused):
                    c._mask(matcher, vocab, lambda: None)

    def test_padded_vocabulary_boundaries_keep_complete_original_coverage(self):
        base = tuple(b" " if piece == "\u2581".encode() else piece for piece in TOKENS)
        for vocab in (31, 32, 63, 64):
            with self.subTest(vocab=vocab):
                raw = base + tuple(("extra-" + str(i)).encode() for i in range(vocab - len(base)))
                report = self.run_compare(FakeModule("padding-ones", tokens=raw), raw=raw, tokenizer_json=None)
                self.assertEqual(report["status"], "passed")
                self.assertEqual(report["sample_count"], 3)
                self.assertEqual(report["modes"]["raw_piece"]["checked"], 3)

    def test_padding_cannot_authorize_real_tokens_or_inflate_prefix_counts(self):
        report = self.run_compare(FakeModule("padding-ones"), tokenizer_json=None)
        positive = report["cases"][0]["samples"][0]["raw_piece"]
        self.assertEqual(positive["prefix_outcome"], "MASK_COMPUTED")
        self.assertEqual(positive["next_allowed_count"], 0)
        self.assertIsNone(positive["accepted"])
        module = FakeModule("padding-only")
        report = self.run_compare(module)
        for sample in report["cases"][0]["samples"]:
            for name in report["modes"]:
                self.assertEqual(sample[name]["outcome"], "TOKEN_MASK")
                self.assertEqual(sample[name]["checked_tokens"], 0)
                self.assertFalse(sample[name]["accepted"])
        self.assertFalse(any(event[0] == "consume" for event in module.events))

    def test_padding_cannot_authorize_out_of_vocab_ids_or_eos_or_hide_sticky_error(self):
        for ids in ([len(TOKENS)], [len(TOKENS) + 1], [31]):
            with self.subTest(ids=ids):
                module = FakeModule("padding-ones"); module.bad_ids = ids
                report = self.run_compare(module)
                self.assertEqual(report["reason"], "token_ids")
                self.assertEqual(report["modes"]["semantic_hf"]["checked"], 0)
        for eos in (len(TOKENS), 31):
            module = FakeModule("padding-ones"); module.eos = eos
            report = c.compare_tokenizers(module, None, TOKENS, eos, corpus())
            self.assertEqual(report["reason"], "input_invalid")
            self.assertEqual(module.events, [])
        base = tuple(b" " if piece == "\u2581".encode() else piece for piece in TOKENS)
        raw = base + tuple(("extra-" + str(i)).encode() for i in range(32 - len(base)))
        for fault in ("padding-error", "padding-eos-mismatch"):
            with self.subTest(fault=fault):
                report = self.run_compare(FakeModule(fault, tokens=raw), raw=raw, tokenizer_json=None)
                self.assertEqual(report["status"], "failed")
                self.assertEqual(report["reason"], "matcher_state")
                positive = report["cases"][0]["samples"][0]["raw_piece"]
                self.assertEqual(positive["outcome"], "FAILED")
                self.assertIsNone(positive["accepted"])
                if fault == "padding-error":
                    self.assertEqual(report["modes"]["raw_piece"]["checked"], 0)

    def test_inert_fake_control_retains_every_original_hash_and_disagreement(self):
        original = corpus()
        frozen = copy.deepcopy(original)
        module = FakeModule()
        report = self.run_compare(module, original)
        self.assertEqual(original, frozen)
        self.assertEqual(report["sample_count"], 3)
        self.assertEqual((report["positive_count"], report["negative_count"], report["refusals"]), (1, 2, 1))
        self.assertEqual(report["status"], "mismatch")
        self.assertFalse(report["sdk_equivalent"])
        self.assertFalse(report["callback_equivalent"])
        row = report["cases"][0]
        self.assertEqual(row["schema_sha256"], hashlib.sha256(original["cases"][0]["schema_json"].encode()).hexdigest())
        samples = original["cases"][0]["positives"] + original["cases"][0]["negatives"]
        for source, sample in zip(samples, row["samples"]):
            self.assertEqual(sample["sha256"], hashlib.sha256(source["json"].encode()).hexdigest())
        positive = row["samples"][0]
        self.assertTrue(positive["semantic_hf"]["accepted"])
        self.assertEqual(positive["raw_piece"]["outcome"], "TOKEN_MASK")
        self.assertEqual(positive["raw_piece"]["checked_tokens"], 2)
        self.assertFalse(positive["raw_piece"]["roundtrip"])
        self.assertEqual(report["first_divergence"]["token"], 2)
        self.assertGreater(report["modes"]["raw_piece"]["non_roundtrip"], 0)

    def test_raw_wrapper_properties_and_callback_do_not_invent_specials_or_encoder(self):
        module = FakeModule()
        self.run_compare(module)
        wrapper = module.wrappers[0]
        self.assertTrue(wrapper.is_tokenizer_wrapper)
        self.assertEqual(tuple(wrapper.tokens), TOKENS)
        self.assertEqual(wrapper.eos_token_id, 0)
        self.assertIsNone(wrapper.bos_token_id)
        self.assertEqual(wrapper.special_token_ids, [])
        self.assertEqual(wrapper(GOOD), [1, 2, 3, 4, 1])

    def test_callback_exception_returns_empty_and_sticky_failure_prevents_credit(self):
        class ConstructorCallback(FakeModule):
            def LLTokenizer(self, value, **kwargs):
                if type(value) is not str:
                    self.callback_result = value(PRIVATE)
                return super().LLTokenizer(value, **kwargs)

        module = ConstructorCallback()
        report = self.run_compare(module)
        self.assertEqual(module.callback_result, [])
        self.assertEqual(report["status"], "failed")
        self.assertEqual(report["reason"], "tokenizer_runtime")
        self.assertEqual(report["sample_count"], 3)
        self.assertNotIn(PRIVATE, json.dumps(report))

    def test_none_json_retains_unencodable_positive_and_negative_without_credit(self):
        module = FakeModule()
        report = self.run_compare(module, tokenizer_json=None)
        self.assertEqual(set(report["modes"]), {"raw_piece"})
        self.assertTrue(report["synthetic_callback"])
        self.assertFalse(report["sp_encoder"])
        sample = report["cases"][0]["samples"][0]
        self.assertEqual(sample["encoding"], {"tokens": 2, "bytes": 2, "complete": False})
        self.assertEqual(sample["raw_piece"]["outcome"], "UNENCODABLE")
        self.assertEqual(sample["raw_piece"]["prefix_outcome"], "MASK_COMPUTED")
        self.assertEqual(sample["raw_piece"]["next_allowed_count"], 0)
        self.assertEqual(sample["raw_piece"]["checked_tokens"], 2)
        self.assertIsNone(sample["raw_piece"]["accepted"])
        self.assertEqual(module.wrappers[0](GOOD), [])
        value = corpus(); value["cases"][0]["negatives"][0]["json"] = '"a !b"'
        report = self.run_compare(FakeModule(), value, tokenizer_json=None)
        self.assertIsNone(report["cases"][0]["samples"][1]["raw_piece"]["accepted"])
        self.assertEqual(report["modes"]["raw_piece"]["unencodable"], 2)

    def test_greedy_longest_match_and_first_utf8_byte_gap_are_exact(self):
        greedy = c._Greedy((b"a", b"ab", b"b", b"", "\u96ea".encode()))
        self.assertEqual(greedy.encode(b"ababa!"), ([1, 1, 0], 5))
        self.assertEqual(greedy.encode("\u96ea!".encode()), ([4], 3))
        self.assertEqual(greedy.encode(b""), ([], 0))

    def test_raw_only_encodable_corpus_can_pass_without_claiming_sp_equivalence(self):
        raw = tuple(b" " if piece == "\u2581".encode() else piece for piece in TOKENS)
        report = self.run_compare(FakeModule(tokens=raw), raw=raw, tokenizer_json=None)
        self.assertEqual(report["status"], "passed")
        self.assertEqual(report["modes"]["raw_piece"]["checked"], 3)
        self.assertEqual(report["modes"]["raw_piece"]["mismatches"], 0)
        self.assertFalse(report["sdk_equivalent"])
        self.assertFalse(report["sp_encoder"])

    def test_multibyte_input_uses_utf8_byte_counts_and_explicit_nonzero_eos(self):
        raw = (b'"', b"<eos>", "\u96ea".encode(), b"x")
        module = FakeModule(tokens=raw); module.eos = 1; module.allowed = ('"\u96ea"'.encode(),)
        value = corpus(); case = value["cases"][0]
        case["schema_json"] = '{"const":"\u96ea","type":"string"}'
        case["positives"][0]["json"] = '"\u96ea"'
        case["negatives"][0]["json"] = '"x"'
        case["negatives"][1]["json"] = '"'
        report = c.compare_tokenizers(module, None, raw, 1, value)
        self.assertTrue(c.validate_report(report, value))
        self.assertEqual(report["status"], "passed")
        self.assertEqual(report["eos"], 1)
        self.assertEqual(report["cases"][0]["samples"][0]["encoding"], {"tokens": 3, "bytes": 5, "complete": True})

    def test_exact_finite_regex_uses_existing_pattern_not_schema_regeneration(self):
        value = corpus(); pattern = r'\A(?:"a b")\z'
        value["cases"][0]["finite_regex"] = pattern
        module = FakeModule(); report = self.run_compare(module, value)
        self.assertEqual(module.patterns, [pattern, pattern])
        self.assertEqual(module.schemas, [])
        row = report["cases"][0]
        self.assertEqual(row["finite_regex_sha256"], hashlib.sha256(pattern.encode()).hexdigest())
        self.assertEqual(row["schema_sha256"], hashlib.sha256(value["cases"][0]["schema_json"].encode()).hexdigest())

    def test_native_compile_refusal_preserves_all_samples_without_negative_credit(self):
        report = self.run_compare(FakeModule("compile-refuse"))
        self.assertEqual(report["status"], "failed")
        self.assertEqual(report["reason"], "compile_refused")
        self.assertEqual(report["sample_count"], 3)
        self.assertEqual(report["cases"][0]["compile"], {"semantic_hf": "REFUSED", "raw_piece": "REFUSED"})
        for sample in report["cases"][0]["samples"]:
            self.assertEqual(sample["semantic_hf"]["outcome"], "COMPILE_REFUSED")
            self.assertIsNone(sample["semantic_hf"]["accepted"])
        self.assertNotIn(PRIVATE, json.dumps(report))

    def test_initialization_exception_keeps_sample_inventory(self):
        report = self.run_compare(FakeModule("init-throw"))
        self.assertEqual(report["status"], "failed")
        self.assertEqual(report["reason"], "tokenizer_init")
        self.assertEqual(report["sample_count"], 3)
        self.assertEqual(len(report["cases"][0]["samples"]), 3)
        self.assertNotIn(PRIVATE, json.dumps(report))

    def test_compile_runtime_failure_keeps_unrun_samples_and_exact_counts(self):
        report = self.run_compare(FakeModule("compile-throw"))
        self.assertEqual(report["status"], "failed")
        self.assertEqual(report["reason"], "compile_runtime")
        self.assertEqual(report["sample_count"], 3)
        self.assertEqual(report["modes"]["semantic_hf"]["runtime_failures"], 1)
        self.assertTrue(all(sample["semantic_hf"]["outcome"] == "UNRUN" for sample in report["cases"][0]["samples"]))
        self.assertNotIn(PRIVATE, json.dumps(report))

    def test_unencodable_prefix_native_failure_is_not_a_negative_pass(self):
        report = self.run_compare(FakeModule("throw-mask"), tokenizer_json=None)
        sample = report["cases"][0]["samples"][0]["raw_piece"]
        self.assertEqual(sample["outcome"], "UNENCODABLE")
        self.assertEqual(sample["prefix_outcome"], "FAILED")
        self.assertIsNone(sample["accepted"])
        self.assertEqual(report["status"], "failed")
        self.assertNotIn(PRIVATE, json.dumps(report))

    def test_malformed_token_ids_are_runtime_failures_including_boolean_and_empty(self):
        for ids in ([True], [-1], [len(TOKENS)], (), [], [0] * (c._oracle.MAX_TEXT + 1)):
            with self.subTest(kind=type(ids).__name__, size=len(ids)):
                module = FakeModule(); module.bad_ids = ids
                report = self.run_compare(module)
                self.assertEqual(report["status"], "failed")
                self.assertEqual(report["reason"], "token_ids")
                self.assertEqual(report["sample_count"], 3)
                self.assertEqual(report["modes"]["semantic_hf"]["checked"], 0)

    def test_sticky_errors_and_eos_inconsistencies_never_credit_a_negative(self):
        for fault in ("initial-error", "unsafe-stop", "mask-error", "consume-error", "wrong-mask",
                      "false-consume", "eos-mismatch", "false-eos", "unstopped-eos", "throw-mask"):
            with self.subTest(fault=fault):
                report = self.run_compare(FakeModule(fault))
                self.assertEqual(report["status"], "failed")
                self.assertGreater(report["modes"]["semantic_hf"]["runtime_failures"], 0)
                self.assertNotIn(PRIVATE, json.dumps(report))

    def test_full_acceptance_incomplete_and_unexpected_negative_acceptance_are_distinct(self):
        module = FakeModule()
        module.allowed += (b'"a!b"',)
        report = self.run_compare(module)
        samples = report["cases"][0]["samples"]
        self.assertEqual(samples[0]["semantic_hf"]["outcome"], "COMPLETE")
        self.assertTrue(samples[1]["semantic_hf"]["accepted"])
        self.assertEqual(samples[2]["semantic_hf"]["outcome"], "INCOMPLETE")
        self.assertGreater(report["modes"]["semantic_hf"]["mismatches"], 0)

    def test_invalid_inputs_refuse_before_calling_fake_module(self):
        for change in (lambda x: x.update(version=True),
                       lambda x: x["cases"][0].update(finite_regex=PRIVATE),
                       lambda x: x["cases"][0]["negatives"].clear(),
                       lambda x: x["refusals"][0].update(provider_calls=1)):
            value = corpus(); change(value)
            module = FakeModule(); report = self.run_compare(module, value)
            self.assertEqual(report["status"], "failed")
            self.assertEqual(module.events, [])
        for eos in (True, -1, len(TOKENS)):
            module = FakeModule()
            self.assertEqual(c.compare_tokenizers(module, None, TOKENS, eos, corpus())["status"], "failed")
            self.assertEqual(module.events, [])

    def test_maximum_sample_inventory_fits_existing_report_bound(self):
        value = corpus()
        value["cases"][0]["negatives"] = [{"id": "negative-" + str(index), "json": '"a!b"'} for index in range(255)]
        report = self.run_compare(value=value)
        self.assertEqual(report["sample_count"], 256)
        self.assertLessEqual(len(c._encoded(report)), c._oracle.MAX_REPORT)
        self.assertEqual(report["negative_count"], 255)

    def test_report_validator_refuses_forged_coverage_counts_types_and_private_fields(self):
        good = self.run_compare()
        changes = (
            lambda r: r.update(status="passed"),
            lambda r: r.update(sample_count=True),
            lambda r: r.update(positive_count=0),
            lambda r: r.update(corpus_json_sha256="0" * 64),
            lambda r: r["cases"][0]["samples"].pop(),
            lambda r: r["cases"][0]["samples"][0].update(sha256="0" * 64),
            lambda r: r["cases"][0]["samples"][0]["raw_piece"].update(reason=PRIVATE),
            lambda r: r["modes"]["raw_piece"].update(non_roundtrip=0),
            lambda r: r["first_divergence"].update(case=False),
            lambda r: r.update(private=PRIVATE),
        )
        for change in changes:
            value = copy.deepcopy(good); change(value)
            self.assertFalse(c.validate_report(value, corpus()))
        missing = {"version": 1, "scope": c.SCOPE, "status": "passed"}
        self.assertFalse(c.validate_report(missing, corpus()))

    def test_report_validator_never_relabels_unencodable_negative_as_rejection(self):
        report = self.run_compare(tokenizer_json=None)
        sample = report["cases"][0]["samples"][0]["raw_piece"]
        sample.update(accepted=False)
        self.assertFalse(c.validate_report(report, corpus()))


if __name__ == "__main__":
    unittest.main()
