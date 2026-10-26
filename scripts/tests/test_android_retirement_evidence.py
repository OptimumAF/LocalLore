"""Original synthetic host controls; no SDK, native process or device access.

Copyright 2026 LocalLore contributors. SPDX-License-Identifier: Apache-2.0
"""
import copy
import hashlib
import json
import unittest

from benchmarks import android_retirement_evidence as evidence


ROOT = ("SYNTHETIC process-restoration dialogue: Mira, caf\u00e9 and lanterns \U0001f30a.\n"
        "Still unsent until my explicit Send.")
PREFIX = ("SYNTHETIC retained-parent prefix: Mira, snow \u96ea and caf\u00e9 \U0001f30a.\n"
          "Keep this accepted statement in the retained child.")
CHILD_DRAFT = ("SYNTHETIC child-timeline draft: Mira, snow \u96ea and caf\u00e9 \U0001f30a.\n"
               "Unsent until one explicit child Send.")


def digest(raw):
    return hashlib.sha256(raw).hexdigest()


def canonical(value):
    # Independent test fixture renderer: canonical key order is imposed before
    # json.dumps; Android always escapes slash (Python normally leaves it).
    def ordered(v):
        if type(v) is dict:
            return {k: ordered(v[k]) for k in sorted(v, key=lambda k: k.encode("utf-16-be"))}
        return [ordered(x) for x in v] if type(v) is list else v
    return json.dumps(ordered(value), ensure_ascii=False, separators=(',', ':')).replace('/', '\\/').encode('utf-8')


def receipt(index):
    scope = {"story": "story_b", "branch": "main" if index == 0 else "parent_p"}
    turn = "synthetic_root" if index == 0 else "synthetic_prefix"
    return {"request": {"version": 1, "scope": scope, "turn": turn,
                        "expected_revision": index, "intent": {"kind": "free_text", "value": {
                            "kind": "dialogue", "text": ROOT if index == 0 else PREFIX}}},
            "proposal": {"version": 1, "scope": copy.deepcopy(scope), "turn": turn,
                         "expected_revision": index, "commands": [{"op": "say", "text": ROOT if index == 0 else PREFIX, "audience": ["mira"]}]},
            "events": [{"version": 1, "scope": copy.deepcopy(scope), "sequence": index + 1,
                        "outcome": {"said": {"text": ROOT if index == 0 else PREFIX}}}],
            "narration": "Synthetic accepted narration: caf\u00e9 / snow \u96ea.\nSecond line.",
            "play": {"version": 1, "fallback": False, "repairs": 0}}


def view(story, branch, head):
    scope = {"story": story, "branch": branch}
    return {"scope": scope, "revision": head, "rules": "fantasy_v1",
            "player": {"version": 1, "scope": copy.deepcopy(scope), "revision": head,
                       "observer": "player", "seed_source": "synthetic_seed", "self_state": {
                           "name": "Player", "location": "quay", "alive": True, "energy": 10,
                           "abilities": {}, "attributes": {"patience": -1}, "injuries": [],
                           "affiliations": [], "goals": []}, "facts": {}, "observations": [], "beliefs": []},
            "inventory": {}, "receipts": [receipt(i) for i in range(head)]}


