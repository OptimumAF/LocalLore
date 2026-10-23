"""Explicit synthetic control fault/recovery probes on one authorized emulator.

No weights or generated prose are needed. Never invoked by default checks.
Copyright 2026 LocalLore contributors. SPDX-License-Identifier: Apache-2.0
"""
import argparse
import json
from pathlib import Path
import shlex

import android_runtime_spike as spike


class InjectedDevice:
    """Inject one known-drained failure; all other calls use the actual device."""
    def __init__(self, device, fault):
        self.device, self.fault, self.armed = device, fault, True
        self.stops, self.launches, self.run_directory = 0, 0, None

    def __getattr__(self, name):
        return getattr(self.device, name)

    def fail(self):
        self.armed = False
        raise spike.Failure("synthetic_control_fault", command_cleaned=True)

    def shell(self, *args, **kwargs):
        if args[0] == "mkdir" and len(args) == 4:
            self.run_directory = args[-1]
            if self.fault == "create_run" and self.armed:
                self.fail()
        if args[0] == "ln" and self.fault == "link_worker" and self.armed:
            self.fail()
        if args[:2] == ("am", "force-stop"):
            self.stops += 1
            if self.fault == "final_stop" and self.stops == 2 and self.armed:
                self.fail()
        result = self.device.shell(*args, **kwargs)
        if args[:2] == ("am", "force-stop") and self.fault == "clean_start" and self.armed:
            self.fail()
        return result

    def put_bytes(self, data, destination):
        self.device.put_bytes(data, destination)
        if self.fault == "write_request" and self.armed:
            self.fail()

    def private_write(self, data):
        self.device.private_write(data)
        if self.fault == "sdk_request" and self.armed:
            self.fail()

    def raw(self, *args, **kwargs):
        self.launches += 1
        return self.device.raw(*args, **kwargs)


def fixture_ok(native, oracle, report):
    report.update(status="oracle_failed", check_passed=False, oracle_runs=[])
    reply = spike.oracle(spike.ObservedOracle(native, report["oracle_runs"]), oracle, "fixture", "gift")
    report["check_passed"] = bool(reply and reply.get("revision") == 0 and reply.get("preflight_error") is None
                                 and isinstance(reply.get("director"), dict))
    if report["check_passed"]:
        report["status"] = "fixture_valid"
    return report["check_passed"]


def probes(device, owner, oracle, apk_sha256, rows):
    native = spike.NativeWorker(device, owner)
    for fault, phase in (("create_run", "native_create_run"), ("link_worker", "native_link_worker"),
                         ("write_request", "native_write_request")):
        injected = InjectedDevice(device, fault)
        row = {"check": "native_" + fault, "injected": True, "passed": False}
        rows.append(row)
        result = spike.NativeWorker(injected, owner).run(oracle, ["fixture", "gift"], deadline=10)
        row.update(spike.remote_metadata(result))
        absent = False
        if injected.run_directory:
            device.script("[ ! -e " + shlex.quote(injected.run_directory) + " ]")
            absent = True
        row["recovery"] = {}
        recovered = fixture_ok(native, oracle, row["recovery"])
        row.update(launcher_calls=injected.launches, owned_directory_absent=absent, fresh_fixture_valid=recovered)
        row["passed"] = bool(result.status == "setup_failed" and result.failure_stage == phase
            and result.cleanup_complete and result.adb_cleanup_complete and absent and recovered
            and injected.launches == 0 and (fault == "create_run" or result.directory_cleanup_complete))
    for fault, mode, phase in (("clean_start", "missing", "sdk_stop_command"),
                               ("sdk_request", "generate", "sdk_write_request"),
                               ("final_stop", "missing", "sdk_stop_command")):
        injected = InjectedDevice(device, fault)
        row = {"check": "sdk_" + fault, "injected": True, "passed": False}
        rows.append(row)
        row["setup_oracle_runs"] = []
        fixture = spike.oracle(spike.ObservedOracle(native, row["setup_oracle_runs"]), oracle, "fixture", "gift")
        if not fixture or not isinstance(fixture.get("director"), dict):
            raise spike.Failure("fixture_failed", command_cleaned=True)
        data = json.dumps(fixture["director"]).encode("utf-8")
        result = spike.SdkWorker(injected, apk_sha256, mode).run("unused", [], data, deadline=30)
        row.update(spike.remote_metadata(result))
        # Explicit recovery follows the retained fault result; it does not relabel it completed.
        row["recovery"] = {"status": "not_started", "check_passed": False}
        recovered = spike.sdk_diagnostic(spike.SdkWorker(device, apk_sha256, "missing"), native, oracle, "missing")
        row["recovery"].update(recovered)
        row.update(launcher_calls=injected.launches, output_discarded=result.stdout == b"" and result.metrics == {},
                   fresh_missing_valid=recovered.get("check_passed") is True)
        if fault == "final_stop":
            passed = (result.status == "cleanup_failed" and result.cleanup_failure_stage == phase
                      and not result.cleanup_complete and injected.launches == 1)
        else:
            passed = (result.status == "setup_failed" and result.failure_stage == phase and result.cleanup_complete
                      and result.adb_cleanup_complete and result.directory_cleanup_complete and injected.launches == 0)
        row["passed"] = bool(passed and row["output_discarded"] and row["fresh_missing_valid"])
    for number in range(3):
        row = {"check": "sdk_corrupt", "repetition": number + 1, "injected": False, "passed": False}
        rows.append(row)
        report = spike.sdk_diagnostic(spike.SdkWorker(device, apk_sha256, "corrupt"), native, oracle, "corrupt")
        row.update(result=report, passed=report.get("check_passed") is True and report.get("directory_cleanup_complete") is True)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--adb", type=Path, required=True)
    parser.add_argument("--serial", required=True)
    parser.add_argument("--owner", type=Path, required=True)
    parser.add_argument("--oracle", type=Path, required=True)
    parser.add_argument("--apk", type=Path, required=True, help="Exact source-built APK already installed")
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    rows, report = [], {"version": 1, "scope": "android_control_fault_recovery", "passed": False}
    try:
        device = spike.Device(args.adb, args.serial)
        device.initialize()
        owner, oracle = [device.cached(path) for path in (args.owner, args.oracle)]
        identity = spike.sha256(args.apk)
        spike.SdkWorker(device, identity).verify_package()
        probes(device, owner, oracle, identity, rows)
        report["passed"] = len(rows) == 9 and all(row["passed"] for row in rows)
    except Exception:
        report["status"] = "probe_failed"
    finally:
        report["checks"] = rows
        text = json.dumps(report, indent=2, allow_nan=False) + "\n"
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(text, encoding="utf-8")
        print(text, end="")
    return 0 if report["passed"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
