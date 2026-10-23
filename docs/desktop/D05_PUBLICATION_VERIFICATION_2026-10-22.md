# D05 desktop inspector publication verification

Refs #26 D05.01-.07, partial UI integration. This publication starts at accepted
main `8f3842e` after #54 and #55. It integrates the reviewed read-only inspector
and its provenance/navigation repairs. Full D05 acceptance remains dependent on
the M06/M07 memory prerequisites; this is not a release or a new memory authority.

## Integrated source and preservation

Final tested source is clean `7611297938a50ac04aa88a42084dafff456b15de` on
`impl/d05-desktop-inspector-publication`. The old `5202b7c` branch, checkout and
preintegration evidence remain preserved. The earlier clean `78e55ff` 93-assertion
run is historical evidence; the new run below exercises accepted main plus the
reviewed UI. Neither is substituted for the other.

The scoped UI commits were cherry-picked in their reviewed order. The only
conflict was the frontend verification list: both main's model-refresh regression
and the inspector regression are retained. Schema-format commit `30827e1` was
skipped because #55 already contains it. The frozen schema and generated types
are byte-equivalent after Git newline normalization to accepted main.

The #54 model poison/unload and stale-import cleanup fixes are preserved.
ModelPanel cleanup wording, the model-refresh test, the fixed worker staging and
journey pins are unchanged from main. The worker remains
`add98cf02249141942c88e2517c2f5a4c9a91dbe9638bf7d3cd30c26916bce87`.
The controller retains main's stop-polling-before-final-refresh correction in
both success and error paths; the deterministic actual-controller test passes.

Integration adds two small corrections: the acknowledgement label is plain
`I understand; reveal spoilers`, and rustfmt collapses the inherited
`FILE_DISPOSITION_INFO { DeleteFile: true }` initializer, removing its optional
trailing comma. The latter is formatting only. No D04 runtime/model behavior,
shared core, query contract, generated schema, root manifest or storage code was
edited for publication. The evidence records preserved-file comparisons.

## Actual native result

The definitive run from clean `7611297` passed **93 distinct assertions, 14
app-owned WebView2 PNG captures and an actual executable restart**. It uses the
real frontend, Controller, native IPC, Host and synthetic SQLite workspace.
Only the explicitly labelled fake provider establishes fixture history. No real
model was loaded or called, and browsing does not trigger generation.

Artifact suffix:
`desktop-inspector-publication-artifacts/inspector-native-5823e178-d77b-4963-b4d4-5d7e7be32cba`.
Summary SHA256:
`dba1b8517affce553a23448520f439be829f4179f9c437117b1bf9101f1aad70`.
The [publication evidence](D05_PUBLICATION_EVIDENCE_2026-10-22.json) retains the
exact source/frontend/native binary hashes, synthetic reports, capture hashes,
regression summaries and normal-asset hashes. Private saves, images, databases
and raw local logs remain ignored outside the repository.

Checks cover current/historical inventory, accepted history and source links,
truth versus statement versus belief, directed relationships, observer/secret
denials, search/cursor bounds, pagination, stale replies, story changes, keyboard
skip/modal focus, restart and browsing nonmutation. Removed-potion Why shows its
prior r0 seed provenance and explicit r1 absence. Its separate accepted-turn
history shows the permitted Give event and r0-to-r1 boundary. Event/message
navigation follows permitted accepted sources, and hidden causes remain
unavailable. Returning to Play restores Player context and clears private query
parameters. Controlled late source replies cannot select another story's row.

The final diff, source, narrow-history and pagination images were inspected with
view_image. Text and source controls wrap legibly. The diff separates prior field
origin from accepted-turn evidence; it makes no single-event causal claim. The
pagination capture shows Play/Player with cleared filters. All 14 semantic capture
checks report no horizontal overflow. This is application-owned CapturePreview,
not desktop capture or desktop input automation.

## Verification commands and results

All new target, temporary and artifact outputs use the task-owned D directory.
Build/test debug information is disabled and incremental compilation is off.
The dependency junction reads the existing task-owned dependency tree.

```powershell
npm --prefix apps/desktop run check
npm --prefix apps/desktop run format:check
node apps/desktop/inspector-harness.mjs
node apps/desktop/harness.mjs native
node apps/desktop/harness.mjs headless
node apps/desktop/durable-harness.mjs
node apps/desktop/export-harness.mjs
cargo test --manifest-path apps/desktop/src-tauri/Cargo.toml --locked --offline --target-dir <owned-D-target>
cargo test --manifest-path apps/desktop/src-tauri/Cargo.toml --locked --offline --features dev-harness --target-dir <owned-D-target>
cargo test --manifest-path apps/desktop/src-tauri/Cargo.toml --locked --offline --target-dir <owned-D-target> models::tests::abandoned_import_reparse_file_is_preserved -- --exact --ignored
cargo clippy --manifest-path apps/desktop/src-tauri/Cargo.toml --all-targets --locked --offline --target-dir <owned-D-target> -- -D warnings
cargo clippy --manifest-path apps/desktop/src-tauri/Cargo.toml --all-targets --locked --offline --features dev-harness --target-dir <owned-D-target> -- -D warnings
cargo fmt --manifest-path apps/desktop/src-tauri/Cargo.toml -- --check
cargo build --manifest-path apps/desktop/src-tauri/Cargo.toml --locked --offline --target-dir <owned-D-target>
git diff --check
```

All final checks pass. Frontend verification includes strict TypeScript,
schema/wire checks, export/model/terminal-refresh/inspection controller
regressions and normal asset hook absence. Prettier passes. Default native tests
pass **17**, with one privilege-dependent test ignored in that suite; development
tests pass **19**, with the same one ignored, plus **2** harness-wrapper tests.
The ignored reparse test was then explicitly run and passed **1**. Both strict
Clippy configurations pass. Unit/Clippy suites ran at `60717ad`; the sole later
source change is the initializer formatting described above. The explicit
reparse test, final native journeys and rustfmt ran at `7611297`.

The legacy native and headless regressions each pass **163 assertions / 21
checkpoints**, the durable journey passes **33 / 11 captures**, and export passes
**36 / 14 captures / 4 publications**. All four use clean `7611297`; durability
and export include executable restart. Their exact artifact suffixes and summary
hashes are in the publication evidence. WebView shutdown emitted class-unregister
warnings while all bounded journey reports and process exits passed.

After the harness runs, frontend verification rebuilt the normal assets and the
default-feature native executable was rebuilt successfully. No harness remains
selected in the final ignored build outputs. Source remained clean before adding
these publication-only documents. Compare Git-normalized text when Windows CRLF
differs between checkouts.

No model/device/protected-process operation, desktop control, unrelated-app
automation, PR, merge, setting change or release occurred. Full D05 acceptance,
M06/M07 memory behavior, hostile-renderer security, assistive-technology testing,
long-history performance and genuine network-blocked qualification remain open.
