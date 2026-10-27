"""Original synthetic closed controller fixtures; these are not Android executions."""
import copy
import hashlib
import json
import unittest

from benchmarks import android_process_controller_evidence as evidence

CASES = ("restore_non_default", "restore_child_branch", "restore_retired_child", "restore_retained_parent")
GAME = ("free_text", "submit", "prepare", "commit", "cancel", "other")
ZERO, SEND, SETUP, RETAINED = (0, 0, 0, 0, 0, 0), (1, 0, 1, 1, 0, 0), (1, 0, 1, 1, 0, 2), (3, 0, 3, 3, 0, 4)
CANARY = "private_story_path_UID_text_6148"
ROOT_HASH = "a8cb95c8145359ad7fadad52d0df311551fab161e1e386a66c87d29fa50a3a55"
CHILD_HASH = "f2e4d3340f433d0982360ad585f270c4f2682b2b0969fab8b246bbaee5e81fa3"
PREFIX_HASH = "d0e88260d20e867ca12440419d4c32fed67d07d9ef45da74251c0ab38869cc5a"
TAIL_HASH = "d07a57c72b9f4a81eedf539fbfdc184ba40fa416dc92f67261c9e54e1a55f9e4"
DRAFT_HASH = "4bbd7fc7d2efea6368acc0fd343b01d8fcb5e38a6af3ae4eb847a197e64b54cb"


def digest(text):
    return hashlib.sha256(text.encode()).hexdigest()


def encoded(value):
    return json.dumps(value, separators=(",", ":"), ensure_ascii=True).encode()


def frame(proof):
    return b"INSTRUMENTATION_RESULT: proof=" + encoded(proof) + b"\nINSTRUMENTATION_CODE: -1\n"


def pins(case):
    return dict(case=case, run_id="0123456789abcdef", product_sha256="a" * 64,
                test_sha256=None if case in CASES[:2] else "c" * 64,
                library_sha256=None if case in CASES[:2] else "d" * 64,
                controller_uid=12346, product_uid=12345, signature_sha256="b" * 64)


def workspace(story, branch="main", head=0):
    return dict(story=story, branch=branch, head=head)


def game(vector):
    return dict(zip(GAME, vector))


def vectors(case):
    return {CASES[0]: (ZERO, SEND), CASES[1]: (SETUP, SEND), CASES[2]: (SETUP, ZERO), CASES[3]: (RETAINED, ZERO)}[case]


def leaf_helper(expected, mode):
    state = dict(other_head=0, parent_head=1, target_head=1, target_active=True)
    after = dict(state, target_head=None, target_active=False) if mode == "retire" else dict(state)
    return dict(version=1, scope="locallore_retired_fixture_v1", mode=mode, run_id=expected["run_id"],
        status="passed", stage="RETIRED_CLOSED" if mode == "retire" else "PROBE_CLOSED", pid=302 if mode == "retire" else 301,
        uid=expected["product_uid"], started_uptime_ms=1600 if mode == "retire" else 1500,
        product_sha256=expected["product_sha256"], test_sha256=expected["test_sha256"], library_sha256=expected["library_sha256"],
        scope_sha256=digest("1\nstory-a\nstory-b\nmain\nchild\n"), commit_attempts=int(mode == "retire"),
        archive_closed=True, workspace_closed=True, before=state, after=after)


