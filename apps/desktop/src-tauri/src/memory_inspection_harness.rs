//! Fixed synthetic read gate; declared only by the development harness.
//! No packet builder, source mutation, provider, job or caller-supplied path.
use crate::WindowLease;
use serde_json::{Value, json};
use std::{
    path::{Component, Path, PathBuf},
    sync::atomic::{AtomicU8, Ordering},
    time::{Duration, Instant},
};

// 0 idle, 1 armed, 2 an actual ReadPermit-held read has entered.
static GATE: AtomicU8 = AtomicU8::new(0);

pub fn active() -> bool {
    crate::memory_harness::active()
        && std::env::var("LOCALLORE_D05_MEMORY_INSPECTION_HARNESS").as_deref() == Ok("1")
}

fn workspace_path() -> Result<PathBuf, String> {
    if !active() {
        return Err("Forbidden".into());
    }
    let path = std::env::var_os("LOCALLORE_TEST_WORKSPACE")
        .map(PathBuf::from)
        .ok_or("SyntheticWorkspaceRequired")?;
    let parent = path.parent().ok_or("SyntheticWorkspaceRequired")?;
    let suffix = parent
        .file_name()
        .and_then(|name| name.to_str())
        .and_then(|name| name.strip_prefix("memory-native-"))
        .ok_or("SyntheticWorkspaceRequired")?;
    if !path.is_absolute()
        || path.components().any(|part| matches!(part, Component::CurDir | Component::ParentDir))
        || path.file_name().and_then(|name| name.to_str()) != Some("stories-v1.sqlite")
        || !crate::archive::valid_id(suffix)
        || suffix != suffix.to_ascii_lowercase()
    {
        return Err("SyntheticWorkspaceRequired".into());
    }
    Ok(path)
}

fn state() -> Value {
    let gate = GATE.load(Ordering::SeqCst);
    json!({"version":1,"kind":"memory_inspection_fixture","synthetic":true,
        "held":gate != 0,"entered":gate == 2})
}

pub fn case(path: &Path, action: &str) -> Result<Value, String> {
    let expected = workspace_path()?;
    if path != expected.as_path() {
        return Err("SyntheticWorkspaceRequired".into());
    }
    // The same reviewed ordinary-ancestor handles used by native exports.
    // Keep them alive through every flag read/write and its acknowledgement.
    let _pins = crate::archive::pin(expected.parent().ok_or("SyntheticWorkspaceRequired")?)?;
    match action {
        "hold-read" => {
            GATE.compare_exchange(0, 1, Ordering::SeqCst, Ordering::SeqCst)
                .map_err(|_| "Busy".to_owned())?;
        }
        "release-read" => GATE.store(0, Ordering::SeqCst),
        "read-state" => {},
        _ => return Err("InvalidMemoryFixture".into()),
    }
    Ok(state())
}

struct Entered;
impl Drop for Entered {
    fn drop(&mut self) {
        // A release/re-arm belongs to its next read. This guard may only clear
        // its still-entered state; the real read slot prevents a second reader.
        let _ = GATE.compare_exchange(2, 0, Ordering::SeqCst, Ordering::SeqCst);
    }
}

pub fn before_read(lease: &WindowLease, epoch: u64) -> Result<(), String> {
    if !active() {
        return Ok(());
    }
    let path = workspace_path()?;
    let _pins = crate::archive::pin(path.parent().ok_or("SyntheticWorkspaceRequired")?)?;
    if !lease.valid(epoch) {
        return Err("Closed".into());
    }
    if GATE.compare_exchange(1, 2, Ordering::SeqCst, Ordering::SeqCst).is_err() {
        return Ok(());
    }
    let _entered = Entered;
    let started = Instant::now();
    loop {
        if !lease.valid(epoch) {
            return Err("Closed".into());
        }
        if GATE.load(Ordering::SeqCst) != 2 {
            return Ok(());
        }
        if started.elapsed() >= Duration::from_secs(10) {
            return Err("MemoryInspectionHarnessDeadline".into());
        }
        std::thread::sleep(Duration::from_millis(10));
    }
}
