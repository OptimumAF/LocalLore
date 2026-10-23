// Copyright 2026 LocalLore contributors. SPDX-License-Identifier: Apache-2.0
//! Trusted app-private workspace adapter. Calls belong on Kotlin IO workers, never the UI thread.
#[path = "branch_fork.rs"]
pub mod branch_fork;
use locallore::host::{Host, MAX_INPUT, MAX_OUTPUT};
use serde_json::{json, Value};
use std::{
    collections::BTreeMap,
    path::{Path, PathBuf},
    sync::{
        atomic::{AtomicBool, Ordering},
        Arc, Mutex,
    },
};

#[derive(Default)]
pub struct WorkspaceRegistry {
    entries: Mutex<RegistryState>,
    mutation: Mutex<()>,
    forks: branch_fork::ForkRegistry,
}
#[derive(Default)]
struct RegistryState {
    next: u64,
    opening: usize,
    leases: BTreeMap<u64, Arc<Lease>>,
}
struct Opening<'a>(&'a WorkspaceRegistry);
impl Drop for Opening<'_> {
    fn drop(&mut self) {
        if let Ok(mut entries) = self.0.entries.lock() {
            entries.opening -= 1;
        }
    }
}
struct Lease {
    host: Host,
    database: PathBuf,
    closed: AtomicBool,
    control: Mutex<()>,
}
impl Lease {
    fn call(&self, bytes: &[u8]) -> Value {
        // Generation bypasses the control gate. Host cancellation/session fences cover its
        // completion; neither cancel nor disposal waits for the fake or future model provider.
        let prepare = serde_json::from_slice::<Value>(bytes)
            .ok()
            .is_some_and(|value| value["command"]["op"] == "prepare");
        if prepare {
            if self.closed.load(Ordering::SeqCst) {
                return rejected("InvalidHandle");
            }
            self.host.call(bytes)
        } else {
            let _control = self.control.lock().unwrap();
            if self.closed.load(Ordering::SeqCst) {
                return rejected("InvalidHandle");
            }
            self.host.call(bytes)
        }
    }
}
fn rejected(category: &str) -> Value {
    json!({"version":1,"status":"rejected","error":category})
}
impl WorkspaceRegistry {
    /// The path is supplied by native app construction, never a Host wire command.
    pub fn open(&self, path: &Path) -> Result<u64, String> {
        let _mutation = self.mutation.lock().map_err(|_| "Internal")?;
        let id = {
            let mut entries = self.entries.lock().map_err(|_| "Internal")?;
            if entries.leases.len() + entries.opening >= 4 {
                return Err("WorkspaceLimit".into());
            }
            let id = entries
                .next
                .checked_add(1)
                .filter(|n| *n <= i64::MAX as u64)
                .ok_or("WorkspaceLimit")?;
            entries.next = id;
            entries.opening += 1;
            id
        };
        let _opening = Opening(self);
        // Database validation/replay can block. Other owners must still be able to cancel/close.
        let host = locallore_workspace::open(path, false)?;
        let database = path.canonicalize().map_err(|_| "Io")?;
        crate::play_fixture::configure(&host)?;
        self.entries.lock().map_err(|_| "Internal")?.leases.insert(
            id,
            Arc::new(Lease {
                host,
                database,
                closed: AtomicBool::new(false),
                control: Mutex::new(()),
            }),
        );
        Ok(id)
    }
    pub fn call(&self, handle: u64, bytes: &[u8]) -> Vec<u8> {
        let result = std::panic::catch_unwind(std::panic::AssertUnwindSafe(|| {
            if bytes.len() > MAX_INPUT {
                return rejected("TooLarge");
            }
            let lease = self.entries.lock().unwrap().leases.get(&handle).cloned();
            let Some(lease) = lease else {
                return rejected("InvalidHandle");
            };
            // Prepare can run a slow provider. Its completion is fenced by Host session
            // invalidation; submit/commit/resume/open cannot cross a deletion transaction.
            let prepare = serde_json::from_slice::<Value>(bytes)
                .ok()
                .is_some_and(|value| value["command"]["op"] == "prepare");
            let _mutation = if prepare {
                None
            } else {
                Some(self.mutation.lock().unwrap())
            };
            lease.call(bytes)
        }))
        .unwrap_or_else(|_| rejected("Internal"));
        let reply = serde_json::to_vec(&result).unwrap_or_default();
        if reply.len() > MAX_OUTPUT {
            serde_json::to_vec(&rejected("TooLarge")).unwrap()
        } else {
            reply
        }
    }
    pub fn close(&self, handle: u64) {
        // Cancel registered/running native forks before waiting for their existing owner locks.
        self.fork_retire_owner(handle);
        let _mutation = self.mutation.lock().unwrap();
        // Remove before waiting for the Host; no new work can acquire this handle.
        let lease = self.entries.lock().unwrap().leases.remove(&handle);
        if let Some(lease) = lease {
            let _control = lease.control.lock().unwrap();
            lease.closed.store(true, Ordering::SeqCst);
            lease.host.close_all();
        }
    }
    /// Serialize accepted deletion and in-process session invalidation with all
    /// session-creating and committing calls. No entries lock is held during Host work.
    pub fn with_story_deletion<T>(
        &self,
        database: &Path,
        story: &str,
        delete: impl FnOnce() -> Result<T, &'static str>,
    ) -> Result<T, &'static str> {
        let _mutation = self.mutation.lock().map_err(|_| "Internal")?;
        let database = database.canonicalize().map_err(|_| "Io")?;
        let leases: Vec<_> = self
            .entries
            .lock()
            .map_err(|_| "Internal")?
            .leases
            .values()
            .filter(|lease| lease.database == database)
            .cloned()
            .collect();
        let deleted = delete()?;
        for lease in leases {
            lease.host.invalidate_story(story);
        }
        Ok(deleted)
    }
    pub fn with_branch_deletion<T>(
        &self,
        database: &Path,
        story: &str,
        delete: impl FnOnce() -> Result<(T, Vec<String>), &'static str>,
    ) -> Result<T, &'static str> {
        let _mutation = self.mutation.lock().map_err(|_| "Internal")?;
        let database = database.canonicalize().map_err(|_| "Io")?;
        let leases: Vec<_> = self
            .entries
            .lock()
            .map_err(|_| "Internal")?
            .leases
            .values()
            .filter(|lease| lease.database == database)
            .cloned()
            .collect();
        let (deleted, invalidated) = delete()?;
        for lease in leases {
            lease.host.invalidate_branches(story, &invalidated);
        }
        Ok(deleted)
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    #[test]
    fn retirement_during_two_observed_running_workers_fences_parent_and_preserves_child() {
        use crate::archive::ArchiveRegistry;
        use locallore::contracts::Scope;
        use locallore_storage::{validate_archive, Store};
        let directory = std::env::temp_dir().join(format!(
            "locallore-running-retention-{}-{}",
            std::process::id(),
            std::time::SystemTime::now()
                .duration_since(std::time::UNIX_EPOCH)
                .unwrap()
                .as_nanos()
        ));
        std::fs::create_dir(&directory).unwrap();
        let database = directory.join("stories.sqlite3");
        let staging = directory.join("staging");
        std::fs::create_dir(&staging).unwrap();
        let mut store = Store::open(&database, None).unwrap();
        let archive = validate_archive(
            include_bytes!(
                "../../../apps/android/app/src/androidTest/assets/parent-retention-v1.json"
            ),
            &|| false,
        )
        .unwrap();
        store.import_archive(archive, &|| false).unwrap();
        let parent = Scope {
            story: "parent-retention-fixture".into(),
            branch: "parent".into(),
        };
        let child = Scope {
            branch: "child".into(),
            ..parent.clone()
        };
        let sibling = Scope {
            branch: "sibling".into(),
            ..parent.clone()
        };
        let child_before = store.resume(&child).unwrap().engine.canonical_bytes();
        let sibling_before = store.resume(&sibling).unwrap().engine.canonical_bytes();
        drop(store);
        let registry = WorkspaceRegistry::default();
        let grant = ArchiveRegistry::default();
        let handle = registry.open(&database).unwrap();
        let owner = grant.open(&database, &staging).unwrap();
        let lease = registry.entries.lock().unwrap().leases[&handle].clone();
        let invoke = |command: Value| {
            serde_json::from_slice::<Value>(&registry.call(
                handle,
                &serde_json::to_vec(&json!({"version":1,"command":command})).unwrap(),
            ))
            .unwrap()
        };
        let accepted = |reply: Value| {
            assert_eq!(reply["status"], "ok", "{reply}");
            reply["data"].clone()
        };
        let pa = accepted(invoke(json!({"op":"resume","scope":parent})))["session"].clone();
        let ch = accepted(invoke(json!({"op":"resume","scope":child})))["session"].clone();
        for (session, scope, head, turn) in [
            (&pa, &parent, 5, "running-parent"),
            (&ch, &child, 4, "running-child"),
        ] {
            assert_eq!(
                accepted(invoke(
                    json!({"op":"free_text","session":session,"request":{
                        "version":1,"scope":scope,"turn":turn,"expected_revision":head,
                        "intent":{"kind":"free_text","value":{"kind":"action","text":"I give my last potion to Mira."}}
                    }})
                ))["phase"],
                "queued"
            );
        }
        std::thread::scope(|threads| {
            let parent_worker = threads.spawn(|| {
                invoke(json!({"op":"prepare","session":pa,"scope":parent,"turn":"running-parent"}))
            });
            let child_worker = threads.spawn(|| {
                invoke(json!({"op":"prepare","session":ch,"scope":child,"turn":"running-child"}))
            });
            let deadline = std::time::Instant::now() + std::time::Duration::from_secs(5);
            while lease.host.live_counts().1 < 2 {
                assert!(
                    std::time::Instant::now() < deadline,
                    "both actual workers must start"
                );
                std::thread::sleep(std::time::Duration::from_millis(1));
            }
            let running = || {
                assert_eq!(lease.host.live_counts().1, 2);
                for (session, scope, turn) in [
                    (&pa, &parent, "running-parent"),
                    (&ch, &child, "running-child"),
                ] {
                    assert_eq!(
                        accepted(invoke(
                            json!({"op":"turn_status","session":session,"scope":scope,"turn":turn})
                        ))["phase"],
                        "running"
                    );
                }
            };
            running();
            let plan: Value = serde_json::from_slice(
                &grant.prepare_branch_delete(
                    owner,
                    &serde_json::to_vec(
                        &json!({"story":parent.story,"branch":parent.branch,"expected_revision":5}),
                    )
                    .unwrap(),
                ),
            )
            .unwrap();
            let token = accepted(plan)["token"].as_u64().unwrap();
            // Prove actual native work is still running at the deletion boundary.
            running();
            let result: Value =
                serde_json::from_slice(&grant.commit_branch_delete(owner, token, &registry))
                    .unwrap();
            assert_eq!(accepted(result)["retained_through_revision"], 4);
            assert_eq!(parent_worker.join().unwrap()["error"], "Closed");
            assert_eq!(accepted(child_worker.join().unwrap())["phase"], "ready");
        });
        assert_eq!(lease.host.live_counts().1, 0);
        let mut store = Store::open(&database, None).unwrap();
        assert!(!store.is_branch_active(&parent).unwrap());
        assert_eq!(
            store.resume(&child).unwrap().engine.canonical_bytes(),
            child_before
        );
        assert_eq!(
            store.resume(&sibling).unwrap().engine.canonical_bytes(),
            sibling_before
        );
        drop(store);
        let commit = json!({"op":"commit","session":ch,"scope":child,"turn":"running-child"});
        let receipt = accepted(invoke(commit.clone()));
        assert_eq!(receipt["phase"], "committed");
        assert_eq!(accepted(invoke(commit)), receipt);
        assert_eq!(
            invoke(json!({"op":"resume","scope":parent}))["error"],
            "NotFound"
        );
        registry.close(handle);
        assert_eq!(lease.host.live_counts(), (0, 0));
        drop(lease);
        grant.close(owner);
        std::fs::remove_dir_all(directory).unwrap();
    }
    #[test]
    fn scripted_prepare_bypasses_control_gate_and_close_drains_host_worker() {
        let host = Host::new(false);
        crate::play_fixture::configure(&host).unwrap();
        let lease = Arc::new(Lease {
            host,
            database: PathBuf::new(), // This fixture uses an in-memory Host, not a disk Store.
            closed: AtomicBool::new(false),
            control: Mutex::new(()),
        });
        let registry = Arc::new(WorkspaceRegistry {
            mutation: Mutex::new(()),
            forks: Default::default(),
            entries: Mutex::new(RegistryState {
                next: 1,
                opening: 0,
                leases: BTreeMap::from([(1, lease.clone())]),
            }),
        });
        let invoke = |command: Value| {
            serde_json::from_slice::<Value>(&registry.call(
                1,
                &serde_json::to_vec(&json!({"version":1,"command":command})).unwrap(),
            ))
            .unwrap()
        };
        let session = invoke(json!({"op":"create","seed":"lantern-quay-v1"}))["data"].clone();
        let request = json!({"version":1,"scope":session["scope"],"turn":"close-fixture","expected_revision":0,
            "intent":{"kind":"free_text","value":{"kind":"action","text":"I give my last potion to Mira."}}});
        assert_eq!(
            invoke(json!({"op":"free_text","session":session["session"],"request":request}))
                ["data"]["phase"],
            "queued"
        );
        std::thread::scope(|threads| {
            let worker = threads.spawn(|| invoke(json!({"op":"prepare","session":session["session"],"scope":session["scope"],"turn":"close-fixture"})));
            let deadline = std::time::Instant::now() + std::time::Duration::from_secs(3);
            while lease.host.live_counts().1 == 0 {
                assert!(
                    std::time::Instant::now() < deadline,
                    "scripted worker did not start"
                );
                std::thread::sleep(std::time::Duration::from_millis(1));
            }
            registry.close(1);
            assert_eq!(worker.join().unwrap()["error"], "Closed");
        });
        assert_eq!(lease.host.live_counts(), (0, 0));
    }
    #[test]
    fn lease_acquired_before_close_cannot_allocate_a_new_session_after_disposal() {
        // Ephemeral Host is sufficient to test the app lease, independently of SQLite startup.
        let lease = Arc::new(Lease {
            host: Host::new(false),
            database: PathBuf::new(),
            closed: AtomicBool::new(false),
            control: Mutex::new(()),
        });
        let registry = WorkspaceRegistry {
            mutation: Mutex::new(()),
            forks: Default::default(),
            entries: Mutex::new(RegistryState {
                next: 1,
                opening: 0,
                leases: BTreeMap::from([(1, lease.clone())]),
            }),
        };
        let create = br#"{"version":1,"command":{"op":"create","seed":"lantern-quay-v1"}}"#;
        assert_eq!(lease.call(create)["status"], "ok");
        registry.close(1);
        assert_eq!(lease.host.live_counts(), (0, 0));
        assert_eq!(lease.call(create)["error"], "InvalidHandle");
        assert_eq!(lease.host.live_counts(), (0, 0));
    }
}

