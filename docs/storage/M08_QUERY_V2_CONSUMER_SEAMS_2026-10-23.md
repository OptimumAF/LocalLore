# Future Query2 scoped messages and neutral author markers

Date: 2026-10-23. Refs #12 M08.03 / #30 D08.05 prerequisites.
**SOURCE ONLY, UNCOMPILED / UNRUN. Not the current first-foundation PR.**

Base: `95db6af97107ba52918885759441a9a4eca953b6`. Separate branch
`impl/m08-query-v2-consumer-seams`, worktree `source-query-v2-consumer-seams`.
Claims: [#12 6378440340](https://github.com/OptimumAF/LocalLore/issues/12#issuecomment-6378440340),
[#30 6378440546](https://github.com/OptimumAF/LocalLore/issues/30#issuecomment-6378440546).
Owned existing files: `inspection_query.rs`, `inspection_query_v2.rs` only.
Owned additions: `tests/m08_query_v2_message_identity_review.rs` and this report.
No Host, app, Store, schema, compiler, canonical record, old test, or fixture edits.

## Pre-production source freeze

The coordinator approved these exact choices before production edits:

- Query1 `Row::Message` remains byte-for-byte unchanged. Query2 uses additive
  `Row::ScopedMessage`, serialized kind `scoped_message`, same message fields plus
  mandatory `original_scope` from `receipt.request().scope`. No selected-branch
  relabeling. The internal/public message key retains the chronological sequence
  prefix and includes actual original story, branch, turn and message kind.
- Query2 History alone may emit `Row::AuthorCorrection`. Its serialized form is
  **exactly** `{"kind":"author_correction","revision":N}`. No key, source,
  fact, reason, old/new value, observation origin, or private binding is sent.
- The marker is restricted to literal `Observer::Player`. Character lenses,
  including `Character { id: selected_player }`, and granted Omniscient receive
  no marker. This preserves the earlier contract; the later task's optional
  omniscient recommendation was explicitly declined before test source freeze.
- Existing `Row::key() -> &str` is used by bounded sorting, diff/provenance and
  compiler consumers. To preserve that signature, the Serialize-only marker
  stores `#[serde(skip)] key: String`. This key is derived solely from the
  actual canonical author revision, e.g. the ordinary history sequence namespace
  `["history","00000000000000000001","author_correction"]`. It is neither a
  fake constant key nor accepted caller input, serialized metadata, or authority.
- Markers come from the already reconstructed selected snapshot's retained
  canonical AuthorV1 records. Existing completed `at_revision` boundaries bound
  that prefix before search, counts, sorting and paging. No new range API,
  alternate ledger or author serialization is introduced.

Frozen actual Core oracles precede production in commit
`aa6c73b1d2fad0177c5d05eda41fab74e441e9b4`, six tests, SHA-256
`cfacbd44ee9612a397117d5115844100b0e7be0d105ec62d21c32b04de34e787`:

1. Real ancestor and child dialogue with the same turn key: four scoped messages
   retain actual original receipt scopes/complete event IDs, unique scoped keys,
   one marker, and exact bounded one-row pagination parity.
2. Replay the immutable actual original2.4 receipt with compact SHA
   `38dcf7329addf4ed98fd984cdb9eac95f8d078be03bf4633dd7082d23ac4bc3f`.
   Assert Query1 Message exact literal field bytes and SHA
   `d14be3029e57a13e45293d3264f17ce23f7b6c9370c630d081882928b538a62e`,
   namespace1 cursor and repeat/replay page equality. The latter literal is a
   newly frozen oracle derived from the existing Message field order and the
   immutable receipt, **not** an executed old Query1 capture. Its hash was
   calculated with .NET SHA256 without executing Rust. No old asset is rewritten.
3. An actual author-only interval gives exactly one two-field Player marker;
   Character(player), NPC and Omniscient have zero rows/counts/search results.
   Other views have no marker; canonical bytes and actor context remain equal.
4. Two actual author intervals obey completed historical boundaries, ordinary
   fork prefixes, marker-only search/paging and sibling exclusion. No hidden
   reason, private value, author turn key or truth source enters Player history.
5. Actual mixed public/private Say receipt: whole eligible player narration is
   scoped to both supporting event IDs, but a partially witnessing NPC receives
   only its one eligible event, no prose, marker, private event or hidden count.
   Granted Omniscient has actual events and eligible prose but no marker.
6. Cursor binding rejects changed observer/search/version and stale head.

All fixtures use actual typed Engine prepare/apply/preview/commit/fork/restore
APIs. No fake receipt, canonical SQL write, provider or model is involved. The
new marker is out-of-story presentation, not an actor observation or narrator
event. `CanonicalRecord` stays unchanged. Query2's internal `actor_rows` refuses
History; compiler state selectors cannot receive the marker. Recent policy
transcript construction independently consumes actual actor receipt views,
which have no author records. No generation grant is introduced.

## Review and execution boundary

Source audit found an expected future compatibility change in the existing
`m08_query_v2.rs` test `owning_player_messages_require_actual_whole_receipt_eligibility`:
it matches `Row::Message` and expects total3 after an author correction plus
dialogue. The approved future contract instead produces ScopedMessage and a
Player marker (total4). That old test is untouched in this stack. Root must
claim and freeze a narrow expectation adaptation before broad qualification;
this is a contract change, not evidence of an already executed failure.

No app decoder currently supports these new row kinds; no wire exposure or
feature availability claim follows. Root owns coordinated Host/UI/Android
decoder/renderer/evidence navigation closure. No current first-PR admission,
historical fixtures, canonical history, knowledge or generation policy changes.

No Cargo/Node/Gradle, model/provider, app/native, device/ADB/CUA/desktop, protected
resource, package or settings action is authorized for this packet. Actual
standalone formatting/source checks and final production commit will be recorded
in the handoff addendum. All test behavior and type compatibility remain UNRUN;
unimplemented source tests are not RED evidence.

Next authorized execution is coordinator isolated qualification with a dedicated
D target/TEMP and one heavy job, first the six unchanged new tests, then Query1
and Query2 compatibility/cursors/privacy/compiler tests and strict Core checks.
Preserve first compile/behavior failures before narrow fixes. No task checkbox,
owner approval, model-quality claim, or whole-milestone acceptance is implied.

## Implementation handoff addendum

Production commit `8d46402a444de8feb9c96ed6a2655ba0ae639a57` changes only the two
owned query files, 40 insertions / 1 deletion. The frozen tests and contract above
precede it; none of the six assertions was changed after implementation.

- `inspection_query.rs` SHA-256:
  `3a5caaf78bdfc8eaf6ae761029225f03ae14487c09245747228f2e79ffa45f65`.
- `inspection_query_v2.rs` SHA-256:
  `6cc07cf9166bd9aa4f9d6ec1130a7ccc8482b426cc0f620d4f1b3d3d1342619f`.

`ReadLens` records literal Player selection, so Character(player) cannot gain the
marker by matching the player ID. Only History examines that flag. It iterates
the actual selected snapshot's canonical records and reads only closed record
kind and last revision. Message construction retains the existing whole-receipt
eligibility gate, original input/narration rules, event list and bounded paging;
it changes the V2 row variant, adds actual original_scope, and extends the key.
No Query1 producer, old row fields, cursor binding or search code was edited.

Actual completed commands (not a type-check):

```text
rustfmt --edition 2021 crates/locallore/tests/m08_query_v2_message_identity_review.rs
rustfmt --edition 2021 --config skip_children=true crates/locallore/src/inspection_query.rs crates/locallore/src/inspection_query_v2.rs
rustfmt --edition 2021 --check --config skip_children=true crates/locallore/src/inspection_query.rs crates/locallore/src/inspection_query_v2.rs crates/locallore/tests/m08_query_v2_message_identity_review.rs
git diff --check
```

All completed successfully using installed `rustfmt 1.8.0-stable`
(`01f6ddf758`, 2026-02-11). Source inspection, Git and SHA256 calculation were the
only other verification actions. **Zero tests or builds were executed**; there
is no actual RED/GREEN, native IPC/UI, model, device or performance evidence.

Suggested next coordinator commands, after explicit ownership and resource GO:

```text
cargo test -p locallore --locked --offline --jobs 1 --test m08_query_v2_message_identity_review
cargo test -p locallore --locked --offline --jobs 1 --all-features --test m08_query_v2_message_identity_review
cargo test -p locallore --locked --offline --jobs 1 --all-features --test inspection_query
cargo test -p locallore --locked --offline --jobs 1 --all-features --test m08_query_v2
cargo clippy -p locallore --locked --offline --jobs 1 --all-targets --all-features -- -D warnings
```

The existing Query2 test adaptation described above is a separately claimed
coordinator prerequisite, never an unreported assertion relaxation. Compiler
compatibility should also verify that neither new History-only marker nor its
internal sorting key enters either construction policy or narrator evidence.
Root owns those broad checks and all consumer exposure. This worktree is clean
at handoff; exact task/path claims are released in the issue handoff comments.
