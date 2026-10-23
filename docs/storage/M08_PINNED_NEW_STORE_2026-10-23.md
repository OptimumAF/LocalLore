# Windows pinned new Store — staging prerequisite, 2026-10-23

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
