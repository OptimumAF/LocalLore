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
from benchmarks.android_process_controller_evidence import validate_controller_result, validate_product_records
from benchmarks.android_retirement_evidence import validate_retirement, SIDECARS

CASES = ("restore_non_default", "restore_child_branch", "restore_retired_child", "restore_retained_parent")
FIXTURE_DIRS = dict(zip(CASES, ("process-controller-v1", "process-controller-child-v1",
                              "process-controller-retired-v1", "process-controller-retained-parent-v1")))
RETIRED = CASES[2:]
MISSING = b"LL_HOST_EVIDENCE_ABSENT_V1\n"
FIELDS = {"case", "run_id", "out", "sdk", "powershell", "build", "gate", "running", "proposal", "server"}
CLAIM = "external-controller-claimed-v1.json"
SCOPE = "android_external_controller_execution"
WORKER_LINE = "external_worker_completed"


class ExternalRefused(RuntimeError):
    pass


def require(value, reason):
    if not value:
        raise ExternalRefused(reason)


def write_bytes(path, raw):
    with path.open("xb") as stream:
        require(stream.write(raw) == len(raw), "short_write")
        stream.flush()
        os.fsync(stream.fileno())


def bindings(request):
    files = [Path(request[key]) for key in ("build", "gate", "running", "proposal", "server", "powershell")]
    files.append(Path(request["sdk"]) / "platform-tools/adb.exe")
    return [environment.binding(path) for path in files]


def admit(request):
    require(type(request) is dict and set(request) == FIELDS | {"inputs", "sources", "driver_sha256"}, "request_fields")
    require(type(request["case"]) is str and request["case"] in CASES and type(request["run_id"]) is str and
            re.fullmatch(r"[0-9a-f]{16}", request["run_id"]), "case_or_nonce")
    for key in FIELDS - {"case", "run_id"}:
        require(type(request[key]) is str, "request_path")
        environment.safe_path(request[key], directory=key in ("out", "sdk"))
    require(request["sources"]["path"] == str(Path(request["out"]) / "sources-before-v1.json"), "source_path")
    require(request["inputs"] == bindings(request), "inputs_changed")
    environment.check_binding(request["sources"])
    require(environment.read_json(request["sources"]["path"]) == driver.source_map(), "sources_changed")
    require(request["driver_sha256"] == environment.digest(Path(__file__)), "driver_changed")


def qualified_gate(path, build_path):
    """A passed label or partial fixture cannot authorize later UI work."""
    path = Path(path)
    require(path.name == "result-v1.json", "gate_result_path")
    value = environment.read_json(path)
    require(type(value) is dict and set(value) == {"version", "phase", "passed", "owner", "owner_record", "request",
            "sources_before", "sources_after", "components"} and type(value["version"]) is int and value["version"] == 1
            and value["phase"] == "components" and value["passed"] is True and known_owner(value["owner"]), "gate_not_qualified")
    out = path.parent
    require(driver.bound_json(value["owner_record"], out / "owner-result-v1.json") == value["owner"], "gate_owner")
    request = driver.bound_json(value["request"], out / "request-v1.json")
    driver.admit_worker(request)
    require(request["phase"] == "components" and Path(request["out"]) == out and Path(request["build"]) == Path(build_path)
            and request["sources"] == value["sources_before"]
            and request["inputs"] == driver.input_bindings(request), "gate_inputs")
    before = driver.bound_json(value["sources_before"], out / "sources-before-v1.json")
    after = driver.bound_json(value["sources_after"], out / "sources-after-v1.json")
    require(before == after == driver.source_map(), "gate_source_drift")
    driver.validate_component_record(driver.bound_json(value["components"], out / "components-v1.json"), out)
    owner_output(out, value["owner"], "worker_completed")
    return request


