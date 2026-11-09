"""Fixed cold-navigation command and result policy over the guarded SDK wire.

This module performs no device or process action.
Copyright 2026 LocalLore contributors. SPDX-License-Identifier: Apache-2.0
"""
from pathlib import PureWindowsPath

from benchmarks import android_instrumentation_evidence as evidence
from benchmarks import archive_ui_build as files
from benchmarks import owned_target_contract as core
from benchmarks import receipt_avd_environment as env

PROTOCOL = "owned-emulator-cold-navigation-ui-v1"
RUN_SCOPE = PROTOCOL
APP = "org.locallore.app.draftprocessverify"
TEST = APP + ".test"
CLASS = "org.locallore.app.ColdNavigationFreshTaskTest"
METHOD = "reopensConfirmedChildFromPrivateHintWithoutSavedTaskState"
KIND = "cold_navigation"
GUEST_ROOT = PureWindowsPath("D:/Dev/Experiments/LocalLore/2026-11-09-cold-navigation-ui-v1/avd-v1")
SOURCE_NAMES = frozenset(core.SOURCE_NAMES | {
    "owned_cold_navigation_ui_contract.py", "archive_ui_build.py", "android_instrumentation_evidence.py",
    "owned_cold_navigation_ui_client.py", "cold_navigation_ui_controller.py",
    "owned_cold_navigation_ui_owner.py", "cold_navigation_ui_activation.py", "cold_navigation_ui_closure.py",
    "cold_navigation_ui_operation.py", "cold_navigation_ui_preparation.py", "cold_navigation_ui_readiness.py",
})

_EVIDENCE = PureWindowsPath("D:/Dev/Experiments/LocalLore/2026-11-09-cold-navigation-artifact-v1")
_APKS = PureWindowsPath("D:/Worktrees/LocalLore-cold-navigation-device-test-v1/apps/android/app/build-input-process/outputs/apk")
_ARTIFACTS = {
    "build": (_EVIDENCE / "artifact-binding-v1.json", 1577,
              "32a20dcd3f8ca85d108d4cb7f73b3e3c8dd42b85669e82376f5a5820430ea67e"),
    "product_apk": (_APKS / "debug/app-debug.apk", 28012692,
                    "8381a3075d826c7e7a43c5dc68d3ebcbe17984497d9563b91906093f236b82bb"),
    "test_apk": (_APKS / "androidTest/debug/app-debug-androidTest.apk", 2274672,
                 "f5476a1abf889a8e8ff0bf5419e62d7634603b6049a0a5d6c4594daa92c88a7f"),
}
_AUDIT = (_EVIDENCE / "exact-pair-v1.log", 803,
          "b5dfdefa356cd45590869108073325319281a8208ed85b1ae16ff20f678e8507")
_SIGNER = "c260302d8114a7a79ea87eca56ce865e9203f6818d5fcf34fbcb41fb67dde4c8"


def _pin(entry):
    path, size, digest = entry
    return dict(path=str(path), bytes=size, sha256=digest)


def artifact_bindings():
    return {role: _pin(entry) for role, entry in _ARTIFACTS.items()}


def instrumentation_argv():
    return ["am", "instrument", "-w", "-r", "-e", "class", CLASS + "#" + METHOD,
            "-e", "cold_navigation_v1", "true", TEST + "/androidx.test.runner.AndroidJUnitRunner"]


def _require_artifacts(pins):
    core._need(core._same(pins, artifact_bindings()), "binding")


def _bound(pin):
    return files._bound(pin, cap=pin["bytes"])


