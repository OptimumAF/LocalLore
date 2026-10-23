// Copyright 2026 LocalLore contributors. SPDX-License-Identifier: Apache-2.0
//! Native-only fixed fork identity, borrowing the existing WorkspaceRegistry owner.
//! Kotlin IO runs the worker. No Store, Java reference, native thread or new canon lives here.
use super::{Lease, WorkspaceRegistry};
use locallore::{contracts::Scope, host::WorkspaceForkRequest};
use serde::Deserialize;
use serde_json::{json, Value};
use std::{
    collections::BTreeMap,
    sync::{
        atomic::{AtomicBool, AtomicU64, Ordering},
        Arc, Mutex,
    },
};

pub const MAX_CONTROL_BYTES: usize = 4096;
pub const MAX_REPLY_BYTES: usize = 4096;
pub const MAX_FORK_OWNERS: usize = 4;
const MAX_REVISION: u64 = 9_007_199_254_740_991;
static NEXT: AtomicU64 = AtomicU64::new(0);
type Result<T> = std::result::Result<T, String>;

#[derive(Clone, Deserialize)]
#[serde(deny_unknown_fields)]
struct ForkInput {
    parent: Scope,
    child_branch: String,
    expected_parent_revision: u64,
    at_revision: u64,
}
#[derive(Deserialize)]
#[serde(deny_unknown_fields)]
struct Registration {
    version: u16,
    session: String,
    input: ForkInput,
}
fn identifier(value: &str) -> bool {
    !value.is_empty()
        && value.len() <= 64
        && value
            .bytes()
            .all(|b| b.is_ascii_alphanumeric() || b"_-".contains(&b))
}
fn input(bytes: &[u8]) -> Result<WorkspaceForkRequest> {
    if bytes.len() > MAX_CONTROL_BYTES {
        return Err("TooLarge".into());
    }
    let value: ForkInput = serde_json::from_slice(bytes).map_err(|_| "InvalidForkInput")?;
    typed(value)
}
fn typed(value: ForkInput) -> Result<WorkspaceForkRequest> {
    if !identifier(&value.parent.story)
        || !identifier(&value.parent.branch)
        || !identifier(&value.child_branch)
        || value.child_branch == value.parent.branch
        || value.expected_parent_revision > MAX_REVISION
        || value.at_revision > value.expected_parent_revision
    {
        return Err("InvalidForkInput".into());
    }
    Ok(WorkspaceForkRequest {
        parent: value.parent,
        child_branch: value.child_branch,
        expected_parent_revision: value.expected_parent_revision,
        at_revision: value.at_revision,
    })
}
fn category(value: &str) -> &str {
    match value {
        "InvalidForkInput"
        | "ForkConsentRequired"
        | "InvalidHandle"
        | "InvalidToken"
        | "Busy"
        | "Closed"
        | "Scope"
        | "Stale"
        | "Cancelled"
        | "Mismatch"
        | "RetryMismatch"
        | "Rule"
        | "NotFound"
        | "UnknownStory"
        | "Malformed"
        | "Version"
        | "Unsupported"
        | "TooLarge"
        | "Integrity"
        | "Database"
        | "Full"
        | "WorkspaceLimit"
        | "Internal" => value,
        _ => "Internal",
    }
}
fn bytes(work: impl FnOnce() -> Result<Value>) -> Vec<u8> {
    let result = std::panic::catch_unwind(std::panic::AssertUnwindSafe(work))
        .unwrap_or_else(|_| Err("Internal".into()));
    let value = match result {
        Ok(data) => json!({"version":1,"status":"ok","data":data}),
        Err(error) => json!({"version":1,"status":"rejected","error":category(&error)}),
    };
    let encoded = serde_json::to_vec(&value).unwrap_or_default();
    if encoded.is_empty() || encoded.len() > MAX_REPLY_BYTES {
        serde_json::to_vec(&json!({"version":1,"status":"rejected","error":"TooLarge"})).unwrap()
    } else {
        encoded
    }
}
#[derive(Default)]
pub(super) struct ForkRegistry {
    // At most one operation (including terminal status) per existing workspace lease.
    operations: Mutex<BTreeMap<u64, Arc<Operation>>>,
}
struct Operation {
    id: u64,
    owner: Arc<Lease>,
    session: String,
    input: WorkspaceForkRequest,
    cancel: AtomicBool,
    phase: Mutex<Phase>,
}
enum Phase {
    Registered,
    Running,
    Terminal(Result<Value>),
}
impl ForkRegistry {
    pub(super) fn retire(&self, handle: u64) {
        // Never take Host/mutation/control while holding this short registry lock.
        let operation = self
            .operations
            .lock()
            .unwrap_or_else(|e| e.into_inner())
            .remove(&handle);
        if let Some(operation) = operation {
            operation.cancel.store(true, Ordering::SeqCst);
        }
    }
    fn operation(&self, handle: u64, id: u64) -> Result<Arc<Operation>> {
        self.operations
            .lock()
            .map_err(|_| "Internal")?
            .get(&handle)
            .filter(|op| op.id == id)
            .cloned()
            .ok_or("InvalidToken".into())
    }
}
impl Operation {
    fn cancelled(&self) -> bool {
        self.cancel.load(Ordering::SeqCst) || self.owner.closed.load(Ordering::SeqCst)
    }
    fn status(&self) -> Result<Value> {
        let phase = self.phase.lock().map_err(|_| "Internal")?;
        let (name, result, error) = match &*phase {
            Phase::Registered => ("registered", Value::Null, Value::Null),
            Phase::Running => ("running", Value::Null, Value::Null),
            Phase::Terminal(Ok(result)) => ("completed", result.clone(), Value::Null),
            Phase::Terminal(Err(error)) => ("rejected", Value::Null, json!(category(error))),
        };
        Ok(
            json!({"operation":self.id,"phase":name,"cancel_requested":self.cancel.load(Ordering::SeqCst),"result":result,"error":error}),
        )
    }
}
impl WorkspaceRegistry {
    pub(super) fn fork_retire_owner(&self, handle: u64) {
        // Close admission BEFORE the operation-map lock: a concurrent register
        // either observes closed or is subsequently removed/cancelled by retire.
        let owner = self
            .entries
            .lock()
            .unwrap_or_else(|e| e.into_inner())
            .leases
            .get(&handle)
            .cloned();
        if let Some(owner) = owner {
            owner.closed.store(true, Ordering::SeqCst);
        }
        self.forks.retire(handle);
    }
    fn fork_owner(&self, handle: u64) -> Result<Arc<Lease>> {
        let owner = self
            .entries
            .lock()
            .map_err(|_| "Internal")?
            .leases
            .get(&handle)
            .cloned()
            .ok_or("InvalidHandle")?;
        if owner.closed.load(Ordering::SeqCst) {
            return Err("InvalidHandle".into());
        }
        Ok(owner)
    }
    fn fork_with_owner<T>(
        &self,
        handle: u64,
        owner: &Arc<Lease>,
        work: impl FnOnce() -> Result<T>,
    ) -> Result<T> {
        let _mutation = self.mutation.lock().map_err(|_| "Internal")?;
        let actual = self.fork_owner(handle)?;
        if !Arc::ptr_eq(&actual, owner) {
            return Err("InvalidHandle".into());
        }
        let _control = owner.control.lock().map_err(|_| "Internal")?;
        if owner.closed.load(Ordering::SeqCst) {
            return Err("InvalidHandle".into());
        }
        work()
    }
    /// Registers exact native consent before Kotlin dispatches its IO worker.
    /// A duplicate pending registration returns the SAME operation; changed input is Busy.
    pub fn fork_register(&self, handle: u64, request: &[u8], consent: bool) -> Vec<u8> {
        bytes(|| {
            if !consent {
                return Err("ForkConsentRequired".into());
            }
            if request.len() > MAX_CONTROL_BYTES {
                return Err("TooLarge".into());
            }
            let registration: Registration =
                serde_json::from_slice(request).map_err(|_| "InvalidForkInput")?;
            if registration.version != 1 {
                return Err("Version".into());
            }
            if registration.session.is_empty() || registration.session.len() > 128 {
                return Err("InvalidForkInput".into());
            }
            let input = typed(registration.input)?;
            let owner = self.fork_owner(handle)?;
            let mut operations = self.forks.operations.lock().map_err(|_| "Internal")?;
            if owner.closed.load(Ordering::SeqCst) {
                return Err("InvalidHandle".into());
            }
            if let Some(old) = operations.get(&handle) {
                let terminal = matches!(
                    *old.phase.lock().map_err(|_| "Internal")?,
                    Phase::Terminal(_)
                );
                if !terminal {
                    if Arc::ptr_eq(&old.owner, &owner)
                        && old.session == registration.session
                        && old.input == input
                    {
                        return old.status();
                    }
                    return Err("Busy".into());
                }
            } else if operations.len() >= MAX_FORK_OWNERS {
                return Err("WorkspaceLimit".into());
            }
            let id = NEXT
                .fetch_update(Ordering::SeqCst, Ordering::SeqCst, |id| {
                    id.checked_add(1).filter(|id| *id <= i64::MAX as u64)
                })
                .map_err(|_| "WorkspaceLimit")?
                + 1;
            let operation = Arc::new(Operation {
                id,
                owner,
                session: registration.session,
                input,
                cancel: AtomicBool::new(false),
                phase: Mutex::new(Phase::Registered),
            });
            let result = operation.status()?;
            operations.insert(handle, operation);
            Ok(result)
        })
    }
    /// One worker, no native spawn. Host/Store alone validate/commit the fork.
    pub fn fork_run(&self, handle: u64, id: u64) -> Vec<u8> {
        bytes(|| {
            let operation = self.forks.operation(handle, id)?;
            if !Arc::ptr_eq(&self.fork_owner(handle)?, &operation.owner) {
                return Err("InvalidHandle".into());
            }
            {
                let mut phase = operation.phase.lock().map_err(|_| "Internal")?;
                match &*phase {
                    Phase::Registered => *phase = Phase::Running,
                    Phase::Running => return Err("Busy".into()),
                    Phase::Terminal(_) => {
                        drop(phase);
                        return operation.status();
                    }
                }
            }
            // Contain trusted boundary panics and always settle the one worker status.
            let result = std::panic::catch_unwind(std::panic::AssertUnwindSafe(|| {
                self.fork_with_owner(handle, &operation.owner, || {
                    if operation.cancelled() {
                        return Err("Cancelled".into());
                    }
                    let outcome = operation.owner.host.fork_branch(
                        &operation.session,
                        &operation.input,
                        &|| operation.cancelled(),
                    )?;
                    // A committed outcome wins cancellation arriving after Host/Store returned.
                    Ok(json!({"kind":"fork","outcome":outcome}))
                })
            }))
            .unwrap_or_else(|_| Err("Internal".into()));
            *operation.phase.lock().map_err(|_| "Internal")? = Phase::Terminal(result);
            operation.status()
        })
    }
    pub fn fork_status(&self, handle: u64, id: u64) -> Vec<u8> {
        bytes(|| {
            let operation = self.forks.operation(handle, id)?;
            if !Arc::ptr_eq(&self.fork_owner(handle)?, &operation.owner) {
                return Err("InvalidHandle".into());
            }
            operation.status()
        })
    }
    pub fn fork_cancel(&self, handle: u64, id: u64) -> Vec<u8> {
        bytes(|| {
            let operation = self.forks.operation(handle, id)?;
            if !Arc::ptr_eq(&self.fork_owner(handle)?, &operation.owner) {
                return Err("InvalidHandle".into());
            }
            operation.cancel.store(true, Ordering::SeqCst);
            {
                let mut phase = operation.phase.lock().map_err(|_| "Internal")?;
                if matches!(*phase, Phase::Registered) {
                    *phase = Phase::Terminal(Err("Cancelled".into()));
                }
            }
            operation.status()
        })
    }
    /// Read-only recovery, including process restart. NEVER executes/recreates a fork.
    pub fn fork_lookup(&self, handle: u64, request: &[u8]) -> Vec<u8> {
        bytes(|| {
            let input = input(request)?;
            let owner = self.fork_owner(handle)?;
            self.fork_with_owner(handle, &owner, || {
                let reply = owner.host.call(&serde_json::to_vec(&json!({"version":1,"command":{"op":"branches","story":input.parent.story}})).map_err(|_| "Internal")?);
                if reply["status"] != "ok" { return Err(reply["error"].as_str().unwrap_or("Internal").into()); }
                let branches = reply["data"]["branches"].as_array().ok_or("Internal")?;
                let row = branches.iter().find(|row| row["scope"]["branch"] == input.child_branch);
                let Some(row) = row else { return Ok(json!({"version":1,"kind":"fork_lookup","found":false,"outcome":null})); };
                if row["scope"]["story"] != input.parent.story || row["parent_branch"] != input.parent.branch
                    || row["fork_revision"].as_u64() != Some(input.at_revision) { return Err("Mismatch".into()); }
                if row["retired"] != false { return Err("Closed".into()); }
                let head = row["revision"].as_u64().filter(|head| *head >= input.at_revision && *head <= MAX_REVISION).ok_or("Internal")?;
                Ok(json!({"version":1,"kind":"fork_lookup","found":true,"outcome":{"version":1,
                    "scope":{"story":input.parent.story,"branch":input.child_branch},"parent":input.parent,
                    "fork_revision":input.at_revision,"head_revision":head,"created":false}}))
            })
        })
    }
}

