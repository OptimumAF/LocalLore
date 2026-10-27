// Copyright 2026 LocalLore contributors. SPDX-License-Identifier: Apache-2.0
//! Stateless native-only player inspection of rechecked deterministic coverage.
//! No Deserialize, raw basis, generation, maintenance admission or persistence writer.
use super::Host;
use crate::{
    contracts::Scope,
    engine::{valid_id, Engine},
    inspection_query::{self, Observer, Page, Privacy, Query, QueryError, Row, View},
    memory_coverage::{
        Closure, CoverageError, CoverageRead, CoverageRequest, Entry, FallbackReason, SourceRef,
        TypedPacket,
    },
};
use serde::Serialize;
use sha2::{Digest, Sha256};
use std::{
    cell::Cell,
    io::{self, Write},
};

pub const MAX_REPLY_BYTES: usize = 65_536;
pub const MAX_SOURCE_BINDING_BYTES: usize = 64 * 1024 * 1024;
pub const MAX_SAFE_INTEGER: u64 = 9_007_199_254_740_991;
const MAX_CURSOR_BYTES: usize = 128;

#[derive(Clone, Debug)]
pub struct MemoryInspectionRequestV1 {
    pub version: u16,
    pub scope: Scope,
    pub expected_head: u64,
    pub observer: Observer,
    pub binding: Option<String>,
    pub view: MemoryInspectionViewV1,
}
#[derive(Clone, Debug)]
pub enum MemoryInspectionViewV1 {
    Packets {
        cursor: Option<String>,
        limit: u16,
    },
    Entries {
        packet_index: u8,
        cursor: Option<String>,
        limit: u16,
    },
    Source {
        packet_index: u8,
        source: SourceRef,
    },
}
#[derive(Clone, Copy, Debug, PartialEq, Eq, Serialize)]
#[serde(rename_all = "snake_case")]
pub enum MemoryInspectionError {
    Version,
    Forbidden,
    Closed,
    Scope,
    Stale,
    Unsupported,
    InvalidInput,
    InvalidCursor,
    Binding,
    TooLarge,
    Cancelled,
    Integrity,
    Unavailable,
    Busy,
    Database,
    Full,
    Internal,
}
impl std::fmt::Display for MemoryInspectionError {
    fn fmt(&self, f: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(f, "{self:?}")
    }
}
impl std::error::Error for MemoryInspectionError {}
type Result<T> = std::result::Result<T, MemoryInspectionError>;
use MemoryInspectionError as Error;

