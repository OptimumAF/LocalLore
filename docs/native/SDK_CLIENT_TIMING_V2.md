# Bounded SDK client timing diagnostics — v2

M10.02 supporting diagnostics, stacked on draft PR #215. The failed child
restoration cohort remains failed. This change does not establish the cause
of its empty-output15-second PowerShell observation timeout or fix that cause.

The current client record is exactly the original nine keys with integer
`version:2` and two additional required keys:

- `elapsed_ms`: the actual trusted `ProcessResult.elapsed_ms`, a strict integer
  in0..2^63-1. Cleanup can overrun the dispatch budget, so elapsed may exceed it.
- `effective_deadline_ms`: a strict integer in1..180000, the ceiling in
  milliseconds of the single exact `min(seconds, remaining)` value actually
  passed to the existing process runner. Rounding does not change dispatch.

If the existing runner/result-unavailable fallback is needed, `elapsed_ms` is
explicitly null, never an invented measured zero. Null is accepted only with
the exact synthetic spawn_failed/unclean/None-returncode/empty-output failure
shape. It cannot qualify a passed client. Ordinary successful, timed-out or
cancelled results need a trusted strict measured integer; malformed timing
does not become successful or trigger another SDK call.

The pure shared shape validator accepts exact historical record1 without new
fields and exact record2 with those fields. Missing/extra timing keys, boolean,
floating, negative/overflow values, invalid versions, and hybrid shapes refuse.
Existing completed0/cleanup/raw/copy/source guards remain separately mandatory
in both component/fixed-roster and external evidence validation.

Current execution also requires every contiguous client row to be record2 with
measured timing. Both worker publication and the current parent entry points
enforce this after the existing raw/copy/status checks. A fully rebound downgrade
to historical record1 therefore remains readable as historical evidence but
cannot qualify a new execution. No timing or successful status is synthesized.

Current external admission and final parent qualification also use
`_qualified_current_gate`: fully validate the native10 prerequisite with the
historical reader, then require its exact complete measured-v2 client set.
The generic `qualified_gate` and `validate_execution` stay readable for original
historical records. A timingless historical native gate cannot authorize new
external SDK dispatch, even when its canonical/raw/roster checks still pass.
There is no runtime downgrade selector. The original seven native-gate
adversaries retain complete ten-method runner evidence and exercise the real
worker/parent path; their execution is recorded separately from older tests.

The15-second observer deadline, before/after observation cadence, PID/FILETIME,
executable/tool hash/launcher/listener pins, session bounds, raw-first capture,
closed output limits and sticky fail-stop behavior are unchanged. No retry,
server restart, global ADB operation, settings change or model access is added.

## Verification actually performed

At sourcee2ffd65a, Root runs123 focused host tests in an isolated C: worktree:
all pass in50.610s, bounded owner54792ms/worker0, known cleanup/capture, stderr0,
778 unchanged source inputs. This includes all25 existing client methods and
ten new original fake-only timing adversaries, plus fixed-phase/external/current
creation evidence tests. Original binary bytes, exact15/120/180-second budgets,
clamped fractional remainder, cleanup overrun, unavailable timing and no SDK
follow-up after an observation timeout are covered. No SDK or OS observation
is executed by these mocked host tests.

The private original request/tools/source maps and streams are retained at
`2026-10-26-client-timing-v2/host-focused-v1`. The current777-input Android
cohorts used their original record1 code; these new records cannot retroactively
qualify them. At this initial check, full host/build/current SDK-record2 runtime
qualification was pending; subsequent checks are recorded below.

An independent review found that the initial generic compatibility reader alone
would allow a fully rebound current row to lose its timing through a record1
downgrade. Five original current-execution adversaries demonstrate the gap.
The isolated `host-red-v2` run at0f9653ed executes128 tests with16 assertion
failures (owner48715ms/worker1). The first guard run `host-green-v2` at8d239d12
executes129 tests with four errors from old stage-order fixtures that supplied
no client records; the other125 pass. These attempts remain preserved.

After fixing those synthetic fixtures to supply real contiguous binary raw and
record2 evidence, `host-green-v3` at3b633d3b passes all129 tests in86.471s
(owner90621ms/worker0), with778 unchanged source inputs, known cleanup/capture
and stderr0. Commit890542be on this PR contains that same fixture change.
Original stage-order test bodies and refusal assertions remain unchanged.
This verifies current worker/parent timing requirements with mocked processes;
it does not execute SDK commands or establish a fix for the earlier timeout.

A second independent finding demonstrates that lowering a component record's
declared count could hide persisted rows. The current helper now requires the
exact contiguous JSON/stdout pair set before and after inspecting every row;
preceding generic validators still own raw-byte hash checks. Historical readers
remain unchanged. Three original persisted-extra/count-truncation/missing-pair
tests are added. Actual `host-red-v4` at5ba01755 executes19 tests with seven
assertion failures (14.358s; owner17288ms/1). Corrected `host-green-v4` atd4800772
passes all132 focused tests in145.393s (owner148635ms/0), with778 stable inputs,
known cleanup/capture and stderr0. Independent source review confirms the fix
closes that bounded finding. PR commits8a067c02/09c66e04 contain the same changes.

The earlier890542be commit contained only the worker-fixture change on the
initial timing implementation. The guard and its original tests were then
integrated forward as0309af96/bc97d337/1c4d8e8f; no earlier PR head is credited
with those checks. No history was rewritten and all failed evidence is retained.

The final isolated full host suite (`host-full-v2`, source d4800772) actually
passes1327 tests in149.684s: owner153527ms/worker0,778 unchanged inputs, known
cleanup/capture and stderr0. Its independently bounded300-second host owner
retains the original source/tool/request/raw records; this host-test budget
does not alter any SDK-client or emulator deadline. Current source09c66e04 has
identical executable inputs. Android build and fresh SDK-record2 runtime
qualification remain pending. Earlier record1 runtime cohorts retain their
original passes or failures and cannot gain new metrics.

The [owned-lifetime follow-up](ANDROID_OWNED_LIFETIME_VERIFICATION_2026-10-26.md)
actually runs native10 against frozen source9ff29c6b with84 clean measured-v2
client records, after1335 host tests and259 executed JVM tests pass. It does not
qualify external process death or a timeout-cause fix. Concurrent upstream
merges change mapped inputs and the Android build graph, so current-main
build/native/external qualification needs separate fresh evidence.
