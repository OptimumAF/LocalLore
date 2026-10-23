# Model-free long-history retrieval baseline — 2026-10-23

Refs #11 **M07.06**, supporting #29 **D07.01/.04**, partial, in review.
Claims #11 comment6371883375 and #29 comment6371883996. Independent delegated
author `/root/resource_metrics_review`, isolated `test/m07-long-history-baseline`
/ `source-long-history`, based on accepted
`a13b80b8f7e37c1fb2aad714f5ba931f7bf37941` (schema3, prompt2.3).
Own only new `crates/locallore-storage/tests/long_history_stress.rs` and this
report. No production Core, Store, Host, compiler, schema, budgets, existing tests,
corpus, runtime, dependency or Android file changed. Coordinator owns future
schema4 jobs and prompt2.4 consumer. No PR/merge or milestone checkbox here.

Frozen final generator/test: `5cfaa4ae4870ce6deff67e454721b8f2d6ade2be`, SHA-256
`8e8ba98f0f4f4b11fbcf271efecaab5963ee648a9e9c87de5029c1fdb30bc8af`.
Earlier source `acc03d7` and `d4bf45f` measurements remain historical; they were
not rewritten. The last change strengthens negative fixtures to share revision
and observer, leaving the primary child history/canonical fingerprint unchanged.
There are zero providers/model calls; these are accepted typed engine events,
not generated prose or a model's ability to use retrieved information.

## Fixed original corpus and acceptance

The new test constructs its own original orchard seed, actors, facts, relationship
and contradictory belief. It does not import/relabel recorded fixtures. Each turn
uses `Engine::request`/typed commands, `Engine::proposal`, actual preview,
`Store::begin_turn` and `Store::commit_turn`; a second ordinary Engine commit
must equal the Store's actual receipt. Accepted event fields are not authored
through SQL, deserialized receipts or projection repair. State is reopened and
strictly replayed before retrieval checks. No SQL fixture writes or alternate
memory/index implementation are introduced.

The primary opening receipt contains eight accepted events: an old spindle
statement (event1), an open promise (2), a healing-item gift (3), a statement
claim (4), a distinct belief (5), player-only spoken information (6), one time
advance (7), and a shared-name encounter (8). Then **128 eight-command batches**
create 1,024 irrelevant spoken ledger observations. Root at fork has **1,032
events /129 receipts**. This is 1,000+ events, not 1,000 turns or a genuinely
generated long session. Story time remains bounded; the deadline7000 commitment
stays open. Most distractors are intentionally simple accepted statements.

Child and sibling fork at completed root revision1032. Child adds public event1033
and player-only event1034. Parent and sibling each add two accepted conflicting
observations at the **same event numbers**. A separate original foreign story
accepts 1,032 distractor events and two conflicting observations. Thus all four
active negative/selected scopes have **head1034 and observer `courier`**. The FTS
scope test cannot pass merely because revision/observer differ. These extra
negative fixtures are **1,038 events outside the primary child's 1,034-event
selected history**; total **2,072 unique accepted events /262 unique receipts**.
Counts are independently deduplicated by original `(Scope,sequence)` and
`(receipt Scope,turn)`, not by relabeling inherited history.

A descendant forks through the child's lineage at completed revision8, before
its parent's birth. Accepted lineage semantics deliberately permit this ancestor
cut; root evidence stays root-scoped and later child/parent/sibling content is
absent. Revision1031 is an incomplete eight-event-turn boundary and must refuse.
Wrong-story request scope, stale expected head and cancellation also refuse.

## What is measured

The same **26 fixed checks** run in each Rust feature mode. They cover exact
actor-event lookup of old event1 with its original root Scope, literal eligible
history search, compiler lexical selection, exact actor-ID disambiguation of two
actors sharing a display name, and refusal of the ambiguous alias.

Compiler assertions inspect typed records/sources, not a flattering transcript:
canonical bronze-ledger truth remains distinct from subjective silver-ledger
belief; the old open promise retains supporting event2; current item owner and
directed obligation1 retain gift source3 while trust remains-4. Actor secrets and
hidden identifying IDs/event6 are absent from courier serialization/diagnostics.
The player director legitimately receives player secrets but not the courier's
private seed fact; a director cannot assume the courier observer. Targeted
forbidden-marker queries and omniscient inspection do not grant character
knowledge. Parent-future, sibling and foreign evidence remain excluded.

