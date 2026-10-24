# Play2.5 staged narrator evidence proposal — 2026-10-23

Refs #12 M08.03, #11 M07.01 consumer prerequisite, #29 D07.03/.04/.05.
Status: **source-only proposal, not implementation or qualification**. Root
owns every existing production path and decides implementation allocations.
Agent resource_metrics_review owns ONLY this new document on
`design/m08-play25-staging` / `source-play25-staging`, from exact
`70021708d5ecfb09fa6eddac69075b6ede35bf54`, compared with accepted main
`cf9332718cc5ffd98c5a4ab8fa0295205d5c9a10`. Claims: #12 6377634886,
#11 6377635062, #29 6377635253. No production/test change is authorized here.

This refines the accepted [consumer contract](M08_CONSUMER_IMPLEMENTATION_CONTRACT_2026-10-23.md),
Core contract03e25f26, actual Query2/compiler2 packets and the unchanged D07
comparison protocol. Compiler2's actual return is `PolicyCompilation`, not the
earlier contract sketch's `MemoryCompilation`. Root's combined Store/schema5
and platform qualification remain separate; their source is not accepted merely
because this document inspects it.

## Actual bound source and the missing seam

`play.rs` remains fresh `locallore-play-v2.4`, grounded-prose-v2.1, compiler1.
It prechecks the finite action through `engine.preview`, compiles the Director
context, parses the actual provider commands, previews again, sends approved
outcomes to a Structured narrator and calls `commit_play`. There is no separate
Character generation in this local Play path. Legacy `inference::Input::Director`
holds `CharacterContext`1; its fake/typed path is a different preserved API.

`Engine::preview` refuses Domain2 FreeText before resolving commands;
`commit_play_history` refuses every Domain2 generated record. Removing those
guards alone would be unsafe. `append_play` already uses the same real resolver
on staged state, creates private per-discovery observation bindings, validates
record/projection/history budgets and appends one canonical record. Core's
`actor_event_v2` resolves the observed value from that event's actual binding;
it does not substitute the latest effective fact. These are the existing
mechanisms the proposed seam must reuse.

`render` and the current narrator see a Discovered actor/fact effect but not the
newly observed proposition. Reading `seed.facts` would miss an author correction;
reading `effective_fact` in Play would expose privileged truth without proving
this action observed it. `character_context_v2` is also too broad for narration:
it includes earlier known facts/history. The missing product is a bounded,
Core-produced **this-turn** observed-value view, not another context compiler.

## Proposed exact native Core API

Names below are proposed, not present functions. Keep existing Receipt, Effect,
Request, Proposal and canonical wrapper wire encodings unchanged.

```rust
// Defined beside Engine's private staging machinery. No Deserialize, Serialize,
// Clone, public fields, Engine accessor, native handle registry or wire token.
pub struct StagedPlayV25 { /* private basis, approved receipt, safe evidence */ }
impl StagedPlayV25 {
    pub fn approved(&self) -> &Receipt;
    pub fn narrator_evidence(&self) -> &NarratorEvidenceV22;
}
impl Engine {
    pub fn stage_play_v25(
        &self, request: &Request, proposal: &Proposal,
        cancel: &dyn Fn() -> bool,
    ) -> Result<StagedPlayV25, Error>;
    pub fn commit_staged_play_v25(
        &mut self, staged: StagedPlayV25, record: &PlayRecord,
        cancel: &dyn Fn() -> bool,
    ) -> Result<Receipt, Error>;
}

// Serialize-only, bounded, private fields with read-only getters. Construction
// stays in Core. These values are evidence, never authority accepted as input.
pub struct NarratorEvidenceV22 {
    // version: 2, events: Vec<NarratorEventV22>,
    // observations: Vec<NarratorObservationV22>, mechanical_summary: String
}
pub struct NarratorEventV22 { /* event_id: u64, outcome: NarratorOutcomeV22 */ }
pub enum NarratorOutcomeV22 {
    Resolved { effect: Effect }, // Core NEVER puts Effect::Said here
    StatementDelivered,        // no utterance/audience/request text
}
pub struct NarratorObservationV22 {
    // event_id: u64, actor: String, fact: String, proposition: String
}
```

Safe output getters may expose scalar/borrowed safe fields; the exact internal
storage arrangement does not grant extra authority. `approved()` is a trusted
native/capture receipt view, **not** narrator input: it retains the ordinary
request/proposal and raw spoken events. Only `narrator_evidence()` is serialized
into the narrator request. The existing ApprovedPlan capture may still record
that actual ordinary receipt under its separate private consent/caps; never
serialize the private canonical wrapper/token to a provider or capture.

`stage_play_v25` must:

