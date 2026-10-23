# D09 Windows developer build and package boundary

Refs #31 D09.03/.04/.05/.07; claims [6358414659](https://github.com/OptimumAF/LocalLore/issues/31#issuecomment-6358414659)
and [6358414908](https://github.com/OptimumAF/LocalLore/issues/7#issuecomment-6358414908).
This is a local unsigned developer-folder build and prepared CI slice. D09 stays
unchecked: no installer, app launch, offline journey, release or owner acceptance
is established here. The initial baseline was accepted `8f3842e`; final source
is accepted `18c5c2f7050001f8b23fe2ca74d188ba1c637228` (D05 UI included).

## Inputs and environment

Windows x64/MSVC is the only target built in this slice. Actual host: Windows 11
Pro 10.0.26300, x64; Rust 1.93.1 (`01f6ddf7588f42ae2d7eb0a2f21d44e8e96674cf`,
LLVM 21.1.8). The inspected worker PE has linker 14.34; its existing CMake cache
selects MSVC 14.34.31933, Ninja, Release `/O2 /Ob2 /DNDEBUG`. This packet did not
rebuild that C++ artifact or install/change any system prerequisite.

Use Node **24.22.1 / npm 11.19.1**, Python **3.14.9**, the checked-in Rust
toolchain and all three Cargo locks plus `apps/desktop/package-lock.json`.
Following [workspace alignment](D09_WORKSPACE_ALIGNMENT_2026-10-23.md), the current
Cargo locks are root `Cargo.lock` (including desktop),
`crates/locallore-local-runtime/Cargo.lock` and `crates/locallore-eval/Cargo.lock`.
Desktop manifest-path commands use the root lock. Portable `--workspace` test/Clippy
commands must exclude `locallore-desktop-spike`; the existing check runner does so.
These Node/Python releases were verified against their official October 21,
2026 security release pages: [Node](https://nodejs.org/en/blog/release/v24.22.1),
[Python](https://www.python.org/downloads/release/python-3149/).
The system Node 23.10 and Python 3.9.12 were not the final package tools.
Bundled Node 24.19 / Python 3.12.14 are older compatibility inputs, not the pins.

Portable official archives were downloaded over TLS to this task's D: directory,
SHA256 checked before unpacking, and used without system installation:

| Archive | SHA256 |
|---|---|
| `node-v24.22.1-win-x64.zip` | `d2046d28c2c3dcd211ac5145c0bf30e2047ef9dfb306693c8c6e2eccd8b95fa5` |
| `python-3.14.9-embed-amd64.zip` | `3c01d7cfc666f746a6f064f60fb2156ab0ec464d3d738ab796371a46a9bb24a2` |

Node's expected value came from its versioned `SHASUMS256.txt`; Python's from
the official release table. Detached signatures/Sigstore attestations were not
independently verified. Portable Python needs only its standard library; no pip
installation is required. Keep build output, temporary files and npm cache on a
volume with several free GB. Frontend and Rust dependencies must be explicitly
provisioned before the offline Cargo build. Dependency provisioning is a networked
development operation, distinct from play or offline installation.

## Repeatable commands

From a clean reviewed checkout, set task-local paths in a new PowerShell session.
Use an already-provisioned MSVC/Windows SDK build environment. These commands do
not launch the application, WebView or model. Replace the example absolute paths
with your own directories; do not repurpose system HOME/CODEX_HOME variables.

```powershell
$taskRoot = 'D:\LocalLore developer'
$taskNode = "$taskRoot\node-v24.22.1-win-x64\node.exe"
$taskNpm = "$taskRoot\node-v24.22.1-win-x64\node_modules\npm\bin\npm-cli.js"
$taskPython = "$taskRoot\python-3.14.9\python.exe"
$taskTarget = "$taskRoot\target-native"
$env:PATH = (Split-Path $taskNode) + [IO.Path]::PathSeparator + $env:PATH
$env:TEMP = "$taskRoot\temp"
$env:TMP = $env:TEMP
$env:CARGO_PROFILE_DEV_DEBUG = '0'
$env:CARGO_PROFILE_TEST_DEBUG = '0'
$env:CARGO_INCREMENTAL = '0'
$env:PLAYWRIGHT_SKIP_BROWSER_DOWNLOAD = '1'
New-Item -ItemType Directory -Path $env:TEMP -Force | Out-Null
& $taskNode $taskNpm --prefix apps/desktop ci --ignore-scripts --no-audit --no-fund
# Stop if any command fails. npm lifecycle scripts/browser downloads are disabled.
& $taskNode $taskNpm --prefix apps/desktop run check
& $taskNode $taskNpm --prefix apps/desktop run format:check
git diff --exit-code -- apps/desktop/ui/host.generated.ts
& $taskPython scripts/desktop-package-tests.py

$taskRuntime = 'crates/locallore-local-runtime/Cargo.toml'
cargo +1.93.1 fmt --manifest-path $taskRuntime -- --check
cargo +1.93.1 build --manifest-path $taskRuntime --features development-worker,engine-adapter --bin protocol-fixture --locked --offline --target-dir $taskTarget
cargo +1.93.1 test --manifest-path $taskRuntime --all-targets --features development-worker,engine-adapter --locked --offline --target-dir $taskTarget
cargo +1.93.1 clippy --manifest-path $taskRuntime --all-targets --features development-worker,engine-adapter --locked --offline --target-dir $taskTarget -- -D warnings

$taskNative = 'apps/desktop/src-tauri/Cargo.toml'
cargo +1.93.1 fmt --manifest-path $taskNative -- --check
cargo +1.93.1 test --manifest-path $taskNative --locked --offline --target-dir $taskTarget
cargo +1.93.1 clippy --manifest-path $taskNative --all-targets --locked --offline --target-dir $taskTarget -- -D warnings
cargo +1.93.1 test --manifest-path $taskNative --features dev-harness --locked --offline --target-dir $taskTarget
cargo +1.93.1 clippy --manifest-path $taskNative --all-targets --features dev-harness --locked --offline --target-dir $taskTarget -- -D warnings

& $taskPython -X utf8 scripts/desktop-package.py build `
  --node $taskNode --npm-cli $taskNpm --target-dir $taskTarget `
  --worker "$taskRoot\approved-worker\locallore-llama-worker.exe" `
  --output "$taskRoot\packages\LocalLore developer"
& $taskPython -X utf8 scripts/desktop-package.py verify "$taskRoot\packages\LocalLore developer.zip"
```

The runtime is excluded from the repository's root workspace. A root Cargo test
does **not** replace its fixture build/test/Clippy commands. The ordinary
`protocol-fixture` executable must exist before tests find it beside `deps/`.
Neither these commands nor CI enable `scene-probe` or invoke a real model. The
Windows symlink tests remain ignored by default; running them explicitly requires
the relevant privilege and a separate recorded result.

For low-C-disk development, provision npm directly into an owned D: dependency
directory using copies of the exact package/lock files and `npm ci --prefix` there,
then point this checkout's ignored `node_modules` at that directory's
**`node_modules`** child. A differently named junction target can break sibling
module resolution after Node/esbuild resolves real paths. `npm ci` may replace a
junction; do not assume it keeps dependencies on D:. This packet's first local
relocation hit that resolution failure and recovered by copying the same fresh
locked dependency tree to the ordinary D: `node_modules` ancestor. No source or
lock change, arbitrary dependency install or weakened frontend check was used.
The final package records empty `NODE_OPTIONS`.

Root host/Android regression entry points remain `python scripts/check.py host`
and `python scripts/check.py android --clean`, with their documented SDK/JDK and
license prerequisites. They were not rerun in this D09 packet. Previous accepted
Android/physical-device evidence and its separate uncompleted gates are unchanged.

## What the packager guarantees

`scripts/desktop-package.py build` checks a clean, committed source input tree,
requires the pinned tools and x64 MSVC Rust host, runs the **normal** frontend
controller/TypeScript/schema/hook checks, and builds native code with
`cargo rustc --locked --offline --no-default-features --bin locallore-desktop-spike
-- -C link-arg=/Brepro`, dev debug info disabled and incremental compilation disabled.
The extra link flag applies to the final binary, not every dependency; see
[Cargo's command contract](https://doc.rust-lang.org/cargo/commands/cargo-rustc.html).
It refuses common Rust/Tauri build overrides. It checks the
source inventory again after building and records relative input SHA256s, source
commit, packager SHA256, tool versions and artifact hashes. Repository/global Cargo
configuration, SDK/compiler installation and dependencies remain trusted developer
inputs; this is not a hermetic build or publisher authentication.
The native dev profile keeps debug assertions (and the source's console subsystem
choice); disabling debug information does not make it a release profile. Normal
here means the normal embedded frontend/handler feature set, not signed/hardened
release qualification. Any devtools/console behavior needs its own release review.

It accepts only the fixed 6,030,336-byte worker artifact identified by SHA256
`add98cf02249141942c88e2517c2f5a4c9a91dbe9638bf7d3cd30c26916bce87`.
There is no caller-provided expected-hash override. Its upstream source is pinned
to `620d2225cc436ab0b001e3200e590e3b286ef9ab`; the profile is included as metadata.
No model weights are read or copied by this script.

The closed package consists of the normal executable, `runtime/` worker and
profile, root license, developer README, build manifest and collected `NOTICES/`.
It copies no target directory wholesale: no PDB, protocol/model probe, dev-harness
executable, save, DB, model, full trace, node_modules or unrelated resource is
selected. The output folder and ZIP must be new; failed builds do not overwrite
existing packages. A partial output/staging folder may survive a write/disk failure;
no cleanup/delete of arbitrary destinations is attempted. ZIP members have fixed
timestamps for stable container metadata. `verify` bounds sizes/counts, rejects
duplicate/traversal/symlink/unapproved-compression entries and checks exact inventory
and the worker pin. A self-consistent external manifest can be forged: verification
does not authenticate the executable/publisher or authorize its execution.
The final-link `/Brepro` change and two identical same-workspace builds are measured
in the evidence report, alongside the original differing timestamp builds. No
independent clean-path/compiler/SDK or worker byte reproducibility is claimed.

Collected notices include the available license files for the Windows-filtered
resolved Rust graph (including build dependencies), the root Apache-2.0 license,
React/react-dom/scheduler MIT files, esbuild's linked frontend comments and the
worker's upstream MIT notice. **This is not a completed distribution license audit.**
The 255-package Rust inventory names missing packaged upstream texts, notably
alloc-stdlib, selectors and webview2-com's three crates; local LocalLore packages
share the included root license. Vendored native/embedded components and any MPL
source obligations still need a coordinated audit. The manifest deliberately
records `license_audit_complete: false`; do not distribute this as a qualified
public package on the strength of generated license expressions alone.

## Worker/community build limitation

The existing `native/llama-worker/build.ps1` requires a reviewed clean local
llama.cpp checkout at the pinned revision and explicit CMake/Ninja/VS paths. It
does not fetch source or models. `CMakeLists.txt` disables server/network-facing
backends, GPU backends, native CPU auto-tuning and shared libraries. Source revision
and build flags are reproducible instructions; output bytes are not yet a proven
reproducible artifact. There is no `/Brepro`, source-path mapping or deterministic
link-timestamp configuration in the reviewed scripts. The measured worker PE
timestamp is `2026-10-22 22:15:29` and linker version 14.34. Its exact hash is from
one qualified local build, not a successfully compared clean community rebuild.

Consequently a clean community checkout plus an independently compiled worker
may fail the unchanged staging/package hash pin. Do not work around this by
accepting an arbitrary supplied expected SHA. A remaining D09.03 prerequisite is
two controlled clean worker builds from separate paths, with compiler/SDK/CMake/
Ninja/upstream-source/license inventory recorded and outputs compared. If unequal,
review deterministic compiler/link flags and path handling, then qualify any new
artifact/pin through native lifecycle/grammar/app gates before adopting it.
This packet neither changes runtime/staging source nor publishes a worker binary.

## Installation and remaining gates

This folder expects already-provisioned WebView2 Evergreen and the Microsoft
Visual C++ x64 runtime including OpenMP. `dumpbin /dependents` found the worker's
`MSVCP140.dll`, `VCOMP140.DLL`, `VCRUNTIME140.dll`, `VCRUNTIME140_1.dll` and Windows
UCRT/system imports; those DLLs are not silently copied into the ZIP. The normal
desktop executable imports Windows/UCRT components; no separate WebView2Loader DLL
appeared in its PE import list. That static list does not prove a missing-component
launch will be informative or enumerate all dynamically loaded dependencies.

At the locked Tauri version, Windows `resource_dir()` is the executable directory;
native setup adds `runtime`, and LocalRuntime adds the fixed worker filename.
The new folder matches this source layout. Path handling was exercised while
writing/reading/verifying the package in `package outputs/LocalLore Δ developer …`;
**the packaged application/worker was not launched from it**. Actual native model
loading, clean-profile launch, missing WebView2/VC runtime, update/uninstall story
retention, runtime DLL search paths and crash/disk-failure installation behavior
remain D09.05 qualification, even though earlier D04/D05 app evidence exists.

No MSI/NSIS is created; `bundle.active` stays false. For a future offline installer,
use explicitly provisioned and licensed WebView2 offline media or separately
document an installed-runtime prerequisite. Tauri's default downloaded bootstrapper
and embedded bootstrapper both need network; an offline/fixed-runtime strategy has
separate servicing/size obligations. See [Tauri's installer modes](https://v2.tauri.app/distribute/windows-installer/).
Nothing here measures outbound traffic or claims fully offline installation.

The exact local results/hashes and remaining D09 status are in
[D09_BUILD_EVIDENCE_2026-10-22.md](D09_BUILD_EVIDENCE_2026-10-22.md).
