# Native long export paths, 2026-10-23

Refs #31 D09.05/.06, #30 D08.01/.07. Root claims
[#30](https://github.com/OptimumAF/LocalLore/issues/30#issuecomment-6371190523),
[#31](https://github.com/OptimumAF/LocalLore/issues/31#issuecomment-6371207267).
Source is separate `impl/d09-native-long-path`, based accepted main b3543d6.
RED regression `a8d4583`, fix `7573d24b30d56e2079b73c156b908a16d24738c7`,
independent review `cd2ddd8` imported as `e8609c0`, accepted main e7ca17a
normally merged at `11520c6357f6dae2b18612dcb83e728bfb9239b4`.

## Demonstrated failure and correction

An actual serial native development test under a longer owned TEMP root returned
archive result `failed`/`Io`, with cleanup_complete=true instead of exported.
The short-root default run passed. Added diagnostic output preserved the actual
result without changing the assertion. A deterministic regression opens an
actual staging file under a Unicode path exceeding290 UTF-16 units, writes and
syncs fixed synthetic bytes, then calls the existing handle-finalize function.
It failed with Io before the fix. Its first fresh-checkout compile also failed
because normal frontendDist was absent; that setup failure remains separate.
Built the normal frontend with existing locked dependencies, then obtained the
actual RED result. No failure is counted as a test pass.

The fix canonicalizes the existing destination parent, then joins only the
original native-selected absent filename. On this Windows system canonicalize
supplies the extended path form. All production callers retain destination
ancestor pins through the call. Source remains the actual held staging handle;
SetFileInformationByHandle still uses ReplaceIfExists=false, with no close/reopen
gap or path-move fallback. The [Microsoft structure reference](https://learn.microsoft.com/en-us/windows/win32/api/winbase/ns-winbase-file_rename_info)
documents absolute destination names and refusal when replacement is disabled.
The exact regression now passes, verifies exact saved bytes, and verifies a
second actual staging handle cannot replace the existing destination: both
original and refused-stage bytes remain unchanged. No system long-path setting
was altered and no path-length assertion was weakened.

The shared native helper also serves inspection/private captures and model-copy
publication. This packet executes no model operation. Archive input retains
its drive-only prefix fence; arbitrary source/target paths are not renderer
capabilities. The independent [review](D09_NATIVE_LONG_PATH_REVIEW_2026-10-23.md)
records caller pin lifetimes and unexecuted UNC/network/substitution schedules.
The new direct regression tests handle rename/nonoverwrite, not parent-pinning
concurrency. Existing pinning/collision/cancellation tests remain intact.

## Actual checks

Windows11 Pro10.0.26300; Rust/Cargo1.93.1; Node24.22.1. Existing locked
dependencies and WebView2 only; task-owned D-drive targets/TEMP/artifacts,
debug0/incremental0. No model/worker, Android/device/ADB, desktop control,
screenshots, window activation or protected resource operation occurred.

```powershell
node apps/desktop/build.mjs
cargo +1.93.1 test --manifest-path apps/desktop/src-tauri/Cargo.toml --locked --offline exports::tests::long_unicode_target_renames_the_actual_handle_without_replacing_an_existing_file -- --exact --nocapture
cargo +1.93.1 test --manifest-path apps/desktop/src-tauri/Cargo.toml --locked --offline -- --test-threads=1
cargo +1.93.1 test --manifest-path apps/desktop/src-tauri/Cargo.toml --features dev-harness --locked --offline -- --test-threads=1
cargo +1.93.1 clippy --manifest-path apps/desktop/src-tauri/Cargo.toml --all-targets --all-features --locked --offline -- -D warnings
node apps/desktop/archive-harness.mjs
```

The harness command requires trusted own LOCALLORE_D08_ARTIFACT_ROOT and
LOCALLORE_D08_TARGET_DIR, as in its existing instructions. It builds dev-only
hooks and drives the actual frontend/controller/native IPC. Pickers and the
Play provider are fixed synthetic doubles; native WebView rendering is actual.
It creates invisible/unfocused app-owned surfaces and uses CapturePreview,
never desktop capture/input. This is not headless rendering or real inference.

| Check | Actual result |
| --- | --- |
| New actual long Unicode handle regression | RED Io -> GREEN; payload and nonoverwrite assertions unchanged |
| Native default | 47 PASS, one existing symlink-privilege ignore |
| Native dev | 49 PASS +2 contract PASS, same one ignore |
| Strict all-feature native Clippy/fmt/diff | PASS |
| Native suites/strict repeated after accepted Cargo workspace/main merge | Same 47 /49+2 PASS, one existing ignore |
| Actual archive WebView/IPC at clean7573d24 | 63 distinct assertions,17 app-owned PNGs,five process launches including restart PASS |

Root inspected narrow export preview, pending import and restarted conflict
renders: labels, disabled actions/cancel, revision/receipt/observer and retained
original-story conflict are coherent; long hashes wrap and narrow view remains
scrollable. These render checks do not independently qualify a >290-character
UI-selected destination; the direct actual handle regression supplies that
path proof. Shutdown Chromium Error1412 observations remain in the raw log,
separate from bounded frontend/native error reports. No full D09 acceptance,
new two-path build, physical-device or real-model result is inferred.

## Private evidence bindings

All raw logs/images remain local and ignored. SHA256:

| Artifact | SHA256 |
| --- | --- |
| actual long-path RED | `9aafa4a83bb3ecd97e4c5c13e20ba985fcd7c35992d14cf8da91a245ae95ca21` |
| exact regression GREEN | `67e2a4d2383cfadd6b78bb1cc0d5ea64539bba2eb814b07ed9e798004e7ad7f8` |
| integrated native default | `eeffbbf27d20e4d8123f0e97a7db94c45214faff26af821a73761e1ab240d441` |
| integrated native dev | `3ec7375765ac7977826c36e699ece2f7aa84691ad9e958995a04dfab9b829e21` |
| archive render log | `76d1601c9da73f5e53d5a08e2f098012d63ab5ecad5b59404ff37c221c4e4b71` |
| actual native summary | `339d79dc9dde0a5d27ea836d778d6bbffb6d02047b86013affd20b845f805395` |

Owner-authorized merge is scoped to this correction. No repository settings,
approvals, releases, downloads or milestone completion are fabricated. Next
runnable work is guarded director/curated UI integration and exact package
notices, then shared memory and timeline/correction capabilities.
