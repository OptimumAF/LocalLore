"""Current-source record UI build admission; file/Git replay, never SDK execution.

Copyright 2026 LocalLore contributors. SPDX-License-Identifier: Apache-2.0
"""
import ast
import copy
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import re
import subprocess
import sys
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[1]
if __package__ in (None, ""):
    sys.path.insert(0, str(ROOT))

BUILD_KEYS = frozenset(("version", "scope", "head", "public", "apks", "jvm_reports", "lint", "roster"))
PUBLIC_FILES = {
    "request": "request-v1.json", "result": "result-v1.json",
    "public_result": "public-result-v1.json", "stdout": "owner-stdout-v1.bin",
    "stderr": "owner-stderr-v1.bin", "sources_before": "sources-before-v1.json",
    "sources_after": "sources-after-v1.json",
}
BUILD = ROOT / "apps/android/app/build-archive-verification"
APK_PATHS = {"product_apk": BUILD / "outputs/apk/debug/app-debug.apk",
             "test_apk": BUILD / "outputs/apk/androidTest/debug/app-debug-androidTest.apk"}
EXPECTED_JVM = 380
EXPECTED_REPORTS = 43
CRITICAL_TASKS = (
    "buildRustAndroid", "compileDebugKotlin", "compileDebugAndroidTestKotlin",
    "testDebugUnitTest", "lintAnalyzeDebug", "lintReportDebug", "lintDebug",
    "assembleDebug", "assembleDebugAndroidTest",
)
QUERY2_POLICY_METHODS = ('allFiveDefaultsUseQuery2WhileExplicitLegacyPlayerQueriesRemainVersion1', 'everyCapturedNativePageDecodesWithoutSkippingRowsFlatteningScopeOrLeakingForbiddenText', 'nativeUnseenCorrectionPreservesKnownObservationUntilAnActualRediscovery', 'exactPrivateCorrectionMarkerHasNoEventOrNavigationAuthority', 'scopedMessagesRetainOriginalScopeAndOrderedIdsWhileLegacyMessagesStayExplicitV1', 'progressionRelationshipsAndObservedKnowledgeAcceptOnlyVersionedTypedSourcesAndPlayerSubjects', 'versionedCursorAndPageFramesRefuseCrossVersionTypesAndFrozenContextDrift', 'progressionSourceDrillUsesExactAncestorTupleAndCurrentLensAndRejectsWrongReturnedBranch', 'nonCooperativeQuery2RepliesCannotReviveDismissedDisposedOrReplacedContexts', 'controllerRefusesStalePageIdentityAndClearsPrivateFailuresWithoutDispatchingEvidence', 'actualGatewayDecodesEveryOpaqueAuthoredNativePageUsingItsSnapshotBoundPlayer', 'actualGatewayBindsOpaqueProfileItemsBeliefsPromisesAndEventWitnessesWithoutRewritingSpeakers', 'explicitQuery1GatewayUsesOpaqueSnapshotIdentityAndRefusesAValidLiteralPlayerForgery', 'missingOrFailedSnapshotBindingRefusesBeforeAnyInspectionBytesAreRequested', 'inFlightReadRejectsObserverChangeReusedAttachmentHeadAdvanceAndClosure')
MAX_FILE = 128 * 1024 ** 2


class BuildRefused(ValueError):
    """A fixed reason, without private artifact text or paths."""


def _need(value, reason="build"):
    if not value:
        raise BuildRefused(reason)


def _read(path, cap=MAX_FILE, *, project=True):
    from benchmarks import receipt_avd_environment as env
    path = Path(path)
    if project:
        path = env.safe_path(path)
        _need(path.drive.upper() == "D:", "path")
    else:
        # Installed executable/JDK/SDK files are allowed tools, not project payload.
        _need(path.is_absolute() and path.resolve(strict=True) == path and not path.is_symlink(), "tool")
    before = path.stat()
    _need(path.is_file() and before.st_nlink == 1 and 0 <= before.st_size <= cap, "size")
    with path.open("rb") as stream:
        raw = stream.read(before.st_size + 1)
        held = os.fstat(stream.fileno())
    after = path.stat()
    stamp = lambda s: (s.st_size, s.st_mtime_ns, s.st_ino, s.st_dev)
    _need(stamp(before) == stamp(held) == stamp(after) and len(raw) == before.st_size, "changed")
    return raw


def _pin(path, *, project=True):
    raw = _read(path, project=project)
    return dict(path=str(Path(path)), bytes=len(raw), sha256=hashlib.sha256(raw).hexdigest())


