# M08 desktop schema5 metadata frozen oracles — 2026-10-23

Source-only partial #12 M08.06 / supporting #8 M04.06 handoff. No acceptance,
model/device, native IPC, rendering, or full Domain2 UI result is claimed.

## Frozen packet

- Base: `29e24efdc3d85e114a5bf7edea5174a8075f2698`, coordinator integration
  including accepted main `cf93327` and schema5 Store/typed legacy Host closure.
- Isolated branch/worktree: `review/m08-desktop-schema5` /
  `source-desktop-schema5-review`.
- Test freeze: `22529f5ee7dbed866f22d13979373c81e852c219`.
- Only new test path:
  `apps/desktop/src-tauri/src/m08_storage_metadata_review.rs`.
- SHA256:
  `2b7a3729c82f8b60809643c0ba7f4acc08214cf7ded897e3c90fee0545efd4f2`.
- Claims before edits: [#12](https://github.com/OptimumAF/LocalLore/issues/12#issuecomment-6377911730),
  [#8](https://github.com/OptimumAF/LocalLore/issues/8#issuecomment-6377911965).
- Reviewer owns only the new test file and this new document. Coordinator owns
  existing production, test registration, existing assertion modernization,
  execution, and integration. Existing sources/assertions/dependencies remain
  unchanged in this packet.

## Actual boundary and deferred registration

The desktop package is binary-only at this base. There is no library exposing
`export_commands`, and its `storage_metadata` helper is private. An external
integration test cannot import the actual helper. The approved fallback is a
new test module registered **inside `export_commands.rs`** by the coordinator:

```rust
#[cfg(test)]
#[path = "m08_storage_metadata_review.rs"]
mod m08_storage_metadata_review;
```

The module uses `super::storage_metadata`; no privacy widening, wrapper
implementation, duplicate validator, or new production endpoint is necessary.
Registration is deliberately not part of this reviewer's two-new-path packet.
Until registration, Cargo does not discover this source. Standalone rustfmt is
only a syntax/format check, not typechecking.

The production `inspection_storage` command captures a window lease, obtains
the actual workspace Host, calls protocol1 `workspace`, and feeds that reply to
`storage_metadata`. Each new test creates its own bounded synthetic temp
database through `Store::open_application`, confirms physical schema5 through
`Store::info`, opens the real `locallore_workspace::open` Host, and obtains an
actual protocol1/schema5 workspace reply. Tests call the **same production
helper** used by the command. They do not construct a window, run the async
native command/IPC transport, launch WebView2, or capture any desktop content.
No fake persistence or provider is used. The guard deletes only its newly
created temp directory after its owners drop.

## Five frozen tests

| Test | Required behavior |
| --- | --- |
| `actual_store_schema5_host_protocol1_passes_same_native_metadata_admission` | Actual schema5 Store/Host reply is accepted by the native metadata helper. Physical schema5 is displayed truthfully, location is retained, metadata remains read-only, cleanup report passes through, and the existing metadata-only notice remains. |
| `known_database1_through4_metadata_remains_compatible_with_protocol1` | All previously admitted database versions1–4 retain the same helper contract under workspace protocol1. |
| `future6_and_malformed_database_versions_are_closed_wire_refusals` | Database6, zero, oversized/negative/fractional/string/null/object/array versions and missing version receive `Wire`. |
| `database5_never_substitutes_for_workspace_protocol1` | Database5 cannot admit an incompatible, missing, string, or null workspace protocol version. |
| `actual_host_protocol_refusal_survives_native_metadata_adapter` | Actual Host envelope-version2 refusal remains typed `Version` through the helper; a subsequent actual workspace call still succeeds. |

The known-old and malformed/future variants change only the relevant metadata
field in a real reply. They are explicit synthetic transport counterexamples,
not claims that the current Store wrote/opened a historical/future schema.
Protocol1, physical database5, and domain contracts remain separate axes.

## Concrete source findings and minimum coordinator changes

At the frozen base:

- `src-tauri/src/export_commands.rs:268` validates workspace protocol1 and
  admits only `Some(1..=4)` physical database metadata. Actual current schema5
  therefore reaches `Wire` in this helper. The scoped production change is
  bounded known versions `Some(1..=5)`, retaining protocol1 and existing error
  propagation. Do not replace this with unbounded future-version acceptance.
- Its existing `storage_metadata_tests` explicitly expects database5 to fail.
  That allocated assertion must explicitly become a database6 refusal. Keep
  every previous known1–4 admission and missing-field assertion; add5 as
  current positive metadata. Record this as current-version expectation
  modernization, not unchanged historical acceptance evidence.
- `ui/controller.ts:405` `library()` admits the actual workspace protocol1
  without an exact database4 gate. `revealStorage()` at line386 calls the
  native metadata command. No new frontend transport or persistence logic is
  needed for this specific metadata compatibility fix.
- `ui/App.tsx:242` displays the actual workspace database version dynamically.
  It does not hardcode4. Its storage details consume the native helper output.
- The **current-target** migration UI oracle is stale:
  `ui/legacy-journeys.ts:92` checks database4 and its check label says db4;
  line160 requires rendered `SQLite schema 4 | Workspace contract 1 | Domain
  contract domain-v1`. Current migration-target checks/labels must become5,
  preserving protocol1, Domain1, exact original receipt/state, retries,
  observer isolation, and no-mutation assertions unchanged.
- `legacy-harness.mjs:154` requires `verified.live.schema_version === 4`, and
  line170 labels the current migration as v1-to-v4. These current-target
  expectations/labels must become5. Its backup expectation remains schema1;
  canonical/receipt hashes, revision1, receipt count1, read-only nonmutation,
  exactly one backup, unchanged backup bytes, and reopen/restart equality must
  stay intact.
- `crates/locallore-storage/examples/native_legacy_workspace.rs:128` already
  verifies live `SCHEMA_VERSION` and discovers its backup via the corresponding
  `before-v{SCHEMA_VERSION}` prefix. Its historical source/backup stays1. It
  does not need a blind hardcoded4→5 replacement.

These are source predictions, not actual failed execution records. Historical
schema1 source, existing immutable archive/device fixtures, accepted old
captures, and calibrated schema4 capacity artifacts must not be rewritten to
claim schema5 execution. A current native migration rerun must retain new,
separately identified artifacts. This packet does not own any existing harness
or native production changes.

## Checks and next runnable commands

Actually run by this reviewer:

```text
rustfmt --edition 2021 apps/desktop/src-tauri/src/m08_storage_metadata_review.rs
git diff --check
```

Both succeeded. Source/Git inspection and source SHA256 were collected. No
Cargo, Node, Gradle, SQLite execution, native app, WebView, Android gateway,
model/device, or computer-use action was run. All five tests are
**UNCOMPILED / UNRUN**, with private-module registration still pending.

Coordinator next registers the unchanged frozen child module, then runs it
against unchanged production to collect actual RED before modifying admission:

```text
cargo test --locked --manifest-path apps/desktop/src-tauri/Cargo.toml --bin locallore-desktop-spike m08_storage_metadata_review -- --nocapture
```

Then apply the bounded production/allocated existing-negative correction and
run the unchanged new tests, existing metadata tests, normal frontend checks,
and current schema5 native legacy migration harness under separately allocated
execution. The current reproducible harness entry point is:

```text
node apps/desktop/legacy-harness.mjs
```

The harness builds native dependencies and launches an application-owned test
WebView; it is not authorized for this source-only reviewer. The coordinator
must record exact environment versions, command outcomes and app-owned render
inspection, and distinguish those actual results from these helper tests. No
native execution success is inferred from the source freeze.
