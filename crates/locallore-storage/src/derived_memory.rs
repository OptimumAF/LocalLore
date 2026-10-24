// Copyright 2026 LocalLore contributors. SPDX-License-Identifier: Apache-2.0
//! Derived cache helpers for the sole Store owner.
//! Never open a connection, migrate a database, accept wire history, or establish canon here.
use locallore::{contracts::*, engine::Engine};
#[cfg(test)]
use rusqlite::TransactionBehavior;
use rusqlite::{params, Connection, OptionalExtension};
use serde_json::{json, Value};

pub const VERSION: u16 = 1;
pub const MAX_EVENTS: usize = 256;
pub const MAX_SOURCE_BYTES: usize = 1_048_576;
pub const MAX_PACKET_BYTES: usize = 65_536;
pub const MAX_PARTITION_PACKETS: usize = 32;
pub const MAX_QUERY_BYTES: usize = 256;
pub const MAX_SEARCH_TERMS: usize = 16;
pub const MAX_HITS: usize = 16;

pub(crate) const DERIVED_SCHEMA_SQL: &str = include_str!("../migrations/002_derived_memory.sql");

#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum MemoryError {
    Scope,
    Stale,
    InvalidInput,
    #[cfg_attr(test, allow(dead_code))]
    // Store schema guard is outside the isolated fixture module.
    Unsupported,
    NotFound,
    TooLarge,
    Cancelled,
    Integrity,
    Database,
    Busy,
    Full,
}
impl From<rusqlite::Error> for MemoryError {
    fn from(error: rusqlite::Error) -> Self {
        match error.sqlite_error_code() {
            Some(rusqlite::ErrorCode::DatabaseBusy | rusqlite::ErrorCode::DatabaseLocked) => {
                Self::Busy
            }
            Some(rusqlite::ErrorCode::DiskFull) => Self::Full,
            _ => Self::Database,
        }
    }
}
impl From<Error> for MemoryError {
    fn from(error: Error) -> Self {
        match error {
            Error::Scope => Self::Scope,
            Error::Stale => Self::Stale,
            Error::Cancelled => Self::Cancelled,
            Error::UnknownReference => Self::NotFound,
            _ => Self::Integrity,
        }
    }
}
type Result<T> = std::result::Result<T, MemoryError>;

