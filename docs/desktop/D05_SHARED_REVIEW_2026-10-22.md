# D05 shared inspection source review — 2026-10-22

Refs #26 D05.01/.03/.04/.06/.07, partial shared prerequisite. Review claim
[6357369374](https://github.com/OptimumAF/LocalLore/issues/26#issuecomment-6357369374).
Reviewer: `/root/desktop_runtime_profile`; coordinator retains production ownership.

Reviewed integration commit `f7968d226f62b27f98203a316b1c5a217a1ac74d`
(query module integration `c8f65e6`) in `LocalLore-d05-integration`, including
`inspection_query.rs`, Host dispatch/capture, generated request schema/types,
15 module tests and 2 Host/SQLite tests. The reviewer's only changed path is this
report, in separate branch `impl/d04-local-worker`, `LocalLore-d04-profile`.

This is source analysis, not execution. No test, build, model, native UI, device,
desktop control, storage mutation or generation was run. The coordinator's packet
reports 17 focused tests and strict Clippy passing; those are not reviewer results.
No D05 acceptance or approval is claimed. Native UI, summaries, indexes and branch
history remain outside this reviewed implementation.

## Finding 1 — P1: event witnesses receive private player display records

At the reviewed commit, `inspection_query.rs:700–740` attaches both original
FreeText/Dialogue input and recorded narration whenever the lens can see every
accepted event in a receipt. Witnessing an outcome does not establish that an NPC
heard the player's action prompt or the prose displayed to the player. A single
witnessed Give therefore exposes an entire private action prompt in that NPC's
History. Narration has the same authority mismatch: it is a player display record,
not a diegetic statement that every outcome witness heard.

The row enters the eligible collection before serialized search/count/page, so
the otherwise correctly ordered search pipeline amplifies this eligibility bug:
searching a private canary can return the original prompt and a positive count.
This does not mutate `character_context` or current generation inputs; it violates
the NPC-scoped inspection boundary independently of such writes.

Concrete regression vector, using existing synthetic fixtures:

1. Adapt `historical_v2_replay_preserves_original_input_without_an_inference_provider`
   (`tests/inspection_query.rs:608`): retain its synthetic profile/record, typed Give
   proposal and recorded replay, but use Action input `Give my potion to Mira.
   PRIVATE-PLAN-731: I secretly intend to visit dry-well later.`
2. Commit only Give(potion, mira, 1). Both player and Mira witness this one event;
   the private clause is absent from the accepted effect and any Say event.
3. Query History with trusted `Character { id: "mira" }`, current expected head,
   first empty search and then `PRIVATE-PLAN-731`, with limits 1 and 64. The
   reviewed code returns an `original_input` Message containing the canary and
   a matching count of 1. Expected: no NPC Message for the player's input or
   narration; the witnessed Give Event remains available, and canary search has
   zero rows/count/cursor.
4. Preserve original input and narration for Player/Omniscient history and
   historical completed-turn replay. A literal Say event should still expose its
   actual spoken words to witnesses. Add an analogous narration canary in a
   synthetic valid recorded player-display fixture if supported by its policy.

Existing tests cover unseen NPCs and a mixed visible/hidden event receipt
(`history_exposes_only_completed_visible_messages_and_never_a_draft:469`), but
not an all-visible outcome paired with private non-spoken input. The v2 replay
test currently exercises only the Player lens.

Smallest correction: make player input/narration explicitly eligible only for
Player/player-character and Omniscient lenses. NPC history can derive speech from
witnessed Say effects without inventing a new transcript or knowledge mechanism.

## Finding 2 — P1: hidden local fulfillment leaks through promise state and sources

At `inspection_query.rs:646–670`, an incoming promise is eligible if its creation
was witnessed, but `completed_by` is always appended to sources (as Withheld when
unseen), and status uses global `Commitment::status`. In `engine.rs:980`, accepted
CompletePromise explicitly remains a local ledger inference that does not
telepathically notify the creditor. Consequently the creditor's Promise row
changes to fulfilled and gains a completion marker without a visible completion.

Masking only the source event ID is insufficient. Both fulfilled and the extra
Withheld source disclose hidden completion. The same row feeds Provenance and
TurnDiff (`state_rows:508`), and its fields enter search/count. The field cannot
be justified by the current source comment that an existing context permits the
value: `character_context` contains no commitment completion grant.

Concrete regression vector, no model required:

1. With `lantern_quay.json`, commit Promise(id=`visible-return`, to=`mira`,
   terms=`Return the potion`, deadline=150, return_item=`potion`). This creates
   an observed promise at sequence 1.
2. Commit Give(potion, mira, 1) at sequence 2. Save Mira's Promises and Provenance
   rows at this completed head. The promise is open with source Event(1).
3. Commit CompletePromise(`visible-return`) alone at sequence 3, still at story
   time 100. It has Mira as a participant but only player as a witness. Confirm
   the test's actual witness set; do not treat participant membership as access.
4. Query Mira at current head 3. The reviewed code yields fulfilled with
   `[Event(1), Withheld]`; expected scoped status remains open, with only Event(1).
   Compare the Promise/Provenance row values before/after; public page head and
   revision necessarily differ and should not be mistaken for a hidden-row leak.
5. Search Mira Promises for fulfilled: expected zero matching rows/count/cursor.
   Query TurnDiff at completed head 3: expected no promise Change or completion
   source marker. Query historical head 2 while expected current head is 3:
   expected the same visible promise values as before completion.
6. Player and Omniscient should retain canonical fulfilled and Event(3). An
   uncompleted visible promise past its deadline must still show overdue under
   the existing public story clock. Do not mutate canonical commitments or
   materialize a competing observer ledger to implement this display filter.

Existing promise tests separately cover canonical player completion, deadline
status and witnessed incoming creation; none combines an incoming witnessed
creation with an unwitnessed completion. A hidden completion source must be
omitted entirely, not replaced by Withheld. Scoped status can derive from the
existing commitment with completion considered only if visible, and the inspected
story clock. Future observer knowledge transfer remains owned by shared memory.

## Reviewed paths without an additional concrete failure

- Host (`host.rs:327–346`) checks open session and exact scope, reloads one
  authoritative durable Engine, and derives the page outside its Host lock.
  A subsequent commit cannot mutate that clone. Expected-head validation is
  against the loaded Engine rather than a stale cached session. No query route
  calls a provider or writes canonical state.
- Strict Query/Observer serde inputs and the generated request schema do not
  accept a renderer-supplied Story Lab grant. Trusted Host construction supplies
  the boolean; this is an application privilege boundary, not a hostile-renderer
  sandbox or the still-pending deliberate UI spoiler acknowledgement.
- `at:320` rebuilds historical completed receipt prefixes with Engine::replay;
  it does not label current projections with an old revision. Future and partial
  turn boundaries reject. Unsupported actual fork history is explicit.
- Grant, scope/head, historical snapshot and row eligibility precede row search,
  count, page selection and cursor binding. Belief ordinals are assigned after
  observer filtering. The two findings concern incorrect row eligibility/value
  derivation, not a raw-state search performed before this pipeline.
- Cursor identity covers the complete query excluding cursor, matching eligible
  serialized rows and offset. Changed lens/view/head/search/limit/revision/rows
  invalidate a copied token. Checksums are deliberately not authentication.
- Rows/pages/search/cursors have explicit byte and count limits. Oversized visible
  rows fail closed. Candidate derivation and replay allocate before final bounds;
  existing docs correctly disclose that these are API bounds, not an OS memory
  guarantee or a measured long-history performance result.

These observations are finite source review, not proof of all interleavings,
privacy or native behavior. No additional finding was established in generated
request-contract correspondence. Response types are not generated by this
request-only envelope schema; native UI consumers remain coordinator work.

## Evidence and handoff

Read-only checks actually performed: `git status --short` (clean reviewed tree),
`git log`, `git show f7968d2 -- crates/locallore/src/host.rs`, focused `rg` searches,
PowerShell `Get-Content` source/test/schema reads and `Get-FileHash` source hashes.
The reviewer's Windows PowerShell environment was used only to read source.

Reviewed query SHA256:
`61afc5710b958ac1dbb8433f2132436ff379d9161d4fae9c58be84e90729616f`.
Reviewed Host SHA256:
`cf2e02563acf2256303f2b3bd17443d2036714229cb2ccbf64eb55597a1af05f`.

Both findings were sent to the coordinator before this report. The coordinator
confirmed them and is implementing fixes/tests in its D05 integration worktree:
NPCs receive only witnessed events; hidden completion is omitted from both
status and sources. That stated plan is not a reviewed or executed correction.
Next runnable task: coordinator runs the above adversarial regressions through
the shared module and Host, records exact results, and then integrates the
native inspector. No new memory implementation or generation grant is proposed.
