"""Pure, bounded validation of real original-author experiment proof bytes.

This qualifies a complete self-consistent proof, never authenticates execution.
JUnit, source/APK/target admission and known host owners remain separate gates.
Legacy receipt trace parsers deliberately retain their existing role contracts.
Copyright 2026 LocalLore contributors. SPDX-License-Identifier: Apache-2.0
"""
from collections.abc import Mapping
import hashlib
import json
import math
import re

MAX_ARTIFACT = 1024 * 1024
MAX_COLLECTED = 2 * MAX_ARTIFACT
MODEL = {"bytes": 2588147712, "sha256": "181938105e0eefd105961417e8da75903eacda102c4fce9ce90f50b97139a63c"}
PACKAGE = "org.locallore.app.litertverify"
CREATION_ID = "ea4a25cdca2f4d6491820bf8a0176d31"
TITLE = "SYNTHETIC Island weather note"
PROFILE = {
    "id": "android-litert-play-probe-v1", "model_sha256": MODEL["sha256"],
    "runtime_revision": "bda624851d74be34d4e1f7fac1fc4155939539c7",
    "template_sha256": MODEL["sha256"],
    "worker_sha256": "1e66e0fbcc30534771f0734d03b22612eb67b1287b3d1fa353d13b7d5e126e67",
    "profile_manifest_sha256": "bf5dc40bc7f6aac28d3a97c37ae21dd39d36adf234b9b4e598cd53b2791f35a8",
    "context_tokens": 4096, "director_tokens": 350, "narrator_tokens": 220,
    "deadline_ms": 60000, "repair_limit": 1,
}
INPUT = {
    "version": 1,
    "premise": "At a tiny island lantern hut, Eira asks keeper Tavi for a weather note. A single room, a brief shared fact, no possessions, and no beliefs are enough.",
    "player_name": "Eira", "player_description": "An island visitor.",
    "cast": [{"name": "Tavi", "description": "A quiet lantern keeper."}],
    "profile": "narrative_v1", "presentation": {"version": 1, "tone": "plain", "excluded_phrases": []},
}
RECORDS = (
    "input-v1.json", "begin-v1.json", "generated-v1.json", "review-v1.json", "create-v1.json", "retry-v1.json",
    "workspace-before-v1.json", "workspace-generated-v1.json", "workspace-reviewed-v1.json", "workspace-created-v1.json",
    "snapshot-created-v1.json", "snapshot-reopened-v1.json", "archive-v1.json",
)
TRACES = ("worker-v2.json", "send-v2.json", "callback-v1.json", "status-v1.json")
# Frozen enums from the existing Kotlin serializers, parsed only in this new
# AUTHOR proof protocol. No lazy receipt-controller import or role monkeypatch.
WORKER_EVENTS = (
    "ADMISSION_ENTERED", "ADMISSION_RETURNED", "ENGINE_CREATE_ENTERED", "ENGINE_CREATE_RETURNED",
    "INITIALIZE_ADMISSION_ENTERED", "INITIALIZE_ADMISSION_RETURNED", "INITIALIZE_ENTERED", "INITIALIZE_RETURNED",
    "ROLE_ADMISSION_ENTERED", "ROLE_ADMISSION_RETURNED", "CONVERSATION_CREATE_ENTERED", "CONVERSATION_CREATE_RETURNED",
    "SEND_ADMISSION_ENTERED", "SEND_ADMISSION_RETURNED", "SEND_ENTERED", "SEND_RETURNED", "MESSAGE_ENTERED", "MESSAGE_RETURNED",
    "DONE_ENTERED", "DONE_RETURNED", "ERROR_ENTERED", "ERROR_RETURNED", "DRAIN_SETTLED", "CANCEL_ENTERED", "CANCEL_RETURNED",
    "CONVERSATION_CLOSE_ENTERED", "CONVERSATION_CLOSE_KNOWN", "ENGINE_CLOSE_ENTERED", "ENGINE_CLOSE_KNOWN", "UNCERTAIN",
)
SEND_EVENTS = ("ARGUMENTS_ENTERED", "ARGUMENTS_RETURNED", "ARGUMENTS_THROWN", "ASYNC_CALL_ENTERED", "ASYNC_CALL_RETURNED", "ASYNC_CALL_THROWN")
CALLBACK_EVENTS = ("OUTPUT_CHUNKS", "OUTPUT_BYTES", "DONE", "CANCELLED", "SDK_JNI", "OTHER")
STATUS_EVENTS = tuple("CODE_" + str(n) for n in range(17)) + ("UNRECOGNIZED",)
REASONS = frozenset(("malformed", "shape", "bounds", "binding", "incomplete", "identity", "provenance", "canonical", "traces"))


