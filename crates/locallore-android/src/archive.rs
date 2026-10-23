// Copyright 2026 LocalLore contributors. SPDX-License-Identifier: Apache-2.0
//! App-private Android archive ownership. Store/archive v1 alone validates and commits canon.
//! Ancestors are trusted application construction; this is not a same-UID filesystem boundary.
use locallore_storage::{
    playable_archive::MAX_ARCHIVE_BYTES, validate_archive, ArchiveError, DeletionError,
    PreparedBranchDeletion, PreparedStoryDeletion, StorageError, Store, ValidatedArchive,
};
use serde::Deserialize;
use serde_json::{json, Value};
use std::{
    collections::BTreeMap,
    fs,
    path::{Path, PathBuf},
    sync::{
        atomic::{AtomicBool, AtomicU64, Ordering},
        Arc, Mutex, Weak,
    },
};

pub const MAX_CONTROL_BYTES: usize = 16 * 1024;
pub const MAX_DELETION_BYTES: usize = 64 * 1024;
static NEXT: AtomicU64 = AtomicU64::new(0);
type Result<T> = std::result::Result<T, &'static str>;
fn next() -> Result<u64> {
    NEXT.fetch_update(Ordering::SeqCst, Ordering::SeqCst, |id| {
        id.checked_add(1).filter(|id| *id <= i64::MAX as u64)
    })
    .map(|id| id + 1)
    .map_err(|_| "WorkspaceLimit")
}
#[derive(Default)]
pub struct ArchiveRegistry {
    entries: Mutex<RegistryState>,
}
#[derive(Default)]
struct RegistryState {
    leases: BTreeMap<u64, Arc<Lease>>,
    retired: Vec<Weak<Lease>>,
    opening: usize,
}
struct Opening<'a>(&'a ArchiveRegistry);
impl Drop for Opening<'_> {
    fn drop(&mut self) {
        if let Ok(mut state) = self.0.entries.lock() {
            state.opening -= 1;
        }
    }
}
struct Lease {
    handle: u64,
    database: PathBuf,
    staging: PathBuf,
    closed: AtomicBool,
    generation: AtomicU64,
    state: Mutex<State>,
    #[cfg(test)]
    hook: Mutex<Option<TestHook>>,
}
#[derive(Default)]
struct State {
    active: Option<u64>,
    pending: Option<Pending>,
}
struct Pending {
    token: u64,
    capability: Capability,
}
enum Capability {
    BranchDelete(Box<PreparedBranchDeletion>),
    Delete(Box<PreparedStoryDeletion>),
    Export(Vec<u8>),
    Import {
        bytes: Vec<u8>,
        validated: Box<ValidatedArchive>,
    },
}
#[derive(Clone, Copy)]
enum Kind {
    BranchDelete,
    Delete,
    Export,
    Import,
}
impl Capability {
    fn kind(&self, kind: Kind) -> bool {
        matches!(
            (self, kind),
            (Self::Export(_), Kind::Export)
                | (Self::Import { .. }, Kind::Import)
                | (Self::Delete(_), Kind::Delete)
                | (Self::BranchDelete(_), Kind::BranchDelete)
        )
    }
}
#[derive(Deserialize)]
#[serde(deny_unknown_fields)]
struct ExportRequest {
    story: String,
    branch: String,
    expected_revision: u64,
}
struct Operation {
    lease: Arc<Lease>,
    id: u64,
}
impl Operation {
    fn cancelled(&self) -> bool {
        self.lease.closed.load(Ordering::SeqCst)
            || self.lease.generation.load(Ordering::SeqCst) != self.id
    }
    fn check(&self) -> Result<()> {
        if self.cancelled() {
            Err("Cancelled")
        } else {
            Ok(())
        }
    }
    fn publish(&self, capability: Capability) -> Result<()> {
        let mut state = self.lease.state.lock().map_err(|_| "Internal")?;
        self.check()?;
        if state.active != Some(self.id) {
            return Err("Cancelled");
        }
        state.pending = Some(Pending {
            token: self.id,
            capability,
        });
        Ok(())
    }
    #[cfg(test)]
    fn hook(&self, phase: &str, path: &Path) {
        let hook = self.lease.hook.lock().unwrap().clone();
        if let Some(hook) = hook {
            hook(phase, path);
        }
    }
}
impl Drop for Operation {
    fn drop(&mut self) {
        if let Ok(mut state) = self.lease.state.lock() {
            if state.active == Some(self.id) {
                state.active = None;
            }
        }
    }
}
impl ArchiveRegistry {
    /// Existing private roots only. No wire identifier/title is used as a filesystem path.
    pub fn open(&self, database: &Path, staging_root: &Path) -> std::result::Result<u64, String> {
        self.open_inner(database, staging_root)
            .map_err(str::to_owned)
    }
    fn open_inner(&self, database: &Path, staging_root: &Path) -> Result<u64> {
        if !database.is_absolute() || !staging_root.is_absolute() {
            return Err("Io");
        }
        regular(database)?;
        directory(staging_root)?;
        let parent = database
            .parent()
            .ok_or("Io")?
            .canonicalize()
            .map_err(|_| "Io")?;
        let database = database.canonicalize().map_err(|_| "Io")?;
        if database.parent() != Some(parent.as_path()) {
            return Err("Io");
        }
        let staging = staging_root.canonicalize().map_err(|_| "Io")?;
        {
            let mut entries = self.entries.lock().map_err(|_| "Internal")?;
            entries.retired.retain(|lease| lease.strong_count() != 0);
            if entries.leases.len() + entries.retired.len() + entries.opening >= 4 {
                return Err("WorkspaceLimit");
            }
            entries.opening += 1;
        }
        let _opening = Opening(self);
        // Read-only validation cannot initialize, migrate or adopt an unknown database.
        drop(Store::open_read_only(&database).map_err(storage_error)?);
        let mut entries = self.entries.lock().map_err(|_| "Internal")?;
        let handle = next()?;
        entries.leases.insert(
            handle,
            Arc::new(Lease {
                handle,
                database,
                staging,
                closed: AtomicBool::new(false),
                generation: AtomicU64::new(0),
                state: Mutex::new(State::default()),
                #[cfg(test)]
                hook: Mutex::new(None),
            }),
        );
        Ok(handle)
    }
    fn lease(&self, handle: u64) -> Result<Arc<Lease>> {
        self.entries
            .lock()
            .map_err(|_| "Internal")?
            .leases
            .get(&handle)
            .cloned()
            .ok_or("InvalidHandle")
    }
    fn begin(&self, handle: u64) -> Result<Operation> {
        let lease = self.lease(handle)?;
        let mut state = lease.state.lock().map_err(|_| "Internal")?;
        if lease.closed.load(Ordering::SeqCst) {
            return Err("InvalidHandle");
        }
        if state.active.is_some() {
            return Err("Busy");
        }
        let old = state.pending.take();
        lease.generation.store(0, Ordering::SeqCst);
        let id = match next() {
            Ok(id) => id,
            Err(error) => {
                drop(state);
                drop(old);
                return Err(error);
            }
        };
        lease.generation.store(id, Ordering::SeqCst);
        state.active = Some(id);
        drop(state);
        drop(old);
        Ok(Operation { lease, id })
    }
    fn consume(&self, handle: u64, token: u64, kind: Kind) -> Result<(Operation, Capability)> {
        let lease = self.lease(handle)?;
        let mut state = lease.state.lock().map_err(|_| "Internal")?;
        if lease.closed.load(Ordering::SeqCst) {
            return Err("InvalidHandle");
        }
        if state.active.is_some() {
            return Err("Busy");
        }
        let valid = state
            .pending
            .as_ref()
            .is_some_and(|pending| pending.token == token && pending.capability.kind(kind));
        if !valid || lease.generation.load(Ordering::SeqCst) != token {
            return Err("InvalidToken");
        }
        let capability = state.pending.take().ok_or("InvalidToken")?.capability;
        state.active = Some(token);
        drop(state);
        Ok((Operation { lease, id: token }, capability))
    }
    // JNI rejects over-cap/null inputs before copying them. Preserve the same replacement
    // semantics as a parsed prepare, without cancelling an already-running operation.
    #[cfg_attr(not(target_os = "android"), allow(dead_code))]
    pub(crate) fn reject_prepare(&self, handle: u64, error: &'static str) -> Vec<u8> {
        control(|| {
            let _op = self.begin(handle)?;
            Err(error)
        })
    }
    pub fn prepare_export(&self, handle: u64, request: &[u8]) -> Vec<u8> {
        control(|| {
            let op = self.begin(handle)?;
            if request.len() > MAX_CONTROL_BYTES {
                return Err("TooLarge");
            }
            let request: ExportRequest =
                serde_json::from_slice(request).map_err(|_| "Malformed")?;
            op.check()?;
            regular(&op.lease.database)?;
            let mut store = Store::open_read_only(&op.lease.database).map_err(storage_error)?;
            let archive = store
                .export_archive(&request.story, &|| op.cancelled())
                .map_err(archive_error)?;
            drop(store);
            if archive.preview().branch_heads.get(&request.branch)
                != Some(&request.expected_revision)
            {
                return Err("Stale");
            }
            let reply = success(json!({"token":op.id,"preview":archive.preview()}))?;
            #[cfg(test)]
            op.hook("export-ready", &op.lease.database);
            op.publish(Capability::Export(archive.bytes().to_vec()))?;
            Ok(reply)
        })
    }
    pub fn prepare_import(&self, handle: u64, bytes: &[u8]) -> Vec<u8> {
        control(|| {
            let op = self.begin(handle)?;
            if bytes.len() > MAX_ARCHIVE_BYTES {
                return Err("TooLarge");
            }
            let validated = validate_archive(bytes, &|| op.cancelled()).map_err(archive_error)?;
            let reply = success(json!({"token":op.id,"preview":validated.preview()}))?;
            #[cfg(test)]
            op.hook("import-ready", &op.lease.database);
            op.publish(Capability::Import {
                bytes: bytes.to_vec(),
                validated: Box::new(validated),
            })?;
            Ok(reply)
        })
    }
    pub fn export_bytes(&self, handle: u64, token: u64) -> std::result::Result<Vec<u8>, String> {
        std::panic::catch_unwind(std::panic::AssertUnwindSafe(|| {
            let (op, capability) = self.consume(handle, token, Kind::Export)?;
            let Capability::Export(bytes) = capability else {
                return Err("InvalidToken");
            };
            op.check()?;
            Ok(bytes)
        }))
        .unwrap_or(Err("Internal"))
        .map_err(str::to_owned)
    }
    pub fn commit_import(&self, handle: u64, token: u64) -> Vec<u8> {
        control(|| {
            let (op, capability) = self.consume(handle, token, Kind::Import)?;
            let Capability::Import { bytes, validated } = capability else {
                return Err("InvalidToken");
            };
            // Revalidate the same immutable bytes. This new token belongs only to staging;
            // the exact opaque capability prepared above is retained for the destination.
            let staged = validate_archive(&bytes, &|| op.cancelled()).map_err(archive_error)?;
            directory(&op.lease.staging)?;
            let stage = Stage::create(&op.lease.staging, op.lease.handle, op.id)?;
            let staged_result = (|| {
                #[cfg(test)]
                op.hook("stage-created", &stage.path);
                op.check()?;
                let mut store =
                    Store::open(&stage.path.join("staged.sqlite3"), None).map_err(storage_error)?;
                store
                    .import_archive(staged, &|| op.cancelled())
                    .map_err(archive_error)?;
                for (branch, head) in &validated.preview().branch_heads {
                    if validated.preview().retired_branch_ids.contains(branch) {
                        continue; // Import already internally replayed these ancestry prefixes.
                    }
                    op.check()?;
                    let scope = locallore::contracts::Scope {
                        story: validated.preview().story_id.clone(),
                        branch: branch.clone(),
                    };
                    if store
                        .resume(&scope)
                        .map_err(|_| "Integrity")?
                        .engine
                        .revision()
                        != *head
                    {
                        return Err("Integrity");
                    }
                }
                drop(store);
                #[cfg(test)]
                op.hook("staged", &stage.path);
                op.check()
            })();
            // Even cancellation/error must close Store and pass exact owned cleanup first.
            stage.cleanup()?;
            staged_result?;
            #[cfg(test)]
            op.hook("before-target", &op.lease.database);
            op.check()?;
            regular(&op.lease.database)?;
            let mut target = Store::open(&op.lease.database, None).map_err(storage_error)?;
            let imported = target
                .import_archive(*validated, &|| op.cancelled())
                .map_err(archive_error)?;
            drop(target);
            #[cfg(test)]
            op.hook("target-imported", &op.lease.database);
            // Commit is Store's linearization point. A late cancel may suppress its reply;
            // callers must reconcile the library, never assume that cancellation rolls it back.
            op.check()?;
            success(
                json!({"root":imported.root,"branches":imported.branches,"committed_turns":imported.committed_turns}),
            )
        })
    }
    pub fn prepare_delete(&self, handle: u64, request: &[u8]) -> Vec<u8> {
        control(|| {
            let op = self.begin(handle)?;
            if request.len() > MAX_CONTROL_BYTES {
                return Err("TooLarge");
            }
            let request: ExportRequest =
                serde_json::from_slice(request).map_err(|_| "Malformed")?;
            op.check()?;
            regular(&op.lease.database)?;
            let mut store = Store::open_read_only(&op.lease.database).map_err(storage_error)?;
            let prepared = store
                .prepare_story_deletion(
                    &locallore::contracts::Scope {
                        story: request.story,
                        branch: request.branch,
                    },
                    request.expected_revision,
                    &|| op.cancelled(),
                )
                .map_err(deletion_error)?;
            let reply = success_bounded(
                json!({"token":op.id,"preview":prepared.preview()}),
                MAX_DELETION_BYTES,
            )?;
            drop(store);
            op.publish(Capability::Delete(Box::new(prepared)))?;
            Ok(reply)
        })
    }
    pub fn commit_delete(
        &self,
        handle: u64,
        token: u64,
        workspaces: &crate::workspace::WorkspaceRegistry,
    ) -> Vec<u8> {
        control(|| {
            let (op, capability) = self.consume(handle, token, Kind::Delete)?;
            let Capability::Delete(prepared) = capability else {
                return Err("InvalidToken");
            };
            let story = prepared.preview().story_id.clone();
            let deleted = workspaces.with_story_deletion(&op.lease.database, &story, || {
                op.check()?;
                regular(&op.lease.database)?;
                let mut store = Store::open(&op.lease.database, None).map_err(storage_error)?;
                #[cfg(test)]
                op.hook("before-delete", &op.lease.database);
                store
                    .delete_story(*prepared, &|| op.cancelled())
                    .map_err(deletion_error)
            })?;
            #[cfg(test)]
            op.hook("target-deleted", &op.lease.database);
            // Accepted deletion already invalidated all matching native sessions.
            // A late cancellation is uncertain to the caller: always reconcile the library.
            op.check()?;
            success(json!(deleted))
        })
    }
    pub fn prepare_branch_delete(&self, handle: u64, request: &[u8]) -> Vec<u8> {
        control(|| {
            let op = self.begin(handle)?;
            if request.len() > MAX_CONTROL_BYTES {
                return Err("TooLarge");
            }
            let request: ExportRequest =
                serde_json::from_slice(request).map_err(|_| "Malformed")?;
            op.check()?;
            regular(&op.lease.database)?;
            let mut store = Store::open_read_only(&op.lease.database).map_err(storage_error)?;
            let prepared = store
                .prepare_branch_deletion(
                    &locallore::contracts::Scope {
                        story: request.story,
                        branch: request.branch,
                    },
                    request.expected_revision,
                    &|| op.cancelled(),
                )
                .map_err(deletion_error)?;
            let reply = success_bounded(
                json!({"token":op.id,"preview":prepared.preview()}),
                MAX_DELETION_BYTES,
            )?;
            drop(store);
            op.publish(Capability::BranchDelete(Box::new(prepared)))?;
            Ok(reply)
        })
    }
    pub fn commit_branch_delete(
        &self,
        handle: u64,
        token: u64,
        workspaces: &crate::workspace::WorkspaceRegistry,
    ) -> Vec<u8> {
        control(|| {
            let (op, capability) = self.consume(handle, token, Kind::BranchDelete)?;
            let Capability::BranchDelete(prepared) = capability else {
                return Err("InvalidToken");
            };
            let story = prepared.preview().scope.story.clone();
            let deleted = workspaces.with_branch_deletion(&op.lease.database, &story, || {
                op.check()?;
                regular(&op.lease.database)?;
                let mut store = Store::open(&op.lease.database, None).map_err(storage_error)?;
                let result = store
                    .delete_branch(*prepared, &|| op.cancelled())
                    .map_err(deletion_error)?;
                let invalidated = result.invalidated_branches.clone();
                Ok((result, invalidated))
            })?;
            op.check()?; // A late cancellation requires actual library reconciliation.
            success(json!(deleted))
        })
    }
    pub fn cancel(&self, handle: u64) {
        if let Ok(lease) = self.lease(handle) {
            invalidate(&lease);
        }
    }
    pub fn close(&self, handle: u64) {
        let lease = self.entries.lock().ok().and_then(|mut entries| {
            let lease = entries.leases.remove(&handle)?;
            entries.retired.push(Arc::downgrade(&lease));
            Some(lease)
        });
        if let Some(lease) = lease {
            lease.closed.store(true, Ordering::SeqCst);
            invalidate(&lease);
        }
    }
}
fn invalidate(lease: &Lease) {
    // Signal first, without waiting for replay, SQLite or a long-lived operation lock.
    lease.generation.store(0, Ordering::SeqCst);
    let old = lease.state.lock().ok().and_then(|mut state| {
        // A begin already inside the short metadata section may have raced the
        // first signal. Fence that generation too before cancellation returns.
        lease.generation.store(0, Ordering::SeqCst);
        state.pending.take()
    });
    drop(old);
}
fn regular(path: &Path) -> Result<()> {
    let metadata = fs::symlink_metadata(path).map_err(|_| "Io")?;
    if metadata.file_type().is_symlink() || !metadata.is_file() {
        Err("Io")
    } else {
        Ok(())
    }
}
fn directory(path: &Path) -> Result<()> {
    let metadata = fs::symlink_metadata(path).map_err(|_| "Io")?;
    if metadata.file_type().is_symlink() || !metadata.is_dir() {
        Err("Io")
    } else {
        Ok(())
    }
}
struct Stage {
    path: PathBuf,
}
impl Stage {
    fn create(root: &Path, owner: u64, operation: u64) -> Result<Self> {
        let path = root.join(format!("archive-{owner}-{operation}"));
        fs::create_dir(&path).map_err(|_| "Io")?;
        Ok(Self { path })
    }
    fn cleanup(self) -> Result<()> {
        directory(&self.path)?;
        let known = [
            "staged.sqlite3",
            "staged.sqlite3-journal",
            "staged.sqlite3-wal",
            "staged.sqlite3-shm",
        ];
        let mut files = Vec::new();
        for entry in fs::read_dir(&self.path).map_err(|_| "Io")? {
            let entry = entry.map_err(|_| "Io")?;
            if !known.iter().any(|name| entry.file_name() == *name) {
                return Err("Io");
            }
            regular(&entry.path())?;
            files.push(entry.path());
        }
        for file in files {
            fs::remove_file(file).map_err(|_| "Io")?;
        }
        fs::remove_dir(self.path).map_err(|_| "Io")
    }
}
fn success(data: Value) -> Result<Vec<u8>> {
    success_bounded(data, MAX_CONTROL_BYTES)
}
fn success_bounded(data: Value, cap: usize) -> Result<Vec<u8>> {
    let bytes = serde_json::to_vec(&json!({"version":1,"status":"ok","data":data}))
        .map_err(|_| "Internal")?;
    if bytes.len() > cap {
        Err("TooLarge")
    } else {
        Ok(bytes)
    }
}
pub(crate) fn error_bytes(error: &str) -> Vec<u8> {
    serde_json::to_vec(&json!({"version":1,"status":"rejected","error":error})).unwrap_or_default()
}
fn control(operation: impl FnOnce() -> Result<Vec<u8>>) -> Vec<u8> {
    std::panic::catch_unwind(std::panic::AssertUnwindSafe(operation))
        .unwrap_or(Err("Internal"))
        .unwrap_or_else(error_bytes)
}
fn archive_error(error: ArchiveError) -> &'static str {
    match error {
        ArchiveError::Malformed => "Malformed",
        ArchiveError::Unsupported => "Unsupported",
        ArchiveError::Integrity => "Integrity",
        ArchiveError::TooLarge => "TooLarge",
        ArchiveError::Conflict => "Conflict",
        ArchiveError::Cancelled => "Cancelled",
        ArchiveError::Busy => "Busy",
        ArchiveError::Full => "Full",
        ArchiveError::Database => "Database",
        ArchiveError::NotFound => "NotFound",
    }
}
fn deletion_error(error: DeletionError) -> &'static str {
    match error {
        DeletionError::Malformed => "Malformed",
        DeletionError::NotFound => "NotFound",
        DeletionError::Stale => "Stale",
        DeletionError::Cancelled => "Cancelled",
        DeletionError::Busy => "Busy",
        DeletionError::Full => "Full",
        DeletionError::Integrity => "Integrity",
        DeletionError::Database => "Database",
        DeletionError::Io => "Io",
        DeletionError::TooLarge => "TooLarge",
    }
}
fn storage_error(error: StorageError) -> &'static str {
    match error {
        StorageError::Io => "Io",
        StorageError::Busy => "Busy",
        StorageError::NotFound => "NotFound",
        StorageError::FutureVersion | StorageError::BackupRequired | StorageError::BackupExists => {
            "Unsupported"
        }
        StorageError::ForeignDatabase
        | StorageError::SchemaMismatch
        | StorageError::Integrity
        | StorageError::InvalidSeed => "Integrity",
        _ => "Database",
    }
}
#[cfg(test)]
type TestHook = Arc<dyn Fn(&str, &Path) + Send + Sync>;

