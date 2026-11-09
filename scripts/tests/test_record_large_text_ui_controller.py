"""Independent SDK19 command and proof oracles with synthetic target observations.

The real v4 client and replay validators see fixture bytes, never an ADB
process, device, emulator, or shared ledger.
"""
import contextlib
import copy
import hashlib
import io
import os
from dataclasses import dataclass, replace
from pathlib import Path
import sys
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import Mock, patch

from benchmarks.android_instrumentation_evidence import EvidenceRefused
from benchmarks import owned_record_large_text_ui_contract as profile
from benchmarks import owned_record_large_text_ui_owner as owner
from benchmarks import owned_target_contract as core
from benchmarks import receipt_avd_environment as env
from benchmarks import record_large_text_ui_controller as controller
from scripts.tests import test_android_instrumentation_evidence as junit
from scripts.tests import test_archive_ui_controller_fixtures as host
from scripts.tests import test_owned_target_contract as legacy
from scripts.tests.test_record_large_text_ui_profile import admission, expected_artifacts


APP = "org.locallore.app.archiveverify"
TEST = APP + ".test"
CLASS = "org.locallore.app.StoryRecordLargeTextTest"
METHOD = "narrowRecordReflowsAtDoubleTextSizeAndKeepsActionsReachable"
INSTRUMENTATIONS = (("record_large_text", CLASS, METHOD),)
SESSION_FILE = "sdk-session-v19.json"
PROOF_PROTOCOL = "record-large-text-ui-socket-proof-v1"
ROLES = ("product_apk", "test_apk")
PACKAGES = dict(zip(ROLES, (APP, TEST)))
UIDS = dict(zip(ROLES, (10001, 10002)))
STAGED = ("/data/local/tmp/locallore-product-v1.apk", "/data/local/tmp/locallore-test-v1.apk")
INSTALLED = {role: f"/data/app/~~synthetic/{package}-opaque==/base.apk"
             for role, package in PACKAGES.items()}
REFUSED = (ValueError, env.EnvironmentRefused, EvidenceRefused)


@dataclass(frozen=True)
class Step:
    argv: list
    label: str
    stdout: bytes
    stderr: bytes = b""
    seconds: int = 15
    source: dict | None = None
    limit: int = 131072


def junit_bytes():
    return (junit.bundle(METHOD, 1, 1, cls=CLASS, count=1)
            + junit.bundle(METHOD, 1, 0, cls=CLASS, count=1)
            + junit.ending(1)).encode()


def package_argv(package):
    return ["cmd", "package", "list", "packages", "-U", "--user", "0", package]


def expected_steps(artifacts, *, boot=(b"1\n",)):
    rows = [Step(["getprop", "sys.boot_completed"], "boot", value) for value in boot]
    rows += [
        Step(["getprop", "ro.build.version.sdk"], "property", b"35\n"),
        Step(["getprop", "ro.product.cpu.abi"], "property", b"x86_64\n"),
        Step(["getprop", "ro.kernel.qemu"], "property", b"1\n"),
        Step(["am", "get-current-user"], "user", b"0\n"),
        Step(package_argv(APP), "package-absent", b""),
        Step(package_argv(TEST), "package-absent", b""),
    ]
    for role, path in zip(ROLES, STAGED):
        pin = artifacts[role]
        rows += [
            Step(["dd", "of=" + path, "bs=65536"], "apk-stage", b"",
                 b"synthetic dd byte count\n", seconds=120, source=pin),
            Step(["sha256sum", path], "staged-hash", f"{pin['sha256']}  {path}\n".encode()),
            Step(["pm", "install", "-r", "-t", "--user", "0", path], "install", b"Success\n", seconds=120),
        ]

    def installed_rows():
        result = []
        for role in ROLES:
            package = PACKAGES[role]
            path = INSTALLED[role]
            # Android matches package-list filter by substring. The app query
            # returns both packages, but only the exact name supplies its UID.
            uid_text = "".join(f"package:{name} uid:{UIDS[key]}\n" for key, name in PACKAGES.items()
                               if package in name)
            result += [
                Step(package_argv(package), "package", uid_text.encode()),
                Step(["cmd", "package", "path", "--user", "0", package], "package-path",
                     f"package:{path}\n".encode()),
                Step(["sha256sum", path], "package-hash",
                     f"{artifacts[role]['sha256']}  {path}\n".encode()),
            ]
        return result

    rows += installed_rows()
    rows += [Step(
        ["am", "instrument", "-w", "-r", "-e", "class", CLASS + "#" + METHOD,
         TEST + "/androidx.test.runner.AndroidJUnitRunner"],
        "record_large_text", junit_bytes(), seconds=90, limit=262144,
    )]
    rows += installed_rows()
    return rows