class Session:
    def __init__(self, request, out):
        self.request = request
        self.failed = False
        self.sources = environment.read_json(request["sources"]["path"])
        self.live = environment.open_live_owner(request["proposal"], request["running"], environment.digest(request["running"]))
        self.lease = self.live.descriptor
        sdk = Path(request["sdk"])
        require(self.lease["adb_path"] == str(sdk / "platform-tools/adb.exe") and self.lease["avd_name"] == environment.NAME
                and self.lease["serial"] == "emulator-5592" and self.lease["console_port"] == 5592
                and self.lease["guest_boot_verified"] is False, "owned_target")
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
        try:
            require(not self.failed, "session_closed")
            self.live.check()
            admit(self.request)
            require(driver.source_map() == self.sources, "source_drift")
        except BaseException:
            self.failed = True
            if hasattr(self, "capture"):
                self.capture.clean = False
            raise ExternalRefused("session_closed") from None

    def adb(self, operation, label, seconds=20, cap=131072):
        try:
            self.check()
            raw = self.capture.adb(operation, label, seconds, cap)
            self.check()
            return raw
        except BaseException:
            self.failed = True
            self.capture.clean = False
            raise ExternalRefused("session_closed") from None

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
    require(all(part not in ("", ".", "..") for part in parts), "read_arguments")
    checks += ["test $(wc -c < " + quoted + ") -gt 0"]
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


def known_owner(value):
    fields = {"status", "cleanup_complete", "elapsed_ms", "worker_returncode", "stdout_bytes", "stderr_bytes", "output_capture_complete"}
    return (type(value) is dict and set(value) == fields and driver.owner_ok(value)
            and type(value["elapsed_ms"]) is int and 0 <= value["elapsed_ms"] <= 1200000
            and type(value["stdout_bytes"]) is int and 0 <= value["stdout_bytes"] <= 262144
            and type(value["stderr_bytes"]) is int and value["stderr_bytes"] == 0)


def owner_output(out, owner, line=WORKER_LINE):
    raw = (out / "owner-stdout-v1.bin").read_bytes()
    error = (out / "owner-stderr-v1.bin").read_bytes()
    require(len(raw) == owner["stdout_bytes"] and len(error) == owner["stderr_bytes"] == 0
            and raw in ((line + "\n").encode(), (line + "\r\n").encode()), "owner_output")


def same_json(left, right):
    if type(left) is not type(right):
        return False
    if type(left) is dict:
        return left.keys() == right.keys() and all(same_json(left[k], right[k]) for k in left)
    if type(left) is list:
        return len(left) == len(right) and all(same_json(a, b) for a, b in zip(left, right))
    return left == right


def check_processes(session, uids):
    raw = session.shell(["ps", "-A", "-o", "PID,UID,NAME"], "processes")
    lines = raw.decode("utf-8").splitlines()
    require(lines and lines[0].split() == ["PID", "UID", "NAME"], "process_shape")
    for line in lines[1:]:
        row = line.split(maxsplit=2)
        require(len(row) == 3 and re.fullmatch(r"[1-9][0-9]*", row[0]) and re.fullmatch(r"[0-9]+", row[1]), "process_shape")
        require(0 < int(row[0]) <= 2**31 - 1 and 0 <= int(row[1]) <= 2**31 - 1, "process_shape")
        require(int(row[1]) not in uids.values() and not any(row[2] == p or row[2].startswith(p + ":") for p in driver.PACKAGES), "process_present")


def reuse_installation(request, gate):
    same_running = Path(request["running"]) == Path(gate["running"])
    same_proposal = Path(request["proposal"]) == Path(gate["proposal"])
    require(same_running == same_proposal, "gate_lease_mixed")
    require(Path(request["sdk"]) == Path(gate["sdk"]) and Path(request["powershell"]) == Path(gate["powershell"]), "gate_tools")
    if same_running:
        require(environment.read_json(request["server"]) == environment.read_json(gate["server"]), "gate_server")
    return same_running


def claim_value(request):
    return {"version": 1, "scope": "android_external_controller_claim", "case": request["case"], "run_id": request["run_id"],
            "request_sha256": environment.digest(Path(request["out"]) / "request-v1.json"),
            "driver_sha256": request["driver_sha256"], "sources_sha256": request["sources"]["sha256"],
            **{key + "_sha256": environment.digest(request[key]) for key in ("running", "proposal", "build")}}


