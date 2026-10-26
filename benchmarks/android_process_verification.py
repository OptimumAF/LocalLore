"""Opt-in Windows host checks for the isolated scripted process-test APKs.

Copyright 2026 LocalLore contributors. SPDX-License-Identifier: Apache-2.0

Create-only private evidence; no phone, model, server lifecycle or task adoption.
The component phase does not qualify the external two-death controller case.
"""
import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import threading
import time
import xml.etree.ElementTree as ET

try:
    from benchmarks import receipt_avd_environment as env
except ModuleNotFoundError:
    import receipt_avd_environment as env

ROOT = Path(__file__).resolve().parents[1]
APP = "org.locallore.app.draftprocessverify"
CONTROL = "org.locallore.app.draftprocesscontroller"
CLASSES = ("RetiredSelectionFixtureInstrumentedTest",
           "RetainedParentFixtureInstrumentedTest", "RetainedParentFallbackNativeTest")
EXPECTED_METHODS = (
    ("loadModeFindsStoredApkLibraryUnderActualProductUidWithoutOpeningWorkspace",
     "wrongUidRefusesBeforeNativeOrWorkspaceAccess", "wrongApkHashRefusesBeforeNativeOrWorkspaceAccess",
     "writableOrAlternateNativeDirectoryCannotReplacePinnedApkZipPath"),
    ("loadModeFindsRetainedParentWorkerWithoutOpeningWorkspace",
     "wrongUidOrFixedRetainedArgumentsRefuseBeforeNativeAccess",
     "wrongApkHashRefusesRetainedParentWorkerBeforeNativeAccess",
     "alternateNativeDirectoryCannotReplaceRetainedParentApkPath"),
    ("parentRetirementFallsBackOnceAndPreservesOriginalGrandchildReceipts",
     "cachedParentReadyIsClosedWhileRetainedChildReadyCommitsExactlyOnce"))
PACKAGES = (APP, APP + ".test", CONTROL)
APK_PATHS = ("app/build-input-process/outputs/apk/debug/app-debug.apk",
             "app/build-input-process/outputs/apk/androidTest/debug/app-debug-androidTest.apk",
             "draft-process-controller/build/outputs/apk/debug/draft-process-controller-debug.apk")
TASKS = (":draft-process-controller:clean", ":app:cleanTestDebugUnitTest",
         ":app:testDebugUnitTest", ":app:lintDebug", ":app:assembleDebug",
         ":app:assembleDebugAndroidTest", ":draft-process-controller:assembleDebug",
         ":draft-process-controller:lintDebug")
MAX_COMMAND_BYTES = 4 * 1024 ** 2
AUDIT_LABELS = ("product-audit", "controller-audit", *(
    label + "-" + str(index) for index in range(3) for label in ("signature", "badging", "manifest")))


class VerificationRefused(RuntimeError):
    pass


def need(value, reason):
    if not value:
        raise VerificationRefused(reason)


def output_path(path):
    path = Path(path)
    env.safe_path(path, exists=False)
    env.safe_path(path.parent, directory=True)
    need(not path.exists() and not path.is_relative_to(ROOT), "evidence_destination")
    return path


def source_map():
    """Tracked build/test inputs, never ignored caches or private model outputs."""
    raw = subprocess.check_output(["git", "ls-files", "-z"], cwd=ROOT)
    names = raw.decode("utf-8").split("\0")
    suffixes = {".rs", ".toml", ".lock", ".kt", ".java", ".xml", ".json", ".py",
                ".kts", ".properties", ".jar", ".bat", ".txt"}
    return {name: env.digest(ROOT / name) for name in sorted(names) if name and
            ((Path(name).suffix in suffixes and name.startswith(("apps/android/", "crates/",
                    "fixtures/", "scripts/", "benchmarks/"))) or
             name in ("Cargo.toml", "Cargo.lock", "rust-toolchain.toml"))}


