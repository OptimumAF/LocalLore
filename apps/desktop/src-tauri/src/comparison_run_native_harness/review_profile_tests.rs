//! Independent SOURCE-ONLY retained-review gate freeze at 11d82d61.
//! Root owns helper implementation, module registration and actual execution.
//! Missing APIs are setup failures, not behavioral RED. Fixtures are retained.
#![cfg(windows)]

use super::{review_active, review_webview_profile};
use std::{
    collections::BTreeMap,
    fs,
    io::Read,
    os::windows::{fs::MetadataExt, process::CommandExt},
    path::{Component, Path, PathBuf, Prefix},
    process::{Command, Stdio},
    time::{Duration, Instant},
};

const CHILD: &str =
    "comparison_run_native_harness::review_profile_tests::fixed_review_profile_case_child";
const ROOT_ENV: &str = "LOCALLORE_RETAINED_REVIEW_PROFILE_TEST_ROOT";
const ARG_ENV: &str = "LOCALLORE_RETAINED_REVIEW_PROFILE_TEST_WORKSPACE_ARGUMENT";
const CASE_ENV: &str = "LOCALLORE_RETAINED_REVIEW_PROFILE_TEST_CASE";
const NEW_ENV: &str = "LOCALLORE_RETAINED_REVIEW_PROFILE_TEST_NEW_ROOT";
const CASES: &[&str] = &[
    "legacy-stage-absent",
    "legacy-stage-zero",
    "legacy-stage-one",
    "malformed-stage",
    "missing-d02",
    "missing-full",
    "missing-native",
    "missing-scene",
    "missing-memory",
    "mixed-d04",
    "missing-output",
    "relative-output",
    "wrong-drive-output-string",
    "wrong-output-leaf",
    "same-source-output-root",
    "output-nested-in-source",
    "case-alias-source-output-root",
    "source-nested-in-output",
    "existing-profile-directory",
    "existing-profile-file",
    "existing-source-database",
    "workspace-env-mismatch",
    "wrong-workspace-leaf",
    "safe-fresh-d-output",
];

#[derive(Debug, PartialEq, Eq)]
enum Entry {
    Directory,
    File(Vec<u8>),
}

fn physical_d_spelling(path: &Path) -> bool {
    path.is_absolute()
        && matches!(path.components().next(), Some(Component::Prefix(p))
            if matches!(p.kind(), Prefix::Disk(d) | Prefix::VerbatimDisk(d)
                if d.eq_ignore_ascii_case(&b'D')))
        && !path
            .components()
            .any(|part| matches!(part, Component::ParentDir | Component::CurDir))
}

// Complete tiny, quiescent fixture inventory: directories and actual file bytes,
// not mtime/size-only comparisons or selected sentinel files. No cleanup runs.
fn inventory(root: &Path) -> BTreeMap<PathBuf, Entry> {
    fn visit(root: &Path, path: &Path, depth: usize, result: &mut BTreeMap<PathBuf, Entry>) {
        assert!(depth <= 8 && result.len() < 128, "bounded fixture inventory");
        let metadata = fs::symlink_metadata(path).unwrap();
        assert_eq!(metadata.file_attributes() & 0x400, 0, "ordinary fixture only");
        let relative = path.strip_prefix(root).unwrap().to_owned();
        if metadata.is_dir() {
            assert!(result.insert(relative, Entry::Directory).is_none());
            let mut children: Vec<_> = fs::read_dir(path)
                .unwrap()
                .map(|entry| entry.unwrap().path())
                .collect();
            children.sort();
            for child in children {
                visit(root, &child, depth + 1, result);
            }
        } else {
            assert!(metadata.is_file() && metadata.len() <= 4096);
            assert!(result.insert(relative, Entry::File(fs::read(path).unwrap())).is_none());
        }
    }
    assert!(physical_d_spelling(root), "fixture commands stay on D:");
    let mut result = BTreeMap::new();
    visit(root, root, 0, &mut result);
    assert!(result.values().map(|entry| match entry {
        Entry::Directory => 0,
        Entry::File(bytes) => bytes.len(),
    }).sum::<usize>() <= 65536);
    result
}

