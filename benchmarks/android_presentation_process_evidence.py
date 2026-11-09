"""Closed v3 presentation-process receipts; no device or file operations.

These synthetic-checkable receipts are source-bound observations, not proof of
an invocation, APK identity, process death, or independent authentication. The
caller must separately retain and qualify those acquisition records.
Copyright 2026 LocalLore contributors. SPDX-License-Identifier: Apache-2.0
"""
import hashlib
import re

from benchmarks.android_process_verification import strict_json_bytes

PROBE_CAP = 4096
RESULT_CAP = 32768
CASE = "restore_player_presentation"
PROBE_SCOPE = "locallore_presentation_process_verify_v3"
RESULT_SCOPE = "locallore_presentation_process_controller_v3"
FIXTURE_SCOPE = "locallore_presentation_process_fixture_v3"
OPS = ("workspace", "branches", "resume", "create", "open", "play_snapshot",
       "free_text", "submit", "prepare", "commit", "cancel", "other",
       "story_template", "create_named", "play_presentation_v2")
GAME = ("free_text", "submit", "prepare", "commit", "cancel", "other")
READS = ("resume", "play_presentation_v2", "play_snapshot")
CREATION = ("create", "create_named")
_ZERO = (0, 0, 0, 0, 0, 0)
_SEND = (1, 0, 1, 1, 0, 0)
_EXPECTED = {"run_id", "product_uid", "controller_uid", "product_sha256", "signature_sha256"}
_RECORD = {"version", "scope", "run_id", "pid", "uid", "task_id", "sequence",
           "process_start_uptime_ms", "event", "restored_state", "factory_creations",
           "hint_present", "hint_sha256", "operations"}
_RESULT = {"version", "scope", "case", "run_id", "status", "stage", "reason", "checks",
           "process_deaths", "last_workspace_read", "last_workspace_utf16_length", "controller",
           "observations", "terminal_observations", "fixture", "presentation_reads"}
_HEX64 = re.compile(r"[0-9a-f]{64}", re.ASCII)


class PresentationEvidenceRefused(RuntimeError):
    """Fixed refusal without private values or exception details."""


def _need(condition):
    if not condition:
        raise PresentationEvidenceRefused("presentation_evidence_refused")


def _keys(value, names):
    _need(type(value) is dict and set(value) == set(names))


def _int(value, low=0, high=2**63 - 1):
    _need(type(value) is int and low <= value <= high)
    return value


def _hex(value, pattern=_HEX64):
    _need(type(value) is str and pattern.fullmatch(value) is not None)


def _expected(value):
    _keys(value, _EXPECTED)
    _hex(value["run_id"], re.compile(r"[0-9a-f]{16}", re.ASCII))
    for name in ("product_sha256", "signature_sha256"):
        _hex(value[name])
    for name in ("product_uid", "controller_uid"):
        _int(value[name], 10000, 99999)
    _need(value["product_uid"] != value["controller_uid"])


def _parse(raw, cap):
    _need(type(raw) is bytes and 0 < len(raw) <= cap)
    return strict_json_bytes(raw, cap)


def _probe(raw, expected, leaf):
    _expected(expected)
    _need(type(leaf) is str and leaf in ("created", "saved", "commands"))
    value = _parse(raw, PROBE_CAP)
    _keys(value, _RECORD)
    _int(value["version"], 3, 3)
    _need(value["scope"] == PROBE_SCOPE and value["run_id"] == expected["run_id"])
    _need(value["event"] == {"created": "created", "saved": "saved_after_super", "commands": "command"}[leaf])
    _int(value["pid"], 1, 2**31 - 1)
    _int(value["uid"], expected["product_uid"], expected["product_uid"])
    _int(value["task_id"], 0, 2**31 - 1)
    _int(value["sequence"], 1, 65536)
    _int(value["process_start_uptime_ms"])
    _int(value["factory_creations"], 0, 16)
    _need(type(value["restored_state"]) is bool and type(value["hint_present"]) is bool)
    if value["hint_present"]:
        _hex(value["hint_sha256"])
    else:
        _need(value["hint_sha256"] is None)
    _keys(value["operations"], OPS)
    for count in value["operations"].values():
        _int(count, 0, 4096)
    return value


def validate_probe(raw: bytes, expected: dict, leaf: str) -> dict:
    """Decode exactly one v3 leaf; this alone makes no lifecycle claim."""
    try:
        return _probe(raw, expected, leaf)
    except Exception:
        raise PresentationEvidenceRefused("presentation_evidence_refused") from None


