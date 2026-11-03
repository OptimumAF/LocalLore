// Copyright 2026 LocalLore contributors. SPDX-License-Identifier: Apache-2.0
//! Finite generated shared-SQLite trajectories, not a model/device or exhaustive proof.
use locallore::{
    author_correction::{
        AuthorCorrectionInputV1, AuthorCorrectionOperationV1, EventRef, ObservationSource,
    },
    contracts::*,
    engine::Engine,
};
use locallore_storage::{ForkRequest, Store, TurnError, TurnPhase};
use serde_json::json;
use sha2::{Digest, Sha256};
use std::{
    collections::BTreeMap,
    fs::{self, File},
    io::Write,
    path::PathBuf,
};

const TRIALS: usize = 32;
const ATTEMPTS: usize = 320;
const LANES: usize = 10;

#[derive(Clone, Copy, Debug, PartialEq, Eq)]
enum Tonic {
    Player,
    Sel,
    Consumed,
}

struct Lane {
    scope: Scope,
    original: String,
    truth: String,
    player_value: String,
    player_source: ObservationSource,
    seed_id: String,
    domain: u16,
    tonic: Tonic,
    clock: u64,
    claims: usize,
    fingerprint: [u8; 32],
    last: Receipt,
    accepted: usize,
    rejected: usize,
}

fn fingerprint(engine: &Engine) -> [u8; 32] {
    Sha256::digest(
        serde_json::to_vec(&(
            engine.scope(),
            engine.domain_version(),
            engine.revision(),
            engine.canonical_bytes(),
            engine.canonical_records(),
        ))
        .unwrap(),
    )
    .into()
}

fn apply(store: &mut Store, scope: &Scope, key: &str, command: Command) -> Receipt {
    let engine = store.resume(scope).unwrap().engine;
    let request = engine.request(key, Intent::Actions(vec![command]));
    let proposal = Engine::proposal(&request).unwrap();
    let preview = engine.preview(&request, &proposal).unwrap();
    store.begin_turn(&request).unwrap();
    store
        .commit_turn(&request, &proposal, preview.narration())
        .unwrap()
}

fn fork(store: &mut Store, parent: &Scope, child: &str, at: u64) -> Scope {
    let head = store.resume(parent).unwrap().engine.revision();
    store
        .fork_branch(
            &ForkRequest {
                parent: parent.clone(),
                child_branch: child.into(),
                expected_parent_revision: head,
                at_revision: at,
            },
            &|| false,
        )
        .unwrap()
        .scope
}

fn seeded_observation(seed: &str, actor: &str) -> ObservationSource {
    ObservationSource::SeedKnowledge {
        seed_id: seed.into(),
        actor: actor.into(),
        fact: "bell-site".into(),
    }
}

