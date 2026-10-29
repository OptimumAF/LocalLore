"""One explicitly admitted original AUTHOR/import/external-restart workflow.

Importing this module neither starts an owner nor grants execution authority.
Copyright 2026 LocalLore contributors. SPDX-License-Identifier: Apache-2.0
"""
import copy
import hashlib
import io
import os
from pathlib import Path
import re
import subprocess
import tarfile
import time
import xml.etree.ElementTree as ET

from benchmarks import receipt_avd_environment as env
from benchmarks import owned_restart_contract as contract
from benchmarks.owned_restart_owner import LiveOwnedRestartTarget
from benchmarks.android_process_client_v5 import OwnedRestartSdkCapture
from benchmarks import android_process_verification_v5 as verification
from benchmarks import android_process_verification as build_verification
from benchmarks import original_author_model_proof as author_proof
from benchmarks import original_author_diagnostic as diagnostic
from benchmarks import original_author_restart_proof as restart_proof
from benchmarks.android_instrumentation_evidence import validate_instrumentation

ROOT = Path(__file__).resolve().parents[1]
SECONDS = 1200
RECORDS = ("workspace-before-v1.json", "recover-v1.json", "snapshot-v1.json",
           "retry-v1.json", "workspace-after-v1.json", "archive-v1.json")
PROCESS_PROBE = "/data/local/tmp/locallore-author-process-probe-v1"
REQUEST_PROTOCOL = "original-author-restart-controller-request-v1"
RESULT_PROTOCOL = "original-author-restart-controller-v1"
BUILD_KEYS = {"version", "scope", "head", "sources", "compiled", "build_files", "fresh_lint_files",
              "apks", "counts", "independent_build", "independent_lint", "process_probe_build"}
PROBE_BUILD_KEYS = {"version", "scope", "ndk_revision", "target", "source", "builder", "tools", "command",
                    "environment", "request", "started", "owner", "compile", "binary", "elf", "passed", "feature_acceptance"}


def _need(value, reason="checks_failed"):
    env.require(value, reason)


def _check_binding(pin):
    _need(type(pin) is dict and set(pin) == {"path", "bytes", "sha256"} and type(pin["path"]) is str and
          type(pin["bytes"]) is int and 0 <= pin["bytes"] <= 3 * 1024 ** 3 and
          type(pin["sha256"]) is str and re.fullmatch("[0-9a-f]{64}", pin["sha256"]) is not None)
    _need(".android" not in (part.casefold() for part in Path(pin["path"]).parts))
    env.check_binding(pin)


def _json(pin):
    _check_binding(pin)
    return env.read_bound_json(pin["path"], pin["sha256"])


def _source_map():
    raw = subprocess.run(["git", "-c", "gc.auto=0", "ls-files", "-z"], cwd=ROOT,
                         capture_output=True, check=True, timeout=10).stdout
    return {name: env.digest(ROOT / name) for name in raw.decode("utf-8").split("\0") if name}


def _compiled_map():
    return build_verification.source_map()


def _current_head():
    status = subprocess.run(["git", "-c", "gc.auto=0", "status", "--porcelain=v1", "--untracked-files=all"],
                            cwd=ROOT, capture_output=True, check=True, timeout=10).stdout
    _need(status == b"")
    return subprocess.run(["git", "-c", "gc.auto=0", "rev-parse", "HEAD"], cwd=ROOT,
                          capture_output=True, check=True, timeout=10).stdout.decode("ascii").strip()


def _content_equal(left, right):
    return all(left[key] == right[key] for key in ("bytes", "sha256"))


