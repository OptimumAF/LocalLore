"""Host-only phone APK audit adversaries; no Android tool or native library execution.

Copyright 2026 LocalLore contributors. SPDX-License-Identifier: Apache-2.0
"""
import contextlib
import copy
import hashlib
import importlib.util
import io
import json
from pathlib import Path
import struct
import tempfile
import unittest
from unittest.mock import patch
import zipfile

SPEC = importlib.util.spec_from_file_location("physical_apk_audit", Path(__file__).resolve().parents[1] / "audit_physical_model_apk.py")
p = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(p)
from scripts.tests import test_audit_apk as legacy


def uleb(value):
    out = bytearray()
    while value >= 128:
        out.append((value & 127) | 128)
        value >>= 7
    return out + bytes([value])


def dex(definitions):
    """Original tiny DEX fixture with separate method references and definitions."""
    types = sorted(set(definitions) | {b"V", b"Lorg/junit/Test;"})
    strings = sorted(set(types) | {m[0] for _, methods in definitions.values() for m in methods})
    methods = [(owner, item) for owner, (_, members) in sorted(definitions.items()) for item in members]
    string_off = 112
    type_off = string_off + 4 * len(strings)
    proto_off = type_off + 4 * len(types)
    method_off = proto_off + 12
    class_off = method_off + 8 * len(methods)
    out = bytearray(class_off + 32 * len(definitions))
    out[:8] = b"dex\n039\0"
    struct.pack_into("<II", out, 36, 112, 0x12345678)
    for header, count, offset in ((56, len(strings), string_off), (64, len(types), type_off),
                                  (72, 1, proto_off), (88, len(methods), method_off),
                                  (96, len(definitions), class_off)):
        struct.pack_into("<II", out, header, count, offset)
    for index, text in enumerate(strings):
        struct.pack_into("<I", out, string_off + 4 * index, len(out))
        out.extend(uleb(len(text)) + text + b"\0")
    for index, name in enumerate(types):
        struct.pack_into("<I", out, type_off + 4 * index, strings.index(name))
    struct.pack_into("<III", out, proto_off, strings.index(b"V"), types.index(b"V"), 0)
    for index, (owner, method) in enumerate(methods):
        struct.pack_into("<HHI", out, method_off + 8 * index, types.index(owner), 0, strings.index(method[0]))
    for index, (owner, (flags, members)) in enumerate(sorted(definitions.items())):
        annotated = []
        indices = []
        for method in members:
            method_index = methods.index((owner, method))
            code = len(out)
            out.extend(bytes(16) + b"\x0e\0")
            indices.append((method_index, method[2], code))
            if method[3]:
                annotation = len(out)
                out.extend(b"\1" + uleb(types.index(b"Lorg/junit/Test;")) + b"\0")
                annotation_set = len(out)
                out.extend(struct.pack("<II", 1, annotation))
                annotated.append((method_index, annotation_set))
        directory = 0
        if annotated:
            directory = len(out)
            out.extend(struct.pack("<IIII", 0, 0, len(annotated), 0))
            for pair in annotated:
                out.extend(struct.pack("<II", *pair))
        body = 0
        if indices:
            body = len(out)
            out.extend(b"\0\0\0" + uleb(len(indices)))
            previous = 0
            for method_index, access, code in indices:
                out.extend(uleb(method_index - previous) + uleb(access) + uleb(code))
                previous = method_index
        struct.pack_into("<IIIIIIII", out, class_off + 32 * index,
                         types.index(owner), flags, 0xFFFFFFFF, 0, 0xFFFFFFFF, directory, body, 0)
    struct.pack_into("<I", out, 32, len(out))
    return bytes(out)


def classes():
    app = {p.descriptor(n): (17, []) for n in ("PhysicalModelPolicy", "AndroidPhysicalModelAccess")}
    test = {p.descriptor(n): (17, [(m.encode(), (b"V", 0), 17, True)]) for n, m in p.TEST_METHODS.items()}
    test[p.descriptor("NativeBoundaryTest")] = (17, [(b"baseFakeControl", (b"V", 0), 17, True)])
    return app, test


