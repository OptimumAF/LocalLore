# Archive3 epistemic journey verification -- 2026-11-02

Refs #12 (M08.04/M08.06), #14 (M10.01/M10.02 supporting host coverage).
Two original deterministic integration tests exercise the actual public Rust
Store, Archive3 validation/import and Core Query2/replay. No provider runs.
These add acceptance evidence, with no demonstrated production defect or behavior
change. Full milestone tasks and platform qualification remain open.

## Journey and authority oracles

`m08_archive_epistemic_journey` starts with A, privately corrects to B, observes B
and gives the last potion in one accepted turn, then privately corrects to C.
Parent and sibling futures deliberately share the selected branch's numeric
head6. Export/validate/import into another database with an unrelated control
story, then actual Store reopen, must preserve all four branch histories and
native accepted-history bases. Exact Query2 pages include row origins, scoped
sources, counts, historical boundary metadata and cursor bytes, across Player,
explicitly granted Mira and granted Omniscient queries. Completed revisions2/4/5
and invalid in-turn revision3 are exercised. Ungranted inspection is forbidden.
Positive own-branch parent/sibling statement controls accompany selected-branch
search exclusion; privacy is not inferred from universally empty results.

The imported original gift retry returns its recorded receipt without another
transfer. Re-export is byte-identical before new play. Only an explicit new
imported-branch discovery at7 makes C player-known: historic6 stays observedB,
Mira's entitled history stays scoped, and old-head/cursor identities cannot be
silently reused at the new head. Actual target reopen preserves the continuation
and foreign story; every original source branch and its archive remain unchanged.

`m08_archive_observation_authority` creates TWO genuine Store histories. Each has
both existing source-a and source-b author corrections with identical B and
sequence1. The same observer branch ID, turn ID and discovery sequence2 yield
identical complete receipts, with different genuine private PlayV2 observation
bindings because their eligible parent sources differ. A later private C keeps
selected projections equal while accepted histories remain distinct. Both full
original archives really validate and import successfully.

A whole genuine donor wrapper is grafted into the other archive. Both source
records exist and their values agree; this is stronger than changing a field to
an unknown sibling ID. Seed, payload and branch-record checksums are recomputed
and asserted. Canonical-state checksums remain authentic original checksums;
no claim is made that an impossible history has a computed valid state hash.
Direct public Core continuation accepts the original wrapper and rejects the
graft with `Error::CorruptHistory`, before any archive state-hash comparison.
Archive validation then returns `ArchiveError::Integrity` before producing an
import capability. Every application row/column of an existing destination,
including its unrelated story and pending draft, remains unchanged. This is
pre-write admission refusal, not an exercised mid-write rollback.

Checksums establish internal integrity, not authenticity of the original author.
Internally coherent alternate histories remain valid inputs; these tests do not
invent signatures, original-author authentication or a new trust boundary.

## Existing coverage and why these cases matter

`m08_archive3` already tests broad A/B/A round trips, native bases, contexts,
original retries, retained branches and target continuation. The existing hostile
suite already mutates actors, discovery IDs and seed/sibling/future sources with
recomputed structural hashes. The new journey joins actual transfer to exact
Query2 pages/cursors/grants and independent knowledge progression; the new
adversary transplants a genuinely generated complete wrapper between two valid
same-value histories with existing competing sources and an independent Core
replay oracle. Neither generic archive implementation nor Query2 itself is new.

## Actual execution

Pinned Rust1.93.1, Windows x86_64-pc-windows-msvc, existing rusqlite0.40.2 with
bundled SQLite/backup. No dependency version or production API/schema changed.
The operator checkout remained frozen at
`8924278ce1c877e6d67c90c15a35fb23ca7198dc` with its normal index unchanged.
197 declared tracked core/storage/Cargo/fixture inputs match public main
`d3862614cb6654305d88d44901eda36b83f2a4e8` by actual bytes and Git blobs.
Independent review identified three legacy Android archive assets consumed by
the selected old tests outside that set. Their separate supplement binds and
backs up another24,695bytes by literal path, Git blob and SHA256: windows-origin,
windows-continued and parent-retention-v1. Thus200 declared source/fixture files
are preserved; this is not an assertion of the entire workspace input closure.

