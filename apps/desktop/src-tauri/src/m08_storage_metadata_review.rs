// Copyright 2026 LocalLore contributors. SPDX-License-Identifier: Apache-2.0
//! Frozen against 29e24ef before desktop schema5 metadata admission changes.
//! Register as a cfg(test) child of export_commands; do not copy its validator.
use super::storage_metadata;
use locallore::host::Host;
use locallore_storage::Store;
use serde_json::{json, Value};
use std::{
    path::PathBuf,
    sync::atomic::{AtomicU64, Ordering},
};

static NEXT: AtomicU64 = AtomicU64::new(0);

struct Temp(PathBuf);
impl Temp {
    fn new() -> Self {
        let directory = std::env::temp_dir().join(format!(
            "locallore-m08-desktop-metadata-{}-{}-{}",
            std::process::id(),
            std::time::SystemTime::now()
                .duration_since(std::time::UNIX_EPOCH)
                .unwrap()
                .as_nanos(),
            NEXT.fetch_add(1, Ordering::Relaxed)
        ));
        std::fs::create_dir(&directory).unwrap();
        Self(directory)
    }
    fn database(&self) -> PathBuf {
        self.0.join("synthetic.sqlite")
    }
    fn host(&self) -> Host {
        let store = Store::open_application(&self.database()).unwrap();
        // Observe the physical schema through its actual native Store owner.
        assert_eq!(store.info().unwrap().schema_version, 5);
        drop(store);
        locallore_workspace::open(&self.database(), false).unwrap()
    }
}
impl Drop for Temp {
    fn drop(&mut self) {
        // This guard removes only its uniquely created synthetic directory.
        if let Err(error) = std::fs::remove_dir_all(&self.0) {
            if !std::thread::panicking() {
                panic!("synthetic metadata fixture cleanup failed: {error}");
            }
        }
    }
}

fn workspace_reply(host: &Host) -> Value {
    let reply = host.call(br#"{"version":1,"command":{"op":"workspace"}}"#);
    assert_eq!(reply["version"], 1, "{reply}");
    assert_eq!(reply["status"], "ok", "{reply}");
    assert_eq!(reply["data"]["persistent"], true, "{reply}");
    assert_eq!(reply["data"]["schema_version"], 1, "{reply}");
    assert_eq!(reply["data"]["database_schema_version"], 5, "{reply}");
    reply
}

#[test]
fn actual_store_schema5_host_protocol1_passes_same_native_metadata_admission() {
    let temp = Temp::new();
    let host = temp.host();
    let reply = workspace_reply(&host);
    let cleanup = json!({"removed":0,"skipped":0});
    // This is the exact production helper called by inspection_storage after
    // its actual Host workspace reply, not a parallel JSON admission function.
    let metadata = storage_metadata(&reply, cleanup.clone())
        .expect("actual schema5 workspace must have usable native storage metadata");
    assert_eq!(metadata["schema_version"], 5);
    assert_eq!(metadata["location"], reply["data"]["location"]);
    assert_eq!(metadata["read_only"], true);
    assert_eq!(metadata["private_preview_cleanup"], cleanup);
    assert!(metadata["notice"]
        .as_str()
        .unwrap()
        .contains("metadata only"));
    assert_eq!(
        Store::open_read_only(&temp.database())
            .unwrap()
            .info()
            .unwrap()
            .schema_version,
        5
    );
}

#[test]
fn known_database1_through4_metadata_remains_compatible_with_protocol1() {
    let temp = Temp::new();
    let host = temp.host();
    let mut reply = workspace_reply(&host);
    // These are explicit synthetic transport variants of an actual reply.
    // They do not claim this Store writer ran historical database versions.
    for version in 1..=4 {
        reply["data"]["database_schema_version"] = json!(version);
        let metadata = storage_metadata(&reply, Value::Null).unwrap();
        assert_eq!(metadata["schema_version"], version);
        assert_eq!(metadata["location"], reply["data"]["location"]);
        assert_eq!(metadata["read_only"], true);
    }
}

#[test]
fn future6_and_malformed_database_versions_are_closed_wire_refusals() {
    let temp = Temp::new();
    let host = temp.host();
    let reply = workspace_reply(&host);
    for invalid in [
        json!(6),
        json!(0),
        json!(u64::MAX),
        json!(-1),
        json!(5.5),
        json!("5"),
        Value::Null,
        json!({}),
        json!([]),
    ] {
        let mut variant = reply.clone();
        variant["data"]["database_schema_version"] = invalid.clone();
        assert_eq!(
            storage_metadata(&variant, Value::Null),
            Err("Wire".into()),
            "synthetic database version variant must remain closed: {invalid}"
        );
    }
    let mut missing = reply;
    missing["data"]
        .as_object_mut()
        .unwrap()
        .remove("database_schema_version");
    assert_eq!(storage_metadata(&missing, Value::Null), Err("Wire".into()));
}

#[test]
fn database5_never_substitutes_for_workspace_protocol1() {
    let temp = Temp::new();
    let host = temp.host();
    let reply = workspace_reply(&host);
    for invalid in [json!(0), json!(2), json!(5), json!("1"), Value::Null] {
        let mut variant = reply.clone();
        variant["data"]["schema_version"] = invalid.clone();
        assert_eq!(
            storage_metadata(&variant, Value::Null),
            Err("Wire".into()),
            "database5 cannot make incompatible workspace protocol valid: {invalid}"
        );
    }
    let mut missing = reply;
    missing["data"]
        .as_object_mut()
        .unwrap()
        .remove("schema_version");
    assert_eq!(storage_metadata(&missing, Value::Null), Err("Wire".into()));
}

#[test]
fn actual_host_protocol_refusal_survives_native_metadata_adapter() {
    let temp = Temp::new();
    let host = temp.host();
    let reply = host.call(br#"{"version":2,"command":{"op":"workspace"}}"#);
    assert_eq!(
        reply,
        json!({"version":1,"status":"rejected","error":"Version"})
    );
    assert_eq!(storage_metadata(&reply, Value::Null), Err("Version".into()));
    // Rejected input must not poison the actual owner.
    workspace_reply(&host);
}
