//! Native-only immutable inspection broker. Renderer IPC accepts no path.
use locallore::inspection::InspectionBundle;
use serde_json::{json, Value};
use std::{
    collections::BTreeMap,
    fs::{self, File, OpenOptions},
    io::{Read, Write},
    path::{Component, Path, PathBuf},
    sync::{
        atomic::{AtomicBool, Ordering},
        Arc, Mutex,
    },
    time::{Duration, Instant},
};

const MAX_BYTES: usize = 66 * 1024 * 1024;
const MAX_DATABASE: usize = 64 * 1024 * 1024;
const MAX_PREVIEWS: usize = 2;
const TTL: Duration = Duration::from_secs(300);
const TEXT_LIMIT: usize = 64 * 1024;
const NAMES: &[&str] = &[
    "diagnostics.json",
    "events.jsonl",
    "transcript.jsonl",
    "state.json",
    "characters.json",
    "relationships.json",
    "knowledge.json",
    "threads.json",
];
enum NativeSnapshot {
    PrivateTrace {
        manifest: Value,
        files: BTreeMap<String, Vec<u8>>,
    },
    Inspection(InspectionBundle),
    Loaded {
        bundle: InspectionBundle,
        manifest_bytes: Vec<u8>,
    },
    Database {
        manifest: Value,
        files: BTreeMap<String, Vec<u8>>,
    },
}
impl NativeSnapshot {
    fn manifest(&self) -> &Value {
        match self {
            Self::Inspection(b) | Self::Loaded { bundle: b, .. } => &b.manifest,
            Self::Database { manifest, .. } | Self::PrivateTrace { manifest, .. } => manifest,
        }
    }
    fn contents(&self) -> &BTreeMap<String, Vec<u8>> {
        match self {
            Self::Inspection(b) | Self::Loaded { bundle: b, .. } => &b.files,
            Self::Database { files, .. } | Self::PrivateTrace { files, .. } => files,
        }
    }
    fn validate(&self) -> Result<(), String> {
        match self {
            Self::PrivateTrace { manifest, files } => {
                let bytes = files.get("capture.json").ok_or("InvalidExport")?;
                if files.len() != 1
                    || bytes.len() > 524288
                    || manifest["format"] != "locallore-private-trace"
                    || manifest["version"] != 1
                    || manifest["mode"] != "private_trace"
                    || manifest["privacy"] != "private_generation_capture"
                    || manifest["files"][0]["path"] != "capture.json"
                    || manifest["files"][0]["bytes"] != bytes.len()
                    || manifest["files"][0]["sha256"] != locallore::inspection::sha256(bytes)
                {
                    return Err("Integrity".into());
                }
                Ok(())
            }
            Self::Inspection(b) => b.validate(),
            Self::Loaded {
                bundle,
                manifest_bytes,
            } => {
                bundle.validate()?;
                let parsed: Value =
                    serde_json::from_slice(manifest_bytes).map_err(|_| "InvalidExport")?;
                if parsed != bundle.manifest {
                    return Err("ChangedExport".into());
                }
                Ok(())
            }
            Self::Database { manifest, files } => {
                let bytes = files
                    .get("stories-snapshot.sqlite")
                    .filter(|b| b.len() <= MAX_DATABASE)
                    .ok_or("TooLarge")?;
                if files.len() != 1
                    || !bytes.starts_with(b"SQLite format 3\0")
                    || manifest["format"] != "locallore-database-inspection"
                    || manifest["mode"] != "database"
                    || manifest["privacy"] != "private_all_stories_and_drafts"
                    || manifest["portable_playable"] != false
                    || manifest["files"][0]["bytes"] != bytes.len()
                    || manifest["files"][0]["sha256"] != locallore::inspection::sha256(bytes)
                {
                    return Err("Integrity".into());
                }
                Ok(())
            }
        }
    }
}
type StageProbe = Box<dyn FnOnce(&Path)>;
pub struct Preview {
    bundle: NativeSnapshot,
    epoch: u64,
    created: Instant,
    cancelled: AtomicBool,
    saving: AtomicBool,
    saved: Mutex<Option<PathBuf>>,
}
#[derive(Default)]
pub struct ExportBroker(Mutex<BTreeMap<String, Arc<Preview>>>);

