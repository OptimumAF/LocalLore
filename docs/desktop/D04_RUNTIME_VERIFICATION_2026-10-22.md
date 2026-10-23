# Bounded local desktop runtime verification

Refs #25 D04.01/.02 partial implementation, claim6356347500. This packet adds
the native worker boundary and its Rust owner. It changes no engine, database,
shared host, Android adapter or desktop application source. The coordinator owns
the shared M05 and app integration. Native lifecycle evidence is not free-text
gameplay, prose-quality acceptance or a supported-phone claim.

## Implementation and API

`crates/locallore-local-runtime` provides `LocalRuntime::spawn_packaged(resource_dir,
model)` selecting the fixed `locallore-llama-worker.exe` resource. No frontend
executable command or model-selected path enters this API. The explicit trusted
development executable override and synthetic process fixture/probe binaries
require feature `development-worker`; they are absent from the default API.

`load(cancel)`, `generate(Generation { role, prompt, schema, max_tokens }, cancel)`,
`unload()` and `shutdown()` block on the application's background worker. Rust
returns fixed Error categories, cached `status()` and bounded `last_metrics()`.
Calls own one native operation at a time. Caller supplies immutable, already
filtered role context and the cancellation closure. This crate has no canonical
state or inference pipeline; only the shared engine may approve outcomes.

The Windows owner opens every model ancestor directory and the final file
without write/delete sharing, with OPEN_REPARSE_POINT and directory backup
semantics, rejects reparse points and hashes the retained final file handle.
Size and SHA-256 must match the single approved profile. Handles remain owned
through the runtime lifetime. Native loading therefore cannot reopen a renamed
or replaced path while this owner lives. `unload` releases native weights;
dropping the runtime also releases file/directory guards. Another selection
requires a new owner. This is Windows qualification; Unix path substitution and
other CPU architectures have not been qualified.

The owner uses inherited private pipes, no shell/socket/debug server. Separate
bounded writer/stdout/stderr threads avoid waiting for an unresponsive stdin
consumer. Requests/replies cap at 32768 bytes, visible text16384, stderr65536.
Replies must match the current monotonic request ID and exact schema/types,
including duplicate-field, finite-metric and thought-channel checks. Diagnostics
are discarded, never forwarded. A60s operation deadline sends cancellation;
after2s without terminal drain the exact child is killed/reaped and the owner
is failed. `Cleanup` distinguishes an unconfirmed cooperative outcome. Drop
kills/reaps its exact child before joining pipe threads. Packaged code must keep
the reviewed no-subprocess worker; no generic arbitrary child is trusted.

`native/llama-worker` implements exact-field line-framed v1 load/generate/cancel/
unload/status/shutdown. JSON strings escape newlines; input frames are capped
before parsing and duplicate keys independently reject. Cancel has no separate
ack frame: the original operation produces one terminal reply after per-call
RAII objects are destroyed. The main pipe reader signals an atomic flag; native
load-progress and CPU-decode abort callbacks honor it, plus checkpoint/deadline
checks. EOF cancels/drains before exit. One model stays loaded across fresh
template/context/chat/sampler/batch owners for each role; there is no shared KV
history across roles, observers or stories. Unload joins previous work then frees
model weights. Native failure cannot commit any story event.

The native build pins llama.cpp commit
`620d2225cc436ab0b001e3200e590e3b286ef9ab`, verifies a clean tracked checkout,
disables shared/GPU/RPC/dynamic backends, server/app/UI, TLS/subprocess and
LLGuidance paths, and exposes only local file APIs. Upstream common still
compiles an HTTP utility; this is not an OS network-denial proof. The effective
profile, exact approved artifact/template hashes and all caps are in
`native/llama-worker/profile-v1.json`. MIT attribution is retained in NOTICE;
model weights are neither bundled nor downloaded. Exact cached Rust dependencies:
serde1.0.229, serde_json1.0.154 and sha2 0.10.9. The crate initially has an isolated
workspace/lock for ownership-safe compilation; central manifest integration is
the coordinator's serialized task.

## Actual checks

Environment: Windows11 Pro10.0.26300, Intel i7-12700K (12 cores/20 logical),
66796484 KiB OS-visible RAM; CPU AVX2/FMA/F16C/BMI2/OpenMP only. No GPU inference.
Rust/cargo1.93.1; MSVC19.34.31937 from VS2022 Community17.4.3; existing CMake3.22.1
and Ninja. These checks used no downloads or device/desktop control.

From repository root, with an existing clean reviewed upstream checkout and
existing approved local model (placeholders deliberately avoid personal paths):

