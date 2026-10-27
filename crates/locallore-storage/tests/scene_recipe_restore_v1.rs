// Copyright 2026 LocalLore contributors. SPDX-License-Identifier: Apache-2.0
//! Independent M05.03/D04.04 Store/Core scene-recipe persistence oracles.
//! First freeze is SOURCE ONLY, UNCOMPILED/UNRUN. New API absence is a compile
//! prerequisite, not behavioral RED. Scripted provider only; no model/Host/UI.
//! No alternate loader, projection, scene renderer or context compiler exists here.
use locallore::{
    contracts::*,
    engine::Engine,
    inference::*,
    memory_coverage::{CoverageRead, FallbackReason},
    play::{
        self,
        scene_narration::{ScenePlayConstructionInput, SceneRecipeV1},
        PlayContextPolicy, PlayProfile,
    },
    story_presentation::{StoryPresentationV1, StoryTone},
};
use locallore_storage::{validate_archive, ArchiveError, Store, TurnPhase};
use serde_json::{json, Value};
use sha2::{Digest, Sha256};
use std::{
    collections::VecDeque,
    fs::OpenOptions,
    io::Write,
    path::PathBuf,
    sync::atomic::{AtomicU64, Ordering},
    task::Poll,
};

const MEMORY: &str = "locallore-play-v2.9-scene-frame-v1";
const LITERAL: &str = "locallore-play-v2.10-literal-director-v1-scene-frame-v1";
const POLICY: &str = "grounded-prose-v2.4-scene-frame-v1";
const PROSE: &str = "You pause as a tide tick passes.";
static NEXT: AtomicU64 = AtomicU64::new(0);
struct Temp {
    path: PathBuf,
    parent: PathBuf,
}
impl Temp {
    fn new() -> Self {
        let parent = std::env::temp_dir().canonicalize().unwrap();
        let path = parent.join(format!(
            "locallore-scene-store-v1-{}-{}-{}",
            std::process::id(),
            std::time::SystemTime::now()
                .duration_since(std::time::UNIX_EPOCH)
                .unwrap()
                .as_nanos(),
            NEXT.fetch_add(1, Ordering::Relaxed)
        ));
        std::fs::create_dir(&path).unwrap();
        Self { path, parent }
    }
    fn open(&self, name: &str) -> Store {
        Store::open(&self.path.join(name), None).unwrap()
    }
}
impl Drop for Temp {
    fn drop(&mut self) {
        let resolved = self.path.canonicalize().unwrap();
        assert_eq!(resolved.parent(), Some(self.parent.as_path()));
        assert!(resolved
            .file_name()
            .unwrap()
            .to_str()
            .unwrap()
            .starts_with("locallore-scene-store-v1-"));
        if let Err(error) = std::fs::remove_dir_all(&resolved) {
            if !std::thread::panicking() {
                panic!("synthetic scene fixture cleanup: {error}");
            }
        }
    }
}
#[derive(Clone, Copy, Debug)]
enum Arm {
    Memory,
    Literal,
}
impl Arm {
    fn recipe(self) -> SceneRecipeV1 {
        match self {
            Self::Memory => SceneRecipeV1::Memory(PlayContextPolicy::StateRecentTranscriptV1),
            Self::Literal => SceneRecipeV1::LiteralV1,
        }
    }
    fn prompt(self) -> &'static str {
        match self {
            Self::Memory => MEMORY,
            Self::Literal => LITERAL,
        }
    }
    fn opposite(self) -> Self {
        match self {
            Self::Memory => Self::Literal,
            Self::Literal => Self::Memory,
        }
    }
}
fn seed(story: &str, presented: bool) -> Seed {
    let mut seed: Seed =
        serde_json::from_str(include_str!("../../../fixtures/lantern_quay.json")).unwrap();
    seed.scope.story = story.into();
    seed.presentation = presented.then(|| StoryPresentationV1 {
        version: 1,
        tone: StoryTone::Warm,
        excluded_phrases: vec!["SYNTHETIC_EXCLUDED_PHRASE".into()],
    });
    seed
}
fn profile() -> PlayProfile {
    PlayProfile {
        id: "synthetic-scene-store-v1".into(),
        model_sha256: "a".repeat(64),
        runtime_revision: "b".repeat(40),
        template_sha256: "c".repeat(64),
        worker_sha256: "d".repeat(64),
        profile_manifest_sha256: "e".repeat(64),
        context_tokens: 4096,
        director_tokens: 350,
        narrator_tokens: 350,
        deadline_ms: 5000,
        repair_limit: 1,
    }
}
#[derive(Default)]
struct Script {
    replies: VecDeque<Vec<u8>>,
    seen: Vec<GenerationRequest>,
}
impl Script {
    fn wait(end: u64) -> Self {
        Self {
            replies: [
                json!({"commands":[{"op":"wait","ticks":1}]}),
                json!({"text":PROSE,"event_ids":[end],"speaker":"narrator"}),
            ]
            .into_iter()
            .map(|value| serde_json::to_vec(&value).unwrap())
            .collect(),
            ..Self::default()
        }
    }
}
impl InferenceProvider for Script {
    fn poll(
        &mut self,
        request: &GenerationRequest,
        _: &Cancellation,
    ) -> Poll<Result<Vec<u8>, Error>> {
        self.seen.push(request.clone());
        Poll::Ready(self.replies.pop_front().ok_or(Error::Provider))
    }
}
fn typed_wait(store: &mut Store, scope: &Scope, turn: &str) -> Receipt {
    let engine = store.resume(scope).unwrap().engine;
    let request = engine.request(turn, Intent::Actions(vec![Command::Wait { ticks: 1 }]));
    let proposal = Engine::proposal(&request).unwrap();
    let receipt = engine.preview(&request, &proposal).unwrap();
    store.begin_turn(&request).unwrap();
    store.commit_prepared(&receipt).unwrap()
}
fn equal_engine(actual: &Engine, expected: &Engine) {
    assert_eq!(actual.scope(), expected.scope());
    assert_eq!(actual.seed(), expected.seed());
    assert_eq!(actual.revision(), expected.revision());
    assert_eq!(actual.domain_version(), expected.domain_version());
    assert_eq!(actual.canonical_records(), expected.canonical_records());
    assert_eq!(actual.receipts(), expected.receipts());
    assert_eq!(actual.canonical_bytes(), expected.canonical_bytes());
    assert_eq!(
        actual.accepted_history_basis().unwrap(),
        expected.accepted_history_basis().unwrap()
    );
    for observer in ["player", "mira", "sable"] {
        assert_eq!(
            actual
                .character_context_v2(observer, actual.scope(), actual.revision())
                .unwrap(),
            expected
                .character_context_v2(observer, expected.scope(), expected.revision())
                .unwrap()
        );
    }
}
fn frame_hash(engine: &Engine, request: &Request, proposal: &Proposal) -> String {
    let staged = engine
        .stage_scene_play_v1(request, proposal, &|| false)
        .unwrap();
    // The shared opaque preparation owns the frame. Hash its actual public
    // serialized bytes; do not recreate the frame/scene/context in this test.
    format!(
        "{:x}",
        Sha256::digest(serde_json::to_vec(staged.scene_frame()).unwrap())
    )
}
fn fixture(temp: &Temp, presented: bool, arm: Arm) -> (Store, Scope, Receipt, Engine) {
    let mut store = temp.open("source.sqlite");
    let seed = seed("scene-recipe-source", presented);
    let scope = seed.scope.clone();
    store.create_story("Synthetic scene recipe", seed).unwrap();
    typed_wait(&mut store, &scope, "historical-prefix");
    let before = store.resume(&scope).unwrap().engine;
    let request = before.request(
        "scene-turn",
        Intent::FreeText {
            kind: PlayInputKind::Action,
            text: "I wait for one tide tick.".into(),
        },
    );
    let mut candidate = before.clone();
    let mut provider = Script::wait(2);
    let coverage = CoverageRead::RawFallback(FallbackReason::Missing);
    let receipt = play::execute_traced_with_scene_recipe_v1(
        &mut candidate,
        &request,
        &mut provider,
        &Cancellation::default(),
        &profile(),
        None,
        ScenePlayConstructionInput {
            recipe: arm.recipe(),
            coverage: match arm {
                Arm::Memory => Some(&coverage),
                Arm::Literal => None,
            },
        },
    )
    .unwrap();
    let roles: Vec<_> = provider
        .seen
        .iter()
        .map(|r| match &r.input {
            Input::Structured { role, .. } => role.as_str(),
            _ => panic!("actual structured pipeline required"),
        })
        .collect();
    assert_eq!(roles, ["director", "narrator"]);
    assert_eq!(receipt.play().unwrap().prompt_version, arm.prompt());
    assert_eq!(receipt.play().unwrap().policy, POLICY);
    assert!(!receipt.play().unwrap().fallback);
    assert_eq!(receipt.narration(), PROSE);
    let record = serde_json::to_value(receipt.play().unwrap()).unwrap();
    assert_eq!(
        record["scene"],
        json!({"version":1,"frame_sha256":frame_hash(&before, &request, receipt.proposal())})
    );
    match arm {
        Arm::Memory => {
            assert_eq!(
                receipt.play().unwrap().context_policy,
                Some(PlayContextPolicy::StateRecentTranscriptV1)
            );
            assert!(receipt.play().unwrap().context.is_some());
        }
        Arm::Literal => {
            assert!(receipt.play().unwrap().context_policy.is_none());
            assert!(receipt.play().unwrap().context.is_none());
        }
    }
    if presented {
        let binding = receipt.play().unwrap().story_presentation.as_ref().unwrap();
        assert_eq!(binding.version, 1);
        assert_eq!(
            binding.presentation_sha256,
            format!(
                "{:x}",
                Sha256::digest(
                    serde_json::to_vec(before.seed().presentation.as_ref().unwrap()).unwrap()
                )
            )
        );
    } else {
        assert!(receipt.play().unwrap().story_presentation.is_none());
    }
    equal_engine(&store.resume(&scope).unwrap().engine, &before);
    assert_eq!(store.begin_turn(&request).unwrap().phase, TurnPhase::Draft);
    let committed = store.commit_prepared(&receipt).unwrap();
    assert_eq!(
        serde_json::to_vec(&committed).unwrap(),
        serde_json::to_vec(&receipt).unwrap()
    );
    equal_engine(&store.resume(&scope).unwrap().engine, &candidate);
    // A later accepted suffix forces restore to validate the scene against its
    // historical prefix, not the final database head or a caller hash.
    let suffix = typed_wait(&mut store, &scope, "after-scene");
    candidate.commit_prepared(&suffix).unwrap();
    equal_engine(&store.resume(&scope).unwrap().engine, &candidate);
    (store, scope, receipt, candidate)
}
fn assert_retry(store: &mut Store, scope: &Scope, receipt: &Receipt, arm: Arm) {
    let mut engine = store.resume(scope).unwrap().engine;
    let before = engine.clone();
    assert_eq!(
        store.begin_turn(receipt.request()).unwrap().receipt,
        Some(receipt.clone())
    );
    let cancel = Cancellation::default();
    cancel.cancel();
    let mut invalid_profile = profile();
    invalid_profile.context_tokens = 0;
    let mut never_infer = Script::default();
    assert_eq!(
        play::execute_traced_with_scene_recipe_v1(
            &mut engine,
            receipt.request(),
            &mut never_infer,
            &cancel,
            &invalid_profile,
            None,
            ScenePlayConstructionInput {
                recipe: arm.opposite().recipe(),
                coverage: None,
            }
        )
        .unwrap(),
        *receipt,
        "recorded identity wins before changed recipe/profile/cancellation/current head"
    );
    assert!(never_infer.seen.is_empty());
    equal_engine(&engine, &before);
    assert_eq!(store.commit_prepared(receipt).unwrap(), *receipt);
    equal_engine(&store.resume(scope).unwrap().engine, &before);
}