def original(case=CASES[0]):
    e = pins(case)
    roots = [workspace("story-a"), workspace("story-b")]
    f = dict(version=1, scope="locallore_process_fixture_v1", case=case, controller_uid=e["controller_uid"],
        product_uid=e["product_uid"], signature_sha256=e["signature_sha256"], origin_run_id=e["run_id"],
        origin_product_sha256=e["product_sha256"])
    if case == CASES[0]:
        f["stories"] = roots
    elif case in CASES[1:3]:
        f.update(scope="locallore_child_process_fixture_v1" if case == CASES[1] else "locallore_retired_process_fixture_v1",
                 roots_at_creation=roots, parent=workspace("story-b", head=1), child=workspace("story-b", "child", 1),
                 parent_text_sha256=ROOT_HASH, child_draft_sha256=CHILD_HASH)
        if case == CASES[2]:
            f["fixture_test_sha256"] = e["test_sha256"]
    else:
        f.update(scope="locallore_retained_parent_process_fixture_v1", roots_at_creation=roots,
                 fixture_test_sha256=e["test_sha256"], root=workspace("story-b", head=1), parent=workspace("story-b", "parent", 3),
                 retained_child=workspace("story-b", "grandchild", 2), root_text_sha256=ROOT_HASH,
                 retained_prefix_sha256=PREFIX_HASH, unreachable_tail_sha256=TAIL_HASH, parent_draft_sha256=DRAFT_HASH)
    observations = [dict(pid=201 + i, uid=e["product_uid"], start=1000 * (i + 1), task=7, factory=1, restored=i > 0) for i in range(3)]
    terminals = [dict(pid=observations[i]["pid"], start=observations[i]["start"], task=7, saved_sequence=11 + 10 * i,
        commands_sequence=10 + 10 * i, saved_game=game(v), commands_game=game(v)) for i, v in enumerate(vectors(case))]
    proof = dict(version=1, scope="locallore_process_controller_v1", case=case, run_id=e["run_id"], status="passed", stage="DONE",
                 reason="NONE", checks={CASES[0]: 82, CASES[1]: 123, CASES[2]: 139, CASES[3]: 200}[case], process_deaths=2,
                 last_workspace_read="VALID", last_workspace_utf16_length=80, controller=dict(pid=200, uid=e["controller_uid"], start=900),
                 observations=observations, terminal_observations=terminals, fixture=f)
    if case in CASES[2:]:
        proof.update(load_gate=dict(pid=300, uid=e["product_uid"], started_uptime_ms=950, proof_sha256=digest("synthetic-load")), last_helper_exit=0)
        if case == CASES[2]:
            proof["retirement_helpers"] = [leaf_helper(e, mode) for mode in ("probe", "retire")]
        else:
            proof["retained_helpers"] = [dict(mode=mode, pid=301 + i, uid=e["product_uid"], started_uptime_ms=1500 + i * 100,
                 proof_sha256=digest("synthetic-" + mode)) for i, mode in enumerate(("probe", "retire"))]
    return proof, e


def product_records(proof, version=1):
    assert type(version) is int and version in (1, 2)
    case, f = proof["case"], proof["fixture"]
    target = f["stories"][1] if case == CASES[0] else f["child"] if case == CASES[1] else f["roots_at_creation"][0]
    hint = digest("1\n" + target["story"] + "\n" + target["branch"] + "\n")
    records = {}
    for name, event, index, sequence in (("created", "created", 2, 2), ("saved", "saved_after_super", 1, 21), ("commands", "command", 2, 13)):
        observation = proof["observations"][index]
        ops = dict(workspace=1, branches=0, resume=0, create=0, open=0, play_snapshot=0, **game(ZERO))
        if name != "created":
            ops.update(workspace=4, branches=4, resume=2, open=3, play_snapshot=3)
        if name == "saved":
            ops.update(game(vectors(case)[1]))
        if version == 2:
            ops.update(story_template=0, create_named=0)
        records[name] = encoded(dict(version=version, scope="locallore_process_verify_v" + str(version), run_id=proof["run_id"],
            pid=observation["pid"], uid=observation["uid"], task_id=observation["task"], sequence=sequence,
            process_start_uptime_ms=observation["start"], event=event, restored_state=True, factory_creations=1,
            hint_present=True, hint_sha256=hint, operations=ops))
    return records


def changed(value, path, replacement):
    value = copy.deepcopy(value)
    at = value
    for key in path[:-1]:
        at = at[key]
    at[path[-1]] = replacement
    return value


