//! Fresh selected-only startup must not require opening the built-in catalog.
use super::*;
#[test]
fn capacity_query_uses_existing_workspace_without_creating_unopened_libraries() {
    let parent = std::env::temp_dir().join(format!("selected budget résumé-{}", uuid().unwrap()));
    fs::create_dir(&parent).unwrap();
    let manager = EvaluationManager::new(parent.join("unopened-builtins"));
    let result = manager.budget(None);
    let empty = fs::read_dir(&parent).unwrap().count() == 0;
    fs::remove_dir(&parent).unwrap();
    assert!(
        result.is_ok(),
        "fresh selected-only capacity failed: {result:?}"
    );
    assert!(empty, "read-only capacity must not create another library");
}
#[test]
fn capacity_query_refuses_missing_workspace_parent_without_creating_it() {
    let parent = std::env::temp_dir().join(format!("selected-absent-{}", uuid().unwrap()));
    let manager = EvaluationManager::new(parent.join("unopened-builtins"));
    assert_eq!(manager.budget(None).unwrap_err(), "EvaluationIo");
    assert!(!parent.exists());
}
