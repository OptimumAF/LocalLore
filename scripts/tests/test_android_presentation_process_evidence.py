"""Independent synthetic proof decoding; no Android execution or death evidence.

Copyright 2026 LocalLore contributors. SPDX-License-Identifier: Apache-2.0
"""
import copy
import hashlib
import json
import unittest

from benchmarks import android_presentation_process_evidence as evidence
from benchmarks import android_process_controller_evidence as legacy
from scripts.tests import test_android_process_controller_creation_v2 as old_creation
from scripts.tests import test_android_process_controller_evidence as old_fixtures


OPS = (
    "workspace", "branches", "resume", "create", "open", "play_snapshot",
    "free_text", "submit", "prepare", "commit", "cancel", "other",
    "story_template", "create_named", "play_presentation_v2",
)
EVENTS = {"created": "created", "saved": "saved_after_super", "commands": "command"}
CANARY = "private_prose_path_3917"


def encoded(value):
    return json.dumps(value, ensure_ascii=True, separators=(",", ":")).encode("utf-8")


def expected():
    return dict(run_id="0123456789abcdef", product_uid=12345, controller_uid=12346,
                product_sha256="a" * 64, signature_sha256="b" * 64)


def probe(leaf="commands"):
    return dict(version=3, scope="locallore_presentation_process_verify_v3",
                run_id=expected()["run_id"], pid=201, uid=12345, task_id=7,
                sequence=13, process_start_uptime_ms=1000, event=EVENTS[leaf],
                restored_state=True, factory_creations=1, hint_present=True,
                hint_sha256=hashlib.sha256(b"1\nstory-a\nmain\n").hexdigest(),
                operations=dict.fromkeys(OPS, 0))


def frame(value):
    return b"INSTRUMENTATION_RESULT: proof=" + encoded(value) + b"\nINSTRUMENTATION_CODE: -1\n"


def result_graph():
    """A synthetic three-process/two-death graph, never a live ownership proof."""
    pins = expected()
    game = dict.fromkeys(("free_text", "submit", "prepare", "commit", "cancel", "other"), 0)
    send = dict(game, free_text=1, prepare=1, commit=1)
    observations = [dict(pid=201 + i, uid=pins["product_uid"], start=1000 * (i + 1),
                         task=7, restored=i > 0, factory=1) for i in range(3)]
    terminals = []
    for index, counts in enumerate((game, send)):
        reads = dict(resume=4 + index * 2, play_presentation_v2=3 + index * 2, play_snapshot=0)
        creation = dict(create=0, create_named=2 if index == 0 else 0)
        terminals.append(dict(pid=201 + index, start=1000 * (index + 1), task=7,
                              saved_sequence=11 + index * 10, commands_sequence=10 + index * 10,
                              saved_game=dict(counts), commands_game=dict(counts),
                              saved_creation=dict(creation), commands_creation=dict(creation),
                              saved_reads=dict(reads), commands_reads=dict(reads)))
    reads = [dict(pid=observation["pid"], start=observation["start"], task=7,
                  before_sequence=2, after_sequence=8, resume_before=1, resume_after=3,
                  presentation_before=1, presentation_after=3, legacy_before=0, legacy_after=0,
                  before_game=dict(game), after_game=dict(game),
                  before_creation=dict(create=0, create_named=0),
                  after_creation=dict(create=0, create_named=0))
             for observation in observations[1:]]
    fixture = dict(version=3, scope="locallore_presentation_process_fixture_v3",
                   case="restore_player_presentation", controller_uid=pins["controller_uid"],
                   product_uid=pins["product_uid"], signature_sha256=pins["signature_sha256"],
                   origin_run_id=pins["run_id"], origin_product_sha256=pins["product_sha256"],
                   stories=[dict(story="story-a", branch="main", head=0),
                            dict(story="story-b", branch="main", head=0)])
    result = dict(version=3, scope="locallore_presentation_process_controller_v3",
                  case="restore_player_presentation", run_id=pins["run_id"], status="passed",
                  stage="DONE", reason="NONE", checks=100, process_deaths=2,
                  last_workspace_read="VALID", last_workspace_utf16_length=80,
                  controller=dict(pid=200, uid=pins["controller_uid"], start=900),
                  observations=observations, terminal_observations=terminals,
                  fixture=fixture, presentation_reads=reads)
    records = {}
    for leaf, index, sequence in (("created", 2, 1), ("saved", 1, 21), ("commands", 2, 9)):
        value = probe(leaf)
        value.update(pid=observations[index]["pid"], process_start_uptime_ms=observations[index]["start"],
                     sequence=sequence, hint_sha256=hashlib.sha256(b"1\nstory-b\nmain\n").hexdigest())
        value["operations"].update(resume=1 if leaf == "created" else 6 if leaf == "saved" else 4,
                                    play_presentation_v2=1 if leaf == "created" else 5 if leaf == "saved" else 4)
        if leaf == "saved":
            value["operations"].update(send)
        records[leaf] = encoded(value)
    return result, records, pins