#[cfg(target_os = "android")]
mod android {
    use super::*;
    use jni::{
        objects::{JByteArray, JClass},
        sys::{jboolean, jbyteArray, jlong},
        JNIEnv,
    };
    fn request(env: &JNIEnv<'_>, input: JByteArray<'_>) -> Result<Vec<u8>> {
        if input.is_null() {
            return Err("Malformed".into());
        }
        let length = env.get_array_length(&input).map_err(|_| "Malformed")?;
        if length < 0 || length as usize > MAX_CONTROL_BYTES {
            return Err("TooLarge".into());
        }
        env.convert_byte_array(input)
            .map_err(|_| "Malformed".into())
    }
    fn output(env: &JNIEnv<'_>, result: Vec<u8>) -> jbyteArray {
        if env.exception_check().unwrap_or(true) {
            return std::ptr::null_mut();
        }
        env.byte_array_from_slice(&result)
            .map_or(std::ptr::null_mut(), |value| value.into_raw())
    }
    #[no_mangle]
    pub extern "system" fn Java_org_locallore_app_NativeFork_register(
        env: JNIEnv<'_>,
        _: JClass<'_>,
        handle: jlong,
        input: JByteArray<'_>,
        consent: jboolean,
    ) -> jbyteArray {
        let result = match request(&env, input) {
            Ok(input) => {
                super::super::android::registry().fork_register(handle as u64, &input, consent != 0)
            }
            Err(error) => bytes(|| Err(error)),
        };
        output(&env, result)
    }
    #[no_mangle]
    pub extern "system" fn Java_org_locallore_app_NativeFork_run(
        env: JNIEnv<'_>,
        _: JClass<'_>,
        handle: jlong,
        operation: jlong,
    ) -> jbyteArray {
        output(
            &env,
            super::super::android::registry().fork_run(handle as u64, operation as u64),
        )
    }
    #[no_mangle]
    pub extern "system" fn Java_org_locallore_app_NativeFork_status(
        env: JNIEnv<'_>,
        _: JClass<'_>,
        handle: jlong,
        operation: jlong,
    ) -> jbyteArray {
        output(
            &env,
            super::super::android::registry().fork_status(handle as u64, operation as u64),
        )
    }
    #[no_mangle]
    pub extern "system" fn Java_org_locallore_app_NativeFork_cancel(
        env: JNIEnv<'_>,
        _: JClass<'_>,
        handle: jlong,
        operation: jlong,
    ) -> jbyteArray {
        output(
            &env,
            super::super::android::registry().fork_cancel(handle as u64, operation as u64),
        )
    }
    #[no_mangle]
    pub extern "system" fn Java_org_locallore_app_NativeFork_lookup(
        env: JNIEnv<'_>,
        _: JClass<'_>,
        handle: jlong,
        input: JByteArray<'_>,
    ) -> jbyteArray {
        let result = match request(&env, input) {
            Ok(input) => super::super::android::registry().fork_lookup(handle as u64, &input),
            Err(error) => bytes(|| Err(error)),
        };
        output(&env, result)
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use std::{
        path::PathBuf,
        time::{Duration, Instant},
    };
    fn fixture() -> (Arc<WorkspaceRegistry>, u64, Vec<u8>, PathBuf) {
        let directory = std::env::temp_dir().join(format!(
            "locallore-fork-lock-review-{}-{}",
            std::process::id(),
            NEXT.fetch_add(1, Ordering::SeqCst)
        ));
        std::fs::create_dir(&directory).unwrap();
        let registry = Arc::new(WorkspaceRegistry::default());
        let handle = registry.open(&directory.join("stories.sqlite3")).unwrap();
        let created: Value = serde_json::from_slice(
            &registry.call(
                handle,
                &serde_json::to_vec(
                    &json!({"version":1,"command":{"op":"create","seed":"lantern-quay-v1"}}),
                )
                .unwrap(),
            ),
        )
        .unwrap();
        assert_eq!(created["status"], "ok");
        let request=serde_json::to_vec(&json!({"version":1,"session":created["data"]["session"],"input":{"parent":created["data"]["scope"],"child_branch":"held-child","expected_parent_revision":0,"at_revision":0}})).unwrap();
        (registry, handle, request, directory)
    }
    fn value(bytes: Vec<u8>) -> Value {
        serde_json::from_slice(&bytes).unwrap()
    }
    fn observed_running(registry: &WorkspaceRegistry, handle: u64, operation: u64) {
        let deadline = Instant::now() + Duration::from_secs(2);
        loop {
            if value(registry.fork_status(handle, operation))["data"]["phase"] == "running" {
                return;
            }
            assert!(
                Instant::now() < deadline,
                "actual native worker never reached Running"
            );
            std::thread::sleep(Duration::from_millis(1));
        }
    }
    #[test]
    fn one_worker_cancel_waits_for_existing_mutation_gate_without_holding_cancel_lock() {
        let (registry, handle, request, directory) = fixture();
        let operation = value(registry.fork_register(handle, &request, true))["data"]["operation"]
            .as_u64()
            .unwrap();
        let gate = registry.mutation.lock().unwrap();
        let worker_registry = registry.clone();
        let worker = std::thread::spawn(move || value(worker_registry.fork_run(handle, operation)));
        observed_running(&registry, handle, operation);
        assert_eq!(value(registry.fork_run(handle, operation))["error"], "Busy");
        assert_eq!(
            value(registry.fork_cancel(handle, operation))["data"]["cancel_requested"],
            true
        );
        drop(gate);
        assert_eq!(worker.join().unwrap()["data"]["error"], "Cancelled");
        let lookup: Value = serde_json::from_slice(&request).unwrap();
        assert_eq!(
            value(registry.fork_lookup(handle, &serde_json::to_vec(&lookup["input"]).unwrap()))
                ["data"]["found"],
            false
        );
        registry.close(handle);
        // Evidence is deliberately retained under caller-owned TEMP; no broad cleanup.
        assert!(directory.is_dir());
    }
    #[test]
    fn close_fences_new_registration_before_waiting_for_actual_worker_drain() {
        let (registry, handle, request, directory) = fixture();
        let operation = value(registry.fork_register(handle, &request, true))["data"]["operation"]
            .as_u64()
            .unwrap();
        let owner = registry.fork_owner(handle).unwrap();
        let gate = registry.mutation.lock().unwrap();
        let worker_registry = registry.clone();
        let worker = std::thread::spawn(move || value(worker_registry.fork_run(handle, operation)));
        observed_running(&registry, handle, operation);
        let close_registry = registry.clone();
        let closer = std::thread::spawn(move || close_registry.close(handle));
        let deadline = Instant::now() + Duration::from_secs(2);
        while !owner.closed.load(Ordering::SeqCst) {
            assert!(
                Instant::now() < deadline,
                "close did not retire before drain locks"
            );
            std::thread::sleep(Duration::from_millis(1));
        }
        assert_eq!(
            value(registry.fork_register(handle, &request, true))["error"],
            "InvalidHandle"
        );
        drop(gate);
        let result = worker.join().unwrap();
        closer.join().unwrap();
        assert_eq!(result["data"]["phase"], "rejected", "{result}");
        assert!(matches!(
            result["data"]["error"].as_str(),
            Some("InvalidHandle" | "Cancelled")
        ));
        assert!(registry.forks.operations.lock().unwrap().is_empty());
        let reopened = registry.open(&directory.join("stories.sqlite3")).unwrap();
        let lookup: Value = serde_json::from_slice(&request).unwrap();
        assert_eq!(
            value(registry.fork_lookup(reopened, &serde_json::to_vec(&lookup["input"]).unwrap()))
                ["data"]["found"],
            false
        );
        registry.close(reopened);
    }
}
