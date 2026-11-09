"""Read-only binding for the isolated cross-owner deletion Activity test.

Copyright 2026 LocalLore contributors. SPDX-License-Identifier: Apache-2.0
"""
from pathlib import PureWindowsPath
import json
import struct
import sys
from zipfile import BadZipFile

if __package__ in (None, ""):
    from pathlib import Path
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from benchmarks import android_instrumentation_evidence as evidence
from benchmarks import archive_ui_build as files
from benchmarks import owned_target_contract as core
from benchmarks import receipt_avd_environment as env
from benchmarks.saved_library_status_binding import _verify_dex

SCOPE = "cross-owner-deletion-ui-binding-v1"
APP = "org.locallore.app.storydelete"
TEST = APP + ".test"
RUNNER = "androidx.test.runner.AndroidJUnitRunner"
ANDROID_SOURCE = "fdb8f622cdff0a4b1ee4e4d1e93d356995440544"
INSTRUMENTATIONS = (
    ("cross_owner_deletion_recovery", "org.locallore.app.CrossOwnerDeletionRecoveryMainActivityTest",
     "recoversRetainedStoryAfterAnotherOwnerDeletesSelection"),
)

_ROOT = PureWindowsPath("D:/Dev/Experiments/LocalLore/2026-11-09-cross-owner-deletion-ui-v1")
_ARTIFACTS = (
    ("build", "publish-summary.json", 348,
     "3d90f805d50303785f2ad4148c4469085f6c403fdca9b5ec9c4856f589779881"),
    ("product_apk", "app-storydelete.apk", 28_161_292,
     "7eb84420693759dd3a1c0b547a46fcfebeb6c4fdcbb15fe4c4c2e51ee50018db"),
    ("test_apk", "test-storydelete.apk", 2_555_606,
     "e5148a0bce6f24ec28cbbfd925d4175a3a4ce673b963ce9154f917cabd4424fa"),
)
_AUDIT = ("apk-audit.json", 1185, "f1889a3b037b9ebb49137d1dac0a48b75808d729256d0bd4f49f3735326f9fa1")
_CERTIFICATE = "17ed497138b20dc1657d54039802305cfe0e3b782c73feaad20359c954707564"


def _pin(name, size, digest):
    return {"path": str(_ROOT / name), "bytes": size, "sha256": digest}


def artifact_bindings():
    return {role: _pin(name, size, digest) for role, name, size, digest in _ARTIFACTS}


def _bound(pin):
    return files._bound(pin, cap=pin["bytes"])


def verify_artifacts(pins):
    """Verify the preserved bytes, recorded audit and exact annotated DEX method."""
    expected = artifact_bindings()
    _, klass, method = INSTRUMENTATIONS[0]
    build = {
        "head": ANDROID_SOURCE, "exit_code": 0, "suites": 90,
        "tests": 720.0, "failures": 0.0, "errors": 0.0, "skipped": 0.0,
        "lint": [
            {"id": "GradleDependency", "severity": "Warning"},
            {"id": "AutoboxingStateCreation", "severity": "Hint"},
        ],
    }
    audit_facts = {
        "head": ANDROID_SOURCE, "app_package": APP, "test_package": TEST,
        "target_package": APP, "runner": RUNNER, "signer_sha256": _CERTIFICATE,
        "abis": ["arm64-v8a", "x86_64"], "zip_alignment_verified": True,
        "selector": klass + "#" + method, "selector_in_test_only": True,
    }
    try:
        core._need(core._same(pins, expected), "binding")
        core._need(core._same(env.decode_json(_bound(expected["build"])), build), "binding")
        audit = env.decode_json(_bound(_pin(*_AUDIT)))
        core._obj(audit, set(audit_facts) | {"app", "test"}, "binding")
        core._need(core._same({key: audit[key] for key in audit_facts}, audit_facts), "binding")
        for field, role in (("app", "product_apk"), ("test", "test_apk")):
            row = audit[field]
            core._obj(row, ("path", "bytes", "sha256"), "binding")
            # The audit recorded the build outputs. Verify the preserved copies by content.
            core._need(core._same({key: row[key] for key in ("bytes", "sha256")},
                                 {key: expected[role][key] for key in ("bytes", "sha256")}), "binding")
        _verify_dex(_bound(expected["product_apk"]), _bound(expected["test_apk"]), klass, method)
    except (OSError, KeyError, TypeError, ValueError, RuntimeError, BadZipFile, struct.error):
        raise core.TargetRefused("binding") from None


def _selector(kind):
    label, klass, method = INSTRUMENTATIONS[0]
    core._need(type(kind) is str and kind == label, "capability")
    return klass, method


def instrumentation_argv(kind):
    klass, method = _selector(kind)
    return ["am", "instrument", "-w", "-r", "-e", "class", klass + "#" + method,
            TEST + "/" + RUNNER]


def validate_result(kind, raw):
    klass, method = _selector(kind)
    return evidence.validate_instrumentation(raw, klass, [method])


def main(argv=None):
    args = sys.argv[1:] if argv is None else argv
    report = {"scope": SCOPE, "execution_authorized": False}
    try:
        core._need(args == [], "schema")
        pins = artifact_bindings()
        verify_artifacts(pins)
    except core.TargetRefused as failure:
        report.update(status="refused", reason=str(failure))
        print(json.dumps(report, sort_keys=True))
        return 1
    label, klass, method = INSTRUMENTATIONS[0]
    report.update(status="verified", android_source=ANDROID_SOURCE, artifacts=pins,
                  audit=_pin(*_AUDIT), app=APP, test=TEST, selector=klass + "#" + method,
                  instrumentation_argv=instrumentation_argv(label))
    print(json.dumps(report, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
