# Android receipt transaction checks — partial qualification

Refs #9 (M05.05 prerequisite), #5 (M01.05 supporting). Under review; full task
checkboxes remain unchecked. Stacked on the unmerged host receipt proof PR144.

**Actual Android result: 3 PASS / 1 FAIL.** Accept/reopen, cancellation across
acceptance and foreign/incomplete-data refusal passed on B. Process-death
recovery failed at its first remote START acknowledgement. The corrected
service compiles and passes host checks, but its Android rerun is **blocked
before admission by APK staging headroom**. This packet does not qualify that
process-death path, activate the receipt store or run a model.

## Implemented boundary

The opt-in volume debug build alone contains a fixed original 63-byte fixture,
four instrumentation methods and a private same-UID `:receiptproof` service.
Trusted Context anchors and unchanged AndroidModelVolume selection/admission
derive all paths. The fixture invokes the existing ReceiptModelTransaction;
ordinary and regular SDK builds exclude the fixture/service/test code and
service declaration. No runtime/model dependency, SDK graph, permission,
launcher, backup exclusion, native library set or active setup route changes.
Canonical storage and Rust gameplay authority are unchanged.

Tests assert actual bytes, ownership records, exclusive markers, close counts,
refusal preservation and coroutine cancellation before recording their proofs.
The process test is designed to prove cross-process OS contention, bounded
binding release and actual child death while holding the lock, then source-free
recovery. Its planned assertions are not evidence that they passed.

See the [protocol](MODEL_RECEIPT_ANDROID_PROTOCOL.md),
[device report](MODEL_RECEIPT_ANDROID_DEVICE_2026-10-24.md) and
[independent review](MODEL_RECEIPT_ANDROID_REVIEW_2026-10-24.md).

## Actual checks and compiled sources

| Check | Result |
|---|---|
| Final repository script suite | 471 tests, all pass; includes 22 mocked receipt-controller tests and 3 new APK-audit tests |
| Initial volume SDK build | 323 JVM tests / 33 suites, zero failures/errors/skips; lint 0 errors / 14 warnings |
| Corrected volume SDK build | 323 / 33, zero failures/errors/skips; lint 0 / 14 |
| Regular SDK build | 323 / 33, zero failures/errors/skips; lint 0 / 9 |
| Ordinary build | 206 / 24, zero failures/errors/skips; lint 0 / 1 |
| Packaging | All app/test pairs assembled and signatures verified; private service, permissions, backup exclusions, code exclusion and native-library audits pass |
| Dependency/analyzer audits | 62 runtime / 67 analyzer rows unchanged from preceding volume/regular SDK graph; analyzer execution did work |

Existing pinned tools: Rust 1.93.1, NDK 29.0.14206865, Gradle 8.11.1,
AGP 8.10.1, Kotlin 2.4.0 for SDK profiles (2.2.21 ordinary), LiteRT-LM 0.18.1;
JBR 17.0.6 runs Gradle and
existing JDK 21.0.4 runs the SDK lint analyzer. Builds were offline with SDK/JDK
downloads disabled, two workers and a bounded owned Windows Job. The initial
builds cross-compiled native libraries for both packaged ABIs; packaging them
does not establish ARM64 execution. The corrected build reused unchanged
native outputs. No Rust source changed or Rust test execution is claimed here.

Initial compiled source: `4d06b51ca4b9c531af70d0ad7687d1a763c61635`.
Initial integrated controller: `95d6722f81bed8077f0d0ed4fbd4556e2f41b454`.
Corrected compiled source: `5fcb7246c21f6d5ef5fa4e0816215f0d8e8cf32c`.
Final controller/protocol check source: `5e62e23d372e690deefb2654fb99fed50e6374e1`.
All Android source rows at the final check equal the corrected compiled
snapshot. Later report commits do not change those sources.

Actual final script command: `python -B -E -m unittest discover -s scripts/tests -v`.
It passed in 19.826 seconds; its owned execution completed returncode 0,
cleanup true, 20,375 ms, stdout 54,773 bytes SHA256
`6f05935794dd49b7d4d560acf7fadb6b336df90e142af657b8b5fe01fbdf731b`.

