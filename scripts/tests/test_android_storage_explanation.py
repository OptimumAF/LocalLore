"""Independent accounting, refusal and privacy cases; no device or SDK access.

Copyright 2026 LocalLore contributors. SPDX-License-Identifier: Apache-2.0
"""
import contextlib
import copy
import io
import json
from pathlib import Path
import sys
import tempfile
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "benchmarks"))
import android_cache_volume as gate

GIB = 1024 ** 3
MIB = 1024 ** 2
UUID = "FEED-BAAD"
TOP_KEYS = {"version", "scope", "policy_version", "error", "post", "comparison_available", "host_groups"}
ROW_KEYS = {"roles", "before_free_bytes", "after_free_bytes", "net_consumption_bytes",
            "reserve_bytes", "allowance_bytes", "reserve_satisfied", "consumption_satisfied"}
ROLES = ("userdata", "cache", "evidence")
HOST_FIELDS = ("userdata_host_volume", "cache_host_volume", "evidence_host_volume")
FREE_FIELDS = ("userdata_host_free_bytes", "cache_host_free_bytes", "evidence_free_bytes")


def sample(partition=(0, 1, 1)):
    return {"version": 1, "volume_uuid": UUID, "userdata_device": 17, "cache_device": 29,
            "mounted": True, "primary": False, "emulated": False, "writable": True,
            "backing_verified": True, "userdata_free_bytes": 8 * GIB,
            "cache_free_bytes": 12 * GIB, "cache_bytes": 12345,
            **{key: "private-host-" + str(group) for key, group in zip(HOST_FIELDS, partition)},
            **{key: 24 * GIB for key in FREE_FIELDS}}


def host_free(value, role, amount):
    """Update one physical group, including every aliasing role measurement."""
    alias = value[HOST_FIELDS[ROLES.index(role)]]
    for host_key, free_key in zip(HOST_FIELDS, FREE_FIELDS):
        if value[host_key] == alias:
            value[free_key] = amount