#[cfg(test)]
mod tests {
    use super::*;
    use std::{
        sync::Barrier,
        thread,
        time::{SystemTime, UNIX_EPOCH},
    };
    struct Fixture {
        root: PathBuf,
        database: PathBuf,
        staging: PathBuf,
        registry: Arc<ArchiveRegistry>,
        handle: u64,
        bytes: Vec<u8>,
    }
    impl Fixture {
        fn new() -> Self {
            let root = std::env::temp_dir().join(format!(
                "locallore-archive-native-unit-{}-{}-{}",
                std::process::id(),
                SystemTime::now()
                    .duration_since(UNIX_EPOCH)
                    .unwrap()
                    .as_nanos(),
                next().unwrap()
            ));
            fs::create_dir(&root).unwrap();
            let database = root.join("destination.sqlite3");
            let staging = root.join("staging");
            fs::create_dir(&staging).unwrap();
            let mut store = Store::open(&database, None).unwrap();
            let mut seed: locallore::contracts::Seed =
                serde_json::from_str(include_str!("../../../fixtures/lantern_quay.json")).unwrap();
            seed.scope.story = "retained".into();
            store
                .create_story("Retained synthetic story", seed.clone())
                .unwrap();
            drop(store);
            let mut source = Store::open(&root.join("source.sqlite3"), None).unwrap();
            seed.scope.story = "imported".into();
            source
                .create_story("Imported synthetic story", seed)
                .unwrap();
            let bytes = source
                .export_archive("imported", &|| false)
                .unwrap()
                .bytes()
                .to_vec();
            drop(source);
            let registry = Arc::new(ArchiveRegistry::default());
            let handle = registry.open(&database, &staging).unwrap();
            Self {
                root,
                database,
                staging,
                registry,
                handle,
                bytes,
            }
        }
        fn hook(&self, hook: TestHook) {
            let lease = self.registry.lease(self.handle).unwrap();
            *lease.hook.lock().unwrap() = Some(hook);
        }
        fn prepared(&self) -> u64 {
            data(self.registry.prepare_import(self.handle, &self.bytes))["token"]
                .as_u64()
                .unwrap()
        }
        fn count(&self) -> usize {
            Store::open(&self.database, None)
                .unwrap()
                .stories()
                .unwrap()
                .len()
        }
    }
    impl Drop for Fixture {
        fn drop(&mut self) {
            self.registry.close(self.handle);
            fs::remove_dir_all(&self.root).unwrap();
        }
    }
    fn reply(bytes: Vec<u8>) -> Value {
        serde_json::from_slice(&bytes).unwrap()
    }
    fn data(bytes: Vec<u8>) -> Value {
        let value = reply(bytes);
        assert_eq!(value["status"], "ok");
        value["data"].clone()
    }

