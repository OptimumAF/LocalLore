# System architecture

Status: target architecture, 2026-10-22. The bounded [v1 host contract](DOMAIN_CONTRACT_V1.md) implements pure rules and fake-provider coordination in one Rust crate. The [Compose shell](../apps/android/README.md) displays Rust-generated fixture outcomes through a replaceable sample adapter. Live native engine/inference and persistence remain future work; the proposed module layout is not a list of existing packages.

## 1. Authority and component boundaries

```text
Phone UI
  | player text + explicit UI commands
  v
Application / turn coordinator
  | stable story/branch/revision snapshot
  +--> Context compiler --> scoped memory queries
  +--> Inference adapter --> one local model / sequential roles
  +--> Domain engine --> validation + resolution + event reducers
  +--> Persistence owner --> SQLite events + projections + drafts
  +--> Derived-memory jobs --> summaries/indexes (never canonical writes)
```

The domain engine owns rules and state transitions. The persistence layer owns all migrations and writes. The [SQLite foundation](storage/README.md) implements that Rust owner for schema initialization and validated seed storage; accepted-turn persistence remains future M04 work. The coordinator owns cancellation, revision checks, inference budgets, and lifecycle. The UI consumes typed state and cannot secretly apply inventory changes. The model cannot call arbitrary SQL, native code, filesystem paths, or network endpoints.

Proposed implementation: Kotlin/Compose UI; Rust domain/persistence core; SQLite; a small native inference adapter chosen after measured spikes. JNI/FFI integration must be demonstrated before expanding the engine API. If the Rust integration imposes disproportionate mobile maintenance costs, propose an alternative in an ADR with tests and portability tradeoffs. Do not maintain two copies of the domain rules.

SQLite is a candidate because transactions and local full-text search fit the design; the actual bundled features, foreign-key enforcement, journal configuration, and mobile integration must be tested. References [S01–S02](REFERENCES.md).

## 2. Canonical data versus derived data

Canonical: accepted seed configuration and world rules; accepted event history; explicit author revisions/branch metadata; complete committed transcript; provenance and actual resolved random outcomes. Current mechanical state is a validated projection of accepted events.

Derived: summaries, embeddings, indexes, retrieval scores, UI recaps, cached prompts, and snapshots. These carry source revisions and can be discarded/rebuilt. A disagreement between a summary and accepted events invalidates the summary, not the history.

Some accepted facts are creative authoring, not mechanical deductions. For example, introducing a previously unknown tavern is permissible if the rules and prior facts allow it. Record the new canonical fact explicitly. Do not label the engine a mathematical judge of the quality or truth of every possible sentence.

## 3. Turn lifecycle and transaction boundary

A proposed lifecycle is `received -> generating -> resolved -> narrating -> validated -> committed`, with terminal `cancelled`, `failed`, and `stale` states. These are application states to be refined in the contract milestone.

1. **Receive:** assign an idempotency key/turn ID; capture story, branch, active revision, rules and content-boundary versions. Save the player input as a draft, not as an accepted action.
2. **Snapshot:** read a coherent state snapshot; compute branch ancestry and allowed context. Start a per-branch generation lease or reject concurrent turns, while still handling process-death recovery.
3. **Compile context:** load mandatory facts and scoped history. Preserve a budget for the proposal, narration, template tokens, and runtime overhead. Stop or narrow the scene if mandatory context cannot fit.
4. **Propose:** run the local director with a bounded schema. Distinguish explicit player intent, NPC intentions, new facts, and claims. Temporary entity references are mapped to engine IDs only after validation.
5. **Resolve:** validate mechanical operations and resolve rules/randomness. Convert intentions into concrete events. Reject or repair inconsistencies and recompute dependent reactions. A model confidence number is not authorization.
6. **Narrate:** describe the resolved plan using a player-visible scene view and explicitly permitted dialogue/knowledge. The resolved plan is not yet committed canon. The engine still has the option to reject the turn.
7. **Check:** validate required structure and event/prose alignment; use targeted semantic checks where justified. A model critic is fallible. Retry within a small explicit budget or fail safely with no canonical changes.
8. **Commit:** in a short transaction, recheck turn status/cancellation and expected branch revision, append events, apply projections, attach final narration, update revision, and mark the turn committed. Only one attempt wins. A repeat returns the stored result.
9. **Post-commit:** schedule bounded derived-memory maintenance. Each job captures its source revision and refuses stale output. The app must work with exact recent-event deltas while summaries lag.

No SQLite write transaction remains open during model generation. No finalized response is shown before a successful commit in the conservative initial UX. Optional draft streaming must be distinctly labeled provisional, removable on failure, and separately tested for confusion; it is not a shortcut around validation.

## 4. Failure behavior

