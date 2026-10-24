# Receipt-backed debug setup verification - 2026-10-24

Refs #9 (M05.05 prerequisite), #5 (M01.05 supporting). The explicit receipt
candidate route is implemented and its integrated host gates pass. All three
initial emulator UI methods passed. The controller then refused its process
gate; restart and host proof-read qualification remain incomplete.
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

The regular SDK build also passed340 tests/35 suites, zero failures/errors/skips;
lint0errors/9warnings. Its APK audit passed and excludes receipt test helpers.
Owned build completed0 with known cleanup,335,047ms;12,264-byte stdout SHA-256
`a33fc5f97339442baedbed260b8b3217030c40db99e5afec908c3dd5a56839e8`.

The ordinary app passed206 tests/24 suites, zero failures/errors/skips;
lint0errors/1warning. Its APK audit passed with four native libraries and no SDK
or receipt helpers. Owned build completed0 with known cleanup,363,250ms;
8,937-byte stdout SHA-256
`1943968f21f4a7483451b81b44e831546c401a665f95f6b374b15ba3b3a53f53`.

Six actual Gradle configurations refused with their exact expected diagnostics,
each returning1: explicit false receipt flag, missing volume, missing SDK/setup,
mixed picker, release task, and wrong project cache. The owned verification
completed0 with known cleanup,68,187ms;4,703-byte stdout SHA-256
`2826a3adc2b2a267a55c7fd9bbf40f4af3ec5e96f5aaa0860e811cd61cb89d94`.

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
Actual guest identity subsequently matched API35/x86_64/4096-byte pages. This
is emulator execution, not physical-phone or ARM64 qualification.

The controller test author retained an initial fake-DF percent-formatting defect
that caused11 mock errors, then fixed the test transport. Subsequent19-test and
central559-test runs passed; this was not a production or guest failure.

## Actual guest result and stopped restart gate

Execution source is `4b6c2db48c342b13b2c6b9e6cc8e599eab003dc2`. Its actual-byte
snapshot contains1,418 files/16,705,626 bytes; source-index SHA-256
`9a1cefc913f9419b9a1bf05c7c9c3e7d9c9e6a37588cf5228f70e8f9df2149d2`.
The app sources match the receipt compilation; all911 non-Markdown snapshot rows
remain identical after execution. Only documentation changed afterward.
Independent review rehashed the snapshot and46 admitted guest inputs.

Guest proposal SHA-256:
`8f5504473d9ae244f5967027d2dec1185479f8d4a7119c64463349635a624614`.
The source-bound live lease was checked before and after each of36 actual
clients. Both exact APKs installed on the fresh target without replace mode.
Initial LocalLore inventory was empty; installed inventory was exactly the
two packages with distinct discovered UIDs. Userdata available was11,350,724,608
bytes before installation and11,273,560,064 afterward, above the unchanged floor.

The one ordinary initial instrumentation invocation actually passed:

- `importsAndRechecksThroughActualReceiptSetup`
- `cancelsBeforeAndAfterAcceptanceThroughCompose`
- `disposedScopeRetainsSourceUntilActualDrain`

The retained runner bytes independently parse as3PASS/0FAIL. Its raw2,165-byte
stdout SHA-256 is
`5f43de09289442850b97da8a15f7fe6713babe661168cfc93190ff7867550dc1`.
These methods exercise the real receipt access class, actual setup ViewModel and
Compose controls, including cancellation before/after acceptance and disposal
with a still-owned blocked source. Successful synthetic callbacks do not qualify
DocumentsUI or real-model provisioning.

The after-stage process inventory contained no APP target process, but retained
the known TEST APK main process under its distinct installed UID. The frozen
controller required both absent, so it stopped before proof reads and the
second instrumentation invocation. Do not call this a restart pass, a test
failure, an all-quiet result, or successful44-check host proof validation.
No final facts or proof-read records were produced. Final capacity was not
observed by this stopped controller.

All36 actual clients completed0 with known cleanup. The owned qualification
worker completed2, known cleanup,65,734ms;345-byte stdout SHA-256
`579d700003ef2b99b9de7d158235675dce653a6eac14a0e69717ef2c4ce7e5cf`,
stderr0. The original outer tool execution was consumed terminal nonzero
(`exit_code=1`); this is distinct from the recorded worker returncode2.

A separately admitted continuation was proposed in ticket comment6387480676,
then deferred in6387504095 before any implementation or call: the original
owner lacked a comfortable full source/test/admission/cohort/closure window.
No continuation source or test result is claimed. The next runnable task is to
qualify a separate controller that records the exact TEST helper independently
of required APP absence, rejects foreign/new process rows, and runs the3+1
sequence on another fresh admitted namespace. Keep the original all-quiet
refusal unchanged; never silently adopt its proofs as a completed run.

The exact stop request closed the original emulator owner. Its original tool
handle was consumed terminal0; owner status `stop_requested`, cleanup and
immutable/default-registry/token closure verified,920,000ms. Owner stdout13,805
bytes/stderr214 bytes; owned worker returncode1 reflects job termination and
does not change the guest test result. All three original host process IDs were
absent afterward and the owned port pair was free. The saved virtual disks were
retained. Their reported sizes are metadata only, without a post-run disk hash
or graceful guest-flush/power-loss durability claim.

## Remaining gates and evidence custody

Private raw evidence lives in new local host/environment namespaces beginning
`D:/LocalLore-receipt-setup-`; no diagnostics or weights are uploaded. The
receipt APK pair is copied create-only and rehashed. Earlier failed/held targets,
old data and immutable evidence are preserved. No model was copied or SDK
inference invoked by these host/preparation checks.

All admitted inputs are archived locally. Root sealed the final inventories;
the independent reviewer rehashed every entry with zero mismatches:

| Private inventory | Files | Bytes | Index SHA-256 |
|---|---:|---:|---|
| Host |1,570|197,304,811|`64c1267450678c0fdd161ee318fa005c1b714939f1022917b2a03d644b9b7cb9`|
| Environment |23|561,229|`55fb2c86480db40f4612c526deac066ff85ec826438410a44e59fe9501529115`|
| Device |129|86,124,753|`a8a7faad8d2e82cb73baa73def32a7f483b4e31c21c9d14fc1453ab363ac050c`|

Still required: the separately qualified restart/proof-read cohort. Full real
candidate import/SDK inference, DocumentsUI delivery, physical reference phone,
ARM64/16KiB execution, media replacement, power loss, cache confidentiality,
quality and sustained behavior remain unqualified. Existing A/#117/#119 holds
are unchanged. [Draft PR147](https://github.com/OptimumAF/LocalLore/pull/147)
is stacked on unmerged146. Full M05.05/M01.05 remain partial and in review;
M01.01 remains blocked on an established authorized reference phone. No merge,
release, access change or production backend selection.
