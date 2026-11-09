//! Original player-self profiles from real accepted native state, for both
//! domain versions and both rule profiles. No model, JNI, SQLite or device claim.
#![cfg(feature = "host")]

use locallore::{
    author_correction::{AuthorCorrectionInputV1, AuthorCorrectionOperationV1},
    contracts::*,
    engine::Engine,
    host::{Host, Persistence, SavedTurn, WorkspaceSummary},
    inspection::ExportMode,
};
use serde_json::{json, Value};
use std::{
    collections::{BTreeMap, BTreeSet},
    fs::{self, OpenOptions},
    io::Write,
    path::PathBuf,
    sync::{Arc, Mutex},
};

const PLAYER: &str = "a-71be92c40d6f8a53c201-0";
const TEACHER: &str = "a-71be92c40d6f8a53c201-1";
const FOREIGN: &str = "a-71be92c40d6f8a53c201-2";
const START: &str = "l-71be92c40d6f8a53c201-0";
const FINISH: &str = "l-71be92c40d6f8a53c201-1";
const OLD: &str = "PRIVATE_SELF_PROFILE_OLD_TRUTH";
const NEW: &str = "PRIVATE_SELF_PROFILE_NEW_TRUTH";
const REASON: &str = "PRIVATE_SELF_PROFILE_AUTHOR_REASON";
const CANARIES: [&str; 5] = [
    "PRIVATE_SELF_PROFILE_NPC",
    "PRIVATE_SELF_PROFILE_BELIEF",
    "PRIVATE_SELF_PROFILE_FOREIGN_ITEM",
    "PRIVATE_SELF_PROFILE_FOREIGN_GOAL",
    "PRIVATE_SELF_PROFILE_FOREIGN_ATTRIBUTE",
];

fn names(values: &[&str]) -> BTreeSet<String> {
    values.iter().map(|s| (*s).into()).collect()
}

fn seed(fantasy: bool) -> Seed {
    let player = Actor {
        name: if fantasy { "Arié 灯" } else { "Noor 灯" }.into(),
        location: START.into(),
        alive: true,
        energy: if fantasy { 9 } else { 0 },
        abilities: if fantasy {
            [("chart-sense".into(), 1), ("focus-step".into(), 2)].into()
        } else {
            BTreeMap::new()
        },
        attributes: if fantasy {
            [("resolve".into(), -7), ("Élan".into(), 23)].into()
        } else {
            BTreeMap::new()
        },
        injuries: names(if fantasy {
            &["ankle-strain", "cut-palm"]
        } else {
            &["sprained-wrist"]
        }),
        affiliations: names(&["cartographers", "夜のギルド"]),
        goals: names(&["finish-chart", "守る"]),
    };
    let mut teacher = player.clone();
    teacher.name = "Nia".into();
    teacher.injuries.clear();
    if fantasy {
        teacher.abilities.insert("focus-step".into(), 3);
    }
    let mut foreign = player.clone();
    foreign.name = CANARIES[0].into();
    foreign.location = FINISH.into();
    foreign.goals = names(&[CANARIES[3]]);
    if fantasy {
        foreign.attributes.insert(CANARIES[4].into(), 13);
    }
    let id = if fantasy {
        "self-profile-fantasy-v1"
    } else {
        "self-profile-narrative-v1"
    };
    Seed {
        version: VERSION,
        id: id.into(),
        scope: Scope {
            story: if fantasy {
                "self-profile-fantasy"
            } else {
                "self-profile-narrative"
            }
            .into(),
            branch: "main".into(),
        },
        profile: if fantasy {
            Profile::FantasyV1
        } else {
            Profile::NarrativeV1
        },
        player: PLAYER.into(),
        locations: names(&[START, FINISH]),
        routes: [(START.into(), FINISH.into())].into(),
        actors: [
            (PLAYER.into(), player),
            (TEACHER.into(), teacher),
            (FOREIGN.into(), foreign),
        ]
        .into(),
        items: [
            (
                "saffron-tonic".into(),
                Item {
                    owner: PLAYER.into(),
                    quantity: 2,
                    return_to: None,
                    healing: true,
                },
            ),
            (
                CANARIES[2].into(),
                Item {
                    owner: FOREIGN.into(),
                    quantity: 17,
                    return_to: None,
                    healing: false,
                },
            ),
        ]
        .into(),
        abilities: if fantasy {
            [
                (
                    "chart-sense".into(),
                    Ability {
                        cost: 1,
                        prerequisite: None,
                        teacher: TEACHER.into(),
                        max_rank: 3,
                    },
                ),
                (
                    "focus-step".into(),
                    Ability {
                        cost: 2,
                        prerequisite: Some("chart-sense".into()),
                        teacher: TEACHER.into(),
                        max_rank: 3,
                    },
                ),
            ]
            .into()
        } else {
            BTreeMap::new()
        },
        facts: [(
            "unseen-beacon".into(),
            Fact {
                proposition: OLD.into(),
                discoverable_at: Some(FINISH.into()),
                known_by: names(&[FOREIGN]),
            },
        )]
        .into(),
        relationships: vec![],
        story_time: 10,
        beliefs: vec![Belief {
            believer: FOREIGN.into(),
            proposition: CANARIES[1].into(),
            source_claim: None,
            source: Evidence::Seed(id.into()),
            confidence: Confidence::Believed,
        }],
        commitments: BTreeMap::new(),
        presentation: None,
        initial_world: None,
    }
}

