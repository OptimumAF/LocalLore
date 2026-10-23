//! Closed synthetic fixture/faults, compiled only with dev-harness.
use crate::WorkspaceState;
use locallore::{contracts::*, engine::Engine};
use locallore_storage::Store;
use serde_json::{json, Value};
use std::{
    path::Path,
    sync::atomic::{AtomicBool, Ordering},
};
pub static HOLD: AtomicBool = AtomicBool::new(false);
pub static LOSE_ACK: AtomicBool = AtomicBool::new(false);
pub fn active() -> bool {
    crate::harness::active() && std::env::var("LOCALLORE_M07_MEMORY_HARNESS").as_deref() == Ok("1")
}
pub fn seed(path: &Path) -> Result<(), String> {
    let mut store = Store::create_new_pinned(path).map_err(|e| e.to_string())?;
    let mut seed: Seed =
        serde_json::from_str(include_str!("../../../../fixtures/lantern_quay.json"))
            .map_err(|_| "SyntheticSeed")?;
    seed.scope.story = "memory-controls-synthetic".into();
    let scope = seed.scope.clone();
    store
        .create_story("Synthetic derived memory", seed)
        .map_err(|e| e.to_string())?;
    let engine = store.resume(&scope).map_err(|e| e.to_string())?.engine;
    let request = engine.request(
        "memory-original-mira-receipt",
        Intent::Actions(vec![Command::Say {
            text: "MEMORY_ORIGINAL_MIRA_ONLY".into(),
            audience: ["mira".into()].into(),
        }]),
    );
    let proposal = Engine::proposal(&request).map_err(|e| e.to_string())?;
    let receipt = engine
        .preview(&request, &proposal)
        .map_err(|e| e.to_string())?;
    store.begin_turn(&request).map_err(|e| e.to_string())?;
    store.commit_prepared(&receipt).map_err(|e| e.to_string())?;
    let mut other: Seed =
        serde_json::from_str(include_str!("../../../../fixtures/lantern_quay.json"))
            .map_err(|_| "SyntheticSeed")?;
    other.scope.story = "memory-controls-other".into();
    store
        .create_story("Other synthetic story", other)
        .map_err(|e| e.to_string())?;
    Ok(())
}
#[tauri::command]
pub async fn harness_memory_case(
    window: tauri::WebviewWindow,
    workspace: tauri::State<'_, WorkspaceState>,
    action: String,
) -> Result<Value, String> {
    if !active() {
        return Err("Forbidden".into());
    }
    workspace
        .lease
        .capture(window.label())
        .map_err(str::to_owned)?;
    match action.as_str() {
        "hold" => {
            HOLD.store(true, Ordering::SeqCst);
            Ok(json!({"held":true}))
        }
        "release" => {
            HOLD.store(false, Ordering::SeqCst);
            Ok(json!({"held":false}))
        }
        "lose-ack" => {
            LOSE_ACK.store(true, Ordering::SeqCst);
            Ok(json!({"armed":true}))
        }
        _ => Err("InvalidMemoryFixture".into()),
    }
}
