# Desktop playable archive adapter — 2026-10-23

Refs #30, partial D08.01/.02/.03/.07 and the desktop prerequisite for D08.06.
This adds a native Windows adapter and visible review/confirmation flow for the
accepted shared Store archive. It does not complete the desktop portability,
branch, author-correction or Android round-trip exit gates.

## Product and authority

Open **Playable story archive** in Story Lab. Preview the current story's full
private snapshot, review its story identity, original root, every branch head,
accepted-turn count, byte count, SHA-256 and exclusions, then explicitly confirm
before choosing an export directory. Import uses a native file picker, validates
the exact held input file, displays the same private review and requires a new
confirmation. An imported story appears in the saved library; opening its root
is explicit and does not switch the current session automatically.

The file is the shared `locallore-playable-archive` v1 from #72, not a D03
inspection snapshot. It includes hidden seed facts, all timelines, original
accepted input/narration and model/timing/provenance references. It excludes
weights, derived caches, full private traces and all noncommitted workflow
keys/status/drafts. Import never resumes pending work or loads a referenced
model. Manual transfer is a snapshot, not live synchronization. Checksums prove
consistency, not authorship. Existing story IDs always conflict, including an
identical retry; overwrite, remap and automatic merge are unavailable.

Renderer commands carry only bounded session/scope/head selectors, opaque
preview tokens, explicit consent and operation IDs. They cannot choose database
paths, SQL, code, executables or archive bytes. Rust rechecks the native session
and authoritative persisted head and calls the existing shared archive/replay
implementation. Inspection access never becomes character knowledge or model
input. Imported child timelines are retained by Store; branch switching and
author corrections are explicitly unavailable in this panel.

## Native lifetime and filesystem boundary

There are at most two preview tokens per window, each expiring ten minutes after
creation, pruned on access. They are bounded encoded snapshots, not a measured
heap limit; two 32MiB input bounds plus decoded/serialized copies may coexist.
One application-owned worker runs at a time. Window epochs, a registered worker
handle and a start barrier fence destruction/reopen and late presentation.
Joining occurs outside lease/metadata locks. Cancellation is cooperative; a
destination commit may already have won. A lost acknowledgement is displayed as
uncertain and requires checking the library; retrying the same identity cannot
overwrite the committed story.

Import first uses a new private staging Store and the shared validator/replayer.
The disposable Windows database is created with accepted #86
`Store::create_new_pinned`: new main/journal/wal/shm reservations and pinned
ancestors exist before SQLite touches the path, with MEMORY journaling only in
that disposable Store. It does not change destination durability. Once staging
succeeds, the original opaque validated archive is applied to the application
Store in its existing atomic, nonoverwriting transaction.

Input reads use the already opened pinned file handle, capped at 32MiB plus one
byte. Windows reparse points, ambiguous path components and unsafe ancestors
are refused. Export writes an exclusively new temporary file, flushes it and
publishes without overwriting the fixed native output name. Cleanup handles
only four known owned staging filenames and their private UUID directory,
without recursion; a failed constructor or interrupted process may leave private
files for later inspection. Cleanup failure is reported honestly. These guards
are not a sandbox against another process running as the same OS user. User
exports and OS copies remain outside application retention control.

## Reproduce local verification

Use Windows with Rust/Cargo 1.93.1 and the checked-in lockfiles. Install the
locked frontend dependencies as described in `apps/desktop/README.md`; this
cohort used Node24.22.1/npm11.19.1. Set private task-owned output directories:

```powershell
$env:CARGO_PROFILE_DEV_DEBUG='0'
$env:CARGO_PROFILE_TEST_DEBUG='0'
$env:CARGO_INCREMENTAL='0'
# TEMP/TMP should point to a fresh task-owned directory.
$env:LOCALLORE_D08_TARGET_DIR='<native-target>'
$env:LOCALLORE_D08_ARTIFACT_ROOT='<private-artifacts>'
node apps/desktop/archive-harness.mjs
node apps/desktop/check-early-cancel.mjs
node apps/desktop/verify-frontend.mjs
cargo +1.93.1 test --manifest-path apps/desktop/src-tauri/Cargo.toml --locked --offline --target-dir <native-target>
cargo +1.93.1 test --manifest-path apps/desktop/src-tauri/Cargo.toml --features dev-harness --locked --offline --target-dir <native-target>
cargo +1.93.1 clippy --manifest-path apps/desktop/src-tauri/Cargo.toml --features dev-harness --all-targets --locked --offline --target-dir <native-target> -- -D warnings
cargo +1.93.1 fmt --manifest-path apps/desktop/src-tauri/Cargo.toml -- --check
```

