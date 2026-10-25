// Copyright 2026 LocalLore contributors. SPDX-License-Identifier: Apache-2.0
//! Frozen model-free native clock/setup oracles; SOURCE ONLY / UNCOMPILED / UNRUN.
//! Root owns registration, setup::read_setups and native::preparation_deadline.
//! Setup/load metrics here are declared synthetic, not measured native work.
//! Reservations and one-sided settlements use actual existing Ledger methods.
use super::*;
use std::collections::BTreeMap;

struct Fixture {
    root: PathBuf,
    binding: String,
}
impl Fixture {
    fn new(label: &str) -> Self {
        let root = std::env::temp_dir().join(format!(
            "locallore-native-clock-setup-{label}-{}-{}",
            std::process::id(),
            std::time::SystemTime::now()
                .duration_since(std::time::UNIX_EPOCH)
                .unwrap()
                .as_nanos()
        ));
        fs::create_dir(&root).unwrap();
        let binding = "6".repeat(64);
        for arm in ARM_NAMES {
            let path = root.join(arm);
            fs::create_dir(&path).unwrap();
            Ledger::load(&path, &binding)
                .unwrap()
                .begin_invocation()
                .unwrap();
        }
        Self { root, binding }
    }
    fn setup(&self, left: usize, right: usize, status: &str, load: Option<Value>) {
        saved(
            &self.root.join(format!("setup-{left:02}.json")),
            &SetupRecord {
                version: 2,
                binding: self.binding.clone(),
                left_invocation: left,
                right_invocation: right,
                native: true,
                physical_ms: 3,
                status: status.into(),
                load,
            },
            64 * 1024,
        )
        .unwrap();
    }
    fn finish(&self, arm: &str) {
        let mut ledger = Ledger::load(&self.root.join(arm), &self.binding).unwrap();
        // Deterministic test clock only, not a measured native setup duration.
        // Actual finish writes its own known settlement, above the 2/1 shares.
        ledger.started = Instant::now()
            .checked_sub(Duration::from_millis(20))
            .unwrap();
        ledger.finish().unwrap();
    }
}

fn synthetic_metrics() -> Value {
    json!({
        "load_ms":1.0,"prefill_ms":0.0,"decode_ms":0.0,"total_ms":1.0,
        "input_tokens":0,"output_tokens":0,"model_loads":1,
        "contexts_created":0,"abort_callbacks":0
    })
}

fn read_json(path: &Path) -> Value {
    serde_json::from_slice(&fs::read(path).unwrap()).unwrap()
}
fn replace_json(path: &Path, value: &Value) {
    // Adversarial edits touch derived test evidence only, never canonical SQL.
    fs::write(path, serde_json::to_vec(value).unwrap()).unwrap();
}
fn inventory(root: &Path) -> BTreeMap<PathBuf, Option<Vec<u8>>> {
    fn visit(root: &Path, dir: &Path, out: &mut BTreeMap<PathBuf, Option<Vec<u8>>>, depth: usize) {
        assert!(depth <= 3 && out.len() <= 128);
        for entry in fs::read_dir(dir).unwrap() {
            let path = entry.unwrap().path();
            let metadata = fs::symlink_metadata(&path).unwrap();
            assert!(!metadata.file_type().is_symlink());
            let relative = path.strip_prefix(root).unwrap().to_owned();
            if metadata.is_dir() {
                assert!(out.insert(relative, None).is_none());
                visit(root, &path, out, depth + 1);
            } else {
                assert!(metadata.is_file() && metadata.len() <= 64 * 1024);
                assert!(out
                    .insert(relative, Some(fs::read(path).unwrap()))
                    .is_none());
            }
        }
    }
    let mut out = BTreeMap::new();
    visit(root, root, &mut out, 0);
    out
}
fn refuse_without_writes(fixture: &Fixture, native: bool) {
    let before = inventory(&fixture.root);
    let result = setup::read_setups(&fixture.root, &fixture.binding, native);
    assert_eq!(
        inventory(&fixture.root),
        before,
        "reader must not repair evidence"
    );
    assert!(result.is_err(), "hostile setup evidence must refuse");
}

