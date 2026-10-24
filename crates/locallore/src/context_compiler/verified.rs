//! Pure Rust input port, not a Host command or an inspection/knowledge grant.
//! Verification currently rebuilds packets; no performance improvement is claimed.
use super::*;
use crate::memory_coverage::{
    CoverageError, CoverageRead, CoverageRequest, Entry, FallbackReason, VerifiedCoverage,
};

#[derive(Clone, Copy, Debug, PartialEq, Eq, Serialize)]
#[serde(rename_all = "snake_case")]
pub enum CoverageMode {
    Raw,
    Verified,
}
#[derive(Clone, Copy, Debug, PartialEq, Eq, Serialize)]
#[serde(rename_all = "snake_case")]
pub enum MemoryFallbackReason {
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
impl From<FallbackReason> for MemoryFallbackReason {
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
/// Closed, count-only construction diagnostics, outside ContextPackage/token budget.
/// Counts describe FINAL event candidates, not reads performed by proof rebuilding,
/// selected rows, cache hits in a database, model use, or elapsed work avoided.
#[derive(Clone, Debug, PartialEq, Eq, Serialize)]
pub struct CoverageDiagnostics {
    pub mode: CoverageMode,
    pub set_fallback_reason: Option<MemoryFallbackReason>,
    pub packets_used: usize,
    pub packets_fell_back: usize,
    pub timespan_fallback_packets: usize,
    pub mandatory_fallback_packets: usize,
    pub covered_through: u64,
    pub raw_delta_after: u64,
    pub cached_event_candidates: usize,
    pub raw_event_candidates: usize,
}
#[derive(Clone, Debug, PartialEq, Eq, Serialize)]
pub struct MemoryCompilation {
    pub package: ContextPackage,
    pub coverage: CoverageDiagnostics,
}

/// The same compiler and budgets with an optional retained opaque coverage proof.
/// Always rechecks against its ACTUAL selected Engine snapshot. Callers cannot
/// deserialize a proof, grant inspector access, or supply arbitrary cache rows.
pub fn compile_verified_cancelled(
    engine: &Engine,
    request: &CompileRequest,
    coverage: Option<&VerifiedCoverage>,
    cancel: &dyn Fn() -> bool,
) -> Result<MemoryCompilation, CompileError> {
    compile_inner(
        engine,
        request,
        Input::Verified(coverage),
        policy::Construction::Legacy,
        cancel,
    )
    .map(|result| result.compilation)
}

pub(super) enum Input<'a> {
    Legacy,
    Verified(Option<&'a VerifiedCoverage>),
}
type EventKey = (Scope, u64);
struct PacketSource {
    after: u64,
    through: u64,
    sources: BTreeSet<EventKey>,
    cached: bool,
}
pub(super) struct ObservationInput {
    pub(super) diagnostics: CoverageDiagnostics,
    packets: Vec<PacketSource>,
}
impl ObservationInput {
    fn raw(reason: MemoryFallbackReason, rejected: usize) -> Self {
        Self {
            diagnostics: CoverageDiagnostics {
                mode: CoverageMode::Raw,
                set_fallback_reason: Some(reason),
                packets_used: 0,
                packets_fell_back: rejected,
                timespan_fallback_packets: 0,
                mandatory_fallback_packets: 0,
                covered_through: 0,
                raw_delta_after: 0,
                cached_event_candidates: 0,
                raw_event_candidates: 0,
            },
            packets: vec![],
        }
    }