def _verify_process_probe_build(pin, admission):
    value = _json(pin)
    _need(set(value) == PROBE_BUILD_KEYS and type(value["version"]) is int and value["version"] == 1 and
          value["scope"] == "android_author_process_probe_build_v1" and value["passed"] is True and
          value["feature_acceptance"] is False and value["ndk_revision"] == "29.0.14206865" and
          value["target"] == "x86_64-linux-android35")
    for key in ("source", "builder", "request", "started", "owner", "compile", "binary"):
        _check_binding(value[key])
    for tool in value["tools"]:
        _check_binding(tool)
    request = _json(value["request"])
    for key in ("version", "scope", "ndk_revision", "target", "source", "builder", "tools", "command", "environment"):
        _need(request[key] == value[key])
    build_root = Path(value["request"]["path"]).parent
    _need(request["output"] == str(build_root) and Path(value["binary"]["path"]) == build_root / "android-author-process-probe-v1")
    # The compiled Choice source paths stay intact; only bytes are compared to current Root source.
    _need(_content_equal(value["source"], admission["artifacts"]["process_probe_source"]) and
          _content_equal(value["builder"], env.binding(ROOT / "scripts/build_android_author_process_probe.py")) and
          value["binary"] == admission["artifacts"]["process_probe"])
    owner = _json(value["owner"])
    _need(owner["status"] == "child_exited" and type(owner["worker_returncode"]) is int and
          owner["worker_returncode"] == 0 and owner["cleanup_complete"] is True and
          owner["output_capture_complete"] is True and owner["stdout_bytes"] == owner["stderr_bytes"] == 0)
    for stream in ("stdout", "stderr"):
        _need(env.safe_path(build_root / ("owner-" + stream + "-v1.bin")).read_bytes() == b"")
    compile_result = _json(value["compile"])
    _need(type(compile_result["returncode"]) is int and compile_result["returncode"] == 0 and compile_result["capture_complete"] is True and
          compile_result["timed_out"] is False and compile_result["output_limit"] is False)
    for stream in ("stdout", "stderr"):
        _check_binding(compile_result[stream])
        _need(compile_result[stream]["bytes"] == 0)
    elf = value["elf"]
    _need(set(elf) == {"elf_class", "machine", "type", "interpreter", "needed"} and elf["elf_class"] == 2 and
          elf["machine"] == 62 and elf["type"] == 3 and elf["interpreter"] == "/system/bin/linker64" and
          "libc.so" in elf["needed"] and set(elf["needed"]) <= {"libc.so", "libdl.so", "libm.so"})
    return value


def _verify_build(pin, admission):
    value = _json(pin)
    _need(set(value) == BUILD_KEYS and type(value["version"]) is int and value["version"] == 1 and
          value["scope"] == "owned_restart_android_build_admission_v1")
    current = _source_map()
    _need(_json(value["sources"]) == current and _json(value["compiled"]) == _compiled_map())
    _need(value["head"] == _current_head())
    counts = value["counts"]
    compiled = _compiled_map()
    _need(all(type(item) is int for item in counts.values()) and
          counts == dict(tracked=len(current), compiled=len(compiled), jvm=588, reports=58) and
          all(current.get(name) == digest for name, digest in compiled.items()))
    for mapping in (value["build_files"], value["fresh_lint_files"]):
        for artifact in mapping.values():
            _check_binding(artifact)
    for key in ("independent_build", "independent_lint"):
        _need(_json(value[key])["passed"] is True)
    files = value["build_files"]
    request = _json(files["request-v1.json"])
    _need(request["sources"] == current == _json(files["sources-before-v1.json"]) == _json(files["sources-after-v1.json"]))
    result = _json(files["result-v1.json"])
    _need(result["passed"] is True and result["sources_equal"] is True and build_verification.owner_ok(result))
    summaries = _json(files["test-summary-v1.json"])
    _need(len(summaries) == 58 and len({item["name"] for item in summaries}) == 58)
    total = 0
    for item in summaries:
        root = ET.parse(files["reports/" + item["name"]]["path"]).getroot()
        for key in ("tests", "failures", "errors", "skipped"):
            _need(type(item[key]) is int and item[key] == int(root.attrib[key]))
        _need(all(item[key] == 0 for key in ("failures", "errors", "skipped")))
        total += item["tests"]
    _need(total == 588)
    lint = value["fresh_lint_files"]
    lint_request = _json(lint["request-v1.json"])
    _need(lint_request["sources"] == current == _json(lint["sources-after-v1.json"]) and
          _json(lint["result-v1.json"])["passed"] is True and
          _json(lint["litert-analyzer-audit.json"])["analysis_did_work"] is True)
    _need(not any(issue.attrib.get("severity") in ("Error", "Fatal") for issue in
                  ET.parse(lint["lint-results-debug.xml"]["path"]).getroot()))
    _need(len(value["apks"]) == 2)
    for apk, package, key in zip(value["apks"], (contract.APP, contract.TEST), ("product_apk", "test_apk")):
        _need(apk["package"] == package and {name: apk[name] for name in ("path", "bytes", "sha256")} == admission["artifacts"][key])
        _check_binding(admission["artifacts"][key])
    _verify_process_probe_build(value["process_probe_build"], admission)
    return value


