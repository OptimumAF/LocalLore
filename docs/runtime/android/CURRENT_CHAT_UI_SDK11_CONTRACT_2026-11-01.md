# SDK11 current-chat UI cohort — 2026-11-01

Refs #14 (M10.02), supporting #13 (M09.03/M09.05/M09.06). This is a developer
qualification profile, not an Android platform version or product feature.
Implementation is in review; Android execution and full task acceptance remain
open. See [actual host evidence](../../native/CURRENT_CHAT_UI_HARNESS_VERIFICATION_2026-11-01.md).

## Fixed authority and separation

SDK11 adds new leaves over the existing finite owner, transport, proof verifier
and shared storage mechanisms. It does not retag SDK10's six-method cohort or
change its source. The fixed authority is:

| Field | Value |
| --- | --- |
| Owner protocol | `owned-emulator-current-chat-ui-v1` |
| SDK / proof | `sdk-current-chat-ui-v1` / `current-chat-ui-socket-proof-v1` |
| Client / session | `11` / `sdk-session-v11.json` |
| Owner / boot claim | `owned_chat_ui_owner.py` / `owned-chat-ui-boot-claim-v1.json` |
| Product / test | `org.locallore.app` / `org.locallore.app.test` |
| Model material | `False` |
| Artifact roles | exactly `build`, `product_apk`, `test_apk` |

Only concrete `LiveOwnedChatUiTarget`, `_ChatUiTargetRuntime` and
`OwnedChatUiSdkCapture` classes select this authority. Fixed lazy build checks
precede owner construction/native work. There is no caller-selected module,
factory, selector, package or model operation. Generic shell, run-as, pidof,
force-stop and legacy-profile substitution remain refused.

Source bindings cover the shared core plus the new profile leaves, build,
controller, activation and instrumentation reader: 23 names. The helper must
itself match an admitted source binding. Activation fixes SOURCE_ROOT to
`D:/Dev/Projects/The Hero's Journey/LocalLore-control-review` and HELPER to its
`benchmarks/chat_ui_activation.py`. Actual module origins, clean physical root
and admitted content bindings are checked. No future Git head is embedded in
the helper that would create a self-reference cycle.

The prospective guest is
`D:/Dev/Experiments/LocalLore/2026-11-01-current-chat-ui-v1/avd-v1`; prospective
runtime is `D:/Dev/Experiments/LocalLore/2026-11-01-current-chat-ui-run-v1`.
Run controls are under the harness experiment's `run-controls-v1`. All remain
absent. Defining constants or publishing a build manifest grants no run authority.

## Eight literal one-shot claims

All classes are in `org.locallore.app.ui`. Order and full class/method identities
are fixed in both the profile and build guard:

| Claim | Class and method |
| --- | --- |
| `chat_ime_latest` | `ChatImeInsetsTest#injectedImeKeepsLatestAboveOcclusionWithoutDoublePaddingSystemBars` |
| `chat_ime_composer` | `ChatImeInsetsTest#doubleFontComposerKeepsSendReachableAndDraftScopedAcrossInjectedImeChanges` |
| `chat_status_history` | `ChatStatusAnnouncementTest#historyReaderKeepsItsAnchorWhileCurrentBusyAndOutcomeAnnouncementsStayAvailable` |
| `chat_status_draft` | `ChatStatusAnnouncementTest#unicodeDialogueAndScopeStaySafeWhileEllipsizedNoticeKeepsFullSemantics` |
| `chat_heading_selection` | `StoryHeadingScreenTest#selectedAuthoredTitlesStayInsideTheIntroWhileDemoAndUnresolvedControlsRemainExact` |
| `chat_heading_draft` | `StoryHeadingScreenTest#titleRefreshRetainsDialogueButStoryAndBranchChangesFenceDraftsAndRetainedEdits` |
| `chat_action_scope` | `QuickActionScopeScreenTest#retainedStoryAndBranchClicksStayQuietWhileFreshControlsPreserveTheUnsentDialogue` |
| `chat_action_availability` | `QuickActionScopeScreenTest#persistentDemoAndWorkflowFencesDoNotTurnTextUnavailabilityIntoAnActionBlock` |

