"""Pure bounded consistency checks for passive original-AUTHOR restart proof.

Source, target, JUnit and actual process-death authentication remain separate.
This module reads no files and never launches a provider, process or device.
Copyright 2026 LocalLore contributors. SPDX-License-Identifier: Apache-2.0
"""
from collections.abc import Mapping
import copy
import re

from benchmarks import original_author_model_proof as author

SCOPE = "original_author_external_restart_v1"
METHOD = "recordsOriginalAuthorAfterExternalRestartWithoutInference"
CLASS = "org.locallore.app.OriginalAuthorRestartInstrumentedTest"
MAX_PROOF = 32768
MAX_ARTIFACT = 1024 * 1024
MAX_COLLECTED = 2 * MAX_ARTIFACT
RECORDS = (
    "workspace-before-v1.json", "recover-v1.json", "snapshot-v1.json",
    "retry-v1.json", "workspace-after-v1.json", "archive-v1.json",
)
KEYS = (
    "version", "scope", "status", "stage", "reason", "process", "package",
    "elapsed_ms", "import_proof_sha256", "author_proof_sha256", "records",
    "pending_before", "pending_after", "workspace_closed", "archive_closed",
)
REASONS = frozenset(("malformed", "shape", "bounds", "binding", "incomplete", "identity", "canonical", "baseline"))


class RestartRefused(ValueError):
    """Fixed categories only; never echo an artifact, path or original error."""
    def __init__(self, reason="malformed"):
        self.reason = reason if reason in REASONS else "malformed"
        super().__init__(self.reason)


def _need(value, reason):
    if not value:
        raise RestartRefused(reason)


def _creation(raw, original):
    data = author._reply(author._json(raw), ("session", "scope", "revision", "created"))
    _need(type(data["session"]) is str and re.fullmatch(r"[A-Za-z0-9_-]{1,128}", data["session"]) is not None,
          "canonical")
    _need(author._equal(data["scope"], original["scope"])
          and type(data["revision"]) is int and data["revision"] == 0
          and data["created"] is False, "canonical")
    return data


def _validate(raw, artifacts, author_raw, author_artifacts, import_raw, expected_prompt_version):
    # A caller cannot replace the original baseline verdict or materialize a
    # supposedly equivalent Seed here. Keep the original cohort-selected reader.
    try:
        baseline = author.validate_author(author_raw, author_artifacts, import_raw,
                                          expected_prompt_version=expected_prompt_version)
    except author.ProofRefused:
        raise RestartRefused("baseline") from None
    value = author._json(raw, MAX_PROOF)
    author._object(value, KEYS)
    _need(type(value["version"]) is int and value["version"] == 1 and value["scope"] == SCOPE, "identity")
    _need(value["status"] == "completed" and value["stage"] == "completed" and value["reason"] is None, "incomplete")
    _need(value["package"] == author.PACKAGE, "identity")
    process = author._process(value["process"])
    _need(process["start_elapsed_ms"] > 0
          and process["uid"] == baseline["process"]["uid"]
          and process["start_elapsed_ms"] > baseline["process"]["start_elapsed_ms"], "identity")
    author._int(value["elapsed_ms"], 0, 180000)
    _need(author._digest(value["import_proof_sha256"]) == author._sha(import_raw)
          and author._digest(value["author_proof_sha256"]) == author._sha(author_raw), "binding")
    _need(value["pending_before"] is False and value["pending_after"] is False
          and value["workspace_closed"] is True and value["archive_closed"] is True, "incomplete")
    records = author._object(value["records"], RECORDS, "binding")
    _need(isinstance(artifacts, Mapping) and set(artifacts) == set(RECORDS), "binding")
    _need(all(type(b) is bytes and 0 < len(b) <= MAX_ARTIFACT for b in artifacts.values())
          and sum(len(b) for b in artifacts.values()) <= MAX_COLLECTED, "bounds")
    for name in RECORDS:
        author._binding(records[name], artifacts[name])
    before = author._workspace(author._json(artifacts["workspace-before-v1.json"]))
    after = author._workspace(author._json(artifacts["workspace-after-v1.json"]))
    expected = author._workspace(author._json(author_artifacts["workspace-created-v1.json"]))
    _need(author._equal(before, expected) and author._equal(after, expected), "canonical")
    original = author._reply(author._json(author_artifacts["create-v1.json"]), ("session", "scope", "revision", "created"))
    _creation(artifacts["recover-v1.json"], original)
    _creation(artifacts["retry-v1.json"], original)
    snapshot_keys = ("scope", "revision", "rules", "player", "inventory", "receipts")
    snapshot = author._reply(author._json(artifacts["snapshot-v1.json"]), snapshot_keys)
    original_snapshot = author._reply(author._json(author_artifacts["snapshot-created-v1.json"]), snapshot_keys)
    _need(author._equal(snapshot, original_snapshot), "canonical")
    # Exact native export bytes cover the full canonical world, including facts
    # hidden from PLAYER. Never rebuild a convenient archive from its projection.
    _need(artifacts["archive-v1.json"] == author_artifacts["archive-v1.json"], "canonical")
    return copy.deepcopy(value)


def validate_restart(raw: bytes, artifacts: Mapping[str, bytes], author_raw: bytes,
                     author_artifacts: Mapping[str, bytes], import_raw: bytes, *,
                     expected_prompt_version="initial-world-v1.1") -> dict:
    """Validate completed bytes only; metadata never proves an OS death or SDK run."""
    try:
        return _validate(raw, artifacts, author_raw, author_artifacts, import_raw, expected_prompt_version)
    except RestartRefused:
        raise
    except author.ProofRefused as error:
        raise RestartRefused(error.reason) from None
    except (ValueError, TypeError, KeyError, UnicodeError, OverflowError, RecursionError):
        raise RestartRefused("malformed") from None
