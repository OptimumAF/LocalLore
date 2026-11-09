"""Fixed B110 build attestation; file inspection only, never run authority.

Copyright 2026 LocalLore contributors. SPDX-License-Identifier: Apache-2.0
"""
import copy
import hashlib
import math
from pathlib import Path
import re

from benchmarks import diagnostic_ui_build as shared

BuildRefused = shared.BuildRefused
_Reader = shared._Reader
_need = shared._need
_equal = shared._equal
_pin = shared._pin
SCOPE = "record-cancellation-ui-build-v1"
MODE = "fixed-b110-byte-attestation-v1"
BASELINE_PATH = Path(__file__).with_name("record_cancellation_ui_build_baseline.json")
BASELINE_BYTES = 741682
BASELINE_SHA256 = "8cce430fa23ffa1562e2f0397e6cbebd763183a6c2de79fec2bac27416048cce"
UI_CLASS = "org.locallore.app.StoryRecordCancellationScreenTest"
VM_CLASS = "org.locallore.app.StoryRecordCancellationViewModelTest"
UI_SOURCE = "apps/android/app/src/androidTest/java/org/locallore/app/StoryRecordCancellationScreenTest.kt"
VM_SOURCE = "apps/android/app/src/test/java/org/locallore/app/StoryRecordCancellationViewModelTest.kt"
REPORT = "docs/android/RECORD_CANCELLATION_UI_VERIFICATION_2026-11-03.md"
PARSER = "scripts/audit_physical_model_apk.py"
METHODS = (
    "cancelledCurrentPageShowsSafeRetryAndReusesTheExactFrozenCursor",
    "cancelledScopedDetailRendersSafeProblemAndRetriesTheSamePlayerLens",
    "obsoletePageCancellationCannotReplaceSectionSelectionOrClosedAndReopenedRecords",
    "oldDetailCancellationAfterBackCannotFinishTheReplacementDetail",
    "disposedOwnerAndRemountedScreenCannotBorrowOldReadsOrRetainedCallbacks",
)
INSTRUMENTATIONS = tuple(("record_cancel_" + str(i), UI_CLASS, name)
                        for i, name in enumerate(METHODS, 1))
ROLES = frozenset(("build", "product_apk", "test_apk"))
ENCODING = "Exact recorded raw Git snapshot bytes; no newline normalization"
_CAPTURE = Path("D:/Dev/Experiments/LocalLore/2026-11-03-record-cancellation-ui-v1")
_ROOTS = dict(product=str(_CAPTURE / "candidate-source-v1"), capture=str(_CAPTURE),
    manifest=str(Path("D:/Dev/Experiments/LocalLore/2026-11-03-record-cancellation-ui-build-v1") /
                 "record-cancellation-ui-build-v1.json"))
_PRODUCT = dict(head="7e29fb724ed781e953f321385f66a5f8982ad0f1",
    tree="39adcae73aae5448f9a3052d5125f1d4cc0d0033",
    tested_head="b591dcc1e7f4d49cd21b7c727d09e0fa6f5959d9",
    tested_tree="b0bdf62d2e3f98f46c27faff89bc0f781802edb4",
    base="7a0602df0db96fa5aa78c1a3667c5ec7fb3eca23",
    base_count=2586, tested_count=2588, source_count=2589)
_PHASES = ("focused-v1", "validation-v1", "package-v1")
_OWNER_BLOB = "64cde2f5c014b01798cd7e945e3bd592434a5993"
_OWNER_SHA = "51e94325ed5e59a31c64fcc274e7a41c40b9dd969b09d39df7be56b0ee941598"
_OWNER_PATH = str(Path("D:/Dev/Repositories/LocalLore/benchmarks/runtime_spike.py"))
_OWNER_REVIEW = "096c517857c95fc854154bbf60d46cb85b6d6d74"
_PYTHON = str(Path("C:/Users/Avery/AppData/Local/Programs/Python/Python314/python.exe"))
_JAVA = "C:/Program Files/Java/jdk-21/bin/java.exe"
_CERT = "17ed497138b20dc1657d54039802305cfe0e3b782c73feaad20359c954707564"
_REASONS = frozenset(("binding", "json", "source", "changed", "path", "budget", "baseline",
    "roster", "report", "phase", "command", "environment", "owner", "worker", "execution",
    "artifact", "audit", "lint", "dex", "roles", "manifest", "shape", "count"))


def _keys(value, names, reason="shape"):
    _need(type(value) is dict and set(value) == set(names), reason)


