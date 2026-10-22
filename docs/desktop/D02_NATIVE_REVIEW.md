# D02 application-owned native evidence boundary

Date: 2026-10-22. Scope: D02.06 development hooks in `src-tauri/src/harness.rs`
under [#23](https://github.com/OptimumAF/LocalLore/issues/23). This is source
review and bounded module verification, not owner acceptance or qualification
of the full shell. The coordinator records integrated journey/render results
separately. Baseline: D01 `77f6d38`, stacked branch `impl/d02-native-harness`.

## Boundary and integration

The module and its app-command registration must be compiled only with Cargo
feature `dev-harness` (off by default). Runtime activation additionally requires
`LOCALLORE_D02_HARNESS=1`. Only the native `main` app window may invoke commands.
There is no server, listener, remote-debug port, desktop capture, injected
input, window activation, arbitrary JavaScript execution or frontend-selected
file path. Production builds must omit both the module and command permission
entries. Environment activation alone cannot add compiled-out commands.

The launcher selects `LOCALLORE_D02_ARTIFACT_DIR`, a fresh absolute leaf beneath
its ignored synthetic artifact parent. The module creates the leaf itself;
an existing file/directory/symlink fails. Fixed allowlisted checkpoint labels
form filenames, and `create_new` forbids overwriting existing artifacts. IPC
cannot select a path or read/write any other file. OS-local processes and the
launcher's chosen artifact parent are trusted; this is not an OS sandbox.

`harness_checkpoint(window, state, label, snapshot)` requires `synthetic:true`
and an unsigned `uiRevision`. The frontend supplies its coherent snapshot of
view, selected session/observer, pending operation, turn status, receipt,
inspection, transcript page, visible error and bounded local error categories.
The coordinator's journey runs must await checkpoint completion before changing
that state. Semantic JSON and capture metadata share the frontend revision;
the PNG is an application render observation, not an independently inferred
canonical engine snapshot. Native engine receipts remain authoritative.

Checkpoint labels are fixed in Rust; each may be used once per process. The
cap is 40 checkpoints (the allowlist is smaller). Pretty JSON is capped at
256 KiB per snapshot/report. Capture output is capped at 16 MiB and must have
the PNG signature. File/COM/transport failures return stable categories, never
OS exception text or local paths. The final report requires `synthetic:true`
and a Boolean `passed`, writes `report.json`, then exits 0/1. A frontend pass
flag alone is not sufficient feature evidence: review the checks and artifacts.

`harness_viewport` permits only this app window's `wide` (1280×900) and `narrow`
(680×900) sizes. It does not show, focus or activate the window. The coordinator
owns hidden creation (`visible(false)`, `focused(false)`), bounded timeout,
synthetic fixtures, fixed close/reopen lifecycle hooks, frontend action/controller
journeys and native IPC/headless receipt comparison. These are integration
requirements, not claims established by the module unit tests below.

## Capture implementation and dependencies

On Windows, Tauri `with_webview` schedules a closure on the application's UI
thread. Its WebView2 controller provides `ICoreWebView2::CapturePreview`, which
writes the app WebView render to an in-memory `IStream`. A completion callback
reads the bounded PNG and returns bytes through a one-shot channel; timeout is
10 seconds. The callback retains its stream until completion. No desktop or
other application's pixels are requested. Failure/timeout still saves semantic
JSON and capture-category metadata. Other platforms report `CaptureUnsupported`.
Hidden-window rendering support must be established by actual runtime artifacts;
it is not inferred from successful compilation. A PNG also needs visual review
for meaningful content. Headless-browser render evidence must be labeled
separately from `native-webview2` capture evidence.

Existing Tauri stays pinned at **2.12.5**. Optional Windows dependencies pin
**webview2-com 0.39.1** (MIT) and **windows 0.62.2** (MIT OR Apache-2.0), matching
the already locked Tauri/Wry transitive versions. The lockfile adds them only
as direct package dependencies; no transitive package version changed. Local
registry source signatures were inspected against the implemented API calls.
These dependencies are enabled by `dev-harness`; Tauri already uses them for
the ordinary Windows host. Existing Tokio 1.54.1 adds its `time` feature for
the capture timeout. Runtime WebView2 remains provided by Windows; these hooks
do not establish offline-installer or runtime redistribution qualification.

Primary sources checked 2026-10-22:
[Tauri `with_webview`](https://docs.rs/tauri/latest/tauri/webview/struct.Webview.html#method.with_webview),
[Microsoft `CapturePreview`](https://learn.microsoft.com/en-us/microsoft-edge/webview2/reference/win32/icorewebview2?view=webview2-1.0.3537.50#capturepreview),
[WebView2 Rust bindings/license](https://github.com/wravery/webview2-rs/blob/main/LICENSE),
[Microsoft Windows Rust license](https://github.com/microsoft/windows-rs/blob/master/license-mit).
Microsoft specifies that CapturePreview must run after ContentLoading; here it
is requested by the loaded app's own frontend after render/journey readiness.
Tauri recommends pinning the minor version when using platform WebView handles.

## Module verification

Actually run in the specialist worktree on Windows x64 with the repository's
Rust toolchain:

```powershell
cargo test --manifest-path apps/desktop/src-tauri/Cargo.toml --locked --offline --features dev-harness --test harness_contract
```

Exit 0: **2 tests passed**. Checks reject non-synthetic/missing-revision and
oversized JSON; require a fresh output leaf; reject traversal labels and
duplicate labels; refuse overwriting an existing fixed artifact. Test-created
synthetic temporary files are removed. The source file is also a dedicated
Cargo test target; command attributes are disabled only in that standalone test
root to avoid Tauri's exported-command macro reimport collision. The actual app
build/integrated native journeys must verify command registration and permission
handling. These module tests do not launch a WebView, capture a render, compare
native receipts, verify close/reopen, or establish Android/device behavior.

Normal-feature compilation must separately demonstrate omission of harness
commands. App-owned native harness runs, visual review of resulting PNGs,
headless-browser checks and Android compatibility are the coordinator's
remaining integration evidence. No desktop-control tool was used for this module.
