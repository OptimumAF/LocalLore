# Android archive provider cancellation binding

The file-only binding pins the archive-verification product APK, test APK,
and paired build record from [PR #521](https://github.com/OptimumAF/LocalLore/pull/521)
at `91de52b4e82fae062584713f84f61c47cdd76769`. It reads the retained copies
on D: and checks their byte counts and SHA-256 digests. It also checks the
test DEX for exactly two public, concrete, annotated methods in
`ArchiveProviderPlatformTest` and requires that the class and provider
fixture appear only in the test APK.

| Operation | Fixed test method |
| --- | --- |
| `archive_import_open` | `cancelledReadOnlyOpenDrainsAndNextImportReadsExactlyTheAssetSlice` |
| `archive_export_open` | `cancelledReadWriteOpenClosesTheLateDestinationAndNextExportWrites` |

Each operation selects one method under the fixed test package and runner.
The evidence parser requires a complete start and pass for that method.
A whole-class run, an aggregate run, or the other method's result is refused.

From the project worktree, run the file-only check with the existing Python:

```powershell
python -B -c "from benchmarks import archive_provider_platform_binding as p; p.verify_artifacts(p.artifact_bindings())"
```

## Owned observation and capture

`benchmarks/owned_archive_provider_platform.py` uses the shared owner and v4
capture/replay for a dedicated SDK26 profile. It requires the fixed D: guest
root, the archived artifact pins and the closed source roster, including
the two DEX audit modules. The observer verifies the APK bytes before it
opens process handles. The capture accepts only this profile's observer.

The two test methods have separate one-use claims. APK staging binds each
input to its role, and package installation uses `-R` to disallow replacing
an existing app. The profile admits no model, arbitrary selectors,
app-process commands, or `run-as` access. See the
[Android package manager implementation](https://android.googlesource.com/platform/frameworks/base.git/+/3b88497957c0c6c8645d35bdf55099d0bb98b4ec/services/core/java/com/android/server/pm/PackageManagerShellCommand.java).

## Bounded controller and replay

`benchmarks/archive_provider_platform_controller.py` takes the pinned admission
and running records of an already-owned guest. It waits up to 120 seconds for
boot, checks Android API 35, x86_64 and user 0, then requires both packages to
be absent. It stages and checks each APK before a non-replacing install.

The controller captures the import test, verifies both installed package
identities again, then captures export and repeats the identity checks.
Each test has a 90-second limit within the 20-minute controller budget.
The controller keeps the command records in order, refuses any mismatch or
uncertain observer closure, and replays the same checks from the saved bytes.

## Preparation-only gate

`benchmarks/archive_provider_platform_preparation.py` uses the fixed SDK26
experiment parent and the [shared storage contract](RECEIPT_AVD_STORAGE.md).
Its plan records the archived APKs, source and interpreter pins and the
shared API 35 preparation proposal for an 8 GiB, four-core guest.
Capacity preview reads the shared ledger and grants no reservation. A
blocked preview skips the host resource checks.

The prepare entry point requires an exact preparation-only authority file
and its SHA-256. The reviewed proposal must identify the exact plan and
ledger digests. Before calling shared preparation, the guard checks the
current inputs and writes an exclusive one-use claim. The shared path checks
the ledger again under lock before reserving 40 GiB. A failed attempt retains
its claim and records.

Success requires the unbooted prepared receipt, worker output and closure
proof, and matching prepared ledger entry. This scope ends at preparation.
Boot and Android execution still require a separately authorized owner handoff.

## Candidate activation

`benchmarks/archive_provider_platform_admission.py` replays the preparation
approval, claim, worker and unbooted guest receipts. It checks the current
ledger for the exact prepared reservation. A previous preparation receipt
keeps its original ledger observation if an unrelated entry later changes.

With the exact SDK and helper inputs, the module stages a run proposal,
owner admission, and review for the two-test sequence. It pins the current
ledger and requires unused boot outputs. The admission includes only the
expected authorization digest. The actual authorization and owner handoff
require separate activation approval and fresh preboot checks.

The complete source roster, including the activation supervisor, uses the
fixed `preparation-plan-sdk26-v2.json` and `prepare-proposal-sdk26-v2.json`
slots at the same guest parent. The file suffix identifies the frozen input
pair. The record schema and the one-use preparation scope are unchanged.
Both slots are create-only. The earlier v1 pair stays at its original paths
as evidence of capacity refusal on its earlier source revision.

From the physical D: worktree with D: temporary paths, the file-only freeze
and inspection can run before requesting preparation approval:

```powershell
python -I -S -B -c 'import sys; sys.path.insert(0, "."); from benchmarks import archive_provider_platform_preparation as p; pin=p.build_plan(*sys.argv[1:]); print(p.inspect(pin, p.env.binding(p.LEDGER)))' $sdkPath $javaPath
```

Inspection reports the current ledger and whether it would fit. If either
storage limit is exceeded, it skips the host resource checks. Neither step
creates a guest or grants preparation authority.

## Activation handoff and terminal evidence

`benchmarks/archive_provider_platform_handoff.py` checks a separate one-boot
grant tied to the reviewed candidate, admission and current ledger. It requires
an exclusive activation claim before publishing the exact authorization bytes
whose digest is already in the admission. Before boot, it replays the candidate
and preparation files and requires a supervisor identity and enough time
remaining for the controller and shutdown.

`benchmarks/archive_provider_platform_closure.py` checks the completed
controller against the independently observed owner and its worker. It
requires normal stop, complete cleanup and the matching closed storage
receipt before accepting the two test results.

## Supervised owner adapter

`benchmarks/owned_archive_provider_platform.py` requires a pinned handoff
from the activation supervisor. It holds the expected process identities and
checks job membership and live ancestry before dispatch. The worker checks
its immediate job and the owner-to-supervisor chain. The
[Windows job query](https://learn.microsoft.com/en-us/windows/win32/api/jobapi2/nf-jobapi2-queryinformationjobobject)
uses the calling process's immediate job when jobs are nested.

The adapter checks host resources, a separate 256 MiB records allowance,
guest ports and the approved ledger. The shared runtime checks the private
ADB port. The prepared reservation transitions to retained under the
ledger lock before the guest starts. The controller requests an owned stop,
and the parent publishes completion only after closure replay.

## One-use activation supervisor

The operator entry point accepts only the SHA-256 of the separately approved
SDK26 activation authority at the fixed activation path. It replays the
candidate against the current ledger, verifies the pinned Python, and creates
the exclusive activation claim before any child starts.

The shared watchdog assigns the worker to its Windows Job before delivering
the pinned request. The worker waits for the supervisor's identity receipt and
checks the actual parent and Job before publishing the exact run authorization.
It starts the owner behind a second stdin barrier, records its observed process
identity and verifies ancestry and Job membership before releasing it. The
owner checks that same receipt before entering the existing SDK26 owner adapter.

The activation window is 30 minutes from initial validation. The shared
watchdog closes the outer Job on exit or timeout. The host accepts success
only if replay finishes by 60 seconds after the activation window ends.
Success requires the expected two owner status records, clean watchdog
closure, both verified instrumentation results, and the closed ledger receipt
for the independently observed owner. The result pins the exact startup
receipts, handoff and captures used for replay. The operation retains its spent
claim and any failure records.
A failure requires review of the original evidence before another proposal.

From the physical D: worktree, with TEMP, TMP and TMPDIR set to
`D:\Dev\_Temp`, use this command only after exact one-boot approval:

```powershell
python -I -S -B benchmarks/archive_provider_platform_operation.py --authority-sha256 <approved-sha256>
```

Host verification of this supervisor leaves both Android methods unrun.
Preparation and activation each require their own approved inputs.
