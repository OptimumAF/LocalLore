// Copyright 2026 LocalLore contributors. SPDX-License-Identifier: Apache-2.0
//! Bounded local native inference owner. No engine, database, network or model downloads.
#[cfg(feature = "engine-adapter")]
pub mod adapter;
use serde::{Deserialize, Serialize};
use serde_json::{json, Value};
use sha2::{Digest, Sha256};
use std::{
    fs::{File, OpenOptions},
    io::{Read, Write},
    path::Path,
    process::{Child, Command, Stdio},
    sync::{
        atomic::{AtomicBool, Ordering},
        mpsc, Arc,
    },
    thread::{self, JoinHandle},
    time::{Duration, Instant},
};

pub const PROFILE: &str = "qwen3-0.6b-q8-cpu-v1";
pub const MODEL_BYTES: u64 = 639_446_688;
pub const MODEL_SHA256: &str = "9465e63a22add5354d9bb4b99e90117043c7124007664907259bd16d043bb031";
pub const RUNTIME_COMMIT: &str = "620d2225cc436ab0b001e3200e590e3b286ef9ab";
const MAX_FRAME: usize = 32_768;
const MAX_PIPE: usize = 65_536;

#[derive(Clone, Copy, Debug, PartialEq, Eq, Serialize)]
pub enum Error {
    InvalidRequest,
    ModelInvalid,
    WorkerUnavailable,
    Protocol,
    Busy,
    Cancelled,
    Timeout,
    Cleanup,
    Runtime,
}
#[derive(Clone, Copy, Debug, PartialEq, Eq, Serialize)]
pub enum Status {
    Unloaded,
    Loaded,
    Failed,
}
#[derive(Clone, Copy, Debug, Serialize)]
#[serde(rename_all = "snake_case")]
pub enum Role {
    Director,
    Narrator,
}
#[derive(Clone, Debug)]
pub struct Generation {
    pub role: Role,
    pub prompt: String,
    pub schema: Option<Value>,
    pub max_tokens: u16,
}
#[derive(Clone, Debug, Default, Deserialize, Serialize, PartialEq)]
#[serde(deny_unknown_fields)]
pub struct Metrics {
    pub load_ms: f64,
    pub prefill_ms: f64,
    pub decode_ms: f64,
    pub total_ms: f64,
    pub input_tokens: u32,
    pub output_tokens: u32,
    pub model_loads: u32,
    pub contexts_created: u32,
    pub abort_callbacks: u32,
}
#[derive(Clone, Debug, Deserialize, Serialize)]
#[serde(deny_unknown_fields)]
pub struct GenerationResult {
    pub text: String,
    pub metrics: Metrics,
}
#[derive(Deserialize)]
#[serde(deny_unknown_fields)]
struct Reply {
    version: u16,
    id: u64,
    status: String,
    error: Option<String>,
    text: String,
    metrics: Metrics,
}

struct PinnedFile {
    path: std::path::PathBuf,
    file: File,
    ancestors: Vec<File>,
}

fn ancestor_paths(absolute: &Path) -> Result<Vec<std::path::PathBuf>, Error> {
    let mut paths: Vec<_> = absolute
        .parent()
        .ok_or(Error::InvalidRequest)?
        .ancestors()
        .map(Path::to_path_buf)
        .collect();
    paths.reverse();
    Ok(paths)
}

