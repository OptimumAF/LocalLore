"""Original synthetic command tapes for the storage-opener journey and replay.

Copyright 2026 LocalLore contributors. SPDX-License-Identifier: Apache-2.0
"""
import copy
import hashlib
from pathlib import PureWindowsPath
import unittest
from unittest.mock import Mock, patch

from benchmarks import android_instrumentation_evidence as evidence
from benchmarks import receipt_avd_environment as env
from benchmarks import storage_opener_capture as capture
from benchmarks import storage_opener_journey as journey
from scripts.tests.test_storage_opener_capture import KINDS, SELECTORS, argv, expected_result, stdout


APP = "org.locallore.app.archiveverify"
TARGETS = (
    ("product_apk", APP, "/data/local/tmp/locallore-product-v1.apk", 10001),
    ("test_apk", APP + ".test", "/data/local/tmp/locallore-test-v1.apk", 10002),
)
REFUSALS = (RuntimeError, ValueError)


def package_query(package):
    return ["cmd", "package", "list", "packages", "-U", "--user", "0", package]


class Tape:
    def __init__(self, pins):
        self.rows = []
        self.expected = []
        self.raw = {}
        self.installed = {
            role: dict(package=package, uid=uid, path=f"/data/app/{package}-fixture/base.apk",
                       sha256=pins[role]["sha256"])
            for role, package, _, uid in TARGETS
        }
        self.add("boot", ["getprop", "sys.boot_completed"], b"0\n")
        self.add("boot", ["getprop", "sys.boot_completed"], b"1\n")
        for key, value in (("ro.build.version.sdk", b"35"), ("ro.product.cpu.abi", b"x86_64"),
                           ("ro.kernel.qemu", b"1")):
            self.add("property", ["getprop", key], value + b"\n")
        self.add("user", ["am", "get-current-user"], b"0\n")
        for _, package, _, _ in TARGETS:
            self.add("package-absent", package_query(package), b"")
        for role, _, path, _ in TARGETS:
            self.add("apk-stage", ["dd", "of=" + path, "bs=65536"], b"", source=pins[role],
                     seconds=120, err=b"synthetic dd transfer summary\n")
            self.add("staged-hash", ["sha256sum", path], self.hash_line(pins[role]["sha256"], path))
            self.add("install", ["pm", "install", "-R", "-t", "--user", "0", path], b"Success\n", seconds=120)
        self.read_installed()
        for index, kind in enumerate(KINDS):
            self.add(kind, argv(index), stdout(index), seconds=90, limit=evidence.MAX_BYTES)
            self.read_installed()

    @staticmethod
    def hash_line(sha256, path):
        return f"{sha256}  {path}\n".encode()

    def pin(self, path, data):
        self.raw[path] = data
        return dict(path=path, bytes=len(data), sha256=hashlib.sha256(data).hexdigest())

    def add(self, label, args, data, *, source=None, seconds=15, limit=131072, err=b""):
        index = len(self.rows) + 1
        self.expected.append((args, label, source, seconds, limit))
        prefix = PureWindowsPath(f"D:/Synthetic/storage-opener/command-{index:04d}")
        self.rows.append(dict(
            index=index, effective_deadline_ms=seconds * 1000, label=label,
            operation=dict(argv=args, stdin=source), client_qualified=True, status="completed", returncode=0,
            stdout=self.pin(str(prefix.with_suffix(".stdout.bin")), data),
            stderr=self.pin(str(prefix.with_suffix(".stderr.bin")), err),
        ))

    def read_installed(self):
        for package in self.installed.values():
            name, uid, path, digest = (package[k] for k in ("package", "uid", "path", "sha256"))
            self.add("package", package_query(name), f"package:{name} uid:{uid}\n".encode())
            self.add("package-path", ["cmd", "package", "path", "--user", "0", name],
                     f"package:{path}\n".encode())
            self.add("package-hash", ["sha256sum", path], self.hash_line(digest, path))

    def read_raw(self, pin, *, cap):
        data = self.raw[pin["path"]]
        env.require(len(data) == pin["bytes"] and len(data) <= cap
                    and hashlib.sha256(data).hexdigest() == pin["sha256"], "raw")
        return data

    def find(self, label, ordinal=0):
        return [index for index, row in enumerate(self.rows) if row["label"] == label][ordinal]

    def replace_raw(self, index, data, channel="stdout"):
        self.rows[index][channel] = self.pin(self.rows[index][channel]["path"], data)


