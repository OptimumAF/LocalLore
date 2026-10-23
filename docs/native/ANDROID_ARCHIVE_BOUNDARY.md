# Android playable archive boundary

M08.04/.06 bounded Android integration, based on accepted shared archive v1.
The shared Store validator/transaction is the only archive authority. No new
format, gameplay rule, schema, Host command, model or shared Store change.

Implemented for review. See [actual checks and remaining gates](ANDROID_ARCHIVE_VERIFICATION_2026-10-23.md).
Workspace wire contract v1 and database schema v2 are distinct fields; the
gateway checks both independently. No schema migration is introduced here.

## Native interface (frozen for parallel implementation)

JNI class `org.locallore.app.NativeArchive` loads `locallore_android` and exposes:

- `open(database: String, stagingRoot: String): Long` (zero on failure).
- `prepareExport(handle: Long, request: ByteArray): ByteArray`.
- `prepareImport(handle: Long, bytes: ByteArray): ByteArray`.
- `exportBytes(handle: Long, token: Long): ByteArray`.
- `commitImport(handle: Long, token: Long): ByteArray`.
- `cancel(handle: Long)` and `close(handle: Long)` (idempotent).

Public host-test `ArchiveRegistry` equivalents use Path/byte slices/u64 and
Result errors for open/export_bytes, JSON bytes for prepare/commit. The native
module owns all lifecycle state; JNI is only bounded copying/error translation.
No Java references/callbacks/native threads are retained. Control replies are
version1 `{version:1,status:"ok",data:...}` or
`{version:1,status:"rejected",error:<fixed category>}`, at most16KiB.

Export request is strict JSON with exactly story, branch, expected_revision.
The selected branch must be in the coherent exported preview at that revision;
otherwise Stale. Prepare replies have exactly token and preview in data.
Preview is the shared ArchivePreview: version,story_id,title,root_branch,
branch_heads,committed_turns,bytes,payload_sha256,privacy_warning,
noncommitted_workflow_transferred. Render title/warning only as inert text.
Tokens/handles are positive signed-64-bit-safe, monotonically allocated without
reuse; at most four leases, one active operation and one pending capability per
lease. Preparing replacement work invalidates the old pending capability.
Unknown/stale/wrong-kind tokens never consume another pending operation.

Import data is at most32MiB (shared MAX_ARCHIVE_BYTES); exportBytes returns the
unchanged captured archive bytes at most that bound and consumes its capability.
On error JNI exportBytes throws IllegalStateException with only a fixed category,
never an exception/path/SQL string. Other methods return bounded JSON errors.
Commit consumes the exact native ValidatedArchive capability; raw bytes cannot
be substituted by the caller. Success data is exactly root:{story,branch},
branches,committed_turns. Never remap or overwrite an existing story ID.

Before destination import, revalidate exact bytes and import/replay them into a
new separate app-private staging Store, close it and remove only the exact
owned directory/known SQLite files. Any staging/cleanup failure blocks target
import. Never adopt an existing staging directory/leaf. No untrusted title/ID
becomes a path; only internal owner/operation numbers do. App-supplied database
and staging roots are trusted construction, not wire/model/picker data. Android
app-private sandbox is the filesystem boundary; no same-UID/OS-adversary promise.
The concurrent Windows pinned-constructor work is outside this packet.

Cancel invalidates pending capabilities and signals running work without waiting
for its operation lock. Closed handles cannot publish replacement previews or
be reused; running work retains only native owner state until it drains.
Store import's commit is the linearization point: a cancellation/transport loss
may race an already completed import. Reconcile the library; identical retry
is Conflict, not an idempotent successful-import acknowledgement.
Fixed errors: shared ArchiveError plus InvalidHandle,InvalidToken,Stale,Io,
WorkspaceLimit,Internal. Ordinary live-work contention is Busy.

## Kotlin/controller interface

UI agent owns NEW ArchiveController.kt, NativeArchive.kt, ArchiveDocuments.kt,
ui/ArchiveDialog.kt and corresponding NEW JVM tests only. Root owns activity,
ShellViewModel, existing gateway/schema prerequisite and UI entry wiring.

Data types: ArchivePreview mirrors native fields in idiomatic Kotlin;
ArchivePrepared(token:Long,preview:ArchivePreview);
ArchiveImported(story:String,branch:String,branches:Int,committedTurns:Int).
ArchiveGateway has suspend prepareExport(SavedStory),prepareImport(ByteArray),
exportBytes(Long),commitImport(Long), plus nonblocking cancel()/close().
NativeArchiveGateway(Context) uses workspace-v1/stories.sqlite3 and a separate
app-private archive staging root, all blocking work on IO. It owns handle
allocation/terminal disposal and never reopens after close.

ArchiveController(gateway,scope,onClosed:(ArchiveImported?)->Unit) exposes state,
open(SavedStory),prepareExport(),beginImportPicker():Long?,
completeImport(ticket,reader:(suspend()->ByteArray)?),
beginExportPicker():Long?,completeExport(ticket,writer:(suspend(ByteArray)->Unit)?),
confirmImport(),pickerFailed(ticket),cancel(),dismiss(),openImported(),dispose().
Begin methods mint unique picker tickets; only the matching pending callback can
read/write or confirm. Root retains the ticket in the ShellViewModel across
Activity recreation, clears it once on delivery; process death retains no
native capability. Outstanding picker cancellation is tombstoned until its
callback drains, preventing an old callback from attaching to a newer request.
Dismissal cancels and drains active work before onClosed releases the shell
guard. Disposal cancels native work immediately, closes asynchronously and
suppresses every late UI/callback publication. UI agent may propose a minimal
API correction centrally before implementing a conflicting signature.

ArchiveDialog(state, callbacks...) provides menu/preview/confirm/progress/error/
success, explicit full-private warning and same-ID conflict text. No archive is
imported before explicit consent; no export picker before capture/preview consent.
Successful import offers explicit Open imported story or return to library.
Root freezes all story mutation/switch/recovery while archive UI owns its guard,
then refreshes the actual Host library; explicit open creates a fresh session.

Document helpers: readArchiveDocument(ContentResolver,Uri):ByteArray,
writeArchiveDocument(ContentResolver,Uri,ByteArray). OpenDocument reads at most
32MiB plus an overflow probe on IO; no filename/path parsing. CreateDocument
selects a new content URI; writer opens rw without truncation, verifies the
opened descriptor is empty before writing and refuses unverifiable/nonempty
targets. Never delete or truncate a preexisting document. Partial new-document
writes may remain on failure/cancel; UI must say so. Provider/OS stalls have no
hard preemption guarantee. No broad storage permission or persisted URI grant.
Selected providers may sync plaintext exports; no automatic app upload occurs.
