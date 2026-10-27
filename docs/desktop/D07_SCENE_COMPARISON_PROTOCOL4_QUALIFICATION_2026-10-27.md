# Protocol4 scene comparison producer qualification

2026-10-27. Refs #29 D07.03/.04, supporting #25 D04.04 and #9 M05.03.
**Supporting producer slice in review; full tasks remain open.** This report
records synthetic Rust producer/Host/Store tests and the closed native adapter's
source boundary. There is no new model, native application, IPC/WebView, Android
or human-quality execution. The original eight-sample **needs improvement**
assessment is unchanged; reports retain `human_reviewed=0`,
`human_rubric="not_reviewed"`, `quality_accepted=false`.

The [Protocol4 contract](D07_SCENE_COMPARISON_PROTOCOL4_CONTRACT_2026-10-27.md)
preserves the original source freeze, prerequisites and later handoffs. Its
dated proposed/unrun statements remain historical. This report adds measured
results without replacing that history or granting model execution. Host/Core
dependencies remain [draft PR237](https://github.com/OptimumAF/LocalLore/pull/237)
and [draft PR232](https://github.com/OptimumAF/LocalLore/pull/232); their broad
results belong to their own source-bound qualification reports, not to this
producer by inheritance. The separate synthetic native UI packet in PR238 does
not execute Protocol4 comparison or a model.

## Implemented boundary and evidence meaning

`memory_comparison_v4.rs` defines separate closed metadata, descriptors and
reports. Exact arms are literal scene on the left and state-relevant memory
scene on the right; required nullable keys remain required and unknown keys,
mixed descriptors and unknown versions refuse. Native construction mapping is
a private typed match to existing Host selectors. Deserialization does not
create execution authority. Current binding includes complete source, suite,
profile/reference and original budget identities.

`local_lane/comparison/scene_v4.rs` reuses existing actual Host/Store execution,
collector/recording, checkpoint/settlement and strict evidence helpers. Paired
snapshots use unchanged validated reference prefixes; continuous rollout uses
each arm's generated accepted history. They are distinct comparisons. The
original four-scene suite has 24 steps per arm: 21 expected accepted and three
expected guards, 48 rows total. Full scripted paired and rollout tests each
verify all 48 outcomes, 42 source-bound committed rows, guard zero-role behavior,
exact Store receipts and the independent scene-capture gate. Paired tests
require 24 same-input pairs. These are synthetic outcomes, not measured model
success rates or enjoyment.

Only a fresh immediate **Domain1 committed** turn can receive
`validated_committed_scene_narrator_v1`. The gate regenerates staging and
Narrator prompt/schema from the actual complete Store prefix and receipt,
binds recipe/profile/candidate/proposal/approved data and indexed recordings.
It checks narrator **input consistency**, not Director source reconstruction,
raw-output origin/causality, actual provider/model execution or memory
compiler/cache execution. Existing `exact_reconstruction=false` remains false.
Identical Narrator inputs across arms are allowed for identical approved
source. Expected guards are explicitly not applicable, dependency-skipped rows
are not executed, and missing/recovered/failed/cancelled/Domain2 evidence cannot
be promoted to a committed source pass. `completed` means four scenes are sealed,
not that every row passed or quality was accepted.

Strict inspection reconstructs rows from retained actual Store/capture/
recording/raw/ledger evidence. Rehashed diagnostic edits cannot replace actual
receipt/provenance or regenerate Narrator source. Missing, unreadable or
hash-invalid required files keep the shared strict inspection refusal; no
tolerant reader or canonical repair is added. Lost-checkpoint recovery preserves
unknown historical calls and unavailable evidence rather than inventing zero
work. Completed scripted resume is checked by unchanged whole-file inventories;
that is no new durable work, not an injected provider-call counter.

The separate `scene_v4/native.rs`, behind `local-model`, reuses the existing
trusted reservation/startup/runtime owner. Source retains both invocation
reservations before asset acquisition, current-source/profile/reference checks,
existing cancellation/drain and conservative uncertain-ownership accounting.
The measured public native tests stop before owner/asset acquisition: pre-cancel,
invalid scene count and reservation refusal never enter their asset methods.
They do **not** qualify actual Protocol4 model load, process drain, panic cleanup,
native completed no-load resume or accounting under a real runtime. Native CLI,
desktop consumers and selected reruns remain separate integrations; old
Protocol2/3 and selected2/source3 meanings/defaults are not repointed to V4.

Original limits remain 32 admissions, 96 reserved roles and 1,800,000ms active
time per arm; 60,000ms turn watchdog, 120,000ms preparation, 3,000ms cleanup
reserve and existing 2,000ms runtime cancellation/drain deadline. Profile caps
are context4096, Director/Narrator350 tokens, one repair and120,000ms deadline;
role visible output cap remains16,384 bytes. Descriptor/budget checks and
scripted settlement tests do not establish real-model timing or cleanup.

## Privacy classification, first failure and corrections

The initial producer/oracles are source-frozen before execution. Corrected API
prerequisites include required budget version1 and setup-version4 admission;
missing future APIs at freeze are not behavioral RED. At clean unchanged
`2f50cb146c5fb495022f47ce2626b6df85c22d0f`, the feature-enabled17-test binary
first compiles successfully in27.3436488s, then actually runs **16 passed,
1 failed** in362.0796843s command time (361.27s test time).

The failing function first exercises a private copy of genuine completed
scripted evidence with self-consistent **empty** Narrator diagnostic bytes.
Inspection returns `CheckpointEvidenceMismatch` instead of the required failed
privacy report. The function stops there; its sentinel variant is **not** a
separately measured baseline failure. Original 15 controls plus the separate
missing/unreadable/hash-invalid raw refusal case pass. These copies mutate
diagnostic bytes/hashes/seals only; the actual canonical receipt and forwarded
Narrator input remain unchanged. They are not fresh generated model output or
authenticated evidence-origin tests.

Private correction `5f20344a`, integrated/formatted at
`00ddb65e5272c723c7ea295471af866624814d4b`, distinguishes empty/unavailable
evidence from observed fixed-sentinel violations. Nonempty bounded UTF-8 raw
bytes must match their declared length/hash. The unchanged17 tests then pass
in372.1058107s command time (359.91s test time), including both variants. Public
privacy status stays `Unavailable` for both failures, while their causes differ:
`observer_or_output_privacy_evidence_unavailable` versus
`observer_or_output_privacy_violation`. The original source-bound Narrator gate
can remain valid for an unchanged committed input even while privacy fails.

Strict Clippy at00ddb separately fails on the existing supported setup pattern
`2 | 3 | 4`. `193dd780` changes it to the equivalent `2..=4`, without changing
admitted versions, historical setup decoding or oracle intent. This is a lint
correction, not a new behavioral result.

Four independent noncommitted controls are first frozen at `c050af3a`; their
optional private observer seam is absent then, so that source is
**UNCOMPILED/UNRUN, not behavioral RED**. Implementation is integrated/formatted
at `903a2940b494c44110aaa670295b8c28594cfc01`. All four actually pass in
11.0970999s command time (0.42s test time), source clean and unchanged.

These four cases use actual existing scripted Host/Store ready-to-cancel or
failed-Director attempts, with no commit and no receipt. Complete history and
projection remain unchanged. Available retained positive flags or consistent
raw sentinel observations survive absent capture/receipt channels as violation
diagnostics; clean incomplete evidence remains unavailable. Optional
`finite_privacy(..., Option<&Value>, Option<&Receipt>)` never creates a checked
construction or privacy pass without the actual committed source gate. Tests
also call the private row builder to retain the public cause tag and
`passed=false`. Explicit flag/loss diagnostic copies are distinguished from the
genuine attempt itself. This is not a full producer cancellation/settlement
journey or a real SDK/model failure measurement.

## Actual results and final checks

| Check | Clean unchanged source | Result / command seconds |
| --- | --- | --- |
| First feature-enabled17-test compile, no-run | 2f50cb14 | PASS;27.3436488 |
| First17 producer/privacy oracles | 2f50cb14 | 16 passed/1 failed/0 ignored;362.0796843 |
| Corrected unchanged17 | 00ddb65e | 17 passed/0 failed/0 ignored;372.1058107 |
| Strict Eval Clippy first | 00ddb65e | FAILED one range-pattern style diagnostic;8.3215470 |
| Four noncommitted controls | 903a2940 | 4 passed/0 failed/0 ignored;11.0970999 |
| Unchanged17 after noncommitted integration, explicit one test thread | 903a2940 | 17 passed/0 failed/0 ignored;543.6751233 (533.74 test seconds) |
| Strict Clippy after that run | 903a2940 | FAILED one existing test's redundant `ok().expect()`;8.3072715 |
| Strict Clippy after removing redundant `ok()` | d828b9f3 | PASS;6.4368025 |
| Formatting at d828 | d828b9f3 | FAILED module declaration order;4.4687004 |
| Final formatting / strict Clippy | 6d7fe511 | PASS;2.5473341 /13.2548317 |

`d828b9f3` removes only the test assertion's redundant `ok()`; direct
`Result::expect` retains the same success condition and preserves error detail
on failure. `6d7fe511` only orders a module declaration. No assertion condition,
private classifier or runtime behavior changes after the 903 test executions.
The seventeen tests were not repeated after these style-only changes; final
strict lint compiles all targets. The earlier17 commands had no explicit
test-thread override; the final command explicitly uses one. Their durations
are not a controlled performance comparison. All final process records report
clean unchanged source.

The focused commands use existing pinned offline packages and one owned target;
no new package/model download or profile upgrade occurs. Root coordinates one
heavy job at a time. Package-scoped Eval cache cleans have separate retained
process records and alter no source; they are not pass evidence or permission
to clean arbitrary occupied targets. No new whole-workspace, native application,
UI/IPC/render, Android build/device or model execution is inferred from these
focused tests. Established Host237 broad checks remain separately attributed.

From the repository root, use an already provisioned exact-lock cache, existing
ordinary task-owned target and owned TEMP/TMP. Command forms replace private
paths only:

```powershell
$env:CARGO_HOME = '<existing isolated exact-lock package cache>'
$env:CARGO_NET_OFFLINE = 'true'
$ownedTarget = '<owned Rust target directory>'
cargo test --manifest-path crates/locallore-eval/Cargo.toml --test scene_comparison_v4 --features local-model --locked --offline --jobs 1 --target-dir $ownedTarget --no-run
cargo test --manifest-path crates/locallore-eval/Cargo.toml --test scene_comparison_v4 --features local-model --locked --offline --jobs 1 --target-dir $ownedTarget
cargo test --manifest-path crates/locallore-eval/Cargo.toml --test scene_comparison_v4 --features local-model --locked --offline --jobs 1 --target-dir $ownedTarget -- --nocapture --test-threads=1
cargo test --manifest-path crates/locallore-eval/Cargo.toml --locked --offline --features local-model --lib --jobs 1 --target-dir $ownedTarget noncommit_privacy_review_tests -- --nocapture --test-threads=1
cargo clippy --manifest-path crates/locallore-eval/Cargo.toml --all-targets --features local-model --locked --offline --jobs 1 --target-dir $ownedTarget -- -D warnings
cargo fmt --manifest-path crates/locallore-eval/Cargo.toml --all -- --check
```

The test suite creates ordinary private synthetic fixtures under task TEMP,
copies bounded closed templates before mutation and leaves generated evidence
local. It imports no real player story and publishes no private raw prompt or
save. Native reservations in the two before-owner tests refuse before assets;
enabling `local-model` compiles that boundary, not a model workload.
Environment is Windows NT10.0.26300 x64 and Rust/Cargo1.93.1 with the previously
provisioned locked dependencies. No new version probe or runtime/device inventory
is performed by this documentation pass.

## Hashes and remaining gates

Local raw logs/process records retain the `d07-scene-v4-*` stems. Hashes below
identify saved bytes, not authenticated model-output origin or a complete
producer artifact seal. Source hashes are at903a2940; earlier result rows retain
their own source commits.

| Public source / retained local evidence | SHA-256 |
| --- | --- |
| `crates/locallore-eval/src/memory_comparison_v4.rs` | `790a4ce89433f188c0f3368dba8b9ea09d1326272c2463a840b4457801d0fe57` |
| `crates/locallore-eval/src/local_lane/comparison/scene_v4.rs` | `9ef2247c432f9d615ffe9718529e30c3152b513e10c26585c05f70f36ad8a6c9` |
| `scene_v4/native.rs` | `d066cec1d3e9d885446cfa07d241d4931328e9dc7a7bc155e9f53eb97208f0fb` |
| `scene_v4/noncommit_privacy_review_tests.rs` | `8c9bb21cded25b4b5f5596cbd2ae8f14484f4653e810c608e0c4d2f12a9a28f2` |
| `crates/locallore-eval/tests/scene_comparison_v4.rs` | `3d7e56dae73f430cefffe0cc51d5293d72221ac8fb8593304a64bfb751073017` |
| `crates/locallore-eval/src/scene_capture_v1.rs` | `02831ff8af5d34b8ca8a2adffe02d10b7e55a90f704e2fb2a62b8f07b4a6c658` |
| Unchanged `Cargo.lock` | `4fb7c498ca0ecc62c4ea1f65c63b370ab4336eb75133d08b3a71f5664156cf93` |
| `d07-scene-v4-first-oracles1.log` | `e79f1bc6c015c7398a84945b68d409c97394d45691e6d1fa0b60880c32bbdb50` |
| `d07-scene-v4-first-oracles1-process.json` | `f0b0a3bfc52c3e51fa72e84c5f0e0918cc71aa6d0ca96360cbd3b5589c3c83ec` |
| `d07-scene-v4-oracles-green1.log` | `7fe62de32a112e8f00d76047f25ae8b9c22e3c1361fccf01c8436529f75af06e` |
| `d07-scene-v4-oracles-green1-process.json` | `743c04761d55aa6029da56aed92d4712b9bc06d5178fce9b521ca389753adf74` |
| `d07-scene-v4-noncommit-four1.log` | `1267b9d91acbb683962bed6e8662836619e1a9acbdad98d74f6e9c60af1fe746` |
| `d07-scene-v4-noncommit-four1-process.json` | `0a2d90d30a521a65b40277fa0a6fe5c3c59d34d667f3902b5121f1c8a7b2164a` |

No new human samples, scores, superiority claim or quality acceptance follows
from synthetic success. Finite sentinel checks do not establish universal
semantic privacy. Complete model-load/cleanup/admission qualification, the
separately frozen read-only consumer, selected execution, actual native UI,
authorized model comparison and human assessment remain with their owning
tickets. The next gate is dependency-aware focused producer review, followed by
the separately frozen read-only consumer and bounded real-model qualification.
No task checkbox, merge, release or settings change is authorized by this report.
