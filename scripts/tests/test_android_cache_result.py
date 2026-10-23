"""Original cache-protocol adversarial evidence, with frozen legacy parser parity.

Copyright 2026 LocalLore contributors. SPDX-License-Identifier: Apache-2.0
"""
import copy
import json
from pathlib import Path
import subprocess
import sys
import types
import unittest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "benchmarks"))
import android_cache_result as decoder
import android_play_probe as play
import test_android_play_probe as fixture

UUID = "ABCD-1234"
BASELINE = "22968a138f9d87a98753684a6f8461d5863568ef"


def value():
    selected = dict(volume_uuid=UUID, mounted=True, primary=False, emulated=False,
                    writable=True, cache_device=20, cache_free_bytes=3 * 1024 ** 3)
    sample = dict(selected, userdata_device=10, userdata_free_bytes=2 * 1024 ** 3, cache_bytes=34)
    metrics = dict(engines_opened=1, engines_closed=1, conversations_opened=2, conversations_closed=2,
                   main_pulses=0, owners_balanced=True, cleanup_requires_process_termination=False,
                   play_roles=2, play_load_ms=1, play_generation_ms=4, play_input_tokens=200, play_output_tokens=40)
    return dict(version=1, operation="play", status="completed", error=None, metrics=metrics,
                volumes=[selected], sample=sample, post_sample=copy.deepcopy(sample),
                play_result=fixture.value(), explicit_cache_directory=True)


def raw(v=None):
    return ("INSTRUMENTATION_RESULT: cache_result=" + json.dumps(value() if v is None else v) +
            "\nINSTRUMENTATION_CODE: -1\n").encode()


def identity():
    v = value()
    del v["play_result"], v["explicit_cache_directory"]
    v.update(operation="verify_model", model_identity=dict(verified=True, sha256=decoder.MODEL_SHA256,
                                                          bytes=decoder.MODEL_BYTES, diagnostic="verified"))
    v["metrics"] = {k: val for k, val in v["metrics"].items() if k not in decoder.PLAY_NUMBERS}
    for k in decoder.COUNTS - {"main_pulses"}:
        v["metrics"][k] = 0
    return v