#[test]
fn memory_and_literal_ordinary_and_presented_store_reopen_and_archive_preserve_exact_scene_records()
{
    for presented in [false, true] {
        for arm in [Arm::Memory, Arm::Literal] {
            let temp = Temp::new();
            let (mut store, scope, receipt, expected) = fixture(&temp, presented, arm);
            let canonical_records = expected
                .canonical_records()
                .iter()
                .map(|r| serde_json::to_string(r).unwrap())
                .collect::<Vec<_>>();
            equal_engine(
                &Engine::restore(expected.seed().clone(), &canonical_records).unwrap(),
                &expected,
            );
            let archive_before = store
                .export_archive(&scope.story, &|| false)
                .unwrap()
                .bytes()
                .to_vec();
            drop(store);
            let mut reopened = temp.open("source.sqlite");
            equal_engine(&reopened.resume(&scope).unwrap().engine, &expected);
            assert_eq!(reopened.load_seed(&scope).unwrap(), *expected.seed());
            let recorded = reopened
                .lookup_turn(&scope, &receipt.request().turn)
                .unwrap();
            assert_eq!(recorded.phase, TurnPhase::Committed);
            assert_eq!(recorded.request, *receipt.request());
            assert_eq!(
                serde_json::to_vec(recorded.receipt.as_ref().unwrap()).unwrap(),
                serde_json::to_vec(&receipt).unwrap()
            );
            assert_retry(&mut reopened, &scope, &receipt, arm);
            let archive = reopened.export_archive(&scope.story, &|| false).unwrap();
            assert_eq!(archive.bytes(), archive_before);
            let path = temp.path.join("synthetic-full-private.locallore");
            let mut file = OpenOptions::new()
                .write(true)
                .create_new(true)
                .open(&path)
                .unwrap();
            file.write_all(archive.bytes()).unwrap();
            file.sync_all().unwrap();
            drop(file);
            let bytes = std::fs::read(path).unwrap();
            assert_eq!(bytes, archive.bytes());
            let validated = validate_archive(&bytes, &|| false).unwrap();
            let mut target = temp.open("target.sqlite");
            let retained_seed = seed("retained-scene-destination", false);
            let retained_scope = retained_seed.scope.clone();
            target
                .create_story("Retained unrelated destination", retained_seed)
                .unwrap();
            typed_wait(&mut target, &retained_scope, "retained-turn");
            let retained = target.resume(&retained_scope).unwrap().engine;
            let imported = target.import_archive(validated, &|| false).unwrap();
            assert_eq!(imported.root, scope);
            assert_eq!(imported.branches, 1);
            equal_engine(&target.resume(&scope).unwrap().engine, &expected);
            equal_engine(&target.resume(&retained_scope).unwrap().engine, &retained);
            drop(target);
            let mut target = temp.open("target.sqlite");
            equal_engine(&target.resume(&scope).unwrap().engine, &expected);
            equal_engine(&target.resume(&retained_scope).unwrap().engine, &retained);
            assert_retry(&mut target, &scope, &receipt, arm);
            assert_eq!(
                target
                    .export_archive(&scope.story, &|| false)
                    .unwrap()
                    .bytes(),
                bytes
            );
        }
    }
}

