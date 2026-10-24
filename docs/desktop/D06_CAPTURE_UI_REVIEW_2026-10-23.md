# Independent private capture UI/native export review, 2026-10-23

Partial D06.02/.03/.06/.07, issue #28. Reviewer `/root/resource_metrics_review`, claim `6369434357`, separate `review/d06-capture-ui` / `source-capture-ui-review` worktree. This is source review, independently executed synthetic checks, and separately attributed inspection of author-generated native evidence. It is not human acceptance or full D06 completion.

## Frozen sources and findings

Base `8e55a98e29235dbc28336022ad3a17f1378747eb`; root shared revoke `81af89793bca220ac75a7eb3c7adc732ee58d631`. UI author source `3e6e1115917d7582d161be0528ea2ed77df92ee8`, followed by `61ac05c8f20a943eb87da3e7b8b4177a20d3bdb4`, `fec3649bac3a631d27cf5d84f0ea0bddd06c86af`, `27136c7821e5dc93a980a094cd392294951004b6`, `0a10bcae02beb324a00bd4fd12579c55597ff4dc`, `b08625f4d7be98d04df8791382492a3c15d98532`, `741abd11f84c57a23fbf406f7f29f2a51b17e2e1`, and final production `4c954dfb294b51a261a6759ac4af47f62a34aa4c`. Final reviewer source head before this document: `b374ce0a13339e8edce0230a734d503a851a13e3`. No reviewer production edits.

- **Fixed P2 consent race.** At `27136c7`, actual gameplay Controller metadata clear/disable launched private revocation without awaiting the entire metadata operation. Holding the actual mocked `trace_clear` effect allowed revocation to finish, then a new private grant, then the older clear to remove native consent while UI still said enabled. Independent failing regression `bdb5481016cd92c554509b626b71acee3b4d604e` exercises the real controllers and main subscription derivation. Retained failure log SHA256 `3bc09826b54203b4cbe60c0fec9e12dc5d54fc054b84006180e616817194c954`. An initial test setup omitted waiting for initial context revocation; that setup failure was corrected before this product failure was demonstrated.
- Author repair `b08625f` synchronously clears presentation and queues owner revocation plus the whole metadata operation/read/finally on the private control chain. Independent adaptation `76ae0e515281d93d585602a541ba09523d735115` forwards the new work callback, expects the barrier busy, and preserves no-early-native-enable and truthful-final-consent assertions. It also verifies thrown metadata releases the barrier, unavailable revocation still executes metadata and reports unknown consent, and same-Scope session reopening fences grants and stale completion. PASS. The original failing commit remains immutable historical evidence.
- **Fixed narrow raw-text overflow.** Source inspection identified absent wrapping for opened private raw `<pre>` elements. Author's clean `741abd1` native run measured horizontal and nested overflow in actual generation request at 620 pixels. Author fix `4c954df` adds scoped wrapping/min-width CSS, leaving encoded JSON/export bytes unchanged. Final native evidence below passes both opened request and exact export text. Earlier collapsed-panel renders did not qualify these states.
- Initial App formatting failure was fixed in `27136c7`; final formatting passes. Author's originating native-session + Scope fences for captured receipt navigation were reviewed; actual controller tests cover coincident turn IDs, reopened same-Scope sessions, and delayed navigation after switch.

## Boundary review

Native `capture_preview` accepts strict selection only, performs the actual Host capture read, and validates retained status, identity, shape and bounds. Renderer bytes and paths are not trusted as export input. Native capture broker is separate from ordinary inspection export: maximum two preview records and 1 MiB aggregate encoded files **including manifests**. Cancelled/expired previews held by outstanding Arc/save/picker holders remain charged until released. Access TTL is 300 seconds from creation, not a deletion timer. Transient serialization/IPC/render copies are outside this retained-byte cap.

Save uses opaque native token plus explicit second plaintext consent and native folder selection. It reuses fixed filenames, guarded staging handles, create-new/nonoverwrite and atomic publication. Lease/revocation checks fence late work; already finalized publication can win concurrent cancellation. Saved exports, detached clones, paging and backups are not erased. Native context/window invalidation and late-token revocation were inspected and covered by synthetic tests. No arbitrary execution, server, renderer-selected filesystem path, or normal-build test provider was introduced.

Full details are shown only in acknowledged Lab omniscient presentation. Actual generation context remains actor-filtered by Rust; inspection grants no character knowledge or generation access. Raw JSON renders as escaped React text. Historical source IDs/budgets and raw outputs are separately labeled; validated plans/accepted candidates are staged evidence, accepted receipts remain separate, and exact reconstruction is explicitly false. Memory maintenance and model reasoning/attention are unavailable. Healthy shared revoke is owner-scoped; existing poisoned trace-control recovery globally clears/disables the untrusted ring. This exceptional policy is not owner-only erasure; see the separate shared revoke review.

## Reviewer-executed checks

