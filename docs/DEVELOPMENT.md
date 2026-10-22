# Host development

The first implementation is a local Rust contract proof with synthetic data and
a deterministic fake provider. It does not load a model or implement Android or
disk persistence. See [contract v1](DOMAIN_CONTRACT_V1.md) and
[implementation evidence](IMPLEMENTATION_EVIDENCE.md).

Install Rust 1.93.1 with rustfmt/clippy and the platform's normal Rust C/C++ linker
prerequisites. `rust-toolchain.toml` pins the compiler; `Cargo.lock` pins all crate
revisions/checksums. Run from the repository root:

```powershell
cargo fmt --all -- --check
cargo clippy --workspace --all-targets --locked -- -D warnings
cargo test --workspace --locked
cargo run --locked -p locallore
python -m unittest discover -s benchmarks -p 'test_*.py' -v
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

No workflow/settings change is part of this packet. Actions stays disabled as
recorded in project setup; M03.05 must introduce reviewed host/Android CI later.
There are no migration scripts or user-data upgrades in this PR. Discarding
the branch removes the proof without touching a user save.

## Dependency inventory

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
| syn | 3.0.9 | MIT OR Apache-2.0 |
| unicode-ident | 1.0.27 | (MIT OR Apache-2.0) AND Unicode-3.0 |
| zmij | 1.0.23 | MIT |

Exact package source/checksums are in `Cargo.lock`; license/notice files reside in
each installed `${CARGO_HOME}/registry/src/<registry>/<name>-<version>/` package.
First-party additions are Apache-2.0. No dependency source was modified or
vendored, model weights redistributed, or release binary published. Packaging
must include the applicable third-party notices before a release (M10.06/M11.02).
This inventory is not a vulnerability or complete supply-chain audit.
