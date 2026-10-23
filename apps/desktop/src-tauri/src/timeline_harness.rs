//! Fixed synthetic development fixture, created before the application's Host opens.
//! No renderer-controlled paths, commands, scripts or model operations.
use locallore::{contracts::*, engine::Engine};
use locallore_storage::{ForkRequest, Store};
use std::path::Path;

pub fn seed(path: &Path) -> Result<(), String> {
    let mut store = Store::create_new_pinned(path).map_err(|e| e.to_string())?;
    let mut seed: Seed =
        serde_json::from_str(include_str!("../../../../fixtures/lantern_quay.json"))
            .map_err(|_| "SyntheticSeed".to_owned())?;
    seed.scope.story = "timeline-native".into();
    let root = seed.scope.clone();
    store
        .create_story("Synthetic saved timelines", seed)
        .map_err(|e| e.to_string())?;
    for n in 0..4 {
        commit(
            &mut store,
            &root,
            &format!("root-{n}"),
            Command::Wait { ticks: 1 },
        )?;
    }
    let parent = fork(&mut store, &root, "parent", 2)?;
    for n in 0..2 {
        commit(
            &mut store,
            &parent,
            &format!("parent-{n}"),
            Command::Say {
                text: format!("Original inherited parent statement {n}"),
                audience: ["mira".into()].into(),
            },
        )?;
    }
    let _child = fork(&mut store, &parent, "child", 4)?;
    commit(
        &mut store,
        &parent,
        "parent-future",
        Command::Say {
            text: "PARENT_FUTURE_CANARY".into(),
            audience: ["mira".into()].into(),
        },
    )?;
    let sibling = fork(&mut store, &root, "sibling", 1)?;
    commit(
        &mut store,
        &sibling,
        "sibling-only",
        Command::Say {
            text: "SIBLING_ONLY_CANARY".into(),
            audience: ["mira".into()].into(),
        },
    )?;
    let deletion = store
        .prepare_branch_deletion(&parent, 5, &|| false)
        .map_err(|e| e.to_string())?;
    store
        .delete_branch(deletion, &|| false)
        .map_err(|e| e.to_string())?;
    Ok(())
}
fn commit(store: &mut Store, scope: &Scope, key: &str, command: Command) -> Result<(), String> {
    let engine = store.resume(scope).map_err(|e| e.to_string())?.engine;
    let request = engine.request(key, Intent::Actions(vec![command]));
    let proposal = Engine::proposal(&request).map_err(|e| e.to_string())?;
    let receipt = engine
        .preview(&request, &proposal)
        .map_err(|e| e.to_string())?;
    store.begin_turn(&request).map_err(|e| e.to_string())?;
    store
        .commit_turn(&request, &proposal, receipt.narration())
        .map_err(|e| e.to_string())?;
    Ok(())
}
fn fork(store: &mut Store, parent: &Scope, child: &str, at: u64) -> Result<Scope, String> {
    let head = store
        .resume(parent)
        .map_err(|e| e.to_string())?
        .engine
        .revision();
    store
        .fork_branch(
            &ForkRequest {
                parent: parent.clone(),
                child_branch: child.into(),
                expected_parent_revision: head,
                at_revision: at,
            },
            &|| false,
        )
        .map(|r| r.scope)
        .map_err(|e| e.to_string())
}

#[cfg(test)]
mod tests {
    use super::*;
    #[test]
    fn actual_fixture_reopens_original_scopes_and_never_reseeds_an_existing_database() {
        let root = std::env::temp_dir().join(format!(
            "timeline-native-{}",
            crate::exports::identifier().unwrap()
        ));
        std::fs::create_dir(&root).unwrap();
        let path = root.join("synthetic.sqlite");
        seed(&path).unwrap();
        let before = std::fs::read(&path).unwrap();
        assert!(seed(&path).is_err());
        assert_eq!(std::fs::read(&path).unwrap(), before);
        let mut store = Store::open_read_only(&path).unwrap();
        let child = Scope {
            story: "timeline-native".into(),
            branch: "child".into(),
        };
        let engine = store.resume(&child).unwrap().engine;
        assert_eq!(engine.revision(), 4);
        assert!(engine
            .receipts()
            .iter()
            .any(|r| r.request().scope.branch == "parent"));
        assert!(engine
            .receipts()
            .iter()
            .flat_map(|r| r.events())
            .all(|e| e.scope().branch != "sibling"));
        let text = serde_json::to_string(engine.receipts()).unwrap();
        assert!(!text.contains("PARENT_FUTURE_CANARY") && !text.contains("SIBLING_ONLY_CANARY"));
        let catalog = store.branch_catalog("timeline-native", &|| false).unwrap();
        let parent = catalog
            .branches
            .iter()
            .find(|b| b.scope.branch == "parent")
            .unwrap();
        assert!(parent.retired);
        assert_eq!(parent.revision, 4);
        drop(store);
        // Read-only SQLite may leave its fixed WAL/SHM siblings after close.
        // Remove only this test's four literal database names, no tree cleanup.
        for name in [
            "synthetic.sqlite",
            "synthetic.sqlite-wal",
            "synthetic.sqlite-shm",
            "synthetic.sqlite-journal",
        ] {
            match std::fs::remove_file(root.join(name)) {
                Ok(()) => {}
                Err(e) if e.kind() == std::io::ErrorKind::NotFound => {}
                Err(e) => panic!("fixed fixture cleanup: {e}"),
            }
        }
        std::fs::remove_dir(root).unwrap();
    }
}
