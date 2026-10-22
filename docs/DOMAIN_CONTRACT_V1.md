# Domain contract v1

Status: implemented and host-tested proposal for M02.01–M02.06; upstream acceptance
remains with the owner. Rust definitions in `crates/locallore/src/contracts.rs`
are the authoritative v1 wire shapes. This document describes the supported small
profile, not the complete future engine. No production model/runtime is selected.

## Authority and scope

The trusted application constructs a `Request` with explicit typed intent after
UI selection or clarification. A model produces only a `Proposal`. Both carry
version 1, story/branch IDs, turn ID and expected revision. The engine requires
the proposed commands to match authorized intent exactly, validates all
operations against a staged projection, and constructs accepted event envelopes.
The model cannot choose sequences, witnesses, rule versions or resolved effects.

Free text does not become an authorized action merely because the director
interpreted it. A future free-text UI can present its interpretation for
clarification before constructing the trusted action. `Dialogue` accepts only
that exact speech and selected listeners. `Thought` and `Ambiguous` return
`ClarificationRequired` without inference or mutation. `AuthorCorrection` returns
`AuthorUiRequired`; this host has no author-edit capability. Quoted/out-of-story
instructions are speech, never SQL, code, tools, world edits or history rewrites.
No marriage, betrayal, motivation or other major player choice is implicit.

IDs are opaque local identifiers resolved inside a validated scope; display names
never resolve identity. Every request and retrieval includes story, branch and
revision. A context request at a stale revision fails rather than mixing a past
event range with a present sheet. V1 has no generic operation, arbitrary script,
temporary-entity creation, reward grant or truth-edit command. Unknown JSON fields,
unknown enum variants, fractional/negative quantities, unsupported versions and
oversized inputs fail closed. Import of untrusted accepted history is absent.

## Profiles, progression and inventory

| Rule | Numeric fantasy v1 | Narrative v1 | Failing/positive executable evidence |
|---|---|---|---|
| Resources | Energy `u16`, valid 0–100, exact checked subtraction | No energy or combat attributes/abilities | `abilities_have_prerequisites_ranks_costs_and_provenance`, `narrative_profile_works_without_combat_stats` |
| Ability | Known definition, rank 1..max, prerequisites, cost, seed or acquisition event | Rejected | Same ability test; unlearned/unknown/max-rank/prerequisite cases |
| Learning | Only seeded curriculum, living co-located teacher who knows ability, prerequisites | Rejected | Same ability test; teacher definitions are preauthorized by the synthetic profile |
| Attributes, injuries, affiliations, goals | Seed-backed structured state; consumption can remove one injury | Seed-backed narrative state | `consumption_records_resolved_injury_and_conserves_quantity`, `invalid_seed_and_operation_limits_fail_closed` |
| Inventory | One owner per item/stack ID; positive `u16` count | Same | `inventory_bounds_and_borrowed_key_are_enforced` |
| Transfer | Full stack only, living co-located recipient, no self-gift | Same | Inventory test; no implicit split or duplicated item IDs |
| Consumption | Healing item owned by player, an existing injury, one unit consumed | Rejected | Consumption test, partial-consume rejection test |
| Loan | `return_to` restricts transfer to lender; cannot consume or give away | Same | Inventory/key-return tests |
| Life/location | Dead player cannot act; directed seeded routes; current co-location required | Same | `dead_and_remote_actors_cannot_act_or_witness` |
| Currency | No currency operation in v1. Future currency uses checked integer minor units and declared maximum; never floats or string parsing | Same | Unknown operation and numeric attack tests reject unsupported edits |

All seed fields cite the seed ID; progression changes cite engine event sequences
in `progression_sources`. Identity/backstory and numeric rules do not come from
recaps. Giving an unborrowed healing item increases only the recipient's existing
directed obligation toward the player by one (bounded at 100). Trust/respect and
the reverse edge remain independent. Returning a loan does not create a debt in
the lender. Other relationship changes, arbitrary attribute grants, combat,
resurrection and automatic off-screen NPC actions require later explicit rules.
`UseAbility` demonstrates cost/rank checks only; it has no invented combat or
teleport effect. NPC consumption/teaching dialogue are not simulated here.

## Truth and observer boundaries

Canonical truth is established by the trusted seed in v1; play cannot change it.
`Say` records the speaker, literal proposition text, audience and source event.
Hearing it establishes an observation of speech, not truth of its content.
`Believe` adds an uncertain, attributed player belief only when its claim source
is already accessible. Seeded NPC beliefs may be false or suspected. Those
records do not move a relic, change ancestry or establish guilt.

`Discover` requires an existing discoverable fact at the player's current
location and a first discovery. It updates only the player's evidence-backed
knowledge. Gift witnesses are the actor and validated recipient; speech
witnesses are the actor and validated co-located listeners. Other bystanders are
conservatively excluded. The model cannot append witnesses. Fulfillment of a
promise is a player ledger inference and does not notify an absent creditor.

`character_context` filters scope/ancestry/revision/observer **before** content is
serialized. It includes only that character's self-state, entitled facts,
observations and beliefs, with source metadata. It has no omniscient world dump,
other characters' sheets, or summary input. This is a finite context proof, not
M07 ranking, temporal fact intervals or semantic retrieval. An old observation
retains its event/time; it does not claim the subject is still present.

`unequal_knowledge_is_filtered_before_serialization`,
`claims_beliefs_and_truth_stay_distinct_with_attribution`,
`discovery_requires_evidence_here_and_does_not_teach_bystanders` and
`narrator_never_receives_secret_seed_and_cannot_grant_summary_rewards` exercise
these boundaries with a secret canary. No summary/index API can mutate canon.
False beliefs remain attributed even when their proposition disagrees with truth.

