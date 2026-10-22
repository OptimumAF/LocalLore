# Desktop engine spike (D01)

One Windows native window calls the shared Rust engine. Give the sole potion to
Mira, try giving it again, try an unlearned ability, and inspect the accepted
revision or observer-filtered context. This is the synthetic fake-provider
boundary proof for [#22](https://github.com/OptimumAF/LocalLore/issues/22), not the
D02 playable shell. All progress is lost when the window closes. There is no
free-text model, durable story library or export yet.

See [ADR-0006](../../docs/adr/0006-desktop-host.md),
[host-v1](../../docs/desktop/HOST_V1.md) and
[actual verification](../../docs/desktop/VERIFICATION_2026-10-22.md).

## Build and run

Prerequisites: pinned Rust 1.93.1, Windows MSVC C++/Windows SDK build tools and
installed WebView2 runtime. Development provisioning can use network; the built
spike uses embedded assets, fake inference and no application server. It does
not install/download WebView2 or models automatically. Other OS targets and
offline installers are unqualified. The native spike needs no Node server/CLI.

From the repository root:

```powershell
# First build downloads locked development dependencies.
cargo build --manifest-path apps/desktop/src-tauri/Cargo.toml --locked
cargo run --manifest-path apps/desktop/src-tauri/Cargo.toml --locked --offline
```

The desktop is deliberately a separate Cargo workspace; existing Android and
host-only checks do not need Tauri/WebView dependencies. Schema tooling is an
optional `host` feature of the shared engine and disabled in Android builds.

## Verify

```powershell
python scripts/check.py host --offline
cargo clippy -p locallore --all-targets --features host --locked --offline -- -D warnings
cargo test -p locallore --features host --locked --offline
cargo fmt --manifest-path apps/desktop/src-tauri/Cargo.toml -- --check
cargo clippy --manifest-path apps/desktop/src-tauri/Cargo.toml --all-targets --locked --offline -- -D warnings

# Automated actual WebView → Rust calls; exits 0 only when all replies match headless.
$env:LOCALLORE_D01_SMOKE = '1'
cargo run --manifest-path apps/desktop/src-tauri/Cargo.toml --locked --offline
Remove-Item Env:LOCALLORE_D01_SMOKE

# Frontend request/schema checks; Node/npm only needed for these development checks.
cd apps/desktop
npm ci --ignore-scripts --no-audit --no-fund
npm run check
```

Smoke mode has a 30-second watchdog and uses only the bundled synthetic fixture.
Normal startup does not run the smoke or permit its exit command. No raw output,
private story, model or machine identifier is uploaded by the app.

Tauri 2.12.5 / tauri-build 2.7.4 are pinned and lock their full graph. The build
copies only the public icon to a fresh temporary directory and removes it after
resource compilation: tauri-winres 0.3.7 incorrectly escapes apostrophes in
canonical icon paths, which breaks RC.EXE in this workspace. It does not relocate
source or introduce a gameplay filesystem command. A build temp path containing
an apostrophe remains an upstream limitation; use a suitable development TEMP
directory if affected. No installer/public release is produced by these commands.
