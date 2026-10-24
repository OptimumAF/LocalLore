# Receipt-backed debug setup verification - 2026-10-24

Refs #9 (M05.05 prerequisite), #5 (M01.05 supporting). The explicit receipt
candidate route is implemented and its integrated host gates pass. Actual
emulator setup/restart qualification is pending in this execution report.
Full tasks remain unchecked pending complete criteria and owner acceptance.

## Implemented boundary

`CandidateModelAccess` keeps pure path planning separate from suspending
import/full reopen and synchronous IO-only runtime admission. Existing profiles
wrap the unchanged `LocalModelStore`; only all four explicit verification flags
select the receipt route. Context supplies fixed internal no-backup control and
removable app-files data children. Existing publication roots are refused,
never adopted or migrated. Canonical story storage remains internal.

The receipt core retains its global reservation and persistent OS lock. It
publishes a verification stamp only after successful full verification and
source/channel/lock closes. Failure/cancellation clears that stamp. Runtime
admission is noncreating and checks current exact receipt/owner/marker,
whitelist, roots, model metadata and cache directory identity. It permits cache
child writes, without claiming cache confidentiality. The unchanged worker
still hashes the full model before constructing SDK resources and rechecks
admission before initialize/conversation/send. Rust gameplay authority is unchanged.

The [contract](RECEIPT_SETUP_CONTRACT.md), [protocol](RECEIPT_SETUP_PROTOCOL.md)
and [ADR0011](../adr/0011-model-receipt-transaction.md) define scope and limits.
The new fixture exercises the production ViewModel and Compose controls through
fixed source callbacks, not DocumentsUI or an arbitrary Intent-selected source.

## Actual host checks

The integrated receipt invocation used installed JBR17 with the existing offline
Gradle wrapper and JDK21 toolchain, all four profile flags, the exclusive
`.gradle-litert-worker` cache and pinned lint analyzer selection:

```text
:app:assembleDebug :app:assembleDebugAndroidTest
:app:cleanTestDebugUnitTest :app:testDebugUnitTest :app:lintDebug
:app:auditLiteRtDependencies :app:auditLintAnalyzer
--offline --no-daemon --console=plain --max-workers=2
-Pandroid.builder.sdkDownload=false -Pkotlin.incremental=false
-Pandroid.experimental.lint.version=9.4.1
-Porg.gradle.java.installations.auto-download=false
-Porg.gradle.java.installations.paths=C:/Program Files/Java/jdk-21
-PlocalLoreLiteRtVerification=true -PlocalLoreModelSetupVerification=true
-PlocalLoreModelVolumeVerification=true -PlocalLoreModelReceiptVerification=true
--project-cache-dir .gradle-litert-worker
```

Actual result: **340 JVM tests / 35 suites**, zero failures/errors/skips. Lint:
zero errors, 19 warnings. The five added warnings concern conservative
`usableSpace` observations in the synthetic fixture; they do not allocate or
count reclaimable storage toward the unchanged floors. Runtime dependency
audit: 62 artifacts. Analyzer audit: 67 artifacts, version32.4.1,
`check_dependencies=true`, actual analysis work recorded. Both graphs equal the
preceding pinned graphs. No dependency, runtime, model or worker update occurred.

The original owned build completed0 with known cleanup in361,812ms. Its
12,798-byte stdout SHA-256 is
`627231dea50d83318fc726aef897402815fb112f9fc8507e48c718f28ab5c5af`.

The actual APK audit command passed:

```text
python -B -E scripts/audit_apk.py <receipt-app.apk>
  --litert-verification --model-provisioning
  --model-volume-verification --model-receipt-verification
```

It checked exact package/capabilities, private service and four fixed private
setup activities, SDK binary/notice hashes, both native ABIs and16KiB ELF/ZIP
alignment. These are packaging checks, not ARM64/16KiB execution evidence.

