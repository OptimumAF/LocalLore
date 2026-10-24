# M08 Query2 source and unrun oracles — 2026-10-23

Refs #12 M08.03 and #30 D08.05 prerequisite. Status: `in_review`, implemented
source **UNCOMPILED / UNRUN**. No current author wire, compiler or native
consumer is enabled by this packet. Root owns integration and actual execution.

## Exact binding and ownership

Separate `impl/m08-query-v2` / `source-query-v2`, base
`54f094be9b4744471abb86134528cfad93a2c457` (candidate pure author Core plus
independent frozen Core oracles and accepted consumer contract). Claims:
#12 6376999500, #30 6376999729. The completed Core and contract worktrees remain
unchanged. Root approved the exact typed plan before production edits.

Only existing ownership is `crates/locallore/src/inspection_query.rs`: 23
additions for version dispatch, early legacy-domain guard, additive source/origin
enum arms and narrow internal V2 module/row registration. No existing statement
was deleted or rewritten. New files are `src/inspection_query_v2.rs`,
`tests/m08_query_v2.rs` and this document. Engine/author/lib/contracts/Host/Store/
compiler/Play/capture/export/platform/schema and old tests are untouched.

Frozen sequence:

- `541a0f0`: ten NEW actual-Core test oracles, before production edits.
- `4aa8263f9c54fa66d12a22d005c2a9f0b509d584`: Query2 production source.
- `b519ed6`: explicit NEW test-fixture correction before any execution. The
  original provenance case asked the player's outgoing relationships for a
  gift-obligation source. Existing `resolve(Give)` changes the recipient Mira's
  obligation toward the player. The positive scoped-source assertion now reads
  Mira's own granted relationship view. All original player read-only/pagination
  assertions remain unchanged. `541a0f0` is retained and was never compiled or
  run; this is not a demonstrated production RED or an oracle waiver.

## Implemented source surface

`QUERY_VERSION` stays 1. Public Query/Page shapes are unchanged. The same
`query` function dispatches request version 2 to the new module; version 1 on
Domain 2 returns `QueryError::Version` before any lens, including omniscient,
historical or TurnDiff. Unknown versions still return Version. Domain-1/version-1
query code, serialization arms, sorting, cursors and original tests remain
unchanged. No broad shared-code refactor was performed.

Additive Serialize-only arms:

```rust
Source::ScopedEvent { original_scope: Scope, sequence: u64 }
ValueOrigin::KnownAsObserved
```

V2 output/cursor namespace is 2. Cursor identity includes the actual versioned
query and matching eligible row bytes, and never author-private payload.
Cursors detect stale/cross-query edits; they are not authentication or canonical
source tokens. Existing row/page/search/cursor/candidate/byte limits remain.

The actor read lens is built from actual Core `actor_receipts_v2`,
`character_context_v2` and `observed_facts`. Its scope map contains only actual
eligible event references. Current knowledge uses KnownAsObserved, not current
world truth or belief conversion; recorded discoveries use the actual per-event
ActorEventV2 observation value. Beliefs, statements and mechanics retain their
distinct origin/visibility rules. Relationship/promise presentation reuses the
existing already-filtered branches and maps supporting visible event sources
to actual original scopes; missing/hidden evidence stays Withheld.

NPC history has only eligible Event rows. Empty ordinary receipts disappear
before search/count/pagination. No raw player Request, Proposal or narration
is attached. The owning player's actual input/narration appears only when all
ordinary receipt events are visible; typed actions without prose gain no
invented input. Message event IDs refer to the accompanying original-scope event
rows. Author records are never treated as ordinary receipts or messages.

Only a granted omniscient lens enumerates all ordinary selected events and
extracts `effective_fact(...).proposition`; it never serializes the full native
EffectiveFactView, private truth source, author record or reason. Query2 uses
uniform Withheld world-truth provenance in BOTH domains, as explicitly approved
by Root. This prevents per-fact private-source flags and avoids invented source
changes for every fact at the first author interval. Query1 seed provenance
remains unchanged. Actual per-event discovery values still come from the Core
discovering actor's V2 observation, not a current truth lookup.

