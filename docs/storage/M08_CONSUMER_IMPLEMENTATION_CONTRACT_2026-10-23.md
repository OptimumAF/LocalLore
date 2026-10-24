# M08 consumer implementation contract — 2026-10-23

Refs #12 M08.03, #11 M07.01/.03/.04 prerequisite, #29 D07.03/.04/.05.
Status: source-only implementation contract, not an implemented consumer or
executed policy comparison. Coordinator-approved scope: this ONE NEW document
in `design/m08-consumer-contract` / `source-m08-consumer-contract` from
`75fe968e802cc47558c4f2c9aeebccf1f7b445b9`. Claims: #12 6376919548,
#11 6376919705, #29 6376919867. Root owns all production, schemas and integration.
The completed `source-author-core` branch is preserved unchanged.

Bindings: Core contract `03e25f26d85d151853dd26f45ea62602940b6362`; candidate
Core production `5476e36` plus closed restore fix `9a9a616`; courier protocol
packet `c67d278b14b3d55e844c7a84a088a784ae9b17ae`, especially
`docs/eval/D07_MEMORY_COMPARISON_PROTOCOL_2026-10-23.md`. At this baseline the
candidate has pure author/actor-V2 APIs but no author native/session route.
Old Play is 2.4/compiler 1/query 1. The protocol's two policy execution gates
remain Unsupported; this document does not change that fact.

## Closed native surfaces and version dispatch

Keep the existing `CompileRequest`, ContextPackage outer shape, query request
and legacy entry points. Do not add required fields to old compile literals or
reinterpret a global constant. Allocate an explicit compiler-2 entry:

```rust
// Native requested construction, not an inspection grant or availability flag.
pub enum ContextPolicy {
    StateRecentTranscriptV1,
    StateRelevantMemoryV1,
}
pub fn compile_policy_cancelled(
    engine: &Engine,
    request: &CompileRequest, // version == 2
    policy: ContextPolicy,
    proof: Option<&VerifiedCoverage>,
    cancel: &dyn Fn() -> bool,
) -> Result<MemoryCompilation, CompileError>;

// play module uses this same type, not a second policy enum.
pub use crate::context_compiler::ContextPolicy as PlayContextPolicy;
```

The closed serialized labels are `state_recent_transcript_v1` and
`state_relevant_memory_v1`. Keep compiler-1 `compile`, `compile_cancelled`,
`compile_verified_cancelled` admission/bytes for Domain 1; Domain 2 must receive
a fixed version/unsupported refusal before legacy rows or proof collection.
Add a separate compiler-2 constant, not a replacement of the legacy constant.
Both entries share one internal candidate, mandatory, measurement and packing
pipeline with explicit version/policy dispatch. No alternate compiler,
evaluator, retriever, ledger, caller boolean or environment enablement switch.

Query dispatch accepts exact query version 1 or 2, preserves query-1 Domain-1
behavior/bytes/cursors, and rejects Domain 2 at the version-1 boundary before
lens construction/search/counts. Query-2 result version and cursor namespace
are 2; a version-1 cursor cannot be accepted under version 2. Unknown versions
and unsupported construction return closed errors, never a successful empty
result pretending the feature ran. Existing Core `Error::Version` remains the
legacy refusal; there is no invented global `Error::Unsupported`.

Compiler-2/query-2 actor knowledge comes from actual `observed_facts` and
`character_context_v2`, with event history from `visit_actor_observations_v2`
and `actor_receipts_v2`. Use a new `KnownAsObserved` origin, kind and mandatory
reason. Never label a remembered proposition `CanonicalTruth` or convert it
to a subjective belief. Query-2 on Domain 1 also uses those safe typed known
values; query-1 and compiler-1 labels remain exact. Existing Row containers may
gain closed V2-only variants; old enum arms must serialize unchanged.
Observation provenance needs the actual scoped observation reference, e.g.
`Source::ObservedEvent { original_scope: Scope, sequence: u64 }`; do not mistake
that for the private truth source. Existing `Source::Event(u64)` bytes stay
unchanged. Seed observation provenance identifies the actual seed/known value,
not the current private author override.

