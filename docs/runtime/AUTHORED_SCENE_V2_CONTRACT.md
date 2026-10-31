# Authored scene V2 construction

Refs #9 (M05.03), #14 (M10.04 supporting tests). B35 contract, not qualification.
Base: PR #300 at `efaab06499a8e4a4a9324c0b464400ae0d529090`, unmerged.

## Authority and compatibility

Add authored-world narration through trusted native selection. Preserve every
V1 recipe, prompt, frame encoding, default and initial_world refusal. New V2
requires a validated authored seed. No new dependency, canonical effect, wire
selector, provider role/schema, Kotlin rule or runtime capability is introduced.
The provider remains untrusted. All staging is transient; only validated commit
can append. Restore reconstructs the exact recipe and revalidates full history.

New module `play::authored_scene_narration` exports:

- `AuthoredSceneRecipeV2::{Memory(PlayContextPolicy), LiteralV1}` (native-only).
- `AuthoredScenePlayConstructionInput<'a> { pub recipe, pub coverage:
  Option<&'a CoverageRead> }`.
- `AUTHORED_SCENE_PROMPT_VERSION_V2 = "locallore-play-v2.11-authored-scene-frame-v2"`.
- `LITERAL_AUTHORED_SCENE_PROMPT_VERSION_V2 =
  "locallore-play-v2.12-literal-director-v1-authored-scene-frame-v2"`.
- `AUTHORED_SCENE_NARRATION_POLICY_V2 =
  "grounded-prose-v2.8-authored-scene-frame-v2"`.
- `render_authored_scene_narrator_v2(&BoundAuthoredScenePlayV2, &PlayProfile,
  &dyn Fn()->bool) -> Result<RenderedSceneNarratorV1, Error>`. Root supplies a
  crate-private constructor for the existing immutable rendered prompt/schema.

Public `play::execute_traced_with_authored_scene_recipe_v2` has the same first
six parameters as `execute_traced_with_scene_recipe_v1`, followed by the V2 input.
Memory uses the existing observer-scoped compiler and coverage validation;
literal retains its existing Domain1 restriction. An authored seed alone is
Domain1; only an actual accepted correction yields Domain2.

New engine module `engine::staged_authored_scene_play` exports non-Clone,
non-Deserialize/non-Serialize capabilities `StagedAuthoredScenePlayV2` and
`BoundAuthoredScenePlayV2`. Engine methods:

```text
stage_authored_scene_play_v2(&self, &Request, &Proposal, &dyn Fn()->bool)
    -> Result<StagedAuthoredScenePlayV2, Error>
bind_authored_scene_play_v2(&self, StagedAuthoredScenePlayV2,
    AuthoredSceneRecipeV2, &dyn Fn()->bool) -> Result<BoundAuthoredScenePlayV2, Error>
commit_authored_scene_play_v2(&mut self, BoundAuthoredScenePlayV2,
    &PlayRecord, &dyn Fn()->bool) -> Result<Receipt, Error>
```

Both capabilities expose `approved()`, `narrator_evidence()`, `scene_frame()`;
the bound capability exposes `recipe()`. Its presentation and provenance getters
are crate-private. Root owns restore dispatch in engine.rs and pipeline wiring.

## Typed location source

`NarratorAuthoredSceneFrameV2` serializes only `version:2`, scope,
before_revision, after_revision, player, location (actual post-candidate opaque
location ID), and optional `location_label`. These fields have read-only getters.
Absent `location_label` serializes as explicit null; its getter returns
`Option<&NarratorLocationLabelV1>`. `NarratorLocationLabelV1` serializes only
`location_id`, `name`, `fact_id`, and
the existing typed `ObservationSource` observation provenance. It has read-only
getters; neither type has a Deserialize constructor.

Derive IDs/name from validated typed `initial_world.accepted.locations` and its
existing materialization recipe. Never parse a generated fact proposition for
a name. Only select the actual post-candidate location. Its exact materialized
seed fact must be in that candidate Player's `observed_facts` at the exact
scope/head, with the exact original materialized value. Compare with the original
seed value, not effective hidden truth: an unseen correction must not silently
change remembered labels. If the player later observes a corrected free-text
value that has no typed label mapping, omit the label rather than parse it.

Do not serialize in the added frame a description, remote location, raw origin/generation/config,
NPC sheet, belief, hidden corrected truth, proposal, ordinary receipt, director
package or arbitrary observed fact. Label provenance is a reference, not a new
observation or discovery. Move alone does not grant a destination label.
The existing staged narrator evidence still includes exact propositions of
discoveries actually accepted in this turn, including a description or corrected
free-text value. That explicit observation is not a hidden-origin leak. It must
not become a typed label through prose parsing. Unrelated hidden data stays out.
Inherited observation provenance may refer to an eligible ancestor scope; do not
force it to equal a child frame's scope. Validate origins against seed.scope.

Staging reuses stage_play_v25 and actual candidate append on a transient clone.
Binding compares complete accepted-history basis and regenerated approved plan,
evidence and frame. Commit consumes and regenerates the capability, validates
record/prose/presentation, appends on a clone, polls cancel, then installs once.
Exact recorded retry wins first, without inference or another append.

## Record and validation seam

Keep PlayRecord fields unchanged. Its existing `scene` shape records
`SceneNarrationRecordV1 { version:2, frame_sha256 }` for this explicitly versioned
construction; V1 continues version1. Hash exact serialized V2 frame bytes.
V2 admits only its exact prompt/policy/context/presentation/provenance. Wire
record metadata cannot mint a staged capability or select history privileges.

Root provides private parent-play function
`validate_staged_record_contents_with_location_label(engine, approved, evidence,
record, Option<&str>) -> Result<(),Error>`. It retains the strict whole-word,
hidden-ID, effect, observation, event-ID, fallback and presentation checks. Only
complete occurrences of the eligible current label extend visible-name spans;
fragments/continuations cannot become independent word authority. Existing
sensitive phrase guards may conservatively fall back; this is not entailment.
No old caller passes an extra label. Root also exposes crate-private
`scene_narration::renderer::validate_generated_for_player(approved, player, text)
-> Result<(), NarrationValidationFailureV1>`
with the existing scene first-person/unapproved-movement checks unchanged.
The rendered prompt/schema constructor is crate-private
`RenderedSceneNarratorV1::from_parts(String, serde_json::Value) -> Self`.

New Host native selectors: `MemoryAuthoredSceneV2(PlayContextPolicy)` and
`PlayerLiteralAuthoredSceneV2`. Existing defaults/wire/Android selection are
unchanged. Durable host execution must use existing storage transactions,
stale/cancel fencing, provider ownership and exact request identity.

## Acceptance and independent ownership

Root owns existing files and integration. Core implementation agent owns ONLY
the two new module files. Independent test author owns ONLY new
`crates/locallore/tests/authored_scene_v2.rs` and
`crates/locallore-workspace/tests/authored_scene_v2.rs`. Freeze tests before new
behavior. Missing API compilation is setup, not behavioral RED. Reviewer is
read-only. All work uses separate D: worktrees; no agent runs project tests
outside the coordinator's bounded execution admission.

Required cases include successful fake-provider authored narration, typed label
only, private description/remote/NPC/belief/reason canaries, move before discovery,
actual correction and rediscovery, sibling/scope/head/history-basis mismatches,
full-label/fragment/Unicode boundaries, cancellation and stale commit, exact
retry, tamper refusal and no-inference durable reopen/restore. Old V1 restrictions
and recorded policy compatibility remain regression gates. Host/fake evidence
does not qualify current Android UI, a model, phone, ARM64, privacy or quality.