def fixture(retained=True):
    case = "restore_retained_parent" if retained else "restore_retired_child"
    expected = {"case": case, "run_id": "0123456789abcdef", "product_sha256": "a" * 64,
                "test_sha256": "b" * 64, "library_sha256": "c" * 64,
                "controller_uid": 10201, "product_uid": 10202, "signature_sha256": "d" * 64}
    a = {"story": "story_a", "branch": "main", "head": 0}
    b = {"story": "story_b", "branch": "main", "head": 0}
    f = {"version": 1, "scope": "locallore_retained_parent_process_fixture_v1" if retained else "locallore_retired_process_fixture_v1",
         "case": case, "controller_uid": 10201, "product_uid": 10202,
         "signature_sha256": "d" * 64, "origin_run_id": expected["run_id"],
         "origin_product_sha256": "a" * 64, "fixture_test_sha256": "b" * 64,
         "roots_at_creation": [a, b]}
    if retained:
        f.update(root={**b, "head": 1}, parent={**b, "branch": "parent_p", "head": 3},
                 retained_child={**b, "branch": "grandchild_g", "head": 2}, root_text_sha256=evidence.ROOT_SHA,
                 retained_prefix_sha256=evidence.PREFIX_SHA,
                 unreachable_tail_sha256="d07a57c72b9f4a81eedf539fbfdc184ba40fa416dc92f67261c9e54e1a55f9e4",
                 parent_draft_sha256="4bbd7fc7d2efea6368acc0fd343b01d8fcb5e38a6af3ae4eb847a197e64b54cb")
    else:
        f.update(parent={**b, "head": 1}, child={**b, "branch": "parent_p", "head": 1},
                 parent_text_sha256=evidence.ROOT_SHA, child_draft_sha256=digest(CHILD_DRAFT.encode()))
    sidecars = {}
    if retained:
        raw = canonical({"version": 1, "scope": "locallore_retained_parent_preserved_v1", "views": {
            "other": view("story_a", "main", 0), "root": view("story_b", "main", 1),
            "retained": view("story_b", "grandchild_g", 2)}})
        sidecars = {name: raw for name in evidence.SIDECARS}
    proof = {"version": 1, "scope": "locallore_process_controller_v1", "case": case,
             "run_id": expected["run_id"], "status": "passed", "process_deaths": 2,
             "last_helper_exit": 0, "fixture": f, "controller": {"pid": 501, "uid": 10201, "start": 100},
             "observations": [{"pid": 601 + i, "uid": 10202, "start": 200 + i * 100,
                               "task": 81, "factory": 1, "restored": i > 0} for i in range(3)],
             "terminal_observations": []}
    game = dict(zip(evidence.GAME, (3, 0, 3, 3, 0, 4) if retained else (1, 0, 1, 1, 0, 2)))
    for i in range(2):
        proof["terminal_observations"].append({"pid": 601 + i, "start": 200 + i * 100, "task": 81,
                                              "saved_sequence": 31, "commands_sequence": 30,
                                              "saved_game": game if i == 0 else dict.fromkeys(evidence.GAME, 0),
                                              "commands_game": game.copy() if i == 0 else dict.fromkeys(evidence.GAME, 0)})
    helpers = {}
    for i, mode in enumerate(evidence.MODES):
        ids = ["load_a", "load_b", "main", "load_child"] if mode == "load" else ["story_a", "story_b", "main", "parent_p"]
        if retained:
            ids += ["load_retained" if mode == "load" else "grandchild_g", "3", "2"]
        state = {"other_head": 0, "target_head": 3 if retained else 1, "target_active": True}
        if retained:
            state.update(root_head=1, target_physical_head=3, retained_head=2, retained_active=True,
                         preserved_sha256=digest(next(iter(sidecars.values()))))
        else:
            state["parent_head"] = 1
        after = copy.deepcopy(state)
        if mode == "retire":
            after.update(target_head=None, target_active=False)
            if retained:
                after["target_physical_head"] = 2
        obj = {"version": 1, "scope": "locallore_retained_parent_fixture_v1" if retained else "locallore_retired_fixture_v1",
               "mode": mode, "run_id": expected["run_id"], "status": "passed",
               "stage": ("LOAD_COMPLETE", "PROBE_CLOSED", "RETIRED_CLOSED")[i], "pid": 701 + i,
               "uid": 10202, "started_uptime_ms": 110 + i * 10, "product_sha256": "a" * 64,
               "test_sha256": "b" * 64, "library_sha256": "c" * 64,
               "scope_sha256": digest((("2\n" if retained else "1\n") + '\n'.join(ids) + '\n').encode()),
               "commit_attempts": int(mode == "retire"), "archive_closed": True, "workspace_closed": True,
               "before": None if mode == "load" else state, "after": None if mode == "load" else after}
        helpers[mode] = json.dumps(obj, ensure_ascii=False, separators=(',', ':')).encode() + b'\n'
    rebind(proof, helpers)
    return proof, helpers, sidecars, expected


def rebind(proof, helpers):
    decoded = {mode: json.loads(raw) for mode, raw in helpers.items()}
    proof["load_gate"] = {key: decoded["load"][key] for key in ("pid", "uid", "started_uptime_ms")}
    proof["load_gate"]["proof_sha256"] = digest(helpers["load"])
    if proof["case"] == "restore_retained_parent":
        proof["retained_helpers"] = [{**{key: decoded[mode][key] for key in ("mode", "pid", "uid", "started_uptime_ms")},
                                       "proof_sha256": digest(helpers[mode])} for mode in ("probe", "retire")]
    else:
        proof["retirement_helpers"] = [decoded[mode] for mode in ("probe", "retire")]


def replace_helper(data, mode, change):
    proof, helpers, _, _ = data
    obj = json.loads(helpers[mode])
    change(obj)
    helpers[mode] = json.dumps(obj, ensure_ascii=False, separators=(',', ':')).encode() + b'\n'
    rebind(proof, helpers)


