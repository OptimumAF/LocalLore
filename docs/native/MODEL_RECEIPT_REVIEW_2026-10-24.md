# Independent model receipt transaction review — 2026-10-24

Refs #9 (M05.05 prerequisite), #5 (M01.05 supporting).

## Disposition and scope

The final host run passed 323 tests in 33 suites, including 23 receipt tests and
one real child-process test. The reviewed implementation is an unwired
Kotlin/JVM proof of logical model acceptance through an exclusive receipt,
a control-bound ownership record and
a final empty acceptance marker. It does not activate a new Android storage
route, replace `LocalModelStore`, or turn the previous native rename refusal
into a successful publication. Android qualification and owner acceptance of
[ADR0011](../adr/0011-model-receipt-transaction.md) remain pending.

This review examined actual integrated source, independent test source and the
[transaction contract](MODEL_RECEIPT_CONTRACT.md). The reviewer owned this report
only and performed no builds, device operations, model operations or shared
cache changes. The coordinator owns execution and integration. The final
execution evidence below was checked against the owned result and retained
reports. The host prerequisite is ready for review; the full
M05.05/M01.05 gates remain open.

## Findings resolved before execution

1. A receipt bound only to the data path did not prevent two control roots,
   each with its own lock, from adopting or deleting the same pending data.
   The implementation now requires exact `model.owner` bytes binding both the
   canonical control path and receipt digest. Only the invocation that
   exclusively created the data directory may create that owner. Missing,
   malformed or foreign ownership blocks adoption and discard. Independent
   tests construct the conflicting receipts and owners themselves.
2. Receipt path digests now use canonical paths. Hashing an accepted spelling
   rather than its canonical identity could prevent a later equivalent-case
   reopen on the host filesystem. The regression tests that case where the
   actual filesystem supports it; this is not a portable case-folding promise.
3. A complete pending file does not establish that an earlier force or source
   close succeeded. Before marker creation, fresh and resumed transactions now
   re-force the exact validated receipt, owner and model through existing
   noncreating, nontruncating, no-follow channels. A full-read source-close
   failure test preserves pending bytes and resumes without reopening a source.
4. A receipted or accepted transaction cannot reconstruct a missing persistent
   lock. An accepted copy cannot reconstruct a missing cache. Fresh capacity is
   checked before control/receipt creation. These refusals have preservation
   tests, including explicit source-open counters.
5. Successful marker creation is the logical acceptance point. Later force,
   close, cancellation or hook errors may still leave an accepted copy;
   reopening must validate it rather than roll it back. Actual child coroutine
   cancellation is exercised on both sides of that boundary.
6. Discard preflights every allowed entry before its first deletion, then
   rechecks admission before each exact nonrecursive delete. If a later guard
   fails, earlier permitted deletions cannot be rolled back. Documentation and
   tests explicitly preserve that limitation. Oversized pending models,
   unknown entries and foreign ownership refuse deletion.
7. Generic negative import tests originally could mistake an exception from
   the source callback for the expected refusal. The final helper counts source
   openings independently and requires zero. Child-process recovery also waits
   at most five seconds for actual OS-lock reacquisition, retrying only BUSY
   and checking pending bytes on each refusal; it does not assert immediate
   release after process termination.

No further concrete source blocker was found in the reviewed final protocol.
That finding is not authorization, device evidence or an acceptance score.

## API basis