## Shared mandatory construction, two optional policies

Both policies validate the SAME canonical Engine/scope/head/observer, action
references and aliases, role/profile/budget, then build the SAME mandatory
rules, current state, observed known values, current beliefs, relationships,
open commitments, supporting evidence and recent-event floor. Preserve the
current mandatory `Referenced`/alias admission too; document it as common
action evidence, not an optional retrieval advantage. A tiny mandatory budget
fails before any provider call. Inspector/omniscient privileges are never
arguments to this generation port.

- **RelevantMemory:** the existing exact/lexical optional selector, with the
  actual eligible raw or rechecked verified representation. It does not mean
  "verified cache enabled" and is not a raw-versus-verified ablation.
- **RecentTranscript:** optional selection ignores lexical scores and packs
  newest eligible whole ordinary-turn units. A player unit contains actual
  original input when present, actual displayed narration, original scope and
  all supporting event references, only when every supporting event passes
  the existing owning-player eligibility. A typed action lacking original
  prose has no invented input. An NPC unit contains only its eligible actor-V2
  events grouped by ordinary receipt: no raw player Request, Proposal or
  narration. Author records contribute no unit. Skip an entire optional unit
  overlapping already selected event-floor/supporting evidence; do not split
  it or duplicate its event references. Rank by latest event revision and a
  stable original-scope/turn tie-break, then emit selected material in stable
  chronological order. Charge the whole unit once against the existing
  optional-record/serialized-byte/token-reserve limits.

The internal player transcript-unit constructor is private to the shared
inspection/compiler eligibility implementation; it accepts no grant flag or
caller-supplied transcript. A V2-only typed Row unit can carry its safe payload
through the SAME ContextPackage packing mechanism. NPC units remain event-only.
No private author/binding wrapper is a context row. Aliases and the common
mandatory phase cannot be dropped just to make the Recent control fit.

Recent remains `UnsupportedPolicy` at its compiler boundary until this actual
whole-unit seam exists. Implementing an enum or report field does not make it
available. Only the actual same-runner policy call can qualify a protocol arm.
The courier optional pennant detail is distinct from mandatory promise/state
evidence; do not retune its fixture, expected commands or budgets after failure.
The 24-attempt protocol (21 expected provider turns, 3 guard refusals) remains
separate from the 1,032-event retrieval stress corpus. Literal transcript-only,
causal recall, narrator memory benefit and human quality acceptance are not
established by these mandatory-preserving policies.

## Representation and old derived-memory refusal

On Domain 1, Relevant may use the existing verifier; mandatory overlap/raw-delta
rules remain unchanged. Recent transcript payloads must come from actual
canonical input/narration, not old event-only packets; report actual raw
representation with `Unsupported` for that packet representation. Domain 2
initially uses actual raw actor-V2 rows for BOTH policies. Old method-v2 packet
build/recheck, derived-memory mutation and jobs reject Domain 2 before deriving
a receipts-only source digest, using a cache or moving any cursor. Do not
upgrade old proofs by renaming them.

`CoverageRead::RawFallback(Unsupported)` is the typed coherent snapshot outcome,
not a failed canonical read. Store `context_snapshot` must read the complete
Domain-2 Engine and return that fallback from the SAME read snapshot without
job admission/writes. Native job operations that resolve a valid Domain-2 scope
return existing `MemoryError::Unsupported`; preserve native handle owner/
NotFound checks. Core packet build needs a closed unsupported error/mapping
(the current CoverageError lacks this variant); coverage verification returns
the existing RawFallback Unsupported. Root owns that exact enum integration.

`source_fallback_reason` reports actual native snapshot input; compiler fallback
reports the actual representation construction. Neither implies a cache hit,
knowledge grant, performance savings or authenticated diagnostic counts.
Maintain these as separate fields. Domain-2 compiler Unsupported must not be
silently rewritten as Missing; historical Play-2.4's existing source-fallback
versus compiler-Missing validation remains version-specific and unchanged.

## Fresh Play 2.5 and persisted validation

