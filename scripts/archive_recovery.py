"""Opt-in synthetic Android archive force-stop/relaunch proof. Never installs or clears apps.

Copyright 2026 LocalLore contributors. SPDX-License-Identifier: Apache-2.0
"""
import argparse
from concurrent.futures import ThreadPoolExecutor, TimeoutError as FutureTimeout
import json
import os
from pathlib import Path
import re
import threading
import time
import uuid

import platform_roundtrip as common

Failure, require = common.Failure, common.require
PACKAGE, TEST_PACKAGE = common.PACKAGE, common.TEST_PACKAGE
TEST_CLASS = "org.locallore.app.ArchiveRecoveryActivityTest"
TEST_METHOD = "processRecovery"
MARKER = b"locallore-archive-recovery-v1"
FILES = {"owner-v1", "archive.json", "ready-v1.json", "verified-v1.json"}
FIELDS = {"version", "run", "phase", "pid", "archive_sha256", "status"}


class OwnedDevice(common.android.Device):
    """One live, owned arm client may coexist with bounded read/control clients."""
    def __init__(self, adb, serial, journal):
        super().__init__(adb, serial)
        self.clients_cleaned = True
        self.lock = threading.Lock()
        self.journal = journal

    def raw(self, args, request=b"", deadline=20, cancel=None):
        with self.lock:
            require(self.clients_cleaned, "client_cleanup_unknown")
        result = super().raw(args, request, deadline, cancel)
        # Publish cleanup before fallible logging, and never let a concurrent
        # successful observation erase another client's unknown cleanup.
        with self.lock:
            self.clients_cleaned = self.clients_cleaned and result.cleanup_complete is True
        self.journal("adb", status=result.status, exit_code=result.returncode,
                     stdout_bytes=len(result.stdout), stderr_bytes=result.stderr_bytes,
                     cleanup=result.cleanup_complete)
        return result


def remote_path(run, name):
    require(isinstance(run, str) and re.fullmatch(r"[a-z0-9-]{1,48}", run), "invalid_run")
    require(name in FILES, "invalid_remote_file")
    return "no_backup/archive-recovery/" + run + "/" + name


def remote_optional(device, run, name):
    path = remote_path(run, name)
    command = ("[ ! -L " + path + " ] && if [ -e " + path + " ]; then [ -f " + path +
               " ] && [ \"$(stat -c %s " + path + ")\" -le 131072 ] && cat " + path + "; fi")
    data = device.shell("run-as", PACKAGE, "/system/bin/sh", "-c", command)
    require(len(data) <= 131072, "remote_size")
    return data or None


def absent_run(device, run):
    path = remote_path(run, "owner-v1").rsplit("/", 1)[0]
    device.shell("run-as", PACKAGE, "/system/bin/sh", "-c",
                 "[ ! -e " + path + " ] && [ ! -L " + path + " ]")


def unique_object(pairs):
    result = {}
    for key, value in pairs:
        require(key not in result, "marker_duplicate_key")
        result[key] = value
    return result


def parse_record(data, run, phase, status):
    require(isinstance(data, bytes) and 0 < len(data) <= 4096, "marker_size")
    try:
        value = json.loads(data.decode("utf-8", errors="strict"), object_pairs_hook=unique_object)
    except (UnicodeError, ValueError, RecursionError):
        raise Failure("marker_json") from None
    require(isinstance(value, dict) and set(value) == FIELDS, "marker_fields")
    require(type(value["version"]) is int and value["version"] == 1 and value["run"] == run
            and value["phase"] == phase and value["status"] == status, "marker_binding")
    require(type(value["pid"]) is int and 1 <= value["pid"] <= 2147483647, "marker_pid")
    require(isinstance(value["archive_sha256"], str) and
            re.fullmatch(r"[0-9a-f]{64}", value["archive_sha256"]), "marker_hash")
    return value


