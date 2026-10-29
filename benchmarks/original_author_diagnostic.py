"""Bound private diagnostic bytes to the original AUTHOR proof; never accept a world.

No IO, inference, repair or native validation runs here. Device/SDK/CLI execution
and source provenance require separately closed host evidence.
Copyright 2026 LocalLore contributors. SPDX-License-Identifier: Apache-2.0
"""
from collections.abc import Mapping
from benchmarks import original_author_model_proof as p

FILES = ("input-v1.json", "response-v1.bin", "generated-v1.json", "workspace-before-v1.json", "workspace-after-v1.json")
MAX_MANIFEST = 32768
MAX_TOTAL = 1024 * 1024
CAPS = {name: 262144 for name in FILES}
CAPS.update({"input-v1.json": 4096, "response-v1.bin": 8192})
NATIVE_REASONS = frozenset((
    "invalid_input", "input_too_large", "proposal_too_large", "proposal_encoding", "proposal_version",
    "location_count", "character_count", "player_location", "route_count", "fact_count", "belief_count",
    "possession_count", "location_names", "character_names", "possession_names", "location_description",
    "cast_names", "character_description", "character_location", "character_known_by", "character_self_knowledge",
    "route_self", "route_reference", "route_duplicate", "route_reachability", "fact_text", "fact_known_by",
    "fact_discovery_location", "fact_duplicate", "belief_believer", "belief_text", "belief_duplicate",
    "possession_description", "possession_owner", "possession_return_to",
))
MALFORMED_REASONS = frozenset(("input_json", "response_json", "input_read", "response_read", "input_bytes", "response_bytes"))
REASONS = p.REASONS | {"native"}
AUTHOR_KEYS = ("version", "scope", "status", "stage", "reason", "process", "package", "prior_import_sha256", "profile", "job", "input_sha256", "review_sha256", "creation_id", "records", "traces", "elapsed_ms")


class DiagnosticRefused(ValueError):
    def __init__(self, reason="malformed"):
        self.reason = reason if reason in REASONS else "malformed"
        super().__init__(self.reason)


def _need(value, reason):
    if not value:
        raise DiagnosticRefused(reason)


def _diagnostic(raw, files, author_raw, author_artifacts, prior_import_raw, expected_prompt_version):
    value = p._object(p._json(raw, MAX_MANIFEST), ("version", "scope", "status", "reason", "feature_acceptance", "input_sha256", "author_proof_sha256", "capture", "files"))
    _need(type(value["version"]) is int and value["version"] == 1 and value["scope"] == "original_author_diagnostic_v1", "identity")
    _need(value["status"] == "completed" and value["reason"] is None and value["feature_acceptance"] is False, "incomplete")
    _need(isinstance(files, Mapping) and set(files) == set(FILES), "binding")
    _need(all(type(files[n]) is bytes and 0 < len(files[n]) <= CAPS[n] for n in FILES)
          and sum(len(b) for b in files.values()) <= MAX_TOTAL, "bounds")
    bindings = p._object(value["files"], FILES, "binding")
    for name in FILES:
        p._binding(bindings[name], files[name])
    files["response-v1.bin"].decode("utf-8", "strict")
    capture = p._object(value["capture"], ("state", "calls", "response"))
    _need(capture["state"] == "recorded" and type(capture["calls"]) is int and capture["calls"] == 1, "incomplete")
    _need(p._equal(capture["response"], bindings["response-v1.bin"]), "binding")
    _need(p._digest(value["input_sha256"]) == p._sha(files["input-v1.json"])
          == p._sha(p._encode(p.INPUT)) and p._equal(p._json(files["input-v1.json"]), p.INPUT), "provenance")
    _need(p._digest(value["author_proof_sha256"]) == p._sha(author_raw), "binding")
    author = p._object(p._json(author_raw), AUTHOR_KEYS)
    _need(type(author["version"]) is int and author["version"] == 1 and author["scope"] == "original_author_model_v1"
          and author["package"] == p.PACKAGE, "identity")
    _need((author["status"] == "completed" and author["stage"] == "completed" and author["reason"] is None)
          or (author["status"] == "refused" and author["stage"] in ("generate", "review", "create", "reopen", "archive")
              and author["reason"] == "checks_failed"), "incomplete")
    prior = p.validate_import(prior_import_raw)
    process = p._process(author["process"])
    _need(process["uid"] == prior["process"]["uid"] and process["start_elapsed_ms"] > prior["process"]["start_elapsed_ms"], "identity")
    _need(p._digest(author["prior_import_sha256"]) == p._sha(prior_import_raw), "binding")
    p._int(author["elapsed_ms"], 0, 180000)
    p._profile(author["profile"])
    _need(type(author["job"]) is str and author["job"].startswith("initial-") and len(author["job"]) <= 32
          and author["job"][8:].isascii() and author["job"][8:].isdigit() and not author["job"][8:].startswith("0"), "identity")
    _need(author["input_sha256"] == value["input_sha256"], "provenance")
    records = p._object(author["records"], p.RECORDS, "binding")
    traces = p._object(author["traces"], p.TRACES, "binding")
    expected = {name for name in p.RECORDS if records[name] is not None} | {name for name in p.TRACES if traces[name] is not None}
    _need(isinstance(author_artifacts, Mapping) and set(author_artifacts) == expected, "binding")
    _need(all(type(b) is bytes and 0 < len(b) <= p.MAX_ARTIFACT for b in author_artifacts.values())
          and sum(len(b) for b in author_artifacts.values()) <= p.MAX_COLLECTED, "bounds")
    for name in expected:
        p._binding((records if name in p.RECORDS else traces)[name], author_artifacts[name])
    if author["status"] == "completed":
        p.validate_author(author_raw, author_artifacts, prior_import_raw,
                          expected_prompt_version=expected_prompt_version)
    for name in ("input-v1.json", "generated-v1.json", "workspace-before-v1.json"):
        _need(name in author_artifacts and files[name] == author_artifacts[name], "binding")
    _need("begin-v1.json" in author_artifacts and set(p.TRACES) <= set(author_artifacts), "incomplete")
    begin = p._reply(p._json(author_artifacts["begin-v1.json"]), ("job", "input_sha256", "provider"))
    _need(begin["job"] == author["job"] and begin["input_sha256"] == value["input_sha256"] and begin["provider"] == "local", "provenance")
    before = p._workspace(p._json(files["workspace-before-v1.json"]))
    after = p._workspace(p._json(files["workspace-after-v1.json"]))
    _need(before["stories"] == [] and p._equal(before, after), "canonical")
    reply = p._json(files["generated-v1.json"])
    if reply.get("status") == "rejected":
        p._object(reply, ("version", "status", "error"))
        _need(type(reply["version"]) is int and reply["version"] == 1 and reply["error"] in ("InvalidProposal", "Malformed"), "native")
        _need(author["status"] == "refused" and author["stage"] == "generate" and author["reason"] == "checks_failed"
              and author["review_sha256"] is None and author["creation_id"] is None, "incomplete")
        _need({n for n in p.RECORDS if records[n] is not None} == {"input-v1.json", "begin-v1.json", "generated-v1.json", "workspace-before-v1.json"}, "incomplete")
    else:
        generated = p._reply(reply, ("job", "input", "proposal", "provider"))
        _need(generated["job"] == author["job"] and generated["provider"] == "local"
              and p._equal(generated["input"], p.INPUT), "provenance")
        _need(p._equal(p._json(files["response-v1.bin"], 8192), generated["proposal"]), "binding")
    p._traces({name: author_artifacts[name] for name in p.TRACES}, len(files["response-v1.bin"]))
    return value


