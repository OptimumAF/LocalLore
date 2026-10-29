"""Synthetic byte-proof adversaries; no model, SDK, target or production engine.

These fixtures demonstrate metadata validation, never execution authenticity.
Copyright 2026 LocalLore contributors. SPDX-License-Identifier: Apache-2.0
"""
import copy
import hashlib
import importlib.util
import json
from pathlib import Path
import unittest
from unittest.mock import patch

PATH = Path(__file__).resolve().parents[2] / "benchmarks/original_author_model_proof.py"
SPEC = importlib.util.spec_from_file_location("original_author_proof_under_test", PATH)
p = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(p)


def raw(value, sort=False):
    return json.dumps(value, ensure_ascii=False, allow_nan=False, sort_keys=sort, separators=(",", ":")).encode("utf-8")


def sha(value):
    return hashlib.sha256(value).hexdigest()


def reply(value):
    return {"version": 1, "status": "ok", "data": value}


def binding(value):
    return {"bytes": len(value), "sha256": sha(value)}


def import_value():
    return {"version": 1, "scope": "original_author_model_import_v1", "status": "completed", "stage": "completed", "reason": None,
            "process": {"pid": 501, "uid": 10421, "start_elapsed_ms": 1000}, "package": p.PACKAGE,
            "model": copy.deepcopy(p.MODEL), "source_counts": {"opened": 1, "closed": 1, "bytes": p.MODEL["bytes"], "off_main": True},
            "accepted": copy.deepcopy(p.MODEL), "elapsed_ms": 5000}


def proposal():
    return {"version": 1, "locations": [{"name": "Lantern hut", "description": "A weather board hangs inside the hut."}], "player_location": 0,
            "characters": [{"name": "Tavi", "description": "A keeper holding a weather note.", "location": 0, "known_by": [1, 0]}],
            "routes": [], "facts": [{"text": "The wind is easing.", "known_by": [0, 1], "discoverable_at": 0}], "beliefs": [], "possessions": []}


def traces(response_bytes):
    zero = {"ERROR_ENTERED", "ERROR_RETURNED", "CANCEL_ENTERED", "CANCEL_RETURNED", "UNCERTAIN"}
    counts = {event: 0 if event in zero else 1 for event in p.WORKER_EVENTS}
    times = {event: None if event in zero else i + 1 for i, event in enumerate(p.WORKER_EVENTS)}
    # The SDK send can return before its asynchronous message/done callbacks.
    worker = {"version": 2, "counts": counts, "saturated": [], "last_ms": times, "snapshot_ms": 100,
              "time_saturated": False, "creations_total": 1, "creations_saturated": False,
              "creations": [{"ordinal": 1, "role": "AUTHOR", "entered_ms": 11, "returned_ms": 12, "failed_ms": None, "failure": "NONE"}]}
    send_counts = {event: 0 if event.endswith("THROWN") else 1 for event in p.SEND_EVENTS}
    send = {"version": 2, "counts": send_counts, "saturated": [],
            "last_ms": {event: None if event.endswith("THROWN") else i + 1 for i, event in enumerate(p.SEND_EVENTS)},
            "snapshot_ms": 100, "time_saturated": False, "format_counts": {"REGEX": 0, "JSON_OBJECT": 1, "OTHER": 0},
            "format_saturated": [], "last_format": "JSON_OBJECT"}
    callback = {"version": 1, "requests": 1, "requests_saturated": False,
                "calls": [{"ordinal": 1, "role": "AUTHOR", "context_tokens": 4096, "max_output_tokens": 1024,
                           "prompt_bytes": 2048, "schema_bytes": 3456,
                           "counts": {"OUTPUT_CHUNKS": 1, "OUTPUT_BYTES": response_bytes, "DONE": 1, "CANCELLED": 0, "SDK_JNI": 0, "OTHER": 0},
                           "saturated": []}]}
    status = {"version": 1, "counts": {event: 0 for event in p.STATUS_EVENTS}, "saturated": []}
    return {"worker-v2.json": worker, "send-v2.json": send, "callback-v1.json": callback, "status-v1.json": status}


