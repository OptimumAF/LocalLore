# Story-record read cancellation

B109; Refs #14 (M10.02), supporting #13 (M09.04/M09.06).

`StoryRecordController` is an owner-thread display adapter. Rust and the existing
reader retain authority over visibility, provenance and canonical history. This
change introduces no query, engine, inference, storage or native ownership API.

A still-current read that ends by cancellation must leave Loading and expose the
existing safe `UNAVAILABLE` problem. A cancelled page keeps its frozen context,
section, search and cursor, with no returned rows. A cancelled event detail keeps
the accepted underlying page and exact eligible event reference, with no event
entry. Cancellation never automatically retries; explicit Retry keeps the same player lens.
Cancellation text, paths and exception payloads never enter displayed state.

The request remains cancelled. Cancellation is neither a successful read nor
proof of native resource closure, rollback, or an unchanged game transaction.
No gameplay command, session, observer change or automatic retry is introduced.

The owned read job is created lazily. Store its identity and register completion
before starting it, so cancellation before dispatcher entry is observed. Check
coroutine activity before calling the reader and immediately after it returns;
a cancelled noncooperative reader cannot publish an otherwise valid response.

Completion handlers may run outside the owner thread. A cancellation handler
only queues a finite, state-only settlement on the inherited owner dispatcher.
Its `NonCancellable` job permits that settlement even if the parent was cancelled
before the read entered. The settlement never reads from the engine or performs
IO. On the owner dispatcher it rechecks disposal, request generation and the
page/detail loading state; pending identity is cleared only for that same job.
Navigation, replacement, Back, dismissal and disposal fence obsolete settlements.

The nine original fake-reader regression methods establish the coroutine/reader
boundary, not a measured native or emulator cancellation defect. Their oracles
cover current page/detail cancellation and exact retry, pre-entry cancellation,
parent/sibling survival, late obsolete cancellation, cancelled owners, and a
cancelled reader returning well-formed data. Actual model/phone/ARM64 and Compose
instrumentation acceptance remain separate gates.

## Rendered event actions

The event detail keeps one view identity from open through loading, completion,
and Retry. Back can close that view after its result settles. It refuses a
callback from an earlier open, even when the current event has the same
reference and story context.

Each read within the view has its own identity. Retry accepts only the
currently rendered failure. If a retry immediately returns the same error,
the new result still reaches the screen so the player can retry it again.
The existing cancellation path preserves both identities when settling the
current read. The request continues to use the existing player-visible lens.