class PresentationProbeEvidenceTests(unittest.TestCase):
    def refused(self, raw, pins=None, leaf="commands"):
        with self.assertRaises(evidence.PresentationEvidenceRefused) as caught:
            evidence.validate_probe(raw, expected() if pins is None else pins, leaf)
        self.assertEqual(str(caught.exception), "presentation_evidence_refused")
        self.assertNotIn(CANARY, str(caught.exception))

    def test_three_leaf_records_decode_without_mutating_inputs_or_lending_process_authority(self):
        pins = expected()
        saved_pins = copy.deepcopy(pins)
        for leaf in EVENTS:
            with self.subTest(leaf=leaf):
                value = probe(leaf)
                raw = encoded(value)
                self.assertEqual(evidence.validate_probe(raw, pins, leaf), value)
                self.assertEqual(raw, encoded(value))
                decoded = evidence.validate_probe(raw + b"\r\n", pins, leaf)
                decoded["operations"]["other"] = 999
                self.assertEqual(evidence.validate_probe(raw, pins, leaf), value)
        self.assertEqual(pins, saved_pins)

    def test_presentation_snapshot_unknown_and_gameplay_counters_remain_distinct_values(self):
        value = probe()
        value["operations"].update(play_presentation_v2=11, play_snapshot=7,
                                   other=3, free_text=2, create_named=4)
        actual = evidence.validate_probe(encoded(value), expected(), "commands")
        self.assertEqual(actual["operations"], value["operations"])
        self.assertEqual(set(actual["operations"]), set(OPS))
        # Structural decoding cannot certify a read-only completed controller.
        self.assertEqual(actual["operations"]["other"], 3)
        self.assertEqual(actual["operations"]["play_snapshot"], 7)

    def test_closed_record_and_operation_schemas_reject_legacy_retagging_and_extra_fields(self):
        base = probe()
        for key in base:
            bad = copy.deepcopy(base)
            del bad[key]
            with self.subTest(missing=key):
                self.refused(encoded(bad))
        for key in OPS:
            bad = copy.deepcopy(base)
            del bad["operations"][key]
            with self.subTest(missing_operation=key):
                self.refused(encoded(bad))
        for patch in ({"version": 2}, {"version": True},
                      {"scope": "locallore_process_verify_v3"},
                      {"scope": "locallore_process_verify_v2"},
                      {"source": CANARY}, {"qualified_target": True}):
            self.refused(encoded(dict(base, **patch)))
        bad = copy.deepcopy(base)
        bad["operations"]["story_presentation"] = 1
        self.refused(encoded(bad))

    def test_every_counter_has_strict_integer_type_and_inclusive_nonwrapping_bound(self):
        for key in OPS:
            for number in (0, 4096):
                value = probe()
                value["operations"][key] = number
                with self.subTest(operation=key, accepted=number):
                    self.assertEqual(evidence.validate_probe(encoded(value), expected(), "commands"), value)
            for number in (True, False, 1.0, "1", None, -1, 4097, 2**64):
                value = probe()
                value["operations"][key] = number
                with self.subTest(operation=key, refused=repr(number)):
                    self.refused(encoded(value))

    def test_identity_sequence_factory_and_uptime_bounds_are_not_boolean_or_float_coercions(self):
        bounds = dict(pid=(1, 2**31 - 1), task_id=(0, 2**31 - 1),
                      sequence=(1, 65536), process_start_uptime_ms=(0, 2**63 - 1),
                      factory_creations=(0, 16))
        for field, (low, high) in bounds.items():
            for number in (low, high):
                value = dict(probe(), **{field: number})
                with self.subTest(field=field, accepted=number):
                    self.assertEqual(evidence.validate_probe(encoded(value), expected(), "commands"), value)
            for number in (low - 1, high + 1, True, False, float(low), str(low), None):
                with self.subTest(field=field, refused=repr(number)):
                    self.refused(encoded(dict(probe(), **{field: number})))

    def test_hint_presence_and_restoration_are_exact_booleans_with_coupled_digest(self):
        value = dict(probe(), hint_present=False, hint_sha256=None, restored_state=False)
        self.assertEqual(evidence.validate_probe(encoded(value), expected(), "commands"), value)
        for field in ("hint_present", "restored_state"):
            for invalid in (0, 1, "true", None, [], {}):
                with self.subTest(field=field, invalid=repr(invalid)):
                    self.refused(encoded(dict(probe(), **{field: invalid})))
        for present, digest in ((True, None), (False, "a" * 64), (True, "A" * 64),
                                (True, "g" * 64), (True, "a" * 63), (True, CANARY)):
            with self.subTest(present=present, digest=digest):
                self.refused(encoded(dict(probe(), hint_present=present, hint_sha256=digest)))

    def test_expected_identity_and_apk_signature_bindings_are_closed_and_strict(self):
        pins = expected()
        mutations = [dict(pins, controller_uid=pins["product_uid"]),
                     dict(pins, controller_uid=True), dict(pins, product_uid=9999),
                     dict(pins, controller_uid=100000), dict(pins, product_uid=12345.0),
                     dict(pins, run_id="A" * 16), dict(pins, run_id="a" * 17),
                     dict(pins, case="restore_non_default"), dict(pins, package=CANARY)]
        for key in ("product_sha256", "signature_sha256"):
            for invalid in ("A" * 64, "a" * 63, "z" * 64, None, True):
                mutations.append(dict(pins, **{key: invalid}))
        for key in pins:
            missing = dict(pins)
            del missing[key]
            mutations.append(missing)
        for index, invalid in enumerate(mutations):
            with self.subTest(mutation=index):
                self.refused(encoded(probe()), pins=invalid)

    def test_run_product_uid_and_leaf_event_cannot_be_substituted(self):
        for patch in ({"run_id": "f" * 16}, {"run_id": CANARY},
                      {"uid": 12346}, {"uid": True}, {"uid": 12345.0},
                      {"uid": 9999}, {"uid": 100000}):
            self.refused(encoded(dict(probe(), **patch)))
        for leaf, event in EVENTS.items():
            for wrong in set(EVENTS.values()) - {event}:
                with self.subTest(leaf=leaf, event=wrong):
                    self.refused(encoded(dict(probe(leaf), event=wrong)), leaf=leaf)
        for invalid in ("commands.json", "../commands", "", None, 1, "saved_after_super"):
            self.refused(encoded(probe()), leaf=invalid)

    def test_json_byte_cap_duplicate_nonfinite_utf8_and_chatter_are_refused(self):
        raw = encoded(probe())
        exact = raw + b" " * (4096 - len(raw))
        self.assertEqual(len(exact), 4096)
        self.assertEqual(evidence.validate_probe(exact, expected(), "commands"), probe())
        invalid = [exact + b" ", b"", b"\xff", raw + b"\n" + raw,
                   raw.decode("utf-8"), bytearray(raw), memoryview(raw),
                   b"private:" + raw, raw + b" trailing", b"[]", b"null",
                   raw.replace(b'"version":3', b'"version":3,"version":3'),
                   raw.replace(b'"other":0', b'"other":0,"other":0')]
        for token in (b"NaN", b"Infinity", b"-Infinity"):
            invalid.append(raw.replace(b'"other":0', b'"other":' + token))
        for index, candidate in enumerate(invalid):
            with self.subTest(raw_case=index):
                self.refused(candidate)

    def test_legacy_four_case_v1_v2_readers_keep_original_shapes_and_refuse_v3_counter(self):
        for case in old_fixtures.CASES:
            for version in (1, 2):
                proof, pins = old_fixtures.original(case) if version == 1 else old_creation.current(case)
                records = old_fixtures.product_records(proof, version)
                legacy.validate_controller_result(old_fixtures.frame(proof), pins)
                parsed = legacy.validate_product_records(proof, records, pins)
                self.assertEqual(parsed, {name: json.loads(raw) for name, raw in records.items()})
                changed = json.loads(records["commands"])
                changed["operations"]["play_presentation_v2"] = 1
                with self.subTest(case=case, legacy_version=version):
                    with self.assertRaises(legacy.ControllerEvidenceRefused):
                        legacy.validate_product_records(proof, dict(records, commands=encoded(changed)), pins)
                    self.refused(records["commands"])


