#!/usr/bin/env python3
"""Run repository checks without provisioning tools or changing machine settings."""

import argparse
from dataclasses import dataclass
import hashlib
import os
from pathlib import Path
import shutil
import subprocess
import sys


ROOT = Path(__file__).resolve().parents[1]
RUST_VERSION = "1.93.1"
WRAPPER_SHA256 = "2db75c40782f5e8ba1fc278a5574bab070adccb2d21ca5a6e5ed840888448046"
DISTRIBUTION_SHA256 = "f397b287023acdba1e9f6fc5ea72d22dd63669d59ed4a289a29b1a76eee151c6"
DISTRIBUTION_URL = r"https\://services.gradle.org/distributions/gradle-8.11.1-bin.zip"


@dataclass(frozen=True)
class Command:
    argv: tuple
    cwd: Path


def host_commands(root, offline):
    cargo = ["cargo", "+" + RUST_VERSION]
    locked = ["--locked"] + (["--offline"] if offline else [])
    executable = root / "target" / "checks" / (
        "native-linker-tests.exe" if os.name == "nt" else "native-linker-tests"
    )
    commands = [
        cargo + ["fmt", "--all", "--", "--check"],
        cargo + ["clippy", "--workspace", "--all-targets"] + locked + ["--", "-D", "warnings"],
        cargo + ["test", "--workspace"] + locked,
        cargo + ["run", "-p", "locallore", "--example", "android_fixtures"] + locked + ["--", "--check"],
        [sys.executable, "-m", "unittest", "discover", "-s", "benchmarks", "-p", "test_*.py"],
        [sys.executable, "-m", "unittest", "discover", "-s", "benchmarks/spike/litert", "-p", "test_*.py"],
        [sys.executable, "-m", "unittest", "discover", "-s", "benchmarks/spike/llama", "-p", "test_*.py"],
        [sys.executable, "-m", "unittest", "discover", "-s", "scripts/tests", "-p", "test_*.py"],
        ["rustfmt", "+" + RUST_VERSION, "--check", "--edition", "2021", "apps/android/native-linker.rs"],
        ["rustc", "+" + RUST_VERSION, "--test", "--edition", "2021", "apps/android/native-linker.rs", "-o", str(executable)],
        [str(executable)],
    ]
    return [Command(tuple(argv), root) for argv in commands]


def verify_wrapper(root):
    """Reject modified bootstrap code/settings before starting a Java process."""
    wrapper = root / "apps/android/gradle/wrapper"
    digest = hashlib.sha256((wrapper / "gradle-wrapper.jar").read_bytes()).hexdigest()
    if digest != WRAPPER_SHA256:
        raise ValueError("Gradle wrapper JAR SHA-256 does not match the pinned official artifact")
    properties = {}
    for line in (wrapper / "gradle-wrapper.properties").read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith(("#", "!")):
            continue
        key, separator, value = line.partition("=")
        if not separator or key.strip() in properties:
            raise ValueError("Malformed or duplicate Gradle wrapper property")
        properties[key.strip()] = value.strip()
    expected = {
        "distributionUrl": DISTRIBUTION_URL,
        "distributionSha256Sum": DISTRIBUTION_SHA256,
        "validateDistributionUrl": "true",
        "distributionBase": "GRADLE_USER_HOME",
        "distributionPath": "wrapper/dists",
        "zipStoreBase": "GRADLE_USER_HOME",
        "zipStorePath": "wrapper/dists",
        "networkTimeout": "10000",
    }
    if properties != expected:
        raise ValueError("Gradle wrapper properties differ from the pinned configuration")


def java_executable():
    java_home = os.environ.get("JAVA_HOME")
    if java_home:
        java = Path(java_home) / "bin" / ("java.exe" if os.name == "nt" else "java")
        if not java.is_file():
            raise ValueError("JAVA_HOME must point to an installed Java 17 JDK")
        return str(java)
    java = shutil.which("java")
    if not java:
        raise ValueError("Java 17 is required; set JAVA_HOME or put java on PATH")
    return java


def android_commands(root, offline, clean):
    verify_wrapper(root)
    # Invoke the verified JAR directly, avoiding .bat/cmd shell interpretation.
    argv = [java_executable(), "-classpath", str(root / "apps/android/gradle/wrapper/gradle-wrapper.jar"),
            "org.gradle.wrapper.GradleWrapperMain"]
    if clean:
        argv.append("clean")
    argv.extend([":app:assembleDebug", ":app:assembleDebugAndroidTest", ":app:testDebugUnitTest",
                 ":app:lintDebug", "--no-daemon", "--console=plain", "-Pandroid.builder.sdkDownload=false"])
    if offline:
        argv.append("--offline")
    return [
        Command(tuple(argv), root / "apps/android"),
        Command((sys.executable, str(root / "scripts/audit_apk.py"),
                 str(root / "apps/android/app/build/outputs/apk/debug/app-debug.apk")), root),
    ]


def run_commands(commands):
    for command in commands:
        print("+ " + repr(list(command.argv)), flush=True)
        completed = subprocess.run(list(command.argv), cwd=command.cwd, shell=False, check=False)
        if completed.returncode:
            return completed.returncode
    return 0


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("suite", choices=("host", "android"))
    parser.add_argument("--offline", action="store_true", help="require cached Cargo/Gradle dependencies")
    parser.add_argument("--clean", action="store_true", help="clean Android build outputs before checking")
    args = parser.parse_args(argv)
    if args.clean and args.suite != "android":
        parser.error("--clean applies only to android")
    try:
        if args.suite == "host":
            (ROOT / "target/checks").mkdir(parents=True, exist_ok=True)
            commands = host_commands(ROOT, args.offline)
        else:
            commands = android_commands(ROOT, args.offline, args.clean)
        return run_commands(commands)
    except KeyboardInterrupt:
        print("Checks interrupted.", file=sys.stderr)
        return 130
    except (OSError, ValueError) as error:
        print("Checks failed: " + str(error), file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
