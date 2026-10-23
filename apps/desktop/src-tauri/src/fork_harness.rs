//! Development-only closed synthetic fork fixtures/faults. No renderer paths/code.
use crate::WorkspaceState;
use locallore::{contracts::*, engine::Engine};
use locallore_storage::Store;
use serde_json::{json, Value};
use std::{
    path::Path,
    sync::{
        atomic::{AtomicBool, Ordering},
        Arc,
    },
};
#[derive(Default)]
pub struct ForkHarnessState {
    pub hold: AtomicBool,
    pub lose_ack: AtomicBool,
}
pub fn active() -> bool {
    crate::harness::active() && std::env::var("LOCALLORE_D08_FORK_HARNESS").as_deref() == Ok("1")
}
pub fn seed(path: &Path) -> Result<(), String> {
    let mut store = Store::create_new_pinned(path).map_err(|e| e.to_string())?;
    let mut seed: Seed =
        serde_json::from_str(include_str!("../../../../fixtures/lantern_quay.json"))
            .map_err(|_| "SyntheticSeed")?;
    seed.scope.story = "fork-native".into();
    let scope = seed.scope.clone();
    store
        .create_story("Synthetic alternate timelines", seed)
        .map_err(|e| e.to_string())?;
    for (key, commands) in [
        (
            "fork-prefix",
            vec![
                Command::Say {
                    text: "ORIGINAL_PREFIX_MIRA_ONLY".into(),
                    audience: ["mira".into()].into(),
                },
                Command::Wait { ticks: 1 },
            ],
        ),
        (
            "parent-future",
            vec![Command::Say {
                text: "PARENT_FUTURE_EXCLUDED".into(),
                audience: ["mira".into()].into(),
            }],
        ),
    ] {
        let engine = store.resume(&scope).map_err(|e| e.to_string())?.engine;
        let request = engine.request(key, Intent::Actions(commands));
        let proposal = Engine::proposal(&request).map_err(|e| e.to_string())?;
        let receipt = engine
            .preview(&request, &proposal)
            .map_err(|e| e.to_string())?;
        store.begin_turn(&request).map_err(|e| e.to_string())?;
        store
            .commit_turn(&request, &proposal, receipt.narration())
            .map_err(|e| e.to_string())?;
    }
    Ok(())
}
#[tauri::command]
pub async fn harness_fork_case(
    window: tauri::WebviewWindow,
    workspace: tauri::State<'_, WorkspaceState>,
    state: tauri::State<'_, Arc<ForkHarnessState>>,
    action: String,
) -> Result<Value, String> {
    if !active() {
        return Err("Forbidden".into());
    }
    let epoch = workspace
        .lease
        .capture(window.label())
        .map_err(str::to_owned)?;
    match action.as_str() {
        "hold" => {
            state.hold.store(true, Ordering::SeqCst);
            Ok(json!({"held":true}))
        }
        "release" => {
            state.hold.store(false, Ordering::SeqCst);
            Ok(json!({"held":false}))
        }
        "lose-ack" => {
            state.lose_ack.store(true, Ordering::SeqCst);
            Ok(json!({"armed":true}))
        }
        "advance-parent" => {
            if std::env::var("LOCALLORE_TEST_RESTART").as_deref() == Ok("1") {
                return Err("Forbidden".into());
            }
            let host = workspace.get(epoch).await?;
            let lease = workspace.lease.clone();
            tauri::async_runtime::spawn_blocking(move||lease.dispatch(epoch,||{
                let call=|command:Value|host.call(&serde_json::to_vec(&json!({"version":1,"command":command})).map_err(|_|"SyntheticInput").unwrap());
                let scope=json!({"story":"fork-native","branch":"main"});
                let resumed=call(json!({"op":"resume","scope":scope}));
                let session=resumed["data"]["session"].as_str().ok_or("SyntheticSession")?;
                let answer=(||{
                    let submit=call(json!({"op":"submit","session":session,"request":{"version":1,"scope":scope,"turn":"fork-fixed-external-wait","expected_revision":3,"intent":{"kind":"actions","value":[{"op":"wait","ticks":1}]}},"mode":"accepted"}));
                    if submit["data"]["phase"]!="queued" {return Err("SyntheticSubmit".to_owned());}
                    for (op,phase) in [("prepare","ready"),("commit","committed")] {let result=call(json!({"op":op,"session":session,"scope":scope,"turn":"fork-fixed-external-wait"}));if result["data"]["phase"]!=phase{return Err("SyntheticCommit".to_owned());}}
                    Ok(json!({"advanced":true,"revision":4}))
                })();
                call(json!({"op":"close","session":session,"scope":scope})); answer
            })).await.map_err(|_|"SyntheticWorker".to_owned())?
        }
        _ => Err("InvalidForkFixture".into()),
    }
}
