// Copyright 2026 LocalLore contributors. SPDX-License-Identifier: Apache-2.0
//! SOURCE-FROZEN preparation oracles, initially UNCOMPILED/UNRUN.
//! Missing future APIs are compilation prerequisites, never behavioral RED.
//! Independent candidate: existing actual Play2.5 + deterministic provider;
//! this is engine-only evidence, not model/native UI/scene quality evidence.
use locallore::{
    author_correction::*,
    contracts::*,
    engine::{
        staged_scene_play::{NarratorSceneFrameV1, StagedScenePlayV1},
        Engine,
    },
    inference::*,
    inspection_query::{self, FieldValue, Observer, Privacy, Query, Row, View},
    play::{self, PlayProfile},
};
use serde_json::{json, Value};
use std::{cell::Cell, collections::VecDeque, task::Poll};

const A: &str = "SCENE_OBSERVED_A";
const B: &str = "PRIVATE_SCENE_CORRECTED_B";
const REASON: &str = "PRIVATE_SCENE_AUTHOR_REASON";

fn fixture() -> Engine {
    let mut seed: Seed =
        serde_json::from_str(include_str!("../../../fixtures/lantern_quay.json")).unwrap();
    let fact = seed.facts.get_mut("relic-location").unwrap();
    fact.proposition = A.into();
    fact.discoverable_at = Some("quay".into());
    fact.known_by = ["mira".into()].into();
    seed.actors.get_mut("sable").unwrap().name = "PRIVATE_SABLE_NAME".into();
    Engine::new(seed).unwrap()
}

fn request(source: &Engine, key: &str, kind: PlayInputKind, text: &str) -> Request {
    source.request(
        key,
        Intent::FreeText {
            kind,
            text: text.into(),
        },
    )
}

fn proposal(request: &Request, command: Command) -> Proposal {
    Proposal {
        version: VERSION,
        scope: request.scope.clone(),
        turn: request.turn.clone(),
        expected_revision: request.expected_revision,
        commands: vec![command],
    }
}

struct Script {
    replies: VecDeque<Vec<u8>>,
    calls: usize,
}
impl InferenceProvider for Script {
    fn poll(
        &mut self,
        _request: &GenerationRequest,
        _cancel: &Cancellation,
    ) -> Poll<Result<Vec<u8>, Error>> {
        self.calls += 1;
        Poll::Ready(self.replies.pop_front().ok_or(Error::Provider))
    }
}

fn actual_candidate(source: &Engine, request: &Request, proposal: &Proposal) -> Engine {
    let profile = PlayProfile {
        id: "synthetic-scene-preparation-oracle".into(),
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
    };
    let mut script = Script {
        replies: [json!({"commands":proposal.commands}), json!({})]
            .into_iter()
            .map(|value| serde_json::to_vec(&value).unwrap())
            .collect(),
        calls: 0,
    };
    let mut candidate = source.clone();
    let receipt = play::execute(
        &mut candidate,
        request,
        &mut script,
        &Cancellation::default(),
        &profile,
    )
    .unwrap();
    assert_eq!(
        script.calls, 2,
        "actual existing Director/narrator path required"
    );
    assert!(script.replies.is_empty());
    assert_eq!(receipt.request(), request);
    assert_eq!(receipt.proposal(), proposal);
    assert!(
        receipt.play().unwrap().fallback,
        "malformed synthetic narrator must use exact mechanical fallback"
    );
    assert_eq!(
        receipt.play().unwrap().prompt_version,
        "locallore-play-v2.5"
    );
    candidate
}

fn player_location(candidate: &Engine) -> String {
    let context = candidate
        .character_context_v2(
            &candidate.seed().player,
            candidate.scope(),
            candidate.revision(),
        )
        .unwrap();
    let page = inspection_query::query(
        candidate,
        &Query {
            version: 2,
            scope: candidate.scope().clone(),
            expected_head: candidate.revision(),
            at_revision: None,
            observer: Observer::Player,
            view: View::Profiles,
            cursor: None,
            limit: 64,
            search: String::new(),
        },
        false,
    )
    .unwrap();
    assert_eq!(page.privacy, Privacy::PlayerVisible);
    assert!(
        page.next_cursor.is_none(),
        "fixture must expose the complete actual Player profile"
    );
    let locations: Vec<_> = page
        .rows
        .into_iter()
        .filter_map(|row| match row {
            Row::Field {
                actor,
                field,
                value: FieldValue::Text(value),
                ..
            } if actor == candidate.seed().player && field == "location" => Some(value),
            _ => None,
        })
        .collect();
    assert_eq!(locations, vec![context.self_state.location.clone()]);
    context.self_state.location
}

