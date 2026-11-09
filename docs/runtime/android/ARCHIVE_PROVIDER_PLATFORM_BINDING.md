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
