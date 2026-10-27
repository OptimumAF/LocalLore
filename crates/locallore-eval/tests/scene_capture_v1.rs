// Copyright 2026 LocalLore contributors. SPDX-License-Identifier: Apache-2.0
//! FIRST SOURCE FREEZE: UNCOMPILED/UNRUN at handoff. The gate API is absent.
//! Actual Core Play + TraceRing collector + deterministic recording provider.
//! The reply wrapper is test-owned; this is NOT Host/Store/native UI execution.
//! Mutated diagnostic copies are never attributed to the genuine collector.
use locallore::{
    author_correction::{AuthorCorrectionInputV1, AuthorCorrectionOperationV1},
    contracts::{Command, Error, Intent, PlayInputKind, Receipt, Request, Seed},
    engine::Engine,
    inference::{Cancellation, GenerationRequest, InferenceProvider, Input},
    play::{
        self,
        scene_narration::{ScenePlayConstructionInput, SceneRecipeV1},
        PlayContextPolicy, PlayProfile,
    },
    story_presentation::{StoryPresentationV1, StoryTone},
    turn_capture::DetailStatus,
    turn_trace::{AttemptIdentity, Provenance, Reader, RingSink, Selection, TraceOwner, TraceRing},
};
use locallore_eval::{
    digest,
    scene_capture_v1::{
        check_committed_scene_capture_v1, CheckedSceneCaptureV1, SceneCaptureErrorV1 as GateError,
        SceneCaptureInputV1,
    },
    Capture,
};
use serde::Deserialize;
use serde_json::{json, Value};
use std::{
    sync::{Arc, Mutex},
    task::Poll,
};

const PROSE: &str = "You pause beside the quay.";
const TEXT: &str = "I wait for one tide tick.";

fn memory() -> SceneRecipeV1 {
    SceneRecipeV1::Memory(PlayContextPolicy::StateRelevantMemoryV1)
}
fn profile() -> PlayProfile {
    PlayProfile {
        id: "synthetic-scene-capture".into(),
        model_sha256: "a".repeat(64),
        runtime_revision: "b".repeat(40),
        template_sha256: "c".repeat(64),
        worker_sha256: "d".repeat(64),
        profile_manifest_sha256: "e".repeat(64),
        context_tokens: 4096,
        director_tokens: 350,
        narrator_tokens: 100,
        deadline_ms: 5000,
        repair_limit: 1,
    }
}
fn engine(presented: bool) -> Engine {
    let mut seed: Seed =
        serde_json::from_str(include_str!("../../../fixtures/lantern_quay.json")).unwrap();
    if presented {
        seed.presentation = Some(StoryPresentationV1 {
            version: 1,
            tone: StoryTone::Warm,
            excluded_phrases: vec!["SYNTHETIC_EXCLUDED_PHRASE".into()],
        });
    }
    Engine::new(seed).unwrap()
}

#[derive(Default)]
struct Script {
    seen: Vec<GenerationRequest>,
    recordings: Vec<Capture>,
    repair: bool,
    fallback: bool,
    fail_narrator: bool,
    cancel_narrator: bool,
    directors: usize,
}
impl InferenceProvider for Script {
    fn poll(
        &mut self,
        request: &GenerationRequest,
        cancel: &Cancellation,
    ) -> Poll<Result<Vec<u8>, Error>> {
        let Input::Structured { role, prompt, schema } = &request.input else {
            panic!("actual structured production request required")
        };
        self.seen.push(request.clone());
        // Observe the actual request exactly as the existing Eval recorder does.
        // This neither compiles context nor constructs a renderer/schema.
        let input = if role == "director" {
            prompt.split_once("Context data: ").and_then(|(_, suffix)| {
                Value::deserialize(&mut serde_json::Deserializer::from_str(suffix)).ok()
            })
        } else {
            None
        };
        self.recordings.push(Capture {
            turn: request.turn.clone(),
            role: role.clone(),
            prompt_sha256: digest(prompt.as_bytes()),
            schema_sha256: digest(&serde_json::to_vec(schema).unwrap()),
            compiler_version: input.as_ref().and_then(|v| v["context"]["compiler_version"].as_u64()),
            player_text_sha256: input.as_ref().and_then(|v| v["player_text"].as_str())
                .map(|text| digest(text.as_bytes())),
            prompt_targets: vec![],
            prompt_targets_present: vec![],
        });
        let output = if role == "director" {
            self.directors += 1;
            if self.repair && self.directors == 1 {
                json!({}) // Real Director parser failure; the production repair path decides.
            } else {
                json!({"commands":[Command::Wait { ticks: 1 }]})
            }
        } else {
            if self.cancel_narrator {
                cancel.cancel();
            }
            if self.fail_narrator {
                return Poll::Ready(Err(Error::Provider));
            }
            json!({
                "text": if self.fallback { "I feel victorious." } else { PROSE },
                "event_ids": schema["properties"]["event_ids"]["const"],
                "speaker":"narrator"
            })
        };
        Poll::Ready(Ok(serde_json::to_vec(&output).unwrap()))
    }
}

