# D01 desktop boundary verification — 2026-10-22

Tasks D01.01–D01.05, [#22](https://github.com/OptimumAF/LocalLore/issues/22),
parent [#21](https://github.com/OptimumAF/LocalLore/issues/21).
Status: implemented/locally verified for owner review; no checklist acceptance,
merge, installer, public release or other-platform qualification inferred.
Source branch `impl/d01-desktop-host`, based on accepted main `3a7cb82`.
Exact source commit and PR are recorded in the ticket handoff; the tests below
exercise the source files in that PR. Documentation-only handoff follows them.

## Delivered and reused

The [ADR](../adr/0006-desktop-host.md) selects Tauri for review after comparing
direct Rust IPC with a Compose Desktop/JNI route. The latter was source-reviewed,
not built as a second application; no comparative performance result is claimed.
The native window uses the original synthetic Lantern Quay seed, typed actions,
fake inference and the same authoritative Rust engine as Android.

`crates/locallore/src/host.rs` provides bounded host-neutral sessions and
workers, exact retry/status lookup, cancellation/close/revision fencing and
coherent observer inspection. `host` is opt-in; Android does not enable it.
Existing `contracts.rs` has four optional schema derives; engine/inference rules,
Android/JNI implementation and original fixtures are unchanged. Schemars generates
one checked frontend schema; Ajv validates UI request builders and smoke requests.
No frontend truth store, broad plugin, SQL writer or real-model adapter was added.

The native main-window grant is bound by both generated app-command ACL and
Rust's window label check. Story Lab is explicitly spoiler-bearing. Default
host construction is player-only; selecting an inspection lens cannot grant
privilege or change any character's generation context. New story sessions
receive distinct scopes; attaching to an existing session reuses one authority.

## Actual environment and pins

Windows 11 Pro x64 `10.0.26300`; Intel i7-12700K; 64 GiB RAM; RTX 3080 / UHD 770.
These are nonunique hardware categories, not inference measurements. Installed
WebView2 runtime includes `155.0.4283.62`. Rust/Cargo 1.93.1, MSVC/Windows SDK;
Node 23.10.0 / npm 11.2.0 used only for development checks. Node is not a shipped
runtime or a newly selected production dependency. Android compatibility:
JetBrains JDK 17.0.6, Gradle 8.11.1, AGP 8.10.1, Kotlin 2.2.21, SDK 36,
Build Tools 35.0.0, NDK 29.0.14206865; Android ABI minimum 26 remains provisional.
Real model/runtime/tokenizer: none.

| Introduced direct dependency | Exact version | License / source |
|---|---|---|
| Tauri | 2.12.5 | Apache-2.0 OR MIT; [source manifest](https://github.com/tauri-apps/tauri/blob/tauri-v2.12.5/crates/tauri/Cargo.toml) |
| tauri-build | 2.7.4 | Apache-2.0 OR MIT; [release](https://github.com/tauri-apps/tauri/releases/tag/tauri-build-v2.7.4) |
| Tokio, native bounded-worker semaphore | 1.54.1 | MIT; [crate](https://crates.io/crates/tokio/1.54.1) |
| Schemars, optional host schema | 1.2.3 | MIT; [crate](https://crates.io/crates/schemars/1.2.3) |
| Ajv, development-only schema checks | 8.20.0 | MIT; [package](https://www.npmjs.com/package/ajv/v/8.20.0) |

The desktop Cargo lock contains 402 registry packages, including target-specific
packages; 321 locally available manifests supplied license declarations in the
[sanitized inventory](DEPENDENCIES_2026-10-22.json). Null license entries identify
unfetched platform sources, not license clearance. Root Cargo adds six optional
schema dependencies. Existing Serde/JSON exact pins are reused. Locks preserve
checksums; inventory contains no machine paths. Full packaging/runtime notices,
security/update policy and other-platform dependency review remain D09 gates.

## Commands and results actually observed

Commands run at repository root except npm, which runs in `apps/desktop`.
Network was used only to provision public build/test dependencies and check
official sources. Offline flags below then used cached dependencies; no
disconnected-network or outbound traffic trace was taken.

| Command / check | Observed result |
|---|---|
| `python scripts/check.py host --offline` | Exit 0; 26 engine + 8 Android boundary tests, four fixture parity cases, five benchmark-helper tests, 18 runner/APK tests, three linker tests, format + Clippy |
| `cargo test -p locallore --features host --locked --offline` | Exit 0; final nine host tests + 26 domain regressions, including 10,000 deterministic attempts |
| `cargo clippy -p locallore --all-targets --features host --locked --offline -- -D warnings` | Exit 0 |
| `cargo fmt --manifest-path apps/desktop/src-tauri/Cargo.toml -- --check` | Pass |
| `cargo clippy --manifest-path apps/desktop/src-tauri/Cargo.toml --all-targets --locked --offline -- -D warnings` | Exit 0 |
| `cargo build --manifest-path apps/desktop/src-tauri/Cargo.toml --locked --offline` | Actual Windows native executable builds; first build compiled the locked native graph |
| Set `LOCALLORE_D01_SMOKE=1`, then `cargo run --manifest-path apps/desktop/src-tauri/Cargo.toml --locked --offline` | Actual native WebView startup/IPC, exit 0: `D01_NATIVE_SMOKE PASS: 25 WebView replies compared with headless Host` |
| `npm install --save-dev --save-exact ajv@8.20.0 --ignore-scripts --no-audit --no-fund`; `npm run check` | Exit 0; 25 fixture envelopes + frontend action builders validate; hostile schema samples reject |
| `python scripts/check.py android --offline --clean` with existing JDK17/SDK env | Exit 0; 78 Gradle tasks (77 executed), both Rust ABIs rebuilt, app/test APKs built, 11 JVM tests (0 failures/errors/skips), lint, final permission/ABI/ZIP/ELF audit passed |
| Native UI via Windows Computer Use | Normal startup; accessible buttons/status/lens and revision JSON visible; click gift → revision 1, accepted narration; click again → `Inventory`, no second transfer |
| Final `git diff --check` / staged check | Pass after removing a trailing blank line found during staging |

The nine host tests cover strict envelopes/UTF-8/version/size/scope rejection,
generated-schema drift, direct-engine receipt/projection equality and status
recovery, observer isolation, successful late completion after cancel/close/
revision advance, two prepared turns and stale commit, actual two-thread
cancel/commit races repeated 20 times, fake failures, unsupported capabilities,
finite session/turn/worker retention and distinct story scopes/shared-session
authority. Production limits are tested as limits, not claimed benchmarks.

The 25 native requests include accepted gift, exact duplicate receipt/status,
canonical projection and Mira/Sable views, post-commit cancel, second potion /
unlearned ability rejection, queued cancellation, malformed provider output,
competing prepared turns/stale commit, foreign story scope and close. A Rust
unit test separately compares the host receipt/projection with direct `Engine`
execution; the native smoke then compares every actual IPC reply with the
headless service. It is not a browser-only mock or a claimed real-model journey.

## Discoveries and review disposition

Independent reviewer owns only the [review report](REVIEW_2026-10-22.md), in a
separate worktree. The coordinator integrates shared interfaces. Review found
native semaphore starvation of control calls; the permit now covers preparation
only. Navigation is restricted to the embedded app origin and new windows are
denied. Valid late-success regressions and threaded cancel/commit races were
added. Final integration also gave each creation a distinct story scope rather
than a second session authority with the fixture's same literal scope.

Actual native build exposed tauri-winres 0.3.7 apostrophe escaping in canonical
icon paths. The build copies only the public icon to a fresh temp directory,
compiles resources, then removes that file/empty directory; source and player
data are not relocated. An apostrophe in TEMP itself remains an upstream
limitation. Initial native smoke exposed missing CSP `connect-src 'self'` for
the embedded fixture fetch; corrected before both successful native smoke runs.
WebView teardown printed an upstream `Chrome_WidgetWin_0` unregister warning
(1412) after PASS; process still exited 0. No native leak qualification inferred.

## Limits and next gate

No real inference, free-text interpretation, SQLite saves, restarts/resume,
archive/snapshot file export, long-history memory, author correction or public
release exists in this packet. Current full JSON inspection may hit its explicit
reply cap rather than serve an inconsistent/truncated snapshot. Only supported
synthetic seeds are accepted. Historical/paginated inspection follows future
shared persistence work. No macOS/Linux, installer, screen reader qualification,
network trace, native sanitizer/leak audit, sustained performance, Android
emulator run or physical-phone/model measurement is newly claimed. Clean Android
compile/JVM success does not waive phone/device gates.

Next implementation slice after D01 owner review: D02 #23, one Play/Story Lab
shell over this host contract. D03/#8 own durability, D04/#9 real inference;
advanced inspectors, evaluations, archives and developer packaging remain their
linked children. Task checkboxes remain unchecked until acceptance is recorded.
