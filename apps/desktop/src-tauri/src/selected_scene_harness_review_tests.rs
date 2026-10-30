// Copyright 2026 LocalLore contributors. SPDX-License-Identifier: Apache-2.0
//! Independent FIRST from e3c5cf51 + 53df4d3f: UNREGISTERED/UNCOMPILED/UNRUN.
//! Source is intentionally unformatted; the coordinator retains raw equality.
//! Child of selected_harness; actual native fixture helper and public Scene4
//! inspection only. No IPC, WebView, consent, model, process or OS isolation proof.
//! Each ordinary fixture is retained, including every intentionally failed byte.
use super::*;
use crate::comparison_reader_harness::{selected_scene_flags, selected_scene_prepare};
use locallore_eval::local_lane::comparison::{self, ComparisonKind};
use sha2::{Digest, Sha256};
use std::{
    collections::{BTreeMap, BTreeSet},
    fs::{self, OpenOptions},
    io::Write,
    sync::{atomic::AtomicU64, OnceLock},
    time::{SystemTime, UNIX_EPOCH},
};

const FREEZE: &str = "selected-scene-source-freeze-v1.json";
type Bytes = BTreeMap<String, Option<Vec<u8>>>;

fn parent() -> PathBuf {
    // The coordinator validates physical D locally. Portable CI may use temp.
    let parent = std::env::var_os("LOCALLORE_SELECTED_SCENE4_NATIVE_TEST_ROOT")
        .map(PathBuf::from)
        .unwrap_or_else(std::env::temp_dir);
    assert!(parent.is_absolute() && parent.is_dir());
    let parent = fs::canonicalize(parent).unwrap();
    let _pins = crate::archive::pin(&parent).unwrap();
    parent
}
fn packet() -> PathBuf {
    static NEXT: AtomicU64 = AtomicU64::new(0);
    let time = u64::try_from(
        SystemTime::now()
            .duration_since(UNIX_EPOCH)
            .unwrap()
            .as_nanos(),
    )
    .unwrap();
    let id = format!("{time:016x}{:016x}", NEXT.fetch_add(1, Ordering::SeqCst));
    let uuid = format!(
        "{}-{}-{}-{}-{}",
        &id[..8],
        &id[8..12],
        &id[12..16],
        &id[16..20],
        &id[20..]
    );
    let path = parent().join(format!("comparison-reader-native-{uuid}"));
    fs::create_dir(&path).unwrap();
    path
}
fn bytes(root: &Path) -> Bytes {
    fn visit(root: &Path, path: &Path, out: &mut Bytes) {
        let metadata = fs::symlink_metadata(path).unwrap();
        assert!(!metadata.file_type().is_symlink());
        if metadata.is_dir() {
            let _pins = crate::archive::pin(path).unwrap();
            if path != root {
                out.insert(
                    path.strip_prefix(root)
                        .unwrap()
                        .to_str()
                        .unwrap()
                        .replace('\\', "/"),
                    None,
                );
            }
            for entry in fs::read_dir(path).unwrap() {
                visit(root, &entry.unwrap().path(), out);
            }
        } else {
            assert!(metadata.is_file());
            out.insert(
                path.strip_prefix(root)
                    .unwrap()
                    .to_str()
                    .unwrap()
                    .replace('\\', "/"),
                Some(fs::read(path).unwrap()),
            );
        }
    }
    let mut out = BTreeMap::new();
    visit(root, root, &mut out);
    out
}
fn new_bytes(path: &Path, bytes: &[u8]) {
    let mut file = OpenOptions::new()
        .write(true)
        .create_new(true)
        .open(path)
        .unwrap();
    file.write_all(bytes).unwrap();
    file.sync_all().unwrap();
}
fn template() -> &'static Path {
    static ORIGINAL: OnceLock<PathBuf> = OnceLock::new();
    ORIGINAL
        .get_or_init(|| {
            let root = packet();
            assert!(bytes(&root).is_empty());
            selected_scene_prepare(&root.join("comparison-fixtures"), "initial").unwrap();
            root
        })
        .as_path()
}
fn retained() -> PathBuf {
    let source = bytes(template());
    let target = packet();
    for (name, value) in &source {
        let path = target.join(name);
        match value {
            None => fs::create_dir_all(path).unwrap(),
            Some(value) => {
                fs::create_dir_all(path.parent().unwrap()).unwrap();
                new_bytes(&path, value);
            }
        }
    }
    assert_eq!(bytes(&target), source);
    target
}
fn frozen(root: &Path) -> Value {
    serde_json::from_slice(&fs::read(root.join(FREEZE)).unwrap()).unwrap()
}
fn reject_unchanged(root: &Path, stage: &str) {
    let before = bytes(root);
    assert!(selected_scene_prepare(&root.join("comparison-fixtures"), stage).is_err());
    assert_eq!(
        bytes(root),
        before,
        "a refused fixture was changed or repaired"
    );
}
fn replace_freeze(root: &Path, value: &Value) {
    fs::write(root.join(FREEZE), serde_json::to_vec(value).unwrap()).unwrap();
}
fn contains_key(value: &Value, expected: &str) -> bool {
    match value {
        Value::Object(map) => {
            map.contains_key(expected) || map.values().any(|value| contains_key(value, expected))
        }
        Value::Array(array) => array.iter().any(|value| contains_key(value, expected)),
        _ => false,
    }
}

