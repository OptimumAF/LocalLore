"""Offline paired-APK audit for the explicit internal-storage phone experiment.

Copyright 2026 LocalLore contributors. SPDX-License-Identifier: Apache-2.0
"""
import argparse
import hashlib
import json
from pathlib import Path
import re
import struct
import stat
import sys
import zipfile
import os

sys.path.insert(0, str(Path(__file__).resolve().parent))
import audit_apk as base
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from benchmarks import runtime_spike as host

APP = "org.locallore.app.phoneverify"
TEST = APP + ".test"
RUNNER = "androidx.test.runner.AndroidJUnitRunner"
TEST_METHODS = {
    "PhysicalModelPreflightTest": "verifiesPrivatePhoneSourceBeforeCopy",
    "PhysicalModelImportTest": "importsFixedPhoneCandidate",
    "PhysicalModelCancellationTest": "cancelsAndJoinsWithoutCommit",
    "PhysicalModelGiftTest": "commitsGuardedPhoneGift",
    "PhysicalModelDialogueTest": "recordsLiteralPhoneDialogue",
    "PhysicalModelReopenTest": "reopensPhoneReceiptsWithoutInference",
}
OLD_FAMILIES = ("ReceiptReal", "ReceiptOrdinary", "ReceiptCompose", "ReceiptSetup", "ReceiptVolume",
                "ReceiptAndroidFixture", "ReceiptProofService", "ModelPicker", "ModelSetupRecovery",
                "LocalModelProvisionInstrumentedTest", "LiteRtWorkerInstrumentedTest")
SETUP_FIXTURE = "PhysicalModelSetupFixtureActivity"
AuditError = base.AuditError
require = base.require


class Dex:
    """Read definitions, not string references, from bounded standard DEX files.

    Only descriptor/method names used by this audit must be ASCII. Other SDK
    strings remain opaque modified-UTF8 bytes. No code is executed or extracted.
    """
    def __init__(self, data):
        self.data = data
        require(len(data) >= 112 and data[:8] in (b"dex\n035\0", b"dex\n037\0", b"dex\n038\0", b"dex\n039\0", b"dex\n040\0"),
                "Unsupported DEX header")
        require(self.u32(32) == len(data) and self.u32(36) == 112 and self.u32(40) == 0x12345678,
                "Invalid DEX header bounds")
        self.strings = []
        for offset in self.table(56, 4):
            pointer = self.u32(offset)
            _, pointer = self.uleb(pointer)
            end = data.find(b"\0", pointer)
            require(end >= pointer, "Unterminated DEX string")
            self.strings.append(data[pointer:end])
        self.types = [self.at(self.strings, self.u32(p)) for p in self.table(64, 4)]
        self.protos = []
        for p in self.table(72, 12):
            result = self.at(self.types, self.u32(p + 4))
            parameters = self.u32(p + 8)
            count = self.u32(parameters) if parameters else 0
            if parameters:
                self.slice(parameters + 4, count * 2)
            self.protos.append((result, count))
        self.methods = []
        for p in self.table(88, 8):
            owner, proto = struct.unpack_from("<HH", self.slice(p, 4))
            self.methods.append((self.at(self.types, owner), self.at(self.strings, self.u32(p + 4)),
                                 self.at(self.protos, proto)))

    def slice(self, p, size):
        require(0 <= p <= len(self.data) and 0 <= size <= len(self.data) - p, "DEX range outside file")
        return self.data[p:p + size]

    def u32(self, p):
        return struct.unpack("<I", self.slice(p, 4))[0]

    @staticmethod
    def at(values, index):
        require(index < len(values), "Invalid DEX index")
        return values[index]

    def table(self, header, width):
        count, offset = self.u32(header), self.u32(header + 4)
        require(count <= 1_000_000 and (not count or offset >= 112), "Invalid DEX table")
        self.slice(offset, count * width)
        return range(offset, offset + count * width, width)

    def uleb(self, p):
        value = 0
        for index in range(5):
            byte = self.slice(p, 1)[0]
            p += 1
            require(index < 4 or byte <= 15, "Invalid DEX integer")
            value |= (byte & 127) << (7 * index)
            if byte < 128:
                return value, p
        raise AuditError("Invalid DEX integer")

    def test_annotations(self, offset):
        result = set()
        if not offset:
            return result
        self.slice(offset, 16)
        fields, methods, parameters = (self.u32(offset + n) for n in (4, 8, 12))
        self.slice(offset + 16, 8 * (fields + methods + parameters))
        for p in range(offset + 16 + 8 * fields, offset + 16 + 8 * (fields + methods), 8):
            method, annotation_set = self.u32(p), self.u32(p + 4)
            self.at(self.methods, method)
            count = self.u32(annotation_set)
            self.slice(annotation_set + 4, 4 * count)
            for index in range(count):
                annotation = self.u32(annotation_set + 4 + 4 * index)
                visibility = self.slice(annotation, 1)[0]
                annotation_type, _ = self.uleb(annotation + 1)
                if self.at(self.types, annotation_type) == b"Lorg/junit/Test;":
                    require(visibility == 1 and method not in result, "Invalid test annotation")
                    result.add(method)
        return result

    def definitions(self):
        result = {}
        for p in self.table(96, 32):
            name = self.at(self.types, self.u32(p))
            require(name not in result, "Duplicate DEX class definition")
            annotations = self.test_annotations(self.u32(p + 20))
            body = self.u32(p + 24)
            methods = []
            if body:
                counts = []
                for _ in range(4):
                    count, body = self.uleb(body)
                    require(count <= 1_000_000, "Excessive DEX class members")
                    counts.append(count)
                for _ in range(counts[0] + counts[1]):
                    _, body = self.uleb(body)
                    _, body = self.uleb(body)
                for count in counts[2:]:
                    method_index = 0
                    for index in range(count):
                        delta, body = self.uleb(body)
                        require(index == 0 or delta > 0, "Duplicate DEX method definition")
                        method_index += delta
                        flags, body = self.uleb(body)
                        code, body = self.uleb(body)
                        owner, method, proto = self.at(self.methods, method_index)
                        require(owner == name, "DEX method belongs to another class")
                        if code:
                            self.slice(code, 16)
                        methods.append((method, proto, flags, method_index in annotations))
            result[name] = (self.u32(p + 4), methods)
        return result


