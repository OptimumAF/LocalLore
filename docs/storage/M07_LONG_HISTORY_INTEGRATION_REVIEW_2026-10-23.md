# M07.06 frozen long-history baseline integration review

Date: 2026-10-23. Reviewer: `app_storage_review`, coordinator-delegated. Refs #11 M07.06 and #29 D07.01/.04, partial. Claims: #11 comment 6372657640 / #29 comment 6372657900. Isolated `review/m07-long-history` / `source-long-history-review`, frozen source `a22dfff463c0b8febc93ec0b99fc35e804025c9c`, accepted production base `a13b80b8f7e37c1fb2aad714f5ba931f7bf37941`.

No concrete correctness/privacy blocker was found in this bounded baseline review. This is evidence for these fixed model-free cases, not milestone acceptance, performance qualification or proof about future production memory consumption. The reviewer did not author this new corpus/test/report; earlier contributions to shared query, branch and cache code limit independence as an assessment of the whole memory implementation.

## Source and oracle review

Read all 797 lines of `crates/locallore-storage/tests/long_history_stress.rs` and the baseline report, then inspected the actual compiler budget/observer/snapshot/cancellation paths, Store strict-history memory wrappers, and verified partition/FTS implementation they call. The entire base-to-frozen diff is two new files: the test and its report. No production, existing test, dependency, corpus, budget or expected outcome changed. Test SHA-256 is `8e8ba98f0f4f4b11fbcf271efecaab5963ee648a9e9c87de5029c1fdb30bc8af`, matching the author's frozen generator.

The opening has eight explicit accepted commands, followed by 128 batches of eight accepted statements: 1,032 events in 129 receipts, not 1,032 turns. `apply` obtains actual Engine preview and Store begin/commit receipts, requires their equality, and requires a separate ordinary Engine commit to agree. It does not write SQL history or deserialize fabricated accepted events. Child resume/continuation and later reopen use the existing Store loader and original-scope replay.

The selected child adds two events to reach 1,034 events / 130 inherited-plus-local receipts. Parent future, sibling and a separate story also end at revision 1,034 with observer `courier`; every negative scope gets an actual published short-tail packet before the child FTS search. Thus revision/observer differences cannot accidentally satisfy wrong-story/branch exclusion. The query API validates and reads the selected story/branch/observer/head partition before packet text, re-extraction and TEMP FTS, using a coherent strict Engine snapshot. These are genuine different canonical sources with identical sequence numbers, not relabeled child events.

The nested prebirth descendant selects completed root revision 8 through the child's ancestry; the oracle requires root event 1 to retain its original Scope and excludes later content. Historical revision 8 is actually rebuilt by the compiler's accepted snapshot path. Revision 1,031 is inside an eight-event turn and must return `Boundary`. The stale head, wrong request Scope, ambiguous alias and tiny mandatory-budget cases compare concrete public errors. Cancellation is the actual `compile_cancelled` entry with an already-true callback; it proves pre-cancellation refusal, not cancellation during synchronous history rebuild or a bounded response deadline.

The 26 fixed checks form one integration test. They cover:

- Exact original-scope old event, literal old history, lexical compiler selection, ambiguous alias refusal and explicit ID disambiguation.
- Truth versus belief, old open promise/source 2, current inventory/directed relationship/source 3, courier/player secret and cross-scope serialization fences, whole-package accounting.
- Targeted forbidden compiler queries, wrong Scope, legitimate player-director secret versus another actor's secret, director observer restriction, historical and prebirth cuts, mid-turn/stale/budget/cancel refusal, no privilege transfer from omniscient inspection.
- Honest unchunked v1 `TooLarge`, verified structured promise FTS, player-versus-courier partition, same-head wrong-story/sibling/parent-future exclusion, and unchanged selected canonical projection.

Compiler prerequisite failure records all dependent checks as false; it is not counted as skipped success. Errors from fixture construction/replay/public cache operations also fail the Rust test. Metrics are written before the final case-failure assertion, so completed negative outcomes remain visible. There is no timing threshold, expected-result retuning or conditional acceptance of a failure.

## Independent execution

Coordinator explicitly cleared one portable Cargo process at a time after its native cohort finished. Reviewer ran the unchanged selected test sequentially, default then all features, with a fresh task-owned D-drive target and TEMP/artifact roots. Rust `1.93.1 (01f6ddf75 2026-02-11)`, Cargo `1.93.1 (083ac5135 2025-12-15)`, bundled SQLite 3.53.2 / Store schema 3. Both dev/test debug information and incremental compilation were disabled. No model/provider/worker/app/native renderer/device/ADB/CUA/desktop action or protected resource was used.

Commands, from the isolated frozen checkout (paths below name task-local directories outside Git):

```powershell
$env:TEMP = "$taskOutput/temp"
$env:TMP = $env:TEMP
$env:CARGO_PROFILE_DEV_DEBUG = '0'
$env:CARGO_PROFILE_TEST_DEBUG = '0'
$env:CARGO_INCREMENTAL = '0'
$env:LOCALLORE_LONG_HISTORY_ARTIFACT_ROOT = "$taskOutput/default"
cargo test -p locallore-storage --test long_history_stress --locked --offline --jobs 1 --target-dir "$taskTarget" -- --nocapture
$env:LOCALLORE_LONG_HISTORY_ARTIFACT_ROOT = "$taskOutput/all-features"
cargo test -p locallore-storage --test long_history_stress --all-features --locked --offline --jobs 1 --target-dir "$taskTarget" -- --nocapture
```

`taskOutput` was the sibling `long-history-review-artifacts` directory; `taskTarget` was sibling `m07-long-history-review`. They are separate from the author's output and from shared/other owners' build targets. Full Cargo output and generated databases/metrics remain task-local; only this review document is tracked.

