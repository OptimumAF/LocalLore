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
MODEL_PUBLICATION_JNI = "Java_org_locallore_app_NativeModelPublication_publishNoReplace"
RECEIPT_SETUP_ACTIVITIES = (
    "ReceiptSetupAcceptActivity", "ReceiptSetupCancelBeforeActivity",
    "ReceiptSetupCancelAfterActivity", "ReceiptSetupDrainActivity",
    "ReceiptComposeCancellationActivity",
)
RECEIPT_SETUP_CLASSES = (
    "ReceiptSetupFixtureActivity", *RECEIPT_SETUP_ACTIVITIES,
    "ReceiptSetupFailureTrace", "ReceiptSetupFailureSnapshot", "ReceiptSetupSourceProgress",
    "ReceiptSetupFailureCase", "ReceiptSetupFailureEvent", "ReceiptSetupFailureCode",
    "ReceiptSetupFailureReporter",
    "ComposeCancellationProof", "ComposeCancellationPhase",
    "OrdinaryRouteProof", "OrdinaryRoutePhase",
)
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


def aapt_text(value):
    """Accept observed uniform LF/CRLF tool framing; never erase lone CR/control bytes."""
    require(type(value) is str and len(value) <= 4 * 1024 * 1024, "Invalid aapt output")
    if "\r" in value:
        remainder = value.replace("\r\n", "")
        require("\r" not in remainder and "\n" not in remainder, "Mixed or malformed aapt framing")
        value = value.replace("\r\n", "\n")
    require(not any((ord(c) < 32 and c not in "\t\n") or c in "\x7f\x85\u2028\u2029" for c in value),
            "Invalid aapt control character")
    return value


def audit_sdk(badging):
    badging = aapt_text(badging)
    selected = [line for line in badging.split("\n")
                if re.match(r"^\s*(?:minSdkVersion|targetSdkVersion|sdkVersion)\b", line)]
    require(selected == ["minSdkVersion:'26'", "targetSdkVersion:'36'"],
            "Wrong, missing, duplicate or malformed SDK contract")


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


def elf_model_publication_export(data, machine):
    """Require the candidate's defined public JNI function, not an embedded name.

    Read only bounded ELF64 section/dynamic-symbol tables and executable LOAD
    mappings. This is packaging evidence; it never loads or executes the library.
    """
    require(type(data) in (bytes, bytearray) and 64 <= len(data) <= 64 * 1024 * 1024,
            "Invalid model publication ELF size")
    elf_alignments(data, machine)
    offset = struct.unpack_from("<Q", data, 40)[0]
    size, count, names = struct.unpack_from("<HHH", data, 58)
    require(size == 64 and 0 < count <= 8192 and offset >= 64 and offset + size * count <= len(data)
            and (names == 0 or names < count), "Invalid model publication ELF section table")
    sections = [struct.unpack_from("<IIQQQQIIQQ", data, offset + index * size) for index in range(count)]
    require(sections[0][1] == 0, "Invalid model publication null section")
    for section in sections:
        require(section[4] <= len(data) and (section[1] == 8 or section[4] + section[5] <= len(data)),
                "Model publication ELF section outside library")
    dynamic = [section for section in sections if section[1] == 11]
    require(len(dynamic) == 1, "Missing or ambiguous model publication dynamic symbols")
    symbols = dynamic[0]
    require(symbols[9] == 24 and symbols[5] % 24 == 0 and 1 <= symbols[5] // 24 <= 65536
            and 0 < symbols[6] < count and symbols[7] <= symbols[5] // 24,
            "Invalid model publication dynamic symbol table")
    strings = sections[symbols[6]]
    require(strings[1] == 3 and 0 < strings[5] <= 16 * 1024 * 1024
            and symbols[2] & 2 and strings[2] & 2, "Invalid model publication symbol strings")
    text = data[strings[4]:strings[4] + strings[5]]
    require(text[:1] == text[-1:] == b"\0", "Unterminated model publication symbol strings")

    def mapped(section, executable=False):
        header = struct.unpack_from("<Q", data, 32)[0]
        header_size, header_count = struct.unpack_from("<HH", data, 54)
        for index in range(header_count):
            position = header + index * header_size
            kind, flags = struct.unpack_from("<II", data, position)
            if kind != 1 or (executable and not flags & 1):
                continue
            file_offset, address, _, file_size, _, _ = struct.unpack_from("<QQQQQQ", data, position + 8)
            delta = section[3] - address
            if 0 <= delta <= file_size and section[5] <= file_size - delta and file_offset + delta == section[4]:
                return True
        return False

    require(mapped(symbols) and mapped(strings), "Unmapped model publication dynamic symbols")
    wanted = MODEL_PUBLICATION_JNI.encode("ascii") + b"\0"
    found = 0
    for position in range(symbols[4], symbols[4] + symbols[5], 24):
        name, info, visibility, section_index, address, function_size = struct.unpack_from("<IBBHQQ", data, position)
        require(name < len(text), "Model publication symbol name outside strings")
        if text[name:name + len(wanted)] != wanted:
            continue
        require(info == 0x12 and visibility == 0 and 0 < section_index < min(count, 0xFF00),
                "Model publication symbol must be defined GLOBAL DEFAULT FUNC")
        definition = sections[section_index]
        delta = address - definition[3]
        require(definition[1] == 1 and definition[2] & 6 == 6 and mapped(definition, executable=True)
                and 0 <= delta < definition[5] and 0 < function_size <= definition[5] - delta,
                "Model publication symbol outside executable definition")
        found += 1
    require(found == 1, "Missing or ambiguous model publication JNI export symbol")
    return MODEL_PUBLICATION_JNI


