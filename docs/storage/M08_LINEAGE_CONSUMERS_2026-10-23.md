# Lineage-aware compiler and inspector snapshots

Refs #12 M08.01 and #11 M07.01/.06, partial. Root claims6360911921/6360912247;
test ownership addenda6360980910/6361027310. Implementation6b24302, obsolete-test
repaircd8e55b, additional pre-birth regression0e36a63. Independent source-only
reviewc5d9946/6deb493 integrated47a3eb4/6a76b91; reviewer authorship and execution
limits are disclosed in `M08_LINEAGE_CONSUMERS_REVIEW.md`. No blocker remained.

`Engine::at_revision` returns a detached same-scope, same-lineage Engine at a
completed accepted-turn boundary. Current head clones an already validated
Engine; historical reads replay original receipts with their original scopes
and strict recorded outcomes, retaining the selected lineage and restoring the
selected child scope afterward. No provider, new branch, observer grant or
canonical write occurs. `fork` reuses this validated snapshot before assigning
its explicit new lineage/scope. Future and partial-turn boundaries are refused.

Compiler/query now accept validated child Engines and use this single historical
snapshot implementation. Current compiler head still borrows the immutable
Engine. Eligibility/witness checks precede serialized actor content; original
event scopes/provenance remain intact. Historical inspection does not backfill
future parent, sibling or later local events. Omniscient inspection remains a
trusted read grant and does not change actor knowledge or generation context.
Pagination remains bound to story/branch/observer/revision/query/head.

No Host/session protocol, Android, archive, database schema or generation prompt
template changes are introduced. Legacy public UnsupportedBranch error variants
remain for API compatibility, though these validated paths no longer return them.
Derived-cache child operations remain explicitly Unsupported in this slice.
The compiler's unsupported diagnostic now says branch-scoped derived caches,
instead of incorrectly denying durable branch history. Its six extra UTF-8 bytes
can change package byte/token estimates, optional selection or MandatoryBudget
at tight thresholds. No old-root byte or prompt equivalence is claimed. Play
excludes that diagnostic from model data, but selection changes can affect it.

Seven new core tests and one actual Store test cover original scoped receipts,
zero/current/historical boundaries, multi-event turn rejection, current and old
supported Play2.1, absent NPC/private seed secrets, inherited/local actor content,
cross-branch/observer/time cursors, stale heads, cancellation and nonmutation.
The explicit `root5 → a@5(+local6) → b@1(+local2)` consumer test verifies reads
before parent birth. A 1,025-event child retains old mandatory promise evidence
within the package budget while excluding later parent content. An actual Store
reopen feeds inherited/local child history into compiler/query; cache Unsupported
is preserved. These are retrieval/mechanics tests, not generated-story quality.

## Executed checks

Windows x64; Rust/Cargo1.93.1; locked/offline; DEV/TEST_DEBUG0, INCREMENTAL0;
task-owned D targets/temp. Initial focused test compilation exposed incorrect
test-only Store API names/arity; fixed before passing. An initial workspace run
then caught a superseded storage test expecting compiler/query UnsupportedBranch;
only that expectation was updated and its real derived-cache denial retained.
The failed log is preserved. No failing result is counted as passing.

Before archive integration, final0e36a63 passed **275 workspace tests**, zero
failed/ignored, all-feature/all-target strict Clippy; standalone evaluator9 tests
and strict Clippy. The earlier pre-additional-vector274 execution is separate.

Accepted D07 and archive main16bb5b2 were reconciled as
`ff4e1c7ecd5cc73a9f42708535b19bfdd9ae53db`, Engine regions merging without
conflict. The final combined tree passed:

```powershell
cargo +1.93.1 test --workspace --all-features --locked --offline --target-dir <task>/m07-context
cargo +1.93.1 clippy --workspace --all-targets --all-features --locked --offline --target-dir <task>/m07-context -- -D warnings
cargo +1.93.1 test --manifest-path crates/locallore-eval/Cargo.toml --all-targets --locked --offline --target-dir <task>/m07-context
cargo +1.93.1 clippy --manifest-path crates/locallore-eval/Cargo.toml --all-targets --locked --offline --target-dir <task>/m07-context -- -D warnings
cargo +1.93.1 test --manifest-path apps/desktop/src-tauri/Cargo.toml --features dev-harness --locked --offline --target-dir <task>/desktop-publication-target
cargo +1.93.1 clippy --manifest-path apps/desktop/src-tauri/Cargo.toml --features dev-harness --all-targets --locked --offline --target-dir <task>/desktop-publication-target -- -D warnings
cargo +1.93.1 fmt --all -- --check
git diff --check
```

**288 workspace tests**, zero failed/ignored; evaluator **9 passed**, zero
failed/ignored,3.02s; native **30 passed/1 existing privilege-related ignore**,
plus **2 wrapper tests**; all strict Clippy/fmt/diff checks passed. Later changes
are documentation and a comment clarifying the current-head snapshot behavior.
Native compilation used copied verified normal D07 assets whose frontend source
inputs match; this is native unit evidence, not new WebView or model execution.

Android compatibility used existing JDK17.0.6, Gradle8.11.1/AGP8.10.1,
Kotlin2.2.21, SDK36/NDK29.0.14206865 and task-private Gradle/build directories:

```powershell
java -classpath gradle/wrapper/gradle-wrapper.jar org.gradle.wrapper.GradleWrapperMain -I <task>/android-output.gradle :app:assembleDebug :app:assembleDebugAndroidTest :app:testDebugUnitTest :app:lintDebug --offline --no-daemon --console=plain '-Pandroid.builder.sdkDownload=false'
python scripts/audit_apk.py <task>/android-build/_app/outputs/apk/debug/app-debug.apk
```

Passed in **1m3s**, **78 tasks:21 executed/57 up-to-date**; both JNI ABIs rebuilt,
both APKs assembled, **38 JVM tests** with zero failures/errors/skips, lint and
APK permission/16KiB alignment audit passed. No model, device/emulator, ADB,
desktop control or protected resources were used. Local logs remain ignored at
`target/lineage-*`.

Full M07/M08/D08 gates remain open. Next: coherent branch-aware derived cache
transactions, then durable maintenance/coverage and shared branch/correction UI.
No child gameplay session command, cached-summary compiler consumption or
Android round-trip execution is implied by this read-consumer slice.
