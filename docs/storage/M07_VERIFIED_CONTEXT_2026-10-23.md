# Pure Core verified-coverage compiler input — 2026-10-23

Refs #11 M07.01/.03/.04/.06, supporting #29 D07.01/.04; partial, in review. Claim #11 comment 6372955526 / #29 comment 6372955906; byte-probe addendum #11 comment 6373077373. Coordinator-delegated author `app_storage_review`, isolated `impl/m07-verified-context` / `source-verified-context`, accepted base `b2c03d4151dc6d257f2dbddbb64b13950ddbf41e`. M07.05 is optional embedding evaluation and is **not** implemented or completed here.

Production implementation was frozen **before tests** in `89dddc3f0b6d4427e5e347411acb3dac76757f57`. Follow-up `6feb3614d289d7c3fcfa48291ec19435f07c9454` adds only four lines of bounded count logging to the new test; production files are identical. The final cohort below uses 6feb361. Independent coordinator review/integration is required; no PR, merge, milestone acceptance or favorable-score gate is claimed.

## Implemented interface and scope

```rust
context_compiler::compile_verified_cancelled(
    engine: &Engine,
    request: &CompileRequest,
    coverage: Option<&memory_coverage::VerifiedCoverage>,
    cancel: &dyn Fn() -> bool,
) -> Result<MemoryCompilation, CompileError>
```

`MemoryCompilation` contains the existing `package: ContextPackage` plus separate `coverage: CoverageDiagnostics`. The latter has closed `CoverageMode::{Raw,Verified}`, optional closed `MemoryFallbackReason`, packet counts (`packets_used`, `packets_fell_back`, `timespan_fallback_packets`, `mandatory_fallback_packets`), `covered_through`, `raw_delta_after`, and actual final event-candidate counts (`cached_event_candidates`, `raw_event_candidates`). No free-form content, packet source list, seed hash, elapsed time or hidden record names occur in these diagnostics.

This is a public pure Rust embedding port. It adds no Host/wire command, inspection grant, provider, native/UI adapter, storage dependency or cache persistence. A trusted caller already holding the Engine remains responsible for choosing its permitted actor, as with the existing compiler. The existing director/player restriction and scope/head/observer/historical-boundary checks remain enforced. The function does not grant a character knowledge or grant a renderer access to other actors.

Owned paths are exactly existing `crates/locallore/src/context_compiler.rs`; new child `context_compiler/verified.rs`; new tests `context_compiler_verified.rs` and `context_compiler_legacy_bytes.rs`; and this document. Existing budgets, tests/fixtures, `memory_coverage.rs`, query, Engine, dependencies, Store/schema/jobs, Play/policies/provenance, Host and generated schemas/types are unchanged. No production Play call uses this entry point yet. The existing package version, serialized shape and legacy unsupported labels are deliberately unchanged; this does not qualify a Store cache, job system or production consumer under those labels.

## Actual forwarding and conservative fallback

The new entry and the existing `compile`/`compile_cancelled` share **one** inner compiler. Request validation and actual snapshot selection occur first, with the same original errors. Existing structured row views, aliases, mandatory/supporting/recent/reference determination, deterministic ranking, limits, omissions and whole-package byte/token estimation are reused. The old event-to-EventRow constructor is extracted, preserving original scope, sequence, turn, story time, participants, witnesses, consequence, key and origin.

The supplied opaque proof is rechecked using the selected snapshot's actual scope, revision, seed, lineage and actor through the accepted v2 verifier. No independent eligibility, digest parser, partial-set trust or fake verified constructor was added. A rejected retained set uses raw observations from zero, with its closed fallback reason; missing proof also uses raw from zero. Cancellation remains `Cancelled`. Actual canonical source reconstruction failure remains `Source`, rather than being disguised as successful fallback. Other request errors are decided by the existing validation/snapshot code. Malformed/gapped untrusted bytes cannot construct a `VerifiedCoverage`; callers first use the existing verifier and supply no proof on rejection. This port accepts opaque proofs, not arbitrary packet bytes. In that absent-proof case it knows only `Missing`, not the upstream reason for absence.

For a valid prefix:

1. Each ordinary `Entry::Observation` supplies its **actual verified packet event** to the shared EventRow constructor and actual candidate list. It is not an ignored argument, a raw reread with a cache counter, or forced selection. Source identity is deduplicated by original `(Scope, sequence)`.
2. Any packet containing `ObservedTimeSpan` is refetched in full from the actual Engine's eligible observations over that packet's complete interval. The aggregate is never expanded into invented events or partly forwarded.
3. The existing mandatory pass identifies real current facts/state/beliefs/relations/open promises and event sources, recent floor, and referenced/supporting evidence. Any still-cached packet intersecting a mandatory event is refetched as a **whole packet** from Engine before final package construction. It verifies exact source membership, replaces the actual candidates with those Engine rows, and updates counts. It never merely changes a cached row's label to raw.
4. Eligible observations in `(covered_through, selected_revision]` are constructed from the actual Engine as the exact raw delta. Final candidate sources occur exactly once; all sorting/selection/omission logic is unchanged.

