// Copyright 2026 LocalLore contributors. SPDX-License-Identifier: Apache-2.0
//! Frozen prepared-metadata privacy/identity oracles, SOURCE-ONLY / UNRUN.
//! One actual scripted Host comparison producer; no native/UI/model execution.
//! Root registers this module and implements the frozen pure getter separately.
use super::*;
use std::{
    collections::{BTreeMap, BTreeSet},
    sync::OnceLock,
};

const INDEX: usize = 4;
type Inventory = BTreeMap<PathBuf, Option<Vec<u8>>>;
fn owned_root(label: &str) -> PathBuf {
    let root = std::env::temp_dir().join(format!(
        "locallore-prepared-metadata-{label}-{}-{}",
        std::process::id(),
        std::time::SystemTime::now()
            .duration_since(std::time::UNIX_EPOCH)
            .unwrap()
            .as_nanos()
    ));
    fs::create_dir(&root).unwrap();
    root
}
fn inventory(root: &Path) -> Inventory {
    fn visit(root: &Path, dir: &Path, depth: usize, bytes: &mut usize, out: &mut Inventory) {
        assert!(depth <= 8);
        for entry in fs::read_dir(dir).unwrap() {
            assert!(out.len() < 4096);
            let path = entry.unwrap().path();
            let metadata = fs::symlink_metadata(&path).unwrap();
            assert!(!metadata.file_type().is_symlink());
            let relative = path.strip_prefix(root).unwrap().to_owned();
            if metadata.is_dir() {
                out.insert(relative, None);
                visit(root, &path, depth + 1, bytes, out);
            } else {
                assert!(metadata.is_file() && metadata.len() <= 8 * 1024 * 1024);
                let value = fs::read(path).unwrap();
                *bytes = bytes.checked_add(value.len()).unwrap();
                assert!(*bytes <= 64 * 1024 * 1024);
                out.insert(relative, Some(value));
            }
        }
    }
    let mut out = BTreeMap::new();
    visit(root, root, 0, &mut 0, &mut out);
    out
}
fn actual_source() -> &'static Path {
    static SOURCE: OnceLock<PathBuf> = OnceLock::new();
    SOURCE
        .get_or_init(|| {
            let source = owned_root("producer").join("source");
            let report = run_comparison(
                &source,
                false,
                ComparisonKind::ContinuousRollout,
                &Cancellation::default(),
                1,
                LaneFactory::ScriptedBaseline,
                None,
            )
            .unwrap();
            assert_eq!((report.completed_scenes, report.turns.len()), (1, 12));
            assert!(report.turns.iter().all(|row| row.passed));
            source
        })
        .as_path()
}
struct Fixture {
    root: PathBuf,
    source: PathBuf,
}
impl Fixture {
    fn new(label: &str) -> Self {
        let original = inventory(actual_source());
        let root = owned_root(label);
        let source = root.join("source");
        fs::create_dir(&source).unwrap();
        for (relative, bytes) in &original {
            match bytes {
                None => fs::create_dir_all(source.join(relative)).unwrap(),
                Some(bytes) => fs::write(source.join(relative), bytes).unwrap(),
            }
        }
        assert!(inventory(&source) == original);
        Self { root, source }
    }
    fn plan(&self) -> PreparedSelectedPlan {
        let reader = desktop_api::open_read_only(&self.source).unwrap();
        let binding = desktop_api::summary(&reader, true).unwrap()["binding"]
            .as_str()
            .unwrap()
            .to_owned();
        drop(reader);
        let corpus = suite().unwrap();
        assert_eq!(corpus.steps()[INDEX].text(), "I move to pier.");
        prepare_selected(
            &self.source,
            &binding,
            &desktop_api::RowId {
                turn: corpus.steps()[INDEX].id().into(),
                arm: desktop_api::Arm::Right,
            },
            SelectedIntent {
                client_id: "prepared-metadata-fixture".into(),
                lane: SelectedLane::ScriptedBaseline,
            },
            &Cancellation::default(),
        )
        .unwrap()
    }
}
fn keys(value: &Value, expected: &[&str]) {
    assert_eq!(
        value
            .as_object()
            .unwrap()
            .keys()
            .map(String::as_str)
            .collect::<BTreeSet<_>>(),
        expected.iter().copied().collect::<BTreeSet<_>>()
    );
}
fn contexts(full: &Engine) -> Value {
    json!([
        full.character_context(&full.seed().player, full.scope(), full.revision())
            .unwrap(),
        full.character_context("mira", full.scope(), full.revision())
            .unwrap(),
        full.character_context("sable", full.scope(), full.revision())
            .unwrap()
    ])
}
fn no_private(value: &Value, source: &Path, request_text: &str) {
    match value {
        Value::Object(fields) => {
            for (key, value) in fields {
                assert!(![
                    "source_binding",
                    "source_inputs",
                    "request",
                    "intent",
                    "expected_revision",
                    "profile",
                    "observer",
                    "source_dir",
                    "path",
                    "text",
                    "trace",
                    "outputs",
                    "narration",
                    "client_id"
                ]
                .contains(&key.as_str()));
                no_private(value, source, request_text);
            }
        }
        Value::Array(values) => {
            for value in values {
                no_private(value, source, request_text);
            }
        }
        Value::String(value) => {
            assert!(!value.contains("SECRET-TIDE-731") && !value.contains("amber stitch"));
            assert!(!value.contains(request_text) && !value.contains(source.to_str().unwrap()));
            assert!(!value.contains("eval-scripted-fake-v1"));
        }
        _ => {}
    }
}