def _verify_inputs(admission_binding, running_binding, build_binding):
    admission = contract.validate_admission(_json(admission_binding))
    contract.validate_running(_json(running_binding), admission, admission_binding)
    _need(admission["artifacts"]["build"] == build_binding)
    contract.revalidate_inputs(admission)
    manifest = _verify_build(build_binding, admission)
    for key in ("model", "probe", "process_probe", "process_probe_source"):
        _check_binding(admission["artifacts"][key])
    _need(admission["artifacts"]["model"]["bytes"] == contract.MODEL_BYTES and
          admission["artifacts"]["model"]["sha256"] == contract.MODEL_SHA256 and
          admission["artifacts"]["process_probe_source"] == env.binding(ROOT / "benchmarks/native/android_author_process_probe.c"))
    return admission, manifest


def _write(path, raw):
    _need(len(raw) <= 4 * 1024 * 1024)
    with path.open("xb") as stream:
        _need(stream.write(raw) == len(raw))
        stream.flush()
        os.fsync(stream.fileno())


def _record(cap):
    return env.binding(cap.directory / ("command-%04d.json" % cap.count))


def _shell(cap, live, argv, label, *, seconds=20, limit=131072):
    live.guard()
    raw = cap.shell(argv, label, seconds=seconds, cap=limit)
    live.guard()
    return raw, _record(cap)


def _package(cap, live, package):
    raw, witness = _shell(cap, live, ["cmd", "package", "list", "packages", "-U", "--user", "0", package], "package")
    values = {}
    lines = raw.decode("ascii").splitlines()
    _need(len(lines) <= 2)
    for line in lines:
        match = re.fullmatch(r"package:([^\s]+) uid:([1-9][0-9]*)", line)
        _need(match is not None and match[1] in (contract.APP, contract.TEST) and match[1] not in values)
        uid = int(match[2])
        _need(10000 <= uid <= 2147483647)
        values[match[1]] = uid
    return values.get(package), witness


def _installed(cap, live, manifest, expected=None):
    identities, checks = {}, {}
    for key, apk in zip(("product", "tests"), manifest["apks"]):
        package = apk["package"]
        uid, uid_pin = _package(cap, live, package)
        _need(uid is not None)
        raw, path_pin = _shell(cap, live, ["cmd", "package", "path", "--user", "0", package], "package-path")
        path = raw.decode("ascii").strip()
        _need(path.startswith("package:/data/app/") and path.endswith("/base.apk") and "\n" not in path)
        actual_path = path[len("package:"):]
        raw, hash_pin = _shell(cap, live, ["sha256sum", actual_path], "package-hash")
        _need(raw.decode("ascii").strip() == apk["sha256"] + "  " + actual_path)
        identities[package] = uid
        checks[key] = dict(uid=uid_pin, path=path_pin, sha256=hash_pin)
    _need(len(set(identities.values())) == 2 and (expected is None or identities == expected))
    return identities, checks


