# ADR-0011: Prove model publication through an exclusive acceptance receipt

Status: proposed; host and synthetic Android transaction checks recorded.
Explicit debug setup integration is under qualification; owner acceptance pending.
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

Implement a Kotlin/JVM transaction, initially unwired, with two trusted, disjoint
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

The transaction uses existing pinned dependencies. The initial proof changed no
active candidate selector. The later explicit debug integration described below
keeps model identity, volume pins, cache privacy policy and canonical storage.
ADR0010 and the native publication contract remain in force for profiles without
the new opt-in flag. A refused rename never selects the receipt route automatically.

## Acceptance before integration

Require actual host file, adversarial, cancellation and child-process lock/death
tests plus compilation/lint. Then separately qualify Android synthetic exclusive
creation, receipt/owner checking, process death and removal/replacement refusal
under the existing exact-one-volume admission. The current external capacity
shortfall and all reserves remain independent; this protocol cannot manufacture
space. Do not copy a real model until those gates and destination authority are
established. No phone, ARM64, 16 KiB, SDK, model quality, cache confidentiality,
power-loss or sustained-runtime result follows from this host proof.

## Partial Android observation — 2026-10-24

An isolated volume-debug fixture passed accept/reopen, cancellation across
acceptance and foreign/incomplete-data refusal on one API35 x86_64 emulator.
Its fourth process-death method failed at the remote START acknowledgment.
The separately reviewed synchronous Binder check correction compiles; a fresh
v2 run is blocked by APK staging headroom above unchanged userdata floors.
Read-only recovery verified three historical proofs and current quiet package
state, not process-death acceptance. No active setup route or fallback changed.
See [actual verification and remaining gates](../native/MODEL_RECEIPT_ANDROID_VERIFICATION_2026-10-24.md).

## Fresh transaction qualification and explicit setup integration

The separately admitted fresh target subsequently passed all four synthetic
Android transaction methods, including the corrected child-process lock/death
case. Its exact retained results and limits are in [PR146](https://github.com/OptimumAF/LocalLore/pull/146)
and the [fresh-target report](../native/RECEIPT_FRESH_TARGET_VERIFICATION_2026-10-24.md).
That result does not erase the earlier failure or qualify existing held targets.

The next bounded experiment selects receipt access only with explicit
`localLoreModelReceiptVerification=true` plus the existing LiteRT, setup and
volume verification flags. Fixed Context-derived control/data children remain
separate from all previous model roots; any prior removable candidate root
refuses. No adoption, migration, automatic retry or fallback follows a rename
failure. The ordinary application and other debug routes keep their existing
publication behavior.

The [setup contract](../native/RECEIPT_SETUP_CONTRACT.md) narrows access to pure
path planning, full-hash import/reopen and IO-only runtime admission. The same
transaction core owns exact metadata parsing, global reservation and persistent
OS lock. A verification stamp becomes available only after successful full
verification and return of all source/channel/lock closes; failure or cancellation
clears it. Runtime checks require current accepted structure and matching file
identity/size/modified metadata. Cache child writes remain opaque. The unchanged
worker still full-hashes the candidate before SDK construction and rechecks
admission at later resource boundaries. Metadata admission does not attest model
bytes against a hostile concurrent writer.

The [qualification protocol](../native/RECEIPT_SETUP_PROTOCOL.md) requires actual
production Compose controller cancellation/drain and a separate-process reopen,
using original synthetic bytes and a fresh isolated target. A direct source
callback does not qualify DocumentsUI, model transfer or SDK inference. Full
real-model, cache/privacy, phone, ARM64/16 KiB, power-loss and sustained gates
remain separate. This opt-in experiment is not a production backend selection.