#[cfg(feature = "local-model")]
#[test]
fn preparation_deadline_preserves_entry_origin_and_remaining_budget_after_delay() {
    let started = Instant::now();
    let entry_limit = started + Duration::from_millis(PREPARATION_MS);
    for delay in [0, 90_000, 119_999] {
        let now = started + Duration::from_millis(delay);
        assert_eq!(
            native::preparation_deadline(started, MAX_ACTIVE_MS, now).unwrap(),
            entry_limit,
            "preflight/callback delay cannot restart the 120s entry clock"
        );
    }
    let now = started + Duration::from_millis(90_000);
    assert_eq!(
        native::preparation_deadline(started, 10_000, now).unwrap(),
        now + Duration::from_millis(7_000)
    );
    assert_eq!(
        native::preparation_deadline(started, CLEANUP_RESERVE_MS + 1, now).unwrap(),
        now + Duration::from_millis(1)
    );
    for remaining in [0, CLEANUP_RESERVE_MS] {
        assert!(native::preparation_deadline(started, remaining, now).is_err());
    }
    for elapsed in [PREPARATION_MS, PREPARATION_MS + 1] {
        assert!(native::preparation_deadline(
            started,
            MAX_ACTIVE_MS,
            started + Duration::from_millis(elapsed)
        )
        .is_err());
    }
    // The eventual caller must min-retain any earlier shortened deadline.
    // This pure-function test does not claim to exercise that caller/callback.
}

#[test]
fn supported_setup_states_and_one_sided_actual_finish_remain_read_only() {
    for (status, load) in [
        ("loaded", Some(synthetic_metrics())),
        ("failed", None),
        ("failed", Some(synthetic_metrics())),
    ] {
        let fixture = Fixture::new(status);
        let empty = inventory(&fixture.root);
        assert!(setup::read_setups(&fixture.root, &fixture.binding, true)
            .unwrap()
            .is_empty());
        assert_eq!(inventory(&fixture.root), empty);
        fixture.setup(0, 0, status, load);
        let before = inventory(&fixture.root);
        let loaded = setup::read_setups(&fixture.root, &fixture.binding, true).unwrap();
        assert_eq!(loaded.len(), 1);
        assert_eq!(loaded[0].status, status);
        assert_eq!(loaded[0].physical_ms, 3);
        assert_eq!(inventory(&fixture.root), before);

        // Real crash state between existing independent finish writes: only
        // left is known. Right retains its full unknown 120000ms reservation.
        fixture.finish("left");
        let left = Ledger::load(&fixture.root.join("left"), &fixture.binding).unwrap();
        let right = Ledger::load(&fixture.root.join("right"), &fixture.binding).unwrap();
        assert!(left.charged_ms >= 2);
        assert_eq!(right.charged_ms, PREPARATION_MS);
        assert_eq!(right.admissions, 0);
        assert_eq!(right.charged_roles, 0);
        assert!(!fixture
            .root
            .join("right/invocation-00-settled.json")
            .exists());
        let before = inventory(&fixture.root);
        assert_eq!(
            setup::read_setups(&fixture.root, &fixture.binding, true)
                .unwrap()
                .len(),
            1
        );
        assert_eq!(inventory(&fixture.root), before);
        assert_eq!(
            Ledger::load(&fixture.root.join("right"), &fixture.binding)
                .unwrap()
                .charged_ms,
            PREPARATION_MS
        );
        fixture.finish("right");
        let before = inventory(&fixture.root);
        assert_eq!(
            setup::read_setups(&fixture.root, &fixture.binding, true)
                .unwrap()
                .len(),
            1
        );
        assert_eq!(inventory(&fixture.root), before);
    }
}

