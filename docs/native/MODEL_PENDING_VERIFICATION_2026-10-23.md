# Pending picker verification — 2026-10-23

Refs #9 (M05.05; M05.04 supporting). Execution began on then-open,
unmerged PR #136 at `4ae51ee55509513e21a91210a262a97c0d8e94ba`.
The [contract](MODEL_PENDING_CONTRACT.md) defines the measured boundary.
Full milestone acceptance and owner review remain pending.

The final upstream refresh observed #136 merged externally as `b279eff`.
That default-branch head contains the tested prerequisite. The focused PR targets
`main`; the checks below apply to this packet's frozen source/artifacts, not a
new execution of every intervening default-branch change. No merge was performed
by this packet.

The final synthetic procedure passed on one Android 15 / API 35 x86_64 emulator
with 4 KiB pages. Android restored the actual pending result into a new process;
the fresh controller rejected it without opening a source. A later explicit
valid selection reached READY, and the separate no-restart observer passed
1 test / 0 failures. This is a bounded provisioning proof, not a playable
real-model scene or physical-phone qualification.

## Source and host checks

Author commit `fbad60a376c7f7baf51c0cdb29c89b801320700f` was integrated
as `1f933fc`. Coordinator integration `51a24bd` adds the no-op callback seam,
private manifest entry, artifact guards, bounded scroll synchronization and
developer documentation. Independent review corrected SDK filtering, sticky
callback overflow/error accounting, receipt-job completion and the test runner's
default Activity finishing before execution. No runtime/model dependency changed.

The initial fixture build compiled but failed lint with one NewApi error:
the Activity's class-wide API-30 annotation conflicted with its manifest entry
and the unchanged API-26 minimum. Commit `b822796` replaces that annotation
with an explicit API-30 runtime guard at the observation boundary; unsupported
calls set the sticky receipt failure and return before newer APIs. The selected
tests retain `SdkSuppress(minSdkVersion=30)`. No lint suppression or minimum-SDK
increase was used. The failed owned worker reached terminal 1 with complete
cleanup in 186.266 s; its output and failing lint XML/text are retained.

| Actual check | Result |
|---|---|
| `python -B -m unittest discover -s scripts/tests` | 196 PASS, 18.094 s |
| Artifact-audit subset (`-p test_audit_apk.py`) | 17 PASS, 0.898 s |
| Regular setup offline assemble APP/TEST, clean JVM tests, lint, dependency and analyzer audits | PASS; owned worker terminal 0, cleanup complete, 191.985 s |
| Regular setup JUnit XML | 276 tests / 28 suites; 0 failure/error/skip |
| Regular setup lint | 0 errors; existing OldTargetApi, GradleDependency and two UsableSpace warnings |
| Copied signed regular APP/TEST audit | PASS: package/permission/launcher/fixture exclusion, signatures, SDK/native inventory and 16 KiB ELF/ZIP alignment |
| Corrected explicit fixture full offline build | PASS; owned worker terminal 0, cleanup complete, 138.390 s |
| Explicit fixture JUnit XML | 276 tests / 28 suites; 0 failure/error/skip |
| Explicit fixture lint | 0 errors; regular four advisories plus one UseKtx suggestion |
| Copied signed fixture APP/TEST audit | PASS: exact private Activities, TEST-only provider, signatures, pinned SDK/notices and native alignment |

The regular copied APP is 73,829,560 bytes, SHA-256
`49d9312f99b64707d5ecd406e06bf94a37624ec7c77519a8711264d4f4a1433c`;
TEST is 1,755,365 bytes, SHA-256
`6ea5c33f3023280ca304b30f844228760e02279e576902a3ba8d824c37569477`.
These artifacts were not installed by this check.

The first admitted fixture APP is 74,157,896 bytes, SHA-256
`c8b9984a8a836cb5f5642f342f115ea8a648ad6c3898baf5b70cc3b14234bd59`;
TEST is 1,809,009 bytes, SHA-256
`270b1db9409a9080166cac297713d93f94d85671ab881c617782d3d9133f5b86`.

