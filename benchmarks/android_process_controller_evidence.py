"""Pure, closed evidence for the four saved-task controller cases.

Invocation, APK/source/ownership binding and private raw retention belong to the
caller. Retirement helper/sidecar semantics require the separate validator.
Copyright 2026 LocalLore contributors. SPDX-License-Identifier: Apache-2.0
"""
import hashlib
import re

from benchmarks.android_process_verification import strict_json_bytes

CASES = ("restore_non_default", "restore_child_branch", "restore_retired_child", "restore_retained_parent")
_COUNTS = dict(zip(CASES[:3], (82, 123, 139)))
_EXPECTED = {"case", "run_id", "product_sha256", "test_sha256", "library_sha256",
             "controller_uid", "product_uid", "signature_sha256"}
_COMMON = {"version", "scope", "case", "run_id", "status", "stage", "reason", "checks", "process_deaths",
           "last_workspace_read", "last_workspace_utf16_length", "controller", "observations", "terminal_observations", "fixture"}
_ORIGIN = {"version", "scope", "case", "controller_uid", "product_uid", "signature_sha256",
           "origin_run_id", "origin_product_sha256"}
_OPS = {"workspace", "branches", "resume", "create", "open", "play_snapshot", "free_text", "submit", "prepare", "commit", "cancel", "other"}
_GAME = ("free_text", "submit", "prepare", "commit", "cancel", "other")
_ZERO = (0, 0, 0, 0, 0, 0)
_SEND = (1, 0, 1, 1, 0, 0)
_SETUP = (1, 0, 1, 1, 0, 2)
_RETAINED_SETUP = (3, 0, 3, 3, 0, 4)
_RECORD = {"version", "scope", "run_id", "pid", "uid", "task_id", "sequence", "process_start_uptime_ms",
           "event", "restored_state", "factory_creations", "hint_present", "hint_sha256", "operations"}
_HELPER = {"version", "scope", "mode", "run_id", "status", "stage", "pid", "uid", "started_uptime_ms",
           "product_sha256", "test_sha256", "library_sha256", "scope_sha256", "commit_attempts",
           "archive_closed", "workspace_closed", "before", "after"}
_ROOT_TEXT = "a8cb95c8145359ad7fadad52d0df311551fab161e1e386a66c87d29fa50a3a55"
_CHILD_TEXT = "f2e4d3340f433d0982360ad585f270c4f2682b2b0969fab8b246bbaee5e81fa3"
_PREFIX = "d0e88260d20e867ca12440419d4c32fed67d07d9ef45da74251c0ab38869cc5a"
_TAIL = "d07a57c72b9f4a81eedf539fbfdc184ba40fa416dc92f67261c9e54e1a55f9e4"
_DRAFT = "4bbd7fc7d2efea6368acc0fd343b01d8fcb5e38a6af3ae4eb847a197e64b54cb"
_HEX = re.compile(r"[0-9a-f]{64}", re.ASCII)
_ID = re.compile(r"[A-Za-z0-9_-]{1,64}", re.ASCII)


class ControllerEvidenceRefused(RuntimeError):
    """A fixed refusal without private input or exception details."""


def _need(value):
    if not value:
        raise ControllerEvidenceRefused("controller_evidence_refused")


def _keys(value, names):
    _need(type(value) is dict and set(value) == set(names))


def _int(value, low=0, high=2**63 - 1):
    _need(type(value) is int and low <= value <= high)
    return value


def _sha(value):
    _need(type(value) is str and _HEX.fullmatch(value) is not None)


def _expected(expected):
    _keys(expected, _EXPECTED)
    _need(type(expected["case"]) is str and expected["case"] in CASES)
    _need(type(expected["run_id"]) is str and re.fullmatch(r"[0-9a-f]{16}", expected["run_id"]) is not None)
    for key in ("product_sha256", "signature_sha256"):
        _sha(expected[key])
    for key in ("test_sha256", "library_sha256"):
        if expected["case"] in CASES[:2] and expected[key] is None:
            continue
        _sha(expected[key])
    for key in ("controller_uid", "product_uid"):
        _int(expected[key], 10_000, 99_999)
    _need(expected["controller_uid"] != expected["product_uid"])


