# Independent coverage-v2 core review

Refs #11 M07.03/.04 partial core prerequisite supporting M07.02. No embedding,
durable-maintenance or full milestone acceptance claim. Reviewer
`/root/resource_metrics_review`, [claim6368800123](https://github.com/OptimumAF/LocalLore/issues/11#issuecomment-6368800123),
separate `review/m07-coverage` / `source-memory-coverage-review` worktree.

Started at freshly fetched accepted main
`bffa7e66bf888411a6a5fce47165965fa247a2ce`. Imported unchanged coordinator ancestry
helper `e5a5460` as `100ce45`, author coverage source
`d3ba729dbc73a631582207b682e8708dc9e1a7f3` as `3a5d7b9`, and author evidence/docs
`fe5150c` as `d15f9c2c463ee5ddd52cc324dde3149fc1477b69`. Reviewer added only
`tests/memory_coverage_review.rs` and this document. All production source is
unchanged; the separate author worktree was not edited.

## Disposition and inspected behavior

No blocking finding in this finite independent source review and test cohort.
This is agent review, not human approval. The coordinator owns shared Store,
schema, compiler/Host/Play integration and upstream acceptance.

Read the full `memory_coverage.rs`, its author tests and contract, selected-lineage
helper, `Engine::at_revision`, the actor visitor and its existing eligibility
predicate. The module reuses that predicate before serializing any event content.
It never creates canonical state, persists memory, accepts a provider result,
duplicates witness filtering or supplies an alternate compiler.

Binding checks actual scope, expected head and actor, hashes the canonical seed
and private selected ancestor chain, and retains original event scopes/sequences.
The chain includes pre-birth fork caps, excludes unrelated branches and does not
bind the mutable current head. An equal scoped sequence number alone does not
identify an accepted source; verification rebuilds full source content from the
actual immutable Engine. Checksums do not authenticate history.

Builder progress is in completed receipt endpoints, including intervals with no
eligible events. Event/source/encoded overflow rejects the complete next turn,
with no partial-turn cursor. Exact receipt/event quanta seal without lookahead;
overflow sealing requires the actual next turn. EOF is a replaceable open tail.
Old tails rebuild at their actual historical endpoint, leaving the exact later
delta raw. Empty or malformed, unsupported, wrongly bound, gapped, overlapping or
unprovable supplied cache sets cannot certify partial coverage. Live source,
scope/head/actor failures and cancellation remain errors. The private reduced
budget test exercises the same builder; it does not establish that a public
64KiB single-turn overflow was reproduced.

The bounded writer accounts for JSON escaping and stops encoded materialization.
Packet/receipt/event/source limits constrain representation, not aggregate
heap/RSS, scheduling or hard deadlines. Visitor scans can repeat across32 packets;
historical reconstruction and hashing/serialization remain synchronous. No speed
or lower memory-use measurement is implied. Cooperative checks catch callback
panic as cancellation, and canonical Engine state remains immutable.

The opaque `VerifiedCoverage` type prevents public construction/deserialization,
but is not a durable capability. Its recheck rebuilds against the supplied actual
compiler Engine. The reviewer independently tested an alternate Engine with all
binding headers and scoped references identical but different accepted content;
the retained opaque value correctly falls back rather than trusting its origin.

Private packet hashes, completed-turn counts and headers can encode history
metadata outside an actor's visible content. They are cache validation data and
must not be forwarded wholesale into actor prompts or ordinary logs. A future
consumer still needs current mandatory facts/state/promises, exact raw delta or
whole raw fallback, scoped-source deduplication and safe failure on budget excess.
Nothing in this core API grants a Host inspection or model-access privilege.

## Independently executed verification

Windows x64 OS10.0.26300.0, rustc/Cargo1.93.1. All output was in the new private
D: `memory-coverage-review` directory, with TEMP/TMP in its
`temp-481cb7a0` subdirectory; locked/offline, debug0 and incremental0.
No model, storage DB, application, device or external inference was used.

```powershell
$env:TEMP="$reviewRoot/temp-481cb7a0"
$env:TMP=$env:TEMP
$env:CARGO_PROFILE_DEV_DEBUG='0'
$env:CARGO_PROFILE_TEST_DEBUG='0'
$env:CARGO_INCREMENTAL='0'
cargo +1.93.1 test -p locallore --lib --test memory_coverage --locked --offline --target-dir "$reviewRoot/target"
cargo +1.93.1 test -p locallore --all-features --lib --test memory_coverage --test actor_observations --test context_compiler --test lineage_consumers --locked --offline --target-dir "$reviewRoot/target"
cargo +1.93.1 test -p locallore --test memory_coverage_review --locked --offline --target-dir "$reviewRoot/target"
cargo +1.93.1 test -p locallore --test memory_coverage_review --all-features --locked --offline --target-dir "$reviewRoot/target"
cargo +1.93.1 clippy -p locallore --lib --test memory_coverage --test memory_coverage_review --locked --offline --target-dir "$reviewRoot/target" -- -D warnings
cargo +1.93.1 clippy -p locallore --lib --test memory_coverage --test memory_coverage_review --all-features --locked --offline --target-dir "$reviewRoot/target" -- -D warnings
cargo +1.93.1 fmt --all -- --check
git diff --check
```

All exited0; no test failure, skip or ignore in these focused runs:

| Cohort | Actual result |
| --- | --- |
| Default author/helper tests | 2lib +13coverage =15pass |
| All-feature author/helper and existing consumer tests | 15lib +13coverage +3visitor +10compiler +7lineage =48pass |
| New independent tests, default | 3pass |
| New independent tests, all features | 3pass |
| Strict default/all-feature Clippy, fmt, diff | pass |

The author's1028-event source parity, hidden/empty windows, nested pre-birth,
same-scope/different-ancestry, old-tail/current inventory,150-commit replacement,
252→259 whole-turn lookahead, exact256 quantum, real encoded64KiB closure,
forged/recomputed hashes, gaps/overlap/duplicates, bounds and observed cancellation
checkpoint tests were executed by this reviewer. Coverage tests took6.06s in the
default run and5.81s in the all-feature run; these suite timings are not product
retrieval benchmarks.

New independent actual Engine cases add:

- Retained `VerifiedCoverage` recheck against alternate accepted text with the
  same scope/head/seed/lineage/scoped refs: SourceMismatch fallback. The original
  Engine still verifies; both alternate canon and receipts remain unchanged.
- A wholly hidden128-receipt sealed prefix, then head advancement to130:
  verified head130, coverage and raw-delta endpoint128, empty visible entries.
- Real accepted Unicode/quote/backslash/newline/tab statements: encoded packet
  budget closure, exact text after JSON roundtrip, bounded bytes and complete-turn
  endpoint; the unwitnessing Sable packet remains empty and canon unchanged.

Private local logs: `tests-default.log`, `tests-allfeatures.log`,
`tests-independent.log`, `tests-independent-allfeatures.log`,
`clippy-final-default.log`, `clippy-final-allfeatures.log` and `fmt.log`.
No generated artifacts are committed. Production module SHA256 matches the
author's frozen file:
`ebcc9fe61eb2298bd81ab9b32139e5e9a5c0286e1c62be0da671c0c259362219`.

## Remaining gates

No durable job ledger/cancellation, transactional Store checkpoint, process-death,
storage-full, actual compiler forwarding, prompt-version migration, Host/native
IPC, Android parity, model use/quality or performance gate is satisfied by this
pure core slice. No production path uses these new packets yet. The next runnable
task is coordinator-owned coherent Store/job/schema integration, then a versioned
compiler/Play consumer with mandatory-state and exact-fallback proofs. Full #11
remains unchecked; no PR, merge, release, settings, desktop control or protected
runtime/device action was performed by this reviewer.
