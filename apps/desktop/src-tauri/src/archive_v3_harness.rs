//! Fixed synthetic Archive3 development fixture. Root registers only under dev-harness.
//! No caller paths, statements, SQL, model, arbitrary script or general debug API.
use crate::WorkspaceState;
use locallore::{author_correction::*, contracts::*, engine::Engine};
use locallore_storage::{StorageError, Store, TurnError};
use serde_json::{json, Value};
use std::path::{Component, Path, PathBuf};

const STORY: &str = "archive-v3-controls-synthetic";
const CHILD: &str = "corrected";
const A: &str = "ARCHIVE_V3_OBSERVED_A";
const B: &str = "ARCHIVE_V3_WORLD_B";
const REASON: &str = "ARCHIVE_V3_PRIVATE_REASON";
pub fn active() -> bool {
    crate::harness::active() && std::env::var("LOCALLORE_D08_V3_HARNESS").as_deref() == Ok("1")
}
fn checked_path(path: &Path) -> Result<bool, String> {
    if !active()
        || std::env::var_os("LOCALLORE_TEST_WORKSPACE")
            .map(PathBuf::from)
            .as_deref()
            != Some(path)
    {
        return Err("Forbidden".into());
    }
    let parent = path.parent().ok_or("SyntheticWorkspaceRequired")?;
    let role = parent
        .file_name()
        .and_then(|v| v.to_str())
        .ok_or("SyntheticWorkspaceRequired")?;
    let owner = parent
        .parent()
        .and_then(Path::file_name)
        .and_then(|v| v.to_str())
        .ok_or("SyntheticWorkspaceRequired")?;
    let stage = std::env::var("LOCALLORE_D08_STAGE").map_err(|_| "SyntheticStageRequired")?;
    let source = match (role, stage.as_str()) {
        ("source-workspace", "v3-source") => true,
        (
            "destination-workspace",
            "v3-import" | "v3-restarted" | "v3-continued" | "v3-continued-restarted",
        )
        | ("uncertain-workspace", "v3-uncertain") => false,
        _ => return Err("SyntheticWorkspaceRequired".into()),
    };
    if !path.is_absolute()
        || path
            .components()
            .any(|p| matches!(p, Component::ParentDir | Component::CurDir))
        || path.file_name().and_then(|v| v.to_str()) != Some("stories-v1.sqlite")
        || !owner
            .strip_prefix("archive-v3-native-")
            .is_some_and(crate::archive::valid_id)
    {
        return Err("SyntheticWorkspaceRequired".into());
    }
    let _pins = crate::archive::pin(parent)?;
    Ok(source)
}
fn seed() -> Result<Seed, String> {
    let actor = |name: &str, location: &str| {
        json!({"name":name,"location":location,"alive":true,"energy":2,
        "abilities":{},"attributes":{},"injuries":[],"affiliations":[],"goals":[]})
    };
    serde_json::from_value(json!({"version":1,"id":"archive-v3-fixture-v1",
        "scope":{"story":STORY,"branch":"main"},"profile":"fantasy_v1","player":"player",
        "locations":["quay","tower"],"routes":[],"actors":{"player":actor("Rowan","quay"),
        "mira":actor("Mira","quay"),"sable":actor("Sable","tower")},"items":{},"abilities":{},
        "facts":{"relic-location":{"proposition":A,"discoverable_at":"quay","known_by":["mira"]}},
        "relationships":[],"story_time":100,"beliefs":[],"commitments":{}}))
    .map_err(|_| "SyntheticSeed".into())
}
fn input() -> AuthorCorrectionInputV1 {
    AuthorCorrectionInputV1 {
        version: 1,
        parent: Scope {
            story: STORY.into(),
            branch: "main".into(),
        },
        expected_parent_revision: 1,
        fork_revision: 1,
        child_branch: CHILD.into(),
        reason: REASON.into(),
        operation: AuthorCorrectionOperationV1::ReplaceFactProposition {
            fact: "relic-location".into(),
            expected_proposition: A.into(),
            replacement: B.into(),
        },
    }
}
fn core_discover(engine: &mut Engine, turn: &str) -> Result<(), String> {
    let request = engine.request(
        turn,
        Intent::Actions(vec![Command::Discover {
            fact: "relic-location".into(),
        }]),
    );
    let proposal = Engine::proposal(&request).map_err(|_| "SyntheticProposal")?;
    let receipt = engine
        .preview(&request, &proposal)
        .map_err(|_| "SyntheticPreview")?;
    engine
        .commit_prepared(&receipt)
        .map_err(|_| "SyntheticCommit")?;
    Ok(())
}
fn expected() -> Result<(Engine, Engine), String> {
    let mut root = Engine::new(seed()?).map_err(|_| "SyntheticEngine")?;
    core_discover(&mut root, "observe-before-author")?;
    let plan = root
        .prepare_author_correction(&input(), &|| false)
        .map_err(|_| "SyntheticAuthorPrepare")?;
    let mut child = root
        .apply_author_correction(&plan, &|| false)
        .map_err(|_| "SyntheticAuthorApply")?
        .engine;
    core_discover(&mut child, "discover-corrected")?;
    Ok((root, child))
}
fn same(actual: &Engine, expected: &Engine) -> Result<(), String> {
    if actual.seed() != expected.seed()
        || actual.scope() != expected.scope()
        || actual.domain_version() != expected.domain_version()
        || actual.revision() != expected.revision()
        || actual.canonical_records() != expected.canonical_records()
        || actual.canonical_bytes() != expected.canonical_bytes()
        || actual
            .accepted_history_basis()
            .map_err(|_| "SyntheticBasis")?
            != expected
                .accepted_history_basis()
                .map_err(|_| "SyntheticBasis")?
    {
        return Err("SyntheticCanonicalMismatch".into());
    }
    for actor in ["player", "mira", "sable"] {
        if actual
            .character_context_v2(actor, actual.scope(), actual.revision())
            .map_err(|_| "SyntheticContext")?
            != expected
                .character_context_v2(actor, expected.scope(), expected.revision())
                .map_err(|_| "SyntheticContext")?
            || actual
                .actor_receipts_v2(actor, actual.scope(), actual.revision())
                .map_err(|_| "SyntheticViews")?
                != expected
                    .actor_receipts_v2(actor, expected.scope(), expected.revision())
                    .map_err(|_| "SyntheticViews")?
        {
            return Err("SyntheticObserverMismatch".into());
        }
    }
    Ok(())
}
fn prepare(path: &Path) -> Result<(), String> {
    if !checked_path(path)? || std::env::var("LOCALLORE_TEST_RESTART").as_deref() == Ok("1") {
        return Err("SyntheticFreshSourceRequired".into());
    }
    let mut store = Store::open_application(path).map_err(|_| "SyntheticOpen")?;
    if !store.stories().map_err(|_| "SyntheticLibrary")?.is_empty() {
        return Err("SyntheticFreshSourceRequired".into());
    }
    let seed = seed()?;
    let root = seed.scope.clone();
    store
        .create_story("Synthetic corrected archive fixture", seed)
        .map_err(|_| "SyntheticStory")?;
    for (scope, turn) in [
        (root.clone(), "observe-before-author"),
        (
            Scope {
                story: STORY.into(),
                branch: CHILD.into(),
            },
            "discover-corrected",
        ),
    ] {
        if scope.branch == CHILD {
            let plan = store
                .prepare_author_correction(&input(), &|| false)
                .map_err(|_| "SyntheticAuthorPrepare")?;
            store
                .apply_author_correction(&plan, &|| false)
                .map_err(|_| "SyntheticAuthorApply")?;
        }
        let engine = store.resume(&scope).map_err(|_| "SyntheticResume")?.engine;
        let request = engine.request(
            turn,
            Intent::Actions(vec![Command::Discover {
                fact: "relic-location".into(),
            }]),
        );
        let proposal = Engine::proposal(&request).map_err(|_| "SyntheticProposal")?;
        let receipt = engine
            .preview(&request, &proposal)
            .map_err(|_| "SyntheticPreview")?;
        store.begin_turn(&request).map_err(|_| "SyntheticBegin")?;
        store
            .commit_prepared(&receipt)
            .map_err(|_| "SyntheticCommit")?;
    }
    Ok(())
}
fn oracle(path: &Path) -> Result<Value, String> {
    let source_role = checked_path(path)?;
    let mut store = Store::open_read_only(path).map_err(|_| "SyntheticRead")?;
    let (root, mut child) = expected()?;
    let stage = std::env::var("LOCALLORE_D08_STAGE").map_err(|_| "SyntheticStageRequired")?;
    let stories = store.stories().map_err(|_| "SyntheticLibrary")?;
    let mut foreign = None;
    for story in &stories {
        if story.scope.story == STORY {
            continue;
        }
        if source_role || foreign.is_some() {
            return Err("SyntheticForeignIdentity".into());
        }
        let actual = store
            .resume(&story.scope)
            .map_err(|_| "SyntheticForeignRead")?
            .engine;
        let mut original: Seed =
            serde_json::from_str(include_str!("../../../../fixtures/lantern_quay.json"))
                .map_err(|_| "SyntheticControlSeed")?;
        if !actual
            .scope()
            .story
            .strip_prefix("quay-")
            .is_some_and(|v| v.len() == 32 && v.bytes().all(|b| b.is_ascii_hexdigit()))
        {
            return Err("SyntheticForeignIdentity".into());
        }
        original.scope = actual.scope().clone();
        let expected = Engine::new(original).map_err(|_| "SyntheticControlEngine")?;
        same(&actual, &expected)?;
        foreign = Some(json!({"scope":actual.scope(),"revision":actual.revision(),
            "canonical_sha256":locallore::inspection::sha256(&actual.canonical_bytes())}));
    }
    if !source_role && foreign.is_none() {
        return Err("SyntheticForeignMissing".into());
    }
    let actual = match store.resume(child.scope()) {
        Ok(value) => Some(value.engine),
        Err(TurnError::Storage(StorageError::NotFound)) => None,
        Err(_) => return Err("SyntheticChildRead".into()),
    };
    let present = actual.is_some();
    let mut digest = None;
    if let Some(actual) = actual {
        // Read-only oracle for the one actual UI fixture action. Derive its
        // expected receipt through Core; never copy accepted authority or write.
        if actual.revision() == 4
            && matches!(stage.as_str(), "v3-continued" | "v3-continued-restarted")
        {
            let last = actual
                .canonical_records()
                .last()
                .and_then(CanonicalRecord::receipt)
                .ok_or("SyntheticContinuationReceipt")?;
            let request = child.request(
                &last.request().turn,
                Intent::Actions(vec![Command::Wait { ticks: 1 }]),
            );
            if last.request() != &request {
                return Err("SyntheticContinuationRequest".into());
            }
            let proposal = Engine::proposal(&request).map_err(|_| "SyntheticProposal")?;
            let receipt = child
                .preview(&request, &proposal)
                .map_err(|_| "SyntheticPreview")?;
            child
                .commit_prepared(&receipt)
                .map_err(|_| "SyntheticCommit")?;
        }
        if stage == "v3-continued-restarted" && actual.revision() != 4 {
            return Err("SyntheticContinuationMissing".into());
        }
        same(
            &store
                .resume(root.scope())
                .map_err(|_| "SyntheticParentRead")?
                .engine,
            &root,
        )?;
        same(&actual, &child)?;
        let player = actual
            .observed_facts("player", actual.scope(), actual.revision())
            .map_err(|_| "SyntheticPlayer")?;
        let mira = actual
            .observed_facts("mira", actual.scope(), actual.revision())
            .map_err(|_| "SyntheticMira")?;
        let sable = actual
            .observed_facts("sable", actual.scope(), actual.revision())
            .map_err(|_| "SyntheticSable")?;
        if player
            .get("relic-location")
            .is_none_or(|v| v.proposition != B)
            || mira
                .get("relic-location")
                .is_none_or(|v| v.proposition != A)
            || sable.contains_key("relic-location")
        {
            return Err("SyntheticKnowledgeMismatch".into());
        }
        let records =
            serde_json::to_vec(actual.canonical_records()).map_err(|_| "SyntheticRecords")?;
        digest = Some(
            json!({"canonical_sha256":locallore::inspection::sha256(&records),
            "basis_equal":true,"full_records_equal":true,"accepted_records":actual.canonical_record_count(),
            "all_actor_contexts_and_views_equal":true,"player_current_mira_prior_sable_unaware":true}),
        );
    } else if stories.iter().any(|s| s.scope.story == STORY) {
        return Err("SyntheticPartialStory".into());
    }
    if source_role && !present {
        return Err("SyntheticSourceMissing".into());
    }
    Ok(
        json!({"version":1,"synthetic":true,"evidence":"actual-read-only-Store-Core-fixed-fixture",
        "source_present":present,"root":root.scope(),"child":child.scope(),"expected_revision":child.revision(),
        "expected_accepted_records":child.canonical_record_count(),"player":"player","foreign":foreign,"proof":digest}),
    )
}
#[tauri::command]
pub async fn harness_archive_v3_fixture(
    window: tauri::WebviewWindow,
    workspace: tauri::State<'_, WorkspaceState>,
    scenario: String,
) -> Result<Value, String> {
    if !active() {
        return Err("Forbidden".into());
    }
    if !["prepare-source", "read-current-fixture"].contains(&scenario.as_str()) {
        return Err("InvalidArchiveFixture".into());
    }
    checked_path(&workspace.path)?;
    let epoch = workspace
        .lease
        .capture(window.label())
        .map_err(str::to_owned)?;
    let lease = workspace.lease.clone();
    let path = workspace.path.clone();
    tauri::async_runtime::spawn_blocking(move || {
        lease.dispatch(epoch, || {
            if scenario == "prepare-source" {
                prepare(&path)?;
            }
            oracle(&path)
        })
    })
    .await
    .map_err(|_| "SyntheticFixtureWorker".to_owned())?
}
