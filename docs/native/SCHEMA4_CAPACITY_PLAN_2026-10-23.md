# Schema-4 capacity requalification plan — 2026-10-23

M04.04 / M07.03/.04 compatibility, supporting D08.07 and D09.03. Coordinator-delegated `app_storage_review`; claims #8 comment 6373465197 / #11 comment 6373465666 / #30 comment 6373466011 / #31 comment 6373466290. Separate `impl/m07-schema4-capacity` / `source-schema4-capacity` from frozen schema-4 source `502cacd18b9c43c3719b42ab37bd642b4ff363c6` (e98ff6a + fdddeef). This is not accepted-main qualification. Android compatibility b7310d1, the verified-Core compiler packet and historical schema-3 reports remain immutable.

## First frozen change: measurement admission only

`crates/locallore-workspace/examples/capacity_probe.rs` changes **only** its exact schema admission/stage label and report metadata from 3 to 4. No request, seed, prefix, key, gift, prepare/commit/retry/reopen assertion, ceiling, budget or production code changes. That is needed to observe the actual schema-4 fixture rather than stop at its intentionally strict old schema-3 guard. The coordinator approved this initial metadata-only change; all calibrated caps remain unchanged until measured review.

No build or SQLite measurement has run at this source freeze. A single uncapped Host measurement waits for the coordinator's resource clearance. No capped build, Android build or device operation is authorized by this plan alone. Further source/cap changes require coordinator approval of the measured proposal.

## Existing reference and preserved semantic boundary

Read actual `capacity_probe.rs`, `capacity_relief_probe.rs`, fixed Python padding reference/ownership/error logic, Android Gradle/manifests/properties/fixture/helper identity and Python tests. Historical schema-3 qualification is source-bound in `SCHEMA3_CAPACITY_HOST_2026-10-23.md` and `SCHEMA3_CAPACITY_VERIFICATION_2026-10-23.md`: actual seeded create/draft/Ready **17** pages; ordinary accepted gift **18** pages; lower16 failed at create. Full17 preserved the same 36-byte key and Ready state through repeated actual Full, unchanged canon and strict reopen. Relief32 measured fill14 of the fixed 3,500-byte zero payloads, attempt15 Full, drop14/free15, then exact same-key acceptance or terminal cancellation. Those reports, raw artifacts and prior accepted identities are not rewritten as schema-4 evidence.

The exact schema-3 reference digest is `c05ced1f0439fb767f97d2ff93a34ef44eb6fbc27da6814a75fad455fb0b2c17`. Its helper reference explicitly executes migrations 001–003, requires exact migration rows/application ID/user-version3/page4096/DELETE journal/no transaction, checks the selected owned root/marker/file identity read-only before writable open, and repeats guards around fixed writes. Only its exact padding table/owner/contiguous IDs/3,500-byte payload is mutable. Unexpected schema, marker drift, owner mismatch or uncertain helper/pipe state prohibits adoption and subsequent native dispatch.

These invariants and assertions remain fixed. So do prefix0, Lantern Quay, the original 36-byte request key, potion gift, no new submit/prepare after relief, cancellation, exact retry, strict reopen, maximum64 padding rows, payload3500, output bounds and time budgets. A measured schema overhead is not permission to alter gameplay or accept a different failure stage.

## Measurement phases and decision freeze