def audit_zip(path, *, litert=False, model_picker=False, model_volume=False, model_receipt=False,
              physical_model=False):
    require(not model_picker or litert, "Model picker fixtures require the explicit SDK profile")
    require(not model_volume or (litert and not model_picker), "Receipt volume fixture requires its separate SDK profile")
    require(not model_receipt or model_volume, "Receipt setup fixtures require the explicit volume profile")
    require(not physical_model or (litert and not any((model_picker, model_volume, model_receipt))),
            "Physical model fixtures require their separate SDK profile")
    libraries = []
    with zipfile.ZipFile(path) as archive, open(path, "rb") as raw:
        entries = archive.infolist()
        names = [entry.filename for entry in entries]
        require(len(names) <= 4096 and len(names) == len(set(names)), "Excessive or duplicate APK entries")
        require(not any("lantern_quay_cases" in name for name in names), "Legacy recorded fixture packaged")
        require("AndroidManifest.xml" in names, "Missing Android manifest")
        dex = [entry for entry in entries if re.fullmatch(r"classes(?:[2-9]|[1-9][0-9]+)?\.dex", entry.filename)]
        require(len(dex) <= 32 and sum(entry.file_size for entry in dex) <= 128 * 1024 * 1024,
                "Excessive DEX contents")
        fixture_present = False
        fixture_activity_present = False
        interruption_present = False
        interruption_activity_present = False
        pending_present = False
        pending_activity_present = False
        receipt_service_present = False
        receipt_fixture_present = False
        receipt_setup_present = set()
        recovery_present = False
        recovery_activity_present = False
        physical_present = set()
        for entry in dex:
            require(0 < entry.file_size <= 32 * 1024 * 1024, "Invalid DEX size")
            contents = archive.read(entry)
            for name in (b"PhysicalModelPolicy", b"AndroidPhysicalModelAccess", b"PhysicalModelSetupFixtureActivity"):
                if name in contents:
                    physical_present.add(name)
            require(not re.search(rb"PhysicalModel(?:Preflight|Import|Cancellation|Gift|Dialogue|Reopen)Test", contents),
                    "Physical instrumentation packaged in app")
            fixture_present |= b"ModelPickerFixture" in contents
            fixture_activity_present |= b"ModelPickerFixtureActivity" in contents
            interruption_present |= b"ModelPickerInterruption" in contents
            interruption_activity_present |= b"ModelPickerInterruptionFixtureActivity" in contents
            pending_present |= b"ModelPickerPending" in contents
            pending_activity_present |= b"ModelPickerPendingFixtureActivity" in contents
            receipt_service_present |= b"ReceiptProofService" in contents
            receipt_fixture_present |= b"ReceiptAndroidFixture" in contents
            require(b"ReceiptVolumeQualificationTest" not in contents, "Receipt test packaged in app")
            require(b"ReceiptReal" not in contents, "Real candidate instrumentation packaged in app")
            require(b"LiteRtSendTraceTest" not in contents, "LiteRT send test packaged in app")
            require(b"LiteRtCallbackTraceTest" not in contents, "LiteRT callback test packaged in app")
            require(b"LiteRtCallbackIntegrationTest" not in contents, "LiteRT callback integration test packaged in app")
            require(b"LiteRtStatusTraceTest" not in contents, "LiteRT status test packaged in app")
            require(b"LiteRtStatusIntegrationTest" not in contents, "LiteRT status integration test packaged in app")
            for name in RECEIPT_SETUP_CLASSES:
                if name.encode("ascii") in contents:
                    receipt_setup_present.add(name)
            require(all(name not in contents for name in
                        (b"ReceiptSetupQualificationTest", b"ReceiptSetupRestartTest", b"ReceiptSetupFailureTraceTest",
                         b"ReceiptSetupFailureTransportTest", b"ReceiptComposeCancellationTest",
                         b"ReceiptComposeCancelTest", b"ReceiptComposeRecoverTest", b"ReceiptComposeReopenTest",
                         b"ComposeCancellationProofTest", b"ReceiptOrdinaryRouteTest", b"ReceiptOrdinaryStartTest",
                         b"ReceiptOrdinaryDialogueTest", b"ReceiptOrdinaryReopenTest", b"OrdinaryRouteProofTest")),
                    "Receipt setup test packaged in app")
            recovery_present |= b"ModelSetupRecovery" in contents
            recovery_activity_present |= b"ModelSetupRecoveryFixtureActivity" in contents
            require(b"ModelPickerDocumentsProvider" not in contents, "Test provider packaged in app")
            require(b"ModelPickerInterruptionTest" not in contents, "Interruption test packaged in app")
            require(b"ModelPickerPendingTest" not in contents, "Pending-picker test packaged in app")
            require(b"ModelSetupRecoveryTest" not in contents, "Setup recovery test packaged in app")
        require(fixture_present == model_picker, "Model picker fixture leaked or missing")
        require(interruption_present == model_picker, "Interruption fixture leaked or missing")
        require(pending_present == model_picker, "Pending-picker fixture leaked or missing")
        require(recovery_present == model_picker, "Setup recovery fixture leaked or missing")
        require(not model_picker or fixture_activity_present, "Missing fixture Activity implementation")
        require(not model_picker or interruption_activity_present, "Missing interruption Activity implementation")
        require(not model_picker or pending_activity_present, "Missing pending-picker Activity implementation")
        require(not model_volume or litert, "Receipt volume fixture requires the SDK candidate")
        require(receipt_service_present == model_volume, "Receipt service leaked or missing")
        require(receipt_fixture_present == model_volume, "Receipt fixture leaked or missing")
        expected_setup = set(RECEIPT_SETUP_CLASSES) if model_receipt else set()
        require(receipt_setup_present == expected_setup, "Receipt setup fixture leaked or missing")
        require(not model_picker or recovery_activity_present, "Missing setup recovery Activity implementation")
        require(b"PhysicalModelSetupFixtureActivity" not in physical_present or physical_model,
                "Physical setup fixture leaked")
        require(not physical_model or {b"PhysicalModelPolicy", b"AndroidPhysicalModelAccess"} <= physical_present,
                "Missing physical model implementation")
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
            contents = archive.read(entry)
            alignment = elf_alignments(contents, ABIS[parts[1]])
            if litert and parts[2] == "liblocallore_android.so":
                elf_model_publication_export(contents, ABIS[parts[1]])
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
    badging, tree = aapt_text(badging), aapt_text(tree)
    require(package in ("org.locallore.app", "org.locallore.app.capacity", "org.locallore.app.capacityrelief", "org.locallore.app.capacityv3",
                        "org.locallore.app.capacityreliefv3", "org.locallore.app.capacityfaultsv3",
                        "org.locallore.app.capacityv4", "org.locallore.app.capacityreliefv4", "org.locallore.app.capacityfaultsv4",
                        "org.locallore.app.externalverify", "org.locallore.app.litertverify",
                        "org.locallore.app.modelverify", "org.locallore.app.modelpickerverify",
                        "org.locallore.app.modelvolumeverify", "org.locallore.app.phoneverify", "org.locallore.app.cancelack",
                        "org.locallore.app.draftverify", "org.locallore.app.draftprocessverify"),
            "Unreviewed app package")
    permission = package + ".DYNAMIC_RECEIVER_NOT_EXPORTED_PERMISSION"
    require(re.search(r"^package: name='" + re.escape(package) + r"' ", badging, re.M), "Wrong app package")
    audit_sdk(badging)
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


