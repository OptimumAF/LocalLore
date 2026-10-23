# Private capture UI and exact export evidence — 2026-10-23

Partial D06.02/.03/.06/.07 under #28, author `/root/app_storage_review`, claim `6368992741`, addendum `6369597743`. Implementation branch `impl/d06-private-capture-ui` started at accepted `4cdbc0d3823c12424720abe8d92106788b766b60`. Root owns shared backend/revoke and final integration; the author changed no core/Host/Store/schema/JNI/runtime/model-management implementation. Imported root revoke `81af89793bca220ac75a7eb3c7adc732ee58d631` as dependency `ff64d7b` only.

Final executed source: **`0a65beff3d3314e9364f140722ee1fa11d213e6b`**, clean during the final native cohort. Subsequent commits import the independent review and add evidence only. The root's newer accepted main is deliberately not merged during this frozen cohort; combined-main, Android and publication qualification belong to the coordinator.

The [contract](D06_CAPTURE_UI_CONTRACT.md) defines consent, retained-byte bounds, native selection/token/picker boundaries, exact-text export, access-time expiry and unavailable features. The [independent review](D06_CAPTURE_UI_REVIEW_2026-10-23.md) is by a different agent, not author self-approval. Full D06 and its real-model/maintenance/pause exit gates remain unchecked.

## Implemented behavior

- Lab omniscient presentation contains explicit future-attempt consent, strict historical detail decoding, selected actor/source/revision/reason/score/mandatory/budget evidence, collapsed raw request/output/repair/proposal/plan/candidate artifacts, and separately linked durable receipts/field diffs. No hidden reasoning or reconstructed prompt is invented.
- Session/lens/close changes clear details immediately, fence late replies, and attempt native owner revocation without requiring a fresh head. Unavailable revocation remains visible as unknown/Busy; head advancement alone preserves future-attempt consent. Metadata clear/disable shares the entire private control barrier with grants.
- Native preview reads the actual Host itself, retains exact immutable `capture.json` plus a checksum manifest, and accepts no renderer bytes/path. A second plaintext consent and native folder picker precede the existing guarded nonoverwrite atomic writer. A separate broker caps retained encoded files at two records / 1 MiB including manifests / 300 seconds from creation, checked on access. In-flight holders remain budgeted after cancellation. These are not total heap or background erasure guarantees.

## Author-executed qualification

Environment: Windows x64 `10.0.26300.0`; installed WebView2 `155.0.4283.62`; Rust/Cargo `1.93.1`; task-local portable Node `v24.22.1`; existing locked frontend dependencies reused through an ignored junction. No installation, repository settings, model weights, model execution, desktop capture/control/input, real picker interaction, device/ADB, hosted inference or protected-chat resources were used. All raw synthetic artifacts, private plaintext exports, generated bundles and targets stayed in this task's ignored D-drive outputs.

Set `CARGO_PROFILE_DEV_DEBUG=0`, `CARGO_PROFILE_TEST_DEBUG=0`, `CARGO_INCREMENTAL=0`, and TEMP/TMP to the task-owned D directory. `$target` below was the task-owned `d06-capture-ui-native`; `$node` was the existing portable `d09-build-security/node-v24.22.1-win-x64/node.exe` under the same task root.

| Lane | Actual result |
| --- | --- |
| `node verify-frontend.mjs` | PASS: normal build, strict TypeScript, 25 original native fixtures + four action builders/schema, existing controller suites, new capture suite, independent metadata barrier regression, normal frontend hook exclusion |
| `prettier --check "ui/*.{ts,tsx,html,css}" "*.{json,mjs}"` | PASS |
| Default native test suite | 45 passed / zero failed / one existing privilege-dependent ignore |
| Explicit existing ignored reparse case | One passed / zero failed |
| Final `dev-harness` native tests | 47 passed / zero failed / one same ignore, plus two harness-contract integration tests passed |
| Strict all-target native Clippy, default and all features | Both PASS, `-D warnings` |
| Native rustfmt / Git diff whitespace checks | PASS |
| Normal native build and payload marker scan | PASS: synthetic director/provider/profile/picker markers absent from normal executable |
| Final invisible native WebView2 cohort | **73 distinct assertions / 15 app-owned PNGs / two actual process launches**, initial plus restart; PASS |

Commands from the repository root (frontend commands run from `apps/desktop`):