Mandatory final payloads always come from Engine. Structured views remain Engine-based, including optional statement/discovery rows those views already produce. Counts above concern **EventRow candidate construction**, not every structured row or every Engine visit. Accepted proof recheck itself rebuilds packets and may replay historical prefixes; mandatory packet fallback also scans actual source ranges. Therefore cached candidate counts do not imply avoided canonical reads, lower CPU/memory, fewer prompt tokens, faster compilation or model use. No performance claim is made.

`CoverageMode::Verified` means the prefix proof remained valid. A valid packet may nevertheless require complete raw fallback; even all packets may do so. `covered_through` describes the verified interval, including those refetched packets, not a claim that every covered source was taken from cache. `raw_delta_after` bounds only the suffix; `raw_event_candidates` also counts complete fallback packets in the prefix. Empty actor-eligible intervals can advance a verified completed boundary without increasing used-packet/event counts. In raw-set fallback, coverage/delta start are zero and the rejected-packet count may exceed the sum of per-packet fallback reasons. Diagnostics stay outside the unchanged ContextPackage accounting and do not enter a prompt here.

## Fixed model-free tests

Seven new tests call actual typed Engine accept/preview/commit, `build_chunk` and `verify_coverage`; no forged proof, SQL history or provider is used. The main fixture has an opening promise and gift, 600 accepted statements in 75 eight-command turns, and one player-private statement: **603 accepted events**, of which **602** are eligible to Mira. The old meaningful spindle event 303 is outside the recent floor and mandatory-support packets, remains selectable as an actual cached EventRow, and retains its original source.

Both final feature modes report the same actual construction:

```json
{"mode":"verified","set_fallback_reason":null,"packets_used":3,"packets_fell_back":2,"timespan_fallback_packets":0,"mandatory_fallback_packets":2,"covered_through":603,"raw_delta_after":603,"cached_event_candidates":384,"raw_event_candidates":218}
```

The tests require exact serialized raw/verified ContextPackage equality across lexical/ID/alias/empty/private queries under identical budgets, plus unchanged Engine projection and accepted receipts. They cover sealed prefix and retained old open tail after head advance, exact delta, TimeSpan whole-packet fallback, recent/mandatory whole-packet fallback, original ancestor scopes, nested prebirth lineage and same-scope/different-ancestry rejection, sibling/foreign/observer/source-change raw fallback, player-private/seed-secret exclusion, selected historical snapshots, malformed/gap/edited cache rejection, and original version/scope/head/observer/boundary/mandatory-budget/cancellation errors. Mid-operation cooperative cancellation is also triggered; no hard response deadline is claimed.

The malformed/gap tests reject untrusted bytes through the accepted verifier, then run the compiler without a proof. Opaque public typing intentionally prevents presenting such malformed bytes as a previously verified object. Changed actual history and wrong live scope/actor/ancestry do exercise recheck rejection of a genuine old opaque proof. Tiny mandatory budget returns the original error rather than dropping required rows. A proof covering a later revision is rechecked against the actual historical selected Engine before any cached event candidate is constructed.

## Legacy byte compatibility measured against the actual old compiler

The identical new `context_compiler_legacy_bytes.rs` probe ran on a separate checkout of accepted **b2c03d4**, with its existing compiler unmodified, before the new compiler runs. It defines five fixed synthetic cases: director, character, historical, referenced alias and mandatory-only. It compares repeated `compile`/`compile_cancelled` bytes and emits only hashes. No old compiler implementation was copied into the new code and no expected bytes were synthesized from the changed compiler.

All five SHA-256 values match the original compiler, new default, and new all-feature runs:

| Case | Serialized ContextPackage SHA-256 |
| --- | --- |
| Director | `b671903865fb32cc641747fe94f3f4264d8e6abb259e501223026967e43df18d` |
| Character | `2bc7c73c6407599b682265b4e9c3f26019cb4bef4e1ff871d7c5e17d6a090381` |
| Historical | `8dfecac53e93e57288d499bcc9321b970e1cc07ff9aceee98d1d260ef86a2e63` |
| Referenced | `7427d245754368d61b1469d29292be7fb67ee049632c3a4237cf8ba210a3abb7` |
| Mandatory-only | `369f6158981edd3012eb997914bd85e99aa7634fd866294e27a04000cd66b8bd` |

This is finite byte-compatibility evidence, not a universal proof or new recorded Play-policy acceptance. Existing ordinary compiler and coverage tests were not modified. Play/prompt versions remain unchanged, with no legacy fresh-commit widening.

## Commands, environment and retained failure

Windows x64; Rust `1.93.1 (01f6ddf75 2026-02-11)` / Cargo `1.93.1 (083ac5135 2025-12-15)`. Coordinator cleared a single portable process slot; all compilation/tests were sequential, `--jobs 1`, locked/offline. Task-owned D-drive target `m07-verified-context` and sibling `verified-context-artifacts/temp` were used; dev/test debug information 0 and incremental 0. No Store, model, worker, app, device, ADB, CUA, desktop control, protected resource, OS settings or download operation occurred.

