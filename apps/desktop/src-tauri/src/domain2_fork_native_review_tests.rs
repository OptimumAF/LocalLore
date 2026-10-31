//! Independent source FIRST, 7c8f3417. UNREGISTERED/UNCOMPILED/UNRUN.
//! Register as cfg(test) child of harness.rs. Actual Core/Store and future fixed
//! domain2_fork_harness::{seed,oracle,validate_mode,allowed_action}; no SQL/provider.
//! tests/harness_contract.rs must also register that PURE module by path; it
//! cannot depend on WorkspaceState/Tauri or crate::exports. Only the primary
//! binary filter executes the one fixture; all-target lint merely compiles both.
//! One retained D TEMP unit root, including DB sidecars <=8MiB; never cleanup.
//! Oracle protocol freeze: {version:1,kind:domain2_fork_native_oracle_v1,
//! fixture_version:1,scopes:[four fixed rows then sorted UUID children],children}.
//! Rows have Core fields below + turns_sha256. The original four turns hashes
//! observe OWN-scope public lookups, including UnknownTurn for inherited play.
//! They are not whole SQL tables. UUID children use turns_sha256:null; expected
//! Core proof excludes that field entirely, never fabricates inherited turn rows.
use super::ArtifactBudget;
use crate::domain2_fork_harness::{allowed_action, oracle, seed, validate_mode};
use locallore::{
    author_correction::{AuthorCorrectionInputV1, AuthorCorrectionOperationV1, CanonicalRecord},
    contracts::{Command, Intent, Scope, Seed},
    engine::Engine,
};
use locallore_storage::{ForkRequest, Store, TurnError, TurnPhase};
use serde_json::{json, Value};
use sha2::{Digest, Sha256};
use std::{
    fs,
    path::{Path, PathBuf},
    time::{SystemTime, UNIX_EPOCH},
};

