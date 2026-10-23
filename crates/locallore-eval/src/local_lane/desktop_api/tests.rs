use super::*;
fn files(path: &Path) -> BTreeMap<PathBuf, Vec<u8>> {
    let mut out = BTreeMap::new();
    for item in fs::read_dir(path).unwrap() {
        let p = item.unwrap().path();
        if p.is_dir() {
            out.extend(files(&p));
        } else {
            out.insert(p.clone(), fs::read(p).unwrap());
        }
    }
    out
}
#[test]
fn read_only_open_and_evidence_preserve_every_byte_and_observer_boundaries() {
    let temp = crate::tests::Temp::new();
    let dir = temp.0.join("curated");
    run_curated(
        &dir,
        false,
        Some(&corpus().unwrap().stories[0].id),
        &Cancellation::default(),
        1,
        LaneFactory::ScriptedBaseline,
    )
    .unwrap();
    let before = files(&dir);
    let opened = inspect(&dir).unwrap();
    assert_eq!(opened["resume_compatible"], true);
    assert_eq!(opened["completed"], true);
    let case = opened["report"]["cases"][0]["id"].as_str().unwrap();
    let turn = opened["report"]["cases"][0]["turns"][0]["id"]
        .as_str()
        .unwrap();
    let binding = opened["binding_sha256"].as_str().unwrap();
    let evidence = evidence(
        &dir,
        binding,
        case,
        turn,
        Observer::Omniscient,
        View::TurnDiff,
    )
    .unwrap();
    assert_eq!(evidence["read_only"], true);
    assert_eq!(evidence["generation_grant"], false);
    assert!(evidence["receipt"].is_object());
    assert!(!evidence["outputs"].as_array().unwrap().is_empty());
    let player =
        super::evidence(&dir, binding, case, turn, Observer::Player, View::Knowledge).unwrap();
    assert!(player["receipt"].is_null());
    assert_eq!(player["outputs"], json!([]));
    assert!(super::evidence(
        &dir,
        &"0".repeat(64),
        case,
        turn,
        Observer::Omniscient,
        View::TurnDiff
    )
    .is_err());
    assert!(super::evidence(
        &dir,
        binding,
        "other-story",
        turn,
        Observer::Omniscient,
        View::TurnDiff
    )
    .is_err());
    assert_eq!(files(&dir), before);
}
#[test]
fn changed_source_is_viewable_but_not_resumable_and_unknown_reservation_is_not_refunded() {
    let temp = crate::tests::Temp::new();
    let dir = temp.0.join("curated");
    run_curated(
        &dir,
        false,
        None,
        &Cancellation::default(),
        1,
        LaneFactory::ScriptedBaseline,
    )
    .unwrap();
    let basis_path = dir.join("run.json");
    let old = fs::read(&basis_path).unwrap();
    let old_hash = digest(&old);
    let prior = inspect(&dir).unwrap();
    let mut abandoned = Ledger::load(&dir, &old_hash).unwrap();
    abandoned
        .admit("gift-agency", "unknown-desktop-work")
        .unwrap();
    drop(abandoned);
    let mut basis: Value = serde_json::from_slice(&old).unwrap();
    basis["source"]["prompt_version"] = json!("historical-different-source");
    let bytes = encode(&basis).unwrap();
    let new_hash = digest(&bytes);
    fs::write(&basis_path, bytes).unwrap();
    // Synthetic source-bound historical fixture: rewrite all consistency digests together,
    // not a claim of authenticity. Validating views must not assume current-source equality.
    for (path, bytes) in files(&dir) {
        if path.extension().is_some_and(|e| e == "json") && path != basis_path {
            let text = String::from_utf8(bytes)
                .unwrap()
                .replace(&old_hash, &new_hash);
            if path.file_name().unwrap() == "report.json" {
                let mut report: Value = serde_json::from_str(&text).unwrap();
                report["provenance"]["binding"] = basis.clone();
                fs::write(path, encode(&report).unwrap()).unwrap();
            } else {
                fs::write(path, text).unwrap();
            }
        }
    }
    let before = files(&dir);
    let opened = inspect(&dir).unwrap();
    assert_eq!(opened["resume_compatible"], false);
    assert_eq!(opened["checkpointed_stories"], 1);
    assert_eq!(
        opened["budget"]["admissions_across_attempts"]
            .as_u64()
            .unwrap(),
        prior["budget"]["admissions_across_attempts"]
            .as_u64()
            .unwrap()
            + 1
    );
    assert_eq!(
        opened["budget"]["roles_charged"].as_u64().unwrap(),
        prior["budget"]["roles_charged"].as_u64().unwrap() + 3
    );
    assert_eq!(
        opened["budget"]["active_ms_charged"].as_u64().unwrap(),
        prior["budget"]["active_ms_charged"].as_u64().unwrap() + TURN_MS
    );
    assert_eq!(files(&dir), before);
    assert!(run_curated(
        &dir,
        true,
        None,
        &Cancellation::default(),
        1,
        LaneFactory::ScriptedBaseline
    )
    .is_err());
}
