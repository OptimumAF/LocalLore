// Copyright 2026 LocalLore contributors. SPDX-License-Identifier: Apache-2.0
//! Atomic root-branch turns. No inference, file selector or SQL escapes this owner.
use crate::{StorageError, Store};
use locallore::{
    contracts::{
        Error, Proposal, Receipt, Request, Scope, Seed, MAX_HISTORY_BYTES, MAX_HISTORY_RECEIPTS,
        MAX_RECEIPT_BYTES,
    },
    engine::Engine,
};
use rusqlite::{Connection, OptionalExtension, TransactionBehavior};

#[derive(Debug, Clone, PartialEq, Eq)]
pub enum TurnError {
    Storage(StorageError),
    Engine(Error),
    Integrity,
    TooLarge,
    UnknownTurn,
    RetryMismatch,
    Stale,
    Terminal,
    Full,
}
impl std::fmt::Display for TurnError {
    fn fmt(&self, f: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(f, "{self:?}")
    }
}
impl std::error::Error for TurnError {}
impl From<StorageError> for TurnError {
    fn from(e: StorageError) -> Self {
        Self::Storage(e)
    }
}
impl From<rusqlite::Error> for TurnError {
    fn from(e: rusqlite::Error) -> Self {
        if e.sqlite_error_code() == Some(rusqlite::ErrorCode::DiskFull) {
            Self::Full
        } else {
            Self::Storage(e.into())
        }
    }
}
type Result<T> = std::result::Result<T, TurnError>;

#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum TurnPhase {
    Draft,
    Cancelled,
    Failed,
    Stale,
    Committed,
}
#[derive(Debug, Clone)]
pub struct TurnRecord {
    pub request: Request,
    pub phase: TurnPhase,
    pub receipt: Option<Receipt>,
}
#[derive(Debug)]
pub struct ResumedStory {
    pub engine: Engine,
    /// A mismatched/missing derived cache was ignored. Canonical history passed validation.
    pub projection_needs_rebuild: bool,
}
fn sql_revision(value: u64) -> Result<i64> {
    i64::try_from(value).map_err(|_| TurnError::TooLarge)
}

