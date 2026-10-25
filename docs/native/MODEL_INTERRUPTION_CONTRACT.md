# Interrupted local model import

Refs #9 (M05.05; M05.04 supporting). This follows the synthetic picker
contract in PR #134. It exercises the existing production store, setup
controller, resolver and screen. It introduces no gameplay authority, runtime
dependency, model identity, downloader or network permission.

## Fixed verification boundary

Only the explicit `localLoreModelPickerVerification=true` debug profile includes
the new non-exported `ModelPickerInterruptionFixtureActivity`. The sole launcher
remains the fixed real-model setup Activity. The new Activity uses the original
63-byte synthetic identity, refuses inference and resolves only
`model-picker-interruption-v1` below its own canonical no-backup directory on IO.
The older `model-picker-fixture-v1` model and process receipt are prerequisites;
both must remain byte-identical. No reset or recursive deletion is provided.

The ordinary and regular setup APK audits reject leaked interruption helpers.
The explicit audit requires both private fixture Activity implementations,
rejects test/provider code in the APP and checks both Activities have no intent
filters and are not exported. The existing TEST provider declaration and grant
boundary remain unchanged.

## Real partial read and independent owners

The TEST-only provider adds one fixed document, `<run>:partial-blocked`, titled
`Partial blocked synthetic model.bin`. Its new API-30 path uses `createPipe`
and public `ParcelFileDescriptor.wrap` to observe actual consumer closure. A
separate writer supplies the first 17 original bytes and blocks the remaining
46 until the exact authenticated run is released. The existing four API-26
proxy documents keep their existing behavior. The production minimum SDK and
dependencies do not change. Below API 30 the new document fails closed.

This avoids forcing an invalid short read through a proxy/FUSE callback. The
writer does not occupy the handler delivering consumer-close notification.
Consumer closure and writer FD closure/terminal execution have separate
counters. A detached descriptor is a failure, not closure proof. A non-null
close error is a bounded peer-error category; its prose is never parsed and
it alone does not identify a particular kernel close status. The test correlates
it with independently established target process death.

If wrapping/allocation fails after descriptor detachment, ownership is uncertain:
the reservation and failure remain sticky and further opens/configuration are
refused. Normal drained admission also requires every started writer to be
terminal with its FD closed. The 30-second writer emergency deadline is a
failure, never evidence of cancellation or successful cleanup.

## Two separately selected instrumentation methods

Select `ModelPickerInterruptionTest#armPartialImportAndTerminateOwnProcess` and
`ModelPickerInterruptionTest#recoverInterruptedImportThroughFreshPicker` in
separate instrumentation processes. Never select the entire class or broad
connected suite for this intentionally interrupted fixture.

The arm requires a fresh interruption root and preserves unknown/cache sentinels.
It opens the actual local-only, openable DocumentsUI selection, waits for the
production importer to write exactly the 17-byte regular staging prefix and
proves no published model exists. It checks the actual self UID/process name
against the target Activity's installed identity. After checking the old fixture
hashes and live blocked owner it writes and forces a CREATE_NEW private proof,
bounded to 1024 bytes, with exactly these keys:

`version,pid,start,uid,process,run,stage_bytes,old_model_sha256,old_receipt_sha256`.

Only then does it send the fixed instrumentation status-2 marker
`locallore_interruption=partial-import-armed-v1` and kill `Process.myPid()`.
This arm intentionally never reports PASS. A generic crash, assertion failure,
timeout or absence of ordinary results cannot establish the arm. The external
controller must bind the expected interrupted result to the marker, exact
private proof, observed target process absence and preserved package identities.

Recovery first verifies the proof and real partial stage before launching any
Activity or invoking `installed()` (which would recover staging). It requires a
different PID/start pair with the same installed target identity. It observes
actual nonclean consumer closure, releases only the saved provider run and
awaits writer FD closure and terminal bookkeeping with zero failures. Only then
does it start the real store: MISSING, stage absent, sentinels retained. A new
explicit valid selection must publish all 63 bytes through the actual native
no-clobber path, reopen with the full hash, report READY and retain the proof,
cache and old fixture. This recovery method requires an ordinary test PASS.

Device admission binds source, signed APKs, installed hashes/UIDs, host/device
capacity and exact allowed process identities before mutation. It does not
authorize clearing APP data, touching real weights or changing other namespaces.
Both methods and the owner observations must fit within the provider deadline;
there is no human/tool handoff while the writer remains blocked.

## Host proof and remaining gates

`LocalModelInterruptionProcessTest` starts one owned Java child with an argument
file, observes actual 17-byte staging while the OS file lock is held, verifies
competing store inspection/import refuse BUSY, kills and reaps that exact child,
then waits at most five seconds for actual store lock reacquisition, accepting
only BUSY while the exact partial bytes remain unchanged. This does not infer
instant resource release from `waitFor`. Only fixed staging is removed; the persistent lock
contents, unknown sentinel and cache contents survive. File-key identity is also
checked where the host filesystem provides it; Windows may return no file key.
A fresh full import succeeds
using the explicitly labeled host publication substitute. It does not establish
Android JNI, provider or physical-device behavior.

This packet does not implement pending-picker result restoration. Normal Android
instrumentation force-stops its target at startup/finish, so a second ordinary
instrumentation invocation cannot prove normal process-death result delivery.
An independent UI driver plus a bounded test-only callback observer and carefully
qualified `--no-restart` topology remain separate prerequisites. A fresh
controller continues to reject old picker delivery. Activity recreation, staged
file construction and runner restart are not substitutes for those missing gates.

Official sources checked: [public descriptor wrapper (API 30)](https://developer.android.com/reference/android/os/ParcelFileDescriptor#wrap(android.os.ParcelFileDescriptor,%20android.os.Handler,%20android.os.ParcelFileDescriptor.OnCloseListener)),
[proxy read contract](https://developer.android.com/reference/android/os/ProxyFileDescriptorCallback#onRead(long,%20int,%20byte[])),
[Android 15 instrumentation lifecycle](https://android.googlesource.com/platform/frameworks/base/+/android-15.0.0_r1/services/core/java/com/android/server/am/ActivityManagerService.java),
and [Java 21 argument-file escaping](https://docs.oracle.com/en/java/javase/21/docs/specs/man/java.html#java-command-line-argument-files).

Actual checks, failures and limitations belong in the dated verification,
device and independent-review reports. Synthetic results cannot qualify real
model throughput/quality, phone support, ARM64 execution, power-loss durability
or the complete M05.05 exit gate.
