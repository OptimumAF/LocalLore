"""SDK19 one-use operation tests with inert preparation and activation ports.

Copyright 2026 LocalLore contributors. SPDX-License-Identifier: Apache-2.0
"""
from contextlib import ExitStack, contextmanager
import copy
import hashlib
from io import BytesIO
from pathlib import Path
import sys
import unittest
from unittest.mock import Mock, patch

from benchmarks import record_large_text_ui_operation as operation


REFUSED = (ValueError, RuntimeError)
ROOT = Path("D:/Dev/Experiments/LocalLore/2026-11-09-record-large-text-operation-v1")
REGISTRY = Path("D:/Dev/_Migration/LocalLore-AVD-Storage")
GUEST = Path("D:/Dev/Experiments/LocalLore/2026-11-09-record-large-text-ui-v1/avd-v1")


def pin(path, payload=b"synthetic only"):
    return dict(path=str(path), bytes=len(payload), sha256=hashlib.sha256(payload).hexdigest())


def authority():
    return dict(version=1, scope=operation.SCOPE, proposal=pin(operation.PROPOSAL),
                plan=pin(operation.PLAN), ledger=pin(REGISTRY / "ledger-v1.json"),
                approval_reference="synthetic-review-reference-128", allow_sdk_prepare=True,
                allow_one_boot=True, allow_model=False, allow_retirement=False,
                max_operation_seconds=2400)


class StagePorts:
    """Track operation dispatch separately from validation and publication."""

    def __init__(self):
        self.approved = authority()
        self.authority_pin = pin(operation.AUTHORITY)
        self.attempt_pin = pin(operation.CLAIM)
        self.prepare_pin = pin(operation.PREPARE)
        self.plan = dict(prepare=self.prepare_pin)
        self.prepare = dict(paths=dict(root=str(GUEST)), memory_mib=8192, cores=4)
        self.admission = pin(operation.activation.ADMISSION)
        self.activation = dict(passed=True, admission=self.admission, feature_acceptance=False)
        self.accepted = (pin(operation.activation.CONTROL / "activation-result-v1.json"),
                         pin(REGISTRY / "ledger-v1.json", b"closed"))
        self.events = []
        self.records = {}
        self.read_authority = self.record("authority", copy.deepcopy(self.approved))
        self.verify_attempt = self.record("attempt")
        self.read_plan = self.record("plan", (self.plan, self.prepare))
        self.preflight = self.record("preflight")
        self.check_sources = self.record("sources")
        self.prepare_guest = self.record("prepare")
        self.create_admission = self.record("admission", self.admission)
        self.activate = self.record("activation", self.activation)
        self.accept_activation = self.record("accept", self.accepted)
        self.check_binding = self.record("binding")
        self.save = Mock(side_effect=self._save)

    def record(self, name, value=None):
        def observe(*args, **kwargs):
            self.events.append(name)
            return value
        return Mock(side_effect=observe)

    def _save(self, path, value):
        self.events.append("save:" + path.name)
        if path in self.records:
            raise AssertionError("operation tried to overwrite evidence")
        self.records[path] = copy.deepcopy(value)
        return pin(path)

    @contextmanager
    def inert(self, *, now=101):
        self.clock = Mock(return_value=now)
        with ExitStack() as stack:
            for obj, name, port in (
                (operation, "_authority", self.read_authority),
                (operation, "_verify_attempt", self.verify_attempt),
                (operation, "_plan", self.read_plan),
                (operation, "_preflight", self.preflight),
                (operation, "_check_sources", self.check_sources),
                (operation.env, "prepare", self.prepare_guest),
                (operation, "_create_admission", self.create_admission),
                (operation.activation, "execute", self.activate),
                (operation, "_accept_activation", self.accept_activation),
                (operation.env, "check_binding", self.check_binding),
                (operation, "_save", self.save),
                (operation.time, "monotonic", self.clock),
            ):
                stack.enter_context(patch.object(obj, name, port))
            yield

    def run(self, *, now=101):
        with self.inert(now=now):
            return operation._run_stages(self.authority_pin, self.attempt_pin, 100)


