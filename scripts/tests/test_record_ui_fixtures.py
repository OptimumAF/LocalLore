# Copyright 2026 LocalLore contributors. SPDX-License-Identifier: Apache-2.0
"""Original SDK7 fixture metadata; synthetic bytes never grant a real target."""
import contextlib
import copy
from pathlib import Path, PureWindowsPath
from types import SimpleNamespace
from unittest.mock import patch

from benchmarks import owned_target_contract as core
from scripts.tests import test_owned_target_contract as legacy
from scripts.tests import test_archive_ui_fixtures as previous_profile
from scripts.tests import test_archive_ui_build_fixtures as previous_builds
from scripts.tests import test_archive_ui_controller_fixtures as previous_controller

PROTOCOL = 'owned-emulator-record-ui-v1'
SDK_PROTOCOL = 'sdk-record-ui-v1'
PROOF_PROTOCOL = 'record-ui-socket-proof-v1'
SESSION_FILE = 'sdk-session-v7.json'
APP = 'org.locallore.app.archiveverify'
TEST = APP + '.test'
GUEST_ROOT = PureWindowsPath('D:/Dev/Experiments/LocalLore/2026-10-31-record-ui-v1/avd-v1')
SOURCE_NAMES = previous_profile.SOURCE_NAMES | {
    'owned_record_ui_contract.py', 'owned_record_ui_owner.py',
    'android_process_record_ui_client.py', 'android_process_record_ui_verification.py',
    'record_ui_build.py', 'record_ui_controller.py', 'android_instrumentation_evidence.py',
}
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
QUERY_METHODS = (
    'allFiveDefaultsUseQuery2WhileExplicitLegacyPlayerQueriesRemainVersion1',
    'everyCapturedNativePageDecodesWithoutSkippingRowsFlatteningScopeOrLeakingForbiddenText',
    'nativeUnseenCorrectionPreservesKnownObservationUntilAnActualRediscovery',
    'exactPrivateCorrectionMarkerHasNoEventOrNavigationAuthority',
    'scopedMessagesRetainOriginalScopeAndOrderedIdsWhileLegacyMessagesStayExplicitV1',
    'progressionRelationshipsAndObservedKnowledgeAcceptOnlyVersionedTypedSourcesAndPlayerSubjects',
    'versionedCursorAndPageFramesRefuseCrossVersionTypesAndFrozenContextDrift',
    'progressionSourceDrillUsesExactAncestorTupleAndCurrentLensAndRejectsWrongReturnedBranch',
    'nonCooperativeQuery2RepliesCannotReviveDismissedDisposedOrReplacedContexts',
    'controllerRefusesStalePageIdentityAndClearsPrivateFailuresWithoutDispatchingEvidence',
    'actualGatewayDecodesEveryOpaqueAuthoredNativePageUsingItsSnapshotBoundPlayer',
    'actualGatewayBindsOpaqueProfileItemsBeliefsPromisesAndEventWitnessesWithoutRewritingSpeakers',
    'explicitQuery1GatewayUsesOpaqueSnapshotIdentityAndRefusesAValidLiteralPlayerForgery',
    'missingOrFailedSnapshotBindingRefusesBeforeAnyInspectionBytesAreRequested',
    'inFlightReadRejectsObserverChangeReusedAttachmentHeadAdvanceAndClosure',
)
encoded = previous_builds.encoded
pin = previous_builds.pin


def admission():
    value = legacy.admission()
    value['protocol'] = PROTOCOL
    value['guest']['root'] = str(GUEST_ROOT)
    value['artifacts'] = {role: value['artifacts'][role] for role in ('build', 'product_apk', 'test_apk')}
    value['sources'] = sorted([legacy.pin(PureWindowsPath('D:/Synthetic/LocalLore/benchmarks') / name)
                               for name in SOURCE_NAMES], key=lambda row: row['path'])
    sources = {PureWindowsPath(row['path']).name: row for row in value['sources']}
    value['server']['sources'] = [copy.deepcopy(sources[PureWindowsPath(row['path']).name]) for row in value['server']['sources']]
    return value


def running(value=None):
    result = legacy.running(admission() if value is None else value)
    result['protocol'] = PROTOCOL
    return result


def session(value=None):
    value = admission() if value is None else value
    result = legacy.session(value)
    result.update(protocol=SDK_PROTOCOL, descriptor=running(value))
    return result


def proof(session_value, *, after=False):
    result = legacy.proof(session_value, after=after)
    result.update(protocol=PROOF_PROTOCOL, session=legacy.pin(PureWindowsPath(session_value['root']) / SESSION_FILE))
    return result


