# Model receipt transaction host verification — 2026-10-24

Refs #9 (M05.05 prerequisite), #5 (M01.05 supporting).
Status: implemented host proof, in review; full tasks remain unchecked.
Stacked on unmerged PR143 at `0cd54cb69176db61ae487a32614413422be0e66c`.

## Result and scope

Compiled source `2f59efde07eec5a67b4ab0df5e96b0c4555360aa` passes candidate
app/instrumentation Kotlin compilation, all **323 JVM tests / 33 suites**, lint
and dependency/analyzer audits. There are zero test failures, errors or skips;
lint has zero errors/fatal findings and nine warnings. The 24 new tests comprise
23 file/ownership/cancellation tests and one actual child-JVM lock/halt/recovery
test. Later verification/review edits are documentation only.

The [contract](MODEL_RECEIPT_CONTRACT.md) and proposed
[ADR0011](../adr/0011-model-receipt-transaction.md) define exclusive receipt and
owner creation, full verification, re-force before acceptance and an empty
exclusive marker as the logical visibility point. This class is unwired: scope
inspection finds no reference from other Kotlin production/test callers beyond
the two receipt test files. Existing LocalModelStore, selectors, SDK admission,
Compose setup, native publication, manifests, dependencies and Rust engine are
unchanged. This packet assembles no APK and executes no Android/device/model or
SDK inference. Native build is explicitly excluded, not reported as passing.

## Executed checks

Windows host, JBR 17.0.6 daemon; JDK 21.0.4 compilation/testing. Existing pinned
Gradle 8.11.1, AGP 8.10.1, Kotlin 2.4.0 and LiteRT-LM 0.18.1 graph. No new
dependency or model selection. From `apps/android`, the final owned worker used:

```powershell
& 'C:/Program Files/Android/Android Studio1/jbr/bin/java.exe' `
  -classpath gradle/wrapper/gradle-wrapper.jar org.gradle.wrapper.GradleWrapperMain `
  :app:compileDebugKotlin :app:compileDebugAndroidTestKotlin `
  :app:cleanTestDebugUnitTest :app:testDebugUnitTest :app:lintDebug `
  :app:auditLiteRtDependencies :app:auditLintAnalyzer -x :app:buildRustAndroid `
  --offline --no-daemon --console=plain --max-workers=2 `
  -Pandroid.builder.sdkDownload=false -Pkotlin.incremental=false `
  -Pandroid.experimental.lint.version=9.4.1 `
  -Porg.gradle.java.installations.auto-download=false `
  '-Porg.gradle.java.installations.paths=C:/Program Files/Java/jdk-21' `
  -PlocalLoreLiteRtVerification=true -PlocalLoreModelSetupVerification=true `
  --project-cache-dir .gradle-litert-worker