def fixture():
    """A synthetic accepted native-output fixture, not a second materializer oracle."""
    input_value = copy.deepcopy(p.INPUT)
    input_hash = sha(raw(input_value))
    proposed = proposal()
    response = raw(proposed).decode()
    origin = {"version": 1, "generation": {"input": input_value, "proposal": proposed, "model_profile": p.PROFILE["id"],
               "model_configuration": copy.deepcopy(p.PROFILE), "provider": "local", "prompt_version": "initial-world-v1", "schema_version": "initial-world-v1",
               "response": response, "response_sha256": sha(response.encode())}, "reviewed": input_value, "accepted": proposed, "title": p.TITLE}
    review_hash = sha(b"locallore/initial-world/v1\0" + raw(origin, True))
    prefix = review_hash[:20]
    player_id = "a-" + prefix + "-0"
    story = "original-" + p.CREATION_ID
    scope = {"story": story, "branch": "main"}
    actor = {"name": "Eira", "location": "l-" + prefix + "-0", "alive": True, "energy": 0, "abilities": [],
             "attributes": {}, "injuries": {}, "affiliations": [], "goals": []}
    seed = {"version": 1, "id": "world-" + prefix, "scope": scope, "profile": "narrative_v1", "player": player_id,
            "locations": [actor["location"]], "routes": [], "actors": {player_id: actor}, "items": {}, "abilities": {},
            "facts": {}, "relationships": {}, "story_time": 0, "beliefs": [], "commitments": {}, "initial_world": origin}
    snapshot = {"scope": scope, "revision": 0, "rules": "narrative_v1", "player": {"version": 1, "scope": scope, "revision": 0,
                 "observer": player_id, "seed_source": seed["id"], "self_state": actor, "facts": [], "observations": [], "beliefs": []},
                "inventory": {}, "receipts": []}
    workspace = {"persistent": True, "location": "Synthetic private workspace", "schema_version": 1, "database_schema_version": 5, "stories": []}
    payload = {"domain_version": 1, "source_database_schema_version": 5, "story": {"id": story, "title": p.TITLE, "seed": seed},
               "transcript": "accepted_request_intent_and_narration_v1", "branches": [{"id": "main", "parent": None, "fork_revision": None, "head_revision": 0, "local_receipts": []}],
               "required_policies": [], "model_references": []}
    archive = {"format": "locallore-playable-archive", "version": 1, "canonicalization": "locallore-json-v1", "privacy": "full_private", "payload": payload,
               "integrity": {"payload_sha256": sha(raw(payload, True)), "seed_sha256": sha(raw(seed, True)),
                             "branches": [{"id": "main", "receipts_sha256": sha(b"[]"), "canonical_state_sha256": "c" * 64}]}}
    documents = {"input-v1.json": input_value,
                 "begin-v1.json": reply({"job": "initial-1", "input_sha256": input_hash, "provider": "local"}),
                 "generated-v1.json": reply({"job": "initial-1", "input": input_value, "proposal": proposed, "provider": "local"}),
                 "review-v1.json": reply({"job": "initial-1", "review_sha256": review_hash, "input": input_value, "proposal": proposed, "title": p.TITLE,
                                          "details": ["World truth · The wind is easing. · Known to: Eira, Tavi"]}),
                 "create-v1.json": reply({"session": "session-1", "scope": scope, "revision": 0, "created": True}),
                 "retry-v1.json": reply({"session": "session-2", "scope": scope, "revision": 0, "created": False}),
                 "workspace-before-v1.json": reply(workspace), "workspace-generated-v1.json": reply(workspace), "workspace-reviewed-v1.json": reply(workspace),
                 "workspace-created-v1.json": reply(dict(workspace, stories=[{"scope": scope, "title": p.TITLE, "revision": 0, "drafts": 0}])),
                 "snapshot-created-v1.json": reply(snapshot), "snapshot-reopened-v1.json": reply(snapshot), "archive-v1.json": archive}
    documents.update(traces(len(response.encode())))
    artifacts = {name: raw(value) for name, value in documents.items()}
    imported = raw(import_value())
    proof = {"version": 1, "scope": "original_author_model_v1", "status": "completed", "stage": "completed", "reason": None,
             "process": {"pid": 502, "uid": 10421, "start_elapsed_ms": 8000}, "package": p.PACKAGE, "prior_import_sha256": sha(imported),
             "profile": copy.deepcopy(p.PROFILE), "job": "initial-1", "input_sha256": input_hash, "review_sha256": review_hash, "creation_id": p.CREATION_ID,
             "records": {name: binding(artifacts[name]) for name in p.RECORDS}, "traces": {name: binding(artifacts[name]) for name in p.TRACES}, "elapsed_ms": 20000}
    return proof, artifacts, imported


