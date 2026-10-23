# Desktop Play & Story Lab (D02)

A native Windows shell over the shared Rust engine. The original Lantern Quay
fixture supports giving the last potion to Mira, waiting, attempting an
unlearned ability and explicit typed dialogue. Finalized Rust receipts populate
the transcript; the inspector shows accepted events, requests and player-state
differences. Play uses player context. Story Lab explicitly reveals spoilers and
can inspect character or omniscient context without granting author mutations.

Fake inference and in-memory-only progress remain visible. Up to four fixture
sessions and their drafts live in this process. Cancel preserves a draft;
reset/close discards the session; closing the app loses all progress. Arbitrary
story generation, model choice/import, free-text interpretation, durable saves,
export and author edits are unavailable. Real runtime spikes elsewhere in the
repository are not integrated into this shell.

See [ADR-0006](../../docs/adr/0006-desktop-host.md),
[host-v1](../../docs/desktop/HOST_V1.md),
[D02 harness](../../docs/desktop/D02_HARNESS.md) and
[verification](../../docs/desktop/D02_VERIFICATION_2026-10-22.md).

## Build and run

Tested on Windows 11 x64 with Rust 1.93.1, MSVC/Windows SDK, installed WebView2,
Node 23.10.0 / npm 11.2.0. Development dependency provisioning uses network;
subsequent locked builds use the cache. No model weights or API key are needed.
Other OS targets and installers remain unqualified.

From a clean checkout at the repository root:

```powershell
npm --prefix apps/desktop ci --ignore-scripts --no-audit --no-fund
npm --prefix apps/desktop run build
cargo build --manifest-path apps/desktop/src-tauri/Cargo.toml --locked
# Subsequent cached build/run; opens this application's normal window.
cargo run --manifest-path apps/desktop/src-tauri/Cargo.toml --locked --offline
```

Always rebuild the normal frontend with `npm run build` after using a development
harness, then rebuild the native executable without `--features dev-harness`.
Node, Playwright and a dev server are not shipped runtimes. React and CSS bundle
into local assets; the executable uses the installed WebView2. The desktop is a
separate Cargo workspace; Android does not enable the optional host feature.

Enter submits the selected typed action; Shift+Enter adds a newline, and IME
composition does not submit. Native form controls support keyboard navigation;
a skip link and visible focus lead to the composer. Layout & text exposes two
pane-width sliders and 100–200% text. The inspector can collapse, and transcript
pages contain at most 12 receipts. Copy receipt writes only the selected
finalized receipt after an explicit button press. Untrusted dialogue renders as
text; it cannot execute HTML, load external images or grant debug privileges.

## Verify without desktop control

```powershell
npm --prefix apps/desktop run check
npm --prefix apps/desktop run format:check
npm --prefix apps/desktop run harness:native
npm --prefix apps/desktop run harness:headless
python scripts/check.py host --offline
cargo test -p locallore --features host --locked --offline
cargo clippy -p locallore --all-targets --features host --locked --offline -- -D warnings
cargo fmt --manifest-path apps/desktop/src-tauri/Cargo.toml -- --check
cargo test --manifest-path apps/desktop/src-tauri/Cargo.toml --locked --offline --features dev-harness
cargo clippy --manifest-path apps/desktop/src-tauri/Cargo.toml --all-targets --locked --offline --features dev-harness -- -D warnings
# Restore and check the normal frontend/native configuration.
npm --prefix apps/desktop run check
cargo clippy --manifest-path apps/desktop/src-tauri/Cargo.toml --all-targets --locked --offline -- -D warnings
cargo build --manifest-path apps/desktop/src-tauri/Cargo.toml --locked --offline
```

First headless provisioning only: from `apps/desktop`, run
`node node_modules/playwright/cli.js install chromium`. It downloads a public
development browser. Native harness rendering requires only installed WebView2.
The harness commands launch their own hidden native app or headless browser,
exercise the same controller, and save synthetic JSON plus app-only PNGs under
ignored `artifacts/`. They never activate a window, inject desktop input or
capture the desktop. Native and headless evidence are labeled separately.

Tauri 2.12.5 / tauri-build 2.7.4 remain pinned. The build-only public-icon temp
copy works around tauri-winres 0.3.7 apostrophe escaping; an apostrophe in TEMP
itself remains an upstream limitation. `bundle.active=false`: these commands
produce a native executable, not an installer or release. No app data or raw
error text is uploaded automatically.
