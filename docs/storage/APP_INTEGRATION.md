# Application save and resume

The desktop and Android shells use `locallore-workspace::open` and the same
`locallore-storage` owner. Each application has a local SQLite database. Shared
means shared implementation and contracts, not cross-device synchronization.
Ordinary receipt contract1 keeps its original bytes. The current Store uses
SQLite schema5 for one mixed canonical ledger: legacy receipts, generated
Domain2 play and explicit author records. Schema5 also preserves bounded
derived memory, retained-branch metadata and restart-safe derived work. It adds
no model dependency or second persistence owner. Author preparation/application
is currently a native shared-Core/Store interface, not an exposed app action.

Native startup chooses a private directory outside the source tree. Desktop uses
Tauri's application-local data directory with `stories-v1.sqlite`; Android uses
`Context.noBackupFilesDir/workspace-v1/stories.sqlite3`. Directory creation and
all Host/database calls run on background workers. The UI shows the actual
location, schema/rules versions and selected story/branch/head. These directories
do not protect against a compromised OS, user backups or explicit file copying.

Before an exact owned old database is upgraded, the private factory makes a new
consistent, fsynced sibling backup named `.before-v5-<unique>.sqlite`. It never
overwrites, deletes or automatically restores the backup. Backup/schema/space
failures prevent migration and surface through the existing fixed error path.
These retained plaintext backups contain private stories and drafts. Foreign or
altered databases are refused before backup/migration. Historical schema1/2/3/4
remain verifiable through the owner's read-only API.

Host `workspace.schema_version` remains the compatible workspace contract1 used
by existing desktop/Android clients. Additive `database_schema_version` reports
the actual SQLite version5 separately. Native storage inspection and database-
copy manifests use that actual version. Canonical readable inspection bundles
keep their distinct export schema1; they are not SQLite schemas or playable
archives. Normal non-database exports omit the derived cache.

The [schema4 job protocol](M07_DURABLE_JOBS_2026-10-23.md) adds no automatic
background maintenance or inference. Current deletion previews use branch
version2 and story version3 to include the new derived row counts in explicit
consent. Android keeps exact historical preview key sets and rejects unknown
versions or inconsistent counts. The workspace wire contract remains1.

Current generated Play2.5 uses compiler2 and an explicit context policy. Core
stages the actual turn and supplies narration only its sanitized outcomes and
new observations; private author reason and earlier knowledge do not enter
that narrator request. Original Play2.1–2.4 records retain strict history-only
replay. Existing legacy app PlaySnapshot/omniscient Inspect and Query1 refuse
Domain2 with a typed error until their V2 views are integrated. Archive1/2 also
refuse mixed Domain2 export until explicit Archive3 support. Memory jobs and
old coverage proofs return Unsupported there. These refusals do not mean
durable correction UI or complete Domain2 app resume is available.

The bounded `workspace` operation returns metadata for up to 256 stories in
deterministic story-ID order. Startup resumes the first entry, or creates a new
opaque story identity when empty. The library permits explicit selection; this
order does not imply last-used or newest. New/reset preserves previous saves.
Closing a session preserves its story. Android exposes separately previewed,
explicitly confirmed whole-story deletion and nonroot timeline retirement; see
the [retention contract](../native/PARENT_RETENTION_CONTRACT.md).

`Host::with_persistence` accepts a trusted storage port; wire requests cannot
choose file paths, issue SQL or install providers. Submitted requests and
committed receipts use the existing atomic/idempotent store operations.
Generation runs outside the owner lock and any database transaction. Completion
reconciles persisted turn status before publishing a worker result. Observing a
terminal outcome or submitting/resuming refreshes the local engine from validated
storage, including changes made by another process. The store resolves competing
commits and cancellations. Story allocation checks its cap inside the writer
transaction. It never overwrites an existing save.

A reopened story restores accepted transcript and player state from recorded
receipts. It does not generate narration during replay. Previously submitted,
uncommitted drafts are counted visibly and never automatically committed or
cancelled on resume: another live owner could still be processing them. Unsent
composer text for saved stories uses one bounded Android saved-instance UI record,
separate from submitted drafts. It restores only for the exact resolved story and
branch, stays hidden while opening/recovery is unresolved, and is discarded when
a different scope settles. Revision changes retain it; restoration never submits
or resumes provider work. This is not a promise of retention after task dismissal,
force-stop or a cold launch. See [Android draft lifecycle evidence](../native/ANDROID_INPUT_DRAFT_VERIFICATION_2026-10-25.md).
Retrying an uncertain outcome retains its original
request key and looks up the recorded result before applying effects again.
Request keys created by the apps are distinct across process restarts.

Unopenable, foreign, corrupt or incompatible databases and bounded storage errors
surface visibly. Production startup has no silent memory fallback. Full-disk and
commit-stage failures are tested at the storage boundary; this is not a claim that
every platform filesystem failure has been reproduced inside the packaged app.

The fixture provider remains explicitly fake. Root branches, the existing session,
turn and reply bounds, and implemented typed actions remain the supported slice.
Forks, archive import, readable inspection exports, real inference, automatic
orphan recovery and cross-device synchronization are separate work.

## Verification

`cargo test -p locallore-workspace --locked --offline` exercises actual shared
Hosts against synthetic temporary databases: accepted save/reopen/exact retry,
isolation, concurrent owners, cancellation, failed acknowledgements, orphan
drafts, stale local caches and a full catalog. Native Android registry tests use
the same factory. No real stories or models are used.

See [desktop app proof](../desktop/APP_DURABILITY.md),
[Android app proof](../native/APP_DURABILITY.md) and
[independent ownership review](APP_INTEGRATION_REVIEW.md) for exact commands,
counts, environment and unrun checks. These are local verification records;
ticket acceptance and merge remain the owner's decision.

The [dated integrated verification](APP_VERIFICATION_2026-10-22.md) records the
final source identity, packaging checks and remaining device limits.

This work used separate worktrees and build outputs. It issued no ADB commands,
stopped no shared build daemons and sent no input to desktop windows. Android
builds use a separate Gradle user home populated from read-only dependency caches.
The protected runtime-control chat's checkouts, device sessions, models and
processes are outside this work's write scope.
