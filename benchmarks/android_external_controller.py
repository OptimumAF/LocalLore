"""Create-only external saved-task checks after the qualified native component gate.

Copyright 2026 LocalLore contributors. SPDX-License-Identifier: Apache-2.0
Private evidence only; no phone/model, server lifecycle, reset or fixture retry.
"""
from __future__ import annotations
import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import secrets
import shlex
import sys
import time
import zipfile

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from benchmarks import android_process_verification as driver
from benchmarks import receipt_avd_environment as environment
from benchmarks.android_process_client import SdkCapture

CASES = ("restore_non_default", "restore_child_branch", "restore_retired_child", "restore_retained_parent")
FIXTURE_DIRS = dict(zip(CASES, ("process-controller-v1", "process-controller-child-v1",
                              "process-controller-retired-v1", "process-controller-retained-parent-v1")))
RETIRED = CASES[2:]
MISSING = b"LL_HOST_EVIDENCE_ABSENT_V1\n"
FIELDS = {"case", "run_id", "out", "sdk", "powershell", "build", "gate", "running", "proposal", "server"}


class ExternalRefused(RuntimeError):
    pass


def require(value, reason):
    if not value:
        raise ExternalRefused(reason)


def write_bytes(path, raw):
    with path.open("xb") as stream:
        stream.write(raw)
        stream.flush()
        os.fsync(stream.fileno())


def bindings(request):
    files = [Path(request[key]) for key in ("build", "gate", "running", "proposal", "server", "powershell")]
    files.append(Path(request["sdk"]) / "platform-tools/adb.exe")
    return [environment.binding(path) for path in files]


def admit(request):
    require(type(request) is dict and set(request) == FIELDS | {"inputs", "sources", "driver_sha256"}, "request_fields")
    require(request["case"] in CASES and type(request["run_id"]) is str and
            re.fullmatch(r"[0-9a-f]{16}", request["run_id"]), "case_or_nonce")
    require(request["inputs"] == bindings(request), "inputs_changed")
    environment.check_binding(request["sources"])
    require(environment.read_json(request["sources"]["path"]) == driver.source_map(), "sources_changed")
    require(request["driver_sha256"] == environment.digest(Path(__file__)), "driver_changed")


def qualified_gate(path, build_path):
    """A passed label or partial fixture cannot authorize later UI work."""
    path = Path(path)
    require(path.name == "result-v1.json", "gate_result_path")
    value = environment.read_json(path)
    require(value.get("version") == 1 and value.get("phase") == "components" and
            value.get("passed") is True and driver.owner_ok(value.get("owner")), "gate_not_qualified")
    out = path.parent
    require(driver.bound_json(value["owner_record"], out / "owner-result-v1.json") == value["owner"], "gate_owner")
    request = driver.bound_json(value["request"], out / "request-v1.json")
    require(Path(request["build"]) == Path(build_path) and request["inputs"] == driver.input_bindings(request), "gate_inputs")
    before = driver.bound_json(value["sources_before"], out / "sources-before-v1.json")
    after = driver.bound_json(value["sources_after"], out / "sources-after-v1.json")
    require(before == after == driver.source_map(), "gate_source_drift")
    driver.validate_component_record(driver.bound_json(value["components"], out / "components-v1.json"), out)
    return request