Default compiler budget is unchanged: max24,576 UTF-8 bytes, estimated4,096 tokens,
reserved512, recent4, optional16. The measured courier package is **14,280 bytes**,
**3,570 estimated tokens +512 reserved**, 24 selected records from 2,073 eligible
candidates, 2,050 eligible omissions. The director package is 13,415 bytes and
21 records. Accounting checks the complete serialized package including
diagnostics. This is explicitly **UTF-8 bytes/4 estimation**, not a measured
tokenizer, native prompt/template/output fit, advertised model context length or
current 350-role-token profile qualification. Tiny1,024-byte/64-estimated-token
input must return `MandatoryBudget`; mandatory context is not silently dropped.

Existing verified **v1 Store cache** is exercised separately from compiler input.
An unchunked full-history scene correctly refuses its existing256-event cap.
An explicitly requested structured commitment packet re-extracts old promise2;
short current-tail packets are published for each actual scope and observer.
SQLite FTS then returns exactly one old-promise packet for `amber compass`,
with source event2. Player-private tail query returns one player hit and zero
courier hits. Wrong-story/sibling/parent-future queries return zero in the child,
despite same-head/same-observer foreign cached packets. Source/canonical state
before and after compiler, inspection, cache publication and search is identical.

FTS here searches a small, already verified scoped packet partition after strict
Engine replay; it is not a global 2,072-event index benchmark. Exact visitor
lookup is a public actor-observation scan, not proof of constant-time indexing.
Literal inspection search and compiler selection have their own different work
and output contracts. No comparison among those timings implies one is a faster
replacement. Accepted pure v2 coverage APIs are not exercised here. No durable
maintenance, verified-memory compiler forwarding, embeddings or production cache
consumer is implemented or qualified by this test. There is no transcript-only
versus verified-memory model comparison.

## Execution, resource failure and results

Windows x64 10.0.26300.0, Intel Core i7-12700K (12 cores/20 logical), visible RAM
63.7 GiB; Rust/Cargo1.93.1, bundled SQLite **3.53.2**, Store schema **3**.
Test/dev debug information0, incremental0. No model, worker, UI, package, device,
CUA, protected resource, download, OS setting or unrelated process action occurred.
Work was sequential in this agent; coordinator owns independent integration.

The first larger same-revision run compiled, then aborted before metrics:
`memory allocation of 24960 bytes failed`, executable exit0xc0000409 (Windows
reports STATUS_STACK_BUFFER_OVERRUN on this fail-fast). A separate read-only
PowerShell status launch failed with System.OutOfMemoryException/exit-532462766.
Coordinator independently reported concurrent OS1455 metadata allocation failure.
These outputs are retained, with no claim that a particular process caused them
and no reinterpretation as passed semantic cases. No budget/corpus/assertion was
changed. After other owned compilation settled, the **identical frozen5cf source**
reran sequentially with `--jobs 1`. No unrelated process was stopped or OS setting
changed. Timings below are single observations under host resource pressure,
not calibrated performance bounds or comparative quality evidence.

| Final command/check | Actual result |
| --- | --- |
| Targeted integration test, default | **1 Rust test PASS /26 fixed case checks PASS**, zero fail/ignore, 62.12 s |
| Same test, `--all-features` | **1 Rust test PASS /same26 checks PASS**, zero fail/ignore, 70.35 s |
| Storage `--all-targets` strict Clippy, both modes | PASS with `-D warnings` |
| Workspace fmt / git diff check | PASS |
| Canonical fingerprint, both modes and earlier primary corpus | `0b4b9b3dc67a9cb457f0510c01771e80847c0869ce120e59cb3f836a298dbce5`, unchanged |

These are26 distinct checks executed twice, not52 distinct scenarios or the full
storage/workspace suite. All-targets Clippy compiled other targets; their tests
were not executed here. No unexpected semantic failure occurred in completed
runs. Observed limitations/refusals remain: full unchunked v1 scene `TooLarge`,
ambiguous alias, invalid completed boundary, wrong scope, stale head, cancellation
and insufficient mandatory budget. No partial compiler package is returned on
those compile errors. A full native generation stop is not exercised here.

| Single timing observation, milliseconds | Default | All-feature |
| --- | ---: | ---: |
| Primary1,032-event generation | 26,672.078 | 24,988.602 |
| All scopes/negative fixtures built | 54,949.235 | 61,332.111 |
| Reopen + strict child/prebirth replay | 555.639 | 701.578 |
| Exact actor-observation scan | 0.592 | 0.829 |
| Literal eligible history search | 48.045 | 56.636 |
| Current compiler old-event query | 150.953 | 169.666 |
| Verified structured-packet FTS search | 224.340 | 324.754 |

