# ADR-0005: Bounded diagnostic metadata and reviewed export

- Date: 2026-10-22
- Status: implemented for review; owner acceptance pending
- Scope: M03.06, [#7](https://github.com/OptimumAF/LocalLore/issues/7)

## Decision

Keep at most 64 diagnostic records in the Android ViewModel's memory. Records
accept only fixed phase/outcome/error enums and nonnegative millisecond durations
clamped at 60,000. Sequence/drop counters saturate; no wall clock or device IDs.
Exact native error categories map to enums, unknown strings map to UNKNOWN.
The log API has no story text, exception, request, receipt, path, URI, session,
story/branch ID or arbitrary label field. Its fixed source marker identifies the
Rust-engine/fake-inference demo. This metadata is never canonical gameplay state.

Snapshots are detached immutable ASCII JSON v1, bounded at 16 KiB. Opening the
diagnostic dialog freezes a snapshot; later gameplay/export records do not
silently change the reviewed bytes. Clearing explicitly refreshes an empty
snapshot. The log survives configuration recreation with its ViewModel and is
cleared on disposal/process death. It writes no default file, Logcat stream,
clipboard, analytics or crash report. This does not prevent OS crash logging.

Export requires an open preview and explicit action. The existing AndroidX
CreateDocument contract requests application/json with a fixed suggested name.
Only the selected content URI is used, without broad storage permission or a
persistent URI grant. The writer receives a fresh byte array of exactly the
reviewed JSON; no dump of the live log, canonical engine or private files.

A picker outstanding flag is separate from consent. Dismiss/reset/disposal
revoke consent immediately, but a new picker cannot launch until the old result
is drained. Duplicate/late callbacks without a pending snapshot cannot write.
Configuration recreation retains pending consent; process death does not.

Provider open/write/close runs in Kotlin IO. A cancellation signal notifies the
provider through an IO task, because a local provider's cancellation listener
can run synchronously. One application-wide permit is held through descriptor
ownership and cancellation cleanup; new exports wait cancellably. Resources
never cross a dispatcher boundary as a returned descriptor. Writer exceptions
become fixed notices/categories without their messages entering diagnostics.

## Limits and alternatives

A provider can ignore cancellation or block writes. At most one export body and
its cancellation notification retain resources; UI cancellation does not wait
on provider code. The I/O slot is released only after cleanup returns. This is
bounded ownership, not guaranteed termination of a hostile provider.

Export is plaintext. The user-selected provider may sync outside the device.
Failure/cancellation may leave an incomplete destination; a completed user copy
is not rolled back by closing/clearing the log. No automatic upload, cloud
fallback, broad file access or external sender is introduced. Engine state is
unchanged by diagnostic clear/export or export failure.

Storing raw exception/context dumps and trying to redact later would expose
private data before redaction. A logging/export SDK would add dependencies and
network review without a demonstrated need. Streaming a mutable log after
preview would export unreviewed bytes. None is used here.

The task adds no dependency or permission. Existing API/version/license review
and actual tests are in [sources](../diagnostics/SOURCES_2026-10-22.md) and the
dated verification report. This does not qualify real-model speed, physical
phones, backup behavior, traffic, durable saves or future diagnostic schemas.
