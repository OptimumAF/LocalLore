use locallore_storage::{validate_archive, Store};
use serde_json::{json, Value};
use std::{collections::BTreeSet, fs, io::{self, Write}, path::PathBuf, time::Instant};

fn main() -> Result<(), Box<dyn std::error::Error>> {
    let started = Instant::now();
    let args: Vec<_> = std::env::args_os().collect();
    assert_eq!(args.len(), 4);
    let archive = fs::read(&args[1])?;
    assert_eq!(archive.len(), 14_497);
    let metadata: Value = serde_json::from_slice(&fs::read(&args[2])?)?;
    let directory = PathBuf::from(&args[3]);
    assert!(directory.is_absolute() && directory.to_string_lossy().starts_with("D:"));
    assert!(!directory.exists());
    fs::create_dir(&directory)?;
    let database = directory.join("probe.sqlite3");
    let mut store = Store::open_application(&database)?;
    let validated = validate_archive(&archive, &|| false).map_err(|e| io::Error::other(format!("{e:?}")))?;
    let imported = store.import_archive(validated, &|| false).map_err(|e| io::Error::other(format!("{e:?}")))?;
    assert_eq!(imported.branches, 3);
    assert_eq!(imported.root.story, metadata["story"]);
    let mut snapshots = Vec::new();
    for role in ["before", "corrected", "rediscovered"] {
        let mut scope = imported.root.clone();
        scope.branch = metadata["branches"][role]["branch"].as_str().unwrap().into();
        let engine = store.resume(&scope)?.engine;
        assert_eq!(engine.revision(), metadata["branches"][role]["head"].as_u64().unwrap());
        assert_eq!(engine.seed().player, metadata["player"]);
        assert_ne!(engine.seed().player, "player");
        snapshots.push((role, scope, engine.canonical_bytes(), engine.accepted_history_basis()?));
    }
    let canonical_archive = store.export_archive(&imported.root.story, &|| false).map_err(|e| io::Error::other(format!("{e:?}")))?.bytes().to_vec();
    assert_eq!(canonical_archive, archive);
    drop(store);
    let host = locallore_workspace::open(&database, false)?;
    assert!(!host.story_lab_granted());
    let mut branches = Vec::new();
    for (role, scope, _, _) in &snapshots {
        assert!(started.elapsed().as_secs() < 25);
        let head = metadata["branches"][role]["head"].as_u64().unwrap();
        let call = |command: Value| host.call(&serde_json::to_vec(&json!({"version":1,"command":command})).unwrap());
        let resumed = call(json!({"op":"resume","scope":scope}));
        assert_eq!(resumed["status"], "ok");
        let session = resumed["data"]["session"].as_str().unwrap();
        let opened = call(json!({"op":"open","session":session,"scope":scope}));
        assert_eq!(opened["status"], "ok");
        assert_eq!(opened["data"]["revision"], head);
        let legacy = call(json!({"op":"play_snapshot","session":session,"scope":scope,"expected_revision":head}));
        if *role == "before" {
            assert_eq!(legacy["status"], "ok");
            assert!(legacy["data"]["receipts"].is_array());
        } else {
            assert_eq!(legacy["status"], "rejected");
            assert_eq!(legacy["error"], "Version");
        }
        let thin = call(json!({"op":"play_snapshot_v2","session":session,"scope":scope,"expected_revision":head}));
        assert_eq!(thin["status"], "ok");
        assert_eq!(thin["data"]["version"], 2);
        assert_eq!(thin["data"]["domain_version"], if *role == "before" {1} else {2});
        assert_eq!(thin["data"]["scope"], json!(scope));
        assert_eq!(thin["data"]["revision"], head);
        assert_eq!(thin["data"]["player"]["observer"], metadata["player"]);
        assert_eq!(thin["data"].as_object().unwrap().len(), 7);
        assert_eq!(thin["data"]["player"].as_object().unwrap().len(), 2);
        let mut inspections = Vec::new();
        for view in ["history", "knowledge"] {
            let mut cursor = Value::Null;
            let mut seen = BTreeSet::new();
            let mut pages = Vec::new();
            let mut finished = false;
            for _ in 0..32 {
                assert!(started.elapsed().as_secs() < 25);
                let query = json!({"version":2,"scope":scope,"expected_head":head,"at_revision":null,
                    "observer":{"kind":"player"},"view":view,"cursor":cursor,"limit":8,"search":""});
                let reply = call(json!({"op":"inspection_query","session":session,"query":query}));
                assert_eq!(reply["status"], "ok");
                assert_eq!(reply["data"]["scope"], json!(scope));
                assert_eq!(reply["data"]["head"], head);
                cursor = reply["data"]["next_cursor"].clone();
                pages.push(json!({"query":query,"reply":reply}));
                if cursor.is_null() { finished = true; break; }
                assert!(seen.insert(cursor.as_str().unwrap().to_owned()));
            }
            assert!(finished);
            let encoded = serde_json::to_string(&pages)?;
            if view == "knowledge" {
                let expected = metadata[if *role == "rediscovered" {"new_observation"} else {"old_observation"}].as_str().unwrap();
                assert!(encoded.contains(expected));
                if *role == "corrected" { assert!(!encoded.contains(metadata["new_observation"].as_str().unwrap())); }
            } else {
                assert!(encoded.contains("scoped_message"));
                assert!(encoded.contains("original_scope"));
                assert_eq!(encoded.contains("\"kind\":\"author_correction\""), *role != "before");
            }
            inspections.push(json!({"view":view,"pages":pages}));
        }
        let public = json!({"legacy":legacy,"thin":thin,"inspections":inspections});
        let encoded = serde_json::to_string(&public)?;
        for forbidden in metadata["forbidden"].as_array().unwrap() {
            assert!(!encoded.contains(forbidden.as_str().unwrap()));
        }
        let closed = call(json!({"op":"close","session":session,"scope":scope}));
        assert_eq!(closed["status"], "ok");
        branches.push(json!({"role":role,"scope":scope,"head":head,"resume":resumed,"open":opened,
            "responses":public,"close":closed}));
    }
    drop(host);
    let mut store = Store::open_application(&database)?;
    for (_, scope, canonical, basis) in &snapshots {
        let engine = store.resume(scope)?.engine;
        assert_eq!(&engine.canonical_bytes(), canonical);
        assert_eq!(&engine.accepted_history_basis()?, basis);
    }
    let after = store.export_archive(&imported.root.story, &|| false).map_err(|e| io::Error::other(format!("{e:?}")))?;
    assert_eq!(after.bytes(), canonical_archive);
    drop(store);
    let report = json!({"version":1,"status":"passed","story_lab_granted":false,"player":metadata["player"],
        "branches":branches,"canonical_archive_equal":true,"all_branch_canonical_and_history_equal":true,
        "body_elapsed_ms":started.elapsed().as_millis(),"no_provider_inference":true});
    let bytes = serde_json::to_vec(&report)?;
    assert!(bytes.len() < 262_144);
    io::stdout().lock().write_all(&bytes)?;
    Ok(())
}
