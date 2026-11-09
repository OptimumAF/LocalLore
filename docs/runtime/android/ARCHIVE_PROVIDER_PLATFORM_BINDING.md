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

The profile has no preparation, boot or service entry point. A controller
and a separately authorized guest handoff are required before any Android
execution. The [shared storage contract](RECEIPT_AVD_STORAGE.md) still applies.
