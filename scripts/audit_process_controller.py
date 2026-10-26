"""Audit the isolated self-instrumented controller, not product behavior or DEX semantics.

Copyright 2026 LocalLore contributors. SPDX-License-Identifier: Apache-2.0
"""
import argparse
import hashlib
import importlib.util
import json
from pathlib import Path
import re
import stat
import subprocess
import zipfile

PACKAGE = "org.locallore.app.draftprocesscontroller"
PRODUCT = "org.locallore.app.draftprocessverify"
INSTRUMENTATION = "org.locallore.processverify.ProcessRestoreInstrumentation"
ANDROID = "http://schemas.android.com/apk/res/android:"
MAX_APK_BYTES = 32 * 1024 * 1024
MAX_DUMP_BYTES = 256 * 1024
MAX_ENTRIES = 256


class AuditError(ValueError):
    """A fixed controller artifact contract was not met."""


def require(condition, reason):
    if not condition:
        raise AuditError(reason)


def aapt2_path():
    """Use the existing offline Build Tools selector only when the CLI needs it."""
    spec = importlib.util.spec_from_file_location("_process_controller_base_audit",
                                                Path(__file__).with_name("audit_apk.py"))
    base = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(base)
    try:
        return base.aapt2_path()
    except base.AuditError:
        raise AuditError("aapt_path") from None


def _lines(text):
    require(type(text) is str and len(text) <= MAX_DUMP_BYTES, "dump_bounds")
    try:
        require(len(text.encode("utf-8")) <= MAX_DUMP_BYTES, "dump_bounds")
    except UnicodeError:
        raise AuditError("dump_unicode") from None
    if "\r" in text:
        remainder = text.replace("\r\n", "")
        require("\r" not in remainder and "\n" not in remainder, "dump_framing")
        text = text.replace("\r\n", "\n")
    require(all(ord(c) >= 32 or c in "\n\t" for c in text), "dump_framing")
    return text.split("\n")


def _string(raw):
    match = re.fullmatch(r'"([^"\r\n\\]*)"(?: \(Raw: "([^"\r\n\\]*)"\))?', raw)
    require(match is not None, "manifest_string")
    require(match[2] is None or match[1] == match[2], "manifest_string")
    return match[1]


def _integer(raw):
    require(len(raw) <= 32, "manifest_integer")
    match = re.fullmatch(r'(?:\(type 0x1[01]\))?(0x[0-9a-fA-F]+|[0-9]+)', raw)
    require(match is not None, "manifest_integer")
    result = int(match[1], 16 if match[1].startswith("0x") else 10)
    require(result <= 2**31 - 1, "manifest_integer")
    return result


def _boolean(raw):
    if raw in ("true", "false"):
        return raw == "true"
    match = re.fullmatch(r'(?:\(type 0x12\))?(0x0+|0xffffffff)', raw)
    require(match is not None, "manifest_boolean")
    return int(match[1], 16) != 0


def _tree(text):
    roots, stack = [], []
    for line in _lines(text):
        if not line:
            continue
        if re.fullmatch(r' *N: android=http://schemas.android.com/apk/res/android', line):
            continue
        element = re.fullmatch(r'( *)E: ([A-Za-z0-9_-]+) \(line=[0-9]+\)', line)
        if element:
            indent = len(element[1])
            while stack and stack[-1][0] >= indent:
                stack.pop()
            node = {"tag": element[2], "attrs": {}, "children": []}
            (stack[-1][1]["children"] if stack else roots).append(node)
            stack.append((indent, node))
            continue
        attribute = re.fullmatch(r'( *)A: ([^=\s(]+)(?:\(0x[0-9a-fA-F]+\))?=(.+)', line)
        require(attribute is not None and stack and len(attribute[1]) > stack[-1][0], "manifest_tree")
        name = attribute[2]
        if name.startswith(ANDROID):
            name = "android:" + name[len(ANDROID):]
        attrs = stack[-1][1]["attrs"]
        require(name not in attrs, "duplicate_attribute")
        attrs[name] = attribute[3]
    require(len(roots) == 1 and roots[0]["tag"] == "manifest", "manifest_root")
    return roots[0]


def _attrs(node, required, optional=()):
    attrs = node["attrs"]
    require(set(required) <= attrs.keys() <= set(required) | set(optional), "manifest_attributes")
    return attrs