struct Fixture {
    outer: PathBuf,
    workspace: PathBuf,
    new_root: PathBuf,
}
impl Fixture {
    fn new() -> Self {
        let temporary = std::env::temp_dir();
        assert!(physical_d_spelling(&temporary), "TEMP/TMP must select owned D: storage");
        for ancestor in temporary.ancestors() {
            let metadata = fs::symlink_metadata(ancestor).unwrap();
            assert!(metadata.is_dir(), "existing D: temporary ancestor");
            assert_eq!(metadata.file_attributes() & 0x400, 0, "no redirected temporary ancestor");
        }
        let old_id = crate::exports::identifier().unwrap();
        let new_id = crate::exports::identifier().unwrap();
        assert_ne!(old_id, new_id);
        let outer = temporary.join(format!("retained-review-profile-tests-{old_id}"));
        fs::create_dir(&outer).unwrap();
        let old_root = outer.join(format!("full-comparison-native-{old_id}"));
        let new_root = outer.join(format!("full-comparison-native-{new_id}"));
        fs::create_dir(&old_root).unwrap();
        fs::create_dir(&new_root).unwrap();
        fs::create_dir(old_root.join("retained-fixture")).unwrap();
        fs::write(old_root.join("retained-fixture/original.bin"), b"synthetic-retained-bytes").unwrap();
        fs::write(new_root.join("launcher-observation.txt"), b"synthetic-new-output").unwrap();
        Self { outer, workspace: old_root.join("stories-v1.sqlite"), new_root }
    }
}

// Preserve the valid lower-case UUID basename; only an ancestor's spelling
// changes. A refusal must not pass merely because the alias does not resolve.
fn case_alias(path: &Path) -> PathBuf {
    let alias = PathBuf::from(path.parent().unwrap().to_str().unwrap().to_ascii_uppercase())
        .join(path.file_name().unwrap());
    assert!(alias.is_dir());
    assert_eq!(fs::canonicalize(&alias).unwrap(), fs::canonicalize(path).unwrap());
    alias
}

#[test]
fn retained_review_profile_matrix_is_pure_and_child_environment_is_isolated() {
    for case in CASES {
        let fixture = Fixture::new();
        let old_root = fixture.workspace.parent().unwrap();
        let mut workspace = fixture.workspace.clone();
        let mut argument = workspace.clone();
        let mut output = fixture.new_root.join("review");
        let mut command = Command::new(std::env::current_exe().unwrap());
        command.creation_flags(0x0800_0000);
        command.args(["--exact", CHILD, "--ignored", "--nocapture", "--test-threads=1"]);
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
        command.env("LOCALLORE_D04_HARNESS", "0")
            .env("LOCALLORE_TEST_RESTART", "review")
            .env("TEMP", "D:/Dev/_Temp").env("TMP", "D:/Dev/_Temp");
        match *case {
            "legacy-stage-absent" => { command.env_remove("LOCALLORE_TEST_RESTART"); }
            "legacy-stage-zero" => { command.env("LOCALLORE_TEST_RESTART", "0"); }
            "legacy-stage-one" => { command.env("LOCALLORE_TEST_RESTART", "1"); }
            "malformed-stage" => { command.env("LOCALLORE_TEST_RESTART", "Review"); }
            "missing-d02" => { command.env_remove("LOCALLORE_D02_HARNESS"); }
            "missing-full" => { command.env_remove("LOCALLORE_D07_FULL_COMPARISON_HARNESS"); }
            "missing-native" => { command.env_remove("LOCALLORE_D07_NATIVE_FULL_HARNESS"); }
            "missing-scene" => { command.env_remove("LOCALLORE_D07_SCENE_NATIVE_FULL_HARNESS"); }
            "missing-memory" => { command.env_remove("LOCALLORE_TEST_MEMORY"); }
            "mixed-d04" => { command.env("LOCALLORE_D04_HARNESS", "1"); }
            "relative-output" => { output = PathBuf::from("relative-review-output/review"); }
            "wrong-drive-output-string" => {
                // String input only: fixture setup never creates/opens C: paths.
                output = PathBuf::from(format!(r"C:\locallore-string-only-{}\review",
                    crate::exports::identifier().unwrap()));
            }
            "wrong-output-leaf" => { output = fixture.new_root.join("initial"); }
            "same-source-output-root" => { output = old_root.join("review"); }
            "output-nested-in-source" => {
                let nested = old_root.join(fixture.new_root.file_name().unwrap());
                fs::create_dir(&nested).unwrap();
                output = nested.join("review");
            }
            "case-alias-source-output-root" => { output = case_alias(old_root).join("review"); }
            "source-nested-in-output" => {
                let nested = fixture.new_root.join(old_root.file_name().unwrap());
                fs::create_dir(&nested).unwrap();
                workspace = nested.join("stories-v1.sqlite");
                argument = workspace.clone();
            }
            "existing-profile-directory" => {
                fs::create_dir(fixture.new_root.join("webview-profile")).unwrap();
                fs::write(fixture.new_root.join("webview-profile/old-profile.bin"), b"retain-profile").unwrap();
            }
            "existing-profile-file" => {
                fs::write(fixture.new_root.join("webview-profile"), b"retain-file").unwrap();
            }
            "existing-source-database" => { fs::write(&workspace, b"synthetic-existing-file").unwrap(); }
            "workspace-env-mismatch" => { argument = old_root.join("different.sqlite"); }
            "wrong-workspace-leaf" => {
                workspace = old_root.join("different.sqlite");
                argument = workspace.clone();
            }
            "missing-output" | "safe-fresh-d-output" => {}
            _ => unreachable!(),
        }
        command.env("LOCALLORE_TEST_WORKSPACE", &workspace)
            .env("LOCALLORE_D02_ARTIFACT_DIR", &output)
            .env(ROOT_ENV, &fixture.outer).env(ARG_ENV, &argument)
            .env(NEW_ENV, &fixture.new_root).env(CASE_ENV, case)
            .stdout(Stdio::piped()).stderr(Stdio::piped());
        if *case == "missing-output" { command.env_remove("LOCALLORE_D02_ARTIFACT_DIR"); }
        let before = inventory(&fixture.outer);
        println!("retained-review-case:{case}; preserved fixture {:?}", fixture.outer);
        let mut child = command.spawn().unwrap();
        let mut stdout = child.stdout.take().unwrap();
        let mut stderr = child.stderr.take().unwrap();
        let out = std::thread::spawn(move || {
            let mut bytes = Vec::new();
            stdout.by_ref().take(65537).read_to_end(&mut bytes).unwrap();
            bytes
        });
        let err = std::thread::spawn(move || {
            let mut bytes = Vec::new();
            stderr.by_ref().take(65537).read_to_end(&mut bytes).unwrap();
            bytes
        });
        let deadline = Instant::now() + Duration::from_secs(30);
        let status = loop {
            if let Some(status) = child.try_wait().unwrap() { break status; }
            if Instant::now() >= deadline {
                let _ = child.kill();
                let cleanup = Instant::now() + Duration::from_secs(5);
                while Instant::now() < cleanup {
                    if child.try_wait().unwrap().is_some() { break; }
                    std::thread::sleep(Duration::from_millis(10));
                }
                panic!("review child timeout {case}; owned drain unqualified; no later child admitted");
            }
            std::thread::sleep(Duration::from_millis(10));
        };
        let cleanup = Instant::now() + Duration::from_secs(5);
        while (!out.is_finished() || !err.is_finished()) && Instant::now() < cleanup {
            std::thread::sleep(Duration::from_millis(10));
        }
        assert!(out.is_finished() && err.is_finished(), "bounded child reader drain; no later child admitted");
        let out = out.join().unwrap();
        let err = err.join().unwrap();
        assert!(out.len() <= 65536 && err.len() <= 65536, "bounded child output");
        assert_eq!(before, inventory(&fixture.outer), "complete parent inventory changed: {case}");
        assert!(status.success(), "case {case}: {} {}", String::from_utf8_lossy(&out), String::from_utf8_lossy(&err));
        println!("retained-review-case:{case}:{}", String::from_utf8_lossy(&out));
    }
}