class ProofRefused(ValueError):
    """Fixed reasons only; never render paths, prose or original exceptions."""
    def __init__(self, reason="malformed"):
        self.reason = reason if reason in REASONS else "malformed"
        super().__init__(self.reason)


def _need(value, reason):
    if not value:
        raise ProofRefused(reason)


def _object(value, keys, reason="shape"):
    _need(type(value) is dict and set(value) == set(keys), reason)
    return value


def _int(value, low=0, high=2**63 - 1, reason="bounds"):
    _need(type(value) is int and low <= value <= high, reason)
    return value


def _text(value, low=0, high=MAX_ARTIFACT):
    _need(type(value) is str, "shape")
    size = len(value.encode("utf-8", "strict"))
    _need(low <= size <= high, "bounds")
    return value


def _sha(raw):
    return hashlib.sha256(raw).hexdigest()


def _digest(value):
    _need(type(value) is str and re.fullmatch(r"[0-9a-f]{64}", value) is not None, "binding")
    return value


def _encode(value, sort=False):
    return json.dumps(value, ensure_ascii=False, allow_nan=False, sort_keys=sort, separators=(",", ":")).encode("utf-8")


def _equal(left, right):
    # JSON equality is type-sensitive; Python's True == 1 must never bind a proof.
    return _encode(left, True) == _encode(right, True)


def _pairs(pairs):
    value = {}
    for key, item in pairs:
        _need(key not in value, "malformed")
        value[key] = item
    return value


def _constant(_):
    raise ProofRefused("malformed")


def _json(raw, cap=MAX_ARTIFACT):
    _need(type(raw) is bytes and 0 < len(raw) <= cap, "bounds")
    value = json.loads(raw.decode("utf-8", "strict"), object_pairs_hook=_pairs, parse_constant=_constant)
    pending = [(value, 0)]
    nodes = 0
    while pending:
        item, depth = pending.pop()
        nodes += 1
        _need(depth <= 64 and nodes <= 100000, "bounds")
        if type(item) is str:
            item.encode("utf-8", "strict")
        elif type(item) is float:
            _need(math.isfinite(item), "malformed")
        elif type(item) is dict:
            pending.extend((k, depth + 1) for k in item)
            pending.extend((v, depth + 1) for v in item.values())
        elif type(item) is list:
            pending.extend((v, depth + 1) for v in item)
    return value


def _process(value):
    _object(value, ("pid", "uid", "start_elapsed_ms"))
    _int(value["pid"], 1, 2**31 - 1)
    _int(value["uid"], 10000, 2**31 - 1)
    _int(value["start_elapsed_ms"])
    return value


def _complete(value, scope, keys):
    _object(value, keys)
    _need(type(value["version"]) is int and value["version"] == 1 and value["scope"] == scope, "identity")
    _need(value["status"] == "completed" and value["stage"] == "completed" and value["reason"] is None, "incomplete")
    _need(value["package"] == PACKAGE, "identity")
    _process(value["process"])
    _int(value["elapsed_ms"])


def _import(raw):
    value = _json(raw)
    _complete(value, "original_author_model_import_v1", ("version", "scope", "status", "stage", "reason", "process", "package", "model", "source_counts", "accepted", "elapsed_ms"))
    _object(value["model"], ("bytes", "sha256"))
    _object(value["accepted"], ("bytes", "sha256"))
    _need(_equal(value["model"], MODEL) and _equal(value["accepted"], MODEL), "identity")
    counts = _object(value["source_counts"], ("opened", "closed", "bytes", "off_main"))
    _need(type(counts["opened"]) is int and counts["opened"] == 1 and type(counts["closed"]) is int and counts["closed"] == 1
          and type(counts["bytes"]) is int and counts["bytes"] == MODEL["bytes"] and counts["off_main"] is True, "incomplete")
    return value


