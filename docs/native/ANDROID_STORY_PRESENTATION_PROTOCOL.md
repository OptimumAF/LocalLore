# Fixed Android story-presentation phase — v1

M09.02, supporting M09.03/M09.06. This freezes the qualification protocol for
initial tone and literal narration phrase boundaries. It does not claim a run.

The fixed `benchmarks/android_process_verification.py story-presentation` phase
requires the existing bound build, live owner proposal, running descriptor and
server inputs. There is no arbitrary class/method/profile/deadline selector.
The three isolated packages must be absent in a distinct fresh owned guest.
Previously used native, creation, chooser, player-setup or broad guests cannot
be adopted. Existing source/APK/user0/tool/owner/server guards remain.

SDK session850 seconds, verification owner900 seconds, per-class180 seconds and
262144-byte raw cap stay unchanged. Readiness alone is not boot proof. Failed
clients, unknown cleanup, source drift or incomplete capture refuse success;
there is no reinstall, data-clear or retry path.

Exact source-declaration roster:

```text
StoryPresentationWireTest (3)
  presentationPreviewRequiresClosedBoundedLiteralSettings
  presentedCreationPreservesLegacyWireAndProbeSemantics
  nativePresentationGatewayRefusesMalformedOrForeignResults
StoryPresentationDialogTest (3)
  presentationEditsRequireExplicitReviewBeforeCreate
  retainedPresentationActionsCannotBorrowAReplacementReview
  invalidPhraseDraftsAndBusyStatesDisableReviewAndCreate
StoryPresentationMainActivityTest (2)
  presentationReviewCancelPreservesTheSelectedLibraryAndDraft
  presentedCreationRetainsToneAndPhrasesOnNativeReopen
```

Each class runs once in this order using the pinned isolated AndroidJUnitRunner
`exec-out am instrument --user 0 -w -r -e class` command. Original runner frames
must contain exactly the source-pinned methods, with no skips/extra methods and
one successful terminal frame. Closed `story_presentation-v1.json` has version1,
phase `story-presentation`,3 results/8 methods, complete clean client count and
`external_controller_case_executed:false`.

Worker and parent validate every raw frame, matching SDK raw copy and source
roster. Current execution requires complete contiguous measured-v2 metadata/raw
pairs; a passed label or rebound player-setup frame is insufficient. Existing
phase rosters and historical-reader support do not relax this current gate.

Real MainActivity/JNI cases exercise explicit presentation review/Create,
Cancel preserving the selected library/play draft, and native read-back across
fresh Host/ordinary Activity reopen. Wire/dialog methods cover malformed or
foreign metadata, literal settings, immutable retained consent and invalid/busy
states. These scripted checks do not prove model quality, OS process death,
joined native drain, semantic-topic filtering, physical/ARM64 or full journeys.
Known terminal capture/cleanup precedes an exact proposal-bound owned stop;
final existing-server observation occurs after requested closures. No server
lifecycle operation or unrelated-emulator stop is part of this protocol.
