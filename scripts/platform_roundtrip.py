"""Explicit synthetic Windows/Android archive proof; never installs or clears apps.

Copyright 2026 LocalLore contributors. SPDX-License-Identifier: Apache-2.0
"""
import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import stat
import subprocess
import sys
import uuid
import zipfile

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "benchmarks"))
import android_runtime_spike as android  # noqa: E402
import runtime_spike as process_owner  # noqa: E402

PACKAGE = "org.locallore.app.archiveverify"
TEST_PACKAGE = PACKAGE + ".test"
TEST_CLASS = "org.locallore.app.ArchivePlatformRoundTripTest"
MARKER = b"locallore-platform-roundtrip-v1"
MAX_FIXTURE_BYTES = 128 * 1024
ASSETS = ("windows-origin.json", "windows-continued.json", "expectations.json")
OUTBOUND = ("windows-return.json", "windows-continued.json", "android-origin.json")
REMOTE_FILES = set(OUTBOUND + ("android-return.json", "android-final.json", "owner-v1"))


class Failure(Exception):
    """Only a fixed category may escape the private proof directory."""
    def __init__(self, category):
        super().__init__(category)
        self.category = category


def require(condition, category):
    if not condition:
        raise Failure(category)


def digest(data):
    return hashlib.sha256(data).hexdigest()


def real_path(path):
    """Trusted construction only; refuse linked/reparse ancestors, including junctions."""
    path = Path(os.path.abspath(path))
    for entry in (path, *path.parents):
        metadata = entry.lstat()
        require(not stat.S_ISLNK(metadata.st_mode) and not
                getattr(metadata, "st_file_attributes", 0) & 0x400, "linked_path")
    return path


def fresh_directory(path):
    path = Path(os.path.abspath(path))
    real_path(path.parent)
    path.mkdir()  # Atomic exclusive reservation; existing output is never adopted.
    return path


def read_small(path):
    path = real_path(path)
    require(stat.S_ISREG(path.lstat().st_mode), "not_regular")
    with path.open("rb") as source:
        data = source.read(MAX_FIXTURE_BYTES + 1)
    require(0 < len(data) <= MAX_FIXTURE_BYTES, "fixture_size")
    return data


def write_new(path, data):
    with Path(path).open("xb") as output:
        output.write(data)


def remote_path(run, name):
    require(isinstance(run, str) and re.fullmatch(r"[a-z0-9-]{1,48}", run), "invalid_run")
    require(name in REMOTE_FILES, "invalid_remote_file")
    return "no_backup/platform-roundtrip/" + run + "/" + name


def parse_instrumentation(data):
    """ADB/runner success is insufficient: require exactly one matched test terminal."""
    try:
        text = data.decode("utf-8", errors="strict")
    except UnicodeError:
        raise Failure("instrumentation_encoding") from None
    fields, started, ended = {}, [], []
    codes = []
    for line in text.splitlines():
        if line.startswith("INSTRUMENTATION_STATUS: "):
            key, separator, value = line[len("INSTRUMENTATION_STATUS: "):].partition("=")
            require(separator and key not in fields, "instrumentation_fields")
            fields[key] = value
        elif line.startswith("INSTRUMENTATION_STATUS_CODE: "):
            code = line.partition(": ")[2]
            require(code in ("1", "0", "-1", "-2", "-3", "-4"), "instrumentation_status")
            require(fields.get("class") == TEST_CLASS and fields.get("test") == "platformRoundTrip"
                    and fields.get("numtests") == "1", "instrumentation_inventory")
            key = (fields["class"], fields["test"])
            if code == "1":
                started.append(key)
            else:
                require(started == [key] and not ended, "instrumentation_terminal")
                ended.append(key)
                codes.append(code)
            fields = {}
        elif line.startswith("INSTRUMENTATION_CODE:"):
            require(line == "INSTRUMENTATION_CODE: -1", "instrumentation_runner")
    require(started == [(TEST_CLASS, "platformRoundTrip")] and ended == started and codes == ["0"],
            "instrumentation_failed")
    require(text.count("INSTRUMENTATION_CODE: -1") == 1 and "OK (1 test)" in text,
            "instrumentation_summary")
    require(not fields and not any(token in text for token in
            ("FAILURES!!!", "INSTRUMENTATION_FAILED", "Process crashed", "shortMsg=")),
            "instrumentation_failed")
    return {"started": 1, "passed": 1, "failed": 0, "skipped": 0, "unfinished": 0}