fn files(bundle: &NativeSnapshot) -> Result<BTreeMap<String, Vec<u8>>, String> {
    bundle.validate()?;
    let mut output = bundle.contents().clone();
    if output.is_empty()
        || output.len() > NAMES.len()
        || output.keys().any(|n| {
            !NAMES.contains(&n.as_str())
                && n != "stories-snapshot.sqlite"
                && !(matches!(bundle, NativeSnapshot::PrivateTrace { .. }) && n == "capture.json")
        })
    {
        return Err("InvalidExport".into());
    }
    let manifest = match bundle {
        NativeSnapshot::Loaded { manifest_bytes, .. } => manifest_bytes.clone(),
        _ => serde_json::to_vec_pretty(bundle.manifest()).map_err(|_| "InvalidExport")?,
    };
    if manifest.len() > 262_144 {
        return Err("TooLarge".into());
    }
    output.insert("manifest.json".into(), manifest);
    let total = output
        .values()
        .try_fold(0usize, |n, b| n.checked_add(b.len()))
        .ok_or("TooLarge")?;
    if total > MAX_BYTES {
        return Err("TooLarge".into());
    }
    Ok(output)
}
impl ExportBroker {
    pub fn insert_capture(
        &self,
        epoch: u64,
        capture: Value,
        current: impl FnOnce() -> bool,
    ) -> Result<Value, String> {
        let bytes = serde_json::to_vec_pretty(&capture).map_err(|_| "InvalidExport")?;
        let text = std::str::from_utf8(&bytes)
            .map_err(|_| "InvalidExport")?
            .to_owned();
        let manifest = json!({"format":"locallore-private-trace","version":1,"mode":"private_trace", "scope":capture["scope"],"revision":capture["head"],"base_revision":capture["base_revision"],"privacy":"private_generation_capture","exact_reconstruction":false,"portable_playable":false,"files":[{"path":"capture.json","bytes":bytes.len(),"sha256":locallore::inspection::sha256(&bytes)}]});
        let mut preview = self.insert_snapshot(
            epoch,
            NativeSnapshot::PrivateTrace {
                manifest,
                files: BTreeMap::from([("capture.json".into(), bytes)]),
            },
            current,
        )?;
        preview["text"] = json!(text);
        Ok(preview)
    }
    #[cfg(feature = "dev-harness")]
    pub fn last_saved(&self, epoch: u64) -> Option<PathBuf> {
        let records = self.0.lock().ok()?;
        records
            .values()
            .filter(|p| p.epoch == epoch)
            .filter_map(|p| {
                p.saved
                    .try_lock()
                    .ok()
                    .and_then(|s| s.clone())
                    .map(|path| (p.created, path))
            })
            .max_by_key(|(created, _)| *created)
            .map(|(_, path)| path)
    }
    pub fn insert(
        &self,
        epoch: u64,
        bundle: InspectionBundle,
        current: impl FnOnce() -> bool,
    ) -> Result<Value, String> {
        self.insert_snapshot(epoch, NativeSnapshot::Inspection(bundle), current)
    }
    pub fn insert_database(
        &self,
        epoch: u64,
        bytes: Vec<u8>,
        stories: Value,
        scope: Value,
        current: impl FnOnce() -> bool,
    ) -> Result<Value, String> {
        let revision = stories
            .as_array()
            .and_then(|rows| rows.iter().find(|row| row["scope"] == scope))
            .and_then(|row| row["revision"].as_u64())
            .ok_or("Scope")?;
        let timestamp = std::time::SystemTime::now()
            .duration_since(std::time::UNIX_EPOCH)
            .map_err(|_| "Clock")?
            .as_millis() as u64;
        let manifest = json!({"format":"locallore-database-inspection","version":1,"mode":"database","privacy":"private_all_stories_and_drafts","portable_playable":false,"schema_version":locallore_workspace::DATABASE_SCHEMA_VERSION,"app_version":env!("CARGO_PKG_VERSION"),"created_at_unix_ms":timestamp,"scope":scope,"revision":revision,"stories":stories,"contents":"All stories, drafts, receipts, derived cache and canonical state. Private copy for explicit read-only SQLite inspection.","files":[{"path":"stories-snapshot.sqlite","bytes":bytes.len(),"sha256":locallore::inspection::sha256(&bytes),"media_type":"application/vnd.sqlite3"}]});
        self.insert_snapshot(
            epoch,
            NativeSnapshot::Database {
                manifest,
                files: BTreeMap::from([("stories-snapshot.sqlite".into(), bytes)]),
            },
            current,
        )
    }
    fn insert_snapshot(
        &self,
        epoch: u64,
        bundle: NativeSnapshot,
        current: impl FnOnce() -> bool,
    ) -> Result<Value, String> {
        let output = files(&bundle)?;
        let token = identifier()?;
        let mut records = self.0.lock().map_err(|_| "Closed")?;
        if !current() {
            return Err("Closed".into());
        }
        records.retain(|_, p| {
            let keep = p.created.elapsed() <= TTL && !p.cancelled.load(Ordering::SeqCst);
            if !keep {
                p.cancelled.store(true, Ordering::SeqCst);
            }
            keep || (matches!(&p.bundle, NativeSnapshot::PrivateTrace { .. })
                && Arc::strong_count(p) > 1)
        });
        if records.len() >= MAX_PREVIEWS {
            let completed = records
                .iter()
                .filter(|(_, p)| {
                    p.saved.try_lock().is_ok_and(|s| s.is_some())
                        && (!matches!(&p.bundle, NativeSnapshot::PrivateTrace { .. })
                            || Arc::strong_count(p) == 1)
                })
                .min_by_key(|(_, p)| p.created)
                .map(|(token, _)| token.clone());
            if let Some(token) = completed {
                records.remove(&token);
            }
        }
        if records.len() >= MAX_PREVIEWS {
            return Err("PreviewLimit".into());
        }
        if matches!(bundle, NativeSnapshot::PrivateTrace { .. }) {
            let retained = records.values().try_fold(0usize, |total, p| {
                if !matches!(p.bundle, NativeSnapshot::PrivateTrace { .. }) {
                    return Err("InvalidExport".to_owned());
                }
                let size = files(&p.bundle)?.values().map(Vec::len).sum::<usize>();
                total.checked_add(size).ok_or_else(|| "TooLarge".to_owned())
            })?;
            if retained.saturating_add(output.values().map(Vec::len).sum::<usize>()) > 1048576 {
                return Err("TooLarge".into());
            }
        }
        let result = json!({"token":token,"manifest":bundle.manifest(),"expires_seconds":TTL.as_secs(),"files":output.iter().map(|(path,b)|json!({"path":path,"bytes":b.len()})).collect::<Vec<_>>()});
        records.insert(
            token,
            Arc::new(Preview {
                bundle,
                epoch,
                created: Instant::now(),
                cancelled: AtomicBool::new(false),
                saving: AtomicBool::new(false),
                saved: Mutex::new(None),
            }),
        );
        Ok(result)
    }
    pub fn get(&self, epoch: u64, token: &str) -> Result<Arc<Preview>, String> {
        if token.len() > 64 {
            return Err("InvalidInput".into());
        }
        let records = self.0.lock().map_err(|_| "Closed")?;
        let record = records.get(token).ok_or("UnknownExport")?;
        if record.epoch != epoch {
            return Err("Closed".into());
        }
        if record.created.elapsed() > TTL || record.cancelled.load(Ordering::SeqCst) {
            return Err("ExpiredExport".into());
        }
        Ok(record.clone())
    }
    pub fn cancel(&self, epoch: u64, token: &str) -> Result<Value, String> {
        let record = self.get(epoch, token)?;
        let saved = record.saved.lock().map_err(|_| "Closed")?;
        if saved.is_some() {
            return Ok(json!({"status":"saved"}));
        }
        record.cancelled.store(true, Ordering::SeqCst);
        Ok(json!({"status":"cancelled"}))
    }
    pub fn invalidate(&self, epoch: u64) {
        if let Ok(mut records) = self.0.lock() {
            records.retain(|_, p| {
                if p.epoch == epoch {
                    p.cancelled.store(true, Ordering::SeqCst);
                    matches!(&p.bundle, NativeSnapshot::PrivateTrace { .. })
                        && Arc::strong_count(p) > 1
                } else {
                    true
                }
            });
        }
    }
    pub fn insert_saved(
        &self,
        epoch: u64,
        bundle: InspectionBundle,
        manifest_bytes: Vec<u8>,
        path: PathBuf,
        current: impl FnOnce() -> bool,
    ) -> Result<Value, String> {
        let mut result = self.insert_snapshot(
            epoch,
            NativeSnapshot::Loaded {
                bundle,
                manifest_bytes,
            },
            current,
        )?;
        let record = self.get(epoch, result["token"].as_str().ok_or("Integrity")?)?;
        *record.saved.lock().map_err(|_| "Closed")? = Some(path.clone());
        result["location"] = json!(path.to_str().ok_or("InvalidInput")?);
        Ok(result)
    }
}
impl Preview {
    pub fn open_current(
        &self,
        name: &str,
        lease: &super::lease::WindowLease,
        epoch: u64,
    ) -> Result<Value, String> {
        if !lease.valid(epoch) {
            return Err("Closed".into());
        }
        let value = self.open(name)?;
        if !lease.valid(epoch) {
            return Err("Closed".into());
        }
        Ok(value)
    }
    fn check(&self) -> Result<(), String> {
        if self.cancelled.load(Ordering::SeqCst) || self.created.elapsed() > TTL {
            Err("Cancelled".into())
        } else {
            Ok(())
        }
    }
    pub fn save(
        &self,
        parent: &Path,
        finalize: impl FnOnce(&File, &Path, &Path) -> Result<(), String>,
    ) -> Result<Value, String> {
        self.save_impl(parent, finalize, None, None)
    }
    #[cfg(any(test, feature = "dev-harness"))]
    pub fn save_injected(
        &self,
        parent: &Path,
        finalize: impl FnOnce(&File, &Path, &Path) -> Result<(), String>,
        fail_after: usize,
    ) -> Result<Value, String> {
        self.save_impl(parent, finalize, Some(fail_after), None)
    }
    fn save_impl(
        &self,
        parent: &Path,
        finalize: impl FnOnce(&File, &Path, &Path) -> Result<(), String>,
        fail_after: Option<usize>,
        stage_probe: Option<StageProbe>,
    ) -> Result<Value, String> {
        if self
            .saving
            .compare_exchange(false, true, Ordering::SeqCst, Ordering::SeqCst)
            .is_err()
        {
            return Err("Busy".into());
        }
        let result = (|| {
            self.check()?;
            if self.saved.lock().map_err(|_| "Closed")?.is_some() {
                return Err("AlreadySaved".into());
            }
            let _pins = pin_directory(parent)?;
            let suffix = identifier()?;
            let mode = self.bundle.manifest()["mode"]
                .as_str()
                .ok_or("InvalidExport")?;
            if !["diagnostics", "player", "full", "database", "private_trace"].contains(&mode) {
                return Err("InvalidExport".into());
            }
            let revision = self.bundle.manifest()["revision"]
                .as_u64()
                .ok_or("InvalidExport")?;
            let target = parent.join(format!("LocalLore-{mode}-r{revision}-{suffix}"));
            let staging = parent.join(format!(".locallore-staging-{suffix}"));
            fs::create_dir(&staging).map_err(io_category)?;
            let mut stage_handle = Some(pin_stage(&staging)?);
            if let Some(probe) = stage_probe {
                probe(&staging);
            }
            let output = files(&self.bundle)?;
            let mut created = Vec::new();
            let written = (|| {
                for (index, (name, bytes)) in output.iter().enumerate() {
                    self.check()?;
                    if fail_after == Some(index) {
                        return Err("Full".into());
                    }
                    let mut file = OpenOptions::new()
                        .write(true)
                        .create_new(true)
                        .open(staging.join(name))
                        .map_err(io_category)?;
                    created.push(name.clone());
                    file.write_all(bytes).map_err(io_category)?;
                    file.sync_all().map_err(io_category)?;
                }
                // Cancellation and final publication serialize; a late cancel reports saved.
                let mut saved = self.saved.lock().map_err(|_| "Closed")?;
                self.check()?;
                finalize(stage_handle.as_ref().unwrap(), &staging, &target)?;
                drop(stage_handle.take());
                *saved = Some(target.clone());
                Ok(
                    json!({"status":"saved","location":target.to_str().ok_or("InvalidInput")?,"revision":revision,"mode":mode}),
                )
            })();
            if written.is_err() {
                for name in &created {
                    let _ = fs::remove_file(staging.join(name));
                }
                drop(stage_handle.take());
                let _ = fs::remove_dir(&staging);
            }
            written
        })();
        self.saving.store(false, Ordering::SeqCst);
        result
    }
    pub fn open(&self, name: &str) -> Result<Value, String> {
        self.check()?;
        let output = files(&self.bundle)?;
        let expected = output.get(name).ok_or("InvalidInput")?;
        let saved = self
            .saved
            .lock()
            .map_err(|_| "Closed")?
            .clone()
            .ok_or("NotSaved")?;
        let _pins = pin_directory(&saved)?;
        for (path, bytes) in &output {
            let actual = read_bounded(&saved.join(path), bytes.len())?;
            if actual != *bytes {
                return Err("ChangedExport".into());
            }
        }
        let length = expected.len().min(TEXT_LIMIT);
        let text = if name == "stories-snapshot.sqlite" {
            "Binary SQLite inspection copy. Open this copy with your own read-only SQLite tool; this app never opens or edits the live database externally.".into()
        } else {
            String::from_utf8_lossy(&expected[..length]).into_owned()
        };
        Ok(
            json!({"path":name,"text":text,"truncated":length<expected.len(),"bytes":expected.len(),"read_only":true,"manifest":self.bundle.manifest()}),
        )
    }
}

