# Frozen actual-Store author oracles

2026-10-23. Refs #12 M08.03 / #30 D08.05. **Thirteen new test cases are
source-frozen, uncompiled and unexecuted.** Store author APIs and schema 5 were
not implemented in this source baseline. Missing APIs are not called an actual
RED run. This packet implements no author capability, migration or app feature.

## Attribution, scope and approved typed surface

Separate `review/m08-author-store-oracles` / `source-author-store-oracles` from
coordinator `1c0b0909c44f712002f258af71a30fba6561bf73`. Claims #12 `6377306411`
and #30 `6377306650` were posted before writing, after the coordinator approved
the exact typed API/oracle proposal. Agent `/root/author_core_review` owns only
these TWO NEW files:

- `crates/locallore-storage/tests/m08_author_store.rs`
- `docs/storage/M08_AUTHOR_STORE_FROZEN_ORACLES_2026-10-23.md`

Read actual existing Store integration-test conventions, Core/Store contracts,
prior independent Store contract findings and current claims. No existing
production, tests, migrations, DDL, Core/Host/compiler/platform contracts or
fixtures changed. Root retains all implementation and schema allocation.

Test source frozen **before Store author implementation** at
`92255d2ffadd6d43c16e5dbd4c3f39b667ecfecc`, SHA-256
`b449345ea0b6b16238cff6295bd1bfd2861d202c87d75188113e4e77f0570d3f`.

The tests infer opaque plan/outcome Rust types through these approved native
methods; they cannot construct or deserialize a preparation:

```text
Store::prepare_author_correction(&mut self, &AuthorCorrectionInputV1, cancel)
    -> Result<PreparedStoreAuthorCorrection, TurnError>
Store::apply_author_correction(&mut self, &PreparedStoreAuthorCorrection, cancel)
    -> Result<AuthorCorrectionOutcome, TurnError>
Store::lookup_author_correction(&mut self, &AuthorCorrectionInputV1, cancel)
    -> Result<Option<AuthorCorrectionOutcome>, TurnError>
```

Outcome fields are `scope`, `parent`, `fork_revision`, `author_revision`,
`head_revision`, `created`. Preparation exposes `preview()` as actual Core
AuthorCorrectionPreviewV1 and `preview_bytes()` as its stable held bytes. The
bytes must parse to the exact typed preview; no compact-versus-pretty encoding
is invented. No unaffected Store/job counts are fabricated or tested.

Approved error distinctions frozen here: foreign/cloned/reopened Store plan is
Integrity; a valid changed parent basis/head is Stale; full-input/kind conflicts
and ordinary APIs encountering an author-key occupant are RetryMismatch. Missing
child lookup returns None even without a live original parent; tombstoned child
is Storage(NotFound). True/panicking cancellation returns Engine(Cancelled).
Invalid oversized input and a noncompleted boundary must fail without mutation,
without imposing an additional unallocated specific error mapping.

## What the thirteen cases require

All fixtures use the existing synthetic Lantern Quay Seed, actual Engine,
actual Store operations and rusqlite. There is no accepted-state mock, alternate
evaluator, model or second persistence path. A unique process/time/counter-owned
temporary directory follows existing integration-test conventions.

1. **Atomic creation and reopen.** Actual H=2/f=1 creation retains the root and
   sibling accepted state, advances the new author boundary to 2 without changing
   story time, and adds exactly one local committed author turn, one normalized
   author receipt and zero witnesses. It copies no derived memory/job/packet.
   The small closed index equals actual child/key/f and SHA-256 of the complete
   Core canonical record. Normalization is exact native
   `Serialize(AuthorCorrectionReceiptV1)`, not serialization of an alphabetically
   reordered JSON Value or a fabricated AcceptedEvent. Projection version is 2.
   Preparation is read-only, preview bytes stable, reopen rebuilds the same
   records/basis and accepts the correct projection cache.
2. **Encoded capacity.** Replacement/reason each contain 2,048 control bytes;
   full input demonstrably exceeds 24,576 encoded bytes. It still saves/reopens
   through the small index and single full authoritative response. An actual
   oversized ordinary-request INSERT must fail the unchanged SQL CHECK.
3. **Observed values and A to B to A.** Player/NPC known A survives world B;
   two accepted discoveries update only player B; changing world back to A
   preserves observed B until explicit re-observation. Reopen retains exact
   records/basis and individual event-observed values B/B/A. NPC serialization
   omits private B and author reason.
4. **Owner capability.** Same-file foreign Store, verified backup clone and
   reopened owner reject the old opaque preparation without row changes, despite
   matching source. A freshly prepared token on the actual owner can succeed.
5. **Parent head guard.** An actual accepted parent turn after prepare makes
   application Stale without any child/draft mutation; missing lookup stays None.