def _int(value, low=0, high=2**63 - 1, reason="count"):
    _need(type(value) is int and low <= value <= high, reason)
    return value


def _inside(path, root):
    _need(type(path) is str and Path(path).is_absolute() and
          Path(path).is_relative_to(Path(root)), "path")


def _pins(value):
    if type(value) is dict:
        if set(value) == {"path", "bytes", "sha256"}:
            yield _pin(value)
        else:
            for child in value.values():
                yield from _pins(child)
    elif type(value) is list:
        for child in value:
            yield from _pins(child)


def _validate_base(base):
    _keys(base, ("version", "scope", "mode", "source_encoding", "roots", "product", "sources",
                 "phases", "apks", "copies", "package", "compiled", "host_owner"))
    _need(type(base["version"]) is int and base["version"] == 1 and
          base["scope"] == "record-cancellation-ui-build-baseline-v1" and
          base["mode"] == MODE and base["source_encoding"] == ENCODING, "baseline")
    roots, product = base["roots"], base["product"]
    _keys(roots, ("product", "capture", "manifest"))
    for path in roots.values():
        _need(type(path) is str and Path(path).is_absolute(), "path")
    _inside(roots["product"], roots["capture"])
    _keys(product, tuple(_PRODUCT))
    for name in ("head", "tree", "tested_head", "tested_tree", "base"):
        _need(shared._hex(product[name], 40), "source")
    for name in ("base_count", "tested_count", "source_count"):
        _int(product[name], 1, 65536)
    _need(product["tested_count"] == product["base_count"] + 2 and
          product["source_count"] == product["tested_count"] + 1, "source")
    _keys(base["apks"], ("product_apk", "test_apk"))
    _keys(base["copies"], ("product_apk", "test_apk"))
    _keys(base["package"], ("audit_0", "audit_1", "lint"))
    for name in ("audit_0", "audit_1"):
        _keys(base["package"][name], ("request", "result", "stdout", "stderr"))
    _need(type(base["phases"]) is list and len(base["phases"]) == 3 and
          all(type(p) is dict for p in base["phases"]) and
          [p.get("name") for p in base["phases"]] == list(_PHASES), "phase")
    for phase in base["phases"]:
        _keys(phase, ("name", "request", "result", "owner", "launch", "worker", "stdout", "stderr",
                      "worker_stderr", "before", "after", "junit"))
        _need(type(phase["junit"]) is list, "report")
    for pin in _pins(base):
        if not _equal(pin, base["host_owner"]):
            _inside(pin["path"], roots["capture"])
    _pin(base["compiled"])
    _pin(base["host_owner"])
    return base


def _load_baseline(reader):
    pin = dict(path=str(BASELINE_PATH), bytes=BASELINE_BYTES, sha256=BASELINE_SHA256)
    base = reader.json(pin)
    _validate_base(base)
    _need(_equal(base["roots"], _ROOTS) and _equal(base["product"], _PRODUCT) and
          base["host_owner"]["path"] == _OWNER_PATH and
          base["host_owner"]["sha256"] == _OWNER_SHA, "baseline")
    return base


def _source_map(rows, omit):
    return [dict(path=row["path"], size=row["bytes"], sha256=row["sha256"])
            for row in rows if row["path"] not in omit]


def _sources(base, reader):
    rows = base["sources"]
    _need(type(rows) is list and len(rows) == base["product"]["source_count"], "source")
    _need(all(type(row) is dict for row in rows), "source")
    paths = [row.get("path") for row in rows]
    _need(all(type(p) is str for p in paths) and paths == sorted(paths) and
          len({p.casefold() for p in paths}) == len(paths), "source")
    bodies = {}
    for row in rows:
        _keys(row, ("path", "mode", "git_blob", "bytes", "sha256"), "source")
        shared._relative(row["path"])
        _need(row["mode"] in ("100644", "100755") and shared._hex(row["git_blob"], 40), "source")
        raw = reader.read(dict(path=str(Path(base["roots"]["product"]) / row["path"]),
                              bytes=row["bytes"], sha256=row["sha256"]), data=True)
        _need(shared._object_hash(b"blob", raw) == row["git_blob"], "source")
        if row["path"] in (UI_SOURCE, VM_SOURCE, PARSER):
            bodies[row["path"]] = raw
    _need(set((UI_SOURCE, VM_SOURCE, REPORT, PARSER)).issubset(paths), "source")
    _need(shared._tree(rows) == base["product"]["tree"] and
          shared._tree([r for r in rows if r["path"] != REPORT]) == base["product"]["tested_tree"], "source")
    _need(shared._methods(bodies[UI_SOURCE]) == list(METHODS) and
          len(shared._methods(bodies[VM_SOURCE])) == 3, "roster")
    return bodies


