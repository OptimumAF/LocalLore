"""Independent aggregate/dispatch regressions; no SDK, model, ADB or subprocess.

Copyright 2026 LocalLore contributors. SPDX-License-Identifier: Apache-2.0
"""
import base64
import copy
import json
from types import SimpleNamespace
import unittest
from unittest.mock import patch

import android_play_probe as play


def generation(role="director", status="completed", error=None):
    complete = status == "completed"
    return dict(role=role, status=status, error=error, load_ms=1 if complete else None,
                generation_ms=2 if complete else None, input_tokens=100 if complete else None,
                output_tokens=10 if complete else None, schema_enforced=complete,
                thinking_disabled=complete, template_applied=complete)


def turn(outcome="committed", error=None, before=0, repaired=False):
    committed = outcome == "committed"
    generations = ([generation()] + ([generation()] if repaired else []) +
                   [generation("narrator")]) if committed else []
    return dict(outcome=outcome, error=error, roles=len(generations),
                director_calls=sum(g["role"] == "director" for g in generations),
                narrator_calls=sum(g["role"] == "narrator" for g in generations),
                revision_before=before, revision_after=before + int(committed),
                receipts_before=before, receipts_after=before + int(committed),
                repairs=int(repaired), exact_retry=committed, reopen_equal=True,
                canon_unchanged=not committed, model_initialized=committed,
                fallback=False, first_output_observed=False, owner_drained=True,
                generations=generations)


def result(case="gift", turns=None):
    turns = copy.deepcopy(turns if turns is not None else [turn()])
    value = copy.deepcopy(turns[-1])
    del value["generations"]
    value.update(version=1, case=case, workspace_retained=True,
                 gift_seeded=case == "spent" and turns[0]["outcome"] == "committed", turns=turns)
    for key in ("roles", "director_calls", "narrator_calls", "repairs"):
        value[key] = sum(t[key] for t in turns)
    for key in ("revision_before", "receipts_before"):
        value[key] = turns[0][key]
    for key in ("model_initialized", "fallback", "first_output_observed"):
        value[key] = any(t[key] for t in turns)
    for key in ("owner_drained", "reopen_equal", "exact_retry"):
        value[key] = all(t[key] for t in turns)
    value["canon_unchanged"] = (value["revision_before"] == value["revision_after"] and
                               value["receipts_before"] == value["receipts_after"])
    return value


def metrics(value):
    initialized = sum(t["model_initialized"] for t in value["turns"])
    conversations = sum(g["status"] == "completed" for t in value["turns"] for g in t["generations"])
    return dict(version=1, mode="play", worker_off_main=True, owners_balanced=True,
                generated_text_logged=False, engines_opened=initialized, engines_closed=initialized,
                conversations_opened=conversations, conversations_closed=conversations,
                main_pulses=3)


def envelope(value, sdk=None, ack=None):
    if sdk is None:
        sdk = metrics(value)
    if ack is None:
        ack = dict(version=1, status="completed", text="", error=None, load_ms=None,
                   generation_ms=None, input_tokens=None, output_tokens=None,
                   schema_enforced=False, thinking_disabled=False, template_applied=False)
    encode = lambda v: json.dumps(v, separators=(",", ":")).encode("utf-8")
    return (b"INSTRUMENTATION_RESULT: result_base64=" + base64.b64encode(encode(ack)) + b"\n" +
            b"INSTRUMENTATION_RESULT: metrics=" + encode(sdk) + b"\n" +
            b"INSTRUMENTATION_RESULT: play_result=" + encode(value) + b"\n" +
            b"INSTRUMENTATION_CODE: -1\n")


