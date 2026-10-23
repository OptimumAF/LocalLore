//! Explicitly consented, process-local diagnostic copies. Never canonical or model authority.
use crate::{
    context_compiler::ContextPackage,
    contracts::{Proposal, Receipt, Scope},
    inference::{GenerationRequest, Input},
    turn_trace::{AttemptIdentity, TraceOwner},
};
use serde::Serialize;
use serde_json::{json, Value};
use sha2::{Digest, Sha256};
use std::{
    collections::VecDeque,
    io::Write,
    time::{Duration, Instant},
};

pub const CAPTURE_VERSION: u16 = 1;
pub const MAX_CAPTURE_ATTEMPTS: usize = 3;
pub const MAX_CAPTURE_BYTES: usize = 524_288;
pub const MAX_ATTEMPT_BYTES: usize = 196_608;
pub const MAX_ARTIFACT_BYTES: usize = 49_152;
pub const MAX_ARTIFACTS: usize = 16;
pub const RETENTION: Duration = Duration::from_secs(600);

/// Borrowed values from the actual production operation, not a second context builder.
pub enum Artifact<'a> {
    Context(&'a ContextPackage),
    Request(&'a GenerationRequest),
    DirectorOutput(&'a [u8]),
    Proposal(&'a Proposal),
    ApprovedPlan(&'a Receipt),
    Candidate(&'a Receipt),
    NarratorOutput(&'a [u8]),
}
#[derive(Clone, Debug, PartialEq, Serialize)]
pub struct CapturedArtifact {
    pub kind: &'static str,
    pub ordinal: usize,
    pub value: Value,
}
#[derive(Clone, Copy, Debug, PartialEq, Eq, Serialize)]
#[serde(rename_all = "snake_case")]
pub enum DetailStatus {
    Disabled,
    Expired,
    NotRetained,
    Recorded,
    Truncated,
}
#[derive(Clone, Debug, PartialEq, Serialize)]
pub struct DetailSnapshot {
    pub version: u16,
    pub status: DetailStatus,
    pub identity: Option<AttemptIdentity>,
    pub artifacts: Vec<CapturedArtifact>,
    pub exact_reconstruction: bool,
    pub privacy: &'static str,
}
struct Consent {
    owner: TraceOwner,
    scope: Scope,
    expires: Instant,
}
struct Attempt {
    sequence: u64,
    epoch: u64,
    identity: AttemptIdentity,
    bytes: usize,
    truncated: bool,
    artifacts: Vec<CapturedArtifact>,
}
/// Only TraceRing may bind the opaque native owner/attempt and authorize reads.
#[derive(Default)]
pub(crate) struct CaptureStore {
    epoch: u64,
    consent: Option<Consent>,
    expired: Option<(TraceOwner, Scope)>,
    attempts: VecDeque<Attempt>,
}
struct Limited(Vec<u8>);
impl Write for Limited {
    fn write(&mut self, bytes: &[u8]) -> std::io::Result<usize> {
        if self.0.len().saturating_add(bytes.len()) > MAX_ARTIFACT_BYTES {
            return Err(std::io::Error::other("DiagnosticBudget"));
        }
        self.0.extend_from_slice(bytes);
        Ok(bytes.len())
    }
    fn flush(&mut self) -> std::io::Result<()> {
        Ok(())
    }
}
fn encode<T: Serialize>(value: &T) -> Option<Value> {
    let mut bytes = Limited(Vec::new());
    serde_json::to_writer(&mut bytes, value).ok()?;
    serde_json::from_slice(&bytes.0).ok()
}
fn output(bytes: &[u8]) -> Option<Value> {
    // Bound before constructing a diagnostic copy, even for trusted native hooks.
    if bytes.len() > 16_384 {
        return None;
    }
    let hash = format!("{:x}", Sha256::digest(bytes));
    Some(match std::str::from_utf8(bytes) {
        Ok(text) => json!({"encoding":"utf8","bytes":bytes.len(),"sha256":hash,"text":text}),
        Err(_) => json!({"encoding":"hex","bytes":bytes.len(),"sha256":hash,
            "hex":bytes.iter().map(|b|format!("{b:02x}")).collect::<String>()}),
    })
}
#[derive(Serialize)]
struct RequestCopy<'a> {
    version: u16,
    scope: &'a Scope,
    turn: &'a str,
    revision: u64,
    model_profile: &'a str,
    schema_id: &'a str,
    budget: BudgetCopy,
    input: InputCopy<'a>,
}
#[derive(Serialize)]
struct BudgetCopy {
    max_output_bytes: usize,
    max_output_tokens: u32,
    max_pending_polls: u16,
    deadline_ms: u64,
}
#[derive(Serialize)]
struct InputCopy<'a> {
    kind: &'static str,
    role: &'a str,
    prompt: &'a str,
    schema: &'a Value,
}
fn artifact(value: Artifact<'_>) -> Option<(&'static str, Value)> {
    Some(match value {
        Artifact::Context(v) => ("selected_context", encode(v)?),
        Artifact::Proposal(v) => ("parsed_proposal", encode(v)?),
        Artifact::ApprovedPlan(v) => ("validated_plan_not_durable_commit", encode(v)?),
        Artifact::Candidate(v) => ("accepted_candidate_not_durable_commit", encode(v)?),
        Artifact::DirectorOutput(v) => ("raw_director_output", output(v)?),
        Artifact::NarratorOutput(v) => ("raw_narrator_output", output(v)?),
        Artifact::Request(v) => {
            let Input::Structured {
                role,
                prompt,
                schema,
            } = &v.input
            else {
                return None;
            };
            // The provider contract already bounds these in Play. Refuse oversized copies.
            if prompt.len() > 32_000 {
                return None;
            }
            let data = RequestCopy {
                version: v.version,
                scope: &v.scope,
                turn: &v.turn,
                revision: v.revision,
                model_profile: &v.model_profile,
                schema_id: &v.schema,
                budget: BudgetCopy {
                    max_output_bytes: v.budget.max_output_bytes,
                    max_output_tokens: v.budget.max_output_tokens,
                    max_pending_polls: v.budget.max_pending_polls,
                    deadline_ms: v.budget.deadline_ms,
                },
                input: InputCopy {
                    kind: "structured",
                    role,
                    prompt,
                    schema,
                },
            };
            ("generation_request", encode(&data)?)
        }
    })
}
impl CaptureStore {
    pub fn configure(&mut self, owner: &TraceOwner, scope: &Scope, enabled: bool) {
        self.clear();
        if enabled {
            self.consent = Some(Consent {
                owner: owner.clone(),
                scope: scope.clone(),
                expires: Instant::now() + RETENTION,
            });
        }
    }
    pub fn clear(&mut self) {
        self.epoch = self.epoch.saturating_add(1);
        self.consent = None;
        self.expired = None;
        self.attempts.clear();
    }
    fn sweep_at(&mut self, now: Instant) {
        if self.consent.as_ref().is_some_and(|c| !c.owner.live()) {
            self.clear();
            return;
        }
        if self.consent.as_ref().is_some_and(|c| now >= c.expires) {
            let marker = self
                .consent
                .as_ref()
                .map(|c| (c.owner.clone(), c.scope.clone()));
            self.clear();
            self.expired = marker;
        }
    }
    fn matches(&self, owner: &TraceOwner, scope: &Scope) -> bool {
        self.consent
            .as_ref()
            .is_some_and(|c| c.owner.live() && c.owner.same(owner) && &c.scope == scope)
    }
    pub fn revoke(&mut self, owner: &TraceOwner) {
        if self.consent.as_ref().is_some_and(|c| c.owner.same(owner)) {
            self.clear();
        }
    }
    pub fn begin(
        &mut self,
        owner: &TraceOwner,
        sequence: u64,
        identity: &AttemptIdentity,
    ) -> Option<u64> {
        self.sweep_at(Instant::now());
        if !self.matches(owner, &identity.scope) || self.epoch == u64::MAX {
            return None;
        }
        while self.attempts.len() >= MAX_CAPTURE_ATTEMPTS {
            self.attempts.pop_front();
        }
        self.attempts.push_back(Attempt {
            sequence,
            epoch: self.epoch,
            identity: identity.clone(),
            bytes: 0,
            truncated: false,
            artifacts: Vec::new(),
        });
        Some(self.epoch)
    }
    pub fn record(&mut self, epoch: Option<u64>, sequence: u64, value: Artifact<'_>) {
        self.sweep_at(Instant::now());
        if epoch != Some(self.epoch) || self.consent.is_none() {
            return;
        }
        let Some(index) = self
            .attempts
            .iter()
            .position(|a| a.sequence == sequence && a.epoch == self.epoch)
        else {
            return;
        };
        if self.attempts[index].artifacts.len() >= MAX_ARTIFACTS {
            self.attempts[index].truncated = true;
            return;
        }
        let Some((kind, value)) = artifact(value) else {
            self.attempts[index].truncated = true;
            return;
        };
        let captured = CapturedArtifact {
            kind,
            ordinal: self.attempts[index].artifacts.len(),
            value,
        };
        let Ok(encoded) = serde_json::to_vec(&captured) else {
            self.attempts[index].truncated = true;
            return;
        };
        let total: usize = self.attempts.iter().map(|a| a.bytes).sum();
        if encoded.len() > MAX_ARTIFACT_BYTES
            || self.attempts[index].bytes.saturating_add(encoded.len()) > MAX_ATTEMPT_BYTES
            || total.saturating_add(encoded.len()) > MAX_CAPTURE_BYTES
        {
            self.attempts[index].truncated = true;
            return;
        }
        self.attempts[index].bytes += encoded.len();
        self.attempts[index].artifacts.push(captured);
    }
    pub fn read(
        &mut self,
        owner: &TraceOwner,
        scope: &Scope,
        sequence: Option<u64>,
    ) -> DetailSnapshot {
        self.sweep_at(Instant::now());
        let mut result=DetailSnapshot{version:CAPTURE_VERSION,status:if self.expired.as_ref().is_some_and(|(o,s)|o.same(owner)&&s==scope){DetailStatus::Expired}else{DetailStatus::Disabled},
            identity:None,artifacts:vec![],exact_reconstruction:false,
            privacy:"Private exact captured context/prompts/outputs; may include spoilers and original input. Memory only; not a canonical receipt or model authority."};
        if !self.matches(owner, scope) {
            return result;
        }
        result.status = DetailStatus::NotRetained;
        if let Some(a) = sequence.and_then(|s| self.attempts.iter().find(|a| a.sequence == s)) {
            result.status = if a.truncated {
                DetailStatus::Truncated
            } else {
                DetailStatus::Recorded
            };
            result.identity = Some(a.identity.clone());
            result.artifacts = a.artifacts.clone();
        }
        result
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    fn key() -> AttemptIdentity {
        AttemptIdentity {
            scope: Scope {
                story: "test".into(),
                branch: "main".into(),
            },
            base_revision: 0,
            observer: "player".into(),
            turn: "turn".into(),
            attempt: 1,
        }
    }
    #[test]
    fn opt_in_owner_scope_epoch_expiry_and_clear_fence_raw_data() {
        let mut store = CaptureStore::default();
        let owner = TraceOwner::default();
        let key = key();
        assert_eq!(store.begin(&owner, 1, &key), None);
        store.configure(&owner, &key.scope, true);
        let lease = store.begin(&owner, 1, &key);
        store.record(lease, 1, Artifact::DirectorOutput(b"PRIVATE"));
        assert_eq!(
            store.read(&owner, &key.scope, Some(1)).status,
            DetailStatus::Recorded
        );
        assert!(store
            .read(&TraceOwner::default(), &key.scope, Some(1))
            .artifacts
            .is_empty());
        store.configure(&owner, &key.scope, true);
        store.record(lease, 1, Artifact::DirectorOutput(b"LATE"));
        assert!(store.read(&owner, &key.scope, Some(1)).artifacts.is_empty());
        let lease = store.begin(&owner, 2, &key);
        store.record(lease, 2, Artifact::DirectorOutput(&[0xff]));
        assert_eq!(
            store.read(&owner, &key.scope, Some(2)).artifacts[0].value["hex"],
            "ff"
        );
        store.sweep_at(Instant::now() + RETENTION + Duration::from_secs(1));
        assert_eq!(
            store.read(&owner, &key.scope, Some(2)).status,
            DetailStatus::Expired
        );
        store.configure(&owner, &key.scope, true);
        store.revoke(&owner);
        assert_eq!(
            store.read(&owner, &key.scope, None).status,
            DetailStatus::Disabled
        );
    }
    #[test]
    fn oversized_artifacts_and_finite_attempts_are_labeled_without_partial_data() {
        let mut store = CaptureStore::default();
        let owner = TraceOwner::default();
        let key = key();
        store.configure(&owner, &key.scope, true);
        for i in 0..4 {
            let lease = store.begin(&owner, i, &key);
            store.record(lease, i, Artifact::DirectorOutput(&vec![b'x'; 16_385]));
        }
        assert_eq!(store.attempts.len(), 3);
        assert_eq!(
            store.read(&owner, &key.scope, Some(0)).status,
            DetailStatus::NotRetained
        );
        let snapshot = store.read(&owner, &key.scope, Some(3));
        assert_eq!(snapshot.status, DetailStatus::Truncated);
        assert!(snapshot.artifacts.is_empty());
    }
    #[test]
    fn byte_and_count_limits_bound_complete_artifacts_and_eviction_recovers_capacity() {
        let mut store = CaptureStore::default();
        let owner = TraceOwner::default();
        let key = key();
        store.configure(&owner, &key.scope, true);
        for sequence in 1..=3 {
            let lease = store.begin(&owner, sequence, &key);
            for _ in 0..MAX_ARTIFACTS {
                store.record(lease, sequence, Artifact::DirectorOutput(&[b'x'; 16_384]));
            }
        }
        assert!(store
            .attempts
            .iter()
            .all(|a| a.bytes <= MAX_ATTEMPT_BYTES && a.truncated));
        let before: usize = store.attempts.iter().map(|a| a.bytes).sum();
        assert!(before <= MAX_CAPTURE_BYTES && before > MAX_CAPTURE_BYTES - MAX_ARTIFACT_BYTES);
        for a in &store.attempts {
            assert_eq!(
                a.bytes,
                a.artifacts
                    .iter()
                    .map(|v| serde_json::to_vec(v).unwrap().len())
                    .sum::<usize>()
            );
            assert!(a
                .artifacts
                .iter()
                .all(|v| v.value["text"].as_str().unwrap().len() == 16_384));
        }
        let lease = store.begin(&owner, 4, &key);
        assert_eq!(
            store.read(&owner, &key.scope, Some(1)).status,
            DetailStatus::NotRetained
        );
        store.record(lease, 4, Artifact::DirectorOutput(b"capacity recovered"));
        assert_eq!(store.read(&owner, &key.scope, Some(4)).artifacts.len(), 1);
        store.configure(&owner, &key.scope, true);
        let lease = store.begin(&owner, 5, &key);
        for _ in 0..=MAX_ARTIFACTS {
            store.record(lease, 5, Artifact::DirectorOutput(b"small"));
        }
        assert_eq!(store.attempts[0].artifacts.len(), MAX_ARTIFACTS);
        assert!(store.attempts[0].truncated);
    }
    #[test]
    fn retirement_blocks_late_writes_and_expiry_status_is_owner_and_scope_local() {
        let mut store = CaptureStore::default();
        let owner = TraceOwner::default();
        let key = key();
        store.configure(&owner, &key.scope, true);
        let lease = store.begin(&owner, 1, &key);
        store.record(lease, 1, Artifact::DirectorOutput(b"private"));
        owner.retire();
        store.record(lease, 1, Artifact::DirectorOutput(b"late private"));
        assert!(store.attempts.is_empty());
        assert_eq!(
            store.read(&owner, &key.scope, Some(1)).status,
            DetailStatus::Disabled
        );
        // A closed owner cannot be revived by reconfiguration.
        store.configure(&owner, &key.scope, true);
        assert_eq!(store.begin(&owner, 2, &key), None);
        let live = TraceOwner::default();
        store.configure(&live, &key.scope, true);
        store.sweep_at(Instant::now() + RETENTION);
        let foreign = Scope {
            story: "other".into(),
            branch: "main".into(),
        };
        assert_eq!(
            store.read(&live, &foreign, None).status,
            DetailStatus::Disabled
        );
        assert_eq!(
            store.read(&owner, &key.scope, None).status,
            DetailStatus::Disabled
        );
        assert_eq!(
            store.read(&live, &key.scope, None).status,
            DetailStatus::Expired
        );
        assert!(store.attempts.is_empty());
    }
}
