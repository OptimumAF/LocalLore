//! Opt-in, bounded, per-turn metadata. No callbacks, text, I/O or gameplay authority.
use crate::{Error, Metrics, ResourceMetrics};
use serde::Serialize;
use sha2::{Digest, Sha256};
use std::sync::{
    atomic::{AtomicBool, Ordering},
    Arc, Mutex,
};

pub const MAX_ROLE_METRICS: usize = 3;

#[derive(Clone, Copy, Debug, PartialEq, Eq, Serialize)]
#[serde(rename_all = "snake_case")]
pub enum MetricRole {
    Director,
    Narrator,
}
#[derive(Clone, Copy, Debug, PartialEq, Eq, Serialize)]
#[serde(rename_all = "snake_case")]
pub enum AdapterTerminal {
    Completed,
    Cancelled,
    Timeout,
    Failed,
    Dropped,
}
#[derive(Clone, Copy, Debug, PartialEq, Eq, Serialize)]
#[serde(rename_all = "snake_case")]
pub enum AdapterError {
    Cancelled,
    Timeout,
    TooLarge,
    RetryMismatch,
    InvalidRequest,
    Provider,
    Cleanup,
}
#[derive(Clone, Copy, Debug, PartialEq, Eq, Serialize)]
#[serde(rename_all = "snake_case")]
pub enum NativeTerminal {
    Completed,
    Cancelled,
    Timeout,
    Failed,
    NotRun,
    Unknown,
}
#[derive(Clone, Debug, PartialEq, Serialize)]
pub struct RoleMetrics {
    pub role: MetricRole,
    /// Zero-based director call: 0 initial, 1 the one permitted repair; null for narrator.
    pub director_attempt: Option<u8>,
    pub ordinal: u8,
    pub request_sha256: String,
    /// Admission through parent observation/drain. Separate clock from worker durations.
    pub parent_elapsed_ms: u64,
    pub adapter_terminal: AdapterTerminal,
    pub adapter_error: Option<AdapterError>,
    /// Native client's operation result, not raw worker-frame status when the client returns an error.
    pub native_terminal: NativeTerminal,
    pub native_error: Option<Error>,
    /// Present only for a validated, completed native reply; failed partial timings are unknown.
    pub worker_metrics: Option<Metrics>,
    pub drained_on_drop: bool,
    /// None means resource sampling disabled or operation not run.
    pub resources: Option<ResourceMetrics>,
}
#[derive(Clone, Debug, PartialEq, Serialize)]
pub struct RoleMetricsSnapshot {
    pub version: u16,
    pub available: bool,
    pub incomplete: bool,
    pub turn_sha256: Option<String>,
    pub records: Vec<RoleMetrics>,
}
struct State {
    turn: Option<String>,
    records: Vec<RoleMetrics>,
}
struct Inner {
    state: Mutex<State>,
    incomplete: AtomicBool,
    author_unavailable: AtomicBool,
}
/// A new recorder is required per turn. Accidental reuse across turn identities drops metadata.
/// Contention/poison/capacity loss is best effort and never changes the provider's result.
#[derive(Clone)]
pub struct RoleMetricsLog(Arc<Inner>);
impl Default for RoleMetricsLog {
    fn default() -> Self {
        Self::new()
    }
}
impl RoleMetricsLog {
    pub fn new() -> Self {
        Self(Arc::new(Inner {
            state: Mutex::new(State {
                turn: None,
                records: Vec::with_capacity(MAX_ROLE_METRICS),
            }),
            incomplete: AtomicBool::new(false),
            author_unavailable: AtomicBool::new(false),
        }))
    }
    pub(crate) fn lost(&self) {
        self.0.incomplete.store(true, Ordering::Relaxed);
    }
    pub(crate) fn author_unavailable(&self) {
        self.0.author_unavailable.store(true, Ordering::Relaxed);
        self.lost();
    }
    pub(crate) fn bind(&self, turn: &str) {
        let Ok(mut state) = self.0.state.try_lock() else {
            self.lost();
            return;
        };
        match &state.turn {
            None => state.turn = Some(turn.into()),
            Some(before) if before == turn => {}
            Some(_) => self.lost(),
        }
    }
    pub(crate) fn record(&self, turn: &str, record: RoleMetrics) {
        let Ok(mut state) = self.0.state.try_lock() else {
            self.lost();
            return;
        };
        if state.turn.as_deref() != Some(turn)
            || state.records.len() == MAX_ROLE_METRICS
            || state
                .records
                .iter()
                .any(|prior| prior.request_sha256 == record.request_sha256)
        {
            self.lost();
            return;
        }
        state.records.push(record);
    }
    pub fn snapshot(&self) -> RoleMetricsSnapshot {
        if self.0.author_unavailable.load(Ordering::Relaxed) {
            return RoleMetricsSnapshot {
                version: 2,
                available: false,
                incomplete: true,
                turn_sha256: None,
                records: vec![],
            };
        }
        match self.0.state.try_lock() {
            Ok(state) => RoleMetricsSnapshot {
                version: 2,
                available: true,
                incomplete: self.0.incomplete.load(Ordering::Relaxed),
                turn_sha256: state.turn.clone(),
                records: state.records.clone(),
            },
            Err(_) => {
                self.lost();
                RoleMetricsSnapshot {
                    version: 2,
                    available: false,
                    incomplete: true,
                    turn_sha256: None,
                    records: vec![],
                }
            }
        }
    }
    #[cfg(test)]
    pub(crate) fn poison_for_test(&self) {
        let _ = std::panic::catch_unwind(|| {
            let _held = self.0.state.lock().unwrap();
            panic!("synthetic recorder poison");
        });
    }
}
pub(crate) fn digest(bytes: &[u8]) -> String {
    format!("{:x}", Sha256::digest(bytes))
}

