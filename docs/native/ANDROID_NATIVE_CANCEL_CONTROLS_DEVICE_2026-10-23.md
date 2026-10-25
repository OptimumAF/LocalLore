# Android native cancellation controls checks

Refs #9 (M05.04 partial), #8 (M04.04 supporting).

Six independently authored methods passed on the selected second Android 15 /
API 35 x86_64 emulator with 4096-byte pages. They render the actual
`LocalLoreScreen`, `ShellViewModel` and `DurableGateway`, and call production
`NativeWorkspaceTransport` through JNI into the Rust workspace and SQLite.
Inference uses the existing deterministic fixture. This establishes the tested
native cancellation/recovery integration, not real-model resource ownership,
physical-device performance, ARM64 execution or a two-emulator qualification.
The first emulator's storage gate remains blocked; no first-emulator call was
issued in this packet.

## Actual native boundary and containment

Each method creates a new UUID-named synthetic directory below the isolated
verification app's private no-backup directory. A confined `ContextWrapper`
redirects only that fixture's `noBackupFilesDir`; the production transport and
native protocol are unchanged. The fixture checks canonical parent containment
before use and again before removing its own directory. It never opens the
ordinary app's workspace, original saves, model cache or model weights. The
Compose rule owns a generic `ComponentActivity`, not the user `MainActivity`.

A real native dialogue turn first establishes accepted revision 1 and two
messages, while retaining the player's potion. The proposed gift then reaches
actual native `ready` before its reply delivery is held. Cancellation calls
actual Rust while that delivery remains held. These gates delay delivery after
JNI returns; they do not simulate a still-running native inference worker or
measure cancellation latency inside a model runtime.

Acknowledgement fault cases alter only the delivered reply after the actual
native cancellation has completed. A foreign turn, unfinished phase and
committed phase missing its receipt must retain visible original history and
require recovery. The recovery click resends the complete original cancellation
key: session, scope and turn. It submits/prepares only once and never invokes a
second commit. The distinct committed-race case runs a real Rust commit before
native cancellation, then displays the actual committed receipt exactly once.

The fixture refreshes the actual native head, verifies player-only inspection
boundaries, and compares the complete permitted player projection and accepted
receipts across SQLite close/reopen. The disposal method clears the actual
ViewModel store, releases delayed replies and confirms no late state replacement
or new gateway operation. Every method drains wrapper exchanges, closes the
production transport, and then opens **all four actual native owner slots
simultaneously**, closing each probe on IO. Reopen checks repeat the slot proof.
These assertions finish inside JUnit, before fixture-directory deletion and
before any external test-host cleanup. No Kotlin gameplay reducer, production
hook, schema change or synthesized native acceptance is introduced.

## Admission and observation

The new private controller namespace copies the preceding reviewed Compose
controller and bounded Windows Job owner. Closed predecessor evidence remains
unchanged. Initial admission requires the exact original 23 selected-target
LocalLore package hashes and the preceding isolated app/test APK pair. Only the
isolated verification app and its test package are installed with
`install --no-streaming -r`.

Unchanged floors are 4 GiB plus 128 MiB on the host userdata volume, 10 GiB on
the private evidence volume, and 1 GiB plus 128 MiB in emulator userdata.
Boot completion, API, ABI, page size and absence of every LocalLore process
namespace are checked before installation and at final boundaries. The fixed
`df -k /data` query may display `/data/user/0` only when the captured
`stat -L` device identities match. No floor or original final gate is relaxed.

The admitted instrumentation command is:

```text
am instrument -w -r -e class org.locallore.app.NativeCancelControlsTest org.locallore.app.cancelack.test/androidx.test.runner.AndroidJUnitRunner
```

The instrumentation client has a 90-second deadline and 128-KiB output limit;
the outer Windows Job has a 180-second deadline and an stdin-EOF barrier before
dispatch. Individual device clients have fixed deadlines and sticky ownership
state. Raw stdout is flushed before interpretation; stderr byte counts are
retained without content. Unknown cleanup, retention failure, binding mismatch
or unexpected namespace stops later dispatch. No observation timeout triggers
a restart. The sole admitted tool session was polled to authoritative completion.

The parser requires all six exact method identities with sequential counters,
paired starts/terminals, no skips, aborts or unfinished methods, and the final
runner code after all pairs. Before dispatch, independent review found that
the predecessor's RED-capable path allowed cleanup after paired failing methods.
This packet now durably retains the parsed result and requires **all six methods
to pass before any post-instrumentation namespace, package or lifecycle call**.
The parser continues to preserve RED results as failures. Source history and the
pre-dispatch correction receipt are retained locally; no device call preceded
the fix.

