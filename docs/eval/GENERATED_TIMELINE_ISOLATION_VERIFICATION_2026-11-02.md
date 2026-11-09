# Generated shared-store timeline isolation

B102, 2026-11-02. Refs #14 (M10.01; supporting M10.02). Implemented and
locally verified for review; full tasks remain unchecked. No production,
schema, dependency, feature, provider, Kotlin or canonical-contract change.

## Gap and executable slice

The existing 10,000-attempt trajectory uses one Engine. Its conservation and
replay assertions remain valid; the existing durable generated sequence uses
96 attempts. Neither is generated interleaving across several story/branch
lanes sharing one SQLite owner. This packet adds one original integration test
and a synthetic Reed Bell fixture through the real Store/Core APIs.

Each scenario creates two stories in one SQLite file. Actor, item, fact, branch
and turn identifiers deliberately collide across scopes. Sel and the unwitnessing
Watcher also share a display name. Each story has five initial lanes:

| Lane | Canonical domain | Initial player observation |
|---|---|---|
| Root | Domain1 | Original seed value A |
| Corrected | Domain2 | B, discovered after private correction |
| Pre-correction fork | Domain1 | A; author record excluded |
| Before-observation fork | Domain2 | A; truth B remains private |
| After-observation fork | Domain2 | B, with original corrected-scope discovery source |

Sel retains A and its seed source throughout; the distant Watcher has neither
the fact nor the private dialogue. A claim of ownership/teleportation changes
neither world truth, beliefs nor the player's abilities. Potion ownership,
unspent coins, story time, claim count and exact observation/source expectations
are independent assertions, not a second copy of the engine reducer.

There are **32 deterministic seeds x320 attempts =10,240 attempted operations**.
Seed i is wrapping-u64 `0x4c4f524520261102 + i*0x9e3779b97f4a7c15`, i0..31.
The source fixes the generator and schedule. Each ten-attempt round visits all
ten lanes in seeded shuffled order and reuses the same round turn key across
them. First rounds guarantee an accepted wait and an atomic rejected batch per
lane; subsequent operation choices are seeded. Setup/correction/fork/bootstrap
operations are excluded from attempted-operation totals.

| Attempt category | Actual count |
|---|---:|
| Wait | 1,196 |
| Give tonic | 857 |
| Consume tonic | 836 |
| Discover | 889 |
| Claim/dialogue | 863 |
| Wait followed by missing ability | 1,217 |
| Foreign-scope proposal for current request | 847 |
| Future expected head | 916 |
| Exact original request retry | 858 |
| Changed intent under same scoped key | 885 |
| Begin, cancel, refuse commit | 876 |

The deliberately invalid batch tests rollback after an earlier valid command.
The request stays in the selected lane while the proposal carries another
existing story's same-named branch. Rejections require exact Ability, Inventory,
Knowledge or Scope errors; Narration cannot stand in for a mechanical refusal.
Stale and changed-key checks use their exact status categories. Exact retries
return the original receipt before the stale-head guard and cannot change canon.

Cancellation is real Store begin/cancel/terminal commit refusal. Its Cancelled
turn row persists separately from unchanged canonical projection/history; raw
SQLite file bytes are not treated as an invariant. Per-lane fingerprints include
scope, domain, head, projection and canonical records. Each selected lane is
checked before work; all lanes are checked after every round and Store reopen.

Every 64 attempts closes/reopens the Store, with a final reopen after cutoff
checks: **192 same-process Store close/reopens** across the cohort. Historical
cutoff forks at the original author boundary match the stored pre-observation
projection. Generated-head forks additionally preserve the exact canonical
record sequence and observation sources. These add128 cutoff branches to320
initial lanes.

## Actual checks

Base `027ddbaf298cd05ebdcdf65d716962e783bcad31`; tested code tree
`40dd668c31e075948acfd59a5df9f7b09b03d3d8`. All2,577 existing source files stay
byte-identical. The tested tree adds only the fixture and test (2,579 files).
This report is the only later source addition in the PR.

| Actual phase | Result |
|---|---|
| New generated integration target | 1 method passes;32 scenarios/10,240 trace lines |
| Five existing Store targets | 41 methods pass |
| Four existing Core targets | 48 methods pass, including the existing singleton10k trajectory |
| Strict storage all-target Clippy | Pass with `-D warnings` |
| Workspace formatting check | Pass, empty stdout/stderr |

