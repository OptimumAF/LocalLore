"""Fixed model-free archive UI authority; no import I/O or legacy retagging.

Copyright 2026 LocalLore contributors. SPDX-License-Identifier: Apache-2.0
"""
from pathlib import PureWindowsPath
from benchmarks import owned_target_contract as core

PROTOCOL = 'owned-emulator-archive-ui-v1'
SDK_PROTOCOL = 'sdk-archive-ui-v1'
PROOF_PROTOCOL = 'archive-ui-socket-proof-v1'
CLIENT_VERSION = 6
SESSION_FILE = 'sdk-session-v6.json'
OWNER_SCRIPT = 'owned_ui_owner.py'
BOOT_CLAIM_FILE = 'owned-ui-boot-claim-v1.json'
APP = 'org.locallore.app.archiveverify'
TEST = APP + '.test'
MODEL_MATERIAL = False
GUEST_ROOT = PureWindowsPath('D:/Dev/Experiments/LocalLore/2026-10-30-archive-ui-v1/avd-v1')
INSTRUMENTATIONS = (
    ('transcript_history', 'org.locallore.app.TranscriptFollowScreenTest',
     'readingHistoryKeepsPositionUntilLatestAndPreservesTheUnsentDialogue'),
    ('transcript_tail', 'org.locallore.app.TranscriptFollowScreenTest',
     'seeingOnlyTheHeadOfALongTailDoesNotAuthorizeFollowingAnAppend'),
    ('transcript_composer', 'org.locallore.app.TranscriptFollowScreenTest',
     'readingTheComposerPastTheTailFollowsTheNewReplyWithoutSubmittingTheDraft'),
    ('transcript_branch', 'org.locallore.app.TranscriptFollowScreenTest',
     'retainedLatestCallbackCannotNavigateAnotherBranchWithReusedMessageIds'),
    ('theme_roundtrip', 'org.locallore.app.SystemThemeTest',
     'systemDayNightRoundTripKeepsScopedDialogueDraftStateAndUserCallbacks'),
    ('theme_busy', 'org.locallore.app.SystemThemeTest',
     'nightDayChangesDoNotSubmitOrCancelBusyDraftAndExplicitCancelStillFiresOnce'),
    ('layout_cancel', 'org.locallore.app.ShellLayoutTest',
     'pendingResponseCancelControlInvokesItsCallback'),
    ('layout_accessibility', 'org.locallore.app.ShellLayoutTest',
     'smallViewportAndDoubleFontScaleKeepControlsReachable'),
    ('playinput_scope', 'org.locallore.app.PlayInputScreenTest',
     'exampleOnlyEditsAndAcceptedOriginalDraftsSurviveHeadsButNotStorySwitches'),
    ('playinput_validation', 'org.locallore.app.PlayInputScreenTest',
     'validationRejectionDuplicatePendingCancelAndDisposalKeepDraftsAndCanonSafe'),
)
CLAIM_KINDS = tuple(row[0] for row in INSTRUMENTATIONS)
ARTIFACT_KEYS = frozenset(('build', 'product_apk', 'test_apk'))
SOURCE_NAMES = frozenset(core.SOURCE_NAMES | {
    'owned_ui_contract.py', 'owned_ui_owner.py',
    'android_process_client_v6.py', 'android_process_verification_v6.py',
    'archive_ui_build.py', 'archive_ui_controller.py',
    'android_instrumentation_evidence.py',
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