pub fn atomic_finalize(handle: &File, _staging: &Path, target: &Path) -> Result<(), String> {
    // Rename the pinned directory itself. No FILE_SHARE_DELETE gap or path re-resolution.
    #[cfg(windows)]
    {
        use std::{
            mem::{offset_of, size_of},
            os::{windows::ffi::OsStrExt, windows::io::AsRawHandle},
        };
        use windows::Win32::{
            Foundation::HANDLE,
            Storage::FileSystem::{
                FileRenameInfo, SetFileInformationByHandle, FILE_RENAME_INFO, FILE_RENAME_INFO_0,
            },
        };
        // Callers retain pinned destination ancestors through publication.
        // Canonicalizing that existing parent supplies Windows' extended path
        // form for the absent target; the actual rename still uses the held
        // staging handle and refuses replacement.
        let target = target
            .parent()
            .ok_or("Io")?
            .canonicalize()
            .map_err(|_| "Io")?
            .join(target.file_name().ok_or("Io")?);
        let name = target
            .as_os_str()
            .encode_wide()
            .chain(Some(0))
            .collect::<Vec<_>>();
        if name.len() > 32768 {
            return Err("TooLarge".into());
        }
        let size = offset_of!(FILE_RENAME_INFO, FileName) + name.len() * 2;
        let mut storage = vec![0u64; size.div_ceil(size_of::<u64>())];
        let info = storage.as_mut_ptr().cast::<FILE_RENAME_INFO>();
        unsafe {
            (*info).Anonymous = FILE_RENAME_INFO_0 {
                ReplaceIfExists: false,
            };
            (*info).RootDirectory = HANDLE::default();
            (*info).FileNameLength = ((name.len() - 1) * 2) as u32;
            std::ptr::copy_nonoverlapping(
                name.as_ptr(),
                storage
                    .as_mut_ptr()
                    .cast::<u8>()
                    .add(offset_of!(FILE_RENAME_INFO, FileName))
                    .cast::<u16>(),
                name.len(),
            );
            SetFileInformationByHandle(
                HANDLE(handle.as_raw_handle()),
                FileRenameInfo,
                info.cast(),
                size as u32,
            )
        }
        .map_err(|_error| {
            if target.exists() {
                "ExportExists".into()
            } else {
                "Io".into()
            }
        })
    }
    #[cfg(not(windows))]
    {
        let _ = (handle, _staging, target);
        Err("Unsupported".into())
    }
}
fn pin_stage(path: &Path) -> Result<File, String> {
    let mut options = OpenOptions::new();
    options.read(true);
    #[cfg(windows)]
    {
        use std::os::windows::fs::OpenOptionsExt;
        options
            .custom_flags(0x02000000 | 0x00200000)
            .access_mode(0x80000000 | 0x00010000)
            .share_mode(1 | 2);
    }
    let file = options.open(path).map_err(io_category)?;
    let metadata = file.metadata().map_err(io_category)?;
    if !metadata.is_dir() || reparse(&metadata) {
        return Err("UnsafeDestination".into());
    }
    Ok(file)
}
#[cfg(test)]
fn load_directory(path: &Path) -> Result<InspectionBundle, String> {
    load_exact_directory(path).map(|(bundle, _)| bundle)
}
pub fn load_exact_directory(path: &Path) -> Result<(InspectionBundle, Vec<u8>), String> {
    let _pins = pin_directory(path)?;
    let manifest_path = path.join("manifest.json");
    let meta = fs::symlink_metadata(&manifest_path).map_err(|_| "Io")?;
    if meta.len() > 262_144 {
        return Err("TooLarge".into());
    }
    let manifest_bytes = read_bounded(&manifest_path, meta.len() as usize)?;
    let manifest: Value = serde_json::from_slice(&manifest_bytes).map_err(|_| "InvalidExport")?;
    let inventory = manifest["files"]
        .as_array()
        .filter(|a| a.len() <= 8)
        .ok_or("InvalidExport")?;
    let mut output = BTreeMap::new();
    let mut total = meta.len() as usize;
    for row in inventory {
        let name = row["path"]
            .as_str()
            .filter(|n| NAMES.contains(n))
            .ok_or("InvalidExport")?;
        let length = row["bytes"]
            .as_u64()
            .filter(|n| *n <= MAX_BYTES as u64)
            .ok_or("TooLarge")? as usize;
        total = total
            .checked_add(length)
            .filter(|n| *n <= MAX_BYTES)
            .ok_or("TooLarge")?;
        if output
            .insert(name.to_owned(), read_bounded(&path.join(name), length)?)
            .is_some()
        {
            return Err("InvalidExport".into());
        }
    }
    let mut actual = std::collections::BTreeSet::new();
    for entry in fs::read_dir(path).map_err(|_| "Io")? {
        let name = entry
            .map_err(|_| "Io")?
            .file_name()
            .into_string()
            .map_err(|_| "InvalidExport")?;
        if actual.len() >= 9 {
            return Err("InvalidExport".into());
        }
        actual.insert(name);
    }
    let mut expected = output
        .keys()
        .cloned()
        .collect::<std::collections::BTreeSet<_>>();
    expected.insert("manifest.json".into());
    if actual != expected {
        return Err("InvalidExport".into());
    }
    let bundle = InspectionBundle {
        manifest,
        files: output,
    };
    bundle.validate()?;
    Ok((bundle, manifest_bytes))
}
fn reparse(metadata: &fs::Metadata) -> bool {
    #[cfg(windows)]
    {
        use std::os::windows::fs::MetadataExt;
        metadata.file_attributes() & 0x400 != 0
    }
    #[cfg(not(windows))]
    {
        metadata.file_type().is_symlink()
    }
}
fn checked_path(path: &Path) -> Result<(), String> {
    if !path.is_absolute()
        || path
            .components()
            .any(|c| matches!(c, Component::ParentDir | Component::CurDir))
    {
        return Err("UnsafeDestination".into());
    }
    Ok(())
}
// Pin every approved ancestor without FILE_SHARE_DELETE, rejecting reparse points.
// No destination path is supplied by renderer IPC.
pub(crate) fn pin_directory(path: &Path) -> Result<Vec<File>, String> {
    checked_path(path)?;
    let mut pins = Vec::new();
    let mut current = PathBuf::new();
    for component in path.components() {
        current.push(component.as_os_str());
        if matches!(component, Component::Prefix(_)) {
            continue;
        }
        let metadata = fs::symlink_metadata(&current).map_err(|_| "Io")?;
        if reparse(&metadata) || !metadata.is_dir() {
            return Err("UnsafeDestination".into());
        }
        let mut options = OpenOptions::new();
        options.read(true);
        #[cfg(windows)]
        {
            use std::os::windows::fs::OpenOptionsExt;
            options
                .custom_flags(0x02000000 | 0x00200000)
                .share_mode(1 | 2);
        }
        let file = options.open(&current).map_err(|_| "Io")?;
        if reparse(&file.metadata().map_err(|_| "Io")?) {
            return Err("UnsafeDestination".into());
        }
        pins.push(file);
    }
    Ok(pins)
}
fn read_bounded(path: &Path, expected: usize) -> Result<Vec<u8>, String> {
    let metadata = fs::symlink_metadata(path).map_err(|_| "Io")?;
    if reparse(&metadata) || !metadata.is_file() || metadata.len() != expected as u64 {
        return Err("ChangedExport".into());
    }
    let mut options = OpenOptions::new();
    options.read(true);
    #[cfg(windows)]
    {
        use std::os::windows::fs::OpenOptionsExt;
        options.custom_flags(0x00200000).share_mode(1);
    }
    let file = options.open(path).map_err(|_| "Io")?;
    if reparse(&file.metadata().map_err(|_| "Io")?) {
        return Err("UnsafeDestination".into());
    }
    let mut bytes = Vec::with_capacity(expected);
    file.take(expected as u64 + 1)
        .read_to_end(&mut bytes)
        .map_err(|_| "Io")?;
    if bytes.len() != expected {
        return Err("ChangedExport".into());
    }
    Ok(bytes)
}
pub fn identifier() -> Result<String, String> {
    #[cfg(windows)]
    {
        unsafe { windows::Win32::System::Com::CoCreateGuid() }
            .map(|g| {
                format!("{g:?}")
                    .trim_matches(['{', '}'])
                    .to_ascii_lowercase()
            })
            .map_err(|_| "Io".into())
    }
    #[cfg(not(windows))]
    {
        Err("Unsupported".into())
    }
}
#[cfg(windows)]
pub fn choose_directory(owner: isize) -> Result<Option<PathBuf>, String> {
    choose_directory_for(owner, false)
}
/// A successful native affirmation is consent to inspect this selected source.
/// No renderer argument can change the purpose, warning or affirmative label.
#[cfg(windows)]
pub fn choose_comparison_directory(owner: isize) -> Result<Option<PathBuf>, String> {
    choose_directory_for(owner, true)
}
#[cfg(windows)]
fn choose_directory_for(owner: isize, comparison: bool) -> Result<Option<PathBuf>, String> {
    use windows::{
        core::HSTRING,
        Win32::{Foundation::HWND, System::Com::*, UI::Shell::*},
    };
    unsafe {
        CoInitializeEx(None, COINIT_APARTMENTTHREADED)
            .ok()
            .map_err(|_| "PickerUnavailable")?;
        let result = (|| {
            let dialog: IFileOpenDialog =
                CoCreateInstance(&FileOpenDialog, None, CLSCTX_INPROC_SERVER)
                    .map_err(|_| "PickerUnavailable")?;
            dialog
                .SetOptions(
                    FOS_PICKFOLDERS
                        | FOS_FORCEFILESYSTEM
                        | FOS_PATHMUSTEXIST
                        | FOS_NOCHANGEDIR
                        | FOS_DONTADDTORECENT,
                )
                .map_err(|_| "PickerUnavailable")?;
            let title = if comparison {
                "Inspect a LocalLore comparison: private character truth, inputs, prompts and outputs may reveal spoilers"
            } else {
                "Choose a folder for this LocalLore inspection snapshot"
            };
            dialog
                .SetTitle(&HSTRING::from(title))
                .map_err(|_| "PickerUnavailable")?;
            if comparison {
                dialog
                    .SetOkButtonLabel(&HSTRING::from("Inspect private evidence"))
                    .map_err(|_| "PickerUnavailable")?;
            }
            if let Err(error) = dialog.Show(Some(HWND(owner as *mut _))) {
                return if error.code().0 as u32 == 0x800704c7 {
                    Ok(None)
                } else {
                    Err("PickerUnavailable".into())
                };
            }
            let item = dialog.GetResult().map_err(|_| "PickerUnavailable")?;
            let pointer = item
                .GetDisplayName(SIGDN_FILESYSPATH)
                .map_err(|_| "PickerUnavailable")?;
            let value = pointer.to_string().map_err(|_| "InvalidInput".to_owned());
            CoTaskMemFree(Some(pointer.0.cast()));
            value.map(|p| Some(PathBuf::from(p)))
        })();
        CoUninitialize();
        result
    }
}
#[cfg(not(windows))]
pub fn choose_directory(_: isize) -> Result<Option<PathBuf>, String> {
    Err("Unsupported".into())
}
#[cfg(not(windows))]
pub fn choose_comparison_directory(_: isize) -> Result<Option<PathBuf>, String> {
    Err("Unsupported".into())
}

