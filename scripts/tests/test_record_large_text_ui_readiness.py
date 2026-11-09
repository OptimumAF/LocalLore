"""Advisory SDK19 tests using inert runtime and resource ports.

Copyright 2026 LocalLore contributors. SPDX-License-Identifier: Apache-2.0
"""
from contextlib import ExitStack
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from benchmarks import record_large_text_ui_operation as operation
from scripts import inspect_record_large_text_ui_readiness as readiness
from scripts.tests.test_record_large_text_ui_operation import pin


@unittest.skipUnless(os.name == "nt", "requires physical Windows D: test storage")
class ReadinessTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory(dir="D:/Dev/_Temp")
        self.addCleanup(temporary.cleanup)
        root = Path(temporary.name)
        self.stack = self.enterContext(ExitStack())
        self.mock(readiness, "REPORT", root / "readiness.json")
        self.mock(operation, "AUTHORITY", root / "authority.json")
        self.mock(operation, "LIVE", root / "attempt")
        self.mock(operation, "GUEST", root / "guest")
        self.mock(operation.activation, "RUNTIME", root / "runtime")
        self.mock(operation, "PLAN", root / "plan.json")
        self.mock(operation, "LEDGER", root / "ledger.json")

        readiness.env.create_json(operation.PLAN, {"frozen": True})
        readiness.env.create_json(operation.LEDGER, {"version": 2})
        prepare = root / "prepare.json"
        readiness.env.create_json(prepare, {"memory_mib": 8192})
        self.plan_pin = readiness.env.binding(operation.PLAN)
        self.ledger_pin = readiness.env.binding(operation.LEDGER)
        self.prepare_pin = readiness.env.binding(prepare)
        self.plan = {"prepare": self.prepare_pin}
        self.proposal = {"memory_mib": 8192}
        self.facts = {"resources": {"available_memory": 13 * 1024**3},
                      "storage": {"ledger": self.ledger_pin, "admission_granted": False},
                      "ports_free": True}
        self.loader = self.mock(operation, "_plan", return_value=(self.plan, self.proposal))
        self.preflight = self.mock(operation, "_preflight", return_value=self.facts)
        self.sources = self.mock(operation, "_check_sources")
        self.prepare = self.mock(readiness.env, "prepare")
        self.activation = self.mock(operation.activation, "execute")
        self.reserve = self.mock(operation.storage, "reserve_prepare")

    def mock(self, obj, name, *args, **kwargs):
        return self.stack.enter_context(patch.object(obj, name, *args, **kwargs))

    def tearDown(self):
        self.prepare.assert_not_called()
        self.activation.assert_not_called()
        self.reserve.assert_not_called()
        self.assertFalse(operation.LIVE.exists())

    def inspect(self):
        value = readiness.inspect(self.plan_pin["sha256"])
        self.assertEqual(readiness.env.read_json(readiness.REPORT), value)
        for field in ("execution_authorized", "admission_granted", "feature_acceptance"):
            self.assertIs(value[field], False)
        return value

    def test_pass_binds_exact_plan_prepare_ledger_and_source(self):
        value = self.inspect()
        self.assertIs(value["ready"], True)
        self.assertEqual(value["observations"], self.facts)
        self.assertEqual(value["plan"], self.plan_pin)
        self.assertEqual(value["ledger"], self.ledger_pin)
        self.loader.assert_called_once_with(self.plan_pin)
        self.preflight.assert_called_once_with(self.ledger_pin, self.plan, self.proposal)
        self.sources.assert_called_once_with(self.plan)
        self.assertFalse(operation.AUTHORITY.exists())

    def test_preexisting_report_refuses_before_loading_inputs(self):
        readiness.env.create_json(readiness.REPORT, {"sentinel": True})
        with self.assertRaisesRegex(readiness.env.EnvironmentRefused, "report_exists"):
            readiness.inspect(self.plan_pin["sha256"])
        self.assertEqual(readiness.env.read_json(readiness.REPORT), {"sentinel": True})
        self.loader.assert_not_called()
        self.preflight.assert_not_called()

    def test_digest_mismatch_refuses_before_preflight(self):
        self.plan_pin["sha256"] = "0" * 64
        value = self.inspect()
        self.assertEqual(value["reason"], "binding")
        self.assertIsNone(value["observations"])
        self.preflight.assert_not_called()

    def test_existing_authority_refuses_before_preflight(self):
        readiness.env.create_json(operation.AUTHORITY, {"sentinel": True})
        value = self.inspect()
        self.assertEqual(value["reason"], "already_used")
        self.assertFalse(value["ready"])
        self.preflight.assert_not_called()
        self.assertEqual(readiness.env.read_json(operation.AUTHORITY), {"sentinel": True})

    def test_resource_refusal_has_no_success_observations(self):
        self.preflight.side_effect = readiness.env.EnvironmentRefused("host_commit_capacity")
        value = self.inspect()
        self.assertEqual(value["reason"], "host_commit_capacity")
        self.assertIsNone(value["observations"])
        self.assertFalse(value["ready"])

    def test_late_drift_discards_observed_success(self):
        def drift(*_args):
            operation.LEDGER.write_text("different ledger", encoding="utf-8")
            return self.facts

        self.preflight.side_effect = drift
        value = self.inspect()
        self.assertFalse(value["ready"])
        self.assertIsNone(value["observations"])

    def test_guest_appearing_after_preflight_revokes_success(self):
        def appear(_plan):
            operation.GUEST.mkdir()

        self.sources.side_effect = appear
        value = self.inspect()
        self.assertFalse(value["ready"])
        self.assertEqual(value["reason"], "already_used")
        self.assertIsNone(value["observations"])

    def test_cancellation_retains_nonready_receipt(self):
        self.preflight.side_effect = KeyboardInterrupt("untrusted payload")
        value = self.inspect()
        self.assertEqual(value["reason"], "cancelled")
        self.assertFalse(value["ready"])
        self.assertNotIn("untrusted", repr(value))


class PreflightTests(unittest.TestCase):
    def test_different_ledger_preview_refuses_before_installed_checks(self):
        ledger = pin(operation.LEDGER)
        preview = {"ledger": pin(operation.LEDGER, b"another ledger"),
                   "would_fit": True, "admission_granted": False}
        with (patch.object(operation, "_at", return_value={"version": 2}),
              patch.object(operation.os.path, "lexists", return_value=False),
              patch.object(operation.env, "safe_path"),
              patch.object(operation.storage, "_validate"),
              patch.object(operation.storage, "preview_prepare", return_value=preview),
              patch.object(operation.server, "revalidate_inputs") as revalidate):
            with self.assertRaisesRegex(readiness.env.EnvironmentRefused, "binding"):
                operation._preflight(ledger, {}, {})
            revalidate.assert_not_called()
