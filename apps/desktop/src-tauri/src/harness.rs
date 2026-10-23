//! Application-owned synthetic development evidence. This module is compiled only
//! with `dev-harness`; main must register its commands only under that same cfg.

use serde_json::{json, Value};
use std::{
    collections::HashSet,
    fs::{self, OpenOptions},
    io::Write,
    path::PathBuf,
    sync::Mutex,
};

const MAX_JSON: usize = 256 * 1024;
const MAX_PNG: usize = 16 * 1024 * 1024;
const MAX_CHECKPOINTS: usize = 40;
const LABELS: &[&str] = &[
    "durable-storage-error",
    "durable-initial",
    "durable-accepted",
    "durable-reopened",
    "durable-resumed",
    "durable-new",
    "durable-cancelled",
    "durable-stale",
    "durable-retry",
    "durable-disposed",
    "initial",
    "play-accepted",
    "play-rejected",
    "pending",
    "cancelled",
    "retry",
    "failed",
    "malformed",
    "stale",
    "session-switch",
    "receipt",
    "observer",
    "play-return",
    "narrow",
    "enlarged",
    "reopened",
    "finished",
    "close",
    "copy",
    "pagination",
    "injection",
    "disposed",
];

pub fn active() -> bool {
    std::env::var("LOCALLORE_D02_HARNESS").as_deref() == Ok("1")
}

struct Progress {
    labels: HashSet<String>,
    finished: bool,
}

pub struct HarnessState {
    directory: PathBuf,
    progress: Mutex<Progress>,
}

impl HarnessState {
    /// The launcher chooses a NEW leaf under its ignored artifact directory.
    /// Never reuse or traverse a frontend-provided path. Existing leaves fail.
    pub fn from_env() -> Result<Self, &'static str> {
        if !active() {
            return Err("Forbidden");
        }
        let directory = std::env::var_os("LOCALLORE_D02_ARTIFACT_DIR")
            .map(PathBuf::from)
            .ok_or("ArtifactDirectoryMissing")?;
        Self::create(directory)
    }

    fn create(directory: PathBuf) -> Result<Self, &'static str> {
        if !directory.is_absolute() {
            return Err("ArtifactDirectoryInvalid");
        }
        // create_dir refuses an existing directory, symlink or file. A local
        // launcher controls the parent; the app never accepts paths over IPC.
        fs::create_dir(&directory).map_err(|_| "ArtifactDirectoryUnavailable")?;
        Ok(Self {
            directory,
            progress: Mutex::new(Progress {
                labels: HashSet::new(),
                finished: false,
            }),
        })
    }

    fn authorize(&self, window: &tauri::WebviewWindow) -> Result<(), &'static str> {
        if !active() || window.label() != "main" {
            return Err("Forbidden");
        }
        Ok(())
    }

    fn reserve(&self, label: &str) -> Result<(), &'static str> {
        if !LABELS.contains(&label) {
            return Err("CheckpointInvalid");
        }
        let mut progress = self.progress.lock().map_err(|_| "HarnessUnavailable")?;
        if progress.finished || progress.labels.len() >= MAX_CHECKPOINTS {
            return Err("CheckpointLimit");
        }
        if !progress.labels.insert(label.into()) {
            return Err("CheckpointDuplicate");
        }
        Ok(())
    }

    fn write(&self, name: &str, bytes: &[u8]) -> Result<(), &'static str> {
        // Every caller passes a literal or a name formed from LABELS above.
        OpenOptions::new()
            .write(true)
            .create_new(true)
            .open(self.directory.join(name))
            .and_then(|mut file| file.write_all(bytes))
            .map_err(|_| "ArtifactWriteFailed")
    }
}