def validate_diagnostic(raw, files, author_raw, author_artifacts, prior_import_raw, *,
                        expected_prompt_version="initial-world-v1"):
    """Bind captured bytes/known trace observations; never qualify device or creation."""
    try:
        expected = p._expected_prompt_version(expected_prompt_version)
        return _diagnostic(raw, files, author_raw, author_artifacts, prior_import_raw, expected)
    except DiagnosticRefused:
        raise
    except p.ProofRefused as error:
        raise DiagnosticRefused(error.reason) from None
    except (ValueError, TypeError, KeyError, UnicodeError, OverflowError, RecursionError, AttributeError):
        raise DiagnosticRefused("malformed") from None


def validate_native_report(report_raw, raw, files, author_raw, author_artifacts, prior_import_raw, *,
                           expected_prompt_version="initial-world-v1"):
    """Bind an independently executed native diagnostic; do not repeat engine rules."""
    try:
        validate_diagnostic(raw, files, author_raw, author_artifacts, prior_import_raw,
                            expected_prompt_version=expected_prompt_version)
        report = p._object(p._json(report_raw, MAX_MANIFEST), ("version", "scope", "input_sha256", "response_sha256", "input_bytes", "response_bytes", "status", "category", "error"))
        _need(type(report["version"]) is int and report["version"] == 1 and report["scope"] == "original_author_native_diagnostic_v1", "identity")
        for stem, name in (("input", "input-v1.json"), ("response", "response-v1.bin")):
            p._int(report[stem + "_bytes"], 1, CAPS[name], "binding")
            _need(report[stem + "_bytes"] == len(files[name]) and p._digest(report[stem + "_sha256"]) == p._sha(files[name]), "binding")
        reply = p._json(files["generated-v1.json"])
        if report["status"] == "valid":
            _need(report["category"] is None and report["error"] is None and reply["status"] == "ok", "native")
        elif report["status"] == "rejected":
            _need(report["category"] in NATIVE_REASONS and reply["status"] == "rejected", "native")
            expected = "InvalidInput" if report["category"] in ("invalid_input", "proposal_encoding") else "TooLarge" if report["category"] in ("input_too_large", "proposal_too_large") else "InvalidProposal"
            _need(report["error"] == expected == reply["error"], "native")
        elif report["status"] == "malformed":
            # This complete fixed-input capture can only bind a response-JSON refusal;
            # read/bounds/input failures remain valid CLI negatives, not diagnosed runs.
            _need(report["category"] == "response_json" and report["error"] == "Malformed"
                  and reply["status"] == "rejected" and reply["error"] == "Malformed", "native")
        else:
            raise DiagnosticRefused("native")
        return report
    except DiagnosticRefused:
        raise
    except p.ProofRefused as error:
        raise DiagnosticRefused(error.reason) from None
    except (ValueError, TypeError, KeyError, UnicodeError, OverflowError, RecursionError, AttributeError):
        raise DiagnosticRefused("malformed") from None
