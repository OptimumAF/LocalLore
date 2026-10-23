#!/usr/bin/env python3
"""Explicit offline Rust/SDK play experiment build. Never installs or invokes a model.

Copyright 2026 LocalLore contributors. SPDX-License-Identifier: Apache-2.0
"""
import argparse
import hashlib
import json
import os
from pathlib import Path
import platform
import shutil
import subprocess
import sys

import build

ROOT = build.ROOT
OUT = ROOT / "target/android-play-probe"
NDK = "29.0.14206865"
TARGETS = {"x86_64": "x86_64-linux-android", "arm64-v8a": "aarch64-linux-android"}


def native_command(target, output, linker, llvm):
    clang = llvm / "bin/clang.exe"
    archiver = llvm / "bin/llvm-ar.exe"
    flags = ["--target=" + target + "26", "--sysroot=" + str(llvm / "sysroot")]
    quoted = lambda value: '"' + value.replace("\\", "\\\\").replace('"', '\\"') + '"'
    env = os.environ.copy()
    # A capacity-fault experiment must not leak SQLite compile limits into this build.
    env.pop("LIBSQLITE3_FLAGS", None)
    env.update({"CARGO_TARGET_" + target.upper().replace("-", "_") + "_LINKER": str(linker),
                "LOCALLORE_ANDROID_CLANG": str(clang),
                "CARGO_ENCODED_RUSTFLAGS": "\x1f".join(["-C", "link-arg=" + flags[0], "-C", "link-arg=" + flags[1],
                                                       "-C", "link-arg=-Wl,-z,max-page-size=16384"]),
                "CC_" + target: str(clang), "AR_" + target: str(archiver),
                "CFLAGS_" + target: " ".join(quoted(f) for f in flags), "CC_SHELL_ESCAPED_FLAGS": "1"})
    argv = ["cargo", "+1.93.1", "build", "--locked", "--offline", "--release", "-p", "locallore-android",
            "--lib", "--features", "play-probe", "--target", target, "--target-dir", str(output / "rust")]
    return argv, env


def build_native(sdk):
    if platform.system() != "Windows":
        raise ValueError("This experiment currently uses the reviewed Windows NDK linker recipe")
    llvm = sdk.resolve() / "ndk" / NDK / "toolchains/llvm/prebuilt/windows-x86_64"
    if any(not p.is_file() for p in (llvm / "bin/clang.exe", llvm / "bin/llvm-ar.exe")):
        raise ValueError("The existing pinned NDK is required")
    OUT.mkdir(parents=True, exist_ok=True)
    linker = OUT / "native-linker.exe"
    subprocess.run(["rustc", "+1.93.1", "--edition=2021", "-O", str(ROOT / "apps/android/native-linker.rs"),
                    "-o", str(linker)], cwd=ROOT, check=True)
    import audit_apk  # build imports scripts/check and adds the reviewed scripts directory.
    report = {"version": 1, "scope": "optional_sdk_play_probe", "native_feature": "play-probe", "libraries": []}
    for abi, target in TARGETS.items():
        argv, env = native_command(target, OUT, linker, llvm)
        subprocess.run(argv, cwd=ROOT, env=env, check=True)
        source = OUT / "rust" / target / "release/liblocallore_android.so"
        raw = source.read_bytes()
        alignments = audit_apk.elf_alignments(raw, audit_apk.ABIS[abi])
        destination = OUT / "jniLibs" / abi / source.name
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(source, destination)
        report["libraries"].append({"abi": abi, "bytes": len(raw), "sha256": hashlib.sha256(raw).hexdigest(),
                                    "elf_load_alignment": alignments})
    with (OUT / "native-build.json").open("w", encoding="utf-8", newline="\n") as output:
        json.dump(report, output, indent=2); output.write("\n")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--java21", type=Path, required=True)
    parser.add_argument("--clean", action="store_true")
    args = parser.parse_args()
    sdk = Path(os.environ.get("ANDROID_HOME", ""))
    build.check.verify_wrapper(ROOT)
    build_native(sdk)
    argv = [sys.executable, str(Path(__file__).with_name("build.py")), "--java21", str(args.java21), "--offline", "--play-probe"]
    if args.clean:
        argv.append("--clean")
    result = subprocess.run(argv, cwd=ROOT, check=False)
    if result.returncode == 0:
        source = build.PROJECT / "app/build/outputs/apk/debug/app-debug.apk"
        frozen = OUT / "verified/app-debug.apk"
        frozen.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(source, frozen)
        print("Preserved opted-in APK SHA256: " + hashlib.sha256(frozen.read_bytes()).hexdigest())
    return result.returncode


if __name__ == "__main__":
    raise SystemExit(main())