#[test]
fn discriminator_preserves_legacy_and_admits_scene3_only_in_scene_mode() {
    for kind in ["selected_prepared", "selected_read"] {
        for scene in [false, true] {
            assert!(metadata_kind_for_mode(&json!({"version":1,"kind":kind}), scene).is_ok());
            assert!(metadata_kind_for_mode(
                &json!({"version":2,"source_protocol_version":3,"kind":kind}),
                scene
            )
            .is_ok());
        }
        let scene = json!({"version":3,"source_protocol_version":4,"kind":kind});
        assert!(metadata_kind_for_mode(&scene, true).is_ok());
        assert!(metadata_kind_for_mode(&scene, false).is_err());
        for bad in [
            json!(null),
            json!([]),
            json!({"version":2,"kind":kind}),
            json!({"version":3,"kind":kind}),
            json!({"version":3,"source_protocol_version":3,"kind":kind}),
            json!({"version":2,"source_protocol_version":4,"kind":kind}),
            json!({"version":4,"source_protocol_version":4,"kind":kind}),
            json!({"version":3,"source_protocol_version":4,"kind":"selected_diagnostics"}),
            json!({"version":3,"source_protocol_version":4,"kind":kind,"padding":"x".repeat(16*1024)}),
        ] {
            for mode in [false, true] {
                assert!(metadata_kind_for_mode(&bad, mode).is_err());
            }
        }
        let mut boundary =
            json!({"version":3,"source_protocol_version":4,"kind":kind,"padding":""});
        let count = 16 * 1024 - serde_json::to_vec(&boundary).unwrap().len();
        boundary["padding"] = json!("x".repeat(count));
        assert_eq!(serde_json::to_vec(&boundary).unwrap().len(), 16 * 1024);
        assert!(metadata_kind_for_mode(&boundary, true).is_ok());
        boundary["padding"] = json!("x".repeat(count + 1));
        assert!(metadata_kind_for_mode(&boundary, true).is_err());
    }
}

#[test]
fn all_flag_combinations_are_pure_and_only_exact_scene_mode_is_admitted() {
    let before: BTreeMap<_, _> = std::env::vars_os().collect();
    for mask in 0u8..32 {
        let flags = [
            mask & 1 != 0,
            mask & 2 != 0,
            mask & 4 != 0,
            mask & 8 != 0,
            mask & 16 != 0,
        ];
        assert_eq!(
            selected_scene_flags(flags[0], flags[1], flags[2], flags[3], flags[4]),
            mask == 7,
            "mask {mask}"
        );
    }
    assert_eq!(std::env::vars_os().collect::<BTreeMap<_, _>>(), before);
}