1. Validate request/version/scope/current head/player, exact proposal identity,
   actual finite intent/agency guard and command/effect limits through ONE
   shared private preview/resolution implementation. Keep legacy public
   preview's Domain2 refusal. A native new entry may use that implementation;
   changing a public boolean to bypass version checks is not the interface.
2. Capture the full opaque accepted-history basis (seed, scope/lineage and all
   canonical records), generate the approved Receipt with the actual resolver,
   and append it through actual `append_play` on a bounded private Engine clone.
   That generates real sparse bindings and checks the candidate's full budgets.
3. Read only the staged suffix `(old_head, new_head]` through actual Core V2
   eligible-event construction for the selected player. A discovery evidence
   row must correspond one-to-one to an approved `Discovered { actor: player,
   fact }`, with matching scoped sequence, fact, observer and event-specific
   observed proposition from that candidate. Never diff whole fact maps, use a
   latest-fact lookup, fabricate observation provenance or attach old knowledge.
4. Build sanitized event outcomes, source-correct observation values and the
   same mechanical rendered summary. `Said` becomes StatementDelivered and
   render's delivery-only summary; no raw utterance or original input is copied.
   An action with no discoveries has an empty observation list, even when the
   player already knows many secrets. Private author records are not events.
5. Drop the temporary Engine clone before provider work. Retain only full basis,
   approved Receipt and bounded safe evidence. Existing max commands/text/
   receipt/history/projection limits and panic-safe cancellation apply before,
   during and after construction. No native I/O, cache write, canonical append
   or persisted Running state occurs on the selected source Engine.

`commit_staged_play_v25` consumes the capability and first honors actual recorded
request retry semantics. For a fresh turn it checks cancellation and the exact
full basis, regenerates the candidate/evidence through the SAME Core path,
compares complete approved results, validates the2.5 record against that safe
evidence and only then installs the actual appended canonical state. Matching
projection/head alone is insufficient. Same-head replacement/author-binding
divergence is Stale; a different request sharing a key is RetryMismatch. No
caller-supplied events/evidence or opaque-token deserialization is admitted.
Cancellation before installation means no append; a late cancellation after a
successful append cannot falsely report rollback. Dropping a token does nothing.

This adds bounded staging/revalidation cost (including a temporary Engine clone
and retained ordinary Receipt/evidence), not a cache-performance improvement.
Peak allocations and serialization work must obey existing caps; document any
additional exact evidence byte bound before implementation. A checksum never
authenticates a supplied discovery value.

## Proposed current Play entry and record dispatch

```rust
pub use crate::context_compiler::ContextPolicy as PlayContextPolicy;
pub struct PlayConstructionInput<'a> {
    pub coverage: &'a crate::memory_coverage::CoverageRead,
    pub policy: PlayContextPolicy,
}
pub fn execute_traced_with_policy(
    engine: &mut Engine, request: &Request,
    provider: &mut (impl InferenceProvider + ?Sized), cancel: &Cancellation,
    profile: &PlayProfile, sink: Option<&mut dyn TraceSink>,
    input: PlayConstructionInput<'_>,
) -> Result<Receipt, Error>;
// Add to PlayRecord with default + skip_serializing_if Option::is_none:
// pub context_policy: Option<PlayContextPolicy>
```

Existing execute/trace/Option-proof/CoverageRead APIs delegate to current2.5 with
Relevant default. The optional-proof entry makes no source-fallback assertion;
CoverageRead keeps its actual closed source-fallback reason separately. The new
entry executes BOTH enum arms by calling actual `compile_policy_cancelled` with
CompileRequest.version2, same selected canonical snapshot/player, role/profile/
budget/query/reference rules. No evaluator-selected expected command, alternate
compiler, availability flag, inspector lens or new model/worker is introduced.

| Recorded prompt | Narrator policy | Context metadata | Construction policy | Admission |
|---|---|---|---|---|
| 2.1/2.2/2.3 | grounded-prose-v2.1 | None | None | Historical replay/retry only, exact prior bytes |
| 2.4 | grounded-prose-v2.1 | existing version1/compiler1 | None | Historical replay/retry only, exact prior bytes |
| 2.5 | grounded-prose-v2.2 | version2/compiler2, package2 | Some exact closed enum | Fresh/current + strict recorded replay |

Dispatch is on the full tuple, not one current constant followed by a loose
historical exception. Unknown/mismatched versions, missing2.5 policy, present
old policy, invalid context binding or future enum labels fail closed. Old2.4
must not silently invoke compiler2 or new narrator checks when restoring bytes.
Domain2 cannot create a fresh2.4 receipt; inherited historical2.1-.4 records are
revalidated at their original pre-author states/scopes, not relabeled Domain2.