fn append(engine: &mut Engine, turn: &str, command: Command) {
    let request = engine.request(turn, Intent::Actions(vec![command]));
    let proposal = Engine::proposal(&request).unwrap();
    let receipt = engine.preview(&request, &proposal).unwrap();
    engine.commit_prepared(&receipt).unwrap();
}

fn scenario(fantasy: bool, domain: u16) -> Engine {
    let mut engine = Engine::new(seed(fantasy)).unwrap();
    append(&mut engine, "arrive-and-wait", Command::Wait { ticks: 1 });
    if domain == 2 {
        let input = AuthorCorrectionInputV1 {
            version: 1,
            parent: engine.scope().clone(),
            expected_parent_revision: engine.revision(),
            fork_revision: engine.revision(),
            child_branch: "corrected".into(),
            operation: AuthorCorrectionOperationV1::ReplaceFactProposition {
                fact: "unseen-beacon".into(),
                expected_proposition: OLD.into(),
                replacement: NEW.into(),
            },
            reason: REASON.into(),
        };
        let plan = engine.prepare_author_correction(&input, &|| false).unwrap();
        engine = engine
            .apply_author_correction(&plan, &|| false)
            .unwrap()
            .engine;
    }
    assert_eq!(engine.domain_version(), domain);
    assert_eq!(engine.state().actors[PLAYER].location, START);
    if fantasy {
        assert_eq!(engine.state().actors[PLAYER].energy, 9);
        assert_eq!(engine.state().actors[PLAYER].abilities["focus-step"], 2);
        append(
            &mut engine,
            "learn-focus",
            Command::Learn {
                ability: "focus-step".into(),
            },
        );
        assert_eq!(engine.state().actors[PLAYER].abilities["focus-step"], 3);
        append(
            &mut engine,
            "use-focus",
            Command::UseAbility {
                ability: "focus-step".into(),
            },
        );
        assert_eq!(engine.state().actors[PLAYER].energy, 7);
        append(
            &mut engine,
            "heal-ankle",
            Command::Consume {
                item: "saffron-tonic".into(),
            },
        );
        assert_eq!(engine.state().actors[PLAYER].injuries, names(&["cut-palm"]));
        assert_eq!(engine.state().items["saffron-tonic"].quantity, 1);
    }
    append(
        &mut engine,
        "walk-to-lookout",
        Command::Move { to: FINISH.into() },
    );
    assert_eq!(
        engine.revision(),
        if fantasy {
            4 + u64::from(domain)
        } else {
            1 + u64::from(domain)
        }
    );
    engine
}