def _run_as(cap, live, argv, label, *, limit=131072):
    return _shell(cap, live, ["run-as", contract.APP, "--user", "0", *argv], label, limit=limit)


def _hashes(cap, live, paths, label):
    raw, _ = _run_as(cap, live, ["sha256sum", *paths], label, limit=16384)
    values = {}
    for line in raw.decode("ascii").splitlines():
        match = re.fullmatch(r"([0-9a-f]{64})  (no_backup/[A-Za-z0-9_./-]+)", line)
        _need(match is not None and match[2] in paths and match[2] not in values)
        values[match[2]] = match[1]
    _need(set(values) == set(paths))
    return values


def _collect(folder, cap, live, uid, remote, names):
    folder.mkdir()
    raw, _ = _run_as(cap, live, ["ls", remote], "artifact-list", limit=16384)
    listed = raw.decode("ascii").splitlines()
    directories = {"workspace-v1", "archive-staging"} if remote == "no_backup/original-author-proof-v1" else (
        {"archive-staging"} if remote == "no_backup/original-author-restart-proof-v1" else set())
    _need(len(listed) == len(set(listed)) and set(listed) == set(names) | directories)
    paths = [remote + "/" + name for name in names]
    before = _hashes(cap, live, paths, "artifact-hash")
    packed, _ = _run_as(cap, live, ["tar", "-cf", "-", *paths], "artifact-tar", limit=4 * 1024 * 1024)
    result = {}
    with tarfile.open(fileobj=io.BytesIO(packed), mode="r:") as archive:
        members = archive.getmembers()
        _need(len(members) == len(paths) and {item.name for item in members} == set(paths))
        for item in members:
            _need(item.isfile() and not item.islnk() and not item.issym() and item.uid == uid and
                  0 < item.size <= author_proof.MAX_ARTIFACT)
            stream = archive.extractfile(item)
            _need(stream is not None)
            raw = stream.read(author_proof.MAX_ARTIFACT + 1)
            _need(len(raw) == item.size and hashlib.sha256(raw).hexdigest() == before[item.name])
            name = item.name.rsplit("/", 1)[1]
            _write(folder / name, raw)
            result[name] = raw
    _need(sum(map(len, result.values())) <= author_proof.MAX_COLLECTED + author_proof.MAX_ARTIFACT)
    _need(_hashes(cap, live, paths, "artifact-post-hash") == before)
    return result


def _resources(cap, live):
    raw, _ = _shell(cap, live, ["df", "-k", "/data"], "guest-storage", limit=16384)
    lines = raw.decode("ascii").splitlines()
    _need(len(lines) == 2 and lines[0].split() == ["Filesystem", "1K-blocks", "Used", "Available", "Use%", "Mounted", "on"])
    row = lines[1].split()
    _need(len(row) == 6 and row[3].isdigit() and row[-1] in ("/data", "/data/user/0") and
          int(row[3]) * 1024 >= 2 * contract.MODEL_BYTES + 2 * 1024 ** 3)
    raw, _ = _shell(cap, live, ["cat", "/proc/meminfo"], "guest-memory", limit=16384)
    values = [line for line in raw.decode("ascii").splitlines() if line.startswith("MemAvailable:")]
    _need(len(values) == 1 and re.fullmatch(r"MemAvailable:\s+([0-9]+) kB", values[0]) is not None and
          int(values[0].split()[1]) * 1024 >= 4 * 1024 ** 3)


def _instrument(cap, live, index):
    if index < 2:
        klass, method = contract.CLASS, contract.METHODS[index]
    else:
        klass = "org.locallore.app.OriginalAuthorRestartInstrumentedTest"
        method = "recordsOriginalAuthorAfterExternalRestartWithoutInference"
    raw, witness = _shell(cap, live, ["am", "instrument", "-w", "-r", "-e", "class", klass + "#" + method,
                                    contract.TEST + "/androidx.test.runner.AndroidJUnitRunner"],
                          "instrument-" + str(index), seconds=210, limit=262144)
    validate_instrumentation(raw, klass, [method])
    return witness


