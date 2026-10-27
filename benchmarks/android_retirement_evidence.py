"""Pure validation of private, source-bound scripted retirement evidence.

Copyright 2026 LocalLore contributors. SPDX-License-Identifier: Apache-2.0

No native/SDK/filesystem operations. A passed result is evidence consistency,
not an independent process observation or hidden-world/canonical authority.
The caller first validates the complete controller result and both transport
footers. This module receives the original quiet helper body, including LF.
"""
from __future__ import annotations

import hashlib
import re

from benchmarks.android_process_verification import strict_json_bytes


class RetirementEvidenceRefused(RuntimeError):
    pass


HELPER_CAP = 4096
SIDECAR_CAP = 262144
SIDECARS = ("probe-before-v1.json", "probe-after-v1.json",
            "retire-before-v1.json", "retire-after-v1.json")
MODES = ("load", "probe", "retire")
EXPECTED = frozenset(("case", "run_id", "product_sha256", "test_sha256", "library_sha256",
                      "controller_uid", "product_uid", "signature_sha256"))
HELPER = frozenset(("version", "scope", "mode", "run_id", "status", "stage", "pid", "uid",
                    "started_uptime_ms", "product_sha256", "test_sha256", "library_sha256",
                    "scope_sha256", "commit_attempts", "archive_closed", "workspace_closed", "before", "after"))
ROOT_SHA = "a8cb95c8145359ad7fadad52d0df311551fab161e1e386a66c87d29fa50a3a55"
PREFIX_SHA = "d0e88260d20e867ca12440419d4c32fed67d07d9ef45da74251c0ab38869cc5a"
TAIL_TEXT = "SYNTHETIC unreachable-parent tail: Mira, this belongs only to the parent after the child fork."
GAME = ("free_text", "submit", "prepare", "commit", "cancel", "other")


def _need(ok, reason):
    if not ok:
        raise RetirementEvidenceRefused(reason)


def _keys(value, keys):
    _need(type(value) is dict and value.keys() == set(keys), "shape")


def _integer(value, low=0, high=2**63 - 1):
    _need(type(value) is int and low <= value <= high, "integer")
    return value


def _string(value):
    _need(type(value) is str, "string")
    try:
        value.encode("utf-8", "strict")
    except UnicodeError:
        raise RetirementEvidenceRefused("unicode") from None
    return value


def _hex(value):
    _need(type(value) is str and re.fullmatch("[0-9a-f]{64}", value) is not None, "digest")
    return value


def _id(value):
    _need(type(value) is str and re.fullmatch("[A-Za-z0-9_-]{1,64}", value) is not None, "identifier")
    return value


def _sha(raw):
    return hashlib.sha256(raw).hexdigest()


def _json(raw, cap):
    try:
        return strict_json_bytes(raw, cap)
    except (RuntimeError, ValueError, UnicodeError, RecursionError):
        raise RetirementEvidenceRefused("json") from None


def _tree(value, depth=0):
    """Actual play_snapshot v1 has integral numbers; no float normalization.

    Java's helper bounds depth at32. Reject unpaired escaped surrogates too:
    Java UTF8 replacement must never become apparent original-byte equality.
    """
    _need(depth <= 32, "depth")
    if type(value) is dict:
        for key, item in value.items():
            _string(key)
            _tree(item, depth + 1)
    elif type(value) is list:
        for item in value:
            _tree(item, depth + 1)
    elif type(value) is str:
        _string(value)
    elif type(value) is int:
        _integer(value, -(2**63))
    else:
        _need(value is None or type(value) is bool, "json_type")


def _equal(actual, expected):
    # Python considers True == 1; structural equality here must not.
    _need(type(actual) is type(expected), "binding")
    if type(actual) is dict:
        _keys(actual, expected)
        for key in expected:
            _equal(actual[key], expected[key])
    elif type(actual) is list:
        _need(len(actual) == len(expected), "binding")
        for a, b in zip(actual, expected):
            _equal(a, b)
    else:
        _need(actual == expected, "binding")


def _no_tail(value):
    # This exact fixed-fixture postfork statement is ineligible for all three
    # preserved views, including observations/narration, not just requests.
    # This does not attempt general semantic prose validation.
    if type(value) is str:
        _need(TAIL_TEXT not in value, "tail_leak")
    elif type(value) is dict:
        for key, item in value.items():
            _no_tail(key)
            _no_tail(item)
    elif type(value) is list:
        for item in value:
            _no_tail(item)


def _quote(value):
    # Android35 JSONStringer.string / JSONObject.quote (including escaped /):
    # https://android.googlesource.com/platform/prebuilts/fullsdk/sources/+/dc3f885ebe8ddc75bd9cf2d567eef4d1ed433a09/android-35/org/json/JSONStringer.java
    _string(value)
    short = {'"': '\\"', '\\': '\\\\', '/': '\\/', '\t': '\\t', '\b': '\\b',
             '\n': '\\n', '\r': '\\r', '\f': '\\f'}
    return '"' + ''.join(short.get(c, "\\u%04x" % ord(c) if ord(c) < 32 else c) for c in value) + '"'


