# Scene narration v1 Core test freeze

Refs #9 M05.03 / #25 D04.04. FIRST SOURCE-ONLY freeze before production work,
on Root's reconciled `fd27d7a66dbca0947213fe10d1d17f60ffbb6f0e`: frozen
PR225 dependency `4de180dd` plus desktop main `c6c21f28`. This is a reviewed
stack base, not a claim that PR225 or this recipe is accepted main. Root owns
production, integration and execution. This allocation owns only this NEW
document and NEW `crates/locallore/tests/scene_narration_recipe_v1.rs`.

## Frozen native APIs and identifiers

Public `play::scene_narration` exports:

- `SceneRecipeV1`, a Copy/Eq native enum: `Memory(PlayContextPolicy)` or
  `LiteralV1`; it is not renderer/model wire authority.
- `ScenePlayConstructionInput<'a>` with public `recipe:SceneRecipeV1` and
  `coverage:Option<&'a CoverageRead>`.
- `SCENE_PROMPT_VERSION_V1 = "locallore-play-v2.9-scene-frame-v1"`;
  `LITERAL_SCENE_PROMPT_VERSION_V1 = "locallore-play-v2.10-literal-director-v1-scene-frame-v1"`;
  `SCENE_NARRATION_POLICY_V1 = "grounded-prose-v2.4-scene-frame-v1"`.
- `render_scene_narrator_v1(&BoundScenePlayV1,&PlayProfile,&dyn Fn()->bool)`
  returning a private-constructor `RenderedSceneNarratorV1` with `prompt()->&str`
  and `schema()->&serde_json::Value`.

`engine::staged_scene_play::BoundScenePlayV1` is a consumed native capability
with private fields, no Clone or Serde, and getters `approved()`,
`narrator_evidence()`, `scene_frame()` and `recipe()->SceneRecipeV1`.
`Engine::bind_scene_play_v1(StagedScenePlayV1,SceneRecipeV1,&dyn Fn()->bool)`
returns it only after complete source/stage validation and exact typed seed
presentation binding. `Engine::commit_scene_play_v1(BoundScenePlayV1,&PlayRecord,
&dyn Fn()->bool)` consumes and regenerates the complete binding before canonical
installation, with final cancellation polling. Preparation alone authorizes no
write. Same scope/head/projection do not substitute for complete history basis.

`play::execute_traced_with_scene_recipe_v1(engine,request,provider,cancel,profile,
sink,input)` uses the actual shared Director/validation/narrator/candidate path.
Memory retains compiler/context provenance and existing Domain2 raw unsupported
fallback; literal retains its immutable transcript source/packing and Domain1
only. Supplied literal coverage is `Error::Rule`, never ignored. Typed
`initial_world` is `Error::Version` before the first Director call and on bind;
no authored Fact scraping or invented location label is permitted.

Exact recorded retry precedes cancellation, profile, construction, coverage,
unsupported-world and head checks. It returns the original receipt, including
an old-policy receipt, with zero provider work.

`PlayRecord` adds public omitted optional `scene:Option<SceneNarrationRecordV1>`.
The closed record in `scene_narration` contains only public `version:u16` and
`frame_sha256:String`; its digest is regenerated provenance, not supplied proof.
Recipe identity comes from the exact prompt/policy/context tuple. All old
validator families reject `scene:Some`, except an existing exact-key recorded
retry wins first. Old 2.1–2.8 defaults, bytes and restore routes remain unchanged.

## Renderer and validation boundary

The renderer is engine-free: the bound capability carries the exact typed seed
presentation. Reuse the existing presentation renderer's semantics through a
typed optional-input extraction; preserve absent/default validation, tone,
Unicode lowercase literal exclusions and seed-binding bytes. Do not interpret
presentation as truth or omit it. Compact `serde_json` frame and sanitized
evidence are embedded without adding raw Receipt, seed facts, NPC sheets,
Director context or private author reason. The frame still has exactly six
fields: version, scope, before_revision, after_revision, player, location.

