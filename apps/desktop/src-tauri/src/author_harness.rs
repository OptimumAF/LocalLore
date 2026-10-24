//! Fixed synthetic development fixture/oracles. Never compiled into normal builds.
use crate::{archive::Work, WorkspaceState};
use locallore::{author_correction::*, contracts::*, engine::Engine};
use locallore_storage::Store;
use serde_json::{json, Value};
use std::{
    path::{Component, Path, PathBuf},
    sync::atomic::{AtomicU8, Ordering},
    time::{Duration, Instant},
};

const CHILDREN: &[&str] = &[
    "author-saved",
    "author-cancelled",
    "author-late",
    "author-unknown",
    "author-known-ack",
    "author-stale",
];
const A: &str = "AUTHOR_OBSERVED_A";
const B: &str = "AUTHOR_WORLD_B";
const REASON: &str = "AUTHOR_PRIVATE_REASON";
// 0 idle, 1/2 armed before/after, 3/4 entered before/after. One actual worker.
static GATE: AtomicU8 = AtomicU8::new(0);
pub fn active() -> bool {
    crate::harness::author_active()
}
fn workspace_path() -> Result<PathBuf, String> {
    if !active() {
        return Err("Forbidden".into());
    }
    let path = std::env::var_os("LOCALLORE_TEST_WORKSPACE")
        .map(PathBuf::from)
        .ok_or("SyntheticWorkspaceRequired")?;
    let parent = path.parent().ok_or("SyntheticWorkspaceRequired")?;
    let leaf = parent
        .file_name()
        .and_then(|n| n.to_str())
        .ok_or("SyntheticWorkspaceRequired")?;
    if !path.is_absolute()
        || path
            .components()
            .any(|p| matches!(p, Component::ParentDir | Component::CurDir))
        || path.file_name().and_then(|n| n.to_str()) != Some("stories-v1.sqlite")
        || !leaf
            .strip_prefix("author-native-")
            .is_some_and(crate::archive::valid_id)
    {
        return Err("SyntheticWorkspaceRequired".into());
    }
    Ok(path)
}
fn fixture_seed(story: &str) -> Result<Seed, String> {
    let mut seed: Seed =
        serde_json::from_str(include_str!("../../../../fixtures/lantern_quay.json"))
            .map_err(|_| "SyntheticSeed")?;
    seed.scope.story = story.into();
    let fact = seed
        .facts
        .get_mut("relic-location")
        .ok_or("SyntheticFact")?;
    fact.proposition = A.into();
    fact.discoverable_at = Some("quay".into());
    fact.known_by = [seed.player.clone(), "mira".into()].into();
    Ok(seed)
}
fn parent_fixture() -> Result<(Seed, Engine, Receipt), String> {
    let seed = fixture_seed("author-controls-synthetic")?;
    let mut engine = Engine::new(seed.clone()).map_err(|_| "SyntheticEngine")?;
    let request = engine.request(
        "author-parent-message",
        Intent::Dialogue {
            text: "AUTHOR_PARENT_MIRA_ONLY".into(),
            audience: ["mira".into()].into(),
        },
    );
    let proposal = Engine::proposal(&request).map_err(|_| "SyntheticProposal")?;
    let approved = engine
        .preview(&request, &proposal)
        .map_err(|_| "SyntheticPreview")?;
    let receipt = engine
        .commit_prepared(&approved)
        .map_err(|_| "SyntheticReceipt")?;
    Ok((seed, engine, receipt))
}
fn input(child: &str) -> AuthorCorrectionInputV1 {
    AuthorCorrectionInputV1 {
        version: 1,
        parent: Scope {
            story: "author-controls-synthetic".into(),
            branch: "main".into(),
        },
        expected_parent_revision: 1,
        fork_revision: 1,
        child_branch: child.into(),
        operation: AuthorCorrectionOperationV1::ReplaceFactProposition {
            fact: "relic-location".into(),
            expected_proposition: A.into(),
            replacement: B.into(),
        },
        reason: REASON.into(),
    }
}
/// Only called once by native setup before opening the application's Repository.
pub fn seed(path: &Path) -> Result<(), String> {
    if workspace_path()? != path
        || path.exists()
        || std::env::var("LOCALLORE_TEST_RESTART").as_deref() == Ok("1")
    {
        return Err("SyntheticFreshWorkspaceRequired".into());
    }
    let _pins = crate::archive::pin(path.parent().ok_or("SyntheticWorkspaceRequired")?)?;
    let (seed, _, receipt) = parent_fixture()?;
    let mut store = Store::create_new_pinned(path).map_err(|_| "SyntheticCreate")?;
    store
        .create_story("Synthetic author correction", seed)
        .map_err(|_| "SyntheticStory")?;
    store
        .begin_turn(receipt.request())
        .map_err(|_| "SyntheticBegin")?;
    store
        .commit_prepared(&receipt)
        .map_err(|_| "SyntheticCommit")?;
    store
        .create_story(
            "Other synthetic author story",
            fixture_seed("author-controls-other")?,
        )
        .map_err(|_| "SyntheticOther")?;
    Ok(())
}
fn wait_gate(work: &Work, after: bool) -> Result<(), String> {
    if !active() {
        return Ok(());
    }
    let armed = if after { 2 } else { 1 };
    let entered = armed + 2;
    if GATE
        .compare_exchange(armed, entered, Ordering::SeqCst, Ordering::SeqCst)
        .is_err()
    {
        return Ok(());
    }
    let started = Instant::now();
    while GATE.load(Ordering::SeqCst) == entered {
        if work.cancelled() {
            let _ = GATE.compare_exchange(entered, 0, Ordering::SeqCst, Ordering::SeqCst);
            return if after {
                Ok(())
            } else {
                Err("Cancelled".into())
            };
        }
        if started.elapsed() >= Duration::from_secs(30) {
            let _ = GATE.compare_exchange(entered, 0, Ordering::SeqCst, Ordering::SeqCst);
            return if after {
                Ok(())
            } else {
                Err("AuthorHarnessDeadline".into())
            };
        }
        std::thread::sleep(Duration::from_millis(10));
    }
    Ok(())
}
pub fn before_apply(work: &Work) -> Result<(), String> {
    wait_gate(work, false)
}
/// A late cancel or harness timeout can never demote an actual committed result.
pub fn after_apply(work: &Work) {
    let _ = wait_gate(work, true);
}

