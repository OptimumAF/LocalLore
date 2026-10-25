"""Original fake-module controls; no native module, tokenizer or model is loaded.

Copyright 2026 LocalLore contributors. SPDX-License-Identifier: Apache-2.0
"""
import copy
import hashlib
import importlib.util
import json
from pathlib import Path
import re
import unittest

from scripts.tests.test_litert_tokenizer_compare import FakeModule

PATH = Path(__file__).resolve().parents[2] / "benchmarks/litert_json_escape_probe.py"
SPEC = importlib.util.spec_from_file_location("escape_probe_under_test", PATH)
p = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(p)
PRIVATE = "PRIVATE-ESCAPE-PROBE-CANARY"
GOOD = '"a b"'
ESCAPED = r'"a\u0020b"'
TOKENS = tuple(bytes((value,)) for value in range(128)) + (b"<eos>",)


def fixtures(samples=None, pattern=r'\A(?:(?:"a b"))\z'):
    value = {"version": 1, "scope": p.compare._oracle.SCOPE, "cases": [{"id": "original",
        "schema_json": '{"const":"a b","type":"string"}',
        "positives": [{"id": "positive", "json": GOOD}],
        "negatives": [{"id": "wrong", "json": '"a!b"'}, {"id": "incomplete", "json": '"a'}]}], "refusals": []}
    if samples is not None:
        value["cases"][0]["negatives"] = [{"id": "negative-" + str(i), "json": text} for i, text in enumerate(samples)]
    raw = json.dumps(value, ensure_ascii=False, indent=2).encode()
    sidecar = {"version": 1, "scope": "locallore_finite_regex_corpus_v1",
               "source_corpus_sha256": hashlib.sha256(raw).hexdigest(), "cases": [{"index": 0,
               "schema_sha256": hashlib.sha256(value["cases"][0]["schema_json"].encode()).hexdigest(), "regex": pattern}]}
    return raw, json.dumps(sidecar, indent=2).encode()


class Module(FakeModule):
    def __init__(self, fault=None, tokens=TOKENS):
        super().__init__(fault, tokens)
        self.eos = len(tokens) - 1
        self.allowed = (GOOD.encode(),)
        self.larks, self.validation_grammars = [], []
        owner = self

        def regex(pattern):
            owner.patterns.append(pattern)
            owner.allowed = (GOOD.encode(), ESCAPED.encode()) if r"(?: |\\u0020)" in pattern else (GOOD.encode(),)
            value = {"grammars": [{"name": "regex", "json_schema": None, "lark_grammar": "start: /" + pattern + "/"}], "max_tokens": None}
            if fault == "bad-generated-grammar": value["no_forcing"] = True
            return json.dumps(value)

        def lark(text):
            owner.larks.append(text)
            return PRIVATE if fault == "bad-lark-return" else text

        original_validate = self.LLMatcher.validate_grammar
        def validate(grammar, *args, **kwargs):
            owner.validation_grammars.append(grammar)
            return original_validate(grammar, *args, **kwargs)

        self.LLMatcher.grammar_from_regex = staticmethod(regex)
        self.LLMatcher.grammar_from_lark = staticmethod(lark)
        self.LLMatcher.validate_grammar = staticmethod(validate)