```

The worker set JAVA_HOME/ANDROID_HOME/ANDROID_SDK_ROOT to existing installations
and private TEMP/TMP. Its Windows Job owned descendants, with a stdin launch
barrier, 900-second deadline, two build workers and 2 MiB output cap. Original
final execution session 75180 was consumed once: chunk 5950ca, exit 0. Retained
owner result: completed, returncode 0, cleanup_complete true, **114,281 ms**,
4,916 output bytes, SHA256
`8ecc5ee7afab3162e6a2afb3ce8c2d72c72d34e95ef46e3d742bece1e40d8222`.

Both audit tasks pass. All 62 runtime and 67 analyzer artifact rows match the
previous PR143 graph exactly; analyzer execution did work. No dependency locks
changed. Lint retains OldTargetApi, GradleDependency, ObsoleteSdkInt and six
UsableSpace advisories. Two UsableSpace findings concern this host proof's
default File capacity callback: Android allocation policy remains the future
trusted adapter's responsibility. No warning suppression or reserve reduction
was added. The new nullable-parent compiler warning was corrected; existing
unrelated compiler/build warnings remain. `git diff --check` passes.

## Failure and recovery evidence

The first attempt failed compilation on inferred Enum/OpenOption intersection
arrays: completed exit 1, cleanup true, 38,750 ms, output SHA256
`cbfd6102058bd9a8d2a21d36f671f93c6e59989e6991a81812356ff7c923cca9`.
Explicit OpenOption arrays fixed it. Intermediate source 81c356d then passed the
entire command: 323 tests, lint 0/9, completed exit 0, cleanup true, 143,719 ms,
output SHA256 `332f6a4cab13247a5e67e7e25bd851b5cce2d4ce21e4ba8950ec20900a1e38ac`.
The final rerun above followed the nullable-parent correction; all results are
retained rather than overwritten.

Actual tests cover exclusive visibility/idempotent reopen; receipt-only and
complete-pending recovery without source reopening; full-read source-close
failure; bounded short/oversize/zero-progress input; malformed records and
nonzero/link markers; canonical-case reopen; cross-control shared-data refusal;
missing lock/cache refusal; unknown-byte preservation; overlapping/unowned/link
roots; overflow-safe capacity and guard revocation; explicit discard/retry and
partial discard interruption. Negative-source tests count actual opens, because
throwing a test error inside a sanitized callback could otherwise falsely pass.

A blocked read remains BUSY after cancellation until its source actually
returns/closes once. Real self-cancelled child coroutines exercise BEFORE_COMMIT
and AFTER_COMMIT: preacceptance data stays invisible and explicitly discardable;
postacceptance data stays verifiable and cannot be discarded. The actual child
JVM is refused through all three operations while it holds the OS lock, halts
with exit 73 at DATA_FORCED without finally cleanup, and leaves exact pending
receipt/owner/model bytes recoverable without opening a source. Its overall
watchdog is 20 seconds; only the owned child can be terminated. A bounded BUSY
wait allows delayed OS lock release. These are host process-death checks, not
Android process-death or power-loss measurements.

## Evidence binding and independent review

Final public-source snapshot: 1,384 tracked files, 16,193,884 bytes, index SHA256
`a0f1b2aec68b341f88afa06f8cf710576214af7b891377f78779aca21794db76`.
Private `LocalLore-receipt-host-20261024` retains all three attempts, frozen
sources, classes, XML, lint/audits and bounded owner results. Final index
`sealed-host-final-index-v2.json`: 4,288 files / 50,820,556 bytes, SHA256
`02db8701deb13e374adc8478939689858989c17558d7b604fb8d30b546b930f1`.
Scratch temp directories are excluded; raw diagnostics remain local.

The first index header accidentally retained the intermediate 81c356d source
after a Python 3.9 metadata-helper compatibility error. Its bytes are preserved;
the appended final v2 explicitly supersedes that header, binds final 2f59efd,
and rehashes every old and new indexed file. The first index must not be used
as the final compiled-source binding. This affected evidence metadata, not the
executed checks. See the [independent review](MODEL_RECEIPT_REVIEW_2026-10-24.md)
for actual source/test findings, corrections and evidence validation.

## Remaining gates and next runnable task

No task checkbox is checked without owner acceptance/merge. Full M05.05 and
M01.05 remain blocked by Android filesystem/storage/runtime and reference-phone
gates. PR143's latest published external observation was 3,556,818,944 bytes,
1,178,812,416 below unchanged 4,735,631,360-byte real-copy admission; this packet
does not remeasure it. A/#117/#119 holds remain. No benchmark/cache adoption,
model copy, volume fallback, environment creation or cleanup authority follows.

Next: separately claim an isolated Android synthetic qualification adapter for
this receipt protocol under existing Context/exact-one-volume guards, without
activating it as a setup fallback. Test exclusive creation, locks, receipt/owner
validation, process death and guard/refusal behavior on admitted targets before
any real model or SDK execution. Capacity remains independent. Nullable file
keys do not prove inode identity; media swaps, hostile OS, power-loss directory
durability, cache confidentiality, phone/ARM64/16 KiB execution, model quality
and sustained runtime remain unproven. Missing/incomplete owner metadata and a
discard crash after owner removal can leave preserved orphans requiring
separately authorized recovery. No merge, release or access change occurred.