def worker(request, out):
    admit(request)
    artifacts = driver.qualified_build(request["build"])
    gate = qualified_gate(request["gate"], request["build"])
    reuse = reuse_installation(request, gate)
    live = environment.open_live_owner(request["proposal"], request["running"], environment.digest(request["running"]))
    claim = environment.safe_path(Path(live.descriptor["root"]) / CLAIM, exists=False)
    live.check()
    environment.create_json(claim, claim_value(request))  # Burn before Session can issue even read-only SDK calls.
    admit(request)
    session = Session(request, out)
    uids = install_or_verify(session, artifacts, reuse)
    check_processes(session, uids)
    expected = expected_pins(request, artifacts, uids)
    session.user_zero()
    raw = session.adb(controller_operation(request, expected), "controller", 180, 4160)
    write_bytes(out / "controller.stdout.raw", raw)
    proof = validate_controller_result(raw, expected)
    environment.create_json(out / "proof-v1.json", proof)
    record_bindings, records = {}, {}
    for leaf in ("created", "saved", "commands"):
        path = "no_backup/process-verify-v1/" + request["run_id"] + "/" + leaf + ".json"
        records[leaf] = collect_blob(session, out, leaf, driver.APP, uids[driver.APP], path, 4096)
        require(records[leaf] is not None, "product_missing")
        record_bindings[leaf] = environment.binding(out / (leaf + ".raw"))
    validate_product_records(proof, records, expected)
    fixture_root = "no_backup/" + FIXTURE_DIRS[request["case"]]
    fixture = collect_blob(session, out, "fixture", driver.CONTROL, uids[driver.CONTROL], fixture_root + "/fixture-v1.json", 4096)
    require(fixture is not None and same_json(driver.strict_json_bytes(fixture, 4096), proof["fixture"]), "fixture_changed")
    helpers, transports, sidecars = {}, {}, {}
    helper_bindings, transport_bindings, sidecar_bindings = {}, {}, {}
    if request["case"] in RETIRED:
        root = fixture_root + "/helpers-" + request["run_id"]
        for mode in ("load", "probe", "retire"):
            helpers[mode] = collect_blob(session, out, "helper-" + mode, driver.CONTROL, uids[driver.CONTROL], root + "/" + mode + "-v1.json", 4096)
            require(helpers[mode] is not None, "helper_missing")
            transports[mode] = collect_blob(session, out, "transport-" + mode, driver.CONTROL, uids[driver.CONTROL], root + "/" + mode + "-transport-v1.bin", 4160)
            require(transports[mode] is not None, "transport_missing")
            helper_bindings[mode] = environment.binding(out / ("helper-" + mode + ".raw"))
            transport_bindings[mode] = environment.binding(out / ("transport-" + mode + ".raw"))
        helper_transports(helpers, transports)
        if request["case"] == CASES[3]:
            for leaf in SIDECARS:
                label = "sidecar-" + leaf[:-5]
                sidecars[leaf] = collect_blob(session, out, label, driver.APP, uids[driver.APP],
                    "no_backup/retained-parent-selection-fixture-v1/" + request["run_id"] + "/" + leaf, 262144)
                require(sidecars[leaf] is not None, "sidecar_missing")
                sidecar_bindings[leaf] = environment.binding(out / (label + ".raw"))
            require(sum(map(len, sidecars.values())) <= 1048576, "sidecar_total")
        validate_retirement(proof, helpers, sidecars, expected)
    pid = session.shell(["pidof", driver.APP], "final-product-pid", cap=1024)
    write_bytes(out / "final-product-pid.raw", pid)
    require(pid.strip() == str(proof["observations"][2]["pid"]).encode(), "product_pid_changed")
    session.check()
    session.capture.check_server()
    require(session.capture.clean is True, "clients_unknown")
    environment.create_json(out / "external-v1.json", {"version": 1, "case": request["case"], "run_id": request["run_id"],
        "expected": expected, "uids": uids, "clients": session.capture.count, "clients_clean": True, "reused_installation": reuse,
        "claim": environment.binding(claim), "controller": environment.binding(out / "controller.stdout.raw"),
        "proof": environment.binding(out / "proof-v1.json"), "records": record_bindings,
        "fixture": environment.binding(out / "fixture.raw"), "helpers": helper_bindings, "transports": transport_bindings,
        "sidecars": sidecar_bindings, "final_product_pid": environment.binding(out / "final-product-pid.raw")})


def bound_bytes(binding, path, cap):
    require(type(binding) is dict and set(binding) == {"path", "bytes", "sha256"} and binding["path"] == str(path), "record_path")
    require(type(binding["bytes"]) is int and 0 < binding["bytes"] <= cap, "record_bounds")
    require(environment.safe_path(path).stat().st_size == binding["bytes"], "record_bounds")
    environment.check_binding(binding)
    return path.read_bytes()


