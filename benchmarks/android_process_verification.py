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
PACKAGES = (APP, APP + ".test", CONTROL)
APK_PATHS = ("app/build-input-process/outputs/apk/debug/app-debug.apk",
             "app/build-input-process/outputs/apk/androidTest/debug/app-debug-androidTest.apk",
             "draft-process-controller/build/outputs/apk/debug/draft-process-controller-debug.apk")
TASKS = (":draft-process-controller:clean", ":app:cleanTestDebugUnitTest",
         ":app:testDebugUnitTest", ":app:lintDebug", ":app:assembleDebug",
         ":app:assembleDebugAndroidTest", ":draft-process-controller:assembleDebug",
         ":draft-process-controller:lintDebug")


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
    with stdout.open("xb") as so, stderr.open("xb") as se:
        result = subprocess.run(command, cwd=cwd, env=variables, stdout=so, stderr=se,
                                creationflags=subprocess.CREATE_NO_WINDOW)
        for stream in (so, se):
            stream.flush()
            os.fsync(stream.fileno())
    record = {"version": 1, "label": label, "returncode": result.returncode,
              "stdout": env.binding(stdout), "stderr": env.binding(stderr)}
    env.create_json(out / (label + ".json"), record)
    need(result.returncode == 0, "command_failed")
    need(stdout.stat().st_size <= 4 * 1024 ** 2 and stderr.stat().st_size <= 4 * 1024 ** 2,
         "command_output_bounds")
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
                    "artifact_command_count": 11, "build_profile": "input-process"})


def checked_apks(path):
    document = env.read_json(path)
    need(document.get("version") == 1 and document.get("build_profile") == "input-process", "artifact_manifest")
    apks = document.get("apks")
    need(type(apks) is list and len(apks) == 3 and [p.get("package") for p in apks] == list(PACKAGES), "artifact_packages")
    for apk in apks:
        env.check_binding({key: apk[key] for key in ("path", "bytes", "sha256")})
    return document


def input_bindings(request):
    paths = []
    if request["phase"] == "build":
        paths = [Path(request["java"]) / "bin/java.exe",
                 Path(request["sdk"]) / "build-tools/35.0.0/aapt2.exe",
                 Path(request["sdk"]) / "build-tools/35.0.0/lib/apksigner.jar"]
    else:
        paths = [Path(request[key]) for key in ("build", "running", "server", "powershell")]
        paths.append(Path(request["sdk"]) / "platform-tools/adb.exe")
    return [env.binding(path) for path in paths]


def component_worker(request, out):
    try:
        from benchmarks.android_process_client import SdkCapture
        from benchmarks.android_instrumentation_evidence import test_roster, validate_instrumentation
    except ModuleNotFoundError:
        from android_process_client import SdkCapture
        from android_instrumentation_evidence import test_roster, validate_instrumentation
    build = env.read_json(request["build"])
    need(build.get("phase") == "build" and build.get("passed") is True, "build_not_qualified")
    env.check_binding(build["artifacts"])
    env.check_binding(build["sources_after"])
    artifact = checked_apks(build["artifacts"]["path"])
    need(env.read_json(build["sources_after"]["path"]) == source_map(), "source_drift")
    lease_path = Path(request["running"])
    lease_sha = env.digest(lease_path)
    lease = env.read_json(lease_path)
    need(lease["avd_name"] == env.NAME and lease["serial"] == "emulator-5592" and
         lease["console_port"] == 5592 and lease["guest_boot_verified"] is False, "owned_avd_profile")
    def own():
        need(env.digest(lease_path) == lease_sha, "lease_changed")
        for key in ("owner", "worker", "launcher"):
            need(env.process_identity(lease[key]["pid"]) == lease[key], "owner_changed")
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
        need(capture.adb(["install", "--user", "0", "-t", apk["path"]], "install", 120).strip().endswith(b"Success"), "install_failed")
        own()
        raw = shell(["cmd", "package", "path", apk["package"]], "installed-path").decode().strip()
        need(raw.startswith("package:/data/app/") and raw.endswith("/base.apk") and "\n" not in raw, "installed_path")
        need(shell(["sha256sum", raw[len("package:"):]], "installed-hash").decode().split()[0] == apk["sha256"], "installed_hash")
    results = []
    for name in CLASSES:
        source = ROOT / "apps/android/app/src/androidTest/java/org/locallore/app" / (name + ".kt")
        methods = test_roster(source)
        raw = shell(["am", "instrument", "-w", "-r", "-e", "class", "org.locallore.app." + name,
                     APP + ".test/androidx.test.runner.AndroidJUnitRunner"], "instrument-" + name, 240, 262144)
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
    qualified = (result["status"] == "child_exited" and result["worker_returncode"] == 0 and
                 result["cleanup_complete"] and result["output_capture_complete"] and before == after and
                 env.digest(Path(__file__)) == script_sha and env.digest(out / "request-v1.json") == request_sha and
                 request["inputs"] == input_bindings(request))
    record = {"version": 1, "phase": request["phase"], "passed": qualified, "owner": result,
              "sources_before": env.binding(out / "sources-before-v1.json"),
              "sources_after": env.binding(out / "sources-after-v1.json")}
    if qualified:
        name = "artifacts-v1.json" if request["phase"] == "build" else "components-v1.json"
        record["artifacts" if request["phase"] == "build" else "components"] = env.binding(out / name)
    env.create_json(out / "result-v1.json", record)
    need(qualified, "execution_not_qualified")
    return record


def main(argv=None):
    if argv is None and sys.argv[1:] == ["_worker"]:
        data = sys.stdin.buffer.read(4097)
        need(len(data) <= 4096, "request_bounds")
        parts = data.decode("utf-8").splitlines()
        need(len(parts) == 2 and re.fullmatch("[0-9a-f]{64}", parts[1]), "request_binding")
        path = env.safe_path(parts[0])
        need(env.digest(path) == parts[1], "request_changed")
        request = env.read_json(path)
        need(type(request) is dict and set(request) == {"phase", "out", "sdk", "java", "build",
                    "running", "server", "powershell", "inputs"}, "request_fields")
        need(request.get("phase") in ("build", "components"), "worker_phase")
        need(request["inputs"] == input_bindings(request), "input_changed")
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
    need(args["java"] if args["phase"] == "build" else all(args[k] for k in ("build", "running", "server", "powershell")), "phase_arguments")
    supervise(args)
    print(json.dumps({"version": 1, "phase": args["phase"], "passed": True}))
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (VerificationRefused, env.EnvironmentRefused, OSError, ValueError, KeyError, TypeError):
        print(json.dumps({"version": 1, "passed": False, "reason": "verification_refused"}))
        raise SystemExit(1)
