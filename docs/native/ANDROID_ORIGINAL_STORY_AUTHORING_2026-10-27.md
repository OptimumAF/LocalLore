# Original story authoring — implementation and verification

M09.02/M09.06 with supporting M10.02/M10.03, bounded implementation in review. This work is stacked
on open/unmerged PR #224 at `b6989a38`; no merge is authorized. Full task
checkboxes remain unchanged. [Contract](ORIGINAL_STORY_AUTHORING_CONTRACT_V1.md)
and [ADR](../adr/0013-original-story-authoring.md) describe the frozen boundary.

The implementation adds a generation path for original premises/casts, bounded native
world validation, editable typed author review and explicit atomic creation.
It retains bundled starter choices. World truth, entitled character knowledge,
private beliefs and initial provenance stay distinct; Kotlin does not become
a second world engine. Native IDs/mechanics and complete reviewed content are
engine-owned. A process-local job cannot edit an existing story or create after
cancel/owner close. Replay/recovery never calls inference.

Independent worktrees own the core module/prompts, Android flow/ownership and
original adversaries. Root owns shared Seed/Host/workspace integration, exact
recovery, worker provenance and the fixed verification phase. Original Ashglass
and Copper fixtures differ in actual topology/cast/entities/truth/beliefs;
they are synthetic samples, not model quality evidence.

## Evidence so far

| Actual check | Scope/result |
|---|---|
| Initial core check | Passed18,435ms,1,973 unchanged tracked inputs; earlier provenance shape |
| Initial full core run | Failed one stale generated-schema assertion after71 unit passes; remaining targets not claimed |
| Schema regeneration | Passed17,744ms; exactly host-v1.schema.json/host.generated.ts changed |
| Independent original-world target | All12 passed;7,264ms,1,978 unchanged inputs; before full configuration refinement |
| New Host/SQLite target | All7 passed;30,318ms owner/0.60s runner,1,980 unchanged inputs |
| Android Rust crate/all features |108 passed,0 failed/ignored;46,613ms,1,980 unchanged inputs |
| Full Rust checks at `c4a2da9c` | Core456/4 ignored, storage239/6 ignored, workspace170/1 ignored, Android108/0 ignored;0 failures |
| Strict Clippy at `c4a2da9c` | Passed with warnings denied;27,398ms |
| Python at `c4a2da9c` |1,505 passed,0 failures/errors/skips;178,759ms owner |
| Frontend at `c4a2da9c` | Verification/format passed;30,770ms |
| Input-process build at `c4a2da9c` |305 JVM tests/35 suites,0 failures/errors/skips;11 APK audits;2 lints with3 warnings/0 errors |
| New original-story driver adversaries |12 synthetic cases included in the Python suite; not device proof |

All listed successful owners retain known cleanup/capture and zero owner
stderr. They do not substitute for future checks after later source edits.
Original failed attempts remain preserved privately on C:.

The early full core schema mismatch is repaired by regeneration. A later full
core attempt actually fails7 of12 author adversaries: their synthetic director
budget512 violates the existing PlayProfile350 cap. The fixture becomes320;
the provenance canary/hash oracle and production validation remain unchanged.
An initial strict lint run fails one needless return; the correction passes.

Rapid editor callbacks are also actually reproduced red:12 focused JVM tests,
2 ComparisonFailures. The first epoch/diff correction passes15 tests. Review
then identifies an explicit edit returning to the originally rendered value
that equality inference still loses. Explicit field/choice/toggle intents
replace that inference; the complete18-controller cohort passes in the305-test
build. Structural operations retire epochs, and action/review identity remains
exact. The second counterexample is source-identified, not an executed historical
red. Review also verifies the current controller already synchronizes reviewed
cast names from edited characters; no rename-refusal defect is claimed.

The first separate LiteRT build compiles against the pinned public SDK and runs
569 JVM tests, with2 failures: exact trace-vocabulary assertions still expect
Director/Narrator without the newly implemented Author tag. Those two closed
expectations are corrected to include Author; counters, wire versions, bounds
and production code are unchanged. That failed cohort remains preserved.
Its subsequent lint/packaging/audits are not claimed as completed. A fresh final
source freeze and separate corrected LiteRT qualification are pending.