#[derive(Clone)]
struct Observed {
    before: Engine,
    after: Engine,
    request: Request,
    recipe: SceneRecipeV1,
    profile: PlayProfile,
    reply: Value,
    recordings: Vec<Capture>,
    actual_requests: Vec<GenerationRequest>,
    outcome: Result<Receipt, Error>,
}
impl Observed {
    fn gate(&self) -> Result<CheckedSceneCaptureV1, GateError> {
        check_committed_scene_capture_v1(SceneCaptureInputV1 {
            before: &self.before,
            after: &self.after,
            request: &self.request,
            expected_recipe: self.recipe,
            expected_profile: &self.profile,
            attempt: 1,
            details_reply: &self.reply,
            recordings: &self.recordings,
        })
    }
    fn receipt(&self) -> Receipt {
        let actual = self.after.recorded(&self.request).unwrap().unwrap();
        assert_eq!(self.outcome.as_ref().unwrap(), &actual);
        actual
    }
    fn artifacts(&self) -> &[Value] {
        self.reply["data"]["details"]["artifacts"].as_array().unwrap()
    }
    fn artifacts_mut(&mut self) -> &mut Vec<Value> {
        self.reply["data"]["details"]["artifacts"].as_array_mut().unwrap()
    }
    fn artifact_mut(&mut self, kind: &str) -> &mut Value {
        &mut self.artifacts_mut().iter_mut().find(|a| a["kind"] == kind).unwrap()["value"]
    }
    fn generation_mut(&mut self, role: &str) -> &mut Value {
        &mut self.artifacts_mut().iter_mut().find(|a| {
            a["kind"] == "generation_request" && a["value"]["input"]["role"] == role
        }).unwrap()["value"]
    }
    fn rehash_generation(&mut self, role: &str) {
        let v = self.generation_mut(role);
        let prompt = digest(v["input"]["prompt"].as_str().unwrap().as_bytes());
        let schema = digest(&serde_json::to_vec(&v["input"]["schema"]).unwrap());
        let c = self.recordings.iter_mut().find(|c| c.role == role).unwrap();
        c.prompt_sha256 = prompt;
        c.schema_sha256 = schema;
    }
    fn renumber(&mut self) {
        for (i, a) in self.artifacts_mut().iter_mut().enumerate() {
            a["ordinal"] = json!(i);
        }
    }
}

