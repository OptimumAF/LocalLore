//! Closed development fixture and read-only Core-derived fingerprints.
//! No renderer paths, WorkspaceState, Tauri, provider, SQL or alternate Store.
use locallore::{
    author_correction::{AuthorCorrectionInputV1, AuthorCorrectionOperationV1, CanonicalRecord},
    contracts::{Command, Intent, Scope, Seed},
    engine::Engine,
};
use locallore_storage::{ForkRequest, Store, TurnError, TurnPhase};
use serde_json::{json, Value};
use sha2::{Digest, Sha256};
use std::{
    collections::HashSet,
    fs,
    path::{Path, PathBuf},
};

const SELECTOR: &str = "LOCALLORE_D08_DOMAIN2_FORK_HARNESS";
const ALLOWED_KEYS: [&str; 4] = [
    SELECTOR,
    "LOCALLORE_D02_HARNESS",
    "LOCALLORE_D02_ARTIFACT_DIR",
    "LOCALLORE_TEST_WORKSPACE",
];
const PRIMARY: &str = "d08-fork-native";
const OTHER: &str = "d08-fork-other";
const TURN: &str = "d08-domain2-fork-prefix";
const SAY: &str = "D08_PREFIX_MIRA_ONLY_421";
const ORACLE_CAP: usize = 32 * 1024;
fn invalid() -> String {
    "SyntheticFixtureInvalid".into()
}
fn workspace_invalid() -> String {
    "SyntheticWorkspaceRequired".into()
}

pub(crate) fn validate_mode(
    selector: Option<&str>,
    development: bool,
    conflict: bool,
    alias: bool,
) -> Result<bool, String> {
    match selector {
        None => Ok(false),
        Some("1") if development && !conflict && !alias => Ok(true),
        Some(_) => Err("Forbidden".into()),
    }
}
pub(crate) fn allowed_action(action: &str) -> bool {
    matches!(action, "hold" | "release" | "lose-ack" | "domain2-oracle")
}
pub(crate) fn requested() -> bool {
    std::env::vars_os().any(|(key, _)| key.to_string_lossy().to_ascii_uppercase() == SELECTOR)
}
pub(crate) fn runtime_mode() -> Result<bool, String> {
    let mut selector = None;
    let mut conflict = false;
    let mut alias = false;
    let mut keys = HashSet::new();
    for (key, value) in std::env::vars_os() {
        let folded = key.to_string_lossy().to_ascii_uppercase();
        if !folded.starts_with("LOCALLORE_") {
            continue;
        }
        alias |= key.to_str() != Some(folded.as_str()) || !keys.insert(folded.clone());
        conflict |= !ALLOWED_KEYS.contains(&folded.as_str());
        if folded == SELECTOR {
            selector = Some(value.into_string().map_err(|_| "Forbidden")?);
        }
    }
    validate_mode(
        selector.as_deref(),
        cfg!(feature = "dev-harness")
            && std::env::var("LOCALLORE_D02_HARNESS").as_deref() == Ok("1"),
        conflict,
        alias,
    )
}
pub(crate) fn active() -> bool {
    runtime_mode() == Ok(true)
}