| Failure | Required behavior |
|---|---|
| Malformed proposal | Bounded repair; no generic execution of unknown fields |
| Valid JSON, invalid mechanics | Reject/resolve in code; model cannot override rules |
| Director timeout or OOM | Cancel work, release resources, preserve input draft and canon |
| Narrator invents a consequential fact | Reject/repair the draft or use a safe fallback; do not silently append it |
| Branch/revision changed during generation | Mark stale; never apply to the new active story |
| Duplicate send/retry | Idempotency returns original committed response or one in-flight state |
| User cancels before commit | Canon unchanged; draft state and resources cleaned up |
| User cancels after commit wins | Show the committed result; offer explicit rewind/branch, not a fake rollback |
| Process death before commit | Recover or abandon draft; no canonical effects |
| Process death after commit | Load committed events/response together |
| Storage full/import invalid | Roll back and explain; preserve existing stories |
| Summary job races with a correction | Discard stale derived output; rebuild from eligible source events |

## 5. Inference boundary

The adapter accepts model/profile ID, input messages or tokenized prompt, schema/grammar where supported, deterministic budget limits, generation settings, cancellation token, and role-specific metadata. It returns bounded output, usage/timing diagnostics, compatibility errors, and cancellation/failure status. It does not receive database handles or broad device permissions.

The initial logical roles are director, narrator, and archivist. They share model weights where feasible but not unfiltered caches or contexts. Character-specific dialogue generation is an optional extra bounded call when secrecy tests require it. Multiple roles do not imply concurrent models, an agent per NPC, or unlimited reasoning loops.

Constrained decoding helps output structure but does not prove valid mechanics or faithful prose. Runtime/schema support must be tested on the pinned implementation. See [S03–S05](REFERENCES.md).

Record model artifact hash, model revision, runtime/backend revision, quantization, tokenizer/template identity, prompt/schema versions, and approved generation parameters for each session/turn as appropriate. Do not persist hidden reasoning traces by default. Store short evidence-linked resolution explanations instead.

Changing a model affects future generated text only; it does not rewrite canonical state. Replay uses stored events and resolved randomness, not regenerated text.

## 6. Scoped contexts and character knowledge

The director may need some authoritative hidden world facts to resolve actions. The player-facing narrator should receive only the permitted surface consequences and approved dialogue, not a dump of every secret. A character-role request is built from that character's eligible beliefs/observations, current situation, and permitted common knowledge.

A prompt saying 'ignore secrets you should not know' is not sufficient isolation. Summary storage and prompt caches must be visibility-aware. Even isolated contexts do not prove a model can never guess a secret; tests should distinguish information leakage from an unsupported lucky invention, and neither invention should become canon automatically.

## 7. Rules and story configuration

Use declarative, versioned rule profiles with allowlisted operations and bounded complexity. Start with numeric resource changes, item ownership, ability prerequisites, location constraints, and explicit progression. Narrative-light profiles can omit combat arithmetic while still preserving identities, promises, knowledge, and consequences.

Do not accept arbitrary scripting in imported stories. A rules change during an existing story needs an explicit version transition and migration decision. Fixed-point/integer quantities are preferred for exact resources. Dialogue, perceptions, and uncertain outcomes may remain narrative judgments with provenance rather than spurious mathematical scores.

## 8. Proposed module layout after implementation begins

```text
apps/android/           Compose UI, Android lifecycle, native adapter wiring
crates/domain/          typed state, commands, rules, events, pure reducers
crates/storage/         SQLite schema/migrations, transaction/replay/export
crates/story-engine/    coordinator and context/retrieval contracts
crates/test-harness/    host-side replay and fake-provider fixtures
fixtures/              original synthetic worlds and adversarial scenarios
prompts/               versioned role templates, schemas, and examples
benchmarks/            harnesses and sanitized aggregate reports
docs/                  plan, decisions, build/privacy/contribution material
```

This is a proposed target layout, not an instruction to create empty folders immediately. Combine small crates until boundaries have real testing or portability value. Shared schema/prompt interfaces require coordinator approval before parallel agents build on them.

## 9. Deferred complexity

No cloud graph service, distributed event bus, unbounded autonomous NPC agents, mandatory vector database, on-device fine-tuning, speculative plug-in framework, or multitier cloud architecture. Start with SQLite tables and query-driven graph traversal. Add local embeddings or specialist models only when evaluation shows a specific failure they solve within the phone budget.

## 10. Architecture decisions to resolve

Reference device/support tiers; backend choice; Rust/native integration; SDK/dependency versions; maximum context/turn/repair budgets; rule-profile schema; branch projection strategy; archive encryption and recovery; native model import trust boundaries; strict offline packaging; and release distribution. Use `adr/0000-template.md`; the initial proposals are in `adr/0001-initial-direction.md`.
