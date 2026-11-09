"""Frozen APP/TEST binding for the saved-library status regression.

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

APP = "org.locallore.app"
TEST = APP + ".test"
ANDROID_SOURCE = "3d967b6332f342a57044383bf79c0d18a95a3074"
INSTRUMENTATIONS = (
    ("library_status", "org.locallore.app.ui.SavedLibraryStatusScreenTest",
     "catalogAdviceTracksConfirmedLibraryState"),
)

_ROOT = PureWindowsPath("D:/Dev/Experiments/LocalLore/2026-11-09-saved-library-recovery-v1")
_ARTIFACTS = (
    ("build", _ROOT / f"host-evidence-{ANDROID_SOURCE[:8]}-v1.json", 737,
     "e1167dd52882ee673e3170ed96526bb16afd0a388e4fa32935c62bd5674d37fc"),
    ("product_apk", _ROOT / "app-debug.apk", 28_012_664,
     "327bf8f7ee40610e23fa949b743d02d36cb02d78e1919ce2025136cbc3f8450d"),
    ("test_apk", _ROOT / "app-debug-androidTest.apk", 2_269_058,
     "3eb72b9fb1c0c22b37a52eb277122ab000cb59a8d59a64e7696eb8e863e71d24"),
)
_PAIR_AUDIT = (_ROOT / f"audit-pair-{ANDROID_SOURCE[:8]}-v1.log", 456,
               "246b4899be2a819106ee39c2fa21ce6b09ee6d66a4bedbea62e591bce9e2b16e")
_CERTIFICATE = "17ed497138b20dc1657d54039802305cfe0e3b782c73feaad20359c954707564"


def _pin(path, size, digest):
    return {"path": str(path), "bytes": size, "sha256": digest}


def artifact_bindings():
    return {role: _pin(path, size, digest) for role, path, size, digest in _ARTIFACTS}


def _bound(pin):
    return files._bound(pin, cap=pin["bytes"])


def _verify_dex(app, test, klass, method):
    descriptor = ("L" + klass.replace(".", "/") + ";").encode("ascii")
    core._need(descriptor not in dex_classes(BytesIO(app)), "binding")
    classes = dex_classes(BytesIO(test))
    core._need(descriptor in classes, "binding")
    class_flags, definitions = classes[descriptor]
    core._need(class_flags & 1 and not class_flags & (0x200 | 0x400), "binding")
    name = method.encode("ascii")
    selected = [row for row in definitions if row[0] == name or row[3] is True]
    core._need(len(selected) == 1, "binding")
    actual, prototype, flags, junit = selected[0]
    core._need(actual == name and prototype == (b"V", 0) and flags & 1
               and not flags & (8 | 0x400) and junit is True, "binding")


def verify_artifacts(pins):
    """Replay the build, signed pair and selector without starting Android tools."""
    expected = artifact_bindings()
    _, klass, method = INSTRUMENTATIONS[0]
    app = {key: expected["product_apk"][key] for key in ("bytes", "sha256")}
    test = {key: expected["test_apk"][key] for key in ("bytes", "sha256")}
    build = {
        "head": ANDROID_SOURCE,
        "baseline": {"tests": 5, "failures": 3, "errors": 0, "skipped": 0},
        "jvm": {"suites": 49, "tests": 422, "failures": 0, "errors": 0, "skipped": 0, "new_tests": 5},
        "lint": {"Warning": 1, "Hint": 1},
        "app": app,
        "test": test,
        "compose_selector": klass + "#" + method,
        "android_executed": False,
    }
    audit = {
        "status": "passed", "package": APP, "test_package": TEST,
        "test_permissions": ["android.permission.REORDER_TASKS"],
        "certificate_sha256": _CERTIFICATE, "app": app, "test": test,
    }
    try:
        core._need(type(pins) is dict and all(type(pin) is dict for pin in pins.values())
                   and core._same(pins, expected), "binding")
        core._need(core._same(env.decode_json(_bound(expected["build"])), build), "binding")
        core._need(core._same(env.decode_json(_bound(_pin(*_PAIR_AUDIT))), audit), "binding")
        _verify_dex(_bound(expected["product_apk"]), _bound(expected["test_apk"]), klass, method)
    except (OSError, TypeError, ValueError, RuntimeError, BadZipFile, struct.error):
        raise core.TargetRefused("binding") from None


def _selector(kind):
    label, klass, method = INSTRUMENTATIONS[0]
    core._need(type(kind) is str and kind == label, "capability")
    return klass, method


def instrumentation_argv(kind):
    klass, method = _selector(kind)
    return ["am", "instrument", "-w", "-r", "-e", "class", klass + "#" + method,
            TEST + "/androidx.test.runner.AndroidJUnitRunner"]


def validate_result(kind, raw):
    klass, method = _selector(kind)
    return evidence.validate_instrumentation(raw, klass, [method])
