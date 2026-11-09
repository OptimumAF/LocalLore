"""Fixed SDK17 Diagnostic UI authority; importing performs no IO.

Copyright 2026 LocalLore contributors. SPDX-License-Identifier: Apache-2.0
"""
from pathlib import PureWindowsPath

from benchmarks import owned_target_contract as core

PROTOCOL = 'owned-emulator-diagnostic-ui-v1'
SDK_PROTOCOL = 'sdk-diagnostic-ui-v1'
PROOF_PROTOCOL = 'diagnostic-ui-socket-proof-v1'
CLIENT_VERSION = 17
SESSION_FILE = 'sdk-session-v17.json'
OWNER_SCRIPT = 'owned_diagnostic_ui_owner.py'
BOOT_CLAIM_FILE = 'owned-diagnostic-ui-boot-claim-v1.json'
APP = 'org.locallore.app'
TEST = APP + '.test'
MODEL_MATERIAL = False
CERTIFICATE_SHA256 = '17ed497138b20dc1657d54039802305cfe0e3b782c73feaad20359c954707564'
GUEST_ROOT = PureWindowsPath('D:/Dev/Experiments/LocalLore/2026-11-03-diagnostic-ui-v1/avd-v1')
INSTRUMENTATIONS = (
    ('diagnostic_1', 'org.locallore.app.DiagnosticsIntegrationTest',
     'actualNativeOutcomesAreSanitizedAndClearingCannotChangeCanon'),
    ('diagnostic_2', 'org.locallore.app.DiagnosticsIntegrationTest',
     'reviewedSnapshotAndPendingConsentSurviveActivityRecreation'),
    ('diagnostic_3', 'org.locallore.app.DiagnosticsIntegrationTest',
     'revokingPickerAndLateResultDoesNotOpenDestination'),
    ('diagnostic_4', 'org.locallore.app.DiagnosticsIntegrationTest',
     'cancelAndMalformedGenerationProduceOnlyFixedDiagnosticCategories'),
    ('diagnostic_5', 'org.locallore.app.DiagnosticsIntegrationTest',
     'retiredReviewCannotClearOrCloseTheReplacementNativePreview'),
    ('diagnostic_6', 'org.locallore.app.DiagnosticsIntegrationTest',
     'staleScopedExportCannotBorrowTheCurrentReviewAcrossRecreation'),
)
CLAIM_KINDS = tuple(row[0] for row in INSTRUMENTATIONS)
ARTIFACT_KEYS = frozenset(('build', 'product_apk', 'test_apk'))
SOURCE_NAMES = frozenset(core.SOURCE_NAMES | core.CURRENT_STORAGE_SOURCES | {
    'owned_diagnostic_ui_contract.py', 'owned_diagnostic_ui_owner.py',
    'android_process_diagnostic_ui_client.py', 'android_process_diagnostic_ui_verification.py',
    'diagnostic_ui_profile_build.py', 'diagnostic_ui_controller.py', 'diagnostic_ui_activation.py',
    'diagnostic_ui_build.py', 'diagnostic_ui_build_baseline.json',
    'archive_ui_build.py', 'android_instrumentation_evidence.py',
})


class _DiagnosticUiContract(core._Contract):
    def revalidate_inputs(self, admission):
        # Scripts live outside the shared same-parent benchmark source grammar.
        # Fixed checker bytes/origins are additional guards, never another profile.
        from benchmarks.diagnostic_ui_profile_build import revalidate_checker
        revalidate_checker()
        result = super().revalidate_inputs(admission)
        revalidate_checker()
        return result

    def validate_operation(self, value, admission):
        core._obj(value, ('argv', 'stdin'), 'command')
        argv = value['argv']
        core._need(type(argv) is list and argv[:1] != ['pidof'] and
                   argv[:2] != ['am', 'force-stop'], 'command')
        return super().validate_operation(value, admission)


_API = _DiagnosticUiContract(core.ContractProfile(
    PROTOCOL, SDK_PROTOCOL, PROOF_PROTOCOL, GUEST_ROOT, SOURCE_NAMES,
    CLIENT_VERSION, SESSION_FILE, OWNER_SCRIPT, BOOT_CLAIM_FILE,
    INSTRUMENTATIONS, ARTIFACT_KEYS, CLAIM_KINDS,
    APP=APP, TEST=TEST, MODEL_MATERIAL=MODEL_MATERIAL,
))

for _name in (
    'PORT', 'ADMISSION_KEYS', 'GUEST_KEYS', 'RUNNING_KEYS', 'SESSION_KEYS',
    'CONTEXT_KEYS', 'PROOF_KEYS', 'QUERY_BUNDLE_KEYS', 'QUERY_KEYS',
    'BRACKET_KEYS', 'READY_KEYS', 'JOB_KEYS', 'REQUEST_KEYS', 'WORKER_KEYS',
    'CLEANUP_KEYS', 'CLIENT_KEYS', 'TargetRefused', '_need', '_obj', '_int', '_same', '_path', '_process',
):
    globals()[_name] = getattr(core, _name)

for _name in (
    'binding', '_sources', 'validate_admission', '_clock', 'validate_running',
    'check_stop', 'validate_session', '_relative', 'validate_operation',
    'operation_digest', '_rows', 'validate_observation', '_guest_observation',
    'validate_guest_observation', 'validate_guest_prefix', 'device_status',
    'device_transport', 'validate_proof', '_brackets', 'validate_query_bundle',
    'validate_guest_job', 'validate_ready', 'validate_claim', 'validate_client_record',
    'source_bindings', 'revalidate_inputs', 'instrumentation_kind', 'claim_record',
):
    globals()[_name] = getattr(_API, _name)
del _name
