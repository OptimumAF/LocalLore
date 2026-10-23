# Independent shared local-play review

Refs #9 M05.01–.04 / #25 D04.04–.06. Source review began at coordinator
`89f77d4` in LocalLore-m05-play, including profile fix `04a67d6`, writer-lock proof
`72d3d16` and resource-hash cancellation/metrics fix `6228ea4`. The coordinator
continues integration. This is a bounded review and corrective handoff, not D04
acceptance, a favorable-score gate or verification of later unreviewed changes.

The reviewer changed no existing shared, storage, runtime or application source.
The explicitly assigned follow-up adds only `intent_guard.rs` and its test file
in commit `a991091`; the coordinator owns module/Engine/play/schema/policy wiring.
No build, app/model/device execution or protected process operation ran during
this review. The coordinator's native/workspace results remain its own evidence.

## Concrete findings

1. **Valid wrong actions can establish unintended canon (blocking scene
   acceptance at the reviewed source).** `validate_interpretation(Action)` only
   excludes Say/Promise/CompletePromise. Give-request → Wait, Consume, wrong
   recipient, wrong quantity or an extra valid operation is not bound to the
   original action text. Invented teleport → ordinary reachable Move likewise
   passes if mechanically legal. The coordinator's actual Qwen runs retained
   wrong-action failures; this review did not rerun them. Correct JSON grammar
   order improves model compatibility but cannot supply this missing authority
   check. The original-input preservation and engine mechanics remain useful;
   neither alone proves that the resolved operation represents the player's
   intention.
2. **Probe rejection criteria are too broad to prove mechanical refusal.**
   `play_scene_probe` requires second-potion/invented-power to be rejected and
   unchanged, but accepts Provider, Timeout or Malformed as well as the intended
   inventory/ability refusal. A green aggregate could therefore conceal a broken
   model path for these cases. Require the expected error family and retain the
   emitted typed plan. Unsupported finite input should explicitly expect
   ClarificationRequired; use an independently supported unlearned-ability form
   for the Ability case. The coordinator is correcting this probe; this document
   does not claim execution of that later correction.
3. **Probe has a cancellation window not present in the Host path.** It executes
   a candidate, joins a timed canceller, then commits an Ok receipt without
   rechecking the now-cancelled token or reconciling durable cancellation. If the
   candidate completes before the timer, cancellation fires during join and the
   probe can then commit after cancellation. The ordinary Host rechecks cancel,
   phase, revision and persisted terminal status. The probe must use equivalent
   precommit reconciliation or exercise the actual Host. Keep a deterministic
   ready-before-cancel-before-commit vector; an arbitrarily slow model is not a
   synchronization mechanism.
4. **Wait schema and resolver bounds differ.** Reviewed schema permits ticks up
   to65,535 while Engine permits1–100. This fails closed at resolution, but makes
   constrained output advertise unsupported values. Align schema to the existing
   rule and test both boundaries; do not expand the engine rule to fit a schema.
5. **Prose validation remains a finite quality guard.** For example, a gift-only
   plan plus “Mira's ankle mends” is a proposed regression vector outside the
   current healing phrase list. Off-screen actor name checks can also reject a
   legitimate present actor when two actors share the display name Oren, or match
   an ID inside an unrelated word. These are source-derived test suggestions,
   not newly executed failures. Preserve safe fallback and its explicit marker;
   do not relax hidden-reference checks wholesale to obtain fluent output. Prose
   cannot become a fact, observation or character memory just because it passes
   a small phrase list. Arbitrary semantic fidelity remains unproven.

## Finite correction, with an honest capability label

The coordinator chose an explicit supported-English single-action compiler instead
of claiming that a keyword heuristic validates arbitrary language. New API:

```rust
intent_guard::compile_action(&Engine, text: &str) -> Result<Command, Error>
intent_guard::validate_action(&Engine, &Request, &Proposal) -> Result<(), Error>
```

The compiler recognizes finite give/consume/drink/use/learn/move/go/wait/discover/
believe forms, with optional I/trailing period and documented limited articles.
Examples: “I give my last potion to Mira.”, “use ability blink”, “move to pier”,
“wait for one tide tick”, “discover fact beacon-mark”, “believe claim event 42”.
Actor identifiers are exact and case-sensitive; display names resolve only when
unique among living co-located actors. Item/ability/location/fact identifiers
retain their literal case and unavailable values. Engine still owns Inventory,
Ability, Location, Knowledge and UnknownReference decisions. An unavailable
operation cannot silently become a valid alternative.