class StorageExplanationTests(unittest.TestCase):
    def explain(self, before, after, size=0):
        result = gate.explain_post(before, after, UUID, size)
        self.assertEqual(set(result), TOP_KEYS)
        self.assertEqual(result["version"], 1)
        self.assertEqual(result["scope"], "android_cache_post_explanation")
        self.assertEqual(result["policy_version"], 1)
        self.assertIsNone(result["error"])
        self.assertEqual(result["post"], gate.after_probe(before, after, UUID, size))
        for row in result["host_groups"]:
            self.assertEqual(set(row), ROW_KEYS)
            self.assertIs(type(row["reserve_satisfied"]), bool)
            self.assertIs(type(row["consumption_satisfied"]), bool)
        return result

    def test_all_five_physical_partitions_have_exact_reserve_sum_and_role_order(self):
        for partition in ((0, 1, 2), (0, 0, 1), (0, 1, 0), (0, 1, 1), (0, 0, 0)):
            with self.subTest(partition=partition):
                value = sample(partition)
                result = self.explain(value, value, 37)
                self.assertIs(result["comparison_available"], True)
                expected = []
                for group in dict.fromkeys(partition):
                    roles = [role for role, item in zip(ROLES, partition) if item == group]
                    expected.append({"roles": roles, "before_free_bytes": 24 * GIB,
                                     "after_free_bytes": 24 * GIB, "net_consumption_bytes": 0,
                                     "reserve_bytes": 10 * GIB if "evidence" in roles else 4 * GIB,
                                     "allowance_bytes": (64 * MIB if "userdata" in roles else 0)
                                     + (GIB + 37 if "cache" in roles else 0),
                                     "reserve_satisfied": True, "consumption_satisfied": True})
                self.assertEqual(result["host_groups"], expected)

    def test_group_order_does_not_follow_private_alias_lexical_order(self):
        before = sample((0, 1, 2))
        after = copy.deepcopy(before)
        host_free(after, "userdata", 24 * GIB - 11)
        host_free(after, "cache", 24 * GIB - 22)
        host_free(after, "evidence", 24 * GIB - 33)
        original = self.explain(before, after)
        for value in (before, after):
            value.update(dict(zip(HOST_FIELDS, ("z-last", "m-middle", "a-first"))))
        self.assertEqual(self.explain(before, after), original)

    def test_signed_delta_records_space_freed_without_causal_or_budget_failure(self):
        before, after = sample(), sample()
        host_free(after, "userdata", 24 * GIB + 71)
        host_free(after, "cache", 24 * GIB + 23)
        result = self.explain(before, after)
        self.assertEqual([row["net_consumption_bytes"] for row in result["host_groups"]], [-71, -23])
        self.assertTrue(all(row["consumption_satisfied"] for row in result["host_groups"]))
        self.assertEqual(result["post"]["status"], "admitted")

    def test_userdata_consumption_boundary_is_64_mib_not_cache_gib(self):
        for delta, satisfied in ((64 * MIB - 1, True), (64 * MIB, True), (64 * MIB + 1, False)):
            with self.subTest(delta=delta):
                before, after = sample(), sample()
                host_free(after, "userdata", 24 * GIB - delta)
                result = self.explain(before, after)
                row = result["host_groups"][0]
                self.assertEqual(row["allowance_bytes"], 64 * MIB)
                self.assertIs(row["consumption_satisfied"], satisfied)
                self.assertIs(row["reserve_satisfied"], True)
                self.assertEqual(result["post"]["reasons"], [] if satisfied else ["host_consumption_budget"])

    def test_shared_group_consumption_includes_copy_once_only(self):
        size = 2588147712
        allowance = 64 * MIB + GIB + size
        before, after = sample((0, 0, 0)), sample((0, 0, 0))
        host_free(after, "cache", 24 * GIB - allowance)
        result = self.explain(before, after, size)
        self.assertEqual(len(result["host_groups"]), 1)
        self.assertEqual(result["host_groups"][0]["allowance_bytes"], allowance)
        self.assertIs(result["host_groups"][0]["consumption_satisfied"], True)
        host_free(after, "cache", 24 * GIB - allowance - 1)
        self.assertIs(self.explain(before, after, size)["host_groups"][0]["consumption_satisfied"], False)

    def test_evidence_only_group_has_zero_consumption_allowance(self):
        before, after = sample((0, 1, 2)), sample((0, 1, 2))
        host_free(after, "evidence", 24 * GIB - 1)
        result = self.explain(before, after, 101)
        self.assertEqual(result["host_groups"][2]["allowance_bytes"], 0)
        self.assertIs(result["host_groups"][2]["consumption_satisfied"], False)
        self.assertEqual(result["post"]["reasons"], ["host_consumption_budget"])

    def test_reserve_and_consumption_flags_are_independent(self):
        before, after = sample((0, 1, 2)), sample((0, 1, 2))
        host_free(before, "userdata", 4 * GIB + 64 * MIB)
        host_free(after, "userdata", 4 * GIB)
        result = self.explain(before, after)
        self.assertIs(result["host_groups"][0]["reserve_satisfied"], True)
        self.assertIs(result["host_groups"][0]["consumption_satisfied"], True)
        host_free(after, "userdata", 4 * GIB - 1)
        result = self.explain(before, after)
        self.assertIs(result["host_groups"][0]["reserve_satisfied"], False)
        self.assertIs(result["host_groups"][0]["consumption_satisfied"], False)
        self.assertEqual(result["post"]["reasons"], ["host_reserve", "host_consumption_budget"])

    def test_guest_only_failure_is_not_falsely_explained_by_host_rows(self):
        before, after = sample(), sample()
        after["userdata_free_bytes"] = GIB - 1
        result = self.explain(before, after)
        self.assertEqual(result["post"]["status"], "blocked")
        self.assertTrue(all(row["reserve_satisfied"] and row["consumption_satisfied"]
                            for row in result["host_groups"]))

    def test_all_identity_drift_suppresses_rows_even_with_large_delta(self):
        changes = {"volume_uuid": "DEAD-BEEF", "userdata_device": 18, "cache_device": 30,
                   "userdata_host_volume": "replacement-u", "cache_host_volume": "replacement-c",
                   "evidence_host_volume": "replacement-e", "mounted": False, "primary": True,
                   "emulated": True, "writable": False, "backing_verified": False}
        for key, value in changes.items():
            with self.subTest(key=key):
                before, after = sample(), sample()
                after[key] = value
                after.update({field: 0 for field in FREE_FIELDS})
                result = self.explain(before, after)
                self.assertIs(result["comparison_available"], False)
                self.assertEqual(result["host_groups"], [])
                self.assertEqual(result["post"]["reasons"], ["identity_changed"])

    def test_blocked_before_never_produces_comparison_even_if_after_recovers(self):
        for changes in ({"mounted": False}, {"userdata_host_free_bytes": 4 * GIB},
                        {"cache_free_bytes": GIB}, {"volume_uuid": "DEAD-BEEF"}):
            with self.subTest(changes=changes), self.assertRaises(gate.InvalidSample):
                gate.explain_post({**sample(), **changes}, sample(), UUID)

    def test_invalid_shape_types_overflow_and_inconsistent_aliases_refuse_both_sides(self):
        bad = [None, [], {**sample(), "extra_private": "secret"}]
        missing = sample(); del missing["cache_bytes"]; bad.append(missing)
        for key, values in (("version", (True, 1.0)), ("cache_device", (True, 0)),
                            ("userdata_host_free_bytes", (True, -1, 1.0, 2 ** 63)),
                            ("mounted", (1, None)), ("cache_host_volume", ("/private", "x" * 65))):
            bad.extend({**sample(), key: value} for value in values)
        bad.append({**sample(), "evidence_free_bytes": 24 * GIB - 1})
        for value in bad:
            for left, right in ((value, sample()), (sample(), value)):
                with self.subTest(value=value), self.assertRaises(gate.InvalidSample):
                    gate.explain_post(left, right, UUID)

    def test_invalid_copy_and_expected_uuid_do_not_fall_through_on_identity_drift(self):
        after = {**sample(), "volume_uuid": "DEAD-BEEF"}
        for value in (True, -1, 1.0, "1", None, 2 ** 63 - 1):
            with self.subTest(copy=value), self.assertRaises(gate.InvalidSample):
                gate.explain_post(sample(), after, UUID, value)
        for value in (None, "", UUID + "\n", 17):
            with self.subTest(uuid=value), self.assertRaises(gate.InvalidSample):
                gate.explain_post(sample(), after, value)

    def test_inputs_are_not_mutated_and_output_does_not_alias_them(self):
        before, after = sample(), sample()
        original = copy.deepcopy((before, after))
        result = self.explain(before, after)
        self.assertEqual((before, after), original)
        result["post"]["bytes"]["cache_bytes"] = 0
        result["host_groups"][0]["roles"].append("private")
        self.assertEqual((before, after), original)
        self.assertEqual(self.explain(before, after)["host_groups"][0]["roles"], ["userdata"])

    def test_large_valid_integer_delta_remains_exact_and_signed(self):
        before, after = sample((0, 1, 2)), sample((0, 1, 2))
        host_free(before, "userdata", 2 ** 63 - 1)
        host_free(after, "userdata", 4 * GIB)
        self.assertEqual(self.explain(before, after)["host_groups"][0]["net_consumption_bytes"],
                         2 ** 63 - 1 - 4 * GIB)

    def test_public_report_never_exposes_alias_uuid_device_or_causal_claim(self):
        result = self.explain(sample(), sample())
        encoded = json.dumps(result)
        for private in (UUID, "private-host", "volume_uuid", "userdata_device", "cache_device",
                        "host_volume", "cause", "sdk", "process"):
            self.assertNotIn(private, encoded)

    def test_prior_failed_observation_has_one_failed_host_group_without_attribution(self):
        before, after = sample(), sample()
        before.update(userdata_free_bytes=1674461184, cache_free_bytes=3619602432,
                      cache_bytes=2365238344, userdata_host_free_bytes=12667879424,
                      cache_host_free_bytes=322707947520, evidence_free_bytes=322707947520)
        after.update(userdata_free_bytes=1674371072, cache_free_bytes=2831179776,
                     cache_bytes=3153651114, userdata_host_free_bytes=10284752896,
                     cache_host_free_bytes=321902133248, evidence_free_bytes=321902133248)
        result = self.explain(before, after)
        self.assertEqual(result["post"]["reasons"], ["host_consumption_budget"])
        self.assertEqual([row["net_consumption_bytes"] for row in result["host_groups"]],
                         [2383126528, 805814272])
        self.assertEqual([row["allowance_bytes"] for row in result["host_groups"]], [64 * MIB, GIB])
        self.assertEqual([row["consumption_satisfied"] for row in result["host_groups"]], [False, True])
        self.assertTrue(all(row["reserve_satisfied"] for row in result["host_groups"]))

    def cli(self, before_raw, after_raw=None):
        with tempfile.TemporaryDirectory() as directory:
            before, after = Path(directory) / "private-before.json", Path(directory) / "private-after.json"
            before.write_bytes(before_raw)
            argv = ["--sample", str(before), "--volume-uuid", UUID]
            if after_raw is not None:
                after.write_bytes(after_raw)
                argv += ["--after-sample", str(after)]
            with contextlib.redirect_stdout(io.StringIO()) as output:
                code = gate.main(argv)
            text = output.getvalue()
            self.assertNotIn(directory, text)
            self.assertNotIn(UUID, text)
            self.assertNotIn("private-host", text)
            return code, json.loads(text)

    def test_cli_new_mode_preserves_old_mode_and_exact_post_result(self):
        before = sample(); raw = json.dumps(before).encode()
        code, value = self.cli(raw)
        self.assertEqual((code, value), (0, gate.before_probe(before, UUID)))
        for after, expected in ((sample(), 0), ({**sample(), "userdata_free_bytes": 0}, 2),
                                ({**sample(), "volume_uuid": "DEAD-BEEF"}, 2)):
            code, value = self.cli(raw, json.dumps(after).encode())
            self.assertEqual(code, expected)
            self.assertEqual(value, self.explain(before, after))

    def test_cli_malformed_inputs_emit_only_fixed_envelope_without_partial_rows(self):
        valid = json.dumps(sample()).encode()
        malformed = (b'{"version":1,"version":1}', b'{"version":NaN}', b'\xff', b'x' * 16385,
                     json.dumps({**sample(), "private_override": "secret"}).encode())
        expected = {"version": 1, "scope": "android_cache_post_explanation", "policy_version": 1,
                    "error": "sample_failed", "post": None, "comparison_available": False, "host_groups": []}
        for bad in malformed:
            for left, right in ((bad, valid), (valid, bad)):
                with self.subTest(raw=bad[:40]):
                    code, value = self.cli(left, right)
                    self.assertEqual((code, value), (1, expected))

    def test_cli_blocked_pre_is_malformed_comparison_but_blocked_post_is_verdict(self):
        valid = json.dumps(sample()).encode()
        blocked = json.dumps({**sample(), "mounted": False}).encode()
        code, value = self.cli(blocked, valid)
        self.assertEqual(code, 1)
        self.assertEqual(set(value), TOP_KEYS)
        self.assertEqual(value["error"], "sample_failed")
        self.assertIsNone(value["post"])
        self.assertEqual(value["host_groups"], [])
        code, value = self.cli(valid, blocked)
        self.assertEqual(code, 2)
        self.assertIsNone(value["error"])
        self.assertEqual(value["post"]["reasons"], ["identity_changed"])

    def test_cli_exact_size_boundary_and_missing_after_path_are_sanitized(self):
        raw = json.dumps(sample()).encode()
        padded = raw + b' ' * (16384 - len(raw))
        self.assertEqual(self.cli(padded, padded)[0], 0)
        self.assertEqual(self.cli(padded, padded + b' ')[0], 1)
        with tempfile.TemporaryDirectory() as directory:
            before = Path(directory) / "private-before.json"
            after = Path(directory) / "private-absent-after.json"
            before.write_bytes(raw)
            with contextlib.redirect_stdout(io.StringIO()) as output:
                code = gate.main(["--sample", str(before), "--after-sample", str(after), "--volume-uuid", UUID])
            self.assertEqual(code, 1)
            self.assertNotIn(directory, output.getvalue())
            self.assertEqual(json.loads(output.getvalue()), {
                "version": 1, "scope": "android_cache_post_explanation", "policy_version": 1,
                "error": "sample_failed", "post": None, "comparison_available": False, "host_groups": []})


if __name__ == "__main__":
    unittest.main()