class AuthorityTests(unittest.TestCase):
    def test_authority_binds_only_one_sdk19_prepare_boot_without_mutation(self):
        value = authority()
        original = copy.deepcopy(value)
        self.assertEqual(operation.validate_authority(value), value)
        self.assertEqual(value, original)

    def test_authority_refuses_aliases_foreign_paths_and_unknown_fields(self):
        for name, bad in (
            ("version", True), ("scope", "sdk18-fresh-operation-v1"),
            ("approval_reference", ""), ("approval_reference", "line\nforged"),
            ("allow_sdk_prepare", 1), ("allow_one_boot", False),
            ("allow_model", 0), ("allow_retirement", True), ("max_operation_seconds", 2400.0),
            ("max_operation_seconds", 2401), ("proposal", pin(ROOT / "other-proposal.md")),
            ("plan", pin(ROOT / "other-plan.json")), ("ledger", pin(ROOT / "ledger-v1.json")),
            ("run_id", "extra"),
        ):
            value = authority()
            value[name] = bad
            with self.subTest(name=name, bad=bad), self.assertRaises(REFUSED):
                operation.validate_authority(value)

    def test_authority_refuses_noncanonical_binding_metadata(self):
        for key, bad in (("bytes", True), ("bytes", -1), ("sha256", "ab"), ("sha256", "Z" * 64)):
            value = authority()
            value["plan"][key] = bad
            with self.subTest(key=key, bad=bad), self.assertRaises(REFUSED):
                operation.validate_authority(value)

    def test_reviewed_markdown_must_bind_the_exact_plan_and_ledger_once(self):
        original = authority()
        authority_pin = pin(operation.AUTHORITY)
        document = ("# Reviewed operation\n"
                    f"Plan SHA-256 {original['plan']['sha256']}\n"
                    f"Ledger SHA-256 {original['ledger']['sha256']}\n").encode("ascii")
        for mutation in ("none", "plan", "ledger", "duplicate"):
            value = copy.deepcopy(original)
            raw = document
            if mutation in ("plan", "ledger"):
                value[mutation]["sha256"] = "7" * 64
            if mutation == "duplicate":
                raw += f"Plan SHA-256 {original['plan']['sha256']}\n".encode("ascii")
            with self.subTest(mutation=mutation), \
                 patch.object(operation, "_at", side_effect=[value, {}]) as read, \
                 patch.object(operation.files, "_bound", return_value=raw), \
                 patch.object(operation.env, "check_binding") as checked:
                if mutation == "none":
                    self.assertEqual(operation._authority(authority_pin), original)
                    self.assertEqual(read.call_count, 2)
                    checked.assert_called_once_with(authority_pin)
                else:
                    with self.assertRaises(REFUSED):
                        operation._authority(authority_pin)
                    self.assertEqual(read.call_count, 1)
                    checked.assert_not_called()


