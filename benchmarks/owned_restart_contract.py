"""Fixed separately admitted restart profile; no import I/O or legacy retagging.

Copyright 2026 LocalLore contributors. SPDX-License-Identifier: Apache-2.0
"""
from pathlib import PureWindowsPath
from benchmarks import owned_target_contract as core

PROTOCOL = 'owned-emulator-restart-target-v1'
SDK_PROTOCOL = 'sdk-owned-restart-v1'
PROOF_PROTOCOL = 'owned-restart-socket-proof-v1'
CLIENT_VERSION = 5
SESSION_FILE = 'sdk-session-v5.json'
OWNER_SCRIPT = 'owned_restart_owner.py'
BOOT_CLAIM_FILE = 'owned-restart-boot-claim-v1.json'
GUEST_ROOT = PureWindowsPath('D:/Dev/Experiments/LocalLore/2026-10-29-restart-after-metadata-v1/avd-v1')
RESTART_CLASS = 'org.locallore.app.OriginalAuthorRestartInstrumentedTest'
RESTART_METHOD = 'recordsOriginalAuthorAfterExternalRestartWithoutInference'
CLASS, METHODS = core.CLASS, core.METHODS
INSTRUMENTATIONS = core.INSTRUMENTATIONS + (('restart', RESTART_CLASS, RESTART_METHOD),)
CLAIM_KINDS = ('import', 'author', 'restart')
ARTIFACT_KEYS = core.ARTIFACT_KEYS | {'process_probe', 'process_probe_source'}
SOURCE_NAMES = frozenset(core.SOURCE_NAMES | {
    'owned_restart_contract.py', 'owned_restart_owner.py',
    'android_process_client_v5.py', 'android_process_verification_v5.py',
    'original_author_restart_controller.py', 'original_author_model_proof.py',
    'original_author_diagnostic.py', 'original_author_restart_proof.py',
    'android_instrumentation_evidence.py',
})

# Immutable mechanism configuration selected only by this fixed code module.
# An admission/JSON tag cannot supply a module, implementation or verifier.
_API = core._Contract(core.ContractProfile(
    PROTOCOL, SDK_PROTOCOL, PROOF_PROTOCOL, GUEST_ROOT, SOURCE_NAMES,
    CLIENT_VERSION, SESSION_FILE, OWNER_SCRIPT, BOOT_CLAIM_FILE,
    INSTRUMENTATIONS, frozenset(ARTIFACT_KEYS), CLAIM_KINDS,
))

# Shared primitives/record keys do not select an authority or start anything.
for _name in (
    'PORT', 'APP', 'TEST', 'MODEL_BYTES', 'MODEL_SHA256', 'ADMISSION_KEYS',
    'GUEST_KEYS', 'RUNNING_KEYS', 'SESSION_KEYS', 'CONTEXT_KEYS', 'PROOF_KEYS',
    'QUERY_BUNDLE_KEYS', 'QUERY_KEYS', 'BRACKET_KEYS', 'READY_KEYS', 'JOB_KEYS',
    'REQUEST_KEYS', 'WORKER_KEYS', 'CLEANUP_KEYS', 'CLIENT_KEYS', 'TargetRefused',
    '_need', '_obj', '_int', '_same', '_path', '_process',
):
    globals()[_name] = getattr(core, _name)

for _name in (
    'binding', '_sources', 'validate_admission', '_clock', 'validate_running',
    'check_stop', 'validate_session', '_relative', 'validate_operation',
    'operation_digest', '_rows', 'validate_observation', '_guest_observation',
    'validate_guest_observation', 'validate_guest_prefix', 'device_status',
    'device_transport', 'validate_proof', '_brackets', 'validate_query_bundle',
    'validate_guest_job', 'validate_ready', 'validate_claim',
    'validate_client_record', 'source_bindings', 'revalidate_inputs',
    'instrumentation_kind', 'claim_record',
):
    globals()[_name] = getattr(_API, _name)
del _name
