# Diagnostic review consent and local egress audit

B101, 2026-11-02. Refs #14 (M10.03; supporting M10.02 host regressions).
Implemented and locally verified for review; full task/privacy/device gates
remain unchecked. No dependency, permission, diagnostic JSON schema, engine/
provider interface or canonical-data change.

## Concrete gap and resulting behavior

MainActivity supplied no-argument Export/Clear/Close callbacks. ShellViewModel
delegated them to the current DiagnosticsController state. After previewA was
replaced by B, a retained A action could export B, clear its later records or
close/cancel B. Existing tests protected frozen bytes after beginExport, old
picker draining and writer cancellation; they did not protect this earlier
rendered-review edge. Diagnostics are bounded metadata: this was a consent
gap, not an observed private-story leak. The separate archive-action PR #341
does not change these diagnostic sources.

Each DiagnosticsUiState now carries an opaque DiagnosticsReview identity.
Open and successful Clear replace it, including when JSON stays identical.
Exporting/notices retain it. The pure diagnosticsActions binder captures the
rendered identity and is used by the actual Dialog's buttons and Back handler.
Main passes that identity to scoped ViewModel entry points. Controller guards
require the current visible, undisposed review before effects; Clear also
retains the existing not-exporting requirement. A stale Close cannot cause
ViewModel fork-context synchronization.

Current-review Close can still revoke/cancel its own pending export. The old
picker tombstone drains before a new picker can start, and late completion
cannot replace a reopened review. Existing no-argument current-owner reset/
disposal/reconciliation paths remain separate. Review identities never enter
JSON, native commands or canonical state. Same-review rotation/unmount callbacks
are not revoked by this token alone: this is review-replacement ownership, not
an assertion of per-mount liveness. [ADR-0005](../adr/0005-local-diagnostic-exports.md)
records that distinction and the existing provider-cancellation limits.

## Source audit scope

Independent reviewers traced source/callers and existing tests rather than
treating keyword absence as a privacy proof:

| Boundary | Bounded source finding | Remaining limit |
|---|---|---|
| Default diagnostic log | Fixed enums, clamped numbers, ASCII <=16KiB, detached snapshot; exact native category maps to enum/UNKNOWN | Not every native SDK or OS log sink |
| Default writer | Explicit content URI, frozen bytes, IO execution, bounded permit through cancellation/cleanup; provider exception text excluded | Cloud-backed providers may sync an explicit export; incomplete writes cannot be undone |
| Runtime traces | Optional finite callback/status metadata; ordinary path leaves these traces unset | Explicit Host trace/Story Lab private capture have separate consent/data schemas |
| Android runtime dependencies | 84 ordinary/88 LiteRT locked runtime coordinates reviewed; named analytics-library entries are analyzer-only | Inventory is not execution or transitive-code absence proof |
| Native/local runtime | Reviewed worker uses a local model path, disables automatic tools and suppresses/discards bounded logs | Root lock contains reqwest/hyper; llama common includes download code, so no repository-wide network-code-absence claim |
| CI/Desktop boundaries | Reviewed source has read-only CI permissions/pinned checkout and local-origin Desktop policy | Not an observed CI/WebView/platform traffic result |

No new automatic upload, account, reporter or cloud-fallback defect was
confirmed in those finite source paths. Actual SDK/OS logging, outbound-traffic
observations and installed offline play remain unverified. The
[privacy contract](../PRIVACY_AND_THREAT_MODEL.md) retains provider, keyboard,
backup and compromised-device limits. No dependency upgrade or promise change
is inferred from this audit; the existing Desktop dependency-risk record remains.

## Actual verification

Base: `027ddbaf298cd05ebdcdf65d716962e783bcad31`.
Tested code tree: `bc3c60f1aef529336ba14c9048e3b4531cee68e2`.
The final PR's only later differences are this report and the ADR clarification.
The six tested paths are Controller, ViewModel, MainActivity, Dialog, the new
DiagnosticsReviewActionsTest and the strengthened Android DiagnosticsDialogTest.
The original eight JVM oracle bytes remain SHA256
`247b27e53daef734e447646bccd34e7173cfa7f75b830caf091fa47e1664a6de`.

| Phase | Actual result |
|---|---|
| Interface-only RED | Both JNI ABIs and Kotlin compile; eight declared JVM methods, six assertion failures, two passes, zero errors/skips |
| First full build | Android-test compilation fails for missing assertSame import; zero new JVM executions |
| Corrected full build | 81/81 tasks execute, both APKs assemble, 419 JVM methods/48 XML suites pass, zero errors/failures/skips; lint0 errors/1 warning/1 hint |
| Main and paired APK audits | Both actual CLI checks pass on the new final artifacts |
| Separate PR #376 candidate audit | Its pinned component/permission checker also passes on the new product; this adds no product dependency on that unmerged PR |

