# Windows pinned new Store — staging prerequisite, 2026-10-23

## Current corrected contract — sidecar blocker reproduced and repaired

**The leaf-only `889cbfb` implementation below was blocked before acceptance.**
Desktop review found an actual planted `staging.sqlite-journal` symlink could
overwrite another valid synthetic Store. Independent shared reproduction
`a2add43` failed against that implementation with
`sidecar=-journal, accepted=true, outside_bytes_changed=true`. The failure log is
retained as `pinned-new-sidecar-repro-before.log`; the native repro is `78e04fe`.
The original 91-test results did not exercise this hole and do not establish
safety against sidecar attacks.

Corrected source: `9ed53a4af0ec83da2050d12a3ca0fd07ac3ee932`, on the original
isolated staging branch. Reopened claims #12 comment 6362065095 / #31 6362065399.
The coordinator explicitly approved the following narrower **disposable staging
only** contract. Independent review/native adoption remain required.

Before **any SQLite call**, `create_new_pinned` atomically reserves all four exact
names: main file, `-journal`, `-wal`, `-shm`. Any existing entry, even an empty
ordinary sidecar, fails with Io before SQLite can inspect/recover it. Main-file
sharing permits READ/WRITE for SQLite. Sidecar sharing permits **READ only**;
every guard denies DELETE. Thus a compatible watcher cannot fill an empty
sidecar with hot-journal/WAL bytes, rename it or redirect it before connection.
Opened-handle regular/nonreparse checks still apply. All guards live in a private
Store field after Connection, so they release after SQLite closes.

The dedicated staging connection first selects `journal_mode=MEMORY` and verifies
the readback, then applies normal connection configuration and the unchanged
normal initializer/schema verification. No public Store API exposes a later mode
switch. Normal `Store::open` configuration/transactions remain unchanged, and a
normal reopen after staging drop uses DELETE journaling in the actual unit test.

**MEMORY mode alone is not the fix.** In the exact bundled SQLite amalgamation,
both `journal_mode` (pragma entry line 144413) and `synchronous` (144585) carry
`PragFlg_NeedSchema`; `sqlite3Pragma` loads schema at 145180. Pager shared-lock
acquisition calls `hasHotJournal` (64739/64887). Consequently even preparing the
pragma can inspect recovery state before its mode change executes. The exact
sidecars are already newly owned, empty, write/delete protected at that point.
The empty-main benign journal-delete attempt in `hasHotJournal` cannot delete
the guard and does not redirect a later write; actual constructor/import tests
exercise this path. The SQLite source inspected is the existing pinned
`libsqlite3-sys 0.38.2/sqlite3/sqlite3.c`, not a modified VFS.

This API is **not a crash-durable active-workspace opener**. In-memory rollback
is appropriate only for disposable staging: process death can leave partial
staging data which must be discarded, never resumed as an accepted durable save.
The durable destination import is a separate normal Store transaction. The
caller retains its trusted ancestor handles and private staging namespace; this
does not prevent a same-user process from directly modifying the main file's
shared-write contents. No ATTACH/multi-database SQL API is exposed, so SQLite
super-journal `-mj*` files are not a supported staging path. TEMP storage remains
the configured/read-back MEMORY policy.

Failures may leave only exclusively created main/sidecar placeholders or a partial
owned staging DB. No path deletion/reopen cleanup gap was added. The trusted
staging owner must clean its own namespace after all handles close. It must also
close the Store before publishing/renaming the staged main file. Non-Windows
still fails closed; no weaker portable reservation guarantee is substituted.

Actual corrected checks, same Rust 1.93.1/locked/offline/own target and TEMP as
below:

- Default storage suite: **92 passed, 0 failed, 2 privileged cases ignored**.
- All-feature storage suite: **92 passed, 0 failed, 2 privileged cases ignored**.
- Explicit `--test pinned_new_store -- --ignored --nocapture`: **2 passed**.
- Full integration `--include-ignored`: **8 passed**, plus three fixed-hook unit
  cases passed separately.
- Strict all-target Clippy in default and all-feature configurations, fmt and
  whitespace checks passed.

New/strengthened assertions cover every sidecar's empty/ordinary/hardlink refusal,
file-symlink-to-valid-Store and dangling-symlink refusal with unchanged outside
bytes/canonical replay, no-connect hooks on sidecar refusal, and exact pre-SQLite
WRITE/delete/rename/replacement denial for all sidecars. Sidecars remain empty and
unwritable during actual turns/archive import. The initializer hook verifies
MEMORY mode before its first transaction; normal reopen verifies DELETE mode.
Original live-guard/drop-release/fork/retry/import/partial-failure cases remain.

