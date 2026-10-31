# Fixed inspector Android qualification contract

B38. Refs #14 M10.02, #13 M09.06/supporting M09.04.
Exact base PR30412857ac7f563c5a9c61092ae8dcabacc6cd4d4cd.

This packet adds a distinct fixed model-free record-UI profile. Original SDK4/5/6
profiles and archive-UI rosters/readers remain byte-unchanged. New fixed adapters
reuse current shared owner, binary-wire, proof-verification and storage mechanisms.
Avoid a generic dispatch refactor across previously frozen protocols; source code,
not admission data, selects each concrete owner/client/contract/verifier. No copied
AVD preparation/storage implementation or alternate ledger is introduced.

Protocol owned-emulator-record-ui-v1, sdk-record-ui-v1, record-ui-socket-proof-v1;
client7, sdk-session-v7.json, owned_record_ui_owner.py,
owned-record-ui-boot-claim-v1.json. Build record-ui-build-v1; controller scopes
record-ui-controller-v1, record-ui-controller-request-v1, record-ui-setup-v1,
record-ui-installed-v1. Existing key/sidecar shapes and 1200s controller ceiling
remain. Existing binary transfer, actual start/pass/end JUnit, per-call ownership,
canonical proof and exact installed package/hash/UID before/after checks remain.
No test retry, model operation, arbitrary selector, run-as, privileged observer
or source-session fallback. Archiveverify product/test packages and exactly
build/product_apk/test_apk roles. Source set covers all imported shared modules.

Fixed future guest D:/Dev/Experiments/LocalLore/2026-10-31-record-ui-v1/avd-v1.
No preparation or boot authority comes from this file/profile. Current shared
ledger already has two unretired roots; fresh admission is blocked. Preserve all
roots/evidence, current designated starter-native guard and other emulator.
Retirement and any new boot require applicable exact-scope user authority.

Build admission requires current clean exact head/source/tool bytes, original
public offline archive runner captures and fresh critical Gradle task states,
380 unique passing JVM cases/43 coherent XML suites, exact existing Transcript8
and frozen Query2 FIRST15 policy sets, no lint Error/Fatal, actual annotated
public concrete JUnit selectors in test DEX and absent product DEX. Original
345/41 legacy build requirement remains unchanged; no retagging old evidence.

Native producer must create genuinely materialized opaque-player corrected
history and export production archive format. Android imports exact synthetic
asset query2-corrected-opaque-v1.llore plus expected metadata
query2-corrected-opaque-v1.json through existing production NativeArchive. No new
JNI correction grant, fake row or manually changed domain flag. Imported branch
selection derives native catalog scope mapping. Browsing proves observed/truth/
belief separation, original tuple/current-player source drill, privacy/no-nav
correction marker, canonical/turn conservation, stale/closed/disposed fences and
ordinary owner reopen. Imported fixture preparation is not app authoring or
OS-death evidence. Native stdout generation is bounded256KiB; output/hash/schema
contract coordinated with independent Android/native writers before execution.

## Fixed ordered instrumentation roster

- `record_native_pages`: `org.locallore.app.StoryRecordInstrumentedTest#playerPaginationAndGiftHistoryAreReadOnlyAndSurviveStrictReopen`
- `record_native_knowledge`: `org.locallore.app.StoryRecordInstrumentedTest#actualClaimsBeliefsAndKnownTruthKeepDistinctOriginsAndObserverGrants`
- `record_native_wire`: `org.locallore.app.StoryRecordInstrumentedTest#androidJsonDecoderRejectsMalformedAndPrivatePagesWithoutEchoingPayloads`
- `source_native_drill`: `org.locallore.app.EventSourceInstrumentedTest#crossSceneSourcesNavigateToExactAcceptedEventsWithoutNewTurnsAndReopenStrictly`
- `source_native_isolation`: `org.locallore.app.EventSourceInstrumentedTest#playerSourcesCannotGrantNpcFutureBranchOrOtherStoryEvents`
- `source_native_wire`: `org.locallore.app.EventSourceInstrumentedTest#decoderRequiresValidTypedEvidenceAndEventMetadataAndNeverLinksWithheldEvidence`
- `record_screen`: `org.locallore.app.StoryRecordScreenTest#collectedRecordPagesSearchOriginsAndGiftRefreshUseTheAuthoritativeSavedHead`
- `source_screen`: `org.locallore.app.EventSourceScreenTest#sourceButtonsRestoreSearchedSecondPageAndFenceLinksAcrossSavedStories`
- `record_corrected_opaque`: `org.locallore.app.Query2StoryRecordScreenTest#correctedOpaquePlayerRecordKeepsObservationsAndCorrectionMarkersSeparateAcrossReopen`
- `record_scope_stale`: `org.locallore.app.Query2StoryRecordScreenTest#opaquePlayerSourceDrillUsesOriginalScopeAndRejectsStaleStoryCallbacks`

## Frozen Query2 FIRST policy methods

- `allFiveDefaultsUseQuery2WhileExplicitLegacyPlayerQueriesRemainVersion1`
- `everyCapturedNativePageDecodesWithoutSkippingRowsFlatteningScopeOrLeakingForbiddenText`
- `nativeUnseenCorrectionPreservesKnownObservationUntilAnActualRediscovery`
- `exactPrivateCorrectionMarkerHasNoEventOrNavigationAuthority`
- `scopedMessagesRetainOriginalScopeAndOrderedIdsWhileLegacyMessagesStayExplicitV1`
- `progressionRelationshipsAndObservedKnowledgeAcceptOnlyVersionedTypedSourcesAndPlayerSubjects`
- `versionedCursorAndPageFramesRefuseCrossVersionTypesAndFrozenContextDrift`
- `progressionSourceDrillUsesExactAncestorTupleAndCurrentLensAndRejectsWrongReturnedBranch`
- `nonCooperativeQuery2RepliesCannotReviveDismissedDisposedOrReplacedContexts`
- `controllerRefusesStalePageIdentityAndClearsPrivateFailuresWithoutDispatchingEvidence`
- `actualGatewayDecodesEveryOpaqueAuthoredNativePageUsingItsSnapshotBoundPlayer`
- `actualGatewayBindsOpaqueProfileItemsBeliefsPromisesAndEventWitnessesWithoutRewritingSpeakers`
- `explicitQuery1GatewayUsesOpaqueSnapshotIdentityAndRefusesAValidLiteralPlayerForgery`
- `missingOrFailedSnapshotBindingRefusesBeforeAnyInspectionBytesAreRequested`
- `inFlightReadRejectsObserverChangeReusedAttachmentHeadAdvanceAndClosure`
