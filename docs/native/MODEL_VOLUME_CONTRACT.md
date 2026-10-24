# Candidate-owned removable model storage

Refs #9 (M05.05 prerequisite), #5 (M01.05 supporting).
This is a separate debug experiment under [ADR-0010](../adr/0010-candidate-volume-storage.md).
It does not qualify a phone, model, removable filesystem or release storage policy.

`localLoreModelVolumeVerification=true` requires both existing LiteRT and model
setup flags, refuses picker mixing and release tasks, and creates only
`org.locallore.app.modelvolumeverify` in `build-model-volume`. False/invalid flags
fail configuration. The SDK project cache, dependency locks, no-download rules,
model bytes/hash, token budgets and native publication feature remain pinned.
The normal candidate retains `noBackupFilesDir/local-model-v1`; ordinary builds
exclude the entire LiteRT source set and SDK.

On IO, `AndroidModelVolume.select` requires API 30+, the exact experimental
package, and Context-provided external-files directories. It maps anchors back
to current StorageVolume metadata, verifies canonical unlinked ancestors, and
requires exactly one writable mounted removable non-primary non-emulated volume.
The pure policy requires the exact `<mount>/Android/data/<own-package>/files`
anchor, a bounded opaque UUID, and a different filesystem device from userdata.
The fixed model/cache root is `local-model-removable-v1` beneath that anchor.
It accepts no external path/profile argument, scans no benchmark root, performs
no migration and never redirects to an internal or alternate volume.

The process pins volume UUID, mount/anchor paths, device numbers, userdata
device and mount/anchor inodes. Every admission re-observes current facts and
capacity. An adapter refusal is sticky for that instance. Pure leases are
immutable observation pins; they do not reserve capacity or authenticate media.
No raw facts or underlying exception details enter setup state.

The volume policy retains the benchmark's **2,147,483,648-byte external** and
**1,140,850,688-byte userdata** floors. Before opening a missing model source,
external free space must also cover its fixed artifact bytes plus the existing
268,435,456-byte import reserve. Arithmetic is checked before addition. Device
controllers may require stricter observation floors. These are admission
floors, not calibrated peak inference/cache consumption guarantees.

`LocalModelStore` calls the injected guard before root access, model opens,
publication, cache/staging operations and post-hash validation. An invalidated
volume cannot authorize partial-stage cleanup. The store's original full hash,
size, cancellation checks, process/file locks, preservation and native
`renameat2(RENAME_NOREPLACE)` behavior remain authoritative. Unsupported native
publication fails closed. Tests must execute that syscall on the actual chosen
filesystem before claiming its compatibility; JVM publication uses an explicitly
labeled host substitute.

Candidate transport construction performs no filesystem work on the UI thread.
Its cached store guard reaches the deferred worker. The worker rechecks before
and after full hashing, before SDK construction/initialization, and before each
conversation/send. Failures retain uncertain resources under existing owner
fences. Cancellation/close still follow their drainage contract; an unavailable
volume does not justify parent-closing an unknown native resource. An active
native call can continue IO between observations; there is no atomic mount lease.

Canonical workspaces, prompts, transcripts and receipts retain their internal
storage route. The removable SDK cache must be treated as potentially sensitive.
Setup explicitly discloses that risk and media removal. Backup rules still
exclude external files; physical media and OEM backup behavior require separate
qualification. This packet permits synthetic test bytes only; it grants no new
model-copy destination, SDK cohort or private-story use. Prior A integrity and
#117/#119 SDK holds remain independent requirements.

The original instrumentation fixture uses 63 synthetic bytes, actual production
store/native publication, full reopen/reuse/hash refusal, a preserved cache
sentinel and a no-clobber attempt that retains a two-byte stage. It never calls
`CandidateLocalModel.store`, an inference owner, Engine, or a canonical workspace.
It requires a fresh isolated package root; it never clears an existing app to
manufacture a clean run. A pass establishes only this bounded filesystem slice.
