# Current-pipeline comparison qualification

2026-10-23 local date; retained executions end on 2026-10-24 UTC.
Refs #29 D07.01–.06 partial / #11 M07.01. **Qualification in progress.**
This report does not accept the whole D07 milestone, a model-quality result,
native tokenizer fit or a physical-device gate.

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
| 8b4422b, d07-compat-eval-clippy.log | Strict evaluator lint exits101 on collapsible_if in the dependency oracle. Root39c770d collapses only equivalent phase-and-disjunction guards, with no lint waiver, changed oracle or acceptance relaxation. |
| 39c770d, d07-dependency-oracle-lint-corrected.log / d07-historical-dependency-guard-corrected.log | Focused actual dependency regression **1 pass /11filtered**,1.99s; genuine historical inspect/resume test **1 pass**,3.46s. Old skips, source mismatch and every retained byte stay unchanged. Corrected compatibility batch remains active. |

The original frozen Core declarations precede production (edf4d265 / contract
03308ea1). The Core fix and evaluator closure were separately allocated and
reviewed; the contracts retain their exact commit inventory. Source baa3283
merged accepted typed-inference PR #137. Candidate b8913a7 then merged accepted
desktop-author PR #135. That integration does not rerun or relabel either
PR's evidence and does not make the D07 comparison an author/Domain2 corpus.

## Pending evidence

| Required evidence | Current disposition |
| --- | --- |
| comparison_runner + memory_comparison_v2 terminal batch | Complete:9runner+3protocol passes above. Initial seven-pass partial output was not counted as a completed result. |
| Current Core/Host fixture and full compatibility checks | Host4, four-package host-feature suite743/10 ignored, strict shared Clippy and remaining evaluator15/1 ignored passed. Corrected evaluator lint/frontend/native/Android stages remain active under the new d07-compat-lint-corrected prefix; no partial stage is counted as passed. |
| Genuine historical complete-cohort opening | Passed actual opt-in test at 4a36b72; see precise inventory/old-field boundary below. |
| Real local-model current comparison | Pending separate authorized source-bound execution; no model, worker, speed, memory-quality or enjoyment result inferred from scripted tests. |
| Exact reproduction and environment | Completed commands below; fresh toolchain versions recorded. Remaining compatibility invocations/terminal results await Root. The contract's suggested commands are not presented as executions. |

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
execution is inferred. Full remaining environment/compatibility attribution
will be recorded with its terminal stage manifest.

Completed compatibility invocations, from repository root, use the existing
owned `<shared-target>` (the placeholder replaces only the local target path):

```powershell
cargo clippy --workspace --all-targets --all-features --offline --locked --exclude locallore-desktop-spike --target-dir <shared-target> -- -D warnings
cargo test --manifest-path crates/locallore-eval/Cargo.toml --features local-model --offline --locked --target-dir <shared-target> --test memory_comparison --test local_model_review --test curated_integration_review -- --test-threads=1
# First invocation failed; corrected-source rerun is pending:
cargo clippy --manifest-path crates/locallore-eval/Cargo.toml --all-targets --all-features --offline --locked --target-dir <shared-target> -- -D warnings
```

Root's local serial launcher uses one Cargo job, dev/test debug info0,
incremental0, owned temporary/Gradle/output directories, existing SDK/JDK,
empty LIBSQLITE3_FLAGS and no SDK download. Source and exit for each stage
are recorded before advancing. The original failed stage manifest is retained;
the new prefix does not overwrite it.

## Retained log integrity

Files are local/gitignored under `<evidence-root>/author-integration-artifacts`.
No raw model weights, private paths or player stories are published. The
following twenty completed logs were hashed read-only; active logs are excluded.

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

No task checkbox, model-quality conclusion, historical report rewrite,
PR acceptance, merge, release, repository setting or protected resource is
changed by this document. Next: obtain terminal remaining compatibility
evidence; then record any separately authorized
native-model cohort with its unchanged scenarios, exact source and failures.