| Independent selected run | Result |
| --- | --- |
| Default | 1 Rust test PASS; 26 fixed checks PASS, zero failed/ignored; 53.74 s test time; fresh compile 40.01 s |
| All features | 1 Rust test PASS; same 26 fixed checks PASS, zero failed/ignored; 49.18 s test time; feature compile 22.55 s |

Read the actual default metrics and independently queried its generated database with Python `sqlite3.connect(...?mode=ro, uri=True)`. Actual physical rows are root 1,034 events / 130 committed turns, child 2 / 1, sibling 2 / 1, foreign 1,034 / 130: total **2,072 original-scoped accepted events / 262 committed turns**. Prebirth has no local rows; inherited prefixes are not duplicated. This corroborates the test's independent set-based event and receipt deduplication, rather than treating inherited selected history as additional stored events.

Both feature modes reproduce the report's stable projection SHA-256 `0b4b9b3dc67a9cb457f0510c01771e80847c0869ce120e59cb3f836a298dbce5`. This hashes `Engine::canonical_bytes()` (the canonical projection), not the whole database or an authenticated history. Both actual courier packages are 14,280 bytes, 3,570 estimated tokens plus 512 reserved, 24 selected records, 2,073 eligible candidates and 2,050 omissions. Candidate and selected/omitted bookkeeping are not interchangeable accuracy denominators. Whole serialized bytes/4 is an estimate, not measured tokenizer/native template/output fit. The feature metrics identify `development_fixtures_feature:true`; default identifies false. The test and fixed oracles remain identical.

Actual default old observation count and literal history match count are each 1; structured promise FTS has one packet with source event 2; private tail has player 1 / courier 0 hits; wrong-story/sibling/parent-future searches have 0/0/0 hits. Single default observations: primary generation 22,734.913 ms; all fixture construction 46,786.318 ms; reopen/two replays 529.503 ms; actor observation scan 0.850 ms; literal history 42.845 ms; compiler 144.533 ms; FTS 235.218 ms. These operations perform different work, with fixture construction including repeated preview, strict Store commit/replay and comparison commits. No speed ratio, memory bound, deadline or performance improvement is inferred.

Feature metrics again contain 2,072 events / 262 receipts and the same selected/forbidden hit results; single primary generation 20,021.110 ms, all fixture construction 43,289.375 ms and reopen/two replays 457.779 ms. Different single runs under different host conditions are not a comparison benchmark. No failed reviewer execution occurred; the author's historical resource failure remains separately preserved below.

## Evidence integrity, failures and limits

Independently hashed and read the author's retained logs: default recovery log `67fc4dc207eeee121b03456107426e0eccdb32e2fa9d6c6d2c1c13280fb1a353`, feature recovery log `3d2b2d3028ab3a48549e5610e6a01d2c46d4d22c562bd426b6b606e4542ef987`, and allocation-aborted log `73c2df6404569aa5845344d84ea3dfae4bedfe062dd14cf6b4c25c1f1d3e10c3` all match the report. The last contains actual `memory allocation of 24960 bytes failed` and Windows exit `0xc0000409` before metrics. It remains a failed execution, not a semantic pass; no cause is attributed to another process. The report separately attributes its PowerShell/concurrent coordinator failure and does not claim those as this reviewer's execution.

Reviewer evidence:

| Task-local artifact | SHA-256 |
| --- | --- |
| `default.log` | `123fd29b29e3e336b6db9cfde23c772e2b2328d3667313cd7062a62ad86eb7c6` |
| Default `metrics.json` | `ca4e412db169a1e0bba9e5a0b054ced26b6137097e81f47e9cb2cc99cb1273f0` |
| `all-features.log` | `d93c598e121e8871ebab13cc8f1f635f514cdce2d77bf9a9688b6df7dbb6ac1d` |
| Feature `metrics.json` | `d8b6355d2ac4e6ff928d7efa82c007a91c926a73f97ae4a931cd94b60a3bb319` |

The fixed synthetic generator emits bounded metrics: fixed case names/canaries/counts, source hash, schema/SQLite version, fixed errors and timing. It does not accept a user story or emit host paths/full prompts. DB/history are local files, outside Git, with no automatic upload. Keeping a configured artifact root intentionally retains them; no encryption, physical-erasure or OS-backup guarantee follows. The default cleanup removes only literal files under the newly created task directory, not recursive unrelated paths. An early panic can leave local diagnostic artifacts; that does not imply they were accepted or uploaded.

No new regression file was needed because no demonstrated new failure required a reproduction. Original test/oracles/budgets were unchanged. Reviewer did not rerun the author's strict Clippy/fmt or full workspace/native/Android checks: those remain attributed to their original evidence. This review runs the selected portable test only. Document ownership/diff/whitespace checks are separate.

Remaining limits are substantive: v1 full-history scene is safely refused at 256 eligible events; FTS searches a small verified packet partition, not a global long-history index; cancellation is pre-cancel only; immutable-canon comparison is selected projection equality, not a universal write audit. Accepted v2 coverage, durable jobs, production verified-memory compiler forwarding, transcript-only/model comparison, narrative use, real tokenizer fit, peak memory, calibrated latency and Android/device/human-quality gates are **not** measured. Source base and generator hashes make this a reproducible finite baseline, not evidence that proposed schema4/prompt2.4 consumers exist or have passed.

Next runnable work is coordinator integration of this unchanged baseline, then separately frozen same-case raw-versus-verified coverage/consumer tests when that shared implementation lands. No source change or gate relaxation is requested by this review.