class EscapeTests(unittest.TestCase):
    def run_probe(self, *, representation="ORIGINAL", pattern_mode="ORIGINAL", forcing="DEFAULT", module=None, raw=None, sidecar=None):
        if raw is None: raw, sidecar = fixtures()
        module = module or Module()
        result = p.run_escape_probe(module, module.tokens, module.eos, raw, sidecar, representation, pattern_mode, forcing)
        if "comparison" in result:
            self.assertTrue(p.validate_report(result, raw, sidecar, representation, pattern_mode, forcing))
        return result, module

    def test_lexical_change_preserves_structure_types_and_existing_backslash_u(self):
        original = ' { "a b" : ["x y", "\\\\u0020 z", 1, 1.0, true, null] } '
        changed, status, equivalence = p.space_escapes(original)
        self.assertEqual(changed, ' { "a\\u0020b" : ["x\\u0020y", "\\\\u0020\\u0020z", 1, 1.0, true, null] } ')
        self.assertEqual(status, "SPACE_ESCAPED")
        self.assertEqual(equivalence, "DECODED_EQUAL")
        self.assertEqual(p._typed(json.loads(changed)), p._typed(json.loads(original)))

    def test_escaped_quotes_slashes_unicode_pairs_and_empty_strings(self):
        for original in ('"x\\\" y"', '"x\\\\ y"', '"\\ud83d\\ude00 y"', '""', '"雪 y"'):
            with self.subTest(original=original):
                transformed, status, equivalence = p.space_escapes(original)
                self.assertIn(status, ("SPACE_ESCAPED", "UNCHANGED"))
                self.assertEqual(equivalence, "DECODED_EQUAL")
                self.assertEqual(json.loads(transformed), json.loads(original))

    def test_malformed_duplicate_nonfinite_surrogate_negatives_remain_identical(self):
        bad = ['"a ', '{"x":1,"x":2}', '{"x":1,"\\u0078":2}', 'NaN', 'Infinity', '1e999', '"\\ud800"', '"bad\\q space"']
        raw, sidecar = fixtures(bad)
        report, _ = self.run_probe(representation="SPACE_ESCAPES", raw=raw, sidecar=sidecar)
        self.assertEqual(report["comparison"]["sample_count"], len(bad) + 1)
        self.assertEqual(report["representation_counts"]["NOT_APPLICABLE"], len(bad))
        for original, row, result in zip(bad, report["correspondence"][1:], report["comparison"]["cases"][0]["samples"][1:]):
            self.assertEqual(row, [p.digest(original.encode()), len(original.encode()), "NOT_APPLICABLE", "IDENTICAL_BYTES"])
            self.assertEqual(result["sha256"], row[0])
        baseline, _ = self.run_probe(raw=raw, sidecar=sidecar)
        self.assertEqual(baseline["representation_counts"]["NOT_APPLICABLE"], len(bad))

    def test_representation_expansion_over_existing_cap_is_not_applicable(self):
        original = '"' + ' ' * 4000 + '"'
        self.assertEqual(p.space_escapes(original), (original, "NOT_APPLICABLE", "IDENTICAL_BYTES"))

    def test_space_alternatives_preserve_original_language_and_add_exact_json_escape(self):
        original = r'\A(?:(?:"a b"|"x\\\\u0020 y"))\z'
        changed = p.space_alternatives(original)
        self.assertEqual(changed, r'\A(?:(?:"a(?: |\\u0020)b"|"x\\\\u0020(?: |\\u0020)y"))\z')
        python_regex = changed.replace(r"\z", r"\Z")
        for valid in (GOOD, ESCAPED, r'"x\\u0020 y"', r'"x\\u0020\u0020y"'):
            with self.subTest(valid=valid):
                self.assertIsNotNone(re.fullmatch(python_regex, valid))
        self.assertIsNone(re.fullmatch(python_regex, '"ab"'))

    def test_pattern_contract_rejects_structural_spaces_and_arbitrary_regex(self):
        for pattern in (r'\A(?: "a b")\z', r'\A(?:"a b" )\z', r'\A(?:"a b"| x)\z',
                        r'\A(?:"a b".*)\z', r'\A(?:[ a])\z', r'\A(?:(?i:"a b"))\z',
                        r'\A(?:"a\ b")\z', r'\A(?:"a b)\z', r'\A(?:"a b"))\z'):
            with self.subTest(pattern=pattern), self.assertRaises(p.Refused):
                p.space_alternatives(pattern)

    def test_pattern_contract_checks_all_alternative_paths_and_growth_limits(self):
        for pattern in (r'\A(?:(?:"a|"b") space)\z',
                        r'\A(?:"' + " " * 3000 + r'")\z',
                        r'\A(?:' + "(?:" * 65 + '"a b"' + ")" * 65 + r')\z'):
            with self.subTest(length=len(pattern)), self.assertRaises(p.Refused):
                p.space_alternatives(pattern)

    def test_every_original_row_is_retained_across_all_eight_controls(self):
        raw, sidecar = fixtures()
        frozen = bytes(raw), bytes(sidecar)
        for representation in p.REPRESENTATIONS:
            for pattern in p.PATTERNS:
                for forcing in p.FORCING:
                    report, module = self.run_probe(raw=raw, sidecar=sidecar, representation=representation, pattern_mode=pattern, forcing=forcing)
                    self.assertEqual(report["comparison"]["sample_count"], 3)
                    self.assertEqual(report["source_corpus_sha256"], p.digest(raw))
                    self.assertEqual(report["regex_sidecar_sha256"], p.digest(sidecar))
                    self.assertEqual(len(report["correspondence"]), 3)
                    self.assertEqual(len(report["grammars"]), 1)
                    self.assertEqual(bool(module.larks), forcing == "DISABLED")
        self.assertEqual((raw, sidecar), frozen)

    def test_representation_does_not_replace_baseline_or_change_schema(self):
        baseline, _ = self.run_probe()
        escaped, _ = self.run_probe(representation="SPACE_ESCAPES")
        alternative, _ = self.run_probe(representation="SPACE_ESCAPES", pattern_mode="SPACE_ALTERNATIVES")
        self.assertEqual(baseline["comparison"]["status"], "passed")
        self.assertFalse(escaped["comparison"]["cases"][0]["samples"][0]["raw_piece"]["accepted"])
        self.assertTrue(alternative["comparison"]["cases"][0]["samples"][0]["raw_piece"]["accepted"])
        self.assertEqual(baseline["comparison"]["cases"][0]["schema_sha256"], alternative["comparison"]["cases"][0]["schema_sha256"])
        self.assertEqual(baseline["correspondence"][0][0], alternative["correspondence"][0][0])
        self.assertFalse(alternative["comparison"]["sdk_equivalent"])

    def test_disabled_forcing_uses_only_generated_public_lark_and_directive(self):
        report, module = self.run_probe(forcing="DISABLED")
        self.assertTrue(module.larks[0].startswith('%llguidance {"no_forcing":true}\nstart: /'))
        self.assertEqual(module.validation_grammars, module.larks)
        self.assertEqual(report["grammars"], [p.digest(module.larks[0].encode())])
        for fault in ("bad-generated-grammar", "bad-lark-return"):
            bad, module = self.run_probe(forcing="DISABLED", module=Module(fault))
            self.assertEqual(bad["status"], "failed")
            self.assertEqual(bad["comparison"]["cases"][0]["compile"]["raw_piece"], "FAILED")
            self.assertNotIn(PRIVATE, json.dumps(bad))

    def test_disabled_forcing_refuses_changed_generated_shape_before_public_lark_call(self):
        original = {"grammars": [{"name": "regex", "json_schema": None, "lark_grammar": 'start: /"a b"/'}], "max_tokens": None}
        for mutation in (lambda v: v.update(max_tokens=1), lambda v: v["grammars"].append(copy.deepcopy(v["grammars"][0])),
                         lambda v: v["grammars"][0].update(name="json_schema"),
                         lambda v: v["grammars"][0].update(json_schema={"const": PRIVATE}),
                         lambda v: v["grammars"][0].update(lark_grammar='start: /x/\n%ignore /./'),
                         lambda v: v["grammars"][0].update(no_forcing=True)):
            value = copy.deepcopy(original); mutation(value)
            module = Module()
            module.LLMatcher.grammar_from_regex = staticmethod(lambda pattern: json.dumps(value))
            report, _ = self.run_probe(module=module, forcing="DISABLED")
            self.assertEqual(report["status"], "failed")
            self.assertEqual(module.larks, [])
            self.assertEqual(report["comparison"]["sample_count"], 3)
            self.assertNotIn(PRIVATE, json.dumps(report))

    def test_native_failures_remain_closed_and_never_credit_negatives(self):
        for fault in ("mask-error", "wrong-mask", "compile-refuse", "init-throw"):
            report, _ = self.run_probe(module=Module(fault))
            self.assertEqual(report["status"], "failed")
            self.assertEqual(report["comparison"]["sample_count"], 3)
            self.assertNotIn(PRIVATE, json.dumps(report))

    def test_sidecar_hash_order_schema_and_unknown_keys_refuse_before_native(self):
        raw, sidecar = fixtures()
        for mutation in (lambda v: v.update(source_corpus_sha256="0" * 64), lambda v: v.update(private=PRIVATE),
                         lambda v: v["cases"][0].update(index=True), lambda v: v["cases"][0].update(schema_sha256="0" * 64)):
            value = json.loads(sidecar); mutation(value); module = Module()
            report, _ = self.run_probe(raw=raw, sidecar=json.dumps(value).encode(), module=module)
            self.assertEqual(report["reason"], "input_invalid")
            self.assertEqual(module.events, [])
        for kwargs in ({"representation": PRIVATE}, {"pattern_mode": True}, {"forcing": "no_forcing"}):
            report, module = self.run_probe(**kwargs)
            self.assertEqual(report["reason"], "input_invalid")
            self.assertEqual(module.events, [])

    def test_maximum_original_inventory_stays_within_unchanged_report_cap(self):
        raw, sidecar = fixtures(['"a!b"'] * 255)
        report, _ = self.run_probe(raw=raw, sidecar=sidecar, representation="SPACE_ESCAPES", pattern_mode="SPACE_ALTERNATIVES", forcing="DISABLED")
        self.assertEqual(report["comparison"]["sample_count"], 256)
        self.assertLessEqual(len(p.encoded(report)), 131072)

    def test_thirteen_pattern_215_row_original_shape_fits_all_eight_controls(self):
        source_raw, sidecar_raw = fixtures()
        source, sidecar = json.loads(source_raw), json.loads(sidecar_raw)
        template = source["cases"][0]
        source["cases"], sidecar["cases"] = [], []
        for index in range(13):
            case = copy.deepcopy(template)
            case["id"] = "case-" + str(index)
            case["schema_json"] = json.dumps({"const": "a b", "type": "string", "title": "case-" + str(index)})
            case["negatives"] = [{"id": "negative-" + str(i), "json": '"a!b"'} for i in range(16 if index < 7 else 15)]
            source["cases"].append(case)
            sidecar["cases"].append({"index": index, "schema_sha256": p.digest(case["schema_json"].encode()), "regex": r'\A(?:(?:"a b"))\z'})
        raw = json.dumps(source).encode()
        sidecar["source_corpus_sha256"] = p.digest(raw)
        sidecar_raw = json.dumps(sidecar).encode()
        for representation in p.REPRESENTATIONS:
            for pattern_mode in p.PATTERNS:
                for forcing in p.FORCING:
                    report, _ = self.run_probe(raw=raw, sidecar=sidecar_raw, representation=representation, pattern_mode=pattern_mode, forcing=forcing)
                    self.assertEqual(report["comparison"]["sample_count"], 215)
                    self.assertEqual(len(report["patterns"]), 13)
                    self.assertEqual(len(report["grammars"]), 13)
                    self.assertLessEqual(len(p.encoded(report)), 131072)

    def test_report_does_not_echo_original_sample_or_exception_canaries(self):
        raw, sidecar = fixtures([json.dumps(PRIVATE)])
        report, _ = self.run_probe(raw=raw, sidecar=sidecar)
        self.assertNotIn(PRIVATE, json.dumps(report))

    def test_strict_report_validator_refuses_missing_rows_forged_counts_and_private_fields(self):
        raw, sidecar = fixtures()
        report, _ = self.run_probe(raw=raw, sidecar=sidecar, representation="SPACE_ESCAPES")
        for mutation in (lambda v: v.update(private=PRIVATE), lambda v: v["correspondence"].pop(),
                         lambda v: v["correspondence"][0].__setitem__(1, True),
                         lambda v: v["correspondence"][0].__setitem__(0, "0" * 64),
                         lambda v: v["representation_counts"].update(SPACE_ESCAPED=True),
                         lambda v: v["patterns"][0].__setitem__(1, "0" * 64),
                         lambda v: v.update(grammars=[]), lambda v: v.update(status="passed"),
                         lambda v: v["comparison"]["cases"][0]["samples"].pop()):
            changed = copy.deepcopy(report); mutation(changed)
            self.assertFalse(p.validate_report(changed, raw, sidecar))
        self.assertFalse(p.validate_report(report, raw, sidecar, "ORIGINAL"))
        self.assertFalse(p.validate_report({"version": 1, "scope": p.SCOPE, "status": "passed"}, raw, sidecar))


if __name__ == "__main__":
    unittest.main()
