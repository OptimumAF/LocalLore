# Independent mixed Store source audit

2026-10-23. Refs #12 M08.03 / #30 D08.05. **Source findings and frozen
unexecuted regressions only.** No Store behavior, migration or durability pass is
claimed here. Archive 3 and Host/domain2 consumer closure remain pending;
application author wire is unavailable.

## Attribution and ownership

Reviewed exact production `65304a34f4c216a93dde0270a3c6b682e68bee64`, schema 5
DDL `2fca290b7b69abf765cdc736ab816b839ca02d57`, reconciled contract `1c0b090`,
and unchanged thirteen actual-Store oracles `92255d2` / report `5561cf7`.
Read the full new Store author module and mixed turns/branches/lib/retention/
memory/coverage/archive changes against actual old source. Existing ownership
and prerequisites follow AGENTS and prior scoped claim/read handoffs.

Root allocated only TWO NEW paths on separate `review/m08-author-store-source` /
`source-author-store-source-review` from `65304a3`:

- `docs/storage/M08_AUTHOR_STORE_SOURCE_REVIEW_2026-10-23.md`
- `crates/locallore-storage/tests/m08_author_store_review.rs`

Claims #12 `6377499779` / #30 `6377499975` preceded writes. No existing
production, migrations, DDL, frozen thirteen tests, Core or Host file changed.
Resource agent owns the compiler slot; no heavy execution was granted.

## Concrete production findings

### Ordinary lookup decodes the author index before checking kind

At reviewed `turns.rs::lookup_turn`, the SQL reads only request_json and then
decodes it as ordinary Request. The new compact author index is deliberately not
a Request. A valid author occupant therefore returns Integrity before reaching
recorded()'s author-kind guard, whereas the agreed closed ordinary-API result is
RetryMismatch without writes.

This failure path is already asserted by the unchanged thirteen-case packet's
`symmetric_child_kind_and_ordinary_author_key_occupants_fail_without_writes`.
No duplicate new author implementation or test was needed. Root confirmed the
source finding and agreed to preserve production `65304a3` for attributable
unchanged execution before a narrow discriminator correction. It is a concrete
source-established defect, **not an executed RED result in this review**.

### Historical ordinary status/lookup/drafts query a nonexistent schema 5 column

`turns.rs::recorded` now unconditionally SELECTs canonical_kind. Versions 1–4 do
not have that column. They are still admitted by Store::open_read_only and the
new read_history/verify_ledger correctly dispatch their old shape. Thus ordinary
read-only turn_status, lookup_turn and drafts fail when they reach recorded(),
despite a validated old canonical history. A schema migration must not be
required merely to recover/read an existing supported historical turn.

Root confirmed both findings and selected the same version-dispatched
discriminator helper for the future repair. No correction is present in this
branch. The new review tests freeze the old-schema read behavior independently.

## Additional qualification fixture seam

The existing private `turns/storage_pressure.rs` fixture's probe INSERT still
uses six positional values for accepted_events. Schema 5 adds record_kind,
making seven columns. That fixture would fail on arity before exercising its
established SQLite-full boundary. This is a test-fixture schema adaptation seam,
not a newly demonstrated canonical production-authority defect. Root should
retain any actual failure and make an explicit fixture-only column-list repair
while preserving the pressure assertions. This reviewer did not alter or run it.

## New frozen historical regression cases

NEW source `m08_author_store_review.rs` is frozen before repair at
`261e24a6b43de8693aff0e4e9169e54887cb37d9`, SHA-256
`64f3e6b6d9f1b4cb82e54127a24e76eabf270b123a5ece250a1fc52a821393eb`.
All three tests are **uncompiled/unrun**:

1. Completed ordinary turn_status returns original Request/Receipt/Committed.
2. Completed ordinary lookup returns original Request/Receipt/Committed.
3. Interrupted ordinary draft status, lookup and drafts listing preserve exact
   original request, Draft phase and absence of a receipt.

Each case loops actual known versions 1–4, including the requested focused
schema4 regression. Fixtures execute the unchanged historical migration SQL
1 through the selected version into fresh synthetic databases, retain the real
application ID/user_version and exact schema/contract constraints, and populate
only an actual Core-generated ordinary Receipt/events/witnesses/projection plus
one draft. FKs are enabled and checked. This fixture SQL is not an application
port or alternate engine; canonical expected results come from actual Core.