Fresh default construction is RelevantMemory. Add one narrow native entry,
`execute_traced_with_policy_and_coverage(..., profile, sink,
coverage: &CoverageRead, policy: PlayContextPolicy)`, forwarding the same private
Play inner execution. No JSON policy/author capability is implied by this
native API. Existing fresh wrappers select the actual current default; recorded
retry lookup still precedes generation and returns its original receipt.

Add only optional `context_policy: Option<PlayContextPolicy>` on
PlayContextRecord with serde default and skip-None, so old context encodings
are unchanged. Validation is an explicit closed table, not comparison with
whatever `PROMPT_VERSION`/`COMPILER_VERSION` happens to mean today:

| Recorded prompt | Narration policy | Context record | Admission |
| --- | --- | --- | --- |
| 2.1 / 2.2 / 2.3 | exact historical grounded-prose-v2.1 | absent | history/retry only |
| 2.4 | exact historical grounded-prose-v2.1 | version1/compiler1/policy omitted | history/retry only |
| 2.5 | grounded-prose-v2.2 | version2/compiler2/Some supported actual policy | fresh and strict history |

Require scope/head/actual seed player and finite closed metadata under the
version's original rules. Reject unknown labels, missing required fields,
old-prompt/new-context combinations and unsupported policy claims. Do not
rerun a model or reinterpret old prose on replay. A historical Domain-1 prefix
before authoring retains its original Play-2.1–2.4 behavior; old generated Play
must not be laundered into fresh Domain-2 history. Counts are bounded provenance,
not proof of context content or a basis for admitting gameplay consequences.

Root owns the necessary Engine internal generated-preview/staging/commit
validation port: current Domain-2 preview and generated commit intentionally
return Version. **Its exact helper name/signature is pending Root
implementation**, not delegated by this doc. Required typed output is the
unchanged, revalidated approved Receipt plus actor-safe `ActorEventV2` /
`ObservedFactView` values produced by that SAME staged candidate's accepted
discovery events. It must reuse actual intent/agency/resolve/admission, validate
event scope/sequence/player/fact against the candidate, and never expose
CanonicalRecord/CanonicalPlayV2/private ObservationBinding/TruthSource as a
provider value. There is no direct fact-value lookup fabricated in Play.

Fresh grounded-prose-v2.2 narrator input contains ONLY approved outcomes and
those sanitized observations actually produced this turn. No optional compiler
history, known-but-not-newly-observed player secret, inspection view, private
world truth/reason/binding enters that input. A→B does not disclose B during
Wait; an eligible actual Discover may disclose its newly observed B. Original
input speech is still delivered literally and is not established truth. Old
grounded-prose-v2.1 replay checks remain untouched. If the trusted staged
observation output is unavailable, generation stays unsupported; do not infer
the missing value/provenance or claim new narration support. Conservative prose
validation and real semantic-quality limitations remain explicit.

## Complete consumer closure inventory at the bound source

These are required Root-owned implementation/verification allocations, not
permission to edit them. Guard order must be before content extraction, hashing,
search/count, provider dispatch or cache mutation.

