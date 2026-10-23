// Copyright 2026 LocalLore contributors. SPDX-License-Identifier: Apache-2.0
//! Independent M03.03 ownership regressions through the public byte boundary.
use locallore::{
    contracts::{Command, Intent},
    engine::Engine,
};
use locallore_android::{Registry, MAX_OUTPUT};
use serde_json::{json, Value};
use std::{
    sync::Arc,
    thread,
    time::{Duration, Instant},
};

fn call(registry: &Registry, handle: u64, control: Value) -> Value {
    let bytes = registry.call(handle, &serde_json::to_vec(&control).unwrap());
    assert!(bytes.len() <= MAX_OUTPUT);
    serde_json::from_slice(&bytes).unwrap()
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

fn begin(registry: &Registry, handle: u64, turn: &str, mode: &str) -> Value {
    call(
        registry,
        handle,
        json!({"version":1,"op":"begin","request":request(turn),"mode":mode}),
    )
}

fn control(registry: &Registry, handle: u64, operation: u64, op: &str) -> Value {
    call(
        registry,
        handle,
        json!({"version":1,"op":op,"operation":operation}),
    )
}

fn stats(registry: &Registry) -> Value {
    call(registry, 0, json!({"version":1,"op":"stats"}))
}

fn assert_released(registry: &Registry) {
    let value = stats(registry);
    for key in [
        "live_sessions",
        "retained_sessions",
        "operations",
        "workers",
    ] {
        assert_eq!(value[key], 0, "{key}: {value}");
    }
}

#[test]
fn wrong_thread_begin_and_commit_cannot_allocate_or_mutate_but_destroy_releases() {
    let registry = Arc::new(Registry::default());
    let created = call(&registry, 0, json!({"version":1,"op":"create"}));
    let handle = created["handle"].as_u64().unwrap();
    let initial = created["snapshot"].clone();

    let other = registry.clone();
    let rejected = thread::spawn(move || begin(&other, handle, "foreign-begin", "accepted"))
        .join()
        .unwrap();
    assert_eq!(rejected["error"], "WrongThread");
    assert_eq!(stats(&registry)["operations"], 0);

    let operation = begin(&registry, handle, "owner-begin", "accepted")["operation"]
        .as_u64()
        .unwrap();
    let other = registry.clone();
    assert_eq!(
        thread::spawn(move || control(&other, handle, operation, "run"))
            .join()
            .unwrap()["status"],
        "prepared"
    );

    let other = registry.clone();
    assert_eq!(
        thread::spawn(move || control(&other, handle, operation, "commit"))
            .join()
            .unwrap()["error"],
        "WrongThread"
    );
    assert_eq!(
        call(&registry, handle, json!({"version":1,"op":"snapshot"}))["snapshot"],
        initial
    );
    assert_eq!(
        control(&registry, handle, operation, "commit")["status"],
        "accepted"
    );

    let other = registry.clone();
    assert_eq!(
        thread::spawn(move || call(&other, handle, json!({"version":1,"op":"destroy"})))
            .join()
            .unwrap()["status"],
        "closed"
    );
    assert_released(&registry);
}

#[test]
fn cancelled_operation_cannot_interfere_with_replacement_in_same_session() {
    let registry = Arc::new(Registry::default());
    let created = call(&registry, 0, json!({"version":1,"op":"create"}));
    let handle = created["handle"].as_u64().unwrap();
    let old = begin(&registry, handle, "cancelled", "delayed")["operation"]
        .as_u64()
        .unwrap();
    let other = registry.clone();
    let worker = thread::spawn(move || control(&other, handle, old, "run"));
    let until = Instant::now() + Duration::from_secs(2);
    while stats(&registry)["workers"] == 0 {
        assert!(Instant::now() < until, "worker did not enter");
        thread::yield_now();
    }
    assert_eq!(
        control(&registry, handle, old, "cancel")["status"],
        "cancelled"
    );

    // Do not await the old worker before starting the replacement. A cancelled
    // caller can still deliver its captured operation ID after this point.
    let new = begin(&registry, handle, "replacement", "accepted")["operation"]
        .as_u64()
        .unwrap();
    assert!(new > old);
    assert_eq!(
        control(&registry, handle, old, "cancel")["error"],
        "InvalidOperation"
    );
    assert_eq!(
        control(&registry, handle, old, "commit")["error"],
        "InvalidOperation"
    );
    let other = registry.clone();
    assert_eq!(
        thread::spawn(move || control(&other, handle, old, "run"))
            .join()
            .unwrap()["error"],
        "InvalidOperation"
    );
    assert_eq!(worker.join().unwrap()["error"], "Cancelled");

    let other = registry.clone();
    assert_eq!(
        thread::spawn(move || control(&other, handle, new, "run"))
            .join()
            .unwrap()["status"],
        "prepared"
    );
    let accepted = control(&registry, handle, new, "commit");
    assert_eq!(accepted["status"], "accepted");
    assert_eq!(accepted["snapshot"]["revision"], 1);
    assert_eq!(accepted["snapshot"]["events"], 1);
    assert_eq!(accepted["snapshot"]["potion_owner"], "Mira");
    assert_eq!(accepted["snapshot"]["sable_observations"], 0);
    call(&registry, handle, json!({"version":1,"op":"destroy"}));
    assert_released(&registry);
}