RED is explicitly an additive interface-only stage, not unchanged-main
execution. It exposed scoped signatures and the actual binder while retaining
the old current-state action delegation. Guard logic was then added without
editing the eight original test bodies. The two baseline passes demonstrate
current-close and picker-draining positive behavior. They are not extra tests
to add to the final count: **411 existing +8 new =419** actual JVM methods.

The failed full build copied the previous RED XML before test execution.
That byte-identical inherited result is retained and expressly unqualified;
it is not counted as another run. The missing import was the only source
difference before the successful full rerun. Final task markers, fresh XML,
source/tool before/after joins and exact archives were independently replayed.

The eight methods use the real controller and the same pure binder used by
the Dialog: stale Export/Clear/Dismiss, equal JSON and foreign identities,
empty Clear, busy/notice retention, frozen bytes, current Close, late writer
completion and old-picker draining. Held synthetic writers have bounded
release/cleanup even in RED. They do not open a real provider or execute a
model/engine. The Android dialog test now asserts received token identity;
it **compiled but was not run on Android**. Layout/text/touch targets are unchanged.

Actual builds used installed Java21, Gradle8.11.1, ordinary Kotlin2.2.21,
Build Tools35.0.0, SDK36, NDK29.0.14206865 and Rust1.93.1 on Windows. Commands
start from the physical D: Android root using the verified wrapper JAR:

```text
java -classpath gradle/wrapper/gradle-wrapper.jar org.gradle.wrapper.GradleWrapperMain :app:testDebugUnitTest --tests org.locallore.app.DiagnosticsReviewActionsTest --offline --no-daemon --console=plain --max-workers=2 --rerun-tasks -Pandroid.builder.sdkDownload=false -Pkotlin.compiler.execution.strategy=in-process
java -classpath gradle/wrapper/gradle-wrapper.jar org.gradle.wrapper.GradleWrapperMain :app:assembleDebug :app:assembleDebugAndroidTest :app:testDebugUnitTest :app:lintDebug --offline --no-daemon --console=plain --max-workers=2 --rerun-tasks -Pandroid.builder.sdkDownload=false -Pkotlin.compiler.execution.strategy=in-process
```

The actual requests use absolute Java/JAR paths and owned D: temp/cache
overrides. A stdin barrier admits each child to the frozen current WindowsJob
owner before Java starts. All three phases have known owned-job closure,
unchanged 2,578-file raw source maps and unchanged selected tool pins. Baseline
200.965s and final100.155s are host verification durations, not inference or
device-performance measurements. JNI code compiled for both ABIs; it was not
executed on Android/ARM64. Full Rust/Python/frontend suites were not rerun.

## Final artifacts and preservation

| Artifact | Bytes | SHA256 |
|---|---:|---|
| Product debug APK | 28,012,664 | 53ce76a5d431e6109b51475765845efcae90ead71a33ad676118c50fc1c73c07 |
| Android-test APK | 2,263,376 | c15455a648ff9d3644f1b65940f9c762512c9a620f0a1e953aca5fee683d973f |

Both are new built files, not install/runtime evidence. The separate component
auditor is pinned to PR #376 source SHA256
`ab77044c1a1cad3a8fb6f592439134946c07a7467aed39cf9a05c2f617d451ea`.
The product branch does not depend on or merge that code.

Private output/recovery basename: `2026-11-02-local-egress-v1`. Source and
snapshots, all failures and XML, partial/final APK captures and protocol records
remain retained; no raw private diagnostics, credentials or model weights enter
this PR. Three later review turns failed at model capacity; another
independent reviewer completed the final source/archive/XML review. Those failed
turns are not presented as completed reviews or owner acceptance. The coordinator
checked the final report against that completed review and retained records.

Retaining three source ZIPs plus failed-partial and final APK captures exceeded
the original64MiB controls estimate:97,001,268bytes at the recorded measurement.
That variance remains recorded; the old estimate did not pass retroactively.
Only host-control retention was revised to128MiB before publication. Source
128MiB, synthetic256MiB, generated3GiB and selected recovery512MiB stay unchanged.
Final sampled generated output643,571,613bytes and known job closure pass their
bounds; sampling is not an OS quota or continuous peak proof. Build payloads
stay in place and are not represented as copied selected evidence. The shared
two-root/64GiB AVD ledger/admission budget is unchanged.

The coordinator used a raw-Git D: input snapshot after managed worktree
attachment was unavailable, preserving the clean frozen operator/index and all
existing worktrees. Installed tools remain in supported locations; project
commands/captures/copies and selected caches/temporary settings are onD.
No guest, ADB/phone/model operation, SDK management, settings change, image
retirement/deletion, private upload, release or merge occurred. Knowledge
Android0/4, physical/model/M10.05, actual diagnostic UI/SAF and full M10.03
privacy qualification remain open and require their own fresh authority/evidence.