Windows x64 10.0.26300.0; Rust/Cargo 1.93.1; existing Node 24.22.1, TypeScript 7.0.2, esbuild 0.28.2, Ajv 8.20.0, Prettier 3.9.10, React 19.3.1. Existing dependencies reused via ignored junction; no installation. Own D target and UUID TEMP/TMP; development/test debug=0, incremental=0, locked/offline Rust. Output root was task-local `capture-ui-review`; generated logs/bundles remain local.

From `apps/desktop`, with Node on PATH and `LOCALLORE_CHECK_OUTPUT_DIR` set to a task-owned output folder:

```powershell
node verify-frontend.mjs
node node_modules/prettier/bin/prettier.cjs --check ui/*.tsx ui/*.ts ui/*.css *.mjs
node check-capture-review.mjs
```

All PASS on final source. Verifier includes strict TypeScript, 25 original native request fixtures + four action builders against current Rust schema, bounded errors, actual MOCK capture/gameplay controllers, stale/session/observer fences, hostile wire replies, second-consent token save, native hook exclusion in normal bundle, existing archive/evaluation/inspection controller checks. These are headless/static/controller checks, not native WebView execution.

From repository root, using an explicit own `$target`:

```powershell
cargo +1.93.1 test --manifest-path apps/desktop/src-tauri/Cargo.toml --all-targets --locked --offline --target-dir $target
cargo +1.93.1 test --manifest-path apps/desktop/src-tauri/Cargo.toml --features dev-harness --all-targets --locked --offline --target-dir $target -- --test-threads=1
cargo +1.93.1 clippy --manifest-path apps/desktop/src-tauri/Cargo.toml --all-targets --locked --offline --target-dir $target -- -D warnings
cargo +1.93.1 clippy --manifest-path apps/desktop/src-tauri/Cargo.toml --features dev-harness --all-targets --locked --offline --target-dir $target -- -D warnings
cargo +1.93.1 fmt --manifest-path apps/desktop/src-tauri/Cargo.toml -- --check
git diff --check
```

Default: **45 passed, 1 existing privilege-dependent ignore**. Dev serial: **47 passed, 1 same ignore, plus 2 integration tests passed**. Both strict Clippy modes and formatting/diff PASS. Native tests include actual production Host/Play with fixed synthetic providers and native capture/export broker/writer/lease/cap/TTL checks; they are not native UI execution.

An initial final dev parallel run had **46 passed, 1 failed, 1 ignored**: unchanged `evaluation::tests::boundary_cancel_resume_old_operation_and_retired_lease_are_fenced` exceeded its existing 1000×5ms polling boundary. Its isolated exact rerun passed, then the entire serial suite passed. Failure log retained; no timing threshold or production source changed. This is observed suite scheduling sensitivity, not claimed universally resolved flakiness. Earlier pre-fix checks remain historical and are superseded by these final runs.

## Separately attributed native render evidence

Author executed invisible application-owned WebView2 harness at clean `4c954df`, folder suffix `capture-native-d9098268-aba1-4cd5-9d78-1066ac48b34b`: **73 distinct assertions, 15 PNGs, two actual process launches/restart**, fixed synthetic provider through production Host/Play, fixed post-selection picker doubles. Summary reports passed, actualProcessRestart=true, realModelGeneration=false, desktopControl=false; exact saved bytes/manifest verified. Only expected bounded native errors Agency and Cancelled; no frontend errors. Reviewer read summary and semantic snapshots; 26 available source input hashes match reviewer checkout. Normal reviewer `dist/app.js` differs from author's development harness bundle as expected.

Reviewer visually inspected final `d06-private-open-request.png` and `d06-private-open-export.png`: actual 620px raw text wraps within panel, readable labels and text; each semantic snapshot reports horizontalOverflow=false and nestedOverflow=false. Also inspected four earlier clean `0a10bca` native PNGs (context, preview, narrow cleared panel, fallback) for consent/state/staged labels; these are historical pre-barrier evidence. App-owned render images were read from disk, never desktop captures. Reviewer did not execute the native WebView cohort or automate system dialogs.

Reproduce author native lane separately, from `apps/desktop`, with task-owned directories:

```powershell
$env:LOCALLORE_D06_CAPTURE_ARTIFACT_ROOT = '<own artifact root>'
$env:LOCALLORE_D06_CAPTURE_TARGET_DIR = '<own Rust target>'
node capture-harness.mjs
```

This builds the dev-only harness and launches the invisible app twice; it is not required for the reviewer controller reproduction. No real model, real picker interaction, Android/device qualification, network-block experiment, physical erasure, human acceptance, settings change, release or protected-chat action occurred in this review. Existing Android code was not modified; no Android build executed by this reviewer.

Final fetch observed accepted main `aec8ad02a662b87b960723da8878f4ead4f0a28d` (#93). Its Host/schema/generated-types match the imported shared revoke source; coordinator owns final integration and broader compatibility checks. No remaining concrete blocker found in this frozen slice after the documented repairs. Next runnable task: coordinator integrates unchanged author production plus independent regression/review evidence, reruns integration gates, and records partial D06 disposition; full milestone acceptance and missing shared memory capabilities remain with their owning tickets.
