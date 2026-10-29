"""Explicit offline NDK29 x86_64 build; never execute the resulting Android probe.

Copyright 2026 LocalLore contributors. SPDX-License-Identifier: Apache-2.0
"""
import argparse
import json
import os
from pathlib import Path
import struct
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
from benchmarks import receipt_avd_environment as env
from benchmarks import android_process_verification as capture

NDK = "29.0.14206865"
TARGET = "x86_64-linux-android35"
SCOPE = "android_author_process_probe_build_v1"
GO = b"LL_ANDROID_AUTHOR_PROCESS_PROBE_BUILD_V1\n"
TEMP = Path("D:/Dev/_Temp")
MAX_BINARY = 64 * 1024 * 1024


def need(value, reason):
    env.require(value, reason)


def physical_d(path, *, exists=True, directory=False):
    path = env.safe_path(path, exists=exists, directory=directory)
    need(path.is_absolute() and path.drive.upper() == "D:" and
         (not exists or path.resolve(strict=True) == path), "physical_D")
    return path


def tool_inputs(ndk):
    ndk = env.safe_path(ndk, directory=True)
    properties = ndk / "source.properties"
    need(ndk.name == NDK and f"Pkg.Revision = {NDK}" in properties.read_text(encoding="utf-8"), "NDK_revision")
    llvm = ndk / "toolchains/llvm/prebuilt/windows-x86_64"
    paths = [properties, llvm / "bin/clang.exe", llvm / "bin/ld.lld.exe",
             llvm / "sysroot/usr/include/x86_64-linux-android/asm/unistd_64.h",
             llvm / "sysroot/usr/include/asm-generic/unistd.h"]
    return llvm, [env.binding(path) for path in sorted(paths)]


def command(llvm, output):
    return [str(llvm / "bin/clang.exe"), "--no-default-config", "--target=" + TARGET,
            "--sysroot=" + str(llvm / "sysroot"), "-std=c11", "-Wall", "-Wextra", "-Werror",
            "-O2", "-fPIE", "-pie", "-Wl,-z,relro,-z,now", "-Wl,-z,max-page-size=16384",
            str(ROOT / "benchmarks/native/android_author_process_probe.c"), "-o",
            str(output / "android-author-process-probe-v1")]


def variables():
    removed = {"CL", "_CL_", "CC", "CFLAGS", "CPPFLAGS", "LDFLAGS", "CPATH", "C_INCLUDE_PATH",
               "CPLUS_INCLUDE_PATH", "OBJC_INCLUDE_PATH", "LIBRARY_PATH", "COMPILER_PATH",
               "GCC_EXEC_PREFIX", "CCC_OVERRIDE_OPTIONS", "CLANG_CONFIG_FILE", "SDKROOT", "INCLUDE", "LIB"}
    value = {key: item for key, item in os.environ.items() if key.upper() not in removed}
    value.update(TEMP=str(TEMP), TMP=str(TEMP), TMPDIR=str(TEMP))
    return value


def verify_inputs(request):
    need(request["version"] == 1 and request["scope"] == SCOPE and
         request["ndk_revision"] == NDK and request["target"] == TARGET, "request")
    for pin in [request["source"], request["builder"], *request["tools"]]:
        env.check_binding(pin)
    need(request["source"] == env.binding(ROOT / "benchmarks/native/android_author_process_probe.c") and
         request["builder"] == env.binding(Path(__file__).resolve()), "source")
    llvm, tools = tool_inputs(Path(request["ndk"]))
    need(tools == request["tools"] and command(llvm, Path(request["output"])) == request["command"], "toolchain")
    need(request["environment"] == {key: str(TEMP) for key in ("TEMP", "TMP", "TMPDIR")}, "environment")


def elf_image(path):
    env.safe_path(path)
    need(64 <= path.stat().st_size <= MAX_BINARY, "ELF_size")
    raw = path.read_bytes()
    need(64 <= len(raw) <= MAX_BINARY and raw[:7] == b"\x7fELF\x02\x01\x01", "ELF_header")
    kind, machine = struct.unpack_from("<HH", raw, 16)
    phoff = struct.unpack_from("<Q", raw, 32)[0]
    phsize, phcount = struct.unpack_from("<HH", raw, 54)
    need(kind == 3 and machine == 62 and phsize == 56 and 1 <= phcount <= 128 and
         phoff + phsize * phcount <= len(raw), "ELF_target")
    segments = [struct.unpack_from("<IIQQQQQQ", raw, phoff + phsize * index) for index in range(phcount)]
    for segment in segments:
        need(segment[2] + segment[5] <= len(raw), "ELF_segment")
    interpreters = [raw[part[2]:part[2] + part[5]] for part in segments if part[0] == 3]
    need(interpreters == [b"/system/bin/linker64\0"], "ELF_interpreter")
    dynamic = [part for part in segments if part[0] == 2]
    need(len(dynamic) == 1 and dynamic[0][5] % 16 == 0, "ELF_dynamic")
    part = dynamic[0]
    entries = [struct.unpack_from("<QQ", raw, part[2] + offset) for offset in range(0, part[5], 16)]
    strings = [value for tag, value in entries if tag == 5]
    sizes = [value for tag, value in entries if tag == 10]
    need(len(strings) == len(sizes) == 1 and 0 < sizes[0] <= 1024 * 1024, "ELF_strings")
    loads = [p for p in segments if p[0] == 1 and p[3] <= strings[0] and strings[0] + sizes[0] <= p[3] + p[5]]
    need(len(loads) == 1, "ELF_strings")
    offset = loads[0][2] + strings[0] - loads[0][3]
    table = raw[offset:offset + sizes[0]]
    needed = []
    for tag, value in entries:
        if tag == 1:
            need(value < len(table) and b"\0" in table[value:], "ELF_needed")
            needed.append(table[value:].split(b"\0", 1)[0].decode("ascii"))
    need(len(needed) == len(set(needed)) and set(needed) <= {"libc.so", "libdl.so", "libm.so"} and
         "libc.so" in needed, "ELF_dependencies")
    return dict(elf_class=2, machine=machine, type=kind, interpreter="/system/bin/linker64", needed=sorted(needed))


