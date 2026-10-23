// Copyright 2026 LocalLore contributors. SPDX-License-Identifier: Apache-2.0
//! Explicit synthetic Full -> free test-owned pages -> same-key acceptance proof.
//! Build in a separate target with LIBSQLITE3_FLAGS=-DSQLITE_MAX_PAGE_COUNT=32.
//! Usage: --directory <fresh parent> --python <Python executable> [--cancel].
//! Retains synthetic files locally; neither runtime changes nor production hooks.
use locallore::host::Host;
use serde_json::{json, Value};
use std::{
    fs::{self, OpenOptions},
    io::Write,
    path::{Path, PathBuf},
    process::{Child, Command, Stdio},
    time::{Duration, Instant, SystemTime, UNIX_EPOCH},
};

const SCHEMA3_SHA256: &str = "c05ced1f0439fb767f97d2ff93a34ef44eb6fbc27da6814a75fad455fb0b2c17";

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
fn op(host: &Host, session: &str, scope: &Value, turn: &str, operation: &str) -> Value {
    call(
        host,
        json!({"op":operation,"session":session,"scope":scope,"turn":turn}),
    )
}
fn snapshot(host: &Host, session: &str, scope: &Value, revision: usize) -> Value {
    call(
        host,
        json!({"op":"play_snapshot","session":session,"scope":scope,"expected_revision":revision}),
    )
}
fn stop_helper(child: &mut Child) -> Result<(), &'static str> {
    // A kill race with normal exit is harmless only after terminal ownership is
    // observed. Never perform a blocking wait or guess that an unknown child died.
    let _ = child.kill();
    let deadline = Instant::now() + Duration::from_secs(2);
    loop {
        match child.try_wait() {
            Ok(Some(_)) => return Ok(()),
            Ok(None) if Instant::now() < deadline => std::thread::sleep(Duration::from_millis(10)),
            _ => return Err("helper_ownership_unknown"),
        }
    }
}
fn helper(
    python: &Path,
    directory: &Path,
    owner: &str,
    action: &str,
) -> Result<Value, &'static str> {
    let stdout = directory.join(format!("{action}.stdout"));
    let stderr = directory.join(format!("{action}.stderr"));
    let output_file = OpenOptions::new()
        .write(true)
        .create_new(true)
        .open(&stdout)
        .map_err(|_| "helper_output")?;
    let error_file = OpenOptions::new()
        .write(true)
        .create_new(true)
        .open(&stderr)
        .map_err(|_| "helper_output")?;
    let script =
        Path::new(env!("CARGO_MANIFEST_DIR")).join("../../scripts/capacity_padding_probe.py");
    let mut child = Command::new(python)
        .arg(script)
        .arg("--directory")
        .arg(directory)
        .arg("--owner")
        .arg(owner)
        .arg("--action")
        .arg(action)
        .stdin(Stdio::null())
        .stdout(output_file)
        .stderr(error_file)
        .spawn()
        .map_err(|_| "helper_start")?;
    let deadline = Instant::now() + Duration::from_secs(10);
    let status = loop {
        let overflow = [&stdout, &stderr]
            .into_iter()
            .any(|path| fs::metadata(path).map_or(true, |metadata| metadata.len() > 4096));
        if overflow {
            stop_helper(&mut child)?;
            return Err("helper_output_bound");
        }
        match child.try_wait() {
            Ok(Some(status)) => break status,
            Ok(None) if Instant::now() < deadline => std::thread::sleep(Duration::from_millis(10)),
            _ => {
                stop_helper(&mut child)?;
                return Err("helper_deadline");
            }
        }
    };
    require(
        fs::metadata(&stdout).map_err(|_| "helper_output")?.len() <= 4096,
        "helper_output",
    )?;
    require(
        fs::metadata(&stderr).map_err(|_| "helper_output")?.len() == 0,
        "helper_stderr",
    )?;
    let report: Value = serde_json::from_slice(&fs::read(stdout).map_err(|_| "helper_output")?)
        .map_err(|_| "helper_json")?;
    require(
        status.success()
            && report["version"] == 2
            && report["database_schema_version"] == 3
            && report["schema_sha256"] == SCHEMA3_SHA256
            && report["status"] == "passed"
            && report["action"] == action,
        "helper_result",
    )?;
    Ok(report)
}
fn run(directory: &Path, python: &Path, cancel: bool) -> Result<Value, &'static str> {
    fs::create_dir(directory).map_err(|_| "fresh_directory")?;
    let owner = format!(
        "{:032x}",
        SystemTime::now()
            .duration_since(UNIX_EPOCH)
            .map_err(|_| "clock")?
            .as_nanos()
            ^ u128::from(std::process::id())
    );
    let owned = directory.join(format!("capacity-relief-{owner}"));
    fs::create_dir(&owned).map_err(|_| "fresh_directory")?;
    let owned = fs::canonicalize(owned).map_err(|_| "directory")?;
    let mut marker = OpenOptions::new()
        .write(true)
        .create_new(true)
        .open(owned.join(".capacity-owner"))
        .map_err(|_| "marker")?;
    marker.write_all(owner.as_bytes()).map_err(|_| "marker")?;
    marker.sync_all().map_err(|_| "marker")?;
    drop(marker);
    let path = owned.join("stories.sqlite");
    let host = locallore_workspace::open(&path, false).map_err(|_| "open")?;
    let workspace = call(&host, json!({"op":"workspace"}));
    require(
        workspace["status"] == "ok" && workspace["data"]["database_schema_version"] == 3,
        "schema3",
    )?;
    let created = call(&host, json!({"op":"create","seed":"lantern-quay-v1"}));
    require(created["status"] == "ok", "create")?;
    let session = created["data"]["session"].as_str().ok_or("session")?;
    let scope = &created["data"]["scope"];
    let before = snapshot(&host, session, scope, 0);
    require(
        before["status"] == "ok"
            && before["data"]["inventory"]["potion"]["owner"] == "player"
            && before["data"]["receipts"]
                .as_array()
                .is_some_and(Vec::is_empty),
        "initial_snapshot",
    )?;
    let turn = "00000000-0000-4000-8000-000000000099";
    let request = json!({"version":1,"scope":scope,"turn":turn,"expected_revision":0,
        "intent":{"kind":"actions","value":[{"op":"give","item":"potion","to":"mira","quantity":1}]}});
    phase(
        &call(
            &host,
            json!({"op":"submit","session":session,"request":request,"mode":"accepted"}),
        ),
        "queued",
        "submit",
    )?;
    phase(
        &op(&host, session, scope, turn, "prepare"),
        "ready",
        "prepare",
    )?;
    let fill = match helper(python, &owned, &owner, "fill") {
        Ok(report) => report,
        Err("helper_ownership_unknown") => return Err("helper_ownership_unknown"),
        Err(_) => {
            // The child is terminal, but filling may have created its owned pad
            // before failing. Attempt only fixed-table cleanup; never resume Host.
            return Err(if helper(python, &owned, &owner, "remove").is_ok() {
                "fill_failed_owned_padding_removed"
            } else {
                "fill_failed_cleanup_unproven"
            });
        }
    };
    let failed = (|| {
        require(
            fill["initial_pages"] == 17
                && fill["pages"] == 32
                && fill["free_pages"] == 0
                && fill["rows"] == 14
                && fill["insert_attempts"] == 15
                && fill["sqlite_full"] == true,
            "measured_fill_profile",
        )?;
        require(
            matches!(locallore_workspace::open(&path, false), Err(error) if error == "SchemaMismatch"),
            "extra_schema_rejected",
        )?;
        for _ in 0..2 {
            let response = op(&host, session, scope, turn, "commit");
            require(
                response["status"] == "rejected" && response["error"] == "Full",
                "commit_full",
            )?;
            phase(
                &op(&host, session, scope, turn, "turn_status"),
                "ready",
                "retained_ready",
            )?;
            require(
                snapshot(&host, session, scope, 0) == before,
                "unchanged_snapshot",
            )?;
        }
        if cancel {
            phase(
                &op(&host, session, scope, turn, "cancel"),
                "cancelled",
                "cancel_while_full",
            )?;
            phase(
                &op(&host, session, scope, turn, "turn_status"),
                "cancelled",
                "cancelled_key",
            )?;
            require(
                snapshot(&host, session, scope, 0) == before,
                "cancel_snapshot",
            )?;
        }
        Ok(())
    })();
    // Both one-shot child processes must terminate before any following Host call.
    // Even a native assertion failure attempts to remove only the owned padding.
    let removed = helper(python, &owned, &owner, "remove");
    if failed.is_err() && removed.is_err() {
        return Err("native_failure_and_cleanup_failure");
    }
    failed?;
    let removed = removed?;
    require(
        removed["initial_pages"] == 32
            && removed["pages"] == 32
            && removed["free_pages"] == 15
            && removed["rows_removed"] == 14
            && removed["schema_restored"] == true,
        "measured_relief_profile",
    )?;
    if cancel {
        phase(
            &op(&host, session, scope, turn, "commit"),
            "cancelled",
            "terminal_after_relief",
        )?;
        require(
            snapshot(&host, session, scope, 0) == before,
            "cancel_relief_snapshot",
        )?;
        drop(host);
        let reopened = locallore_workspace::open(&path, false).map_err(|_| "strict_reopen")?;
        let resumed = call(&reopened, json!({"op":"resume","scope":scope}));
        require(
            resumed["status"] == "ok" && resumed["data"]["revision"] == 0,
            "cancel_resume",
        )?;
        let session = resumed["data"]["session"]
            .as_str()
            .ok_or("resume_session")?;
        phase(
            &op(&reopened, session, scope, turn, "turn_status"),
            "cancelled",
            "reopened_cancelled_key",
        )?;
        phase(
            &op(&reopened, session, scope, turn, "commit"),
            "cancelled",
            "reopened_terminal",
        )?;
        require(
            snapshot(&reopened, session, scope, 0) == before,
            "reopened_cancel_snapshot",
        )?;
        return Ok(
            json!({"version":2,"database_schema_version":3,"status":"passed","prefix":0,"ceiling_pages":32,"fill":fill,"remove":removed,
            "extra_schema_rejected":true,"full_commits":2,"cancelled_while_full":true,
            "player_snapshot_unchanged_after_full":true,"original_key_terminal_after_relief":true,
            "post_relief_submits":0,"post_relief_prepares":0,"accepted_receipts":0,"revision":0,
            "same_key_reopened":true,"physical_enospc_proven":false,"real_model_proven":false}),
        );
    }
    phase(
        &op(&host, session, scope, turn, "turn_status"),
        "ready",
        "ready_after_relief",
    )?;
    let committed = op(&host, session, scope, turn, "commit");
    phase(&committed, "committed", "same_key_commit")?;
    require(
        op(&host, session, scope, turn, "commit") == committed,
        "idempotent_commit",
    )?;
    require(
        op(&host, session, scope, turn, "turn_status") == committed,
        "stored_receipt",
    )?;
    let accepted = snapshot(&host, session, scope, 1);
    require(
        accepted["status"] == "ok"
            && accepted["data"]["inventory"].get("potion").is_none()
            && accepted["data"]["receipts"]
                .as_array()
                .is_some_and(|v| v.len() == 1),
        "accepted_snapshot",
    )?;
    drop(host);
    let reopened = locallore_workspace::open(&path, false).map_err(|_| "strict_reopen")?;
    let resumed = call(&reopened, json!({"op":"resume","scope":scope}));
    require(
        resumed["status"] == "ok" && resumed["data"]["revision"] == 1,
        "resume",
    )?;
    let session = resumed["data"]["session"]
        .as_str()
        .ok_or("resume_session")?;
    require(
        op(&reopened, session, scope, turn, "turn_status") == committed,
        "reopened_key",
    )?;
    require(
        op(&reopened, session, scope, turn, "commit") == committed,
        "reopened_idempotence",
    )?;
    require(
        snapshot(&reopened, session, scope, 1) == accepted,
        "reopened_snapshot",
    )?;
    Ok(
        json!({"version":2,"database_schema_version":3,"status":"passed","prefix":0,"ceiling_pages":32,"fill":fill,"remove":removed,
        "extra_schema_rejected":true,"full_commits":2,"player_snapshot_unchanged_after_full":true,
        "same_live_owner_ready_key_accepted":true,"post_relief_submits":0,"post_relief_prepares":0,
        "accepted_receipts":1,"revision":1,"same_key_reopened":true,
        "physical_enospc_proven":false,"real_model_proven":false}),
    )
}
fn main() {
    let mut directory = None;
    let mut python = None;
    let mut cancel = false;
    let mut args = std::env::args().skip(1);
    while let Some(argument) = args.next() {
        match argument.as_str() {
            "--directory" => directory = args.next().map(PathBuf::from),
            "--python" => python = args.next().map(PathBuf::from),
            "--cancel" => cancel = true,
            _ => {
                eprintln!("capacity_relief_probe: invalid_arguments");
                std::process::exit(2);
            }
        }
    }
    let result = directory.ok_or("directory_argument").and_then(|directory| {
        python
            .ok_or("python_argument")
            .and_then(|python| run(&directory, &python, cancel))
    });
    match result {
        Ok(report) => println!("{report}"),
        Err(stage) => {
            eprintln!("{}", json!({"version":2,"status":"failed","stage":stage}));
            std::process::exit(1);
        }
    }
}