def replace_artifact(proof, artifacts, name, mutate):
    value = json.loads(artifacts[name])
    mutate(value)
    artifacts[name] = raw(value)
    proof["records" if name in p.RECORDS else "traces"][name] = binding(artifacts[name])


class ImportProofTests(unittest.TestCase):
    def test_complete_import_and_no_caller_mutation(self):
        original = raw(import_value())
        self.assertEqual(p.validate_import(original), import_value())
        self.assertEqual(original, raw(import_value()))

    def test_partial_refused_or_unclosed_import_never_qualifies(self):
        for field, bad in (("status", "refused"), ("stage", "import"), ("reason", "checks_failed"), ("accepted", None), ("version", True)):
            with self.subTest(field=field):
                value = import_value(); value[field] = bad
                with self.assertRaises(p.ProofRefused): p.validate_import(raw(value))
        for field, bad in (("opened", 0), ("closed", 0), ("bytes", p.MODEL["bytes"] - 1), ("off_main", False), ("opened", True)):
            with self.subTest(field=field):
                value = import_value(); value["source_counts"][field] = bad
                with self.assertRaises(p.ProofRefused): p.validate_import(raw(value))

    def test_closed_import_identity_and_counts_shapes(self):
        for field in ("model", "accepted", "source_counts", "process"):
            value = import_value(); value[field]["extra"] = 1
            with self.subTest(field=field), self.assertRaises(p.ProofRefused): p.validate_import(raw(value))
        value = import_value(); value["model"]["sha256"] = "0" * 64
        with self.assertRaises(p.ProofRefused): p.validate_import(raw(value))

    def test_strict_json_and_sanitized_errors(self):
        for candidate in (b'{"version":1,"version":1}', b'{"x":NaN}', b'{"x":Infinity}', b'{"x":1e999}', b'{"x":"\\ud800"}', b'\xff', b'{} trailing', b"", b" " * (p.MAX_ARTIFACT + 1)):
            with self.subTest(candidate=candidate[:30]), self.assertRaises(p.ProofRefused) as caught:
                p.validate_import(candidate)
            self.assertIn(str(caught.exception), p.REASONS)
        self.assertEqual(str(p.ProofRefused("secret path or model prose")), "malformed")