def _badging(text):
    lines = _lines(text)
    require(all(not line or not line[0].isspace() for line in lines), "badging_framing")
    package = [line for line in lines if line.startswith("package:")]
    require(len(package) == 1 and re.match(r"package: name='" + re.escape(PACKAGE) + r"' ", package[0]),
            "badging_package")
    require(re.findall(r"\bname='([^']*)'", package[0]) == [PACKAGE], "badging_package")
    for key, expected in (("minSdkVersion", "26"), ("targetSdkVersion", "36")):
        require([line for line in lines if line.startswith(key + ":")] == [f"{key}:'{expected}'"], "badging_sdk")
    require(lines.count("application-debuggable") == 1, "badging_debug")
    require(not any(line.startswith(("uses-permission", "permission:", "launchable-", "native-code:"))
                    for line in lines), "badging_capability")
    instrumentation = [line for line in lines if line.startswith("instrumentation:")]
    require(len(instrumentation) <= 1, "badging_instrumentation")
    if instrumentation:
        line = instrumentation[0]
        require(re.findall(r"\bname='([^']*)'", line) == [INSTRUMENTATION] and
                re.findall(r"\btargetPackage='([^']*)'", line) == [PACKAGE], "badging_instrumentation")


def _archive(entries):
    require(type(entries) in (list, tuple) and 0 < len(entries) <= MAX_ENTRIES, "zip_bounds")
    seen, total, compressed, dex = set(), 0, 0, 0
    for entry in entries:
        require(type(entry) is zipfile.ZipInfo, "zip_metadata")
        name = entry.filename
        require(type(name) is str and 0 < len(name) <= 256 and name.isascii() and
                "\\" not in name and ":" not in name and "\x00" not in name and not name.startswith("/"),
                "zip_name")
        parts = name.rstrip("/").split("/")
        require(all(part not in ("", ".", "..") for part in parts), "zip_name")
        require(name.casefold() not in seen, "zip_duplicate")
        seen.add(name.casefold())
        require(type(entry.file_size) is int and type(entry.compress_size) is int and
                0 <= entry.file_size <= 8 * 1024 * 1024 and 0 <= entry.compress_size <= MAX_APK_BYTES and
                type(entry.compress_type) is int and entry.compress_type in (zipfile.ZIP_STORED, zipfile.ZIP_DEFLATED) and
                type(entry.flag_bits) is int and 0 <= entry.flag_bits <= 65535 and not entry.flag_bits & 1 and
                type(entry.external_attr) is int and 0 <= entry.external_attr <= 2**32 - 1,
                "zip_metadata")
        mode = entry.external_attr >> 16
        kind = stat.S_IFMT(mode)
        require(kind in (0, stat.S_IFREG, stat.S_IFDIR), "zip_kind")
        if name.endswith("/"):
            require(name.startswith("META-INF/") and entry.file_size == 0 and kind != stat.S_IFREG, "zip_entry")
        else:
            require(kind != stat.S_IFDIR and entry.file_size > 0, "zip_entry")
            if name == "classes.dex":
                dex += 1
            else:
                signature = re.fullmatch(r'META-INF/[A-Za-z0-9_-]+\.(?:SF|RSA|DSA|EC)', name)
                require(name in ("AndroidManifest.xml", "resources.arsc", "META-INF/MANIFEST.MF",
                                 "META-INF/com/android/build/gradle/app-metadata.properties") or signature,
                        "zip_entry")
        total += entry.file_size
        compressed += entry.compress_size
    require(dex == 1 and "androidmanifest.xml" in seen and total <= MAX_APK_BYTES and
            compressed <= MAX_APK_BYTES, "zip_bounds")
    return len(entries)


