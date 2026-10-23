# Durable fork prerequisite

Refs #12 M08.01/.02 and #30 D08.04 dependency, **partial/in_review**. Claims
[6359949860](https://github.com/OptimumAF/LocalLore/issues/12#issuecomment-6359949860)
and [6359950283](https://github.com/OptimumAF/LocalLore/issues/30#issuecomment-6359950283)
preceded implementation. This is a shared Rust/Store slice, not branch UI,
correction, playable archive, transfer or full M08/D08 acceptance.

## Native Rust interface

```rust
pub struct ForkRequest {
    pub parent: Scope,
    pub child_branch: String,
    pub expected_parent_revision: u64,
    pub at_revision: u64,
}
pub struct ForkOutcome {
    pub scope: Scope,
    pub parent: Scope,
    pub fork_revision: u64,
    pub head_revision: u64,
    pub created: bool,
}
impl Store {
    pub fn fork_branch(&mut self, request: &ForkRequest,
        cancel: &dyn Fn() -> bool) -> Result<ForkOutcome, TurnError>;
}
```

The trusted native caller chooses a fixed child ID before attempting creation;
it is an operation identity, not a display name/path. Repeating the same story/
child identity with the same immutable parent+fork point resolves the existing
child with `created=false` and its **current** head, even after either branch
advanced or the expected-parent guard changed. A different parent or fork point
for the same child returns RetryMismatch. This is **not byte-equal full
ForkRequest retry** or replay of the first response. `expected_parent_revision`
is a new-creation admission guard only. It is checked under the writer transaction
before creating a new child; a stale guard makes no change. Full-request turn
idempotency remains unchanged and scoped to story+branch+turn ID.

No model/text/renderer JSON can manufacture a prepared accepted history through
this API. It accepts no SQL, database path, seed, projection, receipt or arbitrary
lineage import. There is no new app command or privileged author grant here;
future Host/native UI integration must define and authorize that boundary.

## Representation and replay

Existing schema001 already has branches.parent_branch/fork_revision/head_revision
and scoped canonical tables. **No DDL, migration, receipt format, domain version
or Host schema changes.** New child metadata records the actual parent/fork and
starts at head=fork. The child receives seed entity registry membership rebuilt
from the validated Engine's seed, plus a replaceable canonical projection cache.
It receives **zero copied ancestor turns, events, witnesses, drafts or summaries**.
The entity registry is the fixed seed universe, not what an NPC knows; current
rules cannot dynamically create actors. No foreign registry/projection is treated
as canonical state.

The shared loader walks one explicit root-to-leaf metadata path. It validates the
story's actual root, parent existence, integer ranges, head/fork relations, depth
and cycles before replaying any receipt. It never scans sibling histories. For
ordinary ancestry it reads ancestor local outcomes only through the next fork.
A nested child may rewind before its parent's own birth: a temporary parent prefix
up to that birth validates the intermediate fork, then the next actual Engine::fork
drops every event beyond its earlier boundary. Thus intermediate verification may
read some ancestry that the final child does not inherit; none enters the returned
child Engine or its character context. Later parent outcomes beyond required
verification prefixes are not fetched/parsed and cannot contaminate the child.

Every fork uses actual `Engine::fork`, accepting revision0 or a completed accepted
turn boundary. Partial turns/future revisions/invalid IDs fail. Ancestor receipts
retain original request/proposal/event scopes, original sequence IDs, narration
and accepted Play metadata. New child outcomes use child scope and start at fork+1.
Sibling numeric sequence IDs may overlap; source branch identity remains essential.
Canonical projection bytes can be equal across branches with equal state; those
bytes alone do not identify a story/lineage or form an archive.

`Engine::restore_continuation` restores local serialized receipts onto a cloned
validated fork, using the **same** strict UniqueJson/parser/full reconstructed
receipt validator as root restore. An error returns no partial engine and leaves
the input Engine unchanged. Accepted historical Play policies remain history-only;
fresh prepared commits still enforce the current policy. No provider/model runs
on restore. Existing root restore/replay and typed turn rules retain their authority.

For each selected source segment the loader compares original request columns,
complete canonical envelope bytes, event order/version/turn, exact witnesses and
orphan witness totals. Current-branch extra normalized rows cannot hide after the
head. Ancestor validation is limited to the selected prefix; later parent damage
does not poison an already forked valid child, while inherited source damage fails
closed. Projection caches can be missing/stale/forged: resume flags repair and
rebuild writes only the selected branch accelerator, never accepted history.

## Transaction, cancellation and capacity

New creation uses one IMMEDIATE transaction for admission, validated parent replay,
fork construction, branch row, seed membership and child projection. Cancellation,
SQL error or rollback removes all partial child writes. Existing parent history,
drafts and caches remain untouched. Losing a returned response can be reconciled
using the fixed child identity; no second fork is allocated automatically.
Existing Store begin/status/drafts/cancel/stale/commit/retry use the same scoped
loader, so independent child continuation has the same atomic outcome protocol.

Limits: **32 path nodes including root**, matching the existing Engine lineage
bound, and a conservative **256 branches per story** checked under the writer
reservation. The existing4096 retained-turn/16MiB history limits cover all required
loaded prefixes plus current-branch terminal/draft rows. New turn admission and
response commit account for this aggregate, preventing an accepted child turn
whose next restore would exceed the limit. Ancestor drafts/terminal intents are
not inherited. These conservative verification limits may reject a very large
path even if a later rewind discards part of it; they are not unlimited-history
or performance claims.

Cancellation is cooperative at fork stages before/after parent replay and before
commit; panicking private callbacks become Cancelled. Full Engine reconstruction,
receipt serialization and individual SQLite calls have no mid-call callback.
Holding the writer reservation through bounded replay is deliberate for this
small slice; prompt cancellation/maximum-scale UI responsiveness remains unqualified.
No runtime/model is loaded or lock held across inference. Actual process death
during this new fork transaction is not newly exercised by this packet; cancellation
and SQL abort tests plus existing Store transaction tests are finite evidence,
not an added crash-journey claim.

## Rewind, replacement and unsupported consumers

Regenerating **uncommitted** prose changes no canonical state; this API does not
regenerate prose. To replace a committed selected turn, a future trusted author UI
must create a new child from that turn's prior completed boundary (its original
expected_revision), then submit the replacement there. It must not replay dependent
downstream choices automatically. The old branch remains retained. This primitive
does not implement author retcons, correction-impact preview, deletion or policy
for accepting the replacement.

The context compiler, inspection query and derived-memory child guards remain
explicitly Unsupported. Their historical snapshot paths need separate lineage-aware
integration; removing those guards would conceal incomplete behavior. Low-level
actual Engine character_context/actor visitor works with the restored lineage and
is covered by source canaries. Existing Host/workspace interfaces and root story
catalogue are unchanged; an existing generic resume may load a known child scope,
but this slice adds no branch creation/list/selection UI or branch free-text lane.
No branch cache is copied or used to widen generation knowledge. No D03 inspection
file is relabelled a playable archive.

Verification and preserved fixture failures are in
[M08_DURABLE_BRANCH_EVIDENCE_2026-10-23.md](M08_DURABLE_BRANCH_EVIDENCE_2026-10-23.md).
Independent review and coordinator integration remain required. All full #12/#30
criteria stay unchecked, including archive/round-trip, correction/deletion, actual
app/Android/device/quality/offline and maximum-scale gates.
