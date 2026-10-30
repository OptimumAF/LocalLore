"""Original synthetic SDK6 metadata/bytes; never a live target or build grant."""
import copy
from pathlib import PureWindowsPath

from benchmarks import owned_target_contract as core
from scripts.tests import test_owned_target_contract as legacy

PROTOCOL = 'owned-emulator-archive-ui-v1'
SDK_PROTOCOL = 'sdk-archive-ui-v1'
PROOF_PROTOCOL = 'archive-ui-socket-proof-v1'
APP = 'org.locallore.app.archiveverify'
TEST = APP + '.test'
GUEST_ROOT = PureWindowsPath('D:/Dev/Experiments/LocalLore/2026-10-30-archive-ui-v1/avd-v1')
SOURCE_NAMES = core.SOURCE_NAMES | {
    'owned_ui_contract.py', 'owned_ui_owner.py', 'android_process_client_v6.py',
    'android_process_verification_v6.py', 'archive_ui_build.py',
    'archive_ui_controller.py', 'android_instrumentation_evidence.py',
}
INSTRUMENTATIONS = (
    ('transcript_history', 'org.locallore.app.TranscriptFollowScreenTest', 'readingHistoryKeepsPositionUntilLatestAndPreservesTheUnsentDialogue'),
    ('transcript_tail', 'org.locallore.app.TranscriptFollowScreenTest', 'seeingOnlyTheHeadOfALongTailDoesNotAuthorizeFollowingAnAppend'),
    ('transcript_composer', 'org.locallore.app.TranscriptFollowScreenTest', 'readingTheComposerPastTheTailFollowsTheNewReplyWithoutSubmittingTheDraft'),
    ('transcript_branch', 'org.locallore.app.TranscriptFollowScreenTest', 'retainedLatestCallbackCannotNavigateAnotherBranchWithReusedMessageIds'),
    ('theme_roundtrip', 'org.locallore.app.SystemThemeTest', 'systemDayNightRoundTripKeepsScopedDialogueDraftStateAndUserCallbacks'),
    ('theme_busy', 'org.locallore.app.SystemThemeTest', 'nightDayChangesDoNotSubmitOrCancelBusyDraftAndExplicitCancelStillFiresOnce'),
    ('layout_cancel', 'org.locallore.app.ShellLayoutTest', 'pendingResponseCancelControlInvokesItsCallback'),
    ('layout_accessibility', 'org.locallore.app.ShellLayoutTest', 'smallViewportAndDoubleFontScaleKeepControlsReachable'),
    ('playinput_scope', 'org.locallore.app.PlayInputScreenTest', 'exampleOnlyEditsAndAcceptedOriginalDraftsSurviveHeadsButNotStorySwitches'),
    ('playinput_validation', 'org.locallore.app.PlayInputScreenTest', 'validationRejectionDuplicatePendingCancelAndDisposalKeepDraftsAndCanonSafe'),
)

def admission():
    value = legacy.admission()
    value['protocol'] = PROTOCOL
    value['guest']['root'] = str(GUEST_ROOT)
    value['artifacts'] = {k:value['artifacts'][k] for k in ('build', 'product_apk', 'test_apk')}
    value['sources'] = sorted([legacy.pin(PureWindowsPath('D:/Synthetic/LocalLore/benchmarks')/name)
                               for name in SOURCE_NAMES], key=lambda p:p['path'])
    by_name = {PureWindowsPath(p['path']).name:p for p in value['sources']}
    value['server']['sources'] = [copy.deepcopy(by_name[PureWindowsPath(p['path']).name])
                                  for p in value['server']['sources']]
    return value

def running(value=None):
    value = admission() if value is None else value
    result = legacy.running(value)
    result['protocol'] = PROTOCOL
    return result

def session(value=None):
    value = admission() if value is None else value
    result = legacy.session(value)
    result['protocol'] = SDK_PROTOCOL
    result['descriptor'] = running(value)
    return result

def proof(session_value, *, after=False):
    result = legacy.proof(session_value, after=after)
    result['protocol'] = PROOF_PROTOCOL
    result['session'] = legacy.pin(PureWindowsPath(session_value['root'])/'sdk-session-v6.json')
    return result

def query_bundle(session_value):
    result = legacy.query_bundle(session_value)
    result['protocol'] = PROOF_PROTOCOL
    return result

def instrument(triple):
    _, cls, method = triple
    return ['am', 'instrument', '-w', '-r', '-e', 'class', cls+'#'+method,
            TEST+'/androidx.test.runner.AndroidJUnitRunner']
