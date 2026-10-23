# D03 native inspection snapshots

The Windows desktop provides derived inspection exports without granting story
mutation authority. The shared Host captures a coherent canonical head; native
code privately retains that immutable bundle behind a window-bound random token.
Preview lists privacy, scope, revision, fixed file names and sizes. Saving accepts
only the token and opens a native folder picker. Renderer IPC accepts no path,
file bytes, replacement manifest or save-time mode. A later story turn does not
change an existing preview.

Diagnostics is the default: counts/status and manifest metadata, with no story
text, seed, prompts, state, model weights or source paths. Player is an explicit
private export of accepted story and player-visible state. Full is an explicit
private spoiler export requiring the trusted native Story Lab grant. Text can
contain personal information and must be reviewed before sharing. The manifest
reports unsupported summaries and retrieval indexes explicitly. These views are
not a portable playable archive. The shared contract is
[inspection snapshot v1](../storage/INSPECTION_SNAPSHOT_V1.md).

A separate Story Lab option captures ALL stories, hidden canon, submitted drafts
and receipts into a consistent private SQLite copy. Native code obtains the
source path internally; the shared helper opens it read-only and checks the same
held snapshot against a 64 MiB budget before allocating the copy. This is for
deliberate SQLite inspection, separate from readable exports. No live writable
connection, Explorer or external tool is opened. Reveal storage displays the
actual app-owned path and schema in the application.

Readable exports contain manifest.json plus diagnostics.json, or seven named
JSON/JSONL views. The separate database export contains manifest.json and
stories-snapshot.sqlite. Native code validates inventory, SHA256 and bounded
sizes; it pins approved directory ancestors and the new staging directory,
rejects reparse points, writes create-new files, syncs each file, then publishes
with a no-replace handle-based directory rename. Cancellation and publication
serialize. Existing targets survive collisions. A completed publication is
reported even if the former staging name is recreated afterward. Native memory
holds at most two previews for five minutes; this is not an on-disk deletion TTL.

Opening an existing readable inspection folder uses another explicit native
folder picker and fixed-name validation. The exact loaded manifest bytes are
retained, including legitimate compact/reordered JSON. Read-only opening rejects
later changes. Checksums establish structural consistency, not authorship or
provenance: externally opened exports are always labeled untrusted and may
contain private/hidden text regardless of their claimed mode. Text renders inertly;
no opened content becomes story commands or canonical state. The viewer limits
text to 64 KiB while leaving saved files intact. SQLite is shown as binary metadata.

Private database preview copies normally leave the app-owned cache immediately
after capture. Process death may leave a private-preview-GUID directory. The next
workspace initialization scans at most 128 cache entries, removes only exact
owned GUID directories containing known SQLite copy files, rejects reparse/unknown
contents, and skips directories pinned by another active instance. Cleanup status
is returned with storage metadata; unavailable/skipped/over-limit cleanup may
retain copies until a later successful startup or explicit user maintenance.
This does not promise forensic deletion, OS-backup cleanup, or automatic removal
of a user-saved export. A crash during saving may also leave a staging directory
in the selected destination; no partially written directory is published under
the final export name.

All blocking copy/replay/filesystem/picker operations use native blocking workers.
Window leases fence delayed operations on close/reopen, and story/mode changes
synchronously revoke frontend presentation before waiting for native cancellation.
A save that wins cancellation can remain on disk, but a delayed acknowledgment
cannot appear under another story or privacy selection.

## Development verification

From apps/desktop, run npm run harness:export. The development-only launcher
creates a new ignored synthetic database/export root and supplies fixed native
folder choices. The real frontend controller and actual native IPC exercise
save, faults, scope changes, read-only open and process restart. The test hook
accepts fixed scenario names only; it has no renderer path/file/shell API. Both
Rust feature and frontend build gates exclude development code from production.
Use npm run check then a default cargo build to restore normal assets afterward.

The Windows folder picker is compiled in the normal executable but was not
opened or automated in the isolated run. App-only WebView CapturePreview images
are evidence of this app, not desktop screenshots. Other OS targets, installer
packaging, network filesystems and power-loss behavior remain unqualified.