## Events, time, atomicity and branches

Each accepted event records version, story/branch, engine sequence, turn,
rule/profile, seed provenance, story time, participants, witnesses and resolved
effect. `Receipt` stores the exact request, proposal, accepted events and final
response. Accepted types are engine-created and have no public deserializer.
An ordinary command source is an accepted turn; seeded beliefs/commitments carry
typed `Evidence::Seed`, and changes carry event evidence. No hidden reasoning
trace is recorded. Narration never supplies new effects.

A turn stages all commands against a private projection. A single failed command
rejects the whole turn; successful commit replaces the in-memory projection and
appends one receipt. Duplicate `(story, branch, turn)` plus identical full request
returns that receipt without inference. Different request data under the same
key fails; stale revision/scope fails. This establishes in-process atomicity and
idempotency only. SQLite transactions, process death, storage exhaustion, concurrent
writers and restart durability remain M04; no disk-backed save is supplied.

Story time begins at the seed time and advances only through bounded `Wait`
commands. A promise remains recorded when overdue. Return-item commitments cite
actual transfer identity, sequence and fictional time, and require return to the
creditor. Return at the deadline counts as on time. Recognition can occur later:
the return event's time decides fulfillment, not the time the ledger is updated.
Vague prose promises remain open; no model can mark them fulfilled generically.

Forks rebuild an eligible completed-turn prefix from the seed and accepted
receipts. A child excludes later parent and sibling events; every ancestor cap
applies, including nested forks. IDs are unique within lineage, depth is bounded
at 32, and a new fork cannot reuse an ancestor ID or point beyond head. Half-turn
forks fail. No branch merge, destructive retcon, cycle import or archive API
exists. `ancestry_caps_every_ancestor_and_rejects_invalid_forks` and
`forks_exclude_later_parent_sibling_and_stale_projection` cover these boundaries.

Root replay uses engine-created typed receipts without inference or randomness.
It revalidates deterministic v1 commands and compares every regenerated accepted
envelope with the recorded resolved outcome; a mismatch or duplicate log entry
fails. This is a **verified v1 replay proof**, not yet a migration-capable outcome
reducer/archive format. M04 must reduce stored effects with pinned rules/migrations
and rebuild persisted branched histories. Canonical projection bytes use JSON
struct field order plus sorted maps/sets, exact integers and no diagnostics; they
are compared byte-for-byte, not presented as a cryptographic archive checksum.

## Inference boundary and bounds

`GenerationRequest` supplies immutable scope/turn/revision, profile/schema IDs,
role-specific input and budgets. `InferenceProvider::poll` returns pending,
bounded bytes or a typed error. Its cancellation token is shared and one-way.
The caller owns one exclusive provider session and drops/releases it on terminal
completion; native adapters must promptly return, honor cancellation and release
native resources on drop. No DB handle or unrestricted file/tool capability
crosses the interface. One Rust persistence owner will own SQLite migrations and
writes; Kotlin consumes the adapter and cannot independently mutate that database.

The proof runs director → strict parse → staged engine resolution → narrator →
exact narration check → cancellation/revision recheck → commit. The narrator
receives only the engine's permitted description. It must return the exact safe
template in this packet. This deliberately restricted fallback tests grounding;
it does not evaluate or validate free-form model prose. A native role/cache/session
key must include the immutable scope/revision/observer and model/schema versions.

Bounds: 8 commands, 16,384 serialized request/proposal/output bytes, 2,048 speech
bytes, and 32,768 serialized character-context bytes. Oversized mandatory context
fails safely. Default fake budget: 512 output tokens requested, 8 pending polls,
1,000 ms deadline. Hard bytes/polls and cooperative deadline checks are enforced;
without a tokenizer the fake cannot verify a token count. Native adapters must
count candidate tokens and provide genuinely cancellable execution. Busy polling
is a deterministic host fixture, not an Android scheduler. The adapter may not
block past the deadline; the trait alone cannot preempt arbitrary blocking code.

There are exactly two generation attempts on success, **zero repair attempts**,
and safe unchanged-state failure otherwise. Fake modes cover accepted, malformed,
mechanically rejected, delayed, cancelled, failed, oversized and invented
narration cases. Cancellation before commit leaves no effects; a repeat after
commit returns the accepted receipt. A future async/mobile adapter must separately
prove stale branch switching, lifecycle/resource disposal and cancellation races.

## Original fixtures and review

`fixtures/lantern_quay.json` is original synthetic material. The player and injured
Mira begin at the quay, Oren at the pier, and Sable (also displayed as Oren) in the
tower. There is one potion, a borrowed brass key, a hidden tideglass relic, unequal
NPC beliefs, independent respect/distrust, a timed return promise, and unlearned
abilities. The host demo transfers the potion to Mira; it does **not** claim Mira
consumed it, survived an app restart or produced real model prose. Player
consumption is a separate mechanical fixture.

The independent review matrix is `docs/reviews/M02_ADVERSARIAL_REVIEW.md`;
its conceptual examples are acceptance inputs, while the executable JSON and
this v1 contract define exact profile numbers/names. Each test in
`crates/locallore/tests/contracts.rs` asserts observable state, history or context.
The fixed-seed 10,000-attempt test independently checks conservation, valid owners,
resource ranges, rejection immutability and final replay equality. It does not
complete M10 fault/mobile/privacy/quality qualification.
