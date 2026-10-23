# Desktop Play & Story Lab

A native Windows shell over the shared Rust engine. The original Lantern Quay
fixture supports giving the last potion to Mira, waiting, attempting an
unlearned ability and explicit typed dialogue. Finalized Rust receipts populate
the transcript; the inspector shows accepted events, requests and player-state
differences. Play uses player context. Story Lab explicitly reveals spoilers and
can inspect character or omniscient context without granting author mutations.

Fake inference remains explicit. The production app stores accepted turns in
`stories-v1.sqlite` under Tauri's app-local data directory, outside the source
checkout. Startup resumes the first stable saved story; the library can resume
any listed story. The saved workspace details show its actual path and schema.
Close releases a live session and retains its save. New and Reset create distinct
saved stories and retain earlier history. Up to four sessions can be open.
Unsubmitted composer text remains session-local; submitted uncommitted requests
are durable but are never automatically committed or cancelled on resume.
Storage/replay errors appear explicitly with no temporary-memory fallback.

Memory & evidence opens a read-only typed inspector for profiles, accepted
history, directed relationships, knowledge, promises and evidence. It supports
completed historical heads and before/after replay without changing the live
player. Statement, belief and truth labels remain distinct; NPC lenses exclude
private player display messages. Story Lab requires a spoiler acknowledgement.
Summaries, semantic retrieval and alternate-branch history remain explicitly
unsupported. See [D05 native inspection](../../docs/desktop/D05_NATIVE_INSPECTION.md)
and [verification](../../docs/desktop/D05_NATIVE_VERIFICATION_2026-10-22.md).

Inspection snapshots now provide structural diagnostics by default, explicit
private Player/Full readable views, and a separate private consistent SQLite
copy for deliberate inspection. Preview identifies scope, revision, included
files and privacy. A native folder picker saves the exact captured bytes without
overwriting existing files; existing readable inspection folders open as untrusted,
read-only text within this app. Reveal storage shows app-owned location metadata.
See [D03 native inspection](../../docs/desktop/D03_NATIVE_EXPORT.md) and
[verification](../../docs/desktop/D03_NATIVE_VERIFICATION_2026-10-22.md).

An explicit experimental local CPU profile now imports and verifies the approved
Qwen3-0.6B Q8_0 artifact through a native picker. Action and Dialogue free text use
the shared director, engine validation and narrator; accepted v2 receipts record
provenance, timing and any safe narration fallback. Supported actions are limited
to single English scene commands; unclear text asks for clarification. Quality
and network-blocked qualification remain pending. Arbitrary model choice, story
generation and author edits remain unavailable. See
[D04 native integration](../../docs/desktop/D04_NATIVE_INTEGRATION.md) and
[verification](../../docs/desktop/D04_NATIVE_VERIFICATION_2026-10-22.md).
Save files and the imported model are local app data; OS-level backup, access
control and device security still apply.

See [ADR-0006](../../docs/adr/0006-desktop-host.md),
[host-v1](../../docs/desktop/HOST_V1.md),
[D02 harness](../../docs/desktop/D02_HARNESS.md) and
[original D02 verification](../../docs/desktop/D02_VERIFICATION_2026-10-22.md) and
[current-main gate](../../docs/desktop/D02_CURRENT_GATE_2026-10-22.md).

## Build and run

Tested on Windows 11 x64 with Rust 1.93.1, MSVC/Windows SDK, installed WebView2,
Node 23.10.0 / npm 11.2.0. Development dependency provisioning uses network;
subsequent locked builds use the cache. Fake fixtures need no model or API key.
Real local play additionally requires the verified worker resource and an explicit
approved-model import, as described in D04 integration.
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
member of the repository Cargo workspace and uses the root `Cargo.lock`. The four
portable packages remain default members; portable `--workspace` test/Clippy
commands must explicitly exclude `locallore-desktop-spike`, as `scripts/check.py`
does. Android selects its JNI crate and does not depend on Tauri. Runtime and
evaluation crates retain their separate workspaces and locks. See the
[workspace alignment evidence](../../docs/desktop/D09_WORKSPACE_ALIGNMENT_2026-10-23.md).

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
npm --prefix apps/desktop run harness:export
npm --prefix apps/desktop run harness:durable
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
exercise the same controller. The durable native journey uses one synthetic SQLite
database through app-owned WebView close/reopen and a separate executable process
restart. The legacy D02 journeys explicitly retain memory fixtures. All runners save synthetic JSON plus app-only PNGs under
ignored `artifacts/`. They never activate a window, inject desktop input or
capture the desktop. Native and headless evidence are labeled separately.

Tauri 2.12.5 / tauri-build 2.7.4 remain pinned. The build-only public-icon temp
copy works around tauri-winres 0.3.7 apostrophe escaping; an apostrophe in TEMP
itself remains an upstream limitation. `bundle.active=false`: these commands
produce a native executable, not an installer or release. No app data or raw
error text is uploaded automatically.