def _expected_command(base, phase):
    root = Path(base["roots"]["product"])
    command = [_JAVA, "-classpath", str(root / "apps/android/gradle/wrapper/gradle-wrapper.jar"),
               "org.gradle.wrapper.GradleWrapperMain"]
    command += ([":app:assembleDebug", ":app:assembleDebugAndroidTest", ":app:lintDebug"]
                if phase == "package-v1" else [":app:testDebugUnitTest"])
    command += ["--offline", "--no-daemon", "--console=plain", "-Pandroid.builder.sdkDownload=false",
                "-Pkotlin.compiler.execution.strategy=in-process",
                "-Dorg.gradle.java.installations.auto-download=false", "--max-workers=2"]
    if phase == "focused-v1":
        command += ["--tests", VM_CLASS]
    return command


def _junit(reader, pins, count, suites, vm_methods):
    _need(len(pins) == suites and len({p["path"] for p in pins}) == suites, "report")
    names, cases = set(), set()
    for pin in pins:
        xml = shared._xml(reader, pin)
        name = xml.get("name")
        _need(xml.tag == "testsuite" and name and name not in names and
              Path(pin["path"]).name == "TEST-" + name + ".xml" and
              all(xml.get(k) == "0" for k in ("failures", "errors", "skipped")), "report")
        names.add(name)
        entries = xml.findall("testcase")
        _need(entries and xml.get("tests") == str(len(entries)), "report")
        for entry in entries:
            key = (entry.get("classname"), entry.get("name"))
            _need(key[0] == name and key[1] and key not in cases and not any(
                entry.findall(".//" + tag) for tag in ("failure", "error", "skipped")), "report")
            cases.add(key)
    _need(len(cases) == count and
          {method for klass, method in cases if klass == VM_CLASS} == set(vm_methods), "report")
    return cases


