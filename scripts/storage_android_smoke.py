"""Explicit offline Android storage-smoke cross-build; never invokes ADB.

Copyright 2026 LocalLore contributors. SPDX-License-Identifier: Apache-2.0
"""
import argparse
import hashlib
import json
import os
from pathlib import Path
import struct
import subprocess

from audit_apk import ABIS, AuditError, elf_alignments, require

ROOT = Path(__file__).resolve().parents[1]
NDK_VERSION = "29.0.14206865"
RUST_VERSION = "1.93.1"
TARGETS = {"x86_64": "x86_64-linux-android", "arm64-v8a": "aarch64-linux-android"}


def inspect_binary(path, abi):
    data = path.read_bytes()
    alignments = elf_alignments(data, ABIS[abi])
    offset = struct.unpack_from("<Q", data, 32)[0]
    size, count = struct.unpack_from("<HH", data, 54)
    segments = [struct.unpack_from("<IIQQQQQQ", data, offset + index * size)
                for index in range(count)]
    interpreter, dynamic = None, None
    for segment in segments:
        kind, _, position, _, _, length, _, _ = segment
        if kind == 3:
            require(position + length <= len(data), "Invalid ELF interpreter bounds")
            interpreter = data[position:position + length].rstrip(b"\0").decode("ascii")
        elif kind == 2:
            require(position + length <= len(data) and length % 16 == 0,
                    "Invalid ELF dynamic bounds")
            dynamic = (position, length)
    require(interpreter == "/system/bin/linker64" and dynamic is not None,
            "Expected standalone Android PIE")
    tags = []
    for position in range(dynamic[0], sum(dynamic), 16):
        tag, value = struct.unpack_from("<QQ", data, position)
        if tag == 0:
            break
        tags.append((tag, value))
    require(any(tag == 0x6ffffffb and value & 0x08000000 for tag, value in tags),
            "Missing DF_1_PIE")
    addresses = [value for tag, value in tags if tag == 5]
    require(len(addresses) == 1, "Expected one dynamic string table")
    mappings = [segment for segment in segments if segment[0] == 1
                and segment[3] <= addresses[0] < segment[3] + segment[5]]
    require(len(mappings) == 1, "Invalid dynamic string table mapping")
    strings = mappings[0][2] + addresses[0] - mappings[0][3]
    needed = []
    for tag, value in tags:
        if tag == 1:
            start = strings + value
            require(start < len(data), "Invalid dependency string offset")
            end = data.find(b"\0", start)
            require(end >= start, "Unterminated dependency string")
            needed.append(data[start:end].decode("ascii"))
    require(set(needed) <= {"libc.so", "libdl.so", "libm.so", "liblog.so"},
            "Unexpected shared dependency; SQLite must be bundled")
    return {"abi": abi, "bytes": len(data), "sha256": hashlib.sha256(data).hexdigest(),
            "elf_machine": ABIS[abi], "pie": True, "load_alignments": alignments,
            "needed": needed}


def command(arguments, environment=None):
    subprocess.run([str(value) for value in arguments], cwd=ROOT,
                   env=environment, check=True, shell=False)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--sdk", type=Path, required=True)
    parser.add_argument("--output", type=Path, default=ROOT / "target/storage-android-smoke")
    parser.add_argument("--abi", choices=TARGETS, action="append")
    parser.add_argument("--example", choices=["storage_smoke", "durable_smoke"], default="storage_smoke")
    args = parser.parse_args(argv)
    if os.name != "nt":
        parser.error("This checked recipe currently supports Windows hosts only")
    ndk = args.sdk.resolve() / "ndk" / NDK_VERSION
    require(f"Pkg.Revision = {NDK_VERSION}" in (ndk / "source.properties").read_text(),
            "Unreviewed NDK revision")
    llvm = ndk / "toolchains/llvm/prebuilt/windows-x86_64"
    clang, archive = llvm / "bin/clang.exe", llvm / "bin/llvm-ar.exe"
    require(clang.is_file() and archive.is_file(), "Install the pinned NDK before building")
    output = args.output.resolve()
    output.mkdir(parents=True, exist_ok=True)
    linker = output / "native-linker.exe"
    command(["rustc", f"+{RUST_VERSION}", "--edition=2021", "-O",
             ROOT / "apps/android/native-linker.rs", "-o", linker])
    reports = []
    for abi in args.abi or TARGETS:
        target = TARGETS[abi]
        key = target.replace("-", "_")
        environment = os.environ.copy()
        environment.update({
            f"CARGO_TARGET_{key.upper()}_LINKER": str(linker),
            "LOCALLORE_ANDROID_CLANG": str(clang),
            f"CC_{key}": str(clang),
            f"AR_{key}": str(archive),
            "CC_SHELL_ESCAPED_FLAGS": "1",
            f"CFLAGS_{key}": f'--target={target}26 "--sysroot={(llvm / "sysroot").as_posix()}"',
            "LIBSQLITE3_SYS_USE_PKG_CONFIG": "0",
            "CARGO_ENCODED_RUSTFLAGS": "\x1f".join([
                "-C", f"link-arg=--target={target}26",
                "-C", f"link-arg=--sysroot={llvm / 'sysroot'}",
                "-C", "link-arg=-Wl,-z,max-page-size=16384"]),
        })
        command(["cargo", f"+{RUST_VERSION}", "build", "--locked", "--offline", "--release",
                 "--package", "locallore-storage", "--example", args.example,
                 "--target", target, "--target-dir", output / "rust"], environment)
        report = inspect_binary(output / "rust" / target / "release/examples" / args.example, abi)
        reports.append(report)
        (output / f"{abi}-elf.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
        print(json.dumps({"status": "built", **report}), flush=True)
    (output / "elf.json").write_text(json.dumps(reports, indent=2) + "\n", encoding="utf-8")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (AuditError, OSError, UnicodeError, struct.error, subprocess.CalledProcessError):
        print(json.dumps({"status": "failed", "error": "cross_build_or_audit"}))
        raise SystemExit(1)
