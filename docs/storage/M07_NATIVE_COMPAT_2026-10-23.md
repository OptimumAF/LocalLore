# Store v2 desktop native compatibility

Status: **in_review**, a bounded compatibility check for #11. This is not the
full M07 or D06 exit gate. The tested implementation is
`66e9b3b8ee60f7d77d3ac1707c123cf62b05a596`, based on the coordinator's Store v2
integration `d97770c8dac2927e3584e43f697ecb609b3aa5ac`.

Claim: [#11 comment6359326089](https://github.com/OptimumAF/LocalLore/issues/11#issuecomment-6359326089).
The separately delegated UI correction was claimed before editing in
[comment6359378534](https://github.com/OptimumAF/LocalLore/issues/11#issuecomment-6359378534).
Only `App.tsx` and `model.ts` changed: the saved workspace now displays actual
`database_schema_version`, says **Not reported** if absent, and separately labels
the workspace and domain contracts. No Host, wire, database, native code, generated
schema, Android, controller or harness implementation changed in this slice.

## Verified final source

All runs below used the same React frontend/controllers and actual native IPC in
an application-owned hidden WebView2. Fixtures are explicitly fake inference;
there was no model download, import, load, generation or worker operation.
Every suite created a fresh synthetic database and restarted the actual native
executable. No desktop control or unrelated application automation was used.

| Native journey | Assertions | Captures | Result |
| --- | ---: | ---: | --- |
| D06 trace | 74 | 12 | PASS, restart |
| D05 inspector | 93 | 14 | PASS, restart |
| Durable save/resume | 33 | 11 | PASS, restart and startup failure |
| Inspection export | 36 | 14 | PASS, restart and four publications |

These are **236 original assertions and 51 captures**, not headless-only results.
The final summaries all record clean source `66e9b3b`, actual process restart and
no desktop control. Their exact SHA256 values, per-run frontend/native/core input
hashes and error categories are preserved in
[the evidence](M07_NATIVE_COMPAT_EVIDENCE_2026-10-23.json).

An additional read-only verifier passed **110 supplemental checks**, including
88 reverified source-file hashes across the four summaries. It checked:

- `PRAGMA user_version == 2` through SQLite `mode=ro` connections for all four
  fresh workspaces and the published consistent database copy.
- All 24 durable/export controller captures that retained a workspace reported
  `database_schema_version: 2` and workspace `schema_version: 1`.
- All 22 corresponding mounted DOM captures contained
  `SQLite schema 2 | Workspace contract 1 | Domain contract domain-v1`.
  The two disposed captures correctly had no mounted DOM. This is actual
  controller/native/render evidence, rather than a hand-authored workspace mock.
- Native `inspection_storage` reported schema 2 and read-only metadata. The DB
  preview and saved DB-copy manifest reported schema 2. The saved manifest equaled
  the captured preview, and its database bytes, SHA256 and read-only schema 2
  matched the manifest.
- The three readable JSON inspection manifests deliberately retained their
  independent `locallore-inspection` schema 1. Host protocol version1 and domain-v1
  remain separate contracts.

The old durable assertion name `real-workspace-schema-v1` checks the **workspace
contract**, not SQLite's version; it was preserved. The stable filename
`stories-v1.sqlite` likewise does not identify the migrated database version.
The missing-field **Not reported** branch was source-reviewed; no claim is made
that a legacy fixture exercised it in these native runs.

The earlier clean `d97770c` runs also passed the same 236 assertions. Their
distinct artifact folders remain historical evidence; they are not substituted
for the final UI run.

## Renders and expected errors

Seven final app-owned PNGs were opened and inspected: D06 context and character
lens, D05 accepted source and narrow history table, durable resumed receipts,
storage metadata and private database-copy preview. Text, wrapped IDs, read-only
and privacy labels were legible in those captures. Storage visibly says Schema 2;
the private DB preview names all stories/drafts and its two fixed files. The
new saved-workspace labels are present in captured DOM text; that collapsed
details section is outside the reviewed PNG viewport. This is not a full layout
or assistive-technology qualification.

Expected negative tests retained bounded categories: trace Agency/Cancelled/Stale;
inspector Scope/InvalidBoundary/InvalidCursor/TooLarge/InvalidRequest/Stale;
export UnsafeDestination/Full/ExportExists; deliberate storage-startup failure Io.
Every restart report has an empty error list. Chromium's shutdown-only
`Chrome_WidgetWin_0` unregister warning 1412 appeared after successful child exits;
it did not turn any report or launcher into a failure.

## Reproduction and local artifacts

All new output is task-owned on D. `<task>` below denotes the local directory
`CodexLocalLore/<current-task-id>`, not a renderer-accepted filesystem path.
The source checkout is `<task>/source-memory-native`, the target is
`<task>/desktop-inspector-target`, temporary files are
`<task>/m07-native-compat-temp`, and reports are under
`<task>/m07-native-compat-artifacts`.

Final artifact folders:

```text
trace-native-9f89eef8-eb59-4061-8252-9a4bc599daef
inspector-native-f7780997-923b-45be-8245-684a937797b6
durable-native-275f0f28-5519-4a58-b34d-05a4a29d5746
export-native-9874c734-393e-4a2a-93cf-7a2db5564b16
compatibility-verification-66e9b3b.json
```

The local supplemental verifier is
`<task>/m07-native-compat-temp/verify_schema_compat.py`, SHA256
`86656edb24002b9df65145429d9995bf679a2c102343c36859f1fa1aa30485d5`.
It consumes only these fixed synthetic capture/report/database paths, connects
read-only, and emits the separate verification JSON. It adds no product hook.

Commands ran from `apps/desktop` with TMP/TEMP and
`LOCALLORE_CHECK_OUTPUT_DIR` directed to the owned D temporary directory,
`CARGO_PROFILE_DEV_DEBUG=0`, `CARGO_PROFILE_TEST_DEBUG=0`, `CARGO_INCREMENTAL=0`.
`LOCALLORE_D06_ARTIFACT_ROOT`, `LOCALLORE_D05_ARTIFACT_ROOT` and
`LOCALLORE_DESKTOP_ARTIFACT_ROOT` selected the owned artifact root; their matching
`*_TARGET_DIR` variables selected the owned target.

```powershell
npm run check
npm run format:check
node trace-harness.mjs
node inspector-harness.mjs
node durable-harness.mjs
node export-harness.mjs
# After all native journeys, restore and verify normal assets:
npm run check
npm run format:check
cargo fmt --manifest-path src-tauri/Cargo.toml -- --check
cargo build --manifest-path src-tauri/Cargo.toml --locked --offline --target-dir <owned-D-target>
git diff --check
python <owned-D-temp>/verify_schema_compat.py
```

Every command passed. Frontend verification includes strict TypeScript,
schema/wire/keyboard regressions, cancellation/privacy checks, model recovery,
terminal model-refresh ordering, inspector provenance/context fences, debugger
stale-navigation fences and the normal-asset scan for absent development hooks.
The final default native executable and normal frontend were restored without
running a visible app; their separate hashes are in the evidence. Per-run native
and development frontend hashes describe the earlier harness builds. Raw source
hashes describe this checkout; compare Git-normalized text when another checkout
has different CRLF line endings. Node v23.10.0, Rust/Cargo 1.93.1 and cached pinned
dependencies were used; no installation occurred.

## Limits and handoff

These are **fresh schema 2** native fixtures. They do not seed or migrate an actual
schema 1 native save. The coordinator's Store migration/history/backup tests are
separate evidence and are not reported as executions by this desktop task.
Full workspace, Android and native unit/Clippy integration checks are owned by
the coordinator. No real-model quality, memory usefulness, network-blocked,
long-history, device, hostile-renderer or release qualification was added here.
Full M07 and D06 remain unchecked.

No protected chat, user save, model, device, unrelated process or worktree was
modified. The next step is coordinator review/integration of the focused UI
commit and this evidence, with actual legacy native migration and remaining
memory gates tracked separately. No PR, push, merge, settings or release action
was performed by this compatibility task.
