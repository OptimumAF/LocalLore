# Schema-4 native compatibility source review — 2026-10-23

Refs #11 M07.03/.04, #30 D08.06/.07, #31 D09.03. Independent compatibility review by `desktop_runtime_profile`, delegated by the coordinator. Claims precede this report: #11 comment6374178951, #30 comment6374179275 and #31 comment6374179547. Review branch `review/m07-schema4-native`, isolated `source-schema4-native-review` worktree.

## Source and conclusion

Reviewed immutable coordinator source **`5e44ea91bfa9e93ecf583e31a26937efdfa96366`**. No production or existing test files were changed by this review. **No concrete compatibility blocker was found in the inspected delta.** This is a source review and a small in-memory metadata check, not Android/JNI/WebView execution or acceptance of schema4, M07, D08 or D09.

This reviewer previously authored the independent memory-jobs regressions and reviewed their coordinator fixes. That work is not a new independent approval of the entire jobs implementation here. The present review is limited to native/client compatibility, version boundaries, deletion metadata, test profiles and source/evidence reconciliation.

## Contract boundaries inspected

| Boundary | Actual source behavior |
| --- | --- |
| SQLite owner | `locallore_storage::SCHEMA_VERSION` is4. `locallore_workspace::DATABASE_SCHEMA_VERSION` references that constant; it is not a second hardcoded owner. Initialization applies001–004. Migration of supported older writable databases adds the missing earlier derived schemas before004 and verifies the final schema. |
| Workspace/IPC wire | Workspace and native command/reply protocol versions stay1. Android requires the live workspace's separate `database_schema_version` to equal4 both at admission and snapshot refresh. It does not accept an arbitrary future version or relabel an older live database. |
| Desktop inspection metadata | Native `storage_metadata` accepts supported actual database versions1–4, retains their actual version, and refuses5/missing metadata. This supports historical read-only inspection separately from current writable Android admission. Database export manifests use the shared schema constant. |
| Branch deletion preview | Rust emits preview2 and nine removal-table counters. Android accepts only preview1 or2. The exact legacy1 set has seven tables; exact2 adds `memory_jobs` and `memory_job_packets`. It preserves the received version. Unknown, missing or extra keys and negative/coerced counts are refused. |
| Whole-story deletion preview | Rust emits preview3 and12 counters. Android retains exact legacy1/2 shapes and adds jobs/packets only for3. Version4 is refused. Root/branch/count consistency checks remain in place. |
| Derived packet total | Rust's preview counts old derived packets plus job packets. Android requires `derived >= old_packets` and `derived - old_packets == job_packets`, after nonnegative integer validation. This avoids an overflowing `Long` addition accepting a forged total. Jobs themselves are not incorrectly counted as packets. |
| Controller admission | `BranchDeletionController` changes only the closed preview-version range1–2 within its existing token/story/branch/root/head/title guards. Its immutable consent copy, exact prepared-object identity, consume-before-commit and cancellation/generation fences remain. Whole-story controller has no old1–2-only guard to strand preview3; the native decoder owns the closed wire-version validation. |

The reviewed `ArchiveNativeWire` decoder retains bounded input, strict UTF-8 handling, closed outer reply shapes, fixed error categories and nonnegative integral counts. Branch preview2 is not confused with archive format2 or the separate database schema4. The native archive gateway still binds fixed app-private workspace/staging paths, epoch and positive prepared token; these compatibility changes add no path, SQL, code, model or inspection privilege to the client.

Historical platform assets remain historical. The platform-roundtrip comparison checks current source schema4 and historical source schema2, then normalizes a separately parsed historical comparison object only. It does not rewrite the import bytes, asset, accepted history or receipt. The Rust example uses the shared schema constant for the current side. Supported historical archive import is not permission to accept an incompatible live workspace.

## Schema and capacity reconciliation

Independently rehashed migration004:

`d5b07c6b5ebb5e63a23c7171181662f2406be4c8f507b19ac94d408e840c9500`

The in-memory001–004 reference has14 user schema objects, migration rows1–4 and schema digest:

`e9f19f3b384c52c5c7bd360e23c1db9e76314152f750a5b9f07f7a14071f8362`

That digest matches the fixed Kotlin helper and Python reference. It includes the added jobs/packets DDL and updated schema-migration structure. The helper still checks application identity, version4, exact migration contracts, full user-schema digest, page/journal profile and database integrity before its writable padding phase. A foreign or merely relabeled schema is not accepted by a numeric version check alone.

`git diff --quiet 24e8dab6489fd7acda81f60b235383a1374ac529 HEAD --` on the capacity Gradle/properties, capacity/relief/fault sources and manifests, probes, fixed padding helper and APK audit returned0. Thus those relevant behavioral sources at the reviewed integration equal the capacity author's frozen final source. This is source equivalence, not a new execution of that source by this reviewer.

The current profile is consistently **Full23 / prefix0 / relief32 / initial23 / padding8 / attempt9 / freed9**, database schema4, fixture format3. The distinct v4 IDs, Gradle project caches, output directories and synthetic roots are used across properties, strict Gradle equality guards, manifests, Kotlin fixture admission, app-process helper admission and Python/AAPT probes. Ordinary builds remain uncapped and use their normal package/cache/output. Ambient SQLite cap flags remain refused at the strict profile entry. The APK audit's addition is a closed list of the three exact v4 test IDs; accepting historical IDs for auditing does not make current probes accept a historical profile.