Exactly one generated command must equal the compiled expected command. A valid
but different plan returns Agency. Unsupported, quoted, negated, compound or
ambiguous forms return ClarificationRequired; input over the existing text budget
returns TooLarge. There is no model-selected authority, effects engine, automatic
wait, arbitrary tool or direct mutation. Names containing reserved conjunctions or
quoted punctuation require an explicit identifier; this is deliberately limited
input syntax, not universal English understanding.

Precompile before spending generation work, and compare again through Engine
preview/commit/replay. The real model still proposes, and Rust validates exact
binding plus ordinary mechanical consequences. Public UI/docs must call this
constrained supported input, not arbitrary free-text agency or complete NLP.
Dialogue stays an exact-text separate contract; case-folding or silently repairing
the player's speech is not an acceptable fix for model output. Projecting exact
dialogue text into the constrained schema is compatible with retaining that rule.

### Version disposition

The coordinator explicitly identified v2.0 as unmerged prototype/synthetic data
only, with no accepted-main or human-story dependency. Read-only `51ec963` tree
inspection finds no play.rs; its FreeText Host operation is an unsupported
placeholder. There is no contrary accepted-v2 evidence in this review.

The chosen guarded policy/prompt2.1 may therefore reject unsupported prototype
v2.0 records, while retaining prior failed reports, databases and source pins as
historical evidence and using a fresh synthetic workspace. This incompatibility
must be stated rather than described as a successful migration. Do not introduce
a permissive legacy fresh-commit bypass. Accepted v1 receipt bytes, exact
narration comparison and restore checks must remain unchanged. If accepted or
human v2.0 stories are later discovered, revisit this disposition before dropping
their support. Exact recorded retries must still precede new work/profile checks
within whichever supported version owns the record.

## Authority, storage and lifecycle observations

The original bounded FreeText request, scope, revision, kind and text are persisted
before inference, compared in full on retry and retained with the winning receipt.
Director output is parsed uniquely into typed commands; accepted events remain
engine-created. Store reloads/revalidates under its existing Immediate commit
transaction and atomically records accepted effects, original request, prose and
profile/prompt/policy metadata. An exact already committed result wins before new
output or stale-head checks. No write transaction spans generation.

Director input uses player's CharacterContext, own inventory, living co-located
identity names and available routes; the latter is the current explicit scene
presence assumption, not a general hidden-actor visibility system. Narrator sees
approved outcomes/mechanical summary, not omniscient inspector context. Native
provider selection remains outside wire authority; separate roles use fresh
native contexts. Lab inspection does not widen generation knowledge.

Host worker completion first reconciles durable status and refreshes the canonical
head. An external committed/cancelled/stale result wins over late local work.
Transient reads restore Running→Queued rather than stranding a finished worker;
failed terminal writes cannot publish an unpersisted local terminal phase. Unknown
commit acknowledgements use lookup before deciding outcome. These retained fences
are source observations, not newly executed races in this packet.

`72d3d16` replaces a timing-based writer-lock assertion with explicit provider
entry/release signals and a bounded watchdog. `6228ea4` checks cancellation between
resource hashing chunks and before native spawn, and clears stale metrics on new
or invalid operations. Neither improvement changes canonical authority or proves
end-to-end scene quality. The managed worker remains a trusted same-user native
process, not an OS sandbox.

Profile/model/worker hashes and unsigned stored metadata identify configured inputs;
they do not cryptographically authenticate authorship or prove those weights
generated particular words. V2 restore validates supported policy/mechanics/linkage
without inference. Do not describe shape-checked metadata or policy-valid
replacement prose as universally tamper-authenticated.

## Test handoff and limits

Guard commit `a991091` includes seven model-free focused cases: wrong valid gift
substitutions/extra effects; real Engine refusal of unavailable IDs; nearby duplicate
name ambiguity; canonical argument case preservation; all finite operation forms;
negated/quoted/compound/unsupported/oversized requests; and no privileged/dialogue/
thought intent action grant. Formatting and diff checks passed here. Per the
coordinator's low-disk instruction, these tests await execution in its existing
target; this review claims no local passing test count for the new guard.

Source SHA256: `73c7ffc802db877db2926da365ebc93e78450c17024fa76fcd962ae36f80fd6f`.
Test SHA256: `e9b5648022ab7d84c8e4f9df89af5da52b69448995606ec668221473cba61318`.
After wiring, add a shared end-to-end script-provider regression showing unsupported
teleport syntax stops before any provider poll, a valid model-proposed Move for
explicit Give cannot reach narrator/commit, exact Dialogue remains byte-identical,
cancel-after-ready wins before commit, and new guarded receipts reopen/retry with
no duplicate effect. Retain v1 restore vectors and explicit prototype-version
refusal. The native scene probe must then pass intended errors, not generic
transport failures; actual app import/play/cancel/restart/inspection/offline,
sustained performance and quality/phone gates remain separate and unaccepted.