fn expected_actor(fantasy: bool) -> Value {
    json!({
        "name":if fantasy { "Arié 灯" } else { "Noor 灯" },
        "location":FINISH,"alive":true,"energy":if fantasy { 7 } else { 0 },
        "abilities":if fantasy { json!({"chart-sense":1,"focus-step":3}) } else { json!({}) },
        "attributes":if fantasy { json!({"resolve":-7,"Élan":23}) } else { json!({}) },
        "injuries":if fantasy { vec!["cut-palm"] } else { vec!["sprained-wrist"] },
        "affiliations":["cartographers","夜のギルド"],"goals":["finish-chart","守る"]
    })
}

struct ReadOnly(Arc<Mutex<(Engine, usize)>>);
impl ReadOnly {
    fn refuse<T>(&self) -> Result<T, String> {
        self.0.lock().unwrap().1 += 1;
        Err("Unsupported".into())
    }
}
impl Persistence for ReadOnly {
    fn location(&self) -> &str {
        "synthetic-self-profile-readonly"
    }
    fn list(&mut self) -> Result<Vec<WorkspaceSummary>, String> {
        Err("Unsupported".into())
    }
    fn create(&mut self) -> Result<Engine, String> {
        self.refuse()
    }
    fn validate_scope(&mut self, scope: &Scope) -> Result<(), String> {
        if self.0.lock().unwrap().0.scope() == scope {
            Ok(())
        } else {
            Err("Scope".into())
        }
    }
    fn resume(&mut self, scope: &Scope) -> Result<Engine, String> {
        self.validate_scope(scope)?;
        Ok(self.0.lock().unwrap().0.clone())
    }
    fn begin(&mut self, _: &Request) -> Result<SavedTurn, String> {
        self.refuse()
    }
    fn commit(&mut self, _: &Request, _: &Proposal, _: &str) -> Result<Receipt, String> {
        self.refuse()
    }
    fn cancel(&mut self, _: &Request) -> Result<SavedTurn, String> {
        self.refuse()
    }
    fn fail(&mut self, _: &Request) -> Result<SavedTurn, String> {
        self.refuse()
    }
    fn stale(&mut self, _: &Request) -> Result<SavedTurn, String> {
        self.refuse()
    }
    fn status(&mut self, _: &Scope, _: &str) -> Result<SavedTurn, String> {
        Err("Unsupported".into())
    }
}

fn call(host: &Host, command: Value) -> Value {
    host.call(&serde_json::to_vec(&json!({"version":1,"command":command})).unwrap())
}

fn export_state(
    host: &Host,
    session: &str,
    engine: &Engine,
) -> Result<(Value, BTreeMap<String, Vec<u8>>), String> {
    host.inspection_snapshot(
        session,
        engine.scope(),
        engine.revision(),
        ExportMode::Player,
    )
    .map(|bundle| {
        let mut manifest = bundle.manifest;
        manifest["created_at_unix_ms"] = json!(0); // wall clock is not accepted state
        (manifest, bundle.files)
    })
}

