# M08 canonical-byte accounting frozen oracles — 2026-10-23

Refs #12 (M08.03/M08.06), #29 (D07 compatibility evidence, partial).

Source freeze based on `96ac4ed5ff6bbe09122e124b9162b1dd10542efe`, before
Root's private exact encoded-record-byte accounting optimization. Owned paths:
this new document and `crates/locallore/tests/m08_canonical_budget_review.rs`.
No existing production or test file changes. All new tests are **UNCOMPILED and
UNRUN**; formatting/parser checks do not establish type correctness or acceptance.

## Public-API fixture and frozen expectations

The real budget is 16 MiB across actual serialized canonical records, at most
4,096 records and 65,536 bytes per record. No lowered cap, forged receipt, private
counter access, SQL writer or latency assertion is introduced.

Pure repeated 2,048-backslash Dialogue is not a valid history-byte boundary
fixture: each actual Say appends full text to `Projection.claims`, so the existing
262,144-byte projection guard rejects it before the history-byte guard. Root
explicitly approved the following actual typed-action alternative before freeze:

- Start with valid actual 2,048-backslash and Unicode/escaped spoken Dialogue.
  Preserve the actual Said text and serialize native receipts/records.
- Use a valid synthetic Seed with 64-byte seed/story/branch IDs, normal
  `Engine::new`, unique valid 64-byte turn IDs, and eight actual Wait commands per
  turn. Wait updates only story time and does not accumulate claims. Require each
  actual encoded bulk receipt to exceed 4,096 bytes, proving the byte cap must
  precede the receipt count cap. If that premise fails, the test fails explicitly.
- Independently sum accepted actual serialized records; require the final sum
  to be within the real cap and the next actual preview receipt to cross it.
  Actual commit must return TooLarge without changing full-record SHA-256,
  projection bytes, accepted-history basis or byte sum. Retrying remains rejected.
- Separately freeze the honest escaped-dialogue projection overflow: the rejected
  real receipt would still fit the history-byte budget, all state is unchanged,
  and a subsequent small real Wait remains admissible.
- A small cohort freezes historical fork before a later parent suffix, clone
  independence, ordinary child continuation replay, actual author child plus
  Domain2 typed Play continuation replay, full-record hashes/byte sums/bases,
  idempotent native receipt retry, cancelled author prepare/apply and rejected
  narration followed by a valid append. No cancellation is falsely presented as
  a mutable parent append.

The byte total is derived only from public native record serialization. Full
snapshots are taken at the predicted byte rejection, not on every bulk append.
There is no mirrored implementation counter or machine-dependent timing gate.

## Coordinator execution, still pending

After production implementation, Root may run:

```text
cargo test -p locallore --test m08_canonical_budget_review
```

The large boundary test intentionally was not executed on the known slow
implementation. Root owns all compiler/runtime slots, the existing unchanged
native five-second cancel/resume test, broad compatibility checks and acceptance.
The reported native performance failure is coordinator evidence, not a result
produced by this source-only packet. No model, provider, device, app or desktop
execution was performed here.
