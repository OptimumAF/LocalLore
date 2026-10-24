// Copyright 2026 LocalLore contributors. SPDX-License-Identifier: Apache-2.0
//! Native private author capabilities on the existing bounded shared worker.
use crate::{archive::ArchiveBroker, lease::WindowLease};
use locallore::{
    author_correction::{AuthorCorrectionInputV1, AuthorCorrectionOperationV1},
    contracts::{Scope, MAX_RECEIPT_BYTES},
    host::{Host, HostAuthorPreparation, MAX_OUTPUT},
};
use serde_json::{json, Value};
use std::{
    collections::BTreeMap,
    sync::{
        atomic::{AtomicU64, Ordering},
        Arc, Mutex, Weak,
    },
    time::{Duration, Instant},
};

const TTL: Duration = Duration::from_secs(600);
const MAX_CAPS: usize = 4;
const MAX_INTEGER: u64 = 9_007_199_254_740_991;
type PortResult<T> = std::result::Result<T, String>;
struct PrepareInput {
    session: String,
    input: AuthorCorrectionInputV1,
}
struct CommitInput {
    session: String,
    input: AuthorCorrectionInputV1,
    token: String,
    sha: String,
}
struct Capability {
    created: Instant,
    generation: u64,
    session: String,
    input: AuthorCorrectionInputV1,
    sha: String,
    prepared: HostAuthorPreparation,
}
pub struct AuthorManager {
    host: Weak<Host>,
    lease: Weak<WindowLease>,
    broker: Weak<ArchiveBroker>,
    epoch: u64,
    generation: AtomicU64,
    caps: Mutex<BTreeMap<String, Capability>>,
    #[cfg(test)]
    test_gate: Mutex<Option<TestGate>>,
}
#[cfg(test)]
struct TestGate {
    after_apply: bool,
    entered: std::sync::mpsc::Sender<()>,
    release: std::sync::mpsc::Receiver<()>,
}
fn identifier(value: &str, max: usize) -> bool {
    !value.is_empty()
        && value.len() <= max
        && value
            .bytes()
            .all(|b| b.is_ascii_alphanumeric() || b"_-".contains(&b))
}
fn object<'a>(value: &'a Value, keys: &[&str]) -> PortResult<&'a serde_json::Map<String, Value>> {
    let object = value.as_object().ok_or("InvalidAuthorInput")?;
    if object.len() != keys.len() || !keys.iter().all(|key| object.contains_key(*key)) {
        return Err("InvalidAuthorInput".into());
    }
    Ok(object)
}
fn text(value: &Value) -> PortResult<&str> {
    value.as_str().ok_or_else(|| "InvalidAuthorInput".into())
}
fn integer(value: &Value) -> PortResult<u64> {
    value
        .as_u64()
        .filter(|v| *v <= MAX_INTEGER)
        .ok_or_else(|| "InvalidAuthorInput".into())
}
fn raw(value: &str) -> PortResult<Value> {
    locallore::engine::parse_unique_json(value.as_bytes(), MAX_RECEIPT_BYTES)
        .map_err(|error| error.to_string())
}
fn version(value: &Value) -> PortResult<()> {
    if integer(&value["version"])? != 1 {
        Err("Version".into())
    } else {
        Ok(())
    }
}
fn session(value: &Value) -> PortResult<String> {
    let s = text(value)?;
    if !identifier(s, 128) {
        return Err("InvalidAuthorInput".into());
    }
    Ok(s.into())
}
fn author_input(value: &Value) -> PortResult<AuthorCorrectionInputV1> {
    object(
        value,
        &[
            "version",
            "parent",
            "expected_parent_revision",
            "fork_revision",
            "child_branch",
            "operation",
            "reason",
        ],
    )?;
    version(value)?;
    object(&value["parent"], &["story", "branch"])?;
    let story = text(&value["parent"]["story"])?;
    let branch = text(&value["parent"]["branch"])?;
    let child = text(&value["child_branch"])?;
    let operation = &value["operation"];
    object(
        operation,
        &["op", "fact", "expected_proposition", "replacement"],
    )?;
    if text(&operation["op"])? != "replace_fact_proposition"
        || ![story, branch, child, text(&operation["fact"])?]
            .iter()
            .all(|v| identifier(v, 64))
    {
        return Err("InvalidAuthorInput".into());
    }
    let input = AuthorCorrectionInputV1 {
        version: 1,
        parent: Scope {
            story: story.into(),
            branch: branch.into(),
        },
        expected_parent_revision: integer(&value["expected_parent_revision"])?,
        fork_revision: integer(&value["fork_revision"])?,
        child_branch: child.into(),
        operation: AuthorCorrectionOperationV1::ReplaceFactProposition {
            fact: text(&operation["fact"])?.into(),
            expected_proposition: text(&operation["expected_proposition"])?.into(),
            replacement: text(&operation["replacement"])?.into(),
        },
        reason: text(&value["reason"])?.into(),
    };
    input.validate().map_err(|error| error.to_string())?;
    Ok(input)
}
fn consent(value: &Value, key: &str) -> PortResult<()> {
    if value[key].as_bool() != Some(true) {
        Err("AuthorConsentRequired".into())
    } else {
        Ok(())
    }
}
fn parse_prepare(value: &str) -> PortResult<PrepareInput> {
    let value = raw(value)?;
    object(&value, &["version", "session", "input", "author_consent"])?;
    version(&value)?;
    consent(&value, "author_consent")?;
    Ok(PrepareInput {
        session: session(&value["session"])?,
        input: author_input(&value["input"])?,
    })
}
fn parse_commit(value: &str) -> PortResult<CommitInput> {
    let value = raw(value)?;
    object(
        &value,
        &[
            "version",
            "session",
            "input",
            "preview_token",
            "preview_sha256",
            "confirmed",
        ],
    )?;
    version(&value)?;
    consent(&value, "confirmed")?;
    let token = text(&value["preview_token"])?;
    let sha = text(&value["preview_sha256"])?;
    if !crate::archive::valid_id(token)
        || sha.len() != 64
        || !sha
            .bytes()
            .all(|b| b.is_ascii_digit() || (b'a'..=b'f').contains(&b))
    {
        return Err("InvalidAuthorInput".into());
    }
    Ok(CommitInput {
        session: session(&value["session"])?,
        input: author_input(&value["input"])?,
        token: token.into(),
        sha: sha.into(),
    })
}
fn parse_lookup(value: &str) -> PortResult<AuthorCorrectionInputV1> {
    let value = raw(value)?;
    object(&value, &["version", "input", "author_consent"])?;
    version(&value)?;
    consent(&value, "author_consent")?;
    author_input(&value["input"])
}
fn bounded(value: Value) -> PortResult<Value> {
    if serde_json::to_vec(&value).map_err(|_| "Internal")?.len() > MAX_OUTPUT {
        Err("TooLarge".into())
    } else {
        Ok(value)
    }
}
impl AuthorManager {
    pub fn check_binding(&self, host: &Arc<Host>, lease: &Arc<WindowLease>, broker: &Arc<ArchiveBroker>, epoch: u64) -> PortResult<()> {
        self.check_owner(host, lease, epoch)?;
        self.check_broker(broker)
    }
    pub fn discard_raw(&self, host: &Arc<Host>, lease: &Arc<WindowLease>, broker: &Arc<ArchiveBroker>, epoch: u64, request: &str) -> PortResult<bool> {
        self.check_binding(host, lease, broker, epoch)?;
        let value = raw(request)?;
        object(&value, &["version", "session", "preview_token"])?;
        version(&value)?;
        self.discard_preview(host, lease, epoch, &session(&value["session"])?, text(&value["preview_token"])?)
    }
    pub fn new(
        host: &Arc<Host>,
        lease: &Arc<WindowLease>,
        broker: &Arc<ArchiveBroker>,
        epoch: u64,
    ) -> PortResult<Arc<Self>> {
        if !lease.valid(epoch) {
            return Err("Closed".into());
        }
        Ok(Arc::new(Self {
            host: Arc::downgrade(host),
            lease: Arc::downgrade(lease),
            broker: Arc::downgrade(broker),
            epoch,
            generation: AtomicU64::new(1),
            caps: Mutex::new(BTreeMap::new()),
            #[cfg(test)]
            test_gate: Mutex::new(None),
        }))
    }
    fn check_owner(
        &self,
        host: &Arc<Host>,
        lease: &Arc<WindowLease>,
        epoch: u64,
    ) -> PortResult<()> {
        if !Weak::ptr_eq(&self.host, &Arc::downgrade(host))
            || !Weak::ptr_eq(&self.lease, &Arc::downgrade(lease))
        {
            return Err("Integrity".into());
        }
        if epoch != self.epoch
            || !lease.valid(epoch)
            || self.generation.load(Ordering::SeqCst) == u64::MAX
        {
            // A wrong caller epoch alone must not destroy still-valid owner caps.
            if !lease.valid(self.epoch) {
                self.retire(self.epoch)
            }
            return Err("Closed".into());
        }
        Ok(())
    }
    fn check_broker(&self, broker: &Arc<ArchiveBroker>) -> PortResult<()> {
        if !Weak::ptr_eq(&self.broker, &Arc::downgrade(broker)) {
            return Err("Integrity".into());
        }
        Ok(())
    }
    fn prune(&self, caps: &mut BTreeMap<String, Capability>) {
        if self.host.strong_count() == 0
            || !self
                .lease
                .upgrade()
                .is_some_and(|lease| lease.valid(self.epoch))
        {
            caps.clear();
            return;
        }
        caps.retain(|_, cap| {
            cap.created.elapsed() < TTL && cap.generation == self.generation.load(Ordering::SeqCst)
        });
    }
    pub fn retire(&self, epoch: u64) {
        if epoch == self.epoch {
            // Checked private lifecycle counter; exhaustion closes all future admissions.
            let _ = self
                .generation
                .fetch_update(Ordering::SeqCst, Ordering::SeqCst, |value| {
                    value.checked_add(1)
                });
            self.caps.lock().unwrap_or_else(|p| p.into_inner()).clear();
        }
    }
    pub fn discard_preview(
        &self,
        host: &Arc<Host>,
        lease: &Arc<WindowLease>,
        epoch: u64,
        selected_session: &str,
        token: &str,
    ) -> PortResult<bool> {
        self.check_owner(host, lease, epoch)?;
        if !identifier(selected_session, 128) || !crate::archive::valid_id(token) {
            return Err("InvalidAuthorInput".into());
        }
        lease.dispatch(epoch, || {
            let mut caps = self.caps.lock().map_err(|_| "Internal")?;
            self.prune(&mut caps);
            let Some(cap) = caps.get(token) else {
                return Ok(false);
            };
            if cap.session != selected_session {
                return Err("AuthorPreviewMismatch".into());
            }
            Ok(caps.remove(token).is_some())
        })
    }
    pub fn prepare_start(
        self: &Arc<Self>,
        host: Arc<Host>,
        lease: Arc<WindowLease>,
        broker: Arc<ArchiveBroker>,
        epoch: u64,
        input: &str,
    ) -> PortResult<Value> {
        self.check_owner(&host, &lease, epoch)?;
        self.check_broker(&broker)?;
        let request = parse_prepare(input)?;
        let manager = self.clone();
        let selected_lease = lease.clone();
        let generation = self.generation.load(Ordering::SeqCst);
        broker.start(lease, epoch, move |work| {
            work.phase("author_preparing")?;
            let cancelled = || work.cancelled() || manager.generation.load(Ordering::SeqCst) != generation;
            let prepared = host.prepare_author_correction(&request.session, &request.input, &cancelled)?;
            let bytes = prepared.preview_bytes();
            if bytes.len() > MAX_RECEIPT_BYTES { return Err("TooLarge".into()); }
            let preview_json = std::str::from_utf8(bytes).map_err(|_| "Integrity")?.to_owned();
            let sha = locallore::inspection::sha256(bytes);
            let token = crate::exports::identifier()?;
            let value = bounded(json!({"version":1,"kind":"author_preview","session":request.session,"preview_token":token,"preview_sha256":sha,"preview_json":preview_json,"expires_seconds":TTL.as_secs()}))?;
            selected_lease.dispatch(epoch, || {
                work.check()?;
                manager.check_owner(&host, &selected_lease, epoch)?;
                let mut caps = manager.caps.lock().map_err(|_| "Internal")?;
                manager.prune(&mut caps);
                if manager.generation.load(Ordering::SeqCst) != generation { return Err("Cancelled".into()); }
                if caps.len() >= MAX_CAPS { return Err("AuthorPreviewLimit".into()); }
                if caps.contains_key(&token) { return Err("Internal".into()); }
                caps.insert(token, Capability { created: Instant::now(), generation, session: request.session, input: request.input, sha, prepared });
                Ok(value)
            })
        })
    }
    pub fn commit_start(
        self: &Arc<Self>,
        host: Arc<Host>,
        lease: Arc<WindowLease>,
        broker: Arc<ArchiveBroker>,
        epoch: u64,
        input: &str,
    ) -> PortResult<Value> {
        self.check_owner(&host, &lease, epoch)?;
        self.check_broker(&broker)?;
        let request = parse_commit(input)?;
        // All identity/content/second-consent checks precede consuming the capability.
        let cap = lease.dispatch(epoch, || {
            let mut caps = self.caps.lock().map_err(|_| "Internal")?;
            self.prune(&mut caps);
            let cap = caps.get(&request.token).ok_or("UnknownAuthorPreview")?;
            if cap.session != request.session
                || cap.input != request.input
                || cap.sha != request.sha
                || cap.prepared.preview().input != request.input
                || locallore::inspection::sha256(cap.prepared.preview_bytes()) != request.sha
            {
                return Err("AuthorPreviewMismatch".into());
            }
            caps.remove(&request.token)
                .ok_or_else(|| "UnknownAuthorPreview".into())
        })?;
        // A valid attempt consumes even on Busy/spawn refusal or pre-closure cancellation.
        let manager = self.clone();
        broker.start(lease, epoch, move |work| {
            work.phase("author_applying")?;
            #[cfg(test)]
            manager.gate(false)?;
            work.check()?;
            let cancelled = || work.cancelled() || cap.created.elapsed() >= TTL || manager.generation.load(Ordering::SeqCst) != cap.generation;
            if cancelled() { return Err("Cancelled".into()); }
            let outcome = host.apply_author_correction(&cap.prepared, &cancelled)?;
            #[cfg(test)]
            let _ = manager.gate(true);
            // Successful actual Store commit is never relabeled by a late cancel.
            bounded(json!({"version":1,"kind":"author_commit","session":request.session,"outcome":outcome}))
        })
    }
    pub fn lookup_start(
        self: &Arc<Self>,
        host: Arc<Host>,
        lease: Arc<WindowLease>,
        broker: Arc<ArchiveBroker>,
        epoch: u64,
        input: &str,
    ) -> PortResult<Value> {
        self.check_owner(&host, &lease, epoch)?;
        self.check_broker(&broker)?;
        let input = parse_lookup(input)?;
        broker.start(lease, epoch, move |work| {
            work.phase("author_lookup")?;
            let outcome = host.lookup_author_correction(&input, &|| work.cancelled())?;
            bounded(json!({"version":1,"kind":"author_lookup","found":outcome.is_some(),"outcome":outcome}))
        })
    }
    #[cfg(test)]
    fn gate(&self, after_apply: bool) -> PortResult<()> {
        let gate = {
            let mut gate = self.test_gate.lock().map_err(|_| "Internal")?;
            if gate
                .as_ref()
                .is_some_and(|gate| gate.after_apply == after_apply)
            {
                gate.take()
            } else {
                None
            }
        };
        if let Some(gate) = gate {
            gate.entered.send(()).map_err(|_| "TestClosed")?;
            gate.release
                .recv_timeout(Duration::from_secs(5))
                .map_err(|_| "TestTimeout")?;
        }
        Ok(())
    }
}

#[cfg(all(test, windows))]
#[path = "author_commands_review.rs"]
mod tests;
