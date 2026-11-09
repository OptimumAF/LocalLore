"""File-only binding for the two Android archive provider cancellation methods.

Copyright 2026 LocalLore contributors. SPDX-License-Identifier: Apache-2.0
"""
from io import BytesIO
from pathlib import PureWindowsPath
import struct
from zipfile import BadZipFile

from benchmarks import android_instrumentation_evidence as evidence
from benchmarks import archive_ui_build as files
from benchmarks import owned_target_contract as core
from benchmarks import receipt_avd_environment as env
from scripts.audit_physical_model_apk import dex_classes

APP = "org.locallore.app.archiveverify"
TEST = APP + ".test"
ANDROID_SOURCE = "91de52b4e82fae062584713f84f61c47cdd76769"
_CLASS = "org.locallore.app.ArchiveProviderPlatformTest"
INSTRUMENTATIONS = (
    ("archive_import_open", _CLASS, "cancelledReadOnlyOpenDrainsAndNextImportReadsExactlyTheAssetSlice"),
    ("archive_export_open", _CLASS, "cancelledReadWriteOpenClosesTheLateDestinationAndNextExportWrites"),
)

_ROOT = PureWindowsPath("D:/Dev/Experiments/LocalLore/2026-11-09-archive-provider-both-platform-v1")
_BUILD_OUTPUT = PureWindowsPath(
    "D:/Worktrees/LocalLore-archive-provider-both-platform-v1/apps/android/app/build-archive-verification/outputs/apk"
)
_ARTIFACTS = (
    ("build", "verified-pair-91de52b4.json", 1_373,
     "fbd26daf7c7a111d1edd080c8cc5315bae6cde1872dbd0d0d74d35bbc0db08b2"),
    ("product_apk", "app-debug.apk", 28_161_304,
     "a0b92505aabae6fe2758e426a4ab1c9ffecf03c8ebd53a24aee40b80e6510350"),
    ("test_apk", "app-debug-androidTest.apk", 2_560_246,
     "bb10b70f8b374d6593a5b50b88d71a7f44667958c98f084a11ef8efb7710f17c"),
)
_TEST_DESCRIPTOR = ("L" + _CLASS.replace(".", "/") + ";").encode("ascii")
_PROVIDER_DESCRIPTOR = b"Lorg/locallore/app/ArchiveDocumentProvider;"


def artifact_bindings():
    return {role: {"path": str(_ROOT / name), "bytes": size, "sha256": sha256}
            for role, name, size, sha256 in _ARTIFACTS}


def _verify_dex(product, test):
    fixtures = {_TEST_DESCRIPTOR, _PROVIDER_DESCRIPTOR}
    core._need(not fixtures.intersection(dex_classes(BytesIO(product))), "binding")
    classes = dex_classes(BytesIO(test), with_code=True)
    core._need(fixtures <= classes.keys(), "binding")
    class_flags, methods = classes[_TEST_DESCRIPTOR]
    core._need(class_flags & 1 and not class_flags & (0x200 | 0x400), "binding")
    expected = sorted(method.encode("ascii") for _, _, method in INSTRUMENTATIONS)
    selected = [row for row in methods if row[3] is True or row[0] in expected]
    core._need(sorted(row[0] for row in selected) == expected, "binding")
    for _, prototype, access, annotated, units in selected:
        core._need(prototype == (b"V", 0) and access in (1, 17)
                   and annotated is True and type(units) is int and units > 0, "binding")


def verify_artifacts(pins):
    """Check frozen archived bytes and both actual JUnit definitions before admission."""
    expected = artifact_bindings()
    apks = [
        {"path": str(_BUILD_OUTPUT / output), "bytes": expected[role]["bytes"],
         "sha256": expected[role]["sha256"], "signature_verified": True}
        for role, output in (("product_apk", "debug/app-debug.apk"),
                             ("test_apk", "androidTest/debug/app-debug-androidTest.apk"))
    ]
    build = {
        "source": ANDROID_SOURCE,
        "app_id": APP,
        "test_id": TEST,
        "provider_process": ":archive_test_provider",
        "selectors": [klass + "#" + method for _, klass, method in INSTRUMENTATIONS],
        "test_permissions": ["android.permission.REORDER_TASKS"],
        "apks": apks,
        "jvm": {"suites": 92, "tests": 724, "errors": 0, "failures": 0, "skipped": 0},
        "android_executed": False,
    }
    try:
        core._need(core._same(pins, expected), "binding")
        report = files._bound(expected["build"], cap=expected["build"]["bytes"])
        core._need(core._same(env.decode_json(report), build), "binding")
        product = files._bound(expected["product_apk"], cap=expected["product_apk"]["bytes"])
        test = files._bound(expected["test_apk"], cap=expected["test_apk"]["bytes"])
        _verify_dex(product, test)
    except (OSError, TypeError, ValueError, RuntimeError, BadZipFile, struct.error):
        raise core.TargetRefused("binding") from None


def _selector(kind):
    core._need(type(kind) is str, "capability")
    for label, klass, method in INSTRUMENTATIONS:
        if kind == label:
            return klass, method
    raise core.TargetRefused("capability")


def instrumentation_argv(kind):
    klass, method = _selector(kind)
    return ["am", "instrument", "-w", "-r", "-e", "class", klass + "#" + method,
            TEST + "/androidx.test.runner.AndroidJUnitRunner"]


def validate_result(kind, raw):
    klass, method = _selector(kind)
    return evidence.validate_instrumentation(raw, klass, [method])