Forty-three distinct pure host fixtures passed: 20 parser/storage/install/map/
raw-retention cases, eight process/UID framing cases and 15 ownership/control-flow
cases. They include a failed native method refusing every post-instrumentation
query, wrong UID/package/hash, absent-host skip and no retry after failed cleanup.
The same 43 cases were repeated after the final source binding changed; these
are not 86 unique tests. Mocked controller checks do not replace device execution.

## Actual candidate result

The single candidate cohort completed in **48,782 ms**, with child return code
zero and known Windows Job cleanup. All **46 issued clients** completed with
return code zero and known client cleanup. Every raw record was rehashed with
zero mismatches. All six methods passed; there were no skipped or unfinished
methods. Existing production behavior required no production correction, so no
RED baseline or before/after production fix is claimed.

| Frozen method | Result |
|---|---|
| `nativeCancellationKeepsCheckingVisibleUntilActualAcknowledgementAndRetainsCanon` | Passed |
| `foreignNativeAcknowledgementRequiresVisibleExactKeyRecovery` | Passed |
| `unfinishedNativeAcknowledgementRequiresVisibleExactKeyRecovery` | Passed |
| `incompleteCommittedNativeAcknowledgementRequiresVisibleExactKeyRecovery` | Passed |
| `actualCommitBeforeCancelShowsAcceptedHistoryOnceAndSurvivesReopen` | Passed |
| `disposalFencesActualLateRepliesAndReclaimsAllNativeOwnersBeforeReopen` | Passed |

The raw instrumentation transcript is 4,412 bytes, SHA-256
`46b34ea40b530bd8639d6e0cb8e547e298f7ed7d8ddfa038ee831c9357b4c0d4`.

After all six methods had passed, the sole remaining LocalLore process was the
exact isolated test package. A fresh exact package UID and full 25-package map
matched the fixed cleanup admission. The controller performed one conditional
`am force-stop org.locallore.app.cancelack.test` for that verified test UID.
No other process or package was stopped. This is explicit operator test-host
cleanup, **not natural Android-process exit** and not evidence about model
resources. Native wrapper drain, SQLite reopen and four-slot reclamation were
already asserted before this external action.

Original after/final namespace-absence, package maps and capacity checks passed.
All four observed package maps contain the expected 25 entries, retaining every
original 23-package hash. Final available emulator userdata is
**1,644,118,016 bytes**, above the unchanged 1,207,959,552-byte floor. Final host
userdata/evidence free space also passed. All device calls are stopped and the
exclusive dispatch lease is released. No additional cohort was run.

## Exact artifacts and retained preparation corrections

| Artifact | Bytes | SHA-256 |
|---|---:|---|
| Admitted app APK | 22,479,391 | `fc01b1ce8516b499d5ca47c518176cba1a93ba4350c2e27d1a14f7ec99950e40` |
| Admitted test APK | 2,348,183 | `ed5b4e1a66bf4519b89c651cf451ad9d059a5b4d4bb24935a2334d38a2aab605` |
| Final test source | 20,712 | `bb157bb788ca5ea132dd4664a6664f59c1fca55181c2986ab3f5051e51ef8147` |

The app is byte-identical to the preceding #125 candidate. All four packaged
native library hashes are unchanged; native execution evidence comes from the
actual JNI tests, not packaging alone. The preceding installed test APK hash is
`001edf660218539da70df7e222218d816f3ef8072c5cfe034539620347020740`.
The final audited APK pair, source, controller, owner and 25 input bindings were
independently reviewed by the coordinator before dispatch. The disabled proposal
was preserved; promotion changed only its two admission flags, followed by a
separate exact coordinator execution GO.

The original independent test source is retained at SHA-256
`936e7598daca77b9be658f2efbaddaca918ba05132eacf4a8dded509a275c1ba`.
Its first compile exposed a nullable-parent warning; a checked local parent
preserves the same containment assertions. The original source and first test
APK are retained separately by the coordinator. All six method identities and
oracles remain unchanged. Only the final source/APK pair was installed or run.

Two local preparation errors are preserved, with zero device calls: the host
Python version lacks the `Path.write_text(newline=...)` argument, corrected using
newline-aware `open`; and the copied proposal builder expected audit phase
`candidate`, while the actual final audit says `candidate-final`, corrected by
checking that exact label in a separately retained generator. Neither failure
was reclassified as device evidence or changed the admitted APK bytes.

The closed private selection contains **146 files / 270,802 bytes**. Its
24,640-byte index has SHA-256
`c691d7f7bf2e2890d55b294ca5079d050bd4db3e804e693181320319c9fa0a93`.
All 327 files in the preceding closed Compose selection were also rehashed with
zero mismatches and remain unchanged. Raw diagnostics, APKs, unique process/
device identities and private paths stay local. No screenshots, emulator
relaunch/reset, clear-data, uninstall, real-model operation, original-save access
or first-emulator query occurred. Physical-phone, real-model, ARM64, sustained
performance and first-emulator storage gates remain blocked or unqualified.