class CacheResultTests(unittest.TestCase):
    def decode(self, v):
        return decoder.parse_result(raw(v), "gift", UUID)

    def test_exact_receipt_has_no_invented_legacy_or_private_fields(self):
        result = self.decode(value())
        self.assertEqual(result["result"], fixture.value())
        self.assertTrue(result["storage_samples_valid"])
        self.assertEqual(result["sdk"]["main_pulses"], 0)
        self.assertNotIn(UUID, json.dumps(result))
        self.assertNotIn("volumes", result)
        self.assertNotIn("worker_off_main", result["sdk"])
        self.assertNotIn("generated_text_logged", result["sdk"])

    def test_valid_commit_survives_outer_post_failure(self):
        v = value(); v.update(status="error", error="volume_changed"); del v["post_sample"]
        result = self.decode(v)
        self.assertEqual(result["result"]["outcome"], "committed")
        self.assertEqual(result["result"]["receipts_after"], 1)
        self.assertEqual((result["status"], result["error"]), ("error", "volume_changed"))
        self.assertFalse(result["storage_samples_valid"])

    def test_invalid_storage_proof_never_erases_valid_canonical_receipt(self):
        mutations = [lambda v: v["post_sample"].update(cache_device=21),
                     lambda v: v["post_sample"].update(volume_uuid="FFFF-1234"),
                     lambda v: v["sample"].update(writable=False),
                     lambda v: v["post_sample"].update(cache_bytes=True),
                     lambda v: v["post_sample"].update(userdata_device=20),
                     lambda v: v["post_sample"].update(private_path="CANARY"),
                     lambda v: v["volumes"].append(copy.deepcopy(v["volumes"][0])),
                     lambda v: v["volumes"][0].update(cache_free_bytes=1)]
        for mutate in mutations:
            with self.subTest(mutation=mutate):
                v = value(); mutate(v); result = self.decode(v)
                self.assertIsNotNone(result)
                self.assertEqual(result["result"]["outcome"], "committed")
                self.assertFalse(result["storage_samples_valid"])

    def test_pre_engine_fixed_error_retains_error_and_no_receipt(self):
        v = {k: v for k, v in value().items() if k in decoder.BASE}
        v.update(status="error", error="model_missing")
        v["metrics"] = dict(engines_opened=0, engines_closed=0, conversations_opened=0,
                            conversations_closed=0, main_pulses=1, owners_balanced=True,
                            cleanup_requires_process_termination=False)
        result = self.decode(v)
        self.assertIsNone(result["result"])
        self.assertEqual(result["error"], "model_missing")
        self.assertFalse(result["storage_samples_valid"])
        v["metrics"].update(engines_opened=1, engines_closed=1)
        self.assertIsNone(self.decode(v))

    def test_transport_ambiguity_and_invalid_input_fail_closed(self):
        packet = raw()
        candidates = [packet + b"INSTRUMENTATION_CODE: -1\n", packet + packet,
                      b"INSTRUMENTATION_CODE: -1\n" + packet.split(b"\nINSTRUMENTATION_CODE:")[0] + b"\n",
                      packet.replace(b"CODE: -1", b"CODE: 0"),
                      packet + b"INSTRUMENTATION_FAILED: CANARY\n", b"x" * 131073,
                      packet.replace(b'"version": 1', b'"version": 1, "version": 1', 1),
                      packet.replace(b'"play_load_ms": 1', b'"play_load_ms": NaN'),
                      packet.replace(b'"operation": "play"', b'"operation": "\xff"')]
        for packet in candidates:
            self.assertIsNone(decoder.parse_result(packet, "gift", UUID))
        for packet, case, uuid in [(raw(), "unknown", UUID), (raw(), [], UUID),
                                    (raw(), "gift", "../CANARY"), ("text", "gift", UUID)]:
            self.assertIsNone(decoder.parse_result(packet, case, uuid))

    def test_outer_schema_is_closed_and_typed(self):
        for changes in ({"version": True}, {"operation": "inspect"}, {"private_path": "CANARY"},
                        {"status": "success"}, {"error": "CANARY"}, {"explicit_cache_directory": 1},
                        {"volumes": [None]}, {"volumes": [value()["volumes"][0]] * 17}):
            v = value(); v.update(changes)
            self.assertIsNone(self.decode(v), changes)

    def test_metrics_types_ownership_and_unknown_prose_are_rejected(self):
        changes = [{"engines_closed": 0}, {"conversations_closed": 1}, {"owners_balanced": False},
                   {"cleanup_requires_process_termination": True}, {"main_pulses": True},
                   {"play_roles": 2.0}, {"play_roles": 1}, {"play_load_ms": -1},
                   {"play_generation_ms": float("inf")}, {"text": "CANARY"},
                   {"worker_off_main": True}, {"generated_text_logged": False}]
        for change in changes:
            v = value(); v["metrics"].update(change)
            self.assertIsNone(self.decode(v), change)
        for missing in decoder.COUNTS | decoder.PLAY_NUMBERS | {"owners_balanced", "cleanup_requires_process_termination"}:
            v = value(); del v["metrics"][missing]
            self.assertIsNone(self.decode(v), missing)

    def test_receipt_schema_and_case_are_still_authoritative(self):
        mutations = [lambda v: v["play_result"].update(case="dialogue"),
                     lambda v: v["play_result"].update(roles=True),
                     lambda v: v["play_result"]["turns"][0].update(owner_drained=False),
                     lambda v: v["play_result"]["turns"][0]["generations"][0].update(text="CANARY")]
        for mutate in mutations:
            v = value(); mutate(v)
            self.assertIsNone(self.decode(v))

    def test_failed_play_receipt_remains_observable(self):
        row = fixture.turn()
        row.update(outcome="failed", error="model_missing", roles=0, director_calls=0, narrator_calls=0,
                   revision_after=0, receipts_after=0, exact_retry=False, canon_unchanged=True,
                   model_initialized=False, generations=[])
        v = value(); v["play_result"] = fixture.value(row=row)
        v["metrics"].update(engines_opened=0, engines_closed=0, conversations_opened=0,
                            conversations_closed=0, play_roles=0, play_load_ms=0,
                            play_generation_ms=0, play_input_tokens=0, play_output_tokens=0)
        result = self.decode(v)
        self.assertEqual(result["result"]["error"], "model_missing")
        self.assertTrue(result["storage_samples_valid"])

    def test_extracted_legacy_parser_matches_frozen_baseline_goldens(self):
        source = subprocess.run(["git", "show", BASELINE + ":benchmarks/android_play_probe.py"],
                                cwd=ROOT, capture_output=True, check=True).stdout
        baseline = types.ModuleType("frozen_play_baseline")
        baseline.__file__ = str(ROOT / "benchmarks/android_play_probe.py")
        exec(compile(source, baseline.__file__, "exec"), baseline.__dict__)
        packets = [fixture.raw(), fixture.raw(fixture.value("dialogue")),
                   fixture.raw() + b"INSTRUMENTATION_CODE: -1\n", b"CANARY"]
        for key in play.RESULT_KEYS:
            v = fixture.value(); del v[key]; packets.append(fixture.raw(v))
        for key in play.TURN_KEYS:
            v = fixture.value(); del v["turns"][0][key]; packets.append(fixture.raw(v))
        for key in play.GENERATION_KEYS:
            v = fixture.value(); del v["turns"][0]["generations"][0][key]; packets.append(fixture.raw(v))
        for packet in packets:
            for case in ("gift", "dialogue", "unknown"):
                self.assertEqual(play.parse_result(packet, case), baseline.parse_result(packet, case))


