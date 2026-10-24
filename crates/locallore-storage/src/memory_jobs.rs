// Copyright 2026 LocalLore contributors. SPDX-License-Identifier: Apache-2.0
//! Restart-safe, bounded derived work. No persisted worker lease and no second canon.
//! Preparation releases its read transaction before Core builds a chunk. Publication
//! rebuilds against a fresh strict snapshot and atomically advances cache and cursor.
use crate::{
    derived_memory::{check, MemoryError},
    Store,
};
use locallore::{
    contracts::Scope,
    engine::Engine,
    memory_coverage::{self as coverage, CoverageRead},
};
use rusqlite::{params, Connection, OptionalExtension, TransactionBehavior};
use serde::Serialize;
use sha2::{Digest, Sha256};
use std::{
    io::{self, Write},
    sync::Arc,
};

pub(crate) const SCHEMA_SQL: &str = include_str!("../migrations/004_memory_jobs.sql");
#[cfg(test)]
mod pressure_tests;
pub const MAX_STORE_JOBS: usize = 256;
pub const MAX_PARTITION_JOBS: usize = 8;
const MAX_BASIS_BYTES: usize = 64 * 1024 * 1024;
type Result<T> = std::result::Result<T, MemoryError>;

#[derive(Clone, Debug)]
pub struct MemoryJobRequest {
    pub scope: Scope,
    pub observer: String,
    pub expected_head: u64,
}
impl MemoryJobRequest {
    fn coverage(&self) -> coverage::CoverageRequest {
        coverage::CoverageRequest {
            scope: self.scope.clone(),
            observer: self.observer.clone(),
            expected_head: self.expected_head,
        }
    }
    fn chunk(&self, from: u64) -> coverage::ChunkRequest {
        coverage::ChunkRequest {
            scope: self.scope.clone(),
            observer: self.observer.clone(),
            expected_head: self.expected_head,
            from_exclusive: from,
        }
    }
}
/// Native capability for this partition; no public constructor or Deserialize.
#[derive(Clone, Debug)]
pub struct MemoryJobHandle {
    id: u64,
    scope: Scope,
    observer: String,
    owner: Arc<()>,
}
impl PartialEq for MemoryJobHandle {
    fn eq(&self, other: &Self) -> bool {
        self.id == other.id
            && self.scope == other.scope
            && self.observer == other.observer
            && Arc::ptr_eq(&self.owner, &other.owner)
    }
}
impl Eq for MemoryJobHandle {}
impl MemoryJobHandle {
    pub fn id(&self) -> u64 {
        self.id
    }
}
#[derive(Clone, Copy, Debug, PartialEq, Eq)]
pub enum MemoryJobStatus {
    Ready,
    Cancelled,
    Stale,
    Complete,
    Blocked,
}
impl MemoryJobStatus {
    fn label(self) -> &'static str {
        match self {
            Self::Ready => "ready",
            Self::Cancelled => "cancelled",
            Self::Stale => "stale",
            Self::Complete => "complete",
            Self::Blocked => "blocked",
        }
    }
    fn parse(value: &str) -> Result<Self> {
        Ok(match value {
            "ready" => Self::Ready,
            "cancelled" => Self::Cancelled,
            "stale" => Self::Stale,
            "complete" => Self::Complete,
            "blocked" => Self::Blocked,
            _ => return Err(MemoryError::Integrity),
        })
    }
}
#[derive(Clone, Copy, Debug, PartialEq, Eq)]
pub enum MemoryJobFailure {
    Budget,
    PacketLimit,
    Integrity,
}
impl MemoryJobFailure {
    fn label(self) -> &'static str {
        match self {
            Self::Budget => "budget",
            Self::PacketLimit => "packet_limit",
            Self::Integrity => "integrity",
        }
    }
    fn parse(value: &str) -> Result<Self> {
        Ok(match value {
            "budget" => Self::Budget,
            "packet_limit" => Self::PacketLimit,
            "integrity" => Self::Integrity,
            _ => return Err(MemoryError::Integrity),
        })
    }
}
#[derive(Clone, Debug, PartialEq, Eq)]
pub struct MemoryJobInfo {
    pub handle: MemoryJobHandle,
    pub status: MemoryJobStatus,
    pub basis_revision: u64,
    pub next_from: u64,
    pub generation: u64,
    pub last_error: Option<MemoryJobFailure>,
}
/// Engine and unforgeable coverage proof originate in one SQLite read snapshot.
pub struct ContextSnapshot {
    pub engine: Engine,
    pub coverage: CoverageRead,
}
#[derive(Clone, Debug, PartialEq, Eq)]
struct Basis {
    seed: String,
    lineage: String,
    source: String,
}
struct Job {
    info: MemoryJobInfo,
    basis: Basis,
}
enum Step {
    Packet { bytes: Vec<u8>, through: u64 },
    Blocked(MemoryJobFailure),
}
/// One prepared boundary, never an accepted history or caller-supplied packet.
pub struct PreparedMemoryJobStep {
    job: Job,
    step: Step,
}