Corrected logs: `pinned-new-sidecar-first-fix.log`,
`pinned-new-sidecar-strengthened.log`, `pinned-new-sidecar-hooks.log`,
`pinned-new-sidecar-storage-default.log`, `pinned-new-sidecar-storage-allfeatures.log`,
`pinned-new-sidecar-explicit-reparse.log`, `pinned-new-sidecar-clippy.log`,
`pinned-new-sidecar-clippy-default.log`.

| Corrected file | SHA-256 |
| --- | --- |
| storage/src/lib.rs | `fe9895815393fa48969ae3b6d925257ff11cdcbca5a246515f29bed1fa03089b` |
| storage/tests/pinned_new_store.rs | `86759d53eecb1ed2359fa69cb5b6a179ab689f7235fb4441660e87242eb58589` |

No actual native/UI rerun is attributed to this author. The native owner must
rerun its specific corruption regression and staging flow. Full D08/D09 remains
open. D06 review was paused to repair this blocker; no D06 production changes
were made.

## Historical leaf-only proposal and evidence — superseded

The remainder records `889cbfb`/`7839c44` before the concrete sidecar attack. Its
leaf-only contract and old test/hash counts are historical, not the current
constructor security or durability contract. Use the corrected section above.

Status: implemented/locally tested, in_review, not full D08/D09 acceptance.
Contributor `/root/app_storage_review`; claims #12 comment 6361679628 and #31
6361679983. Isolated branch `impl/m08-pinned-new-store`, accepted base
`a2bb6639eacaa9ac416788caf2fc7a6b70bf1392`; frozen implementation
`889cbfbd2de905ec5bb5e2b27ac749afa19ee44c`. Coordinator independent review and
desktop adoption remain separate gates.

## Scope and caller contract

`Store::create_new_pinned(path: &Path) -> Result<Store, StorageError>` creates a
**new** Windows staging database. It refuses every existing leaf before opening
SQLite: empty/ordinary file, existing valid Store, hard link, directory, file
reparse or dangling reparse. It does not open, migrate, overwrite or adopt one.
Existing-leaf reservation refusal is the fixed `Io` category, without exposing
paths or file content. Other initialization/database errors retain existing
categories. No new error enum or wire schema was added.

Paths must be absolute, have a UTF-8 final component, contain no ParentDir
components, and have no final-component colon/NUL or trailing dot/space. This
avoids relative-current-directory and ambiguous stream/leaf aliases in the new
API. It is not an unrestricted path validator.

**The caller must retain its trusted ancestor chain for the entire Store
lifetime**, and own the private staging namespace/cleanup. The leaf reservation
does not pin ancestor directories, audit all filesystem namespace forms, secure
SQLite sidecar names against an untrusted writer, change ACLs or create a sandbox
against another process with same-user write authority. The desktop staging
owner's root-to-UUID directory handles remain necessary. No protection for
ordinary `Store::open` callers is inferred from this new method.

Non-Windows calls fail closed with existing `InvalidInput`, before any file
creation. A weaker Unix rename guarantee is not substituted. The non-Windows
branch was inspected in source, not executed in this Windows qualification.

## Reservation and initialization

