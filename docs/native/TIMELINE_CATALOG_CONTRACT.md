# Timeline catalog v1

Refs #12 (M08.01), supporting M08.05. This prerequisite exposes existing
validated timelines; branch retirement/deletion remains a separate operation.

`Store::branch_catalog(story, cancel)` reads title, root, sorted timeline
metadata and scoped draft counts in one SQLite read transaction. Each timeline
passes the existing lineage, accepted receipt, ledger and witness replay checks.
The catalog never repairs projections, creates branches, or returns story prose.
Its public result is:

```text
{version:1, story_id, title, root_branch,
 branches:[{scope:{story,branch}, parent_branch, fork_revision, revision, drafts}]}
```

There are at most 256 timelines, depth 32, and a 60 KiB serialized body.
The existing per-lineage replay budgets also apply. Malformed IDs, missing
stories, corrupt history, oversized output and cancellation fail without writes.
Cancellation callbacks are checked between bounded replay operations; there is
no hard CPU deadline or maximum-scale latency qualification.

The trusted Host-v1 command is `branches {story}`. Repository maps the Store
metadata through the Persistence port; the ephemeral host rejects it as
Unsupported. The existing native workspace call carries the response under its
64 KiB bound. No new JNI symbol, database migration, dependency, or archive
version is introduced. Host/domain/workspace wire versions stay 1; database
schema stays 2. Catalog discovery confers no author or gameplay privilege.

Android retains the root-only story library and adds a timeline selector for
the selected story. The gateway validates catalog shape, IDs, ordering, graph,
byte/count limits and selected head. A raced head fails closed. Rust alone
decides inherited receipt eligibility: original ancestor request scopes stay
intact, and Kotlin displays their accepted transcript without rewriting it.
Player scope and revision still match the selected timeline.

Selector callbacks must belong by reference to the current displayed catalog.
Busy work, recovery, archive/deletion overlays and disposal fence selection;
late responses cannot publish into another scene. Opening whole-story deletion
while a child is selected resolves the root scope and current root head.

The Compose sample can select/resume existing timelines and continue using the
fake provider. It does not provide a branch creation, rewind, retcon, retirement
or branch-only deletion UI. Whole-story deletion retains its prior semantics.

Parent deletion needs a separate safely backed-up schema migration and
versioned retirement metadata in archives, so importing cannot resurrect a
retired playable parent. Original accepted ancestry must remain available to
retained descendants. These dependencies preserve M08.05 acceptance criteria;
this catalog is not a leaf-only deletion substitute.
