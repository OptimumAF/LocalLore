# Runtime resource identity and path-pinning correction

Refs #25 D04.01/.02; claim6356942908. Coordinator owns Cargo, the shared
PlayProfile and actual scene/app probes. This packet changes runtime lib.rs
only, plus this report; native C++ and its previously measured binary are
unchanged.

`LocalRuntime::worker_sha256() -> &str` now reports SHA-256 calculated before
process creation from the same opened executable retained by the runtime.
Production still chooses only fixed packaged `locallore-llama-worker.exe`.
The executable file and all its ancestors are pinned read-only without delete
sharing, with OPEN_REPARSE_POINT checks. Their guards live across CreateProcess
and until the runtime drops, preventing path/byte replacement between hashing
and execution. Empty or over128MiB executable resources reject. The optional
trusted-development path uses the same guards; no wire executable selector was
introduced.

Both model and worker pinning now lock ancestor directories **root to leaf**,
checking each opened handle is a directory and not a reparse point before the
next lookup. The previous leaf-to-root traversal could hold an old leaf while
an unguarded parent was replaced. The corrected order keeps the already locked
parent around each subsequent child lookup. The final file is opened without
following a reparse point, checked for ordinary-file metadata, and retained
during hashing and native use. Existing model size/hash approval remains exact.
This is the qualified Windows path behavior; no equivalent Unix guarantee is
claimed.

The free function `profile_manifest_sha256() -> String`, and convenience method
with the same name, identify compile-time embedded `native/llama-worker/profile-v1.json`.
Canonicalization recursively sorts object keys, preserves arrays and scalar
values, then uses compact UTF-8 serde_json serialization. SHA-256 uses the
existing sha2 dependency. This is the pinned serde JSON encoding, not a claim
of implementing RFC8785. The resulting digest is:

`01ad542001b04a96f4a8ed6c841be1866eb025350836e0c5d0a4969fdb361d38`.

The coordinator's shared PlayProfile726b7a9 now has separate worker_sha256 and
profile_manifest_sha256 fields. These identify effective runtime artifacts;
they are distinct from the actual model/template/runtime-source identity and
from the game's rules profile. The runtime returns recorded resource hashes;
it does not grant model bytes/executables authority over canonical state or
provide a signature/attestation of generated prose.

Checks completed before the later low-disk build hold:

```powershell
$env:CARGO_PROFILE_DEV_DEBUG='0'
$env:CARGO_INCREMENTAL='0'
cargo fmt --manifest-path crates/locallore-local-runtime/Cargo.toml --check
cargo build --manifest-path crates/locallore-local-runtime/Cargo.toml --bins --all-features --locked --offline
cargo test --manifest-path crates/locallore-local-runtime/Cargo.toml --all-targets --all-features --locked --offline
cargo clippy --manifest-path crates/locallore-local-runtime/Cargo.toml --all-targets --all-features --locked --offline -- -D warnings
cargo test --manifest-path crates/locallore-local-runtime/Cargo.toml --all-features --locked --offline tests::model_and_worker_reparse_paths_reject -- --ignored --exact
```

Result:18 default tests passed with one explicitly ignored privilege-dependent
Windows test; that test was then separately invoked and **passed**, giving19
actually executed passing cases. New cases verify root-to-leaf ordering, paths
with spaces/non-ASCII, known SHA-256 `abc` vector from a locked synthetic
resource, missing/directory resources, denied write/delete/parent rename while
pinned, and leaf/ancestor symlink rejection for both model/worker categories.
The profile digest matches an independent Python sorted/compact JSON vector,
and nested-object canonicalization is order-independent. Existing15 tests,
including native-owner/adapter hostile process and cancellation cases, remain.
The first explicit ignored-test invocation used an incomplete exact name and
selected zero tests; the corrected `tests::...` invocation above ran one.
Strict Clippy and formatting passed. Source diffcheck passed.

One permitted existing Release lifecycle probe ran against the unchanged native
binary to check that the new retained executable/directory handles remain
compatible with Windows process creation and actual model loading. It passed
load, same-model fresh director/narrator contexts, generation cancel/recovery,
unload/reload/shutdown, separate model-load cancel and fresh-worker recovery.
Observed load278.6ms; director363.9ms; narrator523.9ms; generation-cancel terminal
226ms (one abort callback); recovery263.2ms; load-cancel terminal346ms (one load
callback); fresh load294.2ms. No generated text or raw path was saved in public
evidence. These short lifecycle observations do not establish scene quality,
sustained performance, integrated native UI, network denial or phone support.
Native executable identity remains
`fd5d0e99bae32b2cd4088fbe8eb67ee10bf3b026a9f0ee2ae2379463f70fcd00`.

After all processes/builds were terminal, disk approached200MiB free. Only this
agent's completed standalone Rust target was cleaned, with its absolute target
resolved/checked under this worktree. Native worker/build files, bounded metrics
and a verified Rust probe copy stayed in ignored target/. No global cache,
protected model/experiment, other worktree or live process was touched. No
additional build was started after the hold. Integrated scene/app evidence and
qualification remain coordinator tasks; D04 checkboxes are unchanged.
