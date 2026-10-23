// Copyright 2026 LocalLore contributors. SPDX-License-Identifier: Apache-2.0
//! Development-only valid-cache pressure fixture. No SQL padding, schema changes or cap relief.
use crate::{derived_memory::*, validate_archive, Store};
use locallore::{contracts::*, engine::Engine};
use serde::{Deserialize, Serialize};
use serde_json::{json, Value};
use sha2::{Digest, Sha256};
use std::{
    fs,
    fs::OpenOptions,
    io::{Read, Write},
    path::{Path, PathBuf},
};

const OWNER: &[u8] = b"locallore-archive-capacity-v1";
const PAGES: u32 = 96;
const LIMIT: usize = 128 * 1024;
const CONTROL: &str = "archive-capacity-control-v1";
const SOURCE: &str = "archive-capacity-source-v1";
const CONTROL_TURNS: u64 = 10;
const CANARY: &str = "ARCHIVE_CAPACITY_SIBLING_CANARY";
type Result<T> = std::result::Result<T, &'static str>;

#[cfg(test)]
thread_local! { static LOCAL_TEST_CAP: std::cell::Cell<bool> = const { std::cell::Cell::new(false) }; }
#[cfg(test)]
pub(crate) fn with_local_cap<T>(operation: impl FnOnce() -> T) -> T {
    struct Reset(bool);
    impl Drop for Reset {
        fn drop(&mut self) {
            LOCAL_TEST_CAP.with(|value| value.set(self.0));
        }
    }
    let old = LOCAL_TEST_CAP.with(|value| value.replace(true));
    let _reset = Reset(old);
    operation()
}

