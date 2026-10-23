"""Build the isolated SDK APK with existing tools; never install or run it.

Exit 2 also reports the known AGP 8.10 Kotlin 2.4 metadata-analysis limitation,
even when assembly, Java unit tests and APK audits succeeded.
"""

import argparse
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import zipfile

ROOT = Path(__file__).resolve().parents[4]
PROJECT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / "scripts"))
import check


def dependency_audit():
    manifest = json.loads((ROOT / "docs/runtime/android/LITERT_DEPENDENCIES_2026-10-22.json").read_text())
    cache = Path(os.environ.get("GRADLE_USER_HOME", str(Path.home() / ".gradle"))) / "caches/modules-2/files-2.1"
    for dependency in manifest["dependencies"]:
        group, artifact, version = dependency["coordinate"].split(":")
        for entry in dependency["artifacts"]:
            if not entry["file"].endswith((".jar", ".aar")):
                continue
            matches = list((cache / group / artifact / version).glob("*/" + entry["file"]))
            if not matches or any(hashlib.sha256(path.read_bytes()).hexdigest() != entry["sha256"] for path in matches):
                raise ValueError("Resolved SDK dependency binary identity mismatch")
    print("Resolved SDK/test dependency binary SHA256 values match recorded identities")


def apk_audit(apk, sdk):
    tools = sdk / "build-tools" / "35.0.0"
    suffix = ".exe" if os.name == "nt" else ""
    result = subprocess.run([str(tools / ("aapt2" + suffix)), "dump", "permissions", str(apk)],
                            check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    if result.stdout.decode("utf-8").strip() != "package: org.locallore.runtimebench.litert":
        raise ValueError("Unexpected APK permissions or package")
    subprocess.run([str(tools / ("zipalign" + suffix)), "-c", "-P", "16", "4", str(apk)],
                   check=True, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE)
    with zipfile.ZipFile(apk) as archive:
        expected = {"lib/arm64-v8a/liblitertlm_jni.so", "lib/x86_64/liblitertlm_jni.so"}
        actual = {name for name in archive.namelist() if name.startswith("lib/") and name.endswith(".so")}
        if actual != expected:
            raise ValueError("Unexpected SDK native library set")
    print("APK audit: zero permissions, expected two ABI libraries, 16 KiB ZIP alignment")
    print("APK SHA256: " + hashlib.sha256(apk.read_bytes()).hexdigest())


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--java21", type=Path, required=True, help="Existing Java 21 JDK; never downloaded")
    parser.add_argument("--offline", action="store_true")
    parser.add_argument("--clean", action="store_true")
    args = parser.parse_args()
    check.verify_wrapper(ROOT)
    compiler = args.java21 / "bin" / ("javac.exe" if os.name == "nt" else "javac")
    version = subprocess.run([str(compiler), "-version"], check=True, capture_output=True, text=True)
    if not (version.stdout + version.stderr).strip().startswith("javac 21."):
        raise ValueError("The publisher SDK requires an existing Java 21 compiler")
    sdk = Path(os.environ.get("ANDROID_HOME", ""))
    argv = [check.java_executable(), "-Dorg.gradle.java.installations.paths=" + str(args.java21.resolve()),
            "-classpath", str(ROOT / "apps/android/gradle/wrapper/gradle-wrapper.jar"),
            "org.gradle.wrapper.GradleWrapperMain"]
    if args.clean:
        argv.append("clean")
    argv.extend([":app:assembleDebug", ":app:testDebugUnitTest", ":app:lintDebug", "--no-daemon", "--console=plain",
                 "-Pandroid.builder.sdkDownload=false", "-Dorg.gradle.java.installations.auto-download=false"])
    if args.offline:
        argv.append("--offline")
    # Keep compiler/native dependency messages in ignored build output; SDK runtime
    # requests and generation are never sent to this build command.
    # A clean task removes app/build. Hold the log outside it during execution.
    log = PROJECT / ".gradle/spike-build.log"
    log.parent.mkdir(parents=True, exist_ok=True)
    with log.open("wb") as output:
        result = subprocess.run(argv, cwd=PROJECT, stdout=output, stderr=subprocess.STDOUT)
    if result.returncode:
        print("Build failed; inspect ignored .gradle/spike-build.log")
        return result.returncode
    dependency_audit()
    apk_audit(PROJECT / "app/build/outputs/apk/debug/app-debug.apk", sdk)
    # The exact pinned SDK uses Kotlin metadata 2.4; the exact pinned AGP analyzer
    # expects 2.1. Cached lint tasks do not repeat the diagnostic, so absence from
    # a later incremental log cannot upgrade this known incomplete analysis gate.
    print("Assembly and JVM tests succeeded; lint dependency analysis is limited by Kotlin 2.4 metadata.")
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
