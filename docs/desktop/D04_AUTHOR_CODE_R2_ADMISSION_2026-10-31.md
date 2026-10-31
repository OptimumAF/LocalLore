# Author packet A: proposed corrected code baseline

Refs #25 D04.02 and draft PR301. **Source preparation only; corrected execution
requires a new owner decision.** The [original capture failure](D04_AUTHOR_CODE_CAPTURE_FAILURE_2026-10-31.md)
remains invalid, unknown historically and fully retained. The prior approval
explicitly excluded automatic retry.

## Exact scope

Prepare separate `author-r2-code-checks.mjs` and `author-r2-admit.ps1` with their
own admission/START/PASS/process/log namespace and STOP latch. Preserve all original
scripts, Stage, approvals, format/prep evidence, failed baseline and STOP.
Do not replace filenames or imply that old commands ran under the new coordinator.

The original successful format and offline protocol-fixture build are carried
under their original Stage, runner, arguments, tool/source hashes, complete raw
logs and prepared fixture identity. There is no repeated format/prep invocation.
Original27 fixture fingerprints and the additional10 failed-attempt roots stay
immutable. Preserve the failed unit binary and all earlier normal/diagnostic builds.

The proposed sequence is:

1. **One corrected baseline**, unchanged16 FIRST assertions and old runtime
   behavior, with12KiB stdout/4KiB stderr. Require a complete actual summary,
   exit101,16 executed,0 ignored, genuine failures and no setup failure. Root reads
   the raw logs before accepting behavioral RED.
2. Only after that result, the different author implements the bounded synthetic
   Author lane while production Author access remains disabled.
3. Format exactly the three changed production Rust files and review the diff.
   The two originally formatted FIRST files remain byte-identical.
4. Run unchanged16-case GREEN, existing runtime regressions, explicit format and
   strict Clippy checks, normal desktop build, then exact merged-main build
   readback. No application is launched.

Any further unknown capture/closure, overflow, identity change, failed check or
storage boundary is terminal for that sequence; no automatic retry. An old STOP
may be recognized only as the exact pinned historical capture failure after a
new read-only closure adjudication **and an actual new owner decision**. All other
global STOPs remain effective. These are cooperative local controls, not OS
containment or a remote debugging service.

## Resource admission

Keep the existing hard caps unchanged: metadata1280KiB, same group64MiB,
joint724MiB, old records576KiB physical/decoded, fixtures8MiB, and original target
ceiling12,554,947,872B from8,259,980,576B plus4GiB. The metadata authority remains
bound to the actual earlier owner decision; the new decision concerns one
corrected baseline and remaining code checks.

Revise whole-packet forecasts, including every earlier failure and source cost,
to192KiB records from1,066,473B and192MiB target growth from12,221,409,520B.
These are forecasts, not larger hard limits. Expected target12,422,736,112B stays
below the original ceiling. New retained synthetic fixtures remain expected below
1MiB alongside existing fork fixtures; actual bytes and old fingerprints are checked.

The corrected baseline reserves106,496B for both streams at conservative6x
encoding plus8192B receipts. At the measured1,146,368B metadata checkpoint, a new
source pair at most44KiB and Root gate records forecast8KiB give1,306,112B with
that reserve, below1,310,720B. This leaves only4608B for any fresh admission/START
not already counted. Final actual source/gate sizes, complete reserve and current
inventory must fit before execution; the estimate is not admission.

Both scripts and the explicit owner/closure records are hash-bound. New scope
grants no app, model, packaged C++ worker, Android/device, OS/network work or
downloads. It does not enable original-story UI, qualify author inference, accept
story quality, close D04, release software or reuse any spent native app grant.