// Hostile archive checksums only. This reproduces no scene, context, canonical
// projection or loader semantics; a sender is allowed to recompute checksums.
fn sorted(value: &Value) -> Value {
    match value {
        Value::Object(map) => {
            let mut keys: Vec<_> = map.keys().collect();
            keys.sort_unstable();
            let mut result = serde_json::Map::new();
            for key in keys {
                result.insert(key.clone(), sorted(&map[key]));
            }
            Value::Object(result)
        }
        Value::Array(values) => Value::Array(values.iter().map(sorted).collect()),
        other => other.clone(),
    }
}
fn hash(value: &Value) -> String {
    format!(
        "{:x}",
        Sha256::digest(serde_json::to_vec(&sorted(value)).unwrap())
    )
}
fn rehash(archive: &mut Value) {
    let branches = archive["payload"]["branches"].as_array().unwrap().clone();
    for branch in &branches {
        let records_key = if branch.get("local_records").is_some() {
            "local_records"
        } else {
            "local_receipts"
        };
        let integrity_key = if records_key == "local_records" {
            "records_sha256"
        } else {
            "receipts_sha256"
        };
        let row = archive["integrity"]["branches"]
            .as_array_mut()
            .unwrap()
            .iter_mut()
            .find(|row| row["id"] == branch["id"])
            .unwrap();
        row[integrity_key] = json!(hash(&branch[records_key]));
        // Deliberately preserve the genuine projection checksum: none of these
        // provenance-only changes is authorized to change accepted mechanics.
    }
    archive["integrity"]["seed_sha256"] = json!(hash(&archive["payload"]["story"]["seed"]));
    archive["integrity"]["payload_sha256"] = json!(hash(&archive["payload"]));
}
fn raw_receipt(value: &mut Value) -> &mut Value {
    if value.get("record_version").is_some() {
        &mut value["receipt"]
    } else {
        value
    }
}
fn scene_play_mut(archive: &mut Value) -> &mut Value {
    let branch = &mut archive["payload"]["branches"][0];
    let key = if branch.get("local_records").is_some() {
        "local_records"
    } else {
        "local_receipts"
    };
    // Fixture: one typed prefix, one actual scene record, one typed suffix.
    &mut raw_receipt(&mut branch[key][1])["play"]
}
fn policies_from_mutated_scene(archive: &mut Value) {
    let play = scene_play_mut(archive).clone();
    archive["payload"]["required_policies"] =
        json!([{"policy":play["policy"],"prompt_version":play["prompt_version"]}]);
}
fn unchanged_destination(
    target: &mut Store,
    scope: &Scope,
    expected: &Engine,
    before_archive: &[u8],
) {
    equal_engine(&target.resume(scope).unwrap().engine, expected);
    let catalog = target.stories().unwrap();
    assert_eq!(catalog.len(), 1);
    assert_eq!(catalog[0].scope, *scope);
    assert_eq!(catalog[0].revision, expected.revision());
    assert_eq!(catalog[0].drafts, 0);
    assert_eq!(
        target
            .export_archive(&scope.story, &|| false)
            .unwrap()
            .bytes(),
        before_archive
    );
}

