"""Bind and capture the two fixed Android storage-opener regressions.

The caller supplies a command function backed by an already admitted owner.
This module does not launch an emulator, access ADB, or grant run authority.

Copyright 2026 LocalLore contributors. SPDX-License-Identifier: Apache-2.0
"""
from io import BytesIO
from pathlib import PureWindowsPath
import struct
from zipfile import BadZipFile

from benchmarks import android_instrumentation_evidence as evidence
from benchmarks import archive_ui_build as files
from benchmarks import owned_target_contract as core
from scripts.audit_instrumentation_apk import STORAGE_OPENER_TESTS, audit_storage_opener_selectors
from scripts.audit_physical_model_apk import RUNNER, dex_classes

APP = "org.locallore.app.archiveverify"
TEST = APP + ".test"
KINDS = ("archive_opener", "deletion_opener")
ANDROID_SOURCE = "0ea7a68896242a7e1c90dfe280a9184af59306fa"
AUDIT_SOURCE = "968db00448a3a821d215bacd04123bd6d5c817cf"

_ROOT = PureWindowsPath("D:/Dev/Experiments/LocalLore/2026-11-09-storage-opener-apk-pair-v1")
_ARTIFACTS = (
    ("build", "verified-pair-0ea7a688.json", 2_242,
     "8a953915f104fd87f3b7dd7945ddb706e4558fa72a33da62bc9cef5113556ce3"),
    ("product_apk", "app-debug.apk", 28_161_304,
     "295da3e6e3e4d7eb141015c2ea35130be49564124414d5b7490d98fdafe32178"),
    ("test_apk", "app-debug-androidTest.apk", 2_557_694,
     "43eb85a692cff8cbf1b57b2cf628814fb72ddd4200ccf7b366b33887c894975e"),
)


def artifact_bindings():
    return {role: dict(path=str(_ROOT / name), bytes=size, sha256=digest)
            for role, name, size, digest in _ARTIFACTS}


def verify_artifacts(pins):
    """Re-read the exact #544 report and archived APKs, then verify their DEX."""
    expected = artifact_bindings()
    try:
        core._need(core._same(pins, expected), "binding")
        report = files._json(expected["build"])
        pair = report["pair_audit"]
        core._need(core._same(report["version"], 1) and report["scope"] == "storage-opener-apk-pair-v1"
                   and report["app_source"] == ANDROID_SOURCE and report["audit_source"] == AUDIT_SOURCE
                   and report["android_executed"] is False and report["apk_audit"]["status"] == "passed"
                   and pair["status"] == "passed" and pair["package"] == APP and pair["test_package"] == TEST
                   and pair["runner"] == RUNNER, "binding")
        for role, key in (("product_apk", "app"), ("test_apk", "test")):
            pin = expected[role]
            core._need(core._same(pair[key], {"bytes": pin["bytes"], "sha256": pin["sha256"]}), "binding")
        product = files._bound(expected["product_apk"], cap=expected["product_apk"]["bytes"])
        test = files._bound(expected["test_apk"], cap=expected["test_apk"]["bytes"])
        selectors = audit_storage_opener_selectors(dex_classes(BytesIO(product)),
                                                   dex_classes(BytesIO(test), with_code=True))
        core._need(core._same(pair["selectors"], selectors)
                   and selectors == [instrumentation_argv(kind)[6] for kind in KINDS], "binding")
        return selectors
    except (OSError, TypeError, ValueError, RuntimeError, BadZipFile, struct.error, KeyError):
        raise core.TargetRefused("binding") from None


def _selector(kind):
    core._need(type(kind) is str and kind in KINDS, "capability")
    name, method = STORAGE_OPENER_TESTS[KINDS.index(kind)]
    return "org.locallore.app.ui." + name, method


def instrumentation_argv(kind):
    klass, method = _selector(kind)
    return ["am", "instrument", "-w", "-r", "-e", "class", klass + "#" + method,
            TEST + "/" + RUNNER]


def validate_result(kind, raw):
    klass, method = _selector(kind)
    return evidence.validate_instrumentation(raw, klass, [method])


def capture_tests(pins, command):
    """Collect both tests in order through the caller's qualified command adapter.

    The adapter must enforce the owned client, deadlines and successful host
    command completion. This step validates the independently captured stdout.
    """
    verify_artifacts(pins)
    results = []
    for kind in KINDS:
        raw = command(instrumentation_argv(kind), kind, seconds=90, limit=evidence.MAX_BYTES)
        results.append(dict(kind=kind, **validate_result(kind, raw)))
    return results