fn require(value: bool) -> Result<()> {
    value.then_some(()).ok_or("Integrity")
}
fn linked(metadata: &fs::Metadata) -> bool {
    #[cfg(windows)]
    {
        use std::os::windows::fs::MetadataExt;
        metadata.file_attributes() & 0x400 != 0
    }
    #[cfg(not(windows))]
    {
        metadata.file_type().is_symlink()
    }
}
fn directory(path: &Path) -> Result<()> {
    require(path.is_absolute()).map_err(|_| "Path")?;
    let ancestors: Vec<_> = path.ancestors().collect();
    for ancestor in ancestors.into_iter().rev() {
        let metadata = fs::symlink_metadata(ancestor).map_err(|_| "Io")?;
        require(metadata.is_dir() && !linked(&metadata)).map_err(|_| "Path")?;
    }
    Ok(())
}
fn regular(path: &Path) -> Result<()> {
    directory(path.parent().ok_or("Path")?)?;
    let metadata = fs::symlink_metadata(path).map_err(|_| "Io")?;
    require(metadata.is_file() && !linked(&metadata)).map_err(|_| "Path")
}
fn read(path: &Path, limit: usize) -> Result<Vec<u8>> {
    regular(path)?;
    let mut bytes = Vec::new();
    fs::File::open(path)
        .map_err(|_| "Io")?
        .take((limit + 1) as u64)
        .read_to_end(&mut bytes)
        .map_err(|_| "Io")?;
    require(bytes.len() <= limit).map_err(|_| "TooLarge")?;
    Ok(bytes)
}
fn write(path: &Path, bytes: &[u8]) -> Result<()> {
    require(bytes.len() <= LIMIT).map_err(|_| "TooLarge")?;
    directory(path.parent().ok_or("Path")?)?;
    let mut file = OpenOptions::new()
        .create_new(true)
        .write(true)
        .open(path)
        .map_err(|_| "Io")?;
    file.write_all(bytes).map_err(|_| "Io")?;
    file.sync_all().map_err(|_| "Io")
}
fn digest(bytes: &[u8]) -> String {
    format!("{:x}", Sha256::digest(bytes))
}
fn target(root: &Path) -> PathBuf {
    root.join("workspace-v1").join("stories.sqlite3")
}
fn open(path: &Path) -> Result<Store> {
    let store = Store::open(path, None).map_err(|_| "Store")?;
    #[cfg(test)]
    if LOCAL_TEST_CAP.with(std::cell::Cell::get) {
        let actual: u32 = store
            .connection
            .query_row("PRAGMA max_page_count=96", [], |row| row.get(0))
            .map_err(|_| "Store")?;
        require(actual == PAGES)?;
    }
    let maximum: u32 = store
        .connection
        .pragma_query_value(None, "max_page_count", |row| row.get(0))
        .map_err(|_| "Store")?;
    require(maximum == PAGES).map_err(|_| "Profile")?;
    Ok(store)
}
fn metrics(store: &Store) -> Result<(u32, u32, u32)> {
    let pages = store
        .connection
        .pragma_query_value(None, "page_count", |row| row.get(0))
        .map_err(|_| "Store")?;
    let maximum = store
        .connection
        .pragma_query_value(None, "max_page_count", |row| row.get(0))
        .map_err(|_| "Store")?;
    let caches = store
        .connection
        .query_row("SELECT count(*) FROM derived_memory", [], |row| row.get(0))
        .map_err(|_| "Store")?;
    require(maximum == PAGES && pages <= maximum)?;
    Ok((pages, maximum, caches))
}
fn seed(story: &str) -> Result<Seed> {
    let mut seed: Seed = serde_json::from_str(include_str!("../../../fixtures/lantern_quay.json"))
        .map_err(|_| "Fixture")?;
    seed.scope.story = story.into();
    Ok(seed)
}
fn apply(store: &mut Store, scope: &Scope, id: &str, commands: Vec<Command>) -> Result<()> {
    let engine = store.resume(scope).map_err(|_| "Store")?.engine;
    let request = engine.request(id, Intent::Actions(commands));
    let proposal = Engine::proposal(&request).map_err(|_| "Engine")?;
    let receipt = engine.preview(&request, &proposal).map_err(|_| "Engine")?;
    store.begin_turn(&request).map_err(|_| "Store")?;
    store
        .commit_turn(&request, &proposal, receipt.narration())
        .map_err(|_| "Store")?;
    Ok(())
}
fn say(text: String) -> Vec<Command> {
    vec![Command::Say {
        text,
        audience: ["mira".into()].into(),
    }]
}
fn fork(store: &mut Store, scope: &Scope, child: &str) -> Result<Scope> {
    let revision = store.resume(scope).map_err(|_| "Store")?.engine.revision();
    store
        .fork_branch(
            &crate::ForkRequest {
                parent: scope.clone(),
                child_branch: child.into(),
                expected_parent_revision: revision,
                at_revision: 1,
            },
            &|| false,
        )
        .map(|branch| branch.scope)
        .map_err(|_| "Store")
}
fn export(store: &mut Store, story: &str) -> Result<Vec<u8>> {
    let archive = store
        .export_archive(story, &|| false)
        .map_err(|_| "Archive")?;
    require(archive.bytes().len() <= LIMIT).map_err(|_| "TooLarge")?;
    Ok(archive.bytes().to_vec())
}
fn source(root: &Path) -> Result<Vec<u8>> {
    let mut store = open(&root.join("source.sqlite3"))?;
    let seed = seed(SOURCE)?;
    let main = seed.scope.clone();
    store
        .create_story("Synthetic capacity archive", seed)
        .map_err(|_| "Store")?;
    apply(
        &mut store,
        &main,
        "shared-prefix",
        vec![Command::Wait { ticks: 1 }],
    )?;
    let child = fork(&mut store, &main, "child")?;
    apply(
        &mut store,
        &main,
        "main-statement",
        say("ARCHIVE_CAPACITY_MAIN_STATEMENT".into()),
    )?;
    apply(
        &mut store,
        &child,
        "child-consume",
        vec![Command::Consume {
            item: "potion".into(),
        }],
    )?;
    let sibling = fork(&mut store, &main, "sibling")?;
    apply(&mut store, &sibling, "sibling-private", say(CANARY.into()))?;
    let bytes = export(&mut store, SOURCE)?;
    drop(store);
    // Prove this exact artifact imports/replays into a fresh database under the same cap.
    let mut proof = open(&root.join("fit-proof.sqlite3"))?;
    proof
        .import_archive(
            validate_archive(&bytes, &|| false).map_err(|_| "Archive")?,
            &|| false,
        )
        .map_err(|_| "Fit")?;
    require(export(&mut proof, SOURCE)? == bytes)?;
    check_source(&mut proof)?;
    drop(proof);
    let mut reopened = open(&root.join("fit-proof.sqlite3"))?;
    require(export(&mut reopened, SOURCE)? == bytes)?;
    Ok(bytes)
}
fn scope(story: &str, branch: &str) -> Scope {
    Scope {
        story: story.into(),
        branch: branch.into(),
    }
}
fn memory(observer: &str, from: u64, target: Target) -> PrepareRequest {
    PrepareRequest {
        scope: scope(CONTROL, "main"),
        expected_revision: CONTROL_TURNS,
        observer: observer.into(),
        from_exclusive: from,
        through_revision: CONTROL_TURNS,
        target,
    }
}
fn mira_request() -> PrepareRequest {
    memory("mira", CONTROL_TURNS - 1, Target::SceneWindow)
}
fn fill(store: &mut Store) -> Result<()> {
    let prepared = store
        .prepare_memory(&mira_request(), &|| false)
        .map_err(|_| "Memory")?;
    require(
        store
            .publish_memory(prepared, &|| false)
            .map_err(|_| "Memory")?
            == PublishOutcome::Published,
    )?;
    for from in 0..CONTROL_TURNS {
        for target in [
            Target::SceneWindow,
            Target::Entity {
                kind: EntityKind::Actor,
                id: "player".into(),
            },
            Target::Entity {
                kind: EntityKind::Actor,
                id: "mira".into(),
            },
        ] {
            let request = memory("player", from, target);
            let prepared = store
                .prepare_memory(&request, &|| false)
                .map_err(|_| "Memory")?;
            match store.publish_memory(prepared, &|| false) {
                Ok(PublishOutcome::Published) => (),
                Err(MemoryError::Full) => return Ok(()),
                _ => return Err("Calibration"),
            }
        }
    }
    Err("Calibration")
}
#[derive(Serialize, Deserialize)]
#[serde(deny_unknown_fields)]
struct Baseline {
    version: u32,
    caches: u32,
    source_sha256: String,
    control_sha256: String,
    mira: Value,
    control_rows: Vec<u32>,
}
fn rows(store: &Store, story: &str) -> Result<Vec<u32>> {
    [
        "stories",
        "branches",
        "turns",
        "entities",
        "branch_entities",
        "accepted_events",
        "event_witnesses",
        "branch_projections",
    ]
    .into_iter()
    .map(|table| {
        store
            .connection
            .query_row(
                &format!("SELECT count(*) FROM {table} WHERE story_id=?1"),
                [story],
                |row| row.get(0),
            )
            .map_err(|_| "Store")
    })
    .collect()
}
fn baseline(root: &Path) -> Result<Baseline> {
    let bytes = read(&root.join("fixture-baseline.json"), LIMIT)?;
    let baseline: Baseline = serde_json::from_slice(&bytes).map_err(|_| "Integrity")?;
    require(baseline.version == 1 && baseline.caches > 1 && baseline.caches <= 33)?;
    Ok(baseline)
}
fn check_control(root: &Path, store: &mut Store, baseline: &Baseline) -> Result<()> {
    require(rows(store, CONTROL)? == baseline.control_rows)?;
    let bytes = export(store, CONTROL)?;
    require(bytes == read(&root.join("control-baseline.json"), LIMIT)?)?;
    require(digest(&bytes) == baseline.control_sha256)?;
    let engine = store
        .resume(&scope(CONTROL, "main"))
        .map_err(|_| "Store")?
        .engine;
    require(
        engine.revision() == CONTROL_TURNS && engine.receipts().len() == CONTROL_TURNS as usize,
    )?;
    require(
        store
            .read_memory(&mira_request(), &|| false)
            .map_err(|_| "Memory")?
            .json()
            == &baseline.mira,
    )
}
fn check_source(store: &mut Store) -> Result<()> {
    for branch in ["main", "child", "sibling"] {
        let engine = store
            .resume(&scope(SOURCE, branch))
            .map_err(|_| "Store")?
            .engine;
        require(engine.revision() == 2 && engine.receipts().len() == 2)?;
        require(
            engine
                .state()
                .items
                .get("potion")
                .is_some_and(|item| item.owner == "player")
                == (branch != "child"),
        )?;
        for observer in ["player", "mira", "sable", "oren"] {
            let context = engine
                .character_context(observer, engine.scope(), 2)
                .map_err(|_| "Engine")?;
            let visible = serde_json::to_string(&context).map_err(|_| "Integrity")?;
            require(
                visible.contains(CANARY)
                    == (branch == "sibling" && matches!(observer, "player" | "mira")),
            )?;
            require(visible.contains("SECRET-TIDE-731") == (observer == "player"))?;
        }
    }
    Ok(())
}
fn owned(root: &Path) -> Result<()> {
    require(root.is_absolute()).map_err(|_| "Path")?;
    let parent = root.parent().ok_or("Path")?;
    require(
        parent
            .file_name()
            .is_some_and(|name| name == "archive-capacity"),
    )
    .map_err(|_| "Path")?;
    let run = root
        .file_name()
        .and_then(|name| name.to_str())
        .ok_or("Path")?;
    require(
        !run.is_empty()
            && run.len() <= 48
            && run
                .bytes()
                .all(|byte| byte.is_ascii_lowercase() || byte.is_ascii_digit() || byte == b'-'),
    )
    .map_err(|_| "Path")?;
    directory(parent)
}
fn setup(root: &Path) -> Result<Value> {
    owned(root)?;
    fs::create_dir(root).map_err(|_| "Exists")?;
    write(&root.join("owner-v1"), OWNER)?;
    fs::create_dir(root.join("workspace-v1")).map_err(|_| "Io")?;
    let bytes = source(root)?;
    write(&root.join("archive.json"), &bytes)?;
    let mut store = open(&target(root))?;
    let seed = seed(CONTROL)?;
    let control = seed.scope.clone();
    store
        .create_story("Synthetic retained capacity control", seed)
        .map_err(|_| "Store")?;
    for turn in 0..CONTROL_TURNS {
        apply(
            &mut store,
            &control,
            &format!("cache-source-{turn}"),
            say("C".repeat(2048)),
        )?;
    }
    let control_bytes = export(&mut store, CONTROL)?;
    write(&root.join("control-baseline.json"), &control_bytes)?;
    fill(&mut store)?;
    let (_, _, caches) = metrics(&store)?;
    let baseline = Baseline {
        version: 1,
        caches,
        source_sha256: digest(&bytes),
        control_sha256: digest(&control_bytes),
        mira: store
            .read_memory(&mira_request(), &|| false)
            .map_err(|_| "Memory")?
            .json()
            .clone(),
        control_rows: rows(&store, CONTROL)?,
    };
    write(
        &root.join("fixture-baseline.json"),
        &serde_json::to_vec(&baseline).map_err(|_| "Integrity")?,
    )?;
    check_control(root, &mut store, &baseline)?;
    drop(store);
    inspect(root, "setup", false, true)
}
fn inspect(root: &Path, mode: &str, imported: bool, pressured: bool) -> Result<Value> {
    owned(root)?;
    directory(root)?;
    require(read(&root.join("owner-v1"), OWNER.len())? == OWNER)?;
    regular(&target(root))?;
    let bytes = read(&root.join("archive.json"), LIMIT)?;
    let baseline = baseline(root)?;
    require(digest(&bytes) == baseline.source_sha256)?;
    let validated = validate_archive(&bytes, &|| false).map_err(|_| "Archive")?;
    require(
        validated.preview().story_id == SOURCE
            && validated.preview().branch_heads.len() == 3
            && validated.preview().committed_turns == 4,
    )?;
    let mut store = open(&target(root))?;
    check_control(root, &mut store, &baseline)?;
    let stories = store.stories().map_err(|_| "Store")?;
    require(stories.len() == if imported { 2 } else { 1 })?;
    require(stories.iter().any(|story| story.scope.story == SOURCE) == imported)?;
    if !imported {
        require(rows(&store, SOURCE)?.iter().all(|count| *count == 0))?;
    }
    if imported {
        require(export(&mut store, SOURCE)? == bytes)?;
        check_source(&mut store)?;
    }
    let (pages, maximum, caches) = metrics(&store)?;
    require(caches == if pressured { baseline.caches } else { 1 })?;
    Ok(
        json!({"version":1,"status":"ok","mode":mode,"page_count":pages,"max_page_count":maximum,
        "cache_count":caches,"source_story":SOURCE,"source_branch":"main","source_revision":2,
        "control_story":CONTROL,"control_branch":"main","control_revision":CONTROL_TURNS,
        "canonical_unchanged":true,"imported":imported,"archive_exact":imported}),
    )
}
fn relieve(root: &Path) -> Result<Value> {
    inspect(root, "relieve", false, true)?;
    let mut store = open(&target(root))?;
    store
        .invalidate_memory(&scope(CONTROL, "main"), "player", CONTROL_TURNS, &|| false)
        .map_err(|_| "Memory")?;
    drop(store);
    inspect(root, "relieve", false, false)
}
/// This feature is intentionally absent from ordinary release modules/JNI. Existing model,
/// document, Store and schema authorities do not accept a new capacity or raw SQL parameter.
pub fn run(root: &Path, mode: &str) -> std::result::Result<Value, String> {
    let result = match mode {
        "setup" => setup(root),
        "check-full" => inspect(root, mode, false, true),
        "relieve" => relieve(root),
        "check-imported" => inspect(root, mode, true, false),
        _ => Err("Mode"),
    };
    result.map_err(str::to_owned)
}