#[derive(Clone, Copy, Debug, PartialEq, Eq)]
pub enum EntityKind {
    Actor,
    Item,
    Location,
    Ability,
    Fact,
    Commitment,
}
impl EntityKind {
    fn label(self) -> &'static str {
        match self {
            Self::Actor => "actor",
            Self::Item => "item",
            Self::Location => "location",
            Self::Ability => "ability",
            Self::Fact => "fact",
            Self::Commitment => "commitment",
        }
    }
}
#[derive(Clone, Debug, PartialEq, Eq)]
pub enum Target {
    SceneWindow,
    Entity { kind: EntityKind, id: String },
}
impl Target {
    fn json(&self) -> Value {
        match self {
            Self::SceneWindow => json!({"kind":"scene_window"}),
            Self::Entity { kind, id } => {
                json!({"kind":"entity","entity_kind":kind.label(),"id":id})
            }
        }
    }
    fn parse(value: &Value) -> Result<Self> {
        let object = value.as_object().ok_or(MemoryError::Integrity)?;
        match value["kind"].as_str() {
            Some("scene_window") if object.len() == 1 => Ok(Self::SceneWindow),
            Some("entity") if object.len() == 3 => {
                let kind = match value["entity_kind"].as_str() {
                    Some("actor") => EntityKind::Actor,
                    Some("item") => EntityKind::Item,
                    Some("location") => EntityKind::Location,
                    Some("ability") => EntityKind::Ability,
                    Some("fact") => EntityKind::Fact,
                    Some("commitment") => EntityKind::Commitment,
                    _ => return Err(MemoryError::Integrity),
                };
                let id = value["id"]
                    .as_str()
                    .filter(|v| valid_id(v))
                    .ok_or(MemoryError::Integrity)?;
                Ok(Self::Entity {
                    kind,
                    id: id.into(),
                })
            }
            _ => Err(MemoryError::Integrity),
        }
    }
    fn includes(&self, effect: &Effect) -> bool {
        let Self::Entity { kind, id } = self else {
            return true;
        };
        match (kind, effect) {
            (EntityKind::Actor, Effect::Given { from, to, .. }) => from == id || to == id,
            (
                EntityKind::Actor,
                Effect::Consumed { actor, .. }
                | Effect::AbilityUsed { actor, .. }
                | Effect::Learned { actor, .. }
                | Effect::Moved { actor, .. }
                | Effect::Discovered { actor, .. },
            ) => actor == id,
            (EntityKind::Actor, Effect::Said(claim)) => {
                &claim.speaker == id || claim.audience.contains(id)
            }
            (EntityKind::Actor, Effect::Believed(belief)) => &belief.believer == id,
            (EntityKind::Actor, Effect::Promised { commitment, .. }) => {
                &commitment.from == id || &commitment.to == id
            }
            (EntityKind::Item, Effect::Given { item, .. } | Effect::Consumed { item, .. }) => {
                item == id
            }
            (EntityKind::Location, Effect::Moved { from, to, .. }) => from == id || to == id,
            (
                EntityKind::Ability,
                Effect::AbilityUsed { ability, .. } | Effect::Learned { ability, .. },
            ) => ability == id,
            (EntityKind::Fact, Effect::Discovered { fact, .. }) => fact == id,
            (
                EntityKind::Commitment,
                Effect::Promised { id: promise, .. } | Effect::PromiseCompleted { id: promise, .. },
            ) => promise == id,
            _ => false,
        }
    }
}
#[derive(Clone, Debug)]
pub struct PrepareRequest {
    pub scope: Scope,
    pub expected_revision: u64,
    pub observer: String,
    pub from_exclusive: u64,
    pub through_revision: u64,
    pub target: Target,
}
impl PrepareRequest {
    fn key(&self) -> String {
        json!({"from_exclusive":self.from_exclusive,"target":self.target.json()}).to_string()
    }
}
/// Immutable, non-Deserialize native token; only actual Engine observations can construct one.
pub struct PreparedMemory {
    request: PrepareRequest,
    sources: Vec<(Scope, u64, String)>,
    packet: SummaryPacket,
}
impl PreparedMemory {
    #[cfg_attr(test, allow(dead_code))] // Fixture module does not expose Store authority.
    pub(crate) fn scope(&self) -> &Scope {
        &self.request.scope
    }
}
#[derive(Clone, Debug, PartialEq, Eq)]
pub struct SummaryPacket(Value);
impl SummaryPacket {
    pub fn json(&self) -> &Value {
        &self.0
    }
}
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum PublishOutcome {
    Published,
    Unchanged,
}
#[derive(Clone, Debug)]
pub struct SearchRequest {
    pub scope: Scope,
    pub expected_revision: u64,
    pub observer: String,
    pub text: String,
    pub limit: usize,
}
#[derive(Clone, Debug, PartialEq, Eq)]
pub struct SearchHit {
    pub packet: SummaryPacket,
}
fn valid_id(value: &str) -> bool {
    !value.is_empty()
        && value.len() <= 64
        && value
            .bytes()
            .all(|b| b.is_ascii_alphanumeric() || b"-_".contains(&b))
}
fn cancelled(cancel: &dyn Fn() -> bool) -> bool {
    std::panic::catch_unwind(std::panic::AssertUnwindSafe(cancel)).unwrap_or(true)
}
pub(crate) fn check(cancel: &dyn Fn() -> bool) -> Result<()> {
    if cancelled(cancel) {
        Err(MemoryError::Cancelled)
    } else {
        Ok(())
    }
}
fn revision(value: u64) -> Result<i64> {
    i64::try_from(value).map_err(|_| MemoryError::TooLarge)
}
fn validate_request(engine: &Engine, request: &PrepareRequest) -> Result<()> {
    if engine.domain_version() != 1 {
        return Err(MemoryError::Unsupported);
    }
    if &request.scope != engine.scope() {
        return Err(MemoryError::Scope);
    }
    if request.expected_revision != engine.revision()
        || request.through_revision != engine.revision()
    {
        return Err(MemoryError::Stale);
    }
    if !valid_id(&request.observer) || request.from_exclusive > request.through_revision {
        return Err(MemoryError::InvalidInput);
    }
    if matches!(&request.target,Target::Entity{id,..} if !valid_id(id)) {
        return Err(MemoryError::InvalidInput);
    }
    Ok(())
}

