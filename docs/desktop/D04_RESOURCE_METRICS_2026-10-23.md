# D04 owned-worker resource observations

Refs #25 D04.06 and #29 D07.03, partial resource-measurement prerequisite.
Claims [6366918176](https://github.com/OptimumAF/LocalLore/issues/25#issuecomment-6366918176)
and [6366918663](https://github.com/OptimumAF/LocalLore/issues/29#issuecomment-6366918663).
Contributor `/root/desktop_runtime_profile`, isolated `impl/d04-resource-metrics` /
`source-resource-metrics`, initially accepted base `48118a7`, reconciled accepted
main `0b96d42de65d32838d4fe2fa51e514b52445ab0a` through merge `4bfa999`.
Measured final source: `e09777f8d4b6ff01961885dfc44ebee55f03189e`. This report is a subsequent docs-only change.

Owned net changes are new runtime `resource_metrics.rs`, narrow adapter/role
metadata integration, `lib.rs` module/exports, existing opt-in scene probe and
this document. No dependencies, core, Host, UI, storage, Android, worker,
protocol, model/profile pin, process/job-limit or canonical receipt changes.
Accepted Android changes were merged intact; this agent did not edit or execute
them. Original model and old/current worker hashes remained unchanged.

## Contract and authority

`RuntimeProvider::new(shared)` and `with_metrics(shared, log)` still perform
**no resource handle duplication, sampler thread creation or memory API calls**.
The new opt-in constructor is `with_resource_metrics(shared, per_turn_log)`.
The same production provider/engine paths are used. No alternate inference,
commit, context compiler or diagnostic storage system was introduced.

After exclusive native admission and cancellation precheck, the role thread
clones only `LocalRuntime`'s existing owned Child handle. No PID is supplied,
looked up, reopened, serialized or enumerated. The private module cannot accept
an external process target. The sampler never changes child priority, limits,
state or lifetime. Each role's sampler owns its cloned handle and join handle;
finish and Drop signal its bounded channel and join it before releasing the
native owner and publishing role metadata. No detached sampler survives its
owner. Failure to clone/start/query/join yields fixed diagnostic categories,
never an inference error, fallback, permission, canonical event or receipt.

Sampling has an immediate observation, nominal250ms waits, and a final
observation on stop. Scheduling/query costs can lengthen the actual gaps.
The loop stops at65s or262 total attempted observations; no sample vector is
retained. Cap termination stops **sampling**, not inference, and is explicit
`limit_reached=true` / partial status. Windows' synchronous API itself has no
application-level interrupt; the cap bounds scheduling/checks, not a hard
real-time guarantee if an OS call stalls. Stop wakes the wait immediately rather
than sleeping out the250ms interval. Thread panic/result loss is joined and
reported unavailable, without propagating its panic to the provider.

The observation window begins around native client generation admission and
ends with terminal/cancellation cleanup plus the final sample. Samples can miss
short spikes and do not isolate model evaluation from context allocation,
scheduling or final cleanup. Nothing here measures hash/load RSS, parent-app
memory, total machine usage, private resident bytes, TTFT or CPU/thermal load.

Windows uses the existing Kernel32 export `K32GetProcessMemoryInfo` and the
official `PROCESS_MEMORY_COUNTERS_EX` layout; no added library/dependency.
The API accepts an existing query-capable process handle and returns current
working set, private commit and historical peak counters. See Microsoft's
[function documentation](https://learn.microsoft.com/en-us/windows/win32/api/psapi/nf-psapi-getprocessmemoryinfo)
and [counter definitions](https://learn.microsoft.com/en-us/windows/win32/api/psapi/ns-psapi-process_memory_counters_ex),
verified2026-10-23.

## Metadata and privacy

Private Rust `RoleMetricsSnapshot.version` is now2, with optional
`RoleMetrics.resources`. This is **not a Host/wire/schema version change**.
None means sampling disabled or native operation not run (for example Busy).
Some with unavailable status means attempted sampling did not yield a retained
summary; unsupported is explicit on non-Windows builds. No other-platform
execution was performed here.

`ResourceMetrics` contains only fixed status/error enums, interval, retained
successful/failed sample counts, optional observed duration, optional byte peaks
and cap flag. Setup/panic failures have unknown duration/peaks (`null`), never
fabricated zero-memory/zero-interval success. Zero retained counters on an
unavailable result do not reconstruct how many OS calls occurred before loss.
A failed query does not overwrite prior successful peak observations.

- `sampled_peak_working_set_bytes`: maximum **sampled** working set; an approximate
  RSS observation/lower bound for this observation window, not its exact peak.
- `sampled_peak_private_committed_bytes`: maximum sampled private commit;
  `PrivateUsage` is committed private memory, **not private RSS/working set**.
- `process_lifetime_peak_working_set_bytes`: maximum observed historical worker
  high-water mark; it can predate this role, turn or story and must not be called
  a per-role peak.

At most three admitted role records remain in one turn recorder. A worst-value
whole-snapshot serialization test, now including all resource fields, stays
below8192B (version1's smaller metadata bound was4096B). This does not limit a
caller's retention of many snapshots. No raw paths, handles, PIDs, prompts,
outputs or story/entity IDs are added. Request/turn digests remain metadata,
not capabilities. No Host/renderer/export access is granted. Future exposure
must independently enforce exact session/scope/head/observer/profile policy;
both the lifetime peak and existing cumulative worker counters can reveal prior
process activity and need appropriate redaction. No private diagnostic export
feature is added.

## Executed verification

Windows11 Pro10.0.26300 x64, Intel Core i7-12700K (12 cores/20 logical),
Rust/Cargo1.93.1. Existing locked dependencies, offline builds, debug0,
incremental disabled. Own new D task target/artifacts only. C: concurrently
filled during source inspection; Git reported an index-lock write failure.
No shared/protected caches were deleted. After coordinator-confirmed relief,
Git succeeded; remaining builds and TEMP/TMP were entirely task-owned D paths.

```powershell
$env:TEMP='<task>/resource-metrics-artifacts'
$env:TMP=$env:TEMP
$env:CARGO_PROFILE_DEV_DEBUG='0'
$env:CARGO_PROFILE_TEST_DEBUG='0'
$env:CARGO_INCREMENTAL='0'
cargo +1.93.1 build --manifest-path crates/locallore-local-runtime/Cargo.toml --features scene-probe --bins --locked --offline --target-dir <task>/resource-metrics-native
cargo +1.93.1 test --manifest-path crates/locallore-local-runtime/Cargo.toml --features development-worker,engine-adapter --all-targets --locked --offline --target-dir <task>/resource-metrics-native
cargo +1.93.1 clippy --manifest-path crates/locallore-local-runtime/Cargo.toml --features scene-probe --all-targets --locked --offline --target-dir <task>/resource-metrics-native -- -D warnings
cargo +1.93.1 fmt --manifest-path crates/locallore-local-runtime/Cargo.toml -- --check
git diff --check
```

Final38 passed,0 failed,1 existing privilege-dependent reparse ignore; strict
all-target scene-probe Clippy/fmt/diff check passed. Five new tests cover:
actual owned synthetic-child sampling, stop/Drop join and child nontermination;
fixed cap predicate, missing result/setup failure and panicked sampler;
real invalid-handle query and distinct peak accumulation;
opt-in/default-disabled roles, cached polling, cancellation/Drop native cleanup;
and Busy after a successful prior role yielding no stale resource record.
The whole-snapshot bound includes resource maxima, and the existing actual
production malformed/repair failure/canonical golden also runs sampled mode.
All four disabled/metadata-enabled/poisoned/sampled cases retain the same error
and canonical bytes. These finite tests do not prove zero timing perturbation
at every hardware/deadline race; opt-in sampling has bounded overhead.

## Actual approved-model scene

From the new artifact root, with the source-bound freshly built probe:

```powershell
& '<task>/resource-metrics-native/debug/play-scene-probe.exe' `
  '<task>/worker-repro-clean-09/first/clean build' `
  '<previous synthetic app-owned models>/Qwen3-0.6B-Q8_0.gguf' `
  1> scene-final.json 2> scene-final.stderr.log
```

Existing worker SHA256
`b5dd124e484c67c9dda5aebb2cdff1878ccefd0fba99aba4788e00a166f68434`,
llama.cpp revision `620d2225cc436ab0b001e3200e590e3b286ef9ab`.
Approved existing model639,446,688B SHA256
`9465e63a22add5354d9bb4b99e90117043c7124007664907259bd16d043bb031`,
profile qwen3-0.6b-q8-cpu-v1, context4096, maximum350 tokens per role,
four CPU threads/zero GPU layers, at most one repair/120s whole-turn budget.
Model bytes/hash/last-write time and both old/current worker hashes matched
pre/post. No model copy, import, rename, download or hosted inference occurred.

Final exit0; `scene_pass=true`, `per_role_metrics_complete=true`,
`resource_metrics_observed=true`; total41937ms, fallback2/2, repairs0,
`quality_accepted=false`, `network_blocked=false`. Gift spend, exact retry,
restart/replay, observer-secret, invalid-action and cancellation canonical checks
remain the existing production engine/SQLite assertions, not UI/quality evidence.
Guarded rejections have no admitted resource records. All listed observations
have zero query failures and no cap; no native timing is fabricated for cancel.

| Scenario/role | Parent ms | Sample window ms | Samples | Sampled working-set peak B | Sampled private-commit peak B | Process-lifetime WS peak B |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| gift director | 15408 | 15405 | 60 | 1200672768 | 914145280 | 1200685056 |
| gift narrator | 2237 | 2235 | 10 | 1184022528 | 915308544 | 1203564544 |
| secret director | 12163 | 12162 | 48 | 1201975296 | 918036480 | 1222160384 |
| secret narrator | 2004 | 2003 | 9 | 1187160064 | 925388800 | 1222160384 |
| cancel director | 124 | 124 | 2 | 694124544 | 55844864 | 1222160384 |

All byte values are observations of the owned worker; shared mappings can make
working set exceed private commit. Process-lifetime high-water marks are shown
separately and may retain earlier model/role memory. Parent and worker timing
clock domains stay separate; do not sum/subtract them into invented overhead.
Concurrent host workload was not controlled. These are one synthetic scene on
one host, not a percentile, sustained-session,
phone support, quality ranking or memory threshold qualification.

Final source/executable/artifact bindings and exact results remain local in
`resource-metrics-artifacts`; raw synthetic outputs/database are untracked.

| Binding | Value |
| --- | --- |
| Final executable SHA256 | `db74a8aa77f3b36e37fc9e8f4b82d9c9412cd03efc7037ba65c5c5e6b5f8d351` |
| Final JSON (14008 bytes) SHA256 | `518aa4931aadea4708430755b19f0b09d917dd5b56597d9879f79ab1b89f3113` |
| Final stderr | 0B |

Logs: `build-optional-span.log`, `tests-optional-span.log`,
`clippy-optional-span.log`; `source-binding.json`, `assets-preflight.json`,
`assets-postflight-final.json`, `hardware.json`, `scene-final.json` and
`scene-final.stderr.log`. No generated data was added to Git.

The first4bfa999 run is retained privately, before the follow-up made unavailable
observed duration explicitly optional. No native IPC/WebView/render, desktop
control, Android/device, package, network-blocked operation, quality lane or
sustained cohort was executed for this slice. Existing historical evidence is
not relabelled a new run. Status in_review; no full-task checkbox, PR or merge by
this agent. Next: coordinator independent review/integration, then separately
claimed full-turn/RSS/load and meaningful multi-scene quality work.

## Coordinator integration checks

Independent review and its actual synthetic tests are in
`D04_RESOURCE_METRICS_REVIEW_2026-10-23.md`. The coordinator integrated accepted
#88 and #89 without changing the sampler. Final production integration source
`49c45f37a71304a895f1dd92c22986f005d81d36` includes accepted main
`4cdbc0d3823c12424720abe8d92106788b766b60`.

On the #88 integration the coordinator independently reran the locked/offline
runtime all-target tests with `development-worker,engine-adapter`: **38 passed,
one existing privileged qualification ignore**, strict scene-probe Clippy passed.
On the final #89 integration, actual desktop development native tests passed
**44 module + 2 harness contracts**, with one existing ignore; strict native
all-target Clippy and normal frontend verification passed. Commands are the
review's runtime templates plus:

```powershell
node apps/desktop/verify-frontend.mjs
cargo +1.93.1 test --manifest-path apps/desktop/src-tauri/Cargo.toml --features dev-harness --locked --offline --target-dir <native-target>
cargo +1.93.1 clippy --manifest-path apps/desktop/src-tauri/Cargo.toml --features dev-harness --all-targets --locked --offline --target-dir <native-target> -- -D warnings
```

The first native compatibility compile in the new review checkout failed because
its ignored frontend `dist` did not yet exist. Building the locked normal
frontend resolved that prerequisite; both complete retry checks passed, and the
failure remains in `metrics-desktop-test.log`. No source assertion or production
behavior changed. Final logs are `metrics-integrated-*` and `metrics-final-*`
under the task-owned `worker-adoption-native` target; Rust1.93.1, Node24.22.1,
debug=0/incremental=0 and UUID TEMP/TMP on D were used. No new model execution,
render capture, device operation or blocked-network result is implied by these
compatibility tests. The historical real-model resource observation above
retains its original frozen source and hash.
