# Pure memory coverage v2 — focused evidence, 2026-10-23

Status: M07.03/.04 partial prerequisite, in_review, no acceptance checkbox.
Contributor `/root/app_storage_review`, #11 claim6367988690. Isolated
`source-memory-coverage` / `impl/m07-memory-coverage`, based accepted main
`884cf3fe7ec144b8da082bef9a726d426d4aaf4c`.

Frozen owned source `d3ba729dbc73a631582207b682e8708dc9e1a7f3`: NEW core
memory_coverage.rs, NEW tests/memory_coverage.rs and one reserved lib.rs module
export after intent_guard. Coordinator dependency `e5a5460` imported as
`7caf4c5` adds only the private selected-lineage helper in Engine/scope and its
test. The helper is coordinator-authored, not this contributor's production edit.
No Store/schema/derived-v1/Host/Play/compiler/Android/UI/archive/dependency changes
were authored. [Contract and limitations](M07_MEMORY_COVERAGE_V2.md).

## Actual execution

Windows, Rust/Cargo1.93.1, locked/offline, debug0/incremental off. All output and
TEMP/TMP task-local on D; own target `m07-memory-coverage`. Synthetic Engine/fake
fixture tests only; no model, device, application/dialog/CUA, global settings or
protected-resource operation.

```text
cargo +1.93.1 test -p locallore --lib --test memory_coverage --locked --offline --target-dir <own-target>
PASS: 2 lib (new reduced-budget unit + coordinator lineage unit), 13 integration.
cargo +1.93.1 test -p locallore --all-features --lib --test memory_coverage --test actor_observations --test context_compiler --test lineage_consumers --locked --offline --target-dir <own-target>
PASS: 15 lib + 13 coverage + 3 actor visitor + 10 compiler + 7 lineage = 48.
cargo +1.93.1 clippy -p locallore --lib --test memory_coverage --locked --offline --target-dir <own-target> -- -D warnings
PASS
cargo +1.93.1 clippy -p locallore --lib --test memory_coverage --all-features --locked --offline --target-dir <own-target> -- -D warnings
PASS
cargo +1.93.1 fmt --all -- --check
PASS
git diff --check
PASS
```

Final logs under the task root: `memory-coverage-frozen-default.log`,
`memory-coverage-frozen-allfeature.log`,
`memory-coverage-frozen-default-clippy.log`,
`memory-coverage-frozen-allfeature-clippy.log`. Earlier incremental check/test/
Clippy and wire-fingerprint logs are retained; final results bind the source above.
No full-workspace/native/Android/platform test result is claimed here.

## Meaningful coverage

- 1,028 accepted events: an old promise, allegation and belief followed by1,025
  distractors. Exact complete scoped-source equality with existing character_context,
  deterministic repeated packets, distinct origin classes and unchanged canon/receipts.
- Private Mira dialogue and seed canaries excluded from Sable packets, including
  empty eligible windows that advance receipt boundaries; unknown actor refusal.
- Root5→a@5→b@1 with original root/b event scopes. Parent future and sibling
  canaries excluded. Two b Engines with identical receipts/projection but different
  actual ancestry reject cross-use. Parent continuation leaves the frozen child valid.
- Old open tail remains coverage of its original endpoint after a new gift; exact
  delta endpoint is unchanged, while current inventory remains canonical in Engine.
  Changed seed rejects reuse.
- 150 successive commits retain one window start, then one sealed prefix and one
  tail, rather than one new cache identity per commit. This tests the core boundary
  contract, not a persisted replacement implementation.
- A seven-command turn would change252→259 sources: closure excludes that entire
  turn; historical verification without its lookahead falls back. Exact256 source
  quantum needs no lookahead. Incomplete-turn starting cursor refuses.
- Actual public encoded64KiB boundary reached with long accepted speech; proof is
  recomputed, forged EOF sealing fails. Wide valid scopes and three actor lenses
  preserve receipt/event/source-byte/encoded caps.
- Missing prefix, gaps, overlaps, duplicate/omitted/foreign sources, modified event,
  unknown/future fields, duplicate JSON keys and open-tail-before-end all fail to
  certify coverage. Independently recomputing the documented checksum for forged
  source text still fails actual Engine comparison.
- Every observed cancellation checkpoint in build and verify returns no partial
  value; callback panic maps Cancelled. Wrong live scope/head stop and canon stays
  unchanged. Oversized input/packet count and JSON escaping stop bounded encoding.
- Separate private256-byte policy test runs the SAME builder on one real accepted
  Wait and proves Budget/no progress. Public builder succeeds for that turn. This
  does not claim a public64KiB single-turn overflow was reproduced.

First accepted Wait (`turn=one`, Lantern Quay fixture, player observer) wire SHA-256
is pinned independently of the reduced-budget test:
`37c1b6bbc85f4442a24c8325cea02def28d29e540e76186e3f325a43dd0c1f97`.

## Source bytes and handoff

SHA-256, paths under crates/locallore/:

| File | SHA-256 |
| --- | --- |
| src/memory_coverage.rs | `ebcc9fe61eb2298bd81ab9b32139e5e9a5c0286e1c62be0da671c0c259362219` |
| tests/memory_coverage.rs | `4dbb155895f936bdd96483015868f7e560e6509f8246c5be6a91a3e08ce2da64` |
| src/engine.rs (coordinator helper dependency) | `fb26532689a47e029f2e67ce39c161fda13c2a34b75d6e5c43f575f35e0d6191` |
| src/scope.rs (coordinator helper dependency) | `99ceb19fc682dcfc49b83674a1318f37c3b7f99732948a32717b354467fc446f` |

Independent source review and coordinator integrated execution remain required.
This contributor authored the coverage contract; these tests are implementation
evidence, not independent approval. Next is a separately frozen Store/job/schema
slice, then actual production compiler forwarding. No speed/heap/quality, model,
durable maintenance, pipeline-consumption or full milestone claim is made.
