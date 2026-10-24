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
| Current Core/Host fixture and full compatibility checks | Pending coordinator commands, source bindings and terminal results. The focused six-test success is not a substitute. |
| Genuine historical complete-cohort opening | Passed actual opt-in test at4a36b72; see precise inventory/old-field boundary below. |
| Real local-model current comparison | Pending separate authorized source-bound execution; no model, worker, speed, memory-quality or enjoyment result inferred from scripted tests. |
| Exact reproduction and environment | Root will supply final invocations and versions before this report is finalized; the contract's suggested commands are not presented as executed commands. |

## Genuine historical read-only compatibility

The test source was separately frozen at832e8be, imported asd5d6913 and
formatted only at4a36b72. Its opt-in path selects the retained original33356
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

## Retained log integrity

Files are local/gitignored under `<evidence-root>/author-integration-artifacts`.
No raw model weights, private paths or player stories are published. The
following eight completed logs were hashed read-only; active logs are excluded.

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

No task checkbox, model-quality conclusion, historical report rewrite,
PR acceptance, merge, release, repository setting or protected resource is
changed by this document. Next: obtain terminal Core/Host and broad
compatibility evidence; then record any separately authorized
native-model cohort with its unchanged scenarios, exact source and failures.
