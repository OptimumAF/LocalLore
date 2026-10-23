# Independent durable-turn review

2026-10-22, M04.02/.03 bounded root-turn slice, with related M04.04/.05/.06
recovery checks. Implementation and this review depend on unmerged schema PR
[#38](https://github.com/OptimumAF/LocalLore/pull/38) at `75abe39` and ownership
fix [#35](https://github.com/OptimumAF/LocalLore/pull/35). This report does not
record owner acceptance or completion of the whole milestone.

The reviewer used a separate `review/m04-durable-turns` checkout based on
`f8f2f41`. Owned changes are the independent integration test file and this
report. Production fixes belong to the coordinator. The review claim is
[#8 comment 6355013627](https://github.com/OptimumAF/LocalLore/issues/8#issuecomment-6355013627).

## Demonstrated defects and corrections

1. Normalized event JSON accepted duplicate object keys through generic JSON
   value parsing. A prefix `"sequence":999` followed by the valid event encoding
   passed `resume`; complete receipt parsing already rejected ambiguous keys.
   Coordinator fix `a2f502d` compares the stored normalized event encoding with
   the exact canonical serialization written by this owner. Equivalent externally
   reformatted normalized payloads are also refused; this internal table is not
   an import format.
2. Draft enumeration trusted the embedded request's turn ID when selecting its
   matching row. Replacing the first draft's JSON with a second existing draft's
   request returned the second draft twice instead of rejecting the first row.
   The coordinator independently identified this issue; the reviewer reproduced
   it. Fix `a2f502d` checks the selected row's turn ID and revision directly.
3. A committed exact request returned its original receipt for changed short
   retry narration, but returned `TooLarge` for oversized unused retry narration.
   Fix `bb1e9f9` resolves the durable committed result before validating a new
   output. A fresh draft with oversized narration still fails without changing
   canon. This agrees with `Engine::commit` request-based idempotency.
4. An already-open store ignored an orphan witness at a nonexistent event
   sequence when another synthetic connection bypassed foreign keys. Reopening
   was protected by `Store::open`'s foreign-key check, and normal public writes
   cannot create the orphan, but live replay did not validate every scoped
   witness row. Fix `6873bc8` counts all scoped witness rows against the total
   validated receipt witnesses after the exact per-event checks.

The first corrected-fixture run on `f8f2f41` passed six of nine tests and failed
the three regressions in items 1–3. After applying those two coordinator fixes,
all nine passed. Adding the orphan-witness case then demonstrated item 4.

## Coverage and boundaries

The nine independent tests exercise canonical receipt/event/request/branch-head
tampering, added valid and orphan witnesses, duplicate normalized event keys,
direct draft-row identity, terminal cancellation/failure across reopen and all
retry APIs, exact committed retries, missing/stale/corrupt projection repair,
observer context equality, input/output rejection, the 4,096 total-intent cap,
and the 16 MiB combined stored-history byte cap. Corruption tests deliberately
disable foreign keys on their separate synthetic tampering connection; the
production owner always configures its own connection. Cache repair must refuse
corrupt canonical evidence without overwriting the old cache.

The tests use only the repository's original Lantern Quay fixture. Errors checked
here expose fixed `Integrity`/`TooLarge` categories, with no raw database text.
No user saves, model, network service, app control, desktop capture, ADB, or
physical device is used. Coordinator fault-stage/process-exit/disk-full tests
are separate evidence and are not counted as independent review executions.

Source inspection confirms that no public SQL connection or accepted-event
deserializer is exposed. `commit_turn` accepts a typed request/proposal and
narration; shared engine validation constructs receipts before their atomic
events/witnesses/projection/response/status/head write. `begin_turn` releases its
transaction before returning; inference belongs between separate calls, outside
the store's write transaction. Store calls are blocking and need an owning IO
worker when integrated into a UI.

`Engine::restore` is bounded deterministic v1 root-history validation: it
recomputes each typed outcome under current v1 rules, verifies the entire stored
receipt, and never calls an inference provider or random source. Future random
rules need an explicit recorded-outcome contract; a seed cannot justify rerolling.
Child-branch history, imports, rules migration, real-model narration, pruning of
bounded intent history, UI save/resume and physical power-loss guarantees remain
outside this review. Canonical bytes/equality detect inconsistencies; they are
not a cryptographic authenticity guarantee against coordinated valid edits to
all database authority records.

## Final verification

On Windows x86_64 with `rustc 1.93.1 (01f6ddf75 2026-02-11)`, the reviewer
cherry-picked coordinator fixes `a2f502d`, `bb1e9f9`, and `6873bc8` onto the
separate review checkout. Their local equivalents are `ff258c7`, `11cd55f`, and
`91dae78`. The production change was inspected; only the coordinator authored it.

Actually executed against final review source `91dae78`:

```powershell
cargo +1.93.1 test -p locallore-storage --test durability_review --locked --offline
cargo +1.93.1 clippy -p locallore-storage --test durability_review --locked --offline -- -D warnings
cargo +1.93.1 fmt --all -- --check
git diff --check
```

All commands exited 0. The integration suite passed **9 tests, 0 failed,
0 ignored**, including all **12 canonical-table tampering cases**. Clippy and
format checks passed without warnings or changes. Test commits `51fbb4f` and
`bfec3c2` carry the independent suite; their equivalent integrated commits can
differ after cherry-picking. This report-only handoff adds no production changes.

No unresolved concrete defect was identified within the reviewed bounded root
slice after these corrections. The review is finite evidence, not approval to
merge or a claim that all M04 acceptance criteria are complete. The coordinator
owns broader workspace/Android verification, PR evidence and downstream host/UI
integration. Independent review claim is released to coordinator integration.
