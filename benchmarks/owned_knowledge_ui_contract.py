"""Fixed SDK16 Knowledge UI authority; importing performs no IO.

Copyright 2026 LocalLore contributors. SPDX-License-Identifier: Apache-2.0
"""
from pathlib import PureWindowsPath

from benchmarks import owned_target_contract as core

PROTOCOL = 'owned-emulator-knowledge-ui-v1'
SDK_PROTOCOL = 'sdk-knowledge-ui-v1'
PROOF_PROTOCOL = 'knowledge-ui-socket-proof-v1'
CLIENT_VERSION = 16
SESSION_FILE = 'sdk-session-v16.json'
OWNER_SCRIPT = 'owned_knowledge_ui_owner.py'
BOOT_CLAIM_FILE = 'owned-knowledge-ui-boot-claim-v1.json'
APP = 'org.locallore.app'
TEST = APP + '.test'
MODEL_MATERIAL = False
GUEST_ROOT = PureWindowsPath('D:/Dev/Experiments/LocalLore/2026-11-02-knowledge-ui-v1/avd-v1')
INSTRUMENTATIONS = (
    ('knowledge_labels', 'org.locallore.app.ui.KnowledgeRecordFilterScreenTest',
     'exactlyFiveKnowledgeFacetsExposeLiteralLabelsSelectionAndFortyEightDpTargetsOnlyInKnowledge'),
    ('knowledge_replaced', 'org.locallore.app.ui.KnowledgeRecordFilterScreenTest',
     'retainedRealFacetAndCloseActionsCannotRetargetDifferentOrEqualDistinctSuppliedViews'),
    ('knowledge_remount', 'org.locallore.app.ui.KnowledgeRecordFilterScreenTest',
     'removedAndRemountedSameStateCannotReviveOldFacetOrCloseButFreshActionsStillWork'),
    ('knowledge_text', 'org.locallore.app.ui.KnowledgeRecordFilterScreenTest',
     'doubledFontKeepsEveryFacetAndUnchangedOriginSourceAndCloseReachableInTheActualDialog'),
)
CLAIM_KINDS = tuple(row[0] for row in INSTRUMENTATIONS)
ARTIFACT_KEYS = frozenset(('build', 'product_apk', 'test_apk'))
SOURCE_NAMES = frozenset(core.SOURCE_NAMES | core.CURRENT_STORAGE_SOURCES | {
    'owned_knowledge_ui_contract.py', 'owned_knowledge_ui_owner.py',
    'android_process_knowledge_ui_client.py', 'android_process_knowledge_ui_verification.py',
    'knowledge_ui_profile_build.py', 'knowledge_ui_controller.py', 'knowledge_ui_activation.py',
    'knowledge_ui_build.py', 'knowledge_ui_build_baseline.json',
    'library_ui_build.py', 'library_ui_build_baseline.json', 'android_instrumentation_evidence.py',
})


class _KnowledgeUiContract(core._Contract):
    def validate_operation(self, value, admission):
        core._obj(value, ('argv', 'stdin'), 'command')
        argv = value['argv']
        core._need(type(argv) is list and argv[:1] != ['pidof'] and
                   argv[:2] != ['am', 'force-stop'], 'command')
        return super().validate_operation(value, admission)


_API = _KnowledgeUiContract(core.ContractProfile(
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