#[derive(Clone, Copy, Debug, PartialEq, Eq, Serialize)]
#[serde(rename_all = "snake_case")]
pub enum MemoryFallbackV1 {
    Missing,
    Budget,
    Malformed,
    Unsupported,
    Binding,
    Gap,
    Overlap,
    OpenTailBeforeEnd,
    UnprovableClosure,
    SourceMismatch,
}
impl From<FallbackReason> for MemoryFallbackV1 {
    fn from(reason: FallbackReason) -> Self {
        match reason {
            FallbackReason::Missing => Self::Missing,
            FallbackReason::Budget => Self::Budget,
            FallbackReason::Malformed => Self::Malformed,
            FallbackReason::Unsupported => Self::Unsupported,
            FallbackReason::Binding => Self::Binding,
            FallbackReason::Gap => Self::Gap,
            FallbackReason::Overlap => Self::Overlap,
            FallbackReason::OpenTailBeforeEnd => Self::OpenTailBeforeEnd,
            FallbackReason::UnprovableClosure => Self::UnprovableClosure,
            FallbackReason::SourceMismatch => Self::SourceMismatch,
        }
    }
}
#[derive(Clone, Copy, Debug, PartialEq, Eq, Serialize)]
#[serde(rename_all = "snake_case")]
pub enum MemoryCoverageStatusV1 {
    Verified,
    RawFallback,
}
#[derive(Clone, Debug, PartialEq, Eq, Serialize)]
pub struct MemoryCoverageV1 {
    pub status: MemoryCoverageStatusV1,
    pub verified_head: Option<u64>,
    pub covered_through: Option<u64>,
    pub raw_delta_after: u64,
    pub fallback: Option<MemoryFallbackV1>,
}
#[derive(Clone, Copy, Debug, PartialEq, Eq, Serialize)]
#[serde(rename_all = "snake_case")]
pub enum MemoryInspectionPageViewV1 {
    Packets,
    Entries,
}
#[derive(Clone, Debug, PartialEq, Eq, Serialize)]
#[serde(tag = "kind", rename_all = "snake_case")]
pub enum MemoryInspectionRowV1 {
    Packet {
        index: u8,
        version: u16,
        method: String,
        from_exclusive: u64,
        through_revision: u64,
        receipt_count: usize,
        closure: Closure,
        entry_count: usize,
        source_event_count: usize,
    },
    Entry {
        packet_index: u8,
        index: usize,
        value: Entry,
    },
}
#[derive(Clone, Debug, PartialEq, Eq, Serialize)]
pub struct MemoryInspectionPageV1 {
    pub version: u16,
    pub session: String,
    pub scope: Scope,
    pub head: u64,
    /// Actual native seed player, never a caller-supplied Character ID.
    pub observer: String,
    pub privacy: Privacy,
    pub binding: String,
    pub coverage: MemoryCoverageV1,
    pub view: MemoryInspectionPageViewV1,
    pub packet_index: Option<u8>,
    pub total: usize,
    pub rows: Vec<MemoryInspectionRowV1>,
    pub next_cursor: Option<String>,
}
#[derive(Clone, Debug, PartialEq, Eq, Serialize)]
pub struct MemoryInspectionSourceV1 {
    pub version: u16,
    pub session: String,
    pub scope: Scope,
    pub head: u64,
    pub observer: String,
    pub privacy: Privacy,
    pub binding: String,
    pub packet_index: u8,
    pub source: SourceRef,
    /// A successful response always has an exact original-scope event match.
    pub matched: bool,
    pub page: Page,
}
#[derive(Clone, Debug, PartialEq, Eq, Serialize)]
#[serde(tag = "kind")]
pub enum MemoryInspectionReplyV1 {
    #[serde(rename = "memory_inspection")]
    Page(MemoryInspectionPageV1),
    #[serde(rename = "memory_source")]
    Source(MemoryInspectionSourceV1),
}