Exact and literal old-event queries each found the intended event1; compiler
lexical and explicit-ID/alias cases retained it. Structured FTS found source2;
wrong-story/sibling/parent-future packet hits were **0/0/0** with all relevant
scope heads1034 and observercourier. Private tail hits were player1/courier0.
The package budget figures above matched exactly in both modes. Reported available
memory during recovery was about8,457 MiB physical /2,912 MiB virtual; that bounded
OS observation is not peak-memory measurement, causal diagnosis or a guaranteed
minimum requirement. No wallclock pass/fail threshold exists.

Earlier actual development evidence is also retained: the initial implementation
passed22 checks; acc03d7's stronger structured oracles passed24 in default/all-feature
modes; d4bf45f's explicit director checks passed26 in both. Their smaller foreign
negative fixtures used different heads and cannot qualify the final independent
FTS-scope predicate check. The coordinator authorized the same-head strengthening
before edit. Initial `fmt --check` correctly reported the unformatted new file;
only the owned new test was formatted. No semantic RED was edited away or expected
outcome/budget retuned. The resource-aborted run remains distinct from completed
case results.

## Reproduce and retain bounded local artifacts

From a provisioned checkout, create an absolute task output and unique TEMP/TMP
outside Git. No installs or network are needed. Example PowerShell:

```powershell
$taskOutput = 'D:/task-output/m07-long-history'
$env:TEMP = 'D:/task-output/unique-temp'
$env:TMP = $env:TEMP
$env:CARGO_PROFILE_DEV_DEBUG = '0'
$env:CARGO_PROFILE_TEST_DEBUG = '0'
$env:CARGO_INCREMENTAL = '0'
$env:CARGO_BUILD_JOBS = '1'
$env:LOCALLORE_LONG_HISTORY_ARTIFACT_ROOT = "$taskOutput/private-artifacts"
cargo +1.93.1 test -p locallore-storage --test long_history_stress --jobs 1 --locked --offline --target-dir "$taskOutput/target" -- --nocapture
cargo +1.93.1 clippy -p locallore-storage --all-targets --jobs 1 --locked --offline --target-dir "$taskOutput/target" -- -D warnings
# Repeat both commands with --all-features.
cargo +1.93.1 fmt --all -- --check
git diff --check
```

With the artifact variable, each invocation retains only its newly generated
synthetic SQLite database/history and sanitized `metrics.json` in a new local
directory. Without it, task files use system temp and cleanup known files on
drop. No generated database/history enters Git or automatic upload. The default
test emits bounded sanitized JSON containing generator hash, actual schema/SQLite
version, feature mode, counts, outcomes and timing; no private host path is needed.
Local author logs/artifacts live in sibling `long-history/`, outside this checkout.

Source-bound evidence (local logs retain full sanitized JSON; databases/history
remain local/private):

| Evidence | SHA-256 |
| --- | --- |
| Default recovery test log | 67fc4dc207eeee121b03456107426e0eccdb32e2fa9d6c6d2c1c13280fb1a353 |
| All-feature recovery test log | 3d2b2d3028ab3a48549e5610e6a01d2c46d4d22c562bd426b6b606e4542ef987 |
| Retained allocation-aborted test log | 73c2df6404569aa5845344d84ea3dfae4bedfe062dd14cf6b4c25c1f1d3e10c3 |
| Default `metrics.json` | 6665752d1a990d5f43b739863e58bc4d2b4348f92923221d4e9aa6bf0fa3db8d |
| All-feature `metrics.json` | 6c2ec4a9f659cfeb5eace91a68f5d41bae51a1249eb9bb3ca14d0439042f7565 |

PowerShell launch failure remains in the actual tool output; coordinator's
concurrent compiler allocation error is attributed to their report, not rerun
or claimed as this author's execution. No failure artifact was overwritten.

Next runnable work: independent coordinator review/integration, then reuse the
same fixed primary corpus for raw-versus-verified prompt2.4 consumer parity once
that production capability exists. Generated/model-dependent long-session use,
human quality, measured tokenizer/native fit, stable memory/latency distributions,
peak memory, Android/device parity and full M07/D07 acceptance remain separate.
