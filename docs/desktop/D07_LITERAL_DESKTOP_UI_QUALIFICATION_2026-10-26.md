# Protocol3 desktop comparison reader qualification

Scope: D07.06/.04 supporting consumer work, base accepted PR194 / `e8e30cef`.
Qualified production/render source `56be5743`; final compatibility checks are
terminal with clean/unchanged source. This adds actual desktop inspection of protocol3,
not execution or selected-case reruns for that protocol.

## Behavior and authority

The existing native reader retains a closed V2/V3 capability variant in the same
lease, token, worker, TTL and close lifecycle. Opening tries the actual validated
readers; invalid V2 sources keep their existing failure category. Source protocol
comes from the retained validated snapshot. Summary/evidence use the matching
typed capability and the shared actual Store/Query2/receipt/capture/raw readers.
There is no new engine, inference owner, persistence schema, permission or IPC.

The frontend accepts exactly protocols2/3, requires source/report version
agreement, checks the complete12-key construction tuples/order and binds each
row's descriptor to its physical arm. V3 estimates are required nullable;
V2 retains its optional-array contract. Literal metrics remain separate from
memory fields. Failed turns can retain validated input; that does not approve
their outcome or narration. Guards/dependencies display privacy/construction
checks as not applicable. Unknown roles/timing remain unknown.

Protocol3 read tokens cannot become selected1 execution permission. Native
preparation refuses3 before taking/revoking its reader capability, leaving the
same source usable. App supplies selected-source identities only for2; the
selected pane explains3's unavailable rerun instead of asking for another report.
Existing selected jobs/recovery remain available. The shared report metadata
no longer advertises an unimplemented GUI; selected3 remains explicitly absent.

Observer changes use the existing private-data clearing controller path. Actor
queries remain actual Rust Query2 pages; raw receipts/captures/outputs remain
omniscient-only. Inspector permission never alters character knowledge or
generation access. No canonical state or live story is modified by inspection.

## Frozen tests, failures and corrections

- Native packet895f30dc, adopted d6215342/registration7d8972dc, precedes dispatch:
  actual scripted producer/native APIs RED0/4 in12.19s, V3picker fails
  EvaluationIntegrity. Root2de1dfbd GREEN4/49.09s. Typed source/report, actual
  Store/Query2/receipt/capture, early actor refusal, preconsumption selected3
  denial, close/retire/no late capability, same-manager2/3 switch and byte
  inventories are covered. These are native Rust tests, no IPC/WebView/model.
- Frontend packet39586d34, adopted ccc87d5d, precedes decoder/presentation:
  old source RED90/11 across101 checks. Many negative3 cases pass merely because
  old code rejects3 wholesale; the positive failures and protocol-equality
  failures are the meaningful baseline. Production2d0f18a0 adopted aab77aa3
  reaches100/1; the remaining fixture attempted to mutate a correctly frozen
  decoded object. Correction118f08e7 sets private prose on the raw fixture
  before decoding, preserving its assertions and immutability. GREEN101.
  Synthetic DTO/mocked-controller/headless React only, no Rust/IPC/render proof.
- Initial actual owned WebView cohort7c524a44 passes60 checks in each of two
  processes and30 captures,626 fixture files unchanged. All30 were visually
  inspected; they expose two presentation defects: unsupported3's selected pane
  misleadingly asks for a report already open, and recovered table headings/
  unavailable role values break midword.
- Correction56be5743 adds only an optional display reason in the existing
  selected view/App and narrowly scoped table word wrapping; no action grant
  changes. Actual rerun passes61 checks/process and30 captures. All corrected
  images were inspected: explanation visible, recovered columns readable,
  before/after/observer/receipt/error/pending state coherent, no clipping or
  page/panel horizontal overflow found in the captured views.

No source-only author executed tests. Model-assisted reviews found no additional
concrete production defect; they are not human approvals or story quality review.

## Actual native harness evidence

The existing fixed harness gains one closed development-only environment switch,
`LOCALLORE_D07_LITERAL_COMPARISON_READER=1`. Native-owned fresh synthetic fixture
paths remain fixed under its isolated workspace. It reuses the real scripted
producer/reference, native picker doubles, actual frontend controller actions,
actual comparison IPC, and an actual selected prepare request that must refuse3
without consuming the reader. No renderer-supplied path or general execution
hook is introduced.

The app creates its own hidden, unfocused WebView/profile. Captures use that
WebView's CapturePreview, never the desktop. There is no mouse/keyboard input,
window activation, unrelated-app automation, OS dialog automation or dependence
on human clicks. The normal frontend excludes the development journey/hooks.

At56be5743, initial/restart app wall times149.066s/66.697s, both exit0 without
timeouts;61 checks each. Native build15.488s, frontend build.390s in the launcher.
Its qualification records protocol3, actual hidden/unfocused WebView2, native
IPC=true, desktopInput=false, modelExecution=false and626 unchanged fixture files.
Opening paired2scenes/24rows and rollout1scene/12rows uses fake inference,
clearly labeled. The report being opened is not a native-model experiment.

The30 semantic snapshots and30 PNGs cover open/restart, receipt, actual capture,
raw outputs, narrow layout, Mira/Sable isolation, guard missing evidence,
pending close, lost-ack unknown/recovery, source switch and finished state.
Snapshots separately record selected experiment scope/revision, gameplay
context/revision, observer, pending operation, displayed receipt, visible error,
validated source/row hashes and DOM controls. Canonical gameplay is unchanged.
Expected lost-ack evidence stays bounded/local; no private data is uploaded.

