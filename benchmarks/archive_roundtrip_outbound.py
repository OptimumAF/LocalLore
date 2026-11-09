"""Ordered SDK25 outbound capture and closed replay for the archive cohort.

Copyright 2026 LocalLore contributors. SPDX-License-Identifier: Apache-2.0
"""
import hashlib
from pathlib import Path, PureWindowsPath
import re
import time

from benchmarks import android_instrumentation_evidence as instrumentation
from benchmarks import owned_archive_roundtrip_client as client
from benchmarks import owned_archive_roundtrip_contract as contract
from benchmarks import owned_archive_roundtrip_owner as owner

BOOT_READS = 60
BOOT_SECONDS = 120
SETUP_CAP = 4096
# The fixed roster after boot contains 29 commands. Boot reads are the only
# variable prefix. Transfer and package mutations never retry.
FIXED_COMMANDS = 29
OUTPUT = contract.TRANSFER_OUTPUT
PACKAGES = (contract.APP, contract.TEST)


class OutboundRefused(ValueError):
    """A fixed phase refusal with no raw evidence or local paths."""


def _need(condition, reason):
    if not condition:
        raise OutboundRefused(reason)


def _package_list(package):
    return ["cmd", "package", "list", "packages", "-U", "--user", "0", package]


def _lines(raw, reason):
    try:
        text = raw.decode("ascii")
    except UnicodeError:
        raise OutboundRefused(reason) from None
    # Accept LF or CRLF, without accepting vertical whitespace or blank rows.
    text = text.replace("\r\n", "\n")
    _need(all(ch == "\n" or 32 <= ord(ch) <= 126 for ch in text), reason)
    if text.endswith("\n"):
        text = text[:-1]
    return text.split("\n") if text else []


def _line(raw, reason):
    lines = _lines(raw, reason)
    _need(len(lines) == 1, reason)
    return lines[0]


def _uids(raw, package):
    seen = {}
    for row in _lines(raw, "package_identity"):
        match = re.fullmatch(r"package:([^ ]+) uid:([1-9][0-9]{0,9})", row)
        _need(match is not None and match[1] in PACKAGES and match[1] not in seen,
              "package_identity")
        uid = int(match[2])
        _need(10000 <= uid <= 99999, "package_identity")
        seen[match[1]] = uid
    # The product prefix can list the test package too. A test-prefix
    # query must not report the product or any unrelated package.
    _need(package in seen and (package == contract.APP or set(seen) == {package}),
          "package_identity")
    return seen


def _installed(admission, command):
    installed = {}
    listed_test_uid = None
    for role, package in zip(contract.ROLES, PACKAGES, strict=True):
        listed = _uids(command(_package_list(package), "installed-uid"), package)
        uid = listed[package]
        if package == contract.APP:
            listed_test_uid = listed.get(contract.TEST)
        elif listed_test_uid is not None:
            _need(uid == listed_test_uid, "package_identity")
        raw = command(["cmd", "package", "path", "--user", "0", package], "installed-path")
        line = _line(raw, "package_identity")
        expression = (r"package:/data/app/(?:~~[A-Za-z0-9_=-]+/)?"
                      + re.escape(package) + r"-[A-Za-z0-9_~=-]+/base\.apk")
        _need(re.fullmatch(expression, line) is not None, "package_identity")
        path = line.removeprefix("package:")
        digest = admission["artifacts"][role]["sha256"]
        raw = command(["sha256sum", path], "installed-sha")
        _need(_line(raw, "package_identity") == digest + "  " + path, "package_identity")
        installed[role] = {"uid": uid, "path": path, "sha256": digest}
    _need(len({entry["uid"] for entry in installed.values()}) == 2, "package_identity")
    return installed


def _sequence(admission, command, wait_for_boot):
    for index in range(BOOT_READS):
        raw = command(["getprop", "sys.boot_completed"], "boot")
        state = "" if raw in (b"", b"\n", b"\r\n") else _line(raw, "boot")
        _need(state in ("", "0", "1"), "boot")
        if state == "1":
            break
        if index + 1 < BOOT_READS:
            wait_for_boot()
    else:
        raise OutboundRefused("boot")

    for prop, expected in (("ro.build.version.sdk", "35"),
                           ("ro.product.cpu.abi", "x86_64"),
                           ("ro.kernel.qemu", "1")):
        _need(_line(command(["getprop", prop], "target"), "target") == expected, "target")
    _need(_line(command(["am", "get-current-user"], "user"), "target") == "0", "target")
    for package in PACKAGES:
        _need(command(_package_list(package), "package-absent") == b"", "package_present")

    for role in contract.ROLES:
        pin = admission["artifacts"][role]
        path = contract.staged_path(admission, role)
        _need(command(contract.stage_argv(admission, role), "apk-stage", source=pin, seconds=120)
              == b"", "apk_stage")
        raw = command(["sha256sum", path], "apk-sha")
        _need(_line(raw, "apk_stage") == pin["sha256"] + "  " + path, "apk_stage")
        raw = command(contract.install_argv(admission, role), "apk-install", seconds=120)
        _need(_line(raw, "apk_install") == "Success", "apk_install")

    before = _installed(admission, command)
    raw = command(contract.outbound_argv(admission), contract.OUTBOUND, seconds=120,
                  cap=contract.MAX_BYTES)
    class_name, method = contract.SELECTOR.split("#")
    terminal = instrumentation.validate_instrumentation(raw, class_name, [method])

    marker = command(contract.read_argv(admission, "owner-v1"), "owner-marker")
    _need(marker == contract.MARKER, "owner_marker")
    files = {}
    for leaf in contract.FILES[1:]:
        raw = command(contract.read_argv(admission, leaf), "archive-read", cap=contract.MAX_BYTES)
        _need(0 < len(raw) <= contract.MAX_BYTES, "archive_size")
        if leaf != "android-origin.json":
            role = "windows_origin" if leaf == "windows-return.json" else "windows_continued"
            pin = admission["artifacts"][role]
            _need(len(raw) == pin["bytes"] and hashlib.sha256(raw).hexdigest() == pin["sha256"],
                  "windows_archive_drift")
        files[leaf] = raw
    _need(_installed(admission, command) == before, "package_drift")
    return {"installed": before, "instrumentation": terminal, "files": files}


