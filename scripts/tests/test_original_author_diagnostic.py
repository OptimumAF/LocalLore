"""Original synthetic diagnostic adversaries; no SDK, model or native execution.

A completed sidecar proves byte consistency only. In particular a retained
InvalidProposal is not promoted into an accepted world by an offline report.
Copyright 2026 LocalLore contributors. SPDX-License-Identifier: Apache-2.0
"""
import copy
import importlib.util
import json
from pathlib import Path
import unittest
from unittest.mock import patch

from scripts.tests import test_original_author_model_proof as f

PATH = Path(__file__).resolve().parents[2] / "benchmarks/original_author_diagnostic.py"
SPEC = importlib.util.spec_from_file_location("original_author_diagnostic_under_test", PATH)
d = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(d)

PAYLOADS = ("input-v1.json", "response-v1.bin", "generated-v1.json",
            "workspace-before-v1.json", "workspace-after-v1.json")


def fixture(*, rejected=False, response=None, native_error="InvalidProposal", pretty=False):
    """Derive bytes from the existing synthetic fixture, never private output."""
    if pretty:
        original_encode = f.raw

        def encode(value, sort=False):
            if type(value) is dict and set(value) == set(f.proposal()):
                return json.dumps(value, ensure_ascii=False, indent=2).encode("utf-8")
            return original_encode(value, sort)

        with patch.object(f, "raw", side_effect=encode):
            author, artifacts, imported = f.fixture()
    else:
        author, artifacts, imported = f.fixture()
    if rejected:
        if response is None:
            proposed = f.proposal()
            proposed["characters"][0]["known_by"] = [0]  # Missing the NPC's own slot.
            response = f.raw(proposed)
        generated = f.raw({"version": 1, "status": "rejected", "error": native_error})
        keep = ("input-v1.json", "begin-v1.json", "workspace-before-v1.json")
        artifacts = {name: artifacts[name] for name in keep}
        artifacts["generated-v1.json"] = generated
        artifacts.update({name: f.raw(value) for name, value in f.traces(len(response)).items()})
        author.update(status="refused", stage="generate", reason="checks_failed",
                      review_sha256=None, creation_id=None)
        author["records"] = {name: f.binding(artifacts[name]) if name in artifacts else None
                             for name in f.p.RECORDS}
        author["traces"] = {name: f.binding(artifacts[name]) for name in f.p.TRACES}
    else:
        origin = json.loads(artifacts["archive-v1.json"])["payload"]["story"]["seed"]["initial_world"]
        response = origin["generation"]["response"].encode("utf-8")
    files = {name: artifacts[name] for name in
             ("input-v1.json", "generated-v1.json", "workspace-before-v1.json")}
    files["workspace-after-v1.json"] = files["workspace-before-v1.json"]
    files["response-v1.bin"] = response
    manifest = {"version": 1, "scope": "original_author_diagnostic_v1",
                "status": "completed", "reason": None, "feature_acceptance": False,
                "input_sha256": "", "author_proof_sha256": "",
                "capture": {"state": "recorded", "calls": 1, "response": None}, "files": {}}
    bundle = dict(manifest=manifest, files=files, author=author,
                  artifacts=artifacts, imported=imported)
    seal(bundle)
    return bundle


def seal(bundle):
    """Rebind deliberate forgeries so tests reach more than a stale digest check."""
    manifest, files = bundle["manifest"], bundle["files"]
    manifest["input_sha256"] = f.sha(files["input-v1.json"])
    manifest["author_proof_sha256"] = f.sha(f.raw(bundle["author"]))
    manifest["files"] = {name: f.binding(value) for name, value in files.items()}
    manifest["capture"]["response"] = f.binding(files["response-v1.bin"])


def replace_artifact(bundle, name, mutate):
    value = json.loads(bundle["artifacts"][name])
    mutate(value)
    payload = f.raw(value)
    bundle["artifacts"][name] = payload
    group = "traces" if name in f.p.TRACES else "records"
    bundle["author"][group][name] = f.binding(payload)
    if name in bundle["files"]:
        bundle["files"][name] = payload
    seal(bundle)


