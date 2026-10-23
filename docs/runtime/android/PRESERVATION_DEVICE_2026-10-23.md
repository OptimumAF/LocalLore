# Independent preservation collection, 2026-10-23

Refs #5, M01.05. One authorized read-only cohort completed all eight independent
checks. Seven matched and cache metadata mismatched. **Overall preservation
remains unverified.** The collection now supplies the older canonical-file checks
that the [role-observation cohort](ROLE_OBSERVATION_DEVICE_2026-10-23.md) did not
reach after its preservation assertion; it does not erase that earlier failure.
Milestone acceptance remains pending.

## Scope and safeguards

The selected API 35 x86_64 emulators were used only for metadata and authorized
hash reads. No app, model, SDK or SQLite engine was invoked. No installation,
force-stop, repair, model/cache copy, eviction, save write or emulator-lifecycle
operation occurred. Model/cache payloads were not read. The first emulator
received metadata and APK-identity reads only.

Trusted baselines were copied only after validating their bindings to the prior
sealed index:
`cb676ad461d2038e3c533ce10bbafc3049a047d76562e2c843bbc77b023f8b8a`.
They included the pre-role canonical metadata/hashes, selected app root and app
maps. The selected benchmark APK remained SHA-256
`9417a3e914975918d018c8a7d8954f192c09e40e10320b08c86be8a50fd7217f`.
No new artifact or model qualification was attempted.

The collector verified the selected APK, UID/data root and process absence
before/after every check, with additional owner checks around original-model
metadata and the separate phase-journal owner. Initial/final complete APK maps
were compared. Every check had fresh capacity admission. Unknown ownership,
unsafe paths/types/owners, incomplete depth inspection or failed file inspection
would stop all later device reads. A safe value mismatch stayed recorded while
independent checks continued.

Raw output was retained before parsing. Nine host-only checkpoints never claimed
provisional preservation success. Canonical status compared **all** retained
metadata fields plus SHA-256, size and presence/absence. Content-only subfacts
did not override full-baseline differences. Fixed owner markers were validated
before sibling hashes. Cache inspection rejected links, unexpected types and
unexpanded depth-limit directories, then enumerated every regular file within
that validated bound. One checked `stat` command covered all discovered paths;
a missing/error row could not silently produce a match.

## Actual results

The single owned invocation completed in **65,469 ms**, child/driver exit zero,
with known process cleanup. Exit zero means collection completed, not that
preservation passed.

| Check | Observation |
| --- | --- |
| Model metadata | matched |
| Cache metadata | **mismatched** |
| Prior canonical file set | matched |
| Guarded canonical file set | matched |
| Traced canonical file set | matched |
| Separate phase journal | matched |
| Read-only inspection capacity floor | matched |
| Inventory and complete APK maps | matched |

All eight checks had verified boundaries. The final collector reported
`collection_complete: true`, `retention_complete: true`, `clients_cleaned: true`,
`preservation_verified: false` and `stop_reason: none`. There was no unavailable
or unrun check.

The three canonical checks matched their full historical metadata/hash/size/
absence facts, including two present files for the prior set, two for guarded,
and three for traced. The separate phase check matched two present files.
This compared file facts; it did not open SQLite, replay the engine or establish
that no transient intermediate change ever occurred. Model metadata matching
does not constitute a fresh model-content integrity check or overturn an earlier
integrity failure.

All 21 APK identities on the first emulator and 23 on the second matched the
baseline, including the benchmark and separate phase probe. Final inventory
reported four emulators, no other devices and both selected devices ready.
The final inspection-floor sample recorded 9,814,319,104 host bytes,
321,416,613,888 evidence-volume bytes and 1,674,006,528 userdata bytes free.
All 25 inspection-floor samples were valid and admitted. This check's scope is
read-only inspection; it does **not** reassess or pass the earlier SDK's failed
64 MiB host-consumption budget, cache-growth budget or inference admission.

## Cache mismatch retained

The prior cache metadata matched. The guarded cache retained the previously
observed directory stat-inode difference and its 34-byte owner marker's
modification/change timestamps each one reported second below the baseline.
The traced cache also differed: its 34-byte owner marker's stat-inode and
modification/change timestamps differed, with the same one-second timestamp
decrease. Other reported rows/fields matched their respective baselines.

These are shell-stat observations. Cache/marker payloads were not hashed, and
neither content change, directory replacement nor a cause is established.
No repair or additional device query followed the cohort. The mismatch remains
visible and prevents a global preservation pass.

## Checks and retained evidence

All **627 recorded commands** completed with exit zero and known cleanup:
626 selected-device commands and one host inventory command. They included
119 APK-hash commands, 16 identity boundaries and nine retained checkpoints.
These statements cover recorded owned clients, not every possible host client.
No further device calls followed completion; device leases were released.

Nineteen host-only adapter/collector tests and three owner-driver tests passed
with fake transport. They covered mismatch continuation, full metadata comparison,
new owned sidecars, size-only metadata differences, extra files, links/depth
limits, failed stat, invalid observations, ownership/boundary loss, sink failure,
raw-first retention and the fixed 180-second barrier contract. Earlier fixture
failures and superseded drafts remain retained. Those host tests do not claim
that filesystem faults were induced on the actual emulators.

Collector source SHA-256:
`c1d040439e7208d19df82edbe83fa51ad087ca0fb0371feb87c06439a3aabd4f`.
Controller/helper/driver bindings were unchanged after execution. The closed
private index binds **1,353 files / 1,232,891 bytes**, including all command raw
outputs, checkpoints, authorizations, source, tests, observations and local cache
analysis. Selected prior sealed inputs were rechecked unchanged.

- Index SHA-256:
  `bf4656309c630ab2c183138501cecd85e5c964962a11426ede920b7c38e33236`.
- Sanitized handoff SHA-256:
  `298788dd979d19696292a84d412306d9f84b17b4f90920e2f95e833bfc3a9313`.

The earlier SDK timeout and storage failure remain failed. No model-quality,
runtime/profile, physical-phone or ARM execution qualification follows here.
The next runnable work is host-only review of retained cache-stat differences
and deterministic drift fixtures, preserving the distinction between metadata
mismatch and unavailable content-integrity evidence.