const PRIMARY: &str = "d08-fork-native";
const OTHER: &str = "d08-fork-other";
const TURN: &str = "d08-domain2-fork-prefix";
const SAY: &str = "D08_PREFIX_MIRA_ONLY_421";
const TRUTH: &str = "D08_PRIVATE_AUTHOR_TRUTH_422";
const REASON: &str = "D08_PRIVATE_AUTHOR_REASON_423";
const OTHER_TRUTH: &str = "D08_OTHER_STORY_TRUTH_424";
// Caller must freshly reconcile this retained baseline before any execution.
const MAX_FIXTURE_BYTES: u64 = 8 * 1024 * 1024 - 528_384;
fn scope(story: &str, branch: &str) -> Scope {
    Scope {
        story: story.into(),
        branch: branch.into(),
    }
}
fn base(other: bool) -> Seed {
    let mut value: Seed =
        serde_json::from_str(include_str!("../../../../fixtures/lantern_quay.json")).unwrap();
    value.scope = scope(if other { OTHER } else { PRIMARY }, "main");
    if other {
        value.facts.get_mut("beacon-mark").unwrap().proposition = OTHER_TRUTH.into();
    }
    value
}
fn author() -> AuthorCorrectionInputV1 {
    AuthorCorrectionInputV1 {
        version: 1,
        parent: scope(PRIMARY, "main"),
        expected_parent_revision: 2,
        fork_revision: 2,
        child_branch: "authored".into(),
        operation: AuthorCorrectionOperationV1::ReplaceFactProposition {
            fact: "beacon-mark".into(),
            expected_proposition: base(false).facts["beacon-mark"].proposition.clone(),
            replacement: TRUTH.into(),
        },
        reason: REASON.into(),
    }
}
fn engines() -> Vec<Engine> {
    let mut root = Engine::new(base(false)).unwrap();
    let request = root.request(
        TURN,
        Intent::Actions(vec![
            Command::Say {
                text: SAY.into(),
                audience: ["mira".into()].into(),
            },
            Command::Wait { ticks: 1 },
        ]),
    );
    let receipt = root
        .preview(&request, &Engine::proposal(&request).unwrap())
        .unwrap();
    assert_eq!(receipt.events().len(), 2);
    root.commit_prepared(&receipt).unwrap();
    let prepared = root
        .prepare_author_correction(&author(), &|| false)
        .unwrap();
    let authored = root
        .apply_author_correction(&prepared, &|| false)
        .unwrap()
        .engine;
    let sibling = root.fork("sibling", 2).unwrap();
    vec![root, authored, sibling, Engine::new(base(true)).unwrap()]
}
fn digest(bytes: &[u8]) -> String {
    format!("{:x}", Sha256::digest(bytes))
}
fn hash_json<T: serde::Serialize + ?Sized>(value: &T) -> String {
    digest(&serde_json::to_vec(value).unwrap())
}
fn core_row(engine: &Engine) -> Value {
    let actors = [engine.seed().player.as_str(), "mira", "oren", "sable"]
        .into_iter()
        .map(|id| {
            (
                id,
                engine
                    .character_context_v2(id, engine.scope(), engine.revision())
                    .unwrap(),
                engine
                    .actor_receipts_v2(id, engine.scope(), engine.revision())
                    .unwrap(),
            )
        })
        .collect::<Vec<_>>();
    json!({"scope":engine.scope(),"domain_version":engine.domain_version(),"head":engine.revision(),
        "story_time":engine.state().story_time,"boundaries":engine.completed_boundaries(),
        "canonical_records":engine.canonical_record_count(),"ordinary_receipts":engine.receipts().len(),
        "seed_sha256":hash_json(engine.seed()),"projection_sha256":digest(&engine.canonical_bytes()),
        "records_sha256":hash_json(engine.canonical_records()),"receipts_sha256":hash_json(engine.receipts()),
        "actors_sha256":hash_json(&actors)})
}
fn turns_hash(store: &mut Store, engine: &Engine) -> String {
    let ordinary=engine.receipts().iter().map(|receipt| {
        let turn=&receipt.request().turn;
        match store.lookup_turn(engine.scope(),turn) {
            Ok(saved)=>{assert!(matches!(saved.phase,TurnPhase::Committed));json!({"turn":turn,"status":"committed","request":saved.request,"receipt":saved.receipt})},
            Err(TurnError::UnknownTurn)=>json!({"turn":turn,"status":"unknown_turn"}),
            Err(error)=>panic!("unexpected own-scope lookup: {error}"),
        }
    }).collect::<Vec<_>>();
    let mut authors = Vec::new();
    for record in engine.canonical_records() {
        if let CanonicalRecord::AuthorV1(record) = record {
            // This is the fixed actual author lookup, not fabricated SQL rows.
            if record.scope() == engine.scope() {
                let found = store
                    .lookup_author_correction(record.input(), &|| false)
                    .unwrap()
                    .unwrap();
                authors.push(json!({"scope":found.scope,"parent":found.parent,"fork_revision":found.fork_revision,
                    "author_revision":found.author_revision,"head_revision":found.head_revision,"created":found.created}));
            }
        }
    }
    hash_json(&json!({"ordinary":ordinary,"author":authors}))
}
fn neutral(value: &Value) {
    assert!(serde_json::to_vec(value).unwrap().len() <= 32768);
    let text = serde_json::to_string_pretty(value).unwrap();
    assert!(text.len() <= 32768);
    for marker in [
        SAY,
        TRUTH,
        REASON,
        OTHER_TRUTH,
        "SECRET-TIDE-731",
        "self_state",
        "proposition",
        "known_by",
        "coverage",
        "original_input",
    ] {
        assert!(!text.contains(marker), "neutral oracle leaks {marker}");
    }
    let object = value.as_object().unwrap();
    let mut keys = object.keys().map(String::as_str).collect::<Vec<_>>();
    keys.sort();
    assert_eq!(
        keys,
        ["children", "fixture_version", "kind", "scopes", "version"]
    );
    assert_eq!(value["kind"], "domain2_fork_native_oracle_v1");
    assert_eq!(value["version"], 1);
    assert_eq!(value["fixture_version"], 1);
}
fn inventory(directory: &Path) -> Vec<(PathBuf, u64, String)> {
    fn visit(root: &Path, here: &Path, out: &mut Vec<(PathBuf, u64, String)>) {
        for entry in fs::read_dir(here).unwrap() {
            let path = entry.unwrap().path();
            let metadata = fs::symlink_metadata(&path).unwrap();
            assert!(!metadata.file_type().is_symlink());
            if metadata.is_dir() {
                visit(root, &path, out);
            } else {
                assert!(metadata.is_file());
                assert!(metadata.len() <= MAX_FIXTURE_BYTES);
                out.push((
                    path.strip_prefix(root).unwrap().into(),
                    metadata.len(),
                    digest(&fs::read(&path).unwrap()),
                ));
            }
            assert!(out.len() <= 64);
        }
    }
    let mut out = Vec::new();
    visit(directory, directory, &mut out);
    out.sort();
    assert!(out.iter().map(|row| row.1).sum::<u64>() <= MAX_FIXTURE_BYTES);
    out
}