class AuthorProofTests(unittest.TestCase):
    def assert_reject(self, mutate=None, artifact=None):
        proof, artifacts, imported = fixture()
        if artifact:
            replace_artifact(proof, artifacts, artifact, mutate)
        elif mutate:
            mutate(proof, artifacts)
        with self.assertRaises(p.ProofRefused) as caught:
            p.validate_author(raw(proof), artifacts, imported)
        self.assertIn(caught.exception.reason, p.REASONS)

    def test_complete_synthetic_proof_qualifies_only_metadata(self):
        proof, artifacts, imported = fixture()
        before = copy.deepcopy((proof, artifacts, imported))
        self.assertEqual(p.validate_author(raw(proof), artifacts, imported), proof)
        self.assertEqual((proof, artifacts, imported), before)

    def test_new_process_identity_uses_start_time_not_pid_uniqueness(self):
        proof, artifacts, imported = fixture()
        proof["process"]["pid"] = 501
        self.assertEqual(p.validate_author(raw(proof), artifacts, imported), proof)
        for field, value in (("uid", 10422), ("start_elapsed_ms", 1000), ("start_elapsed_ms", 999), ("pid", 0)):
            with self.subTest(field=field, value=value):
                self.assert_reject(lambda v, _: v["process"].__setitem__(field, value))

    def test_exact_proof_fields_and_incomplete_stage(self):
        for field, value in (("extra", 1), ("version", True), ("status", "refused"), ("stage", "create"), ("reason", "resource_uncertain"), ("prior_import_sha256", "0" * 64),
                             ("job", "../initial-1"), ("job", "initial-0"), ("creation_id", "0" * 32), ("review_sha256", "A" * 64)):
            with self.subTest(field=field, value=value): self.assert_reject(lambda v, _: v.__setitem__(field, value))

    def test_every_missing_null_and_unknown_binding_refused(self):
        for name in p.RECORDS + p.TRACES:
            with self.subTest(name=name, kind="missing"):
                self.assert_reject(lambda v, a: a.pop(name))
            with self.subTest(name=name, kind="null"):
                self.assert_reject(lambda v, a: v["records" if name in p.RECORDS else "traces"].__setitem__(name, None))
        self.assert_reject(lambda v, a: a.__setitem__("unexpected.json", b"{}"))
        self.assert_reject(lambda v, a: v["records"].__setitem__("unexpected.json", {"bytes": 2, "sha256": sha(b"{}")}))

    def test_changed_artifact_bytes_and_binding_shapes_refused(self):
        for name in p.RECORDS + p.TRACES:
            with self.subTest(name=name): self.assert_reject(lambda v, a: a.__setitem__(name, a[name] + b" "))
        self.assert_reject(lambda v, a: v["records"]["begin-v1.json"].__setitem__("bytes", True))
        self.assert_reject(lambda v, a: v["records"]["begin-v1.json"].__setitem__("path", "secret"))

    def test_artifact_byte_caps_before_parsing(self):
        self.assert_reject(lambda v, a: a.__setitem__("archive-v1.json", b" " * (p.MAX_ARTIFACT + 1)))
        def too_many_bytes(v, a):
            for name in ("archive-v1.json", "input-v1.json", "begin-v1.json"):
                a[name] = b" " * 800000
                v["records"][name] = binding(a[name])
        self.assert_reject(too_many_bytes)

    def test_profile_model_and_runtime_pins_are_closed(self):
        for field in p.PROFILE:
            with self.subTest(field=field):
                self.assert_reject(lambda v, a: v["profile"].__setitem__(field, "changed" if type(v["profile"][field]) is str else v["profile"][field] + 1))
        self.assert_reject(lambda v, a: v["profile"].__setitem__("author_tokens", 1024))

    def test_provider_job_input_and_review_are_bound(self):
        for name, field, value in (("begin-v1.json", "provider", "scripted"), ("generated-v1.json", "provider", "scripted"), ("generated-v1.json", "job", "initial-2"),
                                  ("review-v1.json", "review_sha256", "0" * 64), ("review-v1.json", "title", "Changed")):
            with self.subTest(name=name, field=field): self.assert_reject(lambda v: v["data"].__setitem__(field, value), name)
        self.assert_reject(lambda v: v["data"]["input"].__setitem__("player_name", "Changed"), "generated-v1.json")
        self.assert_reject(lambda v: v["data"]["proposal"]["facts"][0].__setitem__("text", "Edited by caller"), "review-v1.json")

    def test_review_details_are_bounded_and_envelopes_closed(self):
        for value in ([], ["x"] * 65, ["x" * 2049], ["x" * 2048] * 9):
            with self.subTest(size=len(value)): self.assert_reject(lambda v: v["data"].__setitem__("details", value), "review-v1.json")
        self.assert_reject(lambda v: v.__setitem__("status", "rejected"), "generated-v1.json")
        self.assert_reject(lambda v: v.__setitem__("extra", "caller cleanup true"), "create-v1.json")

    def test_library_unchanged_until_create(self):
        for name in ("workspace-generated-v1.json", "workspace-reviewed-v1.json"):
            with self.subTest(name=name): self.assert_reject(lambda v: v["data"]["stories"].append({"title": "premature"}), name)
        self.assert_reject(lambda v: v["data"].__setitem__("persistent", False), "workspace-before-v1.json")
        self.assert_reject(lambda v: v["data"]["stories"][0].__setitem__("drafts", 1), "workspace-created-v1.json")

    def test_create_retry_and_reopen_conserve_canonical_state(self):
        for name, field, value in (("create-v1.json", "created", False), ("retry-v1.json", "created", True), ("retry-v1.json", "revision", 1), ("retry-v1.json", "session", "")):
            with self.subTest(name=name, field=field): self.assert_reject(lambda v: v["data"].__setitem__(field, value), name)
        self.assert_reject(lambda v: v["data"]["scope"].__setitem__("story", "foreign"), "retry-v1.json")
        self.assert_reject(lambda v: v["data"]["player"]["self_state"].__setitem__("energy", 99), "snapshot-reopened-v1.json")

    def test_archive_integrity_branch_and_private_format_bound(self):
        for field, value in (("version", 3), ("privacy", "public"), ("format", "changed")):
            with self.subTest(field=field): self.assert_reject(lambda v: v.__setitem__(field, value), "archive-v1.json")
        self.assert_reject(lambda v: v["integrity"].__setitem__("payload_sha256", "0" * 64), "archive-v1.json")
        self.assert_reject(lambda v: v["payload"]["branches"][0].__setitem__("head_revision", 1), "archive-v1.json")
        self.assert_reject(lambda v: v["payload"]["story"]["seed"]["initial_world"]["generation"].__setitem__("provider", "scripted"), "archive-v1.json")

    def test_original_response_and_provenance_tampering_refused_even_rebound(self):
        for field, value in (("response", "{}"), ("response_sha256", "0" * 64), ("prompt_version", "initial-world-v2"), ("schema_version", "initial-world-v2"), ("model_profile", "foreign")):
            with self.subTest(field=field): self.assert_reject(lambda v: v["payload"]["story"]["seed"]["initial_world"]["generation"].__setitem__(field, value), "archive-v1.json")
        self.assert_reject(lambda v: v["payload"]["story"]["seed"]["initial_world"]["generation"]["proposal"]["characters"][0].__setitem__("known_by", [0, 1]), "archive-v1.json")

    def test_native_player_lens_and_inventory_bind_to_archive(self):
        for field, value in (("observer", "player"), ("seed_source", "foreign"), ("observations", [{"forged": True}])):
            with self.subTest(field=field):
                def change(v, a):
                    for name in ("snapshot-created-v1.json", "snapshot-reopened-v1.json"):
                        replace_artifact(v, a, name, lambda doc: doc["data"]["player"].__setitem__(field, value))
                self.assert_reject(change)
        def changed_inventory(v, a):
            for name in ("snapshot-created-v1.json", "snapshot-reopened-v1.json"):
                replace_artifact(v, a, name, lambda doc: doc["data"]["inventory"].__setitem__("unearned", {"quantity": 1}))
        self.assert_reject(changed_inventory)

    def test_each_trace_is_required_closed_and_author_only(self):
        for name in p.TRACES:
            with self.subTest(name=name): self.assert_reject(lambda v: v.__setitem__("extra", True), name)
        self.assert_reject(lambda v: v["creations"][0].__setitem__("role", "DIRECTOR"), "worker-v2.json")
        self.assert_reject(lambda v: v["calls"][0].__setitem__("role", "NARRATOR"), "callback-v1.json")
        self.assert_reject(lambda v: v.__setitem__("version", 1), "worker-v2.json")
        self.assert_reject(lambda v: v.__setitem__("version", 1), "send-v2.json")

    def test_duplicate_author_calls_and_unknown_close_refused(self):
        self.assert_reject(lambda v: v.__setitem__("creations_total", 2), "worker-v2.json")
        self.assert_reject(lambda v: v["creations"].append(copy.deepcopy(v["creations"][0])), "worker-v2.json")
        self.assert_reject(lambda v: v.__setitem__("requests", 2), "callback-v1.json")
        for event in ("DRAIN_SETTLED", "CONVERSATION_CLOSE_KNOWN", "ENGINE_CLOSE_KNOWN"):
            with self.subTest(event=event): self.assert_reject(lambda v: v["counts"].__setitem__(event, 0), "worker-v2.json")
        self.assert_reject(lambda v: v["creations"][0].__setitem__("failure", "UNCERTAIN"), "worker-v2.json")

    def test_trace_errors_saturation_wrong_budget_and_output_refused(self):
        for event in ("CANCELLED", "SDK_JNI", "OTHER"):
            with self.subTest(event=event): self.assert_reject(lambda v: v["calls"][0]["counts"].__setitem__(event, 1), "callback-v1.json")
        for field, value in (("max_output_tokens", 350), ("context_tokens", 8192), ("schema_bytes", 0), ("prompt_bytes", 32768)):
            with self.subTest(field=field): self.assert_reject(lambda v: v["calls"][0].__setitem__(field, value), "callback-v1.json")
        self.assert_reject(lambda v: v["calls"][0]["counts"].__setitem__("OUTPUT_BYTES", 1), "callback-v1.json")
        self.assert_reject(lambda v: v["counts"].__setitem__("CODE_0", 1), "status-v1.json")
        self.assert_reject(lambda v: v.__setitem__("saturated", ["CODE_0"]), "status-v1.json")
        self.assert_reject(lambda v: v.__setitem__("time_saturated", True), "worker-v2.json")
        self.assert_reject(lambda v: v["counts"].__setitem__("MESSAGE_RETURNED", 0), "worker-v2.json")

    def test_send_format_and_time_coherence_are_independent(self):
        self.assert_reject(lambda v: v["format_counts"].update(REGEX=1, JSON_OBJECT=0), "send-v2.json")
        self.assert_reject(lambda v: v.__setitem__("last_format", "OTHER"), "send-v2.json")
        self.assert_reject(lambda v: v["last_ms"].__setitem__("ENGINE_CLOSE_KNOWN", 5), "worker-v2.json")
        self.assert_reject(lambda v: v["last_ms"].__setitem__("ARGUMENTS_RETURNED", 10), "send-v2.json")
        proof, artifacts, imported = fixture()
        # Traces have their own monotonic epochs; comparing cross-trace clocks would be wrong.
        def shift(v):
            v["last_ms"] = {k: None if n is None else n + 200 for k, n in v["last_ms"].items()}
            v["snapshot_ms"] += 200
        replace_artifact(proof, artifacts, "send-v2.json", shift)
        self.assertEqual(p.validate_author(raw(proof), artifacts, imported), proof)

    def test_duplicate_keys_nonfinite_and_surrogates_in_artifacts(self):
        for candidate in (b'{"version":1,"version":1}', b'{"version":NaN}', b'{"secret":"\\ud800"}'):
            def change(v, a):
                a["input-v1.json"] = candidate; v["records"]["input-v1.json"] = binding(candidate)
            with self.subTest(candidate=candidate): self.assert_reject(change)

    def test_validation_does_not_open_files_or_start_processes(self):
        proof, artifacts, imported = fixture()
        with patch("builtins.open", side_effect=AssertionError("IO")), patch("subprocess.Popen", side_effect=AssertionError("process")):
            self.assertEqual(p.validate_author(raw(proof), artifacts, imported), proof)
            self.assertEqual(p.validate_import(imported), import_value())


if __name__ == "__main__":
    unittest.main()