def _phase(base, phase, reader, owner, vm_methods):
    name = phase["name"]
    capture, product = Path(base["roots"]["capture"]), Path(base["roots"]["product"])
    for key in ("request", "result", "stdout", "stderr", "worker_stderr", "before", "after"):
        _need(phase[key]["path"] == str(capture / name / (
            {"before": "sources-before", "after": "sources-after",
             "worker_stderr": "worker-stderr"}.get(key, key) +
            (".txt" if key in ("stdout", "stderr", "worker_stderr") else ".json"))), "path")
    for key in ("owner", "launch", "worker"):
        suffix = "-worker.py" if key == "worker" else "-" + key + ".json"
        _need(phase[key]["path"] == str(capture / (name + suffix)), "path")
    request, result = reader.json(phase["request"]), reader.json(phase["result"])
    recorded, launch = reader.json(phase["owner"]), reader.json(phase["launch"])
    _keys(request, ("command", "cwd", "source_base", "limits", "environment"), "phase")
    _need(_equal(request["command"], _expected_command(base, name)) and
          request["cwd"] == str(product / "apps/android") and request["source_base"] == base["product"]["base"], "command")
    _need(_equal(request["limits"], dict(gradle_deadline_seconds=170, parent_deadline_seconds=180,
        capture_bytes=8 * 1024**2, generated_postrun_planning_bytes=2 * 1024**3)), "budget")
    _need(_equal(request["environment"], dict(TEMP="D:/Dev/_Temp", TMP="D:/Dev/_Temp",
        JAVA_HOME="C:/Program Files/Java/jdk-21", ANDROID_HOME="C:/Users/Avery/AppData/Local/Android/Sdk",
        ANDROID_SDK_ROOT="C:/Users/Avery/AppData/Local/Android/Sdk",
        GRADLE_USER_HOME="D:/Dev/Tools/Caches/Gradle", CARGO_HOME="D:/Dev/Tools/Caches/Cargo-LocalLore-v1")), "environment")
    _keys(recorded, ("status", "returncode", "elapsed_ms", "stderr_bytes", "cleanup_complete", "owner"), "owner")
    _need(recorded["status"] == "completed" and type(recorded["returncode"]) is int and
          recorded["returncode"] == 0 and recorded["cleanup_complete"] is True and
          _equal(recorded["owner"], owner), "owner")
    _int(recorded["elapsed_ms"], 0, 180000, "owner")
    _need(type(recorded["stderr_bytes"]) is int and recorded["stderr_bytes"] == 0, "owner")
    _keys(launch, ("command", "worker_bytes", "worker_sha256", "owner", "no_device_or_sdk_management"), "owner")
    _need(_equal(launch["command"], [_PYTHON, "-I", "-S", "-B", phase["worker"]["path"], name]) and
          _equal(launch["owner"], owner) and launch["no_device_or_sdk_management"] is True and
          type(launch["worker_bytes"]) is int and launch["worker_bytes"] == phase["worker"]["bytes"] and
          launch["worker_sha256"] == phase["worker"]["sha256"], "worker")
    reader.read(phase["worker"])
    omit = {REPORT, UI_SOURCE} if name == "focused-v1" else {REPORT}
    expected = _source_map(base["sources"], omit)
    _need(_equal(reader.json(phase["before"]), expected) and
          _equal(reader.json(phase["after"]), expected), "source")
    _keys(result, ("exit", "seconds", "source_unchanged", "source_files", "android_tree_bytes",
                   "artifacts", "instrumentation_executed"), "phase")
    _need(type(result["exit"]) is int and result["exit"] == 0 and result["source_unchanged"] is True and
          type(result["source_files"]) is int and result["source_files"] == len(expected) and
          result["instrumentation_executed"] is False and type(result["seconds"]) in (int, float) and
          math.isfinite(result["seconds"]) and 0 <= result["seconds"] <= recorded["elapsed_ms"] / 1000, "phase")
    _int(result["android_tree_bytes"], 1, 2 * 1024**3, "budget")
    stdout = reader.read(phase["stdout"], data=True).decode("utf-8", errors="strict")
    _need(reader.read(phase["stderr"], data=True) == b"" and
          reader.read(phase["worker_stderr"], data=True) == b"", "execution")
    lines = stdout.splitlines()
    _need(sum(line.startswith("BUILD SUCCESSFUL in ") for line in lines) == 1 and
          not any("BUILD FAILED" in line for line in lines), "execution")
    headers = [re.fullmatch(r"> Task :app:([A-Za-z0-9]+)(.*)", line) for line in lines]
    headers = [(m[1], m[2]) for m in headers if m]
    required = (("buildRustAndroid", "compileDebugKotlin", "compileDebugUnitTestKotlin", "testDebugUnitTest")
                if name == "focused-v1" else ("testDebugUnitTest",) if name == "validation-v1" else
                ("compileDebugAndroidTestKotlin", "assembleDebug", "assembleDebugAndroidTest",
                 "lintAnalyzeDebug", "lintReportDebug", "lintDebug"))
    _need(all([suffix for task, suffix in headers if task == critical] == [""] for critical in required), "execution")
    if name != "package-v1":
        _need(result["artifacts"] == [], "phase")
        return _junit(reader, phase["junit"], 3 if name == "focused-v1" else 425,
                      1 if name == "focused-v1" else 50, vm_methods)
    _need(phase["junit"] == [] and _equal(result["artifacts"], [
        dict(path=base["apks"][role]["path"], copy=base["copies"][role]["path"],
             size=base["apks"][role]["bytes"], sha256=base["apks"][role]["sha256"])
        for role in ("product_apk", "test_apk")]), "artifact")
    return set()