def package_pid(device):
    rows = device.shell("ps", "-A", "-o", "PID,NAME").decode("ascii", errors="strict").splitlines()
    require(rows and rows[0].split() == ["PID", "NAME"], "process_inventory")
    pids = []
    for row in rows[1:]:
        fields = row.split()
        require(len(fields) == 2 and fields[0].isdigit(), "process_inventory")
        if fields[1] == PACKAGE:
            pids.append(int(fields[0]))
    require(len(pids) <= 1, "process_inventory")
    return pids[0] if pids else None


def await_ready(device, future, run, phase, timeout=40):
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        require(not future.done(), "arm_ended_before_interruption")
        data = remote_optional(device, run, "ready-v1.json")
        if data:
            try:
                record = parse_record(data, run, phase, "ready")
            except Failure as failure:
                # A create-new marker can be observed during its small write.
                # Partial JSON never authorizes a process mutation.
                if failure.category != "marker_json":
                    raise
            else:
                require(remote_optional(device, run, "owner-v1") == MARKER, "remote_owner")
                archive = remote_optional(device, run, "archive.json")
                require(archive and common.digest(archive) == record["archive_sha256"], "source_hash")
                require(package_pid(device) == record["pid"], "live_pid_mismatch")
                require(not future.done(), "arm_ended_before_interruption")
                return record, data
        time.sleep(.05)
    raise Failure("ready_deadline")


def interrupt_live_arm(device, future, record, identities, journal):
    require(not future.done(), "arm_ended_before_interruption")
    for package in (PACKAGE, TEST_PACKAGE):
        require(common.installed_hash(device, package) == identities[package], "owned_package_changed")
    require(package_pid(device) == record["pid"], "live_pid_mismatch")
    require(not future.done(), "arm_ended_before_interruption")
    journal("interrupt_requested", live_pid_confirmed=True, arm_client_live=True)
    # The exact verified app is deliberately terminated; the test/provider
    # package is drained separately after the owned arm client returns.
    device.shell("am", "force-stop", PACKAGE)
    require(package_pid(device) is None, "target_process_survived")
    journal("target_process_absent", confirmed=True)


def parse_transcript(data, interrupted=False, expected_class=TEST_CLASS, expected_method=TEST_METHOD):
    try:
        text = data.decode("utf-8", errors="strict")
    except UnicodeError:
        raise Failure("instrumentation_encoding") from None
    fields, starts, terminals, runners = {}, [], [], []
    for line in text.splitlines():
        if line.startswith("INSTRUMENTATION_STATUS: "):
            key, sep, value = line[len("INSTRUMENTATION_STATUS: "):].partition("=")
            require(sep and key not in fields, "instrumentation_fields")
            fields[key] = value
        elif line.startswith("INSTRUMENTATION_STATUS_CODE: "):
            code = line.partition(": ")[2]
            require(fields.get("class") == expected_class and fields.get("test") == expected_method
                    and fields.get("numtests") == "1", "instrumentation_inventory")
            if code == "1":
                require(not starts and not terminals and not runners, "instrumentation_order")
                starts.append(code)
            else:
                require(starts == ["1"] and not terminals and not runners, "instrumentation_order")
                terminals.append(code)
            fields = {}
        elif line.startswith("INSTRUMENTATION_CODE:"):
            require(starts == ["1"] and not fields and not runners and
                    (interrupted or terminals == ["0"]), "instrumentation_order")
            runners.append(line.partition(": ")[2])
    require(starts == ["1"] and not fields, "instrumentation_start")
    if interrupted:
        require(not terminals and runners == ["0"] and
                "INSTRUMENTATION_RESULT: shortMsg=Process crashed." in text and
                "OK (" not in text and "FAILURES!!!" not in text,
                "arm_unexpected_terminal")
        # Interruption is established by the independently observed live marker,
        # PID and targeted stop, not by treating a runner crash as a passing test.
        return {"started": 1, "passed": 0, "intentional_interruptions": 1,
                "test_terminal_received": False}
    require(terminals == ["0"] and runners == ["-1"] and
            "OK (1 test)" in text and not any(token in text for token in
            ("FAILURES!!!", "INSTRUMENTATION_FAILED", "Process crashed", "shortMsg=")),
            "instrumentation_failed")
    return {"started": 1, "passed": 1, "failed": 0, "skipped": 0, "unfinished": 0}


