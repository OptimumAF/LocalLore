# Schema4 portable capacity verification — 2026-10-23

Partial #8 M04.04 / #11 M07.03/.04 compatibility prerequisite, supporting #30 D08.07 / #31 D09.03. Coordinator-delegated author `app_storage_review`, separate `source-schema4-capacity` / `impl/m07-schema4-capacity`. This packet requalifies the fixed **Windows Host/helper** workload after additive schema4 overhead. It does not complete maintenance jobs, Android/device, partition ENOSPC or an entire milestone.

## Source and change boundary

Actual final behavioral source was frozen **before green execution** at `24e8dab6489fd7acda81f60b235383a1374ac529`. It is based on coordinator schema4 source502cacd, exact final DDL/readguard74785fde (local752a086), and historical-schema3 read-only dependency3680437 (local9337b5a). Those coordinator changes are not authored by this capacity packet. Migration004 SHA-256 remains `d5b07c6b5ebb5e63a23c7171181662f2406be4c8f507b19ac94d408e840c9500`; full-schema SHA-256 is `e9f19f3b384c52c5c7bd360e23c1db9e76314152f750a5b9f07f7a14071f8362`.

Own production-facing edits are only opt-in test profile/fixture admission and current operator documentation: Full23, relief32/initial23/rows8/attempt9/free9, schema4/fixtureformat3/v4 package-cache-output-root namespaces. Host-v1/helper JSONv2, fixed faultv1 and padding marker/ownerv2 shapes remain unchanged. Normal application caps/configuration and Core/Store/schema/jobs implementations are unchanged by the author. `scripts/audit_apk.py` gained only the coordinator-approved exact three v4 capacity IDs in its closed allowlist; ordinary/historical IDs and unknown-package rejection remain. Addenda #31 comments6373842089 and6374002918 precede those exceptional audit/README edits.

The original seed, prefix0, potion gift,36-byte key, corpus, accepted-mode deterministic provider, actual Full checks, exact retry/reopen, zero duplicate-effect assertions, helper SQL/table/3500-byte zeros/32-page ceiling/64-row bound,10s deadline/2s stop and4096-byte output cap are unchanged. No model/provider runtime, UI or alternative persistence path is introduced. Current operator docs identify the new profile and pending Android gates; historical schema3 reports/artifacts stay unchanged.

## Observed calibration, including failures

[Initial uncapped measurement](SCHEMA4_CAPACITY_MEASUREMENT_2026-10-23.md) at9337b5a measured P23/G24 with normal bundled SQLite. [Frozen profile](SCHEMA4_CAPACITY_PROFILE_FREEZE_2026-10-23.md) sourcecd96867 then ran actual isolated17/22/23 builds:17 failed at `open`,22 failed at `create`,23 reached Ready and passed repeated Full/unchanged canon/original-key queued reopen. These are actual negative outcomes at their named stages, not waived successful Full cases.

The first unchanged32 relief run deliberately retained old14/15 expectations. It actually filled8 rows / attempt9 Full, then **failed** `measured_fill_profile` before Host Full/recovery gates and successfully removed8/freed9/restored exact schema. [Calibration evidence](SCHEMA4_CAPACITY_CALIBRATION_2026-10-23.md) retains the source, logs/stdout hashes, adjacent negative cases and cleanup. Only after that measured proposal was approved did [count freeze](SCHEMA4_CAPACITY_COUNTS_FREEZE_2026-10-23.md)24e8dab update exact guards14/15/15→8/9/9. No cap/workload/payload/oracle was changed to manufacture a pass.

Earlier lightweight metadata guards also retained49 tests/4 actual valid-v4 errors from the preexisting audit allowlist. After the explicitly transferred three-ID addition,50 guards passed. A local UTF-8 label misdecode was caught in diff inspection and corrected before final freeze; the final labels match audited v4 labels. No initial failed result was deleted or relabelled as green.

## Actual final execution at24e8dab

