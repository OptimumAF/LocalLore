"""Synthetic tests of cold-navigation client admission and replay ordering.

Copyright 2026 LocalLore contributors. SPDX-License-Identifier: Apache-2.0
"""
import copy
import os
from pathlib import Path
import shlex
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import Mock, call, patch

from benchmarks import android_instrumentation_evidence as evidence
from benchmarks import owned_cold_navigation_ui_client as client
from benchmarks import owned_cold_navigation_ui_contract as contract
from benchmarks import owned_target_contract as core
from scripts.tests import test_android_process_client_v4 as framing
from scripts.tests import test_owned_cold_navigation_ui_contract as fixture
from scripts.tests import test_owned_target_contract as owned


class ColdNavigationClientTests(unittest.TestCase):
    def test_exact_artifacts_are_checked_before_the_base_observer_opens(self):
        bindings = {"path": "D:/Synthetic/admission-v1.json"}, {"path": "D:/Synthetic/running-v1.json"}
        admitted = fixture.admission()
        events = Mock()
        with patch.object(client.mechanisms, "_read_json", return_value=admitted), \
                patch.object(contract, "verify_artifacts", events.verify), \
                patch.object(client.mechanisms._LiveOwnedTarget, "__init__", events.open):
            events.open.return_value = None
            client.LiveOwnedColdNavigationUiTarget(*bindings)
            self.assertEqual(events.mock_calls, [call.verify(admitted["artifacts"]), call.open(*bindings)])
            events.reset_mock()
            events.verify.side_effect = core.TargetRefused("binding")
            with self.assertRaises((core.TargetRefused, client.mechanisms.OwnerRefused)):
                client.LiveOwnedColdNavigationUiTarget(*bindings)
            events.open.assert_not_called()

    def test_bad_admission_does_not_reach_artifact_reads_or_base_observer(self):
        with patch.object(client.mechanisms, "_read_json", return_value={}), \
                patch.object(contract, "verify_artifacts") as verify, \
                patch.object(client.mechanisms._LiveOwnedTarget, "__init__") as open_observer:
            with self.assertRaises((core.TargetRefused, client.mechanisms.OwnerRefused)):
                client.LiveOwnedColdNavigationUiTarget({}, {})
            verify.assert_not_called()
            open_observer.assert_not_called()

    def test_legacy_and_subclass_leases_are_refused_before_any_socket(self):
        class Derived(client.LiveOwnedColdNavigationUiTarget):
            pass

        with patch.object(client.wire.socket, "socket") as connect:
            for lease_type in (client.mechanisms.LiveOwnedTarget, Derived):
                lease = object.__new__(lease_type)
                lease.guard = Mock()
                with self.subTest(lease=lease_type.__name__):
                    with self.assertRaises(client.wire.ClientRefused):
                        client.OwnedColdNavigationUiSdkCapture(Path("D:/Synthetic/clients"), 120, lease)
                    lease.guard.assert_not_called()
            connect.assert_not_called()

    def capture(self):
        capture = object.__new__(client.OwnedColdNavigationUiSdkCapture)
        capture.directory = Path("D:/Synthetic/clients")
        capture.count = 3
        capture._session = {"session": "synthetic"}
        capture._admission = fixture.admission()
        capture.clean = True
        capture._failed = False
        capture.shell = Mock(return_value=fixture.pass_capture())
        return capture

    def test_run_captures_the_fixed_command_and_replays_the_newest_record(self):
        capture = self.capture()
        pin = {"path": str(capture.directory / "command-0003.json")}
        result = {"passed": True, "method_count": 1}
        verifier = SimpleNamespace(_pin=Mock(return_value=pin))
        with patch.object(client, "_REPLAY", verifier), \
                patch.object(client, "replay_client_record", return_value=result) as replay:
            self.assertEqual(capture.run_cold_navigation(), {"client": pin, "instrumentation": result})
        capture.shell.assert_called_once_with(contract.instrumentation_argv(), "cold_navigation",
                                               seconds=120, cap=evidence.MAX_BYTES, full_budget=True)
        verifier._pin.assert_called_once_with(capture.directory / "command-0003.json")
        replay.assert_called_once_with(pin, capture.session, capture._admission,
                                       expected_stdout=capture.shell.return_value)

    def test_run_poisoned_on_replay_refusal(self):
        capture = self.capture()
        verifier = SimpleNamespace(_pin=Mock(return_value={"path": "synthetic"}))
        with patch.object(client, "_REPLAY", verifier), \
                patch.object(client, "replay_client_record", side_effect=core.TargetRefused("capability")):
            with self.assertRaises(client.wire.ClientRefused):
                capture.run_cold_navigation()
        self.assertFalse(capture.clean)
        self.assertTrue(capture._failed)
        capture.shell.assert_called_once()

    def test_verified_record_is_required_before_replaying_bounded_bytes(self):
        pin, session, admitted = {"path": "synthetic"}, {}, fixture.admission()
        stdout, stderr = {"path": "stdout"}, {"path": "stderr"}
        raw = fixture.pass_capture()
        row = dict(operation={"argv": contract.instrumentation_argv(), "stdin": None},
                   returncode=0, label="cold_navigation", stdout=stdout, stderr=stderr)
        verifier = Mock()
        verifier.verify_client_record.return_value = row
        verifier._raw.side_effect = lambda source, **_: raw if source == stdout else b""
        with patch.object(client, "_REPLAY", verifier):
            result = client.replay_client_record(pin, session, admitted, expected_stdout=raw)
            self.assertEqual((result["class"], result["methods"]), (contract.CLASS, [contract.METHOD]))
            self.assertTrue(result["passed"])
            self.assertEqual(verifier.mock_calls[0], call.verify_client_record(pin, session, admitted))
            self.assertEqual(verifier._raw.call_args_list,
                             [call(stdout, cap=evidence.MAX_BYTES), call(stderr, cap=evidence.MAX_BYTES)])
            verifier.reset_mock()
            with self.assertRaises((core.TargetRefused, client.wire.ClientRefused)):
                client.replay_client_record(pin, session, admitted, expected_stdout=raw + b"changed")
            verifier.reset_mock()
            row["label"] = "foreign"
            with self.assertRaises((core.TargetRefused, client.wire.ClientRefused)):
                client.replay_client_record(pin, session, admitted)
            verifier._raw.assert_not_called()
            verifier.verify_client_record.side_effect = core.TargetRefused("capability")
            with self.assertRaises((core.TargetRefused, client.wire.ClientRefused)):
                client.replay_client_record(pin, session, admitted)
            verifier._raw.assert_not_called()

    @unittest.skipUnless(os.name == "nt", "Windows metadata fixtures, all socket and native I/O mocked")
    def test_v4_capture_binds_exact_wire_claim_and_refuses_repeat_before_dispatch(self):
        env = client.wire.environment
        root = Path(tempfile.mkdtemp(prefix="locallore-cold-client-"))
        admitted = fixture.admission()
        admitted.update(root=str(root / "lease"))
        admitted["server"]["root"] = str(root / "lease/server")
        admission_path = root / "admission-v1.json"
        env.create_json(admission_path, admitted)
        admission_pin = env.binding(admission_path)
        running = owned.running(admitted)
        running.update(protocol=contract.PROTOCOL, admission=admission_pin)
        running_path = root / "lease/running-v1.json"
        running_path.parent.mkdir()
        env.create_json(running_path, running)
        lease = object.__new__(client.LiveOwnedColdNavigationUiTarget)
        lease._admission, lease._descriptor = admitted, running
        lease._admission_binding, lease._running_binding = admission_pin, env.binding(running_path)
        lease._caller = running["worker"]
        lease.guard, lease.fast_guard = Mock(), Mock()

        def prove(path, session, context, sock, anchor, after=False):
            queries = owned.query_bundle(session)
            queries["protocol"] = contract.PROOF_PROTOCOL
            query_path = path.with_name(path.stem + "-queries-v1.json")
            env.create_json(query_path, queries)
            proof = owned.proof(session, after=after)
            proof.update(protocol=contract.PROOF_PROTOCOL, context=copy.deepcopy(context),
                         anchor=copy.deepcopy(anchor), queries=env.binding(query_path),
                         session=env.binding(Path(session["root"]) / contract.SESSION_FILE))
            env.create_json(path, proof)
            return env.binding(path)

        lease.prove = prove
        response = b"OKAYOKAY" + framing.packet(1, fixture.pass_capture()) + framing.packet(3, b"\0")
        initial, repeat = (framing.FakeSocket(response) for _ in range(2))
        with patch.object(client.wire.time, "monotonic", return_value=100.0), \
                patch.object(client.wire.time, "time", return_value=1800000010.0), \
                patch.object(client.wire.threading, "Thread", framing.InlineSender), \
                patch.object(client.wire.socket, "socket", side_effect=[initial, repeat]):
            first, second = (root / name for name in ("first", "second"))
            first.mkdir()
            second.mkdir()
            capture = client.OwnedColdNavigationUiSdkCapture(first / "clients", 180, lease)
            result = capture.run_cold_navigation()
            self.assertEqual(result["instrumentation"]["methods"], [contract.METHOD])
            self.assertEqual(capture.count, 1)
            self.assertIn(shlex.join(contract.instrumentation_argv()).encode(), initial.sent)
            claim = env.read_json(running_path.parent / "claims-v1/cold_navigation-v1.json")
            operation = {"argv": contract.instrumentation_argv(), "stdin": None}
            self.assertEqual(claim["operation_sha256"], contract.operation_digest(operation))
            self.assertTrue(initial.closed)

            again = client.OwnedColdNavigationUiSdkCapture(second / "clients", 180, lease)
            with self.assertRaises(client.wire.ClientRefused):
                again.run_cold_navigation()
            self.assertEqual(again.count, 0)
            self.assertEqual(repeat.sent, b"")
            self.assertTrue(repeat.closed)
            self.assertFalse(again.clean)