def instrument(device, phase, run, cancel=None):
    require(phase in ("arm-preview", "verify-preview", "arm-committed", "verify-committed"), "invalid_phase")
    remote_path(run, "owner-v1")
    return device.raw(["shell", "am instrument -w -r -e class " + TEST_CLASS + "#" + TEST_METHOD +
        " -e archive_recovery_phase " + phase + " -e archive_recovery_run " + run + " " +
        TEST_PACKAGE + "/androidx.test.runner.AndroidJUnitRunner"], deadline=160, cancel=cancel)


def exercise_case(device, mode, output, identities, journal, progress=None):
    require(mode in ("preview", "committed"), "invalid_mode")
    progress = progress if progress is not None else {}
    progress.update(status="failed", stage="arming", interruption_confirmed=False)
    run = "recovery-" + uuid.uuid4().hex
    absent_run(device, run)
    cancel = threading.Event()
    record = None
    with ThreadPoolExecutor(max_workers=1) as pool:
        future = pool.submit(instrument, device, "arm-" + mode, run, cancel)
        try:
            record, raw_record = await_ready(device, future, run, "arm-" + mode)
            common.write_new(output / (mode + "-ready.json"), raw_record)
            interrupt_live_arm(device, future, record, identities, journal)
            progress.update(stage="draining_arm", interruption_confirmed=True)
            attempted = future.result(timeout=20)
            common.write_new(output / (mode + "-arm.raw.txt"), attempted.stdout)
            common.require_process(attempted)
            arm = {**parse_transcript(attempted.stdout, interrupted=True),
                   "raw_sha256": common.digest(attempted.stdout)}
            progress["arm"] = arm
        except FutureTimeout:
            raise Failure("arm_client_drain") from None
        finally:
            # Cancels only our owned ADB client. No new device command follows
            # until its process owner has confirmed cleanup.
            cancel.set()
            try:
                pending = future.result(timeout=30)
                if not (output / (mode + "-arm.raw.txt")).exists():
                    common.write_new(output / (mode + "-arm.raw.txt"), pending.stdout)
            except FutureTimeout:
                raise Failure("arm_client_cleanup_unknown") from None
    common.stop_owned(device, identities)
    progress["stage"] = "verifying_relaunch"
    attempted = instrument(device, "verify-" + mode, run)
    common.write_new(output / (mode + "-verify.raw.txt"), attempted.stdout)
    common.require_process(attempted)
    verify = {**parse_transcript(attempted.stdout), "raw_sha256": common.digest(attempted.stdout)}
    progress["relaunch"] = verify
    require(remote_optional(device, run, "owner-v1") == MARKER, "remote_owner")
    raw = remote_optional(device, run, "verified-v1.json")
    verified = parse_record(raw, run, "verify-" + mode, "verified")
    require(record["pid"] != verified["pid"] and record["archive_sha256"] == verified["archive_sha256"],
            "relaunch_binding")
    common.write_new(output / (mode + "-verified.json"), raw)
    common.stop_owned(device, identities)
    progress.update(status="passed", stage="verified", archive_sha256=record["archive_sha256"],
                    different_process_confirmed=True)
    return progress