def verify_packaged_fixtures(test_apk, fixtures):
    with zipfile.ZipFile(test_apk) as archive:
        names = archive.namelist()
        require(len(names) == len(set(names)) and len(names) <= 4096, "apk_entries")
        expected = {"assets/platform-roundtrip-v1/" + name for name in ASSETS}
        actual = {name for name in names if name.startswith("assets/platform-roundtrip-v1/")}
        require(actual == expected, "fixture_inventory")
        result = {}
        for name in ASSETS:
            entry = archive.getinfo("assets/platform-roundtrip-v1/" + name)
            require(0 < entry.file_size <= MAX_FIXTURE_BYTES, "fixture_size")
            data = read_small(fixtures / name)
            require(archive.read(entry) == data, "fixture_drift")
            result[name] = digest(data)
        return result


class OwnedDevice(android.Device):
    def __init__(self, adb, serial, journal):
        super().__init__(adb, serial)
        self.clients_cleaned = True
        self.journal = journal

    def raw(self, args, request=b"", deadline=20, cancel=None):
        require(self.clients_cleaned, "client_cleanup_unknown")
        result = super().raw(args, request, deadline, cancel)
        self.clients_cleaned = result.cleanup_complete is True
        self.journal("adb", status=result.status, exit_code=result.returncode,
                     stdout_bytes=len(result.stdout), cleanup=self.clients_cleaned)
        return result


def require_process(result):
    require(result.status == "completed" and result.returncode == 0 and result.cleanup_complete,
            "process_failed")
    return result.stdout


def installed_hash(device, package):
    require(re.fullmatch(r"org\.locallore\.[A-Za-z0-9_.]+", package), "invalid_package")
    location = device.shell("pm", "path", package).strip()
    require(location.startswith(b"package:") and b"\n" not in location and b"\r" not in location,
            "package_path")
    path = location[len(b"package:"):].decode("utf-8", errors="strict")
    value = device.shell("sha256sum", path).split()
    require(len(value) == 2 and re.fullmatch(b"[0-9a-f]{64}", value[0]), "package_hash")
    return value[0].decode("ascii")


def protected_packages(device):
    listing = device.shell("pm", "list", "packages", "org.locallore.").decode("utf-8")
    require(all(line.startswith("package:org.locallore.") for line in listing.splitlines()),
            "package_inventory")
    packages = [line[len("package:"):] for line in listing.splitlines() if line.startswith("package:")]
    require(len(packages) == len(set(packages)) and PACKAGE in packages and TEST_PACKAGE in packages,
            "package_inventory")
    return {package: installed_hash(device, package) for package in sorted(packages)}


def owned_processes_absent(device):
    rows = device.shell("ps", "-A", "-o", "NAME").decode("utf-8").splitlines()
    require(rows and rows[0].strip() == "NAME", "process_inventory")
    return not any(row.strip() == package or row.strip().startswith(package + ":")
                   for row in rows[1:] for package in (PACKAGE, TEST_PACKAGE))


def stop_owned(device, identities):
    # Identity check precedes every package mutation; no unknown process/package is touched.
    for package in (PACKAGE, TEST_PACKAGE):
        require(installed_hash(device, package) == identities[package], "owned_package_changed")
        device.shell("am", "force-stop", package)
    require(owned_processes_absent(device), "owned_process_cleanup")


def remote_read(device, run, name):
    path = remote_path(run, name)
    command = ("[ -f " + path + " ] && [ ! -L " + path + " ] && "
               "[ \"$(stat -c %s " + path + ")\" -le 131072 ] && cat " + path)
    data = device.shell("run-as", PACKAGE, "/system/bin/sh", "-c", command)
    require(0 < len(data) <= MAX_FIXTURE_BYTES, "fixture_size")
    return data