#[test]
fn actual_initial_produces_public_scene4_sources_and_complete_external_freeze() {
    let root = template();
    let fixtures = root.join("comparison-fixtures");
    let original = bytes(root);
    let reply = selected_scene_prepare(&fixtures, "initial").unwrap();
    assert_eq!(reply["synthetic"], true);
    assert_eq!(reply["protocol_version"], 4);
    assert_eq!(reply["paired_rows"], 24);
    assert_eq!(reply["rollout_rows"], 12);
    assert_eq!(reply["models_executed"], false);
    let reference = comparison::open_reference(&fixtures.join("reference")).unwrap();
    drop(reference);
    for (name, scenes, kind) in [
        ("paired", 2, ComparisonKind::PairedSnapshots),
        ("rollout", 1, ComparisonKind::ContinuousRollout),
    ] {
        let report = comparison::scene_v4::inspect_comparison(&fixtures.join(name)).unwrap();
        assert_eq!(report.version, 4);
        assert_eq!(report.kind, kind);
        assert_eq!(report.completed_scenes, scenes);
        assert_eq!(report.turns.len(), scenes * 12);
        assert!(report.source_matches && report.turns.iter().all(|row| row.passed));
        assert_eq!(report.physical_setups, 0);
        assert!(report.physical_setup_ms.is_none() && report.native_load.is_none());
        assert_eq!(report.human_reviewed, 0);
        assert_eq!(report.human_rubric, "not_reviewed");
        assert!(!report.quality_accepted);
        assert_eq!(reply["scene_proof"][name]["rows"], scenes * 12);
        assert_eq!(reply["scene_proof"][name]["source_matches"], true);
        assert_eq!(reply["scene_proof"][name]["quality_accepted"], false);
        assert_eq!(reply["scene_proof"][name]["models_executed"], false);
    }
    let freeze = frozen(root);
    assert_eq!(
        freeze
            .as_object()
            .unwrap()
            .keys()
            .map(String::as_str)
            .collect::<BTreeSet<_>>(),
        [
            "version",
            "kind",
            "source_protocol_version",
            "files",
            "file_count",
            "entry_count",
            "total_bytes"
        ]
        .into_iter()
        .collect()
    );
    assert_eq!(freeze["version"], 1);
    assert_eq!(freeze["kind"], "selected_scene_source_freeze_v1");
    assert_eq!(freeze["source_protocol_version"], 4);
    let all = bytes(&fixtures);
    let mut total = 0usize;
    let mut expected = BTreeMap::new();
    for (name, value) in &all {
        if let Some(value) = value {
            total = total.checked_add(value.len()).unwrap();
            expected.insert(name.clone(), format!("{:x}", Sha256::digest(value)));
        }
    }
    assert_eq!(freeze["files"], serde_json::to_value(&expected).unwrap());
    assert_eq!(freeze["file_count"], expected.len());
    // Inventory includes the fixture root itself, matching existing inventory_stats.
    assert_eq!(freeze["entry_count"], all.len() + 1);
    assert_eq!(freeze["total_bytes"], total);
    assert!(expected.len() <= 2048 && total <= 64 * 1024 * 1024 && all.len() + 1 <= 8192);
    let raw = fs::read(root.join(FREEZE)).unwrap();
    assert!(raw.len() <= 1024 * 1024);
    assert_eq!(
        reply["fixture_inventory"],
        json!({
            "version":1,"kind":"selected_scene_source_freeze_ref_v1",
            "sha256":format!("{:x}", Sha256::digest(&raw)),"source_protocol_version":4,
            "file_count":freeze["file_count"],"entry_count":freeze["entry_count"],
            "total_bytes":freeze["total_bytes"]
        })
    );
    for name in expected.keys() {
        assert!(!contains_key(&reply, name), "full map escaped into reply");
    }
    assert!(serde_json::to_vec(&reply).unwrap().len() <= 256 * 1024);
    assert_eq!(bytes(root), original);
}

#[test]
fn repeated_initial_and_restart_validate_without_changing_any_retained_byte() {
    let root = retained();
    let before = bytes(&root);
    let initial = selected_scene_prepare(&root.join("comparison-fixtures"), "initial").unwrap();
    assert_eq!(bytes(&root), before);
    let restarted = selected_scene_prepare(&root.join("comparison-fixtures"), "restart").unwrap();
    assert_eq!(restarted, initial);
    assert_eq!(bytes(&root), before);
}

#[test]
fn stage_and_fixed_path_guards_refuse_before_fixture_writes() {
    let root = packet();
    new_bytes(&root.join("retained-sentinel"), b"ordinary retained bytes");
    for stage in ["", "0", "1", "review", "INITIAL", "restart/initial"] {
        reject_unchanged(&root, stage);
    }
    let before = bytes(&root);
    // PathBuf::join normalizes ParentDir on Windows verbatim roots. Append
    // lexical bytes instead so the negative actually reaches the entry guard.
    let mut lexical = root.as_os_str().to_os_string();
    for component in ["comparison-fixtures", "..", "comparison-fixtures"] {
        lexical.push(std::path::MAIN_SEPARATOR.to_string());
        lexical.push(component);
    }
    let lexical = PathBuf::from(lexical);
    assert!(lexical
        .components()
        .any(|part| matches!(part, std::path::Component::ParentDir)));
    assert_ne!(lexical, root.join("comparison-fixtures"));
    for bad in [
        root.join("other-fixtures"),
        lexical,
        root.join("nested/comparison-fixtures"),
    ] {
        assert!(selected_scene_prepare(&bad, "initial").is_err());
        assert_eq!(bytes(&root), before);
    }
    let wrong_parent = root.join("ordinary-not-a-packet");
    fs::create_dir(&wrong_parent).unwrap();
    let before = bytes(&root);
    assert!(selected_scene_prepare(&wrong_parent.join("comparison-fixtures"), "initial").is_err());
    assert_eq!(bytes(&root), before);
}

