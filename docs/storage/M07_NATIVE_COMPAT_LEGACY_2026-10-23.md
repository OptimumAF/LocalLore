# Actual native migration of reconstructed synthetic v1

Status: **in_review**. Supplemental M07.03/.04, D03.02/.07 and D08.07 version
evolution evidence; no portable archive, Android round trip or full milestone
acceptance. Claims preceded edits:
[#11](https://github.com/OptimumAF/LocalLore/issues/11#issuecomment-6359671287),
[#24](https://github.com/OptimumAF/LocalLore/issues/24#issuecomment-6359671725),
[#30](https://github.com/OptimumAF/LocalLore/issues/30#issuecomment-6359672275).

Final clean tested source: `34bea0759e9d1d5f00d51dd9fe00376e1a4d1cc7`.
Base: coordinator integration `f5ac344c004f8a27978192a15ce884b6a9536189`, plus
coordinator SQLite memory-only temp policy `591fb60` (local cherry-pick `a32d038`).
This task did not modify Store library, schema, Host, controller, generated
contracts, Android or IPC commands. Implementation commits are `92ecc47`,
`724c062` and `34bea07`; the latter two only repair a fixture assertion and
redact its capture path.

## Fixture and authority

`locallore-storage` has a new required **development-fixtures** feature for the
fixed `native_legacy_workspace` example. Default-feature attempts to build this
example were verified to fail with the required-feature diagnostic. The feature
reuses the existing Host SHA256 helper and adds no dependency/version. Normal
native builds do not include the example or provide a legacy-creation API.

`create <new-root>/legacy-fixture` refuses existing directories and reparse
ancestors. It accepts no SQL, story payload, database filename or commands.
The original Lantern Quay seed, scope `quay/main`, and `legacy-original-gift`
are fixed. Store exclusively creates the story and commits the accepted gift.
The example then uses the already tested `historical_v1` methodology: remove the
new derived table and reconstruct the unchanged 001 migration metadata. Exact
schema1 validation and history replay pass through `Store::open_read_only`
before app startup. **This is reconstructed synthetic v1, not a save produced by
a historical released app.**

`verify` reads only the fixed fixture and its unique recognized sibling backup;
it never migrates, creates a missing database or writes SQL. It checks all path
ancestors for links/reparse points, validates both schema identities and replays
the exact owner-created receipt. Before/after database bytes must be unchanged
by verification. This development utility is trusted-launcher test code, not an
OS-adversary filesystem sandbox or a renderer capability.

The native launcher exercises actual existing-directory refusal without file
mutation, and actual junction-parent refusal with an empty target retained.
It then uses the normal workspace startup path, existing controller/gateway,
fixed hidden WebView2 capture commands and actual executable restart. Narrow
test routing adds no new native IPC or general execution endpoint.

## Final measured results

| Journey at final source | Assertions | Captures | Result |
| --- | ---: | ---: | --- |
| New native legacy qualification | 29 distinct | 8 | PASS, actual migration and restart |
| Existing native export qualification | 36 distinct | 14 | PASS, restart, four publications |

All final reports use clean source `34bea07`; legacy report errors are empty
before and after restart. The app resumes original scope/head1 and the gift
receipt, shows the spent potion and retained brass key, and resolves both exact
old-key submit and turn-status requests to the original receipt without another
effect. Player sees the original accepted event; Mira sees the witnessed gift
without player/narrator message rows; Sable sees no permitted gift history.
Inspection returns to Play and leaves canonical state unchanged. Closing releases
all owned sessions/workers. No model is loaded or called.

The normal application migration creates exactly **one schema1 backup** and a
schema2 workspace. Read-only verification after both app exits finds equal
canonical projection and receipt fingerprints across seed, backup and live DB;
the entire verification report, including both database file hashes, remains
identical after restart. Canonical SHA256:
`464abab4ac43ae8087657a524eeb09a32f5ca8d3c41ae58529e145b371166c87`.
Receipt SHA256:
`f1eee1ba28217d019f87e5c144e985f6a5462b7c638e739c6884052bffdb6b6f`.

The export rerun includes coordinator policy591fb60. Its actual storage metadata,
DB preview, published manifest and database header all identify schema2. Saved
DB bytes and checksum match the exact captured preview. Native export deliberately
retains its existing expected UnsafeDestination/Full/ExportExists negative tests;
restart errors are empty. These two launchers rebuild the native executable, so
**their binary hashes differ** despite the same source and identical development
frontend hash. Each binary is separately attributed in the evidence; no
byte-identical-binary claim is made.

Final source hashes were reverified against 47 recorded input entries. All eight
legacy captures have native-webview2 rendering metadata, actual workspace DB2 /
contract1, and DOM text distinguishing SQLite, workspace and domain contracts.
No task filesystem path remains in their semantic JSON. Four final PNGs were
opened and inspected: Mira history, Sable history, restarted receipt and export
storage. The Mira and Sable images visibly show **SQLite schema2 / Workspace
contract1 / domain-v1**, rather than only a DOM assertion; paths are synthetic
placeholders. The receipt image shows original turn/head1 and only brass-key.
Labels/tables were legible without horizontal overflow in these captures. This
is not a complete layout, accessibility, power-loss or concurrency qualification.
The usual shutdown-only Chromium unregister warning1412 accompanied successful
child exits and did not change launcher/report results.

## Reproduction and retained attempts

Node v23.10.0 and Rust/Cargo1.93.1 with cached pinned dependencies were used.
All new build/temp/evidence output is task-owned on D; source checkout is
`<task>/source-memory-legacy`, target `<task>/desktop-inspector-target`, temporary
directory `<task>/m07-native-compat-temp`, artifact root
`<task>/m07-native-legacy-artifacts`. No installation or model copy occurred.
The full input/binary/frontend/image hashes and bounded reports are in
[the evidence](M07_NATIVE_COMPAT_LEGACY_EVIDENCE_2026-10-23.json).

Final artifact folders:

```text
legacy-native-a73877d4-4052-4ccf-aff5-e8c215065de1
export-native-7116640e-606e-4934-9aa5-7b57add2b55b
```

Commands ran with TMP/TEMP and `LOCALLORE_CHECK_OUTPUT_DIR` on owned D temp,
`CARGO_PROFILE_DEV_DEBUG=0`, `CARGO_PROFILE_TEST_DEBUG=0`, `CARGO_INCREMENTAL=0`.
The fixed launchers use `LOCALLORE_DESKTOP_ARTIFACT_ROOT` and
`LOCALLORE_DESKTOP_TARGET_DIR` for these owned directories.

```powershell
cargo build -p locallore-storage --example native_legacy_workspace --no-default-features --locked --offline --target-dir <owned-target>
# Expected refusal: requires development-fixtures. Then:
cargo clippy -p locallore-storage --example native_legacy_workspace --features development-fixtures --locked --offline --target-dir <owned-target> -- -D warnings
node apps/desktop/legacy-harness.mjs
node apps/desktop/export-harness.mjs
npm --prefix apps/desktop run check
npm --prefix apps/desktop run format:check
cargo fmt --package locallore-storage -- --check
cargo fmt --manifest-path apps/desktop/src-tauri/Cargo.toml -- --check
cargo build --manifest-path apps/desktop/src-tauri/Cargo.toml --locked --offline --target-dir <owned-target>
git diff --check
```

All expected successful commands passed. Frontend checks retain the existing
schema/wire/model-refresh/privacy/provenance/debugger regressions and add a legacy
marker to the normal-asset exclusion scan. Normal frontend/default native
executable were restored after all journeys, and their separate hashes are
recorded. Compare Git-normalized text when another checkout has different CRLF.

The first native attempt at `92ecc47` failed a new harness assertion that treated
the retained brass-key Item object as numeric1. Migration/scope/head/receipt
checks already passed with no native errors; `724c062` corrected the assertion
to the established inventory-presence contract. That attempt is retained, as is
the passing `724c062` run. The final `34bea07` rerun additionally redacts the
synthetic path in native images; no failed attempt is presented as a pass.

The earlier 236 fresh-schema2 compatibility checks remain separate pre-policy
evidence. Coordinator workspace/Android/native unit checks are separately
attributed and were not executed by this task. No historical released-app save,
model quality, network-blocked/device, archive import, Android round trip,
maximum-scale responsiveness or complete M07/D08/D09 gate is claimed. No protected
chat/save/model/device/process, desktop control, PR, merge, settings or release
action occurred. Next step: coordinator review/integration and remaining gates.