def run_command(out, label, command, cwd, variables):
    """Children belong to the enclosing supervisor job; bytes use explicit handles."""
    need(re.fullmatch(r"[a-z0-9-]{1,60}", label), "command_label")
    stdout = out / (label + ".stdout.raw")
    stderr = out / (label + ".stderr.raw")
    lock = threading.Lock()
    failed, overflow = threading.Event(), threading.Event()
    count = [0]
    sinks = []
    try:
        for path in (stdout, stderr):
            target = path.open("xb", buffering=0)
            sinks.append(target)
            target.flush()
            os.fsync(target.fileno())
        process = subprocess.Popen(command, cwd=cwd, env=variables, stdin=subprocess.DEVNULL,
                                   stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                                   creationflags=subprocess.CREATE_NO_WINDOW)
    except BaseException:
        for target in sinks:
            target.close()
        raise
    def drain(stream, target):
        try:
            with target:
                while True:
                    raw = stream.read1(4096)
                    if not raw:
                        break
                    with lock:
                        left = MAX_COMMAND_BYTES - count[0]
                        piece = raw[:left]
                        need(target.write(piece) == len(piece), "short_write")
                        count[0] += len(piece)
                        if len(raw) > left:
                            overflow.set()
                            break
                target.flush()
                os.fsync(target.fileno())
        except BaseException:
            failed.set()
    threads = [threading.Thread(target=drain, args=pair, daemon=True) for pair in
               ((process.stdout, sinks[0]), (process.stderr, sinks[1]))]
    for thread in threads:
        thread.start()
    deadline = time.monotonic() + 600
    timed_out = False
    try:
        while True:
            if failed.is_set() or overflow.is_set():
                break
            if time.monotonic() >= deadline:
                timed_out = True
                break
            if process.poll() is not None and not any(thread.is_alive() for thread in threads):
                break
            time.sleep(.01)
    finally:
        if process.poll() is None:
            process.kill()
        process.wait(timeout=5)
        for thread in threads:
            thread.join(timeout=2)
    complete = not any(thread.is_alive() for thread in threads) and not failed.is_set()
    # A failed worker exits so its enclosing job closes every descendant.
    # A direct-child exit alone never establishes tree or capture closure.
    need(complete, "command_capture_incomplete")
    process.stdout.close()
    process.stderr.close()
    record = {"version": 1, "label": label, "returncode": process.returncode,
              "capture_complete": complete, "output_limit": overflow.is_set(),
              "timed_out": timed_out,
              "stdout": env.binding(stdout), "stderr": env.binding(stderr)}
    env.create_json(out / (label + ".json"), record)
    need(not timed_out and not overflow.is_set() and process.returncode == 0, "command_failed")
    return stdout.read_bytes()


