"""Adversarial receipt/observation tests, without devices or real models.

Copyright 2026 LocalLore contributors. SPDX-License-Identifier: Apache-2.0
"""
import contextlib
import copy
import hashlib
import io
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "benchmarks"))
import model_integrity as integrity


def receipt(size=integrity.CHUNK_BYTES + 7, whole="a" * 64):
    return {"version": 1, "chunk_bytes": integrity.CHUNK_BYTES, "identity_unchanged": True,
            "before": {"bytes": size, "sha256": whole}, "after": {"bytes": size, "sha256": whole},
            "chunks": [{"index": index, "offset": offset, "bytes": min(integrity.CHUNK_BYTES, size - offset),
                        "sha256": str(index % 10) * 64}
                       for index, offset in enumerate(range(0, size, integrity.CHUNK_BYTES))]}


class ModelIntegrityTest(unittest.TestCase):
    def compare(self, reference, observed):
        return integrity.compare(reference, observed, reference["before"]["bytes"], reference["before"]["sha256"])

    def test_equal_complete_partial_tail(self):
        value = receipt()
        self.assertEqual(self.compare(value, copy.deepcopy(value)), {
            "status": "identity_match", "matches": True, "coverage_bytes": integrity.CHUNK_BYTES + 7,
            "differing_chunks": []})

    def test_mismatch_reports_chunk_interval_not_changed_byte_count(self):
        reference = receipt()
        observed = copy.deepcopy(reference)
        observed["before"]["sha256"] = observed["after"]["sha256"] = "b" * 64
        observed["chunks"][-1]["sha256"] = "c" * 64
        self.assertEqual(self.compare(reference, observed), {
            "status": "identity_mismatch", "matches": False, "coverage_bytes": integrity.CHUNK_BYTES + 7,
            "differing_chunks": [{"index": 1, "offset": integrity.CHUNK_BYTES, "bytes": 7}]})

    def test_size_mismatch_is_not_partial_content_match(self):
        result = self.compare(receipt(), receipt(size=3))
        self.assertEqual(result["status"], "size_mismatch")
        self.assertFalse(result["matches"])
        self.assertIsNone(result["differing_chunks"])

    def test_no_missing_extra_duplicate_reordered_or_gapped_coverage(self):
        reference = receipt()
        cases = []
        for rows in ([], reference["chunks"][:-1], reference["chunks"] * 2,
                     list(reversed(reference["chunks"])), [reference["chunks"][0]] * 2):
            value = copy.deepcopy(reference)
            value["chunks"] = copy.deepcopy(rows)
            cases.append(value)
        for key, replacement in (("index", 0), ("offset", 0), ("offset", integrity.CHUNK_BYTES + 1),
                                 ("bytes", 6), ("bytes", 8), ("bytes", integrity.CHUNK_BYTES)):
            value = copy.deepcopy(reference)
            value["chunks"][-1][key] = replacement
            cases.append(value)
        for value in cases:
            with self.subTest(value=value), self.assertRaises(integrity.InvalidObservation):
                self.compare(reference, value)

    def test_bool_and_float_do_not_pass_integer_contracts(self):
        for field in ("index", "offset", "bytes"):
            for replacement in (True, False, 0.0, 1.0):
                value = receipt()
                value["chunks"][0][field] = replacement
                with self.subTest(field=field, replacement=replacement), self.assertRaises(integrity.InvalidObservation):
                    integrity.validate(value)
        for field in ("version", "chunk_bytes"):
            value = receipt()
            value[field] = True
            with self.assertRaises(integrity.InvalidObservation):
                integrity.validate(value)
        for replacement in (True, 3.0, 0, -1, integrity.MAX_BYTES + 1):
            value = receipt()
            value["before"]["bytes"] = replacement
            with self.assertRaises(integrity.InvalidObservation):
                integrity.validate(value)

    def test_strict_digests_shapes_and_version(self):
        for invalid in ("A" * 64, "g" * 64, "a" * 63, "a" * 65, "a" * 64 + "\n", 9, None):
            for target in ("before", "chunk"):
                value = receipt()
                (value["before"] if target == "before" else value["chunks"][0])["sha256"] = invalid
                with self.subTest(invalid=invalid, target=target), self.assertRaises(integrity.InvalidObservation):
                    integrity.validate(value)
        for mutation in (lambda v: v.update(version=2), lambda v: v.update(identity_unchanged=1),
                         lambda v: v.update(chunk_bytes=1024), lambda v: v.update(path="secret"),
                         lambda v: v["before"].update(path="secret"), lambda v: v["chunks"][0].update(payload="secret"),
                         lambda v: v.pop("after")):
            value = receipt()
            mutation(value)
            with self.assertRaises(integrity.InvalidObservation):
                integrity.validate(value)

    def test_identity_drift_never_yields_a_stable_mismatch(self):
        for side in ("reference", "observed"):
            for changed in ("flag", "hash", "size"):
                source, observed = receipt(), receipt()
                value = source if side == "reference" else observed
                if changed == "flag":
                    value["identity_unchanged"] = False
                else:
                    value["after"]["sha256" if changed == "hash" else "bytes"] = "d" * 64 if changed == "hash" else 42
                with self.subTest(side=side, changed=changed), self.assertRaisesRegex(
                        integrity.InvalidObservation, "source_changed|observed_changed"):
                    self.compare(source, observed)

    def test_source_is_bound_to_expected_approved_identity(self):
        value = receipt()
        for size, sha in ((value["before"]["bytes"] + 1, "a" * 64), (value["before"]["bytes"], "b" * 64),
                          (True, "a" * 64), (1, "private")):
            with self.assertRaises(integrity.InvalidObservation):
                integrity.compare(value, value, size, sha)

    def test_full_digest_is_separate_and_must_agree_with_chunk_comparison(self):
        reference = receipt()
        for changed_full in (False, True):
            observed = copy.deepcopy(reference)
            if changed_full:
                observed["before"]["sha256"] = observed["after"]["sha256"] = "b" * 64
            else:
                observed["chunks"][0]["sha256"] = "b" * 64
            with self.assertRaisesRegex(integrity.InvalidObservation, "inconsistent_hashes"):
                self.compare(reference, observed)

    def test_actual_read_only_local_file_two_passes(self):
        content = b"synthetic private weight bytes" * 1000
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "private-model"
            path.write_bytes(content)
            before = path.stat()
            observed = integrity.inspect_file(path)
            self.assertTrue(integrity.stable(observed))
            self.assertEqual(observed["before"]["sha256"], hashlib.sha256(content).hexdigest())
            self.assertEqual(path.read_bytes(), content)
            self.assertEqual(path.stat().st_mtime_ns, before.st_mtime_ns)
            self.assertNotIn(directory, json.dumps(observed))
            self.assertNotIn("private weight", json.dumps(observed))

    def test_empty_directory_and_symlink_refused(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "empty"
            path.touch()
            with self.assertRaisesRegex(integrity.InvalidObservation, "file_size"):
                integrity.inspect_file(path)
            with self.assertRaisesRegex(integrity.InvalidObservation, "regular_file"):
                integrity.inspect_file(directory)
            path.write_bytes(b"abc")
            with mock.patch.object(Path, "is_symlink", return_value=True), self.assertRaisesRegex(
                    integrity.InvalidObservation, "regular_file"):
                integrity.inspect_file(path)

    def test_actual_growth_and_short_read_refused(self):
        with self.assertRaisesRegex(integrity.InvalidObservation, "file_grew"):
            integrity.read_hash(io.BytesIO(b"abcdef"), 3)
        with self.assertRaisesRegex(integrity.InvalidObservation, "file_shrank"):
            integrity.read_hash(io.BytesIO(b"a"), 3)

    def test_between_pass_mutation_is_observed_not_accepted(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "model"
            path.write_bytes(b"aaa")
            read = integrity.read_hash
            calls = []
            def mutate(source, size):
                result = read(source, size)
                calls.append(1)
                if len(calls) == 1:
                    path.write_bytes(b"bbb")
                return result
            with mock.patch.object(integrity, "read_hash", side_effect=mutate):
                value = integrity.inspect_file(path)
            self.assertFalse(integrity.stable(value))
            self.assertNotEqual(value["before"], value["after"])

    def test_duplicate_json_nonfinite_and_oversized_receipts_refused(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "receipt.json"
            for raw in (b'{"version":1,"version":1}', b'{"bytes":NaN}', b" " * (256 * 1024 + 1)):
                path.write_bytes(raw)
                with self.assertRaises(integrity.InvalidObservation):
                    integrity.load_receipt(path)

    def test_cli_mismatch_and_failure_have_distinct_status_without_private_error(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "private-receipt"
            first = receipt(size=3)
            path.write_text(json.dumps(first), encoding="utf-8")
            observed = Path(directory) / "second"
            second = receipt(size=3, whole="b" * 64)
            second["chunks"][0]["sha256"] = "c" * 64
            observed.write_text(json.dumps(second), encoding="utf-8")
            output = io.StringIO()
            with contextlib.redirect_stdout(output):
                status = integrity.main(["compare", "--reference", str(path), "--observed", str(observed),
                                         "--expected-bytes", "3", "--expected-sha256", "a" * 64])
            self.assertEqual(status, 2)
            self.assertEqual(json.loads(output.getvalue())["status"], "identity_mismatch")
            with contextlib.redirect_stdout(output := io.StringIO()):
                status = integrity.main(["inspect", "--model", str(path.parent / "missing-secret")])
            self.assertEqual(status, 1)
            self.assertEqual(json.loads(output.getvalue()), {"status": "failed", "category": "inspection_failed"})


if __name__ == "__main__":
    unittest.main()
