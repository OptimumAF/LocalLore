"""Coordinator sequencing checks without SDK, model or ADB.
Copyright 2026 LocalLore contributors. SPDX-License-Identifier: Apache-2.0
"""
import copy
import json
import unittest
from unittest.mock import patch

import android_warm_spike as warm


def request(role):
    return dict(version=1, role=role, prompt="Original synthetic request", max_tokens=10,
                context_tokens=4096, threads=4, schema=None)


def worker():
    return dict(version=1, status="completed", text="PRIVATE-CANARY-123", error=None,
                load_ms=1, generation_ms=2, input_tokens=10, output_tokens=2,
                schema_enforced=True, thinking_disabled=True, template_applied=True)


def owners():
    return dict(engines_opened=1, engines_closed=1, conversations_opened=2, conversations_closed=2,
                warm_roles=2, warm_engine_reused=True, warm_cancel_observed=False, owners_balanced=True,
                worker_off_main=True, generated_text_logged=False, main_pulses=4)


class Session:
    def __init__(self):
        self.calls = []
        self.closed = False
        self.expired = False
        self.final = dict(status="completed", cleanup_complete=True, adb_cleanup_complete=True,
                          directory_cleanup_complete=True, sdk=owners())

    def generate(self, request):
        self.calls.append(request["role"])
        return worker()

    def check_budget(self):
        if self.expired:
            raise warm.WarmFailure("timeout", "validate_director")

    def finish(self):
        self.closed = True
        return self.final


class CoordinatorTests(unittest.TestCase):
    def run_case(self, session, validate=None, commit=None):
        phases = []
        def oracle(unused, binary, operation, case, data=b""):
            phases.append(operation)
            if operation == "fixture":
                return dict(director=request("director"), preflight_error=None)
            if operation == "validate":
                self.assertEqual(session.calls, ["director"])
                return validate() if validate else dict(status="accepted", narrator=request("narrator"))
            self.assertTrue(session.closed, "Canonical commit must follow final SDK/process cleanup")
            return commit if commit is not None else dict(status="committed", revision=1, events=1,
                recipient_observations=1, absent_observations=0, exact_retry_unchanged=True)
        with patch.object(warm.spike, "oracle", side_effect=oracle):
            report = warm.run_warm(session, None, "oracle")
        return report, phases

    def test_rust_validates_before_narrator_and_commits_after_cleanup(self):
        session = Session()
        report, phases = self.run_case(session)
        self.assertEqual(phases, ["fixture", "validate", "commit"])
        self.assertEqual(session.calls, ["director", "narrator"])
        self.assertEqual(report["status"], "committed")
        self.assertNotIn("PRIVATE-CANARY-123", json.dumps(report))

    def test_rejected_director_never_reaches_narrator_or_commit(self):
        session = Session()
        report, phases = self.run_case(session, validate=lambda: dict(status="rejected"))
        self.assertEqual(session.calls, ["director"])
        self.assertEqual(phases, ["fixture", "validate"])
        self.assertEqual(report["status"], "engine_rejected")
        self.assertTrue(session.closed)

    def test_deadline_during_validation_never_starts_second_role(self):
        session = Session()
        def validate():
            session.expired = True
            return dict(status="accepted", narrator=request("narrator"))
        report, phases = self.run_case(session, validate=validate)
        self.assertEqual(report["status"], "timeout")
        self.assertEqual(session.calls, ["director"])
        self.assertNotIn("commit", phases)
        self.assertTrue(session.closed)

    def test_cleanup_proofs_are_strict_and_independent(self):
        for key in ("cleanup_complete", "adb_cleanup_complete", "directory_cleanup_complete"):
            for value in (False, None, 1):
                with self.subTest(key=key, value=value):
                    session = Session()
                    session.final[key] = value
                    report, phases = self.run_case(session)
                    self.assertEqual(report["status"], "cleanup_failed")
                    self.assertNotIn("commit", phases)

    def test_one_model_and_two_fresh_closed_owners_required(self):
        for change in ({"engines_opened": 2, "engines_closed": 2}, {"warm_roles": 0},
                       {"warm_cancel_observed": True}, {"conversations_closed": 1},
                       {"engines_opened": True}, {"generated_text_logged": True}):
            with self.subTest(change=change):
                session = Session()
                session.final["sdk"].update(change)
                report, phases = self.run_case(session)
                self.assertEqual(report["status"], "cleanup_failed")
                self.assertNotIn("commit", phases)

    def test_incorrect_oracle_role_never_reaches_second_sdk_call(self):
        session = Session()
        report, phases = self.run_case(session, validate=lambda: dict(status="accepted", narrator=request("director")))
        self.assertEqual(session.calls, ["director"])
        self.assertEqual(report["status"], "invalid_exchange")
        self.assertNotIn("commit", phases)

    def test_exact_commit_scope_counters_cannot_use_boolean_aliases(self):
        result = dict(status="committed", revision=1, events=1, recipient_observations=1,
                      absent_observations=0, exact_retry_unchanged=True)
        for key in ("revision", "events", "recipient_observations", "absent_observations"):
            report, unused = self.run_case(Session(), commit=dict(result, **{key: bool(result[key])}))
            self.assertEqual(report["status"], "engine_rejected")

    def test_private_final_adapter_fields_are_projected_out(self):
        session = Session()
        session.final.update(exception="PRIVATE-CANARY-123", stage=["PRIVATE-CANARY-123"], wall_ms=10 ** 1000)
        session.final["sdk"]["unexpected"] = "PRIVATE-CANARY-123"
        report, unused = self.run_case(session)
        self.assertNotIn("PRIVATE-CANARY-123", json.dumps(report))
        self.assertEqual(report["session"]["wall_ms"], 0)
        self.assertEqual(report["session"]["stage"], "unknown")


if __name__ == "__main__":
    unittest.main()
