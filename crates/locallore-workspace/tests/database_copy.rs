use locallore::{contracts::*, engine::Engine};
use locallore_storage::Store;
use locallore_workspace::inspection_database_copy;
use std::path::PathBuf;

struct Temp(PathBuf);
impl Temp {
    fn new() -> Self {
        let path = std::env::temp_dir().join(format!(
            "locallore-copy-{}-{}",
            std::process::id(),
            std::time::SystemTime::now()
                .duration_since(std::time::UNIX_EPOCH)
                .unwrap()
                .as_nanos()
        ));
        std::fs::create_dir(&path).unwrap();
        Self(path)
    }
}
impl Drop for Temp {
    fn drop(&mut self) {
        std::fs::remove_dir_all(&self.0).unwrap();
    }
}

#[test]
fn consistent_copy_resumes_committed_history_and_reports_actual_heads_without_source_effects() {
    let dir = Temp::new();
    let source = dir.0.join("stories.sqlite");
    let destination = dir.0.join("copy.sqlite");
    let mut store = Store::open(&source, None).unwrap();
    let seed: Seed =
        serde_json::from_str(include_str!("../../../fixtures/lantern_quay.json")).unwrap();
    let scope = store.create_workspace("Synthetic copy", seed).unwrap();
    let mut engine = store.resume(&scope).unwrap().engine;
    let request = engine.request(
        "gift",
        Intent::Actions(vec![Command::Give {
            item: "potion".into(),
            to: "mira".into(),
            quantity: 1,
        }]),
    );
    let proposal = Engine::proposal(&request).unwrap();
    let narration = engine
        .preview(&request, &proposal)
        .unwrap()
        .narration()
        .to_owned();
    store.begin_turn(&request).unwrap();
    store.commit_turn(&request, &proposal, &narration).unwrap();
    engine = store.resume(&scope).unwrap().engine;
    let canonical = engine.canonical_bytes();
    let metadata = inspection_database_copy(&source, &destination).unwrap();
    assert_eq!(metadata.len(), 1);
    assert_eq!(metadata[0].scope, scope);
    assert_eq!(metadata[0].revision, 1);
    let mut copied = Store::open_read_only(&destination).unwrap();
    assert_eq!(
        copied.resume(&scope).unwrap().engine.canonical_bytes(),
        canonical
    );
    assert_eq!(
        store.resume(&scope).unwrap().engine.canonical_bytes(),
        canonical
    );
    assert!(inspection_database_copy(&source, &destination).is_err());
    assert_eq!(
        copied.resume(&scope).unwrap().engine.canonical_bytes(),
        canonical
    );
    let mut forbidden = engine.seed().clone();
    forbidden.scope.story = "new-write-forbidden".into();
    assert!(copied.create_story("forbidden", forbidden).is_err());
    assert_eq!(copied.stories().unwrap().len(), 1);
}

#[test]
fn inspection_copy_does_not_create_or_migrate_missing_empty_or_foreign_sources() {
    let dir = Temp::new();
    let source = dir.0.join("missing.sqlite");
    let dest = dir.0.join("copy.sqlite");
    assert!(inspection_database_copy(&source, &dest).is_err());
    assert!(!source.exists());
    assert!(!dest.exists());
    std::fs::write(&source, b"").unwrap();
    assert!(inspection_database_copy(&source, &dest).is_err());
    assert!(std::fs::read(&source).unwrap().is_empty());
    assert!(!dest.exists());
    std::fs::write(&source, b"foreign non sqlite file").unwrap();
    assert!(inspection_database_copy(&source, &dest).is_err());
    assert_eq!(std::fs::read(&source).unwrap(), b"foreign non sqlite file");
    assert!(!dest.exists());
}