def _bound(pin, cap=MAX_FILE, *, project=True):
    _need(type(pin) is dict and set(pin) == {"path", "bytes", "sha256"}, "binding")
    _need(type(pin["path"]) is str and type(pin["bytes"]) is int and 0 <= pin["bytes"] <= cap and
          type(pin["sha256"]) is str and re.fullmatch("[0-9a-f]{64}", pin["sha256"]), "binding")
    raw = _read(pin["path"], cap, project=project)
    _need(len(raw) == pin["bytes"] and hashlib.sha256(raw).hexdigest() == pin["sha256"], "binding")
    return raw


def _pairs(items):
    result = {}
    for key, value in items:
        _need(key not in result, "json")
        result[key] = value
    return result


def _json(pin):
    try:
        return json.loads(_bound(pin, 2 * 1024 ** 2).decode("utf-8"), object_pairs_hook=_pairs,
                          parse_constant=lambda _: (_ for _ in ()).throw(BuildRefused("json")))
    except (UnicodeError, json.JSONDecodeError, RecursionError):
        raise BuildRefused("json") from None


def _git(*args):
    _need(ROOT.drive.upper() == "D:" and ROOT.resolve(strict=True) == ROOT, "source")
    return subprocess.check_output(["git", *args], cwd=ROOT, stderr=subprocess.DEVNULL)


def _current_head():
    _need(_git("status", "--porcelain") == b"", "source")
    head = _git("rev-parse", "HEAD").decode("ascii").strip()
    _need(re.fullmatch("[0-9a-f]{40}", head), "source")
    return head


def _current_sources():
    names = _git("ls-files", "-z").decode("utf-8").split("\0")[:-1]
    _need(names and len(names) == len(set(names)), "source")
    result = {}
    for name in names:
        relative = PurePosixPath(name)
        _need(not relative.is_absolute() and ".." not in relative.parts and "\\" not in name, "source")
        result[name] = hashlib.sha256(_read(ROOT / name, 8 * 1024 ** 2)).hexdigest()
    return result


def _roster():
    from benchmarks import owned_record_ui_contract as contract
    return [list(row) for row in contract.INSTRUMENTATIONS]


def _dex(path):
    # Definition decoding only. No AAPT, Java, signature tool or SDK is invoked.
    from scripts.audit_physical_model_apk import dex_classes
    return dex_classes(Path(path))


def _verify_selectors(product, tests, roster):
    from benchmarks import android_instrumentation_evidence as evidence
    app, test = _dex(product), _dex(tests)
    classes = {}
    for _, klass, method in roster:
        classes.setdefault(klass, []).append(method)
    for klass, methods in classes.items():
        source = ROOT / "apps/android/app/src/androidTest/java" / (klass.replace(".", "/") + ".kt")
        _need(evidence.test_roster(source) == methods, "roster")
        descriptor = ("L" + klass.replace(".", "/") + ";").encode("ascii")
        _need(descriptor not in app and descriptor in test, "dex")
        class_flags, definitions = test[descriptor]
        _need(class_flags & 1 and not class_flags & (0x200 | 0x400), "dex")
        for method in methods:
            matches = [(proto, flags, junit) for name, proto, flags, junit in definitions
                       if name == method.encode("ascii")]
            _need(len(matches) == 1 and matches[0][0] == (b"V", 0) and matches[0][1] & 1 and
                  not matches[0][1] & (8 | 0x400) and matches[0][2] is True, "dex")


def _xml(pin):
    raw = _bound(pin, 2 * 1024 ** 2)
    _need(b"<!DOCTYPE" not in raw.upper() and b"<!ENTITY" not in raw.upper(), "report")
    try:
        return ET.fromstring(raw)
    except ET.ParseError:
        raise BuildRefused("report") from None


def _reports(reports, lint):
    directory = BUILD / "test-results/testDebugUnitTest"
    expected = sorted(directory.glob("TEST-*.xml"))
    _need(type(reports) is list and len(reports) == EXPECTED_REPORTS and
          [Path(pin["path"]) for pin in reports] == expected, "report")
    cases = []
    for pin in reports:
        suite = _xml(pin)
        _need(suite.tag == "testsuite" and all(int(suite.attrib[k]) == 0 for k in
              ("failures", "errors", "skipped")), "report")
        _need(suite.get("name") and Path(pin["path"]).name == "TEST-" + suite.get("name") + ".xml", "report")
        rows = suite.findall("testcase")
        _need(int(suite.attrib["tests"]) == len(rows), "report")
        for row in rows:
            _need(not any(row.findall(".//" + k) for k in ("failure", "error", "skipped")), "report")
            _need(row.get("classname") == suite.get("name") and row.get("name"), "report")
            cases.append((row.get("classname"), row.get("name")))
    _need(len(cases) == len(set(cases)) == EXPECTED_JVM, "report")
    from benchmarks import android_instrumentation_evidence as evidence
    policy = evidence.test_roster(ROOT / "apps/android/app/src/test/java/org/locallore/app/TranscriptFollowTest.kt")
    _need(len(policy) == 8 and {name for klass, name in cases if klass == "org.locallore.app.TranscriptFollowTest"} == set(policy), "report")
    observed_policy = evidence.test_roster(ROOT / "apps/android/app/src/test/java/org/locallore/app/Query2StoryRecordTest.kt")
    _need(tuple(observed_policy) == QUERY2_POLICY_METHODS and
          {name for klass, name in cases if klass == "org.locallore.app.Query2StoryRecordTest"} == set(QUERY2_POLICY_METHODS), "report")
    _need(Path(lint["path"]) == BUILD / "reports/lint-results-debug.xml", "report")
    _need(not any(issue.get("severity") in ("Error", "Fatal") for issue in _xml(lint)), "lint")