fn collect(before: Engine, recipe: SceneRecipeV1, mut script: Script, scene: bool) -> Observed {
    let request = before.request("scene-capture-turn", Intent::FreeText {
        kind: PlayInputKind::Action, text: TEXT.into(),
    });
    let profile = profile();
    let key = AttemptIdentity {
        scope: request.scope.clone(), base_revision: request.expected_revision,
        observer: before.seed().player.clone(), turn: request.turn.clone(), attempt: 1,
    };
    let owner = TraceOwner::default();
    let mut trace = TraceRing::default();
    trace.set_enabled(true);
    trace.configure_details(&owner, &key.scope, true);
    let handle = trace.begin_for_owner(&owner, key.clone(), Provenance::default()).handle.unwrap();
    let ring = Arc::new(Mutex::new(trace));
    let mut sink = RingSink::new(ring.clone(), handle);
    let mut after = before.clone();
    let outcome = if scene {
        play::execute_traced_with_scene_recipe_v1(
            &mut after, &request, &mut script, &Cancellation::default(), &profile,
            Some(&mut sink), ScenePlayConstructionInput { recipe, coverage: None },
        )
    } else {
        play::execute_traced(&mut after, &request, &mut script,
            &Cancellation::default(), &profile, Some(&mut sink))
    };
    let details = ring.lock().unwrap().read_details_for_owner(
        &owner,
        &Selection {
            scope: key.scope.clone(), base_revision: key.base_revision,
            observer: key.observer.clone(), turn: Some(key.turn.clone()), attempt: Some(key.attempt),
        },
        &Reader::story_lab(key.scope.clone()),
    ).unwrap();
    assert_eq!(details.status, DetailStatus::Recorded);
    assert!(!details.exact_reconstruction);
    // ONLY this transport wrapper is test-authored. Every artifact above is the
    // real opt-in collector's copy of the actual production Core operation.
    let reply = json!({"status":"ok","data":{"details":details}});
    Observed {
        before, after, request, recipe, profile, reply,
        recordings: script.recordings, actual_requests: script.seen, outcome,
    }
}
fn sample(recipe: SceneRecipeV1) -> Observed {
    collect(engine(false), recipe, Script::default(), true)
}
fn refused(observed: &Observed, expected: GateError) {
    // Do not require Debug on the opaque successful result.
    match observed.gate() {
        Err(error) => assert_eq!(error, expected),
        Ok(_) => panic!("mutated/unavailable diagnostic unexpectedly passed: {expected:?}"),
    }
}
fn same_source(a: &Engine, b: &Engine) {
    assert_eq!(a.accepted_history_basis().unwrap(), b.accepted_history_basis().unwrap());
    assert_eq!(a.canonical_records(), b.canonical_records());
    assert_eq!(a.seed(), b.seed());
    assert_eq!(a.canonical_bytes(), b.canonical_bytes());
}
fn append_tick(engine: &mut Engine, key: &str) {
    let r = engine.request(key, Intent::Actions(vec![Command::Wait { ticks: 1 }]));
    let p = Engine::proposal(&r).unwrap();
    let preview = engine.preview(&r, &p).unwrap();
    engine.commit(&r, &p, preview.narration()).unwrap();
}

#[test]
fn actual_core_capture_covers_both_recipes_presentation_repair_and_fallback() {
    for recipe in [memory(), SceneRecipeV1::LiteralV1] {
        for presented in [false, true] {
            for repair in [false, true] {
                for fallback in [false, true] {
                    let s = collect(engine(presented), recipe,
                        Script { repair, fallback, ..Script::default() }, true);
                    let receipt = s.receipt();
                    assert_eq!(receipt.play().unwrap().fallback, fallback);
                    assert_eq!(receipt.play().unwrap().repairs, u8::from(repair));
                    assert_eq!(receipt.play().unwrap().story_presentation.is_some(), presented);
                    assert_eq!(s.after.canonical_record_count(), s.before.canonical_record_count() + 1);
                    assert!(s.after.extends_accepted_history(&s.before).unwrap());
                    let before = s.before.clone();
                    let after = s.after.clone();
                    let reply = s.reply.clone();
                    let recordings = serde_json::to_value(&s.recordings).unwrap();
                    let checked = s.gate().ok().expect("actual complete Core capture must pass");
                    assert_eq!(checked.version(), 1);
                    assert_eq!(checked.director_calls(), 1 + u8::from(repair));
                    assert_eq!(checked.fallback(), fallback);
                    let actual_narrator = s.actual_requests.last().unwrap();
                    let Input::Structured { role, prompt, schema } = &actual_narrator.input else {
                        panic!("structured narrator")
                    };
                    assert_eq!(role, "narrator");
                    assert_eq!(checked.narrator_prompt_sha256(), digest(prompt.as_bytes()));
                    assert_eq!(checked.narrator_schema_sha256(), digest(&serde_json::to_vec(schema).unwrap()));
                    assert_eq!(checked.receipt_sha256(), digest(&serde_json::to_vec(&receipt).unwrap()));
                    assert_eq!(s.actual_requests[0].budget.max_output_tokens, 350);
                    assert_eq!(actual_narrator.budget.max_output_tokens, 100);
                    assert_eq!(s.reply["data"]["details"]["exact_reconstruction"], false);
                    same_source(&before, &s.before);
                    same_source(&after, &s.after);
                    assert_eq!(s.reply, reply);
                    assert_eq!(serde_json::to_value(&s.recordings).unwrap(), recordings);
                }
            }
        }
    }
}

