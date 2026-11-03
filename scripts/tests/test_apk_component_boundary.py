"""Original manifest-policy counterexamples; all APK/tool observations are synthetic.

No subprocess, APK, Android component, or model is executed by this cohort.
The known-component fixture is based on reviewed main/AAR declarations, and
must be reconciled against the separately captured actual merged manifest.
"""
from contextlib import redirect_stdout
import io
import json
from pathlib import Path
from types import SimpleNamespace
import unittest
from unittest.mock import patch

from scripts.tests import test_audit_apk as existing

audit = existing.audit
URI = "http://schemas.android.com/apk/res/android:"
IDS = {
    "name": "0x01010003", "permission": "0x01010006",
    "readPermission": "0x01010007", "writePermission": "0x01010008",
    "protectionLevel": "0x01010009", "enabled": "0x0101000e",
    "exported": "0x01010010", "process": "0x01010011",
    "taskAffinity": "0x01010012", "authorities": "0x01010018",
    "grantUriPermissions": "0x0101001b", "launchMode": "0x0101001d",
    "targetActivity": "0x01010202", "value": "0x01010024",
    "scheme": "0x01010027", "pathPrefix": "0x0101002b",
    "allowBackup": "0x01010280", "fullBackupContent": "0x010104eb",
    "dataExtractionRules": "0x0101063e", "sharedUserId": "0x0101000b",
    "directBootAware": "0x01010505",
    "isolatedProcess": "0x010103a9",
}
MAIN = "org.locallore.app.MainActivity"
HARNESS = "androidx.activity.ComponentActivity"
STARTUP = "androidx.startup.InitializationProvider"
RECEIVER = "androidx.profileinstaller.ProfileInstallReceiver"
SETUP = "org.locallore.app.LocalModelSetupActivity"
PLAY = "org.locallore.app.LiteRtPlayActivity"
PROFILE_ACTIONS = (
    "androidx.profileinstaller.action.INSTALL_PROFILE",
    "androidx.profileinstaller.action.SKIP_FILE",
    "androidx.profileinstaller.action.SAVE_PROFILE",
    "androidx.profileinstaller.action.BENCHMARK_OPERATION",
)


def attr(name, value, indent, *, namespace=URI, identifier=None):
    rendered = value if value in ("true", "false", "0x2") or value.startswith("@") else json.dumps(value)
    return " " * indent + "A: " + namespace + name + "(" + (identifier or IDS[name]) + ")=" + rendered + "\n"


def node(tag, values=(), children="", indent=8):
    return (" " * indent + "E: " + tag + " (line=20)\n"
            + "".join(attr(k, v, indent + 2) for k, v in values) + children)


def launcher(indent=12):
    return node("intent-filter", children=(
        node("action", (("name", "android.intent.action.MAIN"),), indent=indent + 4)
        + node("category", (("name", "android.intent.category.LAUNCHER"),), indent=indent + 4)), indent=indent)


def startup(package="org.locallore.app", extra=(), children=None):
    if children is None:
        children = "".join(node("meta-data", (("name", n), ("value", "androidx.startup")), indent=12)
                           for n in ("androidx.emoji2.text.EmojiCompatInitializer",
                                     "androidx.lifecycle.ProcessLifecycleInitializer",
                                     "androidx.profileinstaller.ProfileInstallerInitializer"))
    return node("provider", (("name", STARTUP), ("authorities", package + ".androidx-startup"),
                            ("exported", "false"), *extra), children)


def receiver(extra=(), children=None):
    if children is None:
        children = "".join(node("intent-filter", children=node("action", (("name", action),), indent=16), indent=12)
                           for action in PROFILE_ACTIONS)
    return node("receiver", (("name", RECEIVER), ("enabled", "true"), ("exported", "true"),
                             ("directBootAware", "false"), ("permission", "android.permission.DUMP"), *extra), children)