def build_worker(request, out):
    sdk = env.safe_path(request["sdk"], directory=True)
    java = env.safe_path(request["java"], directory=True)
    variables = dict(os.environ)
    for key in ("JAVA_TOOL_OPTIONS", "_JAVA_OPTIONS", "JDK_JAVA_OPTIONS", "GRADLE_OPTS", "JAVA_OPTS"):
        variables.pop(key, None)
    variables.update(JAVA_HOME=str(java), ANDROID_HOME=str(sdk), ANDROID_SDK_ROOT=str(sdk),
                     CARGO_NET_OFFLINE="true", CARGO_BUILD_JOBS="2")
    variables["PATH"] = str(java / "bin") + os.pathsep + variables.get("PATH", "")
    command = [str(java / "bin/java.exe"), "-classpath",
               str(ROOT / "apps/android/gradle/wrapper/gradle-wrapper.jar"),
               "org.gradle.wrapper.GradleWrapperMain", "--offline", "--no-daemon", "--no-build-cache",
               "--max-workers=2", "--console=plain", "--project-cache-dir", ".gradle-input-process",
               "-PlocalLoreInputDraftVerification=true", "-PlocalLoreInputProcessVerification=true", *TASKS]
    run_command(out, "gradle", command, ROOT / "apps/android", variables)
    apks = out / "apks"
    apks.mkdir()
    bindings = []
    for package, relative in zip(PACKAGES, APK_PATHS):
        target = apks / (package + ".apk")
        source = env.safe_path(ROOT / "apps/android" / relative)
        with source.open("rb") as src, target.open("xb") as dst:
            shutil.copyfileobj(src, dst)
            dst.flush()
            os.fsync(dst.fileno())
        need(env.digest(source) == env.digest(target), "apk_copy_changed")
        bindings.append(dict(env.binding(target), package=package))
    tool = sdk / "build-tools/35.0.0"
    run_command(out, "product-audit", [sys.executable, "-B", str(ROOT / "scripts/audit_apk.py"),
                bindings[0]["path"], "--input-process-verification"], ROOT, variables)
    run_command(out, "controller-audit", [sys.executable, "-B", str(ROOT / "scripts/audit_process_controller.py"),
                bindings[2]["path"]], ROOT, variables)
    for index, binding in enumerate(bindings):
        run_command(out, "signature-" + str(index), [str(java / "bin/java.exe"), "-jar",
                    str(tool / "lib/apksigner.jar"), "verify", "--verbose", "--print-certs", binding["path"]], ROOT, variables)
        raw = run_command(out, "badging-" + str(index), [str(tool / "aapt2.exe"), "dump", "badging", binding["path"]], ROOT, variables)
        need(("package: name='" + binding["package"] + "'").encode() in raw, "apk_package")
        run_command(out, "manifest-" + str(index), [str(tool / "aapt2.exe"), "dump", "xmltree",
                    binding["path"], "--file", "AndroidManifest.xml"], ROOT, variables)
    reports = out / "reports"
    reports.mkdir()
    summaries = []
    folder = ROOT / "apps/android/app/build-input-process/test-results/testDebugUnitTest"
    for source in sorted(folder.glob("TEST-*.xml")):
        tree = ET.parse(source).getroot()
        counts = {key: int(tree.attrib[key]) for key in ("tests", "failures", "errors", "skipped")}
        need(counts["tests"] > 0 and not any(counts[key] for key in ("failures", "errors", "skipped")), "unit_results")
        shutil.copyfile(source, reports / source.name)
        summaries.append(dict(name=source.name, **counts))
    need(summaries, "missing_unit_results")
    for name, relative in (("app-lint.xml", "app/build-input-process/reports/lint-results-debug.xml"),
                           ("controller-lint.xml", "draft-process-controller/build/reports/lint-results-debug.xml")):
        source = ROOT / "apps/android" / relative
        issues = ET.parse(source).getroot().findall("issue")
        need(not any(issue.attrib.get("severity") in ("Error", "Fatal") for issue in issues), "lint_errors")
        shutil.copyfile(source, reports / name)
    env.create_json(out / "artifacts-v1.json", {"version": 1, "apks": bindings, "unit_results": summaries,
                    "artifact_command_count": 11, "build_profile": "input-process",
                    "commands": [env.binding(out / (label + ".json")) for label in AUDIT_LABELS],
                    "gradle": env.binding(out / "gradle.json"),
                    "reports": [env.binding(path) for path in sorted(reports.iterdir())]})


def checked_apks(path):
    document = env.read_json(path)
    need(document.get("version") == 1 and document.get("build_profile") == "input-process", "artifact_manifest")
    apks = document.get("apks")
    need(type(apks) is list and len(apks) == 3 and [p.get("package") for p in apks] == list(PACKAGES), "artifact_packages")
    for apk in apks:
        env.check_binding({key: apk[key] for key in ("path", "bytes", "sha256")})
    return document


def owner_ok(owner):
    return (type(owner) is dict and owner.get("status") == "child_exited" and
            type(owner.get("worker_returncode")) is int and owner["worker_returncode"] == 0 and
            owner.get("cleanup_complete") is True and owner.get("output_capture_complete") is True)


def bound_json(binding, expected):
    need(binding["path"] == str(expected), "record_path")
    env.check_binding(binding)
    return env.read_json(binding["path"])


