"""Fixed B103 artifact attestation. File-only evidence, never Android run authority.

Copyright 2026 LocalLore contributors. SPDX-License-Identifier: Apache-2.0
"""
import copy
import hashlib
import io
import json
import math
from pathlib import Path, PurePosixPath
import re
import stat
import time
import xml.etree.ElementTree as ET

BASELINE_PATH = Path(__file__).with_name("diagnostic_ui_build_baseline.json")
BASELINE_BYTES = 20299
BASELINE_SHA256 = "044c441d51af096ea50e23ae704fc4b67ae31676b072c9c5f5d01edeba588f45"
MAX_FILE = 128 * 1024 ** 2
MAX_JSON = 2 * 1024 ** 2
MAX_TOTAL = 512 * 1024 ** 2
MAX_RESIDENT = 256 * 1024 ** 2
MAX_SECONDS = 120
ROLES = frozenset(("build", "product_apk", "test_apk"))
SHELL_CLASS = "org.locallore.app.DiagnosticsShellConsentTest"
SHELL_SOURCE = "apps/android/app/src/test/java/org/locallore/app/DiagnosticsShellConsentTest.kt"
INTEGRATION_SOURCE = "apps/android/app/src/androidTest/java/org/locallore/app/DiagnosticsIntegrationTest.kt"
CRITICAL_TASKS = ("buildRustAndroid", "compileDebugKotlin", "compileDebugAndroidTestKotlin",
                  "testDebugUnitTest", "lintAnalyzeDebug", "lintReportDebug", "lintDebug",
                  "assembleDebug", "assembleDebugAndroidTest")


class BuildRefused(ValueError):
    """Fixed refusal category; never embeds private file data or paths."""


def _need(value, reason="binding"):
    if not value:
        raise BuildRefused(reason)


def _equal(a, b):
    # JSON equality must not conflate false/0, true/1 or integers/floats.
    return type(a) is type(b) and (
        set(a) == set(b) and all(_equal(a[k], b[k]) for k in a) if type(a) is dict else
        len(a) == len(b) and all(_equal(x, y) for x, y in zip(a, b)) if type(a) is list else a == b)


def _decode(raw):
    _need(type(raw) is bytes and len(raw) <= MAX_JSON, "json")
    def pairs(items):
        result = {}
        for k, v in items:
            _need(k not in result, "json")
            result[k] = v
        return result
    def number(value):
        parsed = float(value)
        _need(math.isfinite(parsed), "json")
        return parsed
    def constant(_):
        raise BuildRefused("json")
    try:
        return json.loads(raw.decode("utf-8"), object_pairs_hook=pairs,
                          parse_float=number, parse_constant=constant)
    except (ValueError, UnicodeError, RecursionError, OverflowError):
        raise BuildRefused("json") from None


def _hex(value, length):
    return type(value) is str and re.fullmatch("[0-9a-f]{%d}" % length, value) is not None


def _pin(value):
    _need(type(value) is dict and set(value) == {"path", "bytes", "sha256"})
    _need(type(value["path"]) is str and value["path"] and type(value["bytes"]) is int
          and 0 <= value["bytes"] <= MAX_FILE and _hex(value["sha256"], 64))
    return value


def _relative(value):
    _need(type(value) is str and value and not any(c in value for c in ("\\", ":", "\0")), "source")
    parts = value.split("/")
    _need(not any(p in ("", ".", "..") for p in parts) and not PurePosixPath(value).is_absolute(), "source")
    return parts


def _object_hash(kind, raw):
    return hashlib.sha1(kind + b" " + str(len(raw)).encode("ascii") + b"\0" + raw).hexdigest()


def _tree(rows):
    """Rebuild a Git tree from raw blob IDs and recorded Git modes, without Git."""
    _need(type(rows) is list and rows, "source")
    root = {}
    for row in rows:
        _need(type(row) is dict and row.get("mode") in ("100644", "100755") and
              _hex(row.get("git_blob"), 40), "source")
        parts = _relative(row.get("path"))
        current = root
        for part in parts[:-1]:
            current = current.setdefault(part, {})
            _need(type(current) is dict, "source")
        _need(parts[-1] not in current, "source")
        current[parts[-1]] = (row["mode"], row["git_blob"])
    def digest(node):
        body = bytearray()
        try:
            ordered = sorted(node, key=lambda name: (name + ("/" if type(node[name]) is dict else "")).encode("utf-8"))
            for name in ordered:
                child = node[name]
                mode, blob = ("40000", digest(child)) if type(child) is dict else child
                body.extend(mode.encode("ascii") + b" " + name.encode("utf-8") + b"\0" + bytes.fromhex(blob))
        except (UnicodeError, RecursionError, ValueError):
            raise BuildRefused("source") from None
        return _object_hash(b"tree", body)
    return digest(root)


