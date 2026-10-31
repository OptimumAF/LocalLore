// Copyright 2026 LocalLore contributors. SPDX-License-Identifier: Apache-2.0
//! Independent packet-A FIRST. Root registers at crate root under test +
//! engine-adapter + development-worker. Frozen against e5cd498d/b380f161.
//! SOURCE-ONLY/UNRUN; absent seams/binary are SETUP_UNRUN, not behavioral RED.
//! Real parser/native owner plus fixed synthetic fixture; no model or UI proof.
#![cfg(all(test, feature = "engine-adapter", feature = "development-worker"))]

use super::*;
use crate::adapter::{author_fixture, AuthorFixtureCase};

fn reply(text: &str, tokens: u64) -> Value {
    json!({"version":1,"id":17,"status":"completed","error":null,"text":text,
        "metrics":{"load_ms":0,"prefill_ms":0,"decode_ms":0,"total_ms":0,
        "input_tokens":0,"output_tokens":tokens,"model_loads":1,
        "contexts_created":1,"abort_callbacks":0}})
}
fn parsed(value: &Value, bounds: ReplyBounds) -> Result<Reply, Error> {
    parse_reply(&serde_json::to_vec(value).unwrap(), 17, bounds)
}
fn author_generation(tokens: u16) -> Generation {
    Generation {
        role: Role::Author,
        prompt: "Fixed synthetic Author request.".into(),
        schema: Some(locallore::story_authoring::proposal_schema()),
        max_tokens: tokens,
    }
}
fn owned_setup(
    result: Result<(LocalRuntime, std::path::PathBuf), OwnedStartFailure>,
) -> (LocalRuntime, std::path::PathBuf) {
    match result {
        Ok(value) => value,
        Err(OwnedStartFailure::BeforeChild(_)) => panic!("SETUP_UNRUN native fixture unavailable"),
        Err(OwnedStartFailure::AfterChild { mut owner, .. }) => {
            let result = owner.terminate_and_reap();
            assert!(
                result.is_ok(),
                "SETUP_UNRUN partial native cleanup unresolved"
            );
            panic!("SETUP_UNRUN partial native fixture start");
        }
    }
}
fn load(owner: &mut LocalRuntime) -> Status {
    let initial = owner.status();
    if initial == Status::Unloaded && owner.load(|| false).is_err() {
        let result = owner.terminate_and_reap();
        assert!(result.is_ok(), "SETUP_UNRUN native load cleanup unresolved");
        panic!("SETUP_UNRUN native fixture load failed");
    }
    initial
}
fn cleanup(owner: &mut LocalRuntime) -> (Result<(), Error>, bool, bool) {
    let result = owner.terminate_and_reap();
    let terminal = owner.child.try_wait().is_ok_and(|v| v.is_some());
    (
        result,
        terminal,
        owner.writer.is_none() && owner.threads.is_empty(),
    )
}
fn cleaned(initial: Status, result: (Result<(), Error>, bool, bool)) {
    assert_eq!(initial, Status::Unloaded, "fixture starts unloaded");
    assert_eq!(
        result,
        (Ok(()), true, true),
        "positive exact-owner reap and pipe joins"
    );
}
fn author_owner() -> (LocalRuntime, std::path::PathBuf) {
    let (provider, shared, directory) = match author_fixture(None, AuthorFixtureCase::Completed) {
        Ok(value) => value,
        Err(OwnedStartFailure::BeforeChild(_)) => {
            panic!("SETUP_UNRUN Author native fixture unavailable")
        }
        Err(OwnedStartFailure::AfterChild { mut owner, .. }) => {
            let result = owner.terminate_and_reap();
            assert!(
                result.is_ok(),
                "SETUP_UNRUN Author partial cleanup unresolved"
            );
            panic!("SETUP_UNRUN Author partial start");
        }
    };
    drop(provider);
    let mutex = match Arc::try_unwrap(shared) {
        Ok(value) => value,
        Err(shared) => {
            let result = shared
                .lock()
                .unwrap_or_else(|p| p.into_inner())
                .terminate_and_reap();
            assert!(
                result.is_ok(),
                "SETUP_UNRUN unexpected fixture owner cleanup"
            );
            panic!("SETUP_UNRUN fixture unexpectedly retained runtime aliases");
        }
    };
    (
        mutex.into_inner().unwrap_or_else(|p| p.into_inner()),
        directory,
    )
}