fn check(cancel: &dyn Fn() -> bool) -> Result<()> {
    if std::panic::catch_unwind(std::panic::AssertUnwindSafe(cancel)).unwrap_or(true) {
        Err(Error::Cancelled)
    } else {
        Ok(())
    }
}
fn port_error(error: &str) -> Error {
    match error {
        "Closed" => Error::Closed,
        "Scope" => Error::Scope,
        "Stale" => Error::Stale,
        "Unsupported" => Error::Unsupported,
        "Cancelled" => Error::Cancelled,
        "Busy" => Error::Busy,
        "TooLarge" => Error::TooLarge,
        "Integrity" => Error::Integrity,
        "Database" => Error::Database,
        "Full" => Error::Full,
        _ => Error::Internal,
    }
}
fn coverage_error(error: CoverageError) -> Error {
    match error {
        CoverageError::Cancelled => Error::Cancelled,
        CoverageError::Scope => Error::Scope,
        CoverageError::Stale => Error::Stale,
        CoverageError::Observer => Error::Forbidden,
        CoverageError::Budget => Error::TooLarge,
        CoverageError::Unsupported => Error::Unsupported,
        CoverageError::Boundary | CoverageError::Source => Error::Integrity,
    }
}
fn query_error(error: QueryError) -> Error {
    match error {
        QueryError::Version => Error::Version,
        QueryError::Scope => Error::Scope,
        QueryError::Stale => Error::Stale,
        QueryError::Forbidden | QueryError::UnknownObserver => Error::Forbidden,
        QueryError::InvalidBoundary | QueryError::Integrity => Error::Integrity,
        QueryError::InvalidCursor => Error::InvalidCursor,
        QueryError::InvalidRequest => Error::InvalidInput,
        QueryError::TooLarge => Error::TooLarge,
        QueryError::UnsupportedBranch => Error::Unsupported,
    }
}
fn valid_scope(scope: &Scope) -> bool {
    valid_id(&scope.story) && valid_id(&scope.branch)
}
fn hex(value: &str) -> bool {
    value.len() == 64
        && value
            .bytes()
            .all(|b| b.is_ascii_digit() || (b'a'..=b'f').contains(&b))
}
fn valid_request(session: &str, request: &MemoryInspectionRequestV1) -> Result<()> {
    if request.version != 1 {
        return Err(Error::Version);
    }
    if !valid_id(session)
        || !valid_scope(&request.scope)
        || request.expected_head > MAX_SAFE_INTEGER
        || request.binding.as_ref().is_some_and(|value| !hex(value))
    {
        return Err(Error::InvalidInput);
    }
    match &request.view {
        MemoryInspectionViewV1::Packets { cursor, limit }
        | MemoryInspectionViewV1::Entries { cursor, limit, .. } => {
            if *limit == 0 || *limit > 64 {
                return Err(Error::InvalidInput);
            }
            if cursor
                .as_ref()
                .is_some_and(|value| value.len() > MAX_CURSOR_BYTES)
            {
                return Err(Error::InvalidCursor);
            }
            if cursor.is_some() && request.binding.is_none() {
                return Err(Error::InvalidInput);
            }
        }
        MemoryInspectionViewV1::Source { source, .. } => {
            if !valid_scope(&source.scope)
                || source.sequence == 0
                || source.sequence > request.expected_head
            {
                return Err(Error::InvalidInput);
            }
        }
    }
    match &request.view {
        MemoryInspectionViewV1::Entries { packet_index, .. }
        | MemoryInspectionViewV1::Source { packet_index, .. } => {
            if *packet_index >= 32 || request.binding.is_none() {
                return Err(Error::InvalidInput);
            }
        }
        _ => {}
    }
    Ok(())
}