def audit_model_launcher(badging, tree, *, model_picker=False, model_receipt=False, physical_fixture=False):
    """The setup profile must not retain an exported scripted entry point."""
    setup = "org.locallore.app.LocalModelSetupActivity"
    play = "org.locallore.app.LiteRtPlayActivity"
    main_activity = "org.locallore.app.MainActivity"
    fixture = "org.locallore.app.ModelPickerFixtureActivity"
    interruption = "org.locallore.app.ModelPickerInterruptionFixtureActivity"
    pending = "org.locallore.app.ModelPickerPendingFixtureActivity"
    require(not (model_picker and model_receipt), "Picker and receipt setup fixtures are separate profiles")
    require(not physical_fixture or not (model_picker or model_receipt), "Physical setup fixture is a separate profile")
    receipt_activities = {"org.locallore.app." + name for name in RECEIPT_SETUP_ACTIVITIES}
    recovery = "org.locallore.app.ModelSetupRecoveryFixtureActivity"
    require(re.findall(r"^launchable-activity: name='([^']+)'", badging, re.M) == [setup],
            "Model setup must be the sole launcher")
    require(":sharedUserId(" not in tree and "E: activity-alias " not in tree,
            "Model candidate cannot share identity or alias an entry point")
    require(len(re.findall(r':name\([^)]*\)="android.intent.category.LAUNCHER"', tree)) == 1,
            "Unexpected launcher filter")
    lines = tree.splitlines()
    activities = {}
    for index, line in enumerate(lines):
        match = re.match(r"(\s*)E: activity \(", line)
        if not match:
            continue
        block = []
        for following in lines[index + 1:]:
            if following.strip() and len(following) - len(following.lstrip()) <= len(match[1]):
                break
            block.append(following)
        header = []
        for item in block:
            if re.match(r"\s*E:", item):
                break
            header.append(item)
        attributes = "\n".join(header)
        names = re.findall(r':name\([^)]*\)="([^"\n]+)"', attributes)
        require(len(names) == 1 and names[0] not in activities, "Ambiguous activity identity")
        activities[names[0]] = (attributes, "\n".join(block))
    expected = {setup, play, main_activity} | ({fixture, interruption, pending, recovery} if model_picker else set())
    if model_receipt:
        expected |= receipt_activities
    physical_activity = "org.locallore.app.PhysicalModelSetupFixtureActivity"
    if physical_fixture:
        expected.add(physical_activity)
    require({name for name in activities if name.startswith("org.locallore.app.")} ==
            expected, "Unexpected application activity")
    exports = [(setup, "true"), (play, "false"), (main_activity, "false")]
    if model_picker:
        exports.append((fixture, "false"))
        exports.append((interruption, "false"))
        exports.append((pending, "false"))
        exports.append((recovery, "false"))
    if model_receipt:
        exports.extend((name, "false") for name in sorted(receipt_activities))
    if physical_fixture:
        exports.append((physical_activity, "false"))
    for name, exported in exports:
        attributes, block = activities[name]
        require(re.findall(r':exported\([^)]*\)=([^\s]+)', attributes) == [exported],
                "Wrong model activity export boundary")
        if name in (setup, play):
            modes = re.findall(r':launchMode\([^)]*\)=([^\s]+)', attributes)
            require(len(modes) == 1 and re.fullmatch(r'(?:0x0*2|2)', modes[0]),
                    "Model activities require singleTask")
        if name != setup:
            require("E: intent-filter " not in block, "Unexpected scripted or play intent filter")
        if name in receipt_activities or name == physical_activity:
            require(not re.search(r"^\s*E:", block, re.M), "Receipt setup activity has child declarations")
            require(not re.search(r':(?:permission|process|taskAffinity|launchMode)\(', attributes),
                    "Receipt setup activity overrides its fixed process/lifecycle boundary")
    return {"launcher": setup, "scripted_exported": False, "play_exported": False}