| Frozen receipt artifact | Bytes | SHA-256 |
|---|---:|---|
| App |74,867,728|`983f381ed493fdbb8d8d3227a50a164cc6a89ced57cbe0cbeb6dbcefa6f828f7`|
| Android test |1,922,331|`ec35b26743ae7433d51d1d6b4abfa31db888c031d4ccea18b33cdfaa9a234428`|

The final central Python invocation was:

```text
python -B -E -m unittest discover -s scripts/tests -v
```

**559 tests passed**, zero failures/errors/skips,47.438s. Owned execution:
completed0, known cleanup,48,281ms;64,972-byte stdout SHA-256
`599c7aeb8b49bd5335293b44daf19756b375e8536aa7b44dd812534ec72ededf`.
This includes24 APK audit regressions and19 mocked new controller tests.
Mocks cover3+1 exact methods/44 checks, strict proofs/transcripts, real helper
budget validation without spawning, stale/reused restart identities, surviving
processes, owner/cleanup/evidence loss, binding drift and capacity refusal.

The core author separately compiled actual receipt/interface/store sources with
cached Kotlin2.4.0 on installed JDK21, targeting JVM17, and ran36 real-file/core
tests,5.308s. Owned compilation10,079ms and JUnit5,625ms both completed0 with
known cleanup; all21 source/tool bindings remained unchanged. This is not an
Android or Java17-runtime measurement.

Regular SDK and ordinary-build exclusion/regression results remain pending.

## Preparation and review findings

Independent review caught and corrected these defects before device execution:

- Preserve the fixed `NO_SPACE` error rather than redacting it to generic storage.
- Never open the lock inode in a same-process fixture while the transaction holds
  its OS lock; use nonfollowing regular-file/zero-size metadata checks instead.
- Require explicit release to return successfully before cancellation/drain can
  pass; emergency30s checkpoint/source timeouts cannot satisfy the oracle.
- Keep the new controller's outer/aggregate budgets at the unchanged180/165s
  helper limits, with remaining-time caps on every client.
- Exclude the new build output from Git and keep test fixtures private/opt-in.

The initial preparation proposal selected installed JDK21. Review identified
that preparation-toolchain difference; it was retained unexecuted. The selected
v2 uses the previously exercised JBR17. Root and reviewer independently checked
all909 bound inputs/5,046,134,929 bytes, plus token and old registry metadata.
The token was not printed, copied or changed. The new namespace alone receives
the fixed12GiB userdata/8GiB SD/2GiB RAM/two-CPU configuration.

Selected prepare proposal SHA-256:
`67267c43c7d6b0fffb93f4f37101df4bf4e835071e80f03999cdd3c659b7688f`.
Actual preparation completed0, child cleanup/closure verified, prepared record
created. The owned SDK child completed0 in4,125ms; stdout87bytes SHA-256
`f8a408665fb80180169a6ef44d3f071b0da14c493f2dabc40e26871ce45952c8`;
stderr645bytes. No cause is inferred from stderr counts. No image/tool download
or old target mutation occurred.

Run proposal SHA-256:
`347108ad67a41916e818035517ed1b0edc7a3076194a7ba387810f8365042ce9`.
Boot admission and guest results remain pending. A prepared AVD is not boot evidence.

The controller test author retained an initial fake-DF percent-formatting defect
that caused11 mock errors, then fixed the test transport. Subsequent19-test and
central559-test runs passed; this was not a production or guest failure.

## Remaining gates and evidence custody

Private raw evidence lives in new local host/environment namespaces beginning
`D:/LocalLore-receipt-setup-`; no diagnostics or weights are uploaded. The
receipt APK pair is copied create-only and rehashed. Earlier failed/held targets,
old data and immutable evidence are preserved. No model was copied or SDK
inference invoked by these host/preparation checks.

Still required: actual initial/restart UI cohorts, final source/input closure,
separate emulator-owner terminal cleanup and focused PR handoff. Full real
candidate import/SDK inference, DocumentsUI delivery, physical reference phone,
ARM64/16KiB execution, media replacement, power loss, cache confidentiality,
quality and sustained behavior remain unqualified. Existing A/#117/#119 holds
are unchanged. No merge, release, access change or production backend selection.