def run(args):
    require(re.fullmatch(r"[A-Za-z0-9_-]{1,24}", args.alias), "invalid_alias")
    output = common.fresh_directory(args.output_directory)
    result = {"version": 1, "scope": "synthetic_android_archive_force_stop", "target_alias": args.alias,
              "status": "failed", "cases": {}}
    device, identities, before = None, None, None
    owned_verified = False
    tool_cleaned = True
    lock = threading.Lock()
    with (output / "commands.jsonl").open("x", encoding="utf-8", newline="\n") as log:
        def journal(event, **fields):
            nonlocal tool_cleaned
            if event == "tool":
                tool_cleaned = tool_cleaned and fields.get("cleanup") is True
            with lock:
                log.write(json.dumps({"event": event, **fields}) + "\n")
                log.flush()
                os.fsync(log.fileno())
        try:
            app, test = common.real_path(args.app_apk), common.real_path(args.test_apk)
            identities = {PACKAGE: common.digest(app.read_bytes()), TEST_PACKAGE: common.digest(test.read_bytes())}
            result["apk_sha256"] = identities
            aapt = Path(args.adb).parent.parent / "build-tools/35.0.0/aapt2.exe"
            if os.name != "nt":
                aapt = aapt.with_name("aapt2")
            for apk, package in ((app, PACKAGE), (test, TEST_PACKAGE)):
                attempted = common.process_owner.run_process([str(aapt), "dump", "badging", str(apk)], deadline=20)
                journal("tool", status=attempted.status, cleanup=attempted.cleanup_complete)
                badging = common.require_process(attempted)
                require(badging.splitlines() and badging.splitlines()[0].startswith(
                        ("package: name='" + package + "' ").encode()), "apk_package")
            device = OwnedDevice(common.real_path(args.adb), args.serial, journal)
            require(device.shell("getprop", "sys.boot_completed").strip() == b"1", "device_not_booted")
            result["android_api"] = int(device.shell("getprop", "ro.build.version.sdk").strip())
            result["abi"] = device.shell("getprop", "ro.product.cpu.abi").decode("ascii").strip()
            before = common.protected_packages(device)
            require(all(before.get(package) == value for package, value in identities.items()),
                    "installed_artifact_mismatch")
            owned_verified = True
            common.stop_owned(device, identities)
            for mode in ("preview", "committed"):
                result["cases"][mode] = {"status": "failed"}
                result["cases"][mode] = exercise_case(device, mode, output, identities, journal,
                                                      result["cases"][mode])
            result["status"] = "passed"
        except Failure as failure:
            result["failure"] = failure.category
        except common.android.Failure:
            result["failure"] = "device_command_failed"
        except (OSError, ValueError, TypeError, KeyError, RuntimeError):
            result["failure"] = "host_io_or_format"
        finally:
            if device is not None:
                result["adb_clients_cleaned"] = device.clients_cleaned
                if device.clients_cleaned and tool_cleaned and owned_verified:
                    try:
                        common.stop_owned(device, identities)
                        result["owned_processes_absent"] = True
                        result["prior_packages_preserved"] = common.protected_packages(device) == before
                    except (Failure, common.android.Failure, OSError, ValueError):
                        result["cleanup_failure"] = "owned_cleanup_or_identity"
                result["adb_clients_cleaned"] = device.clients_cleaned
            result["tool_clients_cleaned"] = tool_cleaned
            if not tool_cleaned or not all(result.get(key) is True for key in
                    ("adb_clients_cleaned", "owned_processes_absent", "prior_packages_preserved")):
                result["status"] = "failed"
            common.write_new(output / "result.json", (json.dumps(result, indent=2) + "\n").encode("utf-8"))
    return result


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ("serial", "alias", "adb", "app-apk", "test-apk", "output-directory"):
        parser.add_argument("--" + name, required=True, type=str if name in ("serial", "alias") else Path)
    args = parser.parse_args(argv)
    try:
        result = run(args)
        print(json.dumps({key: result[key] for key in ("version", "target_alias", "status")}))
        return 0 if result["status"] == "passed" else 1
    except (Failure, OSError, ValueError):
        print('{"version":1,"status":"refused"}')
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
