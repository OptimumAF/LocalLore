// Copyright 2026 LocalLore contributors. SPDX-License-Identifier: Apache-2.0
//! Explicit synthetic Full -> free test-owned pages -> same-key acceptance proof.
//! Build in a separate target with LIBSQLITE3_FLAGS=-DSQLITE_MAX_PAGE_COUNT=32.
//! Usage: --directory <fresh parent> --python <Python executable> [--cancel].
//! Optional --helper-fault selects only the fixed synthetic child fault cases.
//! Retains synthetic files locally; neither runtime changes nor production hooks.
use locallore::host::Host;
use serde_json::{json, Value};
use std::{
    fs::{self, OpenOptions},
    io::Write,
    path::{Path, PathBuf},
    process::{Child, Command, ExitStatus, Stdio},
    sync::atomic::{AtomicU64, Ordering},
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
static HOST_CALLS: AtomicU64 = AtomicU64::new(0);
static WORKSPACE_OPENS: AtomicU64 = AtomicU64::new(0);
static HELPER_STARTS: AtomicU64 = AtomicU64::new(0);

fn open_workspace(path: &Path) -> Result<Host, String> {
    WORKSPACE_OPENS.fetch_add(1, Ordering::SeqCst);
    locallore_workspace::open(path, false)
}
fn call(host: &Host, command: Value) -> Value {
    HOST_CALLS.fetch_add(1, Ordering::SeqCst);
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
#[derive(Clone, Copy, Default)]
struct ChildState {
    started: bool,
    terminal: bool,
    kill_requested: bool,
    kill_succeeded: bool,
    reaped: bool,
    exit_code: Option<i32>,
}
impl ChildState {
    fn exited(status: ExitStatus) -> Self {
        Self {
            started: true,
            terminal: true,
            reaped: true,
            exit_code: status.code(),
            ..Self::default()
        }
    }
    fn report(self) -> Value {
        json!({"started":self.started,"terminal":self.terminal,"kill_requested":self.kill_requested,
            "kill_succeeded":self.kill_succeeded,"reaped":self.reaped,"exit_code":self.exit_code})
    }
}
struct HelperFailure {
    category: &'static str,
    child: ChildState,
    reported_stage: Option<&'static str>,
}
struct HelperCompleted {
    report: Value,
    child: ChildState,
}
impl HelperFailure {
    fn new(category: &'static str, child: ChildState) -> Self {
        Self {
            category,
            child,
            reported_stage: None,
        }
    }
    fn not_started(category: &'static str) -> Self {
        Self::new(
            category,
            ChildState {
                terminal: true,
                ..ChildState::default()
            },
        )
    }
    fn report(&self) -> Value {
        json!({"category":self.category,"child":self.child.report(),"reported_stage":self.reported_stage})
    }
}
fn stop_helper(child: &mut Child) -> ChildState {
    // Requesting kill is not proof. Only observed terminal try_wait owns a reap.
    let kill_succeeded = child.kill().is_ok();
    let deadline = Instant::now() + Duration::from_secs(2);
    loop {
        match child.try_wait() {
            Ok(Some(status)) => {
                return ChildState {
                    kill_requested: true,
                    kill_succeeded,
                    ..ChildState::exited(status)
                }
            }
            Ok(None) if Instant::now() < deadline => std::thread::sleep(Duration::from_millis(10)),
            _ => {
                return ChildState {
                    started: true,
                    kill_requested: true,
                    kill_succeeded,
                    ..ChildState::default()
                }
            }
        }
    }
}
fn helper(
    python: &Path,
    directory: &Path,
    owner: &str,
    action: &str,
    fault: Option<&str>,
) -> Result<HelperCompleted, HelperFailure> {
    let stdout = directory.join(format!("{action}.stdout"));
    let stderr = directory.join(format!("{action}.stderr"));
    let output_file = OpenOptions::new()
        .write(true)
        .create_new(true)
        .open(&stdout)
        .map_err(|_| HelperFailure::not_started("helper_output"))?;
    let error_file = OpenOptions::new()
        .write(true)
        .create_new(true)
        .open(&stderr)
        .map_err(|_| HelperFailure::not_started("helper_output"))?;
    let script =
        Path::new(env!("CARGO_MANIFEST_DIR")).join("../../scripts/capacity_padding_probe.py");
    let mut command = Command::new(python);
    command
        .arg(script)
        .arg("--directory")
        .arg(directory)
        .arg("--owner")
        .arg(owner)
        .arg("--action")
        .arg(action);
    if let Some(fault) = fault {
        command.arg("--fault").arg(fault);
    }
    let mut child = command
        .stdin(Stdio::null())
        .stdout(output_file)
        .stderr(error_file)
        .spawn()
        .map_err(|_| HelperFailure::not_started("helper_start"))?;
    HELPER_STARTS.fetch_add(1, Ordering::SeqCst);
    let deadline = Instant::now() + Duration::from_secs(10);
    let status = loop {
        let overflow = [&stdout, &stderr]
            .into_iter()
            .any(|path| fs::metadata(path).map_or(true, |metadata| metadata.len() > 4096));
        if overflow {
            return Err(HelperFailure::new(
                "helper_output_bound",
                stop_helper(&mut child),
            ));
        }
        match child.try_wait() {
            Ok(Some(status)) => break status,
            Ok(None) if Instant::now() < deadline => std::thread::sleep(Duration::from_millis(10)),
            Ok(None) => {
                return Err(HelperFailure::new(
                    "helper_deadline",
                    stop_helper(&mut child),
                ))
            }
            Err(_) => return Err(HelperFailure::new("helper_wait", stop_helper(&mut child))),
        }
    };
    let terminal = ChildState::exited(status);
    let length = fs::metadata(&stdout)
        .map_err(|_| HelperFailure::new("helper_output", terminal))?
        .len();
    if length > 4096 {
        return Err(HelperFailure::new("helper_output_bound", terminal));
    }
    if fs::metadata(&stderr)
        .map_err(|_| HelperFailure::new("helper_output", terminal))?
        .len()
        != 0
    {
        return Err(HelperFailure::new("helper_stderr", terminal));
    }
    let bytes = fs::read(stdout).map_err(|_| HelperFailure::new("helper_output", terminal))?;
    let report: Value =
        serde_json::from_slice(&bytes).map_err(|_| HelperFailure::new("helper_json", terminal))?;
    if !(status.success()
        && report["version"] == 2
        && report["database_schema_version"] == 3
        && report["schema_sha256"] == SCHEMA3_SHA256
        && report["status"] == "passed"
        && report["action"] == action)
    {
        let mut failure = HelperFailure::new("helper_result", terminal);
        failure.reported_stage = match report["stage"].as_str() {
            Some("injected_after_fill") => Some("injected_after_fill"),
            Some("injected_cleanup_refusal") => Some("injected_cleanup_refusal"),
            _ => None,
        };
        return Err(failure);
    }
    Ok(HelperCompleted {
        report,
        child: terminal,
    })
}
fn cleanup_allowed(failure: &HelperFailure) -> bool {
    failure.child.started && failure.child.terminal && failure.child.reaped
}
fn cleanup_report(result: &Result<HelperCompleted, HelperFailure>) -> Value {
    match result {
        Ok(completed) => {
            json!({"status":"restored","report":completed.report,"child":completed.child.report()})
        }
        Err(failure) => json!({"status":"failed","failure":failure.report()}),
    }
}
fn failed_fill(
    python: &Path,
    directory: &Path,
    owner: &str,
    failure: &HelperFailure,
    cleanup_fault: Option<&str>,
) -> Value {
    if !cleanup_allowed(failure) {
        return json!({"status":"not_started","reason":if failure.child.started {"ownership_unknown"} else {"fill_not_started"}});
    }
    cleanup_report(&helper(python, directory, owner, "remove", cleanup_fault))
}
fn fault_ready(directory: &Path, owner: &str, fault: &str) -> bool {
    let path = directory.join(".capacity-fault-ready");
    let Ok(metadata) = fs::symlink_metadata(&path) else {
        return false;
    };
    if !metadata.is_file() || metadata.file_type().is_symlink() || metadata.len() > 1024 {
        return false;
    }
    let Ok(bytes) = fs::read(path) else {
        return false;
    };
    let Ok(value) = serde_json::from_slice::<Value>(&bytes) else {
        return false;
    };
    value["version"] == 1
        && value["owner"] == owner
        && value["fault"] == fault
        && value["rows"] == 14
        && value["insert_attempts"] == 15
        && value["pages"] == 32
        && value["sqlite_full"] == true
}
fn run_fault(
    python: &Path,
    directory: &Path,
    owner: &str,
    fault: &str,
) -> Result<Value, &'static str> {
    let mut marker = OpenOptions::new()
        .write(true)
        .create_new(true)
        .open(directory.join(".capacity-fault"))
        .map_err(|_| "fault_marker")?;
    marker
        .write_all(format!("{owner}\n{fault}").as_bytes())
        .map_err(|_| "fault_marker")?;
    marker.sync_all().map_err(|_| "fault_marker")?;
    drop(marker);
    let calls_before = HOST_CALLS.load(Ordering::SeqCst);
    let probes_before = WORKSPACE_OPENS.load(Ordering::SeqCst);
    let helpers_before = HELPER_STARTS.load(Ordering::SeqCst);
    let failure = match helper(python, directory, owner, "fill", Some(fault)) {
        Ok(_) => return Err("fault_did_not_fail"),
        Err(failure) => failure,
    };
    // Unknown live ownership prohibits even a readiness read or another helper.
    let filled = cleanup_allowed(&failure) && fault_ready(directory, owner, fault);
    let cleanup = failed_fill(
        python,
        directory,
        owner,
        &failure,
        (fault == "cleanup-refusal").then_some("cleanup-refusal"),
    );
    let expected_category = match fault {
        "malformed" => "helper_json",
        "overflow" => "helper_output_bound",
        "timeout" => "helper_deadline",
        _ => "helper_result",
    };
    let expected_cleanup = if fault == "cleanup-refusal" {
        cleanup["status"] == "failed"
            && cleanup["failure"]["reported_stage"] == "injected_cleanup_refusal"
            && cleanup["failure"]["child"]["terminal"] == true
            && cleanup["failure"]["child"]["reaped"] == true
    } else {
        cleanup["status"] == "restored"
            && cleanup["child"]["terminal"] == true
            && cleanup["child"]["reaped"] == true
            && cleanup["report"]["rows_removed"] == 14
            && cleanup["report"]["free_pages"] == 15
            && cleanup["report"]["schema_restored"] == true
    };
    let host_calls = HOST_CALLS.load(Ordering::SeqCst) - calls_before;
    let probes = WORKSPACE_OPENS.load(Ordering::SeqCst) - probes_before;
    let helpers = HELPER_STARTS.load(Ordering::SeqCst) - helpers_before;
    let killed_if_required = !matches!(fault, "overflow" | "timeout")
        || (failure.child.kill_succeeded && failure.child.kill_requested);
    let passed = filled
        && failure.category == expected_category
        && (!matches!(fault, "after-fill" | "cleanup-refusal")
            || failure.reported_stage == Some("injected_after_fill"))
        && expected_cleanup
        && failure.child.terminal
        && failure.child.reaped
        && killed_if_required
        && host_calls == 0
        && probes == 0
        && helpers == 2;
    Ok(
        json!({"version":1,"scope":"host_synthetic_helper_fault_v1","database_schema_version":3,
        "status":if passed {"passed"} else {"failed"},"fault":fault,"ceiling_pages":32,
        "original_failure":failure.report(),"cleanup":cleanup,"actual_fill_observed":filled,
        "padding_rows":if filled {Some(14)} else {None},"fill_insert_attempts":if filled {Some(15)} else {None},
        "post_failure_host_calls":host_calls,"post_failure_workspace_opens":probes,
        "helper_children_started":helpers,"no_gameplay_acceptance_claimed":true,
        "physical_enospc_proven":false,"real_model_proven":false}),
    )
}
fn run(
    directory: &Path,
    python: &Path,
    cancel: bool,
    fault: Option<&str>,
) -> Result<Value, &'static str> {
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
    let host = open_workspace(&path).map_err(|_| "open")?;
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
    if let Some(fault) = fault {
        return run_fault(python, &owned, &owner, fault);
    }
    let calls_before = HOST_CALLS.load(Ordering::SeqCst);
    let fill = match helper(python, &owned, &owner, "fill", None) {
        Ok(completed) => completed.report,
        Err(failure) => {
            let cleanup = failed_fill(python, &owned, &owner, &failure, None);
            return Ok(json!({"version":2,"status":"failed","stage":"fill_helper",
                "original_failure":failure.report(),"cleanup":cleanup,
                "post_failure_host_calls":HOST_CALLS.load(Ordering::SeqCst)-calls_before}));
        }
    };
    let failed: Result<(), &'static str> = (|| {
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
            matches!(open_workspace(&path), Err(error) if error == "SchemaMismatch"),
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
    let removed = helper(python, &owned, &owner, "remove", None);
    if failed.is_err() || removed.is_err() {
        return Ok(
            json!({"version":2,"status":"failed","stage":"native_or_cleanup",
            "original_failure":failed.err(),"cleanup":cleanup_report(&removed)}),
        );
    }
    let removed = removed.map_err(|failure| failure.category)?.report;
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
        let reopened = open_workspace(&path).map_err(|_| "strict_reopen")?;
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
    let reopened = open_workspace(&path).map_err(|_| "strict_reopen")?;
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
    let mut fault = None;
    let mut args = std::env::args().skip(1);
    while let Some(argument) = args.next() {
        match argument.as_str() {
            "--directory" => directory = args.next().map(PathBuf::from),
            "--python" => python = args.next().map(PathBuf::from),
            "--cancel" => cancel = true,
            "--helper-fault" => {
                fault = args.next();
                if !matches!(
                    fault.as_deref(),
                    Some("malformed" | "overflow" | "timeout" | "after-fill" | "cleanup-refusal")
                ) {
                    eprintln!("capacity_relief_probe: invalid_fault");
                    std::process::exit(2);
                }
            }
            _ => {
                eprintln!("capacity_relief_probe: invalid_arguments");
                std::process::exit(2);
            }
        }
    }
    if cancel && fault.is_some() {
        eprintln!("capacity_relief_probe: incompatible_arguments");
        std::process::exit(2);
    }
    let result = directory.ok_or("directory_argument").and_then(|directory| {
        python
            .ok_or("python_argument")
            .and_then(|python| run(&directory, &python, cancel, fault.as_deref()))
    });
    match result {
        Ok(report) => {
            println!("{report}");
            if report["status"] != "passed" {
                std::process::exit(1);
            }
        }
        Err(stage) => {
            eprintln!("{}", json!({"version":2,"status":"failed","stage":stage}));
            std::process::exit(1);
        }
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn cleanup_requires_started_terminal_reaped_child_not_kill_request() {
        for state in [
            ChildState::default(),
            ChildState {
                started: true,
                ..ChildState::default()
            },
            ChildState {
                started: true,
                kill_requested: true,
                kill_succeeded: true,
                ..ChildState::default()
            },
            ChildState {
                started: true,
                terminal: true,
                ..ChildState::default()
            },
        ] {
            assert!(!cleanup_allowed(&HelperFailure::new(
                "helper_deadline",
                state
            )));
        }
        assert!(cleanup_allowed(&HelperFailure::new(
            "helper_json",
            ChildState {
                started: true,
                terminal: true,
                reaped: true,
                ..ChildState::default()
            }
        )));
    }

    #[test]
    fn unknown_ownership_never_starts_cleanup_even_for_real_paths() {
        let before = HELPER_STARTS.load(Ordering::SeqCst);
        let failure = HelperFailure::new(
            "helper_deadline",
            ChildState {
                started: true,
                kill_requested: true,
                ..ChildState::default()
            },
        );
        let result = failed_fill(
            Path::new("unused"),
            Path::new("unused"),
            "unused",
            &failure,
            None,
        );
        assert_eq!(result["reason"], "ownership_unknown");
        assert_eq!(HELPER_STARTS.load(Ordering::SeqCst), before);
        assert_eq!(failure.report()["category"], "helper_deadline");
        assert_eq!(failure.report()["child"]["reaped"], false);
    }
}
