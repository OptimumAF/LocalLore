# Windows job cleanup results

B90. Refs #14 (M10.02). FIRST contract before implementation; supports the
unmerged SDK16 profile PR #360 without qualifying an Android run.

Keep `WindowsJob(pid)` and `close() -> bool`; no caller-selected implementation,
new dependency or resource framework. This development-only host owner does not
change the engine, gameplay, artifact/profile scopes or storage authority.

`close()` succeeds only when termination succeeds, a successful accounting
query observes zero active processes, and the owned job handle closes
successfully. Preserve the existing five-second polling window. The first close
latches failure before native calls. Always attempt the owned job-handle close
once, including after termination/query/clock/wait/cancellation exceptions.
Combine results only after that attempt; no `finally` success can override an
earlier failure. A failed close keeps the original handle as diagnostic state,
never as authority to retry. Repeated calls return the first bool without native
calls; an unknown/failed result cannot become success later.
An in-flight or reentrant second call returns false and keeps the first call's
final outcome false. A small private state lock protects claim/finalization;
it is never held across native calls or polling. No concurrent caller can make
a second native close attempt, wait on native cleanup, or turn that uncertainty
into success. This is an internal ownership safeguard, not a new public API.

Construction must also observe native close results. A returned owner has
successfully closed its temporary `OpenProcess` handle after assignment.
Configuration/open/assignment failure or failed/raised temporary close must
attempt every acquired handle's cleanup exactly once, without one failing tail
skipping another. Unknown handle cleanup raises a bounded `OSError`; no worker
stdin barrier is released on failed construction. Creation failure opens no
other handle. Original cancellation/errors can propagate after successful
cleanup; errors must not expose private data.

Every current Windows caller with a created child but no returned job must keep
cleanup false even after fallback child kill/wait; constructor failure cannot
certify resource closure. Current callers are runtime `_run_process`, receipt
`supervise`, Android transfer, native TCP observer and recovery outer owner.
Non-Windows behavior stays unchanged. They must preserve failed cleanup while
attempting independent wait/join/pipe/capture tails. Close safe streams after
their readers/writer stop even if job cleanup failed. Never block closing a pipe
owned by a live reader/writer. An error in one tail must not skip other safe
tails or manufacture cleanup success. Existing deadlines stay unchanged.
Capture-close false/exception or a latched capture failure must also keep both
cleanup and capture qualification false. Receipt storage closure consumes the
cleanup result, so a separate false capture flag alone is insufficient. Capture
file cancellation must not skip remaining file closes. Tests that formerly
expected successful cleanup after construction or late capture failure are
strengthened to require false; preserve their original source and failed runs.

Owned production paths are `benchmarks/runtime_spike.py`,
`benchmarks/receipt_avd_environment.py`, `benchmarks/android_runtime_spike.py`,
`benchmarks/windows_native_tcp_state.py`, `scripts/run_library_ui_recovery.py`.
Original tests live in new `scripts/tests/test_windows_job_close.py`; no existing
test assertion is weakened. Root owns README and this contract/report. Agents
provide proposals and independent review in separate existing D: worktrees;
Root alone integrates tracked files.

Acceptance needs preserved RED tests on original code, exact native-call/BOOL
and repeated-call fault tests, real caller control-flow propagation, and a
bounded real Windows Python child/descendant positive check. Fake APIs establish
injected error behavior; real host checks establish only their measured path.
Neither grants emulator/model/device acceptance. Preserve the initial/final
source maps, archives, raw captures, actual process/terminal joins and failures.

Output is `D:/Dev/Experiments/LocalLore/2026-11-02-windows-job-close-v1`;
selected recovery uses the matching `D:/Dev/Recovery/LocalLore` child. Controls
80 MiB, new generated fixtures 128 MiB, selected recovery 160 MiB. Controls and
recovery were refined from 64/96 MiB before additional capture/oracle checks so
all failures, five source archives and two profile fixture cohorts remain intact.
These selected
meters are not a disk quota or full cache/TEMP measurement. Process temporary
paths stay D:/Dev/_Temp. No actual guest, ADB, SDK16 input/authority, model,
phone, shared-ledger mutation, deletion, settings change or merge is authorized
by this contract. Frozen operator/product/build evidence remains unchanged.

Official API semantics checked 2026-11-02: [CloseHandle](https://learn.microsoft.com/en-us/windows/win32/api/handleapi/nf-handleapi-closehandle)
returns zero on failure; close each opened handle once. [Accounting](https://learn.microsoft.com/en-us/windows/win32/api/winnt/ns-winnt-jobobject_basic_accounting_information)
describes active processes associated with a job. [Job objects](https://learn.microsoft.com/en-us/windows/win32/procthread/job-objects)
documents descendant membership and kill-on-close behavior. Polling/accounting
alone does not prove that `CloseHandle` succeeded or every OS resource vanished.