6. **Full source guard.** An external synthetic valid Seed replacement preserves
   scope/head and corrected fact value while changing another valid hidden fact.
   Actual Store resume still validates it; the old plan must be Stale, with no
   child/write. This is corruption/replacement testing, never an application SQL
   interface or permission to edit user saves.
7. **Read-only recovery.** Exact full-input lookup returns current child head
   after both parent and child progress. Changed reason, guarded H, valid changed
   f, or replacement is RetryMismatch. The fixture uses H=1/f=0 so f=1 remains
   syntactically valid and tests identity rather than invalid-input precedence.
   A missing child with missing original parent returns None. Every lookup
   leaves all application rows unchanged.
8. **Kind and ordinary key isolation.** Ordinary fork finding an authored child
   and author lookup finding an ordinary child both refuse, even with matching
   parent/fork. An ordinary legacy turn can use the same text as the fixed author
   key. Ordinary begin/status/lookup/cancel on a real local author occupant return
   RetryMismatch and preserve all rows. A different child can use an inherited
   ancestor's key without reserving its namespace.
9. **Cancellation and admission bounds.** True and panicking cancellation at
   prepare/apply create no partial child. Oversized reason, invalid child ID and
   an interior multi-event-turn boundary refuse without writes. No catch or
   assertion weakens the original ordinary multi-event rule.
10. **Actual SQLite rollback boundary.** A synthetic SQLite BEFORE INSERT trigger
    on author normalization raises ABORT. Apply must return the mapped database
    failure and leave every application table unchanged. Drop the fixture
    trigger, verify lookup missing and create from a fresh plan. This is an
    actual SQLite ABORT oracle when executed, not SQLITE_FULL, process death,
    power loss, late-cancel or private production checkpoint evidence.
11. **Adversarial normalized/index data.** Independent fresh fixtures alter
    normalized author time, index f, witnesses, normalized kind, turn kind or an
    unknown wrapper field. The final case also recomputes the index hash over
    the mutated written response so an unchanged checksum is not the only
    defense. Resume and author lookup must fail Integrity without repairing or
    hiding any evidence. Strict full Core reconstruction remains authoritative.
12. **Retired source parent.** An author child created at H=2/f=1 progresses to
    head 3. Retiring its nonroot source parent collects excluded future H and
    leaves only required head 1. Exact child lookup remains read-only and returns
    head 3 before/after reopen, without needing a live parent at original H.
13. **Prebirth lineage and tombstones.** A child rewinding before an authored
    parent's birth remains Domain 1 with original A. Retiring the author parent
    preserves the live prebirth child's source. Retiring/collecting the final
    child reserves deleted identities; lookup returns NotFound and preparation
    cannot resurrect the original fixed authored ID.

The fixed application-row snapshot helper covers schema migrations, story,
branch/entity, canonical turn/event/witness, projection, derived-memory,
retention and job/packet tables. It reads SQL row data for equality; it is not an
alternate replay oracle or a SQLite-file-byte comparison. Actual accepted-state
expectations come from Engine/Store and typed scope/source/boundary assertions.

## Actual static evidence and unrun gates

Actual commands so far:

```text
rustfmt --edition 2021 crates/locallore-storage/tests/m08_author_store.rs
git diff --check
Get-FileHash crates/locallore-storage/tests/m08_author_store.rs -Algorithm SHA256
```

Formatting/parser and whitespace checks passed. Git 2.33.0.windows.2,
PowerShell 7.6.5, rustfmt 1.8.0-stable (01f6ddf758 2026-02-11). Formatting
acceptance is not typechecking: the new APIs are absent at this freeze. No Cargo,
Node, Gradle, SQLite execution, app/WebView, model, device, ADB, CUA, desktop
capture/control, download, protected-resource, setting, PR or merge action ran.

Root's next runnable step is implementing the exact frozen Store/schema port,
then allocating the exclusive verification slot for attributable unchanged tests:

```text
cargo test --locked --offline -p locallore-storage --test m08_author_store --jobs 1
cargo test --locked --offline -p locallore-storage --all-targets --jobs 1
cargo clippy --locked --offline -p locallore-storage --all-targets --all-features --jobs 1 -- -D warnings
```

Use task-owned target/TEMP settings and no downloads. Preserve this source freeze,
actual failures and exact commands/source revisions. Any invalid fixture or
unallocated API correction must be explicit and attributable; do not silently
rewrite assertions to fit implementation.

Root separately owns exact schema 1–4 migration/backup/rollback tests and DDL,
archive 3 and historical archive 1/2 fixtures, combined history/count capacity,
actual SQLite-full and mid-operation/late cancellation checks, Domain 2 proof/job
refusal, coherent generation, consumer/query/compiler/Play 2.5 closure and native
grant/consent/UI/platform integration. These thirteen finite cases cannot close
those gates or prove arbitrary interruption safety. No author wire/UI is exposed,
no human approval is inferred and full M08/D08 remain unchecked. Scoped ownership
is released with the ticket handoff.