fn core_error(error: coverage::CoverageError) -> MemoryError {
    use coverage::CoverageError::*;
    match error {
        Cancelled => MemoryError::Cancelled,
        Scope => MemoryError::Scope,
        Stale => MemoryError::Stale,
        Observer => MemoryError::NotFound,
        Boundary => MemoryError::Integrity,
        Budget => MemoryError::TooLarge,
        Source => MemoryError::Integrity,
        Unsupported => MemoryError::Unsupported,
    }
}
fn integer(value: u64) -> Result<i64> {
    i64::try_from(value).map_err(|_| MemoryError::TooLarge)
}
fn unsigned(value: i64) -> Result<u64> {
    u64::try_from(value).map_err(|_| MemoryError::Integrity)
}
struct HashWriter {
    hash: Sha256,
    size: usize,
    exceeded: bool,
}
impl Write for HashWriter {
    fn write(&mut self, bytes: &[u8]) -> io::Result<usize> {
        if self
            .size
            .checked_add(bytes.len())
            .is_none_or(|n| n > MAX_BASIS_BYTES)
        {
            self.exceeded = true;
            return Err(io::Error::other("bounded source fingerprint"));
        }
        self.size += bytes.len();
        self.hash.update(bytes);
        Ok(bytes.len())
    }
    fn flush(&mut self) -> io::Result<()> {
        Ok(())
    }
}
fn digest(value: &impl Serialize) -> Result<String> {
    let mut writer = HashWriter {
        hash: Sha256::new(),
        size: 0,
        exceeded: false,
    };
    if serde_json::to_writer(&mut writer, value).is_err() {
        return Err(if writer.exceeded {
            MemoryError::TooLarge
        } else {
            MemoryError::Integrity
        });
    }
    Ok(format!("{:x}", writer.hash.finalize()))
}
fn basis(connection: &Connection, engine: &Engine, cancel: &dyn Fn() -> bool) -> Result<Basis> {
    check(cancel)?;
    if engine.domain_version() != 1 {
        return Err(MemoryError::Unsupported);
    }
    let path =
        crate::branches::lineage(connection, engine.scope()).map_err(|_| MemoryError::Integrity)?;
    // Mutable ancestor heads are deliberately excluded; accepted selected history
    // and immutable fork boundaries bind the actual source instead.
    let lineage = path
        .iter()
        .map(|b| (&b.scope, &b.parent, b.fork))
        .collect::<Vec<_>>();
    let result = Basis {
        seed: digest(engine.seed())?,
        lineage: digest(&lineage)?,
        source: digest(&(engine.seed(), engine.scope(), &lineage, engine.receipts()))?,
    };
    check(cancel)?;
    Ok(result)
}
fn validate(engine: &Engine, request: &MemoryJobRequest, cancel: &dyn Fn() -> bool) -> Result<()> {
    validate_selection(engine, request, cancel)?;
    if engine.domain_version() != 1 {
        return Err(MemoryError::Unsupported);
    }
    Ok(())
}
fn validate_selection(
    engine: &Engine,
    request: &MemoryJobRequest,
    cancel: &dyn Fn() -> bool,
) -> Result<()> {
    check(cancel)?;
    if engine.scope() != &request.scope {
        return Err(MemoryError::Scope);
    }
    if engine.revision() != request.expected_head {
        return Err(MemoryError::Stale);
    }
    if !engine.state().actors.contains_key(&request.observer) {
        return Err(MemoryError::NotFound);
    }
    Ok(())
}
// A native selected-player operation cannot turn a cached session into an
// arbitrary actor grant or accept a replacement history at the same head.
fn validate_selected(
    engine: &Engine,
    request: &MemoryJobRequest,
    selected: &Engine,
    cancel: &dyn Fn() -> bool,
) -> Result<()> {
    validate(engine, request, cancel)?;
    if engine.seed().player != request.observer
        || !engine
            .extends_accepted_history(selected)
            .map_err(|_| MemoryError::Stale)?
    {
        return Err(MemoryError::Stale);
    }
    check(cancel)
}
fn read_job(connection: &Connection, handle: &MemoryJobHandle) -> Result<Job> {
    let row=connection.query_row("SELECT basis_revision,next_from,generation,CASE WHEN length(CAST(status AS BLOB))<=9 THEN status ELSE '' END,CASE WHEN last_error IS NULL OR length(CAST(last_error AS BLOB))<=12 THEN last_error ELSE '!' END,CASE WHEN length(CAST(seed_sha256 AS BLOB))=64 THEN seed_sha256 ELSE '' END,CASE WHEN length(CAST(lineage_sha256 AS BLOB))=64 THEN lineage_sha256 ELSE '' END,CASE WHEN length(CAST(source_sha256 AS BLOB))=64 THEN source_sha256 ELSE '' END FROM memory_jobs WHERE job_id=?1 AND story_id=?2 AND branch_id=?3 AND observer_id=?4 AND method=?5 AND summary_version=2",
        params![integer(handle.id)?,handle.scope.story,handle.scope.branch,handle.observer,coverage::METHOD],|r|Ok((r.get::<_,i64>(0)?,r.get::<_,i64>(1)?,r.get::<_,i64>(2)?,r.get::<_,String>(3)?,r.get::<_,Option<String>>(4)?,r.get::<_,String>(5)?,r.get::<_,String>(6)?,r.get::<_,String>(7)?))).optional()?.ok_or(MemoryError::NotFound)?;
    let info = MemoryJobInfo {
        handle: handle.clone(),
        basis_revision: unsigned(row.0)?,
        next_from: unsigned(row.1)?,
        generation: unsigned(row.2)?,
        status: MemoryJobStatus::parse(&row.3)?,
        last_error: row.4.as_deref().map(MemoryJobFailure::parse).transpose()?,
    };
    if info.generation == 0
        || info.next_from > info.basis_revision
        || (info.status == MemoryJobStatus::Complete && info.next_from != info.basis_revision)
        || (info.status == MemoryJobStatus::Ready && info.next_from == info.basis_revision)
        || ((info.status == MemoryJobStatus::Blocked) != info.last_error.is_some())
        || [&row.5, &row.6, &row.7]
            .iter()
            .any(|hash| hash.len() != 64 || !hash.bytes().all(|b| b.is_ascii_hexdigit()))
    {
        return Err(MemoryError::Integrity);
    }
    Ok(Job {
        info,
        basis: Basis {
            seed: row.5,
            lineage: row.6,
            source: row.7,
        },
    })
}
fn find_job(
    connection: &Connection,
    request: &MemoryJobRequest,
    owner: &Arc<()>,
) -> Result<Option<Job>> {
    let id:Option<i64>=connection.query_row("SELECT job_id FROM memory_jobs WHERE story_id=?1 AND branch_id=?2 AND observer_id=?3 AND method=?4",params![request.scope.story,request.scope.branch,request.observer,coverage::METHOD],|r|r.get(0)).optional()?;
    id.map(|id| {
        read_job(
            connection,
            &MemoryJobHandle {
                id: unsigned(id)?,
                scope: request.scope.clone(),
                observer: request.observer.clone(),
                owner: owner.clone(),
            },
        )
    })
    .transpose()
}
fn packets(connection: &Connection, handle: &MemoryJobHandle) -> Result<Vec<Vec<u8>>> {
    // Bound allocation even if a foreign writer disabled CHECK constraints.
    let mut query=connection.prepare("SELECT CASE WHEN length(CAST(packet_json AS BLOB))<=65536 THEN packet_json ELSE NULL END FROM memory_job_packets WHERE job_id=?1 AND story_id=?2 AND branch_id=?3 AND observer_id=?4 ORDER BY from_revision LIMIT 33")?;
    let rows = query.query_map(
        params![
            integer(handle.id)?,
            handle.scope.story,
            handle.scope.branch,
            handle.observer
        ],
        |r| r.get::<_, Option<String>>(0),
    )?;
    Ok(rows
        .map(|r| r.map(|s| s.unwrap_or_default().into_bytes()))
        .collect::<std::result::Result<Vec<_>, _>>()?)
}
fn verify(
    engine: &Engine,
    request: &MemoryJobRequest,
    bytes: &[Vec<u8>],
    cancel: &dyn Fn() -> bool,
) -> Result<CoverageRead> {
    coverage::verify_coverage(
        engine,
        &request.coverage(),
        &bytes.iter().map(Vec::as_slice).collect::<Vec<_>>(),
        cancel,
    )
    .map_err(core_error)
}
fn prefix(
    engine: &Engine,
    request: &MemoryJobRequest,
    job: &Job,
    bytes: &[Vec<u8>],
    cancel: &dyn Fn() -> bool,
) -> Result<()> {
    if job.info.next_from == 0 && bytes.is_empty() {
        return Ok(());
    }
    match verify(engine, request, bytes, cancel)? {
        CoverageRead::Verified(proof) if proof.covered_through() == job.info.next_from => Ok(()),
        _ => Err(MemoryError::Integrity),
    }
}
fn request_for(job: &Job) -> MemoryJobRequest {
    MemoryJobRequest {
        scope: job.info.handle.scope.clone(),
        observer: job.info.handle.observer.clone(),
        expected_head: job.info.basis_revision,
    }
}
fn ensure_ready(job: &Job) -> Result<()> {
    match job.info.status {
        MemoryJobStatus::Ready => Ok(()),
        MemoryJobStatus::Cancelled => Err(MemoryError::Cancelled),
        MemoryJobStatus::Stale => Err(MemoryError::Stale),
        _ => Err(MemoryError::InvalidInput),
    }
}
fn next_generation(value: u64) -> Result<u64> {
    let value = value.checked_add(1).ok_or(MemoryError::TooLarge)?;
    integer(value)?;
    Ok(value)
}