def command_stdout(binding, out, label):
    record = bound_json(binding, out / (label + ".json"))
    need(record.get("label") == label and type(record.get("returncode")) is int and
         record["returncode"] == 0 and record.get("capture_complete") is True and
         record.get("output_limit") is False and record.get("timed_out") is False, "command_not_qualified")
    for channel in ("stdout", "stderr"):
        need(record[channel]["path"] == str(out / (label + "." + channel + ".raw")), "command_path")
        env.check_binding(record[channel])
    need(record["stdout"]["bytes"] + record["stderr"]["bytes"] <= MAX_COMMAND_BYTES, "command_output_bounds")
    return Path(record["stdout"]["path"]).read_bytes()


def qualified_build(path):
    """Reject a passed label, partial records or stale maps before any install."""
    path = Path(path)
    need(path.name == "result-v1.json", "build_result_path")
    return validate_build_record(env.read_json(path), path.parent)


def validate_build_record(build, out):
    need(type(build) is dict and build.get("version") == 1 and build.get("phase") == "build" and
         build.get("passed") is True and owner_ok(build.get("owner")), "build_not_qualified")
    need(bound_json(build["owner_record"], out / "owner-result-v1.json") == build["owner"], "owner_record")
    request = bound_json(build["request"], out / "request-v1.json")
    need(request["phase"] == "build" and Path(request["out"]) == out and
         request["inputs"] == input_bindings(request) and request["sources"] == build["sources_before"] and
         request["driver_sha256"] == env.digest(Path(__file__)), "build_inputs")
    before = bound_json(build["sources_before"], out / "sources-before-v1.json")
    after = bound_json(build["sources_after"], out / "sources-after-v1.json")
    need(before == after == source_map(), "source_drift")
    bound_json(build["artifacts"], out / "artifacts-v1.json")
    artifact = checked_apks(build["artifacts"]["path"])
    need(len(artifact["commands"]) == len(AUDIT_LABELS) and artifact["artifact_command_count"] == 11, "audit_roster")
    outputs = {label: command_stdout(binding, out, label) for label, binding in zip(AUDIT_LABELS, artifact["commands"])}
    for label in ("product-audit", "controller-audit"):
        need(json.loads(outputs[label])["status"] == "passed", "artifact_audit")
    certificates = []
    for index, package in enumerate(PACKAGES):
        need(("package: name='" + package + "'").encode() in outputs["badging-" + str(index)], "apk_package")
        signatures = outputs["signature-" + str(index)].decode("utf-8")
        certs = re.findall(r"^Signer #1 certificate SHA-256 digest: ([0-9a-fA-F]{64})\r?$", signatures, re.M)
        need(len(certs) == 1 and "Number of signers: 1" in signatures, "apk_signer")
        certificates.append(certs[0].lower())
    need(len(set(certificates)) == 1, "apk_signer_mismatch")
    test_manifest = outputs["manifest-1"].decode("utf-8")
    targets = re.findall(r'^\s*A: android:targetPackage(?:\([^)]+\))?="([^"]+)"', test_manifest, re.M)
    names = re.findall(r'^\s*A: android:name(?:\([^)]+\))?="([^"]+)"', test_manifest, re.M)
    need(targets == [APP] and names.count("androidx.test.runner.AndroidJUnitRunner") == 1, "test_instrumentation")
    gradle = command_stdout(artifact["gradle"], out, "gradle").decode("utf-8")
    need("BUILD SUCCESSFUL" in gradle and re.search(r"^> Task :app:testDebugUnitTest[ \t\r]*$", gradle, re.M), "unit_not_executed")
    names = set()
    for binding in artifact["reports"]:
        report = Path(binding["path"])
        need(report.parent == out / "reports" and report.name not in names, "report_path")
        names.add(report.name)
        env.check_binding(binding)
        tree = ET.parse(report).getroot()
        if report.name.startswith("TEST-"):
            need(int(tree.attrib["tests"]) == len(tree.findall("testcase")) and int(tree.attrib["tests"]) > 0 and
                 all(int(tree.attrib[key]) == 0 for key in ("failures", "errors", "skipped")), "unit_results")
        else:
            need(report.name in ("app-lint.xml", "controller-lint.xml") and
                 not any(i.attrib.get("severity") in ("Error", "Fatal") for i in tree.findall("issue")), "lint_results")
    need({"app-lint.xml", "controller-lint.xml"} < names, "report_roster")
    return artifact


