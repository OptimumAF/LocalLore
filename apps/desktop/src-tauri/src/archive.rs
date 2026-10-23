//! Native-only full-private playable archive authority. No renderer paths or bytes.
use crate::{exports, lease::WindowLease};
use locallore_storage::{validate_archive, ArchivePreview, Store, ValidatedArchive};
use serde_json::{json, Value};
use std::{
    collections::BTreeMap,
    fs::{self, File, OpenOptions},
    io::{Read, Write},
    path::{Path, PathBuf},
    sync::{
        atomic::{AtomicBool, Ordering},
        Arc, Mutex,
    },
    thread::JoinHandle,
    time::{Duration, Instant},
};
type Result<T> = std::result::Result<T, String>;
pub const MAX_BYTES: usize = 32 * 1024 * 1024;
const TTL: Duration = Duration::from_secs(600);
const PRIVATE: &str = "Full private whole story: hidden facts, original accepted requests, narration, provenance and every branch. Checksums are not authenticity. Manual snapshot transfer is not synchronization. Workflow keys, noncommitted drafts/status, traces, caches and weights are excluded. Models are never loaded.";
fn error<E: std::fmt::Debug>(e: E) -> String {
    format!("{e:?}")
}
fn id() -> Result<String> {
    exports::identifier()
}
pub fn valid_id(s: &str) -> bool {
    s.len() == 36
        && s.bytes().enumerate().all(|(i, b)| {
            if [8, 13, 18, 23].contains(&i) {
                b == b'-'
            } else {
                b.is_ascii_hexdigit()
            }
        })
}
pub fn pin(path: &Path) -> Result<Vec<File>> {
    if !path.is_absolute()
        || path.components().any(|p| {
            matches!(
                p,
                std::path::Component::ParentDir | std::path::Component::CurDir
            )
        })
        || path.as_os_str().len() > 30000
    {
        return Err("UnsafeArchivePath".into());
    }
    #[cfg(windows)]
    if !matches!(path.components().next(),Some(std::path::Component::Prefix(p)) if matches!(p.kind(),std::path::Prefix::Disk(_)|std::path::Prefix::VerbatimDisk(_)))
    {
        return Err("UnsafeArchivePath".into());
    }
    let absolute = std::path::absolute(path).map_err(|_| "ArchiveIo")?;
    let mut paths: Vec<_> = absolute.ancestors().collect();
    paths.reverse();
    let mut handles = Vec::new();
    for p in paths {
        #[cfg(windows)]
        {
            use std::os::windows::fs::{MetadataExt, OpenOptionsExt};
            let f = OpenOptions::new()
                .read(true)
                .share_mode(3)
                .custom_flags(0x0220_0000)
                .open(p)
                .map_err(|_| "ArchiveIo")?;
            if f.metadata().map_err(|_| "ArchiveIo")?.file_attributes() & 0x400 != 0 {
                return Err("UnsafeArchivePath".into());
            }
            handles.push(f);
        }
        #[cfg(not(windows))]
        {
            if fs::symlink_metadata(p)
                .map_err(|_| "ArchiveIo")?
                .file_type()
                .is_symlink()
            {
                return Err("UnsafeArchivePath".into());
            }
        }
    }
    Ok(handles)
}
fn space(path: &Path, required: u64) -> Result<()> {
    #[cfg(windows)]
    {
        use std::os::windows::ffi::OsStrExt;
        use windows::{core::PCWSTR, Win32::Storage::FileSystem::GetDiskFreeSpaceExW};
        let name: Vec<u16> = path.as_os_str().encode_wide().chain(Some(0)).collect();
        let mut available = 0;
        unsafe { GetDiskFreeSpaceExW(PCWSTR(name.as_ptr()), Some(&mut available), None, None) }
            .map_err(|_| "ArchiveIo")?;
        if available < required {
            return Err("Full".into());
        }
    }
    #[cfg(not(windows))]
    {
        let _ = (path, required);
        return Err("Unsupported".into());
    }
    Ok(())
}
pub fn read_input(path: &Path) -> Result<Vec<u8>> {
    let pins = pin(path)?;
    #[cfg(windows)]
    let f = pins
        .last()
        .ok_or("UnsafeArchivePath")?
        .try_clone()
        .map_err(|_| "ArchiveIo")?;
    #[cfg(not(windows))]
    let f = File::open(path).map_err(|_| "ArchiveIo")?;
    let m = f.metadata().map_err(|_| "ArchiveIo")?;
    if !m.is_file() {
        return Err("UnsafeArchivePath".into());
    }
    if m.len() > MAX_BYTES as u64 {
        return Err("TooLarge".into());
    }
    let mut bytes = Vec::new();
    f.take(MAX_BYTES as u64 + 1)
        .read_to_end(&mut bytes)
        .map_err(|_| "ArchiveIo")?;
    if bytes.len() > MAX_BYTES {
        return Err("TooLarge".into());
    }
    Ok(bytes)
}
enum Data {
    Export(Vec<u8>),
    Import {
        bytes: Vec<u8>,
        validated: Box<ValidatedArchive>,
    },
}
struct Preview {
    epoch: u64,
    created: Instant,
    preview: ArchivePreview,
    data: Data,
}
struct Job {
    epoch: u64,
    id: u64,
    cancel: Arc<AtomicBool>,
    running: bool,
    phase: &'static str,
    error: Option<String>,
    result: Option<Value>,
}
#[derive(Default)]
struct State {
    next: u64,
    tokens: BTreeMap<String, Preview>,
    job: Option<Job>,
}
pub struct ArchiveBroker {
    state: Mutex<State>,
    worker: Mutex<Option<(u64, JoinHandle<()>)>>,
    registration: Mutex<()>,
    #[cfg(any(test, feature = "dev-harness"))]
    pub hold: AtomicBool,
    #[cfg(any(test, feature = "dev-harness"))]
    pub collision: AtomicBool,
    #[cfg(any(test, feature = "dev-harness"))]
    pub drop_import_ack: AtomicBool,
    #[cfg(test)]
    fail_spawn: AtomicBool,
    #[cfg(test)]
    before_spawn: Mutex<Option<(Arc<std::sync::Barrier>, Arc<std::sync::Barrier>)>>,
    #[cfg(test)]
    stage_attack: Mutex<Option<(PathBuf, bool)>>,
    #[cfg(test)]
    stage_journal: Mutex<Option<PathBuf>>,
}
impl Default for ArchiveBroker {
    fn default() -> Self {
        Self {
            state: Mutex::new(State::default()),
            worker: Mutex::new(None),
            registration: Mutex::new(()),
            #[cfg(any(test, feature = "dev-harness"))]
            hold: AtomicBool::new(false),
            #[cfg(any(test, feature = "dev-harness"))]
            collision: AtomicBool::new(false),
            #[cfg(any(test, feature = "dev-harness"))]
            drop_import_ack: AtomicBool::new(false),
            #[cfg(test)]
            fail_spawn: AtomicBool::new(false),
            #[cfg(test)]
            before_spawn: Mutex::new(None),
            #[cfg(test)]
            stage_attack: Mutex::new(None),
            #[cfg(test)]
            stage_journal: Mutex::new(None),
        }
    }
}
pub struct Work {
    broker: Arc<ArchiveBroker>,
    lease: Arc<WindowLease>,
    epoch: u64,
    operation: u64,
    cancel: Arc<AtomicBool>,
}
impl Work {
    pub fn cancelled(&self) -> bool {
        self.cancel.load(Ordering::SeqCst) || !self.lease.valid(self.epoch)
    }
    pub fn check(&self) -> Result<()> {
        if self.cancelled() {
            Err("Cancelled".into())
        } else {
            Ok(())
        }
    }
    pub fn phase(&self, phase: &'static str) -> Result<()> {
        self.check()?;
        self.lease.dispatch(self.epoch, || {
            let mut s = self.broker.state.lock().map_err(|_| "ArchiveInternal")?;
            let j = s
                .job
                .as_mut()
                .filter(|j| j.id == self.operation && j.epoch == self.epoch)
                .ok_or("Closed")?;
            j.phase = phase;
            Ok(())
        })
    }
    fn preview(&self, preview: ArchivePreview, data: Data) -> Result<Value> {
        self.lease.dispatch(self.epoch,||{
            self.check()?;let mut s=self.broker.state.lock().map_err(|_|"ArchiveInternal")?;
            s.tokens.retain(|_,p|p.epoch==self.epoch&&p.created.elapsed()<TTL);
            if s.tokens.len()>=2{return Err("ArchivePreviewLimit".into())}
            let token=id()?;let value=json!({"version":1,"token":token,"kind":if matches!(data,Data::Export(_)){"export"}else{"import"},"preview":preview,"warning":PRIVATE});
            s.tokens.insert(token,Preview{epoch:self.epoch,created:Instant::now(),preview,data});Ok(value)
        })
    }
    fn take(&self, token: &str) -> Result<Preview> {
        if !valid_id(token) {
            return Err("InvalidArchiveInput".into());
        }
        self.lease.dispatch(self.epoch, || {
            self.check()?;
            let mut s = self.broker.state.lock().map_err(|_| "ArchiveInternal")?;
            let p = s.tokens.get(token).ok_or("UnknownArchivePreview")?;
            if p.epoch != self.epoch || p.created.elapsed() >= TTL {
                return Err("UnknownArchivePreview".into());
            }
            s.tokens
                .remove(token)
                .ok_or_else(|| "UnknownArchivePreview".into())
        })
    }
}
impl ArchiveBroker {
    pub fn catalog(&self) -> Value {
        json!({"version":1,"format":"locallore-playable-archive","archive_version":1,"privacy":"full_private","warning":PRIVATE,"caps":{"bytes":MAX_BYTES,"tokens":2,"preview_ttl_seconds":600,"workers":1},"branch_ui":false,"corrections":false})
    }
    fn snapshot(s: &State, epoch: u64, operation: u64) -> Result<Value> {
        let j = s
            .job
            .as_ref()
            .filter(|j| j.epoch == epoch && j.id == operation)
            .ok_or("UnknownArchiveOperation")?;
        Ok(
            json!({"version":1,"operation_id":j.id,"running":j.running,"phase":j.phase,"error":j.error,"result":j.result}),
        )
    }
    pub fn status(&self, lease: &WindowLease, epoch: u64, operation: u64) -> Result<Value> {
        if operation == 0 || operation > 9_007_199_254_740_991 {
            return Err("InvalidArchiveInput".into());
        }
        lease.dispatch(epoch, || {
            Self::snapshot(
                &*self.state.lock().map_err(|_| "ArchiveInternal")?,
                epoch,
                operation,
            )
        })
    }
    pub fn cancel(&self, lease: &WindowLease, epoch: u64, operation: u64) -> Result<Value> {
        if operation == 0 || operation > 9_007_199_254_740_991 {
            return Err("InvalidArchiveInput".into());
        }
        lease.dispatch(epoch, || {
            let s = self.state.lock().map_err(|_| "ArchiveInternal")?;
            let value = Self::snapshot(&s, epoch, operation)?;
            s.job
                .as_ref()
                .ok_or("UnknownArchiveOperation")?
                .cancel
                .store(true, Ordering::SeqCst);
            Ok(value)
        })
    }
    pub fn discard(&self, lease: &WindowLease, epoch: u64, token: &str) -> Result<Value> {
        if !valid_id(token) {
            return Err("InvalidArchiveInput".into());
        }
        lease.dispatch(epoch, || {
            let mut s = self.state.lock().map_err(|_| "ArchiveInternal")?;
            if s.tokens.get(token).is_some_and(|p| p.epoch == epoch) {
                s.tokens.remove(token);
            }
            Ok(json!({"version":1,"discarded":true}))
        })
    }
    pub fn start(
        self: &Arc<Self>,
        lease: Arc<WindowLease>,
        epoch: u64,
        work: impl FnOnce(&Work) -> Result<Value> + Send + 'static,
    ) -> Result<Value> {
        loop {
            let registration = self.registration.lock().map_err(|_| "ArchiveInternal")?;
            if self
                .state
                .lock()
                .map_err(|_| "ArchiveInternal")?
                .job
                .as_ref()
                .is_some_and(|j| j.running)
            {
                return Err("ArchiveBusy".into());
            }
            let previous = self.worker.lock().map_err(|_| "ArchiveInternal")?.take();
            if let Some((_, h)) = previous {
                drop(registration);
                h.join().map_err(|_| "ArchiveInternal")?;
                continue;
            }
            let result = lease.dispatch(epoch, || {
                let (operation, cancel) = {
                    let mut s = self.state.lock().map_err(|_| "ArchiveInternal")?;
                    s.next = s
                        .next
                        .checked_add(1)
                        .filter(|id| *id <= 9_007_199_254_740_991)
                        .ok_or("ArchiveBudget")?;
                    let operation = s.next;
                    let cancel = Arc::new(AtomicBool::new(false));
                    s.job = Some(Job {
                        epoch,
                        id: operation,
                        cancel: cancel.clone(),
                        running: true,
                        phase: "starting",
                        error: None,
                        result: None,
                    });
                    (operation, cancel)
                };
                let (start, registered) = std::sync::mpsc::channel();
                #[cfg(test)]
                if let Some((entered, release)) = self.before_spawn.lock().unwrap().take() {
                    entered.wait();
                    release.wait();
                }
                let broker = self.clone();
                let copy = lease.clone();
                let task = move || {
                    if registered.recv().is_err() {
                        return;
                    }
                    let w = Work {
                        broker: broker.clone(),
                        lease: copy.clone(),
                        epoch,
                        operation,
                        cancel,
                    };
                    let answer = std::panic::catch_unwind(std::panic::AssertUnwindSafe(|| {
                        w.check()?;
                        work(&w)
                    }))
                    .unwrap_or_else(|_| Err("ArchiveInternal".into()));
                    let _ = copy.dispatch(epoch, || {
                        let mut s = broker.state.lock().map_err(|_| "ArchiveInternal")?;
                        let j = s
                            .job
                            .as_mut()
                            .filter(|j| j.id == operation && j.epoch == epoch)
                            .ok_or("Closed")?;
                        j.running = false;
                        j.phase = if answer.is_ok() { "completed" } else { "error" };
                        j.error = answer.clone().err();
                        j.result = answer.ok();
                        Ok(())
                    });
                    let mut s = broker.state.lock().unwrap_or_else(|p| p.into_inner());
                    if let Some(j) = s
                        .job
                        .as_mut()
                        .filter(|j| j.id == operation && j.epoch == epoch)
                    {
                        j.running = false;
                    }
                };
                #[cfg(test)]
                let fail = self.fail_spawn.swap(false, Ordering::SeqCst);
                #[cfg(not(test))]
                let fail = false;
                let spawned = if fail {
                    Err(std::io::Error::other("fixed spawn refusal"))
                } else {
                    std::thread::Builder::new()
                        .name("locallore-archive".into())
                        .spawn(task)
                };
                match spawned {
                    Ok(h) => {
                        *self.worker.lock().unwrap_or_else(|p| p.into_inner()) = Some((epoch, h));
                        let _ = start.send(());
                    }
                    Err(_) => {
                        if let Some(j) = self
                            .state
                            .lock()
                            .map_err(|_| "ArchiveInternal")?
                            .job
                            .as_mut()
                        {
                            j.running = false;
                            j.error = Some("ArchiveInternal".into());
                        }
                        return Err("ArchiveInternal".into());
                    }
                }
                Self::snapshot(
                    &*self.state.lock().map_err(|_| "ArchiveInternal")?,
                    epoch,
                    operation,
                )
            });
            drop(registration);
            return if lease.valid(epoch) {
                result
            } else {
                Err("Closed".into())
            };
        }
    }
    pub fn retire(&self, epoch: u64) {
        if let Ok(mut s) = self.state.try_lock() {
            s.tokens.retain(|_, p| p.epoch != epoch);
            if let Some(j) = s.job.as_ref().filter(|j| j.epoch == epoch) {
                j.cancel.store(true, Ordering::SeqCst)
            }
        }
    }
    pub fn drain(&self, epoch: u64) {
        let old = {
            let _registration = self.registration.lock().unwrap_or_else(|p| p.into_inner());
            let mut slot = self.worker.lock().unwrap_or_else(|p| p.into_inner());
            if slot.as_ref().is_some_and(|(e, _)| *e == epoch) {
                slot.take()
            } else {
                None
            }
        };
        if let Some((_, h)) = old {
            let _ = h.join();
        }
        self.state
            .lock()
            .unwrap_or_else(|p| p.into_inner())
            .tokens
            .retain(|_, p| p.epoch != epoch);
    }
}
pub fn capture(w: &Work, path: &Path, story: &str, branch: &str, expected: u64) -> Result<Value> {
    w.phase("capturing")?;
    let _pins = pin(path)?;
    let mut store = Store::open_read_only(path).map_err(error)?;
    let captured = store
        .export_archive(story, &|| w.cancelled())
        .map_err(error)?;
    if captured.preview().branch_heads.get(branch) != Some(&expected) {
        return Err("Stale".into());
    }
    w.preview(
        captured.preview().clone(),
        Data::Export(captured.bytes().to_vec()),
    )
}
pub fn preview_input(w: &Work, path: Option<PathBuf>) -> Result<Value> {
    let Some(path) = path else {
        return Ok(json!({"version":1,"status":"cancelled"}));
    };
    w.phase("validating")?;
    let bytes = read_input(&path)?;
    let validated = validate_archive(&bytes, &|| w.cancelled()).map_err(error)?;
    w.preview(
        validated.preview().clone(),
        Data::Import {
            bytes,
            validated: Box::new(validated),
        },
    )
}
fn writable_file(path: &Path) -> Result<File> {
    let mut options = OpenOptions::new();
    options.read(true).write(true).create_new(true);
    #[cfg(windows)]
    {
        use std::os::windows::fs::OpenOptionsExt;
        options
            .share_mode(3)
            .access_mode(0x80000000 | 0x40000000 | 0x00010000)
            .custom_flags(0x00200000);
    }
    options.open(path).map_err(|_| "ArchiveIo".into())
}
pub fn publish(
    w: &Work,
    token: &str,
    destination: Option<PathBuf>,
    fail_after: Option<usize>,
) -> Result<Value> {
    let p = w.take(token)?;
    let Data::Export(bytes) = p.data else {
        return Err("InvalidArchiveInput".into());
    };
    let Some(destination) = destination else {
        return Ok(json!({"version":1,"status":"cancelled"}));
    };
    w.phase("writing")?;
    let _parents = pin(&destination)?;
    space(&destination, bytes.len() as u64 + 16 * 1024 * 1024)?;
    if !fs::metadata(&destination)
        .map_err(|_| "ArchiveIo")?
        .is_dir()
    {
        return Err("UnsafeArchivePath".into());
    }
    let name = format!(
        "locallore-{}-{}.locallore-story.json",
        p.preview.story_id,
        id()?
    );
    let target = destination.join(name);
    let stage = destination.join(format!(".locallore-archive-{}.partial", id()?));
    let mut file = writable_file(&stage)?;
    let result = (|| {
        for (i, chunk) in bytes.chunks(65536).enumerate() {
            w.check()?;
            if fail_after.is_some_and(|n| i * 65536 >= n) {
                return Err("Full".into());
            }
            file.write_all(chunk).map_err(|_| "ArchiveIo")?;
        }
        file.sync_all().map_err(|_| "ArchiveIo")?;
        w.lease.dispatch(w.epoch, || {
            w.check()?;
            #[cfg(any(test, feature = "dev-harness"))]
            if w.broker.collision.swap(false, Ordering::SeqCst) {
                fs::write(&target, b"fixed existing collision file").map_err(|_| "ArchiveIo")?;
            }
            exports::atomic_finalize(&file, &stage, &target)
        })?;
        Ok(
            json!({"version":1,"status":"exported","location":target,"payload_sha256":p.preview.payload_sha256}),
        )
    })();
    drop(file);
    if result.is_err() {
        let cleanup = fs::remove_file(&stage).is_ok();
        return Ok(
            json!({"version":1,"status":"failed","error":result.err(),"cleanup_complete":cleanup}),
        );
    }
    result
}
// Only exact known stage filenames are removed, never recursive traversal.
fn clean_stage(directory: &Path) -> bool {
    let _pins = match pin(directory) {
        Ok(p) => p,
        Err(_) => return false,
    };
    let mut ok = true;
    for name in [
        "staging.sqlite",
        "staging.sqlite-wal",
        "staging.sqlite-shm",
        "staging.sqlite-journal",
    ] {
        let path = directory.join(name);
        match fs::symlink_metadata(&path) {
            Err(e) if e.kind() == std::io::ErrorKind::NotFound => {}
            Ok(m) if m.is_file() && !m.file_type().is_symlink() => {
                if fs::remove_file(&path).is_err() {
                    ok = false
                }
            }
            _ => ok = false,
        }
    }
    drop(_pins);
    if fs::remove_dir(directory).is_err() {
        ok = false
    }
    ok
}
pub fn import(w: &Work, token: &str, destination: &Path) -> Result<Value> {
    let p = w.take(token)?;
    let Data::Import { bytes, validated } = p.data else {
        return Err("InvalidArchiveInput".into());
    };
    w.phase("staging")?;
    let parent = destination.parent().ok_or("UnsafeArchivePath")?;
    let _parents = pin(parent)?;
    space(parent, 96 * 1024 * 1024)?;
    let staging_root = parent.join("archive-staging-v1");
    if !staging_root.exists() {
        fs::create_dir(&staging_root).map_err(|_| "ArchiveIo")?;
    }
    let _roots = pin(&staging_root)?;
    let directory = staging_root.join(id()?);
    fs::create_dir(&directory).map_err(|_| "ArchiveIo")?;
    let pins = pin(&directory)?;
    let staged: Result<()> = (|| {
        w.check()?;
        let stage_token = validate_archive(&bytes, &|| w.cancelled()).map_err(error)?;
        let stage_path = directory.join("staging.sqlite");
        #[cfg(all(test, windows))]
        if let Some(source) = w.broker.stage_journal.lock().unwrap().take() {
            std::os::windows::fs::symlink_file(source, directory.join("staging.sqlite-journal"))
                .map_err(|_| "ArchiveIo")?;
        }
        #[cfg(test)]
        if let Some((source, symlink)) = w.broker.stage_attack.lock().unwrap().take() {
            #[cfg(windows)]
            if symlink {
                std::os::windows::fs::symlink_file(source, &stage_path).map_err(|_| "ArchiveIo")?;
            } else {
                fs::hard_link(source, &stage_path).map_err(|_| "ArchiveIo")?;
            }
            #[cfg(not(windows))]
            {
                let _ = (source, symlink);
                return Err("Unsupported".into());
            }
        }
        // The shared owner reserves main and all exact sidecars before SQLite,
        // retaining their guards until the disposable MEMORY-journal Store closes.
        // Parent pins alone cannot protect those SQLite pathname lookups.
        let mut store = Store::create_new_pinned(&stage_path).map_err(error)?;
        let outcome = store
            .import_archive(stage_token, &|| w.cancelled())
            .map_err(error)?;
        let resumed = store
            .resume(&outcome.root)
            .map_err(|e| error(locallore_storage::ArchiveError::from(e)))?;
        if resumed.engine.revision() != p.preview.branch_heads[&p.preview.root_branch] {
            return Err("Integrity".into());
        }
        Ok(())
    })();
    drop(pins);
    let cleanup = clean_stage(&directory);
    if let Err(e) = staged {
        return Ok(
            json!({"version":1,"status":"failed","error":e,"staging_cleanup_complete":cleanup}),
        );
    }
    if !cleanup {
        return Ok(
            json!({"version":1,"status":"failed","error":"ArchiveCleanup","staging_cleanup_complete":false}),
        );
    }
    w.phase("importing")?;
    #[cfg(any(test, feature = "dev-harness"))]
    while w.broker.hold.load(Ordering::SeqCst) && !w.cancelled() {
        std::thread::sleep(Duration::from_millis(5));
    }
    w.check()?;
    let _destination = pin(destination)?;
    let mut store = Store::open_application(destination).map_err(error)?;
    let outcome = store
        .import_archive(*validated, &|| w.cancelled())
        .map_err(error)?;
    #[cfg(any(test, feature = "dev-harness"))]
    if w.broker.drop_import_ack.swap(false, Ordering::SeqCst) {
        return Err("ArchiveAcknowledgementUnavailable".into());
    }
    Ok(
        json!({"version":1,"status":"imported","root":outcome.root,"branches":outcome.branches,"committed_turns":outcome.committed_turns,"staging_cleanup_complete":true,"pending_workflow_resumed":false,"model_loaded":false}),
    )
}
#[cfg(windows)]
pub fn choose_input(owner: isize) -> Result<Option<PathBuf>> {
    use windows::{
        core::HSTRING,
        Win32::{Foundation::HWND, System::Com::*, UI::Shell::*},
    };
    unsafe {
        CoInitializeEx(None, COINIT_APARTMENTTHREADED)
            .ok()
            .map_err(|_| "PickerUnavailable")?;
        let answer = (|| {
            let dialog: IFileOpenDialog =
                CoCreateInstance(&FileOpenDialog, None, CLSCTX_INPROC_SERVER)
                    .map_err(|_| "PickerUnavailable")?;
            dialog
                .SetOptions(
                    FOS_FORCEFILESYSTEM
                        | FOS_FILEMUSTEXIST
                        | FOS_PATHMUSTEXIST
                        | FOS_NOCHANGEDIR
                        | FOS_DONTADDTORECENT,
                )
                .map_err(|_| "PickerUnavailable")?;
            dialog
                .SetTitle(&HSTRING::from(
                    "Choose a full-private LocalLore playable archive",
                ))
                .map_err(|_| "PickerUnavailable")?;
            if let Err(e) = dialog.Show(Some(HWND(owner as *mut _))) {
                return if e.code().0 as u32 == 0x800704c7 {
                    Ok(None)
                } else {
                    Err("PickerUnavailable".into())
                };
            }
            let item = dialog.GetResult().map_err(|_| "PickerUnavailable")?;
            let raw = item
                .GetDisplayName(SIGDN_FILESYSPATH)
                .map_err(|_| "PickerUnavailable")?;
            let path = raw.to_string().map_err(|_| "UnsafeArchivePath".to_owned());
            CoTaskMemFree(Some(raw.0.cast()));
            path.map(|p| Some(PathBuf::from(p)))
        })();
        CoUninitialize();
        answer
    }
}
#[cfg(not(windows))]
pub fn choose_input(_: isize) -> Result<Option<PathBuf>> {
    Err("Unsupported".into())
}