#[test]
fn setup_requires_actual_unique_reservations_exact_names_and_closed_native_identity() {
    for fault in [
        "missing-left",
        "missing-right",
        "version",
        "binding",
        "index",
        "story",
        "turn",
        "ms",
        "roles",
    ] {
        let fixture = Fixture::new(fault);
        fixture.setup(0, 0, "loaded", Some(synthetic_metrics()));
        let arm = if fault == "missing-left" {
            "left"
        } else {
            "right"
        };
        let path = fixture.root.join(arm).join("invocation-00.json");
        if matches!(fault, "missing-left" | "missing-right") {
            fs::remove_file(&path).unwrap();
        } else {
            let mut reservation = read_json(&path);
            match fault {
                "version" => reservation["version"] = json!(2),
                "binding" => reservation["binding"] = json!("7".repeat(64)),
                "index" => reservation["index"] = json!(1),
                "story" => reservation["story"] = json!("other"),
                "turn" => reservation["turn"] = json!("other"),
                "ms" => reservation["ms"] = json!(PREPARATION_MS + 1),
                "roles" => reservation["roles"] = json!(1),
                _ => unreachable!(),
            }
            replace_json(&path, &reservation);
        }
        refuse_without_writes(&fixture, true);
    }
    for fault in [
        "right-ref",
        "filename-index",
        "native",
        "status",
        "extra-key",
        "out-of-range-name",
    ] {
        let fixture = Fixture::new(fault);
        fixture.setup(0, 0, "loaded", Some(synthetic_metrics()));
        let path = fixture.root.join("setup-00.json");
        let mut record = read_json(&path);
        match fault {
            "right-ref" => record["right_invocation"] = json!(1),
            "filename-index" => record["left_invocation"] = json!(1),
            "native" => record["native"] = json!(false),
            "status" => record["status"] = json!("scripted"),
            "extra-key" => record["caller_terminal_grant"] = json!(true),
            "out-of-range-name" => {
                fs::rename(&path, fixture.root.join("setup-32.json")).unwrap();
            }
            _ => unreachable!(),
        }
        if fault != "out-of-range-name" {
            replace_json(&path, &record);
        }
        refuse_without_writes(&fixture, true);
    }
    let duplicate = Fixture::new("duplicate-right");
    for arm in ARM_NAMES {
        Ledger::load(&duplicate.root.join(arm), &duplicate.binding)
            .unwrap()
            .begin_invocation()
            .unwrap();
    }
    duplicate.setup(0, 0, "loaded", Some(synthetic_metrics()));
    duplicate.setup(1, 0, "failed", None);
    refuse_without_writes(&duplicate, true);
    let scripted = Fixture::new("scripted");
    scripted.setup(0, 0, "loaded", Some(synthetic_metrics()));
    refuse_without_writes(&scripted, false);
}

#[test]
fn closed_metrics_and_each_known_settlement_share_are_validated_without_repair() {
    for fault in [
        "missing-load",
        "missing-key",
        "extra-key",
        "negative",
        "null",
        "fraction",
        "overflow",
    ] {
        let fixture = Fixture::new(fault);
        fixture.setup(0, 0, "loaded", Some(synthetic_metrics()));
        let path = fixture.root.join("setup-00.json");
        let mut record = read_json(&path);
        match fault {
            "missing-load" => record["load"] = Value::Null,
            "missing-key" => {
                record["load"].as_object_mut().unwrap().remove("total_ms");
            }
            "extra-key" => record["load"]["extra"] = json!(0),
            "negative" => record["load"]["load_ms"] = json!(-0.5),
            "null" => record["load"]["total_ms"] = Value::Null,
            "fraction" => record["load"]["input_tokens"] = json!(0.5),
            "overflow" => record["load"]["output_tokens"] = json!(u64::from(u32::MAX) + 1),
            _ => unreachable!(),
        }
        replace_json(&path, &record);
        refuse_without_writes(&fixture, true);
    }
    for fault in [
        "version",
        "binding",
        "index",
        "roles",
        "left-share",
        "right-share",
    ] {
        let fixture = Fixture::new(fault);
        fixture.setup(0, 0, "failed", Some(synthetic_metrics()));
        let arm = if fault == "right-share" {
            "right"
        } else {
            "left"
        };
        fixture.finish(arm);
        let path = fixture.root.join(arm).join("invocation-00-settled.json");
        let mut settlement = read_json(&path);
        match fault {
            "version" => settlement["version"] = json!(2),
            "binding" => settlement["binding"] = json!("8".repeat(64)),
            "index" => settlement["index"] = json!(1),
            "roles" => settlement["roles"] = json!(1),
            "left-share" => settlement["ms"] = json!(1),
            "right-share" => settlement["ms"] = json!(0),
            _ => unreachable!(),
        }
        replace_json(&path, &settlement);
        refuse_without_writes(&fixture, true);
    }
}

