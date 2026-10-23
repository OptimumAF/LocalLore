# Whole-story deletion v1

M08.05's first deletion slice removes an entire story, including every timeline.
It exposes no branch-only operation. Retaining a child while deleting its parent
still requires a separate ancestry/materialization implementation and acceptance.

Deletion is an explicit library action, outside the gameplay/model proposal wire.
The shared Rust Store owns validation and the SQLite transaction. Kotlin displays
the authoritative preview and confirms an opaque native capability. No model,
summary, transcript, filename or title can authorize deletion.

## Preview and confirmation

`Store::prepare_story_deletion(root_scope, expected_revision, cancel)` checks
the root and replays all timelines before returning a non-cloneable,
non-deserializable `PreparedStoryDeletion`. Its serializable v1 preview contains
the title, story/root IDs, every timeline/head, committed/draft/noncommitted turn
counts, derived packet count, exact counts for all nine story-scoped tables, and
a fixed privacy warning. Noncommitted includes drafts. Preview is bounded to
64 KiB and 256 timelines; JNI's wrapped response also has a 64 KiB bound.

The opaque plan retains a distinct read-only SQLite connection without keeping a
read transaction open during consent. Its `PRAGMA data_version` is compared on
that **same observer connection** before/after preview and after the confirming
connection acquires `BEGIN IMMEDIATE`. Commits by the originating Store and
other connections/processes invalidate consent, including same-content
delete/reimport ABA. Unrelated database writes also conservatively invalidate it.
See the official [SQLite data_version semantics](https://www.sqlite.org/pragma.html#pragma_data_version).

The plan binds the canonical database path and detectable file metadata. Its
trust boundary is the existing app-private database and ancestors: these must
not be replaced while Stores are open. This is not a proof against an OS or
same-UID adversary replacing opened files. Foreign databases and detectable
path/metadata drift reject confirmation.

`Store::delete_story(plan, cancel)` consumes the plan even on failure, rechecks
the complete authoritative preview inside the write transaction, and deletes
only the selected story's rows, in dependency order:

1. `derived_memory`, `event_witnesses`, `accepted_events`, `turns`.
2. `branch_projections`, `branch_entities`, `entities`.
3. All target `branches` in one statement, then `stories`.

The existing deferred story/root foreign key permits atomic removal; no schema
migration or cascade is added. Other stories cannot reference the target's
lineage because ancestry keys include story ID. Actual row removals must match
the preview; foreign-key and zero-target-row checks precede commit. Cancellation
and panicking cancellation callbacks roll back before the final commit. SQLite
Busy/Full/integrity/database failures are fixed categories. There is no automatic
retry with consumed consent. See [SQLite foreign keys](https://www.sqlite.org/foreignkeys.html).

## Android ownership and stale work

`NativeArchive.prepareDelete` and `commitDelete` add two bounded JNI calls to
the existing seven archive calls. Handles, one-use owner/kind-bound tokens,
replacement prepares, cancellation generations and draining retired leases use
the existing registry. At most four owners, including draining owners, can
retain observers. Replacing/cancelling/closing a plan drops its connection.
There is no arbitrary SQL/path or story mutation command in the Host wire.

The process's `WorkspaceRegistry` serializes session creation, submit/commit,
resume/open and accepted deletion with a mutation gate. Deletion's transaction
and matching story-session invalidation finish before that gate reopens.
Matching sessions on every native workspace owner for the same canonical
database are removed; their work is cancelled and trace metadata is cleared.
Other story sessions remain available. Monotonic session IDs prevent late work
attaching to a new session. Prepare can run outside the gate to preserve cancel
responsiveness; an old completion can precede invalidation, but cannot commit
through the gate afterward. Separately captured UI snapshots/archive bytes
(including an independent archive owner's prepared export) and other-process
memory are outside this fence. The product UI excludes concurrent archive and
deletion consent; this is not a guarantee of forensic memory scrubbing.

The Kotlin controller confirms only the exact immutable preview object rendered
by the dialog; a retained callback cannot borrow a later story's token. It
consumes consent before IO, disables competing gameplay/archive/library actions,
and waits for actual work to drain on close/cancel. A late cancel can lose an
acknowledgement after commit. Every close therefore reconciles the real library,
even without a success result. Gateway replies must match the selected story,
root/head/title and accepted deletion counts. Unknown exceptions are sanitized.

The product initializes an empty workspace without creating a story. After
last-story deletion and process/owner recreation the library remains empty;
**New story** is an explicit create. Compatibility harnesses can retain their
one-time automatic seed option; reconciliation never uses that option.

## Privacy and limits

Logical deletion removes accepted history, messages/receipts, drafts and other
workflow statuses, projections, entities, and derived caches maintained by this
Store. It does not recursively remove files, delete shared model weights, erase
external exports or OS backups, or promise forensic flash erasure. Explicitly
importing a previously exported archive can restore its history as a new action.
The Android app still uses fake inference; this adds no runtime/model dependency,
network permission or cloud fallback. Desktop deletion UI is not included.
