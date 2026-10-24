//! Pure, actor-filtered deterministic coverage v2. No database, inference or canon writes.
//! Packets are untrusted cache data. Only rebuilding against the actual Engine verifies them.
use crate::{contracts::*, engine::Engine};
use serde::{Deserialize, Serialize};
use sha2::{Digest, Sha256};
use std::io::{self, Write};

pub const PACKET_VERSION: u16 = 2;
pub const METHOD: &str = "deterministic-event-extractive-v2";
pub const MAX_RECEIPTS: usize = 128;
pub const MAX_EVENTS: usize = 256;
pub const MAX_SOURCE_BYTES: usize = 1_048_576;
pub const MAX_PACKET_BYTES: usize = 65_536;
pub const MAX_PACKETS: usize = 32;
// Reserve room for the longer closure/proof marker after rejecting the next turn.
const CLOSURE_RESERVE: usize = 64;

#[derive(Clone, Copy, Debug, PartialEq, Eq)]
pub enum CoverageError {
    Cancelled,
    Scope,
    Stale,
    Observer,
    Boundary,
    /// A single complete turn cannot be represented. No packet/progress is returned.
    Budget,
    Source,
    Unsupported,
}
#[derive(Clone, Copy, Debug, PartialEq, Eq)]
pub enum FallbackReason {
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
type Result<T> = std::result::Result<T, CoverageError>;

#[derive(Clone, Debug)]
pub struct CoverageRequest {
    pub scope: Scope,
    pub expected_head: u64,
    pub observer: String,
}
#[derive(Clone, Debug)]
pub struct ChunkRequest {
    pub scope: Scope,
    pub expected_head: u64,
    pub observer: String,
    pub from_exclusive: u64,
}
impl ChunkRequest {
    fn coverage(&self) -> CoverageRequest {
        CoverageRequest {
            scope: self.scope.clone(),
            expected_head: self.expected_head,
            observer: self.observer.clone(),
        }
    }
}
#[derive(Clone, Debug, PartialEq, Eq, Serialize, Deserialize)]
#[serde(deny_unknown_fields)]
pub struct SourceRef {
    pub scope: Scope,
    pub sequence: u64,
}
#[derive(Clone, Debug, PartialEq, Eq, Serialize, Deserialize)]
#[serde(tag = "kind", rename_all = "snake_case", deny_unknown_fields)]
pub enum Closure {
    OpenTail,
    ReceiptLimit,
    EventLimit,
    EventBudget { next_turn_end: u64 },
    SourceBudget { next_turn_end: u64 },
    PacketBudget { next_turn_end: u64 },
}
impl Closure {
    pub fn is_sealed(&self) -> bool {
        !matches!(self, Self::OpenTail)
    }
    fn lookahead(&self) -> Option<u64> {
        match self {
            Self::EventBudget { next_turn_end }
            | Self::SourceBudget { next_turn_end }
            | Self::PacketBudget { next_turn_end } => Some(*next_turn_end),
            _ => None,
        }
    }
}
#[derive(Clone, Copy, Debug, PartialEq, Eq, Serialize)]
#[serde(rename_all = "snake_case")]
pub enum ObservationClass {
    CanonicalObservation,
    Statement,
    Belief,
}
#[derive(Clone, Debug, PartialEq, Eq, Serialize)]
#[serde(tag = "class", rename_all = "snake_case")]
pub enum Entry {
    ObservedTimeSpan {
        from: u64,
        to: u64,
        source_events: Vec<SourceRef>,
    },
    Observation {
        origin: ObservationClass,
        source: SourceRef,
        event: Box<AcceptedEvent>,
    },
}
/// Serialize-only extractive representation, never an accepted canonical value.
#[derive(Clone, Debug, PartialEq, Eq, Serialize)]
pub struct TypedPacket {
    pub version: u16,
    pub method: String,
    pub scope: Scope,
    pub observer: String,
    pub seed_sha256: String,
    pub lineage_sha256: String,
    pub from_exclusive: u64,
    pub through_revision: u64,
    pub receipt_count: usize,
    pub closure: Closure,
    pub source_events: Vec<SourceRef>,
    pub source_sha256: String,
    pub entries: Vec<Entry>,
}
impl TypedPacket {
    pub fn bytes(&self) -> Result<Vec<u8>> {
        if self.source_events.len() > MAX_EVENTS
            || self.entries.len() > MAX_EVENTS
            || self.receipt_count > MAX_RECEIPTS
        {
            return Err(CoverageError::Budget);
        }
        encode_limited(self, MAX_PACKET_BYTES)
    }
}
/// These bytes have been rebuilt from one Engine. Before a compiler uses a retained value,
/// call recheck against its actual Engine, even if scope/head strings happen to match.
/// No Deserialize, public construction, provider, SQL or accepted-state mutation authority.
pub struct VerifiedCoverage {
    request: CoverageRequest,
    packets: Vec<TypedPacket>,
    through: u64,
}
impl VerifiedCoverage {
    pub fn packets(&self) -> &[TypedPacket] {
        &self.packets
    }
    pub fn covered_through(&self) -> u64 {
        self.through
    }
    /// The exact raw fallback/delta is (raw_delta_after, actual compiler head].
    pub fn raw_delta_after(&self) -> u64 {
        self.through
    }
    pub fn verified_head(&self) -> u64 {
        self.request.expected_head
    }
    pub fn recheck(
        &self,
        engine: &Engine,
        request: &CoverageRequest,
        cancel: &dyn Fn() -> bool,
    ) -> Result<CoverageRead> {
        check(cancel)?;
        if engine.domain_version() != 1 {
            return verify_coverage(engine, request, &[], cancel);
        }
        let bytes = self
            .packets
            .iter()
            .map(TypedPacket::bytes)
            .collect::<Result<Vec<_>>>()?;
        let borrowed = bytes.iter().map(Vec::as_slice).collect::<Vec<_>>();
        verify_coverage(engine, request, &borrowed, cancel)
    }
}
pub enum CoverageRead {
    Verified(VerifiedCoverage),
    /// Reject the entire supplied cache set; use exact raw observations from zero.
    RawFallback(FallbackReason),
}
fn check(cancel: &dyn Fn() -> bool) -> Result<()> {
    if std::panic::catch_unwind(std::panic::AssertUnwindSafe(cancel)).unwrap_or(true) {
        Err(CoverageError::Cancelled)
    } else {
        Ok(())
    }
}
struct LimitedWriter {
    bytes: Vec<u8>,
    limit: usize,
    exceeded: bool,
}
impl Write for LimitedWriter {
    fn write(&mut self, bytes: &[u8]) -> io::Result<usize> {
        if self
            .bytes
            .len()
            .checked_add(bytes.len())
            .is_none_or(|size| size > self.limit)
        {
            self.exceeded = true;
            return Err(io::Error::other("bounded memory encoding"));
        }
        self.bytes.extend_from_slice(bytes);
        Ok(bytes.len())
    }
    fn flush(&mut self) -> io::Result<()> {
        Ok(())
    }
}
fn encode_limited(value: &impl Serialize, limit: usize) -> Result<Vec<u8>> {
    let mut writer = LimitedWriter {
        bytes: vec![],
        limit,
        exceeded: false,
    };
    if serde_json::to_writer(&mut writer, value).is_err() {
        return Err(if writer.exceeded {
            CoverageError::Budget
        } else {
            CoverageError::Source
        });
    }
    Ok(writer.bytes)
}
struct HashWriter(Sha256);
impl Write for HashWriter {
    fn write(&mut self, bytes: &[u8]) -> io::Result<usize> {
        self.0.update(bytes);
        Ok(bytes.len())
    }
    fn flush(&mut self) -> io::Result<()> {
        Ok(())
    }
}
fn hash_value(value: &impl Serialize) -> Result<String> {
    let mut writer = HashWriter(Sha256::new());
    serde_json::to_writer(&mut writer, value).map_err(|_| CoverageError::Source)?;
    Ok(format!("{:x}", writer.0.finalize()))
}
fn validate_binding(
    engine: &Engine,
    request: &CoverageRequest,
    cancel: &dyn Fn() -> bool,
) -> Result<()> {
    check(cancel)?;
    if request.scope != *engine.scope() {
        return Err(CoverageError::Scope);
    }
    if request.expected_head != engine.revision() {
        return Err(CoverageError::Stale);
    }
    if !engine.state().actors.contains_key(&request.observer) {
        return Err(CoverageError::Observer);
    }
    Ok(())
}
fn binding(
    engine: &Engine,
    request: &CoverageRequest,
    cancel: &dyn Fn() -> bool,
) -> Result<(String, String)> {
    validate_binding(engine, request, cancel)?;
    if engine.domain_version() != 1 {
        return Err(CoverageError::Unsupported);
    }
    let seed = hash_value(engine.seed())?;
    let lineage = hash_value(
        &engine
            .memory_lineage_binding()
            .map_err(|_| CoverageError::Source)?,
    )?;
    check(cancel)?;
    Ok((seed, lineage))
}
fn boundary(engine: &Engine, revision: u64) -> bool {
    revision == 0
        || engine
            .receipts()
            .iter()
            .any(|r| r.events().last().is_some_and(|e| e.sequence() == revision))
}
struct Builder {
    packet: TypedPacket,
    digest: Sha256,
    source_bytes: usize,
    packet_limit: usize,
    done: bool,
    error: Option<CoverageError>,
}
impl Builder {
    fn reject(&mut self, closure: Closure) {
        if self.packet.receipt_count == 0 {
            self.error = Some(CoverageError::Budget);
        } else {
            self.packet.closure = closure;
        }
        self.done = true;
    }
    fn receipt(&mut self, end: u64, events: &[(AcceptedEvent, Vec<u8>)]) -> Result<()> {
        if self.done {
            return Ok(());
        }
        if self.packet.source_events.len() + events.len() > MAX_EVENTS {
            self.reject(Closure::EventBudget { next_turn_end: end });
            return Ok(());
        }
        let source_bytes =
            self.source_bytes + events.iter().map(|(_, bytes)| bytes.len()).sum::<usize>();
        if source_bytes > MAX_SOURCE_BYTES {
            self.reject(Closure::SourceBudget { next_turn_end: end });
            return Ok(());
        }
        let mut candidate = self.packet.clone();
        let mut digest = self.digest.clone();
        for (event, bytes) in events {
            let source = SourceRef {
                scope: event.scope().clone(),
                sequence: event.sequence(),
            };
            digest.update((bytes.len() as u64).to_le_bytes());
            digest.update(bytes);
            candidate.source_events.push(source.clone());
            if let Effect::TimeAdvanced { from, to } = event.outcome() {
                if let Some(Entry::ObservedTimeSpan {
                    to: last,
                    source_events,
                    ..
                }) = candidate.entries.last_mut()
                {
                    if last == from {
                        *last = *to;
                        source_events.push(source);
                        continue;
                    }
                }
                candidate.entries.push(Entry::ObservedTimeSpan {
                    from: *from,
                    to: *to,
                    source_events: vec![source],
                });
            } else {
                candidate.entries.push(Entry::Observation {
                    origin: match event.outcome() {
                        Effect::Said(_) => ObservationClass::Statement,
                        Effect::Believed(_) => ObservationClass::Belief,
                        _ => ObservationClass::CanonicalObservation,
                    },
                    source,
                    event: Box::new(event.clone()),
                });
            }
        }
        candidate.through_revision = end;
        candidate.receipt_count += 1;
        let mut final_digest = digest.clone();
        final_digest.update(end.to_le_bytes());
        candidate.source_sha256 = format!("{:x}", final_digest.finalize());
        match encode_limited(
            &candidate,
            self.packet_limit.saturating_sub(CLOSURE_RESERVE),
        ) {
            Ok(_) => {}
            Err(CoverageError::Budget) => {
                self.reject(Closure::PacketBudget { next_turn_end: end });
                return Ok(());
            }
            Err(error) => return Err(error),
        }
        self.packet = candidate;
        self.digest = digest;
        self.source_bytes = source_bytes;
        if self.packet.receipt_count == MAX_RECEIPTS {
            self.packet.closure = Closure::ReceiptLimit;
            self.done = true;
        } else if self.packet.source_events.len() == MAX_EVENTS {
            self.packet.closure = Closure::EventLimit;
            self.done = true;
        }
        Ok(())
    }
}
/// Build the maximal deterministic first chunk after one completed boundary.
/// Only the shared actor visitor reaches event content. One pass includes at most one
/// rejected complete-turn lookahead; the cursor never advances into that rejected turn.
pub fn build_chunk(
    engine: &Engine,
    request: &ChunkRequest,
    cancel: &dyn Fn() -> bool,
) -> Result<Option<TypedPacket>> {
    build_with_packet_limit(engine, request, cancel, MAX_PACKET_BYTES)
}
// Private implementation parameter permits a stricter cfg(test) failure proof on the
// SAME real builder. Public callers always get the fixed production policy above.
fn build_with_packet_limit(
    engine: &Engine,
    request: &ChunkRequest,
    cancel: &dyn Fn() -> bool,
    packet_limit: usize,
) -> Result<Option<TypedPacket>> {
    let (seed_sha256, lineage_sha256) = binding(engine, &request.coverage(), cancel)?;
    if request.from_exclusive > engine.revision() || !boundary(engine, request.from_exclusive) {
        return Err(CoverageError::Boundary);
    }
    if request.from_exclusive == engine.revision() {
        return Ok(None);
    }
    let ends = engine
        .receipts()
        .iter()
        .filter_map(|r| r.events().last().map(AcceptedEvent::sequence))
        .filter(|end| *end > request.from_exclusive)
        .take(MAX_RECEIPTS + 1)
        .collect::<Vec<_>>();
    let through = *ends.last().ok_or(CoverageError::Source)?;
    let packet = TypedPacket {
        version: PACKET_VERSION,
        method: METHOD.into(),
        scope: request.scope.clone(),
        observer: request.observer.clone(),
        seed_sha256,
        lineage_sha256,
        from_exclusive: request.from_exclusive,
        through_revision: request.from_exclusive,
        receipt_count: 0,
        closure: Closure::OpenTail,
        source_events: vec![],
        source_sha256: "0".repeat(64),
        entries: vec![],
    };
    let mut digest = Sha256::new();
    digest.update(b"locallore-memory-coverage-v2\0");
    let domain = serde_json::to_vec(&(
        &packet.scope,
        &packet.observer,
        &packet.seed_sha256,
        &packet.lineage_sha256,
        packet.from_exclusive,
    ))
    .map_err(|_| CoverageError::Source)?;
    digest.update((domain.len() as u64).to_le_bytes());
    digest.update(domain);
    let mut b = Builder {
        packet,
        digest,
        source_bytes: 0,
        packet_limit,
        done: false,
        error: None,
    };
    let mut index = 0usize;
    let mut pending = Vec::<(AcceptedEvent, Vec<u8>)>::new();
    let mut pending_bytes = 0usize;
    engine
        .visit_actor_observations(
            &request.observer,
            &request.scope,
            request.expected_head,
            request.from_exclusive,
            through,
            &|| check(cancel).is_err(),
            &mut |event| {
                let result = (|| -> Result<()> {
                    check(cancel)?;
                    while !b.done && index < ends.len() && ends[index] < event.sequence() {
                        b.receipt(ends[index], &pending)?;
                        pending.clear();
                        pending_bytes = 0;
                        index += 1;
                    }
                    if b.done {
                        return Ok(());
                    }
                    let end = *ends.get(index).ok_or(CoverageError::Source)?;
                    // Bound copies while still in a single complete turn; the rejected turn is
                    // never partially represented. Eligibility ran before this serialization.
                    if b.packet.source_events.len() + pending.len() + 1 > MAX_EVENTS {
                        b.reject(Closure::EventBudget { next_turn_end: end });
                    } else {
                        match encode_limited(
                            event,
                            MAX_SOURCE_BYTES - b.source_bytes - pending_bytes,
                        ) {
                            Ok(bytes) => {
                                pending_bytes += bytes.len();
                                pending.push((event.clone(), bytes));
                            }
                            Err(CoverageError::Budget) => {
                                b.reject(Closure::SourceBudget { next_turn_end: end })
                            }
                            Err(error) => return Err(error),
                        }
                    }
                    Ok(())
                })();
                if let Err(error) = result {
                    b.error = Some(error);
                    b.done = true;
                }
                !b.done
            },
        )
        .map_err(|e| {
            if e == Error::Cancelled {
                CoverageError::Cancelled
            } else {
                CoverageError::Source
            }
        })?;
    while !b.done && index < ends.len() {
        check(cancel)?;
        b.receipt(ends[index], &pending)?;
        pending.clear();
        index += 1;
    }
    check(cancel)?;
    if let Some(error) = b.error {
        return Err(error);
    }
    b.packet.bytes()?;
    Ok(Some(b.packet))
}

// Header parsing is structural only; Effect/AcceptedEvent are never deserialized as authority.
// Entire unique JSON must equal the independently rebuilt Serialize-only packet.
#[derive(Deserialize)]
#[serde(deny_unknown_fields)]
struct Wire {
    version: u16,
    method: String,
    scope: Scope,
    observer: String,
    seed_sha256: String,
    lineage_sha256: String,
    from_exclusive: u64,
    through_revision: u64,
    receipt_count: usize,
    closure: Closure,
    source_events: Vec<SourceRef>,
    source_sha256: String,
    entries: Vec<serde_json::Value>,
}
/// Verify a contiguous prefix from zero; a gap/invalid set falls back entirely to exact raw.
/// A valid old open tail is rebuilt at its historical end, then the exact delta stays raw.
pub fn verify_coverage(
    engine: &Engine,
    request: &CoverageRequest,
    packets: &[&[u8]],
    cancel: &dyn Fn() -> bool,
) -> Result<CoverageRead> {
    validate_binding(engine, request, cancel)?;
    if engine.domain_version() != 1 {
        return Ok(CoverageRead::RawFallback(FallbackReason::Unsupported));
    }
    let (seed, lineage) = binding(engine, request, cancel)?;
    if packets.is_empty() {
        return Ok(CoverageRead::RawFallback(FallbackReason::Missing));
    }
    if packets.len() > MAX_PACKETS {
        return Ok(CoverageRead::RawFallback(FallbackReason::Budget));
    }
    let mut verified = Vec::new();
    let mut through = 0;
    for (index, bytes) in packets.iter().enumerate() {
        check(cancel)?;
        if bytes.len() > MAX_PACKET_BYTES {
            return Ok(CoverageRead::RawFallback(FallbackReason::Budget));
        }
        let Ok(value) = crate::engine::parse_unique_json(bytes, MAX_PACKET_BYTES) else {
            return Ok(CoverageRead::RawFallback(FallbackReason::Malformed));
        };
        let Ok(wire) = serde_json::from_value::<Wire>(value.clone()) else {
            return Ok(CoverageRead::RawFallback(FallbackReason::Malformed));
        };
        if wire.version != PACKET_VERSION || wire.method != METHOD {
            return Ok(CoverageRead::RawFallback(FallbackReason::Unsupported));
        }
        if wire.scope != request.scope
            || wire.observer != request.observer
            || wire.seed_sha256 != seed
            || wire.lineage_sha256 != lineage
        {
            return Ok(CoverageRead::RawFallback(FallbackReason::Binding));
        }
        if wire.from_exclusive > through {
            return Ok(CoverageRead::RawFallback(FallbackReason::Gap));
        }
        if wire.from_exclusive < through {
            return Ok(CoverageRead::RawFallback(FallbackReason::Overlap));
        }
        if wire.through_revision <= through
            || wire.through_revision > engine.revision()
            || !boundary(engine, wire.through_revision)
        {
            return Ok(CoverageRead::RawFallback(FallbackReason::SourceMismatch));
        }
        if wire.receipt_count > MAX_RECEIPTS
            || wire.source_events.len() > MAX_EVENTS
            || wire.entries.len() > MAX_EVENTS
            || wire.source_sha256.len() != 64
        {
            return Ok(CoverageRead::RawFallback(FallbackReason::Budget));
        }
        let historical;
        let basis = if matches!(wire.closure, Closure::OpenTail) {
            if index + 1 != packets.len() {
                return Ok(CoverageRead::RawFallback(FallbackReason::OpenTailBeforeEnd));
            }
            historical = engine
                .at_revision(wire.through_revision)
                .map_err(|_| CoverageError::Source)?;
            &historical
        } else {
            if wire
                .closure
                .lookahead()
                .is_some_and(|next| next > engine.revision())
            {
                return Ok(CoverageRead::RawFallback(FallbackReason::UnprovableClosure));
            }
            engine
        };
        let chunk = ChunkRequest {
            scope: request.scope.clone(),
            expected_head: basis.revision(),
            observer: request.observer.clone(),
            from_exclusive: through,
        };
        let rebuilt = match build_chunk(basis, &chunk, cancel) {
            Ok(Some(packet)) => packet,
            Ok(None) | Err(CoverageError::Budget) => {
                return Ok(CoverageRead::RawFallback(FallbackReason::SourceMismatch))
            }
            Err(error) => return Err(error),
        };
        if serde_json::to_value(&rebuilt).map_err(|_| CoverageError::Source)? != value {
            return Ok(CoverageRead::RawFallback(FallbackReason::SourceMismatch));
        }
        through = rebuilt.through_revision;
        verified.push(rebuilt);
    }
    check(cancel)?;
    Ok(CoverageRead::Verified(VerifiedCoverage {
        request: request.clone(),
        packets: verified,
        through,
    }))
}

#[cfg(test)]
mod tests {
    use super::*;
    #[test]
    fn reduced_private_budget_rejects_one_real_complete_turn_without_progress() {
        let seed: Seed =
            serde_json::from_str(include_str!("../../../fixtures/lantern_quay.json")).unwrap();
        let mut engine = Engine::new(seed).unwrap();
        let request = engine.request("one", Intent::Actions(vec![Command::Wait { ticks: 1 }]));
        let proposal = Engine::proposal(&request).unwrap();
        let narration = engine
            .preview(&request, &proposal)
            .unwrap()
            .narration()
            .to_owned();
        engine.commit(&request, &proposal, &narration).unwrap();
        let before = engine.canonical_bytes();
        let request = ChunkRequest {
            scope: engine.scope().clone(),
            expected_head: 1,
            observer: "player".into(),
            from_exclusive: 0,
        };
        assert_eq!(
            build_with_packet_limit(&engine, &request, &|| false, 256),
            Err(CoverageError::Budget)
        );
        assert_eq!(before, engine.canonical_bytes());
        assert!(build_chunk(&engine, &request, &|| false).unwrap().is_some());
    }
}
