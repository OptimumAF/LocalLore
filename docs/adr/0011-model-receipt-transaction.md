# ADR-0011: Prove model publication through an exclusive acceptance receipt

Status: proposed, host proof only; Android qualification and owner acceptance pending.
Refs #9 (M05.05 prerequisite), #5 (M01.05 supporting).

## Context

The fresh PR143 synthetic call resolved the native publication wrapper and
returned EINVAL. It did not establish a rejecting layer. Repeating the same
no-replace rename cannot establish a compatible publication protocol. The
existing store must continue to refuse that failure, preserve its stage and
retain its capacity requirements.

An alternative can separate byte creation from acceptance. A model is not a
story event: its acceptance metadata grants only a verified local file handle,
never gameplay authority. No change to Rust canonical history is involved.

## Proposed decision

Implement an unwired Kotlin/JVM transaction proof, with two trusted, disjoint
roots. Write model bytes exactly once using exclusive creation. Force a bounded
exact receipt and a data ownership record; verify the complete model and create
an empty acceptance marker exclusively, last. Readers require the marker,
matching receipt, matching ownership record and full size/digest verification.
The marker's successful creation is the logical visibility point. Failure of
its later force, close or callback may therefore leave an accepted model.

Bind the receipt to the expected data root and the data ownership record to
the expected control root and exact receipt. This prevents two control roots
with different locks from adopting or deleting the same pending model. Never
create an ownership record in a preexisting data directory. Missing/incomplete
ownership metadata is retained and refused, including a crash between exclusive
directory creation and ownership recording.

Use one process reservation before opening a persistent OS lock. Hold both
until owned IO and source close return, including non-cooperative cancellation.
Keep the lock inode. No move, rename, hard link, overwrite, truncate, recursive
delete or automatic failed-import cleanup is part of this protocol. Explicit
discard validates all entries before any deletion and only removes matched,
unaccepted transaction files. A later guard refusal stops further deletes;
already completed deletes are not rolled back.

The frozen [transaction contract](../native/MODEL_RECEIPT_CONTRACT.md) defines
states, exact records, guards, capacity and the test interface.

## API basis and limits

Java specifies an atomic existence check and creation for CREATE_NEW. This
supports an exclusive empty marker, not an atomic multi-file transaction or
protection from a compromised OS. [StandardOpenOption](https://docs.oracle.com/en/java/javase/21/docs/api/java.base/java/nio/file/StandardOpenOption.html).

FileChannel.force gives storage-dependent assurances, particularly outside a
local storage device. Forcing file contents is not proof that containing
directory entries survive power loss. Reopen always revalidates the entire
transaction. File locks protect cooperating processes; filesystem behavior must
be tested on the actual target. [FileChannel](https://docs.oracle.com/en/java/javase/21/docs/api/java.base/java/nio/channels/FileChannel.html),
[FileLock](https://docs.oracle.com/en/java/javase/21/docs/api/java.base/java/nio/channels/FileLock.html).

This proof uses existing pinned dependencies. It changes no candidate selector,
Compose flow, Context adapter, SDK admission, manifest, model identity, volume
pin, cache privacy policy or canonical storage. ADR0010 and the existing native
publication contract remain in force for all current routes. This is a proposed
alternative, not a fallback following a refused rename.

## Acceptance before integration

Require actual host file, adversarial, cancellation and child-process lock/death
tests plus compilation/lint. Then separately qualify Android synthetic exclusive
creation, receipt/owner checking, process death and removal/replacement refusal
under the existing exact-one-volume admission. The current external capacity
shortfall and all reserves remain independent; this protocol cannot manufacture
space. Do not copy a real model until those gates and destination authority are
established. No phone, ARM64, 16 KiB, SDK, model quality, cache confidentiality,
power-loss or sustained-runtime result follows from this host proof.
