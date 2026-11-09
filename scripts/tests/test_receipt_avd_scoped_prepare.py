"""Synthetic tests for scoped preparation and the outer watchdog.

Copyright 2026 LocalLore contributors. SPDX-License-Identifier: Apache-2.0
"""
from contextlib import ExitStack
import io
from pathlib import Path
import sys
import tempfile
import unittest
from unittest import mock

from benchmarks import receipt_avd_environment as env
from benchmarks import receipt_avd_storage as storage


class ScopedPrepareTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory(prefix="locallore-scoped-prepare-", dir="D:/Dev/_Temp")
        self.addCleanup(temporary.cleanup)
        self.base = Path(temporary.name).resolve()
        self.root = self.base / "guest"
        self.registry = self.base / "ledger"
        self.ledger = self.registry / "ledger-v1.json"
        self.proposal = self.base / "proposal.json"
        self.authorization = self.base / "authorization.json"
        self.scope = "sdk20-prepare-and-one-cold-navigation-run-v1"
        self.parent = dict(pid=741, creation_filetime=121, executable=sys.executable)
        self.value = dict(paths=env.paths(self.root))
        self.digest = env.create_json(self.proposal, self.value)
        self.grant = dict(version=1, phase="prepare", proposal_sha256=self.digest, allow_environment_calls=True,
                          root_go_pending=False, prepare_scope=self.scope)
        env.create_json(self.authorization, self.grant)

    def seed_ledger(self, version=2):
        self.registry.mkdir(exist_ok=True)
        self.ledger.write_bytes(storage.encoded(dict(
            version=version, max_guests=storage.MAX_GUESTS, budget_bytes=storage.BUDGET_BYTES,
            reservation_bytes=storage.RESERVATION_BYTES, entries=[],
        )))
        return storage.binding(self.ledger)

    def platform(self):
        stack = ExitStack()
        for name in ("validate_proposal", "verify_installation", "check_external_state"):
            stack.enter_context(mock.patch.object(env, name))
        stack.enter_context(mock.patch.object(env, "resource_facts", return_value={}))
        return stack

    def test_same_size_changed_ledger_is_refused_under_the_lock_without_a_charge(self):
        approved = self.seed_ledger()
        current = self.seed_ledger(version=1)
        self.assertEqual(current["bytes"], approved["bytes"])
        self.assertNotEqual(current["sha256"], approved["sha256"])
        read = storage.read_json

        def locked_read(path, *, expected):
            self.assertTrue((self.registry / "admission.lock").is_file())
            self.assertEqual(expected, approved)
            return read(path, expected=expected)

        with mock.patch.object(storage, "read_json", side_effect=locked_read) as checked:
            with self.assertRaisesRegex(storage.StorageRefused, "^ledger_changed$"):
                storage.reserve_prepare(self.root, self.digest, self.registry, expected_ledger=approved)
        checked.assert_called_once_with(self.ledger, expected=approved)
        self.assertEqual(storage.binding(self.ledger), current)
        self.assertFalse(self.root.exists())
        self.assertFalse((self.registry / "admission.lock").exists())

    def test_expected_ledger_cannot_initialize_a_missing_registry(self):
        missing = dict(path=str(self.ledger), bytes=10, sha256="0" * 64)
        with self.assertRaisesRegex(storage.StorageRefused, "^missing_path$"):
            storage.reserve_prepare(self.root, self.digest, self.registry, expected_ledger=missing)
        self.assertFalse(self.registry.exists())
        self.assertFalse(self.root.exists())

    def test_unscoped_prepare_refuses_the_scoped_grant_without_reserving(self):
        with self.platform(), mock.patch.object(storage, "reserve_prepare") as reserve:
            with self.assertRaisesRegex(env.EnvironmentRefused, "^not_authorized$"):
                env.prepare(self.proposal, self.authorization)
        reserve.assert_not_called()
        self.assertFalse(self.root.exists())

    def test_changed_proposal_refuses_before_shared_reservation(self):
        approved = self.seed_ledger()
        self.proposal.write_bytes(env.encoded(dict(self.value, changed=True)))
        with self.platform(), mock.patch.object(storage, "reserve_prepare") as reserve:
            with self.assertRaisesRegex(env.EnvironmentRefused, "^proposal_changed$"):
                env.prepare(self.proposal, self.authorization, expected_ledger=approved,
                            expected_proposal_sha256=self.digest, prepare_scope=self.scope)
        reserve.assert_not_called()
        self.assertFalse(self.root.exists())
        self.assertEqual(storage.binding(self.ledger), approved)

    def test_all_three_scoped_prepare_inputs_are_required(self):
        approved = self.seed_ledger()
        for absent in ("expected_ledger", "expected_proposal_sha256", "prepare_scope"):
            options = dict(expected_ledger=approved, expected_proposal_sha256=self.digest,
                           prepare_scope=self.scope)
            options.pop(absent)
            with self.subTest(absent=absent), mock.patch.object(env, "authorize") as authorize:
                with self.assertRaisesRegex(env.EnvironmentRefused, "^not_authorized$"):
                    env.prepare(self.proposal, self.authorization, **options)
                authorize.assert_not_called()
        self.assertFalse(self.root.exists())

    def test_scoped_prepare_passes_exact_pin_and_retains_charged_failure(self):
        approved = self.seed_ledger()
        reserve = storage.reserve_prepare

        def local_reserve(root, digest, *, expected_ledger):
            self.assertFalse(root.exists())
            self.assertEqual(expected_ledger, approved)
            return reserve(root, digest, self.registry, expected_ledger=expected_ledger)

        sdk = env.host.ProcessResult("completed", 5, b"synthetic failed SDK", 2, 1, True)
        with self.platform(), mock.patch.object(storage, "reserve_prepare", side_effect=local_reserve) as charged, \
             mock.patch.object(env, "process_identity", return_value=self.parent), \
             mock.patch.object(env.host, "run_process", return_value=sdk) as child:
            with self.assertRaisesRegex(env.EnvironmentRefused, "^prepare_failed$"):
                env.prepare(self.proposal, self.authorization, expected_ledger=approved,
                            expected_proposal_sha256=self.digest, prepare_scope=self.scope)
        charged.assert_called_once_with(self.root, self.digest, expected_ledger=approved)
        self.assertEqual(env.decode_json(child.call_args.kwargs["request"]), dict(
            proposal=str(self.proposal), proposal_sha256=self.digest, authorization=str(self.authorization),
            prepare_scope=self.scope,
        ))
        self.assertEqual(env.read_json(self.root / "prepare-start-v1.json"), dict(
            proposal_sha256=self.digest, facts={}, owner=self.parent, prepare_scope=self.scope,
        ))
        entry = storage.read_json(self.ledger)["entries"][0]
        self.assertEqual((entry["state"], entry["proposal_sha256"], entry["reserved_bytes"]),
                         ("preparing", self.digest, storage.RESERVATION_BYTES))
        self.assertEqual(env.read_json(self.root / "prepare-result-v1.json")["status"], "refused")
        self.assertEqual((self.root / "prepare-stdout-v1.bin").read_bytes(), sdk.stdout)

    def test_scoped_worker_rejects_wrong_parent_scope_and_legacy_request(self):
        self.root.mkdir()
        env.create_json(self.root / "prepare-start-v1.json", dict(
            proposal_sha256=self.digest, facts={}, owner=self.parent, prepare_scope=self.scope,
        ))
        legacy = self.base / "legacy-auth.json"
        env.create_json(legacy, {key: value for key, value in self.grant.items() if key != "prepare_scope"})
        base = dict(proposal=str(self.proposal), proposal_sha256=self.digest, authorization=str(self.authorization))
        attempts = [
            (base, self.parent["pid"], "not_authorized"),
            (dict(base, authorization=str(legacy)), self.parent["pid"], "not_authorized"),
            (dict(base, prepare_scope="another-operation"), self.parent["pid"], "not_authorized"),
            (dict(base, prepare_scope=self.scope), self.parent["pid"] + 1, "owner_lost"),
        ]
        for request, ppid, reason in attempts:
            with self.subTest(request=request, ppid=ppid), self.platform(), \
                 mock.patch.object(env.sys, "stdin", mock.Mock(buffer=io.BytesIO(env.encoded(request)))), \
                 mock.patch.object(env.os, "getppid", return_value=ppid), \
                 mock.patch.object(env.subprocess, "run") as launch:
                with self.assertRaisesRegex(env.EnvironmentRefused, "^" + reason + "$"):
                    env.worker("_prepare-worker")
            launch.assert_not_called()
        self.assertFalse((self.root / "prepare-worker-claimed-v1.json").exists())

    def test_scoped_worker_dispatches_only_with_live_direct_parent_and_one_claim(self):
        self.root.mkdir()
        env.create_json(self.root / "prepare-start-v1.json", dict(
            proposal_sha256=self.digest, facts={}, owner=self.parent, prepare_scope=self.scope,
        ))
        worker = dict(self.parent, pid=742, creation_filetime=122)
        request = env.encoded(dict(proposal=str(self.proposal), proposal_sha256=self.digest,
                                   authorization=str(self.authorization), prepare_scope=self.scope))
        with self.platform(), mock.patch.object(env.os, "getppid", return_value=self.parent["pid"]), \
             mock.patch.object(env.os, "getpid", return_value=worker["pid"]), \
             mock.patch.object(env, "process_identity", side_effect=lambda pid: self.parent if pid == 741 else worker), \
             mock.patch.object(env, "prepare_command", return_value=["synthetic-sdk"]), \
             mock.patch.object(env, "scoped_env", return_value={}), \
             mock.patch.object(env.subprocess, "run", return_value=mock.Mock(returncode=0)) as launch:
            for repeat in (False, True):
                with mock.patch.object(env.sys, "stdin", mock.Mock(buffer=io.BytesIO(request))):
                    if repeat:
                        with self.assertRaises(FileExistsError):
                            env.worker("_prepare-worker")
                    else:
                        self.assertEqual(env.worker("_prepare-worker"), 0)
        launch.assert_called_once_with(["synthetic-sdk"], input=b"no\n", env={})
        self.assertEqual(env.read_json(self.root / "prepare-worker-claimed-v1.json"), dict(
            proposal_sha256=self.digest, worker=worker, prepare_scope=self.scope,
        ))

    def test_operation_watchdog_has_separate_ceiling_and_preserves_runtime_limit(self):
        command = ["synthetic-child"]
        callback = lambda child: True
        self.root.mkdir()
        with mock.patch.object(env.subprocess, "Popen") as child:
            for supervise, budget in ((env.supervise, 1801), (env.supervise_operation, 2401),
                                      (env.supervise_operation, 0), (env.supervise_operation, True)):
                with self.subTest(supervise=supervise.__name__, budget=budget):
                    with self.assertRaisesRegex(env.EnvironmentRefused, "^invalid_budget$"):
                        supervise(command, b"barrier", self.root, budget, callback)
            child.assert_not_called()
        self.assertFalse(list(self.root.iterdir()))
        with mock.patch.object(env.subprocess, "Popen", side_effect=OSError("synthetic refusal")) as child:
            result = env.supervise_operation(command, b"barrier", self.root, 2400, callback)
        child.assert_called_once()
        self.assertFalse(result["cleanup_complete"])
        self.assertEqual({path.name for path in self.root.iterdir()}, set(env.LiveOutput.names))


if __name__ == "__main__":
    unittest.main()