class ControllerEvidenceTests(unittest.TestCase):
    def refused(self, raw, expected):
        with self.assertRaises(evidence.ControllerEvidenceRefused) as caught:
            evidence.validate_controller_result(raw, expected)
        self.assertEqual(str(caught.exception), "controller_evidence_refused")
        self.assertNotIn(CANARY, str(caught.exception))

    def test_four_closed_positive_fixtures_return_original_parsed_objects(self):
        for case in CASES:
            with self.subTest(case=case):
                proof, expected = original(case)
                raw = frame(proof)
                self.assertLessEqual(len(raw), 4160)
                self.assertEqual(evidence.validate_controller_result(raw, expected), proof)
                self.assertEqual(evidence.validate_controller_result(raw.replace(b"\n", b"\r\n"), expected), proof)
        # No case-dependent validation may mutate the global closed-key schema.
        proof, expected = original()
        self.assertEqual(evidence.validate_controller_result(frame(proof), expected), proof)

    def test_read_only_command_after_save_preserves_terminal_gameplay(self):
        # The synchronized producer has one sequence shared by all three files.
        # A read-only native call may write commands.json after onSaveInstanceState.
        for case in CASES:
            with self.subTest(case=case):
                proof, expected = original(case)
                for terminal in proof["terminal_observations"]:
                    terminal["commands_sequence"] = terminal["saved_sequence"] + 1
                self.assertEqual(evidence.validate_controller_result(frame(proof), expected), proof)
                evidence.validate_product_records(proof, product_records(proof), expected)
                terminal = proof["terminal_observations"][0]
                terminal["commands_sequence"] = terminal["saved_sequence"]
                self.refused(frame(proof), expected)
                terminal["commands_sequence"] += 1
                terminal["commands_game"]["cancel"] += 1
                self.refused(frame(proof), expected)

    def test_quiet_exact_frame_rejects_duplicate_unknown_error_and_trailing_frames(self):
        proof, expected = original()
        raw = frame(proof)
        for bad in (b"", raw[:-1], b"chatter\n" + raw, raw + b"error " + CANARY.encode() + b"\n", raw + raw,
                    raw + b"INSTRUMENTATION_CODE: -1\n", raw.replace(b"INSTRUMENTATION_CODE: -1", b"INSTRUMENTATION_CODE: 0"),
                    raw.replace(b"INSTRUMENTATION_CODE:", b"INSTRUMENTATION_RESULT: shortMsg=failed\nINSTRUMENTATION_CODE:"),
                    raw.replace(b"proof=", b"other="), raw.replace(b"INSTRUMENTATION_RESULT:", b"INSTRUMENTATION_STATUS:"),
                    raw.replace(b"INSTRUMENTATION_CODE:", b"INSTRUMENTATION_FAILED: failed\nINSTRUMENTATION_CODE:"),
                    raw.replace(b"\n", b"\v"), raw.replace(b"\n", b"\r"), b"x" * 4161):
            with self.subTest(length=len(bad)):
                self.refused(bad, expected)
        padded = encoded(proof) + b" " * (4097 - len(encoded(proof)))
        oversized_json = b"INSTRUMENTATION_RESULT: proof=" + padded + b"\nINSTRUMENTATION_CODE: -1\n"
        self.assertLessEqual(len(oversized_json), 4160)
        self.refused(oversized_json, expected)  # JSON cap remains4096 inside the larger frame cap.

    def test_json_duplicate_nested_keys_nonfinite_utf8_and_depth_refuse(self):
        proof, expected = original()
        raw = frame(proof)
        for bad in (raw.replace(b'"version":1', b'"version":1,"version":1', 1),
                    raw.replace(b'"factory":1', b'"factory":1,"factory":1', 1),
                    raw.replace(b'"checks":82', b'"checks":NaN'), raw.replace(b'"checks":82', b'"checks":1e999'),
                    raw.replace(b'"VALID"', b'"\xff"'),
                    b"INSTRUMENTATION_RESULT: proof=" + b"[" * 1200 + b"0" + b"]" * 1200 + b"\nINSTRUMENTATION_CODE: -1\n"):
            self.refused(bad, expected)

    def test_expected_closed_keys_types_and_pins_are_required(self):
        proof, expected = original()
        variants = [dict(expected, extra=CANARY), {k: v for k, v in expected.items() if k != "test_sha256"},
                    dict(expected, case=CANARY), dict(expected, run_id="f" * 16), dict(expected, product_sha256="e" * 64),
                    dict(expected, signature_sha256="e" * 64), dict(expected, controller_uid=True),
                    dict(expected, controller_uid=expected["product_uid"]), dict(expected, product_uid=9999),
                    dict(expected, library_sha256=CANARY)]
        for value in variants:
            self.refused(frame(proof), value)
        for case in CASES[2:]:
            p, e = original(case)
            self.refused(frame(p), dict(e, test_sha256=None))
            self.refused(frame(p), dict(e, library_sha256=None))

    def test_closed_root_result_and_exact_original_three_gold_counts(self):
        for case in CASES[:3]:
            proof, expected = original(case)
            for path, value in ((["version"], True), (["status"], "failed"), (["stage"], "EDIT"), (["reason"], "INTERNAL"),
                                (["checks"], proof["checks"] + 1), (["checks"], True), (["process_deaths"], 1),
                                (["process_deaths"], True), (["run_id"], "f" * 16), (["scope"], CANARY),
                                (["last_workspace_read"], "MISSING"), (["last_workspace_utf16_length"], False)):
                with self.subTest(case=case, path=path):
                    self.refused(frame(changed(proof, path, value)), expected)
            self.refused(frame(dict(proof, extra=CANARY)), expected)

    def test_retained_positive_check_count_is_bounded_diagnostic_not_invented_gold(self):
        proof, expected = original(CASES[3])
        for count in (1, 4096):
            self.assertEqual(evidence.validate_controller_result(frame(dict(proof, checks=count)), expected)["checks"], count)
        for count in (0, 4097, True, 1.0):
            self.refused(frame(dict(proof, checks=count)), expected)

    def test_origin_fixture_scope_root_order_heads_and_cert_cannot_change(self):
        for case in CASES:
            proof, expected = original(case)
            roots_key = "stories" if case == CASES[0] else "roots_at_creation"
            for path, value in ((["fixture", "origin_run_id"], "f" * 16), (["fixture", "origin_product_sha256"], "e" * 64),
                                (["fixture", "scope"], CANARY), (["fixture", "signature_sha256"], "e" * 64),
                                (["fixture", "product_uid"], True), (["fixture", "controller_uid"], 12345),
                                (["fixture", roots_key], proof["fixture"][roots_key][::-1]),
                                (["fixture", roots_key, 0, "head"], 1), (["fixture", roots_key, 0, "branch"], "private/path")):
                self.refused(frame(changed(proof, path, value)), expected)
            self.refused(frame(changed(proof, ["fixture"], dict(proof["fixture"], extra=CANARY))), expected)

    def test_child_and_retained_fixture_scope_hash_and_historical_heads(self):
        for case in CASES[1:]:
            proof, expected = original(case)
            for key in (("parent_text_sha256", "child_draft_sha256") if case in CASES[1:3] else
                        ("root_text_sha256", "retained_prefix_sha256", "unreachable_tail_sha256", "parent_draft_sha256")):
                self.refused(frame(changed(proof, ["fixture", key], "e" * 64)), expected)
            self.refused(frame(changed(proof, ["fixture", "parent", "head"], 0)), expected)
            key = "child" if case in CASES[1:3] else "retained_child"
            self.refused(frame(changed(proof, ["fixture", key, "story"], "other-story")), expected)
            self.refused(frame(changed(proof, ["fixture", key, "branch"], proof["fixture"]["parent"]["branch"])), expected)
            if case in CASES[2:]:
                self.refused(frame(changed(proof, ["fixture", "fixture_test_sha256"], "e" * 64)), expected)

    def test_three_instances_one_task_and_restoration_factories_are_exact(self):
        proof, expected = original()
        mutations = [(["observations"], proof["observations"][:2]), (["observations", 2, "pid"], 202),
                     (["observations", 2, "start"], 2000), (["observations", 2, "task"], 8),
                     (["observations", 0, "restored"], True), (["observations", 1, "restored"], False),
                     (["observations", 2, "factory"], 2), (["observations", 2, "uid"], 12346),
                     (["controller", "pid"], 201), (["controller", "uid"], 12345),
                     (["observations", 0, "pid"], True), (["observations", 2, "start"], 3000.0)]
        for path, value in mutations:
            self.refused(frame(changed(proof, path, value)), expected)

    def test_both_postmortem_terminal_vectors_match_original_producers(self):
        for case in CASES:
            proof, expected = original(case)
            for path, value in ((["terminal_observations"], proof["terminal_observations"][:1]),
                                (["terminal_observations", 0, "pid"], 203), (["terminal_observations", 1, "task"], 8),
                                (["terminal_observations", 1, "saved_sequence"], 20),
                                (["terminal_observations", 0, "saved_game", "cancel"], 1),
                                (["terminal_observations", 1, "commands_game", "other"], 1),
                                (["terminal_observations", 0, "commands_sequence"], True)):
                self.refused(frame(changed(proof, path, value)), expected)

    def test_helper_summaries_and_old_full_proofs_have_closed_shapes_and_pins(self):
        for case in CASES[2:]:
            proof, expected = original(case)
            for path, value in ((["last_helper_exit"], False), (["last_helper_exit"], 1),
                                (["load_gate", "uid"], 12346), (["load_gate", "proof_sha256"], CANARY)):
                self.refused(frame(changed(proof, path, value)), expected)
            key = "retirement_helpers" if case == CASES[2] else "retained_helpers"
            self.refused(frame(changed(proof, [key], proof[key][::-1])), expected)
            self.refused(frame(changed(proof, [key, 0], dict(proof[key][0], extra=CANARY))), expected)
            if case == CASES[2]:
                for path, value in (([key, 0, "test_sha256"], "e" * 64), ([key, 1, "archive_closed"], False),
                                    ([key, 1, "before", "target_active"], 1)):
                    self.refused(frame(changed(proof, path, value)), expected)


