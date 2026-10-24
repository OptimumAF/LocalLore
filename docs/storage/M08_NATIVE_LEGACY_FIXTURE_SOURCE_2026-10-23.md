# Native legacy development fixture: exact historical schema reconstruction

Date: 2026-10-23. Partial M08.06/M04.06 source correction, not native app
execution or migration qualification.

Claims before editing: [#12 6378137485](https://github.com/OptimumAF/LocalLore/issues/12#issuecomment-6378137485)
and [#8 6378137713](https://github.com/OptimumAF/LocalLore/issues/8#issuecomment-6378137713).
Separate `fix/m08-legacy-native-fixture` / `source-legacy-native-fixture`, exact
base `b44f911fb7b448823ae04a353e93e8cad1ef9755`. Own only existing
`crates/locallore-storage/examples/native_legacy_workspace.rs` and this new
report. The coordinator retains all production/migration/DDL/harness ownership.

## Actual failure and source cause

The coordinator's native migration harness stopped with `FixtureReadOnly` before
app startup. Original evidence remains in `desktop-schema5-native-legacy.log`.
No passing migration, native IPC, WebView or rendered-app result is inferred
from that attempt.

The example first creates the current Store and saves the actual Core original
gift. Its old reconstruction then dropped derived tables and replaced only the
migration header/user_version with schema1 metadata. Schema5's added turn/event
kind columns and changed projection CHECK constraint remained. This is not the
historical schema1 shape; strict read-only admission correctly refused it.
The same relabeling assumption had previously been corrected in the separate
historical test factory; its TEMP/PID family guard intentionally does not admit
this application's fixed `legacy-fixture` directory.

## Focused development-only correction

Source commit `7c6cb4c2bd236b167d9d3a26a4e03ecb4a2201a7`; example SHA256
`8ed0b346b8406f13ff994d7460b465271e01a2c37d144cb2b6ba6ec3675b731b`.

The example retains the existing development-fixtures Cargo feature gate and
fixed `create|verify` CLI. `create` still requires a new, exclusively created
`legacy-fixture` directory; existing directories/files/links are refused. The
absolute-path, ancestor symlink and Windows reparse checks remain. No arbitrary
SQL, selectable schema, general file path endpoint or production writer is added.

After the existing actual Store/Core create/begin/commit closes, its private
reconstruction now:

1. Requires the fixed database/directory names and an existing regular file no
   larger than64MiB. It runs the existing read-only inspect against the current
   schema, preserving byte equality and actual gift/receipt/state checks before
   source copying. Inspect additionally requires Domain1.
2. Refuses nonlegacy turn/event kinds and projection versions other than1.
   This fixture cannot discard an author record or cast mixed history as old.
3. Creates a private in-memory database from exact unchanged
   `migrations/001_initial.sql`, with its actual old header, constraints and
   original column inventory. Sets the established application ID/user_version1.
4. Copies only the fixed original columns of stories, branches, entities,
   branch_entities, turns, accepted_events, event_witnesses and
   branch_projections. Each historical column inventory is checked. SqlValues
   preserve payload TEXT and other SQL values rather than reserializing them.
   All rows are inserted in one deferred, foreign-key-enabled transaction;
   `foreign_key_check` must be empty before commit.
5. Uses the existing rusqlite backup facility to copy that fully constructed
   historical database into the same newly owned closed fixture file, then
   checks foreign keys again. Existing `inspect(path,1)` performs strict actual
   Store/Core read-only verification of the result after handles close.

This reuses the historical test factory's proven *source algorithm*, not its
module or admission rules. That unrelated helper and its guards were not edited.
No new dependency, fixture asset, production migration or DDL change exists.
It remains a reconstructed synthetic schema1 database containing actual current
Core-validated Domain1 payloads, not execution of an old production Store writer.

## Preserved oracles and limits

The original gift ID, fixed turn key, Give command, request/proposal/narration,
receipt and canonical state construction are unchanged. The read-only library
scope/head/draft checks, receipt equality, canonical byte equality, before/after
database bytes and their hashes remain. Verify still requires the current live
schema, exactly one old-schema backup with the established filename pattern,
exact canonical/receipt hashes across live and backup, and no unexpected files.
The harness's restart and render checks were not touched.

The correction does not weaken strict schema verification or claim durability
from header rewriting. A failed create can leave its newly owned synthetic
directory for inspection; it does not adopt an existing directory or authorize
cleanup of caller data. The existing harness/coordinator must supply its normal
fresh owned fixture root when rerunning.

Actually performed here: source/Git inspection, `rustfmt --edition 2021` parser
formatting, `rustfmt --edition 2021 --check`, source hashing and
`git diff --check`, passed. Git2.33.0.windows.2 / PowerShell7.6.5 /
rustfmt1.8.0-stable are the source environment. **No compilation or execution**
of the corrected example occurred. No Cargo, Node, Gradle, SQLite, app/native IPC,
WebView, model, device, ADB, CUA, desktop capture/control, protected resources,
settings, PR or merge operation was run by this reviewer.

Next runnable task: coordinator imports this source, compiles/checks the
development example in its serialized build slot, reruns its existing native
legacy migration harness against a new owned fixture root, retains exact results
and reviews application-owned render artifacts. The original pre-startup
FixtureReadOnly log stays retained; source checks here are not a corrected GREEN.
Both exact path claims are released at handoff. Full task acceptance remains
with coordinator evidence and the user-authorized review gate.