#[test]
fn recomputed_archive_hashes_cannot_forge_scene_frame_recipe_context_or_seed_presentation() {
    for presented in [false, true] {
        for arm in [Arm::Memory, Arm::Literal] {
            let temp = Temp::new();
            let (mut source, scope, receipt, expected) = fixture(&temp, presented, arm);
            let archive = source.export_archive(&scope.story, &|| false).unwrap();
            validate_archive(archive.bytes(), &|| false).unwrap(); // genuine control must pass first
            let original: Value = serde_json::from_slice(archive.bytes()).unwrap();
            let future = expected.request(
                "future-frame",
                Intent::FreeText {
                    kind: PlayInputKind::Action,
                    text: "I wait.".into(),
                },
            );
            let future_proposal = Proposal {
                version: VERSION,
                scope: scope.clone(),
                turn: future.turn.clone(),
                expected_revision: future.expected_revision,
                commands: vec![Command::Wait { ticks: 1 }],
            };
            let future_hash = frame_hash(&expected, &future, &future_proposal);
            let genuine_hash = serde_json::to_value(receipt.play().unwrap()).unwrap()["scene"]
                ["frame_sha256"]
                .clone();
            assert_ne!(genuine_hash, json!(future_hash));
            let mut cases: Vec<(&str, Value)> = vec![];
            let mut value = original.clone();
            scene_play_mut(&mut value)["scene"]["frame_sha256"] = json!("0".repeat(64));
            cases.push(("wrong frame hash", value));
            let mut value = original.clone();
            scene_play_mut(&mut value)["scene"]["frame_sha256"] = json!(future_hash);
            cases.push(("frame from final head instead of actual prefix", value));
            let mut value = original.clone();
            scene_play_mut(&mut value)["scene"]["version"] = json!(2);
            cases.push(("unknown frame version", value));
            let mut value = original.clone();
            scene_play_mut(&mut value)["scene"]["location"] = json!("quay");
            cases.push(("injected frame field", value));
            let mut value = original.clone();
            scene_play_mut(&mut value)
                .as_object_mut()
                .unwrap()
                .remove("scene");
            cases.push(("missing scene binding", value));
            let mut value = original.clone();
            scene_play_mut(&mut value)["prompt_version"] = json!(arm.opposite().prompt());
            policies_from_mutated_scene(&mut value);
            cases.push(("swapped supported recipe with wrong context arm", value));
            let mut value = original.clone();
            scene_play_mut(&mut value)["policy"] = json!("grounded-prose-v2.2");
            policies_from_mutated_scene(&mut value);
            cases.push(("new prompt with legacy policy tuple", value));
            let mut value = original.clone();
            scene_play_mut(&mut value)["prompt_version"] = json!("locallore-play-v2.5");
            scene_play_mut(&mut value)["policy"] = json!("grounded-prose-v2.2");
            policies_from_mutated_scene(&mut value);
            cases.push(("scene record relabeled as legacy", value));
            let mut value = original.clone();
            match arm {
                Arm::Memory => {
                    scene_play_mut(&mut value)["context_policy"] = Value::Null;
                }
                Arm::Literal => {
                    scene_play_mut(&mut value)["context_policy"] =
                        json!("state_recent_transcript_v1");
                }
            }
            cases.push(("impossible construction context tuple", value));
            let mut value = original.clone();
            if presented {
                scene_play_mut(&mut value)["story_presentation"]["presentation_sha256"] =
                    json!("0".repeat(64));
            } else {
                scene_play_mut(&mut value)["story_presentation"] =
                    json!({"version":1,"presentation_sha256":"0".repeat(64)});
            }
            cases.push((
                "presentation binding absent from actual seed or wrong hash",
                value,
            ));
            if presented {
                let mut value = original.clone();
                scene_play_mut(&mut value)
                    .as_object_mut()
                    .unwrap()
                    .remove("story_presentation");
                cases.push(("missing required presentation binding", value));
                let mut value = original.clone();
                value["payload"]["story"]["seed"]["presentation"]["tone"] = json!("brisk");
                cases.push(("different valid presentation seed at same mechanics", value));
            }
            for (serial, (label, mut value)) in cases.into_iter().enumerate() {
                rehash(&mut value);
                let mut target = temp.open(&format!("reject-{serial}.sqlite"));
                let retained_seed = seed("retained-before-rejection", false);
                let retained = retained_seed.scope.clone();
                target
                    .create_story("Retained destination", retained_seed)
                    .unwrap();
                typed_wait(&mut target, &retained, "retained");
                let before = target.resume(&retained).unwrap().engine;
                let before_archive = target
                    .export_archive(&retained.story, &|| false)
                    .unwrap()
                    .bytes()
                    .to_vec();
                let bytes = serde_json::to_vec(&sorted(&value)).unwrap();
                // Actual shared import validation restores accepted history. No
                // forged Receipt or caller-made ValidatedArchive is constructed.
                match validate_archive(&bytes, &|| false) {
                    Err(error) => assert_eq!(
                        error,
                        ArchiveError::Integrity,
                        "{arm:?}/{presented}/{label}"
                    ),
                    Ok(validated) => {
                        let outcome = target.import_archive(validated, &|| false);
                        panic!("{arm:?}/{presented}/{label}: invalid history minted an import capability: {outcome:?}");
                    }
                }
                unchanged_destination(&mut target, &retained, &before, &before_archive);
                drop(target);
                let mut target = temp.open(&format!("reject-{serial}.sqlite"));
                unchanged_destination(&mut target, &retained, &before, &before_archive);
            }
        }
    }
}