class ProductRecordTests(unittest.TestCase):
    def refused(self, proof, records, expected):
        with self.assertRaises(evidence.ControllerEvidenceRefused) as caught:
            evidence.validate_product_records(proof, records, expected)
        self.assertEqual(str(caught.exception), "controller_evidence_refused")

    def test_four_case_final_records_bind_second_old_and_third_restored_processes(self):
        for case in CASES:
            proof, expected = original(case)
            records = product_records(proof)
            before = copy.deepcopy(proof)
            self.assertEqual(evidence.validate_product_records(proof, records, expected),
                             {k: json.loads(v) for k, v in records.items()})
            self.assertEqual(proof, before)

    def test_later_same_process_operation_counters_cannot_decrease(self):
        for case in CASES:
            with self.subTest(case=case):
                proof, expected = original(case)
                records = product_records(proof)
                created = json.loads(records["created"])
                commands = json.loads(records["commands"])
                self.assertGreater(commands["sequence"], created["sequence"])
                for key in ("workspace", "branches", "resume", "open", "play_snapshot"):
                    altered = copy.deepcopy(created)
                    altered["operations"][key] = commands["operations"][key] + 1
                    self.refused(proof, dict(records, created=encoded(altered)), expected)
                evidence.validate_product_records(proof, records, expected)

    def test_fixed_labels_and_json_byte_types_bounds_duplicate_fields(self):
        proof, expected = original()
        records = product_records(proof)
        for bad in ({k + ".json": v for k, v in records.items()}, dict(records, extra=b"{}"),
                    dict(records, saved=b"x" * 4097), dict(records, saved=b"\xff"), dict(records, saved=bytearray(records["saved"])),
                    dict(records, saved=records["saved"].replace(b'"version":1', b'"version":1,"version":1', 1))):
            self.refused(proof, bad, expected)

    def test_record_run_scope_identity_event_hint_factory_and_sequence_are_bound(self):
        proof, expected = original()
        records = product_records(proof)
        for name in records:
            for path, value in ((["run_id"], "f" * 16), (["scope"], CANARY), (["uid"], 12346), (["pid"], 201),
                                (["task_id"], 8), (["process_start_uptime_ms"], 999), (["event"], "other"),
                                (["factory_creations"], True), (["restored_state"], 1), (["hint_present"], False),
                                (["hint_sha256"], "e" * 64), (["sequence"], 0), (["sequence"], 65537)):
                bad = dict(records)
                bad[name] = encoded(changed(json.loads(records[name]), path, value))
                self.refused(proof, bad, expected)

    def test_saved_must_be_second_producer_not_latest_and_terminal_sequence_exact(self):
        proof, expected = original()
        records = product_records(proof)
        saved = json.loads(records["saved"])
        for change in (dict(saved, pid=203, process_start_uptime_ms=3000), dict(saved, sequence=22)):
            self.refused(proof, dict(records, saved=encoded(change)), expected)
        created = json.loads(records["created"])
        self.refused(proof, dict(records, commands=encoded(dict(json.loads(records["commands"]), sequence=created["sequence"]))), expected)

    def test_all_twelve_counters_strict_with_zero_automatic_work_and_exact_saved_game(self):
        for case in CASES:
            proof, expected = original(case)
            records = product_records(proof)
            for name in records:
                record = json.loads(records[name])
                for op, value in (("create", 1), ("workspace", True), ("branches", -1), ("open", 4097), ("resume", 1.0)):
                    bad = dict(records)
                    bad[name] = encoded(changed(record, ["operations", op], value))
                    self.refused(proof, bad, expected)
                bad = dict(records)
                bad[name] = encoded(changed(record, ["operations"], dict(record["operations"], hidden=1)))
                self.refused(proof, bad, expected)
            self.refused(proof, dict(records, commands=encoded(changed(json.loads(records["commands"]), ["operations", "commit"], 1))), expected)
            saved = json.loads(records["saved"])
            altered = 0 if saved["operations"]["prepare"] else 1
            self.refused(proof, dict(records, saved=encoded(changed(saved, ["operations", "prepare"], altered))), expected)

    def test_product_validator_revalidates_proof_instead_of_trusting_prior_call(self):
        proof, expected = original()
        self.refused(dict(proof, process_deaths=1), product_records(proof), expected)

    def test_v2_four_case_records_preserve_closed_v1_result_and_product_bindings(self):
        for case in CASES:
            proof, expected = original(case)
            records = product_records(proof, version=2)
            before = copy.deepcopy(proof)
            parsed = evidence.validate_product_records(proof, records, expected)
            self.assertEqual(parsed, {key: json.loads(raw) for key, raw in records.items()})
            self.assertEqual(proof, before)
            self.assertEqual(proof["version"], 1)
            for value in parsed.values():
                self.assertEqual(value["version"], 2)
                self.assertEqual(set(value["operations"]), set(json.loads(product_records(proof)["created"])["operations"]) |
                                 {"story_template", "create_named"})

    def test_probe_versions_scopes_and_three_record_stream_must_agree(self):
        proof, expected = original()
        historical, current = product_records(proof), product_records(proof, version=2)
        for records in (historical, current):
            for name in records:
                value = json.loads(records[name])
                for version in (True, "2", 2.0, 0, 3):
                    self.refused(proof, dict(records, **{name: encoded(dict(value, version=version))}), expected)
                wrong_scope = "locallore_process_verify_v2" if value["version"] == 1 else "locallore_process_verify_v1"
                self.refused(proof, dict(records, **{name: encoded(dict(value, scope=wrong_scope))}), expected)
        for name in current:
            self.refused(proof, dict(current, **{name: historical[name]}), expected)
            self.refused(proof, dict(historical, **{name: current[name]}), expected)

    def test_v1_rejects_new_keys_and_v2_requires_all_fourteen_exact_counter_keys(self):
        proof, expected = original()
        for version in (1, 2):
            records = product_records(proof, version=version)
            for name in records:
                value = json.loads(records[name])
                if version == 1:
                    for key in ("story_template", "create_named"):
                        operations = dict(value["operations"], **{key: 0})
                        self.refused(proof, dict(records, **{name: encoded(dict(value, operations=operations))}), expected)
                else:
                    for key in value["operations"]:
                        operations = dict(value["operations"])
                        del operations[key]
                        self.refused(proof, dict(records, **{name: encoded(dict(value, operations=operations))}), expected)
                operations = dict(value["operations"], private=CANARY)
                self.refused(proof, dict(records, **{name: encoded(dict(value, operations=operations))}), expected)

    def test_v2_refuses_automatic_named_creation_and_strict_new_counter_types(self):
        for case in CASES:
            proof, expected = original(case)
            records = product_records(proof, version=2)
            for name in records:
                value = json.loads(records[name])
                for op in ("create", "create_named"):
                    self.refused(proof, dict(records, **{name: encoded(changed(value, ["operations", op], 1))}), expected)
                for op in ("story_template", "create_named"):
                    for bad in (True, -1, 4097, 1.0, "1", None):
                        self.refused(proof, dict(records, **{name: encoded(changed(value, ["operations", op], bad))}), expected)

    def test_v2_preview_is_distinct_read_metadata_not_creation_or_gameplay_authority(self):
        proof, expected = original()
        records = product_records(proof, version=2)
        for name, count in (("created", 1), ("saved", 3), ("commands", 2)):
            records[name] = encoded(changed(json.loads(records[name]), ["operations", "story_template"], count))
        parsed = evidence.validate_product_records(proof, records, expected)
        for value in parsed.values():
            self.assertEqual(value["operations"]["create"], 0)
            self.assertEqual(value["operations"]["create_named"], 0)
        self.assertEqual({key: parsed["commands"]["operations"][key] for key in GAME}, game(ZERO))
        # Only counter history is checked here. Native reread still requires the controller's
        # unchanged resume AND play_snapshot increase, never this preview observation.
        bad = encoded(changed(parsed["commands"], ["operations", "story_template"], 0))
        self.refused(proof, dict(records, commands=bad), expected)


if __name__ == "__main__":
    unittest.main()