```powershell
$env:TEMP = "$taskOutput/temp"
$env:TMP = $env:TEMP
$env:CARGO_PROFILE_DEV_DEBUG = '0'
$env:CARGO_PROFILE_TEST_DEBUG = '0'
$env:CARGO_INCREMENTAL = '0'
# Accepted old checkout first, identical new test file only:
cargo test -p locallore --test context_compiler_legacy_bytes --locked --offline --jobs 1 --target-dir "$taskTarget" -- --nocapture
# New frozen source; repeat with --all-features:
cargo test -p locallore --test context_compiler_verified --test context_compiler_legacy_bytes --test context_compiler --test memory_coverage --locked --offline --jobs 1 --target-dir "$taskTarget" -- --nocapture
cargo clippy -p locallore --all-targets --locked --offline --jobs 1 --target-dir "$taskTarget" -- -D warnings
# Repeat Clippy with --all-features.
cargo fmt --all -- --check
git diff --check
```

Use separate build targets for old/new checkouts when reproducing, or explicitly invalidate only the owned package after switching. The initial new-source compile, after using the same target for the old checkout, reported new API exports missing. No test ran. A package-scoped `cargo clean -p locallore --target-dir` of this task's own output removed 33 generated files / 41.5 MiB. The identical frozen source then passed. This is **consistent with** cross-checkout target freshness reuse, not a proved root cause. Original error and cleanup logs remain intact; no production/assertion/budget correction was needed. The tool wrapper also failed to store an absent running-session ID after that already-completed failing command; this was orchestration output, not a second Rust result.

| Actual final check | Result |
| --- | --- |
| Old compiler byte probe | 1 PASS; five serialized hashes retained |
| Default focused tests | **31 PASS**: existing compiler 10, byte probe 1, new verified 7, existing coverage 13; zero failed/ignored |
| Same all-feature focused tests | **31 PASS**, same distribution; zero failed/ignored |
| Strict Core all-target Clippy | PASS default and all features, `-D warnings`; no lint exemptions |
| Workspace format / owned diff checks | PASS |

The original focused modes passed at 89dddc3 after cleanup; both final modes were rerun at 6feb361 after bounded count logging. Only final same-source logs qualify the final packet. An existing coverage test deliberately panics inside a caught cancellation callback; that test reports PASS and no failed test is suppressed. No full workspace, storage, runtime, Android or native UI suite was executed for this packet. Test times are ordinary observations, not performance acceptance thresholds.

## Source-bound evidence

Task-local logs remain outside Git; no private history, full prompt, generated binary or model artifact is committed. Their contents are synthetic test/count data and normal local compiler paths. No automatic upload is added.

| Artifact | SHA-256 |
| --- | --- |
| Old compiler `baseline-bytes.log` | `1e6bbb3ddf75970537da3f8ab27dfdc8c3489f69e03874b31f49b77e5e777377` |
| Initial missing-export `focused-default-initial.log` | `f9b308e451e0d63c1a6eb15bdacc89379b4c63616777ab22520a28eb08d8e926` |
| `own-package-clean.log` | `e4fe46d73142b573d79589321bd22e5884f1e29093288d9f36e8380edb1c85f3` |
| Final `focused-default-final.log` | `525c16b0ce8e9326024bdb661655ac586b83b87bda5a07c09d9228f9417eca16` |
| Final `focused-feature-final.log` | `9e1da39f56919101bb97ad6e86d28cca3f2414944f6384cce8ee473d1713cb7b` |
| Final default Clippy log | `007363f60e4815f66c558786530ddb71bb3757e3ea8e4b62bf8f53939e432510` |
| Final feature Clippy log | `57cb6d249bba96f600e442f4ba30977a159f9a9e50250551a62ab213775f40da` |

| Frozen source | SHA-256 |
| --- | --- |
| `context_compiler.rs` | `882c10c04a159a9722c4a7758864eb0657f973c78138f634365fcb5af0c437b8` |
| `context_compiler/verified.rs` | `2e4caf490069b033c65faf8cfb6a2a3dd55d49c64e6c7fad01f8bafb6c7e590c` |
| `context_compiler_verified.rs` | `0590ba8b94ee3eeb1eb2596dafabe30e2ba3beec0fe7dfb1bbc859e0bd3ee110` |
| `context_compiler_legacy_bytes.rs` | `1ca2d2783812346858c243b7f6f97e08d54ad46d7a048ca523bb3a7aee7b0a39` |

Next runnable work: independent review, then coordinator Store coherent snapshot/job integration and explicitly versioned Play/prompt provenance wiring. Safe fallback is an entire-set raw prefix on proof rejection, with only already-verified per-packet source-format/mandatory fallbacks permitted; no trust relaxation or partial invalid-set reuse is proposed. Actual production forwarding, durable maintenance/process death, measured performance/tokenizer/model usefulness, UI/device parity and full M07/D07 gates remain unqualified.