def _stamp(path):
    info = path.lstat()
    _need(not stat.S_ISLNK(info.st_mode) and not getattr(info, "st_file_attributes", 0) & 0x400, "path")
    return (info.st_dev, info.st_ino, info.st_mode, info.st_size, info.st_mtime_ns, info.st_nlink)


class _Reader:
    """Bounded guarded reads; tracks file and ancestor identities for one session."""
    def __init__(self):
        from benchmarks import archive_ui_build
        self.bound = archive_ui_build._bound
        self.files = {}
        self.parents = {}
        self.total = 0
        self.resident = 0
        self.started = time.monotonic()

    def _clock(self):
        _need(time.monotonic() - self.started <= MAX_SECONDS, "budget")

    def read(self, pin, data=False):
        _pin(pin)
        _need(type(data) is bool, "binding")
        self._clock()
        path = Path(pin["path"])
        # The accepted shared reader additionally checks absolute physical D:,
        # all ancestors, single links and identities while the file is open.
        if str(path) in self.files:
            old_pin, old_stamp, raw = self.files[str(path)]
            _need(_equal(old_pin, pin) and _stamp(path) == old_stamp, "changed")
            return raw if data else pin["sha256"]
        for parent in path.parents:
            current = _stamp(parent)
            _need(str(parent) not in self.parents or self.parents[str(parent)] == current, "changed")
            self.parents[str(parent)] = current
        self.total += pin["bytes"]
        self.resident += pin["bytes"]
        _need(self.total <= MAX_TOTAL and self.resident <= MAX_RESIDENT, "budget")
        raw = self.bound(pin)
        self.files[str(path)] = (dict(pin), _stamp(path), raw)
        self._clock()
        return raw if data else pin["sha256"]

    def json(self, pin):
        _need(_pin(pin)["bytes"] <= MAX_JSON, "json")
        return _decode(self.read(pin, data=True))

    def definitions(self, pin):
        raw = self.read(pin, data=True)
        from scripts.audit_physical_model_apk import dex_classes
        result = dex_classes(io.BytesIO(raw), with_code=True)
        self._clock()
        _need(_stamp(Path(pin["path"])) == self.files[str(Path(pin["path"]))][1], "changed")
        return result

    def final(self):
        self._clock()
        for path, (pin, stamp, _) in self.files.items():
            self.total += pin["bytes"]
            _need(self.total <= MAX_TOTAL, "budget")
            self.bound(pin)
            _need(_stamp(Path(path)) == stamp, "changed")
            self._clock()
        for path, stamp in self.parents.items():
            _need(_stamp(Path(path)) == stamp, "changed")
        self._clock()


def _load_baseline(reader):
    raw = reader.read({"path": str(BASELINE_PATH), "bytes": BASELINE_BYTES,
                       "sha256": BASELINE_SHA256}, data=True)
    _need(type(raw) is bytes and len(raw) == BASELINE_BYTES and
          hashlib.sha256(raw).hexdigest() == BASELINE_SHA256, "baseline")
    return _decode(raw)


def _xml(reader, pin):
    _need(_pin(pin)["bytes"] <= MAX_JSON, "report")
    raw = reader.read(pin, data=True)
    try:
        text = raw.decode("utf-8", errors="strict")
        _need("<!DOCTYPE" not in text.upper() and "<!ENTITY" not in text.upper(), "report")
        return ET.fromstring(text)
    except (ET.ParseError, ValueError, UnicodeError, RecursionError):
        raise BuildRefused("report") from None


