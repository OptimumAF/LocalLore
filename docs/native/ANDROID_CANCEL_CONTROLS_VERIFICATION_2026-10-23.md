# Compose cancellation controls, 2026-10-23

Refs [#9](https://github.com/OptimumAF/LocalLore/issues/9), M05.04 partial,
and [#8](https://github.com/OptimumAF/LocalLore/issues/8), M04.04 supporting.
Prerequisite: unmerged [#123](https://github.com/OptimumAF/LocalLore/pull/123),
exact `58904bd0ae0280f75ce71998fd4821726e41476a`.

## Behavior and authority

The screen previously said `Opening saved progress…` while awaiting cancellation
reconciliation. It also left New story and Saved stories enabled when recovery
was required. Gateway validation still protected the pending key; this packet
does not claim a reproduced canonical mutation or key-loss bug.

Correction `2dedd502798b0f75647048d1d64444d8fc81f4e2` adds a presentation-only
checking flag, set during saved cancellation and cleared on publication,
failure or disposal. The polite live status says `Checking cancellation…` until
the acknowledgement and accepted snapshot finish. Saved-library button/popup,
New story and retained resume/reset callbacks obey recovery-required state.
Reset remains available for the separate in-memory demo's uncertain outcome.

Only ShellState, ShellViewModel and LocalLoreScreen production code changed.
Existing gateway validation, Rust gameplay/commit authority, wire/schema,
dependencies, permissions and runtime/model selection are unchanged.

## Independent fixture and baseline

Eight actual Compose tests were frozen at
`cf94aebbd6913338f00ef0250966f68587014ae9`, imported as `5f1ab6a`, before
production edits. They render LocalLoreScreen with actual ShellViewModel,
DurableGateway, Android main dispatcher and JSONObject, using synthetic
transport replies. The generic AndroidX Activity host is launched and torn down;
user MainActivity, NativeWorkspace, JNI, SQLite and inference are not invoked.

The fixture starts with available scripted input and a valid draft, so disabled
Send assertions are meaningful. Actual clicks cover Give, Cancel and Recover;
hostile acknowledgements use foreign turn, ready phase and missing committed
receipt as separate methods. Other cases cover acknowledgement/snapshot delay,
accepted committed race, late preparation and disposal.

The baseline ran all eight exact start/terminal pairs and final runner terminal:
**three passed / five failed**, with no skip/unfinished method. Two failures
showed the wrong busy text; three reached the still-enabled Saved stories
button. Later reset/retained-callback assertions were not reached on RED.
Committed-race, late-preparation and disposal methods already passed.

The overall baseline cohort **stopped** at its first post-test process check:
the isolated TEST package process remained. All 27 clients completed with exit
zero and known cleanup, but after/final maps and floors were not reached.
Before/installed maps preserved the original 23 package hashes plus the admitted
pair. Raw instrumentation: 26,700 bytes, SHA256
`dcc64674c0e8e7961395e6450342c27337fede2316f488d77a6290ee5e0d5c64`.
The stopped cohort took 42,969 ms, outer child two with known Job cleanup.

Read-only settlement separately completed ten clients in 2,250 ms, child zero
with known cleanup: the same TEST process UID matched its installed package,
the exact 25-package map matched and storage floors passed. The attempted system
instrumentation subcommand was unsupported; its 115-byte output remains retained.
It establishes no active-instrumentation absence. The original cohort stays
stopped; later observations do not manufacture its missing checks.

## Explicit test-host cleanup

A separately reviewed cleanup revalidated the exact TEST process/UID, package
UID, installed 25-package hashes, device identity and original capacity floors,
bound to all eight terminal baseline method records. It performed one fixed
`am force-stop org.locallore.app.cancelack.test` and then required the original
namespace-absence, map and capacity checks. All **26 clients** completed with
exit zero/known cleanup in **6,000 ms**, outer child zero. Final userdata was
1,644,228,608 bytes free; after/final maps matched. No other package, emulator
lifecycle, reset, data clearing, uninstall or model operation was involved.

This is explicit test hygiene, not evidence of natural process exit or native
worker reclamation. The reason the generic host process survived remains
unqualified; no graphics-cause fix follows. The original cohort remains stopped.
The candidate controller requires all eight paired terminal records before
conditional cleanup of that same exact TEST package: a lone TEST namespace,
matching UID/package UID and exact admitted 25-package map, then at most one
fixed stop. Other namespaces, changed ownership/maps, unfinished methods or
failed cleanup fence further work. It still requires original after/final
absence, capacity and preservation checks. Separate pure fixtures cover these
refusals. This change was reviewed and authorized before candidate execution.

## Actual candidate Compose result

The candidate completed **eight passed / zero failed**, all eight exact
start/terminal pairs, no skips or unfinished methods, and final runner terminal
after those pairs. This includes all later recovery/reset/retained-callback
assertions that the RED cases did not reach. The eight tests now exercise the
visible checking status, disabled competing controls, original-key Recover
click, accepted committed race, late preparation and disposal.

The complete owned cohort took **53,234 ms**, child zero with known cleanup.
All **46 clients** completed with exit zero/known cleanup. One conditional exact
TEST stop occurred after the eight paired terminal records and fresh UID/map
admission. Original after/final absence, exact 25-package maps, original 23
package hashes and storage floors passed. Final userdata was **1,644,175,360
bytes**, above the unchanged **1,207,959,552-byte** floor. Across the separate
baseline, settlement, cleanup and candidate stages, all **109 client stdout
sizes/hashes/statuses** were checked centrally and independently with zero
mismatches. This does not turn the original stopped baseline into a completed
cohort. The two explicit TEST stops across cleanup/candidate are operator
cleanup, not natural-exit or native ownership proof.

Candidate raw instrumentation: **5,728 bytes**, SHA256
`eea20d3b8b7633d0295f64325b4e3857c765bc070c3081f22cafc9e95a7bf7d0`.
The device runner separately passed 20 pure cohort, eight settlement and 14
ownership/flow fixtures; repeated overlapping executions are not extra unique
tests. No further device call or lease remains.

The closed device selection has **327 files / 457,715 bytes**, rehashed by the
coordinator with zero mismatches. Its **55,854-byte** index SHA256 is
`f5d99fb0dad7cef4a567ed6f5514792160b4e745acea35d15313b8cf77a60376`.
Selected closed host evidence has **54 files / 49,933,687 bytes**, including
exact APKs/source copies, build logs/receipts, JVM XML and lint XML, excluding
temporary build files. Its **10,129-byte** index SHA256 is
`ed70b9de8eebcd0a5663d8004b6d5a05083e68a8db1f4bcf9f30593a000a48f5`.
The selections include overlapping bytes, not additional experiments.

## Host build and reproduction

Existing pins: Java 17.0.6, Gradle 8.11.1, AGP 8.10.1, Kotlin 2.2.21,
coroutines 1.10.2, SDK compile/target 36/minimum 26, Build Tools 35.0.0,
NDK 29.0.14206865 and Rust 1.93.1. No new compatibility decision was needed.

From `apps/android`, with those toolchains configured:

```powershell
.\gradlew.bat :app:assembleDebug :app:assembleDebugAndroidTest :app:cleanTestDebugUnitTest :app:testDebugUnitTest :app:lintDebug -PlocalLoreCancelAckVerification=true --project-cache-dir .gradle-cancel-ack -Pkotlin.incremental=false --offline --no-daemon
```

The actual Java wrapper invocation also selected plain console, two workers and
`android.builder.sdkDownload=false`, inside a 900-second/2 MiB Windows Job with
an input barrier and verified cleanup. Baseline app/test assembly completed in
**38,234 ms**; candidate assembly/fresh JVM/lint in **74,625 ms**, both child zero.
Candidate: **150 JVM tests passed**, zero failures/errors/skips across 19 XML
files. This includes the existing in-memory uncertain-commit Reset regression.
Lint: **zero errors / one existing GradleDependency warning**. The existing
FrameworkInterruptionTest AtomicReference/Boolean compiler warning remains.

Both app/test identity, permission, runner and native ELF/ZIP alignment audits
passed. Native build outputs were reused; all four library hashes match the
baseline. No new native compilation or ARM execution is claimed. No scripts
changed; prior script test counts are not new runs for this packet.

After source/artifact, ownership, package-map and capacity admission, select:

```powershell
adb -s <authorized-target> shell am instrument -w -r -e class org.locallore.app.CancelControlsTest org.locallore.app.cancelack.test/androidx.test.runner.AndroidJUnitRunner
```

This command alone does not replace admission, paired-method result parsing or
postchecks. Actual Compose scrolling/idling has a separately reviewed 90-second
instrumentation client bound inside a 180-second owned cohort; production/model
bounds and storage floors are unchanged.

## Artifacts and unchanged assertions

| Artifact | Baseline SHA256 | Candidate SHA256 |
|---|---|---|
| App APK | `d8b82930934304a3352b8cbab415c69b490fafa189364815d71e6d88382fc94d` | `fc01b1ce8516b499d5ca47c518176cba1a93ba4350c2e27d1a14f7ec99950e40` |
| Test APK | `a0f5b338ff292e05717910d4df63df95cff62940aa94b2bf71a5950aa138d5f0` | `001edf660218539da70df7e222218d816f3ef8072c5cfe034539620347020740` |

App sizes: 22,524,394 / 22,479,391 bytes; test sizes: 2,327,862 / 2,327,834.
Both APKs differ. Kotlin test compilation reran after the ShellState constructor
ABI changed. Test assertions/methods did not change: separate cosmetic commit
`c31593de13498ca322f77cfd9f6687316929b446` removes only one extra final LF
after the class brace. Exact baseline fixture is 17,810 bytes, SHA256
`8f4b902dc6214f810d9919a1a377a9b49c8e8f89f6a50f14f1f824eee03e05a8`;
candidate 17,809 bytes, SHA256
`05db4e41f6eeb60d0a9e209c81531b625551d542421cbbea03d18f0c32d1c494`.
The coordinator verified baseline bytes equal candidate bytes plus one LF.
Each cohort binds its own exact source/APK pair; binary identity is not claimed.

## Limits and handoff

Only B, API 35/x86_64/4096-byte pages, is admitted. A remains blocked by its
previous 162,394,112-byte storage deficit and was not queried again. M01.01
physical-phone verification remains blocked. Earlier M01 storage/timeout/
preservation failures and the unexplained graphics cleanup abort remain open.
These synthetic transport tests cannot establish Rust/SQLite canon, natural
native/model resource reclamation, process restart, real generation, quality,
sustained use, ARM or physical-phone behavior, or a two-emulator gate.

See the [device report](ANDROID_CANCEL_CONTROLS_DEVICE_2026-10-23.md) and
[independent review](ANDROID_CANCEL_CONTROLS_REVIEW_2026-10-23.md).
M05.04 remains **in_review, partial**; M04.04 receives supporting evidence. Acceptance boxes
stay unchecked. No merge, release, access/protection change or private payload
upload occurred. Raw diagnostics, identifiers and APKs stay
local. Next useful task: exercise these cancellation/recovery controls against
the actual Rust transport with isolated synthetic acknowledgement faults.