| Actual consumer | Current source observation; required route before exposure |
| --- | --- |
| `engine.rs`, `author_correction.rs` | Actual single canonical records authority and safe actor-V2 APIs exist; generated preview/commit currently Version. Root adds only narrow validated current staging; canonical basis/boundaries/counts/replay remain records-based. |
| `inspection_query.rs` Lens/collect/knowledge/state/History/TurnDiff/query | Actor lens currently maps legacy Version to UnknownObserver; omniscient lens can still use receipts and seed truth. TurnDiff uses last ordinary receipt. Add early query1 Domain2 refusal; query2 uses safe values/events and canonical completed boundaries. Actor author-only interval can yield zero changes at an advanced head. Query2 omniscient requires grant and extracts effective proposition only, never serializes whole EffectiveFactView/private source/reason. |
| `context_compiler.rs`, `context_compiler/verified.rs` | Current candidate port calls query1/borrowed legacy visitor. Compiler1 rejects Domain2 explicitly; compiler2 uses V2 port/common mandatory phase and actual selected optional policy. Existing caches only in supported Domain1 Relevant path. |
| `play.rs`, `intent_guard.rs` | Explicit version table, typed policy entry, actual staged observed values, unchanged finite action guard/no expected-command substitution. Inspect guard-derived names/knowledge through actual safe input; version2.5 metadata cannot grant authority. |
| `inference.rs` typed provider path | Current `character_context` returns Version before provider on Domain2. Keep explicit zero-role refusal until an independently versioned safe Input::Director route exists; do not replace the old boxed CharacterContext silently. |
| `host.rs` Inspect, PlaySnapshot, InspectionQuery, FreeText/Work/commit/status/history | Omniscient Inspect directly emits state+filtered receipts. PlaySnapshot calls legacy `character_context(...).unwrap()` and would panic for Domain2: concrete source finding, not an executed exploit. Replace with closed Unsupported guard/current V2 DTO before session reachability. Actor Inspect/query/snapshot must use versioned safe DTOs. Work/late cleanup/Open retain complete source identity/owner fences; no authority from filtered receipts or projection alone. |
| `inspection.rs`, Host capture/export port | All existing export1 modes currently hit legacy player context first and error, but need explicit closed Domain2 Unsupported rather than accidental routing. Export2 diagnostics/redacted/full use appropriate safe V2 views and real effective values. No internal author reason/binding enters ordinary inspection export. Canonical private author archive is separate archive3 consent/format, not a renamed inspection bundle. |
| `turn_trace.rs`, `turn_capture.rs`, Host trace configure/read/revoke | Context artifact may serialize only actual safe ContextPackage2. ApprovedPlan remains unchanged safe Receipt, never canonical wrapper. Role artifacts are exact actually observed requests/outputs under existing private owner/consent/epoch/caps, not reconstructed history. Counts follow eligible construction; author-private scans cannot create actor-visible counts. Keep revoke/late-write fences, normal-hook exclusion and honest missing captures. |
| `memory_coverage.rs` build/binding/boundary/verify/recheck | Current boundary/build loops use receipts; add Domain2 Unsupported before source/cache work. No old packet can certify an author interval or changed observed value. Actual canonical boundaries remain a separate safe metadata port. |
| Store `memory_jobs.rs`, `derived_memory.rs`; Host `memory_maintenance.rs`; Workspace adapter | Current jobs source digest includes receipts. Ensure/lookup/prepare/publish/status must not validate Domain2 under that method; native maintenance returns Unsupported. Coherent generation snapshot returns full canonical Engine + RawFallback Unsupported, not a fabricated proof or separate resume. Old cancellation/owner/no-resurrection semantics persist. |
| Store `turns.rs`, `lib.rs`, branch loader/projection; Workspace bound turn ports | Current strict loader expects ordinary Requests/receipts and projection version1. Schema5 must validate record kind first, compare full canonical local records/physical key, version projection2 and preserve source-bound begin/status/commit/cleanup. No author session admission while this remains incomplete. |
| Store `branch_retention.rs`, `playable_archive.rs`, capacity fixtures | Retention receipts hash and archive ordinary-receipt loops omit author history. Use full canonical records/source guards; archive3 includes actual author history and no jobs/caches, old archive1/2 paths exact. Canonical projection bytes alone are not full history identity. |
| `locallore-eval/src/lib.rs`, `local_lane.rs`, `local_lane/desktop_api.rs`, `local_recording.rs`, comparison protocol | Existing replay/receipt hashes and desktop evidence query.version1 need explicit historical route; new current runner binds actual policy/compiler/source and full history. Original reports stay viewable/immutable, source mismatch refuses resume. Comparison gates only execute actual supported policies, with cumulative reservations/unknown charges and no substituted expected commands. |
| `locallore-android/src/lib.rs`, `workspace.rs`, `archive.rs` | Legacy registry snapshot unwraps character contexts and caps receipts length; keep Domain2 unavailable/closed until current actor2 DTO/count routing exists. Durable gateway uses shared Host; no parallel caller inference/history. JNI/wire/schema/decoder closure is separate actual qualification. |
| Desktop native `export_commands.rs`, `exports.rs`, `capture_exports.rs`, evaluation adapters; UI `model.ts`, `query-model.ts`, capture/evaluation/timeline controllers | Current query decoder is version1. Keep Unsupported until native/schema/decoder agrees on version2; normal app cannot accidentally accept private author wire. Native export tokens/second consent/picker/caps remain authoritative; no renderer bytes become canonical evidence. Fork boundaries come from complete Rust metadata, not ordinary visible receipt last-event. |
| Core `main.rs`, examples and generated schemas; existing fixtures/tests | Demo replay from receipts is Domain1-only presentation, not mixed-history authority. Audit generated schema/version assertions and current frontend/native fixture builders without rewriting historical golden bytes. Existing fixture/scripted lanes remain available and honestly labeled. |

