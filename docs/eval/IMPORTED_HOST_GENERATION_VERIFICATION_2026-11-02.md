# Imported Host generation verification -- 2026-11-02

Refs #9 (M05.01/M05.03), #12 (M08.06), #14 (M10.01/M10.02), supporting host
acceptance only. Two original cases share private helpers in one integration
test file. They exercise actual Host/Repository/Store and production Play with
explicitly synthetic scripted roles. No production behavior change or
demonstrated defect/fix is claimed; full task checkboxes remain open.

## Why this case

The existing `m08_archive3_play25` generates on the source before export, imports
the accepted receipt, then proves zero-provider-call retry. That is important,
but does not exercise a NEW generation snapshot from a cold imported Host.
Existing generation/cancellation suites also remain the generic coverage; this
packet joins those boundaries to imported corrected actor knowledge.

The fixture uses real public Store operations: seedA, private correctionB,
player discoveryB plus last-potion gift at3/4, then private correctionC at5.
Later parent/sibling canaries share numeric head5 but are outside the selected
lineage. Real Archive3 export/validation/import into a second database preserves
an unrelated target story. Both stores close before the target Host is opened.
Only a fresh explicit imported-side free-text request starts these new cases.

## Positive generation and commit

The actual production context compiler supplies the director with observedB;
unobservedC, private author reason and excluded parent/sibling canaries are
absent. Scripted director proposes Discover through the current constrained
schema. Engine validation supplies C to the narrator's approved candidate packet;
old A/B and private reason/future canaries are excluded from that packet.
The fake narrator returns exactly the approved C, not a new consequential fact.

Host preparation reaches Ready while complete canonical records, projection,
native accepted-history basis and all three actor contexts stay unchanged.
Only explicit commit publishes revision6. Player then knows C, Mira retains A,
Sable has no discovery, potion transfer remains4 and obligation remains1.
Actual saved receipt carries current Play2.5 policy/context metadata, no repair
or safe-narration fallback. Source branches/archive, nonselected imported
branches and unrelated target story remain unchanged.

A cold Host reopen configures a denying factory, then disables the provider.
Exact retry of THIS imported-side generated turn, plus prepare/commit/status/
cancel controls, returns the identical committed response without constructing
or polling another provider. This is not reuse of a source-generated turn.

## Cancellation and deliberately late output

The second fresh imported request runs prepare on an owned Rust thread. A
scripted narrator gate is entered only after the real director/engine validates
a DiscoverC candidate. The main test observes one logical Host worker and
cancels through the real Host command while the scripted poll is held. After
release, the deliberately noncooperative fake returns valid C even with its
cancellation token set. The integrated driver/Host/persistence path discards
that late output and returns the exact terminal Cancelled response/no receipt.

Executed assertions require one fake factory, two role polls, one Script drop,
the observed cancelled token, no extra poll, zero logical workers after joining,
and zero sessions/workers after close. Canon remains observedB/privateC,
Mira retains A, and the durable turn is Cancelled without a receipt. Hot controls,
cold retries with a denying factory, and retries without a provider stay
terminal without regeneration. Expected workflow draft/terminal rows may change;
accepted history does not. All fixture source/nonselected/control branches stay
conserved.

Entered/finished waits are5s, the fake in-poll release gate is bounded10s, and the
synthetic current production profile retains its5s deadline. RAII always releases
and joins the owned prepare thread on assertion paths. The test does not provide
a hard OS join bound. These counters measure one synthetic Script and logical
Rust Host slots; they do not establish native backend/GPU/OS-resource drainage.
The integrated outcome does not isolate which redundant cancellation guard
(driver versus durable Host reconciliation) independently caused rejection.

## Actual execution and reproduction

