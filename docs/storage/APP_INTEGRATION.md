# Application save and resume

The desktop and Android shells use `locallore-workspace::open` and the same
`locallore-storage` owner. Each application has a local SQLite database. Shared
means shared implementation and contracts, not cross-device synchronization.
No new ledger, schema version or model dependency is introduced.

Native startup chooses a private directory outside the source tree. Desktop uses
Tauri's application-local data directory with `stories-v1.sqlite`; Android uses
`Context.noBackupFilesDir/workspace-v1/stories.sqlite3`. Directory creation and
all Host/database calls run on background workers. The UI shows the actual
location, schema/rules versions and selected story/branch/head. These directories
do not protect against a compromised OS, user backups or explicit file copying.

The bounded `workspace` operation returns metadata for up to 256 stories in
deterministic story-ID order. Startup resumes the first entry, or creates a new
opaque story identity when empty. The library permits explicit selection; this
order does not imply last-used or newest. New/reset preserves previous saves.
Closing a session preserves its story. No story deletion is exposed.

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
composer text is session-local. Retrying an uncertain outcome retains its original
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

This work used separate worktrees and build outputs. It issued no ADB commands,
stopped no shared build daemons and sent no input to desktop windows. Android
builds use a separate Gradle user home populated from read-only dependency caches.
The protected runtime-control chat's checkouts, device sessions, models and
processes are outside this work's write scope.
