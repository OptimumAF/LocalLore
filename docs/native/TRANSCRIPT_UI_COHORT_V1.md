# Transcript navigation UI cohort V1

Refs #13 (M09.03/M09.06), #14 (M10.02). This is a host implementation awaiting
Android execution and owner acceptance. It changes no gameplay authority,
canonical events, inference interface, model dependency or app package.

## Why a separate profile

PR #317 fixes following a rolling forty-message transcript and supplies two new
Compose tests. Its frozen ordinary app/test APK pair cannot truthfully be
retagged as the earlier archive UI profile (ten tests under another package) or
SDK9's three-APK external process controller. SDK10 selects exactly four existing
transcript-navigation tests and the two rollover tests against that ordinary
pair. Existing profiles and their frozen evidence remain unchanged.

The launcher is based on PR #315 at
`bb461ea227e77e4925c805e09bc2a0c74b0a1c6b`. The separately frozen product is PR
#317 at `78f254bb50ca0478541f0107ccfbcb16afd40d72`. These are distinct identities;
neither a launcher commit nor a host test constitutes product acceptance.

## Fixed authority and interfaces

`benchmarks/owned_transcript_ui_contract.py` defines the complete profile:

| Field | Fixed value |
| --- | --- |
| Protocol | `owned-emulator-transcript-ui-v1` |
| SDK / proof | `sdk-transcript-ui-v1` / `transcript-ui-socket-proof-v1` |
| Client / session | `10` / `sdk-session-v10.json` |
| Owner | `owned_transcript_ui_owner.py` |
| App / tests | `org.locallore.app` / `org.locallore.app.test` |
| Artifact roles | `build`, `product_apk`, `test_apk` only |
| Model material | `False` |
| Future guest | `D:/Dev/Experiments/LocalLore/2026-11-01-transcript-navigation-ui-v1/avd-v1` |

The future guest path is a source restriction, not an existing guest or a boot
grant. No run proposal, storage reservation or real admission was created for
this cohort. Fresh applicable approval, current shared-ledger admission and
guarded preparation remain prerequisites. The older pending run proposal does
not authorize this cohort.

The profile reuses the current contract/runtime, SDK capture and closed verifier
implementations. Its leaf denies unused `pidof` and `am force-stop` commands.
It adds no general shell, caller-selected package, model transfer, fallback
profile or transport authority. The retirement executor gains only this exact
protocol whitelist member; its existing proof and cleanup requirements remain.

`transcript_ui_build.create_manifest()` has no caller-selected inputs.
`verify_frozen_product(artifacts)` rechecks the fixed original files and returns
`manifest.apks[role]` with exactly `binding`, `package`, `certificate_sha256`.
`verify_current(admission)` additionally validates the SDK10 admission before
and after artifact verification. Importing these modules performs no I/O.

The data-only build guard reads the original phased build logs, 48 JUnit XML
reports/420 passing JVM cases, original failing/green regression reports,
packaging/audit records, APKs, DEX definitions and preserved tracked-source ZIP.
It verifies six real public instance JUnit methods in the test APK, absent from
the product APK, rather than accepting strings naming them. It compares current
source pins before/after, ZIP canonical identity and critical raw source bytes.
The reviewed pure DEX decoder functions must match the launcher helpers even
though unrelated audit-module content differs between the two commits.

This does **not** manufacture a historical supervised build pipeline, historical
full raw source map or Android runtime evidence. Those absences are explicit
manifest fields. Only fixed read-only Git queries and ordinary file reads are
used; no SDK, signing tool, old helper execution or guest discovery is needed.

## Exact one-time test roster

All methods use `androidx.test.runner.AndroidJUnitRunner`. Order is fixed;
failure or uncertainty stops the cohort without repeating a spent claim.

| Claim | Class | Method |
| --- | --- | --- |
| `transcript_history` | `org.locallore.app.TranscriptFollowScreenTest` | `readingHistoryKeepsPositionUntilLatestAndPreservesTheUnsentDialogue` |
| `transcript_tail` | same | `seeingOnlyTheHeadOfALongTailDoesNotAuthorizeFollowingAnAppend` |
| `transcript_composer` | same | `readingTheComposerPastTheTailFollowsTheNewReplyWithoutSubmittingTheDraft` |
| `transcript_branch` | same | `retainedLatestCallbackCannotNavigateAnotherBranchWithReusedMessageIds` |
| `transcript_rollover_follow` | `org.locallore.app.ui.TranscriptRolloverUiTest` | `readerBelowFortyRowTailSeesRolledReplyWithoutScrollingOrSendingDraft` |
| `transcript_rollover_history` | same | `historyReaderKeepsSurvivingRowUntilLatestAndKeepsOriginalDraft` |

The controller verifies boot/API35/x86_64/emulator/user0, initial package
absence, exact transferred and installed APK hashes, distinct UIDs and stable
installed identities. Each method needs original bounded terminal bytes,
qualified SDK/proof records and a complete passing JUnit result. A full cohort
has `Nboot + 30` clients (31 for one boot poll). Controller/boot/method limits
are 1200/120/90 seconds; owner limits remain 1700/1730 seconds. Transfer/install
commands retain their fixed 120-second limit and bounded captures.

`cmd package list packages` uses a substring filter in
[Android 15's package shell](https://android.googlesource.com/platform/frameworks/base/+/refs/heads/android15-release/services/core/java/com/android/server/pm/PackageManagerShellCommand.java).
Thus querying the app may return both packages, but querying its `.test` package
cannot return the app alone as evidence of absence. The controller enforces the
filter as well as the known-package roster.

Closed replay checks exact command labels, role-specific positive integer
deadlines, individual and combined raw capture bounds, canonical paths, complete
client order, current source/proof bindings, observer closure and unchanged
inputs. A return code of zero alone cannot qualify a method or cleanup.

## Execution gate

Use the shared ledger and current guarded preparation/owner paths described in
`docs/runtime/android/RECEIPT_AVD_STORAGE.md`; do not invoke SDK tools directly
or create a substitute registry. The controller's CLI requires both an existing
admission and running binding, each with its exact SHA-256. That CLI is not a
preparation or permission mechanism. Until the concrete run is approved and
actually executed, all six Android tests remain unrun. Phone, real-model,
process-restoration and release qualification are separate gates.
