# Preservation collection verification, 2026-10-23

Refs [#5](https://github.com/OptimumAF/LocalLore/issues/5), M01.05 partial, claim
`6376152312`. Exact base is open/unmerged [#118](https://github.com/OptimumAF/LocalLore/pull/118),
`498a5250cc5f3b55bc4371295814ce4a5acb6e02`.

## Working boundary

The earlier preservation helper asserted cache metadata equality before recording
older database/journal, storage and inventory checks. Its mismatch therefore
left independent evidence missing, despite known client cleanup. The new fixed
collector separates safe value mismatches from ownership/identity uncertainty.
It does not relax comparisons, repair earlier observations or establish canon.

The [versioned protocol](PRESERVATION_COLLECTION_V1.md) fixes eight adapters,
sixteen maximum boundary checks and nine maximum durable checkpoint calls.
Mismatched/unavailable observations continue only through fresh package/UID/root
and process-absence checks with sticky known ownership. Unexpected errors,
invalid statuses, unsafe identity/process state and failed retention stop later
reads. Checkpoint mutation cannot alter frozen callbacks or the returned state.
Sink snapshots never claim preservation success; the final return alone can do
so after the last sink and local ownership check.

The collector contains no transport, model, SQLite, write/repair/retry or device
lifecycle operation. Trusted adapters own raw-first retention, fixed paths,
command deadlines, extra owner checks and fresh capacity admission. This is a
bounded development interface, not a sandbox, canonical validator, backend
selection or general device controller.

## Host verification actually performed

```powershell
python -B -E -m unittest discover -s scripts/tests -v
```

The integrated selection passed **402 tests in 4.988 seconds**, including
**22 new independent methods**. Focused reviewer selections of 21 then 22 also
passed; they overlap the integrated selection. Tests cover all eight error
positions, safe mismatch/unavailable continuation, pre/post boundary failure,
strict literal-True predicates, sticky owner loss, final sink poison/failure,
deep-copy isolation, frozen callback references, private exception suppression,
invalid input/status types and exact 9/16 success bounds.

The coordinator found and fixed a checkpoint edge: ownership lost immediately
before retention could produce an extra stopped checkpoint on the next loop.
The reviewer independently ran the targeted case against the original immutable
`6173ba0`: it genuinely failed with 3 sink calls versus 2 expected. The corrected
`3e205f9` source passes the final 22-method selection. The reviewer did not claim
the initial discovery; the red/green logs and both source copies remain retained.
Corrected collector SHA256:
`c1d040439e7208d19df82edbe83fa51ad087ca0fb0371feb87c06439a3aabd4f`.

No production Kotlin/Rust/JNI, APK, SDK, runtime, model, dependency, canonical
rule or workload budget changed. No new JVM, native or physical-device execution
is inferred from host tests. Existing unrelated untracked build directories
were preserved. Retired Markdown trackers remain pointers; tickets own progress.

## Fresh read-only observation actually performed

One separately admitted, frozen adapter cohort completed on the two selected
Android 15/API 35 x86_64 emulators. It used the existing isolated cacheprobe APK
`9417a3e914975918d018c8a7d8954f192c09e40e10320b08c86be8a50fd7217f`.
No APK/native build, install, application invocation, process stop, emulator
lifecycle operation, SQLite opening, model-content read or inference occurred.
The original model/SDK/native pins are unchanged from the
[role-observation verification](ROLE_OBSERVATION_VERIFICATION_2026-10-23.md).

The stdin-barrier child ran once through the existing 180-second Windows Job
owner: **65,469 ms, child 0, known cleanup**, no stdout/stderr. The same live
handle was followed to terminal; there was no relaunch. All **627 commands**
completed 0 with known client cleanup: 626 device commands and 1 host inventory
command. There were **16 fresh identity boundaries**, **9 durable checkpoints**
and **25 valid capacity samples**. Checkpoints all retained preservation=false.
No device call followed terminal completion; later analysis/sealing was local.

| Fixed observation | Current comparison |
|---|---|
| Original/selected model metadata | matched; metadata only |
| Old cache metadata | mismatched |
| Prior canonical files | full metadata/hash/size/absence matched |
| Guarded canonical files | full metadata/hash/size/absence matched |
| Traced canonical files | full metadata/hash/size/absence matched |
| Separate phase journal | full metadata/hash/size/absence matched |
| Fresh inspection storage floors | matched; not a full-turn consumption test |
| Package maps and inventory | matched |

The final collector result is observed, collection_complete=true,
retention_complete=true, clients_cleaned=true, boundary_verified=true,
stop_reason=none, and **preservation_verified=false**. Child 0 means completed
collection, not preservation success. See the [safe aggregate](PRESERVATION_RESULTS_2026-10-23.json)
and separate [device report](PRESERVATION_DEVICE_2026-10-23.md).

Prior/guarded/traced canonical workspaces respectively had 2/2/3 present fixed
files, including owner markers; their remaining fixed SQLite sidecars/journal
leaves were absent as expected. The separate phase workspace had 2 present
files. Content-only comparisons also matched, but did not replace full stat
fields or alter the verdict. File hashes are finite current comparisons,
not SQLite replay or proof that no transient change ever occurred.

Prior cache metadata matched. Guarded cache retained the previously seen
directory inode difference and 34-byte owner-marker mtime/ctime shifts of -1 s.
The newly completed traced-cache check also found its 34-byte marker inode
changed and mtime/ctime shifted -1 s. Cache payload and marker contents were not
hashed; replacement, writer, timing and cause remain unestablished. No repair,
deletion, rebaseline or metadata criterion was removed to make the check pass.

Initial/final package maps matched, 21 packages on one selected target and 23 on
the other. Final inventory was 4 emulators, 0 other devices, selected targets
ready. The last boundary observed 9,814,319,104 host-userdata free bytes,
321,416,613,888 evidence-host free bytes and 1,674,006,528 selected-userdata
free bytes. These satisfied the fresh inspection floors only. The earlier
64-MiB post-consumption gate remains failed; these samples cannot admit another
SDK turn or reconstruct the earlier missing final checks.

## Adapter review and limitations

The private adapter passed 19 host mock methods; its owned driver passed 3 host
mock methods. These overlap selections, not additional device experiments or
actual Job fault injection. Drafts and initial fixture failures were retained.
Review corrected baseline-absent sidecar handling, nested/dangling link guards,
all-regular-file cache enumeration, checked stat vector/count/path validation,
and safe size-only model metadata comparison before the single actual cohort.
Full metadata comparison and unsafe-structure rejection remain required.

The checked stat vector avoids relying on `find -exec stat ... \;` as evidence
that every operand succeeded. The reviewer retained official Android 15
`android-15.0.0_r1` [find source](https://android.googlesource.com/platform/external/toybox/+/refs/tags/android-15.0.0_r1/toys/posix/find.c),
[stat source](https://android.googlesource.com/platform/external/toybox/+/refs/tags/android-15.0.0_r1/toys/other/stat.c)
and [error handling](https://android.googlesource.com/platform/external/toybox/+/refs/tags/android-15.0.0_r1/lib/lib.c).
This is a pinned reference-source review, not attestation of the emulator's
actual Toybox binary or an executed device fault case. Exact returned path/count
validation independently refuses incomplete operand output.

The safe aggregate is **4,435 LF bytes**, SHA256
`f533011c9cfac0b29de98cc1f56e87a18c00c879d7c303b76e24f6a068767b5f`.
Private paths, identifiers, command output, model weights and database/journal
payloads stay local. Independent review and integrity checkpoints are recorded
in the [review report](PRESERVATION_REVIEW_2026-10-23.md).

M01.05 remains **in_review, partial**, unchecked pending full criteria and owner
acceptance. M01.01 physical-phone qualification remains blocked. Successful
guarded generation/narration, quality, ARM execution, sustained memory/thermal
and a production backend/profile remain unqualified. Current canonical matches
do not retroactively complete missing final preservation in earlier cohorts;
their timeout, storage and cache failures remain recorded. No merge, release,
access or protection change was performed.

## Selected-file integrity checkpoints

These overlapping selections bind exact retained bytes, not unique experiments.
The coordinator rehashed the device, test and official-source selections with
zero mismatches and checked all 627 command stdout sizes/digests against raw
files. The collector source is unchanged from the tested bytes above.

| Selection | Files / selected bytes | Index bytes / SHA256 |
|---|---|---|
| Root host checks, source and public reconstruction | 11 / 84,652 | 1,780 / `6ff50355fb9d1657c2bb4316ce422beb66da7f9ea17017f938fe2e327ba786d7` |
| Independent host regression tests | 9 / 32,245 | 1,529 / `18bbf32f575ae77953bacc8e42b207c15f3526b3b4e7f97ea0b0b641fd03f156` |
| Pinned official Android source supplement | 6 / 69,622 | 1,137 / `a57b8b1e6bf8a60a61069b965cbbf0e271be26d9256c17781fc43d3e9f00c8f5` |
| Closed read-only device cohort | 1,353 / 1,232,891 | 230,349 / `bf4656309c630ab2c183138501cecd85e5c964962a11426ede920b7c38e33236` |

Next runnable step: reconcile M05.04's host fail-safe implementation against
current accepted shared-engine source, [#104](https://github.com/OptimumAF/LocalLore/pull/104)
and active claims before choosing a separate missing implementation case.
The current read-only preservation gap is now measured; further metadata
diagnostics must not displace runnable product work. No new inference is
admitted by this packet's inspection floors.
