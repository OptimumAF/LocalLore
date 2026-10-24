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

## Verification

Implementation and independent adverse/loss-case tests are in progress. No new
test, emulator, model or owner-cleanup pass is claimed by this draft report.

## Remaining gates

The helper classification needs a new separately admitted three-plus-one setup
cohort, eight proof reads and44 checks, final identities/capacity and known
emulator-owner cleanup. Prior synthetic passes stay separate. Real-model/SDK,
DocumentsUI delivery, reference phone, ARM64/16 KiB, privacy/cache, power loss,
quality and sustained behavior remain open; existing A/#117/#119 holds remain.
Full M05.05/M01.05 tasks stay unchecked pending complete criteria and owner
acceptance. No model transfer, inference, merge, release or access change.