    pub(super) fn replace_mandatory(
        &mut self,
        engine: &Engine,
        request: &CompileRequest,
        candidates: &mut [Candidate],
        mandatory: &BTreeMap<String, Reason>,
        cancel: &dyn Fn() -> bool,
    ) -> Result<(), CompileError> {
        let required: BTreeSet<_> = candidates
            .iter()
            .filter(|c| mandatory.contains_key(c.key()))
            .filter_map(|c| c.row().and_then(event_key))
            .collect();
        for packet in &mut self.packets {
            check(cancel)?;
            if !packet.cached || packet.sources.is_disjoint(&required) {
                continue;
            }
            // Actually revisit the Engine for this whole packet. Never relabel
            // cached payloads as raw, expand a time span, or refetch only one row.
            let mut actual = BTreeMap::new();
            visit_events(
                engine,
                &request.observer,
                packet.after,
                packet.through,
                request.version,
                cancel,
                &mut |event| {
                    check(cancel)?;
                    let key = (event.scope().clone(), event.sequence());
                    let row = event_row(event)?;
                    let encoded = serde_json::to_string(&row).map_err(|_| CompileError::Source)?;
                    if actual.insert(key, (row, encoded)).is_some() {
                        return Err(CompileError::Source);
                    }
                    Ok(())
                },
            )?;
            if actual.keys().cloned().collect::<BTreeSet<_>>() != packet.sources {
                return Err(CompileError::Source);
            }
            for candidate in &mut *candidates {
                check(cancel)?;
                let Some(key) = candidate.row().and_then(event_key) else {
                    continue;
                };
                if let Some((row, encoded)) = actual.remove(&key) {
                    *candidate =
                        Candidate::from_row(row, encoded, engine.revision(), request.version);
                }
            }
            if !actual.is_empty() {
                return Err(CompileError::Source);
            }
            packet.cached = false;
            self.diagnostics.packets_used -= 1;
            self.diagnostics.packets_fell_back += 1;
            self.diagnostics.mandatory_fallback_packets += 1;
            self.diagnostics.cached_event_candidates -= packet.sources.len();
            self.diagnostics.raw_event_candidates += packet.sources.len();
        }
        Ok(())
    }
}
fn event_key(row: &Row) -> Option<EventKey> {
    match row {
        Row::Event { event, .. } => Some((event.scope.clone(), event.sequence)),
        _ => None,
    }
}

// Keep the bounded visitor inputs explicit; construction selects the same shared
// raw candidate path without adding a second compiler or mutable context object.
#[allow(clippy::too_many_arguments)]
fn append_raw(
    engine: &Engine,
    observer: &str,
    range: (u64, u64),
    version: u16,
    rows: &mut Vec<(Row, String)>,
    bytes: &mut usize,
    seen: &mut BTreeSet<EventKey>,
    cancel: &dyn Fn() -> bool,
) -> Result<usize, CompileError> {
    let mut count = 0;
    visit_events(
        engine,
        observer,
        range.0,
        range.1,
        version,
        cancel,
        &mut |event| {
            check(cancel)?;
            if rows.len() >= MAX_CANDIDATES {
                return Err(CompileError::TooLarge);
            }
            if !seen.insert((event.scope().clone(), event.sequence())) {
                return Err(CompileError::Source);
            }
            push_row(rows, bytes, event_row(event)?, cancel)?;
            count += 1;
            Ok(())
        },
    )?;
    Ok(count)
}

pub(super) fn collect(
    engine: &Engine,
    request: &CompileRequest,
    input: Input<'_>,
    construction: policy::Construction,
    rows: &mut Vec<(Row, String)>,
    bytes: &mut usize,
    cancel: &dyn Fn() -> bool,
) -> Result<ObservationInput, CompileError> {
    if construction.is_current() && (engine.domain_version() != 1 || construction.is_recent()) {
        // Old event-only packets cannot represent authored observations or player
        // transcript messages. Refuse before inspecting/rechecking/hashing proof.
        let mut state = ObservationInput::raw(MemoryFallbackReason::Unsupported, 0);
        let mut seen = BTreeSet::new();
        state.diagnostics.raw_event_candidates = append_raw(
            engine,
            &request.observer,
            (0, engine.revision()),
            2,
            rows,
            bytes,
            &mut seen,
            cancel,
        )?;
        return Ok(state);
    }
    let mut state = ObservationInput::raw(MemoryFallbackReason::Missing, 0);
    let proof = match input {
        Input::Legacy | Input::Verified(None) => None,
        Input::Verified(Some(supplied)) => {
            let binding = CoverageRequest {
                scope: engine.scope().clone(),
                expected_head: engine.revision(),
                observer: request.observer.clone(),
            };
            match supplied.recheck(engine, &binding, cancel) {
                Ok(CoverageRead::Verified(proof)) => Some(proof),
                Ok(CoverageRead::RawFallback(reason)) => {
                    state = ObservationInput::raw(reason.into(), supplied.packets().len());
                    None
                }
                Err(CoverageError::Cancelled) => return Err(CompileError::Cancelled),
                Err(CoverageError::Source) => return Err(CompileError::Source),
                Err(error) => {
                    let reason = match error {
                        CoverageError::Budget => MemoryFallbackReason::Budget,
                        _ => MemoryFallbackReason::Binding,
                    };
                    state = ObservationInput::raw(reason, supplied.packets().len());
                    None
                }
            }
        }
    };
    let mut seen = BTreeSet::new();
    if let Some(proof) = proof {
        state.diagnostics.mode = CoverageMode::Verified;
        state.diagnostics.set_fallback_reason = None;
        state.diagnostics.covered_through = proof.covered_through();
        state.diagnostics.raw_delta_after = proof.raw_delta_after();
        for packet in proof.packets() {
            check(cancel)?;
            let sources = packet
                .source_events
                .iter()
                .map(|source| (source.scope.clone(), source.sequence))
                .collect::<BTreeSet<_>>();
            let timespan = packet
                .entries
                .iter()
                .any(|entry| matches!(entry, Entry::ObservedTimeSpan { .. }));
            if timespan {
                state.diagnostics.raw_event_candidates += append_raw(
                    engine,
                    &request.observer,
                    (packet.from_exclusive, packet.through_revision),
                    request.version,
                    rows,
                    bytes,
                    &mut seen,
                    cancel,
                )?;
                state.diagnostics.packets_fell_back += 1;
                state.diagnostics.timespan_fallback_packets += 1;
            } else {
                for entry in &packet.entries {
                    check(cancel)?;
                    let Entry::Observation { source, event, .. } = entry else {
                        return Err(CompileError::Source);
                    };
                    if !seen.insert((source.scope.clone(), source.sequence)) {
                        return Err(CompileError::Source);
                    }
                    if rows.len() >= MAX_CANDIDATES {
                        return Err(CompileError::TooLarge);
                    }
                    // This is the actual verified cached event, not an Engine
                    // prefix reread, forced selection, or a diagnostic-only hit.
                    push_row(rows, bytes, event_row(event)?, cancel)?;
                    state.diagnostics.cached_event_candidates += 1;
                }
                if !sources.is_empty() {
                    state.diagnostics.packets_used += 1;
                }
            }
            state.packets.push(PacketSource {
                after: packet.from_exclusive,
                through: packet.through_revision,
                sources,
                cached: !timespan,
            });
        }
    }
    state.diagnostics.raw_event_candidates += append_raw(
        engine,
        &request.observer,
        (state.diagnostics.raw_delta_after, engine.revision()),
        request.version,
        rows,
        bytes,
        &mut seen,
        cancel,
    )?;
    Ok(state)
}