class StorageOpenerJourneyTests(unittest.TestCase):
    def setUp(self):
        self.pins = capture.artifact_bindings()
        self.verify = self.enterContext(patch.object(capture, "verify_artifacts", return_value=SELECTORS))
        self.tape = Tape(self.pins)

    def command(self):
        def dispatch(args, label, *, source=None, seconds=15, limit=131072):
            index = command.call_count - 1
            self.assertEqual((args, label, source, seconds, limit), self.tape.expected[index])
            self.assertGreaterEqual(self.verify.call_count, 1)
            row = self.tape.rows[index]
            return self.tape.read_raw(row["stdout"], cap=limit)

        command = Mock(side_effect=dispatch)
        return command

    def replay(self, rows=None):
        if rows is None:
            rows = self.tape.rows
        return journey.replay_journey(self.pins, rows, self.tape.read_raw)

    def test_live_and_complete_raw_replay_agree_on_all_checks_and_both_tests(self):
        command, pause = self.command(), Mock()
        expected = {"installed": self.tape.installed,
                    "tests": [expected_result(index, stdout(index)) for index in range(2)]}
        self.assertEqual(journey.run_journey(self.pins, command, pause), expected)
        self.assertEqual(command.call_count, 34)
        pause.assert_called_once_with()
        self.assertEqual(self.verify.call_count, 2)
        self.verify.reset_mock()
        self.assertEqual(self.replay(), expected)
        self.assertEqual(self.verify.call_count, 2)

    def test_artifact_refusal_stops_before_even_boot_observation(self):
        self.verify.side_effect = env.EnvironmentRefused("binding")
        command, pause = Mock(), Mock()
        with self.assertRaisesRegex(env.EnvironmentRefused, "^binding$"):
            journey.run_journey(self.pins, command, pause)
        command.assert_not_called()
        pause.assert_not_called()

    def test_existing_test_package_refuses_before_any_staging(self):
        index = self.tape.find("package-absent", 1)
        self.tape.replace_raw(index, f"package:{APP}.test uid:10002\n".encode())
        command = self.command()
        with self.assertRaisesRegex(env.EnvironmentRefused, "^packages_present$"):
            journey.run_journey(self.pins, command, Mock())
        self.assertEqual(command.call_count, index + 1)

    def test_staged_apk_digest_mismatch_refuses_before_installing(self):
        index = self.tape.find("staged-hash")
        path = TARGETS[0][2]
        self.tape.replace_raw(index, self.tape.hash_line("0" * 64, path))
        command = self.command()
        with self.assertRaisesRegex(env.EnvironmentRefused, "^checks_failed$"):
            journey.run_journey(self.pins, command, Mock())
        self.assertEqual(command.call_count, index + 1)

    def test_changed_installed_apk_between_methods_prevents_deletion_test(self):
        index = self.tape.find("package-hash", 2)
        path = self.tape.installed["product_apk"]["path"]
        self.tape.replace_raw(index, self.tape.hash_line("f" * 64, path))
        command = self.command()
        with self.assertRaisesRegex(env.EnvironmentRefused, "^checks_failed$"):
            journey.run_journey(self.pins, command, Mock())
        self.assertEqual(command.call_count, index + 1)
        labels = [entry.args[1] for entry in command.call_args_list]
        self.assertIn(KINDS[0], labels)
        self.assertNotIn(KINDS[1], labels)

    def test_changed_installed_uid_after_both_tests_refuses_the_overall_journey(self):
        index = self.tape.find("package", 4)
        self.tape.replace_raw(index, f"package:{APP} uid:10003\n".encode())
        command = self.command()
        with self.assertRaisesRegex(env.EnvironmentRefused, "^checks_failed$"):
            journey.run_journey(self.pins, command, Mock())
        self.assertEqual(command.call_count, len(self.tape.rows))
        self.assertEqual([entry.args[1] for entry in command.call_args_list if entry.args[1] in KINDS], list(KINDS))

    def test_boot_wait_is_bounded_and_never_reaches_install(self):
        command, pause = Mock(return_value=b"0\n"), Mock()
        with self.assertRaisesRegex(env.EnvironmentRefused, "^deadline$"):
            journey.run_journey(self.pins, command, pause)
        self.assertEqual(command.call_count, 61)
        self.assertEqual(pause.call_count, 60)
        self.assertTrue(all(entry.args == (["getprop", "sys.boot_completed"], "boot")
                            for entry in command.call_args_list))

    def test_replay_rejects_missing_extra_or_swapped_rows(self):
        rows = self.tape.rows
        first, second = (self.tape.find(kind) for kind in KINDS)
        swapped = list(rows)
        swapped[first], swapped[second] = swapped[second], swapped[first]
        for label, variant in (("missing", rows[:-1]), ("extra", rows + rows[-1:]), ("swapped", swapped)):
            with self.subTest(label=label), self.assertRaises(REFUSALS):
                self.replay(variant)

    def test_replay_rejects_replacement_install_or_unqualified_owner_row(self):
        index = self.tape.find("install")
        for label in ("replace", "unqualified", "timeout", "budget", "boolean_exit"):
            with self.subTest(label=label):
                rows = copy.deepcopy(self.tape.rows)
                row = rows[index]
                if label == "replace":
                    row["operation"]["argv"][2] = "-r"
                elif label == "unqualified":
                    row["client_qualified"] = False
                elif label == "timeout":
                    row["status"] = "timed_out"
                elif label == "budget":
                    row["effective_deadline_ms"] += 1
                else:
                    row["returncode"] = False
                with self.assertRaises(REFUSALS):
                    self.replay(rows)

    def test_replay_rejects_nonempty_shell_stderr_and_substituted_method_stdout(self):
        first, second = (self.tape.find(kind) for kind in KINDS)
        variants = (
            dict(stderr=self.tape.pin("synthetic stderr", b"unexpected shell stderr")),
            dict(stdout=self.tape.rows[second]["stdout"]),
        )
        for changes in variants:
            with self.subTest(changes=changes), self.assertRaises(REFUSALS):
                rows = list(self.tape.rows)
                rows[first] = dict(rows[first], **changes)
                self.replay(rows)