def _scope(value, head):
    _keys(value, ("story", "branch", "head"))
    for key in ("story", "branch"):
        _need(type(value[key]) is str and _ID.fullmatch(value[key]) is not None)
    _int(value["head"], head, head)


def _same_scope(value, original, head):
    _scope(value, head)
    _need(value["story"] == original["story"] and value["branch"] == original["branch"])


def _fixture(f, expected):
    case = expected["case"]
    names = _ORIGIN | {"stories"} if case == CASES[0] else _ORIGIN | {"roots_at_creation", "parent", "child", "parent_text_sha256", "child_draft_sha256"}
    if case == CASES[2]:
        names |= {"fixture_test_sha256"}
    elif case == CASES[3]:
        names = _ORIGIN | {"fixture_test_sha256", "roots_at_creation", "root", "parent", "retained_child", "root_text_sha256",
                           "retained_prefix_sha256", "unreachable_tail_sha256", "parent_draft_sha256"}
    _keys(f, names)
    scopes = ("locallore_process_fixture_v1", "locallore_child_process_fixture_v1",
              "locallore_retired_process_fixture_v1", "locallore_retained_parent_process_fixture_v1")
    _int(f["version"], 1, 1)
    _need(f["scope"] == scopes[CASES.index(case)] and f["case"] == case)
    for key in ("controller_uid", "product_uid"):
        _int(f[key], expected[key], expected[key])
    _need(f["origin_run_id"] == expected["run_id"] and f["origin_product_sha256"] == expected["product_sha256"]
          and f["signature_sha256"] == expected["signature_sha256"])
    roots = f["stories" if case == CASES[0] else "roots_at_creation"]
    _need(type(roots) is list and len(roots) == 2)
    for value in roots:
        _scope(value, 0)
    _need(roots[0]["story"] < roots[1]["story"])
    if case == CASES[0]:
        return roots[1]
    if case in CASES[1:3]:
        _same_scope(f["parent"], roots[1], 1)
        _scope(f["child"], 1)
        _need(f["child"]["story"] == roots[1]["story"] and f["child"]["branch"] != roots[1]["branch"])
        _need(f["parent_text_sha256"] == _ROOT_TEXT and f["child_draft_sha256"] == _CHILD_TEXT)
        if case == CASES[1]:
            return f["child"]
    else:
        _same_scope(f["root"], roots[1], 1)
        _scope(f["parent"], 3)
        _scope(f["retained_child"], 2)
        _need(f["parent"]["story"] == f["retained_child"]["story"] == roots[1]["story"])
        _need(len({f["root"]["branch"], f["parent"]["branch"], f["retained_child"]["branch"]}) == 3)
        _need(f["root_text_sha256"] == _ROOT_TEXT and f["retained_prefix_sha256"] == _PREFIX
              and f["unreachable_tail_sha256"] == _TAIL and f["parent_draft_sha256"] == _DRAFT)
    _need(f["fixture_test_sha256"] == expected["test_sha256"])
    return roots[0]  # The final two product processes settle the unavailable selection on A0.


def _vectors(case):
    return {CASES[0]: (_ZERO, _SEND), CASES[1]: (_SETUP, _SEND),
            CASES[2]: (_SETUP, _ZERO), CASES[3]: (_RETAINED_SETUP, _ZERO)}[case]


def _game(value, wanted):
    _keys(value, _GAME)
    for name, number in zip(_GAME, wanted):
        _int(value[name], number, number)