1. **Uncapped actual Host:** build the metadata-only example against this exact schema-4 source in an exclusive ordinary target, with no capacity compiler flag. Run once with `--prefix 0` in a fresh task-owned directory. Record initial/draft/Ready/gift byte/page counts, normal accepted gift, exact receipt retry and strict reopen. Let measured Ready be **P**, accepted gift **G**. Require page4096 and integral reported sizes. No anticipated numeric P/G is treated as measured.
2. **Closed-fixture schema inspection:** only after the example exits and owns no live connection, use a read-only SQLite URI to that one newly generated synthetic database. Query application ID, user version, page size, page count, freelist, exact migration rows and sorted `(type,name,tbl_name,sql)` user schema. Build an independent in-memory reference from fixed 001–004 migrations, compare full schema rows and migration rows, and compute the existing length-prefixed SHA-256 recipe. Report actual Python/SQLite versions and compare reference to actual bundled-SQLite output; do not assume cross-version SQL text identity. No writable open, raw copy/hash of a live DB, canonical SQL writes or user-selected database occurs.
3. **Review P/G before caps:** present exact source, raw logs and P/G/digest. The desired full profile is the **minimum measured Ready-fitting ceiling** with this same gift actually Full; propose cap P only if G>P and the fixed original stage semantics can hold. The coordinator must approve the finite adjacent tests. If no such gap exists, preserve the finding and stop; do not grow receipts or tune input until Full appears.
4. **Adjacent capped proof:** only after approval, separate fresh compile targets for original17 (retained failure), P−1, and P, without reusing ordinary SQLite artifacts. Preserve creation failures at too-low caps; at P require submit/Ready success, twice actual Full on the same key, unchanged snapshot, retained Ready, and strict reopen to the original queued key/revision0. P−1 must prove lower-bound refusal; it cannot substitute for the intended Ready→Full case. No cap is mutated in production or selected at runtime. The compile-time SQLite flag is scoped to that command's child environment/target only.
5. **Relief still32 initially:** keep the existing ceiling32 and payload3500. Measure actual fixed fill until SQLite Full (N successful rows, N+1 attempts) and exact drop/free count M; revalidate restored schema/migrations. No hard-coded N=14/M=15 assumption survives by relabeling. If the schema overhead leaves insufficient room for the original meaningful recovery proof, report that and seek a scoped decision; do not silently increase32, reduce payload, add prefix turns or change the fault workload. A deliberately broad calibration output is not final acceptance; freeze measured N/M with the coordinator, then restore explicit exact checks before qualification.
6. **Current profile freeze:** only after the coordinator accepts measured P/G/N/M/digest and adjacent outcomes, update the capacity-only Rust/Python/Kotlin/Gradle/manifest metadata and exact tests consistently. Proposed new v4 package/cache/build/root identities prevent overwriting/adopting historical v3 outputs; fixture/report shape versions remain unchanged unless an actual shape change is separately approved. Legacy cache paths should remain explicitly refused. No device installation is part of this task.
7. **Final actual proofs:** rerun fixed full and relief accept/cancel with exact frozen values, then all five original helper faults and two ownership-policy tests, relevant Python guards/manifest audits and strict Rust checks. Helper faults must retain actual fill, known terminal/reaped children, expected cleanup category, and **zero** post-failure Host calls/workspace opens. Unknown ownership still forbids even another helper/native probe. Local Android build/JVM/lint/both-ABI/APK checks await explicit resource permission and full source reconciliation. Device/Compose/physical ENOSPC/power-loss gates stay unrun and separately attributed.

## Proposed commands — not executed here

Create exclusive D-drive `$capacityOutput` and TEMP/TMP. Set dev/test debug0 and incremental0 in the tool process. Do not alter persistent/global environment flags, reuse protected resources or reuse a normal target with a capped SQLite library.

```powershell
# Metadata-only uncapped measurement, after resource go:
# This command's environment must have no LIBSQLITE3_FLAGS.
cargo run -p locallore-workspace --example capacity_probe --locked --offline --jobs 1 --target-dir "$capacityOutput/uncapped-target" -- --directory "$capacityOutput/uncapped-prefix0" --prefix 0

# AFTER measured proposal/adjacent-caps approval, each in its own process env:
# LIBSQLITE3_FLAGS=-DSQLITE_MAX_PAGE_COUNT=17      -> cap17-target
# LIBSQLITE3_FLAGS=-DSQLITE_MAX_PAGE_COUNT=<P-1>   -> lower-target
# LIBSQLITE3_FLAGS=-DSQLITE_MAX_PAGE_COUNT=<P>     -> ready-target
cargo run -p locallore-workspace --example capacity_probe --locked --offline --jobs 1 --target-dir "$capacityOutput/ready-target" -- --directory "$capacityOutput/ready-prefix0" --prefix 0 --expect-full

# Only after helper reference/count source is separately frozen and approved:
# LIBSQLITE3_FLAGS=-DSQLITE_MAX_PAGE_COUNT=32
cargo run -p locallore-workspace --example capacity_relief_probe --locked --offline --jobs 1 --target-dir "$capacityOutput/relief32-target" -- --directory "$capacityOutput/relief-accept" --python "$python"
# Repeat in another fresh directory with --cancel; fixed five --helper-fault
# selectors remain malformed/overflow/timeout/after-fill/cleanup-refusal.
```

Fixed closed-file inspection queries are `PRAGMA application_id`, `user_version`, `page_size`, `page_count`, `freelist_count`, `journal_mode`, `SELECT version,contract FROM schema_migrations ORDER BY version`, and the same sorted user-schema query used by the existing helper. These are one-off task-owned read-only measurements, not a new general script/SQL/file capability in the application. No arbitrary scenario/data source, production hook or schema owner change is proposed.

## Ownership and unrun gates

Exact capacity path claim is on the four linked issues: only the two workspace examples, fixed capacity/helper scripts and five corresponding script-test files, capacity properties, capacity-only Gradle regions and opt-in manifests/fixtures/helpers, plus new `docs/native/SCHEMA4_CAPACITY*`. All other production/schema/jobs/Host/main Android files belong to their existing owners. Ask before adding another path. No old dated report/JSON will be edited, moved or renamed as current evidence.

Actually completed at initial freeze: source/spec/claims review, scoped diff and whitespace checks. All caps, helpers, package identities and historical evidence remain unchanged. **No measurement/test/build/device result is claimed yet.** Next action is one explicitly cleared uncapped build/run, then a measured proposal and coordinator decision before any calibrated cap/count/digest mutation.