class AggregateReviewTests(unittest.TestCase):
    def reject(self, value, sdk=None, ack=None):
        self.assertIsNone(play.parse_result(envelope(value, sdk, ack), value["case"]))

    def test_valid_committed_repaired_and_early_rule_rejection_are_distinct(self):
        for value in (result(), result(turns=[turn(repaired=True)]),
                      result("unlearned", [turn("rejected", "Ability")])):
            with self.subTest(case=value["case"], repairs=value["repairs"]):
                self.assertIsNotNone(play.parse_result(envelope(value), value["case"]))

    def test_outer_runtime_error_cannot_borrow_successful_play_result(self):
        ack = dict(version=1, status="error", text="", error="runtime_failed", load_ms=None,
                   generation_ms=None, input_tokens=None, output_tokens=None,
                   schema_enforced=False, thinking_disabled=False, template_applied=False)
        self.reject(result(), ack=ack)

    def test_committed_turn_cannot_contain_failed_generation(self):
        value = result()
        value["turns"][0]["generations"][0] = generation(status="error", error="Provider")
        self.reject(value)

    def test_role_order_and_repair_count_describe_the_same_attempt(self):
        first = turn()
        first["generations"].reverse()
        self.reject(result(turns=[first]))
        for repaired, count in ((False, 1), (True, 0)):
            row = turn(repaired=repaired)
            row["repairs"] = count
            self.reject(result(turns=[row]))

    def test_aggregate_retry_and_reopen_proofs_cannot_override_turns(self):
        for key in ("exact_retry", "reopen_equal", "owner_drained", "model_initialized", "fallback"):
            value = result()
            value[key] = not value[key]
            with self.subTest(key=key):
                self.reject(value)

    def test_balanced_owner_numbers_must_match_successful_roles(self):
        value = result()
        for change in ({"engines_opened": 0, "engines_closed": 0},
                       {"conversations_opened": 0, "conversations_closed": 0},
                       {"conversations_opened": 1, "conversations_closed": 1},
                       {"cleanup_requires_process_termination": True}):
            sdk = metrics(value)
            sdk.update(change)
            with self.subTest(change=change):
                self.reject(value, sdk=sdk)

    def test_success_requires_each_schema_template_and_thinking_proof(self):
        for key in ("schema_enforced", "thinking_disabled", "template_applied"):
            value = result()
            value["turns"][0]["generations"][0][key] = False
            self.reject(value)

    def test_private_fields_cannot_enter_result_turn_or_generation(self):
        for location in ("result", "turn", "generation"):
            value = result()
            target = value if location == "result" else value["turns"][0]
            if location == "generation":
                target = target["generations"][0]
            target["text"] = "PRIVATE-PROSE-CANARY"
            self.reject(value)
        value = result()
        sdk = metrics(value)
        sdk["unrecognized_private_text"] = "PRIVATE-PROSE-CANARY"
        parsed = play.parse_result(envelope(value, sdk), "gift")
        self.assertIsNotNone(parsed)
        self.assertNotIn("PRIVATE-PROSE-CANARY", json.dumps(parsed))

    def test_protocol_duplicates_abort_wrong_case_and_nonfinite_fail_closed(self):
        raw = envelope(result())
        rows = raw.splitlines(keepends=True)
        variants = [raw + rows[0], raw + rows[1], raw + rows[2], raw + rows[3],
                    raw.replace(b"INSTRUMENTATION_CODE: -1", b"INSTRUMENTATION_CODE: 0"),
                    raw + b"INSTRUMENTATION_FAILED: PRIVATE-PROSE-CANARY\n", b"x" * 131073]
        for data in variants:
            self.assertIsNone(play.parse_result(data, "gift"))
        self.assertIsNone(play.parse_result(raw, "dialogue"))
        value = result()
        value["turns"][0]["generations"][0]["generation_ms"] = float("nan")
        self.reject(value)

    def test_numeric_boolean_aliases_and_token_overflow_are_not_proofs(self):
        for key in ("version", "roles", "revision_before", "receipts_after"):
            value = result()
            value[key] = bool(value[key])
            self.reject(value)
        for key, bad in (("input_tokens", 4096), ("output_tokens", 0), ("output_tokens", 351)):
            value = result()
            value["turns"][0]["generations"][0][key] = bad
            self.reject(value)


class FakeDevice:
    def __init__(self, raw, missing=False, client_cleanup=True):
        self.stdout = raw
        self.missing = missing
        self.client_cleanup = client_cleanup
        self.clients_cleaned = True
        self.calls = []

    def shell(self, *args, **kwargs):
        self.calls.append("model_identity")
        return b"absent" if self.missing else play.spike.host.ARTIFACTS["litert"][2].encode("ascii") + b" model\n"

    def raw(self, *args, **kwargs):
        self.calls.append("instrumentation")
        self.clients_cleaned = self.client_cleanup
        return SimpleNamespace(status="completed", returncode=0, cleanup_complete=self.client_cleanup,
                               stdout=self.stdout)