/// Uses the core's existing actor eligibility visitor; no witness/lineage predicate lives here.
pub(crate) fn prepare(
    engine: &Engine,
    request: &PrepareRequest,
    cancel: &dyn Fn() -> bool,
) -> Result<PreparedMemory> {
    check(cancel)?;
    validate_request(engine, request)?;
    // Range boundaries must themselves be known observations; probing a hidden or nonexistent
    // event yields the same fixed category. Do not use raw history to reveal hidden boundaries.
    if request.from_exclusive != 0 {
        let mut known = false;
        engine.visit_actor_observations(
            &request.observer,
            &request.scope,
            request.expected_revision,
            request.from_exclusive - 1,
            request.through_revision,
            &|| cancelled(cancel),
            &mut |event| {
                known = event.sequence() == request.from_exclusive;
                false
            },
        )?;
        if !known
            || !engine.receipts().iter().any(|r| {
                r.events()
                    .last()
                    .is_some_and(|e| e.sequence() == request.from_exclusive)
            })
        {
            return Err(MemoryError::InvalidInput);
        }
    }
    let mut sources = Vec::new();
    let mut entries = Vec::<Value>::new();
    let mut bytes = 0usize;
    let mut failure = None;
    engine.visit_actor_observations(&request.observer,&request.scope,request.expected_revision,
        request.from_exclusive,request.through_revision,&||cancelled(cancel),&mut|event|{
            let result=(||->Result<()>{
                check(cancel)?;
                if !request.target.includes(event.outcome()){return Ok(())}
                if sources.len()>=MAX_EVENTS{return Err(MemoryError::TooLarge)}
                let source=serde_json::to_string(event).map_err(|_|MemoryError::Integrity)?;
                bytes=bytes.checked_add(source.len()).ok_or(MemoryError::TooLarge)?;
                if bytes>MAX_SOURCE_BYTES{return Err(MemoryError::TooLarge)}
                sources.push((event.scope().clone(),event.sequence(),source));
                if let Effect::TimeAdvanced{from,to}=event.outcome(){
                    if let Some(last)=entries.last_mut(){
                        if last["class"]=="observed_time_span"&&last["to"].as_u64()==Some(*from){
                            last["to"]=json!(to);
                            last["source_events"].as_array_mut().unwrap().push(json!(event.sequence()));
                            return Ok(())
                        }
                    }
                    entries.push(json!({"class":"observed_time_span","from":from,"to":to,"source_events":[event.sequence()]}));
                }else{
                    let class=match event.outcome(){Effect::Said(_)=>"statement",Effect::Believed(_)=>"belief",_=>"canonical_observation"};
                    entries.push(json!({"class":class,"source_events":[event.sequence()],"outcome":event.outcome()}));
                }
                Ok(())
            })();
            if let Err(error)=result{failure=Some(error);false}else{true}
        })?;
    if let Some(error) = failure {
        return Err(error);
    }
    check(cancel)?;
    if sources.is_empty() {
        return Err(MemoryError::NotFound);
    }
    let packet = SummaryPacket(json!({"version":VERSION,"scope":request.scope,
        "observer":request.observer,"source_revision":request.expected_revision,
        "from_exclusive":request.from_exclusive,"through_revision":request.through_revision,
        "target":request.target.json(),"visibility":"actor_observations",
        "provenance":{"method":"deterministic-event-extractive-v1","model":null,"prompt":null},
        "source_events":sources.iter().map(|s|s.1).collect::<Vec<_>>(),"entries":entries}));
    if packet.0.to_string().len() > MAX_PACKET_BYTES {
        return Err(MemoryError::TooLarge);
    }
    Ok(PreparedMemory {
        request: request.clone(),
        sources,
        packet,
    })
}
fn head(connection: &Connection, scope: &Scope) -> Result<u64> {
    let value: Option<i64> = connection
        .query_row(
            "SELECT head_revision FROM branches WHERE story_id=?1 AND branch_id=?2",
            (&scope.story, &scope.branch),
            |r| r.get(0),
        )
        .optional()?;
    u64::try_from(value.ok_or(MemoryError::NotFound)?).map_err(|_| MemoryError::Integrity)
}
fn fence(
    connection: &Connection,
    prepared: &PreparedMemory,
    cancel: &dyn Fn() -> bool,
) -> Result<()> {
    check(cancel)?;
    if head(connection, &prepared.request.scope)? != prepared.request.expected_revision {
        return Err(MemoryError::Stale);
    }
    for (scope, sequence, expected) in &prepared.sources {
        check(cancel)?;
        let actual:Option<String>=connection.query_row("SELECT envelope_json FROM accepted_events WHERE story_id=?1 AND branch_id=?2 AND sequence=?3",params![scope.story,scope.branch,revision(*sequence)?],|r|r.get(0)).optional()?;
        if actual.as_ref() != Some(expected) {
            return Err(MemoryError::Integrity);
        }
    }
    Ok(())
}
/// Fixture-only adapter for the original isolated prototype tests. Production
/// Store publication uses publish_in_snapshot after normal strict replay.
#[cfg(test)]
#[allow(dead_code)] // Used only when this module is included by the prototype integration test.
pub(crate) fn publish(
    connection: &mut Connection,
    prepared: PreparedMemory,
    cancel: &dyn Fn() -> bool,
) -> Result<PublishOutcome> {
    check(cancel)?;
    let tx = connection.transaction_with_behavior(TransactionBehavior::Immediate)?;
    let outcome = publish_inner(&tx, prepared, cancel)?;
    tx.commit()?;
    Ok(outcome)
}
/// Store must load this Engine through normal strict replay in the SAME writer
/// transaction. Re-extraction compares all eligible sources, not just cached IDs.
#[cfg_attr(test, allow(dead_code))] // Included independently by the prototype integration test.
pub(crate) fn publish_in_snapshot(
    tx: &Connection,
    engine: &Engine,
    prepared: PreparedMemory,
    cancel: &dyn Fn() -> bool,
) -> Result<PublishOutcome> {
    let fresh = prepare(engine, &prepared.request, cancel)?;
    if fresh.sources != prepared.sources || fresh.packet != prepared.packet {
        return Err(MemoryError::Integrity);
    }
    publish_inner(tx, fresh, cancel)
}
fn publish_inner(
    tx: &Connection,
    prepared: PreparedMemory,
    cancel: &dyn Fn() -> bool,
) -> Result<PublishOutcome> {
    fence(tx, &prepared, cancel)?;
    let r = &prepared.request;
    let key = r.key();
    let packet = prepared.packet.0.to_string();
    let prior:Option<(i64,String)>=tx.query_row("SELECT source_revision,packet_json FROM derived_memory WHERE story_id=?1 AND branch_id=?2 AND observer_id=?3 AND cache_key=?4",params![r.scope.story,r.scope.branch,r.observer,key],|row|Ok((row.get(0)?,row.get(1)?))).optional()?;
    if prior.as_ref().is_some_and(|(basis, value)| {
        *basis == revision(r.expected_revision).unwrap_or(-1) && value == &packet
    }) {
        check(cancel)?;
        return Ok(PublishOutcome::Unchanged);
    }
    tx.execute("DELETE FROM derived_memory WHERE story_id=?1 AND branch_id=?2 AND observer_id=?3 AND source_revision<>?4",params![r.scope.story,r.scope.branch,r.observer,revision(r.expected_revision)?])?;
    let count: i64 = tx.query_row(
        "SELECT count(*) FROM derived_memory WHERE story_id=?1 AND branch_id=?2 AND observer_id=?3",
        params![r.scope.story, r.scope.branch, r.observer],
        |row| row.get(0),
    )?;
    if prior.is_none() && count >= MAX_PARTITION_PACKETS as i64 {
        return Err(MemoryError::TooLarge);
    }
    check(cancel)?;
    tx.execute("INSERT INTO derived_memory(story_id,branch_id,observer_id,cache_key,source_revision,summary_version,method,visibility,packet_json) VALUES(?1,?2,?3,?4,?5,1,'deterministic-event-extractive-v1','actor_observations',?6) ON CONFLICT(story_id,branch_id,observer_id,cache_key) DO UPDATE SET source_revision=excluded.source_revision,packet_json=excluded.packet_json",params![r.scope.story,r.scope.branch,r.observer,key,revision(r.expected_revision)?,packet])?;
    check(cancel)?;
    Ok(PublishOutcome::Published)
}
/// Rebuild against original accepted Engine observations; stored cache bytes are never authority.
pub(crate) fn read_in_snapshot(
    connection: &Connection,
    engine: &Engine,
    request: &PrepareRequest,
    cancel: &dyn Fn() -> bool,
) -> Result<SummaryPacket> {
    let prepared = prepare(engine, request, cancel)?;
    fence(connection, &prepared, cancel)?;
    let stored:Option<(i64,String)>=connection.query_row("SELECT source_revision,packet_json FROM derived_memory WHERE story_id=?1 AND branch_id=?2 AND observer_id=?3 AND cache_key=?4",params![request.scope.story,request.scope.branch,request.observer,request.key()],|r|Ok((r.get(0)?,r.get(1)?))).optional()?;
    let (basis, packet) = stored.ok_or(MemoryError::NotFound)?;
    if basis != revision(request.expected_revision)? {
        return Err(MemoryError::Stale);
    }
    let canonical_packet =
        serde_json::to_vec(&prepared.packet.0).map_err(|_| MemoryError::Integrity)?;
    if packet.as_bytes() != canonical_packet {
        return Err(MemoryError::Integrity);
    }
    check(cancel)?;
    Ok(prepared.packet)
}
/// Fixture-only transaction adapter. Store loads its Engine inside its own snapshot.
#[cfg(test)]
#[allow(dead_code)] // Used only by the prototype integration test's included module.
pub(crate) fn read(
    connection: &Connection,
    engine: &Engine,
    request: &PrepareRequest,
    cancel: &dyn Fn() -> bool,
) -> Result<SummaryPacket> {
    check(cancel)?;
    let tx = connection.unchecked_transaction()?;
    let packet = read_in_snapshot(&tx, engine, request, cancel)?;
    check(cancel)?;
    tx.commit()?;
    Ok(packet)
}
fn parse_request(
    value: &Value,
    scope: &Scope,
    observer: &str,
    head: u64,
) -> Result<PrepareRequest> {
    Ok(PrepareRequest {
        scope: scope.clone(),
        expected_revision: head,
        observer: observer.into(),
        from_exclusive: value["from_exclusive"]
            .as_u64()
            .ok_or(MemoryError::Integrity)?,
        through_revision: value["through_revision"]
            .as_u64()
            .ok_or(MemoryError::Integrity)?,
        target: Target::parse(&value["target"])?,
    })
}
/// No SQL/FTS grammar from the caller: every token is a quoted literal, with bound SQL values.
fn literal_query(text: &str) -> Result<Option<String>> {
    if text.len() > MAX_QUERY_BYTES || text.chars().any(char::is_control) {
        return Err(MemoryError::InvalidInput);
    }
    let terms = text
        .split(|c: char| !c.is_alphanumeric() && c != '_')
        .filter(|v| !v.is_empty())
        .collect::<Vec<_>>();
    if terms.len() > MAX_SEARCH_TERMS {
        return Err(MemoryError::InvalidInput);
    }
    Ok((!terms.is_empty()).then(|| {
        terms
            .iter()
            .map(|term| format!("\"{}\"", term.replace('"', "\"\"")))
            .collect::<Vec<_>>()
            .join(" AND ")
    }))
}
/// Fixture-only transaction adapter; production uses search_in_snapshot.
#[cfg(test)]
#[allow(dead_code)] // Used only by the prototype integration test's included module.
pub(crate) fn search(
    connection: &Connection,
    engine: &Engine,
    request: &SearchRequest,
    cancel: &dyn Fn() -> bool,
) -> Result<Vec<SearchHit>> {
    check(cancel)?;
    let tx = connection.unchecked_transaction()?;
    let hits = search_in_snapshot(&tx, engine, request, cancel)?;
    check(cancel)?;
    tx.commit()?;
    Ok(hits)
}
pub(crate) fn search_in_snapshot(
    connection: &Connection,
    engine: &Engine,
    request: &SearchRequest,
    cancel: &dyn Fn() -> bool,
) -> Result<Vec<SearchHit>> {
    check(cancel)?;
    if request.limit == 0 || request.limit > MAX_HITS {
        return Err(MemoryError::InvalidInput);
    }
    let basis = PrepareRequest {
        scope: request.scope.clone(),
        expected_revision: request.expected_revision,
        observer: request.observer.clone(),
        from_exclusive: 0,
        through_revision: request.expected_revision,
        target: Target::SceneWindow,
    };
    validate_request(engine, &basis)?;
    if !engine.state().actors.contains_key(&request.observer) {
        return Err(MemoryError::NotFound);
    }
    if head(connection, &request.scope)? != request.expected_revision {
        return Err(MemoryError::Stale);
    }
    let expression = literal_query(&request.text)?;
    // Scope/observer/revision partition BEFORE reading text, validating, materializing or FTS.
    let mut query=connection.prepare("SELECT cache_key,packet_json FROM derived_memory WHERE story_id=?1 AND branch_id=?2 AND observer_id=?3 AND source_revision=?4 ORDER BY cache_key LIMIT ?5")?;
    let mut rows = query.query(params![
        request.scope.story,
        request.scope.branch,
        request.observer,
        revision(request.expected_revision)?,
        (MAX_PARTITION_PACKETS + 1) as i64
    ])?;
    let mut packets = Vec::new();
    while let Some(row) = rows.next()? {
        check(cancel)?;
        if packets.len() >= MAX_PARTITION_PACKETS {
            return Err(MemoryError::TooLarge);
        }
        let key: String = row.get(0)?;
        let raw: String = row.get(1)?;
        if raw.len() > MAX_PACKET_BYTES {
            return Err(MemoryError::Integrity);
        }
        let value: Value = serde_json::from_str(&raw).map_err(|_| MemoryError::Integrity)?;
        let request = parse_request(
            &value,
            &request.scope,
            &request.observer,
            request.expected_revision,
        )?;
        if request.key() != key {
            return Err(MemoryError::Integrity);
        }
        packets.push(read_in_snapshot(connection, engine, &request, cancel)?);
    }
    drop(rows);
    drop(query);
    check(cancel)?;
    // The only FTS corpus is this already verified partition on the SAME owner connection.
    // No global index frequency/rank, hidden corpus, snippet, or external rowid is exposed.
    connection.execute_batch("DROP TABLE IF EXISTS temp.derived_memory_search; CREATE VIRTUAL TABLE temp.derived_memory_search USING fts5(body);")?;
    let result = (|| -> Result<Vec<SearchHit>> {
        for packet in &packets {
            check(cancel)?;
            connection.execute(
                "INSERT INTO temp.derived_memory_search(body) VALUES(?1)",
                [packet.0.to_string()],
            )?;
        }
        let Some(expression) = expression else {
            return Ok(vec![]);
        };
        let mut query=connection.prepare("SELECT rowid FROM temp.derived_memory_search WHERE derived_memory_search MATCH ?1 ORDER BY rowid LIMIT ?2")?;
        let mut rows = query.query(params![expression, request.limit as i64])?;
        let mut hits = Vec::new();
        while let Some(row) = rows.next()? {
            check(cancel)?;
            let index: i64 = row.get(0)?;
            let packet = usize::try_from(index - 1)
                .ok()
                .and_then(|i| packets.get(i))
                .ok_or(MemoryError::Integrity)?;
            hits.push(SearchHit {
                packet: packet.clone(),
            });
        }
        Ok(hits)
    })();
    let cleanup = connection.execute_batch("DROP TABLE temp.derived_memory_search");
    match result {
        Err(error) => Err(error),
        Ok(hits) => {
            cleanup?;
            check(cancel)?;
            Ok(hits)
        }
    }
}
/// Fixture-only transaction adapter; production loads strict Engine in its writer.
#[cfg(test)]
#[allow(dead_code)] // Used only by the prototype integration test's included module.
pub(crate) fn invalidate(
    connection: &mut Connection,
    scope: &Scope,
    observer: &str,
    expected_revision: u64,
    cancel: &dyn Fn() -> bool,
) -> Result<()> {
    check(cancel)?;
    let tx = connection.transaction_with_behavior(TransactionBehavior::Immediate)?;
    invalidate_in_snapshot(&tx, scope, observer, expected_revision, cancel)?;
    tx.commit()?;
    Ok(())
}
pub(crate) fn invalidate_in_snapshot(
    connection: &Connection,
    scope: &Scope,
    observer: &str,
    expected_revision: u64,
    cancel: &dyn Fn() -> bool,
) -> Result<()> {
    check(cancel)?;
    if !valid_id(observer) {
        return Err(MemoryError::InvalidInput);
    }
    if head(connection, scope)? != expected_revision {
        return Err(MemoryError::Stale);
    }
    connection.execute(
        "DELETE FROM derived_memory WHERE story_id=?1 AND branch_id=?2 AND observer_id=?3",
        params![scope.story, scope.branch, observer],
    )?;
    check(cancel)?;
    Ok(())
}