fn read_engine(connection: &Connection, scope: &Scope) -> Result<ResumedStory> {
    let seed_json: String = connection
        .query_row(
            "SELECT seed_json FROM stories WHERE story_id=?1 AND root_branch=?2",
            (&scope.story, &scope.branch),
            |r| r.get(0),
        )
        .optional()?
        .ok_or(StorageError::NotFound)?;
    let seed: Seed = serde_json::from_str(&seed_json).map_err(|_| TurnError::Integrity)?;
    if &seed.scope != scope {
        return Err(TurnError::Integrity);
    }
    let head: i64 = connection.query_row(
        "SELECT head_revision FROM branches WHERE story_id=?1 AND branch_id=?2 AND parent_branch IS NULL",
        (&scope.story, &scope.branch), |r| r.get(0))?;
    let (count, bytes): (i64, i64) = connection.query_row(
        "SELECT count(*),coalesce(sum(length(CAST(request_json AS BLOB))+coalesce(length(CAST(response_json AS BLOB)),0)),0) FROM turns WHERE story_id=?1 AND branch_id=?2",
        (&scope.story, &scope.branch), |r| Ok((r.get(0)?,r.get(1)?)))?;
    if count < 0
        || bytes < 0
        || count > MAX_HISTORY_RECEIPTS as i64
        || bytes > MAX_HISTORY_BYTES as i64
    {
        return Err(TurnError::TooLarge);
    }
    let mut query = connection.prepare(
        "SELECT turn_id,expected_revision,request_json,response_json FROM turns WHERE story_id=?1 AND branch_id=?2 AND status='committed' ORDER BY expected_revision,turn_id")?;
    let mut rows = query.query((&scope.story, &scope.branch))?;
    let mut history = Vec::with_capacity(count as usize);
    let mut requests = Vec::with_capacity(count as usize);
    while let Some(row) = rows.next()? {
        let turn: String = row.get(0)?;
        let revision: i64 = row.get(1)?;
        let request: Request =
            serde_json::from_str(&row.get::<_, String>(2)?).map_err(|_| TurnError::Integrity)?;
        let response: String = row.get(3)?;
        if response.len() > MAX_RECEIPT_BYTES
            || request.scope != *scope
            || request.turn != turn
            || sql_revision(request.expected_revision)? != revision
        {
            return Err(TurnError::Integrity);
        }
        history.push(response);
        requests.push(request);
    }
    let engine = Engine::restore(seed, &history).map_err(|_| TurnError::Integrity)?;
    if sql_revision(engine.revision())? != head
        || engine.receipts().len() != requests.len()
        || engine
            .receipts()
            .iter()
            .zip(&requests)
            .any(|(r, q)| r.request() != q)
    {
        return Err(TurnError::Integrity);
    }
    // The normalized ledger must exactly agree with the validated complete receipts.
    let mut events = connection.prepare("SELECT sequence,turn_id,event_version,envelope_json FROM accepted_events WHERE story_id=?1 AND branch_id=?2 ORDER BY sequence")?;
    let mut event_rows = events.query((&scope.story, &scope.branch))?;
    for receipt in engine.receipts() {
        for event in receipt.events() {
            let row = event_rows.next()?.ok_or(TurnError::Integrity)?;
            // This owner writes canonical bytes. Exact comparison also rejects duplicate keys
            // that a generic JSON Value parser would silently collapse.
            let stored: String = row.get(3)?;
            if row.get::<_, i64>(0)? != sql_revision(event.sequence())?
                || row.get::<_, String>(1)? != receipt.request().turn
                || row.get::<_, u16>(2)? != 1
                || stored != serde_json::to_string(event).map_err(|_| TurnError::Integrity)?
            {
                return Err(TurnError::Integrity);
            }
            let mut witnesses = connection.prepare("SELECT observer_id FROM event_witnesses WHERE story_id=?1 AND branch_id=?2 AND sequence=?3 ORDER BY observer_id")?;
            let mut observer_rows =
                witnesses.query((&scope.story, &scope.branch, sql_revision(event.sequence())?))?;
            for observer in event.witnesses() {
                if observer_rows
                    .next()?
                    .ok_or(TurnError::Integrity)?
                    .get::<_, String>(0)?
                    != *observer
                {
                    return Err(TurnError::Integrity);
                }
            }
            if observer_rows.next()?.is_some() {
                return Err(TurnError::Integrity);
            }
        }
    }
    if event_rows.next()?.is_some() {
        return Err(TurnError::Integrity);
    }
    // Also detect scoped orphan rows introduced outside this owner after open-time FK checks.
    // Per-event checks above alone would never visit a witness for a nonexistent sequence.
    let witness_count: i64 = connection.query_row(
        "SELECT count(*) FROM event_witnesses WHERE story_id=?1 AND branch_id=?2",
        (&scope.story, &scope.branch),
        |r| r.get(0),
    )?;
    let expected_witnesses: usize = engine
        .receipts()
        .iter()
        .flat_map(|r| r.events())
        .map(|e| e.witnesses().len())
        .sum();
    if witness_count != expected_witnesses as i64 {
        return Err(TurnError::Integrity);
    }
    let cache: Option<(i64,u16,String)> = connection.query_row(
        "SELECT revision,projection_version,projection_json FROM branch_projections WHERE story_id=?1 AND branch_id=?2",
        (&scope.story,&scope.branch), |r|Ok((r.get(0)?,r.get(1)?,r.get(2)?))).optional()?;
    let canonical = engine.canonical_bytes();
    let valid_cache = cache.is_some_and(|(revision, version, json)| {
        revision == head && version == 1 && json.as_bytes() == canonical
    });
    Ok(ResumedStory {
        engine,
        projection_needs_rebuild: !valid_cache,
    })
}