#[test]
fn author_reply_exact_token_and_utf8_byte_budgets_are_operation_bound() {
    let maximum = ReplyBounds {
        output_tokens: 1024,
        text_bytes: 8192,
    };
    assert!(parsed(&reply(&"x".repeat(8192), 1024), maximum).is_ok());
    assert_eq!(
        parsed(&reply("", 1025), maximum).err(),
        Some(Error::Protocol)
    );
    assert_eq!(
        parsed(&reply(&"x".repeat(8193), 1024), maximum).err(),
        Some(Error::Protocol)
    );
    let small = ReplyBounds {
        output_tokens: 64,
        text_bytes: 3,
    };
    assert!(
        parsed(&reply("éx", 64), small).is_ok(),
        "UTF8 exact three bytes"
    );
    assert_eq!(parsed(&reply("éé", 64), small).err(), Some(Error::Protocol));
    assert_eq!(parsed(&reply("", 65), small).err(), Some(Error::Protocol));
    assert!(parsed(&reply("", 0), small).is_ok());
    // Same bytes are independently accepted/rejected by each passed operation's bounds.
    assert!(parsed(&reply("four", 65), maximum).is_ok());
    assert_eq!(
        parsed(&reply("four", 65), small).err(),
        Some(Error::Protocol)
    );
}

#[test]
fn closed_author_reply_refuses_bad_identity_duplicate_tool_and_thinking_frames() {
    let bounds = ReplyBounds {
        output_tokens: 1024,
        text_bytes: 8192,
    };
    for mutation in 0..12 {
        let mut value = reply("", 0);
        match mutation {
            0 => value["id"] = json!(18),
            1 => value["version"] = json!(2),
            2 => value["tool_calls"] = json!([]),
            3 => value["text"] = json!("<think>private</think>"),
            4 => value["text"] = json!("</think>"),
            5 => value["status"] = json!("running"),
            6 => value["error"] = json!("cancelled"),
            7 => {
                value["status"] = json!("error");
                value["error"] = json!("cancelled");
                value["text"] = json!("not empty");
            }
            8 => value["metrics"]["unknown"] = json!(0),
            9 => value["metrics"]["input_tokens"] = json!(4097),
            10 => value["metrics"]["total_ms"] = json!(-1),
            _ => value["metrics"]["output_tokens"] = json!(-1),
        }
        assert_eq!(
            parsed(&value, bounds).err(),
            Some(Error::Protocol),
            "closed frame {mutation}"
        );
    }
    let raw = serde_json::to_string(&reply("", 0)).unwrap();
    let duplicate = raw.replacen("\"id\":17", "\"id\":17,\"id\":17", 1);
    assert_ne!(duplicate, raw, "duplicate control constructed");
    for malformed in [duplicate.as_bytes(), b"{", b"[]", b"null"] {
        assert_eq!(
            parse_reply(malformed, 17, bounds).err(),
            Some(Error::Protocol)
        );
    }
    let mut terminal_error = reply("", 0);
    terminal_error["status"] = json!("error");
    terminal_error["error"] = json!("cancelled");
    assert!(
        parsed(&terminal_error, bounds).is_ok(),
        "valid closed terminal error is not a success"
    );
}

