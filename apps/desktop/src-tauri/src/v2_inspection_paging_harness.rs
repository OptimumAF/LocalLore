// Copyright 2026 LocalLore contributors. SPDX-License-Identifier: Apache-2.0
//! Fixed development-only D05 fixture and read-only canonical fingerprints.
//! No renderer paths/selectors, provider, model, SQL or alternate persistence.
use crate::WorkspaceState;
use locallore::{
    author_correction::{AuthorCorrectionInputV1, AuthorCorrectionOperationV1, CanonicalRecord},
    contracts::{Intent, Receipt, Request, Scope, Seed},
    engine::Engine,
};
use locallore_storage::{Store, TurnPhase};
use serde_json::{json, Value};
use sha2::{Digest, Sha256};
use std::{
    fs,
    path::{Path, PathBuf},
};

const SELECTOR: &str = "LOCALLORE_D05_INSPECTOR_PAGING_HARNESS";
const PRIMARY_STORY: &str = "d05-inspector-native";
const OTHER_STORY: &str = "d05-inspector-other";
const ORACLE_CAP: usize = 32 * 1024;
const ALLOWED_KEYS: [&str; 5] = [
    "LOCALLORE_D02_HARNESS",
    "LOCALLORE_D02_ARTIFACT_DIR",
    "LOCALLORE_TEST_WORKSPACE",
    SELECTOR,
    "LOCALLORE_D08_TIMELINE_BROWSER_HARNESS",
];

fn fixture_invalid() -> String {
    "SyntheticFixtureInvalid".into()
}
fn workspace_invalid() -> String {
    "SyntheticWorkspaceRequired".into()
}

fn validate_mode(
    selector: Option<&str>,
    development: bool,
    legacy_inspecting: bool,
    other_harness: bool,
) -> Result<bool, String> {
    match selector {
        None => Ok(false),
        Some("1") if development && !legacy_inspecting && !other_harness => Ok(true),
        Some(_) => Err("Forbidden".into()),
    }
}
pub fn requested() -> bool {
    std::env::var_os(SELECTOR).is_some()
        || std::env::var_os("LOCALLORE_D08_TIMELINE_BROWSER_HARNESS").is_some()
        || crate::domain2_fork_harness::requested()
}
fn validate_browser_flag(browser: Option<&str>, paging: Option<&str>) -> Result<bool, String> {
    match browser {
        None => Ok(false),
        Some("1") if paging == Some("1") => Ok(true),
        Some(_) => Err("Forbidden".into()),
    }
}
fn runtime_mode() -> Result<bool, String> {
    let browser = std::env::var_os("LOCALLORE_D08_TIMELINE_BROWSER_HARNESS");
    let paging = std::env::var_os(SELECTOR);
    validate_browser_flag(
        browser
            .as_ref()
            .map(|v| v.to_str().ok_or("Forbidden"))
            .transpose()?,
        paging
            .as_ref()
            .map(|v| v.to_str().ok_or("Forbidden"))
            .transpose()?,
    )?;
    let Some(selector) = paging else {
        return Ok(false);
    };
    let selector = selector.to_str().ok_or("Forbidden")?;
    let conflicting = std::env::vars_os().any(|(key, _)| {
        let folded = key.to_string_lossy().to_ascii_uppercase();
        folded.starts_with("LOCALLORE_") && !ALLOWED_KEYS.contains(&folded.as_str())
    });
    validate_mode(
        Some(selector),
        cfg!(feature = "dev-harness")
            && std::env::var("LOCALLORE_D02_HARNESS").as_deref() == Ok("1"),
        std::env::var_os("LOCALLORE_D05_HARNESS").is_some(),
        conflicting,
    )
}
pub fn active() -> bool {
    runtime_mode() == Ok(true)
}

