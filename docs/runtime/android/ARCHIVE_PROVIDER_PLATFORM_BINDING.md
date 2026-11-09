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

This step validates the frozen artifact inputs. Running the two tests still
requires a guarded owner profile and the shared storage, ownership, and
authorization checks described in [the storage contract](RECEIPT_AVD_STORAGE.md).