TurnDiff2 uses the actual completed-boundary catalog and previous canonical
boundary, including author-only intervals. Actor state can have zero changes
at a new public head. Private omniscient comparison can show the actual changed
proposition without exposing author provenance. Historical snapshots reuse
actual Engine::at_revision and its validated lineage; no new replay/ledger or
flattened scope is introduced.

The crate-private `actor_context_rows_v2(engine, actor, view)` permits only
Profiles/Knowledge/Relationships/Promises and has no grant argument. A narrow
dead-code allowance documents that the separately owned compiler2 is not yet
its consumer; it does not enable a compiler or waive runtime verification.

## Frozen acceptance oracles, not executed results

1. Query1 Domain2 Version for every observer/view/grant, including unknown actor,
   omniscient, unsupported views and TurnDiff.
2. Player/NPC remember A after private truth B; private granted omniscient sees
   B with uniform Withheld provenance and no reason/private truth wrapper.
3. Same-turn repeated rediscovery exposes actual B per event/current latest
   scoped observation while NPC retains A.
4. Private self-speech produces zero NPC history/search/count/page rows;
   witnessed speech is a positive event-only NPC case without raw player data.
5. Owning player actual Dialogue yields original input/narration only under
   complete ordinary-receipt eligibility; NPC receives only its event.
6. Author-only completed head has empty actor diff and exactly one actual
   private world-proposition diff, not ordinary-receipt boundary substitution.
7. Version-1/2 cursors cannot cross, and search/query tampering rejects.
8. Original inherited discovery scope survives ordinary child fork; parent
   future/sibling/private author canaries are excluded; prebirth returns A.
9. Unknown versions, limit/search/cursor bounds/control text, wrong scope/head
   and partial multi-event historical boundary reject closed. Shared summaries/
   retrieval indexes remain explicitly Unsupported.
10. Actual gift/relationship/promise/profile/knowledge/provenance/history/diff
    pagination is bounded, deterministic and read-only; Mira's real directed
    obligation source is scoped to the actual gift event.

These tests use actual typed Engine commits/corrections/forks, not fabricated
receipts, DB fixtures, a provider or a second knowledge interpreter. Root's
independent Core tests/results belong to their own packet; none are claimed as
execution of Query2 here.

## Actual checks and unavailable gates

Actual standalone source checks only:

```text
rustfmt --edition 2021 --config skip_children=true crates/locallore/tests/m08_query_v2.rs
rustfmt --edition 2021 --config skip_children=true crates/locallore/src/inspection_query.rs crates/locallore/src/inspection_query_v2.rs
git diff --check
```

PASS: parser/formatting and whitespace, owned-path diff and clean source tree.
These are not Rust typechecking or behavioral results. Git
2.33.0.windows.2, PowerShell 7.6.5, rustfmt
1.8.0-stable (01f6ddf758 2026-02-11). Android retains the sole heavy slot;
**no Cargo/Node/Gradle/build/model/app/device/native IPC/render/CUA/ADB/desktop/
download/settings/protected-resource/PR/merge action ran** for this packet.

After Root grants a slot, proposed locked/offline jobs1 own-target/TEMP checks:

```text
cargo test --locked --offline -p locallore --test m08_query_v2 --jobs 1
cargo test --locked --offline -p locallore --features host --test m08_query_v2 --test inspection_query --test lineage_consumers --jobs 1
cargo test --locked --offline -p locallore --all-targets --jobs 1
cargo test --locked --offline -p locallore --all-targets --all-features --jobs 1
cargo clippy --locked --offline -p locallore --all-targets --all-features --jobs 1 -- -D warnings
```

Preserve every compile/behavior failure before narrow source or explicit fixture
repair. Do not change an old test or expected privacy/budget outcome to obtain
a pass. Root owns compatibility with future compiler2/Play2.5 and Host/schema/
frontend routing. In particular, this does NOT fix Host PlaySnapshot's legacy
unwrap or export/old proof/jobs/Store ledger compatibility; author native/session
reachability stays unavailable until the complete consumer closure is real.
No performance, model-quality, human approval or full M08/D08 acceptance claim.
Claims are released at handoff for Root's independent review and actual tests.