fn physical_d(path: &Path) -> bool {
    #[cfg(windows)]
    {
        use std::path::{Component, Prefix};
        matches!(path.components().next(), Some(Component::Prefix(prefix))
            if matches!(prefix.kind(), Prefix::Disk(drive) | Prefix::VerbatimDisk(drive)
                if drive.eq_ignore_ascii_case(&b'D')))
    }
    #[cfg(not(windows))]
    {
        let _ = path;
        false
    }
}
fn ordinary(metadata: &fs::Metadata, directory: bool) -> bool {
    if metadata.file_type().is_symlink()
        || (directory && !metadata.is_dir())
        || (!directory && !metadata.is_file())
    {
        return false;
    }
    #[cfg(windows)]
    {
        use std::os::windows::fs::MetadataExt;
        if metadata.file_attributes() & 0x400 != 0 {
            return false;
        }
    }
    true
}
fn lowercase_uuid(value: &str) -> bool {
    value.len() == 36
        && value.bytes().enumerate().all(|(index, byte)| {
            if [8, 13, 18, 23].contains(&index) {
                byte == b'-'
            } else {
                byte.is_ascii_digit() || (b'a'..=b'f').contains(&byte)
            }
        })
}
fn validate_workspace_path(path: &Path) -> Result<(), String> {
    let raw = path.to_str().ok_or_else(workspace_invalid)?;
    // Inspect raw separators before Path::components can discard interior '.'.
    if !path.is_absolute()
        || !physical_d(path)
        || raw
            .split(['/', '\\'])
            .any(|part| matches!(part, "." | ".."))
        || path.file_name().and_then(|name| name.to_str()) != Some("stories-v1.sqlite")
    {
        return Err(workspace_invalid());
    }
    let parent = path.parent().ok_or_else(workspace_invalid)?;
    let suffix = parent
        .file_name()
        .and_then(|name| name.to_str())
        .and_then(|name| name.strip_prefix("d05-v2-inspector-paging-native-"))
        .ok_or_else(workspace_invalid)?;
    if !lowercase_uuid(suffix) {
        return Err(workspace_invalid());
    }
    for ancestor in parent.ancestors() {
        let metadata = fs::symlink_metadata(ancestor).map_err(|_| workspace_invalid())?;
        if !ordinary(&metadata, true) {
            return Err(workspace_invalid());
        }
    }
    let canonical = fs::canonicalize(parent).map_err(|_| workspace_invalid())?;
    if !physical_d(&canonical) {
        return Err(workspace_invalid());
    }
    match fs::symlink_metadata(path) {
        Ok(metadata) if ordinary(&metadata, false) => {}
        Err(error) if error.kind() == std::io::ErrorKind::NotFound => {}
        _ => return Err(workspace_invalid()),
    }
    Ok(())
}
fn fixture_scopes() -> [Scope; 3] {
    [
        Scope {
            story: PRIMARY_STORY.into(),
            branch: "main".into(),
        },
        Scope {
            story: PRIMARY_STORY.into(),
            branch: "paging".into(),
        },
        Scope {
            story: OTHER_STORY.into(),
            branch: "main".into(),
        },
    ]
}