def validate_import(raw: bytes) -> dict:
    """Return only a complete, closed import proof; refused/partial data never qualifies."""
    try:
        return _import(raw)
    except ProofRefused:
        raise
    except (ValueError, TypeError, KeyError, UnicodeError, OverflowError, RecursionError):
        raise ProofRefused("malformed") from None


def _binding(binding, raw):
    _object(binding, ("bytes", "sha256"), "binding")
    _int(binding["bytes"], 1, MAX_ARTIFACT, "binding")
    _digest(binding["sha256"])
    _need(type(raw) is bytes and len(raw) == binding["bytes"] and _sha(raw) == binding["sha256"], "binding")


def _reply(value, keys):
    _object(value, ("version", "status", "data"))
    _need(type(value["version"]) is int and value["version"] == 1 and value["status"] == "ok", "incomplete")
    return _object(value["data"], keys)


def _scope(value, story):
    _object(value, ("story", "branch"))
    _need(value["story"] == story and value["branch"] == "main", "canonical")


def _profile(value):
    _object(value, PROFILE)
    _need(_equal(value, PROFILE), "identity")


def _proposal(value):
    """Closed typed metadata only. Native alone decides cross-field/domain validity."""
    _object(value, ("version", "locations", "player_location", "characters", "routes", "facts", "beliefs", "possessions"))
    _need(type(value["version"]) is int and value["version"] == 1, "provenance")
    _int(value["player_location"], 0, 65535)
    for field, lower, maximum, keys in (
        ("locations", 1, 4, ("name", "description")),
        ("characters", 1, 3, ("name", "description", "location", "known_by")),
        ("routes", 0, 8, ("from", "to")),
        ("facts", 0, 8, ("text", "known_by", "discoverable_at")),
        ("beliefs", 0, 6, ("believer", "text", "confidence")),
        ("possessions", 0, 4, ("name", "description", "owner", "return_to")),
    ):
        rows = value[field]
        _need(type(rows) is list and lower <= len(rows) <= maximum, "bounds")
        for row in rows:
            _object(row, keys)
            for key, item in row.items():
                if key in ("name", "description", "text", "confidence"):
                    _text(item, 1, 512)
                elif key == "known_by":
                    _need(type(item) is list and len(item) <= 4, "shape")
                    for reference in item:
                        _int(reference, 0, 65535)
                elif item is not None or key not in ("discoverable_at", "return_to"):
                    _int(item, 0, 65535)
    _need(len(_encode(value)) <= 8192, "bounds")


def _workspace(value):
    data = _reply(value, ("persistent", "location", "schema_version", "database_schema_version", "stories"))
    _need(data["persistent"] is True and type(data["schema_version"]) is int and data["schema_version"] == 1
          and type(data["database_schema_version"]) is int and data["database_schema_version"] == 5, "canonical")
    _text(data["location"], 1, 4096)
    _need(type(data["stories"]) is list, "shape")
    return data


def _timed_trace(raw, keys, version, events, cap, prefix):
    _need(type(raw) is bytes and len(raw) <= cap - len(prefix) and all(32 <= b <= 126 for b in raw), "traces")
    value = _object(_json(raw, cap), keys, "traces")
    _need(type(value["version"]) is int and value["version"] == version, "traces")
    counts = _object(value["counts"], events, "traces")
    for count in counts.values():
        _int(count, 0, 1000000, "traces")
    _need(value["saturated"] == [], "traces")
    if "snapshot_ms" in value:
        snapshot = _int(value["snapshot_ms"], 0, 180000, "traces")
        _need(value["time_saturated"] is False, "traces")
        last = _object(value["last_ms"], events, "traces")
        for event in events:
            if counts[event] == 0:
                _need(last[event] is None, "traces")
            else:
                _int(last[event], 0, snapshot, "traces")
    return value


