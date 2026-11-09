"""Inert command and closed replay tests for the combined Story Record cohort.

Copyright 2026 LocalLore contributors. SPDX-License-Identifier: Apache-2.0
"""
from collections import Counter
from copy import deepcopy
import json
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import Mock, patch

from benchmarks import android_instrumentation_evidence as evidence
from benchmarks import combined_record_ui_binding as binding
from benchmarks import combined_record_ui_controller as controller
from benchmarks import owned_target_contract as core
from benchmarks import receipt_avd_environment as env


ROLES = ("product_apk", "test_apk")
PACKAGES = (binding.APP, binding.TEST)
STAGED = ("/data/local/tmp/locallore-product-v1.apk", "/data/local/tmp/locallore-test-v1.apk")
INSTALLED = tuple(f"/data/app/~~synthetic/{package}-instance/base.apk" for package in PACKAGES)
BOOT = ["getprop", "sys.boot_completed"]
PROPERTIES = (
    ("ro.build.version.sdk", b"35\n"),
    ("ro.product.cpu.abi", b"x86_64\n"),
    ("ro.kernel.qemu", b"1\n"),
)
USER = ["am", "get-current-user"]
REFUSALS = (env.EnvironmentRefused, core.TargetRefused)


def _packages(package):
    return ["cmd", "package", "list", "packages", "-U", "--user", "0", package]


def _package_path(package):
    return ["cmd", "package", "path", "--user", "0", package]


def _runner_output(klass, method):
    pair = "".join(
        f"INSTRUMENTATION_STATUS: class={klass}\n"
        f"INSTRUMENTATION_STATUS: test={method}\n"
        "INSTRUMENTATION_STATUS: current=1\n"
        "INSTRUMENTATION_STATUS: numtests=1\n"
        f"INSTRUMENTATION_STATUS_CODE: {code}\n"
        for code in (1, 0)
    )
    return (pair + "INSTRUMENTATION_RESULT: stream=\n\nTime: 0.02\n\nOK (1 test)\n\n"
            "INSTRUMENTATION_CODE: -1\n").encode("ascii")


class SyntheticGuest:
    """The fixture never opens files, process handles, sockets, or SDK clients."""

    def __init__(self, boot=(b"1\n",)):
        self.boot = iter(boot)
        self.artifacts = binding.artifact_bindings()
        self.calls = []
        self.counts = Counter()
        self.pauses = 0
        self.overrides = {}
        self.raw = []

    def override(self, argv, occurrence, raw):
        self.overrides[tuple(argv), occurrence] = raw

    def _reply(self, argv, occurrence):
        if argv == BOOT:
            return next(self.boot, b"0\n")
        if argv[0] == "getprop":
            return dict(PROPERTIES)[argv[1]]
        if argv == USER:
            return b"0\n"
        if argv[:4] == ["cmd", "package", "list", "packages"]:
            if occurrence == 1:
                return b""
            index = PACKAGES.index(argv[-1])
            return f"package:{argv[-1]} uid:{10001 + index}\n".encode("ascii")
        if argv[:3] == ["cmd", "package", "path"]:
            path = INSTALLED[PACKAGES.index(argv[-1])]
            return f"package:{path}\n".encode("ascii")
        if argv[0] == "sha256sum":
            path = argv[1]
            index = STAGED.index(path) if path in STAGED else INSTALLED.index(path)
            digest = self.artifacts[ROLES[index]]["sha256"]
            return f"{digest}  {path}\n".encode("ascii")
        if argv[0] == "dd":
            return b""
        if argv[:2] == ["pm", "install"]:
            return b"Success\n"
        if argv[:2] == ["am", "instrument"]:
            klass, method = argv[6].split("#")
            return _runner_output(klass, method)
        raise AssertionError(f"Unexpected synthetic command {argv!r}")

    def command(self, argv, label, *, source=None, seconds=15, limit=131072):
        key = tuple(argv)
        self.counts[key] += 1
        occurrence = self.counts[key]
        self.calls.append((argv, label, source, seconds, limit))
        if (key, occurrence) in self.overrides:
            raw = self.overrides[key, occurrence]
        else:
            raw = self._reply(argv, occurrence)
        self.raw.append(raw)
        return raw

    def pause(self):
        self.pauses += 1
        if self.pauses > 61:
            raise AssertionError("Unbounded synthetic boot polling")

    def run(self):
        return controller._journey(self.command, self.pause, self.artifacts)

    @property
    def argv(self):
        return [row[0] for row in self.calls]

    @property
    def instruments(self):
        return [argv for argv in self.argv if argv[:2] == ["am", "instrument"]]