/// Fresh development profile beside the fixed workspace, inside its packet.
/// No profile creation, migration, reuse, repair or renderer-supplied address.
pub fn webview_profile(workspace: &Path) -> Result<PathBuf, String> {
    if crate::domain2_fork_harness::active() {
        return crate::domain2_fork_harness::webview_profile(workspace);
    }
    validate_workspace_path(workspace)?;
    let packet = workspace
        .parent()
        .and_then(Path::parent)
        .ok_or_else(workspace_invalid)?;
    let identifier = packet
        .file_name()
        .and_then(|name| name.to_str())
        .and_then(|name| name.strip_prefix("p-"))
        .ok_or_else(workspace_invalid)?;
    if !lowercase_uuid(identifier) {
        return Err(workspace_invalid());
    }
    let profile = packet.join("webview-profile");
    let text = profile.to_str().ok_or_else(workspace_invalid)?;
    // Conservative test-layout budget; not a vendor limit or startup guarantee.
    if text.encode_utf16().count() > 190 {
        return Err(workspace_invalid());
    }
    match fs::symlink_metadata(&profile) {
        Err(error) if error.kind() == std::io::ErrorKind::NotFound => Ok(profile),
        Ok(_) | Err(_) => Err(workspace_invalid()),
    }
}
fn fixed_seed(other: bool) -> Result<Seed, String> {
    let mut seed: Seed =
        serde_json::from_str(include_str!("../../../../fixtures/lantern_quay.json"))
            .map_err(|_| fixture_invalid())?;
    seed.scope = fixture_scopes()[if other { 2 } else { 0 }].clone();
    seed.facts
        .get_mut("relic-location")
        .ok_or_else(fixture_invalid)?
        .proposition = if other {
        "D05_OTHER_STORY_SEED_515"
    } else {
        "D05_PLAYER_SEED_SECRET_731"
    }
    .into();
    if !other {
        seed.beliefs
            .iter_mut()
            .find(|belief| belief.believer == "mira")
            .ok_or_else(fixture_invalid)?
            .proposition = "D05_MIRA_PRIVATE_BELIEF_812".into();
    }
    Ok(seed)
}
fn fixed_author_input() -> AuthorCorrectionInputV1 {
    AuthorCorrectionInputV1 {
        version: 1,
        parent: fixture_scopes()[0].clone(),
        expected_parent_revision: 0,
        fork_revision: 0,
        child_branch: "paging".into(),
        reason: "D05_AUTHOR_REASON_PRIVATE_914".into(),
        operation: AuthorCorrectionOperationV1::ReplaceFactProposition {
            fact: "beacon-mark".into(),
            expected_proposition: "An old repair mark is scratched inside the dry well.".into(),
            replacement: "D05_UNOBSERVED_AUTHOR_TRUTH_913".into(),
        },
    }
}
fn fixed_intent(player: &str, index: usize, other: bool) -> Intent {
    Intent::Dialogue {
        text: if other {
            "D05_OTHER_STORY_MESSAGE_516".into()
        } else {
            format!(
                "D05_PAGING_ROW_{index:03}{}",
                if index % 2 == 1 {
                    "_MIRA"
                } else {
                    "_PLAYER_ONLY"
                }
            )
        },
        audience: [if other || index % 2 == 1 {
            "mira".into()
        } else {
            player.into()
        }]
        .into(),
    }
}
fn fixed_turn_key(index: usize, other: bool) -> String {
    if other {
        "d05-other-001".into()
    } else {
        format!("d05-page-{index:03}")
    }
}
fn commit_dialogue(
    store: &mut Store,
    scope: &Scope,
    index: usize,
    other: bool,
) -> Result<(), String> {
    let engine = store.resume(scope).map_err(|_| fixture_invalid())?.engine;
    let request = engine.request(
        &fixed_turn_key(index, other),
        fixed_intent(&engine.seed().player, index, other),
    );
    let proposal = Engine::proposal(&request).map_err(|_| fixture_invalid())?;
    let preview = engine
        .preview(&request, &proposal)
        .map_err(|_| fixture_invalid())?;
    store.begin_turn(&request).map_err(|_| fixture_invalid())?;
    let receipt = store
        .commit_prepared(&preview)
        .map_err(|_| fixture_invalid())?;
    if receipt != preview || receipt.request() != &request {
        return Err(fixture_invalid());
    }
    Ok(())
}
fn prepare_fixture(path: &Path) -> Result<(), String> {
    validate_workspace_path(path)?;
    let parent = path.parent().ok_or_else(workspace_invalid)?;
    let _pins = crate::archive::pin(parent).map_err(|_| workspace_invalid())?;
    match fs::symlink_metadata(path) {
        Ok(_) => return Err("SyntheticFreshWorkspaceRequired".into()),
        Err(error) if error.kind() == std::io::ErrorKind::NotFound => {}
        Err(_) => return Err(workspace_invalid()),
    }
    let mut store = Store::create_new_pinned(path).map_err(|_| fixture_invalid())?;
    let scopes = fixture_scopes();
    store
        .create_story("D05 inspector paging synthetic story", fixed_seed(false)?)
        .map_err(|_| fixture_invalid())?;
    let prepared = store
        .prepare_author_correction(&fixed_author_input(), &|| false)
        .map_err(|_| fixture_invalid())?;
    let corrected = store
        .apply_author_correction(&prepared, &|| false)
        .map_err(|_| fixture_invalid())?;
    if corrected.scope != scopes[1]
        || corrected.parent != scopes[0]
        || corrected.fork_revision != 0
        || corrected.author_revision != 1
        || corrected.head_revision != 1
        || !corrected.created
    {
        return Err(fixture_invalid());
    }
    for index in 1..=43 {
        commit_dialogue(&mut store, &scopes[1], index, false)?;
    }
    store
        .create_story("D05 other synthetic story", fixed_seed(true)?)
        .map_err(|_| fixture_invalid())?;
    commit_dialogue(&mut store, &scopes[2], 1, true)?;
    drop(store);
    fixture_oracle(path)?;
    Ok(())
}
fn encode_fixture<T: serde::Serialize + ?Sized>(value: &T) -> Result<Vec<u8>, String> {
    serde_json::to_vec(value).map_err(|_| "SyntheticOracleBudget".into())
}
fn digest(bytes: &[u8]) -> String {
    format!("{:x}", Sha256::digest(bytes))
}
fn digest_json<T: serde::Serialize + ?Sized>(value: &T) -> Result<String, String> {
    Ok(digest(&encode_fixture(value)?))
}
fn validate_catalog(store: &mut Store) -> Result<(), String> {
    let scopes = fixture_scopes();
    let roots = store.stories().map_err(|_| fixture_invalid())?;
    if roots.len() != 2
        || roots[0].scope != scopes[0]
        || roots[0].revision != 0
        || roots[0].drafts != 0
        || roots[1].scope != scopes[2]
        || roots[1].revision != 1
        || roots[1].drafts != 0
    {
        return Err(fixture_invalid());
    }
    for (story, expected) in [(PRIMARY_STORY, &scopes[..2]), (OTHER_STORY, &scopes[2..])] {
        let catalog = store
            .branch_catalog(story, &|| false)
            .map_err(|_| fixture_invalid())?;
        if catalog.root_branch != "main" || catalog.branches.len() != expected.len() {
            return Err(fixture_invalid());
        }
        for scope in expected {
            let branch = catalog
                .branches
                .iter()
                .find(|branch| &branch.scope == scope)
                .ok_or_else(fixture_invalid)?;
            let child = scope.branch == "paging";
            let revision = if child {
                44
            } else if scope.story == OTHER_STORY {
                1
            } else {
                0
            };
            let parent = if child { Some("main") } else { None };
            let fork = if child { Some(0) } else { None };
            if branch.retired
                || branch.drafts != 0
                || branch.revision != revision
                || branch.parent_branch.as_deref() != parent
                || branch.fork_revision != fork
            {
                return Err(fixture_invalid());
            }
        }
    }
    Ok(())
}
fn scope_oracle(store: &mut Store, scope: &Scope, index: usize) -> Result<Value, String> {
    let engine = store.resume(scope).map_err(|_| fixture_invalid())?.engine;
    let expected_seed = fixed_seed(index == 2)?;
    let (domain, head, ordinary_count, record_count) =
        [(1, 0, 0, 0), (2, 44, 43, 44), (1, 1, 1, 1)][index];
    if engine.scope() != scope
        || engine.domain_version() != domain
        || engine.revision() != head
        || engine.seed() != &expected_seed
        || engine.receipts().len() != ordinary_count
        || engine.canonical_record_count() != record_count
        || engine.state().story_time != 100
        || engine.state().actors != expected_seed.actors
        || engine.state().items != expected_seed.items
    {
        return Err(fixture_invalid());
    }
    if index == 1 {
        match engine.canonical_records().first() {
            Some(CanonicalRecord::AuthorV1(author))
                if author.input() == &fixed_author_input()
                    && author.scope() == scope
                    && author.sequence() == 1 => {}
            _ => return Err(fixture_invalid()),
        }
    }
    let mut turns: Vec<(String, &'static str, Request, Receipt)> =
        Vec::with_capacity(ordinary_count);
    for number in 1..=ordinary_count {
        let other = index == 2;
        let key = fixed_turn_key(number, other);
        let saved = store
            .lookup_turn(scope, &key)
            .map_err(|_| fixture_invalid())?;
        if !matches!(saved.phase, TurnPhase::Committed) {
            return Err(fixture_invalid());
        }
        let receipt = saved.receipt.ok_or_else(fixture_invalid)?;
        let expected = Request {
            version: 1,
            scope: scope.clone(),
            turn: key.clone(),
            expected_revision: if other { 0 } else { number as u64 },
            intent: fixed_intent(&expected_seed.player, number, other),
        };
        let expected_proposal = Engine::proposal(&expected).map_err(|_| fixture_invalid())?;
        let record = engine
            .canonical_records()
            .get(if other { 0 } else { number })
            .ok_or_else(fixture_invalid)?;
        let sequence = if other { 1 } else { number as u64 + 1 };
        if (other && !matches!(record, CanonicalRecord::LegacyPlay(_)))
            || (!other && !matches!(record, CanonicalRecord::PlayV2(_)))
            || saved.request != expected
            || receipt.request() != &expected
            || receipt.proposal() != &expected_proposal
            || receipt.narration() != "Your words are heard by the chosen listeners."
            || receipt.play().is_some()
            || receipt.events().len() != 1
            || receipt.events()[0].scope() != scope
            || receipt.events()[0].sequence() != sequence
            || record.receipt() != Some(&receipt)
        {
            return Err(fixture_invalid());
        }
        turns.push((key, "committed", saved.request, receipt));
    }
    let actors = [engine.seed().player.as_str(), "mira", "oren", "sable"]
        .into_iter()
        .map(|id| {
            Ok((
                id.to_owned(),
                engine
                    .character_context_v2(id, scope, engine.revision())
                    .map_err(|_| fixture_invalid())?,
                engine
                    .actor_receipts_v2(id, scope, engine.revision())
                    .map_err(|_| fixture_invalid())?,
            ))
        })
        .collect::<Result<Vec<_>, String>>()?;
    Ok(
        json!({"scope":scope,"domain_version":engine.domain_version(),"head":engine.revision(),
        "story_time":engine.state().story_time,"seed_sha256":digest_json(engine.seed())?,
        "projection_sha256":digest(&engine.canonical_bytes()),"records_sha256":digest_json(engine.canonical_records())?,
        "receipts_sha256":digest_json(engine.receipts())?,"turns_sha256":digest_json(&turns)?,"actors_sha256":digest_json(&actors)?}),
    )
}
fn fixture_oracle(path: &Path) -> Result<Value, String> {
    validate_workspace_path(path)?;
    let parent = path.parent().ok_or_else(workspace_invalid)?;
    let _parent_pins = crate::archive::pin(parent).map_err(|_| workspace_invalid())?;
    let _file_pins = match fs::symlink_metadata(path) {
        Ok(_) => Some(crate::archive::pin(path).map_err(|_| workspace_invalid())?),
        Err(error) if error.kind() == std::io::ErrorKind::NotFound => None,
        Err(_) => return Err(workspace_invalid()),
    };
    let mut store = Store::open_read_only(path).map_err(|_| "SyntheticReadOnly".to_owned())?;
    validate_catalog(&mut store)?;
    let scopes = fixture_scopes()
        .iter()
        .enumerate()
        .map(|(index, scope)| scope_oracle(&mut store, scope, index))
        .collect::<Result<Vec<_>, _>>()?;
    let value = json!({"version":1,"kind":"v2_inspection_paging_oracle_v1","fixture_version":1,"scopes":scopes});
    if encode_fixture(&value)?.len() > ORACLE_CAP {
        return Err("SyntheticOracleBudget".into());
    }
    Ok(value)
}
fn environment_workspace() -> Result<PathBuf, String> {
    std::env::var_os("LOCALLORE_TEST_WORKSPACE")
        .map(PathBuf::from)
        .ok_or_else(workspace_invalid)
}
/// Called before any Host/other fixture setup; normal absence is a no-op.
pub fn prepare() -> Result<(), String> {
    if crate::domain2_fork_harness::requested() {
        if !crate::domain2_fork_harness::runtime_mode()? {
            return Err("Forbidden".into());
        }
        let path = crate::domain2_fork_harness::environment_workspace()?;
        // Validate all fixed addresses before creating the database or profile.
        crate::domain2_fork_harness::webview_profile(&path)?;
        let parent = path.parent().ok_or_else(workspace_invalid)?;
        let artifact = std::env::var_os("LOCALLORE_D02_ARTIFACT_DIR")
            .map(PathBuf::from)
            .ok_or_else(workspace_invalid)?;
        if artifact != parent.join("evidence") {
            return Err(workspace_invalid());
        }
        match fs::symlink_metadata(&artifact) {
            Err(error) if error.kind() == std::io::ErrorKind::NotFound => {}
            _ => return Err(workspace_invalid()),
        }
        let _pins = crate::archive::pin(parent).map_err(|_| workspace_invalid())?;
        return crate::domain2_fork_harness::seed(&path);
    }
    if !runtime_mode()? {
        return Ok(());
    }
    prepare_fixture(&environment_workspace()?)
}

#[tauri::command]
pub async fn harness_v2_inspection_paging(
    window: tauri::WebviewWindow,
    workspace: tauri::State<'_, WorkspaceState>,
) -> Result<Value, String> {
    if !runtime_mode()? {
        return Err("Forbidden".into());
    }
    let epoch = workspace
        .lease
        .capture(window.label())
        .map_err(str::to_owned)?;
    let path = workspace.path.clone();
    if environment_workspace()?.as_os_str() != path.as_os_str() {
        return Err(workspace_invalid());
    }
    let lease = workspace.lease.clone();
    tauri::async_runtime::spawn_blocking(move || {
        let value = lease.dispatch(epoch, || {
            if !runtime_mode()? {
                return Err("Forbidden".into());
            }
            if environment_workspace()?.as_os_str() != path.as_os_str() {
                return Err(workspace_invalid());
            }
            fixture_oracle(&path)
        })?;
        // Invalidation can occur while a blocking read holds the lease gate.
        // Recheck after completion rather than publish a closed window's result.
        lease.dispatch(epoch, || Ok(value))
    })
    .await
    .map_err(|_| "SyntheticWorker".to_owned())?
}

#[cfg(test)]
#[path = "v2_inspection_paging_harness_review_tests.rs"]
mod review_tests;

#[cfg(all(test, windows))]
#[path = "v2_inspection_paging_profile_review_tests.rs"]
mod profile_review_tests;
