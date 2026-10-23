# Independent review — passive per-role native metrics

2026-10-23, D04.02/.06 and D07 measurement prerequisite, partial acceptance only.
Coordinator claim #25 comment 6362059888 initially mentioned .05; this slice
measures role execution and lifecycle, not a new pending-text UI feature.
Reviewed source `c9e1d55` + `42f9d8e7e8cbf7da6d7dda8aacec6d176db51d2b` against
accepted `a2bb663`. Integrated clean source `bf5d081` on
`impl/d09-worker-adoption`, following implementation cherry-pick `d164dcf`.

Read the complete recorder, adapter admission/poll/drain changes, scene probe,
exports and new tests. No blocking finding remained. The bounded recorder is
opt-in; existing RuntimeProvider::new remains disabled. Native inference still
uses the same single owner/worker and request compiler. Results, cancellation,
identity fencing and join/drain behavior retain their existing authority.
Publication follows owner unlock and uses nonblocking locks with a sticky loss
flag. No arbitrary callback, prompt, output, path, raw turn ID or new dependency
is introduced. Request and turn identities are SHA256 bindings, not wire grants.

At most three role observations are retained per log: director, optional repair,
narrator. Repeated cached polls do not duplicate a sample. Native-client terminal
status and adapter terminal status are deliberately distinct. A valid completed
native reply may still be discarded by cancellation/drop or fail the adapter's
output cap. Failed native calls have unknown worker timings, represented by null,
never synthetic zero durations or stale metrics. External cancellation observed
during unpolled drain is distinguished from ordinary consumer drop. Changed
identity records remain bound to the original admitted request.

These trusted Rust snapshots are not ready-made observer-safe Host responses.
Worker counters such as model_loads/contexts_created/abort_callbacks are process
cumulative and must not be exposed across story/observer boundaries. Snapshot
incomplete=false describes publication loss, not whether an active job finished;
callers must await/drain before interpreting a final snapshot. The scene probe
does so explicitly. No Host/UI bridge, RSS, first-token or network-blocked
qualification is added here.

## Coordinator checks

Windows, Rust/Cargo1.93.1, locked/offline, own `worker-adoption-native` target and
TEMP/TMP; DEV/TEST debug=0, incremental=0. Synthetic subprocess fixtures only.

```text
cargo +1.93.1 test --manifest-path crates/locallore-local-runtime/Cargo.toml --features scene-probe --all-targets --locked --offline --target-dir <target>
33 passed, 0 failed, 1 existing privileged reparse test ignored.
cargo +1.93.1 clippy --manifest-path crates/locallore-local-runtime/Cargo.toml --features scene-probe --all-targets --locked --offline --target-dir <target> -- -D warnings
PASS
cargo +1.93.1 fmt --manifest-path crates/locallore-local-runtime/Cargo.toml -- --check
PASS
cargo +1.93.1 test --manifest-path apps/desktop/src-tauri/Cargo.toml --features dev-harness --locked --offline --target-dir <target>
30 native module tests + 2 harness contracts passed; 1 existing test ignored.
cargo +1.93.1 clippy --manifest-path apps/desktop/src-tauri/Cargo.toml --features dev-harness --all-targets --locked --offline --target-dir <target> -- -D warnings
PASS
git diff --check
PASS
```

Logs under that target: `role-metrics-review-test.log`,
`role-metrics-review-clippy.log`, `role-metrics-review-native.log`,
`role-metrics-review-native-clippy.log`. These are actual native process/module
tests, not WebView rendering or Android execution. No shared core/schema/Android
source changed, so no Android/device claim is inferred.

## Independently inspected author model evidence

Author final native CPU-worker/shared Engine/Store scene binds clean source
`42f9d8e`; probe executable SHA256
`2d416f37b0866e367cb6af29f4fbf4b806dedb359f373e064c49dd7761c137ba`.
Root read source-binding-final.json, scene-final.json and assets-postflight.json
from task-local role-metrics-artifacts and verified report SHA256
`5bf434cb9b9d01ac9bd9a0a40f62887e855075a2fa1d2d8bc3d7e993261e4973`.
Report scene_pass and per_role_metrics_complete are true, total 32,302ms.
Gift and secret each committed with two completed role samples; invalid potion,
invented power and unavailable ability had zero role calls. Cancel retained one
cancelled sample. Durable retry/restart/replay and observer checks pass in the
same existing scene. This is author execution independently inspected by root,
not a second root model run or native UI/IPC measurement.

Approved Qwen3-0.6B Q8 model SHA256
`9465e63a22add5354d9bb4b99e90117043c7124007664907259bd16d043bb031`, worker
`b5dd124e484c67c9dda5aebb2cdff1878ccefd0fba99aba4788e00a166f68434`, pinned
llama.cpp `620d2225cc436ab0b001e3200e590e3b286ef9ab`; postflight asset hashes
and original model mtime were unchanged. Both accepted turns used narration
fallback: 2/2, quality_accepted=false. network_blocked=false. No quality, offline,
physical phone, memory-footprint, full D04/D07 or release acceptance follows.

Owner-authorized merge still requires fresh exact-head/check status. No human
review, hosted Actions run, settings change or public release is fabricated.