fn unchanged(source: &Engine, before: &Engine) {
    assert_eq!(source.seed(), before.seed());
    assert_eq!(source.canonical_bytes(), before.canonical_bytes());
    assert_eq!(source.canonical_records(), before.canonical_records());
    assert_eq!(
        source.accepted_history_basis().unwrap(),
        before.accepted_history_basis().unwrap()
    );
}

fn assert_frame(source: &Engine, candidate: &Engine, frame: &NarratorSceneFrameV1) {
    let location = player_location(candidate);
    assert_eq!(frame.version(), 1);
    assert_eq!(frame.scope(), source.scope());
    assert_eq!(frame.before_revision(), source.revision());
    assert_eq!(frame.after_revision(), candidate.revision());
    assert_eq!(frame.player(), source.seed().player);
    assert_eq!(frame.location(), location);
    // Equality freezes exactly SIX fields, not a list of forbidden-key guesses.
    // This separately encoded actual Player self value is the location oracle.
    assert_eq!(
        serde_json::to_value(frame).unwrap(),
        json!({
            "version":1,
            "scope":source.scope(),
            "before_revision":source.revision(),
            "after_revision":candidate.revision(),
            "player":source.seed().player,
            "location":location,
        })
    );
}

fn assert_prepared(
    source: &Engine,
    request: &Request,
    proposal: &Proposal,
) -> (StagedScenePlayV1, Engine) {
    let before = source.clone();
    let existing = source.stage_play_v25(request, proposal, &|| false).unwrap();
    let candidate = actual_candidate(source, request, proposal);
    let scene = source
        .stage_scene_play_v1(request, proposal, &|| false)
        .unwrap();
    assert_eq!(scene.approved(), existing.approved());
    assert_eq!(scene.narrator_evidence(), existing.narrator_evidence());
    assert_eq!(
        scene.approved().events(),
        candidate.receipts().last().unwrap().events()
    );
    assert_frame(source, &candidate, scene.scene_frame());
    unchanged(source, &before);
    (scene, candidate)
}

#[test]
fn calibration_existing_stage_actual_play_candidate_and_player_profile_agree() {
    // Uses ONLY existing APIs. Future-module absence still prevents compiling the
    // whole file; do not report this calibration as executed until Cargo runs it.
    let source = fixture();
    let before = source.clone();
    let request = request(
        &source,
        "calibration",
        PlayInputKind::Action,
        "I wait for one tide tick.",
    );
    let proposal = proposal(&request, Command::Wait { ticks: 1 });
    let existing = source
        .stage_play_v25(&request, &proposal, &|| false)
        .unwrap();
    let candidate = actual_candidate(&source, &request, &proposal);
    assert_eq!(
        existing.approved().events(),
        candidate.receipts().last().unwrap().events()
    );
    assert_eq!(player_location(&candidate), "quay");
    assert_eq!(candidate.revision(), 1);
    unchanged(&source, &before);
}

#[test]
fn say_give_and_use_keep_actual_postcandidate_player_location_without_source_mutation() {
    let speech = "PRIVATE_PLAYER_WORDS are only a statement.";
    let cases = [
        (
            PlayInputKind::Dialogue,
            speech,
            Command::Say {
                text: speech.into(),
                audience: ["mira".into()].into(),
            },
        ),
        (
            PlayInputKind::Action,
            "I give potion to mira.",
            Command::Give {
                item: "potion".into(),
                to: "mira".into(),
                quantity: 1,
            },
        ),
        (
            PlayInputKind::Action,
            "I use steady.",
            Command::UseAbility {
                ability: "steady".into(),
            },
        ),
    ];
    for (kind, text, command) in cases {
        let source = fixture();
        let request = request(&source, "nonmovement", kind, text);
        let proposal = proposal(&request, command);
        let (scene, candidate) = assert_prepared(&source, &request, &proposal);
        assert_eq!(scene.scene_frame().location(), "quay");
        assert_eq!(player_location(&candidate), player_location(&source));
        let evidence = serde_json::to_string(scene.narrator_evidence()).unwrap();
        assert!(
            !evidence.contains(speech),
            "a delivered statement must stay sanitized"
        );
    }
}

#[test]
fn accepted_move_anchors_validated_destination_not_before_location() {
    let source = fixture();
    let request = request(&source, "move", PlayInputKind::Action, "I move to pier.");
    let proposal = proposal(&request, Command::Move { to: "pier".into() });
    let (scene, candidate) = assert_prepared(&source, &request, &proposal);
    assert_eq!(player_location(&source), "quay");
    assert_eq!(player_location(&candidate), "pier");
    assert_eq!(scene.scene_frame().location(), "pier");
}