// Root-to-leaf pinning makes every next path lookup occur under an already locked parent.
// Holding a leaf first is insufficient: a not-yet-locked ancestor could be replaced meanwhile.
fn pin_file(path: &Path, error: Error) -> Result<PinnedFile, Error> {
    let absolute = std::path::absolute(path).map_err(|_| error)?;
    let directories = ancestor_paths(&absolute).map_err(|_| error)?;
    #[cfg(windows)]
    let mut ancestors = vec![];
    #[cfg(not(windows))]
    let ancestors = vec![];
    #[cfg(windows)]
    {
        use std::os::windows::fs::{MetadataExt, OpenOptionsExt};
        for directory in directories {
            let mut options = OpenOptions::new();
            options.read(true).share_mode(1).custom_flags(0x0220_0000);
            let handle = options.open(directory).map_err(|_| error)?;
            let metadata = handle.metadata().map_err(|_| error)?;
            if !metadata.is_dir() || metadata.file_attributes() & 0x400 != 0 {
                return Err(error);
            }
            ancestors.push(handle);
        }
    }
    #[cfg(not(windows))]
    let _ = directories;
    let mut options = OpenOptions::new();
    options.read(true);
    #[cfg(windows)]
    {
        use std::os::windows::fs::OpenOptionsExt;
        options.share_mode(1).custom_flags(0x0020_0000);
    }
    let file = options.open(&absolute).map_err(|_| error)?;
    let metadata = file.metadata().map_err(|_| error)?;
    if !metadata.is_file() {
        return Err(error);
    }
    #[cfg(windows)]
    {
        use std::os::windows::fs::MetadataExt;
        if metadata.file_attributes() & 0x400 != 0 {
            return Err(error);
        }
    }
    Ok(PinnedFile {
        path: absolute,
        file,
        ancestors,
    })
}
fn hash_file(file: &mut File, error: Error, cancel: &impl Fn() -> bool) -> Result<String, Error> {
    let mut digest = Sha256::new();
    let mut chunk = vec![0; 65_536];
    loop {
        if cancel() {
            return Err(Error::Cancelled);
        }
        let count = file.read(&mut chunk).map_err(|_| error)?;
        if count == 0 {
            break;
        }
        digest.update(&chunk[..count]);
    }
    Ok(format!("{:x}", digest.finalize()))
}
fn verified_model(path: &Path, cancel: &impl Fn() -> bool) -> Result<PinnedFile, Error> {
    if cancel() {
        return Err(Error::Cancelled);
    }
    let mut pinned = pin_file(path, Error::ModelInvalid)?;
    if pinned
        .file
        .metadata()
        .map_err(|_| Error::ModelInvalid)?
        .len()
        != MODEL_BYTES
        || hash_file(&mut pinned.file, Error::ModelInvalid, cancel)? != MODEL_SHA256
    {
        return Err(Error::ModelInvalid);
    }
    Ok(pinned)
}
fn canonical_json(value: &Value) -> Value {
    match value {
        Value::Object(object) => {
            let sorted: std::collections::BTreeMap<_, _> = object.iter().collect();
            let mut result = serde_json::Map::new();
            for (key, value) in sorted {
                result.insert(key.clone(), canonical_json(value));
            }
            Value::Object(result)
        }
        Value::Array(array) => Value::Array(array.iter().map(canonical_json).collect()),
        _ => value.clone(),
    }
}
/// Hash of the embedded reviewed profile after recursive object-key sorting and compact JSON
/// serialization. Arrays retain order; this is the pinned serde JSON encoding, not RFC8785.
pub fn profile_manifest_sha256() -> String {
    let profile: Value =
        serde_json::from_str(include_str!("../../../native/llama-worker/profile-v1.json"))
            .expect("embedded runtime profile is valid JSON");
    let bytes =
        serde_json::to_vec(&canonical_json(&profile)).expect("embedded runtime profile serializes");
    format!("{:x}", Sha256::digest(bytes))
}

