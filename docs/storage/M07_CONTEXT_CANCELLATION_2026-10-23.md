# Cooperative context compilation

Refs #11 M07.01/.04/.06, partial. Claim6360117335 preceded editing. Source
`3e8d97265ccfaa121fdc5cba820675e48f3729e4`, based accepted main82264e7.
Status: in_review; independent source review remains required before merge.

`compile_cancelled` adds a native Rust cancellation callback; existing `compile`
remains source-compatible. Cancellation and callback panic return Cancelled,
with no partial package. Production Play supplies its actual cancellation token
and maps this error to the existing shared Cancelled category before inference.
No inspector grant, new wire field, model access or generation permission exists.

Current-head snapshots borrow the immutable Engine through Cow rather than
cloning its complete accepted history. Historical snapshots still rebuild through
recorded replay. Observations use the existing borrowed actor visitor, so shared
branch/time/witness filtering happens before compiler row construction. Combined
row count/encoded-byte limits are checked during accumulation, and encoded rows
are reused during deterministic selection. Ranking, mandatory facts, policy,
prompt and package versions are unchanged.

Checks cover the compiler's stages, retained observations/candidates, references,
mandatory/optional selection and final package return. This remains cooperative:
historical replay, sorting/individual serialization and the existing shared
actor-row collector can perform synchronous work before the next check. That
collector still internally constructs character contexts; this slice does not
claim every history allocation is eliminated, constant-time privacy, a maximum
RSS bound or a hard whole-operation cancellation deadline. Source scans remain
O(total history). Durable maintenance and cached-summary consumption are separate.

## Executed checks

Windows x64, Rust/Cargo1.93.1, locked offline dependencies, DEV/TEST_DEBUG0,
INCREMENTAL0, task-private D targets/temp. No model, GUI or device execution.

```powershell
cargo +1.93.1 test --workspace --locked --offline --target-dir <task>/m07-context
cargo +1.93.1 clippy --workspace --all-targets --locked --offline --target-dir <task>/m07-context -- -D warnings
cargo +1.93.1 fmt --all -- --check
cargo +1.93.1 test --manifest-path crates/locallore-eval/Cargo.toml --all-targets --locked --offline --target-dir <task>/m07-context
cargo +1.93.1 run --manifest-path crates/locallore-eval/Cargo.toml --locked --offline --target-dir <task>/m07-context -- run <task>/d07-context-cancellation
cargo +1.93.1 test --manifest-path apps/desktop/src-tauri/Cargo.toml --features dev-harness --locked --offline --target-dir <task>/desktop-publication-target
cargo +1.93.1 clippy --manifest-path apps/desktop/src-tauri/Cargo.toml --features dev-harness --all-targets --locked --offline --target-dir <task>/desktop-publication-target -- -D warnings
```

**253 workspace tests passed**, zero failed/ignored; strict Clippy/fmt passed.
The original10 compiler tests include the 1,026-event retrieval/budget cases.
Three new tests cover early/observation/candidate/final cancellation checkpoints,
panic-to-cancellation and successful retry, historical revision boundaries and
private actor packages. No interrupted package escapes or canonical mutation
occurs. Standalone evaluator **9 passed**, zero failed/ignored,2.92s.
CLI: **9 passed/0 failed/3 unsupported**,196 checks, quality_accepted=false.
Director/narrator prompt/schema hashes match the accepted evaluator baseline for
the scripted production scene. Whole-case JSON differs at scoped receipt/retry
fingerprints because fresh synthetic workspaces have different story UUIDs;
read-only inspection confirmed this expected scope difference. A whole-report
byte-equality attempt was not claimed as a pass.

Local report JSON SHA256:
`80eaf469cc0ff4429c51405d3542e98a45dd9bb6793fd09ae090381bdbca362b`.
Binding SHA256:
`341471d9a14a0747ec0404253efe4de78d6a3653bc75f2b4647f59cdd6ce6930`.

Native development units **20 passed/1 existing privilege-related ignore**,
plus **2 wrapper tests**, strict native Clippy passed. Initial native compilation
refused the fresh checkout because frontendDist did not exist. It then used a
copy of already checked normal assets from task source-memory. Git verified UI,
build script and package lock inputs match this checkout; no frontend source
changed. This is native Rust unit/compile evidence, not WebView rendering or a
new frontend build.

Android compatibility used existing JDK17.0.6, Gradle8.11.1, AGP8.10.1,
Kotlin2.2.21, SDK36 and NDK29.0.14206865; task-private Gradle/output directories.

```powershell
java -classpath gradle/wrapper/gradle-wrapper.jar org.gradle.wrapper.GradleWrapperMain -I <task>/android-output.gradle :app:assembleDebug :app:assembleDebugAndroidTest :app:testDebugUnitTest :app:lintDebug --offline --no-daemon --console=plain '-Pandroid.builder.sdkDownload=false'
python scripts/audit_apk.py <task>/android-build/_app/outputs/apk/debug/app-debug.apk
```

Passed: **78 tasks executed**, both JNI ABIs and both APKs built, **38 JVM tests**
with zero failures/errors/skips; lint and APK permission/16KiB alignment audit
passed. No emulator, ADB or physical phone was operated. No system settings,
downloads, hosted inference or protected chat resources changed.

Logs, including the initial missing-frontend failure, remain gitignored under
`target/context-cancellation-*`. Full M07 and desktop quality/offline/device gates
remain unchecked. Next: independent review, reconcile concurrent durable-fork
integration, then maintained memory and production-consumer work.
