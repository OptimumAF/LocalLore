// Copyright 2026 LocalLore contributors. SPDX-License-Identifier: Apache-2.0
//! Explicit synthetic transfer proof, not a general archive CLI or a model/device benchmark.
use locallore::{contracts::*, engine::Engine};
use locallore_android::workspace::WorkspaceRegistry;
use locallore_storage::{validate_archive, ForkRequest, Store, TurnError, TurnPhase};
use serde_json::{json, Value};
use std::{
    collections::BTreeMap,
    ffi::OsString,
    fs::{self, File, OpenOptions},
    io::{Read, Write},
    path::{Path, PathBuf},
};

const LIMIT: usize = 128 * 1024;
const FIXTURE: &str = "locallore-platform-roundtrip-v1";
const WINDOWS: &str = "platform-windows-v1";
const CANARY: &str = "PLATFORM_SIBLING_CANARY";
type Result<T> = std::result::Result<T, &'static str>;
type Engines = BTreeMap<String, Engine>;

#[derive(Clone, Copy, Debug, PartialEq, Eq)]
enum Mode {
    Generate,
    Verify,
    CheckFinal,
}
impl Mode {
    fn name(self) -> &'static str {
        match self {
            Self::Generate => "generate",
            Self::Verify => "verify",
            Self::CheckFinal => "check-final",
        }
    }
}
struct Arguments {
    mode: Mode,
    directory: PathBuf,
    inputs: Option<PathBuf>,
    fixtures: Option<PathBuf>,
}
impl Arguments {
    fn parse(args: Vec<OsString>) -> Result<Self> {
        let mut args = args.into_iter();
        require(args.next().as_deref() == Some(std::ffi::OsStr::new("--development-fixtures")))
            .map_err(|_| "Arguments")?;
        let mode = match args.next().and_then(|s| s.into_string().ok()).as_deref() {
            Some("generate") => Mode::Generate,
            Some("verify") => Mode::Verify,
            Some("check-final") => Mode::CheckFinal,
            _ => return Err("Arguments"),
        };
        let (mut directory, mut inputs, mut fixtures) = (None, None, None);
        while let Some(key) = args.next() {
            let slot = match key.to_str() {
                Some("--directory") => &mut directory,
                Some("--inputs") if mode != Mode::Generate => &mut inputs,
                Some("--fixtures") if mode != Mode::Generate => &mut fixtures,
                _ => return Err("Arguments"),
            };
            if slot.is_some() {
                return Err("Arguments");
            }
            let value = args.next().ok_or("Arguments")?;
            if value.is_empty() || value.to_string_lossy().starts_with("--") {
                return Err("Arguments");
            }
            *slot = Some(PathBuf::from(value));
        }
        let directory = directory.ok_or("Arguments")?;
        if mode != Mode::Generate && (inputs.is_none() || fixtures.is_none()) {
            return Err("Arguments");
        }
        Ok(Self {
            mode,
            directory,
            inputs,
            fixtures,
        })
    }
}
fn require(condition: bool) -> Result<()> {
    condition.then_some(()).ok_or("Mismatch")
}
fn directory(path: &Path) -> Result<()> {
    let absolute = if path.is_absolute() {
        path.to_owned()
    } else {
        std::env::current_dir().map_err(|_| "Io")?.join(path)
    };
    // Inspect from the filesystem root down, before following any selected ancestor.
    // No creation or file read occurs until every existing component is a real directory.
    // This is path validation for the explicit fixture, not a same-UID race defense.
    let ancestors: Vec<_> = absolute.ancestors().collect();
    for ancestor in ancestors.into_iter().rev() {
        let metadata = fs::symlink_metadata(ancestor).map_err(|_| "Io")?;
        require(metadata.is_dir() && !linked(&metadata)).map_err(|_| "Io")?;
    }
    Ok(())
}
fn linked(metadata: &fs::Metadata) -> bool {
    #[cfg(windows)]
    {
        use std::os::windows::fs::MetadataExt;
        // Refuse junctions and other reparse points as well as symbolic links.
        metadata.file_attributes() & 0x400 != 0
    }
    #[cfg(not(windows))]
    {
        metadata.file_type().is_symlink()
    }
}
fn fresh_directory(path: &Path) -> Result<PathBuf> {
    let path = if path.is_absolute() {
        path.to_owned()
    } else {
        std::env::current_dir().map_err(|_| "Io")?.join(path)
    };
    directory(path.parent().ok_or("Io")?)?;
    fs::create_dir(&path).map_err(|_| "Io")?;
    path.canonicalize().map_err(|_| "Io")
}
fn read(root: &Path, name: &str) -> Result<Vec<u8>> {
    directory(root).map_err(|_| "Input")?;
    let path = root.join(name);
    let metadata = fs::symlink_metadata(&path).map_err(|_| "Input")?;
    if !metadata.is_file() || linked(&metadata) {
        return Err("Input");
    }
    if metadata.len() > LIMIT as u64 {
        return Err("Bounds");
    }
    let mut bytes = Vec::new();
    File::open(path)
        .map_err(|_| "Input")?
        .take((LIMIT + 1) as u64)
        .read_to_end(&mut bytes)
        .map_err(|_| "Input")?;
    if bytes.len() > LIMIT {
        return Err("Bounds");
    }
    Ok(bytes)
}
fn write(root: &Path, name: &str, bytes: &[u8]) -> Result<()> {
    directory(root)?;
    if bytes.len() > LIMIT {
        return Err("Bounds");
    }
    let mut file = OpenOptions::new()
        .write(true)
        .create_new(true)
        .open(root.join(name))
        .map_err(|_| "Io")?;
    file.write_all(bytes).map_err(|_| "Io")?;
    file.sync_all().map_err(|_| "Io")
}
fn encode(value: &impl serde::Serialize) -> Result<Vec<u8>> {
    serde_json::to_vec(value).map_err(|_| "Internal")
}
fn seed(story: &str) -> Result<Seed> {
    let mut seed: Seed = serde_json::from_str(include_str!("../../../fixtures/lantern_quay.json"))
        .map_err(|_| "Internal")?;
    seed.scope.story = story.into();
    Ok(seed)
}
fn give() -> Vec<Command> {
    vec![Command::Give {
        item: "potion".into(),
        to: "mira".into(),
        quantity: 1,
    }]
}
fn wait() -> Vec<Command> {
    vec![Command::Wait { ticks: 1 }]
}
fn commit_engine(engine: &mut Engine, id: &str, commands: Vec<Command>) -> Result<Receipt> {
    let request = engine.request(id, Intent::Actions(commands));
    let proposal = Engine::proposal(&request).map_err(|_| "Engine")?;
    let preview = engine.preview(&request, &proposal).map_err(|_| "Engine")?;
    engine
        .commit(&request, &proposal, preview.narration())
        .map_err(|_| "Engine")
}
fn apply(store: &mut Store, scope: &Scope, id: &str, commands: Vec<Command>) -> Result<Receipt> {
    let mut engine = store.resume(scope).map_err(|_| "Store")?.engine;
    let receipt = commit_engine(&mut engine, id, commands)?;
    store.begin_turn(receipt.request()).map_err(|_| "Store")?;
    store
        .commit_turn(receipt.request(), receipt.proposal(), receipt.narration())
        .map_err(|_| "Store")
}
fn fork(store: &mut Store, root: &Scope, child: &str) -> Result<Scope> {
    let head = store.resume(root).map_err(|_| "Store")?.engine.revision();
    store
        .fork_branch(
            &ForkRequest {
                parent: root.clone(),
                child_branch: child.into(),
                expected_parent_revision: head,
                at_revision: 1,
            },
            &|| false,
        )
        .map(|branch| branch.scope)
        .map_err(|_| "Store")
}
fn windows_expected(continued: bool) -> Result<Engines> {
    let mut main = Engine::new(seed(WINDOWS)?).map_err(|_| "Engine")?;
    commit_engine(&mut main, "shared-prefix", wait())?;
    let mut child = main.fork("child", 1).map_err(|_| "Engine")?;
    commit_engine(&mut main, "same-turn-key", give())?;
    commit_engine(
        &mut child,
        "same-turn-key",
        vec![Command::Consume {
            item: "potion".into(),
        }],
    )?;
    let mut sibling = main.fork("sibling", 1).map_err(|_| "Engine")?;
    commit_engine(
        &mut sibling,
        "sibling-private",
        vec![Command::Say {
            text: CANARY.into(),
            audience: ["mira".into()].into(),
        }],
    )?;
    if continued {
        commit_engine(&mut sibling, "android-transfer-gift-v1", give())?;
    }
    Ok(BTreeMap::from([
        ("main".into(), main),
        ("child".into(), child),
        ("sibling".into(), sibling),
    ]))
}
fn contexts(engine: &Engine) -> Result<Value> {
    let mut result = serde_json::Map::new();
    for actor in ["player", "mira", "sable", "oren"] {
        let context = engine
            .character_context(actor, engine.scope(), engine.revision())
            .map_err(|_| "Engine")?;
        let text = serde_json::to_string(&context).map_err(|_| "Internal")?;
        require(text.contains("SECRET-TIDE-731") == (actor == "player"))?;
        require(
            text.contains(CANARY)
                == (engine.scope().story == WINDOWS
                    && engine.scope().branch == "sibling"
                    && (actor == "player" || actor == "mira")),
        )?;
        result.insert(
            actor.into(),
            serde_json::to_value(context).map_err(|_| "Internal")?,
        );
    }
    require(matches!(
        engine.character_context("player", engine.scope(), engine.revision() + 1),
        Err(Error::Stale)
    ))?;
    let foreign = Scope {
        story: "not-this-story".into(),
        branch: engine.scope().branch.clone(),
    };
    require(matches!(
        engine.character_context("player", &foreign, engine.revision()),
        Err(Error::Scope)
    ))?;
    Ok(Value::Object(result))
}
fn compare_engine(actual: &Engine, expected: &Engine) -> Result<()> {
    require(actual.scope() == expected.scope())?;
    require(actual.seed() == expected.seed())?;
    require(actual.canonical_bytes() == expected.canonical_bytes())?;
    require(actual.receipts() == expected.receipts())?;
    require(contexts(actual)? == contexts(expected)?)
}
fn export(path: &Path, story: &str) -> Result<Vec<u8>> {
    let mut store = Store::open_read_only(path).map_err(|_| "Store")?;
    let archive = store
        .export_archive(story, &|| false)
        .map_err(|_| "Archive")?;
    require(archive.bytes().len() <= LIMIT).map_err(|_| "Bounds")?;
    require(!archive.preview().noncommitted_workflow_transferred)?;
    Ok(archive.bytes().to_vec())
}
fn verify_store(path: &Path, expected: &Engines) -> Result<()> {
    // Each call closes and strictly reopens the actual persisted Engine, not a cached snapshot.
    let mut store = Store::open_read_only(path).map_err(|_| "Store")?;
    for engine in expected.values() {
        let actual = store.resume(engine.scope()).map_err(|_| "Store")?.engine;
        compare_engine(&actual, engine)?;
        for receipt in actual.receipts() {
            require(
                serde_json::to_value(receipt).map_err(|_| "Internal")?["events"]
                    .as_array()
                    .is_some_and(|events| !events.is_empty()),
            )?;
        }
    }
    Ok(())
}
fn import(path: &Path, bytes: &[u8], expected: &Engines) -> Result<()> {
    let validated = validate_archive(bytes, &|| false).map_err(|_| "Archive")?;
    require(validated.preview().branch_heads.len() == expected.len())?;
    let mut store = Store::open(path, None).map_err(|_| "Store")?;
    // Preserve an independent synthetic story in every destination, including its receipt.
    let retained_seed = seed("platform-retained-v1")?;
    let retained = retained_seed.scope.clone();
    store
        .create_story("Retained synthetic control", retained_seed)
        .map_err(|_| "Store")?;
    apply(&mut store, &retained, "retained-control", wait())?;
    let retained_before = store.resume(&retained).map_err(|_| "Store")?.engine;
    let imported = store
        .import_archive(validated, &|| false)
        .map_err(|_| "Archive")?;
    require(
        expected
            .values()
            .any(|engine| engine.scope() == &imported.root),
    )?;
    require(imported.branches == expected.len())?;
    compare_engine(
        &store.resume(&retained).map_err(|_| "Store")?.engine,
        &retained_before,
    )?;
    drop(store);
    verify_store(path, expected)?;
    require(export(path, &imported.root.story)? == bytes)?;
    let mut reopened = Store::open_read_only(path).map_err(|_| "Store")?;
    compare_engine(
        &reopened.resume(&retained).map_err(|_| "Store")?.engine,
        &retained_before,
    )
}
struct Owner {
    registry: WorkspaceRegistry,
    handle: u64,
}
impl Owner {
    fn open(path: &Path) -> Result<Self> {
        let registry = WorkspaceRegistry::default();
        let handle = registry.open(path).map_err(|_| "Host")?;
        Ok(Self { registry, handle })
    }
    fn call(&self, command: Value) -> Result<Value> {
        let bytes = self.registry.call(
            self.handle,
            &encode(&json!({"version":1,"command":command}))?,
        );
        locallore::engine::parse_unique_json(&bytes, 262_144).map_err(|_| "Host")
    }
    fn data(&self, command: Value) -> Result<Value> {
        let reply = self.call(command)?;
        require(reply["version"] == 1 && reply["status"] == "ok").map_err(|_| "Host")?;
        Ok(reply["data"].clone())
    }
    fn resume(&self, scope: &Scope) -> Result<Value> {
        self.data(json!({"op":"resume","scope":scope}))
    }
    fn scoped(&self, session: &Value, op: &str, id: &str) -> Result<Value> {
        self.data(json!({"op":op,"session":session["session"],"scope":session["scope"],"turn":id}))
    }
    fn snapshot(&self, session: &Value, revision: u64) -> Result<Value> {
        self.data(json!({"op":"play_snapshot","session":session["session"],"scope":session["scope"],"expected_revision":revision}))
    }
    fn forbidden(&self, session: &Value, revision: u64) -> Result<()> {
        for observer in ["mira", "sable", "omniscient"] {
            let reply = self.call(json!({"op":"inspect","session":session["session"],"scope":session["scope"],"expected_revision":revision,"observer":observer}))?;
            require(reply["status"] == "rejected" && reply["error"] == "Forbidden")?;
        }
        Ok(())
    }
    fn retry(&self, session: &Value, engine: &Engine, receipt: &Receipt) -> Result<()> {
        let before = self.snapshot(session, engine.revision())?;
        let submit = self.data(json!({"op":"submit","session":session["session"],"request":receipt.request(),"mode":"accepted"}))?;
        require(submit["phase"] == "committed")?;
        let committed = self.scoped(session, "commit", &receipt.request().turn)?;
        require(committed["phase"] == "committed")?;
        require(committed["receipt"] == serde_json::to_value(receipt).map_err(|_| "Internal")?)?;
        require(self.snapshot(session, engine.revision())? == before)
    }
    fn deny_spend(&self, session: &Value, engine: &Engine) -> Result<()> {
        let before = self.snapshot(session, engine.revision())?;
        let request = engine.request(
            &format!("rejected-spend-head-{}", engine.revision()),
            Intent::Actions(give()),
        );
        let reply = self.call(
            json!({"op":"submit","session":session["session"],"request":request,"mode":"accepted"}),
        )?;
        require(reply["status"] == "rejected" && reply["error"] == "Inventory")?;
        require(self.snapshot(session, engine.revision())? == before)
    }
}
impl Drop for Owner {
    fn drop(&mut self) {
        self.registry.close(self.handle);
    }
}
fn snapshots(path: &Path, expected: &Engines) -> Result<Value> {
    let owner = Owner::open(path)?;
    let mut snapshots = serde_json::Map::new();
    for (branch, engine) in expected {
        let session = owner.resume(engine.scope())?;
        owner.forbidden(&session, engine.revision())?;
        snapshots.insert(branch.clone(), owner.snapshot(&session, engine.revision())?);
    }
    Ok(Value::Object(snapshots))
}
fn continuation(path: &Path, before: &Engine, id: &str, commands: Vec<Command>) -> Result<Engine> {
    let owner = Owner::open(path)?;
    let session = owner.resume(before.scope())?;
    let frozen = owner.snapshot(&session, before.revision())?;
    let mut expected = before.clone();
    let receipt = commit_engine(&mut expected, id, commands)?;
    let submitted = owner.data(json!({"op":"submit","session":session["session"],"request":receipt.request(),"mode":"accepted"}))?;
    require(submitted["phase"] == "queued")?;
    require(owner.scoped(&session, "prepare", id)?["phase"] == "ready")?;
    require(owner.snapshot(&session, before.revision())? == frozen)?;
    let committed = owner.scoped(&session, "commit", id)?;
    require(committed["phase"] == "committed")?;
    require(committed["receipt"] == serde_json::to_value(&receipt).map_err(|_| "Internal")?)?;
    owner.retry(&session, &expected, &receipt)?;
    owner.deny_spend(&session, &expected)?;
    owner.forbidden(&session, expected.revision())?;
    drop(owner);
    let mut store = Store::open_read_only(path).map_err(|_| "Store")?;
    compare_engine(
        &store.resume(expected.scope()).map_err(|_| "Store")?.engine,
        &expected,
    )?;
    Ok(expected)
}
fn manifest(initial: Value, continued: Value) -> Value {
    json!({"version":1,"fixture":FIXTURE,"windows":{"story":WINDOWS,"root":"main",
        "continuation_branch":"sibling","continuation_turn":"android-transfer-gift-v1",
        "branch_heads":{"main":2,"child":2,"sibling":2},"snapshots":initial,"continued_snapshots":continued}})
}
fn generate(out: &Path) -> Result<()> {
    let path = out.join("windows-source.sqlite3");
    let mut store = Store::open(&path, None).map_err(|_| "Store")?;
    let seed = seed(WINDOWS)?;
    let main = seed.scope.clone();
    store
        .create_story("Synthetic Windows transfer", seed)
        .map_err(|_| "Store")?;
    apply(&mut store, &main, "shared-prefix", wait())?;
    let child = fork(&mut store, &main, "child")?;
    apply(&mut store, &main, "same-turn-key", give())?;
    apply(
        &mut store,
        &child,
        "same-turn-key",
        vec![Command::Consume {
            item: "potion".into(),
        }],
    )?;
    let sibling = fork(&mut store, &main, "sibling")?;
    apply(
        &mut store,
        &sibling,
        "sibling-private",
        vec![Command::Say {
            text: CANARY.into(),
            audience: ["mira".into()].into(),
        }],
    )?;
    let draft = store
        .resume(&main)
        .map_err(|_| "Store")?
        .engine
        .request("EXCLUDED_PLATFORM_DRAFT", Intent::Actions(wait()));
    store.begin_turn(&draft).map_err(|_| "Store")?;
    require(store.turn_status(&draft).map_err(|_| "Store")?.phase == TurnPhase::Draft)?;
    drop(store);
    let expected = windows_expected(false)?;
    verify_store(&path, &expected)?;
    let origin = export(&path, WINDOWS)?;
    require(
        !std::str::from_utf8(&origin)
            .map_err(|_| "Archive")?
            .contains("EXCLUDED_PLATFORM_DRAFT"),
    )?;
    let preview = validate_archive(&origin, &|| false).map_err(|_| "Archive")?;
    require(
        preview.preview().branch_heads
            == BTreeMap::from([
                ("main".into(), 2),
                ("child".into(), 2),
                ("sibling".into(), 2),
            ]),
    )?;
    require(preview.preview().committed_turns == 4)?;
    write(out, "windows-origin.json", &origin)?;
    let initial = snapshots(&path, &expected)?;
    let sibling = expected.get("sibling").ok_or("Internal")?;
    continuation(&path, sibling, "android-transfer-gift-v1", give())?;
    let continued = windows_expected(true)?;
    verify_store(&path, &continued)?;
    write(out, "windows-continued.json", &export(&path, WINDOWS)?)?;
    write(
        out,
        "expectations.json",
        &encode(&manifest(initial, snapshots(&path, &continued)?))?,
    )
}
fn android_expected(bytes: &[u8], waits: u8) -> Result<Engines> {
    let validated = validate_archive(bytes, &|| false).map_err(|_| "Archive")?;
    let preview = validated.preview();
    require(preview.title == "Lantern Quay" && preview.root_branch == "main")?;
    require(preview.branch_heads == BTreeMap::from([("main".into(), u64::from(waits) + 1)]))?;
    require(preview.committed_turns == usize::from(waits) + 1)?;
    let expected_seed = seed(&preview.story_id)?;
    let value = locallore::engine::parse_unique_json(bytes, LIMIT).map_err(|_| "Archive")?;
    require(
        value["payload"]["story"]["seed"]
            == serde_json::to_value(&expected_seed).map_err(|_| "Internal")?,
    )?;
    let mut engine = Engine::new(expected_seed).map_err(|_| "Engine")?;
    commit_engine(&mut engine, "android-origin-gift-v1", give())?;
    if waits >= 1 {
        commit_engine(&mut engine, "windows-return-wait-v1", wait())?;
    }
    if waits >= 2 {
        commit_engine(&mut engine, "android-final-wait-v1", wait())?;
    }
    Ok(BTreeMap::from([("main".into(), engine)]))
}
fn check_retry(path: &Path, engine: &Engine) -> Result<()> {
    let owner = Owner::open(path)?;
    let session = owner.resume(engine.scope())?;
    // Inherited receipts retain their original parent scope; a child session must
    // never submit them as child-owned keys. The parent is checked independently.
    for receipt in engine
        .receipts()
        .iter()
        .filter(|receipt| receipt.request().scope == *engine.scope())
    {
        owner.retry(&session, engine, receipt)?;
    }
    owner.deny_spend(&session, engine)?;
    owner.forbidden(&session, engine.revision())
}
fn verify(out: &Path, inputs: &Path, fixtures: &Path) -> Result<()> {
    let windows = read(inputs, "windows-return.json")?;
    let continued = read(inputs, "windows-continued.json")?;
    require(windows == read(fixtures, "windows-origin.json")?)?;
    require(continued == read(fixtures, "windows-continued.json")?)?;
    let initial_expected = windows_expected(false)?;
    let continued_expected = windows_expected(true)?;
    let initial_path = out.join("windows-return.sqlite3");
    let continued_path = out.join("windows-continued.sqlite3");
    import(&initial_path, &windows, &initial_expected)?;
    import(&continued_path, &continued, &continued_expected)?;
    let expected_manifest = manifest(
        snapshots(&initial_path, &initial_expected)?,
        snapshots(&continued_path, &continued_expected)?,
    );
    require(
        locallore::engine::parse_unique_json(&read(fixtures, "expectations.json")?, LIMIT)
            .map_err(|_| "Input")?
            == expected_manifest,
    )?;
    // Noncommitted workflow status cannot be transferred as an accepted request.
    let mut initial_store = Store::open_read_only(&initial_path).map_err(|_| "Store")?;
    let draft =
        initial_expected["main"].request("EXCLUDED_PLATFORM_DRAFT", Intent::Actions(wait()));
    require(matches!(
        initial_store.turn_status(&draft),
        Err(TurnError::UnknownTurn)
    ))?;
    drop(initial_store);
    for engine in continued_expected.values() {
        check_retry(&continued_path, engine)?;
    }
    let android = read(inputs, "android-origin.json")?;
    let expected = android_expected(&android, 0)?;
    let android_path = out.join("android-origin.sqlite3");
    import(&android_path, &android, &expected)?;
    let engine = &expected["main"];
    check_retry(&android_path, engine)?;
    let returned = continuation(&android_path, engine, "windows-return-wait-v1", wait())?;
    let returned_map = BTreeMap::from([("main".into(), returned.clone())]);
    verify_store(&android_path, &returned_map)?;
    let bytes = export(&android_path, &returned.scope().story)?;
    write(out, "android-return.json", &bytes)?;
    let final_path = out.join("android-final-control.sqlite3");
    import(&final_path, &bytes, &returned_map)?;
    let final_engine = continuation(&final_path, &returned, "android-final-wait-v1", wait())?;
    verify_store(
        &final_path,
        &BTreeMap::from([("main".into(), final_engine.clone())]),
    )?;
    write(
        out,
        "expected-android-final.json",
        &export(&final_path, &final_engine.scope().story)?,
    )
}
fn check_final(out: &Path, inputs: &Path, fixtures: &Path) -> Result<()> {
    let bytes = read(inputs, "android-final.json")?;
    require(bytes == read(fixtures, "expected-android-final.json")?)?;
    let expected = android_expected(&bytes, 2)?;
    let path = out.join("android-final.sqlite3");
    import(&path, &bytes, &expected)?;
    check_retry(&path, &expected["main"])?;
    verify_store(&path, &expected)
}
fn run_with_stdin(mut args: Vec<OsString>, stdin: &mut impl Read) -> Result<Mode> {
    let owned = args.iter().filter(|arg| *arg == "--owned-stdin").count();
    if owned != 0 {
        // The Windows Job process owner closes stdin only after assignment. Never start
        // fixture work (or exit on an argument error) before that ownership handshake.
        let mut byte = [0u8; 1];
        if stdin.read(&mut byte).map_err(|_| "Input")? != 0 {
            return Err("Input");
        }
        if owned > 1 {
            return Err("Arguments");
        }
        args.retain(|arg| arg != "--owned-stdin");
    }
    let args = Arguments::parse(args)?;
    for input in [&args.inputs, &args.fixtures].into_iter().flatten() {
        directory(input)?;
    }
    let out = fresh_directory(&args.directory)?;
    match args.mode {
        Mode::Generate => generate(&out)?,
        Mode::Verify => verify(
            &out,
            args.inputs.as_deref().ok_or("Arguments")?,
            args.fixtures.as_deref().ok_or("Arguments")?,
        )?,
        Mode::CheckFinal => check_final(
            &out,
            args.inputs.as_deref().ok_or("Arguments")?,
            args.fixtures.as_deref().ok_or("Arguments")?,
        )?,
    }
    write(
        &out,
        "result.json",
        &encode(&json!({"version":1,"fixture":FIXTURE,"status":"passed","mode":args.mode.name()}))?,
    )?;
    Ok(args.mode)
}
fn main() {
    // No filesystem path, SQL, story prose or unexpected panic payload reaches CLI diagnostics.
    std::panic::set_hook(Box::new(|_| eprintln!("Internal")));
    let result = std::panic::catch_unwind(|| {
        run_with_stdin(
            std::env::args_os().skip(1).collect(),
            &mut std::io::stdin().lock(),
        )
    });
    match result {
        Ok(Ok(mode)) => println!("{{\"status\":\"passed\",\"mode\":\"{}\"}}", mode.name()),
        Ok(Err(category)) => {
            eprintln!("{category}");
            std::process::exit(1);
        }
        Err(_) => std::process::exit(1),
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use std::sync::atomic::{AtomicU64, Ordering};
    static NEXT: AtomicU64 = AtomicU64::new(0);
    // Synthetic evidence is retained. Neither the tool nor its tests recursively delete.
    fn temp() -> PathBuf {
        let root = std::env::temp_dir().join(format!(
            "locallore-platform-fixture-{}-{}-{}",
            std::process::id(),
            std::time::SystemTime::now()
                .duration_since(std::time::UNIX_EPOCH)
                .unwrap()
                .as_nanos(),
            NEXT.fetch_add(1, Ordering::Relaxed)
        ));
        fs::create_dir(&root).unwrap();
        root
    }
    fn args(
        mode: &str,
        out: &Path,
        inputs: Option<&Path>,
        fixtures: Option<&Path>,
    ) -> Vec<OsString> {
        let mut args = vec![
            "--development-fixtures".into(),
            mode.into(),
            "--directory".into(),
            out.into(),
        ];
        if let Some(inputs) = inputs {
            args.extend(["--inputs".into(), inputs.into()]);
        }
        if let Some(fixtures) = fixtures {
            args.extend(["--fixtures".into(), fixtures.into()]);
        }
        args
    }
    fn run(args: Vec<OsString>) -> Result<Mode> {
        run_with_stdin(args, &mut &b""[..])
    }
    fn android_origin(root: &Path) -> Vec<u8> {
        let path = root.join("actual-origin.sqlite3");
        let owner = Owner::open(&path).unwrap();
        let session = owner
            .data(json!({"op":"create","seed":"lantern-quay-v1"}))
            .unwrap();
        let scope: Scope = serde_json::from_value(session["scope"].clone()).unwrap();
        drop(owner);
        let before = Engine::new(seed(&scope.story).unwrap()).unwrap();
        continuation(&path, &before, "android-origin-gift-v1", give()).unwrap();
        export(&path, &scope.story).unwrap()
    }
    fn outbound(root: &Path, fixtures: &Path) -> PathBuf {
        let input = root.join("outbound");
        fs::create_dir(&input).unwrap();
        write(
            &input,
            "windows-return.json",
            &read(fixtures, "windows-origin.json").unwrap(),
        )
        .unwrap();
        write(
            &input,
            "windows-continued.json",
            &read(fixtures, "windows-continued.json").unwrap(),
        )
        .unwrap();
        write(&input, "android-origin.json", &android_origin(root)).unwrap();
        input
    }
    #[test]
    fn generated_engine_oracle_matches_packaged_android_test_assets() {
        let output = temp().join("generated");
        assert_eq!(
            run(args("generate", &output, None, None)),
            Ok(Mode::Generate)
        );
        let assets: [(&str, &[u8]); 3] = [
            ("windows-origin.json", include_bytes!("../../../apps/android/app/src/androidTest/assets/platform-roundtrip-v1/windows-origin.json")),
            ("windows-continued.json", include_bytes!("../../../apps/android/app/src/androidTest/assets/platform-roundtrip-v1/windows-continued.json")),
            ("expectations.json", include_bytes!("../../../apps/android/app/src/androidTest/assets/platform-roundtrip-v1/expectations.json")),
        ];
        for (name, golden) in assets {
            let generated = read(&output, name).unwrap();
            if name == "expectations.json" {
                assert_eq!(generated, golden, "canonical snapshot fixture drift");
                continue;
            }
            // Preserve the historical schema2/v1 assets as compatibility inputs.
            // Validate both archives before allowing only source-version/checksum drift.
            validate_archive(golden, &|| false).unwrap();
            validate_archive(&generated, &|| false).unwrap();
            let mut historical: Value = serde_json::from_slice(golden).unwrap();
            let current: Value = serde_json::from_slice(&generated).unwrap();
            assert_eq!(historical["payload"]["source_database_schema_version"], 2);
            assert_eq!(
                current["payload"]["source_database_schema_version"],
                locallore_storage::SCHEMA_VERSION
            );
            historical["payload"]["source_database_schema_version"] =
                json!(locallore_storage::SCHEMA_VERSION);
            historical["integrity"]["payload_sha256"] =
                current["integrity"]["payload_sha256"].clone();
            assert_eq!(
                historical, current,
                "accepted history or branch integrity drift"
            );
            assert_eq!(
                serde_json::to_vec(&historical).unwrap(),
                generated,
                "canonical archive encoding drift"
            );
        }
    }
    #[test]
    fn all_three_modes_execute_real_host_retries_and_divergent_store_replay() {
        let root = temp();
        let fixtures = root.join("generated");
        assert_eq!(
            run(args("generate", &fixtures, None, None)),
            Ok(Mode::Generate)
        );
        let inputs = outbound(&root, &fixtures);
        let verified = root.join("verified");
        assert_eq!(
            run(args("verify", &verified, Some(&inputs), Some(&fixtures))),
            Ok(Mode::Verify)
        );
        // A second actual Host continues the reimported return, not a copy of the expected file.
        let returned = read(&verified, "android-return.json").unwrap();
        let expected = android_expected(&returned, 1).unwrap();
        let final_db = root.join("actual-final.sqlite3");
        import(&final_db, &returned, &expected).unwrap();
        let final_engine = continuation(
            &final_db,
            &expected["main"],
            "android-final-wait-v1",
            wait(),
        )
        .unwrap();
        let final_input = root.join("final-input");
        fs::create_dir(&final_input).unwrap();
        write(
            &final_input,
            "android-final.json",
            &export(&final_db, &final_engine.scope().story).unwrap(),
        )
        .unwrap();
        let final_out = root.join("checked");
        assert_eq!(
            run(args(
                "check-final",
                &final_out,
                Some(&final_input),
                Some(&verified)
            )),
            Ok(Mode::CheckFinal)
        );
        for output in [&fixtures, &verified, &final_out] {
            let result: Value =
                serde_json::from_slice(&read(output, "result.json").unwrap()).unwrap();
            assert_eq!(result["version"], 1);
            assert_eq!(result["status"], "passed");
        }
    }
    #[test]
    fn arguments_and_owned_stdin_fail_before_any_output_creation() {
        let root = temp();
        let out = root.join("must-not-exist");
        let valid = args("generate", &out, None, None);
        let mut missing = valid.clone();
        missing.remove(0);
        assert_eq!(run(missing), Err("Arguments"));
        let mut duplicate = valid.clone();
        duplicate.extend(["--directory".into(), out.clone().into()]);
        assert_eq!(run(duplicate), Err("Arguments"));
        let mut unknown = valid.clone();
        unknown.push("--private-PROSE-CANARY".into());
        assert_eq!(run(unknown), Err("Arguments"));
        let mut owned = valid.clone();
        owned.push("--owned-stdin".into());
        assert_eq!(
            run_with_stdin(owned.clone(), &mut &b"PRIVATE-CANARY"[..]),
            Err("Input")
        );
        owned.push("--owned-stdin".into());
        assert_eq!(run(owned), Err("Arguments"));
        assert!(!out.exists());
        let mut eof = valid;
        eof.push("--owned-stdin".into());
        assert_eq!(run(eof), Ok(Mode::Generate));
    }
    #[test]
    fn existing_outputs_and_exclusive_files_are_preserved() {
        let root = temp();
        let out = root.join("existing");
        fs::create_dir(&out).unwrap();
        write(&out, "result.json", b"PRIVATE-CONTROL").unwrap();
        assert_eq!(run(args("generate", &out, None, None)), Err("Io"));
        assert_eq!(write(&out, "result.json", b"replacement"), Err("Io"));
        assert_eq!(read(&out, "result.json").unwrap(), b"PRIVATE-CONTROL");
        assert_eq!(fs::read_dir(&out).unwrap().count(), 1);
    }
    #[test]
    fn altered_windows_bytes_fail_before_import_and_never_get_success_metadata() {
        let root = temp();
        let fixtures = root.join("generated");
        run(args("generate", &fixtures, None, None)).unwrap();
        let inputs = outbound(&root, &fixtures);
        let mut changed = read(&inputs, "windows-return.json").unwrap();
        changed.push(b' ');
        fs::write(inputs.join("windows-return.json"), changed).unwrap();
        let out = root.join("rejected");
        assert_eq!(
            run(args("verify", &out, Some(&inputs), Some(&fixtures))),
            Err("Mismatch")
        );
        assert_eq!(fs::read_dir(&out).unwrap().count(), 0);
    }
    #[test]
    fn canonical_but_different_android_history_cannot_masquerade_as_original_gift() {
        let root = temp();
        let fixtures = root.join("generated");
        run(args("generate", &fixtures, None, None)).unwrap();
        let inputs = outbound(&root, &fixtures);
        let path = root.join("wrong-origin.sqlite3");
        let mut store = Store::open(&path, None).unwrap();
        let wrong_seed = seed("synthetic-wrong-origin").unwrap();
        let scope = wrong_seed.scope.clone();
        store.create_story("Lantern Quay", wrong_seed).unwrap();
        apply(&mut store, &scope, "android-origin-gift-v1", wait()).unwrap();
        drop(store);
        fs::write(
            inputs.join("android-origin.json"),
            export(&path, &scope.story).unwrap(),
        )
        .unwrap();
        let out = root.join("rejected");
        assert_eq!(
            run(args("verify", &out, Some(&inputs), Some(&fixtures))),
            Err("Mismatch")
        );
        assert!(!out.join("result.json").exists());
        assert!(!out.join("android-return.json").exists());
    }
    #[test]
    fn malformed_and_oversized_inputs_have_fixed_errors_and_no_output_archive() {
        let root = temp();
        let fixtures = root.join("fixtures");
        fs::create_dir(&fixtures).unwrap();
        let inputs = root.join("inputs");
        fs::create_dir(&inputs).unwrap();
        for (index, bytes, category) in [
            (0, b"PRIVATE-CANARY".to_vec(), "Archive"),
            (1, vec![b'x'; LIMIT + 1], "Bounds"),
        ] {
            fs::write(inputs.join("android-final.json"), &bytes).unwrap();
            fs::write(fixtures.join("expected-android-final.json"), &bytes).unwrap();
            let out = root.join(format!("reject-{index}"));
            assert_eq!(
                run(args("check-final", &out, Some(&inputs), Some(&fixtures))),
                Err(category)
            );
            assert!(!out.join("result.json").exists());
            assert!(!out.join("android-final.sqlite3").exists());
        }
    }
    #[cfg(unix)]
    #[test]
    fn linked_input_and_output_directories_are_refused_without_following_them() {
        let root = temp();
        let actual = root.join("actual");
        fs::create_dir(&actual).unwrap();
        fs::write(actual.join("archive.json"), b"PRIVATE-CONTROL").unwrap();
        let link = root.join("linked");
        std::os::unix::fs::symlink(&actual, &link).unwrap();
        assert_eq!(read(&root, "linked"), Err("Input"));
        assert_eq!(
            run(args("generate", &link.join("new"), None, None)),
            Err("Io")
        );
        assert!(!actual.join("new").exists());
    }
    #[cfg(windows)]
    #[test]
    fn earlier_windows_junction_ancestor_cannot_redirect_reads_or_new_outputs() {
        let root = temp();
        let external = root.join("external-control");
        let nested = external.join("nested");
        let deep = nested.join("deep");
        fs::create_dir(&external).unwrap();
        fs::create_dir(&nested).unwrap();
        fs::create_dir(&deep).unwrap();
        fs::write(deep.join("android-final.json"), b"PRIVATE-EXTERNAL-CONTROL").unwrap();
        let junction = root.join("junction");
        let command = PathBuf::from(std::env::var_os("SystemRoot").unwrap())
            .join("System32/WindowsPowerShell/v1.0/powershell.exe");
        let created = std::process::Command::new(command)
            .args(["-NoProfile", "-NonInteractive", "-Command", "New-Item -ItemType Junction -Path $env:LOCALLORE_TEST_JUNCTION -Target $env:LOCALLORE_TEST_TARGET -ErrorAction Stop | Out-Null"])
            .env("LOCALLORE_TEST_JUNCTION", &junction)
            .env("LOCALLORE_TEST_TARGET", &external)
            .output()
            .unwrap();
        assert!(created.status.success(), "test junction creation failed");
        assert!(linked(&fs::symlink_metadata(&junction).unwrap()));
        let indirect = junction.join("nested").join("deep");
        assert!(!linked(&fs::symlink_metadata(&indirect).unwrap()));
        assert_eq!(directory(&indirect), Err("Io"));
        assert_eq!(read(&indirect, "android-final.json"), Err("Input"));
        assert_eq!(write(&indirect, "new.json", b"replacement"), Err("Io"));
        assert_eq!(
            run(args("generate", &indirect.join("new-output"), None, None)),
            Err("Io")
        );
        let safe_output = root.join("safe-output");
        assert_eq!(
            run(args(
                "check-final",
                &safe_output,
                Some(&indirect),
                Some(&external)
            )),
            Err("Io")
        );
        assert!(!safe_output.exists());
        assert_eq!(fs::read_dir(&deep).unwrap().count(), 1);
        assert_eq!(
            fs::read(deep.join("android-final.json")).unwrap(),
            b"PRIVATE-EXTERNAL-CONTROL"
        );
    }
}