The corrected `dc8c8a42` cohort passes all569 LiteRT JVM tests/55 suites, lint
with10 warnings/0 errors, dependency/analyzer audits and the candidate APK
audit. It also passes the fresh native10 phase, followed by its exact requested
owned guest closure and7 metadata copies to C: with0 mismatch. A subsequently
run repository formatting gate fails solely the new Rust adversary test file.
Root had omitted that gate earlier. Rustfmt1.93.1 formats the file without
changing assertions. The successful native/host/SDK cohort remains attributed
to its actual pre-format source; a new fresh verification cohort is required.

Broader CI benchmark checks then expose an existing Windows test error:
`test_output_refuses_existing_directory_and_missing_ancestor` expects an
existing C:-TEMP output to reach mkdir, but the unchanged cache-build policy
correctly refuses every non-D: output first. Root retains that failed34-case
attempt and fixes only the test: the C: refusal is exact, and a mocked existing
D: candidate must raise FileExistsError before any owner bytes are written.
No D: filesystem operation or production guard change is introduced.

The final `2ef0f5f4` host cohort passes976 Rust tests (including3 standalone
native-linker cases),11 ignored,1,716 Python tests,305 app JVM cases and569
LiteRT JVM cases. Formatting, default/all-feature Clippy, fixture-output checks,
lints and audits pass. Its native10 phase also passes. Original-story8 actually
fails: wire3/dialog2 pass, while all3 MainActivity cases fail. The first times out
after Create; subsequent startup reports recovery required. No end-to-end
original-story success is claimed for that source. Both exact owned guests are
requested-stopped after known client closure;7 metadata files per guest are
copied to C: with0 mismatch. The separate resource postflight passes with the
existing server unchanged; that does not turn the failed app phase into a pass.

The failure is a production gateway assumption: native original worlds assign
player IDs such as `a-{prefix}-0`, while DurableGateway requires literal
`player` in the fixed native player snapshot. Post-create inspection fails and
later startup hits the same assumption. The correction accepts a bounded native
observer ID, binds it to the attached session/scope and retains response scope/
revision checks. Semantic `player` lens labels in record/fork contracts remain
unchanged. Three focused binding JVM cases actually pass on `f723f2db`
(31,272ms owner,1,997 unchanged inputs); full integration remains pending.

Independent source review then identifies aliasing/overlap cases at the abstract
transport boundary, without claiming executed JNI failures. A fresh attachment
token now fences attach/detach/close and immutable captured scope values. Final
publication atomically rechecks the current observer binding under the same
metadata lock; no native call or suspension occurs under that lock. The existing
Wire method gains deferred same-object/same-session reattachment and overlapping
conflicting-observer cases; the8-method roster and15-second UI wait are unchanged.
A fresh full build/host and native/original emulator cohort must verify this fix.

The `b9bfaee5` correction compiles and passes976 Rust/11 ignored,1,716 Python,
308 app JVM and572 LiteRT JVM cases, formatting/lints/audits, and fresh native10.
Original-story8 again records wire3/dialog2 passed and MainActivity3 failed,
this time solely in the test helper comparing JSON object serialization order:
expected `{story,branch}` and native `{branch,story}` contain the same values.
All3 get past the earlier Create/startup failure. The test now requires exactly
the2 scope keys and compares story/branch values individually; no scope,
revision, player or other gameplay assertion is removed. The failed cohort is
retained. Both exact guests close with known client capture; the independent
resource postflight again leaves the existing server unchanged. A final fresh
cohort is pending for this test-only correction; no8-case pass is inferred.

Review identifies a real recovery design race: looking up a completed authored
seed and then calling insert-or-retry could resurrect it after another Store
deleted it. Recovery is changed to read-only Engine load/presence/full-seed
checks. A new fault-injection test uses an actual second SQLite owner deleting
exactly between lookup and attachment; no reinsert call occurs and the story
remains deleted. This is a source-identified race and a passing corrected
regression, without claiming an executed historical resurrection reproduction.