def _public(pins, head):
    _need(type(pins) is dict and set(pins) == set(PUBLIC_FILES), "public")
    parent = Path(pins["request"]["path"]).parent
    for role, name in PUBLIC_FILES.items():
        _need(Path(pins[role]["path"]) == parent / name, "public")
    request, result, public = (_json(pins[k]) for k in ("request", "result", "public_result"))
    expected = [sys.executable, "-I", "-S", "-B", str(ROOT / "scripts/check.py"),
                "android", "--archive-verification", "--offline"]
    _need(type(request["version"]) is int and request["version"] == 1 and
          request["head"] == head and request["command"] == expected and
          type(request["owner_seconds"]) is int and request["owner_seconds"] == 900 and
          request["sources"] == pins["sources_before"], "public")
    names = {"android.injected.signing." + name for name in
             ("store.file", "store.password", "key.alias", "key.password")}
    _need(request["signing_property_names"] == sorted(names) and request["signing_values_logged"] is False, "public")
    tools = request["tools"]
    _need(type(tools) is list and len(tools) == 7 and len({p["path"] for p in tools}) == 7, "tool")
    expected_tools = {"run-public-v1.py", "python.exe", "java.exe", "jvm.dll", "aapt2.exe",
                      "apksigner.jar", "signing-compatibility-v1.json"}
    _need({Path(p["path"]).name.lower() for p in tools} == expected_tools, "tool")
    for pin in tools:
        _bound(pin, project=Path(pin["path"]).drive.upper() == "D:")
    _need(type(result["version"]) is int and result["version"] == 1 and result["passed"] is True and result["sources_equal"] is True and
          result["tools_equal"] is True and result["feature_acceptance"] is False, "public")
    owner = result["owner"]
    _need(owner["status"] == "child_exited" and type(owner["worker_returncode"]) is int and owner["worker_returncode"] == 0 and
          owner["cleanup_complete"] is owner["output_capture_complete"] is True and
          type(owner["elapsed_ms"]) is int and 0 <= owner["elapsed_ms"] <= 900000, "public")
    _need(type(public["returncode"]) is int and public["returncode"] == 0 and
          type(public["elapsed_ms"]) is int and 0 <= public["elapsed_ms"] <= owner["elapsed_ms"], "public")
    stdout, stderr = _bound(pins["stdout"], 262144), _bound(pins["stderr"], 262144)
    _need(type(owner["stderr_bytes"]) is int and type(owner["stdout_bytes"]) is int and
          stderr == b"" and owner["stderr_bytes"] == 0 and owner["stdout_bytes"] == len(stdout), "public")
    text = stdout.decode("utf-8", errors="strict")
    lines = text.splitlines(keepends=True)
    starts = [index for index, line in enumerate(lines) if line.startswith("+ ")]
    _need(len(starts) == 3, "public")
    commands = [ast.literal_eval(lines[index][2:].strip()) for index in starts]
    task_rows = [line.rstrip("\r\n") for line in lines[starts[0] + 1:starts[1]]
                 if line.startswith("> Task :app:")]
    for task in CRITICAL_TASKS:
        expected_task = "> Task :app:" + task
        matching = [row for row in task_rows if row == expected_task or row.startswith(expected_task + " ")]
        # Gradle can repeat a bare heading when grouping compiler warnings.
        # Every observed state must still indicate execution, never a cache hit.
        _need(matching and all(row == expected_task for row in matching), "freshness")
    java = next(p["path"] for p in tools if Path(p["path"]).name.lower() == "java.exe")
    gradle = [java, "-classpath", str(ROOT / "apps/android/gradle/wrapper/gradle-wrapper.jar"),
              "org.gradle.wrapper.GradleWrapperMain", ":app:assembleDebug", ":app:assembleDebugAndroidTest",
              ":app:testDebugUnitTest", ":app:lintDebug", "--no-daemon", "--console=plain",
              "-Pandroid.builder.sdkDownload=false", "-PlocalLoreArchiveVerification=true", "--offline"]
    _need(commands == [gradle,
          [sys.executable, str(ROOT / "scripts/audit_apk.py"), str(APK_PATHS["product_apk"]), "--archive-verification"],
          [sys.executable, str(ROOT / "scripts/audit_instrumentation_apk.py"), str(APK_PATHS["product_apk"]),
           str(APK_PATHS["test_apk"]), "--archive-verification"]], "public")
    product = json.loads("".join(lines[starts[1] + 1:starts[2]]))
    pair = json.loads("".join(lines[starts[2] + 1:]))
    _need(product["status"] == pair["status"] == "passed", "public")
    before, after = _json(pins["sources_before"]), _json(pins["sources_after"])
    _need(before == after == _current_sources(), "source")
    return pair


