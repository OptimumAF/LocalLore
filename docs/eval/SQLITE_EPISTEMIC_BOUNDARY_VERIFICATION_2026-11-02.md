# SQLite epistemic boundary regressions -- 2026-11-02

Refs #14 (M10.01/M10.02 supporting host coverage). These two deterministic
integration tests exercise the actual Rust Store and bundled SQLite, without an
inference provider. They add coverage; no production defect or behavior change
is claimed. Full milestone acceptance remains pending.

## Coverage

`m10_durable_epistemic_rollback` composes speech, attributed belief, travel,
discovery, elapsed time, return travel and the last-potion gift in one valid
turn. A persisted draft is followed by an actual held-reader SQLite busy error
under the existing DELETE journal. A separate writer probe demonstrates that a
RESERVED write lock can be acquired while that reader is held. The Store's
IMMEDIATE transaction and staged writes therefore reach the final commit lock
boundary, as supported by the source ordering; there is no new SQLite trace or
production fault hook. Final-commit location is inferred for this small fixture
and default cache behavior, not traced or asserted for arbitrary cache-spill
configurations. Compare the complete normalized application rows,
canonical history, projection and character contexts after rollback. The same
Store must remain usable for reads after the error; the successful write retry
occurs after reopening, and exact retries spend once.
Durable cancellation has a separate terminal turn ID; changing payload under
an existing persisted ID is not an engine-only key-reuse operation.

`m10_durable_observation_chain` persists A, privately corrects to B, records the
player's observation of B, and privately corrects to distinct C. It closes and
reopens the Store between boundaries. The reopened Engine supplies the actual
public Query2 API: player retains observed B, Mira retains seeded A, and only
an explicitly granted omniscient query can read canonical C. Same-head parent
and sibling futures, completed historical revisions, search, counts, pagination
and cursor identity must preserve scope and observer boundaries. Querying and
read-only reopening cannot mutate canonical history.

Existing tests already cover simple inventory faults, actual cancellation races,
SQLite exhaustion and durable A -> B -> A observations. The new cases exercise the
composed final-commit rollback and persisted Query2 boundary combinations, rather
than claiming those broader areas were previously untested.

## Reproduce in a normal checkout

Use the pinned Rust 1.93.1 toolchain and already cached locked dependencies:

```powershell
cargo +1.93.1 test --locked --offline -p locallore-storage --test m10_durable_epistemic_rollback --test m10_durable_observation_chain
cargo +1.93.1 test --locked --offline -p locallore-storage --test durable_turns --test durable_branches --test m08_author_store --test m08_author_store_review --test m08_author_play25
cargo +1.93.1 test --locked --offline -p locallore-storage --lib turns::
```

The first command is the intended repository command after checkout of this PR.
Actual execution in this packet uses an isolated test-only Cargo package, as
explained below; it is not reported as execution of that first repository command.
New test databases are synthetic, uniquely named under the process temporary
directory and retained for inspection. Set TEMP/TMP/TMPDIR to a physical D: test
output directory on this Windows host.

## Actual source and execution

The operator checkout stayed frozen at
`8924278ce1c877e6d67c90c15a35fb23ca7198dc`. Its 188 tracked core/storage/Cargo/
fixture inputs match main `d3862614cb6654305d88d44901eda36b83f2a4e8` by Git blob
and actual file bytes. Independent workers used separate existing read-only D:
worktrees and disjoint proposal outputs; the coordinator alone integrated.

An external package `locallore-b96-storage-proof` contains exact candidate test
bytes and the same relative fixture layout, and depends on the unchanged real
`locallore` (host feature) and `locallore-storage` paths. Its direct SQLite
inspection dependency remains the existing pinned rusqlite 0.40.2 with bundled
and backup features, with no new dependency version or production API.
Publication uses an alternate Git index against main; the frozen checkout HEAD,
working files and normal index remain unchanged. This is an isolated test package,
not a newly created managed worktree or full workspace graph equivalence.

Actual checks (exit 0; distinct tests, repeats not additive):

| Check | Result |
|---|---|
| New actual Store/SQLite tests in the isolated package | 2 passed, 0 failed/ignored |
| Existing durable branches / turns | 12 + 6 passed |
| Existing author play / Store / Store review | 3 + 13 + 3 passed |
| Existing `--lib turns::` checkpoint/pressure/race tests | 11 passed, 18 filtered, 0 ignored |
| Strict Clippy for the isolated package, `--locked --offline --all-targets -- -D warnings` | Passed |
| `cargo +1.93.1 fmt -- --check` in the isolated package | Passed |

Total: **50 distinct tests pass** (2 new + 48 existing). Both new cases passed
on their first execution; there is no manufactured RED or production fix claim.
After the first green run, the coordinator strengthened the Query2 case with
positive own-branch parent/sibling History controls; both new cases passed again.
The original independent proposal, formatting changes and all executions remain
retained. A proposed SQL quote-helper correction stopped on an equality assertion:
the actual source already used correct doubled SQL quotes. No source changed in
that attempt; the later repeated pass is not an extra distinct test or bug fix.

Actual new-test invocation, from the isolated package:

```powershell
cargo +1.93.1 test --locked --offline --test m10_durable_epistemic_rollback --test m10_durable_observation_chain
```

The other two repository commands above were actually run from the frozen
physical D: checkout. Its selected test and production inputs match main. No full
workspace, Android or repository-form new-test invocation is claimed. The isolated
lock has 42 packages: 39 registry package version/source/checksum triples match
the public 415-package Cargo.lock, plus real core/storage paths and the test-only
root. This is a tested subset closure, not identity of the entire workspace graph.
The Windows physical D: rule is verified in the local runner before tools start;
it is not hardcoded into the portable public test.

Final test source SHA256:

- `m10_durable_epistemic_rollback.rs`: `9f5cc91b407587f2f1a313d89e92df82f02384f4c3c9c7f30899f4a6a14b6e5b` (11899 bytes).
- `m10_durable_observation_chain.rs`: `6678b8f2fed761b64d54b18d35031aeaa8b19053cda0ca2bfc6a12587b656603` (14922 bytes).


## Evidence and limits

Exact commands, terminal logs, source hashes, candidate proposals and retained
synthetic databases stay under the private D: experiment directory
`2026-11-02-sqlite-boundary-review-v1`, with verified recovery copies. Build output
reuses the retained B95 target, with at most 1 GiB additional output; controls and
synthetic databases each have 32 MiB budgets and recovery has 128 MiB. No original
failure is reclassified by a later pass. Only synthetic source/test descriptions
are published; no private stories, credentials, models or raw device diagnostics.

Host SQLite locks and graceful reopening do not qualify Android/JNI lifecycle,
OS process death, physical power loss, real-model behavior, sustained performance,
ARM64 execution or release readiness. No emulator, phone, model, shared ledger,
system settings, other-emulator lifecycle, deletion or merge action occurs here.
The pending exact retirement proposal remains unapproved; a later fresh guest
requires its own applicable approval and admission.
