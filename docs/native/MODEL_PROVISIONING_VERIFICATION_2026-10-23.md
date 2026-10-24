# Local model setup verification, 2026-10-23

Refs [#9](https://github.com/OptimumAF/LocalLore/issues/9), M05.05 provisioning
prerequisite and M05.04 supporting. This partial implementation depends on open,
unmerged [#130](https://github.com/OptimumAF/LocalLore/pull/130), head
`cb251e7145f0a7038a0a1bd7976035bb95d957d2`. It is not milestone acceptance,
a production backend selection or a real-model demonstration.

## Implemented behavior

The [contract](MODEL_PROVISIONING_CONTRACT.md) describes the explicit
`org.locallore.app.modelverify` debug candidate. It requests an existing local
file, verifies a fixed built-in artifact identity, publishes a private copy
without replacing an existing destination, and rechecks it before enabling
play. Setup, copy and verification run on IO; cancelled or disposed controllers
cannot attach stale results. A blocking provider retains its slot until actual
return. No download, persisted provider grant, network capability or gameplay
authority is added.

The play Activity constructs the existing workspace transport with the paired
concrete LiteRT owner. Its process-wide attachment reservation prevents a second
runtime from overlapping an uncertain predecessor. Ordinary builds retain
their scripted construction. Rust still validates proposals and commits
accepted outcomes. The app's story, archive and fork implementations are shared,
and no storage schema changes in this packet. A narrow Rust JNI helper handles
atomic fixed-name model publication; it adds no gameplay authority.

## Host checks

The coordinator executed the checks; independent agents authored the store,
setup controller and source review in separate worktrees. Their authors did
not claim compilation or device execution. The device executor owns separately
admitted Android runs described in the [device report](MODEL_PROVISIONING_DEVICE_2026-10-23.md).

From `apps/android`, with the installed Java 21 compiler/test launcher configured
and the Java 17 Gradle daemon, the complete candidate task set was:

```powershell
.\gradlew.bat :app:assembleDebug :app:assembleDebugAndroidTest :app:cleanTestDebugUnitTest :app:testDebugUnitTest :app:lintDebug :app:auditLiteRtDependencies :app:auditLintAnalyzer -PlocalLoreLiteRtVerification=true -PlocalLoreModelSetupVerification=true --project-cache-dir .gradle-litert-worker -Pandroid.experimental.lint.version=9.4.1 -Porg.gradle.java.installations.auto-download=false -Pandroid.builder.sdkDownload=false -Pkotlin.incremental=false --offline --no-daemon --max-workers=2
```

The first cold build completed in 374,000 ms with known Windows Job cleanup.
It freshly built both Rust Android ABIs. After the trusted-storage-anchor fix,
that intermediate task set completed in **106,641 ms**, exit zero with known cleanup.
Its retained stdout SHA256 is
`cd721538bd479b2b6712b23c17e0b5b87d9534ced064ae95dace26c5c6855e4f`.

The later publication replacement first completed in 138,984 ms, with 275 tests
passing, before review identified different ARM64 directory-open constants.
That build and its exact source/results remain retained and superseded.
After correcting the constants, the final full task set freshly rebuilt both
Rust ABIs and completed in **40,969 ms**, exit zero with known cleanup. Its
7,374-byte stdout SHA256 is
`965d3302c945e57021752c075c32ea98c43ddb6ba46c5a0653784047edd65f94`.
The subsequent final package-only rebuild completed in 12,735 ms, also exit
zero with known cleanup. Kotlin/lint results reused the preceding unchanged
Kotlin sources; the per-ABI correction changed only Rust constants.

- **275 JVM tests passed**, 27 suites, zero failures/errors/skips. New cases:
  25 store, 16 setup-controller and three process-admission tests. These cover
  actual host file publication/reopen, low space, wrong/truncated/excess bytes,
  source failures, no-clobber races, stale staging, symlinks, blocked provider
  open/read/close cancellation, stale/disposed UI results and constructor failure.
- Lint: **zero errors, four warnings**, unsuppressed. Two `UsableSpace` advisories,
  one dependency suggestion and one target API advisory remain. The import
  reserve is a conservative preflight, not guaranteed allocation or a measured
  runtime cache budget. Ordinary compiler/test advisories remain visible.
- The existing pinned SDK/analyzer audits passed: dependency checking enabled,
  exact 67-artifact analyzer graph, analyzer 32.4.1, SDK 0.18.1 and Kotlin
  reflection/stdlib 2.4.0 present in the analyzed models. Main analysis executed
  for the publication Kotlin source set; the subsequent
  Rust-only correction and package work reused that unchanged Kotlin analysis.
- The final ordinary Kotlin 2.2.21 app independently passed **203 JVM tests**,
  23 suites, zero failures/errors/skips; lint zero errors/one dependency advisory.
  This final 177,485 ms build freshly built both ordinary Rust ABIs and assembled
  the ordinary APK; it supersedes the earlier check that skipped native work.
  Its stdout SHA256 is
  `9ad2d5146ba4a78f403f4f6301d73b50533788d56fd62ed8e6230f13a20d6cec`.
  The actual signed 23,214,204-byte ordinary APK SHA256 is
  `29c56f9d6b37d030d352ecf78ac983cd515774801b27a1a49ae356095e27c111`.
  Manifest/permission and four-library 16 KiB alignment checks pass; the setup
  and play Activities, LiteRT SDK libraries and publication JNI export in both
  Rust libraries are absent. The 38-file / 36,811,287-byte closed ordinary index
  SHA256 is `89a15340bd1fc3212161dd185fbb7645ab8213916cda1b99ba0b08a25b34d539`.
  Independent rehashes match. Existing locks and SDK pins are unchanged.
- From the repository root, `python -B -E -m unittest discover -s scripts/tests`
  passed **192 tests** after the manifest-audit correction, 14.617 seconds;
  owned execution completed in 15,047 ms with known cleanup. Thirteen APK-audit
  methods include hostile package/permission/launcher/export/alias variants.
  Rust domain suites were not rerun: gameplay source did not change. The added
  Android-only JNI module was compiled for both ABIs and executed in the
  synthetic x86_64 Android tests.

All process handles reached authoritative terminal states. Observation timeouts
did not trigger replacement runs. The first successful source/results and the
intermediate warning correction remain retained. A private preparation call
initially used a Python `Path.write_text` option unavailable in the installed
interpreter; it failed before any build and was corrected using `open`.

## Artifact checks and retained oracle corrections

The candidate is built with the existing debug-only SDK graph: LiteRT-LM 0.18.1,
Kotlin/Compose 2.4.0, Java 21 tooling targeting 17, Gradle 8.11.1, AGP 8.10.1,
NDK 29.0.14206865 and Rust 1.93.1. No dependency is introduced or upgraded.
Exact current artifact provenance and official API/storage sources are in the
[independent review](MODEL_PROVISIONING_REVIEW_2026-10-23.md).

Actual `aapt2` inspection establishes the sole setup launcher, nonexported
scripted/play Activities, both candidate Activities using `singleTask`, no
shared UID and only the app's signature receiver permission. Actual signature
verification passes for both exact APKs. ZIP/ELF checks find six 16 KiB-aligned
native libraries; both publisher SDK native hashes and complete license/notice
assets match the frozen identities. Keeping full mixed-component notices does
not establish complete redistribution clearance.

The first launcher audit stopped because `aapt2` prints numeric launch mode as
decimal `2`, while the initial oracle required hexadecimal `0x2`. The corrected
oracle accepts only equivalent numeric two; regressions cover both forms and
reject another mode. The original helper/partial audit remain retained. An
initial local repack comparison also required identical ZIP entry order. A
subsequent comparison established identical unique names and decompressed bytes
for all 156 app and 121 test entries; only ZIP layout/signing changed. This
equivalence belongs to the initial pair. Corrected-source APKs were separately
repackaged and audited, without claiming a second independent entry comparison.

Anchor-corrected APK identities (second failed cohort, superseded by publication fix):

| Artifact | Bytes | SHA256 |
|---|---:|---|
| App | 73,809,384 | `24f59ee6c9d8fbb0932435989af888891c5f13df77c505f87a5fbc87da2c1fce` |
| Test | 1,755,057 | `44b1e3889f4cc764f2076edf666acad50e2ce6a4fc6fc3edb88698135ae58eb4` |

That cohort's instrumented source SHA256 is
`1e2b93f17f044a0f656a988ce88976e069961ee95b1a3f88d8301d16e2347713`.
APKs, raw diagnostics, provider identifiers and private device paths stay local.
No weights are bundled, copied, initialized or generated with by these checks.

The final publication-corrected APKs are separately audited:

| Artifact | Bytes | SHA256 |
|---|---:|---|
| App | 73,829,560 | `228ec0aa4a742707df3a73c4fe14509a7047d3cd3bc7e20f02b5b352dd527415` |
| Test | 1,755,365 | `6ea5c33f3023280ca304b30f844228760e02279e576902a3ba8d824c37569477` |

Its instrumented source SHA256 is
`4ead0ba0cd96c940288be93247679017cf2103767e041e56ab45717610ce19d5`.
Actual `llvm-readelf --dyn-syms --wide` checks of both packaged Rust libraries
find the publication JNI export and system `dlsym` import, with no dynamic
`renameat2` symbol requirement. These are cross-build/package checks, not ARM64
execution or API-26 compatibility measurements. The selected final host index
binds 194 files / 90,898,633 bytes, SHA256
`71dd514dcf172ec354712518f8f35857b24fd248265a0b72534c6c3008d031e7`.
It excludes live build/cache/temp directories; no OS-read-only namespace claim
is made. Independent rehash and final Android outcomes are recorded separately.

## Android discovery and remaining gates

The first admitted B cohort returned two passes and two failures, stopping
before any post-test settlement or cleanup. Both failures reached the strict
canonical-vs-absolute root check before copying. Its raw output does not reveal
a specific framework alias. The nominal symlink pass could have refused at
that earlier root check; the setup test's Choose-enabled assertion also accepted
the failure state. Those passes cannot establish successful import admission.
The actual native configuration/borrowed-handle closure subassertions did run.

The fix canonicalizes only the trusted Android private-storage anchor on IO,
then appends fixed children. Arbitrary-root checks remain strict. The setup
test now requires the exact missing-model status, and the symlink case proves
positive root admission before introducing a child symlink. Original source,
failures, APKs and stopped observations remain separately retained. See the
device report for each later admission and its actual limits.

The anchor-corrected cohort passed the stronger missing-model and symlink
checks, but both full-copy methods failed with a sanitized `STORAGE` error.
That output does not identify the failing operation. Separately, the pinned
Android 15 [app policy](https://android.googlesource.com/platform/system/sepolicy/+/refs/tags/android-15.0.0_r1/private/app_neverallows.te)
explicitly prohibits untrusted-app hard links. This establishes a design
incompatibility; it does not establish the origin of either recorded error.
The replacement is the strict no-clobber public bionic rename described in the
contract. Its additional host regressions cover sanitized publication failure
and cancellation immediately after a move. Android assertions exercise actual
JNI publication against existing regular and symlink destinations.

The corrected cohort subsequently passed all four actual Android methods on
B, Android 15/API 35/x86_64 with 4 KiB pages. Its original owned handle reached
exit zero with known cleanup in 22,828 ms; all 47 device clients completed with
exit zero and known cleanup. The copy/reopen test also exercises the real native
no-clobber operation against existing regular and symlink destinations. The
cancellation case holds the slot until a blocked provider returns, drains it,
and then successfully imports a fresh tiny fixture. The missing-model case
constructs the real configured Rust owner and observes borrowed-handle closure
without initializing an SDK Engine.

After all four passes, the controller verified the signed installed test-host
identity and complete package map before one exact disposable TEST-host stop.
Subsequent gates found no LocalLore process and preserved the exact other 29
package hashes and the updated candidate pair; final userdata available was
1,465,159,680 bytes, above the original floor. The update requested private-data
preservation; it was not a bytewise audit of private userdata. This cleanup
does not establish natural process exit or active-model resource ownership.
The two earlier failed cohorts remain failed; successful correction does not
identify the underlying operation in their sanitized errors. Detailed raw
selection verification, seal and limitations are in the device report.

Real model initialization, large-artifact import performance, provider-picker
round trips, active SDK cancellation/close, narrative quality, sustained memory
and thermal behavior, reference-phone/two-emulator/ARM64/16 KiB execution and
release licensing remain unqualified. Existing A/#117/#119 model and preservation
holds remain unchanged. Corrupt existing artifacts require a future explicit
removal/replacement flow. Finishing an Activity does not reset the process-wide
runtime reservation. No milestone checkbox, owner acceptance, merge or release
is inferred from this packet.
