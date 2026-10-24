# Typed Domain2 fixture continuation qualification

2026-10-23; partial M08.03/.06 and D08.05. This report concerns the narrow shared
prerequisite on `impl/m08-typed-fixture-v2`, based on accepted `20a5a5c`.
Its focused review is [draft PR #137](https://github.com/OptimumAF/LocalLore/pull/137),
created at `6766486` before this report is adopted.
The later desktop author UI/native harness in draft PR #135 is separate.
`desktop_memory_ui` owns only this new report and reads retained source/logs;
all runtime checks below are Root executions, not reviewer reruns.

## Problem, production scope and authority

Root's desktop journey at `13e92ed` reached 71 checks/eight application-owned
WebView images, including Mira retaining observed A after private world B and
Sable isolation, then typed Give failed `Version` at unchanged child head 2.
That is the discovery context, not a successful qualification of the repaired
desktop/native journey. Existing `inference::execute` always requested legacy
`character_context`, whose deliberate Domain2 refusal caused the failure.

Production changes only `crates/locallore/src/inference.rs`: additive native
`Input::DirectorV2`, actual actor-only CharacterContextV2 for Domain2, and one
shared FakeProvider proposal arm. Domain1 retains Director/context bytes;
same selected player/scope/head and 32,768-byte context guard apply. Existing
preflight, proposal/preview, generation budgets/cancellation, narrator and commit
remain the pipeline. Exact recorded retries still bypass provider calls.
Structured real Play, canonical validation, Host protocol/wire, schema, Store
writer/transactions and platform consumers do not change.

## Frozen source and actual failure chronology

The author packet froze tests/contract `869dc28` before production. Root imported
the tests as `7a0394e`, accessor correction `0b61116` as `4aeba62`, and production
`b6a83d1` as `4164266`. Root `3904cb5` corrects the rejected fake-mode expectation.

| Stage | Exact observed result | Meaning |
| --- | --- | --- |
| Original Core oracle compilation | E0616 for private Receipt request/events | New test-source accessor mistake; not a behavioral RED cohort |
| Accessor-corrected Core baseline | 1 PASS / 2 FAIL / 0 ignored | Legacy passed; both Domain2 cases failed actual Version before provider |
| Actual workspace Host baseline | 0 PASS / 2 FAIL / 0 ignored | Typed prepare returned Version, including cancelled fake mode before its provider could run |
| First production Core cohort | 2 PASS / 1 FAIL / 0 ignored | Typed Give/Wait and legacy passed; rejected fake-mode oracle expected Ability but observed Agency |
| First production Host cohort | 2 PASS / 0 FAIL / 0 ignored | Actual SQLite/workspace typed lifecycle and failure cases passed |
| Corrected Core at 3904cb5 | 3 PASS / 0 FAIL / 0 ignored | Existing intent guard's Agency precedence reflected in the new oracle |

The original receipt-field error was corrected solely to public `request()` and
`events()` accessors, preserving comparisons and coverage. The first production
Core log's filename includes `first-green`, but its contents are **2/1 FAIL**;
the filename must not be treated as success. The rejected fake changes requested
Wait into an invented ability. Existing `Engine::preview` compares typed commands
against `Engine::proposal(request)` and returns Agency before ability resolution.
Independent source review confirmed that established guard; `3904cb5` changes
only the new expectation and explanatory comment, not production/old tests.
Both first failures remain retained; this is a transparent oracle correction,
not a claim that the original assertions all passed unchanged.

## What the focused passing cases establish

Three Core tests execute actual discovery A, author correction B, typed Give/Wait,
inventory/revision checks and CanonicalPlayV2. Provider input equals the actual
Engine-produced actor context and preserves old observed A, excluding world B,
author reason and NPC-named-player-only knowledge for custom hero. The adapter
records requests while delegating to the existing synthetic FakeProvider; no
real inference is claimed. Exact retry returns the same receipt with zero polls,
even with a cancelled token. Rejected/failed/malformed/cancelled generation and
narrator-stage cancellation preserve canon/basis; strict continuation replay and
legacy Director representation are checked.

Two workspace tests use public Store APIs, genuine SQLite and actual workspace
Host, without fake persistence or direct SQL writers. They cover both native
inspection grants, default/custom players, prepare without commit, commit,
exact receipt retries/reopen, original parent preservation, persisted V2 replay,
queued cancellation and typed inventory rejection. Omniscient inspection can
read private B only with permission; it does not teach actors B or change their
accepted source. These are native Rust library tests, **not desktop IPC or
WebView rendering**.

## Commands, environment and broad qualification

Root confirmed its shared qualification process terminated successfully at
`3904cb5`: corrected Core exit 0, full shared exit 0 and strict Clippy exit 0.
The full shared log contains **743 PASS / 0 FAIL / 9 ignored**, 107 result groups.
Strict Clippy finished in 35.78s. Root then committed `e33d4d1`, rustfmt-only
changes to the two new test files, preserving their assertions, and
`cargo fmt --all -- --check` exited 0. The zero-byte fmt log alone is not proof;
the successful exit is separately attributed to Root.

These are the exact focused/shared invocations confirmed by Root (repository
root, default features for the two focused tests, no omitted feature switches):

```powershell
cargo test --locked --offline -p locallore --test m08_typed_inference_v2_review
cargo test --locked --offline -p locallore-workspace --test m08_typed_host_v2_review
cargo test -p locallore -p locallore-storage -p locallore-workspace -p locallore-android --all-features --offline --locked
cargo clippy --workspace --all-targets --all-features --offline --locked --exclude locallore-desktop-spike -- -D warnings
cargo fmt --all -- --check
```

For these runs Root set task-owned `CARGO_TARGET_DIR`, `TEMP` and `TMP`;
`CARGO_PROFILE_DEV_DEBUG=0`, `CARGO_PROFILE_TEST_DEBUG=0`, `CARGO_INCREMENTAL=0`,
`CARGO_BUILD_JOBS=1`, and empty `LIBSQLITE3_FLAGS`. Targets and temporary outputs
were outside tracked sources. No package/tool/SDK/model download is part of this
offline qualification. Toolchain is pinned Rust 1.93.1. The existing qualified
environment records rustc 1.93.1 (`01f6ddf75`), Cargo 1.93.1 (`083ac5135`),
Windows 11 Pro x64, Node 24.22.1, JBR Java 17.0.6, Gradle 8.11.1, AGP 8.10.1,
Kotlin/Compose 2.2.21, SDK 36, build-tools 35.0.0 and NDK 29.0.14206865. These
versions are inherited from the unchanged qualified local setup described in
[the V2 prerequisite report](M08_V2_PREREQUISITE_QUALIFICATION_2026-10-23.md),
not new version commands run by this documentation reviewer. Root additionally
confirmed fresh rustc/Cargo/Node/Java version reads matching the values above.

Root's separate compatibility launcher starts at `e33d4d1` and records each
stage's source/exit in a local manifest. Its exact commands are below.
`<native-target>`, `<java>`
and `<task-output-init.gradle>` denote existing task-owned absolute paths,
omitted from public evidence.

```powershell
cargo test --manifest-path crates/locallore-eval/Cargo.toml --all-features --offline --locked --target-dir <native-target>
# apps/desktop, with the existing Node 24.22.1:
node verify-frontend.mjs
node node_modules/prettier/bin/prettier.cjs --check 'ui/*.{ts,tsx,html,css}' '*.{json,mjs}'
# repository root:
cargo test --manifest-path apps/desktop/src-tauri/Cargo.toml --offline --locked --target-dir <native-target> -- --test-threads=1
cargo test --manifest-path apps/desktop/src-tauri/Cargo.toml --features dev-harness --offline --locked --target-dir <native-target> -- --test-threads=1
cargo clippy --manifest-path apps/desktop/src-tauri/Cargo.toml --all-targets --features dev-harness --offline --locked --target-dir <native-target> -- -D warnings
cargo build --manifest-path apps/desktop/src-tauri/Cargo.toml --no-default-features --offline --locked --target-dir <native-target>
# apps/android:
<java> -classpath gradle/wrapper/gradle-wrapper.jar org.gradle.wrapper.GradleWrapperMain --offline --no-daemon --max-workers=1 --console=plain -Pandroid.builder.sdkDownload=false --init-script <task-output-init.gradle> :app:testDebugUnitTest --rerun :app:assembleDebug :app:assembleDebugAndroidTest :app:lintDebug
```

The launcher reuses the same bounded Rust environment, existing JBR/Android SDK
and task-owned Gradle cache/output initialization. Root's separate author UI
frontend pass at `dfbe11c` is not this prerequisite source's frontend cohort.

The first stage manifest entries at `e33d4d1` record Eval, frontend and frontend
format exits 0, followed by normal native serial exit 101. Eval logs contain
27 passed/one existing historical-fixture ignore; frontend includes the 99-case
synthetic V2 decoder, existing controller/retention suites, strict TypeScript,
normal bundle generation and absence of development hooks; Prettier reports all
matched files formatted. The first normal native run contains **84 PASS / 1 FAIL
/ 1 ignored** (21.89s). The failure is
`evaluation::tests::boundary_cancel_resume_old_operation_and_retired_lease_are_fenced`,
with `native evaluation did not reach boundary`. Its retained log is evidence
of failure; later success is evidenced separately below.

Root then reproduced the same boundary failure in isolation: **0 PASS / 1 FAIL**,
85 filtered, 5.84s, retained separately. Its read-only inspection of the owned
synthetic output found cases 0–9 written over roughly six seconds and all twelve
cases from the first cohort over roughly seven seconds. This is Root-attributed
fixture progress evidence; no model or production timing promise follows.
Root `6766486` changes only the `cfg(test)` evaluation completion helper from
1,000 five-millisecond polls to a monotonic **30-second** fixture deadline with
last-status diagnostics. The five-millisecond poll, exact twelve-case checks,
cancel/resume/old-operation/retired-lease assertions and production operation
budgets are unchanged. This test deadline was changed; the report does not
describe the original timing oracle as an unchanged pass. The first failure and
isolated reproduction remain retained alongside the corrected cohort.

The launcher reuses stage-leaf filenames. The initial normal-native stage leaf
was overwritten by the corrected run, so the initial failure is cited by the
retained first **outer** `typed-v2-compat-launcher.log`, not a stale leaf hash.
The corrected outer log has its own basename and the source manifest preserves
both source/exit entries.

The subsequent Root stage manifest records these completed results at `6766486`:

| Compatibility cohort | Terminal result |
| --- | --- |
| Normal native Rust, serial | 85 PASS / 0 FAIL / 1 ignored; 22.99s test time, exit 0 |
| Dev-harness native Rust, serial | Main group 89 PASS / 0 FAIL / 1 ignored, 23.47s; plus two harness-contract passes, 0.01s; aggregate 91 PASS / 0 FAIL / 1 ignored, exit 0 |
| Native strict Clippy | Exit 0, finished 14.15s |
| Normal native build, no default features | Exit 0, finished 15.19s |

The unchanged ignored native case requires Windows symlink privilege. These
Rust test cohorts do not start a WebView or rerun the desktop journey.

The resulting normal executable was read as 28,512,768 bytes, SHA256
`507d4f6f17a02a7634e7be5f8ce5006a8aaa129e2320cba0f4df3987f8c137e9`.
The normal frontend bundle was 413,581 bytes, SHA256
`604ec37bceaa5a50bd60d094933ba32cab32dc759a576278a49ee03dc247f046`.
These are build artifacts, not proof of native application execution.
Root also isolated six untracked generated author permission files in local
artifacts after Tauri builds. They were unreferenced by this source's build,
Main and capabilities and were not committed. PR #137 introduces no author JSON
IPC or normal-app permission exposure; that desktop integration remains separate.

## Android compatibility and static artifact audit

Root's corrected launcher terminated exit 0 at `6766486`. Android reported
**BUILD SUCCESSFUL in 5m 44s; 78 actionable tasks: 7 executed, 71 up-to-date**.
This was not 78 newly executed tasks. Rust JNI rebuilt both targets: x86_64
in 2m41s and aarch64/arm64-v8a in 2m38s. The JVM task reran: fresh XML contains
**182 tests / 22 suites / 0 failures / 0 errors / 0 skips**, modified
2026-10-24T04:49:24.6325795Z–04:49:24.6476081Z after the Android stage started.
This reviewer parsed the XML read-only and independently computed the aggregate
manifest digest `a41d3f5f23f0ba8897b4ced17a1e539412fa17fc016152725df8f3d5a8bcc865`
from sorted UTF-8 LF-terminated `filename|lowercase-sha256|bytes` lines.

APK assembly and lint tasks completed with the cache/up-to-date statuses shown
in the log. `assembleDebugAndroidTest` and lint analysis/report were up-to-date.
The lint XML is therefore the retained **03:19:34Z** artifact, not a fresh lint
analysis at 04:49: it contains zero errors and one existing `GradleDependency`
warning. The app APK is updated at 04:49:26Z; the instrumentation APK is the
retained 03:18:43Z artifact. Do not describe all artifacts as regenerated.

Root's first separate APK audit exited 1 because its shell lacked ANDROID_HOME;
the retained failed log is an environment setup failure, not a failed APK
property. With the existing SDK environment set, the same static audit exited 0.
Its JSON reports only `org.locallore.app.DYNAMIC_RECEIVER_NOT_EXPORTED_PERMISSION`
and four libraries: liblocallore_android.so and libandroidx.graphics.path.so for
both arm64-v8a and x86_64. Every reported ELF LOAD alignment is 16,384 bytes.
The command is `python scripts/audit_apk.py <app-debug.apk>`, with existing
ANDROID_HOME/SDK configured. Final `cargo fmt --all -- --check` at `6766486`
also exited 0; its empty log is accompanied by Root's explicit exit report.

| Android artifact | Bytes | SHA256 |
| --- | ---: | --- |
| `app-debug.apk` | 31,638,248 | `babdcf1c2c4be73707e00329968aff42ca282282d5b80f3ad15e4338e9250744` |
| `app-debug-androidTest.apk` (cached) | 1,715,781 | `40450f596df0d5b5db724f5452aac63124f820cefa20d82bd3a7733a39dc4c36` |
| `lint-results-debug.xml` (cached) | 1,168 | `7b59492e6c21986769142249a2c530fd40ff210ed59910533edc137ea35a3a2a` |

No device, emulator install/run, runtime JNI, Android corrected-child UI or
physical 16 KiB behavior is established by compilation/JVM/static APK checks.

## Retained focused evidence

The local log contents and SHA256 values below were independently read by
this reviewer. Private absolute paths, stack traces and generated artifacts are
omitted from this public report. Artifacts remain local and gitignored.

| Local log basename | SHA256 |
| --- | --- |
| `typed-v2-core-original-red.log` | `bcb0de7129522acdf0aa5c9f1ce5214a8507069543e1ae12a62466da896ee0b0` |
| `typed-v2-core-accessor-corrected-red.log` | `df6a1f3e57e770bda7073e44c3a32e2695df3e1418a547afa4b33928a85ede79` |
| `typed-v2-host-original-red.log` | `03147a96696c427768c0d8a2d9f693d2cbbcde9da79fb2a1b85ea3dd666554d3` |
| `typed-v2-core-first-green.log` (contains FAIL) | `05bb2749d46aa7e17bd85f35f0b1c7892e7602a1581d4c04ed9cf886ec268fcc` |
| `typed-v2-host-first-green.log` | `b2838c19838c9e5bf30768d763f4777f65c9569760caa3b7d6283f0027264fa4` |
| `typed-v2-core-corrected-green.log` | `4454de4c4fd4754b3457737d47525fbb1156367da91e69db365584f9e780ab8c` |
| `typed-v2-shared-full.log` | `be35f6c7fb84f1840185bf357d6411daace1c0b7251626d63ac88e66140ffd63` |
| `typed-v2-shared-clippy.log` | `280372dee6e3d707ce6ffbb31906b810fe9c9cb493bc5193023b52e234f82ddc` |
| `typed-v2-fmt.log` (zero bytes; exit separately confirmed) | `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855` |
| `typed-v2-prerequisite-checks.ps1` (launcher source) | `0f89acf65db5b9922aeb3e5beffd00171094e8d69959ab1cd646957522789302` |
| `typed-v2-eval.log` | `cbe449b0fa8ddc97c06d3b55a8b92b74cc3c336f412b2becc4d16db2b39b45f5` |
| `typed-v2-frontend.log` | `ad6be2e22fabff6403fc278c47687029a1615bbe266bfb2fc84a7e703c8c65c0` |
| `typed-v2-frontend-format.log` | `f20510a9da4717c51c4cffee6d0dd88d6c9a723d0a83711d01216f5b48961283` |
| `typed-v2-compat-launcher.log` (first outer, includes original native failure) | `20ce33038a1db4a82a731eb423949b81730b04ebc7e89b2a6e44aae0ed90929d` |
| `typed-v2-native-boundary-isolated.log` | `217be9765e427ed64fd47e0cc3a2b06dca17e8c31923f1b6538d023944971a04` |
| `typed-v2-native-normal-serial.log` (corrected run) | `7ab55309451ff738e5841c88b286270a63d3ecaf3cb7cefb0cc35c7acff25e01` |
| `typed-v2-native-dev-serial.log` | `8595928296871fb9af1b106796a7e40d028c996bd3c74214b8ccdb9edb5d5ce3` |
| `typed-v2-clippy-native.log` | `5fb9f6ad429cac1f973671e24416d39f70b3391f442496a73c2e5c10324d3656` |
| `typed-v2-native-normal-build.log` | `e9c90737a16b457d565e4b1d7de2b9046cf6fc871e8778e7cb9f52b6eb3905e0` |
| `typed-v2-android.log` | `13557b90b1fb21cf7e1a83c17b0e164107e0e2669bdceb91e0944699db3e1188` |
| `typed-v2-check-results.json` (all original/corrected sources/exits) | `2703c0d98acb8e10f61e839ef3a6b6ab55aa13df4de651b48dae3942519557b0` |
| `typed-v2-compat-native-corrected-launcher.log` | `0400e5d764067a63abc48c669df5694eaf2fea8fa14c8a7bb179775b273845ce` |
| `typed-v2-apk-static.log` (first environment failure) | `e021c1e673c15729730825dfa7cb6028093aa1bc8d10bb6af6c252f3fa7c6864` |
| `typed-v2-apk-static-corrected.log` | `33d292acd39d4040aeb6f7032aad4acaed7619a3446d32a3799b10a220be9699` |
| `typed-v2-fmt-final.log` (exit separately confirmed) | `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855` |

## Limits and next runnable gate

No new engine/Store semantic bug was found in the bounded source audit. That is
not owner acceptance or proof of all consumers. No model quality/performance,
physical Android/device, desktop IPC/WebView/render repair, restart author
recovery, release or full milestone acceptance follows from these library tests.
Root owns focused PR review/integration and the interrupted actual desktop
journey after this prerequisite qualifies. The
reviewer runs only source/log/hash/Git checks; no Cargo/Node/SQLite/app/native
or device execution under this documentation allocation.
