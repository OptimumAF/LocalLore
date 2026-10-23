// Copyright 2026 LocalLore contributors. SPDX-License-Identifier: Apache-2.0
//! Builds the synthetic retained-ancestry scenario with the current Store schema.
//! The packaged historical schema3 asset stays immutable. No real save/model/network.
use locallore::{contracts::*, engine::Engine};
use locallore_storage::{ForkRequest, Store};
use std::{fs, io::Write, path::PathBuf};

fn apply(store: &mut Store, scope: &Scope, id: &str, command: Command) {
    let engine = store.resume(scope).unwrap().engine;
    let request = engine.request(id, Intent::Actions(vec![command]));
    let proposal = Engine::proposal(&request).unwrap();
    let receipt = engine.preview(&request, &proposal).unwrap();
    store.begin_turn(&request).unwrap();
    store
        .commit_turn(&request, &proposal, receipt.narration())
        .unwrap();
}
fn fork(store: &mut Store, parent: &Scope, child: &str, at: u64) -> Scope {
    let head = store.resume(parent).unwrap().engine.revision();
    store
        .fork_branch(
            &ForkRequest {
                parent: parent.clone(),
                child_branch: child.into(),
                expected_parent_revision: head,
                at_revision: at,
            },
            &|| false,
        )
        .unwrap()
        .scope
}
fn fixture() -> Vec<u8> {
    let directory = std::env::temp_dir().join(format!(
        "locallore-parent-fixture-{}-{}",
        std::process::id(),
        std::time::SystemTime::now()
            .duration_since(std::time::UNIX_EPOCH)
            .unwrap()
            .as_nanos()
    ));
    fs::create_dir(&directory).unwrap();
    let mut store = Store::open(&directory.join("original.sqlite3"), None).unwrap();
    let mut seed: Seed =
        serde_json::from_str(include_str!("../../../fixtures/lantern_quay.json")).unwrap();
    seed.scope.story = "parent-retention-fixture".into();
    let root = seed.scope.clone();
    store.create_story("Original retained quay", seed).unwrap();
    for i in 0..4 {
        apply(
            &mut store,
            &root,
            &format!("root-{i}"),
            Command::Wait { ticks: 1 },
        );
    }
    let parent = fork(&mut store, &root, "parent", 2);
    apply(
        &mut store,
        &parent,
        "parent-wait",
        Command::Wait { ticks: 1 },
    );
    apply(
        &mut store,
        &parent,
        "parent-shared",
        Command::Say {
            text: "SHARED_PARENT_MEMORY".into(),
            audience: ["mira".into()].into(),
        },
    );
    apply(
        &mut store,
        &parent,
        "parent-excluded-tail",
        Command::Say {
            text: "EXCLUDED_PARENT_TAIL".into(),
            audience: ["mira".into()].into(),
        },
    );
    fork(&mut store, &parent, "child", 4);
    fork(&mut store, &parent, "rewind", 1);
    fork(&mut store, &root, "sibling", 1);
    let archive = store.export_archive(&root.story, &|| false).unwrap();
    let bytes = archive.bytes().to_vec();
    drop(store);
    fs::remove_dir_all(directory).unwrap();
    bytes
}
fn main() {
    let args: Vec<_> = std::env::args_os().skip(1).collect();
    if args.len() != 1 {
        eprintln!("Supply one new output path for the synthetic fixture.");
        std::process::exit(2);
    }
    let path = PathBuf::from(&args[0]);
    let bytes = fixture();
    let mut output = fs::OpenOptions::new()
        .write(true)
        .create_new(true)
        .open(path)
        .unwrap();
    output.write_all(&bytes).unwrap();
    output.sync_all().unwrap();
}
#[cfg(test)]
mod tests {
    use super::*;
    #[test]
    fn current_fixture_preserves_historical_canon_and_validates_nested_rewind() {
        let actual = fixture();
        let historical = include_bytes!(
            "../../../apps/android/app/src/androidTest/assets/parent-retention-v1.json"
        );
        let mut current_json: serde_json::Value = serde_json::from_slice(&actual).unwrap();
        let mut historical_json: serde_json::Value = serde_json::from_slice(historical).unwrap();
        assert_eq!(
            historical_json["payload"]["source_database_schema_version"],
            3
        );
        assert_eq!(
            current_json["payload"]["source_database_schema_version"],
            locallore_storage::SCHEMA_VERSION
        );
        // Current export must not claim it came from a historical Store. Only
        // source-schema metadata and its dependent payload digest may differ;
        // seed/branch/receipt/state integrity and every canonical field stay equal.
        for value in [&mut current_json, &mut historical_json] {
            value["payload"]
                .as_object_mut()
                .unwrap()
                .remove("source_database_schema_version")
                .unwrap();
            value["integrity"]
                .as_object_mut()
                .unwrap()
                .remove("payload_sha256")
                .unwrap();
        }
        assert_eq!(current_json, historical_json);
        for bytes in [&actual[..], &historical[..]] {
            let validated = locallore_storage::validate_archive(bytes, &|| false).unwrap();
            assert_eq!(
                validated.preview().branch_heads,
                std::collections::BTreeMap::from([
                    ("main".into(), 4),
                    ("parent".into(), 5),
                    ("child".into(), 4),
                    ("rewind".into(), 1),
                    ("sibling".into(), 1)
                ])
            );
            assert!(validated.preview().retired_branch_ids.is_empty());
        }
    }
}
