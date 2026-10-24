# Deterministic negative receipt-status transport

Refs #9 (M05.05 prerequisite), #5 (M01.05 support). This is a separate debug-only
negative experiment. Its one selected Android test must fail. An observed
negative experiment is never a setup, restart, model or gameplay pass.

Build the existing explicit receipt profile. The shared failure reporter runs
the requested block unchanged; if it throws, all claim/capture/encode/send work
is guarded and the identical original Throwable is rethrown, without wrapping
or adding suppressed errors. The ordinary setup phase wait still uses its
ten-second deadline and the existing process-wide one-attempt claim.

`ReceiptSetupFailureTransportTest#preservesOriginalFailureAfterDedicatedStatus`
performs no Activity launch, filesystem/model/SDK operation or import. It creates
a closed ACCEPT trace with CHECK_START/CHECK_MISSING, expected READY, actual
MISSING, error NONE and zero source counters. Through the shared reporter it
throws the fixed original `AssertionError("receipt_setup_failure_transport_v1")`,
uses the actual instrumentation `sendStatus(1337, Bundle)` and asserts identical
Throwable identity before rethrowing. Diagnostics failing must not replace it.
JVM tests separately inject claim/capture/send failures and one-shot behavior.

`benchmarks/receipt_setup_failure_transport.py` requires a distinct disabled
proposal scope `receipt_setup_failure_transport` and exact separate four-key
authorization, with frozen source/APK hashes and live environment lease. Reuse
the existing create-only environment's separately reviewed prepare/run phases
on a fresh target, with unchanged image, ports, capacity and ownership gates.
Do not reuse, clear or replace an old installation or model cache. No model
copy, inference, SDK call or emulator lifecycle command belongs to the guest
controller.

Its hardcoded Owner subclass admits bootstrap observations, exactly two fresh
installs and one exact negative class selection. Class/method/commands cannot be
chosen by proposal or CLI. The ordinary controller retains only its original
two selections. Raw output is forced before interpretation, with unchanged
client/aggregate caps, live-owner checks and cleanup refusal. No helper binding,
proof read or restart follows the deliberately failed instrumentation.

The negative parser requires START/status1337/one failed end in order, exact
class/method/runner/counts, exact closed synthetic payload and the original
AssertionError as the primary error in stack/stream/one-failure summary. Unknown
records, other failures, causes/suppressed errors, duplicates, malformed or
oversized diagnostics, passing summaries and wrong terminal codes refuse.
The ordinary three-pass parser must independently reject the same raw stream.
Retained raw failure evidence is not sufficient without these checks.

After guest completion request the exact owned environment stop, consume its
original terminal and verify cleanup/preservation/capture closure. Preserve all
saved targets and attempts. No guest flush or disk integrity is implied.
This experiment can qualify dedicated status delivery and tested error
preservation only. It does not diagnose the earlier intermittent READY timeout,
qualify current Activity/ViewModel capture after recreation, or replace the
separate positive three-plus-one/44-check evidence. Real-model/SDK, DocumentsUI,
phone, ARM64/16 KiB, privacy/cache, sustained/quality and A/#117/#119 gates remain.
