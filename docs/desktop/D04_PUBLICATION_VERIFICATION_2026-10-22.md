# Desktop local-model publication verification

Refs #25 D04.01–.06 partial and #9 M05 integration. Depends on accepted core
PR #51 and runtime PR #52. This publication wires existing durable Host/Store
and the fixed CPU provider into native model management and explicit free-text
Play. It adds no second inference, memory or storage authority. Quality, actual
network-blocked play, sustained performance and packaging remain unqualified.

## Final actual native result

Clean source `dd3de5739ced38af7d67cd7354bd7136798a0b63` passed **31 distinct
assertions,10 app-owned WebView2 PNG captures and a real executable restart**.
It uses actual frontend controller actions/native IPC and the approved local
CPU model. This is native WebView rendering, separate from headless/browser,
engine-only and model-free native tests. No desktop screenshot/input/window
activation or unrelated application automation was used.

Local artifact suffix:
`desktop-publication-artifacts/model-native-62b40bf6-71ee-4dbd-8c87-b44886fe2fee`.
Summary SHA256:
`be82d7432ee1f5ecd427be9697305f5a077ea257b999a04e3b9cd46c41d20aa5`.
The curated synthetic summary is
[D04_PUBLICATION_EVIDENCE_2026-10-22.json](D04_PUBLICATION_EVIDENCE_2026-10-22.json).
It contains exact source/frontend/native executable/worker input hashes and
bounded semantic reports, with the executable path replaced by a placeholder.
Raw images/databases/logs stay local and ignored. No private stories or personal
paths are published. Subsequent controller regression/report additions do not
change the production frontend/native behavior exercised by that run.

The coordinator inspected the final receipt-with-header, invalid-action and
restarted images. Story selection/revision, loaded/unloaded model, receipt,
fallback label and visible error are coherent and readable. All10 semantic
snapshots report no horizontal overflow. The legacy JSON diff remains verbose;
the separate D05 typed inspector is not part of this publication.

The journeys exercise hash/load cancellation, pending noncanonical state, real
free-text potion transfer, deliberately lost commit acknowledgement and exact
key recovery, double-spend refusal, explicit Dialogue, unsupported-action
clarification, missing ability, active generation cancellation, absent-NPC secret
isolation, new story/original-story resume, unload/reload and process restart.
After restart the spent potion and v2 provenance survive; exact stored retry
works without a loaded model. Unload never selects fake inference. Both accepted
narrations use the visibly labeled safe engine fallback (**2/2**), with no claim
of satisfactory generated prose or arbitrary-language interpretation.

Actual worker SHA256:
`add98cf02249141942c88e2517c2f5a4c9a91dbe9638bf7d3cd30c26916bce87`.
Pinned llama.cpp: `620d2225cc436ab0b001e3200e590e3b286ef9ab`.
Already approved Qwen3-0.6B Q8_0 model:639446688 bytes, SHA256
`9465e63a22add5354d9bb4b99e90117043c7124007664907259bd16d043bb031`.
CPU4 threads/context4096/output350 per role/GPU0/one repair/120s turn deadline.
Manifest `01ad542001b04a96f4a8ed6c841be1866eb025350836e0c5d0a4969fdb361d38`.
The source model is read-only and unchanged. The launcher reuses one verified
previously imported app-owned Unicode/space-path copy, avoiding another640MB copy.
The new fixed worker was consciously re-pinned in the staging helper and journey.

## Review findings and corrections

The source review found poisoned runtime locks could appear loaded and leave
unload permanently stuck. Private lifecycle helpers now classify poison as
failed, recover only to drain/reap, and finalize metadata before returning the
cleanup error. A synthetic poisoned owner tests those helpers and the manager's
actual completion path without a real model. Unload is explicitly described as
waiting for cleanup; its cancellation control is unavailable rather than
promising to interrupt required cleanup.

Process death during import could leave `.import-<GUID>.part` files. Later import/
load now scans at most128 model-root entries, deletes only that exact staging
namespace through a checked ordinary-file DELETE handle under a pinned root,
and preserves active locked copies, reparse entries, unrelated files and the
approved final model. Cleanup is bounded/best-effort; it is not a generic file
cleanup service. Default stale/active/unrelated tests pass; privilege-dependent
symlink preservation is separately marked ignored then explicitly executed here.

