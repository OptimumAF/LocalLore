//! Independent current adapter checks over an immutable copy of a real historical scripted run.
use locallore::{
    inference::Cancellation,
    inspection_query::{Observer, View},
};
use locallore_eval::{
    digest,
    local_lane::{desktop_api, run_curated, LaneFactory},
};
use serde_json::Value;
use std::{
    collections::BTreeMap,
    fs,
    path::{Path, PathBuf},
};

fn inventory(root: &Path) -> BTreeMap<PathBuf, String> {
    fn visit(base: &Path, path: &Path, result: &mut BTreeMap<PathBuf, String>) {
        for item in fs::read_dir(path).unwrap() {
            let path = item.unwrap().path();
            let metadata = fs::symlink_metadata(&path).unwrap();
            assert!(!metadata.file_type().is_symlink());
            if metadata.is_dir() {
                visit(base, &path, result)
            } else {
                result.insert(
                    path.strip_prefix(base).unwrap().to_owned(),
                    digest(&fs::read(path).unwrap()),
                );
            }
        }
    }
    let mut result = BTreeMap::new();
    visit(root, root, &mut result);
    result
}

#[test]
#[ignore = "requires task-owned byte-exact historical scripted v2.2/schema2 copy"]
fn actual_historical_v22_schema2_is_view_only_without_rewrite_or_admission() {
    let path = PathBuf::from(
        std::env::var_os("LOCALLORE_REVIEW_HISTORICAL_CURATED")
            .expect("explicit historical fixture copy"),
    );
    let basis: Value = serde_json::from_slice(&fs::read(path.join("run.json")).unwrap()).unwrap();
    assert_eq!(basis["native"], false);
    assert_eq!(basis["source"]["prompt_version"], "locallore-play-v2.2");
    assert_eq!(basis["source"]["storage_schema_version"], 2);
    let databases: Vec<_> = fs::read_dir(&path)
        .unwrap()
        .filter_map(|e| {
            let p = e.unwrap().path().join("synthetic.sqlite");
            p.is_file().then_some(p)
        })
        .collect();
    assert_eq!(databases.len(), 6);
    for p in &databases {
        let b = fs::read(p).unwrap();
        assert_eq!(&b[..16], b"SQLite format 3\0");
        assert_eq!(u32::from_be_bytes(b[60..64].try_into().unwrap()), 2);
    }
    let before = inventory(&path);
    let opened = desktop_api::inspect(&path).unwrap();
    assert_eq!(opened["resume_compatible"], false);
    assert_eq!(opened["completed"], true);
    assert_eq!(opened["checkpointed_stories"], 6);
    assert_eq!(
        opened["report"]["provenance"]["generation_this_view"],
        false
    );
    let binding = opened["binding_sha256"].as_str().unwrap();
    let mut checked = 0;
    let mut available = 0;
    let mut unavailable = 0;
    for case in opened["report"]["cases"].as_array().unwrap() {
        for turn in case["turns"].as_array().unwrap() {
            let case_id = case["id"].as_str().unwrap();
            let turn_id = turn["id"].as_str().unwrap();
            match desktop_api::evidence(
                &path,
                binding,
                case_id,
                turn_id,
                Observer::Omniscient,
                View::Profiles,
            ) {
                Ok(view) => {
                    available += 1;
                    assert_eq!(view["revision"], turn["revision"]);
                    assert_eq!(view["canonical_sha256"], turn["canonical_sha256"]);
                    assert_eq!(view["receipt"].is_object(), turn["phase"] == "committed");
                    assert_eq!(view["generation_grant"], false);
                    let player = desktop_api::evidence(
                        &path,
                        binding,
                        case_id,
                        turn_id,
                        Observer::Player,
                        View::Knowledge,
                    )
                    .unwrap();
                    assert!(player["receipt"].is_null());
                    assert!(player["role_metrics"].is_null());
                    assert_eq!(player["outputs"].as_array().unwrap().len(), 0);
                }
                Err(error) => {
                    unavailable += 1;
                    assert!(
                        matches!(error.as_str(), "Workspace" | "CheckpointIntegrity"),
                        "unexpected failure: {error}"
                    );
                }
            }
            checked += 1;
        }
    }
    assert_eq!(checked, 24);
    assert_eq!(
        available, 24,
        "frozen current adapter can replay every turn in this actual historical fixture"
    );
    assert_eq!(unavailable, 0);
    eprintln!("actual historical view: {available} available, {unavailable} explicitly unavailable, {checked} turn rows; original schema2 remains unchanged");
    assert!(run_curated(
        &path,
        true,
        None,
        &Cancellation::default(),
        1,
        LaneFactory::ScriptedBaseline
    )
    .is_err());
    assert_eq!(
        inventory(&path),
        before,
        "view/refused resume changed historical bytes or files"
    );
}