def _verify_manifest(value):
    from benchmarks import owned_record_ui_contract as contract
    _need(type(value) is dict and set(value) == BUILD_KEYS and type(value["version"]) is int and
          value["version"] == 1 and value["scope"] == "record-ui-build-v1", "build")
    _need(value["head"] == _current_head() and value["roster"] == _roster(), "source")
    pair = _public(value["public"], value["head"])
    _need(pair["package"] == contract.APP and pair["test_package"] == contract.TEST and
          pair["test_permissions"] == ["android.permission.REORDER_TASKS"] and
          re.fullmatch("[0-9a-f]{64}", pair["certificate_sha256"]), "package")
    _need(type(value["apks"]) is dict and set(value["apks"]) == set(APK_PATHS), "apk")
    for role, package, key in (("product_apk", contract.APP, "app"), ("test_apk", contract.TEST, "test")):
        item = value["apks"][role]
        _need(type(item) is dict and set(item) == {"binding", "package", "certificate_sha256"} and
              Path(item["binding"]["path"]) == APK_PATHS[role] and item["package"] == package and
              item["certificate_sha256"] == pair["certificate_sha256"], "apk")
        _bound(item["binding"])
        _need(type(pair[key]) is dict and set(pair[key]) == {"bytes", "sha256"} and
              type(pair[key]["bytes"]) is int, "apk")
        _need(pair[key] == {k: item["binding"][k] for k in ("bytes", "sha256")}, "apk")
    _reports(value["jvm_reports"], value["lint"])
    _verify_selectors(APK_PATHS["product_apk"], APK_PATHS["test_apk"], value["roster"])
    _need(value["head"] == _current_head() and _json(value["public"]["sources_after"]) == _current_sources(), "source")
    return copy.deepcopy(value)


def make_manifest(public_run_root):
    root = Path(public_run_root)
    public = {role: _pin(root / name) for role, name in PUBLIC_FILES.items()}
    stdout = _bound(public["stdout"], 262144).decode("utf-8")
    last = [line for line in stdout.splitlines() if line.startswith("+ ")][-1]
    pair = json.loads(stdout[stdout.index(last) + len(last):].strip())
    from benchmarks import owned_record_ui_contract as contract
    apks = {role: dict(binding=_pin(path), package=package, certificate_sha256=pair["certificate_sha256"])
            for (role, path), package in zip(APK_PATHS.items(), (contract.APP, contract.TEST))}
    value = dict(version=1, scope="record-ui-build-v1", head=_current_head(), public=public, apks=apks,
                 jvm_reports=[_pin(p) for p in sorted((BUILD / "test-results/testDebugUnitTest").glob("TEST-*.xml"))],
                 lint=_pin(BUILD / "reports/lint-results-debug.xml"), roster=_roster())
    return _verify_manifest(value)


def write_manifest(public_run_root, output_path):
    from benchmarks import receipt_avd_environment as env
    value = make_manifest(public_run_root)
    path = Path(output_path)
    env.safe_path(path.parent, directory=True)
    _need(path.drive.upper() == "D:", "path")
    with path.open("xb") as stream:
        stream.write(json.dumps(value, sort_keys=True, separators=(",", ":")).encode("utf-8"))
    return _pin(path)


def verify_current(admission):
    try:
        value = _verify_manifest(_json(admission["artifacts"]["build"]))
        _need(all(admission["artifacts"][role] == item["binding"] for role, item in value["apks"].items()), "apk")
        return value
    except BuildRefused:
        raise
    except (OSError, ValueError, KeyError, TypeError, IndexError, StopIteration, SyntaxError, RecursionError):
        raise BuildRefused("build") from None


def main(argv=None):
    import argparse
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--public-run", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args(argv)
    try:
        print(json.dumps(write_manifest(args.public_run, args.output)))
        return 0
    except (BuildRefused, OSError, ValueError, KeyError, TypeError, IndexError, StopIteration, SyntaxError):
        print("Record UI build refused", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