#[test]
fn existing_default_and_explicit_literal_records_keep_old_versions_and_omit_scene() {
    for presented in [false, true] {
        for arm in [Arm::Memory, Arm::Literal] {
            let temp = Temp::new();
            let mut store = temp.open("legacy.sqlite");
            let original = seed("legacy-scene-control", presented);
            let scope = original.scope.clone();
            store
                .create_story("Existing recipe control", original)
                .unwrap();
            let mut engine = store.resume(&scope).unwrap().engine;
            let request = engine.request(
                "legacy-turn",
                Intent::FreeText {
                    kind: PlayInputKind::Action,
                    text: "I wait.".into(),
                },
            );
            let mut provider = Script::wait(1);
            let receipt = match arm {
                Arm::Memory => play::execute(
                    &mut engine,
                    &request,
                    &mut provider,
                    &Cancellation::default(),
                    &profile(),
                ),
                Arm::Literal if presented => {
                    play::execute_traced_with_literal_director_presentation_v1(
                        &mut engine,
                        &request,
                        &mut provider,
                        &Cancellation::default(),
                        &profile(),
                        None,
                    )
                }
                Arm::Literal => play::execute_traced_with_literal_director_v1(
                    &mut engine,
                    &request,
                    &mut provider,
                    &Cancellation::default(),
                    &profile(),
                    None,
                ),
            }
            .unwrap();
            let expected_version = match (presented, arm) {
                (false, Arm::Memory) => "locallore-play-v2.5",
                (false, Arm::Literal) => "locallore-play-v2.6-literal-director-v1",
                (true, Arm::Memory) => "locallore-play-v2.7-story-presentation-v1",
                (true, Arm::Literal) => {
                    "locallore-play-v2.8-literal-director-v1-story-presentation-v1"
                }
            };
            assert_eq!(receipt.play().unwrap().prompt_version, expected_version);
            assert_eq!(
                receipt.play().unwrap().policy,
                if presented {
                    "grounded-prose-v2.3-story-presentation-v1"
                } else {
                    "grounded-prose-v2.2"
                }
            );
            assert!(serde_json::to_value(receipt.play().unwrap())
                .unwrap()
                .get("scene")
                .is_none());
            store.begin_turn(&request).unwrap();
            assert_eq!(store.commit_prepared(&receipt).unwrap(), receipt);
            drop(store);
            let mut reopened = temp.open("legacy.sqlite");
            equal_engine(&reopened.resume(&scope).unwrap().engine, &engine);
            assert_eq!(
                reopened.lookup_turn(&scope, &request.turn).unwrap().receipt,
                Some(receipt)
            );
        }
    }
}
