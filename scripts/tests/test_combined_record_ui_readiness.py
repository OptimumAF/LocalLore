"""Synthetic SDK21 readiness checks with inert filesystem and host ports."""

from contextlib import ExitStack, contextmanager, redirect_stdout
from io import StringIO
import json
from pathlib import Path
import unittest
from unittest.mock import Mock, patch

from benchmarks import combined_record_ui_readiness as readiness
from scripts.tests.test_combined_record_ui_handoff import BootRecords, REFUSED


handoff = readiness.handoff
preparation = readiness.preparation
env = handoff.env
GIB = 1024 ** 3
PRIVATE = "synthetic-private-proof"


class ReadinessRecords:
    """Use the real binding and plan decoders with inert filesystem ports."""

    def __init__(self):
        self.graph = BootRecords()
        self.plan_pin, self.plan = self.graph.read(handoff.PLAN)
        self.ledger_pin = self.graph.ledger_pin
        self.host = dict(free_bytes={"C:": 50 * GIB, "D:": 80 * GIB},
                         available_memory=24 * GIB, logical_cpus=12,
                         commit_capacity=dict(version=1, commit_total_bytes=24 * GIB,
                                              commit_limit_bytes=48 * GIB, available_commit_bytes=24 * GIB,
                                              guest_memory_bytes=8 * GIB, required_commit_bytes=10 * GIB,
                                              reserve_bytes=2 * GIB))
        self.storage = dict(max_guests=2, budget_bytes=64 * GIB, reservation_bytes=40 * GIB,
                            active_count=1, charged_bytes=20 * GIB, projected_bytes=60 * GIB,
                            root_limit_exceeded=False, byte_limit_exceeded=False, would_fit=True,
                            admission_granted=False)
        resources = dict(self.host, auth_key=PRIVATE,
                         free_bytes=dict(self.host["free_bytes"], **{"E:": PRIVATE}),
                         commit_capacity=dict(self.host["commit_capacity"], source=PRIVATE))
        self.facts = dict(resources=resources, storage=dict(self.storage, root=str(handoff.GUEST), ledger=self.ledger_pin, proof=PRIVATE),
                          ports_free=True)
        self.preflight = Mock(side_effect=self.check_pending)
        self.writes = Mock(side_effect=AssertionError("readiness attempted a write"))

    def check_pending(self, ledger_pin, plan, prepare):
        self.graph.check_binding(ledger_pin)
        return self.facts

    @contextmanager
    def inert(self):
        with self.graph.ports(), ExitStack() as stack:
            for module, name, options in (
                (preparation, "preflight_pending", {"new": self.preflight}),
                (env, "safe_path", {"side_effect": lambda path, **kwargs: path}),
                (env, "create_json", {"new": self.writes}),
                (env, "prepare", {"new": self.writes}),
                (env, "ports_free", {"new": self.writes}),
                (preparation.process, "_exclusive_preflight", {"new": self.writes}),
                (preparation.storage, "reserve_prepare", {"new": self.writes}),
                (Path, "mkdir", {"new": self.writes}),
            ):
                stack.enter_context(patch.object(module, name, **options))
            yield

    def inspect(self, plan_pin=None, ledger_pin=None):
        with self.inert():
            return readiness.inspect(self.plan_pin if plan_pin is None else plan_pin,
                                     self.ledger_pin if ledger_pin is None else ledger_pin)

    def argv(self, plan_sha=None, ledger_sha=None):
        return ["--plan-sha256", self.plan_pin["sha256"] if plan_sha is None else plan_sha,
                "--ledger-sha256", self.ledger_pin["sha256"] if ledger_sha is None else ledger_sha]

    def invoke(self, args=None):
        stdout = StringIO()
        with self.inert(), redirect_stdout(stdout):
            code = readiness.main(self.argv() if args is None else args)
        return code, json.loads(stdout.getvalue())


