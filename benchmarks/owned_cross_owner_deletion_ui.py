"""Fixed host contract for the isolated story-deletion UI capture.

Importing this module defines the contract without creating a guest or running
any command. A live owner needs separately admitted source and operation scope.
Copyright 2026 LocalLore contributors. SPDX-License-Identifier: Apache-2.0
"""
from pathlib import Path, PureWindowsPath
import sys

from benchmarks import cross_owner_deletion_ui_binding as artifacts
from benchmarks import cross_owner_deletion_ui_capture as capture
from benchmarks import owned_target_contract as core
from benchmarks import receipt_avd_environment as env
from benchmarks.owned_target_contract import _int, _need, _path, _same

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
    "cross_owner_deletion_ui_replay.py", "saved_library_status_binding.py",
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
    "validate_proof", "validate_query_bundle", "validate_claim",
    "instrumentation_kind", "source_bindings", "revalidate_inputs",
):
    globals()[_name] = getattr(_API, _name)
del _name


def verify_capture(admission_binding, running_binding, session_binding, expected_caller):
    return capture.verify_capture(sys.modules[__name__], admission_binding, running_binding,
                                  session_binding, expected_caller)
