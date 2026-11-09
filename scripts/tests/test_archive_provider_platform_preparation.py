"""Exercise the SDK26 preparation guard with synthetic records and no SDK calls.

Copyright 2026 LocalLore contributors. SPDX-License-Identifier: Apache-2.0
"""
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import patch

from benchmarks import archive_provider_platform_preparation as prep


class ArchiveProviderPreparationTests(unittest.TestCase):
    def setUp(self):
        self.root = Path(self.enterContext(TemporaryDirectory())).resolve()
        paths = {
            "GUEST": "avd-v1",
            "PLAN": "preparation-plan-v1.json",
            "PREPARE": "prepare-proposal-v1.json",
            "PROPOSED_PREPARATION": "PROPOSED_PREPARATION.md",
            "AUTHORITY": "human-authority-v1.json",
            "CLAIM": "claim-v1.json",
            "PREPARE_AUTH": "prepare-authorization-v1.json",
            "RESULT": "preparation-result-v1.json",
            "LEDGER": "ledger-v1.json",
        }
        for name, leaf in paths.items():
            self.enterContext(patch.object(prep, name, self.root / leaf))
        self.sdk = self.root / "sdk"
        self.java = self.root / "java"
        self.ledger = self.save(prep.LEDGER, {"version": 2})
        self.preview = dict(root=str(prep.GUEST), ledger=self.ledger, would_fit=True,
                            admission_granted=False)
        self.sources = [self.save(self.root / "source.json", {"source": "synthetic"})]
        self.python = dict(executable=self.save(self.root / "python.exe", {"synthetic": True}),
                           runtime_dll=None)
        self.artifact_pins = {
            role: self.save(self.root / (role + ".pin"), {"synthetic": role})
            for role in ("build", "product_apk", "test_apk")
        }
        self.proposal = dict(version=1, phase="prepare", paths={"root": str(prep.GUEST)},
                             sdk=str(self.sdk), java_home=str(self.java), memory_mib=8192, cores=4,
                             host_free_min={"D:": 40 * 1024**3},
                             allow_environment_calls=False, root_go_pending=True)
        self.enterContext(patch.object(prep.owned, "source_bindings", return_value=self.sources))
        self.enterContext(patch.object(prep.python_probe, "_python_bindings", return_value=self.python))
        self.enterContext(patch.object(prep.artifacts, "artifact_bindings", return_value=self.artifact_pins))
        self.verify_artifacts = self.enterContext(patch.object(prep.artifacts, "verify_artifacts"))
        self.preview_prepare = self.enterContext(
            patch.object(prep.storage, "preview_prepare", return_value=self.preview)
        )
        self.plan_prepare = self.enterContext(
            patch.object(prep.env, "plan_prepare", side_effect=self.write_prepare_proposal)
        )
        self.sdk_prepare = self.enterContext(patch.object(prep.env, "prepare"))
        self.enterContext(patch.object(prep.env, "validate_proposal"))
        self.enterContext(patch.object(prep.env, "verify_installation"))
        self.enterContext(patch.object(prep.env, "check_external_state"))
        self.resource_facts = self.enterContext(patch.object(
            prep.env, "resource_facts", return_value={"free_bytes": {"D:": 50 * 1024**3}},
        ))
        self.enterContext(patch.object(prep.env, "ports_free"))
        self.plan_pin = prep.build_plan(self.sdk, self.java)
        self.prepare_pin = prep.env.binding(prep.PREPARE)

    @staticmethod
    def save(path, data):
        prep.env.create_json(path, data)
        return prep.env.binding(path)

    def write_prepare_proposal(self, root, sdk, java_home, output, **options):
        self.assertEqual((root, sdk, java_home, output), (prep.GUEST, self.sdk, self.java, prep.PREPARE))
        self.assertEqual(options, {"real_candidate": True, "four_core_candidate": True})
        self.save(output, self.proposal)
        return self.proposal

    def approve(self, **overrides):
        text = f"Plan SHA-256 {self.plan_pin['sha256']}\nLedger SHA-256 {self.ledger['sha256']}\n"
        prep.PROPOSED_PREPARATION.write_text(text, encoding="utf-8", newline="\n")
        authority = dict(version=1, scope=prep.PREPARE_SCOPE,
                         proposal=prep.env.binding(prep.PROPOSED_PREPARATION),
                         plan=self.plan_pin, ledger=self.ledger,
                         approval_reference="synthetic approval", allow_sdk_prepare=True,
                         allow_one_boot=False, allow_model=False, allow_retirement=False)
        return self.save(prep.AUTHORITY, dict(authority, **overrides))

    def assert_not_dispatched(self):
        self.assertFalse(prep.GUEST.exists())
        self.assertFalse(prep.CLAIM.exists())
        self.assertFalse(prep.PREPARE_AUTH.exists())
        self.assertFalse(prep.RESULT.exists())
        self.sdk_prepare.assert_not_called()

    def test_plan_pins_exact_proposal_source_python_and_apks(self):
        plan, proposal = prep.load_plan(self.plan_pin)
        self.assertEqual(plan, dict(version=1, scope=prep.PLAN_SCOPE, prepare=self.prepare_pin,
                                    sources=self.sources, python=self.python, artifacts=self.artifact_pins))
        self.assertEqual(proposal, self.proposal)
        self.plan_prepare.assert_called_once()
        self.verify_artifacts.assert_called_with(self.artifact_pins)
        self.assertFalse(prep.AUTHORITY.exists())
        self.assert_not_dispatched()

    def test_inspection_is_read_only_and_reports_capacity_without_authority(self):
        self.preview["would_fit"] = False
        before = set(self.root.iterdir())
        report = prep.inspect(self.plan_pin, self.ledger)
        self.assertIs(report["execution_authorized"], False)
        self.assertIs(report["storage"]["would_fit"], False)
        self.assertIs(report["storage"]["admission_granted"], False)
        self.assertEqual(set(self.root.iterdir()), before)
        self.assertFalse(prep.AUTHORITY.exists())
        self.assert_not_dispatched()

    def test_ledger_drift_refuses_and_never_writes_a_claim(self):
        authority = self.approve()
        prep.LEDGER.write_bytes(prep.env.encoded({"version": 2, "changed": True}))
        self.preview["ledger"] = prep.env.binding(prep.LEDGER)
        with self.assertRaises((RuntimeError, ValueError)):
            prep.prepare(authority)
        self.assert_not_dispatched()

    def test_source_drift_refuses_before_claim(self):
        authority = self.approve()
        changed = dict(self.sources[0], sha256="f" * 64)
        with (patch.object(prep.owned, "source_bindings", return_value=[changed]),
              self.assertRaises((RuntimeError, ValueError))):
            prep.prepare(authority)
        self.assert_not_dispatched()

    def test_wrong_authority_scope_or_capability_refuses_before_claim(self):
        for overrides in (
            {"scope": "sdk24-prepare-cross-owner-deletion-v1"},
            {"allow_one_boot": True},
            {"allow_model": True},
            {"allow_retirement": True},
            {"allow_sdk_prepare": 1},
            {"approval_reference": ""},
        ):
            with self.subTest(overrides=overrides):
                authority = self.approve(**overrides)
                try:
                    with self.assertRaises((RuntimeError, ValueError)):
                        prep.prepare(authority)
                    self.assert_not_dispatched()
                finally:
                    prep.AUTHORITY.unlink()

    def test_reviewed_proposal_drift_refuses_before_claim(self):
        authority = self.approve()
        prep.PROPOSED_PREPARATION.write_text("changed after approval\n", encoding="utf-8")
        with self.assertRaises((RuntimeError, ValueError)):
            prep.prepare(authority)
        self.assert_not_dispatched()

    def test_capacity_refuses_even_with_a_matching_approval(self):
        authority = self.approve()
        self.preview["would_fit"] = False
        with self.assertRaisesRegex(RuntimeError, "storage_capacity"):
            prep.prepare(authority)
        self.assert_not_dispatched()

    def test_prepare_dispatches_only_the_exact_approved_locked_path_once(self):
        authority = self.approve()
        prepared = self.save(self.root / "synthetic-prepared.json", {"prepared": True})
        result_pin = self.save(self.root / "synthetic-result.json", {"result": "completed"})
        with (patch.object(prep, "_prepared_records", return_value=(prepared, result_pin, {})),
              patch.object(prep, "_prepared_ledger", return_value=self.ledger)):
            result = prep.prepare(authority)
            self.assertEqual(prep.env.read_json(prep.RESULT), result)
            self.assertEqual(result["prepared"], prepared)
            self.assertEqual(result["result"], result_pin)
            self.assertEqual(prep.env.read_json(prep.CLAIM), prep._claim(authority))
            with self.assertRaisesRegex(RuntimeError, "already_used"):
                prep.prepare(authority)
        self.sdk_prepare.assert_called_once_with(
            str(prep.PREPARE), str(prep.PREPARE_AUTH), expected_ledger=self.ledger,
            expected_proposal_sha256=self.prepare_pin["sha256"], prepare_scope=prep.PREPARE_SCOPE,
        )
        self.assertFalse(prep.GUEST.exists())

    def test_sdk_failure_retains_the_claim_and_refuses_a_retry(self):
        authority = self.approve()
        self.sdk_prepare.side_effect = prep.env.EnvironmentRefused("prepare_failed")
        with self.assertRaisesRegex(RuntimeError, "prepare_failed"):
            prep.prepare(authority)
        self.assertTrue(prep.CLAIM.exists())
        self.assertTrue(prep.PREPARE_AUTH.exists())
        self.assertFalse(prep.RESULT.exists())
        with self.assertRaisesRegex(RuntimeError, "already_used"):
            prep.prepare(authority)
        self.assertEqual(self.sdk_prepare.call_count, 1)

    def test_cold_cli_cannot_dispatch_without_the_approval_record(self):
        with patch("builtins.print"):
            self.assertEqual(prep.main([]), 1)
            self.assertEqual(prep.main(["--authority-sha256", "a" * 64]), 1)
        self.assert_not_dispatched()
