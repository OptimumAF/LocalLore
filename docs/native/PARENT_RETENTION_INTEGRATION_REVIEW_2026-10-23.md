# Retained-parent integration: independent review, 2026-10-23

Refs #85; #12 M08.05/support M08.01/.04/.06; #8 shared schema/recovery.
Reviewer: `/root/app_storage_review`. Reviewer claims: #85
[6370156017](https://github.com/OptimumAF/LocalLore/pull/85#issuecomment-6370156017),
#12 [6370156371](https://github.com/OptimumAF/LocalLore/issues/12#issuecomment-6370156371),
#8 [6370156720](https://github.com/OptimumAF/LocalLore/issues/8#issuecomment-6370156720).

## Scope and independence

Initial source was integration merge
`f8bb6353ceb7cc8ff0efde75bb47df4a0df9735c`: incoming #85 `a1b1cc9`
plus accepted main `59fa8e8`. Final reviewed production source is
`db1294ecccd56ae802d4afbea302faf3c42d06de`, including coordinator corrections
`8e613af` and `db1294e`. Review checkout: `source-d08-design`, final branch
`review/m08-retention-final`. Only the new review test and this report were
authored here. The coordinator owns every production correction.

This reviewer authored earlier fork/archive-v1/pinned-staging and branch-cache
primitives, but did not author incoming retained-parent/schema3/catalog-v2/
archive-v2 implementation or the coordinator's Host corrections. This is an
independent retention/integration review, not independent approval of those
earlier primitives. No score, human acceptance or full M08/D08 gate is inferred.

## Findings and disposition

1. **Capture owner liveness needed explicit retirement.** Incoming #85 removed
   sessions without retiring their private trace owners, and its targeted
   invalidation blocked on the trace mutex and failed on poisoned gameplay
   state. The coordinator's `311a707` regressions and `8e613af` correction now
   retire targeted owners before cancellation/removal, preserve live children,
   recover a poisoned state guard only for cleanup, retain poison, and use
   best-effort diagnostic cleanup after releasing state. Public `NotFound`
   admission also retires the removed owner. Source recheck and the focused
   Host tests below passed. This reviewer did not run the coordinator's
   original pre-fix liveness cohort and does not claim that execution.

2. **Demonstrated integration regression: revocation read SQLite.** Accepted
   D06 owner-only `trace_capture_revoke` called `get_session`; incoming #85
   added `Persistence::validate_scope` to that helper. A live owner's attempt
   to remove optional private copies consequently failed when canonical
   admission returned `Database`. The independent actual-Host regression in
   `f32b85a62d7818e6acf786cc77b5de0126f1ef73` first **FAILED** at its intended
   assertion with `{"error":"Database","status":"rejected","version":1}`.
   Wrong-scope rejection had already passed. No production source was changed
   by the reviewer. Coordinator `db1294e` resolves only revocation's session
   and exact scope in memory. The unchanged regression then **PASSED**, also
   checking zero additional admission calls and ordinary `Open` still
   rejecting `Database`. The existing private-revoke unit now additionally
   panics if `validate_scope` is called. Read/configure/gameplay admission was
   not waived.

No additional Store retention defect was demonstrated in this bounded review.
The remaining qualifications below are limits, not claims that all adversarial
inputs, platform behavior or milestone requirements have been proved.

## Store, archive and adapter review

- Retirement captures a coherent validated graph, rechecks its opaque consent
  against the same database/file observation and an IMMEDIATE transaction,
  computes retained completed prefixes, checks exact affected row counts,
  replays survivors, compares their canonical/receipt fingerprints, checks
  foreign keys, and commits once. Digests supplement actual replay; they do
  not replace it. Cancellation/error paths drop the transaction.
- Required parent birth floors and direct-child fork caps preserve original
  ancestor scopes, including nested rewinds before a parent's birth. Public
  retired targets fail admission before old request/receipt/cache access;
  private ancestry replay remains available only as a source for live children.
  Unreachable tail, all target noncommitted workflow and derived rows are
  removed. Recursive collection preserves reserved identities.
- Exact historical schema1/2 verification precedes migration. Migration uses
  the established consistent SQLite backup under writer exclusion, rather
  than copying a main file without WAL. The old schema/receipts remain in a
  nonoverwrite backup; DDL/version changes are transactional. Current pinned
  disposable-staging guards remain present after integration.
- Catalog v2 carries physical retired ancestors and validates them before
  consumers filter playable choices. The Android decoder checks the complete
  original graph before filtering; it does not silently reparent children.
- Archive v2 binds the sorted unique retired-ID set, requires source schema3,
  validates retained-prefix normal form and full Engine replay, preserves
  original local receipt scopes, and imports tombstones/history atomically.
  V1 rejects even a null retirement field. Checksums are consistency checks,
  not authentication: deliberate valid reauthoring and rehashing is outside
  the claimed faithful-unchanged-archive roundtrip guarantee.
- JNI branch deletion consumes a native owner/kind/generation-bound token.
  Deletion and session admission/commit share the workspace mutation gate;
  Store commit precedes targeted session invalidation before gate release.
  Provider preparation remains outside it. A post-commit cancellation can
  return uncertainty and the Android controller reconciles saved state. This
  was source review, not a new Android/device execution.

## Independent tests and exact execution

Environment: Windows NT `10.0.26300.0`; rustc
`1.93.1 (01f6ddf75 2026-02-11)`, Cargo
`1.93.1 (083ac5135 2025-12-15)`. All Cargo executions used `--locked --offline`,
`CARGO_PROFILE_DEV_DEBUG=0`, `CARGO_INCREMENTAL=0`, task-owned
`--target-dir <TASK>/retention-review-target`, and task-owned D-drive `TEMP/TMP`.
`<TASK>` is the coordinator's private task output directory. No model, app,
WebView, device, ADB, CUA, protected process or protected checkout was operated.

The three new sole-Store cases exercise:

1. A child and sibling's prepared cache tokens across parent retirement;
   retired-parent token publication refused; exact child inherited/local
   content retained; parent-future/sibling/other-observer canaries excluded
   before FTS; old child token refused after recursive collection; retired ID
   cannot be reused.
2. Corruption of a retained original witness ledger while valid cached data
   exists: cached read, search, catalog, archive export and deletion preview
   all fail closed. Restoring that exact witness makes the valid cached read
   succeed again.
3. A second Store owner commits on the child after consent: the old plan is
   stale although the selected parent's head has not advanced. Competing
   confirmation is stale after the first retirement; exact accepted child
   receipt retry remains exact both locally and after archive-v2 roundtrip.

The fourth feature-gated case is the actual-Host revocation regression above.
The initial test commit was imported unchanged by the coordinator as
`fc2693b`. A later assertion-only lint correction is
`d2f5e206fbc6c01ea2d9b75f2f200266c9696601`; revocation assertions are unchanged.

| Command, with common Cargo flags above | Source | Actual result |
| --- | --- | --- |
| `cargo test -p locallore-storage --test retention_integration_review` | initial f8bb + three tests | 3 pass after fixture correction below |
| `cargo test -p locallore-storage --test branch_retention --test branch_retention_archive --test schema3_migration` | f8bb production bytes | 7 + 9 + 6 = 22 pass |
| feature-enabled exact `private_revocation_does_not_depend_on_new_retired_scope_database_admission` | f8bb + frozen f32b85a | 1 genuine regression failure |
| default review test module | db1294e, unchanged f32 test blob | 3 pass |
| review module with `--features development-fixtures` | db1294e; repeated after d2f5e20 lint correction | 4 pass each |
| `cargo test -p locallore --features host --lib retires` | db1294e | 6 pass: same-story child, public admission, busy/poisoned branch/story/teardown and unload-owner lifetimes |
| exact `private_capture_revoke_is_owner_scoped_busy_honest_and_fences_late_artifacts` | db1294e | 1 pass; busy is not reported as erased |
| storage Clippy `--all-targets`, default and `--all-features`; core Clippy `--all-targets --features host`; all with `-- -D warnings` | db1294e + d2f5e20 | pass |
| `cargo fmt --all -- --check`; `git diff --check` | db1294e + d2f5e20 | pass |

Original failed attempts are retained under the private task output directory:

- `retention-review-first.log`: 2 pass/1 reviewer-fixture failure. Sable has
  zero eligible events; packet-v1 intentionally returns `NotFound`, not an
  empty packet. Corrected expectation; no production defect or fix attributed.
- `retention-review-revoke-before.log`: actual regression failure, SHA256
  `7b7a53ed75f3e74c3e721be6667cb8ee495014dc5814189ab8b14c45226146c2`.
- `retention-review-feature-after.log`: setup compile failure from attempting
  to cherry-pick `8e613af` without its preceding Host test commit. The attempt
  was aborted; no production conflict resolution/edit. The reviewer switched
  cleanly to exact `db1294e`, verified the review test Git blob against f32,
  then ran the final cohorts. The accompanying default run passed but is not
  treated as a qualification of that conflicted tree.
- `retention-review-clippy.log`: review-test `cloned_ref_to_slice_refs` lint;
  fixed only the cloned expected slice in d2f5e20. Final strict logs pass.

Final feature log SHA256:
`4379c0934c30538433fad26e5cf246c9cab08de9cdb5f7755bcebef6b369960b`.
Existing 22-case log SHA256:
`917797f4432fa10aa18f7b0ef84c960d60bff6adb81a6ec7073ab52544d608c3`.

## Reviewed source binding

Production files below are exact db1294e bytes. The test hash includes only
the d2f5e20 lint correction. No claim is made about later coordinator source.

| File | SHA256 |
| --- | --- |
| `crates/locallore-storage/src/branch_retention.rs` | `1aa00d83ef2f83ee8f369528d59413615f321a998702018ddafee437df7ac2e0` |
| `crates/locallore-storage/src/retention_state.rs` | `6e758fbdafc23db2103f61f202f29080f2e4dadd591a369582c6764e1e16edd5` |
| `crates/locallore-storage/migrations/003_branch_retention.sql` | `9dc663a316d0b4250a479596838f250a51b74c94a18ca396469da01cc618ec3d` |
| `crates/locallore-storage/src/lib.rs` | `8f1e09213f08459a65430a382ecc0911c8a87d4aeb7ce592863ed1d83eadc1ad` |
| `crates/locallore-storage/src/turns.rs` | `c29670920fbbf04e2b09571722f9ea311abeb4b7128bef9cd751db270b8d301e` |
| `crates/locallore-storage/src/branches.rs` | `ccc7578de646e4dd69757706680db3b7b600603b8ba949ec97ef0e7a8b5d74fb` |
| `crates/locallore-storage/src/playable_archive.rs` | `3ad4c955bcbf2a1e057b3b64d0951101dde8ca328ee42e13456f0ea4e1b7bbf0` |
| `crates/locallore-storage/src/branch_catalog.rs` | `ccc3369c1525b76b7fce2a7f80ad30a9568fcfe4529f08262a122b2f5fec9505` |
| `crates/locallore-storage/src/derived_memory.rs` | `72c73ddcc7f66e5883f537838737cbde8a98f7b9f4823fc8b07287714507ed37` |
| `crates/locallore/src/host.rs` | `f20d8c75ec997c932b8d33e38e63a5ac92fe70763d333641ea71daa51dd4953a` |
| `crates/locallore-workspace/src/lib.rs` | `2c47544c2dc6499437c4e389ea52290112951b16570191466d700460d428f83e` |
| `crates/locallore-android/src/archive.rs` | `e7e1584b97aacf50d952d33fc222e10a782bdd42eb4e7f7eed0df48f5234c537` |
| `crates/locallore-android/src/archive_jni.rs` | `e0cba7d91da163343e13af1b8f9a7d601dbb52d408bf993338325d322a2b49ad` |
| `crates/locallore-android/src/workspace.rs` | `2d199f6fcafe85792b55dfeaae843e86f9fc516fa44735088d2d6afcd614750c` |
| `crates/locallore-storage/tests/retention_integration_review.rs` | `a81da0dc2486da4e5bd03d9e50a32ba33ffb72bcc22db2f9770336c5bf339d64` |

## Remaining boundaries

The coordinator owns broad combined workspace, desktop-native/frontend and
Android build/JVM/ABI qualification. None is attributed to this reviewer.
Pending #87 then #94 must be reconciled and qualified in that order; their
historical evidence is not a fresh combined run. No protected-owner checkout,
device or process is needed for this source review.

Retirement is logical deletion, not forensic erasure. Required private
ancestry, backups and existing exports remain. Reserved/physical IDs share a
256-ID lifetime story bound; archive physical branches remain capped at32, so
not every maximally populated Store is exportable. Replay/graph cancellation
is cooperative between bounded operations, not a qualified hard CPU deadline.
Normal Store/backup paths retain their trusted app-private ancestor contract;
the Windows staging reservation is not a general same-user/OS sandbox.
No branch-creation/correction UI, production memory consumer, real model,
physical power-loss/ENOSPC, phone/ARM64 execution or release gate is closed.
