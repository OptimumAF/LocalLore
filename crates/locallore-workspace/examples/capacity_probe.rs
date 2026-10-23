// Copyright 2026 LocalLore contributors. SPDX-License-Identifier: Apache-2.0
//! Explicit synthetic Host-v1 capacity experiment. No SQL or production fault hook.
//! Run with a fresh --directory, --prefix 0..8, and optionally --expect-full.
//! A capped run uses a separately compiled bundled SQLite, e.g.
//! LIBSQLITE3_FLAGS=-DSQLITE_MAX_PAGE_COUNT=<measured pages>.
//! The directory is retained for local inspection; it must not already exist.
use locallore::host::Host;
use serde_json::{json, Value};
use std::path::{Path, PathBuf};

fn require(condition: bool, stage: &'static str) -> Result<(), &'static str> {
    if condition {
        Ok(())
    } else {
        Err(stage)
    }
}
fn call(host: &Host, command: Value) -> Value {
    host.call(&serde_json::to_vec(&json!({"version":1,"command":command})).unwrap())
}
fn phase(value: &Value, expected: &str, stage: &'static str) -> Result<(), &'static str> {
    require(
        value["status"] == "ok" && value["data"]["phase"] == expected,
        stage,
    )
}
fn operation(host: &Host, session: &str, scope: &Value, turn: &str, op: &str) -> Value {
    call(
        host,
        json!({"op":op,"session":session,"scope":scope,"turn":turn}),
    )
}
fn snapshot(host: &Host, session: &str, scope: &Value, revision: usize) -> Value {
    call(
        host,
        json!({"op":"play_snapshot","session":session,"scope":scope,"expected_revision":revision}),
    )
}
fn bytes(path: &Path) -> Result<u64, &'static str> {
    // Metadata only: never reads the live database file or opens another connection.
    std::fs::metadata(path)
        .map(|v| v.len())
        .map_err(|_| "metadata")
}
fn run(directory: PathBuf, prefix: usize, expect_full: bool) -> Result<Value, &'static str> {
    std::fs::create_dir(&directory).map_err(|_| "fresh_directory")?;
    let path = directory.join("stories.sqlite");
    let host = locallore_workspace::open(&path, false).map_err(|_| "open")?;
    let created = call(&host, json!({"op":"create","seed":"lantern-quay-v1"}));
    require(created["status"] == "ok", "create")?;
    let session = created["data"]["session"].as_str().ok_or("session")?;
    let scope = &created["data"]["scope"];
    let initial_bytes = bytes(&path)?;
    let mut prefix_sizes = Vec::new();
    for revision in 0..prefix {
        let turn = format!("00000000-0000-4000-8000-{:012}", revision + 1);
        let request = json!({"version":1,"scope":scope,"turn":turn,"expected_revision":revision,
            "intent":{"kind":"dialogue","value":{"text":"C".repeat(2048),"audience":["mira"]}}});
        phase(
            &call(
                &host,
                json!({"op":"submit","session":session,"request":request,"mode":"accepted"}),
            ),
            "queued",
            "prefix_submit",
        )?;
        phase(
            &operation(&host, session, scope, &turn, "prepare"),
            "ready",
            "prefix_prepare",
        )?;
        phase(
            &operation(&host, session, scope, &turn, "commit"),
            "committed",
            "prefix_commit",
        )?;
        prefix_sizes.push(bytes(&path)?);
    }
    let before = snapshot(&host, session, scope, prefix);
    require(
        before["status"] == "ok" && before["data"]["inventory"]["potion"]["owner"] == "player",
        "before_snapshot",
    )?;
    require(
        before["data"]["receipts"]
            .as_array()
            .is_some_and(|v| v.len() == prefix),
        "before_receipts",
    )?;
    let before_draft = bytes(&path)?;
    let turn = "00000000-0000-4000-8000-000000000099";
    let request = json!({"version":1,"scope":scope,"turn":turn,"expected_revision":prefix,
        "intent":{"kind":"actions","value":[{"op":"give","item":"potion","to":"mira","quantity":1}]}});
    phase(
        &call(
            &host,
            json!({"op":"submit","session":session,"request":request,"mode":"accepted"}),
        ),
        "queued",
        "gift_submit",
    )?;
    let after_draft = bytes(&path)?;
    phase(
        &operation(&host, session, scope, turn, "prepare"),
        "ready",
        "gift_prepare",
    )?;
    let after_ready = bytes(&path)?;
    let committed = operation(&host, session, scope, turn, "commit");
    let after_commit = bytes(&path)?;
    let full = committed["status"] == "rejected" && committed["error"] == "Full";
    require(full == expect_full, "expected_commit_outcome")?;
    let retained;
    let canonical_unchanged;
    if full {
        phase(
            &operation(&host, session, scope, turn, "turn_status"),
            "ready",
            "retained_ready",
        )?;
        retained = true;
        let repeated = operation(&host, session, scope, turn, "commit");
        require(
            repeated["status"] == "rejected" && repeated["error"] == "Full",
            "repeat_full",
        )?;
        canonical_unchanged = snapshot(&host, session, scope, prefix) == before;
        require(canonical_unchanged, "canonical_unchanged")?;
    } else {
        phase(&committed, "committed", "gift_commit")?;
        require(
            operation(&host, session, scope, turn, "commit") == committed,
            "idempotent_commit",
        )?;
        let accepted = snapshot(&host, session, scope, prefix + 1);
        require(
            accepted["status"] == "ok" && accepted["data"]["inventory"].get("potion").is_none(),
            "accepted_snapshot",
        )?;
        require(
            accepted["data"]["receipts"]
                .as_array()
                .is_some_and(|v| v.len() == prefix + 1),
            "accepted_receipts",
        )?;
        retained = false;
        canonical_unchanged = false;
    }
    drop(host);
    let reopened = locallore_workspace::open(&path, false).map_err(|_| "reopen")?;
    let resumed = call(&reopened, json!({"op":"resume","scope":scope}));
    require(resumed["status"] == "ok", "resume")?;
    let resumed_session = resumed["data"]["session"]
        .as_str()
        .ok_or("resume_session")?;
    let reopened_key = operation(&reopened, resumed_session, scope, turn, "turn_status");
    phase(
        &reopened_key,
        if full { "queued" } else { "committed" },
        "original_key_after_reopen",
    )?;
    if full {
        require(
            snapshot(&reopened, resumed_session, scope, prefix) == before,
            "reopened_canon",
        )?;
    } else {
        require(reopened_key == committed, "reopened_receipt")?;
    }
    Ok(
        json!({"version":1,"prefix":prefix,"dialogue_bytes":2048,"turn_id_bytes":36,
        "initial_bytes":initial_bytes,"prefix_commit_bytes":prefix_sizes,"before_draft_bytes":before_draft,
        "after_draft_bytes":after_draft,"after_ready_bytes":after_ready,"after_commit_bytes":after_commit,
        "commit_full":full,"same_key_ready_after_full":retained,"canonical_unchanged_after_full":canonical_unchanged,
        "original_key_reopened":true,"reopen_revision":if full { prefix } else { prefix + 1 },
        "relief_recovery_proven":false,"status":"passed"}),
    )
}
fn main() {
    let mut directory = None;
    let mut prefix = 0;
    let mut expect_full = false;
    let mut args = std::env::args().skip(1);
    while let Some(arg) = args.next() {
        match arg.as_str() {
            "--directory" => directory = args.next().map(PathBuf::from),
            "--prefix" => {
                prefix = args
                    .next()
                    .and_then(|v| v.parse::<usize>().ok())
                    .filter(|v| *v <= 8)
                    .unwrap_or(9)
            }
            "--expect-full" => expect_full = true,
            _ => {
                eprintln!("capacity_probe: invalid_arguments");
                std::process::exit(2);
            }
        }
    }
    let result = directory.ok_or("missing_directory").and_then(|dir| {
        require(prefix <= 8, "invalid_prefix")?;
        run(dir, prefix, expect_full)
    });
    match result {
        Ok(report) => println!("{report}"),
        Err(stage) => {
            eprintln!("{}", json!({"version":1,"status":"failed","stage":stage}));
            std::process::exit(1);
        }
    }
}
