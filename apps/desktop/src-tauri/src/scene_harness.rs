//! Fixed synthetic scene cohort. Compiled only with dev-harness; no model assets.
use crate::WorkspaceState;
use locallore::{
    author_correction::*,
    contracts::*,
    engine::Engine,
    host::{Host, HostPlayConstructionV1},
    inference::*,
    play::{PlayContextPolicy, PlayProfile},
};
use locallore_storage::Store;
use serde_json::{json, Value};
use std::{
    path::{Component, Path, PathBuf},
    sync::{
        atomic::{AtomicUsize, Ordering},
        Arc,
    },
    task::Poll,
};

const STORY: &str = "scene-native-controls";
const OTHER: &str = "scene-native-other";
const CHILD: &str = "scene-child";
const A: &str = "SCENE_OBSERVED_A";
const B: &str = "SCENE_UNOBSERVED_B";
const PRIVATE: &str = "SCENE_PARENT_MIRA_ONLY";
const REASON: &str = "SCENE_PRIVATE_AUTHOR_REASON";
const TEXT: &str = "I wait for one tide tick.";
static FACTORIES: AtomicUsize = AtomicUsize::new(0);
static POLLS: AtomicUsize = AtomicUsize::new(0);

#[derive(Clone, Copy, Debug, PartialEq, Eq)]
enum Case {
    Literal,
    Memory,
}
impl Case {
    fn parse(value: &str) -> Result<Self, String> {
        match value {
            "literal" => Ok(Self::Literal),
            "memory" => Ok(Self::Memory),
            _ => Err("SceneCaseRequired".into()),
        }
    }
    fn name(self) -> &'static str {
        match self {
            Self::Literal => "literal",
            Self::Memory => "memory",
        }
    }
    fn scope(self) -> Scope {
        Scope {
            story: STORY.into(),
            branch: if self == Self::Literal { "main" } else { CHILD }.into(),
        }
    }
    fn construction(self) -> HostPlayConstructionV1 {
        match self {
            Self::Literal => HostPlayConstructionV1::PlayerLiteralSceneV1,
            Self::Memory => {
                HostPlayConstructionV1::MemorySceneV1(PlayContextPolicy::StateRelevantMemoryV1)
            }
        }
    }
    fn prompt(self) -> &'static str {
        match self {
            Self::Literal => locallore::play::scene_narration::LITERAL_SCENE_PROMPT_VERSION_V1,
            Self::Memory => locallore::play::scene_narration::SCENE_PROMPT_VERSION_V1,
        }
    }
}
pub(crate) fn active() -> bool {
    crate::harness::active()
        && std::env::var("LOCALLORE_D04_SCENE_HARNESS").is_ok_and(|v| Case::parse(&v).is_ok())
}
pub(crate) fn requested() -> bool {
    crate::harness::active() && std::env::var_os("LOCALLORE_D04_SCENE_HARNESS").is_some()
}
fn case() -> Result<Case, String> {
    if !active() {
        return Err("Forbidden".into());
    }
    Case::parse(&std::env::var("LOCALLORE_D04_SCENE_HARNESS").map_err(|_| "SceneCaseRequired")?)
}
fn workspace_path() -> Result<PathBuf, String> {
    case()?;
    let path = PathBuf::from(
        std::env::var_os("LOCALLORE_TEST_WORKSPACE").ok_or("SceneWorkspaceRequired")?,
    );
    let leaf = path
        .parent()
        .and_then(Path::file_name)
        .and_then(|n| n.to_str())
        .ok_or("SceneWorkspaceRequired")?;
    if !path.is_absolute()
        || path
            .components()
            .any(|c| matches!(c, Component::CurDir | Component::ParentDir))
        || path.file_name().and_then(|n| n.to_str()) != Some("stories-v1.sqlite")
        || !leaf
            .strip_prefix("scene-native-")
            .is_some_and(crate::archive::valid_id)
    {
        return Err("SceneWorkspaceRequired".into());
    }
    Ok(path)
}
fn fixture_seed(story: &str) -> Result<Seed, String> {
    let mut seed: Seed =
        serde_json::from_str(include_str!("../../../../fixtures/lantern_quay.json"))
            .map_err(|_| "SceneSeed")?;
    seed.scope.story = story.into();
    let fact = seed.facts.get_mut("relic-location").ok_or("SceneFact")?;
    fact.proposition = if story == STORY {
        A
    } else {
        "SCENE_OTHER_ONLY"
    }
    .into();
    fact.discoverable_at = Some("quay".into());
    fact.known_by = [seed.player.clone(), "mira".into()].into();
    Ok(seed)
}
fn parent_fixture() -> Result<(Seed, Engine, Receipt), String> {
    let seed = fixture_seed(STORY)?;
    let mut engine = Engine::new(seed.clone()).map_err(|_| "SceneEngine")?;
    let request = engine.request(
        "scene-parent-message",
        Intent::Dialogue {
            text: PRIVATE.into(),
            audience: ["mira".into()].into(),
        },
    );
    let proposal = Engine::proposal(&request).map_err(|_| "SceneProposal")?;
    let approved = engine
        .preview(&request, &proposal)
        .map_err(|_| "ScenePreview")?;
    let receipt = engine
        .commit_prepared(&approved)
        .map_err(|_| "SceneCommit")?;
    Ok((seed, engine, receipt))
}
fn correction() -> AuthorCorrectionInputV1 {
    AuthorCorrectionInputV1 {
        version: 1,
        parent: Scope {
            story: STORY.into(),
            branch: "main".into(),
        },
        expected_parent_revision: 1,
        fork_revision: 1,
        child_branch: CHILD.into(),
        operation: AuthorCorrectionOperationV1::ReplaceFactProposition {
            fact: "relic-location".into(),
            expected_proposition: A.into(),
            replacement: B.into(),
        },
        reason: REASON.into(),
    }
}
fn seed_at(path: &Path) -> Result<(), String> {
    let (seed, _, receipt) = parent_fixture()?;
    let mut store = Store::create_new_pinned(path).map_err(|_| "SceneCreate")?;
    store
        .create_story("Synthetic scene controls", seed)
        .map_err(|_| "SceneStory")?;
    store
        .begin_turn(receipt.request())
        .map_err(|_| "SceneBegin")?;
    store.commit_prepared(&receipt).map_err(|_| "SceneCommit")?;
    let prepared = store
        .prepare_author_correction(&correction(), &|| false)
        .map_err(|_| "SceneAuthorPreview")?;
    store
        .apply_author_correction(&prepared, &|| false)
        .map_err(|_| "SceneAuthorApply")?;
    store
        .create_story("Other synthetic scene story", fixture_seed(OTHER)?)
        .map_err(|_| "SceneOther")?;
    Ok(())
}
pub(crate) fn seed(path: &Path) -> Result<(), String> {
    if workspace_path()? != path
        || path.exists()
        || std::env::var("LOCALLORE_TEST_RESTART").as_deref() == Ok("1")
    {
        return Err("SceneFreshWorkspaceRequired".into());
    }
    let _pins = crate::archive::pin(path.parent().ok_or("SceneWorkspaceRequired")?)?;
    seed_at(path)
}
fn profile() -> PlayProfile {
    PlayProfile {
        id: "scene-native-fixture-v1".into(),
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
struct Script(Scope);
impl InferenceProvider for Script {
    fn poll(
        &mut self,
        request: &GenerationRequest,
        cancel: &Cancellation,
    ) -> Poll<Result<Vec<u8>, Error>> {
        if cancel.is_cancelled() {
            return Poll::Ready(Err(Error::Cancelled));
        }
        if request.scope != self.0 {
            return Poll::Ready(Err(Error::Scope));
        }
        let Input::Structured { role, .. } = &request.input else {
            return Poll::Ready(Err(Error::Provider));
        };
        let value = match role.as_str() {
            "director" => json!({"commands":[{"op":"wait","ticks":1}]}),
            "narrator" => {
                json!({"text":"You pause as a tide tick passes.","event_ids":[request.revision+1],"speaker":"narrator"})
            }
            _ => return Poll::Ready(Err(Error::Provider)),
        };
        POLLS.fetch_add(1, Ordering::SeqCst);
        Poll::Ready(serde_json::to_vec(&value).map_err(|_| Error::Provider))
    }
}
fn configure_case(host: &Host, choice: Case) -> Result<(), String> {
    let scope = choice.scope();
    host.configure_fixture_provider_with_construction(
        profile(),
        Arc::new(move || {
            FACTORIES.fetch_add(1, Ordering::SeqCst);
            Box::new(Script(scope.clone()))
        }),
        choice.construction(),
    )
    .map_err(|_| "SceneProvider".into())
}
pub(crate) fn configure(path: &Path, host: &Host) -> Result<(), String> {
    if workspace_path()? != path {
        return Err("SceneWorkspaceRequired".into());
    }
    configure_validated(path, host, case()?)
}
fn configure_validated(path: &Path, host: &Host, choice: Case) -> Result<(), String> {
    // Restart must validate the actual fixed synthetic history before installing
    // even a scripted owner. A matching directory name alone is insufficient.
    proof(path, choice)?;
    configure_case(host, choice)
}
fn proof(path: &Path, choice: Case) -> Result<Value, String> {
    let _pins = crate::archive::pin(path)?;
    if std::fs::metadata(path).map_err(|_| "SceneMetadata")?.len() > 64 * 1024 * 1024 {
        return Err("SceneBudget".into());
    }
    let mut store = Store::open_read_only(path).map_err(|_| "SceneReadOnly")?;
    let stories = store.stories().map_err(|_| "SceneCatalog")?;
    if stories.len() != 2
        || stories.iter().any(|story| {
            story.scope.branch != "main"
                || match story.scope.story.as_str() {
                    STORY => story.title != "Synthetic scene controls",
                    OTHER => story.title != "Other synthetic scene story",
                    _ => true,
                }
        })
    {
        return Err("SceneCatalog".into());
    }
    for (story, branches) in [(STORY, vec!["main", CHILD]), (OTHER, vec!["main"])] {
        let catalog = store
            .branch_catalog(story, &|| false)
            .map_err(|_| "SceneCatalog")?;
        let actual: std::collections::BTreeSet<_> = catalog
            .branches
            .iter()
            .map(|branch| branch.scope.branch.as_str())
            .collect();
        if actual != branches.into_iter().collect()
            || catalog.branches.iter().any(|branch| branch.retired)
        {
            return Err("SceneCatalog".into());
        }
    }
    let (_, parent, _) = parent_fixture()?;
    let expected_child = parent
        .apply_author_correction(
            &parent
                .prepare_author_correction(&correction(), &|| false)
                .map_err(|_| "SceneAuthor")?,
            &|| false,
        )
        .map_err(|_| "SceneAuthor")?
        .engine;
    let selected = store
        .resume(&choice.scope())
        .map_err(|_| "SceneResume")?
        .engine;
    let baseline = if choice == Case::Literal {
        &parent
    } else {
        &expected_child
    };
    if selected.revision() > baseline.revision() + 6
        || !selected
            .extends_accepted_history(baseline)
            .map_err(|_| "ScenePrefix")?
    {
        return Err("ScenePrefix".into());
    }
    for receipt in selected
        .receipts()
        .iter()
        .filter(|r| r.request().expected_revision >= baseline.revision())
    {
        let play = receipt.play().ok_or("SceneRecord")?;
        if receipt.request().intent
            != (Intent::FreeText {
                kind: PlayInputKind::Action,
                text: TEXT.into(),
            })
            || receipt.proposal().commands != vec![Command::Wait { ticks: 1 }]
            || play.prompt_version != choice.prompt()
            || play.profile != profile()
            || play.scene.is_none()
        {
            return Err("SceneRecord".into());
        }
    }
    let untouched = if choice == Case::Literal {
        &expected_child
    } else {
        &parent
    };
    if store
        .resume(untouched.scope())
        .map_err(|_| "SceneUntouched")?
        .engine
        .accepted_history_basis()
        .map_err(|_| "SceneBasis")?
        != untouched
            .accepted_history_basis()
            .map_err(|_| "SceneBasis")?
    {
        return Err("SceneUntouched".into());
    }
    let other = store
        .resume(&Scope {
            story: OTHER.into(),
            branch: "main".into(),
        })
        .map_err(|_| "SceneOther")?
        .engine;
    if other.accepted_history_basis().map_err(|_| "SceneBasis")?
        != Engine::new(fixture_seed(OTHER)?)
            .map_err(|_| "SceneOther")?
            .accepted_history_basis()
            .map_err(|_| "SceneBasis")?
    {
        return Err("SceneOtherChanged".into());
    }
    let mut observer_hashes = serde_json::Map::new();
    for observer in ["player", "mira", "sable"] {
        let context = selected
            .character_context_v2(observer, selected.scope(), selected.revision())
            .map_err(|_| "SceneObserver")?;
        let bytes = serde_json::to_vec(&context).map_err(|_| "SceneObserverJson")?;
        let text = std::str::from_utf8(&bytes).map_err(|_| "SceneObserverUtf8")?;
        if text.contains(B)
            || text.contains(REASON)
            || (observer != "sable" && !text.contains(A))
            || (observer == "sable" && [A, PRIVATE].iter().any(|v| text.contains(v)))
        {
            return Err("SceneObserverLeak".into());
        }
        observer_hashes.insert(
            observer.into(),
            json!(locallore::inspection::sha256(&bytes)),
        );
    }
    Ok(
        json!({"version":1,"synthetic":true,"case":choice.name(),"scope":selected.scope(),"head":selected.revision(),"domain_version":selected.domain_version(),
        "baseline_head":baseline.revision(),"new_commits":selected.revision()-baseline.revision(),"canonical_sha256":locallore::inspection::sha256(&selected.canonical_bytes()),
        "untouched_preserved":true,"other_preserved":true,"observer_isolated":true,"observer_sha256":observer_hashes,
        "fixture_factories":FACTORIES.load(Ordering::SeqCst),"fixture_polls":POLLS.load(Ordering::SeqCst),"real_model":false}),
    )
}
#[tauri::command]
pub async fn harness_scene_oracle(
    window: tauri::WebviewWindow,
    workspace: tauri::State<'_, WorkspaceState>,
) -> Result<Value, String> {
    let choice = case()?;
    if workspace_path()? != workspace.path {
        return Err("Forbidden".into());
    }
    let epoch = workspace
        .lease
        .capture(window.label())
        .map_err(str::to_owned)?;
    workspace.get(epoch).await?;
    let path = workspace.path.clone();
    let lease = workspace.lease.clone();
    tauri::async_runtime::spawn_blocking(move || lease.dispatch(epoch, || proof(&path, choice)))
        .await
        .map_err(|_| "SceneWorker".to_owned())?
}

#[cfg(test)]
mod tests {
    use super::*;
    #[test]
    fn closed_cases_select_only_native_existing_constructions() {
        assert_eq!(Case::parse("literal").unwrap(), Case::Literal);
        assert_eq!(Case::parse("memory").unwrap(), Case::Memory);
        for invalid in ["", "Literal", "policy", "../memory", "memory "] {
            assert!(Case::parse(invalid).is_err());
        }
        profile().validate().unwrap();
    }
    #[test]
    fn actual_synthetic_store_and_host_have_separate_fixture_provider_and_model_availability() {
        for choice in [Case::Literal, Case::Memory] {
            let root = std::env::temp_dir().join(format!(
                "scene-native-{}",
                crate::exports::identifier().unwrap()
            ));
            std::fs::create_dir(&root).unwrap();
            let path = root.join("stories-v1.sqlite");
            seed_at(&path).unwrap();
            let host = locallore_workspace::open(&path, true).unwrap();
            configure_validated(&path, &host, choice).unwrap();
            let status = host.call(br#"{"version":1,"command":{"op":"model_status"}}"#);
            assert_eq!(status["data"]["provider"], "scene-native-fixture-v1");
            assert_eq!(status["data"]["real_model"], false);
            assert_eq!(status["data"]["loaded"], false);
            assert_eq!(status["data"]["status"], "configured_fixture_owner");
            let result = proof(&path, choice).unwrap();
            assert_eq!(result["new_commits"], 0);
            assert_eq!(
                result["domain_version"],
                if choice == Case::Literal { 1 } else { 2 }
            );
            assert_eq!(result["observer_isolated"], true);
            let other = Engine::new(fixture_seed(OTHER).unwrap()).unwrap();
            let request = other.request(
                "scene-foreign-refusal",
                Intent::FreeText {
                    kind: PlayInputKind::Action,
                    text: TEXT.into(),
                },
            );
            let call = |command: Value| {
                host.call(&serde_json::to_vec(&json!({"version":1,"command":command})).unwrap())
            };
            let resumed = call(json!({"op":"resume","scope":other.scope()}));
            assert_eq!(resumed["status"], "ok");
            let session = resumed["data"]["session"].as_str().unwrap();
            assert_eq!(
                call(json!({"op":"free_text","session":session,"request":request}))["data"]
                    ["phase"],
                "queued"
            );
            let refused = call(
                json!({"op":"prepare","session":session,"scope":other.scope(),"turn":request.turn}),
            );
            assert_eq!(refused["data"]["phase"], "failed");
            assert_eq!(refused["data"]["error"], "Scope");
            assert_eq!(proof(&path, choice).unwrap()["other_preserved"], true);
            host.close_all();
            drop(host);
            // Evidence is retained locally; never delete a computed fixture root.
        }
    }
    #[test]
    fn foreign_existing_database_never_receives_a_fixture_owner() {
        let root = std::env::temp_dir().join(format!(
            "scene-native-{}",
            crate::exports::identifier().unwrap()
        ));
        std::fs::create_dir(&root).unwrap();
        let path = root.join("stories-v1.sqlite");
        let mut store = Store::create_new_pinned(&path).unwrap();
        store
            .create_story("Other synthetic", fixture_seed(OTHER).unwrap())
            .unwrap();
        drop(store);
        let before = std::fs::read(&path).unwrap();
        let host = locallore_workspace::open(&path, true).unwrap();
        assert!(configure_validated(&path, &host, Case::Literal).is_err());
        assert_eq!(
            host.call(br#"{"version":1,"command":{"op":"model_status"}}"#)["data"]["provider"],
            "deterministic-fake-v1"
        );
        host.close_all();
        drop(host);
        assert_eq!(std::fs::read(path).unwrap(), before);
    }
    #[test]
    fn additional_catalog_story_refuses_even_when_named_fixture_histories_are_exact() {
        let root = std::env::temp_dir().join(format!(
            "scene-native-{}",
            crate::exports::identifier().unwrap()
        ));
        std::fs::create_dir(&root).unwrap();
        let path = root.join("stories-v1.sqlite");
        seed_at(&path).unwrap();
        let mut store = Store::open(&path, None).unwrap();
        store
            .create_story(
                "Additional synthetic story",
                fixture_seed("scene-extra-synthetic").unwrap(),
            )
            .unwrap();
        drop(store);
        let before = std::fs::read(&path).unwrap();
        let host = locallore_workspace::open(&path, true).unwrap();
        assert!(configure_validated(&path, &host, Case::Memory).is_err());
        assert_eq!(
            host.call(br#"{"version":1,"command":{"op":"model_status"}}"#)["data"]["provider"],
            "deterministic-fake-v1"
        );
        drop(host);
        assert_eq!(std::fs::read(path).unwrap(), before);
    }
}
