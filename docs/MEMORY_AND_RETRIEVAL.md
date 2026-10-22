# Memory, context compilation, and narrative continuity

Status: proposed design. The main objective is useful retrieval with bounded cost and explicit provenance, not stuffing every message into context.

## 1. Memory layers

**Progressive state:** player/NPC abilities, resources, items, injuries, background, motivations, and current relationships. Read exact structured state for mechanics.

**Event history:** accepted actions, statements, consequences, observations, discoveries, and author revisions. Durable, scoped, and replayable.

**Working scene:** participants, location/time, recent dialogue, unresolved action, immediate objective, and recent accepted-event deltas. The current scene has a bounded prompt footprint.

**Long-term narrative memory:** evidence-linked scene/chapter/entity summaries and important experiences. These compress context but remain replaceable.

**Relationship/knowledge network:** directed relationships, event participation, claims, beliefs, secrets, witnesses, and evidence. The graph connects records instead of becoming another authority.

**Open threads:** promises, clues, obligations, deadlines, rivalries, and ongoing goals. These can remain pinned by unresolved status regardless of age or lexical similarity.

## 2. Context compiler inputs and output

Input: story, active branch ancestry, head revision, scene/time, caller role, observer ID where applicable, player intent/referenced entities, rule/profile version, model/tokenizer, and token budget.

Output: an ordered context package, source-record IDs/revisions, included/excluded reasons, visibility class, and measured token count. A developer diagnostic view can expose safe retrieval rationale; it must not reveal secrets in ordinary play or export private content by default.

Do not let each prompt independently invent a retrieval query. Centralize scope and eligibility in a tested API. A summary or vector hit is never trusted simply because it ranked first.

## 3. Eligibility before relevance

Apply these restrictions before a record can enter model context:

1. It belongs to the intended story.
2. It lies in eligible branch ancestry at or before each fork point.
3. Its temporal meaning matches the request; historical facts are labeled historical.
4. Its visibility and observer entitlement permit access.
5. Its source revision is valid; superseded/invalidated derived content is excluded.
6. Its record type is appropriate: a claim cannot silently masquerade as established truth.

For FTS/embedding systems that cannot prefilter the entire search, retrieve opaque candidate IDs and apply eligibility before fetching/serializing content. Wrong-scope text must not enter prompt logs, rerankers, or a hosted service. Cache keys include story, lineage/revision, role, observer, model/tokenizer, and relevant policy versions.

## 4. Retrieval order

First reserve mandatory context: applicable rules, current mechanical state needed for the action, active participants, immediate scene, and unresolved action constraints. If it cannot fit, narrow the scene/action or stop safely rather than silently dropping a critical rule.

Then resolve explicit references through entity IDs, aliases, and ambiguity handling. Retrieve relevant commitments, recent interactions, supporting relationship events, and evidence for questions asked. Expand a bounded number of graph hops for connected people/items/threads; avoid recursively loading the entire social network.

Next retrieve older events through structured queries and local lexical search. Weight relevance, recency, importance, and unresolved status using documented heuristics. A very old unfulfilled promise can outrank recent small talk.

Finally add short narrative summaries and optional flavor context. Leave enough capacity for chat-template tokens and bounded output. Record what was omitted so evaluation can tell retrieval failure from model failure.

## 5. Proposed initial token budget

A first experimental profile may use an approximately 4,096-token working budget, not the model's advertised maximum. For example, allocate roughly 600 tokens to instructions/schema overhead, 700 to relevant rules/state, 900 to the scene/recent dialogue, 650 to historical evidence, and the remainder to generation/template margin. These are adjustable test allocations, not measurements or hard universal recommendations.

The director and narrator need different packages. A 4k total budget cannot be assumed safe until the actual tokenizer, template, grammar, response cap, and KV-cache/runtime requirements are measured. If the runtime uses a different context accounting model, record it. Never convert disk weight size directly into claimed total RAM requirements.

## 6. Summarization lifecycle

Create summaries at scene boundaries or when a bounded history segment reaches a threshold, not after every sentence. Inputs are the eligible accepted events and relevant transcript excerpts, not an endlessly compressed previous summary. Structured outputs should preserve actors, time, claims versus facts, unresolved commitments, and key changes.

Store source event IDs/ranges, story/branch/revision, visibility, summary schema version, prompt/model provenance, and generation time. A summary generated under omniscient access is not safe to pass to a character with restricted knowledge. Prefer visibility-specific source sets; do not rely on a model to redact all secrets from an omniscient summary.

When new events exist after a summary's coverage, append exact deltas. When a correction or branch change invalidates its basis, exclude/regenerate it. Maintenance tasks are resumable and cancellable; they cannot establish new canon. A model-generated summary is checked for unsupported claims and unresolved attribution before use, but checks are not infallible.

## 7. Embeddings and reflection are optional

Start with IDs, explicit relationships, event tags, and full-text search. Add local embeddings only when the retrieval benchmark shows specific paraphrase failures, and compare against the simpler baseline. A vector model consumes RAM, storage, compute, and an additional dependency/license budget. Record embedding model/version and rebuild rules when it changes.

A character reflection may be a useful inferred interpretation, such as 'Mira is becoming wary of the player.' It must be labeled an interpretation and tied to evidence; it cannot overwrite established events or invent a new betrayal. Distinguish a narrator's hypothesis from a character belief accepted as a story event.

The memory/reflection/planning pattern has a research precedent in *Generative Agents*, but that paper is not evidence that this design works on the target phone or guarantees long-term correctness. See [S10](REFERENCES.md).

## 8. Test scenarios

Retrieve a promise after 1,000 unrelated events; use an alias; disambiguate two characters with the same name; remember an item transfer; preserve an allegation's attribution; keep a lie distinct from truth; exclude a sibling-branch death; exclude a later parent event after a fork; handle stale summaries; filter a secret from an NPC context; handle a character's outdated knowledge; and recover when mandatory context exceeds the budget.

Use two metrics: whether the right eligible evidence was retrieved, and whether the model used it faithfully. An answer can be wrong despite correct retrieval, and good prose can conceal missing evidence. Measure latency and memory as well as recall.

## 9. Visible memory UX

The ordinary player view shows what their character can reasonably know, current state, visible relationship evidence, and open threads. A spoiler warning precedes author/omniscient inspection. 'Why does the story think this?' opens supporting accepted events, not an invented chain of thought or raw hidden model reasoning. Let the user report an incorrect interpretation and enter the explicit correction flow.
