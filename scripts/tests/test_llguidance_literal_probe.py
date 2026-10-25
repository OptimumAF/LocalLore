"""Pure reduction/API-seam checks. Never load the native compiler or a model.

Copyright 2026 LocalLore contributors. SPDX-License-Identifier: Apache-2.0
"""
import importlib.util
import json
import copy
import hashlib
from pathlib import Path
import re
import sys
import unittest
from unittest.mock import patch

BENCHMARKS = Path(__file__).resolve().parents[2] / "benchmarks"
# Bind the checker explicitly: scripts/ has another module with the same basename.
SPEC = importlib.util.spec_from_file_location("llguidance_oracle", BENCHMARKS / "llguidance_oracle.py")
checker = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(checker)
SPEC = importlib.util.spec_from_file_location("llguidance_literal_probe_test", BENCHMARKS / "llguidance_literal_probe.py")
p = importlib.util.module_from_spec(SPEC)
with patch.dict(sys.modules, {"llguidance_oracle": checker}):
    SPEC.loader.exec_module(p)
checker = p.oracle


class ReductionTests(unittest.TestCase):
    def test_reduction_is_deterministic_reproducible_and_deletion_minimal(self):
        seen = []
        def rejects(text):
            seen.append(text)
            return "bad" in text
        result = p.minimize("prefix bad suffix", rejects)
        self.assertEqual(result["status"], "deletion_minimal")
        self.assertEqual("".join("prefix bad suffix"[i] for i in result["indexes"]), "bad")
        self.assertEqual(len(seen), len(set(seen)))
        self.assertLessEqual(result["evaluations"], p.MAX_EVALUATIONS)
        self.assertEqual(result, p.minimize("prefix bad suffix", lambda s: "bad" in s))

    def test_budget_exit_is_explicit_and_preserves_known_counterexample(self):
        result = p.minimize("original", lambda s: s == "original", budget=1)
        self.assertEqual(result, {"status": "budget_exhausted", "indexes": list(range(8)), "evaluations": 1})

    def test_nonreproduction_never_makes_up_a_counterexample(self):
        result = p.minimize("ordinary", lambda s: False)
        self.assertEqual(result["status"], "not_reproduced")
        self.assertEqual(result["evaluations"], 1)

    def test_empty_literal_can_be_a_real_minimum(self):
        result = p.minimize("abc", lambda s: True)
        self.assertEqual(result["status"], "deletion_minimal")
        self.assertEqual(result["indexes"], [])

    def test_bad_predicate_and_bounds_are_failures(self):
        for text, budget in (("", 128), ("a" * 129, 128), ("ok", True), ("ok", 129), ("ok", 0)):
            with self.subTest(text=len(text), budget=budget), self.assertRaises(checker.OracleFailure):
                p.minimize(text, lambda s: True, budget)
        with self.assertRaises(checker.OracleFailure):
            p.minimize("text", lambda s: "PRIVATE_ERROR")

    def test_predicate_runtime_fault_is_not_a_counterexample(self):
        def fault(_):
            raise checker.OracleFailure("backend_runtime")
        with self.assertRaises(checker.OracleFailure) as error:
            p.minimize("text", fault)
        self.assertEqual(error.exception.reason, "backend_runtime")

    def test_literal_regex_and_schema_preserve_original_utf8_json(self):
        self.assertIn("\u96ea", p.ORIGINAL)
        self.assertIn("\n", p.ORIGINAL)
        for text in (p.ORIGINAL, '"\\[]{}()*+?.^$|', "", "\t\r"):
            data = p.encoded(text)
            self.assertEqual(json.loads(p.schema(text))["const"], text)
            self.assertIsNotNone(re.fullmatch(p.literal_regex(data), data))
            self.assertIsNone(re.fullmatch(p.literal_regex(data), data + "x"))

    def test_report_must_bind_every_path_to_original_and_reduction(self):
        text = p.ORIGINAL
        raw = text.encode()
        data = p.encoded(text).encode()
        truncated = p.encoded(raw[:(len(raw)-1)%31+1].decode()).encode()
        paths = [{"wrapper": label, "negative_rejected": True, "truncated_accepted": False,
                  "mask": {"accepted": True, "outcome": "COMPLETE", "checked_bytes": len(data)},
                  "validated_tokens": len(data)+1, "tokens_with_eos": len(data)+1,
                  "direct_consumed": True, "direct_error": False, "direct_complete": True}
                 for label in ("json_default", "lark_default", "lark_no_forcing", "regex_exact")]
        case = {"index": 0, "schema_sha256": hashlib.sha256(p.schema(text).encode()).hexdigest(),
                "sample_sha256": hashlib.sha256(data).hexdigest(), "sample_bytes": len(data),
                "truncated_sha256": hashlib.sha256(truncated).hexdigest(), "truncated_bytes": len(truncated), "paths": paths}
        report = {"version": 1, "scope": p.SCOPE, "native": True, "status": "observed",
                  "controls": {k: True for k in ("basic_compile", "valid_complete", "illegal_rejected", "incomplete_rejected", "unsupported_refused")},
                  "reduction": {"status": "not_reproduced", "indexes": list(range(len(text))), "evaluations": 1},
                  "cases": [case, {**copy.deepcopy(case), "index": 1}]}
        self.assertTrue(p.validate_report(report))  # Simulated wire, no native execution.
        self.assertFalse(p.validate_report({"native": True, "status": "observed"}))
        for key, bad in (("version", True), ("native", 1), ("cases", []), ("private", "PRIVATE")):
            value = copy.deepcopy(report)
            value[key] = bad
            self.assertFalse(p.validate_report(value))
        for change in ("hash", "duplicate-index", "bool-count", "path-shortcut", "unknown-path", "invalid-acceptance"):
            value = copy.deepcopy(report)
            if change == "hash":
                value["cases"][0]["sample_sha256"] = "0" * 64
            elif change == "duplicate-index":
                value["reduction"]["indexes"] = [1, 1]
            elif change == "bool-count":
                value["cases"][0]["paths"][0]["validated_tokens"] = True
            elif change == "path-shortcut":
                value["cases"][0]["paths"] = value["cases"][0]["paths"][:1]
            elif change == "unknown-path":
                value["cases"][0]["paths"][0]["wrapper"] = "unvalidated"
            else:
                value["cases"][0]["paths"][0]["mask"]["accepted"] = False
            self.assertFalse(p.validate_report(value))

    def test_regression_fixture_keeps_full_and_wrong_truncated_values_distinct(self):
        fixture = json.loads((BENCHMARKS.parent / "fixtures/llguidance_literal_regressions.json").read_bytes())
        checker.validate_corpus(json.dumps(fixture).encode())
        self.assertEqual(len(fixture["cases"]), 5)
        for case in fixture["cases"]:
            text = json.loads(case["schema_json"])["const"]
            self.assertEqual(json.loads(case["positives"][0]["json"]), text)
            self.assertNotEqual(json.loads(case["negatives"][0]["json"]), text)

    def test_native_import_is_not_needed_for_validation_or_argument_refusal(self):
        from contextlib import redirect_stdout
        import io
        output = io.StringIO()
        with patch.object(p.sys, "argv", ["probe", "--PRIVATE_ARGUMENT"]), \
                patch.object(p.oracle, "NativeBackend", side_effect=AssertionError("unexpected_native")), redirect_stdout(output):
            self.assertEqual(p.main(), 2)
        self.assertNotIn("PRIVATE", output.getvalue())
        self.assertEqual(json.loads(output.getvalue())["reason"], "arguments")

    def test_actual_pattern_artifact_is_closed_and_bound_to_all_schema_bytes(self):
        corpus_raw = (BENCHMARKS.parent / "fixtures/llguidance_literal_regressions.json").read_bytes()
        corpus = json.loads(corpus_raw)
        artifact = {"version": 1, "scope": "locallore_finite_regex_corpus_v1",
                    "source_corpus_sha256": hashlib.sha256(corpus_raw).hexdigest(), "cases": []}
        for index, case in enumerate(corpus["cases"]):
            artifact["cases"].append({"index": index, "schema_sha256": hashlib.sha256(case["schema_json"].encode()).hexdigest(),
                "regex": "\\A(?:" + p.literal_regex(case["positives"][0]["json"]) + ")\\z"})
        raw = json.dumps(artifact).encode()
        self.assertEqual(len(p.validate_pattern_corpus(raw, corpus_raw)), 5)
        for key, bad in (("version", True), ("scope", "wrong"), ("source_corpus_sha256", "0" * 64),
                         ("cases", []), ("private", "PRIVATE")):
            value = copy.deepcopy(artifact); value[key] = bad
            with self.assertRaises(checker.OracleFailure):
                p.validate_pattern_corpus(json.dumps(value).encode(), corpus_raw)
        for key, bad in (("index", True), ("schema_sha256", "0" * 64), ("regex", "unanchored"),
                         ("regex", "\\A(?:" + "x" * 32768 + ")\\z"), ("private", "PRIVATE")):
            value = copy.deepcopy(artifact); value["cases"][0][key] = bad
            with self.assertRaises(checker.OracleFailure):
                p.validate_pattern_corpus(json.dumps(value).encode(), corpus_raw)
        with self.assertRaises(checker.OracleFailure):
            p.validate_pattern_corpus(b"x" * (checker.MAX_INPUT + 1), corpus_raw)

    def test_finite_cli_validates_pattern_artifact_before_native_import(self):
        import tempfile
        import io
        from contextlib import redirect_stdout
        with tempfile.TemporaryDirectory() as directory:
            corpus = Path(directory) / "corpus.json"
            patterns = Path(directory) / "patterns.json"
            corpus.write_bytes((BENCHMARKS.parent / "fixtures/llguidance_literal_regressions.json").read_bytes())
            patterns.write_bytes(b'{"version":true,"private":"PRIVATE"}')
            output = io.StringIO()
            with patch.object(p.sys, "argv", ["probe", "--corpus", str(corpus), "--regex-corpus", str(patterns), "--module-root", "PRIVATE_ROOT"]), \
                    patch.object(p.oracle, "NativeBackend") as native, redirect_stdout(output):
                self.assertEqual(p.main(), 2)
            native.assert_not_called()
            self.assertNotIn("PRIVATE", output.getvalue())


if __name__ == "__main__":
    unittest.main()
