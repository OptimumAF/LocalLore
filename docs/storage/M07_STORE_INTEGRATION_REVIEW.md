# M07 Store/migration integration source review

Refs #11; review claim
[6359213686](https://github.com/OptimumAF/LocalLore/issues/11#issuecomment-6359213686).
Reviewer `/root/desktop_runtime_profile` authored the earlier extractive/FTS
prototype. **This is independent review of the coordinator's Store/migration and
version integration only, not independent approval of that prototype.** The
prototype's separate reviewer retains that scope. This packet changes only this
new document; no implementation, build, test, application, model, device, CUA,
process control, merge or release was performed by this reviewer.

Reviewed working root additions after `6512077` (prototype on accepted main
`ac7fe2c`), frozen integration `8ea750a`, follow-up
`169beb4ff221e231b32bf4f94e87ce3951f77f6b`, and accepted-main integration
`d97770c8dac2927e3584e43f697ecb609b3aa5ac`, then documentation/test follow-up
`ec2b1a40395e98a44b8f0a9d9e9d8c7cfbea5150`. Own isolated review branch:
`review/m07-store-final` at ec2b1a4. Root owns the implementation and fixes.
The reviewed additions are 002 migration; storage lib schema/open/verify/backup/
Store memory wrappers; prototype integration-only DDL source/error mapping;
workspace private application open; Host additive actual database version;
native inspection version metadata/export manifest; and related tests/version
assertions. Also reviewed the two-file saved-workspace label correction
`66e9b3b8ee60f7d77d3ac1707c123cf62b05a596` by its exact diff. Other D06 UI and
accepted-main changes are not re-reviewed here.

## Concrete finding and resolution

**P2, corrected: database inspection displayed protocol version as database schema.**
At 8ea750a, the Host intentionally retained workspace `schema_version: 1` for its
existing client contract and added `database_schema_version: 2`. But native
`inspection_storage` still copied the former into its storage metadata reply;
InspectionPanel displays that distinct endpoint as `Schema 1` next to the actual
SQLite location. The new database and database-export manifest were schema 2.
This was an externally visible provenance/version mismatch, not a canonical data
corruption or a reason to change the compatible Host protocol field.

The reviewer reported the exact old endpoint/display path. Root's 169beb4 repair
extracts `storage_metadata`: it validates the protocol field separately and copies
the actual database version into this distinct native endpoint's displayed
schema_version. Missing/unsupported actual versions fail Wire. Its native unit
asserts actual schema 2 and rejection when actual version is missing. The reviewer
inspected this exact fix and the coordinator's passing native test output. The
finding is resolved.

**Second display mismatch, found by the native compatibility agent/coordinator:**
the saved-workspace details also labeled protocol `schema_version` as simply
`Schema 1`. Patch 66e9b3b uses optional `database_schema_version` for the explicit
`SQLite schema` label, `schema_version` for `Workspace contract`, and separately
labels Domain contract. The reviewer inspected the exact App.tsx/model.ts diff:
missing/null actual-version values display `Not reported`; they do not silently
substitute contract 1. The patch changes no controller or generation path. This
is source verification, not execution of its final frontend/native render checks.

No remaining concrete blocking Store/migration integration failure was found in
the reviewed source. This is not a score or owner acceptance.

## Migration and database identity

The unchanged 001 schema's Git object is
`3b30dc184e77cf94d515295db05a2016a297daf7` at both accepted base ac7fe2c and final
reviewed integration. The story/branch/entity/turn/accepted-event/witness/projection
tables, receipts and canonical event formats are not changed by this diff.
002 changes the migration-record table to represent versions 1 and 2, retains the
version-1 contract, records the fixed version-2 contract, and adds only the ordinary
STRICT derived_memory cache table with branch/actor foreign keys and bounded JSON.
No permanent FTS virtual/shadow tables, connection pool or second story ledger.

For v1, Store::open first inspects identity, acquires IMMEDIATE, then rechecks the
locked identity and rejects a changed/future owner. It exactly verifies the known
v1 object SQL, application/version identity, complete migration-record rows,
quick_check and foreign keys. Only then does it require a new backup destination.
The separate read connection's consistent SQLite backup completes and fsyncs
before migration DDL runs. The write reservation prevents an intervening canonical
writer during that backup/migration sequence. Failure returns without executing
002; migration DDL, migration records, new user_version and final exact verification
share the transaction before commit. The earlier empty-v0 path remains explicit
and requires a backup for an existing empty file; nonempty unversioned/foreign/
future/altered schemas fail closed. No migration silently adopts them.

`open_application` is a trusted native-path policy for existing app-private files:
a BackupRequired result chooses a new sibling filename with process/time/counter
uniqueness and retries the same verified opening path. create-new backup semantics
prevent overwrites; a race re-enters identity checks. A migration error is not a
reason to substitute an empty ephemeral story. This policy does not accept a path
from model or renderer JSON or claim protection against a hostile filesystem.

`open_read_only` verifies exact known version 1 or 2 and never migrates. Retained
v1 backups can still resume their original recorded receipts without a model;
new derived-memory operations on legacy read-only v1 are unsupported/fail closed.
The unchanged backup API copies the actual captured SQLite data, including its
schema version, rather than rewriting a legacy backup as current.

The new v1-specific test preserves both an existing backup canary and source bytes
on collision, then races two actual migration openers. They may see current
schema 2 or Busy; exactly one migration backup is created and the recorded receipt
survives. The unit fault test checks both an SQL error after derived DDL and an
extra object that fails final verification after user_version 2 has been written;
both roll back exact object SQL, migration records and user_version to v1. The
reviewer suggested the latter case to distinguish rollback of an actual written
version from the earlier pre-version-write failure. Root implemented it in
ec2b1a4 and supplied the passing focused log; this was an evidence coverage
improvement, not a demonstrated migration correctness defect.
These are real SQLite fixtures constructed from unchanged 001, not evidence of
migration on a physical phone or an archived production user's database.

## Store authority, freshness and compatibility

Public derived-memory DTO types are exported, while raw borrowed-Connection helpers
remain crate-private. `PreparedMemory` is opaque and non-Deserialize. The new
Store::prepare_memory/read_memory/search_memory wrappers obtain their Engine only
from that Store's validated resume; callers supply scope/actor/query metadata,
not an Engine, accepted event, raw SQL or mutable projection. Replay validates
canonical receipts and normalized ledger/witness consistency; derived cache is
not loaded as canonical truth. publish consumes the opaque prepared token and
retains the module's IMMEDIATE head/exact-source publication fence. It does not
introduce a different canonical commit or inference path. Read/search retain the
existing exact rederivation and physically actor/scope/revision-partitioned TEMP
FTS construction. This review inspects that wiring, not independently endorses
the prototype's extraction/ranking implementation. DiskFull gains a fixed Full
category rather than leaking native SQL/path/error text.

The Engine replay and later cache-read transaction are separate snapshots. A new
accepted head between them is rejected by the module's exact head fence, not
silently combined with the old Engine. Explicit invalidation validates the owner
snapshot/actor and checks expected head before deleting only its derived partition.
The public API adds no caller Lab grant; app/generation authorization remains with
the native integration before any future renderer command exposes this API.

**Retained qualification limit:** memory_engine checks cancellation before and
after the existing full Store::resume. That replay itself has no cancellation
callback. Therefore the borrowed visitor's bounded callback interval does not
bound cancellation latency of the entire Store operation. A cancelled replay's
result is discarded before preparation, and there is no partial canonical write,
but maximum-history responsiveness remains unqualified. Root must keep this limit
in publication evidence and must not claim prompt whole-operation cancellation.
Job queues/durable partial cursors, LLM archivist, corrections/branches, exact delta
supplementation, model use of summaries and maximum-scale performance remain open.

Workspace host-v1 keeps its existing `schema_version: 1` compatibility field and
adds actual `database_schema_version: 2`; native Repository is constructed only
from the current verified application Store. Kotlin's existing JSONObject
schema-version-1 check and desktop's existing workspace reader therefore retain
their contract. The distinct native storage-inspection endpoint now displays the
actual database version. The native full-database copy manifest uses the current
workspace database version and declares derived cache in its contents; that app
path opens/migrates the active workspace before taking the copy. Ordinary scoped
InspectionBundle's schema/format 1 is a different export contract and remains
unchanged. Those exports do not become full private database copies or consume
an inspector lens as generation knowledge.

## Coordinator evidence read, not reviewer execution

The reviewer read the following local root-produced logs under
`source-memory/target` in the coordinator's ignored D task root:

- `store-integrated-workspace.log`: independently summed all result lines to
  **249 passed, zero failed/ignored**, after d97770c accepted-main integration.
  This predates the ec2b1a4 test-only second rollback case.
- `store-version-rollback.log`: the existing rollback unit containing both fault
  cases passes after ec2b1a4: **1 passed**, 11 filtered out, 0.01s.
- `store-review-followup.log`: **4/4** actual derived Store/migration tests,
  including v1 collision/concurrent openers, passed in 0.10s.
- `store-integrated-clippy.log`: integrated strict workspace check completed
  successfully (0.33s). Earlier `store-clippy-fixed.log` also passes. Root reports
  strict all-target Clippy invocation; the log itself does not print its command.
- `store-native.log`: native Windows **20 passed, 1 existing symlink-privilege
  case ignored**, plus **2/2** harness-wrapper tests. Includes the corrected
  actual-schema-version unit. Run predates the accepted UI merge; the reviewed
  native storage/export code is unchanged by that merge.
- `store-native-default.log`: default native feature **18 passed, 1 existing
  symlink-privilege case ignored**. `store-native-clippy.log` completes the
  development native strict check successfully (4.89s).
- `store-android.log`: actual source rebuild of Rust JNI for x86_64-linux-android
  and aarch64-linux-android, then Gradle unit-test/lint/debug and instrumentation
  APK assembly tasks; **BUILD SUCCESSFUL**, 78 executed tasks, 1m23s. This is
  build/unit/lint evidence, not emulator/physical-device execution. Four emitted
  JUnit suites sum to **38 passed**, zero failures/errors/skips. The coordinator's
  `store-apk-audit.log` reports passed, only the application dynamic-receiver
  permission, both JNI ABIs, and all recorded ELF load alignments 16384.
- `store-frontend.log`: earlier normal bundle/schema/TypeScript and existing
  controller checks pass. It predates the final D06 UI merge; it does not replace
  the coordinator's planned final native/frontend compatibility checks.

The native compatibility agent subsequently ran clean 66e9b3b's existing
`node trace-harness.mjs`, `node inspector-harness.mjs`,
`node durable-harness.mjs` and `node export-harness.mjs`, reporting respectively
74/12, 93/14, 33/11 and 36/14 passing assertions/application-owned captures, all
with actual process restart. This reviewer read its verifier source
`m07-native-compat-temp/verify_schema_compat.py` and emitted
`m07-native-compat-artifacts/compatibility-verification-66e9b3b.json` in the same
ignored D task root: 110 supplemental checks, exact source identities, bounded
expected errors and schema-2 native storage/export evidence. The verifier checks
raw workspace DB2/contract1 and the full rendered DOM label in every nondisposed
durable/export workspace capture, not a mocked workspace object. Directly read
`durable-native-275f0f28-5519-4a58-b34d-05a4a29d5746/restart/durable-resumed.json`
also contains native `database_schema_version: 2`, `schema_version: 1` and DOM
text `SQLite schema 2 | Workspace contract 1 | Domain contract domain-v1`.
The agent reports visual inspection of native application-owned PNGs; the saved
workspace details were collapsed there, so the label check is DOM evidence.
This reviewer did not inspect images or run the verifier/harness. The agent's
packet explicitly says native v1 migration was not exercised, model generation
was false and desktop control was false. This qualifies fresh native DB2/restart
compatibility, not a native end-to-end historical-v1 migration or memory UI.

No test, native IPC/render, APK/device or model execution was done by this reviewer.
Exact commands, environment/tool versions, final native/frontend journey artifacts
and any further results remain the executing coordinator's evidence. The reviewer
read source and Git diffs and checked that 001/canonical tables/contracts/Cargo
were unchanged; no favorable source review is a substitute for those checks.

Final reviewed checkout SHA-256 (checkout line endings may differ from root's
artifact manifest; exact frozen Git commits above identify source):

| File | SHA-256 |
|---|---|
| crates/locallore-storage/src/lib.rs | 17a3b3d6402244de97ed1ad6eff8854a116454752e80e47a5ef6e08988dfc5f9 |
| crates/locallore-storage/migrations/002_derived_memory.sql | bfecd8c0a765993d463b53d6099c4d80453eef85e8c227ceb00e5ae011843f91 |
| crates/locallore-workspace/src/lib.rs | 20aa429c6c1013a42c6b9fe18d6eea4791bfcd0bb66449cd76c5d993056a5abc |
| crates/locallore/src/host.rs | ae8677b684af21f6a15ad1e5daed6b07dea6d9f6c805895d3bd8a123c4d0c802 |
| apps/desktop/src-tauri/src/export_commands.rs | c7d93a653fba2cc3757e50e12dbabeaeaa724fa3cb34f5d043f551be30ffb2de |
| apps/desktop/src-tauri/src/exports.rs | 70e2a214b7981131ab158d346906e069925f938eae2e0cbf42a1de09a4c1acf3 |

Next: coordinator reconcile the separate prototype review and final compatibility
artifacts, publish the focused Store/migration PR, and retain full M07 as unchecked.
No independent approval of the prototype, fabricated human approval or milestone
acceptance is implied by this report.