class Session:
    def __init__(self, request, out):
        self.request = request
        self.sources = environment.read_json(request["sources"]["path"])
        self.live = environment.open_live_owner(request["proposal"], request["running"], environment.digest(request["running"]))
        self.lease = self.live.descriptor
        sdk = Path(request["sdk"])
        require(self.lease["adb_path"] == str(sdk / "platform-tools/adb.exe") and
                self.lease["serial"] == "emulator-5592", "owned_target")
        self.check()
        self.capture = SdkCapture(out / "clients", 1100, sdk / "platform-tools/adb.exe",
                                  Path(request["powershell"]), environment.read_json(request["server"]), self.lease["launcher"])
        self.capture.check_server()
        for _ in range(24):
            self.check()
            raw = self.capture.capture([str(sdk / "platform-tools/adb.exe"), "-H", "127.0.0.1", "-P", "5037",
                                        "devices", "-l"], "devices")
            self.capture.check_server()
            rows = [line for line in raw.decode("utf-8").splitlines() if line.split()[:2] == ["emulator-5592", "device"]]
            require(len(rows) <= 1, "ambiguous_target")
            if rows:
                ids = re.findall(r"\btransport_id:([1-9][0-9]*)\b", rows[0])
                require(len(ids) == 1, "transport")
                self.capture.target = {"transport_id": int(ids[0])}
                break
            time.sleep(2)
        require(self.capture.target is not None, "target_unavailable")
        for _ in range(24):
            if self.shell(["getprop", "sys.boot_completed"], "boot").strip() == b"1":
                break
            time.sleep(3)
        else:
            raise ExternalRefused("boot_timeout")
        for key, expected in (("ro.build.version.sdk", b"35"), ("ro.product.cpu.abi", b"x86_64")):
            require(self.shell(["getprop", key], "profile").strip() == expected, "guest_profile")
        self.user_zero()

    def check(self):
        self.live.check()
        require(driver.source_map() == self.sources, "source_drift")

    def adb(self, operation, label, seconds=20, cap=131072):
        self.check()
        raw = self.capture.adb(operation, label, seconds, cap)
        self.check()
        return raw

    def shell(self, operation, label, seconds=20, cap=131072):
        return self.adb(["shell", shlex.join(operation)], label, seconds, cap)

    def user_zero(self):
        require(self.shell(["am", "get-current-user"], "user").strip() == b"0", "user_zero")


def parse_packages(raw):
    require(type(raw) is bytes and len(raw) <= 16384, "package_bounds")
    result = {}
    for line in raw.decode("utf-8").splitlines():
        match = re.fullmatch(r"package:([A-Za-z0-9_.]+) uid:([0-9]+)", line)
        require(match is not None and match[1] not in result, "package_output")
        uid = int(match[2])
        require(10000 <= uid <= 99999, "package_uid")
        result[match[1]] = uid
    return result


def install_or_verify(session, artifacts, reuse_gate):
    found = {}
    for package in driver.PACKAGES:
        rows = parse_packages(session.shell(["cmd", "package", "list", "packages", "-U", "--user", "0", package], "packages"))
        allowed = {driver.APP, driver.APP + ".test"} if package == driver.APP else {package}
        require(set(rows) <= allowed, "unexpected_package")
        if not reuse_gate:
            require(not rows, "fresh_packages_required")
        found.update(rows)
    if reuse_gate:
        require(set(found) == set(driver.PACKAGES), "qualified_installation_missing")
    else:
        for apk in artifacts["apks"]:
            session.user_zero()
            environment.check_binding({key: apk[key] for key in ("path", "bytes", "sha256")})
            require(session.adb(["install", "--user", "0", "-t", apk["path"]], "install", 120).strip().endswith(b"Success"), "install")
        found = {}
        for package in driver.PACKAGES:
            found.update(parse_packages(session.shell(["cmd", "package", "list", "packages", "-U", "--user", "0", package], "installed")))
        require(set(found) == set(driver.PACKAGES), "installed_packages")
    require(len(set(found.values())) == 3, "package_uid_alias")
    for apk in artifacts["apks"]:
        raw = session.shell(["cmd", "package", "path", apk["package"]], "package-path").decode().strip()
        require(raw.startswith("package:/data/app/") and raw.endswith("/base.apk") and "\n" not in raw, "package_path")
        require(session.shell(["sha256sum", raw[len("package:"):]], "package-hash").decode().split()[0] == apk["sha256"], "installed_hash")
    return found


