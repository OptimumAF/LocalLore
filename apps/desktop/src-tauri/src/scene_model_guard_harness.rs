//! Closed synthetic guard-only cohort. No approved model, runtime or caller path.
//! Root must register this module/command only with dev-harness; author UNRUN.
use crate::{comparison_run_native_harness as native, models::ModelManager, WorkspaceState};
use serde_json::{json, Value};
use sha2::{Digest, Sha256};
use std::{
    collections::BTreeMap,
    fs::{self, File},
    path::{Component, Path, PathBuf},
};

const PUBLIC: &[u8] = b"synthetic-publication-staging-sentinel";
const CONTROL: &[u8] = b"synthetic-control-staging-sentinel";
struct Paths {
    publication: PathBuf,
    control: PathBuf,
    name: String,
    _pins: Vec<File>,
}
fn paths(workspace: &Path) -> Result<Paths, String> {
    if std::env::var("LOCALLORE_D07_SCENE_MODEL_GUARD_HARNESS").as_deref() != Ok("1")
        || !native::scene_active()
        || workspace.file_name().and_then(|v| v.to_str()) != Some("stories-v1.sqlite")
        || !workspace.is_absolute()
        || workspace
            .components()
            .any(|p| matches!(p, Component::ParentDir | Component::CurDir))
    {
        return Err("Forbidden".into());
    }
    let parent = workspace.parent().ok_or("Forbidden")?;
    let id = parent
        .file_name()
        .and_then(|v| v.to_str())
        .and_then(|v| v.strip_prefix("full-comparison-native-"))
        .ok_or("Forbidden")?;
    if !crate::archive::valid_id(id) || id.bytes().any(|v| v.is_ascii_uppercase()) {
        return Err("Forbidden".into());
    }
    let outer = parent.parent().ok_or("Forbidden")?;
    if outer.file_name().and_then(|v| v.to_str())
        != Some(format!("scene-model-guards-{id}").as_str())
    {
        return Err("Forbidden".into());
    }
    let publication = outer.join(format!("guard-modelpub-{id}"));
    let control = outer.join(format!("guard-modelcontrol-{id}"));
    let mut pins = crate::exports::pin_directory(parent)?;
    pins.extend(crate::exports::pin_directory(&publication)?);
    pins.extend(crate::exports::pin_directory(&control)?);
    if native::protocol()? != crate::evaluation::FullComparisonProtocol::SceneV4
        || native::model_root(workspace)? != publication
        || native::approved_model_source(workspace).err().as_deref() != Some("Forbidden")
    {
        return Err("Forbidden".into());
    }
    Ok(Paths {
        publication,
        control,
        name: format!(".import-{id}.part"),
        _pins: pins,
    })
}
fn inventory(root: &Path, name: &str) -> Result<BTreeMap<String, Value>, String> {
    let mut result = BTreeMap::new();
    for (count, entry) in fs::read_dir(root).map_err(|_| "GuardIo")?.enumerate() {
        if count >= 1 {
            return Err("GuardInventory".into());
        }
        let entry = entry.map_err(|_| "GuardIo")?;
        if entry.file_name() != name {
            return Err("GuardInventory".into());
        }
        let metadata = fs::symlink_metadata(entry.path()).map_err(|_| "GuardIo")?;
        #[cfg(windows)]
        {
            use std::os::windows::fs::MetadataExt;
            if metadata.file_attributes() & 0x400 != 0 {
                return Err("GuardPath".into());
            }
        }
        if !metadata.is_file() || metadata.file_type().is_symlink() || metadata.len() > 1024 {
            return Err("GuardInventory".into());
        }
        use std::io::Read;
        let mut bytes = Vec::new();
        File::open(entry.path())
            .map_err(|_| "GuardIo")?
            .take(1025)
            .read_to_end(&mut bytes)
            .map_err(|_| "GuardIo")?;
        if bytes.len() > 1024 {
            return Err("GuardInventory".into());
        }
        result.insert(
            name.into(),
            json!({"bytes":bytes.len(),"sha256":format!("{:x}",Sha256::digest(bytes))}),
        );
    }
    Ok(result)
}
fn require_sentinel(root: &Path, name: &str, bytes: &[u8]) -> Result<(), String> {
    let actual = inventory(root, name)?;
    let expected = BTreeMap::from([(
        name.to_owned(),
        json!({"bytes":bytes.len(),"sha256":format!("{:x}",Sha256::digest(bytes))}),
    )]);
    if actual != expected {
        return Err("GuardSentinel".into());
    }
    Ok(())
}
#[tauri::command]
pub async fn harness_scene_model_guards(
    window: tauri::WebviewWindow,
    workspace: tauri::State<'_, WorkspaceState>,
    case: String,
) -> Result<Value, String> {
    if !matches!(case.as_str(), "snapshot" | "counterfactual") {
        return Err("GuardCase".into());
    }
    let epoch = workspace
        .lease
        .capture(window.label())
        .map_err(str::to_owned)?;
    let lease = workspace.lease.clone();
    let workspace = workspace.path.clone();
    tauri::async_runtime::spawn_blocking(move || {
        lease.dispatch(epoch,||Ok(()))?;
        let paths=paths(&workspace)?;
        require_sentinel(&paths.publication,&paths.name,PUBLIC)?;
        let before=inventory(&paths.publication,&paths.name)?;
        let mut control_status=Value::Null;
        let mut picker_calls=0usize;
        if case=="counterfactual" {
            require_sentinel(&paths.control,&paths.name,CONTROL)?;
            let manager=ModelManager::new(paths.control.clone(),paths.control.join("no-runtime"));
            control_status=manager.import(&lease,epoch,||{
                picker_calls+=1;
                if paths.control.join(&paths.name).exists() {return Err("GuardReapNotObserved".into());}
                Ok(None)
            })?;
            // Import's internal Cancelled is represented by unloaded/error-null.
            if picker_calls!=1 || control_status["phase"]!="unloaded"
                || control_status["loaded"]!=false || control_status["resident"]!=false
                || !control_status["error"].is_null()
                || !inventory(&paths.control,&paths.name)?.is_empty()
            {return Err("GuardCounterfactual".into());}
        }
        let publication=inventory(&paths.publication,&paths.name)?;
        if publication!=before {return Err("GuardPublicationChanged".into());}
        lease.dispatch(epoch,||Ok(json!({"version":1,"kind":"scene_model_guard_fixture","synthetic":true,
            "protocol_version":4,"case":case,"publication":publication,"control":inventory(&paths.control,&paths.name)?,
            "picker_calls":picker_calls,"control_status":control_status,"models_executed":false,
            "runtime_started":false,"approved_basename_created":false})))
    }).await.map_err(|_|"GuardInternal".to_owned())?
}