```powershell
powershell -NoProfile -File native/llama-worker/build.ps1 -SourceDir <reviewed-llama-source> -BuildDir target/d04-worker -CmakePath <installed-cmake>
python native/llama-worker/test_protocol.py target/d04-worker/locallore-llama-worker.exe
$env:CARGO_PROFILE_DEV_DEBUG='0'
$env:CARGO_INCREMENTAL='0'
cargo fmt --manifest-path crates/locallore-local-runtime/Cargo.toml --check
cargo build --manifest-path crates/locallore-local-runtime/Cargo.toml --bins --all-features --locked --offline
cargo test --manifest-path crates/locallore-local-runtime/Cargo.toml --all-targets --all-features --locked --offline
cargo clippy --manifest-path crates/locallore-local-runtime/Cargo.toml --all-targets --all-features --locked --offline -- -D warnings
cargo build --release --manifest-path crates/locallore-local-runtime/Cargo.toml --bins --all-features --locked --offline
crates/locallore-local-runtime/target/release/runtime-probe.exe target/d04-worker/locallore-llama-worker.exe <approved-local-model>
```

Build passed. The first compile exposed Windows' min macro and was corrected
with NOMINMAX; original upstream warnings about Windows SDK macros/GCC pragmas/
conversions remain unsuppressed. A first Rust test compilation required deriving
PartialEq for Metrics. An initial debug probe overflowed the main stack before
worker launch due to a1MiB hash buffer; changing it to a heap64KiB buffer fixed
the failure. These failed attempts are not counted as passing native runs.

Final checks:7 Rust tests passed, strict Clippy and formatting passed;11
model-free cases passed against the actual compiled native worker. Rust tests
include six hostile process modes (EOF/death, oversized stdout/stderr, wrong
identity, duplicate/truncated replies), invalid model before launch, lifecycle,
malformed/bounded reply checks, cancellation and timeout drain failures, and a
30KiB generation with a worker refusing stdin. The latter verifies child
termination releases a genuinely blocked writer and Drop completes. These are
synthetic hostile processes, separate from actual model cooperation.

Final native executable SHA-256:
`fd5d0e99bae32b2cd4088fbe8eb67ee10bf3b026a9f0ee2ae2379463f70fcd00`.
It identifies this local build, not a reproducible byte-identical distribution.
Upstream source remained clean after the build. No binary/private path or raw
prompt/output trace is committed. Generated artifacts stay in ignored target/.

## Actual model lifecycle observations

The probe verified the already available Qwen3-0.6B Q8_0 model,639446688 bytes,
SHA-256 `9465e63a22add5354d9bb4b99e90117043c7124007664907259bd16d043bb031`.
It performed schema-constrained director JSON, one plain narrator sentence,
active cancellation, fresh-context recovery, unload/reload/shutdown, then an
independent load-cancellation and fresh-worker load recovery. Only aggregate
metrics are printed. All model calls were CPU/four threads with the pinned
actual embedded Jinja template, thinking/tools disabled and capped context4096.

The final retained run passed:

| Observation | Result |
|---|---|
| First load |293.0827ms; model loads1 |
| Director |21 input/5 output tokens; prefill172.6718ms, decode104.0489ms, total372.7942ms |
| Narrator |24 input/18 output tokens; prefill116.7412ms, decode322.3792ms, total535.2056ms |
| Active generation cancel |226ms from operation start, requested after200ms; native abort callback count1; no final text published |
| Recovery same loaded model |fresh context4, model loads1;18 input/5 output tokens, total272.9822ms |
| Unload/reload |model loads2;273.3253ms; then orderly shutdown/reap |
| Separate load cancel |359ms from operation start, requested after20ms; native abort callback count1, model loads0, contexts0 |
| New worker after cancelled load |fresh model load291.6993ms; unload/shutdown succeeded |

Director and narrator report fresh contexts1 and2 while model loads remains1;
cancelled generation created context3, then recovery context4. The native
callbacks and terminal replies are observed separately from parent's return.
Cancellation publishes an empty error result after native owners drain; metric
timer fields in that error are zero/unavailable, not measured zero-duration
work. The Rust owner discards any successful reply that loses the cancel race.

Earlier successful probes before the final load-callback counter/timer refinement
also passed warm-role/cancel/recovery/reload. One observed run sampled only this
owned worker46 times, peak working set1195028480 bytes, zero stderr. That sample
predates the final load-cancel extension and is not a final integrated app memory
figure. No controlled OS-cold cache, sustained session, distribution, physical
phone, thermal or quality claim follows from these tiny prompts. Total role
time includes fresh context/template/sampler setup; prefill and decode are
separate inner intervals. Parent hash verification, pipe overhead and app
retrieval/validation/persistence are outside native timer scopes.

## Remaining gates

D04.01/.02 are partial and reviewable, not checked complete by this packet.
Shared M05 free-text/narration/provenance/restore changes and production app
model management integration remain with the coordinator. The current portable
engine is unchanged and still requires its exact engine-rendered narration;
this worker cannot bypass it. No scene quality, durable real gameplay, repair,
native app rendering, Android real-runtime, network-blocked traffic audit,
sustained memory/latency, GPU fallback, allocator OOM injection, installed package,
or valid-model non-ASCII import test was performed here. Existing model path
contains spaces and succeeds; Windows wide argv is explicitly converted to
UTF-8 for the native loader. Physical-phone and release gates stay open.
