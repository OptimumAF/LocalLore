# Independent review of optional worker resource sampling

Refs #25 D04.02/.06 and #29 D07.03, partial measurement prerequisite.
Reviewer `/root/resource_metrics_review` did not author the sampler. Review claims:
[#25 comment6368682406](https://github.com/OptimumAF/LocalLore/issues/25#issuecomment-6368682406)
and [#29 comment6368682732](https://github.com/OptimumAF/LocalLore/issues/29#issuecomment-6368682732).

The separate `review/d04-resource-metrics` worktree started at freshly fetched
accepted main `bffa7e66bf888411a6a5fce47165965fa247a2ce`. It imported unchanged
author source `84335b6` and `e09777f8d4b6ff01961885dfc44ebee55f03189e`
as `28c68b4` and `43859a7`, then author documentation `c1c2ce6` as `4cf3691`.
The author's intermediate merge was omitted to preserve current accepted main.
The tested clean tip was `4cf3691830ef1026ee5c17317d5f535b5c5e3e83`.
This review adds only this document; no sampler or other application code changed.

## Disposition and inspected authority

No blocking finding remains in this finite source review and executed synthetic
test cohort. This is independent agent review, not human approval or acceptance
of the full D04/D07 milestones. The coordinator retains integration/publication.

Inspected all new `resource_metrics.rs`, the complete adapter admission/drain and
observation paths, `role_metrics.rs`, the module/exports and opt-in scene-probe
changes. The implementation uses the already owned `Child` handle and
`try_clone_to_owned`; it never looks up a PID, opens another process, enumerates
processes or changes scheduling/termination authority. Sampling starts only after
exclusive native admission and its cancellation precheck. Busy or poisoned
admission has no sampler and no stale prior-role resource record.

The cloned process handle moves into the sampler thread. Its retained join
handle is consumed by finish or Drop; stop uses a bounded channel that wakes the
wait. Sampler setup failure, query failure or joined thread panic becomes fixed
diagnostic metadata, without selecting an inference result. The native owner
remains held until generation and sampler finish, then is released before the
outcome is published. Provider drain still waits for its existing role thread;
the sampler does not detach a second owner during cancellation or Drop.

The summary retains maxima and counters, not a vector of samples. The loop's
65-second/262-attempt cap and nominal250ms interval are fixed. Stop/Drop cannot
interrupt a synchronous Windows query already in progress, so neither the cap
nor join is a hard real-time bound. Thread scheduling can also delay the first
sample. These observations cannot establish an exact whole-role memory peak or
zero timing perturbation at a deadline race. The author document makes these
limits explicit; sampling remains opt-in.

Checked the FFI structure's field order/types against Microsoft's
[PROCESS_MEMORY_COUNTERS_EX definition](https://learn.microsoft.com/en-us/windows/win32/api/psapi/ns-psapi-process_memory_counters_ex)
and the handle, size and Kernel32 export requirements in
[GetProcessMemoryInfo](https://learn.microsoft.com/en-us/windows/win32/api/psapi/nf-psapi-getprocessmemoryinfo),
read2026-10-23. `PrivateUsage` is private commit, not private resident memory.
The process-lifetime working-set high-water mark is explicitly separate from
sampled-window maxima and may predate the current role or story.

`new` and `with_metrics` remain sampling-disabled. The additive constructor is
`with_resource_metrics`; private Rust snapshot version2 adds optional resource
fields. There is no Host/schema/renderer/export grant. Setup or lost/panicked
summary duration/peaks remain unknown rather than invented zero observations.
The existing recorder binds one turn identity, retains at most three records,
uses nonblocking recorder locks and reports incomplete/lost data. The new fields
contain no raw prompt/output/path, PID, handle or story/entity identifier.
Process-lifetime peaks and existing cumulative worker counters still need
redaction and exact authorization before any future per-story UI exposure.

## Independently executed checks

Windows x64, OS version `10.0.26300.0`; rustc1.93.1
(`01f6ddf75`, LLVM21.1.8), Cargo1.93.1. All build/test outputs and TEMP/TMP
were placed in a new task-owned D: `resource-metrics-review` directory, outside
the source checkout. Locked offline dependencies; development/test debug0 and
incremental0. No dependency was added or downloaded by this review.

From the review worktree, with `$reviewRoot` set to that private output directory:

```powershell
$env:TEMP="$reviewRoot/temp"
$env:TMP=$env:TEMP
$env:CARGO_PROFILE_DEV_DEBUG='0'
$env:CARGO_PROFILE_TEST_DEBUG='0'
$env:CARGO_INCREMENTAL='0'
cargo +1.93.1 build --manifest-path crates/locallore-local-runtime/Cargo.toml --features scene-probe --bins --locked --offline --target-dir "$reviewRoot/target"
cargo +1.93.1 test --manifest-path crates/locallore-local-runtime/Cargo.toml --features development-worker,engine-adapter --all-targets --locked --offline --target-dir "$reviewRoot/target"
cargo +1.93.1 clippy --manifest-path crates/locallore-local-runtime/Cargo.toml --features scene-probe --all-targets --locked --offline --target-dir "$reviewRoot/target" -- -D warnings
cargo +1.93.1 clippy --manifest-path crates/locallore-local-runtime/Cargo.toml --all-targets --locked --offline --target-dir "$reviewRoot/target" -- -D warnings
cargo +1.93.1 fmt --manifest-path crates/locallore-local-runtime/Cargo.toml -- --check
git diff --check
```

All commands exited0. Runtime tests: **38 passed,0 failed,1 existing ignore**;
the ignored reparse test requires Windows symlink privilege and was not run.
Both binary test targets had0 tests. Runtime test execution took6.29s.
Build, both strict Clippy configurations, formatting and diff checks passed.
No intermediate failure occurred in this review cohort.

Executed cases include actual owned synthetic child sampling, bounded stop/Drop
and child nontermination, actual null-handle query refusal, unavailable/panic
summary handling, fixed cap predicates, distinct peak accumulation, disabled
versus sampled provider results, cached polling without duplicate records, Busy
without stale metrics, cancellation/Drop reaping, recorder faults and actual
production parser/repair failure preserving canonical bytes across modes. The
whole three-record worst-value serialization bound remains below8192B.
The65-second cap was inspected and its predicate tested; no65-second sampler
soak or hostile OS-stall experiment was run. No new test-only source hooks were
needed. Logs remain local: `build.log`, `tests.log`, `clippy.log`,
`clippy-default.log`, `fmt.log` and `versions.log`.

## Historical model evidence and remaining gates

Read the author's local `source-binding.json` and hashed `scene-final.json`;
the recorded clean source is `e09777f`, and JSON SHA256 is
`518aa4931aadea4708430755b19f0b09d917dd5b56597d9879f79ab1b89f3113`.
Its scene/per-role/resource checks are true, total41937ms,
quality acceptance false and blocked-network false, matching
[the author's dated report](D04_RESOURCE_METRICS_2026-10-23.md).
That supplied execution is historical evidence. This reviewer did not call a
model, run the probe with weights or verify model assets by executing them.

This slice does not qualify model load/parent-app memory, private RSS, TTFT,
sustained latency/thermal behavior, narrative quality, Android/non-Windows
execution, native IPC/WebView rendering, packaging, blocked-network operation or
release readiness. No desktop control, device/emulator/ADB, protected-chat
runtime/process action, repository setting, installation, release or merge was
performed. Next runnable task: coordinator integrate the unchanged source and
this review, publish a focused partial PR, then separately qualify the bounded
multi-scene local-model lane and its stated performance/quality limits.
