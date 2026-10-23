# Derived cache transaction integration review — 2026-10-23

Reviewer: coordinator `/root`, independent of implementation author
`/root/app_storage_review`. Status: locally verified partial prerequisite for
M07.03/.04 and M08.01; owner acceptance is recorded separately on GitHub.
Claim: #11 comment 6369504352. Reviewed source:
`b21b119d9261bdde5e54720194ce850df8aba567`, including accepted main #95.

## Review and result

Read the complete production diff, original transaction callers and actual Store
regressions. No remaining concrete correctness blocker was found in this slice.
Public signatures, schema, dependencies and packet-v1 JSON remain unchanged.
The strict canonical loader now runs inside the same read or IMMEDIATE writer
transaction as cache operations. It does not use projection repair as authority.
Publication freshly rebuilds and compares both all eligible original-scoped
sources and packet bytes before atomically fencing/inserting. Parent advancement
cannot contaminate a frozen child; child advancement rejects a stale token.

Actor filtering precedes extraction, partition text loading and TEMP FTS. Only
the selected story/branch/observer/current-head partition enters that FTS table;
foreign poisoned partitions cannot influence counts, search terms or ranking.
Stored packets are re-extracted even if the search would otherwise return no hit.
Test-only supplied-Engine adapters preserve the earlier isolated prototype suite;
production Store wrappers cannot accept a caller-supplied Engine/token payload.

Ten new actual-Store cases cover original source identity/root golden bytes,
nested rewind/privacy, parent versus child advancement, inherited event/witness
corruption, excluded future corruption, foreign poisoning/local forgery, every
observed cancellation checkpoint plus SQL-abort rollback, coherent concurrent
WAL snapshots, competing owners/search recovery, and Busy/pre-cancel preservation.
The synthetic WAL fixture changes its own database only. No production journal
policy was changed. Author compile/lint/fixture failures remain in the author
report; none is relabelled as a passing initial attempt.

## Executed checks and attribution

Windows 10.0.26300, Rust/Cargo 1.93.1, Node 24.22.1/npm 11.19.1,
Python 3.14.9; JDK 17.0.6, Gradle 8.11.1, AGP 8.10.1, Kotlin 2.2.21,
SDK 36/NDK 29.0.14206865. Rust profiles DEV/TEST debug=0,
incremental=0, with dedicated D-drive target and fresh task TEMP/TMP.
Commands are from the repository root unless a working directory is stated.

At `9425add7f6406517eec8eb3c4291c386fdd8aea5`:

```text
cargo test --workspace --all-features --locked --offline --target-dir <m07-context>
417 passed, 0 failed, 4 existing qualification ignores
cargo clippy --workspace --all-targets --locked --offline --target-dir <m07-context> -- -D warnings
cargo clippy --workspace --all-targets --all-features --locked --offline --target-dir <m07-context> -- -D warnings
cargo fmt --all -- --check
git diff --check
all PASS
```

In `apps/android`, with an init script redirecting all Gradle build directories
to a fresh dedicated `android-lineage-build`:

```text
java -classpath gradle/wrapper/gradle-wrapper.jar org.gradle.wrapper.GradleWrapperMain -I <android-lineage-output.gradle> :app:assembleDebug :app:assembleDebugAndroidTest :app:testDebugUnitTest :app:lintDebug --offline --no-daemon --console=plain -Pandroid.builder.sdkDownload=false
python ../../scripts/audit_apk.py <android-lineage-build>/_app/outputs/apk/debug/app-debug.apk
PASS: both Rust JNI ABIs, both APKs, 128 JVM tests (0 failures/errors/skips), lint, APK audit
BUILD SUCCESSFUL in 3m59s; 78 tasks, 78 executed
```

The Android cohort began on clean 9425add. Accepted #95 was reconciled at
b21b119 as it finished; exact source diff confirms Core/Store/workspace/JNI and
Android bytes were unchanged. The APK is attributed to 9425add, not relabelled.
No device, emulator or ADB operation occurred.

At `b21b119d9261bdde5e54720194ce850df8aba567`:

```text
node verify-frontend.mjs                                      # apps/desktop
cargo test --manifest-path apps/desktop/src-tauri/Cargo.toml --features dev-harness --locked --offline --target-dir <archive-ui-native>
44 native module + 2 harness contract passes; 1 existing ignored qualification
cargo clippy --manifest-path apps/desktop/src-tauri/Cargo.toml --all-targets --features dev-harness --locked --offline --target-dir <archive-ui-native> -- -D warnings
cargo test --manifest-path crates/locallore-eval/Cargo.toml --locked --offline --target-dir <local-model-final-target>
cargo test --manifest-path crates/locallore-eval/Cargo.toml --features local-model --locked --offline --target-dir <local-model-final-target>
23 default / 24 feature evaluation passes, zero failures
cargo clippy --manifest-path crates/locallore-eval/Cargo.toml --all-targets --features local-model --locked --offline --target-dir <local-model-final-target> -- -D warnings
all PASS
```

Local logs (gitignored build directories, no private data published):
`m07-context/derived-lineage-{workspace,default-clippy,all-clippy,android,apk-audit}.log`,
`archive-ui-native/derived-lineage-{frontend,native,native-clippy}.log`, and
`local-model-final-target/derived-lineage-{default-tests,feature-tests,feature-clippy}.log`.

## Limits and next work

These are Rust/native IPC module, frontend static and Android build/JVM checks.
There is no new native WebView rendering, model call, device test or performance
claim in this slice. Replay and SQLite work remain synchronous; the writer may
be held during strict reconstruction. Packet-v1 still covers the current head,
caps 256 selected events and becomes stale after child advancement. No durable
maintenance ledger, production coverage-v2 consumer or speed improvement exists.

Before storing v2 packets, narrow v1 SQL mutation/query namespaces so versions
cannot erase or interpret each other's rows. Next runnable shared task is durable
maintenance plus compiler consumption using accepted coverage-v2, after reconciling
the separate schema-3 retention/capacity claims. Do not assign a competing schema
version. Full M07/D08 and physical-device gates stay unchecked.
