"""Install and replay the fixed storage-opener journey through an owned command port.

The port owns guest admission, raw bindings and command qualification. This
module does not start an owner or access a guest on its own.

Copyright 2026 LocalLore contributors. SPDX-License-Identifier: Apache-2.0
"""
from benchmarks import combined_record_ui_controller as owner_checks
from benchmarks import owned_target_contract as core
from benchmarks import receipt_avd_environment as env
from benchmarks import storage_opener_capture as capture

MAX_BOOT_POLLS = owner_checks.MAX_BOOT_POLLS
COMMANDS_AFTER_BOOT = 32
_ROW_FIELDS = frozenset(("index", "effective_deadline_ms", "label", "operation",
                         "client_qualified", "status", "returncode", "stdout", "stderr"))


def run_journey(pins, command, pause):
    """Run the fixed sequence with an already admitted, bounded owner port."""
    capture.verify_artifacts(pins)
    artifacts = capture.artifact_bindings()
    line = owner_checks._line
    package_query = owner_checks._package_query
    for index in range(MAX_BOOT_POLLS):
        raw = command(["getprop", "sys.boot_completed"], "boot")
        state = "" if raw == b"" else line(raw)
        env.require(state in ("", "0", "1"), "checks_failed")
        if state == "1":
            break
        env.require(index + 1 < MAX_BOOT_POLLS, "deadline")
        pause()

    for prop, expected in (("ro.build.version.sdk", "35"), ("ro.product.cpu.abi", "x86_64"),
                           ("ro.kernel.qemu", "1")):
        env.require(line(command(["getprop", prop], "property")) == expected, "checks_failed")
    env.require(line(command(["am", "get-current-user"], "user")) == "0", "checks_failed")
    for _, package, _ in owner_checks.TARGETS:
        env.require(command(package_query(package), "package-absent") == b"", "packages_present")

    for role, _, path in owner_checks.TARGETS:
        source = artifacts[role]
        env.require(command(["dd", "of=" + path, "bs=65536"], "apk-stage", source=source,
                            seconds=120) == b"", "checks_failed")
        expected = source["sha256"] + "  " + path
        env.require(line(command(["sha256sum", path], "staged-hash")) == expected, "checks_failed")
        env.require(line(command(["pm", "install", "-R", "-t", "--user", "0", path], "install",
                                 seconds=120)) == "Success", "checks_failed")

    installed = owner_checks._installed(command, artifacts)

    def instrument(argv, kind, *, seconds, limit):
        if kind != capture.KINDS[0]:
            env.require(core._same(installed, owner_checks._installed(command, artifacts)), "checks_failed")
        return command(argv, kind, seconds=seconds, limit=limit)

    tests = capture.capture_tests(artifacts, instrument)
    env.require(core._same(installed, owner_checks._installed(command, artifacts)), "checks_failed")
    return {"installed": installed, "tests": tests}


def replay_journey(pins, rows, read_raw):
    """Re-run the sequence against owner-qualified rows and bounded raw reads.

    The owner verifies each row's session and binding before calling here.
    read_raw must verify the supplied raw pin when reading stdout or stderr.
    """
    env.require(type(rows) is list and
                1 + COMMANDS_AFTER_BOOT <= len(rows) <= MAX_BOOT_POLLS + COMMANDS_AFTER_BOOT, "binding")
    index = 0

    def command(argv, label, *, source=None, seconds=15, limit=131072):
        nonlocal index
        env.require(index < len(rows), "binding")
        row = rows[index]
        index += 1
        env.require(type(row) is dict and _ROW_FIELDS <= row.keys(), "binding")
        owner_checks._check_command(row, index, argv, label, source, seconds)
        stderr = read_raw(row["stderr"], cap=limit)
        stdout = read_raw(row["stdout"], cap=limit)
        env.require(type(stderr) is bytes and type(stdout) is bytes and
                    len(stderr) <= limit and len(stdout) <= limit and
                    (source is not None or stderr == b""), "checks_failed")
        return stdout

    result = run_journey(pins, command, lambda: None)
    env.require(index == len(rows), "binding")
    return result