#[test]
fn invalid_route_returns_no_frame_and_preserves_original_source() {
    let source = fixture();
    let before = source.clone();
    let request = request(
        &source,
        "invalid-route",
        PlayInputKind::Action,
        "I move to tower.",
    );
    let proposal = proposal(&request, Command::Move { to: "tower".into() });
    assert!(matches!(
        source.stage_play_v25(&request, &proposal, &|| false),
        Err(Error::Location)
    ));
    assert!(matches!(
        source.stage_scene_play_v1(&request, &proposal, &|| false),
        Err(Error::Location)
    ));
    unchanged(&source, &before);
}

#[test]
fn immediate_and_midpreparation_cancel_return_no_frame_and_preserve_source() {
    let source = fixture();
    let before = source.clone();
    let request = request(&source, "cancel", PlayInputKind::Action, "I move to pier.");
    let proposal = proposal(&request, Command::Move { to: "pier".into() });
    assert!(matches!(
        source.stage_scene_play_v1(&request, &proposal, &|| true),
        Err(Error::Cancelled)
    ));
    unchanged(&source, &before);
    let calls = Cell::new(0);
    let cancelled = || {
        calls.set(calls.get() + 1);
        calls.get() >= 4
    };
    assert!(matches!(
        source.stage_scene_play_v1(&request, &proposal, &cancelled),
        Err(Error::Cancelled)
    ));
    assert!(
        calls.get() >= 4,
        "cancellation must occur after preparation has begun"
    );
    unchanged(&source, &before);
}

#[test]
fn corrected_child_preserves_scope_location_and_observed_a_until_actual_new_discovery_b() {
    let mut parent = fixture();
    let discovery = parent.request(
        "observed-a",
        Intent::Actions(vec![Command::Discover {
            fact: "relic-location".into(),
        }]),
    );
    let initial_proposal = Engine::proposal(&discovery).unwrap();
    let receipt = parent.preview(&discovery, &initial_proposal).unwrap();
    parent.commit_prepared(&receipt).unwrap();
    let plan = parent
        .prepare_author_correction(
            &AuthorCorrectionInputV1 {
                version: 1,
                parent: parent.scope().clone(),
                expected_parent_revision: parent.revision(),
                fork_revision: parent.revision(),
                child_branch: "corrected-scene".into(),
                operation: AuthorCorrectionOperationV1::ReplaceFactProposition {
                    fact: "relic-location".into(),
                    expected_proposition: A.into(),
                    replacement: B.into(),
                },
                reason: REASON.into(),
            },
            &|| false,
        )
        .unwrap();
    let child = parent
        .apply_author_correction(&plan, &|| false)
        .unwrap()
        .engine;
    assert_eq!(child.domain_version(), 2);
    assert_eq!(child.revision(), 2);
    assert_eq!(
        child.effective_fact("relic-location").unwrap().proposition,
        B
    );
    assert_eq!(
        child
            .character_context_v2("player", child.scope(), child.revision())
            .unwrap()
            .facts["relic-location"]
            .proposition,
        A
    );
    for discover in [false, true] {
        let (text, command) = if discover {
            (
                "I discover relic-location.",
                Command::Discover {
                    fact: "relic-location".into(),
                },
            )
        } else {
            ("I wait for one tide tick.", Command::Wait { ticks: 1 })
        };
        let request = request(&child, "child-frame", PlayInputKind::Action, text);
        let proposal = proposal(&request, command);
        let (scene, candidate) = assert_prepared(&child, &request, &proposal);
        assert_eq!(scene.scene_frame().scope().branch, "corrected-scene");
        assert_ne!(scene.scene_frame().scope(), parent.scope());
        let observed = candidate
            .character_context_v2("player", candidate.scope(), candidate.revision())
            .unwrap();
        assert_eq!(
            observed.facts["relic-location"].proposition,
            if discover { B } else { A }
        );
        assert_eq!(
            candidate
                .character_context_v2("mira", candidate.scope(), candidate.revision())
                .unwrap()
                .facts["relic-location"]
                .proposition,
            A
        );
        let observations = scene.narrator_evidence().observations();
        if discover {
            assert_eq!(observations.len(), 1);
            assert_eq!(observations[0].actor(), "player");
            assert_eq!(observations[0].fact(), "relic-location");
            assert_eq!(observations[0].proposition(), B);
            assert_eq!(observations[0].event_id(), candidate.revision());
        } else {
            assert!(
                observations.is_empty(),
                "old observed A must not become a new discovery"
            );
            assert!(!serde_json::to_string(scene.narrator_evidence())
                .unwrap()
                .contains(B));
        }
        let frame: Value = serde_json::to_value(scene.scene_frame()).unwrap();
        let bytes = serde_json::to_string(&frame).unwrap();
        for private in [
            A,
            B,
            REASON,
            "PRIVATE_SABLE_NAME",
            "mira",
            "sable",
            "tower",
            "director",
        ] {
            assert!(
                !bytes.contains(private),
                "frame leaked private/unrelated fixture material {private}"
            );
        }
    }
}
