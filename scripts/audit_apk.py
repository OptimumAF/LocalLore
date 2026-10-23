"""Check the current debug APK's capability/ABI/alignment contract; never extract it.

Copyright 2026 LocalLore contributors. SPDX-License-Identifier: Apache-2.0
"""
import argparse
import json
import os
from pathlib import Path
import re
import struct
import subprocess
import zipfile

PERMISSION = "org.locallore.app.DYNAMIC_RECEIVER_NOT_EXPORTED_PERMISSION"
ABIS = {"x86_64": 62, "arm64-v8a": 183}


class AuditError(ValueError):
    """A build artifact does not meet the current contract."""


def require(condition, message):
    if not condition:
        raise AuditError(message)


def elf_alignments(data, machine):
    require(len(data) >= 64 and data[:7] == b"\x7fELF\x02\x01\x01", "Expected little-endian ELF64")
    require(struct.unpack_from("<HH", data, 16) == (3, machine), "Wrong ELF type or ABI")
    offset = struct.unpack_from("<Q", data, 32)[0]
    size, count = struct.unpack_from("<HH", data, 54)
    require(size == 56 and 0 < count <= 128 and offset + size * count <= len(data), "Invalid ELF headers")
    alignments = []
    for index in range(count):
        position = offset + index * size
        if struct.unpack_from("<I", data, position)[0] != 1:
            continue
        file_offset, address, _, file_size, memory_size, alignment = struct.unpack_from("<QQQQQQ", data, position + 8)
        require(alignment >= 16384 and alignment & (alignment - 1) == 0, "ELF LOAD alignment below 16 KiB or invalid")
        require(file_offset % alignment == address % alignment, "ELF LOAD address/offset mismatch")
        require(file_size <= memory_size and file_offset + file_size <= len(data), "ELF LOAD outside library")
        alignments.append(alignment)
    require(alignments, "ELF has no LOAD segments")
    return alignments


def audit_zip(path):
    libraries = []
    with zipfile.ZipFile(path) as archive, open(path, "rb") as raw:
        entries = archive.infolist()
        names = [entry.filename for entry in entries]
        require(len(names) <= 4096 and len(names) == len(set(names)), "Excessive or duplicate APK entries")
        require(not any("lantern_quay_cases" in name for name in names), "Legacy recorded fixture packaged")
        require("AndroidManifest.xml" in names, "Missing Android manifest")
        for entry in entries:
            if not entry.filename.endswith(".so"):
                continue
            parts = entry.filename.split("/")
            require(len(parts) == 3 and parts[0] == "lib" and parts[1] in ABIS, "Unexpected native ABI/path")
            require(entry.compress_type == zipfile.ZIP_STORED, "Native libraries must be uncompressed")
            require(0 < entry.file_size <= 64 * 1024 * 1024, "Invalid native library size")
            raw.seek(entry.header_offset)
            header = raw.read(30)
            require(len(header) == 30 and header[:4] == b"PK\x03\x04", "Invalid ZIP local header")
            name_size, extra_size = struct.unpack_from("<HH", header, 26)
            data_offset = entry.header_offset + 30 + name_size + extra_size
            require(data_offset % 16384 == 0, "Native ZIP data not aligned to 16 KiB")
            alignment = elf_alignments(archive.read(entry), ABIS[parts[1]])
            libraries.append({"entry": entry.filename, "elf_load_alignment": alignment})
        expected = {f"lib/{abi}/{library}" for abi in ABIS for library in
                    ("liblocallore_android.so", "libandroidx.graphics.path.so")}
        require({library["entry"] for library in libraries} == expected, "Native library set changed; review dependencies")
    return libraries


def audit_manifest(badging, tree, package="org.locallore.app"):
    require(package in ("org.locallore.app", "org.locallore.app.capacity"), "Unreviewed app package")
    permission = package + ".DYNAMIC_RECEIVER_NOT_EXPORTED_PERMISSION"
    require(re.search(r"^package: name='" + re.escape(package) + r"' ", badging, re.M), "Wrong app package")
    require(re.search(r"^minSdkVersion:'26'$", badging, re.M), "Minimum SDK changed")
    require(re.search(r"^targetSdkVersion:'36'$", badging, re.M), "Target SDK changed")
    uses = re.findall(r"^uses-permission[^:]*: name='([^']+)'", badging, re.M)
    require(uses == [permission], "Unexpected requested permissions")
    # Verify the one requested permission is defined with signature protection.
    declarations = []
    lines = tree.splitlines()
    for index, line in enumerate(lines):
        match = re.match(r"(\s*)E: permission \(", line)
        if not match:
            continue
        block = []
        for following in lines[index + 1:]:
            if following.strip() and len(following) - len(following.lstrip()) <= len(match[1]):
                break
            block.append(following)
        declarations.append("\n".join(block))
    require(len(declarations) == 1, "Unexpected permission declarations")
    require(re.search(r':name\([^)]*\)="' + re.escape(permission) + r'"', declarations[0]), "Permission owner changed")
    require(re.search(r':protectionLevel\([^)]*\)=0x0*2\b', declarations[0]), "Receiver permission must be signature protected")
    return uses


def aapt2_path():
    for variable in ("ANDROID_HOME", "ANDROID_SDK_ROOT"):
        value = os.environ.get(variable)
        if value:
            candidate = Path(value) / "build-tools" / "35.0.0" / ("aapt2.exe" if os.name == "nt" else "aapt2")
            require(candidate.is_file(), "Install Build Tools 35.0.0 in the configured SDK")
            return candidate
    # The app's existing Gradle build supports local.properties; this audit asks
    # for an explicit environment path rather than guessing another SDK.
    raise AuditError("Set ANDROID_HOME or ANDROID_SDK_ROOT for APK auditing")


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("apk", type=Path)
    args = parser.parse_args(argv)
    try:
        libraries = audit_zip(args.apk)
        aapt = str(aapt2_path())
        def dump(*arguments):
            return subprocess.run([aapt, "dump", *arguments], check=True, capture_output=True,
                                  text=True, encoding="utf-8", shell=False).stdout
        permissions = audit_manifest(dump("badging", str(args.apk)),
                                     dump("xmltree", str(args.apk), "--file", "AndroidManifest.xml"))
        print(json.dumps({"status": "passed", "permissions": permissions, "libraries": libraries}, indent=2))
        return 0
    except (AuditError, OSError, zipfile.BadZipFile, subprocess.CalledProcessError, struct.error) as error:
        print(f"APK audit failed: {error}")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