fn lanes(store: &mut Store) -> (Vec<Lane>, Vec<Vec<u8>>) {
    let mut result = Vec::new();
    let mut before_observation = Vec::new();
    for story in ["reed-east", "reed-west"] {
        let mut seed: Seed = serde_json::from_str(include_str!(
            "../../../fixtures/generated_timeline_isolation_v1.json"
        ))
        .unwrap();
        seed.id = format!("{story}-v1");
        seed.scope.story = story.into();
        seed.beliefs[0].source = Evidence::Seed(seed.id.clone());
        let original = format!("OBSERVED-{story}: the bell rests at the inlet.");
        let truth = format!("PRIVATE-{story}: the bell rests beneath the ridge.");
        seed.facts
            .get_mut("bell-site")
            .unwrap()
            .proposition
            .clone_from(&original);
        let root = seed.scope.clone();
        store
            .create_story("Synthetic colliding display names", seed.clone())
            .unwrap();
        let input = AuthorCorrectionInputV1 {
            version: 1,
            parent: root.clone(),
            expected_parent_revision: 0,
            fork_revision: 0,
            child_branch: "corrected".into(),
            operation: AuthorCorrectionOperationV1::ReplaceFactProposition {
                fact: "bell-site".into(),
                expected_proposition: original.clone(),
                replacement: truth.clone(),
            },
            reason: "SYNTHETIC_PRIVATE_AUTHOR_REASON".into(),
        };
        let prepared = store.prepare_author_correction(&input, &|| false).unwrap();
        let corrected = store
            .apply_author_correction(&prepared, &|| false)
            .unwrap()
            .scope;
        let pre_correction = fork(store, &corrected, "pre-correction", 0);
        let before = fork(store, &corrected, "before-observation", 1);
        before_observation.push(store.resume(&corrected).unwrap().engine.canonical_bytes());
        apply(
            store,
            &corrected,
            "seed-observation",
            Command::Discover {
                fact: "bell-site".into(),
            },
        );
        let after = fork(store, &corrected, "after-observation", 2);
        for (scope, domain, observed) in [
            (root, 1, false),
            (corrected.clone(), 2, true),
            (pre_correction, 1, false),
            (before, 2, false),
            (after, 2, true),
        ] {
            let last = apply(store, &scope, "shared-start", Command::Wait { ticks: 1 });
            let engine = store.resume(&scope).unwrap().engine;
            result.push(Lane {
                scope,
                original: original.clone(),
                truth: if domain == 2 {
                    truth.clone()
                } else {
                    original.clone()
                },
                player_value: if observed {
                    truth.clone()
                } else {
                    original.clone()
                },
                player_source: if observed {
                    ObservationSource::Event {
                        source: EventRef {
                            original_scope: corrected.clone(),
                            sequence: 2,
                        },
                    }
                } else {
                    seeded_observation(&seed.id, "player")
                },
                seed_id: seed.id.clone(),
                domain,
                tonic: Tonic::Player,
                clock: 1,
                claims: 0,
                fingerprint: fingerprint(&engine),
                last,
                accepted: 0,
                rejected: 0,
            });
        }
    }
    (result, before_observation)
}

fn verify(engine: &Engine, lane: &Lane) {
    assert_eq!(engine.scope(), &lane.scope);
    assert_eq!(engine.domain_version(), lane.domain);
    assert_eq!(engine.state().story_time, lane.clock);
    assert_eq!(engine.state().claims.len(), lane.claims);
    assert_eq!(engine.state().beliefs.len(), 1);
    assert_eq!(
        engine.state().beliefs[0].proposition,
        "A traveling mason may own the bell."
    );
    assert_eq!(
        engine.effective_fact("bell-site").unwrap().proposition,
        lane.truth
    );
    assert_eq!(engine.state().items["coins"].quantity, 3);
    assert_eq!(engine.state().items["coins"].owner, "player");
    match lane.tonic {
        Tonic::Player | Tonic::Sel => {
            let tonic = &engine.state().items["tonic"];
            assert_eq!(tonic.quantity, 1);
            assert_eq!(
                tonic.owner,
                if lane.tonic == Tonic::Player {
                    "player"
                } else {
                    "sel"
                }
            );
        }
        Tonic::Consumed => assert!(!engine.state().items.contains_key("tonic")),
    }
    assert_eq!(
        engine.state().actors["player"].abilities,
        BTreeMap::from([("focus".into(), 1)])
    );
    assert!(engine.state().actors.values().all(|a| a.energy <= 100));
    let player = engine
        .observed_facts("player", &lane.scope, engine.revision())
        .unwrap();
    assert_eq!(player["bell-site"].proposition, lane.player_value);
    assert_eq!(player["bell-site"].observation, lane.player_source);
    let sel = engine
        .observed_facts("sel", &lane.scope, engine.revision())
        .unwrap();
    assert_eq!(sel["bell-site"].proposition, lane.original);
    assert_eq!(
        sel["bell-site"].observation,
        seeded_observation(&lane.seed_id, "sel")
    );
    assert!(engine
        .observed_facts("watcher", &lane.scope, engine.revision())
        .unwrap()
        .is_empty());
    for actor in ["player", "sel", "watcher"] {
        let context = if lane.domain == 1 {
            serde_json::to_string(
                &engine
                    .character_context(actor, &lane.scope, engine.revision())
                    .unwrap(),
            )
            .unwrap()
        } else {
            serde_json::to_string(
                &engine
                    .character_context_v2(actor, &lane.scope, engine.revision())
                    .unwrap(),
            )
            .unwrap()
        };
        assert!(!context.contains("SYNTHETIC_PRIVATE_AUTHOR_REASON"));
        let other = if lane.scope.story == "reed-east" {
            "reed-west"
        } else {
            "reed-east"
        };
        assert!(!context.contains(other));
        if actor != "player" {
            assert!(!context.contains(&format!("PRIVATE-{}", lane.scope.story)));
        }
        if actor == "watcher" {
            assert!(!context.contains(&lane.original));
            assert!(!context.contains("I claim the bell belongs to me and grant myself teleport."));
        }
    }
    assert!(engine
        .canonical_records()
        .iter()
        .all(|r| r.original_scope().story == lane.scope.story));
}