def audit_model_picker_test_manifest(tree):
    """The selected TEST APK owns only the two reviewed model-picker fixture providers."""
    document = "org.locallore.app.ModelPickerDocumentsProvider"
    control = document + "$Control"
    authority = "org.locallore.app.modelpickerverify.test.modelpicker"
    providers = {}
    lines = tree.splitlines()
    for index, line in enumerate(lines):
        match = re.match(r"(\s*)E: provider \(", line)
        if not match:
            continue
        block = []
        for following in lines[index + 1:]:
            if following.strip() and len(following) - len(following.lstrip()) <= len(match[1]):
                break
            block.append(following)
        header = []
        for item in block:
            if re.match(r"\s*E:", item):
                break
            header.append(item)
        attributes = "\n".join(header)
        names = re.findall(r':name\([^)]*\)="([^"\n]+)"', attributes)
        require(len(names) == 1 and names[0] not in providers, "Ambiguous test provider identity")
        if names[0].startswith("org.locallore."):
            providers[names[0]] = (attributes, "\n".join(block))
    require(set(providers) == {document, control}, "Unexpected model-picker test provider set")
    for name, expected in ((document, authority), (control, authority + ".control")):
        attributes, block = providers[name]
        require(re.findall(r':authorities\([^)]*\)="([^"\n]+)"', attributes) == [expected],
                "Unexpected test provider authority")
        require(re.findall(r':process\([^)]*\)="([^"\n]+)"', attributes) == [":model_picker_provider"],
                "Test provider process changed")
        require(re.findall(r':exported\([^)]*\)=([^\s]+)', attributes) == ["true"],
                "Wrong test provider export boundary")
        permission = re.findall(r':permission\([^)]*\)="([^"\n]+)"', attributes)
        grants = re.findall(r':grantUriPermissions\([^)]*\)=([^\s]+)', attributes)
        require(":readPermission(" not in attributes and ":writePermission(" not in attributes and
                "E: path-permission " not in block, "Unexpected provider permission override")
        if name == document:
            require(permission == ["android.permission.MANAGE_DOCUMENTS"] and grants == ["true"],
                    "Document provider must retain platform grants and protection")
            require(len(re.findall(r':name\([^)]*\)="android.content.action.DOCUMENTS_PROVIDER"', block)) == 1,
                    "Missing document-provider discovery action")
        else:
            require(not permission and not grants and not re.search(r"^\s*E:", block, re.M),
                    "Control provider must not delegate document grants")
    return {"document_authority": authority, "control_authority": authority + ".control",
            "process": ":model_picker_provider"}


