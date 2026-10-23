// Copyright 2026 LocalLore contributors. SPDX-License-Identifier: Apache-2.0
//! Actual child-process interruption, not a power-loss, physical-disk or ENOSPC experiment.
use locallore::{contracts::*, engine::Engine};
use locallore_storage::{validate_archive, ArchiveError, ForkRequest, Store};
use rusqlite::{Connection, ErrorCode, OpenFlags};
use std::{
    cell::Cell,
    fs::{self, File, OpenOptions},
    io::{Read, Write},
    path::{Path, PathBuf},
    process::{Child, Command as ProcessCommand, Stdio},
    sync::{
        atomic::{AtomicBool, AtomicU64, Ordering},
        mpsc, Arc, Mutex,
    },
    thread::{self, JoinHandle},
    time::{Duration, Instant, SystemTime, UNIX_EPOCH},
};

const IMPORTED: &str = "archive-interrupted-story";
const RETAINED: &str = "archive-retained-control";
const CANARY: &str = "ARCHIVE_INTERRUPTION_SIBLING_CANARY";
const ARCHIVE_LIMIT: usize = 128 * 1024;
const LOG_LIMIT: usize = 4096;
// Frozen fixture/import shape: start + story + 3 branches + 18 entities +
// (3 branch starts + 4 receipts + 4 events) + 3 strict replays + final check.
// The postcommit worker asserts this count too, so checkpoint drift fails the cohort.
const FINAL_POLL: u32 = 38;
const OWNER: &str = "locallore-archive-interruption-v1";
static NEXT: AtomicU64 = AtomicU64::new(0);
static OWNERSHIP_CLEAN: AtomicBool = AtomicBool::new(true);
type Result<T> = std::result::Result<T, &'static str>;

