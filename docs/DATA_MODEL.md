# Data model and state invariants

Status: target data model for M02/M04. The implemented [v1 host contract](DOMAIN_CONTRACT_V1.md) defines the current typed subset; names below also describe future records. The [SQLite foundation](storage/README.md) implements schema 1 and validated root-seed persistence. Accepted-turn persistence, outcome replay and full memory tables remain later M04/M06 work.

## 1. Identity, time, and scope

A display name is not an identifier. Use stable opaque IDs for stories, branches, entities, events, turns, abilities, quests, and facts. A model refers to known IDs or declared temporary references; it does not choose arbitrary database keys. Validate every reference against the current scope.

Use two distinct clocks: an engine-assigned event sequence/revision for ordering and a story-time representation for fictional time. Real-world timestamps are diagnostics, not proof that a fictional deadline elapsed. All comparisons involving fictional time use the story's declared time system.

A branch has a story ID, optional parent branch, fork event/revision, and own head revision. The eligible history is its own committed events plus ancestors capped at each fork point. Parent events after a fork and all sibling events are excluded. Validate ancestry cycles and bounds on import.

## 2. Core records

| Record | Key information | Authority / notes |
|---|---|---|
| Story | ID, title, creation configuration, rules/profile version, content boundaries | Canonical seed/config changes are event-backed |
| Branch | ID, story, parent, fork point, head revision | Canonical lineage; no implied merge |
| Turn | ID/idempotency key, branch, expected revision, draft status, committed event range | Lifecycle state; a draft is not story history |
| Entity catalog | Story-scoped identity/type, introduction event, stable aliases | Identity catalog; introduction must be eligible in the branch before exposure |
| Accepted event | Story/branch, sequence, type/version, participants, resolved payload, witnesses, source turn | Authoritative event history |
| Entity projection | Story/branch/entity, revision, mechanical and current narrative state | Derived by reducers; no cross-branch shared mutable sheet |
| Fact record | Subject/predicate/value, validity interval, source event, visibility | Ground-truth assertion only when validly established |
| Statement/claim | Speaker, proposition, audience, event/time, optional deception intent | Establishes a statement, not the proposition's truth |
| Belief | Believer, proposition, confidence category, source events, last revision | May be false or uncertain; separate from truth |
| Observation | Observer, perceived event/aspect, limits and source | Observing speech does not prove its content |
| Relationship | Directed source/target, dimensions/descriptions, evidence, current interval | Projection of relationship-relevant history |
| Thread/commitment | Participants, terms, trigger/deadline, status, source events | Promises and objectives remain explicit |
| Summary | Scope/type, covered event set/range, source revision, visibility, generator versions | Derived and replaceable |
| Search/embedding entry | Scope, source reference/revision, index/model version | Derived; eligibility before prompt use |
| Snapshot | Story/branch/revision, projection version/hash | Replay accelerator, not independent canon |
| Model/profile manifest | Artifact provenance/hash, runtime compatibility, template and license references | Configuration, no bundled weights required |

Use composite foreign keys or equivalent validated constraints for scoped references. SQLite foreign-key support must be enabled and tested for each connection. A global `entity_id` lookup without story and branch-eligibility validation is prohibited. Search indexes are not exempt from these checks.

## 3. Event envelope

An illustrative event shape, not a finalized wire schema:

```json
{
  "schema_version": 1,
  "event_id": "evt-example-0042",
  "story_id": "story-example",
  "branch_id": "branch-main",
  "sequence": 42,
  "turn_id": "turn-example-0017",
  "event_type": "item_consumed",
  "story_time": {"day": 3, "tick": 120},
  "participants": ["player", "mira"],
  "payload": {
    "item_id": "potion-instance-01",
    "previous_owner_id": "player",
    "consumer_id": "mira",
    "quantity": 1,
    "resolved_effect": {"injury_change": "improved"}
  },
  "witnesses": ["player", "mira"],
  "provenance": {
    "source_turn_id": "turn-example-0017",
    "rules_version": "fantasy-example-v1"
  }
}
```

The engine supplies authoritative identity, sequence, branch, and validated resolved effects. A director proposal has its own request schema and cannot pass a fabricated event envelope straight into storage. A successful transfer followed by consumption may be separate events in one atomic turn; the example combines them only to illustrate required provenance.

An event may involve multiple roles: actor, target, recipient, speaker, audience, witness, and bystander. Do not flatten a multi-party event into unrelated pairwise interactions and lose who actually saw what.