def replace_sidecars(data, raw):
    data[2].update({name: raw for name in evidence.SIDECARS})
    for mode in ("probe", "retire"):
        def change(obj):
            for key in ("before", "after"):
                obj[key]["preserved_sha256"] = digest(raw)
        replace_helper(data, mode, change)


class AndroidRetirementEvidenceTests(unittest.TestCase):
    def refused(self, data):
        with self.assertRaises(evidence.RetirementEvidenceRefused) as caught:
            evidence.validate_retirement(*data)
        self.assertNotIn("SYNTHETIC", str(caught.exception))
        self.assertLess(len(str(caught.exception)), 32)

    def test_original_both_cases_and_all_three_modes(self):
        for retained in (False, True):
            with self.subTest(retained=retained):
                data = fixture(retained)
                result = evidence.validate_retirement(*data)
                self.assertEqual({"case": data[3]["case"], "helper_count": 3,
                                  "sidecar_count": 4 if retained else 0,
                                  "preserved_sha256": digest(data[2][evidence.SIDECARS[0]]) if retained else None,
                                  "passed": True}, result)

    def test_decoded_data_not_mutated(self):
        data = fixture()
        before = copy.deepcopy(data)
        evidence.validate_retirement(*data)
        self.assertEqual(before, data)

    def test_helper_quiet_single_lf_utf8_and_caps(self):
        for raw in (b'', b'{}', b'{}\r\n', b'{}\n\n', b'noise\n{}\n', b'\xef\xbb\xbf{}\n', b'\xff\n', b'x' * 4096 + b'\n'):
            with self.subTest(raw=raw[:12]):
                data = fixture()
                data[1]['probe'] = raw
                self.refused(data)

    def test_helper_cap_includes_the_single_final_lf(self):
        data = fixture()
        raw = data[1]['probe']
        data[1]['probe'] = b' ' * (4096 - len(raw)) + raw
        rebind(data[0], data[1])
        self.assertEqual(4096, len(data[1]['probe']))
        self.assertTrue(evidence.validate_retirement(*data)['passed'])
        data[1]['probe'] = b' ' + data[1]['probe']
        rebind(data[0], data[1])
        self.refused(data)

    def test_duplicate_keys_at_top_and_nested(self):
        for raw in (b'{"version":1,"version":1}\n', b'{"before":{"x":1,"x":2}}\n'):
            data = fixture()
            data[1]['probe'] = raw
            self.refused(data)

    def test_helper_unknown_missing_wrong_stage_and_provenance(self):
        mutations = [lambda o: o.update(extra=1), lambda o: o.pop('before'), lambda o: o.update(stage='LOAD_COMPLETE'),
                     lambda o: o.update(mode='retire'), lambda o: o.update(run_id='f' * 16),
                     lambda o: o.update(uid=10201), lambda o: o.update(product_sha256='f' * 64),
                     lambda o: o.update(test_sha256='f' * 64), lambda o: o.update(library_sha256='f' * 64),
                     lambda o: o.update(scope_sha256='f' * 64), lambda o: o.update(status='failed')]
        for change in mutations:
            data = fixture()
            replace_helper(data, 'probe', change)
            self.refused(data)

    def test_typed_counters_no_bool_float_or_negative(self):
        for field in ('version', 'pid', 'uid', 'started_uptime_ms', 'commit_attempts'):
            for value in (True, 1.0, -1, '1'):
                data = fixture()
                replace_helper(data, 'probe', lambda o: o.update({field: value}))
                self.refused(data)

    def test_commit_only_retire_and_both_owners_closed(self):
        for mode in evidence.MODES:
            for field, val in (('commit_attempts', 2), ('archive_closed', False), ('workspace_closed', 1)):
                data = fixture()
                replace_helper(data, mode, lambda o: o.update({field: val}))
                self.refused(data)

    def test_load_cannot_have_database_state(self):
        data = fixture()
        replace_helper(data, 'load', lambda o: o.update(before={}))
        self.refused(data)

    def test_helper_pids_distinct_and_disjoint_from_all_product_and_controller_pids(self):
        for pid in (701, 501, 601, 602, 603):
            data = fixture()
            replace_helper(data, 'retire', lambda o: o.update(pid=pid))
            self.refused(data)

    def test_helper_entry_clock_order_and_equal_millisecond_entries(self):
        for mode, when in (('load', 99), ('probe', 109), ('retire', 119)):
            data = fixture()
            replace_helper(data, mode, lambda o: o.update(started_uptime_ms=when))
            self.refused(data)
        data = fixture()
        for mode in evidence.MODES:
            replace_helper(data, mode, lambda o: o.update(started_uptime_ms=110))
        self.assertTrue(evidence.validate_retirement(*data)['passed'])

    def test_controller_summary_hash_pid_time_and_order_binding(self):
        for key, value in (('proof_sha256', 'f' * 64), ('pid', 999), ('uid', 99999), ('started_uptime_ms', 999)):
            data = fixture()
            data[0]['retained_helpers'][0][key] = value
            self.refused(data)
        data = fixture()
        data[0]['retained_helpers'].reverse()
        self.refused(data)

    def test_old_leaf_full_proofs_must_equal_original_raw(self):
        data = fixture(False)
        data[0]['retirement_helpers'][0]['before']['target_head'] = 0
        self.refused(data)

    def test_missing_extra_helper_or_sidecar(self):
        for index, name in ((1, 'load'), (2, evidence.SIDECARS[0])):
            data = fixture()
            data[index].pop(name)
            self.refused(data)
        data = fixture(False)
        data[2]['unexpected'] = b'{}'
        self.refused(data)

    def test_retirement_states_exact_both_cases(self):
        for retained in (False, True):
            for field, value in (('other_head', True), ('target_active', True), ('target_head', 2)):
                data = fixture(retained)
                replace_helper(data, 'retire', lambda o: o['after'].update({field: value}))
                self.refused(data)
        for field, value in (('target_physical_head', 3), ('retained_head', 3), ('retained_active', False), ('root_head', 0)):
            data = fixture()
            replace_helper(data, 'retire', lambda o: o['after'].update({field: value}))
            self.refused(data)

    def test_all_four_native_digests_and_original_sidecars_match(self):
        data = fixture()
        replace_helper(data, 'retire', lambda o: o['after'].update(preserved_sha256='e' * 64))
        self.refused(data)
        data = fixture()
        data[2][evidence.SIDECARS[-1]] += b' '
        self.refused(data)

    def test_scope_and_revision_and_original_receipt_scope_not_rewritten(self):
        for path, value in ((('scope', 'branch'), 'parent_p'), (('player', 'scope', 'story'), 'story_a'),
                            (('revision',), 3), (('player', 'revision'), True),
                            (('receipts', 0, 'request', 'scope', 'branch'), 'grandchild_g')):
            data = fixture()
            obj = json.loads(next(iter(data[2].values())))
            item = obj['views']['retained']
            for key in path[:-1]:
                item = item[key]
            item[path[-1]] = value
            replace_sidecars(data, canonical(obj))
            self.refused(data)

    def test_tail_or_changed_prefix_cannot_replace_original_positive(self):
        data = fixture()
        obj = json.loads(next(iter(data[2].values())))
        obj['views']['retained']['receipts'][1]['request']['intent']['value']['text'] = 'SYNTHETIC unreachable-parent tail'
        replace_sidecars(data, canonical(obj))
        self.refused(data)

    def test_exact_tail_cannot_leak_through_other_preserved_player_or_receipt_fields(self):
        for label, target in (('other', 'facts'), ('root', 'observations'), ('retained', 'narration')):
            data = fixture()
            obj = json.loads(next(iter(data[2].values())))
            value = obj['views'][label]
            if target == 'facts':
                value['player']['facts']['leaked'] = evidence.TAIL_TEXT
            elif target == 'observations':
                value['player']['observations'].append({'text': evidence.TAIL_TEXT})
            else:
                value['receipts'][0]['narration'] = 'Before ' + evidence.TAIL_TEXT + ' after'
            replace_sidecars(data, canonical(obj))
            self.refused(data)
        data = fixture()
        obj = json.loads(next(iter(data[2].values())))
        obj['views']['retained']['receipts'].append(receipt(1))
        replace_sidecars(data, canonical(obj))
        self.refused(data)

    def test_full_original_nested_data_not_dropped_and_mutated_sidecar_refuses(self):
        data = fixture()
        obj = json.loads(data[2][evidence.SIDECARS[-1]])
        obj['views']['retained']['receipts'][0]['events'][0]['sequence'] = 77
        data[2][evidence.SIDECARS[-1]] = canonical(obj)
        self.refused(data)

    def test_noncanonical_equivalent_json_never_normalized_to_pass(self):
        for transform in (lambda raw: raw + b'\n', lambda raw: b' ' + raw,
                          lambda raw: raw.replace(b'\\/', b'/'),
                          lambda raw: raw.replace('\u96ea'.encode(), b'\\u96ea'),
                          lambda raw: raw.replace(b'"revision":2', b'"revision":2.0'),
                          lambda raw: raw.replace(b'"revision":0', b'"revision":-0')):
            data = fixture()
            raw = next(iter(data[2].values()))
            changed = transform(raw)
            self.assertNotEqual(raw, changed)
            replace_sidecars(data, changed)
            self.refused(data)

    def test_java_utf16_key_order_and_control_quoting(self):
        data = fixture()
        obj = json.loads(next(iter(data[2].values())))
        obj['views']['other']['player']['facts'] = {'\ue000': 'privateuse', '\U00010000': 'supplementary', 'control': '\x00\b\t\r\f\n/"\\'}
        raw = canonical(obj)
        replace_sidecars(data, raw)
        self.assertTrue(evidence.validate_retirement(*data)['passed'])
        wrong_order = json.dumps(obj, sort_keys=True, ensure_ascii=False, separators=(',', ':')).replace('/', '\\/').encode()
        self.assertNotEqual(raw, wrong_order)
        replace_sidecars(data, wrong_order)
        self.refused(data)

    def test_sidecar_bounds_exact_edge_passes_no_raised_caps(self):
        data = fixture()
        obj = json.loads(next(iter(data[2].values())))
        obj['views']['other']['player']['facts']['padding'] = ''
        available = evidence.SIDECAR_CAP - len(canonical(obj))
        obj['views']['other']['player']['facts']['padding'] = 'x' * available
        raw = canonical(obj)
        self.assertEqual(evidence.SIDECAR_CAP, len(raw))
        replace_sidecars(data, raw)
        self.assertTrue(evidence.validate_retirement(*data)['passed'])
        replace_sidecars(data, raw + b' ')
        self.refused(data)

    def test_nonfinite_unpaired_unicode_duplicate_nested_and_deep_refused(self):
        for tail in (b'NaN', b'Infinity', b'1e999', b'"\\ud800"', b'{"x":1,"x":1}', b'[' * 40 + b'0' + b']' * 40):
            data = fixture()
            raw = b'{"attack":' + tail + b'}'
            replace_sidecars(data, raw)
            self.refused(data)

    def test_fixture_scope_hash_origins_signature_and_expected_closed(self):
        for key, value in (('signature_sha256', 'f' * 64), ('origin_run_id', 'f' * 16), ('root_text_sha256', 'f' * 64)):
            data = fixture()
            data[0]['fixture'][key] = value
            self.refused(data)
        data = fixture()
        data[3]['extra'] = True
        self.refused(data)

    def test_old_leaf_original_draft_hash_and_root_target_must_stay_distinct(self):
        data = fixture(False)
        data[0]['fixture']['child_draft_sha256'] = 'f' * 64
        self.refused(data)
        data = fixture(False)
        data[0]['fixture']['child']['branch'] = 'main'
        self.refused(data)

    def test_full_six_key_views_and_player_data_are_not_optional(self):
        for target, key in (('view', 'inventory'), ('view', 'rules'), ('player', 'self_state'),
                            ('player', 'facts'), ('player', 'observations')):
            data = fixture()
            obj = json.loads(next(iter(data[2].values())))
            value = obj['views']['retained']
            if target == 'player':
                value = value['player']
            value.pop(key)
            replace_sidecars(data, canonical(obj))
            self.refused(data)

    def test_controller_and_expected_counter_types_and_unknown_sidecar_shapes(self):
        for key, value in (('version', True), ('process_deaths', 2.0), ('last_helper_exit', False)):
            data = fixture()
            data[0][key] = value
            self.refused(data)
        data = fixture()
        data[3]['product_uid'] = True
        self.refused(data)
        data = fixture()
        data[2]['extra-v1.json'] = next(iter(data[2].values()))
        self.refused(data)

    def test_native_pid_identity_and_source_terminal_game_not_host_observation(self):
        data = fixture()
        data[0]['terminal_observations'][0]['saved_game']['other'] = 3
        self.refused(data)
        data = fixture()
        data[0]['observations'][1]['pid'] = data[0]['observations'][0]['pid']
        self.refused(data)

    def test_input_shapes_privacy_and_counter_traps_are_controlled_refusals(self):
        for index in range(4):
            for bad in (None, True, [], 'SYNTHETIC private diagnostic'):
                data = list(fixture())
                data[index] = bad
                self.refused(data)


if __name__ == '__main__':
    unittest.main()
