# Android native free-text recovery checks

Refs #9 (M05.04 partial, M05.05 supporting).

All six independently authored `NativeTextRecoveryTest` methods passed on the
selected second Android 15 / API 35 x86_64 emulator with 4096-byte pages. They
exercise the rendered Compose Action/Dialogue composer through the actual
`ShellViewModel`, `DurableGateway`, production `NativeWorkspaceTransport`, JNI,
Rust workspace and SQLite. The existing `android-scripted-play-v2` fixture runs
locally; actual model status asserts `real_model=false` and `loaded=false`.
This is native free-text integration evidence, not a model quality, active-model
cancellation, physical-phone, ARM64 or two-emulator qualification. The first
emulator's prior storage gate remains blocked; no first-emulator call occurred.

## What the methods actually exercise

The Compose rule owns a generic `ComponentActivity`, not the user `MainActivity`.
Each method creates a new UUID-named synthetic directory under the isolated
verification app's no-backup directory. A confined `ContextWrapper` redirects
that fixture's private directory; production adapters and protocol are unchanged.
Canonical parent checks precede use and deletion. No ordinary app workspace,
original save, model cache or model weights are opened.

A real accepted dialogue first creates revision 1 and two messages while
retaining the potion. The test then selects the actual Action or Dialogue chip,
types the original input and clicks Send. The request must use `free_text`,
preserve original kind, text, whitespace, Unicode and newline, and retain its
exact session/scope/turn binding. No legacy `submit` call or fabricated native
acceptance may stand in for that path. Accepted receipts must preserve the full
original request and version-2 scripted profile, and visible messages must match
the actual accepted narration.

The Action case transfers the sole potion and survives close/reopen. The
Dialogue case records exactly one `say` proposal and `said` outcome for the
literal statement, while preserving inventory, player self-state, facts and
beliefs and granting no claimed `blink` ability. This checks the permitted player
projection; it does not inspect or prove NPC-private/omniscient contents.

Cancellation cases hold delivery **after actual native preparation is ready**,
then call real Rust cancellation while that delivery remains held. They check
visible checking/disabled controls, unchanged canon, and rejection of a late
noncooperative reply. One case changes only the delivered cancellation turn key
after actual cancellation; the visible recovery click must resend the complete
original key without resubmitting, preparing twice or committing.

The lost-commit case actually commits in Rust, replaces its delivered
acknowledgement with a synthetic `Busy` rejection, and loses one subsequent
status response so the uncertainty reaches visible recovery. Recovery uses the
original key, retrieves the actual persisted receipt, and does not resubmit or
commit again. The UI's initial old history remains under recovery-required controls;
only accepted saved history establishes the outcome.

Disposal clears the actual ViewModel store, releases delayed replies and checks
that no late state replacement or new gateway operation occurs. Every method
drains wrapper exchanges, closes the production transport and opens **all four
actual native owner slots simultaneously**, closing every probe on IO. Each
case also reopens SQLite through a fresh production transport and compares the
entire permitted player projection, inventory and accepted receipts. These
assertions complete inside JUnit before deleting the fixture directory and
before any external test-host cleanup. They do not prove ownership inside a
real inference runtime, an actively blocked JNI call or an OS process-death path.

## Admission and bounded execution

The controller copies the preceding reviewed native cancellation controller into
a fresh private namespace; the preceding sealed evidence remains unchanged.
Initial admission requires the original 23 selected-target LocalLore package
hashes and the exact preceding isolated app/test pair. Only those two isolated
packages are installed using `install --no-streaming -r`.

The original floors remain 4 GiB plus 128 MiB on the host userdata volume,
10 GiB on the evidence volume, and 1 GiB plus 128 MiB in emulator userdata.
Boot completion, API, ABI, page size and absence of every LocalLore process
namespace are checked before installation and at final boundaries. A `/data`
query may display `/data/user/0` only with captured matching `stat -L` device
identities. No floor, final absence check or package-map gate was relaxed.

The actual instrumentation invocation is:

```text
am instrument -w -r -e class org.locallore.app.NativeTextRecoveryTest org.locallore.app.cancelack.test/androidx.test.runner.AndroidJUnitRunner
```

The client deadline is 90 seconds with a 128-KiB output bound. The outer Windows
Job deadline is 180 seconds, with an stdin-EOF barrier before dispatch. Clients
have fixed deadlines and sticky ownership state. Raw stdout is durably retained
before interpretation; stderr byte counts are retained without content. Unknown
cleanup, retention failure or an unexpected binding stops later dispatch.
The same live tool session was polled to authoritative completion; there was no
restart or second cohort.

