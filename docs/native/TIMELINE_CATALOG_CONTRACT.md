# Timeline catalog v2

Refs #12 (M08.01), supporting M08.05. This exposes existing validated timelines.
The [retention contract](PARENT_RETENTION_CONTRACT.md) adds retired ancestors;
the dated v1 verification remains a historical record of the preceding packet.

`Store::branch_catalog(story, cancel)` reads title, root, sorted timeline
metadata and scoped draft counts in one SQLite read transaction. Each timeline
passes the existing lineage, accepted receipt, ledger and witness replay checks.
The catalog never repairs projections, creates branches, or returns story prose.
Its public result is:

```text
{version:2, story_id, title, root_branch,
 branches:[{scope:{story,branch}, parent_branch, fork_revision, revision, drafts, retired}]}
```

There are at most 256 timelines, depth 32, and a 60 KiB serialized body.
The existing per-lineage replay budgets also apply. Malformed IDs, missing
stories, corrupt history, oversized output and cancellation fail without writes.
Cancellation callbacks are checked between bounded replay operations; there is
no hard CPU deadline or maximum-scale latency qualification.

The trusted Host-v1 command is `branches {story}`. Repository maps the Store
metadata through the Persistence port; the ephemeral host rejects it as
Unsupported. The existing native workspace call carries the response under its
64 KiB bound. Catalog discovery adds no JNI symbol or gameplay privilege.
Host/domain/workspace wire versions stay1; retention uses database schema3 and
archivev2 where retirement metadata exists. No dependency is added.

Android retains the root-only story library and adds a timeline selector for
the selected story. The gateway validates catalog shape, IDs, ordering, graph,
byte/count limits and selected head. Physical retired rows stay in the graph
with original parent/fork metadata and zero drafts. The client validates the
full graph before filtering retired choices. A raced head fails closed. Rust alone
decides inherited receipt eligibility: original ancestor request scopes stay
intact, and Kotlin displays their accepted transcript without rewriting it.
Player scope and revision still match the selected timeline.

Selector callbacks must belong by reference to the current displayed catalog.
Busy work, recovery, archive/deletion overlays and disposal fence selection;
late responses cannot publish into another scene. Opening whole-story deletion
while a child is selected resolves the root scope and current root head.

The Compose sample can select/resume existing timelines and continue using the
fake provider. Individual nonroot retirement has its own explicit preview and
confirmation; whole-story deletion retains its separate root-bound semantics.
No branch creation, rewind or retcon UI is added. Original accepted ancestry
remains privately replayable for retained descendants. See the retention
contract for migration, deleted-ID admission and versioned archive rules.
