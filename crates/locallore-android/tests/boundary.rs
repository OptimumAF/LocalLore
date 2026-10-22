// Copyright 2026 LocalLore contributors. SPDX-License-Identifier: Apache-2.0
//! Public byte-boundary tests: no access to registry internals or JNI-only scaffolding.
use locallore::{
    contracts::{Command, Intent},
    engine::Engine,
};
use locallore_android::{Registry, MAX_INPUT, MAX_OUTPUT};
use serde_json::{json, Value};
use std::{
    sync::Arc,
    thread,
    time::{Duration, Instant},
};

fn call(registry: &Registry, handle: u64, control: Value) -> Value {
    let output = registry.call(handle, &serde_json::to_vec(&control).unwrap());
    assert!(output.len() <= MAX_OUTPUT);
    serde_json::from_slice(&output).unwrap()
}
fn create(registry: &Registry) -> u64 {
    let reply = call(registry, 0, json!({"version":1,"op":"create"}));
    assert_eq!(reply["status"], "session", "{reply}");
    reply["handle"].as_u64().unwrap()
}
fn request(turn: &str) -> Value {
    let engine = Engine::new(
        serde_json::from_str(include_str!("../../../fixtures/lantern_quay.json")).unwrap(),
    )
    .unwrap();
    serde_json::to_value(engine.request(
        turn,
        Intent::Actions(vec![Command::Give {
            item: "potion".into(),
            to: "mira".into(),
            quantity: 1,
        }]),
    ))
    .unwrap()
}
fn begin(registry: &Registry, handle: u64, request: Value, mode: &str) -> Value {
    call(
        registry,
        handle,
        json!({"version":1,"op":"begin","request":request,"mode":mode}),
    )
}
fn snapshot(registry: &Registry, handle: u64) -> Value {
    call(registry, handle, json!({"version":1,"op":"snapshot"}))["snapshot"].clone()
}
fn operation(registry: &Registry, handle: u64, turn: &str, mode: &str) -> u64 {
    let reply = begin(registry, handle, request(turn), mode);
    assert_eq!(reply["status"], "started", "{reply}");
    reply["operation"].as_u64().unwrap()
}
fn run(registry: &Arc<Registry>, handle: u64, op: u64) -> thread::JoinHandle<Value> {
    let registry = registry.clone();
    thread::spawn(move || {
        call(
            &registry,
            handle,
            json!({"version":1,"op":"run","operation":op}),
        )
    })
}
fn workers(registry: &Registry) -> u64 {
    call(registry, 0, json!({"version":1,"op":"stats"}))["workers"]
        .as_u64()
        .unwrap()
}
fn await_worker(registry: &Registry) {
    let until = Instant::now() + Duration::from_secs(2);
    while workers(registry) == 0 {
        assert!(Instant::now() < until, "worker did not enter");
        thread::yield_now();
    }
}
fn assert_released(registry: &Registry) {
    let stats = call(registry, 0, json!({"version":1,"op":"stats"}));
    for key in [
        "live_sessions",
        "retained_sessions",
        "operations",
        "workers",
    ] {
        assert_eq!(stats[key], 0, "{key}: {stats}");
    }
}

#[test]
fn accepted_draft_requires_explicit_commit_and_duplicates_do_not_reapply() {
    let registry = Arc::new(Registry::default());
    let handle = create(&registry);
    let initial = snapshot(&registry, handle);
    assert_eq!(initial["potion_owner"], "You");
    let op = operation(&registry, handle, "gift", "accepted");
    assert_eq!(
        run(&registry, handle, op).join().unwrap()["status"],
        "prepared"
    );
    assert_eq!(
        snapshot(&registry, handle),
        initial,
        "prepared draft changed canon"
    );
    let accepted = call(
        &registry,
        handle,
        json!({"version":1,"op":"commit","operation":op}),
    );
    assert_eq!(accepted["status"], "accepted");
    assert_eq!(accepted["snapshot"]["potion_owner"], "Mira");
    assert_eq!(
        accepted["snapshot"]["sable_observations"],
        initial["sable_observations"]
    );
    assert_eq!(
        call(
            &registry,
            handle,
            json!({"version":1,"op":"commit","operation":op})
        ),
        accepted
    );
    assert_eq!(
        call(
            &registry,
            handle,
            json!({"version":1,"op":"cancel","operation":op})
        )["status"],
        "already_committed"
    );
    let repeat = operation(&registry, handle, "gift", "failed");
    assert_eq!(
        run(&registry, handle, repeat).join().unwrap()["status"],
        "prepared",
        "recorded retry called failing provider"
    );
    let retried = call(
        &registry,
        handle,
        json!({"version":1,"op":"commit","operation":repeat}),
    );
    assert_eq!(retried["snapshot"], accepted["snapshot"]);
    assert_eq!(retried["receipt"], accepted["receipt"]);
    call(&registry, handle, json!({"version":1,"op":"destroy"}));
    assert_released(&registry);
}

