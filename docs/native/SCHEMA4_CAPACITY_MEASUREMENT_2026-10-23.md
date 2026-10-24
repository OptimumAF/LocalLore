# Schema-4 initial capacity measurement and proposal — 2026-10-23

Refs #8 M04.04 / #11 M07.03/.04, supporting #30 D08.07 / #31 D09.03. Same capacity-only claim and separate worktree as [the frozen plan](SCHEMA4_CAPACITY_PLAN_2026-10-23.md). This records **one uncapped actual Host run**, not capped Full, relief recovery, Android build/device qualification or acceptance of a new profile. All caps and padding counts remain unchanged pending coordinator approval.

## Exact measured source

Actual measurement checkout: `9337b5acb62d12700132ee29edfa685bd4041759`. Base `502cacd18b9c43c3719b42ab37bd642b4ff363c6`; this author's only example change is `660ccd8`'s exact schema guard/stage/report 3→4. Coordinator `74785fde83f05f6b12188d71eb008f366d381d4e` is imported unchanged as `752a086`, plus read-only historical schema3 dependency `3680437` as `9337b5a`; plan binding is `fbac54b`. No production/schema implementation is authored by this packet.

Final migration004 SHA-256: `d5b07c6b5ebb5e63a23c7171181662f2406be4c8f507b19ac94d408e840c9500`. Exact measured `capacity_probe.rs` SHA-256: `fad098d0d221626359bce257e92624d31fddf61a45e485f990e0f9cb1caa05f5`. These values precede measurement. No old 502-only DDL result was reused after the coordinator's semantic-constraint fix.

## Actual authorized execution

Coordinator cleared one exclusive uncapped portable slot, then reclaimed it for Store tests. The test used a fresh task-owned D-drive target and directory; `LIBSQLITE3_FLAGS` had to be absent or the command refused. TEMP/TMP were task-local; dev/test debug information0 and incremental0; one Cargo job. Rust `1.93.1 (01f6ddf75 2026-02-11)`, Cargo `1.93.1 (083ac5135 2025-12-15)`, Windows x64. Normal bundled SQLite was built; no runtime ceiling or capped build was used.

```powershell
cargo run -p locallore-workspace --example capacity_probe --locked --offline --jobs 1 --target-dir "$capacityOutput/uncapped-target" -- --directory "$capacityOutput/uncapped-prefix0" --prefix 0
# After process exit and all owned SQLite handles closed:
python -I "$capacityOutput/inspect_closed.py"
```

Both commands exited **0**. Cargo build completed in 35.68 s; that is not a calibrated performance measurement. Original prefix0, Lantern Quay, deterministic accepted mode, potion gift, 36-byte key, exact retry, receipt equality and strict reopen were unchanged. The example reports:

| Stage | Actual bytes | 4,096-byte pages |
| --- | ---: | ---: |
| Seeded initial | 94,208 | 23 |
| Before draft | 94,208 | 23 |
| Draft | 94,208 | 23 |
| Ready | 94,208 | **23 (P)** |
| Accepted gift | 98,304 | **24 (G)** |

The gift committed normally, its exact same-key commit returned the same accepted result, and strict reopen preserved the original committed key at revision1. `commit_full:false` and `relief_recovery_proven:false` are explicit. The false `canonical_unchanged_after_full` / `same_key_ready_after_full` flags describe the unexecuted Full branch, not failed uncapped assertions. No new submit/prepare workload, compaction/VACUUM, enlarged receipt, altered seed or moved budget manufactured the growth gap.

The historical schema3 run measured Ready17/gift18; these current observations are +6 pages at both stages. Independent empty-reference SQL is now21 pages versus the dated schema3 reference15, also +6. This is consistent with added schema overhead and an unchanged one-page gift growth; this task did not rerun the old schema3 binary or establish a universal page cost across platforms/builds.

## Closed synthetic fixture verification

