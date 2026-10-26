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
cohorts continue using their original record1 code; these new records cannot
retroactively qualify them. Full host/build/current SDK-record2 runtime
qualification and independent review remain pending.