fn recorded(
    connection: &Connection,
    request: &Request,
    engine: &Engine,
) -> Result<Option<TurnRecord>> {
    let row: Option<(i64,String,String)> = connection.query_row(
        "SELECT expected_revision,status,request_json FROM turns WHERE story_id=?1 AND branch_id=?2 AND turn_id=?3",
        (&request.scope.story,&request.scope.branch,&request.turn), |r|Ok((r.get(0)?,r.get(1)?,r.get(2)?))).optional()?;
    let Some((revision, status, input)) = row else {
        return Ok(None);
    };
    let original: Request = serde_json::from_str(&input).map_err(|_| TurnError::Integrity)?;
    if original.scope != request.scope
        || original.turn != request.turn
        || sql_revision(original.expected_revision)? != revision
    {
        return Err(TurnError::Integrity);
    }
    if original != *request {
        return Err(TurnError::RetryMismatch);
    }
    let phase = match status.as_str() {
        "draft" => TurnPhase::Draft,
        "cancelled" => TurnPhase::Cancelled,
        "failed" => TurnPhase::Failed,
        "stale" => TurnPhase::Stale,
        "committed" => TurnPhase::Committed,
        _ => return Err(TurnError::Integrity),
    };
    let receipt = engine.recorded(request).map_err(|_| TurnError::Integrity)?;
    if (phase == TurnPhase::Committed) != receipt.is_some() {
        return Err(TurnError::Integrity);
    }
    Ok(Some(TurnRecord {
        request: original,
        phase,
        receipt,
    }))
}
fn write_projection(connection: &Connection, engine: &Engine) -> Result<()> {
    let bytes = engine.canonical_bytes();
    if bytes.len() > 262144 {
        return Err(TurnError::TooLarge);
    }
    connection.execute("INSERT INTO branch_projections VALUES (?1,?2,?3,1,?4) ON CONFLICT(story_id,branch_id) DO UPDATE SET revision=excluded.revision,projection_version=1,projection_json=excluded.projection_json",
        (&engine.scope().story,&engine.scope().branch,sql_revision(engine.revision())?,String::from_utf8(bytes).map_err(|_|TurnError::Integrity)?))?;
    Ok(())
}