def _session(admission, session_binding):
    verifier = owner.VERIFIER
    root = PureWindowsPath(admission["root"]) / OUTPUT
    contract.binding(session_binding, max_bytes=2 * 1024 * 1024)
    _need(PureWindowsPath(session_binding["path"]) == root / contract.SESSION_FILE, "session")
    session = contract.validate_session(verifier._json(session_binding), admission)
    _need(PureWindowsPath(session["root"]) == root and
          verifier._pin(Path(session_binding["path"])) == session_binding, "session")
    return session


class _Commands:
    def __init__(self, admission, session, count, capture=None, boot_deadline=None, *, start=0):
        self.admission = admission
        self.session = session
        self.limit = count
        self.capture = capture
        self.boot_deadline = boot_deadline
        self.records = []
        self.start = start

    def _capture_command(self, argv, label, source, seconds, cap):
        if source is None:
            return self.capture.shell(argv, label, seconds=seconds, cap=cap)
        return self.capture.stream(argv, source, label, seconds=seconds, cap=cap)

    def __call__(self, argv, label, *, source=None, seconds=15, cap=SETUP_CAP):
        index = self.start + len(self.records) + 1
        _need(index <= self.limit, "command_count")
        operation = {"argv": argv, "stdin": source}
        contract.validate_operation(operation, self.admission)
        captured = None
        if self.capture is not None:
            _need(self.capture.count == index - 1, "command_count")
            live_seconds = seconds
            if label == "boot":
                remaining = self.boot_deadline - time.monotonic()
                _need(remaining > 0, "boot")
                live_seconds = min(seconds, remaining)
            captured = self._capture_command(argv, label, source, live_seconds, cap)
            _need(self.capture.count == index, "command_count")
        verifier = owner.VERIFIER
        pin = verifier._pin(Path(self.session["root"]) / "clients" / f"command-{index:04d}.json")
        record = verifier.verify_client_record(pin, self.session, self.admission)
        _need(record["index"] == index and record["label"] == label and
              contract._same(record["operation"], operation) and
              record["effective_deadline_ms"] <= seconds * 1000 and
              record["stdout"]["bytes"] <= cap and record["stderr"]["bytes"] == 0,
              "command_evidence")
        stdout = verifier._raw(record["stdout"], cap=cap)
        _need(captured is None or captured == stdout, "command_evidence")
        if self.capture is not None and label == "boot":
            _need(time.monotonic() < self.boot_deadline, "boot")
        self.records.append(pin)
        return stdout


def run(capture):
    """Consume a fresh SDK25 client and verify the outbound evidence as it arrives."""
    _need(type(capture) is client.OwnedArchiveRoundtripSdkCapture and
          capture.clean is True and capture.count == 0, "client_type")
    try:
        admission = contract.validate_admission(capture.lease.admission)
        session_binding = capture.session_binding
        session = _session(admission, session_binding)
        _need(contract._same(session, capture.session), "session")
        boot_deadline = time.monotonic() + BOOT_SECONDS
        commands = _Commands(admission, session, BOOT_READS + FIXED_COMMANDS, capture, boot_deadline)

        def wait_for_boot():
            _need(time.monotonic() + 2 < boot_deadline, "boot")
            time.sleep(2)

        result = _sequence(admission, commands, wait_for_boot)
        _need(capture.count == len(commands.records), "command_count")
        return dict(result, session=session_binding, records=tuple(commands.records))
    except BaseException:
        capture.close()
        raise


def replay_prefix(admission, session_binding, count):
    """Recheck exactly the outbound prefix even when later records exist."""
    admission = contract.validate_admission(admission)
    _need(type(count) is int and FIXED_COMMANDS + 1 <= count <= FIXED_COMMANDS + BOOT_READS,
          "command_count")
    session = _session(admission, session_binding)
    commands = _Commands(admission, session, count)
    result = _sequence(admission, commands, lambda: None)
    _need(len(commands.records) == count, "command_count")
    return dict(result, session=session_binding, records=tuple(commands.records))