def dex_classes(path):
    result = {}
    with zipfile.ZipFile(path) as archive:
        entries = archive.infolist()
        names = [e.filename for e in entries]
        require(len(names) <= 4096 and len(names) == len(set(names)), "Invalid APK entry set")
        dex = [e for e in entries if re.fullmatch(r"classes(?:[2-9]|[1-9][0-9]+)?\.dex", e.filename)]
        require(0 < len(dex) <= 32 and sum(e.file_size for e in dex) <= 128 * 1024 * 1024, "Invalid DEX aggregate")
        for entry in dex:
            require(0 < entry.file_size <= 32 * 1024 * 1024, "Invalid DEX size")
            classes = Dex(archive.read(entry)).definitions()
            require(not result.keys() & classes.keys(), "Class defined in multiple DEX files")
            result.update(classes)
    return result


def descriptor(name):
    return ("Lorg/locallore/app/" + name + ";").encode("ascii")


def audit_classes(app_classes, test_classes, *, physical_fixture=False):
    required = {descriptor(n) for n in ("PhysicalModelPolicy", "AndroidPhysicalModelAccess")}
    require(required <= app_classes.keys(), "Missing physical implementation definitions")
    for classes in (app_classes, test_classes):
        for name in classes:
            if name.startswith(b"Lorg/locallore/app/"):
                short = name[len(b"Lorg/locallore/app/"):].split(b"$")[0].rstrip(b";")
                require(not any(short.startswith(n.encode("ascii")) for n in OLD_FAMILIES), "Old heavyweight fixture packaged")
    expected = {descriptor(n) for n in TEST_METHODS}
    require(not expected & app_classes.keys(), "Physical instrumentation in application")
    require({n for n in test_classes if re.fullmatch(rb"Lorg/locallore/app/PhysicalModel[^/$]*Test;", n)} == expected,
            "Wrong physical test class inventory")
    fixture = descriptor(SETUP_FIXTURE)
    require((fixture in app_classes) == physical_fixture and fixture not in test_classes, "Physical fixture opt-in mismatch")
    for name, method in TEST_METHODS.items():
        flags, members = test_classes[descriptor(name)]
        require(flags & 1 and not flags & (0x200 | 0x400), "Physical test class is not concrete/public")
        tests = [(m, proto, access) for m, proto, access, annotated in members if annotated]
        require(len(tests) == 1 and tests[0][:2] == (method.encode("ascii"), (b"V", 0)) and tests[0][2] in (1, 17),
                "Wrong physical public test method inventory")
    return ["org.locallore.app." + n + "#" + m for n, m in TEST_METHODS.items()]