class StageTests(unittest.TestCase):
    def test_checked_stage_dispatches_prepare_and_activation_once_in_order(self):
        ports = StagePorts()
        result = ports.run()
        self.assertIs(result["passed"], True, result)
        self.assertIs(result["feature_acceptance"], False)
        self.assertEqual((result["phase"], result["step"]), ("completed", "completed"))
        ports.verify_attempt.assert_called()
        ports.preflight.assert_called_once_with(ports.approved, ports.plan, ports.prepare)
        ports.prepare_guest.assert_called_once()
        ports.create_admission.assert_called_once_with(ports.plan)
        ports.activate.assert_called_once_with(ports.admission)
        ports.accept_activation.assert_called_once_with(ports.activation, ports.admission)
        sequence = ("authority", "attempt", "plan", "preflight", "sources",
                    "prepare", "admission", "activation", "accept")
        for first, second in zip(sequence, sequence[1:]):
            self.assertLess(ports.events.index(first), ports.events.index(second))

    def test_invalid_authority_attempt_plan_or_preflight_never_calls_prepare(self):
        for port_name in ("read_authority", "verify_attempt", "read_plan", "preflight",
                          "check_sources", "check_binding"):
            ports = StagePorts()
            getattr(ports, port_name).side_effect = operation.env.EnvironmentRefused("PRIVATE_RECORD")
            with self.subTest(port=port_name):
                result = ports.run()
                self.assertIs(result["passed"], False)
                self.assertNotIn("PRIVATE_RECORD", str(result))
                ports.prepare_guest.assert_not_called()
                ports.create_admission.assert_not_called()
                ports.activate.assert_not_called()

    def test_overall_budget_refuses_before_prepare(self):
        ports = StagePorts()
        result = ports.run(now=2501)
        self.assertIs(result["passed"], False)
        ports.prepare_guest.assert_not_called()
        ports.activate.assert_not_called()

    def test_budget_expiry_during_prepare_prevents_activation_without_retry(self):
        ports = StagePorts()

        def use_remaining_budget(*args, **kwargs):
            ports.clock.return_value = 2501

        ports.prepare_guest.side_effect = use_remaining_budget
        result = ports.run()
        self.assertIs(result["passed"], False)
        ports.prepare_guest.assert_called_once()
        ports.activate.assert_not_called()

    def test_prepare_refusal_and_interruption_never_activate_or_retry(self):
        for error in (operation.env.EnvironmentRefused("PRIVATE_SDK_PATH"), KeyboardInterrupt("PRIVATE_INTERRUPT")):
            ports = StagePorts()
            ports.prepare_guest.side_effect = error
            with self.subTest(error=type(error).__name__):
                result = ports.run()
                self.assertIs(result["passed"], False)
                self.assertNotIn("PRIVATE_", str(result))
                self.assertIs(result["feature_acceptance"], False)
                self.assertEqual((result["phase"], result["step"]), ("prepare", "prepare_dispatch"))
                ports.prepare_guest.assert_called_once()
                ports.create_admission.assert_not_called()
                ports.activate.assert_not_called()

    def test_post_prepare_handoff_or_activation_refusal_is_not_retried(self):
        for port_name, activation_calls in (("create_admission", 0), ("activate", 1), ("accept_activation", 1)):
            ports = StagePorts()
            getattr(ports, port_name).side_effect = operation.env.EnvironmentRefused("PRIVATE_REFUSAL")
            with self.subTest(port=port_name):
                result = ports.run()
                self.assertIs(result["passed"], False)
                self.assertNotIn("PRIVATE_REFUSAL", str(result))
                ports.prepare_guest.assert_called_once()
                self.assertEqual(ports.activate.call_count, activation_calls)

    def test_readiness_failure_retains_exact_trusted_reason_without_dispatch(self):
        for error, reason in (
            (operation.env.EnvironmentRefused("host_commit_capacity"), "host_commit_capacity"),
            (ValueError("host_commit_capacity"), "operation_refused"),
        ):
            ports = StagePorts()
            ports.preflight.side_effect = error
            with self.subTest(error=type(error).__name__):
                result = ports.run()
                self.assertIs(result["passed"], False)
                self.assertEqual((result["phase"], result["step"]), ("preflight", "readiness"))
                self.assertEqual(result["reason"], reason)
                ports.prepare_guest.assert_not_called()
                ports.activate.assert_not_called()

    def test_authority_drift_after_activation_revokes_the_result(self):
        ports = StagePorts()
        ports.read_authority.side_effect = [
            ports.approved, ports.approved, ports.approved,
            operation.env.EnvironmentRefused("PRIVATE_CHANGED_AUTHORITY"),
        ]
        result = ports.run()
        self.assertIs(result["passed"], False)
        self.assertNotIn("PRIVATE_CHANGED_AUTHORITY", str(result))
        self.assertEqual(ports.read_authority.call_count, 4)
        ports.prepare_guest.assert_called_once()
        ports.activate.assert_called_once()