#[cfg(test)]
mod tests {
    use super::*;
    fn record(index: u8) -> RoleMetrics {
        RoleMetrics {
            role: MetricRole::Director,
            director_attempt: Some(0),
            ordinal: index,
            request_sha256: digest(&[index]),
            parent_elapsed_ms: u64::MAX,
            adapter_terminal: AdapterTerminal::Completed,
            adapter_error: None,
            native_terminal: NativeTerminal::Completed,
            native_error: None,
            worker_metrics: Some(Metrics {
                load_ms: f64::MAX,
                prefill_ms: f64::MAX,
                decode_ms: f64::MAX,
                total_ms: f64::MAX,
                input_tokens: u32::MAX,
                output_tokens: u32::MAX,
                model_loads: u32::MAX,
                contexts_created: u32::MAX,
                abort_callbacks: u32::MAX,
            }),
            drained_on_drop: false,
            resources: Some(ResourceMetrics {
                status: crate::ResourceStatus::Partial,
                error: Some(crate::ResourceError::QueryFailed),
                sample_interval_ms: 250,
                successful_samples: 262,
                failed_samples: 262,
                observed_ms: Some(u64::MAX),
                sampled_peak_working_set_bytes: Some(u64::MAX),
                sampled_peak_private_committed_bytes: Some(u64::MAX),
                process_lifetime_peak_working_set_bytes: Some(u64::MAX),
                limit_reached: true,
            }),
        }
    }
    #[test]
    fn cap_scope_duplicate_and_serialized_snapshot_are_bounded() {
        let log = RoleMetricsLog::new();
        let turn = digest(b"synthetic turn");
        log.bind(&turn);
        for index in 0..3 {
            log.record(&turn, record(index));
        }
        assert_eq!(log.snapshot().records.len(), 3);
        assert!(!log.snapshot().incomplete);
        log.record(&turn, record(3));
        log.record(&turn, record(0));
        log.bind(&digest(b"other turn"));
        log.record(&digest(b"other turn"), record(4));
        let snapshot = log.snapshot();
        assert!(snapshot.incomplete);
        assert_eq!(snapshot.turn_sha256.as_deref(), Some(turn.as_str()));
        assert_eq!(snapshot.records.len(), 3);
        assert!(serde_json::to_vec(&snapshot).unwrap().len() < 8192);
    }
    #[test]
    fn contention_and_poison_return_honest_unavailable_snapshots() {
        let log = RoleMetricsLog::new();
        let held = log.0.state.lock().unwrap();
        log.bind("cannot publish while held");
        assert!(!log.snapshot().available);
        drop(held);
        assert!(log.snapshot().incomplete);
        log.poison_for_test();
        let snapshot = log.snapshot();
        assert!(!snapshot.available);
        assert!(snapshot.incomplete);
        assert!(snapshot.records.is_empty());
    }
}
