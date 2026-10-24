# Schema4 fixed capacity calibration — 2026-10-23

Partial #8 M04.04 / #11 M07.03/.04 prerequisite supporting #30 D08.07 / #31 D09.03. This records actual portable synthetic Host/helper execution at frozen source **`cd96867691e1f3419d250c155619f6706b0c158c`**, after the [profile freeze](SCHEMA4_CAPACITY_PROFILE_FREEZE_2026-10-23.md). The earlier [uncapped P23/G24 measurement](SCHEMA4_CAPACITY_MEASUREMENT_2026-10-23.md) remains unchanged. No Android build/device/ENOSPC or broad milestone claim follows.

## Controlled execution

All four runs used separate fresh task-owned targets and directories, `--locked --offline --jobs 1`, pinned Cargo/Rust+1.93.1, process-local TEMP/TMP, debug information0 and incremental0. Each PowerShell process refused ambient `LIBSQLITE3_FLAGS`, then set only its own `-DSQLITE_MAX_PAGE_COUNT=<cap>`. Normal targets/global settings were untouched. Coordinator authorized and serialized the slots; every Cargo/Host/helper process exited before slot release. No parallel heavy command, model, worker, app, device or protected resource was used.

The fixed example/seed/prefix0/gift/36-byte key and every retry/snapshot/reopen oracle were unchanged. The schema004 SHA remains `d5b07c6b5ebb5e63a23c7171181662f2406be4c8f507b19ac94d408e840c9500`; the helper exact full-schema SHA remains `e9f19f3b384c52c5c7bd360e23c1db9e76314152f750a5b9f07f7a14071f8362`.

```powershell
# A new explicit target and fresh fixture directory for EACH cap17,22,23:
$env:LIBSQLITE3_FLAGS = '-DSQLITE_MAX_PAGE_COUNT=<cap>'
cargo +1.93.1 run -p locallore-workspace --example capacity_probe --locked --offline --jobs 1 --target-dir <own-cap-target> -- --directory <own-fresh-directory> --prefix 0 --expect-full
# Separately, a new cap32 target/directory, frozen old14/15 oracles:
$env:LIBSQLITE3_FLAGS = '-DSQLITE_MAX_PAGE_COUNT=32'
cargo +1.93.1 run -p locallore-workspace --example capacity_relief_probe --locked --offline --jobs 1 --target-dir <own-cap32-target> -- --directory <own-fresh-initial-relief-directory> --python C:/Users/Avery/AppData/Local/Programs/Python/Python314/python.exe
```

These are exact command shapes; the literal private paths remain in local logs. The explicit helper interpreter reports **Python3.14.7 / SQLite3.50.4**. Helper JSON remains version2; fixture format3 and schema4 are separate version domains.

| Ceiling | Actual build | Example exit/result | Meaning |
| --- | --- | --- | --- |
|17|PASS,34.92s|1, `stage:open`|Preserved old-profile refusal; never reached Ready|
|22|PASS,34.27s|1, `stage:create`|Initialized schema but could not create the seeded story|
|23|PASS,34.14s|0, passed|Reached Ready23; repeated same-key actual commit Full; canon retained; strict original-key reopen queued at revision0|
|32 initial relief|PASS,37.85s|1, `original_failure:measured_fill_profile`|Actual fill/drop succeeded but frozen schema3 row-count expectation rejected current measurement|

Build times are incidental observations, not calibrated performance measurements. Negative17/22 executions are failures at their recorded stages, not passing Ready→Full cases. The23 report explicitly has `commit_full:true`, `same_key_ready_after_full:true`, `canonical_unchanged_after_full:true`, `original_key_reopened:true`, `reopen_revision:0` and all file sizes94,208 bytes/23 pages. The fixed example asserts two actual same-key Full replies before that report. `relief_recovery_proven:false` remains explicit.

A separate fixed no-CLI read-only inspector ran only after all three capped Host processes exited. It required literal owned paths, ordinary files, no sidecars and `mode=ro`/query-only; only fixed metadata/count queries were used. File size/mtime remained unchanged. It observed cap17's0-byte uninitialized file; cap22's21-page schema4 with four migrations and zero stories/branches/turns/events; cap23's23-page schema4 with one story/branch/turn and zero accepted events/jobs/packets. It did not adopt/repair/reopen a writable partial database or claim a partial initialization succeeded.

## Actual initial32 fill and cleanup — preserved RED

The coordinator explicitly required retaining old14 rows/15 attempts/15 freed-page checks for this first measurement. At sourcecd96867, the helper safely verified schema4/reference metadata, then measured:

- initial23 pages →32 pages, freelist0;
- **8** accepted zero3500-byte padding rows;
- **attempt9** failed with actual SQLite Full, error-code API available;
- exact schema4/full digest retained.

The existing Host example then rejected `measured_fill_profile` because8/9 differed from14/15. It returned `stage:native_or_cleanup`, `status:failed`; it did **not** execute subsequent Host Full, extra-schema reopen, accepted retry, cancellation or strict post-relief reopen gates. This RED is retained unchanged. The fixed known-owned cleanup ran after terminated/reaped fill, removed exactly8 rows, retained32 physical pages with **9** free pages and restored the exact schema/digest. Remove child exit0/terminal/reaped were observed; no kill request was needed. Fill/remove stderr were empty. This does not yet prove the complete relief workflow.

The measured count proposal is therefore **rows8 / Full-attempt9 / free-pages9**, while ceiling32/payload3500/operations/corpus/oracles remain fixed. This document records the proposal before any count update; those edits require coordinator review. No compaction, payload shrink, larger cap, fabricated Full, timeout adjustment, new submit or extra prepare is authorized by the measurement.

## Evidence and remaining gates

Artifacts remain synthetic/private under sibling `schema4-capacity-artifacts`, outside Git. Existing schema3 reports and artifacts are untouched.

| Artifact | SHA-256 |
| --- | --- |
| cap17-prefix0.log |8543523fe52036a6c02374ed577b61ccee198edc7c68338f9332151ef3010165|
| cap22-prefix0.log |9a4a62593cdd06ee33e4939124c354d5a7f94b7fbe0791a7fda9d79ab9080844|
| cap23-prefix0.log |96807ab66819c1001cd401e3e2d5d6af64070b7e8a6d98f60422edac9a02d152|
| fixed capped closed inspector |c419c770de1f7ad349c42b78c9656778f36b7bc2b8f1c043cc0be46a6a6fed07|
| capped-closed-inspection.log |106d0a5922802c83775db03580176c94ed4e90a7a4d5dc16299718bb24d9a57d|
| cap32-accept-initial.log |cea72a0755956bab8d70fb54c22567ebba31780b062e8d4b92499846582b2c8d|
| initial32 fill.stdout |825c6bd8f5bc371b4872ecc46822f31fdd1a84507404f6d3b6d80698c68576df|
| initial32 remove.stdout |f9af1911cb6d8e60ea0d7503b1c8d03c31a00c8afbc02d92f011cc7d85d05ca4|

The portable resource slot was released immediately after each authorized cohort. Required future gates include reviewed exact count updates; full32 accept/retry/reopen and cancel cases; fixed helper faults with unchanged ownership/no-post-uncertainty assertions; strict checks and cross-language profile parity; appropriate Android native/APK and separately authorized device qualification. Physical partition ENOSPC and model behavior remain untested. No full M04/M07/D08/D09 checkbox is checked by this packet.