def _helper_summary(value, expected, with_mode=False):
    names = {"pid", "uid", "started_uptime_ms", "proof_sha256"}
    _keys(value, names | {"mode"} if with_mode else names)
    _int(value["pid"], 1, 2**31 - 1)
    _int(value["uid"], expected["product_uid"], expected["product_uid"])
    _int(value["started_uptime_ms"])
    _sha(value["proof_sha256"])


def _leaf_helper(value, expected, mode):
    # Closed shapes and invocation pins only. Full native state/receipt/sidecar
    # semantics and raw-body correspondence are a separate mandatory check.
    _keys(value, _HELPER)
    _int(value["version"], 1, 1)
    _need(value["scope"] == "locallore_retired_fixture_v1" and value["mode"] == mode
          and value["run_id"] == expected["run_id"] and value["status"] == "passed"
          and value["stage"] == ("PROBE_CLOSED" if mode == "probe" else "RETIRED_CLOSED"))
    _int(value["pid"], 1, 2**31 - 1)
    _int(value["uid"], expected["product_uid"], expected["product_uid"])
    _int(value["started_uptime_ms"])
    for key in ("product_sha256", "test_sha256", "library_sha256"):
        _need(value[key] == expected[key])
    _sha(value["scope_sha256"])
    _int(value["commit_attempts"], int(mode == "retire"), int(mode == "retire"))
    _need(value["archive_closed"] is True and value["workspace_closed"] is True)
    for state in (value["before"], value["after"]):
        _keys(state, ("other_head", "parent_head", "target_head", "target_active"))
        _int(state["other_head"])
        _int(state["parent_head"])
        if state["target_head"] is not None:
            _int(state["target_head"])
        _need(type(state["target_active"]) is bool)


def _proof(proof, expected):
    _expected(expected)
    case = expected["case"]
    names = set(_COMMON)
    if case in CASES[2:]:
        names |= {"load_gate", "last_helper_exit", "retirement_helpers" if case == CASES[2] else "retained_helpers"}
    _keys(proof, names)
    _int(proof["version"], 1, 1)
    _need(proof["scope"] == "locallore_process_controller_v1" and proof["case"] == case
          and proof["run_id"] == expected["run_id"] and proof["status"] == "passed"
          and proof["stage"] == "DONE" and proof["reason"] == "NONE")
    if case in _COUNTS:
        _int(proof["checks"], _COUNTS[case], _COUNTS[case])
    else:
        # Diagnostic positive count only: no source-invented retained-case gold.
        _int(proof["checks"], 1, 4096)
    _int(proof["process_deaths"], 2, 2)
    _need(proof["last_workspace_read"] == "VALID")
    _int(proof["last_workspace_utf16_length"], 1, 4096)
    _keys(proof["controller"], ("pid", "uid", "start"))
    _int(proof["controller"]["pid"], 1, 2**31 - 1)
    _int(proof["controller"]["uid"], expected["controller_uid"], expected["controller_uid"])
    _int(proof["controller"]["start"])
    target = _fixture(proof["fixture"], expected)
    observations = proof["observations"]
    _need(type(observations) is list and len(observations) == 3)
    for index, observation in enumerate(observations):
        _keys(observation, ("pid", "uid", "start", "task", "restored", "factory"))
        _int(observation["pid"], 1, 2**31 - 1)
        _int(observation["uid"], expected["product_uid"], expected["product_uid"])
        _int(observation["start"])
        _int(observation["task"], 0, 2**31 - 1)
        _int(observation["factory"], 1, 1)
        _need(observation["restored"] is (index > 0))
    _need(len({o["pid"] for o in observations}) == 3 and len({o["start"] for o in observations}) == 3
          and len({o["task"] for o in observations}) == 1
          and proof["controller"]["pid"] not in {o["pid"] for o in observations})
    terminals = proof["terminal_observations"]
    _need(type(terminals) is list and len(terminals) == 2)
    for terminal, observation, vector in zip(terminals, observations, _vectors(case)):
        _keys(terminal, ("pid", "start", "task", "saved_sequence", "commands_sequence", "saved_game", "commands_game"))
        for key in ("pid", "start", "task"):
            _int(terminal[key], observation[key], observation[key])
        _int(terminal["commands_sequence"], 1, 65536)
        _int(terminal["saved_sequence"], 1, 65536)
        # One synchronized counter assigns a distinct sequence to every write.
        # A read-only command can finish after the after-super save; gameplay
        # equality below, rather than file write order, rules out automatic work.
        _need(terminal["commands_sequence"] != terminal["saved_sequence"])
        _game(terminal["saved_game"], vector)
        _game(terminal["commands_game"], vector)
    if case in CASES[2:]:
        _int(proof["last_helper_exit"], 0, 0)
        _helper_summary(proof["load_gate"], expected)
        if case == CASES[2]:
            helpers = proof["retirement_helpers"]
            _need(type(helpers) is list and len(helpers) == 2)
            for value, mode in zip(helpers, ("probe", "retire")):
                _leaf_helper(value, expected, mode)
        else:
            helpers = proof["retained_helpers"]
            _need(type(helpers) is list and len(helpers) == 2)
            for value, mode in zip(helpers, ("probe", "retire")):
                _helper_summary(value, expected, with_mode=True)
                _need(value["mode"] == mode)
    return target