The first new native launch passed the reused model's parent directory, causing
an honest InsufficientSpace error before any accepted turn. The corrected second
launch reached accepted gift/dialogue and then exposed a real controller race:
periodic model status reads could supersede the final awaited status refresh,
so modelAction resolved briefly with the previous loaded state. The production
controller now stops polling before its definitive post-action refresh in both
success and error paths. A deterministic actual-controller test reproduces both
failures on old source and passes with the fix. It holds/reorders status replies
and manually ticks only test-process intervals; no real model/timing guess is
needed. Both failed artifact folders/logs remain local. The complete third
native launch above passes after the fix.

## Reproduction and exact checks

Environment: Windows11 Pro10.0.26300, i7-12700K12 cores/20 logical, about64GiB;
Rust/Cargo1.93.1, Node23.10.0/npm11.2.0. Existing local Node is not supported-LTS
qualification; D09 owns that gate. All Cargo commands use locked cached offline
dependencies, dev/test debug0 and incremental0, with task-owned build/temp roots.

From apps/desktop, set these trusted launcher-only inputs (not renderer fields):

```powershell
$env:LOCALLORE_D04_WORKER_SOURCE='<reviewed-build>/locallore-llama-worker.exe'
$env:LOCALLORE_D04_MODEL_SOURCE='<approved-existing-model.gguf>'
$env:LOCALLORE_D04_REUSE_MODEL_ROOT='<owned-directory-containing-Qwen3-0.6B-Q8_0.gguf>'
$env:LOCALLORE_D04_ARTIFACT_ROOT='<task-artifacts>'
$env:LOCALLORE_D04_TARGET_DIR='<task-native-target>'
node model-harness.mjs
npm run check
npm run format:check
```

Omit REUSE_MODEL_ROOT for a new import journey with adequate free space; its value
is the model directory itself, not its parent. Interactive native picker UX is
compiled but was not driven; the development harness supplies fixed synthetic
selection cases through its narrowly gated native bridge. It exposes no generic
file/shell/code execution or remote debugging server. Normal bundles/handlers
exclude these hooks. The fixed worker staging helper verifies exact bytes before
writing the packaged filename; no model is bundled or downloaded.

Native checks from repository root, with `--target-dir <task-native-target>`:

```powershell
cargo test --manifest-path apps/desktop/src-tauri/Cargo.toml --locked --offline
cargo test --manifest-path apps/desktop/src-tauri/Cargo.toml --features dev-harness --locked --offline
cargo test --manifest-path apps/desktop/src-tauri/Cargo.toml --features dev-harness --locked --offline models::tests::abandoned_import_reparse_file_is_preserved -- --ignored --exact
cargo clippy --manifest-path apps/desktop/src-tauri/Cargo.toml --all-targets --locked --offline -- -D warnings
cargo clippy --manifest-path apps/desktop/src-tauri/Cargo.toml --all-targets --features dev-harness --locked --offline -- -D warnings
cargo fmt --manifest-path apps/desktop/src-tauri/Cargo.toml -- --check
```

Results:17 default tests passed/1 ignored;19 development tests passed/1 ignored,
plus2 wrapper tests; the exact ignored reparse test separately passed. Strict
default/dev Clippy and formatting passed. Frontend check includes strict TS,
25 original schema fixtures/current builders, hostile wire/keyboard/errors,
real-versus-fake retry regression, the deterministic terminal-refresh regression
and exclusion of dev hooks from the normal bundle. Formatting passed. Normal
frontend assets and default native executable are restored after the harness.

Expected fault categories are retained in bounded synthetic error buffers.
WebView2 emitted a class-unregister teardown message (Chrome_WidgetWin_0, error1412)
after each successful process report; this is retained in the local log, not
presented as clean stderr. No frontend RenderError/UnhandledError was observed.
Earlier joint legacy/native/headless/durable/export/Android checks are pinned
separately in D04_NATIVE_VERIFICATION and the core report, not relabeled as new
execution against this publication. Full integrated regression continues as
D05/D06 and shared memory land. No whole D04/M05/desktop completion or release.