def input_bindings(request):
    paths = []
    if request["phase"] == "build":
        paths = [Path(request["java"]) / "bin/java.exe",
                 Path(request["sdk"]) / "build-tools/35.0.0/aapt2.exe",
                 Path(request["sdk"]) / "build-tools/35.0.0/lib/apksigner.jar"]
    else:
        paths = [Path(request[key]) for key in ("build", "running", "proposal", "server", "powershell")]
        paths.append(Path(request["sdk"]) / "platform-tools/adb.exe")
    return [env.binding(path) for path in paths]


def validate_component_record(components, out):
    try:
        from benchmarks.android_instrumentation_evidence import validate_instrumentation
    except ModuleNotFoundError:
        from android_instrumentation_evidence import validate_instrumentation
    need(type(components) is dict and set(components) == {"version", "results", "clients", "clients_clean",
         "method_count", "external_controller_case_executed"} and type(components["version"]) is int and
         components["version"] == 1 and components["method_count"] == 10 and components["clients_clean"] is True and
         components["external_controller_case_executed"] is False and type(components["clients"]) is int and
         0 < components["clients"] <= 10000 and len(components["results"]) == 3, "components_not_qualified")
    for result, name, expected in zip(components["results"], CLASSES, EXPECTED_METHODS):
        need(result["class"] == "org.locallore.app." + name and result["method_count"] == len(expected) and
             sorted(result["methods"]) == sorted(expected), "component_roster_changed")
        raw = (out / (name + ".stdout.raw")).read_bytes()
        need(validate_instrumentation(raw, result["class"], result["methods"]) == result, "component_raw_mismatch")
    for index in range(1, components["clients"] + 1):
        stem = out / "clients" / ("command-%04d" % index)
        record = env.read_json(stem.with_suffix(".json"))
        need(record["index"] == index and record["status"] == "completed" and
             type(record["returncode"]) is int and record["returncode"] == 0 and
             record["stderr_bytes"] == 0 and record["cleanup_complete"] is True, "client_not_qualified")
        data = stem.with_suffix(".stdout.bin").read_bytes()
        need(len(data) == record["stdout_bytes"] and hashlib.sha256(data).hexdigest() == record["stdout_sha256"], "client_raw_changed")