def expected_trace():
    return dict(
        installed={role: dict(package=PACKAGES[role], uid=UIDS[role], path=INSTALLED[role])
                   for role in ROLES},
        instrumentation=dict(
            **{"class": CLASS}, methods=[METHOD], method_count=1,
            stdout_sha256=hashlib.sha256(junit_bytes()).hexdigest(), passed=True,
        ),
    )


def running(value):
    result = legacy.running(value)
    result["protocol"] = "owned-emulator-record-large-text-ui-v1"
    return result


class TinyBuild:
    """Fresh tiny fixture files carry real D: pins, never genuine APKs."""

    def __init__(self):
        self.base = Path(tempfile.mkdtemp(prefix="sdk19-controller-"))
        assert self.base.drive.upper() == "D:"
        self.artifacts = {}
        for role, name in (("build", "build.json"), ("product_apk", "app.apk"), ("test_apk", "test.apk")):
            path = self.base / name
            self.write(path, f"SDK19 synthetic {role} bytes\n".encode())
            self.artifacts[role] = env.binding(path)

    def write(self, path, raw):
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(raw)

    def admission(self):
        return dict(artifacts=copy.deepcopy(self.artifacts))

    def inputs(self, _module):
        # Replace only the fixed B124 file identities. The real reader still
        # checks all three fixture paths, sizes and hashes.
        return patch.object(profile, "artifact_bindings", side_effect=lambda: copy.deepcopy(self.artifacts))


class Graph(host.ControllerGraph):
    @contextlib.contextmanager
    def modules(self):
        with contextlib.ExitStack() as stack:
            for name, value in (
                ("f", sys.modules[__name__]), ("controller", controller), ("contract", profile),
                ("owner", owner), ("build", profile),
                ("builds", SimpleNamespace(BuildGraph=TinyBuild, pin=env.binding, encoded=env.encoded)),
            ):
                stack.enter_context(patch.object(host, name, value))
            yield

    def __init__(self, *, boot=(b"1\n",), close=True):
        with self.modules():
            super().__init__(close=close)
        self.steps = expected_steps(self.a["artifacts"], boot=boot)

    @contextlib.contextmanager
    def inputs(self):
        with self.modules(), super().inputs():
            yield

    def prove(self, live, path, session, context, sock, anchor, after=False):
        proof = legacy.proof(session, after=after)
        proof.update(protocol=PROOF_PROTOCOL, context=copy.deepcopy(context), anchor=copy.deepcopy(anchor),
                     session=env.binding(Path(session["root"]) / SESSION_FILE))
        bundle = legacy.query_bundle(session)
        bundle["protocol"] = PROOF_PROTOCOL
        queries = path.with_name(path.stem + "-queries-v1.json")
        env.create_json(queries, bundle)
        proof["queries"] = env.binding(queries)
        env.create_json(path, proof)
        self.proofs.append((context["index"], context["phase"]))
        return env.binding(path)

    def response(self, argv):
        step = self.steps[len(self.calls)]
        self.calls.append(list(argv))
        if step.argv != argv:
            raise AssertionError(f"Unexpected synthetic command: {argv!r}")
        return step.stdout, step.stderr

    def replace_json(self, path, value):
        self.g.write(path, env.encoded(value))
        return env.binding(path)

    def result_path(self):
        return self.output / "controller-result-v1.json"