fn genuine_reply(fantasy: bool, domain: u16) -> Value {
    let engine = scenario(fantasy, domain);
    assert_eq!(
        json!(engine.state().actors[PLAYER]),
        expected_actor(fantasy)
    );
    let canonical = engine.canonical_bytes();
    let history = serde_json::to_vec(engine.canonical_records()).unwrap();
    let basis = engine.accepted_history_basis().unwrap();
    let source = Arc::new(Mutex::new((engine.clone(), 0)));
    let host = Host::with_persistence(false, Box::new(ReadOnly(source.clone())));
    let resumed = call(&host, json!({"op":"resume","scope":engine.scope()}));
    assert_eq!(resumed["status"], "ok");
    let session = resumed["data"]["session"].as_str().unwrap();
    let export_before = export_state(&host, session, &engine);
    // The frozen inspection-export API is v1 only; preserve its Domain2 refusal.
    if domain == 2 {
        assert_eq!(export_before, Err("Version".into()));
    } else {
        assert!(export_before.is_ok());
    }
    let command = json!({"op":"play_presentation_v2","session":session,"scope":engine.scope(),"expected_revision":engine.revision()});
    let first = call(&host, command.clone());
    assert_eq!(first["status"], "ok", "{first}");
    assert_eq!(first["version"], 1);
    let data = &first["data"];
    assert_eq!(data["domain_version"], domain);
    assert_eq!(data["scope"], json!(engine.scope()));
    assert_eq!(data["revision"], engine.revision());
    assert_eq!(
        data["player"],
        json!({"observer":PLAYER,"self_state":expected_actor(fantasy)})
    );
    assert_eq!(
        data["rules"],
        if fantasy {
            "fantasy_v1"
        } else {
            "narrative_v1"
        }
    );
    let encoded = serde_json::to_vec(&first).unwrap();
    assert!(encoded.len() <= 65536);
    let text = String::from_utf8(encoded).unwrap();
    for canary in CANARIES.into_iter().chain([OLD, NEW, REASON, FOREIGN]) {
        assert!(!text.contains(canary), "foreign/private canary was exposed");
    }
    assert_eq!(call(&host, command), first);
    assert_eq!(export_state(&host, session, &engine), export_before);
    let saved = source.lock().unwrap();
    assert_eq!(saved.0.canonical_bytes(), canonical);
    assert_eq!(
        serde_json::to_vec(saved.0.canonical_records()).unwrap(),
        history
    );
    assert_eq!(saved.0.accepted_history_basis().unwrap(), basis);
    assert_eq!(saved.1, 0);
    first
}

fn name(fantasy: bool, domain: u16) -> String {
    format!(
        "player-self-profile-domain{domain}-{}-v1.json",
        if fantasy { "fantasy" } else { "narrative" }
    )
}

fn check_fixture(fantasy: bool, domain: u16) {
    let actual = genuine_reply(fantasy, domain);
    let asset = PathBuf::from(env!("CARGO_MANIFEST_DIR"))
        .join("../../apps/android/app/src/androidTest/assets")
        .join(name(fantasy, domain));
    let expected: Value = serde_json::from_slice(&fs::read(asset).unwrap()).unwrap();
    assert_eq!(actual, expected);
}

#[test]
fn domain_one_fantasy_profile_preserves_actual_progression_and_player_only_state() {
    check_fixture(true, 1);
}
#[test]
fn domain_two_fantasy_profile_preserves_actual_correction_and_progression() {
    check_fixture(true, 2);
}
#[test]
fn domain_one_narrative_profile_keeps_legitimate_empty_combat_fields_and_unicode() {
    check_fixture(false, 1);
}
#[test]
fn domain_two_narrative_profile_keeps_real_correction_and_empty_combat_fields() {
    check_fixture(false, 2);
}

#[test]
#[ignore = "Explicit create-only fixture capture; requires fixed owned D output"]
fn generate_genuine_player_self_profile_fixtures() {
    let out = PathBuf::from(
        std::env::var_os("LOCALLORE_SELF_PROFILE_FIXTURE_OUT").expect("explicit output required"),
    );
    assert_eq!(out, PathBuf::from("D:/Dev/Experiments/LocalLore/2026-11-01-player-self-profile-v1/native-fixtures-v1/generated-v1"));
    assert!(!out.exists());
    fs::create_dir(&out).unwrap();
    for domain in [1, 2] {
        for fantasy in [true, false] {
            let actual = genuine_reply(fantasy, domain);
            let mut bytes = serde_json::to_vec_pretty(&actual).unwrap();
            bytes.push(b'\n');
            assert!(bytes.len() <= 65536);
            let file = name(fantasy, domain);
            let mut destination = OpenOptions::new()
                .write(true)
                .create_new(true)
                .open(out.join(&file))
                .unwrap();
            destination.write_all(&bytes).unwrap();
            destination.sync_all().unwrap();
            println!("captured {file}: {} bytes", bytes.len());
        }
    }
}