def validate_controller_result(raw: bytes, expected: dict) -> dict:
    """Return the original parsed proof for one quiet custom-controller finish."""
    try:
        _need(type(raw) is bytes and 0 < len(raw) <= 4160)
        match = re.fullmatch(rb"INSTRUMENTATION_RESULT: proof=([^\r\n]+)\r?\nINSTRUMENTATION_CODE: -1\r?\n", raw)
        _need(match is not None)
        proof = strict_json_bytes(match.group(1), 4096)
        _proof(proof, expected)
        return proof
    except Exception:
        raise ControllerEvidenceRefused("controller_evidence_refused") from None


def validate_product_records(proof: dict, records: dict[str, bytes], expected: dict) -> dict:
    """Validate only the final three fixed leaves, not arbitrary product files."""
    try:
        target = _proof(proof, expected)
        _keys(records, ("created", "saved", "commands"))
        hint = hashlib.sha256(("1\n" + target["story"] + "\n" + target["branch"] + "\n").encode("utf-8")).hexdigest()
        parsed = {}
        for name, event, index in (("created", "created", 2), ("saved", "saved_after_super", 1), ("commands", "command", 2)):
            record = strict_json_bytes(records[name], 4096)
            _keys(record, _RECORD)
            _int(record["version"], 1, 1)
            _need(record["scope"] == "locallore_process_verify_v1" and record["run_id"] == expected["run_id"]
                  and record["event"] == event and record["restored_state"] is True
                  and record["hint_present"] is True and record["hint_sha256"] == hint)
            observation = proof["observations"][index]
            for key, source in (("pid", "pid"), ("uid", "uid"), ("task_id", "task"), ("process_start_uptime_ms", "start")):
                _int(record[key], observation[source], observation[source])
            _int(record["factory_creations"], 1, 1)
            _int(record["sequence"], 1, 65536)
            _keys(record["operations"], _OPS)
            for value in record["operations"].values():
                _int(value, 0, 4096)
            _int(record["operations"]["create"], 0, 0)
            wanted = _vectors(expected["case"])[1] if name == "saved" else _ZERO
            for key, value in zip(_GAME, wanted):
                _int(record["operations"][key], value, value)
            if name == "saved":
                _int(record["sequence"], proof["terminal_observations"][1]["saved_sequence"],
                     proof["terminal_observations"][1]["saved_sequence"])
            parsed[name] = record
        _need(parsed["commands"]["sequence"] > parsed["created"]["sequence"])
        _need(all(parsed["commands"]["operations"][key] >= parsed["created"]["operations"][key]
                  for key in _OPS))
        return parsed
    except Exception:
        raise ControllerEvidenceRefused("controller_evidence_refused") from None