def _methods(raw):
    # Fixed frozen Kotlin bodies are also bound by SHA256 and Git blob IDs.
    text = raw.decode("utf-8", errors="strict")
    names = re.findall(r"@Test\s+fun\s+(\w+)\s*\(", text)
    _need(names and len(set(names)) == len(names), "roster")
    return names


def _attest_impl(base, reader):
    """Private full-schema fixture seam. Production always uses the byte-pinned baseline."""
    _need(type(base) is dict and set(base) == {"version", "scope", "mode", "source_encoding", "roots",
          "product", "counts", "records", "apks", "jvm_reports", "roster", "doc_delta"}, "baseline")
    _need(type(base["version"]) is int and base["version"] == 1 and base["scope"] == "diagnostic-ui-build-v1"
          and base["mode"] == "fixed-b103-raw-git-attestation-v1", "baseline")
    _need(_equal(base["counts"], {"primary_pairs": 2725, "jvm_cases": 427, "jvm_suites": 49, "selected_methods": 6}), "baseline")
    product, records, roots = base["product"], base["records"], base["roots"]
    _need(set(product) == {"head", "base", "tree", "tested_tree", "source_count", "tested_source_count"} and
          all(_hex(product[k], 40) for k in ("head", "base", "tree", "tested_tree")) and
          type(product["source_count"]) is int and product["source_count"] == 2581 and
          type(product["tested_source_count"]) is int and product["tested_source_count"] == 2580, "source")
    _need(set(roots) == {"source", "capture", "recovery", "manifest"} and
          set(records) == {"publication", "primary", "primary_copy", "before", "after", "result", "request",
                           "stdout", "stderr", "lint", "audits", "main_audit", "pair_audit"}, "baseline")
    _need(set(base["apks"]) == {"product_apk", "test_apk"}, "baseline")
    for pin in list(records.values()) + list(base["apks"].values()) + base["jvm_reports"]:
        _pin(pin)
    publication = reader.json(records["publication"])
    primary = reader.json(records["primary"])
    _need(reader.read(records["primary"], data=True) == reader.read(records["primary_copy"], data=True), "pairs")
    _need(publication["commit"] == primary["commit"] == product["head"] and
          publication["base"] == primary["base"] == product["base"] and
          publication["final_tree"] == product["tree"] and publication["tested_code_tree"] == product["tested_tree"], "source")
    _need(primary["all_pairs_verified"] is primary["all_originals_retained"] is True and
          type(primary["pairs"]) is int and primary["pairs"] == 2725 and
          type(primary["source_files"]) is int and primary["source_files"] == 2581, "pairs")
    rows = primary["rows"]
    _need(type(rows) is list and len(rows) == 2725, "pairs")
    originals, copies = {}, set()
    for row in rows:
        _need(type(row) is dict and set(row) == {"original", "copy", "bytes", "sha256"}, "pairs")
        original, target = Path(row["original"]), Path(row["copy"])
        _need(str(original) not in originals and str(target) not in copies and original != target, "pairs")
        try:
            relative = original.relative_to(Path(roots["source"]))
            expected = Path(roots["recovery"]) / "source-v1" / relative
        except ValueError:
            try:
                relative = original.relative_to(Path(roots["capture"]))
            except ValueError:
                raise BuildRefused("pairs") from None
            expected = Path(roots["recovery"]) / "evidence-v1" / relative
        _need(target == expected and ".." not in relative.parts, "pairs")
        pin = {"path": str(original), "bytes": row["bytes"], "sha256": row["sha256"]}
        reader.read(pin)
        reader.read(dict(pin, path=str(target)))
        originals[str(original)] = pin
        copies.add(str(target))
    # Every saved input/APK/report must be covered by the preserved pair roster.
    for pin in [records[k] for k in records if k not in ("primary", "primary_copy")] + list(base["apks"].values()) + base["jvm_reports"]:
        _need(pin["path"] in originals and _equal(pin, originals[pin["path"]]), "pairs")
    sources = publication["source"]
    _need(type(sources) is list and len(sources) == 2581, "source")
    source_map, bodies = {}, {}
    for row in sources:
        _need(type(row) is dict and set(row) == {"path", "bytes", "sha256", "git_blob", "mode"}, "source")
        _relative(row["path"])
        _need(row["path"] not in source_map, "source")
        pin = {"path": str(Path(roots["source"]) / row["path"]), "bytes": row["bytes"], "sha256": row["sha256"]}
        _need(pin["path"] in originals and _equal(pin, originals[pin["path"]]), "source")
        raw = reader.read(pin, data=True)
        _need(hashlib.sha256(raw).hexdigest() == row["sha256"] and len(raw) == row["bytes"] and
              _object_hash(b"blob", raw) == row["git_blob"], "source")
        source_map[row["path"]] = row
        if row["path"] in (SHELL_SOURCE, INTEGRATION_SOURCE):
            bodies[row["path"]] = raw
    _need(_tree(sources) == product["tree"], "source")
    before, after = reader.json(records["before"]), reader.json(records["after"])
    _need(_equal(before, after) and type(before) is list and len(before) == 2580, "source")
    tested = []
    seen = set()
    for row in before:
        _need(type(row) is dict and set(row) == {"path", "bytes", "sha256"} and row["path"] not in seen, "source")
        current = source_map.get(row["path"])
        _need(current is not None and _equal(row, {k: current[k] for k in row}), "source")
        tested.append(current)
        seen.add(row["path"])
    _need(base["doc_delta"] == ["docs/diagnostics/DIAGNOSTIC_SHELL_CONSENT_VERIFICATION_2026-11-02.md"] and
          set(source_map) - seen == set(base["doc_delta"]) and _tree(tested) == product["tested_tree"], "source")
    result, request = reader.json(records["result"]), reader.json(records["request"])
    required = {"reason": "completed", "returncode": 0, "owned_job_cleanup_complete": True,
                "source_unchanged": True, "source_files": 2580, "tool_pins_unchanged": True,
                "jvm_task_execution_marker": True, "device_or_model_operation": False,
                "phase_kind": "original377_production_full", "expected_child_nonzero": False}
    _need(all(k in result and _equal(result[k], v) for k, v in required.items()), "execution")
    for k in ("generated_before_bytes", "generated_after_bytes", "generated_peak_sampled_bytes"):
        _need(type(result[k]) is int and 0 <= result[k] <= 3 * 1024 ** 3, "execution")
    _need(type(result["seconds"]) in (int, float) and math.isfinite(result["seconds"]) and 0 <= result["seconds"] <= 900, "execution")
    command = request["command"]
    expected = [r"C:\Program Files\Java\jdk-21\bin\java.exe", "-classpath",
                str(Path(roots["source"]) / "apps/android/gradle/wrapper/gradle-wrapper.jar"),
                "org.gradle.wrapper.GradleWrapperMain", ":app:assembleDebug", ":app:assembleDebugAndroidTest",
                ":app:testDebugUnitTest", ":app:lintDebug", "--offline", "--no-daemon", "--console=plain",
                "--max-workers=2", "--rerun-tasks", "-Pandroid.builder.sdkDownload=false",
                "-Pkotlin.compiler.execution.strategy=in-process"]
    _need(command == expected and request["cwd"] == str(Path(roots["source"]) / "apps/android") and
          type(request["source_files"]) is int and request["source_files"] == 2580 and
          type(request["seconds"]) is int and request["seconds"] == 900, "execution")
    _need(request["environment_overrides"]["CARGO_NET_OFFLINE"] == "true" and
          request["environment_overrides"]["RUSTUP_AUTO_INSTALL"] == "0" and
          request["environment_overrides"]["PYTHONDONTWRITEBYTECODE"] == "1", "execution")
    for key in ("TEMP", "TMP", "TMPDIR"):
        _need(request["environment_overrides"][key] == str(Path(roots["capture"]) / "synthetic-v1"), "execution")
    _need(type(request["tools"]) is list and len(request["tools"]) == 7, "execution")
    for tool in request["tools"]:
        _pin(tool)  # Recorded only: no installed tools are reopened or launched.
    stdout = reader.read(records["stdout"], data=True).decode("utf-8", errors="strict")
    stderr = reader.read(records["stderr"], data=True).decode("utf-8", errors="strict")
    expected_options = ("-Djava.io.tmpdir=" + str(Path(roots["capture"]) / "synthetic-v1") +
                        " -Dorg.gradle.caching=false -Dorg.gradle.configuration-cache=false" +
                        " -Dorg.gradle.java.installations.auto-download=false")
    _need(request["environment_overrides"]["JAVA_TOOL_OPTIONS"] == expected_options and
          stderr.splitlines() == ["Picked up JAVA_TOOL_OPTIONS: " + expected_options] * 2 and
          len(re.findall(r"^BUILD SUCCESSFUL in .+$", stdout, re.M)) == 1 and
          re.findall(r"^(\d+) actionable tasks: (\d+) executed\r?$", stdout, re.M) == [("81", "81")], "execution")
    headers = re.findall(r"^> Task :app:([A-Za-z][A-Za-z0-9]*)([^\r\n]*)\r?$", stdout, re.M)
    for task in CRITICAL_TASKS:
        # Gradle repeats this header around the recorded Kotlin warning. The
        # byte-pinned log has two identical unsuffixed headers, not two builds.
        count = 2 if task == "compileDebugAndroidTestKotlin" else 1
        _need([suffix for name, suffix in headers if name == task] == [""] * count, "execution")
    reports = base["jvm_reports"]
    _need(type(reports) is list and len(reports) == 49 and len({p["path"] for p in reports}) == 49, "report")
    cases, suites = set(), set()
    for pin in reports:
        xml = _xml(reader, pin)
        name = xml.get("name")
        _need(xml.tag == "testsuite" and name and name not in suites and
              Path(pin["path"]).name == "TEST-" + name + ".xml" and
              all(xml.get(k) == "0" for k in ("failures", "errors", "skipped")), "report")
        suites.add(name)
        entries = xml.findall("testcase")
        _need(xml.get("tests") == str(len(entries)) and entries, "report")
        for entry in entries:
            case = (entry.get("classname"), entry.get("name"))
            _need(case[0] == name and case[1] and case not in cases and not any(
                entry.findall(".//" + tag) for tag in ("failure", "error", "skipped")), "report")
            cases.add(case)
    shell = _methods(bodies[SHELL_SOURCE])
    _need(len(cases) == 427 and len(shell) == 8 and
          {method for klass, method in cases if klass == SHELL_CLASS} == set(shell), "report")
    lint = _xml(reader, records["lint"])
    _need(lint.tag == "issues" and not any(issue.get("severity") in ("Error", "Fatal") for issue in lint), "lint")
    audits = reader.json(records["audits"])
    main, pair = reader.json(records["main_audit"]), reader.json(records["pair_audit"])
    def short(pin):
        return {k: pin[k] for k in ("bytes", "sha256")}
    _need(audits["android_runtime_execution"] is False and
          _equal(audits["product"], short(base["apks"]["product_apk"])) and
          _equal(audits["test"], short(base["apks"]["test_apk"])), "audit")
    for role, script in (("main", "audit_apk.py"), ("pair", "audit_instrumentation_apk.py")):
        matches = [r for r in audits["results"] if r["name"] == role]
        _need(len(matches) == 1, "audit")
        entry = matches[0]
        expected_args = ["-I", "-S", "-B", "scripts/" + script, base["apks"]["product_apk"]["path"]]
        if role == "pair":
            expected_args.append(base["apks"]["test_apk"]["path"])
        _need(type(entry["returncode"]) is int and entry["returncode"] == 0 and
              type(entry["stderr_bytes"]) is int and entry["stderr_bytes"] == 0 and
              entry["stdout_sha256"] == records[role + "_audit"]["sha256"] and entry["command"][1:] == expected_args, "audit")
    _need(main["status"] == pair["status"] == "passed" and main["permissions"] == [
        "org.locallore.app.DYNAMIC_RECEIVER_NOT_EXPORTED_PERMISSION"] and pair["package"] == "org.locallore.app" and
        pair["test_package"] == "org.locallore.app.test" and pair["test_permissions"] == ["android.permission.REORDER_TASKS"] and
        _hex(pair["certificate_sha256"], 64) and _equal(pair["app"], short(base["apks"]["product_apk"])) and
        _equal(pair["test"], short(base["apks"]["test_apk"])), "audit")
    roster = base["roster"]
    _need(type(roster) is list and len(roster) == 6 and
          [row[0] for row in roster] == ["diagnostic_" + str(i) for i in range(1, 7)] and
          all(type(row) is list and len(row) == 3 and row[1] == "org.locallore.app.DiagnosticsIntegrationTest" for row in roster) and
          _methods(bodies[INTEGRATION_SOURCE]) == [row[2] for row in roster], "roster")
    app = reader.definitions(base["apks"]["product_apk"])
    tests = reader.definitions(base["apks"]["test_apk"])
    selected = []
    for selector, klass, method in roster:
        descriptor = ("L" + klass.replace(".", "/") + ";").encode("ascii")
        _need(descriptor not in app and descriptor in tests, "dex")
        flags, definitions = tests[descriptor]
        _need(type(flags) is int and flags & 1 and not flags & (0x200 | 0x400), "dex")
        matches = [row for row in definitions if row[0] == method.encode("ascii")]
        _need(len(matches) == 1 and len(matches[0]) == 5, "dex")
        _, proto, flags, junit, units = matches[0]
        _need(proto == (b"V", 0) and type(flags) is int and flags & 1 and not flags & (8 | 0x100 | 0x400)
              and junit is True and type(units) is int and units > 0, "dex")
        selected.append({"selector": selector, "class": klass, "method": method, "instruction_units": units})
    reader.final()
    return copy.deepcopy({"version": 1, "scope": base["scope"], "mode": base["mode"],
        "source_encoding": base["source_encoding"], "product": product,
        "counts": base["counts"], "records": records, "apks": base["apks"],
        "jvm_reports": reports, "selected_methods": selected,
        "facts": {"source_tree_recomputed": True, "current_file_revalidation": True,
                  "recorded_jvm_cases": 427, "recorded_jvm_suites": 49,
                  "android_runtime_executed": False, "model_material": False,
                  "feature_acceptance": False, "run_authority": False,
                  "native_compilation_repeated": False, "remote_rechecked": False,
                  "tool_binary_revalidation": False}})