fn ensure(value: bool) -> Result<()> {
    value.then_some(()).ok_or("Mismatch")
}
fn write_new(path: &Path, bytes: &[u8]) -> Result<()> {
    let mut output = OpenOptions::new()
        .create_new(true)
        .write(true)
        .open(path)
        .map_err(|_| "Io")?;
    output.write_all(bytes).map_err(|_| "Io")?;
    output.sync_all().map_err(|_| "Io")
}
fn regular(path: &Path) -> Result<()> {
    let metadata = fs::symlink_metadata(path).map_err(|_| "Io")?;
    ensure(metadata.is_file() && !metadata.file_type().is_symlink()).map_err(|_| "Io")
}
fn read_bounded(path: &Path, limit: usize) -> Result<Vec<u8>> {
    regular(path)?;
    let mut bytes = Vec::new();
    File::open(path)
        .map_err(|_| "Io")?
        .take((limit + 1) as u64)
        .read_to_end(&mut bytes)
        .map_err(|_| "Io")?;
    ensure(bytes.len() <= limit).map_err(|_| "Bounds")?;
    Ok(bytes)
}
fn seed(story: &str) -> Seed {
    let mut seed: Seed =
        serde_json::from_str(include_str!("../../../fixtures/lantern_quay.json")).unwrap();
    seed.scope.story = story.into();
    seed
}
fn apply(store: &mut Store, scope: &Scope, id: &str, commands: Vec<Command>) -> Receipt {
    let engine = store.resume(scope).unwrap().engine;
    let request = engine.request(id, Intent::Actions(commands));
    let proposal = Engine::proposal(&request).unwrap();
    let preview = engine.preview(&request, &proposal).unwrap();
    store.begin_turn(&request).unwrap();
    store
        .commit_turn(&request, &proposal, preview.narration())
        .unwrap()
}
fn fork(store: &mut Store, scope: &Scope, child: &str) -> Scope {
    let revision = store.resume(scope).unwrap().engine.revision();
    store
        .fork_branch(
            &ForkRequest {
                parent: scope.clone(),
                child_branch: child.into(),
                expected_parent_revision: revision,
                at_revision: 1,
            },
            &|| false,
        )
        .unwrap()
        .scope
}
fn archive(store: &mut Store, story: &str) -> Vec<u8> {
    store
        .export_archive(story, &|| false)
        .unwrap()
        .bytes()
        .to_vec()
}
struct Fixture {
    root: PathBuf,
    token: String,
    bytes: Vec<u8>,
    engines: Vec<Engine>,
    retained: Engine,
    retained_archive: Vec<u8>,
    counts: Vec<i64>,
}
impl Fixture {
    fn new() -> Self {
        assert!(
            OWNERSHIP_CLEAN.load(Ordering::SeqCst),
            "Earlier child ownership uncertain"
        );
        let nonce = SystemTime::now()
            .duration_since(UNIX_EPOCH)
            .unwrap()
            .as_nanos()
            ^ u128::from(NEXT.fetch_add(1, Ordering::SeqCst));
        let token = format!("{nonce:032x}");
        let parent = std::env::temp_dir().canonicalize().unwrap();
        let root = parent.join(format!("locallore-archive-interruption-{token}"));
        fs::create_dir(&root).unwrap();
        let root = root.canonicalize().unwrap();
        write_new(
            &root.join("owner-v1"),
            format!("{OWNER}:{token}").as_bytes(),
        )
        .unwrap();
        let mut source = Store::open(&root.join("source.sqlite3"), None).unwrap();
        let main = seed(IMPORTED).scope;
        source
            .create_story("Synthetic interrupted archive", seed(IMPORTED))
            .unwrap();
        apply(
            &mut source,
            &main,
            "shared-prefix",
            vec![Command::Wait { ticks: 1 }],
        );
        let child = fork(&mut source, &main, "child");
        apply(
            &mut source,
            &main,
            "same-turn-key",
            vec![Command::Give {
                item: "potion".into(),
                to: "mira".into(),
                quantity: 1,
            }],
        );
        apply(
            &mut source,
            &child,
            "same-turn-key",
            vec![Command::Consume {
                item: "potion".into(),
            }],
        );
        let sibling = fork(&mut source, &main, "sibling");
        apply(
            &mut source,
            &sibling,
            "sibling-private",
            vec![Command::Say {
                text: CANARY.into(),
                audience: ["mira".into()].into(),
            }],
        );
        let engines = [main, child, sibling]
            .iter()
            .map(|scope| source.resume(scope).unwrap().engine)
            .collect();
        let bytes = archive(&mut source, IMPORTED);
        assert!(bytes.len() <= ARCHIVE_LIMIT);
        drop(source);
        write_new(&root.join("source.json"), &bytes).unwrap();
        let mut target = Store::open(&root.join("destination.sqlite3"), None).unwrap();
        let scope = seed(RETAINED).scope;
        target
            .create_story("Retained synthetic control", seed(RETAINED))
            .unwrap();
        apply(
            &mut target,
            &scope,
            "retained-wait",
            vec![Command::Wait { ticks: 2 }],
        );
        let retained = target.resume(&scope).unwrap().engine;
        let retained_archive = archive(&mut target, RETAINED);
        drop(target);
        let counts = counts(&root.join("destination.sqlite3"));
        Self {
            root,
            token,
            bytes,
            engines,
            retained,
            retained_archive,
            counts,
        }
    }
    fn unchanged(&self, absent: bool) {
        let mut store = Store::open_read_only(&self.root.join("destination.sqlite3")).unwrap();
        let retained = store.resume(self.retained.scope()).unwrap().engine;
        equal_engine(&retained, &self.retained);
        assert!(
            archive(&mut store, RETAINED) == self.retained_archive,
            "Retained archive changed"
        );
        let stories = store.stories().unwrap();
        assert_eq!(stories.len(), if absent { 1 } else { 2 });
        assert_eq!(
            stories.iter().any(|story| story.scope.story == IMPORTED),
            !absent
        );
        if absent {
            assert!(store.resume(self.engines[0].scope()).is_err());
            drop(store);
            assert_eq!(counts(&self.root.join("destination.sqlite3")), self.counts);
        }
    }
    fn complete(&self) {
        self.unchanged(false);
        let mut store = Store::open(&self.root.join("destination.sqlite3"), None).unwrap();
        assert!(
            archive(&mut store, IMPORTED) == self.bytes,
            "Imported archive changed"
        );
        for expected in &self.engines {
            let restored = store.resume(expected.scope()).unwrap().engine;
            equal_engine(&restored, expected);
            assert_eq!(restored.revision(), 2);
            for receipt in restored
                .receipts()
                .iter()
                .filter(|receipt| receipt.request().scope == *restored.scope())
            {
                assert!(
                    store
                        .begin_turn(receipt.request())
                        .unwrap()
                        .receipt
                        .as_ref()
                        == Some(receipt),
                    "Original receipt retry changed"
                );
                assert!(
                    store
                        .commit_turn(receipt.request(), receipt.proposal(), receipt.narration())
                        .unwrap()
                        == *receipt,
                    "Committed receipt retry changed"
                );
            }
        }
        assert_eq!(
            store.import_archive(validate_archive(&self.bytes, &|| false).unwrap(), &|| false),
            Err(ArchiveError::Conflict)
        );
        assert!(
            archive(&mut store, IMPORTED) == self.bytes,
            "Conflict changed imported archive"
        );
        drop(store);
        self.unchanged(false);
    }
}
// Fresh owned synthetic directories, including failures/logs/journals, are intentionally
// retained. There is no recursive or other filesystem deletion in this process test.
fn equal_engine(actual: &Engine, expected: &Engine) {
    assert!(actual.scope() == expected.scope(), "Scope changed");
    assert!(
        actual.canonical_bytes() == expected.canonical_bytes(),
        "Canonical projection changed"
    );
    assert!(
        actual.receipts() == expected.receipts(),
        "Accepted receipts changed"
    );
    for observer in ["player", "mira", "sable", "oren"] {
        let context = actual
            .character_context(observer, actual.scope(), actual.revision())
            .unwrap();
        assert!(
            context
                == expected
                    .character_context(observer, expected.scope(), expected.revision())
                    .unwrap(),
            "Observer context changed"
        );
        let visible = serde_json::to_string(&context).unwrap();
        assert_eq!(visible.contains("SECRET-TIDE-731"), observer == "player");
        assert_eq!(
            visible.contains(CANARY),
            actual.scope().story == IMPORTED
                && actual.scope().branch == "sibling"
                && matches!(observer, "player" | "mira")
        );
    }
}
fn counts(path: &Path) -> Vec<i64> {
    let connection = Connection::open_with_flags(path, OpenFlags::SQLITE_OPEN_READ_ONLY).unwrap();
    [
        "stories",
        "branches",
        "turns",
        "entities",
        "branch_entities",
        "accepted_events",
        "event_witnesses",
        "branch_projections",
        "derived_memory",
    ]
    .into_iter()
    .map(|table| {
        connection
            .query_row(&format!("SELECT count(*) FROM {table}"), [], |row| {
                row.get(0)
            })
            .unwrap()
    })
    .collect()
}

