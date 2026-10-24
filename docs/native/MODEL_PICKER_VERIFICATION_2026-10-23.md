# Model picker verification, 2026-10-23

Refs [#9](https://github.com/OptimumAF/LocalLore/issues/9), M05.05 provisioning
prerequisite and M05.04 supporting. This packet is based on open, unmerged
[#132](https://github.com/OptimumAF/LocalLore/pull/132), head
`ec16bc1c0749b9f421b01f377ec27a61d85ebc48`. No milestone acceptance, merge,
runtime selection or real-model qualification is inferred.

The corrected picker preparation and fresh-process readback each passed as
separately selected methods on one Android 15/API 35 x86_64 emulator with
4 KiB pages. Final package/UID checks preserved the original 31 packages.
The two earlier failed attempts and the pre-dispatch verifier correction are
retained below. Full M05.05 and physical-device/model gates remain unchecked.

The [contract](MODEL_PICKER_CONTRACT.md) describes the fixed default factory,
conditional fixture profile, provider boundary and two-process test protocol.
Fixture authors and reviewer use separate worktrees; central execution owns
builds. Provider/control/fixture code and model identity are absent from the
ordinary and regular setup app profiles. The real candidate identity remains
fixed and the synthetic fixture never constructs an inference owner.

## Executed host checks

The ordinary profile also passed **203 JVM tests in 23 suites**, zero
failures/errors/skips, and lint zero errors/one warning. Its owned full check
completed exit zero with known cleanup in 57,062 ms; stdout SHA256 is
`42e9fa376caf2eb22dbc7e22a4c686db20f91d63bcc2320db6cd54dc6f7210b9`.
The actual 23,214,204-byte ordinary APP, SHA256
`29c56f9d6b37d030d352ecf78ac983cd515774801b27a1a49ae356095e27c111`,
passed signature, permission and native alignment audits. Its DEX excludes
fixture helpers/Activity/provider and its native entries exclude the SDK.
These sources are excluded from that profile, so the later picker-request
correction does not change this ordinary result.

From `apps/android`, the regular candidate task set was:

```powershell
.\gradlew.bat :app:assembleDebug :app:assembleDebugAndroidTest :app:cleanTestDebugUnitTest :app:testDebugUnitTest :app:lintDebug :app:auditLiteRtDependencies :app:auditLintAnalyzer -PlocalLoreLiteRtVerification=true -PlocalLoreModelSetupVerification=true --project-cache-dir .gradle-litert-worker -Pandroid.experimental.lint.version=9.4.1 -Porg.gradle.java.installations.auto-download=false -Porg.gradle.java.installations.paths="C:/Program Files/Java/jdk-21" -Pandroid.builder.sdkDownload=false -Pkotlin.incremental=false --offline --no-daemon --max-workers=2
```

Adding `-PlocalLoreModelPickerVerification=true` ran the same full task set for
the isolated fixture. Both configurations passed **275 JVM tests in 27 suites**,
zero failures/errors/skips, and lint **zero errors/four unsuppressed warnings**:
one target API advisory, one dependency advisory and two usable-space warnings.
Existing Kotlin/compiler advisories remain visible. The pinned SDK 0.18.1,
Kotlin/Compose 2.4.0, Java-21 compiler/test launcher, Java-17 Gradle daemon,
AGP 8.10.1, Gradle 8.11.1 and independently checked analyzer graph are unchanged.

After the request correction described below, the final regular owned run
completed exit zero with known cleanup in 117,594 ms; its 9,085-byte stdout
SHA256 is `81be4ed4fed805031e23bd6341275ac44146578bb73945b2b30e7b14c3575071`.
The final fixture run completed exit zero with known cleanup in 118,766 ms;
its 9,363-byte stdout SHA256 is
`1d5620d97cbec968c5f65f8452877dd1a37b0d969622a3fb6f28814ad48f94cd`.
Both final XML sets independently confirm the counts above. Initial runs and
artifacts remain retained, including the 295,172-ms fixture run that freshly
cross-built both Rust Android ABIs. The correction changed no native source
or dependency pins; final native tasks were up to date. Cross-building is not
ARM64 execution.

Package-only rebuilds completed with known cleanup in 12,641 ms (regular) and
13,734 ms (fixture). Actual signature, `aapt2` manifest, permission, native ZIP/
ELF alignment and full pinned SDK binary/notice checks passed for both pairs.
The fixture APP has only the real setup launcher; the synthetic Activity is
private. Actual TEST manifest auditing verifies the exact protected document
provider/control pair and process, instrumentation target, no shared UID,
REORDER_TASKS-only permission and no native libraries. The provider is absent
from the APP DEX; fixture helper and Activity are absent from regular APP DEX.

| Profile/artifact | Bytes | SHA256 |
|---|---:|---|
| Regular APP | 73,829,560 | `a4a847be86e6135f93698540f10d9bf448ec0615749a92f9ad8d96850188b275` |
| Regular TEST | 1,755,365 | `6ea5c33f3023280ca304b30f844228760e02279e576902a3ba8d824c37569477` |
| Fixture APP | 73,829,600 | `31d3131612f75972096ef78d843995bbf5d3f1feb811c9b07ffd4563f8a9ae89` |
| Fixture TEST | 1,777,609 | `7aa2495ca37675ac2bf0e72c43f68051b01cc3b0566314d33211c957dd624fe5` |

The closed local host selection contains 591 files/329,530,742 bytes,
including 183 final source snapshots, test/lint XML, terminal receipts and
signed artifact audits. Index SHA256:
`c6b7e68b56a52ffaf92d6b2b98a02b2e166a732f9f0625a24cf115a20abf89f1`.
It supersedes the earlier selection to include the corrected fixture artifact
audit; an omitted required helper argument failed before producing that audit
and the corrected invocation completed. These bounded receipts and aggregate
results are public; raw local evidence and signing diagnostics stay private.

From the repository root, `python -B -E -m unittest discover -s scripts/tests`
passed **194 tests**. After independent review tightened helper-only fixture
DEX exclusion, the final recheck completed in 15,281 ms, known cleanup and exit
zero; the runner reports 14.804 seconds. Its stdout SHA256 is
`38b0282990f0aad9de1bc99200c526c281f2f26bb7a5d480301cbc1c1586048e`.
The original 194-test result remains retained separately. Guard cases cover
leaked helper-only fixture code, fixture Activity export/filter drift,
wrong provider authority/process/protection/grants and control delegation.

Three separate configuration probes fail with their intended fixed guard and
exit one: picker without either prerequisite, picker with LiteRT but no setup,
and an explicit false picker flag. All have known owned-process cleanup.

## Device protocol and limits

The first actual preparation attempt failed its final combined six-launch/
request-flags assertion: **zero PASS/one FAIL**. The 3,495-byte selected output
has SHA256 `db4146b89e657147cdcb329910b64688da7dba6f76ee53a1a414c20514241881`.
Earlier assertions had reached valid publication and fresh-Activity rehash,
but the process receipt is written after that assertion and was not created.
All 22 clients terminated with known cleanup; no stop or restart ran. The
post-failure device state was not queried by that stopped controller.

Investigation of the pinned AndroidX Activity 1.10.1 implementation found that
`OpenDocument.createIntent` omits `CATEGORY_OPENABLE`. The production override
now adds it explicitly, preserving the stream-only import requirement. The
test retains exactly six real requests and checks each request's wildcard
type, local-only flag, openable category and singleton wildcard MIME filter
separately, with bounded count/boolean diagnostics. The first raw failure
does not recover the unrecorded count or individual flag values. Before any
source change, the stopped evidence was sealed: 247 files/77,939,634 bytes,
index SHA256 `8706679edaaf360df31635c1d8d8f6bb9da2be0d6bf0ae6b459f3dcc595d21e4`.

A separately admitted recovery attempt then stopped before any mutation at its
initial process-observation gate. All seven read-only clients terminated with
known cleanup; zero stops, clears, installs or instrumentation ran. Exact
33-package hashes and the new installed UID pair matched. Its process list
also contained nine older TEST `:chooser_test_provider` processes, which the
original absence-only parser rejected. No storage query followed that failure.
The failed recovery selection was sealed separately: 297 files/78,291,445 bytes,
index SHA256 `918d8e0f2d1d6aa876b2a6455bea5b19b5198848b70b094b09f99022fc84da5f`.

Independent inspection matched all nine older TEST APKs to the observed hashes
and verified their actual manifests declare protected discoverable document
providers in that exact process. Their root query returns metadata, and the
official platform provider-cache implementation queries registered roots.
Picker discovery is therefore a supported explanation for their appearance,
rather than directly traced causality. The revised verifier must recognize
only these exact signed TEST process names and freshly observed installed
UIDs as passive rows. It may neither stop them nor treat them as new fixture
ownership. Unknown original main/other processes still stop execution.

The read-only settlement then passed nine queries in 2,984 ms, all terminal
with known cleanup: exact 33 hashes/UIDs, two new owned rows and nine passive
rows, with 1,389,101,056 bytes available. Its local selection index SHA256 is
`826df61adaa74ac43f5aa3296a82e1f769ccddeeef47b7296e564178f094eb5d`.
A revised recovery admission was superseded before dispatch when review found
an LF-only success comparison would reject the observed consistent CRLF.
Strict normalized success parsing and LF/CRLF/malformed-result regressions
corrected that private verifier before any mutation.

The separately admitted recovery then passed in 18,204 ms: all 41 clients
terminal with known cleanup, one stop of the new TEST package, no APP stop,
and exactly one clear of the new disposable APP. Fresh before/after checks
preserved all 33 APK hashes and installed UIDs; the final new owned namespace
was absent. Six legacy passive rows remained and 1,389,264,896 bytes were
available. Natural disappearance of passive rows is not cleanup credit.
No older package was stopped, cleared or replaced by this controller.

The corrected preparation method then passed **one PASS/zero FAIL** in an
individually selected instrumentation run. Its 833-byte output SHA256 is
`a24c44b6fb8278916500ba21d561f04c94570dfe241f87e51ca24147336091b7`;
the test reports 17.614 seconds. The owned controller completed exit zero with
known cleanup in 29,219 ms, all 30 clients terminal/known, zero process stops.
The two new APKs were updated; all original 31 hashes and all 33 installed UIDs
were preserved. Install stderr counts were retained; not every client had zero
stderr. The after-PASS gate observed two owned/three passive rows and
1,387,884,544 bytes available. Actual PASS covers the six per-request flag
checks, descriptor drains, cancellation/disposal, valid publication/reopen and
private process-receipt creation. It does not itself prove process restart.

The separately selected readback method then passed **one PASS/zero FAIL**
after the external verifier observed the new fixture's exact owned namespace
absent. Its 800-byte instrumentation output SHA256 is
`62f27d928a95b3e5607da05adcd58e58bcc590c3a9008c90c7514dd2fe177ba3`;
the test reports 3.259 seconds. The owned controller completed exit zero with
known cleanup in 39,047 ms; all 72 clients terminated with known cleanup.
There were two stops of the exact new TEST package across the before/after
rounds, no APP stop and no clear or installation. Actual PASS verifies a
different process/start tuple, full retained-copy rehash, READY state and no
picker/provider opening. Final checks preserve all 33 APK hashes/UIDs, observe
zero new owned/two passive rows and 1,388,707,840 available bytes. The tiny
copy and process receipt remain in private storage. Only the new disposable
TEST namespace received lifecycle actions; no older namespace was stopped.

The corrected preparation selection is 133 files/918,459 bytes, index SHA256
`956362a1df54866e53d942c5f3bec110e7fb3983e77eabe984b95a3dcffc1817`.
The readback selection is 184 files/508,273 bytes, index SHA256
`77e755f068bc73e2db17b3ae95e77c28ae4a4b0fbdc301088439eb10aafeee48`.
Both are closed local selections with original terminal receipts and raw
client hashes. See the [device report](MODEL_PICKER_DEVICE_2026-10-23.md) and
[independent review](MODEL_PICKER_REVIEW_2026-10-23.md) for scoped ownership and
failure-history review. No raw device identifiers or diagnostics are uploaded.

The exact selected methods are:

```text
org.locallore.app.ModelPickerActivityTest#pickerCancelFailuresBlockedReadAndVerifiedRestartPreparation
org.locallore.app.ModelPickerActivityTest#verifiedCopyReopensAfterActualProcessRestart
```

They must run in separate instrumentation processes, with external process
absence verified between them. The first method requires its confined root
absent and performs no reset. It uses real DocumentsUI/provider grants and
checks wrong bytes/open failure, blocked cancellation, background/recreation/
disposal, descriptor drain, actual native publication and fresh-Activity reopen.
The second rejects the original process and rehashes the retained tiny copy
without opening a provider. Each method's selection and result must be paired
in the raw instrumentation output; an exit code alone is insufficient.

The fixture preserves all 31 preexisting package hashes; only its explicitly
admitted disposable APP/TEST namespace may be stopped. Existing A/#117/#119
holds remain. Phone, real model/Engine, story/turn, ARM64/16 KiB execution,
model quality/performance and SDK teardown remain unqualified. The safe
fresh-controller rejection of a late unrecognized picker result is retained;
saved-selection recovery across process death is not implemented by this slice.
