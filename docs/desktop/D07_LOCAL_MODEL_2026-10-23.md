# D07 bounded local-model evaluation lane

Refs #29 D07.01/.02/.03, **partial, in_review**. The implementation claim is
[6367981969](https://github.com/OptimumAF/LocalLore/issues/29#issuecomment-6367981969),
following the frozen proposal
[6367453644](https://github.com/OptimumAF/LocalLore/issues/29#issuecomment-6367453644).
This slice extends the existing standalone `locallore-eval` runner; it adds no
alternate engine, context compiler, observer filter, persistence or inference
pipeline. Real-model evaluation failed four of six stories. Quality is unaccepted.

## Frozen source and authority

The measured clean source is **c76d7917cf0cdd4cd17db151dcd8f313709b7b96** on
`impl/d07-local-model`, based on accepted `884cf3fe7ec144b8da082bef9a726d426d4aaf4c`.
This documentation follows the measurements. The branch includes unchanged
runtime sampler commits `746fb49`, `5f61fd0`, documentation `069af08`, and the
coordinator's retained-handle expected-worker guard as `5eaa217` (upstream source
`41f8b702829ed77dee94dc2c540d8047865a0c59`). Those dependencies require coordinator
integration; this lane does not self-approve them. Later accepted main
`8e377594` private-capture hooks were not part of this cohort, even though their
default is disabled. No combined-main qualification is implied.

Owned changes are `crates/locallore-eval` lane/recording/fixtures/tests and narrow
manifest, lock, runner, report and build-source wiring, plus these documents.
No core, Host, Store, UI, Android, worker, protocol, model or profile changed.
Original nine deterministic tests and original report JSON behavior remain.
Only the optional `local-model` feature adds the existing local-runtime path
dependency; no third-party package versions or downloads were introduced.

Both lanes use the same durable Host free-text action, production Play preparation,
compiler, validation, commit, receipts and Store replay. Scripted output is fake
inference, clearly labeled. Native uses one warm approved Qwen owner and fresh
contexts per role. Native assets are supplied only through the trusted local Rust
API/CLI, with the fixed worker digest verified through the runtime's retained
opened handle before spawn. No renderer capability or Host inspection grant is
added. Recording observes the existing provider; it never decides canonical state.

`LaneFactory::ScriptedBaseline`, optional trusted `LaneFactory::Native`,
`run_curated`, `NativeAssets`, `run_native_curated` and `cli` are the integration
surface. Pre-owned native factories label cold startup `outside_run_unknown`.
The native CLI acquires the run owner and preparation reservation before asset
verification/load. Without the feature it reports `NativeFeatureUnavailable`.

## Frozen corpus and separate expectations

`crates/locallore-eval/fixtures/curated-local-v1.json` has SHA256
`007d71afd310569150012fcf09d1c4d42235625a3b47c0b4c76dcca59d640993`.
It declares six isolated synthetic stories, each with four turn-cases. This is
24 turn-cases, not 24 independent stories. Expected actions, projection values,
prompt targets, exclusions and prohibited prose are declared before execution.
Native and scripted lanes consume identical frozen input. A selected subset
reports its own denominator.

| Story | Declared journey |
| --- | --- |
| gift-agency | Gift ownership without healing/trust inflation; dialogue; spent item refusal; words do not grant a power. |
| loan-promise | Borrowed item refusal; move to lender; old promise context; return key. Thirty-two accepted typed Wait setup events are context setup, not generated quality turns. Returning the key does not automatically complete the promise. |
| ability-cost | Unknown ability refusal; exact resource cost; exhaustion refusal; learn permitted ability at zero energy. |
| knowledge-boundary | Literal extraordinary dialogue as a statement; move; actor-only discovery; return; eligible character context checks. |
| same-name | Ambiguous alias refusal; exact actor gift; borrowed item refusal; leave collision location. |
| lineage | Ancestor observation retains original scope/event provenance; later parent/sibling facts excluded; branch independence; active cancellation. |

Mechanical assertions cover eligibility/agency, bounded actual director context,
original lineage, state/receipts, exact idempotent retry with provider disabled,
Store reopen/replay, scope rejection and cancellation. Narration checks are
finite literal detectors. Faithfulness, agency, repetition, readability and
enjoyment rubric entries stay `not_reviewed`; NPC distinctiveness is unsupported
for this narrator-only lane. A safe fallback is distinct from generated prose
acceptance. Persisted derived summaries/FTS are not consumed by Play here.

## Bounds, interruption and checkpoint contract

There are at most 32 admitted turns, 96 role attempts and 30 minutes cumulative
charged active work across resumes. At most 32 invocations are accepted. Each
turn reserves 60 seconds and three roles before provider work; invocation
preparation reserves 120 seconds. Settled work replaces reservations; interrupted
unknown work remains conservatively charged. A joined external turn watchdog
requests cancellation after 60 seconds. It does not change the approved profile's
120-second deadline, and cleanup is cooperative, not a hard real-time guarantee.
The existing one-director-repair limit remains; a valid but wrong action does
not trigger a schema repair. Tokens remain at most 350 per role.

One file-lock owner controls each run. Fixed-name admission/invocation ledgers
and immutable per-story checkpoints bind source, corpus, selected subset and
profile. Unknown fields, gaps, orphan settlements, overflows, mismatched bindings,
raw-output digest/size/path changes and inconsistent checkpoints fail closed.
Each case is bounded to 64 KiB; JSON and HTML reports to 2 MiB each. At most
96 raw role outputs are retained separately, at most 16 KiB each. They remain
private, local, fixed-name artifacts. Report hashes establish consistency, not
authenticity of untrusted files.

Completed story checkpoints are reused without inference. An interrupted
uncheckpointed story uses a fresh isolated database attempt; prior work remains
charged. A failed expected turn stops its dependent remaining turns and continues
other isolated stories. No model output is replaced by scripted output to make a
native story pass. Completed-run native resume verifies checkpoints/raw artifacts
before opening model/worker assets and labels cached-only verification honestly.

The per-turn recorder preserves at most three role results, immutable full request
identity digests, bounded original output references and actual terminal metrics.
Poisoned/dropped recording cannot change the provider result. Worker counters and
process-lifetime peaks are cumulative within a native epoch; they are private
diagnostics, not independent per-role totals or a new Host/UI export capability.

## Exact local verification

Environment: Windows 11 Pro 10.0.26300 x64, Rust/Cargo 1.93.1. Builds and temporary
files use this task's D: roots, debug info disabled and incremental off. Commands
below ran from the source checkout; `$task` abbreviates the dedicated task root
and `$artifacts = "$task/local-model-artifacts"`.

```powershell
$env:TEMP = "$artifacts/temp"; $env:TMP = $env:TEMP
$env:CARGO_PROFILE_DEV_DEBUG = '0'
$env:CARGO_PROFILE_TEST_DEBUG = '0'; $env:CARGO_INCREMENTAL = '0'
cargo +1.93.1 test --manifest-path crates/locallore-eval/Cargo.toml --all-targets --locked --offline --target-dir "$task/local-model-native"
cargo +1.93.1 test --manifest-path crates/locallore-eval/Cargo.toml --features local-model --all-targets --locked --offline --target-dir "$task/local-model-native"
cargo +1.93.1 clippy --manifest-path crates/locallore-eval/Cargo.toml --all-targets --locked --offline --target-dir "$task/local-model-native" -- -D warnings
cargo +1.93.1 clippy --manifest-path crates/locallore-eval/Cargo.toml --features local-model --all-targets --locked --offline --target-dir "$task/local-model-native" -- -D warnings
cargo +1.93.1 fmt --manifest-path crates/locallore-eval/Cargo.toml -- --check
cargo +1.93.1 build --manifest-path crates/locallore-eval/Cargo.toml --features local-model --bin locallore-eval --locked --offline --target-dir "$task/local-model-native"
git diff --check
```

Default tests: **19 passed**, feature tests: **20 passed**, zero failed/ignored.
Both strict Clippy variants, formatting and diff checks passed. The ten additional
default tests cover full baseline, subset/pause/resume/immutable checkpoint,
wrong valid action, malformed/schema repair, fallback, secret canary, a known
semantic false-negative, actual pending-provider cancellation, cumulative unknown
charges/caps, tampered source/raw/path/checkpoint, exclusive owner, output bounds,
escaping, repeated polling, role cap and recorder poison noninterference. The
feature-only test cancels preparation before missing asset access. These are
synthetic process/provider and shared pipeline tests; no native GUI is involved.

The executable SHA256 is
`8592824fd63332c7eb0a5510cbccb61cb183e9513ec9349e2b551a74a8a88d40`.
Its clean source binding and corpus digest are retained in `source-binding.json`.
Verification logs are `freeze-default-tests.log`, `freeze-feature-tests.log`,
`freeze-default-clippy.log`, `freeze-feature-clippy.log` and `freeze-build.log`.
Earlier failed development logs are retained locally; they are not final passes.

## Scripted baseline and actual native result

```powershell
$exe = "$task/local-model-native/debug/locallore-eval.exe"
& $exe curated run "$artifacts/scripted-cohort" --lane scripted
& $exe curated run "$artifacts/native-cohort" --lane native --resource-dir $approvedWorkerDirectory --model $approvedModel
# Completed native resume intentionally used nonexistent worker/model paths:
& $exe curated resume "$artifacts/native-cohort" --lane native --resource-dir "$artifacts/missing-no-worker" --model "$artifacts/missing-no-model.gguf"
```

`$approvedWorkerDirectory` is the previously qualified b5 worker directory and
`$approvedModel` the existing read-only approved managed GGUF. No copy, import,
download, write, rename or deletion of either asset occurred. Use the coordinator's
approved asset locations rather than adding private absolute paths to Git.

| Measurement | Scripted fake baseline | Actual native Qwen |
| --- | ---: | ---: |
| Process exit | 0 | 1 (failed result retained) |
| Stories passed / declared | 6 / 6 | 2 / 6 |
| Executed turn-cases / declared | 24 / 24 | 21 / 24 |
| Generation commits | 17 | 10 |
| Inference failures | 0 | 4 |
| Preflight guard-only cases | 6 | 6 |
| Cancelled cases | 1 | 1 |
| Dependent turn-cases not run | 0 | 3 |
| Role attempts | 35 | 25 (15 director, 10 narrator) |
| Fallbacks / generation commits | 0 / 17 | 7 / 10 |
| Nonfallback native prose candidates | Not applicable | 3, unreviewed |
| Declared checks failed / executed | 0 / 372 | 20 / 297 |
| Charged active milliseconds, first invocation | 2373 | 164743 |
| Quality accepted | false | false |

The 20 failed checks are five consequences of each of four wrong-action proposals,
not 20 independent model defects. Gift-agency and lineage passed. Loan-promise
failed on the move-to-lender turn: the valid director command chose the wrong
destination, so old-promise and return-key were **not run**. Ability-cost failed
on learn-beacon; knowledge-boundary failed on discovery, leaving return unrun;
same-name failed on its final move. All four were valid command shapes rejected
by agency/intent validation, with no schema repair. Comparison of the prior and
failed-turn projection hashes confirms **4/4 rejected proposals left canonical
projection unchanged**. Required effects were not achieved; those expectation
failures must not be described as canonical success.

The knowledge story's terminal Mira/Sable context assertions are conditional on
successful preceding turns and were also **not run**. This native cohort therefore
does not verify real old-promise retrieval or the discovery/terminal-observer
journey. The scripted baseline covers their declared mechanics. The passing
lineage case verifies its actual director required ancestor source scope. Review
after the cohort found that director absence of parent/sibling/foreign canaries
was checked only through the separate compiler result, not on the actual submitted
director envelope. Narrator checks did inspect actual requests. Historical c76
therefore does **not** prove those actual-director exclusions. Guard-only cases
make no inference-quality contribution.

There is also an intentional model-free regression for a known finite policy
false-negative: unsupported ability/energy prose can pass the current narrow
narration guard, while the predeclared evaluation phrase detector fails the case.
The canonical projection remains unchanged, but the displayed prose is still
unfaithful. A separate recognized unfaithful phrase exercises actual fallback.
Neither detector is a semantic oracle. No core/prompt/fixture change was made to
conceal this observation, and no human prose rubric or quality signoff exists.

The initial native report is preserved separately as
`native-cohort-initial-report.json` (184071 bytes, SHA256
`17b09b316d405a1a00d3d6df9c9bd1e497b34ddeb2157494fe5441a9e660f5fd`).
Completed resume retained the four failures, six checkpoint hashes and totals
21 admissions/25 roles; it returned exit 1 with
`native_startup=not_run_all_checkpoints_complete`,
`artifact_verification_this_invocation=not_run_cached_only` and no `native_load`.
The rewritten cached report SHA256 is
`30e4db2a2d25be02b08d09903795f8a68f41a3214dce9f4d2b60b26a8dae7a74`.
This proves the actual cached-only program path, not OS-wide process observation.
Per-story Store reopen and exact receipt retry also used a disabled provider.

## Runtime and resource interpretation

The fixed Qwen3-0.6B Q8_0 is 639446688 bytes, SHA256
`9465e63a22add5354d9bb4b99e90117043c7124007664907259bd16d043bb031`.
Worker SHA256 is
`b5dd124e484c67c9dda5aebb2cdff1878ccefd0fba99aba4788e00a166f68434`;
llama.cpp revision `620d2225cc436ab0b001e3200e590e3b286ef9ab`;
Qwen revision `23749fefcc72300e3a2ad315e1317431b06b590a`;
template `57f1fd00f0013a2be96aa79b857391f27e23df5b5f847072b524c897e24d0361`;
profile manifest `01ad542001b04a96f4a8ed6c841be1866eb025350836e0c5d0a4969fdb361d38`.
The unchanged profile uses 4096 context tokens, 350 tokens per role, four CPU
threads, no GPU, batch/ubatch 512, seed 42, temperature 0.7, top_p 0.8, top_k 20,
min_p 0, presence penalty 1.5, thinking/tools disabled. A seed is not a promise of
identical generation across hardware/backend revisions.

Twenty-four adapter/native role outcomes completed and one cancelled. All 25
resource windows reported sampled status, no query failure or cap. Maximum sampled
worker working set across these windows was **1214119936 bytes**; maximum sampled
private committed usage **929542144 bytes**; maximum observed process-lifetime
peak working set **1268768768 bytes**. Sampling at 250 ms is a lower bound on a
window's true peak; the process-lifetime peak is cumulative, not a role peak.
Worker load reported 259.7069 ms in its own clock domain. These are observations,
not controlled performance comparisons, TTFT, parent memory, exact peaks or sums
of parent/worker clock domains. Cumulative context/load counters remain private.

Postflight rehashed the model, candidate worker and previous qualified worker;
all hashes matched preflight, and model size/mtime were identical. The initial
asset-JSON comparison briefly compared an auto-parsed date object with a string;
the retained files are byte-identical after trimming, so this was a comparison
type mismatch, not an asset change. No second model cohort was run.

## Handoff and remaining gates

Local evidence root is task-owned `local-model-artifacts` with immutable cases,
ledgers, stdout/stderr, raw outputs, databases, before-resume checkpoint digests,
initial/cached reports and asset integrity JSON. Raw model output/private database
paths are not committed. The adjacent sanitized evidence JSON contains only
public fixture IDs, counts, checksums, coarse outcomes and bounds.

This is a headless real native-worker/shared Host/Store evaluation, not native
WebView/IPC rendering, Android compatibility, a device, a network-block test,
long-session stability, a model ranking or a release. No such checks were run
for this slice. No human quality acceptance, NPC voice assessment, 1000 generated
turns, transcript baseline, summary/FTS model consumption or all-main integration
acceptance is claimed. D07 remains open.

Next runnable work is coordinator review/integration, then a separately claimed
product improvement based on the frozen wrong-action and narration false-negative
evidence. Real old-promise and discovery-dependent coverage remains pending until
the preceding journey succeeds; changing the assertions to manufacture coverage
is not a remedy. Preserve this failed cohort when qualifying future improvements.
