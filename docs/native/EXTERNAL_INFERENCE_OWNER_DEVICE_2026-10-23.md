# External inference owner: emulator evidence, 2026-10-23

Refs [#9](https://github.com/OptimumAF/LocalLore/issues/9), M05.05 prerequisite
and M05.04 fail-safe support. This is local verification for review, not owner
acceptance or a completed playable-model gate.

## Executed boundary

One authorized B-only cohort exercised actual `LocalInferenceOwner`,
`DurableGateway`, production `NativeWorkspaceTransport`, JNI, the shared Rust
Host and SQLite. `LocalRoleWorker` supplied synthetic director/narrator bytes;
Rust validated them and alone committed accepted history. No inference SDK,
language model, Compose screen, MainActivity or original workspace was invoked.
The configured-native-owner metadata is configuration, not a model-load result.

The frozen class was `org.locallore.app.ExternalInferenceInstrumentedTest`.
Its six methods all had matching start/terminal PASS records and the final
runner terminal, with no skipped or unfinished method:

| Method | Exercised assertion |
|---|---|
| `externalPumpCommitsOriginalFreeTextAndReopensSameWorkspace` | Original free-text request and complete synthetic profile survive engine validation, exact commit retry and complete player-snapshot equality across owner reopen. Preparation leaves canon unchanged. |
| `readyWaitsForEngineCloseWhileMainRemainsResponsive` | An actual native Ready remains unpublished while synthetic engine close is held; accepted revision stays zero and Android Main executes a heartbeat. |
| `unknownWorkerCloseInvalidatesBorrowedHandleAndForbidsReuse` | Unknown synthetic close quarantines the owner, invalidates its already borrowed real native handle, prevents reuse, and permits a fresh owner to read unchanged accepted history. |
| `nativeCancellationDuringExternalRoleDiscardsLateResponse` | Actual Rust cancellation during a held external role cancels the synthetic worker, rejects its turn and retains the potion/revision. |
| `storyDeletionDuringExternalRoleInvalidatesSameWorkspaceTicket` | Actual native archive deletion invalidates the same production owner session/ticket and cancels the held external role without recreating the deleted story. |
| `nativeAdmissionRejectsMalformedProfilesAndResponseFramesWithoutFallback` | Actual JNI refuses null, oversized and malformed profile input, invalid handles/tickets and null/oversized response arrays; explicit scripted owners refuse external polling and one external owner cannot bind a second transport. |

Worker lifecycle methods assert execution off Android Main. Every fixture uses a
create-new synthetic child of the test package's private no-backup directory,
with overridden `applicationContext` and `noBackupFilesDir` plus canonical parent
checks. Tests acquire and close all four real workspace handle slots; the archive
case also checks all four archive slots. These assertions finish inside JUnit.
The deliberately quarantined fixture retains its small synthetic database for
diagnosis; this is not a claim that every synthetic directory was deleted.

## Artifact and execution identity

Final isolated identities are `org.locallore.app.externalverify` and
`org.locallore.app.externalverify.test`, using the existing AndroidX runner.
The final root artifact audit passed both manifest identities, permissions,
runner target, native ELF 16 KiB compatibility and ZIP alignment.
Neither manifest has `sharedUserId`; the app has no network permission.
Android subsequently accepted both APK installations. Signature-tool verification
is not attributed to that pre-dispatch artifact audit.

| Binding | Bytes | SHA256 |
|---|---:|---|
| Final APP | 23,457,912 | `6fb05b1fda50f76a96107bb71e9e38b8fbfaf74485fc15d216bf5ea613e0abf0` |
| Final TEST | 2,376,140 | `6a0f5099e32f3303e9543be8ccbce6e2a7167ed70d410077e3888bf89cd6792b` |
| Frozen on-disk test source | 19,808 | `041b9c9223238a4a4af7269afefcad327b98b08739302fb14bd89ac57465f9d5` |
| Raw instrumentation, retained privately | 4,426 | `3ca1b0960c1eba7eaf50079aa98a47993c5bd983330d95fe295c819779dc52e1` |

The source digest binds the actual CRLF build input. Its LF-normalized digest is
`4edee3a59a919d17efa4c31dbdbb3ad7db4b11afe733b5db524520cce52fe88b`;
these are two encodings of the same captured source, not two executions.

Actually executed through the frozen bounded controller:

```text
am instrument -w -r -e class org.locallore.app.ExternalInferenceInstrumentedTest org.locallore.app.externalverify.test/androidx.test.runner.AndroidJUnitRunner
```

B checks returned API 35, x86_64 and 4096-byte pages. The owned outer cohort
completed in **12,563 ms**, child exit zero with known Windows Job cleanup.
All **44** recorded clients completed with exit zero and known cleanup; local
rehashing of every recorded stdout matched its retained size/hash.
Instrumentation is command 0027. No second cohort or subsequent device query ran.

## Preservation and external cleanup

Before installation, the complete preceding **25-package** map matched its
closed prior evidence and both new package identities were absent. Installed,
after and final maps each contained exactly **27** entries: the unchanged prior
25 hashes plus the two admitted final APKs. The prior map digest is
`631f73dd6e5f67ada687536b958d5c0ac53a7d0f90277af3926b5ebf1306788a`.

The controller captured the newly assigned TEST UID from unambiguous exact
installed-package metadata only after successful installs and the complete 27-map
check. Its conditional stop path requires all six PASS records, then fresh sole
TEST process identity, matching fresh package UID, the captured installed UID
and the exact 27-map. No earlier packet's UID is reused.

After this execution, no LocalLore process remained in the bounded namespace
snapshot. Therefore **zero force-stop commands** ran, and the conditional fresh
stop-admission path was not exercised on-device. Its hostile variants were
tested purely on the host. This observation does not qualify natural process
exit for a real SDK or establish real model ownership cleanup.

All original storage/process gates passed. Final userdata availability was
**1,618,149,376 bytes**, above the unchanged **1,207,959,552-byte** floor.
There was no A query, reset, relaunch, clear, uninstall, APP stop, model/cache
operation or original-save access.

## Controller review and retained evidence

The final controller digest is
`c41b098df4081590f09a837c1f9d96ca3401a7412158a79afe1717c81a4c30fa`.
Disabled proposal `858c5a2b4ec9a640e36a84690c72126e04c373bc53c5dd912c1dff9d8182f57e`
became exact root admission
`9556ed67a088db3de6c13c44e3d4a0a5381ea5b8c64da9417b96aa2b27177911`
by changing only its two promotion flags. Coordinator and independent reviewer
rehashed all 38 proposal bindings before that one dispatch.

Final **47 distinct pure controller fixtures passed** in 0.111 seconds, including
dynamic UID capture/revalidation, wrong UID/namespace/maps, preexisting new
packages, malformed instrumentation and all-PASS-before-any-post-instrument
fencing. Earlier repetitions overlap those same cases; their counts are not
added together. Preparation initially pointed to the wrong build-output directory;
the mismatch was corrected before proposal/admission and the old source/hash
was retained. A method-count label was initially parsed as a digest prefix;
that binding attempt stopped before source/proposal mutation and was corrected
against the confirmed final audit. Both preparation failures made zero device
calls. The initial APK pair was not the admitted final pair.

The closed private selection contains **136 files / 251,634 bytes**. Its index is
23,132 bytes, SHA256
`0b3e85e78a409c96ea48bef8e7c903b168c347fc0999e8c66199d5eb4b392305`.
Selected files and index are read-only. The coordinator independently rehashed
all 136 selected files and all 44 command records, parsed the six paired PASS
records and checked the four package maps, with zero mismatches. Its later audit
receipt is outside that closed selection. Raw diagnostics, complete package
maps, assigned UID, private paths and APKs remain local. Device dispatch is
terminal, and its lease has been released.

## Remaining gates

This proves a synthetic external worker can use the production owner boundary;
it does not wire an SDK into MainActivity or demonstrate LLM storytelling.
Physical-phone, ARM64 execution, real SDK loading/cancellation/close, model
quality, sustained operation and two-emulator gates remain unqualified. A's
previous storage blocker remains unchanged. The next production task is a
verified local SDK adapter and explicit trusted model/profile selection using
this owner, with actual model/device admission kept separate.
