"""Original selected-metadata publication tests; no real models or native imports.

Copyright 2026 LocalLore contributors. SPDX-License-Identifier: Apache-2.0
"""
from contextlib import ExitStack
import copy
import hashlib
import importlib.util
import io
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest import mock

from scripts.tests.test_litert_tokenizer_metadata import Container

ROOT = Path(__file__).resolve().parents[2]
SPEC = importlib.util.spec_from_file_location("tokenizer_launcher_under_test", ROOT / "scripts/litert_tokenizer_oracle.py")
s = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = s
SPEC.loader.exec_module(s)


class TokenizerLauncherTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(); self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.data = bytes(Container().data)
        self.source = self.root / "original-synthetic-container.bin"; self.source.write_bytes(self.data)
        self.output = self.root / "new-selected-output"
        self.proposal = self.root / "proposal.json"; self.auth = self.root / "grant.json"
        self.stack = ExitStack(); self.addCleanup(self.stack.close)
        self.stack.enter_context(mock.patch.object(s, "MODEL_BYTES", len(self.data)))
        self.stack.enter_context(mock.patch.object(s, "MODEL_SHA256", hashlib.sha256(self.data).hexdigest()))
        self.value = {"version": 1, "scope": s.SCOPE, "source_commit": "a" * 40,
            "source": {"path": str(self.source), "bytes": len(self.data), "sha256": s.MODEL_SHA256},
            "source_files": {name: s.sha((ROOT / name).read_bytes()) for name in s.SOURCE_FILES},
            "output": str(self.output), "allow_source_reads": False, "root_go_pending": True}
        self.grant = {"version": 1, "proposal_sha256": "", "allow_full_source_hash": True,
            "allow_selected_metadata_read": True, "allow_native": False, "root_go_pending": False}
        self.write()

    def write(self):
        self.proposal.write_bytes(s.encoded(self.value))
        self.grant["proposal_sha256"] = s.sha(self.proposal.read_bytes())
        self.auth.write_bytes(s.encoded(self.grant))

    def test_two_source_hashes_and_create_only_selected_artifacts(self):
        before = self.source.read_bytes()
        with mock.patch.object(s, "full_hash", wraps=s.full_hash) as hashes:
            result = s.extract(self.proposal, self.auth)
        self.assertEqual(hashes.call_count, 2)
        self.assertTrue(result["source_verified_twice"])
        self.assertFalse(result["weight_payloads_published"]); self.assertFalse(result["native_loaded"])
        self.assertEqual(result["kind"], "HF_JSON")
        self.assertEqual(set(p.name for p in self.output.iterdir()),
                         {"selection.json", "selected-tokenizer.bin", "tokenizer.json", "llm-metadata.pb"})
        for name, item in result["artifacts"].items():
            raw = (self.output / name).read_bytes()
            self.assertEqual(len(raw), item["bytes"]); self.assertEqual(s.sha(raw), item["sha256"])
            self.assertNotIn(b"ORIGINAL_WEIGHTS_DO_NOT_READ", raw)
            self.assertNotIn(b"ORIGINAL_GRAPH_DO_NOT_READ", raw)
        self.assertEqual(before, self.source.read_bytes())
        self.assertNotIn(str(self.source), json.dumps(result))
        self.assertTrue(s.validate_report(result, self.value, self.output))
        with self.assertRaises(s.SelectedTokenizerRefused): s.extract(self.proposal, self.auth)

    def test_grants_have_exact_keys_bool_types_and_matching_proposal(self):
        for key in ("allow_full_source_hash", "allow_selected_metadata_read", "allow_native", "root_go_pending"):
            original = self.grant[key]
            for wrong in (not original, int(original), None):
                with self.subTest(key=key, wrong=wrong):
                    self.grant[key] = wrong; self.write()
                    with self.assertRaises(s.SelectedTokenizerRefused), mock.patch.object(s, "module") as load:
                        s.extract(self.proposal, self.auth)
                    load.assert_not_called()
            self.grant[key] = original
        self.grant["unexpected"] = True; self.write()
        with self.assertRaises(s.SelectedTokenizerRefused): s.validate(self.proposal, self.auth)

    def test_source_drift_refuses_before_output_and_preserves_original_error(self):
        self.source.write_bytes(b"x" * len(self.data))
        with self.assertRaisesRegex(s.SelectedTokenizerRefused, "source_identity"):
            s.extract(self.proposal, self.auth)
        self.assertFalse(self.output.exists())

    def test_reader_refusal_is_closed_and_not_replaced_by_success(self):
        self.data = b"X" * len(self.data); self.source.write_bytes(self.data)
        self.stack.enter_context(mock.patch.object(s, "MODEL_SHA256", s.sha(self.data)))
        self.value["source"]["sha256"] = s.MODEL_SHA256; self.write()
        with self.assertRaisesRegex(s.SelectedTokenizerRefused, "metadata_header_invalid"):
            s.extract(self.proposal, self.auth)
        self.assertFalse(self.output.exists())

    def test_second_hash_or_source_code_drift_never_publishes(self):
        with mock.patch.object(s, "full_hash", side_effect=[s.MODEL_SHA256, "0" * 64]), \
                self.assertRaisesRegex(s.SelectedTokenizerRefused, "source_changed"):
            s.extract(self.proposal, self.auth)
        self.assertFalse(self.output.exists())
        self.value["source_files"][s.SOURCE_FILES[0]] = "0" * 64; self.write()
        with self.assertRaisesRegex(s.SelectedTokenizerRefused, "source_changed"):
            s.validate(self.proposal, self.auth)

    def test_relative_linked_and_repository_output_are_refused(self):
        for path in ("relative", str(ROOT / "unexpected-private-metadata")):
            self.value["output"] = path; self.write()
            with self.assertRaises(s.SelectedTokenizerRefused): s.validate(self.proposal, self.auth)
        with mock.patch.object(s, "no_links", side_effect=s.SelectedTokenizerRefused("unsafe_path")), \
                self.assertRaisesRegex(s.SelectedTokenizerRefused, "unsafe_path"):
            s.validate(self.proposal, self.auth)

    def test_worker_waits_for_exact_owner_barrier_before_any_source_validation(self):
        stream = type("Input", (), {"buffer": io.BytesIO(b"not-the-owner")})()
        with mock.patch.object(sys, "stdin", stream), mock.patch.object(s, "extract") as extract, \
                mock.patch("sys.stdout", new_callable=io.StringIO) as output:
            code = s.main(["_extract-worker", "--proposal", str(self.proposal), "--authorization", str(self.auth)])
        self.assertEqual(code, 2); extract.assert_not_called()
        self.assertEqual(json.loads(output.getvalue())["reason"], "owner_barrier")

    def test_report_is_closed_bound_and_rehashed_not_accepted_by_a_status_word(self):
        valid = s.extract(self.proposal, self.auth)
        for key, wrong in (("version", True), ("source_verified_twice", 1), ("native_loaded", 0),
                           ("source_bytes", True), ("source_commit", "b" * 40), ("kind", "private"),
                           ("section_count", 257), ("header_end", True), ("metadata_range", [0, 1]),
                           ("tokenizer_range", [16384, True])):
            bad = copy.deepcopy(valid); bad[key] = wrong
            with self.subTest(key=key), self.assertRaises(s.SelectedTokenizerRefused):
                s.validate_report(bad, self.value, self.output)
        bad = copy.deepcopy(valid); bad["extra"] = "private"
        with self.assertRaises(s.SelectedTokenizerRefused): s.validate_report(bad, self.value, self.output)
        (self.output / "tokenizer.json").write_bytes(b"x" * valid["artifacts"]["tokenizer.json"]["bytes"])
        with self.assertRaises(s.SelectedTokenizerRefused): s.validate_report(valid, self.value, self.output)


if __name__ == "__main__": unittest.main()
