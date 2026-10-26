# Parent retirement and retained timelines

Refs #12 (M08.05, supporting M08.01/M08.04/M08.06). Implemented in the shared
Store, Host/native adapter and Android shell; owner acceptance remains pending
on the ticket. See [ADR-0009](../adr/0009-retained-parent-deletion.md).

## Canonical ownership and migration

Schema3 adds `branch_retention(story_id, branch_id)`. A row reserves and retires
the ID even after its physical branch is collected. It references the story,
not the physical branch. Absence means active when the physical branch exists.
Accepted events, receipt scopes and world/observer semantics are unchanged.

New databases initialize all migrations atomically. An exact owned schema1/2
requires a consistent, create-only backup before an IMMEDIATE migration and
exact schema/version verification. WAL content is included. Application open
chooses a unique sibling backup. Read-only historical schema1/2 opens verify
without migration. Existing backups are never overwritten, unknown/future
schemas are refused, and failed migrations roll back. No automatic downgrade
or destructive restore is provided. Retain private backups until owner acceptance.

## Store preview and accepted deletion

`prepare_branch_deletion(scope, expected_revision, cancel)` returns an opaque
prepared capability. Its previewv1 contains the exact scope/title/root/head,
active retained descendants, changed retained heads, sorted physically removed
branches, seven fixed branch-table row counts, committed/noncommitted turn
counts and the privacy notice. Root targets are refused; use whole-story
deletion. A stale head, corrupt graph/history or cancellation grants no capability.

`delete_branch(prepared, cancel)` consumes that exact capability. Consent is
bound to database identity, file/data-version observation and revalidated
preview. It retires the target and computes the required completed-event prefix
from its birth fork and retained direct-child fork points. Nested rewinds before
the parent's birth remain valid. Unreachable target-local tail, every target
noncommitted workflow and derived projection/cache are removed. Original required
receipt/event/witness prefixes remain; no consequential fact is copied or rescoped.

Retired physical leaves and unneeded retired ancestors are collected child-first.
Their reserved IDs remain. Physical and reserved branch IDs together are bounded
at256, with existing depth32/per-lineage budgets. New forks and matching-child
retries cannot reuse a retired ID or use a retired parent. Retained active
children/siblings are replayed and compared to their original canonical bytes
and receipts. SQL errors, cancellation and panics before commit roll back; exact
row counts and foreign keys are checked before commit.

The accepted result contains scope, optional retained-through revision, collected
branch/deleted-turn counts and sorted invalidated IDs. Public Store/Host access
to retired targets fails even for exact old committed/Ready retries. Only private
ancestry replay may read retained retired prefixes for active descendants.

Whole-story preview is nowv2 with ten fixed tables, including tombstones. Its
transaction removes the entire story and reserved IDs. Android still decodes
historical previewv1 with nine tables; it never guesses unknown versions.

## Narrow native and Android boundary

The existing archive owner gains `prepareBranchDelete` and `commitBranchDelete`;
there are eleven archive JNI exports. Requests are exact story/branch/head
metadata; no SQL or arbitrary path enters the command. Tokens are one-use,
owner/kind/generation-bound and cancelled by the existing cancellation operation.
The native response remains capped at64KiB. SQLite work and JNI run off the UI
thread. Engine rules remain in Rust.

Deletion shares the workspace mutation gate with submit, commit, resume and
session creation. The Store commits first; then matching database owners evict
and cancel only invalidated branch sessions before the gate opens. Their trace
owners are cleared. Active retained child/sibling sessions remain valid,
including in-flight generation. Generation runs outside the mutation gate and
completion cannot restore an invalidated session. Cross-process deletion also
fails public scope admission before a cached response; this does not promise
immediate scrubbing of every other process's memory.

Compose offers **Delete timeline** only for a selected nonroot timeline. It
captures exact displayed scope/head/title, freezes preview collections, fences
input, records, selectors and archive operations, and confirms only the captured
capability. Cancel/close never silently confirm. Late callbacks and disposal
cannot publish into another scene. After close/failure it reconciles saved state;
an uncertain completion tells the user to verify the library. **Delete story**
remains a separate root-bound operation. No branch creation/retcon UI is added.

Catalogv2 includes every physical row with a required Boolean `retired`, retaining
original parent/fork metadata. Clients validate the entire graph first and only
then filter retired choices. A child remains attached to its actual parent;
retired ancestors are not silently reparented. Host/domain/workspace wire
versions remain1; database schema is3.

## Portable state

Ordinary Domain1 play history exports archivev1 without retirement state and
archivev2 with retirement state. Both record the actual source database schema,
currently schema5; a current-schema database alone does not select archivev3.
Historical v1 schema1/2 fixtures remain readable and retain their original bytes.
Their current-schema re-exports differ only in source-schema metadata and its
dependent payload checksum in the compatibility tests, which validate both full
archives before normalizing that single metadata field.

For ordinary Domain1 play history, retirement requires archivev2 and a nonempty sorted unique
`retired_branch_ids` field. It includes physically collected IDs. V1 rejects that
field, even null; v2 accepts source schemas3 through5. Physical archive branches stay
bounded at32 and physical/reserved union at256. A retired root, orphan/retired
leaf, excess retained tail, reused ID or invalid fork/completed-event boundary
is refused. Required retired prefixes replay internally with original scopes;
retired derived projections are not imported. Tombstones and history import in
the same transaction. Active accelerators remain validated. Import staging does
not publicly resume a retired target.

An unchanged v2 roundtrip preserves canonical hashes, knowledge and retirement
state. Checksums do not authenticate an author: a deliberately rewritten,
otherwise valid archive may recompute them. V2 adds no signatures or model data.

Mixed play and author-correction history selects archivev3: exactly Domain2,
source schema5 and transcript `accepted_canonical_records_v2`, using
`local_records` and `records_sha256` instead of the v1/v2 receipt fields. V3
requires the sorted unique `retired_branch_ids` array but permits it to be empty.
These distinct field sets remain closed; relabelling v1/v2 content as v3 does not
grant import. Canonical replay invokes no inference.

The current rules are implemented in
[`playable_archive.rs`](../../crates/locallore-storage/src/playable_archive.rs).
Store/Core coverage includes
[`branch_retention_archive`](../../crates/locallore-storage/tests/branch_retention_archive.rs),
[`m08_archive3`](../../crates/locallore-storage/tests/m08_archive3.rs) and
[`m08_archive3_hostile`](../../crates/locallore-storage/tests/m08_archive3_hostile.rs).

## Privacy and qualification

Logical deletion is not forensic erasure of SQLite free pages, flash storage,
OS/VM copies, migration backups or external exports. Retained children still
need their inherited accepted content. The preview explains this before consent.
No upload or automatic cloud fallback is added. Current playback uses the
explicit synthetic provider; this packet selects no production model/runtime.

Cancellation checks occur between replay operations. No hard catalog/deletion
CPU deadline or maximum-history latency is qualified. Host tests, Android
cross-builds and x86_64 emulator execution are distinct evidence; none qualifies
ARM64 execution, a physical phone, thermal behavior or real-model quality.