def component_worker(request, out):
    try:
        from benchmarks.android_process_client import SdkCapture
        from benchmarks.android_instrumentation_evidence import test_roster, validate_instrumentation
    except ModuleNotFoundError:
        from android_process_client import SdkCapture
        from android_instrumentation_evidence import test_roster, validate_instrumentation
    artifact = qualified_build(request["build"])
    rosters = []
    for name, expected in zip(CLASSES, EXPECTED_METHODS):
        source = ROOT / "apps/android/app/src/androidTest/java/org/locallore/app" / (name + ".kt")
        methods = test_roster(source)
        need(sorted(methods) == sorted(expected), "component_roster_changed")
        rosters.append(methods)
    lease_path = Path(request["running"])
    live = env.open_live_owner(request["proposal"], lease_path, env.digest(lease_path))
    lease = live.descriptor
    need(lease["avd_name"] == env.NAME and lease["serial"] == "emulator-5592" and
         lease["console_port"] == 5592 and lease["guest_boot_verified"] is False, "owned_avd_profile")
    def own():
        live.check()
        need(source_map() == env.read_json(request["sources"]["path"]), "source_drift")
    own()
    server = env.read_json(request["server"])
    sdk = Path(request["sdk"])
    capture = SdkCapture(out / "clients", 850, sdk / "platform-tools/adb.exe",
                         Path(request["powershell"]), server, lease["launcher"])
    capture.check_server()
    matches = []
    for _ in range(24):
        own()
        raw = capture.capture([str(sdk / "platform-tools/adb.exe"), "-H", "127.0.0.1", "-P", "5037", "devices", "-l"], "devices")
        capture.check_server()
        matches = [line for line in raw.decode("utf-8").splitlines() if line.split()[:2] == ["emulator-5592", "device"]]
        if matches:
            break
        time.sleep(2)
    need(len(matches) == 1, "target_unavailable")
    tids = re.findall(r"\btransport_id:([1-9][0-9]*)\b", matches[0])
    need(len(tids) == 1, "transport")
    capture.target = {"transport_id": int(tids[0])}
    def shell(args, label, seconds=20, cap=131072):
        own()
        data = capture.shell(args, label, seconds, cap)
        own()
        return data
    for _ in range(24):
        if shell(["getprop", "sys.boot_completed"], "boot").strip() == b"1":
            break
        time.sleep(3)
    else:
        raise VerificationRefused("not_booted")
    for prop, value in (("ro.build.version.sdk", b"35"), ("ro.product.cpu.abi", b"x86_64")):
        need(shell(["getprop", prop], "profile-" + prop.replace(".", "-")).strip() == value, "guest_profile")
    need(shell(["am", "get-current-user"], "user").strip() == b"0", "user_zero")
    for package in PACKAGES:
        need(not shell(["cmd", "package", "list", "packages", "-U", "--user", "0", package], "absent-" + package.replace(".", "-")).strip(), "package_exists")
    for apk in artifact["apks"]:
        own()
        env.check_binding({key: apk[key] for key in ("path", "bytes", "sha256")})
        need(shell(["am", "get-current-user"], "install-user").strip() == b"0", "user_zero")
        need(capture.adb(["install", "--user", "0", "-t", apk["path"]], "install", 120).strip().endswith(b"Success"), "install_failed")
        own()
        raw = shell(["cmd", "package", "path", apk["package"]], "installed-path").decode().strip()
        need(raw.startswith("package:/data/app/") and raw.endswith("/base.apk") and "\n" not in raw, "installed_path")
        need(shell(["sha256sum", raw[len("package:"):]], "installed-hash").decode().split()[0] == apk["sha256"], "installed_hash")
    results = []
    for name, methods in zip(CLASSES, rosters):
        own()
        need(shell(["am", "get-current-user"], "instrument-user").strip() == b"0", "user_zero")
        raw = capture.adb(["exec-out", "am", "instrument", "--user", "0", "-w", "-r", "-e", "class", "org.locallore.app." + name,
                     APP + ".test/androidx.test.runner.AndroidJUnitRunner"], "instrument-" + name.lower(), 180, 262144)
        own()
        with (out / (name + ".stdout.raw")).open("xb") as stream:
            stream.write(raw)
            stream.flush()
            os.fsync(stream.fileno())
        results.append(validate_instrumentation(raw, "org.locallore.app." + name, methods))
    own()
    capture.check_server()
    env.create_json(out / "components-v1.json", {"version": 1, "results": results, "clients": capture.count,
                    "clients_clean": capture.clean, "method_count": sum(r["method_count"] for r in results),
                    "external_controller_case_executed": False})