fn io_category(error: std::io::Error) -> String {
    if error.kind() == std::io::ErrorKind::StorageFull {
        "Full".into()
    } else {
        "Io".into()
    }
}
// Only our exact private GUID namespace is eligible. A live copy holds pin_stage,
// which denies a second DELETE-access pin, so another process's work is retained.
pub fn reap_private_previews(cache: &Path) -> Result<Value, String> {
    if !cache.exists() {
        return Ok(json!({"removed":0,"retained":0,"limited":false}));
    }
    let _pins = pin_directory(cache)?;
    let mut removed = 0;
    let mut retained = 0;
    let mut limited = false;
    for (index, entry) in fs::read_dir(cache).map_err(io_category)?.enumerate() {
        if index >= 128 {
            limited = true;
            break;
        }
        let entry = entry.map_err(io_category)?;
        let name = entry.file_name();
        let Some(name) = name.to_str() else {
            continue;
        };
        let Some(id) = name.strip_prefix("private-preview-") else {
            continue;
        };
        if id.len() != 36
            || !id.bytes().enumerate().all(|(i, b)| {
                if [8, 13, 18, 23].contains(&i) {
                    b == b'-'
                } else {
                    b.is_ascii_hexdigit()
                }
            })
        {
            continue;
        }
        let path = entry.path();
        let Ok(pin) = pin_stage(&path) else {
            retained += 1;
            continue;
        };
        let mut children = Vec::new();
        let mut safe = true;
        match fs::read_dir(&path) {
            Ok(entries) => {
                for child in entries.take(5) {
                    let Ok(child) = child else {
                        safe = false;
                        break;
                    };
                    let name = child.file_name();
                    if ![
                        "snapshot.sqlite",
                        "snapshot.sqlite-journal",
                        "snapshot.sqlite-wal",
                        "snapshot.sqlite-shm",
                    ]
                    .iter()
                    .any(|n| name == *n)
                    {
                        safe = false;
                        break;
                    }
                    match fs::symlink_metadata(child.path()) {
                        Ok(m) if m.is_file() && !reparse(&m) => children.push(child.path()),
                        _ => {
                            safe = false;
                            break;
                        }
                    }
                }
            }
            Err(_) => safe = false,
        }
        if safe {
            for child in children {
                if fs::remove_file(child).is_err() {
                    safe = false;
                    break;
                }
            }
        }
        drop(pin);
        if safe && fs::remove_dir(&path).is_ok() {
            removed += 1;
        } else {
            retained += 1;
        }
    }
    Ok(json!({"removed":removed,"retained":retained,"limited":limited}))
}