def _expected_commands(boot_count=1):
    setup = [
        *[BOOT] * boot_count,
        *[["getprop", prop] for prop, _ in PROPERTIES],
        USER,
        *[_packages(package) for package in PACKAGES],
    ]
    install = [argv for path in STAGED for argv in (
        ["dd", "of=" + path, "bs=65536"],
        ["sha256sum", path],
        ["pm", "install", "-r", "-t", "--user", "0", path],
    )]
    installed = [argv for package, path in zip(PACKAGES, INSTALLED) for argv in (
        _packages(package), _package_path(package), ["sha256sum", path],
    )]
    methods = [binding.instrumentation_argv(kind) for kind, _, _ in binding.INSTRUMENTATIONS]
    return setup + install + installed + methods + installed


class CombinedRecordUiJourneyTests(unittest.TestCase):
    def test_exact_install_and_test_order_and_distinct_package_identities(self):
        guest = SyntheticGuest((b"", b"0\n", b"1\n"))
        journey = guest.run()
        self.assertEqual(guest.argv, _expected_commands(boot_count=3))
        self.assertEqual(guest.pauses, 2)
        self.assertEqual([source for argv, _, source, _, _ in guest.calls if argv[0] == "dd"],
                         [guest.artifacts[role] for role in ROLES])
        self.assertTrue(all(source is None for argv, _, source, _, _ in guest.calls if argv[0] != "dd"))
        self.assertEqual(journey["installed"], {
            role: dict(package=package, uid=10001 + index, path=path,
                       sha256=guest.artifacts[role]["sha256"])
            for index, (role, package, path) in enumerate(zip(ROLES, PACKAGES, INSTALLED))
        })
        self.assertEqual(journey["tests"], [
            dict(kind=kind, **binding.validate_result(kind, _runner_output(klass, method)))
            for kind, klass, method in binding.INSTRUMENTATIONS
        ])
        self.assertEqual([label for argv, label, _, _, _ in guest.calls if argv[:2] == ["am", "instrument"]],
                         [kind for kind, _, _ in binding.INSTRUMENTATIONS])

    def test_wrong_guest_or_existing_package_refuses_before_any_write(self):
        bad_preflight = (
            (["getprop", "ro.build.version.sdk"], b"34\n"),
            (["getprop", "ro.product.cpu.abi"], b"arm64-v8a\n"),
            (["getprop", "ro.kernel.qemu"], b"0\n"),
            (USER, b"10\n"),
            *[(_packages(package), f"package:{package} uid:10001\n".encode()) for package in PACKAGES],
        )
        for argv, raw in bad_preflight:
            with self.subTest(argv=argv):
                guest = SyntheticGuest()
                guest.override(argv, 1, raw)
                with self.assertRaises(env.EnvironmentRefused):
                    guest.run()
                self.assertEqual(guest.argv[-1], argv)
                self.assertFalse(any(command[0] in ("dd", "pm") for command in guest.argv))
                self.assertEqual(guest.instruments, [])

    def test_boot_polling_stops_without_installing(self):
        guest = SyntheticGuest(boot=())
        with self.assertRaises(env.EnvironmentRefused):
            guest.run()
        self.assertEqual(guest.argv, [BOOT] * 61)
        self.assertEqual(guest.pauses, 60)

    def test_wrong_staged_digest_refuses_install_and_test(self):
        guest = SyntheticGuest()
        argv = ["sha256sum", STAGED[0]]
        guest.override(argv, 1, f"{'0' * 64}  {STAGED[0]}\n".encode())
        with self.assertRaises(env.EnvironmentRefused):
            guest.run()
        self.assertEqual(guest.argv[-1], argv)
        self.assertFalse(any(command[0] == "pm" for command in guest.argv))
        self.assertEqual(guest.instruments, [])

    def test_wrong_installed_digest_shared_uid_or_foreign_path_refuses_test(self):
        cases = (
            (["sha256sum", INSTALLED[1]], 1, f"{'0' * 64}  {INSTALLED[1]}\n".encode()),
            (_packages(PACKAGES[1]), 2, f"package:{PACKAGES[1]} uid:10001\n".encode()),
            (_package_path(PACKAGES[0]), 1, f"package:{INSTALLED[1]}\n".encode()),
        )
        for argv, occurrence, raw in cases:
            with self.subTest(argv=argv):
                guest = SyntheticGuest()
                guest.override(argv, occurrence, raw)
                with self.assertRaises(env.EnvironmentRefused):
                    guest.run()
                self.assertEqual(guest.instruments, [])

    def test_malformed_or_cross_method_result_stops_after_the_failed_attempt(self):
        kinds = [kind for kind, _, _ in binding.INSTRUMENTATIONS]
        next_klass, next_method = binding.INSTRUMENTATIONS[2][1:]
        bad_results = (
            b"INSTRUMENTATION_RESULT: stream=\n\nTime: 0.01\n\nOK (1 test)\n\nINSTRUMENTATION_CODE: -1\n",
            _runner_output(next_klass, next_method),
        )
        for raw in bad_results:
            with self.subTest(raw=raw):
                guest = SyntheticGuest()
                guest.override(binding.instrumentation_argv(kinds[1]), 1, raw)
                with self.assertRaises(evidence.EvidenceRefused):
                    guest.run()
                self.assertEqual(guest.instruments, [binding.instrumentation_argv(kind) for kind in kinds[:2]])
                self.assertEqual(guest.argv[-1], guest.instruments[-1])

    def test_changed_uid_after_cohort_refuses_without_rerunning_any_method(self):
        guest = SyntheticGuest()
        guest.override(_packages(PACKAGES[0]), 3, f"package:{PACKAGES[0]} uid:10003\n".encode())
        with self.assertRaises(env.EnvironmentRefused):
            guest.run()
        self.assertEqual(guest.instruments,
                         [binding.instrumentation_argv(kind) for kind, _, _ in binding.INSTRUMENTATIONS])