def validate_clients(out, count, copies):
    require(type(count) is int and 0 < count <= 10000, "client_count")
    expected_files, rows = set(), []
    for index in range(1, count + 1):
        stem = out / "clients" / ("command-%04d" % index)
        expected_files.update((stem.with_suffix(".json").name, stem.with_suffix(".stdout.bin").name))
        row = environment.read_json(stem.with_suffix(".json"))
        require(type(row) is dict and set(row) == {"version", "index", "label", "status", "returncode", "cleanup_complete", "stdout_bytes", "stdout_sha256", "stderr_bytes"}, "client_shape")
        require(type(row["version"]) is int and row["version"] == 1 and type(row["index"]) is int and row["index"] == index
                and type(row["label"]) is str and re.fullmatch(r"[a-z][a-z0-9_-]{0,47}", row["label"])
                and row["status"] == "completed" and type(row["returncode"]) is int and row["returncode"] == 0
                and row["cleanup_complete"] is True and type(row["stderr_bytes"]) is int and row["stderr_bytes"] == 0
                and type(row["stdout_bytes"]) is int and 0 <= row["stdout_bytes"] <= 262144, "client_failed")
        raw_path = environment.safe_path(stem.with_suffix(".stdout.bin"))
        require(raw_path.stat().st_size == row["stdout_bytes"], "client_raw")
        data = raw_path.read_bytes()
        require(len(data) == row["stdout_bytes"] and hashlib.sha256(data).hexdigest() == row["stdout_sha256"], "client_raw")
        rows.append(row)
    require({p.name for p in (out / "clients").iterdir()} == expected_files, "client_extra")
    for label, raw in copies.items():
        matches = [r for r in rows if r["label"] == label]
        require(len(matches) == 1 and matches[0]["stdout_bytes"] == len(raw)
                and matches[0]["stdout_sha256"] == hashlib.sha256(raw).hexdigest(), "client_copy")


def validate_execution(request, out):
    admit(request)
    artifacts = driver.qualified_build(request["build"])
    gate = qualified_gate(request["gate"], request["build"])
    record = environment.read_json(out / "external-v1.json")
    require(type(record) is dict and set(record) == {"version", "case", "run_id", "expected", "uids", "clients", "clients_clean", "reused_installation",
            "claim", "controller", "proof", "records", "fixture", "helpers", "transports", "sidecars", "final_product_pid"}, "external_shape")
    require(type(record["version"]) is int and record["version"] == 1 and record["case"] == request["case"]
            and record["run_id"] == request["run_id"] and record["clients_clean"] is True
            and record["reused_installation"] is reuse_installation(request, gate), "external_identity")
    uids = record["uids"]
    require(type(uids) is dict and set(uids) == set(driver.PACKAGES) and all(type(v) is int and 10000 <= v <= 99999 for v in uids.values())
            and len(set(uids.values())) == 3, "external_uids")
    expected = expected_pins(request, artifacts, uids)
    require(same_json(record["expected"], expected), "expected_changed")
    running = environment.read_json(request["running"])
    claim_path = Path(running["root"]) / CLAIM
    require(same_json(driver.bound_json(record["claim"], claim_path), claim_value(request)), "claim_changed")
    raw = bound_bytes(record["controller"], out / "controller.stdout.raw", 4160)
    proof = validate_controller_result(raw, expected)
    require(same_json(driver.bound_json(record["proof"], out / "proof-v1.json"), proof), "proof_changed")
    require(type(record["records"]) is dict and set(record["records"]) == {"created", "saved", "commands"}, "record_labels")
    records = {leaf: bound_bytes(record["records"][leaf], out / (leaf + ".raw"), 4096) for leaf in ("created", "saved", "commands")}
    validate_product_records(proof, records, expected)
    fixture = bound_bytes(record["fixture"], out / "fixture.raw", 4096)
    require(same_json(driver.strict_json_bytes(fixture, 4096), proof["fixture"]), "fixture_changed")
    modes = {"load", "probe", "retire"} if request["case"] in RETIRED else set()
    for name in ("helpers", "transports"):
        require(type(record[name]) is dict and set(record[name]) == modes, "helper_modes")
    helpers = {m: bound_bytes(record["helpers"][m], out / ("helper-" + m + ".raw"), 4096) for m in modes}
    transports = {m: bound_bytes(record["transports"][m], out / ("transport-" + m + ".raw"), 4160) for m in modes}
    leaves = set(SIDECARS) if request["case"] == CASES[3] else set()
    require(type(record["sidecars"]) is dict and set(record["sidecars"]) == leaves, "sidecar_labels")
    sidecars = {leaf: bound_bytes(record["sidecars"][leaf], out / ("sidecar-" + leaf[:-5] + ".raw"), 262144) for leaf in leaves}
    require(sum(map(len, sidecars.values())) <= 1048576, "sidecar_total")
    if modes:
        helper_transports(helpers, transports)
        validate_retirement(proof, helpers, sidecars, expected)
    pid = bound_bytes(record["final_product_pid"], out / "final-product-pid.raw", 1024)
    require(pid.strip() == str(proof["observations"][2]["pid"]).encode(), "product_pid_changed")
    copies = {"controller": raw, "read-fixture": fixture, "final-product-pid": pid,
              **{"read-" + k: v for k, v in records.items()}, **{"read-helper-" + k: v for k, v in helpers.items()},
              **{"read-transport-" + k: v for k, v in transports.items()}, **{"read-sidecar-" + k[:-5]: v for k, v in sidecars.items()}}
    validate_clients(out, record["clients"], copies)
    return record