#[derive(Default)]
struct Captured {
    bytes: Vec<u8>,
    overflow: bool,
    io_failed: bool,
}
struct Capture {
    state: Arc<Mutex<Captured>>,
    done: mpsc::Receiver<()>,
    reader: Option<JoinHandle<()>>,
}
impl Capture {
    fn start(mut pipe: impl Read + Send + 'static) -> Result<Self> {
        let state = Arc::new(Mutex::new(Captured::default()));
        let shared = state.clone();
        let (done_tx, done) = mpsc::channel();
        let reader = thread::Builder::new()
            .spawn(move || {
                let mut buffer = [0u8; 1024];
                loop {
                    match pipe.read(&mut buffer) {
                        Ok(0) => break,
                        Ok(count) => {
                            let mut state = shared.lock().unwrap();
                            let retained = count.min(LOG_LIMIT - state.bytes.len());
                            state.bytes.extend_from_slice(&buffer[..retained]);
                            state.overflow |= retained != count;
                        }
                        Err(_) => {
                            shared.lock().unwrap().io_failed = true;
                            break;
                        }
                    }
                }
                let _ = done_tx.send(());
            })
            .map_err(|_| "ReaderSpawn")?;
        Ok(Self {
            state,
            done,
            reader: Some(reader),
        })
    }
    fn finish(&mut self, path: &Path) -> bool {
        let terminated = self.reader.is_none()
            || (self.done.recv_timeout(Duration::from_secs(2)).is_ok()
                && self.reader.take().unwrap().join().is_ok());
        let state = self.state.lock().unwrap();
        let retained = write_new(path, &state.bytes).is_ok();
        terminated && retained && !state.overflow && !state.io_failed
    }
    fn healthy(&self) -> bool {
        let state = self.state.lock().unwrap();
        !state.overflow && !state.io_failed
    }
}
struct OwnedChild {
    child: Child,
    output: Option<Capture>,
    errors: Option<Capture>,
    root: PathBuf,
    closed: bool,
}
impl OwnedChild {
    fn start(fixture: &Fixture, phase: &str) -> Self {
        let child = ProcessCommand::new(std::env::current_exe().unwrap())
            .args([
                "--exact",
                "archive_import_worker",
                "--ignored",
                "--nocapture",
                "--test-threads=1",
            ])
            .env("LOCALLORE_ARCHIVE_WORKER_ROOT", &fixture.root)
            .env("LOCALLORE_ARCHIVE_WORKER_TOKEN", &fixture.token)
            .env("LOCALLORE_ARCHIVE_WORKER_PHASE", phase)
            .stdin(Stdio::null())
            .stdout(Stdio::piped())
            .stderr(Stdio::piped())
            .spawn()
            .unwrap();
        // Own the Child before allocating any drainer thread; setup failure must also
        // terminate/reap this exact process instead of relying on Child's non-killing Drop.
        let mut owner = Self {
            child,
            output: None,
            errors: None,
            root: fixture.root.clone(),
            closed: false,
        };
        owner.output = Some(
            Capture::start(owner.child.stdout.take().unwrap()).expect("Output reader setup failed"),
        );
        owner.errors = Some(
            Capture::start(owner.child.stderr.take().unwrap()).expect("Error reader setup failed"),
        );
        owner
    }
    fn ready(&mut self, phase: &str) -> Result<()> {
        let deadline = Instant::now() + Duration::from_secs(15);
        let expected = format!("{OWNER}:{phase}:ready");
        while Instant::now() < deadline {
            if self.child.try_wait().map_err(|_| "Child")?.is_some() {
                return Err("EarlyExit");
            }
            if !self.output.as_ref().is_some_and(Capture::healthy)
                || !self.errors.as_ref().is_some_and(Capture::healthy)
            {
                return Err("ChildOutput");
            }
            let marker = self.root.join("ready-v1");
            // File creation precedes its bounded write/fsync; never accept an incomplete marker.
            if marker.exists() && read_bounded(&marker, 128)? == expected.as_bytes() {
                return Ok(());
            }
            thread::sleep(Duration::from_millis(10));
        }
        Err("ReadyTimeout")
    }
    fn stop(&mut self) -> bool {
        if self.closed {
            return true;
        }
        let mut reaped = matches!(self.child.try_wait(), Ok(Some(_)));
        let mut killed = false;
        if !reaped {
            killed = self.child.kill().is_ok();
        }
        let deadline = Instant::now() + Duration::from_secs(5);
        while !reaped && Instant::now() < deadline {
            match self.child.try_wait() {
                Ok(Some(_)) => reaped = true,
                Ok(None) => thread::sleep(Duration::from_millis(10)),
                Err(_) => break,
            }
        }
        let output_path = self.root.join("child-stdout.bin");
        let errors_path = self.root.join("child-stderr.bin");
        let output = self.output.as_mut().map_or_else(
            || write_new(&output_path, &[]).is_ok(),
            |capture| capture.finish(&output_path),
        );
        let errors = self.errors.as_mut().map_or_else(
            || write_new(&errors_path, &[]).is_ok(),
            |capture| capture.finish(&errors_path),
        );
        let clean = reaped && output && errors;
        self.closed = clean;
        if !clean {
            OWNERSHIP_CLEAN.store(false, Ordering::SeqCst);
        }
        // Qualification requires an actually live child terminated through its owned handle.
        clean && killed
    }
}
impl Drop for OwnedChild {
    fn drop(&mut self) {
        if !self.closed && !self.stop() && !thread::panicking() {
            panic!("Owned archive child cleanup failed");
        }
    }
}
fn writer_state(path: &Path, busy: bool) -> Result<()> {
    let connection = Connection::open_with_flags(path, OpenFlags::SQLITE_OPEN_READ_WRITE)
        .map_err(|_| "Reader")?;
    connection
        .busy_timeout(Duration::ZERO)
        .map_err(|_| "Reader")?;
    match connection.execute_batch("BEGIN IMMEDIATE") {
        Err(error)
            if busy
                && matches!(
                    error.sqlite_error_code(),
                    Some(ErrorCode::DatabaseBusy | ErrorCode::DatabaseLocked)
                ) =>
        {
            Ok(())
        }
        Ok(()) => {
            connection.execute_batch("ROLLBACK").map_err(|_| "Reader")?;
            ensure(!busy)
        }
        _ => Err("WriterLock"),
    }
}
fn run_interruption(phase: &str, committed: bool) {
    let fixture = Fixture::new();
    let mut child = OwnedChild::start(&fixture, phase);
    let observed = (|| {
        child.ready(phase)?;
        writer_state(&fixture.root.join("destination.sqlite3"), !committed)?;
        // Another real connection sees old or complete history while the worker is alive.
        fixture.unchanged(!committed);
        ensure(child.child.try_wait().map_err(|_| "Child")?.is_none())
    })();
    let cleanup = child.stop();
    assert_eq!(
        (observed, cleanup),
        (Ok(()), true),
        "Archive interruption/cleanup failed"
    );
    // A normal Store reopen performs any real SQLite hot-journal recovery after termination.
    drop(Store::open(&fixture.root.join("destination.sqlite3"), None).unwrap());
    if committed {
        fixture.complete();
    } else {
        fixture.unchanged(true);
        let mut store = Store::open(&fixture.root.join("destination.sqlite3"), None).unwrap();
        store
            .import_archive(
                validate_archive(&fixture.bytes, &|| false).unwrap(),
                &|| false,
            )
            .unwrap();
        drop(store);
        fixture.complete();
    }
}