def _vector(value, keys, wanted=None):
    _keys(value, keys)
    for index, name in enumerate(keys):
        _int(value[name], 0, 4096)
        if wanted is not None:
            _int(value[name], wanted[index], wanted[index])


def _reads(value):
    _vector(value, READS)
    _need(value["resume"] > 0 and value["play_presentation_v2"] > 0 and value["play_snapshot"] == 0)


def _creation(value, named):
    _vector(value, CREATION, (0, named))


def _at_least(later, earlier, keys):
    _need(all(later[key] >= earlier[key] for key in keys))


def _identity(value, observation):
    for key in ("pid", "start", "task"):
        _int(value[key], observation[key], observation[key])


def _fixture(value, expected):
    _keys(value, ("version", "scope", "case", "controller_uid", "product_uid", "signature_sha256",
                  "origin_run_id", "origin_product_sha256", "stories"))
    _int(value["version"], 3, 3)
    _need(value["scope"] == FIXTURE_SCOPE and value["case"] == CASE)
    for name in ("controller_uid", "product_uid"):
        _int(value[name], expected[name], expected[name])
    _need(value["signature_sha256"] == expected["signature_sha256"] and
          value["origin_run_id"] == expected["run_id"] and
          value["origin_product_sha256"] == expected["product_sha256"])
    stories = value["stories"]
    _need(type(stories) is list and len(stories) == 2)
    for story in stories:
        _keys(story, ("story", "branch", "head"))
        for name in ("story", "branch"):
            _hex(story[name], re.compile(r"[A-Za-z0-9_-]{1,64}", re.ASCII))
        _int(story["head"], 0, 0)
    _need(stories[0]["story"] < stories[1]["story"])
    return stories[1]