Each claim is consumed once. The complete controller grammar is **Nboot +32
clients**, with contiguous original records. Extra boot observations do not
repeat a method. The fixed API35/x86_64 checks, per-role deadlines, combined
capture limits, installed package/UID/path/hash checks and first-uncertainty
abort remain. No retry or timeout expansion was introduced.

## Product evidence and build manifest

Product source is the B55 checkout at `8d66c24e`, whose executed source is
`fcf92fa3`; their exact delta is README plus the B55 verification document.
The new launcher is a separate branch based on PR #319. Its own Android source
is not substituted for the frozen product. The immutable pair is:

| Artifact | Bytes | SHA-256 |
| --- | ---: | --- |
| App | 28,012,688 | `a25ab00c458ed5f531935a5dcad17dd8d667fe9ed3e32059a33d77671f063591` |
| Instrumentation | 2,308,386 | `e6acd6ec10960f0861ce3588864ec74eb44a8b468b38a750f76cc96709cfc1a3` |

Common certificate SHA-256 is
`17ed497138b20dc1657d54039802305cfe0e3b782c73feaad20359c954707564`.
The guard replays source/raw maps and ZIPs, recorded Gradle/audit results,
50 XML suites/428 unique cases, lint, native chains and actual DEX definitions.
It preserves the absence of a historical supervised pipeline, inner raw AAPT
streams and historical executable-byte pins. Current Cargo alias observations
are explicitly distinguished from B55 historical metadata.

Generic source/control/APK reads require one link. Only explicit Cargo release
roles allow the two fixed release/deps cdylib pairs, requiring exactly two
links, ordinary D: ancestry, identical held file identity/content, and final
revalidation. Missing, foreign or third aliases refuse; admission cannot select
this exception.

`create_manifest()` returns data only. `verify_frozen_product(artifacts)` is an
artifact-only guard; `verify_current(admission)` revalidates the admission before
and after that guard. Root published only this host artifact manifest:

`D:/Dev/Experiments/LocalLore/2026-11-01-current-chat-ui-cohort-v1/chat-ui-build-v1.json`

It is 415,680 bytes, SHA-256
`c21cc05f6a687605ad7d3f8e1e66d90ff9e96c504844f7e53a6268e4b8ab1c6b`.
It is not a guest admission, authorization, prepare record or runtime input.

## Controller and activation boundaries

Controller APIs are `run(admission_binding, running_binding)` and
`verify_controller_result(result_binding, admission_binding, running_binding,
expected_caller)`. Distinct chat scopes retain the existing strict 15-field
result shape. Raw attempts are persisted before parsing; rc0 alone cannot pass
failed JUnit, missing claims, altered labels/deadlines, extra clients or installed
pair drift. Proofs must join the actual started caller.

Activation exposes `execute(input_binding)`, with exact input fields version,
scope `chat-ui-run-input-v1`, admission and helper. Private worker modes retain
the start barrier, actual self/parent/request identity and running-owner join.
Known caller termination is required before one stop-publication attempt.
An uncertain publication remains spent; cleanup cannot retry it.

Wait, observer close, capture close and terminal/runtime publication are attempted
independently. Unknown results remain sticky. UI completion is separate from
qualified owner result, all 15 exact cleanup booleans, source/input equality,
bound storage closure and one closed shared-ledger entry.

SDK11 additionally replays the **same** controller binding, admission, running
binding and actual caller after owner cleanup, then rechecks bindings before
final success. SDK10's globals are not rebound to achieve this. A controller
record changed during cleanup must refuse final qualification.

## Remaining authority and qualification

The only legacy behavior change is one exact supported closure protocol in
`receipt_avd_retirement.PROTOCOLS`. Metadata extraction is not a native process
query, image plan or deletion permission. Storage guard code and the two-root /
64GiB /40GiB preparing-live reservation rules remain unchanged. Follow
[shared storage policy](RECEIPT_AVD_STORAGE.md) and obtain applicable exact
authority before any preparation, boot or retirement.

All eight Android methods remain unrun. IME injection is not actual keyboard
behavior; semantics are not TalkBack speech; inert heading/action fixtures are
not native authoring or accepted mechanics. The product excludes sibling
PR #317's rollover fix and differs from the older pending SDK10 pair. Physical
phone/model, native/ARM64 execution, accessibility, lifecycle and full milestone
acceptance remain separate. No existing proposal or approval is expanded.
