# Model receipt transaction host contract

Status: proposed host protocol for M05.05/M01.05; unwired to Android adapters or
runtime. See [ADR0011](../adr/0011-model-receipt-transaction.md).

## Interface and authority

`ReceiptModelTransaction(controlRoot, dataRoot, identity, availableBytes,
storageAdmission, checkpoint)` exposes suspending `import(open)`, `installed()`
and `discardUncommitted()`. It reuses LocalModelIdentity, LocalModelFiles and
the fixed LocalModelException/LocalModelFailure types. Construction plans paths
only; operations run on Dispatchers.IO. Cancellation retains its type; ordinary
IO failures expose fixed errors without paths or raw causes.

The caller supplies trusted roots/identity, never model text, picker display
names or arbitrary Intent paths. Existing ancestors must be real directories
without symlinks. Planned absolute/canonical roots are distinct, disjoint and
neither ancestor of the other, with existing parents. A future Android adapter
must derive/canonicalize trusted Context anchors and qualify volume identity;
this class does not establish that authority.

All access is admission-guarded, including root inspection, source opening,
copy/hash, acceptance and discard. Check again after hashing and immediately
before marker creation. Fresh copy requires available >= model bytes + reserve,
using subtraction to avoid overflow; precommit/reopen retain the reserve. A
storageAdmission callback may enforce stricter missing-byte/floor/media policy.
A failed guard never selects another root or permits cleanup through refusal.

## Fixed records

Control children: persistent `model-import.lock`, `model.receipt`, and empty
`model.accepted`. Data children: `model.owner`, `model.litertlm`, and `cache`.
No root or name comes from receipt contents. Exact UTF-8 receipt, at most 512
bytes, including final newline:

```text
locallore-model-receipt-v1
<identity.id>
<identity.bytes decimal>
<identity.sha256 lowercase hex>
<SHA256(dataRoot canonical path UTF8)>
```

Exact UTF-8 ownership record, including final newline:

```text
locallore-model-owner-v1
<SHA256(controlRoot canonical path UTF8)>
<SHA256(exact receipt bytes)>
```

Compare exact bounded bytes; no permissive parsing, path resolution or receipt
version coercion. Identity comes from the caller's trusted built-in manifest.
Path hashes bind the intended pair; they authenticate neither media nor model.
All metadata/model files must be regular and opened without following links.
Unknown control/data entries refuse. Accepted cache contents are opaque to this
proof; its directory must be safe, but this does not attest SDK cache contents.
A pending cache must be empty.

## Lock and state transitions

Acquire one global process reservation before opening the persistent OS lock;
a same-process contender returns BUSY without opening another channel to the
inode. Try an exclusive OS lock; contenders fail BUSY. Keep ownership until the
source and all owned channels actually return/close. Cancellation request alone
does not free a blocked source or its reservation. Never unlink the lock.

`installed()` takes the process reservation first. An existing persistent lock
is opened without CREATE and tried before deciding that a marker is absent;
contention therefore returns BUSY even for pending data. Absent control, or an
absent marker and absent lock, returns null without creating a lock or cache or
exposing pending bytes. A marker requires the existing lock, exact
receipt and owner, zero-byte regular marker, complete model size/digest and safe
cache. Revalidate after hashing before returning LocalModelFiles. A reader may
observe null just before another process commits; it never returns pending data.

`import()` holds one lock throughout:

1. A marker takes the full installed-validation path without opening a source.
2. An exact receipt with owned, complete valid pending data resumes acceptance
   without opening a source. Partial/corrupt pending data refuses and remains.
3. With no receipt, require dataRoot absent; exclusively write/force the exact
   receipt. With a pending exact receipt and absent dataRoot, fresh copy can
   proceed. Invoke RECEIPT_FORCED after a new receipt is forced.
4. Exclusively create dataRoot, then create/force its exact ownership record.
   Never create ownership in an already existing directory. Exclusively create
   the model file, copy bounded 64 KiB chunks, reject short/oversize/zero-progress
   input, verify size/digest, force bytes, and invoke DATA_FORCED.
5. Revalidate roots, receipt, ownership, full model and capacity. Validate/create
   empty safe cache. Invoke BEFORE_COMMIT, recheck cancellation/admission, then
   CREATE_NEW/WRITE/NOFOLLOW the zero-byte marker and force it. Successful create
   is acceptance. Invoke AFTER_COMMIT; later errors do not undo acceptance.

No failure auto-deletes files. Before acceptance, installed remains null. A
crash after complete data can resume; partial model/receipt/owner is preserved
and refused. A crash after directory creation but before complete ownership
leaves a refused orphan requiring separately authorized manual recovery. A
crash during discard after owner removal may leave the same limitation.

## Explicit discard

This internal API has no current UI caller. A future UI requires an explicit
discard action. Any marker refuses deletion, even if invalid. Without a receipt,
only absent data and absent/lock-only control permit a no-op. Otherwise require
exact receipt/owner and preflight EVERY entry before the first delete: control
only lock+receipt; data only owner, regular model no larger than expected, and
empty safe cache. Missing model is allowed; foreign, unknown, link, directory,
oversize or malformed entries refuse before any deletion.

Recheck guard/root before each exact nonrecursive delete: model, empty cache,
owner, empty dataRoot, receipt. Retain controlRoot/lock. A guard refusal stops
further deletion; partial completed cleanup is retained, not rolled back. Never
delete accepted data, recursively clear roots, repair malformed metadata or
adopt an existing benchmark/candidate directory.

## Evidence and limits

Tests must exercise real files, cross-control sharing, accepted/pending recovery,
explicit discard, unknown-byte preservation, bounds, symlinks, guards/capacity,
blocked-source cancellation and a real child JVM holding the OS lock then dying.
Checkpoints are trusted test callbacks; they add no application-facing override.
Host success proves neither Android exclusive-create/lock semantics nor target
capacity, volume identity, SDK teardown, cache privacy or power-loss durability.
The default store/native publication, canonical engine, all device holds and
capacity floors remain unchanged. No new real-model copy is part of this proof.
