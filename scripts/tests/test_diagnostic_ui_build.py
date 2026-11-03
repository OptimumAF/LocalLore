"""Original synthetic attestation oracles; no Android or external tool execution.

The internal graph preserves the recorded cohort sizes. Public front-end tests
retain the real sealed baseline and never substitute a permissive baseline loader.
"""
import copy
import hashlib
import json
from pathlib import Path, PureWindowsPath
import subprocess
import unittest
from unittest import mock
import xml.etree.ElementTree as ET

from benchmarks import diagnostic_ui_build as subject


ROOT = Path(__file__).resolve().parents[2]
SHELL = "apps/android/app/src/test/java/org/locallore/app/DiagnosticsShellConsentTest.kt"
ANDROID = "apps/android/app/src/androidTest/java/org/locallore/app/DiagnosticsIntegrationTest.kt"
DOC = "docs/diagnostics/DIAGNOSTIC_SHELL_CONSENT_VERIFICATION_2026-11-02.md"
SHELL_METHODS = (
    "retainedBinderExportCannotStartPickerOrWriteNewViewModelReview",
    "retainedBinderClearCannotEraseReplacementRecordsThroughViewModel",
    "retainedBinderDismissCannotCancelReplacementExportOrRefreshForkContext",
    "staleCloseAfterOwnerClosureCannotInvokeTheForkContextProvider",
    "equalJsonAndForeignReviewCannotAuthorizeTheCurrentViewModel",
    "currentViewModelReviewExportsFrozenBytesAndSanitizesFailureAndCancellation",
    "disposedViewModelRejectsRetainedActionsAndReturnedPickerWithoutWriting",
    "viewModelPickerTombstonePreventsOldResultFromWritingReplacementReview",
)


def encoded(value):
    return (json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False) + "\n").encode()


def digest(raw):
    return hashlib.sha256(raw).hexdigest()


def blob(raw):
    return hashlib.sha1(b"blob " + str(len(raw)).encode() + b"\0" + raw).hexdigest()


def fixture_tree(rows):
    """Fixture construction only; fixed independent vectors exercise the SUT."""
    directory = {}
    for row in rows:
        branch = directory
        parts = row["path"].split("/")
        for part in parts[:-1]:
            branch = branch.setdefault(part, {})
        if parts[-1] in branch:
            raise AssertionError("fixture duplicate")
        branch[parts[-1]] = (row["mode"], bytes.fromhex(row["git_blob"]))

    def tree(items):
        entries = []
        for name, value in items.items():
            if isinstance(value, dict):
                entries.append((name.encode() + b"/", b"40000 " + name.encode() + b"\0" + tree(value)))
            else:
                mode, identity = value
                entries.append((name.encode(), mode.encode() + b" " + name.encode() + b"\0" + identity))
        raw = b"".join(entry for _, entry in sorted(entries))
        return hashlib.sha1(b"tree " + str(len(raw)).encode() + b"\0" + raw).digest()

    return tree(directory).hex()


class MemoryReader:
    """Allowlisted immutable byte transport, not a replacement JSON validator."""
    def __init__(self, files, definitions=None):
        self.files = files
        self.class_definitions = definitions or {}
        self.reads = []
        self.final_calls = 0
        self.final_error = None
        self.read_error = None

    def read(self, pin, data=False):
        self.reads.append(copy.deepcopy(pin))
        if self.read_error is not None:
            raise self.read_error
        if not isinstance(pin, dict) or set(pin) != {"path", "bytes", "sha256"}:
            raise subject.BuildRefused("fixture_pin")
        if type(pin["bytes"]) is not int or pin["bytes"] < 0:
            raise subject.BuildRefused("fixture_pin")
        raw = self.files.get(str(pin["path"]))
        if raw is None or len(raw) != pin["bytes"] or digest(raw) != pin["sha256"]:
            raise subject.BuildRefused("fixture_bytes")
        return raw if data else digest(raw)

    def json(self, pin):
        raw = self.read(pin, data=True)
        if len(raw) > 2 * 1024 * 1024:
            raise subject.BuildRefused("fixture_json_limit")
        return subject._decode(raw)

    def definitions(self, pin):
        self.read(pin)
        return copy.deepcopy(self.class_definitions[str(pin["path"])])

    def final(self):
        self.final_calls += 1
        if self.final_error is not None:
            raise self.final_error


