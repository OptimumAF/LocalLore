"""Fixed artifact and JUnit evidence policy for the combined Story Record cohort.

Copyright 2026 LocalLore contributors. SPDX-License-Identifier: Apache-2.0
"""
from pathlib import PureWindowsPath

from benchmarks import android_instrumentation_evidence as evidence
from benchmarks import archive_ui_build as files
from benchmarks import owned_target_contract as core
from benchmarks import receipt_avd_environment as env

APP = "org.locallore.app.archiveverify"
TEST = APP + ".test"
ANDROID_SOURCE = "25ab2e9a3cd201bae4765efc3c705df185921f61"
INSTRUMENTATIONS = (
    ("cancel_page", "org.locallore.app.StoryRecordCancellationScreenTest",
     "cancelledCurrentPageShowsSafeRetryAndReusesTheExactFrozenCursor"),
    ("cancel_event", "org.locallore.app.StoryRecordCancellationScreenTest",
     "cancelledScopedDetailRendersSafeProblemAndRetriesTheSamePlayerLens"),
    ("obsolete_page", "org.locallore.app.StoryRecordCancellationScreenTest",
     "obsoletePageCancellationCannotReplaceSectionSelectionOrClosedAndReopenedRecords"),
    ("obsolete_event", "org.locallore.app.StoryRecordCancellationScreenTest",
     "oldDetailCancellationAfterBackCannotFinishTheReplacementDetail"),
    ("dispose_record", "org.locallore.app.StoryRecordCancellationScreenTest",
     "disposedOwnerAndRemountedScreenCannotBorrowOldReadsOrRetainedCallbacks"),
    ("stale_story", "org.locallore.app.ui.StoryRecordActionScopeScreenTest",
     "retainedSearchNextAndCloseCannotRetargetAnotherStoryOrBranchAndFreshControlsStillWork"),
    ("stale_page", "org.locallore.app.ui.StoryRecordActionScopeScreenTest",
     "equalValuedReopenAndLaterPagesRejectOldButtonsWithoutResettingTheCurrentDialogue"),
    ("stale_event", "org.locallore.app.ui.StoryRecordActionScopeScreenTest",
     "retainedListAndEventRetryBackAndSourceActionsCannotAffectFreshDetailsOrReopenedRecords"),
    ("large_text", "org.locallore.app.StoryRecordLargeTextTest",
     "narrowRecordReflowsAtDoubleTextSizeAndKeepsActionsReachable"),
    ("page_scroll", "org.locallore.app.StoryRecordPageScrollTest",
     "nextAndFirstStartAtTheTopOfTheirRenderedPage"),
    ("query_scroll", "org.locallore.app.StoryRecordPageScrollTest",
     "changingSectionAppliedSearchOrContextStartsAtTheTop"),
    ("event_scroll", "org.locallore.app.StoryRecordPageScrollTest",
     "openingAnEventAndGoingBackRestoresTheSamePageOffset"),
)

_ROOT = PureWindowsPath("D:/Dev/Experiments/LocalLore/2026-11-09-record-combined-ui-v1")
_APKS = _ROOT / f"verified-apks-{ANDROID_SOURCE[:8]}"
_ARTIFACTS = (
    ("build", _ROOT / f"host-verification-{ANDROID_SOURCE[:8]}-v1.json", 1907,
     "c056b138d750a991142e015d7da1ec31d246c19b6032670bcdf4f6ecc9b970c9"),
    ("product_apk", _APKS / "app-debug.apk", 28012684,
     "4554f954c61113c51da1585328ca5001a74ec905814574eabf96cff39b8d419e"),
    ("test_apk", _APKS / "app-debug-androidTest.apk", 2321874,
     "0fd3f9eb264f9a1229efbe5516f9173ae7c122463ba4590b31bc8709fba6e56a"),
)
_AUDIT = (_ROOT / f"audit-pair-{ANDROID_SOURCE[:8]}-v1.log", 484,
          "df5debb836908468c884edef4857ca6f0ff07368b855f004583bf134b8e563cc")
_SIGNER = "17ed497138b20dc1657d54039802305cfe0e3b782c73feaad20359c954707564"


def _pin(path, size, sha256):
    return {"path": str(path), "bytes": size, "sha256": sha256}


def artifact_bindings():
    return {role: _pin(path, size, digest) for role, path, size, digest in _ARTIFACTS}


def _bound(pin):
    return files._bound(pin, cap=pin["bytes"])


def verify_artifacts(pins):
    """Check the fixed receipts and APK bytes without opening a device connection."""
    expected = artifact_bindings()
    core._need(core._same(pins, expected), "binding")
    try:
        build = env.decode_json(_bound(expected["build"]))
        host_counts = {"tests": 442, "failures": 0, "errors": 0, "skipped": 0, "suites": 53}
        selectors = [klass + "#" + method for _, klass, method in INSTRUMENTATIONS]
        core._need(type(build) is dict and
                   all(core._same(build.get(key), count) for key, count in host_counts.items()) and
                   core._same(build.get("qualified_selectors"), selectors), "binding")

        audit = env.decode_json(_bound(_pin(*_AUDIT)))
        expected_audit = {
            "status": "passed", "package": APP, "test_package": TEST,
            "test_permissions": ["android.permission.REORDER_TASKS"], "certificate_sha256": _SIGNER,
            "app": {key: expected["product_apk"][key] for key in ("bytes", "sha256")},
            "test": {key: expected["test_apk"][key] for key in ("bytes", "sha256")},
        }
        core._need(core._same(audit, expected_audit), "binding")
        _bound(expected["product_apk"])
        _bound(expected["test_apk"])
    except (OSError, ValueError, RuntimeError):
        raise core.TargetRefused("binding") from None


def _selector(kind):
    for label, klass, method in INSTRUMENTATIONS:
        if type(kind) is str and kind == label:
            return klass, method
    raise core.TargetRefused("capability")


def instrumentation_argv(kind):
    klass, method = _selector(kind)
    return ["am", "instrument", "-w", "-r", "-e", "class", klass + "#" + method,
            TEST + "/androidx.test.runner.AndroidJUnitRunner"]


def validate_result(kind, raw):
    klass, method = _selector(kind)
    return evidence.validate_instrumentation(raw, klass, [method])