fn physical_d(path: &Path) -> bool {
    #[cfg(windows)]
    {
        use std::path::{Component, Prefix};
        matches!(path.components().next(), Some(Component::Prefix(prefix))
            if matches!(prefix.kind(), Prefix::Disk(drive) | Prefix::VerbatimDisk(drive) if drive.eq_ignore_ascii_case(&b'D')))
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
fn uuid(value: &str) -> bool {
    value.len() == 36
        && value.bytes().enumerate().all(|(index, byte)| {
            if [8, 13, 18, 23].contains(&index) {
                byte == b'-'
            } else {
                byte.is_ascii_digit() || (b'a'..=b'f').contains(&byte)
            }
        })
}
pub(crate) fn validate_workspace_path(path: &Path) -> Result<(), String> {
    let raw = path.to_str().ok_or_else(workspace_invalid)?;
    if !path.is_absolute()
        || !physical_d(path)
        || raw.encode_utf16().count() > 248
        || raw
            .split(['/', '\\'])
            .any(|part| matches!(part, "." | ".."))
        || path.file_name().and_then(|n| n.to_str()) != Some("stories-v1.sqlite")
    {
        return Err(workspace_invalid());
    }
    let parent = path.parent().ok_or_else(workspace_invalid)?;
    let id = parent
        .file_name()
        .and_then(|n| n.to_str())
        .and_then(|n| n.strip_prefix("d08-domain2-fork-native-"))
        .ok_or_else(workspace_invalid)?;
    let packet = parent.parent().ok_or_else(workspace_invalid)?;
    let packet_id = packet
        .file_name()
        .and_then(|n| n.to_str())
        .and_then(|n| n.strip_prefix("p-"))
        .ok_or_else(workspace_invalid)?;
    if !uuid(id) || !uuid(packet_id) {
        return Err(workspace_invalid());
    }
    for ancestor in parent.ancestors() {
        if !ordinary(
            &fs::symlink_metadata(ancestor).map_err(|_| workspace_invalid())?,
            true,
        ) {
            return Err(workspace_invalid());
        }
    }
    if !physical_d(&fs::canonicalize(parent).map_err(|_| workspace_invalid())?) {
        return Err(workspace_invalid());
    }
    match fs::symlink_metadata(path) {
        Ok(metadata) if ordinary(&metadata, false) => Ok(()),
        Err(error) if error.kind() == std::io::ErrorKind::NotFound => Ok(()),
        _ => Err(workspace_invalid()),
    }
}
pub(crate) fn webview_profile(path: &Path) -> Result<PathBuf, String> {
    validate_workspace_path(path)?;
    let profile = path
        .parent()
        .and_then(Path::parent)
        .ok_or_else(workspace_invalid)?
        .join("webview-profile");
    if profile
        .to_str()
        .ok_or_else(workspace_invalid)?
        .encode_utf16()
        .count()
        > 190
    {
        return Err(workspace_invalid());
    }
    match fs::symlink_metadata(&profile) {
        Err(error) if error.kind() == std::io::ErrorKind::NotFound => Ok(profile),
        _ => Err(workspace_invalid()),
    }
}
pub(crate) fn environment_workspace() -> Result<PathBuf, String> {
    std::env::var_os("LOCALLORE_TEST_WORKSPACE")
        .map(PathBuf::from)
        .ok_or_else(workspace_invalid)
}

fn scope(story: &str, branch: &str) -> Scope {
    Scope {
        story: story.into(),
        branch: branch.into(),
    }
}
fn fixed_seed(other: bool) -> Result<Seed, String> {
    let mut seed: Seed =
        serde_json::from_str(include_str!("../../../../fixtures/lantern_quay.json"))
            .map_err(|_| invalid())?;
    seed.scope = scope(if other { OTHER } else { PRIMARY }, "main");
    if other {
        seed.facts
            .get_mut("beacon-mark")
            .ok_or_else(invalid)?
            .proposition = "D08_OTHER_STORY_TRUTH_424".into();
    }
    Ok(seed)
}
fn author() -> Result<AuthorCorrectionInputV1, String> {
    Ok(AuthorCorrectionInputV1 {
        version: 1,
        parent: scope(PRIMARY, "main"),
        expected_parent_revision: 2,
        fork_revision: 2,
        child_branch: "authored".into(),
        operation: AuthorCorrectionOperationV1::ReplaceFactProposition {
            fact: "beacon-mark".into(),
            expected_proposition: fixed_seed(false)?
                .facts
                .get("beacon-mark")
                .ok_or_else(invalid)?
                .proposition
                .clone(),
            replacement: "D08_PRIVATE_AUTHOR_TRUTH_422".into(),
        },
        reason: "D08_PRIVATE_AUTHOR_REASON_423".into(),
    })
}
fn intent() -> Intent {
    Intent::Actions(vec![
        Command::Say {
            text: SAY.into(),
            audience: ["mira".into()].into(),
        },
        Command::Wait { ticks: 1 },
    ])
}
fn expected_engines() -> Result<Vec<Engine>, String> {
    let mut root = Engine::new(fixed_seed(false)?).map_err(|_| invalid())?;
    let request = root.request(TURN, intent());
    let proposal = Engine::proposal(&request).map_err(|_| invalid())?;
    let preview = root.preview(&request, &proposal).map_err(|_| invalid())?;
    root.commit_prepared(&preview).map_err(|_| invalid())?;
    let prepared = root
        .prepare_author_correction(&author()?, &|| false)
        .map_err(|_| invalid())?;
    let authored = root
        .apply_author_correction(&prepared, &|| false)
        .map_err(|_| invalid())?
        .engine;
    let sibling = root.fork("sibling", 2).map_err(|_| invalid())?;
    Ok(vec![
        root,
        authored,
        sibling,
        Engine::new(fixed_seed(true)?).map_err(|_| invalid())?,
    ])
}
pub(crate) fn seed(path: &Path) -> Result<(), String> {
    validate_workspace_path(path)?;
    // The existing pinned Store reservation is create-new and retains partial failures.
    let mut store = Store::create_new_pinned(path).map_err(|_| invalid())?;
    let parent = scope(PRIMARY, "main");
    store
        .create_story("Domain2 fork synthetic story", fixed_seed(false)?)
        .map_err(|_| invalid())?;
    let engine = store.resume(&parent).map_err(|_| invalid())?.engine;
    let request = engine.request(TURN, intent());
    let proposal = Engine::proposal(&request).map_err(|_| invalid())?;
    let preview = engine.preview(&request, &proposal).map_err(|_| invalid())?;
    if preview.events().len() != 2 {
        return Err(invalid());
    }
    store.begin_turn(&request).map_err(|_| invalid())?;
    if store.commit_prepared(&preview).map_err(|_| invalid())? != preview {
        return Err(invalid());
    }
    let prepared = store
        .prepare_author_correction(&author()?, &|| false)
        .map_err(|_| invalid())?;
    let authored = store
        .apply_author_correction(&prepared, &|| false)
        .map_err(|_| invalid())?;
    if !authored.created
        || authored.scope != scope(PRIMARY, "authored")
        || authored.author_revision != 3
        || authored.head_revision != 3
    {
        return Err(invalid());
    }
    let sibling = store
        .fork_branch(
            &ForkRequest {
                parent,
                child_branch: "sibling".into(),
                expected_parent_revision: 2,
                at_revision: 2,
            },
            &|| false,
        )
        .map_err(|_| invalid())?;
    if !sibling.created || sibling.head_revision != 2 {
        return Err(invalid());
    }
    store
        .create_story("Domain2 fork other synthetic story", fixed_seed(true)?)
        .map_err(|_| invalid())?;
    drop(store);
    oracle(path)?;
    Ok(())
}
fn digest(bytes: &[u8]) -> String {
    format!("{:x}", Sha256::digest(bytes))
}
fn hash_json<T: serde::Serialize + ?Sized>(value: &T) -> Result<String, String> {
    Ok(digest(&serde_json::to_vec(value).map_err(|_| invalid())?))
}
fn core_row(engine: &Engine) -> Result<Value, String> {
    let actors = [engine.seed().player.as_str(), "mira", "oren", "sable"]
        .into_iter()
        .map(|id| {
            Ok((
                id,
                engine
                    .character_context_v2(id, engine.scope(), engine.revision())
                    .map_err(|_| invalid())?,
                engine
                    .actor_receipts_v2(id, engine.scope(), engine.revision())
                    .map_err(|_| invalid())?,
            ))
        })
        .collect::<Result<Vec<_>, String>>()?;
    Ok(
        json!({"scope":engine.scope(),"domain_version":engine.domain_version(),"head":engine.revision(),
        "story_time":engine.state().story_time,"boundaries":engine.completed_boundaries(),
        "canonical_records":engine.canonical_record_count(),"ordinary_receipts":engine.receipts().len(),
        "seed_sha256":hash_json(engine.seed())?,"projection_sha256":digest(&engine.canonical_bytes()),
        "records_sha256":hash_json(engine.canonical_records())?,"receipts_sha256":hash_json(engine.receipts())?,"actors_sha256":hash_json(&actors)?}),
    )
}
fn turns_hash(store: &mut Store, engine: &Engine) -> Result<String, String> {
    let mut ordinary = Vec::new();
    for receipt in engine.receipts() {
        let turn = &receipt.request().turn;
        ordinary.push(match store.lookup_turn(engine.scope(), turn) {
            Ok(saved) if matches!(saved.phase, TurnPhase::Committed) => json!({"turn":turn,"status":"committed","request":saved.request,"receipt":saved.receipt}),
            Err(TurnError::UnknownTurn) => json!({"turn":turn,"status":"unknown_turn"}),
            _ => return Err(invalid()),
        });
    }
    let mut authors = Vec::new();
    for record in engine.canonical_records() {
        if let CanonicalRecord::AuthorV1(record) = record {
            if record.scope() == engine.scope() {
                let found = store
                    .lookup_author_correction(record.input(), &|| false)
                    .map_err(|_| invalid())?
                    .ok_or_else(invalid)?;
                authors.push(json!({"scope":found.scope,"parent":found.parent,"fork_revision":found.fork_revision,"author_revision":found.author_revision,"head_revision":found.head_revision,"created":found.created}));
            }
        }
    }
    hash_json(&json!({"ordinary":ordinary,"author":authors}))
}
pub(crate) fn oracle(path: &Path) -> Result<Value, String> {
    validate_workspace_path(path)?;
    let mut store = Store::open_read_only(path).map_err(|_| "SyntheticReadOnly")?;
    let expected = expected_engines()?;
    let roots = store.stories().map_err(|_| invalid())?;
    if roots.len() != 2 || roots.iter().any(|row| row.drafts != 0) {
        return Err(invalid());
    }
    for (story, head) in [(PRIMARY, 2), (OTHER, 0)] {
        if !roots
            .iter()
            .any(|row| row.scope == scope(story, "main") && row.revision == head)
        {
            return Err(invalid());
        }
    }
    let catalog = store
        .branch_catalog(PRIMARY, &|| false)
        .map_err(|_| invalid())?;
    let other = store
        .branch_catalog(OTHER, &|| false)
        .map_err(|_| invalid())?;
    if catalog.root_branch != "main"
        || other.root_branch != "main"
        || other.branches.len() != 1
        || !(3..=6).contains(&catalog.branches.len())
    {
        return Err(invalid());
    }
    let mut scopes = Vec::new();
    for (index, engine) in expected.iter().enumerate() {
        let branches = if index == 3 {
            &other.branches
        } else {
            &catalog.branches
        };
        let branch = branches
            .iter()
            .find(|b| &b.scope == engine.scope())
            .ok_or_else(invalid)?;
        let parent = if matches!(index, 1 | 2) {
            Some("main")
        } else {
            None
        };
        let fork = if parent.is_some() { Some(2) } else { None };
        if branch.retired
            || branch.drafts != 0
            || branch.revision != engine.revision()
            || branch.parent_branch.as_deref() != parent
            || branch.fork_revision != fork
        {
            return Err(invalid());
        }
        let actual = store.resume(engine.scope()).map_err(|_| invalid())?.engine;
        let mut row = core_row(&actual)?;
        if row != core_row(engine)? {
            return Err(invalid());
        }
        row["turns_sha256"] = json!(turns_hash(&mut store, &actual)?);
        scopes.push(row);
    }
    let mut descendants = catalog
        .branches
        .iter()
        .filter(|b| !["main", "authored", "sibling"].contains(&b.scope.branch.as_str()))
        .collect::<Vec<_>>();
    descendants.sort_by(|a, b| a.scope.branch.cmp(&b.scope.branch));
    let mut children = Vec::new();
    let mut points = HashSet::new();
    for branch in descendants {
        let at = branch.fork_revision.ok_or_else(invalid)?;
        if !uuid(&branch.scope.branch)
            || branch.retired
            || branch.drafts != 0
            || branch.parent_branch.as_deref() != Some("authored")
            || ![0, 2, 3].contains(&at)
            || branch.revision != at
            || !points.insert(at)
        {
            return Err(invalid());
        }
        let actual = store.resume(&branch.scope).map_err(|_| invalid())?.engine;
        let child = expected[1]
            .fork(&branch.scope.branch, at)
            .map_err(|_| invalid())?;
        let expected_row = core_row(&child)?;
        let mut row = core_row(&actual)?;
        if row != expected_row {
            return Err(invalid());
        }
        row["turns_sha256"] = Value::Null;
        scopes.push(row);
        children.push(json!({"scope":actual.scope(),"parent":scope(PRIMARY,"authored"),"fork_revision":at,"core_prefix_matches":true,"expected":expected_row}));
    }
    let value = json!({"version":1,"kind":"domain2_fork_native_oracle_v1","fixture_version":1,"scopes":scopes,"children":children});
    if serde_json::to_vec(&value).map_err(|_| invalid())?.len() > ORACLE_CAP
        || serde_json::to_vec_pretty(&value)
            .map_err(|_| invalid())?
            .len()
            > ORACLE_CAP
    {
        return Err("SyntheticOracleBudget".into());
    }
    Ok(value)
}