def blocks(tree, tag):
    lines = tree.splitlines()
    result = []
    for index, line in enumerate(lines):
        match = re.fullmatch(r"(\s*)E: " + re.escape(tag) + r" \([^\n]*\)", line)
        if match:
            content = []
            for following in lines[index + 1:]:
                if following.strip() and len(following) - len(following.lstrip()) <= len(match[1]):
                    break
                content.append(following)
            header = []
            for item in content:
                if re.match(r"\s*E:", item):
                    break
                header.append(item)
            result.append(("\n".join(header), "\n".join(content)))
    return result


def attr(header, name):
    values = re.findall(r'\bA: (?:[^\s]*:)?'+re.escape(name)+r'(?:\([^)]*\))?=([^\n]+)', header)
    return [v.strip().split(" (Raw:")[0].strip('"') for v in values]


def one(header, name, expected):
    require(attr(header, name) == [expected], "Wrong manifest " + name)


def audit_manifests(app_badging, app_tree, test_badging, test_tree, extraction_tree, *, physical_fixture=False):
    for tree, package in ((app_tree, APP), (test_tree, TEST)):
        manifests = blocks(tree, "manifest")
        require(len(manifests) == 1, "Wrong manifest root count")
        one(manifests[0][0], "package", package)
    permissions = base.audit_manifest(app_badging, app_tree, APP)
    launcher = base.audit_model_launcher(app_badging, app_tree, physical_fixture=physical_fixture)
    base.audit_receipt_service(app_tree)
    require(not blocks(app_tree, "instrumentation"), "Instrumentation in app")
    require(":sharedUserId(" not in app_tree + test_tree and not blocks(test_tree, "activity-alias"), "Shared or aliased identity")
    applications = blocks(app_tree, "application")
    require(len(applications) == 1, "Wrong application count")
    app_header = applications[0][0]
    one(app_header, "allowBackup", "false")
    one(app_header, "fullBackupContent", "false")
    one(app_header, "debuggable", "true")
    require(len(attr(app_header, "dataExtractionRules")) == 1, "Missing extraction exclusions")
    for name in ("backupAgent", "process", "manageSpaceActivity", "hasFragileUserData"):
        require(not attr(app_header, name), "Unexpected application override")
    for tag in ("cloud-backup", "device-transfer"):
        groups = blocks(extraction_tree, tag)
        require(len(groups) == 1 and not blocks(groups[0][1], "include"), "Wrong backup exclusion group")
        excludes = blocks(groups[0][1], "exclude")
        require(len(excludes) == 5, "Wrong backup exclusion count")
        domains = set()
        for header, _ in excludes:
            one(header, "path", ".")
            values = attr(header, "domain")
            require(len(values) == 1, "Invalid backup domain")
            domains.add(values[0])
        require(domains == {"root", "file", "database", "sharedpref", "external"}, "Wrong backup domains")
    # AndroidX's fixed DUMP-protected profile installer is the sole baseline exported receiver.
    app_providers = blocks(app_tree, "provider")
    require(len(app_providers) <= 1, "Extra app provider")
    for header, _ in app_providers:
        one(header, "name", "androidx.startup.InitializationProvider")
        one(header, "exported", "false")
        one(header, "authorities", APP + ".androidx-startup")
    receivers = blocks(app_tree, "receiver")
    require(len(receivers) <= 1, "Extra app receiver")
    for header, _ in receivers:
        one(header, "name", "androidx.profileinstaller.ProfileInstallReceiver")
        one(header, "exported", "true")
        one(header, "permission", "android.permission.DUMP")
    for header, _ in blocks(app_tree, "activity"):
        require(attr(header, "name")[0].startswith("org.locallore.app."), "Unexpected third-party activity")
        require(not any(attr(header, n) for n in ("process", "permission", "taskAffinity")), "Activity owner override")
    require(re.findall(r"^package: name='([^']+)'", test_badging, re.M) == [TEST], "Wrong test package")
    require(re.findall(r"^minSdkVersion:'([^']+)'", test_badging, re.M) == ["26"] and
            re.findall(r"^targetSdkVersion:'([^']+)'", test_badging, re.M) == ["36"], "Wrong test SDK contract")
    require(re.findall(r"^instrumentation: name='([^']+)' targetPackage='([^']+)'", test_badging, re.M) == [(RUNNER, APP)],
            "Wrong instrumentation binding")
    uses = re.findall(r"^uses-permission[^:]*: name='([^']+)'", test_badging, re.M)
    require(len(uses) == len(set(uses)) and set(uses) <= {"android.permission.REORDER_TASKS"}, "Unexpected test permission")
    require(not blocks(test_tree, "permission") and not blocks(test_tree, "uses-permission-sdk-23"), "Unexpected test permission declaration")
    require(not blocks(test_tree, "service") and not blocks(test_tree, "receiver"),
            "Unexpected test executable component")
    test_activities = set()
    for header, _ in blocks(test_tree, "activity"):
        names = attr(header, "name")
        require(len(names) == 1 and names[0] not in test_activities and names[0] in {
            "androidx.test.core.app.InstrumentationActivityInvoker$BootstrapActivity",
            "androidx.test.core.app.InstrumentationActivityInvoker$EmptyActivity",
            "androidx.test.core.app.InstrumentationActivityInvoker$EmptyFloatingActivity"}, "Unexpected test activity")
        test_activities.add(names[0])
        require(not any(attr(header, key) for key in ("process", "permission", "taskAffinity")), "Test activity owner override")
    instrumentations = blocks(test_tree, "instrumentation")
    require(len(instrumentations) == 1, "Wrong instrumentation count")
    one(instrumentations[0][0], "name", RUNNER)
    one(instrumentations[0][0], "targetPackage", APP)
    require(not attr(instrumentations[0][0], "targetProcesses"), "Unexpected target process override")
    expected = {"ChooserArchiveProvider$Control": ("chooser.control", ":chooser_test_provider"),
                "ChooserArchiveProvider": ("chooser", ":chooser_test_provider"),
                "ArchiveDocumentProvider": ("archives", ":archive_test_provider"),
                "TestDiagnosticProvider": ("diagnostics", ":diagnostic_test_provider")}
    providers = blocks(test_tree, "provider")
    require(len(providers) == len(expected), "Wrong base test provider inventory")
    seen = set()
    for header, body in providers:
        names = attr(header, "name")
        require(len(names) == 1 and names[0].startswith("org.locallore.app."), "Wrong test provider")
        name = names[0][len("org.locallore.app."):]
        require(name in expected and name not in seen, "Unexpected/duplicate test provider")
        seen.add(name)
        authority, process = expected[name]
        one(header, "authorities", TEST + "." + authority)
        one(header, "process", process)
        one(header, "exported", "true")
        require(not attr(header, "readPermission") and not attr(header, "writePermission"), "Provider permission override")
        if name == "ChooserArchiveProvider":
            one(header, "permission", "android.permission.MANAGE_DOCUMENTS")
            one(header, "grantUriPermissions", "true")
        else:
            require(not attr(header, "permission") and not attr(header, "grantUriPermissions") and not re.search(r"^\s*E:", body, re.M),
                    "Unexpected provider grants/children")
    return {"permissions": permissions, "launcher": launcher, "test_methods": len(TEST_METHODS)}