Builds use the existing pinned SDK/runtime graph, offline resolution, two workers,
disabled SDK/Java downloads, Java 21 compilation and the existing lint 9.4.1
verification override. The exact selected tasks/arguments, bounded worker
ownership/terminal metadata, copied XML, lint and signed-artifact audits remain
in the new local evidence namespace. Raw private diagnostics are not published.
Its sealed host index covers 103 files / 151,879,784 bytes, SHA-256
`6f6a682b9e08318818903b82e39d81bffa4e68d2c726e991ac2cf72af59a1c0d`.
The independent reviewer rehashed every indexed file, checked actual XML/lint,
the failed/repaired terminal records, signed pair and current source bindings.

The full fixture worker invoked `org.gradle.wrapper.GradleWrapperMain` with
`:app:assembleDebug :app:assembleDebugAndroidTest :app:cleanTestDebugUnitTest
:app:testDebugUnitTest :app:lintDebug :app:auditLiteRtDependencies
:app:auditLintAnalyzer`. It selected
`-PlocalLoreLiteRtVerification=true`,
`-PlocalLoreModelSetupVerification=true` and
`-PlocalLoreModelPickerVerification=true`, with `--offline --no-daemon
--console=plain --max-workers=2 --project-cache-dir .gradle-litert-worker`,
`-Pandroid.builder.sdkDownload=false`,
`-Pkotlin.incremental=false`,
`-Pandroid.experimental.lint.version=9.4.1` and
`-Porg.gradle.java.installations.auto-download=false`; the local Java 21
installation was explicitly selected. The regular setup run omitted only the
picker-profile property. These are build checks, not device-result substitutes.

## Device checks and limits

The first independently controlled B cohort stopped before accepted readiness.
All 32 clients completed with known cleanup. Its selected arm reported an ordinary
0-PASS/1-FAIL at the APP-active-window scroll guard; it was not the expected
interruption. The original outer invocation reached authoritative terminal
(child rc2, cleanup complete, 16.610 s), and the arm drained naturally without
emergency cancellation. No handshake, host document tap, observer or stop ran.
The copied own pair was updated once each. The latest full package/UID snapshot
was before bootstrap; final state is not inferred from it.

This proves the window guard failed, but does not identify a null/stale/foreign
window or establish that no picker launched. The subsequent repair uses bounded
exact-APP/control readiness, preserved request/DocsUI/save checks and a new fixed
v2 namespace. The failed v1 root is retained. A separate read-only settlement
established later process/task/package state before lifecycle admission. No
automatic retry or data clear was used.

The stopped selection index covers 210 files / 1,481,418 bytes, SHA-256
`10c7b71a3a14711fa7df80ada77ff54f5d1f63c7b79d01b352acd9d98d49566e`.
Independent review rehashed every file and all 32 client receipts, verified the
ordinary FAIL classification and source/artifact bindings. Remote ownership and
final device state remain unobserved at this point. Host tests, source review,
activity recreation or ordinary instrumentation cannot establish restoration.
That attempt establishes no pending-result device PASS or model measurement.

The separately admitted twelve-query read-only settlement passed with known
cleanup in 4.344 s. It observed unchanged installed33 hashes/UIDs, the APP and
TEST provider processes, absent real-model root and 1,387,520,000 bytes free
userdata. The private Activity was then resumed/focused with no saved bundle;
that is a later observation, not the original failure's cause. Its sealed48-file
index (176,185 bytes) has SHA-256
`9959982a235a7993bb8e32f7973a23e5e80f19211e1082aefb5de3d0b25d7ee1`.

Actual output also corrected the earlier server-only claim: AMS `-p` enables
client dumping even without `-c`. The repaired live-arm proof uses plain server
`dumpsys activity activities` and exact host task selection. Actual Hist spacing
and optional organized display-header syntax are incorporated into the repaired
parser with rejection cases. Raw dumps stay local.

