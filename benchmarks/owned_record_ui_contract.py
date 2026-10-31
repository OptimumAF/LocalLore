"""Fixed model-free record UI authority; no import I/O or legacy retagging.

Copyright 2026 LocalLore contributors. SPDX-License-Identifier: Apache-2.0
"""
from pathlib import PureWindowsPath
from benchmarks import owned_target_contract as core
from benchmarks import owned_ui_contract as legacy_ui

PROTOCOL = 'owned-emulator-record-ui-v1'
SDK_PROTOCOL = 'sdk-record-ui-v1'
PROOF_PROTOCOL = 'record-ui-socket-proof-v1'
CLIENT_VERSION = 7
SESSION_FILE = 'sdk-session-v7.json'
OWNER_SCRIPT = 'owned_record_ui_owner.py'
BOOT_CLAIM_FILE = 'owned-record-ui-boot-claim-v1.json'
APP = 'org.locallore.app.archiveverify'
TEST = APP + '.test'
MODEL_MATERIAL = False
GUEST_ROOT = PureWindowsPath('D:/Dev/Experiments/LocalLore/2026-10-31-record-ui-v1/avd-v1')
INSTRUMENTATIONS = (
    ('record_native_pages', 'org.locallore.app.StoryRecordInstrumentedTest', 'playerPaginationAndGiftHistoryAreReadOnlyAndSurviveStrictReopen'),
    ('record_native_knowledge', 'org.locallore.app.StoryRecordInstrumentedTest', 'actualClaimsBeliefsAndKnownTruthKeepDistinctOriginsAndObserverGrants'),
    ('record_native_wire', 'org.locallore.app.StoryRecordInstrumentedTest', 'androidJsonDecoderRejectsMalformedAndPrivatePagesWithoutEchoingPayloads'),
    ('source_native_drill', 'org.locallore.app.EventSourceInstrumentedTest', 'crossSceneSourcesNavigateToExactAcceptedEventsWithoutNewTurnsAndReopenStrictly'),
    ('source_native_isolation', 'org.locallore.app.EventSourceInstrumentedTest', 'playerSourcesCannotGrantNpcFutureBranchOrOtherStoryEvents'),
    ('source_native_wire', 'org.locallore.app.EventSourceInstrumentedTest', 'decoderRequiresValidTypedEvidenceAndEventMetadataAndNeverLinksWithheldEvidence'),
    ('record_screen', 'org.locallore.app.StoryRecordScreenTest', 'collectedRecordPagesSearchOriginsAndGiftRefreshUseTheAuthoritativeSavedHead'),
    ('source_screen', 'org.locallore.app.EventSourceScreenTest', 'sourceButtonsRestoreSearchedSecondPageAndFenceLinksAcrossSavedStories'),
    ('record_corrected_opaque', 'org.locallore.app.Query2StoryRecordScreenTest', 'correctedOpaquePlayerRecordKeepsObservationsAndCorrectionMarkersSeparateAcrossReopen'),
    ('record_scope_stale', 'org.locallore.app.Query2StoryRecordScreenTest', 'opaquePlayerSourceDrillUsesOriginalScopeAndRejectsStaleStoryCallbacks'),
)
CLAIM_KINDS = tuple(row[0] for row in INSTRUMENTATIONS)
ARTIFACT_KEYS = frozenset(('build', 'product_apk', 'test_apk'))
SOURCE_NAMES = frozenset(legacy_ui.SOURCE_NAMES | {
    'owned_record_ui_contract.py', 'owned_record_ui_owner.py',
    'android_process_record_ui_client.py', 'android_process_record_ui_verification.py',
    'record_ui_build.py', 'record_ui_controller.py',
})

# Only this source module chooses the profile. Admission data cannot select it.
_API = core._Contract(core.ContractProfile(
    PROTOCOL, SDK_PROTOCOL, PROOF_PROTOCOL, GUEST_ROOT, SOURCE_NAMES,
    CLIENT_VERSION, SESSION_FILE, OWNER_SCRIPT, BOOT_CLAIM_FILE,
    INSTRUMENTATIONS, ARTIFACT_KEYS, CLAIM_KINDS,
    APP=APP, TEST=TEST, MODEL_MATERIAL=MODEL_MATERIAL,
))

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
