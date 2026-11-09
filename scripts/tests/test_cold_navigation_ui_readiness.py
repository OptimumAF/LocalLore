"""Synthetic read-only cold-navigation readiness checks."""

from contextlib import ExitStack, contextmanager, redirect_stdout
from io import StringIO
import json
from pathlib import Path
import unittest
from unittest.mock import Mock, patch

from benchmarks import cold_navigation_ui_readiness as readiness
from scripts.tests.test_cold_navigation_ui_preparation import Ports
from scripts.tests.test_owned_cold_navigation_ui_owner import BootRecords, REFUSED


owner = readiness.owner
preparation = readiness.preparation
env = owner.env
GIB = 1024 ** 3
PRIVATE = "synthetic-private-proof"


class ReadinessRecords:
    """Use the real binding and plan decoders with inert filesystem ports."""

    def __init__(self):
        self.graph = BootRecords()
        self.plan_pin, self.plan = self.graph.read(owner.PLAN)
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
        self.facts = dict(resources=resources, storage=dict(self.storage, root=PRIVATE, ledger=self.ledger_pin),
                          ports_free=True)
        self.preflight = Mock(side_effect=self.check_pending)
        self.writes = Mock(side_effect=AssertionError("readiness attempted a write"))

    def check_pending(self, ledger_pin, plan, prepare):
        self.graph.check_pin(ledger_pin)
        return self.facts

    @contextmanager
    def inert(self):
        with self.graph.ports(), ExitStack() as stack:
            for module, name, options in (
                (preparation, "preflight_pending", {"new": self.preflight}),
                (env, "safe_path", {"side_effect": lambda path, **kwargs: path}),
                (env, "create_json", {"new": self.writes}),
                (env, "prepare", {"new": self.writes}),
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


class ColdNavigationReadinessTests(unittest.TestCase):
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

    def test_existing_authority_or_attempt_refuses_before_preflight(self):
        for path in (owner.AUTHORITY, owner.ATTEMPT_ROOT):
            with self.subTest(path=path):
                records = ReadinessRecords()
                records.graph.present.add(path)
                self.assert_refusal(*records.invoke(), "already_used")
                records.preflight.assert_not_called()
                records.writes.assert_not_called()

    def test_wrong_plan_path_or_digest_refuses_before_preflight(self):
        for change in (dict(path=str(owner.PREPARE)), dict(sha256="0" * 64)):
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
                rebound = records.graph.add("plan", owner.PLAN, dict(records.plan, **change))
                with self.assertRaises(REFUSED):
                    records.inspect(plan_pin=rebound)
                records.preflight.assert_not_called()
                records.writes.assert_not_called()

    def test_readiness_refuses_a_stale_ledger(self):
        records = ReadinessRecords()
        with self.assertRaises(REFUSED):
            records.inspect(ledger_pin=dict(records.ledger_pin, sha256="0" * 64))
        records.writes.assert_not_called()

    def test_changed_plan_or_ledger_during_preflight_refuses(self):
        for path in (owner.PLAN, owner.LEDGER):
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

    def test_new_authority_or_attempt_during_preflight_refuses(self):
        for path in (owner.AUTHORITY, owner.ATTEMPT_ROOT):
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

    def test_pending_preflight_reuses_the_execution_checks_with_no_attempt(self):
        ports = Ports()
        with ports.inert():
            result = preparation.preflight_pending(ports.authority["ledger"], ports.plan, ports.prepare)
        self.assertEqual(result, dict(resources=ports.resources.return_value, storage=ports.preview,
                                      ports_free=True))
        ports.resources.assert_called_once_with(ports.prepare)
        ports.ports.assert_called_once_with()
        ports.private.assert_called_once_with(ports.native.return_value, port=preparation.contract.PORT)
        self.assertEqual(ports.files, set())
        ports.save.assert_not_called()

    def test_pending_preflight_rechecks_freshness_after_the_shared_probe(self):
        ports = Ports()

        def used(*args, **kwargs):
            ports.files.add(owner.ATTEMPT_ROOT)
            return dict(exclusive_bind_succeeded=True, created_mask=1, close_attempted_mask=1, closed_mask=1)

        ports.private.side_effect = used
        with ports.inert(), self.assertRaisesRegex(REFUSED, "already_used"):
            preparation.preflight_pending(ports.authority["ledger"], ports.plan, ports.prepare)
        ports.private.assert_called_once()
        ports.save.assert_not_called()

    def test_pending_preflight_refuses_source_drift_during_installation_check(self):
        ports = Ports()
        with ports.inert():
            source_bindings = preparation.contract.source_bindings

            def replace_source(prepare):
                source_bindings.assert_called_once_with()
                source_bindings.return_value = []

            env.verify_installation.side_effect = replace_source
            with self.assertRaisesRegex(REFUSED, "source"):
                preparation.preflight_pending(ports.authority["ledger"], ports.plan, ports.prepare)
            self.assertEqual(source_bindings.call_count, 2)
        ports.save.assert_not_called()


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


if __name__ == "__main__":
    unittest.main()