def audit(badging, xmltree, entries):
    """Pure audit of aapt2 text and ZIP metadata; does not read files or execute code."""
    _badging(badging)
    root = _tree(xmltree)
    attrs = _attrs(root, ("package",), ("android:versionCode", "android:versionName",
        "android:compileSdkVersion", "android:compileSdkVersionCodename",
        "platformBuildVersionCode", "platformBuildVersionName"))
    require(_string(attrs["package"]) == PACKAGE, "manifest_package")
    children = root["children"]
    require(sorted(child["tag"] for child in children) ==
            ["application", "instrumentation", "queries", "uses-sdk"], "manifest_elements")
    nodes = {child["tag"]: child for child in children}
    sdk = _attrs(nodes["uses-sdk"], ("android:minSdkVersion", "android:targetSdkVersion"))
    require(not nodes["uses-sdk"]["children"] and _integer(sdk["android:minSdkVersion"]) == 26 and
            _integer(sdk["android:targetSdkVersion"]) == 36, "manifest_sdk")
    application = _attrs(nodes["application"], ("android:debuggable", "android:testOnly",
        "android:allowBackup", "android:fullBackupContent"),
        ("android:label", "android:extractNativeLibs", "android:hasCode"))
    require(not nodes["application"]["children"], "application_components")
    for key, value in (("debuggable", True), ("testOnly", True), ("allowBackup", False), ("fullBackupContent", False)):
        require(_boolean(application["android:" + key]) is value, "application_flags")
    if "android:extractNativeLibs" in application:
        _boolean(application["android:extractNativeLibs"])
    if "android:hasCode" in application:
        require(_boolean(application["android:hasCode"]) is True, "application_flags")
    queries = nodes["queries"]
    require(not queries["attrs"] and len(queries["children"]) == 1, "queries")
    query = queries["children"][0]
    require(query["tag"] == "package" and not query["children"], "queries")
    require(_string(_attrs(query, ("android:name",))["android:name"]) == PRODUCT, "queries")
    instrument = nodes["instrumentation"]
    ia = _attrs(instrument, ("android:name", "android:targetPackage", "android:functionalTest",
        "android:handleProfiling"), ("android:label",))
    require(not instrument["children"] and _string(ia["android:name"]) == INSTRUMENTATION and
            _string(ia["android:targetPackage"]) == PACKAGE and
            _boolean(ia["android:functionalTest"]) is True and
            _boolean(ia["android:handleProfiling"]) is False, "instrumentation")
    count = _archive(entries)
    return {"version": 1, "scope": "locallore_process_controller_apk_audit", "status": "passed",
            "package": PACKAGE, "instrumentation": INSTRUMENTATION, "target": PACKAGE,
            "min_sdk": 26, "target_sdk": 36, "permissions": [], "components": 0, "zip_entries": count}


def _plain(path):
    for ancestor in (path, *path.parents):
        info = ancestor.lstat()
        require(not stat.S_ISLNK(info.st_mode) and not getattr(info, "st_file_attributes", 0) & 0x400,
                "apk_path")
    info = path.stat()
    require(stat.S_ISREG(info.st_mode) and 0 < info.st_size <= MAX_APK_BYTES, "apk_bounds")
    return (info.st_dev, info.st_ino, info.st_size, info.st_mtime_ns, info.st_ctime_ns)


def _digest(source):
    digest = hashlib.sha256()
    while True:
        block = source.read(65536)
        if not block:
            return digest.hexdigest()
        digest.update(block)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("apk", type=Path)
    args = parser.parse_args(argv)
    try:
        path = args.apk.absolute()
        before = _plain(path)
        with path.open("rb") as source:
            digest = _digest(source)
            source.seek(0)
            with zipfile.ZipFile(source) as archive:
                entries = archive.infolist()
        aapt = str(aapt2_path())
        def dump(*arguments):
            result = subprocess.run([aapt, "dump", *arguments], check=True, capture_output=True,
                                    timeout=15, shell=False)
            require(not result.stderr and len(result.stdout) <= MAX_DUMP_BYTES, "aapt_output")
            return result.stdout.decode("utf-8")
        result = audit(dump("badging", str(path)),
                       dump("xmltree", str(path), "--file", "AndroidManifest.xml"), entries)
        require(_plain(path) == before, "apk_changed")
        with path.open("rb") as source:
            require(_digest(source) == digest, "apk_changed")
        require(_plain(path) == before, "apk_changed")
        result["apk_sha256"] = digest
        print(json.dumps(result, sort_keys=True))
        return 0
    except (AuditError, OSError, UnicodeError, zipfile.BadZipFile, subprocess.SubprocessError):
        print(json.dumps({"version": 1, "scope": "locallore_process_controller_apk_audit",
                          "status": "refused", "reason": "controller_audit_failed"}, sort_keys=True))
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
