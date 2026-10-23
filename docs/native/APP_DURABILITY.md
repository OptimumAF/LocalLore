# Android shared save and resume

The production Android app constructs `DurableGateway` with
`NativeWorkspaceTransport`. The JNI `WorkspaceRegistry` opens the same
`locallore-workspace` adapter used by desktop. That adapter owns the shared
SQLite storage implementation and returns the shared `locallore::host::Host`.
Kotlin contains no SQL, gameplay reducer, replay implementation, or second
canonical transcript.

The native app chooses `noBackupFilesDir/workspace-v1/stories.sqlite3`.
The actual canonical database path, schema version 1, engine rules profile,
story/branch scope and accepted head revision appear in the app.
No path or model handle is accepted through the Host wire protocol. Native
workspace opening fails explicitly; the app never silently falls back to an
in-memory game or resets an unreadable database. The existing backup exclusions
remain configured. These settings are not a measurement of OS backup behavior.

Startup resumes the default saved story in deterministic story-ID order. This
is not a most-recently-used promise. **Saved stories** selects another story.
**New story** creates a separate saved story and keeps every earlier entry.
Closing a native owner releases its sessions without deleting the database.
Reopening loads validated canonical history and replays recorded receipts,
without calling an inference provider. The transcript is rendered from the
observer-filtered player snapshot's finalized receipts, capped to the latest
40 displayed messages. The app labels fake inference explicitly.

Uncommitted response drafts remain separate from accepted history. The library
reports their count; resume does not regenerate, apply, erase, or assume
ownership of another instance's draft. This slice does not persist an unsent
composer or provide arbitrary draft adoption/deletion controls. Live pending
requests retain their original scope, request, mode and turn key. Lost submit
or commit acknowledgements are reconciled with that key. **Recover saved
progress** may finish the original prepared turn; once cancellation was
requested, recovery instead retries cancellation and reconciles any commit
that already won. A fresh retry never silently substitutes a new key for an
uncertain commit.

All file opening, SQLite work, replay and JNI calls run on Kotlin IO workers.
Prepare/generation bypasses the adapter's short control gate. The shared Host
validates its completion against the current session and cancellation state;
generation holds neither the canonical lock nor a SQLite transaction.
Native close removes the handle, permanently closes its app lease under the
control gate, and cancels the Host's owned sessions. A retained pre-close lease
cannot create new sessions. Kotlin cleanup has an adapter-owned IO scope so
ViewModel scope cancellation cannot discard native release. ViewModel
generation checks prevent late init/prepare/commit/snapshot results from
publishing after cancellation, switching or disposal.

Diagnostic consent, preview, sanitization and explicit export remain separate.
The displayed storage path and story text do not enter diagnostic records.
No new Android permission, hosted dependency during play, model download,
telemetry, or remote database is introduced. SQLite's bundled C source is now
cross-compiled with the pinned NDK clang/llvm-ar and API-26 sysroot; compiler
flags preserve spaces and apostrophes in SDK paths.

## Verification boundaries

`cargo test -p locallore-android --locked --offline` exercises actual synthetic
SQLite files through the native workspace adapter, including reopen equality,
receipt lookup, retry-safe commit, independent stories, cancelled draft
exclusion, bounds, foreign scope, closed handles and retained lease disposal.
Existing in-memory JNI/Registry tests remain legacy boundary fixtures; the
production Activity does not construct their gateway.

`DurableShellTest` is a pure JVM controller suite covering saved transcript
restoration, authoritative snapshot publication, new/resume library behavior,
unknown commit recovery, cancellation reconciliation and disposal. These tests
do not substitute for SQLite or JNI execution.

`DurableNativeTest` contains actual JNI/SQLite instrumentation for native owner
close/reopen, transcript restoration, story isolation, lost commit replies,
cancellation, cancelled-recovery intent and replacement-turn fencing. Building
the test APK checks its compilation; it does not establish that the tests ran
on a device. Activity recreation tests likewise do not establish OS process-kill
or physical-device qualification. For this change, connected tests, ADB,
emulators, runtime-control worktrees, installed models and desktop control are
outside the authorized verification surface. The PR records the exact checks
actually run and the remaining integration limits.