#[cfg(target_os = "android")]
pub(crate) mod android {
    use super::*;
    use jni::{
        objects::{JByteArray, JObject, JString},
        sys::{jbyteArray, jlong},
        JNIEnv,
    };
    use std::sync::OnceLock;
    static REGISTRY: OnceLock<WorkspaceRegistry> = OnceLock::new();
    pub(crate) fn registry() -> &'static WorkspaceRegistry {
        REGISTRY.get_or_init(WorkspaceRegistry::default)
    }

    #[no_mangle]
    pub extern "system" fn Java_org_locallore_app_NativeWorkspace_open(
        mut env: JNIEnv<'_>,
        _: JObject<'_>,
        path: JString<'_>,
    ) -> jlong {
        std::panic::catch_unwind(std::panic::AssertUnwindSafe(|| {
            let Ok(path) = env.get_string(&path) else {
                return 0;
            };
            let path: String = path.into();
            if path.len() > 4096 || !Path::new(&path).is_absolute() {
                return 0;
            }
            registry().open(Path::new(&path)).unwrap_or(0) as jlong
        }))
        .unwrap_or(0)
    }
    #[no_mangle]
    pub extern "system" fn Java_org_locallore_app_NativeWorkspace_call(
        env: JNIEnv<'_>,
        _: JObject<'_>,
        handle: jlong,
        input: JByteArray<'_>,
    ) -> jbyteArray {
        let reply = std::panic::catch_unwind(std::panic::AssertUnwindSafe(|| {
            if input.is_null() {
                return serde_json::to_vec(&rejected("Malformed")).unwrap();
            }
            let Ok(len) = env.get_array_length(&input) else {
                return Vec::new();
            };
            if len as usize > MAX_INPUT {
                return serde_json::to_vec(&rejected("TooLarge")).unwrap();
            }
            let Ok(bytes) = env.convert_byte_array(&input) else {
                return Vec::new();
            };
            registry().call(handle as u64, &bytes)
        }))
        .unwrap_or_else(|_| serde_json::to_vec(&rejected("Internal")).unwrap());
        if reply.is_empty() {
            return std::ptr::null_mut();
        }
        env.byte_array_from_slice(&reply)
            .map(|a| a.into_raw())
            .unwrap_or(std::ptr::null_mut())
    }
    #[no_mangle]
    pub extern "system" fn Java_org_locallore_app_NativeWorkspace_close(
        _: JNIEnv<'_>,
        _: JObject<'_>,
        handle: jlong,
    ) {
        let _ = std::panic::catch_unwind(|| registry().close(handle as u64));
    }
}
