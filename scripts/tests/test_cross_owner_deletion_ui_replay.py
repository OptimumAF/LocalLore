"""Synthetic replay checks for one isolated cross-owner deletion Activity test.

Copyright 2026 LocalLore contributors. SPDX-License-Identifier: Apache-2.0
"""
import copy
import hashlib
import unittest

from benchmarks import cross_owner_deletion_ui_binding as binding
from benchmarks import cross_owner_deletion_ui_replay as journey
from benchmarks import owned_target_contract as core
from scripts.tests.test_cross_owner_deletion_ui_binding import (
    APP, CLASS, KIND, METHOD, RUNNER, SELECTOR, TEST, runner_bytes,
)


TARGETS = (
    ("product_apk", APP, "/data/local/tmp/locallore-product-v1.apk", 10001),
    ("test_apk", TEST, "/data/local/tmp/locallore-test-v1.apk", 10002),
)
INSTRUMENT = [
    "am", "instrument", "-w", "-r", "-e", "class", SELECTOR, TEST + "/" + RUNNER,
]


def row(argv, stdout=b"", *, stdin=None, stderr=b""):
    return dict(argv=argv, stdin=stdin, stdout=stdout, stderr=stderr, returncode=0)


def package_query(package):
    return ["cmd", "package", "list", "packages", "-U", "--user", "0", package]


def package_path(package):
    return f"/data/app/~~synthetic/{package}-instance/base.apk"


def installed_rows(pins):
    for role, package, _, uid in TARGETS:
        path = package_path(package)
        listing = f"package:{package} uid:{uid}\n"
        if package == APP:
            listing += f"package:{TEST} uid:{TARGETS[1][3]}\n"
        yield row(package_query(package), listing.encode())
        yield row(["cmd", "package", "path", "--user", "0", package],
                  f"package:{path}\n".encode())
        yield row(["sha256sum", path], f"{pins[role]['sha256']}  {path}\n".encode())


def command_tape(pins):
    rows = [
        row(["getprop", "sys.boot_completed"], b"1\n"),
        row(["getprop", "ro.build.version.sdk"], b"35\n"),
        row(["getprop", "ro.product.cpu.abi"], b"x86_64\n"),
        row(["getprop", "ro.kernel.qemu"], b"1\n"),
        row(["am", "get-current-user"], b"0\n"),
        *[row(package_query(package)) for _, package, _, _ in TARGETS],
    ]
    for role, _, path, _ in TARGETS:
        rows.extend((
            row(["dd", "of=" + path, "bs=65536"], stdin=copy.deepcopy(pins[role]),
                stderr=b"1+0 records in\n1+0 records out\n"),
            row(["sha256sum", path], f"{pins[role]['sha256']}  {path}\n".encode()),
            row(["pm", "install", "-R", "-t", "--user", "0", path], b"Success\n"),
        ))
    rows.extend(installed_rows(pins))
    rows.append(row(INSTRUMENT.copy(), runner_bytes()))
    rows.extend(installed_rows(pins))
    return rows


