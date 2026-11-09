# Fixed transcript UI activation V1

Refs #13 (M09.06, supporting M09.03), #14 (M10.02). Host implementation is in
review. All six Android executions and full task acceptance remain pending.
This builds on [the fixed SDK10 cohort](TRANSCRIPT_UI_COHORT_V1.md), not a new
SDK, model interface or gameplay authority.

## Purpose and boundaries

The public SDK10 owner already implements guest/process ownership, one-time
claims, bounded SDK proofs, cleanup and storage closure. Its entrypoint blocks
for the owned lifetime. The controller CLI does not have a start barrier;
`receipt_avd_environment.supervise` writes stdin before its start callback.
Launching that CLI directly therefore cannot establish an expected caller
identity before dispatch.

`benchmarks/transcript_ui_activation.py` supplies the fixed coordination glue.
It reuses the current owner, live observer, controller, closed verifier and
finite supervisor. No preparation, retirement, authorization, admission or
activation input is created by this module. Importing it performs no I/O.
It adds no SDK command, configurable package/profile, fallback or dependency.

Fixed dependency source is PR #318 at
`ed9b8e3e40e061e59c1a3404d77641a929bcbe32`, physically
`D:/Dev/Projects/The Hero's Journey/LocalLore-ci-review`. Product remains PR #317
at `78f254bb50ca0478541f0107ccfbcb16afd40d72`. Both stay frozen. The new helper
itself is separately pinned by exact bytes/path in the future four-key input.
It lives at `D:/Dev/Projects/The Hero's Journey/LocalLore-android-review/benchmarks/transcript_ui_activation.py`.
These are deliberately fixed local experiment paths, not a portable app launcher.

## Activation contract

Input is exactly `version`, `scope`, `admission`, `helper`, with integer version1
and scope `transcript-ui-run-input-v1`. The fixed input path is
`D:/Dev/Experiments/LocalLore/2026-11-01-transcript-ui-capacity-v1/run-controls-v1/run-input-v1.json`.
It can be sealed only after actual applicable approval, qualified guarded
preparation, distinct run proposal/authorization and SDK10 admission exist.
The source, product build, approval, preparation and helper are rechecked before
activation and before success. Invalid metadata refuses before process dispatch.

The future guest remains the SDK10 contract's exact
`D:/Dev/Experiments/LocalLore/2026-11-01-transcript-navigation-ui-v1/avd-v1`.
External output is fixed to
`D:/Dev/Experiments/LocalLore/2026-11-01-transcript-navigation-ui-run-v1`.
Neither was created in this packet. The profile is API35/x86_64, 8 GiB RAM,
four cores and one 40 GiB shared reservation. Limits remain:

| Component | Seconds |
| --- | ---: |
| Outer owned job | 1800 |
| Public owner / parent | 1700 / 1730 |
| Controller / its owned job | 1200 / 1230 |
| Owner-ready wait | 400 |
| Individual UI method | 90 |

The outer worker and controller worker each consume a fixed barrier envelope,
wait for a create-only started receipt, and join their actual PID, birth time,
executable and parent to the request before proceeding. Readiness additionally
joins `running.owner` to the public owner process just launched. The controller's
original raw terminal result is preserved before interpretation; closed replay
receives the actual started caller identity.

A typed SDK10 stop is attempted at most once after known caller termination,
including a known failed cohort. Unknown termination/capture cannot authorize
stop or success. A failed cohort can close safely without becoming a pass.
Observer close, owner wait, capture close, terminal publication and runtime
publication are independent attempts. An unknown result stays unknown; later
observations do not repair it. There is no alternate-file repair or fresh run.

Success requires all six original method proofs, actual caller/owner joins,
complete owner cleanup, original closure/direct-proof bindings, the exact closed
shared-ledger entry and unchanged source/build/input. A zero return code alone
does not qualify those facts. Gameplay remains entirely in the existing engine.

## Actual host verification

All commands ran from physical D: with process-local `TEMP`, `TMP`, `TMPDIR`
set to `D:/Dev/_Temp`, installed Python3.14, `-I -S -B`.

| Check | Result |
| --- | --- |
| Writer's initial suite | 20 passed, 0 failures/errors/skips; 846ms body, 1331ms direct owner |
| Final suite after adding outer-publication coverage | 21 passed, 0 failures/errors/skips; 782ms body, 1093ms direct owner |
| Root integration: activation21 + existing SDK10 profile11 | 32 passed, 0 failures/errors/skips; 2.162s |
| Root independent actual dispatch checks | 4 passed, 0 failures/errors/skips; 0.097s |
| Compile and whitespace checks | Passed |
| Current exact public retirement preview | Passed, 32.844s; no ledger mutation or plan pin |

Both writer captures joined their actual test child and retained terminal/raw
records. The integration driver preloaded ordinary current-checkout modules
before loading the new tests; all watched dependency/helper/test source hashes
were stable. It denied real subprocess, socket and ctypes activation. The four
independent checks enter the actual dispatch method and reject a foreign ready
owner, reject a missing caller, pass the actual caller to the verifier and keep
a refused result unqualified.

Tests exercise actual runtime dispatch/cleanup/run/publication and outer execute
methods, not an extracted copy of a cleanup tail. Contract/authorization/running
metadata and bounded JSON are real; process/native/SDK observations and closed
proof readers are explicitly mocked. Test-only source/helper scopes support
ordinary module discovery without changing production path/source guards.
Windows D: fixture tests are platform scoped; fixed literal/import checks are
separate. These tests do not execute the real activation or qualify Android.
No failed test execution occurred in this packet. The package-cache collection
problem was found and corrected in test setup before the first run; production
source guards were unchanged.

The production helper is 22668 bytes, SHA-256
`abe1900b189821da0591a6e0c693da3b8dc2bb564528ad31c425a1bac0e83c02`.
Final tests are 25551 bytes, SHA-256
`2e4fa2fedfc113dc7f4d823f73ab1de505d05838b5d6386aebdedbd53fd24eed`.
Independent source review found no concrete critical issue; it performed no
execution and cannot substitute for permission or runtime evidence.

## Storage preparation and remaining gate

The current read-only preview exactly matches the prior nine-image snapshot:
18959696384 bytes. All30 guest preservation records and365 nonsecret original/
copy pairs qualify; existing credential copies are referenced without copying
keys. The ledger remains unchanged with two closed unretired roots and current
validated charge44011891769 bytes. Illustrative exact retirement plus one40GiB
reservation leaves715359813 bytes below64GiB. This is not admission, held-image
exclusion, process absence or a future resource/port/free-space guarantee.

B50 controls are under `D:/Dev/Experiments/LocalLore/2026-11-01-transcript-ui-capacity-v1`
(32MiB limit), with a separate additional32MiB synthetic-fixture allowance and
selected recovery limit64MiB. Future runtime output is bounded at256MiB and
selected recovery at128MiB, separately from the40GiB guest reservation. Originals,
old source/branches, failed captures, models, saves and recovery stay in place.

The pending B45 SDK9 operation remains unchanged and unapproved; its retirement
and SDK9 run remain unexecuted. Completed host/preview evidence remains
preserved. SDK10 is a distinct alternative: the capacity scenario cannot admit
both new reserved guests simultaneously. No grant is reused or inferred.

Next: finish exact proposal review and obtain applicable approval, then use the
current shared ledger and guarded preparation/owner paths for one run. No actual
retirement, guest, authorization, admission, input or boot was created here. Other
emulators, shared ADB and settings remain untouched. Phone/model/ARM64,
accessibility, external process restoration and release gates remain separate.
No merge or full M09/M10 acceptance is claimed.
