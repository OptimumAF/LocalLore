//! Data-only player transcript source. This is not a model context, policy,
//! packing decision or execution permission. Existing Play policies are intact.
use super::{check, policy, CompileError, Engine, Scope, MAX_CANDIDATES, MAX_CANDIDATE_BYTES};
use crate::engine::AcceptedHistoryBasis;
use serde::Serialize;

/// Owned, exact-prefix source containing only eligible recorded prose and its
/// provenance. The opaque basis can be checked against an actual Engine; it is
/// never a serialized digest or a grant to execute generation.
///
/// These native data types deliberately have no serde implementation:
/// ```compile_fail,E0277
/// use locallore::context_compiler::LiteralTranscriptSourceV1;
/// fn serialize<T: serde::Serialize>() {}
/// serialize::<LiteralTranscriptSourceV1>();
/// ```
/// ```compile_fail,E0277
/// use locallore::context_compiler::LiteralTranscriptSourceV1;
/// fn deserialize<T: serde::de::DeserializeOwned>() {}
/// deserialize::<LiteralTranscriptSourceV1>();
/// ```
#[derive(Clone, Debug, PartialEq, Eq)]
pub struct LiteralTranscriptSourceV1 {
    scope: Scope,
    head: u64,
    observer: String,
    accepted_basis: AcceptedHistoryBasis,
    units: Vec<LiteralTranscriptUnitV1>,
    budget_bytes: usize,
}

impl LiteralTranscriptSourceV1 {
    pub fn version(&self) -> u16 {
        1
    }
    pub fn scope(&self) -> &Scope {
        &self.scope
    }
    pub fn head(&self) -> u64 {
        self.head
    }
    pub fn observer(&self) -> &str {
        &self.observer
    }
    pub fn accepted_basis(&self) -> &AcceptedHistoryBasis {
        &self.accepted_basis
    }
    pub fn units(&self) -> &[LiteralTranscriptUnitV1] {
        &self.units
    }
    /// Compact private UTF-8 source/provenance shape size, not model tokens,
    /// Rust heap usage or a guarantee that any rendered prompt will fit.
    pub fn budget_bytes(&self) -> usize {
        self.budget_bytes
    }
}

/// A whole eligible ordinary receipt's recorded input and accepted narration.
/// Typed actions have no original text; no input or opening is invented.
/// Structured events/current state are intentionally absent.
/// ```compile_fail,E0277
/// use locallore::context_compiler::LiteralTranscriptUnitV1;
/// fn serialize<T: serde::Serialize>() {}
/// serialize::<LiteralTranscriptUnitV1>();
/// ```
/// ```compile_fail,E0277
/// use locallore::context_compiler::LiteralTranscriptUnitV1;
/// fn deserialize<T: serde::de::DeserializeOwned>() {}
/// deserialize::<LiteralTranscriptUnitV1>();
/// ```
#[derive(Clone, Debug, PartialEq, Eq)]
pub struct LiteralTranscriptUnitV1 {
    original_scope: Scope,
    turn: String,
    through_revision: u64,
    original_input: Option<String>,
    narration: Option<String>,
}

impl LiteralTranscriptUnitV1 {
    pub fn original_scope(&self) -> &Scope {
        &self.original_scope
    }
    pub fn turn(&self) -> &str {
        &self.turn
    }
    pub fn through_revision(&self) -> u64 {
        self.through_revision
    }
    pub fn original_input(&self) -> Option<&str> {
        self.original_input.as_deref()
    }
    pub fn narration(&self) -> Option<&str> {
        self.narration.as_deref()
    }
}

// These private borrowed views measure a fixed shape only. No public wire DTO,
// decoder, basis serialization or serde implementation for Source/Unit exists.
#[derive(Serialize)]
struct BudgetEnvelope<'a> {
    version: u16,
    scope: &'a Scope,
    head: u64,
    observer: &'a str,
    units: [(); 0],
}
#[derive(Serialize)]
struct BudgetUnit<'a> {
    original_scope: &'a Scope,
    turn: &'a str,
    through_revision: u64,
    original_input: Option<&'a str>,
    narration: Option<&'a str>,
}

/// Extract eligible actual player prose at the provided immutable Engine's
/// exact head. Callers may explicitly obtain a historical Engine prefix first.
/// Cancellation (including callback panic) returns no partial source.
///
/// Domain2 and NPC/unknown observers are unavailable. Future packing/rendering
/// must separately enforce the shared forwarded budget and normal engine guard.
pub fn player_literal_transcript_v1_cancelled(
    engine: &Engine,
    scope: &Scope,
    expected_head: u64,
    observer: &str,
    cancel: &dyn Fn() -> bool,
) -> Result<LiteralTranscriptSourceV1, CompileError> {
    check(cancel)?;
    if scope != engine.scope() {
        return Err(CompileError::Scope);
    }
    if expected_head != engine.revision() {
        return Err(CompileError::Stale);
    }
    if observer != engine.seed().player {
        return Err(CompileError::Observer);
    }
    if engine.domain_version() != 1 {
        return Err(CompileError::UnsupportedPolicy);
    }
    let mut budget_bytes = serde_json::to_vec(&BudgetEnvelope {
        version: 1,
        scope,
        head: expected_head,
        observer,
        units: [],
    })
    .map_err(|_| CompileError::Source)?
    .len();
    if budget_bytes > MAX_CANDIDATE_BYTES {
        return Err(CompileError::TooLarge);
    }
    let mut units = Vec::new();
    policy::visit_eligible_transcript_units_cancelled(engine, observer, cancel, |unit| {
        if units.len() >= MAX_CANDIDATES {
            return Err(CompileError::TooLarge);
        }
        let through_revision = unit
            .events
            .last()
            .ok_or(CompileError::Source)?
            .event
            .sequence();
        let encoded_bytes = serde_json::to_vec(&BudgetUnit {
            original_scope: &unit.original_scope,
            turn: &unit.turn,
            through_revision,
            original_input: unit.original_input.as_deref(),
            narration: unit.narration.as_deref(),
        })
        .map_err(|_| CompileError::Source)?
        .len();
        // The envelope already counts []; insert whole encoded units and only
        // their intervening commas. No quadratic reserialization or truncation.
        budget_bytes = budget_bytes
            .checked_add(encoded_bytes)
            .and_then(|n| n.checked_add(usize::from(!units.is_empty())))
            .ok_or(CompileError::TooLarge)?;
        if budget_bytes > MAX_CANDIDATE_BYTES {
            return Err(CompileError::TooLarge);
        }
        units.push(LiteralTranscriptUnitV1 {
            original_scope: unit.original_scope,
            turn: unit.turn,
            through_revision,
            original_input: unit.original_input,
            narration: unit.narration,
        });
        Ok(())
    })?;
    let accepted_basis = engine
        .accepted_history_basis()
        .map_err(|_| CompileError::Source)?;
    check(cancel)?;
    Ok(LiteralTranscriptSourceV1 {
        scope: scope.clone(),
        head: expected_head,
        observer: observer.to_owned(),
        accepted_basis,
        units,
        budget_bytes,
    })
}