def _package(base, reader):
    product = Path(base["roots"]["product"])
    app, test = (base["apks"][r] for r in ("product_apk", "test_apk"))
    for role in ("product_apk", "test_apk"):
        original, retained = base["apks"][role], base["copies"][role]
        _need(Path(original["path"]) != Path(retained["path"]) and
              _equal({k: original[k] for k in ("bytes", "sha256")},
                     {k: retained[k] for k in ("bytes", "sha256")}), "artifact")
        reader.read(original)
        reader.read(retained)
    expected_commands = (
        [_PYTHON, "-I", "-S", "-B", str(product / "scripts/audit_apk.py"), app["path"]],
        [_PYTHON, "-I", "-S", "-B", str(product / "scripts/audit_instrumentation_apk.py"),
         app["path"], test["path"]],
    )
    reports = []
    for i in range(2):
        record = base["package"]["audit_" + str(i)]
        request, result = reader.json(record["request"]), reader.json(record["result"])
        _need(_equal(request, dict(command=expected_commands[i])) and
              _equal(result, dict(returncode=0)) and
              reader.read(record["stderr"], data=True) == b"", "audit")
        reports.append(reader.json(record["stdout"]))
    main, pair = reports
    _keys(main, ("status", "permissions", "libraries"), "audit")
    _need(main["status"] == "passed" and
          main["permissions"] == ["org.locallore.app.DYNAMIC_RECEIVER_NOT_EXPORTED_PERMISSION"] and
          type(main["libraries"]) is list and
          all(type(r) is dict for r in main["libraries"]), "audit")
    library_names = {f"lib/{abi}/{name}" for abi in ("arm64-v8a", "x86_64")
                     for name in ("libandroidx.graphics.path.so", "liblocallore_android.so")}
    _need(len(main["libraries"]) == 4 and
          {r.get("entry") for r in main["libraries"]} == library_names, "audit")
    for library in main["libraries"]:
        _keys(library, ("entry", "elf_load_alignment"), "audit")
        _need(_equal(library["elf_load_alignment"], [16384, 16384, 16384]), "audit")
    _keys(pair, ("status", "package", "test_package", "test_permissions",
                 "certificate_sha256", "app", "test"), "audit")
    _need(pair["status"] == "passed" and pair["package"] == "org.locallore.app" and
          pair["test_package"] == "org.locallore.app.test" and
          pair["test_permissions"] == ["android.permission.REORDER_TASKS"] and
          pair["certificate_sha256"] == _CERT and
          _equal(pair["app"], {k: app[k] for k in ("bytes", "sha256")}) and
          _equal(pair["test"], {k: test[k] for k in ("bytes", "sha256")}), "audit")
    lint = shared._xml(reader, base["package"]["lint"])
    _need(lint.tag == "issues" and
          [(r.get("id"), r.get("severity")) for r in lint.findall("issue")] ==
          [("GradleDependency", "Warning"), ("AutoboxingStateCreation", "Hint")], "lint")
    return main, pair


def _compiled(base, reader, bodies):
    proof = reader.json(base["compiled"])
    _keys(proof, ("class", "class_access_flags", "methods", "source_sha256", "artifacts",
                  "compiled_junit_eligible_methods", "instrumentation_executed",
                  "parser_source", "qualification"), "dex")
    _need(proof["class"] == UI_CLASS and
          type(proof["compiled_junit_eligible_methods"]) is int and
          proof["compiled_junit_eligible_methods"] == 5 and
          type(proof["instrumentation_executed"]) is int and proof["instrumentation_executed"] == 0 and
          proof["source_sha256"] == hashlib.sha256(bodies[UI_SOURCE]).hexdigest() and
          _equal(proof["parser_source"], dict(path=PARSER,
              sha256=hashlib.sha256(bodies[PARSER]).hexdigest())), "dex")
    expected_artifacts = [
        dict(path=base["apks"][r]["path"], copy=base["copies"][r]["path"],
             size=base["apks"][r]["bytes"], sha256=base["apks"][r]["sha256"])
        for r in ("product_apk", "test_apk")]
    _need(_equal(proof["artifacts"], expected_artifacts) and
          type(proof["qualification"]) is str, "dex")
    # The old proof's parser SHA belongs to the product source. The current
    # reviewed bounded runtime parser can additionally inspect code-item units.
    app = reader.definitions(base["apks"]["product_apk"])
    test = reader.definitions(base["apks"]["test_apk"])
    prefix = ("L" + UI_CLASS.replace(".", "/")).encode("ascii")
    descriptor = prefix + b";"
    _need(not any(name.startswith(prefix) for name in app) and descriptor in test, "dex")
    flags, definitions = test[descriptor]
    _int(flags, 0, 0xffffffff, "dex")
    _need(flags & 1 and not flags & (0x200 | 0x400) and
          type(proof["class_access_flags"]) is int and proof["class_access_flags"] == flags, "dex")
    _need({r[0].decode("ascii") for r in definitions if r[3]} == set(METHODS), "dex")
    recorded, selected = [], []
    for selector, klass, method in INSTRUMENTATIONS:
        matches = [r for r in definitions if r[0] == method.encode("ascii")]
        _need(len(matches) == 1 and len(matches[0]) == 5, "dex")
        _, proto, access, junit, units = matches[0]
        _need(proto == (b"V", 0) and type(proto[1]) is int and type(access) is int and access & 1 and
              not access & (8 | 0x100 | 0x400) and junit is True and
              type(units) is int and units > 0, "dex")
        recorded.append(dict(name=method, return_type="void", parameters=0,
                             access_flags=access, runtime_junit_test=True))
        selected.append(dict(selector=selector, class_name=klass, method=method,
                             instruction_units=units))
    expected_rows = [{("return" if k == "return_type" else k): v for k, v in row.items()} for row in recorded]
    _need(_equal(proof["methods"], expected_rows), "dex")
    return selected