#[test]
fn legacy_play_and_non_generation_reply_ceilings_remain_350_and_16384() {
    let legacy = ReplyBounds {
        output_tokens: 350,
        text_bytes: 16_384,
    };
    assert!(parsed(&reply(&"x".repeat(16_384), 350), legacy).is_ok());
    assert!(
        parsed(&reply("", 65), legacy).is_ok(),
        "old Play request64 still has ceiling350"
    );
    assert_eq!(parsed(&reply("", 351), legacy).err(), Some(Error::Protocol));
    assert_eq!(
        parsed(&reply(&"x".repeat(16_385), 0), legacy).err(),
        Some(Error::Protocol)
    );
    assert!(parsed(&reply("", 0), legacy).is_ok());
}

#[test]
fn ordinary_runtime_constructor_cannot_dispatch_author_even_with_typed_role() {
    let (mut owner, _retained) = owned_setup(LocalRuntime::development_protocol_fixture());
    let initial = load(&mut owner);
    let before = owner.next_id;
    let result = owner.generate(author_generation(64), || false).err();
    let bounded = owner
        .generate_bounded(
            author_generation(64),
            ReplyBounds {
                output_tokens: 64,
                text_bytes: 8192,
            },
            || false,
        )
        .err();
    let after = owner.next_id;
    let cleanup = cleanup(&mut owner);
    cleaned(initial, cleanup);
    assert_eq!(result, Some(Error::WorkerUnavailable));
    assert_eq!(bounded, Some(Error::WorkerUnavailable));
    assert_eq!(
        after, before,
        "ordinary fixture is not an Author capability"
    );
}

#[test]
fn native_author_fixture_rechecks_bounds_before_frames_and_uses_same_owner() {
    let (mut owner, _retained) = author_owner();
    let initial = load(&mut owner);
    let before = owner.next_id;
    let mut rejected = vec![];
    for (tokens, bytes) in [(0, 8192), (1025, 8192), (64, 0), (64, 8193)] {
        rejected.push(
            owner
                .generate_bounded(
                    author_generation(tokens),
                    ReplyBounds {
                        output_tokens: tokens,
                        text_bytes: bytes,
                    },
                    || false,
                )
                .err(),
        );
    }
    let after_invalid = owner.next_id;
    let result = owner.generate_bounded(
        author_generation(64),
        ReplyBounds {
            output_tokens: 64,
            text_bytes: 3,
        },
        || false,
    );
    let after_valid = owner.next_id;
    let cleanup = cleanup(&mut owner);
    cleaned(initial, cleanup);
    assert!(rejected.iter().all(|v| *v == Some(Error::InvalidRequest)));
    assert_eq!(
        after_invalid, before,
        "invalid native bounds cannot send a frame"
    );
    assert!(result.is_ok_and(|value| value.text.is_empty()));
    assert_eq!(
        after_valid,
        before + 1,
        "one bounded generation on retained owner"
    );
}

#[test]
fn controlled_unresolved_cleanup_retains_failed_owner_and_refuses_more_author_work() {
    let (mut owner, _retained) = author_owner();
    let initial = load(&mut owner);
    let before = owner.next_id;
    // Existing thread-local fault, not a new hook or an OS unknown-drain probe.
    FAIL_CLEANUP_ONCE.with(|fault| fault.set(true));
    let unresolved = owner.terminate_and_reap();
    let failed = owner.status();
    let result = owner
        .generate_bounded(
            author_generation(64),
            ReplyBounds {
                output_tokens: 64,
                text_bytes: 8192,
            },
            || false,
        )
        .err();
    let after = owner.next_id;
    // A separate explicit cleanup attempt is positively checked before assertions.
    let cleanup = cleanup(&mut owner);
    cleaned(initial, cleanup);
    assert_eq!(unresolved, Err(Error::Cleanup));
    assert_eq!(failed, Status::Failed);
    assert_eq!(result, Some(Error::WorkerUnavailable));
    assert_eq!(
        after, before,
        "failed owner does not create a replacement operation"
    );
}
