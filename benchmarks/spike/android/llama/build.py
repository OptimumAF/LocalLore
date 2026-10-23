#!/usr/bin/env python3
"""Explicit, offline Windows cross-build. Never invokes adb or downloads inputs."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import platform
import struct
import subprocess

ROOT = Path(__file__).resolve().parents[4]
PIN = "620d2225cc436ab0b001e3200e590e3b286ef9ab"
NDK = "29.0.14206865"
TARGETS = {"x86_64": "x86_64-linux-android", "arm64-v8a": "aarch64-linux-android"}


def run(args, env=None):
    subprocess.run([str(arg) for arg in args], cwd=ROOT, env=env, check=True)


def source_check(source):
    revision = subprocess.check_output(["git", "-C", str(source), "rev-parse", "HEAD"], text=True).strip()
    if revision != PIN:
        raise ValueError("Unreviewed llama.cpp revision")
    status = subprocess.check_output(["git", "-C", str(source), "status", "--porcelain"], text=True)
    if status.strip():
        raise ValueError("Modified or untracked llama.cpp source")


def elf_report(path, expected_machine=None):
    """Inspect executable bytes rather than treating successful linking as proof."""
    raw = path.read_bytes()
    if raw[:6] != b"\x7fELF\x02\x01":
        raise ValueError("Expected little-endian ELF64")
    kind, machine = struct.unpack_from("<HH", raw, 16)
    if machine not in {62, 183} or (expected_machine is not None and machine != expected_machine):
        raise ValueError("ELF architecture does not match the requested ABI")
    offset = struct.unpack_from("<Q", raw, 32)[0]
    entry_size, count = struct.unpack_from("<HH", raw, 54)
    loads, interpreter, dynamic = [], None, None
    for index in range(count):
        header = struct.unpack_from("<IIQQQQQQ", raw, offset + index * entry_size)
        ptype, _, file_offset, vaddr, _, file_size, _, alignment = header
        if ptype == 1:
            if alignment < 16384 or (vaddr - file_offset) % 16384:
                raise ValueError("ELF LOAD segment is not 16 KiB aligned")
            loads.append(alignment)
        elif ptype == 3:
            interpreter = raw[file_offset:file_offset + file_size].rstrip(b"\0").decode("ascii")
        elif ptype == 2:
            dynamic = (file_offset, file_size)
    if kind != 3 or not loads or interpreter != "/system/bin/linker64" or dynamic is None:
        raise ValueError("Expected Android PIE with dynamic loader")
    tags = []
    for position in range(dynamic[0], sum(dynamic), 16):
        tag, value = struct.unpack_from("<QQ", raw, position)
        if tag == 0:
            break
        tags.append((tag, value))
    if not any(tag == 0x6ffffffb and value & 0x08000000 for tag, value in tags):
        raise ValueError("Missing DF_1_PIE")
    string_address = next(value for tag, value in tags if tag == 5)
    string_offset = None
    for index in range(count):
        header = struct.unpack_from("<IIQQQQQQ", raw, offset + index * entry_size)
        if header[0] == 1 and header[3] <= string_address < header[3] + header[5]:
            string_offset = header[2] + string_address - header[3]
    if string_offset is None:
        raise ValueError("ELF string table not mapped")
    needed = []
    for tag, value in tags:
        if tag == 1:
            start = string_offset + value
            needed.append(raw[start:raw.index(b"\0", start)].decode("ascii"))
    if any(name not in {"libc.so", "libdl.so", "libm.so", "liblog.so"} for name in needed):
        raise ValueError("Unexpected non-system shared dependency")
    return {"bytes": len(raw), "sha256": hashlib.sha256(raw).hexdigest(),
            "elf_class": 64, "machine": machine, "type": "ET_DYN", "pie": True,
            "interpreter": interpreter, "load_alignments": loads, "needed": needed}


def deadline_report(path):
    """Prove the real linked initializer is scheduled before native main."""
    raw = path.read_bytes()
    shoff = struct.unpack_from("<Q", raw, 40)[0]
    shsize, shcount = struct.unpack_from("<HH", raw, 58)
    sections = [struct.unpack_from("<IIQQQQIIQQ", raw, shoff + index * shsize)
                for index in range(shcount)]
    address = None
    for section in sections:
        if section[1] != 2:  # SHT_SYMTAB
            continue
        strings = sections[section[6]]
        for offset in range(section[4], section[4] + section[5], section[9]):
            name, _, _, _, value, _ = struct.unpack_from("<IBBHQQ", raw, offset)
            start = strings[4] + name
            if raw[start:raw.index(b"\0", start)] == b"locallore_android_arm_deadline":
                address = value
    if address is None:
        raise ValueError("Native deadline initializer is absent from the executable")
    arrays = [section for section in sections if section[1] == 14]  # SHT_INIT_ARRAY
    if not arrays:
        raise ValueError("No native initialization array")
    offsets = {section[3] + index for section in arrays for index in range(0, section[5], 8)}
    retained = any(struct.unpack_from("<Q", raw, section[4] + index)[0] == address
                   for section in arrays for index in range(0, section[5], 8))
    machine = struct.unpack_from("<H", raw, 18)[0]
    relative = {62: 8, 183: 1027}[machine]
    for section in sections:
        if section[1] == 4:  # SHT_RELA; PIE initializer may be a relative addend.
            for offset in range(section[4], section[4] + section[5], section[9]):
                target, info, addend = struct.unpack_from("<QQq", raw, offset)
                if target in offsets and info & 0xffffffff == relative and addend == address:
                    retained = True
    if not retained:
        raise ValueError("Native deadline initializer is not retained in .init_array")
    return {"initializer_retained": True, "fixed_seconds": 90,
            "mechanism": "SIGALRM_default_action", "inherited_signal_unblocked": True}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", type=Path, required=True)
    parser.add_argument("--sdk", type=Path, required=True)
    parser.add_argument("--build-dir", type=Path, default=ROOT / "target/android-runtime/llama")
    parser.add_argument("--abi", choices=TARGETS, action="append")
    args = parser.parse_args()
    if platform.system() != "Windows":
        parser.error("This reproducible recipe currently supports Windows hosts only")
    source_check(args.source.resolve())
    ndk = args.sdk.resolve() / "ndk" / NDK
    if f"Pkg.Revision = {NDK}" not in (ndk / "source.properties").read_text():
        raise ValueError("Unreviewed NDK revision")
    cmake = args.sdk.resolve() / "cmake/3.22.1/bin/cmake.exe"
    ninja = cmake.with_name("ninja.exe")
    llvm = ndk / "toolchains/llvm/prebuilt/windows-x86_64"
    output = args.build_dir.resolve()
    output.mkdir(parents=True, exist_ok=True)
    linker = output / "native-linker.exe"
    run(["rustc", "+1.93.1", "--edition=2021", "-O", ROOT / "apps/android/native-linker.rs", "-o", linker])
    reports = {}
    for abi in args.abi or TARGETS:
        build = output / abi
        run([cmake, "-S", Path(__file__).parent, "-B", build, "-G", "Ninja",
             f"-DCMAKE_MAKE_PROGRAM={ninja}",
             f"-DCMAKE_TOOLCHAIN_FILE={ndk / 'build/cmake/android.toolchain.cmake'}",
             f"-DLLAMA_SOURCE_DIR={args.source.resolve()}", f"-DANDROID_ABI={abi}",
             "-DANDROID_PLATFORM=android-28", "-DANDROID_STL=c++_static", "-DCMAKE_BUILD_TYPE=Release"])
        run([cmake, "--build", build, "--target", "locallore-llama-spike", "--parallel", "4"])
        target = TARGETS[abi]
        env = os.environ.copy()
        env[f"CARGO_TARGET_{target.upper().replace('-', '_')}_LINKER"] = str(linker)
        env["LOCALLORE_ANDROID_CLANG"] = str(llvm / "bin/clang.exe")
        env["CARGO_ENCODED_RUSTFLAGS"] = "\x1f".join([
            "-C", f"link-arg=--target={target}28", "-C", f"link-arg=--sysroot={llvm / 'sysroot'}",
            "-C", "link-arg=-Wl,-z,max-page-size=16384"])
        run(["cargo", "+1.93.1", "build", "--locked", "--offline", "--release", "-p", "locallore",
             "--example", "runtime_spike", "--target", target, "--target-dir", output / "rust"], env)
        helper = build / "host-helper/locallore-llama-spike"
        oracle = output / "rust" / target / "release/examples/runtime_spike"
        machine = 62 if abi == "x86_64" else 183
        reports[abi] = {"helper": elf_report(helper, machine), "oracle": elf_report(oracle, machine),
                        "deadline": deadline_report(helper)}
        destination = output / f"{abi}-elf.json"
        destination.write_text(json.dumps(reports[abi], indent=2) + "\n", encoding="utf-8")
        print(json.dumps({"abi": abi, "helper": str(helper), "oracle": str(oracle), "report": str(destination)}), flush=True)
    source_check(args.source.resolve())


if __name__ == "__main__":
    main()