The build worker invoked GradleWrapperMain from the existing JBR in
`apps/android`, using these tasks and options:

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
--project-cache-dir .gradle-litert-worker
```

Volume adds `-PlocalLoreModelVolumeVerification=true`. Ordinary removes the two
SDK audits, lint override, JDK21 path, SDK/setup flags and separate project cache.
Exact worker argv/environment and original terminal receipts are retained in
the sealed evidence below. Lint/compiler warnings remain visible; no suppression
or reserve reduction was introduced. `git diff --check` passes.

Corrected volume owner: completed 0, cleanup true, 135,937 ms, 9,633 stdout
bytes SHA256 `c171435bbc3faa524572b999f6a383b746e59c2f6fa5663cca3a38eb209c4731`.
Regular owner: 319,078 ms, 12,243 bytes SHA256
`9b5f7e26fde3fb724e26920969663385200bd9e01636a5ce27237009f51be5e8`.
Ordinary owner: 356,453 ms, 8,927 bytes SHA256
`2e6ac03cc4ca38012d1c7a5f98c8e6401a0d3e87caae6071f8256057c29a3fb8`.
Both also completed 0 with known cleanup. Original handles were consumed;
intermediate observation timeouts were never counted as terminal results.

## Android failure, correction and recovery

Only existing B received targeted calls: Android API35, x86_64, 4 KiB pages,
one admitted public volume. A remains on its existing hold. The preceding
read-only readiness observed four emulators and zero other connected devices;
that inventory is not proof of a physical-phone test.

The first full controller updated only its isolated app/test pair and selected
the four-method class in one ordinary instrumentation invocation. Actual runner
time: 17.876 seconds, 3 pass / 1 fail. Its client exited 0 despite the failing
test; the strict parser correctly refused qualification. The owned outer child
completed returncode 2, cleanup true, 30,844 ms. All 25 client results were known;
no after-state/proof reads followed the failure.

The remote exception did not identify the failing service predicate or received
flags. Independent official-source review demonstrated that Android forwards
framework flags on synchronous Binder calls, making the old `flags == 0` check
incorrect. The correction requires no FLAG_ONEWAY and a nonnull reply while
retaining exact identity, UID, interface-token and no-payload checks. Fixed
bounded messages distinguish future refusal stages. Fresh v2 case/proof roots
preserve v1 data; the bytes identity, wire token/layout and proof schema remain
unchanged. Neither the sole cause nor a live success of this fix is claimed.

A separate admitted read-only recovery completed 29 clients with no installs or
instrumentation. It verified current 35 APK/UID identities, actual owned/passive
counts both zero, the six existing regular v1 proof files with empty markers,
all three closed check maps and one historical parent identity. No process
proof exists. It checked v2 proof-root absence; it did not remeasure current
candidate-root absence. Owned result: completed 0, cleanup true, 8,781 ms,
290 stdout bytes SHA256
`0152daed5d2879aeb69990e6e4ea1178628b533bf42df5da1f0bc77952e9858d`.

## Capacity gate and remaining work

Recovery measured 1,223,741,440 available userdata bytes. The unchanged
controller floor is 1,207,959,552, leaving 15,781,888 bytes. The corrected APK
pair is 76,755,379 bytes. Reserving it above that floor requires at least
1,284,714,931 bytes: a 60,973,491-byte shortfall before uncalibrated installer
overhead. The earlier update's observed 74,911,744-byte decrease has no proven
artifact-level cause. Reclaim or space-neutral reinstall is not assumed.

The final controller validates both bounded APK lengths and pinned hashes and
subtracts both incoming sizes from measured headroom before its first install.
Tests prove exact-boundary success, one-byte-short refusal with zero installs/
instrumentation, and a changed or empty test APK refusing before app update.
This necessary reserve does not itself qualify installer overhead. No corrected
v2 authorization, install or instrumentation ran; no floor, file or emulator
configuration was changed to obtain a pass.

Next runnable task: separately claim a read-only capacity settlement or a larger
isolated test environment, preserving all old data and identities. Establish
actual staging headroom, then create a new reviewed proposal/admission for the
corrected four-method v2 cohort. Do not reuse consumed authorizations or roots.

M05.05/M01.05 full gates remain blocked. No SDK inference, model transfer,
physical-phone, ARM64, 16 KiB, cache confidentiality, power-loss durability,
media-swap, model-quality or sustained-runtime result follows. Synthetic guard
revocation is not physical removal. A/#117/#119 holds and the real-model copy
capacity gate remain. No merge, release or access change occurred.

## Private evidence and public provenance

Raw diagnostics and device identities remain local. Independent review rehashed
the following final indices and source/artifact bindings:

| Private evidence namespace | Files / bytes | Final index SHA256 |
|---|---:|---|
| Initial host | 2,946 / 213,227,823 | `ec105395b3d0a158ebff426ca23c958d5e1648e9c8ab21fab031d231574a5b4d` |
| Initial device | 178 / 86,270,754 | `f00b8696e3677616a830b7ac226d7de4928da3252dbab8d7cc33704cb91ab79b` |
| Corrected host | 2,851 / 110,206,738 | `63bf622725db993b92069c3258c93ea94bc493f5521ceedfebb31a7872d25dbd` |
| Read-only recovery | 75 / 115,994 | `759a743b82ea98c62e23d958de6c663e763cb493349ad6366d48840f5836fad8` |
| Final controller checks | 1,445 / 103,451,922 | `f363993e4390a79e3712a267642e200afcd8485b1ed618248a224db5106a0461` |

The initial 25 admitted bindings are completely archived in its v2 frozen-input
index `ea603dcfde6ebea29f7d77672e35b7fb57829194a1a0e28be3d538f662cb2b6a`.
Its incomplete first archive stopped on a correctly detected changed live
protocol; those partial bytes were preserved and are not the final binding.
The complete archive resolves repository files through the admitted 95d6722
snapshot. Recovery's 37 bindings are completely archived through the admitted
2edb54e snapshot, index
`9dc7db2a357f15b103c9be8b3edf5685f0bf1f37796cd1a0d579c93437011090`.
Final 1,394-file source snapshot / 16,337,466 bytes, index
`9e5d0894ebe1488dab80087c46cd70740ad741dfa50341b3326856185b62232b`,
binds the final central script checks. Sealed namespaces are not reused.