class CombinedRecordUiReplayTests(unittest.TestCase):
    def setUp(self):
        guest = SyntheticGuest()
        self.journey = guest.run()
        self.admission = {"artifacts": guest.artifacts}
        self.output = Path("D:/Dev/Experiments/LocalLore/synthetic-combined-record-controller-v1")
        self.session_binding = self.pin(self.output / "sdk-session-v21.json")
        self.trace = [self.pin(self.output / "clients" / f"command-{index:04d}.json")
                      for index in range(1, len(guest.calls) + 1)]
        self.raw = {}
        self.rows = []
        for index, ((argv, label, source, seconds, _), stdout) in enumerate(zip(guest.calls, guest.raw), 1):
            stem = self.output / "clients" / f"command-{index:04d}"
            stdout_pin = self.pin(stem.with_suffix(".stdout.bin"))
            stderr_pin = self.pin(stem.with_suffix(".stderr.bin"))
            self.raw[stdout_pin["path"]] = stdout
            self.raw[stderr_pin["path"]] = b"staged bytes\n" if source is not None else b""
            self.rows.append(dict(index=index, label=label, operation=dict(argv=argv, stdin=source),
                                  client_qualified=True, status="completed", returncode=0,
                                  effective_deadline_ms=seconds * 1000,
                                  stdout=stdout_pin, stderr=stderr_pin))
        self.reader = Mock()
        self.reader._json.return_value = {}
        self.reader._pin.side_effect = self.pin
        self.reader._raw.side_effect = self.read_raw
        self.reader.require_current_clients.side_effect = lambda *_: self.rows

    @staticmethod
    def pin(path):
        return {"path": str(path), "bytes": 1, "sha256": "a" * 64}

    def read_raw(self, pin, cap=131072):
        raw = self.raw[pin["path"]]
        if len(raw) > cap:
            raise core.TargetRefused("binding")
        return raw

    def replay(self):
        with patch.object(controller.client, "REPLAY", self.reader):
            return controller._replay(
                self.output, len(self.trace), self.trace, self.session_binding, self.admission)

    def test_replay_joins_exact_raw_command_and_result_roster(self):
        self.assertEqual(self.replay(), self.journey)
        self.reader.require_current_clients.assert_called_once_with(
            self.output, len(self.trace), self.session_binding, self.admission)

    def test_replay_refuses_missing_reordered_relabelled_and_extra_records(self):
        original_rows = deepcopy(self.rows)
        original_trace = deepcopy(self.trace)
        first_method = next(i for i, row in enumerate(self.rows) if row["operation"]["argv"][:2] == ["am", "instrument"])
        for variant in ("missing", "reordered", "relabelled", "extra"):
            with self.subTest(variant=variant):
                self.rows, self.trace = deepcopy(original_rows), deepcopy(original_trace)
                if variant == "missing":
                    del self.rows[-1], self.trace[-1]
                elif variant == "reordered":
                    self.rows[first_method], self.rows[first_method + 1] = (
                        self.rows[first_method + 1], self.rows[first_method])
                elif variant == "relabelled":
                    self.rows[first_method]["label"] = self.rows[first_method + 1]["label"]
                else:
                    self.rows.append(deepcopy(self.rows[-1]))
                    self.trace.append(deepcopy(self.trace[-1]))
                with self.assertRaises(REFUSALS):
                    self.replay()

    def test_replay_refuses_noncanonical_status_or_changed_command_and_trace(self):
        original_rows = deepcopy(self.rows)
        original_trace = deepcopy(self.trace)
        for variant in ("bool-returncode", "failed-status", "unqualified", "wrong-index", "wrong-argv", "wrong-pin"):
            with self.subTest(variant=variant):
                self.rows, self.trace = deepcopy(original_rows), deepcopy(original_trace)
                row = self.rows[0]
                if variant == "bool-returncode":
                    row["returncode"] = False
                elif variant == "failed-status":
                    row["status"] = "refused"
                elif variant == "unqualified":
                    row["client_qualified"] = False
                elif variant == "wrong-index":
                    row["index"] = 2
                elif variant == "wrong-argv":
                    row["operation"]["argv"] = ["getprop", "ro.product.cpu.abi"]
                else:
                    self.trace[0]["sha256"] = "b" * 64
                with self.assertRaises(REFUSALS):
                    self.replay()

    def test_replay_checks_shell_stderr_and_independently_parses_selected_junit(self):
        row = next(row for row in self.rows if row["operation"]["argv"][:2] == ["am", "instrument"])
        stderr = row["stderr"]["path"]
        self.raw[stderr] = b"synthetic error\n"
        with self.assertRaises(env.EnvironmentRefused):
            self.replay()
        self.raw[stderr] = b""
        self.raw[row["stdout"]["path"]] = _runner_output(*binding.INSTRUMENTATIONS[1][1:])
        with self.assertRaises(evidence.EvidenceRefused):
            self.replay()

    def test_replay_refuses_excess_or_noninteger_command_deadline(self):
        row = self.rows[0]
        allowed = row["effective_deadline_ms"]
        for value in (True, float(allowed), allowed + 1):
            with self.subTest(value=value):
                row["effective_deadline_ms"] = value
                with self.assertRaises(core.TargetRefused):
                    self.replay()