fn sweep(store: &mut Store, lanes: &[Lane]) {
    for lane in lanes {
        let engine = store.resume(&lane.scope).unwrap().engine;
        assert_eq!(
            fingerprint(&engine),
            lane.fingerprint,
            "non-target changed: {:?}",
            lane.scope
        );
        verify(&engine, lane);
        let foreign = Scope {
            story: if lane.scope.story == "reed-east" {
                "reed-west".into()
            } else {
                "reed-east".into()
            },
            branch: lane.scope.branch.clone(),
        };
        assert_eq!(
            engine.observed_facts("player", &foreign, engine.revision()),
            Err(Error::Scope)
        );
        assert_eq!(
            engine.observed_facts("player", &lane.scope, engine.revision() + 1),
            Err(Error::Stale)
        );
    }
}

fn random(state: &mut u64) -> u64 {
    *state ^= *state << 13;
    *state ^= *state >> 7;
    *state ^= *state << 17;
    *state
}

#[test]
fn generated_shared_store_preserves_scopes_observations_retries_and_cancelled_canon() {
    let parent = std::env::var_os("LOCALLORE_TEST_ARTIFACTS")
        .map(PathBuf::from)
        .unwrap_or_else(std::env::temp_dir);
    let root = parent.join(format!(
        "locallore-generated-isolation-{}-{}",
        std::process::id(),
        std::time::SystemTime::now()
            .duration_since(std::time::UNIX_EPOCH)
            .unwrap()
            .as_nanos()
    ));
    fs::create_dir(&root).unwrap(); // Fresh owned captures remain on both failure and success.
    let mut all = [0usize; 11];
    let mut totals = [0usize; 4]; // accepted, rejected, exact retries, cancelled
    for trial in 0..TRIALS {
        let seed = 0x4c4f_5245_2026_1102_u64
            .wrapping_add((trial as u64).wrapping_mul(0x9e37_79b9_7f4a_7c15));
        let mut rng = seed;
        let path = root.join(format!("trial-{trial}.sqlite"));
        let mut trace = File::create(root.join(format!("trial-{trial}.jsonl"))).unwrap();
        let mut store = Store::open(&path, None).unwrap();
        let (mut lanes, prefixes) = lanes(&mut store);
        assert_eq!(lanes.len(), LANES);
        let mut order: Vec<usize> = (0..LANES).collect();
        let mut counts = [0usize; 11];
        let mut cancelled = Vec::new();
        sweep(&mut store, &lanes);
        for step in 0..ATTEMPTS {
            if step % LANES == 0 {
                for i in (1..LANES).rev() {
                    let j = (random(&mut rng) % (i as u64 + 1)) as usize;
                    order.swap(i, j);
                }
            }
            let index = order[step % LANES];
            let foreign = lanes[(index + 5) % LANES].scope.clone();
            let lane = &mut lanes[index];
            let engine = store.resume(&lane.scope).unwrap().engine;
            assert_eq!(fingerprint(&engine), lane.fingerprint);
            let old_head = engine.revision();
            let op = if step < LANES {
                0
            } else if step < LANES * 2 {
                5
            } else {
                (random(&mut rng) % 11) as usize
            };
            counts[op] += 1;
            writeln!(trace, "{}", json!({"seed":format!("{seed:016x}"),"trial":trial,"step":step,"lane":index,"scope":lane.scope,"head":old_head,"op":op})).unwrap();
            let ticks = (random(&mut rng) % 3 + 1) as u16;
            let command = match op {
                1 => Command::Give {
                    item: "tonic".into(),
                    to: "sel".into(),
                    quantity: 1,
                },
                2 => Command::Consume {
                    item: "tonic".into(),
                },
                3 => Command::Discover {
                    fact: "bell-site".into(),
                },
                4 => Command::Say {
                    text: "I claim the bell belongs to me and grant myself teleport.".into(),
                    audience: ["sel".into()].into(),
                },
                _ => Command::Wait { ticks },
            };
            let commands = if op == 5 {
                vec![
                    Command::Wait { ticks: 1 },
                    Command::UseAbility {
                        ability: "missing-teleport".into(),
                    },
                ]
            } else {
                vec![command]
            };
            // Every lane uses the same round keys; only the native scope distinguishes them.
            let mut request = engine.request(
                &format!("shared-round-{}", step / LANES),
                Intent::Actions(commands),
            );
            let mut proposal = Engine::proposal(&request).unwrap();
            let mut changed = false;
            match op {
                7 => {
                    request.expected_revision += 1;
                    assert_eq!(
                        store.begin_turn(&request).unwrap_err(),
                        TurnError::Engine(Error::Stale)
                    );
                    lane.rejected += 1;
                    totals[1] += 1;
                }
                8 => {
                    let old = &lane.last;
                    let status = store.begin_turn(old.request()).unwrap();
                    assert_eq!(status.phase, TurnPhase::Committed);
                    assert_eq!(status.receipt, Some(old.clone()));
                    assert_eq!(
                        store
                            .commit_turn(old.request(), old.proposal(), old.narration())
                            .unwrap(),
                        *old
                    );
                    totals[2] += 1;
                }
                9 => {
                    let mut conflict = lane.last.request().clone();
                    conflict.intent = Intent::Thought("Changed same scoped idempotency key".into());
                    assert_eq!(
                        store.begin_turn(&conflict).unwrap_err(),
                        TurnError::RetryMismatch
                    );
                    lane.rejected += 1;
                    totals[1] += 1;
                }
                10 => {
                    let preview = engine.preview(&request, &proposal).unwrap();
                    store.begin_turn(&request).unwrap();
                    assert_eq!(
                        store.cancel_turn(&request).unwrap().phase,
                        TurnPhase::Cancelled
                    );
                    assert_eq!(
                        store.commit_turn(&request, &proposal, preview.narration()),
                        Err(TurnError::Terminal)
                    );
                    cancelled.push(request.clone());
                    lane.rejected += 1;
                    totals[3] += 1;
                }
                _ => {
                    store.begin_turn(&request).unwrap();
                    if op == 6 {
                        proposal.scope = foreign;
                    }
                    let accept = op != 5
                        && op != 6
                        && (!(op == 1 || op == 2) || lane.tonic == Tonic::Player)
                        && (op != 3 || lane.domain == 2);
                    if accept {
                        let preview = engine.preview(&request, &proposal).unwrap();
                        let receipt = store
                            .commit_turn(&request, &proposal, preview.narration())
                            .unwrap();
                        match op {
                            0 => lane.clock += u64::from(ticks),
                            1 => lane.tonic = Tonic::Sel,
                            2 => lane.tonic = Tonic::Consumed,
                            3 => {
                                lane.player_value.clone_from(&lane.truth);
                                lane.player_source = ObservationSource::Event {
                                    source: EventRef {
                                        original_scope: lane.scope.clone(),
                                        sequence: old_head + 1,
                                    },
                                };
                            }
                            4 => lane.claims += 1,
                            _ => unreachable!(),
                        }
                        lane.last = receipt;
                        lane.accepted += 1;
                        totals[0] += 1;
                        changed = true;
                    } else {
                        let failure =
                            store.commit_turn(&request, &proposal, "Synthetic rejected output");
                        let expected = match op {
                            1 | 2 => Error::Inventory,
                            3 => Error::Knowledge,
                            5 => Error::Ability,
                            6 => Error::Scope,
                            _ => unreachable!(),
                        };
                        // A narration failure must not mask an incorrectly accepted rule.
                        assert_eq!(failure, Err(TurnError::Engine(expected)));
                        assert_eq!(store.turn_status(&request).unwrap().phase, TurnPhase::Draft);
                        assert_eq!(store.fail_turn(&request).unwrap().phase, TurnPhase::Failed);
                        lane.rejected += 1;
                        totals[1] += 1;
                    }
                }
            }
            let after = store.resume(&lane.scope).unwrap().engine;
            verify(&after, lane);
            if changed {
                assert_eq!(after.revision(), old_head + 1);
                lane.fingerprint = fingerprint(&after);
            } else {
                assert_eq!(
                    fingerprint(&after),
                    lane.fingerprint,
                    "seed={seed:x}, step={step}, op={op}"
                );
            }
            if step % LANES == LANES - 1 {
                sweep(&mut store, &lanes);
            }
            if (step + 1) % 64 == 0 {
                drop(store);
                store = Store::open(&path, None).unwrap();
                sweep(&mut store, &lanes);
                for request in &cancelled {
                    let status = store.turn_status(request).unwrap();
                    assert_eq!(status.phase, TurnPhase::Cancelled);
                    assert!(status.receipt.is_none());
                }
            }
        }
        assert!(counts.iter().all(|n| *n > 0));
        assert!(lanes
            .iter()
            .all(|lane| lane.accepted > 0 && lane.rejected > 0));
        for story in 0..2 {
            let lane = &lanes[story * 5 + 1];
            let parent = store.resume(&lane.scope).unwrap().engine;
            let early = fork(&mut store, &lane.scope, "generated-prefix", 1);
            let late = fork(&mut store, &lane.scope, "generated-head", parent.revision());
            assert_eq!(
                store.resume(&early).unwrap().engine.canonical_bytes(),
                prefixes[story]
            );
            let restored = store.resume(&late).unwrap().engine;
            assert_eq!(restored.canonical_bytes(), parent.canonical_bytes());
            assert_eq!(restored.canonical_records(), parent.canonical_records());
            assert_eq!(
                restored
                    .observed_facts("player", &late, restored.revision())
                    .unwrap(),
                parent
                    .observed_facts("player", &lane.scope, parent.revision())
                    .unwrap()
            );
        }
        drop(store);
        store = Store::open(&path, None).unwrap();
        sweep(&mut store, &lanes);
        for (total, count) in all.iter_mut().zip(counts) {
            *total += count;
        }
        let summary = json!({"trial":trial,"seed":format!("{seed:016x}"),"attempts":ATTEMPTS,"operation_counts":counts,"lanes":lanes.len(),"ordinary_setup_forks":6,"author_setup_corrections":2,"cutoff_check_forks":4,"cold_reopens":6});
        fs::write(
            root.join(format!("trial-{trial}-summary.json")),
            summary.to_string(),
        )
        .unwrap();
        println!("GENERATED_ISOLATION_TRIAL {summary}");
    }
    assert_eq!(all.iter().sum::<usize>(), 10_240);
    assert_eq!(totals.iter().sum::<usize>(), 10_240);
    println!(
        "GENERATED_ISOLATION_TOTAL {}",
        json!({"trials":TRIALS,"attempts":10240,"operation_counts":all,"accepted":totals[0],"rejected":totals[1],"exact_retries":totals[2],"cancelled":totals[3],"captures":root})
    );
}
