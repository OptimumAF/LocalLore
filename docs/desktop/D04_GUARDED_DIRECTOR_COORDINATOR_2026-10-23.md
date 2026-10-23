# Guarded director coordinator integration, 2026-10-23

Refs #9 M05.01/.02/.04 and #25 D04.04, partial. Coordinator claims
[#9](https://github.com/OptimumAF/LocalLore/issues/9#issuecomment-6370510771)
and [#25](https://github.com/OptimumAF/LocalLore/issues/25#issuecomment-6370511104).
Original fixture/code/evidence `43bc8cb`/`5138427`/`4d6b9f6` and independent
tests/review `f2adbd5`/`cd03aa5` were imported unchanged. Later accepted main
c7f7c43234fe5f0856f21c403ff76a8b65b86671 (#87/#94/#102/#103) was merged
normally at checked source `1e4fcf6e9ac31648f50b743773ced924af92373e`.
Separate test-only fixture collision fix is already accepted via #94; this PR's
diff against main contains no duplicate fixture correction or native path fix.

## Authority and review

The existing finite action guard already resolves and Engine-preflights exactly
one Command. This change retains that same Command and binds generated JSON
Schema scalar constants to it. The actual provider must still produce bytes;
those bytes pass through unchanged parser, intent checks and Engine validation.
No expected fixture command is substituted for provider output. Wrong valid
commands remain rejected. Dialogue/narrator rules, deadlines, token/repair
budgets, worker and assets are unchanged. This does not expand supported English
syntax or claim the model performs new mechanical interpretation.

Prompt version becomes2.3. Actual accepted2.1/2.2 history remains restorable,
replayable, forkable and exactly retryable without inference; old records cannot
be accepted as a fresh prepared current turn. New2.3 records never rewrite old
provenance. Future memory consumer2.4 remains a separate reserved interface.
Read the [author's exact contract](D04_GUARDED_DIRECTOR_SCHEMA_2026-10-23.md)
and [independent review](D04_GUARDED_DIRECTOR_SCHEMA_REVIEW_2026-10-23.md).
Root independently read the production delta, actual fixture and new tests.

Independent six new production Play cases preserve alias/quantity/child ancestry,
unknown/hidden/overflow/illegal zero-call refusal, exact escaped dialogue,
wrong valid output/no substitution, malformed repair and cancel behavior, and
2.1/actual2.2 history-only admission. Existing bounds/assertions remain intact.

## Actual coordinator checks

Windows11 Pro10.0.26300; Rust/Cargo1.93.1, Node24.22.1/npm11.19.1,
Python3.14.9, JDK17.0.6/Gradle8.11.1/AGP8.10.1/Kotlin2.2.21,
SDK36/NDK29.0.14206865. Task-owned D targets/TEMP, debug0/incremental0;
locked/offline dependencies only. No CUA, desktop control/capture, protected
resource, ADB/device/emulator, model load or generation occurred.

```powershell
python scripts/check.py host --offline
cargo +1.93.1 test --workspace --exclude locallore-desktop-spike --all-features --locked --offline
cargo +1.93.1 clippy --workspace --exclude locallore-desktop-spike --all-targets --all-features --locked --offline -- -D warnings
cargo +1.93.1 test --manifest-path apps/desktop/src-tauri/Cargo.toml --locked --offline -- --test-threads=1
cargo +1.93.1 test --manifest-path apps/desktop/src-tauri/Cargo.toml --features dev-harness --locked --offline -- --test-threads=1
cargo +1.93.1 clippy --manifest-path apps/desktop/src-tauri/Cargo.toml --all-targets --all-features --locked --offline -- -D warnings
cargo +1.93.1 test --manifest-path crates/locallore-eval/Cargo.toml --all-targets --locked --offline
cargo +1.93.1 test --manifest-path crates/locallore-eval/Cargo.toml --all-targets --features local-model --locked --offline
cargo +1.93.1 clippy --manifest-path crates/locallore-eval/Cargo.toml --all-targets --all-features --locked --offline -- -D warnings
node apps/desktop/verify-frontend.mjs
```

| Check | Actual result |
| --- | --- |
| Final complete host runner | 453 workspace Rust+3 linker,381 Python,four fixture bindings,fmt/default strict Clippy PASS; four existing explicit Rust ignores |
| Final portable all-feature workspace / strict Clippy | 464 PASS,four same ignores /PASS |
| Native unit/contract default and dev | 47 default /49 dev+2 contract PASS; one existing symlink-privilege ignore; strict all-feature Clippy PASS |
| Standalone evaluation on same production Play delta, before main-only test/build reconciliation | 23 default /24 local-model synthetic tests PASS, strict all-feature Clippy PASS; no model |
| Frontend/controller/native-double/schema/TypeScript; full Prettier; normal build hook exclusion | PASS |
| Ordinary Android offline bothABI/app+testAPK/JVM/lint/audit | 146 JVM PASS,zero failures/errors/skips; lint0errors/1existingwarning;16KiB audit PASS;78 tasks executed,3m11s |

Android reproduction uses the existing wrapper with a task-local build-directory
init script and quoted argv property:
`java -classpath gradle/wrapper/gradle-wrapper.jar org.gradle.wrapper.GradleWrapperMain -I <own init.gradle> :app:assembleDebug :app:assembleDebugAndroidTest :app:testDebugUnitTest :app:lintDebug --offline --no-daemon --console=plain '-Pandroid.builder.sdkDownload=false'`.
Audit the resulting own app APK using `python scripts/audit_apk.py <app.apk>`.
This is build/JVM/static evidence, not device execution or native WebView rendering.

Root also generated fresh actual production schemas at1e4 via
`LOCALLORE_GUARDED_SCHEMA_OUTPUT=<new own file>` and the focused
`guarded_director_schema` Rust integration test. Their SHA256 is
`a4b66fe0ec00fef809ca18c95f930e5a6c8c5c958b4942ebeafe786b21b5d738`, exactly
matching the original ten-case capture. Root verified the retained standalone
grammar test executable SHA256
`56604f3124a90abed26fe4be48c25eb497990f7d59e7275af999e2122fa0af4e`, then
actually executed it against those fresh cases: **70 native grammar assertions,
10 cases PASS, model_loaded=false**. Root did not recompile that executable;
its pinned converter/compiler provenance remains attributed to the author.
This is actual converter/grammar execution, not worker generation or app IPC.

## Retained failures and limits

The initial integrated all-feature run failed at an accepted-main test fixture's
PID/timestamp create_dir collision, before gameplay. The independent actual
same-clock RED regression, atomic suffix correction and original assertion
preservation are recorded in
[accepted diagnosis](../native/RETENTION_FIXTURE_IDENTITY_DIAGNOSIS_2026-10-23.md).
A root native command initially used the nonexistent feature name
development-harness; Cargo refused before tests. Correct dev-harness invocation
then exposed the separate native long-path export Io bug; #103 corrected that
via a focused actual RED/GREEN test, and final suites above pass. No failure was
counted as a pass or repaired by changing a gameplay expectation/deadline.

Historical curated real-model failures remain failures. There is no new prose,
fallback-rate, latency, enjoyment or quality claim. A future source-bound model
cohort must use unchanged fixtures/budgets/approved assets and report all results.
Curated UI integration, memory-consumer2.4, unsupported natural language,
physical-phone gates and full M05/D04 acceptance remain separate. No milestone
checkbox, public release, settings change or fabricated review is implied.

Private final host/all-feature log hashes:
`d330de2b3f8a476c1e82b4908dcd5d69d1c51314187c22231db1f9b3197000b7` /
`fc05c4da4d1f83252c6f0a2659ec34f337fd87ca1738ce49847e3f382b35a22b`.
Native default/dev:
`402ee3faac8f34e7569cfc4df7febbfe8bd9c31e410861fd60ac2953f06bcb9b` /
`f57883f369fb2120bdd6a7ed05f2f200420d6ab6c6d3cf4558e53e0493fee9a8`.
Android build `2fe593958dd453349716f37bf2ae60d401b7478cead55e81f7f511adf320235d`;
app/test APK respectively
`b01e07f7229fcbafd332bce35df47d19396d90994d97eafb63630712adf4b4ef` /
`e5661bdf6de25dfb87019cd7f58a96e0dd55c32a8760ebb9444814df104169a8`.
Raw logs, synthetic cases and binaries stay local/ignored.
