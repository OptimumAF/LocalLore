# Interrupted-import verification — 2026-10-23

Refs #9 (M05.05 prerequisite; M05.04 supporting). Stacked on open, unmerged
PR #134 at `32161fe743c7a9f8fec22395261b8de35b2d41f0`. This packet adds
verification fixtures and stricter artifact audits; production import, gameplay,
inference and canonical-event code are unchanged. Read the
[contract](MODEL_INTERRUPTION_CONTRACT.md), [device report](MODEL_INTERRUPTION_DEVICE_2026-10-23.md)
and [independent review](MODEL_INTERRUPTION_REVIEW_2026-10-23.md).

## Frozen implementation

Author source was integrated as `54e6034`; central host/audit/contract work is
`95bdfdf`. Final API-30 test filtering is `24742e67e0274fc1e4576f4ec6d20b542982ac4d`.
The last change replaces test `@RequiresApi` annotations with the runner-aware
`@SdkSuppress(minSdkVersion = 30)`; actual runtime API guards remain. Skipping
the methods cannot satisfy the admitted API-35 interruption/recovery protocol.

No dependency, SDK/model pin, production minimum SDK, lockfile or native source
changes. Builds use the existing cached SDK/toolchain and pinned candidate
graph, offline with automatic SDK/Java downloads disabled. The unchanged
LiteRT-LM 0.18.1 binaries and notices are hash-checked. Both Android ABIs are
packaged and checked for native 16 KiB alignment. Cached unchanged Rust outputs
are reused; this does not claim new ARM execution.

## Host and artifact checks

The owned Windows build wrapper applies an input barrier, a 900-second deadline,
a 2 MiB output limit, and a Job owning the build descendants. Every run listed
below returned with known client/descendant cleanup, including failures.

| Final selection | Result |
| --- | --- |
| Script regressions, `python -B -m unittest discover -s scripts/tests` | 195 PASS, 17.255 s |
| Ordinary Kotlin/JVM/lint regression | 203 JVM tests / 23 suites; zero failures, errors or skips; zero lint errors, one `GradleDependency` advisory; 16,703 ms owned run |
| Regular model-setup candidate | 276 JVM tests / 28 suites; zero failures, errors or skips; 53,047 ms owned run |
| Explicit model-picker fixture | 276 JVM tests / 28 suites; zero failures, errors or skips; 98,109 ms owned run |
| Regular and fixture lint | Zero errors; four existing advisories each (`OldTargetApi`, `GradleDependency`, two `UsableSpace`) |
| Final regular and fixture APKs | Signatures, identities, actual manifests/permissions, launcher/provider boundaries, SDK notices and native alignment PASS |
| Candidate analyzer/dependency checks | Locked SDK and actual analyzer/model graph audits PASS in both profiles |
| Independent controller pure fixtures | 42 PASS, zero failures/errors/skips; device dispatch mocked, 18,782 ms |

The private sealed host selection contains 261 files / 155,162,191 bytes,
including failed-run logs, final XML/lint/dependency reports, copied signed APKs
and 48 frozen source files. Index SHA256:
`fc4f16b481737e039826eaabef1e5f475986c9d72a57602c10e0b3cda8e25de7`.
Raw local diagnostics and APKs stay private; this aggregate is an integrity
receipt, not a claim that the private files are publicly downloadable.

Candidate builds select `:app:assembleDebug :app:assembleDebugAndroidTest
:app:cleanTestDebugUnitTest :app:testDebugUnitTest :app:lintDebug
:app:auditLiteRtDependencies :app:auditLintAnalyzer` with `--offline --no-daemon
--console=plain --max-workers=2 -Pandroid.builder.sdkDownload=false
-Pkotlin.incremental=false -Pandroid.experimental.lint.version=9.4.1
-Porg.gradle.java.installations.auto-download=false`, the existing Java-21
installation, both LiteRT/model-setup verification flags, and the exclusive
`.gradle-litert-worker` project cache. The fixture adds only
`-PlocalLoreModelPickerVerification=true`. See the Android README for complete
toolchain setup; local absolute paths remain private.