impl Store {
    /// A coherent read transaction; ignores the derived projection and returns validated replay.
    pub fn resume(&mut self, scope: &Scope) -> Result<ResumedStory> {
        let tx = self.connection.transaction()?;
        let result = read_engine(&tx, scope)?;
        tx.commit()?;
        Ok(result)
    }
    /// Repair only the replaceable cache, after full scoped history validation under the writer lock.
    pub fn rebuild_projection(&mut self, scope: &Scope) -> Result<ResumedStory> {
        let tx = self
            .connection
            .transaction_with_behavior(TransactionBehavior::Immediate)?;
        let result = read_engine(&tx, scope)?;
        write_projection(&tx, &result.engine)?;
        tx.commit()?;
        Ok(ResumedStory {
            engine: result.engine,
            projection_needs_rebuild: false,
        })
    }
    /// Persist intent, then release the transaction BEFORE calling any inference/provider.
    /// An exact retry returns the recorded phase/receipt even after the head advances.
    pub fn begin_turn(&mut self, request: &Request) -> Result<TurnRecord> {
        let tx = self
            .connection
            .transaction_with_behavior(TransactionBehavior::Immediate)?;
        let resumed = read_engine(&tx, &request.scope)?;
        if let Some(existing) = recorded(&tx, request, &resumed.engine)? {
            return Ok(existing);
        }
        resumed
            .engine
            .preflight(request)
            .map_err(TurnError::Engine)?;
        let count: i64 = tx.query_row(
            "SELECT count(*) FROM turns WHERE story_id=?1 AND branch_id=?2",
            (&request.scope.story, &request.scope.branch),
            |r| r.get(0),
        )?;
        if count >= MAX_HISTORY_RECEIPTS as i64 {
            return Err(TurnError::TooLarge);
        }
        let input = serde_json::to_string(request).map_err(|_| TurnError::Integrity)?;
        let bytes:i64 = tx.query_row("SELECT coalesce(sum(length(CAST(request_json AS BLOB))+coalesce(length(CAST(response_json AS BLOB)),0)),0) FROM turns WHERE story_id=?1 AND branch_id=?2",(&request.scope.story,&request.scope.branch),|r|r.get(0))?;
        if bytes.saturating_add(input.len() as i64) > MAX_HISTORY_BYTES as i64 {
            return Err(TurnError::TooLarge);
        }
        tx.execute(
            "INSERT INTO turns VALUES (?1,?2,?3,?4,'draft',?5,NULL)",
            (
                &request.scope.story,
                &request.scope.branch,
                &request.turn,
                sql_revision(request.expected_revision)?,
                input,
            ),
        )?;
        tx.commit()?;
        Ok(TurnRecord {
            request: request.clone(),
            phase: TurnPhase::Draft,
            receipt: None,
        })
    }
    pub fn turn_status(&mut self, request: &Request) -> Result<TurnRecord> {
        let tx = self.connection.transaction()?;
        let resumed = read_engine(&tx, &request.scope)?;
        let result = recorded(&tx, request, &resumed.engine)?.ok_or(TurnError::UnknownTurn)?;
        tx.commit()?;
        Ok(result)
    }
    /// Interrupted intents remain drafts, never automatic canonical actions on restart.
    pub fn drafts(&mut self, scope: &Scope) -> Result<Vec<TurnRecord>> {
        let tx = self.connection.transaction()?;
        let resumed = read_engine(&tx, scope)?;
        let mut result = Vec::new();
        {
            let mut query = tx.prepare("SELECT turn_id,expected_revision,request_json FROM turns WHERE story_id=?1 AND branch_id=?2 AND status='draft' ORDER BY turn_id")?;
            let mut rows = query.query((&scope.story, &scope.branch))?;
            while let Some(row) = rows.next()? {
                let request: Request = serde_json::from_str(&row.get::<_, String>(2)?)
                    .map_err(|_| TurnError::Integrity)?;
                if request.scope != *scope
                    || request.turn != row.get::<_, String>(0)?
                    || sql_revision(request.expected_revision)? != row.get::<_, i64>(1)?
                {
                    return Err(TurnError::Integrity);
                }
                result.push(recorded(&tx, &request, &resumed.engine)?.ok_or(TurnError::Integrity)?);
            }
        }
        tx.commit()?;
        Ok(result)
    }
    pub fn cancel_turn(&mut self, request: &Request) -> Result<TurnRecord> {
        self.finish_draft(request, "cancelled", TurnPhase::Cancelled)
    }
    pub fn fail_turn(&mut self, request: &Request) -> Result<TurnRecord> {
        self.finish_draft(request, "failed", TurnPhase::Failed)
    }
    pub fn stale_turn(&mut self, request: &Request) -> Result<TurnRecord> {
        self.finish_draft(request, "stale", TurnPhase::Stale)
    }
    /// Recover a persisted idempotency key without requiring an untrusted caller to supply its
    /// original request. Scope/key and complete canonical history are still validated together.
    pub fn lookup_turn(&mut self, scope: &Scope, turn: &str) -> Result<TurnRecord> {
        if turn.is_empty() || turn.len() > 64 {
            return Err(TurnError::UnknownTurn);
        }
        let tx = self.connection.transaction()?;
        let resumed = read_engine(&tx, scope)?;
        let input: Option<String> = tx
            .query_row(
                "SELECT request_json FROM turns WHERE story_id=?1 AND branch_id=?2 AND turn_id=?3",
                (&scope.story, &scope.branch, turn),
                |r| r.get(0),
            )
            .optional()?;
        let request: Request = serde_json::from_str(&input.ok_or(TurnError::UnknownTurn)?)
            .map_err(|_| TurnError::Integrity)?;
        if request.scope != *scope || request.turn != turn {
            return Err(TurnError::Integrity);
        }
        let saved = recorded(&tx, &request, &resumed.engine)?.ok_or(TurnError::Integrity)?;
        tx.commit()?;
        Ok(saved)
    }
    fn finish_draft(
        &mut self,
        request: &Request,
        status: &str,
        phase: TurnPhase,
    ) -> Result<TurnRecord> {
        let tx = self
            .connection
            .transaction_with_behavior(TransactionBehavior::Immediate)?;
        let resumed = read_engine(&tx, &request.scope)?;
        let mut result = recorded(&tx, request, &resumed.engine)?.ok_or(TurnError::UnknownTurn)?;
        if result.phase == TurnPhase::Draft {
            tx.execute("UPDATE turns SET status=?4 WHERE story_id=?1 AND branch_id=?2 AND turn_id=?3 AND status='draft'",
                (&request.scope.story,&request.scope.branch,&request.turn,status))?;
            result.phase = phase;
        }
        tx.commit()?;
        Ok(result)
    }
    /// Accepts a typed proposal/narration, never caller-authored accepted events or projection.
    /// Revalidates with the shared engine and atomically writes the entire completed turn.
    pub fn commit_turn(
        &mut self,
        request: &Request,
        proposal: &Proposal,
        narration: &str,
    ) -> Result<Receipt> {
        self.commit_output(request, proposal, narration, None)
    }
    pub fn commit_prepared(&mut self, receipt: &Receipt) -> Result<Receipt> {
        self.commit_output(
            receipt.request(),
            receipt.proposal(),
            receipt.narration(),
            receipt.play(),
        )
    }
    fn commit_output(
        &mut self,
        request: &Request,
        proposal: &Proposal,
        narration: &str,
        play: Option<&locallore::play::PlayRecord>,
    ) -> Result<Receipt> {
        let tx = self
            .connection
            .transaction_with_behavior(TransactionBehavior::Immediate)?;
        let mut resumed = read_engine(&tx, &request.scope)?;
        let turn = recorded(&tx, request, &resumed.engine)?.ok_or(TurnError::UnknownTurn)?;
        if let Some(receipt) = turn.receipt {
            return Ok(receipt);
        }
        if turn.phase != TurnPhase::Draft {
            return Err(TurnError::Terminal);
        }
        // A committed exact request is resolved above before considering a new output.
        // Unknown/provisional output cannot replace or hide a winning recorded result.
        if narration.len() > MAX_RECEIPT_BYTES {
            return Err(TurnError::TooLarge);
        }
        if request.expected_revision != resumed.engine.revision() {
            tx.execute(
                "UPDATE turns SET status='stale' WHERE story_id=?1 AND branch_id=?2 AND turn_id=?3",
                (&request.scope.story, &request.scope.branch, &request.turn),
            )?;
            tx.commit()?;
            return Err(TurnError::Stale);
        }
        let receipt = if let Some(play) = play {
            if play.narration.text != narration {
                return Err(TurnError::Integrity);
            }
            resumed.engine.commit_play(request, proposal, play)
        } else {
            resumed.engine.commit(request, proposal, narration)
        }
        .map_err(TurnError::Engine)?;
        let response = serde_json::to_string(&receipt).map_err(|_| TurnError::Integrity)?;
        let prior_bytes: i64 = tx.query_row("SELECT coalesce(sum(length(CAST(request_json AS BLOB))+coalesce(length(CAST(response_json AS BLOB)),0)),0) FROM turns WHERE story_id=?1 AND branch_id=?2",(&request.scope.story,&request.scope.branch),|r|r.get(0))?;
        if response.len() > MAX_RECEIPT_BYTES
            || prior_bytes.saturating_add(response.len() as i64) > MAX_HISTORY_BYTES as i64
        {
            return Err(TurnError::TooLarge);
        }
        checkpoint(0)?;
        for event in receipt.events() {
            tx.execute(
                "INSERT INTO accepted_events VALUES (?1,?2,?3,?4,1,?5)",
                (
                    &request.scope.story,
                    &request.scope.branch,
                    sql_revision(event.sequence())?,
                    &request.turn,
                    serde_json::to_string(event).map_err(|_| TurnError::Integrity)?,
                ),
            )?;
            checkpoint(1)?;
            for observer in event.witnesses() {
                tx.execute("INSERT INTO event_witnesses(story_id,branch_id,sequence,observer_id) VALUES (?1,?2,?3,?4)",
                    (&request.scope.story,&request.scope.branch,sql_revision(event.sequence())?,observer))?;
            }
        }
        checkpoint(2)?;
        write_projection(&tx, &resumed.engine)?;
        checkpoint(3)?;
        tx.execute("UPDATE turns SET status='committed',response_json=?4 WHERE story_id=?1 AND branch_id=?2 AND turn_id=?3 AND status='draft'",
            (&request.scope.story,&request.scope.branch,&request.turn,response))?;
        checkpoint(4)?;
        if tx.execute("UPDATE branches SET head_revision=?4 WHERE story_id=?1 AND branch_id=?2 AND head_revision=?3",
            (&request.scope.story,&request.scope.branch,sql_revision(request.expected_revision)?,sql_revision(resumed.engine.revision())?))? != 1 { return Err(TurnError::Stale); }
        checkpoint(5)?;
        tx.commit()?;
        checkpoint(6)?;
        Ok(receipt)
    }
}