def tool(command):
    result = host.run_process([str(p) for p in command], deadline=15, max_output=262144)
    require(result.cleanup_complete is True and result.status == "completed" and type(result.returncode) is int and result.returncode == 0,
            "Audit tool failed or cleanup unknown")
    return result.stdout.decode("utf-8", errors="strict")


def certificate(apk, aapt):
    sdk_tools = aapt.parent
    jar = sdk_tools / "lib" / "apksigner.jar"
    java_root = os.environ.get("JAVA_HOME")
    require(java_root is not None, "Set JAVA_HOME to the selected offline JDK")
    java = Path(java_root) / "bin" / ("java.exe" if os.name == "nt" else "java")
    require(jar.is_file() and java.is_file(), "Missing existing signing audit tools")
    output = tool([java, "-jar", jar, "verify", "--verbose", "--print-certs", apk])
    require(re.findall(r"^Number of signers: (\d+)\r?$", output, re.M) == ["1"], "Wrong signer count")
    digests = re.findall(r"^Signer #1 certificate SHA-256 digest: ([0-9a-fA-F]{64})\r?$", output, re.M)
    require(len(digests) == 1, "Missing signing identity")
    return digests[0].lower()


def apk_identity(path):
    def stamp(info):
        return (info.st_dev, info.st_ino, info.st_size, info.st_mtime_ns,
                getattr(info, "st_birthtime_ns", None), info.st_mode)
    before = path.lstat()
    require(stat.S_ISREG(before.st_mode) and 0 < before.st_size <= 256 * 1024 * 1024,
            "APK must be a bounded regular file")
    digest = hashlib.sha256()
    with path.open("rb") as source:
        require(stamp(os.fstat(source.fileno())) == stamp(before), "APK identity changed")
        read = 0
        for block in iter(lambda: source.read(1024 * 1024), b""):
            read += len(block)
            require(read <= before.st_size, "APK grew during hash")
            digest.update(block)
        require(read == before.st_size, "APK shortened during hash")
        require(stamp(os.fstat(source.fileno())) == stamp(before), "APK changed during hash")
    require(stamp(path.lstat()) == stamp(before), "APK path changed")
    return {"bytes": before.st_size, "sha256": digest.hexdigest()}, stamp(before)