## 4. Player and NPC state

Mechanical state includes resources, items, learned abilities and ranks, prerequisites/costs, current injuries, location/status, and progression. Stable identity/backstory is distinguished from evolving state. Subjective traits and interpretive memories are tagged as such; they do not silently change rules.

For every ability, record the canonical definition/rules version, acquisition event, rank, limits, resource cost, and current availability. Saying 'I teleport' does not acquire teleportation. An author-mode edit granting it is a separate explicit operation with provenance.

For resources, define integer/fixed-point units and valid ranges. An inventory instance has one effective owner at a time within an eligible branch. Containers and stackable quantities need explicit rules rather than string matching.

## 5. Truth, knowledge, and deception

A truth assertion concerns the world. A claim records what was said. A belief records what a character thinks. An observation records what they perceived. A discovery updates eligible knowledge because an event exposed evidence. These can disagree without corrupting the database.

Example: the player stole a relic; Mira believes bandits did; the captain suspects the player. A later confession creates speech and belief/knowledge updates only for relevant listeners. Witnessing the confession is not necessarily conclusive proof in every story profile.

Use an uncertainty category or evidence-backed confidence where useful, but do not pretend a model-generated probability is calibrated. A summary containing a claim must preserve attribution. The narrator cannot turn 'Mira suspects the captain' into 'the captain did it.'

A record has visibility, source evidence, and an effective time interval. Remembering that Mira was at the tavern yesterday does not imply she remains there now. Historical beliefs should not be rewritten when later evidence changes a character's mind.

## 6. Relationship graph

A directed edge connects an ordered pair of entities. It may contain categorical/ordinal dimensions such as trust, respect, fear, affection, resentment, and obligation, plus a concise evidence-linked description. Each dimension's meaning/range belongs to the rules/story profile; do not invent universal scientific scales.

Supporting interactions remain event records. Relationship updates cite those events and can be rebuilt. A player sacrificing a resource can plausibly improve gratitude without forcing trust, romance, or agreement. An NPC's background, goals, social context, and prior betrayal may still dominate the response.

Graph traversal should be query-based and bounded. There is no requirement for a dedicated graph database. A character can have abilities/stats/background in its entity state and relationship memory without loading a separate LLM.

## 7. Idempotency and concurrency

A turn ID is unique within its declared scope and cannot be reused to apply a different payload. Store a request digest where needed to reject mismatched retries. An `expected_revision` comparison prevents stale updates. A per-branch in-flight lease improves UX but does not replace transactional checks after process death or duplicate requests.

The commit transaction appends events, updates projections, stores the final response, and moves the branch/turn status together. Random draws/resolved results are recorded once. Retrying a committed turn returns its result; it does not re-run randomness or award another reward.

## 8. Replay, corrections, and branching

Replay consumes accepted versioned events and rules/migration definitions. It does not call a model, regenerate prose, or reroll dice. Compare canonical projection hashes using a documented deterministic serialization. Exclude only documented transient data such as process timings, not inconvenient world-state differences.

A correction to the world's actual past is not the same as an in-world character learning a previous belief was wrong. The former creates an explicit revision/branch and invalidates dependent derived artifacts; the latter is a new story event preserving the prior belief history.

Default rewind/edit behavior is branching. A new branch forks before the edited turn and does not silently inherit later outcomes. Selective retention of later events is future work requiring causal validation, not an initial automatic feature. Branch merging is out of alpha scope.

## 9. Deletion, retention, and migrations

Deleting a story removes its canonical records, derived memory, indexes, drafts, and caches. Deleting a parent branch must not break retained children: either retain required ancestry or materialize the validated inherited history first. Model files are separate shared resources and should not be deleted merely because one story stops referencing them.

Use consistent backups for schema migrations. Validate compatibility before importing; commit imports atomically into a new namespace. Keep original archives unchanged and explain that external copies and forensic flash remnants are outside an ordinary database-delete guarantee.

## 10. Required contract tests

Cross-story foreign-key mismatch; entity introduced only in a sibling branch; parent event after fork; duplicate reward; item double ownership; negative resource; unknown ability; dead actor acting without a valid story rule; a statement misclassified as truth; unauthorized witness; stale relationship summary; corrupted snapshot; mismatched retry digest; stale generation after branch switch; archive ancestry cycle; and replay after migration. These are minimum examples, not exhaustive proofs.
