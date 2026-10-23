# Durable fork integration review

Refs #12 M08.01/.02 and #30 D08.04 dependency, partial. Root integration claim
6360352617 follows the author's explicit release. Independently reviewed author
implementation `b11986c`, integrated as `4756e32` on accepted main82264e7;
author evidence2b8b3d7 integrated as `a8b5199`. This reviewer did not author the
fork implementation. No concrete blocking source finding remained.

## Source findings and boundaries

The existing schema supports lineage without a migration. An IMMEDIATE fork
transaction validates the original parent through the shared strict loader and
uses actual Engine::fork. It creates only child metadata/entity membership and a
replaceable projection. Original ancestor receipts, scopes, events, witnesses,
drafts and caches are not copied or relabeled under the child. Branch identity
is immutable; an existing child+parent+fork resolves its current head even if
the creation-only expected-parent-head guard changes. This is not byte-exact
full-ForkRequest retry; existing turn requests retain their exact retry contract.

The loader validates one bounded root-to-leaf path, original local receipt JSON,
requests, normalized events and witnesses, then rebuilds with strict shared
restore/fork/continuation. Cycles, unknown/cross-story lineage, invalid boundaries
and forged accepted outcomes fail closed. Nested rewinds before a parent's birth
use enough temporary prefix to validate each actual fork, then Engine::fork
discards the excluded future. Siblings and later-than-required ancestor content
do not enter the selected Engine. Full current-branch corruption is still rejected;
excluded later parent corruption does not become selected child content.

Aggregate loaded-prefix count/byte budgets apply at restore, new-turn admission
and response commit. Combined with depth32/branches256 and existing transaction
rollback, this prevents admission of a continuation that only a larger restore
budget could read. It is conservative work accounting, not measured performance.
Cancellation is checked around replay/SQL publication; individual replay and
SQLite calls remain synchronous. No hard whole-fork cancellation deadline is
claimed. Historical accepted Play2.1 restoration remains distinct from fresh
prepared-commit validation; unsupported policy2.0 still fails.

Compiler, inspector query and derived-cache child guards remain explicitly
unsupported. No child model context or desktop branch UI is enabled here. Host
and Android source, wire contracts, archive formats and correction authority do
not change. The fixed branch API must be integrated into those consumers before
full M08.01/.02 or D08 acceptance.

## Coordinator checks executed

Windows x64, Rust/Cargo1.93.1, debug0/incremental0, locked offline dependencies,
owned D targets/temp. These executions used exact source `a8b5199`; subsequent
changes in this packet are documentation only.

```powershell
cargo +1.93.1 test --workspace --locked --offline --target-dir <task>/m07-derived
cargo +1.93.1 clippy --workspace --all-targets --all-features --locked --offline --target-dir <task>/m07-derived -- -D warnings
cargo +1.93.1 test --manifest-path crates/locallore-eval/Cargo.toml --all-targets --locked --offline --target-dir <task>/m07-derived
cargo +1.93.1 clippy --manifest-path crates/locallore-eval/Cargo.toml --all-targets --locked --offline --target-dir <task>/m07-derived -- -D warnings
cargo +1.93.1 test --manifest-path apps/desktop/src-tauri/Cargo.toml --features dev-harness --locked --offline --target-dir <task>/desktop-publication-target
cargo +1.93.1 clippy --manifest-path apps/desktop/src-tauri/Cargo.toml --features dev-harness --all-targets --locked --offline --target-dir <task>/desktop-publication-target -- -D warnings
cargo +1.93.1 fmt --all -- --check
git diff --check
```

All passed: **264 workspace tests**, zero failed/ignored, including the14 new
strict restore/Store cases; standalone evaluator **9 passed**, zero failed/ignored,
2.58s. Strict all-target workspace/all-feature, evaluator and native Clippy passed.
Native development units **20 passed/1 existing privilege-related ignore**, plus
**2 wrapper tests**. Native unit compilation used already checked normal frontend
assets copied from source-memory with unchanged frontend inputs; no frontend or
WebView rendering execution is implied by these unit tests.

Android compatibility used existing JDK17.0.6, Gradle8.11.1/AGP8.10.1,
Kotlin2.2.21, SDK36/NDK29.0.14206865, task-private Gradle/output directories:

```powershell
java -classpath gradle/wrapper/gradle-wrapper.jar org.gradle.wrapper.GradleWrapperMain -I <task>/android-output.gradle :app:assembleDebug :app:assembleDebugAndroidTest :app:testDebugUnitTest :app:lintDebug --offline --no-daemon --console=plain '-Pandroid.builder.sdkDownload=false'
python scripts/audit_apk.py <task>/android-build/_app/outputs/apk/debug/app-debug.apk
```

Passed: **78 tasks executed**, both JNI ABIs and both APKs rebuilt; **38 JVM
tests**, zero failures/errors/skips; lint and APK permission/16KiB alignment audit
passed. This is build/JVM compatibility, not emulator, physical-phone, branch UI
or archive-transfer execution. No ADB/device/model/desktop control was used.
Logs remain gitignored under `target/branches-integrated-*`. The author's204
two-package all-feature tests and initial fixture mistakes are separately
attributed in the original evidence; no execution count is doubled.

Full M08 and desktop epic gates remain unchecked. Next: shared playable archive
validation/atomic import and lineage-aware consumer integration, then desktop/
Android transfer and correction journeys under the same shared authority.