def _traces(values, response_bytes):
    worker = _timed_trace(values["worker-v2.json"], ("version", "counts", "saturated", "last_ms", "snapshot_ms", "time_saturated", "creations_total", "creations_saturated", "creations"), 2, WORKER_EVENTS, 4096, b"INSTRUMENTATION_STATUS: locallore_receipt_worker_v2=")
    counts = worker["counts"]
    _need(type(worker["creations_total"]) is int and worker["creations_total"] == 1 and worker["creations_saturated"] is False
          and type(worker["creations"]) is list and len(worker["creations"]) == 1, "traces")
    creation = _object(worker["creations"][0], ("ordinal", "role", "entered_ms", "returned_ms", "failed_ms", "failure"), "traces")
    _need(type(creation["ordinal"]) is int and creation["ordinal"] == 1 and creation["role"] == "AUTHOR"
          and creation["failed_ms"] is None and creation["failure"] == "NONE", "traces")
    _int(creation["entered_ms"], 0, worker["snapshot_ms"], "traces")
    _int(creation["returned_ms"], creation["entered_ms"], worker["snapshot_ms"], "traces")
    for event in WORKER_EVENTS:
        if event.startswith(("MESSAGE_", "ERROR_", "CANCEL_")) or event == "UNCERTAIN":
            continue
        _need(counts[event] == 1, "traces")
    _need(all(counts[event] == 0 for event in ("ERROR_ENTERED", "ERROR_RETURNED", "CANCEL_ENTERED", "CANCEL_RETURNED", "UNCERTAIN")), "traces")
    _need(1 <= counts["MESSAGE_ENTERED"] == counts["MESSAGE_RETURNED"], "traces")
    for entered, returned in (("ADMISSION_ENTERED", "ADMISSION_RETURNED"), ("ENGINE_CREATE_ENTERED", "ENGINE_CREATE_RETURNED"),
        ("INITIALIZE_ADMISSION_ENTERED", "INITIALIZE_ADMISSION_RETURNED"), ("INITIALIZE_ENTERED", "INITIALIZE_RETURNED"),
        ("ROLE_ADMISSION_ENTERED", "ROLE_ADMISSION_RETURNED"), ("CONVERSATION_CREATE_ENTERED", "CONVERSATION_CREATE_RETURNED"),
        ("SEND_ADMISSION_ENTERED", "SEND_ADMISSION_RETURNED"), ("SEND_ENTERED", "SEND_RETURNED"),
        ("CONVERSATION_CLOSE_ENTERED", "CONVERSATION_CLOSE_KNOWN"), ("ENGINE_CLOSE_ENTERED", "ENGINE_CLOSE_KNOWN")):
        _need(worker["last_ms"][entered] <= worker["last_ms"][returned], "traces")
    for event in ("MESSAGE_RETURNED", "DONE_RETURNED", "SEND_RETURNED"):
        _need(worker["last_ms"][event] <= worker["last_ms"]["DRAIN_SETTLED"], "traces")
    _need(worker["last_ms"]["DRAIN_SETTLED"] <= worker["last_ms"]["CONVERSATION_CLOSE_ENTERED"]
          <= worker["last_ms"]["CONVERSATION_CLOSE_KNOWN"] <= worker["last_ms"]["ENGINE_CLOSE_ENTERED"], "traces")
    send = _timed_trace(values["send-v2.json"], ("version", "counts", "saturated", "last_ms", "snapshot_ms", "time_saturated", "format_counts", "format_saturated", "last_format"), 2, SEND_EVENTS, 2048, b"INSTRUMENTATION_STATUS: locallore_receipt_send_v1=")
    _need(all(send["counts"][event] == (0 if event.endswith("THROWN") else 1) for event in SEND_EVENTS), "traces")
    _need(_equal(_object(send["format_counts"], ("REGEX", "JSON_OBJECT", "OTHER"), "traces"), {"REGEX": 0, "JSON_OBJECT": 1, "OTHER": 0})
          and send["format_saturated"] == [] and send["last_format"] == "JSON_OBJECT", "traces")
    _need(send["last_ms"]["ARGUMENTS_ENTERED"] <= send["last_ms"]["ARGUMENTS_RETURNED"]
          <= send["last_ms"]["ASYNC_CALL_ENTERED"] <= send["last_ms"]["ASYNC_CALL_RETURNED"], "traces")
    callback_raw = values["callback-v1.json"]
    _need(len(callback_raw) <= 4096 - len(b"INSTRUMENTATION_STATUS: locallore_receipt_callback_v1=")
          and all(32 <= b <= 126 for b in callback_raw), "traces")
    callback = _object(_json(callback_raw), ("version", "requests", "requests_saturated", "calls"), "traces")
    _need(type(callback["version"]) is int and callback["version"] == 1 and type(callback["requests"]) is int
          and callback["requests"] == 1 and callback["requests_saturated"] is False
          and type(callback["calls"]) is list and len(callback["calls"]) == 1, "traces")
    call = _object(callback["calls"][0], ("ordinal", "role", "context_tokens", "max_output_tokens", "prompt_bytes", "schema_bytes", "counts", "saturated"), "traces")
    _need(type(call["ordinal"]) is int and call["ordinal"] == 1 and call["role"] == "AUTHOR"
          and type(call["context_tokens"]) is int and call["context_tokens"] == 4096
          and type(call["max_output_tokens"]) is int and call["max_output_tokens"] == 1024, "traces")
    prompt = _int(call["prompt_bytes"], 1, 32768, "traces")
    schema = _int(call["schema_bytes"], 2, 32768, "traces")
    _need(prompt + schema <= 32768, "traces")
    counters = _object(call["counts"], CALLBACK_EVENTS, "traces")
    for count in counters.values():
        _int(count, 0, 1000000, "traces")
    _need(call["saturated"] == [] and counters["OUTPUT_CHUNKS"] == counts["MESSAGE_ENTERED"]
          and counters["OUTPUT_BYTES"] == response_bytes and counters["DONE"] == 1
          and all(counters[k] == 0 for k in ("CANCELLED", "SDK_JNI", "OTHER")), "traces")
    status = _timed_trace(values["status-v1.json"], ("version", "counts", "saturated"), 1, STATUS_EVENTS, 2048, b"INSTRUMENTATION_STATUS: locallore_receipt_status_v1=")
    _need(all(count == 0 for count in status["counts"].values()), "traces")