/// Streaming source identity; never accumulates or returns the canonical input.
struct BindingWriter<'a> {
    hash: Sha256,
    written: usize,
    error: Option<Error>,
    cancel: &'a dyn Fn() -> bool,
}
impl Write for BindingWriter<'_> {
    fn write(&mut self, bytes: &[u8]) -> io::Result<usize> {
        let result = check(self.cancel).and_then(|()| {
            self.written
                .checked_add(bytes.len())
                .filter(|size| *size <= MAX_SOURCE_BINDING_BYTES)
                .ok_or(Error::TooLarge)
        });
        match result {
            Ok(size) => {
                self.written = size;
                self.hash.update(bytes);
                Ok(bytes.len())
            }
            Err(error) => {
                self.error = Some(error);
                Err(io::Error::other("bounded inspection source"))
            }
        }
    }
    fn flush(&mut self) -> io::Result<()> {
        Ok(())
    }
}
fn source_binding(
    engine: &Engine,
    session: &str,
    coverage: &MemoryCoverageV1,
    packets: &[TypedPacket],
    cancel: &dyn Fn() -> bool,
) -> Result<String> {
    check(cancel)?;
    let lineage = engine
        .memory_lineage_binding()
        .map_err(|_| Error::Integrity)?;
    let mut writer = BindingWriter {
        hash: Sha256::new(),
        written: 0,
        error: None,
        cancel,
    };
    // JSON gives an unambiguous closed metadata/history frame. Packet binary
    // frames have explicit length prefixes; packet count is bound in this frame.
    serde_json::to_writer(
        &mut writer,
        &(
            "locallore-memory-inspection-v1",
            session,
            engine.scope(),
            engine.revision(),
            &engine.seed().player,
            engine.seed(),
            lineage,
            engine.canonical_records(),
            coverage,
            packets.len(),
        ),
    )
    .map_err(|_| writer.error.unwrap_or(Error::Integrity))?;
    for packet in packets {
        check(cancel)?;
        let bytes = packet.bytes().map_err(coverage_error)?;
        writer
            .write_all(&(bytes.len() as u64).to_le_bytes())
            .map_err(|_| writer.error.unwrap_or(Error::Integrity))?;
        writer
            .write_all(&bytes)
            .map_err(|_| writer.error.unwrap_or(Error::Integrity))?;
    }
    check(cancel)?;
    Ok(format!("{:x}", writer.hash.finalize()))
}
struct ReplyWriter {
    bytes: Vec<u8>,
    exceeded: bool,
}
impl Write for ReplyWriter {
    fn write(&mut self, bytes: &[u8]) -> io::Result<usize> {
        if self
            .bytes
            .len()
            .checked_add(bytes.len())
            .is_none_or(|size| size > MAX_REPLY_BYTES)
        {
            self.exceeded = true;
            return Err(io::Error::other("bounded inspection reply"));
        }
        self.bytes.extend_from_slice(bytes);
        Ok(bytes.len())
    }
    fn flush(&mut self) -> io::Result<()> {
        Ok(())
    }
}
fn safe_numbers(value: &serde_json::Value, cancel: &dyn Fn() -> bool) -> Result<()> {
    check(cancel)?;
    match value {
        serde_json::Value::Number(number) => {
            let valid = number.as_u64().is_some_and(|n| n <= MAX_SAFE_INTEGER)
                || number.as_i64().is_some_and(|n| {
                    n >= -(MAX_SAFE_INTEGER as i64) && n <= MAX_SAFE_INTEGER as i64
                });
            if !valid {
                return Err(Error::TooLarge);
            }
        }
        serde_json::Value::Array(values) => {
            for value in values {
                safe_numbers(value, cancel)?;
            }
        }
        serde_json::Value::Object(values) => {
            for value in values.values() {
                safe_numbers(value, cancel)?;
            }
        }
        _ => {}
    }
    Ok(())
}
fn bounded_reply(reply: &MemoryInspectionReplyV1, cancel: &dyn Fn() -> bool) -> Result<()> {
    check(cancel)?;
    let mut writer = ReplyWriter {
        bytes: vec![],
        exceeded: false,
    };
    serde_json::to_writer(&mut writer, reply).map_err(|_| {
        if writer.exceeded {
            Error::TooLarge
        } else {
            Error::Integrity
        }
    })?;
    check(cancel)?;
    let value = serde_json::from_slice(&writer.bytes).map_err(|_| Error::Integrity)?;
    safe_numbers(&value, cancel)
}
fn cursor_for(
    binding: &str,
    view: MemoryInspectionPageViewV1,
    packet: Option<u8>,
    limit: u16,
    offset: usize,
) -> String {
    let mut hash = Sha256::new();
    hash.update(b"locallore-memory-inspection-cursor-v1\0");
    hash.update(binding.as_bytes());
    hash.update([match view {
        MemoryInspectionPageViewV1::Packets => 0,
        MemoryInspectionPageViewV1::Entries => 1,
    }]);
    hash.update([packet.unwrap_or(u8::MAX)]);
    hash.update(limit.to_le_bytes());
    hash.update((offset as u64).to_le_bytes());
    format!("mp1:{offset}:{:x}", hash.finalize())
}
fn read_offset(
    cursor: &Option<String>,
    binding: &str,
    view: MemoryInspectionPageViewV1,
    packet: Option<u8>,
    limit: u16,
    total: usize,
) -> Result<usize> {
    let Some(value) = cursor else {
        return Ok(0);
    };
    let mut parts = value.split(':');
    if parts.next() != Some("mp1") {
        return Err(Error::InvalidCursor);
    }
    let offset = parts
        .next()
        .and_then(|s| s.parse::<usize>().ok())
        .ok_or(Error::InvalidCursor)?;
    if offset == 0 || offset >= total || value != &cursor_for(binding, view, packet, limit, offset)
    {
        return Err(Error::InvalidCursor);
    }
    Ok(offset)
}
fn page_rows(
    mut page: MemoryInspectionPageV1,
    rows: Vec<MemoryInspectionRowV1>,
    cursor: &Option<String>,
    limit: u16,
    cancel: &dyn Fn() -> bool,
) -> Result<MemoryInspectionReplyV1> {
    let offset = read_offset(
        cursor,
        &page.binding,
        page.view,
        page.packet_index,
        limit,
        rows.len(),
    )?;
    let end = rows.len().min(offset + usize::from(limit));
    for (index, row) in rows.into_iter().enumerate().take(end).skip(offset) {
        check(cancel)?;
        page.rows.push(row);
        page.next_cursor = (index + 1 < page.total).then(|| {
            cursor_for(
                &page.binding,
                page.view,
                page.packet_index,
                limit,
                index + 1,
            )
        });
        let reply = MemoryInspectionReplyV1::Page(page);
        let valid = bounded_reply(&reply, cancel);
        let MemoryInspectionReplyV1::Page(mut current) = reply else {
            unreachable!()
        };
        match valid {
            Ok(()) => page = current,
            Err(Error::TooLarge) => {
                current.rows.pop();
                if current.rows.is_empty() {
                    return Err(Error::TooLarge);
                }
                current.next_cursor = Some(cursor_for(
                    &current.binding,
                    current.view,
                    current.packet_index,
                    limit,
                    offset + current.rows.len(),
                ));
                let reply = MemoryInspectionReplyV1::Page(current);
                bounded_reply(&reply, cancel)?;
                return Ok(reply);
            }
            Err(error) => return Err(error),
        }
    }
    let reply = MemoryInspectionReplyV1::Page(page);
    bounded_reply(&reply, cancel)?;
    Ok(reply)
}