def arguments(bundle):
    return (f.raw(bundle["manifest"]), bundle["files"], f.raw(bundle["author"]),
            bundle["artifacts"], bundle["imported"])


def native_report(bundle, *, status="rejected", category="character_self_knowledge",
                  error="InvalidProposal"):
    return {"version": 1, "scope": "original_author_native_diagnostic_v1",
            "input_sha256": f.sha(bundle["files"]["input-v1.json"]),
            "response_sha256": f.sha(bundle["files"]["response-v1.bin"]),
            "input_bytes": len(bundle["files"]["input-v1.json"]),
            "response_bytes": len(bundle["files"]["response-v1.bin"]),
            "status": status, "category": category, "error": error}


class OriginalAuthorDiagnosticTests(unittest.TestCase):
    def refuse(self, bundle, manifest_raw=None):
        args = arguments(bundle)
        if manifest_raw is not None:
            args = (manifest_raw, *args[1:])
        with self.assertRaises(d.DiagnosticRefused) as caught:
            d.validate_diagnostic(*args)
        self.assertIn(caught.exception.reason, d.REASONS)

    def refuse_report(self, bundle, report):
        with self.assertRaises(d.DiagnosticRefused) as caught:
            d.validate_native_report(f.raw(report), *arguments(bundle))
        self.assertIn(caught.exception.reason, d.REASONS)

    def test_complete_synthetic_sidecar_is_readonly_and_not_feature_acceptance(self):
        bundle = fixture()
        before = copy.deepcopy(bundle)
        self.assertEqual(d.validate_diagnostic(*arguments(bundle)), bundle["manifest"])
        report = native_report(bundle, status="valid", category=None, error=None)
        self.assertEqual(d.validate_native_report(f.raw(report), *arguments(bundle)), report)
        self.assertIs(bundle["manifest"]["feature_acceptance"], False)
        self.assertEqual(bundle, before)

    def test_completed_diagnostic_retains_the_semantically_rejected_original(self):
        bundle = fixture(rejected=True)
        self.assertEqual(d.validate_diagnostic(*arguments(bundle)), bundle["manifest"])
        report = native_report(bundle)
        self.assertEqual(d.validate_native_report(f.raw(report), *arguments(bundle)), report)
        self.assertEqual(json.loads(bundle["files"]["generated-v1.json"]),
                         {"version": 1, "status": "rejected", "error": "InvalidProposal"})
        self.assertEqual(bundle["author"]["status"], "refused")
        self.assertIsNone(bundle["author"]["creation_id"])
        with self.assertRaises(f.p.ProofRefused):
            f.p.validate_author(f.raw(bundle["author"]), bundle["artifacts"], bundle["imported"])

    def test_valid_utf8_bad_json_can_be_diagnosed_without_repairing_it(self):
        response = b'{"locations": ['
        bundle = fixture(rejected=True, response=response, native_error="Malformed")
        self.assertEqual(d.validate_diagnostic(*arguments(bundle)), bundle["manifest"])
        report = native_report(bundle, status="malformed", category="response_json", error="Malformed")
        self.assertEqual(d.validate_native_report(f.raw(report), *arguments(bundle)), report)
        self.assertEqual(bundle["files"]["response-v1.bin"], response)
        self.assertEqual(bundle["author"]["stage"], "generate")

    def test_duplicate_response_keys_remain_exact_malformed_evidence(self):
        response = b'{"version":1,"version":1}'
        bundle = fixture(rejected=True, response=response, native_error="Malformed")
        report = native_report(bundle, status="malformed", category="response_json", error="Malformed")
        self.assertEqual(d.validate_native_report(f.raw(report), *arguments(bundle)), report)
        self.assertEqual(bundle["files"]["response-v1.bin"], response)
        self.assertEqual(json.loads(bundle["files"]["generated-v1.json"])["error"], "Malformed")

    def test_full_8192_byte_capture_is_not_truncated_or_normalized(self):
        proposal = f.proposal()
        proposal["characters"][0]["known_by"] = [0]
        response = f.raw(proposal).ljust(8192, b" ")
        bundle = fixture(rejected=True, response=response)
        self.assertEqual(d.validate_diagnostic(*arguments(bundle)), bundle["manifest"])
        report = native_report(bundle)
        self.assertEqual(d.validate_native_report(f.raw(report), *arguments(bundle)), report)
        self.assertEqual(bundle["files"]["response-v1.bin"], response)
        self.assertEqual(report["response_bytes"], 8192)

    def test_json_whitespace_is_bound_as_bytes_but_not_a_second_proposal_validator(self):
        bundle = fixture(pretty=True)
        response = bundle["files"]["response-v1.bin"]
        self.assertIn(b"\n", response)
        generated = json.loads(bundle["files"]["generated-v1.json"])["data"]["proposal"]
        self.assertEqual(json.loads(response), generated)
        report = native_report(bundle, status="valid", category=None, error=None)
        self.assertEqual(d.validate_native_report(f.raw(report), *arguments(bundle)), report)

    def test_manifest_fields_and_true_versus_one_are_closed(self):
        for field in fixture()["manifest"]:
            bundle = fixture()
            del bundle["manifest"][field]
            with self.subTest(missing=field):
                self.refuse(bundle)
        for field, value in (("version", True), ("extra", 1), ("scope", "foreign"),
                             ("status", "refused"), ("reason", "checks_failed"),
                             ("feature_acceptance", True), ("feature_acceptance", 0)):
            bundle = fixture()
            bundle["manifest"][field] = value
            with self.subTest(field=field, value=value):
                self.refuse(bundle)

    def test_each_payload_binding_and_actual_roster_is_required(self):
        for name in PAYLOADS:
            for mode in ("file", "binding", "null", "changed"):
                bundle = fixture()
                if mode == "file":
                    del bundle["files"][name]
                elif mode == "binding":
                    del bundle["manifest"]["files"][name]
                elif mode == "null":
                    bundle["manifest"]["files"][name] = None
                else:
                    bundle["files"][name] += b" "
                with self.subTest(name=name, mode=mode):
                    self.refuse(bundle)
        bundle = fixture()
        bundle["files"]["borrowed-story.json"] = b"{}"
        seal(bundle)
        self.refuse(bundle)
        bundle = fixture()
        bundle["manifest"]["files"]["response-v1.bin"]["bytes"] = True
        self.refuse(bundle)

    def test_capture_cannot_alias_another_file_or_claim_duplicate_calls(self):
        for field, value in (("calls", 0), ("calls", 2), ("calls", True),
                             ("state", "empty"), ("state", "duplicate"), ("state", "invalid"),
                             ("response", None), ("response", {"bytes": 1, "sha256": "0" * 64})):
            bundle = fixture(rejected=True)
            bundle["manifest"]["capture"][field] = value
            with self.subTest(field=field, value=value):
                self.refuse(bundle)
        bundle = fixture()
        bundle["manifest"]["capture"]["response"] = bundle["manifest"]["files"]["input-v1.json"]
        self.refuse(bundle)
        bundle = fixture()
        bundle["manifest"]["capture"]["secret_extra"] = "must not echo"
        self.refuse(bundle)

    def test_raw_utf8_and_byte_caps_refuse_before_any_native_claim(self):
        for name, payload in (("response-v1.bin", b"\xff"),
                              ("response-v1.bin", b" " * 8193),
                              ("input-v1.json", b" " * 4097),
                              ("generated-v1.json", b" " * 262145),
                              ("workspace-before-v1.json", b" " * 262145),
                              ("workspace-after-v1.json", b" " * 262145)):
            bundle = fixture(rejected=True)
            bundle["files"][name] = payload
            seal(bundle)
            with self.subTest(name=name, size=len(payload)):
                self.refuse(bundle)
        bundle = fixture()
        self.refuse(bundle, b" " * 32769)

    def test_rebound_changed_input_and_provenance_still_refuse(self):
        for name, mutate in (
            ("input-v1.json", lambda v: v.__setitem__("player_name", "Foreign")),
            ("begin-v1.json", lambda v: v["data"].__setitem__("provider", "scripted")),
            ("begin-v1.json", lambda v: v["data"].__setitem__("job", "initial-2")),
            ("begin-v1.json", lambda v: v["data"].__setitem__("input_sha256", "0" * 64)),
        ):
            bundle = fixture(rejected=True)
            replace_artifact(bundle, name, mutate)
            with self.subTest(name=name):
                self.refuse(bundle)
        bundle = fixture(rejected=True)
        bundle["files"]["input-v1.json"] += b"\n"
        bundle["artifacts"]["input-v1.json"] = bundle["files"]["input-v1.json"]
        bundle["author"]["records"]["input-v1.json"] = f.binding(bundle["files"]["input-v1.json"])
        seal(bundle)
        self.refuse(bundle)

    def test_every_profile_field_is_bound_even_when_author_refused(self):
        for field in f.p.PROFILE:
            bundle = fixture(rejected=True)
            value = bundle["author"]["profile"][field]
            bundle["author"]["profile"][field] = "foreign" if type(value) is str else value + 1
            seal(bundle)
            with self.subTest(field=field):
                self.refuse(bundle)
        for field, value in (("job", "initial-0"), ("job", "initial-1\n"),
                             ("prior_import_sha256", "0" * 64), ("elapsed_ms", True)):
            bundle = fixture(rejected=True)
            bundle["author"][field] = value
            seal(bundle)
            with self.subTest(field=field):
                self.refuse(bundle)

    def test_canonical_library_is_unchanged_and_empty_even_with_rebound_hashes(self):
        for changed in ("after", "both"):
            bundle = fixture(rejected=True)
            value = json.loads(bundle["files"]["workspace-after-v1.json"])
            value["data"]["stories"] = [{"title": "Unauthorized early creation"}]
            bundle["files"]["workspace-after-v1.json"] = f.raw(value)
            if changed == "both":
                bundle["files"]["workspace-before-v1.json"] = f.raw(value)
                bundle["artifacts"]["workspace-before-v1.json"] = f.raw(value)
                bundle["author"]["records"]["workspace-before-v1.json"] = f.binding(f.raw(value))
            seal(bundle)
            with self.subTest(changed=changed):
                self.refuse(bundle)

    def test_rejected_generation_cannot_hide_a_review_or_creation(self):
        original_author, original_artifacts, _ = f.fixture()
        for name in ("review-v1.json", "create-v1.json", "retry-v1.json",
                     "snapshot-created-v1.json", "archive-v1.json", "workspace-generated-v1.json"):
            bundle = fixture(rejected=True)
            bundle["artifacts"][name] = original_artifacts[name]
            bundle["author"]["records"][name] = original_author["records"][name]
            seal(bundle)
            with self.subTest(record=name):
                self.refuse(bundle)
        for field, value in (("review_sha256", "a" * 64), ("creation_id", f.p.CREATION_ID),
                             ("stage", "create"), ("status", "completed")):
            bundle = fixture(rejected=True)
            bundle["author"][field] = value
            seal(bundle)
            with self.subTest(field=field):
                self.refuse(bundle)

    def test_one_closed_author_trace_cannot_be_relabelled_or_duplicated(self):
        changes = (
            ("worker-v2.json", lambda v: v["creations"][0].__setitem__("role", "DIRECTOR")),
            ("worker-v2.json", lambda v: v.__setitem__("creations_total", 2)),
            ("worker-v2.json", lambda v: v["counts"].__setitem__("ENGINE_CLOSE_KNOWN", 0)),
            ("callback-v1.json", lambda v: v["calls"][0].__setitem__("role", "NARRATOR")),
            ("callback-v1.json", lambda v: v.__setitem__("requests", 2)),
            ("callback-v1.json", lambda v: v["calls"][0]["counts"].__setitem__("OUTPUT_BYTES", 1)),
            ("callback-v1.json", lambda v: v["calls"][0].__setitem__("max_output_tokens", 350)),
            ("callback-v1.json", lambda v: v["calls"][0]["counts"].__setitem__("SDK_JNI", 1)),
            ("send-v2.json", lambda v: v.__setitem__("last_format", "REGEX")),
        )
        for name, mutate in changes:
            bundle = fixture(rejected=True)
            replace_artifact(bundle, name, mutate)
            with self.subTest(name=name):
                self.refuse(bundle)

    def test_native_report_cannot_promote_a_rejected_original_or_reverse_an_ok_reply(self):
        rejected = fixture(rejected=True)
        self.refuse_report(rejected, native_report(rejected, status="valid", category=None, error=None))
        accepted = fixture()
        self.refuse_report(accepted, native_report(accepted))
        for field, value in (("error", "Malformed"), ("error", "TooLarge"),
                             ("category", "invalid_input"), ("category", "invented_reason"),
                             ("status", "completed")):
            report = native_report(rejected)
            report[field] = value
            with self.subTest(field=field):
                self.refuse_report(rejected, report)

    def test_native_report_shape_full_hashes_counts_and_types_are_closed(self):
        bundle = fixture(rejected=True)
        good = native_report(bundle)
        for field in good:
            report = good.copy()
            del report[field]
            with self.subTest(missing=field):
                self.refuse_report(bundle, report)
        for field, value in (("extra", "private text"), ("version", True),
                             ("input_bytes", True), ("response_bytes", True),
                             ("input_bytes", None), ("response_bytes", None),
                             ("input_sha256", "0" * 64), ("response_sha256", "0" * 64),
                             ("response_bytes", good["response_bytes"] - 1),
                             ("scope", "foreign")):
            report = good.copy()
            report[field] = value
            with self.subTest(field=field):
                self.refuse_report(bundle, report)

    def test_complete_capture_cannot_be_relabelled_as_unobserved_cli_reads(self):
        bundle = fixture(rejected=True, response=b"{", native_error="Malformed")
        for category in ("input_read", "response_read", "input_bytes", "response_bytes", "input_json"):
            report = native_report(bundle, status="malformed", category=category, error="Malformed")
            with self.subTest(category=category):
                self.refuse_report(bundle, report)

    def test_strict_json_duplicate_keys_and_sanitized_failure_reasons(self):
        bundle = fixture(rejected=True)
        for payload in (b'{"version":1,"version":1}', b'{"version":NaN}',
                        b'{"x":"\\ud800"}', b"\xff", b"{} trailing"):
            with self.subTest(payload=payload[:20]):
                self.refuse(bundle, payload)
                with self.assertRaises(d.DiagnosticRefused) as caught:
                    d.validate_native_report(payload, *arguments(bundle))
                self.assertIn(str(caught.exception), d.REASONS)
                self.assertNotIn("secret", str(caught.exception))
        self.assertEqual(str(d.DiagnosticRefused("private model text / secret path")), "malformed")

    def test_rebound_accepted_proposal_difference_is_not_hidden_by_equal_byte_count(self):
        bundle = fixture()
        response = bundle["files"]["response-v1.bin"]
        self.assertIn(b"Tavi", response)
        bundle["files"]["response-v1.bin"] = response.replace(b"Tavi", b"Luma")
        self.assertEqual(len(response), len(bundle["files"]["response-v1.bin"]))
        seal(bundle)
        self.refuse(bundle)

    def test_both_validators_remain_pure_and_never_mutate_caller_bytes_or_mappings(self):
        for rejected in (False, True):
            bundle = fixture(rejected=rejected)
            before = copy.deepcopy(bundle)
            report = native_report(bundle) if rejected else native_report(bundle, status="valid", category=None, error=None)
            with patch("builtins.open", side_effect=AssertionError("file IO")), \
                    patch("subprocess.Popen", side_effect=AssertionError("process")), \
                    patch.object(Path, "read_bytes", side_effect=AssertionError("path IO")):
                d.validate_diagnostic(*arguments(bundle))
                d.validate_native_report(f.raw(report), *arguments(bundle))
            self.assertEqual(bundle, before)


if __name__ == "__main__":
    unittest.main()
