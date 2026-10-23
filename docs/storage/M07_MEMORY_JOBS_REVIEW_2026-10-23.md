# Memory jobs/schema4 independent review, 2026-10-23

Refs #11 (M07.03/.04), #29 (D07 prerequisites), partial. Reviewer
`/root/desktop_runtime_profile`, isolated `review/m07-memory-jobs` /
`source-memory-jobs-review`. Claims
[#11 6373335331](https://github.com/OptimumAF/LocalLore/issues/11#issuecomment-6373335331),
[#29 6373335701](https://github.com/OptimumAF/LocalLore/issues/29#issuecomment-6373335701).
Root owns production, migrations, fixes and integration. Reviewer changes only
NEW `tests/memory_jobs_review.rs` and this report; the separate lifecycle-test
author owns `memory_jobs_integration.rs`. This is not acceptance of full M07/D07.

Initial production freeze: `e98ff6a0f98bb8b561db8da1b26b2f9d7a99417c`.
Reviewed the complete memory-jobs module,004 migration and Store opening/schema
verification, retention/deletion/archive delta, existing Core coverage builder/
verifier, and relevant accepted snapshot/branch APIs. The reviewer authored
earlier extractive-memory prototype work, not this coordinator-authored job,
migration or runtime-handle implementation; this review does not self-approve
the earlier prototype. AGENTS, current #11/#29 claims and workflow were read.

## Concrete findings and frozen regressions

### 1. Cross-Store and expired native capabilities

At `e98ff6a`, `MemoryJobHandle` held only database-local row ID, scope and
observer. `read_job` used those fields without Store-instance binding. Two valid
independent databases can have identical accepted source/partition and allocate
job ID1. A handle from Store A then read, cancelled or pruned Store B's job;
a prepared step could publish to B when its source/generation matched. An old
native handle also remained accepted after closing/reopening a Store.

This is a derived-job lifecycle authority defect, not a demonstrated canonical
state write. Identical source data or copied databases do not establish native
owner authority. Five actual-API tests were frozen before the fix in
`20dc9bcf47bca541cffb7c87c6f7b18cf836b0ad`, with no forged opaque token or SQL
canonical fixture writes. All five independently failed on the exact original
production: status accepted a foreign owner, cancel changed B, terminal prune
deleted B, foreign prepared work published B, and reopen accepted the old owner.

Root fix `502cacd18b9c43c3719b42ab37bd642b4ff363c6` gives each Store a private
`Arc<()>` identity, copies it only into internally issued handles, validates
`Arc::ptr_eq` before every public handle-based path's database access, and uses
manual identity-aware handle equality. A retained handle keeps the old allocation
alive; a reopened Store receives a new owner and `ensure_memory_job` reissues a
handle to the same persisted row/progress. No persisted lease/schema identity or
deserialization authority is added. Source reviewed; original five tests pass
unchanged after this fix. A foreign-prepare guard is source-checked as well; the
five cases separately execute foreign status/cancel/prune/publication and reopen.

### 2. Valid historical schema3 retired catalog becomes unreadable

The original schema4 change unconditionally added `memory_job_packets` and
`memory_jobs` queries to the retained-ancestor graph validation. A supported
read-only schema3 database has no such tables. With an actual retired parent and
retained child, catalog validation returns `Integrity` despite valid replay.

Unique regression `de62d7b510988286f419740a832cc44115367ea0` creates the history
and retirement through real Store fork/delete APIs. Only schema4 derived tables
and the migration ledger are replaced with their exact historical schema3 form;
canonical tables and actual retirement records remain intact. The original
source opens/verifies schema3, replays the same child canon, and leaves database
bytes unchanged, then fails the catalog assertion. This was independently run
as an actual one-case RED, not inferred from an unavailable old database.

Root fix `368043756f9a9b0841c21845f56575a16a95d30a` reads the actual schema
version and skips only the two new job-table checks before version4. Existing
retired-prefix/projection checks remain; schema4 still checks job emptiness.
The same historical regression now passes without migration or byte changes.

### 3. Inconsistent job metadata can advertise false completion

At the original freeze and after the first two fixes, `read_job` checks positive
generation and cursor upper bound but not status/cursor/error semantics.
Changing only a derived row to `status='complete'` with cursor0/basis1 is admitted
by the original004 constraints. `memory_job_status` and same-basis
`ensure_memory_job` can report Complete despite no covered packet; the cursor0/
empty-prefix shortcut succeeds. The strict canonical context verifier does not
convert that false label into accepted canon, but durable progress is inaccurate.

The seventh test was added in `a0d4a3383d6f2c22331703683bcc8cb3e927554b` and
refined **before execution** in
`0b6baf9409282753c5451b67e68c0261cf6ba142` at the coordinator's request. It uses
only an own derived-row writer, deliberately bypassing CHECK constraints to
exercise read-time guards even after DDL tightening. Frozen oracle: status and
ensure return `Integrity`; actual context read returns
`RawFallback(Malformed)` with valid Engine canon; no silent job-row repair or
canonical mutation. The first six regressions remain unchanged.

The first attempt failed before semantic assertions: its foreign writer tried
to create a rollback journal beside a pinned staging Store whose sidecars deny
write sharing. This expected namespace protection returned SQLite
SystemIoFailure/extended778. It is a retained test-setup failure, not evidence of
the status defect. Setup-only commit
`4409c1982a5ed0f76a9c6eaab943659c56058fd1` closes staging, reopens the ordinary
active Store and reissues the handle before the same derived-row injection;
the oracle is unchanged. The second run then fails the actual status assertion:
Complete cursor0/basis1 is returned instead of Integrity. Canonical and job-row
nonmutation assertions execute before that failure. Semantic repair/final GREEN
are separate from that preserved RED.

Root semantic repair `74785fde83f05f6b12188d71eb008f366d381d4e` is source-reviewed:
new-schema CHECKs and read-time guards enforce Complete cursor==basis,
Ready cursor<basis, and Blocked/error consistency. Read guards also bound short
metadata/hash materialization and validate hash shape. `context_snapshot` still
loads strict canonical Engine first; only derived metadata Integrity becomes
`RawFallback(Malformed)`, without a row repair. Other canonical/storage errors
remain errors. This fixes the identified source path without making malformed
cache an authority or a canonical-context failure. The reviewer read the exact
diff but did not execute it; the coordinator owns the final unchanged seven-case
GREEN and broader Store/migration/retention/archive qualification. At this
report's freeze those final results are **PENDING**, not accepted or invented.

## Reviewed guarantees and limits beyond the findings

- Preparation reads actual scoped Engine/history, validates exact head/actor
  and existing prefix, then releases the read transaction before computing its
  bounded chunk. The opaque prepared value accepts no caller Engine/packet.
- Publication opens an IMMEDIATE transaction, re-reads exact job/basis/generation,
  reconstructs actual Engine, verifies prefix and recomputes the exact chunk.
  Packet insertion and cursor/status/generation CAS commit together; a final
  cancellation error rolls back both. No check after successful commit falsely
  claims rollback. Multiple preparations cannot resurrect an older generation.
- Job IDs use AUTOINCREMENT; native handles are reissued after reopen while row
  identity/cursor persists. Persisted cancellation never implicitly resumes;
  explicit prune/re-admission is distinct maintenance. No durable worker lease
  or model/provider job is invented.
- Context snapshot loads Engine and verifies derived packets from one SQLite
  read transaction, not separate mutable connections. Proof is rebuilt against
  actual accepted source and actor eligibility. Invalid packet content falls
  back rather than becoming accepted history. The proposed metadata-error
  fallback in finding3 preserves that same rule in source; canonical corruption still
  remains an error rather than a successful cache fallback.
- Packet reads cap allocation at33 rows of64KiB to detect a32-packet overflow;
  Core verifies whole-set source/interval/closure/provenance, not just an attacker-
  supplied hash. Retargeting drops an old open tail and retains only sealed
  chunks reverified against current Engine. Source basis excludes mutable ancestor
  heads while retaining immutable lineage and actual accepted receipts.
- Schema migration retains existing backup-before-upgrade/transactional identity
  verification. Jobs are derived-only additions. Retention/deletion remove packet
  rows before jobs and remove parent caches while preserving retained children;
  archive payloads omit job/packet state. Full migration/retention/archive matrix
  execution belongs to root and the separate lifecycle tests, not these seven
  regressions.

Core build/verify and Store replay/fingerprinting are deterministic bounded work,
not LLM summarization, a benchmark speedup, or a hard real-time cancellation
guarantee. Existing strict history reconstruction and source serialization can
still run between cancellation polls. No production prompt/model-consumption,
native UI, Android, full restart/offline/resource or model-quality acceptance is
claimed by this module/source review.

## Actual execution record

All compiler slots were explicitly coordinated with root. Own D-drive target
`memory-jobs-review-rust`, separate UUID TEMP/TMP under
`memory-jobs-review-artifacts`, debug0/incremental0, locked/offline, jobs1 and
test threads1. No root/global/shared target or unrelated resources were cleaned.

```powershell
$env:CARGO_PROFILE_DEV_DEBUG='0'
$env:CARGO_PROFILE_TEST_DEBUG='0'
$env:CARGO_INCREMENTAL='0'
$env:CARGO_TARGET_DIR='<task-root>/memory-jobs-review-rust'
$env:TEMP='<task-root>/memory-jobs-review-artifacts/temp-<fresh UUID>'
$env:TMP=$env:TEMP
cargo test --offline --locked -p locallore-storage --test memory_jobs_review --jobs 1 -- --test-threads=1
```

| Exact source / test selection | Actual result | Log SHA256 |
| --- | --- | --- |
| e98 +20dc; original five | 0 passed,5 failed,0 ignored; exit101; build27.20s/tests0.24s | `a50bb62137b1d9266496623f53cc997471c9ff2cdda9f70fbd752f1001ca9e77` |
| e98 +de62; filter `historical_schema3_retired_catalog_stays_readable_without_job_tables_or_writes` | 0 passed,1 failed,5 filtered; exit101; build0.79s/tests0.06s | `7cd7d1c1f5a53bf7621faf4a30cb34e148b1f4b6cfc2aaede11f5bd5c6288d3a` |
| e98 +502 +368, de62 tests unchanged; local source036eebf | 6 passed,0 failed/ignored; exit0; build3.89s/tests0.41s | `e2703de77794f5e4f6adf775082115b405f3aca215f36f2e525d10eba3662a7b` |
| same production +0b6; seventh only, original pinned setup | SETUP FAIL,0 passed,1 failed,6 filtered; exit101; not semantic RED | `900e6da38082fe581aca680a2d65db8a90b7edf29166d6f67ec78b4ba4ba2420` |
| same production +4409 setup fix; seventh only | actual status RED,0 passed,1 failed,6 filtered; exit101; build0.74s/tests0.04s | `31226a1a470c9307290762b708bdf52a563d3cf31d264d5745c29992612044a7` |

The six-case file SHA256 before/after both fixes is
`7ef35fa871533167bb9dfe3a56934f5ae58d0070a4e8cfb451de7b36bcb23ea4`.
No setup/compile failures preceded the first three reviewer runs. An initial local patch
application for the seventh-test refinement failed to match rustfmt text; it made
no changes and ran no tests, then was reapplied against actual text. This is not
semantic RED evidence. After the disclosed ordinary-Store setup correction,
the frozen seven-case file SHA256 is
`754be687c10d6e75ab823d69a17d4a0f962521bcef6f2d605e6459e315a8efa3`.
Its final combined GREEN after root's third production repair74785fd is pending
coordinator execution; no reviewer assertion or expected outcome was changed to
fit that repair. The only executed fixture adjustment is the disclosed switch
from pinned staging to an ordinary active Store before the injected update.

Four touched/new Rust files passed `rustfmt --edition 2021 --check` after the first
two fixes; Git diff checks PASS. Root's initial cargo check and interrupted broad
Store suite (old table-count assertion7 vs9) are coordinator evidence, not
reviewer test successes. No broad suite, extra Clippy, native app/model/worker,
device/ADB/CUA/desktop, protected resources, OS/settings, dependency downloads,
PR/merge or release actions by the reviewer. Broader new lifecycle tests remain
independently authored and are not duplicated or reattributed.

Final review disposition: three concrete original findings, preserved actual
RED evidence, two source repairs independently verified by six unchanged GREEN
tests, and a third repair source-reviewed with final seven-case GREEN pending
root. No further concrete blocker was found in the reviewed source boundaries;
this is not an approval score or full schema4/M07/D07 gate. Root subsequently
reported its initial new Store cohort24 unit passes/one old ignore,22 integration
passes/one invalid root-retirement fixture failure/one helper ignore and six
review-case passes. Those are preliminary coordinator results, not a complete
suite or independent verification; the test agent owns that fixture correction.

Handoff only the reviewer's NEW-test commits20dc9bc/de62d7b/a0d4a33/0b6baf9/
4409c19 and this report. Root already owns production fixes502cacd/3680437/74785fd;
local copies of the first two were used only for exact fixed-source checks. Do
not reimport them as new reviewer production edits. The compiler slot is released
and no reviewer heavy process remains. Next: root runs unchanged seven-case
regressions and full current-source compatibility, then separately integrates
the actual production compiler/Store/Host path and any platform evidence.
