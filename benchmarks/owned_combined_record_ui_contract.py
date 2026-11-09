"""Fixed model-free combined Story Record authority over the guarded v4 wire.

Copyright 2026 LocalLore contributors. SPDX-License-Identifier: Apache-2.0
"""
from pathlib import PureWindowsPath

from benchmarks import combined_record_ui_binding as artifact_policy
from benchmarks import owned_target_contract as core

PROTOCOL = "owned-emulator-combined-record-ui-v1"
RUN_SCOPE = PROTOCOL
SDK_PROTOCOL = "sdk-combined-record-ui-v1"
PROOF_PROTOCOL = "combined-record-ui-socket-proof-v1"
CLIENT_VERSION = 21
SESSION_FILE = "sdk-session-v21.json"
OWNER_SCRIPT = "owned_combined_record_ui_owner.py"
BOOT_CLAIM_FILE = "owned-combined-record-ui-boot-claim-v1.json"
GUEST_ROOT = PureWindowsPath("D:/Dev/Experiments/LocalLore/2026-11-09-combined-record-ui-guest-v1/avd-v1")
APP = artifact_policy.APP
TEST = artifact_policy.TEST
MODEL_MATERIAL = False
INSTRUMENTATIONS = artifact_policy.INSTRUMENTATIONS
CLAIM_KINDS = tuple(kind for kind, _, _ in INSTRUMENTATIONS)
ARTIFACT_KEYS = frozenset(("build", "product_apk", "test_apk"))
SOURCE_NAMES = frozenset(core.SOURCE_NAMES | {
    "owned_combined_record_ui_contract.py", OWNER_SCRIPT, "owned_combined_record_ui_client.py",
    "combined_record_ui_binding.py", "combined_record_ui_controller.py",
    "combined_record_ui_handoff.py", "combined_record_ui_closure.py",
    "combined_record_ui_preparation.py", "combined_record_ui_activation.py",
    "combined_record_ui_operation.py",
    "combined_record_ui_readiness.py",
    "archive_ui_build.py", "android_instrumentation_evidence.py",
})


class _CombinedRecordUiContract(core._Contract):
    def validate_admission(self, value):
        admission = super().validate_admission(value)
        core._need(core._same(admission["artifacts"], artifact_policy.artifact_bindings()), "binding")
        return admission

    def validate_operation(self, value, admission):
        operation = super().validate_operation(value, admission)
        argv = operation["argv"]
        core._need(argv[:1] != ["pidof"] and argv[:2] != ["am", "force-stop"], "capability")
        return operation


_API = _CombinedRecordUiContract(core.ContractProfile(
    PROTOCOL, SDK_PROTOCOL, PROOF_PROTOCOL, GUEST_ROOT, SOURCE_NAMES,
    CLIENT_VERSION, SESSION_FILE, OWNER_SCRIPT, BOOT_CLAIM_FILE,
    INSTRUMENTATIONS, ARTIFACT_KEYS, CLAIM_KINDS,
    APP=APP, TEST=TEST, MODEL_MATERIAL=MODEL_MATERIAL,
))

for _name in (
    "PORT", "ADMISSION_KEYS", "GUEST_KEYS", "RUNNING_KEYS", "SESSION_KEYS",
    "CONTEXT_KEYS", "PROOF_KEYS", "QUERY_BUNDLE_KEYS", "QUERY_KEYS", "BRACKET_KEYS",
    "READY_KEYS", "JOB_KEYS", "REQUEST_KEYS", "WORKER_KEYS", "CLEANUP_KEYS", "CLIENT_KEYS",
    "TargetRefused", "_need", "_obj", "_int", "_same", "_path", "_process",
):
    globals()[_name] = getattr(core, _name)

for _name in (
    "binding", "_sources", "validate_admission", "_clock", "validate_running", "check_stop",
    "validate_session", "_relative", "validate_operation", "operation_digest", "_rows",
    "validate_observation", "_guest_observation", "validate_guest_observation",
    "validate_guest_prefix", "device_status", "device_transport", "validate_proof", "_brackets",
    "validate_query_bundle", "validate_guest_job", "validate_ready", "validate_claim",
    "validate_client_record", "source_bindings", "revalidate_inputs", "instrumentation_kind",
    "claim_record",
):
    globals()[_name] = getattr(_API, _name)
del _name