Rust1.93.1 / Windows x86_64-pc-windows-msvc; unchanged Core/Store/Workspace and
existing pinned dependencies. Actual operator checkout remained frozen at
`8924278ce1c877e6d67c90c15a35fb23ca7198dc`, clean with its normal index unchanged.
237 declared tracked source/Cargo/fixture files across those three crates match
main `d3862614cb6654305d88d44901eda36b83f2a4e8` by actual bytes and Git blobs,
with verified recovery copies. Selected old tests include only the already
bound lantern fixture; the new fixture is original inline synthetic data.
This declared set is not a claim of complete workspace-input closure.

Independent agents used different existing read-only D: worktrees with disjoint
proposal ownership. The coordinator integrated one test file in an external
test-only Cargo package `locallore-b98-import-generation-proof`, using actual
unchanged Core (host feature), Store and Workspace path dependencies. Its43
packages contain39 registry version/source/checksum triples matching the public
415-package lock plus those three path packages and the test-only root.
This is a subset check, not full workspace graph identity.

Actual isolated-package commands:

```powershell
cargo +1.93.1 test --locked --offline --test m08_imported_generation -- --test-threads=1
cargo +1.93.1 clippy --locked --offline --all-targets -- -D warnings
cargo +1.93.1 fmt -- --check
```

Actual existing-suite command from the physical frozen operator checkout:

```powershell
cargo +1.93.1 test --locked --offline -p locallore-workspace --test m08_archive3_play25 --test play_host --test generation_snapshot_host --test generation_play_consumer --test generation_consumer_review --test generation_snapshot_port_review --test literal_host_durable -- --test-threads=1
```

| Check | Actual result |
|---|---|
| New imported generation/cancellation | 2 passed, 0 failed/ignored |
| Existing generation consumer review | 6 passed |
| Existing production generation consumer | 6 passed |
| Existing native generation snapshot | 6 passed |
| Existing generation snapshot port review | 5 passed |
| Existing durable literal Host | 5 passed |
| Existing Archive3 Play2.5 | 1 passed |
| Existing Play Host | 3 passed |
| Strict isolated-package Clippy / formatting | Both passed |

**34 distinct tests pass** (2 new +32 existing). Both new cases passed first
execution; repeated positive execution alongside the cancellation case is not
additive. The first positive-only compile emitted unused helper warnings while
its cancellation fragment was pending. Integration removes unused Fixture.b
and abandoned PendingDirector code rather than suppressing warnings. Originals,
first-passing candidate and all logs remain retained. Shared preservation checks
were strengthened to all nonselected target branches; Sable's lack of discovery
is explicit. No production failure, manufactured RED or fix is claimed.

Intended reproduction in a normal checkout of this PR:

```powershell
cargo +1.93.1 test --locked --offline -p locallore-workspace --test m08_imported_generation -- --test-threads=1
```

That repository-form new-test command was not run in the frozen operator; exact
candidate bytes ran in the isolated package instead. No full workspace,
Android, real-model, physical-device or narrative-quality result is implied.

Final test source:

- `m08_imported_generation.rs`: `42305c60b8b3ee0275f896bc96351ae809cefe495950eaf813eaf380a3d94e41` (27572 bytes).

## Preservation and remaining gates

All project commands/output/temp/cache are physical D: with process-local
settings and local path checks. Synthetic databases, source/target histories,
actual accepted metadata, proposals and closed logs remain under the private
`2026-11-02-host-import-generation-v1` output/recovery directories. No raw private
stories, credentials, model weights or device diagnostics are published.
Build output reuses the retained target with a512MiB increment limit above
1,543,236,311bytes. Controls and synthetic outputs each have32MiB budgets;
recovery128MiB. New-case fixtures and packet evidence are retained; selected
existing tests keep their original fixture cleanup behavior. No manual/shared-data
cleanup is performed. Alternate-index publication leaves the
operator HEAD, working files and normal index intact.

Host/fake-provider checks do not qualify Android UI/JNI lifecycle, real inference,
physical model performance, ARM64, power loss, native runtime drainage or release
readiness. No guest, phone/model operation, shared-ledger write, image deletion,
settings change, other-emulator stop or merge occurs. Pending exact retirement
and a separate approved fresh guest/admission still gate Knowledge Android0/4.
