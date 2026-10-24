# Android receipt controller preparation

Refs #9 (M05.05 prerequisite), #5 (M01.05 supporting). Source/controller
preparation only; actual device qualification is pending a fresh reviewed
admission. No device, build, model, SDK or cache operation ran in this preparation.

The new `android_receipt_qualification_probe.py` has two closed profiles. A
read-only readiness profile binds the preceding sealed B identity snapshot and
rechecks inventory, exact 35 APK hashes/all UIDs, process classifications,
boot/API/ABI/page-size, volume metadata, userdata and host floors, and absence
of the fresh proof/internal candidate names. It cannot install, instrument or
read proof contents. The full profile separately binds final compiled artifacts
and frozen fixture/service/protocol sources before permitting the planned pair
update and one class-selected four-method instrumentation command. The first
emulator's integrity hold remains unchanged.

Both profiles start disabled. A separate fresh authorization must name the
exact immutable proposal hash. Source bindings are rehashed before launching
the bounded worker and again after its stdin-EOF barrier. Create-only start and
cohort paths prevent reuse. Readiness has a 90-second outer/75-second aggregate
budget; qualification has 180/165 seconds, with at most 120 seconds for its
single instrumentation client. All child clients use the existing owned process
helper; raw stdout is forced before interpretation, while stderr byte counts
are retained. Unknown cleanup or retention failure stops subsequent dispatch.

Qualification requires exactly four paired starts/passes, the closed summary,
all eight fresh proof files, empty ready markers, exact four phase/check maps,
bounded typed identities/capacities and consistent parent identity. The separate
child must have a distinct PID, positive start and the same UID. A historical
proof PID need not still be alive when read. No explicit controller force-stop,
clear, uninstall, emulator lifecycle management or old-root cleanup command
exists; ordinary instrumentation/framework setup may restart its target.

Fifteen pure host tests passed through an actual owned Windows Job child in
2,125 ms, return code zero, known cleanup, zero stderr bytes and unchanged source
bindings. Its 1,937-byte raw test log SHA-256 is
`a2fb64c470a65f52cbf7b50b4f18944e98c49b1914ff1c6238b92a1e8eecb0eb`.
Tests exercise mocked readiness/full flows, exact success and malformed runner
records, strict proof JSON/check/identity gates, unknown proof entries, nonempty
ready files, expired budgets, unknown processes/UIDs, changed authorization/source,
raw-first ownership failure and sink failure. These are controller tests, not
evidence of Android receipt acceptance, process death, native publication or
real-model compatibility. No physical-phone, ARM64, 16 KiB, power-loss, cache
privacy or model-quality gate is qualified.