The v2 readiness repair (`f4eb914`, author `01b5660`) passed its full offline
fixture build in 127.953 s with known worker cleanup: 276 tests / 28 suites,
zero failure/error/skip, lint zero errors/five advisories. Final signed APP is
74,157,899 bytes, SHA-256
`fca450386454226c130ddd01c15ef11f64914263fbb4970b2821f67427b9cba9`;
TEST is 2,539,541 bytes, SHA-256
`bb548af5a57b09962269458d22ef8df1f0dc4a4fa349fc612c4dd4b85d183d0d`.
Current audits pass; DEX checks confirm new v2 identity/root and absence of old
pending-v1 literals. Its separate host seal covers51 files / 76,849,531 bytes,
SHA-256 `5079a5079134a05429e7bc63cc27088af9693aadfa0210ad5de1dfaa025dca93`.

The separately admitted captured-identity lifecycle procedure then passed in
14.297 s: 30 known-clean clients, one TEST stop and one APP stop, final own0,
unchanged33 hashes/UIDs, absent real-model root and 1,387,343,872 bytes available.
It cleared no data and made no install/UI/provider call. Its 90-file/210,680-byte
seal, independently rehashed, is SHA-256
`e437f5c06b0c7e91cf18624f4b4d0ce983bcc5eadf0dae95d87ab625322f6f29`.
This is explicit process-stop evidence; it is not a natural-cleanup or successful
restoration result. Repaired execution requires separate admission.

The admitted v2 run reached the actual saved-task interruption: its ordinary
arm START, waiting and armed markers, forced proofs, self-crash, APP absence
and same-record STOPPED to DESTROYED transition were accepted. The saved bundle
was 1,532 bytes. The arm was never PASS. The host then stopped in the system
drawer because the exact TEST root label had no enabled clickable ancestor.
Only Show roots had been tapped; no root/document tap or observer ran.

Original outer execution completed with child rc2 and known cleanup in 22.657 s;
all62 clients were known terminal, including two successful UI dumps. Its
248-file/1,667,702-byte stopped seal is SHA-256
`f0572a36ff3cc5827997f522f07bf371d3facbaa732d6ffea2dc8553b0c04d83`.
The closure helper's first exact arm-summary equality was corrected locally to
the actual accepted schema; its failed helper/receipt are retained. No device
requery, source-oracle change or success classification replaced the failure.

A separately reviewed host continuation re-established the same retained task,
APP absence, original proofs/run, package/UID identities and DocsUI state before
touch. It used an exact TEST-root ListView row profile supported by actual XML
and Android source. It selected that root and the Wrong synthetic document,
then stopped on a same-task null-focus/finishing transition. Its original worker
completed with child rc2 and known cleanup in 15.532 s; all 41 clients were known
terminal. Its 207-file / 1,542,983-byte seal is SHA-256
`899280bfa3f15c77048524db74a3d80d64e8ddc3399d9afa4c6f6f3918208fc2`.
No callback result is inferred from the tap or transient focus record.

The next independently reviewed continuation read the actual first callback:
saved state restored in a different app process, selected=true, CHECKING to
CHECKING, and zero attempts/opens/closes/active descriptors/failures. It verified
the same task and fixed-v2 MISSING UI, then repeated the current-process proof
immediately before a fresh Choose. That tap was consumed; the driver stopped
at another same-task null-focus transition before any subsequent document tap.
The synchronous original worker completed with child rc2 and known cleanup in
8.828 s; all 30 clients were known terminal, with one new UI dump. This proves
stale-result rejection, not successful fresh import or final observer acceptance.
Its independently rehashed 129-file / 1,020,625-byte seal is SHA-256
`c86410cce551d41e6d81e9c3c6260335f0a26dce208d3df8a8374899a9ed8680`.