def _attest(base, reader):
    try:
        return _attest_impl(base, reader)
    except BuildRefused:
        raise
    except (ValueError, OSError, KeyError, TypeError, IndexError, RecursionError, OverflowError, UnicodeError):
        raise BuildRefused("artifact") from None


def create_manifest():
    """Return detached deterministic metadata for the single fixed saved product."""
    return _run(None)


def verify_frozen_product(artifacts):
    """Verify exactly build/product_apk/test_apk. Grants no execution authority."""
    _need(type(artifacts) is dict and set(artifacts) == ROLES, "roles")
    return _run(artifacts)


def _run(artifacts):
    try:
        reader = _Reader()
        base = _load_baseline(reader)
        if artifacts is not None:
            _need(type(artifacts) is dict and set(artifacts) == ROLES, "roles")
            for role in ("product_apk", "test_apk"):
                _need(_equal(artifacts[role], base["apks"][role]), "roles")
            _need(_pin(artifacts["build"])["path"] == base["roots"]["manifest"], "roles")
            saved = reader.json(artifacts["build"])
        manifest = _attest(base, reader)
        if artifacts is not None:
            _need(_equal(saved, manifest), "manifest")
        return manifest
    except BuildRefused:
        raise
    except (ValueError, OSError, KeyError, TypeError, IndexError, RecursionError, OverflowError, UnicodeError):
        raise BuildRefused("artifact") from None


def main(argv=None):
    import sys
    args = sys.argv[1:] if argv is None else argv
    if args not in (["create"], ["verify"]):
        print("usage: python -m benchmarks.diagnostic_ui_build create|verify", file=sys.stderr)
        return 2
    try:
        if args == ["create"]:
            result = create_manifest()
        else:
            # The fixed manifest path is read with the same file safety rules.
            reader = _Reader()
            base = _load_baseline(reader)
            from benchmarks.archive_ui_build import _pin as pin_file
            artifact = pin_file(base["roots"]["manifest"])
            reader.final()
            result = verify_frozen_product(dict(base["apks"], build=artifact))
        print(json.dumps(result, sort_keys=True, indent=2, allow_nan=False))
        return 0
    except (ValueError, OSError, KeyError, TypeError, IndexError, RecursionError, OverflowError, UnicodeError) as error:
        reason = str(error) if isinstance(error, BuildRefused) else "artifact"
        print("diagnostic build refused: " + reason, file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