def remote_marker(device, run):
    require(remote_read(device, run, "owner-v1") == MARKER, "remote_owner")


def put_return(device, run, data):
    require(0 < len(data) <= MAX_FIXTURE_BYTES, "fixture_size")
    remote_marker(device, run)
    path = remote_path(run, "android-return.json")
    # mksh noclobber exclusively creates the fixed new file; no truncate/overwrite fallback.
    device.shell("run-as", PACKAGE, "/system/bin/sh", "-c",
                 "umask 077; set -C; cat > " + path, request=data)
    require(remote_read(device, run, "android-return.json") == data, "return_transfer_drift")


def phase(device, name, run, output, identities):
    require(name in ("outbound", "return"), "invalid_phase")
    remote_path(run, "owner-v1")
    attempted = device.raw(["shell", "am instrument -w -r -e class " + TEST_CLASS +
        " -e platform_phase " + name + " -e platform_run " + run + " " +
        TEST_PACKAGE + "/androidx.test.runner.AndroidJUnitRunner"], deadline=120)
    raw = attempted.stdout
    write_new(output / (name + ".raw.txt"), raw)
    # Drain the verified isolated packages even when terminal parsing finds a test failure.
    if device.clients_cleaned:
        stop_owned(device, identities)
    require_process(attempted)
    return {**parse_instrumentation(raw), "raw_sha256": digest(raw)}


def native_check(executable, mode, output, inputs, fixtures, journal):
    require(mode in ("verify", "check-final"), "invalid_mode")
    args = [str(executable), "--owned-stdin", "--development-fixtures", mode, "--directory", str(output),
            "--inputs", str(inputs), "--fixtures", str(fixtures)]
    result = process_owner.run_process(args, deadline=120)
    journal("native", mode=mode, status=result.status, exit_code=result.returncode,
            cleanup=result.cleanup_complete)
    write_new(output.parent / (mode + ".raw.txt"), result.stdout)
    require_process(result)
    report = json.loads(read_small(output / "result.json"))
    require(isinstance(report, dict) and type(report.get("version")) is int and report["version"] == 1
            and report.get("status") == "passed" and report.get("mode") == mode
            and report.get("fixture") == "locallore-platform-roundtrip-v1", "native_report")
    return {"status": "passed", "raw_sha256": digest(result.stdout)}


