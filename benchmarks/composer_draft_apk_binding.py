"""File-only verification of the isolated composer draft regression APKs.

Copyright 2026 LocalLore contributors. SPDX-License-Identifier: Apache-2.0
"""
from io import BytesIO
from pathlib import PureWindowsPath
import struct
from zipfile import BadZipFile

from benchmarks import archive_ui_build as files
from benchmarks import owned_target_contract as core
from benchmarks import receipt_avd_environment as env
from scripts.audit_physical_model_apk import dex_classes

APP = "org.locallore.app.draftverify"
TEST = APP + ".test"
RUNNER = "androidx.test.runner.AndroidJUnitRunner"
ANDROID_SOURCE = "50ca9aca67a299a459f786dd49cad2e9500b3de7"
TEST_CLASS = "org.locallore.app.PlayDraftRestorationTest"
METHODS = tuple(sorted((
    "exactKindAndTextRestoreAcrossSameScopeHeadsAndOnlyExplicitSendDispatches",
    "unresolvedAsyncAndRecoveryHideSavedPayloadUntilOnlyItsExactScopeReturns",
    "settledBranchAndStorySwitchesDiscardTheSingleDraftWithoutPerStoryResurrection",
    "retainedEditAndSendActionsCannotChangeOrSubmitTheNewScopeDraft",
    "disposedComposerActionsCannotEditAReopenedDraftForTheSameScope",
    "saveBoundUsesUtf8BytesAndDoesNotRelaxTheSmallerSendBound",
    "unsafeSavedPayloadIsOmittedWholeWithPersistentReentryNoticeAndOriginalKind",
    "sameRenderKindThenTextRetainsBothLatestFields",
    "sameRenderTextThenKindRetainsBothLatestFields",
    "retainedSendAfterSameRenderEditsSubmitsLatestScopedInputOnce",
    "retainedEnabledSendAfterSameRenderClearDoesNotSubmit",
)))
_TEST_DESCRIPTOR = ("L" + TEST_CLASS.replace(".", "/") + ";").encode("ascii")
_ROOT = PureWindowsPath("D:/Dev/Experiments/LocalLore/2026-11-09-composer-apk-pair-v1")
_ARTIFACTS = (
    ("build", "verified-pair-50ca9aca.json", 2_016,
     "78f569b5159d89879a53823ed5c5c4c5d4b4b101b7913f04abba8ca52e3c0f24"),
    ("product_apk", "app-debug.apk", 28_161_304,
     "28d5b035809e7becdef21d9331e67c968bda5e3e20a2c6a0fa43a91d6f2af86b"),
    ("test_apk", "app-debug-androidTest.apk", 2_552_186,
     "2d832b5e6c0ee49b34606d1b5af6a6a69f66ef81f70828591d1828340a44a3e9"),
)


def artifact_bindings():
    return {role: dict(path=str(_ROOT / name), bytes=size, sha256=digest)
            for role, name, size, digest in _ARTIFACTS}


def _build_record(pins):
    return dict(version=1, scope="composer-draft-apk-pair-v1", source=ANDROID_SOURCE,
                app=APP, test=TEST, runner=RUNNER,
                apks={role: pins[role] for role in ("product_apk", "test_apk")},
                selectors=[TEST_CLASS + "#" + name for name in METHODS],
                jvm=dict(suites=90, tests=717, failures=0, errors=0, skipped=0),
                lint=dict(errors=0, warnings=3),
                package_audit=True, matching_signers=True, android_executed=False)


def _verify_dex(product, test):
    files._need(_TEST_DESCRIPTOR not in dex_classes(BytesIO(product)), "binding")
    test_classes = dex_classes(BytesIO(test), with_code=True)
    files._need(_TEST_DESCRIPTOR in test_classes, "binding")
    flags, methods = test_classes[_TEST_DESCRIPTOR]
    files._need(flags & 1 and not flags & (0x200 | 0x400), "binding")
    expected = tuple(name.encode("ascii") for name in METHODS)
    selected = [row for row in methods if row[3] is True or row[0] in expected]
    files._need(tuple(sorted(row[0] for row in selected)) == expected, "binding")
    for _, prototype, access, annotated, units in selected:
        files._need(prototype == (b"V", 0) and access in (1, 17)
                    and annotated is True and type(units) is int and units > 0, "binding")
    return METHODS


def verify_artifacts(pins):
    """Verify only the frozen build report, archived APKs and compiled method roster."""
    try:
        expected = artifact_bindings()
        files._need(set(expected) == {"build", "product_apk", "test_apk"}
                    and core._same(pins, expected), "binding")
        report = files._bound(expected["build"], cap=expected["build"]["bytes"])
        files._need(core._same(env.decode_json(report), _build_record(expected)), "binding")
        product = files._bound(expected["product_apk"], cap=expected["product_apk"]["bytes"])
        test = files._bound(expected["test_apk"], cap=expected["test_apk"]["bytes"])
        return _verify_dex(product, test)
    except (OSError, TypeError, ValueError, RuntimeError, BadZipFile, struct.error, KeyError):
        raise files.BuildRefused("binding") from None