def query_bundle(session_value):
    result = legacy.query_bundle(session_value)
    result['protocol'] = PROOF_PROTOCOL
    return result


def instrument(triple):
    return ['am', 'instrument', '-w', '-r', '-e', 'class', triple[1] + '#' + triple[2],
            TEST + '/androidx.test.runner.AndroidJUnitRunner']


class BuildGraph(previous_builds.BuildGraph):
    """Real file/ZIP/DEX/XML guards; only current Git discovery is simulated.

    Scoped substitutions below affect OLD TEST-FIXTURE generators, never a
    production verdict. The eight frozen transcript cases remain; the exact
    fifteen Query2 methods/source and two suites extend 345/41 to 380/43.
    """
    def __init__(self):
        import sys
        with patch.object(previous_builds, 'f', sys.modules[__name__]):
            super().__init__()
        path = self.root / 'apps/android/app/src/test/java/org/locallore/app/Query2StoryRecordTest.kt'
        self.write(path, 'package org.locallore.app\nclass Query2StoryRecordTest {\n' +
                   ''.join('@Test fun ' + name + '() {}\n' for name in QUERY_METHODS) + '}\n')
        self.source_paths.append(path)
        self.report('TEST-org.locallore.app.Query2StoryRecordTest.xml',
                    [('org.locallore.app.Query2StoryRecordTest', name) for name in QUERY_METHODS])
        self.report('TEST-synthetic.RecordSupplement.xml', [('synthetic.RecordSupplement', 'case%d' % n) for n in range(20)])
        self.source_map = self.current_sources()
        self.write(self.public / 'sources-before-v1.json', encoded(self.source_map))
        self.write(self.public / 'sources-after-v1.json', encoded(self.source_map))
        self.request['sources'] = pin(self.public / 'sources-before-v1.json')
        self.publish()

    def publish(self, **kwargs):
        import sys
        with patch.object(previous_builds, 'f', sys.modules[__name__]):
            super().publish(**kwargs)
        self.manifest['scope'] = 'record-ui-build-v1'
        self.write(self.manifest_path, encoded(self.manifest))

    def admission(self):
        value = admission()
        value['artifacts'] = {'build': pin(self.manifest_path), **{role: pin(path) for role, path in self.apks.items()}}
        return value


class ControllerGraph(previous_controller.ControllerGraph):
    """Full fixed SDK7 simulation, NOT Android/native ownership qualification.

    Inherit only the reviewed fixture's exact synthetic-adb marker exception;
    all other source/runtime/build/APK/proof/claim/JUnit validators stay real.
    Actual OS/native/socket IO is simulated by its scoped IO mocks.
    """
    @contextlib.contextmanager
    def modules(self):
        import sys
        from benchmarks import record_ui_build as build
        from benchmarks import record_ui_controller as controller
        from benchmarks import owned_record_ui_contract as contract
        from benchmarks import owned_record_ui_owner as owner
        with contextlib.ExitStack() as stack:
            for name, value in (('build', build), ('controller', controller), ('contract', contract), ('owner', owner),
                                ('f', sys.modules[__name__]),
                                ('builds', SimpleNamespace(BuildGraph=BuildGraph, pin=pin, encoded=encoded))):
                stack.enter_context(patch.object(previous_controller, name, value))
            yield

    def __init__(self, **kwargs):
        with self.modules():
            super().__init__(**kwargs)

    def run(self):
        from benchmarks import record_ui_controller as controller
        return controller.run(self.admission, self.running)

    def verify(self, caller=None):
        from benchmarks import record_ui_controller as controller
        return controller.verify_controller_result(pin(self.output / 'controller-result-v1.json'),
            self.admission, self.running, self.caller if caller is None else caller)

    def prove(self, live, path, session, context, sock, anchor, after=False):
        from benchmarks import receipt_avd_environment as env
        value = proof(session, after=after)
        value.update(context=copy.deepcopy(context), anchor=copy.deepcopy(anchor),
                     session=env.binding(Path(session['root']) / SESSION_FILE))
        queries = path.with_name(path.stem + '-queries-v1.json')
        env.create_json(queries, query_bundle(session)); value['queries'] = env.binding(queries)
        env.create_json(path, value); self.proofs.append((context['index'], context['phase']))
        return env.binding(path)

    @contextlib.contextmanager
    def inputs(self):
        with self.modules(), super().inputs():
            yield