class CombinedRecordUiControllerResultTests(unittest.TestCase):
    def test_refused_run_preserves_dispatched_prefix_and_releases_observer(self):
        with TemporaryDirectory(prefix="record-controller-", dir=Path.cwd()) as directory:
            root = Path(directory)
            output = root / "controller-v1"
            capture = Mock(count=0, directory=output / "clients", session_binding={"path": "synthetic-session"})
            live = Mock(caller={"pid": 7})
            live.close.return_value = True
            reader = Mock()
            command_pin = {"path": "synthetic-first-command", "bytes": 4, "sha256": "f" * 64}
            reader._pin.return_value = command_pin

            def refuse_after_dispatch(*_args, **_kwargs):
                capture.directory.mkdir()
                (capture.directory / "command-0001.json").write_bytes(b"held")
                capture.count = 1
                raise RuntimeError("private synthetic error")

            capture.shell.side_effect = refuse_after_dispatch
            admission = {"root": str(root), "artifacts": binding.artifact_bindings()}
            with patch.object(controller, "_admission", return_value=admission), \
                    patch.object(controller.client, "LiveOwnedCombinedRecordUiTarget", return_value=live) as opened, \
                    patch.object(controller.client, "OwnedCombinedRecordUiSdkCapture", return_value=capture), \
                    patch.object(controller.client, "REPLAY", reader):
                result = controller.run({"path": "synthetic-admission"}, {"path": "synthetic-running"})
                with self.assertRaises(FileExistsError):
                    controller.run({"path": "synthetic-admission"}, {"path": "synthetic-running"})
            self.assertEqual(result["outcome"], "refused")
            self.assertEqual(result["reason"], "checks_failed")
            self.assertIsNone(result["journey"])
            self.assertFalse(result["feature_acceptance"])
            self.assertIs(result["observer_handles_closed"], True)
            self.assertEqual((result["client_count"], result["clients"]), (1, [command_pin]))
            self.assertEqual(json.loads((output / "controller-result-v1.json").read_bytes()), result)
            opened.assert_called_once()
            capture.close.assert_called_once_with()
            live.close.assert_called_once_with()

    def test_unknown_observer_close_refuses_otherwise_complete_journey(self):
        with TemporaryDirectory(prefix="record-controller-", dir=Path.cwd()) as directory:
            root = Path(directory)
            capture = Mock(count=0, clean=True, session_binding={"path": "synthetic-session"})
            live = Mock(caller={"pid": 7})
            live.close.return_value = False
            journey = {"installed": {}, "tests": []}
            admission = {"root": str(root), "artifacts": binding.artifact_bindings()}
            with patch.object(controller, "_admission", return_value=admission), \
                    patch.object(controller.client, "LiveOwnedCombinedRecordUiTarget", return_value=live), \
                    patch.object(controller.client, "OwnedCombinedRecordUiSdkCapture", return_value=capture), \
                    patch.object(controller, "_journey", return_value=journey), \
                    patch.object(controller, "_replay", return_value=journey), \
                    patch.object(controller.contract, "revalidate_inputs"), \
                    patch.object(controller.binding, "verify_artifacts"):
                result = controller.run({"path": "synthetic-admission"}, {"path": "synthetic-running"})
            self.assertEqual(result["outcome"], "refused")
            self.assertEqual(result["reason"], "resource_uncertain")
            self.assertIs(result["observer_handles_closed"], False)
            self.assertEqual(json.loads((root / "controller-v1" / "controller-result-v1.json").read_bytes()), result)
            capture.close.assert_called_once_with()
            live.close.assert_called_once_with()