def attribute(name, value, indent=6):
    rendered = value if value in ("true", "false", "0x2") or value.startswith("@") else '"' + value + '"'
    return " " * indent + "A: android:" + name + "(1)=" + rendered + "\n"


def element(tag, attrs, children="", indent=4):
    return " " * indent + "E: " + tag + " (line=1)\n" + "".join(attribute(k, v, indent + 2) for k, v in attrs.items()) + children


def manifests():
    permission = p.APP + ".DYNAMIC_RECEIVER_NOT_EXPORTED_PERMISSION"
    badging = (f"package: name='{p.APP}' versionCode='1'\nminSdkVersion:'26'\ntargetSdkVersion:'36'\n"
               f"uses-permission: name='{permission}'\nlaunchable-activity: name='org.locallore.app.LocalModelSetupActivity'\n")
    app = "E: manifest (line=1)\n  A: package=\"" + p.APP + "\"\n" + element("permission", {"name": permission, "protectionLevel": "0x2"})
    app += "    E: application (line=1)\n" + "".join(attribute(k, v) for k, v in {
        "allowBackup": "false", "fullBackupContent": "false", "debuggable": "true", "dataExtractionRules": "@0x7f01"}.items())
    for name, exported in (("LocalModelSetupActivity", "true"), ("LiteRtPlayActivity", "false"), ("MainActivity", "false")):
        attrs = {"name": "org.locallore.app." + name, "exported": exported}
        if name != "MainActivity":
            attrs["launchMode"] = "0x2"
        children = ""
        if name == "LocalModelSetupActivity":
            children = element("intent-filter", {}, element("category", {"name": "android.intent.category.LAUNCHER"}, indent=10), indent=8)
        app += element("activity", attrs, children, indent=6)
    app += element("provider", {"name": "androidx.startup.InitializationProvider", "authorities": p.APP + ".androidx-startup", "exported": "false"}, indent=6)
    app += element("receiver", {"name": "androidx.profileinstaller.ProfileInstallReceiver", "exported": "true", "permission": "android.permission.DUMP"}, indent=6)
    test_badging = (f"package: name='{p.TEST}' versionCode='1'\nminSdkVersion:'26'\ntargetSdkVersion:'36'\n"
                    f"instrumentation: name='{p.RUNNER}' targetPackage='{p.APP}'\nuses-permission: name='android.permission.REORDER_TASKS'\n")
    test = "E: manifest (line=1)\n  A: package=\"" + p.TEST + "\"\n" + element("instrumentation", {"name": p.RUNNER, "targetPackage": p.APP})
    provider_values = (("ChooserArchiveProvider$Control", "chooser.control", ":chooser_test_provider"),
                       ("ChooserArchiveProvider", "chooser", ":chooser_test_provider"),
                       ("ArchiveDocumentProvider", "archives", ":archive_test_provider"),
                       ("TestDiagnosticProvider", "diagnostics", ":diagnostic_test_provider"))
    for name, suffix, process in provider_values:
        attrs = {"name": "org.locallore.app." + name, "authorities": p.TEST + "." + suffix, "process": process, "exported": "true"}
        if name == "ChooserArchiveProvider":
            attrs.update(permission="android.permission.MANAGE_DOCUMENTS", grantUriPermissions="true")
        test += element("provider", attrs)
    extraction = "E: data-extraction-rules (line=1)\n"
    for group in ("cloud-backup", "device-transfer"):
        children = "".join('    E: exclude (line=1)\n      A: domain="' + domain + '"\n      A: path="."\n'
                           for domain in ("root", "file", "database", "sharedpref", "external"))
        extraction += "  E: " + group + " (line=1)\n" + children
    return badging, app, test_badging, test, extraction


