// Copyright 2026 LocalLore contributors. SPDX-License-Identifier: Apache-2.0
//! Frozen SOURCE ONLY / UNCOMPILED / UNRUN. Two private native2 zero-asset
//! recovery/budget groups. Imported receipts are genuinely SCRIPTED history,
//! never evidence of native generation or zero original provider calls.
use super::*;
use locallore_local_runtime::LocalRuntime;
use std::{collections::BTreeMap, sync::{Arc, Mutex, OnceLock, atomic::{AtomicUsize, Ordering}}};

const INDEX: usize = 4;
type Inventory = BTreeMap<PathBuf, Option<Vec<u8>>>;
struct Trap;
impl shared::SelectedNativeReservation for Trap {
    fn assets(&self) -> crate::local_lane::NativeAssets<'_> { panic!("zero-asset native2 recovery/preflight reached assets"); }
    fn retain_uncertain(&mut self, owner: Arc<Mutex<LocalRuntime>>) -> std::result::Result<(), Arc<Mutex<LocalRuntime>>> { Err(owner) }
}
fn root(label: &str) -> PathBuf {
    static NEXT: AtomicUsize = AtomicUsize::new(0);
    let p = std::env::temp_dir().join(format!("literal-selected2-native-{label}-{}-{}-{}", std::process::id(), std::time::SystemTime::now().duration_since(std::time::UNIX_EPOCH).unwrap().as_nanos(), NEXT.fetch_add(1, Ordering::Relaxed)));
    fs::create_dir(&p).unwrap(); p
}
// Full inventories only after opaque destination/source run.lock owners drop.
fn inventory(root: &Path) -> Inventory {
    fn walk(root: &Path, dir: &Path, depth: usize, total: &mut usize, out: &mut Inventory) {
        assert!(depth <= 8 && out.len() < 4096);
        for entry in fs::read_dir(dir).unwrap() {
            let path = entry.unwrap().path(); let metadata = fs::symlink_metadata(&path).unwrap(); assert!(!metadata.file_type().is_symlink());
            #[cfg(windows)] { use std::os::windows::fs::MetadataExt; assert_eq!(metadata.file_attributes() & 0x400, 0); }
            let relative = path.strip_prefix(root).unwrap().to_owned();
            if metadata.is_dir() { out.insert(relative, None); walk(root, &path, depth + 1, total, out); }
            else { assert!(metadata.is_file() && metadata.len() <= 8 * 1024 * 1024); let bytes = fs::read(path).unwrap(); *total = total.checked_add(bytes.len()).unwrap(); assert!(*total <= 64 * 1024 * 1024); out.insert(relative, Some(bytes)); }
        }
    }
    let mut out = Inventory::new(); walk(root, root, 0, &mut 0, &mut out); out
}
fn actual_source() -> &'static Path {
    static SOURCE: OnceLock<PathBuf> = OnceLock::new(); SOURCE.get_or_init(|| {
        let source = root("scripted-source").join("rollout");
        let report = super::super::run_comparison(&source, false, ComparisonKind::ContinuousRollout, &Cancellation::default(), 1, LaneFactory::ScriptedBaseline, None).unwrap();
        assert_eq!((report.completed_scenes, report.turns.len()), (1, 12)); assert!(report.turns.iter().all(|r| r.passed)); source
    }).as_path()
}
struct Fixture { root: PathBuf, source: PathBuf }
impl Fixture {
    fn new(label: &str) -> Self {
        let original = inventory(actual_source()); let root = root(label); let source = root.join("source"); fs::create_dir(&source).unwrap();
        for (path, bytes) in &original { match bytes { None => fs::create_dir_all(source.join(path)).unwrap(), Some(bytes) => fs::write(source.join(path), bytes).unwrap() } }
        assert_eq!(inventory(&source), original); Self { root, source }
    }
    fn plan(&self, client: &str) -> PreparedSelectedPlan {
        let opened = super::super::desktop_api::open_read_only(&self.source).unwrap(); let summary = super::super::desktop_api::summary(&opened, true).unwrap(); let binding = summary["binding"].as_str().unwrap().to_owned(); drop(opened);
        prepare_selected(&self.source, &binding, &shared_read::RowId { turn: suite().unwrap().steps()[INDEX].id().into(), arm: shared_read::Arm::Left }, SelectedIntent { client_id: client.into(), lane: SelectedLane::ApprovedNative }, &Cancellation::default()).unwrap()
    }
}
fn reserve_trap(calls: &AtomicUsize) -> Result<Trap> { calls.fetch_add(1, Ordering::SeqCst); Err("UnexpectedReservation".into()) }
fn native_error<T>(result: std::result::Result<T, shared::SelectedNativeFailure<Trap>>) -> shared::SelectedNativeFailure<Trap> { match result { Ok(_) => panic!("expected native2 budget refusal"), Err(error) => error } }

