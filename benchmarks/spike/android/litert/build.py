"""Build the isolated SDK APK with existing tools; never install or run it.

An analyzer dependency/metadata audit fails closed even when Gradle and a lint
issue report alone would have returned success.
"""

import argparse
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import zipfile
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[4]
PROJECT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / "scripts"))
import check

ANALYZER_LOCK = "docs/runtime/android/LITERT_ANALYZER_LOCK_2026-10-22.json"
ANALYSIS_FAILURES = (
    "incompatible version of kotlin", "incompatible version of metadata",
    "unexpected failure during lint", "no such method", "nosuchmethoderror",
    "noclassdeffounderror", "unsupportedclassversionerror", "incompatibleclasschangeerror",
    "exception in thread", "could not initialize class", "lint infrastructure error",
)


def analysis_failed(log):
    lower = log.lower()
    return any(marker in lower for marker in ANALYSIS_FAILURES) or any(
        line.lstrip().startswith("e: ") for line in lower.splitlines())


def analyzer_audit(log):
    if analysis_failed(log):
        raise ValueError("Lint analyzer reported an incompatible dependency or infrastructure failure")
    expected = json.loads((ROOT / ANALYZER_LOCK).read_text(encoding="utf-8"))
    actual = json.loads((PROJECT / "app/build/reports/analyzer-audit.json").read_text(encoding="utf-8"))
    if (actual.get("version") != 1 or actual.get("analyzer_version") != expected["analyzer_version"]
            or actual.get("artifacts") != expected["artifacts"] or not actual.get("check_dependencies")):
        raise ValueError("Actual AGP analyzer classpath or dependency analysis differs from the pinned audit")
    model = (PROJECT / "app" / actual["model_directory"]).resolve()
    if not model.is_relative_to((PROJECT / "app/build").resolve()):
        raise ValueError("Analyzer model is outside this experiment's build output")
    dependencies = ET.parse(model / "debug-artifact-dependencies.xml").getroot()
    names = {element.get("name", "") for element in dependencies.iter()}
    required = {"com.google.ai.edge.litertlm:litertlm-android:0.18.1@aar",
                "org.jetbrains.kotlin:kotlin-reflect:2.4.0@jar", "org.jetbrains.kotlin:kotlin-stdlib:2.4.0@jar"}
    if not required <= names:
        raise ValueError("The analyzed model does not include the exact SDK and Kotlin dependencies")
    issues = ET.parse(PROJECT / "app/build/reports/lint-results-debug.xml").getroot()
    if any(issue.get("severity", "").lower() in ("error", "fatal") for issue in issues.findall("issue")):
        raise ValueError("Lint reported an error")
    print("Actual locked lint " + actual["analyzer_version"] + " analyzed the SDK/Kotlin dependency model without metadata failures")


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
    parser.add_argument("--probe-incompatible-analyzer", action="store_true",
                        help="Negative lint-only experiment using original 8.10.1 analyzer; expected rejection returns 2")
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
    if args.probe_incompatible_analyzer:
        argv.extend([":app:lintDebug", "-Pandroid.experimental.lint.version=8.10.1", "--rerun-tasks"])
    else:
        argv.extend([":app:assembleDebug", ":app:testDebugUnitTest", ":app:lintDebug", ":app:auditLintAnalyzer"])
    argv.extend(["--no-daemon", "--console=plain",
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
    text = log.read_text(encoding="utf-8", errors="replace")
    if args.probe_incompatible_analyzer:
        if ("incompatible version of Kotlin" in text and "metadata is 2.4.0" in text
                and "expected version is 2.1.0" in text):
            print("Original analyzer rejected actual SDK Kotlin 2.4 metadata (expected exit 2)")
            return 2
        print("Negative analyzer probe did not reproduce the required SDK metadata rejection")
        return 3
    dependency_audit()
    apk_audit(PROJECT / "app/build/outputs/apk/debug/app-debug.apk", sdk)
    try:
        analyzer_audit(text)
    except (ValueError, OSError, KeyError, ET.ParseError) as error:
        print("Analyzer audit failed; inspect ignored .gradle/spike-build.log and analyzer-audit.json")
        return 2
    print("Assembly, JVM tests, lint analyzer and APK audits succeeded.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