def _probe(cap, live, mode, pid=None, uid=None):
    argv = [PROCESS_PROBE, "--boot"] if mode == "boot" else [PROCESS_PROBE, "--snapshot", str(pid), str(uid)]
    raw, witness = _shell(cap, live, argv, "process-" + mode, limit=4096)
    return verification.parse_probe(raw, mode, pid=pid, uid=uid), witness


def _checkpoint(request, live):
    for key in ("admission", "running", "build", "controller"):
        _check_binding(request[key])
    _need(request["sources"] == contract.source_bindings())
    live.guard()


def run(admission_binding, running_binding, build_binding, output_root):
    """No outer process or scope grant. An authorized finite caller owns execution."""
    begin = time.monotonic()
    output = env.safe_path(output_root, exists=False)
    _need(output.is_absolute() and output.drive.upper() == "D:" and not os.path.lexists(output))
    output.mkdir()
    request_pin = session_pin = prerequisite_pin = restart_instrumentation = boot_final = restart_pin = None
    restart_artifacts = {name: None for name in RECORDS}
    live = cap = None
    phase, reason, outcome = "admission", "checks_failed", "refused"
    observer_closed = None
    try:
        admission, manifest = _verify_inputs(admission_binding, running_binding, build_binding)
        request = dict(version=1, protocol=REQUEST_PROTOCOL, admission=copy.deepcopy(admission_binding),
                       running=copy.deepcopy(running_binding), build=copy.deepcopy(build_binding), root=str(output),
                       head=manifest["head"], sources=contract.source_bindings(), python=copy.deepcopy(admission["python"]),
                       controller=env.binding(Path(__file__).resolve()), seconds=SECONDS)
        env.create_json(output / "request-v1.json", request)
        request_pin = env.binding(output / "request-v1.json")
        live = LiveOwnedRestartTarget(admission_binding, running_binding)
        _need(type(live) is LiveOwnedRestartTarget)
        cap = OwnedRestartSdkCapture(output / "clients", SECONDS, live)
        _need(type(cap) is OwnedRestartSdkCapture)
        session_pin = cap.session_binding
        _checkpoint(request, live)
        until = time.monotonic() + 120
        for _ in range(40):
            raw, _ = _shell(cap, live, ["getprop", "sys.boot_completed"], "boot")
            if raw.strip() == b"1":
                break
            _need(time.monotonic() < until, "deadline")
            time.sleep(2)
        _need(raw.strip() == b"1")
        raw, _ = _shell(cap, live, ["am", "get-current-user"], "user")
        _need(raw.strip() == b"0")
        for key, expected in (("ro.build.version.sdk", b"35"), ("ro.product.cpu.abi", b"x86_64"), ("ro.kernel.qemu", b"1")):
            raw, _ = _shell(cap, live, ["getprop", key], "property")
            _need(raw.strip() == expected)
        for package in (contract.APP, contract.TEST):
            _need(_package(cap, live, package)[0] is None)
        _resources(cap, live)
        phase = "install"
        for key, path in (("product_apk", "/data/local/tmp/locallore-product-v1.apk"),
                          ("test_apk", "/data/local/tmp/locallore-test-v1.apk"), ("process_probe", PROCESS_PROBE)):
            pin = admission["artifacts"][key]
            cap.stream(["dd", "of=" + path, "bs=65536"], pin, "process-stage" if key == "process_probe" else "apk-stage", seconds=120)
            raw, _ = _shell(cap, live, ["sha256sum", path], "staged-hash")
            _need(raw.decode("ascii").strip() == pin["sha256"] + "  " + path)
            if key == "process_probe":
                raw, _ = _shell(cap, live, ["chmod", "700", path], "process-mode")
                _need(raw == b"")
            else:
                raw, _ = _shell(cap, live, ["pm", "install", "-r", "-t", "--user", "0", path], "install", seconds=120)
                _need(raw.strip() == b"Success")
        uids, _ = _installed(cap, live, manifest)
        uid = uids[contract.APP]
        initial, boot_initial = _probe(cap, live, "boot")
        _run_as(cap, live, ["mkdir", "-p", "no_backup/original-author-source-v1"], "source-directory")
        phase = "binary_probe"
        probe_path = "no_backup/original-author-transfer-probe-v1.bin"
        cap.stream(["run-as", contract.APP, "--user", "0", "dd", "of=" + probe_path, "bs=65536"],
                   admission["artifacts"]["probe"], "binary-probe")
        _need(_hashes(cap, live, [probe_path], "probe-hash")[probe_path] == admission["artifacts"]["probe"]["sha256"])
        phase = "model_transfer"
        model_path = "no_backup/original-author-source-v1/model.litertlm"
        cap.stream(["run-as", contract.APP, "--user", "0", "dd", "of=" + model_path, "bs=65536"],
                   admission["artifacts"]["model"], "model-transfer", seconds=240)
        _need(_hashes(cap, live, [model_path], "model-hash")[model_path] == contract.MODEL_SHA256)
        _checkpoint(request, live)
        phase = "import"
        import_instrumentation = _instrument(cap, live, 0)
        imported_files = _collect(output / "import-proof", cap, live, uid, "no_backup/original-author-import-proof-v1", ("import-v1.json",))
        imported = author_proof.validate_import(imported_files["import-v1.json"])
        _need(imported["process"]["uid"] == uid)
        raw, _ = _shell(cap, live, ["am", "force-stop", "--user", "0", contract.APP], "import-force-stop")
        _need(raw == b"")
        _installed(cap, live, manifest, uids)
        _checkpoint(request, live)
        phase = "author"
        author_instrumentation = _instrument(cap, live, 1)
        names = ("proof-v1.json", *author_proof.RECORDS, *author_proof.TRACES)
        authored_files = _collect(output / "author-proof", cap, live, uid, "no_backup/original-author-proof-v1", names)
        diagnostics = _collect(output / "diagnostic-proof", cap, live, uid, "no_backup/original-author-diagnostic-v1", ("diagnostic-v1.json", *diagnostic.FILES))
        baseline = {name: authored_files[name] for name in author_proof.RECORDS + author_proof.TRACES}
        authored = author_proof.validate_author(authored_files["proof-v1.json"], baseline, imported_files["import-v1.json"], expected_prompt_version="initial-world-v1.1")
        diagnostic.validate_diagnostic(diagnostics["diagnostic-v1.json"], {name: diagnostics[name] for name in diagnostic.FILES},
                                       authored_files["proof-v1.json"], baseline, imported_files["import-v1.json"], expected_prompt_version="initial-world-v1.1")
        _need(authored["process"]["uid"] == uid)
        phase = "death"
        _, package_checks = _installed(cap, live, manifest, uids)
        pid = authored["process"]["pid"]
        before, probe_before = _probe(cap, live, "snapshot", pid, uid)
        _need(before["boot_id"] == initial["boot_id"])
        raw, force_stop = _shell(cap, live, ["am", "force-stop", "--user", "0", contract.APP], "author-force-stop")
        _need(raw == b"")
        after, probe_after = _probe(cap, live, "snapshot", pid, uid)
        _need(after["boot_id"] == initial["boot_id"] and after["state"] in ("absent", "exited"))
        if after["state"] == "exited" and before["start_ticks"] is not None:
            _need(after["start_ticks"] == before["start_ticks"])
        prerequisite = dict(version=1, protocol="original-author-restart-prerequisite-v1", admission=admission_binding,
                            running=running_binding, session=session_pin, caller=copy.deepcopy(live.caller),
                            import_proof=env.binding(output / "import-proof/import-v1.json"),
                            author_proof=env.binding(output / "author-proof/proof-v1.json"),
                            author_artifacts={name: env.binding(output / "author-proof" / name) for name in author_proof.RECORDS + author_proof.TRACES},
                            import_instrumentation=import_instrumentation, author_instrumentation=author_instrumentation,
                            boot_initial=boot_initial, probe_before=probe_before, force_stop=force_stop, probe_after=probe_after,
                            package_checks=package_checks)
        destination = Path(admission["root"]) / "restart-prerequisite-v1.json"
        pending = destination.with_name("restart-prerequisite.pending-v1.json")
        env.create_json(pending, prerequisite)
        pending.rename(destination)  # Windows create-only atomic publication; no replacement or repair.
        prerequisite_pin = env.binding(destination)
        verification.verify_restart_prerequisite(prerequisite_pin, admission, admission_binding, running_binding, live.caller)
        _checkpoint(request, live)
        phase = "restart"
        restart_instrumentation = _instrument(cap, live, 2)
        phase = "collect"
        restarted_files = _collect(output / "restart-proof", cap, live, uid, "no_backup/original-author-restart-proof-v1", ("proof-v1.json", *RECORDS))
        restart_pin = env.binding(output / "restart-proof/proof-v1.json")
        restart_artifacts = {name: env.binding(output / "restart-proof" / name) for name in RECORDS}
        restart_proof.validate_restart(restarted_files["proof-v1.json"], {name: restarted_files[name] for name in RECORDS},
                                       authored_files["proof-v1.json"], baseline, imported_files["import-v1.json"], expected_prompt_version="initial-world-v1.1")
        final, boot_final = _probe(cap, live, "boot")
        _need(final["boot_id"] == initial["boot_id"])
        _checkpoint(request, live)
        phase, reason, outcome = "completed", None, "completed"
    except BaseException as error:
        reason = "deadline" if isinstance(error, TimeoutError) or str(error) in ("deadline", "expired") else "checks_failed"
        outcome = "refused"
    finally:
        count = 0 if cap is None else cap.count
        if cap is not None:
            if cap.clean:
                try:
                    verification.require_current_clients(output, count, cap.session_binding, admission)
                except BaseException:
                    outcome, reason = "refused", "checks_failed"
            else:
                outcome, reason = "refused", "resource_uncertain"
            try:
                cap.close()
            except BaseException:
                outcome, reason = "refused", "resource_uncertain"
        if live is not None:
            try:
                observed = live.close()
                observer_closed = observed if type(observed) is bool else None
            except BaseException:
                observer_closed = None
            if observer_closed is not True:
                outcome, reason = "refused", "resource_uncertain"
        # File-only retention of any actually copied partial restart evidence; no new target call.
        for name in ("proof-v1.json", *RECORDS):
            path = output / "restart-proof" / name
            if os.path.lexists(path):
                try:
                    pin = env.binding(path)
                    if name == "proof-v1.json":
                        restart_pin = pin
                    else:
                        restart_artifacts[name] = pin
                except BaseException:
                    outcome, reason = "refused", "resource_uncertain"
        result = dict(version=1, protocol=RESULT_PROTOCOL, request=request_pin, session=session_pin,
                      prerequisite=prerequisite_pin, restart_instrumentation=restart_instrumentation,
                      boot_final=boot_final, restart_proof=restart_pin, restart_artifacts=restart_artifacts,
                      client_count=count, outcome=outcome, phase=phase, reason=reason,
                      observer_handles_closed=observer_closed, feature_acceptance=False,
                      elapsed_ms=round(max(0, time.monotonic() - begin) * 1000))
        env.create_json(output / "controller-result-v1.json", result)
    return copy.deepcopy(result)
