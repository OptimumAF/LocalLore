"""Check the current debug APK's capability/ABI/alignment contract; never extract it.

Copyright 2026 LocalLore contributors. SPDX-License-Identifier: Apache-2.0
"""
import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import struct
import subprocess
import zipfile

PERMISSION = "org.locallore.app.DYNAMIC_RECEIVER_NOT_EXPORTED_PERMISSION"
ABIS = {"x86_64": 62, "arm64-v8a": 183}
# Exact candidate SDK; ordinary APKs must never contain these entries.
LITERT_NATIVE_HASHES = {
    "lib/arm64-v8a/liblitertlm_jni.so": "cf4c55139c6fc86425ecfe75f8a907e6193ca665ecc19fbabcaba7ab361bdc43",
    "lib/x86_64/liblitertlm_jni.so": "ba879b2b46be1f7e08df8c8365a276cfc54c1e21383090e058a24f25e603cdd7",
}
LITERT_NOTICES = {
    "assets/notices/litertlm-0.18.1/LICENSE": "ec40a2da15ab0e8b44a9f787ab210203d3cad32572f5f99744a88eb90ff9ba4e",
    "assets/notices/litertlm-0.18.1/THIRD_PARTY_NOTICE.txt": "52a70c82685debf85d4ea9d677615b8636ffd3b75435ce71f247bf5982fb2ba2",
}


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


def audit_zip(path, *, litert=False):
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
        if litert:
            expected |= set(LITERT_NATIVE_HASHES)
        require({library["entry"] for library in libraries} == expected, "Native library set changed; review dependencies")
        if litert:
            for name, digest in {**LITERT_NATIVE_HASHES, **LITERT_NOTICES}.items():
                require(name in names, "Missing pinned SDK binary or notice")
                entry = archive.getinfo(name)
                require(0 < entry.file_size <= 32 * 1024 * 1024, "Invalid SDK binary or notice size")
                require(hashlib.sha256(archive.read(entry)).hexdigest() == digest, "SDK binary or notice changed")
    return libraries


def audit_manifest(badging, tree, package="org.locallore.app"):
    require(package in ("org.locallore.app", "org.locallore.app.capacity", "org.locallore.app.capacityrelief", "org.locallore.app.capacityv3",
                        "org.locallore.app.capacityreliefv3", "org.locallore.app.capacityfaultsv3",
                        "org.locallore.app.capacityv4", "org.locallore.app.capacityreliefv4", "org.locallore.app.capacityfaultsv4",
                        "org.locallore.app.externalverify", "org.locallore.app.litertverify",
                        "org.locallore.app.cancelack"),
            "Unreviewed app package")
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


def audit_fixed_metadata(tree, namespace, expected):
    """Require one exact typed profile, separate from unrelated AndroidX metadata."""
    require(namespace in ("org.locallore.capacity.", "org.locallore.capacity.relief."),
            "Unreviewed profile namespace")
    require(expected and all(type(value) is int and value >= 0 for value in expected.values()),
            "Invalid fixed profile")
    names = re.findall(r':name\([^)]*\)="(org\.locallore\.capacity[^\"]*)"', tree)
    require(sorted(names) == sorted(namespace + key for key in expected),
            "Unexpected, missing or duplicate capacity profile metadata")
    for key, value in expected.items():
        pattern = (r'E: meta-data \([^\n]*\)\s+[^\n]*:name\([^)]*\)="'
                   + re.escape(namespace + key)
                   + r'"[^\n]*\n\s+[^\n]*:value\([^)]*\)='
                   + str(value) + r'[ \t]*\r?$')
        require(len(re.findall(pattern, tree, re.M)) == 1, "Wrong fixed capacity metadata value")


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
    parser.add_argument("--litert-verification", action="store_true", help="Audit only the explicit pinned LiteRT debug candidate")
    args = parser.parse_args(argv)
    try:
        libraries = audit_zip(args.apk, litert=args.litert_verification)
        aapt = str(aapt2_path())
        def dump(*arguments):
            return subprocess.run([aapt, "dump", *arguments], check=True, capture_output=True,
                                  text=True, encoding="utf-8", shell=False).stdout
        permissions = audit_manifest(dump("badging", str(args.apk)),
                                     dump("xmltree", str(args.apk), "--file", "AndroidManifest.xml"),
                                     "org.locallore.app.litertverify" if args.litert_verification else "org.locallore.app")
        print(json.dumps({"status": "passed", "permissions": permissions, "libraries": libraries}, indent=2))
        return 0
    except (AuditError, OSError, zipfile.BadZipFile, subprocess.CalledProcessError, struct.error) as error:
        print(f"APK audit failed: {error}")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