`CREATE_NEW` specifies an atomic existence check and creation, which supports
an exclusive marker but not a transaction spanning multiple files. No-follow
opens complement, rather than replace, ancestor and trusted-root checks.
[Java StandardOpenOption](https://docs.oracle.com/en/java/javase/21/docs/api/java.base/java/nio/file/StandardOpenOption.html).

`FileChannel.force` has storage-dependent guarantees. Forcing a file does not
prove durability of its containing directory entries across power loss.
`tryLock` is nonblocking; filesystem lock behavior still requires target
qualification. [Java FileChannel](https://docs.oracle.com/en/java/javase/21/docs/api/java.base/java/nio/channels/FileChannel.html).

File locks operate across the JVM, are not a thread coordination mechanism,
and may be advisory. The process reservation therefore precedes opening the
persistent lock, avoiding competing same-process channels. The lock is kept
until owned IO returns; cancellation alone does not drain a blocked read.
[Java FileLock](https://docs.oracle.com/en/java/javase/21/docs/api/java.base/java/nio/channels/FileLock.html).

## Verification record

The first central check stopped at Kotlin compilation because the inferred
open-option array type did not satisfy the pinned compiler. The retained
failure was corrected with explicit `arrayOf<OpenOption>` typing in commit
`81c356dfd30ae78ba8e2e4af95d266273491284c`; this changed no protocol or
dependency. That run passed before a final nullable-parent warning correction
changed the default free-space callback to return zero for an absent parent.
The final compiled source is
`2f59efde07eec5a67b4ab0df5e96b0c4555360aa`. The reviewer independently read
its retained actual XML:
323 tests in 33 suites, zero failures, errors or skips. The receipt suite ran
23 tests (3.192 seconds), and the separate child-process suite ran one test
(0.407 seconds). Actual lint XML contained zero errors/fatal issues and nine
warnings, including two usable-space advisories on this new class's default
callback. These warnings do not establish a target capacity policy.

The coordinator confirmed the original owned process's terminal exit zero. The
reviewer checked the corresponding completed child result, known cleanup,
114,281 ms elapsed time, successful build log and collected results. The log
was 4,916 bytes with SHA-256
`8ecc5ee7afab3162e6a2afb3ce8c2d72c72d34e95ef46e3d742bece1e40d8222`.
No result is inferred from authored tests or a wrapper exit alone.

All 1,384 final source snapshot records (16,193,884 bytes) independently matched both
the frozen copies and live compiled source, with zero mismatches. Snapshot
index SHA-256:
`a0f1b2aec68b341f88afa06f8cf710576214af7b891377f78779aca21794db76`.
The inspected build invocation compiled app and Android-test Kotlin and ran
the candidate JVM tests, lint, dependency audit and analyzer audit offline.
It explicitly excluded `:app:buildRustAndroid` and did not assemble an APK or
execute instrumentation. No Rust/JNI, packaged artifact or device result is
claimed for this packet.

The actual task selection was `:app:compileDebugKotlin`,
`:app:compileDebugAndroidTestKotlin`, `:app:cleanTestDebugUnitTest`,
`:app:testDebugUnitTest`, `:app:lintDebug`, `:app:auditLiteRtDependencies` and
`:app:auditLintAnalyzer`, with `-x :app:buildRustAndroid --offline` and the
existing LiteRT/setup verification properties. Independent comparison found
the 62 runtime and 67 analyzer artifact records unchanged from the prior
origin packet. The analyzer reported work performed. Static reference review
found no other Kotlin callers of the new receipt API.

The reviewer independently rehashed every entry in the final immutable
selection: 4,288 files, 50,820,556 bytes, zero mismatches. Final index SHA-256:
`02db8701deb13e374adc8478939689858989c17558d7b604fb8d30b546b930f1`.
An earlier index retained an intermediate passing source header after a local
metadata-helper error. Its bytes were preserved; the final version explicitly
supersedes that header and binds the final source and all prior evidence. The
final version, not the earlier header, is the selection used for this review.

The independent tests cover exact receipt/owner bytes, marker-last visibility,
source-free complete-pending recovery, partial-copy preservation, explicit
discard/retry, unknown-entry preservation, capacity and admission boundaries,
cross-control ownership, corruption, symlinks, cancellation and a real child
JVM halted while it owns the OS lock. The child test uses a forced readiness
acknowledgment, proves competing operations BUSY, terminates only its owned
child, and resumes complete pending bytes without a source.

## Limits and next gate

Pending bytes are physically present before acceptance. The proof prevents a
model handle from being returned through this API until validation and marker
creation; it is not filesystem secrecy. Path digests do not authenticate media.
On filesystems whose `fileKey()` is null, the checks do not establish inode
identity. Trusted roots, cooperating processes and unchanged admission remain
assumptions, not protection against a compromised OS or a malicious writer.

A crash between data-directory creation and a complete owner can leave a
refused orphan. A crash during discard after owner removal can do the same.
There is no automatic cleanup or repair of those states. A source-close
exception is preserved as failure; this is not a general attestation that an
arbitrary external source released every resource. File-force ordering and host
process-death tests do not establish power-loss durability, removable-media
replacement safety, Android API behavior, SDK teardown or cache confidentiality.

The next runnable gate is separately scoped Android synthetic qualification of
exclusive creation, receipt/owner validation, OS-lock/process-death recovery
and removal/replacement refusal, using existing volume admission and reserves.
No real model copy or fallback follows from this prototype. The previous
capacity shortfall remains an independent gate; this packet made no new device
capacity observation. All canonical story storage, default native publication,
exact-one-volume restrictions, reference-phone requirements and A/#117/#119
holds remain unchanged. M05.05 and M01.05 are not completed by this host proof.
