// Copyright 2026 LocalLore contributors. SPDX-License-Identifier: Apache-2.0
//! Synthetic shared save/resume proof. No UI, model, raw SQL or private stories.
use locallore::{
    contracts::{Command, Intent, Seed},
    engine::Engine,
};
use locallore_storage::{Store, TurnPhase};
use serde_json::{json, Value};
use std::path::Path;
fn smoke(directory: &Path) -> Result<Value, &'static str> {
    std::fs::create_dir(directory).map_err(|_| "directory")?;
    let database = directory.join("stories.sqlite");
    let seed: Seed = serde_json::from_str(include_str!("../../../fixtures/lantern_quay.json"))
        .map_err(|_| "fixture")?;
    let mut store = Store::open(&database, None).map_err(|_| "open")?;
    store
        .create_story("Synthetic durability proof", seed.clone())
        .map_err(|_| "create")?;
    let engine = Engine::new(seed.clone()).map_err(|_| "fixture")?;
    let request = engine.request(
        "saved-gift",
        Intent::Actions(vec![Command::Give {
            item: "potion".into(),
            to: "mira".into(),
            quantity: 1,
        }]),
    );
    store.begin_turn(&request).map_err(|_| "draft")?;
    // A provider may run here on an owned worker. There is no open database transaction.
    let proposal = Engine::proposal(&request).map_err(|_| "proposal")?;
    let preview = engine
        .preview(&request, &proposal)
        .map_err(|_| "proposal")?;
    let receipt = store
        .commit_turn(&request, &proposal, preview.narration())
        .map_err(|_| "commit")?;
    let canonical = store
        .resume(&seed.scope)
        .map_err(|_| "resume")?
        .engine
        .canonical_bytes();
    drop(store);
    let mut store = Store::open(&database, None).map_err(|_| "reopen")?;
    let resumed = store.resume(&seed.scope).map_err(|_| "resume")?;
    let equal = resumed.engine.canonical_bytes() == canonical
        && resumed.engine.receipts() == [receipt.clone()]
        && resumed.engine.state().items["potion"].owner == "mira";
    let context = resumed
        .engine
        .character_context("sable", &seed.scope, 1)
        .map_err(|_| "observer")?;
    let retry = store.begin_turn(&request).map_err(|_| "retry")?;
    if !equal
        || !context.observations.is_empty()
        || retry.phase != TurnPhase::Committed
        || retry.receipt != Some(receipt)
    {
        return Err("verification");
    }
    store
        .commit_turn(&request, &proposal, preview.narration())
        .map_err(|_| "retry")?;
    let final_state = store.resume(&seed.scope).map_err(|_| "resume")?;
    if final_state.engine.revision() != 1 || final_state.projection_needs_rebuild {
        return Err("verification");
    }
    store
        .backup_to(&directory.join("backup.sqlite"))
        .map_err(|_| "backup")?;
    let mut backup = Store::open(&directory.join("backup.sqlite"), None).map_err(|_| "backup")?;
    if backup
        .resume(&seed.scope)
        .map_err(|_| "backup")?
        .engine
        .canonical_bytes()
        != canonical
    {
        return Err("backup");
    }
    let info = store.info().map_err(|_| "info")?;
    Ok(
        json!({"version":1,"synthetic":true,"status":"completed","schema_version":info.schema_version,
        "sqlite_version":info.sqlite_version,"foreign_keys":info.foreign_keys,"revision":1,
        "complete_receipt_equal":true,"canonical_bytes_equal":true,"retry_applied_once":true,
        "unwitnessed_observer_isolated":true,"consistent_backup_resumed":true,"model_calls":0}),
    )
}
fn main() {
    std::panic::set_hook(Box::new(|_| {}));
    let result = std::panic::catch_unwind(|| {
        let args: Vec<_> = std::env::args_os().skip(1).collect();
        if args.len() != 2 || args[0] != "--directory" {
            return Err("arguments");
        }
        smoke(Path::new(&args[1]))
    })
    .unwrap_or(Err("panic"));
    let (report, status) = match result {
        Ok(value) => (value, 0),
        Err(category) => (
            json!({"version":1,"synthetic":true,"status":"failed","error":category}),
            1,
        ),
    };
    println!("{report}");
    std::process::exit(status);
}
