# Focused fixed CPU runtime publication

Refs #25 D04.01/.02/.04 partial and #9 M05 shared-provider prerequisite.
This boundary depends on the guarded local-play core accepted in PR #51,
merge `cff7f74bee1962748c8883b7107971cb389af485`. It adds the isolated optional
Rust owner/adapter and fixed C++ worker, with no desktop application, Android,
database, shared schema or canonical engine source changes. Native model
management and frontend integration follow in the next PR.

All runtime/worker implementation inputs are copied without modification from
joint integration `61e8cf1eac0f0aa9285f1515bfd56d01c46d932b`. Earlier reports in
this directory are historical packets: their source pins, counts and old worker
hashes describe those runs. This report and `native/llama-worker/SCHEMA_ORDERING.md`
identify the corrected publication worker and current verification.

## Boundary

The portable engine depends on neither this crate nor llama.cpp. The adapter
implements its existing `InferenceProvider`; only shared Rust prepares, validates
and commits outcomes. It does not add persistence, retrieval or memory authority.
One resident model serves fresh director/narrator contexts. Input identity,
bounded framing, deadlines, cancellation and exact-child cleanup are enforced
by the owner; generation is background work outside canonical write transactions.
Only the fixed packaged worker name is available in the default API. Trusted
development overrides and synthetic fixtures require explicit Cargo features.
There is no general executable/file/shell selector in the renderer contract.

Windows model and executable handles, including ancestor directories in root-to-
leaf order, reject reparse points and remain pinned without write/delete sharing
through native use. The actual locked executable is hashed for provenance.
Approved model size/hash, manifest/template/configuration and token/context caps
are explicit. This is not cryptographic package attestation or Unix qualification.
The implementation has no socket server, hosted provider or download path.
Disabled network build features are not an operating-system traffic-denial test.

## Exact current checks

Windows 11 Pro 10.0.26300; i7-12700K, 12 cores/20 logical, about64GiB RAM;
Rust/Cargo1.93.1. `CARGO_PROFILE_DEV_DEBUG=0` and `CARGO_INCREMENTAL=0`.
From repository root, with task-owned `<build>` outside the source tree:

```powershell
cargo build --manifest-path crates/locallore-local-runtime/Cargo.toml --features development-worker,engine-adapter --bin protocol-fixture --locked --offline --target-dir <build>
cargo test --manifest-path crates/locallore-local-runtime/Cargo.toml --all-targets --all-features --locked --offline --target-dir <build>
cargo test --manifest-path crates/locallore-local-runtime/Cargo.toml --all-features --locked --offline --target-dir <build> tests::model_and_worker_reparse_paths_reject -- --ignored --exact
cargo clippy --manifest-path crates/locallore-local-runtime/Cargo.toml --all-targets --all-features --locked --offline --target-dir <build> -- -D warnings
cargo fmt --manifest-path crates/locallore-local-runtime/Cargo.toml --check
python native/llama-worker/test_protocol.py <reviewed-worker.exe>
& <reviewed-schema-order-test.exe>
```

The standalone fixture build is required before process tests; Cargo's binary
test harness is not the executable protocol fixture. All-target/all-feature test:
20 passed, 0 failed, 1 privilege-dependent case explicitly ignored (4.27s).
The exact ignored reparse-path case then passed separately: **21 actually executed
Rust cases**, no failure. Strict Clippy, rustfmt and staged diff checks passed.
The actual compiled native worker passed **11 model-free protocol cases**.
The actual pinned grammar converter/machine test passed **13 assertions**,
including the demonstrated old property-order failure and corrected op-first
Give, legal Wait, exact Say, narrator references and invalid fields/values.
These are native process/grammar checks; no model or app UI ran in this pass.
Bounded logs stay in ignored local `target/`, not public artifacts.

Actual corrected worker SHA256:
`eda393e923ddfd03ea57d91741d8f7948d1a4af13deb90c7d6c90c492e63ff58`.
Pinned llama.cpp: `620d2225cc436ab0b001e3200e590e3b286ef9ab`.
Approved existing Qwen3-0.6B Q8_0 model SHA256:
`9465e63a22add5354d9bb4b99e90117043c7124007664907259bd16d043bb031`.
Manifest SHA256:
`01ad542001b04a96f4a8ed6c841be1866eb025350836e0c5d0a4969fdb361d38`.
The profile is CPU4 threads, context4096, output350 per role, thinking/tools off.
The shared pipeline separately owns the120s turn/one-repair limit. Reproducing
the C++ build requires the pinned existing upstream checkout and installed
CMake/MSVC, as documented in `D04_RUNTIME_VERIFICATION_2026-10-22.md`.
No binary, model, personal path, private prompt or generated raw story is committed.

## Real-model evidence and pending gates

The same corrected runtime/worker already ran the synthetic shared Engine/Store
scene and actual application-owned Windows IPC/WebView2 harness in the separate
joint integration. Scene gift/refusal/clarification/secret-observer/cancel/restart/
retry/replay invariants passed. Native app evidence:31 assertions,10 app-owned
render images and two process executions across restart. Those dependent app
sources are absent from this boundary and their evidence is not a standalone
runtime UI test. Both accepted narrations used the labeled safe engine fallback
(2/2). Mechanical success does not satisfy story/prose enjoyment acceptance.

Remaining: blocked-network execution, sustained latency/memory and OOM behavior,
GPU/fallback qualification, installers/reproducible binary distribution, arbitrary
language and NPC voices, prose quality, and physical-phone gates. No D04/M05
checkbox, release or whole desktop epic completion is claimed by this PR.
