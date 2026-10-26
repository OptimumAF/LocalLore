"""Original synthetic artifact cases; no Android tool, build or device invocation.

Copyright 2026 LocalLore contributors. SPDX-License-Identifier: Apache-2.0
"""
import contextlib
import importlib.util
import io
import json
from pathlib import Path
import stat
import subprocess
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import Mock, patch
import zipfile

SPEC = importlib.util.spec_from_file_location("audit_process_controller",
    Path(__file__).resolve().parents[1] / "audit_process_controller.py")
audit = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(audit)

BADGING = """package: name='org.locallore.app.draftprocesscontroller' versionCode='1'
minSdkVersion:'26'
targetSdkVersion:'36'
application-debuggable
"""
TREE = """N: android=http://schemas.android.com/apk/res/android
E: manifest (line=2)
  A: package="org.locallore.app.draftprocesscontroller"
  E: uses-sdk (line=3)
    A: android:minSdkVersion(0x0101020c)=26
    A: android:targetSdkVersion(0x01010270)=36
  E: queries (line=4)
    E: package (line=4)
      A: android:name(0x01010003)="org.locallore.app.draftprocessverify"
  E: application (line=5)
    A: android:allowBackup(0x01010280)=false
    A: android:fullBackupContent(0x010104eb)=false
    A: android:testOnly(0x01010272)=true
    A: android:debuggable(0x0101000f)=true
  E: instrumentation (line=6)
    A: android:name(0x01010003)="org.locallore.processverify.ProcessRestoreInstrumentation"
    A: android:targetPackage(0x01010021)="org.locallore.app.draftprocesscontroller"
    A: android:functionalTest(0x01010023)=true
    A: android:handleProfiling(0x01010022)=false
"""


def entry(name, size=16):
    result = zipfile.ZipInfo(name)
    result.file_size = size
    result.compress_size = size
    return result


def entries():
    return [entry("AndroidManifest.xml"), entry("classes.dex"), entry("resources.arsc"),
            entry("META-INF/CERT.SF"), entry("META-INF/CERT.RSA"), entry("META-INF/MANIFEST.MF")]