Public safe metadata may report scope/head/completed boundaries, including
private-author intervals, without exposing record kind, affected fact, reason
or truth source. An inspection grant does not alter actor knowledge or generation
input. No additional author/session capability becomes reachable until EACH
current consumer above either supports its explicit V2 route or returns a
closed Unsupported result without panic, partial content or write.

## Frozen implementation oracle families

1. Exact compact golden Play2.1–2.4/context1/Receipt/Effect/projection/basis
   bytes, legacy cursor behavior, root/fork/prebirth restore and retry0roles;
   strict old/new version matrix and fresh old-prompt refusal.
2. Known player/NPC A→B retain observed A and beliefs; real Discover B changes
   only player. A→B→A and uniform same-value reconfirmation have no stale/source
   oracle. Parent future/sibling/foreign/prebirth canaries never enter V2 rows.
3. NPC event-only history before search/count/page; private player input,
   proposal/narration, author reason/truth bindings absent. Player whole-receipt
   positive eligibility and granted omniscient proposition are tested separately.
4. Author-only head has a real completed boundary and no actor events; query2
   TurnDiff uses that interval; query1/old inference/export fail closed and
   PlaySnapshot returns a closed error rather than panicking.
5. Actual provider envelopes/captured selected context and staged approved
   observations are inspected separately. Wait cannot disclose B; accepted
   Discover can supply its actual observed B. Narrator gets no optional history,
   unrelated player secret, author source or inspection privilege. No fabricated
   private historical capture or alternate expected-proposal repair.
6. Same canonical input/action/model/profile/schema/role budgets yields identical
   common mandatory units between policies; optional selection may differ.
   Recent has no lexical ranking and packs newest whole eligible units without
   overlap/partial units; relevant preserves exact/lexical behavior. Zero/huge
   budgets, escaped text, unsupported policy and cancellation stop safely.
7. Old proof/job refuses Domain2 before hash/cache/admission/cursor change;
   missing/malformed/foreign raw source reasons stay distinct from compiler
   Unsupported. Snapshot Engine/proof/fallback is from one transaction. Replay
   of supported current receipt uses no provider and retains actual closed policy.
8. Full-ledger source guard distinguishes equal head/equal sparse projection but
   changed author values; Store loader/archive/retention/bound counters include
   author records. Preserve M07 same-source/extension Open work/trace and
   non-extension owner retirement. Root owns actual transactional Busy/Full,
   cancel/lost-ack/reopen and platform regressions before user exposure.
9. The unchanged courier fixture and long-history stress keep distinct counts,
   failures/skips/fallbacks/charges and evidence. Paired snapshots require exact
   input basis; continuous rollouts stop same-scenario comparison at divergence.
   No model run, human score, superiority, measured token/speed saving or broad
   D07 completion follows from this document.

Actual work for this packet: source/issue/Git/protocol reads, one-file writing,
`git diff --check`, owned-path/clean-tree checks. Git2.33.0.windows.2,
PowerShell7.6.5; no Rust/Node/Gradle build, app/native IPC/render, model/assets,
device/ADB/CUA/desktop, settings/download, protected resource or PR/merge action.
The managed worktree call returned `Not a git repository`; the coordinator's
native Git fallback created only this isolated new branch/worktree. No approval,
execution evidence or availability is fabricated. Next: Root allocates exact
production paths under this contract and freezes meaningful tests before code.
