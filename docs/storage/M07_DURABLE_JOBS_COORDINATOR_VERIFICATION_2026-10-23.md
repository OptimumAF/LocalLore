# Schema4 durable jobs: coordinator integration, 2026-10-23

Refs #11 M07.03/.04 partial, #29 D07 prerequisite, #30/#31 platform
compatibility. This is a shared Store slice, not acceptance of production memory
consumption, the memory milestone or the desktop epic. The owner authorized
implementation and eligible merges; no settings, reviews or release authority
are manufactured. Protected chat/runtime resources were not touched.

## Source and contract

Coordinator branch `impl/m07-durable-jobs`, integration source
`5e44ea91bfa9e93ecf583e31a26937efdfa96366`, includes accepted main
`d989cf0b53ecf56223c2a9294ba260aae9f6a98a` (PR112).
The [protocol](M07_DURABLE_JOBS_2026-10-23.md),
[independent failures/review](M07_MEMORY_JOBS_REVIEW_2026-10-23.md),
[lifecycle test design/results](M07_JOB_TEST_DESIGN_2026-10-23.md), and
[capacity verification](../native/SCHEMA4_CAPACITY_VERIFICATION_2026-10-23.md)
retain their original source identities and execution attribution.

Migration004 SHA256 is
`d5b07c6b5ebb5e63a23c7171181662f2406be4c8f507b19ac94d408e840c9500`.
Schema4 adds only derived job/packet tables. Owner-bound native capabilities
expire across Store owners/reopen; persisted identity/cursor/cancellation do not.
Preparation releases its read transaction before Core construction. Publication
replays and rebuilds against a fresh exact basis/generation and commits packet
and cursor together. Context reads return actual Engine/proof from one read
snapshot, with whole-set conservative fallback for unusable cache and strict
failure for unusable canon. No packet, inspector permission or job grants a
character knowledge.

Canonical receipt bytes and workspace contract1 stay unchanged. Playable archive
formats1/2 retain their rules; format2 explicitly admits source schemas3/4 and
excludes jobs/cache. Database inspection reports actual schema4. Branch deletion
preview2 and story preview3 include exact new derived counts; Android's decoder
retains closed historical key sets and rejects missing/extra/negative/future or
overflow-inconsistent counts. Controller admission supports branch1/2 with the
existing scope/head/token/consent fences. Current durable Android startup requires
actual schema4 separately from workspace contract1.

## Actual coordinator execution

Windows11 Pro10.0.26300, Rust/Cargo1.93.1, bundled SQLite3.53.2.
Sequential Cargo processes use own D-drive targets/TEMP, jobs1, dev/test debug0,
incremental0 and locked/offline dependencies. Normal targets have no capacity
compile flags. Generated databases/logs remain local outside Git.

```powershell
cargo test -p locallore-storage --offline --locked --no-fail-fast -- --test-threads=1
cargo test -p locallore-storage --offline --locked --test derived_store --test branch_retention --test story_deletion -- --test-threads=1
cargo clippy -p locallore -p locallore-storage -p locallore-workspace -p locallore-android --all-targets --all-features --offline --locked -- -D warnings
```

| Source / execution | Actual result |
| --- | --- |
| `33e5d3e`, whole default Store |184 passed,1 failed,5 ignored; exit101. The sole failure is an old `before-v3` backup filename filter. All23 new job parent scenarios,7 independent regressions,7 migrations and the long-history baseline passed.|
| `71a6d74`, affected targets after correction/versioned previews |19 passed,0 failed/ignored (derived_store4, branch_retention7, story_deletion8); exit0. The corrected stale filter and current consent versions are exercised.|
| `71a6d74`, portable all-target/all-feature strict Clippy |PASS; exit0,30.34s. Capacity-specific follow-up has separate source/results below.|

This is not represented as one all-green whole-suite run. The five whole-suite
ignores are the explicit96-page archive qualifier, two child-only helpers
(their parent-owned interruption scenarios ran), and two Windows file-symlink
privilege cases. No OS privilege or settings change was made to remove them.
The new job cohort includes separate-owner contention, observer/branch/source
isolation, cancelled/obsolete preparation, bounded/blocked metadata, actual
SQLite Full rollback/reopened exact-boundary retry, and killed owned child
processes before/after persisted checkpoints. These are not power-loss,
physical-disk-ENOSPC or native-rendering tests.

Original cross-Store capability, historical schema3 catalog and false Complete
metadata regressions retain their actual RED evidence. Migration preflight
also retained filename/header comparison failures. The corrected backup oracle
allows only SQLite's three documented four-byte header fields to differ while
requiring every other byte, exact SQL rows, literal receipts and strict replay.
No production backup path was changed to satisfy that fixture.

Local logs under `memory-jobs-artifacts`:

| Log | SHA256 |
| --- | --- |
| storage-final-default.log |5aa8e0ad9a04fb4697b7b6e37d5ae7fb020b043d5e89b2f290d9ee65c4a77d96|

The later Android/frontend/native execution results will be recorded before PR
submission. No unexecuted check in this record is a PASS.

## Separate capacity qualification and remaining work

Schema3 physical profiles were not relabeled. The independently authored
[measurement](../native/SCHEMA4_CAPACITY_MEASUREMENT_2026-10-23.md) observed
Ready23 pages/accepted24 before freezing Full23 and relief32 profiles. Actual
relief measured8 owned padding rows, attempt9 Full and9 freed pages; the original
14/15 oracle failed before the new counts were frozen. Profile format3/schema4,
v4 package/cache namespaces and exact schema digest are distinct from unchanged
Host/helper wire2. The final packet runs actual Host accept/cancel/exact-retry
and five bounded helper faults; its own source/log hashes and59 Python checks
are attributed to the contributor, not a new coordinator rerun.

No scheduler, Host/Play verified consumer, new prompt/provenance version, model
comparison, Android device run, physical phone or release qualification follows
from this change. Next is the native same-snapshot Host port and production
Play integration using the already accepted Core verifier/compiler, followed by
the separately frozen comparison and remaining desktop gates.