/// One trusted packaged executable and one verified, locked artifact. Calls block and must run
/// on the application's bounded worker. The cancellation closure never grants model authority.
pub struct LocalRuntime {
    child: Child,
    writer: Option<mpsc::SyncSender<Vec<u8>>>,
    replies: mpsc::Receiver<Result<Vec<u8>, Error>>,
    fault: Arc<AtomicBool>,
    threads: Vec<JoinHandle<()>>,
    _model: File,
    _ancestors: Vec<File>,
    _worker: Option<File>,
    _worker_ancestors: Vec<File>,
    worker_sha256: String,
    next_id: u64,
    status: Status,
    deadline: Duration,
    last_metrics: Option<Metrics>,
}
impl LocalRuntime {
    pub fn spawn_packaged(resource_dir: &Path, model: &Path) -> Result<Self, Error> {
        Self::spawn_packaged_cancelled(resource_dir, model, || false)
    }
    pub fn spawn_packaged_cancelled(
        resource_dir: &Path,
        model: &Path,
        cancel: impl Fn() -> bool,
    ) -> Result<Self, Error> {
        Self::spawn_cancelled(
            &resource_dir.join("locallore-llama-worker.exe"),
            model,
            &cancel,
        )
    }
    #[cfg(feature = "development-worker")]
    pub fn spawn_development(executable: &Path, model: &Path) -> Result<Self, Error> {
        Self::spawn_cancelled(executable, model, &|| false)
    }
    fn spawn_cancelled(
        executable: &Path,
        model: &Path,
        cancel: &impl Fn() -> bool,
    ) -> Result<Self, Error> {
        let model = verified_model(model, cancel)?;
        if cancel() {
            return Err(Error::Cancelled);
        }
        let mut worker = pin_file(executable, Error::WorkerUnavailable)?;
        let bytes = worker
            .file
            .metadata()
            .map_err(|_| Error::WorkerUnavailable)?
            .len();
        if bytes == 0 || bytes > 128 * 1024 * 1024 {
            return Err(Error::WorkerUnavailable);
        }
        let digest = hash_file(&mut worker.file, Error::WorkerUnavailable, cancel)?;
        let mut owner = Self::start_cancelled(&worker.path, &model.path, model.file, cancel)?;
        owner._ancestors = model.ancestors;
        owner._worker = Some(worker.file);
        owner._worker_ancestors = worker.ancestors;
        owner.worker_sha256 = digest;
        Ok(owner)
    }
    #[cfg(all(test, feature = "development-worker"))]
    fn start(executable: &Path, model: &Path, file: File) -> Result<Self, Error> {
        Self::start_cancelled(executable, model, file, &|| false)
    }
    fn start_cancelled(
        executable: &Path,
        model: &Path,
        file: File,
        cancel: &impl Fn() -> bool,
    ) -> Result<Self, Error> {
        let mut command = Command::new(executable);
        command
            .arg("--model")
            .arg(model)
            .stdin(Stdio::piped())
            .stdout(Stdio::piped())
            .stderr(Stdio::piped());
        for (key, _) in std::env::vars_os() {
            let name = key.to_string_lossy().to_uppercase();
            if ["LLAMA_", "GGML_", "HF_", "HUGGINGFACE_"]
                .iter()
                .any(|p| name.starts_with(p))
            {
                command.env_remove(key);
            }
        }
        #[cfg(windows)]
        {
            use std::os::windows::process::CommandExt;
            command.creation_flags(0x0800_0000);
        }
        if cancel() {
            return Err(Error::Cancelled);
        }
        let mut child = command.spawn().map_err(|_| Error::WorkerUnavailable)?;
        let mut stdin = child.stdin.take().ok_or(Error::WorkerUnavailable)?;
        let mut stdout = child.stdout.take().ok_or(Error::WorkerUnavailable)?;
        let mut stderr = child.stderr.take().ok_or(Error::WorkerUnavailable)?;
        let fault = Arc::new(AtomicBool::new(false));
        let (writer, writes) = mpsc::sync_channel::<Vec<u8>>(2);
        let (results, replies) = mpsc::sync_channel(2);
        let write_fault = fault.clone();
        let write_thread = thread::spawn(move || {
            while let Ok(frame) = writes.recv() {
                if stdin.write_all(&frame).and_then(|_| stdin.flush()).is_err() {
                    write_fault.store(true, Ordering::SeqCst);
                    break;
                }
            }
        });
        let read_fault = fault.clone();
        let read_thread = thread::spawn(move || loop {
            let mut frame = vec![];
            loop {
                let mut byte = [0];
                match stdout.read(&mut byte) {
                    Ok(1) if byte[0] == b'\n' => break,
                    Ok(1) if frame.len() < MAX_FRAME => frame.push(byte[0]),
                    _ => {
                        read_fault.store(true, Ordering::SeqCst);
                        let _ = results.try_send(Err(Error::Protocol));
                        return;
                    }
                }
            }
            if results.try_send(Ok(frame)).is_err() {
                read_fault.store(true, Ordering::SeqCst);
                return;
            }
        });
        let error_fault = fault.clone();
        let error_thread = thread::spawn(move || {
            let mut count = 0;
            let mut block = [0; 4096];
            loop {
                match stderr.read(&mut block) {
                    Ok(0) | Err(_) => return,
                    Ok(n) => {
                        count += n;
                        if count > MAX_PIPE {
                            error_fault.store(true, Ordering::SeqCst);
                            return;
                        }
                    }
                }
            }
        });
        Ok(Self {
            child,
            writer: Some(writer),
            replies,
            fault,
            threads: vec![write_thread, read_thread, error_thread],
            _model: file,
            _ancestors: vec![],
            _worker: None,
            _worker_ancestors: vec![],
            worker_sha256: String::new(),
            next_id: 0,
            status: Status::Unloaded,
            deadline: Duration::from_secs(60),
            last_metrics: None,
        })
    }
    /// Identity of the exact read-only executable handle retained across process creation.
    pub fn worker_sha256(&self) -> &str {
        &self.worker_sha256
    }
    pub fn profile_manifest_sha256(&self) -> String {
        profile_manifest_sha256()
    }
    pub fn status(&self) -> Status {
        self.status
    }
    pub fn last_metrics(&self) -> Option<&Metrics> {
        self.last_metrics.as_ref()
    }
    fn send(&mut self, value: Value) -> Result<(), Error> {
        let mut bytes = serde_json::to_vec(&value).map_err(|_| Error::InvalidRequest)?;
        if bytes.len() > MAX_FRAME {
            return Err(Error::InvalidRequest);
        }
        bytes.push(b'\n');
        self.writer
            .as_ref()
            .ok_or(Error::WorkerUnavailable)?
            .try_send(bytes)
            .map_err(|_| Error::Busy)
    }
    fn call(
        &mut self,
        op: &str,
        generation: Option<&Generation>,
        cancel: impl Fn() -> bool,
    ) -> Result<GenerationResult, Error> {
        self.last_metrics = None;
        if self.status == Status::Failed {
            return Err(Error::WorkerUnavailable);
        }
        self.next_id = self.next_id.checked_add(1).ok_or(Error::Protocol)?;
        let id = self.next_id;
        let mut value = json!({"version":1,"id":id,"op":op});
        if let Some(g) = generation {
            value["generation"] = json!({"role":g.role,"prompt":g.prompt,"schema":g.schema,"max_tokens":g.max_tokens});
        }
        self.send(value)?;
        let started = Instant::now();
        let mut cancelled = None;
        loop {
            if cancelled.is_none() && (cancel() || started.elapsed() >= self.deadline) {
                cancelled = Some((
                    Instant::now(),
                    if cancel() {
                        Error::Cancelled
                    } else {
                        Error::Timeout
                    },
                ));
                if self
                    .send(json!({"version":1,"id":id,"op":"cancel"}))
                    .is_err()
                {
                    return self.fail(Error::Cleanup);
                }
            }
            if cancelled.is_some_and(|(time, _)| time.elapsed() > Duration::from_secs(2)) {
                return self.fail(Error::Cleanup);
            }
            match self.replies.recv_timeout(Duration::from_millis(10)) {
                Ok(Ok(frame)) => {
                    let reply = match parse_reply(&frame, id) {
                        Ok(r) => r,
                        Err(e) => return self.fail(e),
                    };
                    self.last_metrics = Some(reply.metrics.clone());
                    if let Some((_, reason)) = cancelled {
                        return Err(reason);
                    }
                    if cancel() {
                        return Err(Error::Cancelled);
                    }
                    if reply.status == "error" {
                        return Err(match reply.error.as_deref() {
                            Some("cancelled") => Error::Cancelled,
                            Some("busy") => Error::Busy,
                            Some(
                                "model_invalid" | "model_load_failed" | "unsupported_template",
                            ) => Error::ModelInvalid,
                            Some("invalid_request" | "context_limit" | "output_limit") => {
                                Error::InvalidRequest
                            }
                            _ => Error::Runtime,
                        });
                    }
                    return Ok(GenerationResult {
                        text: reply.text,
                        metrics: reply.metrics,
                    });
                }
                Ok(Err(e)) => return self.fail(e),
                Err(mpsc::RecvTimeoutError::Disconnected) => return self.fail(Error::Protocol),
                Err(mpsc::RecvTimeoutError::Timeout) => {}
            }
            if self.fault.load(Ordering::SeqCst) {
                return self.fail(Error::Protocol);
            }
        }
    }
    fn fail<T>(&mut self, error: Error) -> Result<T, Error> {
        self.status = Status::Failed;
        let _ = self.child.kill();
        self.child.wait().map_err(|_| Error::Cleanup)?;
        Err(error)
    }
    pub fn load(&mut self, cancel: impl Fn() -> bool) -> Result<Metrics, Error> {
        let result = self.call("load", None, cancel);
        // A cancelled load may have completed just before cancellation. Explicit unload is
        // required before claiming a clean unloaded state; discard the owner on uncertainty.
        match result {
            Ok(r) => {
                self.status = Status::Loaded;
                Ok(r.metrics)
            }
            Err(e) => {
                let _ = self.fail::<()>(e);
                Err(e)
            }
        }
    }
    pub fn generate(
        &mut self,
        generation: Generation,
        cancel: impl Fn() -> bool,
    ) -> Result<GenerationResult, Error> {
        self.last_metrics = None;
        if self.status != Status::Loaded {
            return Err(Error::WorkerUnavailable);
        }
        if generation.prompt.is_empty()
            || generation.prompt.contains('\0')
            || generation.max_tokens == 0
            || generation.max_tokens > 350
        {
            return Err(Error::InvalidRequest);
        }
        if generation.schema.as_ref().is_some_and(|s| !s.is_object()) {
            return Err(Error::InvalidRequest);
        }
        self.call("generate", Some(&generation), cancel)
    }
    pub fn unload(&mut self) -> Result<(), Error> {
        self.call("unload", None, || false)?;
        self.status = Status::Unloaded;
        Ok(())
    }
    pub fn shutdown(&mut self) -> Result<(), Error> {
        self.call("shutdown", None, || false)?;
        let started = Instant::now();
        while self.child.try_wait().map_err(|_| Error::Cleanup)?.is_none() {
            if started.elapsed() > Duration::from_secs(2) {
                return self.fail(Error::Cleanup);
            }
            thread::sleep(Duration::from_millis(10));
        }
        self.status = Status::Failed;
        Ok(())
    }
}
impl Drop for LocalRuntime {
    fn drop(&mut self) {
        // Closing stdin alone cannot bound an unresponsive worker. Kill/reap exactly this child.
        self.writer.take();
        let _ = self.child.kill();
        let _ = self.child.wait();
        for thread in self.threads.drain(..) {
            let _ = thread.join();
        }
    }
}
fn parse_reply(frame: &[u8], id: u64) -> Result<Reply, Error> {
    let reply: Reply = serde_json::from_slice(frame).map_err(|_| Error::Protocol)?;
    if reply.version != 1
        || reply.id != id
        || !["completed", "error"].contains(&reply.status.as_str())
        || reply.text.len() > 16_384
        || reply.text.contains("<think>")
        || reply.text.contains("</think>")
    {
        return Err(Error::Protocol);
    }
    if (reply.status == "completed") != reply.error.is_none()
        || (reply.status == "error" && !reply.text.is_empty())
    {
        return Err(Error::Protocol);
    }
    let m = &reply.metrics;
    if [m.load_ms, m.prefill_ms, m.decode_ms, m.total_ms]
        .iter()
        .any(|n| !n.is_finite() || *n < 0.0)
        || m.input_tokens > 4096
        || m.output_tokens > 350
    {
        return Err(Error::Protocol);
    }
    Ok(reply)
}