class ParentPorts:
    """Build a closed result graph independently from the operation worker."""

    def __init__(self, mutation=None):
        self.mutation = mutation
        self.authority = authority()
        self.authority_pin = pin(operation.AUTHORITY)
        self.parent = dict(pid=412, creation_filetime=1100, executable=sys.executable)
        self.worker = dict(pid=741, creation_filetime=1700, executable=sys.executable)
        self.values = {}
        self.admission = pin(operation.activation.ADMISSION)
        self.activation = self.save(
            operation.activation.CONTROL / "activation-result-v1.json",
            dict(passed=True, admission=self.admission, feature_acceptance=False),
        )
        self.ledger = pin(REGISTRY / "ledger-v1.json", b"closed")
        self.accept = Mock(return_value=(self.activation, self.ledger))
        self.start = Mock(side_effect=self.supervise)
        self.mkdir = Mock()
        self.checked = Mock(side_effect=self.check)

    def save(self, path, value):
        path = Path(path)
        if path in self.values:
            raise AssertionError("operation overwrote a receipt")
        self.values[path] = copy.deepcopy(value)
        return pin(path, operation.env.encoded(value))

    def read(self, path, *_args):
        path = Path(path)
        value = copy.deepcopy(self.values[path])
        return pin(path, operation.env.encoded(value)), value

    def at(self, expected, path, *_args):
        actual, value = self.read(path)
        if actual != expected:
            raise operation.env.EnvironmentRefused("binding")
        return value

    def check(self, expected):
        if expected == self.authority_pin:
            return
        self.at(expected, expected["path"])

    def capture(self, expected, *, cap):
        if expected not in self.captures.values() or cap < 1:
            raise operation.env.EnvironmentRefused("capture")
        return b""

    def supervise(self, request, begin):
        assert begin == 100
        request_data = self.at(request, operation.LIVE / "worker-request-v1.json")
        for name in ("worker-started-v1.json", "worker-claim-v1.json"):
            worker = dict(self.worker)
            if self.mutation == "other_worker" and name == "worker-claim-v1.json":
                worker["pid"] += 1
            self.save(operation.LIVE / name, dict(request=request, worker=worker))
        self.save(operation.LIVE / "stage-result-v1.json",
                  dict(version=1, scope=operation.SCOPE,
                       authority=self.authority_pin if self.mutation != "other_authority"
                       else pin(operation.AUTHORITY, b"other"),
                       attempt=request_data["attempt"], phase="completed", step="completed",
                       passed=True, admission=self.admission, activation=self.activation,
                       ledger=self.ledger, reason=None, feature_acceptance=False))
        self.captures = {name: pin(operation.LIVE / "worker-capture-v1" /
                                   ("owner-" + name + "-v1.bin"), b"")
                         for name in ("stdout", "stderr")}
        return dict(status="child_exited",
                    worker_returncode=False if self.mutation == "boolean_exit" else 0,
                    cleanup_complete=self.mutation != "unknown_cleanup",
                    capture_complete=self.mutation != "unknown_capture",
                    worker=self.worker, captures=self.captures, elapsed_ms=310)

    @contextmanager
    def inert(self):
        with ExitStack() as stack:
            stack.enter_context(patch.dict(operation.os.environ, {
                key: "D:/Dev/_Temp" for key in ("TEMP", "TMP", "TMPDIR")
            }))
            for obj, name, port in (
                (operation.Path, "cwd", Mock(return_value=operation.ROOT)),
                (operation.Path, "mkdir", self.mkdir),
                (operation, "_authority", Mock(return_value=self.authority)),
                (operation, "_save", self.save),
                (operation, "_read", self.read),
                (operation, "_at", self.at),
                (operation, "_supervise", self.start),
                (operation, "_accept_activation", self.accept),
                (operation.activation, "_identity", Mock(return_value=self.parent)),
                (operation.env, "safe_path", Mock()),
                (operation.env, "check_binding", self.checked),
                (operation.files, "_bound", self.capture),
                (operation.time, "monotonic", Mock(return_value=101)),
            ):
                stack.enter_context(patch.object(obj, name, port))
            yield