The archive harness builds its own fixed development frontend and native binary,
then runs five invisible, unfocused application processes: source, import,
restart, uncertain acknowledgement and window retirement. It uses the real
frontend controllers, production native IPC and actual WebView2 CapturePreview
images/semantic snapshots. It never captures or controls the desktop. Native
picker post-selection and write-error cases use fixed development-only doubles;
actual system dialog interaction was not automated. No generic server, file/code
execution hook or production remote debugging API is introduced. Generated
artifacts stay local and ignored. Run the frontend verifier afterward to restore
the normal bundle and check development-hook exclusion.

## Frozen execution evidence

At clean production `4ff02b02344d67bfec266735ee4071c4c14dde29`, including
accepted main `bffa7e6`, the coordinator executed:

| Check | Actual result |
| --- | --- |
| Archive native | 63 distinct assertions, 17 actual app-owned render captures; five process launches |
| Evaluation native | 26 assertions, 14 captures |
| Metadata trace native | 74 assertions, 12 captures |
| Inspector native | 93 assertions, 14 captures |
| Durable native | 33 assertions across actual executable restart |
| Inspection export native | 36 assertions across actual executable restart |
| Original Play/Lab native | 21 checkpoints, 163 assertions |
| Default native unit tests | 42 passed, 1 existing privileged qualification ignore |
| Development native unit/contracts | 44 + 2 passed, 1 existing ignore |
| Strict default and development native Clippy; native fmt; frontend verifier | Passed |

The archive summary SHA-256 is
`c0d3ada2a233c38450041c64fe64d4d50b29dfc7f5ae8f2b436d5838ce385ddc`.
Local cohort directory: `d08-final-artifacts/archive-native-c0a3ac1c-1fd6-4b49-81b2-f74a37004325`.
Its sourceRevision/sourceDirty, source/binary hashes and per-stage reports bind
the evidence. The coordinator inspected the narrow review, actual pending
import, identity-conflict error and retired/reopened-window images and their
semantic state. Text wrapped, actions/errors were readable and the semantic
snapshots reported no horizontal overflow. This is not a claim that every image
was manually inspected. Installed WebView2 application directories were
155.0.4283.45/.60/.62; the harness reports native-webview2 but does not record
which installed revision the loader selected, so that exact runtime is unknown.

Assertions include accepted receipts, observer isolation after import, original
retry identity, staging cancellation without destination changes, duplicate ID,
lost acknowledgement, future/corrupt/oversize input, source preservation,
explicit consent, exact preview bytes, no model auto-load, bounded categorized
errors and real Destroy/reopen fencing. Native tests additionally exercise file
and parent reparse refusal, hardlinks, a changed input after preview, a hostile
SQLite sidecar targeting another valid Store, and commit/cancel/lifetime races.
The harness's disk-full case is a fixed write-failure injection, not measured
physical disk exhaustion. Export-directory and file pickers remain native UI
execution gaps.

## Retained failures and review

Before #86, the shared staging regression demonstrated that a planted journal
could target another database. It was fixed in the shared owner before adapter
publication; the actual hostile-sidecar regression now passes. The independent
adapter review is `D08_NATIVE_ARCHIVE_REVIEW_2026-10-23.md`; it excludes its
reviewer's own shared Store implementation from independent scope.

Combined native runs exposed a real controller race: Cancel could precede Rust
admission and emit UnknownTurn/TransportUnknown. Deferring control until the
submit acknowledgement fixed early cancellation, but the original native suite
then found a second case: cancellation during a lost-acknowledgement recovery
lookup. A separate validated original-key lookup now proves admission before
native cancellation. A five-schedule actual-controller test failed before that
fix and passes afterward. A terminal result clears unresolved recovery, so a
held old Transport error cannot replace it. The independent delta review is
`D06_D08_TEARDOWN_DELTA_REVIEW_2026-10-23.md`.

Another harness failure expected exactly two native Cancelled records. The
corrected early-admission flow legitimately avoids one Prepare call. The
assertion now allows at most two, still requires every captured category to be
native Cancelled, and retains all canonical cancellation checks. Unhandled,
render, other-category or excess errors still fail. Failure artifacts are
retained; they are not counted as passing runs.

Windows WebView shutdown sometimes logs class-unregister error1412 or an invalid
window-handle PostMessage diagnostic after successful fixed journeys. Those
bounded stderr logs remain local and are not frontend RenderError evidence.
The first formatting check detected accepted-main schema whitespace; integrating
#88 supplies its already verified schema formatting. No check was relaxed.

## Remaining gates

No fresh desktop-to-Android chooser loop, emulator/device action, actual model
generation or blocked-network measurement was performed for this adapter.
Accepted shared/Android archive and parity evidence is supplemental and must
retain its original attribution. Desktop branch/rewind/regenerate and author
correction UI are still required. Current accepted archive-v1/schema2 support
must be reconciled with concurrent retained-parent/archive-v2 work (#85) before
claiming newer-format compatibility. No full D08 checkbox or release gate is
satisfied by this partial adapter.