def read_script(path, uid, cap):
    """Only caller-fixed relative leaves; never a path supplied by a proof."""
    require(re.fullmatch(r"no_backup/[A-Za-z0-9_./-]{1,220}", path) and ".." not in path and
            type(uid) is int and 10000 <= uid <= 99999 and type(cap) is int and 0 < cap <= 262144, "read_arguments")
    parts = path.split("/")
    checks = ["test $(id -u) -eq " + str(uid)]
    for index in range(1, len(parts)):
        parent = shlex.quote("/".join(parts[:index]))
        checks += ["test -d " + parent, "test ! -L " + parent,
                   "test $(stat -c %u " + parent + ") -eq " + str(uid)]
    quoted = shlex.quote(path)
    checks += ["test -f " + quoted, "test ! -L " + quoted,
               "test $(stat -c %u " + quoted + ") -eq " + str(uid),
               "test $(wc -c < " + quoted + ") -le " + str(cap)]
    return ("if test ! -e " + quoted + " && test ! -L " + quoted + "; then printf 'LL_HOST_EVIDENCE_ABSENT_V1\\n'; "
            "else " + " && ".join(checks) + " && cat " + quoted + "; fi")


def collect_blob(session, out, label, package, uid, path, cap):
    require(package in driver.PACKAGES, "read_package")
    raw = session.adb(["exec-out", "run-as", package, "--user", "0", "sh", "-c", read_script(path, uid, cap)],
                      "read-" + label, 20, cap)
    write_bytes(out / (label + ".raw"), raw)
    return None if raw == MISSING else raw


def helper_transports(raw, transports):
    require(set(raw) == {"load", "probe", "retire"} and set(transports) == set(raw), "helper_modes")
    suffix = b"\nLL_RETIRED_HELPER_EXIT_V1=0\n\nLL_PROCESS_EXIT_V1=0\n"
    for mode in raw:
        body = raw[mode]
        require(type(body) is bytes and 0 < len(body) <= 4096 and body.endswith(b"\n") and
                body.count(b"\n") == 1 and b"\r" not in body, "helper_quiet")
        require(type(transports[mode]) is bytes and len(transports[mode]) <= 4160 and
                transports[mode] == body + suffix, "helper_transport")


def expected_pins(request, artifacts, uids):
    build = Path(request["build"]).parent
    signature = (build / "signature-0.stdout.raw").read_text(encoding="utf-8")
    certs = re.findall(r"^Signer #1 certificate SHA-256 digest: ([0-9a-fA-F]{64})\r?$", signature, re.M)
    require(len(certs) == 1, "signer")
    library = None
    if request["case"] in RETIRED:
        with zipfile.ZipFile(artifacts["apks"][0]["path"]) as archive:
            entry = archive.getinfo("lib/x86_64/liblocallore_android.so")
            require(entry.compress_type == zipfile.ZIP_STORED and 0 < entry.file_size <= 64 * 1024 ** 2, "native_entry")
            library = hashlib.sha256(archive.read(entry)).hexdigest()
    return {"case": request["case"], "run_id": request["run_id"],
            "product_sha256": artifacts["apks"][0]["sha256"],
            "test_sha256": artifacts["apks"][1]["sha256"] if request["case"] in RETIRED else None,
            "library_sha256": library, "controller_uid": uids[driver.CONTROL], "product_uid": uids[driver.APP],
            "signature_sha256": certs[0].lower()}


def controller_operation(request, expected):
    operation = ["exec-out", "am", "instrument", "--user", "0", "-w", "-r",
                 "-e", "case", request["case"], "-e", "run_id", request["run_id"],
                 "-e", "product_sha256", expected["product_sha256"], "-e", "cohort", "create"]
    if request["case"] in RETIRED:
        operation += ["-e", "fixture_test_sha256", expected["test_sha256"]]
    return operation + [driver.CONTROL + "/org.locallore.processverify.ProcessRestoreInstrumentation"]