#[cfg(test)]
mod tests {
    use super::*;
    use locallore::{
        contracts::{Command, Intent, Seed},
        engine::Engine,
    };
    fn setup() -> (PathBuf, Arc<ArchiveBroker>, Arc<WindowLease>, u64) {
        let root = std::env::temp_dir().join(format!("locallore-native-archive-{}", id().unwrap()));
        fs::create_dir(&root).unwrap();
        let broker = Arc::new(ArchiveBroker::default());
        let lease = Arc::new(WindowLease::default());
        let epoch = lease.begin().unwrap();
        (root, broker, lease, epoch)
    }
    fn seed() -> Seed {
        serde_json::from_str(include_str!("../../../../fixtures/lantern_quay.json")).unwrap()
    }
    fn source(path: &Path) -> Vec<u8> {
        let mut s = Store::open(path, None).unwrap();
        let seed = seed();
        let root = seed.scope.clone();
        s.create_story("Synthetic private archive", seed).unwrap();
        let engine = s.resume(&root).unwrap().engine;
        let req = engine.request(
            "accepted-gift",
            Intent::Actions(vec![Command::Give {
                item: "potion".into(),
                to: "mira".into(),
                quantity: 1,
            }]),
        );
        let proposal = Engine::proposal(&req).unwrap();
        let preview = engine.preview(&req, &proposal).unwrap();
        s.begin_turn(&req).unwrap();
        s.commit_turn(&req, &proposal, preview.narration()).unwrap();
        s.fork_branch(
            &locallore_storage::ForkRequest {
                parent: root.clone(),
                child_branch: "archive-child".into(),
                expected_parent_revision: 1,
                at_revision: 0,
            },
            &|| false,
        )
        .unwrap();
        s.export_archive(&root.story, &|| false)
            .unwrap()
            .bytes()
            .to_vec()
    }
    fn done(b: &Arc<ArchiveBroker>, l: &Arc<WindowLease>, e: u64, op: u64) -> Value {
        for _ in 0..2000 {
            let s = b.status(l, e, op).unwrap();
            if s["running"] == false {
                return s;
            }
            std::thread::sleep(Duration::from_millis(5));
        }
        panic!("fixed archive job timeout")
    }
    fn run(
        b: &Arc<ArchiveBroker>,
        l: &Arc<WindowLease>,
        e: u64,
        f: impl FnOnce(&Work) -> Result<Value> + Send + 'static,
    ) -> Value {
        let op = b.start(l.clone(), e, f).unwrap()["operation_id"]
            .as_u64()
            .unwrap();
        done(b, l, e, op)
    }
    fn preview(b: &Arc<ArchiveBroker>, l: &Arc<WindowLease>, e: u64, file: PathBuf) -> String {
        let r = run(b, l, e, move |w| preview_input(w, Some(file)));
        assert!(r["error"].is_null(), "{r}");
        r["result"]["token"].as_str().unwrap().into()
    }
    #[test]
    fn real_staging_import_preserves_canon_and_same_identity_always_conflicts() {
        let (root, b, l, e) = setup();
        let bytes = source(&root.join("source.sqlite"));
        let input = root.join("input.json");
        fs::write(&input, &bytes).unwrap();
        let target = root.join("target.sqlite");
        Store::open_application(&target).unwrap();
        let token = preview(&b, &l, e, input.clone());
        let path = target.clone();
        let r = run(&b, &l, e, move |w| import(w, &token, &path));
        assert_eq!(r["result"]["status"], "imported");
        assert_eq!(r["result"]["branches"], 2);
        assert_eq!(r["result"]["staging_cleanup_complete"], true);
        assert_eq!(
            fs::read_dir(root.join("archive-staging-v1"))
                .unwrap()
                .count(),
            0
        );
        let mut actual = Store::open_read_only(&target).unwrap();
        let mut child = seed().scope;
        child.branch = "archive-child".into();
        assert_eq!(
            actual.resume(&child).unwrap().engine.canonical_bytes(),
            Store::open_read_only(&root.join("source.sqlite"))
                .unwrap()
                .resume(&child)
                .unwrap()
                .engine
                .canonical_bytes(),
            "whole-story import preserves independent child at its original boundary"
        );
        let snapshot = actual
            .resume(&seed().scope)
            .unwrap()
            .engine
            .canonical_bytes();
        assert_eq!(
            snapshot,
            Store::open_read_only(&root.join("source.sqlite"))
                .unwrap()
                .resume(&seed().scope)
                .unwrap()
                .engine
                .canonical_bytes()
        );
        let token = preview(&b, &l, e, input);
        let path = target.clone();
        let r = run(&b, &l, e, move |w| import(w, &token, &path));
        assert_eq!(r["error"], "Conflict");
        assert_eq!(
            snapshot,
            actual
                .resume(&seed().scope)
                .unwrap()
                .engine
                .canonical_bytes()
        );
        assert_eq!(fs::read(root.join("input.json")).unwrap(), bytes);
    }
    #[test]
    fn cancellation_after_actual_staging_never_inserts_destination_story() {
        let (root, b, l, e) = setup();
        let input = root.join("input.json");
        fs::write(&input, source(&root.join("source.sqlite"))).unwrap();
        let target = root.join("target.sqlite");
        Store::open_application(&target).unwrap();
        let token = preview(&b, &l, e, input);
        b.hold.store(true, Ordering::SeqCst);
        let path = target.clone();
        let op = b
            .start(l.clone(), e, move |w| import(w, &token, &path))
            .unwrap()["operation_id"]
            .as_u64()
            .unwrap();
        for _ in 0..2000 {
            if b.status(&l, e, op).unwrap()["phase"] == "importing" {
                break;
            }
            std::thread::sleep(Duration::from_millis(5));
        }
        b.cancel(&l, e, op).unwrap();
        assert_eq!(done(&b, &l, e, op)["error"], "Cancelled");
        assert!(Store::open_read_only(&target)
            .unwrap()
            .stories()
            .unwrap()
            .is_empty());
        assert_eq!(
            fs::read_dir(root.join("archive-staging-v1"))
                .unwrap()
                .count(),
            0
        );
    }
    #[test]
    fn exact_export_bytes_and_interrupted_write_have_no_partial_publication() {
        let (root, b, l, e) = setup();
        let source_path = root.join("source.sqlite");
        let bytes = source(&source_path);
        let output = root.join("out");
        fs::create_dir(&output).unwrap();
        let path = source_path.clone();
        let r = run(&b, &l, e, move |w| capture(w, &path, "quay", "main", 1));
        let token = r["result"]["token"].as_str().unwrap().to_owned();
        let destination = output.clone();
        let r = run(&b, &l, e, move |w| {
            publish(w, &token, Some(destination), Some(0))
        });
        assert_eq!(r["result"]["error"], "Full");
        assert_eq!(r["result"]["cleanup_complete"], true);
        assert_eq!(fs::read_dir(&output).unwrap().count(), 0);
        let path = source_path.clone();
        let r = run(&b, &l, e, move |w| capture(w, &path, "quay", "main", 1));
        let token = r["result"]["token"].as_str().unwrap().to_owned();
        let destination = output.clone();
        let r = run(&b, &l, e, move |w| {
            publish(w, &token, Some(destination), None)
        });
        assert_eq!(r["result"]["status"], "exported");
        let result: Value =
            serde_json::from_slice(&fs::read(r["result"]["location"].as_str().unwrap()).unwrap())
                .unwrap();
        let original: Value = serde_json::from_slice(&bytes).unwrap();
        assert_eq!(result, original);
        let path = source_path;
        assert_eq!(
            run(&b, &l, e, move |w| capture(w, &path, "quay", "main", 0))["error"],
            "Stale"
        );
    }
    #[test]
    fn input_bounds_malformed_identifiers_and_preview_cap_are_explicit() {
        let (root, b, l, e) = setup();
        let input = root.join("input.json");
        let bytes = source(&root.join("source.sqlite"));
        fs::write(&input, &bytes).unwrap();
        assert_eq!(read_input(&root).unwrap_err(), "UnsafeArchivePath");
        let huge = root.join("huge.json");
        File::create(&huge)
            .unwrap()
            .set_len(MAX_BYTES as u64 + 1)
            .unwrap();
        assert_eq!(read_input(&huge).unwrap_err(), "TooLarge");
        assert_eq!(b.discard(&l, e, "bad").unwrap_err(), "InvalidArchiveInput");
        assert_eq!(b.cancel(&l, e, 0).unwrap_err(), "InvalidArchiveInput");
        preview(&b, &l, e, input.clone());
        preview(&b, &l, e, input.clone());
        let r = run(&b, &l, e, move |w| preview_input(w, Some(input)));
        assert_eq!(r["error"], "ArchivePreviewLimit");
    }
    #[test]
    fn retired_worker_and_spawn_failure_never_wedge_or_publish() {
        let (_root, b, l, e) = setup();
        b.fail_spawn.store(true, Ordering::SeqCst);
        assert_eq!(
            b.start(l.clone(), e, |_| Ok(
                json!({"version":1,"status":"cancelled"})
            ))
            .unwrap_err(),
            "ArchiveInternal"
        );
        let r = run(&b, &l, e, |_| panic!("fixed synthetic archive panic"));
        assert_eq!(r["error"], "ArchiveInternal");
        let entered = Arc::new(std::sync::Barrier::new(2));
        let release = Arc::new(std::sync::Barrier::new(2));
        let a = entered.clone();
        let z = release.clone();
        let op = b
            .start(l.clone(), e, move |_| {
                a.wait();
                z.wait();
                Ok(json!({"version":1,"status":"imported"}))
            })
            .unwrap()["operation_id"]
            .as_u64()
            .unwrap();
        entered.wait();
        let closed = l.invalidate("main-1").unwrap();
        b.retire(e);
        release.wait();
        b.drain(e);
        l.finish_close(closed, || {});
        assert_eq!(b.status(&l, e, op).unwrap_err(), "Closed");
        let fresh = l.begin().unwrap();
        assert_eq!(
            run(&b, &l, fresh, |_| Ok(
                json!({"version":1,"status":"cancelled"})
            ))["result"]["status"],
            "cancelled"
        );
    }
    #[test]
    fn destruction_between_admission_and_registration_waits_and_prevents_work() {
        let (_root, b, l, e) = setup();
        let entered = Arc::new(std::sync::Barrier::new(2));
        let release = Arc::new(std::sync::Barrier::new(2));
        *b.before_spawn.lock().unwrap() = Some((entered.clone(), release.clone()));
        let wrote = Arc::new(AtomicBool::new(false));
        let marker = wrote.clone();
        let manager = b.clone();
        let lease = l.clone();
        let start = std::thread::spawn(move || {
            manager.start(lease, e, move |_| {
                marker.store(true, Ordering::SeqCst);
                Ok(json!({"version":1,"status":"cancelled"}))
            })
        });
        entered.wait();
        let closed = l.invalidate("main-1").unwrap();
        b.retire(e);
        let drained = Arc::new(AtomicBool::new(false));
        let done = drained.clone();
        let manager = b.clone();
        let drain = std::thread::spawn(move || {
            manager.drain(e);
            done.store(true, Ordering::SeqCst);
        });
        assert!(!drained.load(Ordering::SeqCst));
        release.wait();
        assert_eq!(start.join().unwrap().unwrap_err(), "Closed");
        drain.join().unwrap();
        assert!(!wrote.load(Ordering::SeqCst));
        l.finish_close(closed, || {});
    }
    #[test]
    fn collision_preserves_existing_file_and_exact_staging_cleanup() {
        let (root, b, l, e) = setup();
        let input = root.join("source.sqlite");
        source(&input);
        let r = run(&b, &l, e, move |w| capture(w, &input, "quay", "main", 1));
        let token = r["result"]["token"].as_str().unwrap().to_owned();
        let output = root.join("exports");
        fs::create_dir(&output).unwrap();
        b.collision.store(true, Ordering::SeqCst);
        let folder = output.clone();
        let r = run(&b, &l, e, move |w| publish(w, &token, Some(folder), None));
        assert_eq!(r["result"]["error"], "ExportExists");
        assert_eq!(r["result"]["cleanup_complete"], true);
        let files = fs::read_dir(&output)
            .unwrap()
            .map(|e| e.unwrap().path())
            .collect::<Vec<_>>();
        assert_eq!(files.len(), 1);
        assert_eq!(
            fs::read(&files[0]).unwrap(),
            b"fixed existing collision file"
        );
    }
    #[test]
    fn successful_import_with_lost_ack_is_visible_and_never_idempotent_success() {
        let (root, b, l, e) = setup();
        let input = root.join("input.json");
        fs::write(&input, source(&root.join("source.sqlite"))).unwrap();
        let target = root.join("target.sqlite");
        Store::open_application(&target).unwrap();
        let token = preview(&b, &l, e, input.clone());
        b.drop_import_ack.store(true, Ordering::SeqCst);
        let path = target.clone();
        assert_eq!(
            run(&b, &l, e, move |w| import(w, &token, &path))["error"],
            "ArchiveAcknowledgementUnavailable"
        );
        assert_eq!(
            Store::open_read_only(&target)
                .unwrap()
                .stories()
                .unwrap()
                .len(),
            1
        );
        let token = preview(&b, &l, e, input);
        assert_eq!(
            run(&b, &l, e, move |w| import(w, &token, &target))["error"],
            "Conflict"
        );
    }
    #[test]
    fn pinned_ancestor_cannot_move_and_junction_parent_never_reaches_input() {
        let (root, _b, _l, _e) = setup();
        let actual = root.join("real");
        fs::create_dir(&actual).unwrap();
        fs::write(actual.join("input.json"), b"{}").unwrap();
        let pins = pin(&actual).unwrap();
        assert!(fs::rename(&actual, root.join("moved")).is_err());
        drop(pins);
        #[cfg(windows)]
        {
            use std::os::windows::process::CommandExt;
            let junction = root.join("junction");
            let result = std::process::Command::new("cmd")
                .args(["/c", "mklink", "/J"])
                .arg(&junction)
                .arg(&actual)
                .creation_flags(0x08000000)
                .output()
                .unwrap();
            assert!(result.status.success());
            assert_eq!(
                read_input(&junction.join("input.json")).unwrap_err(),
                "UnsafeArchivePath"
            );
            assert_eq!(fs::read(actual.join("input.json")).unwrap(), b"{}");
            fs::remove_dir(&junction).unwrap();
            let leaf = root.join("input-link.json");
            std::os::windows::fs::symlink_file(actual.join("input.json"), &leaf).unwrap();
            assert_eq!(read_input(&leaf).unwrap_err(), "UnsafeArchivePath");
            fs::remove_file(leaf).unwrap();
        }
    }
    fn stage_leaf_attack(symlink: bool) {
        let (root, b, l, e) = setup();
        let input = root.join("archive.json");
        fs::write(&input, source(&root.join("source.sqlite"))).unwrap();
        let outside = root.join("unrelated-valid.sqlite");
        let mut s = Store::open(&outside, None).unwrap();
        let mut kept = seed();
        kept.scope.story = "kept-unrelated-story".into();
        let scope = kept.scope.clone();
        s.create_story("Unrelated private fixture", kept).unwrap();
        let canonical = s.resume(&scope).unwrap().engine.canonical_bytes();
        drop(s);
        let original = fs::read(&outside).unwrap();
        let target = root.join("destination.sqlite");
        Store::open_application(&target).unwrap();
        let token = preview(&b, &l, e, input);
        *b.stage_attack.lock().unwrap() = Some((outside.clone(), symlink));
        let path = target.clone();
        let r = run(&b, &l, e, move |w| import(w, &token, &path));
        assert_eq!(r["result"]["status"], "failed");
        assert_eq!(r["result"]["error"], "Io");
        assert_eq!(
            fs::read(&outside).unwrap(),
            original,
            "refuse before SQLite can open another valid Store"
        );
        let mut reader = Store::open_read_only(&outside).unwrap();
        assert_eq!(reader.stories().unwrap().len(), 1);
        assert_eq!(
            reader.resume(&scope).unwrap().engine.canonical_bytes(),
            canonical
        );
        assert!(Store::open_read_only(&target)
            .unwrap()
            .stories()
            .unwrap()
            .is_empty());
        assert_eq!(
            r["result"]["staging_cleanup_complete"], !symlink,
            "untrusted reparse leaf is retained with explicit cleanup failure"
        );
    }
    #[test]
    fn planted_existing_hardlink_cannot_adopt_another_valid_store() {
        stage_leaf_attack(false)
    }
    #[cfg(windows)]
    #[test]
    fn planted_leaf_reparse_cannot_import_into_another_valid_store() {
        stage_leaf_attack(true)
    }
    #[test]
    fn immutable_unicode_preview_survives_file_edits_and_tokens_cannot_change_mode() {
        let (root, b, l, e) = setup();
        let input = root.join("Private archive 試験 é.json");
        fs::write(&input, source(&root.join("source.sqlite"))).unwrap();
        let target = root.join("target.sqlite");
        Store::open_application(&target).unwrap();
        let token = preview(&b, &l, e, input.clone());
        fs::write(&input, b"later untrusted edit").unwrap();
        let path = target.clone();
        assert_eq!(
            run(&b, &l, e, move |w| import(w, &token, &path))["result"]["status"],
            "imported"
        );
        assert_eq!(
            Store::open_read_only(&target)
                .unwrap()
                .resume(&seed().scope)
                .unwrap()
                .engine
                .revision(),
            1
        );
        fs::write(&input, source(&root.join("second-source.sqlite"))).unwrap();
        let token = preview(&b, &l, e, input);
        let folder = root.join("out");
        fs::create_dir(&folder).unwrap();
        let destination = folder.clone();
        assert_eq!(
            run(&b, &l, e, move |w| publish(
                w,
                &token,
                Some(destination),
                None
            ))["error"],
            "InvalidArchiveInput"
        );
        assert_eq!(fs::read_dir(folder).unwrap().count(), 0);
    }
    #[test]
    fn expired_or_foreign_window_preview_cannot_start_staging() {
        let (root, b, l, e) = setup();
        let input = root.join("input.json");
        fs::write(&input, source(&root.join("source.sqlite"))).unwrap();
        let target = root.join("target.sqlite");
        Store::open_application(&target).unwrap();
        let token = preview(&b, &l, e, input.clone());
        b.state
            .lock()
            .unwrap()
            .tokens
            .get_mut(&token)
            .unwrap()
            .created = Instant::now() - TTL - Duration::from_secs(1);
        let path = target.clone();
        assert_eq!(
            run(&b, &l, e, move |w| import(w, &token, &path))["error"],
            "UnknownArchivePreview"
        );
        assert!(!root.join("archive-staging-v1").exists());
        let token = preview(&b, &l, e, input);
        let closed = l.invalidate("main-1").unwrap();
        b.retire(e);
        b.drain(e);
        l.finish_close(closed, || {});
        let fresh = l.begin().unwrap();
        assert_eq!(
            run(&b, &l, fresh, move |w| import(w, &token, &target))["error"],
            "UnknownArchivePreview"
        );
    }
    #[cfg(windows)]
    #[test]
    fn planted_journal_reparse_cannot_write_another_valid_store() {
        let (root, b, l, e) = setup();
        let input = root.join("archive.json");
        fs::write(&input, source(&root.join("source.sqlite"))).unwrap();
        let outside = root.join("unrelated-journal-target.sqlite");
        let mut s = Store::open(&outside, None).unwrap();
        let mut kept = seed();
        kept.scope.story = "kept-journal-target".into();
        s.create_story("Unrelated fixture", kept).unwrap();
        drop(s);
        let original = fs::read(&outside).unwrap();
        let target = root.join("target.sqlite");
        Store::open_application(&target).unwrap();
        let token = preview(&b, &l, e, input);
        *b.stage_journal.lock().unwrap() = Some(outside.clone());
        let r = run(&b, &l, e, move |w| import(w, &token, &target));
        let before = locallore::inspection::sha256(&original);
        let after = locallore::inspection::sha256(&fs::read(&outside).unwrap());
        let evidence = root.join("journal-attack-evidence.json");
        fs::write(&evidence,serde_json::to_vec_pretty(&json!({"synthetic":true,"attack":"preplanted-staging.sqlite-journal-symlink-to-another-valid-Store","before_sha256":before,"after_sha256":after,"outside_unchanged":before==after,"native_job":r})).unwrap()).unwrap();
        assert_eq!(
            before,
            after,
            "SQLite journal must never follow a planted link; local synthetic evidence {}",
            evidence.display()
        );
    }
}
