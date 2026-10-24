# ADR-0010: Confine an opt-in candidate model to one observed volume

Status: debug implementation under verification; device qualification and owner acceptance pending.
Refs #9 (M05.05 prerequisite), #5 (M01.05 supporting). This does not select a
production backend, supported phone or release storage policy.

## Context

The fixed candidate model and existing import reserve require 2,856,583,168
bytes. Recent synthetic setup evidence observed less available internal space.
Lowering the reserve, trusting a benchmark copy or silently selecting a public
path would change admission without establishing ownership. Canonical story
workspaces and accepted events must retain their existing internal storage.

Android supplies app-specific external directories and volume metadata, but
removable availability and confidentiality differ from internal storage.
Storage policy therefore needs a separate, explicitly enabled debug boundary.

## Decision

Keep the existing internal route as the default. Only a trusted build-time
opt-in may produce the separate `.modelvolumeverify` debug candidate. It requires
API 30 or later, adds no storage/network permission or runtime dependency, and
accepts no path/profile override from Intent, URI, model content or test arguments.

Discover candidate anchors only through the app Context's external-files API,
then map each returned anchor to its current StorageVolume. Admit exactly one
mounted read/write, removable, non-primary, non-emulated volume with a usable
opaque UUID. Null, missing, conflicting or multiple eligible observations fail
closed. Do not infer eligibility from array order or a `/storage` path string.
`StorageVolume.getDirectory()` requires API 30; state, UUID and the three volume
flags are available from API 24. The directory grants no extra access. Use the
opaque UUID string rather than the API-31 converted UUID, which can be null for
portable media. [StorageVolume API](https://developer.android.com/reference/android/os/storage/StorageVolume),
[StorageManager mapping](https://developer.android.com/reference/android/os/storage/StorageManager#getStorageVolume(java.io.File)).

Resolve one fixed candidate child beneath that Context-owned app-files anchor.
Pin the exact UUID, volume/anchor/root canonical paths and filesystem device
observation. Re-observe on IO before source/model/cache access, publication,
cleanup and SDK admission; recheck after verification before returning READY or
admitting a runtime. No mismatch can select a replacement volume or authorize
cleanup on it. Refusal must precede source/model/runtime entry where possible.
The pin is process-local; a fresh process must rediscover and fully verify.

Canonicalization of a trusted framework-provided anchor must be distinguished
from accepting an untrusted symlink child. Android app-data isolation can expose
system-managed aliases; requiring every ancestor spelling to equal its canonical
form is not a portable Android security boundary. Derive authority from Context,
pin its resolved anchor and reject model-child escape or replacement. An actual
selection refusal must remain a refusal until its failing condition is qualified;
it is not evidence that native filesystem publication was attempted.

The implemented correction resolves only the trusted internal Context no-backup
anchor before strict directory validation; external anchors and model children
retain their strict checks. An internal default-no-op closed enum may observe
selection progress for synthetic tests. Diagnostics report only the last entered
stage, a Context-alias normalization boolean and a fixed refusal type, without
paths, volume identities or exception details. A stage is not an exact failed
predicate, and diagnostic instrumentation cannot turn a refused selection into
successful filesystem qualification.

The volume policy requires at least 2,147,483,648 external bytes and 1,140,850,688 userdata bytes. Import preflight must account for missing model bytes plus the larger of the retained external floor and the unchanged 268,435,456-byte reserve, with checked arithmetic. Otherwise a large import can pass preflight and predictably fail the unchanged post-copy free-space guard. The fixed candidate therefore needs at least 4,735,631,360 external bytes before its copy. These are admission lower bounds, not reservations or calibrated runtime RAM/cache budgets; metadata, SDK cache growth and concurrent consumption can still cause later refusal. Separately admitted device controllers can retain stricter floors.

The model identity, full hash/size checks, reserve, process/file-lock ownership,
fixed staging name and native atomic no-replace publication stay unchanged.
Unknown files, earlier candidate/benchmark roots and all canonical saves remain
preserved. No copying/adopting a prior benchmark model or cache is implicit.
Unsupported locking or no-replace rename on a removable filesystem fails closed;
there is no replace-move, hard-link or alternate-volume fallback.

## Availability and privacy

The external-files API can cause framework directory creation; enumeration is
not a promise of zero writes. Android15 ContextImpl creates or filters these
app-owned anchors. Candidate code must not construct an `Android/data` tree or
bypass an unavailable Context result. [Android15 ContextImpl](https://raw.githubusercontent.com/aosp-mirror/platform_frameworks_base/android-15.0.0_r1/core/java/android/app/ContextImpl.java).

App-specific external storage needs no storage permission on supported versions,
but can disappear, and Android removes app-specific files on uninstall. That is not a forensic-erasure or offline-media cleanup guarantee. Scoped storage restricts
cross-app directory access; it does not authenticate a card or establish physical
media encryption. This experimental route must disclose removability and avoid
promising the confidentiality of internal storage. [App-specific storage](https://developer.android.com/training/data-storage/app-specific),
[Android11 scoped storage](https://developer.android.com/about/versions/11/privacy/storage).

Canonical saves, transcripts and application receipts retain their internal workspace; this route does not relocate story files. Runtime cache
contents must be treated as potentially sensitive until the pinned SDK's actual
writes are qualified. The model-file hash does not attest cache integrity or provenance; physical-media changes remain a separate cache gate. This packet does not authorize real-story SDK use or prove
that an external runtime cache contains only public model-derived data. A release
route needs a separate cache/privacy decision and owner acceptance.

Existing manifest backup disablement and explicit external-domain exclusions
remain unchanged. External app files are normally eligible for Auto Backup;
`allowBackup=false` alone does not establish every OEM device-transfer behavior.
Inspect the merged rules and test relevant OS/transport combinations separately.
[Android backup guidance](https://developer.android.com/identity/data/autobackup).

## Alternatives and limits

Insufficient internal capacity must remain an honest refusal. Arbitrary SAF
folder adoption adds an unrelated authority model. A shared benchmark root
cannot supply candidate ownership. Choosing the largest volume or dropping a
failed pin can silently redirect IO. A release-wide default change would exceed
this experiment.

Metadata/device pins are operational checks, not cryptographic identity or an
atomic guarantee against removal/remount between checks. Open descriptors, OS
mount namespaces and native SDK IO impose additional races; no compromised-OS,
physical-media or power-loss durability guarantee is made. Synthetic publication
and refusal tests do not qualify a large real model, phone, ARM64, 16 KiB device,
SDK teardown or inference. Existing #117/#119/A holds remain authoritative.