    #[test]
    fn pre_copy_rejection_invalidates_idle_grant_but_preserves_an_active_operation() {
        let fixture = Fixture::new();
        let token = fixture.prepared();
        assert_eq!(
            reply(fixture.registry.reject_prepare(fixture.handle, "TooLarge"))["error"],
            "TooLarge"
        );
        assert_eq!(
            reply(fixture.registry.commit_import(fixture.handle, token))["error"],
            "InvalidToken"
        );
        let op = fixture.registry.begin(fixture.handle).unwrap();
        assert_eq!(
            reply(fixture.registry.reject_prepare(fixture.handle, "Malformed"))["error"],
            "Busy"
        );
        op.publish(Capability::Export(b"exact captured bytes".to_vec()))
            .unwrap();
        let token = op.id;
        drop(op);
        assert_eq!(
            fixture
                .registry
                .export_bytes(fixture.handle, token)
                .unwrap(),
            b"exact captured bytes"
        );
        assert_eq!(fixture.count(), 1);
    }
    #[test]
    fn closed_active_capture_cannot_publish_and_retained_native_owner_still_counts_toward_four() {
        let fixture = Fixture::new();
        let entered = Arc::new(Barrier::new(2));
        let release = Arc::new(Barrier::new(2));
        let wait_entered = entered.clone();
        let wait_release = release.clone();
        fixture.hook(Arc::new(move |phase, _| {
            if phase == "export-ready" {
                wait_entered.wait();
                wait_release.wait();
            }
        }));
        thread::scope(|threads| {
            let worker = threads.spawn(|| {
                fixture.registry.prepare_export(
                    fixture.handle,
                    br#"{"story":"retained","branch":"main","expected_revision":0}"#,
                )
            });
            entered.wait();
            assert_eq!(
                reply(
                    fixture
                        .registry
                        .prepare_import(fixture.handle, &fixture.bytes)
                )["error"],
                "Busy"
            );
            fixture.registry.close(fixture.handle);
            assert_eq!(
                reply(
                    fixture
                        .registry
                        .prepare_import(fixture.handle, &fixture.bytes)
                )["error"],
                "InvalidHandle"
            );
            let mut handles = Vec::new();
            for _ in 0..3 {
                handles.push(
                    fixture
                        .registry
                        .open(&fixture.database, &fixture.staging)
                        .unwrap(),
                );
            }
            assert_eq!(
                fixture
                    .registry
                    .open(&fixture.database, &fixture.staging)
                    .unwrap_err(),
                "WorkspaceLimit"
            );
            release.wait();
            assert_eq!(reply(worker.join().unwrap())["error"], "Cancelled");
            handles.push(
                fixture
                    .registry
                    .open(&fixture.database, &fixture.staging)
                    .unwrap(),
            );
            for handle in handles {
                fixture.registry.close(handle);
            }
        });
        assert_eq!(fixture.count(), 1);
    }
    #[test]
    fn cancellation_after_known_staging_cleanup_prevents_the_destination_transaction() {
        let fixture = Fixture::new();
        let token = fixture.prepared();
        let entered = Arc::new(Barrier::new(2));
        let release = Arc::new(Barrier::new(2));
        let wait_entered = entered.clone();
        let wait_release = release.clone();
        let staging = fixture.staging.clone();
        fixture.hook(Arc::new(move |phase, _| {
            if phase == "before-target" {
                assert_eq!(fs::read_dir(&staging).unwrap().count(), 0);
                wait_entered.wait();
                wait_release.wait();
            }
        }));
        thread::scope(|threads| {
            let worker = threads.spawn(|| fixture.registry.commit_import(fixture.handle, token));
            entered.wait();
            fixture.registry.cancel(fixture.handle);
            assert_eq!(
                reply(
                    fixture
                        .registry
                        .prepare_import(fixture.handle, &fixture.bytes)
                )["error"],
                "Busy"
            );
            release.wait();
            assert_eq!(reply(worker.join().unwrap())["error"], "Cancelled");
        });
        assert_eq!(fixture.count(), 1);
        assert_eq!(fs::read_dir(&fixture.staging).unwrap().count(), 0);
        assert_eq!(
            reply(fixture.registry.commit_import(fixture.handle, token))["error"],
            "InvalidToken"
        );
    }
    #[test]
    fn unknown_owned_stage_entry_is_retained_and_blocks_destination_import() {
        let fixture = Fixture::new();
        let token = fixture.prepared();
        fixture.hook(Arc::new(|phase, path| {
            if phase == "staged" {
                fs::write(path.join("unknown-canary"), b"OWNED TEST CANARY").unwrap();
            }
        }));
        assert_eq!(
            reply(fixture.registry.commit_import(fixture.handle, token))["error"],
            "Io"
        );
        assert_eq!(fixture.count(), 1);
        let stage = fixture
            .staging
            .join(format!("archive-{}-{token}", fixture.handle));
        assert_eq!(
            fs::read(stage.join("unknown-canary")).unwrap(),
            b"OWNED TEST CANARY"
        );
        assert!(stage.join("staged.sqlite3").is_file());
        assert_eq!(
            reply(fixture.registry.commit_import(fixture.handle, token))["error"],
            "InvalidToken"
        );
    }
    #[test]
    fn cancellation_after_store_commit_requires_library_reconciliation_and_identical_retry_conflicts(
    ) {
        let fixture = Fixture::new();
        let weak = Arc::downgrade(&fixture.registry);
        let handle = fixture.handle;
        fixture.hook(Arc::new(move |phase, _| {
            if phase == "target-imported" {
                weak.upgrade().unwrap().cancel(handle);
            }
        }));
        let token = fixture.prepared();
        assert_eq!(
            reply(fixture.registry.commit_import(fixture.handle, token))["error"],
            "Cancelled"
        );
        assert_eq!(fixture.count(), 2);
        let scope = locallore::contracts::Scope {
            story: "imported".into(),
            branch: "main".into(),
        };
        let before = Store::open(&fixture.database, None)
            .unwrap()
            .resume(&scope)
            .unwrap()
            .engine
            .canonical_bytes();
        let token = fixture.prepared();
        assert_eq!(
            reply(fixture.registry.commit_import(fixture.handle, token))["error"],
            "Conflict"
        );
        assert_eq!(
            Store::open(&fixture.database, None)
                .unwrap()
                .resume(&scope)
                .unwrap()
                .engine
                .canonical_bytes(),
            before
        );
        assert_eq!(fs::read_dir(&fixture.staging).unwrap().count(), 0);
    }
}
