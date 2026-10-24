# Narration ownership contradiction: independent frozen regression

Date: 2026-10-23. Partial #12 M08.03 / #25 D04.04/D04.06. Source-only test
packet, not model-quality acceptance or a general semantic consistency proof.

Branch `review/m08-narration-ownership`, worktree `source-narration-ownership-review`,
base `5f87abf1f631105fa0b091622301a2962df12e4d`. Claims before edits:
[#12 6378282776](https://github.com/OptimumAF/LocalLore/issues/12#issuecomment-6378282776)
and [#25 6378282982](https://github.com/OptimumAF/LocalLore/issues/25#issuecomment-6378282982).
Own only NEW `crates/locallore/tests/m08_narration_ownership_review.rs` and this
NEW report. Root owns production policy and actual qualification. No existing
source/test/fixture/model output was edited.

## Actual observed failure, retained separately from plumbing results

Root reported the current actual-model cohort
`model-native-2d65c91f-f18c-433a-ba74-96db601d844a`, executed source5f87abf,
`initial/report.json`: the potion receipt had fallbackfalse despite narration:

> I gave a small bottle of potion to mira. The potion was warm and felt like it
> had magic in it. I didn’t know what happened next, but I took the potion with me.

The accepted canonical effect transfers the potion to Mira; the player has no
potion afterward. The final sentence contradicts that accepted transfer. Root's
53 passing native plumbing assertions do not establish prose correctness. The
original source/cohort/report/prose remain retained, not reworded, retuned or
reclassified as a successful semantic result. This reviewer did not execute or
repeat the model, inspect private unrelated stories, or alter that evidence.

Actual `play.rs::validate_prose` has finite unsupported-consequence checks and
Given phrase checks such as `still holds`, `still have`, `keeps the potion`,
`retains the potion`, refusal and negated giving. It misses first-person
`took ... with me`, `kept`, `carried` and related ownership continuations. These
checks do not make prose authoritative; state was already protected by Core.
The defect is contradictory displayed narration being accepted without fallback.

Root's planned correction is a conservative **current grounded-prose-v2.2**
ownership guard, constrained by actual approved Given item/transfer evidence.
It must not become an unconditional rejection of the recipient holding the item,
scan/rewrite literal player dialogue, introduce a new effect, or change legacy
grounded-prose-v2.1 recorded-history validation. Exact implementation is Root's.
No perfect NLP, first-person interpretation, broad semantic entailment or prose
quality acceptance is claimed. Other unsupported contradictory paraphrases can
remain outside a finite guard; report that limit honestly.

## Frozen source and substantive oracles

Test commit `ac00aa57e16c845dfd5b65486170ebb989a0cb3d`; SHA256
`fd54843e110994678bb4d397c69fbf2aac64f974cb93b66b12acb67fce61d4a5`.

Five methods invoke the actual current Play pipeline with bounded clearly
synthetic ScriptFakeProvider replies, not a forged Receipt or alternate prose
validator. Valid Director commands pass actual parsing, finite intent guard,
agency and mechanics. Narrator responses use actual event ID1 and narrator
speaker. Exactly two roles, Director/Narrator, are required; no generation
repair/retry is added to evade a failing narration oracle.

1. The exact full observed prose above must produce real mechanical fallback.
   The synthetic action request is the supported finite `I give potion to Mira.`;
   the actual cohort controller input is `I give my last potion to Mira.` in
   `ui/model-journeys.ts:299`. Both resolve the same actual Give potion1 to Mira.
   This is a reproduction of the recorded prose against real current pipeline
   transfer evidence, not a new actual-model sampling or exact prompt replay.
2. For both potion and a synthetic seed with that item renamed to vial,
   `I kept the <item>.`, `I carried the <item> with me.`,
   `The <item> remained with me.` and `I took the <item> with me.` must fallback.
   The second item prevents a potion-only phrase patch from satisfying the case.
   No accepted seed/fixture is edited. Finite intent-guard source admits that
   literal item ID; actual execution remains unrun here.
3. Exact grounded `Mira now holds the potion.` must remain the displayed
   nonfallback prose. The guard cannot confuse the canonical recipient with the
   player or reject every reference to holding an item after Give.
4. Literal Dialogue `I kept the potion with me.` is preserved as the exact
   accepted Said text and original request, with no transfer and potion still
   player-owned. A grounded narrator response remains nonfallback; raw literal
   dialogue does not reach that narrator request. Ownership text in speech is
   not rewritten or turned into an action by the narration policy.
5. Immutable accepted2.1–2.4 fixture file hashes remain exact. Actual strict
   restore preserves each recorded receipt; exact retry calls zero providers
   even when canceled. Original2.4 compact receipt/PlayRecord hashes and exact
   compact receipt asset bytes remain pinned.

Every Give case compares events and canonical state projection to an independent
**actual Core typed Give execution**, not a second evaluator. It requires one
accepted event, one record, revision1, Mira ownership and no player-owned copy.
Fallback text must equal actual `engine::render(events)`. The genuine resulting
record strictly restores unchanged and exact-key retry uses no provider.
This proves no extra canonical effects within the frozen scenario once run;
it does not claim that a fake provider demonstrates model behavior or UI layout.

Pinned existing fixture SHA256 values (files already LF under .gitattributes):

| Immutable fixture | SHA256 |
| --- | --- |
| accepted_play_v2_1.json | 3aefb5a8c1a9ad0f27b15d424dfcecf5f7fb58a639572758a6128fb75ace36d4 |
| accepted_play_v2_2.json | f3645af4047e02b827010134cb57b1d974c86538b68ebf8e43801ea8bcde8f3d |
| accepted_play_v2_3.json | 57fb218ef2f9a50842f77c2c87cd7e694ca53ea064c6205cfef18abd9e51035c |
| accepted_play_v2_4.json | f08801ab9ce13e0bb47434896dafa1e8e671fa4f4a239731cbd2ee0f42730e2d |
| accepted_play_v2_4_receipt.json | 38dcf7329addf4ed98fd984cdb9eac95f8d078be03bf4633dd7082d23ac4bc3f |

Original2.4 compact PlayRecord SHA256 remains
`6ed4abcd325e14fa334d23ead9b843ebe93afd91e26b28e3167ad95e552b9341`.
No asset/hash/source field is regenerated. Previously accepted unmerged
current2.5 contradictory output stays in original evidence; this packet does
not rewrite it into fallback or promise it passes stricter future validation.
The legacy compatibility gate here is original accepted2.1–2.4 behavior/bytes.

## Actual checks, limits and next runnable task

Actually performed: source/Git inspection, hashing, `rustfmt --edition 2021`
parser formatting, `rustfmt --edition 2021 --check` and `git diff --check`, all
passed. Git2.33.0.windows.2 / PowerShell7.6.5 / rustfmt1.8.0-stable source
environment. **All five new tests are UNCOMPILED/UNRUN.** No reproduced test RED
or corrected GREEN is claimed by this reviewer. The earlier model semantic
failure is actual coordinator evidence, separate from these unrun assertions.

No Cargo/Node/Gradle/provider/model/native/app/device/ADB/CUA/desktop/protected-
resource/settings/PR/merge execution was performed. No model output, expected
command, profile, token/deadline budget or earlier assertion was retuned. The
test-only profile is the existing bounded synthetic4096/350/350/5000ms shape.

Next: Root imports this frozen test source before its policy edit, executes
`cargo test --locked -p locallore --test m08_narration_ownership_review -- --nocapture`
in its serialized slot, retains exact compile/fixture/behavior failure attribution,
implements the narrow current-policy guard, then reruns the unchanged packet and
appropriate existing current/legacy checks. Any later actual-model/native run
must retain this original failed cohort and be independently scoped/evidenced.
Both new-path claims release at handoff; no whole D04/M08 acceptance follows.