def _attest_impl(base, reader):
    """Private coherent-fixture seam. Public entry points load only pinned data."""
    _validate_base(base)
    # Inspect every declared evidence binding, including zero-byte stderr, so
    # no discarded sidecar can silently stop participating in the fixed graph.
    for pin in _pins(base):
        reader.read(pin)
    bodies = _sources(base, reader)
    owner_raw = reader.read(base["host_owner"], data=True)
    owner = dict(path=base["host_owner"]["path"], sha256=base["host_owner"]["sha256"],
                 git_blob=shared._object_hash(b"blob", owner_raw), reviewed_pr361=_OWNER_REVIEW)
    vm_methods = shared._methods(bodies[VM_SOURCE])
    cohorts = [_phase(base, p, reader, owner, vm_methods) for p in base["phases"]]
    _need(cohorts[0].issubset(cohorts[1]) and not cohorts[2], "report")
    main, pair = _package(base, reader)
    selected = _compiled(base, reader, bodies)
    reader.final()
    return copy.deepcopy(dict(version=1, scope=SCOPE, mode=MODE,
        product=dict(root=base["roots"]["product"], **base["product"]),
        artifacts=base["apks"], current_native_bindings=main["libraries"],
        evidence=dict(phases=base["phases"], package=base["package"],
                      compiled=base["compiled"], host_owner=base["host_owner"]),
        facts=dict(recorded_jvm_cases=425, recorded_jvm_suites=50, jvm_failures=0, jvm_errors=0,
                   jvm_skips=0, compiled_ui_methods=5, selected_runtime_methods=5,
                   android_runtime_executed=False, model_material=False, run_authority=False,
                   feature_acceptance=False, native_runtime_executed=False,
                   native_compilation_repeated=False, remote_rechecked=False,
                   tool_binary_revalidation=False, intermediate_cohorts_additive=False,
                   source_encoding=ENCODING, package_audit=pair, selected_methods=selected),
        instrumentations=[list(r) for r in INSTRUMENTATIONS]))


def _artifact_roles(artifacts):
    _keys(artifacts, ROLES, "roles")
    for pin in artifacts.values():
        _pin(pin)


def _run(artifacts=None):
    try:
        if artifacts is not None:
            _artifact_roles(artifacts)
        reader = _Reader()
        base = _load_baseline(reader)
        saved = None
        if artifacts is not None:
            _need(all(_equal(artifacts[r], base["apks"][r]) for r in ("product_apk", "test_apk")) and
                  artifacts["build"]["path"] == base["roots"]["manifest"] and
                  artifacts["build"]["bytes"] <= shared.MAX_JSON, "roles")
            saved = reader.json(artifacts["build"])
        expected = _attest_impl(base, reader)
        if artifacts is not None:
            _need(_equal(saved, expected), "manifest")
        return expected
    except BuildRefused as error:
        if str(error) in _REASONS:
            raise
        raise BuildRefused("artifact") from None
    except Exception:
        # File guards may use RuntimeError-derived refusals. Keep every ordinary
        # inspection failure finite and text-free; interrupts still propagate.
        raise BuildRefused("artifact") from None


def create_manifest():
    """Return deterministic nonexecutable metadata; never publishes a file."""
    return _run()


def verify_frozen_product(artifacts):
    """Revalidate exactly build/product_apk/test_apk, without execution authority."""
    _artifact_roles(artifacts)
    return _run(artifacts)


def main(argv=None):
    import json
    import sys
    args = sys.argv[1:] if argv is None else argv
    if args not in (["create"], ["verify"]):
        print("usage: python -m benchmarks.record_cancellation_ui_build create|verify", file=sys.stderr)
        return 2
    try:
        if args == ["create"]:
            value = create_manifest()
        else:
            reader = _Reader()
            base = _load_baseline(reader)
            from benchmarks.archive_ui_build import _pin as file_pin
            pin = file_pin(base["roots"]["manifest"])
            reader.final()
            value = verify_frozen_product(dict(base["apks"], build=pin))
        print(json.dumps(value, sort_keys=True, indent=2, allow_nan=False))
        return 0
    except Exception as error:
        reason = str(error) if isinstance(error, BuildRefused) and str(error) in _REASONS else "artifact"
        print("record cancellation build refused: " + reason, file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