def _result(raw, expected, records):
    _expected(expected)
    _need(type(raw) is bytes and 0 < len(raw) <= RESULT_CAP)
    frame = re.fullmatch(rb"INSTRUMENTATION_RESULT: proof=([^\r\n]+)(\r?\n)INSTRUMENTATION_CODE: -1\2", raw)
    _need(frame is not None)
    value = _parse(frame.group(1), RESULT_CAP)
    _keys(value, _RESULT)
    _int(value["version"], 3, 3)
    _need(value["scope"] == RESULT_SCOPE and value["case"] == CASE and value["run_id"] == expected["run_id"])
    _need(value["status"] == "passed" and value["stage"] == "DONE" and value["reason"] == "NONE")
    _int(value["checks"], 1, 4096)  # Diagnostic, never a substitute for the joins below.
    _int(value["process_deaths"], 2, 2)
    _need(value["last_workspace_read"] == "VALID")
    _int(value["last_workspace_utf16_length"], 1, 4096)
    controller = value["controller"]
    _keys(controller, ("pid", "uid", "start"))
    _int(controller["pid"], 1, 2**31 - 1)
    _int(controller["uid"], expected["controller_uid"], expected["controller_uid"])
    _int(controller["start"])
    target = _fixture(value["fixture"], expected)
    observations = value["observations"]
    _need(type(observations) is list and len(observations) == 3)
    for index, observation in enumerate(observations):
        _keys(observation, ("pid", "uid", "start", "task", "restored", "factory"))
        _int(observation["pid"], 1, 2**31 - 1)
        _int(observation["uid"], expected["product_uid"], expected["product_uid"])
        _int(observation["start"])
        _int(observation["task"], 0, 2**31 - 1)
        _int(observation["factory"], 1, 1)
        _need(observation["restored"] is (index > 0))
    _need(len({o["pid"] for o in observations}) == 3 and
          controller["pid"] not in {o["pid"] for o in observations} and
          len({o["task"] for o in observations}) == 1 and
          observations[0]["start"] < observations[1]["start"] < observations[2]["start"])
    terminals = value["terminal_observations"]
    _need(type(terminals) is list and len(terminals) == 2)
    for index, terminal in enumerate(terminals):
        _keys(terminal, ("pid", "start", "task", "saved_sequence", "commands_sequence", "saved_game", "commands_game",
                         "saved_creation", "commands_creation", "saved_reads", "commands_reads"))
        _identity(terminal, observations[index])
        for name in ("saved_sequence", "commands_sequence"):
            _int(terminal[name], 1, 65536)
        _need(terminal["saved_sequence"] != terminal["commands_sequence"])
        for name in ("saved_game", "commands_game"):
            _vector(terminal[name], GAME, _ZERO if index == 0 else _SEND)
        for name in ("saved_creation", "commands_creation"):
            _creation(terminal[name], 2 if index == 0 else 0)
        for name in ("saved_reads", "commands_reads"):
            _reads(terminal[name])
        earlier, later = (("saved_reads", "commands_reads") if terminal["saved_sequence"] < terminal["commands_sequence"]
                          else ("commands_reads", "saved_reads"))
        _at_least(terminal[later], terminal[earlier], READS)
    witnesses = value["presentation_reads"]
    _need(type(witnesses) is list and len(witnesses) == 2)
    for index, witness in enumerate(witnesses):
        _keys(witness, ("pid", "start", "task", "before_sequence", "after_sequence", "resume_before", "resume_after",
                        "presentation_before", "presentation_after", "legacy_before", "legacy_after", "before_game",
                        "after_game", "before_creation", "after_creation"))
        _identity(witness, observations[index + 1])
        for name in ("before_sequence", "after_sequence"):
            _int(witness[name], 1, 65536)
        _need(witness["before_sequence"] < witness["after_sequence"])
        for name in ("resume_before", "resume_after", "presentation_before", "presentation_after", "legacy_before", "legacy_after"):
            _int(witness[name], 0, 4096)
        _need(witness["resume_before"] < witness["resume_after"] and
              witness["presentation_before"] < witness["presentation_after"] and
              witness["legacy_before"] == witness["legacy_after"] == 0)
        for name in ("before_game", "after_game"):
            _vector(witness[name], GAME, _ZERO)
        for name in ("before_creation", "after_creation"):
            _creation(witness[name], 0)
    witness = witnesses[0]
    for phase in ("saved", "commands"):
        _need(terminals[1][phase + "_sequence"] > witness["after_sequence"])
        _need(terminals[1][phase + "_reads"]["resume"] >= witness["resume_after"] and
              terminals[1][phase + "_reads"]["play_presentation_v2"] >= witness["presentation_after"])
    _keys(records, ("created", "saved", "commands"))
    parsed = {name: _probe(records[name], expected, name) for name in ("created", "saved", "commands")}
    hint = hashlib.sha256(("1\n" + target["story"] + "\n" + target["branch"] + "\n").encode("utf-8")).hexdigest()
    for name, record in parsed.items():
        observation = observations[1 if name == "saved" else 2]
        for key, source in (("pid", "pid"), ("uid", "uid"), ("task_id", "task"), ("process_start_uptime_ms", "start")):
            _int(record[key], observation[source], observation[source])
        _int(record["factory_creations"], 1, 1)
        _need(record["restored_state"] is True and record["hint_present"] is True and record["hint_sha256"] == hint)
        ops = record["operations"]
        _vector({key: ops[key] for key in GAME}, GAME, _SEND if name == "saved" else _ZERO)
        _creation({key: ops[key] for key in CREATION}, 0)
        if name == "created":
            # The Activity receipt can precede asynchronous initialization IO.
            # Later witnesses must establish actual progress in this process.
            _need(ops["play_snapshot"] == 0)
        else:
            _reads({key: ops[key] for key in READS})
        if name == "saved":
            _int(record["sequence"], terminals[1]["saved_sequence"], terminals[1]["saved_sequence"])
            for keys, suffix in ((GAME, "game"), (CREATION, "creation"), (READS, "reads")):
                _need(all(ops[key] == terminals[1]["saved_" + suffix][key] for key in keys))
    final = witnesses[1]
    _need(parsed["created"]["sequence"] <= final["before_sequence"] < final["after_sequence"] <= parsed["commands"]["sequence"])
    _at_least(parsed["commands"]["operations"], parsed["created"]["operations"], OPS)
    for op, prefix in (("resume", "resume"), ("play_presentation_v2", "presentation"), ("play_snapshot", "legacy")):
        created_count = parsed["created"]["operations"][op]
        commands_count = parsed["commands"]["operations"][op]
        _need(created_count <= final[prefix + "_before"] < final[prefix + "_after"] <= commands_count
              if op != "play_snapshot" else created_count == final[prefix + "_before"] == final[prefix + "_after"] == commands_count == 0)
        if parsed["created"]["sequence"] == final["before_sequence"]:
            _need(created_count == final[prefix + "_before"])
        if parsed["commands"]["sequence"] == final["after_sequence"]:
            _need(commands_count == final[prefix + "_after"])
    return value


def validate_result(raw: bytes, expected: dict, product_records: dict) -> dict:
    """Validate one v3 JSON result plus the final three original probe leaves.

    Exactly one quiet instrumentation finish with its closed v3 JSON body is
    accepted. Acquisition/cleanup is a separate gate; no legacy result is retagged.
    """
    try:
        return _result(raw, expected, product_records)
    except Exception:
        raise PresentationEvidenceRefused("presentation_evidence_refused") from None