class DispatchReviewTests(unittest.TestCase):
    def run_fake(self, value, sdk=None, missing=False, allow_missing=False,
                 client_cleanup=True, final_stop=True):
        device = FakeDevice(envelope(value, sdk), missing, client_cleanup)
        stops = []

        class FakeSdk:
            def __init__(self, unused_device, unused_hash):
                pass

            def verify_package(self):
                device.calls.append("verify_package")

            def stop(self):
                device.calls.append("stop")
                stops.append(True)
                return True if len(stops) == 1 else final_stop

        with patch.object(play.spike, "SdkWorker", FakeSdk), \
                patch.object(play, "make_profile", return_value={}), \
                patch.object(play, "cleanup_workspace") as cleanup:
            report = play.run_probe(device, "a" * 64, value["case"], allow_missing)
            return report, device.calls, cleanup.call_count

    def test_cleanup_is_after_terminal_stop_and_all_client_ownership(self):
        report, calls, removed = self.run_fake(result())
        self.assertTrue(report["check_passed"])
        self.assertEqual(1, removed)
        self.assertEqual(["verify_package", "stop", "model_identity", "instrumentation", "stop"], calls)
        for options in ({"client_cleanup": False}, {"final_stop": False}):
            report, calls, removed = self.run_fake(result(), **options)
            self.assertFalse(report["check_passed"])
            self.assertEqual(0, removed)
            if options.get("client_cleanup") is False:
                self.assertEqual(1, calls.count("stop"), "Unknown client cleanup prohibits new stop dispatch")

    def test_unknown_native_owner_never_authorizes_directory_deletion(self):
        row = turn("rejected", "Ability")
        row["owner_drained"] = False
        report, unused, removed = self.run_fake(result("unlearned", [row]))
        self.assertFalse(report["check_passed"])
        self.assertEqual(0, removed)

    def test_rejection_case_must_exercise_its_named_rule(self):
        for case, rows in (("unlearned", [turn("rejected", "Provider")]),
                           ("spent", [turn(), turn("rejected", "Provider", before=1)])):
            report, unused, unused_removed = self.run_fake(result(case, rows))
            self.assertFalse(report["check_passed"], "A provider error is not proof of the named mechanical rule")

    def test_missing_model_proof_cannot_claim_a_model_was_initialized(self):
        row = turn("failed", "model_missing")
        row.update(roles=1, director_calls=1, generations=[generation(status="error", error="model_missing")])
        value = result(turns=[row])
        report, unused, removed = self.run_fake(value, missing=True, allow_missing=True)
        self.assertTrue(report["check_passed"])
        self.assertEqual(1, removed)
        value["model_initialized"] = value["turns"][0]["model_initialized"] = True
        report, unused, unused_removed = self.run_fake(value, missing=True, allow_missing=True)
        self.assertFalse(report["check_passed"])

    def test_no_model_probe_does_not_launch_without_explicit_missing_case(self):
        report, calls, removed = self.run_fake(result(), missing=True)
        self.assertFalse(report["check_passed"])
        self.assertEqual("model_missing", report["status"])
        self.assertNotIn("instrumentation", calls)
        self.assertEqual(0, removed)

    def test_cancel_needs_active_output_sdk_cancel_and_terminal_drain(self):
        row = turn("cancelled", "Cancelled")
        row.update(roles=1, director_calls=1, generations=[generation(status="cancelled", error="Cancelled")],
                   model_initialized=True, first_output_observed=True)
        value = result("cancel", [row])
        sdk = metrics(value)
        sdk.update(conversations_opened=1, conversations_closed=1, cancel_called=True, cancel_terminal_callback=True)
        report, unused, unused_removed = self.run_fake(value, sdk=sdk)
        self.assertTrue(report["check_passed"])
        for key in ("cancel_called", "cancel_terminal_callback"):
            broken = dict(sdk, **{key: False})
            report, unused, unused_removed = self.run_fake(value, sdk=broken)
            self.assertFalse(report["check_passed"])


if __name__ == "__main__":
    unittest.main()