#[test]
#[ignore = "fixed child only; parent supplies an isolated synthetic environment"]
fn fixed_review_profile_case_child() {
    let case = std::env::var(CASE_ENV).unwrap();
    assert!(CASES.contains(&case.as_str()));
    let outer = PathBuf::from(std::env::var_os(ROOT_ENV).unwrap());
    let argument = PathBuf::from(std::env::var_os(ARG_ENV).unwrap());
    let new_root = PathBuf::from(std::env::var_os(NEW_ENV).unwrap());
    let before = inventory(&outer);
    let active = review_active();
    let first = review_webview_profile(&argument);
    let second = review_webview_profile(&argument);
    assert_eq!(before, inventory(&outer), "helpers must not create, write or remove files: {case}");
    let inactive = matches!(case.as_str(),
        "legacy-stage-absent" | "legacy-stage-zero" | "legacy-stage-one" | "malformed-stage"
        | "missing-d02" | "missing-full" | "missing-native" | "missing-scene" | "missing-memory" | "mixed-d04");
    assert_eq!(active, !inactive, "review gate is exactly active Scene4 plus stage review");
    if case == "safe-fresh-d-output" {
        let expected = new_root.join("webview-profile");
        assert_eq!(first.unwrap(), expected);
        assert_eq!(second.unwrap(), expected);
        assert!(!expected.exists(), "helper returns a new path without creating it");
        assert!(!new_root.join("review").exists(), "helper does not create artifact leaf");
        assert!(!argument.exists(), "memory source database remains absent");
    } else {
        assert!(first.is_err() && second.is_err(), "review profile must refuse {case}");
    }
    println!("fixed-retained-review-profile-case:{case}:pure");
}