def supervise(request):
    require(os.name == "nt" and type(request) is dict and set(request) == FIELDS, "request_fields")
    require(type(request["case"]) is str and request["case"] in CASES and type(request["run_id"]) is str
            and re.fullmatch(r"[0-9a-f]{16}", request["run_id"]), "case_or_nonce")
    out = driver.output_path(request["out"])
    out.mkdir()
    before = driver.source_map()
    environment.create_json(out / "sources-before-v1.json", before)
    request = dict(request, inputs=bindings(request), sources=environment.binding(out / "sources-before-v1.json"), driver_sha256=environment.digest(Path(__file__)))
    environment.create_json(out / "request-v1.json", request)
    admit(request)
    request_sha = environment.digest(out / "request-v1.json")
    def started(child):
        environment.create_json(out / "started-v1.json", {"version": 1, "worker": environment.process_identity(child.pid), "request_sha256": request_sha})
        return True
    result = environment.supervise([sys.executable, "-I", "-B", str(Path(__file__)), "_worker"],
        (str(out / "request-v1.json") + "\n" + request_sha + "\n").encode(), out, 1200, started)
    environment.create_json(out / "owner-result-v1.json", result)  # Before any dependent worker-result readback.
    record = {"version": 1, "scope": SCOPE, "case": request["case"], "run_id": request["run_id"], "passed": False, "owner": result,
        "owner_record": environment.binding(out / "owner-result-v1.json"), "request": environment.binding(out / "request-v1.json"),
        "sources_before": environment.binding(out / "sources-before-v1.json")}
    if known_owner(result):
        try:
            owner_output(out, result)
            require(environment.digest(out / "request-v1.json") == request_sha, "request_changed")
            after = driver.source_map()
            environment.create_json(out / "sources-after-v1.json", after)
            record["sources_after"] = environment.binding(out / "sources-after-v1.json")
            require(before == after, "source_drift")
            validate_execution(request, out)
            record.update(passed=True, external=environment.binding(out / "external-v1.json"))
        except Exception:
            record["validation_refused"] = True
    environment.create_json(out / "result-v1.json", record)
    require(record["passed"], "execution_not_qualified")
    return record


def main(argv=None):
    if argv is None and sys.argv[1:] == ["_worker"]:
        raw = sys.stdin.buffer.read(4097)
        require(0 < len(raw) <= 4096, "barrier_bounds")
        parts = raw.decode("utf-8").split("\n")
        require(len(parts) == 3 and parts[2] == "" and "\r" not in parts[0] and re.fullmatch(r"[0-9a-f]{64}", parts[1]), "barrier_shape")
        path = environment.safe_path(parts[0])
        request = environment.read_bound_json(path, parts[1])
        require(path.name == "request-v1.json" and str(path.parent) == request["out"], "request_path")
        admit(request)
        worker(request, path.parent)
        admit(request)
        require(environment.digest(path) == parts[1], "request_changed")
        print(WORKER_LINE, flush=True)
        return 0
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--case", required=True, choices=CASES)
    parser.add_argument("--run-id")
    for key in ("out", "sdk", "powershell", "build", "gate", "running", "proposal", "server"):
        parser.add_argument("--" + key, required=True)
    request = vars(parser.parse_args(argv))
    if request["run_id"] is None:
        request["run_id"] = secrets.token_hex(8)
    supervise(request)
    print(json.dumps({"version": 1, "scope": SCOPE, "passed": True}))
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception:
        print(json.dumps({"version": 1, "scope": SCOPE, "passed": False, "reason": "external_refused"}))
        raise SystemExit(2)