The inherited parser requires six exact sequential paired method starts and
terminals, no skips/aborts/unfinished methods, and final runner completion after
all pairs. It preserves failing results as failures. **All six methods must pass
before any post-instrumentation process, UID, package or lifecycle call.**
Thus an external cleanup cannot manufacture passing native-owner assertions.

All 43 distinct pure controller fixtures passed: 20 framing/storage/install/map/
raw-retention cases, eight namespace/UID cases and 15 ownership/control-flow
cases. The failed-native-method fixture refuses even post-instrumentation
namespace observation, and wrong UID/package/map, uncertain ownership and failed
cleanup cannot trigger a retry. These are the inherited 43 cases executed for
this packet, not 43 newly invented cases or a substitute for device execution.

## Actual candidate result

The sole admitted cohort completed in **54,531 ms**, child return code zero,
with known Windows Job cleanup. All **46 clients** completed with return code
zero and known client cleanup. Every raw stdout record was rehashed with zero
mismatches. All six exact methods passed, with no skip or unfinished method.
Existing production behavior required no production correction; no RED baseline
or before/after production-fix result is claimed.

| Frozen method | Result |
|---|---|
| `typedActionPreservesOriginalInputAndPlayReceiptAcrossReopen` | Passed |
| `typedLiteralDialogueRecordsStatementWithoutGrantingClaimedPowers` | Passed |
| `cancelledReadyTextReplyCannotChangeCanonOrLateVisibleHistory` | Passed |
| `malformedTextCancellationAcknowledgementRecoversOriginalKeyVisibly` | Passed |
| `lostTextCommitAcknowledgementRecoversActualAcceptedReceiptWithoutResubmission` | Passed |
| `disposedTextOwnerFencesLateDeliveryAndReclaimsAllNativeSlots` | Passed |

The raw instrumentation transcript is 4,348 bytes, SHA-256
`f35f70b8cb20b035fb988d0bff7feeed46b71f29a48e5d64a7b506255dca60b6`.

After all six tests passed, the sole remaining LocalLore process was the exact
isolated test package. Fresh exact UID and full 25-package map checks admitted
one `am force-stop org.locallore.app.cancelack.test`. No other package or process
was stopped. This is operator test-host hygiene, **not natural Android-process
exit** or model cleanup. In-JUnit drain, four-slot and reopen assertions had
already passed before this action.

Original after/final namespace absence, all four exact 25-package maps and all
capacity gates passed. Every original 23-package hash was preserved. Final
available emulator userdata is **1,644,441,600 bytes**, above the unchanged
1,207,959,552-byte floor; host volume floors also pass. Every call is terminal,
the exclusive dispatch lease is released and no additional cohort was run.

## Exact artifacts and handoff

| Artifact | Bytes | SHA-256 |
|---|---:|---|
| Admitted app APK | 22,479,391 | `fc01b1ce8516b499d5ca47c518176cba1a93ba4350c2e27d1a14f7ec99950e40` |
| Admitted test APK | 2,368,766 | `eb11f1dd45cee19aadd972b99210fc0a9777352ead35250d94a830f97e664a06` |
| Frozen test source | 23,825 | `bae23dba98f32953c215280ea297c23c91bb25457e4309e262ee21298e35e867` |

The app and four packaged native library bytes match the preceding #126 pair.
The previously installed test APK hash is
`ed5b4e1a66bf4519b89c651cf451ad9d059a5b4d4bb24935a2334d38a2aab605`.
The preceding six-method legacy native fixture remains byte-identical at source
hash `bb157bb788ca5ea132dd4664a6664f59c1fca55181c2986ab3f5051e51ef8147`;
it was retained and compiled, not rerun by this new class invocation.
Coordinator and reviewer independently checked the disabled proposal, final
source/APK and all 25 bound inputs before promotion and separate execution GO.
Promotion changed only the two admission flags; the original proposal is retained.

The closed private selection contains **134 files / 215,225 bytes**. Its
22,707-byte index has SHA-256
`80fcd17373fa9384e45ac98e11dd830c3500c32521ec4ab96ec86bb88df8671d`.
All 146 files in the preceding native cancellation selection were rehashed with
zero mismatches and remain unchanged. An initial duplicate-branch provisioning
attempt found the already-created clean worktree. That failed command changed
no source, reset no checkout and issued no device operation.

Raw diagnostics, APKs, private paths and unique device/process identities remain
local. No screenshot, real-model operation or copy, emulator relaunch/reset,
clear-data, uninstall, original-save access or first-emulator query occurred.
Physical-phone, real-model, ARM64, sustained-performance and two-emulator gates
remain blocked or unqualified. This report is local evidence for partial tasks,
not owner acceptance or permission to merge.
