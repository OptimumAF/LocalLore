# Bounded SDK15 recovery-to-run operator

Refs #14 (M10.02), supporting #13 (M09.06). Supporting implementation is in
review; full task criteria remain unchecked. This connects the
[source-bound inspection](SDK15_RECOVERY_READINESS_2026-11-02.md) to the
[four-method runner](../../native/LIBRARY_UI_V1.md). No app/engine/dependency,
shared storage mechanism, resource floor or existing component deadline changes.

## Fixed operation and authority

Three new scripts separate pure metadata, post-recovery input construction and
the owned operation: `library_ui_recovery_contract.py`,
`library_ui_run_inputs.py`, and `run_library_ui_recovery.py`. Imports perform no
target observation or dispatch. The public operator accepts only
`--authority-sha256 <actual fixed-authority-file hash>`; no paths, profiles,
models, commands or implementation classes are selected by JSON/arguments.

The operational SDK15 checkout remains frozen at
`D:/Worktrees/locallore-record-actions-tests-v1`, commit `18809566` (PR #352).
The operator checkout is `D:/Worktrees/LocalLore-record-query2-tests-v1`, on
open/unmerged PR #353's dependency. Its authority must bind its exact clean Git
head and operator/builder/contract bytes, the reviewed proposal, B82 handoff and
source-bound recovery plan. Changed source, booleans borrowed as integers,
extra keys, alternate paths, old SDK14 inputs or model permission refuse.

Before creating an attempt or dispatching recovery, the builder compares the
running Python executable and loaded runtime DLL with the frozen installed
bindings. Merely having the pinned files installed is insufficient. The reviewed
recipe selects that executable by absolute path; PATH does not choose it.

The fixed authority file is
`D:/Dev/Experiments/LocalLore/2026-11-02-library-recovery-operator-v1/human-authority-v1.json`.
It is created by the coordinating human operator only after applicable fresh
approval. This code never generates that grant or infers it from inspection,
old conversation answers, missing outputs or metadata flags. Local operator
metadata is not cryptographic authentication against an administrator.

Once admitted, a create-only attempt is forced before recovery authorization,
worker dispatch or SDK work. A separate create-only worker claim, bound request,
actual parent PID/creation/executable and parent-observed child identity prevent
another worker inheriting that attempt. A failed or incomplete dispatch stays
spent; there is no retry, rollback, alternate guest or evidence deletion.

## Preparation, inputs and closure

The current `receipt_avd_prepare_recovery.execute` retains the same original
40 GiB reservation and performs the existing one-use journal, ledger-v2 migration,
directory fence and bounded SDK preparation. The original observed mkdir failure
and old proposal remain linked. The new grant must explicitly accept that
operator observation; it does not establish historical native process closure.
All existing ledger/resource/path/source/ownership checks remain mandatory.

The input builder refuses until the actual v2 entry is exactly `prepared`, with
40 GiB reserved, known fence/SDK cleanup and complete immutable history. It joins
the supplied result to the ledger outcome, intent to approved plan/recovery
authorization, completion to the exact preparation proposal/auth/marker and
preparation result. It invokes both `validate_history` and `require_cleanup`;
history validation alone is insufficient for a prepared entry.

Only then does the public normal `plan_run` create a distinct RUN proposal,
followed by fresh RUN authorization. Normal planning/authorization retain their
Windows profile-path lookup, console-token/default-AVD metadata and prepared-image
checks; production does not substitute a synthetic validator. The ADB key remains
a path in metadata; these scripts never copy or hash its credential bytes.

The exact server/SDK15 admission uses a fresh shared run ID, current 25-source
closure and server's exact ten-source subset, existing installed tool/Python pins,
three B81 artifact roles and four fixed selectors. Authority/history/source/
artifact and unchanged-ledger joins precede final activation-input publication.
Partial files remain preserved and do not trigger activation. Builder code never
retains the guest, claims boot, launches the SDK/ADB or records storage closure.

The unchanged SDK15 activation owns one guest/private ADB service and the exact
four UI methods. Its ordinary owner rebinds the same full reservation to the
RUN digest **before** boot claim/launch. Success requires original worker,
capture, controller, source and verified closure joins. The outer operator checks
the returned/stored activation result and closed RUN ledger/history. It never
manually closes the ledger or discounts an unknown outcome.
Migration and preparation release none of the original 40 GiB charge. Only
qualified normal RUN closure may replace it with measured retained storage.

## Deadline and ownership

One clock starts before entry prechecks. A new fixed-worker supervisor assigns
the process to its own existing WindowsJob primitive before releasing its only
stdin barrier. The child reads that bounded barrier/payload before any target
imports or Git subprocess. Only this retained job or a pre-barrier direct child
may be terminated. The other emulator, shared ADB and system settings are outside
its lifecycle authority.

The watchdog is 2,400 seconds from entry, with remaining-budget admission before
phases. Existing guest/activation 1,800, owner 1,700, parent 1,730, controller 1,200,
caller 1,230, readiness 400 and per-method 90 second ceilings are unchanged.
The shared environment supervisor's 1,800-second maximum is not raised or patched.
Slow prechecks can refuse or consume the overall allowance; a snapshot is not a
resource reservation or guarantee of a complete run.

After watchdog expiry/interruption, retained job/child/reader waits have up to
14 additional seconds. OS file I/O, close/flush and evidence publication are synchronous
and not guaranteed to finish within that wait bound. Unknown job/reader/capture
cleanup stays failed/unknown. Outer host cleanup cannot prove recovery fence,
SDK, guest flush, app drain or storage closure; the original charge/history stay
preserved whenever their own required closure proof is unavailable.

The proposed 256 MiB runtime, 16 MiB operation/control and 128 MiB selected
recovery allowances are coordinator-monitored retention bounds. These scripts
do not enforce aggregate directory quotas. Preserve an overrun and refuse
further work; do not delete evidence or silently grow another guest.

Finite exact admission refusals from the actual frozen EnvironmentRefused and
StorageRefused classes retain their safe reason codes. `host_commit_capacity`
is distinct from `host_capacity` (the latter combines physical-memory/disk
checks). Unknown/private text and a known-looking message from another exception
class remain generic. No refusal-time resource numbers are invented or resampled
into the original failure. Resource thresholds remain 8 GiB guest + 2 GiB commit
reserve and the separate existing 12 GiB physical-memory floor.

## Verification actually performed

Final executable/test source: `6c53d959fd14a1abf631a4c1b2e33b723a570426`.
Later publication changes are documentation only. Windows / installed CPython
3.14.7, with process-local `TEMP`, `TMP`, `TMPDIR` all `D:/Dev/_Temp`; commands ran
from the physical operator checkout. OUT below abbreviates
`D:/Dev/Experiments/LocalLore/2026-11-02-library-recovery-operator-v1`.

| Actual command/procedure | Result |
| --- | --- |
| `python -I -S -B OUT/run-host-v1.py first boolean-terminal-first-v1` | At `911552f0`: two methods, one positive/one AssertionError, 1.198 s |
| Same driver, `first boolean-terminal-green-v1` | At `4dbb2cd6`: unchanged two methods pass, 1.069 s |
| Same driver, `full integrated-initial-v1` | Initial 23 methods pass, 17.551 s; partial coverage only |
| Same driver, `genuine missing-authority-v1` | Actual CLI returns refusal/exit 1 in 262 ms; no attempt/runtime/authority created |
| Same driver, `full integrated-final-v1` | Intermediate 37 methods pass, 77.190 s, including the native host case |
| `python -I -S -B OUT/run-diagnostic-v1.py first diagnostic-first-v1` | At `32b31521`: one method/two AssertionError subfailures, 7.895 s |
| Same diagnostic driver, `first diagnostic-green-v1` | Unchanged method passes, 8.033 s |
| `python -I -S -B OUT/run-host-v1.py full integrated-final-v2` | Intermediate 38 methods pass, 105.442 s |
| Independent interpreter target, FIRST / GREEN | One method/four assertion-failing subcases before the gate; unchanged target passes after it, 11.621 s |
| `python -I -S -B OUT/run-host-v1.py full integrated-final-v3` | **39 methods pass, 139.532 s, zero failures/errors/skips** |
| Python 3.9 grammar / whitespace checks | Six new Python files pass / `git diff --check b6e8aa1e` passes |

Central host jobs have known cleanup, complete bounded binary capture and
unchanged monitored source/test/ledger pins. The final 9,615-byte stderr has
SHA256 `46c94d3824fd11a8e8a0c2340649ff977c7172b3129920c3adac4c2e81bbf2b1`.
Counts are not additive across intermediate/targeted cohorts.

The tests use actual isolated recovery journals, planning/authorization schemas,
SDK15 admission/revalidation and ledger snapshots, with explicit Git, build,
SDK-readiness, resource, ownership and activation ports. Unknown history/cleanup,
bad authority/pins, stale claims, partial publication, wrong parent/child, failed
job/thread/capture/wait and time-budget paths refuse without subsequent UI work.
A separate benign child executes the **real** `_supervise`, WindowsJob,
LiveOutput and owned-child identity lookup; both exact six-byte streams preserve
NUL, Ctrl-Z, CRLF and 0xff, with started-record-before-barrier and known cleanup.
This host proof does not establish emulator, SDK or Android behavior.

Original failures remain: False aliased zero at the outer worker-exit gate,
fixed by an exact integer check; safe admission causes were initially hidden,
fixed by exact class/code mapping. Their original oracle bodies and FIRST/GREEN
records are retained. An author's earlier operator cohort also had a fixture
phase failure: the synthetic recovery callback used the default registry argument
and a broad transition tripwire blocked its intended isolated prepare transition.
The default call refused at registry binding after directory metadata only;
no shared ledger contents were read/changed. The corrected seam requires the
exact fake registry/guest/prepared transition only inside that synthetic callback;
builder/outer transition tripwires remain. All failed/corrected captures stay.

Final review also found that a different PATH-selected Python could reach
recovery while the pinned interpreter files merely existed. The new matched
runtime positive control passes; executable/runtime-DLL mismatches at both the
builder and operator entry points reproduce four assertion failures before the
fix, then refuse before build verification, attempt or recovery after it. Exact
six-file FIRST snapshots and the original/additive request joins are retained.

Independent metadata and outer source/evidence reviews at the preceding
checkpoint found no remaining concrete blocker; narrow interpreter-fix review
also found none. Final proposal review is separate from human authorization.
Initial preservation verifies 95 checkpoint source/control pairs
(223,689 bytes) plus 12 exact historical source snapshots recovered against their
recorded request hashes. Receipt: 61,988 bytes, SHA256
`a9b3d41f8b2ab3fafc12f826b1290886eab0e0be56c888d6af070eab40e22862`.
Synthetic fixtures remain in their bounded original location, not full recovery
copies. The final revision adds separately named source/control preservation,
including interpreter FIRST snapshots and the superseded unapproved proposal.
No private raw
outputs, credentials, saves or model weights are uploaded.

## Execution gate

No real authority, recovery/migration, preparation, RUN input, SDK/ADB/emulator,
phone/model operation, retirement, settings change, other-emulator stop or merge
occurred in this packet. Production ledger remains v1/40 GiB charged and the
guest/parent/runtime/controls remain absent. Android remains **0/4**; earlier B77's
grant stays spent. Physical/ARM64/model quality/performance/accessibility/full
milestone acceptance remain open.

Next runnable action is review/approval of the frozen exact operation under OUT's
`PROPOSED_OPERATION.md`. Its authority must bind the final published operator
head and bytes; do not infer a grant from this report. Only after fresh applicable
approval may the coordinator create the exact authority and invoke the fixed
operator once. Preserve all outcomes and do not retry a refusal with that grant.
