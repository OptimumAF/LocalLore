"""Fixed Story Record large-text authority over the guarded owned-target contract.

Copyright 2026 LocalLore contributors. SPDX-License-Identifier: Apache-2.0
"""
from pathlib import PureWindowsPath

from benchmarks import archive_ui_build as files
from benchmarks import owned_target_contract as core

PROTOCOL = 'owned-emulator-record-large-text-ui-v1'
SDK_PROTOCOL = 'sdk-record-large-text-ui-v1'
PROOF_PROTOCOL = 'record-large-text-ui-socket-proof-v1'
CLIENT_VERSION = 19
SESSION_FILE = 'sdk-session-v19.json'
OWNER_SCRIPT = 'owned_record_large_text_ui_owner.py'
BOOT_CLAIM_FILE = 'owned-record-large-text-ui-boot-claim-v1.json'
APP = 'org.locallore.app.archiveverify'
TEST = APP + '.test'
MODEL_MATERIAL = False
GUEST_ROOT = PureWindowsPath('D:/Dev/Experiments/LocalLore/2026-11-09-record-large-text-ui-v1/avd-v1')
INSTRUMENTATIONS = ((
    'record_large_text',
    'org.locallore.app.StoryRecordLargeTextTest',
    'narrowRecordReflowsAtDoubleTextSizeAndKeepsActionsReachable',
),)
CLAIM_KINDS = ('record_large_text',)

# B124 built and independently audited these exact bytes from PR #401's code.
_ARTIFACT_ROOT = PureWindowsPath('D:/Dev/Experiments/LocalLore/2026-11-09-record-large-text-apks-v1')
_ARTIFACTS = (
    ('build', 'artifact-attestation-v1.json', 1514,
     '23dd50c9f29bbc03340b14b2d217b9dbc499c01d3bf9ea4c886d42a93a9447a6'),
    ('product_apk', 'app-debug.apk', 28012684,
     'be73e0b4eda34ed3da3173f8c2147802d17b769b638f8cf512f99bd612e8fe12'),
    ('test_apk', 'app-debug-androidTest.apk', 2269096,
     '9544b1a9b8d47bba1c100fd776f676570402de91624238cfccb3531159d5ad15'),
)
ARTIFACT_KEYS = frozenset(role for role, *_ in _ARTIFACTS)
SOURCE_NAMES = frozenset(core.SOURCE_NAMES | core.CURRENT_STORAGE_SOURCES | {
    'owned_record_large_text_ui_contract.py',
    'owned_record_large_text_ui_owner.py',
    'android_process_record_large_text_ui_client.py',
    'android_process_record_large_text_ui_verification.py',
    'archive_ui_build.py',
    'record_large_text_ui_controller.py',
    'android_instrumentation_evidence.py',
})


def artifact_bindings():
    """Return a new binding map for the audited pair and its build record."""
    return {role: dict(path=str(_ARTIFACT_ROOT / name), bytes=size, sha256=sha)
            for role, name, size, sha in _ARTIFACTS}


def _require_artifacts(pins):
    core._obj(pins, ARTIFACT_KEYS, 'binding')
    core._need(core._same(pins, artifact_bindings()), 'binding')


def verify_artifacts(pins):
    """Check frozen files with bounded reads. This performs no target action."""
    _require_artifacts(pins)
    try:
        # Read only fresh fixed pins, regardless of the order of the supplied map.
        for pin in artifact_bindings().values():
            files._bound(pin, cap=pin['bytes'])
    except Exception:
        raise core.TargetRefused('binding') from None


class _RecordLargeTextUiContract(core._Contract):
    def validate_admission(self, value):
        admission = super().validate_admission(value)
        _require_artifacts(admission['artifacts'])
        return admission

    def validate_operation(self, value, admission):
        operation = super().validate_operation(value, admission)
        argv = operation['argv']
        core._need(argv[:1] != ['pidof'] and argv[:2] != ['am', 'force-stop'], 'command')
        return operation


_API = _RecordLargeTextUiContract(core.ContractProfile(
    PROTOCOL, SDK_PROTOCOL, PROOF_PROTOCOL, GUEST_ROOT, SOURCE_NAMES,
    CLIENT_VERSION, SESSION_FILE, OWNER_SCRIPT, BOOT_CLAIM_FILE,
    INSTRUMENTATIONS, ARTIFACT_KEYS, CLAIM_KINDS,
    APP=APP, TEST=TEST, MODEL_MATERIAL=MODEL_MATERIAL,
))


def verify_current(admission):
    """Bind the recorded APK pair before the guarded owner or live lease proceeds."""
    verify_artifacts(validate_admission(admission)['artifacts'])


for _name in (
    'PORT', 'ADMISSION_KEYS', 'GUEST_KEYS', 'RUNNING_KEYS', 'SESSION_KEYS',
    'CONTEXT_KEYS', 'PROOF_KEYS', 'QUERY_BUNDLE_KEYS', 'QUERY_KEYS',
    'BRACKET_KEYS', 'READY_KEYS', 'JOB_KEYS', 'REQUEST_KEYS', 'WORKER_KEYS',
    'CLEANUP_KEYS', 'CLIENT_KEYS', 'TargetRefused',
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