def _canonical(value):
    """Java helper's exact integer-only canonical form, not Python dumps.

    Java Collections.sort compares UTF16 code units (not Unicode codepoints).
    Integral native v1 data uses JSONObject.numberToString's decimal long form.
    Floating point, exponent spellings and -0 are deliberately not admitted.
    """
    if type(value) is dict:
        keys = sorted(value, key=lambda key: key.encode("utf-16-be"))
        return '{' + ','.join(_quote(key) + ':' + _canonical(value[key]) for key in keys) + '}'
    if type(value) is list:
        return '[' + ','.join(_canonical(item) for item in value) + ']'
    if type(value) is str:
        return _quote(value)
    if value is None:
        return 'null'
    if type(value) is bool:
        return 'true' if value else 'false'
    _integer(value, -(2**63))
    return str(value)


def _scope(value, story, branch):
    _equal(value, {"story": story, "branch": branch})


def _workspace(value, head):
    _keys(value, ("story", "branch", "head"))
    _id(value["story"])
    _id(value["branch"])
    _equal(value["head"], head)
    return value


def _fixture(proof, expected, retained):
    value = proof["fixture"]
    common = {"version", "scope", "case", "controller_uid", "product_uid", "signature_sha256",
              "origin_run_id", "origin_product_sha256", "fixture_test_sha256", "roots_at_creation", "parent"}
    _keys(value, common | ({"root", "retained_child", "root_text_sha256", "retained_prefix_sha256",
                           "unreachable_tail_sha256", "parent_draft_sha256"} if retained else
                          {"child", "parent_text_sha256", "child_draft_sha256"}))
    for key, wanted in {"version": 1, "case": expected["case"], "origin_run_id": expected["run_id"],
                        "origin_product_sha256": expected["product_sha256"],
                        "fixture_test_sha256": expected["test_sha256"],
                        "scope": "locallore_retained_parent_process_fixture_v1" if retained else "locallore_retired_process_fixture_v1",
                        "controller_uid": expected["controller_uid"], "product_uid": expected["product_uid"],
                        "signature_sha256": expected["signature_sha256"]}.items():
        _equal(value[key], wanted)
    roots = value["roots_at_creation"]
    _need(type(roots) is list and len(roots) == 2, "roots")
    a, b = (_workspace(row, 0) for row in roots)
    _need(a["story"] < b["story"] and a["branch"] == b["branch"], "roots")
    root = _workspace(value["root"] if retained else value["parent"], 1)
    _scope({k: root[k] for k in ("story", "branch")}, b["story"], b["branch"])
    target = _workspace(value["parent"] if retained else value["child"], 3 if retained else 1)
    _need(target["story"] == b["story"] and target["branch"] != root["branch"], "target_scope")
    if retained:
        child = _workspace(value["retained_child"], 2)
        _need(child["story"] == b["story"] and child["branch"] not in (root["branch"], target["branch"]), "retained_scope")
        _equal(value["root_text_sha256"], ROOT_SHA)
        _equal(value["retained_prefix_sha256"], PREFIX_SHA)
        _equal(value["unreachable_tail_sha256"], "d07a57c72b9f4a81eedf539fbfdc184ba40fa416dc92f67261c9e54e1a55f9e4")
        _equal(value["parent_draft_sha256"], "4bbd7fc7d2efea6368acc0fd343b01d8fcb5e38a6af3ae4eb847a197e64b54cb")
    else:
        child = None
        _equal(value["parent_text_sha256"], ROOT_SHA)
        _equal(value["child_draft_sha256"], "f2e4d3340f433d0982360ad585f270c4f2682b2b0969fab8b246bbaee5e81fa3")
    return a, root, target, child