#[test]
fn prepared_metadata_has_exact_safe_fields_from_each_actual_arm_without_state_or_io_mutation() {
    let fixture = Fixture::new("privacy");
    let files = inventory(&fixture.root);
    let plan = fixture.plan();
    let corpus = suite().unwrap();
    let before = plan.before.clone();
    let generation = [contexts(&before[0]), contexts(&before[1])];
    let metadata = prepared_metadata(&plan).unwrap();
    assert_eq!(prepared_metadata(&plan).unwrap(), metadata);
    assert!(encode(&metadata).unwrap().len() <= 16 * 1024);
    keys(
        &metadata,
        &["version", "kind", "binding", "lane", "selection", "arms"],
    );
    assert_eq!(metadata["version"], 1);
    assert_eq!(metadata["kind"], "selected_prepared");
    assert_eq!(metadata["binding"], plan.manifest.binding);
    assert_ne!(metadata["binding"], plan.manifest.source_binding);
    assert_eq!(metadata["lane"], "scripted_selected_case");
    keys(&metadata["selection"], &["turn", "clicked_arm", "index"]);
    assert_eq!(metadata["selection"]["turn"], corpus.steps()[INDEX].id());
    assert_eq!(metadata["selection"]["clicked_arm"], "right");
    assert_eq!(metadata["selection"]["index"], INDEX);
    assert_eq!(metadata["arms"].as_array().unwrap().len(), 2);
    for arm in 0..2 {
        let actual = &metadata["arms"][arm];
        let input = &plan.manifest.source_inputs[arm];
        let full = &before[arm];
        keys(
            actual,
            &[
                "arm",
                "scope",
                "before_head",
                "prefix_sha256",
                "input_semantic_sha256",
            ],
        );
        let request = corpus.steps()[INDEX].request(full);
        assert!(input.request == request);
        let stored = engine(
            &fixture.source.join(ARM_NAMES[arm]).join("synthetic.sqlite"),
            full.scope(),
        )
        .unwrap()
        .at_revision(full.revision())
        .unwrap();
        assert!(stored.receipts() == full.receipts());
        assert!(stored.accepted_history_basis().unwrap() == full.accepted_history_basis().unwrap());
        assert_eq!(actual["arm"], ARM_NAMES[arm]);
        assert_eq!(actual["scope"], serde_json::to_value(full.scope()).unwrap());
        assert_eq!(actual["before_head"], full.revision());
        assert_eq!(
            actual["prefix_sha256"],
            digest(&encode(full.receipts()).unwrap())
        );
        assert_eq!(
            actual["input_semantic_sha256"],
            v2::semantic_input(full, &request).unwrap()
        );
        assert_eq!(actual["prefix_sha256"], input.prefix_sha256);
        assert_eq!(actual["input_semantic_sha256"], input.input_semantic_sha256);
        assert!(plan.before[arm].canonical_bytes() == full.canonical_bytes());
        assert!(plan.before[arm].receipts() == full.receipts());
        assert!(
            plan.before[arm].accepted_history_basis().unwrap()
                == full.accepted_history_basis().unwrap()
        );
        assert_eq!(contexts(&plan.before[arm]), generation[arm]);
    }
    no_private(&metadata, &fixture.source, corpus.steps()[INDEX].text());
    drop(plan);
    assert!(inventory(&fixture.root) == files);
}

#[test]
fn metadata_is_pure_identity_data_after_source_corruption_but_consuming_run_revalidates() {
    let fixture = Fixture::new("not-authority");
    let mut expected = inventory(&fixture.root);
    let plan = fixture.plan();
    let metadata = prepared_metadata(&plan).unwrap();
    let unrelated: StoredTurn = decode(
        &checkpoint_path(&fixture.source.join("left"), 0),
        256 * 1024,
    )
    .unwrap();
    assert_ne!(unrelated.index, INDEX);
    let capture = fixture.source.join("left").join(
        unrelated
            .capture_file
            .expect("actual unselected required capture"),
    );
    let mut changed: Value = decode(&capture, v2::MAX_PRIVATE_CAPTURE + 4096).unwrap();
    assert_eq!(changed["status"], "ok");
    changed["status"] = json!("rejected");
    let bytes = encode(&changed).unwrap();
    fs::write(&capture, &bytes).unwrap();
    assert!(expected
        .insert(
            capture.strip_prefix(&fixture.root).unwrap().to_owned(),
            Some(bytes)
        )
        .is_some());
    // Getter must not silently become fresh filesystem validation or a grant.
    assert_eq!(prepared_metadata(&plan).unwrap(), metadata);
    let destination = fixture.root.join("must-not-exist");
    let result = run_selected(plan, &destination, &Cancellation::default());
    assert!(!destination.exists());
    assert!(inventory(&fixture.root) == expected);
    assert!(matches!(result, Err(ref error) if error == "CheckpointEvidenceMismatch"));
}