Fixed inspector `inspect_closed.py` was prepared and hashed **before** the run: `9b6da88857e59be4fe024c6956f25cdc8fc2ed0909395962e43621cc2da3ea2c`. It has no CLI or user path/SQL input: literal task-owned completed database and four literal migrations, no sidecars permitted. It opens only `mode=ro` / `query_only`, checks the expected metadata, and compares exact sorted user-schema rows to a separate in-memory001–004 reference. It does not copy/hash a live database, read canonical user rows, alter page/journal settings or create a writable connection to the fixture. File size/mtime remained unchanged.

Actual inspector interpreter: **Python3.9.12 / SQLite3.38.2**, not the newer Python runtime used for unrelated repository checks. It independently matched:

- application ID `1280069458` (`0x4c4c4f52`), user version4, page size4096, DELETE journal;
- closed committed file page count24 / freelist0;
- exact migration versions1,2,3,4 and matching contract strings;
- 14 user schema objects; zero `memory_jobs` and zero `memory_job_packets` rows;
- actual and reference schema SHA-256 **`e9f19f3b384c52c5c7bd360e23c1db9e76314152f750a5b9f07f7a14071f8362`**, using the existing sorted field/length-prefixed recipe.

The zero derived-job rows distinguish this initial DDL/seeded-workspace measurement from a maintenance workload. Closed-file freelist0 is observed after the successful gift; draft/Ready values in the table are the original example's safe live-file metadata, not an extra live SQL reader. No peak-memory, native device, Android SQLite execution or OS ENOSPC claim follows.

## Proposed next finite calibration — coordinator decision required

The measured proposal is **Full23**, supported by P23/G24, subject to actual adjacent capped outcomes. Do not yet change Android properties/manifests or final helper counts. After coordinator approval and another exclusive slot:

1. Preserve a schema4 run at the **old17** compile-time ceiling as historical-profile failure evidence; retain its actual failure stage rather than counting it as the intended Ready→Full case.
2. Compile separate fresh targets at **22** and **23**. At23 require create/submit/Ready success, two actual same-key gift Full replies, retained Ready/unchanged canon and strict original-key reopen to queued revision0. At22 record lower-bound refusal. No fixture/corpus/oracle/deadline is changed if either expected stage fails; report it and stop.
3. Leave relief ceiling **32** and payload3500 unchanged. The actual schema4 fill/drop row/free counts remain **unmeasured**. The old14/15 cannot be asserted as current, and a predicted arithmetic replacement is not measured evidence. Freeze reference/migration/digest/current-initial23 metadata first; run a measurement preserving original same-key/cleanup/ownership semantics, retain any old-count-profile failure, then present actual N/M for review before final exact-count updates.
4. Only once adjacent and relief evidence support the measured values, coordinate new v4 capacity identities/caches/labels and strict cross-language profiles/digests/tests. Preserve all old v3 reports/APKs/cache identities untouched. No Android build/device gate is inferred from this host measurement.

There is no need to increase relief32 based on the observed P23/G24 gap alone. If the original relief semantics do not fit the unchanged ceiling/payload, that is a new finding requiring review, not authorization to increase32 or shrink padding. Any later change to schema004 or the fixture source invalidates this source-specific measurement until explicitly reconciled.

## Retained evidence and current status

Artifacts remain synthetic/local outside Git in sibling `schema4-capacity-artifacts`; no automatic upload, model, worker, app, ADB/device, desktop/CUA, settings or protected-resource operation occurred. No failed execution occurred in this initial measured cohort. Historical failures remain unchanged in their own evidence.

| Artifact | SHA-256 |
| --- | --- |
| `uncapped-prefix0.log` | `a2ecdde2187c7a57f6066c0feaeefed04492fbbde262e6aff03b5d0bf56dfb16` |
| `closed-inspection.log` | `d8896fd8c7bd4f5bb3cc1a521d0348ef5f4a5efb257a3cd02feefdd72b92a7e2` |
| Fixed inspector | `9b6da88857e59be4fe024c6956f25cdc8fc2ed0909395962e43621cc2da3ea2c` |

The resource slot was released immediately after these two completed processes. Coordinator Store qualification has priority; no capped compilation or cap/profile/helper mutation has started. This measured proposal is in review. M04/M07/D08/D09 checkboxes, Full/relief/helper-fault, Android/device and broader gates remain unchecked.