#[test]
fn identical_new_narrator_bytes_are_legitimate_across_recipe_arms() {
    let memory = sample(memory());
    let literal = sample(SceneRecipeV1::LiteralV1);
    let Input::Structured { role: ar, prompt: ap, schema: aschema } =
        &memory.actual_requests.last().unwrap().input else { panic!("structured narrator") };
    let Input::Structured { role: br, prompt: bp, schema: bschema } =
        &literal.actual_requests.last().unwrap().input else { panic!("structured narrator") };
    assert_eq!((ar, ap, aschema), (br, bp, bschema));
    let ma = memory.gate().ok().unwrap();
    let lb = literal.gate().ok().unwrap();
    assert_eq!(ma.narrator_prompt_sha256(), lb.narrator_prompt_sha256());
    assert_eq!(ma.narrator_schema_sha256(), lb.narrator_schema_sha256());
    // Arm binding is in actual native provenance, not an invented narrator tag.
    assert_ne!(memory.receipt().play().unwrap().prompt_version,
        literal.receipt().play().unwrap().prompt_version);
    let mut wrong = memory.clone();
    wrong.recipe = SceneRecipeV1::LiteralV1;
    refused(&wrong, GateError::RecipeBinding);
}

#[test]
fn self_consistently_rehashed_narrator_prompt_or_schema_forgery_is_refused() {
    for recipe in [memory(), SceneRecipeV1::LiteralV1] {
        let original = sample(recipe);
        for schema in [false, true] {
            let mut forged = original.clone();
            let v = forged.generation_mut("narrator");
            if schema {
                v["input"]["schema"]["properties"]["speaker"]["const"] = json!("forged-speaker");
            } else {
                let text = v["input"]["prompt"].as_str().unwrap().to_owned();
                v["input"]["prompt"] = json!(format!("{text} SYNTHETIC_FORGED_INSTRUCTION"));
            }
            forged.rehash_generation("narrator");
            refused(&forged, GateError::NarratorForwardingMismatch);
        }
    }
}

#[test]
fn actual_old_recipe_is_not_relabelled_to_the_scene_gate() {
    let old = collect(engine(false), memory(), Script::default(), false);
    assert!(old.receipt().play().unwrap().scene.is_none());
    refused(&old, GateError::RecipeBinding);
}

#[test]
fn expected_profile_and_native_recipe_must_match_actual_record() {
    let original = sample(memory());
    let mut wrong = original.clone();
    wrong.profile.narrator_tokens = 99;
    refused(&wrong, GateError::RecipeBinding);
    wrong = original.clone();
    wrong.recipe = SceneRecipeV1::Memory(PlayContextPolicy::StateRecentTranscriptV1);
    refused(&wrong, GateError::RecipeBinding);
}

#[test]
fn captured_candidate_proposal_and_approved_plan_must_equal_native_values() {
    let original = sample(memory());
    for kind in ["accepted_candidate_not_durable_commit", "parsed_proposal", "validated_plan_not_durable_commit"] {
        let mut forged = original.clone();
        let value = forged.artifact_mut(kind);
        if kind == "parsed_proposal" {
            value["commands"][0]["ticks"] = json!(2);
        } else {
            value["narration"] = json!("SYNTHETIC_FORGED_RECEIPT");
        }
        refused(&forged, GateError::ReceiptBinding);
    }
    for field in ["scene", "story_presentation", "context_policy", "profile"] {
        let mut forged = original.clone();
        forged.artifact_mut("accepted_candidate_not_durable_commit")["play"]
            .as_object_mut().unwrap().remove(field);
        // Even a plausible tuple edit must first match the actual entire receipt.
        // story_presentation is absent on this fixture, so add a false value.
        if field == "story_presentation" {
            forged.artifact_mut("accepted_candidate_not_durable_commit")["play"][field] = json!({"version":99});
        }
        refused(&forged, GateError::ReceiptBinding);
    }
    let mut forged = original.clone();
    forged.artifact_mut("accepted_candidate_not_durable_commit")["play"]["scene"]["frame_sha256"] = json!("f".repeat(64));
    refused(&forged, GateError::ReceiptBinding);
}

#[test]
fn same_scope_and_revision_with_changed_seed_is_not_the_same_source() {
    let mut s = sample(memory());
    let mut changed = s.before.seed().clone();
    changed.facts.get_mut("relic-location").unwrap().proposition = "SYNTHETIC_OTHER_PRIVATE_TRUTH".into();
    let other = Engine::new(changed).unwrap();
    assert_eq!(other.scope(), s.before.scope());
    assert_eq!(other.revision(), s.before.revision());
    assert_ne!(other.accepted_history_basis().unwrap(), s.before.accepted_history_basis().unwrap());
    s.before = other;
    refused(&s, GateError::SourceBinding);
}