class Graph:
    """Full-size but tiny-byte coherent graph, with independently built Git IDs."""
    def __init__(self):
        self.base = json.loads((ROOT / "benchmarks/diagnostic_ui_build_baseline.json").read_bytes())
        self.files = {}
        self.originals = set()
        self.source = Path(self.base["roots"]["source"])
        self.capture = Path(self.base["roots"]["capture"])
        self.recovery = Path(self.base["roots"]["recovery"])
        # Use host Path joining exactly as the internal port; no real fixed path
        # is opened. Public closed-baseline tests below use the unmodified bytes.
        old_capture = PureWindowsPath(self.base["roots"]["capture"])
        old_recovery = PureWindowsPath(self.base["roots"]["recovery"])
        for key, pin in self.base["records"].items():
            root = old_recovery if key == "primary_copy" else old_capture
            prefix = self.recovery if key == "primary_copy" else self.capture
            pin["path"] = str(prefix.joinpath(*PureWindowsPath(pin["path"]).relative_to(root).parts))
        for pin in self.base["apks"].values():
            pin["path"] = str(self.capture.joinpath(*PureWindowsPath(pin["path"]).relative_to(old_capture).parts))
        self.base["product"]["base"] = "1" * 40
        self.base["product"]["head"] = "2" * 40
        contents = {SHELL: (ROOT / SHELL).read_bytes(), ANDROID: (ROOT / ANDROID).read_bytes(),
                    DOC: b"Synthetic documentation only.\n", "apps/android/gradlew": b"#!/bin/sh\n"}
        contents.update({"fixture/source-%04d.txt" % n: b"" for n in range(2577)})
        rows = []
        for relative, raw in sorted(contents.items()):
            pin = self.put(self.source / relative, raw)
            rows.append({"path": relative, "mode": "100755" if relative.endswith("/gradlew") else "100644",
                         "git_blob": blob(raw), "bytes": pin["bytes"], "sha256": pin["sha256"]})
        tested = [row for row in rows if row["path"] != DOC]
        self.base["product"]["tree"] = fixture_tree(rows)
        self.base["product"]["tested_tree"] = fixture_tree(tested)
        self.publication = {"base": self.base["product"]["base"], "commit": self.base["product"]["head"],
                            "final_tree": self.base["product"]["tree"],
                            "tested_code_tree": self.base["product"]["tested_tree"], "source": rows}
        self.record("publication", self.publication)
        flat = [{k: row[k] for k in ("path", "bytes", "sha256")} for row in tested]
        self.record("before", flat)
        self.record("after", flat)
        self.record("result", {"reason": "completed", "returncode": 0, "seconds": 12.5,
            "owned_job_cleanup_complete": True, "source_unchanged": True, "source_files": 2580,
            "generated_before_bytes": 100, "generated_after_bytes": 200, "generated_peak_sampled_bytes": 200,
            "tool_pins_unchanged": True, "jvm_task_execution_marker": True,
            "device_or_model_operation": False, "phase_kind": "original377_production_full",
            "expected_child_nonzero": False})
        command = [r"C:\Program Files\Java\jdk-21\bin\java.exe", "-classpath",
            str(self.source / "apps/android/gradle/wrapper/gradle-wrapper.jar"),
            "org.gradle.wrapper.GradleWrapperMain", ":app:assembleDebug", ":app:assembleDebugAndroidTest",
            ":app:testDebugUnitTest", ":app:lintDebug", "--offline", "--no-daemon", "--console=plain",
            "--max-workers=2", "--rerun-tasks", "-Pandroid.builder.sdkDownload=false",
            "-Pkotlin.compiler.execution.strategy=in-process"]
        environment = {"CARGO_NET_OFFLINE": "true", "RUSTUP_AUTO_INSTALL": "0", "PYTHONDONTWRITEBYTECODE": "1"}
        environment.update({key: str(self.capture / "synthetic-v1") for key in ("TEMP", "TMP", "TMPDIR")})
        options = ("-Djava.io.tmpdir=" + str(self.capture / "synthetic-v1") +
                   " -Dorg.gradle.caching=false -Dorg.gradle.configuration-cache=false" +
                   " -Dorg.gradle.java.installations.auto-download=false")
        environment["JAVA_TOOL_OPTIONS"] = options
        self.record("request", {"command": command, "cwd": str(self.source / "apps/android"), "seconds": 900,
            "source_files": 2580, "environment_overrides": environment,
            "tools": [{"path": "recorded-tool-%d" % n, "bytes": n, "sha256": "%064x" % n} for n in range(7)]})
        tasks = ("buildRustAndroid", "compileDebugKotlin", "compileDebugAndroidTestKotlin",
                 "compileDebugAndroidTestKotlin", "testDebugUnitTest",
                 "lintAnalyzeDebug", "lintReportDebug", "lintDebug", "assembleDebug", "assembleDebugAndroidTest")
        self.record("stdout", ("\n".join("> Task :app:" + t for t in tasks) +
            "\n> Task :app:generateDebugAssets UP-TO-DATE\nBUILD SUCCESSFUL in 12s\n81 actionable tasks: 81 executed\n").encode(), raw=True)
        self.record("stderr", (("Picked up JAVA_TOOL_OPTIONS: " + options + "\n") * 2).encode(), raw=True)
        self.record("lint", b'<issues><issue severity="Warning" id="ExistingWarning"/></issues>', raw=True)
        self.base["apks"]["product_apk"] = self.put(self.base["apks"]["product_apk"]["path"], b"synthetic product bytes")
        self.base["apks"]["test_apk"] = self.put(self.base["apks"]["test_apk"]["path"], b"synthetic test bytes")
        self.base["jvm_reports"] = []
        extras = 35
        for pin in json.loads((ROOT / "benchmarks/diagnostic_ui_build_baseline.json").read_bytes())["jvm_reports"]:
            name = PureWindowsPath(pin["path"]).name[len("TEST-"):-len(".xml")]
            if name == "org.locallore.app.DiagnosticsShellConsentTest":
                methods = SHELL_METHODS
            else:
                methods = ["control_%02d" % n for n in range(9 if extras else 8)]
                extras = max(0, extras - 1)
            xml = ET.Element("testsuite", name=name, tests=str(len(methods)), failures="0", errors="0", skipped="0")
            for method in methods:
                ET.SubElement(xml, "testcase", classname=name, name=method)
            path = self.capture / "final-android-v1/jvm-results-v1" / ("TEST-" + name + ".xml")
            self.base["jvm_reports"].append(self.put(path, ET.tostring(xml)))
        short = lambda pin: {key: pin[key] for key in ("bytes", "sha256")}
        self.record("main_audit", {"status": "passed", "permissions": [
            "org.locallore.app.DYNAMIC_RECEIVER_NOT_EXPORTED_PERMISSION"]})
        self.record("pair_audit", {"status": "passed", "package": "org.locallore.app",
            "test_package": "org.locallore.app.test", "test_permissions": ["android.permission.REORDER_TASKS"],
            "certificate_sha256": "3" * 64, "app": short(self.base["apks"]["product_apk"]),
            "test": short(self.base["apks"]["test_apk"])})
        audit_rows = []
        for name, script in (("main", "audit_apk.py"), ("pair", "audit_instrumentation_apk.py")):
            args = ["recorded-python", "-I", "-S", "-B", "scripts/" + script, self.base["apks"]["product_apk"]["path"]]
            if name == "pair":
                args.append(self.base["apks"]["test_apk"]["path"])
            audit_rows.append({"name": name, "command": args, "returncode": 0, "stderr_bytes": 0,
                               "stdout_sha256": self.base["records"][name + "_audit"]["sha256"]})
        self.record("audits", {"results": audit_rows, "product": short(self.base["apks"]["product_apk"]),
                              "test": short(self.base["apks"]["test_apk"]), "android_runtime_execution": False})
        descriptor = b"Lorg/locallore/app/DiagnosticsIntegrationTest;"
        methods = [(row[2].encode(), (b"V", 0), 17, True, 50 + n) for n, row in enumerate(self.base["roster"])]
        self.definitions = {self.base["apks"]["product_apk"]["path"]: {},
                            self.base["apks"]["test_apk"]["path"]: {descriptor: (1, methods)}}
        self.reseal()

    def put(self, path, raw):
        path = str(path)
        self.files[path] = raw
        self.originals.add(path)
        return {"path": path, "bytes": len(raw), "sha256": digest(raw)}

    def record(self, name, value, raw=False):
        path = self.base["records"][name]["path"]
        self.base["records"][name] = self.put(path, value if raw else encoded(value))

    def value(self, name):
        return json.loads(self.files[self.base["records"][name]["path"]])

    def change_record(self, name, change):
        value = self.value(name)
        change(value)
        self.record(name, value)
        self.reseal()

    def reseal(self):
        excluded = {self.base["records"][name]["path"] for name in ("primary", "primary_copy")}
        self.originals.difference_update(excluded)
        n = 0
        while len(self.originals) < 2725:
            self.put(self.capture / "retained-controls" / ("filler-%03d" % n), b"control")
            n += 1
        if len(self.originals) != 2725:
            raise AssertionError("fixture count")
        rows = []
        for path in sorted(self.originals):
            original = Path(path)
            try:
                target = self.recovery / "source-v1" / original.relative_to(self.source)
            except ValueError:
                target = self.recovery / "evidence-v1" / original.relative_to(self.capture)
            raw = self.files[path]
            self.files[str(target)] = raw
            rows.append({"original": path, "copy": str(target), "bytes": len(raw), "sha256": digest(raw)})
        primary = {"commit": self.base["product"]["head"], "base": self.base["product"]["base"],
            "source_files": 2581, "pairs": 2725, "all_pairs_verified": True,
            "all_originals_retained": True, "rows": rows}
        raw = encoded(primary)
        for key in ("primary", "primary_copy"):
            path = self.base["records"][key]["path"]
            self.files[path] = raw
            self.base["records"][key] = {"path": path, "bytes": len(raw), "sha256": digest(raw)}

    def change_primary(self, change):
        primary = self.value("primary")
        change(primary)
        raw = encoded(primary)
        for key in ("primary", "primary_copy"):
            path = self.base["records"][key]["path"]
            self.files[path] = raw
            self.base["records"][key] = {"path": path, "bytes": len(raw), "sha256": digest(raw)}

    def reader(self):
        return MemoryReader(self.files, self.definitions)