class ProcessControllerAuditTests(unittest.TestCase):
    def check(self, badging=BADGING, tree=TREE, archive=None):
        return audit.audit(badging, tree, entries() if archive is None else archive)

    def refused(self, badging=BADGING, tree=TREE, archive=None):
        with self.assertRaises(audit.AuditError):
            self.check(badging, tree, archive)

    def test_exact_self_targeted_controller_accepts_uniform_lf_and_crlf(self):
        for newline in ("\n", "\r\n"):
            result = self.check(BADGING.replace("\n", newline), TREE.replace("\n", newline))
            self.assertEqual(result["package"], audit.PACKAGE)
            self.assertEqual(result["target"], audit.PACKAGE)
            self.assertEqual(result["instrumentation"], audit.INSTRUMENTATION)
            self.assertEqual((result["min_sdk"], result["target_sdk"]), (26, 36))
            self.assertEqual((result["permissions"], result["components"], result["zip_entries"]), ([], 0, 6))

    def test_pure_audit_performs_no_file_or_process_io(self):
        with patch.object(Path, "open", side_effect=AssertionError("unexpected file read")), \
                patch.object(subprocess, "run", side_effect=AssertionError("unexpected child")):
            self.assertEqual(self.check()["status"], "passed")

    def test_both_android_namespace_forms_and_compiled_typed_values_are_supported(self):
        tree = TREE.replace("android:", audit.ANDROID).replace("=26\n", "=(type 0x10)0x1a\n")
        tree = tree.replace("=36\n", "=0x24\n").replace("=true\n", "=(type 0x12)0xffffffff\n")
        tree = tree.replace("=false\n", "=0x00000000\n")
        self.assertEqual(self.check(tree=tree)["status"], "passed")

    def test_badging_instrumentation_if_present_must_agree_with_tree(self):
        line = f"instrumentation: name='{audit.INSTRUMENTATION}' targetPackage='{audit.PACKAGE}'\n"
        self.assertEqual(self.check(badging=BADGING + line)["status"], "passed")
        self.refused(badging=BADGING + line.replace(audit.PACKAGE, audit.PRODUCT))
        self.refused(badging=BADGING + line + line)

    def test_package_duplicates_or_product_target_are_refused(self):
        self.refused(badging=BADGING.replace(audit.PACKAGE, audit.PRODUCT))
        self.refused(badging=BADGING + BADGING.splitlines()[0] + "\n")
        self.refused(badging=BADGING.replace(" versionCode", " name='foreign.package' versionCode"))
        self.refused(tree=TREE.replace(f'package="{audit.PACKAGE}"', f'package="{audit.PRODUCT}"'))
        self.refused(tree=TREE.replace(f':targetPackage(0x01010021)="{audit.PACKAGE}"',
                                      f':targetPackage(0x01010021)="{audit.PRODUCT}"'))

    def test_sdk_and_debug_flags_are_not_coerced_or_defaulted(self):
        for key, old in (("minSdkVersion", "26"), ("targetSdkVersion", "36")):
            self.refused(badging=BADGING.replace(f"{key}:'{old}'", f"{key}:'25'"))
            self.refused(badging=BADGING + f"{key}:'{old}'\n")
        self.refused(tree=TREE.replace("=26\n", "=25\n"))
        self.refused(tree=TREE.replace("=36\n", "=35\n"))
        self.refused(tree=TREE.replace("=26\n", '="26"\n'))
        self.refused(tree=TREE.replace("=26\n", "=" + "9" * 100 + "\n"))
        self.refused(badging=BADGING.replace("application-debuggable\n", ""))
        for name in ("debuggable", "testOnly"):
            self.refused(tree=TREE.replace(f'android:{name}', f'android:missing{name}'))
            self.refused(tree=TREE.replace(f'android:{name}(0x0101000f)=true',
                                          f'android:{name}(0x0101000f)=false')
                         if name == "debuggable" else TREE.replace("testOnly(0x01010272)=true", "testOnly(0x01010272)=false"))

    def test_backup_permissions_and_shared_identity_are_refused(self):
        for name, resource in (("allowBackup", "0x01010280"), ("fullBackupContent", "0x010104eb")):
            self.refused(tree=TREE.replace(f"{name}({resource})=false", f"{name}({resource})=true"))
        for tag in ("permission", "uses-permission", "uses-permission-sdk-23"):
            self.refused(tree=TREE + f"  E: {tag} (line=9)\n    A: android:name(0x01010003)=\"android.permission.INTERNET\"\n")
        self.refused(badging=BADGING + "uses-permission: name='android.permission.INTERNET'\n")
        self.refused(tree=TREE.replace("  E: uses-sdk", '  A: android:sharedUserId(0x0101000b)="shared"\n  E: uses-sdk'))

    def test_application_components_custom_class_and_metadata_are_refused(self):
        for tag in ("activity", "activity-alias", "service", "receiver", "provider", "meta-data"):
            self.refused(tree=TREE.replace("  E: instrumentation", f"    E: {tag} (line=7)\n      A: android:name(0x01010003)=\"unexpected.Class\"\n  E: instrumentation"))
        self.refused(tree=TREE.replace("  E: instrumentation", '    A: android:name(0x01010003)="custom.Application"\n  E: instrumentation'))
        self.refused(badging=BADGING + "launchable-activity: name='unexpected.Class'\n")

    def test_queries_must_be_only_the_one_fixed_product(self):
        self.refused(tree=TREE.replace(audit.PRODUCT, "*"))
        self.refused(tree=TREE.replace("  E: application", '    E: package (line=4)\n      A: android:name(0x01010003)="other.package"\n  E: application'))
        self.refused(tree=TREE.replace("    E: package (line=4)", "    E: intent (line=4)"))
        self.refused(tree=TREE.replace("  E: queries (line=4)\n", ""))

    def test_instrumentation_is_single_fixed_and_not_profiling(self):
        self.refused(tree=TREE.replace(audit.INSTRUMENTATION, "other.Instrumentation"))
        self.refused(tree=TREE.replace("functionalTest(0x01010023)=true", "functionalTest(0x01010023)=false"))
        self.refused(tree=TREE.replace("handleProfiling(0x01010022)=false", "handleProfiling(0x01010022)=true"))
        self.refused(tree=TREE + TREE[TREE.index("  E: instrumentation"):])
        self.refused(tree=TREE + '    A: android:targetProcesses(0x01010541)="*"\n')

    def test_duplicate_attributes_spoofed_namespaces_and_malformed_trees_fail_closed(self):
        line = "    A: android:debuggable(0x0101000f)=true\n"
        self.refused(tree=TREE.replace(line, line + line))
        self.refused(tree=TREE.replace(line, line + line.replace("android:", audit.ANDROID)))
        self.refused(tree=TREE.replace("android:debuggable", "evil:debuggable"))
        self.refused(tree=TREE.replace("=false\n", '="false"\n'))
        self.refused(tree=TREE + "unparsed manifest text\n")
        self.refused(tree=TREE + "E: manifest (line=99)\n")
        self.refused(tree=TREE.replace('package="' + audit.PACKAGE + '"',
                                      'package="' + audit.PACKAGE + '" (Raw: "other.package")'))

    def test_framing_controls_mixed_newlines_and_oversized_dumps_are_refused(self):
        for separator in ("\r", "\v", "\f", "\r\r\n"):
            self.refused(tree=TREE.replace("\n", separator))
        self.refused(tree=TREE.replace("\n", "\r\n", 1))
        self.refused(badging=BADGING.replace("\n", "\r\n", 1))
        self.refused(badging=BADGING + "x" * (audit.MAX_DUMP_BYTES + 1))

    def test_native_assets_model_and_unknown_archive_payloads_are_refused(self):
        for name in ("lib/arm64-v8a/liblocallore_android.so", "assets/fixture.json", "model.litertlm",
                     "weights.bin", "res/raw/model.pb", "classes2.dex", "unknown.txt"):
            self.refused(archive=entries() + [entry(name)])
        self.refused(badging=BADGING + "native-code: 'arm64-v8a'\n")

    def test_archive_duplicate_path_aliases_links_and_missing_code_are_refused(self):
        self.refused(archive=entries() + [entry("classes.dex")])
        self.refused(archive=entries() + [entry("CLASSES.DEX")])
        for name in ("../classes.dex", "/classes.dex", "META-INF/../CERT.SF", "META-INF\\CERT.SF", "C:classes.dex"):
            self.refused(archive=entries() + [entry(name)])
        link = entry("META-INF/CERT.SF")
        link.external_attr = (stat.S_IFLNK | 0o777) << 16
        self.refused(archive=entries()[:-3] + [link])
        self.refused(archive=[item for item in entries() if item.filename != "classes.dex"])
        self.refused(archive=[item for item in entries() if item.filename != "AndroidManifest.xml"])

    def test_archive_metadata_and_decompression_bounds_are_enforced(self):
        for field, value in (("file_size", True), ("file_size", -1), ("file_size", 8 * 1024 * 1024 + 1),
                             ("compress_size", audit.MAX_APK_BYTES + 1), ("flag_bits", 1),
                             ("compress_type", zipfile.ZIP_LZMA), ("external_attr", "invalid")):
            altered = entries()
            setattr(altered[1], field, value)
            self.refused(archive=altered)
        self.refused(archive=entries() + [entry(f"META-INF/CERT{i}.SF") for i in range(audit.MAX_ENTRIES)])
        oversized = entries()
        for item in oversized:
            item.file_size = item.compress_size = 8 * 1024 * 1024
        self.refused(archive=oversized)

    def archive(self, directory):
        path = Path(directory) / "controller.apk"
        with zipfile.ZipFile(path, "w") as archive:
            archive.writestr("AndroidManifest.xml", b"synthetic manifest")
            archive.writestr("classes.dex", b"synthetic dex, not executable evidence")
        return path

    def test_cli_uses_only_offline_aapt_dumps_and_reports_hash_without_paths(self):
        with tempfile.TemporaryDirectory() as directory:
            apk = self.archive(directory)
            output = io.StringIO()
            replies = [SimpleNamespace(stdout=BADGING.encode(), stderr=b""),
                       SimpleNamespace(stdout=TREE.encode(), stderr=b"")]
            with patch.object(audit, "aapt2_path", return_value=Path(directory) / "aapt2"), \
                    patch.object(audit.subprocess, "run", side_effect=replies) as run, contextlib.redirect_stdout(output):
                self.assertEqual(audit.main([str(apk)]), 0)
            self.assertEqual(run.call_count, 2)
            self.assertEqual(run.call_args_list[0].args[0][1:], ["dump", "badging", str(apk)])
            self.assertEqual(run.call_args_list[1].args[0][1:], ["dump", "xmltree", str(apk), "--file", "AndroidManifest.xml"])
            self.assertTrue(all(call.kwargs["timeout"] == 15 and call.kwargs["shell"] is False for call in run.call_args_list))
            parsed = json.loads(output.getvalue())
            self.assertEqual(parsed["status"], "passed")
            self.assertEqual(len(parsed["apk_sha256"]), 64)
            self.assertNotIn(directory, output.getvalue())

    def test_cli_tool_failure_and_changed_artifact_never_emit_a_pass_or_private_exception(self):
        with tempfile.TemporaryDirectory() as directory:
            apk = self.archive(directory)
            output = io.StringIO()
            failure = subprocess.CalledProcessError(1, "PRIVATE_TOOL_PATH", stderr=b"PRIVATE_DIAGNOSTIC")
            with patch.object(audit, "aapt2_path", return_value=Path(directory) / "aapt2"), \
                    patch.object(audit.subprocess, "run", side_effect=failure), contextlib.redirect_stdout(output):
                self.assertEqual(audit.main([str(apk)]), 1)
            self.assertEqual(json.loads(output.getvalue())["status"], "refused")

            self.assertNotIn("PRIVATE", output.getvalue())
            def changed(argv, **kwargs):
                if "xmltree" in argv:
                    apk.write_bytes(b"changed synthetic artifact")
                    return SimpleNamespace(stdout=TREE.encode(), stderr=b"")
                return SimpleNamespace(stdout=BADGING.encode(), stderr=b"")
            output = io.StringIO()
            with patch.object(audit, "aapt2_path", return_value=Path(directory) / "aapt2"), \
                    patch.object(audit.subprocess, "run", side_effect=changed), contextlib.redirect_stdout(output):
                self.assertEqual(audit.main([str(apk)]), 1)
            self.assertEqual(json.loads(output.getvalue())["status"], "refused")

    def test_existing_sdk_selector_refusal_is_translated_without_exposing_private_error(self):
        base = SimpleNamespace(AuditError=ValueError,
            aapt2_path=Mock(side_effect=ValueError("PRIVATE_SDK_PATH")))
        spec = SimpleNamespace(loader=SimpleNamespace(exec_module=Mock()))
        with patch.object(audit.importlib.util, "spec_from_file_location", return_value=spec), \
                patch.object(audit.importlib.util, "module_from_spec", return_value=base):
            with self.assertRaises(audit.AuditError) as caught:
                audit.aapt2_path()
        self.assertEqual(str(caught.exception), "aapt_path")


if __name__ == "__main__":
    unittest.main()