#[test]
fn raw_metric_names_are_unique_and_failed_nullable_load_key_stays_required() {
    // Actual ledger reservations back all records. Only derived synthetic setup
    // bytes are adversarially changed; no canonical receipt/history is invented.
    let mut wrongly_accepted = Vec::new();
    for (label, duplicate, last_value) in [
        (
            "duplicate-forward",
            r#""model_loads":1,"model_loads":2"#,
            2_u64,
        ),
        (
            "duplicate-reversed",
            r#""model_loads":2,"model_loads":1"#,
            1_u64,
        ),
        (
            "duplicate-escaped",
            r#""model_loads":1,"model\u005floads":2"#,
            2_u64,
        ),
    ] {
        let fixture = Fixture::new(label);
        fixture.setup(0, 0, "loaded", Some(synthetic_metrics()));
        let path = fixture.root.join("setup-00.json");
        let original = fs::read_to_string(&path).unwrap();
        let needle = r#""model_loads":1"#;
        assert_eq!(original.matches(needle).count(), 1);
        let raw = original.replacen(needle, duplicate, 1);

        // This is syntactically valid JSON. A plain Value silently retains the
        // last value and still reports nine keys, so numeric validation alone
        // cannot establish raw metric-name uniqueness.
        let collapsed: Value = serde_json::from_str(&raw).unwrap();
        assert_eq!(collapsed["load"].as_object().unwrap().len(), 9);
        assert_eq!(collapsed["load"]["model_loads"], last_value);
        fs::write(&path, raw.as_bytes()).unwrap();
        let before = inventory(&fixture.root);
        let result = setup::read_setups(&fixture.root, &fixture.binding, true);
        assert_eq!(inventory(&fixture.root), before);
        if result.is_ok() {
            wrongly_accepted.push(label);
        }
    }

    let fixture = Fixture::new("failed-required-null-load");
    fixture.setup(0, 0, "failed", None);
    fixture.finish("left");
    let before = inventory(&fixture.root);
    let valid = setup::read_setups(&fixture.root, &fixture.binding, true).unwrap();
    assert_eq!(valid.len(), 1);
    assert_eq!(valid[0].status, "failed");
    assert!(valid[0].load.is_none());
    assert_eq!(inventory(&fixture.root), before);
    assert_eq!(
        Ledger::load(&fixture.root.join("right"), &fixture.binding)
            .unwrap()
            .charged_ms,
        PREPARATION_MS
    );

    let path = fixture.root.join("setup-00.json");
    let mut missing = read_json(&path);
    assert!(missing.as_object_mut().unwrap().remove("load").unwrap().is_null());
    replace_json(&path, &missing);
    let before = inventory(&fixture.root);
    let result = setup::read_setups(&fixture.root, &fixture.binding, true);
    assert_eq!(inventory(&fixture.root), before);
    if result.is_ok() {
        wrongly_accepted.push("failed-missing-load");
    }
    assert_eq!(
        Ledger::load(&fixture.root.join("right"), &fixture.binding)
            .unwrap()
            .charged_ms,
        PREPARATION_MS
    );
    assert!(
        wrongly_accepted.is_empty(),
        "invalid raw setup fields accepted: {wrongly_accepted:?}"
    );
}