#[test]
fn absent_restart_and_each_partial_initial_are_refused_without_repair() {
    let absent = packet();
    reject_unchanged(&absent, "restart");
    let empty = packet();
    fs::create_dir(empty.join("comparison-fixtures")).unwrap();
    reject_unchanged(&empty, "initial");
    reject_unchanged(&empty, "restart");
    let freeze_only = packet();
    new_bytes(
        &freeze_only.join(FREEZE),
        &fs::read(template().join(FREEZE)).unwrap(),
    );
    reject_unchanged(&freeze_only, "initial");
    reject_unchanged(&freeze_only, "restart");
    for member in ["reference", "paired", "rollout"] {
        let root = retained();
        // Move the actual member aside as retained evidence; never delete it.
        fs::rename(
            root.join("comparison-fixtures").join(member),
            root.join(format!("retained-{member}")),
        )
        .unwrap();
        reject_unchanged(&root, "initial");
        reject_unchanged(&root, "restart");
    }
    let root = retained();
    fs::rename(
        root.join(FREEZE),
        root.join("retained-original-freeze.bytes"),
    )
    .unwrap();
    reject_unchanged(&root, "initial");
    reject_unchanged(&root, "restart");
}

#[test]
fn malformed_duplicate_count_hash_and_overflow_freezes_are_never_rewritten() {
    let valid = frozen(template());
    let original = fs::read(template().join(FREEZE)).unwrap();
    let text = serde_json::to_string(&valid).unwrap();
    let first = valid["files"].as_object().unwrap().iter().next().unwrap();
    let duplicate_file = format!(
        "{}:{},",
        serde_json::to_string(first.0).unwrap(),
        serde_json::to_string(first.1).unwrap()
    );
    let controls = [
        b"{".to_vec(),
        format!("{{\"version\":1,{}", &text[1..]).into_bytes(),
        text.replacen("\"files\":{", &format!("\"files\":{{{duplicate_file}"), 1)
            .into_bytes(),
        vec![b' '; 1024 * 1024 + 1],
    ];
    for control in controls {
        assert_ne!(control, original);
        let root = retained();
        fs::write(root.join(FREEZE), control).unwrap();
        reject_unchanged(&root, "initial");
        reject_unchanged(&root, "restart");
    }
    for field in [
        "version",
        "source_protocol_version",
        "file_count",
        "entry_count",
        "total_bytes",
    ] {
        let root = retained();
        let mut changed = valid.clone();
        changed[field] = json!(u64::MAX);
        replace_freeze(&root, &changed);
        reject_unchanged(&root, "initial");
        reject_unchanged(&root, "restart");
    }
    for change in 0..5 {
        let root = retained();
        let mut changed = valid.clone();
        match change {
            0 => changed["kind"] = json!("foreign_fixture"),
            1 => {
                changed
                    .as_object_mut()
                    .unwrap()
                    .insert("foreign".into(), json!(true));
            }
            2 => {
                *changed["files"]
                    .as_object_mut()
                    .unwrap()
                    .values_mut()
                    .next()
                    .unwrap() = json!("A".repeat(64));
            }
            3 => {
                *changed["files"]
                    .as_object_mut()
                    .unwrap()
                    .values_mut()
                    .next()
                    .unwrap() = json!("0".repeat(64));
            }
            4 => {
                changed["files"]
                    .as_object_mut()
                    .unwrap()
                    .insert("../foreign".into(), json!("0".repeat(64)));
            }
            _ => unreachable!(),
        }
        replace_freeze(&root, &changed);
        reject_unchanged(&root, "initial");
        reject_unchanged(&root, "restart");
    }
}

#[test]
fn changed_or_foreign_source_bytes_refuse_with_complete_evidence_preserved() {
    let changed = retained();
    let manifest = frozen(&changed);
    let name = manifest["files"]
        .as_object()
        .unwrap()
        .keys()
        .next()
        .unwrap();
    let file = changed.join("comparison-fixtures").join(name);
    let mut content = fs::read(&file).unwrap();
    content.push(b'\n');
    fs::write(file, content).unwrap();
    reject_unchanged(&changed, "initial");
    reject_unchanged(&changed, "restart");
    let foreign = retained();
    new_bytes(
        &foreign.join("comparison-fixtures/foreign.bytes"),
        b"not an authorized source member",
    );
    reject_unchanged(&foreign, "initial");
    reject_unchanged(&foreign, "restart");
}