```powershell
cargo +1.93.1 test --manifest-path apps/desktop/src-tauri/Cargo.toml --locked --offline --target-dir $target
cargo +1.93.1 test --manifest-path apps/desktop/src-tauri/Cargo.toml --locked --offline --target-dir $target models::tests::abandoned_import_reparse_file_is_preserved -- --exact --ignored
cargo +1.93.1 test --manifest-path apps/desktop/src-tauri/Cargo.toml --locked --offline --features dev-harness --target-dir $target
cargo +1.93.1 clippy --manifest-path apps/desktop/src-tauri/Cargo.toml --locked --offline --all-targets --target-dir $target -- -D warnings
cargo +1.93.1 clippy --manifest-path apps/desktop/src-tauri/Cargo.toml --locked --offline --all-targets --all-features --target-dir $target -- -D warnings
cargo +1.93.1 fmt --manifest-path apps/desktop/src-tauri/Cargo.toml -- --check
git diff --check
```

The normal native executable was built without `dev-harness` and its bytes checked for absence of `MALFORMED_SYNTHETIC_DIRECTOR`, `synthetic-private-capture`, and `LOCALLORE_D06_CAPTURE_EXPORT_ROOT`. The normal frontend verifier separately checks development command/journey markers. This combines actual normal compilation/marker checks with source cfg review; it is not a claim that a development build is safe to distribute.

Actual native command, from `apps/desktop`:

```powershell
$env:LOCALLORE_D06_CAPTURE_ARTIFACT_ROOT = '<task D root>/d06-capture-ui-artifacts'
$env:LOCALLORE_D06_CAPTURE_TARGET_DIR = '<task D root>/d06-capture-ui-native'
& $node capture-harness.mjs
```

The fixed trusted provider returns synthetic structured outputs through **actual Host → production Play → compiler/intent/validation/narration/commit**, not an alternate engine. The app's actual CaptureController/React panel and native IPC read those retained hook artifacts. Fixed development picker doubles select one task-owned destination or cancel after selection. The journey calls the actual Host through IPC to submit the synthetic free-text attempts; it does not qualify normal real-model loading/composer inference. MOCK tests use the actual controllers with a simulated Gateway and are labeled separately.

The new native tests compare capture-on/off canonical events, proposal and narration, and the **entire canonical projection `state.json`** after actual Host commit. Wall-clock Play stage timings are separate provenance, so this is not whole-receipt byte determinism across two executions. Other checks cover actual malformed director output plus repair, rejected Agency proposal without a candidate, rejected narrator output plus fallback candidate, actual provider-poll observation before cancellation, unchanged canon through consent/read/preview/export, and foreign/stale/unretained private selection refusal.

The final journey verifies the real fixture's player-known `SECRET-TIDE-731` remains in selected context, while the undiscovered beacon-mark proposition and Mira's private relic belief are absent **before capture/model input**. It verifies NPC presentation clearing, historical basis versus advanced head, staged-versus-durable labels, exact second-consent save, restart with accepted history but disabled/private-attempt-empty capture, and bounded expected native errors. Initial-stage errors are exactly one Agency and three Cancelled records; every error must be native and one of those categories. Restart errors are empty. No unexpected error category was waived.

The final 620-pixel opened request/export PNGs, context-selection table, narrow cleared view and restart view were inspected with `view_image`, using only app-owned harness images. Prompts/export text wrap without horizontal/nested overflow; raw artifacts start collapsed in ordinary presentation, and markup is inert escaped React text. Native TTL/cap tests use actual broker time/budget boundaries; expired/truncated display decoder cases are MOCK, not ten-minute wall-clock native UI waits.

## Final local evidence binding

Task-local run: `d06-capture-ui-artifacts/capture-native-3167cac7-05c5-41d9-9321-c8901f69a99b`.

- `summary.json`: SHA256 `d871ac886c5ebde99aa3edc4d4f5cdceb2ebd9b619500336f503688544952a20`.
- It records `sourceRevision:0a65beff3d3314e9364f140722ee1fa11d213e6b`, `sourceDirty:false`, full source-input/binary hashes, the two reports, 15 captures and `exactSavedExportVerified:true`.
- The runner checks the selected directory has only `capture.json` and `manifest.json`; saved capture bytes equal the visible preview text and declared length/SHA256. No raw trace/PNG/private export is committed to Git.