def verify_artifacts(pins):
    """Verify the exact retained source and audit bindings, then read both APKs."""
    _require_artifacts(pins)
    audit_pin = _pin(_AUDIT)
    args = instrumentation_argv()[4:]
    try:
        build = env.decode_json(_bound(pins["build"]))
        expected_build = {
            "schema": "cold-navigation-host-artifacts-v1",
            "apks_from_commit": "04a8888b245c4c3db722ee0666814d0272b88c24",
            "apk_source_pr": "https://github.com/OptimumAF/LocalLore/pull/434",
            "audit_commit": "e760e5dee9849a16ca0276edb25851fa3c6533fd",
            "audit_pr": "https://github.com/OptimumAF/LocalLore/pull/436",
            "audit": audit_pin, "app": pins["product_apk"], "test": pins["test_apk"],
            "signer_sha256": _SIGNER, "instrumentation_args": args,
            "device_executed": 0, "operation_authority": False,
        }
        core._need(core._same(build, expected_build), "binding")
        audit = env.decode_json(_bound(audit_pin))
        expected_audit = {
            "status": "passed", "scope": "cold-navigation-apk-pair-v1",
            "package": APP, "test_package": TEST, "test_permissions": ["android.permission.REORDER_TASKS"],
            "certificate_sha256": _SIGNER, "instrumentation_args": args,
            "app": {key: pins["product_apk"][key] for key in ("bytes", "sha256")},
            "test": {key: pins["test_apk"][key] for key in ("bytes", "sha256")},
        }
        core._need(core._same(audit, expected_audit), "binding")
        for role in ("product_apk", "test_apk"):
            _bound(pins[role])
    except (OSError, ValueError, RuntimeError):
        raise core.TargetRefused("binding") from None


class _ColdNavigationContract(core._Contract):
    def _install_argv(self, path):
        return ["pm", "install", "-R", "-t", "--user", "0", path]

    def _instrumentation_argv(self, class_name, method):
        core._need((class_name, method) == (CLASS, METHOD), "command")
        return instrumentation_argv()

    def validate_admission(self, value):
        admission = super().validate_admission(value)
        _require_artifacts(admission["artifacts"])
        return admission

    def validate_operation(self, value, admission):
        operation = super().validate_operation(value, admission)
        argv = operation["argv"]
        core._need(argv[:1] != ["pidof"] and argv[:2] != ["am", "force-stop"], "command")
        return operation


PROFILE = _ColdNavigationContract(core.ContractProfile(
    PROTOCOL, "sdk-cold-navigation-ui-v1", "cold-navigation-ui-socket-proof-v1",
    GUEST_ROOT, SOURCE_NAMES, 20, "sdk-session-v20.json",
    "owned_cold_navigation_ui_owner.py", "owned-cold-navigation-ui-boot-claim-v1.json",
    ((KIND, CLASS, METHOD),), frozenset(_ARTIFACTS), (KIND,),
    APP=APP, TEST=TEST, MODEL_MATERIAL=False,
))

# The v4 owner, client and verifier consume the same module interface as the
# other closed profiles. They cannot select it from an admission record.
for _name in ("PORT", "REQUEST_KEYS", "WORKER_KEYS", "CLEANUP_KEYS",
              "TargetRefused", "_need", "_obj", "_int", "_path", "_process", "_same"):
    globals()[_name] = getattr(core, _name)
for _name in ("SDK_PROTOCOL", "PROOF_PROTOCOL", "CLIENT_VERSION", "SESSION_FILE",
              "OWNER_SCRIPT", "BOOT_CLAIM_FILE", "CLAIM_KINDS"):
    globals()[_name] = getattr(PROFILE.profile, _name)
for _name in (
    "binding", "_rows", "check_stop", "validate_admission", "validate_running",
    "validate_session", "validate_operation", "operation_digest", "validate_observation",
    "validate_guest_job", "validate_guest_observation", "validate_guest_prefix",
    "validate_proof", "validate_query_bundle", "validate_ready", "validate_claim",
    "validate_client_record", "source_bindings", "revalidate_inputs", "device_transport",
    "instrumentation_kind", "claim_record",
):
    globals()[_name] = getattr(PROFILE, _name)
del _name


def replay_instrumentation(operation, admission, returncode, stdout, stderr):
    """Replay the fixed method from a retained capture after client proof validation."""
    operation = PROFILE.validate_operation(operation, admission)
    PROFILE.instrumentation_kind(operation["argv"])
    core._need(type(returncode) is int and returncode == 0 and core._same(stderr, b""), "instrumentation")
    try:
        return evidence.validate_instrumentation(stdout, CLASS, [METHOD])
    except evidence.EvidenceRefused:
        raise core.TargetRefused("instrumentation") from None