The new method atomically reserves with Rust `create_new`, read/write access,
`FILE_SHARE_READ | FILE_SHARE_WRITE` **without FILE_SHARE_DELETE**, and
`FILE_FLAG_OPEN_REPARSE_POINT`. It checks metadata from the opened handle for an
ordinary file without the reparse attribute. The handle remains live across
SQLite connection, initialization, import and subsequent Store operations.
These sharing controls use the documented
[Windows CreateFile contract](https://learn.microsoft.com/en-us/windows/win32/api/fileapi/nf-fileapi-createfilew)
and [Rust OpenOptionsExt](https://doc.rust-lang.org/std/os/windows/fs/trait.OpenOptionsExt.html).
Atomic existing-leaf refusal follows the documented
[create_new contract](https://doc.rust-lang.org/std/fs/struct.OpenOptions.html#method.create_new).

`Store` declares its Connection before its optional private reservation File.
Rust drops struct fields in declaration order, so SQLite closes before the leaf
guard is released. Constructor-error locals likewise close Connection before
the earlier reservation. See the
[Rust destructor rules](https://doc.rust-lang.org/reference/destructors.html#destructors).

The new path must still have zero application/version identity and an empty
schema before initialization. This also refuses adoption if compatible write
sharing populated the new leaf before the SQLite identity check. The method
then reuses the existing normal initializer and strict schema verification.
The common open/initialize/migration body was factored into a private helper;
existing `open`, `open_application` and read-only semantics are unchanged.
An existing unit's direct Store literal now uses the same private constructor.
No memory-wrapper, Engine, Host, migration SQL/version, dependency, app/native or
Android implementation was edited. No alternate SQLite/schema owner exists.

## Failure cleanup decision

The coordinator explicitly approved leaving an exclusively created empty or
partial staging leaf on constructor failure. No path deletion, recursive cleanup,
close/reopen cleanup attempt or foreign-file adoption occurs in this helper.
The trusted staging owner handles that leftover separately after Store failure.
An existing path is never removed or changed by reservation refusal.

The initially considered DELETE-access cleanup handle was rejected **before
implementation**: Windows sharing compatibility is bidirectional, while pinned
bundled SQLite opens its main file sharing READ/WRITE without DELETE. A guard
requesting DELETE would prevent SQLite's compatible second open. Handle-based
disposition requires DELETE access, per
[SetFileInformationByHandle](https://learn.microsoft.com/en-us/windows/win32/api/fileapi/nf-fileapi-setfileinformationbyhandle).
Closing the protective handle and deleting by path would reintroduce a lookup
gap. A retained leftover is preferable to deleting an unknown replacement.

The locally pinned `libsqlite3-sys 0.38.2/sqlite3/sqlite3.c` confirms the main
Windows VFS READ/WRITE sharing at its `dwShareMode` assignment (line 54198 in
the inspected dependency source). Actual connection/import tests below verify
compatibility; no SQLite VFS or system setting was modified.

## Executed evidence

Windows, Rust/Cargo 1.93.1; locked/offline, DEV/TEST debug 0, incremental off;
owned task TEMP/TMP and target
`D:/CodexLocalLore/01a165d9-ff25-7500-a550-1099087d4e37/m08-pinned-new-store`.
All files are synthetic fixtures. No app, model, device/CUA, protected resource,
new dependency, settings change, privilege enablement or binary publication.

```text
cargo +1.93.1 test -p locallore-storage --locked --offline --target-dir <own-target>
91 passed; 0 failed; 1 explicitly privileged reparse case ignored.
cargo +1.93.1 test -p locallore-storage --all-features --locked --offline --target-dir <own-target>
91 passed; 0 failed; 1 explicitly privileged reparse case ignored.
cargo +1.93.1 test -p locallore-storage --test pinned_new_store --locked --offline --target-dir <own-target> -- --ignored --nocapture
1 passed; 0 failed (actual file/dangling symlink test, explicit default-feature run).
cargo +1.93.1 clippy -p locallore-storage --all-targets --locked --offline --target-dir <own-target> -- -D warnings
PASS
cargo +1.93.1 clippy -p locallore-storage --all-targets --all-features --locked --offline --target-dir <own-target> -- -D warnings
PASS
cargo +1.93.1 fmt --all -- --check
PASS
git diff --check
PASS
```

The eight normal new cases plus one explicitly privileged case cover:

- Before SQLite opens, a fixed test-only post-reservation hook attempts actual
  leaf rename/delete and replacement by an outside valid Store. All fail while
  the reservation is held; normal initialization then succeeds. This targets the
  original create/drop/connect interval directly.
- Existing-leaf refusal cannot reach either connection hook. Ordinary, empty,
  valid database, hardlinked and directory fixtures remain unchanged.
- Actual outside valid Store bytes and canonical state remain unchanged after
  planted file-symlink and dangling-symlink refusal; no dangling target is created.
- A fixed test-only initializer failure writes a partial owned database and then
  returns Database. Only that leaf remains, retries refuse it unchanged, outside
  bytes remain unchanged, and rename succeeds after error releases the handles.
- During an actual live SQLite Store, rename/delete/replacement fail; normal
  turns work. Drop releases the reservation and rename/reopen works afterward.
- Shared archive validation/import, original child scopes, exact committed retry,
  reopen and independent continuation work in the pinned staging database.
- Two concurrent creators yield exactly one Store; relative/ambiguous leaf input
  fails before creating anything.

`PinnedNewHooks` and its parameters exist only under `cfg(test)`, with no public,
environment, renderer or normal-build control. New integration tests use the
real public constructor, not hooks. Privileged symlink execution is separate
from the routine suite, with no silent skip counted as a pass.

Retained local logs: `pinned-new-first-check.log`, `pinned-new-focused.log`
(three internal hook cases; the name filter did not select integration cases),
`pinned-new-integration.log` (5 pass/1 ignored), `pinned-new-reparse.log`,
`pinned-new-storage-default.log`, `pinned-new-storage-allfeatures.log`,
`pinned-new-clippy.log`, and `pinned-new-clippy-default.log`.

SHA-256 of frozen implementation bytes:

| File | SHA-256 |
| --- | --- |
| storage/src/lib.rs | `4acc279f353dc4f3500fd29768add7aa7bf9d4bd33ec2671256389a59fb4aa6d` |
| storage/tests/pinned_new_store.rs | `9f3fb7825e7f9ac05b5af42f45d45aa49d6bd7567d2b9fa21cf27055c120c3d8` |

Next: independent source review, coordinator integration, desktop adoption under
its retained ancestor handles and actual staging/import UI gate. This does not
complete parent-path/sidecar security, harden existing open/backup APIs, qualify
other filesystems/platforms, or establish full archive/native/D09 acceptance.
