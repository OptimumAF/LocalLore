"""Offline, fresh D-output cacheprobe build/audit. Never installs, provisions or runs a model."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import stat
import subprocess
import sys
import xml.etree.ElementTree as ET
import zipfile

import build
import play_build

sys.path.insert(0, str(build.ROOT / "benchmarks"))
import runtime_spike
import audit_apk

PACKAGE = "org.locallore.runtimebench.litert.cacheprobe"
INSTRUMENTATION = "org.locallore.runtimebench.litert.CacheProbeInstrumentation"
OWNER = b"locallore-explicit-cache-build-v1\n"
GIB = 1024 ** 3


def real_directory(path):
    path = Path(path)
    if not path.is_absolute() or path != Path(os.path.normpath(path)):
        raise ValueError("invalid_output")
    for ancestor in (path, *path.parents):
        try:
            metadata = ancestor.lstat()
        except OSError as error:
            raise ValueError("linked_or_missing_output") from error
        if (getattr(metadata, "st_file_attributes", 0) & stat.FILE_ATTRIBUTE_REPARSE_POINT
                or not ancestor.is_dir() or ancestor.is_symlink()):
            raise ValueError("linked_or_missing_output")
    if path.resolve(strict=True) != path:
        raise ValueError("linked_or_missing_output")
    return path


def fresh_output(path):
    path = Path(path)
    if os.name != "nt" or path.drive.upper() != "D:":
        raise ValueError("output_must_use_D")
    real_directory(path.parent)
    path.mkdir()  # Never reuse/clean/overwrite a prior attempt.
    (path / "owner-v1").write_bytes(OWNER)
    for name in ("logs", "temp", "gradle-project", "app-build", "native", "verified"):
        (path / name).mkdir()
    return path


def capacity(output, disk_usage=shutil.disk_usage):
    # Keep each independent host volume's reserve and estimated write allowance.
    if disk_usage("C:\\").free < 4 * GIB + 64 * 1024 ** 2:
        raise ValueError("host_system_capacity_blocked")
    if disk_usage(str(output.anchor)).free < 16 * GIB:
        raise ValueError("host_output_capacity_blocked")


def gradle_command(java21, output):
    return [build.check.java_executable(), "-Dorg.gradle.java.installations.paths=" + str(java21),
        "-Djava.io.tmpdir=" + str(output / "temp"), "-classpath",
        str(build.ROOT / "apps/android/gradle/wrapper/gradle-wrapper.jar"), "org.gradle.wrapper.GradleWrapperMain",
        ":app:assembleDebug", ":app:testDebugUnitTest", ":app:lintDebug", ":app:auditLintAnalyzer",
        "--project-cache-dir", str(output / "gradle-project"), "--offline", "--no-daemon", "--console=plain",
        "-Pandroid.builder.sdkDownload=false", "-Dorg.gradle.java.installations.auto-download=false",
        "-PlocalLoreCacheProbe=true", "-PlocalLorePlayProbe=false",
        "-PlocalLoreCacheOutput=" + str(output / "app-build"),
        "-PlocalLoreCacheNativeDir=" + str(output / "native/jniLibs")]


def manifest_audit(permissions, tree):
    if permissions.strip() != "package: " + PACKAGE:
        raise ValueError("unexpected_permissions_or_package")
    blocks = []
    lines = tree.splitlines()
    for index, line in enumerate(lines):
        match = re.match(r"(\s*)E: instrumentation \(", line)
        if not match:
            continue
        block = []
        for following in lines[index + 1:]:
            if following.strip() and len(following) - len(following.lstrip()) <= len(match[1]):
                break
            block.append(following)
        blocks.append("\n".join(block))
    if len(blocks) != 1 or not re.search(r':name\([^)]*\)="' + re.escape(INSTRUMENTATION) + '"', blocks[0]) or not re.search(
            r':targetPackage\([^)]*\)="' + re.escape(PACKAGE) + '"', blocks[0]):
        raise ValueError("unexpected_instrumentation")
    if re.search(r"E: uses-permission|E: permission \(", tree):
        raise ValueError("unexpected_permission_declaration")


def native_archive_audit(apk):
    expected = {f"lib/{abi}/{library}" for abi in play_build.TARGETS for library in
                ("liblitertlm_jni.so", "liblocallore_android.so")}
    with zipfile.ZipFile(apk) as archive:
        names = archive.namelist()
        if len(names) != len(set(names)) or {name for name in names if name.endswith(".so")} != expected:
            raise ValueError("unexpected_native_libraries")
        result = []
        for name in sorted(expected):
            entry = archive.getinfo(name)
            if entry.compress_type != zipfile.ZIP_STORED or not 0 < entry.file_size < 64 * 1024 ** 2:
                raise ValueError("invalid_native_entry")
            data = archive.read(name)
            audit_apk.elf_alignments(data, audit_apk.ABIS[name.split("/")[1]])
            result.append({"entry": name, "bytes": len(data), "sha256": hashlib.sha256(data).hexdigest()})
        return result


def exports_audit(text):
    prefix = "Java_org_locallore_runtimebench_litert_NativePlayProbe_"
    expected = {prefix + method for method in ("open", "call", "poll", "respond", "close")}
    actual = {word for line in text.splitlines() for word in line.split() if word.startswith(prefix)}
    if actual != expected:
        raise ValueError("unexpected_play_probe_exports")


def analyzer_audit(output):
    actual = json.loads((output / "app-build/reports/analyzer-audit.json").read_text(encoding="utf-8"))
    expected = json.loads((build.ROOT / build.ANALYZER_LOCK).read_text(encoding="utf-8"))
    if actual.get("version") != 1 or actual.get("analyzer_version") != expected["analyzer_version"] or actual.get(
            "artifacts") != expected["artifacts"] or actual.get("check_dependencies") is not True:
        raise ValueError("analyzer_identity_mismatch")
    model = real_directory(Path(actual["model_directory"]))
    if not model.is_relative_to((output / "app-build").resolve()):
        raise ValueError("analyzer_model_outside_output")
    names = {item.get("name", "") for item in ET.parse(model / "debug-artifact-dependencies.xml").getroot().iter()}
    if not {"com.google.ai.edge.litertlm:litertlm-android:0.18.1@aar", "org.jetbrains.kotlin:kotlin-stdlib:2.4.0@jar",
            "org.jetbrains.kotlin:kotlin-reflect:2.4.0@jar"} <= names:
        raise ValueError("analyzer_missing_sdk")
    issues = ET.parse(output / "app-build/reports/lint-results-debug.xml").getroot()
    if any(item.get("severity", "").lower() in ("error", "fatal") for item in issues.findall("issue")):
        raise ValueError("lint_failed")


def stage(output, name, command, cwd, overrides=None):
    capacity(output)
    plan = {"command": command, "cwd": str(cwd), "environment": overrides or {}}
    request = json.dumps(plan).encode("utf-8")
    result = runtime_spike.run_process([sys.executable, str(Path(__file__).resolve()), "--owned-stage"],
        request=request, deadline=180, max_output=262144)
    (output / "logs" / (name + ".log")).write_bytes(result.stdout)
    record = {"version": 1, "status": result.status, "returncode": result.returncode,
              "elapsed_ms": result.elapsed_ms, "stderr_bytes": result.stderr_bytes,
              "cleanup_complete": result.cleanup_complete, "command": command}
    (output / "logs" / (name + ".json")).write_text(json.dumps(record, indent=2) + "\n", encoding="utf-8")
    if result.status != "completed" or result.returncode != 0 or not result.cleanup_complete:
        raise ValueError("build_stage_failed_" + name)
    return result.stdout.decode("utf-8", errors="replace")


def owned_stage():
    # No descendant can start before the job-owning controller closes this input pipe.
    raw = sys.stdin.buffer.read(131073)
    if len(raw) > 131072:
        return 2
    plan = json.loads(raw)
    env = os.environ.copy(); env.pop("LIBSQLITE3_FLAGS", None); env.pop("RUSTFLAGS", None)
    env.update(plan["environment"])
    return subprocess.run(plan["command"], cwd=plan["cwd"], env=env, stderr=subprocess.STDOUT).returncode


def execute(java21, output, sdk):
    build.check.verify_wrapper(build.ROOT)
    temp = {"TEMP": str(output / "temp"), "TMP": str(output / "temp"), "TMPDIR": str(output / "temp")}
    source_commit = stage(output, "source-revision", ["git", "rev-parse", "HEAD"], build.ROOT, temp).strip()
    if not re.fullmatch(r"[a-f0-9]{40}", source_commit):
        raise ValueError("source_revision_invalid")
    version = stage(output, "java21", [str(java21 / "bin/javac.exe"), "-version"], build.PROJECT, temp)
    if not version.strip().startswith("javac 21."):
        raise ValueError("java21_required")
    llvm = sdk / "ndk" / play_build.NDK / "toolchains/llvm/prebuilt/windows-x86_64"
    if not (llvm / "bin/clang.exe").is_file() or not (llvm / "bin/llvm-ar.exe").is_file():
        raise ValueError("pinned_ndk_required")
    linker = output / "native/native-linker.exe"
    stage(output, "native-linker", ["rustc", "+1.93.1", "--edition=2021", "-O",
          str(build.ROOT / "apps/android/native-linker.rs"), "-o", str(linker)], build.ROOT, temp)
    for abi, target in play_build.TARGETS.items():
        command, env = play_build.native_command(target, output / "native", linker, llvm)
        overrides = {key: value for key, value in env.items() if os.environ.get(key) != value}
        stage(output, "native-" + abi, command, build.ROOT, dict(overrides, **temp))
        source = output / "native/rust" / target / "release/liblocallore_android.so"
        audit_apk.elf_alignments(source.read_bytes(), audit_apk.ABIS[abi])
        exports_audit(stage(output, "exports-" + abi, [str(llvm / "bin/llvm-nm.exe"), "-D", "--defined-only", str(source)], build.ROOT, temp))
        destination = output / "native/jniLibs" / abi / source.name
        destination.parent.mkdir(parents=True); shutil.copyfile(source, destination)
    return qualify_java(java21, output, sdk, source_commit)


def qualify_java(java21, output, sdk, source_commit):
    """Qualify fresh Java output with an already staged, separately audited native pair.

    The normal CLI always builds that pair immediately above. A coordinator may
    call this narrow phase after recording an unchanged-native-source proof and
    byte-identical copied ABI provenance; it does not locate or adopt old output.
    """
    temp = {"TEMP": str(output / "temp"), "TMP": str(output / "temp"), "TMPDIR": str(output / "temp")}
    log = stage(output, "gradle", gradle_command(java21, output), build.PROJECT, temp)
    if build.analysis_failed(log):
        raise ValueError("analyzer_infrastructure_failed")
    build.dependency_audit(); analyzer_audit(output)
    apk = output / "app-build/outputs/apk/debug/app-debug.apk"
    tools = sdk / "build-tools/35.0.0"
    permissions = stage(output, "permissions", [str(tools / "aapt2.exe"), "dump", "permissions", str(apk)], build.PROJECT)
    tree = stage(output, "manifest", [str(tools / "aapt2.exe"), "dump", "xmltree", str(apk), "--file", "AndroidManifest.xml"], build.PROJECT)
    manifest_audit(permissions, tree)
    libraries = native_archive_audit(apk)
    stage(output, "zipalign", [str(tools / "zipalign.exe"), "-c", "-P", "16", "4", str(apk)], build.PROJECT)
    frozen = output / "verified/cacheprobe-debug.apk"; shutil.copyfile(apk, frozen)
    report = {"version": 1, "status": "passed", "package": PACKAGE, "instrumentation": INSTRUMENTATION,
              "source_commit": source_commit,
              "apk_sha256": hashlib.sha256(frozen.read_bytes()).hexdigest(), "libraries": libraries,
              "permissions": [], "device_execution": False, "model_execution": False}
    (output / "verified/build-result.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    return report


def main():
    if sys.argv[1:] == ["--owned-stage"]:
        return owned_stage()
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--java21", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True, help="Fresh D directory; parent must exist")
    args = parser.parse_args()
    try:
        capacity(args.output)
        output = fresh_output(args.output)
        report = execute(args.java21.resolve(), output, Path(os.environ.get("ANDROID_HOME", "")).resolve())
        print(json.dumps(report, sort_keys=True))
        return 0
    except (OSError, ValueError, KeyError, ET.ParseError, zipfile.BadZipFile):
        print('{"version":1,"status":"failed","error":"cache_build_failed"}')
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