class ModelIdentityTests(unittest.TestCase):
    def test_exact_complete_read_becomes_callback_without_paths_or_volume_list(self):
        result = decoder.parse_model_identity(raw(identity()), UUID)
        self.assertEqual(result, dict(identity()["model_identity"], volume_uuid=UUID))
        self.assertEqual(set(result), decoder.MODEL_KEYS | {"volume_uuid"})

    def test_clean_negative_observation_is_retained_without_authorizing_model(self):
        for diagnostic in decoder.MODEL_DIAGNOSTICS - {"verified"}:
            v = identity(); v["model_identity"].update(verified=False, sha256="", bytes=0, diagnostic=diagnostic)
            result = decoder.parse_model_identity(raw(v), UUID)
            self.assertFalse(result["verified"])
            self.assertEqual(result["diagnostic"], diagnostic)

    def test_full_digest_and_size_cannot_be_replaced_by_claimed_verified_flag(self):
        for changes in ({"sha256": "a" * 64}, {"sha256": ""}, {"bytes": decoder.MODEL_BYTES - 1},
                        {"bytes": True}, {"verified": 1}, {"diagnostic": "mismatch"},
                        {"private_path": "CANARY"}, {"diagnostic": "CANARY"}, {"verified": False}):
            v = identity(); v["model_identity"].update(changes)
            self.assertIsNone(decoder.parse_model_identity(raw(v), UUID), changes)

    def test_app_owner_allocation_invalidates_identity_only_operation(self):
        for changes in ({"engines_opened": 1, "engines_closed": 1},
                        {"conversations_opened": 1, "conversations_closed": 1},
                        {"play_roles": 0}, {"owners_balanced": False}, {"cleanup_requires_process_termination": True}):
            v = identity(); v["metrics"].update(changes)
            self.assertIsNone(decoder.parse_model_identity(raw(v), UUID), changes)

    def test_wrong_volume_or_missing_post_proof_cannot_authorize_a_model(self):
        for mutate in (lambda v: v["post_sample"].update(cache_device=21),
                       lambda v: v.pop("post_sample"), lambda v: v.update(status="error", error="volume_changed"),
                       lambda v: v["volumes"].append(copy.deepcopy(v["volumes"][0])),
                       lambda v: v.update(operation="play")):
            v = identity(); mutate(v)
            self.assertIsNone(decoder.parse_model_identity(raw(v), UUID))
        self.assertIsNone(decoder.parse_model_identity(raw(identity()), "FFFF-FFFF"))

    def test_transport_reuses_ordered_unique_strict_terminal(self):
        packet = raw(identity())
        for bad in (packet + packet, b"INSTRUMENTATION_CODE: -1\n" + packet.split(b"\nINSTRUMENTATION_CODE:")[0] + b"\n",
                    packet.replace(b'"bytes": 2588147712', b'"bytes": 2588147712, "bytes": 2588147712')):
            self.assertIsNone(decoder.parse_model_identity(bad, UUID))


if __name__ == "__main__":
    unittest.main()