def worker(output, digest):
    need(sys.stdin.buffer.read(len(GO)) == GO, "barrier")
    request = env.read_bound_json(output / "request-v1.json", digest)
    physical_d(output, directory=True)
    need(Path(request["output"]) == output, "output_binding")
    verify_inputs(request)
    need(not os.path.lexists(output / "android-author-process-probe-v1"), "create_only_binary")
    capture.run_command(output, "compile", request["command"], ROOT, variables())
    verify_inputs(request)
    elf_image(output / "android-author-process-probe-v1")
    return 0


def build(ndk, output):
    need(os.name == "nt", "Windows_host")
    physical_d(ROOT, directory=True)
    physical_d(TEMP, directory=True)
    need(Path.cwd() == ROOT, "physical_cwd")
    output = physical_d(output, exists=False)
    need(not os.path.lexists(output), "create_only_output")
    llvm, tools = tool_inputs(ndk)
    output.mkdir()
    request = dict(version=1, scope=SCOPE, ndk_revision=NDK, target=TARGET, ndk=str(ndk), output=str(output),
                   source=env.binding(ROOT / "benchmarks/native/android_author_process_probe.c"),
                   builder=env.binding(Path(__file__).resolve()), tools=tools, command=command(llvm, output),
                   environment={key: str(TEMP) for key in ("TEMP", "TMP", "TMPDIR")})
    env.create_json(output / "request-v1.json", request)
    started_pin = None

    def started(child):
        nonlocal started_pin
        env.create_json(output / "started-v1.json", dict(worker=env.process_identity(child.pid)))
        started_pin = env.binding(output / "started-v1.json")
        return True

    owner = env.supervise([sys.executable, "-I", "-S", "-B", str(Path(__file__).resolve()), "_worker",
                            str(output), env.digest(output / "request-v1.json")], GO, output, 300, started)
    env.create_json(output / "owner-result-v1.json", owner)
    binary = compiled = image = None
    passed = False
    try:
        verify_inputs(request)
        need(owner["status"] == "child_exited" and type(owner["worker_returncode"]) is int and
             owner["worker_returncode"] == 0 and owner["cleanup_complete"] is True and
             owner["output_capture_complete"] is True and owner["stderr_bytes"] == 0 and
             started_pin is not None, "owner")
        compiled = env.binding(output / "compile.json")
        command_result = env.read_json(output / "compile.json")
        need(command_result["returncode"] == 0 and command_result["capture_complete"] is True and
             command_result["timed_out"] is False and command_result["output_limit"] is False, "compile")
        image = elf_image(output / "android-author-process-probe-v1")
        binary = env.binding(output / "android-author-process-probe-v1")
        passed = True
    except (OSError, ValueError, KeyError, TypeError, env.EnvironmentRefused):
        if os.path.lexists(output / "compile.json"):
            compiled = env.binding(output / "compile.json")
        if os.path.lexists(output / "android-author-process-probe-v1"):
            path = env.safe_path(output / "android-author-process-probe-v1")
            if path.stat().st_size <= MAX_BINARY:
                binary = env.binding(path)
    result = dict(version=1, scope=SCOPE, ndk_revision=NDK, target=TARGET, source=request["source"],
                  builder=request["builder"], tools=tools, command=request["command"], environment=request["environment"],
                  request=env.binding(output / "request-v1.json"), started=started_pin,
                  owner=env.binding(output / "owner-result-v1.json"), compile=compiled, binary=binary, elf=image,
                  passed=passed, feature_acceptance=False)
    env.create_json(output / "result-v1.json", result)
    print(json.dumps(dict(passed=passed,manifest=env.binding(output / "result-v1.json"), owner=owner)))
    return 0 if passed else 1


def main(argv=None):
    os.environ.update(TEMP=str(TEMP), TMP=str(TEMP), TMPDIR=str(TEMP))
    args = sys.argv[1:] if argv is None else argv
    if len(args) == 3 and args[0] == "_worker":
        return worker(Path(args[1]), args[2])
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--ndk", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    values = parser.parse_args(args)
    return build(values.ndk, values.output)


if __name__ == "__main__":
    raise SystemExit(main())
