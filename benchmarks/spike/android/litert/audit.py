"""Offline, stdlib-only identity and Android ABI audit for LiteRT-LM 0.18.1.

Does not load native code, install dependencies, access devices or fetch models.
The publisher AAR is experimental input, never a production app dependency here.
"""

import argparse
import hashlib
import io
import json
from pathlib import Path
import struct
import xml.etree.ElementTree as ET
import zipfile

VERSION = "0.18.1"
AAR_SHA256 = "05c6bdc8acda834efcca12c0ad5d06d2cd8c83e60770f056d8d222f699f3012b"
POM_SHA256 = "3d6ea70f41bc6305c5985a52c5f5d00da97402d6531c9a395f3145cb5c1a89a5"
ANDROID = "{http://schemas.android.com/apk/res/android}"
MAVEN = "{http://maven.apache.org/POM/4.0.0}"
MACHINES = {62: "x86_64", 183: "arm64-v8a"}


class AuditError(ValueError):
    pass


def digest(data):
    return hashlib.sha256(data).hexdigest()


def elf_info(data):
    """Inspect ELF64 little endian load segments, Android note and DT_NEEDED."""
    if len(data) < 64 or data[:6] != b"\x7fELF\x02\x01":
        raise AuditError("not_elf64_little_endian")
    machine = struct.unpack_from("<H", data, 18)[0]
    if machine not in MACHINES:
        raise AuditError("unsupported_elf_machine")
    offset = struct.unpack_from("<Q", data, 32)[0]
    width, count = struct.unpack_from("<HH", data, 54)
    if width != 56 or not 0 < count <= 128 or offset + width * count > len(data):
        raise AuditError("invalid_program_headers")
    segments = []
    for index in range(count):
        kind, flags, start, address, _, size, memory, align = struct.unpack_from(
            "<IIQQQQQQ", data, offset + width * index)
        if start + size > len(data):
            raise AuditError("truncated_segment")
        segments.append((kind, start, address, size, align))
    loads = [segment for segment in segments if segment[0] == 1]
    if not loads:
        raise AuditError("no_load_segments")
    android_notes = []
    dynamic = []
    for kind, start, _, size, _ in segments:
        if kind == 4:
            end = start + size
            while start + 12 <= end:
                name_size, description_size, note_type = struct.unpack_from("<III", data, start)
                start += 12
                name_end = start + name_size
                description_start = start + ((name_size + 3) & ~3)
                description_end = description_start + description_size
                if description_end > end:
                    raise AuditError("truncated_note")
                if data[start:name_end].rstrip(b"\0") == b"Android" and note_type == 1:
                    if description_size < 132:
                        raise AuditError("invalid_android_note")
                    description = data[description_start:description_end]
                    android_notes.append({
                        "api": struct.unpack_from("<I", description)[0],
                        "ndk": description[4:68].split(b"\0")[0].decode("ascii"),
                        "ndk_build": description[68:132].split(b"\0")[0].decode("ascii"),
                    })
                start = description_start + ((description_size + 3) & ~3)
        if kind == 2:
            if size % 16:
                raise AuditError("invalid_dynamic_size")
            dynamic.extend(struct.iter_unpack("<qQ", data[start:start + size]))
    if len(android_notes) != 1:
        raise AuditError("missing_or_duplicate_android_note")
    tags = {tag: value for tag, value in dynamic if tag in (5, 10)}
    if set(tags) != {5, 10}:
        raise AuditError("missing_dynamic_strings")
    strings = None
    for _, start, address, size, _ in loads:
        if address <= tags[5] and tags[5] + tags[10] <= address + size:
            begin = start + tags[5] - address
            strings = data[begin:begin + tags[10]]
    if strings is None:
        raise AuditError("dynamic_strings_outside_load")
    needed = []
    for tag, value in dynamic:
        if tag == 1:
            end = strings.find(b"\0", value)
            if value >= len(strings) or end < 0:
                raise AuditError("invalid_needed_string")
            needed.append(strings[value:end].decode("ascii"))
    return {
        "abi": MACHINES[machine], "bytes": len(data), "sha256": digest(data),
        "android_ident": android_notes[0], "needed": needed,
        "load_alignments": [segment[4] for segment in loads],
        "elf_16k_load_alignment": all(
            segment[4] >= 16384 and (segment[1] - segment[2]) % 16384 == 0
            for segment in loads),
    }


