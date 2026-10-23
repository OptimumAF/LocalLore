use locallore::{contracts::*, engine::Engine};
use serde_json::{json, Value};

fn seed() -> Seed {
    serde_json::from_str(include_str!("../../../fixtures/lantern_quay.json")).unwrap()
}
fn wait(engine: &mut Engine, turn: &str) -> Receipt {
    let request = engine.request(turn, Intent::Actions(vec![Command::Wait { ticks: 1 }]));
    let proposal = Engine::proposal(&request).unwrap();
    let narration = engine
        .preview(&request, &proposal)
        .unwrap()
        .narration()
        .to_owned();
    engine.commit(&request, &proposal, &narration).unwrap()
}

#[test]
fn strict_continuation_keeps_original_scopes_and_never_returns_partial_history() {
    let mut root = Engine::new(seed()).unwrap();
    let inherited = wait(&mut root, "same-key");
    let mut child = root.fork("child", root.revision()).unwrap();
    let local = wait(&mut child, "same-key");
    let base = root.fork("child", root.revision()).unwrap();
    let before = base.canonical_bytes();
    let restored = base
        .restore_continuation(&[serde_json::to_string(&local).unwrap()])
        .unwrap();
    assert_eq!(restored.receipts(), [inherited, local.clone()]);
    assert_eq!(restored.scope().branch, "child");
    assert_eq!(restored.canonical_bytes(), child.canonical_bytes());
    assert_eq!(
        restored.recorded(local.request()).unwrap(),
        Some(local.clone())
    );
    assert_eq!(base.canonical_bytes(), before);
    let mut forged = serde_json::to_value(&local).unwrap();
    forged["events"][0]["sequence"] = json!(99);
    assert_eq!(
        base.restore_continuation(&[serde_json::to_string(&local).unwrap(), forged.to_string()])
            .err(),
        Some(Error::CorruptHistory)
    );
    assert_eq!(base.canonical_bytes(), before);
    let encoded = serde_json::to_string(&local).unwrap();
    let duplicate = encoded.replacen("\"request\":", "\"request\":{},\"request\":", 1);
    assert_eq!(
        base.restore_continuation(&[duplicate]).err(),
        Some(Error::CorruptHistory)
    );
    assert_eq!(
        base.restore_continuation(&["x".repeat(MAX_RECEIPT_BYTES + 1)])
            .err(),
        Some(Error::TooLarge)
    );
}

#[test]
fn accepted_historical_play_is_supported_only_by_recorded_restore_paths() {
    let fixture: Value =
        serde_json::from_str(include_str!("fixtures/accepted_play_v2_1.json")).unwrap();
    let seed: Seed = serde_json::from_value(fixture["seed"].clone()).unwrap();
    let root = Engine::new(seed.clone()).unwrap();
    let restored = root
        .restore_continuation(&[fixture["receipt"].to_string()])
        .unwrap();
    assert_eq!(
        serde_json::to_value(&restored.receipts()[0]).unwrap(),
        fixture["receipt"]
    );
    let child = restored.fork("child", restored.revision()).unwrap();
    let resumed = child.restore_continuation(&[]).unwrap();
    assert_eq!(resumed.receipts(), restored.receipts());
    let mut fresh = Engine::new(seed).unwrap();
    assert_eq!(
        fresh.commit_prepared(&restored.receipts()[0]),
        Err(Error::Narration)
    );
    let mut unknown = fixture["receipt"].clone();
    unknown["play"]["prompt_version"] = json!("locallore-play-v2.0");
    assert_eq!(
        root.restore_continuation(&[unknown.to_string()]).err(),
        Some(Error::CorruptHistory)
    );
}