def _view(value, story, branch, head, root_branch, parent_branch):
    _keys(value, ("scope", "revision", "rules", "player", "inventory", "receipts"))
    _scope(value["scope"], story, branch)
    _equal(value["revision"], head)
    _need(value["rules"] in ("fantasy_v1", "narrative_v1"), "rules")
    player = value["player"]
    _keys(player, ("version", "scope", "revision", "observer", "seed_source", "self_state", "facts", "observations", "beliefs"))
    _equal(player["version"], 1)
    _scope(player["scope"], story, branch)
    _equal(player["revision"], head)
    _equal(player["observer"], "player")
    _string(player["seed_source"])
    for key in ("self_state", "facts"):
        _need(type(player[key]) is dict, "player")
    for key in ("observations", "beliefs"):
        _need(type(player[key]) is list, "player")
    _need(type(value["inventory"]) is dict, "inventory")
    receipts = value["receipts"]
    _need(type(receipts) is list and len(receipts) == head, "receipt_count")
    for index, receipt in enumerate(receipts):
        _need(type(receipt) is dict and set(receipt) in (
            {"request", "proposal", "events", "narration"}, {"request", "proposal", "events", "narration", "play"}), "receipt")
        _need(type(receipt["proposal"]) is dict and type(receipt["events"]) is list, "receipt")
        _string(receipt["narration"])
        if "play" in receipt:
            _need(type(receipt["play"]) is dict, "receipt")
        request = receipt["request"]
        _keys(request, ("version", "scope", "turn", "expected_revision", "intent"))
        _equal(request["version"], 1)
        _id(request["turn"])
        _scope(request["scope"], story, root_branch if index == 0 else parent_branch)
        _equal(request["expected_revision"], index)
        _keys(request["intent"], ("kind", "value"))
        _equal(request["intent"]["kind"], "free_text")
        text = request["intent"]["value"]
        _keys(text, ("kind", "text"))
        _equal(text["kind"], "dialogue")
        _equal(_sha(_string(text["text"]).encode("utf-8")), ROOT_SHA if index == 0 else PREFIX_SHA)


def validate_retirement(proof: dict, helper_raw: dict[str, bytes], sidecars: dict[str, bytes], expected: dict) -> dict:
    """Validate original helper/sidecar bytes after closed controller validation.

    Error messages are fixed categories, never input, paths, text or exceptions.
    The result cannot grant mutation/retry authority or prove OS observations.
    """
    try:
        return _validate(proof, helper_raw, sidecars, expected)
    except RetirementEvidenceRefused:
        raise
    except (KeyError, TypeError, ValueError, UnicodeError, RecursionError, OverflowError):
        raise RetirementEvidenceRefused("shape") from None


