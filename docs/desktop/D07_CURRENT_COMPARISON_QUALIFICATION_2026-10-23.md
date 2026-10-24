# Current-pipeline comparison qualification

Started 2026-10-23 local date; continued 2026-10-24. Retained execution
timestamps are UTC and attributed below.
Refs #29 D07.01–.06 partial / #11 M07.01. **Bounded qualification record;
coordinator review/adoption remains pending.**
This report does not accept the whole D07 milestone, prose quality, general
tokenizer/template-budget guarantees or a physical-device gate.

The sole new path belongs to author_core_review on
`docs/d07-current-comparison-qualification`, based on
`b8913a72968c0a971466397e8b9fab3551f38261`;
[claim #29 6380432018](https://github.com/OptimumAF/LocalLore/issues/29#issuecomment-6380432018).
The author reads source/logs and writes this document only. All runtime
execution below belongs to coordinator Root; no reviewer execution is inferred.

## Scope and unchanged experiment

The [current-pipeline contract](D07_COMPARISON_CURRENT_PIPELINE_CONTRACT_2026-10-23.md)
and [forwarded-budget contract](../eval/D07_FORWARDED_CONTEXT_BUDGET_CONTRACT_2026-10-23.md)
freeze the scope. The existing courier suite retains all **24 original texts**,
four scenes, expected commands and three guard refusals. Each successful
scripted arm must produce 21 accepted turns, three exact refusals and 42
provider roles, without repairing failures into expected canonical outcomes.
The profile remains **4096 context / 350 Director / 350 Narrator output tokens**,
at most one repair. No corpus shortening, hidden budget increase, weakened
mandatory evidence or new persistence/provider implementation is introduced.
The suite SHA-256 remains
`6e7172c6c8bedb4b82b703aac30b7b92c5a924d0203578cb2f027611d7def21a`,
asserted by the frozen Core constructor oracle.

The two actual Core policies are StateRecentTranscriptV1 and
StateRelevantMemoryV1: state+recent-transcript control versus
state+relevant-memory. Both retain mandatory current state and epistemic
evidence. This is not literal transcript-only versus memory, nor raw versus
verified representation. PairedSnapshots uses the same actual validated
reference prefix in two isolated Stores; ContinuousRollout retains each arm's
own actual chain and honestly records divergence/dependency failures.

The fresh Play2.5 admission correction uses **one compiler packing pipeline**
and a closed Core frame tied to the actual Engine/request/profile. The same
projection/renderer supplies fit checks and the real GenerationRequest.
It budgets the complete forwarded Director prompt and schema, including the
permitted exact 114-byte repair suffix, rounding the combined UTF-8 byte
count once with ceil(bytes/4). The unchanged total reserve is 512: actual
350 output plus an explicitly unmeasured 162 template/envelope estimate for
the pinned profile. The minimum supported context still uses reserve 511.
This is an estimate, not a measured tokenizer/template guarantee.

Full diagnostic ContextPackage caps remain **24,576 bytes / 128 records**;
its byte/token fields still describe the full diagnostic wire. Generic
compiler admission keeps that original meaning. Current Play alone selects
the forwarded fit basis; mandatory eligibility, observer filtering, canonical
validation, narrator policy and historical Play2.1–2.4 replay remain separate
authorities. Recorded retries precede fresh admission and call no provider.
The exported estimate/repair helpers supply no prompt authority, actor grant
or alternate selector.

Current comparison capture validation checks retained actual request bytes,
recording hashes, privacy, output cap, projection equality, exact repair
relation and forwarded admission. New-source count metadata is regenerated
and compared; report JSON is not trusted authority. Historical omitted
fields retain their old serialization/key and read-only source mismatch,
without gaining invented estimates or permission to resume under new source.

## Retained failures and completed checks

| Source / retained log | Actual result and disposition |
| --- | --- |
| Original comparison_runner compile, d07-comparison-compile-first.log | Compilation succeeds in 17.32s; this is no-run evidence, not a runner pass. |
| d07-comparison-focused-first.log | E0061: an old test called character_context with one argument instead of observer/scope/revision. No runtime tests ran in that invocation. Fixture correction 0fd803b supplies the actual scope/head without changing assertions. |
| Corrected fixture, d07-comparison-focused-corrected.log | **5 passed / 4 failed**, 55.47s. Scripted reference/paired/tamper cases fail ReferenceFailed; rollout's all-passed assertion fails. The actual failure report is preserved rather than treated as a successful reference or quality result. |
| Pre-fix a082dc8, d07-forwarded-budget-original-red.log | **4 passed / 2 failed / 1 ignored**, 0.33s after 18.99s compilation. The actual head8 and unchanged24-chain cases fail TooLarge. Generic wire rejection, regular/repair bytes, true oversized mandatory rejection and historical replay already pass. |
| Corrected forwarded admission, d07-forwarded-budget-first-green.log | Same seven declarations: **6 passed / 0 failed / 1 ignored**, 1.13s after 11.57s compilation. Historical baseline-only probe remains ignored, not silently turned into a post-fix acceptance case. |
| baa3283, d07-eval-lib-forwarded-budget-first.log | **39 passed / 0 failed / 1 ignored**, 42.89s. Includes actual Host/Store capture metadata removal/tampering, rehashed prompt/schema over-budget refusal, output351 refusal and exact repair-whitespace refusal. Synthetic bounded provider, not model execution. The opt-in native-owner case is ignored. |
| b8913a7, d07-runner-forwarded-budget-first.log | **9 runner passes**, 238.42s, plus **3 protocol passes**, 0.03s. Original assertions unchanged: actual scripted reference21accepted/3guards/42roles, paired first-scene12rows, resumed continuous48rows/84roles, zero-role committed lost-ack lookup, source/tamper/privacy/reservation/read-only gates all pass. This is not a full24-attempt paired-model comparison. |
| 4a36b72, d07-genuine-historical-readonly-first.log | Explicit opt-in **1 pass**, 3.53s. Opens the genuine pre-forwarded completed synthetic rollout, retains every original failure/field/byte and refuses execution against the new source. |
| d07-host-policy-original-compile.log | E0277: the fixture attempted to deserialize Core Receipt, which is intentionally Serialize-only. No tests ran; production authority was not opened to satisfy the fixture. |
| Serialized-only fixture correction 9e91ef3, d07-host-policy-serialized-fixture-first.log | **1 passed / 3 failed**, 0.07s. The three failures read prompt_version from the ready-phase null receipt; this exposed the fixture's wrong phase assumption, not missing committed provenance. |
| Corrected committed fixture a05254c, d07-host-policy-committed-fixture-corrected.log | **4 passed / 0 failed**, 0.13s. Tests explicitly preserve ready.receipt=null and unchanged precommit canonical state; inspect provenance only after actual committed replies. Both policies, legacy default, held-work configuration fences, policy-changing recorded retry/zero roles and JSON policy refusal pass. |
| a05254c, d07-shared-full-first.log | Four-package batch exits101 during compilation: comparison_policy.rs directly names serde without a direct dependency (E0433). No tests ran. Test-only 8b4422b uses the existing serde_json stream API; assertions and dependencies are unchanged. Corrected result follows. |
| 8b4422b, d07-shared-full-fixture-corrected.log | **743 passed / 0 failed / 10 ignored**, 110 result groups including zero-test documentation groups. Actual four-package **host-feature** suite, not an all-features run. Includes long-history stress, unchanged generic compiler/legacy replay, and actual Store/Repository comparison_policy checks. |
| d07-workspace-format-first.log / d07-eval-format-first.log | Workspace and standalone evaluator Rustfmt checks pass, both empty logs. |
| 8b4422b, d07-compat-shared-clippy.log | Strict workspace all-targets/all-features Clippy (desktop excluded) passes; stage wall duration29.29s. This is a broader feature/lint invocation than the four-package host-feature test suite. |
| 8b4422b, d07-compat-eval-remaining.log | **15 passed / 1 ignored**: memory_comparison12, local_model_review3, curated_integration_review0passed/1ignored. The ignored native case was not executed. |
| 8b4422b, d07-compat-eval-clippy.log | Strict evaluator lint exits101 on collapsible_if in the dependency oracle. Root 39c770d collapses only equivalent phase-and-disjunction guards, with no lint waiver, changed oracle or acceptance relaxation. |
| 39c770d, d07-dependency-oracle-lint-corrected.log / d07-historical-dependency-guard-corrected.log | Focused actual dependency regression **1 pass /11filtered**,1.99s; genuine historical inspect/resume test **1 pass**,3.46s. Old skips, source mismatch and every retained byte stay unchanged. |
| 39c770d, corrected-prefix compatibility logs | Evaluator strict Clippy **pass**,6.14s; full frontend and frontend format **pass**; native normal **88 passes /1ignored**,18.53s (compile35.38s); native dev **92 passes /1ignored**,20.36s plus standalone2passes (compile28.52s); native strict Clippy **pass**,16.48s; normal native build **pass**,14.67s. These are Rust tests/build and synthetic/headless frontend checks, not a D07 WebView journey or model comparison. |
| 39c770d, d07-compat-lint-corrected-android.log | **BUILD SUCCESSFUL**,11m42s, all78tasks executed. Fresh JNI x86_64 and arm64 builds,182JVM tests and APK/lint/static audit evidence below; no device execution. |
| 39c770d, d07-real-owner-admission-refusal.log | Explicit opt-in native-owner refusal test **1 pass /39filtered**,8.38s. It proves refusal before comparison admission when the native runtime is already owned; no inference or model-quality result. |
| Frozen clock APIs, d07-clock-frozen-first-compile.log | Exit101,E0425/E0599: new private clock APIs are absent. **Zero tests ran**; this is not a behavioral RED result. Frozen source f55c178 was imported as dd87579, then registered/formatted at5df28ae. |
| Clock implementation e3b22bc, d07-clock-corrected-first.log | Exit101,E0425: one before-commit check still named removed limit. No tests ran. febc326 uses the same absolute deadline at that final check. |
| febc326, d07-clock-before-commit-corrected.log | **7 passed /0failed /38filtered**,5.71s after5.26s compilation. Actual-open charging/settlement, original-origin continuation, insufficient/exhausted admission, preserved interrupted unknown reservations and absolute turn deadline/prelude/cleanup cases pass. |
| febc326, d07-clock-full-evaluator-first.log | Full all-features evaluator **73 passed /0failed /3ignored**, compile14.33s. Library46/1ignored(51.72s), runner9(266.67s), local_model_review3, memory_comparison12 and protocol3 pass. Historical and curated native cases remain separately ignored, as does the library opt-in owner case; zero-test main/docs add no executed tests. |
| febc326, d07-clock-compat-results.json | All seven stages exit0: strict evaluator Clippy12.55s, full frontend and format, native normal88/1ignored(17.64s), dev92/1ignored(27.17s)+standalone2, strict native Clippy11.08s and normal build14.28s. Source/exit come from the completed coordinator manifest, not partial native-model output. |

The original frozen Core declarations precede production (edf4d265 / contract
03308ea1). The Core fix and evaluator closure were separately allocated and
reviewed; the contracts retain their exact commit inventory. Source baa3283
merged accepted typed-inference PR #137. Candidate b8913a7 then merged accepted
desktop-author PR #135. That integration does not rerun or relabel either
PR's evidence and does not make the D07 comparison an author/Domain2 corpus.

## Evidence boundary and open gates

| Required evidence | Current disposition |
| --- | --- |
| comparison_runner + memory_comparison_v2 terminal batch | Complete:9runner+3protocol passes above. Initial seven-pass partial output was not counted as a completed result. |
| Current Core/Host fixture and full compatibility checks | Host4, shared743/10 ignored, evaluator15/1 ignored, strict shared/eval/native lint, frontend/format, native normal88/1 ignored, dev92/1 ignored+standalone2, normal build and fresh Android compatibility all passed. No runtime/UI/model execution is inferred from build/unit evidence. |
| Genuine historical complete-cohort opening | Passed actual opt-in test at 4a36b72; see precise inventory/old-field boundary below. |
| Real local-model current comparison | Source39c full paired results remain separate. Closed corrected-source febc cohort below has bounded paired12rows/24roles and complete rollout48rows/84roles, all structural/privacy checks passed; quality/human acceptance remains false. Root review/adoption remains separate. |
| Exact reproduction and environment | Completed commands below, including actual arguments retained in corrected native process records; fresh toolchain versions and terminal manifests recorded. Unrecovered older invocation flags are not inferred from filenames. |
| Quality, app UI and physical qualification | human_reviewed=0, quality_accepted=false. Formal faithfulness/agency/readability/repetition/enjoyment review remains unavailable; NPC distinctiveness is unsupported by this narrator-only lane. No actual current-comparison desktop WebView journey, Android parity or physical-device qualification. |

## Genuine historical read-only compatibility

The test source was separately frozen at 832e8be, imported as d5d6913 and
formatted only at 4a36b72. Its opt-in path selects the retained original 33356
rollout executed at **0fd803bcba50fa700efc27072861a51dc6ea3be3**, before
forwarded-estimate fields existed. It pins original manifest SHA-256
`3e6ff45d65582ff9b65e550210dc0b14ff8a9fbf7d538a878d7f35014b0d668b`
and report SHA-256
`4167a78bb84ea5cad983d7eb8ff83fb0be1c4e93d4deb019bfac1be05f785a2d`,
plus both actual Store hashes and retained capture/raw/checkpoint evidence.

Actual current inspect preserves the original **four scenes /48rows /22passes /
26failures** and all report values except source_matches=false. The original
missing estimates stay absent; no successful reference or new metadata is
fabricated. Actual scripted resume returns **CheckpointMismatch** before
admitting work. Full bounded file/entry inventories before and after both
operations are equal. This qualifies this genuine historical cohort's
read-only compatibility and refused resume, not model quality or every possible
old archive/report version.

Root's completed commands, from repository root:

```powershell
cargo test --offline --manifest-path crates/locallore-eval/Cargo.toml --features local-model --test comparison_runner --test memory_comparison_v2 -- --test-threads=1

$env:LOCALLORE_D07_HISTORICAL_COHORT = '<retained-original-synthetic-rollout>'
cargo test --locked --offline --manifest-path crates/locallore-eval/Cargo.toml --features local-model --test comparison_historical_readonly genuine_pre_forwarded_cohort_opens_read_only_and_cannot_resume -- --ignored --exact --test-threads=1
```

The environment path is local-only; the ignored test does not generate an old
fixture or permit arbitrary SQL. These invocations are coordinator execution,
not runs by this documentation author.

Root's actual Host command:

```powershell
cargo test --offline -p locallore --features host --test d07_host_policy -- --test-threads=1
```

The final Host fixture correction changes only tests/d07_host_policy.rs.
Its native Persistence fixture checks the full accepted basis and exact draft
before applying the real Engine.commit_prepared; the other cases commit on
the actual in-memory Host path. No production Receipt deserializer, prepared
receipt exposure, Store writer or phase contract was added. This is Core/Host
fixture execution, not desktop IPC or a real-model result.
The native snapshot fixture's status is draft-only even after its Engine
commit, so that case supplies no durable reopen/retry evidence. The separately
executed actual Repository/Store comparison_policy fixture closes that narrow
gate: both policy arms inspect actual committed Play2.5/compiler2 provenance,
reopen at r13, compare stored receipt/canonical bytes and retrieve the exact
recorded reply with zero additional provider roles. It also distinguishes
recent transcript optional units from relevant-memory selection and excludes
unrelated history/secret material from the narrator.

Actual completed broad command:

```powershell
cargo test --offline -p locallore -p locallore-storage -p locallore-workspace -p locallore-android --features locallore/host -- --test-threads=1
```

Root freshly records rustc **1.93.1 (01f6ddf75)**, cargo **1.93.1 (083ac5135)**,
Node **24.22.1** and Java **17.0.6**. Tests use the existing task-owned target
and serialized execution; no toolchain/model download or physical-device
execution is inferred. Original compatibility manifest records source 8b4422b
and the evaluator lint exit 101; corrected manifest records all eight resumed
stages exiting 0 at 39c770d. It does not relabel the earlier failure as a pass.

Completed compatibility invocations, from repository root, use the existing
owned `<shared-target>` (the placeholder replaces only the local target path):

```powershell
cargo clippy --workspace --all-targets --all-features --offline --locked --exclude locallore-desktop-spike --target-dir <shared-target> -- -D warnings
cargo test --manifest-path crates/locallore-eval/Cargo.toml --features local-model --offline --locked --target-dir <shared-target> --test memory_comparison --test local_model_review --test curated_integration_review -- --test-threads=1
# First invocation failed; corrected source 39c770d passed:
cargo clippy --manifest-path crates/locallore-eval/Cargo.toml --all-targets --all-features --offline --locked --target-dir <shared-target> -- -D warnings

cargo test --manifest-path apps/desktop/src-tauri/Cargo.toml --offline --locked --target-dir <native-target> -- --test-threads=1
cargo test --manifest-path apps/desktop/src-tauri/Cargo.toml --features dev-harness --offline --locked --target-dir <native-target> -- --test-threads=1
cargo clippy --manifest-path apps/desktop/src-tauri/Cargo.toml --all-targets --features dev-harness --offline --locked --target-dir <native-target> -- -D warnings
cargo build --manifest-path apps/desktop/src-tauri/Cargo.toml --no-default-features --offline --locked --target-dir <native-target>

# apps/desktop; node denotes the pinned task-owned 24.22.1 launcher:
node verify-frontend.mjs
node node_modules/prettier/bin/prettier.cjs --check 'ui/*.{ts,tsx,html,css}' '*.{json,mjs}'
```

Root's local serial launcher uses one Cargo job, dev/test debug info 0,
incremental compilation disabled, owned temporary/Gradle/output directories, existing SDK/JDK,
empty LIBSQLITE3_FLAGS and no SDK download. Source and exit for each stage
are recorded before advancing. The original failed stage manifest is retained;
the new prefix does not overwrite it.

The normal build at 39c770d records a **29,160,960-byte executable**, SHA-256
`095f5eaa94ef075625973576986a7599850da73b20922579259ce0b3f2a5d0d1`,
and **492,023-byte normal app.js**, SHA-256
`e0c09f611bfa9c4cf7d26ed2caf311bbc7ec07b9f5b8d02317ceef8d34dbff56`.
Five fixed development fixture/gate markers are absent from the executable;
frontend hook exclusions and native handler cfg are checked separately.
This is **bounded static byte evidence**, not exhaustive exclusion proof or
actual application execution. The local record d07-normal-artifact-evidence.json
is 903 bytes, SHA-256
`fec85dab82258489cc0318b75393e31785345c6b85946766b5f0f8728690f583`.

## Fresh Android build/JVM/static evidence

At 39c770d, all 78 Gradle tasks executed; x86_64 JNI release compilation took
2m25s and arm64 took 4m40s. **182 tests / 22 JUnit XML files / 0 failures /
0 errors / 0 skips** are fresh, timestamped 06:06:15.5456086Z–06:06:15.5566332Z
on 2026-10-24 UTC. Fresh lint at 06:08:46.7990741Z has 0 errors and one existing
GradleDependency warning. These are host JVM tests and builds, **not Android
instrumentation/device execution or Android D2 parity**.

| Android artifact | Bytes / SHA-256 |
| --- | --- |
| App APK | 24,115,468 / `83281d57b8f0682e559ff90da1650c8b7a155d528099cb7d36919034623c4720` |
| Instrumentation APK, built only | 1,715,781 / `40450f596df0d5b5db724f5452aac63124f820cefa20d82bd3a7733a39dc4c36` |
| Fresh 22 XML aggregate | `2c6352b1dd6c94ee2876f12e8f856086b934fb6a2f46d43e0f15b62efebda8b7` |

Static APK audit passes: four packaged ELFs have 16KiB LOAD alignment; the only
permission is the generated non-exported dynamic-receiver permission.
Instrumentation APK timestamp 06:07:29.7033106Z is fresh, but no device is
launched. The XML aggregate was independently recomputed read-only: ordinal
filename order, UTF-8 without BOM, filename TAB bytes TAB lowercase SHA-256 LF,
including final LF. An earlier unspecified aggregate used literal backtick
separators; its retained metadata is superseded **only for that aggregate**.
XML bytes, counts, timestamps, lint and APK evidence do not change.

Root's Android invocation, from apps/android with the recorded existing JDK/SDK
and task-owned output init script:

```powershell
java -classpath gradle/wrapper/gradle-wrapper.jar org.gradle.wrapper.GradleWrapperMain --offline --no-daemon --max-workers=1 --console=plain -Pandroid.builder.sdkDownload=false --init-script <owned-output-init.gradle> :app:testDebugUnitTest --rerun :app:assembleDebug :app:assembleDebugAndroidTest :app:lintDebug

# Repository root; ANDROID_HOME points to the existing SDK:
python scripts/audit_apk.py <owned-output-root>/_app/outputs/apk/debug/app-debug.apk
```

Retained metadata hashes: d07-android-artifact-evidence.json (387 bytes)
`41b9d303252fba88e4c269581234832ccf1b0ba29ea606d9388f432588e2d3b6`;
d07-android-report-evidence.json (508 bytes)
`9e9fb327f5f18d20666a208576558330bb5dd57c58182f899ea32f5fc0d151e3`;
d07-android-report-aggregate-corrected.json (483 bytes)
`c0e3f9eba3d3204345b83e5f9c8a5b8a022b2ba88be209e0802613feab080ac6`.
Local d07-compat-checks.ps1 SHA-256 is
`1b200ca9f336b0959315030648c190f1f3d079bf8212e3a14b206a015bd3c5e7`;
original results manifest SHA-256 is
`4385a4e0b68d91f7dc434bdfc0a97fedab3d5620658abcebc7baf7895b7ce937`,
corrected terminal results SHA-256 is
`eb30f97ab005ad62e22a488be3126ae5592e75f8f34fced8309fb830e8dd0c06`.

## Original-source actual paired comparison; old timings unqualified

Authorized allocation [#29 6380754782](https://github.com/OptimumAF/LocalLore/issues/29#issuecomment-6380754782)
runs at clean 39c770d. Local cohort
`d07-current-native-d5e85003-0ffe-4d51-b13c-a3affe062a4c` first constructs a
fresh **scripted** reference:24 attempts/21accepted/3guards/42roles, exit0.
This is the bounded reference prerequisite, not native model-arm generation.

Its first actual native PairedSnapshots process then exits0 with **12
structural rows passed /24roles /1of4scenes**, elapsed323,466ms. All privacy
checks are true, with no repairs/errors and maximum forwarded estimate3259.
The process stderr is empty. These are finite partial actual-model observations;
they do not qualify unexecuted scenes, rollout or statistical memory benefits.
The same run subsequently resumes without retuning the original corpus or budgets.

The continuation exits 0 at source 39c with **completed=true, four scenes,
48 structural rows passed, 84 roles, zero repairs and zero privacy failures**.
Its six error fields are the expected zero-role refusals: courier-09 Inventory,
courier-10 Ability and courier-24 ClarificationRequired, once per arm.
They are not six unexpected failures. Maximum forwarded estimate is4090,
physical setups2, unavailable=[], human_reviewed=0 and quality_accepted=false.
The continuation process separately takes **730,199ms**, starting
2026-10-24T06:30:06.7166193Z and ending06:42:16.9326310Z. Its stderr is empty.
The initial323,466ms and this continuation have different process scopes;
neither is presented as final-source charged-turn latency or an arm ranking.

Before PR adoption, independent source review identified two timing/accounting
gaps at this exact source: ComparisonSession::open performs reference copying,
replay and checkpoint validation before Ledger.started; the turn watchdog
creates a new Instant after Host/setup/free_text prelude. This can omit setup
cost and extend the nominal turn interval by its prelude. **No observed
overrun is claimed.** Outer process elapsed time, structural/privacy outcomes
and raw evidence remain source-bound facts; they do not qualify the flawed
accounting/deadline implementation. The pinned old paired run completed
unchanged; no original-source rollout was run. Root froze clock regressions
and corrected that boundary, then ran the bounded paired confirmation and
complete rollout below. Old timings and calls are not attributed to that fix.

Corrected clock source is **febc326426096f66deb7262f2651e542a3781db6**.
A continuing invocation now keeps one monotonic public-entry origin through
manifest/reference/checkpoint replay. Both arm clocks conservatively include
common opening work; only measured other-arm work/native setup share are
excluded. Admission requires the unchanged full preparation reserve, and
interrupted unknown reservations remain fully charged. Native asset-phase
120-second allowance is distinct from opening/replay cost. The caller and
watchdog share one absolute deadline: the earlier of original turn start+60s
or current instant+actual remaining active time minus cleanup reserve. Prelude
consumes the turn allowance without being subtracted twice from already-current
remaining time; an expired queued turn cancels before provider dispatch.
This remains cooperative cancellation, not hard real-time preemption.

All three clock compile/test invocations used the same actual command below;
its two compile failures and seven-pass result remain separate:

```powershell
cargo test --manifest-path crates/locallore-eval/Cargo.toml --locked --offline --jobs 1 --target-dir <shared-target> --lib local_lane::comparison::clock_review_tests -- --nocapture --test-threads=1

# Full corrected evaluator, actual completed invocation at febc326:
cargo test --manifest-path crates/locallore-eval/Cargo.toml --all-features --locked --offline --jobs 1 --target-dir <shared-target> -- --test-threads=1
```

Source comparison from 39c770d through febc326 changes only evaluator
local_lane.rs, comparison.rs, the new clock tests and the contract document.
Core/Host/Store/Android source trees are unchanged. The earlier shared/native/
Android results retain their original source attribution; they are not called
reruns at febc326. The evaluator/native artifact subsequently rebuilt successfully
and its corrected-source strict/frontend/native tests passed as above; fresh
model confirmation subsequently completed below. Independent source rereview reports no further clock
finding at febc326 ([call-site evidence](https://github.com/OptimumAF/LocalLore/issues/29#issuecomment-6381131827));
that review is not runtime or owner acceptance.
The completed seven-stage clock compatibility manifest is1,466 bytes,
SHA-256`4e28d332f145e0cc07fcbe50c9c607318e760b2ef673b8bb10902c6be1588e91`;
its local d07-clock-compat-checks.ps1 is4,086 bytes,
SHA-256`3c4e2bbd0d755ab343e3bcd244bb195d3aa641b61a5e2dadeabf81e13d5c01e8`.
It uses the same exact evaluator/native/frontend command arguments shown in
the compatibility section, without rerunning Android or relabelling its
earlier source 39c evidence.

Reported old-source diagnostics are retained in paired-completed-analysis.json,
2,677 bytes, SHA-256
`0de743ae6b6d303dda75be9b2239c9e47adab1a7b1c5d8ed2890773717326943`.
The summary uses **lower median** (sorted index floor((n−1)/2)) and
**nearest-rank p95** (ceil(0.95n), one-based). These pooled old-source values
are diagnostics, not corrected-clock qualification or an arm ranking:

| Reported duration | n | Lower median ms | p95 ms | Maximum ms |
| --- | --- | --- | --- | --- |
| All turn rows, including six zero-role guards | 48 | 20,104 | 23,707 | 24,762 |
| Generated turns only | 42 | 20,881 | 23,707 | 24,762 |
| First final response, including guards | 48 | 19,953 | 23,395 | 24,692 |
| Commit | 42 | 139 | 366 | 425 |
| Director parent role | 42 | 18,208 | 20,394 | 20,902 |
| Narrator parent role | 42 | 1,755 | 2,556 | 3,580 |

Across84 roles the retained worker reports max input3,673/output98 tokens,
sampled peak working set1,217,949,696bytes/private941,670,400bytes and lifetime
peak working set1,232,691,200bytes, with zero sample failures/incomplete role
rows. These are **worker-process-only** counters, not whole-app memory,
Android/phone capacity or true-tokenizer fit for arbitrary future prompts.
Physical setup19443ms is a distinct reported scope, not an additional arm's
independent cold-load measurement. No timing scopes are combined or averaged
into a claimed latency/quality improvement.

Quality remains **not accepted**. The coordinator observed generic forest
narration unrelated to the actual Say utterance. A structural row pass is not
a prose-quality pass, and no human-rubric acceptance is inferred. Actual
model identity and source are bound to the retained report:

| Partial native binding | SHA-256 / identity |
| --- | --- |
| Profile | qwen3-0.6b-q8-cpu-v1;4096/350/350;repair1;deadline120,000ms |
| Model | `9465e63a22add5354d9bb4b99e90117043c7124007664907259bd16d043bb031` |
| Profile manifest | `01ad542001b04a96f4a8ed6c841be1866eb025350836e0c5d0a4969fdb361d38` |
| Runtime revision | `620d2225cc436ab0b001e3200e590e3b286ef9ab` |
| Template | `57f1fd00f0013a2be96aa79b857391f27e23df5b5f847072b524c897e24d0361` |
| Worker | `b5dd124e484c67c9dda5aebb2cdff1878ccefd0fba99aba4788e00a166f68434` |

Frozen initial-process evidence: paired-initial-process.json,271bytes,
SHA-256`5ac69f2d365824356ec59573ccda3d32bdef597e5935080b946a3b54b277127c`;
paired-initial-stdout.json,92,273bytes,
SHA-256`46c7aa18723f6526f40328e1c9a5e6de5b3d5c11fc7247476be1df10ffa4cbdb`;
paired-initial-stderr.log,0bytes,empty SHA-256
`e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855`.
Mutable resumed reports are not frozen under these initial-output hashes.
The immutable completed continuation output is paired-resume-stdout.json,
335,892 bytes, SHA-256
`9cf2f45fcbb68fa290ccab1a2df29187fc032eb21115329567f3d90e16ac8a0f`;
paired-resume-process.json,291 bytes, SHA-256
`3468cb4dd654a866012bdc84d253f7bc499cc0dd5548b4770023472d352562ff`;
paired-resume-stderr.log is0 bytes, with the empty SHA-256 above.
The852-byte cohort-manifest.json SHA-256 is
`6ad6504223809ac703ba7d09e170363109abe873f7b35f559cfc0ef90ad5ccee`.

## Corrected-source native confirmation and rollout

The coordinator-generated progress record for
`d07-clock-native-088a3cdf-d49a-4159-9469-0f31e233f533` is **finished** at
2026-10-24T07:34:28.3591106Z. Its eight process records all exited 0 at
**febc326426096f66deb7262f2651e542a3781db6**. These are actual native CPU-worker
CLI/Host/Store executions, not a desktop WebView journey. The source fingerprint
is `b86e648a247f49d0a3e262d7a49f383a64de4532e75b1bc2a9a79a7a6474a780`;
the 15,968,768-byte evaluator executable is bound by SHA-256
`80bdc4e2db496238da7dddf45dc5850d0ff1fbcc07e2a55c3758efce06596403`.
Model/profile/runtime/template/worker bindings match the earlier explicit table;
the new source does not adopt old-source runtime outcomes.

| Corrected-source phase | Actual result |
| --- | --- |
| Explicit native-owner refusal / genuine old cohort | One actual pass each; owner test 46 filtered, historical test 4.04s. The current full suite's ignored declarations are not counted as executed there. |
| Fresh scripted reference | 24 attempts,21accepted,3guard-only,42scripted roles; no model generation in this prerequisite. |
| Bounded native paired confirmation | 1of4scenes,12rows/12structural passes,24roles,zero repairs/privacy failures; completed=false, source_matches=true. Process258,563ms; max forwarded estimate3259. This is not a full corrected-source paired run. |
| Native continuous rollout | Four scenes,48rows/48structural passes,84roles; completed=true, source_matches=true. Zero repairs/privacy failures; six exact zero-role guard refusals09Inventory/10Ability/24ClarificationRequired across both arms. No unexpected errors or unavailable items. Process964,188ms; max forwarded estimate4094. |
| Completed rollout resume | Exit0 in16,548ms with deliberately nonexistent asset paths. Report is byte-identical to retained rollout output; full inventory unchanged. The displayed84roles are historical totals, **zero new role calls**, not84more generations. |
| New-source inspection of old39c paired run | Exit0, source_matches=false, old48rows/results retained and full inventory unchanged. It does not relabel the old clock source or execute it. |

Paired, rollout, completed-resume and old-inspect stderr are empty. Current
paired and rollout each use one physical setup (8,691ms and 9,781ms respectively),
not one separate cold load per arm. Model quality remains **false**, human
review count0. The bounded structural tests do not resolve generic narration,
human faithfulness/readability/enjoyment or NPC distinctiveness.

At courier-22, recent optional_detail_selected=false and relevant=true, but
director_private_target_present=true in **both** actual forwarded envelopes
(selected diagnostic bytes21,647 versus19,874). The target is therefore
nondiscriminating. No mechanical or comparator-defined semantic divergence
was recorded; equal finite-schema commands and different optional selection
do not demonstrate causal recall, narrator-memory benefit or superiority.

Reported corrected rollout durations use the same lower-median/nearest-rank
p95 definitions as above; this is a different experiment from old paired
snapshots and is not a before/after speed comparison:

| Corrected rollout scope | n | Lower median ms | p95 ms | Maximum ms |
| --- | --- | --- | --- | --- |
| All rows, including six guards | 48 | 21,311 | 30,803 | 31,577 |
| Generated turns only | 42 | 22,016 | 30,803 | 31,577 |
| First final response, including guards | 48 | 21,127 | 30,483 | 31,392 |
| Commit | 42 | 163 | 401 | 423 |
| Director parent role | 42 | 19,188 | 27,044 | 28,012 |
| Narrator parent role | 42 | 1,843 | 2,660 | 4,505 |

Across84current rollout roles, maximum worker input/output tokens are3,673/98;
sampled peak working set1,231,699,968bytes/private950,788,096bytes and lifetime
peak working set1,233,858,560bytes, with zero failed samples/incomplete role rows.
These are worker-only counters on this development host, not whole-app/phone
memory or universal tokenizer/deadline guarantees. No fresh hardware census
or controlled cross-run performance comparison is inferred.

Actual corrected-source CLI arguments, with only local paths replaced:

```powershell
cargo build --manifest-path crates/locallore-eval/Cargo.toml --features local-model --locked --offline --jobs 1 --target-dir <shared-target> --bin locallore-eval
<eval-executable> comparison reference <new-reference>
<eval-executable> comparison run <new-paired-run> --kind paired --lane native --max-scenes 1 --reference <new-reference> --resource-dir <approved-resources> --model <approved-model>
<eval-executable> comparison run <new-rollout-run> --kind rollout --lane native --max-scenes 4 --resource-dir <approved-resources> --model <approved-model>
<eval-executable> comparison resume <same-completed-rollout> --kind rollout --lane native --max-scenes 4 --resource-dir <nonexistent-test-resources> --model <nonexistent-test-model>
```

Primary output hashes: paired-stdout.log(92,242bytes)
`b12550e3212fd3744f55ba53c2fbabc80821be4432f8f31a909df6f6f111cbc7`;
rollout-stdout.log and completed-resume-stdout.log each335,702bytes, both
`c9ecdbce4adc25a0132db9bb162ba769a8078282f7234c4009896219b4ac1053`.
Both61,037-byte completed-resume inventory records hash to
`0e344c120b56c866d35c59876494ea5e35dc987a289fe36a19f23cbf7f8b15d3`;
both100,962-byte original-paired inventory records hash to
`27ae10b3ec979208f7acf5cb2d18cda095ba63cfb84fd54bb8ab445653be05b7`.

A read-only aggregate covers32original top-level records totaling1,552,985bytes:
the eight phase triplets (build,owner-refusal,genuine-historical,reference,
paired,rollout,completed-resume,original-paired-inspect), plus cohort-manifest,
executable,progress, completed-resume-before/after/evidence and
original-paired-before/after JSON. Ordinal filenames, UTF-8 LF-terminated
`filename|sha256|bytes` rows give
`2a23786ecd8c38308852f2ddb2030768006f33b28c613b91111c6e07c221e1fc`.
This names the exact selected records; later analysis files and nested raw/
Store files are not silently included in its count.

## Retained log integrity

Files are local/gitignored under `<evidence-root>/author-integration-artifacts`.
No raw model weights, private paths or player stories are published. The
following forty-one completed logs were hashed read-only; active logs are excluded.

| Log | Bytes / SHA-256 |
| --- | --- |
| d07-comparison-compile-first.log | 959 / `9be376854fffd5fe70772093dbe29d500d156ce42f1c9d795db6b5af67cd59e8` |
| d07-comparison-focused-first.log | 1,045 / `2087e74d43a3fe7c5bff255b6f4374c0bd73db44897077fd08e5c40a997c65e9` |
| d07-comparison-focused-corrected.log | 2,972 / `6cd717ec796c40a711ec426585e0d78b141cde8a3b5f8406eb85178ee1a1447e` |
| d07-forwarded-budget-original-red.log | 2,232 / `372da8cc88d32a6ce11aecc92fcb88ec4166de4e77a818afa792c3dee3029a98` |
| d07-forwarded-budget-first-green.log | 1,194 / `e0b8422329159e4a78362abd2d4a80c6f9dfaea01d0bf935e4cdcf18d896150b` |
| d07-eval-lib-forwarded-budget-first.log | 5,470 / `558d3430211a0c8ac22048718c8408776ffebdd130208260614647de788d4f3a` |
| d07-runner-forwarded-budget-first.log | 2,388 / `cc58dd7e23fc55e8ef08f9198a519bb01a6848518cd04320e5cd651e215bd6e1` |
| d07-genuine-historical-readonly-first.log | 589 / `c9959710e33988ad6511b4cbc77bf9f89066088392adec2ffe209db6b8f1c40f` |
| d07-host-policy-original-compile.log | 1,619 / `a24e8a84dca7361740d1b3c7390f581d725325f1fb0750df112d9c749f0915c5` |
| d07-host-policy-serialized-fixture-first.log | 2,271 / `efba0fd6c7ca6cc42d79df34e9c039e0e8dfccbd93fc5c054fb10dc42f70cdb5` |
| d07-host-policy-committed-fixture-corrected.log | 838 / `26dbc746558dfa693a120404b180d6cbc9f5e41333c19781bf49aeea972113b2` |
| d07-shared-full-first.log | 1,192 / `51fa6c03b42ec6f2808e9785fea146c9ed7f6eb3027c8401fa03dee0259204c2` |
| d07-shared-full-fixture-corrected.log | 98,434 / `517af02e4a1391c7ce5b2a01cb97799acf7db674d636b4516f6ad4f6df4f6fec` |
| d07-workspace-format-first.log | 0 / `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855` |
| d07-eval-format-first.log | 0 / `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855` |
| d07-compat-shared-clippy.log | 638 / `b24d562ab79679764c7e9fcbe9a2f7e2505f17a8d7fbe6f7ef8648b61a0a5612` |
| d07-compat-eval-remaining.log | 2,459 / `f7db38845c62cb9b302a6d835830edbde55f3c479346e1d68908fc9438333c63` |
| d07-compat-eval-clippy.log | 1,839 / `6c16430dadb337e0a053d1de481467d73fa85798a60b24184c6b22322cd1dade` |
| d07-dependency-oracle-lint-corrected.log | 580 / `97d1300eb3e056f2018a5e919fe62ef42a6c53dd454c4c929f42bfe9b62effe2` |
| d07-historical-dependency-guard-corrected.log | 589 / `f4a387abd37349e93285d681b0aef376e30e731d92b5386882cce391086c6ab9` |
| d07-compat-lint-corrected-eval-clippy.log | 202 / `1123d7930560bbc44060fd9816ada710200ab6e5e3df052a4c0e34cb2901b59a` |
| d07-compat-lint-corrected-frontend.log | 11,351 / `cd08fe8e8ed2aa22cf7dcc0560bac20c9a26ad36730334b3d7e8644e3e0dcf21` |
| d07-compat-lint-corrected-frontend-format.log | 68 / `f20510a9da4717c51c4cffee6d0dd88d6c9a723d0a83711d01216f5b48961283` |
| d07-compat-lint-corrected-native-normal.log | 10,399 / `88b4858421016e8ef73d9141a3d0f779c66465905bbb19cd72a7d05eededcccf` |
| d07-compat-lint-corrected-native-dev.log | 10,502 / `dee54391b7e3566c249ea39984640e1a6ad9dc82c3bcaca110cf1242d3ed184a` |
| d07-compat-lint-corrected-native-clippy.log | 942 / `b9b90e62b0ec93351aadeac18952f4c16028f392c604792b600b70e17589aa2e` |
| d07-compat-lint-corrected-native-build.log | 213 / `9379b6fba7552a75ab1eaa63d9d51d56ca8df52a192184865e80ad78a0a2ad49` |
| d07-compat-lint-corrected-android.log | 6,099 / `6d64d75b81ddab62e6126fdf7db35ce9dab215502f051f401037d5b5cd286385` |
| d07-apk-static-audit.log | 783 / `a2220741ab7d3170dc6f144e8b0c0d97b3b85457ef46d7bf0d6e0c76a8cef49f` |
| d07-real-owner-admission-refusal.log | 595 / `594fca8a53b44db9f0d13fe3272d0ef9760ed3b619b60c731b377e3b454b3453` |
| d07-clock-frozen-first-compile.log | 7,717 / `816e0cd470b02d3bbc751d274ad3e21cb78bfd27af2639d6c4293ba44d41ef63` |
| d07-clock-corrected-first.log | 599 / `e27952ba7d245d33262a08077177a9326b7906b38d5287526499b8a2884df0d4` |
| d07-clock-before-commit-corrected.log | 1,425 / `63a72b97c7bbc2899f373d25fef0c53af282af6a10c29591e9331b0f675e1cd7` |
| d07-clock-full-evaluator-first.log | 10,586 / `bfee986a6f9ee1c1c905bdc15e92e69671e08543dd40c1f4d135a0338e29d4d1` |
| d07-clock-compat-eval-clippy.log | 203 / `a212760cceced70ecf6cea1291b00b3ecbd6876b6d6a0137c39e4a6599546ce9` |
| d07-clock-compat-frontend.log | 11,351 / `cd08fe8e8ed2aa22cf7dcc0560bac20c9a26ad36730334b3d7e8644e3e0dcf21` |
| d07-clock-compat-frontend-format.log | 68 / `f20510a9da4717c51c4cffee6d0dd88d6c9a723d0a83711d01216f5b48961283` |
| d07-clock-compat-native-normal.log | 9,811 / `6e364dd370268138b05b0d1b7919fae2238ac675d17d1c4e804151694905656d` |
| d07-clock-compat-native-dev.log | 10,502 / `c36afce65375e4bc3a640fac694de951305287d5a86cbf38ecb0573fd0cf9017` |
| d07-clock-compat-native-clippy.log | 354 / `a01a92c4d98f1264bbfce6e3895f01c5ae7f7506f034a99d17f29c1020eac5db` |
| d07-clock-compat-native-build.log | 213 / `803ae10396e75b105e26289db85a135b6fd944c6928e002d160d50ce72674998` |

All41 completed log rows were independently verified read-only:221,291bytes,
no hash or length mismatch. Their aggregate, ordinal UTF-8 LF-terminated
`relative-log-name|sha256|bytes` rows, has SHA-256
`d897eedb2aa2f352ac00a1ddbabcbc427fe1eabeb6b5f80edf4db39db8829182`.
This is distinct from the selected32 corrected-native phase-record aggregate.

No task checkbox, model-quality acceptance, historical report rewrite,
PR acceptance, merge, release, repository setting or protected resource is
changed by this document. Next: coordinator review/adoption of this bounded
packet, followed by chronological human-rubric review and the current-comparison
application/UI gates. Structural success does not close those D07 requirements.