The ordinary regression selects `:app:compileDebugKotlin
:app:cleanTestDebugUnitTest :app:testDebugUnitTest :app:lintDebug` offline using
the ordinary `.gradle` cache and excludes the unchanged Rust cross-build task.
It does not claim a new ordinary APK package or device run.

The new host process test passed in both final selections (regular 0.330 s;
fixture 0.269 s). A child performs the actual store import, returns 17 bytes,
then blocks its next read while holding the OS lock. The parent verifies
competing inspection/import refuse BUSY without opening a source, kills/reaps
that exact child, and requires actual lock reacquisition within five seconds.
Fixed staging is recovered, other/cache/lock contents survive, and a fresh full
import and rehash succeed using the labeled host publication substitute.
The Windows filesystem returned no Java file key: persistent inode identity
is not claimed there. BUSY is the only tolerated transient during the bounded
post-death wait; it never counts as successful recovery.

## Final signed synthetic pair

| Artifact | Bytes | SHA256 |
| --- | ---: | --- |
| `.modelpickerverify` APP | 73,829,632 | `0777a0c81a601a345170c4a3203cf25c09742baab0120a6ec461bfce1eebe49c` |
| Corresponding TEST | 2,509,313 | `21aa7e166e6128c26ace7dbd6205fb2ef311c03c4439f6cfb9386f66404f20dc` |

The APP audit requires the new non-exported interruption Activity with no filter,
both synthetic Activity implementations in DEX, and no TEST/provider code in
APP DEX. Ordinary/regular profiles reject leaked interruption helper markers.
The TEST retains exactly the existing protected document/control providers,
fixed target, no native libraries and only its existing test permission.

## Failed attempts retained

The initial new host test did not compile because Android's test bootclasspath
lacks `ProcessHandle` and `Redirect.DISCARD`; supported equivalents replaced
them. Subsequent child readiness failures were a harness launch-path bug:
`javaClass` inside `runBlocking` resolved the coroutine receiver, omitting the
child test class location. Explicit `Child::class.java` fixed that omission.
A later host run exposed the absent Windows file key; the test now asserts
nonempty lock contents and conditions key comparison on actual availability.
The next run observed post-death BUSY; the final test waits for real bounded
OS-lock reacquisition while requiring unchanged staging after each refusal.
These runs remain failures, not interruption passes.

The first complete fixture build compiled and ran its JVM tests but failed lint
with three `UseSdkSuppress` errors. The final runner-filter correction and full
rerun passed. No lint baseline, lint-check suppression, dependency upgrade or test
oracle relaxation was used to bypass that failure.

## Qualification limits

The arm intentionally cannot PASS. Only its exact marker/private proof/process
observations can establish expected interruption; recovery needs a separate
ordinary PASS. Actual emulator observations belong in the device report.
The independent controller's pure tests do not substitute for those observations.

One admitted Android 15 / API 35 x86_64 / 4 KiB emulator cohort actually ran.
The arm emitted its exact finite marker and expected process-death result,
with no method PASS. A separately selected recovery reported one PASS, zero
FAIL, confirming the persisted 17-byte stage before store recovery, new process,
actual consumer/writer drain, preserved old fixture/proof/sentinels/cache, and
fresh explicit valid selection/native publication/full rehash. The owned run
completed in 51,000 ms with 64 known-clean clients; the proof/absence/recovery
dispatch gap was 0.421 s. Only the disposable pair was updated; all other 31
hashes and all 33 installed UIDs were preserved. Final own processes: zero;
recognized passive provider observations: two. One exact TEST stop, zero APP
stops, zero APP clears. Device evidence is recorded in the separate report.
Its closed private selection contains 193 files / 548,138 bytes; index SHA256
`4547ca25e356b5976a83d1059b0bf8f09efcc51b522091f269f4bf0f0fac4743`.

Pending-picker framework callback restoration remains unimplemented/unexecuted;
normal instrumentation force-stops its target and cannot establish that gate.
The existing fresh-controller rejection policy remains unchanged. Synthetic
copies do not qualify real-model import/inference, active SDK teardown, phone
performance or narrative quality. A/#117/#119 holds, ARM64/16 KiB execution,
power-loss durability and full milestone checkboxes remain unchanged. No model
weights, private stories or raw device diagnostics are published.
