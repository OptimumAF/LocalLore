// Copyright 2026 LocalLore contributors. SPDX-License-Identifier: Apache-2.0
//! Trusted app-private workspace adapter. Calls belong on Kotlin IO workers, never the UI thread.
use locallore::host::{Host, MAX_INPUT, MAX_OUTPUT};
use serde_json::{json, Value};
use std::{
    collections::BTreeMap,
    path::Path,
    sync::{
        atomic::{AtomicBool, Ordering},
        Arc, Mutex,
    },
};

#[derive(Default)]
pub struct WorkspaceRegistry {
    entries: Mutex<(u64, BTreeMap<u64, Arc<Lease>>)>,
}
struct Lease {
    host: Host,
    closed: AtomicBool,
    control: Mutex<()>,
}
fn rejected(category: &str) -> Value {
    json!({"version":1,"status":"rejected","error":category})
}
impl WorkspaceRegistry {
    /// The path is supplied by native app construction, never a Host wire command.
    pub fn open(&self, path: &Path) -> Result<u64, String> {
        let mut entries = self.entries.lock().map_err(|_| "Internal")?;
        if entries.1.len() >= 4 {
            return Err("WorkspaceLimit".into());
        }
        let host = locallore_workspace::open(path, false)?;
        let id = entries
            .0
            .checked_add(1)
            .filter(|n| *n <= i64::MAX as u64)
            .ok_or("WorkspaceLimit")?;
        entries.0 = id;
        entries.1.insert(
            id,
            Arc::new(Lease {
                host,
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
            let lease = self.entries.lock().unwrap().1.get(&handle).cloned();
            let Some(lease) = lease else {
                return rejected("InvalidHandle");
            };
            // Generation bypasses the control gate. Host cancellation/session fences cover its
            // completion; neither cancel nor disposal waits for the fake or future model provider.
            let prepare = serde_json::from_slice::<Value>(bytes)
                .ok()
                .is_some_and(|value| value["command"]["op"] == "prepare");
            if prepare {
                if lease.closed.load(Ordering::SeqCst) {
                    return rejected("InvalidHandle");
                }
                lease.host.call(bytes)
            } else {
                let _control = lease.control.lock().unwrap();
                if lease.closed.load(Ordering::SeqCst) {
                    return rejected("InvalidHandle");
                }
                lease.host.call(bytes)
            }
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
        // Remove before waiting for the Host; no new work can acquire this handle.
        let lease = self.entries.lock().unwrap().1.remove(&handle);
        if let Some(lease) = lease {
            let _control = lease.control.lock().unwrap();
            lease.closed.store(true, Ordering::SeqCst);
            lease.host.close_all();
        }
    }
}

#[cfg(target_os = "android")]
mod android {
    use super::*;
    use jni::{
        objects::{JByteArray, JObject, JString},
        sys::{jbyteArray, jlong},
        JNIEnv,
    };
    use std::sync::OnceLock;
    static REGISTRY: OnceLock<WorkspaceRegistry> = OnceLock::new();
    fn registry() -> &'static WorkspaceRegistry {
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
