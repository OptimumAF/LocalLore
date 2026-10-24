# Receipt supervisor live evidence — 2026-10-24

Refs #9 (M05.05 prerequisite), #5 (M01.05 support). This packet changes only
development supervisor output handling. App, Rust, native, runtime, model and
dependency sources stay unchanged. It selects no production backend.

## Demonstrated gap and implementation

The [preceding attempt](RECEIPT_SETUP_HELPER_VERIFICATION_2026-10-24.md) stopped
at initial instrumentation255 after its first-method START. Its original
emulator supervisor later became unavailable without stdout/stderr or a final
owner result. The causes remain unknown. The former supervisor buffered output
until final cleanup, so no intermediate prefix was available after owner loss.
All old evidence and saved targets remain preserved.

`LiveOutput` exclusively creates and forces both private output files before
child creation. It retains open handles, forces each retained chunk and counts
only successful forced prefixes. One lock preserves the combined262,144-byte
cap. Any reader/write/flush/force/close failure is sticky, including a trailing
failure after stop selection. Final cleanup never reopens/truncates a log.

`supervise` keeps the same barrier, Windows job, exact-stop and expiry semantics.
Capture failure returns `evidence_failed`; process cleanup remains separately
reported. An unjoined reader gives unknown byte counts and failed cleanup,
without waiting on its potentially blocked capture lock. Partial logs cannot
prove owner liveness, terminal success, descendant cleanup or guest flush.
See the [protocol](../runtime/android/RECEIPT_AVD_ENVIRONMENT.md) for exact limits.

## Actual host verification

```text
python -B -E -m unittest discover -s scripts/tests -v
```

All 597 tests pass, zero failures/errors/skips, 58.945 seconds. Original owned
execution11991 was consumed terminal0: completion0, known cleanup, 59,766 ms.
Its 69,834-byte stdout SHA-256 is
`2f9b8d9b3b4be8229b84639087c242000125b731c1cdab1b84f4557157e349d1`.
The suite includes all 18 new independent sink/ordering/refusal/loss tests and
existing exact-stop, expiry, descendant, controller and artifact regressions.

The independent author retained three attempts. First: 16 tests, 15 PASS and
one test-only import error before the fake supervisor could spawn, owned
completion1/known cleanup, 610 ms. Second: 16 PASS/owned0/known cleanup, 1,000 ms,
but its query-refusal death oracle was weaker and is superseded. Final: corrected
18 PASS, zero failures/errors, 0.911 seconds, owned0/known cleanup, 1,250 ms.
Final stdout2,787 bytes SHA-256
`7d62c7d3554ded85404a22e8d860c58c25e399fbb304e0af4b24af2fa9de0f7f`.
All three source bindings remain unchanged; independent review rehashes them.

The final actual Windows loss case waits for acknowledgment after real fsync
of both expected prefixes. It retains non-inheritable SYNCHRONIZE handles for
the live fake worker/grandchild, kills only the captured fake supervisor, and
requires both exact handles signaled before outer safety-job cleanup. Both
prefixes survive and no terminal record appears. Their emergency60-second timer
cannot satisfy the bounded5-second terminal waits. This is synthetic host
process evidence, without an emulator, guest flush or application/model result.

No Android rebuild is required or claimed. A fresh emulator qualification is
separately admitted only after final source, artifact and environment review.

## Remaining gates

The helper classification needs a new separately admitted three-plus-one setup
cohort, eight proof reads and44 checks, final identities/capacity and known
emulator-owner cleanup. Prior synthetic passes stay separate. Real-model/SDK,
DocumentsUI delivery, reference phone, ARM64/16 KiB, privacy/cache, power loss,
quality and sustained behavior remain open; existing A/#117/#119 holds remain.
Full M05.05/M01.05 tasks stay unchecked pending complete criteria and owner
acceptance. No model transfer, inference, merge, release or access change.
