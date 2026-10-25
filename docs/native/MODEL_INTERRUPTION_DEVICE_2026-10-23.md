# Interrupted synthetic import device verification

One B/API35/x86_64/4KiB cohort completed: the arm produced the exact expected
process-interruption protocol, and the separately selected recovery method
reported **1 PASS, 0 FAIL**. The arm is **not PASS**. The original owned wrapper
terminated with exit 0, known client cleanup and 51,000 ms elapsed. All 64
individual clients also completed with exit 0 and known cleanup. No further
device action was performed after that cohort.

Refs #9, M05.05 interrupted-import prerequisite and supporting M05.04, root claim
6379632495 and device/report subclaim 6379649732. This report alone is owned by
the device subclaim. Source, manifests, host builds and package audits were
coordinated independently. Full milestone acceptance remains pending.

## Actual slice and result

Frozen source `24742e67e0274fc1e4576f4ec6d20b542982ac4d` supplied
`ModelPickerInterruptionTest`. The selected methods ran separately, in one
pre-reviewed controller sequence:

1. `armPartialImportAndTerminateOwnProcess` required a previously absent
   `model-picker-interruption-v1` root, actual staged 17-byte prefix, active
   blocked provider descriptor and forced private receipt. Its own UID and
   process name had to match the target application's declared identity. After
   the exact armed marker, it terminated that target process itself.
2. The controller accepted only the selected START, armed status 2 with
   `partial-import-armed-v1`, `shortMsg=Process crashed.`, runner code 0 and
   known host exit 0. There was no normal method terminal. It then read only the
   fixed proof, bounded to 1,024 bytes, and one process listing requiring target
   app absence. The observed arm-return-to-recovery gap was **0.421 seconds**,
   within its ten-second limit; both clients received actual remaining-budget
   deadlines. No APK scan or lifecycle operation occurred in that gap.
3. `recoverInterruptedImportThroughFreshPicker` passed. It checked a new
   PID/start identity, the retained exact 17-byte stage and receipt, actual old
   consumer peer-error close, and release plus independent writer close/terminal
   accounting. It reacquired the persistent store lock and removed only the
   fixed partial stage. A new explicit system-picker selection then imported
   and fully rehashed the 63-byte synthetic artifact through native no-clobber
   publication. The interruption sentinels, cache sentinel, private arm proof
   and older `model-picker-fixture-v1` model/process receipt remained intact.

The TEST-only provider's API30 prefix-pipe document kept consumer close and
writer completion independent. The original four API26 proxy documents and
production minimum remained unchanged. Deadline expiry or sticky allocation
uncertainty would have stopped acceptance. Source assertions and the selected
recovery PASS provide the descriptor-drain evidence; the later process stop is
not a substitute for it.

Fresh preflight and final metadata verified all 33 package hashes and all 33
installed UIDs. Only the two existing disposable packages were updated; the
other 31 hashes were unchanged. There was no app clear, reset or uninstall.
After recovery PASS and fresh map/UID/captured-process-subset checks, exactly
one TEST-package force-stop occurred; controller APP force-stops were zero.
Final observations contained zero owned processes and two of the exact nine
known passive legacy chooser-provider identities. Passive identities never
authorized a stop or private-file read. No old-namespace lifecycle operation
was performed by this controller.

Final available userdata was **1,386,983,424 bytes**, above the unchanged
1,207,959,552-byte floor. Host C/D storage checks also passed. These are boundary
observations, not space reservations or a byte audit of all existing userdata.

## Source, artifact and controller evidence

The final signed packages were copied into an immutable audit namespace before
admission. Exact SHA-256 and size:

| Artifact | Bytes | SHA-256 |
| --- | ---: | --- |
| APP | 73,829,632 | `0777a0c81a601a345170c4a3203cf25c09742baab0120a6ec461bfce1eebe49c` |
| TEST | 2,509,313 | `21aa7e166e6128c26ace7dbd6205fb2ef311c03c4439f6cfb9386f66404f20dc` |

Final disabled proposal SHA-256 was
`da992be188e848e36d74e776a76a92160637af4066a30e809a9c0599054c7c71`:
133 bindings, including 48 coherent live/copy/record source files, copied signed
packages, actual audit outputs, pinned build inputs, prior closed map/UID
evidence and controller/tests. Root and independent reviewer each verified the
bindings before root issued one precise cohort GO. Promotion changed only the
two admission flags; authorization SHA-256 was
`7d544d7b63b56a906a8a5a7ef953108a23c7c3fee8de719675dcf1aa384b41b2`.
The original handle was retained to authoritative terminal; observation did not
restart it.

Forty-two host-only fixtures passed with zero failures, errors or skips. Device
dispatch was mocked. They cover exact expected-interruption framing and bounded
proofs; contradictory crash/error output beside apparent recovery success;
actual remaining-gap deadlines; two-package-only updates; timeout, uncertain
client cleanup, retained app, wrong proof, expired gap, map/UID/PID drift and
foreign-main-process rejection; and cleanup only after recovery PASS. The actual
inherited process helper accepted its pre-cancelled 180-second budget without
spawning and rejected 210 seconds before spawning. The real CLI guard propagated
nonzero status.

Retained local raw evidence includes every client output/status/hash, exact arm
and recovery streams, private proof, maps, installed UIDs, process observations,
floor checks, original wrapper receipts and source copies. Child stderr is
retained as byte counts rather than raw stderr. Private identifiers remain local.
After root accepted the original terminal, the unchanged frozen closure helper
sealed 193 files / 548,138 bytes. All 193 were locally rehashed with zero
mismatches before lease release. Closed-selection index SHA-256:
`4547ca25e356b5976a83d1059b0bf8f09efcc51b522091f269f4bf0f0fac4743`.
The authorization's 133 bindings also matched at closure. A transient root-owned
README edit after terminal had been restored before that check and did not
produce a failed closure or device retry.

## Preserved preparation history and limits

All early proposals were initially disabled; none supplied standing device
authorization. The first draft's source-95 snapshot was generated while the live
test advanced to the API-level annotation correction. That mixed historical
relationship was disclosed, preserved and replaced by matching source-247 live
files, copies and recorded hashes. The API30 instrumentation fixture now uses
runner SDK filtering after the first lint check rejected a test-only API
annotation. Host compilation/readiness failures and corrected host checks are
preserved separately in the coordinated verification report.

A local proposal preparation also stopped at its broad cleanliness check on the
root's new report, before writing a proposal or dispatching any device child.
The final helper retained global cleanliness with an exact exception for that
sole root-owned untracked report; arbitrary unrelated changes were not allowed.
Parser hardening rejected unknown prose/machine prefixes and contradictory
result keys before final freeze. These were preparation corrections, not device
retries. Exactly one interruption cohort was admitted and executed.

The preceding picker/readback history remains in
[the earlier report](MODEL_PICKER_DEVICE_2026-10-23.md). Its prior closed index
was locally rehashed without mismatch:
`77e755f068bc73e2db17b3ae95e77c28ae4a4b0fbdc301088439eb10aafeee48`.
No current device observation was inferred from that earlier evidence.

This packet establishes a synthetic partial-import recovery prerequisite. Fresh
instrumentation changes target task/process state, so it does not demonstrate
normal pending-picker result delivery after OS process death. No real model,
Engine, native workspace, story, cache repair, A or physical-phone action was
admitted. No natural-process or model/runtime ownership cleanup qualification is
claimed from the scoped TEST stop. ARM64/physical-phone, real-model and remaining
M05.04/M05.05 gates stay incomplete and unchecked. Next runnable task: design and
separately admit the pending-picker framework-restoration prerequisite.