Selected SHA256 values from that final input inventory (desktop-relative paths):

| Input | SHA256 |
| --- | --- |
| `ui/capture-model.ts` | `dfd26aa6cbcee92d1f24f27bfb6c9ad73ff570f5e9e297215e0122e603679a91` |
| `ui/capture-controller.ts` | `1186c6a4b11be13048096efc703732cf037dfc7ff75a2c6577ae35654b57353e` |
| `ui/CapturePanel.tsx` | `cac1354fbb211bfbbde9a246cafdce2c608971bf9518542eb494dc0c26e39961` |
| `ui/controller.ts` | `68979d1facb896947d08b48741f0c7c0300f970626680f8c1e61ccb5b0c83340` |
| `src-tauri/src/capture_exports.rs` | `dea75346b90d0fd1a9fc6f461912a13d350edb47dc46eda9daa163d04d5217e5` |
| `src-tauri/src/exports.rs` | `3330957997b5ad0ee487dd90c88f36c1a481ab68333bbbd4ddf3a81878e6f487` |
| Shared Host dependency | `f8993017b36ec3422dbea01e99e032eb39d2b3d69165359d459a3179db386fb7` |
| Development `dist/app.js` | `86f7ea6f6d1584dee824ec8d26ed98ea0b8588cdcaa6ee4fdbc49e7e37a5d633` |
| Tested native development executable | `5d6e9cd5a9d9e8b3e2ea60cf539096c9ca978da84d18af17b0f80878f2c877c6` |

## Failures retained and corrections

All old task-local runs remain available. Their PASS results are scoped to their original inputs; they do not supersede later findings.

- `e89458aa-53a4-4112-a785-3365221f8c90`, source 3e6e111: stopped at the preview checkpoint with generic Transport and no gameplay errors. The checkpoint duplicated full detail/preview/DOM payloads against the existing 256 KiB evidence limit. 61ac05c bounded the evidence shape to one exact preview text, artifact identity summaries and 16 KiB DOM text, and preserved the original failure-check name before failure capture. The production capture/export cap was not relaxed.
- `c50b9e53-cb5a-4152-a0ca-2ae45787412c`, source 61ac05c: unsupported synthetic `I wait.` correctly produced ClarificationRequired instead of the intended cancellation case. fec3649 uses the existing supported `I wait for one tide tick.` and a development-only actual provider-poll marker before Cancel. No intent/Agency gate changed.
- `f67958c0-b9f6-4ae8-9072-22c2d9fe04b8`, source fec3649: actual cancellation and revocation passed, then the harness supplied nonexistent width/height arguments to the fixed viewport API. 27136c7 uses its existing preset. This was a harness invocation error.
- Clean 27136c7 `d6153e70-3046-4014-8860-c510ff25f1d7` passed 54/12; clean 0a10bca `776455ec-c740-4f45-80fb-958e3cfb318c` passed 55/13. These preceded independent metadata ordering and opened-text coverage, so they are historical rather than final qualification.
- Independent reviewer `bdb5481` demonstrated an actual deferred metadata-clear/new-private-grant race at 27136c7. Root-relayed failure-log SHA256 is `3bc09826b54203b4cbe60c0fec9e12dc5d54fc054b84006180e616817194c954`. b08625f fixes the whole-operation barrier and originating session/scope navigation fences. Reviewer adaptation 76ae0e5 (imported unchanged as 6e83692) and author controller regressions pass. The independent report records its own commands/failures; those executions are not attributed to the author.
- Clean 741abd1 `27bb9247-5625-4ef3-b036-2b65a767d732` measured actual opened-generation-request horizontal and nested overflow at 620px, with no native errors; its app-owned PNG shows the long prompt clipped to the right. 4c954df adds only scoped wrapping/min-width styling. Corrected 4c954df `d9098268-aba1-4cd5-9d78-1066ac48b34b` passed 73/15, followed by final 0a65beff 73/15 with actual fixture knowledge checks and full-projection test.

The native processes also printed Chromium's class-unregistration 1412 line on exit; reports, assertions and artifact checks still passed. This is preserved output, not counted as an application render/unhandled error or silently rewritten as an app failure.

Next: coordinator reconciles newer accepted main, reruns combined rendering/platform checks, and reviews exact publication inputs. No merge/release/human approval/full D06 checkbox is claimed by this handoff.