Persisted context/policy/count metadata is provenance, not proof or a permission
grant. Existing coverage fields stay finite/closed;2.4 validation stays exact.
For2.5, source-fallback is independent of the compiler fallback: Domain2 and
Recent currently yield real Raw/Unsupported with zero cache contribution,
including when the native source itself reports Unsupported. Do not retain
the2.4-specific requirement that every supplied source reason implies compiler
Missing. Domain1 Relevant may use an actual rechecked proof. Both real policies
share the SAME mandatory authority; optional history never enters narration.

The finite action guard still runs before any provider. Its resolved command
may be prechecked by staging then discarded before generation; the model must
still return its own bytes under the existing constrained schema and actual
parse/agency/mechanical validation. Stage again on that actual proposal. There
is no automatic expected-proposal substitution. Dialogue remains literal.
Keep profile<=4096 context,<=350 tokens/role,<=120s,<=1 repair and existing
deadline/output/poll accounting. No extra role or repair is authorized here.

## Narrator2.2, validation and replay lifecycle

Only this-turn safe evidence enters the2.2 Structured narrator request/schema;
no ContextPackage2, optional transcript, known-but-not-newly-observed secret,
CharacterContext, effective world fact, TruthSource, ObservationBinding,
author reason, inspection grant or raw player speech. Scope/revision/request
envelope remains actual. Event IDs exactly match approved events. Sanitized
observation rows add grounded values, never knowledge for an NPC or an effect.

Validation consumes the same Core safe evidence. Existing conservative prose
and hidden-actor checks remain; allow supported discovery propositions only
when grounded in the corresponding actual observation. Do not broaden global
seed/hidden-name allowlists from player knowledge or compiler candidates.
An unsupported/malformed narrator result falls back to exact Core mechanical
summary with actual event IDs and recorded fallback=true. New evidence may
justify a grounded discovery sentence, but no semantic completeness/quality
guarantee follows from phrase checks. Values containing quotes/escaped text can
legitimately trigger conservative fallback; do not weaken controls to improve
scores. Prose never changes the typed candidate.

Fresh generation lifecycle is preflight/guard → actual compiler2 → Director/
optional bounded repair → Core opaque stage → narrator2.2 → validation/fallback
→ consumed-token revalidation → ordinary Receipt candidate. Host/Store still
revalidate/commit against the actual full source boundary; the token is not a
durable transaction, session identity or replacement for those fences.

History-only replay regenerates stage/evidence from the original canonical
prefix and validates the recorded tuple/prose/fallback without a provider.
`commit_prepared` current2.5 must re-stage, not accept serialized evidence;
the history-only path handles old versions unchanged. Domain2 wrapper restore
must compare the fully regenerated record INCLUDING private bindings against
persisted canonical JSON. Existing canonical records remain the sole source
for revision, completed boundaries, fork/restore/caps and accepted-basis hashes.
Opaque tokens/evidence are not persisted; ordinary Receipt bytes do not gain
private bindings or observation values outside explicitly versioned provenance.

## Current consumer closure before exposure

| Actual path | Required Root-owned closure |
|---|---|
| Engine preview/commit_play/commit_prepared/commit_recorded; author_correction append/restore | Shared new staging/commit dispatch and exact full-wrapper replay; preserve old Domain1 entries/refusals/bytes. No bypass of author key collisions or full-ledger budgets. |
| play.rs/intent_guard.rs | Current2.5 typed policy entry, required metadata tuple, real compiler2 call, actual staged evidence and distinct narrator2.2 validator; zero-role guard/cancel/mandatory failures. |
| inference.rs typed Director/CharacterContext1/Narrator | Keep legacy Domain2 Version before provider; do not silently replace public Input::Director payload. Current Structured roles remain Director and narrator, not a fabricated Character pipeline. |
| context_compiler(.rs,/policy.rs,/verified.rs), inspection_query2 | Already implemented separate current safe policies/rows. Integrate actual current entry; do not change compiler1/query1 historical semantics or treat requested policy as raw-vs-verified coverage. |
| Host prepare/Work/generation_snapshot/finish/open/source ports | Current Work calls2.4 coverage API. Forward typed current policy with the coherent Engine/CoverageRead; preserve same-source/extension passive Open, non-extension owner retirement, full accepted-source admission/status/commit/cleanup, late worker and trace-owner fencing. |
| Host PlaySnapshot/Inspect/query/capabilities | Legacy PlaySnapshot unwrap remains a concrete Domain2 panic risk; explicit closed refusal or safe versioned DTO before reachability. Omniscient state+ordinary receipts is not complete canonical history. Capability labels/actual schemas must agree. |
| turn_trace.rs/turn_capture.rs/inspection.rs | Capture only actual safe ContextPackage2 and actual role envelopes; ApprovedPlan ordinary Receipt remains private-consent bounded. No token/private wrapper/newly reconstructed historical capture. Current export1 closes Domain2; export2/decoder support is separate. |
| memory_coverage/jobs/derived_memory/context snapshot | Domain2 old method2 proof/jobs Unsupported before source/hash/cache work; coherent Engine+RawFallback Unsupported, no fake verified proof. Store source/cancellation invariants remain authoritative. |
| Store schema5 turns/author/archive/retention/workspace | Root's mixed-history loader/current commit and native author closure require actual qualification; generated2.5 restore must use new history validator. Old archives1/2 stay immutable, archive3 separate. No schema/public-author admission follows from this proposal. |
| eval lib/local_lane/local_recording/desktop_api/protocol | Source bindings, version/policy/coverage reports and actual envelopes need current explicit support. Existing reports remain immutable/viewable, stale resume refused; no changed fixtures/expected outcomes/budgets or automatic2.5 quality claim. |
| Desktop/Android native/gateways/schema/decoder/UI | Database5 admission is independent of Domain2/Play2.5 support. Close unsupported snapshots/queries/exports and normal hooks, then rebuild/test actual ABI/schema/decoders; no author/current capability until all routes are safe. |
| Examples/schema generation/tests/fixtures | Inventory current-label assertions/literals, frozen2.4 original-source golden capture before bump, preserve existing2.1-.3 golden files. Future-version negative fixtures move explicitly with retained RED evidence, never rewrite history. |