def audit_receipt_service(tree, *, model_volume=False):
    """Only the explicit volume debug APK may own the private same-UID proof service."""
    services = {}
    lines = tree.splitlines()
    for index, line in enumerate(lines):
        match = re.match(r"(\s*)E: service \(", line)
        if not match:
            continue
        block = []
        for following in lines[index + 1:]:
            if following.strip() and len(following) - len(following.lstrip()) <= len(match[1]):
                break
            block.append(following)
        attributes = []
        for item in block:
            if re.match(r"\s*E:", item):
                break
            attributes.append(item)
        header = "\n".join(attributes)
        names = re.findall(r':name\([^)]*\)="([^"\n]+)"', header)
        require(len(names) == 1 and names[0] not in services, "Ambiguous service identity")
        services[names[0]] = (header, "\n".join(block))
    expected = {"org.locallore.app.ReceiptProofService"} if model_volume else set()
    require(set(services) == expected, "Unexpected or missing service")
    if model_volume:
        header, block = services["org.locallore.app.ReceiptProofService"]
        require(re.findall(r':exported\([^)]*\)=([^\s]+)', header) == ["false"], "Receipt service exported")
        require(re.findall(r':process\([^)]*\)="([^"\n]+)"', header) == [":receiptproof"], "Wrong receipt process")
        require(re.findall(r':isolatedProcess\([^)]*\)=([^\s]+)', header) == ["false"], "Receipt service must retain own UID")
        require(not re.search(r"^\s*E:", block, re.M), "Receipt service must have no child declarations")
        require(not re.findall(r':permission\(', header), "Unexpected receipt permission")
    return {"receipt_service": model_volume, "exported": False}


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
    parser.add_argument("--model-provisioning", action="store_true", help="Audit the separate local model setup candidate")
    parser.add_argument("--model-picker-fixture", action="store_true", help="Audit only the explicit synthetic picker fixture profile")
    parser.add_argument("--model-volume-verification", action="store_true", help="Audit the separate candidate-owned removable storage profile")
    parser.add_argument("--model-receipt-verification", action="store_true", help="Audit only the explicit receipt setup debug profile")
    parser.add_argument("--input-draft-verification", action="store_true", help="Audit only the isolated scripted input-draft debug profile")
    parser.add_argument("--input-process-verification", action="store_true", help="Audit only the isolated scripted process-restoration debug profile")
    args = parser.parse_args(argv)
    try:
        require(not (args.input_draft_verification and args.input_process_verification), "Input verification profiles are separate")
        require(not (args.input_draft_verification or args.input_process_verification) or not any((args.litert_verification,
                args.model_provisioning, args.model_picker_fixture, args.model_volume_verification,
                args.model_receipt_verification)), "Input draft verification is a separate profile")
        require(not args.model_provisioning or args.litert_verification,
                "Model provisioning requires the explicit LiteRT audit")
        require(not args.model_picker_fixture or args.model_provisioning,
                "Model picker fixture requires the model provisioning audit")
        require(not args.model_volume_verification or args.model_provisioning,
                "Model volume verification requires the model provisioning audit")
        require(not (args.model_volume_verification and args.model_picker_fixture),
                "Model volume and picker fixtures are separate profiles")
        require(not args.model_receipt_verification or args.model_volume_verification,
                "Receipt setup verification requires the explicit volume audit")
        libraries = audit_zip(args.apk, litert=args.litert_verification, model_picker=args.model_picker_fixture,
                              model_volume=args.model_volume_verification, model_receipt=args.model_receipt_verification)
        aapt = str(aapt2_path())
        def dump(*arguments):
            return subprocess.run([aapt, "dump", *arguments], check=True, capture_output=True,
                                  text=True, encoding="utf-8", shell=False).stdout
        permissions = audit_manifest(dump("badging", str(args.apk)),
                                     dump("xmltree", str(args.apk), "--file", "AndroidManifest.xml"),
                                     "org.locallore.app.draftprocessverify" if args.input_process_verification else
                                     "org.locallore.app.draftverify" if args.input_draft_verification else
                                     "org.locallore.app.modelvolumeverify" if args.model_volume_verification else
                                     "org.locallore.app.modelpickerverify" if args.model_picker_fixture else
                                     "org.locallore.app.modelverify" if args.model_provisioning else
                                     "org.locallore.app.litertverify" if args.litert_verification else "org.locallore.app")
        if args.model_provisioning:
            audit_model_launcher(dump("badging", str(args.apk)),
                                 dump("xmltree", str(args.apk), "--file", "AndroidManifest.xml"),
                                 model_picker=args.model_picker_fixture, model_receipt=args.model_receipt_verification)
        audit_receipt_service(dump("xmltree", str(args.apk), "--file", "AndroidManifest.xml"),
                              model_volume=args.model_volume_verification)
        print(json.dumps({"status": "passed", "permissions": permissions, "libraries": libraries}, indent=2))
        return 0
    except (AuditError, OSError, zipfile.BadZipFile, subprocess.CalledProcessError, struct.error) as error:
        print(f"APK audit failed: {error}")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