class PhysicalApkAuditTests(unittest.TestCase):
    def test_dex_definitions_and_annotations_accept_real_shape_not_string_references(self):
        app, test = classes()
        actual = p.Dex(dex(test)).definitions()
        self.assertEqual(actual, test)
        self.assertEqual(len(p.audit_classes(p.Dex(dex(app)).definitions(), actual)), 6)
        self.assertIn(p.descriptor("NativeBoundaryTest"), actual)

    def test_missing_definition_reference_only_and_wrong_implementation_refused(self):
        app, test = classes()
        for candidate in ({}, {p.descriptor("OtherPhysicalModelPolicy"): (17, [])}):
            with self.subTest(candidate=candidate), self.assertRaises(p.AuditError):
                p.audit_classes(candidate, test)
        raw = bytearray(dex({}) + b"PhysicalModelPolicy AndroidPhysicalModelAccess")
        struct.pack_into("<I", raw, 32, len(raw))
        with self.assertRaises(p.AuditError):
            p.audit_classes(p.Dex(raw).definitions(), test)

    def test_annotated_public_exact_method_and_concrete_class_are_required(self):
        app, test = classes()
        name = p.descriptor("PhysicalModelGiftTest")
        original = test[name][1][0]
        for flags, members in ((0x401, [original]), (17, []), (17, [(*original[:3], False)]),
                               (17, [(b"other", *original[1:])]), (17, [(original[0], (b"V", 1), 17, True)]),
                               (17, [(original[0], (b"V", 0), 9, True)]), (17, [original, original])):
            with self.subTest(flags=flags, members=members), self.assertRaises(p.AuditError):
                p.audit_classes(app, {**test, name: (flags, members)})

    def test_exact_six_physical_classes_and_app_test_separation(self):
        app, test = classes()
        for wrong in ({k: v for k, v in test.items() if k != p.descriptor("PhysicalModelGiftTest")},
                      {**test, p.descriptor("PhysicalModelExtraTest"): (17, [])}):
            with self.assertRaises(p.AuditError):
                p.audit_classes(app, wrong)
        with self.assertRaises(p.AuditError):
            p.audit_classes({**app, p.descriptor("PhysicalModelGiftTest"): test[p.descriptor("PhysicalModelGiftTest")]}, test)

    def test_each_old_heavy_family_excluded_from_both_apks(self):
        app, test = classes()
        for name in p.OLD_FAMILIES:
            for in_app in (False, True):
                with self.subTest(name=name, in_app=in_app), self.assertRaises(p.AuditError):
                    p.audit_classes({**app, **({p.descriptor(name): (17, [])} if in_app else {})},
                                    {**test, **({p.descriptor(name): (17, [])} if not in_app else {})})

    def test_optional_setup_fixture_requires_explicit_optin_and_definition(self):
        app, test = classes()
        fixture = {p.descriptor(p.SETUP_FIXTURE): (17, [])}
        with self.assertRaises(p.AuditError):
            p.audit_classes({**app, **fixture}, test)
        self.assertEqual(len(p.audit_classes({**app, **fixture}, test, physical_fixture=True)), 6)
        with self.assertRaises(p.AuditError):
            p.audit_classes(app, test, physical_fixture=True)

    def test_dex_truncation_tables_indices_and_overlong_integer_fail_closed(self):
        good = dex(classes()[1])
        variants = [good[:90], good[:-1], b"not a DEX" + bytes(120)]
        for offset, value in ((56, 1_000_001), (60, len(good) + 1), (64, 0xFFFFFFFF), (40, 0)):
            bad = bytearray(good)
            struct.pack_into("<I", bad, offset, value)
            variants.append(bad)
        for bad in variants:
            with self.subTest(size=len(bad)), self.assertRaises(p.AuditError):
                p.Dex(bad).definitions()
        reader = p.Dex(good)
        with self.assertRaises(p.AuditError):
            reader.uleb(len(good))

    def test_multidex_duplicate_class_and_duplicate_zip_entry_refused(self):
        with tempfile.TemporaryDirectory() as folder:
            target = Path(folder) / "test.apk"
            with zipfile.ZipFile(target, "w") as archive:
                for name in ("classes.dex", "classes2.dex"):
                    archive.writestr(name, dex(classes()[1]))
            with self.assertRaises(p.AuditError):
                p.dex_classes(target)

    def test_manifest_baseline_and_unqualified_backup_xml_attributes(self):
        result = p.audit_manifests(*manifests())
        self.assertEqual(result["test_methods"], 6)
        self.assertEqual(result["permissions"], [p.APP + ".DYNAMIC_RECEIVER_NOT_EXPORTED_PERMISSION"])

    def test_app_namespace_permissions_backup_and_launcher_refusals(self):
        original = manifests()
        variants = []
        for index, old, new in ((0, p.APP, "org.locallore.app.modelvolumeverify"),
                                (1, 'package="' + p.APP + '"', 'package="wrong.app"'),
                                (0, "launchable-activity:", "wrong-activity:"),
                                (1, 'allowBackup(1)=false', 'allowBackup(1)=true'),
                                (1, 'fullBackupContent(1)=false', 'fullBackupContent(1)=true'),
                                (1, 'debuggable(1)=true', 'debuggable(1)=false'),
                                (1, 'exported(1)=false', 'exported(1)=true'),
                                (4, 'domain="root"', 'domain="file"'),
                                (4, 'path="."', 'path="data"')):
            variant = list(original)
            variant[index] = variant[index].replace(old, new)
            variants.append(variant)
        bad = list(original)
        bad[0] += "uses-permission: name='android.permission.INTERNET'\n"
        variants.append(bad)
        for variant in variants:
            with self.subTest(variant=variants.index(variant)), self.assertRaises(p.AuditError):
                p.audit_manifests(*variant)

    def test_extra_exported_components_aliases_or_processes_refused(self):
        for tag in ("activity", "receiver", "service", "provider", "activity-alias"):
            value = list(manifests())
            value[1] += element(tag, {"name": "org.locallore.app.Bad", "exported": "true"})
            with self.subTest(tag=tag), self.assertRaises(p.AuditError):
                p.audit_manifests(*value)
        value = list(manifests())
        value[1] = value[1].replace('permission(1)="android.permission.DUMP"', 'permission(1)="other"')
        with self.assertRaises(p.AuditError):
            p.audit_manifests(*value)

    def test_test_target_runner_permissions_and_provider_boundaries(self):
        original = manifests()
        for index, old, new in ((2, p.APP, "org.locallore.app.modelverify"), (2, p.RUNNER, "other.Runner"),
                                (3, 'package="' + p.TEST + '"', 'package="wrong.test"'),
                                (2, "REORDER_TASKS", "INTERNET"), (3, p.RUNNER, "other.Runner"),
                                (3, p.TEST + ".archives", p.TEST + ".wrong"),
                                (3, ':archive_test_provider', ':other'),
                                (3, 'MANAGE_DOCUMENTS', 'INTERNET'),
                                (3, 'grantUriPermissions(1)=true', 'grantUriPermissions(1)=false')):
            value = list(original)
            value[index] = value[index].replace(old, new)
            with self.subTest(index=index, old=old), self.assertRaises(p.AuditError):
                p.audit_manifests(*value)

    def test_physical_fixture_launcher_remains_private_filterless_and_optin(self):
        value = list(manifests())
        fixture = element("activity", {"name": "org.locallore.app." + p.SETUP_FIXTURE, "exported": "false"}, indent=6)
        value[1] += fixture
        with self.assertRaises(p.AuditError):
            p.audit_manifests(*value)
        p.audit_manifests(*value, physical_fixture=True)
        for bad in (fixture.replace("=false", "=true"), fixture + "        E: intent-filter (line=2)\n",
                    fixture + attribute("process", ":other", indent=8)):
            bad_value = list(value)
            bad_value[1] = bad_value[1].replace(fixture, bad)
            with self.subTest(bad=bad), self.assertRaises(p.AuditError):
                p.audit_manifests(*bad_value, physical_fixture=True)

    def test_generic_physical_optin_cannot_mix_profiles_or_skip_sdk(self):
        for flags in ({}, {"model_volume": True}, {"litert": True, "model_picker": True},
                      {"litert": True, "model_volume": True}, {"litert": True, "model_volume": True, "model_receipt": True}):
            with self.subTest(flags=flags), self.assertRaises(p.AuditError):
                p.base.audit_zip("never-open.apk", physical_model=True, **flags)

    def test_generic_optional_fixture_default_refuses_leaks_and_physical_tests(self):
        for marker in (p.SETUP_FIXTURE.encode(), b"PhysicalModelGiftTest"):
            with tempfile.TemporaryDirectory() as folder:
                target = legacy.ApkAuditTests().archive(folder)
                with zipfile.ZipFile(target, "a") as archive:
                    archive.writestr("classes.dex", marker)
                with self.assertRaises(p.AuditError):
                    p.base.audit_zip(target)

    def test_generic_physical_reuses_pinned_six_library_notice_and_alignment_checks(self):
        for altered in (None, "lib/arm64-v8a/liblitertlm_jni.so", next(iter(p.base.LITERT_NOTICES))):
            with tempfile.TemporaryDirectory() as folder:
                target, hashes, notices = legacy.ApkAuditTests().candidate_archive(folder, altered=altered)
                with zipfile.ZipFile(target, "a") as archive:
                    archive.writestr("classes.dex", dex(classes()[0]))
                with patch.dict(p.base.LITERT_NATIVE_HASHES, hashes, clear=True), patch.dict(p.base.LITERT_NOTICES, notices, clear=True):
                    if altered:
                        with self.assertRaises(p.AuditError):
                            p.base.audit_zip(target, litert=True, physical_model=True)
                    else:
                        self.assertEqual(len(p.base.audit_zip(target, litert=True, physical_model=True)), 6)

    def test_tool_unknown_cleanup_timeout_nonzero_bool_or_invalid_utf8_refused(self):
        for result in (p.host.ProcessResult("completed", 1, b"safe", 0, 0, False),
                       p.host.ProcessResult("timeout", 1, b"safe", 0, 0, True),
                       p.host.ProcessResult("completed", 1, b"safe", 0, 1, True),
                       p.host.ProcessResult("completed", 1, b"safe", 0, False, True),
                       p.host.ProcessResult("completed", 1, b"\xff", 0, 0, True)):
            with patch.object(p.host, "run_process", return_value=result), self.assertRaises((p.AuditError, UnicodeError)):
                p.tool(["not-executed"])
        with patch.object(p.host, "run_process", return_value=p.host.ProcessResult("completed", 1, b"bounded", 0, 0, True)) as run:
            self.assertEqual(p.tool(["tool", "arg"]), "bounded")
            self.assertEqual(run.call_args.kwargs, {"deadline": 15, "max_output": 262144})

    def test_pair_signer_mismatch_stops_and_success_reports_hashes_without_paths(self):
        with tempfile.TemporaryDirectory() as folder:
            app, test = Path(folder) / "private app.apk", Path(folder) / "private test.apk"
            app.write_bytes(b"app")
            test.write_bytes(b"test")
            values = manifests()
            tool_outputs = [values[0], values[2], values[1], values[3], values[4]]
            with patch.object(p.base, "audit_zip", return_value=[{"entry": "fixed"}]) as archive, \
                    patch.object(p, "dex_classes", side_effect=classes()), \
                    patch.object(p.base, "aapt2_path", return_value=Path(folder) / "aapt2"), \
                    patch.object(p, "tool", side_effect=tool_outputs), \
                    patch.object(p, "certificate", side_effect=["a" * 64, "a" * 64]):
                result = p.audit_pair(app, test)
                archive.assert_called_once_with(app, litert=True, physical_model=True)
                self.assertEqual(result["app"], {"bytes": 3, "sha256": hashlib.sha256(b"app").hexdigest()})
                self.assertNotIn(folder, json.dumps(result))
            with patch.object(p.base, "audit_zip", return_value=[]), patch.object(p, "dex_classes", side_effect=classes()), \
                    patch.object(p.base, "aapt2_path", return_value=Path(folder) / "aapt2"), \
                    patch.object(p, "tool", side_effect=tool_outputs), patch.object(p, "certificate", side_effect=["a" * 64, "b" * 64]):
                with self.assertRaises(p.AuditError):
                    p.audit_pair(app, test)

    def test_cli_fixed_error_envelope_hides_private_tool_errors_and_accepts_only_paired_arguments(self):
        output = io.StringIO()
        with patch.object(p, "audit_pair", side_effect=OSError("private sentinel path")), contextlib.redirect_stdout(output):
            self.assertEqual(p.main(["--app", "app.apk", "--test", "test.apk"]), 1)
        self.assertEqual(json.loads(output.getvalue()), {"version": 1, "scope": "physical_model_apk_audit", "status": "failed", "error": "audit_failed"})
        with contextlib.redirect_stderr(io.StringIO()), self.assertRaises(SystemExit):
            p.main(["--app", "app.apk"])

    def test_signing_tool_is_existing_java_jar_one_signer_exact_digest(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            (root / "bin").mkdir()
            (root / "lib").mkdir()
            (root / "bin" / ("java.exe" if p.os.name == "nt" else "java")).write_bytes(b"not executed")
            (root / "lib" / "apksigner.jar").write_bytes(b"not executed")
            good = "Number of signers: 1\nSigner #1 certificate SHA-256 digest: " + "a" * 64 + "\n"
            with patch.dict(p.os.environ, {"JAVA_HOME": folder}), patch.object(p, "tool", return_value=good) as run:
                self.assertEqual(p.certificate(root / "app.apk", root / "aapt2"), "a" * 64)
                self.assertEqual(run.call_args.args[0][1:5], ["-jar", root / "lib" / "apksigner.jar", "verify", "--verbose"])
            for bad in (good.replace("signers: 1", "signers: 2"), good + good,
                        good.replace("a" * 64, "private path"), ""):
                with patch.dict(p.os.environ, {"JAVA_HOME": folder}), patch.object(p, "tool", return_value=bad), self.assertRaises(p.AuditError):
                    p.certificate(root / "app.apk", root / "aapt2")

    def test_pair_mutation_after_manifest_or_signing_never_publishes_pass(self):
        with tempfile.TemporaryDirectory() as folder:
            app, test = Path(folder) / "app.apk", Path(folder) / "test.apk"
            app.write_bytes(b"original app")
            test.write_bytes(b"original test")
            values = manifests()
            outputs = [values[0], values[2], values[1], values[3], values[4]]
            def changed(*_):
                app.write_bytes(b"changed app")
                return "a" * 64
            with patch.object(p.base, "audit_zip", return_value=[]), patch.object(p, "dex_classes", side_effect=classes()), \
                    patch.object(p.base, "aapt2_path", return_value=Path(folder) / "aapt2"), \
                    patch.object(p, "tool", side_effect=outputs), patch.object(p, "certificate", side_effect=changed):
                with self.assertRaises(p.AuditError):
                    p.audit_pair(app, test)

    def test_unknown_tool_ownership_prevents_all_later_manifest_and_signing_calls(self):
        with tempfile.TemporaryDirectory() as folder:
            app, test = Path(folder) / "app.apk", Path(folder) / "test.apk"
            app.write_bytes(b"app")
            test.write_bytes(b"test")
            result = p.host.ProcessResult("completed", 1, b"untrusted output", 0, 0, False)
            with patch.object(p.base, "audit_zip", return_value=[]), patch.object(p, "dex_classes", side_effect=classes()), \
                    patch.object(p.base, "aapt2_path", return_value=Path(folder) / "aapt2"), \
                    patch.object(p.host, "run_process", return_value=result) as run, patch.object(p, "certificate") as signer:
                with self.assertRaises(p.AuditError):
                    p.audit_pair(app, test)
                self.assertEqual(run.call_count, 1)
                signer.assert_not_called()


if __name__ == "__main__":
    unittest.main()
