# Cache-aware play admission, 2026-10-23

Refs [#5](https://github.com/OptimumAF/LocalLore/issues/5) (M01.05, supporting
bounded M01.03). The guard is implemented and locally verified; the real-model
control remains blocked. This packet stacks on unmerged
[#97](https://github.com/OptimumAF/LocalLore/pull/97), base
`fdf144aec5903052cf9bca32da50b0f95c533f35`. Qualified tool/tests are
`9e66529da41d78c999c4bff786539fa24a12ab30`; later changes are evidence/docs.
Full task and owner acceptance remain pending, with checklists unchecked.

See the [aggregate](CACHE_ADMISSION_RESULTS_2026-10-23.json),
[device observations](CACHE_ADMISSION_DEVICE_2026-10-23.md),
[independent review](CACHE_ADMISSION_REVIEW_2026-10-23.md) and
[cache-placement research](CACHE_PLACEMENT_RESEARCH_2026-10-23.md).

## Working boundary

`benchmarks/android_probe_admission.py` adds the explicit
`run_play_probe_with_admission` entrypoint around the whole legacy play controller,
including its initial SDK stop. It samples before dispatch; invalid, failed or
insufficient samples invoke no probe. Strict fields/types/byte bounds prevent
an input from overriding the fixed policy. The trusted caller still owns fresh
model/APK/process identity, exclusive device admission and bounded read-only
sampling. CLI assessment alone proves neither freshness nor permission to run.
Legacy direct `run_probe` callers are unchanged; this is not a global backport.

| Budget | Before dispatch | After a known-clean return |
|---|---:|---:|
| Host system volume | 5GiB: 4GiB reserve + 1GiB growth | 4GiB reserve |
| Guest userdata | 2GiB: 1GiB reserve + 1GiB growth | 1GiB reserve |
| Evidence volume | 10GiB | 10GiB |
| Cache growth and net guest/host consumption | Planned 1GiB allowance | Each observed delta at most 1GiB |

The allowance exceeds the previously observed 788,412,736-byte cache, but is not
a proven SDK maximum. These are pre-admission and later observations, not a
filesystem quota, live limiter or storage reservation. Free-space deltas include
unrelated OS activity and do not establish causal SDK consumption. This policy
does not retroactively redefine earlier before-only guards.

The original probe result, accepted receipt and original exception remain
separate from storage verdicts. A post failure cannot undo an accepted Rust
turn. A failed probe can have adequate storage without becoming a passing
experiment. If the callback raises or returns unknown client/process cleanup,
the wrapper suppresses its post sampler. The caller must also suppress further
dependent device work until ownership is resolved; this one-attempt wrapper is
not an unknown-owner recovery protocol.

## Actual checks and observations

| Command | Result |
|---|---|
| `python -B -m unittest discover -s scripts/tests -p test_android_probe_admission.py -v` | 20 focused passes |
| `python -B -m unittest discover -s scripts/tests -p 'test_*.py'` | 188 passes, including those 20 |
| `python -B -m unittest discover -s benchmarks -p 'test_*.py'` | 140 passes |
| `python -B benchmarks/android_probe_admission.py --sample <private-A/B-sample.json>` | Both exit2, blocked for host_headroom and guest_headroom |
| `git diff --check`, JSON/hash/link/privacy checks | Pass |

Tests cover exact byte boundaries, strict shapes/integers, original callback and
sampler exceptions, no dispatch before admission, exact controller arguments and
single dispatch, copied input observations, unknown-owner post suppression,
reserve/consumption violations and preservation of an already accepted receipt.
SDK/OS unknown-owner incidents and post-run storage exhaustion are mock boundary
tests here, not executed device incidents.

| Actual field | A | B |
|---|---:|---:|
| Host free bytes | 4,941,430,784 | 4,942,188,544 |
| Guest free bytes | 1,054,388,224 | 1,800,540,160 |
| Evidence free bytes | 121,868,603,392 | 121,865,961,472 |
| Existing cache bytes | 788,412,736 | 0 |

Both fail the new host 5,368,709,120-byte and guest 2,147,483,648-byte floors.
Both evidence-volume measurements pass. Actual sample-based API exercises use
a no-device sentinel: one sample, zero callback dispatches, no post sample.
No real device callback was supplied. The coordinator independently evaluated
B's captured sample through the same CLI, also exit2. No SDK run or real
post-growth measurement occurred.

Fresh selected-device preflight verified API35/x86_64, benchmark-owner absence,
the frozen `715a6c45…` installed APK and all 21 LocalLore APK identities per
target. Its legacy harness is `e7beb858`, LiteRT-LM Android0.18.1 CPU at
`bda624851d74be34d4e1f7fac1fc4155939539c7`; no SDK/profile/dependency changed.
All 314 recorded read-only commands completed with return0/clean clients;
final selected/inventory host clients0, server1. Protected model/cache metadata
and all 21 APK identities per target stayed unchanged. No full model hash was
refreshed: prior #97 integrity is historical, not fresh inference admission.

The initial preflight report retained a `host_storage:null` logging gap. Later
programmatic guards and actual admission samples were captured separately;
they do not reconstruct that missing value. No transport timeout/retry or
resampling to seek admission occurred. Raw journals/receipts stay private;
the public aggregate binds their lengths/hashes without paths, serials or text.

## Capacity discovery and next runnable task

The fixed marked legacy runtime area was absent on both selected targets.
There were zero eligible non-model artifact bytes and no justified relocation
plan in that area. This is a bounded candidate inspection, not an exhaustive
guest filesystem audit. No model, cache, save, compiler output, AVD/image or
other artifact was moved/removed in this packet. No app/emulator lifecycle,
model read/copy/repair, inference or new dependency/build operation occurred.

Read-only official/local research confirms the installed emulator's startup
SD-image override and the pinned SDK's explicit cache-directory API. Emulated
external cache may still share userdata; only an actually independent mounted
volume could relieve that deficit. The preserved APK lacks a cache selector,
so using the API requires a **new experimental artifact/control**. Existing
AVD configuration/card locations were not resolved by the bounded metadata
inventory; reconfiguration remains gated on a concrete preservation plan.
No new volume, destination free space, native mmap/cache compatibility or
storage success is claimed by source/help inspection.

The next runnable M01.05 implementation is an explicitly identified cache-path
experiment and volume-aware admission, with host tests/builds first. In parallel,
resolve the selected AVD attachment/launch environment and record preservation
of the original card, models, userdata and APKs before a separate volume trial.
Do not relabel external free space as userdata capacity for this frozen policy.
The standing goal authorizes bounded local development; coordinator review of
the new plan is not a new requirement to seek owner confirmation for routine
reversible work. No destructive data action is proposed.

The original unchanged715/e7 B control remains blocked. Keep A's mismatched
model/cache intact. Any future model control needs fresh source/B full identity,
owner/capacity admission and all-attempt preservation under its declared artifact
identity. M01.01 remains blocked without an authorized phone; M01.03/.04/.05/.06
full acceptance, physical/ARM64, prose quality, latency, memory/thermal and
production-backend selection remain unqualified. No merge, release, access or
repository-setting change is part of this packet.