The unchanged padding marker/owner2, helper JSON2 and fixed fault1 labels identify different protocols, not database or fixture versions. They are checked inside new v4 owned namespaces and were not widened to adopt an old fixture. The helper still has fixed operations, bounded padding and pipe output, finite child waits, exact owned-child cleanup, and conservative unknown-ownership refusal before later native admission. No arbitrary helper command/SQL endpoint was added.

The reviewed capacity report preserves the actual failed old17 open, adjacent22 create, old14/15 relief-count and initial audit-allowlist outcomes. It separately attributes actual Full23 to the earlier `cd96867` freeze and final relief/helper checks to24e8dab. The later exact-count guards are based on observed8/9/9, not arithmetic predictions. Dated schema3 device/capacity reports remain historical; the earlier Android compatibility proposal's pending calibration is superseded by the separately linked schema4 calibration packet, not rewritten as if it had originally measured schema4.

## Existing regression coverage inspected, not executed here

- `TimelineProtocolTest` uses the actual `DurableGateway`: live4 initializes with wire1; live2/3/5 refuse before resume/gameplay; later schema5 refresh cannot publish a snapshot. These are Android instrumented tests, not locally executed JVM proof.
- `ArchiveIntegrationTest` covers actual JNI workspace contract1/schema4 reopen and archive import/reopen expectations. `ParentRetentionNativeTest` retains the historical schema3/archive1 input. Required device execution remains pending.
- `ParentRetentionProtocolTest` wire cases cover exact branch1/2 and story1/2/3 shapes, unknown versions, missing/extra/negative counters, mismatched total and `Long.MAX_VALUE` derived-sum forgery.
- The new `BranchDeletionShellTest` uses the actual controller: preview2 reaches prepared state, future3 is cancelled/refused without commits/story mutations. These tests do not prove the Android JSONObject/JNI decoder ran.
- Native desktop metadata tests inspect all accepted versions1–4 and future5 refusal. The legacy native UI future-version fixture was moved to5 rather than leaving4 falsely unsupported.
- Python helper/profile tests include older1/2/3 refusal before writable open, future5 refusal, exact004 digest/migrations, missing/altered objects, owner/marker/identity drift and current-v4 versus unknown-v5 package/profile checks. The actual CLI tests explicitly distinguish fixed helper schema restoration from a Host Full proof.

No unique failing regression was identified, so no duplicative test or copied implementation was introduced. A source search for remaining live-schema3 guards across the assigned native/Android/workspace/probe paths found no forgotten current-owner guard. Matches for fixture format3, historical migration contract3, preview3 and story revision3 are separate intentional contracts.

## Actual reviewer checks

Only the following checks ran in this review; no Cargo, Gradle, app, helper child, worker, model, device, ADB or desktop action ran:

1. Clean worktree and exact HEAD inspection; scoped source reads and diffs; `git diff --check`: PASS.
2. `Get-FileHash crates/locallore-storage/migrations/004_memory_jobs.sql -Algorithm SHA256`: matches the004 hash above.
3. The scoped `git diff --quiet 24e8dab... HEAD -- <capacity paths>` described above: exit0.
4. Python3.14.9 / SQLite3.50.4, importing the existing fixed probe only to call `baseline()` and `schema_digest()` on `:memory:`. Assertions require14 objects, exact full digest and exact004 SHA; result PASS. No persistent fixture was opened and no fill/drop/helper CLI ran.

Reproduction of check4 from the repository root, with the already installed task-local Python:

```python
import hashlib, importlib.util
from pathlib import Path
spec = importlib.util.spec_from_file_location("schema4_review", Path("scripts/capacity_padding_probe.py"))
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)
rows = module.baseline()
assert len(rows) == 14
assert module.schema_digest(rows) == "e9f19f3b384c52c5c7bd360e23c1db9e76314152f750a5b9f07f7a14071f8362"
assert hashlib.sha256(module.SCHEMAS[-1].read_bytes()).hexdigest() == "d5b07c6b5ebb5e63a23c7171181662f2406be4c8f507b19ac94d408e840c9500"
```

An initial Windows `rg` invocation with wildcard path arguments produced OS123; replacing those arguments with directory searches/explicit files completed the inspection. A guessed `archive.rs` path was absent; no claim relies on that failed read. Neither is a test result.

## External evidence and remaining gate

Coordinator-reported results are attributed to their executor, not this reviewer: Store full source33e5 had184 passing tests plus an old filename-filter failure and five existing ignores; the corrected affected selection passed19 at71a; new jobs23 passed and the seven earlier independent memory-jobs regressions passed. The capacity author's exact-source report records Host/helper and Python evidence as described above. Those counts are not rerun counts at this review commit.

At report freeze the coordinator owns the ordinary offline Android both-ABI APK/testAPK/JVM/lint build at5e44. Its final output has not been incorporated here. Current Android/JNI instrumented protocol/archive/retention execution, actual capacity APK/helper process behavior on Android, native application rendering and model execution are not proved by this report. Compilation or a synthetic AAPT profile audit must not be presented as those executions. Physical ENOSPC and full maintenance/model-archivist acceptance also remain outside this compatibility slice.

Next runnable work is to finish and record the coordinator's exact-source Android/native/frontend checks, preserving any setup or semantic failures; inspect/audit current ordinary and opt-in APK metadata where built; then separately arrange the required authorized Android instrumentation/device qualification. Any DDL/profile/workload change invalidates the corresponding exact calibration binding until reconciled. This report changes no milestone checkbox, release, approval, license-audit flag or repository setting.