class ParentTests(unittest.TestCase):
    def test_create_only_attempt_failure_never_releases_the_supervisor(self):
        ports = ParentPorts()
        ports.mkdir.side_effect = FileExistsError("existing attempt")
        with ports.inert(), self.assertRaises(FileExistsError):
            operation.execute(ports.authority_pin, 100)
        ports.mkdir.assert_called_once()
        ports.start.assert_not_called()
        self.assertNotIn(operation.CLAIM, ports.values)

    def test_complete_parent_provenance_qualifies_and_publishes_the_join(self):
        ports = ParentPorts()
        with ports.inert():
            result = operation.execute(ports.authority_pin, 100)
        self.assertIs(result["passed"], True, result)
        self.assertIs(result["feature_acceptance"], False)
        self.assertEqual(result["stages"], ports.read(operation.LIVE / "stage-result-v1.json")[0])
        self.assertEqual(ports.values[operation.CLAIM], dict(
            version=1, scope=operation.SCOPE, authority=ports.authority_pin, no_retry=True,
        ))
        ports.start.assert_called_once()
        ports.accept.assert_called_once_with(ports.read(ports.activation["path"])[1], ports.admission)

    def test_exit_type_cleanup_capture_worker_and_stage_authority_cannot_be_borrowed(self):
        for mutation in ("boolean_exit", "unknown_cleanup", "unknown_capture", "other_worker", "other_authority"):
            ports = ParentPorts(mutation)
            with self.subTest(mutation=mutation), ports.inert():
                result = operation.execute(ports.authority_pin, 100)
            self.assertIs(result["passed"], False, result)
            self.assertIsNone(result["stages"])
            ports.start.assert_called_once()
            ports.accept.assert_not_called()

    def test_supervisor_closes_capture_when_spawn_fails(self):
        capture = Mock()
        capture.close.return_value = True
        with patch.object(operation.process, "ServerCapture", return_value=capture), \
             patch.object(operation.subprocess, "Popen", side_effect=OSError("PRIVATE_SPAWN")), \
             patch.object(operation.host, "WindowsJob") as job, \
             patch.object(operation.time, "monotonic", return_value=101):
            result = operation._supervise(pin(operation.LIVE / "worker-request-v1.json"), 100)
        capture.close.assert_called_once_with()
        job.assert_not_called()
        self.assertIs(result["capture_complete"], False)
        self.assertIs(result["cleanup_complete"], False)
        self.assertNotIn("PRIVATE_SPAWN", str(result))


class WorkerTests(unittest.TestCase):
    def test_started_receipt_with_extra_field_never_dispatches_stages(self):
        ports = ParentPorts()
        request_path = operation.LIVE / "worker-request-v1.json"
        started_path = operation.LIVE / "worker-started-v1.json"
        attempt = pin(operation.CLAIM)
        request = ports.save(request_path, dict(
            version=1, scope=operation.SCOPE, authority=ports.authority_pin,
            attempt=attempt, parent=ports.parent, begin=100,
        ))
        ports.save(started_path, dict(request=request, worker=ports.worker, extra=True))
        stdin = Mock(buffer=BytesIO(operation.BARRIER + operation.env.encoded(request)))
        with (patch.object(operation.sys, "stdin", stdin),
              patch.object(operation.os, "getppid", return_value=ports.parent["pid"]),
              patch.object(operation.os, "getpid", return_value=ports.worker["pid"]),
              patch.object(operation, "_at", side_effect=ports.at) as bound_request,
              patch.object(operation, "_read", side_effect=ports.read) as read,
              patch.object(operation.activation, "_identity", side_effect=[ports.parent, ports.worker]) as identity,
              patch.object(operation, "_budget"),
              patch.object(operation, "_save") as save,
              patch.object(operation, "_run_stages", return_value={"passed": True}) as run):
            with self.assertRaises(REFUSED):
                operation._worker()
        bound_request.assert_called_once_with(request, request_path)
        read.assert_called_once_with(started_path)
        identity.assert_called_once_with(ports.parent["pid"], ports.parent)
        save.assert_not_called()
        run.assert_not_called()


if __name__ == "__main__":
    unittest.main()