def _validate(proof, helper_raw, sidecars, expected):
    _keys(expected, EXPECTED)
    case = expected["case"]
    _need(case in ("restore_retired_child", "restore_retained_parent"), "case")
    retained = case == "restore_retained_parent"
    _need(type(expected["run_id"]) is str and re.fullmatch("[0-9a-f]{16}", expected["run_id"]) is not None, "run")
    for key in ("product_sha256", "test_sha256", "library_sha256", "signature_sha256"):
        _hex(expected[key])
    for key in ("controller_uid", "product_uid"):
        _integer(expected[key], 10000, 99999)
    _need(expected["controller_uid"] != expected["product_uid"], "uid")
    _need(type(proof) is dict and proof.get("case") == case and proof.get("run_id") == expected["run_id"]
          and proof.get("status") == "passed", "controller")
    _equal(proof["version"], 1)
    _equal(proof["scope"], "locallore_process_controller_v1")
    _equal(proof["process_deaths"], 2)
    _equal(proof["last_helper_exit"], 0)
    a, root, target, child = _fixture(proof, expected, retained)
    controller = proof["controller"]
    _keys(controller, ("pid", "uid", "start"))
    controller_pid = _integer(controller["pid"], 1, 2**31 - 1)
    _equal(controller["uid"], expected["controller_uid"])
    _integer(controller["start"], 1)
    observations = proof["observations"]
    _need(type(observations) is list and len(observations) == 3, "observations")
    product_pids = []
    starts = []
    tasks = []
    for index, row in enumerate(observations):
        _keys(row, ("pid", "uid", "start", "task", "restored", "factory"))
        product_pids.append(_integer(row["pid"], 1, 2**31 - 1))
        starts.append(_integer(row["start"], 1))
        tasks.append(_integer(row["task"], 1, 2**31 - 1))
        _equal(row["uid"], expected["product_uid"])
        _equal(row["restored"], index > 0)
        _equal(row["factory"], 1)
    _need(len(set(product_pids + [controller_pid])) == 4 and len(set(starts)) == 3 and len(set(tasks)) == 1, "processes")
    terminals = proof["terminal_observations"]
    _need(type(terminals) is list and len(terminals) == 2, "terminals")
    for index, row in enumerate(terminals):
        _keys(row, ("pid", "start", "task", "saved_sequence", "commands_sequence", "saved_game", "commands_game"))
        for key, value in (("pid", product_pids[index]), ("start", starts[index]), ("task", tasks[index])):
            _equal(row[key], value)
        for key in ("saved_sequence", "commands_sequence"):
            _integer(row[key], 1, 65536)
        counts = (3, 0, 3, 3, 0, 4) if retained else (1, 0, 1, 1, 0, 2)
        game = dict(zip(GAME, counts if index == 0 else (0,) * 6))
        _equal(row["saved_game"], game)
        _equal(row["commands_game"], game)
    _keys(helper_raw, MODES)
    helpers = {}
    helper_pids = []
    preserve_hash = None
    for mode in MODES:
        raw = helper_raw[mode]
        _need(type(raw) is bytes and 0 < len(raw) <= HELPER_CAP and raw.endswith(b'\n')
              and raw.count(b'\n') == 1 and b'\r' not in raw, "helper_frame")
        value = _json(raw, HELPER_CAP)
        _tree(value)
        _keys(value, HELPER)
        fields = {"version": 1, "scope": "locallore_retained_parent_fixture_v1" if retained else "locallore_retired_fixture_v1",
                  "mode": mode, "run_id": expected["run_id"], "status": "passed",
                  "stage": {"load": "LOAD_COMPLETE", "probe": "PROBE_CLOSED", "retire": "RETIRED_CLOSED"}[mode],
                  "uid": expected["product_uid"], "product_sha256": expected["product_sha256"],
                  "test_sha256": expected["test_sha256"], "library_sha256": expected["library_sha256"],
                  "commit_attempts": int(mode == "retire"), "archive_closed": True, "workspace_closed": True}
        for key, wanted in fields.items():
            _equal(value[key], wanted)
        ids = ["load_a", "load_b", "main", "load_child"] if mode == "load" else [a["story"], root["story"], root["branch"], target["branch"]]
        if retained:
            ids += ["load_retained" if mode == "load" else child["branch"], "3", "2"]
        scope_bytes = (("2\n" if retained else "1\n") + '\n'.join(ids) + '\n').encode("utf-8")
        _equal(value["scope_sha256"], _sha(scope_bytes))
        helper_pids.append(_integer(value["pid"], 1, 2**31 - 1))
        _integer(value["started_uptime_ms"], 1)
        if mode == "load":
            _need(value["before"] is None and value["after"] is None, "load_state")
        else:
            for key in ("before", "after"):
                retired_now = mode == "retire" and key == "after"
                state = {"other_head": 0, "target_head": None if retired_now else (3 if retained else 1), "target_active": not retired_now}
                if retained:
                    current = _hex(value[key]["preserved_sha256"])
                    preserve_hash = preserve_hash or current
                    _equal(current, preserve_hash)
                    state.update(root_head=1, target_physical_head=2 if retired_now else 3, retained_head=2,
                                 retained_active=True, preserved_sha256=preserve_hash)
                else:
                    state["parent_head"] = 1
                _equal(value[key], state)
        helpers[mode] = value
    _need(len(set(helper_pids)) == 3 and not set(helper_pids) & set(product_pids + [controller_pid]), "helper_processes")
    # Monotonic helper entry clocks follow dispatch order. They are not OS
    # process starts; do not infer app prewarming/specialization interleaving
    # against the producers' getStartUptimeMillis values from these records.
    _need(controller["start"] <= helpers["load"]["started_uptime_ms"]
          <= helpers["probe"]["started_uptime_ms"] <= helpers["retire"]["started_uptime_ms"], "helper_order")
    load = proof["load_gate"]
    _equal(load, {"proof_sha256": _sha(helper_raw["load"]), **{key: helpers["load"][key] for key in ("pid", "uid", "started_uptime_ms")}})
    rows = proof["retained_helpers" if retained else "retirement_helpers"]
    _need(type(rows) is list and len(rows) == 2, "helper_summaries")
    for row, mode in zip(rows, ("probe", "retire")):
        wanted = ({key: helpers[mode][key] for key in ("mode", "pid", "uid", "started_uptime_ms")} |
                  {"proof_sha256": _sha(helper_raw[mode])}) if retained else helpers[mode]
        _equal(row, wanted)
    _keys(sidecars, SIDECARS if retained else ())
    if retained:
        _need(all(type(raw) is bytes and 0 < len(raw) <= SIDECAR_CAP for raw in sidecars.values())
              and sum(map(len, sidecars.values())) <= 1048576, "sidecar_bounds")
        for raw in sidecars.values():
            _equal(_sha(raw), preserve_hash)
            value = _json(raw, SIDECAR_CAP)
            _tree(value)
            _keys(value, ("version", "scope", "views"))
            _equal(value["version"], 1)
            _equal(value["scope"], "locallore_retained_parent_preserved_v1")
            views = value["views"]
            _keys(views, ("other", "root", "retained"))
            _no_tail(views)
            for label, story, branch, head in (("other", a["story"], a["branch"], 0),
                                                ("root", root["story"], root["branch"], 1),
                                                ("retained", child["story"], child["branch"], 2)):
                _view(views[label], story, branch, head, root["branch"], target["branch"])
            _equal(raw, _canonical(value).encode("utf-8"))
    return {"case": case, "helper_count": 3, "sidecar_count": 4 if retained else 0,
            "preserved_sha256": preserve_hash, "passed": True}
