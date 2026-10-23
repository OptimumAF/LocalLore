# D04 bounded per-role runtime metadata

Refs #25 D04.02/.06 / #29 D07.03, first partial prerequisite. Claims
[6361626495](https://github.com/OptimumAF/LocalLore/issues/25#issuecomment-6361626495)
and [6361626892](https://github.com/OptimumAF/LocalLore/issues/29#issuecomment-6361626892).
Contributor `/root/desktop_runtime_profile`, isolated `impl/d04-role-metrics` /
`source-role-metrics`, based on accepted
`a2bb6639eacaa9ac416788caf2fc7a6b70bf1392`.

Measured implementation: clean `42f9d8e7e8cbf7da6d7dda8aacec6d176db51d2b`
(`c9e1d55` plus external-cancellation classification repair). This document is a
subsequent docs-only change. Owned implementation is confined to runtime
`adapter.rs`, new `role_metrics.rs`, `lib.rs` module/exports and the existing
opt-in `play_scene_probe.rs` capture/report. No dependency, manifest, worker,
protocol, pin, core, Host, UI, storage, Android or canonical receipt change.

The final approved-model scene retains director **and** narrator metrics for
each accepted turn. Previous `RuntimeProvider::metrics()` exposes only the last
role and remains unchanged for existing callers. This is private native metadata
and an opt-in probe integration, not completed production diagnostics, RSS,
TTFT, sustained performance, narrative quality or full D04/D07 acceptance.

## API and authority

`RuntimeProvider::new(shared_runtime)` remains recording-disabled. Additive API:

```rust
let log = RoleMetricsLog::new(); // New recorder for each turn.
let mut provider = RuntimeProvider::with_metrics(shared_runtime, log.clone());
// Execute the existing production engine/Host path with this provider.
drop(provider); // Drain/reap any still-active cancelled/abandoned role first.
let snapshot = log.snapshot();
```

`RoleMetricsLog` is a cloneable Arc containing a mutex-protected bounded vector
and atomic publication-loss flag. It accepts no callback, file, shell, network,
observer grant or model authority. Bind/record/read use `try_lock`; publication
contention, poison, duplicate, foreign-turn reuse or capacity loss marks metadata
incomplete without becoming an inference error. At most three records are
retained, matching initial director, one permitted director repair and narrator.
A test serializes the whole three-record snapshot with worst finite floating/
integer values in less than4KiB. This bounds each recorder/snapshot, not arbitrary
caller retention of many snapshots.

Version1 snapshot fields: `available`, `incomplete`, `turn_sha256`, `records`.
`incomplete` means publication loss; false is **not** evidence that an active
provider has finished. Callers must await/drain the provider before interpreting
the terminal dataset. A failed read is available=false, incomplete=true with
no invented records. A preflight rejection may correctly have an empty log.

Each admitted attempt records typed Director/Narrator, zero-based director
attempt0/1 (null for narrator), ordinal0..2, SHA256 of the adapter's existing
serialized full request identity, parent-observed elapsed time, fixed adapter
terminal/error, native-client operation terminal/error, optional validated
worker metrics, and `drained_on_drop`. No raw story/turn/entity IDs, prompts,
contexts, generated text, paths or exception messages enter this recorder.
The request digest covers the existing identity including scope/turn/revision/
profile, budgets, role, prompt and schema; it is an identifier, not a permission
token or proof of the actual loaded artifact. Actual profile hashes remain
bound by the owning runtime/Host/probe.

Adapter terminal values are completed/cancelled/timeout/failed/dropped. A
completed adapter/native call means delivery of bounded bytes; engine parsing,
validation, fallback and atomic commit remain separate authorities. A native
completed result can coexist with adapter cancelled/dropped. Cancellation may
be noticed by the engine before another provider poll; the retained external
token ensures its eventual Drop drain is classified cancelled, while ordinary
abandonment remains dropped. Cached repeated polls emit no duplicate record.
An active changed identity records the original admitted request digest and
observed mismatch when drained, never the replacement request as an attempt.

`native_terminal` describes the native **client operation result**. On client
errors it does not claim knowledge of the raw worker-frame status. Worker timing
metrics are present only after a validated completed client operation; partial,
cancelled, failed, timeout, Busy/no-call and unknown cleanup data stay null rather
than reuse a previous role or report zero-time success. Thread/channel cleanup
uncertainty has a fixed category. Publication occurs after joining the role
thread and releasing the runtime owner lock; no new Host/store lock or canonical
write is introduced.

This is a trusted Rust API, **not a Host authorization boundary**. No wire
command, renderer access, observer privilege, export or retention capability is
added. A future D06 bridge must independently validate session/scope/head/observer
and bind the exact attempt/profile. Process-cumulative worker counters
`model_loads`, `contexts_created`, `abort_callbacks` are retained privately as
reported; they are not per-turn counts or eligible-story counts and must not be
exposed across stories/changed observers without appropriate policy/redaction.

## Verification

Windows11 Pro10.0.26300 x64, Rust/Cargo1.93.1, existing locked offline dependencies,
DEV/TEST_DEBUG0 and INCREMENTAL0. New task-owned `role-metrics-native` and
`role-metrics-artifacts`; no other chat's target, model or process was controlled.

```powershell
$env:CARGO_PROFILE_DEV_DEBUG='0'
$env:CARGO_PROFILE_TEST_DEBUG='0'
$env:CARGO_INCREMENTAL='0'
cargo +1.93.1 build --manifest-path crates/locallore-local-runtime/Cargo.toml --features scene-probe --bins --locked --offline --target-dir <task>/role-metrics-native
cargo +1.93.1 test --manifest-path crates/locallore-local-runtime/Cargo.toml --features development-worker,engine-adapter --all-targets --locked --offline --target-dir <task>/role-metrics-native
cargo +1.93.1 clippy --manifest-path crates/locallore-local-runtime/Cargo.toml --features scene-probe --all-targets --locked --offline --target-dir <task>/role-metrics-native -- -D warnings
cargo +1.93.1 fmt --manifest-path crates/locallore-local-runtime/Cargo.toml -- --check
git diff --check
```

Final result: **33 passed,0 failed,1 existing privilege-dependent reparse ignore**;
strict all-target scene-probe Clippy/fmt/diff checks passed. The fixture binary
is explicitly built before tests. Ten added tests include actual synthetic child
processes plus recorder units. They cover ordered director/repair/narrator,
cached polls, exact identity, Busy/no-call, cancelled polling and external cancel
without another poll, Drop drain and child reap, native completion before late
cancel/Drop, missing metrics after a successful role, valid late-terminal timeout,
unresponsive cleanup failure, recorder full/poison/foreign reuse, contention and
whole-snapshot bounds. Disabled/enabled/poisoned recorder tests compare actual
provider results. A production Play malformed-output/one-repair test asserts two
real synthetic director calls, the same error and unchanged canonical bytes
under all three configurations; it is not a successful-turn on/off golden proof.

An initial test incorrectly expected unresponsive-worker Timeout; the existing
client correctly reports Cleanup after unacknowledged cancellation. That failed
log remains local. No cancellation policy was weakened: separate tests now cover
valid late-terminal Timeout and unacknowledged Cleanup. The existing test-only
delayed-reply hook is forwarded to the role thread; it adds no production hook.
The first real probe exposed cancellation occurring outside the next provider
poll; that source-bound run is retained and motivated the external-token fix.

## Actual approved-model scene

From the new private artifact root, executed:

```powershell
& '<task>/role-metrics-native/debug/play-scene-probe.exe' `
  '<task>/worker-repro-clean-09/first/clean build' `
  '<previous synthetic app-owned models>/Qwen3-0.6B-Q8_0.gguf' `
  1> scene-final.json 2> scene-final.stderr.log
```

The existing fixed worker SHA256 remains
`b5dd124e484c67c9dda5aebb2cdff1878ccefd0fba99aba4788e00a166f68434`,
pinned llama.cpp `620d2225cc436ab0b001e3200e590e3b286ef9ab`. Existing Qwen3-0.6B
Q8_0 model639,446,688B SHA256
`9465e63a22add5354d9bb4b99e90117043c7124007664907259bd16d043bb031`
was reused read-only, with identical size/hash/last-write time after execution.
Original old qualified add98 worker also remains unchanged. No model copy,
download, model/profile/worker/protocol change or hosted inference occurred.

Final probe exit0: `scene_pass=true`, `per_role_metrics_complete=true`,
`quality_accepted=false`, `network_blocked=false`, total32302ms. Both committed
gift/Dialogue turns have initial director then narrator metrics, no repair, same
one resident model and fresh role contexts1→4. Both narrations use fallback2/2.
The gift stays spent, exact-key retry/restart/replay avoid inference, absent NPC
secret isolation holds, invalid actions are rejected and cancellation preserves
canon. Those remain the existing production engine/SQLite checks, not new UI or
semantic-quality evidence. Guarded rejections have no admitted role records.

| Scenario/role | Parent ms | Worker total ms | Prefill ms | Decode ms | Input/output tokens | Cumulative contexts |
| --- | ---: | ---: | ---: | ---: | --- | ---: |
| Gift director0 | 9563 | 9539.4819 | 8569.3305 | 851.3551 | 1789/22 | 1 |
| Gift narrator | 1980 | 1957.5400 | 599.4822 | 1262.5182 | 149/55 | 2 |
| Dialogue director0 | 9737 | 9719.1802 | 8375.3974 | 1233.7915 | 1699/35 | 3 |
| Dialogue narrator | 1579 | 1561.9233 | 569.9653 | 899.1999 | 154/48 | 4 |
| Cancel director0 | 117 | unknown | unknown | unknown | unknown | unknown |

Cancel is adapter cancelled/native-client cancelled, drained_on_drop=true,
worker_metrics=null. Parent wall time includes scheduling and observation/drain;
worker durations use a separate monotonic clock. Do not sum these domains,
subtract them as an IPC latency estimate, confuse worker load with model hashing,
or infer TTFT, RSS, CPU/thermal targets or percentiles from this single run.
The actual director prefill is now visible rather than hidden by the legacy
last-narrator getter. This is an observation, not a model ranking.

Local bindings:

| Artifact | SHA256 |
| --- | --- |
| Final probe executable | `2d416f37b0866e367cb6af29f4fbf4b806dedb359f373e064c49dd7761c137ba` |
| `scene-final.json`,11,521 bytes | `5bf434cb9b9d01ac9bd9a0a40f62887e855075a2fa1d2d8bc3d7e993261e4973` |
| `adapter.rs` local bytes | `e379f7a2688d23fe45fdd70b09c5aef70b6dba896b8fb34c807f2b3399cbcb0d` |
| `role_metrics.rs` local bytes | `0774e4c4c6d5c2d613eb226ef7c066fe27e43b105897a716469668e3a34cb008` |

Final stderr is0B. Actual generated synthetic outputs, database and diagnostic
JSON remain private in task-owned ignored artifacts. No full-text capture/export
feature was introduced. No native IPC/WebView, package, RSS sampler, real quality
lane, network-denial observation, Android/device or sustained cohort was executed
by this slice. Historical UI/package evidence is not relabelled a new run.

Status: in_review; no PR/merge or full-task checkbox completion by this agent.
Next: coordinator independent source/evidence review, then separately claimed
Host/D06 integration and resource/quality measurement work.