Windows x64, Rust `1.93.1 (01f6ddf75 2026-02-11)`, Cargo `1.93.1 (083ac5135 2025-12-15)`. The explicit helper/test executable `C:/Users/Avery/AppData/Local/Programs/Python/Python314/python.exe` actually reports **Python3.14.7 / SQLite3.50.4**. This is distinct from the original uncapped closed inspector's Python3.9.12/SQLite3.38.2 and any coordinator Python3.14.9 evidence. Own D-drive TEMP/TMP and debug0/incremental0 were process-local; no global environment/tool/settings changes occurred.

Coordinator authorized exclusive sequential portable slots. Final runs used the same already isolated `cap32-target` with the same process-local `LIBSQLITE3_FLAGS=-DSQLITE_MAX_PAGE_COUNT=32`; each scenario had a new own directory. Ambient flags were refused before setting them. Every Cargo/Host/helper child exited before the slot was released. Only exact owned Python children were stopped/reaped by the unchanged helper; there was no process enumeration or unrelated process control.

| Actual final case | Result | Demonstrated boundary |
| --- | --- | --- |
| relief accept |PASS exit0|initial23→32,8 rows/attempt9 actual Full; two Host commit Full replies; unchanged player snapshot; exact-schema reopen rejects padding; remove8/free9; original live Ready key accepted once at revision1; exact retry and strict same-key reopen; zero new submit/prepare|
| relief cancel |PASS exit0|same two Full/unchanged snapshot/owned cleanup; cancellation reaches Rust while full and remains terminal after relief and strict same-key reopen; revision0,zero accepted receipts,zero new submit/prepare|
| malformed helper |PASS exit0|actual fill observed; `helper_json`; known terminal/reaped exit0; exact owned cleanup restored|
| overflow helper |PASS exit0|actual fill; `helper_output_bound`; own child kill requested/succeeded,terminal/reaped; exact owned cleanup restored|
| timeout helper |PASS exit0|actual fill; `helper_deadline`; own child kill requested/succeeded,terminal/reaped; exact owned cleanup restored|
| after-fill helper |PASS exit0|actual fill; `helper_result`/`injected_after_fill`; known terminal/reaped exit1; exact owned cleanup restored|
| cleanup-refusal |PASS safety assertions, exit0|actual fill; original `injected_after_fill`; cleanup honestly **failed** with `injected_cleanup_refusal`; root retained and no later native admission|
| original ownership units |2 PASS|cleanup requires started+terminal+reaped, not kill request; unknown ownership starts no cleanup even for an existing own synthetic path|
| Python profile/helper guards |50 PASS|strict current metadata, old/foreign/future schema and profile refusal, exact digest/migrations, RO-before-RW/identity drift/ownership/padding/output/error controls, current-v4 accepted and unknown-v5 refused|
| actual fixed helper CLI tests |3 PASS|own remove restores exact schema and control rows; unknown schema and foreign owner refused without partial drop|
| ordinary APK audit regression |6 PASS|unchanged synthetic test_audit_apk cases; normal package/permission/native ZIP/architecture gates retained|
| strict Clippy |PASS|`-p locallore-workspace --all-targets --all-features --locked --offline --jobs 1 -- -D warnings` on isolated32 target|
| format/whitespace |PASS|`cargo +1.93.1 fmt --all -- --check`; `git diff --check`|

All five helper fault reports assert **zero post-failure Host calls, zero post-failure workspace opens, exactly two helper children started**,8 actual filled rows and9 attempts. They explicitly set `no_gameplay_acceptance_claimed:true`, `physical_enospc_proven:false`, `real_model_proven:false`. Fault-case PASS means these safety/error oracles passed; it does not mean the injected operation or cleanup-refusal succeeded. The retained refusal fixture was not retried/cleared to manufacture recovery.

The Full23 cohort remains bound tocd96867; `capacity_probe.rs` did not change afterward. Final relief/count checks are bound to24e8dab. Later documentation changes do not become execution of newer shared coordinator source; integration must reconcile and verify its exact source separately.

## Reproduction commands and private evidence

All commands used the explicit pinned tool/interpreter above. `<out>` is the existing own D-drive artifact root, not a user-selected database. Commands run sequentially; `--directory` must be fresh for each case.