class FixedCommandTests(unittest.TestCase):
    def exercise(self, rows, *, refused_at=None):
        calls = []
        waits = []
        artifacts = expected_artifacts()

        def command(argv, label, *, seconds=15, source=None, limit=131072):
            index = len(calls)
            calls.append(argv)
            self.assertLess(index, len(rows), "extra command after refusal")
            step = rows[index]
            self.assertEqual((argv, label, seconds, source, limit),
                             (step.argv, step.label, step.seconds, step.source, step.limit))
            return step.stdout

        if refused_at is not None:
            with self.assertRaises(REFUSED):
                controller._exercise(command, artifacts, lambda: waits.append(None))
            self.assertEqual(len(calls), refused_at + 1)
            return None
        trace = controller._exercise(command, artifacts, lambda: waits.append(None))
        self.assertEqual(len(calls), len(rows))
        return trace, len(waits)

    def test_literal_sequence_with_incomplete_boot_and_exactly_one_method(self):
        rows = expected_steps(expected_artifacts(), boot=(b"", b"0\n", b"1\n"))
        self.assertEqual(len(rows), 28)
        self.assertEqual(self.exercise(rows), (expected_trace(), 2))

    def test_invalid_target_stage_and_junit_bytes_stop_at_first_failure(self):
        original = expected_steps(expected_artifacts())
        cases = [
            (0, b"1\n0\n"), (1, b"36\n"), (2, b"arm64-v8a\n"), (3, b"0\n"), (4, b"10\n"),
            (5, f"package:{APP} uid:10001\n".encode()),
            (5, f"package:{TEST} uid:10002\n".encode()),
            (7, b"unexpected output\n"),
            (8, b"0" * 64 + f"  {STAGED[0]}\n".encode()),
            (9, b"Success\nfailure\n"),
            (14, b"package:/data/app/../../base.apk\n"),
            (19, junit.ending(1).encode()),
            (19, junit_bytes().replace(METHOD.encode(), b"otherTest")),
        ]
        for index, raw in cases:
            with self.subTest(index=index, raw=raw):
                rows = list(original)
                rows[index] = replace(rows[index], stdout=raw)
                self.exercise(rows, refused_at=index)

    def test_identity_drift_and_shared_uid_refuse_even_with_exact_apk_hashes(self):
        for changed_index, uid, refused_at in ((16, 10001, 18), (23, 29999, 25)):
            with self.subTest(changed_index=changed_index):
                rows = expected_steps(expected_artifacts())
                rows[changed_index] = replace(rows[changed_index],
                                              stdout=f"package:{TEST} uid:{uid}\n".encode())
                self.exercise(rows, refused_at=refused_at)

    def test_boot_polling_stops_after_sixty_one_unready_observations(self):
        rows = expected_steps(expected_artifacts(), boot=(b"0\n",) * 61)
        self.exercise(rows, refused_at=60)

    def test_cli_returns_one_for_environment_refusal_without_traceback(self):
        admission_pin = legacy.pin("D:/Synthetic/admission.json")
        running_pin = legacy.pin("D:/Synthetic/running.json")
        argv = ["--admission", admission_pin["path"], "--admission-sha256", admission_pin["sha256"],
                "--running", running_pin["path"], "--running-sha256", running_pin["sha256"]]
        stderr = io.StringIO()
        with patch.object(controller.file_guard, "_existing_D_file", side_effect=lambda path, _: Path(path)), \
             patch.object(controller.file_guard, "_read_bound",
                          side_effect=[(admission_pin, {}), (running_pin, {})]), \
             patch.object(controller, "run", side_effect=env.EnvironmentRefused("binding")) as run, \
             contextlib.redirect_stderr(stderr):
            self.assertEqual(controller.main(argv), 1)
        run.assert_called_once_with(admission_pin, running_pin)
        self.assertEqual(stderr.getvalue(), "")


