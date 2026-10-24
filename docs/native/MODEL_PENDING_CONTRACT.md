# Pending local model picker across process death

Refs #9 (M05.05; M05.04 supporting). This follows the interrupted-import
fixture in PR #136 and preserves its data. It tests a different failure point:
Android owns an outstanding document result when the background app dies.

## Fixed boundary

Only the explicit `localLoreModelPickerVerification=true` debug profile includes
`ModelPickerPendingFixtureActivity`. It is non-exported and has no intent filter.
The normal setup Activity remains the sole launcher. The private Activity uses
the existing original 63-byte synthetic payload and native publication path,
refuses inference, and owns only `no_backup/model-picker-pending-v2`. The failed
v1 attempt's root is retained without reset. The older
picker and interruption roots, receipts, sentinels and cache remain unchanged.
There is no reset, downloader, new dependency, permission or gameplay authority.

The production Activity calls a default no-op observer after its existing picker
handler. The observer receives only selection presence and before/after phases;
it receives no URI or source and cannot admit a result. The fixture overrides it
to write bounded primitive receipts on IO. Synchronous callback counts, sticky
overflow/error flags and actual coroutine completion prevent missing or canceled
receipt writes from becoming success. Ordinary and regular setup APK audits
reject these helpers; the explicit audit requires their private implementation
and excludes TEST/provider code from APP.

## Real framework relationship

The two selected methods in `ModelPickerPendingTest` run separately with
`am instrument --no-restart` and `-e waitForActivitiesToComplete false`.
Each asserts the exact target UID/process and the latter argument. Neither uses
an ActivityScenario or Compose rule. Ordinary instrumentation startup/finish can
force-stop or finish the target, destroying the relationship being measured.

Before bootstrap, the external controller requires the normal real-model root
`no_backup/local-model-v1` to be absent, including dangling symlinks. Unexpected
presence stops the experiment without reading weights, clearing data or cleanup.
The controller normally launches only the existing setup launcher to obtain the
live app required by no-restart instrumentation; it never chooses Start.

`armPendingPickerAndTerminateOwnProcess` launches the private Activity without
CLEAR_TASK, uses a five-second readiness deadline for its exact visible synthetic identity
before acting, selects the actual Choose control, and observes one real local-only,
openable wildcard OPEN_DOCUMENT request. DocumentsUI must be foreground while
the Activity is saved and PICKING, with no source opened or staging/model file.
It forces a CREATE_NEW ready proof and marker, then waits at most 30 seconds for
one exact fixed handshake. The host independently requires the matching server
task/Activity to be STOPPED, nonfinishing, app-stopped, with saved state and a
non-null saved bundle. The local saved flag alone is insufficient.

After that server proof the host creates only `kill-request-v1.txt`, containing
`kill-v1\n`, without clobbering or following links. The arm rechecks task, process,
picker, provider and preserved hashes, forces the final proof and ready-file
hash, sends its second fixed status marker, and kills only `Process.myPid()`.
The arm intentionally never passes. Success requires both status markers, exact
proofs, the expected crash framing, the original owned client reaching terminal
state, and independent absence of the armed process. A timeout, generic crash,
assertion failure or runner restart cannot substitute.

## Restored callback and explicit fresh consent

After death, an independent shell UI driver selects the fixed wrong synthetic
document in the retained real DocumentsUI task. Android must restore the same
task with saved state and a new process, then deliver the actual registered
callback. There is no manual registry dispatch or normal app relaunch.

Receipt one must show selected=true, restored saved state, a fresh controller
outside PICKING, unchanged before/after phase and zero provider opens. The UI
must reach MISSING. A later explicit Choose and valid document selection must
produce receipt two, PICKING to IMPORTING, and actual READY. Receipt snapshots
may precede descriptor drain; final verification requires exactly one attempt,
open and close, zero active descriptors/failures, and no retained URI permission.

`observeRestoredPickerAndFreshImport` attaches without restart and performs no
Activity, UI or registry mutation. It requires exactly two completed receipt jobs,
matching run/task/process proofs, no overflow/error and no staging file before
store reopen. The real native store must already have published all original
bytes, and a full reopen/hash must match. All six older fixture hashes must
remain identical. This observer requires an ordinary test PASS.

## External owner and evidence

The host binds frozen source, signed APKs, installed hashes/UIDs, exact allowed
process identities and capacity before mutation. It preserves all installed
package identities and unrelated package bytes. It never clears app data.
The original asynchronous arm client remains owned through terminal state;
observation timeouts never authorize a replacement invocation.

UiAutomation has one owner at a time. Before arm termination, server dumps only
prove foreground/task state. Afterwards, each shell UI dump must finish before
another operation. A fresh shell-only directory holds at most 16 numbered XML
files, retained locally. Exit code or the dumper footer alone is insufficient:
each dump must be a bounded regular non-symlink file with valid restricted XML.
Actions admit only fixed APP/DocsUI controls and the fixed TEST root/documents.
Connection failure, malformed state, unknown controls or exhausted budgets stop
the experiment; they do not trigger a blind retry or broader navigation.

Use plain `dumpsys activity activities` for live task proof, with bounded local
output and exact host component/task selection. Android 15's global `-p` option
also sets `dumpClient=true`; omitting `-c` does not make a package-filtered dump
server-only. The first read-only settlement exposed that earlier review mistake.
Its retained output is qualified accordingly. The repaired profile admits only
source-supported horizontal Hist spacing and the display header's exact optional
`(organized)` suffix; other malformed/duplicate/foreign records still refuse.

Official sources: [Activity Result lifecycle](https://developer.android.com/training/basics/intents/result),
[Android 15 instrumentation lifecycle](https://android.googlesource.com/platform/frameworks/base/+/android-15.0.0_r1/services/core/java/com/android/server/am/ActivityManagerService.java),
[Activity saved-state dump](https://android.googlesource.com/platform/frameworks/base/+/android-15.0.0_r1/services/core/java/com/android/server/wm/ActivityRecord.java),
and the pinned AndroidX monitor 1.7.2 source discussed in the dated independent
review. Actual commands, attempts and limitations belong in the dated reports.
Synthetic emulator checks do not qualify physical phones, ARM64, real-model
performance/quality, power-loss durability or the full M05.05 exit gate.