def manifest(package="org.locallore.app", *, model=False, extra="", app_extra=(), root_extra=""):
    permission = package + ".DYNAMIC_RECEIVER_NOT_EXPORTED_PERMISSION"
    root = ("N: android=http://schemas.android.com/apk/res/android (line=1)\n"
            "E: manifest (line=2)\n  A: package=" + json.dumps(package) + "\n" + root_extra
            + node("permission", (("name", permission), ("protectionLevel", "0x2")), indent=4)
            + node("uses-permission", (("name", permission),), indent=4))
    main = node("activity", (("name", MAIN), ("exported", "false" if model else "true")),
                "" if model else launcher())
    if model:
        main += node("activity", (("name", SETUP), ("exported", "true"), ("launchMode", "0x2")), launcher())
        main += node("activity", (("name", PLAY), ("exported", "false"), ("launchMode", "0x2")))
    children = main + node("activity", (("name", HARNESS), ("exported", "true"))) + startup(package) + receiver() + extra
    return root + node("application", (("allowBackup", "false"), ("fullBackupContent", "false"),
                                      ("dataExtractionRules", "@0x7f0b0000"), *app_extra), children, indent=4)


def rules():
    return "E: data-extraction-rules (line=1)\n" + "".join(
        node(group, children="".join(
            "        E: exclude (line=3)\n          A: domain=" + json.dumps(domain)
            + '\n          A: path="."\n'
            for domain in ("root", "file", "database", "sharedpref", "external")), indent=4)
        for group in ("cloud-backup", "device-transfer"))


def changed(text, before, after):
    assert text.count(before) == 1, "adversary must alter the intended one declaration"
    return text.replace(before, after, 1)