Environment: Windows NT10.0.26300 x64, PowerShell7.6.5, Rust/Cargo1.93.1,
Node24.22.1. Captured native UA reports Chrome155.0.0.0/Edg155.0.0.0,
devicePixelRatio1; full installed runtime build was not independently queried.
Native stages and images are distinct from synthetic/headless tests above.

## Reproduction

With already installed pinned dependencies, from apps/desktop:

```powershell
node check-literal-comparison-reader.mjs
node verify-frontend.mjs
$env:LOCALLORE_D07_COMPARISON_READER_ARTIFACT_ROOT = Join-Path (Get-Location) 'artifacts/literal-reader'
New-Item -ItemType Directory -Path $env:LOCALLORE_D07_COMPARISON_READER_ARTIFACT_ROOT -Force
$env:LOCALLORE_D07_COMPARISON_READER_TARGET_DIR = Join-Path (Get-Location) 'artifacts/literal-reader-target'
$env:LOCALLORE_D07_LITERAL_COMPARISON_READER = '1'
node comparison-reader-harness.mjs
```

The launcher requires a clean source, creates new artifact leaves, builds
locked/offline with jobs1 and debug0, and preserves process output, snapshots,
rendering metadata, PNGs, hashes and qualification locally. It downloads nothing.
Set the literal switch to0 for the existing protocol2 harness. Following any
development harness run, rebuild/verify the normal frontend before the final
normal native build. The coordinator serialized every heavy command and guarded
clean/unchanged source throughout.

From repository root, native unit oracles:

```powershell
cargo test --locked --offline --manifest-path apps/desktop/src-tauri/Cargo.toml --all-features --jobs 1 --bin locallore-desktop-spike evaluation::comparison::literal_read_review:: -- --nocapture --test-threads=1
```

## Final checks and limits

Final compatibility at `56be5743`:

| Check | Result |
|---|---|
| Full frontend/type/controller/normal-hook checks, including101 new strict-wire/headless cases |PASS /11.864s command wall time|
| Native comparison lifecycle/source/evidence tests |14 PASS /227.01s|
| Existing selected lifecycle/ownership/read/recovery tests |14 PASS /185.13s|
| Shared V3 public read capability |4 PASS /29.95s|
| Genuine retained native3 read without optional model feature |1 PASS /33.89s, no source byte changes|
| Evaluator strict all-target Clippy |PASS /20.51s|
| Evaluator format |PASS /4.250s command wall time|
| Native all-feature/all-target strict Clippy / format |PASS /11.30s; format PASS|
| Restored normal native build, unlaunched |PASS /17.29s|
| Android Rust host / dependency graph |20 PASS /1.82s; no evaluator/runtime/Tauri edge|

No selected test was counted as a pass without execution. The retained native
history gate requires the explicit pinned `LOCALLORE_LITERAL_NATIVE3_HISTORY`
fixture qualified previously; it does not create a native result or start a
model. An existing fixed comparison-worker panic prints its static message and
is contained by its passing lifecycle test; it is not a production crash.
No new Android SDK/JVM/ABI/device checks occurred.

From repository root, compatibility commands, with the same locked/offline,
jobs1/debug0 isolated targets and local temporary directories:

```powershell
cargo test --locked --offline --manifest-path apps/desktop/src-tauri/Cargo.toml --all-features --jobs 1 --bin locallore-desktop-spike evaluation::comparison:: -- --nocapture --test-threads=1
cargo test --locked --offline --manifest-path apps/desktop/src-tauri/Cargo.toml --all-features --jobs 1 --bin locallore-desktop-spike evaluation::selected:: -- --nocapture --test-threads=1
cargo test --locked --offline --manifest-path crates/locallore-eval/Cargo.toml --features local-model --jobs 1 --test literal_desktop_read -- --nocapture --test-threads=1
cargo test --locked --offline --manifest-path crates/locallore-eval/Cargo.toml --jobs 1 --test literal_desktop_native_history -- --ignored --nocapture --test-threads=1
cargo clippy --locked --offline --manifest-path crates/locallore-eval/Cargo.toml --features local-model --all-targets --jobs 1 -- -D warnings
cargo fmt --manifest-path crates/locallore-eval/Cargo.toml --all -- --check
cargo clippy --locked --offline --manifest-path apps/desktop/src-tauri/Cargo.toml --all-features --all-targets --jobs 1 -- -D warnings
cargo fmt --manifest-path apps/desktop/src-tauri/Cargo.toml --all -- --check
cargo build --locked --offline --manifest-path apps/desktop/src-tauri/Cargo.toml --jobs 1
cargo test --locked --offline --manifest-path crates/locallore-android/Cargo.toml --jobs 1 --lib -- --nocapture --test-threads=1
cargo tree --locked --offline --manifest-path crates/locallore-android/Cargo.toml --edges normal,build,dev --prefix none
```

Actual approved-model
comparison generation is separately qualified by PR193; its genuine retained
report read is qualified by PR194. This native UI cohort uses actual scripted
fixtures. It does not qualify real-model execution through UI, selected2/3
reruns, native3 CLI, human enjoyment/narration quality, whole-app peak memory,
phone parity, installation/network-denied behavior or packaging.

Next runnable: a versioned selected2 extension over actual V3 source snapshots,
requests and construction descriptors, reusing the shared turn/store/ledger and
native ownership mechanisms. Keep selected1 and existing reports readable;
historical inspection does not authorize resume. Whole D07 remains unchecked.
