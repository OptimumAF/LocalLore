// Copyright 2026 LocalLore contributors. SPDX-License-Identifier: Apache-2.0
//! Legacy in-memory fixture boundary and production shared durable workspace adapter.
//! JNI owns no Java references or native threads.
pub mod archive;
#[cfg(all(target_os = "android", feature = "archive-capacity-fixture"))]
mod archive_capacity_jni;
#[cfg(target_os = "android")]
mod archive_jni;
mod play_fixture;
pub mod workspace;
use locallore::{contracts::*, engine::Engine, inference::*};
use serde::Deserialize;
use serde_json::{json, Value};
use std::{
    collections::BTreeMap,
    sync::{
        atomic::{AtomicUsize, Ordering},
        Arc, Mutex,
    },
    task::Poll,
    thread::{self, ThreadId},
    time::{Duration, Instant},
};

pub const MAX_INPUT: usize = 24_576;
pub const MAX_OUTPUT: usize = 65_536;
const MAX_SESSIONS: usize = 32;
const MAX_TURNS: usize = 64;

#[derive(Deserialize)]
#[serde(tag = "op", rename_all = "snake_case", deny_unknown_fields)]
enum Control {
    Create {
        version: u16,
    },
    Begin {
        version: u16,
        request: Request,
        mode: Mode,
    },
    Run {
        version: u16,
        operation: u64,
    },
    Commit {
        version: u16,
        operation: u64,
    },
    Cancel {
        version: u16,
        operation: u64,
    },
    Snapshot {
        version: u16,
    },
    Destroy {
        version: u16,
    },
    Stats {
        version: u16,
    },
}
#[derive(Clone, Copy, Deserialize)]
#[serde(rename_all = "snake_case")]
enum Mode {
    Accepted,
    Malformed,
    Rejected,
    Delayed,
    Failed,
}
impl Control {
    fn version(&self) -> u16 {
        match self {
            Self::Create { version }
            | Self::Begin { version, .. }
            | Self::Run { version, .. }
            | Self::Commit { version, .. }
            | Self::Cancel { version, .. }
            | Self::Snapshot { version }
            | Self::Destroy { version }
            | Self::Stats { version } => *version,
        }
    }
}
#[derive(Default)]
struct Counts {
    sessions: AtomicUsize,
    operations: AtomicUsize,
    workers: AtomicUsize,
}
struct CountGuard(Arc<Counts>);
impl Drop for CountGuard {
    fn drop(&mut self) {
        self.0.workers.fetch_sub(1, Ordering::SeqCst);
    }
}
struct Session {
    owner: ThreadId,
    inner: Mutex<SessionState>,
    counts: Arc<Counts>,
}
struct SessionState {
    engine: Engine,
    active: Option<Arc<Operation>>,
    closed: bool,
}
struct Operation {
    id: u64,
    request: Request,
    mode: Mode,
    cancel: Cancellation,
    stage: Mutex<Stage>,
    counts: Arc<Counts>,
}
enum Stage {
    Pending,
    Running,
    Ready(Box<Receipt>),
    Committed(Value),
    Cancelled,
}
impl Drop for Session {
    fn drop(&mut self) {
        self.counts.sessions.fetch_sub(1, Ordering::SeqCst);
    }
}
impl Drop for Operation {
    fn drop(&mut self) {
        self.counts.operations.fetch_sub(1, Ordering::SeqCst);
    }
}
#[derive(Default)]
struct RegistryState {
    next: u64,
    sessions: BTreeMap<u64, Arc<Session>>,
}
#[derive(Default)]
pub struct Registry {
    state: Mutex<RegistryState>,
    counts: Arc<Counts>,
}
fn reject(error: impl std::fmt::Display) -> Value {
    json!({"version":1,"status":"rejected","error":error.to_string()})
}
fn snapshot(engine: &Engine) -> Value {
    let owner = &engine.state().items["potion"].owner;
    let name = if owner == &engine.seed().player {
        "You"
    } else {
        &engine.state().actors[owner].name
    };
    json!({"revision":engine.revision(),"potion_owner":name,
        "events":engine.receipts().iter().map(|r|r.events().len()).sum::<usize>(),
        "energy":engine.state().actors[&engine.seed().player].energy,
        "mira_observations":engine.character_context("mira",engine.scope(),engine.revision()).unwrap().observations.len(),
        "sable_observations":engine.character_context("sable",engine.scope(),engine.revision()).unwrap().observations.len()})
}
impl Registry {
    /// Panic containment also covers poisoned locks. Error replies never echo input or private state.
    pub fn call(&self, handle: u64, bytes: &[u8]) -> Vec<u8> {
        let result = std::panic::catch_unwind(std::panic::AssertUnwindSafe(|| {
            if bytes.len() > MAX_INPUT {
                return reject("TooLarge");
            }
            let Ok(control) = serde_json::from_slice::<Control>(bytes) else {
                return reject("Malformed");
            };
            if control.version() != 1 {
                return reject("Version");
            }
            self.dispatch(handle, control)
        }))
        .unwrap_or_else(|_| reject("Internal"));
        let output = serde_json::to_vec(&result).unwrap_or_default();
        if output.len() > MAX_OUTPUT {
            serde_json::to_vec(&reject("TooLarge")).unwrap()
        } else {
            output
        }
    }
    fn dispatch(&self, handle: u64, control: Control) -> Value {
        if let Control::Stats { .. } = control {
            if handle != 0 {
                return reject("InvalidHandle");
            }
            return json!({"version":1,"status":"stats","live_sessions":self.state.lock().unwrap().sessions.len(),
                "retained_sessions":self.counts.sessions.load(Ordering::SeqCst),
                "operations":self.counts.operations.load(Ordering::SeqCst),"workers":self.counts.workers.load(Ordering::SeqCst)});
        }
        if let Control::Create { .. } = control {
            if handle != 0 {
                return reject("InvalidHandle");
            }
            let mut registry = self.state.lock().unwrap();
            if self.counts.sessions.load(Ordering::SeqCst) >= MAX_SESSIONS {
                return reject("SessionLimit");
            }
            let Some(id) = registry
                .next
                .checked_add(1)
                .filter(|n| *n <= i64::MAX as u64)
            else {
                return reject("SessionLimit");
            };
            registry.next = id;
            let engine = Engine::new(
                serde_json::from_str(include_str!("../../../fixtures/lantern_quay.json")).unwrap(),
            )
            .unwrap();
            let initial = snapshot(&engine);
            self.counts.sessions.fetch_add(1, Ordering::SeqCst);
            registry.sessions.insert(
                id,
                Arc::new(Session {
                    owner: thread::current().id(),
                    inner: Mutex::new(SessionState {
                        engine,
                        active: None,
                        closed: false,
                    }),
                    counts: self.counts.clone(),
                }),
            );
            return json!({"version":1,"status":"session","handle":id,"snapshot":initial});
        }
        let session = { self.state.lock().unwrap().sessions.get(&handle).cloned() };
        let Some(session) = session else {
            return reject("InvalidHandle");
        };
        if let Control::Run { operation, .. } = control {
            return self.run(&session, operation);
        }
        if !matches!(control, Control::Cancel { .. } | Control::Destroy { .. })
            && session.owner != thread::current().id()
        {
            return reject("WrongThread");
        }
        let mut state = session.inner.lock().unwrap();
        if state.closed {
            return reject("InvalidHandle");
        }
        match control {
            Control::Begin { request, mode, .. } => {
                if let Some(op) = &state.active {
                    if matches!(
                        *op.stage.lock().unwrap(),
                        Stage::Pending | Stage::Running | Stage::Ready(_)
                    ) {
                        return reject("Busy");
                    }
                }
                if let Err(e) = state.engine.recorded(&request).and_then(|r| {
                    if r.is_some() {
                        Ok(())
                    } else if state.engine.receipts().len() >= MAX_TURNS {
                        Err(Error::TooLarge)
                    } else {
                        state.engine.preflight(&request)
                    }
                }) {
                    return reject(e);
                }
                let id = {
                    let mut r = self.state.lock().unwrap();
                    if self.counts.operations.load(Ordering::SeqCst) >= 64 {
                        return reject("OperationLimit");
                    }
                    let Some(id) = r.next.checked_add(1).filter(|n| *n <= i64::MAX as u64) else {
                        return reject("OperationLimit");
                    };
                    r.next = id;
                    self.counts.operations.fetch_add(1, Ordering::SeqCst);
                    id
                };
                state.active = Some(Arc::new(Operation {
                    id,
                    request,
                    mode,
                    cancel: Cancellation::default(),
                    stage: Mutex::new(Stage::Pending),
                    counts: self.counts.clone(),
                }));
                json!({"version":1,"status":"started","operation":id})
            }
            Control::Commit { operation, .. } => {
                let Some(op) = &state.active else {
                    return reject("InvalidOperation");
                };
                if op.id != operation {
                    return reject("InvalidOperation");
                }
                let op = op.clone();
                let mut stage = op.stage.lock().unwrap();
                if let Stage::Committed(reply) = &*stage {
                    return reply.clone();
                }
                if op.cancel.is_cancelled() {
                    return reject("Cancelled");
                }
                let Stage::Ready(receipt) = &*stage else {
                    return reject("InvalidOperation");
                };
                let proposal = match Engine::proposal(&op.request) {
                    Ok(p) => p,
                    Err(e) => return reject(e),
                };
                match state
                    .engine
                    .commit(&op.request, &proposal, receipt.narration())
                {
                    Ok(receipt) => {
                        let reply = json!({"version":1,"status":"accepted","snapshot":snapshot(&state.engine),"narration":receipt.narration(),"receipt":receipt});
                        *stage = Stage::Committed(reply.clone());
                        reply
                    }
                    Err(e) => reject(e),
                }
            }
            Control::Cancel { operation, .. } => {
                let Some(op) = &state.active else {
                    return reject("InvalidOperation");
                };
                if op.id != operation {
                    return reject("InvalidOperation");
                }
                let mut stage = op.stage.lock().unwrap();
                if matches!(*stage, Stage::Committed(_)) {
                    return json!({"version":1,"status":"already_committed"});
                }
                op.cancel.cancel();
                *stage = Stage::Cancelled;
                json!({"version":1,"status":"cancelled"})
            }
            Control::Snapshot { .. } => {
                json!({"version":1,"status":"snapshot","snapshot":snapshot(&state.engine)})
            }
            Control::Destroy { .. } => {
                state.closed = true;
                if let Some(op) = state.active.take() {
                    op.cancel.cancel();
                }
                self.state.lock().unwrap().sessions.remove(&handle);
                json!({"version":1,"status":"closed"})
            }
            _ => reject("Malformed"),
        }
    }
    fn run(&self, session: &Arc<Session>, operation: u64) -> Value {
        if session.owner == thread::current().id() {
            return reject("WrongThread");
        }
        let (op, mut draft) = {
            let state = session.inner.lock().unwrap();
            if state.closed {
                return reject("InvalidHandle");
            }
            let Some(op) = &state.active else {
                return reject("InvalidOperation");
            };
            if op.id != operation {
                return reject("InvalidOperation");
            }
            let mut stage = op.stage.lock().unwrap();
            if !matches!(*stage, Stage::Pending) {
                return reject("InvalidOperation");
            }
            *stage = Stage::Running;
            (op.clone(), state.engine.clone())
        };
        self.counts.workers.fetch_add(1, Ordering::SeqCst);
        let _worker = CountGuard(self.counts.clone());
        let fake = match op.mode {
            Mode::Malformed => FakeMode::Malformed,
            Mode::Rejected => FakeMode::Rejected,
            Mode::Failed => FakeMode::Failed,
            _ => FakeMode::Accepted,
        };
        let mut provider = TimedFake {
            inner: FakeProvider::new(fake),
            ready: Instant::now()
                + Duration::from_millis(if matches!(op.mode, Mode::Delayed) {
                    5000
                } else {
                    40
                }),
        };
        let result = execute(
            &mut draft,
            &op.request,
            &mut provider,
            &op.cancel,
            Budget {
                max_pending_polls: 1024,
                deadline_ms: 10_000,
                ..Budget::default()
            },
        );
        let state = session.inner.lock().unwrap();
        let mut stage = op.stage.lock().unwrap();
        if state.closed
            || op.cancel.is_cancelled()
            || state.active.as_ref().map(|o| o.id) != Some(operation)
        {
            return reject("Cancelled");
        }
        match result {
            Ok(receipt) => {
                // Bound the complete accepted reply before touching the authoritative engine.
                let reply = json!({"version":1,"status":"accepted","snapshot":snapshot(&draft),
                    "narration":receipt.narration(),"receipt":receipt});
                if serde_json::to_vec(&reply).unwrap().len() > MAX_OUTPUT {
                    *stage = Stage::Cancelled;
                    return reject("TooLarge");
                }
                *stage = Stage::Ready(Box::new(receipt));
                json!({"version":1,"status":"prepared","operation":operation})
            }
            Err(e) => {
                *stage = Stage::Cancelled;
                reject(e)
            }
        }
    }
}
struct TimedFake {
    inner: FakeProvider,
    ready: Instant,
}
impl InferenceProvider for TimedFake {
    fn poll(
        &mut self,
        request: &GenerationRequest,
        cancel: &Cancellation,
    ) -> Poll<Result<Vec<u8>, Error>> {
        if cancel.is_cancelled() {
            return Poll::Ready(Err(Error::Cancelled));
        }
        if Instant::now() < self.ready {
            thread::sleep(Duration::from_millis(5));
            Poll::Pending
        } else {
            self.inner.poll(request, cancel)
        }
    }
}