pub fn capture_database(source: &Path, cache: &Path) -> Result<(Vec<u8>, Value), String> {
    fs::create_dir_all(cache).map_err(io_category)?;
    let _pins = pin_directory(cache)?;
    let directory = cache.join(format!("private-preview-{}", identifier()?));
    fs::create_dir(&directory).map_err(io_category)?;
    let pin = pin_stage(&directory)?;
    let destination = directory.join("snapshot.sqlite");
    let result = (|| {
        let stories = locallore_workspace::inspection_database_copy(source, &destination)?;
        let length = fs::metadata(&destination).map_err(io_category)?.len();
        if length > MAX_DATABASE as u64 {
            return Err("TooLarge".into());
        }
        Ok((
            read_bounded(&destination, length as usize)?,
            serde_json::to_value(stories).map_err(|_| "Integrity")?,
        ))
    })();
    let _ = fs::remove_file(&destination);
    drop(pin);
    let _ = fs::remove_dir(directory);
    result
}

#[cfg(test)]
mod tests {
    use super::*;
    #[cfg(windows)]
    #[test]
    fn long_unicode_target_renames_the_actual_handle_without_replacing_an_existing_file() {
        use std::os::windows::{ffi::OsStrExt, fs::OpenOptionsExt};
        let root = Root::new();
        let mut directory = root.0.clone();
        while directory.as_os_str().encode_wide().count() < 290 {
            directory.push("Synthetic Unicode save 模型 é");
        }
        fs::create_dir_all(&directory).unwrap();
        let stage = directory.join("stage.partial");
        let target = directory.join("saved story.json");
        let mut handle = OpenOptions::new()
            .read(true)
            .write(true)
            .create_new(true)
            .share_mode(3)
            .access_mode(0x80000000 | 0x40000000 | 0x00010000)
            .open(&stage)
            .unwrap();
        handle
            .write_all(b"synthetic original archive bytes")
            .unwrap();
        handle.sync_all().unwrap();
        assert!(target.as_os_str().encode_wide().count() > 260);
        let result = atomic_finalize(&handle, &stage, &target);
        assert!(result.is_ok(), "actual long target rename: {result:?}");
        assert!(!stage.exists());
        assert_eq!(
            fs::read(&target).unwrap(),
            b"synthetic original archive bytes"
        );
        drop(handle);
        let mut other = OpenOptions::new()
            .read(true)
            .write(true)
            .create_new(true)
            .share_mode(3)
            .access_mode(0x80000000 | 0x40000000 | 0x00010000)
            .open(&stage)
            .unwrap();
        other.write_all(b"must never replace original").unwrap();
        assert_eq!(
            atomic_finalize(&other, &stage, &target).unwrap_err(),
            "ExportExists"
        );
        assert_eq!(
            fs::read(&target).unwrap(),
            b"synthetic original archive bytes"
        );
        assert_eq!(fs::read(&stage).unwrap(), b"must never replace original");
    }
    #[test]
    fn private_trace_fixed_bytes_caps_expiry_and_retirement_use_same_writer() {
        let root = Root::new();
        let broker = ExportBroker::default();
        let value = json!({"scope":{"story":"synthetic","branch":"main"},"head":1,"base_revision":0,"details":{"private":"synthetic original bytes"}});
        let first = broker.insert_capture(1, value.clone(), || true).unwrap();
        let token = first["token"].as_str().unwrap();
        let record = broker.get(1, token).unwrap();
        assert!(broker.get(3, token).is_err());
        let saved = record.save(&root.0, atomic_finalize).unwrap();
        let path = PathBuf::from(saved["location"].as_str().unwrap());
        assert_eq!(
            fs::read(path.join("capture.json")).unwrap(),
            first["text"].as_str().unwrap().as_bytes()
        );
        assert_eq!(
            serde_json::from_slice::<Value>(&fs::read(path.join("manifest.json")).unwrap())
                .unwrap(),
            first["manifest"]
        );
        assert_eq!(fs::read_dir(&path).unwrap().count(), 2);
        broker.invalidate(1);
        assert!(record.open("capture.json").is_err());
        assert!(broker.get(1, token).is_err());
        let broker = ExportBroker::default();
        let first = broker.insert_capture(1, value.clone(), || true).unwrap();
        broker.insert_capture(1, value.clone(), || true).unwrap();
        assert_eq!(
            broker
                .insert_capture(1, value.clone(), || true)
                .unwrap_err(),
            "PreviewLimit"
        );
        let token = first["token"].as_str().unwrap();
        {
            let mut records = broker.0.lock().unwrap();
            Arc::get_mut(records.get_mut(token).unwrap())
                .unwrap()
                .created = Instant::now() - TTL - Duration::from_secs(1);
        }
        assert!(broker.get(1, token).is_err());
        broker.insert_capture(1, value, || true).unwrap();
        let broker = ExportBroker::default();
        let large = json!({"scope":{"story":"synthetic","branch":"main"},"head":0,"padding":"x".repeat(524000)});
        broker.insert_capture(1, large.clone(), || true).unwrap();
        assert_eq!(
            broker.insert_capture(1, large, || true).unwrap_err(),
            "TooLarge",
            "total includes both manifests under the same admission mutex"
        );
        assert_eq!(broker.0.lock().unwrap().len(), 1);
        assert!(broker.insert_capture(1, json!({}), || false).is_err());
        let broker = ExportBroker::default();
        let first = broker
            .insert_capture(
                1,
                json!({"scope":{"story":"synthetic","branch":"main"},"head":0}),
                || true,
            )
            .unwrap();
        let held = broker.get(1, first["token"].as_str().unwrap()).unwrap();
        broker.invalidate(1);
        assert_eq!(
            broker.0.lock().unwrap().len(),
            1,
            "in-flight save/picker retains encoded budget even after capability cancellation"
        );
        broker
            .insert_capture(
                3,
                json!({"scope":{"story":"synthetic","branch":"main"},"head":0}),
                || true,
            )
            .unwrap();
        assert_eq!(
            broker
                .insert_capture(
                    3,
                    json!({"scope":{"story":"synthetic","branch":"main"},"head":0}),
                    || true
                )
                .unwrap_err(),
            "PreviewLimit"
        );
        drop(held);
        broker
            .insert_capture(
                3,
                json!({"scope":{"story":"synthetic","branch":"main"},"head":0}),
                || true,
            )
            .unwrap();
    }
    fn bundle() -> InspectionBundle {
        let host = locallore::host::Host::new(true);
        let created =
            host.call(br#"{"version":1,"command":{"op":"create","seed":"lantern-quay-v1"}}"#);
        host.inspection_snapshot(
            created["data"]["session"].as_str().unwrap(),
            &serde_json::from_value(created["data"]["scope"].clone()).unwrap(),
            0,
            locallore::inspection::ExportMode::Diagnostics,
        )
        .unwrap()
    }
    struct Root(PathBuf);
    impl Root {
        fn new() -> Self {
            let path = std::env::temp_dir()
                .join(format!("locallore-export-unit-{}", identifier().unwrap()));
            fs::create_dir(&path).unwrap();
            Self(path)
        }
    }
    impl Drop for Root {
        fn drop(&mut self) {
            let _ = fs::remove_dir_all(&self.0);
        }
    }
    fn preview(broker: &ExportBroker) -> (String, Arc<Preview>) {
        let value = broker.insert(1, bundle(), || true).unwrap();
        let token = value["token"].as_str().unwrap().to_owned();
        let record = broker.get(1, &token).unwrap();
        (token, record)
    }
    #[test]
    fn imported_compact_manifest_preserves_exact_bytes_and_detects_later_edits() {
        let root = Root::new();
        let broker = ExportBroker::default();
        let (_, record) = preview(&broker);
        let saved = record.save(&root.0, atomic_finalize).unwrap();
        let path = PathBuf::from(saved["location"].as_str().unwrap());
        let raw = serde_json::to_vec(record.bundle.manifest()).unwrap();
        fs::write(path.join("manifest.json"), &raw).unwrap();
        let (bundle, bytes) = load_exact_directory(&path).unwrap();
        assert_eq!(bytes, raw);
        let imported = broker
            .insert_saved(2, bundle, bytes, path.clone(), || true)
            .unwrap();
        let record = broker.get(2, imported["token"].as_str().unwrap()).unwrap();
        assert_eq!(
            record.open("manifest.json").unwrap()["text"],
            String::from_utf8(raw).unwrap()
        );
        fs::write(path.join("manifest.json"), b"{}").unwrap();
        assert_eq!(record.open("manifest.json").unwrap_err(), "ChangedExport");
    }
    #[test]
    fn abandoned_private_cache_reaper_skips_active_and_foreign_directories() {
        let root = Root::new();
        let owned = root
            .0
            .join(format!("private-preview-{}", identifier().unwrap()));
        fs::create_dir(&owned).unwrap();
        fs::write(owned.join("snapshot.sqlite"), b"private").unwrap();
        let foreign = root.0.join("private-preview-not-a-guid");
        fs::create_dir(&foreign).unwrap();
        fs::write(foreign.join("snapshot.sqlite"), b"keep").unwrap();
        let active = pin_stage(&owned).unwrap();
        let result = reap_private_previews(&root.0).unwrap();
        assert_eq!(result["retained"], 1);
        assert!(owned.join("snapshot.sqlite").exists());
        drop(active);
        let result = reap_private_previews(&root.0).unwrap();
        assert_eq!(result["removed"], 1);
        assert!(!owned.exists());
        assert!(foreign.join("snapshot.sqlite").exists());
    }
    #[test]
    fn native_token_keeps_exact_mode_and_bytes_after_renderer_preview_changes() {
        let root = Root::new();
        let broker = ExportBroker::default();
        let mut reply = broker.insert(1, bundle(), || true).unwrap();
        let token = reply["token"].as_str().unwrap().to_owned();
        reply["manifest"]["mode"] = json!("full");
        reply["files"] = json!([{"path":"state.json","bytes":0}]);
        let record = broker.get(1, &token).unwrap();
        assert_eq!(record.bundle.manifest()["mode"], "diagnostics");
        let saved = record.save(&root.0, atomic_finalize).unwrap();
        let path = PathBuf::from(saved["location"].as_str().unwrap());
        let loaded = load_directory(&path).unwrap();
        assert_eq!(loaded.manifest, *record.bundle.manifest());
        assert_eq!(loaded.files, *record.bundle.contents());
        assert!(!path.join("state.json").exists());
        assert_eq!(broker.get(3, &token).err().as_deref(), Some("Closed"));
    }
    #[test]
    fn cancelled_full_and_collision_writes_never_publish_a_partial_snapshot() {
        let root = Root::new();
        let broker = ExportBroker::default();
        let (token, record) = preview(&broker);
        assert_eq!(
            record
                .save_injected(&root.0, atomic_finalize, 1)
                .unwrap_err(),
            "Full"
        );
        assert_eq!(fs::read_dir(&root.0).unwrap().count(), 0);
        let collision = Mutex::new(None);
        assert_eq!(
            record
                .save(&root.0, |handle, stage, target| {
                    fs::create_dir(target).unwrap();
                    fs::write(target.join("existing.txt"), b"untouched").unwrap();
                    *collision.lock().unwrap() = Some(target.to_owned());
                    atomic_finalize(handle, stage, target)
                })
                .unwrap_err(),
            "ExportExists"
        );
        let path = collision.lock().unwrap().clone().unwrap();
        assert_eq!(fs::read(path.join("existing.txt")).unwrap(), b"untouched");
        assert!(!fs::read_dir(&root.0).unwrap().any(|e| e
            .unwrap()
            .file_name()
            .to_string_lossy()
            .starts_with(".locallore-staging-")));
        broker.cancel(1, &token).unwrap();
        assert_eq!(
            record.save(&root.0, atomic_finalize).unwrap_err(),
            "Cancelled"
        );
    }
    #[test]
    fn open_is_read_only_and_rejects_changed_or_unlisted_files() {
        let root = Root::new();
        let broker = ExportBroker::default();
        let (_, record) = preview(&broker);
        let saved = record.save(&root.0, atomic_finalize).unwrap();
        let path = PathBuf::from(saved["location"].as_str().unwrap());
        assert_eq!(record.open("../outside").unwrap_err(), "InvalidInput");
        assert_eq!(record.open("manifest.json").unwrap()["read_only"], true);
        fs::write(path.join("unlisted.txt"), b"not opened").unwrap();
        assert_eq!(load_directory(&path).unwrap_err(), "InvalidExport");
        fs::remove_file(path.join("unlisted.txt")).unwrap();
        fs::write(path.join("diagnostics.json"), b"changed").unwrap();
        assert_eq!(
            record.open("diagnostics.json").unwrap_err(),
            "ChangedExport"
        );
        assert!(load_directory(&path).is_err());
    }
    #[test]
    fn traversal_bad_bundle_expiry_and_preview_limits_fail_closed() {
        let root = Root::new();
        assert_eq!(
            pin_directory(&root.0.join("..")).unwrap_err(),
            "UnsafeDestination"
        );
        assert_eq!(
            pin_directory(Path::new("relative")).unwrap_err(),
            "UnsafeDestination"
        );
        let mut bad = bundle();
        bad.files.insert("../outside".into(), vec![]);
        assert!(files(&NativeSnapshot::Inspection(bad)).is_err());
        let broker = ExportBroker::default();
        let (token, _) = preview(&broker);
        preview(&broker);
        assert_eq!(
            broker.insert(1, bundle(), || true).unwrap_err(),
            "PreviewLimit"
        );
        broker.invalidate(1);
        assert_eq!(
            broker.get(1, &token).err().as_deref(),
            Some("UnknownExport")
        );
        assert_eq!(broker.insert(1, bundle(), || false).unwrap_err(), "Closed");
        let old = Preview {
            bundle: NativeSnapshot::Inspection(bundle()),
            epoch: 1,
            created: Instant::now() - TTL - Duration::from_secs(1),
            cancelled: AtomicBool::new(false),
            saving: AtomicBool::new(false),
            saved: Mutex::new(None),
        };
        assert_eq!(old.save(&root.0, atomic_finalize).unwrap_err(), "Cancelled");
    }
    #[test]
    fn pinned_staging_cannot_be_renamed_or_replaced_before_writes() {
        let root = Root::new();
        let broker = ExportBroker::default();
        let (_, record) = preview(&broker);
        let moved = root.0.join("attacker-replacement");
        let observed = Arc::new(AtomicBool::new(false));
        let checked = observed.clone();
        record
            .save_impl(
                &root.0,
                atomic_finalize,
                None,
                Some(Box::new(move |stage| {
                    assert!(fs::rename(stage, &moved).is_err());
                    assert!(stage.is_dir());
                    assert!(!moved.exists());
                    checked.store(true, Ordering::SeqCst);
                })),
            )
            .unwrap();
        assert!(observed.load(Ordering::SeqCst));
    }
    #[test]
    fn concurrent_open_waits_for_save_without_holding_the_window_gate() {
        use std::sync::{mpsc, Barrier};
        let root = Root::new();
        let broker = ExportBroker::default();
        let (_, record) = preview(&broker);
        let lease = Arc::new(super::super::lease::WindowLease::default());
        let epoch = lease.begin().unwrap();
        let entered = Arc::new(Barrier::new(2));
        let release = Arc::new(Barrier::new(2));
        let save = {
            let record = record.clone();
            let lease = lease.clone();
            let entered = entered.clone();
            let release = release.clone();
            let path = root.0.clone();
            std::thread::spawn(move || {
                record.save(&path, |handle, stage, target| {
                    entered.wait();
                    release.wait();
                    lease.dispatch(epoch, || atomic_finalize(handle, stage, target))
                })
            })
        };
        entered.wait();
        let (ready_tx, ready_rx) = mpsc::channel();
        let open = {
            let record = record.clone();
            let lease = lease.clone();
            std::thread::spawn(move || {
                ready_tx.send(()).unwrap();
                record.open_current("manifest.json", &lease, epoch)
            })
        };
        ready_rx.recv_timeout(Duration::from_secs(2)).unwrap();
        // Read-only open must not acquire this gate while it waits for saved publication.
        lease.dispatch(epoch, || Ok(())).unwrap();
        release.wait();
        save.join().unwrap().unwrap();
        assert_eq!(open.join().unwrap().unwrap()["read_only"], true);
    }
}
