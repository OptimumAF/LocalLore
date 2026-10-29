// Copyright 2026 LocalLore contributors. SPDX-License-Identifier: Apache-2.0
//! Independent main backport freeze on d5a6e84c: SOURCE ONLY / UNRUN.
//! Existing public APIs and typed Protocol3 wrapper metadata only. No generated
//! report, accepted receipt, canonical Store, native IPC, GUI or model evidence.
use super::*;
use crate::models::ModelManager;
use std::sync::OnceLock;

type Inventory = BTreeMap<PathBuf, Option<Vec<u8>>>;
fn inventory(root: &Path) -> Inventory {
    fn visit(root: &Path, path: &Path, depth: usize, out: &mut Inventory) {
        assert!(depth <= 6 && out.len() < 64);
        let metadata = fs::symlink_metadata(path).unwrap();
        assert!(!metadata.file_type().is_symlink());
        #[cfg(windows)]
        {
            use std::os::windows::fs::MetadataExt;
            assert_eq!(metadata.file_attributes() & 0x400, 0);
        }
        let relative = path.strip_prefix(root).unwrap().to_owned();
        let value = if metadata.is_dir() {
            for entry in fs::read_dir(path).unwrap() {
                visit(root, &entry.unwrap().path(), depth + 1, out);
            }
            None
        } else {
            assert!(metadata.is_file() && metadata.len() <= 64 * 1024);
            Some(fs::read(path).unwrap())
        };
        assert!(out.insert(relative, value).is_none());
    }
    let mut result = Inventory::new();
    visit(root, root, 0, &mut result);
    result
}
#[track_caller]
fn refused<T>(result: Result<T>) {
    match result {
        Err(error) => assert_eq!(error, "UnknownEvaluationRun"),
        Ok(_) => panic!("expected refusal of another native window's capability"),
    }
}
fn token(status: &Value) -> &str {
    status["run_token"].as_str().unwrap()
}
struct Fixture {
    root: PathBuf,
    manager: Arc<EvaluationManager>,
    models: Arc<ModelManager>,
    lease: Arc<WindowLease>,
    epoch: u64,
    run: String,
    client: String,
    native: bool,
}
impl Fixture {
    fn new(native: bool) -> Self {
        let root = std::env::temp_dir().join(format!("full-run-window-identity-{}", uuid().unwrap()));
        fs::create_dir(&root).unwrap();
        let manager = Arc::new(EvaluationManager::new(root.join("evaluations")));
        let models = Arc::new(ModelManager::new(root.join("models"), root.join("resources")));
        let lease = Arc::new(WindowLease::default());
        let epoch = lease.begin().unwrap();
        let run = uuid().unwrap();
        let client = uuid().unwrap();
        let directory = manager.full_comparison_root().join(&run);
        fs::create_dir_all(&directory).unwrap();
        // Reuse the accepted typed index/current-binding fixture. There is no
        // work directory, report, NativeProfile or outcome to mislabel.
        let index = Index {
            version: if native { 2 } else { 1 },
            protocol_version: 3,
            input_lane: if native { "approved_native" } else { "scripted_baseline" }.into(),
            run_id: run.clone(),
            client_id: client.clone(),
            kind: core::ComparisonKind::ContinuousRollout,
            initial_batch: 1,
            created_ms: 1,
            binding: wire::current_binding(native).unwrap(),
        };
        fs::write(directory.join("desktop.json"), serde_json::to_vec(&index).unwrap()).unwrap();
        Self { root, manager, models, lease, epoch, run, client, native }
    }
    fn lookup(&self, lease: &WindowLease) -> Value {
        let value = if self.native {
            self.manager.full_comparison_lookup_native(lease, self.epoch, true, &self.client)
        } else {
            self.manager.full_comparison_lookup(lease, self.epoch, true, &self.client)
        }.unwrap();
        assert_eq!(value["version"], if self.native { 2 } else { 1 });
        assert_eq!(value["protocol_version"], 3);
        assert_eq!(value["input_lane"], if self.native { "approved_native" } else { "scripted_baseline" });
        assert_eq!(value["run_id"], self.run);
        assert_eq!(value["running"], false);
        assert_eq!(value["report_ready"], false);
        value
    }
    fn status(&self, lease: &WindowLease, cap: &str) -> Result<Value> {
        if self.native { self.manager.full_comparison_status_native(lease, self.epoch, true, cap) }
        else { self.manager.full_comparison_status(lease, self.epoch, true, cap) }
    }
    fn cancel(&self, lease: &WindowLease, cap: &str) -> Result<Value> {
        if self.native { self.manager.full_comparison_cancel_native(lease, self.epoch, true, cap, 1) }
        else { self.manager.full_comparison_cancel(lease, self.epoch, true, cap, 1) }
    }
    fn resume(&self, lease: &Arc<WindowLease>, cap: &str) -> Result<Value> {
        if self.native {
            self.manager.full_comparison_resume_native(lease, &self.models, self.epoch, true,
                FullComparisonNativeResume { run_token: cap.into(), max_new_scenes: 1 },
                |_| panic!("stolen capability must be refused before native consent"))
        } else { self.manager.full_comparison_resume(lease, self.epoch, true, cap, 1) }
    }
    fn close(&self, lease: &WindowLease, cap: &str) -> Result<Value> {
        if self.native { self.manager.full_comparison_close_native(lease, self.epoch, false, cap) }
        else { self.manager.full_comparison_close(lease, self.epoch, false, cap) }
    }
}
struct Retained {
    _manager: Arc<EvaluationManager>,
    _models: Arc<ModelManager>,
    _lease: Arc<WindowLease>,
}
impl Drop for Fixture {
    fn drop(&mut self) {
        self.manager.retire(self.epoch);
        self.manager.drain(self.epoch);
        let _ = self.manager.selected_cleanup_retired(self.epoch);
        self.models.close(None, self.models.retire());
        let _ = self.manager.selected_cleanup_retired(self.epoch);
        if self.manager.cleanup_complete() && self.models.cleanup_complete() {
            if let Some(closed) = self.lease.invalidate(&format!("main-{}", self.epoch)) {
                self.lease.finish_close(closed, || {});
            }
        } else {
            // Preserve the same real owner pair on unexpected cleanup failure.
            static HELD: OnceLock<Mutex<Vec<Retained>>> = OnceLock::new();
            HELD.get_or_init(|| Mutex::new(vec![])).lock().unwrap().push(Retained {
                _manager: self.manager.clone(), _models: self.models.clone(), _lease: self.lease.clone(),
            });
        }
        // Synthetic source files remain on disk even after a failed assertion.
    }
}
fn independent_same_epoch_handles(native: bool) {
    let f = Fixture::new(native);
    let before = inventory(&f.root);
    let model_before = f.models.status().unwrap();
    let initial = f.lookup(&f.lease);
    assert_eq!(initial["phase"], "retained");
    let first = token(&initial).to_owned();
    assert_eq!(token(&f.lookup(&f.lease)), first, "same-owner retry reuses its capability");
    let other = Arc::new(WindowLease::default());
    assert_eq!(other.begin().unwrap(), f.epoch);
    let second = token(&f.lookup(&other)).to_owned();
    assert_ne!(first, second, "explicit lookup by another lease must not rebind the first token");
    assert_eq!(token(&f.lookup(&other)), second);
    for (owner, own, stolen) in [(&f.lease, &first, &second), (&other, &second, &first)] {
        assert_eq!(f.status(owner, own).unwrap()["run_id"], f.run);
        refused(f.status(owner, stolen));
        refused(f.cancel(owner, stolen));
        refused(f.resume(owner, stolen));
        refused(f.close(owner, stolen));
        assert_eq!(f.status(owner, own).unwrap()["run_token"], own.as_str());
    }
    f.close(&f.lease, &first).unwrap();
    refused(f.status(&f.lease, &first));
    assert_eq!(f.status(&other, &second).unwrap()["run_id"], f.run);
    let reopened = token(&f.lookup(&f.lease)).to_owned();
    assert_ne!(reopened, first);
    assert_ne!(reopened, second);
    f.close(&f.lease, &reopened).unwrap();
    f.close(&other, &second).unwrap();
    assert_eq!(f.models.status().unwrap(), model_before);
    assert_eq!(inventory(&f.root), before);
}
#[test]
fn scripted3_same_epoch_windows_have_distinct_nontransferable_handles() {
    independent_same_epoch_handles(false);
}
#[test]
fn native3_same_epoch_windows_have_distinct_nontransferable_handles() {
    independent_same_epoch_handles(true);
}
#[test]
fn dropped_owner_cannot_be_replaced_by_another_same_epoch_window() {
    for native in [false, true] {
        let f = Fixture::new(native);
        let before = inventory(&f.root);
        let old = Arc::new(WindowLease::default());
        assert_eq!(old.begin().unwrap(), f.epoch);
        let previous = token(&f.lookup(&old)).to_owned();
        drop(old);
        let replacement = Arc::new(WindowLease::default());
        assert_eq!(replacement.begin().unwrap(), f.epoch);
        refused(f.status(&replacement, &previous));
        refused(f.cancel(&replacement, &previous));
        refused(f.resume(&replacement, &previous));
        refused(f.close(&replacement, &previous));
        let fresh = token(&f.lookup(&replacement)).to_owned();
        assert_ne!(fresh, previous);
        f.close(&replacement, &fresh).unwrap();
        assert_eq!(inventory(&f.root), before);
    }
}
#[test]
fn existing_four_handle_lru_bound_applies_across_same_epoch_windows() {
    for native in [false, true] {
        let f = Fixture::new(native);
        let before = inventory(&f.root);
        let mut owners = vec![];
        let mut tokens = vec![];
        for _ in 0..4 {
            let owner = Arc::new(WindowLease::default());
            assert_eq!(owner.begin().unwrap(), f.epoch);
            let cap = token(&f.lookup(&owner)).to_owned();
            assert!(!tokens.contains(&cap));
            owners.push(owner);
            tokens.push(cap);
        }
        assert_eq!(f.manager.state().unwrap().tokens.len(), 4);
        f.manager.state().unwrap().tokens.get_mut(&tokens[0]).unwrap().touched =
            Instant::now().checked_sub(Duration::from_secs(1)).unwrap();
        let fifth = Arc::new(WindowLease::default());
        assert_eq!(fifth.begin().unwrap(), f.epoch);
        let cap = token(&f.lookup(&fifth)).to_owned();
        assert!(!tokens.contains(&cap));
        assert_eq!(f.manager.state().unwrap().tokens.len(), 4);
        refused(f.status(&owners[0], &tokens[0]));
        for index in 1..4 {
            assert_eq!(f.status(&owners[index], &tokens[index]).unwrap()["run_id"], f.run);
            refused(f.status(&fifth, &tokens[index]));
            f.close(&owners[index], &tokens[index]).unwrap();
        }
        f.close(&fifth, &cap).unwrap();
        assert_eq!(f.manager.state().unwrap().tokens.len(), 0);
        assert_eq!(inventory(&f.root), before);
    }
}