**90 declared methods pass:1 new +89 existing;0 failed/ignored/filtered.** The
10,240 operations are not10,240 tests or independent seeds. Actual aggregate
outcomes are2,903 accepted,5,603 rejected,858 exact retries and876 cancellations.
Their sum matches all32 per-trial summaries and retained per-attempt traces.
All32 read-only SQLite quick_checks pass, each with2 stories/14 final branches:
64 story instances,448 final branch instances. This is actual SQLite on Windows,
not a mocked storage port or parallel copies of an in-memory engine.

Reproduction from the physical D: repository root, with process-local D: temp,
artifact and cache/target locations, installed pinned Rust1.93.1 and the existing
locked offline cache:

```text
cargo +1.93.1 test -p locallore-storage --test generated_timeline_isolation --locked --offline -- --nocapture --test-threads=1
cargo +1.93.1 test -p locallore-storage --test durable_turns --test durable_branches --test m08_author_store --test m08_author_store_review --test m08_archive3 --locked --offline -- --nocapture --test-threads=1
cargo +1.93.1 test -p locallore --test contracts --test branch_restore --test m08_author_core --test m08_author_review --locked --offline -- --nocapture --test-threads=1
cargo +1.93.1 clippy -p locallore-storage --all-targets --locked --offline -- -D warnings
cargo +1.93.1 fmt --all -- --check
```

The four actual build/test/Clippy requests use absolute installed Cargo/Rustc
paths equivalent to the commands above, two jobs, no incremental/debug info,
and a stdin barrier before admission to the frozen checked WindowsJob owner.
All four jobs have known closure, unchanged selected tool pins and identical
before/after2,579-file source maps and exact source ZIPs. Formatting is a separate
read-only check, not a claimed build job. New-test command173.051s includes
compilation; the test itself160.81s. These are verification durations, not model
or device performance. No runtime/model/native dependency was introduced.

## Original review finding and retained evidence

Independent source review found a false-pass risk before execution: a permissive
`Engine(_)` error assertion with deliberately wrong narration could let Narration
mask an incorrectly accepted mechanical operation. The original unexecuted
proposal/preflight remain retained. Exact rule-category checks replaced that
assertion before the first run. This is an oracle correction, not a production
defect, unchanged-main RED, failed executed test or weakened acceptance criterion.
The executed test and fixture then stayed unchanged through every phase:

| Input | Bytes | SHA256 |
|---|---:|---|
| generated_timeline_isolation.rs | 22,067 | e36d4d837fddb583335685c688033a540dd18d9a741f1dc1d7798b96bf00a908 |
| generated_timeline_isolation_v1.json | 1,480 | 4a81d6de6443efa0e3e67bdca738f2d02ff99e2f773019d77d41372738301d7d |

The existing author-cancellation regression intentionally catches a synthetic
panic; its stderr remains retained and does not represent a failed test. No
new runtime failure/counterexample occurred, so no failing seed is minimized.
One reviewer was unavailable at model capacity; another completed independent
design, source and closed-evidence reviews, retained as separate audit records.
Model review does not constitute owner acceptance.

Private output/recovery basename `2026-11-02-generated-timeline-isolation-v1`.
Original source, pre-execution proposals, requests, ZIPs/maps, raw outputs,
all32 synthetic databases/traces and summaries remain retained. Declared bounds:
source128MiB, controls128MiB, synthetic256MiB, generated3GiB, selected recovery512MiB.
Final build output373,787,616B and synthetic21,468,259B pass their sampled bounds.
Build output remains in place and is not represented as a copied recovery payload;
sampling is not an OS quota/continuous peak proof. Shared AVD limits are unchanged.

## Remaining scope

This is finite generated operations/interleaving on a fixed FantasyV1 topology,
with additional cutoff forks at generated heads. It does not generate arbitrary
fork trees, all profiles, all possible states, concurrent writers or storage
pressure. Actor context/observation calls use trusted explicit actor selection;
no Query2 grant/cursor/paging coverage is claimed. Replay is actual Store reload
and cutoff reconstruction, not a separate `restore_continuation` cohort.
Same-process Store reopen is not OS process death, cold hardware or power loss.

No model/Host inference, Android/JNI/ARM64, full workspace/frontend/Python/JVM,
full CI, privacy/offline traffic, release or full milestone qualification follows.
No emulator/ADB/phone/model, settings, shared-ledger/image operation, deletion,
private upload or merge occurred. Operator checkout/index and existing worktrees
stay preserved. Knowledge Android0/4, physical/model/M10.05 and installed diagnostic
privacy gates remain separately blocked on applicable capacity/authority/evidence.