impl Store {
    fn require_memory_job_owner(&self, handle: &MemoryJobHandle) -> Result<()> {
        if Arc::ptr_eq(&self.memory_job_owner, &handle.owner) {
            Ok(())
        } else {
            Err(MemoryError::NotFound)
        }
    }
    /// Idempotent admission/retarget. A cancelled job never resumes implicitly.
    /// A new head keeps only sealed chunks reverified against that actual Engine.
    pub fn ensure_memory_job(
        &mut self,
        request: &MemoryJobRequest,
        cancel: &dyn Fn() -> bool,
    ) -> Result<MemoryJobInfo> {
        self.ensure_memory_job_inner(request, None, cancel)
    }
    /// Explicit native selected-player admission. Both the initial read and
    /// the publication transaction check the same cached accepted-history basis.
    pub fn ensure_selected_memory_job(
        &mut self,
        request: &MemoryJobRequest,
        selected: &Engine,
        cancel: &dyn Fn() -> bool,
    ) -> Result<MemoryJobInfo> {
        self.ensure_memory_job_inner(request, Some(selected), cancel)
    }
    fn ensure_memory_job_inner(
        &mut self,
        request: &MemoryJobRequest,
        selected: Option<&Engine>,
        cancel: &dyn Fn() -> bool,
    ) -> Result<MemoryJobInfo> {
        check(cancel)?;
        let (engine, source, old, bytes) = {
            let tx = self.connection.transaction()?;
            let engine = Self::memory_engine(&tx, &request.scope, cancel)?;
            validate(&engine, request, cancel)?;
            if let Some(selected) = selected {
                validate_selected(&engine, request, selected, cancel)?;
            }
            let source = basis(&tx, &engine, cancel)?;
            let old = find_job(&tx, request, &self.memory_job_owner)?;
            let bytes = old
                .as_ref()
                .map(|j| packets(&tx, &j.info.handle))
                .transpose()?
                .unwrap_or_default();
            tx.commit()?;
            (engine, source, old, bytes)
        };
        if let Some(job) = &old {
            if job.info.status == MemoryJobStatus::Cancelled {
                return Ok(job.info.clone());
            }
            if job.basis == source && job.info.basis_revision == request.expected_head {
                match prefix(&engine, request, job, &bytes, cancel) {
                    Ok(()) => return Ok(job.info.clone()),
                    // A derived cache can be discarded; canonical validation
                    // has already succeeded. Retarget below advances generation
                    // and keeps only independently reverified sealed coverage.
                    Err(MemoryError::Integrity) => {}
                    Err(error) => return Err(error),
                }
            }
        }
        // Drop an old OpenTail BEFORE whole-set verification. A head change can
        // extend that turn window, so its previous closure is no longer proof.
        let mut sealed = Vec::new();
        for bytes in bytes {
            let value: serde_json::Value = match serde_json::from_slice(&bytes) {
                Ok(v) => v,
                Err(_) => {
                    sealed.clear();
                    break;
                }
            };
            if value["closure"]["kind"] == "open_tail" {
                break;
            }
            sealed.push(bytes);
        }
        let retained = match verify(&engine, request, &sealed, cancel)? {
            CoverageRead::Verified(proof) => proof
                .packets()
                .iter()
                .map(|p| {
                    Ok((
                        p.from_exclusive,
                        p.through_revision,
                        p.bytes().map_err(core_error)?,
                    ))
                })
                .collect::<Result<Vec<_>>>()?,
            CoverageRead::RawFallback(_) => vec![],
        };
        let cursor = retained.last().map_or(0, |p| p.1);
        let tx = self
            .connection
            .transaction_with_behavior(TransactionBehavior::Immediate)?;
        let actual = Self::memory_engine(&tx, &request.scope, cancel)?;
        validate(&actual, request, cancel)?;
        if let Some(selected) = selected {
            validate_selected(&actual, request, selected, cancel)?;
        }
        if basis(&tx, &actual, cancel)? != source {
            return Err(MemoryError::Stale);
        }
        let current = find_job(&tx, request, &self.memory_job_owner)?;
        if current.as_ref().map(|j| (&j.info, &j.basis))
            != old.as_ref().map(|j| (&j.info, &j.basis))
        {
            return Err(MemoryError::Stale);
        }
        let status = if cursor == request.expected_head {
            MemoryJobStatus::Complete
        } else {
            MemoryJobStatus::Ready
        };
        let handle = if let Some(job) = old {
            let generation = next_generation(job.info.generation)?;
            tx.execute(
                "DELETE FROM memory_job_packets WHERE job_id=?1",
                [integer(job.info.handle.id)?],
            )?;
            tx.execute("UPDATE memory_jobs SET basis_revision=?2,seed_sha256=?3,lineage_sha256=?4,source_sha256=?5,next_from=?6,generation=?7,status=?8,last_error=NULL WHERE job_id=?1",params![integer(job.info.handle.id)?,integer(request.expected_head)?,source.seed,source.lineage,source.source,integer(cursor)?,integer(generation)?,status.label()])?;
            job.info.handle
        } else {
            let count: i64 = tx.query_row("SELECT count(*) FROM memory_jobs", [], |r| r.get(0))?;
            if count >= MAX_STORE_JOBS as i64 {
                return Err(MemoryError::TooLarge);
            }
            tx.execute("INSERT INTO memory_jobs(story_id,branch_id,observer_id,method,summary_version,basis_revision,seed_sha256,lineage_sha256,source_sha256,next_from,generation,status) VALUES(?1,?2,?3,?4,2,?5,?6,?7,?8,0,1,?9)",params![request.scope.story,request.scope.branch,request.observer,coverage::METHOD,integer(request.expected_head)?,source.seed,source.lineage,source.source,status.label()])?;
            MemoryJobHandle {
                id: unsigned(tx.last_insert_rowid())?,
                scope: request.scope.clone(),
                observer: request.observer.clone(),
                owner: self.memory_job_owner.clone(),
            }
        };
        for (from, through, bytes) in retained {
            insert_packet(&tx, &handle, from, through, &bytes)?;
        }
        let info = read_job(&tx, &handle)?.info;
        check(cancel)?;
        tx.commit()?;
        Ok(info)
    }
    /// Passive native lookup, including after reopen. Reissues only a handle
    /// bound to this Store instance; never admits, retargets, repairs or writes.
    pub fn lookup_memory_job(
        &mut self,
        request: &MemoryJobRequest,
        selected: &Engine,
        cancel: &dyn Fn() -> bool,
    ) -> Result<Option<MemoryJobInfo>> {
        check(cancel)?;
        let tx = self.connection.transaction()?;
        let engine = Self::memory_engine(&tx, &request.scope, cancel)?;
        validate_selected(&engine, request, selected, cancel)?;
        let info = match find_job(&tx, request, &self.memory_job_owner)? {
            None => None,
            Some(job) => {
                let mut info = job.info;
                if info.status != MemoryJobStatus::Cancelled
                    && (engine.revision() != info.basis_revision
                        || basis(&tx, &engine, cancel)? != job.basis)
                {
                    info.status = MemoryJobStatus::Stale;
                }
                Some(info)
            }
        };
        check(cancel)?;
        tx.commit()?;
        Ok(info)
    }
    pub fn memory_job_status(
        &mut self,
        handle: &MemoryJobHandle,
        cancel: &dyn Fn() -> bool,
    ) -> Result<MemoryJobInfo> {
        check(cancel)?;
        self.require_memory_job_owner(handle)?;
        let tx = self.connection.transaction()?;
        let job = read_job(&tx, handle)?;
        let engine = Self::memory_engine(&tx, &handle.scope, cancel)?;
        if !engine.state().actors.contains_key(&handle.observer) {
            return Err(MemoryError::NotFound);
        }
        let mut info = job.info;
        if info.status != MemoryJobStatus::Cancelled
            && (engine.revision() != info.basis_revision
                || basis(&tx, &engine, cancel)? != job.basis)
        {
            info.status = MemoryJobStatus::Stale;
        }
        check(cancel)?;
        tx.commit()?;
        Ok(info)
    }
    pub fn prepare_memory_job_step(
        &mut self,
        handle: &MemoryJobHandle,
        cancel: &dyn Fn() -> bool,
    ) -> Result<PreparedMemoryJobStep> {
        check(cancel)?;
        self.require_memory_job_owner(handle)?;
        let (job, engine, count) = {
            let tx = self.connection.transaction()?;
            let job = read_job(&tx, handle)?;
            ensure_ready(&job)?;
            let engine = Self::memory_engine(&tx, &handle.scope, cancel)?;
            let request = request_for(&job);
            validate(&engine, &request, cancel)?;
            if basis(&tx, &engine, cancel)? != job.basis {
                return Err(MemoryError::Stale);
            }
            let bytes = packets(&tx, handle)?;
            prefix(&engine, &request, &job, &bytes, cancel)?;
            tx.commit()?;
            (job, engine, bytes.len())
        };
        let step = compute_step(&engine, &job, count, cancel)?;
        Ok(PreparedMemoryJobStep { job, step })
    }
    pub fn publish_memory_job_step(
        &mut self,
        prepared: PreparedMemoryJobStep,
        cancel: &dyn Fn() -> bool,
    ) -> Result<MemoryJobInfo> {
        check(cancel)?;
        self.require_memory_job_owner(&prepared.job.info.handle)?;
        let tx = self
            .connection
            .transaction_with_behavior(TransactionBehavior::Immediate)?;
        let current = read_job(&tx, &prepared.job.info.handle)?;
        if current.info != prepared.job.info || current.basis != prepared.job.basis {
            return Err(MemoryError::Stale);
        }
        ensure_ready(&current)?;
        let request = request_for(&current);
        let engine = Self::memory_engine(&tx, &request.scope, cancel)?;
        validate(&engine, &request, cancel)?;
        if basis(&tx, &engine, cancel)? != current.basis {
            return Err(MemoryError::Stale);
        }
        let bytes = packets(&tx, &current.info.handle)?;
        prefix(&engine, &request, &current, &bytes, cancel)?;
        let actual = compute_step(&engine, &current, bytes.len(), cancel)?;
        let (cursor, status, failure) = match (prepared.step, actual) {
            (
                Step::Packet { bytes, through },
                Step::Packet {
                    bytes: fresh,
                    through: end,
                },
            ) if bytes == fresh && through == end => {
                insert_packet(
                    &tx,
                    &current.info.handle,
                    current.info.next_from,
                    through,
                    &bytes,
                )?;
                (
                    through,
                    if through == current.info.basis_revision {
                        MemoryJobStatus::Complete
                    } else {
                        MemoryJobStatus::Ready
                    },
                    None,
                )
            }
            (Step::Blocked(reason), Step::Blocked(fresh)) if reason == fresh => (
                current.info.next_from,
                MemoryJobStatus::Blocked,
                Some(reason),
            ),
            _ => return Err(MemoryError::Integrity),
        };
        let generation = next_generation(current.info.generation)?;
        let changed=tx.execute("UPDATE memory_jobs SET next_from=?2,generation=?3,status=?4,last_error=?5 WHERE job_id=?1 AND generation=?6 AND status='ready'",params![integer(current.info.handle.id)?,integer(cursor)?,integer(generation)?,status.label(),failure.map(MemoryJobFailure::label),integer(current.info.generation)?])?;
        if changed != 1 {
            return Err(MemoryError::Stale);
        }
        let info = read_job(&tx, &current.info.handle)?.info;
        check(cancel)?;
        tx.commit()?;
        Ok(info)
    }
    pub fn cancel_memory_job(
        &mut self,
        handle: &MemoryJobHandle,
        cancel: &dyn Fn() -> bool,
    ) -> Result<MemoryJobInfo> {
        check(cancel)?;
        self.require_memory_job_owner(handle)?;
        let tx = self
            .connection
            .transaction_with_behavior(TransactionBehavior::Immediate)?;
        let job = read_job(&tx, handle)?;
        // A completed publication is not rolled back by a late cancellation.
        if !matches!(
            job.info.status,
            MemoryJobStatus::Complete | MemoryJobStatus::Cancelled
        ) {
            tx.execute("UPDATE memory_jobs SET status='cancelled',generation=?2,last_error=NULL WHERE job_id=?1",params![integer(handle.id)?,integer(next_generation(job.info.generation)?)?])?;
        }
        let info = read_job(&tx, handle)?.info;
        check(cancel)?;
        tx.commit()?;
        Ok(info)
    }
    pub fn prune_memory_job(
        &mut self,
        handle: &MemoryJobHandle,
        cancel: &dyn Fn() -> bool,
    ) -> Result<()> {
        check(cancel)?;
        self.require_memory_job_owner(handle)?;
        let tx = self
            .connection
            .transaction_with_behavior(TransactionBehavior::Immediate)?;
        let job = read_job(&tx, handle)?;
        if job.info.status == MemoryJobStatus::Ready {
            return Err(MemoryError::Busy);
        }
        tx.execute(
            "DELETE FROM memory_jobs WHERE job_id=?1",
            [integer(handle.id)?],
        )?;
        check(cancel)?;
        tx.commit()?;
        Ok(())
    }
    pub fn context_snapshot(
        &mut self,
        request: &MemoryJobRequest,
        cancel: &dyn Fn() -> bool,
    ) -> Result<ContextSnapshot> {
        check(cancel)?;
        let tx = self.connection.transaction()?;
        let engine = Self::memory_engine(&tx, &request.scope, cancel)?;
        validate_selection(&engine, request, cancel)?;
        if engine.domain_version() != 1 {
            check(cancel)?;
            tx.commit()?;
            return Ok(ContextSnapshot {
                engine,
                coverage: CoverageRead::RawFallback(coverage::FallbackReason::Unsupported),
            });
        }
        // No writes, admission, cursor repair, or canonical mutation on a read.
        let coverage = match find_job(&tx, request, &self.memory_job_owner) {
            Ok(job) => {
                let bytes = job
                    .map(|job| packets(&tx, &job.info.handle))
                    .transpose()?
                    .unwrap_or_default();
                verify(&engine, request, &bytes, cancel)?
            }
            // Only derived metadata is rejected here. Strict canonical replay
            // already succeeded above; preserve usable raw context without a write.
            Err(MemoryError::Integrity) => {
                CoverageRead::RawFallback(coverage::FallbackReason::Malformed)
            }
            Err(error) => return Err(error),
        };
        check(cancel)?;
        tx.commit()?;
        Ok(ContextSnapshot { engine, coverage })
    }
}
fn compute_step(
    engine: &Engine,
    job: &Job,
    count: usize,
    cancel: &dyn Fn() -> bool,
) -> Result<Step> {
    check(cancel)?;
    if count >= coverage::MAX_PACKETS {
        return Ok(Step::Blocked(MemoryJobFailure::PacketLimit));
    }
    match coverage::build_chunk(engine, &request_for(job).chunk(job.info.next_from), cancel) {
        Ok(Some(packet)) => Ok(Step::Packet {
            through: packet.through_revision,
            bytes: packet.bytes().map_err(core_error)?,
        }),
        Ok(None) => Err(MemoryError::Integrity),
        Err(coverage::CoverageError::Budget) => Ok(Step::Blocked(MemoryJobFailure::Budget)),
        Err(error) => Err(core_error(error)),
    }
}
fn insert_packet(
    connection: &Connection,
    handle: &MemoryJobHandle,
    from: u64,
    through: u64,
    bytes: &[u8],
) -> Result<()> {
    if bytes.len() > coverage::MAX_PACKET_BYTES {
        return Err(MemoryError::TooLarge);
    }
    let text = std::str::from_utf8(bytes).map_err(|_| MemoryError::Integrity)?;
    connection.execute("INSERT INTO memory_job_packets(job_id,story_id,branch_id,observer_id,from_revision,through_revision,packet_json) VALUES(?1,?2,?3,?4,?5,?6,?7)",params![integer(handle.id)?,handle.scope.story,handle.scope.branch,handle.observer,integer(from)?,integer(through)?,text])?;
    Ok(())
}
