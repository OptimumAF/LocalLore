"""Fixed file and JUnit evidence policy for the synthetic setup action test.

Copyright 2026 LocalLore contributors. SPDX-License-Identifier: Apache-2.0
"""
from pathlib import PureWindowsPath

from benchmarks import android_instrumentation_evidence as evidence
from benchmarks import archive_ui_build as files
from benchmarks import owned_target_contract as core
from benchmarks import receipt_avd_environment as env

APP = "org.locallore.app.modelpickerverify"
TEST = APP + ".test"
ANDROID_SOURCE = "ef8d3a3be38a18750725a97d85378342e5c574a5"
INSTRUMENTATIONS = (
    ("picker_action_scope", "org.locallore.app.ModelPickerActionScopeTest",
     "retiredChooseAndCheckCannotActOnReplacementStatus"),
)

_ROOT = PureWindowsPath("D:/Dev/Experiments/LocalLore/2026-11-09-model-picker-action-scope-v1")
_ARTIFACTS = (
    ("build", _ROOT / f"audit-test-pair-{ANDROID_SOURCE[:8]}-v1.log", 763,
     "50dd9fc0743a6b940a8efac56c1a2abb120731b30b35dad78aa556c549919e05"),
    ("product_apk", _ROOT / "app-debug.apk", 78_697_092,
     "ce1bba095a49ffa1f9c8be3c6ab4fd3b1ae5502fe07a7cf49e7005fa9c0d44ca"),
    ("test_apk", _ROOT / "app-debug-androidTest.apk", 2_423_912,
     "44815baedc1ae9dccd39976820f4a8ff94b5a3e3b3659c6881975c938f11434e"),
)


def artifact_bindings():
    return {
        role: {"path": str(path), "bytes": size, "sha256": digest}
        for role, path, size, digest in _ARTIFACTS
    }


def verify_artifacts(pins):
    """Replay the fixed pair audit and exact APK bytes on the host."""
    expected = artifact_bindings()
    _, klass, method = INSTRUMENTATIONS[0]
    document_authority = TEST + ".modelpicker"
    audit = {
        "status": "passed",
        "selector": klass + "#" + method,
        "defined_in": "classes3.dex",
        "present_in_app": False,
        "test_permissions": ["android.permission.REORDER_TASKS"],
        "test_provider": {
            "document_authority": document_authority,
            "control_authority": document_authority + ".control",
            "process": ":model_picker_provider",
        },
        "app": {key: expected["product_apk"][key] for key in ("bytes", "sha256")},
        "test": {key: expected["test_apk"][key] for key in ("bytes", "sha256")},
    }
    try:
        core._need(type(pins) is dict and all(type(pin) is dict for pin in pins.values()) and
                   core._same(pins, expected), "binding")
        receipt = expected["build"]
        readback = env.decode_json(files._bound(receipt, cap=receipt["bytes"]))
        core._need(core._same(readback, audit), "binding")
        for role in ("product_apk", "test_apk"):
            pin = expected[role]
            files._bound(pin, cap=pin["bytes"])
    except (OSError, TypeError, ValueError, RuntimeError):
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