impl Host {
    /// Synchronous native read. Callbacks must not reenter Host/Store. No wire
    /// request, observer selection or cache bytes confer the trusted Lab grant.
    pub fn memory_inspection(
        &self,
        session: &str,
        request: &MemoryInspectionRequestV1,
        cancel: &dyn Fn() -> bool,
    ) -> Result<MemoryInspectionReplyV1> {
        if !self.story_lab || request.observer != Observer::Player {
            return Err(Error::Forbidden);
        }
        valid_request(session, request)?;
        let cancelled = Cell::new(false);
        let safe_cancel = || {
            if !cancelled.get() {
                cancelled.set(check(cancel).is_err());
            }
            cancelled.get()
        };
        check(&safe_cancel)?;
        {
            let state = self.state.lock().map_err(|_| Error::Internal)?;
            let selected = state.sessions.get(session).ok_or(Error::Closed)?;
            if selected.engine.scope() != &request.scope {
                return Err(Error::Scope);
            }
            if selected.engine.domain_version() != 1 {
                return Err(Error::Unsupported);
            }
        }
        let snapshot =
            self.generation_snapshot(session, &request.scope, request.expected_head, &safe_cancel);
        // An override may fail after observing cancellation. Keep the sticky
        // cancellation result even on that error path, before translating text.
        check(&safe_cancel)?;
        let snapshot = snapshot.map_err(|error| port_error(&error))?;
        let engine = snapshot.engine;
        if engine.domain_version() != 1 {
            return Err(Error::Unsupported);
        }
        let rechecked = match snapshot.coverage {
            CoverageRead::Verified(proof) => proof
                .recheck(
                    &engine,
                    &CoverageRequest {
                        scope: request.scope.clone(),
                        expected_head: request.expected_head,
                        observer: engine.seed().player.clone(),
                    },
                    &safe_cancel,
                )
                .map_err(coverage_error)?,
            fallback @ CoverageRead::RawFallback(_) => fallback,
        };
        check(&safe_cancel)?;
        let (coverage, packets) = match &rechecked {
            CoverageRead::Verified(proof) => (
                MemoryCoverageV1 {
                    status: MemoryCoverageStatusV1::Verified,
                    verified_head: Some(proof.verified_head()),
                    covered_through: Some(proof.covered_through()),
                    raw_delta_after: proof.raw_delta_after(),
                    fallback: None,
                },
                proof.packets(),
            ),
            CoverageRead::RawFallback(reason) => (
                MemoryCoverageV1 {
                    status: MemoryCoverageStatusV1::RawFallback,
                    verified_head: None,
                    covered_through: None,
                    raw_delta_after: 0,
                    fallback: Some((*reason).into()),
                },
                &[][..],
            ),
        };
        let binding = source_binding(&engine, session, &coverage, packets, &safe_cancel)?;
        if request
            .binding
            .as_ref()
            .is_some_and(|value| value != &binding)
        {
            return Err(Error::Binding);
        }
        if let MemoryInspectionViewV1::Source {
            packet_index,
            source,
        } = &request.view
        {
            let packet = packets
                .get(usize::from(*packet_index))
                .ok_or(Error::Unavailable)?;
            if !packet.source_events.contains(source) {
                return Err(Error::InvalidInput);
            }
            let query = Query {
                version: 2,
                scope: engine.scope().clone(),
                expected_head: engine.revision(),
                at_revision: Some(packet.through_revision),
                observer: Observer::Player,
                view: View::History,
                cursor: None,
                limit: 64,
                search: format!("\"sequence\":{},", source.sequence),
            };
            check(&safe_cancel)?;
            let page =
                inspection_query::query(&engine, &query, self.story_lab).map_err(query_error)?;
            check(&safe_cancel)?;
            if !page.rows.iter().any(|row| {
                matches!(row, Row::Event { event, .. }
                if event.scope == source.scope && event.sequence == source.sequence)
            }) {
                return Err(Error::Unavailable);
            }
            let reply = MemoryInspectionReplyV1::Source(MemoryInspectionSourceV1 {
                version: 1,
                session: session.into(),
                scope: engine.scope().clone(),
                head: engine.revision(),
                observer: engine.seed().player.clone(),
                privacy: Privacy::PlayerVisible,
                binding,
                packet_index: *packet_index,
                source: source.clone(),
                matched: true,
                page,
            });
            bounded_reply(&reply, &safe_cancel)?;
            return Ok(reply);
        }
        let (view, packet_index, cursor, limit, rows) = match &request.view {
            MemoryInspectionViewV1::Packets { cursor, limit } => (
                MemoryInspectionPageViewV1::Packets,
                None,
                cursor,
                *limit,
                packets
                    .iter()
                    .enumerate()
                    .map(|(index, packet)| MemoryInspectionRowV1::Packet {
                        index: index as u8,
                        version: packet.version,
                        method: packet.method.clone(),
                        from_exclusive: packet.from_exclusive,
                        through_revision: packet.through_revision,
                        receipt_count: packet.receipt_count,
                        closure: packet.closure.clone(),
                        entry_count: packet.entries.len(),
                        source_event_count: packet.source_events.len(),
                    })
                    .collect::<Vec<_>>(),
            ),
            MemoryInspectionViewV1::Entries {
                packet_index,
                cursor,
                limit,
            } => {
                let packet = packets
                    .get(usize::from(*packet_index))
                    .ok_or(Error::Unavailable)?;
                (
                    MemoryInspectionPageViewV1::Entries,
                    Some(*packet_index),
                    cursor,
                    *limit,
                    packet
                        .entries
                        .iter()
                        .enumerate()
                        .map(|(index, value)| MemoryInspectionRowV1::Entry {
                            packet_index: *packet_index,
                            index,
                            value: value.clone(),
                        })
                        .collect(),
                )
            }
            MemoryInspectionViewV1::Source { .. } => unreachable!(),
        };
        let page = MemoryInspectionPageV1 {
            version: 1,
            session: session.into(),
            scope: engine.scope().clone(),
            head: engine.revision(),
            observer: engine.seed().player.clone(),
            privacy: Privacy::PlayerVisible,
            binding,
            coverage,
            view,
            packet_index,
            total: rows.len(),
            rows: vec![],
            next_cursor: None,
        };
        page_rows(page, rows, cursor, limit, &safe_cancel)
    }
}
