# Host guard phase observations

Refs #14 (M10.02), supporting #13 (M09.06). These bounded observations identify
costs inside the existing live observer's full guard. They do not validate
execution, establish cleanup, grant time, or qualify Android/model latency.
The separate [closed validation profiler](CLOSED_VALIDATION_PROFILE_V1.md)
continues to measure replay with cProfile; it has not been replaced.

The SDK4/SDK5 shared `_LiveOwnedTarget.guard` retains the same authoritative
statements and order. It observes seven fixed phase names:

| Phase | Existing work |
| --- | --- |
| `total` | Whole guard, including child phases and instrumentation |
| `budget_before` | Argument, fast guard and remaining-budget checks |
| `inputs` | Existing complete source/tool/input revalidation |
| `metadata` | Bound admission/running reads and equality checks |
| `observation` | Existing native guest-port observation |
| `validation` | Existing guest observation and table validation |
| `budget_after` | Existing final fast guard |

The collector is fixed code, initialized before the observer's first guard.
There is no caller-selected clock, callback, implementation or file policy.
Queries, trust positions, constructor signatures, result schemas and deadlines
are unchanged. Streaming fast guards are unchanged and are not separately timed
by this collector. No validation is cached or removed.

## Data and failure semantics

`guard_phase_snapshot()` is a pure, independent snapshot with version1 and scope
`owned-target-guard-phases-v1`. Its fixed ordered `rows` contain `phase`, `calls`,
`completed`, `raised`, `wall_ns` and `max_ns`. Counts refer to closed measured
spans, not accepted SDK commands. `completed + raised == calls`; a raised guard
can have a valid diagnostic. Each count is bounded to1,000,000 and nanosecond
values to2^63-1. No unbounded event history is retained.

`perf_counter_ns` samples must be exact nonnegative integers and nondecreasing.
Clock errors, overflow, malformed state or contention permanently invalidate
the sample. Reasons are fixed enums; no exception text, arguments, model content,
filenames, PIDs or thread identities are captured. Malformed rows are omitted,
never stringified. Returned rows do not alias the collector.

The collector takes nonblocking locks only for small counter operations, never
around a guard body. Ordinary observer errors do not skip validation, suppress
an original refusal or block cleanup. An observer interrupt cannot replace an
already-active action failure; without a primary failure, KeyboardInterrupt and
SystemExit propagate. Existing constructor exception translation is unchanged.

`observer_closed` records only an exact successful existing `close()` return,
not the earlier logical `_closed` flag. `open_phases` distinguishes unfinished
spans. `complete` means valid observations, a known closed observer and no open
span; it does **not** mean the guard, command or runtime succeeded. Every export
has `feature_acceptance: false`. Actual cleanup/proof readers remain authoritative.

Wall costs include instrumentation overhead and subcalls. Total overlaps its
children; concurrent spans can overlap each other. Do not sum overlapping rows
as independent wall/CPU costs, infer exclusive disk traffic or infer model
latency. The collector itself validates fixed bounded state, which adds cost.

## Separate SDK5 sidecar

The original-author restart controller may write `host-guard-phases-v1.json`
only after its original authoritative result is persisted and its observer has
returned known closed. It checks the existing D: output directory identity and
uses create-only output; it never overwrites/adopts an existing diagnostic.
The central strict diagnostic schema rejects extra fields and malformed rows.

Valid, invalid and incomplete observations remain diagnostics. Missing output
means no measurement. Ordinary snapshot/schema/path/write failures leave the
original controller result and cleanup unchanged. An interrupt preserves an
already-refused primary result; otherwise it propagates after terminal result
publication and cleanup. Diagnostic content is never consumed by acceptance
readers and cannot repair an unqualified command or missing proof binding.

This change needs fresh source-bound admission before any future runtime use.
It does not authorize a guest, revive a spent grant, extend the fixed session,
or retag the preserved 4c53 restart refusal. Host tests with fake native/process
and SDK fixtures establish instrumentation behavior only. No current live-phase
measurements, runtime speedup, phone or ARM64 result is claimed.
