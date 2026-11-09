"""Fixed host contract for the isolated story-deletion UI capture.

Importing this module defines the contract without creating a guest or running
any command. A live owner needs separately admitted source and operation scope.
Copyright 2026 LocalLore contributors. SPDX-License-Identifier: Apache-2.0
"""
import copy
from pathlib import Path, PureWindowsPath
import sys

from benchmarks import android_process_client_v4 as wire
from benchmarks import android_process_verification_v4 as verification
from benchmarks import cross_owner_deletion_ui_binding as artifacts
from benchmarks import cross_owner_deletion_ui_capture as capture
from benchmarks import owned_target_contract as core
from benchmarks import owned_target_owner as mechanisms
from benchmarks import receipt_avd_environment as env
from benchmarks.owned_target_contract import (
    CLEANUP_KEYS, PORT, REQUEST_KEYS, WORKER_KEYS, TargetRefused, _int, _need, _obj,
    _path, _process, _same,
)

PROTOCOL = "owned-emulator-cross-owner-deletion-ui-v1"
SDK_PROTOCOL = "sdk-cross-owner-deletion-ui-v1"
PROOF_PROTOCOL = "cross-owner-deletion-ui-socket-proof-v1"
CLIENT_VERSION = 24
SESSION_FILE = "sdk-session-v24.json"
OWNER_SCRIPT = "owned_cross_owner_deletion_ui.py"
BOOT_CLAIM_FILE = "owned-cross-owner-deletion-ui-boot-claim-v1.json"
GUEST_ROOT = PureWindowsPath("D:/Dev/Experiments/LocalLore/2026-11-09-cross-owner-deletion-owned-guest-v1/avd-v1")

APP = artifacts.APP
TEST = artifacts.TEST
MODEL_MATERIAL = False
INSTRUMENTATIONS = artifacts.INSTRUMENTATIONS
CLAIM_KINDS = tuple(kind for kind, _, _ in INSTRUMENTATIONS)
ARTIFACT_KEYS = frozenset(artifacts.artifact_bindings())
SOURCE_NAMES = frozenset(core.SOURCE_NAMES | core.CURRENT_STORAGE_SOURCES | {
    OWNER_SCRIPT, "cross_owner_deletion_ui_binding.py", "cross_owner_deletion_ui_capture.py",
    "cross_owner_deletion_ui_replay.py", "cross_owner_deletion_ui_controller.py",
    "cross_owner_deletion_ui_boot.py", "saved_library_status_binding.py",
    "archive_ui_build.py", "android_instrumentation_evidence.py",
})
_AUDIT_SOURCES = ("audit_apk.py", "audit_physical_model_apk.py")


class _CrossOwnerDeletionContract(core._Contract):
    def _sources(self, value):
        count = len(self.profile.SOURCE_NAMES) + len(_AUDIT_SOURCES)
        _need(type(value) is list and len(value) in (count, count + 1), "source")
        benchmark_pins = []
        script_paths = []
        for pin in value:
            self.binding(pin)
            path = PureWindowsPath(pin["path"])
            if path.parent.name == "benchmarks":
                benchmark_pins.append(pin)
            else:
                script_paths.append(path)
        paths = [pin["path"] for pin in value]
        _need(paths == sorted(set(paths)), "source")
        super()._sources(benchmark_pins)
        scripts = PureWindowsPath(benchmark_pins[0]["path"]).parent.parent / "scripts"
        _need(script_paths == [scripts / name for name in _AUDIT_SOURCES], "source")

    def source_bindings(self):
        pins = super().source_bindings()
        scripts = Path(pins[0]["path"]).parent.parent / "scripts"
        pins.extend(env.binding(scripts / name) for name in _AUDIT_SOURCES)
        return sorted(pins, key=lambda pin: pin["path"])

    def _install_argv(self, path):
        return ["pm", "install", "-R", "-t", "--user", "0", path]

    def validate_admission(self, value):
        admission = super().validate_admission(value)
        _need(_same(admission["artifacts"], artifacts.artifact_bindings()), "binding")
        return admission

    def validate_operation(self, value, admission):
        operation = super().validate_operation(value, admission)
        argv = operation["argv"]
        _need(argv[:1] != ["pidof"] and argv[:2] != ["am", "force-stop"], "capability")
        return operation


_API = _CrossOwnerDeletionContract(core.ContractProfile(
    PROTOCOL, SDK_PROTOCOL, PROOF_PROTOCOL, GUEST_ROOT, SOURCE_NAMES,
    CLIENT_VERSION, SESSION_FILE, OWNER_SCRIPT, BOOT_CLAIM_FILE,
    INSTRUMENTATIONS, ARTIFACT_KEYS, CLAIM_KINDS,
    APP=APP, TEST=TEST, MODEL_MATERIAL=MODEL_MATERIAL,
))

# Fixed facade for the shared verifier's contract interface.
for _name in (
    "binding", "validate_admission", "validate_running", "validate_session",
    "validate_operation", "operation_digest", "validate_client_record",
    "validate_proof", "validate_query_bundle", "validate_claim", "claim_record",
    "instrumentation_kind", "source_bindings", "revalidate_inputs", "check_stop", "_rows",
    "validate_observation", "validate_guest_observation", "validate_guest_prefix",
    "device_transport", "validate_guest_job", "validate_ready",
):
    globals()[_name] = getattr(_API, _name)
del _name


_CONTRACT = sys.modules[__name__]
REPLAY = verification._Verifier(_CONTRACT)


class LiveOwnedCrossOwnerDeletionTarget(mechanisms._LiveOwnedTarget):
    """Observe one already owned target after checking the exact APK pair."""

    def __init__(self, admission_binding, running_binding):
        mechanisms._need(type(self) is LiveOwnedCrossOwnerDeletionTarget, "owner_type")
        admission_binding, running_binding = copy.deepcopy((admission_binding, running_binding))
        admission = validate_admission(REPLAY._json(admission_binding))
        artifacts.verify_artifacts(admission["artifacts"])
        super().__init__(admission_binding, running_binding)

    @property
    def _contract(self):
        mechanisms._need(type(self) is LiveOwnedCrossOwnerDeletionTarget, "owner_type")
        return _CONTRACT

    @property
    def _verification(self):
        mechanisms._need(type(self) is LiveOwnedCrossOwnerDeletionTarget, "owner_type")
        return REPLAY


class OwnedCrossOwnerDeletionSdkCapture(wire._OwnedTargetSdkCapture):
    """Capture commands only through the fixed cross-owner deletion observer."""

    def __init__(self, directory, seconds, lease):
        wire._need(type(self) is OwnedCrossOwnerDeletionSdkCapture, "client_type")
        super().__init__(directory, seconds, lease)

    @property
    def _contract(self):
        wire._need(type(self) is OwnedCrossOwnerDeletionSdkCapture, "client_type")
        return _CONTRACT

    @property
    def _verification(self):
        wire._need(type(self) is OwnedCrossOwnerDeletionSdkCapture, "client_type")
        return REPLAY

    @property
    def _expected_lease_class(self):
        return LiveOwnedCrossOwnerDeletionTarget


def verify_capture(admission_binding, running_binding, session_binding, expected_caller):
    return capture.verify_capture(sys.modules[__name__], admission_binding, running_binding,
                                  session_binding, expected_caller)