```powershell
# Process-local only, isolated target created for32:
$env:LIBSQLITE3_FLAGS='-DSQLITE_MAX_PAGE_COUNT=32'
cargo +1.93.1 run -p locallore-workspace --example capacity_relief_probe --locked --offline --jobs 1 --target-dir <out>/cap32-target -- --directory <out>/cap32-accept-final --python <explicit-python>
cargo +1.93.1 run -p locallore-workspace --example capacity_relief_probe --locked --offline --jobs 1 --target-dir <out>/cap32-target -- --directory <out>/cap32-cancel-final --python <explicit-python> --cancel
# Separately for each fixed selector malformed/overflow/timeout/after-fill/cleanup-refusal:
cargo +1.93.1 run -p locallore-workspace --example capacity_relief_probe --locked --offline --jobs 1 --target-dir <out>/cap32-target -- --directory <out>/cap32-fault-<selector> --python <explicit-python> --helper-fault <selector>
cargo +1.93.1 test -p locallore-workspace --example capacity_relief_probe --locked --offline --jobs 1 --target-dir <out>/cap32-target
cargo +1.93.1 clippy -p locallore-workspace --all-targets --all-features --locked --offline --jobs 1 --target-dir <out>/cap32-target -- -D warnings
python -m unittest discover -s scripts/tests -p 'test*capacity*probe.py' -v
python -m unittest discover -s scripts/tests -p 'test_capacity_integration_review.py' -v
python -m unittest discover -s scripts/tests -p 'test_audit_apk.py' -v
```

Local inert `schema4-capacity-artifacts/final-focused-report.json` contains bounded report values,16 exact source-file hashes and11 log hashes; SHA-256 **`1a28e7143a27fd803e7155943230f9bb2ee32b9cfb844ed10a7abc2354bf326c`**. It is an internal source/evidence binding, not authentication. No raw prompt/model/user story content is present; private synthetic paths/ownership roots stay outside Git. Key final log hashes:

| Artifact | SHA-256 |
| --- | --- |
| accept |4fc9943c73118907271f9f33825c3cd3dbfc1d5d192ef76a50ad2ad4245070d6|
| cancel |c889101ec99153b500419469c8ee3fa4e7aa3c6e08227ef12e7d57853972b584|
| malformed |d8c645a03970c31bb8136ad557bcabf9c544003443d8576e2fcc655b555f74ac|
| overflow |c0507a2e07a81390ba3e185fe91b27869c8f1da361a2614125a9f7ec3e943bf2|
| timeout |bdc5c4bbe5b055d31fb50e79b19f08bb623743e2d0e9e7bd22ef268dc3adb18c|
| after-fill |947dd44ca9805e6a4824d4177184ac0cdd194dd6a93895aeb3d216e4fec166a3|
| cleanup refusal |5969a905548078eff747b697f4898dc812e945ffc2fef8bff557409b565dd3fc|
| ownership units |76a1f492fd0edecbef2e110d7a770b1ac59139af35c9582f079b66517af51689|
| strict Clippy |c454830f18cb8f713fcd84742b9b7f977939e57c3e39e424c741acdee860f74c|
| Python50 guards |e0027ff035bac7ed811c3c32ce96b1050dee0cd2e673d297d5c8ad3ece00f2f3|
| actual CLI3 |d0620f04ee51a48cfec0f700b57f1522fc10bc9705fe56d701c9a5437d4a982f|
| ordinary audit6 (separate follow-up) |a553cbae11c05efe0abe098f70059a4038368b6168e5f17f2470ed7aed971143|

## Honest remaining qualification

No schema4 Android Gradle/JVM/JNI/APK/device test, Compose/native UI journey, physical ENOSPC, performance benchmark, real model/worker, arbitrary user database or protected resource was executed by this packet. Static Kotlin/manifest/profile parity and synthetic AAPT audits do not replace actual Android SQLite/process/reader behavior. Dated schema3 device evidence remains attributed to its original owner. The current README points to this partial Host qualification and keeps its device selector example explicitly unexecuted here.

Coordinator must independently review/integrate these capacity-only commits into final schema4 source, repeat appropriate cross-platform checks and arrange any separately authorized device qualification. The fixed page limit is a test compile ceiling, not a production storage limit or disk quota. No full M04/M07/D08/D09 acceptance, maintenance-consumer performance or user approval is inferred.