fn oracle() -> Result<Value, String> {
    let path = workspace_path()?;
    let _pins = crate::archive::pin(&path)?;
    if std::fs::metadata(&path)
        .map_err(|_| "SyntheticMetadata")?
        .len()
        > 64 * 1024 * 1024
    {
        return Err("SyntheticBudget".into());
    }
    let mut store = Store::open_read_only(&path).map_err(|_| "SyntheticReadOnly")?;
    let (_, expected, _) = parent_fixture()?;
    let parent = store
        .resume(expected.scope())
        .map_err(|_| "SyntheticParent")?
        .engine;
    let parent_records =
        serde_json::to_vec(parent.canonical_records()).map_err(|_| "SyntheticParentRecords")?;
    let expected_records =
        serde_json::to_vec(expected.canonical_records()).map_err(|_| "SyntheticExpectedRecords")?;
    if parent.canonical_bytes() != expected.canonical_bytes()
        || parent.seed() != expected.seed()
        || parent_records != expected_records
    {
        return Err("SyntheticParentChanged".into());
    }
    let mut children = serde_json::Map::new();
    for child in CHILDREN {
        let request = input(child);
        let outcome = store
            .lookup_author_correction(&request, &|| false)
            .map_err(|_| "SyntheticLookup")?;
        let Some(outcome) = outcome else {
            children.insert((*child).into(), json!({"found":false}));
            continue;
        };
        if ["author-cancelled", "author-stale"].contains(child) {
            return Err("SyntheticUnexpectedChild".into());
        }
        let engine = store
            .resume(&outcome.scope)
            .map_err(|_| "SyntheticChild")?
            .engine;
        let mut authors = 0;
        for record in engine.canonical_records() {
            if let CanonicalRecord::AuthorV1(author) = record {
                authors += 1;
                let value = serde_json::to_value(author).map_err(|_| "SyntheticReceiptJson")?;
                if author.input() != &request || value["witnesses"] != json!([]) {
                    return Err("SyntheticAuthorRecord".into());
                }
            }
        }
        let truth = locallore::inspection_query::query(
            &engine,
            &locallore::inspection_query::Query {
                version: 2,
                scope: engine.scope().clone(),
                expected_head: engine.revision(),
                at_revision: None,
                observer: locallore::inspection_query::Observer::Omniscient,
                view: locallore::inspection_query::View::Knowledge,
                cursor: None,
                limit: 64,
                search: String::new(),
            },
            true,
        )
        .map_err(|_| "SyntheticTruthQuery")?;
        if authors != 1
            || !serde_json::to_string(&truth)
                .map_err(|_| "SyntheticTruthJson")?
                .contains(B)
        {
            return Err("SyntheticAuthorCountOrTruth".into());
        }
        for observer in [engine.seed().player.as_str(), "mira"] {
            let context = engine
                .character_context_v2(observer, engine.scope(), engine.revision())
                .map_err(|_| "SyntheticActorContext")?;
            let serialized = serde_json::to_string(&context).map_err(|_| "SyntheticContextJson")?;
            if !serialized.contains(A) || serialized.contains(B) || serialized.contains(REASON) {
                return Err("SyntheticOldKnowerChanged".into());
            }
            let views = engine
                .actor_receipts_v2(observer, engine.scope(), engine.revision())
                .map_err(|_| "SyntheticActorReceipts")?;
            let views = serde_json::to_value(views).map_err(|_| "SyntheticViewsJson")?;
            if views
                .as_array()
                .ok_or("SyntheticViews")?
                .iter()
                .any(|receipt| {
                    receipt["events"]
                        .as_array()
                        .is_none_or(|events| events.iter().any(|e| e["event"]["sequence"] == 2))
                })
            {
                return Err("SyntheticAuthorObservation".into());
            }
        }
        let sable = engine
            .character_context_v2("sable", engine.scope(), engine.revision())
            .map_err(|_| "SyntheticSable")?;
        let sable = serde_json::to_string(&sable).map_err(|_| "SyntheticSableJson")?;
        if [A, B, REASON, "AUTHOR_PARENT_MIRA_ONLY"]
            .iter()
            .any(|text| sable.contains(text))
        {
            return Err("SyntheticObserverLeak".into());
        }
        children.insert((*child).into(), json!({"found":true,"head":engine.revision(),"author_records":authors,"created":outcome.created,"actor_author_observations":0,"old_knowers_preserved":true,"canonical_sha256":locallore::inspection::sha256(&engine.canonical_bytes())}));
    }
    Ok(
        json!({"version":1,"synthetic":true,"evidence":"actual-read-only-Store-Core-oracle","parent_preserved":true,"parent_head":parent.revision(),"parent_sha256":locallore::inspection::sha256(&parent_records),"children":children}),
    )
}
#[tauri::command]
pub async fn harness_author_case(
    window: tauri::WebviewWindow,
    workspace: tauri::State<'_, WorkspaceState>,
    action: String,
) -> Result<Value, String> {
    if !active() {
        return Err("Forbidden".into());
    }
    if workspace_path()? != workspace.path {
        return Err("SyntheticWorkspaceMismatch".into());
    }
    let epoch = workspace
        .lease
        .capture(window.label())
        .map_err(str::to_owned)?;
    match action.as_str() {
        "hold-before" | "hold-after" => workspace.lease.dispatch(epoch, || {
            let armed = if action == "hold-before" { 1 } else { 2 };
            GATE.compare_exchange(0, armed, Ordering::SeqCst, Ordering::SeqCst).map_err(|_| "AuthorHarnessBusy")?;
            Ok(json!({"armed":true}))
        }),
        "release" => workspace.lease.dispatch(epoch, || { GATE.store(0, Ordering::SeqCst); Ok(json!({"released":true})) }),
        "gate-state" => workspace.lease.dispatch(epoch, || {
            let state = GATE.load(Ordering::SeqCst);
            Ok(json!({"version":1,"entered":state >= 3,"mode":match state {1|3=>"before",2|4=>"after",_=>"idle"}}))
        }),
        "oracle" => {
            let lease = workspace.lease.clone();
            tauri::async_runtime::spawn_blocking(move || lease.dispatch(epoch, oracle)).await.map_err(|_| "SyntheticOracleWorker".to_owned())?
        }
        _ => Err("InvalidAuthorFixture".into()),
    }
}