fn checked_json(value: &Value, snapshot: bool) -> Result<Vec<u8>, &'static str> {
    if value.get("synthetic") != Some(&Value::Bool(true)) {
        return Err("SyntheticFixtureRequired");
    }
    if snapshot && value.get("uiRevision").and_then(Value::as_u64).is_none() {
        return Err("RevisionRequired");
    }
    let bytes = serde_json::to_vec_pretty(value).map_err(|_| "ArtifactInvalid")?;
    if bytes.len() > MAX_JSON {
        return Err("ArtifactTooLarge");
    }
    Ok(bytes)
}

#[tauri::command]
pub async fn harness_checkpoint(
    window: tauri::WebviewWindow,
    state: tauri::State<'_, HarnessState>,
    label: String,
    snapshot: Value,
) -> Result<Value, &'static str> {
    state.authorize(&window)?;
    let bytes = checked_json(&snapshot, true)?;
    state.reserve(&label)?;
    state.write(&format!("{label}.json"), &bytes)?;
    let capture = capture(&window).await;
    let rendering = match capture {
        Ok(bytes) => {
            state.write(&format!("{label}.png"), &bytes)?;
            "native-webview2"
        }
        Err(category) => category,
    };
    let result = json!({
        "label": label, "uiRevision": snapshot["uiRevision"],
        "rendering": rendering, "synthetic": true,
    });
    state.write(
        &format!("{label}.capture.json"),
        &serde_json::to_vec_pretty(&result).map_err(|_| "ArtifactInvalid")?,
    )?;
    Ok(result)
}

/// Resize only this application's own test WebView. No activation or input.
#[tauri::command]
pub fn harness_viewport(
    window: tauri::WebviewWindow,
    state: tauri::State<'_, HarnessState>,
    preset: String,
) -> Result<(), &'static str> {
    state.authorize(&window)?;
    let (width, height) = match preset.as_str() {
        "wide" => (1280.0, 900.0),
        "narrow" => (680.0, 900.0),
        _ => return Err("ViewportInvalid"),
    };
    window
        .set_size(tauri::LogicalSize::new(width, height))
        .map_err(|_| "ViewportUnavailable")
}

#[tauri::command]
pub fn harness_finish(
    window: tauri::WebviewWindow,
    state: tauri::State<'_, HarnessState>,
    app: tauri::AppHandle,
    report: Value,
) -> Result<(), &'static str> {
    state.authorize(&window)?;
    let bytes = checked_json(&report, false)?;
    let pass = report
        .get("passed")
        .and_then(Value::as_bool)
        .ok_or("ReportInvalid")?;
    {
        let mut progress = state.progress.lock().map_err(|_| "HarnessUnavailable")?;
        if progress.finished {
            return Err("HarnessFinished");
        }
        progress.finished = true;
    }
    state.write("report.json", &bytes)?;
    println!("D02_NATIVE_HARNESS {}", if pass { "PASS" } else { "FAIL" });
    app.exit(if pass { 0 } else { 1 });
    Ok(())
}

