# Fixed Android player-setup phase — v1

M09.02 with M09.03/M09.06 interaction coverage. This freezes the invocation and
evidence contract for [player-name setup](STORY_PLAYER_SETUP_V1.md); it does not
claim any execution. Host/JVM passes and compiled Android methods cannot stand
in for actual Compose/JNI results or physical/model qualification.

The fixed `benchmarks/android_process_verification.py player-setup` phase accepts
the existing bound build, live owner proposal, running descriptor and server
inputs. It has no class, method, device-profile or deadline selector. All three
isolated app/test/controller packages must be absent before any install. A guest
used for native, creation, chooser, broad, archive or external-controller work
cannot be reused for this phase.

Existing source/APK/tool/owner/user0/server guards remain. SDK session850 seconds,
verification owner900 seconds, per-class client180 seconds and262144-byte raw
class cap are unchanged. Readiness is not a boot proof. Unknown cleanup, source
drift, incomplete capture or any failed client permanently refuses dispatch;
there is no reinstall, data-clear, generic selector or retry path.

The exact source-declaration roster is:

```text
StoryPlayerSetupWireTest (3)
  configuredPreviewRequiresExactHashesNameAndClosedFields
  configuredCommandsRemainDistinctFromLegacyNamedCreation
  nativeGatewayNeverFallsBackOnConfiguredPreviewFailure
StoryPlayerSetupDialogTest (3)
  editingNameRequiresExplicitReviewBeforeCreate
  retainedNameReviewAndConfirmActionsKeepTheirOriginalRequest
  invalidNamesAndBusyStatesCannotReviewOrCreate
StoryPlayerSetupMainActivityTest (2)
  customNameReviewCancelPreservesTheLibraryAndDraft
  configuredCreationAndOrdinaryReopenRetainTheNativePlayerName
```

Each class runs once, in this order, through the pinned isolated
AndroidJUnitRunner `exec-out am instrument --user 0 -w -r -e class` command.
Original runner frames must contain exactly the expected methods, no skips or
extra methods, and one successful terminal frame. The closed `player_setup-v1.json`
has version1, phase `player-setup`, exactly3 results/8 methods, complete clean
client count and `external_controller_case_executed:false`.

Both worker and parent validate the source-pinned roster, every original raw
frame and its matching SDK-client copy. Current execution additionally requires
every contiguous client/observer pair's measured-v2 metadata and raw hash.
Historical readers retaining v1 support do not remove that current-run gate.
A passed label, rebound foreign raw frame, missing pair or partial result is
insufficient. This phase cannot qualify native10, creation19, chooser7, broad89
or the external controller; their fixed rosters remain unchanged.

The real MainActivity/JNI methods exercise editable initial names, explicit
review/Create, Cancel preserving the selected library and play draft, and
ordinary Activity reopen retaining native player state. They do not kill the OS
process, load a real model or prove joined native drain. Guest shutdown requires
known terminal verification capture/cleanup and an exact proposal-bound stop;
final service observation occurs only after the requested closures. No server
lifecycle action or unrelated emulator stop is part of this protocol.
