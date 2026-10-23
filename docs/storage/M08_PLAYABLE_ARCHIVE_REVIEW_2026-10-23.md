# Playable archive integration review

Refs #12 M08.04/.06 and #30 shared dependency, partial. Root claim6361019906
takes the author's released claim. Independently reviewed788afcf, integrated as
f8f656b; author docs2969550 integratedcf7245f. Root did not author this archive.
No concrete blocking source finding remains. This is not human approval or full
M08/D08 acceptance.

The single bounded JSON format contains the original seed and original local
accepted receipts for all included branches. Strict unique-key parsing rejects
duplicate and unknown fields. Size/count/ID/version/graph checks precede target
writes. Checksums establish consistency only: every accepted result still goes
through actual Engine restore/fork/continuation and full semantic receipt
comparison, then normal Store lineage/ledger verification before commit.

One connected root and bounded ancestry retain ancestor source scopes and exclude
parent futures/siblings from children. Original accepted Play provenance and stage
timings survive unchanged, including supported historical2.1. Policy/model
references are recomputed from those receipts; weights, prompts in separate trace
logs, caches and every noncommitted workflow row are excluded. Import never
resumes pending work or loads a referenced model. Full-private hidden seed facts,
original accepted input/narration and metadata are explicitly disclosed.

Export takes one coherent SQLite read snapshot, then validates its immutable
artifact outside the source lock. Import consumes a private nonconstructible
token under one IMMEDIATE nonoverwrite transaction, verifies the inserted
canonical ledger, and commits once. Existing identity always conflicts, even
identical data after an unknown acknowledgement; this is deliberately not an
idempotent successful import-retry promise. Callback panic cancels. Cooperative
checks do not preempt a single parser/replay/hash/SQLite call. No hard RSS or
wall-clock guarantee is inferred from byte caps.

Root read the entire implementation and hostile/roundtrip tests. Tests cover
resealed forged effects/witnesses/proposals, duplicate/unknown/future input,
partial/future/cyclic graph boundaries, original scopes, coherent export while a
second owner commits, every observed importer cancellation checkpoint, actual
SQL-trigger rollback, competing imports, excluded workflow/cache data, exact
committed retries, historical policies and continuation without a model.
Not every numerical boundary has an independent stress vector; no archive-specific
kill-at-commit, actual DiskFull or native transfer execution is claimed here.

## Coordinator execution

Windows x64; Rust/Cargo1.93.1; locked/offline; DEV/TEST_DEBUG0, INCREMENTAL0;
task-owned D targets/temp. Sourcecf7245f passed **280 workspace tests**, zero
failed/ignored, workspace all-feature/all-target strict Clippy and fmt. The first
standalone evaluator command correctly refused its stale lockfile. Root updated
only the local storage dependency lists in the evaluator/native lockfiles as
0c7ac40: existing serde and sha2 entries, no package-version change/download.
The refusal log is retained, not reported as a passing check.

Accepted D07 main25a965a was merged as
`6d7984fd0b9be1f0ffe8febf0522a473773f75d6`. Shared archive source remained
unchanged; the standalone native lock preserved both D07 and archive entries.
Checks against that combined tree:

```powershell
cargo +1.93.1 test --manifest-path crates/locallore-eval/Cargo.toml --all-targets --locked --offline --target-dir <task>/m07-derived
cargo +1.93.1 test --manifest-path apps/desktop/src-tauri/Cargo.toml --features dev-harness --locked --offline --target-dir <task>/desktop-publication-target
cargo +1.93.1 clippy --manifest-path apps/desktop/src-tauri/Cargo.toml --features dev-harness --all-targets --locked --offline --target-dir <task>/desktop-publication-target -- -D warnings
```

Passed: evaluator **9 tests**, zero failed/ignored,2.54s; native **30 passed/1
existing privilege-related ignore**, plus **2 wrapper tests**, strict Clippy.
Evaluator strict all-target Clippy also passed after the lock update. Native
units used the already verified normal frontend assets copied from the D07
checkout; Git confirms those frontend inputs match. This is native unit/compile
compatibility, not a new WebView/model run.

Android used existing JDK17.0.6, Gradle8.11.1/AGP8.10.1, Kotlin2.2.21, SDK36/
NDK29.0.14206865 and task-private Gradle/output directories:

```powershell
java -classpath gradle/wrapper/gradle-wrapper.jar org.gradle.wrapper.GradleWrapperMain -I <task>/android-output.gradle :app:assembleDebug :app:assembleDebugAndroidTest :app:testDebugUnitTest :app:lintDebug --offline --no-daemon --console=plain '-Pandroid.builder.sdkDownload=false'
python scripts/audit_apk.py <task>/android-build/_app/outputs/apk/debug/app-debug.apk
```

Passed in **1m9s**, **78 tasks:21 executed/57 up-to-date**, both JNI ABIs rebuilt,
both APKs assembled, **38 JVM tests** with zero failures/errors/skips, lint and APK
permission/16KiB alignment audit. No APK was installed or device/emulator/ADB
operated. Logs remain gitignored under `target/archive-*`. The author's earlier
217/220 two-package tests are separately attributed, not doubled as root checks.

Full M08/D08 gates remain unchecked. Next: desktop consent/file-boundary adapter
with an actual isolated staging Store before destination import, followed by
native and Android bidirectional transfer/continuation evidence. This shared
transactional API alone does not satisfy D08's separate-copy UI import criterion.