@unittest.skipUnless(os.name == "nt", "D: synthetic fixture and Windows path grammar")
class ClosedReplayTests(unittest.TestCase):
    def complete(self):
        graph = Graph()
        with graph.inputs():
            result = graph.run()
            self.assertEqual(result["outcome"], "completed", result)
            self.assertEqual(graph.verify(), result)
        self.assertEqual(result["trace"], expected_trace())
        self.assertEqual(result["client_count"], 26)
        self.assertEqual(len(graph.calls), 26)
        self.assertEqual(graph.proofs, [(i, phase) for i in range(1, 27) for phase in ("before", "after")])
        self.assertTrue(all(sock.closed for sock in graph.sockets))
        self.assertEqual(graph.close_calls, 1)
        self.assertIs(result["observer_handles_closed"], True)
        self.assertIs(result["feature_acceptance"], False)
        return graph, result

    def test_closed_replay_requires_exact_caller_and_rejects_trace_mutation(self):
        graph, result = self.complete()
        foreign_caller = dict(graph.caller, pid=graph.caller["pid"] + 1000)
        with graph.inputs(), self.assertRaises(REFUSED):
            graph.verify(caller=foreign_caller)
        altered = copy.deepcopy(result)
        altered["trace"]["installed"]["test_apk"]["uid"] = 29999
        graph.replace_json(graph.result_path(), altered)
        with graph.inputs(), self.assertRaises(REFUSED):
            graph.verify()

    def test_closed_replay_refuses_extra_record_and_cross_bound_command_proof(self):
        graph, _ = self.complete()
        clients = graph.output / "clients"
        extra = clients / "unlisted.bin"
        extra.write_bytes(b"extra")
        with graph.inputs(), self.assertRaises(REFUSED):
            graph.verify()
        # Move the synthetic extra to the fixture root, retaining its bytes.
        extra.rename(graph.g.base / "unlisted.bin")
        command = clients / "command-0020.json"
        row = env.decode_json(command.read_bytes())
        row["server_before"] = copy.deepcopy(row["server_after"])
        graph.replace_json(command, row)
        with graph.inputs(), self.assertRaises(REFUSED):
            graph.verify()

    def test_late_cancel_and_unknown_close_preserve_refusal_and_close_observer_once(self):
        cancelled = Graph()
        with cancelled.inputs(), patch.object(controller, "_exercise", side_effect=KeyboardInterrupt("private")):
            result = cancelled.run()
        self.assertEqual((result["outcome"], result["reason"]), ("refused", "cancelled"))
        self.assertEqual(cancelled.close_calls, 1)
        self.assertTrue(cancelled.result_path().is_file())
        self.assertEqual(cancelled.calls, [])

        unknown = Graph(close=1)
        with unknown.inputs():
            result = unknown.run()
        self.assertEqual((result["outcome"], result["reason"]), ("refused", "resource_uncertain"))
        self.assertIsNot(result["observer_handles_closed"], True)
        self.assertEqual(unknown.close_calls, 1)
        self.assertTrue((unknown.output / "clients" / "command-0020.stdout.bin").is_file())

    def test_rejected_preflight_creates_no_output_and_constructs_no_observer(self):
        graph = Graph()
        with patch.object(controller, "_inputs", side_effect=env.EnvironmentRefused("binding")), \
             patch.object(controller, "LiveOwnedRecordLargeTextUiTarget") as live, \
             self.assertRaises(REFUSED):
            graph.run()
        live.assert_not_called()
        self.assertFalse(graph.output.exists())


if __name__ == "__main__":
    unittest.main()