def _expected_prompt_version(value):
    # Caller-selected source cohort, never inferred from untrusted archive data.
    _need(type(value) is str and value in ("initial-world-v1", "initial-world-v1.1"), "provenance")
    return value


def _archive(value, story, generated, review, profile, input_hash, review_hash, expected_prompt_version):
    _object(value, ("format", "version", "canonicalization", "privacy", "payload", "integrity"))
    _need(value["format"] == "locallore-playable-archive" and type(value["version"]) is int and value["version"] == 1
          and value["canonicalization"] == "locallore-json-v1" and value["privacy"] == "full_private", "canonical")
    payload = _object(value["payload"], ("domain_version", "source_database_schema_version", "story", "transcript", "branches", "required_policies", "model_references"))
    _need(type(payload["domain_version"]) is int and payload["domain_version"] == 1
          and type(payload["source_database_schema_version"]) is int and payload["source_database_schema_version"] == 5
          and payload["transcript"] == "accepted_request_intent_and_narration_v1"
          and payload["required_policies"] == [] and payload["model_references"] == [], "canonical")
    saved = _object(payload["story"], ("id", "title", "seed"))
    _need(saved["id"] == story and saved["title"] == TITLE, "canonical")
    seed = _object(saved["seed"], ("version", "id", "scope", "profile", "player", "locations", "routes", "actors", "items", "abilities", "facts", "relationships", "story_time", "beliefs", "commitments", "initial_world"))
    _scope(seed["scope"], story)
    _need(type(seed["version"]) is int and seed["version"] == 1 and seed["profile"] == "narrative_v1", "canonical")
    origin = _object(seed["initial_world"], ("version", "generation", "reviewed", "accepted", "title"))
    _need(type(origin["version"]) is int and origin["version"] == 1 and origin["title"] == TITLE
          and _equal(origin["reviewed"], INPUT) and _equal(origin["accepted"], generated["proposal"]), "provenance")
    generation = _object(origin["generation"], ("input", "proposal", "model_profile", "model_configuration", "provider", "prompt_version", "schema_version", "response", "response_sha256"))
    _need(generation["provider"] == "local" and generation["model_profile"] == profile["id"]
          and _equal(generation["model_configuration"], profile) and _equal(generation["input"], INPUT)
          and _equal(generation["proposal"], generated["proposal"]) and generation["prompt_version"] == expected_prompt_version
          and generation["schema_version"] == "initial-world-v1", "provenance")
    response = _text(generation["response"], 1, 8192).encode("utf-8")
    _need(_digest(generation["response_sha256"]) == _sha(response), "provenance")
    _need(_equal(_json(response, 8192), generation["proposal"]), "provenance")
    _need(_sha(b"locallore/initial-world/v1\0" + _encode(origin, True)) == review_hash, "provenance")
    _need(seed["id"] == "world-" + review_hash[:20] and seed["player"] == "a-" + review_hash[:20] + "-0", "provenance")
    _need(_sha(_encode(INPUT)) == input_hash and _equal(review["proposal"], origin["accepted"]), "provenance")
    _need(type(payload["branches"]) is list and len(payload["branches"]) == 1, "canonical")
    branch = _object(payload["branches"][0], ("id", "parent", "fork_revision", "head_revision", "local_receipts"))
    _need(branch["id"] == "main" and branch["parent"] is None and branch["fork_revision"] is None
          and type(branch["head_revision"]) is int and branch["head_revision"] == 0 and branch["local_receipts"] == [], "canonical")
    integrity = _object(value["integrity"], ("payload_sha256", "seed_sha256", "branches"))
    _need(_digest(integrity["payload_sha256"]) == _sha(_encode(payload, True))
          and _digest(integrity["seed_sha256"]) == _sha(_encode(seed, True)), "canonical")
    _need(type(integrity["branches"]) is list and len(integrity["branches"]) == 1, "canonical")
    branch_hash = _object(integrity["branches"][0], ("id", "receipts_sha256", "canonical_state_sha256"))
    _need(branch_hash["id"] == "main" and _digest(branch_hash["receipts_sha256"]) == _sha(b"[]"), "canonical")
    _digest(branch_hash["canonical_state_sha256"])  # Native already validates/replays its projection; do not reimplement it here.
    return seed, len(response)