class CrossOwnerDeletionUiReplayTests(unittest.TestCase):
    def setUp(self):
        self.pins = binding.artifact_bindings()
        self.rows = command_tape(self.pins)

    def assert_row_refusals(self, cases):
        for index, updates in cases:
            with self.subTest(index=index, fields=tuple(updates)):
                rows = copy.deepcopy(self.rows)
                rows[index].update(updates)
                with self.assertRaises(core.TargetRefused):
                    journey.replay(rows, self.pins)

    def test_exact_tape_verifies_without_granting_runtime_evidence(self):
        self.assertEqual(len(self.rows), 26)
        result = journey.replay(self.rows, self.pins)
        self.assertEqual(result, {
            "scope": "cross-owner-deletion-ui-replay-v1",
            "execution_authorized": False,
            "runtime_verified": False,
            "installed": {
                role: dict(package=package, uid=uid, path=package_path(package),
                           sha256=self.pins[role]["sha256"])
                for role, package, _, uid in TARGETS
            },
            "tests": [{
                "kind": KIND, "class": CLASS, "methods": [METHOD], "method_count": 1,
                "stdout_sha256": hashlib.sha256(runner_bytes()).hexdigest(), "passed": True,
            }],
        })
        self.assertEqual(self.rows, command_tape(self.pins))
        self.assertEqual(self.pins, binding.artifact_bindings())

    def test_requires_a_ready_isolated_api35_emulator_and_user_zero(self):
        self.assert_row_refusals((
            (0, {"stdout": b"0\n"}),
            (1, {"stdout": b"34\n"}),
            (2, {"stdout": b"arm64-v8a\n"}),
            (3, {"stdout": b"0\n"}),
            (4, {"stdout": b"10\n"}),
        ))

    def test_both_packages_must_be_absent_before_staging(self):
        self.assert_row_refusals((
            (5, {"stdout": f"package:{APP} uid:10001\n".encode()}),
            (6, {"stdout": f"package:{TEST} uid:10002\n".encode()}),
            (6, self.rows[7]),
        ))

    def test_artifacts_must_match_both_role_bindings_and_staged_hashes(self):
        changed = copy.deepcopy(self.pins)
        changed["product_apk"]["sha256"] = "0" * 64
        with self.assertRaises(core.TargetRefused):
            journey.replay(self.rows, changed)

        self.assert_row_refusals((
            (7, {"stdin": self.pins["test_apk"]}),
            (8, {"stdout": self.rows[8]["stdout"].replace(
                self.pins["product_apk"]["sha256"].encode(), b"0" * 64, 1)}),
            (10, {"stdin": self.pins["product_apk"]}),
            (11, {"stdout": self.rows[8]["stdout"]}),
        ))

    def test_install_requires_no_replacement_and_a_success_response(self):
        replacing = self.rows[9]["argv"].copy()
        replacing[2] = "-r"
        self.assert_row_refusals((
            (9, {"argv": replacing}),
            (9, {"stdout": b"Failure [INSTALL_FAILED_ALREADY_EXISTS]\n"}),
            (12, {"returncode": 1}),
        ))

    def test_installed_paths_and_hashes_must_belong_to_the_exact_roles(self):
        self.assert_row_refusals((
            (14, {"stdout": f"package:{package_path(TEST)}\n".encode()}),
            (15, {"stdout": b"0" * 64 + f"  {package_path(APP)}\n".encode()}),
            (17, {"stdout": f"package:{package_path(TEST)}\npackage:/data/app/split.apk\n".encode()}),
        ))

    def test_installed_uid_consistency_and_post_test_identity(self):
        later_path = package_path(APP).replace("-instance/", "-replacement/")
        rows = copy.deepcopy(self.rows)
        rows[21]["stdout"] = f"package:{later_path}\n".encode()
        rows[22] = row(["sha256sum", later_path],
                       f"{self.pins['product_apk']['sha256']}  {later_path}\n".encode())
        with self.assertRaises(core.TargetRefused):
            journey.replay(rows, self.pins)

        self.assert_row_refusals((
            (16, {"stdout": f"package:{TEST} uid:10003\n".encode()}),
            (16, {"stdout": f"package:{APP} uid:10001\npackage:{TEST} uid:10002\n".encode()}),
            (20, {"stdout": f"package:{APP} uid:10003\npackage:{TEST} uid:10002\n".encode()}),
            (13, {"stdout": f"package:{APP} uid:10001\npackage:{TEST} uid:10001\n".encode()}),
        ))

    def test_only_one_complete_matching_instrumentation_run_is_accepted(self):
        alternate = INSTRUMENT.copy()
        alternate[6] = CLASS + "#differentMethod"
        self.assert_row_refusals((
            (19, {"argv": alternate}),
            (19, {"stdout": runner_bytes()[:-1]}),
            (19, {"stdout": runner_bytes() + runner_bytes()}),
            (19, {"argv": ["am", "force-stop", "--user", "0", APP]}),
        ))
        with self.assertRaises(core.TargetRefused):
            journey.replay(self.rows + [self.rows[19]], self.pins)

    def test_tape_schema_and_output_channels_are_strict(self):
        self.assert_row_refusals((
            (0, {"extra": True}),
            (1, {"stdout": "35\n"}),
            (13, {"stdout": b"\xff"}),
            (15, {"stderr": b"unexpected\n"}),
            (19, {"returncode": False}),
        ))
        for invalid in (tuple(self.rows), self.rows[:-1]):
            with self.assertRaises(core.TargetRefused):
                journey.replay(invalid, self.pins)