Other actual Store checks cover no canon before explicit Create, distinct
worlds, invalid/stale/cancelled review, configuration invalidation, provider
failure, worker release, accepted turn preservation, missing-job recovery after
restart, and archive import/recovery without another inference call.

A further source review finds successful recovery did not consume a matching
live review. The corrected eighth Store case uses two actual Hosts/SQLite:
recovery consumes that exact job, binds creation ID/hash before lookup, refuses
existing same-origin and absent alternate targets, and retains the binding after
a refused later review. Exact retries remain read-only; a foreign-job recovery
does not consume an unrelated draft. All8 pass (16,069ms owner/0.78s runner).

Stored origin now binds all11 validated PlayProfile fields, not merely a
profile name. The author recipe fixes its own role-specific budget. The worker
LF source hash becomes
`1e66e0fbcc30534771f0734d03b22612eb67b1287b3d1fa353d13b7d5e126e67`
(25889 bytes), bound in the candidate manifest and Gradle guard. Model/runtime
pins are unchanged; earlier model results retain their earlier source hashes.
No new dependency, download, device setting or model transfer occurs.

The existing worker retains its finite-regex path and exact JSON-schema path
for non-finite schemas. Current official [constrained-decoding documentation](https://github.com/google-ai-edge/LiteRT-LM/blob/main/docs/api/cpp/constrained-decoding.md)
describes JSON-schema constraints; this is API context, not proof that the
selected model completes the new author schema. Pinned-source web retrieval
was unavailable during this check. Actual compilation/public SDK value-object
tests and a future real author inference run must retain separate attribution.
Thinking and speculative decoding remain disabled in the current CPU worker.

## Current integrated checks and recovery

The unchanged executable source at `58e71dde` passes976 Rust tests/11 ignored,
1,716 Python tests,308 app JVM tests and572 separate LiteRT JVM tests.
Repository formatting, default/all-feature Clippy, frontend checks, fixture
output checks, native-linker checks, lints and artifact audits pass. The build
maps877 compiled inputs; each host gate retains1,998 unchanged tracked inputs.
Embedded author prompt/schema files are included in the compiled source map.
JNI cross-compilation covers x86_64/ARM64; this is not ARM64 execution.
The976 total includes the separately retained108-test Android Rust cohort and
3 standalone linker tests, in addition to the core/storage/workspace gates.
An independent file-only audit replays82 build/artifact/output bindings with0
mismatches. Retained lint reports have0 errors,3 ordinary app/controller
warnings and10 LiteRT warnings. Some lint analysis tasks are up-to-date;
neither build is described as forced fresh lint analysis. Both JVM test tasks
actually execute.

Its first fresh native attempt fails before installation or test collection:
the existing-server observer times out at its unchanged15-second budget. All21
SDK client records have matching raw lengths/hashes and known cleanup. The
outer output reader then fails to prove complete capture, so its original
owner result retains `evidence_failed`, cleanup/capture false and null byte
counts. It is not a native10 pass. No timeout cause is established.

A separate recovery checks the exact worker identity is absent, all21 closed
client pairs and the source/request bindings are unchanged, and the fixed
failure path reaches no later SDK dispatch. This qualifies only SDK-client
closure; it does not repair the original outer capture or cleanup evidence.
The unchanged live-owner lease then admits a proposal-bound stop for only that
owned guest. Its original owner handle actually terminates0; its guest receipt
records `stop_requested`, worker1, cleanup/capture/closure true and no flush
claim. An independent file-only audit replays53 recovery bindings with0
mismatches. A new runtime-only retry uses the unchanged qualified source/APKs;
native10 and original-story8 subsequently pass in that retry.

The fresh runtime-only retry preserves the exact877 compiled inputs and C5
APKs. Its native phase passes10 methods across3 classes,271055ms, with90
complete measured SDK2 pairs. The original-story phase passes all8 methods
across3 classes,304445ms, with93 complete measured SDK2 pairs. Both phase
owners exit0 with known cleanup/capture and0 stderr. Independent file-only
replay verifies the complete start/pass/runner records, exact Kotlin rosters,
raw-to-numbered-client matches, observer brackets, source and installed APK
bindings. No method or deadline is weakened.

Original-story coverage is wire3, dialog2 and MainActivity3: malformed input,
cancel/no early canon, exact creation retry after reopen without generation,
scripted-provider label, edits invalidating consent, an edited original world
with retained player after ordinary reopen, cancelled creation preserving the
current draft/scope, and an accepted generated turn with scoped receipts.
Deferred transport cases inside the existing Wire method also exercise
reattachment and conflicting observer publication. These are scripted
inference/real JNI and SQLite tests, not model-quality measurements.

Each exact owned guest is stopped only after its phase has known client
closure. Native/original owner handles actually terminate0; guest receipts
record301998/328748ms, `stop_requested`, worker1, known cleanup/capture/closure
and no flush claim. Seven metadata files per guest are copied to C: with0
mismatches. The final one-shot read-only postflight passes after both closures,
with the existing server unchanged and0 device calls/server lifecycle actions.
The fresh protected-process inventory contains0 identities; this is an
observation, not a claim that another chat's emulator was stopped.

Private recovery archives preserve earlier failures separately from success:

| Selection | Original files / indexed controls | ZIP SHA-256 | Independent replay |
|---|---|---|---|
| Historical C1–C3 |2157 /3 |`9dcf70959d39b63eee0ccfdd3d5650062b91a87e02f61a3023d31714ef28d8bd` |0 missing/mismatches |
| C4 UI assertion-order failure |927 /3 |`526e81d3b98fa1fb01b696bf7eadff2659535e79acc6efcb52ac13df215126c4` |0 missing/mismatches |
| C5 preflight/capture failure |559 /3 |`8ceeb2d583341c6f588cb279c6f27e6e3edc898bd8e9e1cc3f157eae6ba380d0` |0 missing/mismatches |
| Final runtime/source/recovery |442 /4 |`09457cc2442cee5cb6d284dd5aecccf2be98b30276b1658b7480acdcd61668cb` |0 missing/mismatches |

These explicit admitted metadata/helper/report/audited-artifact selections stay
on C:. They exclude model weights, saves and live guest data. Byte preservation
does not qualify a failed feature test; each archive records acceptance false.

The final recovery contains446 indexed originals/controls and copies,447 exact
ZIP members and449 output files,27,652,046 bytes total. Its index SHA256 is
`c05e1e5a8cdc05b78c07cda4269d06c2b7d3046547fbe33331493921897f9164`;
the independent streaming verification result SHA256 is
`205107234dfb43515147a208125f31257a6116bd20d4072504da282e66dc6570`.
The replay checks all originals/copies/ZIP members and the prior C5 seal,
including the three exact closed failed-guest metadata files. Unknown payloads
are refused rather than recursively admitting arbitrary generated folders.

Source history is separately verified at checkpoint `68c9b216`: all1211 named
Git references match the bundle's1526 heads, including314 additional worktree
pseudo-heads. The12,557,958-byte bundle SHA256 is
`d5c824fbe60aeebf476d61ddbf85cecf3542280eba2838efeed5c6e214b9ddf4`.
The first whole-head comparison refuses because named refs and worktree heads
are different sets; the next classifier omits `main-worktree/HEAD` and also
refuses. A read-only corrected collector verifies every named ref with no
missing/mismatched entry and records both original refusals. No bundle is
recreated or failed runtime result repaired. This report's later preservation
metadata commit is separate from that source checkpoint.

Android's8 fixed original-story methods and the native10 prerequisite now
qualify this bounded scripted API35/x86_64 slice. Full task checkboxes remain
unchecked pending broader criteria and owner acceptance. Current-source legacy
creation19/broad89 regression is the next runnable supporting verification;
older-source results are not promoted to this build.
No real-model compatibility/quality/performance is inferred from SDK value
objects, injected resources or scripted plumbing. Physical/ARM64, semantic narrative quality, accessibility,
external process death and joined callback drain remain separate gates.

Source and reports are committed/pushed during implementation. Private evidence
and recoveries stay on C:; model weights, saves and private diagnostics stay out
of GitHub. No unrelated emulator stop, server lifecycle operation, system
settings change, release, permission administration or merge is performed.

## Reproduction and artifact bindings

The retained commands use Rust1.93.1, Python3.14 and JDK21, with cached
dependencies and the Android prerequisites in the app README. The following
are the checked command arguments; evidence/output directories must be new.

```text
cargo test --locked --offline -p locallore --all-features
cargo test --locked --offline -p locallore-storage --all-features
cargo test --locked --offline -p locallore-workspace --all-features --features locallore-storage/development-fixtures
cargo test --locked --offline -p locallore-android --all-features
cargo fmt --all -- --check
cargo clippy --locked --offline -p locallore -p locallore-storage -p locallore-workspace --all-targets --all-features -- -D warnings
cargo clippy --workspace --exclude locallore-desktop-spike --all-targets --locked --offline -- -D warnings
cargo run --locked --offline -p locallore --example android_fixtures -- --check
rustfmt --check --edition 2021 apps/android/native-linker.rs
rustc --test --edition 2021 apps/android/native-linker.rs -o <new-linker-test-binary>
<new-linker-test-binary>
python -B -m unittest discover -s scripts/tests -p test_*.py
python -B -m unittest discover -s benchmarks -p test_*.py
python -B -m unittest discover -s benchmarks/spike/litert -p test_*.py
python -B -m unittest discover -s benchmarks/spike/llama -p test_*.py
python -B -m unittest discover -s benchmarks/spike/android/litert -p test_*.py
python -B -m unittest discover -s benchmarks/spike/android/llama -p test_*.py
python -B benchmarks/android_process_verification.py build --sdk <SDK> --java <JDK21> --out <new-build-evidence>
python -B benchmarks/android_process_verification.py components --out <new-native-evidence> --sdk <SDK> --build <qualified-build-result> --running <owned-native-running> --proposal <owned-native-run-proposal> --server <fresh-existing-server-pin> --powershell <Windows-PowerShell>
python -B benchmarks/android_process_verification.py original-story --out <new-original-evidence> --sdk <SDK> --build <qualified-build-result> --running <owned-original-running> --proposal <owned-original-run-proposal> --server <fresh-existing-server-pin> --powershell <Windows-PowerShell>
```

Frontend checks from `apps/desktop` run `node verify-frontend.mjs` and
`node node_modules/prettier/bin/prettier.cjs --check "ui/*.{ts,tsx,html,css}" "*.{json,mjs}"`.
The separate LiteRT Gradle wrapper uses `--offline --no-daemon --no-build-cache
--max-workers=2 --console=plain --project-cache-dir .gradle-litert-worker`,
with `localLoreLiteRtVerification=true`, `android.experimental.lint.version=9.4.1`,
Java installation auto-download and Android SDK download false, and Kotlin
incremental compilation false. Tasks are `:app:cleanTestDebugUnitTest
:app:testDebugUnitTest :app:lintDebug :app:auditLiteRtDependencies
:app:auditLintAnalyzer :app:cleanPackageDebug :app:cleanPackageDebugAndroidTest
:app:assembleDebug :app:assembleDebugAndroidTest`.

Compiled source-map SHA256 is
`dabb92be2a7f3b77d6d96d4ff60af03a73c1cd0208cc4d572ab17274786f620a`.
Later report commits are separate from the historical1,998-file gate maps.

| Artifact | Bytes | SHA256 |
|---|---:|---|
| Process-verification app |42452872 |`30233d3f9d3502ce7ce94c40f8906f2bf50874382efcbb7cf503037e343e2746` |
| Process-verification tests |3185615 |`65f5b8d159505411cc7614cee5e6bccc97ff627d4f62efb431c42e9fa21a257f` |
| Process controller |55073 |`6ea09f4c5105d62e61498d2bebc05de52ce597e30b9681e4975a323b36ef7693` |
| LiteRT app |78238576 |`2509c77b40950b5d374ac095592d700c98f655218e3798d7818b1a2625a76eeb` |
| LiteRT tests |2212547 |`3d1a500b6410d2c0d925b3bfcc6494bb361d1e62724473902cfdb61f6d9f2a36` |