def _author(raw, artifacts, prior_import_raw, expected_prompt_version):
    prior = _import(prior_import_raw)
    value = _json(raw)
    _complete(value, "original_author_model_v1", ("version", "scope", "status", "stage", "reason", "process", "package", "prior_import_sha256", "profile", "job", "input_sha256", "review_sha256", "creation_id", "records", "traces", "elapsed_ms"))
    _need(value["process"]["uid"] == prior["process"]["uid"]
          and value["process"]["start_elapsed_ms"] > prior["process"]["start_elapsed_ms"], "identity")
    _need(_digest(value["prior_import_sha256"]) == _sha(prior_import_raw), "binding")
    _profile(value["profile"])
    _need(type(value["job"]) is str and re.fullmatch(r"initial-[1-9][0-9]*", value["job"]) is not None and len(value["job"]) <= 32
          and value["creation_id"] == CREATION_ID, "identity")
    _digest(value["input_sha256"])
    _digest(value["review_sha256"])
    records = _object(value["records"], RECORDS, "binding")
    traces = _object(value["traces"], TRACES, "binding")
    _need(isinstance(artifacts, Mapping) and set(artifacts) == set(RECORDS + TRACES), "binding")
    _need(all(type(b) is bytes and 0 < len(b) <= MAX_ARTIFACT for b in artifacts.values())
          and sum(len(b) for b in artifacts.values()) <= MAX_COLLECTED, "bounds")
    decoded = {}
    for name in RECORDS + TRACES:
        _binding((records if name in RECORDS else traces)[name], artifacts[name])
        decoded[name] = _json(artifacts[name])
    _need(_equal(decoded["input-v1.json"], INPUT) and _sha(_encode(INPUT)) == value["input_sha256"], "provenance")
    begin = _reply(decoded["begin-v1.json"], ("job", "input_sha256", "provider"))
    _need(begin["job"] == value["job"] and begin["input_sha256"] == value["input_sha256"] and begin["provider"] == "local", "provenance")
    generated = _reply(decoded["generated-v1.json"], ("job", "input", "proposal", "provider"))
    _need(generated["job"] == value["job"] and generated["provider"] == "local" and _equal(generated["input"], INPUT), "provenance")
    _proposal(generated["proposal"])
    review = _reply(decoded["review-v1.json"], ("job", "review_sha256", "input", "proposal", "title", "details"))
    _need(review["job"] == value["job"] and review["review_sha256"] == value["review_sha256"] and review["title"] == TITLE
          and _equal(review["input"], INPUT) and _equal(review["proposal"], generated["proposal"]), "provenance")
    _need(type(review["details"]) is list and 1 <= len(review["details"]) <= 64, "bounds")
    _need(sum(len(_text(row, 1, 2048).encode("utf-8")) for row in review["details"]) <= 16384, "bounds")
    before = _workspace(decoded["workspace-before-v1.json"])
    _need(before["stories"] == [] and _equal(_workspace(decoded["workspace-generated-v1.json"]), before)
          and _equal(_workspace(decoded["workspace-reviewed-v1.json"]), before), "canonical")
    story = "original-" + CREATION_ID
    created = _reply(decoded["create-v1.json"], ("session", "scope", "revision", "created"))
    retry = _reply(decoded["retry-v1.json"], ("session", "scope", "revision", "created"))
    for data in (created, retry):
        _scope(data["scope"], story)
        _need(type(data["session"]) is str and re.fullmatch(r"[A-Za-z0-9_-]{1,128}", data["session"]) is not None
              and type(data["revision"]) is int and data["revision"] == 0, "canonical")
    _need(created["created"] is True and retry["created"] is False, "canonical")
    after = _workspace(decoded["workspace-created-v1.json"])
    expected_after = dict(before, stories=[{"scope": {"story": story, "branch": "main"}, "title": TITLE, "revision": 0, "drafts": 0}])
    _need(_equal(after, expected_after), "canonical")
    snapshot = _reply(decoded["snapshot-created-v1.json"], ("scope", "revision", "rules", "player", "inventory", "receipts"))
    reopened = _reply(decoded["snapshot-reopened-v1.json"], ("scope", "revision", "rules", "player", "inventory", "receipts"))
    _need(_equal(snapshot, reopened), "canonical")
    _scope(snapshot["scope"], story)
    _need(type(snapshot["revision"]) is int and snapshot["revision"] == 0 and snapshot["rules"] == "narrative_v1"
          and snapshot["receipts"] == [], "canonical")
    seed, response_bytes = _archive(decoded["archive-v1.json"], story, generated, review, value["profile"], value["input_sha256"], value["review_sha256"], expected_prompt_version)
    player = _object(snapshot["player"], ("version", "scope", "revision", "observer", "seed_source", "self_state", "facts", "observations", "beliefs"))
    _scope(player["scope"], story)
    _need(type(player["version"]) is int and player["version"] == 1 and type(player["revision"]) is int and player["revision"] == 0
          and player["observer"] == seed["player"] and player["seed_source"] == seed["id"] and player["observations"] == [], "canonical")
    _need(type(seed["actors"]) is dict and seed["player"] in seed["actors"] and _equal(player["self_state"], seed["actors"][seed["player"]]), "canonical")
    _need(type(seed["items"]) is dict and type(snapshot["inventory"]) is dict, "canonical")
    inventory = {key: item for key, item in seed["items"].items() if type(item) is dict and item.get("owner") == seed["player"]}
    _need(_equal(snapshot["inventory"], inventory), "canonical")
    _traces({name: artifacts[name] for name in TRACES}, response_bytes)
    return value


def validate_author(raw: bytes, artifacts: Mapping[str, bytes], prior_import_raw: bytes, *,
                    expected_prompt_version="initial-world-v1") -> dict:
    """Bind a caller-selected prompt cohort; the default stays strictly legacy v1."""
    try:
        expected = _expected_prompt_version(expected_prompt_version)
        return _author(raw, artifacts, prior_import_raw, expected)
    except ProofRefused:
        raise
    except (ValueError, TypeError, KeyError, UnicodeError, OverflowError, RecursionError):
        raise ProofRefused("malformed") from None
