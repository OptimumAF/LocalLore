//! Native-owned verified model lifecycle. No renderer-supplied file or executable paths.
use crate::{exports, lease::WindowLease};
use locallore::{host::Host, play::PlayProfile};
use locallore_local_runtime::{LocalRuntime, MODEL_BYTES, MODEL_SHA256, PROFILE, RUNTIME_COMMIT};
use serde_json::{json, Value};
use sha2::{Digest, Sha256};
use std::{
    fs::{self, OpenOptions},
    io::{Read, Write},
    path::{Path, PathBuf},
    sync::{
        atomic::{AtomicBool, Ordering},
        Arc, Mutex,
    },
};
type SharedRuntime = Arc<Mutex<LocalRuntime>>;
struct Inner {
    phase: &'static str,
    percent: u64,
    error: Option<String>,
    job: u64,
    cancel: Arc<AtomicBool>,
    runtime: Option<SharedRuntime>,
    profile: Option<PlayProfile>,
}
pub struct ModelManager {
    root: PathBuf,
    resource: PathBuf,
    inner: Mutex<Inner>,
}
impl ModelManager {
    pub fn new(root: PathBuf, resource: PathBuf) -> Self {
        Self {
            root,
            resource,
            inner: Mutex::new(Inner {
                phase: "unloaded",
                percent: 0,
                error: None,
                job: 0,
                cancel: Arc::new(AtomicBool::new(false)),
                runtime: None,
                profile: None,
            }),
        }
    }
    fn path(&self) -> PathBuf {
        self.root.join("Qwen3-0.6B-Q8_0.gguf")
    }
    pub fn status(&self) -> Result<Value, String> {
        let imported = self.path().is_file();
        let mut s = self.inner.lock().map_err(|_| "Internal")?;
        let failed = s.runtime.as_ref().is_some_and(|owner| {
            owner.try_lock().is_ok_and(|runtime| {
                matches!(runtime.status(), locallore_local_runtime::Status::Failed)
            })
        });
        if failed {
            s.phase = "failed";
            s.error = Some("Runtime".into());
        }
        Ok(
            json!({"operation_id":s.job,"resident":s.runtime.is_some(),"phase":s.phase,"percent":s.percent,"error":s.error,"loaded":s.runtime.is_some()&&!failed,"imported":imported,"profile":s.profile,"available_profile":{"id":PROFILE,"model_bytes":MODEL_BYTES,"model_sha256":MODEL_SHA256,"runtime_revision":RUNTIME_COMMIT,"device":"CPU: experimental Windows x64","qualification":"Experimental. Narrative quality and offline qualification remain pending."}}),
        )
    }
    fn begin(&self, phase: &'static str) -> Result<(u64, Arc<AtomicBool>), String> {
        let mut s = self.inner.lock().map_err(|_| "Internal")?;
        if matches!(
            s.phase,
            "choosing" | "checking" | "copying" | "loading" | "unloading"
        ) {
            return Err("Busy".into());
        }
        if s.runtime.is_some() && phase != "unloading" {
            return Err("ModelLoaded".into());
        }
        s.job += 1;
        s.cancel = Arc::new(AtomicBool::new(false));
        s.phase = phase;
        s.percent = 0;
        s.error = None;
        Ok((s.job, s.cancel.clone()))
    }
    fn progress(&self, job: u64, phase: &'static str, percent: u64) {
        if let Ok(mut s) = self.inner.lock() {
            if s.job == job {
                s.phase = phase;
                s.percent = percent.min(100);
            }
        }
    }
    fn finish(&self, job: u64, result: &Result<(), String>) {
        if let Ok(mut s) = self.inner.lock() {
            if s.job == job {
                s.phase = if s.runtime.is_some() {
                    "loaded"
                } else if result
                    .as_ref()
                    .err()
                    .is_some_and(|e| e != "Cancelled" && e != "Closed")
                {
                    "failed"
                } else {
                    "unloaded"
                };
                s.error = result
                    .as_ref()
                    .err()
                    .filter(|e| *e != "Cancelled" && *e != "Closed")
                    .cloned();
                s.percent = if result.is_ok() { 100 } else { 0 };
            }
        }
    }
    pub fn cancel(&self) -> Result<Value, String> {
        let s = self.inner.lock().map_err(|_| "Internal")?;
        s.cancel.store(true, Ordering::SeqCst);
        Ok(json!({"status":"cancelling"}))
    }
    pub fn import(
        &self,
        lease: &WindowLease,
        epoch: u64,
        pick: impl FnOnce() -> Result<Option<PathBuf>, String>,
    ) -> Result<Value, String> {
        let (job, cancel) = lease.dispatch(epoch, || self.begin("choosing"))?;
        let result = (|| {
            if cancel.load(Ordering::SeqCst) || !lease.valid(epoch) {
                return Err("Closed".into());
            }
            let Some(source) = pick()? else {
                return Err("Cancelled".into());
            };
            let cancelled = || cancel.load(Ordering::SeqCst) || !lease.valid(epoch);
            copy_model(
                &source,
                &self.root,
                cancelled,
                |phase, n| self.progress(job, phase, n),
                |handle, staging, target| {
                    lease.dispatch(epoch, || {
                        if cancel.load(Ordering::SeqCst) {
                            return Err("Cancelled".into());
                        }
                        exports::atomic_finalize(handle, staging, target).map_err(|e| {
                            if e == "ExportExists" {
                                "ModelExists".into()
                            } else {
                                e
                            }
                        })
                    })
                },
            )
        })();
        self.finish(job, &result);
        match result {
            Ok(()) => self.status(),
            Err(e) if e == "Cancelled" => self.status(),
            Err(e) => Err(e),
        }
    }
    pub fn load(&self, host: &Host, lease: &WindowLease, epoch: u64) -> Result<Value, String> {
        let (job, cancel) = lease.dispatch(epoch, || self.begin("loading"))?;
        let result = (|| {
            if !lease.valid(epoch) {
                return Err("Closed".into());
            }
            let mut runtime =
                LocalRuntime::spawn_packaged_cancelled(&self.resource, &self.path(), || {
                    cancel.load(Ordering::SeqCst) || !lease.valid(epoch)
                })
                .map_err(runtime_error)?;
            runtime
                .load(|| cancel.load(Ordering::SeqCst) || !lease.valid(epoch))
                .map_err(runtime_error)?;
            let profile = PlayProfile {
                id: PROFILE.into(),
                model_sha256: MODEL_SHA256.into(),
                runtime_revision: RUNTIME_COMMIT.into(),
                template_sha256: "57f1fd00f0013a2be96aa79b857391f27e23df5b5f847072b524c897e24d0361"
                    .into(),
                worker_sha256: runtime.worker_sha256().into(),
                profile_manifest_sha256: locallore_local_runtime::profile_manifest_sha256(),
                context_tokens: 4096,
                director_tokens: 350,
                narrator_tokens: 350,
                deadline_ms: 120000,
                repair_limit: 1,
            };
            profile.validate().map_err(|e| e.to_string())?;
            let shared = Arc::new(Mutex::new(runtime));
            lease.dispatch(epoch, || {
                let mut s = self.inner.lock().map_err(|_| "Internal")?;
                if s.job != job || cancel.load(Ordering::SeqCst) {
                    return Err("Cancelled".into());
                }
                let owner = shared.clone();
                host.configure_local_provider(
                    profile.clone(),
                    Arc::new(move || {
                        Box::new(locallore_local_runtime::adapter::RuntimeProvider::new(
                            owner.clone(),
                        ))
                    }),
                )?;
                s.runtime = Some(shared.clone());
                s.profile = Some(profile);
                Ok(())
            })
        })();
        self.finish(job, &result);
        result?;
        self.status()
    }
    pub fn unload(&self, host: &Host, lease: &WindowLease, epoch: u64) -> Result<Value, String> {
        let (job, runtime) = lease.dispatch(epoch, || {
            let (job, _) = self.begin("unloading")?;
            host.disable_local_provider();
            let mut s = self.inner.lock().map_err(|_| "Internal")?;
            s.profile = None;
            Ok((job, s.runtime.take()))
        })?;
        let result = if let Some(owner) = runtime {
            owner
                .lock()
                .map_err(|_| "Internal".to_owned())?
                .shutdown()
                .map_err(runtime_error)
        } else {
            Ok(())
        };
        self.finish(job, &result);
        result?;
        self.status()
    }
    // Synchronous revocation happens before the close cleanup worker is scheduled.
    pub fn retire(&self) -> Option<(u64, Option<SharedRuntime>)> {
        let mut s = self.inner.lock().ok()?;
        s.cancel.store(true, Ordering::SeqCst);
        s.job += 1;
        s.phase = "unloading";
        s.profile = None;
        Some((s.job, s.runtime.take()))
    }
    pub fn close(&self, host: Option<&Host>, retired: Option<(u64, Option<SharedRuntime>)>) {
        if let Some(host) = host {
            host.disable_local_provider();
        }
        let Some((job, runtime)) = retired else {
            return;
        };
        if let Some(owner) = runtime {
            if let Ok(mut r) = owner.lock() {
                let _ = r.shutdown();
            }
        }
        if let Ok(mut s) = self.inner.lock() {
            if s.job == job {
                s.phase = "unloaded";
                s.error = None;
            }
        }
    }
}
fn runtime_error(error: locallore_local_runtime::Error) -> String {
    format!("{error:?}")
}
fn copy_model(
    source: &Path,
    root: &Path,
    cancelled: impl Fn() -> bool,
    progress: impl Fn(&'static str, u64),
    publish: impl FnOnce(&std::fs::File, &Path, &Path) -> Result<(), String>,
) -> Result<(), String> {
    progress("checking", 0);
    if cancelled() {
        return Err("Cancelled".into());
    }
    let _source_pins = exports::pin_directory(source.parent().ok_or("ModelInvalid")?)?;
    let mut options = OpenOptions::new();
    options.read(true);
    #[cfg(windows)]
    {
        use std::os::windows::fs::OpenOptionsExt;
        options.share_mode(1).custom_flags(0x00200000);
    }
    let mut input = options.open(source).map_err(|_| "ModelInvalid")?;
    let meta = input.metadata().map_err(|_| "ModelInvalid")?;
    #[cfg(windows)]
    {
        use std::os::windows::fs::MetadataExt;
        if meta.file_attributes() & 0x400 != 0 {
            return Err("ModelInvalid".into());
        }
    }
    if !meta.is_file() || meta.len() != MODEL_BYTES {
        return Err("ModelInvalid".into());
    }
    fs::create_dir_all(root).map_err(|_| "Io")?;
    let _pins = exports::pin_directory(root)?;
    if root.join("Qwen3-0.6B-Q8_0.gguf").exists() {
        return Err("ModelExists".into());
    }
    if available(root)? < MODEL_BYTES + 64 * 1024 * 1024 {
        return Err("InsufficientSpace".into());
    }
    let staging = root.join(format!(".import-{}.part", exports::identifier()?));
    let target = root.join("Qwen3-0.6B-Q8_0.gguf");
    let result = (|| {
        let mut options = OpenOptions::new();
        options.write(true).create_new(true);
        #[cfg(windows)]
        {
            use std::os::windows::fs::OpenOptionsExt;
            options.access_mode(0x40000000 | 0x00010000).share_mode(1);
        }
        let mut output = options.open(&staging).map_err(|_| "Io")?;
        let mut digest = Sha256::new();
        let mut chunk = vec![0u8; 1024 * 1024];
        let mut count = 0;
        loop {
            if cancelled() {
                return Err("Cancelled".into());
            }
            let n = input.read(&mut chunk).map_err(|_| "Io")?;
            if n == 0 {
                break;
            }
            count += n as u64;
            if count > MODEL_BYTES {
                return Err("ModelInvalid".into());
            }
            digest.update(&chunk[..n]);
            output.write_all(&chunk[..n]).map_err(|_| "Io")?;
            progress("copying", count * 100 / MODEL_BYTES);
        }
        if count != MODEL_BYTES || format!("{:x}", digest.finalize()) != MODEL_SHA256 {
            return Err("ModelInvalid".into());
        }
        output.sync_all().map_err(|_| "Io")?;
        if cancelled() {
            return Err("Cancelled".into());
        }
        // Windows rename never replaces an existing model. Existing imported artifact is immutable.
        publish(&output, &staging, &target)?;
        Ok(())
    })();
    if result.is_err() {
        let _ = fs::remove_file(staging);
    }
    result
}
fn available(path: &Path) -> Result<u64, String> {
    #[cfg(windows)]
    {
        use std::os::windows::ffi::OsStrExt;
        use windows::{core::PCWSTR, Win32::Storage::FileSystem::GetDiskFreeSpaceExW};
        let wide = path
            .as_os_str()
            .encode_wide()
            .chain(Some(0))
            .collect::<Vec<_>>();
        let mut available = 0;
        unsafe { GetDiskFreeSpaceExW(PCWSTR(wide.as_ptr()), Some(&mut available), None, None) }
            .map_err(|_| "Io")?;
        Ok(available)
    }
    #[cfg(not(windows))]
    {
        let _ = path;
        Err("Unsupported".into())
    }
}
pub fn choose_model(owner: isize) -> Result<Option<PathBuf>, String> {
    #[cfg(windows)]
    {
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
                        FOS_FORCEFILESYSTEM
                            | FOS_FILEMUSTEXIST
                            | FOS_PATHMUSTEXIST
                            | FOS_NOCHANGEDIR
                            | FOS_DONTADDTORECENT,
                    )
                    .map_err(|_| "PickerUnavailable")?;
                dialog
                    .SetTitle(&HSTRING::from(
                        "Import the approved Qwen3-0.6B Q8_0 GGUF (local copy)",
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
                let p = item
                    .GetDisplayName(SIGDN_FILESYSPATH)
                    .map_err(|_| "PickerUnavailable")?;
                let result = p
                    .to_string()
                    .map(|s| Some(PathBuf::from(s)))
                    .map_err(|_| "InvalidInput".into());
                CoTaskMemFree(Some(p.0.cast()));
                result
            })();
            CoUninitialize();
            result
        }
    }
    #[cfg(not(windows))]
    {
        let _ = owner;
        Err("Unsupported".into())
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    struct Root(PathBuf);
    impl Root {
        fn new() -> Self {
            let p = std::env::temp_dir().join(format!(
                "locallore-model-unit-{}",
                exports::identifier().unwrap()
            ));
            fs::create_dir(&p).unwrap();
            Self(p)
        }
    }
    impl Drop for Root {
        fn drop(&mut self) {
            let _ = fs::remove_dir_all(&self.0);
        }
    }
    #[test]
    fn old_window_cancellation_cannot_reach_a_new_model_operation() {
        let root = Root::new();
        let manager = ModelManager::new(root.0.clone(), root.0.clone());
        let lease = WindowLease::default();
        let old = lease.begin().unwrap();
        let closed = lease.invalidate("main-1").unwrap();
        lease.finish_close(closed, || {});
        let current = lease.begin().unwrap();
        let (_, cancel) = manager.begin("loading").unwrap();
        assert_eq!(
            lease.dispatch(old, || manager.cancel()).unwrap_err(),
            "Closed"
        );
        assert!(!cancel.load(Ordering::SeqCst));
        assert!(lease.dispatch(current, || manager.cancel()).is_ok());
        assert!(cancel.load(Ordering::SeqCst));
    }
    #[test]
    fn delayed_closed_operations_cannot_start_picker_or_unload_new_window() {
        let root = Root::new();
        let manager = ModelManager::new(root.0.clone(), root.0.clone());
        let lease = WindowLease::default();
        let old = lease.begin().unwrap();
        let closed = lease.invalidate("main-1").unwrap();
        lease.finish_close(closed, || {});
        let _new = lease.begin().unwrap();
        let called = AtomicBool::new(false);
        assert_eq!(
            manager
                .import(&lease, old, || {
                    called.store(true, Ordering::SeqCst);
                    Ok(None)
                })
                .unwrap_err(),
            "Closed"
        );
        assert!(!called.load(Ordering::SeqCst));
        assert_eq!(
            manager.unload(&Host::new(true), &lease, old).unwrap_err(),
            "Closed"
        );
        assert_eq!(manager.status().unwrap()["operation_id"], 0);
    }
    #[test]
    fn invalid_sources_cancel_and_missing_worker_are_honest() {
        let root = Root::new();
        let lease = WindowLease::default();
        let epoch = lease.begin().unwrap();
        let manager = ModelManager::new(root.0.join("models"), root.0.join("missing-runtime"));
        assert_eq!(
            manager
                .import(&lease, epoch, || Ok(Some(root.0.join("missing.gguf"))))
                .unwrap_err(),
            "ModelInvalid"
        );
        let corrupt = root.0.join("corrupt model.gguf");
        fs::write(&corrupt, b"not GGUF").unwrap();
        assert_eq!(
            manager
                .import(&lease, epoch, || Ok(Some(corrupt.clone())))
                .unwrap_err(),
            "ModelInvalid"
        );
        assert_eq!(fs::read(&corrupt).unwrap(), b"not GGUF");
        assert_eq!(
            manager.import(&lease, epoch, || Ok(None)).unwrap()["phase"],
            "unloaded"
        );
        assert!(!manager.path().exists());
        let host = Host::new(true);
        assert!(manager.load(&host, &lease, epoch).is_err());
        assert_eq!(manager.status().unwrap()["loaded"], false);
    }
    #[test]
    fn retirement_fences_late_metadata_and_new_loads_until_cleanup() {
        let root = Root::new();
        let manager = ModelManager::new(root.0.clone(), root.0.clone());
        let (job, cancel) = manager.begin("checking").unwrap();
        let retired = manager.retire();
        assert!(cancel.load(Ordering::SeqCst));
        manager.progress(job, "loaded", 100);
        manager.finish(job, &Ok(()));
        assert_eq!(manager.status().unwrap()["phase"], "unloading");
        assert_eq!(manager.begin("loading").err().unwrap(), "Busy");
        manager.close(None, retired);
        assert_eq!(manager.status().unwrap()["loaded"], false);
        assert!(manager.begin("loading").is_ok());
    }
}