Each real Store::open_read_only first must verify the historical schema and
resume exactly the Core source basis, then exercise the ordinary public read.
The complete SQLite main-file bytes must remain unchanged after close. There is
no historical fixture downgrade using altered schema5 definitions, no migration
backup omission excused by a write, and no expected-error relaxation.

## Bounded audit observations and limits

No additional concrete production defect was established in this source audit.
The following observations remain subject to actual verification:

- One existing turns.response_json contains each full Core canonical record.
  The small author index regenerates from that complete record/hash and SQL
  scope/key/f. Author normalization compares exact private author receipt bytes,
  original sequence/key/version/kind and zero witnesses. Ordinary PlayV2 compares
  private binding wrapper bytes while normalizing only actual public events.
- The opaque preparation's Arc identity is held alongside the exact Core plan,
  parent basis and preview bytes. Same-source Store reopen/foreign owners cannot
  substitute for its native owner. The token derives Clone, but a clone retains
  the same owner and fixed complete input; it does not bypass owner/basis checks
  or allocate another child identity. No Deserialize/public constructor is added.
- Fresh application reads/checks actual source in one IMMEDIATE transaction,
  compares actual preview, uses transaction-local child insertion, writes author
  row/index/normalization/projection and replays the actual transactional bytes
  and Store accounting before commit. Exact existing outcome recovery is read-only
  and deliberately precedes fresh parent-head guards. Cancellation checks remain
  before commit; no post-commit cancellation result relabels saved success.
- Child insertion rechecks actual branch capacity/depth and retention admission.
  Recovery loads active child/retained ancestry rather than live original H.
  Ordinary fork retry explicitly refuses an actual local author creation record;
  an inherited ancestor author key does not become a local ordinary-key occupant.
- Schema5 DDL is additive for canonical table discriminators and rebuilds only
  the projection cache table; old migration versions/contract text remain fixed.
  Known-version migration, consistent backup, exact schema checks and atomic
  rollback still need actual source-attributed tests, not inference from SQL text.
- Retention fingerprint now includes complete canonical records. Existing birth
  floors/cap deletion rules are retained. Domain2 old proof/job source hashing
  refuses Unsupported; coherent context snapshot returns actual Engine plus raw
  Unsupported fallback. New author children copy no old derivatives.
- Current mixed archive export fails Unsupported rather than silently dropping
  author records. Existing Domain1 archive2 known-source range now includes5.
  Full private archive3 round trip remains unimplemented and cannot be claimed.

This finite audit does not cover all mutation/error schedules, resource limits,
power loss, allocation/latency, native grant/second-consent lifecycle or app
privacy decoders. Core/Store capability source is not a renderer permission.

## Actual checks and handoff

Actual reviewer commands only:

```text
rustfmt --edition 2021 crates/locallore-storage/tests/m08_author_store_review.rs
git diff --check
Get-FileHash crates/locallore-storage/tests/m08_author_store_review.rs -Algorithm SHA256
```

Formatting/parser and whitespace checks passed. Git 2.33.0.windows.2,
PowerShell 7.6.5, rustfmt 1.8.0-stable (01f6ddf758 2026-02-11). No Cargo,
Node, Gradle, SQLite execution, model, app/WebView, device, ADB, CUA, desktop
control/capture, protected-resource, download, setting, PR or merge operation ran.

After explicit heavy-slot allocation, Root should execute the unchanged thirteen
and these three new cases against preserved `65304a3`, retain every actual
failure, then make the agreed narrow version-dispatched kind/read repair and
rerun unchanged assertions:

```text
cargo test --locked --offline -p locallore-storage --test m08_author_store --test m08_author_store_review --jobs 1
```

Actual schema migration/backup/rollback, SQLite-full/cancellation boundaries,
complete old/current Store suites and strict checks remain separate. Do not
present a source finding or missing-column inference as an executed failure.
Root owns all fixes, integration and evidence reconciliation. Scoped claims are
released with the ticket handoff; no score, human approval or M08/D08 gate closes.