class PresentationControllerEvidenceTests(unittest.TestCase):
    def refused(self, result, records=None, pins=None):
        _, default_records, default_pins = result_graph()
        with self.assertRaises(evidence.PresentationEvidenceRefused) as caught:
            evidence.validate_result(frame(result), default_pins if pins is None else pins,
                                     default_records if records is None else records)
        self.assertEqual(str(caught.exception), "presentation_evidence_refused")
        self.assertNotIn(CANARY, str(caught.exception))

    def test_complete_three_process_graph_joins_both_deaths_and_final_raw_records(self):
        result, records, pins = result_graph()
        original = copy.deepcopy((result, records, pins))
        for newline in (b"\n", b"\r\n"):
            raw = frame(result).replace(b"\n", newline)
            self.assertEqual(evidence.validate_result(raw, pins, records), result)
        self.assertEqual((result, records, pins), original)
        # Checks are a bounded diagnostic, not an invocation or death count.
        for checks in (1, 4096):
            candidate = dict(result, checks=checks)
            self.assertEqual(evidence.validate_result(frame(candidate), pins, records), candidate)

    def test_result_and_nested_shapes_cannot_retag_legacy_or_claim_partial_success(self):
        result, _, _ = result_graph()
        for key in result:
            bad = copy.deepcopy(result)
            del bad[key]
            with self.subTest(missing=key):
                self.refused(bad)
        for patch in ({"version": 2}, {"scope": "locallore_process_controller_v3"},
                      {"case": "restore_retained_parent"}, {"status": "failed"},
                      {"stage": "PROBE"}, {"reason": "TIMEOUT"}, {"checks": True},
                      {"checks": 0}, {"checks": 4097}, {"process_deaths": 1},
                      {"process_deaths": True}, {"last_workspace_read": "INVALID"},
                      {"last_workspace_utf16_length": 0}, {"qualified_target": True}):
            self.refused(dict(result, **patch))
        for path in (("controller",), ("fixture",), ("observations", 1),
                     ("terminal_observations", 0), ("presentation_reads", 1)):
            bad = copy.deepcopy(result)
            node = bad
            for key in path:
                node = node[key]
            node["private_extra"] = CANARY
            self.refused(bad)

    def test_observation_uid_task_run_and_distinct_increasing_process_identities_are_bound(self):
        result, _, _ = result_graph()
        for index in range(3):
            for field, value in (("uid", 12346), ("task", 8), ("factory", 2),
                                 ("restored", index == 0), ("pid", True), ("start", -1)):
                bad = copy.deepcopy(result)
                bad["observations"][index][field] = value
                with self.subTest(index=index, field=field):
                    self.refused(bad)
        for field in ("pid", "start"):
            bad = copy.deepcopy(result)
            bad["observations"][1][field] = bad["observations"][0][field]
            self.refused(bad)
        bad = copy.deepcopy(result)
        bad["controller"]["pid"] = bad["observations"][0]["pid"]
        self.refused(bad)
        self.refused(dict(result, run_id="f" * 16))

    def test_restored_read_witnesses_require_two_bound_strict_increases_and_no_legacy_reads(self):
        result, _, _ = result_graph()
        for index in (0, 1):
            for field, value in (("pid", 201), ("start", 1000), ("task", 8),
                                 ("after_sequence", 2), ("after_sequence", 1),
                                 ("resume_after", 1), ("presentation_after", 1),
                                 ("legacy_before", 1), ("legacy_after", 1),
                                 ("presentation_after", True), ("resume_after", 4097)):
                bad = copy.deepcopy(result)
                bad["presentation_reads"][index][field] = value
                with self.subTest(witness=index, field=field, value=value):
                    self.refused(bad)
        for rows in ([], result["presentation_reads"][:1],
                     result["presentation_reads"] * 2, list(reversed(result["presentation_reads"]))):
            self.refused(dict(result, presentation_reads=rows))

    def test_terminal_game_creation_and_read_vectors_follow_either_actual_save_order(self):
        result, _, _ = result_graph()
        for index in (0, 1):
            after = copy.deepcopy(result)
            terminal = after["terminal_observations"][index]
            terminal["commands_sequence"] = terminal["saved_sequence"] + 1
            terminal["commands_reads"]["resume"] += 1
            terminal["commands_reads"]["play_presentation_v2"] += 1
            _, records, pins = result_graph()
            self.assertEqual(evidence.validate_result(frame(after), pins, records), after)
            for field in ("saved_game", "commands_game"):
                for operation in ("other", "cancel", "commit"):
                    bad = copy.deepcopy(result)
                    bad["terminal_observations"][index][field][operation] += 1
                    self.refused(bad)
            for field in ("saved_creation", "commands_creation"):
                bad = copy.deepcopy(result)
                bad["terminal_observations"][index][field]["create_named"] = 0 if index == 0 else 2
                self.refused(bad)
            for field in ("saved_reads", "commands_reads"):
                for operation, value in (("play_snapshot", 1), ("play_presentation_v2", 0),
                                         ("resume", 0), ("resume", True)):
                    bad = copy.deepcopy(result)
                    bad["terminal_observations"][index][field][operation] = value
                    self.refused(bad)
            bad = copy.deepcopy(result)
            terminal = bad["terminal_observations"][index]
            terminal["commands_sequence"] = terminal["saved_sequence"]
            self.refused(bad)
            # A read-only race can change reads, but cannot reverse monotonic time.
            bad = copy.deepcopy(result)
            bad["terminal_observations"][index]["commands_reads"]["resume"] += 1
            self.refused(bad)
            bad = copy.deepcopy(after)
            bad["terminal_observations"][index]["commands_reads"]["resume"] = 0
            self.refused(bad)

    def test_refresh_witnesses_never_authorize_gameplay_creation_or_unjoined_raw_progress(self):
        result, records, _ = result_graph()
        for index in (0, 1):
            for field, names in (("before_game", ("free_text", "other", "cancel")),
                                 ("after_game", ("prepare", "commit", "other")),
                                 ("before_creation", ("create", "create_named")),
                                 ("after_creation", ("create", "create_named"))):
                for name in names:
                    bad = copy.deepcopy(result)
                    bad["presentation_reads"][index][field][name] = 1
                    self.refused(bad)
        bad = copy.deepcopy(result)
        bad["presentation_reads"][0]["after_sequence"] = 22
        self.refused(bad)
        bad = copy.deepcopy(result)
        bad["presentation_reads"][0]["resume_after"] = 7
        self.refused(bad)
        changed = json.loads(records["created"])
        changed["sequence"] = 3
        self.refused(result, dict(records, created=encoded(changed)))
        changed = json.loads(records["commands"])
        changed["sequence"] = 7
        self.refused(result, dict(records, commands=encoded(changed)))
        changed = json.loads(records["commands"])
        changed["operations"]["play_presentation_v2"] = 2
        self.refused(result, dict(records, commands=encoded(changed)))

    def test_fixture_origin_scope_signature_and_final_navigation_hint_cannot_be_borrowed(self):
        result, records, _ = result_graph()
        for key, invalid in (("version", 2), ("scope", "locallore_process_fixture_v1"),
                             ("origin_run_id", "f" * 16), ("origin_product_sha256", "c" * 64),
                             ("signature_sha256", "c" * 64), ("controller_uid", 12345),
                             ("product_uid", 12346)):
            bad = copy.deepcopy(result)
            bad["fixture"][key] = invalid
            self.refused(bad)
        for invalid in ([dict(story="story-a", branch="main", head=0)] * 2,
                        [dict(story="story-b", branch="main", head=0),
                         dict(story="story-a", branch="main", head=0)]):
            bad = copy.deepcopy(result)
            bad["fixture"]["stories"] = invalid
            self.refused(bad)
        for leaf in records:
            value = json.loads(records[leaf])
            value["hint_sha256"] = hashlib.sha256(b"1\nstory-a\nmain\n").hexdigest()
            self.refused(result, dict(records, **{leaf: encoded(value)}))

    def test_final_raw_record_roster_identities_sequences_and_counter_join_are_replayed(self):
        result, records, _ = result_graph()
        for leaf in records:
            missing = dict(records)
            del missing[leaf]
            self.refused(result, missing)
            for key, value in (("pid", 999), ("process_start_uptime_ms", 999),
                               ("task_id", 8), ("restored_state", False),
                               ("factory_creations", 0), ("hint_present", False)):
                changed = json.loads(records[leaf])
                changed[key] = value
                if key == "hint_present":
                    changed["hint_sha256"] = None
                self.refused(result, dict(records, **{leaf: encoded(changed)}))
            for operation in ("other", "create_named", "play_snapshot"):
                changed = json.loads(records[leaf])
                changed["operations"][operation] += 1
                self.refused(result, dict(records, **{leaf: encoded(changed)}))
        self.refused(result, dict(records, private=records["saved"]))
        changed = json.loads(records["saved"])
        changed["sequence"] += 1
        self.refused(result, dict(records, saved=encoded(changed)))
        changed = json.loads(records["commands"])
        changed["sequence"] = json.loads(records["created"])["sequence"]
        self.refused(result, dict(records, commands=encoded(changed)))

    def test_result_frame_is_one_quiet_bounded_strict_utf8_json_record(self):
        result, records, pins = result_graph()
        raw = frame(result)
        self.assertLess(len(raw), 32768)
        invalid = [b"", b"\xff", raw + raw, b"chatter\n" + raw, raw + b"trailing\n",
                   raw.replace(b"INSTRUMENTATION_CODE: -1", b"INSTRUMENTATION_CODE: 0"),
                   raw.replace(b'"version":3', b'"version":3,"version":3', 1),
                   raw.replace(b'"checks":100', b'"checks":NaN'),
                   b" " * 32769, raw.decode(), bytearray(raw), memoryview(raw)]
        for index, candidate in enumerate(invalid):
            with self.subTest(frame=index):
                with self.assertRaises(evidence.PresentationEvidenceRefused):
                    evidence.validate_result(candidate, pins, records)

    def test_equal_sequence_read_forks_and_pre_send_terminal_aliases_cannot_qualify(self):
        result, records, pins = result_graph()
        # Equal endpoints are possible only when the actual counter snapshots agree.
        created = json.loads(records["created"])
        commands = json.loads(records["commands"])
        created["sequence"] = 2
        commands["sequence"] = 8
        commands["operations"].update(resume=3, play_presentation_v2=3)
        equal_records = dict(records, created=encoded(created), commands=encoded(commands))
        self.assertEqual(evidence.validate_result(frame(result), pins, equal_records), result)
        before = copy.deepcopy(result)
        before["presentation_reads"][1]["resume_before"] = 2
        self.refused(before, equal_records)  # Same sequence, different counter value.
        after = copy.deepcopy(result)
        after["presentation_reads"][1]["presentation_after"] = 2
        self.refused(after, equal_records)
        regressed = copy.deepcopy(result)
        regressed["presentation_reads"][1]["resume_before"] = 0
        self.refused(regressed, records)  # Later witness cannot precede created counters.
        equal_command = copy.deepcopy(result)
        equal_command["presentation_reads"][0]["after_sequence"] = 20
        self.refused(equal_command, records)
        equal_saved = copy.deepcopy(result)
        equal_saved["presentation_reads"][0]["after_sequence"] = 21
        equal_saved["terminal_observations"][1]["commands_sequence"] = 22
        self.refused(equal_saved, records)  # Explicit Send changes GAME after the witness.


if __name__ == "__main__":
    unittest.main()
