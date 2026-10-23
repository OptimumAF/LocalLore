"""Explicit synthetic SQLite-page-limit archive proof. Never installs, clears or fills a device.

Copyright 2026 LocalLore contributors. SPDX-License-Identifier: Apache-2.0
"""
import argparse
import json
import os
from pathlib import Path
import re
import uuid

import archive_recovery as ownership
import platform_roundtrip as common

PACKAGE = "org.locallore.app.archivecapacity"
TEST_PACKAGE = PACKAGE + ".test"
TEST_CLASS = "org.locallore.app.ArchiveCapacityActivityTest"
TEST_METHOD = "storageFullThenCacheReliefAndFreshImport"
MARKER = b"locallore-archive-capacity-v1"
FIELDS = {"version", "run", "status", "archive_sha256", "source_revision",
          "continued_revision", "full_count", "cache_only_relief"}
require, Failure = common.require, common.Failure


def remote_path(run, name):
    require(isinstance(run, str) and re.fullmatch(r"[a-z0-9-]{1,48}", run), "invalid_run")
    require(name in ("owner-v1", "archive.json", "capacity-verified.json"), "invalid_remote_file")
    return "no_backup/archive-capacity/" + run + "/" + name


def read_remote(device, run, name):
    path = remote_path(run, name)
    limit = 131072 if name == "archive.json" else 4096
    command = ("[ ! -L " + path + " ] && [ -f " + path + " ] && "
               "[ \"$(stat -c %s " + path + ")\" -le " + str(limit) + " ] && cat " + path)
    value = device.shell("run-as", PACKAGE, "/system/bin/sh", "-c", command)
    require(0 < len(value) <= limit, "remote_size")
    return value


def record(data, run, source):
    require(isinstance(data, bytes) and 0 < len(data) <= 4096, "record_size")
    try:
        value = json.loads(data.decode("utf-8", errors="strict"), object_pairs_hook=ownership.unique_object)
    except (UnicodeError, ValueError, RecursionError):
        raise Failure("record_json") from None
    require(isinstance(value, dict) and set(value) == FIELDS, "record_fields")
    require(type(value["version"]) is int and value["version"] == 1 and
            value["run"] == run and value["status"] == "verified", "record_binding")
    require(value["archive_sha256"] == common.digest(source), "record_source")
    require(type(value["source_revision"]) is int and value["source_revision"] == 2 and
            type(value["continued_revision"]) is int and value["continued_revision"] == 3 and
            type(value["full_count"]) is int and value["full_count"] == 1 and
            value["cache_only_relief"] is True, "record_checks")
    return value


def snapshot(device):
    listing = device.shell("pm", "list", "packages", "org.locallore.").decode("ascii", errors="strict")
    names = []
    for line in listing.splitlines():
        require(line.startswith("package:org.locallore."), "package_inventory")
        names.append(line[len("package:"):])
    require(len(names) == len(set(names)) and PACKAGE in names and TEST_PACKAGE in names, "package_inventory")
    return {name: common.installed_hash(device, name) for name in sorted(names)}


def stop_owned(device, identities):
    # Verify BOTH identities before either mutation. Every call is gated by sticky client cleanup.
    require(set(identities) == {PACKAGE, TEST_PACKAGE}, "owned_inventory")
    for package, expected in identities.items():
        require(common.installed_hash(device, package) == expected, "owned_package_changed")
    for package in identities:
        device.shell("am", "force-stop", package)
    rows = device.shell("ps", "-A", "-o", "NAME").decode("ascii", errors="strict").splitlines()
    require(rows and rows[0].strip() == "NAME", "process_inventory")
    require(not any(row.strip() == package or row.strip().startswith(package + ":")
                    for row in rows[1:] for package in identities), "owned_process_cleanup")


