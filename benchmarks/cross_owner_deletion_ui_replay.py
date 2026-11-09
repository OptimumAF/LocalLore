"""Verify a bounded story-deletion command tape without executing it.

The caller must qualify the owner, transport and raw command records separately.
Copyright 2026 LocalLore contributors. SPDX-License-Identifier: Apache-2.0
"""
import re

from benchmarks import android_instrumentation_evidence as evidence
from benchmarks import cross_owner_deletion_ui_binding as binding
from benchmarks import owned_target_contract as core

SCOPE = "cross-owner-deletion-ui-replay-v1"
COMMAND_COUNT = 26
TARGETS = (
    ("product_apk", binding.APP, "/data/local/tmp/locallore-product-v1.apk"),
    ("test_apk", binding.TEST, "/data/local/tmp/locallore-test-v1.apk"),
)
_ROW_KEYS = ("argv", "stdin", "stdout", "stderr", "returncode")
_MAX_REPLY = 131_072


def _lines(raw):
    return raw.decode("ascii").replace("\r\n", "\n").removesuffix("\n").split("\n")


def _line(raw):
    lines = _lines(raw)
    core._need(len(lines) == 1, "observation")
    return lines[0]


def _package_query(package):
    return ["cmd", "package", "list", "packages", "-U", "--user", "0", package]


def _package_uids(raw, package):
    allowed = (binding.APP, binding.TEST) if package == binding.APP else (binding.TEST,)
    listing = {}
    for line in _lines(raw):
        match = re.fullmatch(r"package:([^\s]+) uid:([1-9][0-9]{0,9})", line)
        core._need(match is not None and match[1] in allowed
                   and match[1] not in listing, "identity")
        uid = int(match[2])
        core._int(uid, 10_000, 2_147_483_647, "identity")
        listing[match[1]] = uid
    core._need(package in listing, "identity")
    return listing


def _installed(read, pins):
    installed = {}
    observed_uids = {}
    for role, package, _ in TARGETS:
        listing = _package_uids(read(_package_query(package), "package"), package)
        for name, uid in listing.items():
            core._need(observed_uids.setdefault(name, uid) == uid, "identity")
        line = _line(read(["cmd", "package", "path", "--user", "0", package], "package-path"))
        pattern = (r"package:/data/app/(?:~~[A-Za-z0-9_=-]+/)?"
                   + re.escape(package) + r"-[A-Za-z0-9_~=-]+/base\.apk")
        core._need(re.fullmatch(pattern, line) is not None, "identity")
        path = line.removeprefix("package:")
        digest = pins[role]["sha256"]
        core._need(_line(read(["sha256sum", path], "package-hash")) == digest + "  " + path, "binding")
        installed[role] = dict(package=package, uid=listing[package], path=path, sha256=digest)
    core._need(len(set(observed_uids.values())) == len(TARGETS), "identity")
    return installed


def _journey(read, pins):
    """Run or replay the fixed sequence, checking each reply before continuing."""
    expected = binding.artifact_bindings()
    core._need(core._same(pins, expected), "binding")
    try:
        core._need(_line(read(["getprop", "sys.boot_completed"], "boot")) == "1", "environment")
        for prop, value in (("ro.build.version.sdk", "35"), ("ro.product.cpu.abi", "x86_64"),
                            ("ro.kernel.qemu", "1")):
            core._need(_line(read(["getprop", prop], "property")) == value, "environment")
        core._need(_line(read(["am", "get-current-user"], "user")) == "0", "identity")

        # Prove both absences before the first staged write or install.
        for _, package, _ in TARGETS:
            core._need(read(_package_query(package), "package-absent") == b"", "identity")
        for role, _, path in TARGETS:
            pin = expected[role]
            core._need(read(["dd", "of=" + path, "bs=65536"], "apk-stage", source=pin) == b"", "observation")
            core._need(_line(read(["sha256sum", path], "staged-hash")) == pin["sha256"] + "  " + path, "binding")
            core._need(_line(read(["pm", "install", "-R", "-t", "--user", "0", path], "install"))
                       == "Success", "observation")

        before = _installed(read, expected)
        kind, _, _ = binding.INSTRUMENTATIONS[0]
        raw = read(binding.instrumentation_argv(kind), kind, limit=evidence.MAX_BYTES)
        result = binding.validate_result(kind, raw)
        core._need(core._same(before, _installed(read, expected)), "identity")
    except (UnicodeError, evidence.EvidenceRefused):
        raise core.TargetRefused("observation") from None
    return {"scope": SCOPE, "execution_authorized": False, "runtime_verified": False,
            "installed": before, "tests": [dict(kind=kind, **result)]}


def replay(rows, pins):
    """Check the exact command order and replies, independently of run authority."""
    expected = binding.artifact_bindings()
    core._need(core._same(pins, expected), "binding")
    core._need(type(rows) is list and len(rows) == COMMAND_COUNT, "schema")
    tape = iter(rows)

    def read(argv, _label, *, source=None, limit=_MAX_REPLY):
        row = next(tape)
        core._obj(row, _ROW_KEYS, "schema")
        core._need(core._same(row["argv"], argv), "capability")
        core._need(core._same(row["stdin"], source), "binding")
        stdout, stderr = row["stdout"], row["stderr"]
        core._need(core._same(row["returncode"], 0)
                   and type(stdout) is bytes and len(stdout) <= limit
                   and type(stderr) is bytes and len(stderr) <= limit
                   and (source is not None or stderr == b""), "observation")
        return stdout

    return _journey(read, pins)