Continuations preserve the actual outstanding relationship. They do not rearm,
install, bootstrap, configure the provider, dispatch a registry result or replay
already consumed actions. Source and APKs stay frozen throughout each owned
cohort. Known same-task transition records grant passive bounded waiting only;
stable exact foreground and fresh XML remain required before any new action.

The final valid-only continuation requalified the actual callback1, matching
live APP process, immutable history, all installed package/UID identities,
capacity and callback2 absence. It consumed the previous Choose history without
replaying it, waited passively for stable same-task DocsUI, selected the exact
TEST root in this fresh picker and then the Valid synthetic document. Receipt2
records the same restored process/task/run and PICKING to IMPORTING. Separate
actual READY preceded the observer; receipt counters alone were not treated as
asynchronous publication or descriptor-drain evidence.

`observeRestoredPickerAndFreshImport` returned 1 PASS / 0 FAIL. Its assertions
establish exactly two actual callbacks, all receipt jobs terminal with no sticky
error/overflow, exactly one provider attempt/open/close, zero active descriptors
or provider failures, no staging file before native-store reopen, all 63 original
bytes and full SHA-256 after reopen, all six older file hashes unchanged and no
persisted provider grant. The actual selected arm remains an expected crash,
never a passing method.

The original final worker completed with child rc0 and known cleanup in 52.657 s.
All 87 clients were known terminal. Four new dumps made nine across the preserved
relationship, within the combined limit of 16. After observer PASS, freshly
identified captured TEST and APP processes were each explicitly stopped once.
Final observations showed no owned or passive provider processes, all 33 package
hashes and UIDs unchanged, absent real-model root and 1,388,744,704 available
userdata bytes. These explicit stops do not establish natural APP exit or active
inference teardown. No data was cleared or inference started.
The final sealed index covers 253 files / 1,309,542 bytes, SHA-256
`276e85ff4aafde6705e42e4f796a0744b299f45f551cbe9f1e0180f2c115cb6c`.
The coordinator rehashed every entry; independent review separately checked the
raw client pairs, actual receipts, observer result, final gates and commitments.

The selected instrumentation invocations use this argument shape, separately:

```text
am instrument --no-restart -w -r -e waitForActivitiesToComplete false -e class org.locallore.app.ModelPickerPendingTest#armPendingPickerAndTerminateOwnProcess org.locallore.app.modelpickerverify.test/androidx.test.runner.AndroidJUnitRunner
am instrument --no-restart -w -r -e waitForActivitiesToComplete false -e class org.locallore.app.ModelPickerPendingTest#observeRestoredPickerAndFreshImport org.locallore.app.modelpickerverify.test/androidx.test.runner.AndroidJUnitRunner
```

They are parts of the externally owned procedure, not a standalone connected
suite: the first requires a new fixed fixture root and the admitted saved-task
handshake; the second requires actual intervening DocumentsUI callbacks. Existing
fixture data is retained, so blindly repeating the first method must refuse.

The [device report](MODEL_PENDING_DEVICE_2026-10-23.md) and
[independent review](MODEL_PENDING_REVIEW_2026-10-23.md) preserve the admission,
attempt, closure and sealed-evidence details. The 61/13/22/69/26/29/31-case
controller-fixture sets passed their respective admitted phases; they are local
mock/admission checks, distinct from the actual arm and final observer.

The implemented prerequisite is in review; M05.05 and M05.04 remain unchecked.
M01.01 reference-phone availability and the
existing A/#117/#119 holds remain separate gates. Original synthetic bytes do
not establish real-model quality, performance, active SDK teardown, ARM64
execution or power-loss durability. Nothing is merged, released or reconfigured.
Next runnable scoped work: setup launch-failure/held-session recovery, preserving
the model, canonical story state and explicit consent boundaries. Real-model
storage/admission and reference-phone gates remain prerequisites for a full scene.