#[test]
fn killed_after_story_insert_rolls_back_and_fresh_import_preserves_all_scopes() {
    run_interruption("story", false);
}
#[test]
fn killed_after_branch_replay_before_commit_leaves_no_canonical_or_projection_rows() {
    run_interruption("precommit", false);
}
#[test]
fn killed_after_commit_before_ack_preserves_complete_archive_exactly_once() {
    run_interruption("committed", true);
}

fn hold(root: &Path, phase: &str) -> Result<()> {
    write_new(
        &root.join("ready-v1"),
        format!("{OWNER}:{phase}:ready").as_bytes(),
    )?;
    // Independent self-lease: even if the parent disappears, no transaction is held forever.
    let deadline = Instant::now() + Duration::from_secs(30);
    while Instant::now() < deadline {
        thread::sleep(Duration::from_millis(20));
    }
    Err("LeaseExpired")
}
fn worker() -> Result<()> {
    let root = PathBuf::from(std::env::var_os("LOCALLORE_ARCHIVE_WORKER_ROOT").ok_or("Arguments")?);
    let token = std::env::var("LOCALLORE_ARCHIVE_WORKER_TOKEN").map_err(|_| "Arguments")?;
    ensure(
        token.len() == 32
            && token
                .bytes()
                .all(|byte| byte.is_ascii_digit() || (b'a'..=b'f').contains(&byte)),
    )?;
    let phase = std::env::var("LOCALLORE_ARCHIVE_WORKER_PHASE").map_err(|_| "Arguments")?;
    let stop_at = match phase.as_str() {
        "story" => 2,
        "precommit" => FINAL_POLL,
        "committed" => 0,
        _ => return Err("Arguments"),
    };
    let expected = std::env::temp_dir()
        .canonicalize()
        .map_err(|_| "Io")?
        .join(format!("locallore-archive-interruption-{token}"));
    ensure(
        root.is_absolute() && root == expected && root.canonicalize().map_err(|_| "Io")? == root,
    )?;
    ensure(read_bounded(&root.join("owner-v1"), 128)? == format!("{OWNER}:{token}").as_bytes())?;
    regular(&root.join("destination.sqlite3"))?;
    let bytes = read_bounded(&root.join("source.json"), ARCHIVE_LIMIT)?;
    let validated = validate_archive(&bytes, &|| false).map_err(|_| "Archive")?;
    ensure(
        validated.preview().story_id == IMPORTED
            && validated.preview().committed_turns == 4
            && validated.preview().branch_heads.len() == 3,
    )?;
    let mut store = Store::open(&root.join("destination.sqlite3"), None).map_err(|_| "Store")?;
    let polls = Cell::new(0u32);
    let barrier_failed = Cell::new(false);
    let imported = store
        .import_archive(validated, &|| {
            let poll = polls.get() + 1;
            polls.set(poll);
            if poll == stop_at && hold(&root, &phase).is_err() {
                barrier_failed.set(true);
                return true;
            }
            false
        })
        .map_err(|_| "Import")?;
    ensure(!barrier_failed.get() && polls.get() == FINAL_POLL)?;
    ensure(
        imported.root.story == IMPORTED && imported.branches == 3 && imported.committed_turns == 4,
    )?;
    ensure(phase == "committed")?;
    hold(&root, &phase)
}
#[test]
#[ignore = "IPC worker only; qualification is the three parent-owned process interruption tests"]
fn archive_import_worker() {
    std::panic::set_hook(Box::new(|_| eprintln!("Archive worker failed")));
    if let Err(category) = worker() {
        eprintln!("Archive worker: {category}");
        std::process::exit(70);
    }
}