#[cfg(windows)]
async fn capture(window: &tauri::WebviewWindow) -> Result<Vec<u8>, &'static str> {
    use webview2_com::{
        CapturePreviewCompletedHandler,
        Microsoft::Web::WebView2::Win32::COREWEBVIEW2_CAPTURE_PREVIEW_IMAGE_FORMAT_PNG,
    };
    use windows::Win32::{
        System::Com::{STATFLAG_NONAME, STATSTG, STREAM_SEEK_SET},
        UI::Shell::SHCreateMemStream,
    };

    let (sender, receiver) = tokio::sync::oneshot::channel();
    window
        .with_webview(move |webview| {
            // Native WebView2 rendering only. No screen/window APIs, desktop
            // handles, DevTools protocol, script evaluation or filesystem COM.
            let setup = (|| unsafe {
                let stream = SHCreateMemStream(None).ok_or("CaptureUnavailable")?;
                let view = webview
                    .controller()
                    .CoreWebView2()
                    .map_err(|_| "CaptureUnavailable")?;
                Ok::<_, &'static str>((stream, view))
            })();
            let (stream, view) = match setup {
                Ok(value) => value,
                Err(category) => {
                    let _ = sender.send(Err(category));
                    return;
                }
            };
            // The callback retains the stream until WebView2 has completed.
            let completed_stream = stream.clone();
            let callback = CapturePreviewCompletedHandler::create(Box::new(move |status| {
                let result = (|| unsafe {
                    status.map_err(|_| "CaptureFailed")?;
                    let mut stat = STATSTG::default();
                    completed_stream
                        .Stat(&mut stat, STATFLAG_NONAME)
                        .map_err(|_| "CaptureFailed")?;
                    let length = usize::try_from(stat.cbSize).map_err(|_| "CaptureTooLarge")?;
                    if length > MAX_PNG {
                        return Err("CaptureTooLarge");
                    }
                    let mut bytes = vec![0; length];
                    completed_stream
                        .Seek(0, STREAM_SEEK_SET, None)
                        .map_err(|_| "CaptureFailed")?;
                    let mut read = 0;
                    completed_stream
                        .Read(bytes.as_mut_ptr().cast(), length as u32, Some(&mut read))
                        .ok()
                        .map_err(|_| "CaptureFailed")?;
                    if read as usize != length || !bytes.starts_with(b"\x89PNG\r\n\x1a\n") {
                        return Err("CaptureInvalid");
                    }
                    Ok(bytes)
                })();
                let _ = sender.send(result);
                Ok(())
            }));
            // Immediate failure drops the callback sender; receiver maps that
            // case to a stable category rather than reporting an OS message.
            let _ = unsafe {
                view.CapturePreview(
                    COREWEBVIEW2_CAPTURE_PREVIEW_IMAGE_FORMAT_PNG,
                    &stream,
                    &callback,
                )
            };
        })
        .map_err(|_| "CaptureUnavailable")?;
    tokio::time::timeout(std::time::Duration::from_secs(10), receiver)
        .await
        .map_err(|_| "CaptureTimeout")?
        .map_err(|_| "CaptureUnavailable")?
}

#[cfg(not(windows))]
async fn capture(_: &tauri::WebviewWindow) -> Result<Vec<u8>, &'static str> {
    Err("CaptureUnsupported")
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn artifacts_require_synthetic_revision_and_are_bounded() {
        assert_eq!(
            checked_json(&json!({}), true),
            Err("SyntheticFixtureRequired")
        );
        assert_eq!(
            checked_json(&json!({"synthetic":true}), true),
            Err("RevisionRequired")
        );
        assert!(checked_json(&json!({"synthetic":true,"uiRevision":1}), true).is_ok());
        assert_eq!(
            checked_json(
                &json!({"synthetic":true,"uiRevision":1,"text":"x".repeat(MAX_JSON)}),
                true
            ),
            Err("ArtifactTooLarge")
        );
    }

    #[test]
    fn artifact_directory_is_new_and_names_are_allowlisted() {
        let directory = std::env::temp_dir().join(format!(
            "locallore-d02-unit-{}-{}",
            std::process::id(),
            std::time::SystemTime::now()
                .duration_since(std::time::UNIX_EPOCH)
                .unwrap()
                .as_nanos()
        ));
        let state = HarnessState::create(directory.clone()).unwrap();
        assert!(matches!(
            HarnessState::create(directory.clone()),
            Err("ArtifactDirectoryUnavailable")
        ));
        assert_eq!(state.reserve("../escape"), Err("CheckpointInvalid"));
        state.reserve("initial").unwrap();
        assert_eq!(state.reserve("initial"), Err("CheckpointDuplicate"));
        state.write("initial.json", b"{}").unwrap();
        assert_eq!(
            state.write("initial.json", b"changed"),
            Err("ArtifactWriteFailed")
        );
        fs::remove_file(directory.join("initial.json")).unwrap();
        fs::remove_dir(directory).unwrap();
    }
}
