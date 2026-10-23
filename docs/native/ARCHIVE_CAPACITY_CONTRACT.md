# Bounded archive storage exhaustion proof

M08.06 follows the interruption/recovery proof in PR79. This is a synthetic
SQLite page-limit experiment, not device-partition exhaustion or a phone benchmark.
Accepted events, projections and engine validation remain the production authority.

## Isolated build

`localLoreArchiveCapacityVerification=true` selects application ID
`org.locallore.app.archivecapacity`, its own provider authorities, the separate
`build-archive-capacity` directory and the `archive-capacity-fixture` Rust feature.
The build enforces a separate Gradle project cache (`.gradle-archive-capacity`). It cannot be
combined with `localLoreArchiveVerification`; release variants are disabled.
Ordinary builds explicitly clear `LIBSQLITE3_FLAGS` and omit the fixture feature.
No dependency version or schema changes are required.

The dedicated build passes `SQLITE_MAX_PAGE_COUNT=96` to the existing pinned
bundled SQLite. This initializes each connection's page limit; it is not an
immutable operating-system quota. The fixture checks the actual limit on each
connection and never changes it. SQLite documents growth beyond
[`max_page_count`](https://www.sqlite.org/pragma.html#pragma_max_page_count) as
`SQLITE_FULL`; its [compile option](https://www.sqlite.org/compile.html#max_page_count)
sets that default. This does not exercise all physical
[`SQLITE_FULL` causes](https://www.sqlite.org/rescode.html#full), I/O failures or
power loss.

## Native fixture and ownership

The feature-only `NativeArchiveCapacityFixture.run(root, mode)` JNI export calls
the fixed development fixture owned by the storage crate. No product archive JNI
call changes. Normal and archive-verification libraries must have no fixture
export. Java inputs and responses are bounded; no Java reference, callback,
thread or native handle is retained by the fixture.

`root` must be a new run under a real `archive-capacity` parent. `setup` exclusively
creates it, its exact `owner-v1` marker (`locallore-archive-capacity-v1`, no newline),
its original synthetic archive, private baseline and `workspace-v1/stories.sqlite3`.
Later `check-full`, `relieve` and `check-imported` modes require that owner and fixed
files. Runs are retained; none is adopted, reset or recursively deleted.

Pressure consists of real deterministic, observer-filtered packets produced by
`Store::prepare_memory`/`publish_memory` for accepted synthetic control-story
events. Exact schema verification stays enabled. Relief invalidates only that
control story's player cache partition through `Store::invalidate_memory`.
Accepted history, the retained Mira cache partition and archive bytes must remain
unchanged. No padding table, raw canonical write, story deletion, public SQL
input, runtime cap increase or alternate uncapped binary is used for relief.

## Compose and JNI qualification

`ArchiveCapacityActivityTest#storageFullThenCacheReliefAndFreshImport` uses an
actual Compose test Activity, real ShellViewModel and real native gateways. A
test Context redirects only its own no-backup workspace into the fresh fixture.
It is not the production MainActivity callback test; PR78 covers those callbacks.
The existing instrumentation-only DocumentsProvider and actual system selection
still supply the product's temporary URI grant. Root titles and selectors include
the exact instrumentation package so coexisting verification providers cannot be
confused by a shared human label. Each selected preview must match the fixture's
source story ID before confirmation.

The test must observe a real native `Full` while confirming import, render the
storage guidance, remove consumed consent and refuse an old native token.
Native strict reopen must show no imported identity or partial rows and unchanged
retained canonical history. A successful standalone staging import of the same
source establishes that the target pressure causes the failure. After draining
owners, cache-only relief uses the same installed library and fixed cap. Fresh
selection/validation and explicit consent must import the exact original archive.
Before continued play, native reexport must equal the original bytes. Explicit
opening, one potion gift, duplicate refusal and reopened accepted history follow.

Only after all checks, document descriptors and both four-slot archive/workspace
owner fences pass may the
test write a create-new `capacity-verified.json`. Its eight exact fields are
`version`, `run`, `status`, `archive_sha256`, `source_revision`,
`continued_revision`, `full_count`, `cache_only_relief` (1, exact run, verified,
exact source digest, 2, 3, 1, true respectively). The external runner requires
one ordered matching test start/pass and successful runner terminal as well as
this source-bound record. A runner exit or marker alone cannot qualify a pass.

`scripts/archive_capacity.py` requires preinstalled exact dedicated APKs; it never
installs, uninstalls or clears data. It snapshots all LocalLore package hashes,
verifies both owned identities before targeted stopping, and checks all owned
processes including provider subprocesses are absent. Sticky unknown client
cleanup fences further device calls. Raw attempts and records stay in exclusive
private output directories; only reviewed aggregates belong in Git.

## Remaining gates

Device ENOSPC, Android mid-transaction process death, arbitrary provider hard
preemption, low-memory death, power loss, physical phones, ARM64 execution,
16 KiB operating-system pages and real-model quality/performance remain separate.
Passing this packet does not accept the whole M08 milestone or authorize a merge.