def run(args):
    require(re.fullmatch(r"[A-Za-z][A-Za-z0-9_-]{0,31}", args.alias), "invalid_alias")
    output = fresh_directory(args.output_directory)
    run_id = "transfer-" + uuid.uuid4().hex
    result = {"version": 1, "target_alias": args.alias, "status": "failed",
              "phases": {}, "models_copied": 0, "model_generations": 0,
              "installed_apks": False, "cleared_app_data": False,
              "prior_packages_preserved": False, "owned_processes_absent": False,
              "adb_clients_cleaned": True}
    device, before, identities = None, None, None
    owned_verified = False
    native_cleaned = True
    with (output / "commands.jsonl").open("x", encoding="utf-8", newline="\n") as log:
        def journal(event, **fields):
            nonlocal native_cleaned
            if event == "native":
                native_cleaned = native_cleaned and fields.get("cleanup") is True
            log.write(json.dumps({"event": event, **fields}) + "\n")
            log.flush()
            os.fsync(log.fileno())
        try:
            app, test = real_path(args.app_apk), real_path(args.test_apk)
            executable, fixtures = real_path(args.fixture_executable), real_path(args.fixtures)
            identities = {PACKAGE: digest(app.read_bytes()), TEST_PACKAGE: digest(test.read_bytes())}
            result["apk_sha256"] = identities
            result["native_fixture_sha256"] = digest(executable.read_bytes())
            result["fixture_sha256"] = verify_packaged_fixtures(test, fixtures)
            # Package names are checked from artifacts, never inferred from filenames.
            aapt = Path(args.adb).parent.parent / "build-tools/35.0.0/aapt2.exe"
            if os.name != "nt":
                aapt = aapt.with_name("aapt2")
            for apk, package in ((app, PACKAGE), (test, TEST_PACKAGE)):
                command = [str(aapt), "dump", "badging", str(apk)]
                badging = subprocess.run(command, check=True, capture_output=True, timeout=20).stdout
                require(badging.splitlines() and badging.splitlines()[0].startswith(("package: name='" + package + "' ").encode()),
                        "apk_package")
            device = OwnedDevice(real_path(args.adb), args.serial, journal)
            require(device.shell("getprop", "sys.boot_completed").strip() == b"1", "device_not_booted")
            result["android_api"] = int(device.shell("getprop", "ro.build.version.sdk").strip())
            result["abi"] = device.shell("getprop", "ro.product.cpu.abi").decode("ascii").strip()
            before = protected_packages(device)
            require(all(before.get(package) == value for package, value in identities.items()),
                    "installed_artifact_mismatch")
            owned_verified = True
            stop_owned(device, identities)
            outbound = phase(device, "outbound", run_id, output, identities)
            result["phases"]["android_outbound"] = outbound
            remote_marker(device, run_id)
            inputs = fresh_directory(output / "outbound")
            artifacts = {}
            for name in OUTBOUND:
                data = remote_read(device, run_id, name)
                write_new(inputs / name, data)
                artifacts[name] = {"bytes": len(data), "sha256": digest(data)}
            require(read_small(inputs / "windows-return.json") == read_small(fixtures / "windows-origin.json")
                    and read_small(inputs / "windows-continued.json") == read_small(fixtures / "windows-continued.json"),
                    "windows_transfer_drift")
            native_output = output / "windows"
            result["phases"]["windows_import_continue"] = native_check(
                executable, "verify", native_output, inputs, fixtures, journal)
            returned = read_small(native_output / "android-return.json")
            put_return(device, run_id, returned)
            artifacts["android-return.json"] = {"bytes": len(returned), "sha256": digest(returned)}
            result["phases"]["android_return"] = phase(device, "return", run_id, output, identities)
            remote_marker(device, run_id)
            final = fresh_directory(output / "final")
            data = remote_read(device, run_id, "android-final.json")
            write_new(final / "android-final.json", data)
            artifacts["android-final.json"] = {"bytes": len(data), "sha256": digest(data)}
            require(data == read_small(native_output / "expected-android-final.json"), "final_transfer_drift")
            result["phases"]["windows_final_replay"] = native_check(
                executable, "check-final", output / "windows-final", final, native_output, journal)
            result["artifacts"] = artifacts
            result["status"] = "passed"
        except Failure as failure:
            result["failure"] = failure.category
        except android.Failure:
            result["failure"] = "device_command_failed"
        except (OSError, ValueError, TypeError, KeyError, RuntimeError, zipfile.BadZipFile, subprocess.SubprocessError):
            result["failure"] = "host_io_or_format"
        finally:
            if device is not None:
                result["adb_clients_cleaned"] = device.clients_cleaned
                if device.clients_cleaned and native_cleaned and owned_verified:
                    try:
                        stop_owned(device, identities)
                        result["owned_processes_absent"] = True
                        result["prior_packages_preserved"] = protected_packages(device) == before
                    except (Failure, android.Failure, OSError, ValueError):
                        result["cleanup_failure"] = "owned_cleanup_or_identity"
                result["adb_clients_cleaned"] = device.clients_cleaned
            require_process_guards = all(result.get(key) is True for key in
                ("prior_packages_preserved", "owned_processes_absent", "adb_clients_cleaned"))
            result["native_clients_cleaned"] = native_cleaned
            if not require_process_guards or not native_cleaned:
                result["status"] = "failed"
            write_new(output / "result.json", (json.dumps(result, indent=2) + "\n").encode("utf-8"))
    return result


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ("serial", "alias", "adb", "app-apk", "test-apk", "fixture-executable", "fixtures", "output-directory"):
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