#[test]
fn imported_actual_scripted_commits_recover_without_assets_and_completed_resume_is_read_only() {
    let fixture = Fixture::new("real-import-recovery"); let source_before = inventory(&fixture.source); let plan = fixture.plan("native2-imported-scripted-receipts"); let target = fixture.root.join("selected"); let destination = new_destination(&plan, &target).unwrap(); let binding = destination.manifest.binding.clone(); let corpus = suite().unwrap(); let mut imported = Vec::new();
    for arm in ARM_NAMES {
        let source_arm = fixture.source.join(arm); let cp: StoredTurn3 = decode(&checkpoint_path(&source_arm, INDEX), 256 * 1024).unwrap(); assert_eq!(cp.row.phase, "committed");
        let full = engine(&database(&source_arm, INDEX, ComparisonKind::ContinuousRollout), &corpus.seed().scope).unwrap(); let after = full.at_revision(cp.after_head).unwrap(); let actual = after.receipts().last().unwrap(); assert_eq!(actual.request(), &cp.request);
        // Existing ensure_database imports genuine Core-validated receipts via
        // Store. No target checkpoint/profile/receipt is rewritten as native.
        let target_arm = target.join(arm); let path = database(&target_arm, INDEX, ComparisonKind::ContinuousRollout); ensure_database(&path, corpus.seed(), after.receipts()).unwrap();
        assert!(!checkpoint_path(&target_arm, INDEX).exists()); imported.push(after);
    }
    drop(destination); drop(plan);
    let canonical_before: Vec<_> = ARM_NAMES.iter().map(|arm| engine(&database(&target.join(arm), INDEX, ComparisonKind::ContinuousRollout), &corpus.seed().scope).unwrap()).collect();
    let calls = AtomicUsize::new(0);
    let report = serde_json::to_value(resume_native_selected(&target, &fixture.source, &binding, &Cancellation::default(), || reserve_trap(&calls)).unwrap()).unwrap();
    assert_eq!(calls.load(Ordering::SeqCst), 0); assert_eq!(report["completed"], true); assert_eq!(report["version"], 2); assert_eq!(report["source_protocol_version"], 3); assert_eq!(report["physical_setups"], 0); assert!(report["physical_setup_ms"].is_null() && report["native_load"].is_null()); assert_eq!(report["human_reviewed"], 0); assert_eq!(report["quality_accepted"], false); assert_eq!(report["rows"].as_array().unwrap().len(), 2);
    for (arm, name) in ARM_NAMES.iter().enumerate() {
        let row = &report["rows"][arm]; assert_eq!(row["arm"], *name); assert_eq!(row["phase"], "committed"); assert_eq!(row["recovered_without_checkpoint"], true); assert_eq!(row["roles_known"], false); assert_eq!(row["passed"], false); assert_eq!(row["construction_evidence_status"], "unavailable"); assert_eq!(row["context_evidence_available"], false);
        assert_eq!(row["actual_receipt_sha256"], digest(&encode(imported[arm].receipts().last().unwrap()).unwrap())); for key in ["literal_source_units", "literal_selected_start", "literal_selected_units", "role_metrics", "capture_sha256", "recording_sha256"] { assert!(row[key].is_null()); }
        let dir = target.join(name); let ledger = Ledger::load(&dir, &binding).unwrap(); assert_eq!(ledger.admissions, 0); assert_eq!(ledger.charged_roles, 0); assert_eq!(report[if arm == 0 { "left_reserved_roles" } else { "right_reserved_roles" }], 0);
        let after = engine(&database(&dir, INDEX, ComparisonKind::ContinuousRollout), &corpus.seed().scope).unwrap(); assert_eq!(after.receipts(), canonical_before[arm].receipts()); assert_eq!(after.canonical_bytes(), canonical_before[arm].canonical_bytes());
        assert!(fs::read_dir(&dir).unwrap().all(|e| { let name = e.unwrap().file_name().to_string_lossy().into_owned(); !name.starts_with("admission-") && !name.starts_with("raw-") }));
    }
    assert_eq!(inventory(&fixture.source), source_before); let completed_before = inventory(&target);
    let repeated = serde_json::to_value(resume_native_selected(&target, &fixture.source, &binding, &Cancellation::default(), || reserve_trap(&calls)).unwrap()).unwrap(); assert_eq!(repeated, report); assert_eq!(calls.load(Ordering::SeqCst), 0); assert_eq!(inventory(&target), completed_before); assert_eq!(inventory(&fixture.source), source_before);
    // A zero-current-admission recovery does not authenticate the absent old
    // native workflow or imply zero historical scripted provider work.
}

