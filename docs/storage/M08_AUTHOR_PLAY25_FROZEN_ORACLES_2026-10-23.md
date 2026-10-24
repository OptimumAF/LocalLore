# Author → Play2.5 → Store frozen integration oracles — 2026-10-23

Refs #12 M08.03/.06 and #8 M04.04. Status: **source frozen, UNCOMPILED /
UNRUN**, not a passed gate or demonstrated RED. Root owns all production,
existing tests and actual qualification. Agent resource_metrics_review owns
ONLY NEW `crates/locallore-storage/tests/m08_author_play25.rs` and this new
document in separate `test/m08-author-play25` / `source-author-play25-oracles`,
from `3db86dda2e462698539cee4d085e8fecc51204d5`. Claims #12 6377999000,
#8 6377999167. No existing production/test/DDL/fixture/dependency edit.

Frozen test commit `20a5f83de83e04794c7c1f79e32c17a6ed41f3f8`, three tests,
477 lines; SHA256
`0b174a0badea73639f880ba58675b077f67385b5b3a38b1a44bdf7c616c38f73`.
Unlike the earlier stage source freeze, these public Store/Core APIs exist at
the bound source. Their actual compilation/behavior has not been checked by
this packet. First execution may expose a real integration or fixture defect;
preserve it before a narrow, attributed fix. No prediction is a test result.

## Actual API path, not another persistence implementation

Fixtures use ONLY public Store/Core methods: create_story, typed preview and
Store begin_turn/commit_prepared, fork_branch, prepare_author_correction and
apply_author_correction, resume, actual `play::execute` with a synthetic
Script implementing InferenceProvider, begin_turn/commit_prepared, lookup_turn,
lookup_author_correction and cancel_turn. There is no SQL connection/writer,
handmade Receipt/accepted event, metadata import, host grant or database stub.

The provider returns bounded synthetic command/narration JSON through the
actual production Play2.5 role/controller path; two actual poll calls are
asserted. It is not an LLM or semantic-quality evaluator. Preparation mutates
only an Engine clone; Store's real shared commit revalidates it independently.
No source/head/scope is relabeled or copied into a different story to fake
isolation. Fake profile identity and original synthetic strings are explicit.

## Three frozen families

1. **Real author fork + generated discovery + durable reopen.** A real retained
   parent gift at revision1 and separate real sibling/parent-future utterances
   establish nontrivial lineage. Store prepares/applies author correction at
   f1/H2 into a fixed child: inherited gift1, private author2, then current
   generated discovery3. Before generation player/Mira retain observed A;
   actual Director/narrator work yields a genuine Core candidate discovering B.
   A durable Draft exists before the synthetic provider, and canonical Store
   state remains unchanged until commit_prepared. The committed Receipt is
   byte-identical to the actual prepared candidate. Full canonical records,
   accepted-history basis, completed boundaries and original inherited scope
   match the candidate. Player sees B, Mira stays A; no parent-future/sibling/
   author-reason/private-truth-source canary enters actor views. Parent and
   sibling canonical histories remain exact. After actual Store close/reopen,
   full records/basis/values/ordinary exact-key lookup remain identical;
   author lookup reports the current child head3. Exact begin/commit retry and
   Core recorded retry are idempotent; the latter spends zero roles despite
   invalid current profile and cancelled token. A late cancel_turn returns
   Committed with the real receipt, never false rollback. Changed request at
   the same key returns RetryMismatch.
2. **Cancelled draft.** A genuine current2.5 prepared Wait is produced on a
   clone, then the actual persisted draft is cancelled. Store commit_prepared
   returns Terminal, not acceptance, and canonical author-only history stays
   exact. After close/reopen the same key is Cancelled/no receipt, head1,
   with both player/NPC still observing A. No fake cancellation callback or
   forged prepared value is used.
3. **Same scope/head/mechanics, different canonical author source.** Two real
   independent stores share the same seed/child/request identity and mechanical
   projection but have actual B versus C author truth and distinct complete
   accepted bases. A genuine B-generated discovery candidate is supplied to C's
   real persisted draft. Bound commit must return Stale and preserve C/cursor/
   draft. Then unbound commit must revalidate the same actual candidate against
   C: its guarded `golden` prose was grounded only in B, while actual C's new
   observation is plain. Expected existing error is Engine(Narration), with no
   canonical mutation and draft unchanged. This tests both the authoritative
   source fence and actual current prepared-value validation, not merely an
   arbitrary receipt rejection. The original B Store remains uncommitted.

Every expected revision/record count follows real accepted events: private
author intervals count toward canonical heads while ordinary Receipt cache
does not define them. Main history has three canonical records and two ordinary
receipts; later views use actual Core actorV2 eligible discovery bindings.
Generation is never treated as a durable commit.

## Explicit limits

This qualifies the shared public Store/Core boundary **only after actual tests
run**. It does not exercise Host/native IPC, desktop/Android UI/decoder, an
actual local model, hidden-state semantic completeness, transport, cache/
memory performance, archive3, power loss, concurrent writer scheduling, Busy,
Full or process kill. Existing separately attributed evidence for those paths
is not rerun or inherited as this packet's result.

Public Store commit_prepared has no cancellation callback; the tested late
cancel is an actual cancel_turn after successful commit. The precommit case is
actual persisted draft cancellation, not a claimed midtransaction power race.
The cross-source unbound guard tests exact finite `golden` grounding; it does
not prove arbitrary false prose can always be recognized. Metadata remains
closed provenance rather than proof/authentication of historical prompts.
No original curated fixtures, expected outcomes, budgets or historical goldens
are altered. Any discovered failure remains a gate, not an excuse to weaken
the oracle or broaden source authority.

Each run creates private synthetic SQLite files under an owned uniquely named
TEMP child. Cleanup verifies the resolved parent and fixed family prefix and
deletes only that test-owned directory after Store values drop. No generated
DB/history artifact is tracked or uploaded; source generator/oracles only.

## Actual checks and next command

Own checks: standalone rustfmt/parser, test count/source SHA, `git diff --check`,
owned-path and final clean-tree inspection. Git2.33.0.windows.2,
PowerShell7.6.5, rustfmt1.8.0-stable (01f6ddf758 2026-02-11). No Cargo/typecheck,
SQLite open/provider execution, Node/Gradle/model/app/native/device/ADB/CUA/
desktop/transport/download/settings/protected-resource/PR/merge action and no
heavy slot taken.

Proposed first command for Root on its actual combined source, NOT yet run:

```text
cargo test --locked --offline -p locallore-storage --test m08_author_play25 --jobs 1
```

Use the allocated own D target/TEMP, debug0/incremental0, ordinary SQLite flags,
one process/jobs1. Record source, first compile/behavior failure and exact counts
before fixes. Then broaden only for actual changes/unresolved concerns. Root
owns integration, actual test execution and production fixes; claims release
after this frozen handoff. No milestone/human-acceptance/model-quality claim.
