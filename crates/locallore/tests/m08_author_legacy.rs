//! Frozen compatibility oracles before new canonical storage exists.
use locallore::{contracts::*, engine::Engine};
fn fixture() -> Engine { Engine::new(serde_json::from_str(include_str!("../../../fixtures/lantern_quay.json")).unwrap()).unwrap() }
#[test]
fn legacy_projection_receipt_and_restore_remain_byte_exact() {
    let mut e = fixture(); let original = serde_json::to_vec(e.state()).unwrap(); assert_eq!(e.canonical_bytes(), original);
    let r = e.request("legacy", Intent::Actions(vec![Command::Wait { ticks: 1 }])); let p = Engine::proposal(&r).unwrap();
    let v = e.preview(&r, &p).unwrap(); let bytes = serde_json::to_string(&v).unwrap(); e.commit_prepared(&v).unwrap();
    assert_eq!(e.domain_version(), 1); assert_eq!(serde_json::to_string(&e.canonical_records()[0]).unwrap(), bytes);
    let restored = Engine::restore(e.seed().clone(), &[bytes]).unwrap(); assert_eq!(restored.canonical_bytes(), e.canonical_bytes());
    assert_eq!(restored.receipts(), e.receipts()); assert_eq!(restored.accepted_history_basis().unwrap(), e.accepted_history_basis().unwrap());
}
#[test]
fn legacy_known_discovery_and_author_intent_admission_are_unchanged() {
    let e = fixture(); let r = e.request("author", Intent::AuthorCorrection("change ancestry".into())); assert_eq!(Engine::proposal(&r), Err(Error::AuthorUiRequired));
    let mut seed = e.seed().clone(); seed.facts.get_mut("relic-location").unwrap().discoverable_at = Some("quay".into()); let e = Engine::new(seed).unwrap();
    let r = e.request("known", Intent::Actions(vec![Command::Discover { fact: "relic-location".into() }])); let p = Engine::proposal(&r).unwrap(); assert_eq!(e.preview(&r, &p), Err(Error::Knowledge));
}