def inspect_aar(data, target_abi, api):
    if target_abi not in MACHINES.values() or type(api) is not int or api < 1:
        raise AuditError("invalid_target")
    try:
        with zipfile.ZipFile(io.BytesIO(data)) as archive:
            names = archive.namelist()
            if len(names) != len(set(names)):
                raise AuditError("duplicate_zip_entries")
            manifest_data = archive.read("AndroidManifest.xml")
            manifest = ET.fromstring(manifest_data)
            sdk = manifest.find("uses-sdk")
            if sdk is None:
                raise AuditError("missing_min_sdk")
            minimum = int(sdk.attrib[ANDROID + "minSdkVersion"])
            native = []
            for name in sorted(names):
                if name.startswith("jni/") and name.endswith(".so"):
                    info = elf_info(archive.read(name))
                    if name != "jni/" + info["abi"] + "/liblitertlm_jni.so":
                        raise AuditError("native_path_machine_mismatch")
                    native.append(dict(path=name, **info))
            abis = [item["abi"] for item in native]
            if len(abis) != len(set(abis)):
                raise AuditError("duplicate_native_abi")
            target = next((item for item in native if item["abi"] == target_abi), None)
            conservative_floor = max(minimum, target["android_ident"]["api"]) if target else None
            return {
                "manifest_min_sdk": minimum,
                "manifest_permissions": sorted(element.attrib[ANDROID + "name"]
                    for element in manifest if element.tag.startswith("uses-permission")),
                "manifest_sha256": digest(manifest_data), "native": native,
                "classes_sha256": digest(archive.read("classes.jar")),
                "license_sha256": digest(archive.read("LICENSE")),
                "notice_sha256": digest(archive.read("THIRD_PARTY_NOTICE.txt")),
                "target_abi": target_abi, "target_api": api,
                "conservative_api_floor": conservative_floor,
                "artifact_gate": "eligible_for_runtime_test" if target and api >= conservative_floor
                    else "blocked_abi" if not target else "blocked_api",
                "runtime_load_verified": False,
            }
    except (zipfile.BadZipFile, KeyError, ET.ParseError, UnicodeError, struct.error) as error:
        raise AuditError("malformed_artifact") from error


def inspect_pom(data):
    project = ET.fromstring(data)
    def value(node, name):
        result = node.findtext(MAVEN + name)
        if result is None:
            raise AuditError("missing_pom_field")
        return result
    coordinates = [value(project, key) for key in ("groupId", "artifactId", "version", "packaging")]
    if coordinates != ["com.google.ai.edge.litertlm", "litertlm-android", VERSION, "aar"]:
        raise AuditError("unexpected_coordinates")
    return [{key: value(dep, key) for key in ("groupId", "artifactId", "version", "scope")}
            for dep in project.findall(MAVEN + "dependencies/" + MAVEN + "dependency")]


def audit(aar, pom, target_abi, api):
    if digest(aar) != AAR_SHA256 or digest(pom) != POM_SHA256:
        raise AuditError("artifact_identity_mismatch")
    return dict(version=1, coordinate="com.google.ai.edge.litertlm:litertlm-android:" + VERSION,
                aar_bytes=len(aar), aar_sha256=digest(aar), pom_sha256=digest(pom),
                declared_dependencies=inspect_pom(pom), **inspect_aar(aar, target_abi, api))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--aar", required=True, type=Path)
    parser.add_argument("--pom", required=True, type=Path)
    parser.add_argument("--abi", choices=sorted(MACHINES.values()), required=True)
    parser.add_argument("--api", type=int, required=True)
    args = parser.parse_args()
    try:
        report = audit(args.aar.read_bytes(), args.pom.read_bytes(), args.abi, args.api)
    except (AuditError, OSError, ValueError):
        print('{"status":"error","error":"artifact_audit_failed"}')
        return 2
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0 if report["artifact_gate"] == "eligible_for_runtime_test" else 2


if __name__ == "__main__":
    raise SystemExit(main())
