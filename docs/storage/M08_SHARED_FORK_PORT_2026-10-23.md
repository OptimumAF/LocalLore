# Shared native fork port — 2026-10-23

Refs #12 **M08.01/.02**, prerequisite for #30 **D08.04**, partial, in review.
Claims [#12 comment6372796615](https://github.com/OptimumAF/LocalLore/issues/12#issuecomment-6372796615)
and [#30 comment6372797094](https://github.com/OptimumAF/LocalLore/issues/30#issuecomment-6372797094).
Coordinator-delegated author `/root/resource_metrics_review`, isolated
`impl/m08-shared-fork-port` / `source-shared-fork`, accepted base
`b2c03d4151dc6d257f2dbddbb64b13950ddbf41e` (accepted timeline PR #106).
Only production changes are `crates/locallore/src/host.rs` and
`crates/locallore-workspace/src/lib.rs`. New tests and this report are additive.
No Store, schema/migration, compiler, Play, archive, dependency, fixture, desktop,
JNI or Android changes. Root owns independent review, application wiring and
integration; no full M08/D08 acceptance or PR/merge by this author.

## Implemented native interface

`locallore::host::WorkspaceForkRequest` has `parent: Scope`, a fixed native
`child_branch: String`, `expected_parent_revision: u64`, and `at_revision: u64`.
The request is not deserializable and is not a `HostCommand`. JSON/model/player
text cannot grant this operation or author privileges.

`WorkspaceForkOutcome` contains `version: 1`, `scope`, `parent`, `fork_revision`,
`head_revision` and `created`. It is serializable for a future bounded native
adapter, not a new command accepted by Host JSON. `Persistence::fork_branch`
defaults to `Unsupported`; the shared SQLite Repository maps each field directly
to existing `Store::fork_branch`/`ForkRequest` and its actual committed outcome.
There is no new persistence format or branch identity algorithm.

`Host::fork_branch(&self, session, &request, cancel)`:

- Fails closed with `Internal` on a poisoned owner lock, `Closed` for a missing/
  closed session and `Scope` if that selected session is not the exact parent.
- Rejects `Busy` when any session in this Host has an active queued/running/ready
  gameplay turn on that parent Scope. An unrelated scope's work does not block
  it. Admission and publication serialize with this synchronous operation under
  the existing Host owner lock. It belongs on a native I/O worker, not a UI thread.
- Returns `Unsupported` without durable persistence. It never substitutes an
  in-memory fork or confers Story Lab, knowledge or author authority.
- Delegates boundary, branch/ancestry/retention/capacity validation, transactional
  cancellation and immutable identity retry to Store. It does **not** resume/read
  the parent or compare expected head before Store resolves an existing child.
- Leaves every selected session/Engine/turn unchanged; it does not attach/select
  the child, replace the parent or replay downstream choices. A caller may later
  explicitly resume the returned scope through the existing validated API.

The fixed child ID binds `(story, child ID, parent branch, fork point)`, not full
request byte equality. The expected parent revision is a new-creation guard only.
Existing matching child retries return its **current** head, including after the
parent or child advances and when the original expected parent head is stale.
Changing the immutable parent or fork point remains `RetryMismatch` (invalid
self-child identity remains `Rule`). Native callers must retain the same child
ID across an unknown acknowledgment; a fresh ID could intentionally create a
second branch and is not recovery of the first request.

The cancellation predicate is passed through unchanged to Store. Store checks
before commit and rolls back an interrupted transaction. After Store returns a
committed outcome, Host does not perform another cancel check and falsely report
rollback. A cancellation callback must be a short, non-reentrant signal; calling
back into Host while its owner lock is held is unsupported. Window/activity epoch
fencing and acknowledgment presentation belong to future caller adapters. Host
cannot establish that a particular window is still selected. Session IDs are
process-local and may be reused after restart; they are not a durable operation
identity. Fixed child identity and caller epoch fencing serve different purposes.

## Actual test scope

New `crates/locallore-workspace/tests/fork_host.rs` runs seven tests against actual
durable Host/Repository/Store using ordinary accepted typed commands, actual
prepare/commit and strict Store replay. No SQL fixture writes, forged receipt,
alternate authority, UI, worker process or real model is used.

1. A two-event accepted turn forks at completed head2. Parent canonical bytes and
   live session count are unchanged by creation. Parent and sibling then advance
   independently; child has only the actual inherited receipt plus its own local
   receipt, preserving original parent event/receipt Scopes. Mira sees the shared
   prefix and child observation, not later parent/sibling text; absent Sable does
   not see the prefix. These observations use the actual Engine actor context.
   The ordinary Host still rejects character/omniscient inspection and reports
   `author=false`; the test does not enable Story Lab to obtain a pass.
2. Pre-cancel creates no child. Cancellation at Store's third poll (after new
   child insertion at this frozen source) rolls back the transaction and leaves
   one root branch. Retry of the same fixed child then succeeds.
3. Stale expected head on new creation, a mid-turn fork at revision1 of a two-event
   receipt, and immutable child/fork mismatch retain authoritative Store errors.
   No partial/invalid branch remains in the actual catalog.
4. Discard a real committed outcome, explicitly close/drop Host, reopen and resume
   the parent. Advance parent2→3 and child2→4; retry the original fixed request
   returns `created=false`, current child head4. A changed creation-only expected
   guard999 still resolves the same child. Parent/child canonical bytes, two
   receipts and branch count are unchanged. A different parent for the same
   existing child produces actual `RetryMismatch`.
5. Actual queued and ready parent turns reject fork as `Busy`; another story can
   fork independently. After actual cancellation settles the turn, the original
   fixed request succeeds.
6. An actual FreeText Host worker enters a narrowly held synthetic provider poll.
   Channel barriers establish in-flight state without sleep-based overlap. Fork
   returns `Busy`; release makes that provider return `Provider`, the turn settles
   failed with no commit, and the fork succeeds. This is synthetic lifecycle
   execution, not inference quality or native application execution.
7. Missing/closed session, wrong live selected scope, injected JSON `fork_branch`
   and ephemeral Host all refuse appropriately; JSON creates no child.

New `crates/locallore/src/host/fork_port_tests.rs` adds two narrower Host unit
tests. A deliberately minimal native Persistence test double returns a committed
retry outcome while flipping cancellation; Host returns that outcome, never
pre-reads parent head or changes the cached Engine. This is a boundary test,
**not** a second SQLite cancellation execution. A deliberately poisoned owner
lock returns `Internal` before that port is dispatched. SQLite rollback and
unknown-ack durability are exercised separately by the actual integration tests.

## Source and retained failure evidence

Production source and initial tests: `08c5107d72de242d9c37d541396cf4c523703583`.
Final test correction: `490972aa6153335644470214aa0fbea4b6a5196d`; production
source did not change. The initial focused build failed with E0277 because a new
test helper attempted to deserialize an opaque `Receipt`. No tests executed in
that attempt. The corrected helper compares returned wire JSON with actual
Store-replayed receipt values, without adding deserialization or weakening canon.
Source review also corrected the initial test's proposed non-Lab character query:
it now asserts Host `Forbidden` and uses the actual Engine context for isolation.
That would-be query failure was observed in source review, not represented as an
executed RED. Original commit and compile log remain retained.

Initial compile log SHA-256:
`82770bbe4d5b02ca049a01a9922b4ca73ec96ea56b32318b96aa58a09810de52`.
Local logs/target/TEMP live under the task's D-root
`fork-port-run-e6c6bf40-27ef-4442-8e8d-5cc030aeff29`, outside Git. Databases are
synthetic under that task TEMP and removed by test cleanup. No private database,
raw local diagnostics or machine-specific path is committed.

## Reproducible checks

Environment actually queried: Windows NT10.0.26300.0 x64; cargo1.93.1
`083ac5135 2025-12-15`, rustc1.93.1 `01f6ddf75 2026-02-11`. Existing locked
dependencies only. Initial build log has no Updating/Downloading/Downloaded
entries; subsequent checks explicitly use offline mode. Use a fresh own target
and UUID TEMP/TMP under a private task directory, with
`CARGO_PROFILE_DEV_DEBUG=0`, `CARGO_PROFILE_TEST_DEBUG=0`, `CARGO_INCREMENTAL=0`.
Run sequentially with `--jobs 1` and test threads1; do not run heavy native builds
concurrently with these checks.

```powershell
cargo test --offline --locked -p locallore-workspace --test fork_host --jobs 1 -- --test-threads=1
cargo test --offline --locked -p locallore --no-default-features --jobs 1 -- --test-threads=1
cargo test --offline --locked -p locallore -p locallore-workspace --jobs 1 -- --test-threads=1
cargo test --offline --locked -p locallore -p locallore-workspace --all-features --jobs 1 -- --test-threads=1
cargo clippy --offline --locked -p locallore -p locallore-workspace --all-targets --jobs 1 -- -D warnings
cargo clippy --offline --locked -p locallore -p locallore-workspace --all-targets --all-features --jobs 1 -- -D warnings
rustfmt --edition 2021 --check crates/locallore/src/host.rs crates/locallore/src/host/fork_port_tests.rs crates/locallore-workspace/src/lib.rs crates/locallore-workspace/tests/fork_host.rs
git diff --check
```

### Final results at source490972a

| Check | Actual result | Local log SHA-256 |
| --- | --- | --- |
| Focused actual durable fork tests | 7 passed, 0 failed/ignored; exit0 | `be9697d57c5addcba4c1119131d10863b4777e63b1fa141c1bf9a45e6373663f` |
| Portable Core, no default features | 158 passed, 0 failed/ignored; exit0 | `52a7f07b5ea6f795b17f7168186b6fb1145dab6c58bec2fe1a1c666c6823d0f3` |
| Scoped Core + workspace, default features | 250 passed, 0 failed/ignored; exit0 | `90b3b45985eeb82d414e7359ab9c6cd6d68ec62bb4f550194f5b7de7fc799a35` |
| Same scoped packages, all features | 250 passed, 0 failed/ignored; exit0 | `9572c1dac87301a59461099a7673e897776c6b2eedede83c9e6ec728596401fe` |
| Strict scoped Clippy, all targets/default | PASS, exit0 | `2b02b8e9f4d0ed73a8e763bc9ae58c8ede18e18bb24113cb962f8c22b5171917` |
| Strict scoped Clippy, all targets/all features | PASS, exit0 | `152401eb23769371722bd6aa1d0f44dbfa868769bfd3b4424241f64d4239d362` |
| Four touched/new Rust files format check + Git diff check | PASS, explicit exit0 each | `466cb443669f4f2f7dedcba3bfcf32e17cafbc153be037a8da03c314bc17ccbb` |

Both 250-test runs include the two new Host unit tests and seven actual fork
integration cases. Counts are per command/feature mode, not additive unique
coverage. Portable Core excludes the host-gated port; it checks that adding the
native seam does not impose Host/schema dependencies on the portable build.
Default scoped workspace already enables Host through its existing dependency;
all-features is an explicit repeated compatibility gate, not a different model.
No runtime inference/native app process starts in any command above. Test fixtures
retain their original language/budgets/expected outcomes.

At handoff, locally fetched accepted `origin/main` had advanced to
`e534f01e107a48642370fa0a976fa25c747baba9` (PR #107 long-history tests/docs only).
Read-only diff confirmed no change from b2c03d4 to that ref in either owned
production file. Tests remain bound to this worktree's b2c03d4+08c5107+490972a
source, not falsely attributed to the newer main. Coordinator will reconcile
current accepted main during independent integration.

## Remaining application gates

No desktop/JNI command, UI control, window/activity epoch fence or platform test
was added/executed. No model/assets/worker/device/ADB/CUA/desktop control,
protected-chat/resource, OS/settings, dependency download or release operation
occurred. Portable tests are shared Rust execution on Windows, not physical phone
or Android ABI execution. No arbitrary author corrections, draft regeneration,
rewind UI, automatic downstream replay or new knowledge privilege is implemented.
Root next independently reviews/integrates this port and wires explicit native
fixed-ID fork/recovery callers with stale-window fencing and actual application
verification. Existing Store/archive/retention compatibility remains authoritative;
full M08/D08 exit gates remain unchecked.
