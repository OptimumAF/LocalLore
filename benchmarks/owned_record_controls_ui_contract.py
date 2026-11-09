"""Fixed SDK14 record-controls UI authority; importing performs no IO.

Copyright 2026 LocalLore contributors. SPDX-License-Identifier: Apache-2.0
"""
from pathlib import PureWindowsPath

from benchmarks import owned_target_contract as core

PROTOCOL = 'owned-emulator-record-controls-ui-v1'
SDK_PROTOCOL = 'sdk-record-controls-ui-v1'
PROOF_PROTOCOL = 'record-controls-ui-socket-proof-v1'
CLIENT_VERSION = 14
SESSION_FILE = 'sdk-session-v14.json'
OWNER_SCRIPT = 'owned_record_controls_ui_owner.py'
BOOT_CLAIM_FILE = 'owned-record-controls-ui-boot-claim-v1.json'
APP = 'org.locallore.app'
TEST = APP + '.test'
MODEL_MATERIAL = False
GUEST_ROOT = PureWindowsPath('D:/Dev/Experiments/LocalLore/2026-11-01-record-controls-ui-v1/avd-v1')
INSTRUMENTATIONS = (
    ('chat_ime_latest', 'org.locallore.app.ui.ChatImeInsetsTest',
     'injectedImeKeepsLatestAboveOcclusionWithoutDoublePaddingSystemBars'),
    ('chat_ime_composer', 'org.locallore.app.ui.ChatImeInsetsTest',
     'doubleFontComposerKeepsSendReachableAndDraftScopedAcrossInjectedImeChanges'),
    ('chat_status_history', 'org.locallore.app.ui.ChatStatusAnnouncementTest',
     'historyReaderKeepsItsAnchorWhileCurrentBusyAndOutcomeAnnouncementsStayAvailable'),
    ('chat_status_draft', 'org.locallore.app.ui.ChatStatusAnnouncementTest',
     'unicodeDialogueAndScopeStaySafeWhileEllipsizedNoticeKeepsFullSemantics'),
    ('chat_heading_selection', 'org.locallore.app.ui.StoryHeadingScreenTest',
     'selectedAuthoredTitlesStayInsideTheIntroWhileDemoAndUnresolvedControlsRemainExact'),
    ('chat_heading_draft', 'org.locallore.app.ui.StoryHeadingScreenTest',
     'titleRefreshRetainsDialogueButStoryAndBranchChangesFenceDraftsAndRetainedEdits'),
    ('chat_action_scope', 'org.locallore.app.ui.QuickActionScopeScreenTest',
     'retainedStoryAndBranchClicksStayQuietWhileFreshControlsPreserveTheUnsentDialogue'),
    ('chat_action_availability', 'org.locallore.app.ui.QuickActionScopeScreenTest',
     'persistentDemoAndWorkflowFencesDoNotTurnTextUnavailabilityIntoAnActionBlock'),
    ('inventory_entries', 'org.locallore.app.ui.PlayerInventoryScreenTest',
     'savedRowsKnownEmptyAndUnavailableStayDistinctWhileDemoKeepsItsOriginalPotionRow'),
    ('inventory_scope', 'org.locallore.app.ui.PlayerInventoryScreenTest',
     'scopeChangesFenceRetainedOpenAndCloseWhileAcceptedRefreshesKeepTheUnsentDialogue'),
    ('inventory_accessibility', 'org.locallore.app.ui.PlayerInventoryScreenTest',
     'doubledFontKeepsLongExactIdentifiersAllQuantitiesAndCloseReachableWithoutGameActions'),
    ('profile_fields', 'org.locallore.app.ui.PlayerSelfProfileScreenTest',
     'acceptedFieldsEmptyUnavailableAndNarrativeApplicabilityStaySeparateFromDemo'),
    ('profile_scope', 'org.locallore.app.ui.PlayerSelfProfileScreenTest',
     'retainedInspectorCallbacksRespectScopesWorkflowClosureAndAcceptedRefreshWithoutSendingDraft'),
    ('profile_accessibility', 'org.locallore.app.ui.PlayerSelfProfileScreenTest',
     'doubledFontKeepsFullUnicodeCollectionsAndCloseReachableWithoutCanonicalCallbacks'),
    ('record_scope_story', 'org.locallore.app.ui.StoryRecordActionScopeScreenTest',
     'retainedSearchNextAndCloseCannotRetargetAnotherStoryOrBranchAndFreshControlsStillWork'),
    ('record_scope_reopen', 'org.locallore.app.ui.StoryRecordActionScopeScreenTest',
     'equalValuedReopenAndLaterPagesRejectOldButtonsWithoutResettingTheCurrentDialogue'),
    ('record_scope_detail', 'org.locallore.app.ui.StoryRecordActionScopeScreenTest',
     'retainedListAndEventRetryBackAndSourceActionsCannotAffectFreshDetailsOrReopenedRecords'),
    ('promise_status_browse', 'org.locallore.app.ui.PromiseStatusScreenTest',
     'statusPagingAndEvidenceBackKeepTheNativePresetWhileTextSearchReturnsToAll'),
    ('promise_status_scope', 'org.locallore.app.ui.PromiseStatusScreenTest',
     'retainedPresetCannotRetargetLaterStatusEqualReopenOrAnotherStory'),
)
CLAIM_KINDS = tuple(row[0] for row in INSTRUMENTATIONS)
ARTIFACT_KEYS = frozenset(('build', 'product_apk', 'test_apk'))
SOURCE_NAMES = frozenset(core.SOURCE_NAMES | {
    'owned_record_controls_ui_contract.py', 'owned_record_controls_ui_owner.py',
    'android_process_record_controls_ui_client.py', 'android_process_record_controls_ui_verification.py',
    'record_controls_ui_build.py', 'record_controls_ui_controller.py', 'record_controls_ui_activation.py',
    'record_controls_ui_build_baseline.json', 'android_instrumentation_evidence.py',
})


class _RecordControlsContract(core._Contract):
    def validate_operation(self, value, admission):
        core._obj(value, ('argv', 'stdin'), 'command')
        argv = value['argv']
        core._need(type(argv) is list and argv[:1] != ['pidof'] and
                   argv[:2] != ['am', 'force-stop'], 'command')
        return super().validate_operation(value, admission)


_API = _RecordControlsContract(core.ContractProfile(
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