#[test]
fn full_prefix_is_required_even_when_seed_scope_head_and_projection_match() {
    let mut actual_before = engine(false);
    let mut other_before = actual_before.clone();
    append_tick(&mut actual_before, "actual-prefix");
    append_tick(&mut other_before, "different-prefix");
    assert_eq!(actual_before.seed(), other_before.seed());
    assert_eq!(actual_before.scope(), other_before.scope());
    assert_eq!(actual_before.revision(), other_before.revision());
    assert_eq!(actual_before.canonical_bytes(), other_before.canonical_bytes());
    assert_ne!(actual_before.accepted_history_basis().unwrap(), other_before.accepted_history_basis().unwrap());
    let mut s = collect(actual_before, memory(), Script::default(), true);
    assert_eq!(s.request.expected_revision, 1);
    assert!(s.gate().is_ok(), "genuine nonempty prefix positive control");
    s.before = other_before;
    refused(&s, GateError::SourceBinding);
}

#[test]
fn missing_commit_retry_basis_or_second_append_cannot_pass_the_immediate_gate() {
    let original = sample(memory());
    let mut missing = original.clone();
    missing.after = missing.before.clone();
    refused(&missing, GateError::Unavailable);
    let mut retry = original.clone();
    retry.before = retry.after.clone();
    refused(&retry, GateError::SourceBinding);
    let mut suffix = original.clone();
    append_tick(&mut suffix.after, "later-append");
    assert_eq!(suffix.after.canonical_record_count(), 2);
    refused(&suffix, GateError::SourceBinding);
}

#[test]
fn failed_actual_core_generation_and_unavailable_capture_statuses_are_not_success() {
    let failed = collect(engine(false), memory(),
        Script { fail_narrator: true, ..Script::default() }, true);
    assert_eq!(failed.outcome.as_ref().err(), Some(&Error::Provider));
    same_source(&failed.before, &failed.after);
    refused(&failed, GateError::Unavailable);
    let original = sample(memory());
    for status in ["disabled", "expired", "not_retained", "truncated"] {
        let mut s = original.clone();
        s.reply["data"]["details"]["status"] = json!(status);
        refused(&s, GateError::Unavailable);
    }
    for kind in ["generation_request", "parsed_proposal", "validated_plan_not_durable_commit", "accepted_candidate_not_durable_commit"] {
        let mut s = original.clone();
        s.artifacts_mut().retain(|a| a["kind"] != kind);
        s.renumber();
        refused(&s, GateError::Unavailable);
    }
}

#[test]
fn actual_cancelled_core_attempt_is_unavailable_without_canonical_append() {
    for recipe in [memory(), SceneRecipeV1::LiteralV1] {
        let cancelled = collect(engine(false), recipe,
            Script { cancel_narrator: true, ..Script::default() }, true);
        assert_eq!(cancelled.outcome.as_ref().err(), Some(&Error::Cancelled));
        same_source(&cancelled.before, &cancelled.after);
        refused(&cancelled, GateError::Unavailable);
    }
}

#[test]
fn actual_domain2_author_correction_has_no_scene_capture_success() {
    let s = sample(memory());
    let proposition = s.before.seed().facts["relic-location"].proposition.clone();
    let input = AuthorCorrectionInputV1 {
        version: 1, parent: s.before.scope().clone(), expected_parent_revision: 0,
        fork_revision: 0, child_branch: "scene-capture-corrected".into(),
        operation: AuthorCorrectionOperationV1::ReplaceFactProposition {
            fact: "relic-location".into(), expected_proposition: proposition,
            replacement: "SYNTHETIC_CORRECTED_TRUTH".into(),
        },
        reason: "Synthetic diagnostic Domain2 qualification".into(),
    };
    let plan = s.before.prepare_author_correction(&input, &|| false).unwrap();
    let d2 = s.before.apply_author_correction(&plan, &|| false).unwrap().engine;
    assert_eq!(d2.domain_version(), 2);
    let mut unsupported = s;
    unsupported.before = d2.clone();
    unsupported.after = d2;
    refused(&unsupported, GateError::Unsupported);
}