class ApkComponentBoundaryTests(unittest.TestCase):
    def cli(self, tree, *, package="org.locallore.app", model=False, crlf=False, flags=None):
        """Exercise the public audit wiring; the fake aapt never spawns a process."""
        badging = ("package: name='" + package + "' versionCode='1'\nminSdkVersion:'26'\ntargetSdkVersion:'36'\n"
                   "uses-permission: name='" + package + ".DYNAMIC_RECEIVER_NOT_EXPORTED_PERMISSION'\n"
                   "launchable-activity: name='" + (SETUP if model else MAIN) + "' label='LocalLore'\n")
        resources = ("Binary APK\nPackage name=" + package + " id=7f\n  type xml id=0b entryCount=1\n"
                     "    resource 0x7f0b0000 xml/data_extraction_rules\n"
                     "      () (file) res/xml/data_extraction_rules.xml type=XML\n")
        calls = []
        def run(argv, **kwargs):
            self.assertIs(kwargs["shell"], False)
            self.assertIs(kwargs["check"], True)
            self.assertIs(kwargs["capture_output"], True)
            self.assertEqual(kwargs["encoding"], "utf-8")
            self.assertEqual(argv[:2], [str(Path("D:/Synthetic/aapt2.exe")), "dump"])
            calls.append(tuple(argv))
            if argv[2] == "badging": value = badging
            elif argv[2] == "resources": value = resources
            elif argv[2] == "xmltree":
                selected = argv[argv.index("--file") + 1]
                self.assertIn(selected, ("AndroidManifest.xml", "res/xml/data_extraction_rules.xml"))
                value = tree if selected == "AndroidManifest.xml" else rules()
            else: raise AssertionError("Unexpected fake tool operation")
            return SimpleNamespace(stdout=value.replace("\n", "\r\n") if crlf else value)
        output = io.StringIO()
        flags = (["--litert-verification", "--model-provisioning"] if model else []) if flags is None else flags
        with patch.object(audit, "audit_zip", return_value=[]), \
                patch.object(audit, "aapt2_path", return_value=Path("D:/Synthetic/aapt2.exe")), \
                patch.object(audit.subprocess, "run", side_effect=run), redirect_stdout(output):
            code = audit.main(["unread-synthetic.apk", *flags])
        return code, output.getvalue(), calls

    def refused(self, tree, **kwargs):
        code, output, _ = self.cli(tree, **kwargs)
        self.assertEqual(code, 1)
        self.assertNotIn('"status": "passed"', output)

    def test_known_ordinary_and_model_rosters_preserve_cli_json_and_crlf(self):
        for model in (False, True):
            package = "org.locallore.app.modelverify" if model else "org.locallore.app"
            for crlf in (False, True):
                with self.subTest(model=model, crlf=crlf):
                    code, output, calls = self.cli(manifest(package, model=model), package=package, model=model, crlf=crlf)
                    self.assertEqual(code, 0)
                    self.assertEqual(set(json.loads(output)), {"status", "permissions", "libraries"})
                    self.assertEqual(json.loads(output)["status"], "passed")
                    self.assertTrue(calls)

    def test_exported_foreign_provider_receiver_activity_and_alias_are_not_an_implicit_allowlist(self):
        hostile = (
            node("provider", (("name", "foreign.vendor.Reader"), ("exported", "true"),
                              ("authorities", "org.locallore.app.foreign"), ("grantUriPermissions", "true"))),
            node("receiver", (("name", "foreign.vendor.Receiver"), ("exported", "true"))),
            node("activity", (("name", "foreign.vendor.Entry"), ("exported", "true"))),
            node("activity-alias", (("name", "foreign.vendor.Alias"), ("targetActivity", MAIN), ("exported", "true"))),
        )
        for component in hostile:
            with self.subTest(component=component): self.refused(manifest(extra=component))

    def test_private_unknown_components_and_nonexported_aliases_also_require_review(self):
        for tag in ("provider", "receiver", "activity", "activity-alias"):
            values = (("name", "org.locallore.app.Unreviewed"), ("exported", "false"))
            if tag == "provider": values += (("authorities", "org.locallore.app.unknown"),)
            if tag == "activity-alias": values += (("targetActivity", MAIN),)
            with self.subTest(tag=tag): self.refused(manifest(extra=node(tag, values)))

    def test_model_foreign_activity_cannot_hide_outside_org_locallore_prefix(self):
        package = "org.locallore.app.modelverify"
        hostile = node("activity", (("name", "foreign.vendor.SetupBridge"), ("exported", "true")),
                       node("intent-filter", children=node("action", (("name", "foreign.vendor.OPEN"),), indent=16), indent=12))
        self.refused(manifest(package, model=True, extra=hostile), package=package, model=True)

    def test_startup_provider_cannot_gain_exports_grants_or_permission_overrides(self):
        good = manifest()
        cases = [changed(good, startup(), startup().replace(attr("exported", "false", 10), attr("exported", "true", 10)))]
        for name, value in (("grantUriPermissions", "true"), ("permission", "foreign.READ"),
                            ("readPermission", "foreign.READ"), ("writePermission", "foreign.WRITE"),
                            ("process", ":foreign")):
            cases.append(changed(good, startup(), startup(extra=((name, value),))))
        for candidate in cases:
            with self.subTest(candidate=candidate): self.refused(candidate)

    def test_profile_receiver_keeps_dump_protection_and_closed_action_set(self):
        good = manifest()
        before = receiver()
        cases = [changed(good, before, before.replace(attr("permission", "android.permission.DUMP", 10), "")),
                 changed(good, before, before.replace("android.permission.DUMP", "org.locallore.app.DYNAMIC_RECEIVER_NOT_EXPORTED_PERMISSION")),
                 changed(good, before, receiver(extra=(("process", ":foreign"),))),
                 changed(good, before, before.replace(PROFILE_ACTIONS[0], "foreign.vendor.PROFILE")),
                 changed(good, before, receiver(children=node("intent-filter", children=node("action", (("name", "foreign.OPEN"),), indent=16), indent=12)))]
        for candidate in cases:
            with self.subTest(candidate=candidate): self.refused(candidate)

    def test_framework_namespace_and_resource_id_cannot_spoof_component_authority(self):
        good = manifest()
        main = node("activity", (("name", MAIN), ("exported", "true")), launcher())
        for name, value in (("name", MAIN), ("exported", "true")):
            original = attr(name, value, 10)
            for forged in (attr(name, value, 10, namespace="foreign:"),
                           attr(name, value, 10, identifier="0x0101ffff")):
                with self.subTest(name=name, forged=forged):
                    self.refused(changed(good, main, changed(main, original, forged)))

    def test_wrong_component_ownership_cannot_be_repaired_by_matching_header_text(self):
        values = (("name", "foreign.vendor.Reader"), ("exported", "true"), ("authorities", "foreign.reader"))
        # Syntactically structured AAPT trees; declaration ownership must be checked.
        self.refused(manifest() + node("provider", values, indent=4))
        self.refused(changed(manifest(), startup(), startup(children=node("provider", values, indent=12))))
        self.refused(changed(manifest(), startup(), startup(children=node("meta-data", (("name", "holder"),),
                                                                                         node("receiver", (("name", "foreign.Hidden"), ("exported", "true")), indent=16), indent=12))))

    def test_duplicate_or_relative_component_identity_does_not_shadow_reviewed_main(self):
        for selected in (MAIN, ".MainActivity", "MainActivity"):
            with self.subTest(selected=selected):
                self.refused(manifest(extra=node("activity", (("name", selected), ("exported", "false")))))

    def test_launcher_cannot_add_external_actions_data_or_duplicate_filter(self):
        good = manifest(); before = launcher()
        extras = (node("action", (("name", "foreign.vendor.OPEN"),), indent=16),
                  node("data", (("scheme", "content"),), indent=16))
        for extra in extras:
            with self.subTest(extra=extra): self.refused(changed(good, before, before + extra))
        self.refused(changed(good, before, before + before))
        self.refused(changed(good, "android.intent.action.MAIN", "android.intent.action.VIEW"))

    def test_application_and_component_identity_overrides_are_not_runtime_authority(self):
        for name, value in (("permission", "foreign.DEFAULT"), ("process", ":foreign"), ("taskAffinity", "foreign.task")):
            with self.subTest(owner="application", name=name): self.refused(manifest(app_extra=((name, value),)))
            extra = node("activity", (("name", HARNESS), ("exported", "true"), (name, value)))
            with self.subTest(owner="activity", name=name):
                self.refused(changed(manifest(), node("activity", (("name", HARNESS), ("exported", "true"))), extra))
        self.refused(manifest(root_extra=attr("sharedUserId", "foreign.shared", 2)))

    def test_unknown_nested_component_children_and_typed_export_spoofs_fail_closed(self):
        grant = node("grant-uri-permission", (("pathPrefix", "/"),), indent=12)
        path = node("path-permission", (("pathPrefix", "/"), ("readPermission", "foreign.READ")), indent=12)
        for extra in (grant, path):
            with self.subTest(extra=extra): self.refused(changed(manifest(), startup(), startup(children=extra)))
        good = manifest(); main = node("activity", (("name", MAIN), ("exported", "true")), launcher())
        original = attr("exported", "true", 10)
        for encoded in ('"true"', "@0x7f010001", "0x2"):
            with self.subTest(encoded=encoded): self.refused(changed(good, main, changed(main, original, original.replace("=true", "=" + encoded))))

    def test_all_nine_main_cli_profiles_bind_their_own_roster_and_authority(self):
        ordinary = (
            ("org.locallore.app", []),
            ("org.locallore.app.archiveverify", ["--archive-verification"]),
            ("org.locallore.app.litertverify", ["--litert-verification"]),
            ("org.locallore.app.draftverify", ["--input-draft-verification"]),
            ("org.locallore.app.draftprocessverify", ["--input-process-verification"]),
        )
        provision = ["--litert-verification", "--model-provisioning"]
        private_picker = "".join(node("activity", (("name", "org.locallore.app." + name), ("exported", "false")))
            for name in ("ModelPickerFixtureActivity", "ModelPickerInterruptionFixtureActivity",
                         "ModelPickerPendingFixtureActivity", "ModelSetupRecoveryFixtureActivity"))
        receipt_service = node("service", (("name", "org.locallore.app.ReceiptProofService"),
            ("exported", "false"), ("process", ":receiptproof"), ("isolatedProcess", "false")))
        private_receipts = "".join(node("activity", (("name", "org.locallore.app." + name), ("exported", "false")))
            for name in ("ReceiptSetupAcceptActivity", "ReceiptSetupCancelBeforeActivity", "ReceiptSetupCancelAfterActivity",
                         "ReceiptSetupDrainActivity", "ReceiptComposeCancellationActivity"))
        profiles = [(package, flags, False, "") for package, flags in ordinary] + [
            ("org.locallore.app.modelverify", provision, True, ""),
            ("org.locallore.app.modelpickerverify", provision + ["--model-picker-fixture"], True, private_picker),
            ("org.locallore.app.modelvolumeverify", provision + ["--model-volume-verification"], True, receipt_service),
            ("org.locallore.app.modelvolumeverify", provision + ["--model-volume-verification", "--model-receipt-verification"],
             True, receipt_service + private_receipts),
        ]
        self.assertEqual(len(profiles), 9)
        for package, flags, model, extra in profiles:
            with self.subTest(package=package, flags=flags):
                good = manifest(package, model=model, extra=extra)
                code, output, _ = self.cli(good, package=package, flags=flags, model=model)
                self.assertEqual(code, 0, output)
                self.assertEqual(set(json.loads(output)), {"status", "permissions", "libraries"})
                wrong_authority = changed(good, package + ".androidx-startup", "foreign.vendor.startup")
                self.refused(wrong_authority, package=package, flags=flags, model=model)
                foreign = good + node("provider", (("name", "foreign.Reader"), ("authorities", "foreign"),
                                                    ("exported", "true")), indent=4)
                self.refused(foreign, package=package, flags=flags, model=model)
                if extra:
                    self.refused(manifest(package, model=model), package=package, flags=flags, model=model)


    """Three original methods to append to ApkComponentBoundaryTests.

    The enclosing test module supplies attr/node/manifest/changed and self.refused.
    This fragment is syntax-checked, never imported or executed by its author.
    """


    def test_signature_permission_framework_namespace_and_numeric_identity_are_required(self):
        permission = "org.locallore.app.DYNAMIC_RECEIVER_NOT_EXPORTED_PERMISSION"
        declaration = node("permission", (("name", permission), ("protectionLevel", "0x2")), indent=4)
        good = manifest()
        for name, value in (("name", permission), ("protectionLevel", "0x2")):
            original = attr(name, value, 6)
            for forged in (attr(name, value, 6, namespace="foreign:"),
                           attr(name, value, 6, identifier="0x0101ffff")):
                with self.subTest(name=name, forged=forged):
                    self.refused(changed(good, declaration, changed(declaration, original, forged)))


    def test_signature_permission_is_root_owned_and_cannot_hide_nested_declarations(self):
        permission = "org.locallore.app.DYNAMIC_RECEIVER_NOT_EXPORTED_PERMISSION"
        values = (("name", permission), ("protectionLevel", "0x2"))
        declaration = node("permission", values, indent=4)
        base = changed(manifest(), declaration, "")
        # The final indent8 declaration is an application child, not manifest-owned.
        self.refused(base + node("permission", values, indent=8))
        child = node("meta-data", (("name", "unreviewed-child"),), indent=8)
        self.refused(changed(manifest(), declaration, node("permission", values, child, indent=4)))


    def test_compiled_uses_permission_must_bind_the_same_root_owned_signature_identity(self):
        permission = "org.locallore.app.DYNAMIC_RECEIVER_NOT_EXPORTED_PERMISSION"
        declaration = node("uses-permission", (("name", permission),), indent=4)
        good = manifest()
        cases = [changed(good, declaration, ""),
                 changed(good, declaration, node("uses-permission", (("name", "foreign.REQUEST"),), indent=4)),
                 changed(good, declaration, declaration + declaration)]
        for forged in (attr("name", permission, 6, namespace="foreign:"),
                       attr("name", permission, 6, identifier="0x0101ffff")):
            cases.append(changed(good, declaration, changed(declaration, attr("name", permission, 6), forged)))
        cases.append(changed(good, declaration, "") + node("uses-permission", (("name", permission),), indent=8))
        child = node("meta-data", (("name", "unreviewed-child"),), indent=8)
        cases.append(changed(good, declaration, node("uses-permission", (("name", permission),), child, indent=4)))
        for candidate in cases:
            with self.subTest(candidate=candidate): self.refused(candidate)

if __name__ == "__main__":
    unittest.main()