Actual provider prompt/schema must equal the shared renderer exactly. Keep
`narration_schema(actual accepted events)` and `locallore-narrator-v2` schema ID;
new recipe/version/policy identifies construction. Existing profile limits and
24KiB role input cap remain. No measured narrator token-fit claim is made.

Apply only the previously frozen finite new-policy English first-person and
listed unsupported-travel guards, to generated narration only. Keep structural,
event ID/speaker, observation, ownership and safe mechanical fallback checks.
Exact mechanical fallback still passes seed exclusions; an excluded fallback
refuses rather than bypassing preferences. `Error::Cancelled` must propagate
through render/validation rather than a catch-all `.is_err()` conversion into
fallback or `Error::Narration`. No extra narrator repair call is introduced.
These finite checks do not prove semantic consistency, enjoyment or quality.

## Independent first oracles and limits

The test file uses actual existing Core fixtures and deterministic recording
providers, never a fake scene stage/renderer/commit. Its authored-world refusal
fixture comes from the actual typed `materialize`/`validate_origin` dependency.
Fourteen tests freeze:

1. Existing preparation and real typed authored-origin fixture calibration.
2. Actual forwarded prompt/schema equality to the shared renderer, exact frame
   digest, memory/literal tuples, typed presentation and narrator secret absence.
3. Actual Move destination versus Give/Use nonmovement self location.
4. Corrected Domain2 observed A versus canonical B, raw memory status and literal
   refusal before provider calls.
5. Scene version/hash/omission, event IDs, policy/tuple tampering, wrong bound
   recipe, closed provenance parsing and refusal by old commit admission.
6. Same-head different private history and exact changed presentation refusal.
7. Finite generated first-person/travel fallback, with positive cases elsewhere.
8. Excluded generated prose and excluded exact mechanical fallback.
9. Valid typed authored-world zero-call refusal and bind refusal.
10. Cancelled bind/render/commit and cancellation during the actual narrator call.
11. Cancellation after actual `NarratorOutput` capture: the trusted test sink
    cancels then, while both generated prose and fallback violate exclusions;
    the result must remain `Cancelled`, with source unchanged.
12. Exact retry across later head/cancel/invalid profile/different construction,
    consumed-capability retry and actual Core replay/restore without providers.
13. Literal irrelevant-coverage refusal and old authored receipt retry priority.
14. Existing default 2.5/literal2.6/presentation2.7–2.8 behavior, old prompt bytes,
    and original 2.1–2.4 fixture encodings/replay, including exact 2.4 bytes.

Source/Git/diff review is the author's only verification. All new tests are
**UNCOMPILED/UNRUN**. A baseline missing module/API/field fails compilation; that
is a prerequisite result, not executed behavioral RED. Even existing-API
calibration is unexecuted until the entire test file compiles. Root independently
reviews and runs the frozen tests; preserve source-attributed failures and do
not weaken assertions to match implementation.

This slice does not implement Host construction selection, Store/archive
qualification, exact source-bound capture verification, a new evaluation
protocol, native UI or a model cohort. Actual forwarding equality here does not
authenticate an arbitrary rehashed diagnostic capture. A distinct Eval/Host
gate remains required before model work; existing Protocol3 contracts/reports
stay immutable. Native rendering, physical Android, accessibility and human
quality remain separate. The owner's needs-improvement assessment is unchanged.

## Additive old-validator provenance oracle

After FIRST freeze `5722c9b3`, the author adds one fifteenth source-only oracle
without changing any first-fourteen assertion. Actual original 2.5/2.6/2.7/2.8
records calibrate through their existing production entry points, then receive a
closed, deserializable `scene:Some` value through JSON. Fresh old-policy commit
must refuse without source mutation. Original 2.1–2.4 fixtures similarly
calibrate first, then history restoration must refuse the same injected field.
This tests all existing validator families, rather than relying on a new record
with an already-invalid old tuple. Exact recorded retry remains a separate
positive fast path. The additive oracle is also UNCOMPILED/UNRUN; no execution,
formatter or production changes were performed by its author.
