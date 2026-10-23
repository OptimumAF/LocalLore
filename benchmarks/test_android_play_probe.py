"""Model-free controller tests; no Android/model execution is inferred.
Copyright 2026 LocalLore contributors. SPDX-License-Identifier: Apache-2.0
"""
import base64
import copy
import json
from types import SimpleNamespace
import unittest
from unittest.mock import patch

import android_play_probe as play


def generation(role):
    return dict(role=role, status="completed", error=None, load_ms=1 if role == "director" else 0,
                generation_ms=2, input_tokens=100, output_tokens=20, schema_enforced=True,
                thinking_disabled=True, template_applied=True)


def turn():
    return dict(outcome="committed", error=None, roles=2, director_calls=1, narrator_calls=1,
                revision_before=0, revision_after=1, receipts_before=0, receipts_after=1,
                exact_retry=True, reopen_equal=True, canon_unchanged=False, model_initialized=True,
                repairs=0, fallback=False, first_output_observed=False, owner_drained=True,
                generations=[generation("director"), generation("narrator")])


def value(case="gift", row=None):
    row = row or turn()
    result = {k: v for k, v in row.items() if k != "generations"}
    result.update(version=1, case=case, gift_seeded=False, workspace_retained=True, turns=[row])
    return result


def raw(result=None):
    worker = dict(version=1, status="completed", text="", error=None, load_ms=None, generation_ms=None,
                  input_tokens=None, output_tokens=None, schema_enforced=False, thinking_disabled=False, template_applied=False)
    metrics = dict(version=1, mode="play", worker_off_main=True, owners_balanced=True, generated_text_logged=False,
                   engines_opened=1, engines_closed=1, conversations_opened=2, conversations_closed=2, main_pulses=8)
    return ("INSTRUMENTATION_RESULT: result_base64=" + base64.b64encode(json.dumps(worker).encode()).decode() +
            "\nINSTRUMENTATION_RESULT: metrics=" + json.dumps(metrics) +
            "\nINSTRUMENTATION_RESULT: play_result=" + json.dumps(result or value()) +
            "\nINSTRUMENTATION_CODE: -1\n").encode()


class FakeDevice:
    def __init__(self, output=None, model=True, clean=True):
        self.clients_cleaned = True
        self.output = output or raw()
        self.model = model
        self.clean = clean
        self.calls = []

    def shell(self, *args, **kwargs):
        self.calls.append(args)
        if "sha256sum files/" in args[-1]:
            return play.spike.host.ARTIFACTS["litert"][2].encode() + b" model" if self.model else b"absent"
        return b""

    def raw(self, args, **kwargs):
        self.calls.append(args)
        self.clients_cleaned &= self.clean
        return SimpleNamespace(status="completed", returncode=0, cleanup_complete=self.clean, stdout=self.output)


class Sdk:
    def __init__(self, *args): self.stops = 0
    def verify_package(self): pass
    def stop(self): self.stops += 1; return True


class ControllerTests(unittest.TestCase):
    def test_cancel_outcome_cannot_substitute_an_inventory_error_and_completed_role(self):
        row = turn()
        row.update(outcome="cancelled", error="Inventory", roles=1, narrator_calls=0,
                   revision_after=0, receipts_after=0, canon_unchanged=True, exact_retry=False,
                   first_output_observed=True, generations=[generation("director")])
        packet = raw(value("cancel", row)).replace(b'"conversations_opened": 2', b'"conversations_opened": 1') \
            .replace(b'"conversations_closed": 2', b'"conversations_closed": 1')
        self.assertIsNone(play.parse_result(packet, "cancel"))

    def test_valid_accepted_proof_reaches_cleanup_after_terminal_and_stop(self):
        device = FakeDevice()
        with patch.object(play.spike, "SdkWorker", Sdk), patch.object(play, "cleanup_workspace") as cleanup:
            report = play.run_probe(device, "a" * 64, "gift")
        self.assertTrue(report["check_passed"])
        self.assertTrue(report["model_verified"])
        self.assertTrue(report["workspace_removed"])
        cleanup.assert_called_once()
        self.assertEqual(len(report["result"]["turns"][0]["generations"]), 2)

    def test_unknown_client_cleanup_prevents_stop_cleanup_or_success(self):
        device = FakeDevice(clean=False)
        sdk = Sdk()
        with patch.object(play.spike, "SdkWorker", return_value=sdk), patch.object(play, "cleanup_workspace") as cleanup:
            report = play.run_probe(device, "a" * 64, "gift")
        self.assertFalse(report["check_passed"])
        self.assertFalse(report["clients_cleaned"])
        self.assertEqual(sdk.stops, 1)  # Initial proven stop only; no new mutation after uncertain launcher.
        cleanup.assert_not_called()

    def test_invalid_terminal_or_case_identity_cannot_erase_retained_fixture(self):
        for output in (raw() + b"INSTRUMENTATION_CODE: -1\n", raw(value("dialogue")), b"untrusted private payload"):
            with patch.object(play.spike, "SdkWorker", Sdk), patch.object(play, "cleanup_workspace") as cleanup:
                report = play.run_probe(FakeDevice(output), "a" * 64, "gift")
            self.assertFalse(report["check_passed"])
            self.assertEqual(report["status"], "invalid_terminal")
            self.assertNotIn("private", json.dumps(report))
            cleanup.assert_not_called()

    def test_missing_model_gate_does_not_launch_or_provision_anything(self):
        device = FakeDevice(model=False)
        with patch.object(play.spike, "SdkWorker", Sdk), patch.object(play, "cleanup_workspace") as cleanup:
            report = play.run_probe(device, "a" * 64, "gift")
        self.assertEqual(report["status"], "model_missing")
        self.assertFalse(report["check_passed"])
        self.assertEqual(len(device.calls), 1)
        cleanup.assert_not_called()

    def test_original_profile_is_actual_apk_and_manifest_bound(self):
        profile = play.make_profile("a" * 64)
        self.assertEqual(profile["worker_sha256"], "a" * 64)
        self.assertEqual(profile["template_sha256"], profile["model_sha256"])
        self.assertEqual(profile["profile_manifest_sha256"], play.hashlib.sha256(play.PROFILE_PATH.read_bytes()).hexdigest())
        self.assertEqual(profile["deadline_ms"], 60000)
        with self.assertRaises(ValueError): play.make_profile("not a hash")

    def test_recursive_protocol_types_counts_and_private_fields_fail_closed(self):
        mutations = [lambda v: v.update(roles=True), lambda v: v.update(error="PRIVATE TEXT"),
                     lambda v: v.update(unrecognized="PRIVATE TEXT"),
                     lambda v: v["turns"][0].update(owner_drained=False),
                     lambda v: v["turns"][0]["generations"][0].update(text="PRIVATE TEXT"),
                     lambda v: v["turns"][0]["generations"][0].update(input_tokens=0),
                     lambda v: v["turns"][0]["generations"][0].update(output_tokens=351)]
        self.assertIsNotNone(play.parse_result(raw(), "gift"))
        for mutate in mutations:
            v = value(); mutate(v)
            self.assertIsNone(play.parse_result(raw(v), "gift"))


if __name__ == "__main__":
    unittest.main()