The frozen checkout is an operator source for a separately gated run. Independent
authors/reviewers used different existing read-only D: worktrees with disjoint
proposal ownership; the coordinator integrated exact candidate tests into an
external test-only Cargo package, `locallore-b97-archive-proof`. It depends on
the actual unchanged core (host feature) and storage paths, with the existing
pinned SQLite/serde_json/sha2 versions. Its42-package lock has39 registry package
version/source/checksum triples matching the public415-package lock, plus real
core/storage path packages and the test-only root. This verifies the used subset,
not equality of the full workspace graph or execution on Android.

Actual isolated-package command:

```powershell
cargo +1.93.1 test --locked --offline --test m08_archive_epistemic_journey --test m08_archive_observation_authority -- --test-threads=1
cargo +1.93.1 clippy --locked --offline --all-targets -- -D warnings
cargo +1.93.1 fmt -- --check
```

Actual existing-test command from the physical D: frozen checkout:

```powershell
cargo +1.93.1 test --locked --offline -p locallore-storage --test playable_archive --test m08_archive3 --test m08_archive3_hostile --test branch_retention_archive -- --test-threads=1
```

| Check | Actual result |
|---|---|
| Two new tests in isolated package | 2 passed, 0 failed/ignored |
| Existing retained-branch archive | 11 passed |
| Existing Archive3 | 7 passed |
| Existing hostile Archive3 | 6 passed |
| Existing playable archive | 13 passed |
| Strict isolated-package Clippy | Passed |
| Isolated-package formatting check | Passed |

**39 distinct tests pass** (2 new +37 existing). Both new cases passed on first
execution; no failed implementation, manufactured RED or production fix is
claimed. Repeating the journey alongside the newly added adversary is not an
extra distinct test. Original proposals and the positive-control refinement
remain preserved. A later explicit assertion confirms Mira still knows A after
the imported player discovers C; both tests and final checks pass again. No full
workspace or Android check was executed in this packet.

In a normal checkout of this PR the intended reproduction command is:

```powershell
cargo +1.93.1 test --locked --offline -p locallore-storage --test m08_archive_epistemic_journey --test m08_archive_observation_authority -- --test-threads=1
```

That repository-form new-test command was not executed in the frozen operator
checkout; the exact candidates were executed in the isolated package instead.

Final candidate SHA256:

- `m08_archive_epistemic_journey.rs`: `1a23f251c5615fcb1ecd0142ea3262273bde3e716471c95cb2ffac2af719cd63` (16763 bytes).
- `m08_archive_observation_authority.rs`: `c60eeeb12e354443179ed42cc154bb8b8532ebc2cf291a382040747ea4661924` (15038 bytes).

## Preservation and limits

Project commands, output, temporary settings and caches are physical D:. Local
runner checks resolve D: paths before launching project tools; no global settings
change is made. New uniquely named synthetic databases and three authority
archives are retained rather than deleted. Existing tests keep their normal
owned fixture cleanup. Exact logs, sources, proposals and recoveries stay in the
private `2026-11-02-archive-epistemic-journey-v1` output/recovery directories.
Builds reuse the retained target, allowing at most512MiB above its1,406,959,302-byte
baseline. Controls and synthetic outputs each have32MiB budgets; recovery128MiB.
No private stories, model weights, credentials or raw device diagnostics are
published. Publication uses a separate Git index/branch and leaves the operator
checkout HEAD, normal index and working files frozen.

These are host semantic-transfer and validation checks. They do not qualify
Android UI/JNI lifecycle, process death, physical power loss, real inference,
model quality, ARM64, sustained device performance or release readiness. No
new guest, phone/model operation, shared-ledger write, image deletion, settings
change, other-emulator stop or merge occurs. The exact retirement proposal stays
pending, and a future fresh guest needs separate applicable approval/admission.