#[cfg(all(test, windows))]
mod tests {
    use super::*;
    use std::{
        io::Read,
        process::{Command, Stdio},
        time::{Duration, Instant},
    };
    const CHILD: &str = "scene_model_guard_harness::tests::fixed_root_case_child";
    const CASES: &[&str] = &[
        "old-absent",
        "old-zero",
        "old-d04",
        "scene",
        "bad-scene",
        "missing-active",
        "mixed-d04",
        "workspace-mismatch",
        "missing-root",
        "relative-root",
        "dot-root",
        "nested-root",
        "case-alias",
        "short-alias",
    ];
    fn fixture() -> (PathBuf, PathBuf, PathBuf) {
        let id = crate::exports::identifier().unwrap();
        let outer = std::env::temp_dir().join(format!("scene-model-guards-{id}"));
        fs::create_dir(&outer).unwrap();
        let parent = outer.join(format!("full-comparison-native-{id}"));
        let publication = outer.join(format!("guard-modelpub-{id}"));
        fs::create_dir(&parent).unwrap();
        fs::create_dir(&publication).unwrap();
        fs::write(publication.join("sentinel.txt"), b"synthetic-path-only").unwrap();
        (outer, parent.join("stories-v1.sqlite"), publication)
    }
    #[test]
    fn root_protocol_matrix_uses_isolated_fixed_children_without_parent_environment_mutation() {
        use std::os::windows::process::CommandExt;
        for case in CASES {
            let (_outer, workspace, publication) = fixture();
            let mut command = Command::new(std::env::current_exe().unwrap());
            command.creation_flags(0x0800_0000);
            command.args(["--exact", CHILD, "--ignored", "--nocapture"]);
            for (key, _) in std::env::vars_os() {
                if key.to_string_lossy().starts_with("LOCALLORE_") {
                    command.env_remove(key);
                }
            }
            for key in [
                "LOCALLORE_D02_HARNESS",
                "LOCALLORE_TEST_MEMORY",
                "LOCALLORE_D07_FULL_COMPARISON_HARNESS",
                "LOCALLORE_D07_NATIVE_FULL_HARNESS",
                "LOCALLORE_D07_SCENE_NATIVE_FULL_HARNESS",
            ] {
                command.env(key, "1");
            }
            command
                .env("LOCALLORE_D04_HARNESS", "0")
                .env("LOCALLORE_TEST_WORKSPACE", &workspace)
                .env("LOCALLORE_D04_MODEL_ROOT", &publication)
                .env("LOCALLORE_SCENE_MODEL_GUARD_TEST_CASE", case)
                .stdout(Stdio::piped())
                .stderr(Stdio::piped());
            match *case {
                "old-absent" => {
                    command.env_remove("LOCALLORE_D07_SCENE_NATIVE_FULL_HARNESS");
                }
                "old-zero" => {
                    command.env("LOCALLORE_D07_SCENE_NATIVE_FULL_HARNESS", "0");
                }
                "old-d04" => {
                    command
                        .env("LOCALLORE_D07_SCENE_NATIVE_FULL_HARNESS", "0")
                        .env("LOCALLORE_D04_HARNESS", "1");
                }
                "bad-scene" => {
                    command.env("LOCALLORE_D07_SCENE_NATIVE_FULL_HARNESS", "invalid");
                }
                "missing-active" => {
                    command.env("LOCALLORE_D07_NATIVE_FULL_HARNESS", "0");
                }
                "mixed-d04" => {
                    command.env("LOCALLORE_D04_HARNESS", "1");
                }
                "workspace-mismatch" => {
                    command.env(
                        "LOCALLORE_TEST_WORKSPACE",
                        workspace.with_file_name("different.sqlite"),
                    );
                }
                "missing-root" => {
                    command.env_remove("LOCALLORE_D04_MODEL_ROOT");
                }
                "relative-root" => {
                    command.env("LOCALLORE_D04_MODEL_ROOT", "relative-publication");
                }
                "dot-root" => {
                    command.env(
                        "LOCALLORE_D04_MODEL_ROOT",
                        publication.join("..").join("other"),
                    );
                }
                "nested-root" | "case-alias" | "short-alias" => {
                    let nested = workspace.parent().unwrap().join("NestedModelPublication");
                    fs::create_dir(&nested).unwrap();
                    let path = if *case == "case-alias" {
                        PathBuf::from(nested.to_str().unwrap().to_ascii_uppercase())
                    } else if *case == "short-alias" {
                        short_path(&nested).unwrap_or_else(|| nested.clone())
                    } else {
                        nested
                    };
                    command.env("LOCALLORE_D04_MODEL_ROOT", path);
                }
                _ => {}
            }
            let mut child = command.spawn().unwrap();
            let mut stdout = child.stdout.take().unwrap();
            let mut stderr = child.stderr.take().unwrap();
            let out = std::thread::spawn(move || {
                let mut b = Vec::new();
                stdout.by_ref().take(65537).read_to_end(&mut b).unwrap();
                b
            });
            let err = std::thread::spawn(move || {
                let mut b = Vec::new();
                stderr.by_ref().take(65537).read_to_end(&mut b).unwrap();
                b
            });
            let deadline = Instant::now() + Duration::from_secs(30);
            let status = loop {
                if let Some(status) = child.try_wait().unwrap() {
                    break status;
                }
                if Instant::now() >= deadline {
                    let _ = child.kill();
                    let cleanup = Instant::now() + Duration::from_secs(5);
                    while Instant::now() < cleanup {
                        if child.try_wait().unwrap().is_some() {
                            break;
                        }
                        std::thread::sleep(Duration::from_millis(10));
                    }
                    panic!("fixed child timeout {case}; descendant drain unqualified, no later child admitted");
                }
                std::thread::sleep(Duration::from_millis(10));
            };
            let cleanup = Instant::now() + Duration::from_secs(5);
            while (!out.is_finished() || !err.is_finished()) && Instant::now() < cleanup {
                std::thread::sleep(Duration::from_millis(10));
            }
            assert!(
                out.is_finished() && err.is_finished(),
                "bounded owned child reader drain; no later child admitted"
            );
            let out = out.join().unwrap();
            let err = err.join().unwrap();
            assert!(
                out.len() <= 65536 && err.len() <= 65536,
                "fixed child output budget"
            );
            assert!(
                status.success(),
                "case {case}: {} {}",
                String::from_utf8_lossy(&out),
                String::from_utf8_lossy(&err)
            );
            println!("fixed-root-case:{case}:{}", String::from_utf8_lossy(&out));
        }
    }
    fn short_path(path: &Path) -> Option<PathBuf> {
        use std::os::windows::ffi::{OsStrExt, OsStringExt};
        #[link(name = "kernel32")]
        unsafe extern "system" {
            fn GetShortPathNameW(input: *const u16, output: *mut u16, size: u32) -> u32;
        }
        let input: Vec<u16> = path.as_os_str().encode_wide().chain(Some(0)).collect();
        let mut output = vec![0u16; 32768];
        let count =
            unsafe { GetShortPathNameW(input.as_ptr(), output.as_mut_ptr(), output.len() as u32) };
        if count == 0 || count as usize >= output.len() {
            None
        } else {
            Some(PathBuf::from(std::ffi::OsString::from_wide(
                &output[..count as usize],
            )))
        }
    }
    #[test]
    #[ignore = "fixed child only; parent supplies isolated synthetic environment"]
    fn fixed_root_case_child() {
        let case = std::env::var("LOCALLORE_SCENE_MODEL_GUARD_TEST_CASE").unwrap();
        assert!(CASES.contains(&case.as_str()));
        let mut workspace = PathBuf::from(std::env::var_os("LOCALLORE_TEST_WORKSPACE").unwrap());
        if case == "workspace-mismatch" {
            workspace.set_file_name("stories-v1.sqlite");
        }
        let parent = workspace.parent().unwrap();
        if matches!(case.as_str(), "old-absent" | "old-zero" | "old-d04") {
            assert!(matches!(
                native::protocol(),
                Ok(crate::evaluation::FullComparisonProtocol::LiteralV3)
            ));
            assert_eq!(
                native::model_root(&workspace).unwrap(),
                parent.join("model-native-v1")
            );
            assert!(!parent.join("model-native-v1").exists());
            assert_eq!(fs::read_dir(parent).unwrap().count(), 0);
            return;
        }
        if case == "scene" {
            assert!(matches!(
                native::protocol(),
                Ok(crate::evaluation::FullComparisonProtocol::SceneV4)
            ));
            let root = PathBuf::from(std::env::var_os("LOCALLORE_D04_MODEL_ROOT").unwrap());
            assert_eq!(native::model_root(&workspace).unwrap(), root);
            assert_eq!(
                fs::read(root.join("sentinel.txt")).unwrap(),
                b"synthetic-path-only"
            );
            assert_eq!(fs::read_dir(root).unwrap().count(), 1);
            assert_eq!(
                fs::read_dir(parent).unwrap().count(),
                0,
                "no model-root directory/copy created"
            );
            assert_eq!(
                native::approved_model_source(&workspace).unwrap_err(),
                "Forbidden"
            );
            return;
        }
        if matches!(case.as_str(), "bad-scene" | "missing-active" | "mixed-d04") {
            assert_eq!(native::protocol().err().as_deref(), Some("Forbidden"));
        }
        if case == "short-alias" {
            let root = PathBuf::from(std::env::var_os("LOCALLORE_D04_MODEL_ROOT").unwrap());
            if !root.to_string_lossy().contains('~') {
                println!("8.3-alias-unavailable:ordinary-nested-control-only");
            }
        }
        if matches!(case.as_str(), "case-alias" | "short-alias") {
            let root = PathBuf::from(std::env::var_os("LOCALLORE_D04_MODEL_ROOT").unwrap());
            assert!(
                root.is_dir(),
                "alias fixture must resolve, not pass by being missing"
            );
            assert_eq!(
                fs::canonicalize(&root).unwrap(),
                fs::canonicalize(parent.join("NestedModelPublication")).unwrap(),
                "actual ordinary alias is the owned nested directory"
            );
        }
        assert!(
            native::model_root(&workspace).is_err(),
            "actual root helper must refuse {case}"
        );
        assert_eq!(
            native::approved_model_source(&workspace).unwrap_err(),
            "Forbidden"
        );
    }
}