def exercise(device, run, output):
    parent = remote_path(run, "owner-v1").rsplit("/", 1)[0]
    device.shell("run-as", PACKAGE, "/system/bin/sh", "-c",
                 "[ ! -e " + parent + " ] && [ ! -L " + parent + " ]")
    attempted = device.raw(["shell", "am instrument -w -r -e class " + TEST_CLASS + "#" + TEST_METHOD +
        " -e archive_capacity_run " + run + " " + TEST_PACKAGE + "/androidx.test.runner.AndroidJUnitRunner"], deadline=180)
    common.write_new(output / "instrumentation.raw.txt", attempted.stdout)
    common.require_process(attempted)
    parsed = ownership.parse_transcript(attempted.stdout, expected_class=TEST_CLASS, expected_method=TEST_METHOD)
    require(read_remote(device, run, "owner-v1") == MARKER, "remote_owner")
    source = read_remote(device, run, "archive.json")
    raw = read_remote(device, run, "capacity-verified.json")
    verified = record(raw, run, source)
    common.write_new(output / "capacity-verified.json", raw)
    return {**parsed, "raw_sha256": common.digest(attempted.stdout),
            "archive_sha256": verified["archive_sha256"], "full_count": verified["full_count"],
            "same_binary_cache_relief": True}


def run(args):
    require(re.fullmatch(r"[A-Za-z0-9_-]{1,24}", args.alias), "invalid_alias")
    output = common.fresh_directory(args.output_directory)
    result = {"version": 1, "scope": "synthetic_sqlite_page_limit_archive", "target_alias": args.alias, "status": "failed"}
    device, identities, before = None, None, None
    admitted = False
    tool_cleaned = True
    with (output / "commands.jsonl").open("x", encoding="utf-8", newline="\n") as log:
        def journal(event, **fields):
            nonlocal tool_cleaned
            if event == "tool":
                tool_cleaned = tool_cleaned and fields.get("cleanup") is True
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
            device = ownership.OwnedDevice(common.real_path(args.adb), args.serial, journal)
            require(device.shell("getprop", "sys.boot_completed").strip() == b"1", "device_not_booted")
            result["android_api"] = int(device.shell("getprop", "ro.build.version.sdk").strip())
            result["abi"] = device.shell("getprop", "ro.product.cpu.abi").decode("ascii").strip()
            require(result["android_api"] == 35 and result["abi"] == "x86_64", "device_profile")
            before = snapshot(device)
            require(all(before.get(package) == value for package, value in identities.items()), "installed_artifact_mismatch")
            admitted = True
            stop_owned(device, identities)
            result["test"] = exercise(device, "capacity-" + uuid.uuid4().hex, output)
            result["status"] = "passed"
        except Failure as failure:
            result["failure"] = failure.category
        except common.android.Failure:
            result["failure"] = "device_command_failed"
        except (OSError, ValueError, TypeError, KeyError, RuntimeError):
            result["failure"] = "host_io_or_format"
        finally:
            if device is not None:
                if device.clients_cleaned and tool_cleaned and admitted:
                    try:
                        stop_owned(device, identities)
                        result["owned_processes_absent"] = True
                        result["prior_packages_preserved"] = snapshot(device) == before
                    except (Failure, common.android.Failure, OSError, ValueError):
                        result["cleanup_failure"] = "owned_cleanup_or_identity"
                result["adb_clients_cleaned"] = device.clients_cleaned
            result["tool_clients_cleaned"] = tool_cleaned
            if not tool_cleaned or not all(result.get(key) is True for key in
                    ("adb_clients_cleaned", "owned_processes_absent", "prior_packages_preserved")):
                result["status"] = "failed"
            common.write_new(output / "result.json", (json.dumps(result, indent=2) + "\n").encode())
    return result


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ("serial", "alias", "adb", "app-apk", "test-apk", "output-directory"):
        parser.add_argument("--" + name, required=True, type=str if name in ("serial", "alias") else Path)
    try:
        result = run(parser.parse_args(argv))
        print(json.dumps({key: result[key] for key in ("version", "target_alias", "status")}))
        return 0 if result["status"] == "passed" else 1
    except (Failure, OSError, ValueError):
        print('{"version":1,"status":"refused"}')
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
