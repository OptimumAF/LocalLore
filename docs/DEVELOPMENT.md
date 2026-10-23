# Development checks

This page covers the local Rust contract proof with synthetic data and
a deterministic fake provider. It does not load a model or implement disk
persistence. The [Compose engine demo](../apps/android/README.md) has separate
build/test instructions and an actual in-memory Rust connection through JNI (M03.03).
See [contract v1](DOMAIN_CONTRACT_V1.md) and
[implementation evidence](IMPLEMENTATION_EVIDENCE.md).

Install Rust 1.93.1 with rustfmt/clippy and the platform's normal Rust C/C++ linker
prerequisites. `rust-toolchain.toml` pins the compiler; `Cargo.lock` pins all crate
revisions/checksums. Run from the repository root:

```powershell
python scripts/check.py host
cargo run --locked -p locallore
git diff --check
```

First-time toolchain/crate provisioning can need network access. After dependencies
are installed, `cargo test --workspace --locked --offline` and
`cargo run --locked --offline -p locallore` exercise fully local host behavior.
The executable makes no network calls, requests no account, writes no save file
and loads only the compiled-in original fixture. No model weights or private
stories are required. Python feasibility helpers use the standard library.

`cargo run` prints the accepted potion transfer, verifies root replay bytes and
checks that Mira observed the gift while Sable did not. This is an in-memory
proof. Successful output is not proof of SQLite durability, phone support,
native FFI, real narrative quality or offline Android packaging.

The Python 3.9+ standard-library runner executes formatting, Clippy, Rust tests,
fixture parity, Python helper/runner/APK-audit regressions and native-linker tests
with pinned tools. `python scripts/check.py android --clean` builds both native
ABIs and app/test APKs, runs JVM tests/lint and audits final APK capabilities and
alignment. It does not run emulators. See [commands/prerequisites](ci/CHECKS.md),
[workflow sources](ci/SOURCES_2026-10-22.md) and
[verification](ci/VERIFICATION_2026-10-22.md).

The M03.05 workflow calls these entrypoints on standard hosted Windows runners
with read-only permissions and a reviewed SHA-pinned checkout. It uses no
secrets, persistent credentials, caches, uploads, private runners or model
downloads. Provisioning is separate; new SDK license prompts are declined and
Gradle SDK auto-download is disabled. Repository Actions/settings are unchanged.
Local/static checks do not establish hosted execution; actual status and limits
belong in the verification report. No migration or save upgrade is introduced.

## Dependency inventory

The [SQLite foundation](storage/README.md) is a separate Rust storage owner.
Workspace tests include its model-free schema/migration/backup regressions.
Its [dependency inventory and official compatibility sources](storage/SOURCES_2026-10-22.md)
cover exact rusqlite/libsqlite3-sys pins, bundled SQLite and C build helpers.
Shared root-turn save/resume is implemented by the [durability follow-on](storage/DURABILITY.md),
with model-free restart/retry/fault tests and an explicit `durable_smoke` example.
Both app adapters now open the shared native workspace factory on background IO
workers. See [application storage integration](storage/APP_INTEGRATION.md) for
paths, restart semantics, tests and remaining limits. In-memory Hosts remain
available for explicit fixtures; production startup errors never select that fallback.

Verified 2026-10-22 using official registry metadata, installed package manifests
and `cargo metadata --locked --format-version 1`. All dependencies build with
Rust 1.93.1; compile/lint/tests are the compatibility evidence. Direct versions
were checked at [the serde registry API](https://crates.io/api/v1/crates/serde)
and [serde_json registry API](https://crates.io/api/v1/crates/serde_json).
Serde's [derive](https://serde.rs/derive.html) and
[strict field handling](https://serde.rs/container-attrs.html) are the official
API references used. No native inference dependency is added.

| Package | Exact version | Upstream declared license |
|---|---|---|
| serde (direct), serde_core, serde_derive | 1.0.229 | MIT OR Apache-2.0 |
| serde_json (direct) | 1.0.154 | MIT OR Apache-2.0 |
| itoa | 1.0.18 | MIT OR Apache-2.0 |
| memchr | 2.8.3 | Unlicense OR MIT |
| proc-macro2 | 1.0.107 | MIT OR Apache-2.0 |
| quote | 1.0.47 | MIT OR Apache-2.0 |
| syn (host derive dependency) | 3.0.9 | MIT OR Apache-2.0 |
| unicode-ident | 1.0.27 | (MIT OR Apache-2.0) AND Unicode-3.0 |
| zmij | 1.0.23 | MIT |

Exact package source/checksums are in `Cargo.lock`; license/notice files reside in
each installed `${CARGO_HOME}/registry/src/<registry>/<name>-<version>/` package.
The JNI boundary adds Android-specific and cross-platform packages; its complete
[registry/source/license inventory](native/DEPENDENCY_SOURCES.json) and
[JNI rationale](native/SOURCES_2026-10-22.md) supplement this host table.
First-party additions are Apache-2.0. No dependency source was modified or
vendored, model weights redistributed, or release binary published. Packaging
must include the applicable third-party notices before a release (M10.06/M11.02).
This inventory is not a vulnerability or complete supply-chain audit.