def supervise(request):
    need(os.name == "nt", "windows_required")
    out = output_path(request["out"])
    out.mkdir()
    request = dict(request, inputs=input_bindings(request))
    before = source_map()
    env.create_json(out / "sources-before-v1.json", before)
    request = dict(request, sources=env.binding(out / "sources-before-v1.json"),
                   driver_sha256=env.digest(Path(__file__)))
    env.create_json(out / "request-v1.json", request)
    request_sha = env.digest(out / "request-v1.json")
    script_sha = env.digest(Path(__file__))
    def started(child):
        env.create_json(out / "started-v1.json", {"version": 1, "worker": env.process_identity(child.pid),
                         "request_sha256": request_sha, "driver_sha256": script_sha})
        return True
    result = env.supervise([sys.executable, "-I", "-B", str(Path(__file__)), "_worker"],
                           (str(out / "request-v1.json") + "\n" + request_sha + "\n").encode("utf-8"),
                           out, 900, started)
    env.create_json(out / "owner-result-v1.json", result)
    after = source_map()
    env.create_json(out / "sources-after-v1.json", after)
    qualified = (owner_ok(result) and before == after and
                 env.digest(Path(__file__)) == script_sha and env.digest(out / "request-v1.json") == request_sha and
                 request["inputs"] == input_bindings(request))
    record = {"version": 1, "phase": request["phase"], "passed": qualified, "owner": result,
              "owner_record": env.binding(out / "owner-result-v1.json"),
              "request": env.binding(out / "request-v1.json"),
              "sources_before": env.binding(out / "sources-before-v1.json"),
              "sources_after": env.binding(out / "sources-after-v1.json")}
    if qualified:
        name = "artifacts-v1.json" if request["phase"] == "build" else "components-v1.json"
        record["artifacts" if request["phase"] == "build" else "components"] = env.binding(out / name)
        try:
            if request["phase"] == "build":
                validate_build_record(record, out)
            else:
                components = env.read_json(out / name)
                validate_component_record(components, out)
        except (VerificationRefused, env.EnvironmentRefused, OSError, ValueError, KeyError, TypeError, ET.ParseError):
            qualified = False
            record["passed"] = False
            record["validation_refused"] = True
    env.create_json(out / "result-v1.json", record)
    need(qualified, "execution_not_qualified")
    return record


def admit_worker(request):
    need(type(request) is dict and set(request) == {"phase", "out", "sdk", "java", "build",
            "running", "proposal", "server", "powershell", "inputs", "sources", "driver_sha256"}, "request_fields")
    need(request["phase"] in ("build", "components"), "worker_phase")
    need(request["driver_sha256"] == env.digest(Path(__file__)), "driver_changed")
    env.check_binding(request["sources"])
    need(env.read_json(request["sources"]["path"]) == source_map(), "source_drift")
    need(request["inputs"] == input_bindings(request), "input_changed")


def main(argv=None):
    if argv is None and sys.argv[1:] == ["_worker"]:
        data = sys.stdin.buffer.read(4097)
        need(len(data) <= 4096, "request_bounds")
        parts = data.decode("utf-8").splitlines()
        need(len(parts) == 2 and re.fullmatch("[0-9a-f]{64}", parts[1]), "request_binding")
        path = env.safe_path(parts[0])
        need(env.digest(path) == parts[1], "request_changed")
        request = env.read_json(path)
        admit_worker(request)
        need(Path(request["out"]) == path.parent and path.name == "request-v1.json", "request_path")
        (build_worker if request["phase"] == "build" else component_worker)(request, path.parent)
        need(request["inputs"] == input_bindings(request), "input_changed")
        print("worker_completed", flush=True)
        return 0
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("phase", choices=("build", "components", "server"))
    parser.add_argument("--out", required=True)
    parser.add_argument("--sdk", required=True)
    parser.add_argument("--java")
    parser.add_argument("--build")
    parser.add_argument("--running")
    parser.add_argument("--proposal")
    parser.add_argument("--server")
    parser.add_argument("--powershell")
    args = vars(parser.parse_args(argv))
    if args["phase"] == "server":
        try:
            from benchmarks.android_process_client import observe_server
        except ModuleNotFoundError:
            from android_process_client import observe_server
        need(args["powershell"], "powershell_required")
        out = output_path(args["out"])
        out.mkdir()
        value = observe_server(Path(args["sdk"]) / "platform-tools/adb.exe", Path(args["powershell"]))
        env.create_json(out / "server-v1.json", value)
        print(json.dumps({"version": 1, "phase": "server", "passed": True}))
        return 0
    need(args["java"] if args["phase"] == "build" else all(args[k] for k in ("build", "running", "proposal", "server", "powershell")), "phase_arguments")
    supervise(args)
    print(json.dumps({"version": 1, "phase": args["phase"], "passed": True}))
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (VerificationRefused, env.EnvironmentRefused, OSError, ValueError, KeyError, TypeError):
        print(json.dumps({"version": 1, "passed": False, "reason": "verification_refused"}))
        raise SystemExit(1)