def audit_pair(app, test, *, physical_fixture=False):
    app, test = Path(app), Path(test)
    require(app.resolve() != test.resolve() and app.is_file() and test.is_file(), "Invalid APK pair")
    app_before, test_before = apk_identity(app), apk_identity(test)
    libraries = base.audit_zip(app, litert=True, physical_model=True)
    methods = audit_classes(dex_classes(app), dex_classes(test), physical_fixture=physical_fixture)
    aapt = base.aapt2_path()
    def dump(apk, *args):
        return tool([aapt, "dump", *args, apk])
    app_badging, test_badging = dump(app, "badging"), dump(test, "badging")
    app_tree = tool([aapt, "dump", "xmltree", app, "--file", "AndroidManifest.xml"])
    test_tree = tool([aapt, "dump", "xmltree", test, "--file", "AndroidManifest.xml"])
    extraction = tool([aapt, "dump", "xmltree", app, "--file", "res/xml/data_extraction_rules.xml"])
    manifests = audit_manifests(app_badging, app_tree, test_badging, test_tree, extraction, physical_fixture=physical_fixture)
    signer = certificate(app, aapt)
    require(certificate(test, aapt) == signer, "APK signing identities differ")
    require(apk_identity(app) == app_before and apk_identity(test) == test_before, "APK pair changed during audit")
    return {"version": 1, "scope": "physical_model_apk_audit", "status": "passed", "app": app_before[0], "test": test_before[0],
            "signer_sha256": signer, "methods": methods, "manifest": manifests, "libraries": libraries}


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--app", required=True, type=Path)
    parser.add_argument("--test", required=True, type=Path)
    parser.add_argument("--physical-setup-fixture", action="store_true", help="Explicitly audit the sole optional private physical setup fixture")
    args = parser.parse_args(argv)
    try:
        print(json.dumps(audit_pair(args.app, args.test, physical_fixture=args.physical_setup_fixture), sort_keys=True))
        return 0
    except (AuditError, OSError, ValueError, zipfile.BadZipFile, struct.error):
        print(json.dumps({"version": 1, "scope": "physical_model_apk_audit", "status": "failed", "error": "audit_failed"}))
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