class CombinedRecordUiReadinessTests(unittest.TestCase):
    def assert_refusal(self, code, report, reason):
        self.assertEqual(code, 1)
        self.assertEqual(report, dict(version=1, scope=readiness.SCOPE, status="refused",
                                      readiness_only=True, execution_authorized=False, reason=reason))

    def test_success_shares_exact_preflight_and_returns_only_aggregates(self):
        records = ReadinessRecords()
        result = records.inspect()
        self.assertEqual(result, dict(version=1, scope=readiness.SCOPE, status="ready",
                                      readiness_only=True, execution_authorized=False,
                                      plan=records.plan_pin, ledger=records.ledger_pin, host=records.host,
                                      storage=records.storage, ports_free=True))
        records.preflight.assert_called_once_with(records.ledger_pin, records.plan, records.graph.prepare)
        self.assertNotIn(PRIVATE, json.dumps(result))
        records.writes.assert_not_called()

    def test_existing_authority_attempt_or_guest_refuses_before_preflight(self):
        for path in (handoff.AUTHORITY, handoff.ATTEMPT_ROOT, handoff.GUEST):
            with self.subTest(path=path):
                records = ReadinessRecords()
                records.graph.present.add(path)
                self.assert_refusal(*records.invoke(), "already_used")
                records.preflight.assert_not_called()
                records.writes.assert_not_called()

    def test_wrong_plan_path_or_digest_refuses_before_preflight(self):
        for change in (dict(path=str(handoff.PREPARE)), dict(sha256="0" * 64)):
            with self.subTest(change=change):
                records = ReadinessRecords()
                with self.assertRaises(REFUSED):
                    records.inspect(plan_pin=dict(records.plan_pin, **change))
                records.preflight.assert_not_called()
                records.writes.assert_not_called()

    def test_plan_semantics_refuse_authority_even_with_matching_digest(self):
        for change in (dict(execution_authorized=True), dict(model_material=True), dict(scope="other")):
            with self.subTest(change=change):
                records = ReadinessRecords()
                rebound = records.graph.add("plan", handoff.PLAN, dict(records.plan, **change))
                with self.assertRaises(REFUSED):
                    records.inspect(plan_pin=rebound)
                records.preflight.assert_not_called()
                records.writes.assert_not_called()

    def test_readiness_refuses_a_stale_ledger_or_wrong_ledger_path(self):
        for change in (dict(sha256="0" * 64), dict(path=str(handoff.PLAN))):
            with self.subTest(change=change):
                records = ReadinessRecords()
                with self.assertRaises(REFUSED):
                    records.inspect(ledger_pin=dict(records.ledger_pin, **change))
                records.writes.assert_not_called()

    def test_preview_must_bind_the_fixed_guest_and_exact_ledger(self):
        for change in (dict(root=PRIVATE), dict(ledger={"sha256": "0" * 64})):
            with self.subTest(change=change):
                records = ReadinessRecords()
                records.facts["storage"].update(change)
                with self.assertRaises(REFUSED):
                    records.inspect()
                records.writes.assert_not_called()

    def test_late_plan_prepare_or_ledger_drift_refuses(self):
        for path in (handoff.PLAN, handoff.PREPARE, handoff.LEDGER):
            with self.subTest(path=path):
                records = ReadinessRecords()

                def changed(*args):
                    facts = records.check_pending(*args)
                    _, value = records.graph.read(path)
                    records.graph.add("drift", path, dict(value, changed=True))
                    return facts

                records.preflight.side_effect = changed
                with self.assertRaises(REFUSED):
                    records.inspect()
                records.preflight.assert_called_once()
                records.writes.assert_not_called()

    def test_new_authority_attempt_or_guest_during_preflight_refuses(self):
        for path in (handoff.AUTHORITY, handoff.ATTEMPT_ROOT, handoff.GUEST):
            with self.subTest(path=path):
                records = ReadinessRecords()

                def changed(*args):
                    facts = records.check_pending(*args)
                    records.graph.present.add(path)
                    return facts

                records.preflight.side_effect = changed
                self.assert_refusal(*records.invoke(), "already_used")
                records.preflight.assert_called_once()
                records.writes.assert_not_called()

    def test_cli_uses_the_exact_supplied_plan_and_ledger_digests(self):
        records = ReadinessRecords()
        code, result = records.invoke()
        self.assertEqual(code, 0)
        self.assertEqual((result["plan"], result["ledger"]), (records.plan_pin, records.ledger_pin))
        for change in (dict(plan_sha="0" * 64), dict(ledger_sha="0" * 64)):
            with self.subTest(change=change):
                records = ReadinessRecords()
                self.assert_refusal(*records.invoke(records.argv(**change)), "binding")
                records.preflight.assert_not_called()
                records.writes.assert_not_called()

    def test_cli_refuses_malformed_arguments_before_preflight(self):
        records = ReadinessRecords()
        good = records.argv()
        for args in ([], good[:-1], good[2:] + good[:2], good + ["--extra"],
                     records.argv(plan_sha="A" * 64), records.argv(ledger_sha="0" * 63)):
            with self.subTest(args=args):
                self.assert_refusal(*records.invoke(args), "binding")
                records.preflight.assert_not_called()
                records.writes.assert_not_called()

    def test_malformed_public_facts_cannot_report_ready(self):
        for mutate in (lambda facts: facts.update(ports_free=1),
                       lambda facts: facts["storage"].update(admission_granted=True),
                       lambda facts: facts["resources"].update(logical_cpus=True)):
            with self.subTest(mutate=mutate):
                records = ReadinessRecords()
                mutate(records.facts)
                self.assert_refusal(*records.invoke(), "facts")
                records.writes.assert_not_called()

    def test_cli_unknown_errors_expose_only_a_fixed_reason(self):
        records = ReadinessRecords()
        records.preflight.side_effect = RuntimeError(PRIVATE)
        code, result = records.invoke()
        self.assert_refusal(code, result, "readiness_refused")
        self.assertNotIn(PRIVATE, json.dumps(result))
        records.writes.assert_not_called()

    def test_cli_preserves_safe_capacity_and_port_refusals(self):
        for reason in ("host_commit_capacity", "storage_capacity", "ports_unavailable"):
            with self.subTest(reason=reason):
                records = ReadinessRecords()
                records.preflight.side_effect = env.EnvironmentRefused(reason)
                self.assert_refusal(*records.invoke(), reason)
                records.writes.assert_not_called()


if __name__ == "__main__":
    unittest.main()