#[cfg(target_os = "android")]
mod android {
    use super::*;
    use jni::{
        objects::{JByteArray, JObject},
        sys::{jbyteArray, jlong},
        JNIEnv,
    };
    use std::sync::OnceLock;
    static REGISTRY: OnceLock<Registry> = OnceLock::new();
    #[no_mangle]
    pub extern "system" fn Java_org_locallore_app_NativeBridge_call(
        env: JNIEnv<'_>,
        _: JObject<'_>,
        handle: jlong,
        input: JByteArray<'_>,
    ) -> jbyteArray {
        // No borrowed elements, global refs, callbacks, or JNIEnv leave this invocation.
        let reply = std::panic::catch_unwind(std::panic::AssertUnwindSafe(|| {
            if input.is_null() {
                return serde_json::to_vec(&reject("Malformed")).unwrap();
            }
            let Ok(len) = env.get_array_length(&input) else {
                return Vec::new();
            };
            if len as usize > MAX_INPUT {
                return serde_json::to_vec(&reject("TooLarge")).unwrap();
            }
            let Ok(bytes) = env.convert_byte_array(&input) else {
                return Vec::new();
            };
            REGISTRY
                .get_or_init(Registry::default)
                .call(handle as u64, &bytes)
        }))
        .unwrap_or_else(|_| serde_json::to_vec(&reject("Internal")).unwrap());
        // If JNI raised (e.g. OOM), return with that exception pending; do not make more JNI calls.
        if reply.is_empty() {
            return std::ptr::null_mut();
        }
        env.byte_array_from_slice(&reply)
            .map(|a| a.into_raw())
            .unwrap_or(std::ptr::null_mut())
    }
}