#[test]
fn strict_serialization_handles_versions_sizes_and_scope_fail_closed() {
    let registry = Registry::default();
    let handle = create(&registry);
    let initial = snapshot(&registry, handle);
    for bytes in [
        b"not json".as_slice(),
        b"\xff",
        br#"{"op":"snapshot","version":1,"extra":true}"#,
        br#"{"op":"execute_sql","version":1}"#,
    ] {
        let reply: Value = serde_json::from_slice(&registry.call(handle, bytes)).unwrap();
        assert_eq!(reply["error"], "Malformed", "{reply}");
    }
    assert_eq!(
        call(&registry, handle, json!({"version":2,"op":"snapshot"}))["error"],
        "Version"
    );
    let oversized: Value =
        serde_json::from_slice(&registry.call(handle, &vec![b' '; MAX_INPUT + 1])).unwrap();
    assert_eq!(oversized["error"], "TooLarge");
    let mut wrong = request("wrong-story");
    wrong["scope"]["story"] = json!("another-story");
    assert_eq!(
        begin(&registry, handle, wrong, "accepted")["error"],
        "Scope"
    );
    let mut stale = request("stale");
    stale["expected_revision"] = json!(99);
    assert_eq!(
        begin(&registry, handle, stale, "accepted")["error"],
        "Stale"
    );
    assert_eq!(snapshot(&registry, handle), initial);
    call(&registry, handle, json!({"version":1,"op":"destroy"}));
    assert_released(&registry);
}

#[test]
fn failed_provider_modes_cannot_change_state_or_commit() {
    let registry = Arc::new(Registry::default());
    let handle = create(&registry);
    let initial = snapshot(&registry, handle);
    for (mode, error) in [
        ("malformed", "Malformed"),
        ("rejected", "Agency"),
        ("failed", "Provider"),
    ] {
        let op = operation(&registry, handle, mode, mode);
        assert_eq!(run(&registry, handle, op).join().unwrap()["error"], error);
        assert_eq!(
            call(
                &registry,
                handle,
                json!({"version":1,"op":"commit","operation":op})
            )["error"],
            "InvalidOperation"
        );
        assert_eq!(snapshot(&registry, handle), initial);
    }
    call(&registry, handle, json!({"version":1,"op":"destroy"}));
    assert_released(&registry);
}

#[test]
fn owner_thread_enforcement_and_cross_session_operation_ids() {
    let registry = Arc::new(Registry::default());
    let first = create(&registry);
    let second = create(&registry);
    let op = operation(&registry, first, "gift", "accepted");
    assert_eq!(
        call(
            &registry,
            first,
            json!({"version":1,"op":"run","operation":op})
        )["error"],
        "WrongThread"
    );
    let other = registry.clone();
    assert_eq!(
        thread::spawn(move || call(&other, first, json!({"version":1,"op":"snapshot"})))
            .join()
            .unwrap()["error"],
        "WrongThread"
    );
    assert_eq!(
        call(
            &registry,
            second,
            json!({"version":1,"op":"commit","operation":op})
        )["error"],
        "InvalidOperation"
    );
    assert_eq!(
        run(&registry, second, op).join().unwrap()["error"],
        "InvalidOperation"
    );
    call(&registry, first, json!({"version":1,"op":"destroy"}));
    call(&registry, second, json!({"version":1,"op":"destroy"}));
    assert_released(&registry);
}

