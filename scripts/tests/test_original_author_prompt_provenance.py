"""Original synthetic prompt-provenance adversaries; no SDK or model execution.

Prompt selection binds a claimed completed origin. It never authenticates an SDK
run, validates a proposal, or converts a retained native refusal into acceptance.
Copyright 2026 LocalLore contributors. SPDX-License-Identifier: Apache-2.0
"""
import copy
import json
import unittest
from unittest.mock import patch

from scripts.tests import test_original_author_diagnostic as df

f, d = df.f, df.d
LEGACY = "initial-world-v1"
CURRENT = "initial-world-v1.1"


def fixture(version=LEGACY, *, rejected=False, schema_version=LEGACY):
    """Rebuild every synthetic byte/hash binding, not a stale-digest forgery."""
    encode = f.raw

    def rewrite(value):
        if type(value) is dict:
            value = {key: rewrite(item) for key, item in value.items()}
            if set(value) == {"version", "generation", "reviewed", "accepted", "title"}:
                value["generation"]["prompt_version"] = version
                value["generation"]["schema_version"] = schema_version
            return value
        if type(value) is list:
            return [rewrite(item) for item in value]
        return value

    with patch.object(f, "raw", side_effect=lambda value, sort=False: encode(rewrite(value), sort)):
        return df.fixture(rejected=rejected)


def report(bundle):
    return df.native_report(bundle, status="valid", category=None, error=None)


def author(bundle, **kwargs):
    return f.p.validate_author(f.raw(bundle["author"]), bundle["artifacts"], bundle["imported"], **kwargs)


def diagnostic(bundle, **kwargs):
    return d.validate_diagnostic(*df.arguments(bundle), **kwargs)


def native(bundle, **kwargs):
    return d.validate_native_report(f.raw(report(bundle)), *df.arguments(bundle), **kwargs)


class OriginalAuthorPromptProvenanceTests(unittest.TestCase):
    def refuse_all(self, bundle, **kwargs):
        for api, error in ((author, f.p.ProofRefused), (diagnostic, d.DiagnosticRefused),
                           (native, d.DiagnosticRefused)):
            with self.subTest(api=api.__name__), self.assertRaises(error) as caught:
                api(bundle, **kwargs)
            self.assertIn(caught.exception.reason, f.p.REASONS | d.REASONS)

    def pass_all(self, bundle, **kwargs):
        self.assertEqual(author(bundle, **kwargs), bundle["author"])
        self.assertEqual(diagnostic(bundle, **kwargs), bundle["manifest"])
        self.assertEqual(native(bundle, **kwargs), report(bundle))

    def test_legacy_default_is_readonly_and_still_valid(self):
        bundle = fixture()
        before = copy.deepcopy(bundle)
        self.pass_all(bundle)
        self.assertEqual(bundle, before)

    def test_new_completed_origin_refuses_legacy_default(self):
        self.refuse_all(fixture(CURRENT))

    def test_explicit_current_selector_binds_new_completed_origin(self):
        bundle = fixture(CURRENT)
        before = copy.deepcopy(bundle)
        self.pass_all(bundle, expected_prompt_version=CURRENT)
        self.assertEqual(bundle, before)

    def test_explicit_current_selector_does_not_relabel_legacy_origin(self):
        self.refuse_all(fixture(), expected_prompt_version=CURRENT)

    def test_explicit_legacy_selector_remains_exact(self):
        self.pass_all(fixture(), expected_prompt_version=LEGACY)
        self.refuse_all(fixture(CURRENT), expected_prompt_version=LEGACY)

    def test_unknown_and_nonstring_selectors_refuse_all_apis(self):
        for value in (None, True, False, 1, b"initial-world-v1", [], {},
                      "", "initial-world-v2", "initial-world-v1.1 ", "INITIAL-WORLD-V1.1"):
            with self.subTest(selector=repr(value)):
                self.refuse_all(fixture(), expected_prompt_version=value)

    def test_rejected_generation_cannot_hide_invalid_selector(self):
        for value in (True, {}, [], "initial-world-v2"):
            with self.subTest(selector=repr(value)):
                self.refuse_all(fixture(rejected=True), expected_prompt_version=value)

    def test_current_selection_never_promotes_native_refusal(self):
        bundle = fixture(CURRENT, rejected=True)
        before = copy.deepcopy(bundle)
        self.assertEqual(diagnostic(bundle, expected_prompt_version=CURRENT), bundle["manifest"])
        rejected = df.native_report(bundle)
        self.assertEqual(d.validate_native_report(f.raw(rejected), *df.arguments(bundle),
                                                  expected_prompt_version=CURRENT), rejected)
        with self.assertRaises(f.p.ProofRefused):
            author(bundle, expected_prompt_version=CURRENT)
        with self.assertRaises(d.DiagnosticRefused):
            native(bundle, expected_prompt_version=CURRENT)
        self.assertEqual(bundle["author"]["status"], "refused")
        self.assertIsNone(bundle["author"]["creation_id"])
        self.assertIs(bundle["manifest"]["feature_acceptance"], False)
        self.assertEqual(bundle, before)

    def test_prompt_revision_is_bound_in_origin_review_and_seed_identity(self):
        old, new = fixture(), fixture(CURRENT)
        old_archive = json.loads(old["artifacts"]["archive-v1.json"])
        new_archive = json.loads(new["artifacts"]["archive-v1.json"])
        old_seed = old_archive["payload"]["story"]["seed"]
        new_seed = new_archive["payload"]["story"]["seed"]
        self.assertEqual(old_seed["initial_world"]["generation"]["prompt_version"], LEGACY)
        self.assertEqual(new_seed["initial_world"]["generation"]["prompt_version"], CURRENT)
        self.assertNotEqual(old["author"]["review_sha256"], new["author"]["review_sha256"])
        self.assertNotEqual(old_seed["id"], new_seed["id"])
        self.assertNotEqual(old_seed["player"], new_seed["player"])
        self.assertNotEqual(old_archive["integrity"]["seed_sha256"], new_archive["integrity"]["seed_sha256"])
        self.assertEqual(old["files"]["response-v1.bin"], new["files"]["response-v1.bin"])
        self.pass_all(old)
        self.pass_all(new, expected_prompt_version=CURRENT)

    def test_selector_does_not_relax_exact_sidecar_byte_bindings(self):
        for label in (LEGACY, CURRENT):
            bundle = fixture(label)
            bundle["files"]["response-v1.bin"] += b" "
            with self.subTest(label=label), self.assertRaises(d.DiagnosticRefused):
                diagnostic(bundle, expected_prompt_version=label)
            with self.subTest(label=label), self.assertRaises(d.DiagnosticRefused):
                native(bundle, expected_prompt_version=label)

    def test_current_prompt_does_not_change_schema_contract(self):
        self.refuse_all(fixture(CURRENT, schema_version=CURRENT), expected_prompt_version=CURRENT)

    def test_current_selection_does_not_mutate_legacy_default(self):
        self.pass_all(fixture(CURRENT), expected_prompt_version=CURRENT)
        self.pass_all(fixture())
        self.refuse_all(fixture(CURRENT))


if __name__ == "__main__":
    unittest.main()