// Fault hooks are private unit-test code; no environment/control API exists in normal builds.
#[cfg(not(test))]
#[inline(always)]
fn checkpoint(_: u8) -> Result<()> {
    Ok(())
}
#[cfg(test)]
thread_local! { static FAULT: std::cell::Cell<Option<(u8,bool)>> = const {std::cell::Cell::new(None)}; }
#[cfg(test)]
fn checkpoint(stage: u8) -> Result<()> {
    if let Some((at, abrupt)) = FAULT.get() {
        if at == stage {
            if abrupt {
                std::process::exit(77);
            }
            return Err(TurnError::Storage(StorageError::Database));
        }
    }
    Ok(())
}

#[cfg(test)]
mod tests {
    use super::*;
    use locallore::contracts::{Command, Intent};
    use std::path::PathBuf;
    struct Temp(PathBuf);
    impl Temp {
        fn new() -> Self {
            let path = std::env::temp_dir().join(format!(
                "locallore-atomic-{}-{}",
                std::process::id(),
                std::time::SystemTime::now()
                    .duration_since(std::time::UNIX_EPOCH)
                    .unwrap()
                    .as_nanos()
            ));
            std::fs::create_dir(&path).unwrap();
            Self(path)
        }
        fn path(&self) -> PathBuf {
            self.0.join("story.sqlite")
        }
        fn open(&self) -> Store {
            Store::open(&self.path(), None).unwrap()
        }
    }
    impl Drop for Temp {
        fn drop(&mut self) {
            std::fs::remove_dir_all(&self.0).unwrap();
        }
    }
    fn seed() -> Seed {
        serde_json::from_str(include_str!("../../../fixtures/lantern_quay.json")).unwrap()
    }
    fn plan() -> (Request, Proposal, String) {
        let engine = Engine::new(seed()).unwrap();
        let request = engine.request(
            "atomic",
            Intent::Actions(vec![
                Command::Give {
                    item: "potion".into(),
                    to: "mira".into(),
                    quantity: 1,
                },
                Command::Wait { ticks: 1 },
            ]),
        );
        let proposal = Engine::proposal(&request).unwrap();
        let text = engine
            .preview(&request, &proposal)
            .unwrap()
            .narration()
            .to_owned();
        (request, proposal, text)
    }
    #[test]
    fn failures_at_every_commit_boundary_leave_old_or_complete_new_state() {
        for stage in 0..=6 {
            let dir = Temp::new();
            let mut store = dir.open();
            store.create_story("Fixture", seed()).unwrap();
            let (r, p, n) = plan();
            store.begin_turn(&r).unwrap();
            FAULT.set(Some((stage, false)));
            let result = store.commit_turn(&r, &p, &n);
            FAULT.set(None);
            assert!(result.is_err());
            drop(store);
            let mut store = dir.open();
            let resumed = store.resume(&r.scope).unwrap();
            assert_eq!(resumed.engine.revision(), if stage == 6 { 2 } else { 0 });
            assert_eq!(
                resumed.engine.state().items["potion"].owner,
                if stage == 6 { "mira" } else { "player" }
            );
            assert_eq!(
                resumed.engine.state().story_time,
                if stage == 6 { 101 } else { 100 }
            );
            assert_eq!(
                store.turn_status(&r).unwrap().phase,
                if stage == 6 {
                    TurnPhase::Committed
                } else {
                    TurnPhase::Draft
                }
            );
            assert!(!resumed.projection_needs_rebuild);
            assert_eq!(store.commit_turn(&r, &p, &n).unwrap().events().len(), 2);
            assert_eq!(store.resume(&r.scope).unwrap().engine.revision(), 2);
        }
    }
    #[test]
    fn crash_child() {
        let Some(path) = std::env::var_os("LOCALLORE_ATOMIC_TEST_DB") else {
            return;
        };
        let stage = std::env::var("LOCALLORE_ATOMIC_TEST_STAGE")
            .unwrap()
            .parse()
            .unwrap();
        let mut store = Store::open(std::path::Path::new(&path), None).unwrap();
        let (r, p, n) = plan();
        FAULT.set(Some((stage, true)));
        let _ = store.commit_turn(&r, &p, &n);
        panic!("fault boundary did not exit");
    }
    #[test]
    fn process_exit_without_destructors_recovers_before_and_after_commit() {
        for stage in 0..=6 {
            let dir = Temp::new();
            let mut store = dir.open();
            store.create_story("Fixture", seed()).unwrap();
            let (r, p, n) = plan();
            store.begin_turn(&r).unwrap();
            drop(store);
            let mut child = std::process::Command::new(std::env::current_exe().unwrap())
                .args(["--exact", "turns::tests::crash_child", "--nocapture"])
                .env("LOCALLORE_ATOMIC_TEST_DB", dir.path())
                .env("LOCALLORE_ATOMIC_TEST_STAGE", stage.to_string())
                .stdout(std::process::Stdio::null())
                .stderr(std::process::Stdio::null())
                .spawn()
                .unwrap();
            let start = std::time::Instant::now();
            let status = loop {
                if let Some(status) = child.try_wait().unwrap() {
                    break status;
                }
                if start.elapsed() > std::time::Duration::from_secs(10) {
                    child.kill().unwrap();
                    let _ = child.wait();
                    panic!("child timeout");
                }
                std::thread::sleep(std::time::Duration::from_millis(10));
            };
            assert_eq!(status.code(), Some(77));
            let mut store = dir.open();
            let engine = store.resume(&r.scope).unwrap().engine;
            assert_eq!(engine.revision(), if stage == 6 { 2 } else { 0 });
            assert_eq!(
                engine.state().items["potion"].owner,
                if stage == 6 { "mira" } else { "player" }
            );
            assert_eq!(store.commit_turn(&r, &p, &n).unwrap().events().len(), 2);
            assert_eq!(store.resume(&r.scope).unwrap().engine.revision(), 2);
        }
    }
    #[test]
    fn sqlite_full_rolls_back_events_projection_response_status_and_head() {
        let dir = Temp::new();
        let mut store = dir.open();
        let s = seed();
        let scope = s.scope.clone();
        store.create_story("Fixture", s.clone()).unwrap();
        let engine = Engine::new(s).unwrap();
        let old = engine.canonical_bytes();
        let request = engine.request(
            "full",
            Intent::Actions(
                (0..7)
                    .map(|_| Command::Say {
                        text: "x".repeat(1800),
                        audience: ["mira".into()].into(),
                    })
                    .collect(),
            ),
        );
        let proposal = Engine::proposal(&request).unwrap();
        let text = engine
            .preview(&request, &proposal)
            .unwrap()
            .narration()
            .to_owned();
        store.begin_turn(&request).unwrap();
        let pages: i64 = store
            .connection
            .pragma_query_value(None, "page_count", |r| r.get(0))
            .unwrap();
        store
            .connection
            .pragma_update(None, "max_page_count", pages)
            .unwrap();
        assert_eq!(
            store.commit_turn(&request, &proposal, &text),
            Err(TurnError::Full)
        );
        assert_eq!(store.resume(&scope).unwrap().engine.canonical_bytes(), old);
        assert_eq!(store.turn_status(&request).unwrap().phase, TurnPhase::Draft);
        drop(store);
        let mut store = dir.open();
        assert_eq!(store.resume(&scope).unwrap().engine.revision(), 0);
    }
    #[test]
    fn projection_is_replaceable_but_canonical_rows_fail_closed() {
        let dir = Temp::new();
        let mut store = dir.open();
        store.create_story("Fixture", seed()).unwrap();
        let (r, p, n) = plan();
        store.begin_turn(&r).unwrap();
        store.commit_turn(&r, &p, &n).unwrap();
        let old = store.resume(&r.scope).unwrap().engine.canonical_bytes();
        store
            .connection
            .execute(
                "UPDATE branch_projections SET revision=0,projection_json='{}'",
                [],
            )
            .unwrap();
        let result = store.resume(&r.scope).unwrap();
        assert!(result.projection_needs_rebuild);
        assert_eq!(result.engine.canonical_bytes(), old);
        store.rebuild_projection(&r.scope).unwrap();
        assert!(!store.resume(&r.scope).unwrap().projection_needs_rebuild);
        store
            .connection
            .execute("DELETE FROM branch_projections", [])
            .unwrap();
        assert!(store.resume(&r.scope).unwrap().projection_needs_rebuild);
        store.rebuild_projection(&r.scope).unwrap();
        store
            .connection
            .execute("DELETE FROM event_witnesses WHERE observer_id='mira'", [])
            .unwrap();
        assert!(matches!(store.resume(&r.scope), Err(TurnError::Integrity)));
    }
    #[test]
    fn omitted_receipt_suffix_cannot_hide_a_persisted_head() {
        let dir = Temp::new();
        let mut store = dir.open();
        store.create_story("Fixture", seed()).unwrap();
        let (r, p, n) = plan();
        store.begin_turn(&r).unwrap();
        store.commit_turn(&r, &p, &n).unwrap();
        store
            .connection
            .execute("DELETE FROM event_witnesses", [])
            .unwrap();
        store
            .connection
            .execute("DELETE FROM accepted_events", [])
            .unwrap();
        store
            .connection
            .execute("UPDATE turns SET status='draft',response_json=NULL", [])
            .unwrap();
        assert!(matches!(store.resume(&r.scope), Err(TurnError::Integrity)));
    }
    #[test]
    fn writer_contention_is_bounded_and_draft_phase_releases_the_writer() {
        let dir = Temp::new();
        let mut first = dir.open();
        first.create_story("Fixture", seed()).unwrap();
        let mut second = dir.open();
        let (r, _, _) = plan();
        first.begin_turn(&r).unwrap();
        assert_eq!(second.turn_status(&r).unwrap().phase, TurnPhase::Draft);
        let tx = first
            .connection
            .transaction_with_behavior(TransactionBehavior::Immediate)
            .unwrap();
        assert!(matches!(
            second.cancel_turn(&r),
            Err(TurnError::Storage(StorageError::Busy))
        ));
        drop(tx);
        assert_eq!(second.cancel_turn(&r).unwrap().phase, TurnPhase::Cancelled);
    }
    #[test]
    fn actual_threads_cancel_against_commit_have_one_durable_winner() {
        for _ in 0..8 {
            let dir = Temp::new();
            let mut store = dir.open();
            store.create_story("Fixture", seed()).unwrap();
            let (r, p, n) = plan();
            store.begin_turn(&r).unwrap();
            let mut other = dir.open();
            let barrier = std::sync::Arc::new(std::sync::Barrier::new(2));
            let peer = barrier.clone();
            let rq = r.clone();
            let commit = std::thread::spawn(move || {
                peer.wait();
                store.commit_turn(&rq, &p, &n)
            });
            barrier.wait();
            let cancelled = other.cancel_turn(&r).unwrap();
            let committed = commit.join().unwrap();
            let engine = other.resume(&r.scope).unwrap().engine;
            if committed.is_ok() {
                assert_eq!(cancelled.phase, TurnPhase::Committed);
                assert_eq!(engine.revision(), 2);
            } else {
                assert_eq!(committed, Err(TurnError::Terminal));
                assert_eq!(cancelled.phase, TurnPhase::Cancelled);
                assert_eq!(engine.revision(), 0);
            }
        }
    }
}