#[cfg(all(test, feature = "development-worker"))]
mod tests {
    use super::*;
    use std::sync::atomic::AtomicU64;
    static SEQUENCE: AtomicU64 = AtomicU64::new(0);
    fn resources() -> std::path::PathBuf {
        let dir = std::env::temp_dir().join(format!(
            "locallore-runtime-resource-{}-{}",
            std::process::id(),
            SEQUENCE.fetch_add(1, Ordering::Relaxed)
        ));
        std::fs::create_dir(&dir).unwrap();
        dir
    }
    #[test]
    fn hashing_cancels_between_chunks_without_finishing_or_starting_child() {
        use std::{cell::Cell, io::Seek};
        let dir = resources();
        let path = dir.join("synthetic hash input");
        std::fs::write(&path, vec![0u8; 131_072]).unwrap();
        let mut file = File::open(&path).unwrap();
        let checks = Cell::new(0);
        let result = hash_file(&mut file, Error::ModelInvalid, &|| {
            let count = checks.get() + 1;
            checks.set(count);
            count >= 2
        });
        assert_eq!(result, Err(Error::Cancelled));
        assert_eq!(file.stream_position().unwrap(), 65_536);
        assert_eq!(
            LocalRuntime::spawn_packaged_cancelled(&dir, &dir.join("missing model"), || true).err(),
            Some(Error::Cancelled)
        );
        assert_eq!(
            LocalRuntime::start_cancelled(&dir.join("missing worker"), &path, file, &|| true).err(),
            Some(Error::Cancelled)
        );
        std::fs::remove_dir_all(dir).unwrap();
    }
    #[test]
    fn invalid_and_unavailable_operations_clear_previous_metrics() {
        let (mut owner, dir) = fixture("valid");
        owner.load(|| false).unwrap();
        assert!(owner.last_metrics().is_some());
        assert_eq!(
            owner
                .generate(
                    Generation {
                        role: Role::Director,
                        prompt: "fixture".into(),
                        schema: None,
                        max_tokens: 0
                    },
                    || false
                )
                .err(),
            Some(Error::InvalidRequest)
        );
        assert!(owner.last_metrics().is_none());
        owner.unload().unwrap();
        assert!(owner.last_metrics().is_some());
        assert_eq!(
            owner
                .generate(
                    Generation {
                        role: Role::Director,
                        prompt: "fixture".into(),
                        schema: None,
                        max_tokens: 16
                    },
                    || false
                )
                .err(),
            Some(Error::WorkerUnavailable)
        );
        assert!(owner.last_metrics().is_none());
        drop(owner);
        std::fs::remove_dir_all(dir).unwrap();
    }
    #[test]
    fn profile_manifest_digest_is_canonical_and_matches_independent_vector() {
        // Independent Python json(sort_keys=True,separators=(',',':')) SHA-256 vector.
        assert_eq!(
            profile_manifest_sha256(),
            "01ad542001b04a96f4a8ed6c841be1866eb025350836e0c5d0a4969fdb361d38"
        );
        let one: Value = serde_json::from_str(r#"{"b":[{"z":1,"a":2}],"a":true}"#).unwrap();
        let two: Value = serde_json::from_str(r#"{"a":true,"b":[{"a":2,"z":1}]}"#).unwrap();
        assert_eq!(
            serde_json::to_vec(&canonical_json(&one)).unwrap(),
            serde_json::to_vec(&canonical_json(&two)).unwrap()
        );
    }
    #[test]
    fn ancestor_order_is_root_to_leaf_even_with_spaces_and_unicode() {
        let path = std::path::absolute(
            std::env::temp_dir()
                .join("worker resources Δ")
                .join("nested")
                .join("worker.exe"),
        )
        .unwrap();
        let paths = ancestor_paths(&path).unwrap();
        assert!(paths.first().unwrap().parent().is_none());
        assert_eq!(paths.last().unwrap(), path.parent().unwrap());
        for pair in paths.windows(2) {
            assert_eq!(pair[1].parent().unwrap(), pair[0]);
        }
    }
    #[test]
    fn pinned_resource_hash_uses_locked_handle_and_missing_paths_reject() {
        let dir = resources();
        let nested = dir.join("worker resources Δ");
        std::fs::create_dir(&nested).unwrap();
        let path = nested.join("synthetic worker.exe");
        std::fs::write(&path, b"abc").unwrap();
        let mut pinned = pin_file(&path, Error::WorkerUnavailable).unwrap();
        assert_eq!(
            hash_file(&mut pinned.file, Error::WorkerUnavailable, &|| false).unwrap(),
            "ba7816bf8f01cfea414140de5dae2223b00361a396177a9cb410ff61f20015ad"
        );
        assert!(pin_file(&nested.join("missing.exe"), Error::WorkerUnavailable).is_err());
        assert!(pin_file(&nested, Error::WorkerUnavailable).is_err());
        #[cfg(windows)]
        {
            assert!(OpenOptions::new().write(true).open(&path).is_err());
            assert!(std::fs::remove_file(&path).is_err());
            assert!(std::fs::rename(&nested, dir.join("replaced")).is_err());
        }
        drop(pinned);
        assert!(OpenOptions::new().write(true).open(&path).is_ok());
        std::fs::remove_dir_all(&dir).unwrap();
    }
    #[cfg(windows)]
    #[test]
    #[ignore = "requires Windows symlink privilege; run explicitly when available"]
    fn model_and_worker_reparse_paths_reject() {
        let dir = resources();
        let real = dir.join("actual");
        std::fs::create_dir(&real).unwrap();
        let file = real.join("file.exe");
        std::fs::write(&file, b"abc").unwrap();
        let leaf = dir.join("worker-link.exe");
        std::os::windows::fs::symlink_file(&file, &leaf).unwrap();
        let ancestor = dir.join("directory-link");
        std::os::windows::fs::symlink_dir(&real, &ancestor).unwrap();
        for category in [Error::WorkerUnavailable, Error::ModelInvalid] {
            assert_eq!(pin_file(&leaf, category).err().unwrap(), category);
            assert_eq!(
                pin_file(&ancestor.join("file.exe"), category)
                    .err()
                    .unwrap(),
                category
            );
        }
        std::fs::remove_file(leaf).unwrap();
        std::fs::remove_dir(ancestor).unwrap();
        std::fs::remove_dir_all(dir).unwrap();
    }
    pub(super) fn fixture(mode: &str) -> (LocalRuntime, std::path::PathBuf) {
        let dir = std::env::temp_dir().join(format!(
            "locallore-runtime-{}-{}",
            std::process::id(),
            SEQUENCE.fetch_add(1, Ordering::Relaxed)
        ));
        std::fs::create_dir(&dir).unwrap();
        let path = dir.join(mode);
        let file = File::create(&path).unwrap();
        let mut exe = std::env::current_exe().unwrap();
        exe.pop();
        exe.pop();
        exe.push(if cfg!(windows) {
            "protocol-fixture.exe"
        } else {
            "protocol-fixture"
        });
        let owner = LocalRuntime::start(&exe, &path, file).unwrap();
        (owner, dir)
    }
    #[test]
    fn hostile_frames_fail_closed() {
        for mode in [
            "die",
            "overflow",
            "stderr",
            "wrong-id",
            "duplicate",
            "truncated",
        ] {
            let (mut owner, dir) = fixture(mode);
            assert_eq!(owner.load(|| false), Err(Error::Protocol), "{mode}");
            assert_eq!(owner.status(), Status::Failed);
            assert!(owner.child.try_wait().unwrap().is_some());
            drop(owner);
            std::fs::remove_dir_all(dir).unwrap();
        }
    }
    #[test]
    fn unresponsive_worker_is_reaped_after_cancel_deadline() {
        for mode in ["hang", "no-read"] {
            let (mut owner, dir) = fixture(mode);
            let start = Instant::now();
            assert_eq!(
                owner.load(|| start.elapsed() > Duration::from_millis(20)),
                Err(Error::Cleanup)
            );
            assert!(start.elapsed() < Duration::from_secs(5));
            assert!(owner.child.try_wait().unwrap().is_some());
            drop(owner);
            std::fs::remove_dir_all(dir).unwrap();
        }
    }
    #[test]
    fn invalid_artifact_never_launches_worker() {
        let path = std::env::temp_dir().join(format!("locallore-model-{}", std::process::id()));
        std::fs::write(&path, b"not a model").unwrap();
        assert_eq!(
            LocalRuntime::spawn_cancelled(Path::new("missing-worker"), &path, &|| false).err(),
            Some(Error::ModelInvalid)
        );
        std::fs::remove_file(path).unwrap();
    }
    #[test]
    fn blocked_stdin_writer_is_released_by_owned_child_reap() {
        let (mut owner, dir) = fixture("blocked-generation");
        owner.load(|| false).unwrap();
        let start = Instant::now();
        let result = owner.generate(
            Generation {
                role: Role::Director,
                prompt: "x".repeat(30_000),
                schema: None,
                max_tokens: 16,
            },
            || start.elapsed() > Duration::from_millis(20),
        );
        assert_eq!(result.err(), Some(Error::Cleanup));
        drop(owner);
        assert!(start.elapsed() < Duration::from_secs(5));
        std::fs::remove_dir_all(dir).unwrap();
    }
    #[test]
    fn deadline_requests_cancel_and_reaps_unresponsive_process() {
        let (mut owner, dir) = fixture("hang");
        owner.deadline = Duration::from_millis(20);
        let start = Instant::now();
        assert_eq!(owner.load(|| false).err(), Some(Error::Cleanup));
        assert!(start.elapsed() < Duration::from_secs(5));
        drop(owner);
        std::fs::remove_dir_all(dir).unwrap();
    }
    #[test]
    fn valid_reply_and_lifecycle() {
        let (mut owner, dir) = fixture("valid");
        owner.load(|| false).unwrap();
        assert_eq!(owner.status(), Status::Loaded);
        let result = owner.generate(
            Generation {
                role: Role::Director,
                prompt: "original synthetic fixture".into(),
                schema: None,
                max_tokens: 16,
            },
            || false,
        );
        assert!(result.is_ok());
        owner.unload().unwrap();
        assert_eq!(owner.status(), Status::Unloaded);
        drop(owner);
        std::fs::remove_dir_all(dir).unwrap();
    }
    #[test]
    fn reply_identity_bounds_and_channels() {
        let base = json!({"version":1,"id":1,"status":"completed","error":null,"text":"ok","metrics":{"load_ms":0,"prefill_ms":0,"decode_ms":0,"total_ms":0,"input_tokens":1,"output_tokens":1,"model_loads":1,"contexts_created":1,"abort_callbacks":0}});
        assert!(parse_reply(&serde_json::to_vec(&base).unwrap(), 1).is_ok());
        for (key, value) in [
            ("id", json!(2)),
            ("version", json!(2)),
            ("text", json!("<think>private</think>")),
            ("error", json!("unexpected")),
            ("status", json!("pending")),
            ("text", json!("x".repeat(16_385))),
        ] {
            let mut changed = base.clone();
            changed[key] = value;
            assert!(parse_reply(&serde_json::to_vec(&changed).unwrap(), 1).is_err());
        }
        for key in ["input_tokens", "output_tokens"] {
            let mut changed = base.clone();
            changed["metrics"][key] = json!(10000);
            assert!(parse_reply(&serde_json::to_vec(&changed).unwrap(), 1).is_err());
        }
    }
}