#[test]
fn actual_right_unknown_turn_reservations_refuse_before_callback_or_left_mutation() {
    let fixture = Fixture::new("both-arm-native-budget"); let source_before = inventory(&fixture.source); let plan = fixture.plan("native2-budget-preflight"); let target = fixture.root.join("selected"); let destination = new_destination(&plan, &target).unwrap(); let binding = destination.manifest.binding.clone(); let right = target.join("right"); let corpus = suite().unwrap(); let step = &corpus.steps()[INDEX];
    let mut ledger = Ledger::load(&right, &binding).unwrap(); ledger.begin_invocation().unwrap();
    for admission in 0..27 { assert_eq!(ledger.admit(&format!("scene-{}", step.scene()), step.id()).unwrap(), admission); assert!(!right.join(format!("admission-{admission:02}-settled.json")).exists()); }
    // Measured invocation finish, actual reservations remain deliberately unknown.
    ledger.finish().unwrap(); let settled: Settlement = decode(&right.join("invocation-00-settled.json"), 4096).unwrap(); assert_eq!((settled.index, settled.roles), (0, 0)); assert_eq!(settled.binding, binding); drop(ledger);
    let persisted = Ledger::load(&right, &binding).unwrap(); assert_eq!((persisted.invocations, persisted.admissions, persisted.charged_roles), (1, 27, 81)); assert_eq!(persisted.charged_ms, 27 * TURN_MS + settled.ms); assert!(persisted.remaining() >= PREPARATION_MS); assert!(persisted.remaining().saturating_sub(PREPARATION_MS) < TURN_MS + CLEANUP_RESERVE_MS); drop(persisted);
    for arm in ARM_NAMES { assert!(!database(&target.join(arm), INDEX, ComparisonKind::ContinuousRollout).exists()); assert!(!checkpoint_path(&target.join(arm), INDEX).exists()); }
    drop(destination); drop(plan); assert!(inventory(&target.join("left")).is_empty()); let target_before = inventory(&target); let calls = AtomicUsize::new(0);
    let error = native_error(resume_native_selected(&target, &fixture.source, &binding, &Cancellation::default(), || reserve_trap(&calls)));
    assert_eq!(calls.load(Ordering::SeqCst), 0); assert!(!error.cleanup_uncertain()); assert_eq!(inventory(&target), target_before); assert_eq!(inventory(&fixture.source), source_before); assert_eq!(error.code(), "RunBudget"); assert!(inventory(&target.join("left")).is_empty());
}

// Actual guard-terminal missing-checkpoint is not covered by this one-scene
// source. The independent public scripted selected2 packet covers that case;
// no synthetic/native Failed row or cause is manufactured for this packet.