#[test]
fn closed_flag_and_action_admission_never_changes_legacy_absence() {
    for development in [false, true] {
        for conflict in [false, true] {
            for alias in [false, true] {
                assert_eq!(validate_mode(None, development, conflict, alias), Ok(false));
                assert_eq!(
                    validate_mode(Some("1"), development, conflict, alias),
                    if development && !conflict && !alias {
                        Ok(true)
                    } else {
                        Err("Forbidden".into())
                    }
                );
            }
        }
    }
    for value in ["", "0", "true", " 1", "1 ", "雪"] {
        assert_eq!(
            validate_mode(Some(value), true, false, false),
            Err("Forbidden".into())
        );
    }
    for action in ["hold", "release", "lose-ack", "domain2-oracle"] {
        assert!(allowed_action(action));
    }
    for action in [
        "advance-parent",
        "oracle",
        "seed",
        "domain2-oracle/x",
        "Domain2-oracle",
        "",
        "../escape",
    ] {
        assert!(!allowed_action(action));
    }
}
#[test]
fn existing_counter_enforces_eight_mib_and_permanent_failure() {
    let cap = 8 * 1024 * 1024;
    let mut budget = ArtifactBudget::default();
    assert_eq!(budget.reserve_with_limit(cap - 1, cap), Ok(()));
    assert_eq!(budget.reserve_with_limit(1, cap), Ok(()));
    assert_eq!(budget.reserve_with_limit(0, cap), Ok(()));
    assert_eq!(
        budget.reserve_with_limit(1, cap),
        Err("ArtifactWriteBudget")
    );
    assert_eq!(budget.reserved, cap);
    assert!(budget.failed);
    assert_eq!(
        budget.reserve_with_limit(0, cap),
        Err("ArtifactWriteBudget")
    );
    let mut overflow = ArtifactBudget {
        reserved: usize::MAX,
        failed: false,
    };
    assert_eq!(
        overflow.reserve_with_limit(1, cap),
        Err("ArtifactWriteBudget")
    );
    assert!(overflow.failed);
    // Counter placement only; no eight-MiB filesystem allocation or actual mode writer claim.
}
#[test]
#[cfg(windows)]
fn one_actual_fixed_fixture_and_core_prefix_children_have_neutral_readonly_proofs() {
    // Root later admits this one retained unit root; no fallback location or Drop cleanup.
    let parent =
        fs::canonicalize(std::env::temp_dir()).expect("SETUP_UNRUN: admitted existing D TEMP");
    use std::path::{Component, Prefix};
    assert!(
        matches!(parent.components().next(),Some(Component::Prefix(prefix)) if
        matches!(prefix.kind(),Prefix::Disk(drive)|Prefix::VerbatimDisk(drive) if drive.eq_ignore_ascii_case(&b'D'))),
        "SETUP_UNRUN: physical D Windows TEMP"
    );
    for ancestor in parent.ancestors() {
        let metadata = fs::symlink_metadata(ancestor).unwrap();
        assert!(metadata.is_dir() && !metadata.file_type().is_symlink());
        #[cfg(windows)]
        {
            use std::os::windows::fs::MetadataExt;
            assert_eq!(metadata.file_attributes() & 0x400, 0);
        }
    }
    let stamp = SystemTime::now()
        .duration_since(UNIX_EPOCH)
        .unwrap()
        .as_nanos();
    let directory = parent.join(format!(
        "d08-domain2-fork-native-unit-{}-{stamp}",
        std::process::id()
    ));
    fs::create_dir(&directory).unwrap();
    // Fixed valid UUID leaves live under the one uniquely retained unit root.
    let uuid = "00000000-0000-4000-8000-000000000099";
    let packet = directory.join(format!("p-{uuid}"));
    fs::create_dir(&packet).unwrap();
    let workspace = packet.join(format!("d08-domain2-fork-native-{uuid}"));
    fs::create_dir(&workspace).unwrap();
    let database = workspace.join("stories-v1.sqlite");
    let wrong = workspace.join("unowned.sqlite");
    assert!(seed(&wrong).is_err());
    assert!(!wrong.exists());
    seed(&database).unwrap();
    let seeded = inventory(&directory);
    assert!(seed(&database).is_err());
    assert_eq!(inventory(&directory), seeded);
    let baseline = oracle(&database).unwrap();
    neutral(&baseline);
    assert_eq!(inventory(&directory), seeded);
    assert_eq!(baseline["children"], json!([]));
    let expected = engines();
    let rows = baseline["scopes"].as_array().unwrap();
    assert_eq!(rows.len(), 4);
    let mut store = Store::open_read_only(&database).unwrap();
    for (index, engine) in expected.iter().enumerate() {
        let mut row = core_row(engine);
        row["turns_sha256"] = json!(turns_hash(&mut store, engine));
        assert_eq!(rows[index], row);
    }
    assert_eq!(rows[0]["boundaries"], json!([0, 2]));
    assert_eq!(rows[1]["boundaries"], json!([0, 2, 3]));
    assert_eq!(rows[1]["canonical_records"], 2);
    assert_eq!(rows[1]["ordinary_receipts"], 1);
    // Actor visibility remains Core-derived: Mira heard the prefix, Sable did not.
    assert!(serde_json::to_string(
        &expected[1]
            .actor_receipts_v2("mira", expected[1].scope(), 3)
            .unwrap()
    )
    .unwrap()
    .contains(SAY));
    assert!(!serde_json::to_string(
        &expected[1]
            .actor_receipts_v2("sable", expected[1].scope(), 3)
            .unwrap()
    )
    .unwrap()
    .contains(SAY));
    drop(store);
    let ids = [
        "00000000-0000-4000-8000-000000000001",
        "00000000-0000-4000-8000-000000000002",
        "00000000-0000-4000-8000-000000000003",
    ];
    let mut store = Store::open_application(&database).unwrap();
    for (at, id) in [0, 2, 3].into_iter().zip(ids) {
        let result = store
            .fork_branch(
                &ForkRequest {
                    parent: scope(PRIMARY, "authored"),
                    child_branch: id.into(),
                    expected_parent_revision: 3,
                    at_revision: at,
                },
                &|| false,
            )
            .unwrap();
        assert!(result.created);
    }
    drop(store);
    let before = inventory(&directory);
    let observed = oracle(&database).unwrap();
    neutral(&observed);
    assert_eq!(inventory(&directory), before);
    let rows = observed["scopes"].as_array().unwrap();
    assert_eq!(&rows[..4], baseline["scopes"].as_array().unwrap());
    assert_eq!(rows.len(), 7);
    let children = observed["children"].as_array().unwrap();
    assert_eq!(children.len(), 3);
    let mut store = Store::open_read_only(&database).unwrap();
    for (index, (at, id)) in [0, 2, 3].into_iter().zip(ids).enumerate() {
        let expected_child = expected[1].fork(id, at).unwrap();
        let actual = store.resume(expected_child.scope()).unwrap().engine;
        assert_eq!(core_row(&actual), core_row(&expected_child));
        let mut row = core_row(&actual);
        row["turns_sha256"] = Value::Null;
        assert_eq!(rows[index + 4], row);
        assert_eq!(
            children[index],
            json!({"scope":actual.scope(),"parent":scope(PRIMARY,"authored"),"fork_revision":at,"core_prefix_matches":true,"expected":core_row(&expected_child)})
        );
        assert!(children[index]["expected"].get("turns_sha256").is_none());
    }
    drop(store);
    let mut store = Store::open_application(&database).unwrap();
    store
        .fork_branch(
            &ForkRequest {
                parent: scope(PRIMARY, "authored"),
                child_branch: "unexpected-child".into(),
                expected_parent_revision: 3,
                at_revision: 2,
            },
            &|| false,
        )
        .unwrap();
    drop(store);
    let before = inventory(&directory);
    assert_eq!(oracle(&database), Err("SyntheticFixtureInvalid".into()));
    assert_eq!(inventory(&directory), before);
}