## Test source/oracles to freeze before production

1. **Original bytes:** freeze actual accepted2.4 compact receipt/package hashes
   before bump; unchanged2.1/.2/.3 goldens and actual2.4 full/compact bytes replay,
   restore/fork/prebirth and retry with zero provider calls. Current2.5 is a new
   tuple, not a mutated old fixture. Strict closed version/policy/context matrix.
2. **Core stage:** real Domain1/2 Wait/Give/Dialogue/Discover stages reproduce
   exact approved events, mutate no source, and match actual appended Core V2
   event/observed-value views. A→B Wait discloses neither B nor old player
   secrets; eligible Discover produces exactly B for player, not NPC. Reconfirm
   same value/A→B→A preserve exact event-specific observations without source
   oracle. Multiple discoveries keep event-specific values/order, no map diff.
3. **Capabilities/source:** no Serde construction of token/evidence; wrong
   scope/head/request/proposal/key, same-head different history/seed/author
   bindings, changed head after stage and wrong child/sibling/parent-future
   reject without mutation. Recorded exact retry returns accepted receipt with
   zero providers even with changed current profile/policy/proof.
4. **Actual envelopes:** record real synthetic provider requests, not compiler
   assertions alone. Both policies share mandatory evidence; optional rows may
   differ only in Director. Narrator has ONLY actual sanitized outcomes/new
   observation values, no raw speech/proposal/history/secret/source/reason.
   NPC event-only/query2 eligibility remains separate; no new NPC call.
5. **Narration/replay:** valid grounded discovery prose, forged observation
   text/id/actor/fact, unrelated old knowledge, quotes/escaped text, wrong event
   IDs/speaker, invention/hidden actors and malformed output produce exact
   validation/fallback behavior. Edited persisted private binding/record/tuple
   is CorruptHistory; replay uses no model and cannot grant knowledge.
6. **Limits/cancel:** mandatory fit and unsupported intent refuse before role0;
   original finite guard/schema never substitutes model output. Cancel/panic
   before/during/after stage, during narrator and before install leaves source
   unchanged; retry succeeds. Drop token does nothing; postcommit cancel never
   lies about rollback. Huge escaped observed values respect request/evidence/
   context/receipt/history bounds; no truncation or relaxed existing budget.
7. **Integration closure:** actual Host/Store current prepare+commit/reopen,
   stale replacement/lost ack/full/Busy/late worker and passive Open preserve
   source/trace. Query1/compiler1/legacy typed inference/export/PlaySnapshot
   refuse Domain2 before panic/content/provider/mutation. New2.5 decoder/schema
   and normal hook exclusion qualify separately on actual platforms.

These are proposed test families, not frozen executable tests or passed results.
No new input-quality/model-score tuning, changed eval expected outcomes, new
provider/worker/transport/assets or memory-performance assertion is included.

## Actual work and next allocation

Only repository/issue/Git/source reads, this one new Markdown file and
`git diff --check`/owned-path/clean-tree checks ran. Existing heavy tests and
platform evidence belong to their attributed authors/coordinator, not this
proposal. No Cargo/Node/Gradle, provider/model, app/native runtime, device/ADB/
CUA/desktop, transport/download, settings/protected-resource/PR/merge action.
Git2.33.0.windows.2 and PowerShell7.6.5 are source-tool versions only.

Root must approve exact signatures/evidence bound and allocate existing Core/
Play/version/consumer paths before any implementation. Then capture2.4 golden
and freeze meaningful actual test source before editing production. Until the
complete privacy/version closure and actual qualification, Domain2 generated
Play and the comparison runner remain unavailable; no acceptance is implied.