class DiagnosticUiBuildProtocolTest(unittest.TestCase):
    def test_complete_graph_returns_detached_metadata_and_no_authority(self):
        graph = Graph()
        reader = graph.reader()
        manifest = subject._attest(graph.base, reader)
        self.assertEqual(reader.final_calls, 1)
        self.assertEqual(manifest["counts"], {"primary_pairs": 2725, "jvm_cases": 427, "jvm_suites": 49, "selected_methods": 6})
        self.assertEqual(len(manifest["selected_methods"]), 6)
        self.assertEqual(manifest["facts"], {
            "source_tree_recomputed": True, "current_file_revalidation": True,
            "recorded_jvm_cases": 427, "recorded_jvm_suites": 49,
            "android_runtime_executed": False, "model_material": False,
            "feature_acceptance": False, "run_authority": False,
            "native_compilation_repeated": False, "remote_rechecked": False,
            "tool_binary_revalidation": False})
        expected = copy.deepcopy(manifest)
        manifest["product"]["head"] = "f" * 40
        manifest["selected_methods"][0]["method"] = "borrowed"
        self.assertEqual(subject._attest(graph.base, graph.reader()), expected)
        self.assertNotIn("execution_authorized", expected)
        self.assertNotIn("admission", expected)

    def test_schema_rejects_bool_float_counts_and_extra_profile_fields(self):
        for target, key, value in (("root", "version", True), ("counts", "jvm_cases", 427.0),
                ("counts", "selected_methods", True), ("product", "source_count", 2581.0),
                ("root", "registry", "caller-choice"), ("root", "scope", "knowledge-ui-build-v1")):
            with self.subTest(target=target, key=key, value=value):
                graph = Graph()
                destination = graph.base if target == "root" else graph.base[target]
                destination[key] = value
                with self.assertRaises(subject.BuildRefused):
                    subject._attest(graph.base, graph.reader())

    def test_raw_crlf_bytes_cannot_borrow_the_lf_git_blob_even_with_resealed_sha(self):
        graph = Graph()
        raw = graph.files[str(graph.source / SHELL)]
        self.assertIn(b"\n", raw)
        changed = raw.replace(b"\n", b"\r\n")
        self.assertNotEqual(raw, changed)
        pin = graph.put(graph.source / SHELL, changed)
        publication = graph.value("publication")
        row = next(row for row in publication["source"] if row["path"] == SHELL)
        old_blob = row["git_blob"]
        row.update(bytes=pin["bytes"], sha256=pin["sha256"])
        self.assertNotEqual(blob(changed), old_blob)
        graph.record("publication", publication)
        for key in ("before", "after"):
            before = graph.value(key)
            next(row for row in before if row["path"] == SHELL).update(bytes=pin["bytes"], sha256=pin["sha256"])
            graph.record(key, before)
        graph.reseal()
        with self.assertRaises(subject.BuildRefused):
            subject._attest(graph.base, graph.reader())

    def test_executable_mode_and_literal_source_path_are_bound_to_recorded_tree(self):
        for mutation in ("mode", "duplicate", "parent", "empty_segment", "drive"):
            with self.subTest(mutation=mutation):
                graph = Graph()
                def change(value):
                    rows = value["source"]
                    if mutation == "mode":
                        next(row for row in rows if row["path"] == "apps/android/gradlew")["mode"] = "100644"
                    elif mutation == "duplicate":
                        rows[-1] = copy.deepcopy(rows[-2])
                    else:
                        rows[-1]["path"] = {"parent": "../outside", "empty_segment": "fixture//outside", "drive": "C:/outside"}[mutation]
                graph.change_record("publication", change)
                with self.assertRaises(subject.BuildRefused):
                    subject._attest(graph.base, graph.reader())

    def test_primary_pair_receipt_cannot_alias_outside_or_claim_unknown_preservation(self):
        for mutation in ("copy_alias", "original_alias", "outside", "wrong_copy", "unknown", "bool_count"):
            with self.subTest(mutation=mutation):
                graph = Graph()
                def change(value):
                    rows = value["rows"]
                    if mutation == "copy_alias": rows[1]["copy"] = rows[0]["copy"]
                    elif mutation == "original_alias": rows[1]["original"] = rows[0]["original"]
                    elif mutation == "outside": rows[0]["original"] = "foreign/origin"
                    elif mutation == "wrong_copy": rows[0]["copy"] = str(graph.recovery / "wrong-owner")
                    elif mutation == "unknown": value["all_originals_retained"] = False
                    else: value["pairs"] = True
                graph.change_primary(change)
                with self.assertRaises(subject.BuildRefused):
                    subject._attest(graph.base, graph.reader())

    def test_every_copy_is_read_and_copy_pin_tampering_is_not_a_summary_pass(self):
        for mutation in ("missing", "changed", "primary_mirror"):
            with self.subTest(mutation=mutation):
                graph = Graph()
                primary = graph.value("primary")
                path = primary["rows"][-1]["copy"]
                if mutation == "missing": del graph.files[path]
                elif mutation == "changed": graph.files[path] += b"changed"
                else: graph.files[graph.base["records"]["primary_copy"]["path"]] += b"\n"
                with self.assertRaises(subject.BuildRefused):
                    subject._attest(graph.base, graph.reader())

    def test_only_the_declared_later_document_may_be_absent_from_tested_source(self):
        graph = Graph()
        publication = graph.value("publication")
        doc = next(row for row in publication["source"] if row["path"] == DOC)
        for key in ("before", "after"):
            value = graph.value(key)
            index = next(n for n, row in enumerate(value) if row["path"] == SHELL)
            value[index] = {k: doc[k] for k in ("path", "bytes", "sha256")}
            graph.record(key, value)
        graph.reseal()
        with self.assertRaises(subject.BuildRefused):
            subject._attest(graph.base, graph.reader())

    def test_execution_requires_known_cleanup_original_phase_and_concrete_values(self):
        mutations = {"returncode": False, "owned_job_cleanup_complete": False,
            "source_unchanged": False, "source_files": 2580.0, "tool_pins_unchanged": False,
            "device_or_model_operation": True, "phase_kind": "adapter_mutant_vm_only",
            "expected_child_nonzero": True, "seconds": 900.01, "generated_peak_sampled_bytes": 3 * 1024 ** 3 + 1}
        for key, value in mutations.items():
            with self.subTest(key=key):
                graph = Graph()
                graph.change_record("result", lambda result: result.__setitem__(key, value))
                with self.assertRaises(subject.BuildRefused):
                    subject._attest(graph.base, graph.reader())

    def test_command_request_cannot_borrow_an_offline_full_build_marker(self):
        for mutation in ("online", "foreign_task", "wrong_cwd", "wrong_temp", "time_bool", "tools_count"):
            with self.subTest(mutation=mutation):
                graph = Graph()
                def change(request):
                    if mutation == "online": request["command"].remove("--offline")
                    elif mutation == "foreign_task": request["command"][4] = ":app:installDebug"
                    elif mutation == "wrong_cwd": request["cwd"] = str(graph.capture)
                    elif mutation == "wrong_temp": request["environment_overrides"]["TMP"] = "C:/Temp"
                    elif mutation == "time_bool": request["seconds"] = True
                    else: request["tools"].pop()
                graph.change_record("request", change)
                with self.assertRaises(subject.BuildRefused):
                    subject._attest(graph.base, graph.reader())

    def test_fresh_jvm_and_critical_tasks_cannot_be_inferred_from_summary_or_old_xml(self):
        for mutation in ("uptodate", "missing", "duplicate", "summary", "stderr"):
            with self.subTest(mutation=mutation):
                graph = Graph()
                key = "stderr" if mutation == "stderr" else "stdout"
                raw = graph.files[graph.base["records"][key]["path"]]
                if mutation == "uptodate": raw = raw.replace(b":app:testDebugUnitTest\n", b":app:testDebugUnitTest UP-TO-DATE\n")
                elif mutation == "missing": raw = raw.replace(b"> Task :app:testDebugUnitTest\n", b"")
                elif mutation == "duplicate": raw += b"> Task :app:testDebugUnitTest\n"
                elif mutation == "summary": raw = raw.replace(b"81 executed", b"80 executed, 1 up-to-date")
                else: raw += b"unreviewed exception\n"
                graph.record(key, raw, raw=True)
                graph.reseal()
                with self.assertRaises(subject.BuildRefused):
                    subject._attest(graph.base, graph.reader())

    def test_xml_unique_cases_and_zero_failure_claims_require_actual_elements(self):
        for mutation in ("duplicate", "failure", "skipped", "count", "doctype", "bool_bytes"):
            with self.subTest(mutation=mutation):
                graph = Graph()
                pin = graph.base["jvm_reports"][0]
                xml = ET.fromstring(graph.files[pin["path"]])
                if mutation == "duplicate": xml[1].set("name", xml[0].get("name"))
                elif mutation in ("failure", "skipped"): ET.SubElement(xml[0], mutation)
                elif mutation == "count": xml.set("tests", "427")
                raw = ET.tostring(xml)
                if mutation == "doctype": raw = b'<!DOCTYPE testsuite [<!ENTITY leak "private">]>' + raw
                updated = graph.put(pin["path"], raw)
                graph.base["jvm_reports"][0] = updated
                graph.reseal()
                if mutation == "bool_bytes": updated["bytes"] = True
                with self.assertRaises(subject.BuildRefused):
                    subject._attest(graph.base, graph.reader())

    def test_packaging_audit_must_match_artifact_roles_and_local_permissions(self):
        for name, key, value in (("main_audit", "permissions", ["android.permission.INTERNET"]),
                ("pair_audit", "package", "foreign.package"),
                ("pair_audit", "test_permissions", ["android.permission.INTERNET"]),
                ("pair_audit", "certificate_sha256", True), ("audits", "android_runtime_execution", True)):
            with self.subTest(name=name, key=key):
                graph = Graph()
                graph.change_record(name, lambda record: record.__setitem__(key, value))
                # Reseal the referenced audit stdout digest as well: refusal must
                # reach the actual semantic field, not stop at an old digest.
                if name in ("main_audit", "pair_audit"):
                    role = name.split("_")[0]
                    graph.change_record("audits", lambda audit: next(row for row in audit["results"] if row["name"] == role).__setitem__(
                        "stdout_sha256", graph.base["records"][name]["sha256"]))
                with self.assertRaises(subject.BuildRefused):
                    subject._attest(graph.base, graph.reader())

    def test_selected_android_roster_is_source_bound_and_absent_from_product(self):
        for mutation in ("foreign", "reordered", "duplicate", "in_product"):
            with self.subTest(mutation=mutation):
                graph = Graph()
                if mutation == "foreign": graph.base["roster"][0][2] = "borrowedMethod"
                elif mutation == "reordered": graph.base["roster"][0], graph.base["roster"][1] = graph.base["roster"][1], graph.base["roster"][0]
                elif mutation == "duplicate": graph.base["roster"][1][2] = graph.base["roster"][0][2]
                else:
                    graph.definitions[graph.base["apks"]["product_apk"]["path"]] = copy.deepcopy(
                        graph.definitions[graph.base["apks"]["test_apk"]["path"]])
                with self.assertRaises(subject.BuildRefused):
                    subject._attest(graph.base, graph.reader())

    def test_compiled_selection_requires_public_concrete_instance_junit_code(self):
        # Definitions are supplied by the pure parsing port. These are eligibility
        # checks, not a claim that this synthetic map parses a real DEX file.
        positive = Graph()
        accepted = subject._attest(positive.base, positive.reader())
        self.assertEqual(len(accepted["selected_methods"]), 6)
        self.assertTrue(all(row["instruction_units"] > 0 for row in accepted["selected_methods"]))
        mutations = ("nonpublic_class", "interface_class", "abstract_class", "bool_class",
            "native", "static", "abstract", "private", "nonvoid", "parameterized",
            "no_junit", "absent", "duplicate", "zero_units", "bool_units")
        descriptor = b"Lorg/locallore/app/DiagnosticsIntegrationTest;"
        for mutation in mutations:
            with self.subTest(mutation=mutation):
                graph = Graph()
                mapping = graph.definitions[graph.base["apks"]["test_apk"]["path"]]
                class_flags, methods = mapping[descriptor]
                methods = list(methods)
                method, proto, flags, junit, units = methods[0]
                if mutation == "nonpublic_class": class_flags = 0
                elif mutation == "interface_class": class_flags = 1 | 0x200
                elif mutation == "abstract_class": class_flags = 1 | 0x400
                elif mutation == "bool_class": class_flags = True
                elif mutation == "native": flags |= 0x100
                elif mutation == "static": flags |= 8
                elif mutation == "abstract": flags |= 0x400
                elif mutation == "private": flags = 2
                elif mutation == "nonvoid": proto = (b"I", 0)
                elif mutation == "parameterized": proto = (b"V", 1)
                elif mutation == "no_junit": junit = False
                elif mutation == "zero_units": units = 0
                elif mutation == "bool_units": units = True
                if mutation == "absent":
                    methods.pop(0)
                elif mutation == "duplicate":
                    methods.append(methods[0])
                else:
                    methods[0] = (method, proto, flags, junit, units)
                mapping[descriptor] = (class_flags, methods)
                with self.assertRaises(subject.BuildRefused):
                    subject._attest(graph.base, graph.reader())

    def test_final_identity_change_and_reader_budget_refusal_never_return_metadata(self):
        graph = Graph()
        reader = graph.reader()
        reader.final_error = subject.BuildRefused("changed")
        with self.assertRaisesRegex(subject.BuildRefused, "^changed$"):
            subject._attest(graph.base, reader)
        self.assertEqual(reader.final_calls, 1)
        reader = graph.reader()
        reader.read_error = subject.BuildRefused("budget")
        with self.assertRaisesRegex(subject.BuildRefused, "^budget$"):
            subject._attest(graph.base, reader)
        self.assertEqual(reader.final_calls, 0)

    def test_public_loader_pins_raw_baseline_bytes_not_equivalent_json(self):
        raw = (ROOT / "benchmarks/diagnostic_ui_build_baseline.json").read_bytes()
        key = str(subject.BASELINE_PATH)
        reader = MemoryReader({key: raw})
        self.assertEqual(subject._load_baseline(reader), json.loads(raw))
        self.assertEqual(len(reader.reads), 1)
        normalized = encoded(json.loads(raw))
        self.assertNotEqual(raw, normalized)
        self.assertEqual(json.loads(raw), json.loads(normalized))
        with self.assertRaises(subject.BuildRefused):
            subject._load_baseline(MemoryReader({key: normalized}))

    def test_public_roles_and_fixed_paths_refuse_before_untrusted_artifact_reads(self):
        raw = (ROOT / "benchmarks/diagnostic_ui_build_baseline.json").read_bytes()
        base = json.loads(raw)
        for value in (None, [], {}, {"build": {}}, {"build": {}, "product_apk": {}, "test_apk": {}, "registry": {}}):
            with self.subTest(value=value), mock.patch.object(subject, "_Reader", side_effect=AssertionError("reader before role rejection")):
                with self.assertRaises(subject.BuildRefused):
                    subject.verify_frozen_product(value)
        artifacts = dict(copy.deepcopy(base["apks"]), build={"path": base["roots"]["manifest"], "bytes": 1, "sha256": "0" * 64})
        for mutation in ("copied_build", "moved_apk", "swapped_apks", "bool_bytes"):
            with self.subTest(mutation=mutation):
                value = copy.deepcopy(artifacts)
                if mutation == "copied_build": value["build"]["path"] += ".copy"
                elif mutation == "moved_apk": value["product_apk"]["path"] += ".copy"
                elif mutation == "swapped_apks": value["product_apk"], value["test_apk"] = value["test_apk"], value["product_apk"]
                else: value["test_apk"]["bytes"] = True
                reader = MemoryReader({str(subject.BASELINE_PATH): raw})
                with mock.patch.object(subject, "_Reader", return_value=reader), self.assertRaises(subject.BuildRefused):
                    subject.verify_frozen_product(value)
                self.assertEqual([pin["path"] for pin in reader.reads], [str(subject.BASELINE_PATH)])
        with self.assertRaises(TypeError):
            subject.create_manifest(root="caller-selected")

    def test_git_tree_uses_frozen_raw_blob_mode_and_directory_order_vectors(self):
        hello = "ce013625030ba8dba906f756967f9e9ca394464a"
        with self.assertRaises(subject.BuildRefused):
            subject._tree([])
        regular = [{"path": "hello.txt", "mode": "100644", "git_blob": hello}]
        self.assertEqual(subject._tree(regular), "aaa96ced2d9a1c8e72c56b253a0e2fe78393feb7")
        regular[0]["mode"] = "100755"
        self.assertEqual(subject._tree(regular), "98fdf9811d717ff3732a85097d50ccacd67d941d")
        collision = [
            {"path": "a/item", "mode": "100644", "git_blob": hello},
            {"path": "a.c", "mode": "100644", "git_blob": hello},
        ]
        self.assertEqual(subject._tree(collision), "d17e08325713c59525452976aa65ec2c67398819")
        self.assertEqual(subject._tree(list(reversed(collision))), subject._tree(collision))

    def test_json_duplicates_nonfinite_numbers_and_invalid_utf8_refuse(self):
        for raw in (
            b'{"version":1,"version":1}', b'{"outer":{"x":1,"x":2}}',
            b'{"x":NaN}', b'{"x":Infinity}', b'{"x":-Infinity}', b'{"x":1e999}',
            b'{"x":"\xff"}', b'{"x":1} trailing',
        ):
            with self.subTest(raw=raw), self.assertRaises(subject.BuildRefused):
                subject._decode(raw)
        self.assertEqual(subject._decode(b'{"x":[false,0,"literal"]}'), {"x": [False, 0, "literal"]})

    def test_decoder_limit_is_bytes_exact_and_does_not_accept_mutable_buffers(self):
        raw = b'"' + b'x' * (2 * 1024 * 1024 - 2) + b'"'
        self.assertEqual(len(subject._decode(raw)), 2 * 1024 * 1024 - 2)
        for invalid in (raw + b" ", bytearray(b"{}"), "{}"):
            with self.subTest(kind=type(invalid).__name__), self.assertRaises(subject.BuildRefused):
                subject._decode(invalid)

    def test_module_execution_is_quiet_before_any_reader_is_created(self):
        raw = Path(subject.__file__).read_bytes()
        namespace = {"__name__": "benchmarks._diagnostic_quiet_oracle", "__file__": subject.__file__, "__package__": "benchmarks"}
        denied = AssertionError("import performed external observation")
        with mock.patch("builtins.open", side_effect=denied), \
             mock.patch("os.open", side_effect=denied), \
             mock.patch.object(Path, "open", side_effect=denied), \
             mock.patch.object(Path, "read_bytes", side_effect=denied), \
             mock.patch.object(Path, "stat", side_effect=denied), \
             mock.patch.object(subprocess, "Popen", side_effect=denied):
            exec(compile(raw, subject.__file__, "exec"), namespace)
        self.assertTrue(callable(namespace["create_manifest"]))
        self.assertTrue(callable(namespace["verify_frozen_product"]))