#[test]
fn cancel_running_and_prepared_work_preserves_canon_and_releases_workers() {
    let registry = Arc::new(Registry::default());
    let handle = create(&registry);
    let initial = snapshot(&registry, handle);
    for iteration in 0..12 {
        let op = operation(&registry, handle, &format!("cancel-{iteration}"), "delayed");
        let worker = run(&registry, handle, op);
        await_worker(&registry);
        assert_eq!(
            run(&registry, handle, op).join().unwrap()["error"],
            "InvalidOperation",
            "duplicate worker entered"
        );
        assert_eq!(
            call(
                &registry,
                handle,
                json!({"version":1,"op":"cancel","operation":op})
            )["status"],
            "cancelled"
        );
        assert_eq!(worker.join().unwrap()["error"], "Cancelled");
        assert_eq!(workers(&registry), 0);
        assert_eq!(
            call(
                &registry,
                handle,
                json!({"version":1,"op":"commit","operation":op})
            )["error"],
            "Cancelled"
        );
        assert_eq!(snapshot(&registry, handle), initial);
    }
    let op = operation(&registry, handle, "prepared-cancel", "accepted");
    assert_eq!(
        run(&registry, handle, op).join().unwrap()["status"],
        "prepared"
    );
    call(
        &registry,
        handle,
        json!({"version":1,"op":"cancel","operation":op}),
    );
    assert_eq!(
        call(
            &registry,
            handle,
            json!({"version":1,"op":"commit","operation":op})
        )["error"],
        "Cancelled"
    );
    assert_eq!(snapshot(&registry, handle), initial);
    call(&registry, handle, json!({"version":1,"op":"destroy"}));
    assert_released(&registry);
}

#[test]
fn destroy_running_work_invalidates_handle_and_new_session_stays_independent() {
    let registry = Arc::new(Registry::default());
    let old = create(&registry);
    let op = operation(&registry, old, "destroyed", "delayed");
    let worker = run(&registry, old, op);
    await_worker(&registry);
    assert_eq!(
        call(&registry, old, json!({"version":1,"op":"destroy"}))["status"],
        "closed"
    );
    let new = create(&registry);
    assert!(new > old);
    assert_eq!(
        call(&registry, old, json!({"version":1,"op":"snapshot"}))["error"],
        "InvalidHandle"
    );
    assert_eq!(
        call(&registry, old, json!({"version":1,"op":"destroy"}))["error"],
        "InvalidHandle"
    );
    assert_eq!(worker.join().unwrap()["error"], "Cancelled");
    assert_eq!(snapshot(&registry, new)["potion_owner"], "You");
    call(&registry, new, json!({"version":1,"op":"destroy"}));
    assert_released(&registry);
}

#[test]
fn session_limit_rejects_excess_and_cleanup_restores_capacity() {
    let registry = Registry::default();
    let handles: Vec<_> = (0..32).map(|_| create(&registry)).collect();
    assert_eq!(
        call(&registry, 0, json!({"version":1,"op":"create"}))["error"],
        "SessionLimit"
    );
    for handle in handles {
        call(&registry, handle, json!({"version":1,"op":"destroy"}));
    }
    assert_released(&registry);
    let new = create(&registry);
    call(&registry, new, json!({"version":1,"op":"destroy"}));
    assert_released(&registry);
}

#[test]
fn racing_cancel_and_commit_have_one_observable_outcome() {
    for index in 0..20 {
        let registry = Arc::new(Registry::default());
        let handle = create(&registry);
        let initial = snapshot(&registry, handle);
        let op = operation(&registry, handle, &format!("race-{index}"), "accepted");
        assert_eq!(
            run(&registry, handle, op).join().unwrap()["status"],
            "prepared"
        );
        let gate = Arc::new(std::sync::Barrier::new(2));
        let other = registry.clone();
        let ready = gate.clone();
        let cancellation = thread::spawn(move || {
            ready.wait();
            call(
                &other,
                handle,
                json!({"version":1,"op":"cancel","operation":op}),
            )
        });
        gate.wait();
        let committed = call(
            &registry,
            handle,
            json!({"version":1,"op":"commit","operation":op}),
        );
        let cancelled = cancellation.join().unwrap();
        if committed["status"] == "accepted" {
            assert_eq!(cancelled["status"], "already_committed");
            assert_eq!(snapshot(&registry, handle), committed["snapshot"]);
            assert_eq!(snapshot(&registry, handle)["potion_owner"], "Mira");
        } else {
            assert_eq!(committed["error"], "Cancelled");
            assert_eq!(cancelled["status"], "cancelled");
            assert_eq!(snapshot(&registry, handle), initial);
        }
        call(&registry, handle, json!({"version":1,"op":"destroy"}));
        assert_released(&registry);
    }
}