#[test]
fn capture_identity_and_each_role_budget_are_bound() {
    let original = sample(memory());
    for field in ["attempt", "observer", "base_revision", "turn", "scope"] {
        let mut s = original.clone();
        s.reply["data"]["details"]["identity"][field] = match field {
            "attempt" | "base_revision" => json!(7),
            "scope" => json!({"story":"other","branch":"main"}),
            _ => json!("other"),
        };
        refused(&s, GateError::CaptureBinding);
    }
    for role in ["director", "narrator"] {
        for field in ["max_output_bytes", "max_output_tokens", "max_pending_polls", "deadline_ms"] {
            let mut s = original.clone();
            s.generation_mut(role)["budget"][field] = json!(0);
            refused(&s, GateError::CaptureBinding);
        }
        for field in ["version", "scope", "turn", "revision", "model_profile", "schema_id"] {
            let mut s = original.clone();
            s.generation_mut(role)[field] = match field {
                "version" | "revision" => json!(99),
                "scope" => json!({"story":"other","branch":"main"}),
                _ => json!("forged"),
            };
            refused(&s, GateError::CaptureBinding);
        }
    }
}

#[test]
fn recording_order_multiplicity_and_hashes_are_not_set_membership() {
    let original = sample(memory());
    let mut reordered = original.clone();
    reordered.recordings.swap(0, 1);
    refused(&reordered, GateError::RecordingMismatch);
    let mut duplicate = original.clone();
    duplicate.recordings.push(duplicate.recordings[0].clone());
    refused(&duplicate, GateError::RecordingMismatch);
    for role in ["director", "narrator"] {
        for schema in [false, true] {
            let mut s = original.clone();
            let c = s.recordings.iter_mut().find(|c| c.role == role).unwrap();
            if schema { c.schema_sha256 = "0".repeat(64); }
            else { c.prompt_sha256 = "0".repeat(64); }
            refused(&s, GateError::RecordingMismatch);
        }
    }
    let mut wrong_roles = original.clone();
    wrong_roles.generation_mut("narrator")["input"]["role"] = json!("director");
    refused(&wrong_roles, GateError::RecordingMismatch);
}

#[test]
fn malformed_ordinals_unknown_and_duplicate_structural_artifacts_are_refused() {
    let original = sample(memory());
    let mut ordinal = original.clone();
    ordinal.artifacts_mut()[0]["ordinal"] = json!(77);
    refused(&ordinal, GateError::Malformed);
    let mut unknown = original.clone();
    unknown.artifacts_mut().push(json!({"kind":"unrecognised_authority","value":{},"ordinal":0}));
    unknown.renumber();
    refused(&unknown, GateError::Malformed);
    for kind in ["parsed_proposal", "validated_plan_not_durable_commit", "accepted_candidate_not_durable_commit", "selected_context"] {
        let mut duplicate = original.clone();
        let value = duplicate.artifacts().iter().find(|a| a["kind"] == kind).unwrap().clone();
        duplicate.artifacts_mut().push(value);
        duplicate.renumber();
        refused(&duplicate, GateError::Malformed);
    }
}

#[test]
fn oversized_capture_is_bounded_before_source_validation() {
    let mut s = sample(memory());
    s.reply["data"]["details"]["oversized_private_diagnostic"] = json!("x".repeat(196_608 + 4097));
    refused(&s, GateError::Budget);
}

#[test]
fn director_envelope_only_and_raw_output_authentication_limits_are_explicit() {
    let original = sample(memory());
    let mut changed = original.clone();
    let prompt = changed.generation_mut("director")["input"]["prompt"].as_str().unwrap().to_owned();
    changed.generation_mut("director")["input"]["prompt"] = json!(format!("{prompt} SYNTHETIC_UNAUTHENTICATED_DIRECTOR_SUFFIX"));
    changed.rehash_generation("director");
    // Deliberately NOT a claim that this altered prompt was forwarded. The
    // smallest gate binds Narrator source only; Director is envelope-only.
    let checked = changed.gate().ok().expect("Director source authentication is outside V1");
    let actual = original.gate().ok().unwrap();
    assert_eq!(checked.narrator_prompt_sha256(), actual.narrator_prompt_sha256());
    assert_eq!(checked.receipt_sha256(), actual.receipt_sha256());
    let mut output_copy = original.clone();
    // Make a self-consistent raw-output diagnostic, without changing the native
    // receipt. This gate does not authenticate output origin or causal linkage.
    let text = "SYNTHETIC_UNAUTHENTICATED_OUTPUT";
    *output_copy.artifact_mut("raw_narrator_output") = json!({
        "encoding":"utf8","bytes":text.len(),"sha256":digest(text.as_bytes()),"text":text
    });
    assert!(output_copy.gate().is_ok());
}
